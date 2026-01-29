"""
Tests for process_historical_data.py script.

Tests the historical data processor with sample PDFs to verify
batch processing, parallel execution, error recovery, validation,
and report generation.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from process_historical_data import HistoricalDataProcessor, ProcessedPDF  # noqa: E402


class TestHistoricalDataProcessor:
    """Test suite for HistoricalDataProcessor."""

    def test_initialization(self):
        """Test processor initialization."""
        processor = HistoricalDataProcessor()

        assert processor.pdf_dir is not None
        assert processor.db_path is not None
        assert processor.workers == 4
        assert processor.force is False
        assert "total" in processor.stats
        assert "success" in processor.stats

    def test_find_pdfs_empty_directory(self, tmp_path):
        """Test finding PDFs in empty directory."""
        processor = HistoricalDataProcessor(pdf_dir=tmp_path)

        pdfs = processor.find_pdfs()

        assert len(pdfs) == 0

    def test_find_pdfs_with_files(self, tmp_path):
        """Test finding PDFs in directory with files."""
        # Create test PDFs
        (tmp_path / "hansard_20240101_A.pdf").touch()
        (tmp_path / "hansard_20240102_P.pdf").touch()
        (tmp_path / "votes_20240101T143000Z.pdf").touch()
        (tmp_path / "other_file.txt").touch()

        processor = HistoricalDataProcessor(pdf_dir=tmp_path)

        pdfs = processor.find_pdfs()

        # Should find only PDFs
        assert len(pdfs) == 3
        assert all(p.suffix == ".pdf" for p in pdfs)

    def test_find_pdfs_filter_by_type(self, tmp_path):
        """Test finding PDFs filtered by document type."""
        # Create test PDFs
        (tmp_path / "hansard_20240101_A.pdf").touch()
        (tmp_path / "hansard_20240102_P.pdf").touch()
        (tmp_path / "votes_20240101T143000Z.pdf").touch()

        processor = HistoricalDataProcessor(pdf_dir=tmp_path)

        # Filter for hansard only
        pdfs = processor.find_pdfs(document_types=["hansard"])

        assert len(pdfs) == 2
        assert all("hansard" in p.name for p in pdfs)

    @patch("process_historical_data.PDFProcessor")
    def test_process_single_pdf_success(self, mock_processor_class, tmp_path):
        """Test processing a single PDF successfully."""
        # Create test PDF
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\ntest content")

        # Setup mock
        mock_processor = Mock()
        mock_processor.process_pdf.return_value = {
            "date": "2024-01-01",
            "statements": 10,
        }
        mock_processor_class.return_value = mock_processor

        processor = HistoricalDataProcessor(pdf_dir=tmp_path)

        # Process PDF
        result = processor.process_single_pdf(pdf_path)

        # Verify
        assert result.status == "success"
        assert result.statements == 10
        assert result.pdf_date == "2024-01-01"
        assert result.processing_time > 0

    @patch("process_historical_data.PDFProcessor")
    def test_process_single_pdf_error(self, mock_processor_class, tmp_path):
        """Test processing a PDF that fails."""
        # Create test PDF
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\ntest content")

        # Setup mock to raise exception
        mock_processor = Mock()
        mock_processor.process_pdf.side_effect = Exception("Processing error")
        mock_processor_class.return_value = mock_processor

        processor = HistoricalDataProcessor(pdf_dir=tmp_path)

        # Process PDF
        result = processor.process_single_pdf(pdf_path)

        # Verify error was handled
        assert result.status == "error"
        assert result.error_message == "Processing error"

    def test_process_single_pdf_already_processed(self, tmp_path):
        """Test skipping already processed PDF."""
        # Create test PDF
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\ntest content")

        processor = HistoricalDataProcessor(pdf_dir=tmp_path, force=False)

        # Mock _is_already_processed to return True
        with patch.object(processor, "_is_already_processed", return_value=True):
            result = processor.process_single_pdf(pdf_path)

        # Verify PDF was skipped
        assert result.status == "skipped"
        assert result.reason == "already_processed"

    @patch("process_historical_data.PDFProcessor")
    def test_process_batch(self, mock_processor_class, tmp_path):
        """Test batch processing multiple PDFs."""
        # Create test PDFs
        pdf1 = tmp_path / "test1.pdf"
        pdf2 = tmp_path / "test2.pdf"
        pdf1.write_bytes(b"%PDF-1.4\ntest1")
        pdf2.write_bytes(b"%PDF-1.4\ntest2")

        # Setup mock
        mock_processor = Mock()
        mock_processor.process_pdf.return_value = {
            "date": "2024-01-01",
            "statements": 5,
        }
        mock_processor_class.return_value = mock_processor

        processor = HistoricalDataProcessor(pdf_dir=tmp_path, workers=2)

        # Process batch
        results = processor.process_batch([pdf1, pdf2], max_retries=0)

        # Verify
        assert len(results) == 2
        assert all(r.status == "success" for r in results)
        assert processor.stats["success"] == 2
        assert processor.stats["total_statements"] == 10

    @patch("process_historical_data.PDFProcessor")
    def test_process_batch_with_retry(self, mock_processor_class, tmp_path):
        """Test batch processing with retry logic."""
        # Create test PDF
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\ntest")

        # Setup mock to fail first time, succeed second time
        mock_processor = Mock()
        mock_processor.process_pdf.side_effect = [
            Exception("First attempt failed"),
            {"date": "2024-01-01", "statements": 5},
        ]
        mock_processor_class.return_value = mock_processor

        processor = HistoricalDataProcessor(pdf_dir=tmp_path)

        # Process batch with retry
        results = processor.process_batch([pdf_path], max_retries=1)

        # Verify retry was attempted
        assert len(results) >= 1
        # First result should be error
        assert results[0].status == "error"

    def test_validate_results(self):
        """Test validating processing results."""
        processor = HistoricalDataProcessor()

        # Create test results
        results = [
            ProcessedPDF(
                pdf_path="test1.pdf",
                pdf_date="2024-01-01",
                status="success",
                statements=10,
                processing_time=1.5,
            ),
            ProcessedPDF(
                pdf_path="test2.pdf",
                pdf_date="2024-01-02",
                status="success",
                statements=0,  # Quality issue
                processing_time=1.0,
            ),
            ProcessedPDF(
                pdf_path="test3.pdf",
                pdf_date="",
                status="error",
                error_message="Failed",
            ),
        ]

        # Validate
        validation = processor.validate_results(results)

        # Verify validation stats
        assert validation["total_pdfs"] == 3
        assert validation["successful"] == 2
        assert validation["failed"] == 1
        assert validation["total_statements"] == 10
        assert len(validation["quality_issues"]) == 1
        assert validation["quality_issues"][0]["issue"] == "no_statements_extracted"

    def test_generate_report(self, tmp_path):
        """Test generating processing report."""
        processor = HistoricalDataProcessor()

        # Create test results
        results = [
            ProcessedPDF(
                pdf_path="test1.pdf",
                pdf_date="2024-01-01",
                status="success",
                statements=10,
                processing_time=1.5,
            ),
        ]

        validation = processor.validate_results(results)

        # Generate report
        report_path = tmp_path / "report.txt"
        processor.generate_report(results, validation, report_path)

        # Verify report was created
        assert report_path.exists()

        # Verify report content
        content = report_path.read_text()
        assert "HISTORICAL DATA PROCESSING REPORT" in content
        assert "SUMMARY" in content
        assert "test1.pdf" in content

    def test_print_summary(self, capsys):
        """Test printing processing summary."""
        processor = HistoricalDataProcessor()

        # Set some stats
        processor.stats["total"] = 10
        processor.stats["success"] = 8
        processor.stats["error"] = 2
        processor.stats["total_statements"] = 100
        processor.stats["total_time"] = 50.0

        # Print summary
        processor.print_summary()

        # Capture output
        captured = capsys.readouterr()

        # Verify output contains stats
        assert "PROCESSING SUMMARY" in captured.out
        assert "Total PDFs:        10" in captured.out
        assert "Successful:        8" in captured.out
        assert "Failed:            2" in captured.out
        assert "Total Statements:  100" in captured.out
