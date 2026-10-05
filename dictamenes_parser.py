"""
Open Legal Chile — Analizador de Dictámenes Administrativos (dictamenes_parser.py)
Wrapper y alias de resoluciones_parser.py para compatibilidad directa.
"""

from resoluciones_parser import (
    ResolucionesParserEngine,
    DictamenesParserEngine
)

__all__ = [
    "ResolucionesParserEngine",
    "DictamenesParserEngine"
]
