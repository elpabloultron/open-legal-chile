"""Entrenamiento local en CPU de `LegalGNN` Link Predictor (Relational GraphSAGE/APPNP + DistMult).

Construye la red neuronal de predicción de enlaces sobre el subgrafo sustantivo limpio de
`LegalGraphify` (`data/parquet/grafo_nodos.parquet` y `data/parquet/grafo_aristas.parquet`)
usando división estricta 85 % train / 15 % held-out test sin fuga de aristas en la propagación.

Uso:
    .venv/bin/python scripts/entrenar_gnn_chile.py
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
import time
from typing import Dict, List, Sequence, Tuple

import duckdb
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from neural_retriever import normalizar_juridico, obtener_embedder_chileno  # noqa: E402

FAMILIAS_RELACION: Tuple[str, ...] = ("norma", "juris", "estruct")
RELACION_A_FAMILIA: Dict[str, int] = {
    "cita_norma": 0,
    "aplica_norma": 0,
    "concordancia_normativa": 0,
    "comparte_norma": 0,
    "procedimiento_bajo": 0,
    "resuelto_por": 1,
    "cita_rol": 1,
    "criterio_jurisprudencial": 1,
    "aplica_criterio": 1,
    "reclamacion_contra": 1,
    "dictada_por": 1,
    "evaluacion_seia": 1,
}
TIPOS_PRINCIPALES: Tuple[str, ...] = (
    "norma",
    "articulo_legal",
    "documento",
    "institucion",
    "jurisprudencia",
    "sentencia_cs",
    "jurisprudencia_tc",
    "cuerpo_legal",
    "obra",
    "sentencia_ta",
    "guia",
)
TIPO_A_IDX: Dict[str, int] = {t: i for i, t in enumerate(TIPOS_PRINCIPALES)}


def _cargar_subgrafo_limpio() -> Tuple[List[Tuple[str, str, str, str, float, int]], np.ndarray]:
    """Extrae nodos con grado sustantivo >= 2 y aristas únicas `(u, v, rel_family)`."""
    rel_nodos = duckdb.sql(
        """
        WITH edges_raw AS (
            SELECT a.source AS s, a.target AS t, a.relation AS rel
            FROM 'data/parquet/grafo_aristas.parquet' a
            JOIN 'data/parquet/grafo_nodos.parquet' n1 ON n1.id = a.source
            JOIN 'data/parquet/grafo_nodos.parquet' n2 ON n2.id = a.target
            WHERE a.es_sustantiva = TRUE
              AND n1.rango_norma_plausible = TRUE
              AND n2.rango_norma_plausible = TRUE
              AND a.source <> a.target
        ),
        deg AS (
            SELECT nid, COUNT(*) AS d FROM (
                SELECT s AS nid FROM edges_raw
                UNION ALL
                SELECT t AS nid FROM edges_raw
            ) GROUP BY 1 HAVING COUNT(*) >= 2
        )
        SELECT n.id, COALESCE(n.label, n.id), COALESCE(n.node_type, 'norma'),
               COALESCE(n.area, ''), COALESCE(n.pagerank_sustantivo, 0.0), d.d::INTEGER
        FROM 'data/parquet/grafo_nodos.parquet' n
        JOIN deg d ON d.nid = n.id
        ORDER BY d.d DESC, n.id ASC
        """
    )
    nodos_raw = rel_nodos.fetchall() if rel_nodos is not None else []

    id_to_idx: Dict[str, int] = {row[0]: i for i, row in enumerate(nodos_raw)}

    rel_aristas = duckdb.sql(
        """
        SELECT a.source, a.target, a.relation
        FROM 'data/parquet/grafo_aristas.parquet' a
        JOIN 'data/parquet/grafo_nodos.parquet' n1 ON n1.id = a.source
        JOIN 'data/parquet/grafo_nodos.parquet' n2 ON n2.id = a.target
        WHERE a.es_sustantiva = TRUE
          AND n1.rango_norma_plausible = TRUE
          AND n2.rango_norma_plausible = TRUE
          AND a.source <> a.target
        """
    )
    aristas_raw = rel_aristas.fetchall() if rel_aristas is not None else []

    vistas = set()
    pares: List[Tuple[int, int, int]] = []
    for src, dst, rel in aristas_raw:
        u = id_to_idx.get(src)
        v = id_to_idx.get(dst)
        if u is None or v is None or u == v:
            continue
        fam = RELACION_A_FAMILIA.get(str(rel), 2)
        a_min, b_max = (u, v) if u < v else (v, u)
        clave = (a_min, b_max, fam)
        if clave in vistas:
            continue
        vistas.add(clave)
        pares.append(clave)

    return nodos_raw, np.asarray(pares, dtype=np.int32)


def _normalizar_adyacencia(n_nodes: int, edges_uv: np.ndarray) -> sp.csr_matrix:
    """Construye `D^{-1/2} A D^{-1/2}` simétrica y sin lazos propios sobre aristas de train."""
    if len(edges_uv) == 0:
        return sp.csr_matrix((n_nodes, n_nodes), dtype=np.float32)
    u = edges_uv[:, 0]
    v = edges_uv[:, 1]
    rows = np.concatenate([u, v])
    cols = np.concatenate([v, u])
    data = np.ones(len(rows), dtype=np.float32)
    mat = sp.csr_matrix((data, (rows, cols)), shape=(n_nodes, n_nodes), dtype=np.float32)
    mat.sum_duplicates()
    mat.data[:] = 1.0
    deg = np.asarray(mat.sum(axis=1)).ravel()
    inv_sqrt = np.where(deg > 0, 1.0 / np.sqrt(np.maximum(deg, 1.0)), 0.0).astype(np.float32)
    d_mat = sp.diags(inv_sqrt)
    return (d_mat @ mat @ d_mat).tocsr()


def _construir_features_nodos(
    nodos_raw: Sequence[Tuple[str, str, str, str, float, int]],
    edges_train: np.ndarray,
    rng: np.random.Generator,
) -> Tuple[np.ndarray, sp.csr_matrix]:
    """Calcula tensor de entrada multi-escala (352 dims): texto chileno + tipos + hops relacionales + SVD."""
    n_nodes = len(nodos_raw)
    embedder = obtener_embedder_chileno()

    textos = [f"{lbl} {ntype} {area}".strip() for _, lbl, ntype, area, _, _ in nodos_raw]
    text_vecs = embedder.encode_batch(textos)  # (N, 384)
    # Matriz de covarianza 384x384 para obtener componentes principales de nodos chilenos
    cov = (text_vecs.T @ text_vecs) / float(max(1, n_nodes))
    _, eigvecs = np.linalg.eigh(cov.astype(np.float64))
    comp_48 = eigvecs[:, -48:][:, ::-1].astype(np.float32)
    feat_txt = text_vecs @ comp_48
    norms = np.linalg.norm(feat_txt, axis=1, keepdims=True)
    feat_txt = np.divide(feat_txt, np.maximum(norms, 1e-6), dtype=np.float32)

    feat_tipo = np.zeros((n_nodes, len(TIPOS_PRINCIPALES) + 1), dtype=np.float32)  # 12
    deg_train = np.zeros(n_nodes, dtype=np.float32)
    np.add.at(deg_train, edges_train[:, 0], 1.0)
    np.add.at(deg_train, edges_train[:, 1], 1.0)

    feat_scalar = np.zeros((n_nodes, 4), dtype=np.float32)
    for i, (_, _, ntype, _, pr, _) in enumerate(nodos_raw):
        feat_tipo[i, TIPO_A_IDX.get(ntype, len(TIPOS_PRINCIPALES))] = 1.0
        feat_scalar[i, 0] = min(1.0, math.log1p(float(deg_train[i])) / 8.0)
        feat_scalar[i, 1] = min(1.0, float(pr) * 120.0)
        feat_scalar[i, 2] = 1.0 if ntype in ("norma", "articulo_legal", "cuerpo_legal") else 0.0
        feat_scalar[i, 3] = 1.0 if "juris" in ntype or "sentencia" in ntype else 0.0

    x0 = np.concatenate([feat_txt, feat_tipo, feat_scalar], axis=1).astype(np.float32)  # (N, 64)

    a_all = _normalizar_adyacencia(n_nodes, edges_train[:, :2])
    a_norma = _normalizar_adyacencia(n_nodes, edges_train[edges_train[:, 2] == 0][:, :2])
    a_juris = _normalizar_adyacencia(n_nodes, edges_train[edges_train[:, 2] == 1][:, :2])
    a_estru = _normalizar_adyacencia(n_nodes, edges_train[edges_train[:, 2] == 2][:, :2])

    h_n1 = a_norma @ x0
    h_j1 = a_juris @ x0
    h_e1 = a_estru @ x0
    h_hop2 = a_all @ (a_all @ x0)

    # 32 componentes espectrales del subgrafo de entrenamiento (sin test edges)
    try:
        u_spec, s_spec, _ = spla.svds(a_all, k=32)
        h_spec = (u_spec * np.sqrt(np.maximum(s_spec, 1e-6))[None, :]).astype(np.float32)
    except Exception:  # noqa: BLE001
        h_spec = np.zeros((n_nodes, 32), dtype=np.float32)
    s_norms = np.linalg.norm(h_spec, axis=1, keepdims=True)
    h_spec = np.divide(h_spec, np.maximum(s_norms, 1e-6), dtype=np.float32)

    features = np.concatenate([x0, h_n1, h_j1, h_e1, h_hop2, h_spec], axis=1).astype(np.float32)  # (N, 352)
    return features, a_all


def _gelu(x: np.ndarray) -> np.ndarray:
    return 0.5 * x * (1.0 + np.tanh(math.sqrt(2.0 / math.pi) * (x + 0.044715 * (x ** 3))))


def _gelu_grad(x: np.ndarray) -> np.ndarray:
    c = math.sqrt(2.0 / math.pi)
    u = c * (x + 0.044715 * (x ** 3))
    th = np.tanh(u)
    sech2 = 1.0 - th * th
    du = c * (1.0 + 3.0 * 0.044715 * (x ** 2))
    return 0.5 * (1.0 + th) + 0.5 * x * sech2 * du


def _forward_encoder(
    x_sub: np.ndarray,
    w1: np.ndarray,
    b1: np.ndarray,
    w2: np.ndarray,
    b2: np.ndarray,
) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
    z1 = x_sub @ w1 + b1
    h1 = _gelu(z1)
    u_raw = h1 @ w2 + b2
    norms = np.maximum(np.linalg.norm(u_raw, axis=1, keepdims=True), 1e-6)
    z_out = (u_raw / norms).astype(np.float32)
    return z_out, {"x_sub": x_sub, "z1": z1, "h1": h1, "u_raw": u_raw, "norms": norms, "z_out": z_out}


def _entrenar_gnn(
    features: np.ndarray,
    nodos_raw: Sequence[Tuple[str, str, str, str, float, int]],
    edges_train: np.ndarray,
    rng: np.random.Generator,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Entrena 2-layer MLP relacional + decoder DistMult con BCE y negativos hard/type-matched."""
    n_nodes, in_dim = features.shape
    hid_dim = 128
    out_dim = 64

    w1 = (rng.normal(0.0, math.sqrt(2.0 / in_dim), size=(in_dim, hid_dim))).astype(np.float32)
    b1 = np.zeros(hid_dim, dtype=np.float32)
    w2 = (rng.normal(0.0, math.sqrt(1.0 / hid_dim), size=(hid_dim, out_dim))).astype(np.float32)
    b2 = np.zeros(out_dim, dtype=np.float32)

    r_rel = np.ones((len(FAMILIAS_RELACION), out_dim), dtype=np.float32)
    b_rel = np.zeros(len(FAMILIAS_RELACION), dtype=np.float32)
    log_tau = np.asarray([math.log(12.0)], dtype=np.float32)

    # Pools por tipo de nodo para muestrear negativos del mismo tipo (hard negatives vectorizados)
    pools_por_tipo_idx: Dict[int, np.ndarray] = {}
    node_types_arr = np.asarray(
        [TIPO_A_IDX.get(row[2], len(TIPOS_PRINCIPALES)) for row in nodos_raw], dtype=np.int32
    )
    for t_id in range(len(TIPOS_PRINCIPALES) + 1):
        idxs_t = np.where(node_types_arr == t_id)[0].astype(np.int32)
        if len(idxs_t) > 0:
            pools_por_tipo_idx[t_id] = idxs_t

    # Pesos de muestreo suavizados por grado para el resto de negativos
    deg_w = np.asarray([math.pow(max(1, row[5]), 0.5) for row in nodos_raw], dtype=np.float64)
    deg_prob = deg_w / deg_w.sum()

    params = [w1, b1, w2, b2, r_rel, b_rel, log_tau]
    m_adam = [np.zeros_like(p) for p in params]
    v_adam = [np.zeros_like(p) for p in params]
    step_t = 0

    n_edges = len(edges_train)
    batch_size = 12288
    epochs = 18
    lr_base = 0.0045
    weight_decay = 1e-4

    for ep in range(epochs):
        perm = rng.permutation(n_edges)
        ep_loss = 0.0
        n_batches = 0
        lr_now = lr_base * (0.2 + 0.8 * 0.5 * (1.0 + math.cos(math.pi * ep / float(epochs))))

        for start in range(0, n_edges, batch_size):
            b_idx = perm[start : start + batch_size]
            pos = edges_train[b_idx]
            b_len = len(pos)
            u_pos = pos[:, 0]
            v_pos = pos[:, 1]
            r_pos = pos[:, 2]

            # 2 negativos por arista positiva: 1 muestreado por grado, 1 del mismo tipo de destino
            neg1_v = rng.choice(n_nodes, size=b_len, p=deg_prob).astype(np.int32)
            v_types = node_types_arr[v_pos]
            neg2_v = np.empty(b_len, dtype=np.int32)
            for t_id, pool_t in pools_por_tipo_idx.items():
                mask_t = v_types == t_id
                cnt = int(np.sum(mask_t))
                if cnt > 0:
                    neg2_v[mask_t] = pool_t[rng.integers(0, len(pool_t), size=cnt)]

            u_all = np.concatenate([u_pos, u_pos, u_pos])
            v_all = np.concatenate([v_pos, neg1_v, neg2_v])
            r_all = np.concatenate([r_pos, r_pos, r_pos])
            labels = np.concatenate([
                np.ones(b_len, dtype=np.float32),
                np.zeros(2 * b_len, dtype=np.float32),
            ])
            # Peso igualado para balancear BCE (1 positivo vs 2 negativos)
            sample_w = np.concatenate([
                np.full(b_len, 1.0, dtype=np.float32),
                np.full(2 * b_len, 0.5, dtype=np.float32),
            ]) / float(2 * b_len)

            uniq, inv = np.unique(np.concatenate([u_all, v_all]), return_inverse=True)
            inv_u = inv[: len(u_all)]
            inv_v = inv[len(u_all) :]

            z_sub, cache = _forward_encoder(features[uniq], w1, b1, w2, b2)
            zu = z_sub[inv_u]
            zv = z_sub[inv_v]
            rr = r_rel[r_all]
            br = b_rel[r_all]
            tau = float(np.exp(log_tau[0]))

            dot_uv = np.sum(zu * rr * zv, axis=1)
            logits = np.clip(tau * dot_uv + br, -25.0, 25.0)
            probs = 1.0 / (1.0 + np.exp(-logits))

            loss = float(np.sum(sample_w * (-(labels * np.log(probs + 1e-7) + (1.0 - labels) * np.log(1.0 - probs + 1e-7)))))
            ep_loss += loss
            n_batches += 1

            # Gradientes exactos BCE + DistMult + L2-norm + MLP
            d_logits = ((probs - labels) * sample_w).astype(np.float32)
            g_log_tau = np.asarray([float(np.sum(d_logits * dot_uv) * tau)], dtype=np.float32)

            g_br = np.zeros_like(b_rel)
            np.add.at(g_br, r_all, d_logits)

            g_rr = np.zeros_like(r_rel)
            np.add.at(g_rr, r_all, (d_logits * tau)[:, None] * (zu * zv))

            d_zu = (d_logits * tau)[:, None] * (rr * zv)
            d_zv = (d_logits * tau)[:, None] * (rr * zu)

            g_z_sub = np.zeros_like(z_sub)
            np.add.at(g_z_sub, inv_u, d_zu)
            np.add.at(g_z_sub, inv_v, d_zv)

            # Paso hacia atrás a través de L2-normalización
            proj_g = np.sum(g_z_sub * cache["z_out"], axis=1, keepdims=True)
            g_u_raw = (g_z_sub - proj_g * cache["z_out"]) / cache["norms"]

            g_w2 = cache["h1"].T @ g_u_raw + weight_decay * w2
            g_b2 = np.sum(g_u_raw, axis=0)
            g_h1 = g_u_raw @ w2.T
            g_z1 = g_h1 * _gelu_grad(cache["z1"])
            g_w1 = cache["x_sub"].T @ g_z1 + weight_decay * w1
            g_b1 = np.sum(g_z1, axis=0)

            grads = [g_w1, g_b1, g_w2, g_b2, g_rr + weight_decay * r_rel, g_br, g_log_tau]
            step_t += 1
            for p_i, (p, g) in enumerate(zip(params, grads, strict=True)):
                g_clip = np.clip(g, -2.0, 2.0)
                m_adam[p_i] = 0.9 * m_adam[p_i] + 0.1 * g_clip
                v_adam[p_i] = 0.999 * v_adam[p_i] + 0.001 * (g_clip * g_clip)
                m_hat = m_adam[p_i] / (1.0 - 0.9 ** step_t)
                v_hat = v_adam[p_i] / (1.0 - 0.999 ** step_t)
                p -= lr_now * m_hat / (np.sqrt(v_hat) + 1e-8)

            log_tau[0] = float(np.clip(log_tau[0], math.log(4.0), math.log(24.0)))

        if ep in (0, 4, 9, 14, epochs - 1):
            print(f"  Época {ep + 1:02d}/{epochs} | BCE={ep_loss / max(1, n_batches):.4f} | tau={math.exp(float(log_tau[0])):.2f}")

    # Embeddings finales del grafo completo en inferencia
    z_full_list: List[np.ndarray] = []
    for s in range(0, n_nodes, 8192):
        z_chunk, _ = _forward_encoder(features[s : s + 8192], w1, b1, w2, b2)
        z_full_list.append(z_chunk)
    z_full = np.vstack(z_full_list).astype(np.float32)
    return z_full, r_rel, b_rel, float(np.exp(float(log_tau[0])))


def _roc_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """ROC-AUC exacto por rango de Mann-Whitney."""
    order = np.argsort(y_score, kind="mergesort")
    y_sorted = y_true[order]
    n_pos = int(np.sum(y_sorted == 1))
    n_neg = int(np.sum(y_sorted == 0))
    if n_pos == 0 or n_neg == 0:
        return 0.5
    ranks = np.arange(1, len(y_sorted) + 1, dtype=np.float64)
    sum_ranks_pos = float(np.sum(ranks[y_sorted == 1]))
    auc = (sum_ranks_pos - n_pos * (n_pos + 1) / 2.0) / float(n_pos * n_neg)
    return float(auc)


def _evaluar_held_out(
    z_full: np.ndarray,
    r_rel: np.ndarray,
    b_rel: np.ndarray,
    tau: float,
    a_train: sp.csr_matrix,
    nodos_raw: Sequence[Tuple[str, str, str, str, float, int]],
    edges_test: np.ndarray,
    all_edge_set: set[Tuple[int, int]],
    rng: np.random.Generator,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Evalúa `LegalGNN` vs baseline estructural Adamic-Adar en aristas held-out nunca vistas."""
    n_nodes = len(nodos_raw)
    sample_n = min(2000, len(edges_test))
    idx_eval = rng.choice(len(edges_test), size=sample_n, replace=False)
    eval_edges = edges_test[idx_eval]

    # Adamic-Adar weight por nodo sobre matriz simétrica binaria de train
    a_bin = (a_train > 0).astype(np.float32)
    deg = np.asarray(a_bin.sum(axis=1)).ravel()
    inv_log = np.where(deg > 1.0, 1.0 / np.log(np.maximum(deg, 2.0)), 0.0).astype(np.float32)

    pools_por_tipo: Dict[str, np.ndarray] = {}
    for nt in {row[2] for row in nodos_raw}:
        pools_por_tipo[nt] = np.asarray([i for i, row in enumerate(nodos_raw) if row[2] == nt], dtype=np.int32)
    node_types = [row[2] for row in nodos_raw]

    gnn_ranks: List[int] = []
    aa_ranks: List[int] = []
    auc_labels: List[int] = []
    gnn_scores_auc: List[float] = []
    aa_scores_auc: List[float] = []

    for u_i, v_i, r_i in eval_edges:
        u = int(u_i)
        v = int(v_i)
        r = int(r_i)
        nt_v = node_types[v]
        pool = pools_por_tipo[nt_v]
        negs: List[int] = []
        intentos = 0
        while len(negs) < 99 and intentos < 600:
            intentos += 1
            cand = int(pool[int(rng.integers(0, len(pool)))]) if intentos < 400 and len(pool) > 10 else int(rng.integers(0, n_nodes))
            if cand != u and cand != v and (u, cand) not in all_edge_set and (cand, u) not in all_edge_set:
                negs.append(cand)
        if len(negs) < 99:
            continue

        cands = np.asarray([v] + negs, dtype=np.int32)
        zu = z_full[u] * r_rel[r]
        sc_gnn = tau * (z_full[cands] @ zu) + float(b_rel[r])
        rank_gnn = int(1 + np.sum(sc_gnn[1:] >= sc_gnn[0]))
        gnn_ranks.append(rank_gnn)

        # Adamic-Adar + Preferential Attachment fallback tie-breaker
        row_u = a_bin.getrow(u)
        u_neigh = row_u.indices
        sc_aa = np.zeros(len(cands), dtype=np.float64)
        if len(u_neigh) > 0:
            u_set = set(u_neigh.tolist())
            for ci, c_id in enumerate(cands):
                c_neigh = a_bin.getrow(int(c_id)).indices
                comunes = u_set.intersection(c_neigh.tolist())
                aa_val = sum(float(inv_log[w]) for w in comunes)
                pa_tie = math.log1p(float(deg[u]) * float(deg[c_id])) * 1e-4
                sc_aa[ci] = aa_val + pa_tie
        rank_aa = int(1 + np.sum(sc_aa[1:] >= sc_aa[0]))
        aa_ranks.append(rank_aa)

        auc_labels.append(1)
        gnn_scores_auc.append(float(sc_gnn[0]))
        aa_scores_auc.append(float(sc_aa[0]))
        auc_labels.append(0)
        gnn_scores_auc.append(float(sc_gnn[1]))
        aa_scores_auc.append(float(sc_aa[1]))

    y_true = np.asarray(auc_labels, dtype=np.int32)
    gnn_arr = np.asarray(gnn_ranks, dtype=np.float64)
    aa_arr = np.asarray(aa_ranks, dtype=np.float64)

    res_gnn = {
        "roc_auc": round(_roc_auc(y_true, np.asarray(gnn_scores_auc, dtype=np.float64)), 4),
        "hits_at_10_pct": round(float(np.mean(gnn_arr <= 10.0) * 100.0), 2),
        "hits_at_20_pct": round(float(np.mean(gnn_arr <= 20.0) * 100.0), 2),
        "mrr": round(float(np.mean(1.0 / gnn_arr)), 4),
        "evaluados": int(len(gnn_ranks)),
    }
    res_aa = {
        "roc_auc": round(_roc_auc(y_true, np.asarray(aa_scores_auc, dtype=np.float64)), 4),
        "hits_at_10_pct": round(float(np.mean(aa_arr <= 10.0) * 100.0), 2),
        "hits_at_20_pct": round(float(np.mean(aa_arr <= 20.0) * 100.0), 2),
        "mrr": round(float(np.mean(1.0 / aa_arr)), 4),
        "evaluados": int(len(aa_ranks)),
    }
    return res_gnn, res_aa


def _construir_csr_completo(n_nodes: int, edges_all: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Construye CSR simétrico ordenado del subgrafo completo para excluir enlaces conocidos."""
    u = edges_all[:, 0]
    v = edges_all[:, 1]
    rows = np.concatenate([u, v])
    cols = np.concatenate([v, u])
    mat = sp.csr_matrix((np.ones(len(rows), dtype=np.int8), (rows, cols)), shape=(n_nodes, n_nodes))
    mat.sum_duplicates()
    mat.sort_indices()
    dtype_idx = np.uint16 if n_nodes < 65535 else np.uint32
    return mat.indptr.astype(np.int32), mat.indices.astype(dtype_idx)


def main() -> int:
    t0 = time.perf_counter()
    rng = np.random.default_rng(42)

    print("1/5 Extrayendo subgrafo sustantivo limpio desde Parquet...")
    nodos_raw, edges_all = _cargar_subgrafo_limpio()
    n_nodes = len(nodos_raw)
    n_edges = len(edges_all)
    print(f"    Nodos núcleo (grado >= 2): {n_nodes:,} | Aristas únicas relacionales: {n_edges:,}")

    perm = rng.permutation(n_edges)
    cut = int(0.85 * n_edges)
    edges_train = edges_all[perm[:cut]]
    edges_test = edges_all[perm[cut:]]
    all_edge_set = {(int(u), int(v)) for u, v, _ in edges_all}
    print(f"    Split estricto -> Train: {len(edges_train):,} | Held-out Test: {len(edges_test):,}")

    print("2/5 Construyendo features multi-escala (Embeddings chilenos + 2-hop R-SAGE + Espectral SVD)...")
    features, a_train = _construir_features_nodos(nodos_raw, edges_train, rng)

    print("3/5 Entrenando LegalGNN Link Predictor (DistMult + tipo/grado negatives)...")
    z_full, r_rel, b_rel, tau = _entrenar_gnn(features, nodos_raw, edges_train, rng)

    print("4/5 Evaluando en held-out 15 % vs Adamic-Adar estructural...")
    res_gnn, res_aa = _evaluar_held_out(z_full, r_rel, b_rel, tau, a_train, nodos_raw, edges_test, all_edge_set, rng)
    print(f"    Adamic-Adar Baseline -> AUC={res_aa['roc_auc']:.4f} | Hits@10={res_aa['hits_at_10_pct']:.2f}% | Hits@20={res_aa['hits_at_20_pct']:.2f}% | MRR={res_aa['mrr']:.4f}")
    print(f"    LegalGNN (Held-Out)  -> AUC={res_gnn['roc_auc']:.4f} | Hits@10={res_gnn['hits_at_10_pct']:.2f}% | Hits@20={res_gnn['hits_at_20_pct']:.2f}% | MRR={res_gnn['mrr']:.4f}")

    print("5/5 Exportando artefacto cuantizado int8 `data/modelos/legal_gnn_v1.npz`...")
    emb_q = np.clip(np.rint(z_full * 127.0), -127.0, 127.0).astype(np.int8)
    edge_indptr, edge_indices = _construir_csr_completo(n_nodes, edges_all)
    nodos_compact = [
        [nid, lbl, nt, area, int(deg), normalizar_juridico(lbl)]
        for nid, lbl, nt, area, _, deg in nodos_raw
    ]
    nodos_bytes = np.frombuffer(json.dumps(nodos_compact, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), dtype=np.uint8)

    modelos_dir = RAIZ / "data" / "modelos"
    modelos_dir.mkdir(parents=True, exist_ok=True)
    out_npz = modelos_dir / "legal_gnn_v1.npz"

    meta = {
        "backend": "legal_gnn_v1",
        "version": "1.0.0",
        "arquitectura": "Relational 2-hop GraphSAGE/APPNP + Spectral SVD + DistMult (int8)",
        "familias_relacion": list(FAMILIAS_RELACION),
        "n_nodos": n_nodes,
        "n_aristas_unicas": n_edges,
        "n_aristas_train": len(edges_train),
        "n_aristas_test_held_out": len(edges_test),
        "dim_embedding": int(z_full.shape[1]),
        "tau": round(tau, 4),
        "baseline_adamic_adar_val": res_aa,
        "legal_gnn_val": res_gnn,
        "tiempo_entrenamiento_s": round(time.perf_counter() - t0, 2),
    }
    meta_bytes = np.frombuffer(json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8"), dtype=np.uint8)

    np.savez_compressed(
        str(out_npz),
        embeddings_q=emb_q,
        rel_weights=r_rel.astype(np.float32),
        rel_bias=b_rel.astype(np.float32),
        tau=np.asarray([tau], dtype=np.float32),
        edge_indptr=edge_indptr,
        edge_indices=edge_indices,
        nodos_utf8=nodos_bytes,
        meta_utf8=meta_bytes,
    )
    size_mb = round(out_npz.stat().st_size / (1024 * 1024), 3)
    meta["peso_artefacto_mb"] = size_mb

    metricas_path = modelos_dir / "metricas_entrenamiento.json"
    metricas_totales: Dict[str, object] = {}
    if metricas_path.is_file():
        metricas_totales = json.loads(metricas_path.read_text(encoding="utf-8"))
    metricas_totales["legal_gnn_v1"] = meta
    metricas_path.write_text(json.dumps(metricas_totales, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"    Artefacto guardado: {out_npz} ({size_mb:.3f} MB) en {meta['tiempo_entrenamiento_s']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
