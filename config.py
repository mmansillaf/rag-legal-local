"""
Configuracion central del sistema RAG Legal.
Todas las rutas, modelos y parametros en un solo lugar.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
QDRANT_DIR = DATA_DIR / "qdrant"
SQLITE_PATH = DATA_DIR / "documentos.db"
LOG_DIR = BASE_DIR / "logs"

# Crear directorios si no existen
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Carpeta de documentos a indexar (cambiar segun tu maquina)
DOCUMENTS_FOLDER = os.environ.get("RAG_DOCS_FOLDER", "")

# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024
EMBEDDING_BATCH_SIZE = 64  # cuantos chunks procesar a la vez

# ---------------------------------------------------------------------------
# Qdrant
# ---------------------------------------------------------------------------
QDRANT_COLLECTION = "documentos_legales"

# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
CHUNK_MAX_CHARS = 4000   # tamano maximo de cada chunk en caracteres
CHUNK_OVERLAP = 400       # solapamiento entre chunks consecutivos

# ---------------------------------------------------------------------------
# APIs Cloud
# ---------------------------------------------------------------------------
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------
TOP_K = 10                     # cuantos resultados devolver de cada store
CONFIDENCE_THRESHOLD = 0.75    # debajo de esto, activar web fallback
MAX_CONTEXT_CHARS = 8000       # maximo de caracteres a enviar al LLM

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "rag_legal.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("rag_legal")
