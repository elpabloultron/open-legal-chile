"""Pruebas de los textos íntegros nuevos y de su integración al grafo jurídico.

- Sentencias del Tribunal Constitucional (últimos 2 años) en `jurisprudencia_tc/`.
- Anuarios y boletines ambientales en `publicaciones_ambientales/`.
- Nodos y aristas nuevas en `data/legal_knowledge_graph.json`.
- Separación del dataset de entrenamiento en el publicador.

Los textos pesados no se versionan: cuando faltan (CI), las pruebas que dependen de
los archivos se saltan solas; el grafo y los índices sí se versionan y siempre se verifican.
"""

import json
import pathlib

import pytest

BASE = pathlib.Path(__file__).resolve().parent.parent
GRAFO = BASE / "data" / "legal_knowledge_graph.json"
TC_INDICE = BASE / "data" / "jurisprudencia" / "tc_textos.jsonl"
PUB_INDICE = BASE / "data" / "jurisprudencia" / "publicaciones_textos.jsonl"


def _filas(ruta: pathlib.Path) -> list[dict]:
    with open(ruta, encoding="utf-8") as f:
        return [json.loads(linea) for linea in f if linea.strip()]


def test_indice_tc_cubre_las_sentencias():
    assert TC_INDICE.exists(), "falta el índice de textos del TC"
    filas = _filas(TC_INDICE)
    assert len(filas) >= 950, "el índice debe cubrir las sentencias del TC de los últimos 2 años"
    assert all(r["archivo_md"].startswith("jurisprudencia_tc/") for r in filas[:100])
    assert all((r.get("caracteres") or 0) > 200 for r in filas[:100]), "cada sentencia debe traer texto"
    faltantes = [r["archivo_md"] for r in filas if not (BASE / r["archivo_md"]).exists()]
    if faltantes and len(faltantes) == len(filas):
        pytest.skip("textos del TC no presentes en este entorno (no versionados)")


def test_indice_publicaciones_cubre_los_anuarios_y_boletines():
    assert PUB_INDICE.exists(), "falta el índice de publicaciones ambientales"
    filas = _filas(PUB_INDICE)
    assert len(filas) >= 50, "deben estar los anuarios y boletines convertidos"
    tipos = {r["tipo"] for r in filas}
    assert any(t.startswith("Anuario") for t in tipos) and any(t.startswith("Boletín") for t in tipos)
    assert all(r["archivo_md"].startswith("publicaciones_ambientales/") for r in filas[:50])


def test_el_grafo_integra_la_jurisprudencia_nueva():
    grafo = json.loads(GRAFO.read_text(encoding="utf-8"))
    nodos, aristas = grafo["nodes"], grafo["edges"]
    ids = {n["id"] for n in nodos}
    sent_tc = [n for n in nodos if n.get("node_type") == "jurisprudencia_tc"]
    assert len(sent_tc) >= 900, "el grafo debe incluir las sentencias del TC de los últimos 2 años"
    assert "organo_tc" in ids, "debe existir el nodo del Tribunal Constitucional"
    assert all(n.get("source_file", "").startswith("jurisprudencia_tc/") for n in sent_tc if n.get("source_file"))
    relaciones = {e.get("relation") for e in aristas}
    assert {"resuelto_por", "cita_norma"} <= relaciones, "deben existir las relaciones nuevas"
    enlaces_norma = [e for e in aristas if e.get("relation") == "cita_norma"]
    assert len(enlaces_norma) >= 1000, "las sentencias del TC deben quedar enlazadas a las normas que citan"
    con_comunidad = [n for n in nodos if "community" in n]
    assert len(con_comunidad) >= len(nodos) * 0.95, "las comunidades deben quedar recalculadas"
    assert len({n["community"] for n in con_comunidad}) >= 20


def test_publicaciones_ambientales_quedan_enlazadas_al_tribunal():
    grafo = json.loads(GRAFO.read_text(encoding="utf-8"))
    pub = [n for n in grafo["nodes"] if n.get("node_type") == "anuario_boletin_ambiental"]
    assert len(pub) >= 50, "las publicaciones ambientales deben estar todas en el grafo"
    publicadas = [e for e in grafo["edges"] if e.get("relation") == "publicado_por"]
    assert len(publicadas) >= 50, "cada publicación debe quedar enlazada a su tribunal"


def test_el_publicador_separa_el_dataset_de_entrenamiento():
    fuente = (BASE / "online_library_sync.py").read_text(encoding="utf-8")
    assert "publicar_dataset_entrenamiento" in fuente
    assert "doctrina-jurisprudencia-chile-training" in fuente
    assert 'ignore_patterns=["instituciones.jsonl", "train.jsonl"]' in fuente, \
        "el dataset principal no debe volver a subir las versiones plenas"
    assert '"data/train.jsonl", "data/instituciones.jsonl"' in fuente, \
        "el publicador debe retirar del dataset principal las versiones plenas si estaban"
