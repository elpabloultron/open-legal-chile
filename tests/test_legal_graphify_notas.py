"""Las notas de modificación del margen no son artículos (vía de texto corrido de LegalGraphify).

Medido sobre el Código Civil de la caché real, unido en un solo texto: 150 de los 2.901 cortes por «Art.»
eran notas del margen («Art. 1º, Nº 2», «Art. 16»). Cada una, leída como «Artículo 1», hacía retroceder la
numeración y partía el código en 75 cuerpos: el principal conservaba 794 de 2.567 artículos.
"""

from legal_graphify import extract_articulos_de_codigo

CODIGO = "Código de Prueba"

TEXTO = """\
Art. 1º. La ley es una declaración de la voluntad soberana.
Art. 1º, Nº 2
Art. 2º. La costumbre no constituye derecho sino en los casos en que la ley se remite a ella.
Art. 16
Art. 3º. Sólo toca al legislador explicar o interpretar la ley de un modo generalmente obligatorio.
Art. 1º Nº 25
Art. 4. Las disposiciones contenidas en los Códigos de Comercio, de Minería y otros.
Art. 67
                                                                    L. 19.250
Art. 5º. La Corte Suprema de Justicia y las Cortes de Alzada, en el mes de marzo.
"""


def _articulos(grafo):
    return {d["label"].rsplit("Art. ", 1)[1]: d["texto"]
            for _, d in grafo.nodes(data=True) if d.get("node_type") == "articulo_legal"}


def test_las_notas_del_margen_no_parten_el_codigo():
    articulos = _articulos(extract_articulos_de_codigo(CODIGO, TEXTO))
    assert list(articulos) == ["1", "2", "3", "4", "5"]
    assert articulos["1"].startswith("La ley es una declaración de la voluntad soberana")
    assert "Nº 2" in articulos["1"], "la nota queda dentro del artículo al que acompaña"
    assert articulos["4"].startswith("Las disposiciones contenidas")
    assert "L. 19.250" in articulos["4"]
