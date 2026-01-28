"""
Shared test fixtures for Hansard Tales test suite.

This module provides reusable fixtures for:
- Temporary directories and files
- Test configurations
- Database sessions
- Vector database instances
- Sample PDFs and documents
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from datetime import date, datetime
from typing import Generator
from unittest.mock import Mock

from hansard_tales.config.settings import (
    Config,
    DatabaseConfig,
    VectorDBConfig,
    EmbeddingConfig,
    ScraperConfig,
)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_config(temp_dir: Path) -> Config:
    """
    Create test configuration with temporary paths.
    
    Uses SQLite and ChromaDB for testing to avoid external dependencies.
    """
    return Config(
        environment="test",
        database=DatabaseConfig(
            engine="sqlite",
            database=str(temp_dir / "test.db"),
        ),
        vector_db=VectorDBConfig(
            engine="chromadb",
            persist_directory=temp_dir / "vector_db",
        ),
        embedding=EmbeddingConfig(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dimension=384,
            batch_size=32,
            device="cpu",
        ),
        scraper=ScraperConfig(
            base_url="https://parliament.go.ke",
            download_dir=temp_dir / "pdfs",
            max_retries=3,
            retry_delay=1.0,
            timeout=30,
        ),
    )


@pytest.fixture
def temp_db(temp_dir: Path) -> Generator[Path, None, None]:
    """
    Create temporary SQLite database with schema.
    
    Yields:
        Path to temporary database file
    """
    db_path = temp_dir / "test.db"
    
    # Create database with basic schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create minimal schema for testing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            chamber TEXT NOT NULL,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_hash TEXT NOT NULL UNIQUE,
            vector_doc_id TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS downloaded_files (
            id TEXT PRIMARY KEY,
            source_url TEXT NOT NULL,
            source_hash TEXT NOT NULL UNIQUE,
            standardized_filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            download_date TEXT NOT NULL,
            file_path TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def sample_pdf(temp_dir: Path) -> Path:
    """
    Create sample PDF for testing.
    
    Creates a simple PDF with test content using reportlab.
    Falls back to creating a dummy file if reportlab is not available.
    """
    pdf_path = temp_dir / "sample_hansard.pdf"
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.drawString(100, 750, "NATIONAL ASSEMBLY")
        c.drawString(100, 730, "HANSARD")
        c.drawString(100, 710, "Thursday, 15th January 2024")
        c.drawString(100, 680, "")
        c.drawString(100, 660, "Hon. John Doe (Nairobi, Party): Mr. Speaker, I rise to...")
        c.drawString(100, 640, "This is a sample statement for testing purposes.")
        c.save()
    except ImportError:
        # Fallback: create a dummy PDF-like file
        pdf_path.write_bytes(b"%PDF-1.4\n%Test PDF\n%%EOF")
    
    return pdf_path


@pytest.fixture
def sample_document():
    """
    Create sample Document model for testing.
    
    Returns a valid Document instance with all required fields.
    """
    from hansard_tales.models.base import Document, DocumentType, Chamber, SourceReference
    
    return Document(
        type=DocumentType.HANSARD,
        chamber=Chamber.NATIONAL_ASSEMBLY,
        title="Test Hansard - 15th January 2024",
        date=date(2024, 1, 15),
        parliament_term=13,
        source=SourceReference(
            source_url="https://parliament.go.ke/test/hansard_20240115.pdf",
            source_hash="abc123def456",
            download_date=datetime.utcnow(),
        ),
        vector_doc_id="test_doc_001",
    )


@pytest.fixture
def sample_statement():
    """
    Create sample Statement model for testing.
    
    Returns a valid Statement instance with all required fields.
    """
    from hansard_tales.models.base import Statement, SourceReference
    from uuid import uuid4
    
    return Statement(
        document_id=uuid4(),
        mp_id=uuid4(),
        text="Mr. Speaker, I rise to address the issue of education funding.",
        source=SourceReference(
            source_url="https://parliament.go.ke/test/hansard_20240115.pdf",
            source_hash="abc123def456",
            download_date=datetime.utcnow(),
            page_number=5,
            line_number=120,
        ),
        vector_doc_id="test_stmt_001",
    )


@pytest.fixture
def mock_vector_db():
    """
    Create mock vector database for testing.
    
    Returns a Mock object with common vector DB methods.
    """
    mock_db = Mock()
    mock_db.create_collection = Mock()
    mock_db.insert = Mock()
    mock_db.search = Mock(return_value=[])
    mock_db.delete = Mock()
    mock_db.get = Mock(return_value=None)
    return mock_db


@pytest.fixture
def mock_embedding_generator():
    """
    Create mock embedding generator for testing.
    
    Returns a Mock object that generates fake embeddings.
    """
    mock_gen = Mock()
    # Return a fake 384-dimensional embedding
    mock_gen.generate = Mock(return_value=[0.1] * 384)
    mock_gen.generate_batch = Mock(return_value=[[0.1] * 384])
    mock_gen.similarity = Mock(return_value=0.95)
    return mock_gen


@pytest.fixture
def sample_pdf_files(temp_dir: Path) -> list[Path]:
    """
    Create multiple sample PDF files for batch testing.
    
    Returns:
        List of paths to sample PDF files
    """
    pdf_files = []
    for i in range(3):
        pdf_path = temp_dir / f"hansard_2024010{i+1}.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%Test PDF %d\n%%EOF" % i)
        pdf_files.append(pdf_path)
    return pdf_files
