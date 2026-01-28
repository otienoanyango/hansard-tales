"""ChromaDB adapter for development environment."""

from typing import List, Dict, Any, Optional
import chromadb

from hansard_tales.vector_db.interface import VectorDB, VectorSearchResult


class ChromaDBAdapter(VectorDB):
    """ChromaDB implementation (development)."""
    
    def __init__(self, persist_directory: str):
        """
        Initialize ChromaDB adapter.
        
        Args:
            persist_directory: Directory for persistent storage
        """
        self.client = chromadb.PersistentClient(path=persist_directory)
    
    def create_collection(self, name: str, dimension: int) -> None:
        """
        Create a new collection.
        
        Args:
            name: Collection name
            dimension: Vector dimension
        """
        self.client.get_or_create_collection(
            name=name,
            metadata={"dimension": dimension}
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
        coll = self.client.get_collection(collection)
        # ChromaDB requires non-empty metadata dict
        # Add a default field if payload is empty
        metadata = payload if payload else {"_empty": True}
        coll.add(
            ids=[id],
            embeddings=[vector],
            metadatas=[metadata],
            documents=[text]
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
        coll = self.client.get_collection(collection)
        results = coll.query(
            query_embeddings=[query_vector],
            n_results=limit,
            where=filter
        )
        
        return [
            VectorSearchResult(
                id=results['ids'][0][i],
                score=results['distances'][0][i],
                payload=results['metadatas'][0][i],
                text=results['documents'][0][i]
            )
            for i in range(len(results['ids'][0]))
        ]
    
    def delete(self, collection: str, id: str) -> None:
        """
        Delete a vector by ID.
        
        Args:
            collection: Collection name
            id: Document ID
        """
        coll = self.client.get_collection(collection)
        coll.delete(ids=[id])
    
    def get(self, collection: str, id: str) -> Optional[VectorSearchResult]:
        """
        Get a vector by ID.
        
        Args:
            collection: Collection name
            id: Document ID
            
        Returns:
            Search result or None if not found
        """
        coll = self.client.get_collection(collection)
        result = coll.get(ids=[id])
        if not result['ids']:
            return None
        return VectorSearchResult(
            id=result['ids'][0],
            score=1.0,
            payload=result['metadatas'][0],
            text=result['documents'][0]
        )
