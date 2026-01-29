"""Embedding generator using sentence-transformers."""

import numpy as np
from sentence_transformers import SentenceTransformer

from hansard_tales.config.settings import EmbeddingConfig


class EmbeddingGenerator:
    """Generate embeddings using sentence-transformers."""

    def __init__(self, config: EmbeddingConfig):
        """
        Initialize embedding generator.

        Args:
            config: Embedding configuration
        """
        self.model = SentenceTransformer(config.model_name, device=config.device)
        self.dimension = config.dimension
        self.batch_size = config.batch_size

    def generate(self, text: str) -> list[float]:
        """
        Generate embedding for single text.

        Args:
            text: Input text

        Returns:
            Embedding vector as list of floats

        Example:
            >>> generator = EmbeddingGenerator(EmbeddingConfig())
            >>> embedding = generator.generate("This is a test")
            >>> len(embedding)
            384
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for batch of texts.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors

        Example:
            >>> generator = EmbeddingGenerator(EmbeddingConfig())
            >>> texts = ["First text", "Second text"]
            >>> embeddings = generator.generate_batch(texts)
            >>> len(embeddings)
            2
        """
        embeddings = self.model.encode(
            texts, batch_size=self.batch_size, convert_to_numpy=True, show_progress_bar=True
        )
        return embeddings.tolist()

    def similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0 to 1)

        Example:
            >>> generator = EmbeddingGenerator(EmbeddingConfig())
            >>> emb1 = generator.generate("Hello world")
            >>> emb2 = generator.generate("Hello world")
            >>> similarity = generator.similarity(emb1, emb2)
            >>> similarity > 0.99
            True
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
