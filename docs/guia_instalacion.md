# Guia de Instalacion — RAG Legal Local en Windows

**Paso a paso para tener un buscador inteligente sobre tus documentos legales.**

---

## ¿Necesito instalar Hermes Agent?

**NO.** El sistema funciona standalone con `query_pipeline.py`. Hermes Agent es OPCIONAL y aporta:

| Sin Hermes | Con Hermes Agent |
|------------|------------------|
| `python query_pipeline.py "pregunta"` | `hermes ask "pregunta"` |
| Busqueda en Qdrant + SQLite | Lo mismo + clasificacion de preguntas |
| DeepSeek/Groq para respuestas | Lo mismo + web fallback (Serper) |
| Sin memoria entre sesiones | Memoria persistente |
| Solo busqueda local | Busqueda local + internet |

**Recomendacion:** Empeza sin Hermes. Si necesitas web fallback o memoria, instalalo despues.

---

## Requisitos

| Requisito | Detalle |
|-----------|---------|
| Windows 10/11 | 64-bit |
| RAM | 8 GB minimo, 16 GB recomendado |
| Disco | 4 GB libres para indices (+ espacio de tus documentos) |
| Python | 3.10 o superior |
| API Keys | DeepSeek (gratis, pay-as-you-go) o Groq (free tier) |
| Internet | Solo para generar respuestas (la busqueda es local) |

---

## Paso 1: Instalar Python

1. Descargar de https://www.python.org/downloads/
2. Ejecutar el instalador
3. **IMPORTANTE:** Marcar "Add Python to PATH"
4. Click "Install Now"
5. Verificar en PowerShell:
   ```
   python --version
   ```

---

## Paso 2: Descargar el proyecto

```powershell
cd C:\Users\TU_USUARIO\
git clone https://github.com/mmansillaf/rag-legal-local.git
cd rag-legal-local
```

Si no tenes Git: https://git-scm.com/download/win

---

## Paso 3: Instalar dependencias

```powershell
pip install -r requirements.txt
```

Esto instala: `markitdown`, `sentence-transformers`, `qdrant-client`, `pymupdf`, `tqdm`.

La primera vez que corra, `sentence-transformers` va a descargar el modelo bge-m3 (~2 GB). Solo ocurre una vez.

---

## Paso 4: Configurar API Keys

Consegui tus API keys (gratis, solo pagas por uso):

- **DeepSeek:** https://platform.deepseek.com → recargar $2 (dura meses)
- **Groq:** https://console.groq.com → free tier

En PowerShell:

```powershell
# Opcion A: Variables de entorno (temporales, se pierden al cerrar)
$env:DEEPSEEK_API_KEY = "sk-tu-key"
$env:GROQ_API_KEY = "gsk_tu-key"

# Opcion B: Variables del sistema (permanentes)
# Win+R → sysdm.cpl → Avanzadas → Variables de entorno → Nueva
# Nombre: DEEPSEEK_API_KEY  Valor: sk-tu-key
# Nombre: GROQ_API_KEY      Valor: gsk_tu-key
```

---

## Paso 5: Indexar tus documentos

```powershell
python ingestion_pipeline.py --input "C:\Users\TU_USUARIO\Documentos\Legales"
```

**Que va a pasar:**
1. El script escanea la carpeta buscando .docx y .pdf
2. Extrae el texto de cada uno
3. Los divide en secciones legales (articulos, clausulas)
4. Genera embeddings (vectores) con bge-m3
5. Los guarda en Qdrant y SQLite

**Tiempo estimado:**
- 100 documentos → 2-5 minutos
- 1,000 documentos → 15-30 minutos
- 10,000 documentos → 1-2 horas

Es normal que tarde. Solo se hace UNA vez. Podes seguir usando la PC mientras tanto.

---

## Paso 6: Hacer tu primera consulta

```powershell
python query_pipeline.py "cual es el plazo de apelacion?"
```

**Respuesta esperada:**
```
📎 Confianza: 0.87 | Proveedor: deepseek

El plazo maximo de apelacion en materia tributaria es de 30 dias habiles
[Fuente: ley_tributaria.docx, Articulo 125].

────────────────────────────────────────
Fuentes:
  📄 ley_tributaria.docx — Articulo 125 (relevancia: 0.94)
  📄 codigo_fiscal.docx — Seccion IV (relevancia: 0.89)
```

---

## Uso Diario

### Agregar documentos nuevos

```powershell
python ingestion_pipeline.py --input "C:\Users\TU_USUARIO\Documentos\Legales" --incremental
```

Solo procesa los archivos nuevos. Tarda segundos.

### Modo interactivo (chat)

```powershell
python query_pipeline.py --interactive
```

Escribis preguntas y responde. Escribi `salir` para terminar.

### Modo JSON (para scripts)

```powershell
python query_pipeline.py "plazo de prescripcion" --json
```

---

## Solucion de Problemas

### "No module named 'markitdown'"

```powershell
pip install markitdown
```

### "No encontre documentos"

Verifica que la carpeta en `--input` existe y contiene .docx o .pdf.

### "Error: API key no configurada"

El sistema funciona SIN API keys (solo busqueda, sin respuestas generadas). Para respuestas con IA, configura `DEEPSEEK_API_KEY`.

### "ModuleNotFoundError: No module named 'utils'"

Ejecuta los scripts desde la carpeta `rag-legal-local`:
```powershell
cd C:\Users\TU_USUARIO\rag-legal-local
python ingestion_pipeline.py --input "..."
```

### La indexacion es muy lenta

Es normal para miles de documentos. Tips:
- Cerrá otras aplicaciones para liberar RAM
- Usa `--batch-size 50` para lotes mas chicos
- Si tenes SSD, asegurate de que los documentos esten ahi

---

## Proximos Pasos

1. **Integrar con Hermes Agent** para web fallback y memoria
2. **Open WebUI** para interfaz chat visual
3. **OCR** para PDFs escaneados
4. **Dashboard** con estadisticas de la coleccion
