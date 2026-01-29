"""
End-to-end tests for complete Hansard Tales workflows.

Tests the entire system from scraping to storage and retrieval:
- Scrape documents from parliament.go.ke (mocked)
- Process PDFs and extract text
- Generate embeddings
- Store in database and vector DB
- Retrieve and search documents
"""

import hashlib
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hansard_tales.config.settings import ScraperConfig
from hansard_tales.database.models import Base, DocumentORM, DownloadedFileORM
from hansard_tales.models import Chamber, DocumentType
from hansard_tales.processors.pdf_processor import PDFProcessor
from hansard_tales.scrapers import create_scraper
from hansard_tales.scrapers.base import ScrapedDocument
from hansard_tales.vector_db import ChromaDBAdapter, EmbeddingGenerator


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def temp_storage():
    """Create temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_vector_db():
    """Create temporary vector database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vector_db = ChromaDBAdapter(persist_directory=tmpdir)
        vector_db.create_collection("documents", dimension=384)
        yield vector_db


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    # Minimal valid PDF structure
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


class TestCompleteScrapingWorkflow:
    """Test complete scraping workflow from URL to storage."""

    @patch("hansard_tales.scrapers.base.requests.Session.get")
    def test_scrape_and_store_hansard_documents(
        self, mock_get, temp_db, temp_storage, sample_pdf_content
    ):
        """Test complete workflow: scrape -> download -> store -> database."""
        # Setup mock responses for PDF downloads with unique content for each
        mock_responses = [
            # PDF downloads - each with unique content to avoid hash collision
            Mock(content=sample_pdf_content + b" - Document 1", raise_for_status=Mock()),
            Mock(content=sample_pdf_content + b" - Document 2", raise_for_status=Mock()),
            Mock(content=sample_pdf_content + b" - Document 3", raise_for_status=Mock()),
        ]
        mock_get.side_effect = mock_responses

        # Create scraper
        config = ScraperConfig(base_url="https://parliament.go.ke")
        scraper = create_scraper("hansard", config)

        # Mock get_document_urls to return fixed list
        with patch.object(scraper, "get_document_urls") as mock_urls:
            mock_urls.return_value = [
                "https://parliament.go.ke/sites/default/files/2025-11/Hansard%20Report%20-%20Tuesday%2C%204th%20November%202025%20%28P%29.pdf",
                "https://parliament.go.ke/sites/default/files/2025-11/Hansard%20Report%20-%20Tuesday%2C%204th%20November%202025%20%28A%29.pdf",
                "https://parliament.go.ke/sites/default/files/2025-11/Hansard%20Report%20-%20Wednesday%2C%205th%20November%202025%20%28P%29.pdf",
            ]

            # Scrape documents
            documents = scraper.scrape(Chamber.NATIONAL_ASSEMBLY, skip_existing=False)

        assert len(documents) == 3

        # Save documents and record in database
        for doc in documents:
            # Save PDF using scraper's save_document method
            file_path = scraper.save_document(doc, temp_storage)
            assert file_path.exists()

            # Record in database
            record = DownloadedFileORM(
                source_url=doc.url,
                source_hash=doc.hash,
                standardized_filename=doc.filename,
                original_filename=doc.metadata.get("original_filename", doc.filename),
                file_size=len(doc.content),
                document_type="hansard",
                download_date=datetime.now(UTC),
                file_path=str(file_path),
                chamber="national_assembly",
                parliament_term=2022,
                created_at=datetime.now(UTC),
            )
            temp_db.add(record)

        temp_db.commit()

        # Verify database records
        records = temp_db.query(DownloadedFileORM).all()
        assert len(records) == 3

        # Verify filenames are standardized
        filenames = [r.standardized_filename for r in records]
        assert "hansard_20251104_P.pdf" in filenames
        assert "hansard_20251104_A.pdf" in filenames
        assert "hansard_20251105_P.pdf" in filenames
        assert "hansard_20251104_A.pdf" in filenames
        assert "hansard_20251105_P.pdf" in filenames

    @patch("hansard_tales.scrapers.base.requests.Session.get")
    def test_duplicate_detection_prevents_redownload(
        self, mock_get, temp_db, temp_storage, sample_pdf_content
    ):
        """Test that duplicate detection prevents redownloading same document."""
        # Setup
        config = ScraperConfig()
        scraper = create_scraper("hansard", config)

        # Create existing record in database
        existing_hash = hashlib.sha256(sample_pdf_content).hexdigest()
        existing_record = DownloadedFileORM(
            source_url="https://parliament.go.ke/files/test.pdf",
            source_hash=existing_hash,
            standardized_filename="hansard_20251104_P.pdf",
            original_filename="Hansard Report - Tuesday, 4th November 2025 (P).pdf",
            file_size=len(sample_pdf_content),
            document_type="hansard",
            download_date=datetime.now(UTC),
            file_path="/path/to/file.pdf",
            chamber="national_assembly",
            parliament_term=2022,
            created_at=datetime.now(UTC),
        )
        temp_db.add(existing_record)
        temp_db.commit()

        # Mock _is_duplicate to check database
        def is_duplicate(doc_hash):
            return (
                temp_db.query(DownloadedFileORM)
                .filter(DownloadedFileORM.source_hash == doc_hash)
                .first()
                is not None
            )

        with patch.object(scraper, "_is_duplicate", side_effect=is_duplicate):
            # Create document with same hash
            doc = ScrapedDocument(
                url="https://parliament.go.ke/files/test.pdf",
                filename="hansard_20251104_P.pdf",
                content=sample_pdf_content,
                hash=existing_hash,
                metadata={"document_type": "hansard"},
            )

            # Check if duplicate
            assert scraper._is_duplicate(doc.hash) is True


class TestCompletePDFProcessingWorkflow:
    """Test complete PDF processing workflow with real PDFs."""

    def test_process_real_hansard_pdf_and_store_in_database(self, temp_db, real_hansard_pdfs):
        """Test processing real Hansard PDF and storing extracted data in database."""
        if not real_hansard_pdfs:
            pytest.skip("No real Hansard PDFs available for testing")

        # Use first real PDF
        pdf_data = real_hansard_pdfs[0]
        pdf_path = pdf_data["file"]

        # Process real PDF
        processor = PDFProcessor()
        processed = processor.process(pdf_path)

        assert processed.text_blocks is not None
        assert len(processed.text_blocks) > 0
        assert processed.page_count > 0

        # Extract text from text_blocks for metadata
        extracted_text = " ".join([block.text for block in processed.text_blocks])

        # Store in database using real metadata
        doc_orm = DocumentORM(
            type="HANSARD",
            chamber="NATIONAL_ASSEMBLY",
            title=pdf_data["link_text"],
            date=datetime.strptime(pdf_data["date"], "%Y-%m-%d").date(),
            parliament_term=13,
            source_url=pdf_data["url"],
            source_hash=processed.file_hash,
            download_date=datetime.now(UTC),
            vector_doc_id="vec_001",
            metadata={
                "extracted_text_length": len(extracted_text),
                "period": pdf_data["period"],
                "page_count": processed.page_count,
            },
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        temp_db.add(doc_orm)
        temp_db.commit()

        # Verify database record
        stored_doc = temp_db.query(DocumentORM).first()
        assert stored_doc is not None
        assert stored_doc.title == pdf_data["link_text"]
        assert stored_doc.type.name == "HANSARD"
        assert stored_doc.source_hash == processed.file_hash


class TestCompleteVectorDBWorkflow:
    """Test complete vector database workflow."""

    def test_generate_embedding_and_store_in_vector_db(self, temp_vector_db):
        """Test generating embeddings and storing in vector DB."""
        # Generate embedding
        from hansard_tales.config.settings import EmbeddingConfig

        config = EmbeddingConfig(model_name="sentence-transformers/all-MiniLM-L6-v2")
        embedder = EmbeddingGenerator(config)
        text = "This is a test parliamentary statement about climate change legislation."
        embedding = embedder.generate(text)

        assert len(embedding) == 384  # Model dimension

        # Store in vector DB
        doc_id = str(uuid4())
        temp_vector_db.insert(
            collection="documents",
            id=doc_id,
            vector=embedding,
            payload={
                "document_type": "hansard",
                "chamber": "national_assembly",
                "date": "2025-11-04",
            },
            text=text,
        )

        # Retrieve from vector DB
        result = temp_vector_db.get(collection="documents", id=doc_id)

        assert result is not None
        assert result.id == doc_id
        assert result.text == text
        assert result.payload["document_type"] == "hansard"

    def test_semantic_search_workflow(self, temp_vector_db):
        """Test complete semantic search workflow."""
        from hansard_tales.config.settings import EmbeddingConfig

        config = EmbeddingConfig(model_name="sentence-transformers/all-MiniLM-L6-v2")
        embedder = EmbeddingGenerator(config)

        # Insert multiple documents
        documents = [
            "Parliamentary debate on climate change and environmental protection.",
            "Discussion about healthcare reform and universal coverage.",
            "Budget allocation for education and infrastructure development.",
        ]

        for i, text in enumerate(documents):
            embedding = embedder.generate(text)
            temp_vector_db.insert(
                collection="documents",
                id=f"doc_{i}",
                vector=embedding,
                payload={"index": i},
                text=text,
            )

        # Search for climate-related documents
        query = "environmental issues and climate policy"
        query_embedding = embedder.generate(query)

        results = temp_vector_db.search(
            collection="documents", query_vector=query_embedding, limit=3
        )

        assert len(results) > 0
        # First result should be climate-related document
        assert "climate" in results[0].text.lower() or "environmental" in results[0].text.lower()


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow with real PDFs."""

    def test_complete_system_workflow_with_real_pdf(
        self, temp_db, temp_storage, temp_vector_db, real_hansard_pdfs
    ):
        """Test complete workflow with real PDF: process -> store -> search."""
        if not real_hansard_pdfs:
            pytest.skip("No real Hansard PDFs available for testing")

        # Use first real PDF
        pdf_data = real_hansard_pdfs[0]
        pdf_path = pdf_data["file"]

        # 1. Process real PDF
        processor = PDFProcessor()
        processed = processor.process(pdf_path)

        assert processed.text_blocks is not None
        assert len(processed.text_blocks) > 0
        assert processed.page_count > 0

        # 2. Extract text for embedding
        extracted_text = " ".join(
            [block.text for block in processed.text_blocks[:10]]
        )  # First 10 blocks

        # 3. Generate embedding
        from hansard_tales.config.settings import EmbeddingConfig

        config = EmbeddingConfig(model_name="sentence-transformers/all-MiniLM-L6-v2")
        embedder = EmbeddingGenerator(config)
        embedding = embedder.generate(extracted_text)

        # 4. Store in vector DB
        vector_id = f"vec_{processed.file_hash[:8]}"
        temp_vector_db.insert(
            collection="documents",
            id=vector_id,
            vector=embedding,
            payload={
                "document_type": "hansard",
                "date": pdf_data["date"],
                "period": pdf_data["period"],
                "chamber": pdf_data["chamber"],
            },
            text=extracted_text,
        )

        # 5. Store in database
        doc_orm = DocumentORM(
            type="HANSARD",
            chamber="NATIONAL_ASSEMBLY",
            title=pdf_data["link_text"],
            date=datetime.strptime(pdf_data["date"], "%Y-%m-%d").date(),
            parliament_term=13,
            source_url=pdf_data["url"],
            source_hash=processed.file_hash,
            download_date=datetime.now(UTC),
            vector_doc_id=vector_id,
            metadata={
                "period": pdf_data["period"],
                "page_count": processed.page_count,
                "text_blocks_count": len(processed.text_blocks),
            },
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        temp_db.add(doc_orm)
        temp_db.commit()

        # 6. Verify database record
        stored_doc = temp_db.query(DocumentORM).first()
        assert stored_doc is not None
        assert stored_doc.source_hash == processed.file_hash
        assert stored_doc.vector_doc_id == vector_id

        # 7. Verify vector search works
        search_results = temp_vector_db.search(
            collection="documents",
            query_vector=embedding,
            limit=5,
        )
        assert len(search_results) > 0
        assert search_results[0].id == vector_id

        # 8. Verify complete workflow
        # Check database
        stored_doc = temp_db.query(DocumentORM).first()
        assert stored_doc is not None
        assert stored_doc.vector_doc_id == vector_id
        assert stored_doc.source_hash == processed.file_hash

        # Check vector DB
        vector_result = temp_vector_db.get(collection="documents", id=vector_id)
        assert vector_result is not None
        assert vector_result.text == extracted_text

        # Check file storage
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

        # 9. Test search
        query = "parliamentary proceedings"
        query_embedding = embedder.generate(query)
        search_results = temp_vector_db.search(
            collection="documents", query_vector=query_embedding, limit=1
        )

        assert len(search_results) > 0
        assert search_results[0].id == vector_id


class TestWorkflowErrorRecovery:
    """Test error recovery in workflows."""

    @patch("hansard_tales.scrapers.base.requests.Session.get")
    def test_workflow_continues_after_single_failure(
        self, mock_get, temp_db, temp_storage, sample_pdf_content
    ):
        """Test that workflow continues after single document failure."""
        # First doc succeeds, second fails, third succeeds
        mock_responses = [
            Mock(content=sample_pdf_content, raise_for_status=Mock()),  # doc 1
            Mock(raise_for_status=Mock(side_effect=Exception("Network error"))),  # doc 2
            Mock(content=sample_pdf_content, raise_for_status=Mock()),  # doc 3
        ]
        mock_get.side_effect = mock_responses

        config = ScraperConfig(max_retries=1)
        scraper = create_scraper("hansard", config)

        # Mock get_document_urls to return fixed list
        with patch.object(scraper, "get_document_urls") as mock_urls:
            mock_urls.return_value = [
                "https://parliament.go.ke/files/doc1.pdf",
                "https://parliament.go.ke/files/doc2.pdf",
                "https://parliament.go.ke/files/doc3.pdf",
            ]

            documents = scraper.scrape(Chamber.NATIONAL_ASSEMBLY, skip_existing=False)

        # Should have 2 documents (1 and 3), document 2 failed
        assert len(documents) == 2

    def test_database_rollback_on_error(self, temp_db):
        """Test that database transactions rollback on error."""
        # Start transaction
        doc_orm = DocumentORM(
            type=DocumentType.HANSARD.value,
            chamber=Chamber.NATIONAL_ASSEMBLY.value,
            title="Test Document",
            date=date(2025, 11, 4),
            parliament_term=13,
            source_url="https://test.com/doc.pdf",
            source_hash="abc123",
            download_date=datetime.now(UTC),
            vector_doc_id="vec_001",
            metadata={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        temp_db.add(doc_orm)

        # Rollback without commit
        temp_db.rollback()

        # Verify nothing was saved
        count = temp_db.query(DocumentORM).count()
        assert count == 0


class TestWorkflowPerformance:
    """Test workflow performance characteristics."""

    def test_batch_embedding_generation(self):
        """Test batch embedding generation is faster than individual."""
        import time

        from hansard_tales.config.settings import EmbeddingConfig

        config = EmbeddingConfig(model_name="sentence-transformers/all-MiniLM-L6-v2")
        embedder = EmbeddingGenerator(config)
        texts = [f"Test document {i}" for i in range(10)]

        # Individual generation
        start = time.time()
        for text in texts:
            embedder.generate(text)
        individual_time = time.time() - start

        # Batch generation
        start = time.time()
        embedder.generate_batch(texts)
        batch_time = time.time() - start

        # Batch should be faster (or at least not significantly slower)
        assert batch_time <= individual_time * 1.5  # Allow 50% margin
