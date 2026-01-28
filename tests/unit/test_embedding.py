"""Unit tests for embedding generator."""

import pytest
from hansard_tales.vector_db.embedding import EmbeddingGenerator
from hansard_tales.config.settings import EmbeddingConfig


class TestEmbeddingGenerator:
    """Test suite for EmbeddingGenerator."""
    
    @pytest.fixture
    def generator(self):
        """Create embedding generator for testing."""
        config = EmbeddingConfig(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dimension=384,
            batch_size=32,
            device="cpu"
        )
        return EmbeddingGenerator(config)
    
    def test_generate_single_embedding(self, generator):
        """Test generating embedding for single text."""
        text = "This is a test statement from parliament."
        embedding = generator.generate(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
    
    def test_generate_batch_embeddings(self, generator):
        """Test generating embeddings for batch of texts."""
        texts = [
            "First parliamentary statement",
            "Second parliamentary statement",
            "Third parliamentary statement"
        ]
        embeddings = generator.generate_batch(texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)
    
    def test_embedding_consistency(self, generator):
        """Test that same text generates same embedding."""
        text = "Consistent text for testing"
        
        embedding1 = generator.generate(text)
        embedding2 = generator.generate(text)
        
        assert embedding1 == embedding2
    
    def test_similarity_identical_texts(self, generator):
        """Test similarity between identical texts."""
        text = "Test statement"
        
        emb1 = generator.generate(text)
        emb2 = generator.generate(text)
        
        similarity = generator.similarity(emb1, emb2)
        
        assert similarity > 0.99
        assert similarity <= 1.0
    
    def test_similarity_different_texts(self, generator):
        """Test similarity between different texts."""
        text1 = "Parliamentary debate on education"
        text2 = "Discussion about healthcare policy"
        
        emb1 = generator.generate(text1)
        emb2 = generator.generate(text2)
        
        similarity = generator.similarity(emb1, emb2)
        
        # Different texts should have lower similarity
        assert 0.0 <= similarity < 0.99
    
    def test_empty_text_handling(self, generator):
        """Test handling of empty text."""
        text = ""
        embedding = generator.generate(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
    
    def test_batch_empty_list(self, generator):
        """Test batch generation with empty list."""
        texts = []
        embeddings = generator.generate_batch(texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 0
