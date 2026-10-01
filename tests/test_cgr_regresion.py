"""Regresion de la busqueda CGR: paginacion 0-indexada y resolucion exacta por ID."""
import urllib.error
import pytest
from cgr_connector import CGRClient

NETWORK_ERRORS = (urllib.error.URLError, TimeoutError, ConnectionError, OSError)
CONSULTA_ACOTADA = "oficina de partes virtual"  # 2 dictamenes en la base


def test_consulta_acotada_no_devuelve_vacio():
    """total > 0 con resultados vacios es el sintoma de pedir la pagina equivocada."""
    try:
        res = CGRClient().search_jurisprudencia(CONSULTA_ACOTADA, use_cache=False)
    except NETWORK_ERRORS as e:
        pytest.skip(f"Portal CGR no disponible temporalmente: {e}")
    assert res["total"] > 0, "la consulta de control dejo de tener resultados en la base"
    assert len(res["resultados"]) > 0, (
        f"total={res['total']} pero resultados=[]; la API es 0-indexada"
    )


def test_get_dictamen_devuelve_el_dictamen_pedido():
    """Nunca entregar otro documento: una cita falsa es peor que un error."""
    try:
        d = CGRClient().get_dictamen("E311060N23")
    except NETWORK_ERRORS as e:
        pytest.skip(f"Portal CGR no disponible temporalmente: {e}")
    if "error" in d:
        pytest.skip("dictamen de control no disponible en la base")
    assert d["docId"].upper() == "E311060N23", (
        f"se pidio E311060N23 y se devolvio {d['docId']}"
    )


def test_resultado_trae_texto_del_dictamen():
    """documento_completo viene en la respuesta de busqueda; debe mapearse."""
    try:
        d = CGRClient().get_dictamen("E311060N23")
    except NETWORK_ERRORS as e:
        pytest.skip(f"Portal CGR no disponible temporalmente: {e}")
    if "error" in d:
        pytest.skip("dictamen de control no disponible en la base")
    assert d.get("texto"), "el texto del dictamen vuelve vacio"


def test_identificador_citable_incluye_anio():
    """Un dictamen se cita con año: 'E311060N23', no 'E311060'."""
    try:
        res = CGRClient().search_jurisprudencia(CONSULTA_ACOTADA, use_cache=False)
    except NETWORK_ERRORS as e:
        pytest.skip(f"Portal CGR no disponible temporalmente: {e}")
    if not res["resultados"]:
        pytest.skip("consulta de control sin resultados")
    for item in res["resultados"]:
        assert item["anio"], f"{item['docId']} sin año"
        assert item["anio"][-2:] in item["docId"], (
            f"docId {item['docId']} no es citable: omite el año {item['anio']}"
        )
        assert item["urlHtml"].startswith("https://www.contraloria.cl/"), "falta procedencia"


def test_auditorias_identificador_citable():
    """En auditorías el identificable es 'número' ('460/2026'), no el correlativo."""
    try:
        res = CGRClient().search_auditorias("patrimonio cultural")
    except NETWORK_ERRORS as e:
        pytest.skip(f"Portal CGR no disponible temporalmente: {e}")
    if not res["resultados"]:
        pytest.skip("consulta de control sin resultados")
    assert any("/" in item["docId"] for item in res["resultados"]), (
        "ningún informe trae identificador con año; se perdió la referencia citable"
    )
