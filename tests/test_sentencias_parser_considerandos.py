"""Tests para el motor de sentencias y ranking/citación de considerandos."""

import pytest
from sentencias_parser import SentenciaParserEngine

TEXTO_FALLO_1 = """
Santiago, cinco de marzo de dos mil veintiséis.
VISTOS:
En estos autos sobre recurso de unificación de doctrina caratulados "López con Retail S.A.".
CONSIDERANDO:
1° Que la parte demandante solicita la unificación respecto de la procedencia del descuento de AFC.
2° Que, en cuanto a los hechos, el actor fue despedido por necesidades de la empresa conforme al artículo 161 del Código del Trabajo, declarándose judicialmente injustificado dicho despido.
3° Que, sobre el fondo del derecho, la jurisprudencia uniforme de esta Corte Suprema ha establecido que si el despido por necesidades de la empresa es declarado injustificado, carece de causa legal y resulta improcedente imputar el saldo de la cuenta individual por cesantía (AFC) del trabajador.
POR ESTAS CONSIDERACIONES,
SE RESUELVE:
Se ACOGE el recurso de unificación de doctrina deducido por el demandante.
Regístrese y devuélvase.
"""

TEXTO_FALLO_2 = """
Santiago, quince de abril de dos mil veintiséis.
VISTOS:
Causa Rol N° 7890-2026 sobre tutela laboral caratulada "Pérez con Minera Norte".
CONSIDERANDO:
PRIMERO: Que el denunciante interpone denuncia de tutela por vulneración de la integridad psíquica.
SEGUNDO: Que las pruebas documentales acreditan actos reiterados de hostigamiento en el lugar de trabajo.
TERCERO: Que de conformidad con el artículo 485 y 489 del Código del Trabajo y la Ley N° 21.643, el empleador está obligado a garantizar un entorno libre de acoso y violencia, procediendo la indemnización por daño moral cuando se acredita la afección extrapatrimonial del trabajador.
RESUELVO:
Ha lugar a la denuncia de tutela con expresa condenación en costas por no haber tenido motivo plausible.
"""


def test_sentencia_parser_full_text_and_selection():
    engine = SentenciaParserEngine()
    res1 = engine.parsear_sentencia(TEXTO_FALLO_1)

    assert res1["total_considerandos"] == 3
    assert len(res1["todos_considerandos"]) == 3
    # Comprobar que no está truncado
    assert "cuenta individual por cesantía (AFC)" in res1["todos_considerandos"][2]["texto"]

    # Probar selección de considerando relevante por tema
    cons_afc = engine.seleccionar_considerando_relevante(
        res1["todos_considerandos"],
        "descuento de afc despido injustificado"
    )
    assert cons_afc is not None
    assert cons_afc["numero"] == "3°"
    assert "improcedente imputar" in cons_afc["texto"]


def test_formatear_cita_considerando():
    engine = SentenciaParserEngine()
    meta = {
        "tribunal": "Corte Suprema",
        "rol": "45.123-2021",
        "fecha": "15-09-2022",
        "link": "https://juris.pjud.cl"
    }
    cons = {
        "numero": "3°",
        "texto": "Es improcedente imputar el saldo de la cuenta individual por cesantía cuando el despido es injustificado."
    }
    cita = engine.formatear_cita_considerando(cons, meta)
    assert "[CS - Rol N° 45.123-2021, Fecha: 15-09-2022, Considerando 3°]" in cita["corchete"]
    assert "«Es improcedente imputar el saldo" in cita["cita_canonica"]
    assert cita["tribunal_prefijo"] == "CS"


def test_analizar_lote_sentencias_multiples():
    engine = SentenciaParserEngine()
    lote = [
        {
            "tribunal": "Corte Suprema",
            "rol": "1234-2026",
            "fecha": "2026-03-05",
            "texto_integral": TEXTO_FALLO_1
        },
        {
            "tribunal": "Corte de Apelaciones de Santiago",
            "rol": "7890-2026",
            "fecha": "2026-04-15",
            "texto_integral": TEXTO_FALLO_2
        }
    ]

    res_lote = engine.analizar_lote_sentencias(lote, tema_relevante="descuento AFC cuenta individual")
    assert res_lote["total_sentencias_analizadas"] == 2
    assert len(res_lote["citas_destacadas"]) == 2

    # El fallo 1 debe destacar el considerando sobre AFC
    cita1 = res_lote["citas_destacadas"][0]
    assert cita1["numero_considerando"] == "3°"
    assert "AFC" in cita1["extracto_literal"]

    # El fallo 2 debe haber seleccionado considerando relevante
    cita2 = res_lote["citas_destacadas"][1]
    assert cita2["tribunal_prefijo"] == "C.A. de Santiago"
