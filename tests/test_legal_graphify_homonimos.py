"""La ingesta de códigos al grafo no pisa artículos homónimos (Frente 0).

El texto completo de un código del BCN trae, además del código, sus leyes anexas y sus transitorios,
y en todos hay un «Artículo 1». El nodo del grafo se identifica por «<código>, Art. N»; recorriendo
el texto sin distinguir cuerpos, el último «Artículo 1» reemplazaba los atributos del primero.
"""

from legal_graphify import extract_articulos_de_codigo

CODIGO = "Código Civil"

TEXTO_CON_ANEXA = """
Artículo 1º. La ley es una declaración de la voluntad soberana que, manifestada en la forma
prescrita por la Constitución, manda, prohíbe o permite.

Art. 2º. La costumbre no constituye derecho sino en los casos en que la ley se remite a ella.

Art. 3º. Sólo toca al legislador explicar o interpretar la ley de un modo generalmente obligatorio.

Art. 4. Las disposiciones contenidas en los Códigos de Comercio, de Minería y otros.

Art. 1.º Los impuestos sobre asignaciones por causa de muerte y donaciones se regirán por esta ley.

Art. 2.º El impuesto se aplicará sobre el valor líquido de cada asignación.
"""


def _articulos(grafo):
    return {d["label"]: d["texto"] for _, d in grafo.nodes(data=True) if d.get("node_type") == "articulo_legal"}


def test_el_articulo_1_del_codigo_no_lo_pisa_el_de_una_ley_anexa():
    articulos = _articulos(extract_articulos_de_codigo(CODIGO, TEXTO_CON_ANEXA))

    assert set(articulos) == {f"{CODIGO}, Art. {n}" for n in ("1", "2", "3", "4")}
    assert articulos[f"{CODIGO}, Art. 1"].startswith("La ley es una declaración de la voluntad soberana")
    assert "impuestos" not in articulos[f"{CODIGO}, Art. 2"]


def test_una_remision_en_minuscula_a_mitad_de_frase_no_es_un_articulo():
    texto = (
        "Art. 5. El plazo se cuenta según lo dispuesto en el\n"
        "artículo 12 de esta ley y en lo demás se aplica la regla general.\n\n"
        "Art. 12. Los plazos de días son completos.\n"
    )
    articulos = _articulos(extract_articulos_de_codigo(CODIGO, texto))
    assert set(articulos) == {f"{CODIGO}, Art. 5", f"{CODIGO}, Art. 12"}
    assert articulos[f"{CODIGO}, Art. 12"].startswith("Los plazos de días son completos")


def test_con_el_mapa_del_conector_no_se_reinterpreta_ningun_texto():
    mapa = {
        "1": "Artículo 1º. La ley es una declaración de la voluntad soberana.",
        "25 quáter": "Artículo 25 quáter.- Regla intermedia.",
    }
    articulos = _articulos(extract_articulos_de_codigo(CODIGO, "", articulos=mapa))
    assert articulos == {
        f"{CODIGO}, Art. 1": "La ley es una declaración de la voluntad soberana.",
        f"{CODIGO}, Art. 25 quáter": "Regla intermedia.",
    }
