"""
Suite de Pruebas Automatizadas para los Módulos de Claude for Legal Chilenizados
Verifica: Examen de Grado, Docket Watcher, Clínica Jurídica, Cold-Start, Privacidad ARCO e INAPI.
"""

import os
import pytest
from examen_grado import ExamenGradoEngine
from docket_watcher import DocketWatcherEngine
from clinica_juridica import ClinicaJuridicaEngine
from cold_start import ColdStartInterviewEngine
from privacidad_inapi import PrivacyARCOEngine, INAPIEngine
from mcp_server import handle_tool_call, TOOLS


def test_examen_grado_socratico():
    engine = ExamenGradoEngine()
    res = engine.interrogar_socratico("civil")
    assert "pregunta_socratica" in res
    assert "articulos_vinculados" in res
    assert len(res["articulos_vinculados"]) > 0
    assert "autor_canonico" in res
    assert "estandar_evaluacion" in res


def test_examen_grado_cedula_y_flashcards():
    engine = ExamenGradoEngine()
    cedula = engine.generar_cedula_completa("obligaciones")
    assert "cedula_titulo" in cedula
    assert len(cedula["interrogantes_principales"]) >= 2
    assert "pauta_de_aprobacion" in cedula

    flashcards = engine.get_flashcards(area="civil", tipo="definicion")
    assert len(flashcards) > 0
    assert any("Posesión" in c["titulo"] or "Contrato" in c["titulo"] for c in flashcards)


def test_docket_watcher_resoluciones():
    # Prueba detección de auto de prueba
    res = DocketWatcherEngine.analizar_resolucion("Recíbase la causa a prueba y fíjense los hechos sustanciales")
    assert res["encontrado"] is True
    assert res["tipo_tramite"] == "AUTO DE PRUEBA / INTERLOCUTORIA DE PRUEBA"
    assert res["severidad"] == "CRÍTICA"
    assert res["alerta_plazo_fatal"] is True

    # Prueba traslado de incidente
    res_traslado = DocketWatcherEngine.analizar_resolucion("Al otrosí, traslado.")
    assert res_traslado["encontrado"] is True
    assert res_traslado["tipo_tramite"] == "CONFERIMIENTO DE TRASLADO (INCIDENTE)"


def test_docket_watcher_radar_y_contratos():
    radar = DocketWatcherEngine.radar_normativo_resumen("laboral", dias_atras=10)
    assert radar["total_alertas_detectadas"] >= 1
    assert any("Karin" in a["norma"] for a in radar["alertas_regulatorias"])

    calc = DocketWatcherEngine.calcular_vencimiento_contrato("Arrendamiento", "2026-12-31", preaviso_dias=60)
    assert "fecha_limite_notificacion" in calc
    assert "dias_para_enviar_aviso" in calc


def test_clinica_juridica_lenguaje_claro():
    res = ClinicaJuridicaEngine.traducir_lenguaje_claro("Autos para fallo y dése traslado al litisconsorcio")
    assert "traduccion_lenguaje_claro" in res
    assert len(res["terminos_tecnicos_identificados"]) >= 2
    assert any(t["termino_legal"] == "autos para fallo" for t in res["terminos_tecnicos_identificados"])


def test_clinica_juridica_intake_y_auditoria():
    intake = ClinicaJuridicaEngine.generar_intake_social("alimentos", {"nombre": "María Rojas", "rut": "18.123.456-7"})
    assert intake["estado_atencion"] == "ADMISIBLE PARA ASISTENCIA JUDICIAL GRATUITA"
    assert any("mediación" in doc.lower() for doc in intake["ficha_atencion"]["documentos_exigidos"])

    borrador_valido = "PROCEDIMIENTO: ORDINARIO\nMATERIA: RESOLUCIÓN\nDEMANDANTE: X\nDEMANDADO: Y\nEN LO PRINCIPAL: DEMANDA\nPRIMER OTROSÍ: PATROCINIO Y PODER LEY 18.120\nPOR TANTO, A US. PIDO..."
    audit = ClinicaJuridicaEngine.auditar_borrador_supervisor(borrador_valido)
    assert audit["aprobado_para_firma"] is True


def test_cold_start_profile(tmp_path):
    datos = {
        "firm_name": "Estudio Jurídico Test",
        "jurisdiction": "Valparaíso",
        "tone": "Formal tradicional",
        "doctrina_preference": "Barros Bourie"
    }
    saved = ColdStartInterviewEngine.save_profile(datos, base_dir=str(tmp_path))
    assert saved["firm_name"] == "Estudio Jurídico Test"

    loaded = ColdStartInterviewEngine.load_profile(base_dir=str(tmp_path))
    assert loaded is not None
    assert loaded["jurisdiction"] == "Valparaíso"


def test_privacidad_arco_e_inapi():
    arco = PrivacyARCOEngine.procesar_solicitud_arco("ACCESO", "Pedro Gómez", "12.345.678-9", "Datos personales")
    assert arco["estatus"] == "ADMITIDA A TRÁMITE"
    assert arco["plazo_legal_dias"] == 15
    assert "Pedro Gómez".upper() in arco["modelo_oficial_respuesta"]

    cd = INAPIEngine.redactar_cease_and_desist("MarcaChile", "Titular S.A.", "Infractor SpA", "Uso no autorizado en web")
    assert cd["plazo_intimacion_dias"] == 5
    assert "MarcaChile" in cd["carta_completa"]

    eval_marca = INAPIEngine.evaluar_factibilidad_marca("VindexLegal", clase_niza="45")
    assert eval_marca["clase_niza"] == "45"
    assert eval_marca["nivel_riesgo_preliminar"] == "BAJO"


def test_mcp_server_new_tools_dispatch():
    # 1. grado_interrogar
    r1 = handle_tool_call("grado_interrogar", {"materia": "civil"})
    assert "pregunta_socratica" in r1

    # 2. grado_generar_cedula
    r2 = handle_tool_call("grado_generar_cedula", {"tema": "recursos"})
    assert "cedula_titulo" in r2

    # 3. grado_obtener_flashcards
    r3 = handle_tool_call("grado_obtener_flashcards", {"area": "procesal"})
    assert "flashcards" in r3

    # 4. vigilante_analizar_resolucion
    r4 = handle_tool_call("vigilante_analizar_resolucion", {"resolucion_texto": "Autos para fallo"})
    assert r4.get("encontrado") is True

    # 5. vigilante_radar_normativo
    r5 = handle_tool_call("vigilante_radar_normativo", {"materia": "laboral"})
    assert "alertas_regulatorias" in r5

    # 6. vigilante_contrato_plazos
    r6 = handle_tool_call("vigilante_contrato_plazos", {"tipo_contrato": "Arriendo", "fecha_vencimiento": "2027-01-01"})
    assert "fecha_limite_notificacion" in r6

    # 7. clinica_lenguaje_claro
    r7 = handle_tool_call("clinica_lenguaje_claro", {"texto_resolucion": "Autos para fallo"})
    assert "traduccion_lenguaje_claro" in r7

    # 8. clinica_intake_social
    r8 = handle_tool_call("clinica_intake_social", {"materia": "alimentos"})
    assert "ficha_atencion" in r8

    # 9. clinica_auditar_borrador
    r9 = handle_tool_call("clinica_auditar_borrador", {"borrador_texto": "POR TANTO, PIDO"})
    assert "puntaje_formal" in r9

    # 10. privacidad_tramitar_arco
    r10 = handle_tool_call("privacidad_tramitar_arco", {
        "tipo_derecho": "RECTIFICACIÓN",
        "solicitante": "Ana Silva",
        "rut": "11.222.333-4",
        "datos_solicitados": "Domicilio"
    })
    assert "modelo_oficial_respuesta" in r10

    # 11. inapi_cease_and_desist
    r11 = handle_tool_call("inapi_cease_and_desist", {
        "marca_afectada": "SuperLegal",
        "titular": "Legal Corp",
        "infractor": "Copia SpA",
        "hechos_infraccion": "Copia de logotipo"
    })
    assert "carta_completa" in r11

    # 12. inapi_evaluar_marca
    r12 = handle_tool_call("inapi_evaluar_marca", {"marca_propuesta": "InnoJuris"})
    assert "nivel_riesgo_preliminar" in r12
