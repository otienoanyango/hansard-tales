"""Vector database integration for semantic search."""

from hansard_tales.vector_db.interface import VectorDB, VectorSearchResult
from hansard_tales.vector_db.chromadb_adapter import ChromaDBAdapter
from hansard_tales.vector_db.factory import create_vector_db
from hansard_tales.vector_db.embedding import EmbeddingGenerator

# Qdrant is optional (production only)
try:
    from hansard_tales.vector_db.qdrant_adapter import QdrantAdapter
    __all__ = [
        "VectorDB",
        "VectorSearchResult",
        "ChromaDBAdapter",
        "QdrantAdapter",
        "create_vector_db",
        "EmbeddingGenerator",
    ]
except ImportError:
    __all__ = [
        "VectorDB",
        "VectorSearchResult",
        "ChromaDBAdapter",
        "create_vector_db",
        "EmbeddingGenerator",
    ]
