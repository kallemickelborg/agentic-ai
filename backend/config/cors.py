from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app):
    """Configure CORS middleware for the FastAPI application."""

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
