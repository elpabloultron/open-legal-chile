"""Regenera docs/tools.json con el catálogo real del servidor MCP (misma forma y orden que TOOLS)."""

import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import mcp_server  # noqa: E402

destino = RAIZ / "docs" / "tools.json"
destino.write_text(json.dumps(mcp_server.TOOLS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"docs/tools.json: {len(mcp_server.TOOLS)} herramientas · {destino.stat().st_size / 1024:.0f} KB")
