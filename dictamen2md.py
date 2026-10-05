"""
Open Legal Chile — Conversor de Dictámenes Administrativos a Markdown Canónico (dictamen2md)
Wrapper y alias de resolucion_administrativa2md.py para pronunciamientos de la Contraloría (CGR),
Dirección del Trabajo (DT) y otros órganos del Estado.
"""

from resolucion_administrativa2md import (
    segmentar_secciones_administrativas,
    generar_markdown_resolucion,
    convertir_dictamen_a_md,
    convertir_lote_dictamenes,
    parsear_frontmatter_dictamen_yaml,
    convertir_resolucion_a_md,
    convertir_lote_resoluciones,
)

__all__ = [
    "segmentar_secciones_administrativas",
    "generar_markdown_resolucion",
    "convertir_dictamen_a_md",
    "convertir_lote_dictamenes",
    "parsear_frontmatter_dictamen_yaml",
    "convertir_resolucion_a_md",
    "convertir_lote_resoluciones",
]
