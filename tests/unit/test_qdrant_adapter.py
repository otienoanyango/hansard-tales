"""Unit tests for Qdrant adapter."""

import sys
from unittest.mock import MagicMock, Mock

import pytest

# Mock both qdrant_client and chromadb before importing to avoid numpy issues
sys.modules["qdrant_client"] = MagicMock()
sys.modules["qdrant_client.models"] = MagicMock()
sys.modules["chromadb"] = MagicMock()
sys.modules["numpy"] = MagicMock()


class TestQdrantAdapter:
    """Test suite for Qdrant adapter."""

    @pytest.fixture
    def mock_qdrant_client(self):
        """Create mock Qdrant client."""
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
        # Mock the QdrantClient class
        monkeypatch.setattr("qdrant_client.QdrantClient", lambda host, port: mock_qdrant_client)

        from hansard_tales.vector_db.qdrant_adapter import QdrantAdapter

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
        # Mock search results
        mock_result = Mock()
        mock_result.id = "doc_1"
        mock_result.score = 0.95
        mock_result.payload = {"text": "Test statement", "type": "statement"}

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
        # Mock search results
        mock_result = Mock()
        mock_result.id = "doc_1"
        mock_result.score = 0.95
        mock_result.payload = {"text": "Test statement", "chamber": "national_assembly"}

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
        mock_result = Mock()
        mock_result.id = "doc_1"
        mock_result.score = 0.95
        mock_result.payload = {"text": "Test", "chamber": "national_assembly", "type": "statement"}

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
        # Mock retrieve result
        mock_record = Mock()
        mock_record.id = "doc_1"
        mock_record.payload = {"text": "Test statement", "type": "statement"}

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

    def test_search_with_limit(self, qdrant_adapter, mock_qdrant_client):
        """Test search with custom limit."""
        # Mock multiple results
        mock_results = []
        for i in range(5):
            mock_result = Mock()
            mock_result.id = f"doc_{i}"
            mock_result.score = 0.9 - i * 0.1
            mock_result.payload = {"text": f"Test {i}"}
            mock_results.append(mock_result)

        mock_qdrant_client.search.return_value = mock_results

        query_vector = [0.1] * 384
        results = qdrant_adapter.search(
            collection="test_collection", query_vector=query_vector, limit=5
        )

        # Verify limit was respected
        assert len(results) == 5

        # Verify results are ordered by score
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score
