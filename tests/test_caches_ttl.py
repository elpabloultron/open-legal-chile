"""Las copias locales de BCN y SNIFA caducan: antes vivían para siempre, sin refrescarse nunca.

Medido el 2026-09-28: la caché de leyes se reusaba sin fecha límite (también cuando una ley ya
pudo haber cambiado); ahora se revalida —30 días BCN, 7 días SNIFA— con degradación honesta si
la red falla: se entrega la copia vencida marcada, en vez de un error.
"""

import json
import os
import time

import pytest

import ambiental_connector
import bcn_connector


def _envejecer(ruta, dias=40):
    """Las cosas viejas se hacen con mtime, como la vida real."""
    viejo = time.time() - dias * 24 * 60 * 60
    os.utime(ruta, (viejo, viejo))


# ─────────────────────────── BCN (30 días) ───────────────────────────


def test_ley_fresca_no_va_a_la_red(monkeypatch, tmp_path):
    cliente = bcn_connector.BCNClient(cache_dir=str(tmp_path))
    cache = tmp_path / "ley_p2_99999.json"
    cache.write_text(json.dumps({"titulo": "de prueba", "articulos": {"1": "uno"}}),
                     encoding="utf-8")

    def _sin_red(*_a, **_k):
        raise AssertionError("no debía consultar la red con la copia fresca")

    monkeypatch.setattr(cliente, "_fetch_xml", _sin_red)

    datos = cliente.get_ley(99999)
    assert datos["articulos"]["1"] == "uno"


def test_ley_vencida_se_refresca(monkeypatch, tmp_path):
    cliente = bcn_connector.BCNClient(cache_dir=str(tmp_path))
    cache = tmp_path / "ley_p2_99999.json"
    cache.write_text(json.dumps({"titulo": "vieja", "articulos": {"1": "viejo"}}),
                     encoding="utf-8")
    _envejecer(cache, dias=40)

    monkeypatch.setattr(cliente, "_fetch_xml", lambda params: "<norma/>")
    monkeypatch.setattr(cliente, "_parse_norma_xml",
                        lambda xml: {"titulo": "nueva", "articulos": {"1": "nuevo"},
                                     "fechaVersion": "2026-09-28"})

    datos = cliente.get_ley(99999)
    assert datos["articulos"]["1"] == "nuevo"
    guardado = json.loads(cache.read_text(encoding="utf-8"))
    assert guardado["articulos"]["1"] == "nuevo", "la copia vencida se reemplaza"


def test_ley_vencida_sin_red_entrega_la_copia_marcada(monkeypatch, tmp_path):
    cliente = bcn_connector.BCNClient(cache_dir=str(tmp_path))
    cache = tmp_path / "ley_p2_99999.json"
    cache.write_text(json.dumps({"titulo": "vieja", "articulos": {"1": "viejo"}}),
                     encoding="utf-8")
    _envejecer(cache, dias=40)

    def _sin_red(*_a, **_k):
        raise RuntimeError("red caída")

    monkeypatch.setattr(cliente, "_fetch_xml", _sin_red)

    datos = cliente.get_ley(99999)
    assert datos["articulos"]["1"] == "viejo"
    assert datos.get("copia_local_vencida") is True, (
        "usar una copia vencida tiene que verse en la respuesta"
    )


# ─────────────────────────── SNIFA / SMA (7 días) ───────────────────────────


def _respuesta_snifa(expediente="D-1-2026"):
    fila = ["", expediente, "unidad fiscalizable", "Titular SpA", "Planta de compostaje",
            "Los Lagos", "en curso", '<a href="/Sancionatorio/Ficha/99">Ver ficha</a>']
    return json.dumps({"recordsTotal": 1, "data": [fila]}).encode("utf-8")


def test_snifa_fresca_no_repite_la_red(monkeypatch, tmp_path):
    llamadas = []

    def _pedir(url, metodo="GET", headers=None, cuerpo=None, timeout=25):
        llamadas.append(1)
        return _respuesta_snifa()

    monkeypatch.setattr(ambiental_connector, "pedir_http", _pedir)
    cliente = ambiental_connector.SMAClient(cache_dir=str(tmp_path))

    primera = cliente.search_sancionatorios(nombre="prueba")
    segunda = cliente.search_sancionatorios(nombre="prueba")

    assert len(llamadas) == 1, "la copia fresca evita la segunda consulta"
    assert primera["resultados"][0]["expediente"] == "D-1-2026"
    assert segunda["resultados"][0]["expediente"] == "D-1-2026"


def test_snifa_vencida_se_refresca(monkeypatch, tmp_path):
    llamadas = []

    def _pedir(url, metodo="GET", headers=None, cuerpo=None, timeout=25):
        llamadas.append(1)
        return _respuesta_snifa()

    monkeypatch.setattr(ambiental_connector, "pedir_http", _pedir)
    cliente = ambiental_connector.SMAClient(cache_dir=str(tmp_path))

    cliente.search_sancionatorios(nombre="prueba")
    cache = next(tmp_path.glob("sanc_*.json"))
    _envejecer(cache, dias=10)

    cliente.search_sancionatorios(nombre="prueba")
    assert len(llamadas) == 2, "vencida la copia, se revalida contra el SNIFA"


def test_snifa_vencida_sin_red_entrega_copia_marcada(monkeypatch, tmp_path):
    estado = {"red": True}

    def _pedir(url, metodo="GET", headers=None, cuerpo=None, timeout=25):
        if not estado["red"]:
            raise RuntimeError("red caída")
        return _respuesta_snifa()

    monkeypatch.setattr(ambiental_connector, "pedir_http", _pedir)
    cliente = ambiental_connector.SMAClient(cache_dir=str(tmp_path))

    cliente.search_sancionatorios(nombre="prueba")
    cache = next(tmp_path.glob("sanc_*.json"))
    _envejecer(cache, dias=10)
    estado["red"] = False

    datos = cliente.search_sancionatorios(nombre="prueba")
    assert datos["resultados"][0]["expediente"] == "D-1-2026"
    assert datos.get("copia_local_vencida") is True


def test_listado_hf_concurrente_descarga_una_sola_vez(monkeypatch, tmp_path):
    """El precalentado del server y la primera consulta piden el listado a la vez: una descarga."""
    from concurrent.futures import ThreadPoolExecutor

    import online_library_sync as ols

    pytest.importorskip("huggingface_hub")
    monkeypatch.setattr(ols, "CACHE_HF", tmp_path)

    llamadas = []

    class _HfFalso:
        def __init__(self, *args, **kwargs):
            pass

        def list_repo_files(self, repo_id, repo_type=None):
            llamadas.append(repo_id)
            time.sleep(0.3)
            return ["a.md", "b.md"]

    monkeypatch.setattr("huggingface_hub.HfApi", _HfFalso)
    monkeypatch.setattr(ols, "resolver_token_hf", lambda: "token-falso")
    monkeypatch.setattr(ols, "_ARCHIVOS_HF_CACHE", {})

    with ThreadPoolExecutor(max_workers=4) as pool:
        resultados = list(pool.map(lambda _: ols._listar_archivos_hf("repo/prueba"), range(4)))

    assert all(r == ["a.md", "b.md"] for r in resultados)
    assert len(llamadas) == 1, "cuatro llamadas simultáneas no pueden pagar cuatro descargas"


# ─────────────────── Listado HF en disco (24 h) ───────────────────


def _hf_falso(monkeypatch, ols, archivos):
    llamadas = []

    class _Hf:
        def __init__(self, *args, **kwargs):
            pass

        def list_repo_files(self, repo_id, repo_type=None):
            llamadas.append(repo_id)
            return list(archivos)

    monkeypatch.setattr("huggingface_hub.HfApi", _Hf)
    monkeypatch.setattr(ols, "resolver_token_hf", lambda: "token-falso")
    return llamadas


def test_listado_hf_se_reutiliza_desde_disco(monkeypatch, tmp_path):
    """Segundo proceso (memoria vacía) lee la copia en disco: no vuelve a pagar el hub (~18 s)."""
    import online_library_sync as ols

    pytest.importorskip("huggingface_hub")

    monkeypatch.setattr(ols, "CACHE_HF", tmp_path)
    monkeypatch.setattr(ols, "_ARCHIVOS_HF_CACHE", {})
    llamadas = _hf_falso(monkeypatch, ols, ["a.md", "b.md"])

    assert ols._listar_archivos_hf("repo/prueba") == ["a.md", "b.md"]
    assert llamadas == ["repo/prueba"]
    assert (tmp_path / "repo__prueba__listado.json").exists(), "la copia queda en disco"

    monkeypatch.setattr(ols, "_ARCHIVOS_HF_CACHE", {})   # memoria vacía = proceso nuevo
    assert ols._listar_archivos_hf("repo/prueba") == ["a.md", "b.md"]
    assert len(llamadas) == 1, "con la copia en disco no se vuelve al hub"


def test_listado_hf_vencido_se_refresca(monkeypatch, tmp_path):
    import online_library_sync as ols

    pytest.importorskip("huggingface_hub")

    monkeypatch.setattr(ols, "CACHE_HF", tmp_path)
    monkeypatch.setattr(ols, "_ARCHIVOS_HF_CACHE", {})
    mapa = tmp_path / "repo__prueba__listado.json"
    mapa.write_text(json.dumps({"repo": "repo/prueba", "t": time.time() - 999_999,
                                "archivos": ["viejo.md"]}), encoding="utf-8")
    llamadas = _hf_falso(monkeypatch, ols, ["nuevo.md"])

    assert ols._listar_archivos_hf("repo/prueba") == ["nuevo.md"]
    assert llamadas == ["repo/prueba"], "vencida la copia, se revalida contra el hub"
    actualizado = json.loads(mapa.read_text(encoding="utf-8"))
    assert actualizado["archivos"] == ["nuevo.md"], "la copia de disco se actualiza"


def test_listado_hf_vencido_sin_red_usa_la_copia(monkeypatch, tmp_path):
    """Sin red, el índice viejo sirve igual: es un índice de búsqueda, no una cita."""
    import online_library_sync as ols

    pytest.importorskip("huggingface_hub")

    monkeypatch.setattr(ols, "CACHE_HF", tmp_path)
    monkeypatch.setattr(ols, "_ARCHIVOS_HF_CACHE", {})
    monkeypatch.setattr(ols, "resolver_token_hf", lambda: "token-falso")
    mapa = tmp_path / "repo__prueba__listado.json"
    mapa.write_text(json.dumps({"repo": "repo/prueba", "t": time.time() - 999_999,
                                "archivos": ["viejo.md"]}), encoding="utf-8")

    class _HfRoto:
        def __init__(self, *args, **kwargs):
            pass

        def list_repo_files(self, repo_id, repo_type=None):
            raise RuntimeError("sin red")

    monkeypatch.setattr("huggingface_hub.HfApi", _HfRoto)

    assert ols._listar_archivos_hf("repo/prueba") == ["viejo.md"]


# ─────────────────────────── Helpers de caché (config) ───────────────────────────

def test_cache_fresco_y_vencido(tmp_path):
    import config

    archivo = tmp_path / "c.json"
    assert config.cache_fresco(str(archivo), 60) is False          # no existe
    archivo.write_text("{}", encoding="utf-8")
    assert config.cache_fresco(str(archivo), 60) is True
    vencido = time.time() - 3600
    os.utime(archivo, (vencido, vencido))
    assert config.cache_fresco(str(archivo), 60) is False


def test_leer_json_si_se_puede(tmp_path):
    import config

    assert config.leer_json_si_se_puede(str(tmp_path / "nada.json")) is None
    roto = tmp_path / "roto.json"
    roto.write_text("{no es json", encoding="utf-8")
    assert config.leer_json_si_se_puede(str(roto)) is None
    bueno = tmp_path / "bueno.json"
    bueno.write_text('{"a": 1}', encoding="utf-8")
    assert config.leer_json_si_se_puede(str(bueno)) == {"a": 1}
