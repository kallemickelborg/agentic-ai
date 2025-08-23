from typing import List, Dict, Any
from fastapi.responses import StreamingResponse
import json
from models.domain import Task, Paper
from services.state_service import StateService
from services.research_service import ResearchService
from services.analysis_service import AnalysisService
from services.clarification_service import ClarificationService
from services.conclusion_service import ConclusionService
from core.logging import logger


class TaskService:
    """Main service for orchestrating task processing across different states."""

    def __init__(self):
        self.state_service = StateService()
        self.research_service = ResearchService()
        self.analysis_service = AnalysisService()
        self.clarification_service = ClarificationService()
        self.conclusion_service = ConclusionService()

    async def process_task(self, task: Task) -> Any:
        """Process a task based on its current state."""
        try:
            # Get direction from input_data
            direction = task.input_data.get("direction", "forward")

            # For backward transitions, just update the state without executing functions
            if direction == "backward":
                return await self._handle_backward_transition(task)

            # Forward transitions continue with normal function execution
            if task.state == "Start":
                return await self._handle_start_state(task)
            elif task.state == "Clarify":
                return await self._handle_clarify_state(task)
            elif task.state == "Research":
                return await self._handle_research_state(task)
            elif task.state == "Analyze":
                return await self._handle_analyze_state(task)
            elif task.state == "Conclude":
                return await self._handle_conclude_state(task)
            else:
                logger.warning(f"Unknown state '{task.state}'. Ending task.")
                return {
                    "state": "Start",
                    "current_steps": self.state_service.get_state_substeps("Start"),
                    "state_history": [],
                }

        except Exception as e:
            logger.error(f"Error in task service: {str(e)}")
            raise

    async def _handle_backward_transition(self, task: Task) -> dict:
        """Handle backward state transitions."""
        # Update state history
        if task.state_history:
            task.state_history.pop()  # Remove current state

        # Update state based on current state
        if task.state == "Clarify":
            return {
                "state": "Start",
                "current_steps": self.state_service.get_state_substeps("Start"),
                "state_history": task.state_history,
            }
        elif task.state == "Research":
            return {
                "state": "Clarify",
                "current_steps": self.state_service.get_state_substeps("Clarify"),
                "state_history": task.state_history,
            }
        elif task.state == "Analyze":
            return {
                "state": "Research",
                "current_steps": self.state_service.get_state_substeps("Research"),
                "state_history": task.state_history,
                "research_papers": task.research_papers,
            }
        elif task.state == "Conclude":
            return {
                "state": "Analyze",
                "current_steps": self.state_service.get_state_substeps("Analyze"),
                "state_history": task.state_history,
                "paper_analyses": task.input_data.get("paper_analyses", []),
            }

    async def _handle_start_state(self, task: Task) -> dict:
        """Handle the Start state."""
        next_state = self.state_service.get_next_state(task.state, "forward")
        return {
            "state": next_state,
            "current_steps": self.state_service.get_state_substeps(task.state),
            "state_history": task.state_history,
        }

    async def _handle_clarify_state(self, task: Task) -> dict:
        """Handle the Clarify state."""
        questions = self.clarification_service.generate_clarifying_questions(
            task.task_description
        )
        logger.info(f"Generated questions: {questions}")
        return {
            "state": self.state_service.get_next_state(task.state, "forward"),
            "questions": questions,
            "current_steps": self.state_service.get_state_substeps(task.state),
            "state_history": task.state_history,
        }

    async def _handle_research_state(self, task: Task) -> StreamingResponse:
        """Handle the Research state."""

        async def generate_research_updates():
            async for update in self.research_service.process_research_papers(
                task.task_description, task.input_data
            ):
                yield f"data: {json.dumps(update)}\n\n"

        return StreamingResponse(
            generate_research_updates(), media_type="text/event-stream"
        )

    async def _handle_analyze_state(self, task: Task) -> dict:
        """Handle the Analyze state."""
        selected_papers_links = task.input_data.get("selected_papers", [])
        if not selected_papers_links:
            logger.warning("No papers selected for analysis.")
            return {
                "state": "Error",
                "error_message": "No papers have been selected for analysis.",
                "current_steps": [],
            }

        research_papers = [
            paper
            for paper in task.research_papers
            if paper.link in selected_papers_links
        ]
        if not research_papers:
            logger.warning("Selected papers not found in research_papers.")
            return {
                "state": "Error",
                "error_message": "Selected papers not found for analysis.",
                "current_steps": [],
            }

        logger.info(f"Starting analysis for {len(research_papers)} papers")
        analysis_result = await self.analysis_service.analyze_papers(
            task.task_description,
            task.state,
            research_papers,
            task.input_data.get("clarify_answers", []),
        )
        logger.info(
            f"Analysis completed, result structure: {json.dumps(analysis_result, indent=2)}"
        )

        if not analysis_result.get("paper_analyses"):
            logger.warning("Analysis produced no results.")
            return {
                "state": "Error",
                "error_message": "Analysis produced no results for the selected papers.",
                "current_steps": [],
            }

        logger.info(
            f"Sending analysis response: {json.dumps(analysis_result, indent=2)}"
        )
        return analysis_result

    async def _handle_conclude_state(self, task: Task) -> dict:
        """Handle the Conclude state."""
        selected_papers_links = task.input_data.get("selected_papers", [])
        if not selected_papers_links:
            logger.warning("No papers selected for conclusion.")
            return {
                "state": "Error",
                "error_message": "No papers have been selected for conclusion.",
                "current_steps": [],
            }

        research_papers = [
            paper
            for paper in task.research_papers
            if paper.link in selected_papers_links
        ]
        if not research_papers:
            logger.warning("Selected papers not found in research_papers.")
            return {
                "state": "Error",
                "error_message": "Selected papers not found for conclusion.",
                "current_steps": [],
            }

        conclusion = self.conclusion_service.conclude_research(
            task.task_description, task.state, research_papers
        )
        if len(conclusion.split()) < 50:
            logger.warning("Response is not conclusive.")
            return {
                "state": "Error",
                "error_message": "Based on the papers, not enough information is provided to conclude anything based on the prompt.",
                "current_steps": [],
            }

        next_state = self.state_service.get_next_state(task.state, "forward")
        logger.info(f"Transitioning from '{task.state}' to '{next_state}'")
        return {
            "state": next_state,
            "response": conclusion,
            "current_steps": self.state_service.get_state_substeps(task.state),
        }
