"""Qdrant adapter for production environment."""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from hansard_tales.vector_db.interface import VectorDB, VectorSearchResult


class QdrantAdapter(VectorDB):
    """Qdrant implementation (production)."""
    
    def __init__(self, host: str, port: int):
        """
        Initialize Qdrant adapter.
        
        Args:
            host: Qdrant server host
            port: Qdrant server port
        """
        self.client = QdrantClient(host=host, port=port)
        self.Distance = Distance
        self.VectorParams = VectorParams
    
    def create_collection(self, name: str, dimension: int) -> None:
        """
        Create a new collection.
        
        Args:
            name: Collection name
            dimension: Vector dimension
        """
        self.client.recreate_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=dimension,
                distance=Distance.COSINE
            )
        )
    
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
        payload['text'] = text
        self.client.upsert(
            collection_name=collection,
            points=[PointStruct(id=id, vector=vector, payload=payload)]
        )
    
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
        qdrant_filter = None
        if filter:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filter.items()
            ]
            qdrant_filter = Filter(must=conditions)
        
        results = self.client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=qdrant_filter
        )
        
        return [
            VectorSearchResult(
                id=str(result.id),
                score=result.score,
                payload=result.payload,
                text=result.payload.get('text', '')
            )
            for result in results
        ]
    
    def delete(self, collection: str, id: str) -> None:
        """
        Delete a vector by ID.
        
        Args:
            collection: Collection name
            id: Document ID
        """
        self.client.delete(
            collection_name=collection,
            points_selector=[id]
        )
    
    def get(self, collection: str, id: str) -> Optional[VectorSearchResult]:
        """
        Get a vector by ID.
        
        Args:
            collection: Collection name
            id: Document ID
            
        Returns:
            Search result or None if not found
        """
        results = self.client.retrieve(
            collection_name=collection,
            ids=[id]
        )
        if not results:
            return None
        result = results[0]
        return VectorSearchResult(
            id=str(result.id),
            score=1.0,
            payload=result.payload,
            text=result.payload.get('text', '')
        )
