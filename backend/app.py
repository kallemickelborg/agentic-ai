from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, AsyncGenerator
import os
import logging
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import urllib.parse
import re
import traceback
import requests
from fastapi.middleware.cors import CORSMiddleware
import json
import aiohttp
import io
import PyPDF2
import pdfplumber
from bs4 import BeautifulSoup
from typing import Optional, Tuple, Dict
import datetime

import dspy

# ============================================================================
# FastAPI Setup and Configuration
# ============================================================================

app = FastAPI()

load_dotenv()

origins = [
    "https://agentic-ai-frontend.onrender.com",
    "http://localhost:3000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Logging Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# ============================================================================
# OpenAI Configuration
# ============================================================================

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.error(
        "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
    )
    raise EnvironmentError("OpenAI API key not found.")

gpt4o_mini = dspy.LM("openai/gpt-4o-mini", max_tokens=8192, api_key=openai_api_key)
dspy.configure(lm=gpt4o_mini)

# ============================================================================
# Data Models
# ============================================================================


class Author(BaseModel):
    name: str


class EvidencePoint(BaseModel):
    title: str
    evidence: str


class Paper(BaseModel):
    title: str
    link: str
    authors: List[Author] = []
    published_date: str = ""
    abstract: Optional[str] = None
    citation_count: int = 0
    peer_reviewed: bool = False
    journal_name: str = ""
    journal_impact_factor: float = 0.0
    sciscore: Optional[float] = None
    study_type: str = ""
    publication_type: List[str] = []
    relevancy_score: Optional[float] = None
    citation_score: Optional[float] = None
    full_text_accessible: bool = False
    full_text_link: Optional[str] = None
    source_type: str = (
        "open_access",
        "abstract_only",
        "requires_access",
    )
    supporting_evidence: Optional[List[EvidencePoint]] = None
    opposing_evidence: Optional[List[EvidencePoint]] = None
    key_findings: Optional[str] = None


class Task(BaseModel):
    state: str
    input_data: dict
    task_description: str
    research_papers: List[Paper] = []


# ============================================================================
# State Management
# ============================================================================

state_transitions = {
    "Start": "Clarify",
    "Clarify": "Research",
    "Research": "Analyze",
    "Analyze": "Conclude",
    "Conclude": "Start",
}

state_substeps = {
    "Start": ["Initializing the research assistant.", "Setting up the environment."],
    "Clarify": [
        "Analyzing the prompt for specificity.",
        "Generating clarifying questions.",
    ],
    "Research": [
        "Optimizing query for optimal findings.",
        "Querying medical publications.",
        "Finding relevant research papers for the prompt.",
    ],
    "Analyze": [
        "Analyzing the fetched research papers.",
        "Extracting key insights and data.",
    ],
    "Conclude": [
        "Formulating the final conclusion based on research.",
        "Ensuring all points are covered comprehensively.",
    ],
}

# ============================================================================
# DSPy Signatures
# ============================================================================


class ClarifyQuestions(dspy.Signature):
    """Generate clarifying questions for a research topic."""

    task_description = dspy.InputField()
    questions = dspy.OutputField(
        desc="3-5 clarifying questions that can be answered with Yes/No. The questions should be in the format of 'Do you want to know more about ...?'"
    )


class EnhanceQuery(dspy.Signature):
    """Enhance a search query based on clarifying answers."""

    original_query = dspy.InputField()
    clarify_answers = dspy.InputField()
    enhanced_query = dspy.OutputField(desc="An enhanced search query")


class Analysis(dspy.Signature):
    """Analyze research papers in context of the task."""

    task_description = dspy.InputField()
    state = dspy.InputField()
    research_papers = dspy.InputField()
    analysis = dspy.OutputField(desc="Analysis of the research papers")


class Conclude(dspy.Signature):
    """Provide a conclusion based on research."""

    task_description = dspy.InputField()
    state = dspy.InputField()
    research_papers = dspy.InputField()
    conclusion = dspy.OutputField(desc="Comprehensive conclusion")


class PaperEvaluation(dspy.Signature):
    """Evaluate a research paper for both relevance to the query and scientific merit."""

    paper_title = dspy.InputField()
    paper_abstract = dspy.InputField()
    peer_reviewed = dspy.InputField()
    study_type = dspy.InputField()
    user_query = dspy.InputField()
    relevancy_score = dspy.OutputField(
        desc="Numeric score from 1-100 representing how well the paper matches the user's query."
    )
    citation_score = dspy.OutputField(
        desc="Numeric score from 1-100 representing the scientific merit of the paper."
    )


class PaperAnalysis(dspy.Signature):
    """Analyze a single research paper for supporting/opposing evidence."""

    paper_title = dspy.InputField()
    paper_content = dspy.InputField(desc="Full text or abstract of the paper")
    content_type = dspy.InputField(
        desc="Whether this is 'full_text' or 'abstract_only'"
    )
    user_query = dspy.InputField()
    clarifying_context = dspy.InputField()

    supporting_evidence = dspy.OutputField(
        desc="""List of evidence points that support the user's query. Each point must be an object in this exact format:
        [
            {
                "title": "Short descriptive title of the evidence point",
                "evidence": "Detailed evidence with page/section reference"
            },
            ...
        ]
        Example:
        [
            {
                "title": "Vitamin K2 improves metabolic health",
                "evidence": "Study showed significant decrease in waist circumference and fat mass (p. 1246)"
            }
        ]"""
    )
    opposing_evidence = dspy.OutputField(
        desc="""List of evidence points that oppose or limit the user's query. Each point must be an object in this exact format:
        [
            {
                "title": "Short descriptive title of the limitation/opposing evidence",
                "evidence": "Detailed evidence with page/section reference"
            },
            ...
        ]
        Example:
        [
            {
                "title": "Limited effectiveness in elderly population",
                "evidence": "No significant improvements observed in patients over 75 years (Results section)"
            }
        ]"""
    )
    key_findings = dspy.OutputField(
        desc="Brief summary of the paper's key findings relevant to the query"
    )


# Initialize DSPy modules
clarify_questions_module = dspy.ChainOfThought(ClarifyQuestions)
enhance_query_module = dspy.ChainOfThought(EnhanceQuery)
analysis_module = dspy.ChainOfThought(Analysis)
conclude_module = dspy.ChainOfThought(Conclude)
paper_evaluation_module = dspy.ChainOfThought(PaperEvaluation)

# Configure paper analysis module with specific parameters
paper_analysis_module = dspy.ChainOfThought(PaperAnalysis)
paper_analysis_module.temperature = 0.7

# Example prompt to guide the analysis
paper_analysis_module.preset_prompt = """
Given a research paper's content and a user's query with clarifying context, analyze the paper to extract evidence in a specific format.

For both supporting and opposing evidence, you must return a list of objects, where each object has exactly two fields:
- "title": A short, descriptive title summarizing the evidence point
- "evidence": Detailed evidence with page/section reference

Example format:
{
    "supporting_evidence": [
        {
            "title": "Vitamin K2 improves metabolic health",
            "evidence": "Study showed significant decrease in waist circumference and fat mass (p. 1246)"
        },
        {
            "title": "Positive effects on insulin sensitivity",
            "evidence": "Randomized controlled trial showed improvements in insulin sensitivity markers (p. 1247)"
        }
    ],
    "opposing_evidence": [
        {
            "title": "Limited effectiveness in elderly",
            "evidence": "No significant improvements in patients over 75 years (Results section)"
        }
    ]
}

Important:
1. Always return evidence as a list of objects, even if there's only one piece of evidence
2. Each evidence point must have both a title and evidence field
3. Make titles clear and informative
4. Include page numbers or section references when available
5. If no evidence is found, return an empty list []
6. Never return plain strings, always use the object format
"""

# ============================================================================
# Core Functions
# ============================================================================


def generate_clarifying_questions(task_description: str) -> List[str]:
    """Generate clarifying questions using DSPy's ChainOfThought module."""
    response = clarify_questions_module.forward(task_description=task_description)
    questions = response.questions if hasattr(response, "questions") else ""
    return [q.strip() for q in questions.split("\n") if q.strip()]


def clean_query(query: str) -> str:
    """Clean the query by removing any AI-generated prefixes or unwanted phrases."""
    cleaned = re.sub(
        r"^(Optimized research query:|Enhanced query:)\s*",
        "",
        query,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r'^"(.*)"$', r"\1", cleaned.strip())
    return cleaned.strip()


def enhance_search_query(query: str) -> str:
    """Enhance the search query to improve relevance of results."""
    cleaned_query = re.sub(r"\[.*?\]", "", query).strip()
    words = cleaned_query.split()
    phrases = []
    for i in range(len(words)):
        phrases.append(words[i])
        if i < len(words) - 1:
            phrases.append(f'"{words[i]} {words[i+1]}"')
        if i < len(words) - 2:
            phrases.append(f'"{words[i]} {words[i+1]} {words[i+2]}"')
    enhanced_query = " OR ".join(phrases)
    enhanced_query += ' AND ("last 5 years"[PDat])'
    return enhanced_query


def enhance_query_with_dspy(
    original_query: str, clarify_answers: List[Dict[str, str]]
) -> str:
    """Enhance the original query based on clarifying answers using DSPy's ChainOfThought module."""
    formatted_answers = "\n".join(
        [f"Q: {ans['question']}\nA: {ans['answer']}" for ans in clarify_answers]
    )
    response = enhance_query_module.forward(
        original_query=original_query, clarify_answers=formatted_answers
    )
    enhanced_query = (
        response.enhanced_query
        if hasattr(response, "enhanced_query")
        else original_query
    )
    return enhanced_query


def analyze_individual_paper(
    paper: Paper, user_query: str, clarifying_context: str
) -> dict:
    """Analyze a single paper for supporting and opposing evidence."""
    try:
        response = paper_analysis_module(
            paper_title=paper.title,
            paper_abstract=paper.abstract or "",
            user_query=user_query,
            clarifying_context=clarifying_context,
        )

        return {
            "title": paper.title,
            "link": paper.link,
            "supporting_evidence": (
                response.supporting_evidence
                if hasattr(response, "supporting_evidence")
                else ""
            ),
            "opposing_evidence": (
                response.opposing_evidence
                if hasattr(response, "opposing_evidence")
                else ""
            ),
            "key_findings": (
                response.key_findings if hasattr(response, "key_findings") else ""
            ),
        }
    except Exception as e:
        logger.error(f"Error analyzing paper '{paper.title}': {str(e)}")
        return {
            "title": paper.title,
            "link": paper.link,
            "supporting_evidence": "Error analyzing supporting evidence.",
            "opposing_evidence": "Error analyzing opposing evidence.",
            "key_findings": "Error analyzing key findings.",
        }


async def fetch_pdf_content(url: str) -> Optional[str]:
    """
    Fetch and extract text content from a PDF URL.
    Returns the extracted text or None if unsuccessful.
    """
    logger.info(f"Attempting to fetch PDF from: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
    }

    try:
        # Ensure URL ends with /pdf/ for PMC
        if "pmc/articles" in url and not url.endswith("/pdf/"):
            url = url.rstrip("/") + "/pdf/"
            logger.info(f"Adjusted PMC URL to: {url}")

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(
                        f"Failed to fetch PDF from {url}: {response.status} - {response.reason}"
                    )
                    logger.debug(f"Response headers: {dict(response.headers)}")

                    # Try alternative URL format if PMC
                    if "pmc/articles" in url:
                        alt_url = url.replace("/pdf/", "/pdf")
                        logger.info(f"Trying alternative URL: {alt_url}")
                        async with session.get(alt_url) as alt_response:
                            if alt_response.status != 200:
                                logger.error(
                                    f"Failed to fetch PDF from alternate URL {alt_url}: {alt_response.status} - {alt_response.reason}"
                                )
                                logger.debug(
                                    f"Alternative response headers: {dict(alt_response.headers)}"
                                )
                                return None
                            content = await alt_response.read()
                            logger.info(
                                f"Successfully fetched PDF from alternative URL, content size: {len(content)} bytes"
                            )
                    else:
                        return None
                else:
                    content = await response.read()
                    logger.info(
                        f"Successfully fetched PDF, content size: {len(content)} bytes"
                    )

                pdf_file = io.BytesIO(content)

                # Try with PyPDF2 first
                try:
                    reader = PyPDF2.PdfReader(pdf_file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    if text.strip():  # Check if we got meaningful text
                        logger.info(
                            f"Successfully extracted text with PyPDF2, length: {len(text)} characters"
                        )
                        return text.strip()
                    logger.warning("PyPDF2 extracted empty text, trying pdfplumber")
                except Exception as e:
                    logger.warning(f"PyPDF2 failed, trying pdfplumber: {str(e)}")

                # Fallback to pdfplumber
                try:
                    pdf_file.seek(0)  # Reset file pointer
                    with pdfplumber.open(pdf_file) as pdf:
                        text = ""
                        for page in pdf.pages:
                            text += page.extract_text() + "\n"
                        if text.strip():
                            logger.info(
                                f"Successfully extracted text with pdfplumber, length: {len(text)} characters"
                            )
                        else:
                            logger.warning("pdfplumber extracted empty text")
                        return text.strip()
                except Exception as e:
                    logger.error(f"PDF extraction failed: {str(e)}")
                    return None

    except Exception as e:
        logger.error(f"Error fetching PDF: {str(e)}")
        logger.error(traceback.format_exc())
        return None


async def fetch_pmc_paper_content(pmid: str) -> Tuple[bool, Optional[str]]:
    """
    Fetch paper content from PubMed Central.
    Returns (success, content) tuple.
    """
    try:
        # First get the PMC ID
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        pmc_check_url = f"{base_url}elink.fcgi"
        params = {"dbfrom": "pubmed", "db": "pmc", "id": pmid, "retmode": "json"}

        async with aiohttp.ClientSession() as session:
            async with session.get(pmc_check_url, params=params) as response:
                if response.status != 200:
                    return False, None

                data = await response.json()
                link_set = data.get("linksets", [{}])[0]
                id_list = (
                    link_set.get("linksetdbs", [{}])[0].get("links", [])
                    if link_set.get("linksetdbs")
                    else []
                )

                if not id_list:
                    return False, None

                pmc_id = id_list[0]

                # Try different URL formats for PMC
                urls_to_try = [
                    f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/",
                    f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf",
                    f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}",
                ]

                # Try each URL format
                for url in urls_to_try:
                    if url.endswith("pdf/") or url.endswith("pdf"):
                        content = await fetch_pdf_content(url)
                        if content:
                            return True, content
                    else:
                        # If HTML URL, try to fetch HTML version
                        async with session.get(url) as html_response:
                            if html_response.status == 200:
                                html_content = await html_response.text()
                                soup = BeautifulSoup(html_content, "html.parser")

                                # Extract main content
                                article_text = ""
                                main_content = soup.find(
                                    "div", {"class": "jig-ncbiinpagenav"}
                                )
                                if not main_content:
                                    # Try alternative content div
                                    main_content = soup.find(
                                        "div", {"class": "article-body"}
                                    )

                                if main_content:
                                    # Remove references and other unwanted sections
                                    for unwanted in main_content.find_all(
                                        ["div", "table"],
                                        {"class": ["ref-list", "table-wrap"]},
                                    ):
                                        unwanted.decompose()
                                    article_text = main_content.get_text(
                                        separator="\n", strip=True
                                    )

                                    if article_text:
                                        return True, article_text

                return False, None

    except Exception as e:
        logger.error(f"Error fetching PMC content: {str(e)}")
        return False, None


async def analyze_paper_content(
    paper: Paper, user_query: str, clarifying_context: str
) -> Dict[str, any]:
    """Analyze paper content using full text when available, otherwise use abstract."""
    try:
        # Extract PMID from the PubMed URL
        pmid = paper.link.split("/")[-1]
        logger.info(f"Analyzing paper {paper.title} (PMID: {pmid})")

        # Try to get full text content
        success = False
        content = None

        if paper.source_type == "open_access":
            success, content = await fetch_pmc_paper_content(pmid)
            logger.info(f"Full text fetched for paper {paper.title}: {success}")

        # Use full text if available, otherwise fall back to abstract
        analysis_text = content if success else paper.abstract
        content_type = "full_text" if success else "abstract_only"

        if not analysis_text:
            logger.warning(f"No content available for paper {paper.title}")
            return {
                "title": paper.title,
                "link": paper.link,
                "supporting_evidence": [],
                "opposing_evidence": [],
                "key_findings": "No content available for analysis.",
                "analysis_type": "error",
            }

        # Analyze content using DSPy
        try:
            logger.info(f"Starting DSPy analysis for {paper.title}")
            response = paper_analysis_module(
                paper_title=paper.title,
                paper_content=analysis_text,
                content_type=content_type,
                user_query=user_query,
                clarifying_context=clarifying_context,
            )

            # Extract and validate the evidence
            supporting = []
            opposing = []

            # Format supporting evidence
            if hasattr(response, "supporting_evidence"):
                raw_supporting = response.supporting_evidence
                logger.info(
                    f"Raw supporting evidence for {paper.title}: {raw_supporting}"
                )

                # Handle both string and list formats
                if isinstance(raw_supporting, list):
                    for point in raw_supporting:
                        if (
                            isinstance(point, dict)
                            and "title" in point
                            and "evidence" in point
                        ):
                            supporting.append(
                                {"title": point["title"], "evidence": point["evidence"]}
                            )
                elif isinstance(raw_supporting, str):
                    # Try to parse if it's a JSON string
                    try:
                        parsed = json.loads(raw_supporting)
                        if isinstance(parsed, list):
                            for point in parsed:
                                if (
                                    isinstance(point, dict)
                                    and "title" in point
                                    and "evidence" in point
                                ):
                                    supporting.append(
                                        {
                                            "title": point["title"],
                                            "evidence": point["evidence"],
                                        }
                                    )
                    except json.JSONDecodeError:
                        # If not valid JSON, split into sentences
                        sentences = raw_supporting.split(". ")
                        supporting = [
                            {
                                "title": f"Evidence Point {i+1}",
                                "evidence": sentence.strip() + ".",
                            }
                            for i, sentence in enumerate(sentences)
                            if sentence.strip()
                        ]

            # Format opposing evidence
            if hasattr(response, "opposing_evidence"):
                raw_opposing = response.opposing_evidence
                logger.info(f"Raw opposing evidence for {paper.title}: {raw_opposing}")

                # Handle both string and list formats
                if isinstance(raw_opposing, list):
                    for point in raw_opposing:
                        if (
                            isinstance(point, dict)
                            and "title" in point
                            and "evidence" in point
                        ):
                            opposing.append(
                                {"title": point["title"], "evidence": point["evidence"]}
                            )
                elif isinstance(raw_opposing, str):
                    # Try to parse if it's a JSON string
                    try:
                        parsed = json.loads(raw_opposing)
                        if isinstance(parsed, list):
                            for point in parsed:
                                if (
                                    isinstance(point, dict)
                                    and "title" in point
                                    and "evidence" in point
                                ):
                                    opposing.append(
                                        {
                                            "title": point["title"],
                                            "evidence": point["evidence"],
                                        }
                                    )
                    except json.JSONDecodeError:
                        # If not valid JSON, split into sentences
                        sentences = raw_opposing.split(". ")
                        opposing = [
                            {
                                "title": f"Evidence Point {i+1}",
                                "evidence": sentence.strip() + ".",
                            }
                            for i, sentence in enumerate(sentences)
                            if sentence.strip()
                        ]

            findings = (
                response.key_findings if hasattr(response, "key_findings") else ""
            )

            # Log the extracted content for debugging
            logger.info(f"Extracted evidence for {paper.title}:")
            logger.info(f"Supporting evidence: {json.dumps(supporting, indent=2)}")
            logger.info(f"Opposing evidence: {json.dumps(opposing, indent=2)}")
            logger.info(f"Key findings: {findings}")

            # Add content type context to the response
            content_note = f" [Analysis based on {content_type}]"

            result = {
                "title": paper.title,
                "link": paper.link,
                "supporting_evidence": supporting,
                "opposing_evidence": opposing,
                "key_findings": findings + content_note,
                "analysis_type": content_type,
            }

            logger.info(
                f"Final analysis result for {paper.title}: {json.dumps(result, indent=2)}"
            )
            return result

        except Exception as e:
            logger.error(f"Error in DSPy analysis for {paper.title}: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "title": paper.title,
                "link": paper.link,
                "supporting_evidence": [],
                "opposing_evidence": [],
                "key_findings": "Error during paper analysis.",
                "analysis_type": "error",
            }

    except Exception as e:
        logger.error(f"Error analyzing paper content for {paper.title}: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "title": paper.title,
            "link": paper.link,
            "supporting_evidence": [],
            "opposing_evidence": [],
            "key_findings": "Error analyzing paper content.",
            "analysis_type": "error",
        }


async def analyze_papers(
    task_description: str,
    state: str,
    research_papers: List[Paper],
    clarify_answers: List[Dict[str, str]] = [],
) -> dict:
    """Analyze research papers and provide detailed analysis for each paper."""
    logger.info(f"Analyzing papers for task: {task_description}")

    # Format clarifying context
    clarifying_context = "\n".join(
        [f"Q: {ans['question']}\nA: {ans['answer']}" for ans in clarify_answers]
    )

    # Analyze each paper individually with full text when available
    paper_analyses = []
    for paper in research_papers:
        try:
            analysis = await analyze_paper_content(
                paper=paper,
                user_query=task_description,
                clarifying_context=clarifying_context,
            )
            logger.info(
                f"Individual paper analysis result: {json.dumps(analysis, indent=2)}"
            )

            # Ensure the analysis has all required fields
            if not all(
                key in analysis
                for key in ["supporting_evidence", "opposing_evidence", "key_findings"]
            ):
                logger.warning(
                    f"Missing required fields in analysis for paper: {paper.title}"
                )
                continue

            paper_analyses.append(analysis)

        except Exception as e:
            logger.error(f"Error analyzing paper {paper.title}: {str(e)}")
            logger.error(traceback.format_exc())
            # Add error result for this paper
            paper_analyses.append(
                {
                    "title": paper.title,
                    "link": paper.link,
                    "supporting_evidence": "Error analyzing paper.",
                    "opposing_evidence": "Error analyzing paper.",
                    "key_findings": "Error analyzing paper.",
                    "analysis_type": "error",
                }
            )

    # Generate overall analysis using existing module
    papers_formatted = "\n".join(
        [f"- {paper.title} ({paper.link})" for paper in research_papers]
    )

    try:
        overall_analysis = analysis_module.forward(
            task_description=task_description,
            state=state,
            research_papers=papers_formatted,
        )
        overall_text = (
            overall_analysis.analysis if hasattr(overall_analysis, "analysis") else ""
        )
    except Exception as e:
        logger.error(f"Error generating overall analysis: {str(e)}")
        logger.error(traceback.format_exc())
        overall_text = "Error generating overall analysis."

    result = {
        "state": "Analyze",  # Ensure we stay in Analyze state
        "paper_analyses": paper_analyses,
        "overall_analysis": overall_text,
        "total_papers_analyzed": len(paper_analyses),
        "analysis_timestamp": datetime.datetime.now().isoformat(),
        "analysis_complete": True,  # Add flag to indicate analysis is complete
        "current_steps": state_substeps.get("Analyze", []),
        "can_proceed": True,  # Add flag to indicate user can proceed to next state
    }

    logger.info(f"Final analysis result structure: {json.dumps(result, indent=2)}")
    return result


def conclude_research(  # WIP
    task_description: str, state: str, research_papers: List[Paper]
) -> str:
    """Provide a comprehensive conclusion based on research papers using DSPy's ChainOfThought module."""
    papers_formatted = "\n".join(
        [f"- {paper.title} ({paper.link})" for paper in research_papers]
    )
    response = conclude_module.forward(
        task_description=task_description, state=state, research_papers=papers_formatted
    )
    return response.get("conclusion", "")


def check_paper_accessibility(pmid: str) -> tuple[bool, Optional[str], str]:
    """
    Check if a paper is accessible and get its full text link if available.
    Returns: (is_accessible, full_text_link, source_type)
    """
    try:
        # First check if paper is available in PubMed Central (open access)
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        pmc_check_url = f"{base_url}elink.fcgi"
        params = {"dbfrom": "pubmed", "db": "pmc", "id": pmid, "retmode": "json"}

        response = requests.get(pmc_check_url, params=params, timeout=10)
        response.raise_for_status()

        # Parse the response to check for PMC link
        data = response.json()
        link_set = data.get("linksets", [{}])[0]
        id_list = (
            link_set.get("linksetdbs", [{}])[0].get("links", [])
            if link_set.get("linksetdbs")
            else []
        )

        if id_list:
            # Paper is available in PMC
            pmc_id = id_list[0]
            full_text_link = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}"
            return True, full_text_link, "open_access"

        # If not in PMC, check the original publisher's link
        linkout_url = f"{base_url}elink.fcgi?dbfrom=pubmed&id={pmid}&cmd=prlinks"
        response = requests.head(linkout_url, timeout=10, allow_redirects=True)

        final_url = response.url
        if any(
            domain in final_url
            for domain in [
                "sciencedirect.com",
                "springer.com",
                "wiley.com",
                "tandfonline.com",
                "academic.oup.com",
                "nature.com",
                "bmj.com",
            ]
        ):
            # Paper requires institutional access
            return False, final_url, "requires_access"

        # Paper might be freely available on publisher's site
        return True, final_url, "open_access"

    except Exception as e:
        logger.error(f"Error checking paper accessibility for PMID {pmid}: {str(e)}")
        return False, None, "abstract_only"


def fetch_research_papers(query: str, max_results: int = 20) -> List[Paper]:
    """Fetch research papers from PubMed E-utilities API."""
    logger.info(f"Original query: '{query}'")
    cleaned_query = clean_query(query)
    enhanced_query = enhance_search_query(cleaned_query)
    logger.info(f"Enhanced query: '{enhanced_query}'")
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    papers = []

    try:
        # Initial search to get paper IDs
        search_response = requests.get(
            f"{base_url}esearch.fcgi",
            params={
                "db": "pubmed",
                "term": enhanced_query,
                "retmax": max_results,
                "sort": "relevance",
                "retmode": "json",
                "usehistory": "y",
            },
            timeout=10,
        )
        search_response.raise_for_status()

        try:
            search_data = search_response.json()
        except Exception as e:
            logger.error(f"Error parsing search response: {e}")
            search_data = {}

        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        query_key = search_data.get("esearchresult", {}).get("querykey")
        web_env = search_data.get("esearchresult", {}).get("webenv")

        if not id_list:
            raise HTTPException(status_code=204, detail="No research papers found")

        logger.info(f"Found {len(id_list)} papers")

        # Fetch detailed information
        efetch_response = requests.get(
            f"{base_url}efetch.fcgi",
            params={
                "db": "pubmed",
                "query_key": query_key,
                "WebEnv": web_env,
                "retmode": "xml",
                "retmax": max_results,
            },
            timeout=10,
        )
        efetch_response.raise_for_status()
        root = ET.fromstring(efetch_response.content)

        for article in root.findall(".//PubmedArticle"):
            try:
                # Extract basic information
                title = article.findtext(".//ArticleTitle") or "No title available"
                abstract = article.findtext(".//AbstractText") or ""
                pmid = article.findtext(".//PMID") or "No PMID available"

                # Check accessibility
                is_accessible, full_text_link, source_type = check_paper_accessibility(
                    pmid
                )

                # Extract authors
                authors = []
                for author in article.findall(".//Author"):
                    last_name = author.findtext("LastName") or ""
                    fore_name = author.findtext("ForeName") or ""
                    if last_name or fore_name:
                        authors.append(Author(name=f"{last_name} {fore_name}".strip()))

                # Extract date
                pub_date = article.find(".//PubDate")
                published_date = "Date not available"
                if pub_date is not None:
                    year = pub_date.findtext("Year") or ""
                    month = pub_date.findtext("Month") or ""
                    day = pub_date.findtext("Day") or ""
                    published_date = "-".join(filter(None, [year, month, day]))

                # Study type
                study_type = "unknown"
                abstract_lower = abstract.lower()
                if any(
                    term in abstract_lower
                    for term in ["clinical trial", "human subjects", "patient"]
                ):
                    study_type = "clinical trial"
                elif any(
                    term in abstract_lower
                    for term in ["in vivo", "animal model", "mouse", "rat"]
                ):
                    study_type = "in vivo"
                elif any(
                    term in abstract_lower
                    for term in ["in vitro", "cell culture", "cell line"]
                ):
                    study_type = "in vitro"

                # Publication types
                publication_types = [
                    pub_type.text
                    for pub_type in article.findall(".//PublicationType")
                    if pub_type.text
                ]

                # Peer review status
                peer_reviewed = bool(
                    article.find(".//Journal")
                    and "Journal Article" in publication_types
                )

                papers.append(
                    Paper(
                        title=title,
                        link=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}",
                        authors=authors,
                        published_date=published_date,
                        abstract=abstract,
                        peer_reviewed=peer_reviewed,
                        study_type=study_type,
                        publication_type=publication_types,
                        full_text_accessible=is_accessible,
                        full_text_link=full_text_link,
                        source_type=source_type,
                    )
                )
            except Exception as e:
                logger.error(f"Error processing article: {str(e)}")
                continue

    except requests.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise HTTPException(
            status_code=503, detail="Failed to fetch papers from PubMed"
        )
    except ET.ParseError as e:
        logger.error(f"XML parsing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to parse PubMed response")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return papers


def process_research_papers(task_description: str, input_data: dict):
    """Process research papers and yield updates for each paper."""
    research_papers = fetch_research_papers(task_description)
    logger.info(f"Processing Research state for task: {task_description}")

    # Get clarifying answers
    clarify_answers = input_data.get("clarify_answers", [])
    clarify_context = "\n".join(
        [f"Q: {ans['question']}\nA: {ans['answer']}" for ans in clarify_answers]
    )

    # Create a context-aware query by combining original query and clarifying answers
    context_aware_query = f"""
    Original Query: {task_description}
    User's Clarifications:
    {clarify_context}
    """

    processed_papers = []
    total_papers = len(research_papers)

    # Send initial count
    yield {
        "state": "Research",
        "total_papers": total_papers,
        "processed_papers": 0,
        "current_paper": None,
    }

    for index, paper in enumerate(research_papers):
        try:
            # Single call to evaluate both scores with context-aware query
            response = paper_evaluation_module(
                paper_title=paper.title,
                paper_abstract=paper.abstract or "",
                peer_reviewed=str(paper.peer_reviewed),
                study_type=paper.study_type or "Unknown",
                user_query=context_aware_query,  # Use context-aware query instead of just task_description
            )

            # Parse out both scores
            rel_score = 50.0
            cit_score = 50.0

            # Convert to float and clamp
            try:
                rel_score = max(1.0, min(float(response.relevancy_score), 100.0))
            except (ValueError, TypeError):
                logger.warning(
                    f"Invalid relevancy_score for '{paper.title}'. Using default=50."
                )

            try:
                cit_score = max(1.0, min(float(response.citation_score), 100.0))
            except (ValueError, TypeError):
                logger.warning(
                    f"Invalid citation_score for '{paper.title}'. Using default=50."
                )

            paper.relevancy_score = rel_score
            paper.citation_score = cit_score

            processed_papers.append(paper)

            # Send update for each processed paper
            yield {
                "state": "Research",
                "total_papers": total_papers,
                "processed_papers": len(processed_papers),
                "current_paper": {
                    "title": paper.title,
                    "relevancy_score": rel_score,
                    "citation_score": cit_score,
                },
            }

        except Exception as e:
            logger.error(f"Error evaluating paper '{paper.title}': {str(e)}")
            paper.relevancy_score = 50.0
            paper.citation_score = 50.0
            processed_papers.append(paper)

    # Sort by relevancy_score, then by citation_score
    processed_papers.sort(
        key=lambda p: (p.relevancy_score or 0, p.citation_score or 0),
        reverse=True,
    )

    # Send final update with all papers
    yield {
        "state": state_transitions.get("Research", "End"),
        "research_papers": [paper.dict() for paper in processed_papers],
        "response": "Papers have been evaluated for both relevancy and scientific merit.",
        "current_steps": state_substeps.get("Research", []),
        "total_papers": total_papers,
        "processed_papers": len(processed_papers),
        "original_query": task_description,
        "enhanced_query": enhance_query_with_dspy(
            task_description, input_data.get("clarify_answers", [])
        ),
    }


@app.post("/solve-task/")
async def solve_task(task: Task):
    logger.info(f"Received task: {task.dict()}")
    try:
        state = task.state
        logger.info(f"Current state: {state}")
        input_data = task.input_data
        task_description = task.task_description
        research_papers = task.research_papers

        if state == "Start":
            next_state = "Clarify"
            current_steps = state_substeps.get(state, [])
            logger.info(f"Transitioning from 'Start' to '{next_state}'")
            return {"state": next_state, "current_steps": current_steps}

        elif state == "Clarify":
            questions = generate_clarifying_questions(task_description)
            logger.info(f"Generated questions: {questions}")
            current_steps = state_substeps.get(state, [])
            return {
                "state": "Clarify",
                "questions": questions,
                "current_steps": current_steps,
            }

        if state == "Research":

            async def generate_research_updates():
                for update in process_research_papers(task_description, input_data):
                    yield f"data: {json.dumps(update)}\n\n"

            return StreamingResponse(
                generate_research_updates(), media_type="text/event-stream"
            )

        elif state == "Analyze":
            selected_papers_links = input_data.get("selected_papers", [])
            if not selected_papers_links:
                logger.warning("No papers selected for analysis.")
                return {
                    "state": "Error",
                    "error_message": "No papers have been selected for analysis.",
                    "current_steps": [],
                }

            research_papers = [
                paper
                for paper in research_papers
                if paper.link in selected_papers_links
            ]
            if not research_papers:
                logger.warning("Selected papers not found in research_papers.")
                return {
                    "state": "Error",
                    "error_message": "Selected papers not found for analysis.",
                    "current_steps": [],
                }

            logger.info(f"Starting analysis for {len(research_papers)} papers")
            analysis_result = await analyze_papers(
                task_description,
                state,
                research_papers,
                input_data.get("clarify_answers", []),
            )
            logger.info(
                f"Analysis completed, result structure: {json.dumps(analysis_result, indent=2)}"
            )

            # Check if analysis was successful
            if not analysis_result.get("paper_analyses"):
                logger.warning("Analysis produced no results.")
                return {
                    "state": "Error",
                    "error_message": "Analysis produced no results for the selected papers.",
                    "current_steps": [],
                }

            # Return the analysis result directly
            logger.info(
                f"Sending analysis response to frontend: {json.dumps(analysis_result, indent=2)}"
            )
            return analysis_result

        elif state == "Conclude":
            selected_papers_links = input_data.get("selected_papers", [])
            if not selected_papers_links:
                logger.warning("No papers selected for analysis.")
                return {
                    "state": "Error",
                    "error_message": "No papers have been selected for analysis.",
                    "current_steps": [],
                }

            research_papers = [
                paper
                for paper in research_papers
                if paper.link in selected_papers_links
            ]
            if not research_papers:
                logger.warning("Selected papers not found in research_papers.")
                return {
                    "state": "Error",
                    "error_message": "Selected papers not found for analysis.",
                    "current_steps": [],
                }

            conclusion = conclude_research(task_description, state, research_papers)
            response = conclusion

            if len(response.split()) < 50:
                logger.warning("Response is not conclusive.")
                return {
                    "state": "Error",
                    "error_message": "Based on the papers, not enough information is provided to conclude anything based on the prompt.",
                    "current_steps": [],
                }

            next_state = state_transitions.get(state, "End")
            logger.info(f"Transitioning from '{state}' to '{next_state}'")
            return {
                "state": next_state,
                "response": response,
                "current_steps": state_substeps.get(state, []),
            }

        else:
            logger.warning(f"Unknown state '{state}'. Ending task.")
            return {"state": "End", "current_steps": state_substeps.get("End", [])}

    except HTTPException as e:
        if e.status_code == 204:
            return {"message": "No research papers found", "restart": True}
        raise e
    except Exception as e:
        logger.error(f"Error in solve_task: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
