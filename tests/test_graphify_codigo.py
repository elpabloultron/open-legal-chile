"""El grafo de CÓDIGO de graphify no se diluye en el derecho, y el grafo DOCTRINAL no vive en la
carpeta de trabajo de graphify.

Medido el 07-10-2026 sobre graphify-out/ versionado: 21.521 nodos, 68 % secciones de doctrina,
2.103 de código, y los nodos más conectados eran «Academia Judicial de Chile» (8.073 aristas) y
«doctrina48981». Con .graphifyignore, `graphify update .` arma 3.740 nodos de código en ~9 s; pero
sobre la carpeta vieja se NEGABA a escribir (el grafo «se achicaría» de 21.521 a 4.798), así que la
regla de CLAUDE.md fallaba en cada sesión. El grafo doctrinal pasó, byte a byte, a graphify-doctrinal/.
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import shutil
import subprocess

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
IGNORE = RAIZ / ".graphifyignore"


def _reglas() -> list[str]:
    return [x.strip() for x in IGNORE.read_text(encoding="utf-8").splitlines()
            if x.strip() and not x.lstrip().startswith("#")]


def test_el_grafo_de_codigo_excluye_el_corpus_juridico_y_los_datos():
    reglas = set(_reglas())
    for carpeta in ("doctrina/", "corpus_guias_aj/", "data/", "jurisprudencia_cs/", "jurisprudencia_tc/",
                    "jurisprudencia_ambiental/", "publicaciones_ambientales/", "biblioteca_ambiental/",
                    "graphify-doctrinal/", ".agents/skills/", "graphify-out/"):
        assert carpeta in reglas, f".graphifyignore debe excluir {carpeta}"


def test_el_ignore_no_saca_codigo_de_la_suite():
    """La semántica real de exclusión, no las líneas: .gitignore + .graphifyignore, como las aplica graphify.

    Comparar líneas literales no veía que `investigacion_academica/` se lleva un .py versionado. Aquí se
    usa el mismo motor de patrones que graphify (`check-ignore --no-index`, que también evalúa lo que ya
    está versionado) sobre cada .py y .sh del repositorio.
    """
    if shutil.which("git") is None or not (RAIZ / ".git").exists():
        pytest.skip("requiere git y un checkout con .git")

    def _excluidos(rutas: list[str]) -> set[str]:
        r = subprocess.run(
            ["git", "-c", f"core.excludesFile={IGNORE.as_posix()}", "check-ignore", "--no-index", "--stdin", "-z"],
            input="\0".join(rutas) + "\0", capture_output=True, text=True, encoding="utf-8", cwd=RAIZ,
            timeout=120)
        assert r.returncode in (0, 1), r.stderr  # 1 = ninguna ruta ignorada
        return {x for x in r.stdout.split("\0") if x}

    versionados = subprocess.run(["git", "ls-files", "-z", "*.py", "*.sh"], capture_output=True, text=True,
                                 encoding="utf-8", cwd=RAIZ, timeout=120)
    assert versionados.returncode == 0, versionados.stderr
    codigo = [x for x in versionados.stdout.split("\0") if x]
    assert "servidor/corpus.py" in codigo and ".claude/hooks/graphify-sesion.sh" in codigo
    assert _excluidos(codigo) == {"investigacion_academica/generar_docx_paper.py"}, (
        "el grafo de código perdería archivos de la suite; la única excepción declarada es la del paper")

    # Y el corpus sí queda fuera: lo que el grafo de código no debe diluir.
    muestras = ["doctrina/civil/x.md", "data/legal_knowledge_graph.json", ".agents/skills/a/SKILL.md",
                "docs/index.html", "corpus_guias_aj/g.md"]
    assert _excluidos(muestras) == set(muestras)
    assert not _excluidos(["servidor/corpus.py", "docs/grafo.md", "tests/test_graphify_codigo.py"])
    assert not any(r.startswith("!") for r in _reglas()), "graphify no re-incluye lo que ignora .gitignore"


def test_el_grafo_de_codigo_es_local():
    lineas = (RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "graphify-out/" in lineas, "graphify-out/ se regenera local en ~9 s: no se versiona"
    # Paridad con lo que ignoraba graphify-out/ antes del movimiento: si alguien corre graphify con
    # GRAPHIFY_OUT=graphify-doctrinal, sus subproductos tampoco se versionan.
    for regla in ("cache/", "[0-9]*/", "*.sig", ".graphify_labels.json*", "*.graphml", "cypher.txt"):
        assert f"graphify-doctrinal/{regla}" in lineas, f"falta graphify-doctrinal/{regla} en .gitignore"


def test_el_grafo_doctrinal_vive_fuera_de_graphify_out():
    import legal_graphify
    import online_library_sync

    assert pathlib.Path(online_library_sync.GRAPHIFY_DOCTRINAL_DIR).name == "graphify-doctrinal"
    defecto = inspect.signature(legal_graphify.LegalGraphifyEngine.integrar_con_graphify).parameters
    assert defecto["graphify_out_path"].default == "graphify-doctrinal/graph.json"
    for archivo in ("online_library_sync.py", "legal_graphify.py", "scripts/enrich_legal_graphify_interconnections.py"):
        arbol = ast.parse((RAIZ / archivo).read_text(encoding="utf-8"))
        rutas = [n.value for n in ast.walk(arbol) if isinstance(n, ast.Constant) and isinstance(n.value, str)
                 and "graphify-out" in n.value]
        assert not rutas, f"{archivo}: graphify-out/ es el grafo de código local; lo doctrinal va en graphify-doctrinal/"
    # Ninguna referencia viva al graph.html de la carpeta de trabajo de graphify: ahora es el grafo de
    # código local. El visualizador doctrinal es graphify-doctrinal/graph.html.
    for archivo in ("docs/index.html", "grafo_vista.py", "README.md"):
        assert "graphify-out/graph.html" not in (RAIZ / archivo).read_text(encoding="utf-8"), archivo
