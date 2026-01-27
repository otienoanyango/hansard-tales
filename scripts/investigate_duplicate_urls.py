#!/usr/bin/env python3
"""
Investigate duplicate URLs on parliament.go.ke

This script scrapes the first page and shows all URLs with their metadata,
highlighting any duplicates (same date + period).
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hansard_tales.scrapers.hansard_scraper import HansardScraper
from hansard_tales.storage.filesystem import FilesystemStorage
from collections import defaultdict


def main():
    """Investigate duplicate URLs."""
    print("Investigating duplicate URLs on parliament.go.ke")
    print("=" * 80)
    
    # Initialize scraper (no database, no downloads)
    storage = FilesystemStorage("data/pdfs/hansard")
    scraper = HansardScraper(storage=storage, db_path=None)
    
    # Scrape first page only
    print("\nScraping first page...")
    hansards = scraper.scrape_hansard_page(page_num=1)
    
    if not hansards:
        print("No Hansards found!")
        return
    
    print(f"Found {len(hansards)} Hansard entries\n")
    
    # Group by date + period
    by_date_period = defaultdict(list)
    
    for hansard in hansards:
        date = hansard.get('date', 'unknown')
        title = hansard.get('title', '')
        url = hansard.get('url', '')
        
        # Extract period from title
        period = scraper.period_extractor.extract_from_title(title)
        if not period:
            period = 'P'  # Default
        
        key = f"{date}_{period}"
        by_date_period[key].append({
            'date': date,
            'period': period,
            'title': title,
            'url': url
        })
    
    # Show all entries, highlighting duplicates
    print("All entries (grouped by date + period):")
    print("-" * 80)
    
    duplicate_count = 0
    for key in sorted(by_date_period.keys(), reverse=True):
        entries = by_date_period[key]
        
        if len(entries) > 1:
            duplicate_count += len(entries) - 1
            print(f"\n⚠️  DUPLICATE: {key} ({len(entries)} entries)")
        else:
            print(f"\n✓  {key}")
        
        for i, entry in enumerate(entries, 1):
            print(f"  [{i}] Date: {entry['date']}")
            print(f"      Period: {entry['period']}")
            print(f"      Title: {entry['title'][:80]}...")
            print(f"      URL: {entry['url']}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total entries found: {len(hansards)}")
    print(f"Unique date+period combinations: {len(by_date_period)}")
    print(f"Duplicate entries: {duplicate_count}")
    print(f"Files that would be created: {len(by_date_period)}")
    print(f"URLs that would be marked 'skipped': {duplicate_count}")
    
    # Show which duplicates exist
    if duplicate_count > 0:
        print("\nDuplicate date+period combinations:")
        for key in sorted(by_date_period.keys(), reverse=True):
            entries = by_date_period[key]
            if len(entries) > 1:
                print(f"  - {key}: {len(entries)} URLs")


if __name__ == "__main__":
    main()
