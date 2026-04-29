"""
Generacion de embeddings usando bge-m3 (local, CPU).
"""

import numpy as np
from config import EMBEDDING_MODEL, EMBEDDING_DIM, EMBEDDING_BATCH_SIZE, logger

_encoder = None


def get_encoder():
    """Carga el modelo de embeddings (singleton, se cachea en memoria)."""
    global _encoder
    if _encoder is None:
        logger.info(f"Cargando modelo {EMBEDDING_MODEL}...")
        from sentence_transformers import SentenceTransformer
        _encoder = SentenceTransformer(EMBEDDING_MODEL)
        logger.info(f"Modelo cargado. Dimension: {EMBEDDING_DIM}")
    return _encoder


def embed_chunks(chunks: list[dict]) -> np.ndarray:
    """
    Genera embeddings para una lista de chunks.
    Retorna numpy array de shape (n_chunks, 1024).
    """
    encoder = get_encoder()
    texts = [c["text"] for c in chunks]

    embeddings = encoder.encode(
        texts,
        batch_size=EMBEDDING_BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,  # importante para cosine similarity
    )
    return embeddings


def embed_query(question: str) -> np.ndarray:
    """Genera embedding para una pregunta (vector unico)."""
    encoder = get_encoder()
    embedding = encoder.encode(
        [question],
        normalize_embeddings=True,
    )
    return embedding[0]
