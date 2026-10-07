"""Casos borde del protocolo MCP (JSON-RPC 2.0 sobre stdio) que rompían a algunos harness.

- JSON inválido como primera línea mataba el servidor (UnboundLocalError en el manejador de error)
  y, en líneas posteriores, se contestaba con el id de la petición anterior.
- Una versión de protocolo desconocida se negociaba a la más antigua, no a la más nueva.
- Los lotes JSON-RPC (arrays) se descartaban en silencio: el cliente quedaba esperando.
- `initialize` no enviaba `instructions`, el canal estándar del protocolo de citación.
"""

import json
import os
import subprocess
import sys
import pathlib

import mcp_server
from mcp_server import INSTRUCCIONES, VERSIONES_PROTOCOLO, TOOLS, atender_linea, procesar_mensaje

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def _linea(**mensaje) -> str:
    return json.dumps({"jsonrpc": "2.0", **mensaje})


def test_json_invalido_responde_parse_error_con_id_null():
    respuesta = atender_linea("{esto no es json", TOOLS)
    assert respuesta["id"] is None
    assert respuesta["error"]["code"] == -32700


def test_mensaje_que_no_es_objeto_es_peticion_invalida():
    respuesta = atender_linea("42", TOOLS)
    assert respuesta["error"]["code"] == -32600


def test_notificacion_no_recibe_respuesta():
    assert atender_linea(_linea(method="notifications/initialized"), TOOLS) is None
    assert atender_linea(_linea(method="notifications/cancelled", params={"requestId": 3}), TOOLS) is None


def test_version_conocida_se_respeta_y_desconocida_va_a_la_mas_nueva():
    for version in VERSIONES_PROTOCOLO:
        r = procesar_mensaje({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                              "params": {"protocolVersion": version, "capabilities": {}}}, TOOLS)
        assert r["result"]["protocolVersion"] == version
    r = procesar_mensaje({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                          "params": {"protocolVersion": "2099-01-01", "capabilities": {}}}, TOOLS)
    assert r["result"]["protocolVersion"] == VERSIONES_PROTOCOLO[0]
    assert "2025-03-26" in VERSIONES_PROTOCOLO


def test_initialize_envia_instrucciones_con_el_protocolo():
    r = procesar_mensaje({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}, TOOLS)
    instrucciones = r["result"]["instructions"]
    assert instrucciones == INSTRUCCIONES
    assert "consulta_maestra" in instrucciones and "cita_texto" in instrucciones
    # Algunos clientes recortan instrucciones largas: se mantienen breves.
    assert len(instrucciones) < 2000


def test_lote_jsonrpc_se_contesta_entero():
    lote = json.dumps([
        {"jsonrpc": "2.0", "id": 1, "method": "ping"},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "metodo/inexistente"},
    ])
    respuestas = atender_linea(lote, TOOLS)
    assert [r["id"] for r in respuestas] == [1, 2]
    assert respuestas[0]["result"] == {}
    assert respuestas[1]["error"]["code"] == -32601
    assert atender_linea("[]", TOOLS)["error"]["code"] == -32600


def test_params_que_no_son_objeto_dan_error_con_su_id():
    r = procesar_mensaje({"jsonrpc": "2.0", "id": 7, "method": "tools/list", "params": [1, 2]}, TOOLS)
    assert r["id"] == 7 and r["error"]["code"] == -32600


def test_herramientas_que_cambian_el_entorno_son_destructivas():
    por_nombre = {t["name"]: t for t in mcp_server.TOOLS}
    for nombre in ("suite_auto_update", "suite_instalar"):
        assert por_nombre[nombre]["annotations"]["destructiveHint"] is True
    assert por_nombre["bcn_get_codigo"]["annotations"]["destructiveHint"] is False


def test_servidor_real_sobrevive_a_json_invalido_en_la_primera_linea():
    """El caso que mataba el proceso: basura primero, después el handshake normal."""
    entrada = "\n".join([
        "{basura",
        _linea(id=1, method="initialize", params={"protocolVersion": "2025-03-26", "capabilities": {}}),
        _linea(method="notifications/initialized"),
        _linea(id=2, method="ping"),
    ]) + "\n"
    entorno = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    corrida = subprocess.run([sys.executable, str(RAIZ / "mcp_server.py")], input=entrada, capture_output=True,
                             text=True, encoding="utf-8", timeout=180, cwd=str(RAIZ), env=entorno)
    respuestas = [json.loads(linea) for linea in corrida.stdout.splitlines() if linea.strip().startswith("{")]
    assert respuestas[0]["error"]["code"] == -32700 and respuestas[0]["id"] is None
    assert respuestas[1]["id"] == 1 and respuestas[1]["result"]["protocolVersion"] == "2025-03-26"
    assert respuestas[2] == {"jsonrpc": "2.0", "id": 2, "result": {}}


def test_salida_gigante_se_recorta_y_se_guarda_completa(tmp_path, monkeypatch):
    """Medido el 2026-10-07: ocr_extract_pdf devolvía 3,2 M de caracteres y caso_ejecutar 3,7 M;
    Claude Code corta por encima de ~25 000 tokens y los demás harness llenan el contexto."""
    monkeypatch.setenv("OPENLEGAL_SALIDAS_DIR", str(tmp_path))
    monkeypatch.setenv("OPENLEGAL_MAX_SALIDA", "5000")
    enorme = {"texto": "a" * 50_000, "articulos": [{"n": i, "t": "b" * 500} for i in range(200)], "fuente": "BCN"}
    salida = mcp_server.ajustar_salida("ocr_extract_pdf", enorme)
    assert len(json.dumps(salida, ensure_ascii=False, separators=(",", ":"))) <= 5000
    assert salida["fuente"] == "BCN", "la forma del resultado se conserva"
    aviso = salida["_salida_recortada"]
    assert aviso["caracteres_originales"] > 100_000
    assert json.loads(pathlib.Path(aviso["archivo_completo"]).read_text(encoding="utf-8")) == enorme


def test_salida_chica_no_se_toca_y_el_tope_se_puede_apagar(monkeypatch):
    chico = {"ok": True}
    assert mcp_server.ajustar_salida("x", chico) is chico
    monkeypatch.setenv("OPENLEGAL_MAX_SALIDA", "0")
    grande = {"texto": "a" * 200_000}
    assert mcp_server.ajustar_salida("x", grande) is grande


def test_tools_call_aplica_el_tope(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENLEGAL_SALIDAS_DIR", str(tmp_path))
    monkeypatch.setenv("OPENLEGAL_MAX_SALIDA", "3000")
    monkeypatch.setattr(mcp_server, "handle_tool_call", lambda nombre, args: {"items": ["x" * 400] * 100})
    r = procesar_mensaje({"jsonrpc": "2.0", "id": 9, "method": "tools/call",
                          "params": {"name": "cgr_search_auditorias", "arguments": {}}}, TOOLS)
    texto = r["result"]["content"][0]["text"]
    assert len(texto) <= 3000 and "_salida_recortada" in json.loads(texto)
    assert r["result"]["isError"] is False


def test_caso_ejecutar_no_trae_codigos_completos(monkeypatch):
    """Sin artículo, bcn_get_codigo devolvía el Código entero (millones de caracteres)."""
    import case_intake

    assert case_intake._articulos_mencionados("despido Art. 161 Código del Trabajo", "trabajo") == ["161"]
    assert case_intake._articulos_mencionados("un caso sin normas", "civil") == []


def test_stdout_solo_lleva_json_rpc_aunque_una_libreria_avise():
    """PyMuPDF escribía su aviso de `import fitz` en el stdout real (fuera del redirect): el SDK
    oficial de MCP recibía una línea no-JSON. Una herramienta que abre un PDF no puede ensuciar el canal."""
    pdf = RAIZ / "Manuales" / "doctrina48981.pdf"
    if not pdf.exists():
        import pytest
        pytest.skip("falta el PDF de muestra")
    entrada = "\n".join([
        _linea(id=1, method="initialize", params={"protocolVersion": "2025-06-18", "capabilities": {}}),
        _linea(id=2, method="tools/call", params={"name": "ocr_plan_documento", "arguments": {"pdf_path": str(pdf)}}),
    ]) + "\n"
    entorno = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    corrida = subprocess.run([sys.executable, str(RAIZ / "mcp_server.py")], input=entrada, capture_output=True,
                             text=True, encoding="utf-8", timeout=240, cwd=str(RAIZ), env=entorno)
    lineas = [linea for linea in corrida.stdout.splitlines() if linea.strip()]
    for linea in lineas:
        assert json.loads(linea)["jsonrpc"] == "2.0", f"línea no JSON-RPC en stdout: {linea[:120]}"
    assert [json.loads(linea)["id"] for linea in lineas] == [1, 2]
