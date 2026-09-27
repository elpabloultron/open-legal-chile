"""Las herramientas de conocimiento entregan sus citas con el texto: nadie cita a mano.

Nace del reclamo: «no está citando como es debido y tampoco me da el texto de los artículos».
Cada resultado citable viaja con su corchete oficial y su texto literal; la forma de la respuesta
(lista o dict) no cambia, para no romper a ningún consumidor.
"""

import mcp_server


class _FalsoBCN:
    def get_codigo(self, codigo, articulo=None):
        return {"codigo": "Código Civil de Chile", "articulo": articulo,
                "texto": "Contrato o convención es un acto por el cual una parte se obliga…"}

    def get_articulo_ley(self, id_ley, articulo):
        return {"ley": id_ley, "titulo": "Ley Karin", "articulo": articulo,
                "texto": "Para efectos de esta ley se entenderá por acoso laboral…"}

    def get_ley(self, id_ley):
        return {"normaId": 207436, "numero": id_ley, "titulo": "Código del Trabajo"}


class _FalsoDT:
    def search_dictamenes(self, query, limit=10):
        return [{"titulo": "ORD. N°653/34", "materia": "Fuero maternal: alcance de la protección",
                 "fecha": "10/10/2024", "url": "https://dt.gob.cl/x"}]


class _FalsoCGR:
    def search_jurisprudencia(self, query, **k):
        return {"query": query, "total": 1,
                "resultados": [{"numero": "E123456", "nombre": "Dictamen E123456", "anio": "2024",
                                "texto": "Sobre la confianza legítima en los actos administrativos…",
                                "url": "https://contraloria.cl/x"}]}


class _FalsoAJ:
    def search_guias(self, query, materia=None):
        return [{"titulo": "Guía aplicada para la determinación de penas", "materia": "Penal",
                 "descripcion": "Metodología judicial para el cómputo de marcos penales…",
                 "url_pdf": "https://guias.academiajudicial.cl/x.pdf"}]


def test_bcn_get_codigo_trae_su_cita(monkeypatch):
    monkeypatch.setattr(mcp_server, "bcn", _FalsoBCN())

    res = mcp_server.handle_tool_call("bcn_get_codigo", {"codigo": "civil", "articulo": "1438"})

    cita = res["citas"][0]
    assert cita["formato"] == "[BCN - Código Civil, Art. 1438]"
    assert cita["texto"].startswith("Contrato o convención")
    assert "bcn.cl" in cita["url"]


def test_bcn_get_ley_trae_su_cita(monkeypatch):
    monkeypatch.setattr(mcp_server, "bcn", _FalsoBCN())

    res = mcp_server.handle_tool_call("bcn_get_ley", {"numero": 21643, "articulo": "2"})

    assert res["citas"][0]["formato"] == "[BCN - Ley N° 21643, Art. 2]"
    assert res["citas"][0]["texto"].startswith("Para efectos")


def test_dt_search_trae_citas_por_dictamen(monkeypatch):
    monkeypatch.setattr(mcp_server, "dt", _FalsoDT())

    res = mcp_server.handle_tool_call("dt_search_doctrina", {"query": "fuero maternal"})

    assert isinstance(res, list), "la forma de la herramienta no puede cambiar"
    cita = res[0]["citas"][0]
    assert cita["formato"] == "[Dictamen DT - ORD. N°653/34, 10/10/2024]"
    assert cita["texto"].startswith("Fuero maternal")


def test_cgr_trae_citas_por_dictamen(monkeypatch):
    monkeypatch.setattr(mcp_server, "cgr", _FalsoCGR())

    res = mcp_server.handle_tool_call("cgr_search_jurisprudencia", {"query": "confianza legitima"})

    cita = res["resultados"][0]["citas"][0]
    assert cita["formato"] == "[CGR - Dictamen E123456, 2024]"
    assert cita["texto"]


def test_academia_judicial_trae_citas(monkeypatch):
    monkeypatch.setattr(mcp_server, "aj_client", _FalsoAJ())

    res = mcp_server.handle_tool_call("academia_judicial_buscar_guias", {"query": "penas"})

    assert isinstance(res, list)
    cita = res[0]["citas"][0]
    assert cita["formato"] == "[Academia Judicial - Guía aplicada para la determinación de penas, Penal]"
    assert cita["url"].endswith(".pdf")
