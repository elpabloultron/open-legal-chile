"""
La búsqueda de la BCN no puede devolver vacío en silencio.

`BCNClient.search` resuelve números de ley, palabras clave de leyes frecuentes y nombres de
códigos; NO es búsqueda de texto libre (el portal de la BCN sólo publica consultas por
idNorma/número). Antes, una consulta como "hipoteca" devolvía [] — indistinguible de "no existe
norma sobre esto" — y así lo leyó quien la usó: se concluyó que no había nada sobre un concepto
que está lleno de normas. Ahora la lista vacía viene con un aviso que dice qué no cubre y por
dónde seguir.

Caso real: 18-09-2026, buscando normas para el caso de una propiedad en copropiedad con hipoteca.
"""

from bcn_connector import BCNClient


def test_concepto_que_no_cubre_avisa_en_vez_de_venir_vacio():
    res = BCNClient().search("hipoteca")

    assert res, "una búsqueda de un concepto no puede devolver una lista vacía y muda"
    aviso = res[0]
    assert aviso.get("tipo") == "aviso", f"se esperaba un aviso, llegó: {aviso}"
    assert "hipoteca" in aviso.get("titulo", "")
    mensaje = aviso.get("mensaje", "").lower()
    assert "no hace búsqueda de texto libre" in mensaje, mensaje
    # Y tiene que decir por dónde seguir, no sólo que no puede.
    assert "doctrina_search" in mensaje or "artículo directo" in mensaje


def test_lo_que_si_resuelve_no_lleva_aviso():
    """Un nombre de código se resuelve con los datos locales: sin red y sin aviso."""
    res = BCNClient().search("civil")

    assert res, "el nombre de un código tiene que resolverse"
    assert all(r.get("tipo") != "aviso" for r in res), res
    assert any(r.get("tipo") == "Código" for r in res), res
