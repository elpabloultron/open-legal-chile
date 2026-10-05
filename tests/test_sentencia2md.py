"""Tests para el módulo sentencia2md de conversión de fallos judiciales a Markdown canónico."""

import pathlib
import pytest
from sentencia2md import (
    segmentar_secciones_sentencia,
    generar_markdown_sentencia,
    convertir_sentencia_a_md,
    convertir_lote_sentencias,
    parsear_frontmatter_yaml
)

TEXTO_SENTENCIA_MOCK = """
Santiago, dos de octubre de dos mil veintiséis.
VISTOS:
Don Juan Pérez, abogado, en representación de doña María Gómez, deduce recurso de protección en contra de Banco del Estado.
CONSIDERANDO:
1° Que la recurrente fundamenta su acción en el acto arbitrario e ilegal consistente en el bloqueo de su cuenta bancaria.
2° Que, en cuanto al derecho aplicable, el artículo 19 N° 24 de la Constitución Política de la República asegura el derecho de propiedad.
3° Que la conducta de la recurrida carece de sustento contractual válido y vulnera la garantía constitucional antes citada.
POR ESTAS CONSIDERACIONES, y de conformidad con el artículo 20 de la Carta Fundamental y el Auto Acordado de la Corte Suprema,
SE RESUELVE:
Se ACOGE el recurso de protección deducido, ordenándose el inmediato desbloqueo de la cuenta corriente.
Acordada con el voto en contra del Ministro Sr. X, quien estuvo por rechazar el recurso.
Regístrese, notifíquese y archívese en su oportunidad.
"""

DOC_MOCK = {
    "id": "14076",
    "tipo_corte": "cs",
    "tribunal": "Corte Suprema",
    "sala": "Tercera Sala (Constitucional)",
    "rol": "14076-2026",
    "fecha": "2026-10-02",
    "caratula": "Gómez con Banco del Estado",
    "recurso": "Protección",
    "resultado": "Acogido",
    "ministros": "Silva, Valderrama, Muñoz",
    "texto_integral": TEXTO_SENTENCIA_MOCK,
    "url_origen": "https://juris.pjud.cl"
}


def test_segmentar_secciones_sentencia():
    res = segmentar_secciones_sentencia(TEXTO_SENTENCIA_MOCK)
    assert "Juan Pérez" in res["vistos"]
    assert len(res["considerandos"]) == 3
    assert res["considerandos"][0]["numero"] == "1°"
    assert "19 N° 24" in res["considerandos"][1]["texto"]
    assert res["considerandos"][1]["tipo"] == "DERECHO"
    assert "ACOGE" in res["resolutiva"]
    assert "Ministro Sr. X" in res["disidencia"]


def test_generar_markdown_sentencia():
    md = generar_markdown_sentencia(DOC_MOCK)
    assert md.startswith("---")
    assert 'rol: "14076-2026"' in md
    assert 'tribunal: "Corte Suprema"' in md
    assert "### Considerando 1°" in md
    assert "### Considerando 2°" in md
    assert "## III. Parte Resolutiva" in md
    assert "## IV. Votos Disidentes y Prevenciones" in md


def test_convertir_y_guardar_lote_md(tmp_path):
    doc1 = dict(DOC_MOCK, rol="14076-2026")
    doc2 = dict(DOC_MOCK, rol="14077-2026")
    paths = convertir_lote_sentencias([doc1, doc2], destino_dir=tmp_path)
    assert len(paths) == 2
    for p in paths:
        assert p.exists()
        meta, cuerpo = parsear_frontmatter_yaml(p.read_text(encoding="utf-8"))
        assert "rol" in meta
        assert "tribunal" in meta
        assert len(cuerpo) > 50
