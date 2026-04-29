"""
Indexacion en Qdrant (vectores) + SQLite FTS5 (keywords).
"""

import sqlite3
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from config import (
    QDRANT_DIR, SQLITE_PATH, QDRANT_COLLECTION,
    EMBEDDING_DIM, logger
)

_qdrant = None


def get_qdrant() -> QdrantClient:
    """Cliente Qdrant en modo archivo (sin servidor)."""
    global _qdrant
    if _qdrant is None:
        QDRANT_DIR.mkdir(parents=True, exist_ok=True)
        _qdrant = QdrantClient(path=str(QDRANT_DIR))
    return _qdrant


def get_sqlite() -> sqlite3.Connection:
    """Conexion SQLite (nueva cada vez, thread-safe)."""
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# ======================================================================
# Qdrant
# ======================================================================

def setup_qdrant(reset: bool = False):
    """Crea la coleccion en Qdrant si no existe."""
    client = get_qdrant()

    collections = [c.name for c in client.get_collections().collections]

    if QDRANT_COLLECTION in collections:
        if reset:
            client.delete_collection(QDRANT_COLLECTION)
            logger.info(f"Coleccion '{QDRANT_COLLECTION}' eliminada.")
        else:
            logger.info(f"Coleccion '{QDRANT_COLLECTION}' ya existe.")
            return

    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(
            size=EMBEDDING_DIM,
            distance=Distance.COSINE,
        ),
    )
    logger.info(f"Coleccion '{QDRANT_COLLECTION}' creada ({EMBEDDING_DIM}dim, cosine).")


def insert_to_qdrant(chunks: list[dict], embeddings) -> int:
    """Inserta chunks + embeddings en Qdrant. Retorna cantidad insertada."""
    if len(chunks) == 0:
        return 0

    client = get_qdrant()
    points = []

    for i, chunk in enumerate(chunks):
        doc_id = str(uuid.uuid4())[:8]
        points.append(PointStruct(
            id=doc_id,
            vector=embeddings[i].tolist(),
            payload={
                "text": chunk["text"],
                "source": chunk["source"],
                "filename": chunk["filename"],
                "section": chunk["section"],
                "chunk_index": chunk.get("chunk_index", 0),
            }
        ))

    client.upsert(collection_name=QDRANT_COLLECTION, points=points)
    return len(points)


def get_qdrant_count() -> int:
    """Cantidad de puntos en Qdrant."""
    client = get_qdrant()
    info = client.get_collection(QDRANT_COLLECTION)
    return info.points_count


# ======================================================================
# SQLite FTS5 (Keyword Search)
# ======================================================================

def setup_sqlite(reset: bool = False):
    """Crea la tabla FTS5 en SQLite si no existe."""
    conn = get_sqlite()
    if reset:
        conn.execute("DROP TABLE IF EXISTS documentos_fts")
        logger.info("Tabla FTS5 eliminada.")

    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS documentos_fts USING fts5(
            doc_id,
            filename,
            section,
            text,
            tokenize='unicode61 remove_diacritics 2'
        )
    """)
    conn.commit()
    conn.close()
    logger.info("SQLite FTS5 listo.")


def insert_to_sqlite(chunks: list[dict]):
    """Inserta chunks en SQLite FTS5."""
    if len(chunks) == 0:
        return

    conn = get_sqlite()
    for chunk in chunks:
        doc_id = str(uuid.uuid4())[:8]
        conn.execute(
            "INSERT INTO documentos_fts(doc_id, filename, section, text) VALUES (?, ?, ?, ?)",
            (doc_id, chunk["filename"], chunk["section"], chunk["text"])
        )
    conn.commit()
    conn.close()


def get_sqlite_count() -> int:
    """Cantidad de documentos en SQLite."""
    conn = get_sqlite()
    count = conn.execute("SELECT COUNT(*) FROM documentos_fts").fetchone()[0]
    conn.close()
    return count


# ======================================================================
# Indexed Files Tracking (para soportar --incremental)
# ======================================================================

def get_indexed_files() -> set:
    """Retorna set de paths de archivos ya indexados."""
    conn = get_sqlite()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS indexed_files (
            filepath TEXT PRIMARY KEY,
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    rows = conn.execute("SELECT filepath FROM indexed_files").fetchall()
    conn.close()
    return {r["filepath"] for r in rows}


def mark_file_indexed(filepath: str):
    """Marca un archivo como indexado."""
    conn = get_sqlite()
    conn.execute(
        "INSERT OR REPLACE INTO indexed_files(filepath) VALUES (?)",
        (filepath,)
    )
    conn.commit()
    conn.close()


def remove_file_from_index(filepath: str):
    """Elimina un archivo del indice (para archivos borrados del disco)."""
    conn = get_sqlite()
    conn.execute("DELETE FROM documentos_fts WHERE filename = ?", (filepath,))
    conn.execute("DELETE FROM indexed_files WHERE filepath = ?", (filepath,))
    conn.commit()
    conn.close()
