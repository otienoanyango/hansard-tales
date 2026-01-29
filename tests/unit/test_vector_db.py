"""Unit tests for vector database adapters."""

import tempfile
from pathlib import Path

import pytest

from hansard_tales.config.settings import EmbeddingConfig, VectorDBConfig
from hansard_tales.vector_db.chromadb_adapter import ChromaDBAdapter
from hansard_tales.vector_db.embedding import EmbeddingGenerator
from hansard_tales.vector_db.factory import create_vector_db


class TestChromaDBAdapter:
    """Test suite for ChromaDB adapter."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for ChromaDB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def vector_db(self, temp_dir):
        """Create ChromaDB adapter for testing."""
        vdb = ChromaDBAdapter(temp_dir)
        vdb.create_collection("test_collection", dimension=384)
        return vdb

    @pytest.fixture
    def generator(self):
        """Create embedding generator for testing."""
        config = EmbeddingConfig(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dimension=384,
            batch_size=32,
            device="cpu",
        )
        return EmbeddingGenerator(config)

    def test_create_collection(self, temp_dir):
        """Test creating a collection."""
        vdb = ChromaDBAdapter(temp_dir)
        vdb.create_collection("test", dimension=384)

        # Should not raise error
        assert True

    def test_insert_and_get(self, vector_db, generator):
        """Test inserting and retrieving a vector."""
        text = "Test parliamentary statement"
        embedding = generator.generate(text)

        vector_db.insert(
            collection="test_collection",
            id="doc_1",
            vector=embedding,
            payload={"type": "statement", "chamber": "national_assembly"},
            text=text,
        )

        result = vector_db.get("test_collection", "doc_1")

        assert result is not None
        assert result.id == "doc_1"
        assert result.text == text
        assert result.payload["type"] == "statement"

    def test_search_similar_vectors(self, vector_db, generator):
        """Test searching for similar vectors."""
        texts = [
            "Parliamentary debate on education policy",
            "Discussion about healthcare reforms",
            "Education system improvements",
        ]

        # Insert documents
        for i, text in enumerate(texts):
            embedding = generator.generate(text)
            vector_db.insert(
                collection="test_collection",
                id=f"doc_{i}",
                vector=embedding,
                payload={"index": i},
                text=text,
            )

        # Search for education-related content
        query_text = "education policy discussion"
        query_embedding = generator.generate(query_text)

        results = vector_db.search(
            collection="test_collection", query_vector=query_embedding, limit=2
        )

        assert len(results) == 2
        # First result should be most similar (education-related)
        assert "education" in results[0].text.lower()

    def test_delete_vector(self, vector_db, generator):
        """Test deleting a vector."""
        text = "Test statement to delete"
        embedding = generator.generate(text)

        vector_db.insert(
            collection="test_collection",
            id="doc_delete",
            vector=embedding,
            payload={"test": "data"},
            text=text,
        )

        # Verify it exists
        result = vector_db.get("test_collection", "doc_delete")
        assert result is not None

        # Delete it
        vector_db.delete("test_collection", "doc_delete")

        # Verify it's gone
        result = vector_db.get("test_collection", "doc_delete")
        assert result is None

    def test_search_with_filter(self, vector_db, generator):
        """Test searching with metadata filters."""
        texts = [
            "National Assembly statement",
            "Senate statement",
            "Another National Assembly statement",
        ]
        chambers = ["national_assembly", "senate", "national_assembly"]

        # Insert documents
        for i, (text, chamber) in enumerate(zip(texts, chambers, strict=False)):
            embedding = generator.generate(text)
            vector_db.insert(
                collection="test_collection",
                id=f"doc_{i}",
                vector=embedding,
                payload={"chamber": chamber},
                text=text,
            )

        # Search with filter
        query_embedding = generator.generate("statement")
        results = vector_db.search(
            collection="test_collection",
            query_vector=query_embedding,
            limit=10,
            filter={"chamber": "national_assembly"},
        )

        # Should only return National Assembly documents
        assert len(results) == 2
        assert all(r.payload["chamber"] == "national_assembly" for r in results)

    def test_get_nonexistent_document(self, vector_db):
        """Test getting a document that doesn't exist."""
        result = vector_db.get("test_collection", "nonexistent_id")
        assert result is None


class TestQdrantAdapter:
    """Test suite for Qdrant adapter."""

    @pytest.fixture
    def mock_qdrant_client(self):
        """Create mock Qdrant client."""
        from unittest.mock import Mock

        client = Mock()

        # Mock recreate_collection
        client.recreate_collection = Mock()

        # Mock upsert
        client.upsert = Mock()

        # Mock search - return empty list by default
        client.search = Mock(return_value=[])

        # Mock delete
        client.delete = Mock()

        # Mock retrieve - return empty list by default
        client.retrieve = Mock(return_value=[])

        return client

    @pytest.fixture
    def qdrant_adapter(self, mock_qdrant_client, monkeypatch):
        """Create Qdrant adapter with mocked client."""
        from hansard_tales.vector_db.qdrant_adapter import QdrantAdapter

        # Mock QdrantClient constructor
        def mock_qdrant_init(host, port):
            return mock_qdrant_client

        monkeypatch.setattr("hansard_tales.vector_db.qdrant_adapter.QdrantClient", mock_qdrant_init)

        adapter = QdrantAdapter(host="localhost", port=6333)
        adapter.client = mock_qdrant_client
        return adapter

    def test_create_collection(self, qdrant_adapter, mock_qdrant_client):
        """Test creating a collection."""
        qdrant_adapter.create_collection("test_collection", dimension=384)

        # Verify recreate_collection was called
        mock_qdrant_client.recreate_collection.assert_called_once()
        call_args = mock_qdrant_client.recreate_collection.call_args
        assert call_args[1]["collection_name"] == "test_collection"

    def test_insert_vector(self, qdrant_adapter, mock_qdrant_client):
        """Test inserting a vector."""
        vector = [0.1] * 384
        payload = {"type": "statement", "chamber": "national_assembly"}
        text = "Test statement"

        qdrant_adapter.insert(
            collection="test_collection", id="doc_1", vector=vector, payload=payload, text=text
        )

        # Verify upsert was called
        mock_qdrant_client.upsert.assert_called_once()
        call_args = mock_qdrant_client.upsert.call_args
        assert call_args[1]["collection_name"] == "test_collection"

        # Verify text was added to payload
        points = call_args[1]["points"]
        assert len(points) == 1
        assert points[0].payload["text"] == text
        assert points[0].payload["type"] == "statement"

    def test_search_without_filter(self, qdrant_adapter, mock_qdrant_client):
        """Test searching without filters."""
        from qdrant_client.models import ScoredPoint

        # Mock search results
        mock_result = ScoredPoint(
            id="doc_1", score=0.95, payload={"text": "Test statement", "type": "statement"}
        )
        mock_qdrant_client.search.return_value = [mock_result]

        query_vector = [0.1] * 384
        results = qdrant_adapter.search(
            collection="test_collection", query_vector=query_vector, limit=10
        )

        # Verify search was called
        mock_qdrant_client.search.assert_called_once()
        call_args = mock_qdrant_client.search.call_args
        assert call_args[1]["collection_name"] == "test_collection"
        assert call_args[1]["limit"] == 10
        assert call_args[1]["query_filter"] is None

        # Verify results
        assert len(results) == 1
        assert results[0].id == "doc_1"
        assert results[0].score == 0.95
        assert results[0].text == "Test statement"

    def test_search_with_filter(self, qdrant_adapter, mock_qdrant_client):
        """Test searching with metadata filters."""
        from qdrant_client.models import ScoredPoint

        # Mock search results
        mock_result = ScoredPoint(
            id="doc_1",
            score=0.95,
            payload={"text": "Test statement", "chamber": "national_assembly"},
        )
        mock_qdrant_client.search.return_value = [mock_result]

        query_vector = [0.1] * 384
        results = qdrant_adapter.search(
            collection="test_collection",
            query_vector=query_vector,
            limit=10,
            filter={"chamber": "national_assembly"},
        )

        # Verify search was called with filter
        mock_qdrant_client.search.assert_called_once()
        call_args = mock_qdrant_client.search.call_args
        assert call_args[1]["query_filter"] is not None

        # Verify results
        assert len(results) == 1
        assert results[0].payload["chamber"] == "national_assembly"

    def test_search_multiple_filters(self, qdrant_adapter, mock_qdrant_client):
        """Test searching with multiple metadata filters."""
        from qdrant_client.models import ScoredPoint

        mock_result = ScoredPoint(
            id="doc_1",
            score=0.95,
            payload={"text": "Test", "chamber": "national_assembly", "type": "statement"},
        )
        mock_qdrant_client.search.return_value = [mock_result]

        query_vector = [0.1] * 384
        qdrant_adapter.search(
            collection="test_collection",
            query_vector=query_vector,
            limit=10,
            filter={"chamber": "national_assembly", "type": "statement"},
        )

        # Verify filter was created with multiple conditions
        mock_qdrant_client.search.assert_called_once()
        call_args = mock_qdrant_client.search.call_args
        assert call_args[1]["query_filter"] is not None

    def test_delete_vector(self, qdrant_adapter, mock_qdrant_client):
        """Test deleting a vector."""
        qdrant_adapter.delete("test_collection", "doc_1")

        # Verify delete was called
        mock_qdrant_client.delete.assert_called_once()
        call_args = mock_qdrant_client.delete.call_args
        assert call_args[1]["collection_name"] == "test_collection"
        assert call_args[1]["points_selector"] == ["doc_1"]

    def test_get_existing_vector(self, qdrant_adapter, mock_qdrant_client):
        """Test getting an existing vector."""
        from qdrant_client.models import Record

        # Mock retrieve result
        mock_record = Record(id="doc_1", payload={"text": "Test statement", "type": "statement"})
        mock_qdrant_client.retrieve.return_value = [mock_record]

        result = qdrant_adapter.get("test_collection", "doc_1")

        # Verify retrieve was called
        mock_qdrant_client.retrieve.assert_called_once()
        call_args = mock_qdrant_client.retrieve.call_args
        assert call_args[1]["collection_name"] == "test_collection"
        assert call_args[1]["ids"] == ["doc_1"]

        # Verify result
        assert result is not None
        assert result.id == "doc_1"
        assert result.text == "Test statement"
        assert result.score == 1.0

    def test_get_nonexistent_vector(self, qdrant_adapter, mock_qdrant_client):
        """Test getting a vector that doesn't exist."""
        # Mock empty retrieve result
        mock_qdrant_client.retrieve.return_value = []

        result = qdrant_adapter.get("test_collection", "nonexistent_id")

        # Verify result is None
        assert result is None

    def test_search_empty_results(self, qdrant_adapter, mock_qdrant_client):
        """Test search with no results."""
        # Mock empty search results
        mock_qdrant_client.search.return_value = []

        query_vector = [0.1] * 384
        results = qdrant_adapter.search(
            collection="test_collection", query_vector=query_vector, limit=10
        )

        # Verify empty results
        assert len(results) == 0

    def test_insert_with_empty_payload(self, qdrant_adapter, mock_qdrant_client):
        """Test inserting with empty payload."""
        vector = [0.1] * 384
        text = "Test statement"

        qdrant_adapter.insert(
            collection="test_collection", id="doc_1", vector=vector, payload={}, text=text
        )

        # Verify upsert was called
        mock_qdrant_client.upsert.assert_called_once()
        call_args = mock_qdrant_client.upsert.call_args
        points = call_args[1]["points"]

        # Verify text was added to payload
        assert points[0].payload["text"] == text


class TestVectorDBFactory:
    """Test suite for vector DB factory."""

    def test_create_chromadb(self):
        """Test creating ChromaDB adapter via factory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = VectorDBConfig(engine="chromadb", persist_directory=Path(tmpdir))

            vdb = create_vector_db(config)

            assert isinstance(vdb, ChromaDBAdapter)

    def test_create_qdrant(self):
        """Test creating Qdrant adapter via factory."""
        from unittest.mock import patch

        config = VectorDBConfig(engine="qdrant", qdrant_host="localhost", qdrant_port=6333)

        # Mock QdrantClient to avoid actual connection
        with patch("hansard_tales.vector_db.factory.QdrantAdapter") as mock_adapter:
            create_vector_db(config)

            # Verify QdrantAdapter was instantiated
            mock_adapter.assert_called_once_with(host="localhost", port=6333)

    def test_create_unknown_engine(self):
        """Test creating adapter with unknown engine."""
        from unittest.mock import Mock

        # Create a mock config that bypasses Pydantic validation
        config = Mock(spec=VectorDBConfig)
        config.engine = "unknown_engine"
        config.persist_directory = Path(".")

        with pytest.raises(ValueError, match="Unknown vector DB engine"):
            create_vector_db(config)
