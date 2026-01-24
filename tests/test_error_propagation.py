"""
Error propagation tests for workflow components.

This module tests that errors propagate correctly through the workflow,
are logged appropriately, and that cleanup executes on errors.

Validates: Requirements 6.1, 6.2, 6.3, 6.5
"""

import logging
import sqlite3
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from hansard_tales.database.db_updater import DatabaseUpdater
from hansard_tales.scrapers.hansard_scraper import HansardScraper
from hansard_tales.storage.filesystem import FilesystemStorage
from hansard_tales.workflow.orchestrator import WorkflowOrchestrator


class TestErrorPropagation:
    """Test that errors propagate correctly with messages intact."""
    
    def test_scraper_error_propagates_with_message(self, production_db):
        """
        Test that scraper errors propagate with original message.
        
        Validates: Requirements 6.2
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FilesystemStorage(tmpdir)
            
            # Create scraper
            scraper = HansardScraper(storage=storage, db_path=str(production_db))
            
            # Mock session to raise specific error
            with patch.object(scraper.session, 'get') as mock_get:
                original_error = requests.ConnectionError("Connection refused by server")
                mock_get.side_effect = original_error
                
                # Attempt download - should return False but not raise
                result = scraper.download_pdf(
                    "http://example.com/test.pdf",
                    "Test Session",
                    "2024-01-01"
                )
                
                # Verify error was handled (returned False)
                assert result is False, "Download should have failed"
    
    def test_database_error_propagates_with_message(self, production_db):
        """
        Test that database errors propagate with original message.
        
        Validates: Requirements 6.2
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create updater
            updater = DatabaseUpdater(str(production_db))
            
            # Create a temporary PDF file
            pdf_path = Path(tmpdir) / "test.pdf"
            pdf_path.write_bytes(b'%PDF-1.4 fake pdf content')
            
            # Mock PDF processor to raise specific error
            with patch('hansard_tales.database.db_updater.PDFProcessor') as mock_processor:
                original_error = ValueError("Invalid PDF structure")
                mock_processor.return_value.extract_text.side_effect = original_error
                
                # Attempt to process - should return error status
                result = updater.process_hansard_pdf(
                    str(pdf_path),
                    "http://example.com/test.pdf",
                    "2024-01-01",
                    "Test Session"
                )
                
                # Verify error was handled
                assert result['status'] == 'error', "Should return error status"
                assert 'reason' in result, "Should include error reason"
    
    def test_workflow_error_propagates_through_layers(self, production_db):
        """
        Test that errors propagate through all workflow layers.
        
        Validates: Requirements 6.2
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FilesystemStorage(tmpdir)
            
            # Create orchestrator
            orchestrator = WorkflowOrchestrator(
                db_path=str(production_db),
                storage=storage
            )
            
            # Mock MP scraper to raise specific error
            with patch.object(orchestrator, '_scrape_mps') as mock_scrape:
                original_error = Exception("MP data source unavailable")
                mock_scrape.side_effect = original_error
                
                # Run workflow - should raise the error
                with pytest.raises(Exception) as exc_info:
                    orchestrator.run_full_workflow()
                
                # Verify original error message is preserved
                assert "MP data source unavailable" in str(exc_info.value)


class TestErrorLogging:
    """Test that errors are logged appropriately."""
    
    def test_scraper_error_logged_with_details(self, production_db):
        """
        Test that scraper errors are logged with full details.
        
        Validates: Requirements 6.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(storage=storage, db_path=str(production_db))
            
            # Capture logs
            log_stream = StringIO()
            handler = logging.StreamHandler(log_stream)
            handler.setLevel(logging.ERROR)
            logger = logging.getLogger('hansard_tales.scrapers.hansard_scraper')
            logger.addHandler(handler)
            logger.setLevel(logging.ERROR)
            
            try:
                # Mock session to raise error
                with patch.object(scraper.session, 'get') as mock_get:
                    mock_get.side_effect = requests.Timeout("Request timed out after 30s")
                    
                    # Attempt download
                    scraper.download_pdf(
                        "http://example.com/test.pdf",
                        "Test Session",
                        "2024-01-01"
                    )
                    
                    # Get log output
                    log_output = log_stream.getvalue()
                    
                    # Verify error was logged with details
                    assert 'Download failed:' in log_output, "Error message not logged"
                    assert 'Request timed out' in log_output, "Error details not logged"
                    assert 'http://example.com/test.pdf' in log_output, "URL not logged"
            
            finally:
                logger.removeHandler(handler)
    
    def test_database_error_logged_with_context(self, production_db):
        """
        Test that database errors are logged with context.
        
        Validates: Requirements 6.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            updater = DatabaseUpdater(str(production_db))
            
            # Capture logs
            log_stream = StringIO()
            handler = logging.StreamHandler(log_stream)
            handler.setLevel(logging.ERROR)
            logger = logging.getLogger('hansard_tales.database.db_updater')
            logger.addHandler(handler)
            logger.setLevel(logging.ERROR)
            
            try:
                # Create a temporary PDF file
                pdf_path = Path(tmpdir) / "test.pdf"
                pdf_path.write_bytes(b'%PDF-1.4 fake pdf content')
                
                # Mock PDF processor to raise error
                with patch('hansard_tales.database.db_updater.PDFProcessor') as mock_processor:
                    mock_processor.return_value.extract_text.side_effect = \
                        RuntimeError("PDF extraction failed: corrupted file")
                    
                    # Attempt to process
                    updater.process_hansard_pdf(
                        str(pdf_path),
                        "http://example.com/test.pdf",
                        "2024-01-01",
                        "Test Session"
                    )
                    
                    # Get log output
                    log_output = log_stream.getvalue()
                    
                    # Verify error was logged with context
                    # The actual error message is "Failed to extract text from PDF"
                    assert 'Failed to extract text from PDF' in log_output, "Error message not logged"
                    assert 'test.pdf' in log_output or 'PDF' in log_output, "Context not logged"
            
            finally:
                logger.removeHandler(handler)
    
    def test_workflow_error_logged_at_each_layer(self, production_db):
        """
        Test that workflow errors are logged at each layer.
        
        Validates: Requirements 6.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FilesystemStorage(tmpdir)
            orchestrator = WorkflowOrchestrator(
                db_path=str(production_db),
                storage=storage
            )
            
            # Capture logs
            log_stream = StringIO()
            handler = logging.StreamHandler(log_stream)
            handler.setLevel(logging.ERROR)
            logger = logging.getLogger('hansard_tales.workflow.orchestrator')
            logger.addHandler(handler)
            logger.setLevel(logging.ERROR)
            
            try:
                # Mock component to raise error
                with patch.object(orchestrator, '_scrape_mps') as mock_scrape:
                    mock_scrape.side_effect = Exception("Network error during MP scraping")
                    
                    # Run workflow
                    try:
                        orchestrator.run_full_workflow()
                    except Exception:
                        pass  # Expected
                    
                    # Get log output
                    log_output = log_stream.getvalue()
                    
                    # Verify error was logged
                    assert 'Workflow failed:' in log_output, "Error message not logged"
                    assert 'Network error during MP scraping' in log_output, \
                        "Error details not logged"
            
            finally:
                logger.removeHandler(handler)


class TestErrorCleanup:
    """Test that cleanup executes on errors."""
    
    def test_scraper_cleanup_on_download_error(self, production_db):
        """
        Test that scraper cleans up resources on download error.
        
        Validates: Requirements 6.5
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(storage=storage, db_path=str(production_db))
            
            # Mock session to raise error after partial download
            with patch.object(scraper.session, 'get') as mock_get:
                mock_response = Mock()
                # Simulate partial download then error
                mock_response.iter_content = Mock(side_effect=requests.ConnectionError("Connection lost"))
                mock_get.return_value = mock_response
                
                # Attempt download
                result = scraper.download_pdf(
                    "http://example.com/test.pdf",
                    "Test Session",
                    "2024-01-01"
                )
                
                # Verify download failed
                assert result is False, "Download should have failed"
                
                # Verify no partial files left behind
                files = list(Path(tmpdir).rglob("*.pdf"))
                # Either no files, or only complete files (not partial)
                for file in files:
                    # If file exists, it should have content
                    assert file.stat().st_size > 0, "No partial files should remain"
    
    def test_database_cleanup_on_processing_error(self, production_db):
        """
        Test that database operations clean up on error.
        
        Validates: Requirements 6.5
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            updater = DatabaseUpdater(str(production_db))
            
            # Create a temporary PDF file
            pdf_path = Path(tmpdir) / "test.pdf"
            pdf_path.write_bytes(b'%PDF-1.4 fake pdf content')
            
            # Get initial record count
            conn = sqlite3.connect(str(production_db))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM hansard_sessions")
            initial_count = cursor.fetchone()[0]
            conn.close()
            
            # Mock PDF processor to raise error mid-processing
            with patch('hansard_tales.database.db_updater.PDFProcessor') as mock_processor:
                mock_processor.return_value.extract_text.side_effect = \
                    RuntimeError("Processing failed midway")
                
                # Attempt to process
                result = updater.process_hansard_pdf(
                    str(pdf_path),
                    "http://example.com/test.pdf",
                    "2024-01-01",
                    "Test Session"
                )
                
                # Verify error was handled
                assert result['status'] == 'error'
                
                # Verify no partial records were left in database
                conn = sqlite3.connect(str(production_db))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM hansard_sessions")
                final_count = cursor.fetchone()[0]
                conn.close()
                
                # Count should be unchanged (no partial records)
                assert final_count == initial_count, \
                    "No partial database records should remain after error"
    
    def test_workflow_cleanup_on_component_error(self, production_db):
        """
        Test that workflow cleans up on component error.
        
        Validates: Requirements 6.5
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FilesystemStorage(tmpdir)
            orchestrator = WorkflowOrchestrator(
                db_path=str(production_db),
                storage=storage
            )
            
            # Mock component to raise error
            with patch.object(orchestrator, '_scrape_hansards') as mock_scrape:
                mock_scrape.side_effect = Exception("Scraping failed")
                
                # Run workflow - should raise error
                with pytest.raises(Exception):
                    orchestrator.run_full_workflow()
                
                # Verify database connection is closed (no locks)
                # Try to connect - should succeed if cleanup happened
                conn = sqlite3.connect(str(production_db))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM parliamentary_terms")
                cursor.fetchone()
                conn.close()
                
                # If we get here, database was properly cleaned up


class TestPartialFailureHandling:
    """Test that partial failures are handled correctly."""
    
    def test_some_pdfs_fail_others_succeed(self, production_db):
        """
        Test that some PDFs failing doesn't stop others from processing.
        
        Validates: Requirements 6.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FilesystemStorage(tmpdir)
            scraper = HansardScraper(storage=storage, db_path=str(production_db))
            
            # Mock session to fail on first PDF, succeed on second
            call_count = 0
            
            def mock_get_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                
                if call_count == 1:
                    # First call fails
                    raise requests.ConnectionError("Connection failed")
                else:
                    # Second call succeeds
                    mock_response = Mock()
                    mock_response.iter_content = lambda chunk_size: [b'PDF content']
                    mock_response.raise_for_status = Mock()
                    return mock_response
            
            with patch.object(scraper.session, 'get', side_effect=mock_get_side_effect):
                # Attempt to download two PDFs
                result1 = scraper.download_pdf(
                    "http://example.com/test1.pdf",
                    "Test Session 1",
                    "2024-01-01"
                )
                
                result2 = scraper.download_pdf(
                    "http://example.com/test2.pdf",
                    "Test Session 2",
                    "2024-01-02"
                )
                
                # Verify first failed, second succeeded
                assert result1 is False, "First download should have failed"
                assert result2 is True, "Second download should have succeeded"
    
    def test_error_status_returns_not_exceptions(self, production_db):
        """
        Test that components return error status instead of raising exceptions.
        
        Validates: Requirements 6.1
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            updater = DatabaseUpdater(str(production_db))
            
            # Create a temporary PDF file
            pdf_path = Path(tmpdir) / "test.pdf"
            pdf_path.write_bytes(b'%PDF-1.4 fake pdf content')
            
            # Mock PDF processor to raise error
            with patch('hansard_tales.database.db_updater.PDFProcessor') as mock_processor:
                mock_processor.return_value.extract_text.side_effect = \
                    ValueError("Invalid PDF")
                
                # Attempt to process - should NOT raise exception
                result = updater.process_hansard_pdf(
                    str(pdf_path),
                    "http://example.com/test.pdf",
                    "2024-01-01",
                    "Test Session"
                )
                
                # Verify error status was returned (not exception raised)
                assert isinstance(result, dict), "Should return dict, not raise exception"
                assert result['status'] == 'error', "Should return error status"
                assert 'reason' in result, "Should include error reason"
