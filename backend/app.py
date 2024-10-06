from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import openai
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import logging
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import urllib.parse
import re
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

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
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Author(BaseModel):
    name: str

class Paper(BaseModel):
    title: str
    link: str
    authors: list[Author] = []
    published_date: str = ""
    abstract: Optional[str] = None

class Task(BaseModel):
    state: str
    input_data: dict
    task_description: str
    research_papers: list[Paper] = []

state_transitions = {
    "Start": "Clarify",
    "Clarify": "Research",
    "Research": "Analyze",
    "Analyze": "Synthesize",
    "Synthesize": "Conclude",
    "Conclude": "End"
}

# Might need to remove this
state_substeps = {
    "Start": [
        "Initializing the research assistant.",
        "Setting up the environment."
    ],
    "Clarify": [
        "Analyzing the prompt for specificity.",
        "Generating clarifying questions."
    ],
    "Research": [
        "Optimizing query for optimal findings.",
        "Querying medical publications.",
        "Finding relevant research papers for the prompt."
    ],
    "Analyze": [
        "Analyzing the fetched research papers.",
        "Extracting key insights and data."
    ],
    "Synthesize": [
        "Synthesizing information from analysis.",
        "Compiling comprehensive insights."
    ],
    "Conclude": [
        "Formulating the final conclusion based on research.",
        "Ensuring all points are covered comprehensively."
    ],
    "End": [
        "Task completed successfully."
    ]
}

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    raise EnvironmentError("OpenAI API key not found.")

client = OpenAI()

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
        'db': 'pubmed',
        'term': enhanced_query,
        'retmax': max_results,
        'sort': 'relevance',
        'retmode': 'json',
        'usehistory': 'y'
    }
    
    full_search_url = search_url + '?' + urllib.parse.urlencode(search_params)
    logger.info(f"Full PubMed search URL: {full_search_url}")

    search_response = requests.get(search_url, params=search_params)
    
    if search_response.status_code != 200:
        logger.error(f"Failed to fetch research papers: {search_response.status_code}")
        logger.error(f"Response content: {search_response.text}")
        return []
    
    search_data = search_response.json()
    logger.info(f"Search response: {search_data}")
    
    id_list = search_data.get('esearchresult', {}).get('idlist', [])
    query_key = search_data.get('esearchresult', {}).get('querykey')
    web_env = search_data.get('esearchresult', {}).get('webenv')
    
    if not id_list:
        logger.info("No research papers found.")
        raise HTTPException(status_code=204, detail="No research papers found")
    
    logger.info(f"Number of papers found: {len(id_list)}")
    
    efetch_url = f"{base_url}efetch.fcgi"
    efetch_params = {
        'db': 'pubmed',
        'query_key': query_key,
        'WebEnv': web_env,
        'retmode': 'xml',
        'retmax': max_results
    }
    efetch_response = requests.get(efetch_url, params=efetch_params)
    
    if efetch_response.status_code != 200:
        logger.error(f"Failed to fetch research paper details: {efetch_response.status_code}")
        logger.error(f"Response content: {efetch_response.text}")
        return []
    
    root = ET.fromstring(efetch_response.content)
    papers = []
    
    for article in root.findall('.//PubmedArticle'):
        title_elem = article.find('.//ArticleTitle')
        title = title_elem.text if title_elem is not None else 'No title available'
        
        abstract_elem = article.find('.//AbstractText')
        abstract = abstract_elem.text if abstract_elem is not None else ''
        
        pmid_elem = article.find('.//PMID')
        pmid = pmid_elem.text if pmid_elem is not None else 'No PMID available'
        
        authors = [
            f"{author.find('LastName').text if author.find('LastName') is not None else ''} "
            f"{author.find('ForeName').text if author.find('ForeName') is not None else ''}".strip()
            for author in article.findall('.//Author')
        ]
        
        pub_date = article.find('.//PubDate')
        if pub_date is not None:
            year = pub_date.find('Year')
            month = pub_date.find('Month')
            day = pub_date.find('Day')
            published_date = f"{year.text if year is not None else ''}-{month.text if month is not None else ''}-{day.text if day is not None else ''}"
        else:
            published_date = 'Date not available'
        
        papers.append(
            Paper(
                title=title,
                link=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}",
                authors=[Author(name=author) for author in authors],
                published_date=published_date,
                abstract=abstract
            )
        )
    
    logger.info(f"Successfully fetched and parsed {len(papers)} research papers.")
    return papers

def clean_query(query: str) -> str:
    """
    Clean the query by removing any AI-generated prefixes or unwanted phrases.
    """
    cleaned = re.sub(r'^(Optimized research query:|Enhanced query:)\s*', '', query, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'^"(.*)"$', r'\1', cleaned.strip())
    
    return cleaned.strip()

def enhance_search_query(query: str) -> str:
    """
    Enhance the search query to improve relevance of results.
    """
    # Remove any text within square brackets
    cleaned_query = re.sub(r'\[.*?\]', '', query).strip()
    
    # Split the query into words
    words = cleaned_query.split()
    
    # Combine words into phrases (2-3 words) and individual words
    phrases = []
    for i in range(len(words)):
        phrases.append(words[i])
        if i < len(words) - 1:
            phrases.append(f'"{words[i]} {words[i+1]}"')
        if i < len(words) - 2:
            phrases.append(f'"{words[i]} {words[i+1]} {words[i+2]}"')
    
    # Join phrases with OR
    enhanced_query = " OR ".join(phrases)
    
    # Add date restriction
    enhanced_query += " AND (\"last 5 years\"[PDat])"
    
    return enhanced_query

def query_openai(prompt: str):
    """
    Query OpenAI with the given prompt.
    """
    logger.info("Sending prompt to OpenAI...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024
        )
        logger.info("Received response from OpenAI.")
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "An error occurred while processing your request."

def query_openai_questions(prompt: str):
    logger.info(f"Querying OpenAI with prompt: {prompt}")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=256
        )
        questions_text = response.choices[0].message.content.strip()
        logger.info(f"OpenAI response: {questions_text}")
        questions = questions_text.split('\n')
        return [q.strip() for q in questions if q.strip()]
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return ["An error occurred while generating questions."]

def enhance_query(original_query: str, clarify_answers: List[Dict[str, str]]) -> str:
    logger.info(f"Enhancing query. Original: {original_query}, Answers: {clarify_answers}")
    prompt = f"""Original research query: {original_query}
Clarifying questions and answers:
"""
    for answer in clarify_answers:
        prompt += f"Q: {answer['question']}\nA: {answer['answer']}\n"
    
    prompt += "Based on the original query and the answers to the clarifying questions, formulate a new, optimized research query."
    
    logger.info(f"Sending prompt to OpenAI: {prompt}")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that optimizes research queries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=256
        )
        enhanced_query = response.choices[0].message.content.strip()
        logger.info(f"Enhanced query: {enhanced_query}")
        return enhanced_query
    except Exception as e:
        logger.error(f"Error in enhance_query: {str(e)}")
        return original_query

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
            return {
                "state": next_state,
                "current_steps": current_steps
            }
        
        elif state == "Clarify":
            prompt = f"""
                Given the research topic: "{task_description}", generate 3-5 clarifying questions that can be answered with a simple 'Yes' or 'No'.

                These questions should help narrow down the scope of the research and clarify the user's specific interests within the topic.

                Each question should:
                1. Be directly related to the research topic
                2. Be answerable with only 'Yes' or 'No'
                3. Start with words like 'Are', 'Is', 'Do', 'Does', 'Can', 'Will', or 'Should'
                4. Help focus the research direction

                Example format:
                1. Are you interested in [specific aspect of the topic]?
                2. Do you want to focus on [particular area within the topic]?
                3. Should the research include [specific consideration]?

                Please generate the questions now:
                """
            logger.info(f"Generating clarifying questions. Prompt: {prompt}")
            questions = query_openai_questions(prompt)
            logger.info(f"Generated questions: {questions}")
            current_steps = state_substeps.get(state, [])
            return {
                "state": "Clarify",
                "questions": questions,
                "current_steps": current_steps
            }
        
        elif state == "Research":
            enhanced_query = enhance_query(task_description, input_data.get("clarify_answers", []))
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
                    "current_steps": []
                }
            
            research_papers = [paper for paper in research_papers if paper.link in selected_papers_links]
            if not research_papers:
                logger.warning("Selected papers not found in research_papers.")
                return {
                    "state": "Error",
                    "error_message": "Selected papers not found for analysis.",
                    "current_steps": []
                }
            
            if len(research_papers) < 2:
                logger.warning("Not enough papers selected for a conclusive analysis.")
                return {
                    "state": "Error",
                    "error_message": "Based on the papers, not enough information is provided to conclude anything based on the prompt.",
                    "current_steps": []
                }
            
            prompt = f"Task Description: {task_description}\nCurrent State: {state}\n"
            for paper in research_papers:
                prompt += f"- {paper.title} ({paper.link})\n"
            
            prompt += "Provide an analysis based on the above research papers."
            
            action = query_openai(prompt)
            
            if len(action.split()) < 50:
                logger.warning("Analysis is not conclusive.")
                return {
                    "state": "Error",
                    "error_message": "Based on the papers, not enough information is provided to conclude anything based on the prompt.",
                    "current_steps": []
                }
            
            next_state = state_transitions.get(state, "End")
            logger.info(f"Transitioning from '{state}' to '{next_state}'")
            return {
                "state": next_state,
                "response": action,
                "current_steps": state_substeps.get(state, [])
            }
        
        elif state in ["Synthesize", "Conclude"]:
            selected_papers_links = input_data.get("selected_papers", [])
            if not selected_papers_links:
                logger.warning("No papers selected for analysis.")
                return {
                    "state": "Error",
                    "error_message": "No papers have been selected for analysis.",
                    "current_steps": []
                }
            
            research_papers = [paper for paper in research_papers if paper.link in selected_papers_links]
            if not research_papers:
                logger.warning("Selected papers not found in research_papers.")
                return {
                    "state": "Error",
                    "error_message": "Selected papers not found for analysis.",
                    "current_steps": []
                }
            
            prompt = f"Task Description: {task_description}\nCurrent State: {state}\n"
            for paper in research_papers:
                prompt += f"- {paper.title} ({paper.link})\n"
            
            if state == "Analyze":
                prompt += "Provide an analysis based on the above research papers."
            elif state == "Synthesize":
                prompt += "Synthesize the information from the above research papers."
            elif state == "Conclude":
                prompt += "Based on the above research, provide a comprehensive conclusion."
            
            action = query_openai(prompt)
            
            if len(action.split()) < 50:
                logger.warning("Analysis is not conclusive.")
                return {
                    "state": "Error",
                    "error_message": "Based on the papers, not enough information is provided to conclude anything based on the prompt.",
                    "current_steps": []
                }
            
            next_state = state_transitions.get(state, "End")
            logger.info(f"Transitioning from '{state}' to '{next_state}'")
            return {
                "state": next_state,
                "response": action,
                "current_steps": state_substeps.get(state, [])
            }
        
        else:
            logger.warning(f"Unknown state '{state}'. Ending task.")
            return {
                "state": "End",
                "current_steps": state_substeps.get("End", [])
            }
    
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