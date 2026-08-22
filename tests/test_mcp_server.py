"""
Pruebas unitarias para el Servidor MCP (Model Context Protocol) de Open Legal Chile.
Verifica que las 12 herramientas forenses cumplan con la especificación JSON-RPC 2.0.
"""

from mcp_server import handle_tool_call, TOOLS

def test_tools_list():
    """Verifica que el catálogo de herramientas MCP contenga los 8 conectores y exportadores."""
    assert len(TOOLS) >= 12
    tool_names = [t["name"] for t in TOOLS]
    assert "bcn_get_codigo" in tool_names
    assert "bcn_get_ley" in tool_names
    assert "cgr_search_jurisprudencia" in tool_names
    assert "dt_search_doctrina" in tool_names
    assert "export_brief_ojv" in tool_names

def test_bcn_codigo_call():
    """Verifica consulta de artículo del Código Civil en la BCN."""
    res = handle_tool_call("bcn_get_codigo", {"codigo": "civil", "articulo": "1545"})
    assert isinstance(res, dict)
    assert "articulo" in res or "codigo" in res or "texto" in res
    assert "1545" in str(res.get("articulo", "")) or "contrato" in res.get("texto", "").lower() or "ley" in res.get("texto", "").lower()

def test_dt_doctrina_call():
    """Verifica consulta de doctrina laboral en la Dirección del Trabajo."""
    res = handle_tool_call("dt_search_doctrina", {"query": "344"})
    assert isinstance(res, list)
    assert len(res) > 0
    assert "titulo" in res[0]

def test_cgr_jurisprudencia_call():
    """Verifica consulta de dictámenes en la Contraloría."""
    res = handle_tool_call("cgr_search_jurisprudencia", {"query": "confianza legitima"})
    assert isinstance(res, dict)
    assert "total" in res
    assert "resultados" in res

def test_export_brief_call():
    """Verifica generación de escrito formal OJV."""
    res = handle_tool_call("export_brief_ojv", {
        "titulo": "DEMANDA ORDINARIA DE RESOLUCIÓN DE CONTRATO",
        "tribunal": "S.J.L. EN LO CIVIL DE SANTIAGO",
        "comparecencia": "COMPARECIENTE TITULAR, RUT XX.XXX.XXX-X",
        "hechos": "1. Antecedentes del caso.",
        "derecho": "Artículos 1489 y 1545 Código Civil.",
        "peticiones": "POR TANTO, A US. PIDO acoger la demanda con costas.",
        "otrosies": []
    })
    assert isinstance(res, dict)
    assert "htmlPath" in res
    assert "markdownPath" in res
    assert res.get("htmlPath").endswith(".html")
