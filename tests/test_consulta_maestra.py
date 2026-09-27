"""consulta_maestra: el primer paso obligatorio de toda consulta jurídica.

El harness solo llama lo que el modelo ve; por eso la secuencia obligatoria (Hugging Face →
doctrina → normas con su texto literal) vive en una sola herramienta que no depende del
criterio del modelo. Nace del reclamo: «no solicitó información a Hugging Face de inmediato».
"""

import mcp_server

CITA_HF = {"formato": "[Hugging Face - repo, Archivo: doctrina/civil/x.md]",
           "texto": "pasaje del corpus", "url": "https://hf.co/x", "fuente": "huggingface"}
CITA_DOCTRINA = {"formato": "[Doctrina - Ramos Pazos, Tomo I]", "texto": "definición",
                 "url": "https://hf.co/d", "fuente": "doctrina"}
NORMA_CC = {"codigo": "Código Civil de Chile", "articulo": "1545",
            "texto": "Contrato o convención es un acto por el cual una parte se obliga…",
            "url": "https://www.bcn.cl/leychile/navegar?idNorma=172986"}


def _parchear(monkeypatch, hf=None, doctrina=None, normas=None, subgrafo=None):
    monkeypatch.setattr(mcp_server, "_hf_para_consulta", lambda q, lim=3: hf or {"resultados": [], "citas": []})
    monkeypatch.setattr(mcp_server, "_doctrina_para_consulta",
                        lambda q, lim=3: doctrina or {"resultados": [], "citas": []})
    monkeypatch.setattr(mcp_server, "_normas_para_consulta", lambda q: normas or [])
    monkeypatch.setattr(mcp_server, "_subgrafo_para_consulta", lambda q, hops=1: subgrafo or {})


def test_consulta_maestra_junta_hf_doctrina_y_normas_con_texto(monkeypatch):
    _parchear(
        monkeypatch,
        hf={"resultados": [{"archivo": "doctrina/civil/x.md"}], "citas": [CITA_HF]},
        doctrina={"resultados": [{"id": 1}], "citas": [CITA_DOCTRINA]},
        normas=[NORMA_CC],
    )

    res = mcp_server.handle_tool_call("consulta_maestra", {"consulta": "¿qué es el contrato? art. 1545"})

    assert res["consulta"].startswith("¿qué es el contrato?")
    fuentes = {c["fuente"] for c in res["citas"]}
    assert {"huggingface", "doctrina", "BCN"} <= fuentes
    assert all(c["texto"] for c in res["citas"]), "ninguna cita puede viajar sin texto"
    assert res["faltantes"] == []
    assert "texto literal" in res["como_citar"]
    bcn = [c for c in res["citas"] if c["fuente"] == "BCN"][0]
    assert bcn["formato"] == "[BCN - Código Civil de Chile, Art. 1545]"


def test_consulta_maestra_marca_lo_que_falta(monkeypatch):
    _parchear(monkeypatch, hf={"resultados": [], "citas": [], "error": "sin red"})

    res = mcp_server.handle_tool_call("consulta_maestra", {"consulta": "hola"})

    assert "huggingface" in res["faltantes"]
    assert res["citas"] == []


def test_consulta_maestra_exige_consulta():
    res = mcp_server.handle_tool_call("consulta_maestra", {})
    assert "error" in res


def test_la_herramienta_esta_declarada_en_el_catalogo():
    nombres = {t["name"] for t in mcp_server.TOOLS}
    assert "consulta_maestra" in nombres
    descripcion = next(t["description"] for t in mcp_server.TOOLS if t["name"] == "consulta_maestra")
    assert "PRIMER PASO" in descripcion
