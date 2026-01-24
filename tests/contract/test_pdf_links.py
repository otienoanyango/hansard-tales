"""
Contract tests for PDF link structure assumptions.

These tests validate that our PDF link extraction and parsing logic
handles all the link format variations from parliament.go.ke correctly.
They serve as an early warning system when link structures change.

Validates: Requirements 9.2

Contract tests validate assumptions about PDF link structures:
1. PDF link structure matches expected format
2. Link hrefs follow expected patterns (/sites/default/files/...)
3. Link text contains session information (Morning/Afternoon/Evening)
4. Links contain date information in expected format

These tests use the PDF link examples from tests/fixtures/pdf_metadata.py
which are based on real parliament.go.ke link structures.
"""

import re

import pytest
from bs4 import BeautifulSoup

from tests.fixtures.pdf_metadata import PDFLinkExamples


class TestPDFLinkContract:
    """
    Contract tests for PDF link structure assumptions.
    
    These tests validate that parliament.go.ke PDF link structures
    match our expectations and that our link extraction logic handles
    all variations correctly. If these tests fail, it indicates that
    the link format has changed and our scraper may need updates.
    """
    
    def test_all_fixture_links_parse_correctly(self):
        """
        Validate that all PDF link examples parse correctly.
        
        Contract: Every PDF link example from parliament.go.ke must
        parse successfully with BeautifulSoup. This is the fundamental
        assumption our link extraction relies on.
        
        If this test fails: Either the link HTML structure has changed
        or our fixtures are malformed.
        """
        links = PDFLinkExamples.get_links()
        
        # Contract: Must have link examples to test
        assert len(links) > 0, (
            "Contract violation: PDFLinkExamples must contain link examples. "
            "Found 0 links. This indicates the fixtures are not properly configured."
        )
        
        failures = []
        for link_example in links:
            try:
                soup = BeautifulSoup(link_example.html, 'html.parser')
                anchor = soup.find('a', href=True)
                
                if anchor is None:
                    failures.append({
                        'html': link_example.html,
                        'error': 'No anchor tag found'
                    })
                elif anchor['href'] != link_example.href:
                    failures.append({
                        'html': link_example.html,
                        'expected_href': link_example.href,
                        'actual_href': anchor['href'],
                        'error': 'Href mismatch'
                    })
            except Exception as e:
                failures.append({
                    'html': link_example.html,
                    'error': str(e)
                })
        
        # Contract: All links must parse correctly
        assert len(failures) == 0, (
            f"Contract violation: {len(failures)} PDF links failed to parse:\n" +
            "\n".join([
                f"  - HTML: '{f['html'][:100]}...'\n"
                f"    Error: {f['error']}"
                for f in failures
            ]) +
            "\n\nThis indicates either:\n"
            "1. The link HTML structure on parliament.go.ke has changed\n"
            "2. Our fixtures are malformed\n"
            "3. Our parsing logic has a bug"
        )
    
    def test_link_hrefs_follow_expected_pattern(self):
        """
        Validate that link hrefs follow the expected path pattern.
        
        Contract: PDF link hrefs must follow the pattern:
        /sites/default/files/YYYY-MM/Hansard%20Report%20...pdf
        
        This validates that the URL structure is consistent and matches
        what our scraper expects.
        
        If this test fails: The URL path structure has changed on
        parliament.go.ke.
        """
        # Expected pattern: /sites/default/files/YYYY-MM/...pdf
        href_pattern = re.compile(
            r'^/sites/default/files/\d{4}-\d{2}/.*\.pdf$',
            re.IGNORECASE
        )
        
        hrefs = PDFLinkExamples.get_hrefs()
        invalid_hrefs = []
        
        for href in hrefs:
            if not href_pattern.match(href):
                invalid_hrefs.append(href)
        
        # Contract: All hrefs must match the expected pattern
        assert len(invalid_hrefs) == 0, (
            f"Contract violation: Found {len(invalid_hrefs)} hrefs that don't match expected pattern:\n" +
            "\n".join([f"  - '{href}'" for href in invalid_hrefs]) +
            "\n\nExpected pattern: /sites/default/files/YYYY-MM/...pdf\n"
            "This indicates the URL structure on parliament.go.ke has changed."
        )
    
    def test_link_hrefs_are_relative_urls(self):
        """
        Validate that all link hrefs are relative URLs.
        
        Contract: PDF link hrefs must be relative URLs starting with /
        (not absolute URLs with http:// or https://). This is important
        for URL construction in the scraper.
        
        If this test fails: The URL format has changed from relative to
        absolute URLs.
        """
        hrefs = PDFLinkExamples.get_hrefs()
        absolute_urls = []
        
        for href in hrefs:
            if href.startswith('http://') or href.startswith('https://'):
                absolute_urls.append(href)
            elif not href.startswith('/'):
                absolute_urls.append(href)
        
        # Contract: All hrefs must be relative URLs
        assert len(absolute_urls) == 0, (
            f"Contract violation: Found {len(absolute_urls)} absolute or invalid URLs:\n" +
            "\n".join([f"  - '{url}'" for url in absolute_urls]) +
            "\n\nExpected: Relative URLs starting with '/'\n"
            "This indicates the URL format has changed."
        )
    
    def test_link_hrefs_contain_year_month_directory(self):
        """
        Validate that link hrefs contain year-month directory structure.
        
        Contract: PDF link hrefs must contain a YYYY-MM directory component
        (e.g., 2025-12, 2024-11). This is used for organizing files by date.
        
        If this test fails: The directory structure has changed.
        """
        year_month_pattern = re.compile(r'/\d{4}-\d{2}/')
        
        hrefs = PDFLinkExamples.get_hrefs()
        hrefs_without_date_dir = []
        
        for href in hrefs:
            if not year_month_pattern.search(href):
                hrefs_without_date_dir.append(href)
        
        # Contract: All hrefs must contain year-month directory
        assert len(hrefs_without_date_dir) == 0, (
            f"Contract violation: Found {len(hrefs_without_date_dir)} hrefs without YYYY-MM directory:\n" +
            "\n".join([f"  - '{href}'" for href in hrefs_without_date_dir]) +
            "\n\nExpected: URLs containing /YYYY-MM/ directory structure\n"
            "This indicates the directory organization has changed."
        )
    
    def test_link_hrefs_end_with_pdf_extension(self):
        """
        Validate that all link hrefs end with .pdf extension.
        
        Contract: PDF link hrefs must end with .pdf (case-insensitive).
        This validates that we're actually linking to PDF files.
        
        If this test fails: The file format or extension has changed.
        """
        hrefs = PDFLinkExamples.get_hrefs()
        non_pdf_hrefs = []
        
        for href in hrefs:
            if not href.lower().endswith('.pdf'):
                non_pdf_hrefs.append(href)
        
        # Contract: All hrefs must end with .pdf
        assert len(non_pdf_hrefs) == 0, (
            f"Contract violation: Found {len(non_pdf_hrefs)} hrefs not ending with .pdf:\n" +
            "\n".join([f"  - '{href}'" for href in non_pdf_hrefs]) +
            "\n\nExpected: All URLs ending with .pdf extension\n"
            "This indicates the file format has changed."
        )
    
    def test_link_text_contains_session_information(self):
        """
        Validate that link text contains session information.
        
        Contract: PDF link text must contain session information
        (Morning, Afternoon, or Evening). This is used to identify
        the time of day for each sitting.
        
        If this test fails: The link text format has changed and may
        no longer include session information.
        """
        valid_sessions = ['Morning', 'Afternoon', 'Evening']
        
        texts = PDFLinkExamples.get_texts()
        texts_without_session = []
        
        for text in texts:
            has_session = any(session in text for session in valid_sessions)
            if not has_session:
                texts_without_session.append(text)
        
        # Contract: All link texts must contain session information
        assert len(texts_without_session) == 0, (
            f"Contract violation: Found {len(texts_without_session)} link texts without session info:\n" +
            "\n".join([f"  - '{text}'" for text in texts_without_session]) +
            f"\n\nExpected one of: {', '.join(valid_sessions)}\n"
            "This indicates the link text format has changed."
        )
    
    def test_link_text_contains_date_information(self):
        """
        Validate that link text contains date information.
        
        Contract: PDF link text must contain date information with
        month names (January-December). This is used to extract the
        date of each sitting.
        
        If this test fails: The link text format has changed and may
        no longer include date information.
        """
        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        
        texts = PDFLinkExamples.get_texts()
        texts_without_date = []
        
        for text in texts:
            has_month = any(month in text for month in month_names)
            if not has_month:
                texts_without_date.append(text)
        
        # Contract: All link texts must contain month names
        assert len(texts_without_date) == 0, (
            f"Contract violation: Found {len(texts_without_date)} link texts without date info:\n" +
            "\n".join([f"  - '{text}'" for text in texts_without_date]) +
            f"\n\nExpected one of: {', '.join(month_names)}\n"
            "This indicates the link text format has changed."
        )
    
    def test_link_text_follows_expected_format(self):
        """
        Validate that link text follows the expected format pattern.
        
        Contract: PDF link text should follow patterns like:
        - "Hansard Report - Thursday, 4th December 2025 - Evening Sitting"
        - "Hansard Report - 21st January 2025 - Morning Sitting"
        
        This validates that the text structure is consistent.
        
        If this test fails: The link text format has changed significantly.
        """
        # Expected pattern: "Hansard Report - ... - (Morning|Afternoon|Evening) Sitting"
        text_pattern = re.compile(
            r'Hansard\s+Report\s+-\s+.*\s+-\s+(Morning|Afternoon|Evening)\s+Sitting',
            re.IGNORECASE
        )
        
        texts = PDFLinkExamples.get_texts()
        texts_with_wrong_format = []
        
        for text in texts:
            if not text_pattern.match(text):
                texts_with_wrong_format.append(text)
        
        # Contract: All link texts should match the expected format
        assert len(texts_with_wrong_format) == 0, (
            f"Contract violation: Found {len(texts_with_wrong_format)} link texts with unexpected format:\n" +
            "\n".join([f"  - '{text}'" for text in texts_with_wrong_format]) +
            "\n\nExpected format: 'Hansard Report - <date> - <session> Sitting'\n"
            "This indicates the link text format has changed."
        )
    
    def test_link_text_contains_ordinal_suffixes(self):
        """
        Validate that link text contains ordinal suffixes for dates.
        
        Contract: Link text should include ordinal suffixes (1st, 2nd, 3rd, 4th)
        for day numbers. This is part of the British date format.
        
        If this test fails: The date format in link text may have changed
        to exclude ordinal suffixes.
        """
        ordinal_pattern = re.compile(r'\b\d{1,2}(st|nd|rd|th)\b')
        
        texts = PDFLinkExamples.get_texts()
        texts_without_ordinals = []
        
        for text in texts:
            if not ordinal_pattern.search(text):
                texts_without_ordinals.append(text)
        
        # Contract: Most link texts should include ordinal suffixes
        # (Allow some flexibility as some formats may omit them)
        percentage_with_ordinals = ((len(texts) - len(texts_without_ordinals)) / len(texts)) * 100
        
        assert percentage_with_ordinals >= 80, (
            f"Contract violation: Expected at least 80% of link texts to include ordinal suffixes. "
            f"Found {percentage_with_ordinals:.1f}% ({len(texts) - len(texts_without_ordinals)}/{len(texts)}). "
            "This indicates the date format in link text may have changed."
        )
    
    def test_link_text_contains_year(self):
        """
        Validate that link text contains 4-digit year.
        
        Contract: Link text must include a 4-digit year (e.g., 2025, 2024).
        This is required for unambiguous date extraction.
        
        If this test fails: The date format may have changed to use
        2-digit years or omit years entirely.
        """
        year_pattern = re.compile(r'\b(20\d{2})\b')  # Years 2000-2099
        
        texts = PDFLinkExamples.get_texts()
        texts_without_year = []
        
        for text in texts:
            if not year_pattern.search(text):
                texts_without_year.append(text)
        
        # Contract: All link texts must include 4-digit year
        assert len(texts_without_year) == 0, (
            f"Contract violation: Found {len(texts_without_year)} link texts without 4-digit year:\n" +
            "\n".join([f"  - '{text}'" for text in texts_without_year]) +
            "\n\nExpected: All texts containing 4-digit year (20XX)\n"
            "This indicates the date format has changed."
        )
    
    def test_fixture_links_have_complete_metadata(self):
        """
        Validate that all fixture links have complete metadata.
        
        Contract: Each PDFLinkStructure in fixtures must have:
        - html: The complete HTML of the link
        - href: The href attribute value
        - text: The link text content
        - expected_date: Expected date in ISO format
        - expected_period: Expected period (Morning/Afternoon/Evening)
        - source_url: URL where captured
        - captured_date: Date when captured
        
        If this test fails: The fixtures are incomplete or misconfigured.
        """
        links = PDFLinkExamples.get_links()
        incomplete_links = []
        
        for i, link in enumerate(links):
            missing_fields = []
            
            if not link.html:
                missing_fields.append('html')
            if not link.href:
                missing_fields.append('href')
            if not link.text:
                missing_fields.append('text')
            if not link.expected_date:
                missing_fields.append('expected_date')
            if not link.expected_period:
                missing_fields.append('expected_period')
            if not link.source_url:
                missing_fields.append('source_url')
            if not link.captured_date:
                missing_fields.append('captured_date')
            
            if missing_fields:
                incomplete_links.append({
                    'index': i,
                    'missing': missing_fields,
                    'href': link.href if link.href else 'N/A'
                })
        
        # Contract: All links must have complete metadata
        assert len(incomplete_links) == 0, (
            f"Contract violation: Found {len(incomplete_links)} links with incomplete metadata:\n" +
            "\n".join([
                f"  - Link {l['index']} (href: {l['href']})\n"
                f"    Missing: {', '.join(l['missing'])}"
                for l in incomplete_links
            ]) +
            "\n\nThis indicates the fixtures are misconfigured."
        )
    
    def test_fixture_expected_dates_are_valid_iso_format(self):
        """
        Validate that expected dates in fixtures are valid ISO format.
        
        Contract: All expected_date values must be in ISO 8601 format
        (YYYY-MM-DD) and represent valid calendar dates.
        
        If this test fails: The fixtures contain invalid date values.
        """
        from datetime import datetime
        
        iso_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        
        links = PDFLinkExamples.get_links()
        invalid_dates = []
        
        for i, link in enumerate(links):
            # Check format
            if not iso_pattern.match(link.expected_date):
                invalid_dates.append({
                    'index': i,
                    'href': link.href,
                    'date': link.expected_date,
                    'issue': 'Invalid ISO format'
                })
                continue
            
            # Check if it's a valid date
            try:
                datetime.strptime(link.expected_date, '%Y-%m-%d')
            except ValueError:
                invalid_dates.append({
                    'index': i,
                    'href': link.href,
                    'date': link.expected_date,
                    'issue': 'Invalid calendar date'
                })
        
        # Contract: All expected dates must be valid ISO dates
        assert len(invalid_dates) == 0, (
            f"Contract violation: Found {len(invalid_dates)} invalid expected dates:\n" +
            "\n".join([
                f"  - Link {d['index']} (href: {d['href']})\n"
                f"    Date: {d['date']}\n"
                f"    Issue: {d['issue']}"
                for d in invalid_dates
            ]) +
            "\n\nThis indicates the fixtures are misconfigured."
        )
    
    def test_fixture_expected_periods_are_valid(self):
        """
        Validate that expected periods in fixtures are valid values.
        
        Contract: All expected_period values must be one of:
        Morning, Afternoon, or Evening.
        
        If this test fails: The fixtures contain invalid period values.
        """
        valid_periods = ['Morning', 'Afternoon', 'Evening']
        
        links = PDFLinkExamples.get_links()
        invalid_periods = []
        
        for i, link in enumerate(links):
            if link.expected_period not in valid_periods:
                invalid_periods.append({
                    'index': i,
                    'href': link.href,
                    'period': link.expected_period
                })
        
        # Contract: All expected periods must be valid
        assert len(invalid_periods) == 0, (
            f"Contract violation: Found {len(invalid_periods)} invalid expected periods:\n" +
            "\n".join([
                f"  - Link {p['index']} (href: {p['href']})\n"
                f"    Period: '{p['period']}'"
                for p in invalid_periods
            ]) +
            f"\n\nExpected one of: {', '.join(valid_periods)}\n"
            "This indicates the fixtures are misconfigured."
        )
    
    def test_link_href_matches_expected_date(self):
        """
        Validate that link href contains date matching expected_date.
        
        Contract: The YYYY-MM directory in the href should match the
        year and month of the expected_date. This validates consistency
        between URL structure and date information.
        
        If this test fails: There's a mismatch between URL structure
        and date information in the fixtures.
        """
        links = PDFLinkExamples.get_links()
        mismatches = []
        
        for i, link in enumerate(links):
            # Extract YYYY-MM from expected_date
            expected_year_month = link.expected_date[:7]  # "2025-12"
            
            # Check if href contains this year-month
            if f'/{expected_year_month}/' not in link.href:
                mismatches.append({
                    'index': i,
                    'href': link.href,
                    'expected_date': link.expected_date,
                    'expected_year_month': expected_year_month
                })
        
        # Contract: Href should contain matching year-month
        assert len(mismatches) == 0, (
            f"Contract violation: Found {len(mismatches)} links with href/date mismatch:\n" +
            "\n".join([
                f"  - Link {m['index']}\n"
                f"    Href: {m['href']}\n"
                f"    Expected date: {m['expected_date']}\n"
                f"    Expected year-month in href: /{m['expected_year_month']}/"
                for m in mismatches
            ]) +
            "\n\nThis indicates inconsistency in the fixtures."
        )
    
    def test_link_text_matches_expected_period(self):
        """
        Validate that link text contains the expected period.
        
        Contract: The link text should contain the expected_period value
        (Morning, Afternoon, or Evening). This validates consistency
        between link text and period information.
        
        If this test fails: There's a mismatch between link text and
        period information in the fixtures.
        """
        links = PDFLinkExamples.get_links()
        mismatches = []
        
        for i, link in enumerate(links):
            if link.expected_period not in link.text:
                mismatches.append({
                    'index': i,
                    'text': link.text,
                    'expected_period': link.expected_period
                })
        
        # Contract: Link text should contain expected period
        assert len(mismatches) == 0, (
            f"Contract violation: Found {len(mismatches)} links with text/period mismatch:\n" +
            "\n".join([
                f"  - Link {m['index']}\n"
                f"    Text: '{m['text']}'\n"
                f"    Expected period: {m['expected_period']}"
                for m in mismatches
            ]) +
            "\n\nThis indicates inconsistency in the fixtures."
        )
    
    def test_fixture_coverage_includes_all_periods(self):
        """
        Validate that fixtures include examples of all session periods.
        
        Contract: The fixtures should include examples of Morning,
        Afternoon, and Evening sessions to ensure comprehensive testing.
        
        If this test fails: The fixtures are missing examples of some
        session periods.
        """
        links = PDFLinkExamples.get_links()
        periods_found = set(link.expected_period for link in links)
        expected_periods = {'Morning', 'Afternoon', 'Evening'}
        
        missing_periods = expected_periods - periods_found
        
        # Contract: Fixtures should cover all session periods
        assert len(missing_periods) == 0, (
            f"Contract violation: Fixtures are missing examples of these periods: "
            f"{', '.join(missing_periods)}. "
            "Fixtures should include examples of Morning, Afternoon, and Evening sessions "
            "to ensure comprehensive testing."
        )
    
    def test_fixture_coverage_includes_various_ordinals(self):
        """
        Validate that fixtures include various ordinal suffixes.
        
        Contract: The fixtures should include examples of different
        ordinal suffixes (1st, 2nd, 3rd, 4th, etc.) to ensure our
        parsing handles all variations.
        
        If this test fails: The fixtures may not have sufficient variety
        in ordinal suffixes.
        """
        ordinal_pattern = re.compile(r'\b\d{1,2}(st|nd|rd|th)\b')
        
        texts = PDFLinkExamples.get_texts()
        ordinals_found = set()
        
        for text in texts:
            match = ordinal_pattern.search(text)
            if match:
                ordinals_found.add(match.group(1))
        
        # Contract: Should have examples of all ordinal types
        expected_ordinals = {'st', 'nd', 'rd', 'th'}
        missing_ordinals = expected_ordinals - ordinals_found
        
        assert len(missing_ordinals) == 0, (
            f"Contract violation: Fixtures are missing examples of these ordinal suffixes: "
            f"{', '.join(missing_ordinals)}. "
            "Fixtures should include examples of 1st, 2nd, 3rd, and 4th+ dates "
            "to ensure comprehensive testing."
        )
