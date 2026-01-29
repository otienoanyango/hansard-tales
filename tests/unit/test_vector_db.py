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


class TestVectorDBFactory:
    """Test suite for vector DB factory."""

    def test_create_chromadb(self):
        """Test creating ChromaDB adapter via factory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = VectorDBConfig(engine="chromadb", persist_directory=Path(tmpdir))

            vdb = create_vector_db(config)

            assert isinstance(vdb, ChromaDBAdapter)

    def test_create_unknown_engine(self):
        """Test creating adapter with unknown engine."""
        from unittest.mock import Mock

        # Create a mock config that bypasses Pydantic validation
        config = Mock(spec=VectorDBConfig)
        config.engine = "unknown_engine"
        config.persist_directory = Path(".")

        with pytest.raises(ValueError, match="Unknown vector DB engine"):
            create_vector_db(config)
