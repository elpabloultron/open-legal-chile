"""
Pruebas unitarias para el módulo scripts.ci_watchdog (Watchdog y Auto-Reparador de CI de GitHub).
"""

from scripts import ci_watchdog


def test_clasificar_fallo_skills_lock():
    log = """
    tests/test_legal_design.py:257: AssertionError
    E       AssertionError: chilean-corporate-legal: lock=fb562fd96c97… archivo=e0b8392c827b…
    E       assert not ['chilean-corporate-legal: lock=fb562fd96c97… archivo=e0b8392c827b…']
    """
    analisis = ci_watchdog.clasificar_fallo(log)
    assert analisis["tipo"] == "SKILLS_LOCK"
    assert analisis["skill"] == "chilean-corporate-legal"
    assert analisis["reparable_automaticamente"] is True


def test_clasificar_fallo_bandit():
    log = """
    >> Issue: [B108:hardcoded_tmp_directory] Probable insecure usage of temp file/directory.
       Location: ./scripts/generar_informe_pdf.py:510:15
    """
    analisis = ci_watchdog.clasificar_fallo(log)
    assert analisis["tipo"] == "BANDIT_SAST"
    assert analisis["archivo"] == "./scripts/generar_informe_pdf.py"
    assert analisis["linea"] == "510"


def test_clasificar_fallo_ruff():
    log = """
    Found 2 errors. 1 fixable with `--fix`.
    """
    analisis = ci_watchdog.clasificar_fallo(log)
    assert analisis["tipo"] == "RUFF_LINT"
    assert analisis["reparable_automaticamente"] is True


def test_clasificar_fallo_network_timeout():
    log = """
    requests.exceptions.ConnectionError: HTTPSConnectionPool(host='api.bcn.cl', port=443): Max retries exceeded
    503 Service Unavailable
    """
    analisis = ci_watchdog.clasificar_fallo(log)
    assert analisis["tipo"] == "NETWORK_TIMEOUT"
    assert analisis["reparable_automaticamente"] is True


def test_clasificar_fallo_pytest():
    log = """
    FAILED tests/test_sii_robustez.py::test_sii_leer_documento_error
    """
    analisis = ci_watchdog.clasificar_fallo(log)
    assert analisis["tipo"] == "PYTEST_FAIL"
    assert analisis["test_file"] == "tests/test_sii_robustez.py"
    assert analisis["test_name"] == "test_sii_leer_documento_error"


def test_reparar_skills_lock_no_rompe(tmp_path, monkeypatch):
    monkeypatch.setattr(ci_watchdog, "ROOT_DIR", tmp_path)
    # Sin skills-lock.json devuelve False limpiamente
    assert ci_watchdog.reparar_skills_lock() is False
