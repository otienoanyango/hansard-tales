"""Property-based tests for embedding generator."""

import pytest
from hypothesis import given, strategies as st
from hansard_tales.vector_db.embedding import EmbeddingGenerator
from hansard_tales.config.settings import EmbeddingConfig


@pytest.fixture(scope="module")
def generator():
    """Create embedding generator for property tests."""
    config = EmbeddingConfig(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        dimension=384,
        batch_size=32,
        device="cpu"
    )
    return EmbeddingGenerator(config)


@given(text=st.text(min_size=1, max_size=1000))
def test_embedding_consistency_property(generator, text):
    """
    Property: Same text must always generate same embedding.
    
    **Validates: Requirements 2.4**
    """
    embedding1 = generator.generate(text)
    embedding2 = generator.generate(text)
    
    assert embedding1 == embedding2


@given(text=st.text(min_size=1, max_size=1000))
def test_embedding_dimension_property(generator, text):
    """
    Property: All embeddings must have correct dimension.
    
    **Validates: Requirements 2.4**
    """
    embedding = generator.generate(text)
    
    assert len(embedding) == 384
    assert all(isinstance(x, float) for x in embedding)


@given(texts=st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=10))
def test_batch_consistency_property(generator, texts):
    """
    Property: Batch generation must match individual generation.
    
    **Validates: Requirements 2.4**
    """
    batch_embeddings = generator.generate_batch(texts)
    individual_embeddings = [generator.generate(text) for text in texts]
    
    assert len(batch_embeddings) == len(individual_embeddings)
    for batch_emb, ind_emb in zip(batch_embeddings, individual_embeddings):
        assert batch_emb == ind_emb


@given(
    text1=st.text(min_size=1, max_size=100),
    text2=st.text(min_size=1, max_size=100)
)
def test_similarity_symmetry_property(generator, text1, text2):
    """
    Property: Similarity must be symmetric.
    
    **Validates: Requirements 2.4**
    """
    emb1 = generator.generate(text1)
    emb2 = generator.generate(text2)
    
    sim1 = generator.similarity(emb1, emb2)
    sim2 = generator.similarity(emb2, emb1)
    
    assert abs(sim1 - sim2) < 1e-6


@given(text=st.text(min_size=1, max_size=100))
def test_self_similarity_property(generator, text):
    """
    Property: Text similarity with itself must be 1.0.
    
    **Validates: Requirements 2.4**
    """
    emb = generator.generate(text)
    similarity = generator.similarity(emb, emb)
    
    assert similarity > 0.99
    assert similarity <= 1.0


@given(
    text1=st.text(min_size=1, max_size=100),
    text2=st.text(min_size=1, max_size=100),
    text3=st.text(min_size=1, max_size=100)
)
def test_similarity_range_property(generator, text1, text2, text3):
    """
    Property: Similarity must be in range [0, 1].
    
    **Validates: Requirements 2.4**
    """
    emb1 = generator.generate(text1)
    emb2 = generator.generate(text2)
    emb3 = generator.generate(text3)
    
    sim12 = generator.similarity(emb1, emb2)
    sim23 = generator.similarity(emb2, emb3)
    sim13 = generator.similarity(emb1, emb3)
    
    assert 0.0 <= sim12 <= 1.0
    assert 0.0 <= sim23 <= 1.0
    assert 0.0 <= sim13 <= 1.0
