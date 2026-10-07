"""El idNorma 172986 trae el Código Civil y leyes embebidas con sus propios Arts. 1, 50…:
debe ganar la primera aparición (el Código), también al leer copias locales antiguas."""

import json

import pytest

from bcn_connector import BCNClient

ART1 = "Artículo 1.- La ley es una declaración de la voluntad soberana que, manifestada en la forma prescrita por la Constitución, manda, prohíbe o permite."
ART48 = "Artículo 48.- Todos los plazos de días, meses o años de que se hable en las leyes, terminarán a la medianoche del último día del plazo; hasta la medianoche del último día del plazo."
ART50 = "Artículo 50.- En los plazos que se señalaren en las leyes, o en los decretos del Presidente de la República, se comprenderán aun los días feriados."
LEY_ART1 = "Artículo 1.- Los impuestos sobre asignaciones por causa de muerte y donaciones se regirán por esta ley."
LEY_ART50 = "Artículo 50.- El impuesto deberá declararse y pagarse dentro del plazo."


def _xml(textos):
    nodos = "".join(
        f'<EstructuraFuncional tipoParte="Artículo" idParte="{i}"><Texto>{t}</Texto></EstructuraFuncional>'
        for i, t in enumerate(textos)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?><Norma normaId="172986" fechaVersion="2025-01-01">'
        f"<EstructurasFuncionales>{nodos}</EstructurasFuncionales></Norma>"
    )


XML_CC = _xml([ART1, ART48, ART50, LEY_ART1, LEY_ART50])


def _verifica(articulos):
    assert articulos["1"].startswith("Artículo 1.- La ley es una declaración de la voluntad soberana")
    assert "hasta la medianoche del último día del plazo" in articulos["48"]
    assert "se comprenderán aun los días feriados" in articulos["50"]


def test_parser_gana_la_primera_aparicion():
    _verifica(BCNClient()._parse_norma_xml(XML_CC)["articulos"])


def test_get_codigo_civil_articulo_50(tmp_path, monkeypatch):
    cliente = BCNClient(cache_dir=str(tmp_path))
    monkeypatch.setattr(cliente, "_fetch_xml", lambda params: XML_CC)
    res = cliente.get_codigo("civil", "50")
    assert "se comprenderán aun los días feriados" in res["texto"]


def test_copia_local_antigua_se_reconstruye_sin_red(tmp_path, monkeypatch):
    cliente = BCNClient(cache_dir=str(tmp_path))
    parseado = cliente._parse_norma_xml(XML_CC)
    parseado.pop("parser")
    parseado["articulos"] = {"1": LEY_ART1, "50": LEY_ART50}
    (tmp_path / "norma_p2_172986.json").write_text(json.dumps(parseado), encoding="utf-8")

    def sin_red(params):
        raise AssertionError("no debe ir a la red")

    monkeypatch.setattr(cliente, "_fetch_xml", sin_red)
    _verifica(cliente.get_norma(172986)["articulos"])


def test_transitorio_no_pisa_al_permanente():
    xml = _xml(["Artículo 5.- Texto permanente.", "Artículo 5.- Texto transitorio."])
    assert BCNClient()._parse_norma_xml(xml)["articulos"]["5"] == "Artículo 5.- Texto permanente."
