"""
Tests for CLI argument parsing and main() function.
"""

from unittest.mock import Mock, patch

import pytest


class TestCLI:
    """Test suite for CLI argument parsing and main() function."""
    
    @patch('hansard_tales.scrapers.hansard_scraper.HansardScraper')
    @patch('sys.argv', ['hansard-scraper', '--max-pages', '3', '--storage-dir', 'test_output'])
    def test_main_with_arguments(self, mock_scraper_class):
        """Test main() with custom arguments."""
        from hansard_tales.scrapers.hansard_scraper import main
        
        # Mock scraper instance
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = [
            {'title': 'Test Hansard', 'date': '2024-01-01', 'url': 'http://test.pdf', 'filename': '20240101_0.pdf'}
        ]
        mock_scraper.download_all.return_value = {
            'total': 1, 'downloaded': 1, 'skipped': 0, 'failed': 0
        }
        mock_scraper_class.return_value = mock_scraper
        
        # Run main
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Should exit with 0 (success)
        assert exc_info.value.code == 0
        
        # Verify scraper was initialized with correct args
        mock_scraper_class.assert_called_once()
        
        # Verify scrape_all was called
        mock_scraper.scrape_all.assert_called_once_with(max_pages=3)
        
        # Verify download_all was called
        mock_scraper.download_all.assert_called_once()
    
    @patch('hansard_tales.scrapers.hansard_scraper.HansardScraper')
    @patch('sys.argv', ['hansard-scraper', '--dry-run'])
    def test_main_dry_run(self, mock_scraper_class):
        """Test main() with --dry-run flag."""
        from hansard_tales.scrapers.hansard_scraper import main
        
        # Mock scraper instance
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = [
            {'title': 'Test Hansard', 'date': '2024-01-01', 'url': 'http://test.pdf', 'filename': '20240101_0.pdf'}
        ]
        mock_scraper_class.return_value = mock_scraper
        
        # Run main
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Should exit with 0 (success)
        assert exc_info.value.code == 0
        
        # Verify download_all was NOT called (dry run)
        mock_scraper.download_all.assert_not_called()
    
    @patch('hansard_tales.scrapers.hansard_scraper.HansardScraper')
    @patch('sys.argv', ['hansard-scraper'])
    def test_main_no_hansards_found(self, mock_scraper_class):
        """Test main() when no Hansards are found."""
        from hansard_tales.scrapers.hansard_scraper import main
        
        # Mock scraper instance that returns empty list
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = []
        mock_scraper_class.return_value = mock_scraper
        
        # Run main
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Should exit with 1 (failure)
        assert exc_info.value.code == 1
    
    @patch('hansard_tales.scrapers.hansard_scraper.HansardScraper')
    @patch('sys.argv', ['hansard-scraper'])
    def test_main_download_failures(self, mock_scraper_class):
        """Test main() when downloads fail."""
        from hansard_tales.scrapers.hansard_scraper import main
        
        # Mock scraper instance
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = [
            {'title': 'Test Hansard', 'date': '2024-01-01', 'url': 'http://test.pdf', 'filename': '20240101_0.pdf'}
        ]
        mock_scraper.download_all.return_value = {
            'total': 1, 'downloaded': 0, 'skipped': 0, 'failed': 1
        }
        mock_scraper_class.return_value = mock_scraper
        
        # Run main
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Should exit with 1 (failure due to failed downloads)
        assert exc_info.value.code == 1
