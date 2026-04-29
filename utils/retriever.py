"""
Busqueda y recuperacion de chunks relevantes.
"""

from qdrant_client.models import Filter, FieldCondition, MatchValue
from config import (
    QDRANT_COLLECTION, TOP_K, CONFIDENCE_THRESHOLD, logger
)
from utils.embedder import embed_query
from utils.indexer import get_qdrant, get_sqlite


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    """
    Busca en Qdrant + SQLite y retorna resultados combinados.
    Cada resultado: {text, filename, section, source, relevance, score}
    """
    results = []

    # Buscar en Qdrant (semantico)
    qdrant_results = _search_qdrant(question, top_k)
    results.extend(qdrant_results)

    # Buscar en SQLite FTS5 (keywords exactas)
    sqlite_results = _search_sqlite(question, top_k)
    results.extend(sqlite_results)

    # Deducplicar por texto similar y ordenar por relevance
    results = _deduplicate(results)
    results.sort(key=lambda x: x.get("relevance", 0), reverse=True)

    return results[:top_k]


def _search_qdrant(question: str, top_k: int) -> list[dict]:
    """Busqueda semantica en Qdrant."""
    try:
        client = get_qdrant()
        vec = embed_query(question)

        hits = client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=vec.tolist(),
            limit=top_k,
        ).points

        results = []
        for hit in hits:
            results.append({
                "text": hit.payload.get("text", ""),
                "filename": hit.payload.get("filename", ""),
                "section": hit.payload.get("section", ""),
                "source": "qdrant",
                "relevance": round(hit.score, 4),
                "score": hit.score,
            })
        return results
    except Exception as e:
        logger.warning(f"Qdrant search error: {e}")
        return []


def _search_sqlite(question: str, top_k: int) -> list[dict]:
    """Busqueda exacta en SQLite FTS5."""
    try:
        conn = get_sqlite()
        # Construir query FTS5 con OR entre terminos
        terms = [t for t in question.split() if len(t) >= 3]
        if not terms:
            conn.close()
            return []

        fts_query = " OR ".join(terms)

        rows = conn.execute(
            "SELECT filename, section, text, rank as score "
            "FROM documentos_fts "
            "WHERE documentos_fts MATCH ? "
            "ORDER BY rank "
            "LIMIT ?",
            (fts_query, top_k)
        ).fetchall()
        conn.close()

        # Normalizar scores BM25 a 0-1
        results = []
        max_score = max((abs(r["score"]) for r in rows), default=1)
        for r in rows:
            results.append({
                "text": r["text"],
                "filename": r["filename"],
                "section": r["section"],
                "source": "sqlite",
                "relevance": round(abs(r["score"]) / max_score, 4),
                "score": r["score"],
            })
        return results
    except Exception as e:
        logger.warning(f"SQLite search error: {e}")
        return []


def _deduplicate(results: list[dict]) -> list[dict]:
    """Elimina duplicados por texto similar (primeros 100 chars)."""
    seen = set()
    unique = []
    for r in results:
        key = r["text"][:100].strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def confidence_score(results: list[dict]) -> float:
    """
    Calcula confidence score (0-1) basado en calidad de resultados.
    Si es < CONFIDENCE_THRESHOLD, conviene activar web fallback.
    """
    if not results:
        return 0.0

    qdrant_results = [r for r in results if r["source"] == "qdrant"]
    sqlite_results = [r for r in results if r["source"] == "sqlite"]

    # Calidad semantica (Qdrant) — mas peso
    if qdrant_results:
        max_q = max(r["relevance"] for r in qdrant_results)
        avg_q = sum(r["relevance"] for r in qdrant_results) / len(qdrant_results)
        semantic_quality = (max_q * 0.6 + avg_q * 0.4)
    else:
        semantic_quality = 0.0

    # Cantidad de resultados
    count_score = min(len(results) / 10.0, 1.0)

    # Boost si hay resultados en ambas fuentes
    cross_source_boost = 0.1 if qdrant_results and sqlite_results else 0.0

    return round(min(semantic_quality * 0.6 + count_score * 0.3 + cross_source_boost, 1.0), 4)
