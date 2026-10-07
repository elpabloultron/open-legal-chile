"""graphify en las sesiones en la nube: se instala fijado, construye el grafo de código sin
bloquear, nunca hace fallar la sesión y su guardia no empuja al grafo de código a quien estudia
doctrina.

Hasta 1.13.1 CLAUDE.md exigía `graphify query` y `graphify update .`, pero graphify no estaba
instalado en ninguna sesión (los hooks PreToolUse quedaban mudos) y, ya instalado, `hook-guard`
respondía «MANDATORY: You MUST run graphify» incluso al leer doctrina/README.md.
Las pruebas usan dobles de `uv` y `graphify` en tmp_path: sin red y sin tocar el repositorio.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
HOOKS = RAIZ / ".claude" / "hooks"
SESION = HOOKS / "graphify-sesion.sh"
GUARDIA = HOOKS / "graphify-guardia.sh"

pytestmark = pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("bash") is None,
    reason="los hooks de Claude Code en la nube son bash sobre Linux",
)

_HERRAMIENTAS = ("bash", "sh", "cat", "grep", "sed", "paste", "head", "mkdir", "timeout",
                 "setsid", "nohup", "dirname", "cp", "chmod", "env")

_GRAPHIFY_DOBLE = """#!/bin/sh
echo "graphify $*" >> "$DOBLE_LOG"
case "$1" in
  --version) [ -f "$DOBLE_VERSION" ] && cat "$DOBLE_VERSION" ;;
  hook-guard) cat > /dev/null; echo '{"guardia":"'"$2"'"}' ;;
  update) mkdir -p graphify-out && echo '{"nodes":[]}' > graphify-out/graph.json ;;
esac
exit 0
"""

_UV_DOBLE = """#!/bin/sh
echo "uv $*" >> "$DOBLE_LOG"
if [ "$1 $2" = "tool install" ]; then
  [ -n "${DOBLE_UV_FALLA:-}" ] && exit 1
  for a in "$@"; do case "$a" in graphifyy==*) echo "graphify ${a#graphifyy==}" > "$DOBLE_VERSION" ;; esac; done
  cp "$DOBLE_GRAPHIFY" "$DOBLE_TOOLBIN/graphify" && chmod +x "$DOBLE_TOOLBIN/graphify"
elif [ "$1 $2" = "tool dir" ]; then
  echo "$DOBLE_TOOLBIN"
fi
exit 0
"""


def _version_fijada() -> str:
    m = re.search(r'^GRAPHIFY_VERSION="([^"]+)"', SESION.read_text(encoding="utf-8"), re.M)
    assert m, "graphify-sesion.sh debe fijar GRAPHIFY_VERSION"
    return m.group(1)


@pytest.fixture
def entorno(tmp_path):
    """Proyecto vacío, herramientas del sistema aisladas y dobles de uv/graphify."""
    sistema = tmp_path / "sistema"
    sistema.mkdir()
    for nombre in _HERRAMIENTAS:
        real = shutil.which(nombre)
        if real:
            (sistema / nombre).symlink_to(real)
    dobles = tmp_path / "dobles"
    toolbin = tmp_path / "toolbin"
    dobles.mkdir()
    toolbin.mkdir()
    graphify = tmp_path / "graphify_doble"
    graphify.write_text(_GRAPHIFY_DOBLE, encoding="utf-8")
    graphify.chmod(0o755)
    (dobles / "uv").write_text(_UV_DOBLE, encoding="utf-8")
    (dobles / "uv").chmod(0o755)
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    shutil.copy(RAIZ / ".graphifyignore", proyecto / ".graphifyignore")
    env_file = tmp_path / "claude_env.sh"
    env_file.touch()
    env = {
        "PATH": f"{dobles}{os.pathsep}{sistema}",
        "HOME": str(tmp_path),
        "CLAUDE_PROJECT_DIR": str(proyecto),
        "CLAUDE_ENV_FILE": str(env_file),
        "OPENLEGAL_GRAPHIFY_ESPERAR": "1",
        "DOBLE_LOG": str(tmp_path / "llamadas.log"),
        "DOBLE_VERSION": str(tmp_path / "version.txt"),
        "DOBLE_TOOLBIN": str(toolbin),
        "DOBLE_GRAPHIFY": str(graphify),
    }
    return {"env": env, "tmp": tmp_path, "proyecto": proyecto, "sistema": sistema,
            "toolbin": toolbin, "dobles": dobles, "env_file": env_file}


def _correr(script, env, *args, entrada=""):
    return subprocess.run(["bash", str(script), *args], env=env, input=entrada, text=True, encoding="utf-8",
                          capture_output=True, timeout=60)


def _llamadas(e) -> str:
    log = pathlib.Path(e["env"]["DOBLE_LOG"])
    return log.read_text(encoding="utf-8") if log.exists() else ""


def test_instala_la_version_fijada_y_construye_el_grafo(entorno):
    r = _correr(SESION, entorno["env"])
    assert r.returncode == 0, r.stderr
    llamadas = _llamadas(entorno)
    assert f"uv tool install --quiet graphifyy=={_version_fijada()}" in llamadas
    assert "graphify update ." in llamadas
    assert (entorno["proyecto"] / "graphify-out" / "graph.json").exists()
    # uv dejó graphify fuera del PATH: la sesión lo recibe por CLAUDE_ENV_FILE.
    assert str(entorno["toolbin"]) in entorno["env_file"].read_text(encoding="utf-8")


def test_no_reinstala_si_la_version_ya_esta(entorno):
    shutil.copy(entorno["env"]["DOBLE_GRAPHIFY"], entorno["toolbin"] / "graphify")
    pathlib.Path(entorno["env"]["DOBLE_VERSION"]).write_text(f"graphify {_version_fijada()}\n", encoding="utf-8")
    env = dict(entorno["env"], PATH=f"{entorno['toolbin']}{os.pathsep}{entorno['env']['PATH']}")
    r = _correr(SESION, env)
    assert r.returncode == 0, r.stderr
    assert "tool install" not in _llamadas(entorno)
    assert entorno["env_file"].read_text(encoding="utf-8") == "", "ya estaba en el PATH"


def test_sin_uv_ni_graphify_la_sesion_sigue(entorno):
    env = dict(entorno["env"], PATH=str(entorno["sistema"]))
    r = _correr(SESION, env)
    assert r.returncode == 0
    assert "no quedó instalado" in r.stderr
    assert not (entorno["proyecto"] / "graphify-out").exists()


def test_si_uv_falla_la_sesion_sigue(entorno):
    env = dict(entorno["env"], DOBLE_UV_FALLA="1")
    r = _correr(SESION, env)
    assert r.returncode == 0
    assert "graphify update" not in _llamadas(entorno)


def test_es_idempotente_y_no_duplica_el_path(entorno):
    for _ in range(2):
        assert _correr(SESION, entorno["env"]).returncode == 0
    lineas = [x for x in entorno["env_file"].read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(lineas) == 1, lineas
    assert _llamadas(entorno).count("tool install") == 1


@pytest.mark.parametrize("ruta", [
    "doctrina/civil/orrego/teoria_general_del_contrato.md",
    "data/legal_knowledge_graph.json",
    "corpus_guias_aj/Guia_Audiencia_Monitoria-v1.md",
    ".agents/skills/chilean-case-intake/SKILL.md",
])
def test_la_guardia_calla_en_el_corpus_juridico(entorno, ruta):
    shutil.copy(entorno["env"]["DOBLE_GRAPHIFY"], entorno["dobles"] / "graphify")
    entrada = json.dumps({"tool_name": "Read", "tool_input": {"file_path": f"{entorno['proyecto']}/{ruta}"}})
    r = _correr(GUARDIA, entorno["env"], "read", entrada=entrada)
    assert r.returncode == 0 and r.stdout == ""
    assert "hook-guard" not in _llamadas(entorno)


@pytest.mark.parametrize("tipo,entrada", [
    ("read", {"tool_name": "Read", "tool_input": {"file_path": "servidor/corpus.py"}}),
    ("search", {"tool_name": "Bash", "tool_input": {"command": "grep -rn ORDEN_ORIGEN mcp_server.py"}}),
])
def test_la_guardia_deja_pasar_el_codigo(entorno, tipo, entrada):
    shutil.copy(entorno["env"]["DOBLE_GRAPHIFY"], entorno["dobles"] / "graphify")
    r = _correr(GUARDIA, entorno["env"], tipo, entrada=json.dumps(entrada))
    assert r.returncode == 0
    assert json.loads(r.stdout) == {"guardia": tipo}


def test_la_guardia_sin_graphify_no_dice_nada(entorno):
    env = dict(entorno["env"], PATH=str(entorno["sistema"]))
    r = _correr(GUARDIA, env, "read", entrada='{"tool_input": {"file_path": "mcp_server.py"}}')
    assert r.returncode == 0 and r.stdout == ""


def test_los_hooks_registrados_son_tolerantes():
    settings = json.loads((RAIZ / ".claude" / "settings.json").read_text(encoding="utf-8"))
    comandos = [h["command"] for grupo in settings["hooks"]["PreToolUse"] for h in grupo["hooks"]]
    assert comandos and all("graphify-guardia.sh" in c and c.rstrip().endswith("|| true") for c in comandos)
    inicio = (HOOKS / "session-start.sh").read_text(encoding="utf-8")
    assert re.search(r'graphify-sesion\.sh"?\s*\|\|\s*true', inicio), "graphify no puede cortar el arranque"


def test_la_version_fijada_es_la_documentada():
    version = _version_fijada()
    for doc in ("CLAUDE.md", ".agents/rules/graphify.md", ".cursor/rules/graphify.mdc"):
        assert f"graphifyy=={version}" in (RAIZ / doc).read_text(encoding="utf-8"), doc
