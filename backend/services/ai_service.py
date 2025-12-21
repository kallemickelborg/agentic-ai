import dspy
from typing import List, Dict, Optional, Tuple
from models.domain import Paper, EvidencePoint
import json


# DSPy Signatures
class ClarifyQuestions(dspy.Signature):
    """Generate clarifying questions for a research topic."""

    task_description = dspy.InputField()
    questions = dspy.OutputField(
        desc="3-5 clarifying questions that can be answered with Yes/No. The questions should be in the format of 'Do you want to know more about ...?'"
    )


class EnhanceQuery(dspy.Signature):
    """Enhance a search query based on clarifying answers."""

    original_query = dspy.InputField()
    clarify_answers = dspy.InputField()
    enhanced_query = dspy.OutputField(desc="An enhanced search query")


class Analysis(dspy.Signature):
    """Analyze research papers in context of the task."""

    task_description = dspy.InputField()
    state = dspy.InputField()
    research_papers = dspy.InputField()
    analysis = dspy.OutputField(desc="Analysis of the research papers")


class Conclude(dspy.Signature):
    """Provide a conclusion based on research."""

    task_description = dspy.InputField()
    state = dspy.InputField()
    research_papers = dspy.InputField()
    conclusion = dspy.OutputField(desc="Comprehensive conclusion")


class PaperEvaluation(dspy.Signature):
    """Evaluate a research paper for both relevance to the query and scientific merit."""

    paper_title = dspy.InputField()
    paper_abstract = dspy.InputField()
    peer_reviewed = dspy.InputField()
    study_type = dspy.InputField()
    user_query = dspy.InputField()
    relevancy_score = dspy.OutputField(
        desc="Numeric score from 1-100 representing how well the paper matches the user's query."
    )
    citation_score = dspy.OutputField(
        desc="Numeric score from 1-100 representing the scientific merit of the paper."
    )


class PaperAnalysis(dspy.Signature):
    """Analyze a single research paper for supporting/opposing evidence."""

    paper_title = dspy.InputField()
    paper_content = dspy.InputField(desc="Full text or abstract of the paper")
    content_type = dspy.InputField(
        desc="Whether this is 'full_text' or 'abstract_only'"
    )
    user_query = dspy.InputField()
    clarifying_context = dspy.InputField()

    supporting_evidence = dspy.OutputField(
        desc="""List of evidence points that support the user's query. Each point must be an object in this exact format:
        [
            {
                "title": "Short descriptive title of the evidence point",
                "evidence": "Detailed evidence with page/section reference"
            },
            ...
        ]
        Example:
        [
            {
                "title": "Vitamin K2 improves metabolic health",
                "evidence": "Study showed significant decrease in waist circumference and fat mass (p. 1246)"
            }
        ]"""
    )
    opposing_evidence = dspy.OutputField(
        desc="""List of evidence points that oppose or limit the user's query. Each point must be an object in this exact format:
        [
            {
                "title": "Short descriptive title of the limitation/opposing evidence",
                "evidence": "Detailed evidence with page/section reference"
            },
            ...
        ]
        Example:
        [
            {
                "title": "Limited effectiveness in elderly population",
                "evidence": "No significant improvements observed in patients over 75 years (p. 18)"
            }
        ]"""
    )
    key_findings = dspy.OutputField(
        desc="Brief summary of the paper's key findings relevant to the query"
    )


class AIService:
    """Service for AI/ML operations using DSPy."""

    def __init__(self):
        # Initialize DSPy modules
        self.clarify_questions_module = dspy.ChainOfThought(ClarifyQuestions)
        self.enhance_query_module = dspy.ChainOfThought(EnhanceQuery)
        self.analysis_module = dspy.ChainOfThought(Analysis)
        self.conclude_module = dspy.ChainOfThought(Conclude)
        self.paper_evaluation_module = dspy.ChainOfThought(PaperEvaluation)

        # Configure paper analysis module with specific parameters
        self.paper_analysis_module = dspy.ChainOfThought(PaperAnalysis)
        self.paper_analysis_module.temperature = 1

        # Example prompt to guide the analysis
        self.paper_analysis_module.preset_prompt = """
Given a research paper's content and a user's query with clarifying context, analyze the paper to extract evidence in a specific format.

For both supporting and opposing evidence, you must return a list of objects, where each object has exactly two fields:
- "title": A short, descriptive title summarizing the evidence point
- "evidence": Detailed evidence with page/section reference

Example format:
{
    "supporting_evidence": [
        {
            "title": "Vitamin K2 improves metabolic health",
            "evidence": "Study showed significant decrease in waist circumference and fat mass (p. 1246)"
        },
        {
            "title": "Positive effects on insulin sensitivity",
            "evidence": "Randomized controlled trial showed improvements in insulin sensitivity markers (p. 1247)"
        }
    ],
    "opposing_evidence": [
        {
            "title": "Limited effectiveness in elderly",
            "evidence": "No significant improvements in patients over 75 years (p. 12)"
        }
    ]
}

Important:
1. Always return evidence as a list of objects, even if there's only one piece of evidence
2. Each evidence point must have both a title and evidence field
3. Make titles clear and informative
4. Include page numbers or section references when available
5. If no evidence is found, return an empty list []
6. Never return plain strings, always use the object format
"""

    def generate_clarifying_questions(self, task_description: str) -> List[str]:
        """Generate clarifying questions using DSPy's ChainOfThought module."""
        response = self.clarify_questions_module.forward(
            task_description=task_description
        )
        questions = response.questions if hasattr(response, "questions") else ""
        return [q.strip() for q in questions.split("\n") if q.strip()]

    def enhance_query_with_dspy(
        self, original_query: str, clarify_answers: List[Dict[str, str]]
    ) -> str:
        """Enhance the original query based on clarifying answers using DSPy's ChainOfThought module."""
        formatted_answers = "\n".join(
            [f"Q: {ans['question']}\nA: {ans['answer']}" for ans in clarify_answers]
        )
        response = self.enhance_query_module.forward(
            original_query=original_query, clarify_answers=formatted_answers
        )
        enhanced_query = (
            response.enhanced_query
            if hasattr(response, "enhanced_query")
            else original_query
        )
        return enhanced_query

    def evaluate_paper(self, paper: Paper, user_query: str) -> Tuple[float, float]:
        """Evaluate a paper for relevance and scientific merit."""
        response = self.paper_evaluation_module(
            paper_title=paper.title,
            paper_abstract=paper.abstract or "",
            peer_reviewed=str(paper.peer_reviewed),
            study_type=paper.study_type or "Unknown",
            user_query=user_query,
        )

        # Parse scores with defaults
        rel_score = 50.0
        cit_score = 50.0

        try:
            rel_score = max(1.0, min(float(response.relevancy_score), 100.0))
        except (ValueError, TypeError):
            rel_score = 50.0

        try:
            cit_score = max(1.0, min(float(response.citation_score), 100.0))
        except (ValueError, TypeError):
            cit_score = 50.0

        return rel_score, cit_score

    def analyze_individual_paper(
        self, paper: Paper, user_query: str, clarifying_context: str
    ) -> dict:
        """Analyze a single paper for supporting and opposing evidence."""
        try:
            response = self.paper_analysis_module(
                paper_title=paper.title,
                paper_abstract=paper.abstract or "",
                user_query=user_query,
                clarifying_context=clarifying_context,
            )

            return {
                "title": paper.title,
                "link": paper.link,
                "supporting_evidence": (
                    response.supporting_evidence
                    if hasattr(response, "supporting_evidence")
                    else ""
                ),
                "opposing_evidence": (
                    response.opposing_evidence
                    if hasattr(response, "opposing_evidence")
                    else ""
                ),
                "key_findings": (
                    response.key_findings if hasattr(response, "key_findings") else ""
                ),
            }
        except Exception as e:
            return {
                "title": paper.title,
                "link": paper.link,
                "supporting_evidence": "Error analyzing supporting evidence.",
                "opposing_evidence": "Error analyzing opposing evidence.",
                "key_findings": "Error analyzing key findings.",
            }

    def analyze_paper_content(
        self,
        paper: Paper,
        content: str,
        content_type: str,
        user_query: str,
        clarifying_context: str,
    ) -> dict:
        """Analyze paper content using full text when available."""
        try:
            response = self.paper_analysis_module(
                paper_title=paper.title,
                paper_content=content,
                content_type=content_type,
                user_query=user_query,
                clarifying_context=clarifying_context,
            )

            # Extract and validate the evidence
            supporting = []
            opposing = []

            # Format supporting evidence
            if hasattr(response, "supporting_evidence"):
                raw_supporting = response.supporting_evidence
                if isinstance(raw_supporting, list):
                    for point in raw_supporting:
                        if (
                            isinstance(point, dict)
                            and "title" in point
                            and "evidence" in point
                        ):
                            supporting.append(
                                {"title": point["title"], "evidence": point["evidence"]}
                            )
                elif isinstance(raw_supporting, str) and raw_supporting.strip():
                    try:
                        parsed = json.loads(raw_supporting)
                        if isinstance(parsed, list):
                            for point in parsed:
                                if (
                                    isinstance(point, dict)
                                    and "title" in point
                                    and "evidence" in point
                                ):
                                    supporting.append(
                                        {"title": point["title"], "evidence": point["evidence"]}
                                    )
                    except json.JSONDecodeError:
                        pass

            # Format opposing evidence
            if hasattr(response, "opposing_evidence"):
                raw_opposing = response.opposing_evidence
                if isinstance(raw_opposing, list):
                    for point in raw_opposing:
                        if (
                            isinstance(point, dict)
                            and "title" in point
                            and "evidence" in point
                        ):
                            opposing.append(
                                {"title": point["title"], "evidence": point["evidence"]}
                            )
                elif isinstance(raw_opposing, str) and raw_opposing.strip():
                    try:
                        parsed = json.loads(raw_opposing)
                        if isinstance(parsed, list):
                            for point in parsed:
                                if (
                                    isinstance(point, dict)
                                    and "title" in point
                                    and "evidence" in point
                                ):
                                    opposing.append(
                                        {"title": point["title"], "evidence": point["evidence"]}
                                    )
                    except json.JSONDecodeError:
                        pass

            findings = (
                response.key_findings if hasattr(response, "key_findings") else ""
            )

            return {
                "title": paper.title,
                "link": paper.link,
                "supporting_evidence": supporting,
                "opposing_evidence": opposing,
                "key_findings": findings,
                "analysis_type": content_type,
            }

        except Exception as e:
            return {
                "title": paper.title,
                "link": paper.link,
                "supporting_evidence": [],
                "opposing_evidence": [],
                "key_findings": "Error during paper analysis.",
                "analysis_type": "error",
            }
