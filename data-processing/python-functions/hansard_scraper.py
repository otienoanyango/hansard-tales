#!/usr/bin/env python3
"""
Hansard Tales PDF Scraper
Scrapes and downloads Hansard PDFs from Parliament of Kenya website
with intelligent rate limiting and SQLite tracking.
"""

import requests
import sqlite3
import time
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging
import sys
from typing import List, Dict, Optional, Tuple
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hansard_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HansardScraper:
    def __init__(self, data_dir: str = "hansard_data", db_path: str = "hansard_sessions.db"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.db_path = db_path
        
        # Rate limiting settings
        self.base_delay = 2.0  # Base delay between requests (seconds)
        self.current_delay = self.base_delay
        self.max_delay = 30.0  # Maximum delay (30 seconds)
        self.backoff_factor = 1.5  # Multiply delay by this when throttled
        self.success_factor = 0.9  # Reduce delay by this on success
        self.min_delay = 1.0  # Minimum delay
        
        # Request settings
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Initialize database
        self.init_database()
        
        # Parliament URLs
        self.base_url = "https://www.parliament.go.ke"
        self.hansard_url = "https://www.parliament.go.ke/the-national-assembly/house-business/hansard"
        
        # Stats tracking
        self.stats = {
            'total_found': 0,
            'already_downloaded': 0,
            'newly_downloaded': 0,
            'failed_downloads': 0,
            'throttle_events': 0,
            'errors': 0
        }

    def init_database(self):
        """Initialize SQLite database with hansard sessions table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hansard_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_date DATE NOT NULL,
                    session_title TEXT NOT NULL,
                    pdf_filename TEXT,
                    pdf_url TEXT,
                    youtube_url TEXT,
                    download_status TEXT DEFAULT 'pending',
                    file_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(session_date, session_title)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_date ON hansard_sessions(session_date);
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_download_status ON hansard_sessions(download_status);
            """)
            
            conn.commit()
            conn.close()
            logger.info(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    def make_request(self, url: str, stream: bool = False) -> requests.Response:
        """Make HTTP request with intelligent rate limiting and throttling detection"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Apply current delay
                logger.debug(f"Waiting {self.current_delay:.1f}s before request to {url}")
                time.sleep(self.current_delay)
                
                response = self.session.get(url, stream=stream, timeout=30)
                
                # Check for throttling indicators
                is_throttled = self.detect_throttling(response)
                
                if is_throttled:
                    self.handle_throttling(url)
                    retry_count += 1
                    continue
                
                # Success - reduce delay slightly
                if response.status_code == 200:
                    self.current_delay = max(
                        self.min_delay, 
                        self.current_delay * self.success_factor
                    )
                    return response
                
                # Handle HTTP errors
                if response.status_code in [429, 503, 502, 504]:
                    self.handle_throttling(url, response.status_code)
                    retry_count += 1
                    continue
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {retry_count + 1}): {e}")
                retry_count += 1
                if retry_count >= max_retries:
                    raise
                time.sleep(self.current_delay * retry_count)
        
        raise Exception(f"Failed to fetch {url} after {max_retries} attempts")

    def detect_throttling(self, response: requests.Response) -> bool:
        """Detect if we're being throttled"""
        throttling_indicators = [
            response.status_code in [429, 503, 502, 504],
            response.elapsed.total_seconds() > 10.0,  # Very slow response
            'rate limit' in response.text.lower(),
            'too many requests' in response.text.lower(),
            'please slow down' in response.text.lower(),
            len(response.content) < 1000 and response.status_code == 200  # Suspiciously small response
        ]
        
        return any(throttling_indicators)

    def handle_throttling(self, url: str, status_code: int = None):
        """Handle throttling by increasing delays"""
        old_delay = self.current_delay
        self.current_delay = min(self.max_delay, self.current_delay * self.backoff_factor)
        self.stats['throttle_events'] += 1
        
        logger.warning(f"Throttling detected for {url} (status: {status_code})")
        logger.warning(f"Increasing delay from {old_delay:.1f}s to {self.current_delay:.1f}s")
        
        # Extra wait on throttling
        time.sleep(self.current_delay)

    def extract_hansard_links(self, html_content: str) -> List[Dict]:
        """Extract Hansard PDF and YouTube links from parliament website"""
        soup = BeautifulSoup(html_content, 'html.parser')
        sessions = []
        
        try:
            # Look for hansard links in various possible locations
            link_selectors = [
                'a[href*="hansard"]',
                'a[href*=".pdf"]', 
                'a[href*="Hansard"]',
                '.views-field-title a',
                '.field-content a'
            ]
            
            for selector in link_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    if not href or not text:
                        continue
                    
                    # Skip non-relevant links
                    if not any(keyword in text.lower() for keyword in ['hansard', 'debate', 'proceedings', 'assembly']):
                        continue
                    
                    # Extract date from link text or URL
                    session_date = self.extract_date(text, href)
                    if not session_date:
                        continue
                    
                    # Determine if it's a PDF or YouTube link
                    full_url = urljoin(self.base_url, href)
                    
                    session_data = {
                        'session_date': session_date,
                        'session_title': text,
                        'pdf_url': full_url if '.pdf' in href.lower() else None,
                        'youtube_url': full_url if 'youtube' in href.lower() or 'youtu.be' in href.lower() else None,
                        'source_text': text
                    }
                    
                    sessions.append(session_data)
            
            # Also look for YouTube embeds or links
            youtube_links = soup.find_all(['iframe', 'a'], src=True) + soup.find_all(['iframe', 'a'], href=True)
            for element in youtube_links:
                url = element.get('src') or element.get('href', '')
                if 'youtube.com' in url or 'youtu.be' in url:
                    # Try to associate with a hansard session
                    parent_text = element.find_parent().get_text(strip=True) if element.find_parent() else ""
                    session_date = self.extract_date(parent_text, url)
                    
                    if session_date:
                        sessions.append({
                            'session_date': session_date,
                            'session_title': f"Parliamentary Proceedings {session_date}",
                            'pdf_url': None,
                            'youtube_url': url,
                            'source_text': parent_text[:200]
                        })
            
            # Remove duplicates and sort by date
            unique_sessions = {}
            for session in sessions:
                key = (session['session_date'], session['session_title'])
                if key not in unique_sessions:
                    unique_sessions[key] = session
                else:
                    # Merge PDF and YouTube URLs if we have both
                    existing = unique_sessions[key]
                    if session.get('pdf_url') and not existing.get('pdf_url'):
                        existing['pdf_url'] = session['pdf_url']
                    if session.get('youtube_url') and not existing.get('youtube_url'):
                        existing['youtube_url'] = session['youtube_url']
            
            sessions = list(unique_sessions.values())
            sessions.sort(key=lambda x: x['session_date'], reverse=True)
            
            logger.info(f"Extracted {len(sessions)} unique Hansard sessions")
            return sessions
            
        except Exception as e:
            logger.error(f"Error extracting hansard links: {e}")
            return []

    def extract_date(self, text: str, url: str = "") -> Optional[str]:
        """Extract date from text or URL"""
        # Common date patterns in Hansard titles
        date_patterns = [
            r'(\d{1,2})\w{0,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
            r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})'
        ]
        
        # Search in text first, then URL
        for source in [text, url]:
            for pattern in date_patterns:
                match = re.search(pattern, source, re.IGNORECASE)
                if match:
                    try:
                        groups = match.groups()
                        if len(groups) == 3:
                            if groups[1].isalpha():  # Month name format
                                month_names = {
                                    'january': '01', 'jan': '01',
                                    'february': '02', 'feb': '02', 
                                    'march': '03', 'mar': '03',
                                    'april': '04', 'apr': '04',
                                    'may': '05', 'june': '06', 'jun': '06',
                                    'july': '07', 'jul': '07',
                                    'august': '08', 'aug': '08',
                                    'september': '09', 'sep': '09',
                                    'october': '10', 'oct': '10',
                                    'november': '11', 'nov': '11',
                                    'december': '12', 'dec': '12'
                                }
                                month = month_names.get(groups[1].lower())
                                if month:
                                    day = groups[0].zfill(2)
                                    year = groups[2]
                                    return f"{year}-{month}-{day}"
                            else:  # Numeric format
                                if len(groups[0]) == 4:  # YYYY-MM-DD
                                    return f"{groups[0]}-{groups[1].zfill(2)}-{groups[2].zfill(2)}"
                                else:  # DD/MM/YYYY or similar
                                    return f"{groups[2]}-{groups[1].zfill(2)}-{groups[0].zfill(2)}"
                    except:
                        continue
        
        return None

    def save_session_to_db(self, session: Dict) -> bool:
        """Save session metadata to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generate filename from date and title
            safe_title = re.sub(r'[^\w\s-]', '', session['session_title'][:50])
            safe_title = re.sub(r'\s+', '_', safe_title)
            pdf_filename = f"hansard_{session['session_date']}_{safe_title}.pdf" if session.get('pdf_url') else None
            
            cursor.execute("""
                INSERT OR IGNORE INTO hansard_sessions 
                (session_date, session_title, pdf_filename, pdf_url, youtube_url, download_status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session['session_date'],
                session['session_title'],
                pdf_filename,
                session.get('pdf_url'),
                session.get('youtube_url'),
                'pending'
            ))
            
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Database save error: {e}")
            return False

    def download_pdf(self, session_id: int, pdf_url: str, filename: str) -> bool:
        """Download PDF file with progress tracking"""
        file_path = self.data_dir / filename
        
        # Skip if already downloaded
        if file_path.exists():
            logger.info(f"File already exists: {filename}")
            self.update_download_status(session_id, 'completed', file_path.stat().st_size)
            self.stats['already_downloaded'] += 1
            return True
        
        try:
            logger.info(f"Downloading: {filename}")
            response = self.make_request(pdf_url, stream=True)
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Log progress for large files
                        if total_size > 0 and downloaded_size % (1024 * 1024) == 0:  # Every MB
                            progress = (downloaded_size / total_size) * 100
                            logger.debug(f"Download progress: {progress:.1f}% ({downloaded_size:,} bytes)")
            
            file_size = file_path.stat().st_size
            self.update_download_status(session_id, 'completed', file_size)
            
            logger.info(f"Downloaded successfully: {filename} ({file_size:,} bytes)")
            self.stats['newly_downloaded'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Download failed for {filename}: {e}")
            
            # Clean up partial file
            if file_path.exists():
                file_path.unlink()
            
            self.update_download_status(session_id, 'failed', 0)
            self.stats['failed_downloads'] += 1
            return False

    def update_download_status(self, session_id: int, status: str, file_size: int = 0):
        """Update download status in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE hansard_sessions 
                SET download_status = ?, file_size = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, file_size, session_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Status update error: {e}")

    def get_pending_downloads(self) -> List[Tuple]:
        """Get sessions that need PDF downloads"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, pdf_url, pdf_filename 
                FROM hansard_sessions 
                WHERE pdf_url IS NOT NULL 
                AND (download_status = 'pending' OR download_status = 'failed')
                ORDER BY session_date DESC
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return []

    def scrape_hansard_page(self, page_num: int = 1) -> List[Dict]:
        """Scrape a single page of the Hansard listing"""
        try:
            url = f"{self.hansard_url}?page={page_num}" if page_num > 1 else self.hansard_url
            logger.info(f"Scraping page {page_num}: {url}")
            
            response = self.make_request(url)
            sessions = self.extract_hansard_links(response.text)
            
            logger.info(f"Found {len(sessions)} sessions on page {page_num}")
            return sessions
            
        except Exception as e:
            logger.error(f"Error scraping page {page_num}: {e}")
            self.stats['errors'] += 1
            return []

    def scrape_all_pages(self, max_pages: int = 10) -> int:
        """Scrape multiple pages of Hansard listings"""
        total_new_sessions = 0
        
        for page_num in range(1, max_pages + 1):
            try:
                sessions = self.scrape_hansard_page(page_num)
                
                if not sessions:
                    logger.info(f"No sessions found on page {page_num}, stopping")
                    break
                
                new_sessions = 0
                for session in sessions:
                    if self.save_session_to_db(session):
                        new_sessions += 1
                
                total_new_sessions += new_sessions
                self.stats['total_found'] += len(sessions)
                
                logger.info(f"Page {page_num}: {new_sessions} new sessions added")
                
                # If no new sessions found, we might have reached already-scraped content
                if new_sessions == 0:
                    logger.info("No new sessions found, stopping pagination")
                    break
                
            except Exception as e:
                logger.error(f"Error processing page {page_num}: {e}")
                continue
        
        return total_new_sessions

    def download_pending_pdfs(self, limit: int = None):
        """Download all pending PDFs"""
        pending = self.get_pending_downloads()
        
        if limit:
            pending = pending[:limit]
        
        logger.info(f"Starting download of {len(pending)} PDFs")
        
        for session_id, pdf_url, filename in pending:
            try:
                success = self.download_pdf(session_id, pdf_url, filename)
                
                if success:
                    logger.info(f"✅ Downloaded: {filename}")
                else:
                    logger.error(f"❌ Failed: {filename}")
                
            except KeyboardInterrupt:
                logger.info("Download interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error downloading {filename}: {e}")
                continue

    def print_stats(self):
        """Print scraping statistics"""
        print("\n" + "="*60)
        print("HANSARD SCRAPER STATISTICS")
        print("="*60)
        print(f"📊 Total sessions found:     {self.stats['total_found']}")
        print(f"✅ Already downloaded:       {self.stats['already_downloaded']}")
        print(f"⬇️  Newly downloaded:        {self.stats['newly_downloaded']}")
        print(f"❌ Failed downloads:        {self.stats['failed_downloads']}")
        print(f"🐌 Throttling events:       {self.stats['throttle_events']}")
        print(f"⚠️  Errors encountered:      {self.stats['errors']}")
        print(f"⏱️  Current delay:           {self.current_delay:.1f}s")
        print(f"📁 Data directory:          {self.data_dir}")
        print(f"🗃️  Database:                {self.db_path}")
        print("="*60)

    def get_database_summary(self):
        """Get summary of database contents"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    download_status,
                    COUNT(*) as count,
                    SUM(file_size) as total_size
                FROM hansard_sessions 
                GROUP BY download_status
            """)
            
            status_summary = cursor.fetchall()
            
            cursor.execute("""
                SELECT 
                    MIN(session_date) as earliest,
                    MAX(session_date) as latest,
                    COUNT(*) as total
                FROM hansard_sessions
            """)
            
            date_range = cursor.fetchone()
            
            conn.close()
            
            print("\n" + "="*50)
            print("DATABASE SUMMARY")
            print("="*50)
            
            for status, count, total_size in status_summary:
                size_mb = total_size / (1024*1024) if total_size else 0
                print(f"{status.upper():12}: {count:3d} sessions ({size_mb:.1f} MB)")
            
            if date_range[0]:
                print(f"Date Range  : {date_range[0]} to {date_range[1]}")
                print(f"Total       : {date_range[2]} sessions")
            
            print("="*50)
            
        except Exception as e:
            logger.error(f"Database summary error: {e}")

def main():
    """Main execution function"""
    print("🏛️  Hansard Tales PDF Scraper")
    print("🇰🇪 Scraping Parliament of Kenya Hansard Documents")
    print("-" * 60)
    
    scraper = HansardScraper()
    
    try:
        # Step 1: Scrape session metadata
        print("📡 Step 1: Discovering Hansard sessions...")
        new_sessions = scraper.scrape_all_pages(max_pages=5)  # Start with 5 pages
        print(f"✅ Found {new_sessions} new sessions")
        
        # Step 2: Download PDFs
        print("\n📥 Step 2: Downloading PDF files...")
        scraper.download_pending_pdfs(limit=10)  # Start with 10 PDFs for testing
        
        # Step 3: Print results
        scraper.print_stats()
        scraper.get_database_summary()
        
        print("\n🎯 Next Steps:")
        print("1. Run with more pages: python hansard_scraper.py --max-pages 20")
        print("2. Download all PDFs: python hansard_scraper.py --download-all")
        print("3. Check database: sqlite3 hansard_sessions.db '.tables'")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        scraper.print_stats()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Hansard Tales PDF Scraper")
    parser.add_argument("--max-pages", type=int, default=5, help="Maximum pages to scrape")
    parser.add_argument("--download-limit", type=int, default=10, help="Maximum PDFs to download")
    parser.add_argument("--download-all", action="store_true", help="Download all pending PDFs")
    parser.add_argument("--data-dir", default="hansard_data", help="Data directory")
    parser.add_argument("--db-path", default="hansard_sessions.db", help="Database path")
    parser.add_argument("--delay", type=float, default=2.0, help="Base delay between requests")
    
    args = parser.parse_args()
    
    scraper = HansardScraper(data_dir=args.data_dir, db_path=args.db_path)
    scraper.base_delay = args.delay
    scraper.current_delay = args.delay
    
    try:
        # Scrape sessions
        new_sessions = scraper.scrape_all_pages(max_pages=args.max_pages)
        print(f"✅ Found {new_sessions} new sessions")
        
        # Download PDFs
        if args.download_all:
            scraper.download_pending_pdfs()
        else:
            scraper.download_pending_pdfs(limit=args.download_limit)
        
        scraper.print_stats()
        scraper.get_database_summary()
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        scraper.print_stats()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
