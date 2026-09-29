"""Prueba de la regla de la casa: los documentos se entregan en Word (.docx), editables.

El compilador Word convierte el Markdown de un escrito (encabezados, negritas, viñetas) en un .docx
que el abogado puede corregir. Esta prueba cuida que: (1) compile de verdad, (2) el archivo se pueda
volver a abrir y guardar (o sea, es editable), y (3) el contenido esté adentro.
"""
from __future__ import annotations

import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))


def test_compila_word_desde_markdown(tmp_path):
    from docx_compiler import WordDossierCompiler

    motor = WordDossierCompiler()
    assert motor.is_available(), "python-docx debe estar instalado: es la regla de la casa"

    escrito = (
        "# EN LO PRINCIPAL: RECURSO DE PROTECCIÓN\n\n"
        "**Primero:** Que vengo en interponer recurso de protección en contra de la recurrida.\n\n"
        "- Hecho uno, con *énfasis*.\n"
        "- Hecho dos.\n\n"
        "---\n\n"
        "## SEGUNDO OTROSÍ: ACOMPAÑA DOCUMENTOS\n\n"
        "Cuerpo del otrosí con negrita **relevante**.\n"
    )
    destino = tmp_path / "escrito.docx"
    resultado = motor.compile(markdown_content=escrito, output_docx_path=str(destino),
                              title="Recurso de Protección — Prueba")

    assert resultado["ok"] is True, resultado
    assert destino.exists() and destino.stat().st_size > 0

    # editable: se abre, dice lo que debe decir, y se puede volver a guardar
    from docx import Document

    documento = Document(str(destino))
    texto = "\n".join(p.text for p in documento.paragraphs)
    assert "EN LO PRINCIPAL: RECURSO DE PROTECCIÓN" in texto
    assert "Primero:" in texto
    assert "SEGUNDO OTROSÍ" in texto
    assert "Hecho uno" in texto

    reeditado = tmp_path / "reeditado.docx"
    documento.save(str(reeditado))
    assert reeditado.exists() and reeditado.stat().st_size > 0


def test_el_servidor_expone_el_compilador_word():
    """El servidor MCP tiene el compilador conectado, listo para usarlo en las herramientas."""
    fuente = (RAIZ / "mcp_server.py").read_text(encoding="utf-8")
    assert "from docx_compiler import WordDossierCompiler" in fuente
    assert "word_compiler = WordDossierCompiler()" in fuente
    # las dos vías de documentos lo usan: recurso de protección y dossier genérico
    # (los despachos viven en servidor/forense.py desde el split por dominios)
    todo = fuente + "".join(p.read_text(encoding="utf-8")
                            for p in sorted((RAIZ / "servidor").glob("*.py")))
    assert todo.count('res_final["word_document"] = word_compiler.compile(') == 1
    assert todo.count('res_comp["word_document"] = word_compiler.compile(') == 1


def test_cita_literal_del_informe_llega_al_docx(tmp_path):
    """La transcripción «…» de una norma entra al Word como bloque citado en cursiva."""
    from docx_compiler import WordDossierCompiler

    salida = tmp_path / "informe.docx"
    res = WordDossierCompiler().compile(
        "# INFORME\n> «Los contratos deben ejecutarse de buena fe.»", str(salida))

    assert res["ok"], res
    from docx import Document

    documento = Document(str(salida))
    con_cita = [p for p in documento.paragraphs if "buena fe" in p.text]
    assert con_cita, [p.text for p in documento.paragraphs]
    assert any(r.italic for p in con_cita for r in p.runs), "la cita literal va en cursiva (bloque citado)"


def test_el_separador_es_doble_espaciado_y_no_salto_de_pagina(tmp_path):
    """Regla del usuario: nada de páginas en blanco; un doble espaciado separa capítulos."""
    from docx_compiler import WordDossierCompiler
    from docx.oxml.ns import qn

    salida = tmp_path / "sin_saltos.docx"
    res = WordDossierCompiler().compile("I. Uno\n\n---\n\nII. Dos", str(salida))
    assert res["ok"], res

    from docx import Document

    documento = Document(str(salida))
    saltos = [b for b in documento._element.findall(".//" + qn("w:br"))
              if b.get(qn("w:type")) == "page"]
    assert saltos == [], "el separador no puede generar páginas en blanco"
    assert any(p.text == "" for p in documento.paragraphs), "el separador deja el doble espaciado"


def test_el_docx_va_en_a4_y_con_el_cuerpo_justificado(tmp_path):
    """Regla del usuario: tamaño A4 y texto justificado (el cuerpo y las citas), no carta gringa."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm

    from docx_compiler import WordDossierCompiler

    salida = tmp_path / "a4.docx"
    res = WordDossierCompiler().compile(
        "# INFORME\n\nEl contrato debe ejecutarse de buena fe.\n\n> «La buena fe es el alma de los contratos.»",
        str(salida))
    assert res["ok"], res

    from docx import Document

    documento = Document(str(salida))
    seccion = documento.sections[0]
    assert abs(seccion.page_width - Cm(21)) <= 635, seccion.page_width  # twips: tolerancia de 1 twip
    assert abs(seccion.page_height - Cm(29.7)) <= 635, seccion.page_height
    cuerpo = [p for p in documento.paragraphs if "buena fe" in p.text]
    assert cuerpo, [p.text for p in documento.paragraphs]
    assert all(p.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY for p in cuerpo), \
        "el cuerpo y las citas van justificados"


def test_el_docx_acepta_tamano_oficio(tmp_path):
    """Variante pedida por el usuario: oficio chileno (21,59 × 33,02 cm)."""
    from docx.shared import Cm

    from docx_compiler import WordDossierCompiler

    salida = tmp_path / "oficio.docx"
    res = WordDossierCompiler().compile("Texto\n", str(salida), tamano="oficio")
    assert res["ok"], res

    from docx import Document

    seccion = Document(str(salida)).sections[0]
    assert abs(seccion.page_width - Cm(21.59)) <= 635, seccion.page_width
    assert abs(seccion.page_height - Cm(33.02)) <= 635, seccion.page_height
