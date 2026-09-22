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


def test_grafo_vacio_avisa_que_las_consultas_no_tendran_nada(tmp_path):
    """
    El paquete de PyPI no lleva el corpus doctrinal: quien lo instala tiene un motor con 0
    nodos que responde 'no encontrado' a todo. Eso no puede quedar en silencio, porque el
    agente concluiría que el tema no está en la doctrina.
    """
    vacio = LegalGraphifyEngine(doctrina_dir=str(tmp_path / "sin_doctrina"))
    vacio.construir_grafo_desde_doctrina()
    assert vacio.graph.number_of_nodes() == 0
    aviso = " ".join(vacio.advertencias)
    assert "grafo quedó vacío" in aviso, vacio.advertencias
    assert "PyPI" in aviso and "corpus" in aviso, aviso


def test_archivo_de_grafo_ausente_avisa(tmp_path):
    """Tampoco puede ser silencioso 'todavía no hay artefacto'."""
    eng = LegalGraphifyEngine()
    assert eng.cargar_grafo_json(str(tmp_path / "no_existe.json")) is False
    assert any("No existe el grafo" in a for a in eng.advertencias), eng.advertencias


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
    «afianzamiento» aparece en el texto de un tratado pero no es el nombre de ninguna
    institución ni está en la definición de ninguna: antes el motor respondía "no encontrado"
    y el tema sí estaba en la doctrina. («compraventa» servía para esta prueba hasta que el
    corpus ampliado la volvió el nombre de una sección: el motor ahora la resuelve por nombre,
    que es mejor. Por eso se busca una palabra que sólo viva en el cuerpo del texto.)
    """
    r = engine.calcular_ahorro_tokens("afianzamiento")
    assert r.get("encontrado") is True, "el tema está en la doctrina: no puede decir que no"

    # Y debe avisar que la coincidencia es de texto, no de nombre del nodo
    avisos = engine.advertencias
    assert any("afianzamiento" in a and "TEXTO" in a for a in avisos), (
        f"falta el aviso de coincidencia textual: {avisos}"
    )


def test_consulta_inexistente_sigue_siendo_no_encontrada(engine):
    """El recall por corpus no puede inventar: un término que no está en ninguna parte falla."""
    r = engine.calcular_ahorro_tokens("zzzzqwerty inexistente")
    assert r.get("encontrado") is False


def test_con_avisos_agrega_y_no_cambia_la_forma(monkeypatch):
    """
    _con_avisos es la función que decide si el agente ve los avisos del motor. Se prueba con un
    motor de mentira para que el resultado no dependa de si el entorno tiene numpy/scipy (sin
    ellos el motor real agrega su propio aviso de PageRank y la prueba sería frágil).
    """
    import mcp_server

    class MotorFalso:
        advertencias = []

    falso = MotorFalso()
    monkeypatch.setattr(mcp_server, "legal_graphify_engine", falso)

    # Sin avisos, la respuesta no cambia de forma (hay consumidores que dependen de esas claves)
    assert mcp_server._con_avisos({"encontrado": True}) == {"encontrado": True}

    # Con avisos, se agregan
    falso.advertencias = ["aviso de prueba"]
    assert mcp_server._con_avisos({"encontrado": True}) == {
        "encontrado": True,
        "advertencias": ["aviso de prueba"],
    }

    # Un error no se adorna con avisos
    assert mcp_server._con_avisos({"error": "algo falló"}) == {"error": "algo falló"}


def test_god_nodes_dice_por_que_metrica_ordeno(engine):
    """
    El ranking cambia según la métrica disponible (PageRank real con numpy+scipy, grado sin
    ellos), así que el payload tiene que declarar cuál usó: sin eso, el mismo tool devuelve
    dos órdenes distintos en dos máquinas sin que nadie pueda notarlo.
    """
    r = engine.calcular_god_nodes(top_n=3)
    assert r["ordenado_por"] in ("pagerank", "grado_conexiones")

    if r["ordenado_por"] == "grado_conexiones":
        assert any("PageRank no disponible" in a for a in engine.advertencias)
    else:
        assert not any("PageRank no disponible" in a for a in engine.advertencias)

    # El orden debe ser coherente con la métrica declarada
    scores = [g["pagerank"] for g in r["god_instituciones"]]
    assert scores == sorted(scores, reverse=True), "la lista no está ordenada por lo que declara"
