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
