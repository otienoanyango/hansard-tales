"""
Votes & Proceedings scraper for National Assembly and Senate documents.

This module implements the scraper for Votes & Proceedings documents from
parliament.go.ke, extracting PDF links from HTML tables.
"""

from typing import List, Optional
from datetime import date
import re

from bs4 import BeautifulSoup

from hansard_tales.scrapers.base import BaseScraper, DataCollectionError
from hansard_tales.models.base import Chamber


class VotesScraper(BaseScraper):
    """
    Scraper for Votes & Proceedings documents.
    
    This scraper extracts Votes & Proceedings PDF links from parliament.go.ke
    by parsing HTML tables on the Votes & Proceedings pages.
    
    Example:
        >>> config = ScraperConfig()
        >>> scraper = VotesScraper(config)
        >>> documents = scraper.scrape(Chamber.NATIONAL_ASSEMBLY)
    """
    
    def get_document_urls(
        self,
        chamber: Chamber,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[str]:
        """
        Get Votes & Proceedings PDF URLs from parliament.go.ke tables.
        
        This method extracts PDF links from the Votes & Proceedings page by:
        1. Fetching the Votes & Proceedings page HTML
        2. Finding tables containing document links
        3. Extracting PDF links from table rows
        4. Validating links are Votes & Proceedings documents
        
        Args:
            chamber: Parliamentary chamber (National Assembly or Senate)
            start_date: Optional start date for filtering (not implemented yet)
            end_date: Optional end date for filtering (not implemented yet)
            
        Returns:
            List of Votes & Proceedings PDF URLs
            
        Raises:
            DataCollectionError: If no documents found (indicates HTML/CSS changes)
        """
        # Construct base URL based on chamber
        if chamber == Chamber.NATIONAL_ASSEMBLY:
            base_url = f"{self.config.base_url}/the-national-assembly/house-business/votes-and-proceedings"
        elif chamber == Chamber.SENATE:
            base_url = f"{self.config.base_url}/the-senate/house-business/votes-and-proceedings"
        else:
            raise ValueError(f"Unknown chamber: {chamber}")
        
        # Fetch page HTML
        response = self.session.get(base_url, timeout=self.config.timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        urls = []
        
        # Find tables containing Votes & Proceedings documents
        # Try specific class first, then fallback to all tables
        tables = soup.find_all('table', class_='views-table')
        
        if not tables:
            # Fallback: look for any table containing PDF links
            tables = soup.find_all('table')
        
        # Extract PDF links from tables
        for table in tables:
            for row in table.find_all('tr'):
                for link in row.find_all('a', href=True):
                    href = link['href']
                    
                    # Validate it's a PDF link
                    if not href.endswith('.pdf'):
                        continue
                    
                    # Additional validation: check if it's a Votes & Proceedings document
                    # by looking at the link text or URL pattern
                    link_text = link.get_text().lower()
                    href_lower = href.lower()
                    
                    # Check for votes/proceedings keywords
                    is_votes_doc = (
                        'vote' in link_text or 
                        'vote' in href_lower or 
                        'proceeding' in link_text or
                        'proceeding' in href_lower
                    )
                    
                    if is_votes_doc:
                        # Convert relative URLs to absolute
                        if href.startswith('http'):
                            full_url = href
                        else:
                            # Remove leading slash if present
                            href = href.lstrip('/')
                            full_url = f"{self.config.base_url}/{href}"
                        
                        urls.append(full_url)
        
        # Fail fast if no documents found - likely indicates HTML/CSS changes
        if not urls:
            raise DataCollectionError(
                f"No Votes & Proceedings documents found at {base_url}. "
                "This may indicate that the website structure has changed. "
                "Please verify the page HTML and update the scraper accordingly."
            )
        
        return urls
    
"""
Votes & Proceedings scraper for National Assembly and Senate documents.

This module implements the scraper for Votes & Proceedings documents from
parliament.go.ke, extracting PDF links from HTML tables with pagination support.
"""

from typing import List, Optional
from datetime import date, datetime
import re

from bs4 import BeautifulSoup

from hansard_tales.scrapers.base import BaseScraper, DataCollectionError
from hansard_tales.models.base import Chamber


class VotesScraper(BaseScraper):
    """
    Scraper for Votes & Proceedings documents.
    
    This scraper extracts Votes & Proceedings PDF links from parliament.go.ke
    by parsing HTML tables on the Votes & Proceedings pages with pagination support.
    
    Example:
        >>> config = ScraperConfig()
        >>> scraper = VotesScraper(config)
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
        Get Votes & Proceedings PDF URLs from parliament.go.ke tables with pagination.
        
        This method extracts PDF links from all pages of the Votes listing by:
        1. Fetching the first page to determine total pages
        2. Iterating through all pages
        3. Extracting PDF links using CSS selectors
        
        Args:
            chamber: Parliamentary chamber (National Assembly or Senate)
            start_date: Optional start date for filtering (not implemented yet)
            end_date: Optional end date for filtering (not implemented yet)
            parliament_term: Parliament term start year (default: 2022)
            
        Returns:
            List of Votes & Proceedings PDF URLs from all pages
            
        Raises:
            DataCollectionError: If no documents found (indicates HTML/CSS changes)
        """
        # Construct base URL based on chamber
        if chamber == Chamber.NATIONAL_ASSEMBLY:
            base_path = "/the-national-assembly/house-business/votes-proceedings"
        elif chamber == Chamber.SENATE:
            base_path = "/the-senate/house-business/votes-proceedings"
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
                f"No Votes & Proceedings documents found at {first_page_url}. "
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
        pager = soup.select_one('nav.pager, ul.pager, div.pager')
        
        if not pager:
            return 1
        
        # Find all page links
        page_links = pager.select('a')
        
        if not page_links:
            return 1
        
        # Extract page numbers from links
        max_page = 0
        for link in page_links:
            href = link.get('href', '')
            match = re.search(r'page=(\d+)', href)
            if match:
                page_num = int(match.group(1))
                max_page = max(max_page, page_num)
        
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
                    href = href.lstrip('/')
                    full_url = f"{self.config.base_url}/{href}"
                
                urls.append(full_url)
        
        return urls
    
    def extract_metadata(self, url: str, content: bytes) -> dict:
        """
        Extract metadata from Votes & Proceedings PDF.
        
        Extracts date and time from filename title.
        Example: "Tuesday ,November 4, 2025 at 2.30pm.pdf"
        
        Args:
            url: Document URL
            content: Document content (not used for filename-based extraction)
            
        Returns:
            Dictionary containing:
                - document_type: Always "votes"
                - original_filename: Original filename from URL
                - date: Extracted date in YYYY-MM-DD format
                - time: Extracted time in HH:MM format
                - datetime_iso: ISO 8601 datetime string
        """
        # Extract filename from URL (URL-decoded)
        import urllib.parse
        filename = urllib.parse.unquote(url.split('/')[-1])
        
        metadata = {
            'document_type': 'votes',
            'original_filename': filename,
        }
        
        # Extract date from filename
        # Pattern: "Tuesday ,November 4, 2025 at 2.30pm.pdf"
        date_match = re.search(r'(\w+)\s*,?\s*(\d{1,2})\s*,?\s*(\d{4})', filename)
        if date_match:
            month_name, day, year = date_match.groups()
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
        
        # Extract time from filename
        # Pattern: "at 2.30pm" or "at 10.00am"
        time_match = re.search(r'at\s+(\d{1,2})\.(\d{2})\s*(am|pm)', filename, re.IGNORECASE)
        if time_match:
            hour, minute, meridiem = time_match.groups()
            hour = int(hour)
            
            # Convert to 24-hour format
            if meridiem.lower() == 'pm' and hour != 12:
                hour += 12
            elif meridiem.lower() == 'am' and hour == 12:
                hour = 0
            
            metadata['time'] = f"{hour:02d}:{minute}"
            
            # Create ISO 8601 datetime if we have both date and time
            if 'date' in metadata:
                metadata['datetime_iso'] = f"{metadata['date']}T{hour:02d}:{minute}:00Z"
        
        return metadata
    
    def _generate_filename(self, url: str) -> str:
        """
        Generate standardized filename from URL.
        
        Format: votes_YYYYMMDDTHHMMZ.pdf
        Example: votes_20241104T143000Z.pdf
        
        Args:
            url: Document URL
            
        Returns:
            Standardized filename
        """
        import urllib.parse
        original_filename = urllib.parse.unquote(url.split('/')[-1])
        
        # Extract date from filename
        date_match = re.search(r'(\w+)\s*,?\s*(\d{1,2})\s*,?\s*(\d{4})', original_filename)
        time_match = re.search(r'at\s+(\d{1,2})\.(\d{2})\s*(am|pm)', original_filename, re.IGNORECASE)
        
        if date_match and time_match:
            month_name, day, year = date_match.groups()
            hour, minute, meridiem = time_match.groups()
            
            # Convert month name to number
            month_map = {
                'january': '01', 'february': '02', 'march': '03', 'april': '04',
                'may': '05', 'june': '06', 'july': '07', 'august': '08',
                'september': '09', 'october': '10', 'november': '11', 'december': '12'
            }
            month = month_map.get(month_name.lower(), '01')
            
            # Convert to 24-hour format
            hour = int(hour)
            if meridiem.lower() == 'pm' and hour != 12:
                hour += 12
            elif meridiem.lower() == 'am' and hour == 12:
                hour = 0
            
            return f"votes_{year}{month}{day.zfill(2)}T{hour:02d}{minute}00Z.pdf"
        
        # Fallback to original filename if parsing fails
        return original_filename
