"""Abstract vector database interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class VectorSearchResult:
    """Result from vector search."""

    id: str
    score: float
    payload: dict[str, Any]
    text: str


class VectorDB(ABC):
    """Abstract vector database interface."""

    @abstractmethod
    def create_collection(self, name: str, dimension: int) -> None:
        """
        Create a new collection.

        Args:
            name: Collection name
            dimension: Vector dimension
        """
        pass

    @abstractmethod
    def insert(
        self, collection: str, id: str, vector: list[float], payload: dict[str, Any], text: str
    ) -> None:
        """
        Insert a vector with metadata.

        Args:
            collection: Collection name
            id: Document ID
            vector: Embedding vector
            payload: Metadata dictionary
            text: Original text
        """
        pass

    @abstractmethod
    def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 10,
        filter: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """
        Search for similar vectors.

        Args:
            collection: Collection name
            query_vector: Query embedding
            limit: Maximum number of results
            filter: Optional metadata filters

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    def delete(self, collection: str, id: str) -> None:
        """
        Delete a vector by ID.

        Args:
            collection: Collection name
            id: Document ID
        """
        pass

    @abstractmethod
    def get(self, collection: str, id: str) -> VectorSearchResult | None:
        """
        Get a vector by ID.

        Args:
            collection: Collection name
            id: Document ID

        Returns:
            Search result or None if not found
        """
        pass
