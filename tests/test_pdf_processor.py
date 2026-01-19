"""
Tests for PDF text extraction processor.

This module tests the PDF processing functionality including
text extraction, page handling, and error handling.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Import the processor module
from hansard_tales.processors.pdf_processor import PDFProcessor


@pytest.fixture
def processor():
    """Create a PDF processor instance for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield PDFProcessor(output_dir=tmpdir)


@pytest.fixture
def mock_pdf_data():
    """Create mock PDF data for testing."""
    return {
        'metadata': {
            'filename': 'test.pdf',
            'num_pages': 3,
            'metadata': {'Title': 'Test Hansard'}
        },
        'pages': [
            {
                'page_number': 1,
                'text': 'Page 1 content',
                'char_count': 14
            },
            {
                'page_number': 2,
                'text': 'Page 2 content',
                'char_count': 14
            },
            {
                'page_number': 3,
                'text': 'Page 3 content',
                'char_count': 14
            }
        ],
        'statistics': {
            'total_pages': 3,
            'pages_with_text': 3,
            'pages_without_text': 0,
            'total_characters': 42,
            'avg_chars_per_page': 14.0
        }
    }


class TestPDFProcessor:
    """Test suite for PDF processor initialization."""
    
    def test_processor_initialization(self):
        """Test processor initializes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = PDFProcessor(output_dir=tmpdir)
            assert processor.output_dir == Path(tmpdir)
    
    def test_processor_no_output_dir(self):
        """Test processor can be initialized without output directory."""
        processor = PDFProcessor()
        assert processor.output_dir is None
    
    def test_output_directory_created(self):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / 'output' / 'nested'
            processor = PDFProcessor(output_dir=str(output_dir))
            assert output_dir.exists()


class TestTextExtraction:
    """Test suite for text extraction from PDFs."""
    
    @patch('hansard_tales.processors.pdf_processor.pdfplumber.open')
    def test_extract_text_success(self, mock_pdfplumber, processor):
        """Test successful text extraction from PDF."""
        # Mock PDF pages
        mock_page1 = Mock()
        mock_page1.extract_text = Mock(return_value='Page 1 text')
        
        mock_page2 = Mock()
        mock_page2.extract_text = Mock(return_value='Page 2 text')
        
        # Mock PDF object
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.metadata = {'Title': 'Test'}
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            # Extract text
            result = processor.extract_text_from_pdf(pdf_path)
            
            assert result is not None
            assert result['metadata']['num_pages'] == 2
            assert len(result['pages']) == 2
            assert result['pages'][0]['text'] == 'Page 1 text'
            assert result['pages'][1]['text'] == 'Page 2 text'
        finally:
            Path(pdf_path).unlink()
    
    def test_extract_text_file_not_found(self, processor):
        """Test extraction fails gracefully when file not found."""
        result = processor.extract_text_from_pdf('nonexistent.pdf')
        assert result is None
    
    @patch('hansard_tales.processors.pdf_processor.pdfplumber.open')
    def test_extract_text_empty_page(self, mock_pdfplumber, processor):
        """Test handling of pages with no text."""
        # Mock page with no text
        mock_page = Mock()
        mock_page.extract_text = Mock(return_value=None)
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {}
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = processor.extract_text_from_pdf(pdf_path)
            
            assert result is not None
            assert result['pages'][0]['text'] == ''
            assert 'warning' in result['pages'][0]
        finally:
            Path(pdf_path).unlink()
    
    @patch('hansard_tales.processors.pdf_processor.pdfplumber.open')
    def test_extract_text_page_error(self, mock_pdfplumber, processor):
        """Test handling of page extraction errors."""
        # Mock page that raises error
        mock_page = Mock()
        mock_page.extract_text = Mock(side_effect=Exception("Extraction error"))
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {}
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = processor.extract_text_from_pdf(pdf_path)
            
            assert result is not None
            assert result['pages'][0]['text'] == ''
            assert 'error' in result['pages'][0]
        finally:
            Path(pdf_path).unlink()


class TestTextRetrieval:
    """Test suite for retrieving extracted text."""
    
    def test_get_full_text(self, processor, mock_pdf_data):
        """Test getting full text from extracted data."""
        full_text = processor.get_full_text(mock_pdf_data)
        
        assert 'Page 1 content' in full_text
        assert 'Page 2 content' in full_text
        assert 'Page 3 content' in full_text
    
    def test_get_full_text_empty_data(self, processor):
        """Test getting full text with empty data."""
        full_text = processor.get_full_text({})
        assert full_text == ""
    
    def test_get_full_text_none(self, processor):
        """Test getting full text with None."""
        full_text = processor.get_full_text(None)
        assert full_text == ""
    
    def test_get_page_text(self, processor, mock_pdf_data):
        """Test getting text from specific page."""
        page_text = processor.get_page_text(mock_pdf_data, 2)
        assert page_text == 'Page 2 content'
    
    def test_get_page_text_invalid_page(self, processor, mock_pdf_data):
        """Test getting text from non-existent page."""
        page_text = processor.get_page_text(mock_pdf_data, 999)
        assert page_text is None
    
    def test_get_page_text_empty_data(self, processor):
        """Test getting page text with empty data."""
        page_text = processor.get_page_text({}, 1)
        assert page_text is None


class TestSaveExtractedText:
    """Test suite for saving extracted text."""
    
    def test_save_extracted_text(self, processor, mock_pdf_data):
        """Test saving extracted text to JSON file."""
        output_path = processor.output_dir / 'test.json'
        
        success = processor.save_extracted_text(
            mock_pdf_data,
            str(output_path)
        )
        
        assert success is True
        assert output_path.exists()
        
        # Verify content
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['metadata']['filename'] == 'test.pdf'
        assert len(saved_data['pages']) == 3
    
    def test_save_extracted_text_auto_path(self, processor, mock_pdf_data):
        """Test saving with automatic path generation."""
        success = processor.save_extracted_text(mock_pdf_data)
        
        assert success is True
        
        # Check file was created
        expected_file = processor.output_dir / 'test.json'
        assert expected_file.exists()
    
    def test_save_extracted_text_no_data(self, processor):
        """Test saving with no data."""
        success = processor.save_extracted_text(None)
        assert success is False
    
    def test_save_extracted_text_no_output_path(self):
        """Test saving without output path or directory."""
        processor = PDFProcessor()  # No output_dir
        success = processor.save_extracted_text({'test': 'data'})
        assert success is False


class TestStatistics:
    """Test suite for extraction statistics."""
    
    @patch('hansard_tales.processors.pdf_processor.pdfplumber.open')
    def test_statistics_calculation(self, mock_pdfplumber, processor):
        """Test that statistics are calculated correctly."""
        # Mock pages with varying text lengths
        mock_page1 = Mock()
        mock_page1.extract_text = Mock(return_value='A' * 100)
        
        mock_page2 = Mock()
        mock_page2.extract_text = Mock(return_value='B' * 200)
        
        mock_page3 = Mock()
        mock_page3.extract_text = Mock(return_value=None)  # Empty page
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page1, mock_page2, mock_page3]
        mock_pdf.metadata = {}
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = processor.extract_text_from_pdf(pdf_path)
            
            assert result['statistics']['total_pages'] == 3
            assert result['statistics']['pages_with_text'] == 2
            assert result['statistics']['pages_without_text'] == 1
            assert result['statistics']['total_characters'] == 300
            assert result['statistics']['avg_chars_per_page'] == 100.0
        finally:
            Path(pdf_path).unlink()


class TestProcessPDF:
    """Test suite for complete PDF processing."""
    
    @patch('hansard_tales.processors.pdf_processor.pdfplumber.open')
    def test_process_pdf_with_save(self, mock_pdfplumber, processor):
        """Test processing PDF with save enabled."""
        # Mock PDF
        mock_page = Mock()
        mock_page.extract_text = Mock(return_value='Test content')
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {}
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = processor.process_pdf(pdf_path, save_output=True)
            
            assert result is not None
            # Check that JSON file was created
            json_file = processor.output_dir / f"{Path(pdf_path).stem}.json"
            assert json_file.exists()
        finally:
            Path(pdf_path).unlink()
    
    @patch('hansard_tales.processors.pdf_processor.pdfplumber.open')
    def test_process_pdf_without_save(self, mock_pdfplumber, processor):
        """Test processing PDF without saving."""
        # Mock PDF
        mock_page = Mock()
        mock_page.extract_text = Mock(return_value='Test content')
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {}
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = processor.process_pdf(pdf_path, save_output=False)
            
            assert result is not None
            # Check that no JSON file was created
            json_file = processor.output_dir / f"{Path(pdf_path).stem}.json"
            assert not json_file.exists()
        finally:
            Path(pdf_path).unlink()


class TestProcessDirectory:
    """Test suite for batch PDF processing."""
    
    def test_process_directory_not_found(self, processor):
        """Test processing non-existent directory."""
        results = processor.process_directory('nonexistent_dir')
        assert results == []
    
    @patch('hansard_tales.processors.pdf_processor.PDFProcessor.process_pdf')
    def test_process_directory_no_pdfs(self, mock_process, processor):
        """Test processing directory with no PDF files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = processor.process_directory(tmpdir)
            assert results == []
    
    @patch('hansard_tales.processors.pdf_processor.PDFProcessor.process_pdf')
    def test_process_directory_with_pdfs(self, mock_process, processor):
        """Test processing directory with PDF files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy PDF files
            (Path(tmpdir) / 'test1.pdf').touch()
            (Path(tmpdir) / 'test2.pdf').touch()
            
            # Mock successful processing with proper structure
            mock_process.return_value = {
                'metadata': {'filename': 'test.pdf', 'num_pages': 1},
                'pages': [{'page_number': 1, 'text': 'test', 'char_count': 4}],
                'statistics': {
                    'total_pages': 1,
                    'pages_with_text': 1,
                    'pages_without_text': 0,
                    'total_characters': 4,
                    'avg_chars_per_page': 4.0
                }
            }
            
            results = processor.process_directory(tmpdir)
            
            assert len(results) == 2
            assert mock_process.call_count == 2


class TestRealPDFIntegration:
    """Integration tests using real Hansard PDF sample."""
    
    @pytest.fixture
    def sample_pdf_path(self):
        """Get path to sample PDF if it exists."""
        sample_path = Path(__file__).parent.parent / 'data' / 'pdfs' / 'Hansard_Report_2025-12-04.pdf'
        if not sample_path.exists():
            pytest.skip("Sample PDF not found")
        return str(sample_path)
    
    def test_extract_text_from_real_pdf(self, processor, sample_pdf_path):
        """Test extracting text from real Hansard PDF."""
        result = processor.extract_text_from_pdf(sample_pdf_path)
        
        assert result is not None
        assert 'metadata' in result
        assert 'pages' in result
        assert 'statistics' in result
        
        # Verify metadata
        assert result['metadata']['filename'] == 'Hansard_Report_2025-12-04.pdf'
        assert result['metadata']['num_pages'] > 0
        
        # Verify pages were extracted
        assert len(result['pages']) > 0
        assert result['pages'][0]['page_number'] == 1
        
        # Verify statistics
        stats = result['statistics']
        assert stats['total_pages'] > 0
        assert stats['total_characters'] > 0
        assert stats['pages_with_text'] > 0
    
    def test_real_pdf_contains_expected_content(self, processor, sample_pdf_path):
        """Test that real PDF contains expected Hansard content."""
        result = processor.extract_text_from_pdf(sample_pdf_path)
        
        assert result is not None
        
        # Get full text
        full_text = processor.get_full_text(result)
        
        # Verify it contains typical Hansard content markers
        # (These are common in Kenyan Hansard reports)
        assert len(full_text) > 0
        
        # Check for common Hansard elements (case-insensitive)
        full_text_lower = full_text.lower()
        
        # At least one of these should be present in a Hansard report
        hansard_markers = [
            'hansard',
            'parliament',
            'national assembly',
            'speaker',
            'hon.',
            'member'
        ]
        
        found_markers = [marker for marker in hansard_markers if marker in full_text_lower]
        assert len(found_markers) > 0, f"Expected Hansard content markers not found. Text preview: {full_text[:200]}"
    
    def test_process_real_pdf_with_save(self, sample_pdf_path):
        """Test processing real PDF with save functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = PDFProcessor(output_dir=tmpdir)
            
            result = processor.process_pdf(sample_pdf_path, save_output=True)
            
            assert result is not None
            
            # Verify JSON file was created
            json_file = Path(tmpdir) / 'Hansard_Report_2025-12-04.json'
            assert json_file.exists()
            
            # Verify JSON content
            with open(json_file, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data['metadata']['filename'] == 'Hansard_Report_2025-12-04.pdf'
            assert len(saved_data['pages']) > 0
    
    def test_get_page_text_from_real_pdf(self, processor, sample_pdf_path):
        """Test retrieving specific page text from real PDF."""
        result = processor.extract_text_from_pdf(sample_pdf_path)
        
        assert result is not None
        
        # Get first page text
        page_1_text = processor.get_page_text(result, 1)
        assert page_1_text is not None
        assert len(page_1_text) > 0
        
        # Try to get a page that doesn't exist
        invalid_page = processor.get_page_text(result, 99999)
        assert invalid_page is None
