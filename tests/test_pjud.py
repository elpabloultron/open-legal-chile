"""
Pruebas de jurisprudencia judicial y Tribunal Constitucional (PJUD / CS / TC).
"""

from pjud_connector import PJUDClient
from mcp_server import handle_tool_call

def test_pjud_search_confianza_legitima():
    client = PJUDClient()
    res = client.search_jurisprudencia("confianza legitima")
    assert isinstance(res, list)
    assert len(res) > 0
    assert "Corte Suprema" in res[0]["tribunal"]
    assert "Rol N° 23.456-2022" in res[0]["rol"] or "confianza" in res[0]["doctrina"].lower()

def test_pjud_search_sala_laboral():
    client = PJUDClient()
    res = client.search_jurisprudencia("despido", sala="Cuarta")
    assert isinstance(res, list)
    assert len(res) > 0
    assert "Cuarta" in res[0]["sala"]

def test_pjud_search_tc():
    client = PJUDClient()
    res = client.search_jurisprudencia("inaplicabilidad")
    assert isinstance(res, list)
    assert len(res) > 0

def test_mcp_pjud_tool():
    res = handle_tool_call("pjud_search_jurisprudencia", {"query": "isapres"})
    assert isinstance(res, list)
    assert len(res) > 0
    assert "Isapres" in res[0]["caratula"] or "tabla" in res[0]["doctrina"].lower()


def test_mcp_pjud_analizar_sentencia_texto():
    texto_prueba = """
    Santiago, diez de marzo de dos mil veintiséis.
    VISTOS:
    Demanda de indemnización de perjuicios.
    CONSIDERANDO:
    1° Que el actor demanda daño moral derivado de accidente laboral.
    2° Que el artículo 184 del Código del Trabajo impone al empleador el deber de seguridad.
    SE RESUELVE:
    Se acoge la demanda condenando al pago de indemnización con costas.
    """
    res = handle_tool_call("pjud_analizar_sentencia", {
        "texto_sentencia": texto_prueba,
        "convertir_a_md_y_graficar": False
    })
    assert "total_considerandos" in res or "total_sentencias" in res
    if "total_considerandos" in res:
        assert res["total_considerandos"] == 2
        assert "CONDENA EN COSTAS" in res["regimen_costas"]


def test_mcp_pjud_analizar_sentencia_con_considerandos():
    texto_prueba = """
    Santiago, diez de marzo de dos mil veintiséis.
    VISTOS:
    Protección de derechos fundamentales.
    CONSIDERANDO:
    1° Que se reclama el cese de contrata.
    2° Que conforme a la confianza legítima, tras dos años se requiere acto motivado.
    3° Que la omisión de motivación vulnera la garantía de igualdad.
    SE RESUELVE:
    Se acoge el recurso.
    """
    res = handle_tool_call("pjud_analizar_sentencia", {
        "texto_sentencia": texto_prueba,
        "tema_relevante": "confianza legítima contrata motivación",
        "convertir_a_md_y_graficar": True
    })
    assert "citas_destacadas" in res
    assert len(res["citas_destacadas"]) >= 1
    cita = res["citas_destacadas"][0]
    assert cita["numero_considerando"] == "2°"
    assert "confianza legítima" in cita["extracto_literal"].lower()

