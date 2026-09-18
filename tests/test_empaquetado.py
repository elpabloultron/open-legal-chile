"""
Empaquetado: el paquete publicado tiene que llevar el corpus y el grafo.

El wheel de 1.5.3 (y de todas las versiones anteriores) viajaba solo con los módulos: quien
hacía `pip install openlegal-chile` recibía las 64 herramientas, pero `graphify_*` respondía
"no encontrado" a cualquier tema y `doctrina_search` no tenía índice — justo las dos funciones
que justifican la suite. Nadie lo notaba porque el motor lo callaba.

Estos tests fijan la declaración que lo evita. La verificación de fondo es construir el wheel y
mirar adentro:

    uv build --wheel --out-dir /tmp/x && python -c "import zipfile,glob; \\
      z=zipfile.ZipFile(sorted(glob.glob('/tmp/x/*.whl'))[-1]); \\
      print(len([n for n in z.namelist() if n.startswith('doctrina/')]))"

(Hacerlo dentro de pytest significaría construir en cada corrida del CI; se deja como
verificación manual y queda documentado en el README.)
"""

import json
import pathlib

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def test_declara_el_corpus_y_los_datos_como_paquetes():
    tomllib = pytest.importorskip("tomllib", reason="requiere Python 3.11+")
    cfg = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    setuptools = cfg["tool"]["setuptools"]

    incluidos = setuptools["packages"]["find"]["include"]
    assert any(p.startswith("doctrina") for p in incluidos), incluidos
    assert any(p.startswith("data") for p in incluidos), incluidos
    assert setuptools["packages"]["find"].get("namespaces") is True, (
        "sin namespaces, setuptools no descubre doctrina/ ni data/ (no tienen __init__.py)"
    )
    assert setuptools["package-data"]["doctrina"] == ["**/*.md"]
    assert setuptools["package-data"]["data"] == ["**/*.json"]


def test_el_corpus_existe_y_tiene_las_obras():
    obras = list((RAIZ / "doctrina").rglob("*.md"))
    assert len(obras) >= 50, f"el corpus tiene {len(obras)} obras: el paquete iría vacío"


def test_el_grafo_existe_y_no_esta_vacio():
    grafo = RAIZ / "data" / "legal_knowledge_graph.json"
    assert grafo.exists(), "sin el grafo, graphify_* responde 'no encontrado' a todo"
    datos = json.loads(grafo.read_text(encoding="utf-8"))
    assert len(datos["nodes"]) >= 900, f"el grafo tiene {len(datos['nodes'])} nodos"
    assert "edges" in datos, "el grafo debe usar el esquema Node-Link estándar"
