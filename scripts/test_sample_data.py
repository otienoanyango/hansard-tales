#!/usr/bin/env python3
"""
Test script for Task 8.1: Test with sample data

This script:
1. Downloads 5 sample Hansard PDFs (or uses existing ones)
2. Runs the full processing pipeline
3. Validates MP identification accuracy
4. Checks statement extraction quality
5. Validates database integrity
6. Generates a detailed report
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from hansard_tales.scrapers.hansard_scraper import HansardScraper
from hansard_tales.processors.pdf_processor import PDFProcessor
from hansard_tales.processors.mp_identifier import MPIdentifier
from hansard_tales.processors.bill_extractor import BillExtractor
from hansard_tales.database.db_updater import DatabaseUpdater


class SampleDataTester:
    """Test the full processing pipeline with sample data."""
    
    def __init__(self, db_path: str = "data/hansard.db", pdf_dir: str = "data/pdfs"):
        self.db_path = db_path
        self.pdf_dir = Path(pdf_dir)
        self.report = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message to console and report."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {level}: {message}"
        print(formatted)
        self.report.append(formatted)
        
    def download_sample_pdfs(self, target_count: int = 5) -> list[Path]:
        """Download sample PDFs if needed."""
        self.log("=" * 80)
        self.log("STEP 1: Download Sample PDFs")
        self.log("=" * 80)
        
        # Check existing PDFs
        existing_pdfs = list(self.pdf_dir.glob("*.pdf"))
        self.log(f"Found {len(existing_pdfs)} existing PDFs")
        
        if len(existing_pdfs) >= target_count:
            self.log(f"Already have {len(existing_pdfs)} PDFs, using first {target_count}")
            return existing_pdfs[:target_count]
        
        # Download more PDFs
        needed = target_count - len(existing_pdfs)
        self.log(f"Need to download {needed} more PDFs")
        
        try:
            scraper = HansardScraper(output_dir=str(self.pdf_dir))
            self.log("Fetching Hansard listing pages...")
            hansards = scraper.scrape_all(max_pages=2)  # Get from first 2 pages
            
            if hansards:
                self.log(f"Found {len(hansards)} Hansard PDFs")
                # Download only what we need
                stats = scraper.download_all(hansards[:needed])
                self.log(f"Downloaded {stats['downloaded']} new PDFs")
        except Exception as e:
            self.log(f"Error downloading PDFs: {e}", "ERROR")
            self.log("Continuing with existing PDFs only")
        
        # Return all PDFs
        all_pdfs = list(self.pdf_dir.glob("*.pdf"))
        self.log(f"Total PDFs available: {len(all_pdfs)}")
        return all_pdfs[:target_count]
    
    def process_pdfs(self, pdf_files: list[Path]) -> dict:
        """Process PDFs and extract statements."""
        self.log("\n" + "=" * 80)
        self.log("STEP 2: Process PDFs")
        self.log("=" * 80)
        
        processor = PDFProcessor()
        mp_identifier = MPIdentifier()
        bill_extractor = BillExtractor()
        
        results = {
            "pdfs_processed": 0,
            "total_statements": 0,
            "identified_mps": set(),
            "bills_found": 0,
            "errors": []
        }
        
        for pdf_file in pdf_files:
            self.log(f"\nProcessing: {pdf_file.name}")
            
            try:
                # Extract text
                extracted_data = processor.extract_text_from_pdf(str(pdf_file))
                if not extracted_data:
                    raise Exception("Failed to extract text")
                
                page_count = extracted_data['statistics']['total_pages']
                char_count = extracted_data['statistics']['total_characters']
                self.log(f"  Extracted {char_count} characters from {page_count} pages")
                
                # Identify MPs and statements
                statements = mp_identifier.extract_statements_from_pages(extracted_data['pages'])
                self.log(f"  Found {len(statements)} statements")
                
                # Extract bills from full text
                full_text = processor.get_full_text(extracted_data)
                bills = bill_extractor.extract_bill_references(full_text)
                self.log(f"  Found {len(bills)} bill references")
                
                # Update results
                results["pdfs_processed"] += 1
                results["total_statements"] += len(statements)
                results["bills_found"] += len(bills)
                
                for stmt in statements:
                    if stmt.mp_name:
                        results["identified_mps"].add(stmt.mp_name)
                
            except Exception as e:
                error_msg = f"Error processing {pdf_file.name}: {e}"
                self.log(f"  {error_msg}", "ERROR")
                results["errors"].append(error_msg)
        
        self.log(f"\nProcessing Summary:")
        self.log(f"  PDFs processed: {results['pdfs_processed']}")
        self.log(f"  Total statements: {results['total_statements']}")
        self.log(f"  Unique MPs identified: {len(results['identified_mps'])}")
        self.log(f"  Bills found: {results['bills_found']}")
        self.log(f"  Errors: {len(results['errors'])}")
        
        return results
    
    def update_database(self, pdf_files: list[Path]) -> dict:
        """Update database with processed data."""
        self.log("\n" + "=" * 80)
        self.log("STEP 3: Update Database")
        self.log("=" * 80)
        
        updater = DatabaseUpdater(db_path=self.db_path)
        
        results = {
            "sessions_created": 0,
            "statements_inserted": 0,
            "new_mps": 0,
            "errors": []
        }
        
        for pdf_file in pdf_files:
            self.log(f"\nUpdating database for: {pdf_file.name}")
            
            try:
                # Extract date from filename (format: Hansard_Report_YYYY-MM-DD.pdf)
                filename = pdf_file.stem
                date_match = filename.split("_")[-1] if "_" in filename else None
                
                if not date_match:
                    # Try to extract date from filename
                    import re
                    date_pattern = r'(\d{4}-\d{2}-\d{2})'
                    match = re.search(date_pattern, filename)
                    date = match.group(1) if match else datetime.now().strftime("%Y-%m-%d")
                else:
                    date = date_match
                
                # Process PDF
                stats = updater.process_hansard_pdf(
                    pdf_path=str(pdf_file),
                    pdf_url=f"file://{pdf_file.absolute()}",
                    date=date,
                    title=filename,
                    skip_if_processed=False  # Process even if exists for testing
                )
                
                if stats['status'] == 'success':
                    self.log(f"  Session: {date}")
                    self.log(f"  Statements: {stats.get('statements', 0)}")
                    self.log(f"  Unique MPs: {stats.get('unique_mps', 0)}")
                    
                    results["sessions_created"] += 1
                    results["statements_inserted"] += stats.get("statements", 0)
                    results["new_mps"] += stats.get("unique_mps", 0)
                else:
                    error_msg = f"Processing failed: {stats.get('reason', 'unknown')}"
                    self.log(f"  {error_msg}", "WARN")
                    results["errors"].append(error_msg)
                
            except Exception as e:
                error_msg = f"Error updating database for {pdf_file.name}: {e}"
                self.log(f"  {error_msg}", "ERROR")
                results["errors"].append(error_msg)
        
        self.log(f"\nDatabase Update Summary:")
        self.log(f"  Sessions created: {results['sessions_created']}")
        self.log(f"  Statements inserted: {results['statements_inserted']}")
        self.log(f"  MPs involved: {results['new_mps']}")
        self.log(f"  Errors: {len(results['errors'])}")
        
        return results
    
    def validate_database(self) -> dict:
        """Validate database integrity and data quality."""
        self.log("\n" + "=" * 80)
        self.log("STEP 4: Validate Database")
        self.log("=" * 80)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        validation = {
            "total_mps": 0,
            "total_sessions": 0,
            "total_statements": 0,
            "statements_with_mps": 0,
            "statements_without_mps": 0,
            "mp_attribution_rate": 0.0,
            "top_speakers": [],
            "issues": []
        }
        
        try:
            # Count MPs
            cursor.execute("SELECT COUNT(*) FROM mps")
            validation["total_mps"] = cursor.fetchone()[0]
            self.log(f"Total MPs in database: {validation['total_mps']}")
            
            # Count sessions
            cursor.execute("SELECT COUNT(*) FROM hansard_sessions")
            validation["total_sessions"] = cursor.fetchone()[0]
            self.log(f"Total Hansard sessions: {validation['total_sessions']}")
            
            # Count statements
            cursor.execute("SELECT COUNT(*) FROM statements")
            validation["total_statements"] = cursor.fetchone()[0]
            self.log(f"Total statements: {validation['total_statements']}")
            
            # Count statements with MP attribution
            cursor.execute("SELECT COUNT(*) FROM statements WHERE mp_id IS NOT NULL")
            validation["statements_with_mps"] = cursor.fetchone()[0]
            validation["statements_without_mps"] = (
                validation["total_statements"] - validation["statements_with_mps"]
            )
            
            if validation["total_statements"] > 0:
                validation["mp_attribution_rate"] = (
                    validation["statements_with_mps"] / validation["total_statements"] * 100
                )
            
            self.log(f"Statements with MP attribution: {validation['statements_with_mps']}")
            self.log(f"Statements without MP attribution: {validation['statements_without_mps']}")
            self.log(f"MP attribution rate: {validation['mp_attribution_rate']:.1f}%")
            
            # Check attribution rate
            if validation["mp_attribution_rate"] < 90:
                issue = f"MP attribution rate ({validation['mp_attribution_rate']:.1f}%) is below 90% target"
                self.log(f"  WARNING: {issue}", "WARN")
                validation["issues"].append(issue)
            else:
                self.log(f"  ✓ MP attribution rate meets 90% target")
            
            # Get top speakers
            cursor.execute("""
                SELECT m.name, COUNT(s.id) as statement_count
                FROM mps m
                JOIN statements s ON m.id = s.mp_id
                GROUP BY m.id
                ORDER BY statement_count DESC
                LIMIT 10
            """)
            validation["top_speakers"] = cursor.fetchall()
            
            self.log(f"\nTop 10 Speakers:")
            for i, (name, count) in enumerate(validation["top_speakers"], 1):
                self.log(f"  {i}. {name}: {count} statements")
            
            # Check for duplicate statements
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT text, COUNT(*) as cnt
                    FROM statements
                    GROUP BY text
                    HAVING cnt > 1
                )
            """)
            duplicate_count = cursor.fetchone()[0]
            if duplicate_count > 0:
                issue = f"Found {duplicate_count} duplicate statements"
                self.log(f"  WARNING: {issue}", "WARN")
                validation["issues"].append(issue)
            else:
                self.log(f"  ✓ No duplicate statements found")
            
        except Exception as e:
            error_msg = f"Error validating database: {e}"
            self.log(error_msg, "ERROR")
            validation["issues"].append(error_msg)
        finally:
            conn.close()
        
        return validation
    
    def generate_report(self, processing_results: dict, db_results: dict, validation: dict):
        """Generate final test report."""
        self.log("\n" + "=" * 80)
        self.log("FINAL REPORT: Task 8.1 - Test with Sample Data")
        self.log("=" * 80)
        
        self.log(f"\n📊 Processing Results:")
        self.log(f"  PDFs processed: {processing_results['pdfs_processed']}")
        self.log(f"  Statements extracted: {processing_results['total_statements']}")
        self.log(f"  Unique MPs identified: {len(processing_results['identified_mps'])}")
        self.log(f"  Bills found: {processing_results['bills_found']}")
        
        self.log(f"\n💾 Database Results:")
        self.log(f"  Sessions created: {db_results['sessions_created']}")
        self.log(f"  Statements inserted: {db_results['statements_inserted']}")
        self.log(f"  MPs involved: {db_results['new_mps']}")
        
        self.log(f"\n✅ Validation Results:")
        self.log(f"  Total MPs: {validation['total_mps']}")
        self.log(f"  Total sessions: {validation['total_sessions']}")
        self.log(f"  Total statements: {validation['total_statements']}")
        self.log(f"  MP attribution rate: {validation['mp_attribution_rate']:.1f}%")
        
        # Overall status
        total_errors = len(processing_results['errors']) + len(db_results['errors'])
        total_issues = len(validation['issues'])
        
        self.log(f"\n🎯 Overall Status:")
        self.log(f"  Errors: {total_errors}")
        self.log(f"  Warnings: {total_issues}")
        
        if total_errors == 0 and validation['mp_attribution_rate'] >= 90:
            self.log(f"\n✅ SUCCESS: All tests passed!")
            self.log(f"  - Full pipeline executed successfully")
            self.log(f"  - MP attribution rate meets 90% target")
            self.log(f"  - Database integrity validated")
            return True
        else:
            self.log(f"\n⚠️  PARTIAL SUCCESS: Some issues found")
            if total_errors > 0:
                self.log(f"  - {total_errors} errors occurred during processing")
            if validation['mp_attribution_rate'] < 90:
                self.log(f"  - MP attribution rate below 90% target")
            return False
    
    def save_report(self, filename: str = "test_sample_data_report.txt"):
        """Save report to file."""
        report_path = Path(filename)
        with open(report_path, "w") as f:
            f.write("\n".join(self.report))
        self.log(f"\n📄 Report saved to: {report_path.absolute()}")
    
    def run(self):
        """Run the full test suite."""
        self.log("Starting Task 8.1: Test with Sample Data")
        self.log(f"Database: {self.db_path}")
        self.log(f"PDF directory: {self.pdf_dir}")
        
        # Step 1: Download sample PDFs
        pdf_files = self.download_sample_pdfs(target_count=5)
        
        if not pdf_files:
            self.log("No PDFs available for testing", "ERROR")
            return False
        
        # Step 2: Process PDFs
        processing_results = self.process_pdfs(pdf_files)
        
        # Step 3: Update database
        db_results = self.update_database(pdf_files)
        
        # Step 4: Validate database
        validation = self.validate_database()
        
        # Step 5: Generate report
        success = self.generate_report(processing_results, db_results, validation)
        
        # Save report
        self.save_report()
        
        return success


if __name__ == "__main__":
    tester = SampleDataTester()
    success = tester.run()
    sys.exit(0 if success else 1)
