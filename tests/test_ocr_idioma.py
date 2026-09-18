"""
Pruebas del idioma del OCR en el motor forense.

El problema que cubren: `ocr_extract_pdf` leía todo con el modelo inglés de
tesseract, porque `lang` no estaba declarado en el esquema de la herramienta (el
dispatcher sí lo leía, con default 'eng') y, si el modelo pedido faltaba, el
motor caía al que hubiera **sin avisar**. Un expediente chileno escaneado así no
falla: devuelve texto peor, y eso no se nota hasta que el error llega al escrito.
"""

import pytest

from forensic_ocr import ForensicOCREngine
from mcp_server import TOOLS, handle_tool_call

pymupdf = pytest.importorskip("pymupdf")


def _esquema_ocr():
    for herramienta in TOOLS:
        if herramienta["name"] == "ocr_extract_pdf":
            return herramienta["inputSchema"]["properties"]
    pytest.fail("ocr_extract_pdf no está en el catálogo de herramientas")


def _pdf_escaneado(ruta, texto="hola"):
    """Un PDF sin capa de texto útil: obliga a pasar por OCR."""
    doc = pymupdf.open()
    pagina = doc.new_page()
    pagina.insert_text((50, 100), texto, fontsize=8)
    doc.save(str(ruta))
    doc.close()
    return str(ruta)


def test_la_herramienta_declara_idioma_y_dpi():
    props = _esquema_ocr()
    assert "lang" in props, "el modelo no puede elegir idioma si no está en el esquema"
    assert props["lang"]["default"] == "spa"
    assert "spa" in props["lang"]["enum"]
    assert "dpi" in props, "dpi se leía del argumento pero no estaba declarado"


def test_default_del_motor_es_espanol():
    motor = ForensicOCREngine()
    import inspect

    firma = inspect.signature(motor.extract_from_pdf)
    assert firma.parameters["lang"].default == "spa"


def test_avisa_cuando_falta_el_modelo_de_espanol(monkeypatch):
    motor = ForensicOCREngine()
    monkeypatch.setattr(motor, "get_available_languages", lambda: ["eng", "osd"])

    resolucion = motor.resolve_language("spa")

    assert resolucion["solicitado"] == "spa"
    assert resolucion["usado"] == "eng"
    assert "advertencia" in resolucion
    assert "spa" in resolucion["advertencia"]
    assert "tesseract-data-spa" in resolucion["advertencia"]  # dice cómo arreglarlo


def test_no_avisa_cuando_el_modelo_esta_instalado(monkeypatch):
    motor = ForensicOCREngine()
    monkeypatch.setattr(motor, "get_available_languages", lambda: ["spa", "eng", "osd"])

    resolucion = motor.resolve_language("spa")

    assert resolucion["usado"] == "spa"
    assert "advertencia" not in resolucion


def test_mezcla_de_idiomas_conserva_lo_que_existe(monkeypatch):
    motor = ForensicOCREngine()
    monkeypatch.setattr(motor, "get_available_languages", lambda: ["spa", "osd"])

    resolucion = motor.resolve_language("spa+eng")

    assert resolucion["usado"] == "spa"  # no pierde el español por falta de inglés
    assert "eng" in resolucion["advertencia"]


def test_extract_informa_idioma_pedido_y_usado(tmp_path, monkeypatch):
    motor = ForensicOCREngine()
    monkeypatch.setattr(motor, "get_available_languages", lambda: ["eng", "osd"])
    monkeypatch.setattr(motor, "_run_tesseract", lambda img, lang="spa": "TEXTO LEÍDO")

    # Se fija engine="tesseract" a propósito: esta prueba verifica el comportamiento del idioma en
    # Tesseract. Con engine="auto" el resultado depende de qué motores haya instalados (al instalar
    # RapidOCR, el motor elegido pasó a ser rapidocr y la prueba fallaba por el entorno, no por el
    # código). Un motor explícito hace la prueba reproducible en cualquier máquina.
    res = motor.extract_from_pdf(
        _pdf_escaneado(tmp_path / "escaneo.pdf"), force_ocr=True, lang="spa", engine="tesseract"
    )

    assert res["ocr_language_requested"] == "spa"
    assert res["ocr_language"] == "eng"
    assert res["available_languages"] == ["eng", "osd"]
    assert any("spa" in aviso for aviso in res["advertencias"])
    assert res["paginas_con_error"] == 0
    assert all(pagina["ok"] for pagina in res["pages"])


def test_un_fallo_de_ocr_no_pasa_por_texto_del_documento(tmp_path, monkeypatch):
    motor = ForensicOCREngine()
    monkeypatch.setattr(
        motor, "_run_tesseract",
        lambda img, lang="spa": "[Aviso OCR Tesseract: Failed to load language spa]",
    )

    # Motor explícito por la misma razón que la prueba anterior: aquí se simula un fallo de
    # Tesseract, así que el motor no puede quedar al azar de lo que esté instalado.
    res = motor.extract_from_pdf(_pdf_escaneado(tmp_path / "roto.pdf"), force_ocr=True, engine="tesseract")

    assert res["paginas_con_error"] == 1
    assert res["pages"][0]["ok"] is False
    assert any("no devolvió texto" in aviso for aviso in res["advertencias"])


def test_rapidocr_no_advierte_por_tesseract(tmp_path, monkeypatch):
    motor = ForensicOCREngine()
    monkeypatch.setattr(motor, "get_available_languages", lambda: ["eng"])  # sin español
    monkeypatch.setattr(motor, "is_rapidocr_available", lambda: True)
    monkeypatch.setattr(motor, "_run_rapidocr", lambda img: "TEXTO LEÍDO")

    res = motor.extract_from_pdf(_pdf_escaneado(tmp_path / "escaneo2.pdf"), force_ocr=True)

    assert res["ocr_engine_used"] == "rapidocr"
    assert res["ocr_language"] == "multilingüe (rapidocr)"
    assert not any("tesseract" in aviso for aviso in res["advertencias"])


def test_la_herramienta_mcp_pasa_el_idioma(monkeypatch):
    import mcp_server

    visto = {}

    class MotorFalso:
        def extract_from_pdf(self, **argumentos):
            visto.update(argumentos)
            return {"ok": True}

    monkeypatch.setattr(mcp_server, "ocr_engine", MotorFalso())

    handle_tool_call("ocr_extract_pdf", {"pdf_path": "expediente.pdf", "lang": "eng", "dpi": 300})
    assert visto["lang"] == "eng"
    assert visto["dpi"] == 300

    handle_tool_call("ocr_extract_pdf", {"pdf_path": "expediente.pdf"})
    assert visto["lang"] == "spa", "sin argumento, una herramienta chilena debe leer en español"
    assert visto["dpi"] == 150
