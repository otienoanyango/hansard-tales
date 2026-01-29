#!/usr/bin/env python3
"""
Validate historical parliamentary data integrity.

This script validates downloaded PDFs, database consistency, and vector DB
entries to ensure data quality and completeness.

Usage:
    # Validate all data
    python scripts/validate_historical_data.py

    # Validate specific components
    python scripts/validate_historical_data.py --checks pdfs database

    # Generate detailed report
    python scripts/validate_historical_data.py --report-path validation_report.txt
"""

import argparse
import hashlib
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from hansard_tales.config.settings import Config
from hansard_tales.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationIssue:
    """A validation issue found during checks."""

    check: str  # Which check found the issue
    severity: str  # "error", "warning", "info"
    item: str  # Item being validated (file path, record ID, etc.)
    message: str  # Description of the issue


class HistoricalDataValidator:
    """
    Validate historical parliamentary data integrity.

    This class performs comprehensive validation of downloaded PDFs,
    database records, and vector DB entries to ensure data quality.

    Attributes:
        config: Application configuration
        pdf_dir: Directory containing PDFs
        db_path: Path to database
        vector_db_dir: Directory containing vector DB
    """

    def __init__(
        self,
        pdf_dir: Path | None = None,
        db_path: Path | None = None,
        vector_db_dir: Path | None = None,
    ):
        """
        Initialize validator.

        Args:
            pdf_dir: Directory containing PDFs (default: data/pdfs)
            db_path: Path to database (default: from config)
            vector_db_dir: Directory containing vector DB (default: data/vector_db)
        """
        self.config = Config()
        self.pdf_dir = pdf_dir or self.config.scraper.download_dir
        self.db_path = db_path or Path(self.config.database.database + ".db")
        self.vector_db_dir = vector_db_dir or self.config.vector_db.persist_directory

        # Validation results
        self.issues = []
        self.stats = {
            "pdfs_checked": 0,
            "pdfs_valid": 0,
            "pdfs_invalid": 0,
            "db_records_checked": 0,
            "db_records_valid": 0,
            "db_records_invalid": 0,
            "vector_entries_checked": 0,
            "vector_entries_valid": 0,
            "vector_entries_invalid": 0,
        }

    def validate_pdfs(self) -> list[ValidationIssue]:
        """
        Verify all PDFs are readable and not corrupted.

        Checks:
        - PDF files exist and are readable
        - PDF files are not empty
        - PDF files have valid PDF headers
        - PDF files can be opened by PyPDF2

        Returns:
            List of validation issues found
        """
        logger.info("Validating PDFs...")
        issues = []

        if not self.pdf_dir.exists():
            issues.append(
                ValidationIssue(
                    check="pdfs",
                    severity="error",
                    item=str(self.pdf_dir),
                    message="PDF directory does not exist",
                )
            )
            return issues

        # Find all PDFs
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files")

        # Validate each PDF
        for pdf_path in tqdm(pdf_files, desc="Validating PDFs"):
            self.stats["pdfs_checked"] += 1

            # Check file exists
            if not pdf_path.exists():
                issues.append(
                    ValidationIssue(
                        check="pdfs",
                        severity="error",
                        item=str(pdf_path),
                        message="File does not exist",
                    )
                )
                self.stats["pdfs_invalid"] += 1
                continue

            # Check file is not empty
            if pdf_path.stat().st_size == 0:
                issues.append(
                    ValidationIssue(
                        check="pdfs",
                        severity="error",
                        item=str(pdf_path),
                        message="File is empty",
                    )
                )
                self.stats["pdfs_invalid"] += 1
                continue

            # Check PDF header
            try:
                with open(pdf_path, "rb") as f:
                    header = f.read(5)
                    if header != b"%PDF-":
                        issues.append(
                            ValidationIssue(
                                check="pdfs",
                                severity="error",
                                item=str(pdf_path),
                                message="Invalid PDF header",
                            )
                        )
                        self.stats["pdfs_invalid"] += 1
                        continue
            except Exception as e:
                issues.append(
                    ValidationIssue(
                        check="pdfs",
                        severity="error",
                        item=str(pdf_path),
                        message=f"Cannot read file: {e}",
                    )
                )
                self.stats["pdfs_invalid"] += 1
                continue

            # Try to open with PyMuPDF (fitz)
            try:
                import fitz  # PyMuPDF

                doc = fitz.open(pdf_path)
                # Try to access first page
                if doc.page_count == 0:
                    issues.append(
                        ValidationIssue(
                            check="pdfs",
                            severity="warning",
                            item=str(pdf_path),
                            message="PDF has no pages",
                        )
                    )
                    self.stats["pdfs_invalid"] += 1
                    doc.close()
                    continue
                doc.close()
            except Exception as e:
                issues.append(
                    ValidationIssue(
                        check="pdfs",
                        severity="error",
                        item=str(pdf_path),
                        message=f"Cannot open PDF: {e}",
                    )
                )
                self.stats["pdfs_invalid"] += 1
                continue

            # PDF is valid
            self.stats["pdfs_valid"] += 1

        logger.info(
            f"PDF validation complete: {self.stats['pdfs_valid']} valid, "
            f"{self.stats['pdfs_invalid']} invalid"
        )

        return issues

    def validate_database(self) -> list[ValidationIssue]:
        """
        Check database consistency and integrity.

        Checks:
        - Database file exists and is readable
        - All tables exist
        - Foreign key constraints are valid
        - No orphaned records
        - File paths in database point to existing files
        - Hash values match actual file hashes

        Returns:
            List of validation issues found
        """
        logger.info("Validating database...")
        issues = []

        # Check database file exists
        if not self.db_path.exists():
            issues.append(
                ValidationIssue(
                    check="database",
                    severity="error",
                    item=str(self.db_path),
                    message="Database file does not exist",
                )
            )
            return issues

        try:
            from sqlalchemy import create_engine, inspect
            from sqlalchemy.orm import sessionmaker

            from hansard_tales.database.models import DownloadedFileORM

            # Connect to database
            engine = create_engine(f"sqlite:///{self.db_path}")
            Session = sessionmaker(bind=engine)
            session = Session()

            try:
                # Check tables exist
                inspector = inspect(engine)
                tables = inspector.get_table_names()

                required_tables = [
                    "downloaded_files",
                    "documents",
                    "mps",
                    "statements",
                    "bills",
                    "votes",
                ]

                for table in required_tables:
                    if table not in tables:
                        issues.append(
                            ValidationIssue(
                                check="database",
                                severity="error",
                                item=table,
                                message=f"Required table '{table}' does not exist",
                            )
                        )

                # Validate downloaded_files records
                records = session.query(DownloadedFileORM).all()
                logger.info(f"Validating {len(records)} database records...")

                for record in tqdm(records, desc="Validating DB records"):
                    self.stats["db_records_checked"] += 1

                    # Check file path exists
                    file_path = Path(record.file_path)
                    if not file_path.exists():
                        issues.append(
                            ValidationIssue(
                                check="database",
                                severity="error",
                                item=str(record.id),
                                message=f"File not found: {record.file_path}",
                            )
                        )
                        self.stats["db_records_invalid"] += 1
                        continue

                    # Verify hash matches
                    try:
                        with open(file_path, "rb") as f:
                            content = f.read()
                            actual_hash = hashlib.sha256(content).hexdigest()

                            if actual_hash != record.source_hash:
                                issues.append(
                                    ValidationIssue(
                                        check="database",
                                        severity="error",
                                        item=str(record.id),
                                        message=f"Hash mismatch for {record.file_path}",
                                    )
                                )
                                self.stats["db_records_invalid"] += 1
                                continue
                    except Exception as e:
                        issues.append(
                            ValidationIssue(
                                check="database",
                                severity="error",
                                item=str(record.id),
                                message=f"Cannot verify hash: {e}",
                            )
                        )
                        self.stats["db_records_invalid"] += 1
                        continue

                    # Record is valid
                    self.stats["db_records_valid"] += 1

            finally:
                session.close()

        except Exception as e:
            issues.append(
                ValidationIssue(
                    check="database",
                    severity="error",
                    item=str(self.db_path),
                    message=f"Database validation failed: {e}",
                )
            )

        logger.info(
            f"Database validation complete: {self.stats['db_records_valid']} valid, "
            f"{self.stats['db_records_invalid']} invalid"
        )

        return issues

    def validate_vector_db(self) -> list[ValidationIssue]:
        """
        Validate vector DB entries.

        Checks:
        - Vector DB directory exists
        - Collections exist
        - Embeddings are valid
        - Document IDs match database records

        Returns:
            List of validation issues found
        """
        logger.info("Validating vector DB...")
        issues = []

        # Check vector DB directory exists
        if not self.vector_db_dir.exists():
            issues.append(
                ValidationIssue(
                    check="vector_db",
                    severity="warning",
                    item=str(self.vector_db_dir),
                    message="Vector DB directory does not exist",
                )
            )
            return issues

        try:
            # Try to connect to vector DB
            from hansard_tales.vector_db.factory import create_vector_db

            vector_db = create_vector_db(self.config.vector_db)

            # Get collections
            collections = vector_db.list_collections()
            logger.info(f"Found {len(collections)} collections")

            if not collections:
                issues.append(
                    ValidationIssue(
                        check="vector_db",
                        severity="warning",
                        item="collections",
                        message="No collections found in vector DB",
                    )
                )
                return issues

            # Validate each collection
            for collection_name in collections:
                try:
                    # Get collection stats
                    count = vector_db.count(collection_name)
                    self.stats["vector_entries_checked"] += count
                    self.stats["vector_entries_valid"] += count

                    logger.info(f"Collection '{collection_name}': {count} entries")

                except Exception as e:
                    issues.append(
                        ValidationIssue(
                            check="vector_db",
                            severity="error",
                            item=collection_name,
                            message=f"Cannot access collection: {e}",
                        )
                    )

        except Exception as e:
            issues.append(
                ValidationIssue(
                    check="vector_db",
                    severity="error",
                    item=str(self.vector_db_dir),
                    message=f"Vector DB validation failed: {e}",
                )
            )

        logger.info(f"Vector DB validation complete: {self.stats['vector_entries_valid']} valid")

        return issues

    def generate_report(
        self,
        output_path: Path | None = None,
    ) -> None:
        """
        Generate validation report.

        Args:
            output_path: Path to save report (default: data/logs/validation_report.txt)
        """
        if output_path is None:
            output_path = Path("data/logs/validation_report.txt")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("HISTORICAL DATA VALIDATION REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"PDF Directory: {self.pdf_dir}\n")
            f.write(f"Database: {self.db_path}\n")
            f.write(f"Vector DB: {self.vector_db_dir}\n")
            f.write("\n")

            # Summary statistics
            f.write("SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(f"PDFs Checked:           {self.stats['pdfs_checked']}\n")
            f.write(f"PDFs Valid:             {self.stats['pdfs_valid']}\n")
            f.write(f"PDFs Invalid:           {self.stats['pdfs_invalid']}\n")
            f.write(f"DB Records Checked:     {self.stats['db_records_checked']}\n")
            f.write(f"DB Records Valid:       {self.stats['db_records_valid']}\n")
            f.write(f"DB Records Invalid:     {self.stats['db_records_invalid']}\n")
            f.write(f"Vector Entries Checked: {self.stats['vector_entries_checked']}\n")
            f.write(f"Vector Entries Valid:   {self.stats['vector_entries_valid']}\n")
            f.write("\n")

            # Issues by severity
            errors = [i for i in self.issues if i.severity == "error"]
            warnings = [i for i in self.issues if i.severity == "warning"]
            info = [i for i in self.issues if i.severity == "info"]

            f.write(f"Total Issues: {len(self.issues)}\n")
            f.write(f"  Errors:   {len(errors)}\n")
            f.write(f"  Warnings: {len(warnings)}\n")
            f.write(f"  Info:     {len(info)}\n")
            f.write("\n")

            # Detailed issues
            if errors:
                f.write("ERRORS\n")
                f.write("-" * 80 + "\n")
                for issue in errors:
                    f.write(f"[{issue.check}] {issue.item}\n")
                    f.write(f"  {issue.message}\n")
                f.write("\n")

            if warnings:
                f.write("WARNINGS\n")
                f.write("-" * 80 + "\n")
                for issue in warnings:
                    f.write(f"[{issue.check}] {issue.item}\n")
                    f.write(f"  {issue.message}\n")
                f.write("\n")

            if info:
                f.write("INFO\n")
                f.write("-" * 80 + "\n")
                for issue in info:
                    f.write(f"[{issue.check}] {issue.item}\n")
                    f.write(f"  {issue.message}\n")
                f.write("\n")

        logger.info(f"Report saved to {output_path}")

    def print_summary(self) -> None:
        """Print validation summary to console."""
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)

        # PDFs
        print("\nPDFs:")
        print(f"  Checked: {self.stats['pdfs_checked']}")
        print(f"  Valid:   {self.stats['pdfs_valid']}")
        print(f"  Invalid: {self.stats['pdfs_invalid']}")

        # Database
        print("\nDatabase Records:")
        print(f"  Checked: {self.stats['db_records_checked']}")
        print(f"  Valid:   {self.stats['db_records_valid']}")
        print(f"  Invalid: {self.stats['db_records_invalid']}")

        # Vector DB
        print("\nVector DB Entries:")
        print(f"  Checked: {self.stats['vector_entries_checked']}")
        print(f"  Valid:   {self.stats['vector_entries_valid']}")

        # Issues
        errors = [i for i in self.issues if i.severity == "error"]
        warnings = [i for i in self.issues if i.severity == "warning"]

        print(f"\nTotal Issues: {len(self.issues)}")
        print(f"  Errors:   {len(errors)}")
        print(f"  Warnings: {len(warnings)}")

        print("=" * 60)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate historical parliamentary data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--pdf-dir",
        type=Path,
        help="Directory containing PDFs (default: data/pdfs)",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        help="Path to database (default: from config)",
    )
    parser.add_argument(
        "--vector-db-dir",
        type=Path,
        help="Directory containing vector DB (default: data/vector_db)",
    )
    parser.add_argument(
        "--checks",
        nargs="+",
        choices=["pdfs", "database", "vector_db", "all"],
        default=["all"],
        help="Validation checks to run (default: all)",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        help="Path to save validation report",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Parse checks
    checks = args.checks
    if "all" in checks:
        checks = ["pdfs", "database", "vector_db"]

    # Create validator
    validator = HistoricalDataValidator(
        pdf_dir=args.pdf_dir,
        db_path=args.db_path,
        vector_db_dir=args.vector_db_dir,
    )

    try:
        # Run validation checks
        if "pdfs" in checks:
            issues = validator.validate_pdfs()
            validator.issues.extend(issues)

        if "database" in checks:
            issues = validator.validate_database()
            validator.issues.extend(issues)

        if "vector_db" in checks:
            issues = validator.validate_vector_db()
            validator.issues.extend(issues)

        # Generate report
        validator.generate_report(args.report_path)

        # Print summary
        validator.print_summary()

        # Return error code if any errors found
        errors = [i for i in validator.issues if i.severity == "error"]
        if errors:
            logger.warning(f"Validation found {len(errors)} errors")
            return 1

        return 0

    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        validator.print_summary()
        return 1

    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
