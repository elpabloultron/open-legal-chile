# convertir_pdf

> 18 nodes · cohesion 0.13

## Key Concepts

- **convertir_pdf()** (7 connections) — `ingesta_fuentes.py`
- **convertir_todo()** (6 connections) — `ingesta_fuentes.py`
- **_a_markdown()** (5 connections) — `ingesta_fuentes.py`
- **inferir_materia()** (4 connections) — `ingesta_fuentes.py`
- **_texto_de_pdf()** (4 connections) — `ingesta_fuentes.py`
- **_concordancias()** (3 connections) — `ingesta_fuentes.py`
- **_es_titulo()** (3 connections) — `ingesta_fuentes.py`
- **_limpiar()** (3 connections) — `ingesta_fuentes.py`
- **Path** (3 connections)
- **Any** (2 connections)
- **_sin_acentos()** (2 connections) — `ingesta_fuentes.py`
- **Saca encabezados y pies repetidos, números de página sueltos y guiones de corte.** (1 connections) — `ingesta_fuentes.py`
- **Saca del texto las normas que cita, en forma compacta para la ficha del índice.** (1 connections) — `ingesta_fuentes.py`
- **Heurística de encabezado: mayúsculas, numeración, «CAPÍTULO», o línea corta sin…** (1 connections) — `ingesta_fuentes.py`
- **Arma secciones `##` con la ficha que el índice de doctrina sabe leer. El índice…** (1 connections) — `ingesta_fuentes.py`
- **Recorre las fuentes y escribe el corpus en Markdown. Devuelve el informe.** (1 connections) — `ingesta_fuentes.py`
- **Devuelve (área, materia). Si no hay señal suficiente, «General» — no se inventa.** (1 connections) — `ingesta_fuentes.py`
- **Devuelve (texto, cómo). Intenta pdftotext y, si no hay capa de texto, OCR.** (1 connections) — `ingesta_fuentes.py`

## Relationships

- [os](os.md) (9 shared connections)

## Source Files

- `ingesta_fuentes.py`

## Audit Trail

- EXTRACTED: 29 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*