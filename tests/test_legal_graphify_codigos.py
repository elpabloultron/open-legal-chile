"""
Tests de la ingesta de códigos oficiales al grafo (rescate del parser del paquete legal-graphify).

El motor sabía sacar artículos del texto doctrinal, pero no de un código descargado del BCN.
Estos tests fijan el contrato del rescate: extrae, no duplica, queda consultable, y si el texto
no rinde nada lo dice en vez de reportar un éxito vacío.
"""

import os

import pytest

from legal_graphify import (
    LegalGraphifyEngine,
    extract_articulos_de_codigo,
    _normalize_str,
)

CODIGO = "Código Civil"
TEXTO = """
Art. 1545. Todo contrato legalmente celebrado es una ley para los contratantes, y no puede
ser invalidado sino por su consentimiento mutuo o por causas legales.

Artículo 1546. Los contratos deben ejecutarse de buena fe, y por consiguiente obligan no solo
a lo que en ellos se expresa, sino a todas las cosas que emanan precisamente de la naturaleza
de la obligación, o que por la ley pertenecen a ella.
"""


@pytest.fixture(scope="module")
def engine():
    from legal_graphify import DEFAULT_GRAPH_PATH
    eng = LegalGraphifyEngine()
    if not (os.path.exists(DEFAULT_GRAPH_PATH) and eng.cargar_grafo_json(DEFAULT_GRAPH_PATH)):
        eng.construir_grafo_desde_doctrina()
    return eng


def test_extrae_articulos_y_los_cuelga_del_codigo():
    grafo = extract_articulos_de_codigo(CODIGO, TEXTO)
    articulos = [
        (nid, d) for nid, d in grafo.nodes(data=True) if d.get("node_type") == "articulo_legal"
    ]
    assert len(articulos) == 2, f"esperaba 2 artículos, extrajo {len(articulos)}"

    etiquetas = sorted(d["label"] for _, d in articulos)
    assert etiquetas == ["Código Civil, Art. 1545", "Código Civil, Art. 1546"]

    codigos = [nid for nid, d in grafo.nodes(data=True) if d.get("node_type") == "cuerpo_legal"]
    assert len(codigos) == 1, "debe haber un nodo para el código"
    assert grafo.number_of_edges() == 2
    for nid, _ in articulos:
        assert grafo.has_edge(nid, codigos[0])
        assert grafo.edges[nid, codigos[0]]["relation"] == "pertenece_a"

    # El texto del artículo queda guardado (no solo el número)
    cuerpo = next(d["texto"] for _, d in articulos if d["label"].endswith("1546"))
    assert "buena fe" in cuerpo


def test_la_ingesta_no_duplica_articulos(engine):
    primera = engine.ingerir_codigo_bcn(CODIGO, TEXTO)
    assert primera["articulos_detectados"] == 2

    segunda = engine.ingerir_codigo_bcn(CODIGO, TEXTO)
    assert segunda["articulos_detectados"] == 2, "el texto se sigue leyendo igual"
    assert segunda["nodos_nuevos"] == 0, "lo ya ingestado no puede volver a entrar"
    assert segunda["enlaces_nuevos"] == 0


def test_los_articulos_ingeridos_quedan_consultables(engine):
    engine.ingerir_codigo_bcn(CODIGO, TEXTO)
    clave = _normalize_str("Código Civil, Art. 1546")
    assert clave in engine.normas_index, "un artículo ingestado debe quedar indexado"

    r = engine.consultar_subgrafo("Código Civil, Art. 1545")
    assert r.get("encontrado") is True


def test_texto_que_no_es_un_codigo_avisa_en_vez_de_fingir(engine):
    resultado = engine.ingerir_codigo_bcn("Código Inventado", "Este texto no tiene artículos.")
    assert resultado["articulos_detectados"] == 0
    assert resultado["nodos_nuevos"] == 0
    assert resultado["advertencias"], "no puede reportarse como éxito una ingesta que no ingirió"


def test_articulos_bis_y_ter_se_reconocen():
    grafo = extract_articulos_de_codigo("Código Procesal Penal", "Art. 1 bis. Regla especial.")
    etiquetas = [d["label"] for _, d in grafo.nodes(data=True) if d.get("node_type") == "articulo_legal"]
    assert etiquetas == ["Código Procesal Penal, Art. 1 bis"]
