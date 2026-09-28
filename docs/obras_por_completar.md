# Obras del corpus: qué está completo y qué falta

Auditoría medida el **2026-09-27** (H6/H7 del plan de 1.8.0). Regla del proyecto: lo que
no se puede tener completo **se declara**; no se inventa el texto.

## 1 · Apuntes de Juan Andrés Orrego — reconciliado

- **Local:** 73 obras con texto íntegro en `doctrina/apuntes_orrego/` (17 MB).
- **Sitio:** `juanandresorrego.cl/apuntes_all.html` lista 73 PDF; los nombres coinciden 1:1
  con los locales tras normalizar puntuación (`LA RELACIÓN JURÍDICA, EL DEBER…` ↔
  `LA RELACIÓN JURÍDICA EL DEBER…`).
- **Faltantes: ninguno.** El listado del sitio no publica fechas de modificación, así que la
  frescura se verifica por contenido: si un apunte cambiara, se vuelve a bajar su PDF y se
  regenera el md. No hay apuntes «2025-2026» adicionales visibles hoy.

## 2 · Guías de la Academia Judicial — al día con el sitio

- **Local:** 24 guías con texto íntegro en `corpus_guias_aj/` (12 MB) + 108 archivos en
  `doctrina/academia_judicial/` (resúmenes ejecutivos y versiones de trabajo que apuntan a
  su guía completa).
- **Sitio:** 21 PDF en `guias.academiajudicial.cl` + 3 publicadas fuera del índice.
- **Bajadas en esta auditoría** (estaban en el sitio y no acá):

  | Guía | Publicada | Md |
  |---|---|---|
  | Guía de Ética 24 de septiembre de 2026 | 09/2026 | `Guia_Etica_24_sep_2026.md` (136.152 c.) |
  | Guía sobre inteligencia artificial para juezas y jueces | 09/2026 | `Guia_sobre_inteligencia_artificial_para_juezas_y_jueces.md` (97.060 c.) |
  | Buenas prácticas para la consejería técnica en tribunales de familia | 06/2026 | `Guia_buenas_practicas_consejeria_tecnica_familia_jun_2026.md` (359.671 c.) |

- Las dos versiones anteriores de Ética (7 y 10 de julio de 2026) **se conservan**: son
  versiones, no duplicados.
- Conversor reproducible: `scripts/guia_aj_a_md.py` (pdftotext; se niega si el PDF no rinde
  texto en vez de dejarlo vacío). PDF con descarga truncada detectado en la primera bajada
  (1.580.930 de 2.486.849 bytes): se rehizo y se verificó el tamaño exacto.

## 3 · Obras cortas (< 12 KB), una por una — ninguna truncada

59 archivos en `doctrina/`, en dos familias y por diseño:

1. **Resúmenes ejecutivos de la AJ** (15 con prefijo `aj_`, 2-3 KB): síntesis «token-optimized»;
   la guía completa vive en `corpus_guias_aj/` y se enlaza desde el resumen.
2. **Páginas canónicas de manuales** (44, 3-7 KB por capítulo: Bermúdez administrativo, Ramos
   Pazos, Barros Bourie, Gamonal…): «Base Doctrinal Canónica Exhaustiva», también por diseño.

Ninguna quedó cortada por una conversión: el candado de ambientales
(`tests/test_ambientales_a_md.py`) comprueba el último párrafo del original, y las guías
nuevas se convirtieron con el conversor de arriba (caracteres contados, no estimados).

## Pendiente declarado (no inventado)

- **Bermúdez, *Derecho Administrativo* íntegro:** en el corpus viven los 3 capítulos
  canónicos; el libro completo no tiene edición libre publicable → pendiente de licencia,
  no se rellena con texto de terceros.
- **Grafo de guías (`data/grafo_guias_aj.json`, `data/enlaces_guias_aj.json`):** fotografía
  al 27/09 **sin script generador en el repo**. Las 3 guías nuevas ya están en
  `data/enlaces_guias_corpus.json` (enlace por norma compartida) y sus bloques «Véase
  también» ya las conectan; el grafo de guías queda pendiente de reconstrucción con su
  extractor de normas.
- **Enlaces guías ↔ corpus (medido 2026-09-28):** 23 guías con lista de enlaces (134 en total;
  2-6 por guía, mediana 6) y bloques «Véase también» en 24/24 guías y 227/228 obras de
  `doctrina/`. Huecos declarados: en guías como `Guia_Audiencia_Juicio_Oral_Laboral.md` la sección
  «relacionadas» sale «(sin conexiones medidas todavía)» —el enlace por norma compartida no
  alcanzó— y hay títulos truncados en algunos listados (p. ej. «…Conciliación y»). Umbral
  propuesto para la próxima regeneración: **≥3 obras por guía**; el insumo que falta es el
  extractor de normas del grafo de guías (pendiente de arriba).
- **1TA · 111 sentencias ambientales:** el portal dejó de servir los PDF (301 → `sgc-web`,
  ya sólo HTML); quedan como ficha + enlace, declarado en `jurisprudencia_ambiental/README.md`.
- **Textos íntegros de la Corte Suprema (70.523):** el buscador del PJUD exige sesión;
  se publican como ficha Markdown + enlace oficial (declarado en `jurisprudencia_cs/README.md`).

## Comandos de la auditoría

```bash
curl -s https://www.juanandresorrego.cl/apuntes_all.html | grep -oE 'href="[^"]+"\.pdf' | sort -u | wc -l   # 73
ls doctrina/apuntes_orrego/*.md | wc -l                                                                     # 73
ls corpus_guias_aj/*.md | wc -l                                                                             # 24
find doctrina -name '*.md' -size -12k | wc -l                                                               # 59
python scripts/guia_aj_a_md.py --pdf guia.pdf --titulo "…" --area "…" --materia "…" --fuente "…"
python scripts/optimizar_catalogo_hf.py      # llms.txt y enlaces guías ↔ corpus
python scripts/enlazar_corpus.py             # bloques «Véase también» del canon
```
