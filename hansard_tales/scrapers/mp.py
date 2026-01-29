"""
MP scraper for National Assembly members.

This module implements the scraper for MP data from parliament.go.ke,
extracting MP information including name, county, constituency, party,
and status from the MPs listing page.
"""

import re
import time
from dataclasses import dataclass

from bs4 import BeautifulSoup

from hansard_tales.models.base import Chamber
from hansard_tales.scrapers.base import BaseScraper, DataCollectionError


@dataclass
class MPData:
    """MP data extracted from parliament.go.ke."""

    name: str  # Full name with honorifics
    clean_name: str  # Name without honorifics
    honorifics: list[str]  # Extracted honorifics (HON., DR., etc.)
    county: str | None  # Empty for nominated MPs
    constituency: str | None  # Empty for nominated MPs
    party: str
    status: str  # "Elected" or "Nominated"
    profile_url: str  # Link to MP profile page
    parliament_term: int
    photo_url: str | None = None


class MPScraper(BaseScraper):
    """
    Scraper for MP data from parliament.go.ke.

    Extracts MP information including name, county, constituency, party,
    and status from the MPs listing page.

    URL Format: https://parliament.go.ke/the-national-assembly/mps?field_parliament_value=2022&page=0
    CSS Selector: table.cols-7 tr.mp
    Pagination: Extracts last page from nav.pager li.pager__item--last

    Test Data: tests/sample_html.md, tests/fixtures/sample_mps.html

    Example:
        >>> config = ScraperConfig()
        >>> scraper = MPScraper(config)
        >>> mps = scraper.scrape_mps(parliament_term=2022)
    """

    # Honorific patterns
    HONORIFICS = [
        "HON.",
        "DR.",
        "ENG.",
        "AMB.",
        "PROF.",
        "MR.",
        "MS.",
        "MRS.",
    ]

    def __init__(self, chamber: Chamber = Chamber.NATIONAL_ASSEMBLY, **kwargs):
        """
        Initialize MP scraper.

        Args:
            chamber: Parliamentary chamber (default: National Assembly)
            **kwargs: Additional arguments passed to BaseScraper
        """
        super().__init__(**kwargs)
        self.chamber = chamber
        self.base_url = "https://www.parliament.go.ke"

    def _build_url(self, page: int = 0, parliament_term: int = 2022) -> str:
        """
        Build URL for MP listing page.

        Args:
            page: Page number (0-indexed)
            parliament_term: Parliament term year

        Returns:
            Full URL for MP listing page
        """
        if self.chamber == Chamber.NATIONAL_ASSEMBLY:
            path = "/the-national-assembly/mps"
        elif self.chamber == Chamber.SENATE:
            path = "/the-senate/senators"
        else:
            raise ValueError(f"Unknown chamber: {self.chamber}")

        return (
            f"{self.base_url}{path}?"
            f"field_name_value=%20&"
            f"field_parliament_value={parliament_term}&"
            f"field_employment_history_value=&"
            f"page={page}"
        )

    def _get_total_pages(self, soup: BeautifulSoup) -> int:
        """
        Extract total number of pages from pagination.

        Looks for: nav.pager li.pager__item--last a[href]
        Extracts page number from: page=34

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Total number of pages (minimum 1)
        """
        last_page_link = soup.select_one("nav.pager li.pager__item--last a[href]")
        if not last_page_link:
            return 1

        href = last_page_link.get("href", "")
        match = re.search(r"page=(\d+)", href)
        if match:
            return int(match.group(1)) + 1  # Convert 0-indexed to count
        return 1

    def _extract_mps_from_page(self, soup: BeautifulSoup, parliament_term: int) -> list[MPData]:
        """
        Extract MP data from a single page.

        CSS Selector: table.cols-7 tr.mp
        Fields:
        - Name: td.views-field-field-name
        - County: td.views-field-field-county
        - Constituency: td.views-field-field-constituency
        - Party: td.views-field-field-party
        - Status: td.views-field-field-status
        - Profile URL: td.views-field-view-node a[href]

        Args:
            soup: BeautifulSoup object of the page
            parliament_term: Parliament term year

        Returns:
            List of MPData objects extracted from the page
        """
        mps = []
        rows = soup.select("table.cols-7 tr.mp")

        for row in rows:
            # Extract fields
            name_td = row.select_one("td.views-field-field-name")
            county_td = row.select_one("td.views-field-field-county")
            constituency_td = row.select_one("td.views-field-field-constituency")
            party_td = row.select_one("td.views-field-field-party")
            status_td = row.select_one("td.views-field-field-status")
            profile_link = row.select_one("td.views-field-view-node a[href]")

            # Skip rows with empty name
            if not name_td or not name_td.get_text(strip=True):
                continue

            # Extract and clean text (remove extra whitespace and newlines)
            name = " ".join(name_td.get_text(strip=True).split())
            county = " ".join(county_td.get_text(strip=True).split()) if county_td else None
            constituency = (
                " ".join(constituency_td.get_text(strip=True).split()) if constituency_td else None
            )
            party = " ".join(party_td.get_text(strip=True).split()) if party_td else None
            status = " ".join(status_td.get_text(strip=True).split()) if status_td else None
            profile_url = profile_link.get("href") if profile_link else None

            # Convert relative URLs to absolute
            if profile_url and not profile_url.startswith("http"):
                profile_url = f"{self.base_url}{profile_url}"

            # Parse honorifics
            honorifics, clean_name = self._parse_honorifics(name)

            # Handle empty county/constituency (convert empty strings to None)
            if not county or not county.strip():
                county = None
            if not constituency or not constituency.strip():
                constituency = None
            if not party or not party.strip():
                party = None
            if not status or not status.strip():
                status = None

            mps.append(
                MPData(
                    name=name,
                    clean_name=clean_name,
                    honorifics=honorifics,
                    county=county,
                    constituency=constituency,
                    party=party,
                    status=status,
                    profile_url=profile_url,
                    parliament_term=parliament_term,
                    photo_url=None,  # Can be extracted from profile page later
                )
            )

        return mps

    def _parse_honorifics(self, name: str) -> tuple[list[str], str]:
        """
        Parse honorifics from MP name.

        Examples:
        - "HON. JOHN DOE" → (["HON."], "JOHN DOE")
        - "HON. (DR.) JANE SMITH" → (["HON.", "DR."], "JANE SMITH")
        - "HON. (ENG.) PETER JONES" → (["HON.", "ENG."], "PETER JONES")

        Args:
            name: Full MP name with honorifics

        Returns:
            Tuple of (honorifics_list, clean_name)
        """
        honorifics = []
        clean_name = name

        # Extract honorifics in parentheses: (DR.), (ENG.), etc.
        paren_pattern = r"\(([A-Z]+\.)\)"
        for match in re.finditer(paren_pattern, name):
            honorific = match.group(1)
            if honorific in self.HONORIFICS:
                honorifics.append(honorific)
            clean_name = clean_name.replace(match.group(0), "").strip()

        # Extract leading honorifics: HON., DR., etc.
        for honorific in self.HONORIFICS:
            if clean_name.startswith(honorific):
                honorifics.append(honorific)
                clean_name = clean_name[len(honorific) :].strip()

        # Clean up extra spaces and commas
        clean_name = re.sub(r"\s+", " ", clean_name)
        clean_name = clean_name.strip(", ")

        return honorifics, clean_name

    def scrape_mps(self, parliament_term: int = 2022, max_pages: int | None = None) -> list[MPData]:
        """
        Scrape all MPs for a given parliament term.

        Args:
            parliament_term: Parliament term (default: 2022 for 13th Parliament)
            max_pages: Maximum pages to scrape (None = all pages)

        Returns:
            List of MPData objects

        Raises:
            DataCollectionError: If no MPs found (indicates HTML/CSS changes)
        """
        all_mps = []

        # Fetch first page to get total pages (with retry)
        url = self._build_url(page=0, parliament_term=parliament_term)
        response = self._fetch_page_with_retry(url, timeout=self.config.timeout)

        soup = BeautifulSoup(response.content, "html.parser")

        total_pages = self._get_total_pages(soup)
        if max_pages:
            total_pages = min(total_pages, max_pages)

        self.logger.info(f"Found {total_pages} pages to scrape")

        # Extract MPs from first page
        mps = self._extract_mps_from_page(soup, parliament_term)
        all_mps.extend(mps)

        # Fetch remaining pages with retry logic
        for page in range(1, total_pages):
            url = self._build_url(page=page, parliament_term=parliament_term)

            try:
                response = self._fetch_page_with_retry(url, timeout=self.config.timeout)
                soup = BeautifulSoup(response.content, "html.parser")
                mps = self._extract_mps_from_page(soup, parliament_term)
                all_mps.extend(mps)

                # Rate limiting
                time.sleep(self.config.retry_delay)

            except Exception as e:
                self.logger.error(f"Failed to fetch page {page} after retries: {e}")
                # Continue with remaining pages
                continue

        # Fail fast if no MPs found - likely indicates HTML/CSS changes
        if not all_mps:
            raise DataCollectionError(
                f"No MPs found at {self._build_url(0, parliament_term)}. "
                "This may indicate that the website structure has changed. "
                "Please verify the page HTML and update the scraper accordingly."
            )

        return all_mps

    def detect_duplicates(self, mps: list[MPData]) -> list[tuple[MPData, MPData]]:
        """
        Detect duplicate MPs by name+constituency combination.

        Args:
            mps: List of MPData objects to check

        Returns:
            List of tuples containing duplicate MP pairs
        """
        duplicates = []
        seen = {}

        for mp in mps:
            # Create key from clean name and constituency
            key = (mp.clean_name.lower(), mp.constituency.lower() if mp.constituency else None)

            if key in seen:
                duplicates.append((seen[key], mp))
            else:
                seen[key] = mp

        return duplicates

    def store_mps(self, mps: list[MPData]) -> int:
        """
        Store MPs in database with proper relationships.

        Uses upsert logic to handle updates to existing MPs.
        MPs are identified by name+constituency+parliament_term combination.

        Args:
            mps: List of MPData objects to store

        Returns:
            Number of MPs stored/updated

        Raises:
            Exception: If database operation fails
        """
        try:
            from datetime import datetime

            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker

            from hansard_tales.config.settings import Config
            from hansard_tales.database.models import MPORM, ChamberEnum

            # Convert Chamber to ChamberEnum
            chamber_enum = (
                ChamberEnum.NATIONAL_ASSEMBLY
                if self.chamber == Chamber.NATIONAL_ASSEMBLY
                else ChamberEnum.SENATE
            )

            # Get database connection
            config = Config()
            engine = create_engine(config.database.connection_string)
            Session = sessionmaker(bind=engine)
            session = Session()

            stored_count = 0

            try:
                for mp in mps:
                    # Check if MP already exists
                    existing = (
                        session.query(MPORM)
                        .filter(
                            MPORM.name == mp.name,
                            MPORM.chamber == chamber_enum,
                            MPORM.parliament_term == mp.parliament_term,
                        )
                        .first()
                    )

                    if existing:
                        # Update existing MP
                        existing.party = mp.party
                        existing.constituency = mp.constituency
                        existing.updated_at = datetime.now()
                    else:
                        # Create new MP
                        mp_orm = MPORM(
                            name=mp.name,
                            chamber=chamber_enum,
                            party=mp.party,
                            constituency=mp.constituency,
                            parliament_term=mp.parliament_term,
                            created_at=datetime.now(),
                            updated_at=datetime.now(),
                        )
                        session.add(mp_orm)

                    stored_count += 1

                session.commit()
                return stored_count

            finally:
                session.close()

        except Exception as e:
            # Log error but don't fail the scrape
            print(f"Warning: Failed to store MPs in database: {e}")
            return 0

    # Implement abstract methods from BaseScraper
    def get_document_urls(self, chamber: Chamber, start_date=None, end_date=None) -> list[str]:
        """
        Not applicable for MP scraper.

        MP scraper doesn't download documents, it extracts data from HTML.
        This method is required by BaseScraper but not used.
        """
        return []

    def extract_metadata(self, url: str, content: bytes) -> dict:
        """
        Not applicable for MP scraper.

        MP scraper doesn't download documents, it extracts data from HTML.
        This method is required by BaseScraper but not used.
        """
        return {"document_type": "mp_data"}
