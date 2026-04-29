# RAG Legal Local

Sistema RAG (Retrieval-Augmented Generation) para buscar y consultar documentos legales (Word + PDF) localmente en Windows. Usa Qdrant + SQLite para busqueda, bge-m3 para embeddings, y DeepSeek/Groq APIs cloud para generar respuestas con fuentes citadas.

## Estructura

```
rag-legal-local/
├── config.py               ← Toda la configuracion en un solo lugar
├── ingestion_pipeline.py   ← Indexa documentos (corre 1 vez)
├── query_pipeline.py        ← Consulta documentos (uso diario)
├── requirements.txt         ← Dependencias Python
├── .env.example             ← Template de API keys
├── README.md                ← Este archivo
├── data/                    ← Indices (se crea solo)
│   ├── qdrant/              ← Vectores
│   └── documentos.db        ← SQLite FTS5
├── logs/                    ← Logs de ejecucion
└── utils/                   ← Modulos reutilizables
    ├── extractor.py         ← Extrae texto de .docx/.pdf
    ├── chunker.py           ← Divide en chunks legales
    ├── embedder.py          ← Genera embeddings (bge-m3)
    ├── indexer.py           ← Qdrant + SQLite
    ├── retriever.py         ← Busqueda combinada
    └── generator.py         ← LLM cloud (DeepSeek + Groq)
```

## Instalacion

```powershell
# 1. Clonar o copiar la carpeta
cd rag-legal-local

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar API keys
copy .env.example .env
# Editar .env con tus keys reales
```

## Uso

### Indexar documentos (una sola vez)

```powershell
# Primera vez: indexa toda la carpeta
python ingestion_pipeline.py --input "C:\Users\Usuario\Documentos\Legales"

# Despues: solo indexa archivos nuevos
python ingestion_pipeline.py --input "C:\Users\Usuario\Documentos\Legales" --incremental

# Reconstruir desde cero
python ingestion_pipeline.py --input "C:\Users\Usuario\Documentos\Legales" --reset
```

### Consultar documentos

```powershell
# Pregunta unica
python query_pipeline.py "cual es el plazo de apelacion?"

# Modo interactivo
python query_pipeline.py --interactive

# Salida JSON
python query_pipeline.py "plazo de prescripcion" --json
```

## Requisitos

- Python 3.10+
- 8GB RAM (recomendado 16GB)
- 3-4GB disco para indices
- API keys: DeepSeek (primario) o Groq (fallback)
- Sin GPU necesaria (embeddings en CPU)
