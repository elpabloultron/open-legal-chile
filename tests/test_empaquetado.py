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


def test_el_ocr_viaja_como_dependencia_base():
    """La instalación lleva todo: el OCR no se instala aparte («siempre se debe instalar todo»)."""
    tomllib = pytest.importorskip("tomllib", reason="requiere Python 3.11+")
    cfg = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    proyecto = cfg["project"]

    assert any("rapidocr" in dep for dep in proyecto["dependencies"]), (
        "rapidocr-onnxruntime tiene que estar en las dependencias base, no en un extra")
    assert "ocr" not in proyecto.get("optional-dependencies", {}), (
        "el extra 'ocr' dejó de existir: el OCR ya no es opcional")

    setup_py = (RAIZ / "setup.py").read_text(encoding="utf-8")
    assert "rapidocr" in setup_py, "setup.py (vía legada) también tiene que llevar el OCR"


def test_los_dominios_del_servidor_viajan_en_el_paquete():
    """servidor/ (los dominios de herramientas) tiene que viajar en el wheel: si no, el MCP
    instalado no encuentra la mitad de las herramientas."""
    tomllib = pytest.importorskip("tomllib", reason="requiere Python 3.11+")
    cfg = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    incluidos = cfg["tool"]["setuptools"]["packages"]["find"]["include"]
    assert any(p.startswith("servidor") for p in incluidos), incluidos
    assert (RAIZ / "servidor" / "corpus.py").exists()


def test_el_codigo_no_manda_a_instalar_dependencias_por_terminal():
    """El producto no le pide al usuario abrir una terminal para completar la instalación."""
    for nombre in ("forensic_ocr.py", "online_library_sync.py"):
        texto = (RAIZ / nombre).read_text(encoding="utf-8")
        assert "rapidocr-onnxruntime" not in texto, f"{nombre}: instrucción manual del OCR"
        assert "[ocr]" not in texto, f"{nombre}: el extra de OCR ya no existe"
        assert "pip install huggingface_hub" not in texto, f"{nombre}: es dependencia base"


def test_todos_los_modulos_de_la_raiz_viajan_en_el_paquete():
    """Candado: un módulo sin declarar no llega al wheel y el paquete instalado no arranca.

    Pasó en 1.7.0: la lista de módulos vivía duplicada en setup.py, sin docx_compiler, case_intake,
    diagnostico, citas_legales, integraciones_harness ni doc2md_ingestor. El MCP del paquete
    publicado no importaba (`ModuleNotFoundError: docx_compiler`) y devolvía cero herramientas.
    La lista canónica es la de pyproject.toml; acá se exige que esté completa.
    """
    tomllib = pytest.importorskip("tomllib", reason="requiere Python 3.11+")
    cfg = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    declarados = set(cfg["tool"]["setuptools"]["py-modules"])

    reales = {p.stem for p in RAIZ.glob("*.py")} - {"setup", "conftest"}
    faltan = sorted(reales - declarados)
    sobran = sorted(declarados - reales)
    assert not faltan, f"módulos que NO viajan al wheel: {faltan}"
    assert not sobran, f"declarados pero inexistentes: {sobran}"

    # Una sola fuente de verdad: setup.py no debe volver a tener su propia lista.
    setup_py = (RAIZ / "setup.py").read_text(encoding="utf-8")
    assert "py_modules=" not in setup_py, (
        "py_modules volvió a setup.py: dos listas divergentes son la falla que dejó 1.7.0 roto")

