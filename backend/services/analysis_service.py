import datetime
import json
from typing import List, Dict, Any
from models.domain import Paper
from services.ai_service import AIService
from services.pdf_service import PDFService
from core.logging import logger


class AnalysisService:
    """Service for analyzing research papers and extracting evidence."""

    def __init__(self):
        self.ai_service = AIService()
        self.pdf_service = PDFService()

    def analyze_individual_paper(
        self, paper: Paper, user_query: str, clarifying_context: str
    ) -> dict:
        """Analyze a single paper for supporting and opposing evidence."""
        return self.ai_service.analyze_individual_paper(
            paper, user_query, clarifying_context
        )

    async def analyze_paper_content(
        self, paper: Paper, user_query: str, clarifying_context: str
    ) -> Dict[str, Any]:
        """Analyze paper content using full text when available, otherwise use abstract."""
        try:
            # Extract PMID from the PubMed URL
            pmid = paper.link.split("/")[-1]
            logger.info(f"Analyzing paper {paper.title} (PMID: {pmid})")

            # Try to get full text content
            success = False
            content = None

            if paper.source_type == "open_access":
                success, content = await self.pdf_service.fetch_pmc_paper_content(pmid)
                logger.info(f"Full text fetched for paper {paper.title}: {success}")

            # Use full text if available, otherwise fall back to abstract
            analysis_text = content if success else paper.abstract
            content_type = "full_text" if success else "abstract_only"

            if not analysis_text:
                logger.warning(f"No content available for paper {paper.title}")
                return {
                    "title": paper.title,
                    "link": paper.link,
                    "supporting_evidence": [],
                    "opposing_evidence": [],
                    "key_findings": "No content available for analysis.",
                    "analysis_type": "error",
                }

            # Analyze content using DSPy
            result = self.ai_service.analyze_paper_content(
                paper, analysis_text, content_type, user_query, clarifying_context
            )

            # Add content type context to the response
            content_note = f" Analysis is based on {content_type} content type."

            result["key_findings"] = result.get("key_findings", "") + content_note

            logger.info(
                f"Final analysis result for {paper.title}: {json.dumps(result, indent=2)}"
            )
            return result

        except Exception as e:
            logger.error(f"Error analyzing paper content for {paper.title}: {str(e)}")
            return {
                "title": paper.title,
                "link": paper.link,
                "supporting_evidence": [],
                "opposing_evidence": [],
                "key_findings": "Error analyzing paper content.",
                "analysis_type": "error",
            }

    async def analyze_papers(
        self,
        task_description: str,
        state: str,
        research_papers: List[Paper],
        clarify_answers: List[Dict[str, str]] = [],
    ) -> dict:
        """Analyze research papers and provide detailed analysis for each paper."""
        logger.info(f"Analyzing papers for task: {task_description}")

        # Format clarifying context
        clarifying_context = "\n".join(
            [f"Q: {ans['question']}\nA: {ans['answer']}" for ans in clarify_answers]
        )

        # Analyze each paper individually with full text when available
        paper_analyses = []
        for paper in research_papers:
            try:
                analysis = await self.analyze_paper_content(
                    paper=paper,
                    user_query=task_description,
                    clarifying_context=clarifying_context,
                )
                logger.info(
                    f"Individual paper analysis result: {json.dumps(analysis, indent=2)}"
                )

                # Ensure the analysis has all required fields
                if not all(
                    key in analysis
                    for key in [
                        "supporting_evidence",
                        "opposing_evidence",
                        "key_findings",
                    ]
                ):
                    logger.warning(
                        f"Missing required fields in analysis for paper: {paper.title}"
                    )
                    continue

                paper_analyses.append(analysis)

            except Exception as e:
                logger.error(f"Error analyzing paper {paper.title}: {str(e)}")
                # Add error result for this paper
                paper_analyses.append(
                    {
                        "title": paper.title,
                        "link": paper.link,
                        "supporting_evidence": "Error analyzing paper.",
                        "opposing_evidence": "Error analyzing paper.",
                        "key_findings": "Error analyzing paper.",
                        "analysis_type": "error",
                    }
                )

        # Generate overall analysis using existing module
        papers_formatted = "\n".join(
            [f"- {paper.title} ({paper.link})" for paper in research_papers]
        )

        try:
            overall_analysis = self.ai_service.analysis_module.forward(
                task_description=task_description,
                state=state,
                research_papers=papers_formatted,
            )
            overall_text = (
                overall_analysis.analysis
                if hasattr(overall_analysis, "analysis")
                else ""
            )
        except Exception as e:
            logger.error(f"Error generating overall analysis: {str(e)}")
            overall_text = "Error generating overall analysis."

        result = {
            "state": "Analyze",  # Ensure we stay in Analyze state
            "paper_analyses": paper_analyses,
            "overall_analysis": overall_text,
            "total_papers_analyzed": len(paper_analyses),
            "analysis_timestamp": datetime.datetime.now().isoformat(),
            "analysis_complete": True,  # Add flag to indicate analysis is complete
            "can_proceed": True,  # Add flag to indicate user can proceed to next state
        }

        logger.info(f"Final analysis result structure: {json.dumps(result, indent=2)}")
        return result
