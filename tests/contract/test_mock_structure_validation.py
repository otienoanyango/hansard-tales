"""
Property-based tests for mock structure validation.

This module implements Property 2: Mock Structure Contract Validation.
It validates that mock data used in tests matches production data structure
and fails with descriptive errors when divergence is detected.

Validates: Requirements 2.1, 2.3, 4.5, 8.5

Property 2: Mock Structure Contract Validation
For any mock data used in tests (HTML, HTTP responses, fixtures), contract tests
should verify the mock structure matches production data structure, and fail with
descriptive errors when divergence is detected.

The property tests validate:
1. All HTML fixtures have required structural elements
2. All HTML fixtures contain valid, parseable HTML
3. All HTML fixtures with PDF links have proper link structure
4. All HTML fixtures are documented with source and capture date
5. Mock HTTP responses match expected structure
"""

import re
from typing import Dict, List, Tuple

import pytest
from bs4 import BeautifulSoup
from hypothesis import given, settings, strategies as st

from tests.fixtures.html_samples import ParliamentHTMLSamples


class TestMockStructureValidation:
    """
    Property-based tests for mock structure validation.
    
    These tests ensure that all mock data (HTML fixtures, HTTP responses)
    maintain structural consistency with production data from parliament.go.ke.
    """
    
    @given(
        sample_name=st.sampled_from([
            'HANSARD_LIST_PAGE',
            'HANSARD_PAGE_WITH_PAGINATION',
            'HANSARD_EMPTY_PAGE',
            'HANSARD_MIXED_FORMATS'
        ])
    )
    @settings(max_examples=10)
    def test_all_html_fixtures_are_valid_html(self, sample_name: str):
        """
        Property: All HTML fixtures must be valid, parseable HTML.
        
        For ANY HTML fixture in ParliamentHTMLSamples, the HTML must:
        1. Be parseable by BeautifulSoup without errors
        2. Have a valid HTML structure (html, head, body tags)
        3. Not be empty or None
        
        If this test fails: An HTML fixture has invalid HTML structure
        that cannot be parsed. This will cause scraper tests to fail.
        
        Validates: Requirements 2.1, 2.3
        """
        # Get the HTML sample
        html = ParliamentHTMLSamples.get_sample(sample_name)
        
        # Property 1: HTML must not be empty
        assert html is not None, (
            f"Mock structure violation: {sample_name} is None. "
            "All HTML fixtures must contain valid HTML content."
        )
        assert len(html.strip()) > 0, (
            f"Mock structure violation: {sample_name} is empty. "
            "All HTML fixtures must contain valid HTML content."
        )
        
        # Property 2: HTML must be parseable
        try:
            soup = BeautifulSoup(html, 'html.parser')
        except Exception as e:
            pytest.fail(
                f"Mock structure violation: {sample_name} contains invalid HTML. "
                f"BeautifulSoup parsing failed with error: {e}. "
                "All HTML fixtures must be valid, parseable HTML."
            )
        
        # Property 3: HTML must have basic structure
        assert soup.find('html') is not None, (
            f"Mock structure violation: {sample_name} missing <html> tag. "
            "All HTML fixtures must have proper HTML document structure."
        )
        assert soup.find('body') is not None, (
            f"Mock structure violation: {sample_name} missing <body> tag. "
            "All HTML fixtures must have proper HTML document structure."
        )
    
    @given(
        sample_name=st.sampled_from([
            'HANSARD_LIST_PAGE',
            'HANSARD_PAGE_WITH_PAGINATION',
            'HANSARD_MIXED_FORMATS'
        ])
    )
    @settings(max_examples=10)
    def test_html_fixtures_with_pdfs_have_valid_link_structure(self, sample_name: str):
        """
        Property: All HTML fixtures with PDF links must have valid link structure.
        
        For ANY HTML fixture that contains PDF links, each link must:
        1. Have an 'href' attribute
        2. Have the href start with '/' (relative URL)
        3. Have '.pdf' in the href (case-insensitive)
        4. Have non-empty link text
        5. Have link text containing a month name (British date format)
        
        If this test fails: An HTML fixture has PDF links with invalid structure
        that doesn't match production parliament.go.ke structure.
        
        Validates: Requirements 2.1, 2.3, 4.5
        """
        html = ParliamentHTMLSamples.get_sample(sample_name)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all links
        all_links = soup.find_all('a', href=True)
        pdf_links = [link for link in all_links if '.pdf' in link['href'].lower()]
        
        # Property: Fixtures with PDF links must have at least one
        assert len(pdf_links) > 0, (
            f"Mock structure violation: {sample_name} should contain PDF links "
            "but none were found. This fixture is expected to have PDF links "
            "based on its name and purpose."
        )
        
        # Validate each PDF link structure
        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        
        for i, link in enumerate(pdf_links):
            href = link['href']
            text = link.get_text().strip()
            
            # Property 1: href must be relative URL
            assert href.startswith('/'), (
                f"Mock structure violation: {sample_name} PDF link {i+1} "
                f"has absolute URL '{href}'. "
                "Production parliament.go.ke uses relative URLs starting with '/'. "
                "Update fixture to match production structure."
            )
            
            # Property 2: href must contain .pdf
            assert '.pdf' in href.lower(), (
                f"Mock structure violation: {sample_name} PDF link {i+1} "
                f"href '{href}' does not contain '.pdf'. "
                "All PDF links must point to .pdf files."
            )
            
            # Property 3: link text must not be empty
            assert len(text) > 0, (
                f"Mock structure violation: {sample_name} PDF link {i+1} "
                "has empty link text. "
                "Production parliament.go.ke PDF links have descriptive text."
            )
            
            # Property 4: link text must contain month name (British date format)
            has_month = any(month in text for month in month_names)
            assert has_month, (
                f"Mock structure violation: {sample_name} PDF link {i+1} "
                f"text '{text}' does not contain a month name. "
                f"Expected one of: {', '.join(month_names)}. "
                "Production parliament.go.ke uses British date formats with month names."
            )
    
    @given(
        sample_name=st.sampled_from([
            'HANSARD_LIST_PAGE',
            'HANSARD_PAGE_WITH_PAGINATION',
            'HANSARD_EMPTY_PAGE',
            'HANSARD_MIXED_FORMATS'
        ])
    )
    @settings(max_examples=10)
    def test_html_fixtures_are_documented(self, sample_name: str):
        """
        Property: All HTML fixtures must be documented with source and capture date.
        
        For ANY HTML fixture, the fixture must be documented in the source code with:
        1. Source URL comment (where the HTML was captured from)
        2. Capture date comment (when it was captured)
        3. Description comment (what the sample represents)
        
        This ensures fixtures can be updated when production structure changes.
        
        If this test fails: An HTML fixture is missing required documentation.
        Add source URL, capture date, and description comments to the fixture.
        
        Validates: Requirements 2.5, 8.5
        """
        # Read the source code of the fixtures module
        import inspect
        source = inspect.getsource(ParliamentHTMLSamples)
        
        # Find the section for this sample
        # Look for the sample name in the source
        sample_pattern = rf'{sample_name}\s*=\s*"""'
        match = re.search(sample_pattern, source)
        
        assert match is not None, (
            f"Mock structure violation: Could not find {sample_name} in source code. "
            "This indicates a problem with the fixture definition."
        )
        
        # Get the text before the sample definition (should contain comments)
        text_before_sample = source[:match.start()]
        
        # Look for the last comment block before this sample
        # Get the last 500 characters before the sample (should contain the comments)
        comment_section = text_before_sample[-500:]
        
        # Property 1: Must have Source comment
        assert 'Source:' in comment_section or 'source:' in comment_section.lower(), (
            f"Mock structure violation: {sample_name} missing 'Source:' documentation. "
            "All HTML fixtures must document the source URL where the HTML was captured. "
            "Add a comment like: # Source: https://parliament.go.ke/..."
        )
        
        # Property 2: Must have Captured date comment
        assert 'Captured:' in comment_section or 'captured:' in comment_section.lower(), (
            f"Mock structure violation: {sample_name} missing 'Captured:' documentation. "
            "All HTML fixtures must document when the HTML was captured. "
            "Add a comment like: # Captured: 2025-01-15"
        )
        
        # Property 3: Must have Description comment
        assert 'Description:' in comment_section or 'description:' in comment_section.lower(), (
            f"Mock structure violation: {sample_name} missing 'Description:' documentation. "
            "All HTML fixtures must document what the sample represents. "
            "Add a comment like: # Description: Hansard list page with PDF links"
        )
    
    def test_empty_page_fixture_has_no_pdf_links(self):
        """
        Property: Empty page fixture must not contain PDF links.
        
        The HANSARD_EMPTY_PAGE fixture represents the case when no reports
        are available. It must not contain any PDF links to accurately
        represent this edge case.
        
        If this test fails: The empty page fixture contains PDF links,
        which contradicts its purpose as an empty state representation.
        
        Validates: Requirements 2.1, 2.3
        """
        html = ParliamentHTMLSamples.HANSARD_EMPTY_PAGE
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all links
        all_links = soup.find_all('a', href=True)
        pdf_links = [link for link in all_links if '.pdf' in link['href'].lower()]
        
        # Property: Empty page must have no PDF links
        assert len(pdf_links) == 0, (
            f"Mock structure violation: HANSARD_EMPTY_PAGE contains {len(pdf_links)} PDF links. "
            "This fixture represents an empty state and should not contain any PDF links. "
            "Remove PDF links from this fixture to accurately represent the empty state."
        )
    
    def test_pagination_fixture_has_pagination_controls(self):
        """
        Property: Pagination fixture must contain pagination controls.
        
        The HANSARD_PAGE_WITH_PAGINATION fixture represents a page with
        pagination controls. It must contain navigation elements that
        match production parliament.go.ke pagination structure.
        
        If this test fails: The pagination fixture is missing pagination
        controls or has incorrect structure.
        
        Validates: Requirements 2.1, 2.3
        """
        html = ParliamentHTMLSamples.HANSARD_PAGE_WITH_PAGINATION
        soup = BeautifulSoup(html, 'html.parser')
        
        # Property 1: Must have pagination navigation
        pagination = soup.find('nav', class_='pagination')
        assert pagination is not None, (
            "Mock structure violation: HANSARD_PAGE_WITH_PAGINATION missing "
            "<nav class='pagination'> element. "
            "Production parliament.go.ke uses this structure for pagination. "
            "Add pagination navigation to match production structure."
        )
        
        # Property 2: Must have pager list
        pager = soup.find('ul', class_='pager')
        assert pager is not None, (
            "Mock structure violation: HANSARD_PAGE_WITH_PAGINATION missing "
            "<ul class='pager'> element. "
            "Production parliament.go.ke uses this structure for pagination controls. "
            "Add pager list to match production structure."
        )
        
        # Property 3: Must have page links
        page_links = soup.find_all('a', href=lambda h: h and 'page=' in h)
        assert len(page_links) > 0, (
            "Mock structure violation: HANSARD_PAGE_WITH_PAGINATION missing "
            "page links with 'page=' parameter. "
            "Production parliament.go.ke uses ?page=N for pagination. "
            "Add page links to match production structure."
        )
    
    @given(
        sample_name=st.sampled_from([
            'HANSARD_LIST_PAGE',
            'HANSARD_PAGE_WITH_PAGINATION',
            'HANSARD_MIXED_FORMATS'
        ])
    )
    @settings(max_examples=10)
    def test_pdf_links_use_url_encoding(self, sample_name: str):
        """
        Property: PDF links must use URL encoding for special characters.
        
        For ANY HTML fixture with PDF links, the links must use URL encoding
        (e.g., %20 for spaces, %2C for commas) to match production structure.
        
        If this test fails: PDF links are not properly URL-encoded, which
        doesn't match production parliament.go.ke structure.
        
        Validates: Requirements 2.1, 2.3
        """
        html = ParliamentHTMLSamples.get_sample(sample_name)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all PDF links
        all_links = soup.find_all('a', href=True)
        pdf_links = [link for link in all_links if '.pdf' in link['href'].lower()]
        
        # Property: PDF links should use URL encoding
        for i, link in enumerate(pdf_links):
            href = link['href']
            
            # Check for URL encoding patterns (%, followed by hex digits)
            has_url_encoding = '%' in href and re.search(r'%[0-9A-Fa-f]{2}', href)
            
            # If the link text has spaces or special chars, the href should be encoded
            text = link.get_text()
            has_special_chars = any(char in text for char in [' ', ',', '-'])
            
            if has_special_chars:
                assert has_url_encoding, (
                    f"Mock structure violation: {sample_name} PDF link {i+1} "
                    f"href '{href}' should use URL encoding. "
                    f"Link text '{text}' contains special characters. "
                    "Production parliament.go.ke uses URL encoding (e.g., %20 for spaces). "
                    "Update fixture to use URL encoding to match production structure."
                )
    
    def test_all_fixtures_accessible_via_get_sample(self):
        """
        Property: All HTML fixtures must be accessible via get_sample() method.
        
        For ANY HTML fixture defined in ParliamentHTMLSamples, it must be
        accessible via the get_sample() method. This ensures consistent
        access pattern across all tests.
        
        If this test fails: A fixture is defined but not accessible via
        get_sample(), indicating an inconsistency in the fixture API.
        
        Validates: Requirements 2.1, 8.5
        """
        # Get all class attributes that are HTML samples (uppercase constants)
        import inspect
        members = inspect.getmembers(ParliamentHTMLSamples)
        
        html_samples = [
            name for name, value in members
            if isinstance(value, str) and name.isupper() and 'HANSARD' in name
        ]
        
        # Property: All samples must be accessible via get_sample()
        for sample_name in html_samples:
            try:
                html = ParliamentHTMLSamples.get_sample(sample_name)
                assert html is not None, (
                    f"Mock structure violation: get_sample('{sample_name}') returned None. "
                    "All fixtures must return valid HTML content."
                )
                assert len(html) > 0, (
                    f"Mock structure violation: get_sample('{sample_name}') returned empty string. "
                    "All fixtures must return valid HTML content."
                )
            except AttributeError as e:
                pytest.fail(
                    f"Mock structure violation: get_sample('{sample_name}') failed with AttributeError. "
                    f"Error: {e}. "
                    "All fixtures must be accessible via get_sample() method."
                )
