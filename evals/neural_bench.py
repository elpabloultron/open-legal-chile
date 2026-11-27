"""Benchmark reproducible de modelos neuronales locales (`ChileNeuralEmbedder` + `LegalGNNEngine`).

Mide carga en frío, latencia por consulta, calibración semántica chilena, ordenamiento Top-K
del reranker y tiempos de predicción de enlaces + auditoría de brechas normativas sin red externa.

Uso:
    .venv/bin/python evals/neural_bench.py
"""

from __future__ import annotations

import json
import pathlib
import sys
import time
from typing import Any, Dict, List

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def ejecutar_benchmark_neuronal() -> Dict[str, Any]:
    """Ejecuta pruebas deterministas de precisión y latencia sobre los modelos `.npz` locales."""
    from legal_gnn import obtener_motor_gnn, reiniciar_motor_gnn
    from neural_retriever import obtener_embedder_chileno, obtener_reranker_chileno, reiniciar_modelos_neurales

    reiniciar_modelos_neurales()
    reiniciar_motor_gnn()

    t0 = time.perf_counter()
    embedder = obtener_embedder_chileno()
    reranker = obtener_reranker_chileno()
    t_load_emb_ms = (time.perf_counter() - t0) * 1000.0

    t1 = time.perf_counter()
    gnn = obtener_motor_gnn()
    t_load_gnn_ms = (time.perf_counter() - t1) * 1000.0

    pares_sinonimia = [
        (
            "autodespido por incumplimiento grave del empleador",
            "Artículo 171 Código del Trabajo despido indirecto imputable al empleador indemnizaciones",
            "concesión minera de explotación patente anual Código de Minería",
        ),
        (
            "precario por mera tolerancia sin contrato previo",
            "Artículo 2195 inciso segundo Código Civil tenencia ajena por ignorancia o mera tolerancia",
            "recurso de nulidad penal causal absoluta artículo 374 CPP",
        ),
        (
            "ley karin prevención investigación y sanción acoso laboral",
            "Ley 21.643 modifica Código del Trabajo protocolo violencia acoso sexual trabajo",
            "compensación económica divorcio menoscabo económico Ley 19.947",
        ),
        (
            "registro nacional de deudores pensión de alimentos retención",
            "Ley 21.389 Ley 14.908 alimentos UTM pago efectivo fondos previsionales",
            "recurso de reclamación ambiental artículo 17 Ley 20.600",
        ),
    ]

    sinonimia_ok = 0
    rerank_ok = 0
    lat_emb_ms: List[float] = []
    for q, pos_doc, neg_doc in pares_sinonimia:
        t_q = time.perf_counter()
        vq = embedder.encode(q)
        lat_emb_ms.append((time.perf_counter() - t_q) * 1000.0)
        s_pos = float(vq @ embedder.encode(pos_doc))
        s_neg = float(vq @ embedder.encode(neg_doc))
        if s_pos > s_neg:
            sinonimia_ok += 1

        ordenados = reranker.rerank(
            q,
            [
                {"etiqueta_bcn": "Distractor no relacionado", "texto": neg_doc},
                {"etiqueta_bcn": "Norma pertinente Chile", "texto": pos_doc},
            ],
            top_k=2,
        )
        if ordenados and "Norma pertinente" in ordenados[0].get("etiqueta_bcn", ""):
            rerank_ok += 1

    consultas_gnn = [
        "Art. 2314 Código Civil",
        "Art. 161 Código del Trabajo",
        "Ley N° 19.300",
    ]
    lat_gnn_ms: List[float] = []
    gnn_con_pred = 0
    for c in consultas_gnn:
        tg = time.perf_counter()
        pred = gnn.predecir_enlaces(c, relacion="todas", top_k=5)
        lat_gnn_ms.append((time.perf_counter() - tg) * 1000.0)
        if pred.get("nodo_origen") is not None and len(pred.get("predicciones") or []) >= 1:
            gnn_con_pred += 1

    tb = time.perf_counter()
    brechas = gnn.auditar_brechas_escrito(
        "EN LO PRINCIPAL: Demanda de indemnización de perjuicios por responsabilidad extracontractual "
        "y daño moral fundada en el artículo 2314 del Código Civil. El demandado actuó con culpa y "
        "provocó lesiones graves acreditadas mediante documental y peritajes dentro de plazo.",
        top_k=6,
    )
    lat_brechas_ms = (time.perf_counter() - tb) * 1000.0

    metricas_archivo = {}
    m_path = RAIZ / "data" / "modelos" / "metricas_entrenamiento.json"
    if m_path.is_file():
        metricas_archivo = json.loads(m_path.read_text(encoding="utf-8"))

    return {
        "embedder_backend": embedder.backend,
        "embedder_disponible": embedder.modelo_disponible,
        "reranker_backend": reranker.backend,
        "gnn_backend": gnn.backend,
        "gnn_disponible": gnn.modelo_disponible,
        "carga_embedder_ms": round(t_load_emb_ms, 2),
        "carga_gnn_ms": round(t_load_gnn_ms, 2),
        "latencia_encode_mediana_ms": round(sorted(lat_emb_ms)[len(lat_emb_ms) // 2], 3),
        "latencia_gnn_pred_mediana_ms": round(sorted(lat_gnn_ms)[len(lat_gnn_ms) // 2], 3),
        "latencia_brechas_ms": round(lat_brechas_ms, 3),
        "sinonimia_chile_aprobados": f"{sinonimia_ok}/{len(pares_sinonimia)}",
        "reranker_orden_aprobados": f"{rerank_ok}/{len(pares_sinonimia)}",
        "gnn_anclajes_aprobados": f"{gnn_con_pred}/{len(consultas_gnn)}",
        "brechas_detectadas": brechas.get("cobertura_estructural", {}),
        "metricas_held_out": metricas_archivo,
    }


def main() -> int:
    res = ejecutar_benchmark_neuronal()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
