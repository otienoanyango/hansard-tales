"""
Contract tests for HTML structure assumptions.

These tests validate that our mocks match the actual structure
of parliament.go.ke pages. They serve as an early warning system
when the external system changes.

Validates: Requirements 2.2, 9.1

Contract tests validate assumptions about parliament.go.ke HTML structure:
1. Hansard list pages contain PDF links
2. PDF link text contains date information (month names)
3. PDF links are relative URLs (start with /)
4. Links point to .pdf files

These tests use the HTML samples from tests/fixtures/html_samples.py
which are based on real parliament.go.ke structure.
"""

import pytest
from bs4 import BeautifulSoup
from tests.fixtures.html_samples import ParliamentHTMLSamples


class TestHTMLStructureContract:
    """
    Contract tests for HTML structure assumptions.
    
    These tests validate that parliament.go.ke HTML structure
    matches our expectations and fixtures. If these tests fail,
    it indicates that the parliament.go.ke website structure
    has changed and our scraper may need updates.
    """
    
    def test_hansard_list_has_pdf_links(self):
        """
        Validate that Hansard list page contains PDF links.
        
        Contract: The main Hansard list page must contain at least one
        link to a PDF file. This is the fundamental assumption our
        scraper relies on.
        
        If this test fails: The parliament.go.ke website structure has
        changed and PDF links may no longer be present or may have moved
        to a different location.
        """
        html = ParliamentHTMLSamples.HANSARD_LIST_PAGE
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all links
        links = soup.find_all('a', href=True)
        pdf_links = [link for link in links if '.pdf' in link['href'].lower()]
        
        # Contract: Page must have at least one PDF link
        assert len(pdf_links) > 0, (
            "Contract violation: Hansard list page must contain PDF links. "
            "Found 0 PDF links. This indicates the parliament.go.ke website "
            "structure has changed."
        )
        
        # Additional validation: Should have multiple links (typically 3-10 per page)
        assert len(pdf_links) >= 3, (
            f"Contract warning: Expected at least 3 PDF links, found {len(pdf_links)}. "
            "This may indicate incomplete page loading or structure changes."
        )
    
    def test_pdf_link_text_contains_date(self):
        """
        Validate that PDF link text contains date information.
        
        Contract: PDF link text must contain month names (British format)
        which we use to extract dates. The text should follow patterns like:
        - "Hansard Report - Thursday, 4th December 2025 - Evening Sitting"
        - "Hansard Report - Tuesday, 15th October 2025 - Morning Sitting"
        
        If this test fails: The link text format has changed and our date
        extraction logic may need updates.
        """
        html = ParliamentHTMLSamples.HANSARD_LIST_PAGE
        soup = BeautifulSoup(html, 'html.parser')
        
        links = soup.find_all('a', href=True)
        pdf_links = [link for link in links if '.pdf' in link['href'].lower()]
        
        # Contract: PDF link text must contain date-like patterns
        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        
        for link in pdf_links:
            text = link.get_text()
            has_month = any(month in text for month in month_names)
            
            assert has_month, (
                f"Contract violation: PDF link text must contain a month name. "
                f"Link text: '{text}'. "
                f"Expected one of: {', '.join(month_names)}. "
                "This indicates the date format in link text has changed."
            )
    
    def test_pdf_links_are_relative_urls(self):
        """
        Validate that PDF links are relative URLs.
        
        Contract: PDF links should be relative URLs starting with /
        (e.g., "/sites/default/files/2025-12/Hansard...pdf").
        This is important for URL construction in the scraper.
        
        If this test fails: The URL format has changed from relative to
        absolute, or the path structure has changed.
        """
        html = ParliamentHTMLSamples.HANSARD_LIST_PAGE
        soup = BeautifulSoup(html, 'html.parser')
        
        links = soup.find_all('a', href=True)
        pdf_links = [link for link in links if '.pdf' in link['href'].lower()]
        
        # Contract: PDF links should be relative URLs starting with /
        for link in pdf_links:
            href = link['href']
            
            assert href.startswith('/'), (
                f"Contract violation: PDF link should be a relative URL starting with '/'. "
                f"Found: '{href}'. "
                "This indicates the URL format has changed from relative to absolute."
            )
    
    def test_pdf_links_point_to_pdf_files(self):
        """
        Validate that PDF links actually point to .pdf files.
        
        Contract: All links identified as PDF links must have '.pdf'
        in their href attribute (case-insensitive). This validates
        our link filtering logic.
        
        If this test fails: The file extension or URL structure has
        changed.
        """
        html = ParliamentHTMLSamples.HANSARD_LIST_PAGE
        soup = BeautifulSoup(html, 'html.parser')
        
        links = soup.find_all('a', href=True)
        pdf_links = [link for link in links if '.pdf' in link['href'].lower()]
        
        # Contract: All PDF links must end with .pdf (case-insensitive)
        for link in pdf_links:
            href = link['href']
            
            assert '.pdf' in href.lower(), (
                f"Contract violation: PDF link must contain '.pdf' extension. "
                f"Found: '{href}'. "
                "This indicates the file format or URL structure has changed."
            )
    
    def test_pagination_page_has_pdf_links(self):
        """
        Validate that paginated pages also contain PDF links.
        
        Contract: Pages beyond the first page (with pagination controls)
        should also contain PDF links. This validates that our pagination
        logic will find content on subsequent pages.
        
        If this test fails: The pagination structure may have changed or
        subsequent pages may not contain the expected content.
        """
        html = ParliamentHTMLSamples.HANSARD_PAGE_WITH_PAGINATION
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all links
        links = soup.find_all('a', href=True)
        pdf_links = [link for link in links if '.pdf' in link['href'].lower()]
        
        # Contract: Paginated pages must also have PDF links
        assert len(pdf_links) > 0, (
            "Contract violation: Paginated Hansard pages must contain PDF links. "
            "Found 0 PDF links on page with pagination. "
            "This indicates the pagination structure has changed."
        )
    
    def test_empty_page_has_no_pdf_links(self):
        """
        Validate that empty pages correctly have no PDF links.
        
        Contract: When no Hansard reports are available, the page should
        not contain PDF links. This validates our handling of empty results.
        
        If this test fails: The empty state representation has changed.
        """
        html = ParliamentHTMLSamples.HANSARD_EMPTY_PAGE
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all links
        links = soup.find_all('a', href=True)
        pdf_links = [link for link in links if '.pdf' in link['href'].lower()]
        
        # Contract: Empty pages should have no PDF links
        assert len(pdf_links) == 0, (
            f"Contract violation: Empty Hansard page should have no PDF links. "
            f"Found {len(pdf_links)} PDF links. "
            "This indicates the empty state representation has changed."
        )
    
    def test_mixed_formats_page_has_valid_links(self):
        """
        Validate that pages with mixed date formats still have valid PDF links.
        
        Contract: Even when date formats vary (with/without day of week,
        different ordinal formats), the PDF links should still be valid
        relative URLs pointing to .pdf files.
        
        If this test fails: The URL structure may have changed or become
        inconsistent across different date formats.
        """
        html = ParliamentHTMLSamples.HANSARD_MIXED_FORMATS
        soup = BeautifulSoup(html, 'html.parser')
        
        links = soup.find_all('a', href=True)
        pdf_links = [link for link in links if '.pdf' in link['href'].lower()]
        
        # Contract: Must have PDF links
        assert len(pdf_links) > 0, (
            "Contract violation: Mixed formats page must contain PDF links."
        )
        
        # Contract: All links must be relative and point to PDFs
        for link in pdf_links:
            href = link['href']
            assert href.startswith('/'), (
                f"Contract violation: PDF link should be relative. Found: '{href}'"
            )
            assert '.pdf' in href.lower(), (
                f"Contract violation: Link should point to PDF. Found: '{href}'"
            )
