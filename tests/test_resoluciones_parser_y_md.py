"""Tests para resolucion_administrativa2md y resoluciones_parser (CGR, DT, SII, TDLC, CMF)."""

import pytest
from resolucion_administrativa2md import (
    segmentar_secciones_administrativas,
    generar_markdown_resolucion,
    convertir_dictamen_a_md,
    convertir_lote_dictamenes,
    parsear_frontmatter_dictamen_yaml
)
from resoluciones_parser import ResolucionesParserEngine

TEXTO_CGR_MOCK = """
Santiago, doce de septiembre de dos mil veintitrés.
Se ha dirigido a esta Contraloría General doña Ana Pérez, solicitando un pronunciamiento sobre la aplicación del principio de confianza legítima.
Al respecto, cabe señalar que de conformidad con la Ley N° 18.883 y la jurisprudencia de este Órgano de Control, los funcionarios a contrata que han superado los dos años continuos de servicios adquieren la legítima expectativa de renovación.
En consecuencia, la no renovación de sus servicios debe fundarse en un acto administrativo debidamente motivado con razones objetivas y comprobables.
Saluda atentamente a Ud.
Jorge Bermúdez Soto, Contralor General de la República.
"""

TEXTO_DT_MOCK = """
Santiago, seis de marzo de dos mil veintiséis.
Mediante presentación de fecha 15 de enero de 2026, se consulta sobre el procedimiento de investigación en casos de acoso laboral conforme a la Ley N° 21.643.
Sobre el particular, cabe hacer presente que el Código del Trabajo en sus artículos 2 y 485 impone al empleador la obligación estricta de resguardar la salud psíquica.
Por consiguiente, quienes detentan un cargo de dirigencia sindical gozan de los mismos derechos y deberes para denunciar o ser denunciados bajo el procedimiento de la Ley Karin.
Cumplo con informar a Ud.
"""

TEXTO_SII_MOCK = """
Circular N° 45 sobre tributación de servicios digitales y modificaciones de la Ley de la Renta.
El Director del Servicio de Impuestos Internos instruye sobre el artículo 59 de la LIR.
En consecuencia, los pagos al exterior por servicios prestados vía remota están afectos a retención tributaria.
"""


def test_segmentar_secciones_administrativas():
    res = segmentar_secciones_administrativas(TEXTO_CGR_MOCK, organismo="CGR")
    assert "Ana Pérez" in res["antecedentes"]
    assert len(res["marco_normativo"]) > 0
    assert any("18.883" in n for n in res["marco_normativo"])
    assert "debidamente motivado" in res["conclusion"]


def test_generar_markdown_resolucion():
    doc = {
        "organismo": "CGR",
        "tipo_acto": "Dictamen",
        "identificador": "E391939",
        "fecha": "2023-09-12",
        "materia": "Confianza legítima en contratas de más de 2 años",
        "texto_integral": TEXTO_CGR_MOCK,
        "link_oficial": "https://www.contraloria.cl/dictamenes/E391939"
    }
    md = generar_markdown_resolucion(doc)
    assert md.startswith("---")
    assert 'organismo: "CGR"' in md
    assert 'identificador: "E391939"' in md
    assert "# DICTAMEN CGR — N° E391939" in md
    assert "## V. Conclusión y Doctrina Vinculante" in md


def test_convertir_lote_md(tmp_path):
    doc1 = {
        "organismo": "CGR",
        "tipo_acto": "Dictamen",
        "identificador": "E391939",
        "fecha": "2023-09-12",
        "texto_integral": TEXTO_CGR_MOCK
    }
    doc2 = {
        "organismo": "DT",
        "tipo_acto": "Dictamen",
        "identificador": "ORD.N°205",
        "fecha": "2026-03-06",
        "texto_integral": TEXTO_DT_MOCK
    }
    paths = convertir_lote_dictamenes([doc1, doc2], destino_dir=tmp_path)
    assert len(paths) == 2
    for p in paths:
        assert p.exists()
        meta, cuerpo = parsear_frontmatter_dictamen_yaml(p.read_text(encoding="utf-8"))
        assert "organismo" in meta


def test_parser_ranking_y_citas_canonica():
    engine = ResolucionesParserEngine()

    # Probar CGR
    doc_cgr = {
        "organismo": "CGR",
        "tipo_acto": "Dictamen",
        "identificador": "E391939",
        "fecha": "2023-09-12",
        "texto_integral": TEXTO_CGR_MOCK,
        "link_oficial": "https://www.contraloria.cl/dictamenes/E391939"
    }
    parsed = engine.parsear_resolucion(TEXTO_CGR_MOCK, organismo="CGR")
    p_elegido = engine.seleccionar_parrafo_relevante(parsed["todos_parrafos"], "confianza legítima contrata")
    assert p_elegido is not None
    assert "legítima" in p_elegido["texto"].lower() and "contrata" in p_elegido["texto"].lower()

    cita_cgr = engine.formatear_cita_canonica(p_elegido, doc_cgr)
    assert "[Dictamen CGR N° E391939 (2023), Fecha: 2023-09-12]" in cita_cgr["corchete"]
    assert "«" in cita_cgr["cita_canonica"] and "»" in cita_cgr["cita_canonica"]

    # Probar DT
    doc_dt = {
        "organismo": "DT",
        "tipo_acto": "Dictamen",
        "identificador": "ORD.N°205",
        "fecha": "2026-03-06",
        "texto_integral": TEXTO_DT_MOCK,
        "link_oficial": "https://www.dt.gob.cl"
    }
    parsed_dt = engine.parsear_resolucion(TEXTO_DT_MOCK, organismo="DT")
    p_dt = engine.seleccionar_parrafo_relevante(parsed_dt["todos_parrafos"], "ley karin acoso laboral dirigentes")
    cita_dt = engine.formatear_cita_canonica(p_dt, doc_dt)
    assert "[Dictamen DT N° 205, Fecha: 2026-03-06]" in cita_dt["corchete"]
    assert "Ley Karin" in cita_dt["extracto_literal"] or "acoso" in cita_dt["extracto_literal"].lower()

    # Probar SII
    doc_sii = {
        "organismo": "SII",
        "tipo_acto": "Circular",
        "identificador": "45",
        "fecha": "2023-08-10",
        "texto_integral": TEXTO_SII_MOCK
    }
    parsed_sii = engine.parsear_resolucion(TEXTO_SII_MOCK, organismo="SII")
    cita_sii = engine.formatear_cita_canonica(parsed_sii["todos_parrafos"][0], doc_sii)
    assert "[Circular SII N° 45 (2023), Fecha: 2023-08-10]" in cita_sii["corchete"]


def test_parser_ranking_y_citas_tdlc_cmf_panel_sma():
    engine = ResolucionesParserEngine()

    # TDLC
    doc_tdlc = {
        "organismo": "TDLC",
        "tipo_acto": "Sentencia",
        "identificador": "216/2026",
        "fecha": "2026-08-10",
        "texto_integral": "El Tribunal resuelve que la negativa de interconexión constituye abuso de posición dominante.",
    }
    parsed_tdlc = engine.parsear_resolucion(doc_tdlc["texto_integral"], organismo="TDLC")
    p_tdlc = engine.seleccionar_parrafo_relevante(parsed_tdlc["todos_parrafos"], "abuso de posición dominante")
    cita_tdlc = engine.formatear_cita_canonica(p_tdlc, doc_tdlc)
    assert "[TDLC - Sentencia N° 216/2026, Fecha: 2026-08-10]" in cita_tdlc["corchete"]
    assert cita_tdlc["etiqueta_seccion"] == "Resolutivo"

    # CMF
    doc_cmf = {
        "organismo": "CMF",
        "tipo_acto": "NCG",
        "identificador": "461",
        "fecha": "2021-11-12",
        "texto_integral": "La CMF dispone reporte de sostenibilidad en la memoria anual.",
    }
    parsed_cmf = engine.parsear_resolucion(doc_cmf["texto_integral"], organismo="CMF")
    cita_cmf = engine.formatear_cita_canonica(parsed_cmf["todos_parrafos"][0], doc_cmf)
    assert "[NCG CMF N° 461, Fecha: 2021-11-12]" in cita_cmf["corchete"]
    assert cita_cmf["etiqueta_seccion"] == "Disposición"

    # Panel
    doc_panel = {
        "organismo": "PANEL",
        "tipo_acto": "Dictamen",
        "identificador": "12-2023",
        "fecha": "2023-11-20",
        "texto_integral": "El Panel determina el cálculo de peajes zonales conforme a bases técnicas.",
    }
    parsed_panel = engine.parsear_resolucion(doc_panel["texto_integral"], organismo="PANEL")
    cita_panel = engine.formatear_cita_canonica(parsed_panel["todos_parrafos"][0], doc_panel)
    assert "[Panel de Expertos - Dictamen N° 12-2023, Fecha: 2023-11-20]" in cita_panel["corchete"]
    assert cita_panel["etiqueta_seccion"] == "Determinación"

    # SMA
    doc_sma = {
        "organismo": "SMA",
        "tipo_acto": "Sancionatorio",
        "identificador": "D-045-2023",
        "fecha": "2023-09-14",
        "texto_integral": "La SMA formula cargos graves por superación de norma de ruidos.",
    }
    parsed_sma = engine.parsear_resolucion(doc_sma["texto_integral"], organismo="SMA")
    cita_sma = engine.formatear_cita_canonica(parsed_sma["todos_parrafos"][0], doc_sma)
    assert "[SMA - Expediente SNIFA D-045-2023, Fecha: 2023-09-14]" in cita_sma["corchete"]
    assert cita_sma["etiqueta_seccion"] == "Infracción"


def test_legal_graphify_ingesta_dictamenes_lote():
    from legal_graphify import LegalGraphifyEngine
    engine = LegalGraphifyEngine()

    docs = [
        {
            "organismo": "CGR",
            "tipo_acto": "Dictamen",
            "identificador": "D100N24",
            "fecha": "2024-01-10",
            "materia": "Estatuto administrativo y probidad",
            "fuentes_legales": ["Ley 18.575"],
            "texto_integral": "La Contraloría determina el deber de probidad en compras públicas."
        },
        {
            "organismo": "DT",
            "tipo_acto": "Dictamen",
            "identificador": "ORD. N° 500",
            "fecha": "2024-02-15",
            "materia": "Jornada laboral 40 horas",
            "fuentes_legales": ["Código del Trabajo art. 22"],
            "texto_integral": "La Dirección del Trabajo interpreta la reducción de jornada laboral."
        }
    ]
    res = engine.ingerir_lote_dictamenes(docs, guardar_disco=False)
    assert res["total_dictamenes"] == 2
    assert res["nodos_nuevos_totales"] > 0
    assert res["enlaces_nuevos_totales"] > 0
