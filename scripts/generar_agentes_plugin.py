"""Genera agents/<agente>.md (subagentes del plugin de Claude Code) desde agents/<agente>.json.

Los JSON son la fuente de verdad del runtime (`agent_list`, `agent_run`); Claude Code solo lee
agentes en Markdown. Este script escribe el par .md de cada JSON con las herramientas calificadas
como las expone el plugin (mcp__plugin_open-legal-chile_open-legal-chile__<herramienta>).
tests/test_plugin_claude.py falla si un .md queda desactualizado.

Uso:
  python scripts/generar_agentes_plugin.py          # escribe agents/*.md
  python scripts/generar_agentes_plugin.py --check  # solo verifica (exit 1 si hay diferencias)
"""

import json
import pathlib
import sys
from types import SimpleNamespace
from typing import Dict

RAIZ = pathlib.Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


def agentes_markdown() -> Dict[pathlib.Path, str]:
    """{ruta del .md: contenido esperado} para cada agents/*.json."""
    from agents_runtime import PREFIJO_MCP_PLUGIN, subagente_markdown

    salida = {}
    for archivo in sorted((RAIZ / "agents").glob("*.json")):
        datos = json.loads(archivo.read_text(encoding="utf-8"))
        agente = SimpleNamespace(name=datos.get("name", archivo.stem), description=datos.get("description", ""),
                                 tools=datos.get("tools", []), system_prompt=datos.get("systemPrompt", ""))
        salida[archivo.with_suffix(".md")] = subagente_markdown(agente, PREFIJO_MCP_PLUGIN)
    return salida


def main() -> int:
    solo_verificar = "--check" in sys.argv
    distintos = []
    for ruta, contenido in agentes_markdown().items():
        actual = ruta.read_text(encoding="utf-8") if ruta.exists() else None
        if actual == contenido:
            continue
        distintos.append(ruta.name)
        if not solo_verificar:
            ruta.write_text(contenido, encoding="utf-8")
    if solo_verificar and distintos:
        print("Agentes desactualizados (correr scripts/generar_agentes_plugin.py):", ", ".join(distintos))
        return 1
    print(f"{len(distintos)} agentes {'por actualizar' if solo_verificar else 'escritos'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
