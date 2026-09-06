"""
Pruebas unitarias para los sistemas de actualización automática, estadísticas de adopción
y nuevas herramientas MCP de Open Legal Chile Suite.
"""

import pytest
from update_checker import (
    check_for_updates,
    format_update_banner,
    _parse_version_tuple,
    run_auto_update
)
from stats_tracker import (
    get_pypi_download_stats,
    get_github_community_stats,
    get_suite_adoption_metrics,
    send_anonymous_telemetry_ping
)
from mcp_server import handle_tool_call, TOOLS


def test_parse_version_tuple():
    assert _parse_version_tuple("1.3.0") == (1, 3, 0)
    assert _parse_version_tuple("v1.4.2") == (1, 4, 2)
    assert _parse_version_tuple("invalid") == (0, 0, 0)


def test_check_for_updates_structure():
    info = check_for_updates(force=False)
    assert "version_actual" in info
    assert "version_disponible" in info
    assert "hay_actualizacion" in info
    assert "comando_pip" in info
    assert "instruccion_ia" in info


def test_format_update_banner():
    # Caso sin actualización
    assert format_update_banner({"hay_actualizacion": False}) is None

    # Caso con actualización
    banner = format_update_banner({
        "hay_actualizacion": True,
        "version_actual": "1.3.0",
        "version_disponible": "1.4.0"
    })
    assert banner is not None
    assert "NUEVA VERSIÓN DISPONIBLE" in banner
    assert "pip install --upgrade openlegal-chile" in banner
    assert "openlegal update" in banner


def test_pypi_stats_structure():
    stats = get_pypi_download_stats()
    assert "descargas_ultimo_dia" in stats
    assert "descargas_ultima_semana" in stats
    assert "descargas_ultimo_mes" in stats
    assert isinstance(stats["descargas_ultimo_dia"], int)


def test_github_stats_structure():
    stats = get_github_community_stats()
    assert "estrellas" in stats
    assert "forks" in stats
    assert "repositorio" in stats


def test_suite_adoption_metrics():
    metrics = get_suite_adoption_metrics()
    assert metrics["suite"] == "Open Legal Chile"
    assert "metricas_pypi" in metrics
    assert "metricas_github" in metrics
    assert metrics["capacidades_locales"]["herramientas_mcp_oficiales"] == 54
    assert metrics["capacidades_locales"]["instituciones_doctrinales_indexadas"] >= 100


def test_anonymous_telemetry_ping():
    # Debe retornar booleano sin levantar excepción
    res = send_anonymous_telemetry_ping(client="test", action="unit_test")
    assert isinstance(res, bool)


def test_mcp_suite_stats_tool():
    res = handle_tool_call("suite_telemetria_stats", {})
    assert "metricas_pypi" in res
    assert "capacidades_locales" in res


def test_mcp_suite_verificar_actualizacion_tool():
    res = handle_tool_call("suite_verificar_actualizacion", {"forzar": False})
    assert "version_actual" in res
    assert "hay_actualizacion" in res


def test_mcp_suite_auto_update_dry():
    # Verificar que el despachador de la herramienta responde la estructura esperada
    res = handle_tool_call("suite_auto_update", {})
    assert "metodo" in res
    assert "mensaje" in res
