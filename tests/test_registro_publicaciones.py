"""Candado del registro de publicaciones ambientales (metadatos de la cosecha).

El registro se amplía a mano cuando aparece una publicación nueva (boletines 2TA, anuarios
sueltos): este test impide reintroducir duplicados, filas sin fuente o boletines sin número,
que es como se pisaron los anuarios la vez que el nombrado salió del nombre de la carpeta.
"""
from __future__ import annotations

import json
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[1]
REGISTRO = RAIZ / "data" / "jurisprudencia" / "ambiental_boletines_anuarios.jsonl"


def _filas():
    return [json.loads(linea) for linea in REGISTRO.read_text(encoding="utf-8").splitlines() if linea.strip()]


def test_sin_duplicados():
    claves = []
    for r in _filas():
        base = str(r.get("numero") or r.get("anio"))
        tomo = str(r.get("tomo") or "").strip()
        claves.append((r["tribunal"], r["tipo"], f"{base}-t{tomo}" if tomo else base))
    assert len(claves) == len(set(claves)), "hay filas repetidas en el registro"


def test_filas_completas():
    for r in _filas():
        assert r.get("tribunal") in {"1TA", "2TA", "3TA"}, r
        assert r.get("tribunal_nombre"), r
        assert r.get("titulo"), r
        assert r.get("url_pdf"), r


def test_boletines_con_numero():
    for r in _filas():
        if str(r.get("tipo", "")).startswith("Boletín"):
            assert str(r.get("numero", "")).strip(), f"boletín sin número: {r.get('titulo')}"
