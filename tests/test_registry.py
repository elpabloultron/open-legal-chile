"""
Pruebas para el módulo profundo de registro estatal y modelos de dominio.
"""

from domain.models import NormaBCN, DictamenCGR, DoctrinaDT, PresumaOJV, EscritoOJV
from connectors.registry import StateRegistry

def test_domain_models():
    norma = NormaBCN(tipo_norma="Ley", numero=21643, titulo="Ley Karin", articulo="2")
    assert norma.numero == 21643
    assert norma.articulo == "2"

    presuma = PresumaOJV(
        procedimiento="ORDINARIO",
        materia="RESOLUCION DE CONTRATO",
        demandante="TITULAR",
        rut_demandante="XX.XXX.XXX-X",
        abogado_patrocinante="ABOGADO",
        rut_abogado="XX.XXX.XXX-X",
        demandado="DEMANDADO",
        rut_demandado="76.XXX.XXX-X"
    )
    escrito = EscritoOJV(
        presuma=presuma,
        tribunal="S.J.L. EN LO CIVIL",
        comparecencia="COMPARECIENTE...",
        hechos="1. Hechos...",
        derecho="Art. 1545...",
        peticiones_concretas="POR TANTO..."
    )
    assert escrito.presuma.procedimiento == "ORDINARIO"
    assert escrito.tribunal == "S.J.L. EN LO CIVIL"

def test_state_registry_search_all():
    registry = StateRegistry()
    res = registry.search_all("Ley Karin")
    assert isinstance(res, dict)
    assert "query" in res
    assert "cgr" in res
    assert "dt" in res
