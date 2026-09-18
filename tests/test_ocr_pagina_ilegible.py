"""
El OCR no puede reportar éxito cuando no leyó nada.

Caso real (18-09-2026): dos boletas notariales fotografiadas (compraventa/mutuo/hipoteca y el
impuesto del mutuo de la causa de Ailin Astorga). Con Tesseract devolvían 0 caracteres en
cualquier orientación y el extractor las informaba como `ok: true, length: 0` — o sea, "éxito
silencioso": quien lo consumía concluía que la página estaba en blanco, cuando en realidad eran
fotos que el motor no podía leer. Con RapidOCR, las mismas páginas dieron 553 y 525 caracteres.

Estas pruebas fijan que una página que no rinde texto del documento quede no-ok, se cuente como
error y venga con un aviso ACCIONABLE. Se escribieron sin asumir un modo de falla concreto: según
lo que haya instalado (motor de OCR, modelo de idioma) la razón cambia —"no extrajo ni un
carácter" o "el modelo de idioma 'spa' no está instalado"— y en las dos el aviso tiene que decir
qué hacer. La primera versión de estas pruebas asumía el caso local y falló en CI, que no tiene el
modelo español: el test estaba mal, no el código.
"""

import pymupdf
import pytest

from forensic_ocr import ForensicOCREngine


@pytest.fixture(scope="module")
def motor():
    return ForensicOCREngine()


def _pdf_de_una_pagina(destino, con_texto=False):
    doc = pymupdf.open()
    pagina = doc.new_page(width=595, height=842)
    if con_texto:
        pagina.insert_text((72, 100), "COMPRAVENTA MUTUO HIPOTECA 130.000", fontsize=12)
    doc.save(str(destino))
    doc.close()
    return destino


def test_pagina_sin_texto_no_se_reporta_como_exito(motor, tmp_path):
    """Una página de la que no se extrajo texto del documento no puede quedar como ok:true."""
    pdf = _pdf_de_una_pagina(tmp_path / "ilegible.pdf")
    res = motor.extract_from_pdf(str(pdf))

    pagina = res["pages"][0]
    assert pagina["ok"] is False, (
        "una página ilegible quedó marcada como ok:true (éxito silencioso): "
        f"método={pagina['method']} motor={pagina['engine']}"
    )
    assert pagina["length"] == 0, (
        "'length' debe medir texto extraído del documento, no el mensaje de diagnóstico: "
        f"{pagina['length']} caracteres ({str(pagina['text'])[:80]!r})"
    )
    assert res["paginas_con_error"] >= 1


def test_pagina_ilegible_dice_como_arreglarlo(motor, tmp_path):
    """El aviso tiene que ser accionable: qué hacer, no solo que falló."""
    pdf = _pdf_de_una_pagina(tmp_path / "ilegible2.pdf")
    res = motor.extract_from_pdf(str(pdf))
    avisos = res.get("advertencias") or []

    assert avisos, "una página que no se pudo leer tiene que dejar aviso"
    # El motivo depende del entorno (sin motor robusto, sin modelo de idioma...); lo que no puede
    # cambiar es que indique cómo resolverlo.
    assert any(
        ("instala" in a.lower()) or ("fotograf" in a.lower()) or ("modelo de idioma" in a.lower())
        for a in avisos
    ), f"el aviso no dice qué hacer: {avisos}"
