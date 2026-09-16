"""
Open Legal Chile — Pruebas Unitarias para el Motor de Agentes Jurídicos (Agents Runtime)
Verifica la carga del registro, pipelines deterministas soberanos (100 % offline),
orquestación de herramientas MCP, auditoría de 5 dimensiones y exportación de subagentes.
"""

import os
import pytest
from agents_runtime import agent_runtime, BaseLegalAgent, AgentExecutionResult, AgentStep
from mcp_server import handle_tool_call, TOOLS


def test_agent_registry_load():
    """Verifica la carga dinámica de los 18 perfiles de agentes desde agents/*.json."""
    agentes = agent_runtime.list_agents()
    assert len(agentes) == 18
    nombres = [a["name"] for a in agentes]
    assert "agente-litigios" in nombres
    assert "agente-inmobiliario" in nombres
    assert "agente-dogmatico" in nombres
    assert "agente-probidad" in nombres
    assert "agente-laboral" in nombres
    assert "agente-forense" in nombres
    assert "agente-vigilante" in nombres
    assert "agente-clinica" in nombres
    assert "agente-regulatorio" in nombres
    assert "agente-ingestor" in nombres


def test_agent_lookup_alias():
    """Verifica la resolución de nombres por alias corto (sin prefijo agente-)."""
    ag_lit = agent_runtime.get_agent("litigios")
    assert ag_lit is not None
    assert ag_lit.name == "agente-litigios"
    assert "recurso_proteccion_generar" in ag_lit.tools

    ag_inm = agent_runtime.get_agent("inmobiliario")
    assert ag_inm is not None
    assert ag_inm.name == "agente-inmobiliario"
    assert "cbr_estudio_titulos" in ag_inm.tools

    ag_dog = agent_runtime.get_agent("dogmatico")
    assert ag_dog is not None
    assert ag_dog.name == "agente-dogmatico"
    assert "graphify_explicar_institucion" in ag_dog.tools


def test_deterministic_pipeline_litigios():
    """Verifica la orquestación determinista del Agente Litigante OJV."""
    res = agent_runtime.run_agent(
        "litigios",
        "Clausura ilegal de acceso a rampa de desembarque de pescadores artesanales",
        context={
            "tribunal": "Ilustrísima Corte de Apelaciones de Valparaíso",
            "fecha_acto": "2026-09-08",
            "compilar_pdf": False
        },
        mode="deterministic"
    )

    assert isinstance(res, AgentExecutionResult)
    assert res.status == "success"
    assert res.mode == "deterministic"
    assert len(res.steps) == 3
    assert "recurso_proteccion_generar" in res.tools_used
    assert "Ilustrísima Corte de Apelaciones de Valparaíso" in res.output
    assert "TEMPESTIVO" in res.output
    assert res.critique is not None
    assert res.critique.get("puntuacion_total", 0) >= 40


def test_deterministic_pipeline_inmobiliario():
    """Verifica la auditoría decenal de títulos inmobiliarios CBR."""
    res = agent_runtime.run_agent(
        "inmobiliario",
        "Auditoría de dominio propiedad Las Condes",
        context={
            "fojas": "4567",
            "numero": "2345",
            "ano": 2022,
            "cbr": "Santiago"
        },
        mode="deterministic"
    )

    assert res.status == "success"
    assert len(res.steps) == 3
    assert "cbr_estudio_titulos" in res.tools_used
    assert "cbr_checklist_documentos" in res.tools_used
    assert "cpc_validar_mandato" in res.tools_used
    assert "ESTUDIO DE TÍTULOS" in res.output
    assert "Cadena Dominial Decenal" in res.output


def test_deterministic_pipeline_probidad():
    """Verifica la fiscalización de probidad y compras públicas CGR."""
    res = agent_runtime.run_agent(
        "probidad",
        "confianza legitima contrata municipalidad",
        mode="deterministic"
    )

    assert res.status == "success"
    assert len(res.steps) == 2
    assert "cgr_search_jurisprudencia" in res.tools_used
    assert "cgr_search_auditorias" in res.tools_used
    assert "FISCALIZACIÓN Y COMPLIANCE PÚBLICO" in res.output
    assert "Contraloría General de la República" in res.output


def test_deterministic_pipeline_laboral():
    """Verifica el análisis de causales de despido y doctrina DT."""
    res = agent_runtime.run_agent(
        "laboral",
        "despido necesidades de la empresa",
        context={"articulo": "161"},
        mode="deterministic"
    )

    assert res.status == "success"
    assert len(res.steps) == 3
    assert "dt_search_doctrina" in res.tools_used
    assert "bcn_get_codigo" in res.tools_used
    assert "pjud_search_jurisprudencia" in res.tools_used
    assert "RELACIONES LABORALES" in res.output
    assert "Dirección del Trabajo" in res.output


def test_deterministic_pipeline_dogmatico():
    """Verifica el análisis ontológico 360° en LegalGraphify."""
    res = agent_runtime.run_agent(
        "dogmatico",
        "simulacion",
        mode="deterministic"
    )

    assert res.status == "success"
    assert len(res.steps) == 3
    assert "graphify_explicar_institucion" in res.tools_used
    assert "doctrina_search" in res.tools_used
    assert "graphify_god_nodes" in res.tools_used
    assert "TEORÍA GENERAL DEL DERECHO" in res.output


def test_deterministic_pipeline_forense():
    """Verifica la auditoría en 5 dimensiones del Red Team judicial."""
    escrito_prueba = """
    EN LO PRINCIPAL: DEMANDA ORDINARIA DE INDEMNIZACIÓN DE PERJUICIOS.
    PRIMER OTROSÍ: ACOMPAÑA DOCUMENTOS.
    S.J.L. en lo Civil de Santiago
    Juan Pérez, por sí, deduce demanda en contra de Inversiones Sur SpA...
    El demandado incurrió en culpa grave causando daño emergente y moral.
    POR TANTO, conforme al Art. 2314 y Art. 2329 del Código Civil,
    RUEGO A US. acoger la demanda con costas.
    """
    res = agent_runtime.run_agent(
        "forense",
        "Auditar borrador civil",
        context={"documento_texto": escrito_prueba},
        mode="deterministic"
    )

    assert res.status == "success"
    assert "AUDITORÍA FORENSE Y CONTRA-ARGUMENTACIÓN" in res.output
    assert res.critique is not None


def test_deterministic_pipeline_vigilante():
    """Verifica la interpretación de proveídos OJV y plazos fatales."""
    res = agent_runtime.run_agent(
        "vigilante",
        "Interpretar resolución",
        context={"proveido": "Como se pide, con citación. Vengan los autos para resolver."},
        mode="deterministic"
    )

    assert res.status == "success"
    assert "VIGILANTE PROCESAL" in res.output
    assert "pjud_interpretar_proveido" in res.tools_used


def test_deterministic_pipeline_clinica():
    """Verifica la traducción a Lenguaje Claro y orientación CAJ."""
    res = agent_runtime.run_agent(
        "clinica",
        "Traducir fallo",
        context={"texto": "Vistos y considerando: Que atendido el mérito de autos y lo dispuesto en el Art. 1437 del Código Civil, no ha lugar a la reposición por extemporánea."},
        mode="deterministic"
    )

    assert res.status == "success"
    assert "CLÍNICA JURÍDICA" in res.output
    assert "clinica_lenguaje_claro" in res.tools_used


def test_mcp_agent_tools():
    """Verifica las 3 nuevas herramientas MCP expuestas en mcp_server."""
    # 1. agent_list
    res_list = handle_tool_call("agent_list", {})
    assert isinstance(res_list, list)
    assert len(res_list) == 18

    # 2. agent_run
    res_run = handle_tool_call("agent_run", {
        "agent_name": "inmobiliario",
        "task": "Revisar fojas 100 número 50 CBR Santiago",
        "mode": "deterministic"
    })
    assert isinstance(res_run, dict)
    assert res_run["status"] == "success"
    assert "output" in res_run
    assert len(res_run["steps"]) >= 1

    # 3. agent_export_subagents
    res_exp = handle_tool_call("agent_export_subagents", {})
    assert isinstance(res_exp, dict)
    assert len(res_exp) >= 18


def test_deterministic_pipeline_ingestor(tmp_path):
    """Verifica la ingesta, normalización RAE y asimilación al grafo del Agente Ingestor."""
    sample_doc = (
        "Tratado de la Responsabilidad Extracontractual.\n"
        "Por don Enrique Barros Bourie.\n\n"
        "## 🏛️ Culpa Infraccional y Presunción de Culpa\n"
        "**Definición Canónica:**\n"
        "La culpa infraccional se configura por la transgresión de un deber de cuidado estatutario o legal positivo.\n\n"
        "**Operativa Procesal Forense:**\n"
        "* **Vía Procesal:** Juicio Sumario u Ordinario de Indemnización de Perjuicios.\n"
        "* **Carga Probatoria:** La víctima únicamente debe acreditar la infracción normativa.\n\n"
        "**Concordancias Legales:** `[BCN - Código Civil, Art. 2314]` `[BCN - Código Civil, Art. 2329]`\n"
        "**Criterio Jurisprudencial Rector:** `[CS - Rol N° 78.432-2023]`\n"
    )
    src_file = tmp_path / "test_culpa.txt"
    src_file.write_text(sample_doc, encoding="utf-8")
    dest_md = tmp_path / "test_culpa_canonico.md"

    res = agent_runtime.run_agent(
        "ingestor",
        str(src_file),
        context={
            "area": "civil",
            "tratadista": "Enrique Barros Bourie",
            "obra": "Tratado de la Responsabilidad Extracontractual",
            "target_path": str(dest_md),
            "actualizar_grafo": False
        },
        mode="deterministic"
    )

    assert isinstance(res, AgentExecutionResult)
    assert res.status == "success"
    assert res.mode == "deterministic"
    assert "doctrina_ingestar_documento" in res.tools_used
    assert "CERTIFICADO DE ASIMILACIÓN DOCTRINAL" in res.output
    assert dest_md.exists()
    content = dest_md.read_text(encoding="utf-8")
    assert "# TRATADO DE LA RESPONSABILIDAD EXTRACONTRACTUAL" in content
    assert "Culpa Infraccional" in content


def test_unknown_agent_error():
    """Verifica el manejo de error elegante cuando el agente no existe."""
    res = agent_runtime.run_agent("agente-inexistente", "tarea cualquiera")
    assert res.status == "error"
    assert "no encontrado" in res.output.lower()


def test_cli_summary_formatting():
    """Verifica la salida visual para la terminal CLI."""
    res = agent_runtime.run_agent("litigios", "Tarea de prueba")
    cli_txt = res.format_cli_summary()
    assert "AGENTE: ABOGADO LITIGANTE" in cli_txt
    assert "MODO: DETERMINISTIC" in cli_txt
    assert "TRAZA DE RAZONAMIENTO Y EJECUCIÓN" in cli_txt
    assert "DICTAMEN / PRODUCTO FORENSE FINAL" in cli_txt
