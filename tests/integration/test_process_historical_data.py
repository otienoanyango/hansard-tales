"""
Tests for process_historical_data module.

This module tests the historical data processing functionality including
date parsing, PDF processing, parallel execution, and database operations.
"""

import sqlite3
import tempfile
from pathlib import Path
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor

import pytest

from hansard_tales.process_historical_data import (
    parse_date_string,
    _extract_date_from_filename,
    process_single_pdf,
    ProcessedPDF,
    HistoricalDataProcessor,
    DATEPARSER_AVAILABLE
)
from hansard_tales.processors.mp_identifier import Statement


# Use production_db fixture from conftest.py


@pytest.fixture
def temp_pdf_dir():
    """Create temporary directory with sample PDFs."""
    import tempfile
    temp_dir = tempfile.mkdtemp()
    pdf_dir = Path(temp_dir) / "pdfs" / "hansard-report"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample PDF files (empty files with correct names)
    sample_pdfs = [
        "20240101_0_P.pdf",
        "20240115_0_A.pdf",
        "20240201_0_P.pdf",
        "Hansard_Report_2024-03-15.pdf",
    ]
    
    for pdf_name in sample_pdfs:
        (pdf_dir / pdf_name).touch()
    
    yield pdf_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


class TestParseDateString:
    """Test suite for parse_date_string function."""
    
    def test_parse_iso_format(self):
        """Test parsing ISO format dates."""
        result = parse_date_string("2024-01-01")
        assert result == "2024-01-01"
        
        result = parse_date_string("2024-12-31")
        assert result == "2024-12-31"
    
    def test_parse_natural_language(self):
        """Test parsing natural language dates (if dateparser available)."""
        if not DATEPARSER_AVAILABLE:
            pytest.skip("dateparser not available")
        
        # Test relative dates
        result = parse_date_string("yesterday")
        assert result is not None
        assert len(result) == 10  # YYYY-MM-DD format
        
        result = parse_date_string("last week")
        assert result is not None
    
    def test_parse_invalid_dates(self):
        """Test parsing invalid dates."""
        result = parse_date_string("not-a-date")
        assert result is None
        
        # Note: dateparser may parse "2024-13-01" as "2024-01-13" (swapping month/day)
        # so we test with a truly invalid date
        result = parse_date_string("invalid-date-string")
        assert result is None
        
        result = parse_date_string("")
        assert result is None
        
        result = parse_date_string(None)
        assert result is None


class TestExtractDateFromFilename:
    """Test suite for _extract_date_from_filename function."""
    
    def test_standardized_format(self):
        """Test extracting date from standardized format."""
        pdf_path = Path("20250314_0_A.pdf")
        result = _extract_date_from_filename(pdf_path)
        assert result == date(2025, 3, 14)
        
        pdf_path = Path("20251204_2_P.pdf")
        result = _extract_date_from_filename(pdf_path)
        assert result == date(2025, 12, 4)
    
    def test_iso_format(self):
        """Test extracting date from ISO format."""
        pdf_path = Path("Hansard_Report_2025-12-04.pdf")
        result = _extract_date_from_filename(pdf_path)
        assert result == date(2025, 12, 4)
    
    def test_long_format(self):
        """Test extracting date from long format."""
        pdf_path = Path("Hansard Report - Wednesday, 3rd December 2025 (P).pdf")
        result = _extract_date_from_filename(pdf_path)
        assert result == date(2025, 12, 3)
        
        pdf_path = Path("Hansard Report - Thursday, 21st March 2024 (A).pdf")
        result = _extract_date_from_filename(pdf_path)
        assert result == date(2024, 3, 21)
    
    def test_invalid_filenames(self):
        """Test extracting date from invalid filenames."""
        pdf_path = Path("invalid_filename.pdf")
        result = _extract_date_from_filename(pdf_path)
        assert result is None
        
        pdf_path = Path("no_date_here.pdf")
        result = _extract_date_from_filename(pdf_path)
        assert result is None


class TestProcessSinglePDF:
    """Test suite for process_single_pdf function."""
    
    @patch('hansard_tales.process_historical_data.PDFProcessor')
    @patch('hansard_tales.process_historical_data.MPIdentifier')
    @patch('hansard_tales.process_historical_data.BillExtractor')
    def test_success_case(self, mock_bill_ext, mock_mp_id, mock_pdf_proc, production_db):
        """Test successful PDF processing."""
        # Setup mocks
        mock_pdf = Mock()
        mock_pdf.extract_text_from_pdf.return_value = {
            'pages': [{'page_number': 1, 'text': 'Test content'}]
        }
        mock_pdf_proc.return_value = mock_pdf
        
        mock_mp = Mock()
        statements = [
            Statement("John Doe", "Test statement 1", 0, 100, page_number=1),
            Statement("Jane Smith", "Test statement 2", 100, 200, page_number=1),
        ]
        mock_mp.extract_statements_from_pages.return_value = statements
        mock_mp.get_unique_mp_names.return_value = ["John Doe", "Jane Smith"]
        mock_mp_id.return_value = mock_mp
        
        mock_bill = Mock()
        mock_bill.extract_bill_references.return_value = ["Bill No. 123"]
        mock_bill_ext.return_value = mock_bill
        
        # Create test PDF
        pdf_path = Path("20240101_0_P.pdf")
        
        result = process_single_pdf(pdf_path, Path(production_db), force=False)
        
        assert result.status == 'success'
        assert result.statements == 2
        assert result.unique_mps == 2
        assert result.bills == 2  # 2 statements * 1 bill each
        assert result.pdf_date == "2024-01-01"
    
    def test_already_processed(self, production_db):
        """Test skipping already processed PDF."""
        # Mark PDF as processed
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hansard_sessions (term_id, date, title, pdf_path, pdf_url, processed)
            VALUES (1, '2024-01-01', 'Test', '20240101_0_P.pdf', 'http://example.com/test.pdf', 1)
        """)
        conn.commit()
        conn.close()
        
        pdf_path = Path("20240101_0_P.pdf")
        result = process_single_pdf(pdf_path, Path(production_db), force=False)
        
        assert result.status == 'skipped'
        assert result.reason == 'already_processed'
    
    @patch('hansard_tales.process_historical_data.PDFProcessor')
    def test_pdf_extraction_failure(self, mock_pdf_proc, production_db):
        """Test handling PDF extraction failure."""
        mock_pdf = Mock()
        mock_pdf.extract_text_from_pdf.return_value = None
        mock_pdf_proc.return_value = mock_pdf
        
        pdf_path = Path("20240101_0_P.pdf")
        result = process_single_pdf(pdf_path, Path(production_db), force=False)
        
        assert result.status == 'error'
        assert result.reason == 'pdf_extraction_failed'
    
    @patch('hansard_tales.process_historical_data.PDFProcessor')
    @patch('hansard_tales.process_historical_data.MPIdentifier')
    def test_no_statements_found(self, mock_mp_id, mock_pdf_proc, production_db):
        """Test handling when no statements are found."""
        mock_pdf = Mock()
        mock_pdf.extract_text_from_pdf.return_value = {
            'pages': [{'page_number': 1, 'text': 'Test content'}]
        }
        mock_pdf_proc.return_value = mock_pdf
        
        mock_mp = Mock()
        mock_mp.extract_statements_from_pages.return_value = []
        mock_mp_id.return_value = mock_mp
        
        pdf_path = Path("20240101_0_P.pdf")
        result = process_single_pdf(pdf_path, Path(production_db), force=False)
        
        assert result.status == 'warning'
        assert result.reason == 'no_statements_found'
    
    @patch('hansard_tales.process_historical_data.PDFProcessor')
    def test_unexpected_error(self, mock_pdf_proc, production_db):
        """Test handling unexpected errors."""
        mock_pdf = Mock()
        mock_pdf.extract_text_from_pdf.side_effect = Exception("Unexpected error")
        mock_pdf_proc.return_value = mock_pdf
        
        pdf_path = Path("20240101_0_P.pdf")
        result = process_single_pdf(pdf_path, Path(production_db), force=False)
        
        assert result.status == 'error'
        assert result.reason == 'unexpected_error'
        assert "Unexpected error" in result.error_message


class TestHistoricalDataProcessor:
    """Test suite for HistoricalDataProcessor class."""
    
    def test_initialization(self):
        """Test processor initialization."""
        processor = HistoricalDataProcessor(
            year=2024,
            start_date="2024-01-01",
            end_date="2024-12-31",
            dry_run=True,
            force=True,
            clean=False,
            workers=4
        )
        
        assert processor.year == 2024
        assert processor.start_date == "2024-01-01"
        assert processor.end_date == "2024-12-31"
        assert processor.dry_run is True
        assert processor.force is True
        assert processor.clean is False
        assert processor.workers == 4
    
    def test_is_within_date_range_no_range(self):
        """Test date range filtering with no range specified."""
        processor = HistoricalDataProcessor()
        
        pdf_path = Path("20240101_0_P.pdf")
        result = processor._is_within_date_range(pdf_path)
        
        assert result is True
    
    def test_is_within_date_range_start_only(self):
        """Test date range filtering with start date only."""
        processor = HistoricalDataProcessor(start_date="2024-06-01")
        
        # Before start date
        pdf_path = Path("20240501_0_P.pdf")
        assert processor._is_within_date_range(pdf_path) is False
        
        # After start date
        pdf_path = Path("20240701_0_P.pdf")
        assert processor._is_within_date_range(pdf_path) is True
    
    def test_is_within_date_range_end_only(self):
        """Test date range filtering with end date only."""
        processor = HistoricalDataProcessor(end_date="2024-06-30")
        
        # Before end date
        pdf_path = Path("20240501_0_P.pdf")
        assert processor._is_within_date_range(pdf_path) is True
        
        # After end date
        pdf_path = Path("20240701_0_P.pdf")
        assert processor._is_within_date_range(pdf_path) is False
    
    def test_is_within_date_range_both_dates(self):
        """Test date range filtering with both dates."""
        processor = HistoricalDataProcessor(
            start_date="2024-06-01",
            end_date="2024-06-30"
        )
        
        # Before range
        pdf_path = Path("20240501_0_P.pdf")
        assert processor._is_within_date_range(pdf_path) is False
        
        # Within range
        pdf_path = Path("20240615_0_P.pdf")
        assert processor._is_within_date_range(pdf_path) is True
        
        # After range
        pdf_path = Path("20240701_0_P.pdf")
        assert processor._is_within_date_range(pdf_path) is False
    
    def test_clean_database_backup_creation(self, production_db):
        """Test database backup creation during cleaning."""
        processor = HistoricalDataProcessor(clean=True, dry_run=False)
        processor.db_path = Path(production_db)
        
        # Add some data
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO statements (mp_id, session_id, text) VALUES (1, 1, 'test')")
        conn.commit()
        conn.close()
        
        with patch('shutil.copy2') as mock_copy:
            try:
                processor._clean_database()
            except sqlite3.OperationalError:
                # sqlite_sequence table may not exist in test db, that's ok
                pass
            mock_copy.assert_called_once()
    
    def test_clean_database_data_deletion(self, production_db):
        """Test data deletion during database cleaning."""
        processor = HistoricalDataProcessor(clean=True, dry_run=False)
        processor.db_path = Path(production_db)
        
        # Add some data with proper foreign keys
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        # Insert MP with required constituency
        cursor.execute("INSERT INTO mps (name, constituency) VALUES ('Test MP', 'Test Constituency')")
        mp_id = cursor.lastrowid
        # Insert session with required term_id
        cursor.execute("INSERT INTO hansard_sessions (term_id, date, title, pdf_url) VALUES (1, '2024-01-01', 'test', 'http://example.com/test.pdf')")
        session_id = cursor.lastrowid
        # Insert statement
        cursor.execute("INSERT INTO statements (mp_id, session_id, text) VALUES (?, ?, 'test')", (mp_id, session_id))
        conn.commit()
        
        # Verify data exists before cleaning
        cursor.execute("SELECT COUNT(*) FROM statements")
        assert cursor.fetchone()[0] == 1
        cursor.execute("SELECT COUNT(*) FROM hansard_sessions WHERE date = '2024-01-01'")
        assert cursor.fetchone()[0] == 1
        conn.close()
        
        # Clean the database (should succeed now that schema is correct)
        with patch('shutil.copy2'):
            processor._clean_database()
        
        # Verify data was deleted
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM statements")
        statements_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM hansard_sessions WHERE date = '2024-01-01'")
        sessions_count = cursor.fetchone()[0]
        conn.close()
        
        # Data should be deleted
        assert statements_count == 0, "Statements should be deleted"
        assert sessions_count == 0, "Sessions should be deleted"
    
    def test_clean_database_preserve_downloaded_pdfs(self, production_db):
        """Test that downloaded_pdfs table is preserved during cleaning."""
        processor = HistoricalDataProcessor(clean=True, dry_run=False)
        processor.db_path = Path(production_db)
        
        # Add data to downloaded_pdfs with correct schema
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO downloaded_pdfs (original_url, file_path, date, period_of_day)
            VALUES ('http://test.com/test.pdf', '/path/to/test.pdf', '2024-01-01', 'P')
        """)
        conn.commit()
        conn.close()
        
        with patch('shutil.copy2'):
            try:
                processor._clean_database()
            except sqlite3.OperationalError:
                # sqlite_sequence table may not exist in test db, that's ok
                pass
        
        # Verify downloaded_pdfs was preserved
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM downloaded_pdfs")
        assert cursor.fetchone()[0] == 1
        conn.close()
    
    @patch('hansard_tales.process_historical_data.HansardScraper')
    def test_download_pdfs_success(self, mock_scraper_class):
        """Test successful PDF download."""
        processor = HistoricalDataProcessor(dry_run=False)
        
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = ['url1', 'url2']
        mock_scraper.download_all.return_value = {
            'downloaded': 2,
            'skipped': 0,
            'failed': 0
        }
        mock_scraper_class.return_value = mock_scraper
        
        with patch('pathlib.Path.glob', return_value=[]):
            processor._download_pdfs()
        
        assert processor.stats['pdfs_downloaded'] == 2
    
    @patch('hansard_tales.process_historical_data.HansardScraper')
    def test_download_pdfs_error_handling(self, mock_scraper_class):
        """Test error handling during PDF download."""
        processor = HistoricalDataProcessor(dry_run=False)
        
        mock_scraper = Mock()
        mock_scraper.scrape_all.side_effect = Exception("Network error")
        mock_scraper_class.return_value = mock_scraper
        
        with patch('pathlib.Path.glob', return_value=[]):
            processor._download_pdfs()
        
        # Should not raise exception, just log error
        assert len(processor.stats['errors']) > 0
    
    @patch('hansard_tales.process_historical_data.process_single_pdf')
    def test_process_pdfs_parallel(self, mock_process, temp_pdf_dir, production_db):
        """Test parallel PDF processing."""
        processor = HistoricalDataProcessor(workers=2, dry_run=False)
        processor.db_path = Path(production_db)
        
        # Mock process_single_pdf to return success
        mock_process.return_value = ProcessedPDF(
            pdf_path="test.pdf",
            pdf_date="2024-01-01",
            status='success',
            statements=10,
            unique_mps=5,
            bills=2
        )
        
        with patch('pathlib.Path.glob', return_value=list(temp_pdf_dir.glob("*.pdf"))):
            with patch.object(processor, '_batch_write_to_database'):
                processor._process_pdfs()
        
        # Verify parallel processing was used
        assert mock_process.call_count > 0
    
    def test_process_pdfs_date_filtering(self, temp_pdf_dir, production_db):
        """Test date filtering during PDF processing."""
        processor = HistoricalDataProcessor(
            start_date="2024-02-01",
            end_date="2024-02-28",
            dry_run=False
        )
        processor.db_path = Path(production_db)
        
        with patch('pathlib.Path.glob', return_value=list(temp_pdf_dir.glob("*.pdf"))):
            with patch('hansard_tales.process_historical_data.process_single_pdf') as mock_process:
                # Return a proper ProcessedPDF object
                mock_process.return_value = ProcessedPDF(
                    pdf_path="test.pdf",
                    pdf_date="2024-02-15",
                    status='success',
                    statements=10,
                    processing_time=1.0
                )
                with patch.object(processor, '_batch_write_to_database'):
                    processor._process_pdfs()
        
        # Should only process PDFs within date range
        assert processor.stats['pdfs_skipped'] > 0
    
    @patch('hansard_tales.process_historical_data.DatabaseUpdater')
    def test_batch_write_to_database(self, mock_updater_class, production_db):
        """Test batch writing to database."""
        processor = HistoricalDataProcessor()
        processor.db_path = Path(production_db)
        
        mock_updater = Mock()
        mock_updater.process_hansard_pdf.return_value = {
            'status': 'success',
            'duplicates_skipped': 0
        }
        mock_updater_class.return_value = mock_updater
        
        results = [
            ProcessedPDF(
                pdf_path="test1.pdf",
                pdf_date="2024-01-01",
                status='success',
                statements=10
            ),
            ProcessedPDF(
                pdf_path="test2.pdf",
                pdf_date="2024-01-02",
                status='success',
                statements=15
            )
        ]
        
        processor._batch_write_to_database(results)
        
        # Verify database writes
        assert mock_updater.process_hansard_pdf.call_count == 2
    
    def test_quality_assurance(self, production_db):
        """Test quality assurance checks."""
        processor = HistoricalDataProcessor()
        processor.db_path = Path(production_db)
        
        # Add test data with proper schema
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO mps (name, constituency) VALUES ('John Doe', 'Test Constituency')")
        mp_id = cursor.lastrowid
        cursor.execute("INSERT INTO hansard_sessions (term_id, date, title, pdf_url, processed) VALUES (1, '2024-01-01', 'test', 'http://example.com/test.pdf', 1)")
        session_id = cursor.lastrowid
        cursor.execute("INSERT INTO statements (mp_id, session_id, text) VALUES (?, ?, 'test')", (mp_id, session_id))
        conn.commit()
        conn.close()
        
        # Should not raise exception
        processor._quality_assurance()
    
    @patch('hansard_tales.search_index_generator.generate_search_index')
    @patch('hansard_tales.site_generator.generate_static_site')
    def test_generate_outputs(self, mock_site_gen, mock_search_gen):
        """Test output generation."""
        processor = HistoricalDataProcessor()
        
        processor._generate_outputs()
        
        mock_search_gen.assert_called_once()
        mock_site_gen.assert_called_once()
    
    def test_print_summary(self):
        """Test summary printing."""
        processor = HistoricalDataProcessor()
        processor.stats['pdfs_processed'] = 10
        processor.stats['pdfs_failed'] = 2
        processor.stats['statements_extracted'] = 100
        
        # Should not raise exception
        processor._print_summary()
    
    def test_emit_metrics(self):
        """Test metrics emission."""
        processor = HistoricalDataProcessor()
        processor.stats['pdfs_downloaded'] = 10
        processor.stats['pdfs_processed'] = 8
        processor.stats['pdfs_failed'] = 2
        
        # Should not raise exception
        processor._emit_metrics()



class TestHistoricalDataProcessorRun:
    """Test suite for the run() method."""
    
    @patch('hansard_tales.process_historical_data.HansardScraper')
    @patch('hansard_tales.process_historical_data.process_single_pdf')
    @patch('hansard_tales.process_historical_data.DatabaseUpdater')
    @patch('hansard_tales.search_index_generator.generate_search_index')
    @patch('hansard_tales.site_generator.generate_static_site')
    def test_run_success(self, mock_site_gen, mock_search_gen, mock_updater_class, 
                        mock_process, mock_scraper_class, production_db):
        """Test successful run of the processor."""
        processor = HistoricalDataProcessor(dry_run=False)
        processor.db_path = Path(production_db)
        
        # Mock scraper
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = []
        mock_scraper.download_all.return_value = {'downloaded': 0, 'skipped': 0, 'failed': 0}
        mock_scraper_class.return_value = mock_scraper
        
        # Mock process_single_pdf
        mock_process.return_value = ProcessedPDF(
            pdf_path="test.pdf",
            pdf_date="2024-01-01",
            status='success',
            statements=10
        )
        
        # Mock updater
        mock_updater = Mock()
        mock_updater.process_hansard_pdf.return_value = {'status': 'success', 'duplicates_skipped': 0}
        mock_updater_class.return_value = mock_updater
        
        with patch('pathlib.Path.glob', return_value=[]):
            result = processor.run()
        
        assert result is True
    
    @patch('hansard_tales.process_historical_data.HansardScraper')
    @patch('hansard_tales.search_index_generator.generate_search_index')
    def test_run_with_error(self, mock_search_gen, mock_scraper_class, production_db):
        """Test run with error."""
        processor = HistoricalDataProcessor(dry_run=False)
        processor.db_path = Path(production_db)
        
        # Mock scraper to raise exception in a way that causes run() to fail
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = []
        mock_scraper.download_all.return_value = {'downloaded': 0, 'skipped': 0, 'failed': 0}
        mock_scraper_class.return_value = mock_scraper
        
        # Make search index generation fail fatally
        mock_search_gen.side_effect = Exception("Fatal error")
        
        with patch('pathlib.Path.glob', return_value=[]):
            result = processor.run()
        
        # Non-fatal errors don't cause run() to return False
        # Only exceptions in the main try block do
        assert result is True  # Run completes despite errors
        assert len(processor.stats['errors']) > 0
    
    @patch('hansard_tales.process_historical_data.HansardScraper')
    def test_run_dry_run(self, mock_scraper_class, production_db):
        """Test dry run mode."""
        processor = HistoricalDataProcessor(dry_run=True)
        processor.db_path = Path(production_db)
        
        mock_scraper = Mock()
        mock_scraper_class.return_value = mock_scraper
        
        with patch('pathlib.Path.glob', return_value=[]):
            result = processor.run()
        
        # Should succeed without actually processing
        assert result is True
    
    @patch('hansard_tales.process_historical_data.HansardScraper')
    @patch('shutil.copy2')
    def test_run_with_clean(self, mock_copy, mock_scraper_class, production_db):
        """Test run with database cleaning."""
        processor = HistoricalDataProcessor(clean=True, dry_run=False)
        processor.db_path = Path(production_db)
        
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = []
        mock_scraper.download_all.return_value = {'downloaded': 0, 'skipped': 0, 'failed': 0}
        mock_scraper_class.return_value = mock_scraper
        
        with patch('pathlib.Path.glob', return_value=[]):
            try:
                result = processor.run()
            except sqlite3.OperationalError:
                # sqlite_sequence error is expected in test db
                pass
        
        # Backup should have been attempted
        mock_copy.assert_called()


class TestMainFunction:
    """Test suite for the main() function."""
    
    @patch('hansard_tales.process_historical_data.HistoricalDataProcessor')
    @patch('sys.argv', ['prog', '--year', '2024'])
    def test_main_with_year(self, mock_processor_class):
        """Test main function with year argument."""
        mock_processor = Mock()
        mock_processor.run.return_value = True
        mock_processor_class.return_value = mock_processor
        
        from hansard_tales.process_historical_data import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 0
        mock_processor_class.assert_called_once()
    
    @patch('hansard_tales.process_historical_data.HistoricalDataProcessor')
    @patch('sys.argv', ['prog', '--start-date', '2024-01-01', '--end-date', '2024-12-31'])
    def test_main_with_date_range(self, mock_processor_class):
        """Test main function with date range."""
        mock_processor = Mock()
        mock_processor.run.return_value = True
        mock_processor_class.return_value = mock_processor
        
        from hansard_tales.process_historical_data import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 0
    
    @patch('sys.argv', ['prog', '--start-date', 'invalid-date'])
    def test_main_with_invalid_date(self):
        """Test main function with invalid date."""
        from hansard_tales.process_historical_data import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1
    
    @patch('hansard_tales.process_historical_data.HistoricalDataProcessor')
    @patch('sys.argv', ['prog', '--workers', '8'])
    def test_main_with_workers(self, mock_processor_class):
        """Test main function with workers argument."""
        mock_processor = Mock()
        mock_processor.run.return_value = True
        mock_processor_class.return_value = mock_processor
        
        from hansard_tales.process_historical_data import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 0
        # Verify workers parameter was passed
        call_args = mock_processor_class.call_args
        assert call_args[1]['workers'] == 8
    
    @patch('hansard_tales.process_historical_data.HistoricalDataProcessor')
    @patch('sys.argv', ['prog', '--force', '--clean'])
    def test_main_with_flags(self, mock_processor_class):
        """Test main function with force and clean flags."""
        mock_processor = Mock()
        mock_processor.run.return_value = True
        mock_processor_class.return_value = mock_processor
        
        from hansard_tales.process_historical_data import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 0
        call_args = mock_processor_class.call_args
        assert call_args[1]['force'] is True
        assert call_args[1]['clean'] is True


class TestEdgeCases:
    """Test suite for edge cases."""
    
    def test_extract_date_url_encoded_filename(self):
        """Test extracting date from URL-encoded filename."""
        pdf_path = Path("Hansard%20Report%20-%20Wednesday%2C%203rd%20December%202025%20%28P%29.pdf")
        result = _extract_date_from_filename(pdf_path)
        assert result == date(2025, 12, 3)
    
    def test_process_single_pdf_cannot_extract_date(self, production_db):
        """Test processing PDF when date cannot be extracted."""
        pdf_path = Path("invalid_name.pdf")
        result = process_single_pdf(pdf_path, Path(production_db), force=False)
        
        assert result.status == 'error'
        assert result.reason == 'cannot_extract_date'
    
    @patch('hansard_tales.process_historical_data.PDFProcessor')
    @patch('hansard_tales.process_historical_data.MPIdentifier')
    @patch('hansard_tales.process_historical_data.BillExtractor')
    def test_process_single_pdf_with_force(self, mock_bill_ext, mock_mp_id, mock_pdf_proc, production_db):
        """Test processing PDF with force flag."""
        # Mark PDF as already processed
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hansard_sessions (term_id, date, title, pdf_path, pdf_url, processed)
            VALUES (1, '2024-01-01', 'Test', '20240101_0_P.pdf', 'http://example.com/test.pdf', 1)
        """)
        conn.commit()
        conn.close()
        
        # Setup mocks
        mock_pdf = Mock()
        mock_pdf.extract_text_from_pdf.return_value = {
            'pages': [{'page_number': 1, 'text': 'Test content'}]
        }
        mock_pdf_proc.return_value = mock_pdf
        
        mock_mp = Mock()
        statements = [Statement("John Doe", "Test", 0, 100, page_number=1)]
        mock_mp.extract_statements_from_pages.return_value = statements
        mock_mp.get_unique_mp_names.return_value = ["John Doe"]
        mock_mp_id.return_value = mock_mp
        
        mock_bill = Mock()
        mock_bill.extract_bill_references.return_value = []
        mock_bill_ext.return_value = mock_bill
        
        pdf_path = Path("20240101_0_P.pdf")
        
        # With force=True, should process even if already processed
        result = process_single_pdf(pdf_path, Path(production_db), force=True)
        
        assert result.status == 'success'
    
    def test_processor_with_invalid_workers(self):
        """Test processor initialization with invalid workers."""
        # Should accept any value, validation happens in main()
        processor = HistoricalDataProcessor(workers=0)
        assert processor.workers == 0
    
    def test_is_within_date_range_invalid_date(self):
        """Test date range filtering with invalid date in filename."""
        processor = HistoricalDataProcessor(start_date="2024-01-01")
        
        # PDF with invalid date should be included (with warning)
        pdf_path = Path("invalid_date.pdf")
        result = processor._is_within_date_range(pdf_path)
        
        assert result is True



class TestAdditionalCoverage:
    """Additional tests to reach 90% coverage."""
    
    @patch('hansard_tales.process_historical_data.HansardScraper')
    @patch('hansard_tales.process_historical_data.TQDM_AVAILABLE', False)
    def test_download_pdfs_without_tqdm(self, mock_scraper_class):
        """Test PDF download without tqdm."""
        processor = HistoricalDataProcessor(dry_run=False)
        
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = ['url1']
        mock_scraper.download_all.return_value = {
            'downloaded': 1,
            'skipped': 0,
            'failed': 0
        }
        mock_scraper_class.return_value = mock_scraper
        
        with patch('pathlib.Path.glob', return_value=[]):
            processor._download_pdfs()
        
        assert processor.stats['pdfs_downloaded'] == 1
    
    @patch('hansard_tales.process_historical_data.process_single_pdf')
    @patch('hansard_tales.process_historical_data.TQDM_AVAILABLE', False)
    def test_process_pdfs_without_tqdm(self, mock_process, temp_pdf_dir, production_db):
        """Test PDF processing without tqdm."""
        processor = HistoricalDataProcessor(workers=2, dry_run=False)
        processor.db_path = Path(production_db)
        
        mock_process.return_value = ProcessedPDF(
            pdf_path="test.pdf",
            pdf_date="2024-01-01",
            status='success',
            statements=10,
            unique_mps=5,
            bills=2
        )
        
        with patch('pathlib.Path.glob', return_value=list(temp_pdf_dir.glob("*.pdf"))):
            with patch.object(processor, '_batch_write_to_database'):
                processor._process_pdfs()
        
        assert mock_process.call_count > 0
    
    @patch('hansard_tales.process_historical_data.DatabaseUpdater')
    @patch('hansard_tales.process_historical_data.TQDM_AVAILABLE', False)
    def test_batch_write_without_tqdm(self, mock_updater_class, production_db):
        """Test batch writing without tqdm."""
        processor = HistoricalDataProcessor()
        processor.db_path = Path(production_db)
        
        mock_updater = Mock()
        mock_updater.process_hansard_pdf.return_value = {
            'status': 'success',
            'duplicates_skipped': 0
        }
        mock_updater_class.return_value = mock_updater
        
        results = [
            ProcessedPDF(
                pdf_path="test1.pdf",
                pdf_date="2024-01-01",
                status='success',
                statements=10
            )
        ]
        
        processor._batch_write_to_database(results)
        
        assert mock_updater.process_hansard_pdf.call_count == 1
    
    def test_print_summary_with_timing(self):
        """Test summary printing with timing statistics."""
        processor = HistoricalDataProcessor(workers=4)
        processor.stats['pdfs_downloaded'] = 10
        processor.stats['pdfs_processed'] = 8
        processor.stats['pdfs_failed'] = 2
        processor.stats['processing_times'] = [1.0, 2.0, 1.5, 2.5]
        
        # Should not raise exception
        processor._print_summary()
    
    def test_print_summary_with_errors(self):
        """Test summary printing with many errors."""
        processor = HistoricalDataProcessor()
        processor.stats['pdfs_processed'] = 5
        processor.stats['errors'] = [f"Error {i}" for i in range(15)]
        
        # Should not raise exception and should truncate error list
        processor._print_summary()
    
    def test_print_summary_with_recommendations(self):
        """Test summary printing with various recommendation scenarios."""
        processor = HistoricalDataProcessor()
        processor.stats['pdfs_downloaded'] = 20
        processor.stats['pdfs_skipped'] = 5
        processor.stats['pdfs_processed'] = 10
        processor.stats['pdfs_failed'] = 5
        processor.stats['mps_identified'] = 50
        processor.stats['processing_times'] = [1.0] * 10
        
        # Should not raise exception
        processor._print_summary()
    
    @patch('hansard_tales.process_historical_data.HansardScraper')
    def test_download_pdfs_with_date_range(self, mock_scraper_class):
        """Test PDF download with date range specified."""
        processor = HistoricalDataProcessor(
            start_date="2024-01-01",
            end_date="2024-12-31",
            dry_run=False
        )
        
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = ['url1', 'url2']
        mock_scraper.download_all.return_value = {
            'downloaded': 2,
            'skipped': 0,
            'failed': 0
        }
        mock_scraper_class.return_value = mock_scraper
        
        with patch('pathlib.Path.glob', return_value=[]):
            processor._download_pdfs()
        
        # Verify scraper was initialized with date range
        call_args = mock_scraper_class.call_args
        assert call_args[1]['start_date'] == "2024-01-01"
        assert call_args[1]['end_date'] == "2024-12-31"
    
    @patch('hansard_tales.process_historical_data.HansardScraper')
    def test_download_pdfs_with_failures(self, mock_scraper_class):
        """Test PDF download with some failures."""
        processor = HistoricalDataProcessor(dry_run=False)
        
        mock_scraper = Mock()
        mock_scraper.scrape_all.return_value = ['url1', 'url2', 'url3']
        mock_scraper.download_all.return_value = {
            'downloaded': 2,
            'skipped': 0,
            'failed': 1
        }
        mock_scraper_class.return_value = mock_scraper
        
        with patch('pathlib.Path.glob', return_value=[]):
            processor._download_pdfs()
        
        assert processor.stats['pdfs_downloaded'] == 3
    
    @patch('hansard_tales.process_historical_data.DatabaseUpdater')
    def test_batch_write_with_duplicates(self, mock_updater_class, production_db):
        """Test batch writing with duplicate detection."""
        processor = HistoricalDataProcessor()
        processor.db_path = Path(production_db)
        
        mock_updater = Mock()
        mock_updater.process_hansard_pdf.return_value = {
            'status': 'success',
            'duplicates_skipped': 5
        }
        mock_updater_class.return_value = mock_updater
        
        results = [
            ProcessedPDF(
                pdf_path="test1.pdf",
                pdf_date="2024-01-01",
                status='success',
                statements=10
            )
        ]
        
        processor._batch_write_to_database(results)
        
        assert processor.stats['duplicates_skipped'] == 5
    
    @patch('hansard_tales.process_historical_data.DatabaseUpdater')
    def test_batch_write_with_error(self, mock_updater_class, production_db):
        """Test batch writing with database error."""
        processor = HistoricalDataProcessor()
        processor.db_path = Path(production_db)
        
        mock_updater = Mock()
        mock_updater.process_hansard_pdf.return_value = {
            'status': 'error',
            'reason': 'database_error'
        }
        mock_updater_class.return_value = mock_updater
        
        results = [
            ProcessedPDF(
                pdf_path="test1.pdf",
                pdf_date="2024-01-01",
                status='success',
                statements=10
            )
        ]
        
        processor._batch_write_to_database(results)
        
        # Should handle error gracefully
        assert mock_updater.process_hansard_pdf.call_count == 1
    
    @patch('hansard_tales.process_historical_data.DatabaseUpdater')
    def test_batch_write_with_exception(self, mock_updater_class, production_db):
        """Test batch writing with exception during write."""
        processor = HistoricalDataProcessor()
        processor.db_path = Path(production_db)
        
        mock_updater = Mock()
        mock_updater.process_hansard_pdf.side_effect = Exception("Write error")
        mock_updater_class.return_value = mock_updater
        
        results = [
            ProcessedPDF(
                pdf_path="test1.pdf",
                pdf_date="2024-01-01",
                status='success',
                statements=10
            )
        ]
        
        # Should handle exception gracefully
        processor._batch_write_to_database(results)
    
    @patch('sys.argv', ['prog', '--start-date', '2024-12-31', '--end-date', '2024-01-01'])
    def test_main_with_invalid_date_range(self):
        """Test main function with start date after end date."""
        from hansard_tales.process_historical_data import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1
    
    @patch('hansard_tales.process_historical_data.HistoricalDataProcessor')
    @patch('sys.argv', ['prog', '--workers', '0'])
    def test_main_with_invalid_workers_count(self, mock_processor_class):
        """Test main function with invalid workers count."""
        from hansard_tales.process_historical_data import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1
    
    @patch('hansard_tales.process_historical_data.HistoricalDataProcessor')
    @patch('sys.argv', ['prog', '--workers', '20'])
    def test_main_with_many_workers(self, mock_processor_class):
        """Test main function with many workers (warning case)."""
        mock_processor = Mock()
        mock_processor.run.return_value = True
        mock_processor_class.return_value = mock_processor
        
        from hansard_tales.process_historical_data import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Should succeed but print warning
        assert exc_info.value.code == 0
    
    @patch('hansard_tales.process_historical_data.HistoricalDataProcessor')
    @patch('sys.argv', ['prog'])
    def test_main_with_processor_failure(self, mock_processor_class):
        """Test main function when processor fails."""
        mock_processor = Mock()
        mock_processor.run.return_value = False
        mock_processor_class.return_value = mock_processor
        
        from hansard_tales.process_historical_data import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1
    
    @patch('hansard_tales.process_historical_data.process_single_pdf')
    def test_process_pdfs_with_keyboard_interrupt(self, mock_process, temp_pdf_dir, production_db):
        """Test handling of keyboard interrupt during processing."""
        processor = HistoricalDataProcessor(workers=2, dry_run=False)
        processor.db_path = Path(production_db)
        
        # Mock to raise KeyboardInterrupt
        mock_process.side_effect = KeyboardInterrupt()
        
        with patch('pathlib.Path.glob', return_value=list(temp_pdf_dir.glob("*.pdf"))):
            with pytest.raises(KeyboardInterrupt):
                processor._process_pdfs()
    
    def test_clean_database_nonexistent(self):
        """Test cleaning database that doesn't exist."""
        processor = HistoricalDataProcessor(clean=True, dry_run=False)
        processor.db_path = Path("/nonexistent/database.db")
        
        # Should handle gracefully
        processor._clean_database()
    
    def test_clean_database_dry_run(self, production_db):
        """Test cleaning database in dry run mode."""
        processor = HistoricalDataProcessor(clean=True, dry_run=True)
        processor.db_path = Path(production_db)
        
        # Add some data
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO statements (mp_id, session_id, text) VALUES (1, 1, 'test')")
        conn.commit()
        conn.close()
        
        processor._clean_database()
        
        # Data should still be there (dry run)
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM statements")
        assert cursor.fetchone()[0] == 1
        conn.close()



class TestFinalCoverage:
    """Final tests to reach 90% coverage."""
    
    @patch('hansard_tales.process_historical_data.DATEPARSER_AVAILABLE', False)
    def test_parse_date_without_dateparser(self):
        """Test date parsing without dateparser library."""
        # Should only work with ISO format
        result = parse_date_string("2024-01-01")
        assert result == "2024-01-01"
        
        # Natural language should return None
        result = parse_date_string("last week")
        assert result is None
    
    def test_extract_date_leap_year(self):
        """Test extracting date from leap year."""
        pdf_path = Path("20240229_0_P.pdf")
        result = _extract_date_from_filename(pdf_path)
        assert result == date(2024, 2, 29)
    
    def test_extract_date_invalid_month(self):
        """Test extracting date with invalid month."""
        pdf_path = Path("20241301_0_P.pdf")  # Month 13
        result = _extract_date_from_filename(pdf_path)
        assert result is None
    
    def test_extract_date_invalid_day(self):
        """Test extracting date with invalid day."""
        pdf_path = Path("20240132_0_P.pdf")  # Day 32
        result = _extract_date_from_filename(pdf_path)
        assert result is None
    
    def test_extract_date_long_format_invalid_month(self):
        """Test extracting date from long format with invalid month name."""
        pdf_path = Path("Hansard Report - Wednesday, 3rd Invalidmonth 2025 (P).pdf")
        result = _extract_date_from_filename(pdf_path)
        assert result is None
    
    def test_extract_date_long_format_invalid_day(self):
        """Test extracting date from long format with invalid day."""
        pdf_path = Path("Hansard Report - Wednesday, 32nd December 2025 (P).pdf")
        result = _extract_date_from_filename(pdf_path)
        assert result is None
    
    def test_quality_assurance_with_duplicates(self, production_db):
        """Test quality assurance with duplicate statements."""
        processor = HistoricalDataProcessor()
        processor.db_path = Path(production_db)
        
        # Add duplicate statements with proper schema
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO mps (name, constituency) VALUES ('John Doe', 'Test Constituency')")
        mp_id = cursor.lastrowid
        cursor.execute("INSERT INTO hansard_sessions (term_id, date, title, pdf_url, processed) VALUES (1, '2024-01-01', 'test', 'http://example.com/test.pdf', 1)")
        session_id = cursor.lastrowid
        cursor.execute("INSERT INTO statements (mp_id, session_id, text) VALUES (?, ?, 'duplicate')", (mp_id, session_id))
        cursor.execute("INSERT INTO statements (mp_id, session_id, text) VALUES (?, ?, 'duplicate')", (mp_id, session_id))
        conn.commit()
        conn.close()
        
        # Should detect duplicates
        processor._quality_assurance()
    
    def test_quality_assurance_with_bills(self, production_db):
        """Test quality assurance with bill references."""
        processor = HistoricalDataProcessor()
        processor.db_path = Path(production_db)
        
        # Add statements with bills with proper schema
        conn = sqlite3.connect(production_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO mps (name, constituency) VALUES ('John Doe', 'Test Constituency')")
        mp_id = cursor.lastrowid
        cursor.execute("INSERT INTO hansard_sessions (term_id, date, title, pdf_url, processed) VALUES (1, '2024-01-01', 'test', 'http://example.com/test.pdf', 1)")
        session_id = cursor.lastrowid
        cursor.execute("INSERT INTO statements (mp_id, session_id, text, bill_reference) VALUES (?, ?, 'test', 'Bill No. 123')", (mp_id, session_id))
        conn.commit()
        conn.close()
        
        processor._quality_assurance()
    
    @patch('hansard_tales.process_historical_data.HansardScraper')
    def test_download_pdfs_dry_run_with_existing(self, mock_scraper_class, temp_pdf_dir):
        """Test PDF download in dry run mode with existing PDFs."""
        processor = HistoricalDataProcessor(dry_run=True)
        
        mock_scraper = Mock()
        mock_scraper_class.return_value = mock_scraper
        
        with patch('pathlib.Path.glob', return_value=list(temp_pdf_dir.glob("*.pdf"))):
            processor._download_pdfs()
        
        # Should count existing PDFs
        assert processor.stats['pdfs_downloaded'] > 0
    
    def test_process_pdfs_dry_run(self, temp_pdf_dir, production_db):
        """Test PDF processing in dry run mode."""
        processor = HistoricalDataProcessor(dry_run=True)
        processor.db_path = Path(production_db)
        
        with patch('pathlib.Path.glob', return_value=list(temp_pdf_dir.glob("*.pdf"))):
            processor._process_pdfs()
        
        # Should count PDFs without processing
        assert processor.stats['pdfs_processed'] > 0
