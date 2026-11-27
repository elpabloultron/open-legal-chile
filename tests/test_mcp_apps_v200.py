"""Pruebas offline de MCP Apps interactivas (SEP-1865 ui:// y structuredContent) v2.0.0."""

from __future__ import annotations

import json
import pathlib

import pytest

import mcp_apps_engine
import mcp_server

RAIZ = pathlib.Path(__file__).resolve().parent.parent
APP_NAMES = ("graphify", "calculadoras", "expediente")
APP_URIS = (
    mcp_apps_engine.URI_GRAPHIFY,
    mcp_apps_engine.URI_CALCULADORAS,
    mcp_apps_engine.URI_EXPEDIENTE,
)
APP_TOOLS = ("app_abrir_grafo", "app_abrir_calculadoras", "app_abrir_expediente")


@pytest.mark.parametrize("nombre", APP_NAMES)
def test_bundles_html_existen_y_cumplen_restricciones_seguridad(nombre: str) -> None:
    ruta = RAIZ / "mcp_apps" / f"{nombre}.html"
    assert ruta.is_file(), f"Falta HTML compilado de MCP App: {ruta}"
    crudo = ruta.read_bytes()
    assert 10_000 < len(crudo) <= mcp_apps_engine.MAX_BYTES_HTML
    texto = crudo.decode("utf-8")
    assert "Compuerta de Revisión Jurídica" in texto
    assert ".innerHTML" not in texto
    assert "callServerTool" in texto


def test_recursos_ui_disponibles_y_legibles() -> None:
    recursos = mcp_server._recursos_disponibles()
    assert len(recursos) == 6
    uris = {r["uri"]: r for r in recursos}
    for uri in APP_URIS:
        assert uri in uris
        assert uris[uri]["mimeType"] == mcp_apps_engine.MIME_MCP_APP
        assert uris[uri]["_meta"]["ui"]["prefersBorder"] is False
        contenido = mcp_server._leer_recurso(uri)
        assert contenido is not None
        assert contenido["mimeType"] == mcp_apps_engine.MIME_MCP_APP
        assert "<!DOCTYPE html>" in contenido["text"] or "<html" in contenido["text"]


def test_herramientas_exponen_meta_ui_y_entrypoints() -> None:
    por_nombre = {t["name"]: t for t in mcp_server.TOOLS}
    assert len(por_nombre) == 114
    for nombre in APP_TOOLS:
        tool = por_nombre[nombre]
        meta = tool.get("_meta") or {}
        assert meta["ui"]["resourceUri"].startswith("ui://open-legal-chile/")
        entrypoints = meta["com.google.antigravity/ui"]["entrypoints"]
        tipos = {e["type"] for e in entrypoints}
        assert tipos == {"aux_pane", "global"}

    for vinculada in (
        "graphify_consulta_subgrafo",
        "calcular_plazo_procesal",
        "calcular_finiquito_laboral",
        "calcular_cuantias_legales",
        "caso_analizar",
        "vigilante_analizar_resolucion",
    ):
        assert por_nombre[vinculada]["_meta"]["ui"]["resourceUri"].startswith("ui://open-legal-chile/")


@pytest.mark.parametrize(
    ("tool_name", "expected_key"),
    [
        ("app_abrir_grafo", "comunidades"),
        ("app_abrir_calculadoras", "calculadoras"),
        ("app_abrir_expediente", "guia_inicial"),
    ],
)
def test_invocacion_herramientas_app_y_structured_content(tool_name: str, expected_key: str) -> None:
    resp = mcp_server.procesar_mensaje(
        {
            "jsonrpc": "2.0",
            "id": 42,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": {}},
        },
        mcp_server.TOOLS,
    )
    assert resp is not None and "result" in resp
    result = resp["result"]
    assert result.get("isError", False) is False
    sc = result.get("structuredContent")
    assert isinstance(sc, dict) and expected_key in sc
    texto_json = json.loads(result["content"][0]["text"])
    assert texto_json == sc


def test_tools_call_normal_incluye_structured_content() -> None:
    resp = mcp_server.procesar_mensaje(
        {
            "jsonrpc": "2.0",
            "id": 99,
            "method": "tools/call",
            "params": {"name": "rut_validar_chile", "arguments": {"rut": "99.999.999-9"}},
        },
        mcp_server.TOOLS,
    )
    assert resp is not None
    result = resp["result"]
    assert result.get("isError", False) is False
    assert isinstance(result.get("structuredContent"), dict)
    assert result["structuredContent"]["valido"] is True


def test_app_abrir_grafo_y_expediente_con_parametros() -> None:
    resp_g = mcp_server.procesar_mensaje(
        {
            "jsonrpc": "2.0",
            "id": 100,
            "method": "tools/call",
            "params": {"name": "app_abrir_grafo", "arguments": {"query": "simulacion", "max_hops": 1}},
        },
        mcp_server.TOOLS,
    )
    assert resp_g is not None
    sc_g = resp_g["result"]["structuredContent"]
    assert isinstance(sc_g, dict) and (sc_g.get("encontrado") is True or "nodo" in sc_g or "mensaje" in sc_g)

    resp_e = mcp_server.procesar_mensaje(
        {
            "jsonrpc": "2.0",
            "id": 101,
            "method": "tools/call",
            "params": {"name": "app_abrir_expediente", "arguments": {"entrada": "Despido Art. 161 CT sin carta"}},
        },
        mcp_server.TOOLS,
    )
    assert resp_e is not None
    sc_e = resp_e["result"]["structuredContent"]
    assert isinstance(sc_e, dict) and sc_e.get("materia", "").lower() == "laboral"
