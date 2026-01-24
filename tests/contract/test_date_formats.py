"""
Contract tests for date format assumptions.

These tests validate that our date parsing logic correctly handles
all British date formats used in parliament.go.ke Hansard reports.
They serve as an early warning system when date formats change.

Validates: Requirements 9.3

Contract tests validate assumptions about British date formats:
1. All British date formats from fixtures parse correctly
2. Date formats include expected components (day name, ordinal, month, year)
3. Ordinal suffixes are correct (1st, 2nd, 3rd, 4th, etc.)
4. Month names are spelled correctly
5. Parsing is consistent and produces valid ISO dates

These tests use the date format examples from tests/fixtures/date_formats.py
which are based on real parliament.go.ke Hansard report titles.
"""

import re
import tempfile
from datetime import datetime

import pytest

from hansard_tales.scrapers.hansard_scraper import HansardScraper
from hansard_tales.storage.filesystem import FilesystemStorage
from tests.fixtures.date_formats import DateFormatExamples


@pytest.fixture
def scraper():
    """Create a scraper instance for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FilesystemStorage(tmpdir)
        yield HansardScraper(storage=storage, rate_limit_delay=0.1)


class TestDateFormatContract:
    """
    Contract tests for British date format assumptions.
    
    These tests validate that parliament.go.ke date formats
    match our expectations and that our parsing logic handles
    all variations correctly. If these tests fail, it indicates
    that the date format has changed or our parsing logic needs updates.
    """
    
    def test_all_fixture_dates_parse_correctly(self, scraper):
        """
        Validate that all British date formats from fixtures parse correctly.
        
        Contract: Every British date format example from parliament.go.ke
        must parse to the correct ISO date. This is the fundamental
        assumption our date extraction relies on.
        
        If this test fails: Either the date format has changed on
        parliament.go.ke, or our parsing logic has a bug.
        """
        pairs = DateFormatExamples.get_pairs()
        
        # Contract: Must have date examples to test
        assert len(pairs) > 0, (
            "Contract violation: DateFormatExamples must contain date pairs. "
            "Found 0 pairs. This indicates the fixtures are not properly configured."
        )
        
        failures = []
        for british_format, expected_iso in pairs:
            result = scraper.extract_date(british_format)
            
            if result != expected_iso:
                failures.append({
                    'input': british_format,
                    'expected': expected_iso,
                    'actual': result
                })
        
        # Contract: All dates must parse correctly
        assert len(failures) == 0, (
            f"Contract violation: {len(failures)} date formats failed to parse correctly:\n" +
            "\n".join([
                f"  - Input: '{f['input']}'\n"
                f"    Expected: {f['expected']}\n"
                f"    Actual: {f['actual']}"
                for f in failures
            ]) +
            "\n\nThis indicates either:\n"
            "1. The date format on parliament.go.ke has changed\n"
            "2. Our date parsing logic has a bug\n"
            "3. The fixtures need to be updated"
        )
    
    def test_british_dates_contain_day_names(self):
        """
        Validate that British date formats include day names.
        
        Contract: British date formats from parliament.go.ke should
        include day names (Monday, Tuesday, etc.). This is part of
        the standard format we expect.
        
        If this test fails: The date format may have changed to exclude
        day names, which could affect our parsing logic.
        """
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        dates_with_day_names = [
            date for date in DateFormatExamples.BRITISH_FORMATS
            if any(day in date for day in day_names)
        ]
        
        # Contract: Most dates should include day names
        # (We expect at least 80% to have day names based on parliament.go.ke format)
        total_dates = len(DateFormatExamples.BRITISH_FORMATS)
        percentage_with_day_names = (len(dates_with_day_names) / total_dates) * 100
        
        assert percentage_with_day_names >= 80, (
            f"Contract violation: Expected at least 80% of dates to include day names. "
            f"Found {percentage_with_day_names:.1f}% ({len(dates_with_day_names)}/{total_dates}). "
            "This indicates the date format on parliament.go.ke may have changed."
        )
    
    def test_british_dates_contain_ordinal_suffixes(self):
        """
        Validate that British date formats include ordinal suffixes.
        
        Contract: British date formats should include ordinal suffixes
        (1st, 2nd, 3rd, 4th, etc.). This is a key characteristic of
        British date formatting.
        
        If this test fails: The date format may have changed to exclude
        ordinal suffixes, which could affect our parsing logic.
        """
        ordinal_pattern = re.compile(r'\b\d{1,2}(st|nd|rd|th)\b')
        
        dates_with_ordinals = [
            date for date in DateFormatExamples.BRITISH_FORMATS
            if ordinal_pattern.search(date)
        ]
        
        # Contract: All dates should include ordinal suffixes
        # (This is standard British date format)
        total_dates = len(DateFormatExamples.BRITISH_FORMATS)
        percentage_with_ordinals = (len(dates_with_ordinals) / total_dates) * 100
        
        assert percentage_with_ordinals >= 95, (
            f"Contract violation: Expected at least 95% of dates to include ordinal suffixes. "
            f"Found {percentage_with_ordinals:.1f}% ({len(dates_with_ordinals)}/{total_dates}). "
            "This indicates the date format on parliament.go.ke may have changed."
        )
    
    def test_ordinal_suffixes_are_correct(self):
        """
        Validate that ordinal suffixes follow correct English rules.
        
        Contract: Ordinal suffixes must follow English rules:
        - 1, 21, 31 → 1st, 21st, 31st
        - 2, 22 → 2nd, 22nd
        - 3, 23 → 3rd, 23rd
        - All others → th (4th, 5th, 6th, etc.)
        
        If this test fails: The date format may have incorrect ordinal
        suffixes, which could indicate data quality issues.
        """
        # Extract all day numbers with ordinals from fixtures
        ordinal_pattern = re.compile(r'\b(\d{1,2})(st|nd|rd|th)\b')
        
        incorrect_ordinals = []
        for date_str in DateFormatExamples.BRITISH_FORMATS:
            match = ordinal_pattern.search(date_str)
            if match:
                day = int(match.group(1))
                suffix = match.group(2)
                
                # Determine correct suffix
                if day in [1, 21, 31]:
                    expected_suffix = 'st'
                elif day in [2, 22]:
                    expected_suffix = 'nd'
                elif day in [3, 23]:
                    expected_suffix = 'rd'
                else:
                    expected_suffix = 'th'
                
                if suffix != expected_suffix:
                    incorrect_ordinals.append({
                        'date': date_str,
                        'day': day,
                        'found': suffix,
                        'expected': expected_suffix
                    })
        
        # Contract: All ordinal suffixes must be correct
        assert len(incorrect_ordinals) == 0, (
            f"Contract violation: Found {len(incorrect_ordinals)} dates with incorrect ordinal suffixes:\n" +
            "\n".join([
                f"  - Date: '{o['date']}'\n"
                f"    Day: {o['day']}\n"
                f"    Found: {o['found']}\n"
                f"    Expected: {o['expected']}"
                for o in incorrect_ordinals
            ]) +
            "\n\nThis indicates data quality issues in the fixtures or source data."
        )
    
    def test_month_names_are_spelled_correctly(self):
        """
        Validate that month names are spelled correctly.
        
        Contract: Month names must be spelled correctly in full English
        (January, February, March, etc.). No abbreviations or misspellings.
        
        If this test fails: The date format may have changed to use
        abbreviations or there are spelling errors.
        """
        valid_months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        
        dates_with_valid_months = []
        dates_without_valid_months = []
        
        for date_str in DateFormatExamples.BRITISH_FORMATS:
            has_valid_month = any(month in date_str for month in valid_months)
            if has_valid_month:
                dates_with_valid_months.append(date_str)
            else:
                dates_without_valid_months.append(date_str)
        
        # Contract: All dates must contain a valid month name
        assert len(dates_without_valid_months) == 0, (
            f"Contract violation: Found {len(dates_without_valid_months)} dates without valid month names:\n" +
            "\n".join([f"  - '{date}'" for date in dates_without_valid_months]) +
            f"\n\nExpected one of: {', '.join(valid_months)}\n"
            "This indicates the date format has changed or there are spelling errors."
        )
    
    def test_parsed_dates_are_valid_iso_format(self, scraper):
        """
        Validate that all parsed dates are valid ISO 8601 format.
        
        Contract: All parsed dates must be in ISO 8601 format (YYYY-MM-DD)
        and represent valid calendar dates.
        
        If this test fails: Our date parsing logic is producing invalid
        dates or incorrect formats.
        """
        iso_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        
        invalid_dates = []
        for british_format, expected_iso in DateFormatExamples.get_pairs():
            result = scraper.extract_date(british_format)
            
            # Check format
            if result and not iso_pattern.match(result):
                invalid_dates.append({
                    'input': british_format,
                    'output': result,
                    'issue': 'Invalid ISO format'
                })
                continue
            
            # Check if it's a valid date
            if result:
                try:
                    datetime.strptime(result, '%Y-%m-%d')
                except ValueError:
                    invalid_dates.append({
                        'input': british_format,
                        'output': result,
                        'issue': 'Invalid calendar date'
                    })
        
        # Contract: All parsed dates must be valid ISO dates
        assert len(invalid_dates) == 0, (
            f"Contract violation: Found {len(invalid_dates)} invalid parsed dates:\n" +
            "\n".join([
                f"  - Input: '{d['input']}'\n"
                f"    Output: {d['output']}\n"
                f"    Issue: {d['issue']}"
                for d in invalid_dates
            ]) +
            "\n\nThis indicates our date parsing logic has a bug."
        )
    
    def test_date_parsing_is_consistent(self, scraper):
        """
        Validate that date parsing is consistent across multiple calls.
        
        Contract: Parsing the same date string multiple times should
        always produce the same result. This validates that our parsing
        logic is deterministic.
        
        If this test fails: Our date parsing logic has non-deterministic
        behavior, which could cause inconsistent results.
        """
        # Test a sample of dates multiple times
        sample_dates = DateFormatExamples.get_pairs()[:5]  # Test first 5
        
        inconsistent_results = []
        for british_format, expected_iso in sample_dates:
            # Parse the same date 3 times
            results = [scraper.extract_date(british_format) for _ in range(3)]
            
            # Check if all results are the same
            if len(set(results)) > 1:
                inconsistent_results.append({
                    'input': british_format,
                    'results': results
                })
        
        # Contract: Parsing must be consistent
        assert len(inconsistent_results) == 0, (
            f"Contract violation: Found {len(inconsistent_results)} dates with inconsistent parsing:\n" +
            "\n".join([
                f"  - Input: '{r['input']}'\n"
                f"    Results: {r['results']}"
                for r in inconsistent_results
            ]) +
            "\n\nThis indicates non-deterministic behavior in date parsing."
        )
    
    def test_british_dates_contain_year(self):
        """
        Validate that British date formats include 4-digit years.
        
        Contract: All British date formats must include a 4-digit year
        (e.g., 2025, not 25). This is required for unambiguous date parsing.
        
        If this test fails: The date format may have changed to use
        2-digit years or omit years entirely.
        """
        year_pattern = re.compile(r'\b(20\d{2})\b')  # Years 2000-2099
        
        dates_with_year = [
            date for date in DateFormatExamples.BRITISH_FORMATS
            if year_pattern.search(date)
        ]
        
        # Contract: All dates must include a 4-digit year
        total_dates = len(DateFormatExamples.BRITISH_FORMATS)
        
        assert len(dates_with_year) == total_dates, (
            f"Contract violation: Expected all {total_dates} dates to include 4-digit years. "
            f"Found only {len(dates_with_year)} with years. "
            "This indicates the date format has changed."
        )
    
    def test_fixture_dates_match_expected_iso_dates(self):
        """
        Validate that fixture British dates match their expected ISO dates.
        
        Contract: The BRITISH_FORMATS and EXPECTED_ISO_FORMATS lists
        must be the same length and correspond to each other correctly.
        This validates the integrity of our test fixtures.
        
        If this test fails: The fixtures are misconfigured and need
        to be corrected.
        """
        british_count = len(DateFormatExamples.BRITISH_FORMATS)
        iso_count = len(DateFormatExamples.EXPECTED_ISO_FORMATS)
        
        # Contract: Lists must be the same length
        assert british_count == iso_count, (
            f"Contract violation: BRITISH_FORMATS has {british_count} entries "
            f"but EXPECTED_ISO_FORMATS has {iso_count} entries. "
            "These lists must be the same length and correspond to each other. "
            "This indicates the fixtures are misconfigured."
        )
        
        # Contract: Each ISO date must be valid
        iso_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        invalid_iso_dates = []
        
        for i, iso_date in enumerate(DateFormatExamples.EXPECTED_ISO_FORMATS):
            if not iso_pattern.match(iso_date):
                invalid_iso_dates.append({
                    'index': i,
                    'value': iso_date,
                    'british': DateFormatExamples.BRITISH_FORMATS[i]
                })
        
        assert len(invalid_iso_dates) == 0, (
            f"Contract violation: Found {len(invalid_iso_dates)} invalid ISO dates in fixtures:\n" +
            "\n".join([
                f"  - Index {d['index']}: '{d['value']}' (for '{d['british']}')"
                for d in invalid_iso_dates
            ]) +
            "\n\nThis indicates the fixtures are misconfigured."
        )
    
    def test_date_components_are_extractable(self):
        """
        Validate that date components can be extracted from British formats.
        
        Contract: British date formats must allow extraction of:
        - Day number (1-31)
        - Month name (January-December)
        - Year (4 digits)
        
        If this test fails: The date format structure has changed in a way
        that makes component extraction difficult.
        """
        day_pattern = re.compile(r'\b(\d{1,2})(st|nd|rd|th)\b')
        month_pattern = re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b')
        year_pattern = re.compile(r'\b(20\d{2})\b')
        
        dates_missing_components = []
        
        for date_str in DateFormatExamples.BRITISH_FORMATS:
            missing = []
            
            if not day_pattern.search(date_str):
                missing.append('day')
            if not month_pattern.search(date_str):
                missing.append('month')
            if not year_pattern.search(date_str):
                missing.append('year')
            
            if missing:
                dates_missing_components.append({
                    'date': date_str,
                    'missing': missing
                })
        
        # Contract: All dates must have extractable components
        assert len(dates_missing_components) == 0, (
            f"Contract violation: Found {len(dates_missing_components)} dates with missing components:\n" +
            "\n".join([
                f"  - Date: '{d['date']}'\n"
                f"    Missing: {', '.join(d['missing'])}"
                for d in dates_missing_components
            ]) +
            "\n\nThis indicates the date format structure has changed."
        )

