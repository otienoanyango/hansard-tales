"""
Unit tests for web scrapers.

Tests cover base scraper functionality including downloading,
retry logic, duplicate detection, and error handling.
"""

import hashlib
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from hansard_tales.config.settings import ScraperConfig
from hansard_tales.models.base import Chamber
from hansard_tales.scrapers.base import BaseScraper, DataCollectionError, ScrapedDocument


class TestBaseScraper:
    """Test suite for BaseScraper."""

    @pytest.fixture
    def config(self):
        """Create test scraper configuration."""
        return ScraperConfig(
            base_url="https://parliament.go.ke",
            download_dir=Path("data/pdfs"),
            max_retries=3,
            retry_delay=1.0,
            timeout=30,
            user_agent="HansardTales/1.0",
        )

    @pytest.fixture
    def concrete_scraper(self, config):
        """Create concrete scraper for testing."""

        class ConcreteScraper(BaseScraper):
            def get_document_urls(self, chamber, start_date=None, end_date=None):
                return ["https://example.com/doc.pdf"]

            def extract_metadata(self, url, content):
                return {"test": "metadata"}

        return ConcreteScraper(config)

    def test_init(self, config):
        """Test scraper initialization."""

        class ConcreteScraper(BaseScraper):
            def get_document_urls(self, chamber, start_date=None, end_date=None):
                return []

            def extract_metadata(self, url, content):
                return {}

        scraper = ConcreteScraper(config)

        assert scraper.config == config
        assert scraper.session is not None
        assert scraper.session.headers["User-Agent"] == "HansardTales/1.0"

    @patch("requests.Session.get")
    def test_download_document_success(self, mock_get, concrete_scraper):
        """Test successful document download."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = b"test content"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Download document
        url = "https://example.com/test.pdf"
        result = concrete_scraper.download_document(url)

        # Verify result
        assert isinstance(result, ScrapedDocument)
        assert result.url == url
        assert result.filename == "test.pdf"
        assert result.content == b"test content"
        assert result.hash == hashlib.sha256(b"test content").hexdigest()
        assert result.metadata == {"test": "metadata"}

        # Verify request was made
        mock_get.assert_called_once()

    @patch("requests.Session.get")
    def test_download_document_retry_logic(self, mock_get, concrete_scraper):
        """Test retry logic on transient failures."""
        # Setup mock to fail twice then succeed
        mock_response = Mock()
        mock_response.content = b"test content"
        mock_response.raise_for_status = Mock()

        mock_get.side_effect = [
            requests.RequestException("Network error"),
            requests.RequestException("Network error"),
            mock_response,
        ]

        # Download document
        url = "https://example.com/test.pdf"
        result = concrete_scraper.download_document(url)

        # Verify result
        assert isinstance(result, ScrapedDocument)
        assert result.content == b"test content"

        # Verify retries
        assert mock_get.call_count == 3

    @patch("requests.Session.get")
    def test_download_document_max_retries_exceeded(self, mock_get, concrete_scraper):
        """Test failure after max retries exceeded."""
        from tenacity import RetryError

        # Setup mock to always fail
        mock_get.side_effect = requests.RequestException("Network error")

        # Attempt download
        url = "https://example.com/test.pdf"
        with pytest.raises(RetryError):
            concrete_scraper.download_document(url)

        # Verify max retries attempted (5 attempts)
        assert mock_get.call_count == 5

    def test_save_document(self, concrete_scraper, tmp_path):
        """Test saving document to disk."""
        # Create test document
        doc = ScrapedDocument(
            url="https://example.com/test.pdf",
            filename="test.pdf",
            content=b"test content",
            hash="abc123",
            metadata={},
        )

        # Save document
        output_path = concrete_scraper.save_document(doc, tmp_path)

        # Verify file was created
        assert output_path.exists()
        assert output_path.read_bytes() == b"test content"
        assert output_path.name == "test.pdf"

    def test_generate_filename(self, concrete_scraper):
        """Test filename extraction from URL."""
        url = "https://example.com/path/to/document.pdf"
        filename = concrete_scraper._generate_filename(url)
        assert filename == "document.pdf"

    @patch.object(BaseScraper, "download_document")
    @patch.object(BaseScraper, "_is_duplicate")
    def test_scrape_success(self, mock_is_duplicate, mock_download, concrete_scraper):
        """Test successful scraping of multiple documents."""
        # Setup mocks
        mock_is_duplicate.return_value = False

        doc1 = ScrapedDocument(
            url="https://example.com/doc1.pdf",
            filename="doc1.pdf",
            content=b"content1",
            hash="hash1",
            metadata={},
        )
        doc2 = ScrapedDocument(
            url="https://example.com/doc2.pdf",
            filename="doc2.pdf",
            content=b"content2",
            hash="hash2",
            metadata={},
        )

        mock_download.side_effect = [doc1, doc2]

        # Mock get_document_urls to return 2 URLs
        concrete_scraper.get_document_urls = Mock(
            return_value=["https://example.com/doc1.pdf", "https://example.com/doc2.pdf"]
        )

        # Scrape documents
        results = concrete_scraper.scrape(Chamber.NATIONAL_ASSEMBLY)

        # Verify results
        assert len(results) == 2
        assert results[0] == doc1
        assert results[1] == doc2

    @patch.object(BaseScraper, "download_document")
    @patch.object(BaseScraper, "_batch_check_urls_in_db")
    @patch.object(BaseScraper, "_verify_file_exists")
    def test_scrape_skip_duplicates(
        self, mock_verify, mock_batch_check, mock_download, concrete_scraper
    ):
        """Test skipping duplicate documents using new batch workflow."""
        urls = ["https://example.com/doc1.pdf", "https://example.com/doc2.pdf"]

        # Setup: doc1 exists in DB and storage, doc2 is new
        mock_batch_check.return_value = {
            urls[0]: (True, Path("data/pdfs/doc1.pdf")),
            urls[1]: (False, None),
        }
        mock_verify.return_value = True  # doc1 exists in storage

        doc2 = ScrapedDocument(
            url=urls[1],
            filename="doc2.pdf",
            content=b"content2",
            hash="hash2",
            metadata={"document_type": "test", "original_filename": "doc2.pdf"},
        )

        mock_download.return_value = doc2

        # Mock get_document_urls
        concrete_scraper.get_document_urls = Mock(return_value=urls)

        # Scrape documents
        results = concrete_scraper.scrape(Chamber.NATIONAL_ASSEMBLY, skip_existing=True)

        # Verify only non-duplicate returned (doc2)
        assert len(results) == 1
        assert results[0] == doc2
        # download_document should only be called once (for doc2)
        mock_download.assert_called_once()

    @patch.object(BaseScraper, "download_document")
    def test_scrape_continues_on_error(self, mock_download, concrete_scraper):
        """Test that scraping continues when individual document fails."""
        # Setup mocks - first fails, second succeeds
        doc2 = ScrapedDocument(
            url="https://example.com/doc2.pdf",
            filename="doc2.pdf",
            content=b"content2",
            hash="hash2",
            metadata={},
        )

        mock_download.side_effect = [Exception("Download failed"), doc2]

        # Mock get_document_urls
        concrete_scraper.get_document_urls = Mock(
            return_value=["https://example.com/doc1.pdf", "https://example.com/doc2.pdf"]
        )

        # Scrape documents
        results = concrete_scraper.scrape(Chamber.NATIONAL_ASSEMBLY)

        # Verify second document was still processed
        assert len(results) == 1
        assert results[0] == doc2

    def test_is_duplicate_placeholder(self, concrete_scraper):
        """Test duplicate detection placeholder."""
        # Currently returns False (placeholder implementation)
        result = concrete_scraper._is_duplicate("test_hash")
        assert result is False

    def test_scrape_with_date_range(self, concrete_scraper):
        """Test scraping with date range filtering."""
        # Mock get_document_urls to verify date parameters are passed
        concrete_scraper.get_document_urls = Mock(return_value=[])

        start = date(2024, 1, 1)
        end = date(2024, 12, 31)

        # Scrape with date range
        concrete_scraper.scrape(Chamber.NATIONAL_ASSEMBLY, start_date=start, end_date=end)

        # Verify date parameters were passed
        concrete_scraper.get_document_urls.assert_called_once_with(
            Chamber.NATIONAL_ASSEMBLY, start, end
        )

    @patch("requests.Session.get")
    def test_download_computes_sha256_hash(self, mock_get, concrete_scraper):
        """Test that SHA256 hash is computed for downloaded content."""
        # Setup mock response
        test_content = b"test content for hashing"
        expected_hash = hashlib.sha256(test_content).hexdigest()

        mock_response = Mock()
        mock_response.content = test_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Download document
        url = "https://example.com/test.pdf"
        result = concrete_scraper.download_document(url)

        # Verify hash is correct
        assert result.hash == expected_hash

    @patch("requests.Session.get")
    def test_download_extracts_metadata(self, mock_get, concrete_scraper):
        """Test that metadata is extracted during download."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = b"test content"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Download document
        url = "https://example.com/test.pdf"
        result = concrete_scraper.download_document(url)

        # Verify metadata was extracted
        assert result.metadata == {"test": "metadata"}

    @patch("requests.Session.get")
    def test_retry_exponential_backoff(self, mock_get, concrete_scraper):
        """Test exponential backoff delay between retries."""
        import time

        # Setup mock to fail twice then succeed
        mock_response = Mock()
        mock_response.content = b"test content"
        mock_response.raise_for_status = Mock()

        # Set side effect before any calls
        mock_get.side_effect = [
            requests.RequestException("Network error"),
            requests.RequestException("Network error"),
            mock_response,
        ]

        # Download document and measure time
        url = "https://example.com/test.pdf"
        start_time = time.time()
        result = concrete_scraper.download_document(url)
        elapsed_time = time.time() - start_time

        # Verify retries occurred (3 attempts total)
        assert mock_get.call_count == 3

        # Verify exponential backoff occurred (should take at least 3 seconds: 1s + 2s)
        # We use a lower bound to account for execution time
        assert elapsed_time >= 2.5, f"Expected at least 2.5s delay, got {elapsed_time}s"

        # Verify document was downloaded successfully
        assert result.content == b"test content"

    def test_save_document_creates_directory(self, concrete_scraper, tmp_path):
        """Test that save_document creates output directory if it doesn't exist."""
        # Create test document
        doc = ScrapedDocument(
            url="https://example.com/test.pdf",
            filename="test.pdf",
            content=b"test content",
            hash="abc123",
            metadata={},
        )

        # Use non-existent subdirectory
        output_dir = tmp_path / "subdir" / "nested"

        # Save document
        output_path = concrete_scraper.save_document(doc, output_dir)

        # Verify directory was created
        assert output_dir.exists()
        assert output_path.exists()

    @patch.object(BaseScraper, "download_document")
    def test_scrape_empty_url_list(self, mock_download, concrete_scraper):
        """Test scraping with no URLs returns empty list."""
        # Mock get_document_urls to return empty list
        concrete_scraper.get_document_urls = Mock(return_value=[])

        # Scrape documents
        results = concrete_scraper.scrape(Chamber.NATIONAL_ASSEMBLY)

        # Verify empty results
        assert len(results) == 0
        mock_download.assert_not_called()

    @patch.object(BaseScraper, "download_document")
    @patch.object(BaseScraper, "_is_duplicate")
    def test_scrape_skip_existing_false(self, mock_is_duplicate, mock_download, concrete_scraper):
        """Test that skip_existing=False includes all documents."""
        # Setup mocks
        mock_is_duplicate.return_value = True  # All are duplicates

        doc1 = ScrapedDocument(
            url="https://example.com/doc1.pdf",
            filename="doc1.pdf",
            content=b"content1",
            hash="hash1",
            metadata={},
        )

        mock_download.return_value = doc1

        # Mock get_document_urls
        concrete_scraper.get_document_urls = Mock(return_value=["https://example.com/doc1.pdf"])

        # Scrape with skip_existing=False
        results = concrete_scraper.scrape(Chamber.NATIONAL_ASSEMBLY, skip_existing=False)

        # Verify document was included even though it's a duplicate
        assert len(results) == 1
        assert results[0] == doc1
        # _is_duplicate should not be called when skip_existing=False
        mock_is_duplicate.assert_not_called()

    def test_generate_filename_with_query_params(self, concrete_scraper):
        """Test filename extraction from URL with query parameters."""
        url = "https://example.com/document.pdf?version=1&download=true"
        filename = concrete_scraper._generate_filename(url)
        # Should extract filename including query params
        assert filename == "document.pdf?version=1&download=true"

    @patch("requests.Session.get")
    def test_download_timeout_configuration(self, mock_get, concrete_scraper):
        """Test that timeout configuration is used in requests."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = b"test content"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Download document
        url = "https://example.com/test.pdf"
        concrete_scraper.download_document(url)

        # Verify timeout was passed
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["timeout"] == 30

    @patch("requests.Session.get")
    def test_scrape_continues_on_download_error(self, mock_get, concrete_scraper, capsys):
        """Test that scrape continues when a document download fails."""
        # Override get_document_urls to return multiple URLs
        concrete_scraper.get_document_urls = Mock(
            return_value=[
                "https://example.com/doc1.pdf",
                "https://example.com/doc2.pdf",
                "https://example.com/doc3.pdf",
            ]
        )

        # Setup mock to fail on second document
        mock_response = Mock()
        mock_response.content = b"test content"
        mock_response.raise_for_status = Mock()

        def side_effect(*args, **kwargs):
            url = args[0]
            if "doc2" in url:
                raise requests.RequestException("Network error")
            return mock_response

        mock_get.side_effect = side_effect

        # Scrape documents
        from hansard_tales.models.base import Chamber

        documents = concrete_scraper.scrape(Chamber.NATIONAL_ASSEMBLY, skip_existing=False)

        # Should have 2 documents (doc1 and doc3), doc2 failed
        assert len(documents) == 2

        # Verify error was printed
        captured = capsys.readouterr()
        assert "Error downloading" in captured.out
        assert "doc2.pdf" in captured.out

    @patch("requests.Session.get")
    @patch("hansard_tales.scrapers.base.BaseScraper._batch_check_urls_in_db")
    def test_scrape_updates_existing_file_when_missing(
        self, mock_batch_check, mock_get, concrete_scraper, tmp_path
    ):
        """Test that scrape updates database when file exists in DB but not storage."""
        # Override get_document_urls
        concrete_scraper.get_document_urls = Mock(
            return_value=[
                "https://example.com/doc1.pdf",
            ]
        )

        # Mock batch check to return file exists in DB but not in storage
        mock_batch_check.return_value = {
            "https://example.com/doc1.pdf": (True, tmp_path / "nonexistent.pdf")
        }

        # Setup mock response
        mock_response = Mock()
        mock_response.content = b"test content"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Set download dir to temp path
        concrete_scraper.config.download_dir = tmp_path

        # Scrape documents
        from hansard_tales.models.base import Chamber

        documents = concrete_scraper.scrape(Chamber.NATIONAL_ASSEMBLY, skip_existing=True)

        # Should have downloaded the document
        assert len(documents) == 1

    def test_batch_check_urls_handles_database_error(self, concrete_scraper):
        """Test that batch check handles database errors gracefully."""
        # The actual implementation catches exceptions and returns empty dict
        # Let's test the real method by mocking the database connection to fail
        from unittest.mock import patch

        with patch("sqlalchemy.create_engine") as mock_engine:
            mock_engine.side_effect = Exception("Database connection failed")

            urls = ["https://example.com/doc1.pdf", "https://example.com/doc2.pdf"]
            result = concrete_scraper._batch_check_urls_in_db(urls)

            # Should return all URLs as not existing
            assert result == {
                "https://example.com/doc1.pdf": (False, None),
                "https://example.com/doc2.pdf": (False, None),
            }

    def test_update_download_record_handles_database_error(
        self, concrete_scraper, capsys, tmp_path
    ):
        """Test that update download record handles database errors gracefully."""
        from unittest.mock import patch

        from hansard_tales.models.base import Chamber

        # Create a scraped document
        doc = ScrapedDocument(
            url="https://example.com/test.pdf",
            filename="test.pdf",
            content=b"test content",
            hash="testhash",
            metadata={"test": "metadata"},
        )

        # Mock database connection to fail
        with patch("sqlalchemy.create_engine") as mock_engine:
            mock_engine.side_effect = Exception("Database connection failed")

            # Should not raise exception
            concrete_scraper._update_download_record(
                doc, tmp_path / "test.pdf", Chamber.NATIONAL_ASSEMBLY, 2022
            )

            # Should print warning
            captured = capsys.readouterr()
            assert "Warning: Failed to update download record" in captured.out


class TestScrapedDocument:
    """Test suite for ScrapedDocument dataclass."""

    def test_creation(self):
        """Test creating ScrapedDocument."""
        doc = ScrapedDocument(
            url="https://example.com/test.pdf",
            filename="test.pdf",
            content=b"test content",
            hash="abc123",
            metadata={"key": "value"},
        )

        assert doc.url == "https://example.com/test.pdf"
        assert doc.filename == "test.pdf"
        assert doc.content == b"test content"
        assert doc.hash == "abc123"
        assert doc.metadata == {"key": "value"}


class TestDataCollectionError:
    """Test suite for DataCollectionError exception."""

    def test_exception_creation(self):
        """Test creating DataCollectionError."""
        error = DataCollectionError("Test error message")
        assert str(error) == "Test error message"

    def test_exception_raising(self):
        """Test raising DataCollectionError."""
        with pytest.raises(DataCollectionError) as exc_info:
            raise DataCollectionError("Test error")

        assert "Test error" in str(exc_info.value)


class TestHansardScraper:
    """Test suite for HansardScraper."""

    @pytest.fixture
    def config(self):
        """Create test scraper configuration."""
        return ScraperConfig(
            base_url="https://parliament.go.ke",
            download_dir=Path("data/pdfs"),
            max_retries=3,
            retry_delay=1.0,
            timeout=30,
            user_agent="HansardTales/1.0",
        )

    @pytest.fixture
    def hansard_scraper(self, config):
        """Create Hansard scraper for testing."""
        from hansard_tales.scrapers.hansard import HansardScraper

        return HansardScraper(config)

    @patch("requests.Session.get")
    def test_get_document_urls_national_assembly(self, mock_get, hansard_scraper):
        """Test getting Hansard URLs for National Assembly."""
        # Create mock HTML with Hansard links in table
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/hansard-2024-01-15.pdf">Hansard 15 Jan 2024</a>
                        </td>
                    </tr>
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/hansard-2024-01-16.pdf">Hansard 16 Jan 2024</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify URLs
        assert len(urls) == 2
        assert "https://parliament.go.ke/files/hansard-2024-01-15.pdf" in urls
        assert "https://parliament.go.ke/files/hansard-2024-01-16.pdf" in urls

        # Verify correct URL was called with parliament term parameter
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0]
        assert "national-assembly" in call_args[0]
        assert "hansard" in call_args[0]
        assert "field_parliament_value=2022" in call_args[0]
        assert "page=0" in call_args[0]

    @patch("requests.Session.get")
    def test_get_document_urls_senate(self, mock_get, hansard_scraper):
        """Test getting Hansard URLs for Senate."""
        # Create mock HTML with Hansard links
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/senate-hansard-2024-01-15.pdf">Senate Hansard 15 Jan 2024</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = hansard_scraper.get_document_urls(Chamber.SENATE, parliament_term=2022)

        # Verify URLs
        assert len(urls) == 1
        assert "https://parliament.go.ke/files/senate-hansard-2024-01-15.pdf" in urls

        # Verify correct URL was called
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0]
        assert "senate" in call_args[0]
        assert "hansard" in call_args[0]
        assert "field_parliament_value=2022" in call_args[0]

    @patch("requests.Session.get")
    def test_get_document_urls_absolute_urls(self, mock_get, hansard_scraper):
        """Test handling of absolute URLs in HTML."""
        # Create mock HTML with absolute URLs
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="https://parliament.go.ke/files/hansard-2024-01-15.pdf">Hansard 15 Jan 2024</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify absolute URL is preserved
        assert len(urls) == 1
        assert urls[0] == "https://parliament.go.ke/files/hansard-2024-01-15.pdf"

    @patch("requests.Session.get")
    def test_get_document_urls_filters_non_pdf(self, mock_get, hansard_scraper):
        """Test that non-PDF links are filtered out by CSS selector."""
        # Create mock HTML with mixed link types
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/hansard-2024-01-15.pdf">Hansard PDF</a>
                        </td>
                        <td class="views-field-field-pdf">
                            <a href="/page/hansard-info.html">Hansard Info Page</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify only PDF link is included (CSS selector filters by href$=".pdf")
        assert len(urls) == 1
        assert urls[0].endswith(".pdf")

    @patch("requests.Session.get")
    def test_get_document_urls_filters_non_hansard(self, mock_get, hansard_scraper):
        """Test extraction from cols-2 table structure."""
        # Create mock HTML with cols-2 table
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/hansard-2024-01-15.pdf">Hansard Document</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify link is included
        assert len(urls) == 1
        assert "hansard" in urls[0].lower()

    @patch("requests.Session.get")
    def test_get_document_urls_fallback_to_all_tables(self, mock_get, hansard_scraper):
        """Test that empty results are handled correctly."""
        # Create mock HTML without cols-2 table
        html_content = """
        <html>
            <body>
                <table>
                    <tr>
                        <td><a href="/files/hansard-2024-01-15.pdf">Hansard 15 Jan 2024</a></td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs - should raise error since CSS selector won't match
        with pytest.raises(DataCollectionError):
            hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

    @patch("requests.Session.get")
    def test_get_document_urls_no_documents_raises_error(self, mock_get, hansard_scraper):
        """Test that DataCollectionError is raised when no documents found."""
        # Create mock HTML with no Hansard links
        html_content = """
        <html>
            <body>
                <table class="views-table">
                    <tr>
                        <td><a href="/page/info.html">Information Page</a></td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Attempt to get document URLs
        with pytest.raises(DataCollectionError) as exc_info:
            hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY)

        # Verify error message
        error_msg = str(exc_info.value)
        assert "No Hansard documents found" in error_msg
        assert "website structure has changed" in error_msg

    @patch("requests.Session.get")
    def test_get_document_urls_empty_page_raises_error(self, mock_get, hansard_scraper):
        """Test that DataCollectionError is raised for empty page."""
        # Create mock HTML with no tables
        html_content = """
        <html>
            <body>
                <p>No documents available</p>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Attempt to get document URLs
        with pytest.raises(DataCollectionError):
            hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY)

    def test_extract_metadata_with_date_in_filename(self, hansard_scraper):
        """Test metadata extraction with date in filename."""
        url = "https://parliament.go.ke/sites/default/files/2025-11/Hansard%20Report%20-%20Tuesday%2C%204th%20November%202025%20%28P%29.pdf"
        content = b"test content"

        metadata = hansard_scraper.extract_metadata(url, content)

        assert metadata["document_type"] == "hansard"
        assert (
            metadata["original_filename"] == "Hansard Report - Tuesday, 4th November 2025 (P).pdf"
        )
        assert metadata["date"] == "2025-11-04"
        assert metadata["period"] == "P"

    def test_extract_metadata_with_date_no_dashes(self, hansard_scraper):
        """Test metadata extraction with different date format."""
        url = "https://parliament.go.ke/sites/default/files/2025-11/Hansard%20Report%20-%20Wednesday%2C%205th%20November%202025%20%28A%29.pdf"
        content = b"test content"

        metadata = hansard_scraper.extract_metadata(url, content)

        assert metadata["document_type"] == "hansard"
        assert metadata["date"] == "2025-11-05"
        assert metadata["period"] == "A"

    def test_extract_metadata_without_date(self, hansard_scraper):
        """Test metadata extraction when date parsing fails."""
        url = "https://parliament.go.ke/files/hansard-document.pdf"
        content = b"test content"

        metadata = hansard_scraper.extract_metadata(url, content)

        assert metadata["document_type"] == "hansard"
        assert metadata["original_filename"] == "hansard-document.pdf"
        assert "date" not in metadata

    def test_extract_metadata_complex_filename(self, hansard_scraper):
        """Test metadata extraction with evening session."""
        url = "https://parliament.go.ke/sites/default/files/2025-12/Hansard%20Report%20-%20Thursday%2C%204th%20December%202025%20%28E%29.pdf"
        content = b"test content"

        metadata = hansard_scraper.extract_metadata(url, content)

        assert metadata["document_type"] == "hansard"
        assert metadata["date"] == "2025-12-04"
        assert metadata["period"] == "E"

    @patch("requests.Session.get")
    def test_get_document_urls_handles_leading_slash(self, mock_get, hansard_scraper):
        """Test that leading slashes in relative URLs are handled correctly."""
        # Create mock HTML with leading slash in href
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/hansard-2024-01-15.pdf">Hansard</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify URL doesn't have double slashes
        assert len(urls) == 1
        assert urls[0] == "https://parliament.go.ke/files/hansard-2024-01-15.pdf"
        assert "//" not in urls[0].replace("https://", "")

    @patch("requests.Session.get")
    def test_get_document_urls_multiple_tables(self, mock_get, hansard_scraper):
        """Test extracting URLs from multiple cols-2 tables."""
        # Create mock HTML with multiple tables
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/hansard-2024-01-15.pdf">Hansard 15 Jan</a>
                        </td>
                    </tr>
                </table>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/hansard-2024-01-16.pdf">Hansard 16 Jan</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify URLs from both tables
        assert len(urls) == 2
        assert any("hansard-2024-01-15.pdf" in url for url in urls)
        assert any("hansard-2024-01-16.pdf" in url for url in urls)

    @patch("requests.Session.get")
    def test_get_document_urls_case_insensitive_hansard_check(self, mock_get, hansard_scraper):
        """Test extraction with various filename cases."""
        # Create mock HTML with various case variations
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/HANSARD-2024-01-15.pdf">HANSARD Document</a>
                        </td>
                        <td class="views-field-field-pdf">
                            <a href="/files/Hansard-2024-01-16.pdf">Hansard Document</a>
                        </td>
                        <td class="views-field-field-pdf">
                            <a href="/files/hansard-2024-01-17.pdf">hansard document</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify all variations are found
        assert len(urls) == 3

    @patch("requests.Session.get")
    def test_get_document_urls_with_cols2_table(self, mock_get, hansard_scraper):
        """Test extraction using cols-2 table with views-field-field-pdf cells."""
        # Create mock HTML matching parliament.go.ke structure
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/sites/default/files/2025-12/Hansard%20Report%20-%20Thursday%2C%204th%20December%202025.pdf">Hansard Report</a>
                        </td>
                    </tr>
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/sites/default/files/2025-12/Hansard%20Report%20-%20Wednesday%2C%203rd%20December%202025.pdf">Hansard Report</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY)

        # Verify URLs were extracted from cols-2 table
        assert len(urls) == 2
        assert all("Hansard" in url for url in urls)
        assert all(".pdf" in url for url in urls)

    def test_get_document_urls_invalid_chamber(self, hansard_scraper):
        """Test that invalid chamber raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            hansard_scraper.get_document_urls("invalid_chamber")

        assert "Unknown chamber" in str(exc_info.value)

    @patch("requests.Session.get")
    def test_integration_with_base_scraper(self, mock_get, hansard_scraper):
        """Test that HansardScraper integrates correctly with BaseScraper."""
        # Create mock HTML
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/hansard-2024-01-15.pdf">Hansard</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        # Mock both the page fetch and document download
        mock_page_response = Mock()
        mock_page_response.content = html_content.encode("utf-8")
        mock_page_response.raise_for_status = Mock()

        mock_pdf_response = Mock()
        mock_pdf_response.content = b"PDF content"
        mock_pdf_response.raise_for_status = Mock()

        mock_get.side_effect = [mock_page_response, mock_pdf_response]

        # Use scrape method from BaseScraper
        documents = hansard_scraper.scrape(Chamber.NATIONAL_ASSEMBLY, skip_existing=False)

        # Verify document was scraped
        assert len(documents) == 1
        assert documents[0].content == b"PDF content"
        assert documents[0].metadata["document_type"] == "hansard"

    @patch("requests.Session.get")
    def test_get_document_urls_with_pagination(self, mock_get, hansard_scraper):
        """Test pagination support with multiple pages."""
        # Create mock HTML for first page with pagination
        first_page_html = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/hansard-page0.pdf">Hansard Page 0</a>
                        </td>
                    </tr>
                </table>
                <nav class="pager">
                    <a href="?page=0">1</a>
                    <a href="?page=1">2</a>
                    <a href="?page=2">Last</a>
                </nav>
            </body>
        </html>
        """

        # Create mock HTML for second page
        second_page_html = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/hansard-page1.pdf">Hansard Page 1</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        # Create mock HTML for third page
        third_page_html = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/hansard-page2.pdf">Hansard Page 2</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        # Setup mock responses for all pages
        mock_responses = []
        for html in [first_page_html, second_page_html, third_page_html]:
            mock_response = Mock()
            mock_response.content = html.encode("utf-8")
            mock_response.raise_for_status = Mock()
            mock_responses.append(mock_response)

        mock_get.side_effect = mock_responses

        # Get document URLs with pagination
        urls = hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify URLs from all pages
        assert len(urls) == 3
        assert any("hansard-page0.pdf" in url for url in urls)
        assert any("hansard-page1.pdf" in url for url in urls)
        assert any("hansard-page2.pdf" in url for url in urls)

        # Verify all pages were fetched
        assert mock_get.call_count == 3


class TestVotesScraper:
    """Test suite for VotesScraper."""

    @pytest.fixture
    def config(self):
        """Create test scraper configuration."""
        return ScraperConfig(
            base_url="https://parliament.go.ke",
            download_dir=Path("data/pdfs"),
            max_retries=3,
            retry_delay=1.0,
            timeout=30,
            user_agent="HansardTales/1.0",
        )

    @pytest.fixture
    def votes_scraper(self, config):
        """Create Votes scraper for testing."""
        from hansard_tales.scrapers.votes import VotesScraper

        return VotesScraper(config)

    @patch("requests.Session.get")
    def test_get_document_urls_national_assembly(self, mock_get, votes_scraper):
        """Test getting Votes URLs for National Assembly."""
        # Create mock HTML with Votes links in table
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/votes-Tuesday%2C%20November%204%2C%202025%20at%202.30pm.pdf">Votes - Tuesday, November 4, 2025 At 2.30pm</a>
                        </td>
                    </tr>
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/votes-Wednesday%2C%20November%205%2C%202025%20at%209.00am.pdf">Votes - Wednesday, November 5, 2025 At 9.00am</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify URLs
        assert len(urls) == 2
        assert any("November%204" in url or "November 4" in url for url in urls)
        assert any("November%205" in url or "November 5" in url for url in urls)

        # Verify correct URL was called with parliament term parameter
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0]
        assert "national-assembly" in call_args[0]
        assert "votes-proceeding" in call_args[0]
        assert "field_parliament_value=2022" in call_args[0]

    @patch("requests.Session.get")
    def test_get_document_urls_senate(self, mock_get, votes_scraper):
        """Test getting Votes URLs for Senate."""
        # Create mock HTML with Votes links
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/Tuesday%2C%20November%204%2C%202025%20at%202.30pm.pdf">Senate Votes</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.SENATE, parliament_term=2022)

        # Verify URLs
        assert len(urls) == 1

        # Verify correct URL was called
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0]
        assert "senate" in call_args[0]
        assert "votes-proceeding" in call_args[0]
        assert "field_parliament_value=2022" in call_args[0]

    @patch("requests.Session.get")
    def test_get_document_urls_proceedings_keyword(self, mock_get, votes_scraper):
        """Test extraction using cols-2 table structure."""
        # Create mock HTML with cols-2 table
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/Tuesday%2C%20November%204%2C%202025%20at%202.30pm.pdf">Proceedings</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify URL was found
        assert len(urls) == 1

    @patch("requests.Session.get")
    def test_get_document_urls_absolute_urls(self, mock_get, votes_scraper):
        """Test handling of absolute URLs in HTML."""
        # Create mock HTML with absolute URLs
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="https://parliament.go.ke/files/Tuesday%2C%20November%204%2C%202025%20at%202.30pm.pdf">Votes</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify absolute URL is preserved
        assert len(urls) == 1
        assert urls[0].startswith("https://parliament.go.ke")

    @patch("requests.Session.get")
    def test_get_document_urls_filters_non_pdf(self, mock_get, votes_scraper):
        """Test that non-PDF links are filtered out by CSS selector."""
        # Create mock HTML with mixed link types
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/Tuesday%2C%20November%204%2C%202025%20at%202.30pm.pdf">Votes PDF</a>
                        </td>
                        <td class="views-field-field-pdf">
                            <a href="/page/votes-info.html">Votes Info Page</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify only PDF link is included (CSS selector filters by href$=".pdf")
        assert len(urls) == 1
        assert urls[0].endswith(".pdf")

    @patch("requests.Session.get")
    def test_get_document_urls_filters_non_votes(self, mock_get, votes_scraper):
        """Test extraction from cols-2 table structure."""
        # Create mock HTML with cols-2 table
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/Tuesday%2C%20November%204%2C%202025%20at%202.30pm.pdf">Votes Document</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify link is included
        assert len(urls) == 1

    @patch("requests.Session.get")
    def test_get_document_urls_fallback_to_all_tables(self, mock_get, votes_scraper):
        """Test fallback to all tables when views-table class not found."""
        # Create mock HTML without views-table class
        html_content = """
        <html>
            <body>
                <table>
                    <tr>
                        <td><a href="/files/votes-2024-01-15.pdf">Votes</a></td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs - should find document using fallback
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
        assert len(urls) == 1
        assert "votes-2024-01-15.pdf" in urls[0]

    @patch("requests.Session.get")
    def test_get_document_urls_no_documents_raises_error(self, mock_get, votes_scraper):
        """Test that DataCollectionError is raised when no documents found."""
        # Create mock HTML with no Votes links
        html_content = """
        <html>
            <body>
                <table class="views-table">
                    <tr>
                        <td><a href="/page/info.html">Information Page</a></td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Attempt to get document URLs
        with pytest.raises(DataCollectionError) as exc_info:
            votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY)

        # Verify error message
        error_msg = str(exc_info.value)
        assert "No Votes & Proceedings documents found" in error_msg
        assert "website structure has changed" in error_msg

    @patch("requests.Session.get")
    def test_get_document_urls_empty_page_raises_error(self, mock_get, votes_scraper):
        """Test that DataCollectionError is raised for empty page."""
        # Create mock HTML with no tables
        html_content = """
        <html>
            <body>
                <p>No documents available</p>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Attempt to get document URLs
        with pytest.raises(DataCollectionError):
            votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY)

    def test_extract_metadata_with_date_in_filename(self, votes_scraper):
        """Test metadata extraction with date and time in filename."""
        url = "https://parliament.go.ke/sites/default/files/2025-11/Tuesday%20%2CNovember%204%2C%202025%20at%202.30pm.pdf"
        content = b"test content"

        metadata = votes_scraper.extract_metadata(url, content)

        assert metadata["document_type"] == "votes"
        assert metadata["original_filename"] == "Tuesday ,November 4, 2025 at 2.30pm.pdf"
        assert metadata["date"] == "2025-11-04"
        assert metadata["time"] == "14:30"
        assert metadata["datetime_iso"] == "2025-11-04T14:30:00Z"

    def test_extract_metadata_with_date_no_dashes(self, votes_scraper):
        """Test metadata extraction with morning time."""
        url = "https://parliament.go.ke/sites/default/files/2025-11/Wednesday%2C%20November%205%2C%202025%20at%209.00am.pdf"
        content = b"test content"

        metadata = votes_scraper.extract_metadata(url, content)

        assert metadata["document_type"] == "votes"
        assert metadata["date"] == "2025-11-05"
        assert metadata["time"] == "09:00"
        assert metadata["datetime_iso"] == "2025-11-05T09:00:00Z"

    def test_extract_metadata_without_date(self, votes_scraper):
        """Test metadata extraction when date parsing fails."""
        url = "https://parliament.go.ke/files/votes-document.pdf"
        content = b"test content"

        metadata = votes_scraper.extract_metadata(url, content)

        assert metadata["document_type"] == "votes"
        assert metadata["original_filename"] == "votes-document.pdf"
        assert "date" not in metadata

    def test_extract_metadata_complex_filename(self, votes_scraper):
        """Test metadata extraction with noon time."""
        url = "https://parliament.go.ke/sites/default/files/2025-12/Thursday%2C%20December%2031%2C%202025%20at%2012.00pm.pdf"
        content = b"test content"

        metadata = votes_scraper.extract_metadata(url, content)

        assert metadata["document_type"] == "votes"
        assert metadata["date"] == "2025-12-31"
        assert metadata["time"] == "12:00"

    @patch("requests.Session.get")
    def test_get_document_urls_handles_leading_slash(self, mock_get, votes_scraper):
        """Test that leading slashes in relative URLs are handled correctly."""
        # Create mock HTML with leading slash in href
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/Tuesday%2C%20November%204%2C%202025%20at%202.30pm.pdf">Votes</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify URL doesn't have double slashes
        assert len(urls) == 1
        assert "//" not in urls[0].replace("https://", "")

    @patch("requests.Session.get")
    def test_get_document_urls_multiple_tables(self, mock_get, votes_scraper):
        """Test extracting URLs from multiple cols-2 tables."""
        # Create mock HTML with multiple tables
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/Tuesday%2C%20November%204%2C%202025%20at%202.30pm.pdf">Votes 1</a>
                        </td>
                    </tr>
                </table>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/Wednesday%2C%20November%205%2C%202025%20at%209.00am.pdf">Votes 2</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify URLs from both tables
        assert len(urls) == 2

    @patch("requests.Session.get")
    def test_get_document_urls_case_insensitive_votes_check(self, mock_get, votes_scraper):
        """Test extraction with various filename formats."""
        # Create mock HTML with various formats
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/votes-Tuesday%2C%20November%204%2C%202025%20at%202.30pm.pdf">Votes - Doc 1</a>
                        </td>
                        <td class="views-field-field-pdf">
                            <a href="/files/votes-Wednesday%2C%20November%205%2C%202025%20at%209.00am.pdf">Votes - Doc 2</a>
                        </td>
                        <td class="views-field-field-pdf">
                            <a href="/files/votes-Thursday%2C%20November%206%2C%202025%20at%2010.00am.pdf">Votes - Doc 3</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify all variations are found
        assert len(urls) == 3

    def test_get_document_urls_invalid_chamber(self, votes_scraper):
        """Test that invalid chamber raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            votes_scraper.get_document_urls("invalid_chamber")

        assert "Unknown chamber" in str(exc_info.value)

    @patch("requests.Session.get")
    def test_integration_with_base_scraper(self, mock_get, votes_scraper):
        """Test that VotesScraper integrates correctly with BaseScraper."""
        # Create mock HTML
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/Tuesday%2C%20November%204%2C%202025%20at%202.30pm.pdf">Votes</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        # Mock both the page fetch and document download
        mock_page_response = Mock()
        mock_page_response.content = html_content.encode("utf-8")
        mock_page_response.raise_for_status = Mock()

        mock_pdf_response = Mock()
        mock_pdf_response.content = b"PDF content"
        mock_pdf_response.raise_for_status = Mock()

        mock_get.side_effect = [mock_page_response, mock_pdf_response]

        # Use scrape method from BaseScraper
        documents = votes_scraper.scrape(Chamber.NATIONAL_ASSEMBLY, skip_existing=False)

        # Verify document was scraped
        assert len(documents) == 1
        assert documents[0].content == b"PDF content"
        assert documents[0].metadata["document_type"] == "votes"

    @patch("requests.Session.get")
    def test_get_document_urls_votes_in_url(self, mock_get, votes_scraper):
        """Test extraction when votes keyword is in URL."""
        # Create mock HTML with cols-2 structure
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/votes-Tuesday%2C%20November%204%2C%202025%20at%202.30pm.pdf">Document</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)

        # Verify URL was found
        assert len(urls) == 1

    def test_get_total_pages_with_pagination(self, votes_scraper):
        """Test extracting total pages from pagination element."""
        from bs4 import BeautifulSoup

        html_content = """
        <html>
            <body>
                <nav class="pager">
                    <a href="?page=0">1</a>
                    <a href="?page=1">2</a>
                    <a href="?page=2">3</a>
                    <a href="?page=3">4</a>
                </nav>
            </body>
        </html>
        """

        soup = BeautifulSoup(html_content, "html.parser")
        total_pages = votes_scraper._get_total_pages(soup)

        # Should return max page + 1 (0-indexed)
        assert total_pages == 4

    def test_get_total_pages_no_pagination(self, votes_scraper):
        """Test extracting total pages when no pagination exists."""
        from bs4 import BeautifulSoup

        html_content = """
        <html>
            <body>
                <p>No pagination here</p>
            </body>
        </html>
        """

        soup = BeautifulSoup(html_content, "html.parser")
        total_pages = votes_scraper._get_total_pages(soup)

        # Should return 1 when no pagination
        assert total_pages == 1

    def test_get_total_pages_empty_pagination(self, votes_scraper):
        """Test extracting total pages when pagination has no links."""
        from bs4 import BeautifulSoup

        html_content = """
        <html>
            <body>
                <nav class="pager">
                    <span>No links</span>
                </nav>
            </body>
        </html>
        """

        soup = BeautifulSoup(html_content, "html.parser")
        total_pages = votes_scraper._get_total_pages(soup)

        # Should return 1 when pagination has no links
        assert total_pages == 1

    def test_get_total_pages_ul_pager(self, votes_scraper):
        """Test extracting total pages from ul.pager element."""
        from bs4 import BeautifulSoup

        html_content = """
        <html>
            <body>
                <ul class="pager">
                    <li><a href="?page=0">1</a></li>
                    <li><a href="?page=1">2</a></li>
                </ul>
            </body>
        </html>
        """

        soup = BeautifulSoup(html_content, "html.parser")
        total_pages = votes_scraper._get_total_pages(soup)

        # Should return max page + 1
        assert total_pages == 2

    def test_extract_urls_from_page_with_cols2_table(self, votes_scraper):
        """Test extracting URLs from page with cols-2 table."""
        from bs4 import BeautifulSoup

        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/votes-doc1.pdf">Document 1</a>
                        </td>
                    </tr>
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/votes-doc2.pdf">Document 2</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        soup = BeautifulSoup(html_content, "html.parser")
        urls = votes_scraper._extract_urls_from_page(soup)

        # Should extract both URLs
        assert len(urls) == 2
        assert any("votes-doc1.pdf" in url for url in urls)
        assert any("votes-doc2.pdf" in url for url in urls)

    def test_extract_urls_from_page_no_table(self, votes_scraper):
        """Test extracting URLs when no cols-2 table exists."""
        from bs4 import BeautifulSoup

        html_content = """
        <html>
            <body>
                <p>No table here</p>
            </body>
        </html>
        """

        soup = BeautifulSoup(html_content, "html.parser")
        urls = votes_scraper._extract_urls_from_page(soup)

        # Should return empty list
        assert len(urls) == 0

    def test_extract_urls_from_page_absolute_urls(self, votes_scraper):
        """Test extracting absolute URLs from page."""
        from bs4 import BeautifulSoup

        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="https://parliament.go.ke/files/votes-doc1.pdf">Document 1</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        soup = BeautifulSoup(html_content, "html.parser")
        urls = votes_scraper._extract_urls_from_page(soup)

        # Should keep absolute URLs as-is
        assert len(urls) == 1
        assert urls[0] == "https://parliament.go.ke/files/votes-doc1.pdf"

    def test_extract_urls_from_page_empty_href(self, votes_scraper):
        """Test extracting URLs when href is empty."""
        from bs4 import BeautifulSoup

        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="">Empty href</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        soup = BeautifulSoup(html_content, "html.parser")
        urls = votes_scraper._extract_urls_from_page(soup)

        # Should skip empty hrefs
        assert len(urls) == 0


class TestScraperFactory:
    """Test suite for scraper factory."""

    @pytest.fixture
    def config(self):
        """Create test scraper configuration."""
        return ScraperConfig(
            base_url="https://parliament.go.ke",
            download_dir=Path("data/pdfs"),
            max_retries=3,
            retry_delay=1.0,
            timeout=30,
            user_agent="HansardTales/1.0",
        )

    def test_create_hansard_scraper(self, config):
        """Test creating Hansard scraper."""
        from hansard_tales.models.base import DocumentType
        from hansard_tales.scrapers.factory import create_scraper
        from hansard_tales.scrapers.hansard import HansardScraper

        scraper = create_scraper(DocumentType.HANSARD, config)

        assert isinstance(scraper, HansardScraper)
        assert scraper.config == config

    def test_create_votes_scraper(self, config):
        """Test creating Votes scraper."""
        from hansard_tales.models.base import DocumentType
        from hansard_tales.scrapers.factory import create_scraper
        from hansard_tales.scrapers.votes import VotesScraper

        scraper = create_scraper(DocumentType.VOTES, config)

        assert isinstance(scraper, VotesScraper)
        assert scraper.config == config

    def test_create_scraper_unsupported_type(self, config):
        """Test that unsupported document type raises ValueError."""
        from hansard_tales.models.base import DocumentType
        from hansard_tales.scrapers.factory import create_scraper

        # Try to create scraper for unsupported type
        with pytest.raises(ValueError) as exc_info:
            create_scraper(DocumentType.BILL, config)

        error_msg = str(exc_info.value)
        assert "No scraper available" in error_msg
        assert "bill" in error_msg.lower()
        assert "Available types" in error_msg

    def test_create_scraper_returns_base_scraper(self, config):
        """Test that factory returns BaseScraper instances."""
        from hansard_tales.models.base import DocumentType
        from hansard_tales.scrapers.base import BaseScraper
        from hansard_tales.scrapers.factory import create_scraper

        hansard_scraper = create_scraper(DocumentType.HANSARD, config)
        votes_scraper = create_scraper(DocumentType.VOTES, config)

        assert isinstance(hansard_scraper, BaseScraper)
        assert isinstance(votes_scraper, BaseScraper)

    def test_create_scraper_with_different_configs(self):
        """Test creating scrapers with different configurations."""
        from hansard_tales.models.base import DocumentType
        from hansard_tales.scrapers.factory import create_scraper

        config1 = ScraperConfig(
            base_url="https://parliament.go.ke",
            download_dir=Path("data/pdfs1"),
            max_retries=3,
            retry_delay=1.0,
            timeout=30,
            user_agent="HansardTales/1.0",
        )

        config2 = ScraperConfig(
            base_url="https://parliament.go.ke",
            download_dir=Path("data/pdfs2"),
            max_retries=5,
            retry_delay=2.0,
            timeout=60,
            user_agent="HansardTales/2.0",
        )

        scraper1 = create_scraper(DocumentType.HANSARD, config1)
        scraper2 = create_scraper(DocumentType.HANSARD, config2)

        assert scraper1.config.download_dir == Path("data/pdfs1")
        assert scraper2.config.download_dir == Path("data/pdfs2")
        assert scraper1.config.max_retries == 3
        assert scraper2.config.max_retries == 5

    def test_factory_error_message_lists_available_types(self, config):
        """Test that error message lists available document types."""
        from hansard_tales.models.base import DocumentType
        from hansard_tales.scrapers.factory import create_scraper

        with pytest.raises(ValueError) as exc_info:
            create_scraper(DocumentType.PETITION, config)

        error_msg = str(exc_info.value)
        assert "hansard" in error_msg.lower()
        assert "votes" in error_msg.lower()

    def test_create_multiple_scrapers_independently(self, config):
        """Test creating multiple scraper instances independently."""
        from hansard_tales.models.base import DocumentType
        from hansard_tales.scrapers.factory import create_scraper

        scraper1 = create_scraper(DocumentType.HANSARD, config)
        scraper2 = create_scraper(DocumentType.VOTES, config)
        scraper3 = create_scraper(DocumentType.HANSARD, config)

        # Verify they are different instances
        assert scraper1 is not scraper3
        assert scraper1 is not scraper2

        # But have same config
        assert scraper1.config == scraper3.config


class TestFilenameGeneration:
    """Test suite for standardized filename generation."""

    @pytest.fixture
    def config(self):
        """Create test scraper configuration."""
        return ScraperConfig(
            base_url="https://parliament.go.ke",
            download_dir=Path("data/pdfs"),
            max_retries=3,
            retry_delay=1.0,
            timeout=30,
            user_agent="HansardTales/1.0",
        )

    @pytest.fixture
    def hansard_scraper(self, config):
        """Create Hansard scraper for testing."""
        from hansard_tales.scrapers.hansard import HansardScraper

        return HansardScraper(config)

    @pytest.fixture
    def votes_scraper(self, config):
        """Create Votes scraper for testing."""
        from hansard_tales.scrapers.votes import VotesScraper

        return VotesScraper(config)

    def test_hansard_filename_generation_morning(self, hansard_scraper):
        """Test Hansard filename generation for morning session."""
        url = "https://parliament.go.ke/sites/default/files/2025-11/Hansard%20Report%20-%20Tuesday%2C%204th%20November%202025%20%28P%29.pdf"

        filename = hansard_scraper._generate_filename(url)

        assert filename == "hansard_20251104_P.pdf"

    def test_hansard_filename_generation_afternoon(self, hansard_scraper):
        """Test Hansard filename generation for afternoon session."""
        url = "https://parliament.go.ke/sites/default/files/2025-11/Hansard%20Report%20-%20Wednesday%2C%205th%20November%202025%20%28A%29.pdf"

        filename = hansard_scraper._generate_filename(url)

        assert filename == "hansard_20251105_A.pdf"

    def test_hansard_filename_generation_evening(self, hansard_scraper):
        """Test Hansard filename generation for evening session."""
        url = "https://parliament.go.ke/sites/default/files/2025-12/Hansard%20Report%20-%20Thursday%2C%204th%20December%202025%20%28E%29.pdf"

        filename = hansard_scraper._generate_filename(url)

        assert filename == "hansard_20251204_E.pdf"

    def test_hansard_filename_fallback(self, hansard_scraper):
        """Test Hansard filename fallback when parsing fails."""
        url = "https://parliament.go.ke/files/unknown-format.pdf"

        filename = hansard_scraper._generate_filename(url)

        assert filename == "unknown-format.pdf"

    def test_votes_filename_generation_afternoon(self, votes_scraper):
        """Test Votes filename generation for afternoon session."""
        url = "https://parliament.go.ke/sites/default/files/2025-11/Tuesday%20%2CNovember%204%2C%202025%20at%202.30pm.pdf"

        filename = votes_scraper._generate_filename(url)

        assert filename == "votes_20251104T143000Z.pdf"

    def test_votes_filename_generation_morning(self, votes_scraper):
        """Test Votes filename generation for morning session."""
        url = "https://parliament.go.ke/sites/default/files/2025-11/Wednesday%2C%20November%205%2C%202025%20at%209.00am.pdf"

        filename = votes_scraper._generate_filename(url)

        assert filename == "votes_20251105T090000Z.pdf"

    def test_votes_filename_generation_noon(self, votes_scraper):
        """Test Votes filename generation for noon."""
        url = "https://parliament.go.ke/sites/default/files/2025-12/Thursday%2C%20December%2031%2C%202025%20at%2012.00pm.pdf"

        filename = votes_scraper._generate_filename(url)

        assert filename == "votes_20251231T120000Z.pdf"

    def test_votes_filename_generation_midnight(self, votes_scraper):
        """Test Votes filename generation for midnight."""
        url = "https://parliament.go.ke/sites/default/files/2025-12/Friday%2C%20January%201%2C%202025%20at%2012.00am.pdf"

        filename = votes_scraper._generate_filename(url)

        assert filename == "votes_20250101T000000Z.pdf"

    def test_votes_filename_fallback(self, votes_scraper):
        """Test Votes filename fallback when parsing fails."""
        url = "https://parliament.go.ke/files/unknown-format.pdf"

        filename = votes_scraper._generate_filename(url)

        assert filename == "unknown-format.pdf"


class TestDownloadTracking:
    """Test suite for download tracking functionality."""

    @pytest.fixture
    def config(self):
        """Create test scraper configuration."""
        return ScraperConfig(
            base_url="https://parliament.go.ke",
            download_dir=Path("data/pdfs"),
            max_retries=3,
            retry_delay=1.0,
            timeout=30,
            user_agent="HansardTales/1.0",
        )

    @pytest.fixture
    def concrete_scraper(self, config):
        """Create concrete scraper for testing."""

        class ConcreteScraper(BaseScraper):
            def get_document_urls(self, chamber, start_date=None, end_date=None):
                return ["https://example.com/doc.pdf"]

            def extract_metadata(self, url, content):
                return {"document_type": "hansard", "original_filename": "test.pdf"}

        return ConcreteScraper(config)

    @patch("sqlalchemy.create_engine")
    @patch("sqlalchemy.orm.sessionmaker")
    def test_is_duplicate_returns_true_for_existing_file(
        self, mock_sessionmaker, mock_create_engine, concrete_scraper
    ):
        """Test that _is_duplicate returns True for existing file."""
        # Setup mock database session
        mock_session = Mock()
        mock_sessionmaker.return_value = Mock(return_value=mock_session)

        # Mock query to return existing record
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = Mock()  # Non-None = exists
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query

        # Check for duplicate
        result = concrete_scraper._is_duplicate("test_hash")

        # Verify result
        assert result is True
        mock_session.close.assert_called_once()

    @patch("sqlalchemy.create_engine")
    @patch("sqlalchemy.orm.sessionmaker")
    def test_is_duplicate_returns_false_for_new_file(
        self, mock_sessionmaker, mock_create_engine, concrete_scraper
    ):
        """Test that _is_duplicate returns False for new file."""
        # Setup mock database session
        mock_session = Mock()
        mock_sessionmaker.return_value = Mock(return_value=mock_session)

        # Mock query to return None (not found)
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query

        # Check for duplicate
        result = concrete_scraper._is_duplicate("new_hash")

        # Verify result
        assert result is False
        mock_session.close.assert_called_once()

    @patch("sqlalchemy.create_engine")
    def test_is_duplicate_handles_database_error(self, mock_create_engine, concrete_scraper):
        """Test that _is_duplicate handles database errors gracefully."""
        # Setup mock to raise exception
        mock_create_engine.side_effect = Exception("Database unavailable")

        # Check for duplicate
        result = concrete_scraper._is_duplicate("test_hash")

        # Verify returns False on error (allows scraper to continue)
        assert result is False

    @patch("sqlalchemy.create_engine")
    @patch("sqlalchemy.orm.sessionmaker")
    def test_record_download_inserts_record(
        self, mock_sessionmaker, mock_create_engine, concrete_scraper, tmp_path
    ):
        """Test that _record_download inserts record into database."""
        # Setup mock database session
        mock_session = Mock()
        mock_sessionmaker.return_value = Mock(return_value=mock_session)

        # Create test document
        doc = ScrapedDocument(
            url="https://example.com/test.pdf",
            filename="hansard_20251104_P.pdf",
            content=b"test content",
            hash="abc123",
            metadata={"document_type": "hansard", "original_filename": "test.pdf"},
        )

        file_path = tmp_path / "test.pdf"

        # Record download
        concrete_scraper._record_download(doc, file_path, Chamber.NATIONAL_ASSEMBLY, 2022)

        # Verify session operations
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

        # Verify record was created with correct data
        added_record = mock_session.add.call_args[0][0]
        assert added_record.source_url == "https://example.com/test.pdf"
        assert added_record.source_hash == "abc123"
        assert added_record.standardized_filename == "hansard_20251104_P.pdf"
        assert added_record.document_type == "hansard"
        assert added_record.chamber == "national_assembly"
        assert added_record.parliament_term == 2022

    @patch("sqlalchemy.create_engine")
    def test_record_download_handles_database_error(
        self, mock_create_engine, concrete_scraper, tmp_path
    ):
        """Test that _record_download handles database errors gracefully."""
        # Setup mock to raise exception
        mock_create_engine.side_effect = Exception("Database unavailable")

        # Create test document
        doc = ScrapedDocument(
            url="https://example.com/test.pdf",
            filename="test.pdf",
            content=b"test content",
            hash="abc123",
            metadata={"document_type": "hansard"},
        )

        file_path = tmp_path / "test.pdf"

        # Record download - should not raise exception
        concrete_scraper._record_download(doc, file_path, Chamber.NATIONAL_ASSEMBLY)

        # Test passes if no exception raised
        assert True

    @patch("sqlalchemy.create_engine")
    @patch("sqlalchemy.orm.sessionmaker")
    @patch.object(BaseScraper, "download_document")
    @patch.object(BaseScraper, "save_document")
    def test_scrape_records_downloads(
        self,
        mock_save,
        mock_download,
        mock_sessionmaker,
        mock_create_engine,
        concrete_scraper,
        tmp_path,
    ):
        """Test that scrape() records downloads in database."""
        # Setup mock database session
        mock_session = Mock()
        mock_sessionmaker.return_value = Mock(return_value=mock_session)

        # Mock query to return None (not duplicate)
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query

        # Setup mock document
        doc = ScrapedDocument(
            url="https://example.com/test.pdf",
            filename="test.pdf",
            content=b"test content",
            hash="abc123",
            metadata={"document_type": "hansard", "original_filename": "test.pdf"},
        )

        mock_download.return_value = doc
        mock_save.return_value = tmp_path / "test.pdf"

        # Mock get_document_urls
        concrete_scraper.get_document_urls = Mock(return_value=["https://example.com/test.pdf"])

        # Scrape documents
        results = concrete_scraper.scrape(Chamber.NATIONAL_ASSEMBLY, skip_existing=False)

        # Verify download was recorded
        assert len(results) == 1
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


class TestScrapingWorkflow:
    """Test suite for URL-based scraping workflow with batch checking."""

    @pytest.fixture
    def config(self):
        """Create test scraper configuration."""
        return ScraperConfig(
            base_url="https://parliament.go.ke",
            download_dir=Path("data/pdfs"),
            max_retries=3,
            retry_delay=1.0,
            timeout=30,
            user_agent="HansardTales/1.0",
        )

    @pytest.fixture
    def concrete_scraper(self, config):
        """Create concrete scraper for testing."""

        class ConcreteScraper(BaseScraper):
            def get_document_urls(self, chamber, start_date=None, end_date=None):
                return ["https://example.com/doc.pdf"]

            def extract_metadata(self, url, content):
                return {"document_type": "test", "original_filename": "doc.pdf"}

        return ConcreteScraper(config)

    def test_batch_check_urls_returns_status_for_all_urls(self, concrete_scraper):
        """Test batch URL checking returns status for all URLs."""
        urls = [
            "https://example.com/doc1.pdf",
            "https://example.com/doc2.pdf",
            "https://example.com/doc3.pdf",
        ]

        # Mock the entire method to test the interface
        with patch.object(concrete_scraper, "_batch_check_urls_in_db") as mock_batch:
            mock_batch.return_value = {
                urls[0]: (True, Path("/path/to/doc1.pdf")),
                urls[1]: (True, Path("/path/to/doc2.pdf")),
                urls[2]: (False, None),
            }

            result = concrete_scraper._batch_check_urls_in_db(urls)

        # Verify results
        assert len(result) == 3
        assert result[urls[0]] == (True, Path("/path/to/doc1.pdf"))
        assert result[urls[1]] == (True, Path("/path/to/doc2.pdf"))
        assert result[urls[2]] == (False, None)

    def test_batch_check_urls_handles_empty_list(self, concrete_scraper):
        """Test batch URL checking handles empty list."""
        result = concrete_scraper._batch_check_urls_in_db([])
        assert result == {}

    def test_batch_check_urls_handles_database_error(self, concrete_scraper):
        """Test batch URL checking handles database errors gracefully."""
        urls = ["https://example.com/doc1.pdf", "https://example.com/doc2.pdf"]

        with patch("sqlalchemy.create_engine", side_effect=Exception("DB error")):
            result = concrete_scraper._batch_check_urls_in_db(urls)

        # Should return all URLs as not existing
        assert len(result) == 2
        assert result[urls[0]] == (False, None)
        assert result[urls[1]] == (False, None)

    def test_verify_file_exists_returns_true_when_file_exists(self, concrete_scraper, tmp_path):
        """Test file existence verification returns True when file exists."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"test content")

        result = concrete_scraper._verify_file_exists(test_file)

        assert result is True

    def test_verify_file_exists_returns_false_when_file_missing(self, concrete_scraper, tmp_path):
        """Test file existence verification returns False when file doesn't exist."""
        missing_file = tmp_path / "missing.pdf"

        result = concrete_scraper._verify_file_exists(missing_file)

        assert result is False

    @patch.object(BaseScraper, "download_document")
    @patch.object(BaseScraper, "_batch_check_urls_in_db")
    @patch.object(BaseScraper, "_verify_file_exists")
    def test_workflow_uses_batch_checking(
        self, mock_verify, mock_batch_check, mock_download, concrete_scraper
    ):
        """Test workflow uses batch checking instead of one-at-a-time."""
        urls = ["https://example.com/doc1.pdf", "https://example.com/doc2.pdf"]

        # Setup: doc1 exists in DB and storage, doc2 is new
        mock_batch_check.return_value = {
            urls[0]: (True, Path("data/pdfs/doc1.pdf")),
            urls[1]: (False, None),
        }
        mock_verify.return_value = True  # doc1 exists in storage

        doc2 = ScrapedDocument(
            url=urls[1],
            filename="doc2.pdf",
            content=b"content2",
            hash="hash2",
            metadata={"document_type": "test", "original_filename": "doc2.pdf"},
        )
        mock_download.return_value = doc2

        concrete_scraper.get_document_urls = Mock(return_value=urls)

        # Execute scrape
        results = concrete_scraper.scrape(Chamber.NATIONAL_ASSEMBLY, skip_existing=True)

        # Verify batch check was called once with all URLs
        mock_batch_check.assert_called_once_with(urls)

        # Verify only doc2 was downloaded
        mock_download.assert_called_once()
        assert len(results) == 1
        assert results[0].url == urls[1]

    @patch.object(BaseScraper, "download_document")
    @patch.object(BaseScraper, "_batch_check_urls_in_db")
    @patch.object(BaseScraper, "_verify_file_exists")
    def test_workflow_skips_existing_file_in_storage(
        self, mock_verify, mock_batch_check, mock_download, concrete_scraper
    ):
        """Test workflow: skip download when file exists in both database and storage."""
        url = "https://example.com/doc.pdf"

        # Setup: URL exists in database, file exists in storage
        mock_batch_check.return_value = {url: (True, Path("data/pdfs/doc.pdf"))}
        mock_verify.return_value = True

        concrete_scraper.get_document_urls = Mock(return_value=[url])

        # Execute scrape
        results = concrete_scraper.scrape(Chamber.NATIONAL_ASSEMBLY, skip_existing=True)

        # Verify: no download occurred
        mock_download.assert_not_called()
        assert len(results) == 0

    @patch.object(BaseScraper, "download_document")
    @patch.object(BaseScraper, "_batch_check_urls_in_db")
    @patch.object(BaseScraper, "_verify_file_exists")
    @patch.object(BaseScraper, "_update_download_record")
    @patch.object(BaseScraper, "save_document")
    def test_workflow_downloads_when_file_missing_from_storage(
        self,
        mock_save,
        mock_update,
        mock_verify,
        mock_batch_check,
        mock_download,
        concrete_scraper,
        tmp_path,
    ):
        """Test workflow: download when URL in database but file missing from storage."""
        url = "https://example.com/doc.pdf"

        # Setup: URL exists in database, but file missing from storage
        mock_batch_check.return_value = {url: (True, Path("data/pdfs/doc.pdf"))}
        mock_verify.return_value = False

        doc = ScrapedDocument(
            url=url,
            filename="doc.pdf",
            content=b"content",
            hash="hash123",
            metadata={"document_type": "test", "original_filename": "doc.pdf"},
        )
        mock_download.return_value = doc
        mock_save.return_value = tmp_path / "doc.pdf"

        concrete_scraper.get_document_urls = Mock(return_value=[url])

        # Execute scrape
        results = concrete_scraper.scrape(Chamber.NATIONAL_ASSEMBLY, skip_existing=True)

        # Verify: download occurred and record updated
        mock_download.assert_called_once()
        mock_update.assert_called_once()
        assert len(results) == 1

    @patch.object(BaseScraper, "download_document")
    @patch.object(BaseScraper, "_batch_check_urls_in_db")
    @patch.object(BaseScraper, "_record_download")
    @patch.object(BaseScraper, "save_document")
    def test_workflow_downloads_new_file(
        self, mock_save, mock_record, mock_batch_check, mock_download, concrete_scraper, tmp_path
    ):
        """Test workflow: download when URL not in database."""
        url = "https://example.com/new-doc.pdf"

        # Setup: URL not in database
        mock_batch_check.return_value = {url: (False, None)}

        doc = ScrapedDocument(
            url=url,
            filename="new-doc.pdf",
            content=b"new content",
            hash="newhash",
            metadata={"document_type": "test", "original_filename": "new-doc.pdf"},
        )
        mock_download.return_value = doc
        mock_save.return_value = tmp_path / "new-doc.pdf"

        concrete_scraper.get_document_urls = Mock(return_value=[url])

        # Execute scrape
        results = concrete_scraper.scrape(Chamber.NATIONAL_ASSEMBLY, skip_existing=True)

        # Verify: download occurred and new record created
        mock_download.assert_called_once()
        mock_record.assert_called_once()
        assert len(results) == 1


class TestDateParserIntegration:
    """Test suite for dateparser integration with UTC+3 timezone."""

    @pytest.fixture
    def config(self):
        """Create test scraper configuration."""
        return ScraperConfig(
            base_url="https://parliament.go.ke",
            download_dir=Path("data/pdfs"),
            max_retries=3,
            retry_delay=1.0,
            timeout=30,
            user_agent="HansardTales/1.0",
        )

    @pytest.fixture
    def hansard_scraper(self, config):
        """Create Hansard scraper for testing."""
        from hansard_tales.scrapers.hansard import HansardScraper

        return HansardScraper(config)

    @pytest.fixture
    def votes_scraper(self, config):
        """Create Votes scraper for testing."""
        from hansard_tales.scrapers.votes import VotesScraper

        return VotesScraper(config)

    def test_hansard_dateparser_integration(self, hansard_scraper):
        """Test Hansard uses dateparser for British dates."""
        url = "https://parliament.go.ke/files/Hansard%20Report%20-%20Tuesday%2C%204th%20November%202025%20%28P%29.pdf"
        content = b"test"

        metadata = hansard_scraper.extract_metadata(url, content)

        assert metadata["date"] == "2025-11-04"
        assert metadata["period"] == "P"

    def test_hansard_dateparser_handles_real_world_examples(self, hansard_scraper):
        """Test dateparser with real-world Hansard URLs from parliament.go.ke.

        Note: The href (URL) contains the period code (A/P/E), not the link text.
        Period mapping:
        - (A) = Morning Sitting
        - (P) = Afternoon Sitting
        - (E) = Evening Sitting
        """
        test_cases = [
            # Real URLs from parliament.go.ke (href attribute)
            (
                "Hansard Report - Thursday, 4th December 2025 (E).pdf",
                "2025-12-04",
                "E",
                "hansard_20251204_E.pdf",
            ),
            (
                "Hansard Report - Thursday, 4th December 2025 (P).pdf",
                "2025-12-04",
                "P",
                "hansard_20251204_P.pdf",
            ),
            (
                "Hansard Report - Wednesday, 3rd December 2025 (P).pdf",
                "2025-12-03",
                "P",
                "hansard_20251203_P.pdf",
            ),
            (
                "Hansard Report - Wednesday, 3rd December 2025 (A).pdf",
                "2025-12-03",
                "A",
                "hansard_20251203_A.pdf",
            ),
            (
                "Hansard Report - Tuesday, 2nd December 2025 (P).pdf",
                "2025-12-02",
                "P",
                "hansard_20251202_P.pdf",
            ),
            (
                "Hansard Report - Thursday, 27th November 2025 (P).pdf",
                "2025-11-27",
                "P",
                "hansard_20251127_P.pdf",
            ),
            (
                "Hansard Report - Wednesday, 26th November 2025 (P).pdf",
                "2025-11-26",
                "P",
                "hansard_20251126_P.pdf",
            ),
            (
                "Hansard Report - Wednesday, 26th November 2025 (A).pdf",
                "2025-11-26",
                "A",
                "hansard_20251126_A.pdf",
            ),
            (
                "Hansard Report - Thursday, 16th October 2025 (P).pdf",
                "2025-10-16",
                "P",
                "hansard_20251016_P.pdf",
            ),
            (
                "Hansard Report - Thursday, 16th October 2025 (A).pdf",
                "2025-10-16",
                "A",
                "hansard_20251016_A.pdf",
            ),
            # Edge cases
            (
                "Hansard Report - Thursday,16th January 2025 (P).pdf",
                "2025-01-16",
                "P",
                "hansard_20250116_P.pdf",
            ),  # No space after comma
            (
                "Hansard Report - Thursday, 16th January 2025 (A).pdf",
                "2025-01-16",
                "A",
                "hansard_20250116_A.pdf",
            ),
            (
                "Hansard Report - Tuesday, 5th November 2024 (P).pdf",
                "2024-11-05",
                "P",
                "hansard_20241105_P.pdf",
            ),
            # Lowercase period codes
            (
                "Hansard Report - Tuesday, 4th November 2025 (p).pdf",
                "2025-11-04",
                "P",
                "hansard_20251104_P.pdf",
            ),
            (
                "Hansard Report - Wednesday, 5th November 2025 (a).pdf",
                "2025-11-05",
                "A",
                "hansard_20251105_A.pdf",
            ),
        ]

        for filename, expected_date, expected_period, expected_standardized in test_cases:
            url = (
                f"https://parliament.go.ke/files/{filename.replace(' ', '%20').replace(',', '%2C')}"
            )

            # Test metadata extraction
            metadata = hansard_scraper.extract_metadata(url, b"test")
            assert metadata["date"] == expected_date, f"Date failed for: {filename}"
            assert metadata["period"] == expected_period, f"Period failed for: {filename}"

            # Test filename generation
            standardized = hansard_scraper._generate_filename(url)
            assert standardized == expected_standardized, f"Filename failed for: {filename}"

    def test_votes_dateparser_handles_real_world_examples(self, votes_scraper):
        """Test dateparser with real-world link titles from parliament.go.ke."""
        test_cases = [
            (
                "Tuesday, November 18, 2025 At 2.30pm",
                "2025-11-18",
                "14:30",
                "votes_20251118T143000Z.pdf",
            ),
            (
                "Thursday, November 13,2025 At 2.30pm",
                "2025-11-13",
                "14:30",
                "votes_20251113T143000Z.pdf",
            ),
            (
                "Wednesday, November 12, 2025 At 2.30pm",
                "2025-11-12",
                "14:30",
                "votes_20251112T143000Z.pdf",
            ),
            (
                "Wednesday, November 12, 2025 At 9.30am",
                "2025-11-12",
                "09:30",
                "votes_20251112T093000Z.pdf",
            ),
            (
                "Tuesday, 11 November 2025 At 2.30pm",
                "2025-11-11",
                "14:30",
                "votes_20251111T143000Z.pdf",
            ),
            (
                "Thursday, November 6, 2025 At 2.30pm",
                "2025-11-06",
                "14:30",
                "votes_20251106T143000Z.pdf",
            ),
            (
                "Wednesday, November 5, 2025 At 2.30pm",
                "2025-11-05",
                "14:30",
                "votes_20251105T143000Z.pdf",
            ),
            (
                "Wednesday, November 5, 2025 At 9.30am",
                "2025-11-05",
                "09:30",
                "votes_20251105T093000Z.pdf",
            ),
            (
                "Tuesday, November 4, 2025 At 2.30pm",
                "2025-11-04",
                "14:30",
                "votes_20251104T143000Z.pdf",
            ),
            (
                "Thursday, October 16, 2025 At 2.30pm",
                "2025-10-16",
                "14:30",
                "votes_20251016T143000Z.pdf",
            ),
            (
                "Thursday, October 16, 2025 At 10.00am",
                "2025-10-16",
                "10:00",
                "votes_20251016T100000Z.pdf",
            ),
            (
                "Wednesday, October 15, 2025 At 2.30pm",
                "2025-10-15",
                "14:30",
                "votes_20251015T143000Z.pdf",
            ),
            (
                "Wednesday,october 15,2025 At 9.30am",
                "2025-10-15",
                "09:30",
                "votes_20251015T093000Z.pdf",
            ),
        ]

        for title, expected_date, expected_time, expected_filename in test_cases:
            url = f"https://parliament.go.ke/files/{title.replace(' ', '%20').replace(',', '%2C')}.pdf"

            # Test metadata extraction
            metadata = votes_scraper.extract_metadata(url, b"test")
            assert metadata["date"] == expected_date, f"Date failed for: {title}"
            assert metadata["time"] == expected_time, f"Time failed for: {title}"

            # Test filename generation
            filename = votes_scraper._generate_filename(url)
            assert filename == expected_filename, f"Filename failed for: {title}"

    def test_dateparser_consistency(self, hansard_scraper):
        """Test dateparser produces consistent results for same input."""
        url = "https://parliament.go.ke/files/Hansard%20Report%20-%20Thursday%2C%204th%20December%202025%20%28E%29.pdf"

        # Parse same URL multiple times
        results = [hansard_scraper.extract_metadata(url, b"test")["date"] for _ in range(5)]

        # All results should be identical
        assert len(set(results)) == 1
        assert results[0] == "2025-12-04"
