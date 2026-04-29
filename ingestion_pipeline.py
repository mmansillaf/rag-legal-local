#!/usr/bin/env python3
"""
Ingestion Pipeline — Indexa documentos legales en Qdrant + SQLite.

Uso:
  python ingestion_pipeline.py --input "C:/docs_legales"
  python ingestion_pipeline.py --input "C:/docs_legales" --reset
  python ingestion_pipeline.py --input "C:/docs_legales" --incremental

Que hace:
  1. Escanea la carpeta en busca de .docx y .pdf
  2. Extrae texto de cada documento
  3. Divide en chunks semanticos (articulos, clausulas)
  4. Genera embeddings con bge-m3
  5. Inserta en Qdrant (vectores) + SQLite FTS5 (keywords)
  6. Muestra reporte final
"""

import sys
import argparse
import time
from pathlib import Path
from tqdm import tqdm

# Agregar el directorio raiz al path
sys.path.insert(0, str(Path(__file__).parent))

from config import logger, DOCUMENTS_FOLDER
from utils.extractor import extract_text, discover_files
from utils.chunker import chunk_document
from utils.embedder import embed_chunks, get_encoder
from utils.indexer import (
    setup_qdrant, setup_sqlite,
    insert_to_qdrant, insert_to_sqlite,
    get_qdrant_count, get_sqlite_count,
    get_indexed_files, mark_file_indexed,
)


def main():
    parser = argparse.ArgumentParser(description="Indexar documentos legales en RAG")
    parser.add_argument("--input", type=str, default=DOCUMENTS_FOLDER,
                        help="Carpeta con documentos .docx/.pdf")
    parser.add_argument("--reset", action="store_true",
                        help="Reiniciar indices desde cero")
    parser.add_argument("--incremental", action="store_true",
                        help="Solo indexar archivos nuevos o modificados")
    parser.add_argument("--batch-size", type=int, default=100,
                        help="Cuantos archivos procesar por lote de embeddings")
    args = parser.parse_args()

    if not args.input:
        logger.error("Especifica --input <carpeta> o configura RAG_DOCS_FOLDER")
        sys.exit(1)

    input_folder = Path(args.input)
    if not input_folder.exists():
        logger.error(f"Carpeta no encontrada: {input_folder}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("RAG LEGAL — Ingestion Pipeline")
    logger.info(f"Carpeta: {input_folder}")
    logger.info(f"Modo: {'RESET' if args.reset else 'INCREMENTAL' if args.incremental else 'COMPLETO'}")
    logger.info("=" * 60)

    t_start = time.time()

    # Inicializar DBs
    setup_qdrant(reset=args.reset)
    setup_sqlite(reset=args.reset)

    # Cargar modelo de embeddings una sola vez al inicio
    logger.info("Pre-cargando modelo de embeddings...")
    get_encoder()

    # ------------------------------------------------------------------
    # Descubrir archivos
    # ------------------------------------------------------------------
    all_files = discover_files(str(input_folder))
    if not all_files:
        logger.error(f"No se encontraron .docx/.pdf en {input_folder}")
        sys.exit(1)

    # Filtrar si es incremental
    if args.incremental and not args.reset:
        indexed = get_indexed_files()
        files_to_process = [f for f in all_files if str(f) not in indexed]
        logger.info(f"Modo incremental: {len(files_to_process)} nuevos de {len(all_files)} totales")
    else:
        files_to_process = all_files

    if not files_to_process:
        logger.info("Nada que indexar. Todos los archivos ya estan indexados.")
        _print_stats()
        return

    # ------------------------------------------------------------------
    # Procesar archivos en lotes
    # ------------------------------------------------------------------
    total_chunks = 0
    errors = []

    for batch_start in tqdm(range(0, len(files_to_process), args.batch_size),
                            desc="Procesando lotes", unit="lote"):
        batch_files = files_to_process[batch_start:batch_start + args.batch_size]
        batch_chunks = []

        # Extraer texto + chunking
        for file_path in batch_files:
            try:
                text = extract_text(str(file_path))
                if not text:
                    errors.append((file_path.name, "Texto vacio"))
                    continue

                chunks = chunk_document(text, str(file_path))
                batch_chunks.extend(chunks)

                # Marcar como indexado (incluso si no genera chunks)
                mark_file_indexed(str(file_path))

            except Exception as e:
                errors.append((file_path.name, str(e)))
                logger.warning(f"Error con {file_path.name}: {e}")

        if not batch_chunks:
            continue

        # Generar embeddings para todo el lote
        embeddings = embed_chunks(batch_chunks)

        # Insertar en Qdrant + SQLite
        n_qdrant = insert_to_qdrant(batch_chunks, embeddings)
        insert_to_sqlite(batch_chunks)

        total_chunks += len(batch_chunks)
        logger.debug(f"Lote: {len(batch_chunks)} chunks, {n_qdrant} en Qdrant")

    # ------------------------------------------------------------------
    # Reporte final
    # ------------------------------------------------------------------
    elapsed = time.time() - t_start
    logger.info("=" * 60)
    logger.info("INDEXACION COMPLETA")
    logger.info(f"Tiempo total: {elapsed/60:.1f} minutos")
    logger.info(f"Archivos procesados: {len(files_to_process)}")
    logger.info(f"Chunks generados: {total_chunks}")
    logger.info(f"Errores: {len(errors)}")
    _print_stats()

    if errors:
        logger.info("--- Errores ---")
        for fname, err in errors[:20]:
            logger.info(f"  {fname}: {err}")
        if len(errors) > 20:
            logger.info(f"  ... y {len(errors) - 20} mas")


def _print_stats():
    """Muestra estadisticas de los indices."""
    qdrant_count = get_qdrant_count()
    sqlite_count = get_sqlite_count()
    logger.info(f"Qdrant: {qdrant_count} vectores")
    logger.info(f"SQLite FTS5: {sqlite_count} documentos")


if __name__ == "__main__":
    main()
