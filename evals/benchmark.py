"""
Open Legal Chile — Evaluador de Rendimiento Jurídico (Chilean Legal Benchmark)
Evalúa las respuestas de cualquier modelo de lenguaje contra el ordenamiento jurídico chileno:
1. Puntuación de Citas Oficiales (BCN, CGR, DT, CS, CPR).
2. Detección y penalización de términos inexistentes de Common Law.
3. Precisión dogmática y jurisprudencial.
"""

import os
import sys
import json
from typing import Dict, Any, List

def evaluate_response(test_case: Dict[str, Any], response_text: str) -> Dict[str, Any]:
    text_lower = response_text.lower()
    
    # 1. Verificar criterios obligatorios
    matched_criteria = []
    missing_criteria = []
    for crit in test_case.get("criterios_obligatorios", []):
        if crit.lower() in text_lower:
            matched_criteria.append(crit)
        else:
            missing_criteria.append(crit)

    # 2. Verificar términos prohibidos de Common Law
    forbidden_hits = []
    for forb in test_case.get("prohibiciones", []):
        if forb.lower() in text_lower:
            forbidden_hits.append(forb)

    # 3. Calcular puntaje (0.0 a 10.0)
    total_criteria = len(test_case.get("criterios_obligatorios", []))
    score = (len(matched_criteria) / total_criteria) * 10.0 if total_criteria > 0 else 10.0
    
    # Penalizar severamente alucinaciones de Common Law (-3.0 por término)
    score -= (len(forbidden_hits) * 3.0)
    score = max(0.0, min(10.0, score))

    return {
        "id": test_case.get("id"),
        "materia": test_case.get("materia"),
        "score": round(score, 2),
        "passed": score >= 7.0 and len(forbidden_hits) == 0,
        "matched_criteria": matched_criteria,
        "missing_criteria": missing_criteria,
        "forbidden_hits": forbidden_hits
    }

def run_benchmark(eval_file: str = "evals/test_cases.json", provider: str = "") -> Dict[str, Any]:
    if not os.path.exists(eval_file):
        return {"error": f"Archivo no encontrado: {eval_file}"}

    with open(eval_file, "r", encoding="utf-8") as f:
        cases = json.load(f)

    from chat_engine import LegalChatEngine
    engine = LegalChatEngine()
    provider = provider or LegalChatEngine.detect_provider()

    results = []
    total_score = 0.0

    print(f"\n🏛️ INICIANDO BENCHMARK JURÍDICO CHILENO ({len(cases)} Casos de Prueba) — Proveedor: {provider.upper()}")
    print("=" * 80)

    for case in cases:
        print(f"\n🧪 Evaluando: [{case.get('id')}] {case.get('materia')}...")
        resp = engine.chat(user_message=case.get("pregunta"), provider=provider)
        reply = resp.get("reply", "")
        
        eval_res = evaluate_response(case, reply)
        results.append(eval_res)
        total_score += eval_res["score"]

        status = "✅ APROBADO" if eval_res["passed"] else "❌ REPROBADO"
        print(f"   Puntaje: {eval_res['score']}/10.0 — {status}")
        if eval_res["forbidden_hits"]:
            print(f"   ⚠️ Alucinación de Common Law detectada: {eval_res['forbidden_hits']}")

    avg_score = round(total_score / len(cases), 2) if cases else 0.0
    print("\n" + "=" * 80)
    print(f"📊 PROMEDIO GENERAL BENCHMARK: {avg_score} / 10.0")
    print("=" * 80)

    return {
        "total_cases": len(cases),
        "average_score": avg_score,
        "cases": results
    }

if __name__ == "__main__":
    run_benchmark()
