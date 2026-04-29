# Interfaz Web para RAG Legal — Opciones y Estrategia

**Objetivo:** Que un abogado (sin conocimientos tecnicos) pueda buscar en sus 15k documentos legales desde una interfaz web amigable, sin usar la terminal.

---

## Opcion 1: Streamlit ⭐ Recomendado

**Que es:** Framework Python que convierte scripts en apps web. Ideal para dashboards y busquedas.

**Ventajas:**
- Solo Python (ya lo tenemos)
- ~100 lineas de codigo para la UI completa
- Se abre solo en el navegador
- Caja de busqueda, resultados, fuentes clickeables
- Subida de archivos (drag & drop)
- Barra lateral con filtros

**Contras:**
- Diseño funcional pero no "pixel-perfect"
- No es multi-usuario (single user, lo cual esta bien para local)

**Tiempo:** 2-3 horas

**Demo de como se veria:**

```
┌─────────────────────────────────────────────────────────┐
│  🔍 RAG Legal                                   [Ayuda] │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│  📁 Filtros  │  ┌────────────────────────────────────┐  │
│              │  │ 🔍 Escribe tu pregunta...     [Buscar] │
│  ☐ Leyes     │  └────────────────────────────────────┘  │
│  ☐ Sentencias│                                          │
│  ☐ Doctrina  │  📎 Respuesta                           │
│              │  ┌────────────────────────────────────┐  │
│  📅 Año      │  │ El plazo maximo de apelacion es    │  │
│  [2024  ▼]   │  │ de 30 dias habiles [Fuente:        │  │
│              │  │ ley_tributaria.docx, Art. 125].     │  │
│              │  │                                    │  │
│              │  │ Para recursos de reconsideracion   │  │
│              │  │ el plazo se reduce a 15 dias       │  │
│              │  │ [Fuente: codigo_fiscal.docx, Sec.   │  │
│              │  │ IV].                               │  │
│              │  └────────────────────────────────────┘  │
│              │                                          │
│              │  📄 Fuentes consultadas                  │
│              │  ┌────────────────────────────────────┐  │
│              │  │ 📄 ley_tributaria.docx              │  │
│              │  │    Articulo 125 — 94% relevancia   │  │
│              │  │    "El plazo maximo de apelacion.." │  │
│              │  ├────────────────────────────────────┤  │
│              │  │ 📄 codigo_fiscal.docx               │  │
│              │  │    Seccion IV — 89% relevancia     │  │
│              │  └────────────────────────────────────┘  │
│              │                                          │
│              │  ─────────────────────────────           │
│              │  📤 Subir documentos nuevos              │
│              │  [Arrastrar archivos aqui]               │
│              │  o click para seleccionar                │
│              │                                          │
└──────────────┴──────────────────────────────────────────┘
```

---

## Opcion 2: Open WebUI (ChatGPT-like)

**Que es:** Interfaz chat ya construida, estilo ChatGPT. Se conecta con Ollama.

**Ventajas:**
- Ya esta hecho (no hay que desarrollar)
- Interfaz pulida y profesional
- Multi-modelo, historial, prompts guardados
- ★134k estrellas en GitHub

**Contras:**
- Necesita Ollama corriendo (mas RAM)
- No esta integrado con nuestro RAG sin configuracion extra
- No muestra fuentes legales de forma nativa (hay que adaptarlo)
- La UI de chat no es ideal para busqueda legal (mejor busqueda + resultados)

**Tiempo:** 1-2 horas de configuracion, pero requiere adaptacion para fuentes

---

## Opcion 3: Integracion con Word (Hermes Add-in)

**Que es:** Usar el add-in de Word que ya construimos. El abogado busca desde Word.

**Ventajas:**
- El abogado YA esta en Word (su herramienta principal)
- Flujo natural: leer documento → preguntar → insertar respuesta
- No abre otra aplicacion
- Panel lateral discreto

**Contras:**
- Solo funciona con Word abierto
- Requiere el add-in instalado
- No es standalone para busquedas generales

**Tiempo:** 2-3 horas para conectar el add-in con el backend RAG

---

## Opcion 4: Flask + HTML/CSS (Control Total)

**Que es:** App web completa con backend Flask y frontend HTML personalizado.

**Ventajas:**
- Diseno 100% personalizado
- Puede verse exactamente como quieras
- Multi-usuario si se necesita

**Contras:**
- Mas codigo (~500 lineas)
- Mas tiempo (2-3 dias)
- Hay que diseñar el frontend

**Tiempo:** 2-3 dias

---

## Comparativa

| | Streamlit | Open WebUI | Word Add-in | Flask |
|---|:---:|:---:|:---:|:---:|
| **Tiempo desarrollo** | 2-3h | 1-2h config | 2-3h | 2-3d |
| **Facilidad usuario** | ★★★★★ | ★★★★☆ | ★★★★★ | ★★★★★ |
| **Busqueda + fuentes** | ✅ nativo | ❌ requiere adaptacion | ✅ | ✅ |
| **Subir docs** | ✅ drag-drop | ❌ | ❌ | ✅ |
| **Filtros** | ✅ facil | ❌ | ❌ | ✅ |
| **Instalacion** | 1 comando | compleja | media | 1 comando |
| **Mantenimiento** | Bajo | Medio | Bajo | Medio |

---

## Estrategia Recomendada: Streamlit + Word Add-in

```
┌─────────────────────────────────────────────────────────┐
│                                                          │
│  ABOGADO                                                 │
│                                                          │
│  ┌──────────────────────┐    ┌─────────────────────────┐ │
│  │  Streamlit Web UI    │    │  Word + Hermes Add-in   │ │
│  │  (busquedas generales)│    │  (trabajo con docs)     │ │
│  │                       │    │                         │ │
│  │  • Buscar en 15k docs │    │  • Leer doc activo      │ │
│  │  • Ver fuentes        │    │  • Preguntar sobre el   │ │
│  │  • Subir nuevos docs  │    │  • Insertar respuestas  │ │
│  │  • Filtrar por tipo   │    │  • Buscar jurisprudencia│ │
│  │                       │    │                         │ │
│  │  Abrir navegador      │    │  Ya esta en Word        │ │
│  │  http://localhost:8501│    │  Panel lateral          │ │
│  └──────────┬───────────┘    └───────────┬─────────────┘ │
│             │                             │               │
│             └──────────┬──────────────────┘               │
│                        ▼                                  │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  query_pipeline.py (mismo backend)                  │ │
│  │  Qdrant + SQLite + DeepSeek/Groq                    │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

Dos puntos de entrada, mismo backend:
1. **Streamlit** → para buscar "que dice la ley sobre X"
2. **Word Add-in** → para trabajar sobre un documento concreto

---

## Plan de Implementacion (Streamlit)

### Fase 1: UI Basica (2-3 horas)

```
app.py (~120 lineas)
├── Barra lateral: filtros, stats, subida de docs
├── Caja de busqueda principal
├── Area de respuesta con fuentes destacadas
├── Cards de fuentes (clickeables, expandibles)
└── Indicador de confianza
```

### Fase 2: Mejoras UX (1-2 horas)

```
├── Historial de busquedas (session_state)
├── Sugerencias de preguntas
├── "Copiar respuesta" button
├── Exportar a Word
├── Dark/light mode
└── Barra de progreso al indexar
```

### Fase 3: Integracion Word (2-3 horas)

```
├── Conectar add-in con backend RAG
├── Boton "Buscar en legislacion" en Word
├── Insertar fuentes como comentarios
└── Panel de resultados en task pane
```

---

## Ruta de Desarrollo (Priorizada)

```
AHORA → Streamlit UI (2-3h, maximo impacto)
  ↓
DESPUES → Si el abogado usa Word mucho: integrar add-in
  ↓
FUTURO → Si necesita multi-usuario: migrar a Flask
```

---

## Que Necesita el Abogado en Windows (con Streamlit)

```powershell
# 1. Instalar (una vez)
pip install streamlit

# 2. Ejecutar (cada vez que quiera usar el sistema)
streamlit run app.py

# 3. Se abre SOLO el navegador en http://localhost:8501
#    No toca la terminal nunca mas.
#    Puede crear un acceso directo en el Escritorio.
```

**Acceso directo en el Escritorio:**
```
Crear archivo "RAG Legal.bat" con:
  cd C:\Users\Abogado\rag-legal-local
  streamlit run app.py
```

Doble click → se abre el navegador con la interfaz.
