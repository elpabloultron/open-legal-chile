"""Las seis capacidades que vivían solo en la terminal, ahora dentro del harness."""

import json
import pathlib

import mcp_server


def test_suite_doctor_devuelve_el_diagnostico_medido():
    res = mcp_server.handle_tool_call("suite_doctor", {})

    assert res["estado"] in ("ok", "degradado", "error")
    nombres = {c["nombre"] for c in res["chequeos"]}
    assert {"ocr", "corpus", "grafo", "herramientas_mcp"} <= nombres


def test_ocr_plan_documento_esta_en_el_catalogo_y_razona(tmp_path, monkeypatch):
    import ocr_decision

    assert "ocr_plan_documento" in {t["name"] for t in mcp_server.TOOLS}
    monkeypatch.setattr(ocr_decision, "_ruta_existe", lambda r: True)
    res = mcp_server.handle_tool_call("ocr_plan_documento",
                                      {"pdf_path": str(tmp_path / "escaneo.pdf"),
                                       "contexto": "expediente con plazo de notificación"})
    assert res["recomendado"]["modo"] in ("nativo", "ocr")
    assert res["razonamiento"] and "como_ejecutar" in res


def test_busqueda_universal_agrega_citas(monkeypatch):
    class FalsoRegistro:
        def search_all(self, consulta):
            return {"bcn": [{"nombre": "Ley 21.643", "url": "https://bcn.cl/x",
                             "resumen": "Modifica el Código del Trabajo en materia de prevención"}]}

    monkeypatch.setattr(mcp_server, "_registro_estatal", lambda: FalsoRegistro())

    res = mcp_server.handle_tool_call("busqueda_universal", {"consulta": "Ley Karin"})

    assert res["citas"][0]["formato"] == "[BCN - Ley 21.643]"
    assert res["citas"][0]["texto"].startswith("Modifica")
    assert res["resultados"]["bcn"]


def test_critique_documento_envuelve_la_auditoria(monkeypatch):
    import critique as modulo_critique

    class FalsoMotor:
        llamado = None

        def critique(self, texto, provider=None):
            FalsoMotor.llamado = (texto, provider)
            return {"critique": "Informe forense de prueba"}

    monkeypatch.setattr(modulo_critique, "LegalCritiqueEngine", lambda: FalsoMotor())

    res = mcp_server.handle_tool_call("critique_documento", {"texto": "EN LO PRINCIPAL: demanda…"})

    assert res["informe"] == "Informe forense de prueba"
    assert FalsoMotor.llamado[0].startswith("EN LO PRINCIPAL")


def test_critique_documento_exige_texto():
    res = mcp_server.handle_tool_call("critique_documento", {})

    assert "error" in res


def test_generar_documento_entrega_word(tmp_path, monkeypatch):
    import exporters

    monkeypatch.setattr(exporters, "EXPORTS_DIR", str(tmp_path))

    res = mcp_server.handle_tool_call("generar_documento", {
        "tipo": "laboral",
        "tribunal": "Juzgado de Letras del Trabajo de Santiago",
        "demandante": "Ana Pérez",
        "rut": "11.111.111-1",
        "demandado": "Comercial SpA",
        "hechos": "Prestó servicios desde 2019 con despido verbal.",
        "derecho": "Arts. 161 y 162 del Código del Trabajo.",
        "peticiones": "Se acoja la demanda en todas sus partes.",
    })

    ruta = pathlib.Path(res["archivos"]["docxPath"])
    assert ruta.exists() and ruta.suffix == ".docx", res

    from docx import Document

    documento = Document(str(ruta))
    assert len(documento.paragraphs) >= 1
    assert res["entregable"] == "word"


def test_generar_documento_rechaza_un_tipo_desconocido():
    res = mcp_server.handle_tool_call("generar_documento", {"tipo": "habeas_data"})

    assert "error" in res and "demanda_civil" in res["error"]


def test_entrevista_estudio_acumula_el_perfil(tmp_path, monkeypatch):
    import cold_start

    monkeypatch.setattr(cold_start, "PROFILE_FILE", str(tmp_path / "practice_profile.json"))

    guia = mcp_server.handle_tool_call("entrevista_estudio", {"base_dir": str(tmp_path)})
    assert guia["cuestionario"], "sin argumentos tiene que devolver el cuestionario"

    primera = mcp_server.handle_tool_call("entrevista_estudio", {
        "pregunta": "nombre del estudio", "respuesta": "Estudio Pérez", "base_dir": str(tmp_path)})
    segunda = mcp_server.handle_tool_call("entrevista_estudio", {
        "pregunta": "tono procesal", "respuesta": "2", "base_dir": str(tmp_path)})
    tercera = mcp_server.handle_tool_call("entrevista_estudio", {
        "pregunta": "jurisdiccion", "respuesta": "Santiago", "base_dir": str(tmp_path)})

    assert primera["perfil"] and segunda["perfil"] and tercera["perfil"]
    perfil = json.loads((tmp_path / "practice_profile.json").read_text(encoding="utf-8"))
    assert len(perfil) >= 3


def test_skills_listar_trae_las_dieciocho_y_los_agentes():
    res = mcp_server.handle_tool_call("skills_listar", {})

    assert len(res["skills"]) >= 18, f"el repo tiene 18 skills y el listado trajo {len(res['skills'])}"
    assert len(res["agentes"]) >= 19
    assert {s["nombre"] for s in res["skills"]} >= {"chilean-employment-legal", "ponytail"}


def test_skill_ver_devuelve_el_contenido():
    res = mcp_server.handle_tool_call("skill_ver", {"nombre": "chilean-employment-legal"})

    assert "Código del Trabajo" in res["contenido"] or len(res["contenido"]) > 200


def test_skill_ver_avisa_cuando_no_existe():
    res = mcp_server.handle_tool_call("skill_ver", {"nombre": "skill-inexistente"})

    assert "error" in res


def test_generar_documento_informe_transcribe_normas(tmp_path, monkeypatch):
    """El tipo «informe» arma el informe en derecho y entrega Word, con las normas transcritas."""
    import informe_derecho

    monkeypatch.setattr(informe_derecho, "EXPORTS_DIR", str(tmp_path))
    monkeypatch.setattr(
        informe_derecho, "_textos_de_normas",
        lambda referencias: {"citas": [{"formato": "[BCN - Código Civil, Art. 1545]",
                                        "texto": "LOS CONTRATOS DEBEN EJECUTARSE DE BUENA FE " * 4,
                                        "url": "https://www.bcn.cl/x",
                                        "cita_completa": "[BCN - Código Civil, Art. 1545] https://www.bcn.cl/x"}],
                             "faltantes": []})
    monkeypatch.setattr(informe_derecho, "_doctrina_para", lambda termino, limite=3: [])

    res = mcp_server.handle_tool_call("generar_documento", {
        "tipo": "informe",
        "objeto": "¿Es procedente la acción por incumplimiento contractual?",
        "hechos": ("1. Las partes celebraron un contrato de prestación de servicios. "
                   "2. La demandada no pagó las facturas vencidas. "
                   "3. Se irrogaron perjuicios que se avaluarán en ejecución."),
        "normas": ["Código Civil art. 1545"],
        "peticiones": "Se acoja la acción en todas sus partes.",
    })

    assert res["entregable"] == "word", res
    ruta = pathlib.Path(res["archivos"]["docxPath"])
    assert ruta.exists() and ruta.suffix == ".docx"
    assert res["citas"] and res["citas"][0]["formato"] == "[BCN - Código Civil, Art. 1545]"
