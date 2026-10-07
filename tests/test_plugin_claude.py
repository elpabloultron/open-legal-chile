"""El plugin de Claude Code y su marketplace cargan todo lo que el producto promete.

Hasta 1.13.0 `claude --plugin-dir . plugin details open-legal-chile` mostraba Skills (0) y
Agents (0): las skills viven en .agents/skills/ (fuera de la ruta por defecto) y los agentes eran
JSON, que Claude Code no lee. El MCP se lanzaba con `python3 -m openlegal mcp`, que solo andaba si
el paquete ya estaba instalado en ese mismo python3. El marketplace no tenía el plugin principal.
"""

import json
import pathlib
import re

import pytest

from mcp_server import TOOLS

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PLUGIN = json.loads((RAIZ / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
MARKETPLACE = json.loads((RAIZ / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
NOMBRES = {t["name"] for t in TOOLS}


def _version_pyproject() -> str:
    texto = (RAIZ / "pyproject.toml").read_text(encoding="utf-8")
    return re.search(r'(?m)^version = "([^"]+)"', texto).group(1)


def test_el_plugin_declara_las_skills():
    rutas = PLUGIN["skills"] if isinstance(PLUGIN["skills"], list) else [PLUGIN["skills"]]
    encontradas = [d for r in rutas for d in (RAIZ / r).glob("*/SKILL.md")]
    assert len(encontradas) >= 18, rutas
    for ruta in rutas:
        assert ruta.startswith("./"), "Claude Code exige rutas relativas con ./"


def test_el_mcp_del_plugin_se_lanza_con_uvx_y_la_version_del_paquete():
    servidor = PLUGIN["mcpServers"]["open-legal-chile"]
    assert servidor["command"] == "uvx"
    assert servidor["args"] == ["--from", f"openlegal-chile=={_version_pyproject()}", "openlegal-mcp"]
    assert "${user_config.perfil}" in servidor["env"]["OPENLEGAL_PROFILE"]
    assert PLUGIN["userConfig"]["hf_token"]["sensitive"] is True


def test_todas_las_versiones_coinciden():
    version = _version_pyproject()
    assert PLUGIN["version"] == version
    server = json.loads((RAIZ / "server.json").read_text(encoding="utf-8"))
    assert server["version"] == version
    assert all(p["version"] == version for p in server["packages"])
    assert f'version="{version}"' in (RAIZ / "setup.py").read_text(encoding="utf-8")
    assert f'"version": "{version}"' in (RAIZ / "mcp_server.py").read_text(encoding="utf-8")
    assert f'CURRENT_VERSION = "{version}"' in (RAIZ / "update_checker.py").read_text(encoding="utf-8")
    gemini = RAIZ / "gemini-extension.json"
    if gemini.exists():
        datos = json.loads(gemini.read_text(encoding="utf-8"))
        assert datos["version"] == version
        assert f"openlegal-chile=={version}" in json.dumps(datos)


def test_el_marketplace_ofrece_primero_la_suite_completa():
    plugins = MARKETPLACE["plugins"]
    assert plugins[0]["name"] == "open-legal-chile" and plugins[0]["source"] == "./"
    for plugin in plugins:
        assert (RAIZ / plugin["source"]).exists(), plugin["source"]
    for plugin in plugins[1:]:
        assert plugin["dependencies"] == ["open-legal-chile"], (
            f"{plugin['name']}: una skill suelta necesita el MCP del plugin principal")


def test_el_marketplace_lista_todas_las_skills_de_dominio():
    ofrecidas = {p["name"] for p in MARKETPLACE["plugins"]}
    for carpeta in (RAIZ / ".agents" / "skills").glob("chilean-*"):
        assert carpeta.name in ofrecidas, f"falta {carpeta.name} en marketplace.json"


@pytest.mark.parametrize("archivo", sorted((RAIZ / "agents").glob("*.json")), ids=lambda p: p.stem)
def test_las_herramientas_de_cada_agente_existen(archivo):
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    desconocidas = sorted(set(datos.get("tools", [])) - NOMBRES)
    assert not desconocidas, f"{archivo.name}: herramientas inexistentes {desconocidas}"


def test_los_agentes_markdown_estan_sincronizados_con_los_json():
    from scripts.generar_agentes_plugin import agentes_markdown

    esperados = agentes_markdown()
    assert len(esperados) == len(list((RAIZ / "agents").glob("*.json")))
    for ruta, contenido in esperados.items():
        assert ruta.exists() and ruta.read_text(encoding="utf-8") == contenido, (
            f"{ruta.name} desactualizado: correr python scripts/generar_agentes_plugin.py")


def test_frontmatter_de_los_agentes_es_yaml_valido():
    yaml = pytest.importorskip("yaml")
    for ruta in sorted((RAIZ / "agents").glob("*.md")):
        texto = ruta.read_text(encoding="utf-8")
        cabecera = texto.split("---", 2)[1]
        datos = yaml.safe_load(cabecera)
        assert datos["name"] and datos["description"], ruta.name
        for herramienta in [h.strip() for h in datos.get("tools", "").split(",") if h.strip()]:
            assert herramienta.startswith("mcp__plugin_open-legal-chile_open-legal-chile__"), herramienta
            assert herramienta.rsplit("__", 1)[1] in NOMBRES, herramienta


def test_exportar_subagentes_para_proyecto_usa_el_prefijo_del_servidor(tmp_path):
    from agents_runtime import PREFIJO_MCP_PROYECTO, agent_runtime

    exportados = agent_runtime.export_subagents_config(str(tmp_path))
    assert len(exportados) >= 19
    laboral = (tmp_path / ".claude" / "agents" / "agente-laboral.md").read_text(encoding="utf-8")
    assert f"tools: {PREFIJO_MCP_PROYECTO}bcn_get_codigo" in laboral
    assert laboral.startswith("---\nname: agente-laboral\ndescription: \"")
