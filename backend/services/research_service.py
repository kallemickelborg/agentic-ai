import requests
import xml.etree.ElementTree as ET
import re
import asyncio
from typing import List, Optional, Tuple
from fastapi import HTTPException
from models.domain import Paper, Author
from services.ai_service import AIService
import datetime


class ResearchService:
    """Service for fetching and processing research papers."""

    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.ai_service = AIService()

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

    def enhance_query_with_dspy(
        self, original_query: str, clarify_answers: List[dict]
    ) -> str:
        """Enhance the original query based on clarifying answers using DSPy's ChainOfThought module."""
        return self.ai_service.enhance_query_with_dspy(original_query, clarify_answers)

    def check_paper_accessibility(self, pmid: str) -> Tuple[bool, Optional[str], str]:
        """
        Check if a paper is accessible and get its full text link if available.
        Returns: (is_accessible, full_text_link, source_type)
        """
        try:
            # First check if paper is available in PubMed Central (open access)
            pmc_check_url = f"{self.base_url}elink.fcgi"
            params = {"dbfrom": "pubmed", "db": "pmc", "id": pmid, "retmode": "json"}

            response = requests.get(pmc_check_url, params=params, timeout=10)
            response.raise_for_status()

            # Parse the response to check for PMC link
            data = response.json()
            link_set = data.get("linksets", [{}])[0]
            id_list = (
                link_set.get("linksetdbs", [{}])[0].get("links", [])
                if link_set.get("linksetdbs")
                else []
            )

            if id_list:
                # Paper is available in PMC
                pmc_id = id_list[0]
                full_text_link = (
                    f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}"
                )
                return True, full_text_link, "open_access"

            # If not in PMC, check the original publisher's link
            linkout_url = (
                f"{self.base_url}elink.fcgi?dbfrom=pubmed&id={pmid}&cmd=prlinks"
            )
            response = requests.head(linkout_url, timeout=10, allow_redirects=True)

            final_url = response.url
            if any(
                domain in final_url
                for domain in [
                    "sciencedirect.com",
                    "springer.com",
                    "wiley.com",
                    "tandfonline.com",
                    "academic.oup.com",
                    "nature.com",
                    "bmj.com",
                ]
            ):
                # Paper requires institutional access
                return False, final_url, "requires_access"

            # Paper might be freely available on publisher's site
            return True, final_url, "open_access"

        except Exception as e:
            return False, None, "abstract_only"

    def fetch_research_papers(self, query: str, max_results: int = 20) -> List[Paper]:
        """Fetch research papers from PubMed E-utilities API."""
        cleaned_query = self.clean_query(query)
        enhanced_query = self.enhance_search_query(cleaned_query)

        papers = []

        try:
            # Initial search to get paper IDs
            search_response = requests.get(
                f"{self.base_url}esearch.fcgi",
                params={
                    "db": "pubmed",
                    "term": enhanced_query,
                    "retmax": max_results,
                    "sort": "relevance",
                    "retmode": "json",
                    "usehistory": "y",
                },
                timeout=10,
            )
            search_response.raise_for_status()

            try:
                search_data = search_response.json()
            except Exception:
                search_data = {}

            id_list = search_data.get("esearchresult", {}).get("idlist", [])
            query_key = search_data.get("esearchresult", {}).get("querykey")
            web_env = search_data.get("esearchresult", {}).get("webenv")

            if not id_list:
                raise HTTPException(status_code=204, detail="No research papers found")

            # Fetch detailed information
            efetch_response = requests.get(
                f"{self.base_url}efetch.fcgi",
                params={
                    "db": "pubmed",
                    "query_key": query_key,
                    "WebEnv": web_env,
                    "retmode": "xml",
                    "retmax": max_results,
                },
                timeout=10,
            )
            efetch_response.raise_for_status()
            root = ET.fromstring(efetch_response.content)

            for article in root.findall(".//PubmedArticle"):
                try:
                    # Extract basic information
                    title = article.findtext(".//ArticleTitle") or "No title available"
                    abstract = article.findtext(".//AbstractText") or ""
                    pmid = article.findtext(".//PMID") or "No PMID available"

                    # Check accessibility
                    is_accessible, full_text_link, source_type = (
                        self.check_paper_accessibility(pmid)
                    )

                    # Extract authors
                    authors = []
                    for author in article.findall(".//Author"):
                        last_name = author.findtext("LastName") or ""
                        fore_name = author.findtext("ForeName") or ""
                        if last_name or fore_name:
                            authors.append(
                                Author(name=f"{last_name} {fore_name}".strip())
                            )

                    # Extract date
                    pub_date = article.find(".//PubDate")
                    published_date = "Date not available"
                    if pub_date is not None:
                        year = pub_date.findtext("Year") or ""
                        month = pub_date.findtext("Month") or ""
                        day = pub_date.findtext("Day") or ""
                        published_date = "-".join(filter(None, [year, month, day]))

                    # Study type
                    study_type = "unknown"
                    abstract_lower = abstract.lower()
                    if any(
                        term in abstract_lower
                        for term in ["clinical trial", "human subjects", "patient"]
                    ):
                        study_type = "clinical trial"
                    elif any(
                        term in abstract_lower
                        for term in ["in vivo", "animal model", "mouse", "rat"]
                    ):
                        study_type = "in vivo"
                    elif any(
                        term in abstract_lower
                        for term in ["in vitro", "cell culture", "cell line"]
                    ):
                        study_type = "in vitro"

                    # Publication types
                    publication_types = [
                        pub_type.text
                        for pub_type in article.findall(".//PublicationType")
                        if pub_type.text
                    ]

                    # Peer review status
                    peer_reviewed = bool(
                        article.find(".//Journal")
                        and "Journal Article" in publication_types
                    )

                    papers.append(
                        Paper(
                            title=title,
                            link=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}",
                            authors=authors,
                            published_date=published_date,
                            abstract=abstract,
                            peer_reviewed=peer_reviewed,
                            study_type=study_type,
                            publication_type=publication_types,
                            full_text_accessible=is_accessible,
                            full_text_link=full_text_link,
                            source_type=source_type,
                        )
                    )
                except Exception as e:
                    continue

        except requests.RequestException:
            raise HTTPException(
                status_code=503, detail="Failed to fetch papers from PubMed"
            )
        except ET.ParseError:
            raise HTTPException(
                status_code=500, detail="Failed to parse PubMed response"
            )

        return papers

    async def process_research_papers(self, task_description: str, input_data: dict):
        """Process research papers and yield updates for each paper."""
        research_papers = await asyncio.to_thread(self.fetch_research_papers, task_description)

        # Get clarifying answers
        clarify_answers = input_data.get("clarify_answers", [])
        clarify_context = "\n".join(
            [f"Q: {ans['question']}\nA: {ans['answer']}" for ans in clarify_answers]
        )

        # Create a context-aware query by combining original query and clarifying answers
        context_aware_query = f"""
        Original Query: {task_description}
        User's Clarifications:
        {clarify_context}
        """

        processed_papers = []
        total_papers = len(research_papers)

        # Send initial count
        yield {
            "state": "Research",
            "total_papers": total_papers,
            "processed_papers": 0,
            "current_paper": None,
        }

        for index, paper in enumerate(research_papers):
            try:
                # Single call to evaluate both scores with context-aware query
                rel_score, cit_score = await asyncio.to_thread(
                    self.ai_service.evaluate_paper, paper, context_aware_query
                )

                paper.relevancy_score = rel_score
                paper.citation_score = cit_score

                processed_papers.append(paper)

                # Send update for each processed paper
                yield {
                    "state": "Research",
                    "total_papers": total_papers,
                    "processed_papers": len(processed_papers),
                    "current_paper": {
                        "title": paper.title,
                        "relevancy_score": rel_score,
                        "citation_score": cit_score,
                    },
                }

            except Exception as e:
                paper.relevancy_score = 50.0
                paper.citation_score = 50.0
                processed_papers.append(paper)

        # Sort by relevancy_score, then by citation_score
        processed_papers.sort(
            key=lambda p: (p.relevancy_score or 0, p.citation_score or 0),
            reverse=True,
        )

        # Send final update with all papers
        yield {
            "state": "Research",
            "research_papers": [paper.dict() for paper in processed_papers],
            "response": "Papers have been evaluated for both relevancy and scientific merit.",
            "total_papers": total_papers,
            "processed_papers": len(processed_papers),
            "original_query": task_description,
            "enhanced_query": await asyncio.to_thread(
                self.enhance_query_with_dspy,
                task_description,
                input_data.get("clarify_answers", []),
            ),
        }
