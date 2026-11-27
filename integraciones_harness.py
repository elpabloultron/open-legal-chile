"""Configuración MCP lista para cada harness: una instalación, todos los clientes.

El producto apunta a que cualquier harness (Claude Code, Claude Desktop, Cursor, VS Code, Gemini
CLI, Antigravity, Windsurf, Codex, OpenCode, dsh…) vea las 88 herramientas sin editar archivos a
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
import re
import shutil
import subprocess
import sys
import sysconfig
from typing import Any, Dict, List, Optional, Tuple, Union

from recursos import ruta_recurso

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
    "hermes": ".hermes/config.yaml",
    "opencode": "opencode.json",
    "dsh": "cordis.patch.yml",
    "generic": ".mcp.json",
}
# Clientes que solo tienen configuración global.
_SOLO_GLOBAL = ("claude-desktop", "windsurf")


def clientes() -> List[str]:
    return ["claude-code", "claude-desktop", "cursor", "vscode", "gemini", "antigravity", "windsurf",
            "codex", "hermes", "opencode", "dsh", "generic"]


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
        "hermes": casa / ".hermes" / "config.yaml",
        "opencode": soporte / "opencode" / "opencode.json",
        "dsh": casa / "cordis.patch.yml",
        "generic": casa / ".mcp.json",
    }.get(cliente)


def _normalizar(cliente: str) -> str:
    c = (cliente or "").strip().lower()
    alias = {
        "claude": "claude-code",
        "gemini-cli": "gemini",
        "code": "vscode",
        "vs-code": "vscode",
        "hermes-agent": "hermes",
    }
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
    if c == "hermes":
        argumentos = "[" + ", ".join(json.dumps(a) for a in entrada["args"]) + "]"
        yaml_hermes = (
            "mcp_servers:\n"
            f"  {SERVIDOR}:\n"
            f"    command: {json.dumps(entrada['command'])}\n"
            f"    args: {argumentos}\n"
            "    env:\n"
            '      PYTHONUNBUFFERED: "1"\n'
            "    enabled: true\n"
        )
        return {"cliente": c, "clave": "", "ruta": ruta, "contenido": yaml_hermes}
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
        "hermes": (".hermes",),
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
    orden = ["claude", "mcp", "add", "-s", "user", "-e", "PYTHONUNBUFFERED=1", "--", SERVIDOR, comando, *argumentos]
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


PREFIJO_MCP_ANTIGRAVITY = "mcp_open-legal-chile_open-legal-chile_"


def _copiar_skills(dest_skills: pathlib.Path, limpiar_obsoletas: bool = False) -> int:
    """Copia las 26 skills jurídicas (`.agents/skills/*/SKILL.md`) en `dest_skills`.

    Si `limpiar_obsoletas=True`, elimina subcarpetas antiguas en `dest_skills` que ya no existan
    en el paquete (evita skills huérfanas al actualizar un plugin instalado).
    """
    skills_src = ruta_recurso(".agents/skills")
    copiadas = 0
    if not skills_src.exists():
        return 0
    dest_skills.mkdir(parents=True, exist_ok=True)
    activas = set()
    for carpeta in sorted(skills_src.iterdir()):
        skill_md = carpeta / "SKILL.md"
        if skill_md.exists():
            activas.add(carpeta.name)
            d_skill = dest_skills / carpeta.name
            d_skill.mkdir(parents=True, exist_ok=True)
            shutil.copy2(skill_md, d_skill / "SKILL.md")
            copiadas += 1
    if limpiar_obsoletas:
        for existente in list(dest_skills.iterdir()):
            if existente.is_dir() and existente.name not in activas:
                shutil.rmtree(existente, ignore_errors=True)
    return copiadas


def _copiar_agentes_md(dest_agents: pathlib.Path) -> int:
    """Copia los 24 agentes jurídicos (`agents/*.md`, formato Claude Code) en `dest_agents`."""
    agents_src = ruta_recurso("agents")
    copiados = 0
    if not agents_src.exists():
        return 0
    dest_agents.mkdir(parents=True, exist_ok=True)
    for arch in sorted(agents_src.glob("*.md")):
        shutil.copy2(arch, dest_agents / arch.name)
        copiados += 1
    return copiados


def _escribir_agentes_antigravity(dest_agents: pathlib.Path) -> int:
    """Genera los 24 agentes en formato YAML nativo de Google Antigravity (`tools:` como lista).

    Antigravity exige que `tools` en el frontmatter YAML de `agents/*.md` sea una secuencia
    (`[]string`), a diferencia de Claude Code que usa cadena separada por comas. Generar los `.md`
    desde `agents/*.json` garantiza 0 errores bajo `agy plugin validate --strict`.
    """
    agents_src = ruta_recurso("agents")
    if not agents_src.exists():
        return 0
    dest_agents.mkdir(parents=True, exist_ok=True)
    escritos = 0
    esperados = set()
    for archivo in sorted(agents_src.glob("*.json")):
        datos = json.loads(archivo.read_text(encoding="utf-8"))
        nombre = datos.get("name", archivo.stem)
        descripcion = datos.get("description", "")
        herramientas = datos.get("tools", [])
        prompt = (datos.get("systemPrompt") or "").strip()
        lineas = [
            "---",
            f"name: {nombre}",
            f"description: {json.dumps(descripcion, ensure_ascii=False)}",
        ]
        if herramientas:
            lineas.append("tools:")
            for herramienta in herramientas:
                lineas.append(f"  - {PREFIJO_MCP_ANTIGRAVITY}{herramienta}")
        lineas += ["---", "", prompt, ""]
        destino = dest_agents / f"{archivo.stem}.md"
        destino.write_text("\n".join(lineas), encoding="utf-8")
        esperados.add(destino.name)
        escritos += 1
    for existente in list(dest_agents.glob("*.md")):
        if existente.name not in esperados:
            existente.unlink(missing_ok=True)
    return escritos


def _copiar_reglas(
    dest_archivo: pathlib.Path,
    cabecera: str = "",
    preferir_compacta: bool = False,
) -> bool:
    """Copia las reglas maestras de Derecho Continental chileno a `dest_archivo`.

    Cuando `preferir_compacta=True` (plugins de Antigravity con límite estricto de 24 000 bytes
    por archivo de reglas), usa `rules/AGENTS.md` (completo y < 24 KB, sin truncamiento) con
    respaldo a `AGENTS.md`.
    """
    src = ruta_recurso("rules/AGENTS.md") if preferir_compacta else ruta_recurso("AGENTS.md")
    if not src.exists():
        src = ruta_recurso("AGENTS.md")
    if not src.exists():
        return False
    dest_archivo.parent.mkdir(parents=True, exist_ok=True)
    if cabecera:
        dest_archivo.write_text(cabecera + src.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        shutil.copy2(src, dest_archivo)
    return True


def instalar_plugin_antigravity(
    destino_plugin: Optional[Union[str, pathlib.Path]] = None,
    uvx: bool = False,
) -> Dict[str, Any]:
    """Instala y sincroniza el paquete nativo de plugin de Google Antigravity
    en ~/.gemini/config/plugins/open-legal-chile/ (plugin.json, README.md, mcp_config.json,
    assets/logo.svg, skills/, agents/, rules/AGENTS.md). Cumple `agy plugin validate --strict`.
    """
    dest = pathlib.Path(destino_plugin) if destino_plugin else (
        pathlib.Path.home() / ".gemini" / "config" / "plugins" / SERVIDOR
    )
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "assets").mkdir(parents=True, exist_ok=True)
    (dest / "rules").mkdir(parents=True, exist_ok=True)

    # 1. plugin.json, README.md y logo.svg (desde repo o share/openlegal-chile en wheel)
    plugin_src = ruta_recurso("plugin.json")
    if plugin_src.exists():
        datos_plugin = json.loads(plugin_src.read_text(encoding="utf-8"))
        # En el plugin instalado las skills viven en la carpeta estándar `skills/`, no en `.agents/skills`
        datos_plugin.pop("skills", None)
        (dest / "plugin.json").write_text(_json_bonito(datos_plugin), encoding="utf-8")
    readme_src = ruta_recurso("README.md")
    if readme_src.exists():
        shutil.copy2(readme_src, dest / "README.md")
    logo_src = ruta_recurso("assets/logo.svg")
    if logo_src.exists():
        shutil.copy2(logo_src, dest / "assets" / "logo.svg")

    # 2. rules/AGENTS.md (<24 KB sin truncamiento), 26 skills (sin obsoletas) y 24 agentes YAML
    reglas_ok = _copiar_reglas(dest / "rules" / "AGENTS.md", preferir_compacta=True)
    skills_copiadas = _copiar_skills(dest / "skills", limpiar_obsoletas=True)
    agentes_copiados = _escribir_agentes_antigravity(dest / "agents")

    # 3. mcp_config.json con ruta absoluta del ejecutable y herramientas eager
    entrada = _entrada(uvx)
    entrada["tools"] = {
        "consulta_maestra": {"eager": True},
        "cita_texto": {"eager": True},
        "caso_analizar": {"eager": True},
        "ambiental_consulta_maestra": {"eager": True},
        "pjud_search_jurisprudencia": {"eager": True},
        "generar_documento": {"eager": True},
        "critique_documento": {"eager": True},
        "suite_doctor": {"eager": True},
    }
    mcp_file = dest / "mcp_config.json"
    mcp_file.write_text(
        _json_bonito({"mcpServers": {SERVIDOR: entrada}}),
        encoding="utf-8",
    )
    return {
        "cliente": "antigravity",
        "modo": "plugin_nativo",
        "plugin_dir": str(dest),
        "archivo": str(mcp_file),
        "estado": "instalado",
        "skills": skills_copiadas,
        "agents": agentes_copiados,
        "reglas": str(dest / "rules" / "AGENTS.md") if reglas_ok else "",
    }


def instalar_plugin_harness(
    cliente: str,
    carpeta_base: Optional[Union[str, pathlib.Path]] = None,
    global_: bool = True,
    uvx: bool = False,
) -> Dict[str, Any]:
    """Instala el **Plugin completo** de Open Legal Chile (MCP + 26 skills + 24 agentes + reglas
    maestras chilenas) en el harness indicado: antigravity, claude-code, codex, hermes, cursor, vscode.
    """
    c = _normalizar(cliente)
    base = (
        pathlib.Path(carpeta_base)
        if carpeta_base is not None
        else (pathlib.Path.home() if global_ else pathlib.Path.cwd())
    )

    if c == "antigravity":
        destino_ag = base / ".gemini" / "config" / "plugins" / SERVIDOR
        return instalar_plugin_antigravity(destino_plugin=destino_ag, uvx=uvx)

    mcp_res = escribir(c, carpeta_base=base, uvx=uvx)
    resultado: Dict[str, Any] = {
        "cliente": c,
        "modo": "plugin_completo",
        "archivo": mcp_res.get("archivo", ""),
        "estado": mcp_res.get("estado", "escrito"),
        "skills": 0,
        "agents": 0,
        "reglas": "",
    }

    if c == "claude-code":
        raiz_c = base / ".claude"
        resultado["skills"] = _copiar_skills(raiz_c / "skills")
        resultado["agents"] = _copiar_agentes_md(raiz_c / "agents")
        regla = raiz_c / "rules" / f"{SERVIDOR}.md"
        if _copiar_reglas(regla):
            resultado["reglas"] = str(regla)
        resultado["plugin_dir"] = str(raiz_c)
        resultado["comando_nativo"] = (
            "/plugin marketplace add elpabloultron/open-legal-chile && /plugin install open-legal-chile"
        )
        return resultado

    if c == "codex":
        # Codex descubre Agent Skills en .agents/skills/ y configuración MCP en .codex/config.toml
        skills_dir = base / ".agents" / "skills"
        resultado["skills"] = _copiar_skills(skills_dir)
        regla = base / ".codex" / "AGENTS.md"
        if _copiar_reglas(regla):
            resultado["reglas"] = str(regla)
        resultado["plugin_dir"] = str(base / ".codex")
        return resultado

    if c == "hermes":
        # Hermes Agent carga MCP desde .hermes/config.yaml y skills/reglas desde .hermes/skills/open-legal-chile/
        hermes_pack = base / ".hermes" / "skills" / SERVIDOR
        resultado["skills"] = _copiar_skills(hermes_pack)
        regla = hermes_pack / "AGENTS.md"
        if _copiar_reglas(regla):
            resultado["reglas"] = str(regla)
        resultado["plugin_dir"] = str(hermes_pack)
        return resultado

    if c == "cursor":
        raiz_cur = base / ".cursor"
        resultado["skills"] = _copiar_skills(raiz_cur / "skills")
        regla = raiz_cur / "rules" / f"{SERVIDOR}.mdc"
        cab = (
            "---\n"
            "description: Open Legal Chile — Derecho Continental de Chile (114 herramientas MCP y protocolo de citas)\n"
            "alwaysApply: true\n"
            "---\n\n"
        )
        if _copiar_reglas(regla, cabecera=cab):
            resultado["reglas"] = str(regla)
        resultado["plugin_dir"] = str(raiz_cur)
        return resultado

    if c == "vscode":
        raiz_gh = base / ".github"
        resultado["skills"] = _copiar_skills(raiz_gh / "skills")
        regla = raiz_gh / "instructions" / f"{SERVIDOR}.instructions.md"
        cab = "---\napplyTo: \"**\"\n---\n\n"
        if _copiar_reglas(regla, cabecera=cab):
            resultado["reglas"] = str(regla)
        resultado["plugin_dir"] = str(raiz_gh)
        return resultado

    if c == "opencode":
        raiz_oc = base / ".opencode"
        resultado["skills"] = _copiar_skills(raiz_oc / "skills")
        regla = raiz_oc / "AGENTS.md"
        if _copiar_reglas(regla):
            resultado["reglas"] = str(regla)
        resultado["plugin_dir"] = str(raiz_oc)
        return resultado

    resultado["modo"] = "mcp"
    return resultado


def instalar_plugin_todos(
    clientes_objetivo: Optional[List[str]] = None,
    carpeta_base: Optional[Union[str, pathlib.Path]] = None,
    global_: bool = True,
    uvx: bool = False,
) -> List[Dict[str, Any]]:
    """Instala el plugin completo en todos los harnesses detectados (o los indicados explícitamente)."""
    if clientes_objetivo is not None:
        return [
            instalar_plugin_harness(c, carpeta_base=carpeta_base, global_=global_, uvx=uvx)
            for c in clientes_objetivo
        ]

    base = (
        pathlib.Path(carpeta_base)
        if carpeta_base is not None
        else (pathlib.Path.home() if global_ else pathlib.Path.cwd())
    )
    detectados = detectar_instalados(base)
    if not detectados and not _es_casa(base):
        base = pathlib.Path.home()
        detectados = detectar_instalados(base)
    return [
        instalar_plugin_harness(c, carpeta_base=base, global_=global_, uvx=uvx)
        for c in detectados
    ]


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
    if cfg["clave"] and previo.strip():
        try:
            datos_previos = json.loads(previo)
            if isinstance(datos_previos, dict) and SERVIDOR in datos_previos.get(cfg["clave"], {}):
                return {"cliente": cfg["cliente"], "archivo": str(ruta), "estado": "ya_configurado",
                        "nota": "ya estaba configurado: no se tocó el archivo"}
        except (json.JSONDecodeError, AttributeError):
            pass
    elif not cfg["clave"] and (SERVIDOR in previo or ID_DSH in previo):
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
    elif c == "hermes" and re.search(r"(?m)^mcp_servers:\s*(?:\{\}|null|~)?\s*(?:#.*)?$", previo):
        bloque_hijo = cfg["contenido"].split("\n", 1)[1].rstrip("\n")
        nuevo = re.sub(
            r"(?m)^mcp_servers:\s*(?:\{\}|null|~)?\s*((?:#.*)?)$",
            lambda m: f"mcp_servers:{(' ' + m.group(1)) if m.group(1) else ''}\n{bloque_hijo}",
            previo,
            count=1,
        )
        ruta.write_text(nuevo, encoding="utf-8")
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
