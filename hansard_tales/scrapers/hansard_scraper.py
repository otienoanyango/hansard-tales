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
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

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
        
        # Initialize period extractor and filename generator
        self.period_extractor = PeriodOfDayExtractor()
        self.filename_generator = FilenameGenerator()
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HansardTales/1.0 (Educational Project)'
        })
    
    def fetch_page(self, url: str, retry_count: int = 0) -> Optional[str]:
        """
        Fetch a web page with retry logic.
        
        Args:
            url: URL to fetch
            retry_count: Current retry attempt
            
        Returns:
            HTML content or None if failed
        """
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            return response.text
            
        except requests.RequestException as e:
            logger.warning(f"Request failed: {e}")
            
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                return self.fetch_page(url, retry_count + 1)
            
            logger.error(f"Failed after {self.max_retries} retries")
            return None
    
    def extract_hansard_links(self, html: str) -> List[Dict[str, str]]:
        """
        Extract Hansard PDF links and metadata from HTML.
        
        Args:
            html: HTML content
            
        Returns:
            List of dictionaries with PDF metadata
        """
        soup = BeautifulSoup(html, 'html.parser')
        hansard_items = []
        
        # Find all PDF links (adjust selectors based on actual site structure)
        # This is a generic implementation - may need adjustment
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        
        for link in pdf_links:
            href = link.get('href', '')
            if not href:
                continue
            
            # Make absolute URL
            pdf_url = urljoin(self.BASE_URL, href)
            
            # Extract title from link text or parent elements
            title = link.get_text(strip=True)
            if not title:
                # Try to get title from parent
                parent = link.find_parent(['div', 'li', 'td'])
                if parent:
                    title = parent.get_text(strip=True)
            
            # Try to extract date from title or URL
            date = self.extract_date(title) or self.extract_date(href)
            
            hansard_items.append({
                'url': pdf_url,
                'title': title,
                'date': date,
                'filename': Path(urlparse(pdf_url).path).name
            })
        
        return hansard_items
    
    def extract_date(self, text: str) -> Optional[str]:
        """
        Extract date from text using dateparser (preferred) or regex patterns (fallback).
        
        Args:
            text: Text to search for dates
            
        Returns:
            Date string in YYYY-MM-DD format or None
        """
        if not text:
            return None
        
        # Try dateparser first (handles many formats including British dates)
        if DATEPARSER_AVAILABLE:
            try:
                # Use search_dates to find dates within text
                from dateparser.search import search_dates
                
                results = search_dates(
                    text,
                    settings={
                        'PREFER_DATES_FROM': 'past',
                        'STRICT_PARSING': False,
                        'DATE_ORDER': 'DMY'  # British/Kenyan format: day-month-year
                    },
                    languages=['en']
                )
                
                if results:
                    # Get the first date found
                    date_str, date_obj = results[0]
                    return date_obj.strftime('%Y-%m-%d')
            except Exception as e:
                logger.debug(f"dateparser failed: {e}, falling back to regex")
        
        # Fallback to regex patterns
        
        # Pattern: DD/MM/YYYY or DD-MM-YYYY
        pattern1 = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        match = re.search(pattern1, text)
        if match:
            day, month, year = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Pattern: YYYY-MM-DD
        pattern2 = r'(\d{4})-(\d{1,2})-(\d{1,2})'
        match = re.search(pattern2, text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Pattern: Month DD, YYYY (American format)
        pattern3 = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})'
        match = re.search(pattern3, text, re.IGNORECASE)
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
        
        # Pattern: DD Month YYYY (British/Kenyan format)
        pattern4 = r'(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December),?\s+(\d{4})'
        match = re.search(pattern4, text, re.IGNORECASE)
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
                logger.warning(f"Database query failed: {e}")
        
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
            logger.warning(f"Could not track download in database: {e}")
    
    def download_pdf(
        self,
        url: str,
        title: str,
        date: str
    ) -> bool:
        """
        Download PDF with enhanced metadata tracking.
        
        Steps:
        1. Extract period-of-day from title
        2. Generate standardized filename
        3. Check for existing download
        4. Download if needed
        5. Track in database with metadata
        
        Args:
            url: PDF URL
            title: PDF title
            date: PDF date (YYYY-MM-DD format)
            
        Returns:
            True if successful (downloaded or skipped), False if failed
            
        Example:
            >>> scraper = HansardScraper()
            >>> success = scraper.download_pdf(
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
            return False
        
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
            return True
        
        # Download the file
        logger.info(f"Downloading: filename={filename}, reason={reason}")
        
        try:
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Collect content
            content = b''.join(response.iter_content(chunk_size=8192))
            
            # Write to storage
            self.storage.write(filename, content)
            
            file_size = len(content)
            logger.info(f"Download successful: URL={url}, filename={filename}, size={file_size}, result=success")
            
            # Track in database
            self._track_download(url, filename, date, period_of_day, None)
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            return True
            
        except requests.RequestException as e:
            logger.error(f"Download failed: URL={url}, filename={filename}, error={str(e)}, result=failed", exc_info=True)
            # Clean up partial download if it exists
            try:
                if self.storage.exists(filename):
                    self.storage.delete(filename)
                    logger.debug(f"Cleaned up partial download: {filename}")
            except Exception as cleanup_error:
                logger.warning(f"Could not clean up partial download: {cleanup_error}")
            return False
    
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
    
    def scrape_all(self, max_pages: int = 5) -> List[Dict[str, str]]:
        """
        Scrape multiple pages of Hansard listings.
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of all Hansard metadata
        """
        all_hansards = []
        
        for page_num in range(1, max_pages + 1):
            logger.info(f"Scraping page {page_num}/{max_pages}")
            
            hansards = self.scrape_hansard_page(page_num)
            
            if not hansards:
                logger.info(f"No more Hansards found on page {page_num}")
                break
            
            all_hansards.extend(hansards)
            logger.info(f"Found {len(hansards)} Hansards on page {page_num}")
        
        return all_hansards
    
    def download_all(self, hansards: List[Dict[str, str]]) -> Dict[str, int]:
        """
        Download all Hansard PDFs.
        
        Args:
            hansards: List of Hansard metadata
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'total': len(hansards),
            'downloaded': 0,
            'skipped': 0,
            'failed': 0
        }
        
        for i, hansard in enumerate(hansards, 1):
            logger.info(f"Processing {i}/{stats['total']}: {hansard['title']}")
            
            # Use new download_pdf signature with title and date
            if self.download_pdf(
                hansard['url'],
                hansard['title'],
                hansard.get('date', '')
            ):
                # Check if file was actually downloaded or skipped
                # Extract filename from title and date
                date = hansard.get('date', '')
                if date:
                    date_compact = date.replace('-', '')
                    existing_files = self.storage.list_files(f"hansard_{date_compact}")
                    if existing_files:
                        stats['downloaded'] += 1
                    else:
                        stats['skipped'] += 1
                else:
                    stats['skipped'] += 1
            else:
                stats['failed'] += 1
        
        return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape Hansard PDFs from parliament.go.ke"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Maximum number of pages to scrape (default: 5)"
    )
    parser.add_argument(
        "--storage-dir",
        default="data/pdfs/hansard",
        help="Storage directory for PDFs (default: data/pdfs/hansard)"
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)"
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
    
    # Scrape Hansard listings
    logger.info("Starting Hansard scraper...")
    hansards = scraper.scrape_all(max_pages=args.max_pages)
    
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
    logger.info("\n" + "="*50)
    logger.info("SCRAPING SUMMARY")
    logger.info("="*50)
    logger.info(f"Total PDFs found:     {stats['total']}")
    logger.info(f"Successfully downloaded: {stats['downloaded']}")
    logger.info(f"Already existed:      {stats['skipped']}")
    logger.info(f"Failed:               {stats['failed']}")
    logger.info("="*50)
    
    sys.exit(0 if stats['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
