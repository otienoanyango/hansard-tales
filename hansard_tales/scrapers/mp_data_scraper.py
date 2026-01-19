#!/usr/bin/env python3
"""
MP Data Scraper

Scrapes MP information from parliament.go.ke for specified parliamentary terms.
Extracts: name, constituency, county, party, status (elected/nominated), and photo URL.

Usage:
    python scripts/mp_data_scraper.py --term 2022 --output data/mps_13th_parliament.json
    python scripts/mp_data_scraper.py --term 2017 --output data/mps_12th_parliament.json
"""

import argparse
import json
import logging
import re
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MPDataScraper:
    """Scraper for MP data from parliament.go.ke"""
    
    BASE_URL = "https://parliament.go.ke"
    MP_LIST_URL = f"{BASE_URL}/the-national-assembly/mps"
    
    def __init__(self, term_start_year: int, delay: float = 1.0):
        """
        Initialize the scraper.
        
        Args:
            term_start_year: Start year of parliamentary term (e.g., 2022, 2017)
            delay: Delay between requests in seconds (default: 1.0)
        """
        self.term_start_year = term_start_year
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def build_url(self, page: int = 0) -> str:
        """
        Build URL for MP list page.
        
        Args:
            page: Page number (0-based)
            
        Returns:
            Full URL with query parameters
        """
        params = {
            'field_parliament_value': str(self.term_start_year),
            'field_name_value': ' ',
            'field_employment_history_value': '',
            'page': str(page)
        }
        
        param_str = '&'.join(f"{k}={v}" for k, v in params.items())
        return f"{self.MP_LIST_URL}?{param_str}"
    
    def fetch_page(self, page: int) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a single page.
        
        Args:
            page: Page number (0-based)
            
        Returns:
            BeautifulSoup object or None if request fails
        """
        url = self.build_url(page)
        logger.info(f"Fetching page {page}: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Add delay to be respectful
            time.sleep(self.delay)
            
            return BeautifulSoup(response.content, 'html.parser')
        
        except requests.RequestException as e:
            logger.error(f"Error fetching page {page}: {e}")
            return None
    
    def extract_mp_data(self, row) -> Optional[Dict]:
        """
        Extract MP data from a table row.
        
        Args:
            row: BeautifulSoup table row element
            
        Returns:
            Dictionary with MP data or None if extraction fails
        """
        try:
            # Find cells by class name (more reliable than index)
            name_cell = row.find('td', class_='views-field-field-name')
            photo_cell = row.find('td', class_='views-field-field-image')
            county_cell = row.find('td', class_='views-field-field-county')
            constituency_cell = row.find('td', class_='views-field-field-constituency')
            party_cell = row.find('td', class_='views-field-field-party')
            status_cell = row.find('td', class_='views-field-field-status')
            
            if not name_cell:
                return None
            
            # Extract name (remove "HON." prefix and extra whitespace)
            name = name_cell.get_text(strip=True)
            name = re.sub(r'^HON\.\s*', '', name, flags=re.IGNORECASE)
            name = re.sub(r'\s+', ' ', name).strip()
            
            # Skip empty rows
            if not name or name == '':
                return None
            
            # Extract photo URL if available
            photo_url = None
            if photo_cell:
                img_tag = photo_cell.find('img')
                if img_tag and img_tag.get('src'):
                    photo_url = urljoin(self.BASE_URL, img_tag['src'])
            
            # Extract other fields
            county = county_cell.get_text(strip=True) if county_cell else None
            constituency = constituency_cell.get_text(strip=True) if constituency_cell else None
            party = party_cell.get_text(strip=True) if party_cell else None
            status = status_cell.get_text(strip=True) if status_cell else None
            
            return {
                'name': name,
                'county': county if county else None,
                'constituency': constituency if constituency else None,
                'party': party if party else None,
                'status': status if status else None,
                'photo_url': photo_url,
                'term_start_year': self.term_start_year
            }
        
        except Exception as e:
            logger.warning(f"Error extracting MP data from row: {e}")
            return None
    
    def scrape_page(self, page: int) -> List[Dict]:
        """
        Scrape all MPs from a single page.
        
        Args:
            page: Page number (0-based)
            
        Returns:
            List of MP dictionaries
        """
        soup = self.fetch_page(page)
        if not soup:
            return []
        
        mps = []
        
        # Find all table rows with class="mp"
        rows = soup.find_all('tr', class_='mp')
        
        if not rows:
            logger.warning(f"No MP rows found on page {page}")
            return []
        
        for row in rows:
            mp_data = self.extract_mp_data(row)
            if mp_data:
                mps.append(mp_data)
        
        logger.info(f"Extracted {len(mps)} MPs from page {page}")
        return mps
    
    def has_next_page(self, soup: BeautifulSoup, current_page: int) -> bool:
        """
        Check if there's a next page.
        
        Args:
            soup: BeautifulSoup object of current page
            current_page: Current page number
            
        Returns:
            True if next page exists, False otherwise
        """
        # Look for pagination nav
        pager = soup.find('nav', class_='pager')
        if not pager:
            return False
        
        # Look for a link to the next page number
        next_page = current_page + 1
        next_link = pager.find('a', href=lambda href: href and f'page={next_page}' in href)
        
        return next_link is not None
    
    def scrape_all(self, max_pages: int = 50) -> List[Dict]:
        """
        Scrape all MPs across all pages.
        
        Args:
            max_pages: Maximum number of pages to scrape (safety limit)
            
        Returns:
            List of all MP dictionaries
        """
        all_mps = []
        page = 0
        
        logger.info(f"Starting scrape for {self.term_start_year} parliament")
        
        while page < max_pages:
            mps = self.scrape_page(page)
            
            if not mps:
                logger.info(f"No MPs found on page {page}, stopping")
                break
            
            all_mps.extend(mps)
            
            # Check if there's a next page
            soup = self.fetch_page(page)
            if not soup or not self.has_next_page(soup, page):
                logger.info(f"No more pages after page {page}")
                break
            
            page += 1
        
        logger.info(f"Scraped {len(all_mps)} total MPs from {page + 1} pages")
        return all_mps
    
    def save_to_json(self, mps: List[Dict], output_path: str):
        """
        Save MP data to JSON file.
        
        Args:
            mps: List of MP dictionaries
            output_path: Path to output JSON file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mps, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(mps)} MPs to {output_path}")
    
    def save_to_csv(self, mps: List[Dict], output_path: str):
        """
        Save MP data to CSV file.
        
        Args:
            mps: List of MP dictionaries
            output_path: Path to output CSV file
        """
        import csv
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not mps:
            logger.warning("No MPs to save")
            return
        
        fieldnames = ['name', 'county', 'constituency', 'party', 'status', 
                     'photo_url', 'term_start_year']
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(mps)
        
        logger.info(f"Saved {len(mps)} MPs to {output_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Scrape MP data from parliament.go.ke'
    )
    parser.add_argument(
        '--term',
        type=int,
        required=True,
        help='Parliamentary term start year (e.g., 2022, 2017)'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output file path (JSON or CSV)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay between requests in seconds (default: 1.0)'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=50,
        help='Maximum number of pages to scrape (default: 50)'
    )
    
    args = parser.parse_args()
    
    # Create scraper
    scraper = MPDataScraper(
        term_start_year=args.term,
        delay=args.delay
    )
    
    # Scrape all MPs
    mps = scraper.scrape_all(max_pages=args.max_pages)
    
    if not mps:
        logger.error("No MPs scraped")
        return 1
    
    # Save to file
    output_path = Path(args.output)
    if output_path.suffix.lower() == '.json':
        scraper.save_to_json(mps, args.output)
    elif output_path.suffix.lower() == '.csv':
        scraper.save_to_csv(mps, args.output)
    else:
        logger.error(f"Unsupported output format: {output_path.suffix}")
        return 1
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Scraping Summary for {args.term} Parliament")
    print(f"{'='*60}")
    print(f"Total MPs scraped: {len(mps)}")
    print(f"Output file: {args.output}")
    
    # Count by status
    elected = sum(1 for mp in mps if mp.get('status', '') and mp.get('status', '').lower() == 'elected')
    nominated = sum(1 for mp in mps if mp.get('status', '') and mp.get('status', '').lower() == 'nominated')
    print(f"Elected: {elected}")
    print(f"Nominated: {nominated}")
    
    # Count by party
    parties = {}
    for mp in mps:
        party = mp.get('party', 'Unknown')
        parties[party] = parties.get(party, 0) + 1
    
    print(f"\nTop 5 parties:")
    for party, count in sorted(parties.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {party}: {count}")
    
    return 0


if __name__ == '__main__':
    exit(main())
