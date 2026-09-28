#!/usr/bin/env python3
"""Mide los caminos calientes de la suite y escribe docs/bench_rendimiento.md y .json.

    .venv/bin/python scripts/bench_rendimiento.py
    .venv/bin/python scripts/bench_rendimiento.py --comparar

Los números son una SERIE (medidos en la máquina de turno), no umbrales de CI: sirven para
detectar regresiones comparando corridas; `--comparar` imprime los deltas contra el JSON guardado.
Ninguna medición usa red: todas corren contra el corpus y los índices locales.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import platform
import subprocess
import sys
import tempfile
import time

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def medir_import_mcp() -> dict:
    """El arranque del servidor MCP en proceso nuevo (se paga en cada sesión de harness)."""
    codigo = ("import time;t=time.perf_counter();import mcp_server;"
              "print(f'{1000*(time.perf_counter()-t):.0f}')")
    salida = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, capture_output=True,
                            text=True, encoding="utf-8", timeout=300)
    ms = (salida.stdout or "").strip() or "?"
    return {"detalle": f"arranque en proceso nuevo: {ms} ms "
                       "(decisión 2026-09-28: sin arranque perezoso, YAGNI)"}


def medir_grafo() -> dict:
    """Carga en frío del grafo + un subgrafo (la cifra «~72 s» era CPU saturada por OCR; son ~0,4 s)."""
    from legal_graphify import LegalGraphifyEngine
    engine = LegalGraphifyEngine()
    engine.cargar_grafo_json()
    nodos = engine.graph.number_of_nodes()
    r = engine.consultar_subgrafo("humedal", max_hops=1)
    return {"detalle": f"{nodos:,} nodos · subgrafo {'ok' if r else 'vacío'}"}


def medir_subgrafo_frio() -> dict:
    """La 1ª consulta al grafo en un proceso nuevo, SIN cargar el artefacto a mano.

    Es el camino del server recién arrancado: antes del arreglo del 2026-09-28 reconstruía el
    corpus doctrinal completo (62-70 s medidos); ahora carga el JSON publicado (~0,3 s) y responde.
    """
    codigo = (
        "import time,sys;sys.path.insert(0, '.');"
        "from legal_graphify import LegalGraphifyEngine;"
        "e = LegalGraphifyEngine();"
        "t = time.perf_counter();r = e.consultar_subgrafo('humedal');"
        "print(f'{time.perf_counter()-t:.2f}', r.get('encontrado'))"
    )
    salida = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, capture_output=True,
                            text=True, encoding="utf-8", timeout=300)
    partes = (salida.stdout or "").strip().split()
    if len(partes) != 2:
        raise RuntimeError(f"salida inesperada: {salida.stdout!r} {salida.stderr[-200:]!r}")
    return {"detalle": f"1ª consulta en proceso nuevo: {float(partes[0]):.2f} s "
                       f"(antes del arreglo: 62-70 s) · encontrado={partes[1]}"}


def medir_fts() -> dict:
    """Índice trigram sobre 200k líneas: indexado una vez y consulta después (en ms)."""
    import shutil

    import hf_cache_index
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="bench_hf_"))
    original = hf_cache_index.DIR_INDICES
    hf_cache_index.DIR_INDICES = tmp / "indices"
    transformar = lambda linea: json.loads(linea)["texto"]  # noqa: E731 — lambda corta por claridad
    try:
        grande = tmp / "grande.jsonl"
        with grande.open("w", encoding="utf-8") as f:
            for i in range(200_000):
                texto = ("ficha final con humedal rarisimo" if i == 199_999
                         else f"ficha {i} sin materia")
                f.write(json.dumps({"texto": texto}, ensure_ascii=False) + "\n")
        t0 = time.perf_counter()
        hf_cache_index.indexar(grande, transformar=transformar)
        t1 = time.perf_counter()
        r = hf_cache_index.buscar(grande, ["rarisimo"], transformar=transformar)
        t2 = time.perf_counter()
        return {"detalle": f"200k líneas · indexado {t1 - t0:.2f} s · "
                           f"consulta {1000 * (t2 - t1):.0f} ms ({len(r)} resultado)",
                "segundos_indexado": round(t1 - t0, 3),
                "ms_consulta": round(1000 * (t2 - t1))}
    finally:
        hf_cache_index.DIR_INDICES = original
        shutil.rmtree(tmp, ignore_errors=True)


def medir_ambiental() -> dict:
    """La consulta ambiental local, en frío y en caliente (caché de textos por proceso)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("modulo_ambiental_bench", RAIZ / "modulo_ambiental.py")
    if spec is None or spec.loader is None:
        return {"detalle": "modulo_ambiental no cargable"}
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    tiene_corpus = ((RAIZ / "publicaciones_ambientales").exists()
                    or (RAIZ / "biblioteca_ambiental").exists())
    if not tiene_corpus:
        t0 = time.perf_counter()
        mod.consulta_ambiental("humedales", limite=3)
        return {"detalle": f"corpus local ausente (CI): arranque {time.perf_counter() - t0:.2f} s"}
    t0 = time.perf_counter()
    r1 = mod.consulta_ambiental("humedales", limite=5)
    t1 = time.perf_counter()
    r2 = mod.consulta_ambiental("humedales", limite=5)
    t2 = time.perf_counter()
    return {"detalle": f"1ª {t1 - t0:.2f} s (fría) · 2ª {t2 - t1:.2f} s (caliente) · "
                       f"{len(r1['resultados'])} y {len(r2['resultados'])} resultados",
            "segundos_fria": round(t1 - t0, 2), "segundos_caliente": round(t2 - t1, 2)}


def medir_consulta_maestra() -> dict:
    """El armado de consulta_maestra sin red (los cuatro sondeos corren en paralelo)."""
    import mcp_server as m
    originales = (m._hf_para_consulta, m._doctrina_para_consulta,
                  m._normas_para_consulta, m._subgrafo_para_consulta)
    m._hf_para_consulta = lambda query, lim=3: {"resultados": [], "citas": []}
    m._doctrina_para_consulta = lambda query, lim=3: {"resultados": [], "citas": []}
    m._normas_para_consulta = lambda query: []
    m._subgrafo_para_consulta = lambda query, hops=1: {}
    try:
        r = m.handle_tool_call("consulta_maestra", {"consulta": "humedales"})
    finally:
        (m._hf_para_consulta, m._doctrina_para_consulta,
         m._normas_para_consulta, m._subgrafo_para_consulta) = originales
    return {"detalle": f"armado sin red · faltantes: {r.get('faltantes')}"}


MEDICIONES = (
    ("import mcp_server", medir_import_mcp),
    ("grafo (carga + subgrafo)", medir_grafo),
    ("subgrafo en frío (proceso nuevo)", medir_subgrafo_frio),
    ("fts trigram (200k líneas)", medir_fts),
    ("consulta ambiental (fría/caliente)", medir_ambiental),
    ("consulta_maestra (armado)", medir_consulta_maestra),
)


def _cronometrar(nombre: str, fn) -> dict:
    t0 = time.perf_counter()
    try:
        extra, fallo = (fn() or {}), None
    except Exception as error:  # noqa: BLE001 — una medición caída no tumba el bench
        extra, fallo = {}, f"{type(error).__name__}: {str(error)[:140]}"
    fila = {"medicion": nombre, "segundos": round(time.perf_counter() - t0, 3), **extra}
    if fallo:
        fila["error"] = fallo
    return fila


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmarks versionados de Open Legal Chile")
    parser.add_argument("--salida-md", default=str(RAIZ / "docs" / "bench_rendimiento.md"))
    parser.add_argument("--salida-json", default=str(RAIZ / "docs" / "bench_rendimiento.json"))
    parser.add_argument("--comparar", action="store_true",
                        help="imprime los deltas contra el JSON guardado antes de reescribirlo")
    args = parser.parse_args()

    anterior = None
    if args.comparar and pathlib.Path(args.salida_json).exists():
        try:
            anterior = json.loads(pathlib.Path(args.salida_json).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            anterior = None

    filas = [_cronometrar(nombre, fn) for nombre, fn in MEDICIONES]
    fecha = time.strftime("%Y-%m-%d %H:%M")
    datos = {"fecha": fecha, "python": platform.python_version(),
             "plataforma": platform.platform(), "mediciones": filas}

    if anterior:
        previos = {m.get("medicion"): m.get("segundos") for m in anterior.get("mediciones", [])}
        print(f"Deltas contra la corrida del {anterior.get('fecha', '?')}:")
        for fila in filas:
            antes = previos.get(fila["medicion"])
            if isinstance(antes, (int, float)):
                print(f"  {fila['medicion']}: {antes:.3f}s → {fila['segundos']:.3f}s "
                      f"({fila['segundos'] - antes:+.3f}s)")

    lineas_md = [
        "# Benchmarks de Open Legal Chile",
        "",
        f"Medido el {fecha} en `{platform.platform()}` · Python {platform.python_version()}.",
        "",
        "> Estos números son una **serie**, no umbrales: la gracia es compararlos entre corridas.",
        "> `.venv/bin/python scripts/bench_rendimiento.py --comparar` imprime los deltas.",
        "",
        "| Medición | Segundos | Detalle |",
        "|---|---:|---|",
    ]
    for fila in filas:
        detalle = fila.get("detalle") or fila.get("error") or ""
        lineas_md.append(f"| {fila['medicion']} | {fila['segundos']:.2f} | {detalle} |")
    lineas_md += [
        "",
        "Notas: la carga del grafo (~0,4 s) desmintió la cifra falsa de «~72 s» que había quedado",
        "de una corrida con la CPU saturada por OCR; el arranque del MCP (~0,40 s) cerró el ítem del",
        "arranque perezoso como no-acción (YAGNI). El 2026-09-28 (noche) la 1ª consulta al grafo en",
        "frío pasó de 62-70 s a ~1 s: el subgrafo carga primero el artefacto publicado y el server lo",
        "precalienta en segundo plano al arrancar.",
        "",
    ]

    pathlib.Path(args.salida_md).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.salida_md).write_text("\n".join(lineas_md), encoding="utf-8")
    pathlib.Path(args.salida_json).write_text(json.dumps(datos, ensure_ascii=False, indent=2),
                                              encoding="utf-8")
    print(f"OK · {args.salida_md} · {args.salida_json}")


if __name__ == "__main__":
    main()
