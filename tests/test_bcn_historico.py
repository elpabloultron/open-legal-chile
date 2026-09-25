"""Pruebas del histórico de normas (versiones de LeyChile) — sin red.

Cubren la lógica que sostiene `bcn_get_codigo_historico`: elegir la versión vigente a una
fecha, aplanar el JSON de LeyChile a texto y recortar el artículo pedido.
"""

import pytest

from bcn_connector import BCNClient


def test_version_para_fecha_elige_la_vigente_y_descarta_la_diferida():
    versiones = [
        {"@tipoVersion": "Con Vigencia Diferida por Evento", "@vigenteDesde": "2222-02-02"},
        {"@tipoVersion": "Original", "@vigenteDesde": "2003-01-16", "@vigenteHasta": "2013-12-31"},
        {"@tipoVersion": "Intermedio", "@vigenteDesde": "2020-04-01", "@vigenteHasta": "2024-04-25"},
        {"@tipoVersion": "Vigente", "@vigenteDesde": "2024-04-26"},
    ]
    elegida = BCNClient._version_para_fecha(versiones, "2020-06-01")
    assert elegida is not None and elegida["@vigenteDesde"] == "2020-04-01"
    vigente = BCNClient._version_para_fecha(versiones, "2026-09-25")
    assert vigente is not None and vigente["@vigenteDesde"] == "2024-04-26"
    primera = BCNClient._version_para_fecha(versiones, "2004-05-05")
    assert primera is not None and primera["@vigenteDesde"] == "2003-01-16"
    # Antes del inicio del historial: no hay versión (no se inventa ninguna).
    assert BCNClient._version_para_fecha(versiones, "1995-01-01") is None


def test_texto_version_aplana_y_limpia():
    data = {
        "html": [
            {"t": "Encabezado", "h": "<div>Art. 22. La duración</div>"},
            {"h": [{"h": "&nbsp;de la jornada"}]},
            {"t": "sin cuerpo"},
        ]
    }
    texto = BCNClient._texto_version(data)
    assert "Art. 22. La duración" in texto
    assert "de la jornada" in texto
    assert "<div>" not in texto and "&nbsp;" not in texto


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("Previo. Art. 22. La jornada no excederá de cuarenta y cinco horas. Art. 23. Siguiente.", "cuarenta y cinco"),
        ("Previo. Artículo 22.- La jornada no excederá de cuarenta horas. Artículo 23.- Siguiente.", "cuarenta horas"),
    ],
)
def test_extraer_articulo_acepta_las_dos_cabeceras(texto, esperado):
    fragmento = BCNClient._extraer_articulo(texto, "22")
    assert fragmento is not None
    assert esperado in fragmento
    assert "Siguiente" not in fragmento  # corta en la siguiente cabecera


def test_extraer_articulo_ignora_referencias_en_minuscula():
    texto = "Art. 1. Se aplicará lo dispuesto en el artículo 22 a todos los casos. Art. 2. Otro."
    fragmento = BCNClient._extraer_articulo(texto, "22")
    assert fragmento is None


def test_extraer_articulo_no_confunde_notas_de_modificacion():
    texto = "Art. 5. Texto. Ley 21258 Art. 22 N° 1 D.O. 02.09.2020 siga. Art. 6. Otro."
    assert BCNClient._extraer_articulo(texto, "22") is None
