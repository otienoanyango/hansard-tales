"""
Unit tests for Context Retriever.

Tests cover context retrieval using RAG including embedding generation,
historical statement retrieval, bill retrieval, vote retrieval, and
result deduplication.
"""

from unittest.mock import Mock, patch

import numpy as np
import pytest

from hansard_tales.analysis.context_retriever import (
    ContextRetriever,
    RetrievedContext,
)
from hansard_tales.analysis.statement_segmenter import Statement


class TestRetrievedContext:
    """Test suite for RetrievedContext dataclass."""

    def test_create_empty_context(self):
        """Test creating empty context."""
        context = RetrievedContext()

        assert context.historical_statements == []
        assert context.related_bills == []
        assert context.related_votes == []
        assert context.session_context == []
        assert context.is_empty()
        assert context.total_items() == 0

    def test_create_context_with_data(self):
        """Test creating context with data."""
        historical = [{"text": "Previous statement", "metadata": {}}]
        bills = [{"text": "Bill text", "metadata": {}}]
        votes = [{"text": "Vote text", "metadata": {}}]
        session = [{"text": "Session statement", "metadata": {}}]

        context = RetrievedContext(
            historical_statements=historical,
            related_bills=bills,
            related_votes=votes,
            session_context=session,
        )

        assert len(context.historical_statements) == 1
        assert len(context.related_bills) == 1
        assert len(context.related_votes) == 1
        assert len(context.session_context) == 1
        assert not context.is_empty()
        assert context.total_items() == 4

    def test_context_validation(self):
        """Test context validation in __post_init__."""
        # Test with None values (should convert to empty lists)
        context = RetrievedContext(
            historical_statements=None,
            related_bills=None,
            related_votes=None,
            session_context=None,
        )

        assert context.historical_statements == []
        assert context.related_bills == []
        assert context.related_votes == []
        assert context.session_context == []

    def test_total_items_calculation(self):
        """Test total items calculation."""
        context = RetrievedContext(
            historical_statements=[{}, {}],
            related_bills=[{}, {}, {}],
            related_votes=[{}],
            session_context=[{}, {}, {}, {}],
        )

        assert context.total_items() == 10


class TestContextRetriever:
    """Test suite for ContextRetriever."""

    @pytest.fixture
    def mock_vector_db(self):
        """Create mock vector database."""
        mock_db = Mock()
        mock_db.search = Mock(return_value=[])
        return mock_db

    @pytest.fixture
    def mock_embedder(self):
        """Create mock sentence transformer."""
        mock = Mock()
        # Return a numpy array as embedding
        mock.encode = Mock(return_value=np.array([0.1, 0.2, 0.3]))
        return mock

    @pytest.fixture
    def retriever(self, mock_vector_db):
        """Create context retriever instance."""
        retriever = ContextRetriever(vector_db=mock_vector_db, embedding_model="all-MiniLM-L6-v2")
        return retriever

    @pytest.fixture
    def sample_statement(self):
        """Create sample statement for testing."""
        return Statement(
            text="This is a test statement about healthcare policy.",
            mp_id="mp-123",
            start_pos=0,
            end_pos=100,
            page_number=1,
        )

    def test_init(self, mock_vector_db):
        """Test ContextRetriever initialization."""
        retriever = ContextRetriever(vector_db=mock_vector_db, embedding_model="test-model")

        assert retriever.vector_db == mock_vector_db
        assert retriever.embedding_model == "test-model"
        assert retriever.embedder is None  # Lazy initialization

    @patch("sentence_transformers.SentenceTransformer")
    def test_init_embedder(self, mock_st_class, retriever):
        """Test embedding generation."""
        # Setup mock
        mock_embedder = Mock()
        mock_st_class.return_value = mock_embedder

        # Initialize embedder
        retriever._init_embedder()

        # Verify
        assert retriever.embedder is not None
        mock_st_class.assert_called_once_with("all-MiniLM-L6-v2")

    @patch("sentence_transformers.SentenceTransformer")
    def test_init_embedder_import_error(self, mock_st_class, retriever):
        """Test embedder initialization with import error."""
        # Setup mock to raise ImportError
        mock_st_class.side_effect = ImportError("Module not found")

        # Verify exception is raised
        with pytest.raises(ImportError):
            retriever._init_embedder()

    @patch("sentence_transformers.SentenceTransformer")
    def test_retrieve_full_context(self, mock_st_class, retriever, sample_statement, mock_embedder):
        """Test retrieving full context for a statement."""
        # Setup mocks
        mock_st_class.return_value = mock_embedder

        # Create mock search results
        from hansard_tales.vector_db.interface import VectorSearchResult

        mock_result = VectorSearchResult(
            id="stmt-1",
            score=0.5,
            payload={"mp_id": "mp-123", "date": "2024-01-01"},
            text="Historical statement text",
        )
        retriever.vector_db.search = Mock(return_value=[mock_result])

        # Retrieve context
        context = retriever.retrieve(sample_statement, top_k=5)

        # Verify
        assert isinstance(context, RetrievedContext)
        assert retriever.embedder is not None
        mock_embedder.encode.assert_called_once()

    @patch("sentence_transformers.SentenceTransformer")
    def test_retrieve_historical_statements(
        self, mock_st_class, retriever, sample_statement, mock_embedder
    ):
        """Test historical statement retrieval."""
        # Setup mocks
        mock_st_class.return_value = mock_embedder
        query_embedding = np.array([0.1, 0.2, 0.3])

        from hansard_tales.vector_db.interface import VectorSearchResult

        mock_results = [
            VectorSearchResult(
                id="stmt-1",
                score=0.3,
                payload={"mp_id": "mp-123", "date": "2024-01-01"},
                text="Previous statement 1",
            ),
            VectorSearchResult(
                id="stmt-2",
                score=0.5,
                payload={"mp_id": "mp-123", "date": "2024-01-02"},
                text="Previous statement 2",
            ),
        ]
        retriever.vector_db.search = Mock(return_value=mock_results)

        # Retrieve historical statements
        retriever._init_embedder()
        historical = retriever._retrieve_historical_statements(
            sample_statement, query_embedding, top_k=5
        )

        # Verify
        assert len(historical) == 2
        assert historical[0]["text"] == "Previous statement 1"
        assert historical[0]["metadata"]["mp_id"] == "mp-123"
        assert historical[0]["distance"] == 0.3
        assert historical[1]["text"] == "Previous statement 2"

        # Verify search was called with correct parameters
        retriever.vector_db.search.assert_called_once()
        call_args = retriever.vector_db.search.call_args
        assert call_args[1]["collection"] == "statements"
        assert call_args[1]["filter"]["mp_id"] == "mp-123"
        assert call_args[1]["filter"]["document_type"] == "statement"
        assert call_args[1]["limit"] == 5

    def test_retrieve_historical_statements_no_mp_id(self, retriever, mock_embedder):
        """Test historical retrieval with no MP ID."""
        statement = Statement(text="Test statement", mp_id=None, start_pos=0, end_pos=100)
        query_embedding = np.array([0.1, 0.2, 0.3])

        historical = retriever._retrieve_historical_statements(statement, query_embedding, top_k=5)

        assert historical == []

    def test_retrieve_historical_statements_error(self, retriever, sample_statement, mock_embedder):
        """Test historical retrieval with error."""
        query_embedding = np.array([0.1, 0.2, 0.3])
        retriever.vector_db.search = Mock(side_effect=Exception("Database error"))

        historical = retriever._retrieve_historical_statements(
            sample_statement, query_embedding, top_k=5
        )

        assert historical == []

    def test_retrieve_related_bills(self, retriever, mock_embedder):
        """Test bill retrieval."""
        query_embedding = np.array([0.1, 0.2, 0.3])

        from hansard_tales.vector_db.interface import VectorSearchResult

        mock_results = [
            VectorSearchResult(
                id="bill-1",
                score=0.2,
                payload={"bill_id": "bill-1", "title": "Finance Bill 2024"},
                text="Finance Bill 2024",
            ),
            VectorSearchResult(
                id="bill-2",
                score=0.4,
                payload={"bill_id": "bill-2", "title": "Health Bill 2024"},
                text="Health Bill 2024",
            ),
        ]
        retriever.vector_db.search = Mock(return_value=mock_results)

        bills = retriever._retrieve_related_bills(query_embedding, top_k=3)

        assert len(bills) == 2
        assert bills[0]["text"] == "Finance Bill 2024"
        assert bills[0]["metadata"]["bill_id"] == "bill-1"
        assert bills[0]["distance"] == 0.2

        # Verify search parameters
        call_args = retriever.vector_db.search.call_args
        assert call_args[1]["collection"] == "bills"
        assert call_args[1]["filter"]["document_type"] == "bill"
        assert call_args[1]["limit"] == 3

    def test_retrieve_related_bills_error(self, retriever):
        """Test bill retrieval with error."""
        query_embedding = np.array([0.1, 0.2, 0.3])
        retriever.vector_db.search = Mock(side_effect=Exception("Database error"))

        bills = retriever._retrieve_related_bills(query_embedding, top_k=3)

        assert bills == []

    def test_retrieve_related_votes(self, retriever):
        """Test vote retrieval."""
        query_embedding = np.array([0.1, 0.2, 0.3])

        from hansard_tales.vector_db.interface import VectorSearchResult

        mock_result = VectorSearchResult(
            id="vote-1",
            score=0.3,
            payload={"vote_id": "vote-1", "result": "passed"},
            text="Vote on Finance Bill",
        )
        retriever.vector_db.search = Mock(return_value=[mock_result])

        votes = retriever._retrieve_related_votes(query_embedding, top_k=3)

        assert len(votes) == 1
        assert votes[0]["text"] == "Vote on Finance Bill"
        assert votes[0]["metadata"]["vote_id"] == "vote-1"
        assert votes[0]["distance"] == 0.3

        # Verify search parameters
        call_args = retriever.vector_db.search.call_args
        assert call_args[1]["collection"] == "votes"
        assert call_args[1]["filter"]["document_type"] == "vote"
        assert call_args[1]["limit"] == 3

    def test_retrieve_related_votes_error(self, retriever):
        """Test vote retrieval with error."""
        query_embedding = np.array([0.1, 0.2, 0.3])
        retriever.vector_db.search = Mock(side_effect=Exception("Database error"))

        votes = retriever._retrieve_related_votes(query_embedding, top_k=3)

        assert votes == []

    def test_retrieve_session_context(self, retriever, sample_statement):
        """Test session context retrieval."""
        # Currently returns empty list (not implemented)
        session = retriever._retrieve_session_context(sample_statement, top_k=5)

        assert session == []

    def test_retrieve_empty_results(self, retriever, sample_statement):
        """Test retrieval with empty results."""
        retriever.vector_db.search = Mock(return_value=[])

        with patch("sentence_transformers.SentenceTransformer") as mock_st:
            mock_embedder = Mock()
            mock_embedder.encode = Mock(return_value=np.array([0.1, 0.2, 0.3]))
            mock_st.return_value = mock_embedder

            context = retriever.retrieve(sample_statement, top_k=5)

            assert context.is_empty()
            assert context.total_items() == 0

    def test_retrieve_result_deduplication(self, retriever, sample_statement):
        """Test result deduplication."""
        from hansard_tales.vector_db.interface import VectorSearchResult

        # Setup mock to return duplicate results
        mock_results = [
            VectorSearchResult(
                id="1",
                score=0.1,
                payload={"id": "1", "mp_id": "mp-123"},
                text="Statement 1",
            ),
            VectorSearchResult(
                id="1",
                score=0.1,
                payload={"id": "1", "mp_id": "mp-123"},
                text="Statement 1",
            ),
            VectorSearchResult(
                id="2",
                score=0.2,
                payload={"id": "2", "mp_id": "mp-123"},
                text="Statement 2",
            ),
        ]
        retriever.vector_db.search = Mock(return_value=mock_results)

        with patch("sentence_transformers.SentenceTransformer") as mock_st:
            mock_embedder = Mock()
            mock_embedder.encode = Mock(return_value=np.array([0.1, 0.2, 0.3]))
            mock_st.return_value = mock_embedder

            context = retriever.retrieve(sample_statement, top_k=5)

            # Note: Current implementation doesn't deduplicate
            # This test documents current behavior
            # If deduplication is added, update this test
            assert len(context.historical_statements) == 3
