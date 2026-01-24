"""
Tests for Period-of-Day extractor.

This module tests the period-of-day extraction functionality including
keyword matching, PDF content extraction, and fallback logic.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from hypothesis import given, strategies as st, settings

from hansard_tales.processors.period_extractor import PeriodOfDayExtractor


@pytest.fixture
def extractor():
    """Create a PeriodOfDayExtractor instance for testing."""
    return PeriodOfDayExtractor()


class TestExtractFromTitle:
    """Test suite for extracting period-of-day from title."""
    
    @pytest.mark.parametrize("text,expected", [
        ("Hansard Report - Afternoon Session", "A"),
        ("Morning Plenary Session", "P"),
        ("Plenary Session Report", "P"),
        ("Evening Session - Hansard", "E"),
    ])
    def test_period_extraction_from_title(self, extractor, text, expected):
        """Test period extraction for all session types."""
        result = extractor.extract_from_title(text)
        assert result == expected
    
    def test_extract_case_insensitive(self, extractor):
        """Test that keyword matching is case-insensitive."""
        assert extractor.extract_from_title("AFTERNOON SESSION") == 'A'
        assert extractor.extract_from_title("Morning Session") == 'P'
        assert extractor.extract_from_title("EVENING session") == 'E'
        assert extractor.extract_from_title("PlEnArY") == 'P'
    
    def test_extract_first_match_when_multiple_keywords(self, extractor):
        """Test that first match is returned when multiple keywords present."""
        # 'afternoon' should be found first (A comes before P in KEYWORDS dict)
        result = extractor.extract_from_title("Afternoon and Morning Session")
        assert result == 'A'
    
    def test_extract_no_keywords_found(self, extractor):
        """Test that None is returned when no keywords found."""
        result = extractor.extract_from_title("Hansard Report - Regular Session")
        assert result is None
    
    def test_extract_empty_title(self, extractor):
        """Test that None is returned for empty title."""
        assert extractor.extract_from_title("") is None
        assert extractor.extract_from_title(None) is None
    
    def test_extract_keyword_as_substring(self, extractor):
        """Test that keywords are matched as substrings."""
        # 'afternoon' should be found even in compound words
        result = extractor.extract_from_title("This afternoon's session")
        assert result == 'A'


class TestExtractFromContent:
    """Test suite for extracting period-of-day from PDF content."""
    
    @patch('hansard_tales.processors.period_extractor.pdfplumber.open')
    def test_extract_afternoon_from_content(self, mock_pdfplumber, extractor):
        """Test extracting 'A' from PDF content containing 'afternoon'."""
        # Mock PDF page
        mock_page = Mock()
        mock_page.extract_text = Mock(return_value='This is an afternoon session report.')
        
        # Mock PDF object
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = extractor.extract_from_content(pdf_path)
            assert result == 'A'
        finally:
            Path(pdf_path).unlink()
    
    @patch('hansard_tales.processors.period_extractor.pdfplumber.open')
    def test_extract_morning_from_content(self, mock_pdfplumber, extractor):
        """Test extracting 'P' from PDF content containing 'morning'."""
        mock_page = Mock()
        mock_page.extract_text = Mock(return_value='Morning session of parliament.')
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = extractor.extract_from_content(pdf_path)
            assert result == 'P'
        finally:
            Path(pdf_path).unlink()
    
    @patch('hansard_tales.processors.period_extractor.pdfplumber.open')
    def test_extract_plenary_from_content(self, mock_pdfplumber, extractor):
        """Test extracting 'P' from PDF content containing 'plenary'."""
        mock_page = Mock()
        mock_page.extract_text = Mock(return_value='Plenary session report.')
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = extractor.extract_from_content(pdf_path)
            assert result == 'P'
        finally:
            Path(pdf_path).unlink()
    
    @patch('hansard_tales.processors.period_extractor.pdfplumber.open')
    def test_extract_evening_from_content(self, mock_pdfplumber, extractor):
        """Test extracting 'E' from PDF content containing 'evening'."""
        mock_page = Mock()
        mock_page.extract_text = Mock(return_value='Evening parliamentary session.')
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = extractor.extract_from_content(pdf_path)
            assert result == 'E'
        finally:
            Path(pdf_path).unlink()
    
    @patch('hansard_tales.processors.period_extractor.pdfplumber.open')
    def test_extract_case_insensitive_content(self, mock_pdfplumber, extractor):
        """Test that keyword matching in content is case-insensitive."""
        mock_page = Mock()
        mock_page.extract_text = Mock(return_value='AFTERNOON SESSION')
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = extractor.extract_from_content(pdf_path)
            assert result == 'A'
        finally:
            Path(pdf_path).unlink()
    
    @patch('hansard_tales.processors.period_extractor.pdfplumber.open')
    def test_extract_no_keywords_in_content(self, mock_pdfplumber, extractor):
        """Test that None is returned when no keywords found in content."""
        mock_page = Mock()
        mock_page.extract_text = Mock(return_value='Regular session report.')
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = extractor.extract_from_content(pdf_path)
            assert result is None
        finally:
            Path(pdf_path).unlink()
    
    def test_extract_file_not_found(self, extractor):
        """Test that None is returned when PDF file not found."""
        result = extractor.extract_from_content('nonexistent.pdf')
        assert result is None
    
    @patch('hansard_tales.processors.period_extractor.pdfplumber.open')
    def test_extract_no_pages(self, mock_pdfplumber, extractor):
        """Test handling of PDF with no pages."""
        mock_pdf = Mock()
        mock_pdf.pages = []
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = extractor.extract_from_content(pdf_path)
            assert result is None
        finally:
            Path(pdf_path).unlink()
    
    @patch('hansard_tales.processors.period_extractor.pdfplumber.open')
    def test_extract_empty_first_page(self, mock_pdfplumber, extractor):
        """Test handling of PDF with empty first page."""
        mock_page = Mock()
        mock_page.extract_text = Mock(return_value=None)
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = extractor.extract_from_content(pdf_path)
            assert result is None
        finally:
            Path(pdf_path).unlink()
    
    @patch('hansard_tales.processors.period_extractor.pdfplumber.open')
    def test_extract_pdf_error(self, mock_pdfplumber, extractor):
        """Test handling of PDF extraction errors."""
        mock_pdfplumber.side_effect = Exception("PDF error")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = extractor.extract_from_content(pdf_path)
            assert result is None
        finally:
            Path(pdf_path).unlink()


class TestExtractWithFallback:
    """Test suite for extract() method with fallback logic."""
    
    def test_extract_from_title_first(self, extractor):
        """Test that title is checked first."""
        # Mock extract_from_content to ensure it's not called
        with patch.object(extractor, 'extract_from_content') as mock_content:
            result = extractor.extract('dummy.pdf', title='Afternoon Session')
            
            assert result == 'A'
            # extract_from_content should not be called
            mock_content.assert_not_called()
    
    @patch('hansard_tales.processors.period_extractor.pdfplumber.open')
    def test_extract_fallback_to_content(self, mock_pdfplumber, extractor):
        """Test fallback to content when title has no keywords."""
        # Mock PDF content
        mock_page = Mock()
        mock_page.extract_text = Mock(return_value='Morning session report.')
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = extractor.extract(pdf_path, title='Regular Session')
            assert result == 'P'
        finally:
            Path(pdf_path).unlink()
    
    @patch('hansard_tales.processors.period_extractor.pdfplumber.open')
    def test_extract_default_to_p(self, mock_pdfplumber, extractor):
        """Test default to 'P' when no keywords found."""
        # Mock PDF content with no keywords
        mock_page = Mock()
        mock_page.extract_text = Mock(return_value='Regular session report.')
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = extractor.extract(pdf_path, title='Regular Session')
            assert result == 'P'
        finally:
            Path(pdf_path).unlink()
    
    def test_extract_no_title_provided(self, extractor):
        """Test extraction when no title is provided."""
        with patch.object(extractor, 'extract_from_content', return_value='A'):
            result = extractor.extract('dummy.pdf')
            assert result == 'A'
    
    def test_extract_empty_title(self, extractor):
        """Test extraction with empty title."""
        with patch.object(extractor, 'extract_from_content', return_value='E'):
            result = extractor.extract('dummy.pdf', title='')
            assert result == 'E'
    
    def test_extract_file_not_found_defaults_to_p(self, extractor):
        """Test that default 'P' is returned when file not found."""
        result = extractor.extract('nonexistent.pdf', title='Regular Session')
        assert result == 'P'


class TestKeywordsMapping:
    """Test suite for KEYWORDS mapping."""
    
    def test_keywords_structure(self, extractor):
        """Test that KEYWORDS has correct structure."""
        assert 'A' in extractor.KEYWORDS
        assert 'P' in extractor.KEYWORDS
        assert 'E' in extractor.KEYWORDS
        
        assert isinstance(extractor.KEYWORDS['A'], list)
        assert isinstance(extractor.KEYWORDS['P'], list)
        assert isinstance(extractor.KEYWORDS['E'], list)
    
    def test_keywords_content(self, extractor):
        """Test that KEYWORDS contains expected keywords."""
        assert 'afternoon' in extractor.KEYWORDS['A']
        assert 'morning' in extractor.KEYWORDS['P']
        assert 'plenary' in extractor.KEYWORDS['P']
        assert 'evening' in extractor.KEYWORDS['E']
    
    def test_all_keywords_lowercase(self, extractor):
        """Test that all keywords are lowercase."""
        for period, keywords in extractor.KEYWORDS.items():
            for keyword in keywords:
                assert keyword == keyword.lower(), f"Keyword '{keyword}' should be lowercase"


class TestEdgeCases:
    """Test suite for edge cases."""
    
    @patch('hansard_tales.processors.period_extractor.pdfplumber.open')
    def test_multiple_keywords_in_content(self, mock_pdfplumber, extractor):
        """Test handling of multiple keywords in content."""
        # 'afternoon' should be found first
        mock_page = Mock()
        mock_page.extract_text = Mock(
            return_value='This afternoon session continues into the evening.'
        )
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = extractor.extract_from_content(pdf_path)
            assert result == 'A'
        finally:
            Path(pdf_path).unlink()
    
    def test_keyword_in_different_context(self, extractor):
        """Test that keywords are matched regardless of context."""
        # 'afternoon' in a sentence
        result = extractor.extract_from_title(
            "The meeting was held this afternoon at parliament"
        )
        assert result == 'A'
        
        # 'morning' in a different context
        result = extractor.extract_from_title(
            "Good morning, this is the plenary session"
        )
        assert result == 'P'
    
    @patch('hansard_tales.processors.period_extractor.pdfplumber.open')
    def test_whitespace_handling(self, mock_pdfplumber, extractor):
        """Test handling of extra whitespace in content."""
        mock_page = Mock()
        mock_page.extract_text = Mock(
            return_value='   afternoon   session   '
        )
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = extractor.extract_from_content(pdf_path)
            assert result == 'A'
        finally:
            Path(pdf_path).unlink()
    
    def test_special_characters_in_title(self, extractor):
        """Test handling of special characters in title."""
        result = extractor.extract_from_title(
            "Hansard Report - Afternoon Session (2024-01-01)"
        )
        assert result == 'A'
        
        result = extractor.extract_from_title(
            "Morning Session [Parliament]"
        )
        assert result == 'P'
    
    @patch('hansard_tales.processors.period_extractor.pdfplumber.open')
    def test_unicode_content(self, mock_pdfplumber, extractor):
        """Test handling of unicode characters in content."""
        mock_page = Mock()
        mock_page.extract_text = Mock(
            return_value='Afternoon session – Parliament of Kenya'
        )
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        
        mock_pdfplumber.return_value = mock_pdf
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            result = extractor.extract_from_content(pdf_path)
            assert result == 'A'
        finally:
            Path(pdf_path).unlink()



class TestPeriodExtractionProperties:
    """Property-based tests for period-of-day extraction."""
    
    @given(
        text=st.text(
            alphabet=st.characters(
                blacklist_categories=('Cs',),
                blacklist_characters=set('afternomigplsy')  # Exclude keyword chars
            ),
            min_size=0,
            max_size=100
        )
    )
    @settings(max_examples=100)
    def test_no_keywords_returns_none_property(self, text):
        """
        Property: Text without period-of-day keywords returns None.
        
        For any text that does not contain the keywords 'afternoon',
        'morning', 'evening', or 'plenary', the extractor should return None.
        """
        extractor = PeriodOfDayExtractor()
        
        # Ensure text doesn't contain any keywords
        text_lower = text.lower()
        has_keyword = any(
            keyword in text_lower
            for keywords in extractor.KEYWORDS.values()
            for keyword in keywords
        )
        
        # Only test if text truly has no keywords
        if not has_keyword:
            result = extractor.extract_from_title(text)
            assert result is None, (
                f"Expected None for text without keywords, got '{result}' "
                f"for text: '{text}'"
            )
