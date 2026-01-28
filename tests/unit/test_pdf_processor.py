"""Unit tests for PDF processor module."""

import pytest
from pathlib import Path
import fitz  # PyMuPDF
from hansard_tales.processors.pdf_processor import (
    PDFProcessor,
    HansardProcessor,
    VotesProcessor,
    ProcessedPDF,
)


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a simple test PDF file."""
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "Test Document Title", fontsize=16)
    page.insert_text((50, 100), "First paragraph.", fontsize=12)
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def multi_page_pdf(tmp_path):
    """Create a multi-page test PDF."""
    pdf_path = tmp_path / "multipage.pdf"
    doc = fitz.open()
    for i in range(1, 4):
        page = doc.new_page()
        page.insert_text((50, 50), f"Page {i} Content", fontsize=14)
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


class TestPDFProcessor:
    """Test suite for PDFProcessor class."""
    
    def test_init_success(self):
        """Test that PDFProcessor can be instantiated."""
        processor = PDFProcessor()
        assert processor is not None
    
    def test_process_pdf_success(self, sample_pdf):
        """Test successful PDF processing."""
        processor = PDFProcessor()
        result = processor.process(sample_pdf)
        
        assert isinstance(result, ProcessedPDF)
        assert result.file_path == sample_pdf
        assert result.page_count == 1
        assert len(result.file_hash) == 64
        assert len(result.text_blocks) > 0
    
    def test_process_nonexistent_file(self):
        """Test processing nonexistent PDF file."""
        processor = PDFProcessor()
        with pytest.raises(FileNotFoundError):
            processor.process(Path("nonexistent.pdf"))
    
    def test_compute_hash_consistency(self, sample_pdf):
        """Test that same file produces same hash."""
        processor = PDFProcessor()
        hash1 = processor._compute_hash(sample_pdf)
        hash2 = processor._compute_hash(sample_pdf)
        assert hash1 == hash2
        assert len(hash1) == 64
    
    def test_extract_text_with_source_tracking(self, sample_pdf):
        """Test text extraction with page and line numbers."""
        processor = PDFProcessor()
        text_blocks = processor._extract_text(sample_pdf)
        
        assert len(text_blocks) > 0
        first_block = text_blocks[0]
        assert first_block.text
        assert first_block.page_number == 1
        assert first_block.line_number is not None
        assert first_block.bbox is not None
    
    def test_extract_text_multiple_pages(self, multi_page_pdf):
        """Test text extraction from multiple pages."""
        processor = PDFProcessor()
        text_blocks = processor._extract_text(multi_page_pdf)
        
        page_numbers = {block.page_number for block in text_blocks}
        assert 1 in page_numbers
        assert 2 in page_numbers
        assert 3 in page_numbers
    
    def test_extract_metadata(self, sample_pdf):
        """Test metadata extraction from PDF."""
        processor = PDFProcessor()
        metadata = processor._extract_metadata(sample_pdf)
        
        assert isinstance(metadata, dict)
        assert 'title' in metadata
        assert 'author' in metadata
    
    def test_extract_text_by_page(self, multi_page_pdf):
        """Test extracting text from specific page."""
        processor = PDFProcessor()
        text_page1 = processor.extract_text_by_page(multi_page_pdf, 1)
        text_page2 = processor.extract_text_by_page(multi_page_pdf, 2)
        
        assert "Page 1" in text_page1
        assert "Page 2" in text_page2
    
    def test_extract_text_by_page_invalid_number(self, sample_pdf):
        """Test extracting text with invalid page number."""
        processor = PDFProcessor()
        
        with pytest.raises(ValueError, match="Invalid page number"):
            processor.extract_text_by_page(sample_pdf, 5)
    
    def test_search_text(self, sample_pdf):
        """Test searching for text in PDF."""
        processor = PDFProcessor()
        results = processor.search_text(sample_pdf, "Test Document")
        
        assert len(results) > 0
        assert results[0].page_number == 1


class TestHansardProcessor:
    """Test suite for HansardProcessor class."""
    
    def test_process_hansard(self, sample_pdf):
        """Test Hansard-specific processing."""
        processor = HansardProcessor()
        result = processor.process_hansard(sample_pdf)
        
        assert isinstance(result, ProcessedPDF)
        assert result.file_path == sample_pdf


class TestVotesProcessor:
    """Test suite for VotesProcessor class."""
    
    def test_process_votes(self, sample_pdf):
        """Test Votes-specific processing."""
        processor = VotesProcessor()
        result = processor.process_votes(sample_pdf)
        
        assert isinstance(result, ProcessedPDF)
        assert result.file_path == sample_pdf
