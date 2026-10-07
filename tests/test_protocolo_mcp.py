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
