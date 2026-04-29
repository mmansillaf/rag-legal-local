---
name: rag-legal
description: RAG sobre documentos legales locales (Qdrant + SQLite). Busca en 15k+ documentos y genera respuestas con fuentes citadas.
category: legal
---

# RAG Legal Local

Sistema de Retrieval-Augmented Generation sobre carpeta de documentos legales (Word + PDF).

## Trigger

Cuando el usuario pregunta sobre documentos legales indexados, busca terminos juridicos, necesita fuentes citadas, o pregunta sobre normativa, jurisprudencia, leyes, sentencias.

## Pipeline de Query

1. **Clasificar pregunta** → tipo A-H (ID, semantica, temporal, etc.)
2. **SQLite FTS5** → busqueda exacta de terminos legales
3. **Qdrant** → busqueda semantica (bge-m3 embeddings)
4. **Merge + dedup** → combinar y ordenar por relevance
5. **Confidence score** → si < 0.75, activar web fallback (Serper)
6. **LLM Cloud** → DeepSeek primario, Groq fallback
7. **Source citation** → [Fuente: archivo.docx, seccion]
8. **ResponseValidator** → chequeo anti-alucinaciones

## Comandos

```bash
# Consultar documentos legales
hermes ask "plazo de apelacion tributaria"
hermes ask "requisitos para recurso de reconsideracion"
hermes ask "sanciones por incumplimiento" --filter "ley_12345"
```

## Codigo

El sistema RAG esta en `rag-legal-local/`. Para indexar:

```bash
python ingestion_pipeline.py --input "C:/docs_legales" --incremental
```
