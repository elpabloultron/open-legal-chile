"""graphify en las sesiones en la nube: se instala fijado, construye el grafo de código sin
retener el arranque, nunca hace fallar la sesión y su guardia no empuja al grafo de código a quien
estudia doctrina.

Hasta 1.13.0 CLAUDE.md exigía `graphify query` y `graphify update .`, pero graphify no estaba
instalado en ninguna sesión (los hooks PreToolUse quedaban mudos) y, ya instalado, `hook-guard`
respondía «MANDATORY: You MUST run graphify» incluso al leer doctrina/README.md.
Las pruebas usan dobles de `uv` y `graphify` en tmp_path: sin red y sin tocar el repositorio.
La decisión de alcance de la guardia (qué carpetas calla) se prueba en tests/test_graphify_alcance.py,
que corre también en Windows; aquí se prueba el envoltorio bash y la sesión.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
HOOKS = RAIZ / ".claude" / "hooks"
SESION = HOOKS / "graphify-sesion.sh"
GUARDIA = HOOKS / "graphify-guardia.sh"

pytestmark = pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("bash") is None,
    reason="los hooks de Claude Code en la nube son bash sobre Linux",
)

_HERRAMIENTAS = ("bash", "sh", "cat", "grep", "head", "mkdir", "rm", "timeout", "sleep",
                 "setsid", "nohup", "dirname", "basename", "cp", "chmod", "env")

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
  [ -n "${DOBLE_UV_LENTO:-}" ] && sleep "$DOBLE_UV_LENTO"
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
    # La guardia delega el alcance en graphify_alcance.py: necesita un Python, que no es del sistema
    # aislado sino el del intérprete que corre pytest.
    (sistema / "python3").symlink_to(sys.executable)
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
    # El trabajo desacoplado deja la causa en el log de la sesión (la sesión misma no imprime nada).
    log = (entorno["proyecto"] / "graphify-out" / ".sesion.log").read_text(encoding="utf-8")
    assert "uv tool install falló" in log


def test_es_idempotente_y_no_duplica_el_path(entorno):
    for _ in range(2):
        assert _correr(SESION, entorno["env"]).returncode == 0
    lineas = [x for x in entorno["env_file"].read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(lineas) == 1, lineas
    assert _llamadas(entorno).count("tool install") == 1


def test_no_imprime_nada_en_el_stdout_del_hook(entorno):
    # Claude Code agrega el stdout de un hook SessionStart al contexto de la sesión.
    r = _correr(SESION, entorno["env"])
    assert r.returncode == 0 and r.stdout == ""


def test_funciona_con_ruta_relativa_desde_otro_directorio(entorno):
    # Con CLAUDE_PROJECT_DIR definido, el script cambia de directorio: su propia ruta (para relanzarse
    # en modo --trabajo) se calcula antes. Con `$0` relativo y el cd hecho, el trabajo no arrancaba.
    r = subprocess.run(["bash", "./graphify-sesion.sh"], env=entorno["env"], cwd=HOOKS, text=True,
                       encoding="utf-8", capture_output=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert (entorno["proyecto"] / "graphify-out" / "graph.json").exists()


@pytest.mark.skipif(shutil.which("setsid") is None or shutil.which("nohup") is None,
                    reason="el desacople usa nohup y setsid")
def test_no_retiene_la_sesion_mientras_instala_y_construye(entorno):
    # Sin OPENLEGAL_GRAPHIFY_ESPERAR: la rama real. Un uv que tarda 3 s en instalar no puede retener el
    # arranque. Con capture_output=True, subprocess.run espera el cierre de los pipes: si el proceso
    # desacoplado los heredara, devolvería recién a los ~3 s y Claude Code esperaría al grafo.
    env = {k: v for k, v in entorno["env"].items() if k != "OPENLEGAL_GRAPHIFY_ESPERAR"}
    env["DOBLE_UV_LENTO"] = "3"
    inicio = time.monotonic()
    r = _correr(SESION, env)
    demora = time.monotonic() - inicio
    assert r.returncode == 0, r.stderr
    assert demora < 1.5, f"el hook retuvo la sesión {demora:.2f} s"
    assert r.stdout == ""
    grafo = entorno["proyecto"] / "graphify-out" / "graph.json"
    assert not grafo.exists(), "el grafo se construye después, ya desacoplado"
    limite = time.monotonic() + 15
    while not grafo.exists() and time.monotonic() < limite:
        time.sleep(0.1)
    assert grafo.exists(), "el proceso desacoplado no llegó a construir el grafo"


def test_la_sesion_reinicia_las_marcas_de_aviso(entorno):
    marca = entorno["proyecto"] / "graphify-out" / ".guardia" / "x-read"
    marca.parent.mkdir(parents=True)
    marca.touch()
    assert _correr(SESION, entorno["env"]).returncode == 0
    assert not marca.parent.exists(), "SessionStart (incluido compact/clear) debe volver a permitir el aviso"


@pytest.fixture
def guardia(entorno):
    """Guardia lista: graphify doble en el PATH y un graph.json (sin él la guardia sale temprano)."""
    shutil.copy(entorno["env"]["DOBLE_GRAPHIFY"], entorno["dobles"] / "graphify")
    grafo = entorno["proyecto"] / "graphify-out"
    grafo.mkdir()
    (grafo / "graph.json").write_text('{"nodes": []}', encoding="utf-8")
    return entorno


def _evento(herramienta, sesion="s1", **campos):
    return json.dumps({"session_id": sesion, "tool_name": herramienta, "tool_input": campos})


@pytest.mark.parametrize("herramienta,tipo,campos", [
    pytest.param("Read", "read", {"file_path": "{P}/doctrina/civil/orrego/teoria_general_del_contrato.md"},
                 id="read_doctrina"),
    pytest.param("Read", "read", {"file_path": "{P}/data/legal_knowledge_graph.json"}, id="read_data"),
    pytest.param("Read", "read", {"file_path": "{P}/.agents/skills/chilean-case-intake/SKILL.md"}, id="skills"),
    pytest.param("Grep", "search", {"pattern": "compraventa", "path": "{P}/doctrina"}, id="grep_path_sin_barra"),
    pytest.param("Glob", "read", {"pattern": "*.md", "path": "{P}/corpus_guias_aj"}, id="glob_path"),
    pytest.param("Bash", "search", {"command": "rg -n compraventa doctrina"}, id="bash_rg"),
    pytest.param("Read", "read", {"file_path": "doctrina\\civil\\a.md"}, id="windows"),
])
def test_la_guardia_calla_en_el_corpus_juridico(guardia, herramienta, tipo, campos):
    campos = {k: v.replace("{P}", str(guardia["proyecto"])) for k, v in campos.items()}
    r = _correr(GUARDIA, guardia["env"], tipo, entrada=_evento(herramienta, **campos))
    assert r.returncode == 0 and r.stdout == ""
    assert "hook-guard" not in _llamadas(guardia)


@pytest.mark.parametrize("tipo,herramienta,campos", [
    ("read", "Read", {"file_path": "servidor/corpus.py"}),
    ("search", "Bash", {"command": "grep -rn ORDEN_ORIGEN mcp_server.py"}),
])
def test_la_guardia_deja_pasar_el_codigo(guardia, tipo, herramienta, campos):
    r = _correr(GUARDIA, guardia["env"], tipo, entrada=_evento(herramienta, **campos))
    assert r.returncode == 0
    assert json.loads(r.stdout) == {"guardia": tipo}


def test_la_guardia_avisa_una_vez_por_sesion(guardia):
    codigo = _evento("Read", sesion="s1", file_path="servidor/corpus.py")
    primero = _correr(GUARDIA, guardia["env"], "read", entrada=codigo)
    assert json.loads(primero.stdout) == {"guardia": "read"}
    segundo = _correr(GUARDIA, guardia["env"], "read", entrada=codigo)
    assert segundo.returncode == 0 and segundo.stdout == ""
    otra = _correr(GUARDIA, guardia["env"], "read", entrada=_evento("Read", "s2", file_path="servidor/corpus.py"))
    assert json.loads(otra.stdout) == {"guardia": "read"}


def test_un_comando_sin_aviso_no_consume_el_aviso_de_la_sesion(guardia):
    # La marca se crea solo si graphify avisó: si no hubo aviso, el siguiente Grep todavía lo recibe.
    (guardia["dobles"] / "graphify").write_text("#!/bin/sh\ncat > /dev/null\nexit 0\n", encoding="utf-8")
    sin_aviso = _correr(GUARDIA, guardia["env"], "search", entrada=_evento("Bash", command="ls servidor"))
    assert sin_aviso.stdout == ""
    assert not (guardia["proyecto"] / "graphify-out" / ".guardia").exists()


def test_la_guardia_sin_grafo_no_llama_a_graphify(entorno):
    shutil.copy(entorno["env"]["DOBLE_GRAPHIFY"], entorno["dobles"] / "graphify")
    r = _correr(GUARDIA, entorno["env"], "read", entrada=_evento("Read", file_path="servidor/corpus.py"))
    assert r.returncode == 0 and r.stdout == ""
    assert "hook-guard" not in _llamadas(entorno)


def test_la_guardia_sin_python_falla_abierta(guardia):
    (guardia["sistema"] / "python3").unlink()
    r = _correr(GUARDIA, guardia["env"], "read", entrada=_evento("Read", file_path="servidor/corpus.py"))
    assert r.returncode == 0 and r.stdout == ""


def test_la_guardia_sin_graphify_no_dice_nada(entorno):
    env = dict(entorno["env"], PATH=str(entorno["sistema"]))
    r = _correr(GUARDIA, env, "read", entrada='{"tool_input": {"file_path": "mcp_server.py"}}')
    assert r.returncode == 0 and r.stdout == ""


def test_los_hooks_de_graphify_son_tolerantes():
    settings = json.loads((RAIZ / ".claude" / "settings.json").read_text(encoding="utf-8"))
    comandos = [h["command"] for grupo in settings["hooks"]["PreToolUse"] for h in grupo["hooks"]]
    # Solo los de graphify: un hook futuro sin relación con graphify no debe romper esta prueba.
    de_graphify = [c for c in comandos if "graphify" in c]
    assert de_graphify, "debe haber al menos un hook PreToolUse de graphify"
    for comando in de_graphify:
        assert "graphify-guardia.sh" in comando and comando.rstrip().endswith("|| true"), comando
    inicio = (HOOKS / "session-start.sh").read_text(encoding="utf-8")
    assert re.search(r'graphify-sesion\.sh"?\s*\|\|\s*true', inicio), "graphify no puede cortar el arranque"
    # La carpeta de los hooks se calcula antes del cd: con una ruta relativa, después apuntaría mal.
    lineas = [x.strip() for x in inicio.splitlines() if x.strip() and not x.strip().startswith("#")]
    pos_hooks = next(i for i, x in enumerate(lineas) if x.startswith("HOOKS_DIR="))
    pos_cd = next(i for i, x in enumerate(lineas) if x.startswith("cd "))
    assert pos_hooks < pos_cd
    assert '"$HOOKS_DIR/graphify-sesion.sh"' in inicio


def test_la_version_fijada_es_la_documentada():
    version = _version_fijada()
    for doc in ("CLAUDE.md", ".agents/rules/graphify.md", ".cursor/rules/graphify.mdc"):
        assert f"graphifyy=={version}" in (RAIZ / doc).read_text(encoding="utf-8"), doc
