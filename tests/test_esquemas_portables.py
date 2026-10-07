"""Los esquemas de las herramientas tienen que valer en cualquier harness, no solo en Claude.

Gemini CLI, Antigravity, Codex/OpenAI y Copilot validan los `inputSchema` más estricto que
Claude: un array sin `items`, un `required` que nombra campos que no existen o una unión de
tipos (`"type": ["string", "object"]`) bastan para que descarten la herramienta o el servidor
completo. Esta prueba recorre las 87 herramientas con esas reglas.
"""

import re

import pytest

from mcp_server import TOOL_PROFILES, TOOLS

NOMBRE_VALIDO = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
# Claude Code expone mcp__<servidor>__<herramienta>; varios proveedores limitan el nombre a 64.
PREFIJO_CLAUDE_CODE = "mcp__open-legal-chile__"


def _problemas(esquema, ruta="$"):
    if not isinstance(esquema, dict):
        return [f"{ruta}: el esquema no es un objeto"]
    problemas = []
    tipo = esquema.get("type")
    if isinstance(tipo, list):
        problemas.append(f"{ruta}: unión de tipos {tipo} (usar anyOf)")
    if tipo is None and not any(k in esquema for k in ("anyOf", "oneOf", "enum")):
        problemas.append(f"{ruta}: sin 'type'")
    if tipo == "array":
        if "items" not in esquema:
            problemas.append(f"{ruta}: array sin 'items'")
        else:
            problemas += _problemas(esquema["items"], ruta + "[]")
    if tipo == "object":
        propiedades = esquema.get("properties", {})
        for requerido in esquema.get("required", []) or []:
            if requerido not in propiedades:
                problemas.append(f"{ruta}: required '{requerido}' sin definir en properties")
        for nombre, sub in propiedades.items():
            problemas += _problemas(sub, f"{ruta}.{nombre}")
    for clave in ("anyOf", "oneOf"):
        for i, sub in enumerate(esquema.get(clave, []) or []):
            problemas += _problemas(sub, f"{ruta}.{clave}[{i}]")
    return problemas


@pytest.mark.parametrize("herramienta", TOOLS, ids=[t["name"] for t in TOOLS])
def test_esquema_portable(herramienta):
    esquema = herramienta.get("inputSchema")
    assert isinstance(esquema, dict), "falta inputSchema"
    assert esquema.get("type") == "object", "la raíz del inputSchema tiene que ser un objeto"
    assert not _problemas(esquema), _problemas(esquema)


def test_nombres_validos_en_todos_los_clientes():
    nombres = [t["name"] for t in TOOLS]
    assert len(nombres) == len(set(nombres)), "nombres duplicados"
    for nombre in nombres:
        assert NOMBRE_VALIDO.match(nombre), nombre
        assert len(PREFIJO_CLAUDE_CODE + nombre) <= 64, f"{nombre}: el nombre calificado supera 64 caracteres"


def test_descripciones_presentes():
    for t in TOOLS:
        assert (t.get("description") or "").strip(), f"{t['name']} sin descripción"


@pytest.mark.parametrize("perfil", sorted(TOOL_PROFILES))
def test_todo_perfil_puede_cumplir_el_protocolo_de_citas(perfil):
    """El prompt `protocolo_citas` exige `consulta_maestra` primero y `cita_texto` antes de citar."""
    herramientas = set(TOOL_PROFILES[perfil])
    for requerida in ("consulta_maestra", "cita_texto", "suite_doctor"):
        assert requerida in herramientas, f"el perfil {perfil} no expone {requerida}"
    assert herramientas <= {t["name"] for t in TOOLS}
