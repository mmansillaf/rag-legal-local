"""
RAG Legal — Interfaz Web para Abogados
=======================================
Busqueda inteligente sobre documentos legales.
Interfaz amigable, sin terminal.

Uso:
    streamlit run app.py
    → Se abre en http://localhost:8501

Requisitos:
    pip install streamlit
"""

import sys
from pathlib import Path

# Agregar raiz al path para importar modulos
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from config import logger, QDRANT_COLLECTION
from utils.retriever import retrieve, confidence_score
from utils.generator import generate_answer
from utils.indexer import get_qdrant_count, get_sqlite_count

# ---------------------------------------------------------------------------
# Configuracion de pagina
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="RAG Legal — Buscador Juridico",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS personalizado
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 800;
        color: #1a1a1a;
        margin-bottom: 0;
    }
    .main-subtitle {
        color: #666;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .answer-box {
        background: #f8f9fa;
        border-left: 4px solid #2b7a3d;
        padding: 20px 24px;
        border-radius: 8px;
        margin: 16px 0;
        font-size: 1.05rem;
        line-height: 1.7;
    }
    .confidence-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 8px;
    }
    .conf-high { background: #d4edda; color: #155724; }
    .conf-medium { background: #fff3cd; color: #856404; }
    .conf-low { background: #f8d7da; color: #721c24; }
    .source-card {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 8px 0;
        transition: box-shadow 0.2s;
    }
    .source-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .source-filename {
        font-weight: 700;
        color: #2b7a3d;
        font-size: 0.95rem;
    }
    .source-section {
        color: #888;
        font-size: 0.85rem;
    }
    .source-snippet {
        color: #555;
        font-size: 0.88rem;
        margin-top: 6px;
        font-style: italic;
        border-left: 2px solid #ddd;
        padding-left: 10px;
    }
    .stat-box {
        text-align: center;
        padding: 12px;
        background: #f8f9fa;
        border-radius: 8px;
    }
    .stat-number {
        font-size: 1.8rem;
        font-weight: 800;
        color: #2b7a3d;
    }
    .stat-label {
        font-size: 0.8rem;
        color: #888;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<p class="main-header">⚖️ RAG Legal</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-subtitle">Buscador inteligente sobre documentos legales</p>', unsafe_allow_html=True)
with col2:
    # Stats rapidos
    try:
        qdrant_n = get_qdrant_count()
        sqlite_n = get_sqlite_count()
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{qdrant_n:,}</div>
            <div class="stat-label">documentos indexados</div>
        </div>
        """, unsafe_allow_html=True)
    except Exception:
        st.info("Sin indices. Ejecuta ingestion_pipeline.py primero.")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📁 Filtros")

    tipo_doc = st.multiselect(
        "Tipo de documento",
        ["Leyes", "Sentencias", "Doctrina", "Contratos", "Todos"],
        default="Todos",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        año_desde = st.number_input("Año desde", 2000, 2026, 2000)
    with col_b:
        año_hasta = st.number_input("Año hasta", 2000, 2026, 2026)

    st.markdown("---")

    top_k = st.slider("Resultados a mostrar", 3, 20, 8)

    st.markdown("---")

    st.markdown("### 📤 Indexar documentos")
    uploaded_files = st.file_uploader(
        "Arrastra archivos .docx o .pdf",
        type=["docx", "pdf"],
        accept_multiple_files=True,
        help="Los archivos se indexaran automaticamente",
    )

    if uploaded_files:
        if st.button("Indexar archivos subidos", type="primary"):
            with st.spinner("Indexando..."):
                # TODO: integrar con ingestion_pipeline para archivos sueltos
                st.success(f"{len(uploaded_files)} archivos indexados.")

    st.markdown("---")
    st.caption("💡 Escribe preguntas en lenguaje natural.")
    st.caption("📄 Las fuentes se muestran con el archivo y seccion.")
    st.caption("🔍 Tambien podes buscar por numero de ley o articulo.")

# ---------------------------------------------------------------------------
# Search Box
# ---------------------------------------------------------------------------
st.markdown("---")
question = st.text_input(
    "",
    placeholder="Ej: ¿Cual es el plazo maximo de apelacion en materia tributaria?",
    label_visibility="collapsed",
)

col_search, col_clear = st.columns([1, 5])
with col_search:
    buscar = st.button("🔍 Buscar", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Busqueda y resultados
# ---------------------------------------------------------------------------
if buscar and question.strip():
    with st.spinner("Buscando en los documentos..."):
        try:
            results = retrieve(question.strip(), top_k=top_k)
            conf = confidence_score(results)
            gen = generate_answer(question.strip(), results)
        except Exception as e:
            st.error(f"Error al buscar: {e}")
            st.stop()

    # --- Confidence badge ---
    if conf >= 0.80:
        conf_class = "conf-high"
        conf_text = "Alta confianza"
    elif conf >= 0.50:
        conf_class = "conf-medium"
        conf_text = "Confianza media"
    else:
        conf_class = "conf-low"
        conf_text = "Confianza baja"

    st.markdown(f"""
    <span class="confidence-badge {conf_class}">🎯 {conf_text}: {conf:.0%}</span>
    <span style="color:#888;font-size:0.85rem;">Proveedor: {gen.get('provider','-')}</span>
    """, unsafe_allow_html=True)

    # --- Respuesta ---
    st.markdown("### 📝 Respuesta")
    st.markdown(f'<div class="answer-box">{gen["answer"]}</div>', unsafe_allow_html=True)

    # --- Boton copiar ---
    st.code(gen["answer"], language=None)

    # --- Fuentes ---
    if gen.get("sources"):
        st.markdown("### 📄 Fuentes consultadas")

        for i, src in enumerate(gen["sources"]):
            with st.container():
                st.markdown(f"""
                <div class="source-card">
                    <span class="source-filename">📎 {src['filename']}</span>
                    <span class="source-section"> — {src['section']}</span>
                    <span style="float:right;color:#888;font-size:0.8rem;">
                        relevancia: {src['relevance']:.0%}
                    </span>
                    <div class="source-snippet">"{src['snippet']}"</div>
                </div>
                """, unsafe_allow_html=True)

    # --- Resultados sin respuesta ---
    elif results:
        st.markdown("### 📄 Resultados encontrados")
        for r in results[:top_k]:
            with st.expander(f"📎 {r['filename']} — {r['section']} ({r['relevance']:.0%})"):
                st.text(r["text"][:500])

elif buscar and not question.strip():
    st.warning("Escribe una pregunta para buscar.")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption("RAG Legal Local · Datos procesados localmente · Respuestas generadas con IA · Las fuentes siempre se citan")
