"""
Tests para el scraper y extractor oficial de jurisprudencia PJUD (juris.pjud.cl)
Valida la extracción de metadatos, texto de sentencias y generación de descargas oficiales (PDF / Word).
"""

import json
from unittest.mock import MagicMock, patch
import pytest

from scripts.cosechar_pjud_scrapper import PJUDScraper


class FakeResponse:
    def __init__(self, text="", json_data=None, content=b"", status_code=200):
        self.text = text
        self._json = json_data or {}
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json


@pytest.fixture
def scraper():
    return PJUDScraper()


def test_obtener_token_csrf(scraper):
    html_falso = '<form><input type="hidden" name="_token" value="fake_token_csrf_12345"></form>'
    with patch.object(scraper.session, "get", return_value=FakeResponse(text=html_falso)):
        token = scraper._obtener_token("cs")
        assert token == "fake_token_csrf_12345"


def test_buscar_sentencias_cs_y_normalizar(scraper):
    html_token = '<input type="hidden" name="_token" value="tok123">'
    solr_response = {
        "response": {
            "numFound": 1,
            "docs": [{
                "id": 8315605,
                "rol_era_sup_s": "14076-2026",
                "era_sup_i": 2026,
                "fec_sentencia_sup_dt": "2026-10-02T00:00:00Z",
                "gls_sala_sup_s": "TERCERA, CONSTITUCIONAL",
                "gls_corte_s": "Corte Suprema",
                "gls_tip_recurso_sup_s": "APELACIÓN PROTECCIÓN",
                "resultado_recurso_sup_s": "CONFIRMA",
                "caratulado_s": "SILVA / TGR",
                "sent__gls_int_firma_sup_s": "MATUS, FRANULIC",
                "texto_sentencia": "Santiago, dos de octubre.<br/>Vistos:<br/>Se confirma."
            }]
        }
    }

    with patch.object(scraper.session, "get", return_value=FakeResponse(text=html_token)), \
         patch.object(scraper.session, "post", return_value=FakeResponse(json_data=solr_response)):

        docs = scraper.buscar(tipo_corte="cs", texto="proteccion", limite=1)
        assert len(docs) == 1
        d = docs[0]
        assert d["id"] == 8315605
        assert d["rol"] == "14076-2026"
        assert d["fecha"] == "2026-10-02"
        assert d["sala"] == "TERCERA, CONSTITUCIONAL"
        assert "Se confirma." in d["texto_integral"]
        assert "<br/>" not in d["texto_integral"]
        assert d["id_buscador"] == "528"


def test_descargar_documento_pdf_y_docx(scraper, tmp_path):
    html_token = '<input type="hidden" name="_token" value="tok123">'
    dummy_pdf_bytes = b"%PDF-1.7 fake pdf content"
    dummy_docx_bytes = b"PK\x03\x04 fake docx content"

    with patch.object(scraper.session, "get", return_value=FakeResponse(text=html_token)):
        # Test PDF
        with patch.object(scraper.session, "post", return_value=FakeResponse(content=dummy_pdf_bytes)):
            dest_pdf = tmp_path / "test.pdf"
            ruta = scraper.descargar_documento(doc_id=123, tipo_corte="cs", formato="pdf", ruta_destino=dest_pdf)
            assert ruta.exists()
            assert ruta.read_bytes() == dummy_pdf_bytes

        # Test DOCX
        with patch.object(scraper.session, "post", return_value=FakeResponse(content=dummy_docx_bytes)):
            dest_docx = tmp_path / "test.docx"
            ruta = scraper.descargar_documento(doc_id=123, tipo_corte="ca", formato="docx", ruta_destino=dest_docx)
            assert ruta.exists()
            assert ruta.read_bytes() == dummy_docx_bytes
