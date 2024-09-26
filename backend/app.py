from fastapi import FastAPI, Body
from pydantic import BaseModel
import openai
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import logging
from dotenv import load_dotenv

app = FastAPI()

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
    task_description: str  # New field for task description
    research_papers: list[Paper] = []  # New field to store research papers
    clarifying_questions: list[str] = []  # Add this field
    # No need to store answers here; they can be part of input_data

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
    """
    Use OpenAI to generate clarifying yes/no questions.
    """
    logger.info(f"Querying OpenAI with prompt: {prompt}")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        questions_text = response.choices[0].message['content'].strip()
        logger.info(f"OpenAI response: {questions_text}")
        questions = questions_text.split('\n')
        return [q.strip() for q in questions if q.strip()]
    except openai.error.OpenAIError as e:
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
def solve_task(task: Task):
    logger.info(f"Received task: {task.dict()}")
    try:
        if task.state == "Init":
            # Transition from Init to Clarify
            next_state = state_transitions.get(task.state, "End")
            current_steps = state_substeps.get(task.state, [])
            logger.info(f"Transitioning from 'Init' to '{next_state}'")
            return {
                "state": next_state,
                "response": "Analyzing your prompt to generate clarifying questions.",
                "current_steps": current_steps
            }
        
        elif task.state == "Clarify":
            if "clarify_answers" not in task.input_data or not task.input_data["clarify_answers"]:
                # Generate clarifying questions
                prompt = f"You are an Agentic AI Dietician. Ask 2-3 critical follow-up questions that can be answered with 'Yes' or 'No' to make the user's research prompt more specific. Ensure that the questions are strictly yes/no and won't require further elaboration. The user's prompt is: '{task.task_description}'"
                logger.info(f"Generating clarifying questions. Prompt: {prompt}")
                questions = query_openai_questions(prompt)
                logger.info(f"Generated questions: {questions}")
                current_steps = state_substeps.get(task.state, [])
                return {
                    "state": "Clarify",
                    "response": "Please answer the following questions to refine your research query:",
                    "questions": questions,
                    "current_steps": current_steps
                }
            else:
                # Process answers and enhance query
                logger.info(f"Processing clarifying answers: {task.input_data['clarify_answers']}")
                enhanced_query = enhance_query(task.task_description, task.input_data.get("clarify_answers", []))
                logger.info(f"Enhanced query: {enhanced_query}")
                # Use the enhanced query to fetch research papers
                papers = fetch_research_papers(enhanced_query, max_results=20)
                logger.info(f"Fetched {len(papers)} research papers")
                task.research_papers = papers
                next_state = "Research"
                logger.info(f"Transitioning from 'Clarify' to '{next_state}'")
                return {
                    "state": next_state,
                    "response": "Research papers fetched based on your refined query. Please select the papers you want to include and click 'Proceed with Selected Papers'.",
                    "research_papers": papers,
                    "current_steps": state_substeps.get(next_state, []),
                }
        
        elif task.state == "Research":
            # Combine user's prompt with answers to generate enhanced query
            enhanced_query = enhance_query(task.task_description, task.input_data.get("clarify_answers", []))
            # logger.info(f"Enhanced query for research: {enhanced_query}")
            papers = fetch_research_papers(enhanced_query, max_results=20)
            logger.info(f"Fetched {len(papers)} research papers")
            task.research_papers = papers
            # Stay in 'Research' state to allow paper selection
            next_state = task.state  # Do not transition yet
            logger.info(f"Staying in 'Research' state to allow paper selection")
            return {
                "state": next_state,
                "response": "Research papers fetched. Please select the papers you want to include and click 'Proceed with Selected Papers'.",
                "research_papers": papers,
                "current_steps": state_substeps.get(task.state, []),
            }
        
        elif task.state in ["Analyze", "Synthesize", "Conclude"]:
            # Get selected papers from input_data
            selected_papers_links = task.input_data.get("selected_papers", [])
            if selected_papers_links:
                task.research_papers = [paper for paper in task.research_papers if paper.link in selected_papers_links]
                logger.info(f"Using {len(task.research_papers)} selected research papers for '{task.state}' step.")
            else:
                logger.info(f"No selected papers provided. Using all {len(task.research_papers)} research papers for '{task.state}' step.")
            
            prompt = (
                f"Task Description: {task.task_description}\n"
                f"Current State: {task.state}\n"
                f"Input Data: {task.input_data}\n"
                f"Research Papers:\n"
            )
            for paper in task.research_papers:
                prompt += f"- {paper.title} ({paper.link})\n"
            
            if task.state == "Analyze":
                prompt += "Provide an analysis based on the above research papers."
            elif task.state == "Synthesize":
                prompt += "Synthesize the information from the above research papers."
            elif task.state == "Conclude":
                prompt += (
                    "\nBased on the above research, please provide a comprehensive conclusion.\n"
                    "Break down the key insights into bullet points, and for each bullet point, "
                    "include the associated reference citation (link)."
                    "Do NOT use any other information other than the research papers in question."
                    "If no information is found to answer the question, please respond with 'No information found in the research papers provided.'"
                )
            
            current_steps = state_substeps.get(task.state, [])
            logger.info(f"Executing {task.state} steps:")
            for step in current_steps:
                logger.info(f"Step: {step}")
                # Implement actual step execution logic here
            
            action = query_openai(prompt, sources=[paper.link for paper in task.research_papers])
            next_state = state_transitions.get(task.state, "End")
            logger.info(f"Transitioning from '{task.state}' to '{next_state}'")
            return {
                "state": next_state,
                "response": action,
                "current_steps": current_steps
            }
        
        else:
            logger.warning(f"Unknown state '{task.state}'. Ending task.")
            return {
                "state": "End",
                "response": "Task completed.",
                "current_steps": state_substeps.get("End", [])
            }
    except openai.error.AuthenticationError:
        logger.error("OpenAI Authentication Error: Invalid API key.")
        return {
            "state": "End",
            "response": "Authentication error. Please check your API key.",
            "current_steps": state_substeps.get("End", [])
        }
    except Exception as e:
        logger.error(f"Error in solve_task: {str(e)}", exc_info=True)
        return {
            "state": "End",
            "response": "An unexpected error occurred. Please try again later.",
            "current_steps": state_substeps.get("End", [])
        }

# Allow CORS for the frontend
origins = [
    "http://localhost:3000",  # For local development
    "https://agentic-ai.netlify.app",  # Replace with your actual Netlify URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)