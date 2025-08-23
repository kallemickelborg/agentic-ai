from pydantic import BaseModel
from typing import List, Dict, Optional


class Author(BaseModel):
    name: str


class EvidencePoint(BaseModel):
    title: str
    evidence: str


class Paper(BaseModel):
    title: str
    link: str
    authors: List[Author] = []
    published_date: str = ""
    abstract: Optional[str] = None
    citation_count: int = 0
    peer_reviewed: bool = False
    journal_name: str = ""
    journal_impact_factor: float = 0.0
    sciscore: Optional[float] = None
    study_type: str = ""
    publication_type: List[str] = []
    relevancy_score: Optional[float] = None
    citation_score: Optional[float] = None
    full_text_accessible: bool = False
    full_text_link: Optional[str] = None
    source_type: str = (
        "open_access",
        "abstract_only",
        "requires_access",
    )
    supporting_evidence: Optional[List[EvidencePoint]] = None
    opposing_evidence: Optional[List[EvidencePoint]] = None
    key_findings: Optional[str] = None


class Task(BaseModel):
    state: str
    input_data: dict
    task_description: str
    research_papers: List[Paper] = []
    state_history: List[str] = []
