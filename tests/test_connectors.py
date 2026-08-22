"""
Pruebas de integración para los conectores oficiales del Estado de Chile.
Verifica que las consultas en tiempo real retornen estructuras de datos consistentes.
"""

from bcn_connector import BCNClient
from cgr_connector import CGRClient
from dt_connector import DTClient
from cne_connector import CNEClient
from panel_expertos_connector import PanelExpertosClient
from cmf_connector import CMFClient
from sii_connector import SIIClient
from ambiental_connector import SMAClient
from tdlc_connector import TDLCClient

def test_bcn_ley_chile():
    client = BCNClient()
    res = client.get_ley(21643) # Ley Karin
    assert isinstance(res, dict)
    assert res.get("numero") == "21643" or "titulo" in res or "articulos" in res
    assert "normaId" in res

def test_cgr_dictamenes():
    client = CGRClient()
    res = client.search_jurisprudencia("municipalidad")
    assert isinstance(res, dict)
    assert "resultados" in res or "total" in res

def test_dt_laboral():
    client = DTClient()
    res = client.search_dictamenes("remuneracion", limit=3)
    assert isinstance(res, list)

def test_cne_energia():
    client = CNEClient()
    capacidad = client.get_capacidad_instalada()
    assert isinstance(capacidad, list)

def test_panel_expertos():
    client = PanelExpertosClient()
    res = client.search_dictamenes("peajes", max_pages=1)
    assert isinstance(res, list)

def test_cmf_valores():
    client = CMFClient()
    res = client.search_normativa("461")
    assert isinstance(res, list)

def test_sii_tributario():
    client = SIIClient()
    res = client.search_circulares("2024")
    assert isinstance(res, list)

def test_sma_ambiental():
    client = SMAClient()
    res = client.search_sancionatorios(nombre="Minera")
    assert isinstance(res, dict)
    assert "resultados" in res or "total" in res

def test_tdlc_competencia():
    client = TDLCClient()
    res = client.get_sentencias(page=1, per_page=3)
    assert isinstance(res, list)

