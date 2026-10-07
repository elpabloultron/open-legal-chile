"""
Ingesta incremental de doctrina (doctrina_ingestar_documento).

Antes, ingerir un documento reindexaba todo doctrina.db y reconstruía el grafo desde el corpus
completo (~167 s, casi todo en la modularidad del grafo), y de paso borraba del grafo publicado
los nodos que no vienen de doctrina/. Estas pruebas fijan el comportamiento incremental: solo
se indexa el documento nuevo, sus nodos se agregan al grafo existente y nada se reconstruye.

Todo ocurre en tmp_path: ninguna prueba escribe en doctrina/, data/ ni doctrina.db.
"""

import json
import sqlite3

import pytest

import doc2md_ingestor
import doctrina_connector
import mcp_server
from doctrina_connector import index_all_doctrina, index_doctrina_file, search_doctrina
from legal_graphify import LegalGraphifyEngine
from mcp_server import handle_tool_call

DOC_PREVIO = """# TRATADO DE PRUEBA DOGMÁTICA
**Tratadista:** Jurista Previo | **Área:** Derecho Civil | **Materia:** Cuasicontratos

---

## 🏛️ Enriquecimiento sin Causa
**Definición Canónica:**
Atribución patrimonial sin justificación jurídica legítima que impone la obligación de restituir.

**Concordancias Legales:** `[BCN - Código Civil, Art. 1545]` `[BCN - Código Civil, Art. 2295]`
**Criterio Jurisprudencial Rector:** `[CS - Rol N° 1.234-2021]`
"""

DOC_NUEVO = (
    "Tratado de Derecho Civil.\n\n"
    "## 🏛️ Teoría de la Imprevisión\n"
    "**Definición Canónica:**\n"
    "Facultad del deudor de solicitar la revisión judicial de las prestaciones cuando sobrevienen "
    "circunstancias extraordinarias.\n"
    "**Concordancias Legales:** `[BCN - Código Civil, Art. 1545]`\n"
    "**Criterio Jurisprudencial Rector:** `[CS - Rol N° 12.345-2023]`\n"
)

NODO_AJENO = "stc_rol_9999_2024"  # p. ej. jurisprudencia TC: no sale de doctrina/


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    """Corpus, doctrina.db y grafo publicados en miniatura, todos bajo tmp_path."""
    doctrina = tmp_path / "doctrina"
    (doctrina / "civil").mkdir(parents=True)
    (doctrina / "civil" / "previo.md").write_text(DOC_PREVIO, encoding="utf-8")
    db = tmp_path / "doctrina.db"
    grafo = tmp_path / "legal_knowledge_graph.json"

    monkeypatch.setattr(doctrina_connector, "DOCTRINA_DIR", str(doctrina))
    monkeypatch.setattr(doctrina_connector, "DB_PATH", str(db))
    monkeypatch.setattr(doc2md_ingestor, "DOCTRINA_DIR", str(doctrina))
    monkeypatch.setattr(doc2md_ingestor, "DEFAULT_GRAPH_PATH", str(grafo))

    motor = LegalGraphifyEngine(doctrina_dir=str(doctrina))
    motor.construir_grafo_desde_doctrina()
    motor.graph.add_node(NODO_AJENO, label="STC Rol N° 9999-2024", node_type="jurisprudencia_tc", community=7)
    motor.guardar_grafo_json(str(grafo))

    index_all_doctrina(doctrina_dir=str(doctrina), db_path=str(db))

    # El motor vivo del servidor ya precalentado (cargó el grafo publicado), pero uno propio de
    # la prueba: así no se contamina el del proceso.
    vivo = LegalGraphifyEngine(doctrina_dir=str(doctrina))
    assert vivo.cargar_grafo_json(str(grafo))
    monkeypatch.setattr(mcp_server, "legal_graphify_engine", vivo)

    fuente = tmp_path / "imprevision.txt"
    fuente.write_text(DOC_NUEVO, encoding="utf-8")
    return {"doctrina": doctrina, "db": db, "grafo": grafo, "fuente": fuente}


def _prohibir_reconstruccion(monkeypatch):
    def _no(*_a, **_k):
        raise AssertionError("la ingesta de un documento no debe reconstruir el índice ni el grafo")

    monkeypatch.setattr(doctrina_connector, "index_all_doctrina", _no)
    monkeypatch.setattr(LegalGraphifyEngine, "construir_grafo_desde_doctrina", _no)
    monkeypatch.setattr(LegalGraphifyEngine, "_detectar_comunidades", _no)


def _filas_de(db, ruta):
    conn = sqlite3.connect(db)
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM doctrina_instituciones WHERE filepath = ?;", (str(ruta),)
        ).fetchone()[0]
    finally:
        conn.close()


def test_ingesta_incremental_no_reconstruye_y_es_buscable(entorno, monkeypatch):
    _prohibir_reconstruccion(monkeypatch)

    res = handle_tool_call("doctrina_ingestar_documento", {
        "file_path": str(entorno["fuente"]),
        "area": "civil",
        "tratadista": "René Ramos Pazos",
        "obra": "De las Obligaciones",
    })

    assert res["status"] == "success", res
    assert res["fts_actualizado"] is True
    assert res["grafo_actualizado"] is True
    assert "advertencias" not in res
    assert res["instituciones_indexadas_fts"] >= 1
    assert res["nodos_agregados_grafo"] >= 1
    md = entorno["doctrina"] / "civil" / "imprevision.md"
    assert res["markdown_path"] == str(md) and md.exists()

    # doctrina_search encuentra el documento recién ingerido, y el corpus previo sigue indexado.
    nuevo = handle_tool_call("doctrina_search", {"query": "imprevisión"})["resultados"]
    assert any(r["institucion"] == "Teoría de la Imprevisión" and r["autor"] == "René Ramos Pazos" for r in nuevo)
    previo = handle_tool_call("doctrina_search", {"query": "enriquecimiento"})["resultados"]
    assert any(r["autor"] == "Jurista Previo" for r in previo)

    # El grafo publicado ganó los nodos del documento y conservó los que no vienen de doctrina/.
    datos = json.loads(entorno["grafo"].read_text(encoding="utf-8"))
    nodos = {n["id"]: n for n in datos["nodes"]}
    assert NODO_AJENO in nodos and nodos[NODO_AJENO]["community"] == 7
    assert "inst_enriquecimiento_sin_causa" in nodos
    inst = nodos.get("inst_teoria_de_la_imprevision")
    assert inst is not None and inst["autor"] == "René Ramos Pazos"
    assert isinstance(inst["community"], int)
    aristas = {(e["source"], e["target"]) for e in datos["edges"]}
    # Comparte el Art. 1545 con la institución previa: la conexión cruzada también es incremental.
    assert ("inst_enriquecimiento_sin_causa", "inst_teoria_de_la_imprevision") in aristas

    # El motor vivo del servidor también lo ve, sin reiniciar.
    assert mcp_server.legal_graphify_engine.graph.has_node("inst_teoria_de_la_imprevision")


def test_reingesta_no_duplica_filas_fts(entorno):
    args = {"file_path": str(entorno["fuente"]), "area": "civil", "actualizar_grafo": False}
    res1 = handle_tool_call("doctrina_ingestar_documento", args)
    md = res1["markdown_path"]
    filas = _filas_de(entorno["db"], md)
    total = res1["total_instituciones_fts"]
    assert filas >= 1

    res2 = handle_tool_call("doctrina_ingestar_documento", args)
    assert res2["markdown_path"] == md
    assert _filas_de(entorno["db"], md) == filas
    assert res2["total_instituciones_fts"] == total


def test_index_doctrina_file_con_indice_vacio_indexa_el_corpus_primero(tmp_path, monkeypatch):
    doctrina = tmp_path / "doctrina"
    (doctrina / "civil").mkdir(parents=True)
    (doctrina / "civil" / "previo.md").write_text(DOC_PREVIO, encoding="utf-8")
    monkeypatch.setattr(doctrina_connector, "DOCTRINA_DIR", str(doctrina))
    db = str(tmp_path / "doctrina.db")

    nuevo = tmp_path / "fuera_del_corpus.md"
    nuevo.write_text(DOC_PREVIO.replace("Enriquecimiento sin Causa", "Pago de lo No Debido")
                     .replace("Jurista Previo", "Jurista Nuevo"), encoding="utf-8")

    res = index_doctrina_file(str(nuevo), db_path=db)

    assert res == {"indexadas": 1, "reemplazadas": 0, "total": 2}
    assert any(r["autor"] == "Jurista Previo" for r in search_doctrina("enriquecimiento", db_path=db))
    assert any(r["autor"] == "Jurista Nuevo" for r in search_doctrina("debido", db_path=db))


def test_incorporar_archivos_equivale_a_construir_el_grafo(tmp_path):
    """Red de seguridad del refactor: el recorrido completo y la suma de archivos dan el mismo grafo."""
    doctrina = tmp_path / "doctrina"
    (doctrina / "civil").mkdir(parents=True)
    (doctrina / "civil" / "a.md").write_text(DOC_PREVIO, encoding="utf-8")
    (doctrina / "civil" / "b.md").write_text(
        doc2md_ingestor.convert_text_to_canonical_markdown(DOC_NUEVO, obra="De las Obligaciones",
                                                           autor="René Ramos Pazos"),
        encoding="utf-8",
    )
    # Sin encabezado '# ': la obra se toma del nombre del archivo.
    (doctrina / "civil" / "sin_titulo.md").write_text(
        "Apuntes sueltos.\n\n## Pago de lo No Debido\nRestitución de lo pagado por error. Art. 2295 CC.\n",
        encoding="utf-8",
    )

    completo = LegalGraphifyEngine(doctrina_dir=str(doctrina))
    completo._detectar_comunidades = lambda: None
    completo.construir_grafo_desde_doctrina()

    sumado = LegalGraphifyEngine(doctrina_dir=str(doctrina))
    for nombre in ("a.md", "b.md", "sin_titulo.md"):
        sumado._incorporar_archivo(str(doctrina / "civil" / nombre))
    sumado._conectar_instituciones_cruzadas()

    assert completo.graph.has_node("obra_sin_titulo")
    assert dict(completo.graph.nodes(data=True)) == dict(sumado.graph.nodes(data=True))
    assert set(completo.graph.edges) == set(sumado.graph.edges)
