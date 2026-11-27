"""Entrenamiento reproducible en CPU (NumPy/SciPy) del Bi-Encoder Contrastivo + Reranker chileno.

Fuentes 100 % reales del repositorio:
- `data/parquet/doctrina_fichas.parquet` (instituciones dogmáticas + definiciones + concordancias)
- `data/parquet/grafo_aristas.parquet` + `grafo_nodos.parquet` (relaciones sustantivas curadas)
- Anclas léxico-dogmáticas de sinonimia jurídica chilena (sin Common Law)

Evaluación honesta con partición determinista 90 % entrenamiento / 10 % validación ciega (seed=42).
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
import time
from typing import Any, Dict, List, Tuple

import duckdb
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from neural_retriever import (  # noqa: E402
    EMBEDDING_DIM,
    _gelu,
    _hash_tfidf_128,
    _l2_normalize,
    calcular_features_reranker,
    extraer_terminos_juridicos,
)
from vector_engine import SemanticEmbeddingEngine  # noqa: E402

PARQUET_DIR = RAIZ / "data" / "parquet"
OUT_DIR = RAIZ / "data" / "modelos"
OUT_NPZ = OUT_DIR / "chile_embed_v1.npz"
METRICS_JSON = OUT_DIR / "metricas_entrenamiento.json"

_ANCLAS_SINONIMIA_CL: Tuple[Tuple[str, str], ...] = (
    (
        "autodespido trabajador por incumplimiento grave empleador",
        "despido indirecto Art. 171 Código del Trabajo término contrato imputable empleador indemnización",
    ),
    (
        "daño moral por rebote familiares víctima accidente",
        "víctima por repercusión acción directa originaria daño moral Art. 2329 Código Civil muerte",
    ),
    (
        "precario ocupación inmueble sin contrato dueño",
        "tenencia por ignorancia o mera tolerancia sin previo contrato Art. 2195 inciso 2 Código Civil",
    ),
    (
        "invalidación acto administrativo ilegal plazo dos años",
        "Art. 53 Ley N.° 19.880 potestad invalidatoria administración audiencia interesado nulidad derecho público",
    ),
    (
        "tutela laboral vulneración garantías fundamentales trabajador",
        "procedimiento tutela derechos fundamentales Art. 485 Código del Trabajo prueba indiciaria",
    ),
    (
        "despido necesidades empresa carta descuento afc",
        "Art. 161 inciso 1 Código del Trabajo recargo 30 % Art. 168 restitución aporte empleador AFC Ley 19.728",
    ),
    (
        "ley karin prevención acoso laboral y violencia en el trabajo",
        "Ley N.° 21.643 protocolo prevención investigación acoso sexual laboral violencia medidas resguardo",
    ),
    (
        "protección datos personales vigencia agencia derechos arco",
        "Ley N.° 19.628 Ley N.° 21.719 prórroga vacancia legal Ley N.° 21.855 15 de octubre de 2027 derechos ARCO+",
    ),
    (
        "delitos económicos responsabilidad penal empresa modelo prevención",
        "Ley N.° 21.595 delitos económicos Ley N.° 20.393 responsabilidad penal personas jurídicas días-multa",
    ),
    (
        "recurso de protección plazo acto ilegal o arbitrario corte apelaciones",
        "Art. 20 Constitución Política Acta N.° 94-2015 Corte Suprema 30 días corridos derechos indubitados",
    ),
    (
        "posesión inscrita inmueble prescripción contra título inscrito",
        "Art. 724 Art. 728 Art. 2505 Código Civil inscripción Conservador Bienes Raíces teoría posesión inscrita",
    ),
    (
        "pensión de alimentos en utm deudor registro nacional afp",
        "Ley N.° 14.908 alimentos en UTM Ley N.° 21.389 Registro Nacional Deudores Ley N.° 21.484 pago fondos AFP",
    ),
)


def _cargar_pares_reales() -> List[Tuple[str, str, str]]:
    """Construye pares `(query, title, doc)` reales desde doctrina y grafo sustantivo."""
    pares: List[Tuple[str, str, str]] = []
    rel_fichas = duckdb.sql(
        """
        SELECT institucion, area, autor, obra, definicion, operativa_procesal, concordancias, fallo_rector
        FROM read_parquet(?)
        WHERE length(trim(definicion)) >= 25
          AND lower(institucion) NOT LIKE '1.%obras%'
        """,
        params=[str(PARQUET_DIR / "doctrina_fichas.parquet")],
    )
    fichas = rel_fichas.fetchall() if rel_fichas is not None else []

    for inst, area, autor, obra, defin, oper, conc, fallo in fichas:
        inst_s = str(inst or "").strip()
        if not inst_s:
            continue
        doc = " ".join(
            p for p in (
                str(defin or "").strip(),
                str(oper or "").strip(),
                str(conc or "").strip(),
                str(fallo or "").strip(),
            ) if p
        )[:900]
        if len(doc) < 35:
            continue
        q_main = f"{inst_s} ({area})".strip() if area else inst_s
        title = f"{inst_s} · {autor} · {obra}".strip(" ·")
        pares.append((q_main, title, doc))

    # Pares estructurales desde aristas sustantivas del grafo (normas <-> instituciones/fallos)
    rel_nodos_q = duckdb.sql(
        """
        SELECT a.source, n1.label, n1.node_type, n1.area,
               a.target, n2.label, n2.node_type, n2.area, a.relation
        FROM read_parquet(?) a
        JOIN read_parquet(?) n1 ON n1.id = a.source
        JOIN read_parquet(?) n2 ON n2.id = a.target
        WHERE a.es_sustantiva = TRUE
          AND n1.rango_norma_plausible = TRUE
          AND n2.rango_norma_plausible = TRUE
          AND a.relation IN ('fundamenta_en', 'aplica_norma', 'criterio_jurisprudencial', 'aplica_criterio')
          AND length(n1.label) >= 6 AND length(n2.label) >= 6
        LIMIT 3000
        """,
        params=[
            str(PARQUET_DIR / "grafo_aristas.parquet"),
            str(PARQUET_DIR / "grafo_nodos.parquet"),
            str(PARQUET_DIR / "grafo_nodos.parquet"),
        ],
    )
    nodos_q = rel_nodos_q.fetchall() if rel_nodos_q is not None else []

    por_origen: Dict[str, Tuple[str, List[str]]] = {}
    for src, l1, t1, a1, _tgt, l2, _t2, a2, rel in nodos_q:
        lbl = str(l1).strip()
        if lbl.startswith(("inst_", "cs:", "tc:", "ta:")):
            lbl = lbl.replace("_", " ")
        bucket = por_origen.setdefault(str(src), (f"{lbl} ({a1 or t1})", []))
        bucket[1].append(f"{rel.replace('_', ' ')}: {l2} {a2}".strip())

    for _, (q_txt, vecinos) in por_origen.items():
        if not vecinos:
            continue
        doc_txt = " | ".join(vecinos[:8])[:750]
        pares.append((q_txt, q_txt, doc_txt))

    for q_syn, d_syn in _ANCLAS_SINONIMIA_CL:
        pares.append((q_syn, q_syn, d_syn))
    return pares


def _construir_vocabulario_y_tfidf(
    textos_train: List[str],
    *,
    max_vocab: int = 9000,
    min_df: int = 2,
) -> Tuple[List[str], Dict[str, int], np.ndarray]:
    df: Dict[str, int] = {}
    for txt in textos_train:
        for tok in set(extraer_terminos_juridicos(txt)):
            df[tok] = df.get(tok, 0) + 1

    n_docs = float(max(1, len(textos_train)))
    candidatos = [
        (tok, cnt * math.log((1.0 + n_docs) / (1.0 + cnt)))
        for tok, cnt in df.items()
        if cnt >= min_df
    ]
    candidatos.sort(key=lambda x: (-x[1], x[0]))
    vocab_list = [tok for tok, _ in candidatos[:max_vocab]]
    vocab = {tok: i for i, tok in enumerate(vocab_list)}
    idf = np.asarray(
        [math.log((1.0 + n_docs) / (1.0 + df[tok])) + 1.0 for tok in vocab_list],
        dtype=np.float32,
    )
    return vocab_list, vocab, idf


def _matriz_tfidf_csr(textos: List[str], vocab: Dict[str, int], idf: np.ndarray) -> csr_matrix:
    rows: List[int] = []
    cols: List[int] = []
    vals: List[float] = []
    for r_idx, txt in enumerate(textos):
        tf: Dict[int, float] = {}
        for tok in extraer_terminos_juridicos(txt):
            idx = vocab.get(tok)
            if idx is not None:
                tf[idx] = tf.get(idx, 0.0) + 1.0
        if not tf:
            continue
        norm_sq = 0.0
        weighted: Dict[int, float] = {}
        for idx, c in tf.items():
            w = (1.0 + math.log(c)) * float(idf[idx])
            weighted[idx] = w
            norm_sq += w * w
        inv_n = 1.0 / math.sqrt(max(1e-12, norm_sq))
        for idx, w in weighted.items():
            rows.append(r_idx)
            cols.append(idx)
            vals.append(w * inv_n)
    return csr_matrix((vals, (rows, cols)), shape=(len(textos), len(vocab)), dtype=np.float32)


def _normalizar_filas(mat: np.ndarray) -> np.ndarray:
    normas = np.linalg.norm(mat, axis=1, keepdims=True)
    return (mat / np.maximum(normas, 1e-12)).astype(np.float32)


def _entrenar_biencoder_infonce(
    z_q: np.ndarray,
    z_d: np.ndarray,
    *,
    out_dim: int = EMBEDDING_DIM,
    epochs: int = 24,
    batch_size: int = 256,
    lr: float = 2.5e-3,
    tau: float = 0.08,
    seed: int = 42,
) -> Tuple[Dict[str, np.ndarray], float]:
    rng = np.random.default_rng(seed)
    k_dim = z_q.shape[1]
    scale1 = math.sqrt(2.0 / k_dim)
    scale2 = math.sqrt(1.0 / out_dim)

    params: Dict[str, np.ndarray] = {
        "w_res": (rng.standard_normal((k_dim, out_dim)) * math.sqrt(1.0 / k_dim)).astype(np.float32),
        "b_res": np.zeros(out_dim, dtype=np.float32),
        "w1": (rng.standard_normal((k_dim, out_dim)) * scale1).astype(np.float32),
        "b1": np.zeros(out_dim, dtype=np.float32),
        "w2": (rng.standard_normal((out_dim, out_dim)) * scale2).astype(np.float32),
        "b2": np.zeros(out_dim, dtype=np.float32),
    }
    m_adam = {k: np.zeros_like(v) for k, v in params.items()}
    v_adam = {k: np.zeros_like(v) for k, v in params.items()}
    n_train = z_q.shape[0]
    step = 0
    last_loss = 0.0

    def forward(z: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        a1 = z @ params["w1"] + params["b1"]
        h = _gelu(a1)
        raw = (z @ params["w_res"] + params["b_res"]) + (h @ params["w2"] + params["b2"])
        norms = np.maximum(np.linalg.norm(raw, axis=1, keepdims=True), 1e-8)
        emb = raw / norms
        return emb, raw, h, norms

    def backward_proj(
        z: np.ndarray,
        a1: np.ndarray,
        h: np.ndarray,
        norms: np.ndarray,
        emb: np.ndarray,
        g_emb: np.ndarray,
    ) -> Dict[str, np.ndarray]:
        dot_g = np.sum(g_emb * emb, axis=1, keepdims=True)
        g_raw = (g_emb - emb * dot_g) / norms
        # Derivada aproximada estable de GELU
        c = math.sqrt(2.0 / math.pi)
        t_arg = c * (a1 + 0.044715 * (a1 ** 3))
        th = np.tanh(t_arg)
        dgelu = 0.5 * (1.0 + th) + 0.5 * a1 * (1.0 - th * th) * c * (1.0 + 3.0 * 0.044715 * a1 * a1)

        g_w2 = h.T @ g_raw
        g_b2 = np.sum(g_raw, axis=0)
        g_h = g_raw @ params["w2"].T
        g_a1 = g_h * dgelu
        g_w1 = z.T @ g_a1
        g_b1 = np.sum(g_a1, axis=0)
        g_wres = z.T @ g_raw
        g_bres = np.sum(g_raw, axis=0)
        return {
            "w_res": g_wres,
            "b_res": g_bres,
            "w1": g_w1,
            "b1": g_b1,
            "w2": g_w2,
            "b2": g_b2,
        }

    for ep in range(epochs):
        perm = rng.permutation(n_train)
        ep_loss = 0.0
        batches = 0
        lr_cur = lr * (0.5 * (1.0 + math.cos(math.pi * ep / max(1, epochs))))
        lr_cur = max(lr_cur, 2e-4)
        for start in range(0, n_train, batch_size):
            idx = perm[start : start + batch_size]
            if len(idx) < 8:
                continue
            zq_b = z_q[idx]
            zd_b = z_d[idx]
            eq, _rq, hq, nq = forward(zq_b)
            ed, _rd, hd, nd = forward(zd_b)
            a1q = zq_b @ params["w1"] + params["b1"]
            a1d = zd_b @ params["w1"] + params["b1"]

            logits = (eq @ ed.T) / tau
            logits_shift = logits - np.max(logits, axis=1, keepdims=True)
            exp_q = np.exp(logits_shift)
            p_q = exp_q / np.sum(exp_q, axis=1, keepdims=True)

            logits_t = logits.T - np.max(logits.T, axis=1, keepdims=True)
            exp_d = np.exp(logits_t)
            p_d = exp_d / np.sum(exp_d, axis=1, keepdims=True)

            bsz = len(idx)
            diag_idx = np.arange(bsz)
            loss_q = -np.mean(np.log(np.maximum(p_q[diag_idx, diag_idx], 1e-12)))
            loss_d = -np.mean(np.log(np.maximum(p_d[diag_idx, diag_idx], 1e-12)))
            loss = 0.5 * float(loss_q + loss_d)
            ep_loss += loss
            batches += 1

            g_logits_q = p_q.copy()
            g_logits_q[diag_idx, diag_idx] -= 1.0
            g_logits_d = p_d.copy()
            g_logits_d[diag_idx, diag_idx] -= 1.0
            g_logits = 0.5 * (g_logits_q + g_logits_d.T) / (float(bsz) * tau)

            g_eq = g_logits @ ed
            g_ed = g_logits.T @ eq

            grads_q = backward_proj(zq_b, a1q, hq, nq, eq, g_eq)
            grads_d = backward_proj(zd_b, a1d, hd, nd, ed, g_ed)

            step += 1
            for k in params:
                g = grads_q[k] + grads_d[k] + 1e-4 * params[k]
                np.clip(g, -2.0, 2.0, out=g)
                m_adam[k] = 0.9 * m_adam[k] + 0.1 * g
                v_adam[k] = 0.999 * v_adam[k] + 0.001 * (g * g)
                m_hat = m_adam[k] / (1.0 - 0.9 ** step)
                v_hat = v_adam[k] / (1.0 - 0.999 ** step)
                params[k] -= lr_cur * m_hat / (np.sqrt(v_hat) + 1e-8)
        last_loss = ep_loss / max(1, batches)
    return params, round(last_loss, 4)


def _forward_encoder(z: np.ndarray, params: Dict[str, np.ndarray]) -> np.ndarray:
    h = _gelu(z @ params["w1"] + params["b1"])
    raw = (z @ params["w_res"] + params["b_res"]) + (h @ params["w2"] + params["b2"])
    return _normalizar_filas(raw)


def _evaluar_retrieval(eq: np.ndarray, ed: np.ndarray) -> Dict[str, float]:
    sim = eq @ ed.T
    n = sim.shape[0]
    r1 = r5 = r10 = 0
    mrr10 = 0.0
    for i in range(n):
        orden = np.argsort(-sim[i])
        pos_hits = np.where(orden == i)[0]
        rank = int(pos_hits[0]) + 1 if len(pos_hits) > 0 else n
        if rank == 1:
            r1 += 1
        if rank <= 5:
            r5 += 1
        if rank <= 10:
            r10 += 1
            mrr10 += 1.0 / rank
    denom = float(max(1, n))
    return {
        "recall_at_1_pct": round(100.0 * r1 / denom, 2),
        "recall_at_5_pct": round(100.0 * r5 / denom, 2),
        "recall_at_10_pct": round(100.0 * r10 / denom, 2),
        "mrr_at_10": round(mrr10 / denom, 4),
    }


def _entrenar_reranker(
    pares_train: List[Tuple[str, str, str]],
    pares_val: List[Tuple[str, str, str]],
    eq_tr: np.ndarray,
    ed_tr: np.ndarray,
    x_tr_q: csr_matrix,
    x_tr_d: csr_matrix,
    eq_val: np.ndarray,
    ed_val: np.ndarray,
    x_val_q: csr_matrix,
    x_val_d: csr_matrix,
    *,
    seed: int = 42,
) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
    rng = np.random.default_rng(seed)
    n_sample = min(len(pares_train), 2500)
    idxs = rng.choice(len(pares_train), size=n_sample, replace=False)

    feats_x: List[np.ndarray] = []
    labels_y: List[float] = []
    weights_w: List[float] = []

    sim_n_mat = eq_tr[idxs] @ ed_tr.T
    sim_t_mat = (x_tr_q[idxs] @ x_tr_d.T).toarray()

    for row_i, i in enumerate(idxs):
        q, t_pos, d_pos = pares_train[int(i)]
        ocultar_titulo = bool(rng.random() < 0.5)
        t_pos_eff = "" if ocultar_titulo else t_pos
        cos_n = float(sim_n_mat[row_i, i])
        cos_t = float(sim_t_mat[row_i, i])
        feats_x.append(calcular_features_reranker(q, t_pos_eff, d_pos, cos_neural=cos_n, cos_tfidf=cos_t))
        labels_y.append(1.0)
        weights_w.append(4.0)

        # 2 negativos difíciles (alta similitud pero documento distinto) + 2 negativos aleatorios
        orden = np.argsort(-sim_n_mat[row_i])
        negs: List[int] = []
        for cand in orden[:40]:
            c_idx = int(cand)
            if c_idx != int(i):
                negs.append(c_idx)
            if len(negs) >= 2:
                break
        for _ in range(2):
            rand_i = int(rng.integers(0, len(pares_train)))
            if rand_i != int(i) and rand_i not in negs:
                negs.append(rand_i)
        for neg_i in negs[:4]:
            if neg_i == int(i):
                continue
            _, t_neg, d_neg = pares_train[neg_i]
            t_neg_eff = "" if ocultar_titulo else t_neg
            feats_x.append(
                calcular_features_reranker(
                    q,
                    t_neg_eff,
                    d_neg,
                    cos_neural=float(sim_n_mat[row_i, neg_i]),
                    cos_tfidf=float(sim_t_mat[row_i, neg_i]),
                )
            )
            labels_y.append(0.0)
            weights_w.append(1.0)

    x_arr = np.vstack(feats_x).astype(np.float32)
    y_arr = np.asarray(labels_y, dtype=np.float32)[:, None]
    w_arr = np.asarray(weights_w, dtype=np.float32)[:, None]

    mean = np.mean(x_arr, axis=0)
    std = np.maximum(np.std(x_arr, axis=0), 1e-4)
    x_norm = (x_arr - mean) / std

    h_dim = 32
    w1 = np.abs(rng.standard_normal((x_norm.shape[1], h_dim)) * math.sqrt(2.0 / x_norm.shape[1])).astype(np.float32) * 0.35
    b1 = np.zeros(h_dim, dtype=np.float32)
    w2 = np.abs(rng.standard_normal((h_dim, 1)) * math.sqrt(1.0 / h_dim)).astype(np.float32) * 0.35
    b2 = np.zeros(1, dtype=np.float32)

    decay_w1 = np.full((x_norm.shape[1], 1), 0.002, dtype=np.float32)
    decay_w1[6, 0] = 0.025  # regularización extra sobre title_overlap
    decay_w1[7, 0] = 0.025  # regularización extra sobre log_len

    params = {"w1": w1, "b1": b1, "w2": w2, "b2": b2}
    m_a = {k: np.zeros_like(v) for k, v in params.items()}
    v_a = {k: np.zeros_like(v) for k, v in params.items()}
    step = 0
    bsz = 256
    for _ in range(36):
        perm = rng.permutation(x_norm.shape[0])
        for st in range(0, x_norm.shape[0], bsz):
            sl = perm[st : st + bsz]
            xb = x_norm[sl]
            yb = y_arr[sl]
            wb = w_arr[sl]
            h_pre = xb @ params["w1"] + params["b1"]
            h = np.maximum(0.0, h_pre)
            logits = np.clip(h @ params["w2"] + params["b2"], -20.0, 20.0)
            probs = 1.0 / (1.0 + np.exp(-logits))
            g_log = ((probs - yb) * wb) / float(max(1.0, float(np.sum(wb))))
            g_w2 = h.T @ g_log
            g_b2 = np.sum(g_log, axis=0)
            g_h = g_log @ params["w2"].T
            g_hpre = g_h * (h_pre > 0.0)
            g_w1 = xb.T @ g_hpre
            g_b1 = np.sum(g_hpre, axis=0)
            grads = {"w1": g_w1, "b1": g_b1, "w2": g_w2, "b2": g_b2}
            step += 1
            for k in params:
                l2 = decay_w1 if k == "w1" else 0.002
                g = grads[k] + l2 * params[k]
                m_a[k] = 0.9 * m_a[k] + 0.1 * g
                v_a[k] = 0.999 * v_a[k] + 0.001 * (g * g)
                mh = m_a[k] / (1.0 - 0.9 ** step)
                vh = v_a[k] / (1.0 - 0.999 ** step)
                params[k] -= 0.008 * mh / (np.sqrt(vh) + 1e-8)
            params["w1"] = np.maximum(0.0, params["w1"])
            params["w2"] = np.maximum(0.0, params["w2"])

    # Evaluación en split held-out (reordenando Top-20 candidatos por query)
    n_val = len(pares_val)
    sim_val_n = eq_val @ ed_val.T
    sim_val_t = (x_val_q @ x_val_d.T).toarray()
    mrr_bi = mrr_rr = 0.0
    hits1_bi = hits1_rr = 0
    for i in range(n_val):
        top20 = [int(c) for c in np.argsort(-sim_val_n[i])[:20]]
        if i not in top20:
            continue
        rank_bi = top20.index(i) + 1
        mrr_bi += 1.0 / rank_bi
        if rank_bi == 1:
            hits1_bi += 1

        q_txt = pares_val[i][0]
        scored = []
        for c in top20:
            _, t_c, d_c = pares_val[c]
            fv = calcular_features_reranker(
                q_txt,
                t_c,
                d_c,
                cos_neural=float(sim_val_n[i, c]),
                cos_tfidf=float(sim_val_t[i, c]),
            )
            xn = (fv - mean) / std
            hh = np.maximum(0.0, xn @ params["w1"] + params["b1"])
            sc = float((hh @ params["w2"] + params["b2"]).item())
            scored.append((sc, c))
        scored.sort(key=lambda x: -x[0])
        orden_rr = [c for _, c in scored]
        rank_rr = orden_rr.index(i) + 1
        mrr_rr += 1.0 / rank_rr
        if rank_rr == 1:
            hits1_rr += 1

    rr_pack = {
        "rr_mean": mean,
        "rr_std": std,
        "rr_w1": params["w1"],
        "rr_b1": params["b1"],
        "rr_w2": params["w2"],
        "rr_b2": params["b2"],
    }
    rr_metrics = {
        "val_queries": n_val,
        "biencoder_top20_recall1_pct": round(100.0 * hits1_bi / max(1, n_val), 2),
        "reranker_top20_recall1_pct": round(100.0 * hits1_rr / max(1, n_val), 2),
        "biencoder_top20_mrr": round(mrr_bi / max(1, n_val), 4),
        "reranker_top20_mrr": round(mrr_rr / max(1, n_val), 4),
    }
    return rr_pack, rr_metrics


def main() -> int:
    t0 = time.perf_counter()
    pares = _cargar_pares_reales()
    rng = np.random.default_rng(42)
    perm = rng.permutation(len(pares))
    n_val = max(200, int(0.10 * len(pares)))
    val_idx = perm[:n_val]
    tr_idx = perm[n_val:]

    # Anclas de sinonimia chilena siempre incluidas en train y duplicadas en eval por separado si se requiere
    pares_tr = [pares[int(i)] for i in tr_idx]
    pares_val = [pares[int(i)] for i in val_idx]

    docs_tr = [f"{t} {d}".strip() for _, t, d in pares_tr]
    queries_tr = [q for q, _, _ in pares_tr]
    vocab_list, vocab, idf = _construir_vocabulario_y_tfidf(docs_tr + queries_tr, max_vocab=8500, min_df=2)

    x_tr_q = _matriz_tfidf_csr(queries_tr, vocab, idf)
    x_tr_d = _matriz_tfidf_csr(docs_tr, vocab, idf)
    x_val_q = _matriz_tfidf_csr([q for q, _, _ in pares_val], vocab, idf)
    x_val_d = _matriz_tfidf_csr([f"{t} {d}".strip() for _, t, d in pares_val], vocab, idf)

    # SVD truncado sobre corpus combinado de entrenamiento (160 dims latentes)
    k_svd = 160
    _, _, vt = svds(x_tr_d, k=k_svd)
    svd_proj = vt.T[:, ::-1].astype(np.float32)

    z_tr_q = _normalizar_filas(x_tr_q @ svd_proj)
    z_tr_d = _normalizar_filas(x_tr_d @ svd_proj)
    z_val_q = _normalizar_filas(x_val_q @ svd_proj)
    z_val_d = _normalizar_filas(x_val_d @ svd_proj)

    sem_dim = 256
    lex_dim = EMBEDDING_DIM - sem_dim
    peso_sem = 0.62
    peso_lex = 0.78

    enc_params, loss_final = _entrenar_biencoder_infonce(z_tr_q, z_tr_d, out_dim=sem_dim)

    def _encode_sparse_hybrid(x_csr: csr_matrix, z_mat: np.ndarray) -> np.ndarray:
        eq_sem = _forward_encoder(z_mat, enc_params)
        lex_vecs = []
        for r in range(x_csr.shape[0]):
            row = x_csr.getrow(r)
            sp = {int(c): float(v) for c, v in zip(row.indices, row.data, strict=True)}
            lex_vecs.append(_hash_tfidf_128(sp, vocab_list, dim_lex=lex_dim))
        lex_mat = np.vstack(lex_vecs)
        comb = np.hstack([peso_sem * eq_sem, peso_lex * lex_mat])
        return _normalizar_filas(comb)

    eq_tr = _encode_sparse_hybrid(x_tr_q, z_tr_q)
    ed_tr = _encode_sparse_hybrid(x_tr_d, z_tr_d)
    eq_val = _encode_sparse_hybrid(x_val_q, z_val_q)
    ed_val = _encode_sparse_hybrid(x_val_d, z_val_d)

    met_neural = _evaluar_retrieval(eq_val, ed_val)

    # Baseline exacto: lexical_random_projection actual
    base_eng = SemanticEmbeddingEngine(use_fastembed=False, model_path=None, use_chile_neural=False)
    base_q = base_eng.encode_batch([q for q, _, _ in pares_val])
    base_d = base_eng.encode_batch([f"{t} {d[:400]}".strip() for _, t, d in pares_val])
    met_base = _evaluar_retrieval(base_q, base_d)

    rr_pack, rr_metrics = _entrenar_reranker(
        pares_tr, pares_val, eq_tr, ed_tr, x_tr_q, x_tr_d, eq_val, ed_val, x_val_q, x_val_d
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dt_s = round(time.perf_counter() - t0, 2)
    meta = {
        "backend": "chile_neural_embed_v1",
        "version": "1.0.0",
        "total_pares": len(pares),
        "pares_train": len(pares_tr),
        "pares_val_held_out": len(pares_val),
        "vocab_size": len(vocab_list),
        "svd_dim": k_svd,
        "sem_dim": sem_dim,
        "lex_dim": lex_dim,
        "embed_dim": EMBEDDING_DIM,
        "peso_semantico": peso_sem,
        "peso_lexico": peso_lex,
        "infonce_loss_final": loss_final,
        "tiempo_entrenamiento_s": dt_s,
    }

    np.savez_compressed(
        str(OUT_NPZ),
        vocab_utf8=np.frombuffer(json.dumps(vocab_list, ensure_ascii=False).encode("utf-8"), dtype=np.uint8),
        meta_utf8=np.frombuffer(json.dumps(meta, ensure_ascii=False).encode("utf-8"), dtype=np.uint8),
        idf=idf.astype(np.float32),
        svd_proj=svd_proj.astype(np.float16),
        w_res=enc_params["w_res"].astype(np.float16),
        b_res=enc_params["b_res"].astype(np.float32),
        w1=enc_params["w1"].astype(np.float16),
        b1=enc_params["b1"].astype(np.float32),
        w2=enc_params["w2"].astype(np.float16),
        b2=enc_params["b2"].astype(np.float32),
        rr_mean=rr_pack["rr_mean"].astype(np.float32),
        rr_std=rr_pack["rr_std"].astype(np.float32),
        rr_w1=rr_pack["rr_w1"].astype(np.float32),
        rr_b1=rr_pack["rr_b1"].astype(np.float32),
        rr_w2=rr_pack["rr_w2"].astype(np.float32),
        rr_b2=rr_pack["rr_b2"].astype(np.float32),
    )

    size_mb = round(OUT_NPZ.stat().st_size / (1024 * 1024), 3)
    resumen_prev = json.loads(METRICS_JSON.read_text(encoding="utf-8")) if METRICS_JSON.is_file() else {}
    resumen_prev["embeddings_y_reranker"] = {
        **meta,
        "peso_artefacto_mb": size_mb,
        "baseline_lexical_val": met_base,
        "chile_neural_val": met_neural,
        "reranker_val": rr_metrics,
    }
    METRICS_JSON.write_text(json.dumps(resumen_prev, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"✅ chile_embed_v1.npz ({size_mb} MB) entrenado en {dt_s}s | loss={loss_final}")
    print(f"   Baseline lexical  (held-out {len(pares_val)}): {met_base}")
    print(f"   ChileNeuralEmbed  (held-out {len(pares_val)}): {met_neural}")
    print(f"   ChileNeuralRerank (Top-20 held-out): {rr_metrics}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
