"""cita_texto en lote: verificar N normas en una sola llamada, con una pasada de red por norma.

Medido el 2026-09-28: la verificación de ~30 citas una por una dominó el tiempo del barrido
forense; en lote, los artículos de una misma ley comparten descarga (detección → dedupe por
norma → pool de 6) y lo que falla queda declarado en `faltantes`, sin rellenarse.
"""

import mcp_server


class _BCNFalso:
    def __init__(self):
        self.leyes_pedidas = []
        self.codigos_pedidos = []

    def get_ley(self, id_ley):
        self.leyes_pedidas.append(id_ley)
        return {"normaId": 1000 + id_ley, "numero": id_ley, "titulo": f"Ley {id_ley}",
                "articulos": {}}

    def get_articulo_ley(self, id_ley, articulo):
        return {"ley": id_ley, "titulo": f"Ley {id_ley}", "articulo": articulo,
                "texto": f"Texto del artículo {articulo} de la Ley {id_ley}."}

    def get_codigo(self, codigo, articulo=None):
        self.codigos_pedidos.append((codigo, articulo))
        return {"codigo": codigo, "articulo": articulo, "fechaVersion": "2026-01-01",
                "texto": f"Texto del artículo {articulo} del {codigo}."}


def test_lote_una_pasada_de_red_por_ley(monkeypatch):
    falso = _BCNFalso()
    monkeypatch.setattr(mcp_server, "_bcn_para_citas", lambda: falso)

    res = mcp_server.handle_tool_call("cita_texto", {"referencias": [
        "Ley 19.300 art. 47",
        "Ley 19.300 art. 48",
        "Ley 20.417 art. 48",
        "Código Civil art. 1438",
    ]})

    assert sorted(falso.leyes_pedidas) == [19300, 20417], (
        f"una descarga por ley única, no por artículo: {falso.leyes_pedidas}"
    )
    assert res["total"] == 4
    assert len(res["citas"]) == 4
    assert res["faltantes"] == []
    formatos = {cita["formato"] for cita in res["citas"]}
    assert "[BCN - Ley N° 19300, Art. 47]" in formatos
    assert "[BCN - Código Civil, Art. 1438]" in formatos


def test_lote_declara_lo_que_no_pudo(monkeypatch):
    falso = _BCNFalso()

    def _articulo_roto(id_ley, articulo):
        if articulo == "9":
            raise RuntimeError("sin red")
        return _BCNFalso().get_articulo_ley(id_ley, articulo)

    falso.get_articulo_ley = _articulo_roto
    monkeypatch.setattr(mcp_server, "_bcn_para_citas", lambda: falso)

    res = mcp_server.handle_tool_call("cita_texto", {"referencias": [
        "Ley 19.300 art. 9",
        "Ley 19.300 art. 10",
        "hola, ¿cómo estás?",
    ]})

    assert res["total"] == 3
    assert len(res["citas"]) == 1
    assert len(res["faltantes"]) == 2
    assert "hola, ¿cómo estás?" in res["faltantes"]
    assert "Ley 19.300 art. 9" in res["faltantes"]


def test_lote_documentado_en_el_esquema():
    """El modo lote tiene que estar en el esquema de la herramienta, no en un comentario."""
    herramienta = next(t for t in mcp_server.TOOLS if t["name"] == "cita_texto")
    propiedades = herramienta["inputSchema"]["properties"]
    assert "referencias" in propiedades
    assert propiedades["referencias"]["type"] == "array"
