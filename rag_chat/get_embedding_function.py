import os
import numpy as np
from langchain_core.embeddings import Embeddings

class FakeEmbeddings(Embeddings):
    """Implementation of simple hash-based embeddings that work offline."""
    
    def __init__(self, size: int = 1536):
        """Initialize with embedding size."""
        self.size = size
    
    def _get_embedding_for_text(self, text: str) -> list[float]:
        """Convert text to a deterministic embedding vector."""
        # Use hash of text to seed random generator for deterministic output
        seed = hash(text) % 2**32
        np.random.seed(seed)
        return list(np.random.uniform(-1, 1, self.size))
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for documents."""
        return [self._get_embedding_for_text(text) for text in texts]
    
    def embed_query(self, text: str) -> list[float]:
        """Generate embeddings for query."""
        return self._get_embedding_for_text(text)


def get_embedding_function():
    """Return embedding function to use for vectorstore."""
    # Use FakeEmbeddings that work offline
    return FakeEmbeddings()
