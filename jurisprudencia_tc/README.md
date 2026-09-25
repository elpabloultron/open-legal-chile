# Tribunal Constitucional de Chile — sentencias (últimos 2 años) en Markdown

Texto íntegro de las sentencias del Tribunal Constitucional descargadas desde su buscador
oficial (`buscador.tcchile.cl`), convertidas a Markdown.

- **Cobertura:** 966 sentencias · 2024-09-25 → 2026-03-26 (el TC publica con rezago).
- **Cada archivo:** `<rol>.md` con ficha de cita (rol, fecha, tipo de gestión, precepto legal,
  resultado) y el texto completo de la sentencia.
- **Índice:** `data/jurisprudencia/tc_textos.jsonl` (rol → archivo, caracteres y tokens).
- **Metadatos de la cosecha:** `data/jurisprudencia/tc_sentencias_2anios.jsonl`.
- **Reproducible:** `python scripts/tc_pdfs_a_md.py` (descarga el PDF oficial y extrae el texto).

**Cita:** `[Hugging Face - jurisprudencia_tc/<rol>.md]`
