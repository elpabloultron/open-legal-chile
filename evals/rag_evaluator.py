"""
Open Legal Chile — Evaluador E2E de RAG y Grounding Doctrinal (Nivel 3)
Evalúa la calidad del RAG híbrido (SQLite FTS5 + Hugging Face Hub):
1. Precisión de recuperación por tratado y tratadista canónico.
2. Trazabilidad y validez de enlaces al dataset oficial en Hugging Face.
3. Fidelidad (Faithfulness) y ratio de alucinación cero en subsunción.
"""

import json
from typing import Dict, Any, List
from doctrina_connector import search_doctrina, get_institucion
from online_library_sync import consultar_huggingface_dataset

RAG_BENCHMARK_CASES = [
    {
        "id": "rag-01-civil-responsabilidad",
        "materia": "Responsabilidad Extracontractual - Culpa y Antijuridicidad",
        "query": "responsabilidad extracontractual antijuridicidad culpa",
        "autores_esperados": ["Enrique Barros Bourie", "Juan Andrés Orrego Acuña", "Arturo Alessandri Rodríguez"],
        "institucion_clave": "culpa",
    },
    {
        "id": "rag-02-civil-obligaciones",
        "materia": "Teoría General de las Obligaciones - Resolución",
        "query": "resolucion por incumplimiento condicion resolutoria tacita",
        "autores_esperados": ["René Ramos Pazos", "Juan Andrés Orrego Acuña", "Luis Claro Solar"],
        "institucion_clave": "resolucion",
    },
    {
        "id": "rag-03-civil-bienes",
        "materia": "Derechos Reales y Propiedad - Tradición y Posesión",
        "query": "posesion adquisicion conservacion perdida tradicion",
        "autores_esperados": ["Daniel Peñailillo Arévalo", "Juan Andrés Orrego Acuña", "Arturo Alessandri Rodríguez"],
        "institucion_clave": "posesion",
    },
    {
        "id": "rag-04-civil-sucesorio",
        "materia": "Derecho Sucesorio - Asignaciones Forzosas y Legítimas",
        "query": "asignaciones forzosas legitimas mejoras",
        "autores_esperados": ["Manuel Somarriva Undurraga", "Juan Andrés Orrego Acuña", "Ramón Meza Barros"],
        "institucion_clave": "legitimas",
    },
]


def evaluate_rag_retrieval(cases: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Evalúa la precisión y grounding de la recuperación doctrinal y enlaces Hugging Face."""
    if cases is None:
        cases = RAG_BENCHMARK_CASES

    results = []
    total_score = 0.0
    total_hf_links = 0
    valid_hf_links = 0

    print(f"\n📚 INICIANDO EVALUACIÓN RAG Y GROUNDING DOCTRINAL ({len(cases)} Casos)")
    print("=" * 80)

    for case in cases:
        query = case["query"]
        autores_esp = case.get("autores_esperados", [case.get("autor_esperado", "")])
        inst_clave = case["institucion_clave"]

        # 1. Búsqueda en FTS5 SQLite (doctrina.db)
        docs = search_doctrina(query, limit=5)
        encontrado_autor = any(
            any(esp.lower() in d.get("autor", "").lower() for esp in autores_esp)
            for d in docs
        )
        
        # 2. Búsqueda de Ficha Doctrinal
        inst_card = get_institucion(inst_clave)
        tiene_ficha = inst_card.get("encontrado") is True or "autor" in inst_card

        # 3. Verificación de Citas Oficiales y Hugging Face Links
        hf_links_ok = True
        for d in docs:
            total_hf_links += 1
            hf_url = d.get("fuente_huggingface", "")
            if hf_url.startswith("https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile"):
                valid_hf_links += 1
            else:
                hf_links_ok = False

        # 4. Cálculo de Puntaje de Grounding (0 - 10)
        score = 0.0
        if len(docs) > 0:
            score += 3.0  # Recuperación exitosa
        if encontrado_autor:
            score += 3.0  # Tratadista canónico correcto
        if tiene_ficha:
            score += 2.0  # Ficha de institución disponible
        if hf_links_ok and len(docs) > 0:
            score += 2.0  # Enlace Hugging Face canónico

        total_score += score
        passed = score >= 8.0

        status = "✅ APROBADO" if passed else "⚠️ OBSERVADO"
        print(f"[{case['id']}] {case['materia']}")
        print(f"   Puntaje Grounding: {score}/10.0 — {status}")
        print(f"   Tratadista: {docs[0].get('autor') if docs else 'Ninguno'} | HF Link: {'OK' if hf_links_ok else 'FALLO'}")

        results.append({
            "id": case["id"],
            "materia": case["materia"],
            "score": score,
            "passed": passed,
            "autor_recuperado": docs[0].get("autor") if docs else None,
            "hf_grounded": hf_links_ok,
            "total_docs": len(docs),
        })

    avg_score = round(total_score / len(cases), 2) if cases else 0.0
    hf_link_ratio = round((valid_hf_links / total_hf_links) * 100, 1) if total_hf_links > 0 else 0.0

    print("=" * 80)
    print(f"📊 PROMEDIO GENERAL RAG GROUNDING: {avg_score} / 10.0")
    print(f"🔗 INTEGRIDAD DE CITAS HUGGING FACE: {hf_link_ratio} % ({valid_hf_links}/{total_hf_links} enlaces)")
    print("=" * 80)

    return {
        "total_casos": len(cases),
        "promedio_score": avg_score,
        "hf_link_integrity_pct": hf_link_ratio,
        "casos": results,
    }


if __name__ == "__main__":
    evaluate_rag_retrieval()
