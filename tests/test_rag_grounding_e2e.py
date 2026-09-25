"""
Open Legal Chile — Test E2E de Grounding Doctrinal y RAG (Nivel 3)
Verifica que las consultas doctrinales recuperen tratados canónicos reales
y que el 100% de los resultados contenga enlaces verificables a Hugging Face.
"""

import pytest
from evals.rag_evaluator import evaluate_rag_retrieval


def test_rag_doctrinal_grounding_e2e():
    """Ejecuta la batería de evaluación RAG doctrinal y valida integridad al 100%."""
    eval_result = evaluate_rag_retrieval()

    assert eval_result["total_casos"] >= 4
    assert eval_result["promedio_score"] >= 8.5
    assert eval_result["hf_link_integrity_pct"] == 100.0

    for caso in eval_result["casos"]:
        assert caso["passed"] is True
        assert caso["hf_grounded"] is True
        assert caso["total_docs"] > 0
