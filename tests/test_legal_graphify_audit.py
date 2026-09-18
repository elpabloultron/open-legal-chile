"""
Tests de auditoría de la superficie LegalGraphify (motor legal_graphify.py +
herramientas MCP graphify_*).

Cada prueba de este archivo reproduce un defecto concreto detectado en la
auditoría. Están escritas para FALLAR contra el código previo al arreglo y
PASAR una vez aplicados los arreglos acotados.
"""

import json
import os

import pytest

import legal_graphify
from legal_graphify import LegalGraphifyEngine


@pytest.fixture(scope="module")
def engine():
    eng = LegalGraphifyEngine()
    if not (os.path.exists(legal_graphify.DEFAULT_GRAPH_PATH) and eng.cargar_grafo_json()):
        eng.construir_grafo_desde_doctrina()
    return eng


@pytest.fixture(scope="module")
def built_engine():
    eng = LegalGraphifyEngine()
    eng.construir_grafo_desde_doctrina()
    return eng


# ---------------------------------------------------------------------------
# D1 — guardar_grafo_json duplicaba la lista de aristas bajo `edges` y `links`
# ---------------------------------------------------------------------------
def test_guardar_grafo_emite_una_sola_clave_de_aristas(tmp_path, built_engine):
    p = str(tmp_path / "g.json")
    built_engine.guardar_grafo_json(p)
    with open(p, encoding="utf-8") as f:
        data = json.load(f)

    claves = [k for k in ("edges", "links") if k in data]
    assert len(claves) == 1, f"la lista de aristas está duplicada bajo {claves}"
    assert len(data[claves[0]]) == built_engine.graph.number_of_edges()


# ---------------------------------------------------------------------------
# D2 — integrar_con_graphify crasheaba con KeyError en un grafo keyed `edges`
# ---------------------------------------------------------------------------
def test_integrar_con_graphify_acepta_esquema_edges(tmp_path, built_engine):
    p = str(tmp_path / "graph.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(
            {
                "directed": False,
                "multigraph": False,
                "graph": {},
                "nodes": [{"id": "a"}, {"id": "b"}],
                "edges": [{"source": "a", "target": "b", "relation": "x"}],
            },
            f,
        )

    res = built_engine.integrar_con_graphify(p)  # antes: KeyError: 'links'
    assert res["fusionado"] is True
    assert res["nodos_agregados"] == built_engine.graph.number_of_nodes()

    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    claves = [k for k in ("edges", "links") if k in data]
    assert len(claves) == 1
    assert len(data[claves[0]]) == 1 + built_engine.graph.number_of_edges()


# ---------------------------------------------------------------------------
# D2b — integrar_con_graphify debe ser idempotente
# ---------------------------------------------------------------------------
def test_integrar_con_graphify_idempotente(tmp_path, built_engine):
    p = str(tmp_path / "graph.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"directed": False, "graph": {}, "nodes": [], "links": []}, f)

    r1 = built_engine.integrar_con_graphify(p)
    r2 = built_engine.integrar_con_graphify(p)

    assert r1["nodos_agregados"] == built_engine.graph.number_of_nodes()
    assert r1["aristas_agregadas"] == built_engine.graph.number_of_edges()
    assert r2["nodos_agregados"] == 0, "la segunda fusión duplicó nodos"
    assert r2["aristas_agregadas"] == 0, "la segunda fusión duplicó aristas"
    assert r2["total_nodos_final"] == r1["total_nodos_final"]
    assert r2["total_aristas_final"] == r1["total_aristas_final"]


# ---------------------------------------------------------------------------
# D3 — los nodos `obra` no tienen `tokens_completos`, por lo que se usaba el
#      baseline fabricado 2800 y se reportaba un ahorro irreal (~97%)
# ---------------------------------------------------------------------------
def test_ahorro_obra_usa_tokens_archivo_no_default(engine):
    obras = [
        (d.get("tokens_archivo"), n, d.get("label"))
        for n, d in engine.graph.nodes(data=True)
        if d.get("node_type") == "obra" and d.get("tokens_archivo")
    ]
    assert obras, "no hay nodos obra en el grafo"
    obras.sort(reverse=True, key=lambda t: t[0])
    tokens_archivo, _nid, label = obras[0]

    res = engine.calcular_ahorro_tokens(label)
    assert res["encontrado"] is True
    m = res["metricas"]

    assert m["tokens_texto_completo"] == tokens_archivo, (
        "el baseline de tokens ignoró tokens_archivo y usó el default fabricado"
    )
    assert m["tokens_texto_completo"] != 2800
    assert m["porcentaje_ahorro"] < 95.0, "ahorro irreal por baseline fabricado"


# ---------------------------------------------------------------------------
# D5 — guardar_grafo_json crasheaba con una ruta relativa sin directorio
# ---------------------------------------------------------------------------
def test_guardar_grafo_ruta_relativa_sin_directorio(tmp_path, monkeypatch, built_engine):
    monkeypatch.chdir(tmp_path)
    p = built_engine.guardar_grafo_json("g_relativo.json")  # antes: FileNotFoundError ''
    assert os.path.exists(p)
    assert os.path.dirname(p) in ("", os.getcwd())
