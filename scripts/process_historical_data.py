#!/usr/bin/env python3
"""
Process historical Hansard data (2024-2025)

This script:
1. Downloads all available 2024-2025 Hansard PDFs
2. Processes them in batches
3. Updates the database
4. Generates search index and static site
5. Provides quality assurance reports

Usage:
    python scripts/process_historical_data.py [--year 2024] [--dry-run] [--force]
"""

import argparse
import sys
import time
from pathlib import Path
from datetime import datetime
import sqlite3

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hansard_tales.scrapers.hansard_scraper import HansardScraper
from hansard_tales.processors.pdf_processor import PDFProcessor
from hansard_tales.database.db_updater import DatabaseUpdater
import hansard_tales.search_index_generator as search_index_gen
import hansard_tales.site_generator as site_gen


class HistoricalDataProcessor:
    """Process historical Hansard data with quality assurance"""
    
    def __init__(self, year=2024, dry_run=False, force=False):
        self.year = year
        self.dry_run = dry_run
        self.force = force
        self.db_path = Path("data/hansard.db")
        self.pdf_dir = Path("data/pdfs")
        self.output_dir = Path("output")
        
        # Statistics
        self.stats = {
            'pdfs_downloaded': 0,
            'pdfs_processed': 0,
            'pdfs_failed': 0,
            'statements_extracted': 0,
            'mps_identified': 0,
            'bills_extracted': 0,
            'errors': []
        }
    
    def run(self):
        """Run the complete historical data processing pipeline"""
        print("=" * 70)
        print(f"Historical Hansard Data Processing - {self.year}")
        print("=" * 70)
        print(f"Dry run: {self.dry_run}")
        print(f"Force reprocess: {self.force}")
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
        """Process all PDFs in the data directory"""
        pdf_processor = PDFProcessor()
        db_updater = DatabaseUpdater(str(self.db_path))
        
        # Get all PDFs
        pdf_files = sorted(self.pdf_dir.glob("*.pdf"))
        total_pdfs = len(pdf_files)
        
        print(f"Processing {total_pdfs} PDFs...")
        
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"\n  [{i}/{total_pdfs}] Processing: {pdf_path.name}")
            
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
        if self.stats['pdfs_downloaded'] > 0:
            success_rate = (self.stats['pdfs_processed'] / self.stats['pdfs_downloaded']) * 100
            print(f"\n  Success rate: {success_rate:.1f}%")
        
        # Recommendations
        print("\nRecommendations:")
        if self.stats['pdfs_failed'] > 0:
            print("  - Review failed PDFs and retry with --force flag")
        if self.stats['mps_identified'] < 100:
            print("  - Low MP identification rate, review regex patterns")
        if self.dry_run:
            print("  - Run without --dry-run to actually process data")


def main():
    parser = argparse.ArgumentParser(
        description="Process historical Hansard data (2024-2025)"
    )
    parser.add_argument(
        '--year',
        type=int,
        default=2024,
        help='Year to process (default: 2024)'
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
    
    # Run processor
    processor = HistoricalDataProcessor(
        year=args.year,
        dry_run=args.dry_run,
        force=args.force
    )
    
    success = processor.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
