"""
Votes & Proceedings scraper for National Assembly and Senate documents.

This module implements the scraper for Votes & Proceedings documents from
parliament.go.ke, extracting PDF links from HTML tables.
"""

import re
from datetime import date

from bs4 import BeautifulSoup

from hansard_tales.models.base import Chamber
from hansard_tales.scrapers.base import BaseScraper, DataCollectionError


class VotesScraper(BaseScraper):
    """
    Scraper for Votes & Proceedings documents.

    This scraper extracts Votes & Proceedings PDF links from parliament.go.ke
    by parsing HTML tables on the Votes & Proceedings pages.

    Example:
        >>> config = ScraperConfig()
        >>> scraper = VotesScraper(config)
        >>> documents = scraper.scrape(Chamber.NATIONAL_ASSEMBLY)
    """

    def get_document_urls(
        self,
        chamber: Chamber,
        start_date: date | None = None,
        end_date: date | None = None,
        parliament_term: int = 2022,
    ) -> list[str]:
        """
        Get Votes & Proceedings PDF URLs from parliament.go.ke tables.

        This method extracts PDF links from the Votes & Proceedings page by:
        1. Fetching the Votes & Proceedings page HTML
        2. Finding tables containing document links
        3. Extracting PDF links from table rows
        4. Validating links are Votes & Proceedings documents

        Note on URLs:
        - Page URL: /the-national-assembly/house-business/votes-proceeding (singular)
        - PDF URLs: /sites/default/files/YYYY-MM/Thursday%2CDecember%204%2C2025%20at%204.15pm.pdf

        Args:
            chamber: Parliamentary chamber (National Assembly or Senate)
            start_date: Optional start date for filtering (not implemented yet)
            end_date: Optional end date for filtering (not implemented yet)
            parliament_term: Parliament term start year (default: 2022)

        Returns:
            List of Votes & Proceedings PDF URLs

        Raises:
            DataCollectionError: If no documents found (indicates HTML/CSS changes)
        """
        # Construct base URL based on chamber
        # Note: The page URL uses "votes-proceeding" (singular), not "votes-and-proceedings"
        if chamber == Chamber.NATIONAL_ASSEMBLY:
            base_url = (
                f"{self.config.base_url}/the-national-assembly/house-business/votes-proceeding"
                f"?title=%20&field_parliament_value={parliament_term}&page=0"
            )
        elif chamber == Chamber.SENATE:
            base_url = (
                f"{self.config.base_url}/the-senate/house-business/votes-proceeding"
                f"?title=%20&field_parliament_value={parliament_term}&page=0"
            )
        else:
            raise ValueError(f"Unknown chamber: {chamber}")

        # Fetch page HTML
        response = self.session.get(base_url, timeout=self.config.timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        urls = []

        # Find tables containing Votes & Proceedings documents
        # Try specific class first, then fallback to all tables
        tables = soup.find_all("table", class_="views-table")

        if not tables:
            # Fallback: look for any table containing PDF links
            tables = soup.find_all("table")

        # Extract PDF links from tables
        for table in tables:
            for row in table.find_all("tr"):
                for link in row.find_all("a", href=True):
                    href = link["href"]

                    # Validate it's a PDF link
                    if not href.endswith(".pdf"):
                        continue

                    # Additional validation: check if it's a Votes & Proceedings document
                    # by looking at the link text or URL pattern
                    link_text = link.get_text().lower()
                    href_lower = href.lower()

                    # Check for votes/proceedings keywords
                    is_votes_doc = (
                        "vote" in link_text
                        or "vote" in href_lower
                        or "proceeding" in link_text
                        or "proceeding" in href_lower
                    )

                    if is_votes_doc:
                        # Convert relative URLs to absolute
                        if href.startswith("http"):
                            full_url = href
                        else:
                            # Remove leading slash if present
                            href = href.lstrip("/")
                            full_url = f"{self.config.base_url}/{href}"

                        urls.append(full_url)

        # Fail fast if no documents found - likely indicates HTML/CSS changes
        if not urls:
            raise DataCollectionError(
                f"No Votes & Proceedings documents found at {base_url}. "
                "This may indicate that the website structure has changed. "
                "Please verify the page HTML and update the scraper accordingly."
            )

        return urls

    def _get_total_pages(self, soup: BeautifulSoup) -> int:
        """
        Extract total number of pages from pagination element.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Total number of pages (minimum 1)
        """
        # Look for pagination using CSS selector
        pager = soup.select_one("nav.pager, ul.pager, div.pager")

        if not pager:
            return 1

        # Find all page links
        page_links = pager.select("a")

        if not page_links:
            return 1

        # Extract page numbers from links
        max_page = 0
        for link in page_links:
            href = link.get("href", "")
            match = re.search(r"page=(\d+)", href)
            if match:
                page_num = int(match.group(1))
                max_page = max(max_page, page_num)

        return max_page + 1 if max_page > 0 else 1

    def _extract_urls_from_page(self, soup: BeautifulSoup) -> list[str]:
        """
        Extract PDF URLs from a single page using CSS selectors.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            List of PDF URLs found on the page
        """
        urls = []

        # Use CSS selector: table.cols-2 td.views-field-field-pdf a[href$=".pdf"]
        pdf_links = soup.select('table.cols-2 td.views-field-field-pdf a[href$=".pdf"]')

        for link in pdf_links:
            href = link.get("href", "")

            if href:
                # Convert relative URLs to absolute
                if href.startswith("http"):
                    full_url = href
                else:
                    href = href.lstrip("/")
                    full_url = f"{self.config.base_url}/{href}"

                urls.append(full_url)

        return urls

    def extract_metadata(self, url: str, content: bytes) -> dict:
        """
        Extract metadata from Votes & Proceedings PDF using dateparser.

        Extracts date and time from filename title using dateparser library.
        All dates are assumed to be in UTC+3 timezone (Kenya timezone).

        Example: "Tuesday, November 4, 2025 at 2.30pm.pdf"

        Args:
            url: Document URL
            content: Document content (not used for filename-based extraction)

        Returns:
            Dictionary containing:
                - document_type: Always "votes"
                - original_filename: Original filename from URL
                - date: Extracted date in YYYY-MM-DD format (using dateparser)
                - time: Extracted time in HH:MM format
                - datetime_iso: ISO 8601 datetime string
        """
        import urllib.parse

        import dateparser

        filename = urllib.parse.unquote(url.split("/")[-1])

        metadata = {
            "document_type": "votes",
            "original_filename": filename,
        }

        # Extract date using dateparser with UTC+3 timezone
        # Pattern: "Tuesday, November 4, 2025" or "November 4, 2025" or "11 November 2025"
        # Try to capture the full date string including optional day of week
        date_match = re.search(
            r"(\w+\s*,?\s*\w+\s+\d{1,2}\s*,?\s*\d{4}|\d{1,2}\s+\w+\s+\d{4})",
            filename,
            re.IGNORECASE,
        )
        if date_match:
            date_str = date_match.group(1)
            parsed_date = dateparser.parse(
                date_str,
                settings={
                    "TIMEZONE": "Africa/Nairobi",  # UTC+3
                    "RETURN_AS_TIMEZONE_AWARE": False,
                },
            )

            if parsed_date:
                metadata["date"] = parsed_date.strftime("%Y-%m-%d")
                metadata["year"] = parsed_date.strftime("%Y")
                metadata["month"] = parsed_date.strftime("%m")
                metadata["day"] = parsed_date.strftime("%d")

        # Extract time from filename
        # Pattern: "at 2.30pm" or "at 10.00am" or "At 2.30pm"
        time_match = re.search(r"[Aa]t\s+(\d{1,2})\.(\d{2})\s*(am|pm)", filename, re.IGNORECASE)
        if time_match:
            hour, minute, meridiem = time_match.groups()
            hour = int(hour)

            # Convert to 24-hour format
            if meridiem.lower() == "pm" and hour != 12:
                hour += 12
            elif meridiem.lower() == "am" and hour == 12:
                hour = 0

            metadata["time"] = f"{hour:02d}:{minute}"

            # Create ISO 8601 datetime if we have both date and time
            if "date" in metadata:
                metadata["datetime_iso"] = f"{metadata['date']}T{hour:02d}:{minute}:00Z"

        return metadata

    def _generate_filename(self, url: str) -> str:
        """
        Generate standardized filename from URL using dateparser.

        Format: votes_YYYYMMDDTHHMMSSZ.pdf
        Example: votes_20241104T143000Z.pdf

        Uses dateparser to parse British format dates with UTC+3 timezone.

        Args:
            url: Document URL

        Returns:
            Standardized filename
        """
        import urllib.parse

        import dateparser

        original_filename = urllib.parse.unquote(url.split("/")[-1])

        # Extract date using dateparser - handle various formats
        date_match = re.search(
            r"(\w+\s*,?\s*\w+\s+\d{1,2}\s*,?\s*\d{4}|\d{1,2}\s+\w+\s+\d{4})",
            original_filename,
            re.IGNORECASE,
        )
        time_match = re.search(
            r"[Aa]t\s+(\d{1,2})\.(\d{2})\s*(am|pm)", original_filename, re.IGNORECASE
        )

        if date_match and time_match:
            date_str = date_match.group(1)
            hour, minute, meridiem = time_match.groups()

            parsed_date = dateparser.parse(
                date_str,
                settings={
                    "TIMEZONE": "Africa/Nairobi",  # UTC+3
                    "RETURN_AS_TIMEZONE_AWARE": False,
                },
            )

            if parsed_date:
                # Convert to 24-hour format
                hour = int(hour)
                if meridiem.lower() == "pm" and hour != 12:
                    hour += 12
                elif meridiem.lower() == "am" and hour == 12:
                    hour = 0

                return f"votes_{parsed_date.strftime('%Y%m%d')}T{hour:02d}{minute}00Z.pdf"

        # Fallback to original filename if parsing fails
        return original_filename
