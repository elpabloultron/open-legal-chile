"""El medidor de rendimiento tiene que correr sin red y escribir sus dos salidas."""

import json
import pathlib
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]


def test_el_bench_corre_y_escribe(tmp_path):
    out_md = tmp_path / "bench.md"
    out_json = tmp_path / "bench.json"
    res = subprocess.run([sys.executable, str(RAIZ / "scripts" / "bench_rendimiento.py"),
                          "--salida-md", str(out_md), "--salida-json", str(out_json)],
                         capture_output=True, text=True, encoding="utf-8", cwd=RAIZ, timeout=600)
    assert res.returncode == 0, res.stderr[-400:]
    datos = json.loads(out_json.read_text(encoding="utf-8"))
    assert {"fecha", "mediciones"} <= set(datos)
    assert len(datos["mediciones"]) >= 3
    nombres = {m["medicion"] for m in datos["mediciones"]}
    assert "import mcp_server" in nombres
    assert "grafo (carga + subgrafo)" in nombres
    assert out_md.read_text(encoding="utf-8").startswith("# Benchmarks")
