import aiohttp
import io
import PyPDF2
import pdfplumber
from typing import Optional, Tuple
from bs4 import BeautifulSoup
from models.domain import Paper
import traceback
from core.logging import logger


class PDFService:
    """Service for processing PDF documents and extracting content."""

    async def fetch_pdf_content(self, url: str) -> Optional[str]:
        """
        Fetch and extract text content from a PDF URL.
        Returns the extracted text or None if unsuccessful.
        """
        logger.info(f"Attempting to fetch PDF from: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }

        try:
            # Ensure URL ends with /pdf/ for PMC
            if "pmc/articles" in url and not url.endswith("/pdf/"):
                url = url.rstrip("/") + "/pdf/"
                logger.info(f"Adjusted PMC URL to: {url}")

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(
                            f"Failed to fetch PDF from {url}: {response.status} - {response.reason}"
                        )
                        logger.debug(f"Response headers: {dict(response.headers)}")

                        # Try alternative URL format if PMC
                        if "pmc/articles" in url:
                            alt_url = url.replace("/pdf/", "/pdf")
                            logger.info(f"Trying alternative URL: {alt_url}")
                            async with session.get(alt_url) as alt_response:
                                if alt_response.status != 200:
                                    logger.error(
                                        f"Failed to fetch PDF from alternate URL {alt_url}: {alt_response.status} - {alt_response.reason}"
                                    )
                                    logger.debug(
                                        f"Alternative response headers: {dict(alt_response.headers)}"
                                    )
                                    return None
                                content = await alt_response.read()
                                logger.info(
                                    f"Successfully fetched PDF from alternative URL, content size: {len(content)} bytes"
                                )
                        else:
                            return None
                    else:
                        content = await response.read()
                        logger.info(
                            f"Successfully fetched PDF, content size: {len(content)} bytes"
                        )

                pdf_file = io.BytesIO(content)

                # Try with PyPDF2 first
                try:
                    reader = PyPDF2.PdfReader(pdf_file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    if text.strip():  # Check if we got meaningful text
                        logger.info(
                            f"Successfully extracted text with PyPDF2, length: {len(text)} characters"
                        )
                        return text.strip()
                    logger.warning("PyPDF2 extracted empty text, trying pdfplumber")
                except Exception as e:
                    logger.warning(f"PyPDF2 failed, trying pdfplumber: {str(e)}")

                # Fallback to pdfplumber
                try:
                    pdf_file.seek(0)  # Reset file pointer
                    with pdfplumber.open(pdf_file) as pdf:
                        text = ""
                        for page in pdf.pages:
                            text += page.extract_text() + "\n"
                        if text.strip():
                            logger.info(
                                f"Successfully extracted text with pdfplumber, length: {len(text)} characters"
                            )
                        else:
                            logger.warning("pdfplumber extracted empty text")
                        return text.strip()
                except Exception as e:
                    logger.error(f"PDF extraction failed: {str(e)}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching PDF: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    async def fetch_pmc_paper_content(self, pmid: str) -> Tuple[bool, Optional[str]]:
        """
        Fetch paper content from PubMed Central.
        Returns (success, content) tuple.
        """
        try:
            # First get the PMC ID
            base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
            pmc_check_url = f"{base_url}elink.fcgi"
            params = {"dbfrom": "pubmed", "db": "pmc", "id": pmid, "retmode": "json"}

            async with aiohttp.ClientSession() as session:
                async with session.get(pmc_check_url, params=params) as response:
                    if response.status != 200:
                        return False, None

                    data = await response.json()
                    link_set = data.get("linksets", [{}])[0]
                    id_list = (
                        link_set.get("linksetdbs", [{}])[0].get("links", [])
                        if link_set.get("linksetdbs")
                        else []
                    )

                    if not id_list:
                        return False, None

                    pmc_id = id_list[0]

                    # Try different URL formats for PMC
                    urls_to_try = [
                        f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/",
                        f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf",
                        f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}",
                    ]

                    # Try each URL format
                    for url in urls_to_try:
                        if url.endswith("pdf/") or url.endswith("pdf"):
                            content = await self.fetch_pdf_content(url)
                            if content:
                                return True, content
                        else:
                            # If HTML URL, try to fetch HTML version
                            async with session.get(url) as html_response:
                                if html_response.status == 200:
                                    html_content = await html_response.text()
                                    soup = BeautifulSoup(html_content, "html.parser")

                                    # Extract main content
                                    article_text = ""
                                    main_content = soup.find(
                                        "div", {"class": "jig-ncbiinpagenav"}
                                    )
                                    if not main_content:
                                        # Try alternative content div
                                        main_content = soup.find(
                                            "div", {"class": "article-body"}
                                        )

                                    if main_content:
                                        # Remove references and other unwanted sections
                                        for unwanted in main_content.find_all(
                                            ["div", "table"],
                                            {"class": ["ref-list", "table-wrap"]},
                                        ):
                                            unwanted.decompose()
                                        article_text = main_content.get_text(
                                            separator="\n", strip=True
                                        )

                                        if article_text:
                                            return True, article_text

                    return False, None

        except Exception as e:
            logger.error(f"Error fetching PMC content: {str(e)}")
            return False, None
