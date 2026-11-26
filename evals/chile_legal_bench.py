"""Open Legal Chile — ChileLegalBench v1.0 (Benchmark Jurídico Chileno Reproducible).

Evalúa determinísticamente 105 casos curados del ordenamiento jurídico de la República de Chile
en 7 categorías (100 % offline, trazable por SHA/reglas positivas y sin llamadas a LLM):
1. vigencia_normativa (10 casos)
2. plazos_procesales (15 casos)
3. calculadoras_cuantias (15 casos)
4. validacion_formal_cbr (15 casos)
5. triage_enrutamiento (15 casos)
6. grounding_doctrina_grafo (20 casos)
7. anti_alucinacion_common_law (15 casos)
"""

from __future__ import annotations

import argparse
from datetime import date
import json
import pathlib
import statistics
import sys
import time
from typing import Any, Callable, Dict, List, Optional

RAIZ = pathlib.Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

DATASET_POR_DEFECTO = RAIZ / "evals" / "chile_legal_bench_dataset.json"


def _eval_vigencia_normativa(caso: Dict[str, Any]) -> Dict[str, Any]:
    from bcn_connector import evaluar_vigencia_norma

    entrada = caso["entrada"]
    hoy = date.fromisoformat(entrada["hoy"]) if entrada.get("hoy") else None
    res = evaluar_vigencia_norma(
        entrada.get("data") or {},
        hoy=hoy,
        numero_ley=entrada.get("numero_ley"),
    )
    esp = caso["esperado"]
    ok = res.get("estado") == esp["estado"]
    if esp.get("fecha_entrada_vigencia"):
        ok = ok and res.get("fecha_entrada_vigencia") == esp["fecha_entrada_vigencia"]
    if esp.get("contiene_aviso"):
        ok = ok and esp["contiene_aviso"].lower() in str(res.get("aviso") or "").lower()
    return {"passed": ok, "detalle": {"estado": res.get("estado"), "fecha_entrada_vigencia": res.get("fecha_entrada_vigencia")}}


def _eval_plazos_procesales(caso: Dict[str, Any]) -> Dict[str, Any]:
    from calculadoras_chile import calcular_plazo_procesal

    ent = caso["entrada"]
    res = calcular_plazo_procesal(
        fecha_notificacion=ent["fecha_notificacion"],
        plazo_dias=int(ent["plazo_dias"]),
        regimen=ent.get("regimen", "judicial_cpc"),
        dias_suspension_dt=int(ent.get("dias_suspension_dt") or 0),
        feriados_adicionales=ent.get("feriados_adicionales"),
        fecha_referencia=ent.get("fecha_referencia"),
    )
    esp = caso["esperado"]
    ok = res.get("fecha_vencimiento") == esp["fecha_vencimiento"]
    if esp.get("regimen"):
        ok = ok and res.get("regimen") == esp["regimen"]
    if "estado" in esp:
        ok = ok and res.get("estado") == esp["estado"]
    if "plazo_efectivo_dias" in esp:
        ok = ok and res.get("plazo_efectivo_dias") == esp["plazo_efectivo_dias"]
    if "min_feriados" in esp:
        ok = ok and len(res.get("feriados_en_ventana") or []) >= int(esp["min_feriados"])
    return {"passed": ok, "detalle": {"fecha_vencimiento": res.get("fecha_vencimiento"), "estado": res.get("estado")}}


def _eval_calculadoras_cuantias(caso: Dict[str, Any]) -> Dict[str, Any]:
    from calculadoras_chile import (
        calcular_cuantias_legales,
        calcular_finiquito_laboral,
        convertir_moneda_legal,
    )

    ent = caso["entrada"]
    esp = caso["esperado"]
    herr = ent["herramienta"]

    if herr == "finiquito":
        res = calcular_finiquito_laboral(**ent["params"])
        ok = "error" not in res
        if "anios_indemnizables" in esp:
            ok = ok and res["antiguedad"]["anios_indemnizables"] == esp["anios_indemnizables"]
        if "base_tope_aplicado" in esp:
            ok = ok and res["base_calculo"]["tope_90_uf_aplicado"] is esp["base_tope_aplicado"]
        if "recargo_pct" in esp:
            ok = ok and round(float(res["escenario_demanda_judicial"]["recargo_art_168_porcentaje"]), 2) == float(esp["recargo_pct"])
        if "descuento_afc" in esp:
            ok = ok and float(res["finiquito_base"]["descuento_afc_empleador_clp"]) == float(esp["descuento_afc"])
        if "min_total_finiquito" in esp:
            ok = ok and float(res["finiquito_base"]["total_liquido_estimado_clp"]) >= float(esp["min_total_finiquito"])
        if "exact_anios_clp" in esp:
            ok = ok and float(res["finiquito_base"]["indemnizacion_anios_servicio_clp"]) == float(esp["exact_anios_clp"])
        return {"passed": ok, "detalle": {"total_liquido_estimado_clp": res.get("finiquito_base", {}).get("total_liquido_estimado_clp")}}

    if herr == "cuantias":
        res = calcular_cuantias_legales(**ent["params"])
        ok = "error" not in res
        if "min_pension_clp" in esp:
            ok = ok and float(res["pension_minima"]["clp"]) >= float(esp["min_pension_clp"])
        if "exact_pension_min_clp" in esp:
            ok = ok and float(res["pension_minima"]["clp"]) == float(esp["exact_pension_min_clp"])
        if "tope_50_clp" in esp:
            ok = ok and float(res["tope_50_por_ciento_rentas"]["clp"]) == float(esp["tope_50_clp"])
        if "rango_dias_min" in esp:
            ok = ok and res["rango_dias_multa"]["min"] == esp["rango_dias_min"]
        if "rango_dias_max" in esp:
            ok = ok and res["rango_dias_multa"]["max"] == esp["rango_dias_max"]
        return {"passed": ok, "detalle": {"tipo": res.get("tipo")}}

    res = convertir_moneda_legal(**ent["params"])
    ok = "error" not in res and abs(float(res["monto_destino"]) - float(esp["monto_destino"])) <= 0.05
    return {"passed": ok, "detalle": {"monto_destino": res.get("monto_destino")}}


def _eval_validacion_formal_cbr(caso: Dict[str, Any]) -> Dict[str, Any]:
    from cbr_titles import CBRTitleStudyEngine, JudicialPowerVerifier
    from entes_publicos import validar_rut
    from privacidad_anonimizar import anonimizar_texto, desanonimizar_texto

    ent = caso["entrada"]
    esp = caso["esperado"]
    sub = ent["subtipo"]

    if sub == "rut":
        res = validar_rut(ent["rut"])
        ok = res.get("valido") is esp["valido"]
        if esp.get("rut_canonico"):
            ok = ok and res.get("rut_canonico") == esp["rut_canonico"]
        return {"passed": ok, "detalle": {"valido": res.get("valido")}}

    if sub == "mandato":
        res = JudicialPowerVerifier().auditar_mandato(ent["texto_mandato"])
        ok = res.get("cumple_formalidad_patrocinio_poder") is esp["cumple"]
        return {"passed": ok, "detalle": {"cumple": res.get("cumple_formalidad_patrocinio_poder")}}

    if sub == "cbr":
        res = CBRTitleStudyEngine().auditar_cadena_dominio(
            ent["inscripciones"],
            anios_requeridos=int(ent.get("anios_requeridos") or 10),
        )
        ok = res.get("aprobado") is esp["aprobado"]
        if "min_banderas_rojas" in esp:
            ok = ok and len(res.get("banderas_rojas") or []) >= int(esp["min_banderas_rojas"])
        return {"passed": ok, "detalle": {"aprobado": res.get("aprobado"), "cobertura": res.get("cobertura_anios")}}

    res = anonimizar_texto(ent["texto"])
    restaurado = desanonimizar_texto(res["texto_anonimizado"], res["mapa_reversion"])
    ok = (
        res.get("total_reemplazos", 0) >= int(esp.get("min_reemplazos", 1))
        and restaurado == ent["texto"]
        and (esp.get("ocultar") or "") not in res["texto_anonimizado"]
    )
    return {"passed": ok, "detalle": {"total_reemplazos": res.get("total_reemplazos"), "roundtrip": restaurado == ent["texto"]}}


def _eval_triage_enrutamiento(caso: Dict[str, Any]) -> Dict[str, Any]:
    from legal_open_jev import LegalOpenJevEngine

    ent = caso["entrada"]
    esp = caso["esperado"]
    motor = LegalOpenJevEngine()
    decision = motor.evaluate_choice(ent["consulta"], max_tools=int(ent.get("max_tools") or 5))
    ok = True
    if esp.get("materias_validas"):
        ok = ok and decision.materia in esp["materias_validas"]
    if esp.get("herramienta_esperada"):
        ok = ok and esp["herramienta_esperada"] in decision.herramientas_recomendadas
    ok = ok and 1 <= len(decision.herramientas_recomendadas) <= 5
    return {"passed": ok, "detalle": {"materia": decision.materia, "tools": decision.herramientas_recomendadas}}


def _eval_grounding_doctrina_grafo(caso: Dict[str, Any]) -> Dict[str, Any]:
    from doctrina_connector import get_institucion, search_doctrina
    from legal_graphify import LegalGraphifyEngine

    ent = caso["entrada"]
    esp = caso["esperado"]
    sub = ent["subtipo"]

    if sub == "doctrina":
        docs = search_doctrina(ent["query"], limit=int(ent.get("limit") or 3))
        inst = get_institucion(ent["institucion"])
        hf_ok = any(str(d.get("fuente_huggingface") or "").startswith("https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile") for d in docs)
        inst_ok = bool(inst and (inst.get("encontrado") is True or "autor" in inst))
        ok = len(docs) >= int(esp.get("min_docs", 1)) and hf_ok and inst_ok
        return {"passed": ok, "detalle": {"docs": len(docs), "hf_ok": hf_ok, "inst_ok": inst_ok}}

    motor = LegalGraphifyEngine()
    sg = motor.consultar_subgrafo(ent["query"], max_hops=int(ent.get("max_hops") or 1))
    ok = bool(sg.get("encontrado")) and len(sg.get("ppr_vecinos_clave") or []) >= int(esp.get("min_vecinos", 1))
    return {"passed": ok, "detalle": {"encontrado": sg.get("encontrado"), "ahorro": (sg.get("metricas_tokens") or {}).get("porcentaje_ahorro")}}


def _eval_anti_alucinacion_common_law(caso: Dict[str, Any]) -> Dict[str, Any]:
    from critique import verificar_citas_escrito

    ent = caso["entrada"]
    esp = caso["esperado"]
    res = verificar_citas_escrito(ent["texto"], consultar_bcn=False)
    ok = res.get("estado") == esp["estado"]
    if esp.get("requiere_common_law"):
        ok = ok and len(res.get("common_law_prohibido") or []) >= 1
    if esp.get("requiere_articulo_imposible"):
        ok = ok and len(res.get("articulos_imposibles") or []) >= 1
    if esp.get("sin_common_law"):
        ok = ok and len(res.get("common_law_prohibido") or []) == 0
    if esp.get("sin_articulos_imposibles"):
        ok = ok and len(res.get("articulos_imposibles") or []) == 0
    return {"passed": ok, "detalle": {"estado": res.get("estado"), "common_law": res.get("common_law_prohibido")}}


_EVALUADORES: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "vigencia_normativa": _eval_vigencia_normativa,
    "plazos_procesales": _eval_plazos_procesales,
    "calculadoras_cuantias": _eval_calculadoras_cuantias,
    "validacion_formal_cbr": _eval_validacion_formal_cbr,
    "triage_enrutamiento": _eval_triage_enrutamiento,
    "grounding_doctrina_grafo": _eval_grounding_doctrina_grafo,
    "anti_alucinacion_common_law": _eval_anti_alucinacion_common_law,
}


def cargar_dataset(dataset_path: Optional[pathlib.Path] = None) -> List[Dict[str, Any]]:
    ruta = dataset_path or DATASET_POR_DEFECTO
    return list(json.loads(ruta.read_text(encoding="utf-8")))


def _percentil_ms(valores: List[float], p: float) -> float:
    if not valores:
        return 0.0
    ord_v = sorted(valores)
    idx = min(len(ord_v) - 1, max(0, int(round((p / 100.0) * (len(ord_v) - 1)))))
    return round(ord_v[idx], 3)


def generar_reporte_markdown(reporte: Dict[str, Any]) -> str:
    lineas = [
        "# ChileLegalBench v1.0 — Reporte de Evaluación Reproducible",
        "",
        f"- **Fecha de ejecución:** {reporte['fecha']}",
        f"- **Total casos evaluados:** {reporte['total_casos']}",
        f"- **Aprobados:** {reporte['aprobados']} / {reporte['total_casos']} (**{reporte['puntaje_global_pct']} %**)",
        f"- **Latencia mediana (p50) / p95:** {reporte['latencia_p50_ms']} ms / {reporte['latencia_p95_ms']} ms",
        "",
        "| Categoría | Casos | Aprobados | Tasa de Acierto | p50 (ms) | p95 (ms) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]
    for cat, stats in reporte["por_categoria"].items():
        lineas.append(
            f"| `{cat}` | {stats['total']} | {stats['aprobados']} | {stats['tasa_pct']} % | {stats['p50_ms']} | {stats['p95_ms']} |"
        )
    fallidos = [c for c in reporte["casos"] if not c["passed"]]
    if fallidos:
        lineas.extend(["", "## Casos Observados", ""])
        for f in fallidos:
            lineas.append(f"- `{f['id']}` ({f['categoria']}): {f.get('detalle')}")
    return "\n".join(lineas) + "\n"


def ejecutar_benchmark(
    *,
    categoria: Optional[str] = None,
    json_out: Optional[str] = None,
    md_out: Optional[str] = None,
    baseline_json: Optional[str] = None,
    dataset_path: Optional[pathlib.Path] = None,
) -> Dict[str, Any]:
    """Ejecuta ChileLegalBench v1.0 (o una categoría puntual) y genera reportes opcionales."""
    casos = cargar_dataset(dataset_path)
    if categoria:
        casos = [c for c in casos if c.get("categoria") == categoria]

    resultados: List[Dict[str, Any]] = []
    latencias: List[float] = []
    por_cat: Dict[str, Dict[str, Any]] = {}

    for caso in casos:
        cat = str(caso["categoria"])
        evaluador = _EVALUADORES.get(cat)
        if evaluador is None:
            raise ValueError(f"Categoría desconocida en dataset: {cat}")
        t0 = time.perf_counter()
        res_caso = evaluador(caso)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        latencias.append(dt_ms)

        passed = bool(res_caso.get("passed"))
        resultados.append(
            {
                "id": caso["id"],
                "categoria": cat,
                "titulo": caso.get("titulo", ""),
                "passed": passed,
                "latencia_ms": round(dt_ms, 3),
                "detalle": res_caso.get("detalle", {}),
            }
        )
        bucket = por_cat.setdefault(cat, {"total": 0, "aprobados": 0, "latencias": []})
        bucket["total"] += 1
        bucket["aprobados"] += 1 if passed else 0
        bucket["latencias"].append(dt_ms)

    resumen_cat: Dict[str, Dict[str, Any]] = {}
    for cat, b in por_cat.items():
        tasa = round((b["aprobados"] / b["total"]) * 100.0, 2) if b["total"] else 0.0
        resumen_cat[cat] = {
            "total": b["total"],
            "aprobados": b["aprobados"],
            "tasa_pct": tasa,
            "p50_ms": round(statistics.median(b["latencias"]), 3) if b["latencias"] else 0.0,
            "p95_ms": _percentil_ms(b["latencias"], 95.0),
        }

    total_c = len(resultados)
    aprobados = sum(1 for r in resultados if r["passed"])
    reporte: Dict[str, Any] = {
        "benchmark": "ChileLegalBench v1.0",
        "fecha": date.today().isoformat(),
        "total_casos": total_c,
        "aprobados": aprobados,
        "puntaje_global_pct": round((aprobados / total_c) * 100.0, 2) if total_c else 0.0,
        "latencia_p50_ms": round(statistics.median(latencias), 3) if latencias else 0.0,
        "latencia_p95_ms": _percentil_ms(latencias, 95.0),
        "por_categoria": resumen_cat,
        "casos": resultados,
    }

    if baseline_json and pathlib.Path(baseline_json).is_file():
        base = json.loads(pathlib.Path(baseline_json).read_text(encoding="utf-8"))
        base_pct = float(base.get("puntaje_global_pct") or 0.0)
        reporte["comparativa_baseline"] = {
            "baseline_pct": base_pct,
            "delta_pct": round(reporte["puntaje_global_pct"] - base_pct, 2),
        }

    if json_out:
        pathlib.Path(json_out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(json_out).write_text(json.dumps(reporte, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if md_out:
        pathlib.Path(md_out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(md_out).write_text(generar_reporte_markdown(reporte), encoding="utf-8")

    return reporte


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Runner de ChileLegalBench v1.0 (105 casos chilenos).")
    parser.add_argument("--categoria", default="", help="Filtrar por una categoría específica")
    parser.add_argument("--json-out", default="", help="Guardar reporte JSON en esta ruta")
    parser.add_argument("--md-out", default="", help="Guardar reporte Markdown en esta ruta")
    parser.add_argument("--baseline-json", default="", help="Archivo JSON baseline para calcular delta")
    args = parser.parse_args(argv)

    rep = ejecutar_benchmark(
        categoria=args.categoria or None,
        json_out=args.json_out or None,
        md_out=args.md_out or None,
        baseline_json=args.baseline_json or None,
    )
    print(f"📊 ChileLegalBench v1.0: {rep['aprobados']}/{rep['total_casos']} aprobados ({rep['puntaje_global_pct']} %) | p50={rep['latencia_p50_ms']} ms | p95={rep['latencia_p95_ms']} ms")
    for cat, st in rep["por_categoria"].items():
        print(f"  · {cat:<30} {st['aprobados']:>2}/{st['total']:<2} ({st['tasa_pct']:>6.2f} %) | p95={st['p95_ms']} ms")
    return 0 if rep["aprobados"] == rep["total_casos"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
