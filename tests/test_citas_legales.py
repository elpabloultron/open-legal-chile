"""El formato oficial de citas (AGENTS.md §2) en un solo lugar, con su texto literal."""

import citas_legales


def test_formato_oficial_de_cita():
    c = citas_legales.formatear_cita("BCN", "Código Civil, Art. 1545",
                                     url="https://bcn.cl/x", texto="Contrato o convención…")
    assert c["formato"] == "[BCN - Código Civil, Art. 1545]"
    assert c["texto"].startswith("Contrato")
    assert c["url"] == "https://bcn.cl/x"
    assert c["cita_completa"].endswith("https://bcn.cl/x")


def test_bloque_de_fuentes_numerado():
    bloque = citas_legales.bloque_fuentes([
        citas_legales.formatear_cita("BCN", "Código Civil, Art. 1545", url="https://bcn.cl/x", texto="t"),
        citas_legales.formatear_cita("Dictamen DT", "N° 1234/15 de 2024", url="https://dt.gob.cl/y", texto="t"),
    ])
    assert bloque.startswith("---\nFuentes:")
    assert "1. [BCN - Código Civil, Art. 1545] https://bcn.cl/x" in bloque
    assert "2. [Dictamen DT - N° 1234/15 de 2024] https://dt.gob.cl/y" in bloque


def test_detecta_normas_en_texto_libre():
    normas = citas_legales.detectar_normas("¿Qué dice el artículo 1545 del Código Civil y la Ley 21.643?")
    familias = {n["familia"] for n in normas}
    assert "codigo" in familias and "ley" in familias
    codigo = [n for n in normas if n["familia"] == "codigo"][0]
    assert codigo["obra"] == "civil"
    assert codigo["articulo"] == "1545"
    assert codigo["etiqueta"] == "BCN - Código Civil, Art. 1545"
    ley = [n for n in normas if n["familia"] == "ley"][0]
    assert ley["numero"] == "21643"


def test_detecta_normas_en_orden_inverso():
    """«Código del Trabajo art. 161» y «el artículo 161 del Código del Trabajo» son la misma norma."""
    for texto in ("Código del Trabajo art. 161", "el artículo 161 del Código del Trabajo"):
        normas = citas_legales.detectar_normas(texto)
        assert normas, f"no detectó nada en: {texto}"
        assert normas[0]["obra"] == "trabajo" and normas[0]["articulo"] == "161"


def test_no_inventa_normas_donde_no_las_hay():
    assert citas_legales.detectar_normas("hola, ¿cómo estás?") == []
