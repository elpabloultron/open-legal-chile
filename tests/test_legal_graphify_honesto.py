"""
Tests de las correcciones de honestidad del motor del grafo (auditoría del 18-09-2026).

Cubren los tres defectos que hacían que el motor dijera más de lo que sabía:

1. El tamaño de cada obra se calculaba con un piso de 1200 tokens, así que el 93% de las
   instituciones reportaba un tamaño que no era el suyo y el ahorro publicado salía inflado.
2. Un archivo de grafo corrupto se trataba en silencio: el motor lo reconstruía desde
   doctrina/ y respondía como si nada, sin que nadie pudiera enterarse.
3. Una consulta que no calzaba con el nombre de ningún nodo devolvía "no encontrado"
   aunque el tema estuviera en el texto de las obras (p. ej. 'compraventa').

Los tres comparten la misma regla del resto del sistema: avisar, no inventar.
"""

import json
import os

import pytest

from legal_graphify import LegalGraphifyEngine, DEFAULT_GRAPH_PATH


@pytest.fixture(scope="module")
def engine():
    eng = LegalGraphifyEngine()
    if not (os.path.exists(DEFAULT_GRAPH_PATH) and eng.cargar_grafo_json(DEFAULT_GRAPH_PATH)):
        eng.construir_grafo_desde_doctrina()
    return eng


def _instituciones(eng):
    return [
        (nid, d)
        for nid, d in eng.graph.nodes(data=True)
        if d.get("node_type") == "institucion"
    ]


def test_tamano_de_obra_no_usa_piso(engine):
    """El tamaño guardado debe ser el del archivo, no un mínimo de 1200 tokens."""
    tamanos = [d.get("tokens_completos") for _, d in _instituciones(engine)]
    con_valor = [t for t in tamanos if t]
    assert con_valor, "las instituciones deben declarar su tamaño"

    # Antes de la corrección, 93 de 967 nodos reportaban exactamente 1200 (el piso).
    # Con el arreglo, el valor es el del archivo: puede haber coincidencias sueltas,
    # pero no una mayoría pegada al piso.
    pegados_al_piso = sum(1 for t in con_valor if t == 1200)
    assert pegados_al_piso < len(con_valor) * 0.2, (
        f"{pegados_al_piso} de {len(con_valor)} instituciones siguen reportando 1200 tokens: "
        "el piso volvió"
    )

    # Y el rango debe ser el medido, no todos iguales
    assert min(con_valor) < 400, "debe haber instituciones pequeñas con su tamaño real"
    assert max(con_valor) > 800, "debe haber instituciones grandes con su tamaño real"


def test_ahorro_usa_el_tamano_real_de_la_obra(engine):
    """El ahorro de una institución no puede venir de un tamaño fabricado."""
    # 'tutela laboral' tiene 1176 tokens reales; con el piso habría reportado 2800.
    r = engine.calcular_ahorro_tokens("tutela laboral")
    assert r.get("encontrado") is True
    m = r["metricas"]
    assert m["tokens_texto_completo"] < 2000, (
        "el denominador volvió a inflarse: "
        f"{m['tokens_texto_completo']} tokens para una obra de ~1176"
    )
    assert 0 < m["porcentaje_ahorro"] <= 100


def test_grafo_corrupto_avisa_en_vez_de_callar(engine, tmp_path):
    """Un archivo ilegible se reconstruye, pero el motor lo dice."""
    corrupto = tmp_path / "grafo_corrupto.json"
    corrupto.write_text('{ "nodes": [ roto', encoding="utf-8")

    eng = LegalGraphifyEngine()
    resultado = eng.cargar_grafo_json(str(corrupto))

    assert resultado is True, "el motor debe seguir siendo usable (reconstruye desde doctrina/)"
    assert eng.advertencias, "pero tiene que avisar de que no usó el archivo"
    assert any(str(corrupto) in a for a in eng.advertencias), (
        f"el aviso debe nombrar el archivo: {eng.advertencias}"
    )


def test_grafo_valido_no_deja_avisos(engine):
    """Si el archivo está bien, no hay nada que avisar (el aviso no puede ser ruido)."""
    eng = LegalGraphifyEngine()
    assert eng.cargar_grafo_json(DEFAULT_GRAPH_PATH) is True
    assert eng.advertencias == []


def test_json_que_no_es_node_link_avisa(engine, tmp_path):
    """Un JSON válido pero que no es un grafo no puede pasar como carga exitosa en silencio."""
    raro = tmp_path / "no_grafo.json"
    raro.write_text(json.dumps({"hola": "mundo"}), encoding="utf-8")

    eng = LegalGraphifyEngine()
    eng.cargar_grafo_json(str(raro))
    assert eng.advertencias, "un JSON sin estructura Node-Link debe dejar aviso"


def test_recall_por_corpus_encuentra_lo_que_no_es_un_nodo(engine):
    """
    'compraventa' aparece en el texto de 4 tratados pero no es el nombre de ninguna
    institución: antes el motor respondía "no encontrado" y el tema sí estaba en la doctrina.
    """
    r = engine.calcular_ahorro_tokens("compraventa")
    assert r.get("encontrado") is True, "el tema está en la doctrina: no puede decir que no"

    # Y debe avisar que la coincidencia es de texto, no de nombre del nodo
    avisos = engine.advertencias
    assert any("compraventa" in a and "TEXTO" in a for a in avisos), (
        f"falta el aviso de coincidencia textual: {avisos}"
    )


def test_consulta_inexistente_sigue_siendo_no_encontrada(engine):
    """El recall por corpus no puede inventar: un término que no está en ninguna parte falla."""
    r = engine.calcular_ahorro_tokens("zzzzqwerty inexistente")
    assert r.get("encontrado") is False


def test_mcp_agrega_los_avisos_al_payload(engine):
    """Las herramientas del servidor MCP deben exponer el aviso al agente."""
    import mcp_server

    mcp_server.legal_graphify_engine.advertencias = []
    sin_avisos = mcp_server.handle_tool_call("graphify_god_nodes", {"top_n": 2})
    assert "error" not in sin_avisos
    assert "advertencias" not in sin_avisos, "sin avisos, la forma de la respuesta no cambia"

    mcp_server.legal_graphify_engine.advertencias = ["aviso de prueba"]
    con_avisos = mcp_server.handle_tool_call("graphify_god_nodes", {"top_n": 2})
    assert con_avisos.get("advertencias") == ["aviso de prueba"]
    mcp_server.legal_graphify_engine.advertencias = []
