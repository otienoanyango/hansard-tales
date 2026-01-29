#!/usr/bin/env python3
"""
Process historical parliamentary PDFs with parallel processing.

This script processes downloaded PDFs (Hansard, Votes & Proceedings)
with batch processing, parallel workers, progress tracking, error recovery,
and quality validation.

Usage:
    # Process all PDFs in data/pdfs
    python scripts/process_historical_data.py

    # Process specific directory
    python scripts/process_historical_data.py --pdf-dir /path/to/pdfs

    # Process with custom workers
    python scripts/process_historical_data.py --workers 8

    # Process specific document types
    python scripts/process_historical_data.py --types hansard votes

    # Force reprocess all PDFs
    python scripts/process_historical_data.py --force
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from hansard_tales.config.settings import Config
from hansard_tales.processors.pdf_processor import PDFProcessor
from hansard_tales.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessedPDF:
    """Result of processing a single PDF."""

    pdf_path: str
    pdf_date: str
    status: str  # "success", "error", "warning", "skipped"
    reason: str | None = None
    statements: int = 0
    processing_time: float = 0.0
    error_message: str | None = None


class HistoricalDataProcessor:
    """
    Process historical parliamentary PDFs with quality assurance.

    This class manages the complete pipeline for processing historical
    parliamentary data including batch processing, parallel execution,
    error recovery, and validation.

    Attributes:
        pdf_dir: Directory containing PDFs to process
        db_path: Path to database
        workers: Number of parallel workers
        force: Force reprocess even if already processed
    """

    def __init__(
        self,
        pdf_dir: Path | None = None,
        db_path: Path | None = None,
        workers: int = 4,
        force: bool = False,
    ):
        """
        Initialize processor.

        Args:
            pdf_dir: Directory containing PDFs (default: data/pdfs)
            db_path: Path to database (default: from config)
            workers: Number of parallel workers (default: 4)
            force: Force reprocess even if already processed (default: False)
        """
        self.config = Config()
        self.pdf_dir = pdf_dir or self.config.scraper.download_dir
        self.db_path = db_path or Path(self.config.database.database + ".db")
        self.workers = workers
        self.force = force

        # Statistics
        self.stats = {
            "total": 0,
            "success": 0,
            "error": 0,
            "warning": 0,
            "skipped": 0,
            "total_statements": 0,
            "total_time": 0.0,
        }

        # Error tracking
        self.errors = []

    def find_pdfs(self, document_types: list[str] | None = None) -> list[Path]:
        """
        Find all PDFs in directory matching document types.

        Args:
            document_types: List of document types to process (hansard, votes)
                          If None, process all PDFs

        Returns:
            List of PDF paths to process
        """
        if not self.pdf_dir.exists():
            logger.error(f"PDF directory not found: {self.pdf_dir}")
            return []

        pdfs = []

        # Find all PDFs
        for pdf_path in self.pdf_dir.glob("*.pdf"):
            # Filter by document type if specified
            if document_types:
                filename = pdf_path.name.lower()
                if not any(doc_type in filename for doc_type in document_types):
                    continue

            pdfs.append(pdf_path)

        logger.info(f"Found {len(pdfs)} PDFs to process")
        return sorted(pdfs)

    def process_single_pdf(self, pdf_path: Path) -> ProcessedPDF:
        """
        Process a single PDF file (stateless, idempotent, portable).

        This function is designed to be:
        - Stateless: No shared state between calls
        - Idempotent: Can be called multiple times safely
        - Portable: Can run on any machine

        Args:
            pdf_path: Path to PDF file

        Returns:
            ProcessedPDF with processing results
        """
        start_time = datetime.now()

        try:
            # Check if already processed (unless force=True)
            if not self.force and self._is_already_processed(pdf_path):
                return ProcessedPDF(
                    pdf_path=str(pdf_path),
                    pdf_date="",
                    status="skipped",
                    reason="already_processed",
                )

            # Create processor instance (thread-safe)
            processor = PDFProcessor()

            # Process PDF
            result = processor.process(pdf_path)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()

            # Extract date from metadata if available
            pdf_date = result.metadata.get("date", "")

            return ProcessedPDF(
                pdf_path=str(pdf_path),
                pdf_date=pdf_date,
                status="success",
                statements=len(result.text_blocks),  # Use text blocks as proxy for statements
                processing_time=processing_time,
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error processing {pdf_path}: {e}")

            return ProcessedPDF(
                pdf_path=str(pdf_path),
                pdf_date="",
                status="error",
                error_message=str(e),
                processing_time=processing_time,
            )

    def process_batch(
        self,
        pdf_paths: list[Path],
        max_retries: int = 3,
    ) -> list[ProcessedPDF]:
        """
        Process batch of PDFs with parallel workers and retry logic.

        Args:
            pdf_paths: List of PDF paths to process
            max_retries: Maximum retry attempts for failed PDFs

        Returns:
            List of ProcessedPDF results
        """
        results = []
        failed_pdfs = []

        # Process PDFs in parallel
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # Submit all tasks
            future_to_pdf = {
                executor.submit(self.process_single_pdf, pdf): pdf for pdf in pdf_paths
            }

            # Process results with progress bar
            with tqdm(total=len(pdf_paths), desc="Processing PDFs") as pbar:
                for future in as_completed(future_to_pdf):
                    pdf = future_to_pdf[future]

                    try:
                        result = future.result()
                        results.append(result)

                        # Update statistics
                        self.stats["total"] += 1
                        self.stats[result.status] += 1
                        self.stats["total_statements"] += result.statements
                        self.stats["total_time"] += result.processing_time

                        # Track failed PDFs for retry
                        if result.status == "error":
                            failed_pdfs.append(pdf)
                            self.errors.append(
                                {
                                    "pdf": str(pdf),
                                    "error": result.error_message,
                                }
                            )

                    except Exception as e:
                        logger.error(f"Unexpected error processing {pdf}: {e}")
                        self.stats["total"] += 1
                        self.stats["error"] += 1
                        failed_pdfs.append(pdf)
                        self.errors.append({"pdf": str(pdf), "error": str(e)})

                    pbar.update(1)

        # Retry failed PDFs
        if failed_pdfs and max_retries > 0:
            logger.info(f"Retrying {len(failed_pdfs)} failed PDFs...")
            retry_results = self._retry_failed_pdfs(failed_pdfs, max_retries - 1)
            results.extend(retry_results)

        return results

    def _retry_failed_pdfs(
        self,
        failed_pdfs: list[Path],
        max_retries: int,
    ) -> list[ProcessedPDF]:
        """
        Retry processing failed PDFs with exponential backoff.

        Args:
            failed_pdfs: List of PDFs that failed processing
            max_retries: Maximum retry attempts remaining

        Returns:
            List of ProcessedPDF results from retries
        """
        import time

        results = []

        for attempt in range(max_retries):
            if not failed_pdfs:
                break

            logger.info(f"Retry attempt {attempt + 1}/{max_retries}")

            # Wait before retry (exponential backoff)
            if attempt > 0:
                wait_time = 2**attempt
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)

            # Retry failed PDFs
            retry_results = []
            still_failed = []

            for pdf in failed_pdfs:
                result = self.process_single_pdf(pdf)
                retry_results.append(result)

                if result.status == "error":
                    still_failed.append(pdf)

            results.extend(retry_results)
            failed_pdfs = still_failed

        return results

    def _is_already_processed(self, pdf_path: Path) -> bool:
        """
        Check if PDF has already been processed.

        Queries the database to check if this PDF has been processed.

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if PDF has been processed, False otherwise
        """
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker

            from hansard_tales.database.models import DownloadedFileORM

            # Get database connection
            engine = create_engine(f"sqlite:///{self.db_path}")
            Session = sessionmaker(bind=engine)
            session = Session()

            try:
                # Check if file exists in database
                existing = (
                    session.query(DownloadedFileORM)
                    .filter(DownloadedFileORM.file_path == str(pdf_path))
                    .first()
                )

                return existing is not None

            finally:
                session.close()

        except Exception:
            # If database check fails, assume not processed
            return False

    def validate_results(self, results: list[ProcessedPDF]) -> dict:
        """
        Validate processing results and generate quality report.

        Args:
            results: List of processing results

        Returns:
            Dictionary with validation statistics
        """
        validation = {
            "total_pdfs": len(results),
            "successful": sum(1 for r in results if r.status == "success"),
            "failed": sum(1 for r in results if r.status == "error"),
            "skipped": sum(1 for r in results if r.status == "skipped"),
            "warnings": sum(1 for r in results if r.status == "warning"),
            "total_statements": sum(r.statements for r in results),
            "avg_statements_per_pdf": 0.0,
            "avg_processing_time": 0.0,
            "quality_issues": [],
        }

        # Calculate averages
        successful_results = [r for r in results if r.status == "success"]
        if successful_results:
            validation["avg_statements_per_pdf"] = sum(
                r.statements for r in successful_results
            ) / len(successful_results)
            validation["avg_processing_time"] = sum(
                r.processing_time for r in successful_results
            ) / len(successful_results)

        # Identify quality issues
        for result in results:
            if result.status == "success" and result.statements == 0:
                validation["quality_issues"].append(
                    {
                        "pdf": result.pdf_path,
                        "issue": "no_statements_extracted",
                    }
                )

        return validation

    def generate_report(
        self,
        results: list[ProcessedPDF],
        validation: dict,
        output_path: Path | None = None,
    ) -> None:
        """
        Generate processing report.

        Args:
            results: List of processing results
            validation: Validation statistics
            output_path: Path to save report (default: data/logs/processing_report.txt)
        """
        if output_path is None:
            output_path = Path("data/logs/processing_report.txt")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("HISTORICAL DATA PROCESSING REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"PDF Directory: {self.pdf_dir}\n")
            f.write(f"Workers: {self.workers}\n")
            f.write(f"Force Reprocess: {self.force}\n")
            f.write("\n")

            # Summary statistics
            f.write("SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total PDFs:           {validation['total_pdfs']}\n")
            f.write(f"Successful:           {validation['successful']}\n")
            f.write(f"Failed:               {validation['failed']}\n")
            f.write(f"Skipped:              {validation['skipped']}\n")
            f.write(f"Warnings:             {validation['warnings']}\n")
            f.write(f"Total Statements:     {validation['total_statements']}\n")
            f.write(f"Avg Statements/PDF:   {validation['avg_statements_per_pdf']:.1f}\n")
            f.write(f"Avg Processing Time:  {validation['avg_processing_time']:.2f}s\n")
            f.write("\n")

            # Quality issues
            if validation["quality_issues"]:
                f.write("QUALITY ISSUES\n")
                f.write("-" * 80 + "\n")
                for issue in validation["quality_issues"]:
                    f.write(f"  {issue['pdf']}: {issue['issue']}\n")
                f.write("\n")

            # Errors
            if self.errors:
                f.write("ERRORS\n")
                f.write("-" * 80 + "\n")
                for error in self.errors:
                    f.write(f"  {error['pdf']}\n")
                    f.write(f"    Error: {error['error']}\n")
                f.write("\n")

            # Detailed results
            f.write("DETAILED RESULTS\n")
            f.write("-" * 80 + "\n")
            for result in results:
                f.write(f"{result.pdf_path}\n")
                f.write(f"  Status:      {result.status}\n")
                f.write(f"  Statements:  {result.statements}\n")
                f.write(f"  Time:        {result.processing_time:.2f}s\n")
                if result.error_message:
                    f.write(f"  Error:       {result.error_message}\n")
                f.write("\n")

        logger.info(f"Report saved to {output_path}")

    def print_summary(self) -> None:
        """Print processing summary to console."""
        print("\n" + "=" * 60)
        print("PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Total PDFs:        {self.stats['total']}")
        print(f"Successful:        {self.stats['success']}")
        print(f"Failed:            {self.stats['error']}")
        print(f"Skipped:           {self.stats['skipped']}")
        print(f"Warnings:          {self.stats['warning']}")
        print(f"Total Statements:  {self.stats['total_statements']}")
        print(f"Total Time:        {self.stats['total_time']:.2f}s")

        if self.stats["success"] > 0:
            avg_time = self.stats["total_time"] / self.stats["success"]
            avg_statements = self.stats["total_statements"] / self.stats["success"]
            print(f"Avg Time/PDF:      {avg_time:.2f}s")
            print(f"Avg Statements:    {avg_statements:.1f}")

        print("=" * 60)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Process historical parliamentary PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--pdf-dir",
        type=Path,
        help="Directory containing PDFs to process (default: data/pdfs)",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        help="Path to database (default: from config)",
    )
    parser.add_argument(
        "--types",
        nargs="+",
        choices=["hansard", "votes", "all"],
        default=["all"],
        help="Document types to process (default: all)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocess even if already processed",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retry attempts for failed PDFs (default: 3)",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        help="Path to save processing report",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Parse document types
    document_types = args.types
    if "all" in document_types:
        document_types = None  # Process all PDFs

    # Create processor
    processor = HistoricalDataProcessor(
        pdf_dir=args.pdf_dir,
        db_path=args.db_path,
        workers=args.workers,
        force=args.force,
    )

    try:
        # Find PDFs to process
        pdfs = processor.find_pdfs(document_types)

        if not pdfs:
            logger.warning("No PDFs found to process")
            return 0

        # Process PDFs
        logger.info(f"Processing {len(pdfs)} PDFs with {args.workers} workers...")
        results = processor.process_batch(pdfs, max_retries=args.max_retries)

        # Validate results
        validation = processor.validate_results(results)

        # Generate report
        processor.generate_report(results, validation, args.report_path)

        # Print summary
        processor.print_summary()

        # Return error code if any PDFs failed
        if validation["failed"] > 0:
            logger.warning(f"{validation['failed']} PDFs failed processing")
            return 1

        return 0

    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        processor.print_summary()
        return 1

    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
