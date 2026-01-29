"""
Unit tests for document storage service.

Tests cover:
- Document storage in SQL and vector databases
- Duplicate detection
- Document retrieval
"""

from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest

from hansard_tales.models.base import Chamber, Document, DocumentType, SourceReference
from hansard_tales.processors.pdf_processor import ExtractedText, ProcessedPDF
from hansard_tales.processors.storage_service import DocumentStorageService


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.query = Mock()
    return session


@pytest.fixture
def mock_vector_db():
    """Create mock vector database."""
    vector_db = Mock()
    vector_db.insert = Mock()
    return vector_db


@pytest.fixture
def mock_embedding_generator():
    """Create mock embedding generator."""
    generator = Mock()
    generator.generate = Mock(return_value=[0.1, 0.2, 0.3])
    return generator


@pytest.fixture
def sample_document():
    """Create sample document for testing."""
    return Document(
        id=uuid4(),
        type=DocumentType.HANSARD,
        chamber=Chamber.NATIONAL_ASSEMBLY,
        title="Test Hansard",
        date=date(2024, 1, 15),
        session_id="session-123",
        parliament_term=13,
        source=SourceReference(
            source_url="https://example.com/test.pdf",
            source_hash="abc123",
            download_date=datetime(2024, 1, 15, 10, 0, 0),
        ),
        vector_doc_id="vec-123",
        metadata={"test": "data"},
        created_at=datetime(2024, 1, 15, 10, 0, 0),
        updated_at=datetime(2024, 1, 15, 10, 0, 0),
    )


@pytest.fixture
def sample_processed_pdf():
    """Create sample processed PDF for testing."""
    return ProcessedPDF(
        file_path=Path("test.pdf"),
        file_hash="abc123",
        text_blocks=[
            ExtractedText(text="First block", page_number=1, line_number=0),
            ExtractedText(text="Second block", page_number=1, line_number=1),
        ],
        tables=[],
        metadata={"title": "Test"},
        page_count=1,
    )


class TestDocumentStorageService:
    """Test suite for DocumentStorageService class."""

    def test_init_success(self, mock_db_session, mock_vector_db, mock_embedding_generator):
        """Test that DocumentStorageService can be instantiated."""
        service = DocumentStorageService(
            db_session=mock_db_session,
            vector_db=mock_vector_db,
            embedding_generator=mock_embedding_generator,
        )

        assert service is not None
        assert service.db == mock_db_session
        assert service.vector_db == mock_vector_db
        assert service.embedding_generator == mock_embedding_generator

    def test_store_document_success(
        self,
        mock_db_session,
        mock_vector_db,
        mock_embedding_generator,
        sample_document,
        sample_processed_pdf,
    ):
        """Test successful document storage."""
        service = DocumentStorageService(
            db_session=mock_db_session,
            vector_db=mock_vector_db,
            embedding_generator=mock_embedding_generator,
        )

        doc_id = service.store_document(sample_processed_pdf, sample_document)

        # Verify document was stored in SQL database
        assert mock_db_session.add.called
        assert mock_db_session.commit.called

        # Verify embedding was generated
        assert mock_embedding_generator.generate.called

        # Verify document was stored in vector database
        assert mock_vector_db.insert.called

        # Verify returned document ID
        assert doc_id == str(sample_document.id)

    def test_store_document_generates_embedding_from_text(
        self,
        mock_db_session,
        mock_vector_db,
        mock_embedding_generator,
        sample_document,
        sample_processed_pdf,
    ):
        """Test that embedding is generated from document text."""
        service = DocumentStorageService(
            db_session=mock_db_session,
            vector_db=mock_vector_db,
            embedding_generator=mock_embedding_generator,
        )

        service.store_document(sample_processed_pdf, sample_document)

        # Verify embedding generator was called with combined text
        mock_embedding_generator.generate.assert_called_once()
        call_args = mock_embedding_generator.generate.call_args[0][0]
        assert "First block" in call_args
        assert "Second block" in call_args

    def test_store_document_vector_db_payload(
        self,
        mock_db_session,
        mock_vector_db,
        mock_embedding_generator,
        sample_document,
        sample_processed_pdf,
    ):
        """Test that vector database receives correct payload."""
        service = DocumentStorageService(
            db_session=mock_db_session,
            vector_db=mock_vector_db,
            embedding_generator=mock_embedding_generator,
        )

        service.store_document(sample_processed_pdf, sample_document)

        # Verify vector DB insert was called with correct parameters
        mock_vector_db.insert.assert_called_once()
        call_kwargs = mock_vector_db.insert.call_args[1]

        assert call_kwargs["collection"] == "documents"
        assert call_kwargs["id"] == sample_document.vector_doc_id
        assert call_kwargs["vector"] == [0.1, 0.2, 0.3]
        assert "payload" in call_kwargs
        assert call_kwargs["payload"]["document_id"] == str(sample_document.id)
        assert call_kwargs["payload"]["document_type"] == "hansard"

    def test_is_duplicate_returns_true_when_exists(
        self, mock_db_session, mock_vector_db, mock_embedding_generator
    ):
        """Test duplicate detection when document exists."""
        # Setup mock to return existing document
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = Mock()  # Document exists
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query

        service = DocumentStorageService(
            db_session=mock_db_session,
            vector_db=mock_vector_db,
            embedding_generator=mock_embedding_generator,
        )

        result = service.is_duplicate("abc123")

        assert result is True

    def test_is_duplicate_returns_false_when_not_exists(
        self, mock_db_session, mock_vector_db, mock_embedding_generator
    ):
        """Test duplicate detection when document doesn't exist."""
        # Setup mock to return None
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None  # No document
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query

        service = DocumentStorageService(
            db_session=mock_db_session,
            vector_db=mock_vector_db,
            embedding_generator=mock_embedding_generator,
        )

        result = service.is_duplicate("xyz789")

        assert result is False

    def test_get_document_returns_document_when_exists(
        self, mock_db_session, mock_vector_db, mock_embedding_generator, sample_document
    ):
        """Test document retrieval when document exists."""
        # Setup mock to return document ORM
        mock_doc_orm = Mock()
        mock_doc_orm.id = sample_document.id
        mock_doc_orm.type = sample_document.type.value
        mock_doc_orm.chamber = sample_document.chamber.value
        mock_doc_orm.title = sample_document.title
        mock_doc_orm.date = sample_document.date
        mock_doc_orm.session_id = sample_document.session_id
        mock_doc_orm.parliament_term = sample_document.parliament_term
        mock_doc_orm.source_url = sample_document.source.source_url
        mock_doc_orm.source_hash = sample_document.source.source_hash
        mock_doc_orm.download_date = sample_document.source.download_date
        mock_doc_orm.vector_doc_id = sample_document.vector_doc_id
        mock_doc_orm.metadata = sample_document.metadata
        mock_doc_orm.created_at = sample_document.created_at
        mock_doc_orm.updated_at = sample_document.updated_at

        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_doc_orm
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query

        service = DocumentStorageService(
            db_session=mock_db_session,
            vector_db=mock_vector_db,
            embedding_generator=mock_embedding_generator,
        )

        result = service.get_document(str(sample_document.id))

        assert result is not None
        assert result.id == sample_document.id
        assert result.title == sample_document.title
        assert result.type == sample_document.type

    def test_get_document_returns_none_when_not_exists(
        self, mock_db_session, mock_vector_db, mock_embedding_generator
    ):
        """Test document retrieval when document doesn't exist."""
        # Setup mock to return None
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query

        service = DocumentStorageService(
            db_session=mock_db_session,
            vector_db=mock_vector_db,
            embedding_generator=mock_embedding_generator,
        )

        result = service.get_document("nonexistent-id")

        assert result is None
