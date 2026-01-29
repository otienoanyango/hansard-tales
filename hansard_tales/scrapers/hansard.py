"""
Hansard scraper for National Assembly and Senate documents.

This module implements the scraper for Hansard documents from
parliament.go.ke, extracting PDF links from HTML tables with pagination support.
"""

import re
from datetime import date

from bs4 import BeautifulSoup

from hansard_tales.models.base import Chamber
from hansard_tales.scrapers.base import BaseScraper, DataCollectionError


class HansardScraper(BaseScraper):
    """
    Scraper for Hansard documents.

    This scraper extracts Hansard PDF links from parliament.go.ke
    by parsing HTML tables on the Hansard pages with pagination support.

    Example:
        >>> config = ScraperConfig()
        >>> scraper = HansardScraper(config)
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
        Get Hansard PDF URLs from parliament.go.ke tables with pagination.

        This method extracts PDF links from all pages of the Hansard listing by:
        1. Fetching the first page to determine total pages
        2. Iterating through all pages
        3. Extracting PDF links using CSS selectors

        Args:
            chamber: Parliamentary chamber (National Assembly or Senate)
            start_date: Optional start date for filtering (not implemented yet)
            end_date: Optional end date for filtering (not implemented yet)
            parliament_term: Parliament term start year (default: 2022)

        Returns:
            List of Hansard PDF URLs from all pages

        Raises:
            DataCollectionError: If no documents found (indicates HTML/CSS changes)
        """
        # Construct base URL based on chamber
        if chamber == Chamber.NATIONAL_ASSEMBLY:
            base_path = "/the-national-assembly/house-business/hansard"
        elif chamber == Chamber.SENATE:
            base_path = "/the-senate/house-business/hansard"
        else:
            raise ValueError(f"Unknown chamber: {chamber}")

        urls = []

        # Fetch first page to determine total pages (with retry)
        first_page_url = (
            f"{self.config.base_url}{base_path}?field_parliament_value={parliament_term}&page=0"
        )
        response = self._fetch_page_with_retry(first_page_url, timeout=self.config.timeout)

        soup = BeautifulSoup(response.content, "html.parser")

        # Determine total number of pages from pagination
        total_pages = self._get_total_pages(soup)

        # Extract URLs from first page
        page_urls = self._extract_urls_from_page(soup)
        urls.extend(page_urls)

        # Fetch remaining pages with retry logic
        for page_num in range(1, total_pages):
            # Add delay to avoid rate limiting
            import time

            time.sleep(self.config.retry_delay)

            page_url = f"{self.config.base_url}{base_path}?field_parliament_value={parliament_term}&page={page_num}"

            try:
                response = self._fetch_page_with_retry(page_url, timeout=self.config.timeout)
                soup = BeautifulSoup(response.content, "html.parser")
                page_urls = self._extract_urls_from_page(soup)
                urls.extend(page_urls)
            except Exception as e:
                self.logger.error(f"Failed to fetch page {page_num} after retries: {e}")
                # Continue with remaining pages
                continue

        # Fail fast if no documents found - likely indicates HTML/CSS changes
        if not urls:
            raise DataCollectionError(
                f"No Hansard documents found at {first_page_url}. "
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
        # Common patterns: nav.pager, ul.pager, div.pager
        pager = soup.select_one("nav.pager, ul.pager, div.pager")

        if not pager:
            # No pagination found, assume single page
            return 1

        # Find all page links
        page_links = pager.select("a")

        if not page_links:
            return 1

        # Extract page numbers from links
        max_page = 0
        for link in page_links:
            href = link.get("href", "")
            # Look for page parameter in URL
            match = re.search(r"page=(\d+)", href)
            if match:
                page_num = int(match.group(1))
                max_page = max(max_page, page_num)

        # Total pages is max page number + 1 (zero-indexed)
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
                    # Remove leading slash if present
                    href = href.lstrip("/")
                    full_url = f"{self.config.base_url}/{href}"

                urls.append(full_url)

        return urls

    def extract_metadata(self, url: str, content: bytes) -> dict:
        """
        Extract metadata from Hansard PDF using dateparser.

        Extracts date and period from the URL (href attribute).
        All dates are assumed to be in UTC+3 timezone (Kenya timezone).

        The URL contains the period code in the filename:
        - (A) = Morning Sitting
        - (P) = Afternoon Sitting
        - (E) = Evening Sitting

        Example URL:
        "https://parliament.go.ke/files/Hansard%20Report%20-%20Thursday%2C%204th%20December%202025%20%28P%29.pdf"

        Note: The link text shows "Afternoon Sitting" but the URL contains "(P)".
        We extract from the URL, not the link text.

        Args:
            url: Document URL (href attribute from the link)
            content: Document content (not used for filename-based extraction)

        Returns:
            Dictionary containing:
                - document_type: Always "hansard"
                - original_filename: Original filename from URL
                - date: Extracted date in YYYY-MM-DD format (using dateparser)
                - period: Session period (A=Morning, P=Afternoon, E=Evening)
        """
        import urllib.parse

        import dateparser

        filename = urllib.parse.unquote(url.split("/")[-1])

        metadata = {
            "document_type": "hansard",
            "original_filename": filename,
        }

        # Extract date using dateparser with UTC+3 timezone
        # Pattern: "4th December 2025" from URL
        date_match = re.search(r"(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s*,?\s*\d{4})", filename)
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

        # Extract period from URL filename
        # The URL contains (A), (P), or (E) which maps to:
        # A = Morning, P = Afternoon, E = Evening
        period_match = re.search(r"\(([APE])\)", filename, re.IGNORECASE)
        if period_match:
            metadata["period"] = period_match.group(1).upper()
        else:
            # Default to P (Afternoon) if no period found
            metadata["period"] = "P"

        return metadata

    def _generate_filename(self, url: str) -> str:
        """
        Generate standardized filename from URL using dateparser.

        Format: hansard_YYYYMMDD_<A|P|E>.pdf
        Example: hansard_20241204_P.pdf

        Period codes (from URL):
        - A = Morning Sitting
        - P = Afternoon Sitting
        - E = Evening Sitting

        Uses dateparser to parse British format dates with UTC+3 timezone.

        Args:
            url: Document URL (href attribute)

        Returns:
            Standardized filename
        """
        import urllib.parse

        import dateparser

        # Handle edge cases: empty URL or URL ending with /
        if not url or url.endswith("/"):
            return "hansard_unknown.pdf"

        original_filename = urllib.parse.unquote(url.split("/")[-1])

        # Handle empty filename after split
        if not original_filename:
            return "hansard_unknown.pdf"

        # Extract date using dateparser
        date_match = re.search(r"(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s*,?\s*\d{4})", original_filename)

        # Extract period from URL (A, P, or E)
        period_match = re.search(r"\(([APE])\)", original_filename, re.IGNORECASE)

        if date_match and period_match:
            date_str = date_match.group(1)
            period = period_match.group(1).upper()

            parsed_date = dateparser.parse(
                date_str,
                settings={
                    "TIMEZONE": "Africa/Nairobi",  # UTC+3
                    "RETURN_AS_TIMEZONE_AWARE": False,
                },
            )

            if parsed_date:
                return f"hansard_{parsed_date.strftime('%Y%m%d')}_{period}.pdf"

        # Fallback to original filename if parsing fails
        return original_filename
