"""Las conexiones HTTP se reutilizan por host: una sola negociación TLS por ráfaga.

Medido el 2026-09-28: cada consulta a la BCN abría su propia conexión (TLS nuevo cada vez);
en ráfagas (varios artículos de una ley, varias leyes) eso es cientos de ms por salto. El
canal persistente por host los reutiliza y reintenta una sola vez si la conexión murió.
"""

import pytest

import config


class _RespuestaFalsa:
    status = 200
    reason = "OK"

    def __init__(self, cuerpo: bytes = b'{"ok": true}'):
        self._cuerpo = cuerpo

    def read(self) -> bytes:
        return self._cuerpo


class _ConexionFalsa:
    creadas = 0

    def __init__(self, host, timeout=None):
        type(self).creadas += 1
        self.host = host
        self.peticiones = []
        self.explotar_una_vez = False
        self.cerrada = False
        self.respuesta = _RespuestaFalsa()

    def request(self, metodo, ruta, body=None, headers=None):
        if self.explotar_una_vez:
            self.explotar_una_vez = False
            raise ConnectionResetError("conexión caída")
        self.peticiones.append((metodo, ruta))

    def getresponse(self):
        return self.respuesta

    def close(self):
        self.cerrada = True


_VARIABLES_PROXY = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy",
                    "NO_PROXY", "no_proxy")


@pytest.fixture(autouse=True)
def _limpiar(monkeypatch):
    for variable in _VARIABLES_PROXY:  # la máquina que corre las pruebas puede estar tras un proxy
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setattr("http.client.HTTPSConnection", _ConexionFalsa)
    _ConexionFalsa.creadas = 0
    config._CANALES.clear()
    yield
    config._CANALES.clear()


def test_dos_peticiones_reutilizan_la_conexion():
    config.pedir_http("https://ejemplo.cl/a")
    config.pedir_http("https://ejemplo.cl/b")
    assert _ConexionFalsa.creadas == 1, "mismo host: una sola conexión"
    assert config.pedir_http("https://ejemplo.cl/c") == b'{"ok": true}'


def test_conexion_caida_se_reintenta_una_vez():
    config.pedir_http("https://ejemplo.cl/a")
    canal = config._CANALES["https://ejemplo.cl"][0][0]
    canal.explotar_una_vez = True
    assert config.pedir_http("https://ejemplo.cl/b") == b'{"ok": true}'
    assert _ConexionFalsa.creadas == 2, "la conexión muerta se descarta y se reintenta con una nueva"


def test_esquema_prohibido():
    with pytest.raises(ValueError):
        config.pedir_http("file:///etc/passwd")


def test_bcn_fetch_xml_usa_el_canal(monkeypatch, tmp_path):
    import bcn_connector

    llamadas = []
    monkeypatch.setattr(bcn_connector, "pedir_http",
                        lambda url, timeout=30.0, **k: llamadas.append(url) or b"<norma/>")

    cliente = bcn_connector.BCNClient(cache_dir=str(tmp_path))
    assert cliente._fetch_xml({"opt": 7, "idLey": 21643}) == "<norma/>"
    assert llamadas and "obtxml" in llamadas[0]


def test_snifa_usa_el_canal(monkeypatch, tmp_path):
    import ambiental_connector

    llamadas = []
    cuerpo_falso = b'{"recordsTotal": 0, "data": []}'

    def _pedir(url, metodo="GET", headers=None, cuerpo=None, timeout=25):
        llamadas.append(url)
        return cuerpo_falso

    monkeypatch.setattr(ambiental_connector, "pedir_http", _pedir)

    cliente = ambiental_connector.SMAClient(cache_dir=str(tmp_path))
    datos = cliente.search_sancionatorios(nombre="prueba")
    assert datos["total"] == 0
    assert llamadas and "ObtenerResultadosGrid" in llamadas[0]


class _ConexionProxyFalsa(_ConexionFalsa):
    def __init__(self, host, port=None, timeout=None):
        super().__init__(host, timeout=timeout)
        self.port = port
        self.tunel = None
        self.cabeceras_tunel = None

    def set_tunnel(self, host, port=None, headers=None):
        self.tunel = host
        self.cabeceras_tunel = headers


def test_https_respeta_el_proxy_con_tunel(monkeypatch):
    """Tras un proxy (estudio, CI, nube) la conexión va por CONNECT al proxy, no directo al host."""
    monkeypatch.setattr("http.client.HTTPSConnection", _ConexionProxyFalsa)
    monkeypatch.setenv("HTTPS_PROXY", "http://usuario:clave@proxy.local:3128")
    assert config.pedir_http("https://www.leychile.cl/Consulta/obtxml?opt=7") == b'{"ok": true}'
    canal = config._CANALES["https://www.leychile.cl"][0][0]
    assert (canal.host, canal.port, canal.tunel) == ("proxy.local", 3128, "www.leychile.cl")
    assert canal.cabeceras_tunel["Proxy-Authorization"].startswith("Basic ")
    assert canal.peticiones == [("GET", "/Consulta/obtxml?opt=7")]


def test_no_proxy_va_directo(monkeypatch):
    monkeypatch.setattr("http.client.HTTPSConnection", _ConexionProxyFalsa)
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.local:3128")
    monkeypatch.setenv("NO_PROXY", "ejemplo.cl")
    config.pedir_http("https://ejemplo.cl/a")
    canal = config._CANALES["https://ejemplo.cl"][0][0]
    assert canal.host == "ejemplo.cl" and canal.tunel is None


def test_http_plano_por_proxy_pide_url_absoluta(monkeypatch):
    monkeypatch.setattr("http.client.HTTPConnection", _ConexionProxyFalsa)
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.local:8080")
    config.pedir_http("http://snifa.sma.gob.cl/x?y=1")
    canal = config._CANALES["http://snifa.sma.gob.cl"][0][0]
    assert (canal.host, canal.port) == ("proxy.local", 8080)
    assert canal.peticiones == [("GET", "http://snifa.sma.gob.cl/x?y=1")]
