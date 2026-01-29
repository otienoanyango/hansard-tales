"""
Shared test fixtures for Hansard Tales tests.

Provides realistic test data including real PDFs from parliament.go.ke
and temporary databases with actual schema.
"""

import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hansard_tales.database.models import Base


@pytest.fixture
def real_hansard_pdfs():
    """
    Provide real Hansard PDFs downloaded from parliament.go.ke.

    Returns:
        List of tuples: (file_path, url, metadata)
    """
    base_dir = Path("tests/data/pdfs/hansard")

    # Real PDFs with their metadata from parliament.go.ke
    pdfs = [
        {
            "file": base_dir / "hansard_20251204_E.pdf",
            "url": "https://www.parliament.go.ke/sites/default/files/2025-12/Hansard%20Report%20-%20Thursday%2C%204th%20December%202025%20%28E%29.pdf",
            "title": "Hansard Report - Thursday, 4th December 2025 (E).pdf",
            "link_text": "Hansard Report - Thursday, 4th December 2025 - Evening Sitting",
            "date": "2025-12-04",
            "period": "E",
            "chamber": "national_assembly",
        },
        {
            "file": base_dir / "hansard_20251204_P.pdf",
            "url": "https://www.parliament.go.ke/sites/default/files/2025-12/Hansard%20Report%20-%20Thursday%2C%204th%20December%202025%20%28P%29.pdf",
            "title": "Hansard Report - Thursday, 4th December 2025 (P).pdf",
            "link_text": "Hansard Report - Thursday, 4th December 2025 - Afternoon Sitting",
            "date": "2025-12-04",
            "period": "P",
            "chamber": "national_assembly",
        },
        {
            "file": base_dir / "hansard_20251203_P.pdf",
            "url": "https://www.parliament.go.ke/sites/default/files/2025-12/Hansard%20Report%20-%20Wednesday%2C%203rd%20December%202025%20%28P%29.pdf",
            "title": "Hansard Report - Wednesday, 3rd December 2025 (P).pdf",
            "link_text": "Hansard Report - Wednesday, 3rd December 2025 - Afternoon Sitting",
            "date": "2025-12-03",
            "period": "P",
            "chamber": "national_assembly",
        },
    ]

    # Filter to only existing files
    existing_pdfs = [pdf for pdf in pdfs if pdf["file"].exists()]

    return existing_pdfs


@pytest.fixture
def temp_db():
    """
    Create temporary SQLite database with actual schema.

    Prefer this over mocking database operations.
    """
    # Create temporary database file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Create engine and tables
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    # Cleanup
    session.close()
    engine.dispose()
    Path(db_path).unlink()


@pytest.fixture
def temp_storage(tmp_path):
    """
    Create temporary storage directory for file operations.

    Prefer this over mocking file operations.
    """
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


@pytest.fixture
def sample_pdf_content():
    """
    Minimal valid PDF content for tests that need to create PDFs.

    Use real_hansard_pdfs fixture when possible instead.
    """
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
306
%%EOF
"""
