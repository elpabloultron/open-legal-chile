"""Script opcional de escalamiento en GPU (PyTorch Geometric) para `LegalGNN` en Chile.

Permite reentrenar `data/modelos/legal_gnn_v1.npz` usando `RGCNConv`/`SAGEConv` en GPU cuando el
equipo dispone de `torch` y `torch_geometric`, exportando exactamente el mismo esquema binario
portable (`allow_pickle=False`) que `scripts/entrenar_gnn_chile.py`. Nunca se importa en runtime.

Uso opcional:
    pip install torch torch-geometric
    python scripts/entrenar_gnn_pyg_gpu.py --epochs 80
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def main() -> int:
    parser = argparse.ArgumentParser(description="Escalamiento opcional PyTorch Geometric para LegalGNN")
    parser.add_argument("--epochs", type=int, default=80, help="Épocas de entrenamiento RGCN en GPU/CPU")
    parser.add_argument("--hidden-dim", type=int, default=128, help="Dimensión oculta RGCN")
    parser.add_argument("--out-dim", type=int, default=64, help="Dimensión final de embeddings de nodos")
    args = parser.parse_args()

    try:
        import numpy as np
        import torch
        import torch.nn as nn
        import torch.nn.functional as F
        from torch_geometric.nn import RGCNConv
    except ImportError as exc:
        print(
            "PyTorch / PyTorch Geometric no está instalado en este entorno.\n"
            "El motor runtime de producción usa `data/modelos/legal_gnn_v1.npz` en NumPy puro.\n"
            "Para entrenar una versión R-GCN en GPU ejecute:\n"
            "  pip install torch torch-geometric && python scripts/entrenar_gnn_pyg_gpu.py\n"
            f"Detalle: {exc}"
        )
        return 0

    from scripts.entrenar_gnn_chile import (
        FAMILIAS_RELACION,
        _cargar_subgrafo_limpio,
        _construir_csr_completo,
        _construir_features_nodos,
    )

    t0 = time.perf_counter()
    rng = np.random.default_rng(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    nodos_raw, edges_all = _cargar_subgrafo_limpio()
    n_nodes = len(nodos_raw)
    perm = rng.permutation(len(edges_all))
    cut = int(0.85 * len(edges_all))
    edges_train = edges_all[perm[:cut]]
    features, _ = _construir_features_nodos(nodos_raw, edges_train, rng)

    class RGCNLinkModel(nn.Module):
        def __init__(self, in_dim: int, hid: int, out_d: int, n_rel: int) -> None:
            super().__init__()
            self.conv1 = RGCNConv(in_dim, hid, n_rel)
            self.conv2 = RGCNConv(hid, out_d, n_rel)
            self.rel_w = nn.Parameter(torch.ones(n_rel, out_d))
            self.rel_b = nn.Parameter(torch.zeros(n_rel))
            self.tau = nn.Parameter(torch.tensor(12.0))

        def encode(self, x: torch.Tensor, edge_index: torch.Tensor, edge_type: torch.Tensor) -> torch.Tensor:
            h = F.gelu(self.conv1(x, edge_index, edge_type))
            h = self.conv2(h, edge_index, edge_type)
            return F.normalize(h, p=2, dim=-1)

    u_t = np.concatenate([edges_train[:, 0], edges_train[:, 1]])
    v_t = np.concatenate([edges_train[:, 1], edges_train[:, 0]])
    r_t = np.concatenate([edges_train[:, 2], edges_train[:, 2]])

    x_t = torch.from_numpy(features).to(device)
    ei_t = torch.from_numpy(np.vstack([u_t, v_t])).long().to(device)
    et_t = torch.from_numpy(r_t).long().to(device)

    model = RGCNLinkModel(features.shape[1], args.hidden_dim, args.out_dim, len(FAMILIAS_RELACION)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-3, weight_decay=1e-4)

    u_pos_t = torch.from_numpy(edges_train[:, 0]).long().to(device)
    v_pos_t = torch.from_numpy(edges_train[:, 1]).long().to(device)
    r_pos_t = torch.from_numpy(edges_train[:, 2]).long().to(device)

    for ep in range(args.epochs):
        model.train()
        opt.zero_grad()
        z = model.encode(x_t, ei_t, et_t)
        v_neg_t = torch.randint(0, n_nodes, v_pos_t.shape, device=device)
        pos_s = torch.sum(z[u_pos_t] * model.rel_w[r_pos_t] * z[v_pos_t], dim=-1) * model.tau + model.rel_b[r_pos_t]
        neg_s = torch.sum(z[u_pos_t] * model.rel_w[r_pos_t] * z[v_neg_t], dim=-1) * model.tau + model.rel_b[r_pos_t]
        loss = F.binary_cross_entropy_with_logits(
            torch.cat([pos_s, neg_s]),
            torch.cat([torch.ones_like(pos_s), torch.zeros_like(neg_s)]),
        )
        loss.backward()
        opt.step()
        if (ep + 1) % 20 == 0:
            print(f"RGCN PyG Ep {ep + 1}/{args.epochs} | loss={float(loss.item()):.4f}")

    model.eval()
    with torch.no_grad():
        z_final = model.encode(x_t, ei_t, et_t).cpu().numpy()
        r_w = model.rel_w.cpu().numpy().astype(np.float32)
        r_b = model.rel_b.cpu().numpy().astype(np.float32)
        tau_val = float(model.tau.cpu().item())

    emb_q = np.clip(np.rint(z_final * 127.0), -127.0, 127.0).astype(np.int8)
    edge_indptr, edge_indices = _construir_csr_completo(n_nodes, edges_all)
    nodos_compact = [[nid, lbl, nt, area, int(deg), lbl.lower()] for nid, lbl, nt, area, _, deg in nodos_raw]
    nodos_bytes = np.frombuffer(json.dumps(nodos_compact, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), dtype=np.uint8)
    meta = {
        "backend": "legal_gnn_pyg_rgcn_v1",
        "version": "1.0.0",
        "arquitectura": "PyTorch Geometric RGCNConv + DistMult (int8)",
        "familias_relacion": list(FAMILIAS_RELACION),
        "n_nodos": n_nodes,
        "n_aristas_unicas": int(len(edges_all)),
        "tiempo_entrenamiento_s": round(time.perf_counter() - t0, 2),
    }
    meta_bytes = np.frombuffer(json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8"), dtype=np.uint8)
    out_npz = RAIZ / "data" / "modelos" / "legal_gnn_v1.npz"
    np.savez_compressed(
        str(out_npz),
        embeddings_q=emb_q,
        rel_weights=r_w,
        rel_bias=r_b,
        tau=np.asarray([tau_val], dtype=np.float32),
        edge_indptr=edge_indptr,
        edge_indices=edge_indices,
        nodos_utf8=nodos_bytes,
        meta_utf8=meta_bytes,
    )
    print(f"Exportado artefacto R-GCN GPU en {out_npz} ({out_npz.stat().st_size / (1024 * 1024):.3f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
