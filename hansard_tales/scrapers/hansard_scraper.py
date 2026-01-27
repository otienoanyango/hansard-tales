#!/usr/bin/env python3
"""
Hansard PDF scraper for parliament.go.ke

This script scrapes the Parliament of Kenya website for Hansard PDFs,
extracts metadata, and downloads them to the local data directory.

Usage:
    python scripts/scraper.py [--max-pages N] [--output-dir PATH]
"""

import argparse
import logging
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from hansard_tales.storage.base import StorageBackend
from hansard_tales.storage.filesystem import FilesystemStorage
from hansard_tales.processors.period_extractor import PeriodOfDayExtractor
from hansard_tales.utils.filename_generator import FilenameGenerator

# Try to import dateparser for robust date parsing
try:
    import dateparser
    DATEPARSER_AVAILABLE = True
except ImportError:
    DATEPARSER_AVAILABLE = False
    logger.warning("dateparser not installed. Date parsing will use regex patterns only.")
    logger.warning("Install with: pip install dateparser")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HansardScraper:
    """Scraper for Parliament of Kenya Hansard PDFs."""
    
    BASE_URL = "https://parliament.go.ke"
    HANSARD_URL = f"{BASE_URL}/the-national-assembly/house-business/hansard"
    
    def __init__(
        self,
        storage: Optional[StorageBackend] = None,
        db_path: Optional[str] = None,
        rate_limit_delay: float = 1.0,
        max_retries: int = 3,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """
        Initialize the scraper.
        
        Args:
            storage: Storage backend for PDFs (default: FilesystemStorage("data/pdfs/hansard"))
            db_path: Path to database for tracking downloads
            rate_limit_delay: Delay between requests in seconds
            max_retries: Maximum number of retry attempts
            start_date: Start date for filtering (YYYY-MM-DD format)
            end_date: End date for filtering (YYYY-MM-DD format)
        """
        # Initialize storage backend
        if storage is None:
            storage = FilesystemStorage("data/pdfs/hansard")
        self.storage = storage
        
        self.db_path = db_path
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.start_date = start_date
        self.end_date = end_date
        
        # Initialize database if path provided
        if self.db_path:
            self._ensure_database_initialized()
        
        # Initialize period extractor and filename generator
        self.period_extractor = PeriodOfDayExtractor()
        self.filename_generator = FilenameGenerator()
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HansardTales/1.0 (Educational Project)'
        })
    
    def _ensure_database_initialized(self) -> None:
        """
        Ensure database exists and has required tables with correct schema.
        
        Logic:
        1. If database doesn't exist: Create it with full schema
        2. If database exists but table missing: Create the table
        3. If database exists with table: Verify schema is correct
        
        Raises:
            RuntimeError: If database cannot be initialized or has wrong schema
        """
        from hansard_tales.database.init_db import initialize_database
        
        db_file = Path(self.db_path)
        
        # If database doesn't exist, create it with full schema
        if not db_file.exists():
            logger.info(f"Database not found, initializing: {self.db_path}")
            if not initialize_database(self.db_path):
                raise RuntimeError(f"Failed to initialize database: {self.db_path}")
            logger.info(f"Database created successfully: {self.db_path}")
            return
        
        # Database exists - verify and fix if needed
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if downloaded_pdfs table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='downloaded_pdfs'
            """)
            
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Table missing - create it with correct schema
                logger.info(f"Table 'downloaded_pdfs' missing, creating it...")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS downloaded_pdfs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        original_url TEXT UNIQUE NOT NULL,
                        file_path TEXT UNIQUE NOT NULL,
                        date DATE NOT NULL,
                        period_of_day TEXT CHECK(period_of_day IN ('A', 'P', 'E')),
                        session_id INTEGER REFERENCES hansard_sessions(id),
                        downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        file_size INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                logger.info(f"Table 'downloaded_pdfs' created successfully")
            else:
                # Table exists - verify schema
                cursor.execute("PRAGMA table_info(downloaded_pdfs)")
                columns = {row[1]: row[2] for row in cursor.fetchall()}
                
                # Check for required columns (use original_url as per init_db.py schema)
                required_columns = {
                    'id': 'INTEGER',
                    'original_url': 'TEXT',
                    'file_path': 'TEXT',
                    'date': 'DATE',
                    'period_of_day': 'TEXT'
                }
                
                # Check for missing columns
                missing_columns = set(required_columns.keys()) - set(columns.keys())
                if missing_columns:
                    conn.close()
                    raise RuntimeError(
                        f"Table 'downloaded_pdfs' has incorrect schema. "
                        f"Missing columns: {', '.join(missing_columns)}. "
                        f"Please backup and recreate the database."
                    )
                
                logger.debug(f"Database schema verified: {self.db_path}")
            
            conn.close()
            logger.info(f"Database ready: {self.db_path}")
            
        except sqlite3.Error as e:
            raise RuntimeError(f"Database verification/initialization failed: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True
    )
    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a web page with automatic retry logic using tenacity.
        
        Retries up to 3 times with exponential backoff (1s, 2s, 3s max).
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if failed
            
        Raises:
            requests.RequestException: If all retries fail
        """
        logger.info(f"Fetching: {url}")
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        
        # Rate limiting
        time.sleep(self.rate_limit_delay)
        
        return response.text
    
    def extract_max_page(self, html: str) -> Optional[int]:
        """
        Extract maximum page number from pagination HTML.
        
        Looks for the "Last page" link in pagination:
        <li class="pager__item pager__item--last">
            <a href="?title=%20&field_parliament_value=2022&page=18">
        
        Args:
            html: HTML content
            
        Returns:
            Maximum page number or None if not found
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the last page link
        last_page_link = soup.find('li', class_='pager__item--last')
        if not last_page_link:
            logger.debug("No pagination found, assuming single page")
            return 1
        
        # Extract href
        link = last_page_link.find('a')
        if not link or not link.get('href'):
            logger.debug("No href in last page link")
            return 1
        
        href = link.get('href')
        
        # Parse query parameters
        try:
            # Extract page parameter from URL
            match = re.search(r'[?&]page=(\d+)', href)
            if match:
                max_page = int(match.group(1)) + 1  # Page numbers are 0-indexed in URL
                logger.info(f"Detected max page: {max_page}")
                return max_page
        except (ValueError, AttributeError) as e:
            logger.warning(f"Could not parse max page from {href}: {e}")
        
        return None
    
    def extract_hansard_links(self, html: str) -> List[Dict[str, str]]:
        """
        Extract Hansard PDF links and metadata from HTML.
        
        Uses CSS selectors to target PDF links within the visible table (col-2)
        to avoid duplicate links from hidden tables (col-0) or other page elements.
        
        Args:
            html: HTML content
            
        Returns:
            List of dictionaries with PDF metadata (deduplicated by URL)
            
        Raises:
            RuntimeError: If no PDF links found with CSS selector (indicates page structure changed)
        """
        soup = BeautifulSoup(html, 'html.parser')
        hansard_items = []
        seen_urls = set()  # Track URLs to avoid duplicates
        
        # Use CSS selector to find all PDF links within the visible table
        # Selector: table.cols-2 td.views-field-field-pdf a[href$=".pdf"]
        pdf_links = soup.select('table.cols-2 td.views-field-field-pdf a[href$=".pdf"]')
        
        for link in pdf_links:
            href = link.get('href', '')
            if not href:
                continue
            
            # Make absolute URL
            pdf_url = urljoin(self.BASE_URL, href)
            
            # Skip if we've already seen this URL
            if pdf_url in seen_urls:
                logger.debug(f"Skipping duplicate URL: {pdf_url}")
                continue
            
            seen_urls.add(pdf_url)
            
            # Extract title from the <a> element text
            title = link.get_text(strip=True)
            
            # Skip non-Hansard documents (Order Papers, etc.)
            if 'order paper' in title.lower():
                logger.debug(f"Skipping non-Hansard document: {title}")
                continue
            
            # Try to extract date from title or URL
            date = self.extract_date(title) or self.extract_date(href)
            
            hansard_items.append({
                'url': pdf_url,
                'title': title,
                'date': date,
                'filename': Path(urlparse(pdf_url).path).name
            })
        
        # Fail if no links found - indicates page structure changed
        if not pdf_links:
            raise RuntimeError(
                "No PDF links found with CSS selector 'table.cols-2 td.views-field-field-pdf a[href$=\".pdf\"]'. "
                "The parliament.go.ke page structure may have changed."
            )
        
        return hansard_items
    
    def extract_date(self, text: str) -> Optional[str]:
        """
        Extract date from text using dateparser with British locale.
        
        Uses dateparser with British/Kenyan date format (DMY) as primary method,
        with regex patterns as fallback for edge cases.
        
        Args:
            text: Text to search for dates
            
        Returns:
            Date string in YYYY-MM-DD format or None
        """
        if not text:
            return None
        
        # Try dateparser first with British locale settings
        if DATEPARSER_AVAILABLE:
            try:
                # Use search_dates to find dates within text
                from dateparser.search import search_dates
                
                results = search_dates(
                    text,
                    settings={
                        'PREFER_DATES_FROM': 'past',
                        'STRICT_PARSING': False,
                        'DATE_ORDER': 'DMY',  # British/Kenyan format: day-month-year
                        'PREFER_DAY_OF_MONTH': 'first',  # Interpret ambiguous dates as DMY
                        'PREFER_LOCALE_DATE_ORDER': True,  # Use locale date order
                        'RETURN_AS_TIMEZONE_AWARE': False,
                    },
                    languages=['en-GB', 'en']  # British English first, then general English
                )
                
                if results:
                    # Get the first date found
                    date_str, date_obj = results[0]
                    return date_obj.strftime('%Y-%m-%d')
            except Exception as e:
                logger.debug(f"dateparser failed: {e}, falling back to regex")
        
        # Fallback to regex patterns for edge cases
        
        # Pattern: YYYY-MM-DD (ISO format - unambiguous)
        pattern_iso = r'(\d{4})-(\d{1,2})-(\d{1,2})'
        match = re.search(pattern_iso, text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Pattern: DD/MM/YYYY or DD-MM-YYYY (British format)
        pattern_dmy = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        match = re.search(pattern_dmy, text)
        if match:
            day, month, year = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Pattern: DD Month YYYY (British/Kenyan format with month name)
        pattern_british = r'(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December),?\s+(\d{4})'
        match = re.search(pattern_british, text, re.IGNORECASE)
        if match:
            day, month_name, year = match.groups()
            month_map = {
                'january': '01', 'february': '02', 'march': '03',
                'april': '04', 'may': '05', 'june': '06',
                'july': '07', 'august': '08', 'september': '09',
                'october': '10', 'november': '11', 'december': '12'
            }
            month = month_map.get(month_name.lower(), '01')
            return f"{year}-{month}-{day.zfill(2)}"
        
        # Pattern: Month DD, YYYY (American format - less common but supported)
        pattern_american = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})'
        match = re.search(pattern_american, text, re.IGNORECASE)
        if match:
            month_name, day, year = match.groups()
            month_map = {
                'january': '01', 'february': '02', 'march': '03',
                'april': '04', 'may': '05', 'june': '06',
                'july': '07', 'august': '08', 'september': '09',
                'october': '10', 'november': '11', 'december': '12'
            }
            month = month_map.get(month_name.lower(), '01')
            return f"{year}-{month}-{day.zfill(2)}"
        
        return None
    
    def _check_existing_download(
        self,
        url: str,
        filename: str,
        date: str,
        period_of_day: str
    ) -> Tuple[bool, str]:
        """
        Check if download should be skipped.
        
        Implements 4-case logic:
        1. File exists in storage AND in database: skip (file_exists_with_record)
        2. File exists in storage but NOT in database: insert record, skip (file_exists_without_record)
        3. File NOT in storage but in database: download (file_missing_redownload)
        4. File NOT in storage AND NOT in database: download (new_download)
        
        Args:
            url: PDF URL
            filename: Standardized filename
            date: PDF date (YYYY-MM-DD format)
            period_of_day: Period code ('A', 'P', or 'E')
            
        Returns:
            Tuple of (should_skip, reason)
            
        Raises:
            RuntimeError: If database query fails
            
        Example:
            >>> scraper = HansardScraper()
            >>> should_skip, reason = scraper._check_existing_download(url, filename, "2024-01-15", "P")
            >>> if should_skip:
            ...     logger.info(f"Skipping: {reason}")
        """
        # Check if file exists in storage
        file_exists = self.storage.exists(filename)
        
        # Check if URL exists in database
        db_record = None
        if self.db_path:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, file_path FROM downloaded_pdfs WHERE original_url = ?",
                    (url,)
                )
                db_record = cursor.fetchone()
                conn.close()
            except sqlite3.Error as e:
                raise RuntimeError(f"Database query failed: {e}")
        
        # Case 1: File exists in storage AND in database
        if file_exists and db_record:
            return (True, "file_exists_with_record")
        
        # Case 2: File exists in storage but NOT in database
        elif file_exists and not db_record:
            # Insert tracking record for existing file
            self._track_download(url, filename, date, period_of_day, None)
            return (True, "file_exists_without_record")
        
        # Case 3: File NOT in storage but in database
        elif not file_exists and db_record:
            # File missing but tracked - need to re-download
            return (False, "file_missing_redownload")
        
        # Case 4: Neither exists - download needed
        else:
            return (False, "new_download")
    
    def _track_download(
        self,
        url: str,
        file_path: str,
        date: Optional[str],
        period_of_day: Optional[str],
        session_id: Optional[int]
    ) -> None:
        """
        Track download in database with enhanced metadata.
        
        Uses INSERT OR REPLACE to handle duplicate URL entries.
        
        Args:
            url: PDF URL
            file_path: Storage path (relative to storage backend)
            date: PDF date (YYYY-MM-DD format)
            period_of_day: Period code ('A', 'P', or 'E')
            session_id: Session ID (if known, otherwise None)
            
        Raises:
            RuntimeError: If database operation fails
            
        Example:
            >>> scraper._track_download(
            ...     "http://example.com/pdf",
            ...     "hansard_20240101_A.pdf",
            ...     "2024-01-01",
            ...     "A",
            ...     None
            ... )
        """
        if not self.db_path:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get file size if file exists
            file_size = None
            if self.storage.exists(file_path):
                try:
                    file_size = self.storage.get_size(file_path)
                except Exception as e:
                    logger.warning(f"Could not get file size for {file_path}: {e}")
            
            # Insert or replace record
            cursor.execute("""
                INSERT OR REPLACE INTO downloaded_pdfs 
                (original_url, file_path, date, period_of_day, session_id, file_size, downloaded_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (url, file_path, date, period_of_day, session_id, file_size))
            
            conn.commit()
            conn.close()
            logger.debug(f"Tracked download in database: {file_path}")
        
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to track download in database: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True
    )
    def _download_pdf_with_retry(self, url: str, timeout: int = 60) -> bytes:
        """
        Download PDF content with automatic retry logic.
        
        Retries up to 3 times with exponential backoff (1s, 2s, 4s, max 10s).
        
        Args:
            url: PDF URL
            timeout: Request timeout in seconds
            
        Returns:
            PDF content as bytes
            
        Raises:
            requests.RequestException: If all retries fail
        """
        response = self.session.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Collect content
        content = b''.join(response.iter_content(chunk_size=8192))
        return content
    
    def download_pdf(
        self,
        url: str,
        title: str,
        date: str
    ) -> tuple[bool, str]:
        """
        Download PDF with enhanced metadata tracking.
        
        Steps:
        1. Check if date is within specified range (if filters set)
        2. Extract period-of-day from title
        3. Generate standardized filename
        4. Check for existing download
        5. Download if needed (with retry logic)
        6. Track in database with metadata
        
        Args:
            url: PDF URL
            title: PDF title
            date: PDF date (YYYY-MM-DD format)
            
        Returns:
            Tuple of (success: bool, action: str) where action is one of:
            - 'downloaded': File was downloaded
            - 'skipped_exists': File already exists
            - 'skipped_date': Date outside range
            - 'failed': Download failed
            
        Example:
            >>> scraper = HansardScraper()
            >>> success, action = scraper.download_pdf(
            ...     "http://example.com/hansard.pdf",
            ...     "Afternoon Session",
            ...     "2024-01-01"
            ... )
        """
        # Log download attempt
        logger.info(f"Download attempt: URL={url}, title={title}, date={date}")
        
        # Handle None or empty date
        if not date:
            logger.warning(f"No date provided for {url}, cannot generate standardized filename")
            return (False, 'failed')
        
        # Check if date is within specified range
        if self.start_date and date < self.start_date:
            logger.info(f"Skipping {url}: date {date} is before start_date {self.start_date}")
            return (True, 'skipped_date')
        
        if self.end_date and date > self.end_date:
            logger.info(f"Skipping {url}: date {date} is after end_date {self.end_date}")
            return (True, 'skipped_date')
        
        # Extract period-of-day from title
        period_of_day = self.period_extractor.extract_from_title(title)
        if not period_of_day:
            # Default to 'P' if not found in title
            period_of_day = 'P'
            logger.debug(f"No period-of-day found in title, defaulting to 'P'")
        
        # Generate standardized filename (base filename without suffix)
        # We don't pass existing_files here because duplicate detection
        # is handled by _check_existing_download based on URL
        date_compact = date.replace('-', '')
        filename = self.filename_generator.generate(
            date, period_of_day, []
        )
        
        # Check for existing download
        should_skip, reason = self._check_existing_download(url, filename, date, period_of_day)
        
        if should_skip:
            logger.info(f"Download skipped: URL={url}, filename={filename}, reason={reason}, result=skipped")
            return (True, 'skipped_exists')
        
        # Download the file with retry logic
        logger.info(f"Downloading: filename={filename}, reason={reason}")
        
        try:
            content = self._download_pdf_with_retry(url)
            
            # Write to storage
            self.storage.write(filename, content)
            
            file_size = len(content)
            logger.info(f"Download successful: URL={url}, filename={filename}, size={file_size}, result=success")
            
            # Track in database
            self._track_download(url, filename, date, period_of_day, None)
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            return (True, 'downloaded')
            
        except requests.RequestException as e:
            logger.error(f"Download failed after retries: URL={url}, filename={filename}, error={str(e)}, result=failed")
            # Clean up partial download if it exists
            try:
                if self.storage.exists(filename):
                    self.storage.delete(filename)
                    logger.debug(f"Cleaned up partial download: {filename}")
            except Exception as cleanup_error:
                logger.warning(f"Could not clean up partial download: {cleanup_error}")
            return (False, 'failed')
    
    def scrape_hansard_page(self, page_num: int = 1) -> List[Dict[str, str]]:
        """
        Scrape a single Hansard listing page.
        
        Args:
            page_num: Page number to scrape
            
        Returns:
            List of Hansard metadata dictionaries
        """
        # Construct page URL (adjust based on actual pagination)
        if page_num == 1:
            url = self.HANSARD_URL
        else:
            url = f"{self.HANSARD_URL}?page={page_num}"
        
        html = self.fetch_page(url)
        if not html:
            return []
        
        return self.extract_hansard_links(html)
    
    def scrape_all(self) -> List[Dict[str, str]]:
        """
        Scrape all pages of Hansard listings with intelligent pagination.
        
        Strategy:
        1. Fetch first page to determine max page from pagination
        2. Iterate through all pages until:
           - No more pages exist
           - All dates on a page are outside the end_date range
           - Network errors after retries
        
        Returns:
            List of all Hansard metadata
        """
        all_hansards = []
        
        # Fetch first page to determine max pages
        logger.info("Fetching first page to determine pagination...")
        try:
            first_page_html = self.fetch_page(self.HANSARD_URL)
            if not first_page_html:
                logger.error("Could not fetch first page")
                return []
            
            # Extract max page from pagination
            max_pages = self.extract_max_page(first_page_html)
            if max_pages:
                logger.info(f"Detected {max_pages} total pages")
            else:
                logger.info("Could not detect max pages, will scrape until empty page")
                max_pages = 999  # Large number as fallback
            
            # Extract hansards from first page
            first_page_hansards = self.extract_hansard_links(first_page_html)
            if first_page_hansards:
                all_hansards.extend(first_page_hansards)
                logger.info(f"Found {len(first_page_hansards)} Hansards on page 1")
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch first page after retries: {e}")
            return []
        
        # Iterate through remaining pages
        for page_num in range(2, max_pages + 1):
            logger.info(f"Scraping page {page_num}/{max_pages}")
            
            try:
                hansards = self.scrape_hansard_page(page_num)
                
                if not hansards:
                    logger.info(f"No Hansards found on page {page_num}, stopping")
                    break
                
                # Check if any date on this page is before start_date
                if self.start_date:
                    dates_on_page = [h.get('date') for h in hansards if h.get('date')]
                    if dates_on_page and any(date < self.start_date for date in dates_on_page):
                        logger.info(f"Found date before start_date {self.start_date} on page {page_num}, stopping pagination")
                        # Still add hansards from this page (will be filtered later)
                        all_hansards.extend(hansards)
                        break
                
                # Check if all dates on this page are after end_date
                if self.end_date:
                    dates_on_page = [h.get('date') for h in hansards if h.get('date')]
                    if dates_on_page and all(date > self.end_date for date in dates_on_page):
                        logger.info(f"All dates on page {page_num} are after end_date {self.end_date}, stopping")
                        break
                
                all_hansards.extend(hansards)
                logger.info(f"Found {len(hansards)} Hansards on page {page_num}")
                
            except requests.RequestException as e:
                logger.error(f"Failed to fetch page {page_num} after retries: {e}")
                logger.info("Stopping pagination due to network errors")
                break
        
        logger.info(f"Total Hansards found across all pages: {len(all_hansards)}")
        return all_hansards
    
    def download_all(self, hansards: List[Dict[str, str]]) -> Dict[str, int]:
        """
        Download all Hansard PDFs.
        
        Args:
            hansards: List of Hansard metadata
            
        Returns:
            Statistics dictionary with counts for:
            - total: Total hansards to process
            - downloaded: Successfully downloaded (new files)
            - skipped: Already existed (not downloaded again)
            - filtered: Filtered by date range
            - failed: Download failures
        """
        stats = {
            'total': len(hansards),
            'downloaded': 0,
            'skipped': 0,
            'filtered': 0,  # Filtered by date range
            'failed': 0
        }
        
        for i, hansard in enumerate(hansards, 1):
            logger.info(f"Processing {i}/{stats['total']}: {hansard['title']}")
            
            # Check if date is within range before attempting download
            date = hansard.get('date', '')
            if date:
                if self.start_date and date < self.start_date:
                    logger.info(f"Filtered: date {date} is before start_date {self.start_date}")
                    stats['filtered'] += 1
                    continue
                
                if self.end_date and date > self.end_date:
                    logger.info(f"Filtered: date {date} is after end_date {self.end_date}")
                    stats['filtered'] += 1
                    continue
            
            # Download PDF and get result
            success, action = self.download_pdf(
                hansard['url'],
                hansard['title'],
                date
            )
            
            # Update stats based on action
            if action == 'downloaded':
                stats['downloaded'] += 1
            elif action == 'skipped_exists':
                stats['skipped'] += 1
            elif action == 'skipped_date':
                stats['filtered'] += 1
            elif action == 'failed':
                stats['failed'] += 1
        
        return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape Hansard PDFs from parliament.go.ke"
    )
    parser.add_argument(
        "--storage-dir",
        default="data/pdfs/hansard",
        help="Storage directory for PDFs (default: data/pdfs/hansard)"
    )
    parser.add_argument(
        "--db-path",
        default="data/hansard.db",
        help="Path to database for tracking downloads (default: data/hansard.db)"
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--start-date",
        help="Start date for filtering (YYYY-MM-DD format)"
    )
    parser.add_argument(
        "--end-date",
        help="End date for filtering (YYYY-MM-DD format)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List PDFs without downloading"
    )
    
    args = parser.parse_args()
    
    # Initialize storage backend
    storage = FilesystemStorage(args.storage_dir)
    
    # Initialize scraper
    scraper = HansardScraper(
        storage=storage,
        db_path=args.db_path if not args.dry_run else None,
        rate_limit_delay=args.rate_limit,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    # Scrape Hansard listings (automatically detects max pages)
    logger.info("Starting Hansard scraper...")
    if args.start_date or args.end_date:
        logger.info(f"Date range filter: {args.start_date or 'any'} to {args.end_date or 'any'}")
    
    hansards = scraper.scrape_all()
    
    if not hansards:
        logger.warning("No Hansards found")
        sys.exit(1)
    
    logger.info(f"\nFound {len(hansards)} Hansard PDFs")
    
    # Display sample
    for hansard in hansards[:5]:
        logger.info(f"  - {hansard['title']} ({hansard['date']})")
    if len(hansards) > 5:
        logger.info(f"  ... and {len(hansards) - 5} more")
    
    if args.dry_run:
        logger.info("\nDry run - no downloads performed")
        sys.exit(0)
    
    # Download PDFs
    logger.info("\nDownloading PDFs...")
    stats = scraper.download_all(hansards)
    
    # Print summary
    # Calculate PDFs in date range (not filtered out)
    in_date_range = stats['downloaded'] + stats['skipped'] + stats['failed']
    
    logger.info("\n" + "="*50)
    logger.info("SCRAPING SUMMARY")
    logger.info("="*50)
    logger.info(f"Total URLs found:        {stats['total']}")
    logger.info(f"In date range:           {in_date_range}")
    logger.info(f"Successfully downloaded: {stats['downloaded']}")
    logger.info(f"Skipped (file exists):   {stats['skipped']}")
    logger.info(f"Failed:                  {stats['failed']}")
    logger.info("="*50)
    logger.info("Note: 'Skipped' count may exceed actual files on disk")
    logger.info("      due to duplicate URLs on parliament.go.ke")
    logger.info("="*50)
    
    sys.exit(0 if stats['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
