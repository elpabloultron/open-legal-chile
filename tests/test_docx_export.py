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
    assert fuente.count('res_final["word_document"] = word_compiler.compile(') == 1
    assert fuente.count('res_comp["word_document"] = word_compiler.compile(') == 1
