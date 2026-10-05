"""Tests unitarios para PJUDClient con búsqueda online y pipeline forense multi-sentencia."""

from unittest.mock import MagicMock
import pytest
from pjud_connector import PJUDClient

DOC_MOCK_CS = {
    "id": "14076",
    "tipo_corte": "cs",
    "tribunal": "Corte Suprema",
    "sala": "Tercera Sala (Constitucional)",
    "rol": "14076-2026",
    "fecha": "2026-10-02",
    "caratula": "Gómez con Banco",
    "recurso": "Protección",
    "resultado": "Acogido",
    "ministros": "Silva, Muñoz",
    "texto_integral": """
    Santiago, dos de octubre de dos mil veintiséis.
    VISTOS:
    Recurso de protección.
    CONSIDERANDO:
    1° Que la recurrente reclama por el bloqueo de su cuenta.
    2° Que el artículo 19 N° 24 de la Constitución asegura el derecho de propiedad.
    3° Que el actuar recurrido es arbitrario e ilegal al no fundarse en norma alguna.
    SE RESUELVE:
    Se acoge el recurso.
    """,
    "url_origen": "https://juris.pjud.cl/busqueda?Corte_Suprema"
}

DOC_MOCK_CA = {
    "id": "504",
    "tipo_corte": "ca",
    "tribunal": "Corte de Apelaciones de Temuco",
    "sala": "Segunda Sala",
    "rol": "504-2026",
    "fecha": "2026-09-28",
    "caratula": "Arias con Municipalidad",
    "recurso": "Protección",
    "resultado": "Acogido",
    "ministros": "Troncoso, García",
    "texto_integral": """
    Temuco, veintiocho de septiembre de dos mil veintiséis.
    VISTOS:
    Protección en contra del cese intempestivo de contrata.
    CONSIDERANDO:
    1° Que el actor sirvió ininterrumpidamente por más de tres años en el municipio.
    2° Que conforme al principio de confianza legítima y la jurisprudencia de la Corte Suprema, las contratas de más de dos años requieren sumario o acto debidamente motivado para no renovación.
    3° Que la resolución carece de motivación suficiente y vulnera el artículo 19 N° 2 de la Constitución.
    SE RESUELVE:
    Se acoge el recurso y se ordena el reintegro.
    """,
    "url_origen": "https://juris.pjud.cl/busqueda?Corte_de_Apelaciones"
}


def test_pjud_client_search_online_mocked(monkeypatch):
    client = PJUDClient()
    mock_scraper = MagicMock()
    mock_scraper.buscar.return_value = [DOC_MOCK_CS]
    monkeypatch.setattr(client, "_scraper", mock_scraper)

    res = client.search_online("bloqueo cuenta", corte="cs", limite=2)
    assert len(res) == 1
    assert res[0]["rol"] == "14076-2026"
    mock_scraper.buscar.assert_called_once_with(tipo_corte="cs", texto="bloqueo cuenta", limite=2, offset=0)


def test_pjud_client_get_sentencia_integral_mocked(monkeypatch):
    client = PJUDClient()
    mock_scraper = MagicMock()
    mock_scraper.buscar.return_value = [DOC_MOCK_CS]
    monkeypatch.setattr(client, "_scraper", mock_scraper)

    doc = client.get_sentencia_integral("14076-2026", corte="cs")
    assert doc["id"] == "14076"
    assert "Corte Suprema" in doc["tribunal"]


def test_pjud_procesar_y_graficar_sentencias_pipeline(monkeypatch):
    client = PJUDClient()
    # Ejecutamos el pipeline completo pasando directamente los dos documentos simulados
    lote = [DOC_MOCK_CS, DOC_MOCK_CA]

    resultado = client.procesar_y_graficar_sentencias(
        roles_o_docs=lote,
        corte="cs",
        tema_relevante="confianza legítima contrata no renovación",
        convertir_a_md=True
    )

    assert resultado["total_sentencias"] == 2
    assert len(resultado["citas_destacadas"]) == 2

    # Verificar que el fallo de CA Temuco seleccionó el considerando de confianza legítima
    cita_ca = resultado["citas_destacadas"][1]
    assert cita_ca["tribunal_prefijo"] == "C.A. de Temuco"
    assert cita_ca["numero_considerando"] == "2°"
    assert "confianza legítima" in cita_ca["extracto_literal"].lower()
    assert "[C.A. de Temuco - Rol N° 504-2026" in cita_ca["corchete"]

    # Verificar que se generaron los archivos Markdown
    assert len(resultado["archivos_generados"]["markdown"]) == 2
