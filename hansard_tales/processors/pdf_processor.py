"""
PDF processing module for extracting text, tables, and metadata from PDF documents.

This module provides the core PDFProcessor class for processing parliamentary PDFs
with source tracking (page numbers, line numbers, bounding boxes).
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfplumber

    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


@dataclass
class ExtractedText:
    """Text extracted from PDF with source tracking."""

    text: str
    page_number: int
    line_number: int | None = None
    bbox: tuple | None = None  # Bounding box (x0, y0, x1, y1)


@dataclass
class ExtractedTable:
    """Table extracted from PDF."""

    data: list[list[str]]
    page_number: int
    bbox: tuple | None = None


@dataclass
class ProcessedPDF:
    """Result of PDF processing."""

    file_path: Path
    file_hash: str
    text_blocks: list[ExtractedText]
    tables: list[ExtractedTable]
    metadata: dict[str, Any]
    page_count: int


class PDFProcessor:
    """
    Process PDF documents with text and table extraction.

    This class provides methods for extracting text, tables, and metadata
    from PDF documents while maintaining source tracking (page numbers,
    line numbers, bounding boxes) for anti-hallucination purposes.

    Attributes:
        None (stateless processor)

    Example:
        >>> processor = PDFProcessor()
        >>> result = processor.process(Path("hansard.pdf"))
        >>> print(f"Extracted {len(result.text_blocks)} text blocks")
    """

    def __init__(self):
        """Initialize PDF processor."""
        if not PYMUPDF_AVAILABLE:
            raise ImportError(
                "PyMuPDF (fitz) is required for PDF processing. Install with: pip install PyMuPDF"
            )
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError(
                "pdfplumber is required for table extraction. Install with: pip install pdfplumber"
            )

    def process(self, pdf_path: Path) -> ProcessedPDF:
        """
        Process a PDF file and extract all content.

        Args:
            pdf_path: Path to PDF file

        Returns:
            ProcessedPDF with extracted text, tables, and metadata

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If file is not a valid PDF

        Example:
            >>> processor = PDFProcessor()
            >>> result = processor.process(Path("document.pdf"))
            >>> print(result.page_count)
            10
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Compute hash
        file_hash = self._compute_hash(pdf_path)

        # Extract text with source tracking
        text_blocks = self._extract_text(pdf_path)

        # Extract tables
        tables = self._extract_tables(pdf_path)

        # Extract metadata
        metadata = self._extract_metadata(pdf_path)

        # Get page count
        with fitz.open(pdf_path) as doc:
            page_count = len(doc)

        return ProcessedPDF(
            file_path=pdf_path,
            file_hash=file_hash,
            text_blocks=text_blocks,
            tables=tables,
            metadata=metadata,
            page_count=page_count,
        )

    def _compute_hash(self, pdf_path: Path) -> str:
        """
        Compute SHA256 hash of PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            SHA256 hash as hexadecimal string
        """
        return hashlib.sha256(pdf_path.read_bytes()).hexdigest()

    def _extract_text(self, pdf_path: Path) -> list[ExtractedText]:
        """
        Extract text with page and line tracking.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of ExtractedText objects with source tracking
        """
        text_blocks = []

        with fitz.open(pdf_path) as doc:
            for page_num, page in enumerate(doc, start=1):
                # Get text blocks with bounding boxes
                blocks = page.get_text("blocks")

                for block_num, block in enumerate(blocks):
                    if block[6] == 0:  # Text block (not image)
                        text = block[4].strip()
                        if text:
                            text_blocks.append(
                                ExtractedText(
                                    text=text,
                                    page_number=page_num,
                                    line_number=block_num,
                                    bbox=(block[0], block[1], block[2], block[3]),
                                )
                            )

        return text_blocks

    def _extract_tables(self, pdf_path: Path) -> list[ExtractedTable]:
        """
        Extract tables from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of ExtractedTable objects
        """
        tables = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_tables = page.extract_tables()

                for table in page_tables:
                    if table:  # Skip empty tables
                        tables.append(
                            ExtractedTable(
                                data=table,
                                page_number=page_num,
                                bbox=None,  # pdfplumber doesn't provide bbox easily
                            )
                        )

        return tables

    def _extract_metadata(self, pdf_path: Path) -> dict[str, Any]:
        """
        Extract PDF metadata.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with PDF metadata
        """
        with fitz.open(pdf_path) as doc:
            metadata = doc.metadata

            return {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", ""),
            }

    def extract_text_by_page(self, pdf_path: Path, page_number: int) -> str:
        """
        Extract text from specific page.

        Args:
            pdf_path: Path to PDF file
            page_number: Page number (1-indexed)

        Returns:
            Text content of the page

        Raises:
            ValueError: If page number is invalid
        """
        with fitz.open(pdf_path) as doc:
            if page_number < 1 or page_number > len(doc):
                raise ValueError(f"Invalid page number: {page_number}. PDF has {len(doc)} pages.")

            page = doc[page_number - 1]
            return page.get_text()

    def search_text(self, pdf_path: Path, query: str) -> list[ExtractedText]:
        """
        Search for text in PDF.

        Args:
            pdf_path: Path to PDF file
            query: Text to search for

        Returns:
            List of ExtractedText objects containing the query
        """
        results = []

        with fitz.open(pdf_path) as doc:
            for page_num, page in enumerate(doc, start=1):
                text_instances = page.search_for(query)

                for inst in text_instances:
                    # Get surrounding text
                    text = page.get_text("text", clip=inst)
                    results.append(
                        ExtractedText(
                            text=text,
                            page_number=page_num,
                            bbox=(inst.x0, inst.y0, inst.x1, inst.y1),
                        )
                    )

        return results


class HansardProcessor(PDFProcessor):
    """
    Specialized processor for Hansard documents.

    This class extends PDFProcessor with Hansard-specific processing
    capabilities. Additional MP identification and statement extraction
    will be added in Phase 1.

    Example:
        >>> processor = HansardProcessor()
        >>> result = processor.process_hansard(Path("hansard.pdf"))
    """

    def process_hansard(self, pdf_path: Path) -> ProcessedPDF:
        """
        Process Hansard document with specialized handling.

        Args:
            pdf_path: Path to Hansard PDF file

        Returns:
            ProcessedPDF with Hansard-specific processing

        Note:
            Additional Hansard-specific processing (MP identification,
            statement extraction) will be expanded in Phase 1.
        """
        base_result = self.process(pdf_path)

        # Additional Hansard-specific processing
        # This will be expanded in Phase 1 with:
        # - MP identification
        # - Statement extraction
        # - Speaker attribution

        return base_result


class VotesProcessor(PDFProcessor):
    """
    Specialized processor for Votes & Proceedings documents.

    This class extends PDFProcessor with Votes-specific processing
    capabilities. Additional structured data extraction will be
    added in Phase 1.

    Example:
        >>> processor = VotesProcessor()
        >>> result = processor.process_votes(Path("votes.pdf"))
    """

    def process_votes(self, pdf_path: Path) -> ProcessedPDF:
        """
        Process Votes & Proceedings document with specialized handling.

        Args:
            pdf_path: Path to Votes PDF file

        Returns:
            ProcessedPDF with Votes-specific processing

        Note:
            Additional Votes-specific processing (vote table extraction,
            MP vote parsing) will be expanded in Phase 1.
        """
        base_result = self.process(pdf_path)

        # Additional Votes-specific processing
        # This will be expanded in Phase 1 with:
        # - Vote table extraction
        # - MP vote parsing
        # - Vote result aggregation

        return base_result
