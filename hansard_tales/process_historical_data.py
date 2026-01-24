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
    hansard-process-historical --year 2024
    
    # Process specific date range
    hansard-process-historical --start-date 2024-01-01 --end-date 2024-12-31
    
    # Process from date onwards
    hansard-process-historical --start-date 2024-06-01
    
    # Process up to date
    hansard-process-historical --end-date 2024-12-31
    
    # Dry run to see what would be processed
    hansard-process-historical --start-date 2024-01-01 --end-date 2024-12-31 --dry-run
"""

import argparse
import shutil
import sys
import time
from pathlib import Path
from datetime import datetime, date
import sqlite3
import re
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional, Dict, List

try:
    import dateparser
    DATEPARSER_AVAILABLE = True
except ImportError:
    DATEPARSER_AVAILABLE = False
    print("Warning: dateparser not installed. Natural language dates not supported.")
    print("Install with: pip install dateparser")

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("Warning: tqdm not installed. Progress bars not available.")
    print("Install with: pip install tqdm")

from hansard_tales.scrapers.hansard_scraper import HansardScraper
from hansard_tales.database.db_updater import DatabaseUpdater
from hansard_tales.processors.pdf_processor import PDFProcessor
from hansard_tales.processors.mp_identifier import MPIdentifier
from hansard_tales.processors.bill_extractor import BillExtractor
import hansard_tales.search_index_generator as search_index_gen
import hansard_tales.site_generator as site_gen


def parse_date_string(date_str):
    """
    Parse date string - supports both ISO format and natural language.
    
    Supports:
    - ISO format: 2024-01-01
    - Natural language: "last week", "2 weeks ago", "last month", "yesterday"
    
    Args:
        date_str: Date string to parse
        
    Returns:
        Date string in YYYY-MM-DD format or None if parsing fails
    """
    if not date_str:
        return None
    
    # Try ISO format first (YYYY-MM-DD)
    try:
        parsed = datetime.strptime(date_str, '%Y-%m-%d')
        return parsed.strftime('%Y-%m-%d')
    except ValueError:
        pass
    
    # Try natural language parsing if dateparser is available
    if DATEPARSER_AVAILABLE:
        parsed = dateparser.parse(
            date_str,
            settings={
                'PREFER_DATES_FROM': 'past',  # Assume past dates for historical data
                'RETURN_AS_TIMEZONE_AWARE': False
            }
        )
        if parsed:
            return parsed.strftime('%Y-%m-%d')
    
    return None


@dataclass
class ProcessedPDF:
    """Result of processing a single PDF (stateless, portable)."""
    pdf_path: str
    pdf_date: str
    status: str  # 'success', 'error', 'warning'
    reason: Optional[str] = None
    statements: int = 0
    unique_mps: int = 0
    bills: int = 0
    processing_time: float = 0.0
    error_message: Optional[str] = None


def process_single_pdf(
    pdf_path: Path,
    db_path: Path,
    force: bool = False
) -> ProcessedPDF:
    """
    Process a single PDF file (stateless, idempotent, portable).
    
    This function is designed to be:
    - Stateless: No shared state between calls
    - Idempotent: Can be called multiple times safely
    - Portable: Can run on any machine (local, GitHub Actions, EC2)
    
    Args:
        pdf_path: Path to PDF file
        db_path: Path to database
        force: Force reprocess even if already processed
        
    Returns:
        ProcessedPDF with processing results
    """
    start_time = time.time()
    
    # Extract date from filename
    pdf_date_obj = _extract_date_from_filename(pdf_path)
    if not pdf_date_obj:
        return ProcessedPDF(
            pdf_path=str(pdf_path),
            pdf_date="unknown",
            status='error',
            reason='cannot_extract_date',
            error_message=f"Cannot extract date from filename: {pdf_path.name}",
            processing_time=time.time() - start_time
        )
    
    date_str = pdf_date_obj.strftime('%Y-%m-%d')
    
    # Check if already processed (unless force flag is set)
    if not force and _is_already_processed(pdf_path, db_path):
        return ProcessedPDF(
            pdf_path=str(pdf_path),
            pdf_date=date_str,
            status='skipped',
            reason='already_processed',
            processing_time=time.time() - start_time
        )
    
    try:
        # Initialize processors (each thread gets its own instances)
        pdf_processor = PDFProcessor()
        mp_identifier = MPIdentifier()
        bill_extractor = BillExtractor()
        
        # Extract text from PDF
        extracted_data = pdf_processor.extract_text_from_pdf(str(pdf_path))
        
        if not extracted_data:
            return ProcessedPDF(
                pdf_path=str(pdf_path),
                pdf_date=date_str,
                status='error',
                reason='pdf_extraction_failed',
                error_message="Failed to extract text from PDF",
                processing_time=time.time() - start_time
            )
        
        # Extract statements
        statements = mp_identifier.extract_statements_from_pages(
            extracted_data['pages']
        )
        
        if not statements:
            return ProcessedPDF(
                pdf_path=str(pdf_path),
                pdf_date=date_str,
                status='warning',
                reason='no_statements_found',
                error_message="No statements found in PDF",
                processing_time=time.time() - start_time
            )
        
        # Extract bill references
        bill_count = 0
        for statement in statements:
            bills = bill_extractor.extract_bill_references(statement.text)
            bill_count += len(bills)
        
        # Get unique MP count
        unique_mps = len(mp_identifier.get_unique_mp_names(statements))
        
        return ProcessedPDF(
            pdf_path=str(pdf_path),
            pdf_date=date_str,
            status='success',
            statements=len(statements),
            unique_mps=unique_mps,
            bills=bill_count,
            processing_time=time.time() - start_time
        )
    
    except Exception as e:
        return ProcessedPDF(
            pdf_path=str(pdf_path),
            pdf_date=date_str,
            status='error',
            reason='unexpected_error',
            error_message=str(e),
            processing_time=time.time() - start_time
        )


def _extract_date_from_filename(pdf_path: Path) -> Optional[date]:
    """
    Extract date from PDF filename.
    
    Supports formats:
    - Standardized: 20250314_0_A.pdf, 20251204_2.pdf
    - Hansard_Report_2025-12-04.pdf
    - Hansard Report - Wednesday, 3rd December 2025 (P).pdf
    - Hansard Report - Thursday, 4th December 2025 (E).pdf
    
    Returns:
        date object or None if date cannot be extracted
    """
    # URL-decode the filename first
    filename = unquote(pdf_path.name)
    
    # Try standardized format first: YYYYMMDD_n.pdf, YYYYMMDD_n_TYPE.pdf, or hansard_YYYYMMDD_TYPE.pdf
    standardized_match = re.search(r'(\d{4})(\d{2})(\d{2})_\d+', filename)
    if standardized_match:
        try:
            return date(int(standardized_match.group(1)), int(standardized_match.group(2)), int(standardized_match.group(3)))
        except ValueError:
            pass
    
    # Try hansard_YYYYMMDD_TYPE.pdf format (without index number)
    hansard_match = re.search(r'hansard_(\d{4})(\d{2})(\d{2})_[APE]', filename)
    if hansard_match:
        try:
            return date(int(hansard_match.group(1)), int(hansard_match.group(2)), int(hansard_match.group(3)))
        except ValueError:
            pass
    
    # Try ISO format: YYYY-MM-DD
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


def _is_already_processed(pdf_path: Path, db_path: Path) -> bool:
    """Check if PDF has already been processed."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) FROM hansard_sessions
        WHERE pdf_path = ? AND processed = 1
    """, (str(pdf_path),))
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count > 0


class HistoricalDataProcessor:
    """Process historical Hansard data with quality assurance and parallel processing"""
    
    def __init__(self, year=None, start_date=None, end_date=None, dry_run=False, force=False, clean=False, workers=4):
        self.year = year
        self.start_date = start_date
        self.end_date = end_date
        self.dry_run = dry_run
        self.force = force
        self.clean = clean
        self.workers = workers  # Number of parallel workers
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
            'duplicates_skipped': 0,
            'errors': [],
            'processing_times': []  # Per-PDF processing times
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
        print(f"Clean database: {self.clean}")
        print(f"Parallel workers: {self.workers}")
        if self.start_date:
            print(f"Start date: {self.start_date}")
        if self.end_date:
            print(f"End date: {self.end_date}")
        print()
        
        try:
            # Step 0: Clean database if requested
            if self.clean:
                print("Step 0: Cleaning database...")
                self._clean_database()
            
            # Step 1: Download PDFs
            print("\nStep 1: Downloading Hansard PDFs...")
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
            
            # Step 6: Emit metrics for observability
            self._emit_metrics()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.stats['errors'].append(str(e))
            return False
    
    def _extract_date_from_filename(self, pdf_path):
        """Wrapper for module-level function."""
        return _extract_date_from_filename(pdf_path)
    
    def _clean_database(self):
        """
        Clean the database by backing it up and removing all processed data.
        
        This creates a timestamped backup before cleaning, allowing recovery if needed.
        IMPORTANT: The downloaded_pdfs table is NOT cleaned - it tracks downloads permanently.
        """
        if not self.db_path.exists():
            print("  ℹ️  Database does not exist, nothing to clean")
            return
        
        if self.dry_run:
            print("  [DRY RUN] Would backup and clean database")
            return
        
        # Create backup with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.db_path.parent / f"{self.db_path.stem}_backup_{timestamp}{self.db_path.suffix}"
        
        try:
            print(f"  Creating backup: {backup_path}")
            shutil.copy2(self.db_path, backup_path)
            print(f"  ✓ Backup created: {backup_path}")
            
            # Clean the database (remove hansard_sessions and statements ONLY)
            # The downloaded_pdfs table is preserved
            print("  Cleaning database tables...")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get counts before cleaning
            cursor.execute("SELECT COUNT(*) FROM statements")
            statements_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM hansard_sessions")
            sessions_count = cursor.fetchone()[0]
            
            print(f"  Removing {statements_count:,} statements and {sessions_count} sessions...")
            print(f"  ℹ️  Note: downloaded_pdfs table is preserved (tracks download history)")
            
            # Delete data (foreign keys will cascade if configured)
            cursor.execute("DELETE FROM statements")
            cursor.execute("DELETE FROM hansard_sessions")
            
            # Reset autoincrement counters
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='statements'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='hansard_sessions'")
            
            conn.commit()
            conn.close()
            
            print(f"  ✓ Database cleaned (backup saved to {backup_path.name})")
            print(f"  ℹ️  To restore: cp {backup_path} {self.db_path}")
            
        except Exception as e:
            print(f"  ❌ Error cleaning database: {e}")
            self.stats['errors'].append(f"Database cleaning error: {e}")
            raise
    
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
        """Download all available PDFs for the specified date range (with robust error handling)"""
        scraper = HansardScraper(
            start_date=self.start_date,
            end_date=self.end_date,
            db_path=str(self.db_path)
        )
        
        print(f"Scraping Hansard PDFs from parliament website...")
        if self.start_date or self.end_date:
            print(f"  Date range: {self.start_date or 'beginning'} to {self.end_date or 'present'}")
        
        if self.dry_run:
            print("  [DRY RUN] Would download PDFs")
            # Count existing PDFs
            existing_pdfs = list(Path("data/pdfs/hansard-report").glob("*.pdf"))
            self.stats['pdfs_downloaded'] = len(existing_pdfs)
            print(f"  Found {len(existing_pdfs)} existing PDFs")
        else:
            try:
                # Scrape with date filtering
                downloaded = scraper.scrape_all(max_pages=10)
                self.stats['pdfs_downloaded'] = len(downloaded)
                print(f"  ✓ Scraped {len(downloaded)} PDF links from website")
                
                # Download the PDFs (scraper checks database before downloading)
                if downloaded:
                    print(f"  Downloading PDFs...")
                    download_stats = scraper.download_all(downloaded)
                    print(f"  ✓ Downloaded {download_stats['downloaded']} new PDFs")
                    print(f"  ℹ️  Skipped {download_stats['skipped']} existing PDFs")
                    if download_stats['failed'] > 0:
                        print(f"  ⚠️  Failed to download {download_stats['failed']} PDFs")
                
            except Exception as e:
                # Log error but don't fail - we can still process existing PDFs
                print(f"  ⚠️  Warning: PDF download failed: {e}")
                print(f"  ℹ️  Continuing with existing PDFs in data/pdfs/hansard-report")
                self.stats['errors'].append(f"Download error (non-fatal): {e}")
            
            # Count existing PDFs (whether download succeeded or not)
            existing_pdfs = list(Path("data/pdfs/hansard-report").glob("*.pdf"))
            print(f"  Found {len(existing_pdfs)} total PDFs in data/pdfs/hansard-report")
            
            # Warn if date range specified but might not have those PDFs
            if (self.start_date or self.end_date) and len(existing_pdfs) > 0:
                print(f"  ℹ️  Note: Parliament website typically only has recent PDFs")
                print(f"  ℹ️  Date filtering will be applied to existing PDFs")
                if self.start_date:
                    print(f"  ℹ️  Looking for PDFs from {self.start_date} onwards")
    
    def _process_pdfs(self):
        """Process all PDFs in parallel using ThreadPoolExecutor"""
        # Get all PDFs from standardized directory
        pdf_dir = Path("data/pdfs/hansard-report")
        all_pdf_files = sorted(pdf_dir.glob("*.pdf"))
        
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
        
        print(f"\nProcessing {total_pdfs} PDFs with {self.workers} parallel workers...")
        
        if self.dry_run:
            print(f"[DRY RUN] Would process {total_pdfs} PDFs in parallel")
            self.stats['pdfs_processed'] = total_pdfs
            return
        
        # Process PDFs in parallel
        processed_results = []
        
        try:
            # Use ThreadPoolExecutor for parallel processing
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                # Submit all PDF processing tasks
                future_to_pdf = {
                    executor.submit(process_single_pdf, pdf_path, self.db_path, self.force): pdf_path
                    for pdf_path in pdf_files
                }
                
                # Create progress bar if tqdm is available
                if TQDM_AVAILABLE:
                    progress = tqdm(total=total_pdfs, desc="Processing PDFs", unit="pdf")
                else:
                    progress = None
                
                # Collect results as they complete
                for future in as_completed(future_to_pdf):
                    pdf_path = future_to_pdf[future]
                    
                    try:
                        result = future.result()
                        processed_results.append(result)
                        
                        # Update progress
                        if progress:
                            progress.update(1)
                            # Update progress bar description with current status
                            success_count = sum(1 for r in processed_results if r.status == 'success')
                            progress.set_postfix({
                                'success': success_count,
                                'failed': sum(1 for r in processed_results if r.status == 'error')
                            })
                        else:
                            # Print progress without tqdm
                            print(f"  [{len(processed_results)}/{total_pdfs}] Processed: {pdf_path.name}")
                    
                    except Exception as e:
                        # This should rarely happen since process_single_pdf catches exceptions
                        print(f"\n  ❌ Unexpected error processing {pdf_path.name}: {e}")
                        processed_results.append(ProcessedPDF(
                            pdf_path=str(pdf_path),
                            pdf_date="unknown",
                            status='error',
                            reason='executor_error',
                            error_message=str(e)
                        ))
                        if progress:
                            progress.update(1)
                
                if progress:
                    progress.close()
        
        except KeyboardInterrupt:
            print(f"\n\n⚠️  Processing interrupted by user")
            print(f"Processed {len(processed_results)}/{total_pdfs} PDFs before interruption")
            raise
        
        # Now batch write all successful results to database
        print(f"\nWriting results to database...")
        self._batch_write_to_database(processed_results)
        
        # Update statistics
        for result in processed_results:
            self.stats['processing_times'].append(result.processing_time)
            
            if result.status == 'success':
                self.stats['pdfs_processed'] += 1
                self.stats['statements_extracted'] += result.statements
                self.stats['mps_identified'] += result.unique_mps
                self.stats['bills_extracted'] += result.bills
            elif result.status == 'skipped':
                # Don't count as processed or failed
                pass
            elif result.status == 'error':
                self.stats['pdfs_failed'] += 1
                self.stats['errors'].append(f"{Path(result.pdf_path).name}: {result.error_message}")
            elif result.status == 'warning':
                self.stats['pdfs_processed'] += 1
                self.stats['errors'].append(f"{Path(result.pdf_path).name}: Warning - {result.error_message}")
        
        # Print timing statistics
        if self.stats['processing_times']:
            avg_time = sum(self.stats['processing_times']) / len(self.stats['processing_times'])
            max_time = max(self.stats['processing_times'])
            min_time = min(self.stats['processing_times'])
            print(f"\nProcessing time per PDF: avg={avg_time:.2f}s, min={min_time:.2f}s, max={max_time:.2f}s")
    
    def _batch_write_to_database(self, results: List[ProcessedPDF]):
        """
        Batch write processed results to database.
        
        This reduces SQLite lock contention by writing all results
        in a single transaction per PDF (but sequentially to avoid locks).
        
        Args:
            results: List of ProcessedPDF results
        """
        db_updater = DatabaseUpdater(str(self.db_path))
        
        # Filter to only successful results
        successful_results = [r for r in results if r.status == 'success']
        
        if not successful_results:
            print("  No successful results to write")
            return
        
        # Create progress bar if available
        if TQDM_AVAILABLE:
            progress = tqdm(total=len(successful_results), desc="Writing to database", unit="pdf")
        else:
            progress = None
        
        # Write each PDF's data to database (must be sequential due to SQLite)
        for result in successful_results:
            try:
                # Use db_updater to write to database
                # Note: We already extracted the data, but db_updater needs to re-extract
                # This is a trade-off for simplicity - in Phase 2 we can optimize this
                db_result = db_updater.process_hansard_pdf(
                    pdf_path=result.pdf_path,
                    pdf_url=f"file://{Path(result.pdf_path).absolute()}",
                    date=result.pdf_date,
                    skip_if_processed=False  # We already checked this
                )
                
                if db_result.get('status') == 'error':
                    print(f"\n  ⚠️  Database write failed for {Path(result.pdf_path).name}: {db_result.get('reason')}")
                
                # Track duplicates skipped
                if db_result.get('duplicates_skipped', 0) > 0:
                    self.stats['duplicates_skipped'] += db_result['duplicates_skipped']
                
                if progress:
                    progress.update(1)
            
            except Exception as e:
                print(f"\n  ❌ Error writing {Path(result.pdf_path).name} to database: {e}")
        
        if progress:
            progress.close()
        
        print(f"  ✓ Wrote {len(successful_results)} PDFs to database")
    
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
        """Print processing summary with clear success/failure metrics"""
        print("\nProcessing Statistics:")
        print("-" * 70)
        print(f"  PDFs downloaded: {self.stats['pdfs_downloaded']}")
        if self.stats['pdfs_skipped'] > 0:
            print(f"  PDFs skipped (outside date range): {self.stats['pdfs_skipped']}")
        print(f"  PDFs processed successfully: {self.stats['pdfs_processed']}")
        print(f"  PDFs failed: {self.stats['pdfs_failed']}")
        print(f"  Statements extracted: {self.stats['statements_extracted']:,}")
        if self.stats['duplicates_skipped'] > 0:
            print(f"  Duplicate statements skipped: {self.stats['duplicates_skipped']:,}")
        print(f"  Unique MPs identified: {self.stats['mps_identified']}")
        print(f"  Bill references extracted: {self.stats['bills_extracted']}")
        
        # Timing statistics
        if self.stats['processing_times']:
            total_time = sum(self.stats['processing_times'])
            avg_time = total_time / len(self.stats['processing_times'])
            max_time = max(self.stats['processing_times'])
            min_time = min(self.stats['processing_times'])
            
            print(f"\n  Processing time:")
            print(f"    Total: {total_time:.2f}s")
            print(f"    Average per PDF: {avg_time:.2f}s")
            print(f"    Min: {min_time:.2f}s, Max: {max_time:.2f}s")
            
            # Calculate theoretical speedup
            if self.workers > 1:
                sequential_time = total_time
                parallel_time = max_time + (total_time - max_time) / self.workers
                speedup = sequential_time / parallel_time if parallel_time > 0 else 1
                print(f"    Estimated speedup: {speedup:.2f}x (with {self.workers} workers)")
        
        # Calculate success metrics
        total_to_process = self.stats['pdfs_downloaded'] - self.stats['pdfs_skipped']
        if total_to_process > 0:
            success_rate = (self.stats['pdfs_processed'] / total_to_process) * 100
            print(f"\n  Success rate: {success_rate:.1f}% ({self.stats['pdfs_processed']}/{total_to_process})")
        
        # Error summary
        if self.stats['errors']:
            print(f"\n  ⚠️  Issues encountered: {len(self.stats['errors'])}")
            
            # Categorize errors
            fatal_errors = [e for e in self.stats['errors'] if 'non-fatal' not in e.lower()]
            warnings = [e for e in self.stats['errors'] if 'non-fatal' in e.lower() or 'warning' in e.lower()]
            
            if warnings:
                print(f"  ℹ️  Warnings (non-fatal): {len(warnings)}")
            if fatal_errors:
                print(f"  ❌ Errors: {len(fatal_errors)}")
            
            print("\nIssue Details:")
            for error in self.stats['errors'][:10]:  # Show first 10 issues
                prefix = "  ⚠️  " if 'warning' in error.lower() or 'non-fatal' in error.lower() else "  ❌ "
                print(f"{prefix}{error}")
            if len(self.stats['errors']) > 10:
                print(f"    ... and {len(self.stats['errors']) - 10} more issues")
        else:
            print(f"\n  ✅ No errors encountered")
        
        # Recommendations
        print("\nRecommendations:")
        if self.stats['pdfs_failed'] > 0:
            print("  - Review failed PDFs and retry with --force flag")
        if self.stats['mps_identified'] < 100 and self.stats['pdfs_processed'] > 0:
            print("  - Low MP identification rate, review regex patterns")
        if self.dry_run:
            print("  - Run without --dry-run to actually process data")
        if self.stats['pdfs_skipped'] > 0:
            print(f"  - {self.stats['pdfs_skipped']} PDFs were outside the specified date range")
        if self.stats['pdfs_processed'] == 0 and total_to_process > 0:
            print("  - No PDFs were successfully processed - check error logs above")
        if not self.stats['errors'] and self.stats['pdfs_processed'] > 0:
            print("  - ✅ All PDFs processed successfully!")
        if self.workers == 1 and self.stats['pdfs_processed'] > 10:
            print(f"  - Consider using more workers (--workers 4-8) for faster processing")
    
    def _emit_metrics(self):
        """
        Emit metrics for observability (future integration with CloudWatch, Prometheus, etc.)
        
        This method outputs metrics in a structured format that can be parsed by
        monitoring systems. Currently outputs to stdout, but can be extended to
        send to actual monitoring services.
        """
        # Calculate derived metrics
        total_to_process = self.stats['pdfs_downloaded'] - self.stats['pdfs_skipped']
        success_rate = (self.stats['pdfs_processed'] / total_to_process * 100) if total_to_process > 0 else 0
        
        # Categorize errors
        fatal_errors = len([e for e in self.stats['errors'] if 'non-fatal' not in e.lower()])
        warnings = len([e for e in self.stats['errors'] if 'non-fatal' in e.lower() or 'warning' in e.lower()])
        
        # Output metrics in a parseable format
        print("\n" + "="*70)
        print("METRICS (for observability)")
        print("="*70)
        print(f"hansard.processing.pdfs.downloaded={self.stats['pdfs_downloaded']}")
        print(f"hansard.processing.pdfs.skipped={self.stats['pdfs_skipped']}")
        print(f"hansard.processing.pdfs.processed={self.stats['pdfs_processed']}")
        print(f"hansard.processing.pdfs.failed={self.stats['pdfs_failed']}")
        print(f"hansard.processing.pdfs.success_rate={success_rate:.2f}")
        print(f"hansard.processing.statements.extracted={self.stats['statements_extracted']}")
        print(f"hansard.processing.mps.identified={self.stats['mps_identified']}")
        print(f"hansard.processing.bills.extracted={self.stats['bills_extracted']}")
        print(f"hansard.processing.errors.fatal={fatal_errors}")
        print(f"hansard.processing.errors.warnings={warnings}")
        print(f"hansard.processing.errors.total={len(self.stats['errors'])}")
        print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="Process historical Hansard data with date range filtering (supports natural language dates)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all 2024 data
  hansard-process-historical --year 2024
  
  # Process specific date range (ISO format)
  hansard-process-historical --start-date 2024-01-01 --end-date 2024-12-31
  
  # Natural language dates (requires dateparser)
  hansard-process-historical --start-date "last week"
  hansard-process-historical --start-date "2 weeks ago" --end-date "yesterday"
  hansard-process-historical --start-date "last month"
  hansard-process-historical --start-date "3 months ago" --end-date "1 month ago"
  
  # Process from date onwards
  hansard-process-historical --start-date 2024-06-01
  
  # Process up to date
  hansard-process-historical --end-date 2024-12-31
  
  # Dry run to see what would be processed
  hansard-process-historical --start-date "last week" --dry-run
  
  # Force reprocess already-processed PDFs (duplicates are automatically skipped)
  hansard-process-historical --year 2024 --force
  
  # Clean database before processing (creates backup first)
  hansard-process-historical --year 2024 --clean
  
  # Use parallel processing with 8 workers
  hansard-process-historical --year 2024 --workers 8

Important Notes:
  --force: Reprocesses PDFs even if already in database. Duplicate statements are
           automatically detected and skipped using content hashing.
  
  --clean: Backs up the database (with timestamp) and removes all hansard_sessions
           and statements before processing. Use this for a fresh start.
           Backup location: data/hansard_backup_YYYYMMDD_HHMMSS.db
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
        help='Start date (YYYY-MM-DD or natural language like "last week", "2 weeks ago")'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date (YYYY-MM-DD or natural language like "yesterday", "last month")'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate processing without making changes'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force reprocessing of already processed PDFs (duplicates automatically skipped)'
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Backup and clean database before processing (removes all sessions and statements)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Number of parallel workers for PDF processing (default: 4, recommended: 4-8)'
    )
    
    args = parser.parse_args()
    
    # Parse dates (supports both ISO format and natural language)
    start_date = None
    end_date = None
    
    if args.start_date:
        start_date = parse_date_string(args.start_date)
        if not start_date:
            print(f"Error: Could not parse start date '{args.start_date}'")
            print("Supported formats:")
            print("  - ISO: 2024-01-01")
            if DATEPARSER_AVAILABLE:
                print("  - Natural language: 'last week', '2 weeks ago', 'last month'")
            else:
                print("  - Install dateparser for natural language support: pip install dateparser")
            sys.exit(1)
        print(f"Parsed start date: '{args.start_date}' → {start_date}")
    
    if args.end_date:
        end_date = parse_date_string(args.end_date)
        if not end_date:
            print(f"Error: Could not parse end date '{args.end_date}'")
            print("Supported formats:")
            print("  - ISO: 2024-12-31")
            if DATEPARSER_AVAILABLE:
                print("  - Natural language: 'yesterday', 'last month', '1 week ago'")
            else:
                print("  - Install dateparser for natural language support: pip install dateparser")
            sys.exit(1)
        print(f"Parsed end date: '{args.end_date}' → {end_date}")
    
    # Validate that start date is before end date
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        if start > end:
            print(f"Error: start date ({start_date}) must be before end date ({end_date})")
            sys.exit(1)
    
    print()  # Blank line before processing starts
    
    # Validate workers parameter
    if args.workers < 1:
        print("Error: --workers must be at least 1")
        sys.exit(1)
    if args.workers > 16:
        print("Warning: Using more than 16 workers may not improve performance")
    
    # Run processor
    processor = HistoricalDataProcessor(
        year=args.year,
        start_date=start_date,
        end_date=end_date,
        dry_run=args.dry_run,
        force=args.force,
        clean=args.clean,
        workers=args.workers
    )
    
    success = processor.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
