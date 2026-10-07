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
import fnmatch
import inspect
import pathlib

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


def test_el_grafo_de_codigo_no_pierde_codigo():
    reglas = _reglas()
    assert not any(r.startswith("!") for r in reglas), "graphify no re-incluye lo que ignora .gitignore"
    excluidas = {r.rstrip("/") for r in reglas if r.endswith("/") and "*" not in r}
    for carpeta in ("servidor", "connectors", "domain", "scripts", "tests", "evals", "agents", ".claude/hooks"):
        assert carpeta not in excluidas, f"{carpeta}/ es código: no puede salir del grafo"
    assert not any(r.endswith(".py") or r in ("*", "*.*") for r in reglas), reglas
    # Ningún patrón de archivo tapa un módulo de la raíz (los que lista pyproject en py-modules).
    de_archivo = [r for r in reglas if not r.endswith("/")]
    for modulo in RAIZ.glob("*.py"):
        assert not any(fnmatch.fnmatch(modulo.name, r) for r in de_archivo), modulo.name


def test_el_grafo_de_codigo_es_local():
    lineas = (RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "graphify-out/" in lineas, "graphify-out/ se regenera local en ~9 s: no se versiona"


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
