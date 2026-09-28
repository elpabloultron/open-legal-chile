"""Al analizar un caso, sus leyes se adelantan en segundo plano (best-effort, sin bloquear).

Medido el 2026-09-28: la primera consulta a cada ley pagaba red; adelantar la descarga deja la
caché caliente para cuando el abogado pregunte. Nunca lanza ni bloquea: es un adelanto.
"""

import servidor.casos as casos


def _hilo_sincrono(monkeypatch):
    """Thread de mentira que ejecuta el trabajo ya mismo: la prueba no depende de tiempos."""

    class _Hilo:
        def __init__(self, target=None, name=None, daemon=None):
            self._target = target

        def start(self):
            self._target()

    monkeypatch.setattr(casos.threading, "Thread", _Hilo)


def test_precalentado_descarga_las_leyes_del_caso(monkeypatch):
    llamadas = []

    class _BCNFalso:
        def __init__(self, *a, **k):
            pass

        def get_ley(self, numero):
            llamadas.append(numero)
            return {"numero": numero}

    monkeypatch.setattr("bcn_connector.BCNClient", _BCNFalso)
    _hilo_sincrono(monkeypatch)

    casos._precalentar_normas_caso(
        {"resumen": "Ver Ley 21.643 art. 2 y Ley 19.300 art. 25 quinquies."})

    assert llamadas == [21643, 19300], llamadas


def test_precalentado_ignora_leyes_imposibles(monkeypatch):
    llamadas = []

    class _BCNFalso:
        def __init__(self, *a, **k):
            pass

        def get_ley(self, numero):
            llamadas.append(numero)
            return {}

    monkeypatch.setattr("bcn_connector.BCNClient", _BCNFalso)
    _hilo_sincrono(monkeypatch)

    casos._precalentar_normas_caso({"resumen": "Ley 242 art. 1 y Ley 21643 art. 2"})

    assert llamadas == [21643], llamadas  # 242 queda fuera del rango 9000-30000


def test_despachar_caso_analizar_precalienta(monkeypatch):
    import case_intake as ci

    avisos = []
    monkeypatch.setattr(casos, "_precalentar_normas_caso", lambda resultado: avisos.append(resultado))
    monkeypatch.setattr(ci, "caso_analizar", lambda *a, **k: {"resumen": "ok"})

    resultado = casos.despachar("caso_analizar", {"entrada": "x"})

    assert resultado == {"resumen": "ok"}
    assert len(avisos) == 1, "el caso analizado dispara el adelanto de sus leyes"


def test_despachar_con_error_no_precalienta(monkeypatch):
    import case_intake as ci

    avisos = []
    monkeypatch.setattr(casos, "_precalentar_normas_caso", lambda resultado: avisos.append(resultado))
    monkeypatch.setattr(ci, "caso_analizar", lambda *a, **k: {"error": "nada que analizar"})

    casos.despachar("caso_analizar", {"entrada": "x"})

    assert avisos == [], "sin análisis no hay nada que adelantar"
