"""Unión del mapa del corpus con LegalGraphify: la capa del mapa sobre el grafo curado.

El mapa es diminuto y se arma en disco con `fabrica_mapa` (tests/conftest.py); las consultas que
necesitan el índice (fallos de la Corte Suprema bajo demanda, roles, búsqueda de texto) usan un
cliente activo sobre ese mapa, sin red. Nada escribe archivos versionados: el grafo curado de
prueba vive en tmp_path y DEFAULT_GRAPH_PATH se reapunta antes de cualquier guardado. Lo rápido no
se mide en milisegundos: se prueba contando llamadas (un rol que el mapa no tiene no recorre la
doctrina).
"""

import json
import os
import re

import networkx as nx
import pytest

import legal_graphify
from legal_graphify import CAPA_MAPA, GrafoConCapaMapaError, LegalGraphifyEngine

from conftest import FILAS_MAPA_MINIMO

# Grafo curado mínimo, con la forma del artefacto del repositorio (Node-Link). Trae dos normas
# duplicadas que el mapa reconoce como la misma (Código Civil, Art. 2314), una ficha del TC con la
# cabecera de otra causa, una vía procesal a la que equivale un recurso de la CS y un fallo curado
# que el corpus sí tiene. Ninguna etiqueta ni definición dice «moral» (lo usa la búsqueda de texto).
CURADO = {
    "directed": True, "multigraph": False, "graph": {},
    "nodes": [
        {"id": "inst_responsabilidad_extracontractual", "label": "Responsabilidad extracontractual",
         "node_type": "institucion", "definicion": "Obligación de indemnizar el perjuicio causado por un hecho ilícito.",
         "autor": "Enrique Barros Bourie", "obra": "Tratado de responsabilidad extracontractual", "area": "Civil",
         "operativa_procesal": "Demanda ordinaria de indemnización de perjuicios.", "community": 0,
         "tokens_completos": 1500},
        {"id": "cons_aplicacion_art_2314", "label": "Considerando 5 (Rol 1-2020)", "node_type": "considerando_judicial",
         "community": 3},
        {"id": "norma_art_2314_cc", "label": "Código Civil, Art. 2314", "node_type": "articulo_legal", "community": 2},
        {"id": "norma_art_2314_del_codigo_civil", "label": "Art. 2314 del Código Civil", "node_type": "articulo_legal",
         "community": 2},
        {"id": "autor_enrique_barros", "label": "Enrique Barros Bourie", "node_type": "autor", "community": 1},
        {"id": "sent_tc_rol_n_2402_12_ina", "label": "TC · Rol N° 9999-12-INA — cabecera de otra causa",
         "node_type": "jurisprudencia_tc", "url": "https://buscador-backend.tcchile.cl/api/extended/2402/download",
         "community": "1"},
        {"id": "via_recurso_de_proteccion", "label": "Recurso De Proteccion", "node_type": "via_procesal", "community": 4},
        {"id": "fallo_cs_rol_n_1_234_2023", "label": "CS - Rol N° 1.234-2023", "node_type": "jurisprudencia",
         "community": 3},
    ],
    "edges": [
        {"source": "cons_aplicacion_art_2314", "target": "norma_art_2314_cc", "relation": "aplica_norma"},
        {"source": "inst_responsabilidad_extracontractual", "target": "norma_art_2314_cc", "relation": "fundamenta_en",
         "weight": 1.0},
        {"source": "inst_responsabilidad_extracontractual", "target": "norma_art_2314_del_codigo_civil",
         "relation": "fundamenta_en", "weight": 1.0},
        {"source": "inst_responsabilidad_extracontractual", "target": "autor_enrique_barros", "relation": "analizado_por",
         "weight": 1.0},
        {"source": "inst_responsabilidad_extracontractual", "target": "via_recurso_de_proteccion",
         "relation": "via_procesal", "weight": 1.0},
        {"source": "inst_responsabilidad_extracontractual", "target": "fallo_cs_rol_n_1_234_2023",
         "relation": "criterio_jurisprudencial", "weight": 1.0},
    ],
}

# Un fallo de la Corte Suprema que ninguna otra entrada cita: no es nodo del mapa, vive solo en el
# índice y se materializa por consulta.
FALLO_NO_CITADO = {
    "id": "cs:555-2022", "col": "cs", "ruta": "jurisprudencia_cs/2022/08/555-2022.md", "blob": "a" * 40,
    "bytes": 810, "fecha": "2022-08-17", "era": 2022, "rol": "555-2022", "titulo": "ROJAS CON ISAPRE",
    "sala": "sala:cs-3", "recurso": "recurso:proteccion", "recurso_txt": "PROTECCIÓN", "resultado": "REVOCA",
    "ministros": ["ministro:maria-gajardo-harboe"], "ministros_txt": ["MARÍA GAJARDO HARBOE"],
}
MINISTRA = "ministro:maria-gajardo-harboe"


def _escribir_curado(tmp_path, curado=None):
    ruta = tmp_path / "curado.json"
    ruta.write_text(json.dumps(curado or CURADO, ensure_ascii=False), encoding="utf-8")
    return str(ruta)


def _motor(tmp_path, curado=None, **kwargs):
    """Motor sobre el grafo curado de prueba, con la doctrina en una carpeta vacía: la búsqueda en
    el texto de la doctrina no encuentra nada y no lee el corpus real."""
    doctrina = tmp_path / "doctrina_vacia"
    doctrina.mkdir(exist_ok=True)
    motor = LegalGraphifyEngine(doctrina_dir=str(doctrina), **kwargs)
    assert motor.cargar_grafo_json(_escribir_curado(tmp_path, curado))
    return motor


def _foto(grafo):
    """Huella completa de un grafo (nodos, aristas y atributos), para comparar antes y después."""
    nodos = sorted((n, json.dumps(d, sort_keys=True, default=str)) for n, d in grafo.nodes(data=True))
    aristas = sorted((u, v, json.dumps(d, sort_keys=True, default=str)) for u, v, d in grafo.edges(data=True))
    return nodos, aristas


@pytest.fixture
def mapa_curado(fabrica_mapa):
    """Mapa diminuto armado con el grafo curado de prueba (alias y puentes incluidos)."""
    return fabrica_mapa(curado=CURADO)


@pytest.fixture
def cliente_mapa(fabrica_mapa, tmp_path, monkeypatch):
    """Cliente del mapa ACTIVO (sin red) sobre el mapa diminuto + un fallo de la CS que nadie cita."""
    from mapa_corpus import cliente

    destino = fabrica_mapa(filas=FILAS_MAPA_MINIMO + [FALLO_NO_CITADO], curado=CURADO,
                           destino=tmp_path / "mapa_con_fallo")
    monkeypatch.setenv("OPENLEGAL_MAPA", "")
    monkeypatch.setenv("OPENLEGAL_MAPA_LOCAL", str(destino))
    monkeypatch.setenv("OPENLEGAL_MAPA_DIR", str(tmp_path / "cache_mapa"))
    cliente.reiniciar_cliente()
    c = cliente.obtener_cliente()
    assert c.asegurar(bloquear=True, timeout=120), c.error
    yield c
    cliente.reiniciar_cliente()


@pytest.fixture
def motor_con_mapa(tmp_path, cliente_mapa):
    motor = _motor(tmp_path)
    motor.cargar_capa_mapa(cliente_mapa.directorio())
    return motor


# ── Unión ──────────────────────────────────────────────────────────────────────────────────────
def test_la_capa_se_superpone_sin_duplicar_los_alias(tmp_path, mapa_curado):
    motor = _motor(tmp_path)
    curados = set(motor.graph.nodes)
    resumen = motor.cargar_capa_mapa(mapa_curado)

    assert motor.origen_grafo == "mapa"
    assert {"nodos", "aristas", "segundos"} <= set(resumen)
    g = motor.graph
    # Lo curado sigue ahí, con sus IDs de siempre.
    assert curados <= set(g.nodes)
    # La norma del mapa no se duplica: sus aristas cuelgan de la curada (la primera de las dos
    # duplicadas, en orden de ID), que pasa a llevar su ID canónico.
    assert "norma:cc:2314" not in g
    assert g.nodes["norma_art_2314_cc"]["id_mapa"] == "norma:cc:2314"
    assert sum(1 for _, d in g.nodes(data=True) if d.get("id_mapa") == "norma:cc:2314") == 1
    assert g.edges["doc:revistas/rchd/2020/responsabilidad", "norma_art_2314_cc"]["relation"] == "cita_norma"
    assert g.edges["tc:2402", "norma_art_2314_cc"]["capa"] == CAPA_MAPA
    assert g.edges["norma_art_2314_cc", "norma:cc"]["relation"] == "parte_de"
    # El autor curado también se funde: las obras del mapa le cuelgan a él.
    assert "autor:barros_bourie_enrique" not in g
    assert g.has_edge("doc:revistas/rchd/2020/responsabilidad", "autor_enrique_barros")
    # Los nodos nuevos traen tipo, etiqueta, capa y comunidad del mapa.
    nuevos = [n for n, d in g.nodes(data=True) if d.get("capa") == CAPA_MAPA]
    assert len(nuevos) == resumen["nodos"] and resumen["fusionados"] >= 2
    for n in nuevos:
        d = g.nodes[n]
        assert d["node_type"] and d["label"] and "community" in d, n
    assert g.nodes["sala:cs-3"]["node_type"] == "sala"
    # La arista curada y la del mapa no se pisan: lo curado conserva su relación y no lleva capa.
    assert g.edges["inst_responsabilidad_extracontractual", "norma_art_2314_cc"].get("capa") is None
    # Un recurso de la CS equivale a la vía curada.
    assert g.edges["recurso:proteccion", "via_recurso_de_proteccion"]["relation"] == "equivale_a"


def test_las_fichas_sent_tc_no_se_funden_con_el_tc(tmp_path, mapa_curado):
    motor = _motor(tmp_path)
    motor.cargar_capa_mapa(mapa_curado)
    g = motor.graph
    assert g.nodes["tc:2402"].get("capa") == CAPA_MAPA
    curada = g.nodes["sent_tc_rol_n_2402_12_ina"]
    assert "id_mapa" not in curada
    assert g.edges["sent_tc_rol_n_2402_12_ina", "tc:2402"]["relation"] == "mismo_documento"
    assert curada["calidad_mapa"] == "cabecera_desalineada"
    assert curada["documento_oficial"] == "tc:2402"


def test_cargar_es_idempotente_y_quitar_deja_lo_curado_como_estaba(tmp_path, mapa_curado):
    motor = _motor(tmp_path)
    antes = _foto(motor.graph)
    primera = motor.cargar_capa_mapa(mapa_curado)
    nodos, aristas = motor.graph.number_of_nodes(), motor.graph.number_of_edges()

    segunda = motor.cargar_capa_mapa(mapa_curado)
    assert segunda.get("ya_cargada") is True
    assert (segunda["nodos"], segunda["aristas"]) == (primera["nodos"], primera["aristas"])
    assert (motor.graph.number_of_nodes(), motor.graph.number_of_edges()) == (nodos, aristas)

    assert motor.quitar_capa_mapa() is True
    assert motor.origen_grafo == "repo"
    assert _foto(motor.graph) == antes
    assert motor.quitar_capa_mapa() is False


def test_otra_revision_reemplaza_la_capa_anterior(tmp_path, fabrica_mapa):
    motor = _motor(tmp_path)
    antes = _foto(motor.graph)
    motor.cargar_capa_mapa(fabrica_mapa(curado=CURADO))
    otra = fabrica_mapa(filas=FILAS_MAPA_MINIMO[:2], curado=CURADO, destino=tmp_path / "otra_revision")
    motor.cargar_capa_mapa(otra)
    g = motor.graph
    assert "tc:2402" not in g  # solo estaba en la revisión anterior
    assert "cs:10641-2024" not in g and "sala:cs-3" in g
    motor.quitar_capa_mapa()
    assert _foto(motor.graph) == antes


def test_cargar_grafo_json_sin_ruta_sigue_cargando_el_artefacto_del_repo(tmp_path, monkeypatch, mapa_curado):
    ruta = _escribir_curado(tmp_path)
    monkeypatch.setattr(legal_graphify, "DEFAULT_GRAPH_PATH", ruta)
    motor = LegalGraphifyEngine(doctrina_dir=str(tmp_path))
    assert motor.cargar_grafo_json()
    motor.cargar_capa_mapa(mapa_curado)
    # Recargar el artefacto reemplaza el grafo: la capa se va y el origen vuelve a "repo".
    assert motor.cargar_grafo_json()
    assert motor.origen_grafo == "repo"
    assert not any(d.get("capa") == CAPA_MAPA for _, d in motor.graph.nodes(data=True))
    assert motor.graph.number_of_nodes() == len(CURADO["nodes"])


# ── Guardado ───────────────────────────────────────────────────────────────────────────────────
def test_no_se_vuelca_la_capa_al_artefacto_versionado(tmp_path, monkeypatch, mapa_curado):
    versionado = tmp_path / "data" / "legal_knowledge_graph.json"
    monkeypatch.setattr(legal_graphify, "DEFAULT_GRAPH_PATH", str(versionado))
    motor = _motor(tmp_path)
    motor.cargar_capa_mapa(mapa_curado)

    with pytest.raises(GrafoConCapaMapaError):
        motor.guardar_grafo_json(legal_graphify.DEFAULT_GRAPH_PATH)
    assert not versionado.exists()
    # El artefacto del repositorio queda protegido aunque DEFAULT_GRAPH_PATH apunte a otro lado
    # (se comprueba sin escribir nada).
    assert legal_graphify._es_grafo_versionado(legal_graphify._GRAFO_VERSIONADO)
    # Un respaldo en otra ruta sí se puede escribir, con la capa adentro.
    respaldo = tmp_path / "respaldo.json"
    motor.guardar_grafo_json(str(respaldo))
    assert "norma:cc" in respaldo.read_text(encoding="utf-8")
    # Sin la capa, el artefacto se guarda como siempre.
    motor.quitar_capa_mapa()
    motor.guardar_grafo_json(legal_graphify.DEFAULT_GRAPH_PATH)
    assert versionado.exists()


def test_la_ingesta_en_lote_con_la_capa_no_escribe_el_artefacto(tmp_path, monkeypatch, mapa_curado):
    versionado = tmp_path / "versionado.json"
    monkeypatch.setattr(legal_graphify, "DEFAULT_GRAPH_PATH", str(versionado))
    motor = _motor(tmp_path)
    motor.cargar_capa_mapa(mapa_curado)
    with pytest.raises(GrafoConCapaMapaError):
        motor.guardar_grafo_json(str(versionado))
    assert not versionado.exists()


# ── Ingesta local con la capa ──────────────────────────────────────────────────────────────────
DOCTRINA_LOCAL = """# Tratado de la imprevisión contractual

**Tratadista:** Autora de Prueba | **Área:** Derecho Civil | **Materia:** Contratos

## Teoría de la imprevisión
**Definición Canónica:** Revisión judicial del contrato cuando un hecho sobreviniente lo vuelve excesivamente oneroso.
**Concordancias Legales:** [BCN - Código Civil, Art. 1545]
"""

DOCTRINA_LOCAL_2 = """# Estudio de la fuerza mayor

**Tratadista:** Autor de Prueba | **Área:** Derecho Civil | **Materia:** Obligaciones

## Fuerza mayor contractual
**Definición Canónica:** Imprevisto imposible de resistir que exime de responsabilidad al deudor.
**Concordancias Legales:** [BCN - Código Civil, Art. 45]
"""


def test_la_ingesta_local_sigue_visible_con_la_capa(tmp_path, mapa_curado):
    motor = _motor(tmp_path)
    local = tmp_path / "doctrina_vacia" / "imprevision.md"
    local.write_text(DOCTRINA_LOCAL, encoding="utf-8")
    motor.incorporar_archivo_doctrina(str(local))
    assert motor.graph.has_node("inst_teoria_de_la_imprevision")

    motor.cargar_capa_mapa(mapa_curado)
    assert motor.graph.has_node("inst_teoria_de_la_imprevision")
    assert motor.consultar_subgrafo("teoria de la imprevision")["nodo_id"] == "inst_teoria_de_la_imprevision"

    # Y lo que se ingiere con la capa ya cargada también queda a la vista, sin tocar la capa.
    capa = sum(1 for _, d in motor.graph.nodes(data=True) if d.get("capa") == CAPA_MAPA)
    otro = tmp_path / "doctrina_vacia" / "fuerza_mayor.md"
    otro.write_text(DOCTRINA_LOCAL_2, encoding="utf-8")
    motor.incorporar_archivo_doctrina(str(otro))
    assert motor.consultar_subgrafo("fuerza mayor contractual")["nodo_id"] == "inst_fuerza_mayor_contractual"
    assert motor.origen_grafo == "mapa"
    assert sum(1 for _, d in motor.graph.nodes(data=True) if d.get("capa") == CAPA_MAPA) == capa

    # Al quitar la capa, lo ingerido se queda.
    motor.quitar_capa_mapa()
    assert motor.graph.has_node("inst_teoria_de_la_imprevision")
    assert motor.graph.has_node("inst_fuerza_mayor_contractual")


def test_una_arista_curada_sobre_una_del_mapa_no_cambia_las_demas(tmp_path, mapa_curado):
    """Los atributos de las aristas del mapa son compartidos: afirmar una desde lo curado no puede
    modificar las otras cientos que comparten su diccionario."""
    motor = _motor(tmp_path)
    motor.cargar_capa_mapa(mapa_curado)
    g = motor.graph
    u, v = "doc:revistas/rchd/2020/responsabilidad", "autor_enrique_barros"
    hermanas = [(a, b) for a, b, d in g.edges(data=True) if d is g.edges[u, v] and (a, b) != (u, v)]
    antes = [dict(g.edges[a, b]) for a, b in hermanas]
    motor._agregar_arista(u, v, relation="escrito_por", weight=1.0)
    assert g.edges[u, v].get("capa") is None
    assert [dict(g.edges[a, b]) for a, b in hermanas] == antes


# ── Búsqueda en el grafo ───────────────────────────────────────────────────────────────────────
def test_un_rol_que_el_mapa_no_tiene_da_none_sin_recorrer_la_doctrina(motor_con_mapa, monkeypatch):
    llamadas = []
    monkeypatch.setattr(motor_con_mapa, "_buscar_por_corpus", lambda q: llamadas.append(q))
    assert motor_con_mapa._buscar_nodo_relevante("Rol 4321-2020") is None
    res = motor_con_mapa.consultar_subgrafo("Rol N° 4.321-2020")
    assert res["encontrado"] is False
    assert "no está en el mapa" in res["mensaje"]
    assert llamadas == []
    # Un rol que sí está (y es nodo, porque otra entrada lo cita) se resuelve directo.
    assert motor_con_mapa._buscar_nodo_relevante("Rol 10641-2024") == "cs:10641-2024"
    assert llamadas == []


def test_un_fallo_curado_que_el_mapa_no_tiene_se_sigue_encontrando(tmp_path, cliente_mapa, monkeypatch):
    """La CS del mapa cubre dos años; los fallos antiguos citados en la doctrina viven en el curado."""
    curado = json.loads(json.dumps(CURADO))
    curado["nodes"].append({"id": "fallo_rol_n_4_821_2019", "label": "Rol N° 4.821-2019",
                            "node_type": "jurisprudencia", "community": 3})
    curado["edges"].append({"source": "inst_responsabilidad_extracontractual", "target": "fallo_rol_n_4_821_2019",
                            "relation": "criterio_jurisprudencial", "weight": 1.0})
    motor = _motor(tmp_path, curado)
    sin_mapa = motor._buscar_nodo_relevante("Rol N° 4.821-2019")
    motor.cargar_capa_mapa(cliente_mapa.directorio())
    llamadas = []
    monkeypatch.setattr(motor, "_buscar_por_corpus", lambda q: llamadas.append(q))
    assert sin_mapa == "fallo_rol_n_4_821_2019"
    assert motor._buscar_nodo_relevante("Rol N° 4.821-2019") == sin_mapa
    assert motor.consultar_subgrafo("Rol N° 4.821-2019")["encontrado"] is True
    assert llamadas == []


def test_la_institucion_exacta_gana_a_la_norma_del_mapa(tmp_path, cliente_mapa):
    curado = json.loads(json.dumps(CURADO))
    curado["nodes"].append({"id": "inst_hecho_ilicito_art_2314_cc", "label": "Hecho ilícito (Art. 2314 CC)",
                            "node_type": "institucion", "community": 0})
    curado["edges"].append({"source": "inst_hecho_ilicito_art_2314_cc", "target": "norma_art_2314_cc",
                            "relation": "fundamenta_en", "weight": 1.0})
    motor = _motor(tmp_path, curado)
    assert motor._buscar_nodo_relevante("Hecho ilícito (Art. 2314 CC)") == "inst_hecho_ilicito_art_2314_cc"
    motor.cargar_capa_mapa(cliente_mapa.directorio())
    assert motor._buscar_nodo_relevante("Hecho ilícito (Art. 2314 CC)") == "inst_hecho_ilicito_art_2314_cc"


def test_un_rol_sin_mapa_sigue_el_flujo_de_siempre(tmp_path, monkeypatch):
    motor = _motor(tmp_path)
    llamadas = []
    monkeypatch.setattr(motor, "_buscar_por_corpus", lambda q: llamadas.append(q))
    motor._buscar_nodo_relevante("Rol 4321-2020")
    assert llamadas == ["Rol 4321-2020"]


def test_alias_ids_canonicos_y_nombres_del_mapa(motor_con_mapa):
    buscar = motor_con_mapa._buscar_nodo_relevante
    # ID canónico de un nodo fundido → el curado; ID legado → él mismo.
    assert buscar("norma:cc:2314") == "norma_art_2314_cc"
    assert buscar("autor:barros_bourie_enrique") == "autor_enrique_barros"
    # Una norma citada como tal.
    assert buscar("artículo 2314 del Código Civil") == "norma_art_2314_cc"
    # Nombre exacto de una entidad del mapa, con o sin el tratamiento.
    assert buscar("María Gajardo Harboe") == MINISTRA
    assert buscar("ministra María Gajardo Harboe") == MINISTRA
    assert buscar("Revista Chilena de Derecho") == "revista:rchd"
    # Un fallo que vive solo en el índice: su ID canónico, para materializarlo.
    assert buscar("Rol 555-2022") == "cs:555-2022"


def test_las_normas_curadas_prefieren_la_institucion(tmp_path, mapa_curado):
    # Sin mapa, el primer predecesor de la norma es el considerando (va primero en el artefacto).
    motor = _motor(tmp_path)
    assert motor._buscar_nodo_relevante("art. 2314") == "cons_aplicacion_art_2314"
    # Con la capa, entre sus predecesores (ahora también documentos del mapa) gana la institución.
    motor.cargar_capa_mapa(mapa_curado)
    assert motor._buscar_nodo_relevante("art. 2314") == "inst_responsabilidad_extracontractual"


def test_la_busqueda_de_texto_del_mapa_es_el_ultimo_paso_y_avisa(motor_con_mapa):
    nodo = motor_con_mapa._buscar_nodo_relevante("daño moral")
    assert nodo == "doc:revistas/rchd/2020/responsabilidad"
    assert any("TEXTO" in a and "mapa del corpus" in a for a in motor_con_mapa.advertencias)


# ── Fallos de la CS bajo demanda ───────────────────────────────────────────────────────────────
def test_los_fallos_cs_se_materializan_en_una_vista_sin_tocar_el_grafo(motor_con_mapa):
    antes = _foto(motor_con_mapa.graph)
    res = motor_con_mapa.consultar_subgrafo(MINISTRA)
    assert res["encontrado"] is True and res["capa"] == CAPA_MAPA and res["tipo"] == "ministro"
    assert res["fallos_cs_total"] == 3
    assert [f["id"] for f in res["fallos_cs"]] == ["cs:10641-2024", "cs:1234-2023", "cs:555-2022"]
    assert res["fallos_cs"][0]["cita"] == "[CS - Rol N° 10.641-2024, Fecha: 04-03-2026]"
    assert "fallos_cs_total: 3" in res["subgrafo_resumen_yaml"]
    assert "ROJAS CON ISAPRE" in res["subgrafo_resumen_yaml"]
    # El fallo que nadie cita aparece en la consulta, pero el grafo compartido no cambió.
    assert "cs:555-2022" not in motor_con_mapa.graph
    assert _foto(motor_con_mapa.graph) == antes
    vista = motor_con_mapa.vista_mapa(MINISTRA)
    assert vista is not None and vista.has_edge("cs:555-2022", MINISTRA)
    vista.add_node("basura")
    assert "basura" not in motor_con_mapa.graph


def test_el_resultado_no_depende_del_orden_de_las_consultas(tmp_path, cliente_mapa):
    consultas = [MINISTRA, "sala:cs-3", "recurso:proteccion", "norma:cc:2314", "Rol 555-2022"]
    uno, dos = _motor(tmp_path), _motor(tmp_path)
    for motor in (uno, dos):
        motor.cargar_capa_mapa(cliente_mapa.directorio())
    ida = {q: uno.consultar_subgrafo(q) for q in consultas}
    vuelta = {q: dos.consultar_subgrafo(q) for q in reversed(consultas)}
    repetida = {q: uno.consultar_subgrafo(q) for q in consultas}
    assert ida == vuelta == repetida
    assert _foto(uno.graph) == _foto(dos.graph)


def test_un_fallo_que_nadie_cita_tiene_su_ficha(motor_con_mapa):
    res = motor_con_mapa.consultar_subgrafo("Rol 555-2022")
    assert res["encontrado"] is True
    assert res["nodo_id"] == "cs:555-2022" and res["tipo"] == "sentencia_cs"
    ficha = res["subgrafo_resumen_yaml"]
    assert ficha.startswith('sentencia_cs: "ROJAS CON ISAPRE"')
    assert "Corte Suprema, Sala 3" in ficha and "REVOCA" in ficha
    assert res["metricas_tokens"]["tokens_texto_completo"] > 0
    assert res["url_huggingface"].endswith("/jurisprudencia_cs/2022/08/555-2022.md")
    assert "cs:555-2022" not in motor_con_mapa.graph


def test_explicar_e_impacto_de_un_nodo_del_mapa(motor_con_mapa):
    exp = motor_con_mapa.explicar_institucion("sala:cs-3")
    assert exp["encontrado"] is True and exp["capa"] == CAPA_MAPA
    assert exp["fallos_cs_total"] == 2  # 10641-2024 y 555-2022
    assert "Jurisprudencia de la Corte Suprema (2 fallos" in exp["explicacion_markdown"]
    assert "[CS - Rol N° 555-2022, Fecha: 17-08-2022]" in exp["explicacion_markdown"]

    imp = motor_con_mapa.analizar_impacto_normativo("norma:cc:2314")
    assert imp["encontrado"] is True and imp["capa"] == CAPA_MAPA
    directos = {x["id"] for x in imp["impacto_directo"]}
    assert {"tc:2402", "doc:revistas/rchd/2020/responsabilidad", "inst_responsabilidad_extracontractual"} <= directos
    assert imp["metricas_impacto"]["fallos_cs_grado_1"] == 0  # ningún fallo de la CS la cita
    assert imp == motor_con_mapa.analizar_impacto_normativo("norma:cc:2314")


def test_sin_indice_los_fallos_cs_no_se_inventan(tmp_path, mapa_curado):
    """Con la capa cargada pero sin cliente del mapa, el total de fallos no es «0»: es desconocido."""
    motor = _motor(tmp_path)
    motor.cargar_capa_mapa(mapa_curado)
    res = motor.consultar_subgrafo(MINISTRA)
    assert res["encontrado"] is True
    assert res["fallos_cs_total"] is None and res["fallos_cs"] == []
    assert "sin índice del mapa" in res["subgrafo_resumen_yaml"]


# ── La ficha curada no cambia ──────────────────────────────────────────────────────────────────
def test_la_ficha_de_simulacion_queda_intacta_con_la_capa(fabrica_mapa, tmp_path):
    if not os.path.exists(legal_graphify.DEFAULT_GRAPH_PATH):
        pytest.skip("no hay grafo curado construido")
    motor = LegalGraphifyEngine()
    assert motor.cargar_grafo_json(legal_graphify.DEFAULT_GRAPH_PATH)
    sin_mapa = {h: motor.consultar_subgrafo("simulacion", max_hops=h) for h in (1, 2)}
    centro = sin_mapa[1]["nodo_id"]

    # Un mapa que cuelga documentos, normas y un fallo de los vecinos curados de la simulación.
    vecinos = set(motor.graph.successors(centro)) | set(motor.graph.predecessors(centro)) | {centro}
    curado = {"nodes": [dict(motor.graph.nodes[n], id=n) for n in sorted(vecinos)],
              "edges": [{"source": u, "target": v, **d} for u, v, d in motor.graph.edges(data=True)
                        if u in vecinos and v in vecinos]}
    doc = {"id": "doc:revistas/rchd/2021/simulacion", "col": "doc", "sub": "revistas", "revista": "revista:rchd",
           "ruta": "doctrina/revistas/rchd/2021/simulacion.md", "blob": "1" * 40, "bytes": 4000,
           "titulo": "La simulación de los actos jurídicos", "normas": [["norma:cc:1707", 3], ["norma:cc:1712", 1]],
           "autores": ["autor:vial_del_rio_victor"], "autores_txt": ["Víctor Vial del Río"],
           "cita_cs": ["cs:22105-2019"]}
    fallo = {"id": "cs:22105-2019", "col": "cs", "ruta": "jurisprudencia_cs/2020/05/22105-2019.md", "blob": "2" * 40,
             "bytes": 700, "fecha": "2020-05-04", "rol": "22105-2019", "titulo": "FISCO CON PÉREZ",
             "sala": "sala:cs-1", "recurso": "recurso:casacion-en-el-fondo", "recurso_txt": "CASACIÓN FONDO"}
    mapa = fabrica_mapa(filas=FILAS_MAPA_MINIMO + [doc, fallo], curado=curado, destino=tmp_path / "mapa_simulacion")
    resumen = motor.cargar_capa_mapa(mapa)
    assert resumen["fusionados"] >= 2  # las normas curadas vecinas llevan ahora aristas del mapa

    for h, antes in sin_mapa.items():
        con_mapa = motor.consultar_subgrafo("simulacion", max_hops=h)
        assert con_mapa["nodo_id"] == antes["nodo_id"]
        assert con_mapa["subgrafo_resumen_yaml"] == antes["subgrafo_resumen_yaml"]
        assert con_mapa["metricas_tokens"] == antes["metricas_tokens"]
        assert set(con_mapa) == set(antes)  # ninguna clave nueva en una ficha curada


# ── Mermaid y caminos ──────────────────────────────────────────────────────────────────────────
def test_mermaid_usa_alias_y_respeta_el_tope(motor_con_mapa, monkeypatch):
    diagrama = motor_con_mapa.exportar_subgrafo_mermaid("sala:cs-3")
    nodos = re.findall(r"^\s+(\S+)\[\"", diagrama, re.MULTILINE)
    assert nodos and all(re.fullmatch(r"n\d+", n) for n in nodos)
    assert "sala:cs-3" not in diagrama.replace("Corte Suprema, Sala 3", "")
    assert "classDef mapa" in diagrama
    monkeypatch.setattr(legal_graphify, "TOPE_NODOS_MERMAID", 3)
    recortado = motor_con_mapa.exportar_subgrafo_mermaid("sala:cs-3")
    assert len(re.findall(r"^\s+n\d+\[\"", recortado, re.MULTILINE)) == 3
    assert "quedaron fuera del diagrama" in recortado


def test_mermaid_sin_mapa_conserva_nodos_y_aristas(tmp_path, monkeypatch):
    motor = _motor(tmp_path)
    diagrama = motor.exportar_subgrafo_mermaid("responsabilidad extracontractual")
    etiquetas = re.findall(r'^\s+(\w+)\["([^"]+)"\]', diagrama, re.MULTILINE)
    # Los mismos 6 nodos y 5 aristas que el diagrama de siempre, con sus IDs de siempre: la
    # institución y sus 5 vecinos (el considerando queda a 2 saltos y la ficha del TC no tiene
    # aristas en el curado).
    assert sorted(etiquetas) == sorted([
        ("inst_responsabilidad_extracontractual", "Responsabilidad extracontractual"),
        ("norma_art_2314_cc", "Código Civil, Art. 2314"),
        ("norma_art_2314_del_codigo_civil", "Art. 2314 del Código Civil"),
        ("autor_enrique_barros", "Enrique Barros Bourie"), ("via_recurso_de_proteccion", "Recurso De Proteccion"),
        ("fallo_cs_rol_n_1_234_2023", "CS - Rol N° 1.234-2023")])
    assert diagrama.count("-->") == 5
    # Sin la capa del mapa tampoco hay tope: el diagrama de siempre, completo.
    monkeypatch.setattr(legal_graphify, "TOPE_NODOS_MERMAID", 3)
    assert motor.exportar_subgrafo_mermaid("responsabilidad extracontractual") == diagrama


def test_el_camino_se_cachea_y_se_invalida_al_cambiar_el_grafo(tmp_path):
    motor = _motor(tmp_path)
    res = motor.encontrar_camino("Responsabilidad extracontractual", "Recurso De Proteccion")
    assert res["encontrado"] is True
    cacheada = motor._no_dirigido()
    assert motor._no_dirigido() is cacheada
    # Un nodo suelto no tiene camino; al enlazarlo (aun por fuera del motor), la caché se rehace.
    motor.graph.add_node("inst_aislada", label="Institución aislada", node_type="institucion")
    motor.instituciones_index["institucion aislada"] = "inst_aislada"
    assert motor.encontrar_camino("Institución aislada", "Recurso De Proteccion")["encontrado"] is False
    motor.graph.add_edge("inst_aislada", "via_recurso_de_proteccion", relation="via_procesal")
    assert motor.encontrar_camino("Institución aislada", "Recurso De Proteccion")["encontrado"] is True
    assert motor._no_dirigido() is not cacheada


def test_el_camino_cacheado_es_el_mismo_que_el_de_siempre():
    if not os.path.exists(legal_graphify.DEFAULT_GRAPH_PATH):
        pytest.skip("no hay grafo curado construido")
    motor = LegalGraphifyEngine()
    assert motor.cargar_grafo_json(legal_graphify.DEFAULT_GRAPH_PATH)
    a, b = motor._buscar_nodo_relevante("simulacion"), motor._buscar_nodo_relevante("nulidad absoluta")
    de_siempre = list(nx.all_shortest_paths(motor.graph.to_undirected(), a, b))[:3]
    res = motor.encontrar_camino("simulacion", "nulidad absoluta")
    assert [c["nodos"] for c in res["caminos"]] == [[motor.graph.nodes[n].get("label", n) for n in p] for p in de_siempre]


# ── Motor compartido y carga perezosa ──────────────────────────────────────────────────────────
def test_el_motor_compartido_es_uno_por_proceso():
    # mcp_server y modulo_ambiental guardan el motor del proceso al importarse: al terminar se
    # devuelve ese mismo, o las pruebas que vienen después verían dos motores distintos.
    original = legal_graphify.obtener_motor_compartido()
    legal_graphify.reiniciar_motor_compartido()
    try:
        uno = legal_graphify.obtener_motor_compartido()
        assert uno is legal_graphify.obtener_motor_compartido()
        assert uno.usar_mapa is True and uno.origen_grafo == "repo"  # nada se carga al pedirlo
        legal_graphify.reiniciar_motor_compartido()
        assert legal_graphify.obtener_motor_compartido() is not uno
    finally:
        with legal_graphify._MOTOR_COMPARTIDO_LOCK:
            legal_graphify._MOTOR_COMPARTIDO = original


def test_la_capa_se_sube_en_la_primera_consulta_que_la_necesita(tmp_path, cliente_mapa):
    motor = _motor(tmp_path, usar_mapa=True)
    assert motor.origen_grafo == "repo"
    res = motor.consultar_subgrafo(MINISTRA)
    assert motor.origen_grafo == "mapa"
    assert res["encontrado"] is True and res["fallos_cs_total"] == 3
    # Un motor suelto (sin usar_mapa) no la sube nunca.
    suelto = _motor(tmp_path)
    suelto.consultar_subgrafo("responsabilidad extracontractual")
    assert suelto.origen_grafo == "repo"


def test_con_el_mapa_apagado_no_hay_capa(tmp_path):
    """La suite corre con OPENLEGAL_MAPA=off: el motor compartido se comporta como siempre."""
    motor = _motor(tmp_path, usar_mapa=True)
    assert motor.subir_capa_mapa() is False
    res = motor.consultar_subgrafo("responsabilidad extracontractual")
    assert motor.origen_grafo == "repo"
    assert "capa" not in res and "fallos_cs" not in res
