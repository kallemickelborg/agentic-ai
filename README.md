# Stateful AI Agent for Knowledge Extraction in Medical Research

A simple human-in-the-loop multi-state AI agent designed to answer medical research questions with research papers from PubMed. This project is based on the [StateFlow](https://arxiv.org/abs/2403.11322) research paper, using states with cascading function calling in a research pipeline. The benefit of using states is that it allows for a more structured and modular approach to the research process, making it easier to manage and scale. Using states is a different but highly effective approach for building AI agents, allowing for more deterministic and predictable behavior. The function calling is implemented using [FastAPI](https://fastapi.tiangolo.com/), [OpenAI API](https://openai.com/api/) and [DSPy](https://dspy.ai/) to process Chain-of-Thought reasoning for prompting the LLM. The backend is interfaced using a frontend implemented in [Next.js](https://nextjs.org/) and [Tailwind CSS](https://tailwindcss.com/).

## Table of Contents

- [Tech Stack](#tech-stack)
- [Overview](#overview)
- [Functions](#functions)
- [Roadmap](#roadmap)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Development](#development)
- [Deployment](#deployment)
- [Contributing](#contributing)

## Tech Stack

- Frontend: [Next.js](https://nextjs.org/) (React framework)
- Backend: [Python](https://www.python.org/) with [FastAPI](https://fastapi.tiangolo.com/) (Python framework)
- Data Validation: [Pydantic](https://docs.pydantic.dev/) (Type checking)
- Language Model: [OpenAI API](https://openai.com/blog/openai-api) (GPT models)
- Prompting Framework: [DSPy](https://dspy.ai/) (Chain-of-Thought reasoning)
- Styling: [Tailwind CSS](https://tailwindcss.com/), [Radix UI](https://www.radix-ui.com/primitives) (UI components)
- Animation: [Framer Motion](https://www.framer.com/motion/)
- Deployment: [Render](https://render.com/)

## Overview

This project implements a number of different Python frameworks and libraries to create a multi-state AI agent for knowledge extraction in medical research. The agent has been designed with 5 states in mind; Start, Clarify, Research, Analyze, and Conclusion. Each state has a number of functions that are used to extract knowledge from the research papers. Below is a list of the functions for each state.

### Functions

#### State 1: Start

- `solve_task`: Initializes the research process and transitions to the Clarify state

#### State 2: Clarify

- `generate_clarifying_questions`: Generates relevant questions to better understand the user's research needs
- `ClarifyQuestions` (DSPy Signature): Processes the task description to generate targeted clarifying questions

#### State 3: Research

- `fetch_research_papers`: Retrieves research papers from PubMed based on the query
- `process_research_papers`: Processes and evaluates retrieved papers
- `enhance_search_query`: Optimizes the search query for better results
- `enhance_query_with_dspy`: Enhances the query using clarifying answers
- `check_paper_accessibility`: Checks if papers are openly accessible
- `PaperEvaluation` (DSPy Signature): Evaluates papers for relevance and scientific merit
- `relevancy_score`: Ranks each research paper based on its relevance to the user's query
- `citation_score`: Ranks each research paper based on its methdology, study design, and other factors

#### State 4: Analyze

- `analyze_papers`: Performs comprehensive analysis of selected papers, altogether
- `analyze_paper_content`: Analyzes individual paper content using full text or abstract
- `fetch_pdf_content`: Retrieves and extracts text from PDF papers using URL
- `fetch_pmc_paper_content`: Fetches paper content from PubMed Central
- `PaperAnalysis` (DSPy Signature): Extracts supporting and opposing evidence from papers

#### State 5: Conclude (WIP)

- `conclude_research`: Generates final conclusions based on analyzed papers
- `Conclude` (DSPy Signature): Processes all findings to create a comprehensive conclusion

## Roadmap

This project is a work in progress, and so needs more work to be fully functional. Below is a list of tasks.

- [ ] Finish the Conclusion state placeholder
- [ ] Add functions for Conclusion state
- [ ] Refactor functions for each state for better readability and maintainability
- [ ] Add more descriptive logging and error handling for debugging and troubleshooting
- [ ] Improve the UI/UX for the frontend for better user experience and legibility
- [ ] Add proper DSPy instantiation of prompt optimization

## Getting Started

### Prerequisites

- Node.js (v14 or later)
- Python (v3.7 or later)
- OpenAI API key

### Installation

1. Clone the repository:

   ```
   git clone https://github.com/kallemickelborg/agentic-ai.git
   cd agentic-ai
   ```

2. Set up the frontend:

   ```
   cd frontend
   npm install
   ```

3. Set up the backend:

   ```
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the backend directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Development

1. Start the backend server:

   ```
   cd backend
   uvicorn app:app --reload
   ```

2. In a new terminal, start the frontend development server:

   ```
   cd frontend
   npm run dev
   ```

3. Open your browser and navigate to `http://localhost:3000`

## Deployment

This project is configured for deployment on Render. Follow these steps:

1. Fork this repository to your GitHub account.
2. Create a new Web Service on Render, connecting to your forked repository.
3. Set up the environment variables in Render, including your OpenAI API key.
4. Deploy the service on Render.

For detailed deployment instructions, refer to the [Render documentation](https://render.com/docs).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
