#!/usr/bin/env python3
"""
Query Pipeline — Busca en los indices y genera respuestas con fuentes.

Uso:
  python query_pipeline.py "cual es el plazo de apelacion?"
  python query_pipeline.py --interactive
  python query_pipeline.py --web (con Streamlit)

Forma recomendada: usar Hermes Agent para queries (tiene mas features).
Este script es para testing rapido y uso standalone.
"""

import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import CONFIDENCE_THRESHOLD, DEEPSEEK_API_KEY, GROQ_API_KEY, logger
from utils.retriever import retrieve, confidence_score
from utils.generator import generate_answer


def query(question: str, top_k: int = 10) -> dict:
    """
    Pipeline completo de query:
    1. Buscar en Qdrant + SQLite
    2. Evaluar confidence
    3. Generar respuesta con fuentes
    """
    # Buscar
    results = retrieve(question, top_k=top_k)
    conf = confidence_score(results)

    logger.info(f"Query: '{question[:80]}...' → {len(results)} resultados, conf={conf}")

    # Si confidence baja y no hay API keys configuradas, advertir
    if conf < CONFIDENCE_THRESHOLD and not DEEPSEEK_API_KEY and not GROQ_API_KEY:
        return {
            "question": question,
            "answer": (
                f"Confidence baja ({conf:.2f}). No hay API keys configuradas para web fallback.\n"
                f"Resultados encontrados: {len(results)}\n"
                f"Configura DEEPSEEK_API_KEY o GROQ_API_KEY para mejores respuestas."
            ),
            "sources": _format_sources(results),
            "confidence": conf,
            "provider": "none",
        }

    # Generar respuesta
    gen = generate_answer(question, results)

    return {
        "question": question,
        "answer": gen["answer"],
        "sources": gen["sources"],
        "confidence": conf,
        "provider": gen["provider"],
    }


def _format_sources(results: list[dict]) -> list[dict]:
    """Formatea las fuentes para mostrarlas."""
    return [
        {
            "filename": r["filename"],
            "section": r["section"],
            "relevance": r["relevance"],
            "snippet": r["text"][:200] + "...",
        }
        for r in results[:5]
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Consultar RAG Legal")
    parser.add_argument("question", nargs="?", type=str, help="Pregunta a responder")
    parser.add_argument("--interactive", "-i", action="store_true", help="Modo interactivo")
    parser.add_argument("--top-k", type=int, default=10, help="Resultados a recuperar")
    parser.add_argument("--json", action="store_true", help="Salida en JSON")
    args = parser.parse_args()

    if args.interactive:
        _interactive_mode(args.top_k)
    elif args.question:
        result = query(args.question, top_k=args.top_k)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            _print_result(result)
    else:
        parser.print_help()


def _interactive_mode(top_k: int):
    """Modo interactivo: pregunta-respuesta en bucle."""
    print("\n" + "=" * 60)
    print("RAG LEGAL — Modo Interactivo")
    print("Escribe tu pregunta o 'salir' para terminar.")
    print("=" * 60 + "\n")

    while True:
        try:
            question = input("💬 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break

        if not question:
            continue
        if question.lower() in ("salir", "exit", "quit", "q"):
            break

        result = query(question, top_k=top_k)
        _print_result(result)


def _print_result(result: dict):
    """Imprime resultado en formato legible."""
    print(f"\n📎 Confianza: {result['confidence']:.2f} | Proveedor: {result['provider']}")
    print(f"\n{result['answer']}\n")

    if result.get("sources"):
        print("─" * 40)
        print("Fuentes:")
        for s in result["sources"]:
            print(f"  📄 {s['filename']} — {s['section']} (relevancia: {s['relevance']})")
        print()


if __name__ == "__main__":
    main()
