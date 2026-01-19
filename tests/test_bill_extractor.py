"""
Tests for bill reference extraction.

This module tests the bill extraction functionality including
pattern matching, normalization, and deduplication.
"""

import json
import tempfile
from pathlib import Path

import pytest

# Import the extractor module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.bill_extractor import BillExtractor, BillReference


@pytest.fixture
def extractor():
    """Create a bill extractor instance for testing."""
    return BillExtractor()


@pytest.fixture
def sample_text_with_bills():
    """Create sample text with various bill references."""
    return """
    Hon. John Doe: I rise to support the Finance Bill, 2024. This bill is crucial for our economy.
    
    Hon. Jane Smith: I agree with the Member. Bill No. 123 should be passed immediately.
    
    Hon. Bob Wilson: The Appropriation Bill 2024 and Bill 2024/456 are also important.
    
    Hon. Alice Brown: We must consider Bill Number 789 carefully.
    """


class TestBillExtractor:
    """Test suite for bill extractor initialization."""
    
    def test_extractor_initialization(self):
        """Test extractor initializes correctly."""
        extractor = BillExtractor()
        assert extractor is not None
    
    def test_patterns_compiled(self):
        """Test that bill patterns are compiled."""
        extractor = BillExtractor()
        assert len(extractor.COMPILED_PATTERNS) > 0
        assert all(hasattr(p[0], 'finditer') for p in extractor.COMPILED_PATTERNS)


class TestBillNormalization:
    """Test suite for bill reference normalization."""
    
    def test_normalize_simple_number(self, extractor):
        """Test normalizing simple bill number."""
        result = extractor.normalize_bill_reference("123")
        assert result == "Bill No. 123"
    
    def test_normalize_with_year(self, extractor):
        """Test normalizing bill with year."""
        result = extractor.normalize_bill_reference("123", "2024")
        assert result == "Bill 2024/123"
    
    def test_normalize_leading_zeros(self, extractor):
        """Test normalizing bill number with leading zeros."""
        result = extractor.normalize_bill_reference("0123")
        assert result == "Bill No. 123"
    
    def test_normalize_zero(self, extractor):
        """Test normalizing bill number zero."""
        result = extractor.normalize_bill_reference("000")
        assert result == "Bill No. 0"


class TestBillPatternMatching:
    """Test suite for bill pattern matching."""
    
    def test_extract_bill_no_format(self, extractor):
        """Test extracting 'Bill No. 123' format."""
        text = "We must pass Bill No. 123 today."
        bills = extractor.extract_bill_references(text)
        
        assert len(bills) == 1
        assert bills[0].bill_number == "123"
        assert bills[0].bill_year is None
    
    def test_extract_bill_year_slash_format(self, extractor):
        """Test extracting 'Bill 2024/123' format."""
        text = "Bill 2024/123 is under consideration."
        bills = extractor.extract_bill_references(text)
        
        assert len(bills) == 1
        assert bills[0].bill_number == "123"
        assert bills[0].bill_year == "2024"
    
    def test_extract_bill_year_dash_format(self, extractor):
        """Test extracting 'Bill 2024-123' format."""
        text = "Bill 2024-456 needs review."
        bills = extractor.extract_bill_references(text)
        
        assert len(bills) == 1
        assert bills[0].bill_number == "456"
        assert bills[0].bill_year == "2024"
    
    def test_extract_named_bill_with_year(self, extractor):
        """Test extracting 'The Finance Bill, 2024' format."""
        text = "The Finance Bill, 2024 is controversial."
        bills = extractor.extract_bill_references(text)
        
        assert len(bills) == 1
        assert bills[0].bill_type == "Finance"
        assert bills[0].bill_year == "2024"
    
    def test_extract_named_bill_without_the(self, extractor):
        """Test extracting 'Finance Bill 2024' format."""
        text = "Finance Bill 2024 passed yesterday."
        bills = extractor.extract_bill_references(text)
        
        assert len(bills) == 1
        assert bills[0].bill_type == "Finance"
        assert bills[0].bill_year == "2024"
    
    def test_extract_bill_number_format(self, extractor):
        """Test extracting 'Bill Number 123' format."""
        text = "Bill Number 789 is pending."
        bills = extractor.extract_bill_references(text)
        
        assert len(bills) == 1
        assert bills[0].bill_number == "789"
    
    def test_extract_simple_bill_format(self, extractor):
        """Test extracting simple 'Bill 123' format."""
        text = "We discussed Bill 999 in committee."
        bills = extractor.extract_bill_references(text)
        
        assert len(bills) == 1
        assert bills[0].bill_number == "999"
    
    def test_extract_multiple_bills(self, extractor, sample_text_with_bills):
        """Test extracting multiple bills from text."""
        bills = extractor.extract_bill_references(sample_text_with_bills)
        
        # Should find: Finance Bill 2024, Bill No. 123, Appropriation Bill 2024, Bill 2024/456, Bill Number 789
        assert len(bills) >= 4
    
    def test_case_insensitive_matching(self, extractor):
        """Test that matching is case-insensitive."""
        text = "bill no. 123 and BILL NO. 456"
        bills = extractor.extract_bill_references(text)
        
        assert len(bills) == 2
    
    def test_no_bills_found(self, extractor):
        """Test handling text with no bills."""
        text = "This is just regular text with no bill references."
        bills = extractor.extract_bill_references(text)
        
        assert len(bills) == 0
    
    def test_empty_text(self, extractor):
        """Test handling empty text."""
        bills = extractor.extract_bill_references("")
        assert len(bills) == 0
    
    def test_none_text(self, extractor):
        """Test handling None text."""
        bills = extractor.extract_bill_references(None)
        assert len(bills) == 0


class TestBillDeduplication:
    """Test suite for bill deduplication."""
    
    def test_deduplicate_same_bill_number(self, extractor):
        """Test deduplicating same bill mentioned multiple times."""
        text = "Bill No. 123 is important. I support Bill No. 123. Bill No. 123 must pass."
        bills = extractor.extract_bill_references(text)
        
        # Should only return one instance
        assert len(bills) == 1
        assert bills[0].bill_number == "123"
    
    def test_deduplicate_named_bills(self, extractor):
        """Test deduplicating named bills."""
        text = "The Finance Bill, 2024 is crucial. Finance Bill 2024 must pass."
        bills = extractor.extract_bill_references(text)
        
        # Should only return one instance
        assert len(bills) == 1
        assert bills[0].bill_type == "Finance"
    
    def test_different_bills_not_deduplicated(self, extractor):
        """Test that different bills are not deduplicated."""
        text = "Bill No. 123 and Bill No. 456 are different."
        bills = extractor.extract_bill_references(text)
        
        assert len(bills) == 2


class TestBillPositions:
    """Test suite for bill position tracking."""
    
    def test_bills_sorted_by_position(self, extractor):
        """Test that bills are sorted by position in text."""
        text = "Bill No. 456 comes first. Then Bill No. 123. Finally Bill No. 789."
        bills = extractor.extract_bill_references(text)
        
        # Verify positions are in ascending order
        positions = [bill.position for bill in bills]
        assert positions == sorted(positions)
    
    def test_position_recorded(self, extractor):
        """Test that position is recorded correctly."""
        text = "Some text. Bill No. 123 here."
        bills = extractor.extract_bill_references(text)
        
        assert len(bills) == 1
        assert bills[0].position > 0


class TestExtractFromStatements:
    """Test suite for extracting from statements."""
    
    def test_extract_from_statements(self, extractor):
        """Test extracting bills from statement list."""
        statements = [
            {'text': 'I support Bill No. 123.'},
            {'text': 'The Finance Bill, 2024 is important.'},
            {'text': 'No bills mentioned here.'}
        ]
        
        results = extractor.extract_from_statements(statements)
        
        assert len(results) == 2  # Only first two statements have bills
        assert 0 in results
        assert 1 in results
        assert 2 not in results
    
    def test_extract_from_empty_statements(self, extractor):
        """Test extracting from empty statement list."""
        results = extractor.extract_from_statements([])
        assert len(results) == 0


class TestStatistics:
    """Test suite for bill statistics."""
    
    def test_statistics_with_bills(self, extractor):
        """Test getting statistics with bills."""
        bills = [
            BillReference("123", None, "Bill No. 123", 0),
            BillReference("456", "2024", "Bill 2024/456", 10),
            BillReference("", "2024", "Finance Bill 2024", 20, bill_type="Finance"),
        ]
        
        stats = extractor.get_statistics(bills)
        
        assert stats['total_bills'] == 3
        assert stats['bills_with_numbers'] == 2
        assert stats['bills_with_years'] == 2
        assert stats['bills_with_types'] == 1
        assert 'Finance' in stats['bill_types']
    
    def test_statistics_empty(self, extractor):
        """Test getting statistics with no bills."""
        stats = extractor.get_statistics([])
        
        assert stats['total_bills'] == 0
        assert stats['bills_with_numbers'] == 0
        assert stats['bills_with_years'] == 0
        assert stats['bills_with_types'] == 0


class TestBillFormatting:
    """Test suite for bill formatting."""
    
    def test_format_named_bill_with_year(self, extractor):
        """Test formatting named bill with year."""
        bill = BillReference("", "2024", "Finance Bill 2024", 0, bill_type="Finance")
        formatted = extractor.format_bill_reference(bill)
        
        assert formatted == "Finance Bill 2024"
    
    def test_format_numbered_bill_with_year(self, extractor):
        """Test formatting numbered bill with year."""
        bill = BillReference("123", "2024", "Bill 2024/123", 0)
        formatted = extractor.format_bill_reference(bill)
        
        assert formatted == "Bill 2024/123"
    
    def test_format_numbered_bill_without_year(self, extractor):
        """Test formatting numbered bill without year."""
        bill = BillReference("123", None, "Bill No. 123", 0)
        formatted = extractor.format_bill_reference(bill)
        
        assert formatted == "Bill No. 123"
    
    def test_format_fallback(self, extractor):
        """Test formatting fallback to full text."""
        bill = BillReference("", None, "Some Bill Reference", 0)
        formatted = extractor.format_bill_reference(bill)
        
        assert formatted == "Some Bill Reference"


class TestRealTextIntegration:
    """Integration tests with realistic Hansard text."""
    
    def test_extract_from_realistic_text(self, extractor):
        """Test extracting from realistic Hansard text."""
        text = """
        Hon. John Mbadi: Mr. Speaker, I rise to support the Finance Bill, 2024. 
        This Bill is crucial for our economic recovery. The provisions in Bill No. 45 
        complement the Finance Bill 2024 perfectly.
        
        Hon. Alice Wahome: I agree with the Member. However, we must also consider 
        the Appropriation Bill 2024 and ensure that Bill 2024/67 is aligned with our budget.
        """
        
        bills = extractor.extract_bill_references(text)
        
        # Should find multiple bills
        assert len(bills) >= 3
        
        # Check for specific bills
        bill_texts = [extractor.format_bill_reference(b) for b in bills]
        assert any("Finance Bill 2024" in text for text in bill_texts)
        assert any("Bill No. 45" in text for text in bill_texts)
    
    def test_extract_with_complex_formatting(self, extractor):
        """Test extracting with complex text formatting."""
        text = """
        The Finance Bill, 2024, which was introduced last month, seeks to...
        In addition, Bill No.123 (without space) and Bill Number 456 are pending.
        """
        
        bills = extractor.extract_bill_references(text)
        
        assert len(bills) >= 3
