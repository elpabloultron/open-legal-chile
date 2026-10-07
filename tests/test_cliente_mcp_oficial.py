"""El servidor habla con el cliente oficial del SDK de MCP, no solo con nuestro cliente de pruebas.

Los harness (Claude Code, Cursor, VS Code, Gemini CLI…) usan implementaciones del SDK oficial, que
validan cada mensaje con su esquema. Esta prueba hace el recorrido completo con ese cliente:
handshake con versión e instrucciones, catálogo, prompts, los tres recursos y llamadas sin red.
Se salta si el paquete `mcp` no está instalado (el job `harness` de la CI lo instala).
"""

import json
import os
import pathlib
import sys

import pytest

pytest.importorskip("mcp")
anyio = pytest.importorskip("anyio")

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def _campo(objeto, *nombres):
    """El SDK 1.x usa camelCase (protocolVersion) y el 2.x snake_case (protocol_version)."""
    for nombre in nombres:
        if hasattr(objeto, nombre):
            return getattr(objeto, nombre)
    raise AttributeError(nombres)


async def _recorrido() -> dict:
    parametros = StdioServerParameters(
        command=sys.executable, args=[str(RAIZ / "mcp_server.py")],
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
    )
    async with stdio_client(parametros) as (lectura, escritura):
        async with ClientSession(lectura, escritura) as sesion:
            inicio = await sesion.initialize()
            herramientas = (await sesion.list_tools()).tools
            prompts = (await sesion.list_prompts()).prompts
            recursos = (await sesion.list_resources()).resources
            textos = {}
            for recurso in recursos:
                contenido = await sesion.read_resource(recurso.uri)
                textos[str(recurso.uri)] = contenido.contents[0].text
            rut = await sesion.call_tool("rut_validar_chile", {"rut": "11.111.111-1"})
            skills = await sesion.call_tool("skills_listar", {})
            inexistente = await sesion.call_tool("herramienta_que_no_existe", {})
            return {
                "version": _campo(inicio, "protocolVersion", "protocol_version"),
                "instrucciones": _campo(inicio, "instructions"),
                "herramientas": [h.name for h in herramientas],
                "prompts": [p.name for p in prompts],
                "recursos": textos,
                "rut": (json.loads(rut.content[0].text), _campo(rut, "isError", "is_error")),
                "skills": json.loads(skills.content[0].text),
                "inexistente_es_error": _campo(inexistente, "isError", "is_error"),
            }


def test_recorrido_completo_con_el_cliente_oficial():
    r = anyio.run(_recorrido)
    assert r["version"] in ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
    assert "consulta_maestra" in r["instrucciones"]
    assert len(r["herramientas"]) == 87 and "consulta_maestra" in r["herramientas"]
    assert r["prompts"] == ["protocolo_citas", "consulta_juridica_completa"]
    assert len(r["recursos"]) == 3 and all(texto.strip() for texto in r["recursos"].values())
    assert "Protocolo no disponible" not in r["recursos"]["openlegal://reglas/citacion"]
    datos_rut, rut_es_error = r["rut"]
    assert datos_rut["valido"] is True and rut_es_error is False
    assert len(r["skills"]["skills"]) >= 18 and len(r["skills"]["agentes"]) >= 19
    assert r["inexistente_es_error"] is True
