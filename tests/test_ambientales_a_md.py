"""Candado del conversor de sentencias ambientales a Markdown.

Regla del producto: se extrae el **texto íntegro** (nada resumido) y los PDFs escaneados
pasan por el OCR de la casa. El test comprueba que el último párrafo del original llega
al Markdown.
"""
import importlib.util
import pathlib
import shutil

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
requiere_poppler = pytest.mark.skipif(
    shutil.which("pdftotext") is None, reason="requiere poppler (pdftotext)")


def _modulo():
    spec = importlib.util.spec_from_file_location(
        "ambientales_a_md", RAIZ / "scripts" / "ambientales_a_md.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _pdf_con_texto(tmp_path) -> pathlib.Path:
    fitz = pytest.importorskip("fitz")
    doc = fitz.open()
    pagina = doc.new_page()
    lineas = [
        "PRIMERA LÍNEA DEL ORIGINAL EN EL EXPEDIENTE AMBIENTAL.",
        "SENTENCIA AMBIENTAL. Santiago, dos de mayo de dos mil veintiséis.",
        "VISTOS: se ha presentado demanda de reparación por daño ambiental.",
        "CONSIDERANDO: que la demandante alega afectación al ecosistema.",
        "ÚLTIMA LÍNEA DEL ORIGINAL ANTES DE LA FIRMA.",
    ]
    for indice, linea in enumerate(lineas):
        pagina.insert_text((72, 90 + indice * 16), linea, fontsize=9)
    ruta = tmp_path / "sentencia.pdf"
    doc.save(str(ruta))
    return ruta


def _registro() -> dict:
    return {
        "tribunal": "2TA", "tribunal_nombre": "Segundo Tribunal Ambiental",
        "jurisdiccion": "Región de Valparaíso", "rol": "45-2026", "tipo": "Sentencia",
        "caratula": "COMUNIDAD c/ PROYECTO", "fecha": "2026-05-02",
        "redactor": "Ministra X", "integracion": "Ministros A, B y C", "materia": "Daño ambiental",
        "resuelve": "Acoge", "url_pdf": "https://www.portaljudicial1ta.cl/ejemplo.pdf",
        "url_expediente": "https://www.portaljudicial1ta.cl/expediente",
    }


@requiere_poppler
def test_convierte_pdf_con_capa_de_texto(tmp_path):
    mod = _modulo()
    estado, archivo, caracteres, metodo = mod.convertir(
        _registro(), _pdf_con_texto(tmp_path), tmp_path / "salida")

    assert estado == "ok", archivo
    assert archivo == "2TA/45-2026.md"
    md = tmp_path / "salida" / "2TA" / "45-2026.md"
    texto = md.read_text(encoding="utf-8")
    assert "PRIMERA LÍNEA DEL ORIGINAL EN EL EXPEDIENTE AMBIENTAL." in texto
    assert "ÚLTIMA LÍNEA DEL ORIGINAL ANTES DE LA FIRMA." in texto, "el texto no se resume"
    assert "Segundo Tribunal Ambiental" in texto and "45-2026" in texto
    assert "[Hugging Face - jurisprudencia_ambiental/2TA/45-2026.md]" in texto
    assert caracteres > 50


def test_pdf_que_no_responde_queda_como_ficha(tmp_path, monkeypatch):
    mod = _modulo()
    monkeypatch.setattr(mod, "DIR_MD", tmp_path / "salida")
    monkeypatch.setattr(mod, "DIR_PDF", tmp_path / "pdf")

    def sin_pdf(url, destino):
        raise RuntimeError("404 Client Error")

    monkeypatch.setattr(mod, "descargar", sin_pdf)
    indice, resultado = mod.procesar((0, _registro()))

    assert resultado.startswith("ficha|"), resultado
    md = tmp_path / "salida" / "2TA" / "45-2026.md"
    texto = md.read_text(encoding="utf-8")
    assert "Ficha de metadatos" in texto and "No se inventa contenido" in texto
    assert "45-2026" in texto


@requiere_poppler
def test_pdf_escaneado_pasa_por_ocr(tmp_path, monkeypatch):
    mod = _modulo()
    fitz = pytest.importorskip("fitz")
    doc = fitz.open()
    pagina = doc.new_page()
    pagina.draw_rect(fitz.Rect(50, 50, 500, 700), color=(0, 0, 0), fill=(0.9, 0.9, 0.9))
    ruta = tmp_path / "escaneada.pdf"
    doc.save(str(ruta))

    llamadas = {}

    def falso(pdf, max_paginas=None):
        llamadas["max_paginas"] = max_paginas
        relleno = "TEXTO POR OCR DE LA PÁGINA. " * 12
        return (relleno + "\nÚLTIMA LÍNEA DEL ORIGINAL ANTES DE LA FIRMA.", "ocr:rapidocr")

    monkeypatch.setattr(mod.ing, "_texto_de_pdf", falso)
    estado, archivo, caracteres, metodo = mod.convertir(
        _registro(), ruta, tmp_path / "salida")

    assert estado == "ok", archivo
    assert llamadas["max_paginas"] == 120, "los escaneos se OCR-ean completos (tope 120 páginas)"
    texto = (tmp_path / "salida" / "2TA" / "45-2026.md").read_text(encoding="utf-8")
    assert "ÚLTIMA LÍNEA DEL ORIGINAL ANTES DE LA FIRMA." in texto
