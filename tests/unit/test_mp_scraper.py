"""
Unit tests for MP scraper.

Tests cover MP data extraction, honorific parsing, pagination,
and database storage.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from bs4 import BeautifulSoup

from hansard_tales.config.settings import ScraperConfig
from hansard_tales.models.base import Chamber
from hansard_tales.scrapers.mp import MPData, MPScraper


class TestMPScraper:
    """Test suite for MPScraper."""

    @pytest.fixture
    def config(self):
        """Create test scraper configuration."""
        return ScraperConfig(
            base_url="https://www.parliament.go.ke",
            download_dir=Path("data/pdfs"),
            max_retries=3,
            retry_delay=0.1,  # Faster for tests
            timeout=30,
            user_agent="HansardTales/1.0",
        )

    @pytest.fixture
    def scraper(self, config):
        """Create MP scraper instance."""
        return MPScraper(chamber=Chamber.NATIONAL_ASSEMBLY, config=config)

    @pytest.fixture
    def sample_html(self):
        """Load sample MP HTML from fixture."""
        fixture_path = Path("tests/fixtures/sample_mps.html")
        return fixture_path.read_text()

    def test_init(self, config):
        """Test MP scraper initialization."""
        scraper = MPScraper(chamber=Chamber.NATIONAL_ASSEMBLY, config=config)

        assert scraper.chamber == Chamber.NATIONAL_ASSEMBLY
        assert scraper.base_url == "https://www.parliament.go.ke"
        assert scraper.config == config

    def test_build_url_national_assembly(self, scraper):
        """Test URL building for National Assembly."""
        url = scraper._build_url(page=0, parliament_term=2022)

        assert "the-national-assembly/mps" in url
        assert "field_parliament_value=2022" in url
        assert "page=0" in url

    def test_build_url_senate(self, config):
        """Test URL building for Senate."""
        scraper = MPScraper(chamber=Chamber.SENATE, config=config)
        url = scraper._build_url(page=0, parliament_term=2022)

        assert "the-senate/senators" in url
        assert "field_parliament_value=2022" in url

    def test_build_url_pagination(self, scraper):
        """Test URL building with pagination."""
        url = scraper._build_url(page=5, parliament_term=2022)

        assert "page=5" in url

    def test_parse_honorifics_single(self, scraper):
        """Test parsing single honorific."""
        honorifics, clean_name = scraper._parse_honorifics("HON. JOHN DOE")

        assert honorifics == ["HON."]
        assert clean_name == "JOHN DOE"

    def test_parse_honorifics_multiple(self, scraper):
        """Test parsing multiple honorifics."""
        honorifics, clean_name = scraper._parse_honorifics("HON. (DR.) JANE SMITH")

        assert "HON." in honorifics
        assert "DR." in honorifics
        assert clean_name == "JANE SMITH"

    def test_parse_honorifics_amb(self, scraper):
        """Test parsing AMB. honorific."""
        honorifics, clean_name = scraper._parse_honorifics("HON. (AMB.) PETER JONES")

        assert "HON." in honorifics
        assert "AMB." in honorifics
        assert clean_name == "PETER JONES"

    def test_parse_honorifics_eng(self, scraper):
        """Test parsing ENG. honorific."""
        honorifics, clean_name = scraper._parse_honorifics("HON. (ENG.) MARY WILSON")

        assert "HON." in honorifics
        assert "ENG." in honorifics
        assert clean_name == "MARY WILSON"

    def test_parse_honorifics_no_honorific(self, scraper):
        """Test parsing name without honorific."""
        honorifics, clean_name = scraper._parse_honorifics("JOHN DOE")

        assert honorifics == []
        assert clean_name == "JOHN DOE"

    def test_get_total_pages(self, scraper, sample_html):
        """Test pagination detection."""
        soup = BeautifulSoup(sample_html, "html.parser")
        total_pages = scraper._get_total_pages(soup)

        # Sample HTML has page=34 as last page, so total is 35
        assert total_pages == 35

    def test_get_total_pages_no_pagination(self, scraper):
        """Test pagination detection with no pagination."""
        html = "<html><body><table></table></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        total_pages = scraper._get_total_pages(soup)

        assert total_pages == 1

    def test_extract_mps_from_page(self, scraper, sample_html):
        """Test MP data extraction from sample HTML."""
        soup = BeautifulSoup(sample_html, "html.parser")
        mps = scraper._extract_mps_from_page(soup, parliament_term=2022)

        # Sample HTML has 7 MPs (including one with empty name that should be skipped)
        assert len(mps) == 6  # 7 rows - 1 empty = 6 MPs

        # Check first valid MP
        mp = mps[0]
        assert mp.name == "HON. MEJJADONK, BENJAMIN GATHIRU"
        assert mp.clean_name == "MEJJADONK, BENJAMIN GATHIRU"
        assert "HON." in mp.honorifics
        assert mp.county == "NAIROBI"
        assert mp.constituency == "EMBAKASI CENTRAL"
        assert mp.party == "UDA"
        assert mp.status == "Elected"
        assert mp.parliament_term == 2022

    def test_extract_mps_honorific_amb(self, scraper, sample_html):
        """Test extraction of MP with AMB. honorific."""
        soup = BeautifulSoup(sample_html, "html.parser")
        mps = scraper._extract_mps_from_page(soup, parliament_term=2022)

        # Find MP with AMB. honorific
        amb_mp = next((mp for mp in mps if "AMB." in mp.honorifics), None)
        assert amb_mp is not None
        assert amb_mp.name == "HON. (AMB.) LANGAT BENJAMIN KIPKIRUI"
        assert "HON." in amb_mp.honorifics
        assert "AMB." in amb_mp.honorifics

    def test_extract_mps_honorific_dr(self, scraper, sample_html):
        """Test extraction of MP with DR. honorific."""
        soup = BeautifulSoup(sample_html, "html.parser")
        mps = scraper._extract_mps_from_page(soup, parliament_term=2022)

        # Find MP with DR. honorific
        dr_mp = next((mp for mp in mps if "DR." in mp.honorifics), None)
        assert dr_mp is not None
        assert "HON." in dr_mp.honorifics
        assert "DR." in dr_mp.honorifics

    def test_extract_mps_honorific_eng(self, scraper, sample_html):
        """Test extraction of MP with ENG. honorific."""
        soup = BeautifulSoup(sample_html, "html.parser")
        mps = scraper._extract_mps_from_page(soup, parliament_term=2022)

        # Find MP with ENG. honorific
        eng_mp = next((mp for mp in mps if "ENG." in mp.honorifics), None)
        assert eng_mp is not None
        assert eng_mp.name == "HON. (ENG.) NZAMBIA KITHUA THUDDEUS"
        assert "HON." in eng_mp.honorifics
        assert "ENG." in eng_mp.honorifics

    def test_extract_mps_empty_fields(self, scraper, sample_html):
        """Test handling of empty county/constituency fields."""
        soup = BeautifulSoup(sample_html, "html.parser")
        mps = scraper._extract_mps_from_page(soup, parliament_term=2022)

        # Find nominated MP with empty county/constituency
        nominated_mp = next((mp for mp in mps if mp.status == "Nominated"), None)
        assert nominated_mp is not None
        assert nominated_mp.county is None
        assert nominated_mp.constituency is None

    def test_extract_mps_status_elected(self, scraper, sample_html):
        """Test extraction of Elected status."""
        soup = BeautifulSoup(sample_html, "html.parser")
        mps = scraper._extract_mps_from_page(soup, parliament_term=2022)

        elected_mps = [mp for mp in mps if mp.status == "Elected"]
        assert len(elected_mps) > 0

    def test_extract_mps_status_nominated(self, scraper, sample_html):
        """Test extraction of Nominated status."""
        soup = BeautifulSoup(sample_html, "html.parser")
        mps = scraper._extract_mps_from_page(soup, parliament_term=2022)

        nominated_mps = [mp for mp in mps if mp.status == "Nominated"]
        assert len(nominated_mps) > 0

    def test_detect_duplicates_no_duplicates(self, scraper):
        """Test duplicate detection with no duplicates."""
        mps = [
            MPData(
                name="HON. JOHN DOE",
                clean_name="JOHN DOE",
                honorifics=["HON."],
                county="NAIROBI",
                constituency="WESTLANDS",
                party="UDA",
                status="Elected",
                profile_url="http://example.com/1",
                parliament_term=2022,
            ),
            MPData(
                name="HON. JANE SMITH",
                clean_name="JANE SMITH",
                honorifics=["HON."],
                county="MOMBASA",
                constituency="MVITA",
                party="ODM",
                status="Elected",
                profile_url="http://example.com/2",
                parliament_term=2022,
            ),
        ]

        duplicates = scraper.detect_duplicates(mps)
        assert len(duplicates) == 0

    def test_detect_duplicates_with_duplicates(self, scraper):
        """Test duplicate detection with duplicates."""
        mps = [
            MPData(
                name="HON. JOHN DOE",
                clean_name="JOHN DOE",
                honorifics=["HON."],
                county="NAIROBI",
                constituency="WESTLANDS",
                party="UDA",
                status="Elected",
                profile_url="http://example.com/1",
                parliament_term=2022,
            ),
            MPData(
                name="HON. (DR.) JOHN DOE",
                clean_name="JOHN DOE",
                honorifics=["HON.", "DR."],
                county="NAIROBI",
                constituency="WESTLANDS",
                party="UDA",
                status="Elected",
                profile_url="http://example.com/2",
                parliament_term=2022,
            ),
        ]

        duplicates = scraper.detect_duplicates(mps)
        assert len(duplicates) == 1
        assert duplicates[0][0].name == "HON. JOHN DOE"
        assert duplicates[0][1].name == "HON. (DR.) JOHN DOE"

    @patch("requests.Session.get")
    def test_scrape_mps_success(self, mock_get, scraper, sample_html):
        """Test successful MP scraping."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = sample_html.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Scrape MPs (limit to 1 page for test)
        mps = scraper.scrape_mps(parliament_term=2022, max_pages=1)

        # Verify results
        assert len(mps) > 0
        assert all(isinstance(mp, MPData) for mp in mps)
        assert all(mp.parliament_term == 2022 for mp in mps)

    @patch("requests.Session.get")
    def test_scrape_mps_no_mps_found(self, mock_get, scraper):
        """Test error when no MPs found."""
        # Setup mock response with empty table
        html = """
        <html>
            <body>
                <table class="cols-7">
                    <tbody></tbody>
                </table>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.content = html.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Should raise DataCollectionError
        from hansard_tales.scrapers.base import DataCollectionError

        with pytest.raises(DataCollectionError):
            scraper.scrape_mps(parliament_term=2022)

    @patch("hansard_tales.scrapers.mp.MPScraper.store_mps")
    def test_store_mps_called(self, mock_store, scraper):
        """Test that store_mps can be called."""
        mps = [
            MPData(
                name="HON. JOHN DOE",
                clean_name="JOHN DOE",
                honorifics=["HON."],
                county="NAIROBI",
                constituency="WESTLANDS",
                party="UDA",
                status="Elected",
                profile_url="http://example.com/1",
                parliament_term=2022,
            )
        ]

        mock_store.return_value = 1
        count = scraper.store_mps(mps)

        assert count == 1
        mock_store.assert_called_once_with(mps)
