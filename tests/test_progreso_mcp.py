"""Las herramientas lentas avisan avance por `notifications/progress` cuando el cliente lo pide.

Sin token (cliente que no pidió avances) no se escribe nada: el protocolo queda igual que antes.
"""

import io
import json

import mcp_server


def _capturar(monkeypatch):
    buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    return buf


def test_sin_token_no_escribe_nada(monkeypatch):
    buf = _capturar(monkeypatch)
    monkeypatch.setattr(mcp_server, "_TOKEN_PROGRESO", None)

    mcp_server.enviar_progreso("nada", 1, 4)

    assert buf.getvalue() == ""


def test_con_token_emite_la_notificacion(monkeypatch):
    buf = _capturar(monkeypatch)
    monkeypatch.setattr(mcp_server, "_TOKEN_PROGRESO", "tok-9")

    mcp_server.enviar_progreso("Hugging Face listo", 1, 4)

    notificacion = json.loads(buf.getvalue().strip())
    assert notificacion["method"] == "notifications/progress"
    assert notificacion["params"] == {"progressToken": "tok-9", "progress": 1, "total": 4,
                                      "message": "Hugging Face listo"}


def test_consulta_maestra_emite_avances(monkeypatch):
    buf = _capturar(monkeypatch)
    monkeypatch.setattr(mcp_server, "_TOKEN_PROGRESO", "tok-9")
    monkeypatch.setattr(mcp_server, "_hf_para_consulta",
                        lambda q, lim=3: {"resultados": [], "citas": []})
    monkeypatch.setattr(mcp_server, "_doctrina_para_consulta",
                        lambda q, lim=3: {"resultados": [], "citas": []})
    monkeypatch.setattr(mcp_server, "_normas_para_consulta", lambda q: [])
    monkeypatch.setattr(mcp_server, "_subgrafo_para_consulta", lambda q, hops=1: {})

    resultado = mcp_server.handle_tool_call("consulta_maestra", {"consulta": "humedales"})

    avisos = [json.loads(linea) for linea in buf.getvalue().splitlines() if linea.strip()]
    avances = sorted(a["params"]["progress"] for a in avisos
                     if a.get("method") == "notifications/progress")
    assert avances == [0, 1, 2, 3, 4], avisos
    assert "faltantes" in resultado


def test_ambiental_emite_avances(monkeypatch):
    buf = _capturar(monkeypatch)
    monkeypatch.setattr(mcp_server, "_TOKEN_PROGRESO", "tok-9")

    class _Modulo:
        @staticmethod
        def consulta_ambiental(consulta, limite=8, incluir_subgrafo=False):
            return {"consulta": consulta}

    monkeypatch.setitem(__import__("sys").modules, "modulo_ambiental", _Modulo)

    resultado = mcp_server.handle_tool_call("ambiental_consulta_maestra", {"consulta": "humedal"})

    avisos = [json.loads(linea) for linea in buf.getvalue().splitlines() if linea.strip()]
    avances = sorted(a["params"]["progress"] for a in avisos
                     if a.get("method") == "notifications/progress")
    assert avances == [1, 3], avisos
    assert resultado == {"consulta": "humedal"}


def test_caso_ejecutar_emite_avance_por_paso(monkeypatch):
    buf = _capturar(monkeypatch)
    monkeypatch.setattr(mcp_server, "_TOKEN_PROGRESO", "tok-9")

    import case_intake

    monkeypatch.setattr(case_intake, "caso_analizar", lambda *a, **k: {
        "plan": [{"herramienta": "bcn_get_codigo", "argumentos": {"codigo": "civil"}},
                 {"herramienta": "bcn_get_codigo", "argumentos": {"codigo": "penal"}}],
        "deteccion": {"roles": [], "documentos": []},
        "materia": "civil", "materia_etiqueta": "Civil", "fuero_probable": "civil",
        "instituciones": [], "faltantes": [], "advertencias": [],
    })
    monkeypatch.setattr(mcp_server, "handle_tool_call", lambda n, a: {"ok": n})

    case_intake.caso_ejecutar(entrada="x")

    avisos = [json.loads(linea) for linea in buf.getvalue().splitlines() if linea.strip()]
    avances = [a["params"]["progress"] for a in avisos
               if a.get("method") == "notifications/progress"]
    assert avances == [1, 2], avisos
