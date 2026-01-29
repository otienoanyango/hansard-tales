"""
Tests for validate_historical_data.py script.

Tests the historical data validator to verify PDF validation,
database consistency checks, vector DB validation, and report generation.
"""

import hashlib
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from validate_historical_data import HistoricalDataValidator, ValidationIssue  # noqa: E402


class TestHistoricalDataValidator:
    """Test suite for HistoricalDataValidator."""

    def test_initialization(self):
        """Test validator initialization."""
        validator = HistoricalDataValidator()

        assert validator.pdf_dir is not None
        assert validator.db_path is not None
        assert validator.vector_db_dir is not None
        assert len(validator.issues) == 0
        assert "pdfs_checked" in validator.stats

    def test_validate_pdfs_directory_not_exists(self, tmp_path):
        """Test validating PDFs when directory doesn't exist."""
        non_existent = tmp_path / "nonexistent"
        validator = HistoricalDataValidator(pdf_dir=non_existent)

        issues = validator.validate_pdfs()

        # Should report directory not found
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "does not exist" in issues[0].message

    def test_validate_pdfs_empty_file(self, tmp_path):
        """Test validating empty PDF file."""
        # Create empty PDF
        pdf_path = tmp_path / "empty.pdf"
        pdf_path.touch()

        validator = HistoricalDataValidator(pdf_dir=tmp_path)

        issues = validator.validate_pdfs()

        # Should report empty file
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "empty" in issues[0].message.lower()
        assert validator.stats["pdfs_invalid"] == 1

    def test_validate_pdfs_invalid_header(self, tmp_path):
        """Test validating PDF with invalid header."""
        # Create file with invalid header
        pdf_path = tmp_path / "invalid.pdf"
        pdf_path.write_bytes(b"NOT A PDF")

        validator = HistoricalDataValidator(pdf_dir=tmp_path)

        issues = validator.validate_pdfs()

        # Should report invalid header
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "header" in issues[0].message.lower()
        assert validator.stats["pdfs_invalid"] == 1

    def test_validate_pdfs_valid_pdf(self, tmp_path):
        """Test validating valid PDF file."""
        # Create minimal valid PDF
        pdf_path = tmp_path / "valid.pdf"
        # Minimal PDF structure
        pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
190
%%EOF"""
        pdf_path.write_bytes(pdf_content)

        validator = HistoricalDataValidator(pdf_dir=tmp_path)

        # Mock fitz.open to avoid actual PDF parsing
        with patch("fitz.open") as mock_fitz:
            mock_doc = Mock()
            mock_doc.page_count = 1
            mock_fitz.return_value = mock_doc

            issues = validator.validate_pdfs()

        # Should pass validation
        assert len(issues) == 0
        assert validator.stats["pdfs_valid"] == 1
        assert validator.stats["pdfs_invalid"] == 0

    def test_validate_database_not_exists(self, tmp_path):
        """Test validating database when it doesn't exist."""
        non_existent = tmp_path / "nonexistent.db"
        validator = HistoricalDataValidator(db_path=non_existent)

        issues = validator.validate_database()

        # Should report database not found
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "does not exist" in issues[0].message

    def test_validate_database_missing_tables(self, tmp_path):
        """Test validating database with missing tables."""
        # Create a temporary database file
        db_path = tmp_path / "test.db"
        db_path.touch()

        validator = HistoricalDataValidator(db_path=db_path)

        # Mock the imports inside the function
        with patch("sqlalchemy.create_engine"), patch(
            "sqlalchemy.orm.sessionmaker"
        ) as mock_sessionmaker, patch("sqlalchemy.inspect") as mock_inspect:
            # Setup mocks
            mock_inspector = Mock()
            mock_inspector.get_table_names.return_value = ["downloaded_files"]  # Missing tables
            mock_inspect.return_value = mock_inspector

            mock_session = Mock()
            mock_session.query.return_value.all.return_value = []
            mock_sessionmaker.return_value.return_value = mock_session

            issues = validator.validate_database()

        # Should report missing tables
        missing_tables = [i for i in issues if "does not exist" in i.message]
        assert len(missing_tables) > 0

    def test_validate_database_file_not_found(self, tmp_path):
        """Test validating database record with missing file."""
        # Create a temporary database file
        db_path = tmp_path / "test.db"
        db_path.touch()

        validator = HistoricalDataValidator(db_path=db_path)

        # Mock the imports inside the function
        with patch("sqlalchemy.create_engine"), patch(
            "sqlalchemy.orm.sessionmaker"
        ) as mock_sessionmaker, patch("sqlalchemy.inspect") as mock_inspect:
            # Setup mocks
            mock_inspector = Mock()
            mock_inspector.get_table_names.return_value = [
                "downloaded_files",
                "documents",
                "mps",
                "statements",
                "bills",
                "votes",
            ]
            mock_inspect.return_value = mock_inspector

            # Create mock record with non-existent file
            mock_record = Mock()
            mock_record.id = "test-id"
            mock_record.file_path = str(tmp_path / "nonexistent.pdf")
            mock_record.source_hash = "abc123"

            mock_session = Mock()
            mock_session.query.return_value.all.return_value = [mock_record]
            mock_sessionmaker.return_value.return_value = mock_session

            issues = validator.validate_database()

        # Should report file not found
        file_issues = [i for i in issues if "not found" in i.message.lower()]
        assert len(file_issues) == 1
        assert validator.stats["db_records_invalid"] == 1

    def test_validate_database_hash_mismatch(self, tmp_path):
        """Test validating database record with hash mismatch."""
        # Create test file
        pdf_path = tmp_path / "test.pdf"
        pdf_content = b"test content"
        pdf_path.write_bytes(pdf_content)
        hashlib.sha256(pdf_content).hexdigest()

        # Create a temporary database file
        db_path = tmp_path / "test.db"
        db_path.touch()

        validator = HistoricalDataValidator(db_path=db_path)

        # Mock the imports inside the function
        with patch("sqlalchemy.create_engine"), patch(
            "sqlalchemy.orm.sessionmaker"
        ) as mock_sessionmaker, patch("sqlalchemy.inspect") as mock_inspect:
            # Setup mocks
            mock_inspector = Mock()
            mock_inspector.get_table_names.return_value = [
                "downloaded_files",
                "documents",
                "mps",
                "statements",
                "bills",
                "votes",
            ]
            mock_inspect.return_value = mock_inspector

            # Create mock record with wrong hash
            mock_record = Mock()
            mock_record.id = "test-id"
            mock_record.file_path = str(pdf_path)
            mock_record.source_hash = "wrong_hash"

            mock_session = Mock()
            mock_session.query.return_value.all.return_value = [mock_record]
            mock_sessionmaker.return_value.return_value = mock_session

            issues = validator.validate_database()

        # Should report hash mismatch
        hash_issues = [i for i in issues if "mismatch" in i.message.lower()]
        assert len(hash_issues) == 1
        assert validator.stats["db_records_invalid"] == 1

    def test_validate_vector_db_directory_not_exists(self, tmp_path):
        """Test validating vector DB when directory doesn't exist."""
        non_existent = tmp_path / "nonexistent"
        validator = HistoricalDataValidator(vector_db_dir=non_existent)

        issues = validator.validate_vector_db()

        # Should report directory not found
        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert "does not exist" in issues[0].message

    def test_validate_vector_db_no_collections(self, tmp_path):
        """Test validating vector DB with no collections."""
        # Create vector DB directory
        vector_db_dir = tmp_path / "vector_db"
        vector_db_dir.mkdir()

        validator = HistoricalDataValidator(vector_db_dir=vector_db_dir)

        # Mock the create_vector_db function
        with patch("hansard_tales.vector_db.factory.create_vector_db") as mock_create:
            # Setup mock
            mock_vector_db = Mock()
            mock_vector_db.list_collections.return_value = []
            mock_create.return_value = mock_vector_db

            issues = validator.validate_vector_db()

        # Should report no collections
        assert len(issues) == 1
        assert "No collections" in issues[0].message

    def test_validate_vector_db_with_collections(self, tmp_path):
        """Test validating vector DB with collections."""
        # Create vector DB directory
        vector_db_dir = tmp_path / "vector_db"
        vector_db_dir.mkdir()

        validator = HistoricalDataValidator(vector_db_dir=vector_db_dir)

        # Mock the create_vector_db function
        with patch("hansard_tales.vector_db.factory.create_vector_db") as mock_create:
            # Setup mock
            mock_vector_db = Mock()
            mock_vector_db.list_collections.return_value = ["hansard", "votes"]
            mock_vector_db.count.return_value = 100
            mock_create.return_value = mock_vector_db

            issues = validator.validate_vector_db()

        # Should pass validation
        assert len(issues) == 0
        assert validator.stats["vector_entries_valid"] == 200  # 100 per collection

    def test_generate_report(self, tmp_path):
        """Test generating validation report."""
        validator = HistoricalDataValidator()

        # Add some test issues
        validator.issues = [
            ValidationIssue(
                check="pdfs",
                severity="error",
                item="test.pdf",
                message="Invalid PDF",
            ),
            ValidationIssue(
                check="database",
                severity="warning",
                item="record-123",
                message="File not found",
            ),
        ]

        # Set some stats
        validator.stats["pdfs_checked"] = 10
        validator.stats["pdfs_valid"] = 9
        validator.stats["pdfs_invalid"] = 1

        # Generate report
        report_path = tmp_path / "validation_report.txt"
        validator.generate_report(report_path)

        # Verify report was created
        assert report_path.exists()

        # Verify report content
        content = report_path.read_text()
        assert "HISTORICAL DATA VALIDATION REPORT" in content
        assert "SUMMARY" in content
        assert "ERRORS" in content
        assert "WARNINGS" in content
        assert "test.pdf" in content

    def test_print_summary(self, capsys):
        """Test printing validation summary."""
        validator = HistoricalDataValidator()

        # Set some stats
        validator.stats["pdfs_checked"] = 10
        validator.stats["pdfs_valid"] = 9
        validator.stats["pdfs_invalid"] = 1
        validator.stats["db_records_checked"] = 5
        validator.stats["db_records_valid"] = 5
        validator.stats["db_records_invalid"] = 0

        # Add some issues
        validator.issues = [
            ValidationIssue(
                check="pdfs",
                severity="error",
                item="test.pdf",
                message="Invalid",
            ),
        ]

        # Print summary
        validator.print_summary()

        # Capture output
        captured = capsys.readouterr()

        # Verify output contains stats
        assert "VALIDATION SUMMARY" in captured.out
        assert "PDFs:" in captured.out
        assert "Checked: 10" in captured.out
        assert "Valid:   9" in captured.out
        assert "Invalid: 1" in captured.out
        assert "Total Issues: 1" in captured.out
        assert "Errors:   1" in captured.out
