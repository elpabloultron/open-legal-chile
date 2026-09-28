"""El registro de tiempos por fase: p50/p95, sin disco, sin red, sin datos de usuario.

El percentil es «rango más cercano» (ceil): con 5 muestras [0,1 0,2 0,3 0,4 1,0] el p95 es la
muestra mayor (1,0 s), que es lo que un p95 tiene que significar para vigilar latencias.
"""

import config


def test_registrar_y_resumir(monkeypatch):
    monkeypatch.setattr(config, "_TIEMPOS", {})
    for segundos in (0.1, 0.2, 0.3, 0.4, 1.0):
        config.registrar_tiempo("bcn.red", segundos)
    resumen = config.tiempos_resumen()
    assert resumen["bcn.red"]["n"] == 5
    assert resumen["bcn.red"]["p50_ms"] == 300.0
    assert resumen["bcn.red"]["p95_ms"] == 1000.0


def test_registro_vacio_no_falla():
    assert isinstance(config.tiempos_resumen(), dict)


def test_una_medicion_sola(monkeypatch):
    monkeypatch.setattr(config, "_TIEMPOS", {})
    config.registrar_tiempo("snifa.red", 0.25)
    resumen = config.tiempos_resumen()
    assert resumen["snifa.red"] == {"n": 1, "p50_ms": 250.0, "p95_ms": 250.0}


def test_medicion_rota_no_tumba(monkeypatch):
    monkeypatch.setattr(config, "_TIEMPOS", {})
    config.registrar_tiempo("x", "no es un número")  # noqa: BLE001 — se traga y sigue
    assert config.tiempos_resumen() == {}


def test_doctor_incluye_rendimiento(monkeypatch):
    import servidor.suite as suite

    monkeypatch.setattr("diagnostico.diagnostico_completo",
                        lambda: {"estado": "ok", "chequeos": []})
    monkeypatch.setattr(config, "_TIEMPOS", {})
    config.registrar_tiempo("bcn.red", 0.5)

    resultado = suite.despachar("suite_doctor", {})

    assert resultado["rendimiento"]["bcn.red"]["p50_ms"] == 500.0
