"""Configuración MCP lista para cada harness: una instalación, todos los clientes.

El producto apunta a que cualquier harness (Antigravity, Claude Code, Cursor, VS Code, Codex, dsh…)
vea las 77 herramientas sin editar archivos a mano y sin abrir una terminal más que para este
comando. Ninguna integración pisa lo que la persona ya tenga configurado: los JSON se fusionan
(con respaldo `.bak`) y el parche Cordis de dsh se agrega al final del que exista, porque en ese
harness los plugins viven en capas.
"""

from __future__ import annotations

import json
import pathlib
import shutil
from typing import Any, Dict, List, Optional, Union

COMANDO = "openlegal-mcp"
SERVIDOR = "open-legal-chile"
ID_DSH = "mcp-open-legal-chile"


def _entrada() -> Dict[str, Any]:
    return {"command": COMANDO, "args": [], "env": {"PYTHONUNBUFFERED": "1"}}


def clientes() -> List[str]:
    return ["claude-code", "cursor", "vscode", "antigravity", "codex", "dsh", "generic"]


def _json_bonito(datos: Dict[str, Any]) -> str:
    return json.dumps(datos, indent=2, ensure_ascii=False) + "\n"


def configuracion(cliente: str) -> Dict[str, str]:
    """Devuelve {cliente, clave, ruta, contenido} para el archivo de configuración del cliente."""
    c = (cliente or "").strip().lower()
    if c in ("claude-code", "claude", "claude-desktop", "cursor", "antigravity", "generic"):
        ruta = {
            "claude-code": ".mcp.json",
            "cursor": ".cursor/mcp.json",
            "antigravity": "mcp_config.json",
        }.get(c, ".mcp.json")  # genérico y claude-desktop comparten el formato estándar
        return {"cliente": c, "clave": "mcpServers", "ruta": ruta,
                "contenido": _json_bonito({"mcpServers": {SERVIDOR: _entrada()}})}
    if c == "vscode":
        return {"cliente": c, "clave": "servers", "ruta": ".vscode/mcp.json",
                "contenido": _json_bonito({"servers": {SERVIDOR: {"type": "stdio", **_entrada()}}})}
    if c == "codex":
        toml = f'[mcp_servers.{SERVIDOR}]\ncommand = "{COMANDO}"\nargs = []\n'
        return {"cliente": c, "clave": "", "ruta": ".codex/config.toml", "contenido": toml}
    if c == "dsh":
        yaml = (
            "# Open Legal Chile — capa de parche Cordis (agregado por `openlegal integrar`)"
            "\n- insert:"
            f"\n    - id: {ID_DSH}"
            "\n      name: '@deepseek-ai/dsh-mcp-client'"
            "\n      config:"
            "\n        serverName: open_legal_chile"
            "\n        transport: stdio"
            f"\n        command: '{COMANDO}'"
            "\n        args: []"
            "\n"
        )
        return {"cliente": c, "clave": "", "ruta": "cordis.patch.yml", "contenido": yaml}
    raise ValueError(f"Cliente desconocido: {cliente}. Opciones: {', '.join(clientes())}")


def detectar_instalados(carpeta_base: Optional[Union[str, pathlib.Path]] = None) -> List[str]:
    """Clientes que parecen estar instalados, por sus carpetas de configuración.

    Mira la carpeta indicada (por defecto, la actual: ahí vive la configuración por proyecto, que
    es la que un usuario configura desde la raíz de su despacho).
    """
    base = pathlib.Path(carpeta_base) if carpeta_base else pathlib.Path.cwd()
    pistas = {
        "claude-code": (".claude", ".claude.json", ".mcp.json"),
        "cursor": (".cursor", ".config/Cursor"),
        "vscode": (".vscode", ".config/Code", ".config/Code - Insiders"),
        "codex": (".codex", ".config/codex"),
        "dsh": (".dsh",),
        "antigravity": (".antigravity", ".codeium", ".config/Antigravity"),
    }
    return [cliente for cliente, posibles in pistas.items() if any((base / p).exists() for p in posibles)]


def escribir(cliente: str, destino: Optional[Union[str, pathlib.Path]] = None,
             carpeta_base: Optional[Union[str, pathlib.Path]] = None) -> Dict[str, str]:
    """Escribe (o fusiona) la configuración del cliente. Devuelve qué se hizo, con la ruta."""
    cfg = configuracion(cliente)
    base = pathlib.Path(carpeta_base) if carpeta_base else pathlib.Path.cwd()
    ruta = pathlib.Path(destino) if destino else base / cfg["ruta"]
    if not ruta.is_absolute():
        ruta = base / ruta
    ruta.parent.mkdir(parents=True, exist_ok=True)

    previo = ruta.read_text(encoding="utf-8") if ruta.exists() else ""
    if SERVIDOR in previo or ID_DSH in previo:
        return {"cliente": cfg["cliente"], "archivo": str(ruta), "estado": "ya_configurado",
                "nota": "ya estaba configurado: no se tocó el archivo"}

    if not previo:
        ruta.write_text(cfg["contenido"], encoding="utf-8")
        return {"cliente": cfg["cliente"], "archivo": str(ruta), "estado": "escrito",
                "nota": "configuración nueva"}

    respaldo = ruta.with_name(ruta.name + ".bak")
    shutil.copy2(ruta, respaldo)
    if cfg["clave"]:
        # JSON: se fusiona nuestra entrada y se respeta todo lo demás que ya estaba.
        try:
            datos = json.loads(previo)
        except json.JSONDecodeError:
            datos = {}
        if not isinstance(datos, dict):
            datos = {}
        datos.setdefault(cfg["clave"], {})[SERVIDOR] = json.loads(cfg["contenido"])[cfg["clave"]][SERVIDOR]
        ruta.write_text(_json_bonito(datos), encoding="utf-8")
        estado = "fusionado"
    else:
        # TOML/YAML: el bloque se agrega al final (en dsh el parche se compone por capas).
        ruta.write_text(previo.rstrip() + "\n\n" + cfg["contenido"], encoding="utf-8")
        estado = "agregado"
    return {"cliente": cfg["cliente"], "archivo": str(ruta), "estado": estado,
            "respaldo": str(respaldo), "nota": "se conservó lo que ya estaba"}


def escribir_todos(clientes_a_configurar: Optional[List[str]] = None,
                   carpeta_base: Optional[Union[str, pathlib.Path]] = None) -> List[Dict[str, str]]:
    """Configura varios clientes de una vez.

    Sin lista explícita: mira la carpeta actual (configuración por proyecto) y, si ahí no hay
    ninguna pista, cae a la carpeta personal — que es el caso de `pip install` y una sola línea.
    """
    if clientes_a_configurar is not None:
        return [escribir(nombre, carpeta_base=carpeta_base) for nombre in clientes_a_configurar]

    base = pathlib.Path(carpeta_base) if carpeta_base else pathlib.Path.cwd()
    detectados = detectar_instalados(base)
    if not detectados and base != pathlib.Path.home():
        base = pathlib.Path.home()
        detectados = detectar_instalados(base)
    return [escribir(nombre, carpeta_base=base) for nombre in detectados]


if __name__ == "__main__":  # pragma: no cover
    for nombre in clientes():
        cfg = configuracion(nombre)
        print(f"# {nombre} → {cfg['ruta']}")
