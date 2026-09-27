"""cita_texto: el texto literal de la norma que se cita, o un aviso honesto.

Nace del reclamo: «tampoco está dándome el texto de los artículos que está citando, que debería».
El producto no cita sin texto: si la fuente no responde, lo dice y no inventa.
"""

import mcp_server


class _FalsoBCN:
    def get_codigo(self, codigo, articulo=None):
        return {"codigo": "Código Civil de Chile", "articulo": articulo, "fechaVersion": "2024-01-15",
                "texto": "Contrato o convención es un acto por el cual una parte se obliga para con otra…"}

    def get_articulo_ley(self, id_ley, articulo):
        return {"ley": id_ley, "titulo": "Ley que modifica el Código del Trabajo", "articulo": articulo,
                "texto": "Introdúcense las siguientes modificaciones…"}

    def get_ley(self, id_ley):
        return {"normaId": 123456, "numero": id_ley, "titulo": "Ley de prueba", "articulos": {}}


def test_cita_texto_resuelve_un_codigo(monkeypatch):
    monkeypatch.setattr(mcp_server, "_bcn_para_citas", lambda: _FalsoBCN())

    res = mcp_server.handle_tool_call("cita_texto", {"referencia": "Código Civil art. 1438"})

    cita = res["citas"][0]
    assert cita["formato"] == "[BCN - Código Civil, Art. 1438]"
    assert cita["texto"].startswith("Contrato o convención")
    assert cita["url"].startswith("https://www.bcn.cl/")


def test_cita_texto_acepta_ley_con_articulo(monkeypatch):
    monkeypatch.setattr(mcp_server, "_bcn_para_citas", lambda: _FalsoBCN())

    res = mcp_server.handle_tool_call("cita_texto", {"referencia": "el artículo 2 de la Ley 21.643"})

    assert res["citas"][0]["formato"] == "[BCN - Ley N° 21643, Art. 2]"
    assert res["citas"][0]["texto"]


def test_cita_texto_es_honesta_cuando_no_puede(monkeypatch):
    def explota():
        raise RuntimeError("sin red")

    monkeypatch.setattr(mcp_server, "_bcn_para_citas", explota)

    res = mcp_server.handle_tool_call("cita_texto", {"referencia": "Código Civil art. 1438"})

    assert res.get("sin_fuente_verificable") is True
    assert "error" in res


def test_cita_texto_rechaza_lo_que_no_es_una_norma():
    res = mcp_server.handle_tool_call("cita_texto", {"referencia": "hola, ¿cómo estás?"})
    assert res.get("sin_fuente_verificable") is True


def test_cita_texto_esta_en_el_catalogo():
    assert "cita_texto" in {t["name"] for t in mcp_server.TOOLS}
