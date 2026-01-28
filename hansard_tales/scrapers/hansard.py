"""
Hansard scraper for National Assembly and Senate documents.

This module implements the scraper for Hansard documents from
parliament.go.ke, extracting PDF links from HTML tables with pagination support.
"""

from typing import List, Optional
from datetime import date
import re

from bs4 import BeautifulSoup

from hansard_tales.scrapers.base import BaseScraper, DataCollectionError
from hansard_tales.models.base import Chamber


class HansardScraper(BaseScraper):
    """
    Scraper for Hansard documents.
    
    This scraper extracts Hansard PDF links from parliament.go.ke
    by parsing HTML tables on the Hansard pages with pagination support.
    
    Example:
        >>> config = ScraperConfig()
        >>> scraper = HansardScraper(config)
        >>> documents = scraper.scrape(Chamber.NATIONAL_ASSEMBLY)
    """
    
    def get_document_urls(
        self,
        chamber: Chamber,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        parliament_term: int = 2022
    ) -> List[str]:
        """
        Get Hansard PDF URLs from parliament.go.ke tables with pagination.
        
        This method extracts PDF links from all pages of the Hansard listing by:
        1. Fetching the first page to determine total pages
        2. Iterating through all pages
        3. Extracting PDF links using CSS selectors
        
        Args:
            chamber: Parliamentary chamber (National Assembly or Senate)
            start_date: Optional start date for filtering (not implemented yet)
            end_date: Optional end date for filtering (not implemented yet)
            parliament_term: Parliament term start year (default: 2022)
            
        Returns:
            List of Hansard PDF URLs from all pages
            
        Raises:
            DataCollectionError: If no documents found (indicates HTML/CSS changes)
        """
        # Construct base URL based on chamber
        if chamber == Chamber.NATIONAL_ASSEMBLY:
            base_path = "/the-national-assembly/house-business/hansard"
        elif chamber == Chamber.SENATE:
            base_path = "/the-senate/house-business/hansard"
        else:
            raise ValueError(f"Unknown chamber: {chamber}")
        
        urls = []
        
        # Fetch first page to determine total pages
        first_page_url = f"{self.config.base_url}{base_path}?field_parliament_value={parliament_term}&page=0"
        response = self.session.get(first_page_url, timeout=self.config.timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Determine total number of pages from pagination
        total_pages = self._get_total_pages(soup)
        
        # Extract URLs from first page
        page_urls = self._extract_urls_from_page(soup)
        urls.extend(page_urls)
        
        # Fetch remaining pages
        for page_num in range(1, total_pages):
            # Add delay to avoid rate limiting
            import time
            time.sleep(self.config.retry_delay)
            
            page_url = f"{self.config.base_url}{base_path}?field_parliament_value={parliament_term}&page={page_num}"
            response = self.session.get(page_url, timeout=self.config.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_urls = self._extract_urls_from_page(soup)
            urls.extend(page_urls)
        
        # Fail fast if no documents found - likely indicates HTML/CSS changes
        if not urls:
            raise DataCollectionError(
                f"No Hansard documents found at {first_page_url}. "
                "This may indicate that the website structure has changed. "
                "Please verify the page HTML and update the scraper accordingly."
            )
        
        return urls
    
    def _get_total_pages(self, soup: BeautifulSoup) -> int:
        """
        Extract total number of pages from pagination element.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Total number of pages (minimum 1)
        """
        # Look for pagination using CSS selector
        # Common patterns: nav.pager, ul.pager, div.pager
        pager = soup.select_one('nav.pager, ul.pager, div.pager')
        
        if not pager:
            # No pagination found, assume single page
            return 1
        
        # Find all page links
        page_links = pager.select('a')
        
        if not page_links:
            return 1
        
        # Extract page numbers from links
        max_page = 0
        for link in page_links:
            href = link.get('href', '')
            # Look for page parameter in URL
            match = re.search(r'page=(\d+)', href)
            if match:
                page_num = int(match.group(1))
                max_page = max(max_page, page_num)
        
        # Total pages is max page number + 1 (zero-indexed)
        return max_page + 1 if max_page > 0 else 1
    
    def _extract_urls_from_page(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract PDF URLs from a single page using CSS selectors.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of PDF URLs found on the page
        """
        urls = []
        
        # Use CSS selector: table.cols-2 td.views-field-field-pdf a[href$=".pdf"]
        pdf_links = soup.select('table.cols-2 td.views-field-field-pdf a[href$=".pdf"]')
        
        for link in pdf_links:
            href = link.get('href', '')
            
            if href:
                # Convert relative URLs to absolute
                if href.startswith('http'):
                    full_url = href
                else:
                    # Remove leading slash if present
                    href = href.lstrip('/')
                    full_url = f"{self.config.base_url}/{href}"
                
                urls.append(full_url)
        
        return urls
    
    def extract_metadata(self, url: str, content: bytes) -> dict:
        """
        Extract metadata from Hansard PDF.
        
        Extracts date and period from filename title.
        Example: "Hansard Report - Tuesday, 4th November 2025 (P).pdf"
        
        Args:
            url: Document URL
            content: Document content (not used for filename-based extraction)
            
        Returns:
            Dictionary containing:
                - document_type: Always "hansard"
                - original_filename: Original filename from URL
                - date: Extracted date in YYYY-MM-DD format
                - period: Session period (P=Morning, A=Afternoon, E=Evening)
        """
        # Extract filename from URL (URL-decoded)
        import urllib.parse
        filename = urllib.parse.unquote(url.split('/')[-1])
        
        metadata = {
            'document_type': 'hansard',
            'original_filename': filename,
        }
        
        # Extract date from filename
        # Pattern: "Hansard Report - Tuesday, 4th November 2025 (P).pdf"
        date_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(\w+)\s+(\d{4})', filename)
        if date_match:
            day, month_name, year = date_match.groups()
            # Convert month name to number
            month_map = {
                'january': '01', 'february': '02', 'march': '03', 'april': '04',
                'may': '05', 'june': '06', 'july': '07', 'august': '08',
                'september': '09', 'october': '10', 'november': '11', 'december': '12'
            }
            month = month_map.get(month_name.lower(), '01')
            metadata['date'] = f"{year}-{month}-{day.zfill(2)}"
            metadata['year'] = year
            metadata['month'] = month
            metadata['day'] = day.zfill(2)
        
        # Extract period (P=Morning, A=Afternoon, E=Evening)
        period_match = re.search(r'\(([APE])\)', filename)
        if period_match:
            metadata['period'] = period_match.group(1)
        
        return metadata
    
    def _generate_filename(self, url: str) -> str:
        """
        Generate standardized filename from URL.
        
        Format: hansard_YYYYMMDD_<P|A|E>.pdf
        Example: hansard_20241104_P.pdf
        
        Args:
            url: Document URL
            
        Returns:
            Standardized filename
        """
        import urllib.parse
        original_filename = urllib.parse.unquote(url.split('/')[-1])
        
        # Extract date and period from original filename
        date_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(\w+)\s+(\d{4})', original_filename)
        period_match = re.search(r'\(([APE])\)', original_filename)
        
        if date_match and period_match:
            day, month_name, year = date_match.groups()
            period = period_match.group(1)
            
            # Convert month name to number
            month_map = {
                'january': '01', 'february': '02', 'march': '03', 'april': '04',
                'may': '05', 'june': '06', 'july': '07', 'august': '08',
                'september': '09', 'october': '10', 'november': '11', 'december': '12'
            }
            month = month_map.get(month_name.lower(), '01')
            
            return f"hansard_{year}{month}{day.zfill(2)}_{period}.pdf"
        
        # Fallback to original filename if parsing fails
        return original_filename
