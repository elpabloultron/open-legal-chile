"""Arranque, diagnóstico e instalación con el mapa del corpus.

El mapa diminuto de `tests/conftest.py` (sin red) o el mapa apagado de toda la suite. Nada espera
una descarga real: el cliente apunta a un mapa local o no tiene revisión.
"""

import sys
import threading

import pytest

import diagnostico
import mcp_server
import openlegal
from mapa_corpus import cliente as mod_cliente


def _hilo_mapa():
    return next((h for h in threading.enumerate() if h.name == "openlegal-precalentar-mapa"), None)


@pytest.fixture
def sin_grafo_ni_hub(monkeypatch):
    """El precalentado sin cargar el grafo real ni listar el hub."""
    monkeypatch.setattr(mcp_server.legal_graphify_engine, "cargar_grafo_json", lambda *a, **k: True)
    monkeypatch.setattr(mcp_server, "_precalentar_hf", lambda: None)


def test_el_servidor_usa_el_motor_compartido():
    from legal_graphify import obtener_motor_compartido
    import modulo_ambiental
    assert mcp_server.legal_graphify_engine is obtener_motor_compartido()
    assert modulo_ambiental._engine() is obtener_motor_compartido()


def test_precalentar_sube_la_capa_del_mapa(mapa_activo, sin_grafo_ni_hub, monkeypatch):
    subidas = []
    monkeypatch.setattr(mcp_server.legal_graphify_engine, "subir_capa_mapa", lambda: subidas.append(True) or True)
    mcp_server.precalentar_caches()
    hilo = _hilo_mapa()
    if hilo:
        hilo.join(30)
    assert subidas == [True]


def test_precalentar_sin_mapa_no_hace_nada(sin_grafo_ni_hub, monkeypatch):
    subidas = []
    monkeypatch.setattr(mcp_server.legal_graphify_engine, "subir_capa_mapa", lambda: subidas.append(True))
    mod_cliente.reiniciar_cliente()            # OPENLEGAL_MAPA=off (tests/conftest.py)
    mcp_server.precalentar_caches()
    hilo = _hilo_mapa()
    if hilo:
        hilo.join(30)
    assert subidas == []


def test_precalentar_no_espera_al_mapa(sin_grafo_ni_hub, monkeypatch):
    """La descarga del mapa corre en su propio hilo: el precalentado (y el handshake) no la esperan."""
    soltar = threading.Event()
    monkeypatch.setattr(mcp_server, "_precalentar_mapa", lambda: soltar.wait(30))
    mcp_server.precalentar_caches()
    hilo = _hilo_mapa()
    assert hilo is not None and hilo.is_alive()
    soltar.set()
    hilo.join(30)


def test_precalentar_resiste_un_mapa_roto(sin_grafo_ni_hub, monkeypatch):
    def romper():
        raise RuntimeError("caché ilegible")

    monkeypatch.setattr(mcp_server, "_precalentar_mapa", romper)
    assert mcp_server.precalentar_caches() is None


# ── Doctor ────────────────────────────────────────────────────────────────────────────────────
def test_doctor_mapa_apagado_es_ok():
    mod_cliente.reiniciar_cliente()
    chequeo = diagnostico._chequeo_mapa()
    assert chequeo["estado"] == "ok" and "desactivado" in chequeo["detalle"]
    assert "mapa_corpus" in {c["nombre"] for c in diagnostico.diagnostico_completo()["chequeos"]}


def test_doctor_mapa_sin_publicar_es_ok(monkeypatch):
    monkeypatch.setenv("OPENLEGAL_MAPA", "")
    monkeypatch.setattr(mod_cliente, "leer_puntero", lambda *a, **k: {"revision_mapa": None})
    mod_cliente.reiniciar_cliente()
    try:
        chequeo = diagnostico._chequeo_mapa()
    finally:
        mod_cliente.reiniciar_cliente()
    assert chequeo["estado"] == "ok" and "aún no publicado" in chequeo["detalle"]


def test_doctor_mapa_publicado_sin_descargar_es_aviso(monkeypatch):
    monkeypatch.setenv("OPENLEGAL_MAPA", "")
    monkeypatch.setattr(mod_cliente, "leer_puntero",
                        lambda *a, **k: {"revision_mapa": "1" * 40, "sha256_estado": "2" * 64})
    mod_cliente.reiniciar_cliente()
    try:
        chequeo = diagnostico._chequeo_mapa()
    finally:
        mod_cliente.reiniciar_cliente()
    assert chequeo["estado"] == "aviso" and "suite_instalar" in chequeo["sugerencia"]


def test_doctor_mapa_listo(mapa_activo):
    chequeo = diagnostico._chequeo_mapa()
    assert chequeo["estado"] == "ok" and chequeo["detalle"].startswith("listo: fuente 99999999")


# ── CLI y suite_instalar ──────────────────────────────────────────────────────────────────────
def test_cli_cache_mapa(mapa_activo, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["openlegal", "cache", "mapa"])
    openlegal.main()
    salida = capsys.readouterr().out
    assert "Mapa del corpus: fuente 99999999" in salida and "5 entradas" in salida


def test_cli_cache_mapa_apagado(monkeypatch, capsys):
    mod_cliente.reiniciar_cliente()
    monkeypatch.setattr(sys, "argv", ["openlegal", "cache", "mapa", "--refrescar"])
    openlegal.main()
    assert "Mapa del corpus: desactivado" in capsys.readouterr().out


def test_suite_instalar_deja_el_mapa_listo_con_avances(mapa_activo, tmp_path, monkeypatch):
    avances = []
    monkeypatch.setattr(mcp_server, "enviar_progreso", lambda *a, **k: avances.append(a))
    res = mcp_server.handle_tool_call("suite_instalar", {"carpeta": str(tmp_path)})
    assert res["mapa"]["activo"] is True and res["mapa"]["sha_fuente"] == "9" * 40
    assert res["herramientas"] == 87


def test_suite_instalar_sin_mapa_igual_instala(tmp_path):
    mod_cliente.reiniciar_cliente()
    res = mcp_server.handle_tool_call("suite_instalar", {"carpeta": str(tmp_path)})
    assert res["mapa"]["activo"] is False and res["doctor"]["estado"] in ("ok", "degradado", "error")


def test_cli_cache_mapa_muestra_el_error_de_una_descarga_fallida(monkeypatch, capsys):
    breve = {"activo": False, "aviso": "Se descarga en segundo plano; para forzarlo, usa suite_instalar.",
             "error": "HTTP 503 en estado.json", "descargando": False}
    monkeypatch.setattr(openlegal, "_asegurar_mapa", lambda espera: breve)
    monkeypatch.setattr(sys, "argv", ["openlegal", "cache", "mapa", "--refrescar"])
    openlegal.main()
    salida = capsys.readouterr().out
    assert "Mapa del corpus: HTTP 503 en estado.json" in salida
    assert "segundo plano" not in salida                     # el proceso termina: nada sigue bajando
