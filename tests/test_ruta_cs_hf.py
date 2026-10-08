"""Rutas de las fichas de la Corte Suprema en el dataset de Hugging Face.

El dataset guarda `jurisprudencia_cs/{era}/{mes}/{rol}.md`: la carpeta es la era del rol, no el
año de la fecha del fallo. Con el año de la fecha, el 18,8 % de las 70.523 rutas no existía
(medido contra el listado real del dataset el 2026-10-08). Ninguna ruta se cita sin existir.
"""

import online_library_sync as ols
from pjud_connector import ruta_hf_corte_suprema


def test_carpeta_es_la_era_del_rol_y_no_el_anio_de_la_fecha():
    assert ruta_hf_corte_suprema({"rol": "10641-2024", "fecha": "2026-03-04"}) == \
        "jurisprudencia_cs/2024/03/10641-2024.md"


def test_era_explicita_del_indice():
    assert ruta_hf_corte_suprema({"rol": "50838-2026", "era": 2026, "fecha": "2026-09-24"}) == \
        "jurisprudencia_cs/2026/09/50838-2026.md"


def test_rol_con_puntos_de_miles_y_prefijo():
    assert ruta_hf_corte_suprema({"rol": "Rol N° 29.635-2018", "fecha": "2019-05-02"}) == \
        "jurisprudencia_cs/2018/05/29635-2018.md"


def test_sin_fecha_o_rol_ajeno_no_hay_ruta():
    assert ruta_hf_corte_suprema({"rol": "123-2020", "fecha": ""}) is None
    assert ruta_hf_corte_suprema({"rol": "C-123-2020", "fecha": "2022-09-15"}) is None


def _sentencia(**extra):
    base = {"tribunal": "Corte Suprema", "rol": "10641-2024", "fecha": "2026-03-04",
            "caratula": "PARRA CON SERRANO", "recurso": "(PENAL) QUEJA", "resultado": "RECHAZA"}
    base.update(extra)
    return base


def test_catalogo_usa_la_ruta_que_existe(monkeypatch):
    monkeypatch.setattr("pjud_connector.buscar_sentencias_locales",
                        lambda q, limit=10: [_sentencia(archivo_fuente="data/jurisprudencia/cs_sentencias_2anios.jsonl")])
    res = ols._buscar_catalogo_jurisprudencia("10641-2024", archivos={"jurisprudencia_cs/2024/03/10641-2024.md"})
    assert res[0]["archivo"] == "jurisprudencia_cs/2024/03/10641-2024.md"


def test_catalogo_no_inventa_rutas(monkeypatch):
    """Si la ficha .md no está en el listado, se cita el JSONL donde vive el registro."""
    monkeypatch.setattr("pjud_connector.buscar_sentencias_locales",
                        lambda q, limit=10: [_sentencia(archivo_fuente="data/jurisprudencia/cs_sentencias.jsonl")])
    res = ols._buscar_catalogo_jurisprudencia("10641-2024", archivos={"data/jurisprudencia/cs_sentencias.jsonl"})
    assert res[0]["archivo"] == "data/jurisprudencia/cs_sentencias.jsonl"
    assert res[0]["cita_estandar"].endswith("Archivo: data/jurisprudencia/cs_sentencias.jsonl]")


def test_catalogo_sin_listado_solo_confia_en_el_indice_que_genero_las_fichas(monkeypatch):
    monkeypatch.setattr("pjud_connector.buscar_sentencias_locales",
                        lambda q, limit=10: [_sentencia(archivo_fuente="data/jurisprudencia/cs_sentencias.jsonl"),
                                             _sentencia(rol="777-2025", fecha="2025-01-02",
                                                        archivo_fuente="data/jurisprudencia/cs_sentencias_2anios.jsonl")])
    res = ols._buscar_catalogo_jurisprudencia("rol")
    assert [r["archivo"] for r in res] == ["data/jurisprudencia/cs_sentencias.jsonl",
                                           "jurisprudencia_cs/2025/01/777-2025.md"]
