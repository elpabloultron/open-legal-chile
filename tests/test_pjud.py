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
