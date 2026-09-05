"""
Pruebas de integración para los conectores oficiales del Estado de Chile.
Verifica que las consultas en tiempo real retornen estructuras de datos consistentes.
"""

import pytest
import urllib.error

from bcn_connector import BCNClient
from cgr_connector import CGRClient
from dt_connector import DTClient
from cne_connector import CNEClient
from panel_expertos_connector import PanelExpertosClient
from cmf_connector import CMFClient
from sii_connector import SIIClient
from ambiental_connector import SMAClient
from tdlc_connector import TDLCClient


NETWORK_ERRORS = (urllib.error.URLError, TimeoutError, ConnectionError, OSError)


def test_bcn_ley_chile():
    try:
        client = BCNClient()
        res = client.get_ley(21643)  # Ley Karin
        assert isinstance(res, dict)
        assert res.get("numero") == "21643" or "titulo" in res or "articulos" in res
        assert "normaId" in res
    except NETWORK_ERRORS as e:
        pytest.skip(f"Portal BCN no disponible temporalmente: {e}")


def test_cgr_dictamenes():
    try:
        client = CGRClient()
        res = client.search_jurisprudencia("municipalidad")
        assert isinstance(res, dict)
        assert "resultados" in res or "total" in res
    except NETWORK_ERRORS as e:
        pytest.skip(f"Portal CGR no disponible temporalmente: {e}")


def test_dt_laboral():
    try:
        client = DTClient()
        res = client.search_dictamenes("remuneracion", limit=3)
        assert isinstance(res, list)
    except NETWORK_ERRORS as e:
        pytest.skip(f"Portal DT no disponible temporalmente: {e}")


def test_cne_energia():
    try:
        client = CNEClient()
        capacidad = client.get_capacidad_instalada()
        assert isinstance(capacidad, list)
    except NETWORK_ERRORS as e:
        pytest.skip(f"Portal CNE no disponible temporalmente: {e}")


def test_panel_expertos():
    try:
        client = PanelExpertosClient()
        res = client.search_dictamenes("peajes", max_pages=1)
        assert isinstance(res, list)
    except NETWORK_ERRORS as e:
        pytest.skip(f"Portal Panel de Expertos no disponible temporalmente: {e}")


def test_cmf_valores():
    try:
        client = CMFClient()
        res = client.search_normativa("461")
        assert isinstance(res, list)
    except NETWORK_ERRORS as e:
        pytest.skip(f"Portal CMF no disponible temporalmente: {e}")


def test_sii_tributario():
    try:
        client = SIIClient()
        res = client.search_circulares("2024")
        assert isinstance(res, list)
    except NETWORK_ERRORS as e:
        pytest.skip(f"Portal SII no disponible temporalmente: {e}")


def test_sma_ambiental():
    try:
        client = SMAClient()
        res = client.search_sancionatorios(nombre="Minera")
        assert isinstance(res, dict)
        assert "resultados" in res or "total" in res
    except NETWORK_ERRORS as e:
        pytest.skip(f"Portal SMA no disponible temporalmente: {e}")


def test_tdlc_competencia():
    try:
        client = TDLCClient()
        res = client.get_sentencias(page=1, per_page=3)
        assert isinstance(res, list)
    except NETWORK_ERRORS as e:
        pytest.skip(f"Portal TDLC no disponible temporalmente: {e}")

