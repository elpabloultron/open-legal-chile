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


def test_los_codigos_procesales_con_nombre_completo_no_se_confunden():
    """«Código de Procedimiento Civil art. 66» se resolvía como Código Civil art. 66, y «Código
    Procesal Penal art. 140» como Código Penal art. 140: cita_texto devolvía el artículo de otro
    código con su corchete oficial."""
    from citas_legales import detectar_normas

    casos = {
        "Código de Procedimiento Civil art. 66": ("cpc", "66"),
        "el artículo 254 del Código de Procedimiento Civil": ("cpc", "254"),
        "art. 254 CPC": ("cpc", "254"),
        "Código Procesal Penal art. 140": ("cpp", "140"),
        "según el artículo 140 del Código Procesal Penal": ("cpp", "140"),
        "Código Penal art. 391": ("penal", "391"),
        "Código Civil art. 1545": ("civil", "1545"),
    }
    for texto, esperado in casos.items():
        normas = detectar_normas(texto)
        assert [(n["obra"], n["articulo"]) for n in normas] == [esperado], (texto, normas)
    assert detectar_normas("Código de Procedimiento Civil art. 66")[0]["etiqueta"] == \
        "BCN - Código de Procedimiento Civil, Art. 66"


def test_inferencia_segura_codigo_matriz():
    """Artículos huérfanos con marcadores inequívocos de un único código chileno se asocian a ese código matriz."""
    from citas_legales import detectar_normas

    # Trabajo
    normas = detectar_normas("despido por necesidades de la empresa art. 161")
    assert len(normas) == 1
    assert normas[0]["tipo"] == "codigo"
    assert normas[0]["codigo"] == "trabajo"
    assert normas[0]["articulo"] == "161"
    assert normas[0]["etiqueta"] == "BCN - Código del Trabajo, Art. 161"

    # Civil
    normas_civ = detectar_normas("demanda de responsabilidad extracontractual art. 2314")
    assert len(normas_civ) == 1
    assert normas_civ[0]["codigo"] == "civil"
    assert normas_civ[0]["articulo"] == "2314"
    assert normas_civ[0]["etiqueta"] == "BCN - Código Civil, Art. 2314"

    # CPC
    normas_cpc = detectar_normas("solicita abandono del procedimiento art. 152")
    assert len(normas_cpc) == 1
    assert normas_cpc[0]["codigo"] == "cpc"
    assert normas_cpc[0]["articulo"] == "152"
    assert normas_cpc[0]["etiqueta"] == "BCN - Código de Procedimiento Civil, Art. 152"

    # Conflicto entre múltiples códigos: no inventa ni asume
    assert detectar_normas("despido e incumplimiento contractual art. 161") == []

    # Sin marcadores inequívocos: no inventa norma
    assert detectar_normas("art. 161") == []

