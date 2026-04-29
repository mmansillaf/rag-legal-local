"""
Generacion de respuestas con LLM cloud (DeepSeek + Groq fallback).
"""

import json
import urllib.request
from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL,
    MAX_CONTEXT_CHARS, logger
)

SYSTEM_PROMPT = """Eres un asistente legal. Responde UNICAMENTE basandote en los
documentos proporcionados abajo. Para cada afirmacion, cita la fuente
usando exactamente este formato: [Fuente: nombre_archivo, seccion].

Ejemplo correcto:
"El plazo es de 30 dias [Fuente: ley_12345.docx, Articulo 15]."

Reglas:
1. NUNCA inventes informacion.
2. Si la respuesta no esta en los documentos, di claramente:
   "No encontre informacion sobre este tema en los documentos proporcionados."
3. Cita TODAS las fuentes usadas.
4. Responde en espanol.
5. Se conciso pero completo."""


def generate_answer(question: str, results: list[dict]) -> dict:
    """
    Genera respuesta usando DeepSeek (primario) o Groq (fallback).
    Retorna dict con answer, sources, provider.
    """
    if not results:
        return {
            "answer": "No encontre documentos relevantes para responder esta pregunta.",
            "sources": [],
            "provider": "none",
        }

    # Construir contexto con fuentes
    context_parts = []
    for i, r in enumerate(results[:8]):
        label = f"[DOC_{i+1}]"
        context_parts.append(
            f"{label} Fuente: {r['filename']}, {r['section']}\n"
            f"Contenido: {r['text'][:600]}"
        )

    context = "\n\n---\n\n".join(context_parts)

    # Truncar si excede el limite
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n\n[... contexto truncado ...]"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"DOCUMENTOS:\n\n{context}\n\nPREGUNTA: {question}"},
    ]

    # Intentar DeepSeek primero
    answer = _call_deepseek(messages)
    provider = "deepseek"

    # Fallback a Groq si DeepSeek fallo
    if not answer:
        logger.info("DeepSeek fallo, intentando Groq...")
        answer = _call_groq(messages)
        provider = "groq"

    if not answer:
        return {
            "answer": "Error: No se pudo generar respuesta. Verifica las API keys.",
            "sources": [],
            "provider": "error",
        }

    # Extraer fuentes usadas
    sources = [
        {
            "filename": r["filename"],
            "section": r["section"],
            "relevance": r["relevance"],
            "snippet": r["text"][:200] + "...",
        }
        for r in results[:5]
    ]

    return {
        "answer": answer,
        "sources": sources,
        "provider": provider,
    }


def _call_deepseek(messages: list[dict]) -> str:
    """Llama a DeepSeek API. Retorna string o "" si falla."""
    if not DEEPSEEK_API_KEY:
        return ""

    try:
        data = json.dumps({
            "model": DEEPSEEK_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1500,
        }).encode()

        req = urllib.request.Request(
            DEEPSEEK_BASE_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            }
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"].strip()

    except Exception as e:
        logger.warning(f"DeepSeek error: {e}")
        return ""


def _call_groq(messages: list[dict]) -> str:
    """Llama a Groq API (fallback rapido). Retorna string o "" si falla."""
    if not GROQ_API_KEY:
        return ""

    try:
        import requests

        resp = requests.post(
            GROQ_BASE_URL,
            json={
                "model": GROQ_MODEL,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1500,
            },
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    except Exception as e:
        logger.warning(f"Groq error: {e}")
        return ""
