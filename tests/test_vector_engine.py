"""Pruebas unitarias para el motor vectorial local integrado (vector_engine.py)."""

import os
import sqlite3
import numpy as np
import pytest

from vector_engine import (
    SemanticEmbeddingEngine,
    VectorLegalEngine,
    init_vector_db,
    _normalizar_texto,
    obtener_motor_vectorial,
    EMBEDDING_DIM,
)


@pytest.fixture
def tmp_vector_db(tmp_path):
    """Base de datos vectorial aislada para pruebas."""
    db_file = tmp_path / "test_codigos_vectorial.db"
    return str(db_file)


def test_normalizar_texto():
    assert _normalizar_texto("Código del Trabajo — Art. 161") == "codigo del trabajo — art. 161"
    assert _normalizar_texto("Prescripción Adquisitiva") == "prescripcion adquisitiva"
    assert _normalizar_texto("") == ""


def test_semantic_embedding_engine():
    engine = SemanticEmbeddingEngine()
    assert engine.dim == EMBEDDING_DIM

    # Vector no vacío y normalizado a norma unitaria (L2 = 1.0)
    v1 = engine.encode("despido injustificado indemnizacion por anos de servicio")
    assert v1.shape == (EMBEDDING_DIM,)
    assert np.isclose(np.linalg.norm(v1), 1.0, atol=1e-4)

    # Texto vacío produce vector ceros
    v_vacio = engine.encode("")
    assert np.all(v_vacio == 0.0)

    # Similitud semántica: textos afines con raíces y lemas compartidos tienen mayor similitud
    v_lab1 = engine.encode("despido injustificado del trabajador en la empresa")
    v_lab2 = engine.encode("trabajador despedido por necesidades de la empresa")
    v_min = engine.encode("concesion minera pertenencia mensura canon de mineria")

    sim_afin = float(np.dot(v_lab1, v_lab2))
    sim_dif = float(np.dot(v_lab1, v_min))
    assert sim_afin > sim_dif, f"Esperado sim_afin ({sim_afin:.4f}) > sim_dif ({sim_dif:.4f})"

    # Codificación por lotes (batch)
    batch = engine.encode_batch(["texto uno", "texto dos"])
    assert batch.shape == (2, EMBEDDING_DIM)


def test_init_vector_db(tmp_vector_db):
    con = init_vector_db(tmp_vector_db)
    cur = con.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = {r[0] for r in cur.fetchall()}
    assert "articulos_vectorial" in tablas
    assert "articulos_fts" in tablas
    con.close()


def test_vector_legal_engine_indexacion_y_busqueda(tmp_vector_db):
    engine = VectorLegalEngine(db_path=tmp_vector_db)
    assert engine.total_articulos_indexados() == 0

    articulos_trabajo = {
        "161": "El contrato de trabajo termina por necesidades de la empresa, establecimiento o servicio.",
        "160": "El contrato de trabajo termina sin derecho a indemnización alguna cuando el trabajador incurre en falta de probidad.",
        "162": "Si el contrato termina por las causales del artículo 161, el empleador deberá comunicarlo por escrito al trabajador.",
    }

    articulos_civil = {
        "1545": "Todo contrato legalmente celebrado es una ley para los contratantes, y no puede ser invalidado sino por su consentimiento mutuo o por causas legales.",
        "1437": "Las obligaciones nacen, ya del concurso real de las voluntades de dos o más personas, como en los contratos o convenciones.",
    }

    n_trabajo = engine.indexar_cuerpo_legal("trabajo", articulos_trabajo, "Código del Trabajo")
    n_civil = engine.indexar_cuerpo_legal("civil", articulos_civil, "Código Civil")

    assert n_trabajo == 3
    assert n_civil == 2
    assert engine.total_articulos_indexados() == 5

    # 1. Búsqueda semántica densa
    res_vec = engine.buscar_vectorial("necesidades de la empresa despido", top_k=2)
    assert len(res_vec) == 2
    assert res_vec[0]["articulo_id"] == "161"
    assert "similitud" in res_vec[0]

    # Filtrando por cuerpo legal
    res_vec_civil = engine.buscar_vectorial("contrato ley consentimiento", cuerpo_legal="civil", top_k=2)
    assert len(res_vec_civil) >= 1
    assert res_vec_civil[0]["cuerpo_legal"] == "civil"
    assert res_vec_civil[0]["articulo_id"] == "1545"

    # 2. Búsqueda léxica FTS5 BM25
    res_fts = engine.buscar_lexica_fts("probidad", top_k=2)
    assert len(res_fts) >= 1
    assert res_fts[0]["articulo_id"] == "160"
    assert "rank_bm25" in res_fts[0]

    # 3. Búsqueda híbrida Reciprocal Rank Fusion (RRF)
    res_rrf = engine.buscar_hibrido("falta de probidad despido", top_k=3)
    assert len(res_rrf) >= 1
    assert res_rrf[0]["articulo_id"] == "160"
    assert "puntaje_rrf" in res_rrf[0]

    # Consultas vacías
    assert engine.buscar_vectorial("") == []
    assert engine.buscar_lexica_fts("") == []
    assert engine.buscar_hibrido("") == []


def test_obtener_motor_vectorial_singleton():
    m1 = obtener_motor_vectorial()
    m2 = obtener_motor_vectorial()
    assert m1 is m2
