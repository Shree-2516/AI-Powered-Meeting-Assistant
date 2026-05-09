from sentence_transformers import SentenceTransformer
from app.core.settings import settings
import numpy as np

_model = None

def get_model():
    """Lazy-load the embedding model."""
    global _model
    if _model is None:
        print(f"[EmbeddingService] Loading model: {settings.EMBEDDING_MODEL_NAME}...")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        print("[EmbeddingService] Model loaded successfully")
    return _model

def generate_embedding(text: str) -> list:
    """
    Generate a vector embedding for the given text.
    Returns a list of floats (vector).
    """
    if not text:
        return None
        
    model = get_model()
    # Ensure text is string and not too long (model usually truncates to 256/512 tokens anyway)
    embedding = model.encode(text)
    
    # Convert numpy array to list for SQLAlchemy/pgvector
    return embedding.tolist()

def similarity_search(query: str, top_k: int = 5):
    """
    This is just a helper for local testing if needed.
    Actual DB search uses pgvector SQL operators.
    """
    pass
