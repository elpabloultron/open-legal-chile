"""consulta_maestra: el primer paso obligatorio de toda consulta jurídica.

El harness solo llama lo que el modelo ve; por eso la secuencia obligatoria (Hugging Face →
organismos del Estado → doctrina → normas con su texto literal) vive en una sola herramienta
que no depende del criterio del modelo. Nace del reclamo: «no solicitó información a Hugging Face
de inmediato».
"""

import mcp_server

CITA_HF = {"formato": "[Hugging Face - repo, Archivo: doctrina/civil/x.md]",
           "texto": "pasaje del corpus", "url": "https://hf.co/x", "fuente": "huggingface"}
CITA_DOCTRINA = {"formato": "[Doctrina - Ramos Pazos, Tomo I]", "texto": "definición",
                 "url": "https://hf.co/d", "fuente": "doctrina"}
CITA_ORGANISMO = {"formato": "[PJUD - Rol N° 1234-2023]", "texto": "fallo judicial",
                  "url": "https://pjud.cl/1234", "fuente": "pjud"}
NORMA_CC = {"codigo": "Código Civil de Chile", "articulo": "1545",
            "texto": "Contrato o convención es un acto por el cual una parte se obliga…",
            "url": "https://www.bcn.cl/leychile/navegar?idNorma=172986"}


def _parchear(monkeypatch, hf=None, doctrina=None, normas=None, subgrafo=None, organismos=None):
    monkeypatch.setattr(mcp_server, "_hf_para_consulta", lambda q, lim=3: hf or {"resultados": [], "citas": []})
    monkeypatch.setattr(mcp_server, "_doctrina_para_consulta",
                        lambda q, lim=3: doctrina or {"resultados": [], "citas": []})
    monkeypatch.setattr(mcp_server, "_normas_para_consulta", lambda q: normas or [])
    monkeypatch.setattr(mcp_server, "_subgrafo_para_consulta", lambda q, hops=1: subgrafo or {})
    monkeypatch.setattr(mcp_server, "_organismos_para_consulta",
                        lambda q, lim=3: organismos or {"organismos": [], "resultados": {}, "citas": []})


def test_consulta_maestra_junta_hf_doctrina_y_normas_con_texto(monkeypatch):
    _parchear(
        monkeypatch,
        hf={"resultados": [{"archivo": "doctrina/civil/x.md"}], "citas": [CITA_HF]},
        doctrina={"resultados": [{"id": 1}], "citas": [CITA_DOCTRINA]},
        normas=[NORMA_CC],
        organismos={"organismos": ["pjud"], "resultados": {"pjud": [{"title": "Rol 1234"}]}, "citas": [CITA_ORGANISMO]},
    )

    res = mcp_server.handle_tool_call("consulta_maestra", {"consulta": "¿qué es el contrato? art. 1545"})

    assert res["consulta"].startswith("¿qué es el contrato?")
    fuentes = {c["fuente"] for c in res["citas"]}
    assert {"huggingface", "doctrina", "BCN", "pjud"} <= fuentes
    assert all(c["texto"] for c in res["citas"]), "ninguna cita puede viajar sin texto"
    assert res["faltantes"] == []
    assert "texto literal" in res["como_citar"]
    bcn = [c for c in res["citas"] if c["fuente"] == "BCN"][0]
    assert bcn["formato"] == "[BCN - Código Civil de Chile, Art. 1545]"


def test_consulta_maestra_marca_lo_que_falta(monkeypatch):
    _parchear(monkeypatch, hf={"resultados": [], "citas": [], "error": "sin red"})

    res = mcp_server.handle_tool_call("consulta_maestra", {"consulta": "hola"})

    assert "huggingface" in res["faltantes"]
    assert "organismos" in res["faltantes"]
    assert res["citas"] == []


def test_consulta_maestra_exige_consulta():
    res = mcp_server.handle_tool_call("consulta_maestra", {})
    assert "error" in res


def test_la_herramienta_esta_declarada_en_el_catalogo():
    nombres = {t["name"] for t in mcp_server.TOOLS}
    assert "consulta_maestra" in nombres
    descripcion = next(t["description"] for t in mcp_server.TOOLS if t["name"] == "consulta_maestra")
    assert "PRIMER PASO" in descripcion


def test_los_sondeos_corren_en_paralelo(monkeypatch):
    """Los cinco sondeos son independientes: el tiempo total no puede ser la suma."""
    import time

    def _lento(valor):
        def _fn(*a, **k):
            time.sleep(0.4)
            return valor
        return _fn
    monkeypatch.setattr(mcp_server, "_hf_para_consulta", _lento({"resultados": [], "citas": []}))
    monkeypatch.setattr(mcp_server, "_doctrina_para_consulta", _lento({"resultados": [], "citas": []}))
    monkeypatch.setattr(mcp_server, "_normas_para_consulta", _lento([]))
    monkeypatch.setattr(mcp_server, "_subgrafo_para_consulta", _lento({}))
    monkeypatch.setattr(mcp_server, "_organismos_para_consulta", _lento({"organismos": [], "resultados": {}, "citas": []}))

    t0 = time.time()
    mcp_server.handle_tool_call("consulta_maestra", {"consulta": "humedales", "max_fuentes": 1})
    transcurrido = time.time() - t0

    assert transcurrido < 1.0, f"secuencial tardaría ≥2.0 s; tardó {transcurrido:.2f} s"


def test_detector_de_dominios_estatales():
    """Comprueba que el clasificador heurístico identifique los órganos del Estado pertinentes."""
    assert "dt" in mcp_server._detectar_dominios_estatales("despido injustificado trabajador")
    assert "cgr" in mcp_server._detectar_dominios_estatales("sumario administrativo funcionario publico")
    assert "sii" in mcp_server._detectar_dominios_estatales("liquidacion de impuesto iva")
    assert "sma" in mcp_server._detectar_dominios_estatales("sancion ambiental superintendencia rca")
    assert "pjud" in mcp_server._detectar_dominios_estatales("contrato civil incumplimiento")

