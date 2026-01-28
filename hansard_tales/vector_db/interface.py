"""Abstract vector database interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class VectorSearchResult:
    """Result from vector search."""
    
    id: str
    score: float
    payload: Dict[str, Any]
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
        self,
        collection: str,
        id: str,
        vector: List[float],
        payload: Dict[str, Any],
        text: str
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
        query_vector: List[float],
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
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
    def get(self, collection: str, id: str) -> Optional[VectorSearchResult]:
        """
        Get a vector by ID.
        
        Args:
            collection: Collection name
            id: Document ID
            
        Returns:
            Search result or None if not found
        """
        pass
