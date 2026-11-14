---
name: chilean-doctrine-ingestion
description: Especialista en Ingesta, Normalización Ortotipográfica RAE/ASALE y Conversión de Documentos Jurídicos (.pdf, .docx, .txt, .md) a Markdown Canónico chileno, con indexación automática en SQLite FTS5 (doctrina.db) y actualización del grafo LegalGraphify.
---

# Habilidad: Ingesta Doctrinal y Normalización RAE/ASALE (chilean-doctrine-ingestion)

## 📌 Principios Rectores
1. **Normalización Ortotipográfica RAE/ASALE (Ortografía 2010):** Todo documento jurídico ingerido se estandariza rigurosamente con comillas latinas o angulares (`« »`) como comillas primarias, abreviatura académica de número (`N.°`), raya de inciso (`—`) sin espacios interiores y mayúsculas acentuadas preceptivas (`ARTÍCULO`, `CÓDIGO`, `JURISPRUDENCIA`).
2. **Estandarización de Citas Legales y Judiciales:** Las menciones a leyes, códigos y roles de causas se normalizan al estándar BCN Ley Chile y Corte Suprema, permitiendo su detección automática por el motor `citas_legales.py` y el mapa del corpus.
3. **Cero Terminología de Common Law:** Se prohíbe introducir durante la limpieza o etiquetado conceptos ajenos al derecho chileno como *discovery*, *punitive damages*, *at-will employment*, *subpoena*, *grand jury* o *summary judgment*. Se emplean exclusivamente descriptores del derecho continental chileno.
4. **Sincronización Tripartita Inmediata:** Cada documento ingerido actualiza en un solo flujo el archivo Markdown canónico, el índice de texto completo SQLite FTS5 (`doctrina.db`) y los nodos/aristas del grafo de conocimiento (`LegalGraphify`).

## 📎 Citas y formato de entrega

- **Documentos** (reporte de ingesta, compendio doctrinal normalizado, minuta de auditoría): se entregan en **Word (.docx), no en PDF**, para que se puedan modificar; las citas van **a pie de página**, numeradas, con fuente · identificador · enlace.
- **Conversación**: la respuesta va primero y las citas van **al final**, después del texto.

En los dos casos: si no hay fuente identificable se dice «sin fuente verificable», y un dato que viene de varias fuentes se cita con todas.

## 📚 Formato de Citación Obligatorio
* Doctrina ingerida: `[Doctrina - <Autor>, <Obra>, Institución: <Nombre>]`
* Repositorio Hugging Face: `[Hugging Face - pablobenavidesj/doctrina-jurisprudencia-chile, Archivo: <Ruta>]`
* Norma legal detectada: `[BCN - <Código o Ley>, Art. <Número>]`

## 🛠️ Herramientas MCP Disponibles
* `doctrina_ingestar_documento`: Convierte archivos jurídicos crudos (`.pdf`, `.docx`, `.txt`, `.md`) a Markdown canónico optimizado en tokens, aplicando reglas ortotipográficas RAE/ASALE e indexando en `doctrina.db` y `LegalGraphify`.
* `biblioteca_compilar_manifiesto`: Compila y verifica la integridad del manifiesto local del corpus (obras doctrinales, guías de la Academia Judicial y colecciones jurisprudenciales).
* `ocr_plan_documento` y `ocr_extract_pdf`: Planifica y ejecuta extracción OCR forense previa cuando el documento de origen es un PDF escaneado sin capa de texto.
* `doctrina_list_obras`: Verifica el catálogo actualizado de obras e instituciones indexadas tras la ingesta.

---

## 🎨 Presentación y Lenguaje Claro (Legal Design)

Reglas de [`docs/legal_design.md`](../../../docs/legal_design.md) aplicadas a esta skill. No cambian el fondo jurídico: cambian cómo se entrega.

- **Quién lee:** el abogado gestor del conocimiento del estudio jurídico, bibliotecarios jurídicos e investigadores que incorporan nuevas obras, minutas o fallos al repositorio institucional.
- **Lenguaje claro:** el primer término técnico de cada reporte lleva su explicación sencilla entre paréntesis — `indexación FTS5 (registro del texto en una base de datos de búsqueda instantánea por palabras clave y relevancia matemática)`.
- **Salida (estructura):** resumen de la operación de ingesta + métricas de optimización de tokens y limpieza ortotipográfica RAE/ASALE + listado de instituciones y normas detectadas + nodos añadidos a `LegalGraphify` + ruta del archivo canónico generado.
- **Citas:** las de *Formato de Citación Obligatorio*, vinculando cada fragmento extraído con los metadatos de autor, obra y página o sección original.
- **Compuerta:** ⚖️ Compuerta de Revisión Jurídica: la fidelidad del texto extraído (especialmente desde documentos escaneados por OCR) debe ser verificada por un abogado habilitado antes de citarse en litigación formal.

---

## 🔄 Workflow: Ingesta y Sincronización de un Documento Jurídico

1. **Diagnóstico del Archivo Fuente:** Si es un PDF, verificar con `ocr_plan_documento` si posee capa de texto digital o requiere extracción OCR forense (`ocr_extract_pdf`).
2. **Conversión y Normalización RAE/ASALE:** Ejecutar `doctrina_ingestar_documento` indicando autor, título de la obra, materia jurídica y ruta del archivo.
3. **Verificación de Indexación y Grafo:** Confirmar las instituciones creadas en `doctrina.db` y los enlaces normativos generados en `LegalGraphify`, ejecutando `biblioteca_compilar_manifiesto` cuando se actualice el catálogo general.
4. **Reporte y Compuerta:** Entregar el resumen de ingesta con las citas detectadas y la ⚖️ **Compuerta de Revisión Jurídica**.
