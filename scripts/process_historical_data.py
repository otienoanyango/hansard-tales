#!/usr/bin/env python3
"""
Process historical Hansard data with date range filtering

This script:
1. Downloads Hansard PDFs within specified date range
2. Processes them in batches
3. Updates the database
4. Generates search index and static site
5. Provides quality assurance reports

Usage:
    # Process all 2024 data
    python scripts/process_historical_data.py --year 2024
    
    # Process specific date range
    python scripts/process_historical_data.py --start-date 2024-01-01 --end-date 2024-12-31
    
    # Process from date onwards
    python scripts/process_historical_data.py --start-date 2024-06-01
    
    # Process up to date
    python scripts/process_historical_data.py --end-date 2024-12-31
    
    # Dry run to see what would be processed
    python scripts/process_historical_data.py --start-date 2024-01-01 --end-date 2024-12-31 --dry-run
"""

import argparse
import sys
import time
from pathlib import Path
from datetime import datetime, date
import sqlite3
import re

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hansard_tales.scrapers.hansard_scraper import HansardScraper
from hansard_tales.processors.pdf_processor import PDFProcessor
from hansard_tales.database.db_updater import DatabaseUpdater
import hansard_tales.search_index_generator as search_index_gen
import hansard_tales.site_generator as site_gen


class HistoricalDataProcessor:
    """Process historical Hansard data with quality assurance"""
    
    def __init__(self, year=None, start_date=None, end_date=None, dry_run=False, force=False):
        self.year = year
        self.start_date = start_date
        self.end_date = end_date
        self.dry_run = dry_run
        self.force = force
        self.db_path = Path("data/hansard.db")
        self.pdf_dir = Path("data/pdfs")
        self.output_dir = Path("output")
        
        # Statistics
        self.stats = {
            'pdfs_downloaded': 0,
            'pdfs_processed': 0,
            'pdfs_skipped': 0,
            'pdfs_failed': 0,
            'statements_extracted': 0,
            'mps_identified': 0,
            'bills_extracted': 0,
            'errors': []
        }
    
    def run(self):
        """Run the complete historical data processing pipeline"""
        print("=" * 70)
        if self.start_date or self.end_date:
            date_range = f"{self.start_date or 'beginning'} to {self.end_date or 'present'}"
            print(f"Historical Hansard Data Processing - {date_range}")
        else:
            print(f"Historical Hansard Data Processing - {self.year or 'All available'}")
        print("=" * 70)
        print(f"Dry run: {self.dry_run}")
        print(f"Force reprocess: {self.force}")
        if self.start_date:
            print(f"Start date: {self.start_date}")
        if self.end_date:
            print(f"End date: {self.end_date}")
        print()
        
        try:
            # Step 1: Download PDFs
            print("Step 1: Downloading Hansard PDFs...")
            self._download_pdfs()
            
            # Step 2: Process PDFs
            print("\nStep 2: Processing PDFs...")
            self._process_pdfs()
            
            # Step 3: Quality assurance
            print("\nStep 3: Quality assurance checks...")
            self._quality_assurance()
            
            # Step 4: Generate search index and site (if not dry run)
            if not self.dry_run:
                print("\nStep 4: Generating search index and static site...")
                self._generate_outputs()
            
            # Step 5: Print summary
            print("\n" + "=" * 70)
            print("Processing Complete!")
            print("=" * 70)
            self._print_summary()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.stats['errors'].append(str(e))
            return False
    
    def _extract_date_from_filename(self, pdf_path):
        """
        Extract date from PDF filename.
        
        Supports formats:
        - Hansard_Report_2025-12-04.pdf
        - Hansard Report - Wednesday, 3rd December 2025 (P).pdf
        - Hansard Report - Thursday, 4th December 2025 (E).pdf
        
        Returns:
            date object or None if date cannot be extracted
        """
        filename = pdf_path.name
        
        # Try ISO format first: YYYY-MM-DD
        iso_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
        if iso_match:
            try:
                return date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
            except ValueError:
                pass
        
        # Try long format: "3rd December 2025"
        long_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)\s+(\w+)\s+(\d{4})', filename)
        if long_match:
            try:
                day = int(long_match.group(1))
                month_name = long_match.group(2)
                year = int(long_match.group(3))
                
                # Convert month name to number
                month_map = {
                    'January': 1, 'February': 2, 'March': 3, 'April': 4,
                    'May': 5, 'June': 6, 'July': 7, 'August': 8,
                    'September': 9, 'October': 10, 'November': 11, 'December': 12
                }
                month = month_map.get(month_name)
                if month:
                    return date(year, month, day)
            except (ValueError, KeyError):
                pass
        
        return None
    
    def _is_within_date_range(self, pdf_path):
        """
        Check if PDF date is within the specified date range.
        
        Returns:
            True if within range (or no range specified), False otherwise
        """
        # If no date range specified, include all PDFs
        if not self.start_date and not self.end_date:
            return True
        
        # Extract date from filename
        pdf_date = self._extract_date_from_filename(pdf_path)
        
        # If date cannot be extracted, include the PDF (with warning)
        if pdf_date is None:
            return True
        
        # Check against start date
        if self.start_date:
            start = datetime.strptime(self.start_date, '%Y-%m-%d').date()
            if pdf_date < start:
                return False
        
        # Check against end date
        if self.end_date:
            end = datetime.strptime(self.end_date, '%Y-%m-%d').date()
            if pdf_date > end:
                return False
        
        return True
    
    def _download_pdfs(self):
        """Download all available PDFs for the specified year"""
        scraper = HansardScraper()
        
        print(f"Scraping Hansard PDFs from {self.year}...")
        
        if self.dry_run:
            print("  [DRY RUN] Would download PDFs")
            # Count existing PDFs
            existing_pdfs = list(self.pdf_dir.glob("*.pdf"))
            self.stats['pdfs_downloaded'] = len(existing_pdfs)
            print(f"  Found {len(existing_pdfs)} existing PDFs")
        else:
            try:
                downloaded = scraper.scrape()
                self.stats['pdfs_downloaded'] = len(downloaded)
                print(f"  ✓ Downloaded {len(downloaded)} PDFs")
            except Exception as e:
                print(f"  ❌ Error downloading PDFs: {e}")
                self.stats['errors'].append(f"Download error: {e}")
    
    def _process_pdfs(self):
        """Process all PDFs in the data directory (filtered by date range if specified)"""
        pdf_processor = PDFProcessor()
        db_updater = DatabaseUpdater(str(self.db_path))
        
        # Get all PDFs
        all_pdf_files = sorted(self.pdf_dir.glob("*.pdf"))
        
        # Filter by date range if specified
        if self.start_date or self.end_date:
            pdf_files = []
            for pdf_path in all_pdf_files:
                if self._is_within_date_range(pdf_path):
                    pdf_files.append(pdf_path)
                else:
                    pdf_date = self._extract_date_from_filename(pdf_path)
                    if pdf_date:
                        self.stats['pdfs_skipped'] += 1
            
            print(f"Found {len(all_pdf_files)} PDFs, {len(pdf_files)} within date range")
            if self.stats['pdfs_skipped'] > 0:
                print(f"Skipped {self.stats['pdfs_skipped']} PDFs outside date range")
        else:
            pdf_files = all_pdf_files
        
        total_pdfs = len(pdf_files)
        
        if total_pdfs == 0:
            print("No PDFs to process")
            return
        
        print(f"\nProcessing {total_pdfs} PDFs...")
        
        for i, pdf_path in enumerate(pdf_files, 1):
            pdf_date = self._extract_date_from_filename(pdf_path)
            date_str = f" ({pdf_date})" if pdf_date else ""
            print(f"\n  [{i}/{total_pdfs}] Processing: {pdf_path.name}{date_str}")
            
            try:
                # Check if already processed (unless force flag is set)
                if not self.force and self._is_already_processed(pdf_path):
                    print(f"    ⏭️  Already processed, skipping")
                    continue
                
                if self.dry_run:
                    print(f"    [DRY RUN] Would process PDF")
                    self.stats['pdfs_processed'] += 1
                    continue
                
                # Extract text from PDF
                print(f"    Extracting text...")
                extracted_data = pdf_processor.process_pdf(str(pdf_path))
                
                if not extracted_data or not extracted_data.get('text'):
                    print(f"    ⚠️  No text extracted")
                    self.stats['pdfs_failed'] += 1
                    self.stats['errors'].append(f"{pdf_path.name}: No text extracted")
                    continue
                
                # Update database
                print(f"    Updating database...")
                result = db_updater.process_hansard_pdf(
                    pdf_path=str(pdf_path),
                    extracted_data=extracted_data
                )
                
                # Update statistics
                self.stats['pdfs_processed'] += 1
                self.stats['statements_extracted'] += result.get('statements_added', 0)
                self.stats['mps_identified'] += result.get('unique_mps', 0)
                self.stats['bills_extracted'] += result.get('bills_mentioned', 0)
                
                print(f"    ✓ Processed: {result.get('statements_added', 0)} statements, "
                      f"{result.get('unique_mps', 0)} MPs")
                
                # Small delay to avoid overwhelming the system
                time.sleep(0.5)
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
                self.stats['pdfs_failed'] += 1
                self.stats['errors'].append(f"{pdf_path.name}: {e}")
    
    def _is_already_processed(self, pdf_path):
        """Check if PDF has already been processed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM hansard_sessions
            WHERE pdf_path = ? AND processed = 1
        """, (str(pdf_path),))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def _quality_assurance(self):
        """Run quality assurance checks on the processed data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("\nQuality Assurance Checks:")
        print("-" * 70)
        
        # Check 1: Total statements
        cursor.execute("SELECT COUNT(*) FROM statements")
        total_statements = cursor.fetchone()[0]
        print(f"  Total statements in database: {total_statements:,}")
        
        # Check 2: Unique MPs
        cursor.execute("SELECT COUNT(DISTINCT mp_id) FROM statements")
        unique_mps = cursor.fetchone()[0]
        print(f"  Unique MPs with statements: {unique_mps}")
        
        # Check 3: MPs without statements
        cursor.execute("""
            SELECT COUNT(*) FROM mps m
            WHERE NOT EXISTS (
                SELECT 1 FROM statements s WHERE s.mp_id = m.id
            )
        """)
        mps_without_statements = cursor.fetchone()[0]
        print(f"  MPs without statements: {mps_without_statements}")
        
        # Check 4: Statements with bill references
        cursor.execute("SELECT COUNT(*) FROM statements WHERE bill_reference IS NOT NULL")
        statements_with_bills = cursor.fetchone()[0]
        print(f"  Statements with bill references: {statements_with_bills}")
        
        # Check 5: Sessions processed
        cursor.execute("SELECT COUNT(*) FROM hansard_sessions WHERE processed = 1")
        sessions_processed = cursor.fetchone()[0]
        print(f"  Sessions processed: {sessions_processed}")
        
        # Check 6: Date range
        cursor.execute("""
            SELECT MIN(date), MAX(date) FROM hansard_sessions
            WHERE processed = 1
        """)
        date_range = cursor.fetchone()
        if date_range[0]:
            print(f"  Date range: {date_range[0]} to {date_range[1]}")
        
        # Check 7: Top 10 most active MPs
        print("\n  Top 10 Most Active MPs:")
        cursor.execute("""
            SELECT m.name, COUNT(s.id) as statement_count
            FROM mps m
            JOIN statements s ON m.id = s.mp_id
            GROUP BY m.id
            ORDER BY statement_count DESC
            LIMIT 10
        """)
        
        for i, (name, count) in enumerate(cursor.fetchall(), 1):
            print(f"    {i}. {name}: {count} statements")
        
        # Check 8: Duplicate detection
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT mp_id, session_id, text, COUNT(*) as cnt
                FROM statements
                GROUP BY mp_id, session_id, text
                HAVING cnt > 1
            )
        """)
        duplicates = cursor.fetchone()[0]
        if duplicates > 0:
            print(f"\n  ⚠️  Warning: {duplicates} potential duplicate statements found")
        
        conn.close()
    
    def _generate_outputs(self):
        """Generate search index and static site"""
        try:
            # Generate search index
            print("  Generating search index...")
            search_index_gen.generate_search_index(str(self.db_path), str(self.output_dir / "data"))
            print("  ✓ Search index generated")
            
            # Generate static site
            print("  Generating static site...")
            site_gen.generate_static_site(str(self.db_path), str(self.output_dir))
            print("  ✓ Static site generated")
            
        except Exception as e:
            print(f"  ❌ Error generating outputs: {e}")
            self.stats['errors'].append(f"Output generation error: {e}")
    
    def _print_summary(self):
        """Print processing summary"""
        print("\nProcessing Statistics:")
        print("-" * 70)
        print(f"  PDFs downloaded: {self.stats['pdfs_downloaded']}")
        if self.stats['pdfs_skipped'] > 0:
            print(f"  PDFs skipped (outside date range): {self.stats['pdfs_skipped']}")
        print(f"  PDFs processed: {self.stats['pdfs_processed']}")
        print(f"  PDFs failed: {self.stats['pdfs_failed']}")
        print(f"  Statements extracted: {self.stats['statements_extracted']:,}")
        print(f"  Unique MPs identified: {self.stats['mps_identified']}")
        print(f"  Bill references extracted: {self.stats['bills_extracted']}")
        
        if self.stats['errors']:
            print(f"\n  ⚠️  Errors encountered: {len(self.stats['errors'])}")
            print("\nError Details:")
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                print(f"    - {error}")
            if len(self.stats['errors']) > 10:
                print(f"    ... and {len(self.stats['errors']) - 10} more errors")
        
        # Success rate
        total_to_process = self.stats['pdfs_downloaded'] - self.stats['pdfs_skipped']
        if total_to_process > 0:
            success_rate = (self.stats['pdfs_processed'] / total_to_process) * 100
            print(f"\n  Success rate: {success_rate:.1f}%")
        
        # Recommendations
        print("\nRecommendations:")
        if self.stats['pdfs_failed'] > 0:
            print("  - Review failed PDFs and retry with --force flag")
        if self.stats['mps_identified'] < 100:
            print("  - Low MP identification rate, review regex patterns")
        if self.dry_run:
            print("  - Run without --dry-run to actually process data")
        if self.stats['pdfs_skipped'] > 0:
            print(f"  - {self.stats['pdfs_skipped']} PDFs were outside the specified date range")


def main():
    parser = argparse.ArgumentParser(
        description="Process historical Hansard data with date range filtering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all 2024 data
  python scripts/process_historical_data.py --year 2024
  
  # Process specific date range
  python scripts/process_historical_data.py --start-date 2024-01-01 --end-date 2024-12-31
  
  # Process from date onwards
  python scripts/process_historical_data.py --start-date 2024-06-01
  
  # Process up to date
  python scripts/process_historical_data.py --end-date 2024-12-31
  
  # Dry run to see what would be processed
  python scripts/process_historical_data.py --start-date 2024-01-01 --end-date 2024-12-31 --dry-run
  
  # Force reprocess already-processed PDFs
  python scripts/process_historical_data.py --year 2024 --force
        """
    )
    parser.add_argument(
        '--year',
        type=int,
        help='Year to process (optional if using date range)'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date (YYYY-MM-DD format, inclusive)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date (YYYY-MM-DD format, inclusive)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate processing without making changes'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force reprocessing of already processed PDFs'
    )
    
    args = parser.parse_args()
    
    # Validate date format if provided
    if args.start_date:
        try:
            datetime.strptime(args.start_date, '%Y-%m-%d')
        except ValueError:
            print("Error: start-date must be in YYYY-MM-DD format")
            sys.exit(1)
    
    if args.end_date:
        try:
            datetime.strptime(args.end_date, '%Y-%m-%d')
        except ValueError:
            print("Error: end-date must be in YYYY-MM-DD format")
            sys.exit(1)
    
    # Validate that start date is before end date
    if args.start_date and args.end_date:
        start = datetime.strptime(args.start_date, '%Y-%m-%d')
        end = datetime.strptime(args.end_date, '%Y-%m-%d')
        if start > end:
            print("Error: start-date must be before end-date")
            sys.exit(1)
    
    # Run processor
    processor = HistoricalDataProcessor(
        year=args.year,
        start_date=args.start_date,
        end_date=args.end_date,
        dry_run=args.dry_run,
        force=args.force
    )
    
    success = processor.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
