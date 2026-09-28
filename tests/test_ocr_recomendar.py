"""Candado de `ocr_plan_documento`: la recomendación de OCR razonada según el derecho chileno.

La herramienta no decide: mide el PDF, aplica reglas explícitas y devuelve opciones con su
fundamento. El harness elige con esa información.
"""
import mcp_server
import ocr_decision


def _pdf_de_prueba(tmp_path, con_texto: bool):
    import fitz
    doc = fitz.open()
    pagina = doc.new_page()
    if con_texto:
        pagina.insert_text((72, 100), "En Santiago, a veinticuatro de septiembre de dos mil veintiseis, se notificó")
        pagina.insert_text((72, 116), "la resolución que ordena el traslado al demandado por el plazo de diez días.")
    else:
        pagina.draw_rect(fitz.Rect(50, 50, 500, 700), color=(0, 0, 0), fill=(0.9, 0.9, 0.9))
    ruta = tmp_path / ("con_texto.pdf" if con_texto else "escaneado.pdf")
    doc.save(str(ruta))
    return ruta


def test_pdf_con_capa_de_texto_no_se_reinterpreta(tmp_path):
    plan = ocr_decision.recomendar_ocr(_pdf_de_prueba(tmp_path, con_texto=True))
    assert plan["recomendado"]["modo"] == "nativo"
    assert "no se reinterpreta" in " ".join(plan["razonamiento"]).lower()


def test_escaneo_judicial_recomienda_rapidocr_300(tmp_path):
    plan = ocr_decision.recomendar_ocr(_pdf_de_prueba(tmp_path, con_texto=False),
                                       contexto="expediente judicial, hay plazo corriendo")
    assert plan["recomendado"]["engine"] == "rapidocr"
    assert plan["recomendado"]["dpi"] >= 300
    assert plan["recomendado"]["lang"] == "spa"
    assert plan["como_ejecutar"]["herramienta"] == "ocr_extract_pdf"
    assert any("66" in r for r in plan["razonamiento"]), "cuando hay plazo, se razona sobre el art. 66 CPC"


def test_la_herramienta_mcp_expone_el_plan(tmp_path, monkeypatch):
    monkeypatch.setattr(ocr_decision, "_ruta_existe", lambda r: True)
    res = mcp_server.handle_tool_call("ocr_plan_documento",
                                      {"pdf_path": str(tmp_path / "x.pdf"), "contexto": "escritura notarial de 1978"})
    assert "recomendado" in res and "razonamiento" in res and "avisos" in res
    assert res["recomendado"]["engine"] in ("rapidocr", "tesseract", "paddleocr", "nativo")
