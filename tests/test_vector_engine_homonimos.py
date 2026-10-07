"""El índice vectorial se arma con el mapa de artículos vigente (Frente 0: homónimos pisados).

`codigos_vectorial.db` (local, ignorada por git) se construyó con el parser v2, que dejaba bajo el
número de un artículo el texto de otro: el Art. 1 del Código Civil indexado era un artículo de la
Ley 16.271. Un índice sin la marca del parser vigente se reconstruye entero.
"""

import json
import sqlite3

import pytest

import vector_engine
from vector_engine import VectorLegalEngine


@pytest.fixture
def tmp_vector_db(tmp_path):
    return str(tmp_path / "test_codigos_vectorial.db")


def _norma_dfl_con_anexa(carpeta, version):
    """Una copia local de «civil» con un DFL que trae una ley anexa (el patrón del Código Civil)."""
    estructuras = [
        {"tipoParte": "Artículo", "idParte": "1", "texto": "Artículo 1º.- Fíjase el texto refundido del Código Civil."},
        {"tipoParte": "Doble Articulado", "idParte": "2", "texto": ""},
        {"tipoParte": "Artículo", "idParte": "3", "texto": "Artículo 1º. La ley es una declaración de la voluntad soberana."},
        {"tipoParte": "Artículo", "idParte": "4", "texto": "Art. 2º. La costumbre no constituye derecho sino en los casos en que la ley se remite a ella."},
        {"tipoParte": "Artículo", "idParte": "5", "texto": "Art. 3º. Sólo toca al legislador explicar o interpretar la ley."},
        {"tipoParte": "Doble Articulado", "idParte": "6", "texto": ""},
        {"tipoParte": "Artículo", "idParte": "7", "texto": "Art. 1.º Los impuestos sobre asignaciones por causa de muerte y donaciones."},
    ]
    # La copia v2 llevaba el mapa pisado (el último «Art. 1» ganaba): se reproduce a propósito.
    # La v3 trae el mapa correcto, que es lo que el índice debe leer.
    primero = estructuras[-1] if version == 2 else estructuras[2]
    mapa = {"1": primero["texto"], "2": estructuras[3]["texto"], "3": estructuras[4]["texto"]}
    ruta = carpeta / f"norma_p{version}_172986.json"
    ruta.write_text(json.dumps({"titulo": "CC", "articulos": mapa, "estructuras": estructuras},
                               ensure_ascii=False), encoding="utf-8")
    return ruta


def _texto_indexado(db, cuerpo, articulo):
    con = sqlite3.connect(db)
    try:
        return con.execute("SELECT texto FROM articulos_vectorial WHERE cuerpo_legal=? AND articulo_id=?",
                           (cuerpo, articulo)).fetchone()[0]
    finally:
        con.close()


def test_el_indice_se_arma_con_el_mapa_vigente_y_no_con_el_pisado(tmp_vector_db, tmp_path, monkeypatch):
    monkeypatch.setattr(vector_engine, "BCN_CACHE_DIR", str(tmp_path))
    _norma_dfl_con_anexa(tmp_path, version=2)          # solo existe la copia v2 (pisada)
    engine = VectorLegalEngine(db_path=tmp_vector_db)

    assert engine.indexar_desde_bcn_cache() == {"civil": 3}

    assert _texto_indexado(tmp_vector_db, "civil", "1").startswith("Artículo 1º. La ley es una declaración")
    assert engine.version_indice() == 3, "el índice queda marcado con la versión del parser"
    assert not (tmp_path / "norma_p3_172986.json").exists(), "indexar solo lee la caché, no la reescribe"


def test_un_indice_de_la_version_anterior_se_reconstruye_y_retira_lo_que_no_pudo_rehacer(
        tmp_vector_db, tmp_path, monkeypatch):
    monkeypatch.setattr(vector_engine, "BCN_CACHE_DIR", str(tmp_path))
    _norma_dfl_con_anexa(tmp_path, version=3)
    engine = VectorLegalEngine(db_path=tmp_vector_db)
    # Índice viejo: «civil» con el texto equivocado bajo el Art. 1 y «penal» sin copia local para rehacerlo.
    engine.indexar_cuerpo_legal("civil", {"1": "Art. 1.º Los impuestos sobre asignaciones (texto ajeno)"}, "Código Civil")
    engine.indexar_cuerpo_legal("penal", {"1": "Art. 1. Es delito toda acción u omisión voluntaria"}, "Código Penal")
    assert engine.version_indice() == 0

    assert engine.indexar_desde_bcn_cache() == {"civil": 3}      # sin forzar: la marca vieja basta

    con = sqlite3.connect(tmp_vector_db)
    try:
        cuerpos = {f[0] for f in con.execute("SELECT DISTINCT cuerpo_legal FROM articulos_vectorial")}
    finally:
        con.close()
    assert cuerpos == {"civil"}, "lo que no se pudo reconstruir se retira: un texto equivocado es peor que ninguno"
    assert _texto_indexado(tmp_vector_db, "civil", "1").startswith("Artículo 1º. La ley es una declaración")

    # Con la marca vigente, indexar de nuevo no reconstruye si no se pide.
    engine.indexar_cuerpo_legal("civil", {"1": "marca"}, "Código Civil", forzar=True)
    assert engine.indexar_desde_bcn_cache() == {"civil": 1}
    assert _texto_indexado(tmp_vector_db, "civil", "1") == "marca"
