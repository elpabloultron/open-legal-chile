"""
Tests unitarios e integración para la arquitectura Data Science de Open Legal Chile:
- Pilar 1: Grafo Multiplex (atenuación de súper-hubs editoriales, PPR multiplex, caminos sustantivos,
  unificación ontológica Baremo 17/17, enriquecimiento masivo de instituciones y aristas semánticas).
- Pilar 2: Exportación columnar Apache Parquet (esquemas tipados, trazabilidad sin rutas privadas).
- Pilar 3: Módulo `jurimetria.py` + herramientas MCP `jurimetria_analizar_corpus` y
  `jurimetria_exportar_investigacion` (PageRank dirigido, HITS Authority/Hub, muestreo estratificado
  determinista para validación intercodificador y paquete reproducible CSV/GraphML/Parquet/BibTeX).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import networkx as nx
import pytest

import jurimetria
import legal_graphify
import mcp_server
from legal_graphify import (
    DEFAULT_GRAPH_PATH,
    PESO_ARISTA_BIBLIOGRAFICA,
    LegalGraphifyEngine,
    es_arista_sustantiva,
    peso_multiplex,
)
from mapa_corpus import constructor, grafo as mapa_grafo


def _motor_sintetico() -> LegalGraphifyEngine:
    """Construye un grafo controlado con súper-hub editorial + capa sustantiva normativa/jurisprudencial."""
    eng = LegalGraphifyEngine(usar_mapa=False)
    g = nx.DiGraph()
    # Súper-hub editorial conectando dos instituciones de materias distintas
    g.add_node("autor_editorial", label="Academia Judicial de Chile", node_type="autor", community=1)
    g.add_node("obra_compendio", label="Compendio General", node_type="obra", community=1)

    # Instituciones jurídicas
    g.add_node(
        "inst_nulidad",
        label="Nulidad Absoluta",
        node_type="institucion",
        area="Derecho Civil",
        definicion="Sanción civil de ineficacia por omisión de requisitos de validez del acto jurídico.",
        operativa_procesal="Acción ordinaria de nulidad absoluta (Art. 1683 Código Civil).",
        tokens_completos=1200,
        community=2,
    )
    g.add_node(
        "inst_simulacion",
        label="Simulación Ilícita",
        node_type="institucion",
        area="Derecho Civil",
        definicion="Divergencia deliberada entre la voluntad declarada y la voluntad real en fraude a terceros.",
        operativa_procesal="Acción declarativa de simulación y nulidad absoluta.",
        tokens_completos=1100,
        community=2,
    )
    g.add_node(
        "inst_despido_injustificado",
        label="Despido Injustificado",
        node_type="institucion",
        area="Derecho Laboral",
        definicion="Término unilateral del contrato de trabajo sin causal legal acreditada.",
        operativa_procesal="Procedimiento de aplicación general laboral.",
        tokens_completos=1300,
        community=3,
    )
    g.add_node(
        "inst_huerfana_ineficacia",
        label="Ineficacia del Acto Jurídico por Nulidad",
        node_type="institucion",
        area="Derecho Civil",
        definicion="Sanción civil de ineficacia por omisión de requisitos de validez del acto jurídico y simulación.",
        tokens_completos=900,
        community=2,
    )

    # Normas y jurisprudencia
    g.add_node("norma:cc:1682", label="Código Civil, Art. 1682", node_type="articulo_legal", community=2)
    g.add_node("norma:cc:1707", label="Código Civil, Art. 1707", node_type="articulo_legal", community=2)
    g.add_node("norma:cpr:1682", label="CPR, Art. 1682 (ruido OCR)", node_type="norma", community=2)
    g.add_node("cs:1001-2024", label="CS - Rol N.° 1.001-2024", node_type="sentencia_cs", community=3)
    g.add_node("baremo_muerte_3", label="Baremo Daño Moral por Muerte — Hijo(a)", node_type="baremo", parentesco="Hijo(a)", community=4)

    # Aristas bibliográficas (contención editorial)
    for inst in ("inst_nulidad", "inst_simulacion", "inst_despido_injustificado", "inst_huerfana_ineficacia"):
        g.add_edge(inst, "obra_compendio", relation="contenido_en", weight=1.0)
        g.add_edge(inst, "autor_editorial", relation="analizado_por", weight=1.0)
    g.add_edge("obra_compendio", "autor_editorial", relation="escrito_por", weight=1.0)

    # Aristas jurídicas sustantivas
    g.add_edge("inst_nulidad", "norma:cc:1682", relation="fundamenta_en", weight=2.0)
    g.add_edge("inst_simulacion", "norma:cc:1682", relation="fundamenta_en", weight=1.0)
    g.add_edge("inst_simulacion", "norma:cc:1707", relation="fundamenta_en", weight=2.0)
    g.add_edge("cs:1001-2024", "norma:cc:1682", relation="cita_norma", weight=1.0)
    g.add_edge("inst_nulidad", "cs:1001-2024", relation="criterio_jurisprudencial", weight=1.0)
    g.add_edge("inst_despido_injustificado", "norma:cpr:1682", relation="fundamenta_en", weight=1.0)

    eng.graph = g
    eng.is_built = True
    eng._actualizar_indice_invertido()
    for nid, d in g.nodes(data=True):
        if d.get("node_type") == "institucion":
            eng.instituciones_index[legal_graphify._normalize_str(d["label"])] = nid
        elif d.get("node_type") in ("articulo_legal", "norma"):
            eng.normas_index[legal_graphify._normalize_str(d["label"])] = nid
    return eng


# ── Pilar 1: Grafo Multiplex, Resolución Ontológica y Semántica ───────────────────────────────
def test_clasificacion_y_atenuacion_multiplex():
    eng = _motor_sintetico()
    g = eng.graph
    assert es_arista_sustantiva("inst_nulidad", "norma:cc:1682", g["inst_nulidad"]["norma:cc:1682"], g) is True
    assert es_arista_sustantiva("inst_nulidad", "obra_compendio", g["inst_nulidad"]["obra_compendio"], g) is False
    assert es_arista_sustantiva("inst_nulidad", "autor_editorial", g["inst_nulidad"]["autor_editorial"], g) is False

    w_sust = peso_multiplex("inst_nulidad", "norma:cc:1682", g["inst_nulidad"]["norma:cc:1682"], g)
    w_bib = peso_multiplex("inst_nulidad", "autor_editorial", g["inst_nulidad"]["autor_editorial"], g)
    assert w_sust == 2.0
    assert w_bib == pytest.approx(PESO_ARISTA_BIBLIOGRAFICA, rel=1e-3)
    assert w_sust > w_bib * 10


def test_ppr_multiplex_prioriza_norma_y_fallo_sobre_hub_editorial():
    eng = _motor_sintetico()
    ranking = eng.ranking_ppr_subgrafo("inst_nulidad", top_k=5)
    assert ranking
    # La norma positiva Art. 1682 CC y la sentencia CS deben rankear por encima del súper-hub editorial
    posiciones = {r["id"]: idx for idx, r in enumerate(ranking)}
    assert "norma:cc:1682" in posiciones
    if "autor_editorial" in posiciones:
        assert posiciones["norma:cc:1682"] < posiciones["autor_editorial"]


def test_camino_sustantivo_evita_puente_bibliografico_y_degrada_si_desconexo():
    eng = _motor_sintetico()
    # Entre Simulación y Nulidad existe camino sustantivo real vía Art. 1682 CC
    res_sust = eng.encontrar_camino("Simulación Ilícita", "Nulidad Absoluta", solo_sustantivo=True)
    assert res_sust["encontrado"] is True
    assert res_sust["tipo_camino"] == "sustantivo"
    for camino in res_sust["caminos"]:
        assert "Academia Judicial de Chile" not in camino["nodos"]
        assert "Compendio General" not in camino["nodos"]
        assert "Código Civil, Art. 1682" in camino["nodos"]

    # Entre Simulación y Despido Injustificado solo hay puente bibliográfico -> fallback explícito
    res_fb = eng.encontrar_camino("Simulación Ilícita", "Despido Injustificado", solo_sustantivo=True)
    assert res_fb["encontrado"] is True
    assert res_fb["tipo_camino"] == "bibliografico_fallback"


def test_god_nodes_sustantivo_excluye_contenedores_editoriales():
    eng = _motor_sintetico()
    res = eng.calcular_god_nodes(top_n=5, solo_sustantivo=True)
    assert res["modo_multiplex_sustantivo"] is True
    tipos_inst = {x["tipo"] for x in res["god_instituciones"]}
    assert "obra" not in tipos_inst and "autor" not in tipos_inst


def test_enriquecer_aristas_semanticas_conecta_institucion_huerfana():
    eng = _motor_sintetico()
    res = eng.enriquecer_aristas_semanticas(
        max_nodos=10,
        top_k=2,
        umbral=0.25,
        solo_sin_enlaces_sustantivos=True,
        use_fastembed=False,
    )
    assert res["aristas_agregadas"] >= 1
    assert eng.graph.has_edge("inst_huerfana_ineficacia", "inst_nulidad")
    assert eng.graph["inst_huerfana_ineficacia"]["inst_nulidad"]["relation"] == "similar_semantico"


def test_unificacion_ontologica_baremo_en_alias_y_capa_mapa(tmp_path, fabrica_mapa):
    curado = {
        "directed": True,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"id": "baremo_muerte_3", "label": "Baremo Daño Moral por Muerte — Hijo(a)", "node_type": "baremo", "parentesco": "Hijo(a)", "community": 4},
        ],
        "edges": [],
    }
    fila_baremo = {
        "id": "baremo:baremo_muerte_3_hijoa",
        "col": "baremo",
        "ruta": "jurisprudencia_baremo/baremo_muerte_3_hijoa.md",
        "blob": "f" * 40,
        "bytes": 600,
        "titulo": "Baremo Daño Moral por Muerte — Demandante: Hijo(a)",
    }
    # 1. alias_curados del constructor del mapa emite alias exacto
    ents = constructor.entidades([fila_baremo])
    capa = mapa_grafo.construir_capa([fila_baremo], ents, set())
    alias, _ = mapa_grafo.alias_curados(curado, capa, [fila_baremo])
    assert alias.get("baremo_muerte_3") == "baremo:baremo_muerte_3_hijoa"

    # 2. cargar_capa_mapa también unifica dinámicamente incluso si el alias no venía precomputado
    ruta_curado = tmp_path / "curado_baremo.json"
    ruta_curado.write_text(json.dumps(curado, ensure_ascii=False), encoding="utf-8")
    dir_mapa = fabrica_mapa(filas=[fila_baremo], curado={"nodes": [], "edges": []}, destino=tmp_path / "mapa_sin_alias")

    eng = LegalGraphifyEngine(doctrina_dir=str(tmp_path), usar_mapa=False)
    assert eng.cargar_grafo_json(str(ruta_curado))
    resumen = eng.cargar_capa_mapa(dir_mapa)
    assert resumen["fusionados"] >= 1
    nodos_baremo = [n for n, d in eng.graph.nodes(data=True) if d.get("node_type") == "baremo"]
    assert nodos_baremo == ["baremo_muerte_3"]


def test_grafo_curado_real_enriquecido_supera_55_pct_cobertura_normativa():
    if not os.path.exists(DEFAULT_GRAPH_PATH):
        pytest.skip("no existe data/legal_knowledge_graph.json")
    eng = LegalGraphifyEngine(usar_mapa=False)
    assert eng.cargar_grafo_json(DEFAULT_GRAPH_PATH)
    red = jurimetria.analizar_red_citaciones(motor=eng, top_k=5)
    cal = red["calidad_ontologica"]
    assert cal["instituciones_enlazadas_a_norma_pct"] >= 55.0
    assert cal["nodos_baremo_unicos"] == 17


def test_filtro_ruido_instituciones_toc_y_ocr():
    from legal_graphify import es_nodo_ruido_institucion

    assert es_nodo_ruido_institucion("Docentes", "Gabriel Autores") is True
    assert es_nodo_ruido_institucion("3.2.1   Discriminación", "3.2.2 \tDerecho") is True
    assert es_nodo_ruido_institucion("41 NOGUEIRA ALCALÁ, Humberto (2006), p. 386", "") is True
    assert es_nodo_ruido_institucion("Capítulo 4", "", obra="doctrina48981") is True
    assert es_nodo_ruido_institucion("La Simulación de los Actos Jurídicos", "Concertación entre las partes.") is False
    assert es_nodo_ruido_institucion("Tutela de Derechos Fundamentales", "Procedimiento laboral especial.") is False


def test_extractores_mapa_filtran_normas_ocr_fuera_de_rango():
    from mapa_corpus import extractores

    texto = "Conforme al Art. 19 N° 24 de la Constitución Política y el falso Art. 1682 de la Constitución."
    citas = extractores._citas(texto)
    ids_normas = [nid for nid, _ in citas["normas"]]
    assert "norma:cpr:19:n24" in ids_normas
    assert "norma:cpr:1682" not in ids_normas

    lista = extractores.normas_de_lista(["[CPR 1980 - Art. 19 N° 3]", "[CPR 1980 - Art. 1682]"])
    assert "norma:cpr:19:n3" in lista
    assert "norma:cpr:1682" not in lista


def test_busqueda_hibrida_doctrina_rrf_e_indexacion_vectorial(tmp_path):
    import doctrina_connector

    doc_dir = tmp_path / "doctrina_test"
    doc_dir.mkdir()
    (doc_dir / "laboral.md").write_text(
        "# Manual de Derecho del Trabajo\n\n"
        "**Tratadista:** Sergio Gamonal | **Área:** Derecho del Trabajo | **Materia:** Terminación\n\n"
        "## Tutela de Derechos Fundamentales y Despido con Licencia Médica\n"
        "**Definición Canónica:** Acción laboral frente a vulneración de la integridad psíquica o discriminación.\n"
        "**Operativa Procesal Forense:** Procedimiento de tutela laboral (Arts. 485 y ss. Código del Trabajo).\n"
        "**Concordancias Legales:** [BCN - Código del Trabajo, Art. 485]\n\n"
        "## Contrato de Compraventa Inmobiliaria\n"
        "**Definición Canónica:** Convención por la cual una parte se obliga a dar un inmueble y la otra a pagarlo en dinero.\n"
        "**Concordancias Legales:** [BCN - Código Civil, Art. 1793]\n",
        encoding="utf-8",
    )
    db_tmp = str(tmp_path / "doctrina_vec.db")
    n_idx = doctrina_connector.index_all_doctrina(doctrina_dir=str(doc_dir), db_path=db_tmp)
    assert n_idx == 2

    res_idx = doctrina_connector.indexar_doctrina_vectorial(db_path=db_tmp, use_fastembed=False)
    assert res_idx["indexadas"] == 2
    assert res_idx["dim"] > 0

    res_hib = doctrina_connector.search_doctrina(
        "vulneración integridad psíquica licencia médica laboral",
        limit=2,
        db_path=db_tmp,
        hibrido=True,
    )
    assert res_hib
    assert "Tutela" in res_hib[0]["institucion"]
    assert res_hib[0]["rrf_score"] > 0
    assert res_hib[0]["modo_busqueda"].startswith("hibrido_rrf:")


def test_notebook_jurimetria_duckdb_valido():
    nb_path = Path(__file__).resolve().parent.parent / "docs" / "investigacion_jurimetrica_duckdb.ipynb"
    assert nb_path.exists()
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    assert nb["nbformat"] == 4
    fuentes = "\n".join("".join(c.get("source", [])) for c in nb["cells"])
    assert "duckdb" in fuentes
    assert "cohen_kappa" in fuentes
    assert "baremo_dano_moral" in fuentes


# ── Pilar 2: Exportación Apache Parquet ───────────────────────────────────────────────────────
def test_exportar_parquet_hf_genera_tablas_tipadas_sin_rutas_privadas(tmp_path):
    pytest.importorskip("pyarrow")
    import pyarrow.parquet as pq
    from scripts.exportar_parquet_hf import exportar_parquet_completo

    eng = _motor_sintetico()
    grafo_tmp = tmp_path / "grafo_test.json"
    eng.guardar_grafo_json(str(grafo_tmp))

    salida = tmp_path / "parquet_out"
    manif = exportar_parquet_completo(
        carpeta_salida=salida,
        graph_path=str(grafo_tmp),
        db_path=tmp_path / "sin_db.db",
        usar_mapa=False,
    )
    assert manif["total_tablas"] >= 2
    assert (salida / "grafo_nodos.parquet").exists()
    assert (salida / "grafo_aristas.parquet").exists()
    assert (salida / "manifiesto_parquet.json").exists()

    # Verificar que no se filtre el directorio HOME ni rutas absolutas privadas
    texto_manif = (salida / "manifiesto_parquet.json").read_text(encoding="utf-8")
    assert "/home/" not in texto_manif

    t_nodos = pq.read_table(str(salida / "grafo_nodos.parquet"))
    t_aristas = pq.read_table(str(salida / "grafo_aristas.parquet"))
    assert t_nodos.num_rows == eng.graph.number_of_nodes()
    assert t_aristas.num_rows == eng.graph.number_of_edges()
    assert "pagerank_sustantivo" in t_nodos.column_names
    assert "es_sustantiva" in t_aristas.column_names


# ── Pilar 3: Jurimetría, Validación Humana y Paquete Reproducible + MCP ──────────────────────
def test_plausibilidad_normativa_y_normalizacion_resultados():
    assert jurimetria.es_articulo_plausible("norma:cpr:19:n24") is True
    assert jurimetria.es_articulo_plausible("norma:cpr:19-transitorio") is True
    assert jurimetria.es_articulo_plausible("norma:cpr:1682") is False
    assert jurimetria.es_articulo_plausible("norma:cc:0") is False
    assert jurimetria.es_articulo_plausible("norma:cc:1545") is True
    assert jurimetria.es_articulo_plausible("norma:ley-19300:10") is True

    assert jurimetria.normalizar_resultado_judicial("ACOGIDO") == "acoge"
    assert jurimetria.normalizar_resultado_judicial("NO SE HACE LUGAR") == "rechaza"
    assert jurimetria.normalizar_resultado_judicial("INADMISIBLE") == "inadmisible"
    assert jurimetria.normalizar_resultado_judicial("CASACIÓN DE OFICIO") == "casacion_oficio"
    assert jurimetria.normalizar_resultado_judicial("REVOCA") == "revoca"
    assert jurimetria.normalizar_resultado_judicial("CONFIRMA") == "confirma"


def test_jurimetria_red_citaciones_hits_y_auditoria_ocr():
    eng = _motor_sintetico()
    red = jurimetria.analizar_red_citaciones(motor=eng, top_k=5)
    assert red["metricas_red"]["aristas_sustantivas"] > 0
    assert red["metricas_red"]["aristas_bibliograficas"] > 0
    # Detecta y excluye el ruido OCR `norma:cpr:1682` del ranking de normas válidas
    assert red["calidad_ontologica"]["normas_ocr_fuera_de_rango_detectadas"] == 1
    ids_normas = [x["id"] for x in red["normas_mas_citadas"]]
    assert "norma:cc:1682" in ids_normas
    assert "norma:cpr:1682" not in ids_normas
    # HITS Authority real > 0 en la norma más citada
    art_1682 = next(x for x in red["normas_mas_citadas"] if x["id"] == "norma:cc:1682")
    assert art_1682["hits_authority"] > 0.0


def test_jurimetria_longitudinal_y_muestra_estratificada_determinista():
    lon = jurimetria.estadisticas_longitudinales(coleccion="cs", incluir_baremo=True)
    assert lon["universo_n"] >= 1
    assert len(lon["baremo_dano_moral_uf_clp"]) == 17
    assert any("Art. 3 inc. 2" in adv for adv in lon["advertencias_metodologicas"])

    m1 = jurimetria.generar_muestra_validacion_humana(coleccion="cs", n=15, semilla=42)
    m2 = jurimetria.generar_muestra_validacion_humana(coleccion="cs", n=15, semilla=42)
    assert m1["n_obtenido"] == m2["n_obtenido"] and m1["n_obtenido"] > 0
    assert [x["id"] for x in m1["muestra"]] == [x["id"] for x in m2["muestra"]]
    assert "codificador_1_resultado" in m1["muestra"][0]
    assert "codificador_2_resultado" in m1["muestra"][0]


def test_exportar_paquete_investigacion_reproducible(tmp_path):
    eng = _motor_sintetico()
    carpeta = tmp_path / "paquete_nulidad"
    res = jurimetria.exportar_paquete_investigacion(
        tema="Nulidad Absoluta",
        carpeta_salida=str(carpeta),
        incluir_muestra_validacion=True,
        n_muestra=10,
        semilla=42,
        motor=eng,
    )
    assert res["nodos_exportados"] >= 3
    assert (carpeta / "nodos_subgrafo.csv").exists()
    assert (carpeta / "aristas_subgrafo.csv").exists()
    assert (carpeta / "red_citaciones.graphml").exists()
    assert (carpeta / "estadisticas_longitudinales.json").exists()
    assert (carpeta / "METODOLOGIA_REPRODUCIBLE.md").exists()
    assert (carpeta / "referencia.bib").exists()

    # Verificar firma institucional Open Legal Chile y RAE en memoria metodológica y BibTeX
    md_txt = (carpeta / "METODOLOGIA_REPRODUCIBLE.md").read_text(encoding="utf-8")
    assert "Open Legal Chile" in md_txt
    assert "Art. 3 inc. 2" in md_txt
    bib_txt = (carpeta / "referencia.bib").read_text(encoding="utf-8")
    assert "@misc{openlegalchile_dataset_" in bib_txt


def test_mcp_herramientas_jurimetria_y_perfil_dogmatico(tmp_path):
    nombres_dog = {t["name"] for t in mcp_server.get_active_tools("dogmatico")}
    assert {"jurimetria_analizar_corpus", "jurimetria_exportar_investigacion"} <= nombres_dog

    res_lon = mcp_server.handle_tool_call(
        "jurimetria_analizar_corpus",
        {"modo": "longitudinal", "coleccion": "cs"},
    )
    assert "error" not in res_lon
    assert res_lon["universo_n"] >= 1

    res_exp = mcp_server.handle_tool_call(
        "jurimetria_exportar_investigacion",
        {"tema": "simulacion", "carpeta_salida": str(tmp_path / "exp_mcp"), "n_muestra": 5},
    )
    assert "error" not in res_exp
    assert (tmp_path / "exp_mcp" / "red_citaciones.graphml").exists()
    assert (tmp_path / "exp_mcp" / "referencia.bib").exists()
