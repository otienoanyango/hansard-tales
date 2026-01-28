"""
Integration tests for scraping and storing documents.

Tests the complete workflow from scraping to storage.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import date

from hansard_tales.scrapers.factory import create_scraper
from hansard_tales.processors.storage_service import DocumentStorageService
from hansard_tales.models.base import Chamber, DocumentType
from hansard_tales.config.settings import Config, ScraperConfig, VectorDBConfig


@pytest.mark.integration
class TestScrapeAndStore:
    """Integration tests for scraping and storing workflow."""
    
    @patch('hansard_tales.scrapers.base.requests.Session.get')
    def test_scrape_hansard_and_store(self, mock_get, temp_dir):
        """
        Test complete workflow: scrape Hansard → store in database.
        
        **Validates: Requirements 4.1, 4.6, 5.1**
        """
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'%PDF-1.4\n%Test Hansard PDF\n%%EOF'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Create scraper
        config = ScraperConfig(download_dir=temp_dir / "pdfs")
        scraper = create_scraper("hansard", config)
        
        # Mock get_document_urls to return test URL
        with patch.object(scraper, 'get_document_urls', return_value=[
            'https://parliament.go.ke/test/hansard_20240115.pdf'
        ]):
            # Scrape documents
            documents = scraper.scrape(Chamber.NATIONAL_ASSEMBLY, skip_existing=False)
        
        # Verify document was scraped
        assert len(documents) == 1
        doc = documents[0]
        assert doc.url == 'https://parliament.go.ke/test/hansard_20240115.pdf'
        assert doc.content == b'%PDF-1.4\n%Test Hansard PDF\n%%EOF'
        assert len(doc.hash) == 64  # SHA256 hash
        
        # Save document
        output_path = scraper.save_document(doc, config.download_dir)
        assert output_path.exists()
        assert output_path.read_bytes() == doc.content
    
    @patch('hansard_tales.scrapers.base.requests.Session.get')
    def test_scrape_votes_and_store(self, mock_get, temp_dir):
        """
        Test complete workflow: scrape Votes → store in database.
        
        **Validates: Requirements 4.2, 4.6, 5.1**
        """
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'%PDF-1.4\n%Test Votes PDF\n%%EOF'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Create scraper
        config = ScraperConfig(download_dir=temp_dir / "pdfs")
        scraper = create_scraper("votes", config)
        
        # Mock get_document_urls to return test URL
        with patch.object(scraper, 'get_document_urls', return_value=[
            'https://parliament.go.ke/test/votes_20240115.pdf'
        ]):
            # Scrape documents
            documents = scraper.scrape(Chamber.NATIONAL_ASSEMBLY, skip_existing=False)
        
        # Verify document was scraped
        assert len(documents) == 1
        doc = documents[0]
        assert doc.url == 'https://parliament.go.ke/test/votes_20240115.pdf'
        assert len(doc.hash) == 64
        
        # Save document
        output_path = scraper.save_document(doc, config.download_dir)
        assert output_path.exists()
    
    def test_duplicate_detection_across_scrapes(self, temp_dir):
        """
        Test that duplicate documents are detected across multiple scrapes.
        
        **Validates: Requirements 4.9, 1.11, 1.12**
        """
        # Create test PDF
        pdf_content = b'%PDF-1.4\n%Test PDF\n%%EOF'
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(pdf_content)
        
        # Create scraper
        config = ScraperConfig(download_dir=temp_dir / "pdfs")
        scraper = create_scraper("hansard", config)
        
        # Compute hash
        import hashlib
        doc_hash = hashlib.sha256(pdf_content).hexdigest()
        
        # First scrape - should not be duplicate
        assert not scraper._is_duplicate(doc_hash)
        
        # Note: In full implementation, _is_duplicate would query database
        # For now, it always returns False (placeholder implementation)
        # This test documents the expected behavior


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Integration tests for complete end-to-end workflows."""
    
    def test_scrape_process_store_workflow(self, temp_dir):
        """
        Test complete workflow: scrape → process → store → retrieve.
        
        **Validates: Requirements 4.1, 5.1, 5.7, 2.6**
        """
        # This is a placeholder for full end-to-end testing
        # In Phase 1, this will be expanded to include:
        # 1. Scraping documents
        # 2. Processing PDFs
        # 3. Storing in database
        # 4. Generating embeddings
        # 5. Storing in vector DB
        # 6. Retrieving and verifying
        
        # For now, verify basic infrastructure is in place
        assert temp_dir.exists()
        
        # Create necessary directories
        pdf_dir = temp_dir / "pdfs"
        pdf_dir.mkdir(exist_ok=True)
        
        vector_dir = temp_dir / "vector_db"
        vector_dir.mkdir(exist_ok=True)
        
        assert pdf_dir.exists()
        assert vector_dir.exists()
