"""Nada que la CLI pueda hacer debe quedar invisible para un harness.

Este test es el candado: si mañana se agrega un comando a la CLI y no se expone como herramienta
MCP, falla acá. La razón es la regla del producto: el trabajo ocurre dentro del harness, sin abrir
una terminal.
"""

import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parent.parent

# Solo interfaz de consola, o ya cubierto por una herramienta MCP equivalente.
ALLOWLIST = {"menu", "chat", "query", "mcp", "agent", "agents", "audit"}

COMANDO_A_HERRAMIENTA = {
    "check": "suite_doctor",
    "doctor": "suite_doctor",
    "search": "busqueda_universal",
    "skills": "skills_listar",
    "critique": "critique_documento",
    "generate": "generar_documento",
    "interview": "entrevista_estudio",
    "integrar": "integraciones_harness",  # módulo, no herramienta: configura harnesses, no consulta
    # El resto ya estaba cubierto por una herramienta con otro nombre (mapa explícito, no adivinado).
    "arco": "privacidad_tramitar_arco",
    "clinica": "clinica_lenguaje_claro",
    "doctrina": "doctrina_search",
    "export": "export_brief_ojv",
    "grado": "grado_interrogar",
    "graph": "graphify_consulta_subgrafo",
    "guias": "academia_judicial_buscar_guias",
    "inapi": "inapi_evaluar_marca",
    "stats": "suite_telemetria_stats",
    "update": "suite_auto_update",
    "vigilar": "vigilante_analizar_resolucion",
}


def _comandos_cli() -> set:
    fuente = (RAIZ / "openlegal.py").read_text(encoding="utf-8")
    coincidencia = re.search(r'add_argument\("comando".*?choices=\[(.*?)\]', fuente, re.S)
    if coincidencia is None:
        raise AssertionError("no se encontró el add_argument('comando') con choices= en openlegal.py")
    return set(re.findall(r'"([a-z-]+)"', coincidencia.group(1)))


def _herramientas_mcp() -> set:
    fuente = (RAIZ / "mcp_server.py").read_text(encoding="utf-8")
    return set(re.findall(r'"name": "([a-z_0-9]+)"', fuente))


def test_cada_comando_tiene_herramienta_o_esta_en_la_allowlist():
    faltan = []
    for comando in sorted(_comandos_cli() - ALLOWLIST):
        esperada = COMANDO_A_HERRAMIENTA.get(comando, comando)
        if esperada == "integraciones_harness":
            assert (RAIZ / "integraciones_harness.py").exists()
            continue
        if esperada not in _herramientas_mcp():
            faltan.append(f"{comando} → {esperada}")

    assert not faltan, "comandos sin herramienta MCP: " + ", ".join(faltan)


def test_las_capacidades_de_paridad_estan_expuestas():
    herramientas = _herramientas_mcp()

    assert {"suite_doctor", "busqueda_universal", "skills_listar", "skill_ver",
            "critique_documento", "generar_documento", "entrevista_estudio"} <= herramientas


def test_el_protocolo_viaja_como_prompts_y_recursos_mcp():
    """Además de las herramientas, el harness tiene que poder leer las reglas del producto."""
    fuente = (RAIZ / "mcp_server.py").read_text(encoding="utf-8")

    assert '"prompts"' in fuente, "el servidor debe declarar la capacidad de prompts"
    assert '"resources"' in fuente, "el servidor debe declarar la capacidad de resources"
    assert "prompts/list" in fuente and "resources/list" in fuente
