# Agentic AI Playground
## Creating a medical research assistant for nutrition using layered AI agents

A working playground for a multilayer AI agent, designed to assist with nutrition research. This project demonstrates the integration of OpenAI's GPT models with a Next.js frontend and a FastAPI backend, all deployed on Render.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Development](#development)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Overview

This project implements an AI-powered nutrition research assistant. It uses a multi-step process to clarify research queries, fetch relevant scientific papers, and provide analysis and synthesis of the information.

## Features

- Interactive research query refinement
- Automated scientific paper retrieval from PubMed
- AI-driven analysis and synthesis of research findings
- Responsive and intuitive user interface

## Tech Stack

- Frontend: [Next.js](https://nextjs.org/) (React framework)
- Backend: [FastAPI](https://fastapi.tiangolo.com/) (Python framework)
- AI: [OpenAI API](https://openai.com/blog/openai-api) (GPT models)
- Deployment: [Render](https://render.com/)
- Styling: [Tailwind CSS](https://tailwindcss.com/)
- Animation: [Framer Motion](https://www.framer.com/motion/)

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
