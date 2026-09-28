# Publicaciones de los Tribunales Ambientales en Markdown

Anuarios y boletines de jurisprudencia ambiental de los Tribunales Ambientales de Chile,
descargados de las páginas oficiales (2TA Santiago y 3TA Valdivia) y convertidos a Markdown.

- **Cobertura:** 55 publicaciones · 13 anuarios del 2TA (2013 y 2015–2025, con los dos tomos
  del 2018) · 5 anuarios del 3TA (2021–2025) · 37 boletines del 3TA (serie n23–n71).
- **Años verificados contra el documento**, no contra la carpeta de subida del sitio (el
  Anuario 2015 vive en `2014/09`, el de 2018 en `2019/06`…).
- **El Primer Tribunal Ambiental** no publica una serie de anuarios en su portal (verificado).
- **Cada archivo:** `<tribunal>_<tipo>_<número|año>.md` con ficha de cita y el texto íntegro.
- **Índice:** `data/jurisprudencia/publicaciones_textos.jsonl` (→ archivo, caracteres y tokens).
- **Metadatos de la cosecha:** `data/jurisprudencia/ambiental_boletines_anuarios.jsonl`.
- **Reproducible:** `python scripts/publicaciones_a_md.py`.

**Cita:** `[Hugging Face - publicaciones_ambientales/<archivo>.md]`
