#!/usr/bin/env python3
"""
Daily Hansard Scraper Runner
Automates daily scraping with smart scheduling and error handling
"""

import subprocess
import sys
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_scraper(max_pages=10, download_limit=None, retry_on_failure=True):
    """Run the hansard scraper with error handling"""
    try:
        cmd = ['python', 'hansard_scraper.py', '--max-pages', str(max_pages)]
        
        if download_limit:
            cmd.extend(['--download-limit', str(download_limit)])
        else:
            cmd.append('--download-all')
        
        logger.info(f"Running scraper: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes timeout
        )
        
        if result.returncode == 0:
            logger.info("✅ Scraper completed successfully")
            logger.info("STDOUT:", result.stdout[-500:])  # Last 500 chars
            return True
        else:
            logger.error("❌ Scraper failed")
            logger.error("STDERR:", result.stderr)
            
            if retry_on_failure:
                logger.info("🔄 Retrying in 5 minutes...")
                time.sleep(300)  # Wait 5 minutes
                return run_scraper(max_pages//2, download_limit//2 if download_limit else 5, False)
            
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("⏰ Scraper timed out after 30 minutes")
        return False
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        return False

def main():
    """Main daily scraper routine"""
    print("🕐 Daily Hansard Scraper - Starting at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Conservative daily run - don't overwhelm the server
    success = run_scraper(
        max_pages=5,      # Only check first 5 pages daily
        download_limit=10  # Download maximum 10 PDFs per day
    )
    
    if success:
        print("✅ Daily scraping completed successfully")
        
        # Show quick stats
        try:
            result = subprocess.run(
                ['sqlite3', 'hansard_sessions.db', 'SELECT COUNT(*) FROM hansard_sessions;'],
                capture_output=True, text=True
            )
            total_sessions = result.stdout.strip()
            
            result = subprocess.run(
                ['sqlite3', 'hansard_sessions.db', "SELECT COUNT(*) FROM hansard_sessions WHERE download_status='completed';"],
                capture_output=True, text=True  
            )
            downloaded = result.stdout.strip()
            
            print(f"📊 Total sessions: {total_sessions}, Downloaded: {downloaded}")
            
        except:
            pass  # Stats are optional
            
        return 0
    else:
        print("❌ Daily scraping failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
