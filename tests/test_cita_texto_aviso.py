"""cita_texto no calla lo que el conector BCN advierte sobre el cuerpo del que salió el artículo.

El parser de la BCN marca `aviso_cuerpos` (norma con varios cuerpos de peso parecido, como la Ley 20.416)
y `cuerpo: "anexo"` (artículo ordinal tomado de un texto aprobado dentro de la ley). Sin pasar ese aviso
a la respuesta, la cita salía con su corchete oficial y nada que advirtiera al lector.
"""

import mcp_server


class _BCNConAviso:
    def get_ley(self, id_ley):
        return {"normaId": 1, "numero": id_ley, "titulo": "Ley de prueba"}

    def get_articulo_ley(self, id_ley, articulo):
        return {"ley": id_ley, "titulo": "Ley de prueba", "articulo": articulo,
                "texto": "Ámbito de aplicación…",
                "aviso_cuerpos": "La norma contiene 5 cuerpos con numeración propia y ninguno domina."}

    def get_codigo(self, codigo, articulo=None):
        return {"codigo": "Código Civil de Chile", "articulo": articulo, "texto": "Contrato o convención…",
                "cuerpo": "anexo", "cuerpo_indice": 3}


class _BCNSinAviso:
    def get_articulo_ley(self, id_ley, articulo):
        return {"ley": id_ley, "articulo": articulo, "texto": "Texto del artículo."}

    def get_codigo(self, codigo, articulo=None):
        return {"codigo": "Código Civil de Chile", "articulo": articulo, "texto": "Contrato o convención…"}


def test_cita_texto_pasa_el_aviso_de_cuerpos(monkeypatch):
    monkeypatch.setattr(mcp_server, "_bcn_para_citas", lambda: _BCNConAviso())
    res = mcp_server.handle_tool_call("cita_texto", {"referencia": "Ley 20.416 art. 1"})
    assert res["citas"][0]["texto"].startswith("Ámbito")
    assert "5 cuerpos" in res["aviso"]


def test_cita_texto_avisa_cuando_el_articulo_vino_de_un_anexo(monkeypatch):
    monkeypatch.setattr(mcp_server, "_bcn_para_citas", lambda: _BCNConAviso())
    res = mcp_server.handle_tool_call("cita_texto", {"referencia": "Código Civil art. 17"})
    assert "cuerpo anexo" in res["aviso"]


def test_cita_texto_sin_aviso_no_inventa_uno(monkeypatch):
    monkeypatch.setattr(mcp_server, "_bcn_para_citas", lambda: _BCNSinAviso())
    res = mcp_server.handle_tool_call("cita_texto", {"referencia": "Código Civil art. 1438"})
    assert "aviso" not in res and res["citas"]


def test_el_lote_conserva_el_aviso_por_referencia(monkeypatch):
    monkeypatch.setattr(mcp_server, "_bcn_para_citas", lambda: _BCNConAviso())
    res = mcp_server.handle_tool_call("cita_texto", {"referencias": ["Ley 20.416 art. 1", "Código Civil art. 17"]})
    avisos = [r.get("aviso") for r in res["resultados"]]
    assert all(avisos), avisos
