"""Pruebas unitarias e integración para v2.1.0 (Bi-Encoder Chileno, Reranker Monotónico y LegalGNN)."""

from __future__ import annotations

import pathlib
from concurrent.futures import ThreadPoolExecutor

import numpy as np


def test_embedder_chileno_dimension_sinonimia_y_fallback(monkeypatch):
    from neural_retriever import (
        ChileNeuralEmbedder,
        obtener_embedder_chileno,
        reiniciar_modelos_neurales,
    )

    reiniciar_modelos_neurales()
    emb = obtener_embedder_chileno()
    assert emb.modelo_disponible is True
    assert emb.dim == 384

    vq = emb.encode("autodespido por incumplimiento grave del empleador")
    vp = emb.encode("Artículo 171 del Código del Trabajo sobre despido indirecto e indemnizaciones")
    vn = emb.encode("patente municipal y concesión minera del Código de Minería")
    assert vq.shape == (384,)
    assert abs(float(np.linalg.norm(vq)) - 1.0) < 1e-4
    assert float(vq @ vp) > float(vq @ vn)

    # Degradación honesta sin artefacto disponible
    vacio = ChileNeuralEmbedder(model_path=pathlib.Path("/tmp/no_existe_chile_embed_v999.npz"))
    assert vacio.modelo_disponible is False
    assert vacio.backend == "unavailable"
    assert np.allclose(vacio.encode("cualquier consulta"), 0.0)

    # Escape hatch de desactivación explícita en VectorLegalEngine
    monkeypatch.setenv("OPENLEGAL_NEURAL_EMBEDDINGS", "0")
    from vector_engine import SemanticEmbeddingEngine

    eng_lex = SemanticEmbeddingEngine()
    assert eng_lex.backend == "lexical_random_projection"
    monkeypatch.delenv("OPENLEGAL_NEURAL_EMBEDDINGS", raising=False)
    reiniciar_modelos_neurales()


def test_reranker_monotonico_y_concurrencia_sin_deadlock():
    from neural_retriever import obtener_reranker_chileno, reiniciar_modelos_neurales

    reiniciar_modelos_neurales()

    # Inicialización concurrente multi-hilo: valida threading.RLock sin deadlock
    with ThreadPoolExecutor(max_workers=6) as pool:
        instancias = list(pool.map(lambda _: obtener_reranker_chileno(), range(6)))
    assert all(inst is instancias[0] for inst in instancias)

    rr = instancias[0]
    assert rr.modelo_disponible is True
    candidatos = [
        {"etiqueta_bcn": "Distractor neutro", "texto": "concesión minera de explotación patente anual Código de Minería"},
        {"etiqueta_bcn": "Norma pertinente", "texto": "Artículo 171 Código del Trabajo despido indirecto imputable al empleador"},
    ]
    ordenados = rr.rerank("autodespido por incumplimiento grave del empleador", candidatos, top_k=2)
    assert len(ordenados) == 2
    assert ordenados[0]["etiqueta_bcn"] == "Norma pertinente"
    assert ordenados[0]["puntaje_reranker"] > ordenados[1]["puntaje_reranker"]


def test_legal_gnn_prediccion_auditoria_y_degradacion():
    from legal_gnn import LegalGNNEngine, obtener_motor_gnn

    gnn = obtener_motor_gnn()
    assert gnn.modelo_disponible is True

    pred = gnn.predecir_enlaces("Art. 2314 Código Civil", relacion="norma", top_k=5)
    assert pred["nodo_origen"] is not None
    assert len(pred["predicciones"]) == 5
    etiquetas = {p["label"] for p in pred["predicciones"]}
    assert any("2329" in e or "2332" in e or "1698" in e for e in etiquetas)
    assert all(p["verificacion_requerida"] is True for p in pred["predicciones"])

    brechas = gnn.auditar_brechas_escrito(
        "EN LO PRINCIPAL: Demanda por responsabilidad extracontractual fundada en el artículo 2314 del Código Civil.",
        top_k=5,
    )
    assert len(brechas["nodos_ancla"]) >= 1
    assert len(brechas["normas_sugeridas"]) >= 1

    # Degradación honesta sin artefacto
    vacio = LegalGNNEngine(model_path=pathlib.Path("/tmp/no_existe_legal_gnn_v999.npz"))
    assert vacio.modelo_disponible is False
    res_off = vacio.predecir_enlaces("Art. 2314 CC")
    assert res_off["modelo_disponible"] is False and res_off["predicciones"] == []


def test_mcp_critique_y_consulta_maestra_integracion_gnn():
    import mcp_server
    from critique import LegalCritiqueEngine

    nombres = {t["name"] for t in mcp_server.TOOLS}
    assert {"gnn_predecir_enlaces", "gnn_auditar_brechas_escrito"} <= nombres

    r_pred = mcp_server.handle_tool_call(
        "gnn_predecir_enlaces",
        {"nodo_o_consulta": "Art. 161 Código del Trabajo", "relacion": "norma", "top_k": 4},
    )
    assert r_pred.get("modelo_disponible") is True
    assert len(r_pred.get("predicciones") or []) >= 1

    r_brechas = mcp_server.handle_tool_call(
        "gnn_auditar_brechas_escrito",
        {"texto": "Despido por necesidades de la empresa del artículo 161 del Código del Trabajo.", "top_k": 4},
    )
    assert r_brechas.get("modelo_disponible") is True
    assert len(r_brechas.get("nodos_ancla") or []) >= 1

    # Revisión Goldfish incluye sección consultiva LegalGNN sin volver bloqueante un texto válido
    borrador = (
        "EN LO PRINCIPAL: Demanda en juicio ordinario civil.\n"
        "Comparecencia: Juan Pérez, RUT 12.345.678-5, domiciliado en Santiago.\n\n"
        "HECHOS\n"
        + (
            "El día 10 de mayo de 2025 el demandado condujo sin diligencia y provocó una colisión "
            "que ocasionó daños materiales emergentes, gastos médicos y secuelas acreditadas mediante "
            "prueba documental, pericial y testigos dentro del plazo legal de prescripción de cuatro años. "
        )
        * 2
        + "\nDERECHO\n"
        "Dispone el artículo 2314 del Código Civil: «El que ha cometido un delito o cuasidelito que ha "
        "inferido daño a otro, es obligado a la indemnización; sin perjuicio de la pena que le impongan las "
        "leyes por el delito o cuasidelito». Comparezco con patrocinio y poder según Ley 18.120.\n\n"
        "POR TANTO, ruego a SS. acoger la demanda con costas."
    )
    engine = LegalCritiqueEngine()
    res_crit = engine.critique(borrador, provider="soberano", modo="goldfish")
    dictamen = str(res_crit.get("critique") or "")
    assert "Cobertura Normativa Sugerida" in dictamen
    assert "APROBADO PARA FIRMA (PASS)" in dictamen

    r_cm = mcp_server.handle_tool_call(
        "consulta_maestra",
        {"consulta": "Art. 2314 Código Civil responsabilidad extracontractual"},
    )
    sug_gnn = (r_cm.get("hallazgos") or {}).get("sugerencias_gnn")
    assert isinstance(sug_gnn, list) and len(sug_gnn) >= 1
