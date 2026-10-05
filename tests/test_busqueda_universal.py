"""busqueda_universal: el registro del Estado no devuelve una forma única.

Fallaba en vivo con «slice(None, 3, None)»: los conectores mezclan listas (BCN, DT, PJUD) con dicts
que traen «resultados» (CGR, SMA), y las listas incluyen avisos honestos («este conector no cubre…»).
Acá se fija la normalización y que las citas salgan con el corchete oficial.
"""

import mcp_server


class RegistroFalso:
    """Misma mezcla de formas que el registro real, sin salir a la red."""

    def search_all(self, consulta):
        return {
            "query": consulta,
            "bcn": [{"tipo": "aviso", "titulo": "La búsqueda de BCN no cubre esto",
                     "mensaje": "Resuelve por número de ley."}],
            "cgr": {"resultados": [
                {"docId": "E584740", "nombre": "", "materia": "Procede otorgar beneficio",
                 "pdfUrl": "https://www.contraloria.cl/e584740", "texto": "…"},
            ]},
            "dt": [{"titulo": "Dictamen N° 653", "url": "https://dt.gob.cl/653",
                    "resumen": "Sobre acoso laboral."}],
            "sma": {},
            "pjud": [],
        }


def test_normaliza_listas_dicts_y_avisos(monkeypatch):
    monkeypatch.setattr(mcp_server, "_registro_estatal", lambda: RegistroFalso())
    monkeypatch.setattr(mcp_server, "_hf_para_consulta", lambda q, lim=3: {
        "resultados": [{"archivo": "doctrina/laboral/tutela.md"}],
        "citas": [{"formato": "[Hugging Face - doctrina/laboral/tutela.md]", "texto": "texto doctrina",
                   "url": "https://hf.co/tutela", "fuente": "huggingface"}]
    })

    resultado = mcp_server.handle_tool_call("busqueda_universal", {"consulta": "acoso laboral"})

    assert "error" not in resultado, resultado
    # Los avisos no son fuentes: quedan en el payload, no en las citas. Integra HF + órganos estatales.
    assert len(resultado["citas"]) == 3, resultado["citas"]
    fuentes = {c["formato"] for c in resultado["citas"]}
    assert "[CGR - Procede otorgar beneficio]" in fuentes
    assert "[DT - Dictamen N° 653]" in fuentes
    assert "[Hugging Face - doctrina/laboral/tutela.md]" in fuentes
    assert all(c["url"] for c in resultado["citas"]), "cada cita lleva su enlace"


def test_sin_resultados_no_falla_ni_inventa(monkeypatch):
    class RegistroVacio:
        def search_all(self, consulta):
            return {"query": consulta, "sma": {}, "pjud": []}

    monkeypatch.setattr(mcp_server, "_registro_estatal", lambda: RegistroVacio())
    monkeypatch.setattr(mcp_server, "_hf_para_consulta", lambda q, lim=3: {"resultados": [], "citas": []})

    resultado = mcp_server.handle_tool_call("busqueda_universal", {"consulta": "algo"})

    assert resultado["citas"] == []
    assert resultado["resultados"]["query"] == "algo"


def test_la_consulta_es_obligatoria():
    resultado = mcp_server.handle_tool_call("busqueda_universal", {"consulta": "   "})

    assert "error" in resultado
