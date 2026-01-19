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
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


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
        output_dir: str = "data/pdfs",
        rate_limit_delay: float = 1.0,
        max_retries: int = 3
    ):
        """
        Initialize the scraper.
        
        Args:
            output_dir: Directory to save downloaded PDFs
            rate_limit_delay: Delay between requests in seconds
            max_retries: Maximum number of retry attempts
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        
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
        Extract date from text using regex patterns.
        
        Args:
            text: Text to search for dates
            
        Returns:
            Date string in YYYY-MM-DD format or None
        """
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
        
        # Pattern: Month DD, YYYY
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
        
        return None
    
    def download_pdf(self, url: str, filename: str) -> bool:
        """
        Download a PDF file.
        
        Args:
            url: PDF URL
            filename: Local filename to save
            
        Returns:
            True if successful, False otherwise
        """
        output_path = self.output_dir / filename
        
        # Skip if already downloaded
        if output_path.exists():
            logger.info(f"Already exists: {filename}")
            return True
        
        try:
            logger.info(f"Downloading: {filename}")
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Write to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✓ Downloaded: {filename} ({output_path.stat().st_size} bytes)")
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            return True
            
        except requests.RequestException as e:
            logger.error(f"Download failed: {e}")
            # Clean up partial download
            if output_path.exists():
                output_path.unlink()
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
            
            if self.download_pdf(hansard['url'], hansard['filename']):
                if (self.output_dir / hansard['filename']).stat().st_size > 0:
                    stats['downloaded'] += 1
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
        "--output-dir",
        default="data/pdfs",
        help="Output directory for PDFs (default: data/pdfs)"
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
    
    # Initialize scraper
    scraper = HansardScraper(
        output_dir=args.output_dir,
        rate_limit_delay=args.rate_limit
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
