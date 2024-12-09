from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import logging
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import urllib.parse
import re
import traceback
import requests
from fastapi.middleware.cors import CORSMiddleware

import dspy
from dspy import ChainOfThought, LM, Signature

app = FastAPI()

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
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class Author(BaseModel):
    name: str


class Paper(BaseModel):
    title: str
    link: str
    authors: List[Author] = []
    published_date: str = ""
    abstract: Optional[str] = None


class Task(BaseModel):
    state: str
    input_data: dict
    task_description: str
    research_papers: List[Paper] = []


state_transitions = {
    "Start": "Clarify",
    "Clarify": "Research",
    "Research": "Analyze",
    "Analyze": "Synthesize",
    "Synthesize": "Conclude",
    "Conclude": "End",
}

# Might need to remove this
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
    "Synthesize": [
        "Synthesizing information from analysis.",
        "Compiling comprehensive insights.",
    ],
    "Conclude": [
        "Formulating the final conclusion based on research.",
        "Ensuring all points are covered comprehensively.",
    ],
    "End": ["Task completed successfully."],
}

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.error(
        "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
    )
    raise EnvironmentError("OpenAI API key not found.")

# Initialize DSPy Language Models
gpt4o_mini = LM("openai/gpt-4o-mini", max_tokens=2000, api_key=openai_api_key)
gpt4o = LM("openai/gpt-4o", max_tokens=2000, api_key=openai_api_key)

dspy.configure(lm=gpt4o_mini)

clarify_questions_signature = Signature(
    "task_description -> questions",
    "Given a research topic, generate 3-5 clarifying questions that can be answered with Yes/No.",
)

clarify_questions_module = ChainOfThought(clarify_questions_signature)

enhance_query_signature = Signature(
    "original_query, clarify_answers -> enhanced_query",
    "Given a query and clarifying answers, generate an enhanced search query.",
)

analysis_signature = Signature(
    "task_description, state, research_papers -> analysis",
    "Analyze the research papers in context of the task.",
)

synthesize_signature = Signature(
    "task_description, state, research_papers -> synthesis",
    "Synthesize information from the research papers.",
)

conclude_signature = Signature(
    "task_description, state, research_papers -> conclusion",
    "Provide a comprehensive conclusion based on the research.",
)

# Initialize modules without prompt templates
clarify_questions_module = dspy.ChainOfThought(clarify_questions_signature)

enhance_query_module = dspy.ChainOfThought(enhance_query_signature)

analysis_module = dspy.ChainOfThought(analysis_signature)

synthesize_module = dspy.ChainOfThought(synthesize_signature)

conclude_module = dspy.ChainOfThought(conclude_signature)

# Remove or comment out the old initializations that used prompt_template
# enhance_query_module = ChainOfThought(
#     signature=enhance_query_signature,
#     prompt_template="""...""",
# )


def fetch_research_papers(query: str, max_results: int = 20):
    """
    Fetch research papers related to the query using PubMed E-utilities API.
    """
    logger.info(f"Original query: '{query}'")

    cleaned_query = clean_query(query)
    enhanced_query = enhance_search_query(cleaned_query)
    logger.info(f"Enhanced query: '{enhanced_query}'")

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    search_url = f"{base_url}esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": enhanced_query,
        "retmax": max_results,
        "sort": "relevance",
        "retmode": "json",
        "usehistory": "y",
    }

    full_search_url = search_url + "?" + urllib.parse.urlencode(search_params)
    # logger.info(f"Full PubMed search URL: {full_search_url}")

    search_response = requests.get(search_url, params=search_params)

    if search_response.status_code != 200:
        logger.error(f"Failed to fetch research papers: {search_response.status_code}")
        logger.error(f"Response content: {search_response.text}")
        return []

    search_data = search_response.json()
    # logger.info(f"Search response: {search_data}")

    id_list = search_data.get("esearchresult", {}).get("idlist", [])
    query_key = search_data.get("esearchresult", {}).get("querykey")
    web_env = search_data.get("esearchresult", {}).get("webenv")

    if not id_list:
        # logger.info("No research papers found.")
        raise HTTPException(status_code=204, detail="No research papers found")

    logger.info(f"Number of papers found: {len(id_list)}")

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
        # logger.error(f"Response content: {efetch_response.text}")
        return []

    root = ET.fromstring(efetch_response.content)
    papers = []

    for article in root.findall(".//PubmedArticle"):
        title_elem = article.find(".//ArticleTitle")
        title = title_elem.text if title_elem is not None else "No title available"

        abstract_elem = article.find(".//AbstractText")
        abstract = abstract_elem.text if abstract_elem is not None else ""

        pmid_elem = article.find(".//PMID")
        pmid = pmid_elem.text if pmid_elem is not None else "No PMID available"

        authors = [
            f"{author.find('LastName').text if author.find('LastName') is not None else ''} "
            f"{author.find('ForeName').text if author.find('ForeName') is not None else ''}".strip()
            for author in article.findall(".//Author")
        ]

        pub_date = article.find(".//PubDate")
        if pub_date is not None:
            year = pub_date.find("Year")
            month = pub_date.find("Month")
            day = pub_date.find("Day")
            published_date = f"{year.text if year is not None else ''}-{month.text if month is not None else ''}-{day.text if day is not None else ''}"
        else:
            published_date = "Date not available"

        papers.append(
            Paper(
                title=title,
                link=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}",
                authors=[Author(name=author) for author in authors],
                published_date=published_date,
                abstract=abstract,
            )
        )

    logger.info(f"Successfully fetched and parsed {len(papers)} research papers.")
    return papers


def clean_query(query: str) -> str:
    """
    Clean the query by removing any AI-generated prefixes or unwanted phrases.
    """
    cleaned = re.sub(
        r"^(Optimized research query:|Enhanced query:)\s*",
        "",
        query,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(r'^"(.*)"$', r"\1", cleaned.strip())

    return cleaned.strip()


def enhance_search_query(query: str) -> str:
    """
    Enhance the search query to improve relevance of results.
    """
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
    """
    Generate clarifying questions using DSPy's ChainOfThought module.
    """
    response = clarify_questions_module.forward(task_description=task_description)
    questions = response.questions if hasattr(response, "questions") else ""
    return [q.strip() for q in questions.split("\n") if q.strip()]


def enhance_query_with_dspy(
    original_query: str, clarify_answers: List[Dict[str, str]]
) -> str:
    """
    Enhance the original query based on clarifying answers using DSPy's ChainOfThought module.
    """
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
    """
    Analyze research papers using DSPy's ChainOfThought module.
    """
    papers_formatted = "\n".join(
        [f"- {paper.title} ({paper.link})" for paper in research_papers]
    )
    response = analysis_module.forward(
        task_description=task_description, state=state, research_papers=papers_formatted
    )
    return response.analysis if hasattr(response, "analysis") else ""


def synthesize_information(
    task_description: str, state: str, research_papers: List[Paper]
) -> str:
    """
    Synthesize information from research papers using DSPy's ChainOfThought module.
    """
    papers_formatted = "\n".join(
        [f"- {paper.title} ({paper.link})" for paper in research_papers]
    )
    response = synthesize_module.forward(
        task_description=task_description, state=state, research_papers=papers_formatted
    )
    return response.get("synthesis", "")


def conclude_research(
    task_description: str, state: str, research_papers: List[Paper]
) -> str:
    """
    Provide a comprehensive conclusion based on research papers using DSPy's ChainOfThought module.
    """
    papers_formatted = "\n".join(
        [f"- {paper.title} ({paper.link})" for paper in research_papers]
    )
    response = conclude_module.forward(
        task_description=task_description, state=state, research_papers=papers_formatted
    )
    return response.get("conclusion", "")


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

        elif state == "Research":
            enhanced_query = enhance_query_with_dspy(
                original_query=task_description,
                clarify_answers=input_data.get("clarify_answers", []),
            )
            papers = fetch_research_papers(enhanced_query, max_results=20)
            logger.info(f"Fetched {len(papers)} research papers")
            return {
                "state": "Research",
                "research_papers": papers,
                "current_steps": state_substeps.get(state, []),
            }

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

        elif state in ["Synthesize", "Conclude"]:
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

            if state == "Synthesize":
                synthesis = synthesize_information(
                    task_description, state, research_papers
                )
                response = synthesis
            elif state == "Conclude":
                conclusion = conclude_research(task_description, state, research_papers)
                response = conclusion
            else:
                response = ""

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
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
