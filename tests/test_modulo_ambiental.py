"""Candado del módulo de derecho ambiental: detección de materia y consulta con citas."""
from __future__ import annotations

import importlib.util
import pathlib

import pytest

RAIZ = pathlib.Path(__file__).resolve().parents[1]


def _modulo():
    spec = importlib.util.spec_from_file_location("modulo_ambiental", RAIZ / "modulo_ambiental.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_detecta_materia_ambiental():
    mod = _modulo()
    assert mod.es_materia_ambiental("reclamación contra la RCA del proyecto")
    assert mod.es_materia_ambiental("sanción de la SMA por incumplimiento del PdC")
    assert mod.es_materia_ambiental("daño ambiental en humedales urbanos")
    assert not mod.es_materia_ambiental("despido injustificado y finiquito")


def test_consulta_trae_citas_y_texto():
    mod = _modulo()
    r = mod.consulta_ambiental("informe en derecho R-40", limite=3)
    assert r["resultados"], "sin resultados"
    primero = r["resultados"][0]
    for clave in ("titulo", "archivo", "cita", "enlace"):
        assert clave in primero
    assert "[Hugging Face -" in primero["cita"]
    assert r["citas"] and r["citas"][0]["formato"].startswith("[Hugging Face -")


def test_fragmento_con_corpus_local():
    if not (RAIZ / "publicaciones_ambientales").exists() and not (RAIZ / "biblioteca_ambiental").exists():
        pytest.skip("corpus local no presente (CI): el barrido de texto requiere los .md")
    mod = _modulo()
    r = mod.consulta_ambiental("humedales", limite=5)
    assert r["resultados"]
    assert any(x.get("fragmento") for x in r["resultados"])


def test_el_texto_se_lee_una_vez_por_proceso(monkeypatch):
    """La segunda consulta no puede volver a leer el corpus: ese es el punto del caché."""
    if not (RAIZ / "publicaciones_ambientales").exists() and not (RAIZ / "biblioteca_ambiental").exists():
        pytest.skip("corpus local no presente (CI)")
    mod = _modulo()
    mod._limpiar_caches()
    llamadas = {"n": 0}
    original = pathlib.Path.read_text

    def _cuenta(self, *a, **k):
        if "ambientales" in str(self) or "biblioteca_ambiental" in str(self):
            llamadas["n"] += 1
        return original(self, *a, **k)
    monkeypatch.setattr(pathlib.Path, "read_text", _cuenta)

    r1 = mod.consulta_ambiental("humedales", limite=5)
    primera = llamadas["n"]
    assert primera > 0, "la primera consulta sí lee el corpus"

    r2 = mod.consulta_ambiental("humedales", limite=5)
    assert llamadas["n"] == primera, "la segunda consulta no debe releer el corpus"
    assert r1["resultados"][0]["titulo"] == r2["resultados"][0]["titulo"]


def test_extracto_de_sentencia_desde_el_texto_completo(tmp_path, monkeypatch):
    mod = _modulo()
    monkeypatch.setattr(mod, "BASE", tmp_path)
    (tmp_path / "jurisprudencia_ambiental").mkdir()
    (tmp_path / "jurisprudencia_ambiental" / "R-574-2025.md").write_text(
        "x" * 120 + " El tribunal razona sobre los olores ofensivos y la cautelar pedida. " + "y" * 6000,
        encoding="utf-8")

    extracto = mod._extracto_de_sentencia("jurisprudencia_ambiental/R-574-2025.md", ["olores"])

    assert "olores ofensivos" in extracto


def test_ficha_de_sentencia_no_se_cita_como_texto(tmp_path, monkeypatch):
    mod = _modulo()
    monkeypatch.setattr(mod, "BASE", tmp_path)
    (tmp_path / "ficha.md").write_text("# Reclamación — R-51-2021\n- **Rol:** R-51-2021\n", encoding="utf-8")

    assert mod._extracto_de_sentencia("ficha.md", ["olores"]) == ""


def test_consulta_cita_el_pasaje_literal_de_la_sentencia(tmp_path, monkeypatch):
    mod = _modulo()
    monkeypatch.setattr(mod, "BASE", tmp_path)
    (tmp_path / "jurisprudencia_ambiental" / "2TA").mkdir(parents=True)
    (tmp_path / "jurisprudencia_ambiental" / "2TA" / "R-574-2025.md").write_text(
        "Considerando décimo: los olores ofensivos acreditan el riesgo inminente. " + "z" * 6000,
        encoding="utf-8")
    monkeypatch.setattr(mod, "_archivo_por_rol",
                        lambda: {("2TA", "R-574-2025"): "jurisprudencia_ambiental/2TA/R-574-2025.md"})
    monkeypatch.setattr(mod, "_filas_colecciones", lambda: [])

    import tribunales_ambientales_connector

    class Conector:
        def search_jurisprudencia(self, consulta):
            return [{"tribunal": "2TA", "rol": "R-574-2025", "titulo": "Vecinos con SMA",
                     "caratula": "Vecinos con SMA", "materia": "Sancionatorio SMA", "resuelve": "",
                     "fecha": "2025-08-01", "tipo": "Reclamación"}]

    monkeypatch.setattr(tribunales_ambientales_connector, "TribunalesAmbientalesClient", Conector)

    res = mod.consulta_ambiental("olores ofensivos humedal", limite=3)

    assert res["resultados"], "sin resultados"
    assert "olores ofensivos" in res["resultados"][0]["fragmento"]


def test_sin_texto_se_describe_el_fallo_y_no_se_cita_la_materia(tmp_path, monkeypatch):
    mod = _modulo()
    monkeypatch.setattr(mod, "BASE", tmp_path)
    monkeypatch.setattr(mod, "_archivo_por_rol", lambda: {})
    monkeypatch.setattr(mod, "_filas_colecciones", lambda: [])

    import tribunales_ambientales_connector

    class Conector:
        def search_jurisprudencia(self, consulta):
            return [{"tribunal": "1TA", "rol": "R-51-2021", "titulo": "Huasco Altinos con SMA",
                     "caratula": "Huasco Altinos con SMA", "materia": "Contencioso Ambiental / SMA / SEA",
                     "fecha": "13/10/2022", "tipo": "Reclamación"}]

    monkeypatch.setattr(tribunales_ambientales_connector, "TribunalesAmbientalesClient", Conector)

    res = mod.consulta_ambiental("reclamación SMA", limite=3)

    fragmento = res["resultados"][0]["fragmento"]
    assert "Huasco Altinos" in fragmento
    assert "Contencioso Ambiental / SMA / SEA" not in fragmento
