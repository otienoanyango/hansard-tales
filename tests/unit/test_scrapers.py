"""
Unit tests for web scrapers.

Tests cover base scraper functionality including downloading,
retry logic, duplicate detection, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import date
import hashlib
import requests

from hansard_tales.scrapers.base import (
    BaseScraper,
    ScrapedDocument,
    DataCollectionError
)
from hansard_tales.config.settings import ScraperConfig
from hansard_tales.models.base import Chamber


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
            user_agent="HansardTales/1.0"
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
        assert scraper.session.headers['User-Agent'] == "HansardTales/1.0"
    
    @patch('requests.Session.get')
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
    
    @patch('requests.Session.get')
    def test_download_document_retry_logic(self, mock_get, concrete_scraper):
        """Test retry logic on transient failures."""
        # Setup mock to fail twice then succeed
        mock_response = Mock()
        mock_response.content = b"test content"
        mock_response.raise_for_status = Mock()
        
        mock_get.side_effect = [
            requests.RequestException("Network error"),
            requests.RequestException("Network error"),
            mock_response
        ]
        
        # Download document
        url = "https://example.com/test.pdf"
        result = concrete_scraper.download_document(url)
        
        # Verify result
        assert isinstance(result, ScrapedDocument)
        assert result.content == b"test content"
        
        # Verify retries
        assert mock_get.call_count == 3
    
    @patch('requests.Session.get')
    def test_download_document_max_retries_exceeded(self, mock_get, concrete_scraper):
        """Test failure after max retries exceeded."""
        # Setup mock to always fail
        mock_get.side_effect = requests.RequestException("Network error")
        
        # Attempt download
        url = "https://example.com/test.pdf"
        with pytest.raises(requests.RequestException):
            concrete_scraper.download_document(url)
        
        # Verify max retries attempted
        assert mock_get.call_count == 3
    
    def test_save_document(self, concrete_scraper, tmp_path):
        """Test saving document to disk."""
        # Create test document
        doc = ScrapedDocument(
            url="https://example.com/test.pdf",
            filename="test.pdf",
            content=b"test content",
            hash="abc123",
            metadata={}
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
    
    @patch.object(BaseScraper, 'download_document')
    @patch.object(BaseScraper, '_is_duplicate')
    def test_scrape_success(self, mock_is_duplicate, mock_download, concrete_scraper):
        """Test successful scraping of multiple documents."""
        # Setup mocks
        mock_is_duplicate.return_value = False
        
        doc1 = ScrapedDocument(
            url="https://example.com/doc1.pdf",
            filename="doc1.pdf",
            content=b"content1",
            hash="hash1",
            metadata={}
        )
        doc2 = ScrapedDocument(
            url="https://example.com/doc2.pdf",
            filename="doc2.pdf",
            content=b"content2",
            hash="hash2",
            metadata={}
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
    
    @patch.object(BaseScraper, 'download_document')
    @patch.object(BaseScraper, '_is_duplicate')
    def test_scrape_skip_duplicates(self, mock_is_duplicate, mock_download, concrete_scraper):
        """Test skipping duplicate documents."""
        # Setup mocks
        mock_is_duplicate.side_effect = [False, True]  # Second doc is duplicate
        
        doc1 = ScrapedDocument(
            url="https://example.com/doc1.pdf",
            filename="doc1.pdf",
            content=b"content1",
            hash="hash1",
            metadata={}
        )
        doc2 = ScrapedDocument(
            url="https://example.com/doc2.pdf",
            filename="doc2.pdf",
            content=b"content2",
            hash="hash2",
            metadata={}
        )
        
        mock_download.side_effect = [doc1, doc2]
        
        # Mock get_document_urls
        concrete_scraper.get_document_urls = Mock(
            return_value=["https://example.com/doc1.pdf", "https://example.com/doc2.pdf"]
        )
        
        # Scrape documents
        results = concrete_scraper.scrape(Chamber.NATIONAL_ASSEMBLY, skip_existing=True)
        
        # Verify only non-duplicate returned
        assert len(results) == 1
        assert results[0] == doc1
    
    @patch.object(BaseScraper, 'download_document')
    def test_scrape_continues_on_error(self, mock_download, concrete_scraper):
        """Test that scraping continues when individual document fails."""
        # Setup mocks - first fails, second succeeds
        doc2 = ScrapedDocument(
            url="https://example.com/doc2.pdf",
            filename="doc2.pdf",
            content=b"content2",
            hash="hash2",
            metadata={}
        )
        
        mock_download.side_effect = [
            Exception("Download failed"),
            doc2
        ]
        
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
        concrete_scraper.scrape(
            Chamber.NATIONAL_ASSEMBLY,
            start_date=start,
            end_date=end
        )
        
        # Verify date parameters were passed
        concrete_scraper.get_document_urls.assert_called_once_with(
            Chamber.NATIONAL_ASSEMBLY,
            start,
            end
        )
    
    @patch('requests.Session.get')
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
    
    @patch('requests.Session.get')
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
    
    @patch('requests.Session.get')
    @patch('time.sleep')
    def test_retry_exponential_backoff(self, mock_sleep, mock_get, concrete_scraper):
        """Test exponential backoff delay between retries."""
        # Setup mock to fail twice then succeed
        mock_response = Mock()
        mock_response.content = b"test content"
        mock_response.raise_for_status = Mock()
        
        mock_get.side_effect = [
            requests.RequestException("Network error"),
            requests.RequestException("Network error"),
            mock_response
        ]
        
        # Download document
        url = "https://example.com/test.pdf"
        concrete_scraper.download_document(url)
        
        # Verify exponential backoff: 1.0 * 2^0 = 1.0, 1.0 * 2^1 = 2.0
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1.0)  # First retry
        mock_sleep.assert_any_call(2.0)  # Second retry
    
    def test_save_document_creates_directory(self, concrete_scraper, tmp_path):
        """Test that save_document creates output directory if it doesn't exist."""
        # Create test document
        doc = ScrapedDocument(
            url="https://example.com/test.pdf",
            filename="test.pdf",
            content=b"test content",
            hash="abc123",
            metadata={}
        )
        
        # Use non-existent subdirectory
        output_dir = tmp_path / "subdir" / "nested"
        
        # Save document
        output_path = concrete_scraper.save_document(doc, output_dir)
        
        # Verify directory was created
        assert output_dir.exists()
        assert output_path.exists()
    
    @patch.object(BaseScraper, 'download_document')
    def test_scrape_empty_url_list(self, mock_download, concrete_scraper):
        """Test scraping with no URLs returns empty list."""
        # Mock get_document_urls to return empty list
        concrete_scraper.get_document_urls = Mock(return_value=[])
        
        # Scrape documents
        results = concrete_scraper.scrape(Chamber.NATIONAL_ASSEMBLY)
        
        # Verify empty results
        assert len(results) == 0
        mock_download.assert_not_called()
    
    @patch.object(BaseScraper, 'download_document')
    @patch.object(BaseScraper, '_is_duplicate')
    def test_scrape_skip_existing_false(self, mock_is_duplicate, mock_download, concrete_scraper):
        """Test that skip_existing=False includes all documents."""
        # Setup mocks
        mock_is_duplicate.return_value = True  # All are duplicates
        
        doc1 = ScrapedDocument(
            url="https://example.com/doc1.pdf",
            filename="doc1.pdf",
            content=b"content1",
            hash="hash1",
            metadata={}
        )
        
        mock_download.return_value = doc1
        
        # Mock get_document_urls
        concrete_scraper.get_document_urls = Mock(
            return_value=["https://example.com/doc1.pdf"]
        )
        
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
    
    @patch('requests.Session.get')
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
        assert call_kwargs['timeout'] == 30


class TestScrapedDocument:
    """Test suite for ScrapedDocument dataclass."""
    
    def test_creation(self):
        """Test creating ScrapedDocument."""
        doc = ScrapedDocument(
            url="https://example.com/test.pdf",
            filename="test.pdf",
            content=b"test content",
            hash="abc123",
            metadata={"key": "value"}
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
            user_agent="HansardTales/1.0"
        )
    
    @pytest.fixture
    def hansard_scraper(self, config):
        """Create Hansard scraper for testing."""
        from hansard_tales.scrapers.hansard import HansardScraper
        return HansardScraper(config)
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
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
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
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
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Get document URLs
        urls = hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
        
        # Verify absolute URL is preserved
        assert len(urls) == 1
        assert urls[0] == "https://parliament.go.ke/files/hansard-2024-01-15.pdf"
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Get document URLs
        urls = hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
        
        # Verify only PDF link is included (CSS selector filters by href$=".pdf")
        assert len(urls) == 1
        assert urls[0].endswith('.pdf')
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Get document URLs
        urls = hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
        
        # Verify link is included
        assert len(urls) == 1
        assert 'hansard' in urls[0].lower()
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Get document URLs - should raise error since CSS selector won't match
        with pytest.raises(DataCollectionError):
            hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Attempt to get document URLs
        with pytest.raises(DataCollectionError) as exc_info:
            hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY)
        
        # Verify error message
        error_msg = str(exc_info.value)
        assert "No Hansard documents found" in error_msg
        assert "website structure has changed" in error_msg
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
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
        
        assert metadata['document_type'] == 'hansard'
        assert metadata['original_filename'] == 'Hansard Report - Tuesday, 4th November 2025 (P).pdf'
        assert metadata['date'] == '2025-11-04'
        assert metadata['period'] == 'P'
    
    def test_extract_metadata_with_date_no_dashes(self, hansard_scraper):
        """Test metadata extraction with different date format."""
        url = "https://parliament.go.ke/sites/default/files/2025-11/Hansard%20Report%20-%20Wednesday%2C%205th%20November%202025%20%28A%29.pdf"
        content = b"test content"
        
        metadata = hansard_scraper.extract_metadata(url, content)
        
        assert metadata['document_type'] == 'hansard'
        assert metadata['date'] == '2025-11-05'
        assert metadata['period'] == 'A'
    
    def test_extract_metadata_without_date(self, hansard_scraper):
        """Test metadata extraction when date parsing fails."""
        url = "https://parliament.go.ke/files/hansard-document.pdf"
        content = b"test content"
        
        metadata = hansard_scraper.extract_metadata(url, content)
        
        assert metadata['document_type'] == 'hansard'
        assert metadata['original_filename'] == 'hansard-document.pdf'
        assert 'date' not in metadata
    
    def test_extract_metadata_complex_filename(self, hansard_scraper):
        """Test metadata extraction with evening session."""
        url = "https://parliament.go.ke/sites/default/files/2025-12/Hansard%20Report%20-%20Thursday%2C%204th%20December%202025%20%28E%29.pdf"
        content = b"test content"
        
        metadata = hansard_scraper.extract_metadata(url, content)
        
        assert metadata['document_type'] == 'hansard'
        assert metadata['date'] == '2025-12-04'
        assert metadata['period'] == 'E'
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Get document URLs
        urls = hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
        
        # Verify URL doesn't have double slashes
        assert len(urls) == 1
        assert urls[0] == "https://parliament.go.ke/files/hansard-2024-01-15.pdf"
        assert "//" not in urls[0].replace("https://", "")
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Get document URLs
        urls = hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
        
        # Verify URLs from both tables
        assert len(urls) == 2
        assert any('hansard-2024-01-15.pdf' in url for url in urls)
        assert any('hansard-2024-01-16.pdf' in url for url in urls)
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Get document URLs
        urls = hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
        
        # Verify all variations are found
        assert len(urls) == 3
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Get document URLs
        urls = hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY)
        
        # Verify URLs were extracted from cols-2 table
        assert len(urls) == 2
        assert all('Hansard' in url for url in urls)
        assert all('.pdf' in url for url in urls)
    
    def test_get_document_urls_invalid_chamber(self, hansard_scraper):
        """Test that invalid chamber raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            hansard_scraper.get_document_urls("invalid_chamber")
        
        assert "Unknown chamber" in str(exc_info.value)
    
    @patch('requests.Session.get')
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
        mock_page_response.content = html_content.encode('utf-8')
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
        assert documents[0].metadata['document_type'] == 'hansard'
    
    @patch('requests.Session.get')
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
            mock_response.content = html.encode('utf-8')
            mock_response.raise_for_status = Mock()
            mock_responses.append(mock_response)
        
        mock_get.side_effect = mock_responses
        
        # Get document URLs with pagination
        urls = hansard_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
        
        # Verify URLs from all pages
        assert len(urls) == 3
        assert any('hansard-page0.pdf' in url for url in urls)
        assert any('hansard-page1.pdf' in url for url in urls)
        assert any('hansard-page2.pdf' in url for url in urls)
        
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
            user_agent="HansardTales/1.0"
        )
    
    @pytest.fixture
    def votes_scraper(self, config):
        """Create Votes scraper for testing."""
        from hansard_tales.scrapers.votes import VotesScraper
        return VotesScraper(config)
    
    @patch('requests.Session.get')
    def test_get_document_urls_national_assembly(self, mock_get, votes_scraper):
        """Test getting Votes URLs for National Assembly."""
        # Create mock HTML with Votes links in table
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/Tuesday%2C%20November%204%2C%202025%20at%202.30pm.pdf">Tuesday, November 4, 2025 At 2.30pm</a>
                        </td>
                    </tr>
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/Wednesday%2C%20November%205%2C%202025%20at%209.00am.pdf">Wednesday, November 5, 2025 At 9.00am</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
        
        # Verify URLs
        assert len(urls) == 2
        assert any('November%204' in url or 'November 4' in url for url in urls)
        assert any('November%205' in url or 'November 5' in url for url in urls)
        
        # Verify correct URL was called with parliament term parameter
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0]
        assert "national-assembly" in call_args[0]
        assert "votes-proceedings" in call_args[0]
        assert "field_parliament_value=2022" in call_args[0]
        assert "page=0" in call_args[0]
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
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
        assert "votes-proceedings" in call_args[0]
        assert "field_parliament_value=2022" in call_args[0]
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
        
        # Verify URL was found
        assert len(urls) == 1
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
        
        # Verify absolute URL is preserved
        assert len(urls) == 1
        assert urls[0].startswith("https://parliament.go.ke")
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
        
        # Verify only PDF link is included (CSS selector filters by href$=".pdf")
        assert len(urls) == 1
        assert urls[0].endswith('.pdf')
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
        
        # Verify link is included
        assert len(urls) == 1
    
    @patch('requests.Session.get')
    def test_get_document_urls_fallback_to_all_tables(self, mock_get, votes_scraper):
        """Test that empty results are handled correctly."""
        # Create mock HTML without cols-2 table
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
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Get document URLs - should raise error since CSS selector won't match
        with pytest.raises(DataCollectionError):
            votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Attempt to get document URLs
        with pytest.raises(DataCollectionError) as exc_info:
            votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY)
        
        # Verify error message
        error_msg = str(exc_info.value)
        assert "No Votes & Proceedings documents found" in error_msg
        assert "website structure has changed" in error_msg
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
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
        
        assert metadata['document_type'] == 'votes'
        assert metadata['original_filename'] == 'Tuesday ,November 4, 2025 at 2.30pm.pdf'
        assert metadata['date'] == '2025-11-04'
        assert metadata['time'] == '14:30'
        assert metadata['datetime_iso'] == '2025-11-04T14:30:00Z'
    
    def test_extract_metadata_with_date_no_dashes(self, votes_scraper):
        """Test metadata extraction with morning time."""
        url = "https://parliament.go.ke/sites/default/files/2025-11/Wednesday%2C%20November%205%2C%202025%20at%209.00am.pdf"
        content = b"test content"
        
        metadata = votes_scraper.extract_metadata(url, content)
        
        assert metadata['document_type'] == 'votes'
        assert metadata['date'] == '2025-11-05'
        assert metadata['time'] == '09:00'
        assert metadata['datetime_iso'] == '2025-11-05T09:00:00Z'
    
    def test_extract_metadata_without_date(self, votes_scraper):
        """Test metadata extraction when date parsing fails."""
        url = "https://parliament.go.ke/files/votes-document.pdf"
        content = b"test content"
        
        metadata = votes_scraper.extract_metadata(url, content)
        
        assert metadata['document_type'] == 'votes'
        assert metadata['original_filename'] == 'votes-document.pdf'
        assert 'date' not in metadata
    
    def test_extract_metadata_complex_filename(self, votes_scraper):
        """Test metadata extraction with noon time."""
        url = "https://parliament.go.ke/sites/default/files/2025-12/Thursday%2C%20December%2031%2C%202025%20at%2012.00pm.pdf"
        content = b"test content"
        
        metadata = votes_scraper.extract_metadata(url, content)
        
        assert metadata['document_type'] == 'votes'
        assert metadata['date'] == '2025-12-31'
        assert metadata['time'] == '12:00'
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
        
        # Verify URL doesn't have double slashes
        assert len(urls) == 1
        assert "//" not in urls[0].replace("https://", "")
    
    @patch('requests.Session.get')
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
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
        
        # Verify URLs from both tables
        assert len(urls) == 2
    
    @patch('requests.Session.get')
    def test_get_document_urls_case_insensitive_votes_check(self, mock_get, votes_scraper):
        """Test extraction with various filename formats."""
        # Create mock HTML with various formats
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/Tuesday%2C%20November%204%2C%202025%20at%202.30pm.pdf">Doc 1</a>
                        </td>
                        <td class="views-field-field-pdf">
                            <a href="/files/Wednesday%2C%20November%205%2C%202025%20at%209.00am.pdf">Doc 2</a>
                        </td>
                        <td class="views-field-field-pdf">
                            <a href="/files/Thursday%2C%20November%206%2C%202025%20at%2010.00am.pdf">Doc 3</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = html_content.encode('utf-8')
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
    
    @patch('requests.Session.get')
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
        mock_page_response.content = html_content.encode('utf-8')
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
        assert documents[0].metadata['document_type'] == 'votes'
    
    @patch('requests.Session.get')
    def test_get_document_urls_votes_in_url(self, mock_get, votes_scraper):
        """Test extraction using CSS selector."""
        # Create mock HTML with cols-2 structure
        html_content = """
        <html>
            <body>
                <table class="cols-2">
                    <tr>
                        <td class="views-field-field-pdf">
                            <a href="/files/Tuesday%2C%20November%204%2C%202025%20at%202.30pm.pdf">Document</a>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = html_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Get document URLs
        urls = votes_scraper.get_document_urls(Chamber.NATIONAL_ASSEMBLY, parliament_term=2022)
        
        # Verify URL was found
        assert len(urls) == 1



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
            user_agent="HansardTales/1.0"
        )
    
    def test_create_hansard_scraper(self, config):
        """Test creating Hansard scraper."""
        from hansard_tales.scrapers.factory import create_scraper
        from hansard_tales.scrapers.hansard import HansardScraper
        from hansard_tales.models.base import DocumentType
        
        scraper = create_scraper(DocumentType.HANSARD, config)
        
        assert isinstance(scraper, HansardScraper)
        assert scraper.config == config
    
    def test_create_votes_scraper(self, config):
        """Test creating Votes scraper."""
        from hansard_tales.scrapers.factory import create_scraper
        from hansard_tales.scrapers.votes import VotesScraper
        from hansard_tales.models.base import DocumentType
        
        scraper = create_scraper(DocumentType.VOTES, config)
        
        assert isinstance(scraper, VotesScraper)
        assert scraper.config == config
    
    def test_create_scraper_unsupported_type(self, config):
        """Test that unsupported document type raises ValueError."""
        from hansard_tales.scrapers.factory import create_scraper
        from hansard_tales.models.base import DocumentType
        
        # Try to create scraper for unsupported type
        with pytest.raises(ValueError) as exc_info:
            create_scraper(DocumentType.BILL, config)
        
        error_msg = str(exc_info.value)
        assert "No scraper available" in error_msg
        assert "bill" in error_msg.lower()
        assert "Available types" in error_msg
    
    def test_create_scraper_returns_base_scraper(self, config):
        """Test that factory returns BaseScraper instances."""
        from hansard_tales.scrapers.factory import create_scraper
        from hansard_tales.scrapers.base import BaseScraper
        from hansard_tales.models.base import DocumentType
        
        hansard_scraper = create_scraper(DocumentType.HANSARD, config)
        votes_scraper = create_scraper(DocumentType.VOTES, config)
        
        assert isinstance(hansard_scraper, BaseScraper)
        assert isinstance(votes_scraper, BaseScraper)
    
    def test_create_scraper_with_different_configs(self):
        """Test creating scrapers with different configurations."""
        from hansard_tales.scrapers.factory import create_scraper
        from hansard_tales.models.base import DocumentType
        
        config1 = ScraperConfig(
            base_url="https://parliament.go.ke",
            download_dir=Path("data/pdfs1"),
            max_retries=3,
            retry_delay=1.0,
            timeout=30,
            user_agent="HansardTales/1.0"
        )
        
        config2 = ScraperConfig(
            base_url="https://parliament.go.ke",
            download_dir=Path("data/pdfs2"),
            max_retries=5,
            retry_delay=2.0,
            timeout=60,
            user_agent="HansardTales/2.0"
        )
        
        scraper1 = create_scraper(DocumentType.HANSARD, config1)
        scraper2 = create_scraper(DocumentType.HANSARD, config2)
        
        assert scraper1.config.download_dir == Path("data/pdfs1")
        assert scraper2.config.download_dir == Path("data/pdfs2")
        assert scraper1.config.max_retries == 3
        assert scraper2.config.max_retries == 5
    
    def test_factory_error_message_lists_available_types(self, config):
        """Test that error message lists available document types."""
        from hansard_tales.scrapers.factory import create_scraper
        from hansard_tales.models.base import DocumentType
        
        with pytest.raises(ValueError) as exc_info:
            create_scraper(DocumentType.PETITION, config)
        
        error_msg = str(exc_info.value)
        assert "hansard" in error_msg.lower()
        assert "votes" in error_msg.lower()
    
    def test_create_multiple_scrapers_independently(self, config):
        """Test creating multiple scraper instances independently."""
        from hansard_tales.scrapers.factory import create_scraper
        from hansard_tales.models.base import DocumentType
        
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
            user_agent="HansardTales/1.0"
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
            user_agent="HansardTales/1.0"
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
    
    @patch('sqlalchemy.create_engine')
    @patch('sqlalchemy.orm.sessionmaker')
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
    
    @patch('sqlalchemy.create_engine')
    @patch('sqlalchemy.orm.sessionmaker')
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
    
    @patch('sqlalchemy.create_engine')
    def test_is_duplicate_handles_database_error(
        self, mock_create_engine, concrete_scraper
    ):
        """Test that _is_duplicate handles database errors gracefully."""
        # Setup mock to raise exception
        mock_create_engine.side_effect = Exception("Database unavailable")
        
        # Check for duplicate
        result = concrete_scraper._is_duplicate("test_hash")
        
        # Verify returns False on error (allows scraper to continue)
        assert result is False
    
    @patch('sqlalchemy.create_engine')
    @patch('sqlalchemy.orm.sessionmaker')
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
            metadata={"document_type": "hansard", "original_filename": "test.pdf"}
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
    
    @patch('sqlalchemy.create_engine')
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
            metadata={"document_type": "hansard"}
        )
        
        file_path = tmp_path / "test.pdf"
        
        # Record download - should not raise exception
        concrete_scraper._record_download(doc, file_path, Chamber.NATIONAL_ASSEMBLY)
        
        # Test passes if no exception raised
        assert True
    
    @patch('sqlalchemy.create_engine')
    @patch('sqlalchemy.orm.sessionmaker')
    @patch.object(BaseScraper, 'download_document')
    @patch.object(BaseScraper, 'save_document')
    def test_scrape_records_downloads(
        self, mock_save, mock_download, mock_sessionmaker, 
        mock_create_engine, concrete_scraper, tmp_path
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
            metadata={"document_type": "hansard", "original_filename": "test.pdf"}
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
