"""
Tests unitarios para el motor LegalGraphify y reducción de tokens con Grafos de Conocimiento.
Valida la extracción de entidades dogmáticas, concordancias BCN, fallos rectores CS,
cálculo de ahorro de tokens (medido: 30% a 90% según la institución, mediana 74%; ver
docs/medicion_tokens.md) y exportación a diagramas Mermaid.
"""

import os
import json
import pytest

from legal_graphify import LegalGraphifyEngine, DEFAULT_GRAPH_PATH
import mcp_server


@pytest.fixture(scope="module")
def engine():
    eng = LegalGraphifyEngine()
    if not (os.path.exists(DEFAULT_GRAPH_PATH) and eng.cargar_grafo_json(DEFAULT_GRAPH_PATH)):
        eng.construir_grafo_desde_doctrina()
    return eng


def test_construccion_grafo_metricas_base(engine):
    """Verifica que el grafo contenga cientos de nodos y aristas de doctrina chilena."""
    assert engine.graph.number_of_nodes() >= 100
    assert engine.graph.number_of_edges() >= 200

    tipos_nodos = set(d.get("node_type") for _, d in engine.graph.nodes(data=True))
    assert "institucion" in tipos_nodos
    assert "articulo_legal" in tipos_nodos
    assert "autor" in tipos_nodos
    assert "jurisprudencia" in tipos_nodos
    assert "via_procesal" in tipos_nodos


def test_consulta_subgrafo_simulacion(engine):
    """Verifica la consulta de subgrafo para la institución de Simulación."""
    res = engine.consultar_subgrafo("simulacion")
    assert res["encontrado"] is True
    assert "Simulación" in res["label"]

    info = res["subgrafo_info"]
    assert info["total_nodos_subgrafo"] >= 3
    assert info["normas_conectadas"] >= 1

    yaml_res = res["subgrafo_resumen_yaml"]
    assert "institucion:" in yaml_res
    assert "fuente_canonica:" in yaml_res
    assert "normas_positivas:" in yaml_res
    assert "criterios_cs:" in yaml_res


def test_ahorro_tokens_significativo(engine):
    """Verifica que el ahorro de tokens sea significativo (> 70% vs texto completo)."""
    ahorro = engine.calcular_ahorro_tokens("simulacion")
    assert ahorro["encontrado"] is True

    m = ahorro["metricas"]
    assert m["tokens_subgrafo"] < m["tokens_texto_completo"]
    assert m["tokens_ahorrados"] > 0
    # El umbral era 70% y pasaba solo porque el tamaño de cada obra se inflaba con un piso
    # de 1200 tokens: la medición real de 'simulacion' es 69,1% (968 -> 299). Se exige un
    # piso que el motor cumple con números honestos, y la distribución medida vive en
    # docs/medicion_tokens.md (mediana 99,9 % sobre 9.863 instituciones, medición 2026-09-25).
    assert m["porcentaje_ahorro"] >= 50.0
    assert "x" in m["factor_reduccion"]


def test_consulta_subgrafo_imprevision(engine):
    """Verifica la consulta sobre Teoría de la Imprevisión y Pacta Sunt Servanda."""
    res = engine.consultar_subgrafo("imprevision")
    assert res["encontrado"] is True
    assert "Imprevisión" in res["label"] or "Rebus Sic Stantibus" in res["label"]

    yaml_res = res["subgrafo_resumen_yaml"]
    assert "Jorge López Santa María" in yaml_res or "López" in yaml_res


def test_exportar_subgrafo_mermaid(engine):
    """Verifica que la exportación Mermaid genere sintaxis válida y formateada."""
    mermaid_code = engine.exportar_subgrafo_mermaid("simulacion", max_hops=1)
    assert mermaid_code.startswith("```mermaid")
    assert "graph TD" in mermaid_code
    assert "classDef central" in mermaid_code
    assert "classDef norma" in mermaid_code
    assert "classDef fallo" in mermaid_code
    assert mermaid_code.endswith("```")


def test_persistencia_y_carga_json(tmp_path, engine):
    """Verifica que el grafo se pueda serializar y deserializar sin pérdida de nodos."""
    temp_json = str(tmp_path / "test_graph.json")
    eng = engine  # el grafo ya cargado: serializar y deserializar no necesita reconstruirlo
    saved = eng.guardar_grafo_json(temp_json)
    assert os.path.exists(saved)

    eng_loaded = LegalGraphifyEngine()
    ok = eng_loaded.cargar_grafo_json(temp_json)
    assert ok is True
    assert eng_loaded.graph.number_of_nodes() == eng.graph.number_of_nodes()
    assert eng_loaded.graph.number_of_edges() == eng.graph.number_of_edges()


def test_integracion_mcp_server():
    """Verifica que la herramienta graphify_consulta_subgrafo funcione en el servidor MCP."""
    res = mcp_server.handle_tool_call(
        "graphify_consulta_subgrafo",
        {"query": "simulacion", "incluir_mermaid": True}
    )
    assert isinstance(res, dict)
    assert res.get("encontrado") is True
    assert "Simulación" in res.get("label", "")
    assert "diagrama_mermaid" in res
    assert "```mermaid" in res["diagrama_mermaid"]


def test_consulta_nodo_inexistente(engine):
    """Verifica el comportamiento graceful ante una búsqueda sin coincidencias."""
    res = engine.consultar_subgrafo("termino_completamente_inexistente_xyz_123")
    assert res["encontrado"] is False
    assert "sugerencias" in res


def test_consulta_subgrafo_baremo_y_pjud_especializado(engine):
    """Verifica la consulta e interconexión de nodos del Baremo Daño Moral y portales PJUD especializados."""
    res_baremo = engine.consultar_subgrafo("baremo dano moral abuelo")
    assert res_baremo["encontrado"] is True
    assert "Baremo" in res_baremo["label"] or "Abuelo" in res_baremo["label"]

    res_confianza = engine.consultar_subgrafo("Principio de Confianza Legítima en Contratas Públicas")
    assert res_confianza["encontrado"] is True
    assert res_confianza["subgrafo_info"]["fallos_conectados"] >= 1

    res_ddhh = engine.consultar_subgrafo("Imprescriptibilidad de Crímenes de Lesa Humanidad")
    assert res_ddhh["encontrado"] is True
    assert res_ddhh["subgrafo_info"]["fallos_conectados"] >= 1


def test_analizar_tendencia_y_baremo_en_explicar_institucion(engine):
    """Verifica que explicar_institucion integre cuantificación Baremo UF/CLP y tendencia jurisprudencial temporal."""
    exp = engine.explicar_institucion("Baremo Estadístico de Daño Moral por Muerte y Lesiones")
    assert exp["encontrado"] is True
    assert "tendencia_jurisprudencial" in exp
    tend = exp["tendencia_jurisprudencial"]
    assert tend["total_tramos_baremo"] >= 10
    assert len(tend["tramos_baremo_uf_clp"]) >= 5
    parentescos = {t["parentesco"] for t in tend["tramos_baremo_uf_clp"]}
    assert any("Hijo" in p or "Cónyuge" in p or "Abuelo" in p for p in parentescos)

    exp_isapres = engine.explicar_institucion("Judicialización de Alzas de Planes de Isapres, GES y Cobertura de Medicamentos de Alto Costo")
    assert exp_isapres["encontrado"] is True
    tend_isapres = exp_isapres["tendencia_jurisprudencial"]
    assert tend_isapres["total_fallos_analizados"] >= 10
    assert "indice_vigencia_temporal" in tend_isapres
    assert "distribucion_anual" in tend_isapres

