"""
Open Legal Chile — Modelos de Dominio Jurídico Tipados (Domain Models)
Estructuras de datos inmutables y tipadas con la biblioteca estándar de Python (dataclasses).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass(frozen=True)
class NormaBCN:
    """Representa una norma legal, código o ley de la República de Chile."""
    tipo_norma: str
    numero: Optional[int]
    titulo: str
    articulo: Optional[str] = None
    texto: str = ""
    fecha_version: str = ""
    es_vigente: bool = True

@dataclass(frozen=True)
class DictamenCGR:
    """Representa un dictamen vinculante de la Contraloría General de la República."""
    doc_id: str
    materia: str
    descriptor: str
    fecha: str
    link: str
    resumen: str = ""

@dataclass(frozen=True)
class DoctrinaDT:
    """Representa un pronunciamiento o dictamen de la Dirección del Trabajo."""
    id: str
    numero_dictamen: str
    titulo: str
    materias: str
    fecha: str
    texto_doctrina: str

@dataclass(frozen=True)
class DiscrepanciaPanel:
    """Representa una discrepancia resuelta por el Panel de Expertos Eléctrico."""
    id: int
    numero: str
    materia: str
    empresa: str
    fecha_dictamen: str
    resultado: str

@dataclass(frozen=True)
class SancionSMA:
    """Representa un procedimiento sancionatorio ambiental del SNIFA."""
    id: str
    expediente: str
    unidad_fiscalizable: str
    titular: str
    estado: str
    infracciones: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class SentenciaTDLC:
    """Representa una sentencia del Tribunal de Defensa de la Libre Competencia."""
    id: int
    titulo: str
    fecha: str
    link: str

@dataclass
class PresumaOJV:
    """Encabezado oficial OJV según Ley N° 20.886 y práctica forense."""
    procedimiento: str
    materia: str
    demandante: str
    rut_demandante: str
    abogado_patrocinante: str
    rut_abogado: str
    demandado: str
    rut_demandado: str

@dataclass
class EscritoOJV:
    """Estructura completa de un escrito judicial chileno para la OJV."""
    presuma: PresumaOJV
    tribunal: str
    comparecencia: str
    hechos: str
    derecho: str
    peticiones_concretas: str
    otrosies: List[Dict[str, str]] = field(default_factory=list)
