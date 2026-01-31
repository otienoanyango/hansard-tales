"""
Questions scraper for National Assembly and Senate documents.

This module implements the scraper for parliamentary questions from
parliament.go.ke, extracting PDF links and metadata for question tracking.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from bs4 import BeautifulSoup

from hansard_tales.models.base import Chamber
from hansard_tales.scrapers.base import BaseScraper, DataCollectionError


@dataclass
class QuestionMetadata:
    """Metadata extracted for a question."""

    question_number: str
    asker: str
    question_text: str
    question_date: date
    chamber: Chamber
    question_type: str  # "oral", "written", "supplementary"
    ministry: Optional[str]
    url: str
    source_hash: str


class QuestionScraper(BaseScraper):
    """
    Scraper for parliamentary questions.

    This scraper extracts question records from parliament.go.ke
    by parsing HTML tables on the Questions pages.

    Example:
        >>> config = ScraperConfig()
        >>> scraper = QuestionScraper(config)
        >>> questions = scraper.discover_questions(Chamber.NATIONAL_ASSEMBLY)
    """

    def discover_questions(
        self,
        chamber: Chamber,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        parliament_term: int = 2022,
    ) -> list[QuestionMetadata]:
        """
        Discover questions from parliament.go.ke tables.

        This method extracts question information from the Questions page by:
        1. Fetching the Questions page HTML
        2. Finding tables containing question records
        3. Extracting question metadata from table rows
        4. Filtering by date range if provided
        5. Validating question data is complete

        Args:
            chamber: Parliamentary chamber (National Assembly or Senate)
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            parliament_term: Parliament term start year (default: 2022)

        Returns:
            List of QuestionMetadata objects

        Raises:
            DataCollectionError: If no questions found
        """
        # Construct base URL based on chamber
        if chamber == Chamber.NATIONAL_ASSEMBLY:
            base_url = (
                f"{self.config.base_url}/the-national-assembly/business/questions"
                f"?title=%20&field_parliament_value={parliament_term}&page=0"
            )
        elif chamber == Chamber.SENATE:
            base_url = (
                f"{self.config.base_url}/the-senate/business/questions"
                f"?title=%20&field_parliament_value={parliament_term}&page=0"
            )
        else:
            raise ValueError(f"Unknown chamber: {chamber}")

        # Fetch page HTML (with retry)
        response = self._fetch_page_with_retry(base_url, timeout=self.config.timeout)

        soup = BeautifulSoup(response.content, "html.parser")

        questions = []

        # Find tables containing questions
        tables = soup.find_all("table", class_="views-table")

        if not tables:
            tables = soup.find_all("table")

        # Extract question metadata from tables
        for table in tables:
            for row in table.find_all("tr"):
                cells = row.find_all("td")

                if not cells:
                    continue

                try:
                    # Extract question metadata from row cells
                    question_data = self._extract_question_from_row(cells, chamber)
                    if question_data:
                        # Apply date filtering if specified
                        if start_date and question_data.question_date < start_date:
                            continue
                        if end_date and question_data.question_date > end_date:
                            continue

                        questions.append(question_data)
                except (IndexError, ValueError, AttributeError) as e:
                    self.logger.warning(f"Failed to extract question from row: {e}")
                    continue

        if not questions:
            raise DataCollectionError(
                f"No questions found for {chamber.value}. " "Website structure may have changed."
            )

        self.logger.info(f"Discovered {len(questions)} questions for {chamber.value}")
        return questions

    def _extract_question_from_row(
        self, cells: list, chamber: Chamber
    ) -> Optional[QuestionMetadata]:
        """
        Extract question metadata from a table row.

        Assumes row structure:
        - Cell 0: Question Number
        - Cell 1: Asker (MP name)
        - Cell 2: Question Text (or snippet)
        - Cell 3: Question Date
        - Cell 4: Question Type
        - Cell 5: Ministry
        - Cell 6: Link (PDF or details page)

        Args:
            cells: List of table cells from a row
            chamber: Parliamentary chamber

        Returns:
            QuestionMetadata object or None if extraction fails
        """
        if len(cells) < 6:
            return None

        # Extract question number
        question_number = cells[0].get_text(strip=True).strip()
        if not question_number:
            return None

        # Extract asker name
        asker = cells[1].get_text(strip=True).strip()

        # Extract question text (may be truncated)
        question_text = cells[2].get_text(strip=True).strip()
        if not question_text:
            return None

        # Extract question date
        date_text = cells[3].get_text(strip=True).strip()
        try:
            question_date = self._parse_date(date_text)
        except ValueError:
            self.logger.warning(f"Could not parse date: {date_text}")
            return None

        # Extract question type
        question_type = cells[4].get_text(strip=True).strip().lower()
        if not question_type:
            question_type = "written"

        # Extract ministry if available
        ministry = None
        if len(cells) > 5:
            ministry = cells[5].get_text(strip=True).strip()
            ministry = ministry if ministry else None

        # Extract URL from link (usually in last cell or within cells)
        url = None
        if len(cells) > 6:
            link_elem = cells[6].find("a", href=True)
            if link_elem:
                href = link_elem.get("href")
                if isinstance(href, str):
                    if not href.startswith("http"):
                        href = f"{self.config.base_url}{href}"
                    url = href

        # If no link in separate cell, look in all cells
        if not url:
            for cell in cells:
                link_elem = cell.find("a", href=True)
                if link_elem:
                    href = link_elem.get("href")
                    if isinstance(href, str) and href.endswith(".pdf"):
                        if not href.startswith("http"):
                            href = f"{self.config.base_url}{href}"
                        url = href
                        break

        if not url:
            # Questions may not have downloadable PDFs, which is ok
            url = f"{self.config.base_url}/question/{question_number}"

        # Calculate hash
        source_hash = self._hash_url(url)

        return QuestionMetadata(
            question_number=question_number,
            asker=asker,
            question_text=question_text,
            question_date=question_date,
            chamber=chamber,
            question_type=question_type,
            ministry=ministry,
            url=url,
            source_hash=source_hash,
        )

    def _parse_date(self, date_str: str) -> date:
        """
        Parse date string in various formats.

        Args:
            date_str: Date string to parse

        Returns:
            Parsed date object

        Raises:
            ValueError: If date cannot be parsed
        """
        import datetime

        # Try common formats
        formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d %B %Y",
            "%d %b %Y",
        ]

        for fmt in formats:
            try:
                return datetime.datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        raise ValueError(f"Could not parse date: {date_str}")

    def _hash_url(self, url: str) -> str:
        """
        Generate SHA256 hash of URL for duplicate detection.

        Args:
            url: URL to hash

        Returns:
            SHA256 hash as hex string
        """
        import hashlib

        return hashlib.sha256(url.encode()).hexdigest()

    def download_question(self, question_metadata: QuestionMetadata) -> bytes:
        """
        Download question document if available.

        Args:
            question_metadata: Question metadata containing URL

        Returns:
            Document content as bytes (may be empty if no PDF)

        Raises:
            DataCollectionError: If download fails for PDF URL
        """
        try:
            response = self._fetch_page_with_retry(
                question_metadata.url, timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            # Questions may not have downloadable documents
            if question_metadata.url.endswith(".pdf"):
                raise DataCollectionError(
                    f"Failed to download question {question_metadata.question_number}: {e}"
                ) from e
            # For non-PDF links, log warning but continue
            self.logger.warning(f"Could not retrieve question {question_metadata.question_number}")
            return b""

    def get_document_urls(
        self,
        chamber: Chamber,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        parliament_term: int = 2022,
    ) -> list[str]:
        """
        Get question document URLs from parliament.go.ke.

        This is a compatibility method for the BaseScraper interface.

        Args:
            chamber: Parliamentary chamber
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            parliament_term: Parliament term start year

        Returns:
            List of question document URLs
        """
        questions = self.discover_questions(chamber, start_date, end_date, parliament_term)
        return [q.url for q in questions if q.url]

    def extract_metadata(self, url: str, content: bytes) -> dict:
        """
        Extract metadata from question content.

        This is a required implementation of the BaseScraper abstract method.

        Args:
            url: URL of the question document
            content: Binary content of the document

        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            "url": url,
            "content_length": len(content),
        }

        # Try to extract text-based metadata if content is PDF
        if content.startswith(b"%PDF"):
            try:
                import io

                import pdfplumber

                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    if pdf.pages:
                        first_page_text = pdf.pages[0].extract_text() or ""
                        metadata["first_page_preview"] = first_page_text[:200]
                        metadata["page_count"] = len(pdf.pages)
            except Exception:
                pass

        return metadata
