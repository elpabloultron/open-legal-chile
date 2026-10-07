"""Configuración MCP lista para cada harness: una instalación, todos los clientes.

El producto apunta a que cualquier harness (Claude Code, Claude Desktop, Cursor, VS Code, Gemini
CLI, Antigravity, Windsurf, Codex, OpenCode, dsh…) vea las 87 herramientas sin editar archivos a
mano y sin abrir una terminal más que para este comando. Ninguna integración pisa lo que la
persona ya tenga configurado: los JSON se fusionan (con respaldo `.bak`) y el parche Cordis de dsh
se agrega al final del que exista, porque en ese harness los plugins viven en capas.

Dos formas de lanzar el servidor:
- por defecto, la ruta absoluta de `openlegal-mcp` del mismo entorno donde está instalada la suite:
  las apps de escritorio (Claude Desktop, Cursor, VS Code abiertos desde el dock) no heredan el
  PATH de la terminal y un `openlegal-mcp` a secas no se encuentra;
- con `uvx=True`, `uvx --from openlegal-chile==<versión> openlegal-mcp`: no requiere instalar nada
  antes (solo uv) y es igual en Linux, macOS y Windows.

Configuración por proyecto (carpeta actual) o global (carpeta personal, con la ruta que cada
cliente lee de verdad: VS Code y Claude Desktop guardan la suya en la carpeta de soporte del
sistema operativo, y Claude Code registra el alcance de usuario con `claude mcp add -s user`).
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import sysconfig
from typing import Any, Dict, List, Optional, Tuple, Union

COMANDO = "openlegal-mcp"
SERVIDOR = "open-legal-chile"
ID_DSH = "mcp-open-legal-chile"
ESQUEMA_OPENCODE = "https://opencode.ai/config.json"

# Clientes que leen el formato estándar {"mcpServers": {...}}.
_FORMATO_MCPSERVERS = ("claude-code", "claude-desktop", "cursor", "gemini", "antigravity", "windsurf", "generic")
# Ruta por proyecto (relativa a la carpeta del proyecto).
_RUTA_PROYECTO = {
    "claude-code": ".mcp.json",
    "cursor": ".cursor/mcp.json",
    "vscode": ".vscode/mcp.json",
    "gemini": ".gemini/settings.json",
    "antigravity": "mcp_config.json",
    "codex": ".codex/config.toml",
    "opencode": "opencode.json",
    "dsh": "cordis.patch.yml",
    "generic": ".mcp.json",
}
# Clientes que solo tienen configuración global.
_SOLO_GLOBAL = ("claude-desktop", "windsurf")


def clientes() -> List[str]:
    return ["claude-code", "claude-desktop", "cursor", "vscode", "gemini", "antigravity", "windsurf",
            "codex", "opencode", "dsh", "generic"]


def comando_servidor() -> str:
    """Ruta absoluta de `openlegal-mcp` del entorno actual (o el nombre a secas si no se encuentra)."""
    nombre = COMANDO + (".exe" if os.name == "nt" else "")
    try:
        candidato = pathlib.Path(sysconfig.get_path("scripts")) / nombre
        if candidato.exists():
            return str(candidato)
    except (KeyError, TypeError):
        pass
    return shutil.which(COMANDO) or COMANDO


def _version_instalada() -> str:
    try:
        from importlib.metadata import version

        return version("openlegal-chile")
    except Exception:  # noqa: BLE001 — sin metadatos, uvx resuelve la última versión
        return ""


def lanzador(uvx: bool = False) -> Tuple[str, List[str]]:
    """(comando, argumentos) para arrancar el servidor MCP."""
    if uvx:
        version = _version_instalada()
        return "uvx", ["--from", f"openlegal-chile=={version}" if version else "openlegal-chile", COMANDO]
    return comando_servidor(), []


def _entrada(uvx: bool = False) -> Dict[str, Any]:
    comando, argumentos = lanzador(uvx)
    return {"command": comando, "args": argumentos, "env": {"PYTHONUNBUFFERED": "1"}}


def _json_bonito(datos: Dict[str, Any]) -> str:
    return json.dumps(datos, indent=2, ensure_ascii=False) + "\n"


def _carpeta_soporte() -> pathlib.Path:
    """Carpeta de configuración de aplicaciones del sistema operativo."""
    casa = pathlib.Path.home()
    if sys.platform == "darwin":
        return casa / "Library" / "Application Support"
    if os.name == "nt":
        return pathlib.Path(os.environ.get("APPDATA") or casa / "AppData" / "Roaming")
    return pathlib.Path(os.environ.get("XDG_CONFIG_HOME") or casa / ".config")


def ruta_global(cliente: str) -> Optional[pathlib.Path]:
    """Archivo de configuración global (de usuario) del cliente; None si se registra por CLI."""
    casa = pathlib.Path.home()
    soporte = _carpeta_soporte()
    return {
        "claude-desktop": soporte / "Claude" / "claude_desktop_config.json",
        "vscode": soporte / "Code" / "User" / "mcp.json",
        "cursor": casa / ".cursor" / "mcp.json",
        "gemini": casa / ".gemini" / "settings.json",
        "antigravity": casa / ".gemini" / "antigravity" / "mcp_config.json",
        "windsurf": casa / ".codeium" / "windsurf" / "mcp_config.json",
        "codex": casa / ".codex" / "config.toml",
        "opencode": soporte / "opencode" / "opencode.json",
        "dsh": casa / "cordis.patch.yml",
        "generic": casa / ".mcp.json",
    }.get(cliente)


def _normalizar(cliente: str) -> str:
    c = (cliente or "").strip().lower()
    alias = {"claude": "claude-code", "gemini-cli": "gemini", "code": "vscode", "vs-code": "vscode"}
    c = alias.get(c, c)
    if c not in clientes():
        raise ValueError(f"Cliente desconocido: {cliente}. Opciones: {', '.join(clientes())}")
    return c


def configuracion(cliente: str, uvx: bool = False, global_: bool = False) -> Dict[str, str]:
    """Devuelve {cliente, clave, ruta, contenido} para el archivo de configuración del cliente.

    `ruta` es relativa a la carpeta del proyecto, salvo en la configuración global (o en los
    clientes que solo tienen global), donde es absoluta.
    """
    c = _normalizar(cliente)
    entrada = _entrada(uvx)
    if global_ or c in _SOLO_GLOBAL:
        destino = ruta_global(c)
        ruta = str(destino) if destino else _RUTA_PROYECTO[c]
    else:
        ruta = _RUTA_PROYECTO[c]

    if c in _FORMATO_MCPSERVERS:
        return {"cliente": c, "clave": "mcpServers", "ruta": ruta,
                "contenido": _json_bonito({"mcpServers": {SERVIDOR: entrada}})}
    if c == "vscode":
        return {"cliente": c, "clave": "servers", "ruta": ruta,
                "contenido": _json_bonito({"servers": {SERVIDOR: {"type": "stdio", **entrada}}})}
    if c == "opencode":
        servidor = {"type": "local", "command": [entrada["command"], *entrada["args"]], "enabled": True,
                    "environment": entrada["env"]}
        return {"cliente": c, "clave": "mcp", "ruta": ruta,
                "contenido": _json_bonito({"$schema": ESQUEMA_OPENCODE, "mcp": {SERVIDOR: servidor}})}
    if c == "codex":
        # Las cadenas JSON son cadenas básicas TOML válidas (escapan \ y " igual): rutas de Windows incluidas.
        toml = (f'[mcp_servers.{SERVIDOR}]\ncommand = {json.dumps(entrada["command"])}\n'
                f'args = {json.dumps(entrada["args"])}\n\n'
                f'[mcp_servers.{SERVIDOR}.env]\nPYTHONUNBUFFERED = "1"\n')
        return {"cliente": c, "clave": "", "ruta": ruta, "contenido": toml}
    # dsh
    argumentos = "[" + ", ".join(f"'{a}'" for a in entrada["args"]) + "]"
    yaml = (
        "# Open Legal Chile — capa de parche Cordis (agregado por `openlegal integrar`)"
        "\n- insert:"
        f"\n    - id: {ID_DSH}"
        "\n      name: '@deepseek-ai/dsh-mcp-client'"
        "\n      config:"
        "\n        serverName: open_legal_chile"
        "\n        transport: stdio"
        f"\n        command: '{entrada['command']}'"
        f"\n        args: {argumentos}"
        "\n"
    )
    return {"cliente": c, "clave": "", "ruta": ruta, "contenido": yaml}


def _pistas(global_: bool) -> Dict[str, Tuple[str, ...]]:
    pistas = {
        "claude-code": (".claude", ".claude.json", ".mcp.json"),
        "cursor": (".cursor", ".config/Cursor"),
        "vscode": (".vscode", ".config/Code", ".config/Code - Insiders"),
        "gemini": (".gemini",),
        "codex": (".codex", ".config/codex"),
        "opencode": ("opencode.json", ".opencode", ".config/opencode"),
        "dsh": (".dsh",),
        "antigravity": (".antigravity", ".gemini/antigravity", ".config/Antigravity"),
    }
    if global_:
        pistas["claude-desktop"] = ("Library/Application Support/Claude", ".config/Claude", "AppData/Roaming/Claude")
        pistas["windsurf"] = (".codeium/windsurf", ".windsurf")
        pistas["vscode"] = pistas["vscode"] + ("Library/Application Support/Code", "AppData/Roaming/Code")
    return pistas


def _es_casa(base: pathlib.Path) -> bool:
    try:
        return base.resolve() == pathlib.Path.home().resolve()
    except OSError:
        return False


def detectar_instalados(carpeta_base: Optional[Union[str, pathlib.Path]] = None) -> List[str]:
    """Clientes que parecen estar instalados, por sus carpetas de configuración.

    Mira la carpeta indicada (por defecto, la actual: ahí vive la configuración por proyecto, que
    es la que un usuario configura desde la raíz de su despacho). Si la carpeta es la personal,
    también reconoce los clientes que solo tienen configuración global (Claude Desktop, Windsurf).
    """
    base = pathlib.Path(carpeta_base) if carpeta_base else pathlib.Path.cwd()
    pistas = _pistas(global_=_es_casa(base))
    return [cliente for cliente, posibles in pistas.items() if any((base / p).exists() for p in posibles)]


def _registrar_claude_code_usuario(uvx: bool) -> Dict[str, str]:
    """Alcance de usuario de Claude Code: vive en ~/.claude.json y se registra con su CLI."""
    comando, argumentos = lanzador(uvx)
    orden = ["claude", "mcp", "add", "-s", "user", "-e", "PYTHONUNBUFFERED=1", SERVIDOR, "--", comando, *argumentos]
    if not shutil.which("claude"):
        return {"cliente": "claude-code", "archivo": "~/.claude.json", "estado": "manual",
                "nota": "no se encontró el CLI de Claude Code; registralo con: " + " ".join(orden)}
    corrida = subprocess.run(orden, capture_output=True, text=True, timeout=60)  # nosec B603
    salida = (corrida.stdout + corrida.stderr).strip()
    if corrida.returncode == 0:
        return {"cliente": "claude-code", "archivo": "~/.claude.json", "estado": "registrado",
                "nota": "alcance de usuario vía `claude mcp add -s user`"}
    if "already exists" in salida.lower():
        return {"cliente": "claude-code", "archivo": "~/.claude.json", "estado": "ya_configurado",
                "nota": "ya estaba registrado en el alcance de usuario"}
    return {"cliente": "claude-code", "archivo": "~/.claude.json", "estado": "error", "nota": salida[:300]}


def escribir(cliente: str, destino: Optional[Union[str, pathlib.Path]] = None,
             carpeta_base: Optional[Union[str, pathlib.Path]] = None, uvx: bool = False) -> Dict[str, str]:
    """Escribe (o fusiona) la configuración del cliente. Devuelve qué se hizo, con la ruta.

    Si la carpeta base es la personal, se escribe la configuración global del cliente.
    """
    base = pathlib.Path(carpeta_base) if carpeta_base else pathlib.Path.cwd()
    global_ = destino is None and _es_casa(base)
    c = _normalizar(cliente)
    if global_ and c == "claude-code":
        return _registrar_claude_code_usuario(uvx)
    cfg = configuracion(c, uvx=uvx, global_=global_)
    ruta = pathlib.Path(destino) if destino else base / cfg["ruta"]
    if not ruta.is_absolute():
        ruta = base / ruta
    ruta.parent.mkdir(parents=True, exist_ok=True)

    previo = ruta.read_text(encoding="utf-8") if ruta.exists() else ""
    if SERVIDOR in previo or ID_DSH in previo:
        return {"cliente": cfg["cliente"], "archivo": str(ruta), "estado": "ya_configurado",
                "nota": "ya estaba configurado: no se tocó el archivo"}

    if not previo.strip():
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
                   carpeta_base: Optional[Union[str, pathlib.Path]] = None, uvx: bool = False) -> List[Dict[str, str]]:
    """Configura varios clientes de una vez.

    Sin lista explícita: mira la carpeta actual (configuración por proyecto) y, si ahí no hay
    ninguna pista, cae a la carpeta personal — que es el caso de `pip install` y una sola línea.
    """
    if clientes_a_configurar is not None:
        return [escribir(nombre, carpeta_base=carpeta_base, uvx=uvx) for nombre in clientes_a_configurar]

    base = pathlib.Path(carpeta_base) if carpeta_base else pathlib.Path.cwd()
    detectados = detectar_instalados(base)
    if not detectados and not _es_casa(base):
        base = pathlib.Path.home()
        detectados = detectar_instalados(base)
    return [escribir(nombre, carpeta_base=base, uvx=uvx) for nombre in detectados]


if __name__ == "__main__":  # pragma: no cover
    for nombre in clientes():
        cfg = configuracion(nombre)
        print(f"# {nombre} → {cfg['ruta']}")
