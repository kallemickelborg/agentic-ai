from fastapi import FastAPI, Body
from pydantic import BaseModel
import openai
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import logging
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

app = FastAPI()

origins = ["https://agentic-ai-frontend.onrender.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Logging
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

class Task(BaseModel):
    state: str
    input_data: dict
    task_description: str
    research_papers: list[Paper] = []
    # Removed clarifying_questions field as it's not being used

# StateFlow framework to reflect research process
state_transitions = {
    "Init": "Clarify",
    "Clarify": "Research",
    "Research": "Analyze",
    "Analyze": "Synthesize",
    "Synthesize": "Conclude",
    "Conclude": "End"
}

# Define substeps for each state
state_substeps = {
    "Init": [
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

# Load environment variables from .env file
load_dotenv()

# Securely set your OpenAI API key using environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    raise EnvironmentError("OpenAI API key not found.")

client = OpenAI()

def fetch_research_papers(query: str, max_results: int = 20):
    """
    Fetch research papers related to the query using PubMed E-utilities API.
    """
    logger.info(f"Fetching research papers for query: '{query}'")
    
    # PubMed E-utilities API URL
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        'db': 'pubmed',
        'term': query,
        'retmax': max_results,
        'retmode': 'json'
    }
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch research papers: {response.status_code}")
        return []
    
    data = response.json()
    id_list = data.get('esearchresult', {}).get('idlist', [])
    
    if not id_list:
        logger.info("No research papers found.")
        return []
    
    # Fetch details for each paper
    ids = ','.join(id_list)
    details_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    details_params = {
        'db': 'pubmed',
        'id': ids,
        'retmode': 'json'
    }
    details_response = requests.get(details_url, params=details_params)
    
    if details_response.status_code != 200:
        logger.error(f"Failed to fetch research paper details: {details_response.status_code}")
        return []
    
    details_data = details_response.json()
    papers = []
    
    for uid in id_list:
        item = details_data.get('result', {}).get(uid, {})
        title = item.get('title', 'No title available')
        link = f"https://pubmed.ncbi.nlm.nih.gov/{uid}"
        authors = [
            Author(name=author.get('name', 'Unknown'))
            for author in item.get('authors', [])
        ]
        published_date = item.get('pubdate', 'Date not available')
        
        papers.append(
            Paper(
                title=title,
                link=link,
                authors=authors,
                published_date=published_date
            )
        )
    
    logger.info(f"Successfully fetched {len(papers)} research papers.")
    return papers

def query_openai(prompt: str, sources: list):
    """
    Query OpenAI with the given prompt and sources.
    """
    logger.info("Sending prompt to OpenAI...")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant. When providing responses, "
                        "please break down key insights into bullet points, and for each bullet point, "
                        "include the associated reference citation (link)."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000  # Increase if necessary
        )
        logger.info("Received response from OpenAI.")
        return response.choices[0].message['content'].strip()
    except openai.error.OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        return "An error occurred while communicating with OpenAI."

def query_openai_questions(prompt: str):
    logger.info(f"Querying OpenAI with prompt: {prompt}")
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        questions_text = response.choices[0].message.content.strip()
        logger.info(f"OpenAI response: {questions_text}")
        questions = questions_text.split('\n')
        return [q.strip() for q in questions if q.strip()]
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return ["An error occurred while generating questions."]

def enhance_query(original_query: str, answers: list):
    logger.info(f"Enhancing query. Original: {original_query}, Answers: {answers}")
    
    prompt = f"Original research query: {original_query}\n\n"
    prompt += "Clarifying questions and answers:\n"
    for answer in answers:
        prompt += f"Q: {answer.get('question')}\nA: {answer.get('answer')}\n"
    prompt += "\nBased on the original query and the answers to the clarifying questions, formulate a new, optimized research query."

    logger.info(f"Sending prompt to OpenAI: {prompt}")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        enhanced_query = response.choices[0].message['content'].strip()
        logger.info(f"Enhanced query from OpenAI: {enhanced_query}")
        return enhanced_query
    except openai.error.OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
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

        if state == "Init":
            # Transition from Init to Clarify
            next_state = "Clarify"
            current_steps = state_substeps.get(state, [])
            logger.info(f"Transitioning from 'Init' to '{next_state}'")
            return {
                "state": next_state,
                "response": "Analyzing your prompt to generate clarifying questions.",
                "current_steps": current_steps
            }
        
        elif state == "Clarify":
            if not input_data.get("clarify_answers"):
                # Generate clarifying questions
                prompt = f"You are an Agentic AI Dietician. Ask 2-3 critical follow-up questions that can be answered with 'Yes' or 'No' to make the user's research prompt more specific. Ensure that the questions are strictly yes/no and won't require further elaboration. The user's prompt is: '{task_description}'"
                logger.info(f"Generating clarifying questions. Prompt: {prompt}")
                questions = query_openai_questions(prompt)
                logger.info(f"Generated questions: {questions}")
                current_steps = state_substeps.get(state, [])
                return {
                    "state": "Clarify",
                    "response": "Please answer the following questions to refine your research query:",
                    "questions": questions,
                    "current_steps": current_steps
                }
            else:
                # Process answers and enhance query
                logger.info(f"Processing clarifying answers: {input_data['clarify_answers']}")
                enhanced_query = enhance_query(task_description, input_data.get("clarify_answers", []))
                logger.info(f"Enhanced query: {enhanced_query}")
                next_state = "Research"
                logger.info(f"Transitioning from 'Clarify' to '{next_state}'")
                return {
                    "state": next_state,
                    "response": "Clarification complete. Proceeding to research.",
                    "current_steps": state_substeps.get(next_state, []),
                }
        
        elif state == "Research":
            # Fetch research papers
            enhanced_query = enhance_query(task_description, input_data.get("clarify_answers", []))
            papers = fetch_research_papers(enhanced_query, max_results=20)
            logger.info(f"Fetched {len(papers)} research papers")
            return {
                "state": "Research",
                "response": "Research papers fetched. Please select the papers you want to include.",
                "research_papers": papers,
                "current_steps": state_substeps.get(state, []),
            }
        
        elif state in ["Analyze", "Synthesize", "Conclude"]:
            # Process the current state
            selected_papers_links = input_data.get("selected_papers", [])
            if selected_papers_links:
                research_papers = [paper for paper in research_papers if paper.link in selected_papers_links]
            
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
                "response": "Task completed.",
                "current_steps": state_substeps.get("End", [])
            }

    except Exception as e:
        logger.error(f"Error in solve_task: {str(e)}", exc_info=True)
        return {
            "state": "End",
            "response": "An unexpected error occurred. Please try again later.",
            "current_steps": state_substeps.get("End", [])
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)