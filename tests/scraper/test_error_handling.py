"""
Tests for error handling in download operations.
"""

import tempfile
from unittest.mock import Mock, patch

import pytest

from hansard_tales.scrapers.hansard_scraper import HansardScraper


@pytest.fixture
def scraper():
    """Create a scraper instance for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from hansard_tales.storage.filesystem import FilesystemStorage
        storage = FilesystemStorage(tmpdir)
        yield HansardScraper(storage=storage, rate_limit_delay=0.1)


class TestErrorHandling:
    """Test suite for error handling in download operations."""
    
    @patch('hansard_tales.scrapers.hansard_scraper.requests.Session')
    def test_download_pdf_network_error(self, mock_session_class, scraper):
        """Test download_pdf() with network error."""
        import requests
        
        # Mock session that raises network error
        mock_session = Mock()
        mock_session.get = Mock(side_effect=requests.RequestException("Network error"))
        scraper.session = mock_session
        
        # Attempt download with new signature (url, title, date)
        success = scraper.download_pdf(
            'https://example.com/test.pdf',
            'Morning Session',
            '2024-01-01'
        )
        
        # Should return False
        assert success is False
        
        # File should not exist
        files = scraper.storage.list_files('hansard_20240101')
        assert len(files) == 0
    
    @patch('hansard_tales.scrapers.hansard_scraper.requests.Session')
    def test_download_pdf_partial_download_cleanup(self, mock_session_class, scraper):
        """Test download_pdf() cleans up partial downloads."""
        import requests
        
        # Mock response that writes partial data then fails
        mock_response = Mock()
        mock_response.iter_content = Mock(side_effect=requests.RequestException("Connection lost"))
        mock_response.raise_for_status = Mock()
        
        mock_session = Mock()
        mock_session.get = Mock(return_value=mock_response)
        scraper.session = mock_session
        
        # Attempt download with new signature
        success = scraper.download_pdf(
            'https://example.com/test.pdf',
            'Morning Session',
            '2024-01-01'
        )
        
        # Should return False
        assert success is False
        
        # Partial file should be cleaned up
        files = scraper.storage.list_files('hansard_20240101')
        assert len(files) == 0
    
    def test_download_pdf_database_error(self):
        """Test download_pdf() continues despite database error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from hansard_tales.storage.filesystem import FilesystemStorage
            
            # Create scraper with invalid database
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(
                storage=storage,
                db_path='/invalid/path/db.db',
                rate_limit_delay=0.1
            )
            
            # Mock successful download
            mock_response = Mock()
            mock_response.iter_content = Mock(return_value=[b'PDF content'])
            mock_response.raise_for_status = Mock()
            
            mock_session = Mock()
            mock_session.get = Mock(return_value=mock_response)
            scraper.session = mock_session
            
            # Download should succeed despite database error
            success = scraper.download_pdf(
                'https://example.com/test.pdf',
                'Morning Session',
                '2024-01-01'
            )
            
            assert success is True
            # Check file exists using storage
            files = scraper.storage.list_files('hansard_20240101')
            assert len(files) > 0
