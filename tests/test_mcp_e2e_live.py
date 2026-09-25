"""
Open Legal Chile — Test E2E de Protocolo y Servidor MCP (Nivel 1)
Valida en vivo el ciclo completo JSON-RPC 2.0 por stdio:
1. Handshake MCP (initialize, notifications/initialized).
2. Catálogo completo de 75 herramientas y validación de JSON Schema.
3. Invocación de herramientas en vivo sobre conectores estatales, doctrina y Hugging Face.
4. Perfiles temáticos (scoped profiles) y ahorro de tokens.
"""

import json
import os
import subprocess
import sys
import time
import pytest


class MCPClientRunner:
    """Cliente mínimo MCP JSON-RPC 2.0 sobre stdio para pruebas E2E."""

    def __init__(self, profile: str = ""):
        self.profile = profile
        self.proc = None
        self.req_counter = 0

    def __enter__(self):
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        if self.profile:
            env["OPENLEGAL_PROFILE"] = self.profile
        else:
            env.pop("OPENLEGAL_PROFILE", None)

        self.proc = subprocess.Popen(
            [sys.executable, "mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=env,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=3)
            except Exception:
                self.proc.kill()

    def send_request(self, method: str, params: dict | None = None) -> dict:
        self.req_counter += 1
        req_id = self.req_counter
        msg = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
        }
        if params is not None:
            msg["params"] = params

        line = json.dumps(msg, ensure_ascii=False) + "\n"
        assert self.proc is not None and self.proc.stdin is not None and self.proc.stdout is not None
        self.proc.stdin.write(line)
        self.proc.stdin.flush()

        resp_line = self.proc.stdout.readline()
        if not resp_line:
            stderr = self.proc.stderr.read() if self.proc.stderr else ""
            raise RuntimeError(f"Servidor MCP cerró el stream sin respuesta. Stderr: {stderr}")

        data = json.loads(resp_line)
        assert data.get("id") == req_id, f"ID de respuesta no coincide: {data.get('id')} != {req_id}"
        return data

    def call_tool(self, name: str, arguments: dict | None = None) -> tuple[dict, float]:
        start = time.perf_counter()
        resp = self.send_request("tools/call", {
            "name": name,
            "arguments": arguments or {},
        })
        elapsed = time.perf_counter() - start

        assert "error" not in resp, f"Error JSON-RPC en tool {name}: {resp.get('error')}"
        result = resp.get("result", {})
        assert not result.get("isError", False), f"Tool {name} retornó isError=True"
        content = result.get("content", [])
        assert len(content) > 0, f"Tool {name} no retornó contenido"
        payload_text = content[0].get("text", "{}")
        parsed = json.loads(payload_text)
        return parsed, elapsed


def test_mcp_e2e_handshake_and_catalog():
    """Valida el handshake y el catálogo de las 75 herramientas oficiales."""
    with MCPClientRunner() as client:
        # 1. Initialize
        init_resp = client.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "e2e-tester", "version": "1.0.0"},
        })
        assert "result" in init_resp
        server_info = init_resp["result"].get("serverInfo", {})
        assert server_info.get("name") in ("open-legal-chile", "open-legal-chile-mcp")

        # 2. Ping
        ping_resp = client.send_request("ping")
        assert "result" in ping_resp

        # 3. Tools List
        tools_resp = client.send_request("tools/list")
        tools = tools_resp.get("result", {}).get("tools", [])
        assert len(tools) == 75, f"Esperadas 75 herramientas, obtenidas: {len(tools)}"

        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"].get("type") == "object"


def test_mcp_e2e_live_tools_execution():
    """Ejecuta llamadas E2E reales a los pilares de conectores, doctrina y Hugging Face."""
    with MCPClientRunner() as client:
        # Handshake previo
        client.send_request("initialize")

        # 1. Pilar Positivo (BCN Ley Chile: Código Civil)
        data, t = client.call_tool("bcn_get_codigo", {"codigo": "civil", "articulo": "1545"})
        texto_norma = data.get("texto", "").lower().replace("\n", " ")
        assert "todo contrato legalmente celebrado es una ley para los contratantes" in texto_norma
        assert t < 5.0

        # 2. Pilar Positivo (BCN Ley Chile: Ley Karin 21.643)
        data, t = client.call_tool("bcn_get_ley", {"numero": 21643})
        assert "karin" in str(data).lower() or "acoso" in str(data).lower()

        # 3. Validador Forense de RUT (Algoritmo Módulo 11)
        data, _ = client.call_tool("rut_validar_chile", {"rut": "11.111.111-1"})
        assert "valido" in data
        assert data["valido"] is True

        # 4. Mandato Judicial Art. 7 CPC
        data, _ = client.call_tool("cpc_validar_mandato", {
            "texto_mandato": "Se confiere poder para percibir, transigir y desistirse en primera instancia."
        })
        assert "detalle_facultades_art_7_inc_2" in data
        assert "resumen_ejecutivo" in data

        # 5. Pilar Dogmático (Tratados Canónicos SQLite FTS5)
        data, _ = client.call_tool("doctrina_search", {"query": "responsabilidad extracontractual culpa", "limit": 2})
        items = data.get("resultados", [])
        assert len(items) > 0
        assert "cita_oficial" in items[0]
        assert "fuente_huggingface" in items[0]

        # 6. Pilar Dogmático (Ficha de Institución Doctrinal)
        data, _ = client.call_tool("doctrina_get_institucion", {"nombre": "culpa"})
        assert "autor" in data
        assert "fuente_huggingface" in data

        # 7. Hugging Face Datasets Hub
        data, _ = client.call_tool("huggingface_search_dataset", {"query": "barros", "limit": 3})
        assert data.get("total_coincidencias", 0) > 0
        assert len(data.get("resultados", [])) > 0

        # 8. Mesa de Entrada (Intake automático en lenguaje natural)
        data, _ = client.call_tool("caso_analizar", {
            "entrada": "El trabajador fue despedido verbalmente sin carta de despido ni pago de finiquito."
        })
        assert data.get("materia", "").lower() == "laboral"
        assert "plan" in data
        assert len(data.get("plan", [])) > 0


def test_mcp_e2e_scoped_profiles():
    """Valida que los perfiles temáticos reduzcan la lista de herramientas para ahorrar tokens."""
    with MCPClientRunner(profile="laboral") as client:
        client.send_request("initialize")
        tools_resp = client.send_request("tools/list")
        tools = tools_resp.get("result", {}).get("tools", [])
        tool_names = [t["name"] for t in tools]

        # El perfil laboral debe contener las herramientas laborales clave y no las 75
        assert len(tools) <= 15
        assert "dt_search_doctrina" in tool_names
        assert "bcn_get_codigo" in tool_names
        assert "cne_get_centrales_y_proyectos" not in tool_names
