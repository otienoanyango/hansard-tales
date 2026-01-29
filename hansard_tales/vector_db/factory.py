"""Factory function for creating vector database adapters."""

from hansard_tales.config.settings import VectorDBConfig
from hansard_tales.vector_db.chromadb_adapter import ChromaDBAdapter
from hansard_tales.vector_db.interface import VectorDB

# Qdrant is optional (production only)
try:
    from hansard_tales.vector_db.qdrant_adapter import QdrantAdapter

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False


def create_vector_db(config: VectorDBConfig) -> VectorDB:
    """
    Factory function to create vector DB adapter.

    Args:
        config: Vector database configuration

    Returns:
        VectorDB adapter instance

    Raises:
        ValueError: If unknown vector DB engine specified
        ImportError: If qdrant engine requested but qdrant-client not installed

    Example:
        >>> config = VectorDBConfig(engine="chromadb", persist_directory="data/vector_db")
        >>> vdb = create_vector_db(config)
        >>> vdb.create_collection("documents", dimension=384)
    """
    if config.engine == "chromadb":
        return ChromaDBAdapter(str(config.persist_directory))
    elif config.engine == "qdrant":
        if not QDRANT_AVAILABLE:
            raise ImportError(
                "Qdrant engine requested but qdrant-client is not installed. "
                "Install it with: pip install qdrant-client"
            )
        return QdrantAdapter(config.host, config.port)
    else:
        raise ValueError(f"Unknown vector DB engine: {config.engine}")
