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
    "Conclude": "End",
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
    "End": ["Task completed successfully."],
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


# Initialize DSPy modules
clarify_questions_module = dspy.ChainOfThought(ClarifyQuestions)
enhance_query_module = dspy.ChainOfThought(EnhanceQuery)
analysis_module = dspy.ChainOfThought(Analysis)
conclude_module = dspy.ChainOfThought(Conclude)
paper_evaluation_module = dspy.ChainOfThought(PaperEvaluation)

# ============================================================================
# Core Functions
# ============================================================================


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


def generate_clarifying_questions(task_description: str) -> List[str]:
    """Generate clarifying questions using DSPy's ChainOfThought module."""
    response = clarify_questions_module.forward(task_description=task_description)
    questions = response.questions if hasattr(response, "questions") else ""
    return [q.strip() for q in questions.split("\n") if q.strip()]


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
    print(f"Enhanced query: {response.reasoning}")
    return enhanced_query


def analyze_papers(
    task_description: str, state: str, research_papers: List[Paper]
) -> str:
    """Analyze research papers using DSPy's ChainOfThought module."""
    papers_formatted = "\n".join(
        [f"- {paper.title} ({paper.link})" for paper in research_papers]
    )
    response = analysis_module.forward(
        task_description=task_description, state=state, research_papers=papers_formatted
    )
    return response.analysis if hasattr(response, "analysis") else ""


def conclude_research(
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


def fetch_research_papers(query: str, max_results: int = 20):
    """Fetch research papers related to the query using PubMed E-utilities API."""
    logger.info(f"Original query: '{query}'")

    cleaned_query = clean_query(query)
    enhanced_query = enhance_search_query(cleaned_query)
    logger.info(f"Enhanced query: '{enhanced_query}'")

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    # First, search for papers
    search_url = f"{base_url}esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": enhanced_query,
        "retmax": max_results,
        "sort": "relevance",
        "retmode": "json",
        "usehistory": "y",
    }

    search_response = requests.get(search_url, params=search_params)

    if search_response.status_code != 200:
        logger.error(f"Failed to fetch research papers: {search_response.status_code}")
        logger.error(f"Response content: {search_response.text}")
        return []

    search_data = search_response.json()
    id_list = search_data.get("esearchresult", {}).get("idlist", [])
    query_key = search_data.get("esearchresult", {}).get("querykey")
    web_env = search_data.get("esearchresult", {}).get("webenv")

    if not id_list:
        raise HTTPException(status_code=204, detail="No research papers found")

    logger.info(f"Number of papers found: {len(id_list)}")

    # Fetch detailed information
    efetch_url = f"{base_url}efetch.fcgi"
    efetch_params = {
        "db": "pubmed",
        "query_key": query_key,
        "WebEnv": web_env,
        "retmode": "xml",
        "retmax": max_results,
    }
    efetch_response = requests.get(efetch_url, params=efetch_params)

    if efetch_response.status_code != 200:
        logger.error(
            f"Failed to fetch research paper details: {efetch_response.status_code}"
        )
        return []

    root = ET.fromstring(efetch_response.content)
    papers = []

    for article in root.findall(".//PubmedArticle"):
        # Basic information
        title_elem = article.find(".//ArticleTitle")
        title = (
            title_elem.text
            if title_elem is not None and title_elem.text is not None
            else "No title available"
        )

        abstract_elem = article.find(".//AbstractText")
        abstract = abstract_elem.text if abstract_elem is not None else ""

        pmid_elem = article.find(".//PMID")
        pmid = pmid_elem.text if pmid_elem is not None else "No PMID available"

        # Authors
        authors = [
            f"{author.find('LastName').text if author.find('LastName') is not None else ''} "
            f"{author.find('ForeName').text if author.find('ForeName') is not None else ''}".strip()
            for author in article.findall(".//Author")
        ]

        # Publication date
        pub_date = article.find(".//PubDate")
        if pub_date is not None:
            year = pub_date.find("Year")
            month = pub_date.find("Month")
            day = pub_date.find("Day")
            published_date = f"{year.text if year is not None else ''}-{month.text if month is not None else ''}-{day.text if day is not None else ''}"
        else:
            published_date = "Date not available"

        # Journal information
        journal_elem = article.find(".//Journal")
        journal_name = ""
        if journal_elem is not None:
            journal_title = journal_elem.find(".//Title")
            journal_name = journal_title.text if journal_title is not None else ""

        # Publication types
        publication_types = [
            pub_type.text for pub_type in article.findall(".//PublicationType")
        ]

        # Study type determination
        study_type = "unknown"
        if abstract:
            if any(
                term.lower() in abstract.lower()
                for term in ["in vitro", "cell culture", "cell line"]
            ):
                study_type = "in vitro"
            elif any(
                term.lower() in abstract.lower()
                for term in ["in vivo", "animal model", "mouse", "rat"]
            ):
                study_type = "in vivo"
            elif any(
                term.lower() in abstract.lower()
                for term in ["clinical trial", "human subjects", "patient"]
            ):
                study_type = "clinical trial"

        # Citation metrics
        citation_count = article.find(".//CitedByCount")
        citation_count = int(citation_count.text) if citation_count is not None else 0

        # Peer review status (based on publication type and journal presence)
        peer_reviewed = (
            journal_elem is not None and "Journal Article" in publication_types
        )

        # Create Paper object
        papers.append(
            Paper(
                title=title,
                link=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}",
                authors=[Author(name=author) for author in authors],
                published_date=published_date,
                abstract=abstract,
                citation_count=citation_count,
                peer_reviewed=peer_reviewed,
                journal_name=journal_name,
                study_type=study_type,
                publication_type=publication_types,
            )
        )

    return papers


def process_research_papers(task_description: str):
    """Process research papers and yield updates for each paper."""
    research_papers = fetch_research_papers(task_description)
    logger.info(f"Processing Research state for task: {task_description}")

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
            # Single call to evaluate both scores
            response = paper_evaluation_module(
                paper_title=paper.title,
                paper_abstract=paper.abstract or "",
                peer_reviewed=str(paper.peer_reviewed),
                study_type=paper.study_type or "Unknown",
                user_query=task_description,
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

            logger.info(
                f"Paper '{paper.title}' => Relevancy: {paper.relevancy_score}, Citation: {paper.citation_score}"
            )
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
        "research_papers": [
            paper.dict() for paper in processed_papers
        ],  # Convert to dict for JSON serialization
        "response": "Papers have been evaluated for both relevancy and scientific merit.",
        "current_steps": state_substeps.get("Research", []),
        "total_papers": total_papers,
        "processed_papers": len(processed_papers),
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
                for update in process_research_papers(task_description):
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

            if len(research_papers) < 2:
                logger.warning("Not enough papers selected for a conclusive analysis.")
                return {
                    "state": "Error",
                    "error_message": "Based on the papers, not enough information is provided to conclude anything based on the prompt.",
                    "current_steps": [],
                }

            analysis = analyze_papers(task_description, state, research_papers)

            if len(analysis.split()) < 50:
                logger.warning("Analysis is not conclusive.")
                return {
                    "state": "Error",
                    "error_message": "Based on the papers, not enough information is provided to conclude anything based on the prompt.",
                    "current_steps": [],
                }

            next_state = state_transitions.get(state, "End")
            logger.info(f"Transitioning from '{state}' to '{next_state}'")
            return {
                "state": next_state,
                "response": analysis,
                "current_steps": state_substeps.get(state, []),
            }

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
