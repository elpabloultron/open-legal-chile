"""Pruebas del catálogo eficiente para Hugging Face (scripts/optimizar_catalogo_hf.py).

Verifican que los artefactos publicados existan, no tengan el texto íntegro duplicado
y sostengan la cadena de citación del producto (respuesta → fuente → archivo → URL).

Si los artefactos no están presentes (p. ej. en CI, donde los pesados no se versionan),
las pruebas los generan una vez con el propio script y luego verifican el resultado.
"""

import json
import pathlib
import subprocess
import sys

import pytest

BASE = pathlib.Path(__file__).resolve().parent.parent
CATALOGO = BASE / "data" / "catalogo"


@pytest.fixture(scope="module", autouse=True)
def catalogo_generado() -> None:
    """Genera el catálogo con el script oficial cuando falta (CI)."""
    if (CATALOGO / "instituciones_lite.jsonl").exists() and (BASE / "llms.txt").exists():
        return
    subprocess.run(
        [sys.executable, str(BASE / "scripts" / "optimizar_catalogo_hf.py")],
        cwd=str(BASE),
        check=True,
        capture_output=True,
        timeout=900,
    )


def _filas(path: pathlib.Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(linea) for linea in f if linea.strip()]


def test_llms_txt_define_el_formato_de_cita():
    llms = BASE / "llms.txt"
    assert llms.exists(), "falta llms.txt (mapa del corpus para agentes)"
    texto = llms.read_text(encoding="utf-8")
    assert "[Hugging Face - " in texto, "llms.txt debe declarar el formato de cita del producto"
    assert "data/catalogo/" in texto, "llms.txt debe indicar el catálogo eficiente"


def test_version_ligera_de_instituciones_es_completa_pero_sin_contenido():
    completa = BASE / "data" / "instituciones.jsonl"
    lite = CATALOGO / "instituciones_lite.jsonl"
    if not completa.exists() or not lite.exists():
        pytest.skip("dataset no generado todavía")
    filas_full = _filas(completa)
    filas_lite = _filas(lite)
    assert len(filas_lite) == len(filas_full), "la versión ligera debe conservar todas las fichas"
    assert all("contenido" not in r for r in filas_lite[:200]), "la versión ligera no debe traer el contenido íntegro"
    assert all(r.get("ruta_hf", "").startswith("https://huggingface.co/") for r in filas_lite[:200])
    assert lite.stat().st_size < completa.stat().st_size / 3, "la versión ligera debe pesar menos de un tercio"


def test_version_ligera_de_obras_conserva_el_indice():
    lite = CATALOGO / "train_lite.jsonl"
    if not lite.exists():
        pytest.skip("dataset no generado todavía")
    filas = _filas(lite)
    assert len(filas) >= 200, "el índice debe cubrir las obras del corpus"
    assert all("texto_completo" not in r for r in filas[:50])
    assert all(r.get("ruta_hf", "").startswith("https://huggingface.co/") for r in filas[:50])


def test_indice_de_citas_cubre_doctrina_y_guias():
    indice = CATALOGO / "indice_citas.jsonl"
    if not indice.exists():
        pytest.skip("dataset no generado todavía")
    filas = _filas(indice)
    archivos = {r["archivo"] for r in filas}
    assert len(filas) >= 240, "debe cubrir doctrina + guías"
    assert any(a.startswith("doctrina/") for a in archivos)
    assert any(a.startswith("guias_academia_judicial/") for a in archivos)
    con_secciones = [r for r in filas if r.get("secciones")]
    assert len(con_secciones) >= len(filas) * 0.9, "casi todos los documentos deben exponer sus secciones"
    assert all(r.get("url", "").startswith("https://huggingface.co/") for r in filas[:50])


def test_enlaces_guias_corpus_estan_poblados():
    enlaces = BASE / "data" / "enlaces_guias_corpus.json"
    if not enlaces.exists():
        pytest.skip("enlaces no generados todavía")
    datos = json.loads(enlaces.read_text(encoding="utf-8"))
    assert datos["guias"] >= 20
    assert datos["claves_de_norma_en_el_corpus"] > 500, "las claves de norma deben salir del corpus real"
    assert datos["enlaces"], "el archivo existía con 0 enlaces: la reparación debe poblarlo"
    assert sum(1 for v in datos["enlaces"].values() if v) >= 15, "al menos 15 guías deben quedar enlazadas"


def test_indice_de_agentes_ofrece_rutas_y_cita():
    indice = CATALOGO / "indice_agentes.json"
    if not indice.exists():
        pytest.skip("dataset no generado todavía")
    datos = json.loads(indice.read_text(encoding="utf-8"))
    assert datos["rutas"], "el índice debe ofrecer rutas «tema → archivo»"
    assert datos["como_citar"]["formato"].startswith("[Hugging Face - ")
    assert datos["archivos_clave"]["fichas_lite"].endswith("instituciones_lite.jsonl")


def test_el_publicador_ya_no_sube_los_artefactos_pesados():
    """graphify/ en Hugging Face conserva solo la wiki y el informe (los dumps viven en data/)."""
    fuente = (BASE / "online_library_sync.py").read_text(encoding="utf-8")
    bloque = fuente.split("def preparar_artefactos_graphify", 1)[1].split("def ", 1)[0]
    for pesado in ("graph.graphml", "cypher.txt", "GRAPH_TREE.html", ".graphify_analysis.json"):
        assert pesado not in bloque, f"{pesado} no debe volver a publicarse en graphify/"
    assert "wiki" in bloque and "GRAPH_REPORT.md" in bloque
