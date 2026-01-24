"""
Tests for Filename Generator.

This module tests the filename generation and parsing functionality including
format validation, numeric suffix generation, and date conversion.
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import date as dt_date

from hansard_tales.utils.filename_generator import FilenameGenerator


@pytest.fixture
def generator():
    """Create a FilenameGenerator instance for testing."""
    return FilenameGenerator()


class TestGenerate:
    """Test suite for filename generation."""
    
    def test_generate_different_periods_no_conflict(self, generator):
        """Test that different periods don't conflict."""
        existing = ["hansard_20240101_A.pdf"]
        result = generator.generate("2024-01-01", "P", existing)
        assert result == "hansard_20240101_P.pdf"
    
    def test_generate_different_dates_no_conflict(self, generator):
        """Test that different dates don't conflict."""
        existing = ["hansard_20240101_A.pdf"]
        result = generator.generate("2024-01-02", "A", existing)
        assert result == "hansard_20240102_A.pdf"
    
    def test_generate_invalid_period_raises_error(self, generator):
        """Test that invalid period raises ValueError."""
        with pytest.raises(ValueError, match="Invalid period_of_day"):
            generator.generate("2024-01-01", "X", [])
    
    def test_generate_invalid_date_format_raises_error(self, generator):
        """Test that invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date format"):
            generator.generate("2024/01/01", "A", [])
        
        with pytest.raises(ValueError, match="Invalid date format"):
            generator.generate("20240101", "A", [])
        
        with pytest.raises(ValueError, match="Invalid date format"):
            generator.generate("01-01-2024", "A", [])
    
    def test_generate_invalid_month_raises_error(self, generator):
        """Test that invalid month raises ValueError."""
        with pytest.raises(ValueError, match="Invalid month"):
            generator.generate("2024-13-01", "A", [])
        
        with pytest.raises(ValueError, match="Invalid month"):
            generator.generate("2024-00-01", "A", [])
    
    def test_generate_invalid_day_raises_error(self, generator):
        """Test that invalid day raises ValueError."""
        with pytest.raises(ValueError, match="Invalid day"):
            generator.generate("2024-01-32", "A", [])
        
        with pytest.raises(ValueError, match="Invalid day"):
            generator.generate("2024-01-00", "A", [])
    
    def test_generate_empty_existing_files(self, generator):
        """Test generating filename with empty existing files list."""
        result = generator.generate("2024-01-01", "A", [])
        assert result == "hansard_20240101_A.pdf"
    
    def test_generate_preserves_leading_zeros(self, generator):
        """Test that leading zeros in date are preserved."""
        result = generator.generate("2024-01-05", "A", [])
        assert result == "hansard_20240105_A.pdf"
        
        result = generator.generate("2024-09-09", "P", [])
        assert result == "hansard_20240909_P.pdf"


class TestParse:
    """Test suite for filename parsing."""
    
    def test_parse_basic_filename(self, generator):
        """Test parsing basic filename without suffix."""
        result = generator.parse("hansard_20240101_A.pdf")
        assert result == {
            'date': '2024-01-01',
            'period_of_day': 'A',
            'suffix': None
        }
    
    def test_parse_filename_with_suffix(self, generator):
        """Test parsing filename with numeric suffix."""
        result = generator.parse("hansard_20240101_A_2.pdf")
        assert result == {
            'date': '2024-01-01',
            'period_of_day': 'A',
            'suffix': '2'
        }
    
    def test_parse_morning_period(self, generator):
        """Test parsing filename with morning period (P)."""
        result = generator.parse("hansard_20240115_P.pdf")
        assert result == {
            'date': '2024-01-15',
            'period_of_day': 'P',
            'suffix': None
        }
    
    def test_parse_evening_period(self, generator):
        """Test parsing filename with evening period (E)."""
        result = generator.parse("hansard_20241231_E.pdf")
        assert result == {
            'date': '2024-12-31',
            'period_of_day': 'E',
            'suffix': None
        }
    
    def test_parse_large_suffix(self, generator):
        """Test parsing filename with large suffix number."""
        result = generator.parse("hansard_20240101_A_99.pdf")
        assert result == {
            'date': '2024-01-01',
            'period_of_day': 'A',
            'suffix': '99'
        }
    
    def test_parse_invalid_format_returns_none(self, generator):
        """Test that invalid format returns None values."""
        result = generator.parse("invalid_filename.pdf")
        assert result == {
            'date': None,
            'period_of_day': None,
            'suffix': None
        }
    
    def test_parse_wrong_prefix(self, generator):
        """Test parsing filename with wrong prefix."""
        result = generator.parse("report_20240101_A.pdf")
        assert result == {
            'date': None,
            'period_of_day': None,
            'suffix': None
        }
    
    def test_parse_wrong_date_format(self, generator):
        """Test parsing filename with wrong date format."""
        result = generator.parse("hansard_2024-01-01_A.pdf")
        assert result == {
            'date': None,
            'period_of_day': None,
            'suffix': None
        }
    
    def test_parse_invalid_period(self, generator):
        """Test parsing filename with invalid period."""
        result = generator.parse("hansard_20240101_X.pdf")
        assert result == {
            'date': None,
            'period_of_day': None,
            'suffix': None
        }
    
    def test_parse_missing_extension(self, generator):
        """Test parsing filename without .pdf extension."""
        result = generator.parse("hansard_20240101_A")
        assert result == {
            'date': None,
            'period_of_day': None,
            'suffix': None
        }
    
    def test_parse_wrong_extension(self, generator):
        """Test parsing filename with wrong extension."""
        result = generator.parse("hansard_20240101_A.txt")
        assert result == {
            'date': None,
            'period_of_day': None,
            'suffix': None
        }
    
    def test_parse_extra_underscores(self, generator):
        """Test parsing filename with extra underscores."""
        result = generator.parse("hansard_20240101_A_2_extra.pdf")
        assert result == {
            'date': None,
            'period_of_day': None,
            'suffix': None
        }
    
    def test_parse_preserves_leading_zeros(self, generator):
        """Test that parsing preserves leading zeros in date."""
        result = generator.parse("hansard_20240105_A.pdf")
        assert result['date'] == '2024-01-05'
        
        result = generator.parse("hansard_20240909_P.pdf")
        assert result['date'] == '2024-09-09'


class TestRoundTrip:
    """Test suite for generate/parse round-trip consistency."""
    
    def test_roundtrip_basic(self, generator):
        """Test that generate and parse are inverse operations."""
        filename = generator.generate("2024-01-01", "A", [])
        parsed = generator.parse(filename)
        
        assert parsed['date'] == "2024-01-01"
        assert parsed['period_of_day'] == "A"
        assert parsed['suffix'] is None
    
    def test_roundtrip_with_suffix(self, generator):
        """Test round-trip with numeric suffix."""
        existing = ["hansard_20240101_A.pdf"]
        filename = generator.generate("2024-01-01", "A", existing)
        parsed = generator.parse(filename)
        
        assert parsed['date'] == "2024-01-01"
        assert parsed['period_of_day'] == "A"
        assert parsed['suffix'] == "2"
    
    def test_roundtrip_all_periods(self, generator):
        """Test round-trip for all period types."""
        for period in ['A', 'P', 'E']:
            filename = generator.generate("2024-06-15", period, [])
            parsed = generator.parse(filename)
            
            assert parsed['date'] == "2024-06-15"
            assert parsed['period_of_day'] == period
            assert parsed['suffix'] is None


class TestEdgeCases:
    """Test suite for edge cases."""
    
    def test_generate_leap_year_date(self, generator):
        """Test generating filename for leap year date."""
        result = generator.generate("2024-02-29", "A", [])
        assert result == "hansard_20240229_A.pdf"
    
    def test_generate_year_boundary(self, generator):
        """Test generating filename for year boundary dates."""
        result = generator.generate("2024-01-01", "A", [])
        assert result == "hansard_20240101_A.pdf"
        
        result = generator.generate("2024-12-31", "E", [])
        assert result == "hansard_20241231_E.pdf"
    
    def test_parse_year_boundary(self, generator):
        """Test parsing filename for year boundary dates."""
        result = generator.parse("hansard_20240101_A.pdf")
        assert result['date'] == "2024-01-01"
        
        result = generator.parse("hansard_20241231_E.pdf")
        assert result['date'] == "2024-12-31"
    
    def test_generate_with_unrelated_files(self, generator):
        """Test that unrelated files don't affect generation."""
        existing = [
            "hansard_20240101_P.pdf",  # Different period
            "hansard_20240102_A.pdf",  # Different date
            "other_file.pdf"           # Unrelated file
        ]
        result = generator.generate("2024-01-01", "A", existing)
        assert result == "hansard_20240101_A.pdf"
    
    def test_generate_case_sensitive_period(self, generator):
        """Test that period is case-sensitive."""
        # Lowercase should raise error
        with pytest.raises(ValueError, match="Invalid period_of_day"):
            generator.generate("2024-01-01", "a", [])
    
    def test_parse_case_sensitive_period(self, generator):
        """Test that parsing is case-sensitive for period."""
        # Lowercase period should not match
        result = generator.parse("hansard_20240101_a.pdf")
        assert result['period_of_day'] is None


class TestFilenameProperties:
    """Property-based tests for filename generation and parsing."""
    
    @given(
        date=st.dates(min_value=dt_date(2020, 1, 1), max_value=dt_date(2030, 12, 31)),
        period=st.sampled_from(['A', 'P', 'E'])
    )
    @settings(max_examples=100)
    def test_filename_format_validation_property(self, date, period):
        """
        **Validates: Requirements 2.1**
        
        Property 1: Filename Format Validation
        
        For any date and period-of-day (A, P, or E), the generated filename
        should match the pattern hansard_YYYYMMDD_{A|P|E}.pdf where YYYYMMDD
        is the date in compact format.
        
        This property test verifies that:
        1. Generated filenames always match the expected pattern
        2. Date is correctly formatted as YYYYMMDD
        3. Period code is correctly included
        """
        generator = FilenameGenerator()
        
        # Generate filename
        date_str = date.strftime('%Y-%m-%d')
        filename = generator.generate(date_str, period, [])
        
        # Verify format matches pattern
        import re
        pattern = r'^hansard_\d{8}_[APE]\.pdf$'
        assert re.match(pattern, filename), (
            f"Filename '{filename}' does not match pattern '{pattern}'"
        )
        
        # Verify date is correctly formatted
        date_compact = date.strftime('%Y%m%d')
        assert date_compact in filename, (
            f"Date '{date_compact}' not found in filename '{filename}'"
        )
        
        # Verify period is correctly included
        assert f'_{period}.pdf' in filename, (
            f"Period '_{period}.pdf' not found in filename '{filename}'"
        )
    
    @given(
        date=st.dates(min_value=dt_date(2020, 1, 1), max_value=dt_date(2030, 12, 31)),
        period=st.sampled_from(['A', 'P', 'E']),
        num_existing=st.integers(min_value=0, max_value=10)
    )
    @settings(max_examples=100)
    def test_numeric_suffix_generation_property(self, date, period, num_existing):
        """
        **Validates: Requirements 2.4**
        
        Property 3: Numeric Suffix Generation
        
        For any date and period-of-day where files already exist, the generated
        filename should append a numeric suffix starting from 2.
        
        This property test verifies that:
        1. When no files exist, no suffix is added
        2. When base file exists, suffix starts at 2
        3. Suffix increments correctly for multiple existing files
        4. Generated filename is always unique
        """
        generator = FilenameGenerator()
        
        date_str = date.strftime('%Y-%m-%d')
        date_compact = date.strftime('%Y%m%d')
        
        # Create list of existing files
        existing = []
        if num_existing > 0:
            # Add base file
            existing.append(f"hansard_{date_compact}_{period}.pdf")
            # Add files with suffixes
            for i in range(2, num_existing + 1):
                existing.append(f"hansard_{date_compact}_{period}_{i}.pdf")
        
        # Generate new filename
        filename = generator.generate(date_str, period, existing)
        
        # Verify filename is unique
        assert filename not in existing, (
            f"Generated filename '{filename}' already exists in {existing}"
        )
        
        # Verify correct suffix logic
        if num_existing == 0:
            # No existing files - should have no suffix
            expected = f"hansard_{date_compact}_{period}.pdf"
            assert filename == expected, (
                f"Expected '{expected}' with no existing files, got '{filename}'"
            )
        else:
            # Existing files - should have suffix
            expected_suffix = num_existing + 1
            expected = f"hansard_{date_compact}_{period}_{expected_suffix}.pdf"
            assert filename == expected, (
                f"Expected '{expected}' with {num_existing} existing files, "
                f"got '{filename}'"
            )
    
    @given(
        date=st.dates(min_value=dt_date(2020, 1, 1), max_value=dt_date(2030, 12, 31)),
        period=st.sampled_from(['A', 'P', 'E']),
        suffix=st.integers(min_value=2, max_value=99)
    )
    @settings(max_examples=100)
    def test_parse_roundtrip_property(self, date, period, suffix):
        """
        Property: Parse is inverse of generate (round-trip consistency).
        
        For any valid filename generated by generate(), parsing it should
        return the original date, period, and suffix.
        """
        generator = FilenameGenerator()
        
        date_str = date.strftime('%Y-%m-%d')
        date_compact = date.strftime('%Y%m%d')
        
        # Create filename with suffix
        filename = f"hansard_{date_compact}_{period}_{suffix}.pdf"
        
        # Parse filename
        parsed = generator.parse(filename)
        
        # Verify round-trip consistency
        assert parsed['date'] == date_str, (
            f"Expected date '{date_str}', got '{parsed['date']}'"
        )
        assert parsed['period_of_day'] == period, (
            f"Expected period '{period}', got '{parsed['period_of_day']}'"
        )
        assert parsed['suffix'] == str(suffix), (
            f"Expected suffix '{suffix}', got '{parsed['suffix']}'"
        )
    
    @given(
        date=st.dates(min_value=dt_date(2020, 1, 1), max_value=dt_date(2030, 12, 31)),
        period=st.sampled_from(['A', 'P', 'E'])
    )
    @settings(max_examples=100)
    def test_generate_parse_roundtrip_property(self, date, period):
        """
        Property: Generate then parse returns original values.
        
        For any date and period, generating a filename and then parsing it
        should return the original date and period.
        """
        generator = FilenameGenerator()
        
        date_str = date.strftime('%Y-%m-%d')
        
        # Generate filename
        filename = generator.generate(date_str, period, [])
        
        # Parse filename
        parsed = generator.parse(filename)
        
        # Verify round-trip
        assert parsed['date'] == date_str, (
            f"Round-trip failed: expected date '{date_str}', "
            f"got '{parsed['date']}' from filename '{filename}'"
        )
        assert parsed['period_of_day'] == period, (
            f"Round-trip failed: expected period '{period}', "
            f"got '{parsed['period_of_day']}' from filename '{filename}'"
        )
        assert parsed['suffix'] is None, (
            f"Round-trip failed: expected no suffix, "
            f"got '{parsed['suffix']}' from filename '{filename}'"
        )
    
    @given(
        text=st.text(
            alphabet=st.characters(blacklist_categories=('Cs',)),
            min_size=1,
            max_size=100
        )
    )
    @settings(max_examples=100)
    def test_parse_invalid_format_property(self, text):
        """
        Property: Invalid filenames return None values.
        
        For any text that doesn't match the expected filename pattern,
        parse() should return None for all fields.
        """
        generator = FilenameGenerator()
        
        # Skip if text happens to match valid pattern
        import re
        if re.match(r'^hansard_\d{8}_[APE](?:_\d+)?\.pdf$', text):
            return
        
        # Parse invalid filename
        parsed = generator.parse(text)
        
        # Verify all fields are None
        assert parsed['date'] is None, (
            f"Expected None for date in invalid filename '{text}', "
            f"got '{parsed['date']}'"
        )
        assert parsed['period_of_day'] is None, (
            f"Expected None for period in invalid filename '{text}', "
            f"got '{parsed['period_of_day']}'"
        )
        assert parsed['suffix'] is None, (
            f"Expected None for suffix in invalid filename '{text}', "
            f"got '{parsed['suffix']}'"
        )
