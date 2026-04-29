"""
Chunking semantico para documentos legales.
Divide por articulos/clausulas/secciones, no por tamano fijo.
"""

import re
from config import CHUNK_MAX_CHARS, CHUNK_OVERLAP, logger


def chunk_document(text: str, source_file: str) -> list[dict]:
    """
    Divide un texto legal en chunks semanticos.
    Cada chunk es un dict con: text, source, section, chunk_index.
    """
    if not text or len(text.strip()) < 50:
        return []

    chunks = []
    filename = source_file.split("\\")[-1] if "\\" in source_file else source_file

    # Intentar dividir por articulos/clausulas/secciones
    # Patron: "Articulo 42", "ARTICULO 15", "Clausula 3ra", "Seccion IV"
    pattern = r'(?=(?:Art[ií]culo|ART[IÍ]CULO|Cl[aá]usula|CLAUSULA|Secci[oó]n|SECCI[OÓ]N)\s+\w+)'
    sections = re.split(pattern, text, flags=re.IGNORECASE)

    # Si no encontro divisiones legales, dividir por parrafos dobles
    if len(sections) <= 1:
        sections = text.split("\n\n")

    chunk_idx = 0
    for sec in sections:
        sec = sec.strip()
        if len(sec) < 50:
            continue

        # Extraer nombre de la seccion (primeros 80 chars)
        section_name = sec.split("\n")[0][:80].strip()

        # Si la seccion es muy larga, subdividir
        if len(sec) > CHUNK_MAX_CHARS:
            sub_chunks = _split_long_section(sec, CHUNK_MAX_CHARS, CHUNK_OVERLAP)
            for sub in sub_chunks:
                chunks.append({
                    "text": sub.strip(),
                    "source": source_file,
                    "filename": filename,
                    "section": section_name,
                    "chunk_index": chunk_idx,
                })
                chunk_idx += 1
        else:
            chunks.append({
                "text": sec,
                "source": source_file,
                "filename": filename,
                "section": section_name,
                "chunk_index": chunk_idx,
            })
            chunk_idx += 1

    return chunks


def _split_long_section(text: str, max_chars: int, overlap: int) -> list[str]:
    """Divide una seccion larga en sub-chunks con solapamiento."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end])
        start += max_chars - overlap
    return chunks
