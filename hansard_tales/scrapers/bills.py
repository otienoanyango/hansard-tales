"""
Bills scraper for National Assembly and Senate documents.

This module implements the scraper for parliamentary bills from
parliament.go.ke, extracting PDF links and metadata for bill tracking.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from bs4 import BeautifulSoup

from hansard_tales.models.base import Chamber
from hansard_tales.scrapers.base import BaseScraper, DataCollectionError


@dataclass
class BillMetadata:
    """Metadata extracted for a bill."""

    bill_number: str
    title: str
    chamber: Chamber
    sponsor: Optional[str]
    introduction_date: date
    status: str
    url: str
    source_hash: str


class BillScraper(BaseScraper):
    """
    Scraper for parliamentary bills.

    This scraper extracts bill PDF links and metadata from parliament.go.ke
    by parsing HTML tables on the Bills pages.

    Example:
        >>> config = ScraperConfig()
        >>> scraper = BillScraper(config)
        >>> bills = scraper.discover_bills(Chamber.NATIONAL_ASSEMBLY)
    """

    def discover_bills(
        self,
        chamber: Chamber,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        parliament_term: int = 2022,
    ) -> list[BillMetadata]:
        """
        Discover bills from parliament.go.ke tables.

        This method extracts bill information from the Bills page by:
        1. Fetching the Bills page HTML
        2. Finding tables containing bill records
        3. Extracting bill metadata from table rows
        4. Validating bill data is complete

        Args:
            chamber: Parliamentary chamber (National Assembly or Senate)
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            parliament_term: Parliament term start year (default: 2022)

        Returns:
            List of BillMetadata objects

        Raises:
            DataCollectionError: If no bills found (indicates HTML/CSS changes)
        """
        # Construct base URL based on chamber
        if chamber == Chamber.NATIONAL_ASSEMBLY:
            base_url = (
                f"{self.config.base_url}/the-national-assembly/business/bills"
                f"?title=%20&field_parliament_value={parliament_term}&page=0"
            )
        elif chamber == Chamber.SENATE:
            base_url = (
                f"{self.config.base_url}/the-senate/business/bills"
                f"?title=%20&field_parliament_value={parliament_term}&page=0"
            )
        else:
            raise ValueError(f"Unknown chamber: {chamber}")

        # Fetch page HTML (with retry)
        response = self._fetch_page_with_retry(base_url, timeout=self.config.timeout)

        soup = BeautifulSoup(response.content, "html.parser")

        bills = []

        # Find tables containing bills
        tables = soup.find_all("table", class_="views-table")

        if not tables:
            tables = soup.find_all("table")

        # Extract bill metadata from tables
        for table in tables:
            for row in table.find_all("tr"):
                cells = row.find_all("td")

                if not cells:
                    continue

                try:
                    # Extract bill metadata from row cells
                    bill_data = self._extract_bill_from_row(cells, chamber)
                    if bill_data:
                        bills.append(bill_data)
                except (IndexError, ValueError, AttributeError) as e:
                    self.logger.warning(f"Failed to extract bill from row: {e}")
                    continue

        if not bills:
            raise DataCollectionError(
                f"No bills found for {chamber.value}. " "Website structure may have changed."
            )

        self.logger.info(f"Discovered {len(bills)} bills for {chamber.value}")
        return bills

    def _extract_bill_from_row(self, cells: list, chamber: Chamber) -> Optional[BillMetadata]:
        """
        Extract bill metadata from a table row.

        Assumes row structure:
        - Cell 0: Bill Number
        - Cell 1: Title
        - Cell 2: Sponsor
        - Cell 3: Introduction Date
        - Cell 4: Status
        - Cell 5: Link (PDF or details page)

        Args:
            cells: List of table cells from a row
            chamber: Parliamentary chamber

        Returns:
            BillMetadata object or None if extraction fails
        """
        if len(cells) < 6:
            return None

        # Extract bill number
        bill_number_text = cells[0].get_text(strip=True)
        bill_number = bill_number_text.strip()

        if not bill_number:
            return None

        # Extract title
        title = cells[1].get_text(strip=True).strip()

        # Extract sponsor
        sponsor = cells[2].get_text(strip=True).strip()
        sponsor = sponsor if sponsor else None

        # Extract introduction date
        date_text = cells[3].get_text(strip=True).strip()
        try:
            intro_date = self._parse_date(date_text)
        except ValueError:
            self.logger.warning(f"Could not parse date: {date_text}")
            return None

        # Extract status
        status = cells[4].get_text(strip=True).strip()

        # Extract PDF link
        pdf_link = None
        link_elem = cells[5].find("a", href=True)
        if link_elem:
            href = link_elem.get("href")
            if isinstance(href, str):
                if not href.startswith("http"):
                    href = f"{self.config.base_url}{href}"
                pdf_link = href

        if not pdf_link:
            return None

        # Calculate hash
        source_hash = self._hash_url(pdf_link)

        return BillMetadata(
            bill_number=bill_number,
            title=title,
            chamber=chamber,
            sponsor=sponsor,
            introduction_date=intro_date,
            status=status,
            url=pdf_link,
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

    def download_bill(self, bill_metadata: BillMetadata) -> bytes:
        """
        Download bill PDF.

        Args:
            bill_metadata: Bill metadata containing URL

        Returns:
            PDF content as bytes

        Raises:
            DataCollectionError: If download fails
        """
        try:
            response = self._fetch_page_with_retry(bill_metadata.url, timeout=self.config.timeout)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise DataCollectionError(
                f"Failed to download bill {bill_metadata.bill_number}: {e}"
            ) from e

    def get_document_urls(
        self,
        chamber: Chamber,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        parliament_term: int = 2022,
    ) -> list[str]:
        """
        Get bill PDF URLs from parliament.go.ke.

        This is a compatibility method for the BaseScraper interface.

        Args:
            chamber: Parliamentary chamber
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            parliament_term: Parliament term start year

        Returns:
            List of bill PDF URLs
        """
        bills = self.discover_bills(chamber, start_date, end_date, parliament_term)
        return [bill.url for bill in bills]

    def extract_metadata(self, url: str, content: bytes) -> dict:
        """
        Extract metadata from bill content.

        This is a required implementation of the BaseScraper abstract method.

        Args:
            url: URL of the bill document
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
