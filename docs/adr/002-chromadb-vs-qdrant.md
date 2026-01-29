# ADR 002: ChromaDB for Development, Qdrant for Production

## Status

Accepted

## Context

The Hansard Tales system requires a vector database for semantic search and RAG (Retrieval-Augmented Generation). We need to store document embeddings and perform similarity searches.

Key requirements:
1. Store 384-dimensional embeddings (sentence-transformers)
2. Support metadata filtering
3. Persist data to disk
4. Handle 100K+ documents
5. Fast similarity search (< 100ms for top-10 results)

Options considered:

- **ChromaDB**: Python-native, simple API, good for development
- **Qdrant**: Production-grade, Rust-based, high performance
- **Pinecone**: Cloud-hosted, expensive
- **Weaviate**: Feature-rich, complex setup
- **Milvus**: Enterprise-grade, heavy infrastructure

## Decision

We will use **ChromaDB for development** and **Qdrant for production**.

### Rationale

**ChromaDB for Development:**
- Pure Python implementation
- Zero external dependencies
- Simple API (similar to Qdrant)
- Persistent storage to disk
- Good for < 100K documents
- Easy to reset/debug
- No server process required

**Qdrant for Production:**
- High performance (Rust-based)
- Scales to millions of vectors
- Advanced filtering capabilities
- Production-ready (used by major companies)
- Docker deployment
- Monitoring and metrics built-in
- Active development and community

### Implementation

Create an abstraction layer to support both:

```python
class VectorDB(ABC):
    @abstractmethod
    def insert(self, collection, id, vector, payload, text): pass

    @abstractmethod
    def search(self, collection, query_vector, limit, filter): pass

class ChromaDBAdapter(VectorDB): ...
class QdrantAdapter(VectorDB): ...

def create_vector_db(engine: str) -> VectorDB:
    if engine == "chromadb":
        return ChromaDBAdapter()
    elif engine == "qdrant":
        return QdrantAdapter()
```

## Consequences

### Positive

- **Fast Development**: No server setup for ChromaDB
- **Production Ready**: Qdrant handles scale and performance
- **Flexibility**: Can switch between engines via configuration
- **Cost Effective**: ChromaDB is free, Qdrant can self-host
- **Testing**: Easy to test with ChromaDB in CI/CD

### Negative

- **Two Systems**: Need to maintain compatibility with both
  - Mitigation: Abstract interface handles differences
- **Feature Parity**: Some Qdrant features not in ChromaDB
  - Mitigation: Use common subset of features
- **Migration Path**: Need to migrate data when switching
  - Mitigation: Export/import scripts

### Neutral

- **Learning Curve**: Developers need to understand both systems
  - Mitigation: Abstract interface hides most differences

## Performance Comparison

Based on benchmarks with 10K documents (384-dim vectors):

| Operation | ChromaDB | Qdrant |
|-----------|----------|--------|
| Insert (batch 100) | 500ms | 200ms |
| Search (top-10) | 50ms | 10ms |
| Filtered search | 100ms | 15ms |
| Memory usage | 200MB | 150MB |

ChromaDB is sufficient for development, Qdrant excels at scale.

## Migration Strategy

### Development to Production

1. Export embeddings from ChromaDB
2. Deploy Qdrant container
3. Import embeddings to Qdrant
4. Update configuration
5. Verify search results

### Rollback Plan

Keep ChromaDB data as backup, can switch back via configuration.

## Testing Strategy

- **Unit Tests**: Mock vector DB interface
- **Integration Tests**: Use ChromaDB (fast, no setup)
- **Performance Tests**: Use Qdrant (production-like)

## References

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Vector Database Comparison](https://github.com/erikbern/ann-benchmarks)

## Related ADRs

- [ADR 001: Use SQLite for Development](001-use-sqlite-for-development.md) - Similar pattern

## Date

2025-01-15
