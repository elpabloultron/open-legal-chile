"""Pruebas offline para redlining nativo XML (`w:del`/`w:ins` y `word/comments.xml`) en .docx."""

import zipfile
import xml.etree.ElementTree as ET

from docx import Document

from docx_compiler import WordDossierCompiler
import mcp_server


def test_aplicar_redline_cuerpo_tabla_comentarios_y_segunda_pasada(tmp_path):
    entrada = tmp_path / "contrato.docx"
    salida1 = tmp_path / "contrato_redline.docx"
    salida2 = tmp_path / "contrato_redline_v2.docx"

    doc = Document()
    p1 = doc.add_paragraph()
    p1.add_run("La ")
    r_b = p1.add_run("multa será ")
    r_b.bold = True
    p1.add_run("de 10 UF por atraso.")
    doc.add_paragraph("Cláusula de Jurisdicción arbitral en Santiago.")
    tabla = doc.add_table(rows=1, cols=2)
    tabla.cell(0, 0).text = "Vigencia"
    tabla.cell(0, 1).text = "Plazo: 30 días"
    doc.save(str(entrada))

    comp = WordDossierCompiler()
    res1 = comp.aplicar_redline(
        input_docx_path=str(entrada),
        output_docx_path=str(salida1),
        autor="Abogado Revisor",
        cambios=[
            {
                "buscar": "multa será de 10 UF",
                "reemplazar": "multa será de 5 UF",
                "comentario": 'Rebaja por proporcionalidad ("cláusula penal", Art. 1544 CC).',
            },
            {
                "buscar": "Plazo: 30 días",
                "reemplazar": "Plazo: 15 días",
            },
            {
                "buscar": "Jurisdicción arbitral",
                "comentario": "Verificar arbitraje conforme Ley N° 19.971.",
            },
            {
                "buscar": "cláusula inexistente",
                "reemplazar": "otro texto",
            },
        ],
    )

    assert res1["ok"] is True
    assert res1["cambios_aplicados"] == 3
    assert res1["comentarios_insertados"] == 2
    assert res1["no_encontrados"] == ["cláusula inexistente"]
    assert salida1.exists()

    with zipfile.ZipFile(salida1, "r") as zf:
        nombres = set(zf.namelist())
        assert "word/comments.xml" in nombres
        doc_xml = zf.read("word/document.xml").decode("utf-8")
        com_xml = zf.read("word/comments.xml").decode("utf-8")
        ct_xml = zf.read("[Content_Types].xml").decode("utf-8")
        rels_xml = zf.read("word/_rels/document.xml.rels").decode("utf-8")

    assert "/word/comments.xml" in ct_xml
    assert "comments.xml" in rels_xml

    root_doc = ET.fromstring(doc_xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    dels = ["".join(el.itertext()) for el in root_doc.findall(".//w:del", ns)]
    inss = ["".join(el.itertext()) for el in root_doc.findall(".//w:ins", ns)]
    assert "multa será de 10 UF" in dels
    assert "Plazo: 30 días" in dels
    assert "multa será de 5 UF" in inss
    assert "Plazo: 15 días" in inss
    assert len(root_doc.findall(".//w:commentRangeStart", ns)) == 2
    assert len(root_doc.findall(".//w:commentReference", ns)) == 2

    root_com = ET.fromstring(com_xml)
    comentarios = ["".join(c.itertext()) for c in root_com.findall(".//w:comment", ns)]
    assert len(comentarios) == 2
    assert any("«cláusula penal»" in c for c in comentarios)
    assert any("N.° 19.971" in c for c in comentarios)

    # Segunda pasada preserva los comentarios previos y asigna ID único (3)
    res2 = mcp_server.handle_tool_call("docx_aplicar_redline", {
        "input_docx_path": str(salida1),
        "output_docx_path": str(salida2),
        "cambios": [{"buscar": "Vigencia", "comentario": "Confirmar fecha de inicio."}],
    })
    assert res2["ok"] is True
    assert res2["comentarios_insertados"] == 1
    with zipfile.ZipFile(salida2, "r") as zf:
        root_com2 = ET.fromstring(zf.read("word/comments.xml").decode("utf-8"))
        ids = [c.attrib.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id") for c in root_com2.findall(".//w:comment", ns)]
    assert ids == ["1", "2", "3"]
