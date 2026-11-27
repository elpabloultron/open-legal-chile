"""Pruebas offline de servidor Streamable HTTP (Zero-Data-Leak) y empaquetador `.mcpb`."""

from __future__ import annotations

import json
import pathlib
import threading
import urllib.error
import urllib.request
import zipfile
from typing import Any, Dict, Optional, Tuple

import pytest

import mcp_http_server
from scripts.empaquetar_mcpb import ARCHIVOS_BUNDLE, construir_mcpb, validar_manifiesto_mcpb


def _http_call(
    url: str,
    *,
    method: str = "GET",
    body: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[int, Dict[str, str], bytes]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read()
    except urllib.error.HTTPError as err:
        return err.code, {k.lower(): v for k, v in err.headers.items()}, err.read()


def test_guardia_red_y_origin_allowlist() -> None:
    token_prueba = "-".join(("olc", "guard", "v2"))
    with pytest.raises(ValueError, match="OPENLEGAL_AUTH_TOKEN"):
        mcp_http_server.validar_configuracion_red("0.0.0.0", "")

    mcp_http_server.validar_configuracion_red("127.0.0.1", "")
    mcp_http_server.validar_configuracion_red("0.0.0.0", token_prueba)
    mcp_http_server.validar_configuracion_red("0.0.0.0", "", allow_insecure=True)

    patrones = ["http://localhost", "https://estudio.cl"]
    assert mcp_http_server.origin_permitido("https://estudio.cl:8443", patrones) is True
    assert mcp_http_server.origin_permitido("https://malicioso.example", patrones) is False


def test_ciclo_completo_streamable_http_auth_sse_y_sesiones() -> None:
    token_dinamico = "-".join(("olc", "http", "session", "200"))
    srv = mcp_http_server.crear_servidor_http(
        "127.0.0.1",
        0,
        profile="full",
        auth_token=token_dinamico,
        max_rpm=500,
    )
    hilo = threading.Thread(target=srv.serve_forever, daemon=True)
    hilo.start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    auth_h = {"Authorization": f"Bearer {token_dinamico}", "Origin": "http://127.0.0.1"}

    try:
        # 1. /health sin secreto expuesto
        st, _h, raw = _http_call(f"{base}/health")
        assert st == 200
        health = json.loads(raw.decode("utf-8"))
        assert health["status"] == "ok"
        assert health["tools"] == 114
        assert health["auth_enabled"] is True

        # 2. 401 sin token y 403 con Origin bloqueado
        st_unauth, _h, _raw = _http_call(
            f"{base}/mcp",
            method="POST",
            body={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        )
        assert st_unauth == 401

        st_orig, _h, _raw = _http_call(
            f"{base}/mcp",
            method="POST",
            body={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={"Authorization": f"Bearer {token_dinamico}", "Origin": "https://evil.example"},
        )
        assert st_orig == 403

        # 3. initialize -> Mcp-Session-Id
        st_init, hdr_init, raw_init = _http_call(
            f"{base}/mcp",
            method="POST",
            body={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05", "capabilities": {}},
            },
            headers=auth_h,
        )
        assert st_init == 200
        sid = hdr_init.get("mcp-session-id", "")
        assert sid
        assert json.loads(raw_init.decode("utf-8"))["result"]["serverInfo"]["name"] == "open-legal-chile-mcp"

        # 4. tools/list con sesión
        st_list, _h, raw_list = _http_call(
            f"{base}/mcp",
            method="POST",
            body={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            headers={**auth_h, "Mcp-Session-Id": sid},
        )
        assert st_list == 200
        assert len(json.loads(raw_list.decode("utf-8"))["result"]["tools"]) == 114

        # 5. tools/call rut_validar_chile (JSON y SSE)
        call_payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "rut_validar_chile", "arguments": {"rut": "99.999.999-9"}},
        }
        st_call, _h, raw_call = _http_call(
            f"{base}/mcp",
            method="POST",
            body=call_payload,
            headers={**auth_h, "Mcp-Session-Id": sid, "Accept": "application/json"},
        )
        assert st_call == 200
        res_call = json.loads(raw_call.decode("utf-8"))["result"]
        assert res_call["structuredContent"]["valido"] is True

        st_sse, hdr_sse, raw_sse = _http_call(
            f"{base}/mcp",
            method="POST",
            body=call_payload,
            headers={**auth_h, "Mcp-Session-Id": sid, "Accept": "text/event-stream"},
        )
        assert st_sse == 200
        assert hdr_sse["content-type"].startswith("text/event-stream")
        assert b"event: message" in raw_sse and b"data:" in raw_sse

        # 6. GET /mcp SSE ready
        st_get, hdr_get, raw_get = _http_call(
            f"{base}/mcp",
            method="GET",
            headers={**auth_h, "Accept": "text/event-stream"},
        )
        assert st_get == 200
        assert hdr_get["content-type"].startswith("text/event-stream")
        assert b"event: ready" in raw_get

        # 7. DELETE /mcp cierra sesión y rechaza uso posterior con 404
        st_del, _h, raw_del = _http_call(
            f"{base}/mcp",
            method="DELETE",
            headers={**auth_h, "Mcp-Session-Id": sid},
        )
        assert st_del == 200
        assert json.loads(raw_del.decode("utf-8"))["closed"] is True

        st_closed, _h, _raw = _http_call(
            f"{base}/mcp",
            method="POST",
            body={"jsonrpc": "2.0", "id": 4, "method": "tools/list"},
            headers={**auth_h, "Mcp-Session-Id": sid},
        )
        assert st_closed == 404
    finally:
        srv.shutdown()
        srv.server_close()


def test_empaquetador_mcpb_valido_y_autocontenido(tmp_path: pathlib.Path) -> None:
    assert validar_manifiesto_mcpb() == []
    salida = tmp_path / "open-legal-chile-test.mcpb"
    bundle = construir_mcpb(salida)
    assert bundle.is_file()
    with zipfile.ZipFile(bundle, "r") as zf:
        nombres = set(zf.namelist())
        assert "manifest.json" in nombres
        for rel in ARCHIVOS_BUNDLE:
            assert rel in nombres
        manifiesto = json.loads(zf.read("manifest.json").decode("utf-8"))
        assert manifiesto["name"] == "open-legal-chile"
        assert manifiesto["manifest_version"] == "0.3"
