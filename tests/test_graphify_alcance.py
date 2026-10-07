"""Alcance de la guardia de graphify: ¿la llamada cae dentro del grafo de CÓDIGO o en el corpus?

Python puro, sin subprocess ni bash: corre igual en Linux, macOS y Windows (la parte bash de la
guardia se prueba en tests/test_graphify_sesion.py y se omite en win32).

Medido el 07-10-2026 con graphify 0.9.79: la primera versión de la guardia (grep sobre el JSON
completo, con `(^|["/ ])carpeta/`) no callaba con Grep{path: '<raíz>/doctrina'}, Grep{path:
'doctrina'}, Glob{path: '<raíz>/corpus_guias_aj'} ni `rg -n x doctrina`, y se callaba ante un
comando de código cuya `description` nombraba `data/`. Las pruebas de ahí solo usaban Read de un
archivo dentro de la carpeta, la única forma que funcionaba.
"""
from __future__ import annotations

import importlib.util
import io
import json
import pathlib
import shutil

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
MODULO = RAIZ / ".claude" / "hooks" / "graphify_alcance.py"

_spec = importlib.util.spec_from_file_location("graphify_alcance", MODULO)
assert _spec is not None and _spec.loader is not None
alcance = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(alcance)

CARPETAS = alcance.carpetas_excluidas((RAIZ / ".graphifyignore").read_text(encoding="utf-8"))
PROYECTO = "/work/proyecto"


def test_las_carpetas_salen_de_graphifyignore():
    for carpeta in ("doctrina", "data", "corpus_guias_aj", ".agents/skills", "graphify-doctrinal"):
        assert carpeta in CARPETAS, carpeta
    for codigo in ("servidor", "tests", ".claude/hooks", "connectors"):
        assert codigo not in CARPETAS, f"{codigo}/ es código: no puede quedar fuera del grafo"
    # Solo reglas de carpeta: ni comentarios, ni comodines, ni archivos sueltos.
    assert all("*" not in c and not c.startswith("#") and not c.endswith("/") for c in CARPETAS)


@pytest.mark.parametrize("entrada", [
    pytest.param({"tool_name": "Read", "tool_input": {"file_path": f"{PROYECTO}/doctrina/civil/a.md"}},
                 id="read_archivo"),
    pytest.param({"tool_name": "Grep", "tool_input": {"pattern": "compraventa", "path": f"{PROYECTO}/doctrina"}},
                 id="grep_carpeta_absoluta_sin_barra"),
    pytest.param({"tool_name": "Grep", "tool_input": {"pattern": "x", "path": "corpus_guias_aj"}},
                 id="grep_carpeta_relativa"),
    pytest.param({"tool_name": "Glob", "tool_input": {"pattern": "*.md", "path": f"{PROYECTO}/data"}},
                 id="glob_path"),
    pytest.param({"tool_name": "Glob", "tool_input": {"pattern": "doctrina/**/*.md"}}, id="glob_pattern"),
    pytest.param({"tool_name": "Bash", "tool_input": {"command": "rg -n compraventa doctrina"}},
                 id="bash_rg_carpeta"),
    pytest.param({"tool_name": "Read", "tool_input": {"file_path": ".agents/skills/x/SKILL.md"}}, id="skills"),
    pytest.param({"tool_name": "Grep", "tool_input": {"pattern": "x", "path": "./doctrina/"}}, id="barra_final"),
    pytest.param({"tool_name": "Read", "tool_input": {"file_path": "servidor/../doctrina/a.md"}}, id="con_punto_punto"),
    # Ruta de Windows dentro de un comando de Bash (Git Bash la recibe con `\\`).
    pytest.param({"tool_name": "Bash", "tool_input": {"command": "type doctrina\\civil\\a.md"}},
                 id="bash_ruta_windows"),
])
def test_el_corpus_queda_fuera(entrada):
    assert alcance.fuera_del_grafo(entrada, PROYECTO, CARPETAS) is True


def test_rutas_estilo_windows():
    carpeta = {"tool_name": "Read", "tool_input": {"file_path": "C:\\proj\\doctrina\\a.md"}}
    assert alcance.fuera_del_grafo(carpeta, "C:\\proj", CARPETAS) is True
    codigo = {"tool_name": "Read", "tool_input": {"file_path": "C:\\proj\\servidor\\corpus.py"}}
    assert alcance.fuera_del_grafo(codigo, "C:\\proj", CARPETAS) is False
    # Grep sobre la carpeta, sin barra final, con separadores de Windows.
    grep = {"tool_name": "Grep", "tool_input": {"pattern": "x", "path": "C:\\proj\\doctrina"}}
    assert alcance.fuera_del_grafo(grep, "C:\\proj", CARPETAS) is True
    relativa = {"tool_name": "Glob", "tool_input": {"pattern": "data\\**\\*.json"}}
    assert alcance.fuera_del_grafo(relativa, "C:\\proj", CARPETAS) is True


def test_windows_no_distingue_mayusculas(monkeypatch):
    # NTFS no distingue mayúsculas: el Explorador puede dar `c:\\Proj\\Doctrina\\a.md`. Solo se simula
    # `os.name` (las funciones comparan textos, sin tocar el disco), para cubrirlo también en Linux.
    entrada = {"tool_name": "Read", "tool_input": {"file_path": "c:\\PROJ\\Doctrina\\a.md"}}
    monkeypatch.setattr(alcance.os, "name", "nt")
    assert alcance.fuera_del_grafo(entrada, "C:\\proj", CARPETAS) is True
    monkeypatch.setattr(alcance.os, "name", "posix")
    assert alcance.fuera_del_grafo(entrada, "C:\\proj", CARPETAS) is False


@pytest.mark.parametrize("entrada", [
    pytest.param({"tool_name": "Read", "tool_input": {"file_path": "servidor/corpus.py"}}, id="read_codigo"),
    pytest.param({"tool_name": "Read", "tool_input": {"file_path": ".claude/hooks/graphify-sesion.sh"}},
                 id="read_hook"),
    pytest.param({"tool_name": "Bash", "tool_input": {"command": "grep -rn ORDEN_ORIGEN mcp_server.py"}},
                 id="bash_codigo"),
    # El pattern de Grep es una regex: nombrar «data» ahí no es una ruta.
    pytest.param({"tool_name": "Grep", "tool_input": {"pattern": "data", "path": "servidor"}}, id="grep_pattern"),
    # La descripción no cuenta: antes un comando de código quedaba mudo por lo que decía su descripción.
    pytest.param({"tool_name": "Bash", "tool_input": {"description": "Buscar casos en doctrina/",
                                                      "command": "grep -rn x servidor/"}}, id="descripcion"),
    pytest.param({"tool_name": "Grep", "tool_input": {"pattern": "x", "path": f"{PROYECTO}/servidor"}},
                 id="grep_carpeta_de_codigo"),
    # Una carpeta de código que solo empieza igual que una excluida no es la excluida.
    pytest.param({"tool_name": "Read", "tool_input": {"file_path": "datos_de_prueba/a.py"}}, id="prefijo_parcial"),
    # Mutación comprobada: con `startswith(carpeta)` sin la barra, «database/» caía dentro de «data/».
    pytest.param({"tool_name": "Read", "tool_input": {"file_path": "database/a.py"}}, id="prefijo_database"),
    pytest.param({"tool_name": "Grep", "tool_input": {"pattern": "x", "path": f"{PROYECTO}/doctrina_x"}},
                 id="prefijo_doctrina_x"),
    pytest.param({"tool_name": "Read", "tool_input": "no-es-un-dict"}, id="tool_input_invalido"),
])
def test_el_codigo_queda_dentro(entrada):
    assert alcance.fuera_del_grafo(entrada, PROYECTO, CARPETAS) is False


def test_sin_carpetas_nada_queda_fuera():
    entrada = {"tool_name": "Read", "tool_input": {"file_path": "doctrina/a.md"}}
    assert alcance.fuera_del_grafo(entrada, PROYECTO, []) is False


def _correr(monkeypatch, capsys, proyecto, entrada, tipo="read"):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(proyecto))
    monkeypatch.setattr("sys.stdin", io.StringIO(entrada if isinstance(entrada, str) else json.dumps(entrada)))
    codigo = alcance.main([tipo])
    return codigo, capsys.readouterr().out.strip()


def test_avisa_una_vez_por_sesion(monkeypatch, capsys, tmp_path):
    shutil.copy(RAIZ / ".graphifyignore", tmp_path / ".graphifyignore")
    entrada = {"session_id": "s1", "tool_name": "Read", "tool_input": {"file_path": "servidor/corpus.py"}}
    marca = tmp_path / "graphify-out" / ".guardia" / "s1-read"

    codigo, salida = _correr(monkeypatch, capsys, tmp_path, entrada)
    assert codigo == 1
    assert pathlib.Path(salida) == marca

    # La marca la crea la guardia (bash) solo si graphify avisó; aquí se simula.
    marca.parent.mkdir(parents=True)
    marca.touch()
    assert _correr(monkeypatch, capsys, tmp_path, entrada)[0] == 0
    # Otro tipo de herramienta en la misma sesión sí avisa: es una marca por tipo.
    assert _correr(monkeypatch, capsys, tmp_path, entrada, tipo="search")[0] == 1
    # Otra sesión vuelve a avisar.
    otra = dict(entrada, session_id="s2")
    assert _correr(monkeypatch, capsys, tmp_path, otra)[0] == 1


def test_sin_session_id_avisa_pero_no_marca(monkeypatch, capsys, tmp_path):
    shutil.copy(RAIZ / ".graphifyignore", tmp_path / ".graphifyignore")
    entrada = {"tool_name": "Read", "tool_input": {"file_path": "servidor/corpus.py"}}
    assert _correr(monkeypatch, capsys, tmp_path, entrada) == (1, "")


def test_el_session_id_se_sanea(tmp_path):
    marca = alcance.ruta_de_marca({"session_id": "../../etc/x y"}, "read", str(tmp_path))
    assert marca is not None and marca.parent == tmp_path / "graphify-out" / ".guardia"
    assert marca.name == "etcxy-read"
    assert alcance.ruta_de_marca({"session_id": "///"}, "read", str(tmp_path)) is None


def test_el_corpus_no_avisa_ni_marca(monkeypatch, capsys, tmp_path):
    shutil.copy(RAIZ / ".graphifyignore", tmp_path / ".graphifyignore")
    entrada = {"session_id": "s1", "tool_name": "Grep", "tool_input": {"pattern": "x", "path": "doctrina"}}
    assert _correr(monkeypatch, capsys, tmp_path, entrada, tipo="search") == (0, "")


@pytest.mark.parametrize("basura", ["no-json", "[1, 2]", ""])
def test_json_invalido_falla_abierta(monkeypatch, capsys, tmp_path, basura):
    assert _correr(monkeypatch, capsys, tmp_path, basura)[0] == 2


def test_stdin_en_utf8_aunque_la_pagina_de_codigos_sea_otra(monkeypatch, capsys, tmp_path):
    # En Windows el stdin de texto usaría cp1252: la guardia lee los bytes y decodifica en UTF-8.
    shutil.copy(RAIZ / ".graphifyignore", tmp_path / ".graphifyignore")
    cuerpo = json.dumps({"session_id": "añ1", "tool_name": "Bash",
                         "tool_input": {"command": "grep -rn 'compraventa ñandú' servidor/"}},
                        ensure_ascii=False).encode("utf-8")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(cuerpo), encoding="cp1252"))
    assert alcance.main(["search"]) == 1
    assert pathlib.Path(capsys.readouterr().out.strip()).name == "a1-search"
