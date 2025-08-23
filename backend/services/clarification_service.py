import re
from typing import List, Dict
from services.ai_service import AIService


class ClarificationService:
    """Service for generating and handling clarifying questions."""

    def __init__(self):
        self.ai_service = AIService()

    def generate_clarifying_questions(self, task_description: str) -> List[str]:
        """Generate clarifying questions using DSPy's ChainOfThought module."""
        return self.ai_service.generate_clarifying_questions(task_description)

    def clean_query(self, query: str) -> str:
        """Clean the query by removing any AI-generated prefixes or unwanted phrases."""
        cleaned = re.sub(
            r"^(Optimized research query:|Enhanced query:)\s*",
            "",
            query,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r'^"(.*)"$', r"\1", cleaned.strip())
        return cleaned.strip()

    def enhance_search_query(self, query: str) -> str:
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
