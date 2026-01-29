"""
Integration tests for web scraper components.

Tests the complete scraping workflow including:
- Scraper factory creation
- URL extraction with pagination
- Document downloading
- Metadata extraction
- Filename standardization
- Duplicate detection
- Error handling
"""

import hashlib
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests
from bs4 import BeautifulSoup

from hansard_tales.config.settings import ScraperConfig
from hansard_tales.models import Chamber
from hansard_tales.scrapers import create_scraper
from hansard_tales.scrapers.base import BaseScraper, DataCollectionError, ScrapedDocument
from hansard_tales.scrapers.hansard import HansardScraper
from hansard_tales.scrapers.votes import VotesScraper


class TestScraperFactoryIntegration:
    """Integration tests for scraper factory."""

    def test_create_hansard_scraper(self):
        """Test creating Hansard scraper through factory."""
        config = ScraperConfig()
        scraper = create_scraper("hansard", config)

        assert isinstance(scraper, HansardScraper)
        assert isinstance(scraper, BaseScraper)
        assert scraper.config == config

    def test_create_votes_scraper(self):
        """Test creating Votes scraper through factory."""
        config = ScraperConfig()
        scraper = create_scraper("votes", config)

        assert isinstance(scraper, VotesScraper)
        assert isinstance(scraper, BaseScraper)
        assert scraper.config == config

    def test_create_invalid_scraper(self):
        """Test creating invalid scraper type raises error."""
        config = ScraperConfig()

        with pytest.raises(ValueError, match="No scraper available for document type"):
            create_scraper("invalid_type", config)


class TestHansardScraperIntegration:
    """Integration tests for Hansard scraper."""

    @pytest.fixture
    def scraper(self):
        """Create Hansard scraper for testing."""
        config = ScraperConfig(
            base_url="https://parliament.go.ke",
            max_retries=2,
            retry_delay=0.1,
            timeout=10,
        )
        return HansardScraper(config)

    @pytest.fixture
    def sample_html(self):
        """Sample HTML page with Hansard links."""
        return """
        <html>
            <body>
                <table class="cols-2">
                    <tbody>
                        <tr>
                            <td class="views-field-field-pdf">
                                <a href="/files/hansard_20251104_P.pdf">
                                    Hansard Report - Tuesday, 4th November 2025 (P)
                                </a>
                            </td>
                        </tr>
                        <tr>
                            <td class="views-field-field-pdf">
                                <a href="/files/hansard_20251105_A.pdf">
                                    Hansard Report - Wednesday, 5th November 2025 (A)
                                </a>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <nav class="pager">
                    <ul>
                        <li><a href="?page=0">1</a></li>
                        <li><a href="?page=1">2</a></li>
                    </ul>
                </nav>
            </body>
        </html>
        """

    def test_extract_urls_from_page(self, scraper, sample_html):
        """Test extracting URLs from HTML page."""
        soup = BeautifulSoup(sample_html, "html.parser")
        urls = scraper._extract_urls_from_page(soup)

        assert len(urls) == 2
        assert urls[0].endswith("hansard_20251104_P.pdf")
        assert urls[1].endswith("hansard_20251105_A.pdf")

    def test_get_total_pages(self, scraper, sample_html):
        """Test extracting total pages from pagination."""
        soup = BeautifulSoup(sample_html, "html.parser")
        total_pages = scraper._get_total_pages(soup)

        assert total_pages == 2

    def test_get_total_pages_no_pagination(self, scraper):
        """Test handling page with no pagination."""
        html = "<html><body><table class='cols-2'></table></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        total_pages = scraper._get_total_pages(soup)

        assert total_pages == 1

    def test_extract_metadata(self, scraper):
        """Test extracting metadata from Hansard filename."""
        url = "https://parliament.go.ke/files/Hansard%20Report%20-%20Tuesday%2C%204th%20November%202025%20%28P%29.pdf"
        content = b"PDF content"

        metadata = scraper.extract_metadata(url, content)

        assert metadata["document_type"] == "hansard"
        assert metadata["date"] == "2025-11-04"
        assert metadata["period"] == "P"

    def test_generate_standardized_filename(self, scraper):
        """Test generating standardized filename."""
        url = "https://parliament.go.ke/files/Hansard%20Report%20-%20Tuesday%2C%204th%20November%202025%20%28P%29.pdf"

        filename = scraper._generate_filename(url)

        assert filename == "hansard_20251104_P.pdf"

    def test_generate_filename_fallback(self, scraper):
        """Test filename generation falls back to original on parse failure."""
        url = "https://parliament.go.ke/files/unknown_format.pdf"

        filename = scraper._generate_filename(url)

        assert filename == "unknown_format.pdf"

    @patch("hansard_tales.scrapers.base.requests.Session.get")
    def test_download_document_success(self, mock_get, scraper):
        """Test successful document download."""
        # Mock response
        mock_response = Mock()
        mock_response.content = b"PDF content here"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = "https://parliament.go.ke/files/hansard_20251104_P.pdf"
        doc = scraper.download_document(url)

        assert isinstance(doc, ScrapedDocument)
        assert doc.url == url
        assert doc.content == b"PDF content here"
        assert doc.hash == hashlib.sha256(b"PDF content here").hexdigest()
        assert doc.filename == "hansard_20251104_P.pdf"

    @patch("hansard_tales.scrapers.base.requests.Session.get")
    def test_download_document_retry_on_failure(self, mock_get, scraper):
        """Test document download retries on failure."""
        # First call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = requests.RequestException("Network error")

        mock_response_success = Mock()
        mock_response_success.content = b"PDF content"
        mock_response_success.raise_for_status = Mock()

        mock_get.side_effect = [mock_response_fail, mock_response_success]

        url = "https://parliament.go.ke/files/test.pdf"
        doc = scraper.download_document(url)

        assert doc.content == b"PDF content"
        assert mock_get.call_count == 2

    @patch("hansard_tales.scrapers.base.requests.Session.get")
    def test_download_document_max_retries_exceeded(self, mock_get, scraper):
        """Test download fails after max retries."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.RequestException("Network error")
        mock_get.return_value = mock_response

        url = "https://parliament.go.ke/files/test.pdf"

        with pytest.raises(requests.RequestException):
            scraper.download_document(url)

        assert mock_get.call_count == scraper.config.max_retries

    def test_save_document(self, scraper):
        """Test saving document to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            doc = ScrapedDocument(
                url="https://test.com/doc.pdf",
                filename="test_doc.pdf",
                content=b"PDF content",
                hash="abc123",
                metadata={"type": "hansard"},
            )

            saved_path = scraper.save_document(doc, output_dir)

            assert saved_path.exists()
            assert saved_path.name == "test_doc.pdf"
            assert saved_path.read_bytes() == b"PDF content"

    @patch("hansard_tales.scrapers.base.requests.Session.get")
    def test_scrape_workflow_no_documents(self, mock_get, scraper):
        """Test scrape workflow when no documents found."""
        # Mock empty page
        mock_response = Mock()
        mock_response.content = b"<html><body><table class='cols-2'></table></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with pytest.raises(DataCollectionError, match="No Hansard documents found"):
            scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)


class TestVotesScraperIntegration:
    """Integration tests for Votes scraper."""

    @pytest.fixture
    def scraper(self):
        """Create Votes scraper for testing."""
        config = ScraperConfig(
            base_url="https://parliament.go.ke",
            max_retries=2,
            retry_delay=0.1,
            timeout=10,
        )
        return VotesScraper(config)

    def test_extract_metadata_with_time(self, scraper):
        """Test extracting metadata with time from Votes filename."""
        url = "https://parliament.go.ke/files/Tuesday%20%2CNovember%204%2C%202025%20at%202.30pm.pdf"
        content = b"PDF content"

        metadata = scraper.extract_metadata(url, content)

        assert metadata["document_type"] == "votes"
        assert metadata["date"] == "2025-11-04"
        assert metadata["time"] == "14:30"
        assert metadata["datetime_iso"] == "2025-11-04T14:30:00Z"

    def test_generate_standardized_filename_with_time(self, scraper):
        """Test generating standardized filename with time."""
        url = "https://parliament.go.ke/files/Tuesday%20%2CNovember%204%2C%202025%20at%202.30pm.pdf"

        filename = scraper._generate_filename(url)

        assert filename == "votes_20251104T143000Z.pdf"

    def test_time_conversion_am_to_24hour(self, scraper):
        """Test AM time conversion to 24-hour format."""
        url = "https://parliament.go.ke/files/Tuesday%20%2CNovember%204%2C%202025%20at%209.00am.pdf"

        metadata = scraper.extract_metadata(url, b"content")

        assert metadata["time"] == "09:00"

    def test_time_conversion_pm_to_24hour(self, scraper):
        """Test PM time conversion to 24-hour format."""
        url = "https://parliament.go.ke/files/Tuesday%20%2CNovember%204%2C%202025%20at%202.30pm.pdf"

        metadata = scraper.extract_metadata(url, b"content")

        assert metadata["time"] == "14:30"

    def test_time_conversion_noon(self, scraper):
        """Test noon (12 PM) time conversion."""
        url = (
            "https://parliament.go.ke/files/Tuesday%20%2CNovember%204%2C%202025%20at%2012.00pm.pdf"
        )

        metadata = scraper.extract_metadata(url, b"content")

        assert metadata["time"] == "12:00"

    def test_time_conversion_midnight(self, scraper):
        """Test midnight (12 AM) time conversion."""
        url = (
            "https://parliament.go.ke/files/Tuesday%20%2CNovember%204%2C%202025%20at%2012.00am.pdf"
        )

        metadata = scraper.extract_metadata(url, b"content")

        assert metadata["time"] == "00:00"


class TestScraperErrorHandling:
    """Integration tests for scraper error handling."""

    @pytest.fixture
    def scraper(self):
        """Create scraper for testing."""
        config = ScraperConfig(max_retries=2, retry_delay=0.1)
        return HansardScraper(config)

    @patch("hansard_tales.scrapers.base.requests.Session.get")
    def test_scrape_continues_on_single_document_error(self, mock_get, scraper):
        """Test that scraping continues when single document fails."""
        # First document succeeds, second fails, third succeeds
        responses = [
            # doc1 download
            Mock(content=b"PDF 1", raise_for_status=Mock()),
            # doc2 download (fails)
            Mock(raise_for_status=Mock(side_effect=requests.RequestException("Error"))),
            # doc3 download
            Mock(content=b"PDF 3", raise_for_status=Mock()),
        ]
        mock_get.side_effect = responses

        # Mock get_document_urls to return test URLs
        with patch.object(scraper, "get_document_urls") as mock_urls:
            mock_urls.return_value = [
                "https://test.com/doc1.pdf",
                "https://test.com/doc2.pdf",
                "https://test.com/doc3.pdf",
            ]

            documents = scraper.scrape(Chamber.NATIONAL_ASSEMBLY, skip_existing=False)

        # Should have 2 documents (doc1 and doc3), doc2 failed
        assert len(documents) == 2
        assert documents[0].content == b"PDF 1"
        assert documents[1].content == b"PDF 3"

    def test_duplicate_detection(self, scraper):
        """Test duplicate detection based on hash."""
        doc1 = ScrapedDocument(
            url="https://test.com/doc1.pdf",
            filename="doc1.pdf",
            content=b"Same content",
            hash=hashlib.sha256(b"Same content").hexdigest(),
            metadata={},
        )

        doc2 = ScrapedDocument(
            url="https://test.com/doc2.pdf",
            filename="doc2.pdf",
            content=b"Same content",
            hash=hashlib.sha256(b"Same content").hexdigest(),
            metadata={},
        )

        # Same hash means duplicate
        assert doc1.hash == doc2.hash


class TestScraperConfiguration:
    """Integration tests for scraper configuration."""

    def test_scraper_uses_custom_config(self):
        """Test that scraper uses custom configuration."""
        config = ScraperConfig(
            base_url="https://custom.url",
            max_retries=5,
            retry_delay=2.0,
            timeout=60,
            user_agent="CustomAgent/1.0",
        )

        scraper = HansardScraper(config)

        assert scraper.config.base_url == "https://custom.url"
        assert scraper.config.max_retries == 5
        assert scraper.config.retry_delay == 2.0
        assert scraper.config.timeout == 60
        assert scraper.session.headers["User-Agent"] == "CustomAgent/1.0"

    def test_scraper_default_config(self):
        """Test that scraper uses default configuration."""
        config = ScraperConfig()
        scraper = HansardScraper(config)

        assert scraper.config.base_url == "https://parliament.go.ke"
        assert scraper.config.max_retries == 3
        assert scraper.config.retry_delay == 1.0
        assert scraper.config.timeout == 30


class TestScraperChamberSupport:
    """Integration tests for chamber-specific scraping."""

    @pytest.fixture
    def scraper(self):
        """Create scraper for testing."""
        return HansardScraper(ScraperConfig())

    @patch("hansard_tales.scrapers.base.requests.Session.get")
    def test_national_assembly_url_construction(self, mock_get, scraper):
        """Test URL construction for National Assembly."""
        mock_response = Mock()
        mock_response.content = b"""
            <html><body>
                <table class="cols-2">
                    <tr><td class="views-field-field-pdf">
                        <a href="/files/test.pdf">Test</a>
                    </td></tr>
                </table>
            </body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify URL contains national-assembly
        call_args = mock_get.call_args[0][0]
        assert "/the-national-assembly/" in call_args
        assert "field_parliament_value=2022" in call_args

    @patch("hansard_tales.scrapers.base.requests.Session.get")
    def test_senate_url_construction(self, mock_get, scraper):
        """Test URL construction for Senate."""
        mock_response = Mock()
        mock_response.content = b"""
            <html><body>
                <table class="cols-2">
                    <tr><td class="views-field-field-pdf">
                        <a href="/files/test.pdf">Test</a>
                    </td></tr>
                </table>
            </body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        scraper.get_document_urls(Chamber.SENATE, parliament_term=2022)

        # Verify URL contains senate
        call_args = mock_get.call_args[0][0]
        assert "/the-senate/" in call_args
        assert "field_parliament_value=2022" in call_args
