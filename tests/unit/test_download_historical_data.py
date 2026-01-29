"""
Tests for download_historical_data.py script.

Tests the historical data downloader with mock data to verify
parliament term iteration, date range support, progress tracking,
resume capability, and error handling.
"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from download_historical_data import HistoricalDataDownloader  # noqa: E402


class TestHistoricalDataDownloader:
    """Test suite for HistoricalDataDownloader."""

    def test_initialization(self):
        """Test downloader initialization."""
        downloader = HistoricalDataDownloader()

        assert downloader.output_dir is not None
        assert downloader.resume is True
        assert downloader.workers == 4
        assert "hansard" in downloader.stats
        assert "votes" in downloader.stats
        assert "mps" in downloader.stats

    def test_parliament_term_mapping(self):
        """Test parliament term mapping is correct."""
        downloader = HistoricalDataDownloader()

        # Check all terms are defined
        assert 2013 in downloader.PARLIAMENT_TERMS
        assert 2017 in downloader.PARLIAMENT_TERMS
        assert 2022 in downloader.PARLIAMENT_TERMS

        # Check term details
        term_2022 = downloader.PARLIAMENT_TERMS[2022]
        assert term_2022["term"] == 13
        assert term_2022["start"] == date(2022, 9, 13)
        assert term_2022["end"] == date(2027, 8, 31)

    def test_get_parliament_term_valid_year(self):
        """Test getting parliament term for valid year."""
        downloader = HistoricalDataDownloader()

        # Test year within term
        term_info = downloader._get_parliament_term(2024)
        assert term_info is not None
        assert term_info["term"] == 13
        assert term_info["term_start_year"] == 2022

    def test_get_parliament_term_invalid_year(self):
        """Test getting parliament term for invalid year."""
        downloader = HistoricalDataDownloader()

        # Test year before any term
        term_info = downloader._get_parliament_term(2010)
        assert term_info is None

        # Test year after all terms
        term_info = downloader._get_parliament_term(2030)
        assert term_info is None

    @patch("download_historical_data.HansardScraper")
    def test_download_hansard(self, mock_scraper_class):
        """Test downloading Hansard documents."""
        # Setup mock
        mock_scraper = Mock()
        mock_scraper.scrape.return_value = [Mock(), Mock(), Mock()]
        mock_scraper_class.return_value = mock_scraper

        downloader = HistoricalDataDownloader()

        # Download Hansard
        from hansard_tales.models.base import Chamber

        count = downloader.download_hansard(
            chamber=Chamber.NATIONAL_ASSEMBLY,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            parliament_term=2022,
        )

        # Verify
        assert count == 3
        assert downloader.stats["hansard"]["downloaded"] == 3
        mock_scraper.scrape.assert_called_once()

    @patch("download_historical_data.VotesScraper")
    def test_download_votes(self, mock_scraper_class):
        """Test downloading Votes & Proceedings documents."""
        # Setup mock
        mock_scraper = Mock()
        mock_scraper.scrape.return_value = [Mock(), Mock()]
        mock_scraper_class.return_value = mock_scraper

        downloader = HistoricalDataDownloader()

        # Download Votes
        from hansard_tales.models.base import Chamber

        count = downloader.download_votes(
            chamber=Chamber.NATIONAL_ASSEMBLY,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            parliament_term=2022,
        )

        # Verify
        assert count == 2
        assert downloader.stats["votes"]["downloaded"] == 2
        mock_scraper.scrape.assert_called_once()

    @patch("download_historical_data.MPScraper")
    def test_download_mps(self, mock_scraper_class):
        """Test downloading MP data."""
        # Setup mock
        mock_scraper = Mock()
        mock_scraper.scrape_mps.return_value = [Mock(), Mock(), Mock(), Mock()]
        mock_scraper.store_mps.return_value = 4
        mock_scraper_class.return_value = mock_scraper

        downloader = HistoricalDataDownloader()

        # Download MPs
        from hansard_tales.models.base import Chamber

        count = downloader.download_mps(
            chamber=Chamber.NATIONAL_ASSEMBLY,
            parliament_term=2022,
        )

        # Verify
        assert count == 4
        assert downloader.stats["mps"]["downloaded"] == 4
        mock_scraper.scrape_mps.assert_called_once()
        mock_scraper.store_mps.assert_called_once()

    @patch("download_historical_data.HansardScraper")
    @patch("download_historical_data.VotesScraper")
    @patch("download_historical_data.MPScraper")
    def test_download_for_year(self, mock_mp, mock_votes, mock_hansard):
        """Test downloading all documents for a year."""
        # Setup mocks
        mock_hansard.return_value.scrape.return_value = [Mock()]
        mock_votes.return_value.scrape.return_value = [Mock()]
        mock_mp.return_value.scrape_mps.return_value = [Mock()]
        mock_mp.return_value.store_mps.return_value = 1

        downloader = HistoricalDataDownloader()

        # Download for year
        from hansard_tales.models.base import Chamber

        stats = downloader.download_for_year(
            year=2024,
            document_types=["hansard", "votes", "mps"],
            chamber=Chamber.NATIONAL_ASSEMBLY,
        )

        # Verify all types were downloaded
        assert stats["hansard"]["downloaded"] == 1
        assert stats["votes"]["downloaded"] == 1
        assert stats["mps"]["downloaded"] == 1

    @patch("download_historical_data.HansardScraper")
    def test_download_error_handling(self, mock_scraper_class):
        """Test error handling during download."""
        # Setup mock to raise exception
        mock_scraper = Mock()
        mock_scraper.scrape.side_effect = Exception("Network error")
        mock_scraper_class.return_value = mock_scraper

        downloader = HistoricalDataDownloader()

        # Download should handle error gracefully
        from hansard_tales.models.base import Chamber

        count = downloader.download_hansard(
            chamber=Chamber.NATIONAL_ASSEMBLY,
            parliament_term=2022,
        )

        # Verify error was tracked
        assert count == 0
        assert downloader.stats["hansard"]["failed"] == 1

    def test_print_summary(self, capsys):
        """Test printing download summary."""
        downloader = HistoricalDataDownloader()

        # Set some stats
        downloader.stats["hansard"]["downloaded"] = 10
        downloader.stats["votes"]["downloaded"] = 5
        downloader.stats["mps"]["downloaded"] = 350

        # Print summary
        downloader.print_summary()

        # Capture output
        captured = capsys.readouterr()

        # Verify output contains stats
        assert "DOWNLOAD SUMMARY" in captured.out
        assert "HANSARD" in captured.out
        assert "10" in captured.out
        assert "VOTES" in captured.out
        assert "5" in captured.out
        assert "MPS" in captured.out
        assert "350" in captured.out
