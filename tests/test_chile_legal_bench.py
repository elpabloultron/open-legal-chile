"""Pruebas offline de regresión para ChileLegalBench v1.0 (105 casos deterministas)."""

from __future__ import annotations

import json
import pathlib

from evals.chile_legal_bench import ejecutar_benchmark

CATEGORIAS_ESPERADAS = {
    "vigencia_normativa",
    "plazos_procesales",
    "calculadoras_cuantias",
    "validacion_formal_cbr",
    "triage_enrutamiento",
    "grounding_doctrina_grafo",
    "anti_alucinacion_common_law",
}


def test_chile_legal_bench_105_casos_100_por_ciento(tmp_path: pathlib.Path) -> None:
    json_p = tmp_path / "bench.json"
    md_p = tmp_path / "bench.md"
    res = ejecutar_benchmark(json_out=str(json_p), md_out=str(md_p))
    assert res["total_casos"] == 105
    assert res["aprobados"] == 105
    assert res["puntaje_global_pct"] == 100.0
    assert set(res["por_categoria"].keys()) == CATEGORIAS_ESPERADAS
    for cat, bloque in res["por_categoria"].items():
        assert bloque["tasa_pct"] == 100.0, f"Fallo en categoría {cat}: {bloque}"

    cargado = json.loads(json_p.read_text(encoding="utf-8"))
    assert cargado["aprobados"] == 105
    md_txt = md_p.read_text(encoding="utf-8")
    assert "ChileLegalBench v1.0" in md_txt
    assert "105 / 105" in md_txt
