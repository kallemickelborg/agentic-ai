from typing import List
from models.domain import Paper
from services.ai_service import AIService


class ConclusionService:
    """Service for generating conclusions from research papers."""

    def __init__(self):
        self.ai_service = AIService()

    def conclude_research(
        self, task_description: str, state: str, research_papers: List[Paper]
    ) -> str:
        """Provide a comprehensive conclusion based on research papers using DSPy's ChainOfThought module."""
        papers_formatted = "\n".join(
            [f"- {paper.title} ({paper.link})" for paper in research_papers]
        )
        response = self.ai_service.conclude_module.forward(
            task_description=task_description,
            state=state,
            research_papers=papers_formatted,
        )
        return response.get("conclusion", "")
