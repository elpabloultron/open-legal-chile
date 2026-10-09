"""Mapa del corpus de Hugging Face: índice de todo el dataset + capa conectora de LegalGraphify.

El dataset `pablobenavidesj/doctrina-jurisprudencia-chile` tiene ~80 mil archivos (fichas de la
Corte Suprema, sentencias del TC y ambientales, doctrina y revistas). El mapa los inventaría a
todos con IDs canónicos, sus citas a normas y roles, y las entidades que los conectan (normas,
autores, revistas, ministros, salas, tribunales). Vive en el propio dataset (`data/mapa/`), se
actualiza de forma incremental cuando HF cambia, y el repositorio solo guarda un puntero
(`mapa_corpus/puntero.json`) a la revisión publicada.
"""

REPO_ID = "pablobenavidesj/doctrina-jurisprudencia-chile"
RUTA_HF = "data/mapa"
ESQUEMA = 1
