"""Open Legal Chile — `LegalGNN` Link Predictor sobre `LegalGraphify`.

Motor neuronal 100 % local (*Zero Data Leak*) basado en `numpy` puro sobre embeddings cuantizados
`int8` (`data/modelos/legal_gnn_v1.npz`). Predice concordancias normativas, jurisprudencia e
instituciones estructuralmente esperadas y audita brechas de fundamentación en escritos judiciales.
"""

from __future__ import annotations

import bisect
import json
import math
import pathlib
import re
import threading
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from neural_retriever import normalizar_juridico, resolver_ruta_modelo

DEFAULT_GNN_FILENAME = "legal_gnn_v1.npz"

_CODIGO_SIGLA_CORTO: Dict[str, str] = {
    "civil": "cc",
    "trabajo": "ct",
    "cpc": "cpc",
    "cpp": "cpp",
    "penal": "cp",
    "comercio": "ccom",
    "tributario": "ctrib",
    "aguas": "caguas",
    "mineria": "cmin",
    "constitucion": "cpr",
    "sanitario": "csan",
}

_NOTA_VERIFICACION = (
    "Hipótesis estructural generada por LegalGNN sobre el grafo doctrinal/jurisprudencial. "
    "Verifique siempre el texto literal vigente mediante `cita_texto` en BCN Ley Chile antes de citar."
)


def _sigmoid(x: float) -> float:
    xc = max(-30.0, min(30.0, float(x)))
    return 1.0 / (1.0 + math.exp(-xc))


def _tokens_limpios(texto: str) -> List[str]:
    norm = normalizar_juridico(texto)
    return [t for t in re.findall(r"[a-z0-9]{2,}", norm) if t not in {"de", "la", "el", "en", "del", "art", "articulo"}]


def _clave_dedup_norma(label: str) -> str:
    """Normaliza variantes tipográficas de un mismo artículo para evitar falsos duplicados."""
    n = normalizar_juridico(label)
    n = n.replace("codigo civil", "cc").replace("codigo del trabajo", "ct").replace("codigo de procedimiento civil", "cpc")
    n = n.replace("codigo procesal penal", "cpp").replace("codigo penal", "cp").replace("constitucion politica de la republica", "cpr")
    toks = sorted(re.findall(r"[a-z0-9]+", n))
    return " ".join(toks)


class LegalGNNEngine:
    """Motor de inferencia rápido (< 15 ms) para predicción de enlaces en Derecho chileno."""

    def __init__(self, model_path: Optional[str | pathlib.Path] = None) -> None:
        self.modelo_disponible = False
        self.backend = "unavailable"
        self.metadata: Dict[str, Any] = {}
        self.familias: Tuple[str, ...] = ("norma", "juris", "estruct")

        self._z: Optional[np.ndarray] = None
        self._rel_w: Optional[np.ndarray] = None
        self._rel_b: Optional[np.ndarray] = None
        self._tau: float = 12.0
        self._indptr: Optional[np.ndarray] = None
        self._indices: Optional[np.ndarray] = None

        self._nodos: List[List[Any]] = []
        self._id_to_idx: Dict[str, int] = {}
        self._norm_label_to_idxs: Dict[str, List[int]] = {}
        self._tipo_a_idxs: Dict[str, np.ndarray] = {}

        ruta = pathlib.Path(model_path) if model_path else resolver_ruta_modelo(DEFAULT_GNN_FILENAME)
        if ruta and ruta.is_file():
            self._cargar_npz(ruta)

    def _cargar_npz(self, ruta: pathlib.Path) -> None:
        with np.load(str(ruta), allow_pickle=False) as npz:
            emb_q = np.asarray(npz["embeddings_q"], dtype=np.float32) / 127.0
            norms = np.maximum(np.linalg.norm(emb_q, axis=1, keepdims=True), 1e-6)
            self._z = (emb_q / norms).astype(np.float32)

            self._rel_w = np.asarray(npz["rel_weights"], dtype=np.float32)
            self._rel_b = np.asarray(npz["rel_bias"], dtype=np.float32)
            self._tau = float(np.asarray(npz["tau"], dtype=np.float32).ravel()[0])
            self._indptr = np.asarray(npz["edge_indptr"], dtype=np.int32)
            self._indices = np.asarray(npz["edge_indices"], dtype=np.int32)

            nodos_raw = bytes(npz["nodos_utf8"].tolist()).decode("utf-8")
            self._nodos = json.loads(nodos_raw)
            meta_raw = bytes(npz["meta_utf8"].tolist()).decode("utf-8")
            self.metadata = json.loads(meta_raw)

        fams = self.metadata.get("familias_relacion")
        if isinstance(fams, list) and len(fams) >= 3:
            self.familias = tuple(str(f) for f in fams[:3])

        self._id_to_idx = {}
        self._norm_label_to_idxs = {}
        por_tipo: Dict[str, List[int]] = {}
        for idx, item in enumerate(self._nodos):
            nid = str(item[0])
            ntype = str(item[2])
            lbl_norm = str(item[5]) if len(item) > 5 else normalizar_juridico(str(item[1]))
            self._id_to_idx[nid] = idx
            self._norm_label_to_idxs.setdefault(lbl_norm, []).append(idx)
            por_tipo.setdefault(ntype, []).append(idx)

        self._tipo_a_idxs = {k: np.asarray(v, dtype=np.int32) for k, v in por_tipo.items()}
        self.backend = str(self.metadata.get("backend") or "legal_gnn_v1")
        self.modelo_disponible = True

    def _tiene_arista(self, u: int, v: int) -> bool:
        if self._indptr is None or self._indices is None:
            return False
        ini = int(self._indptr[u])
        fin = int(self._indptr[u + 1])
        if fin <= ini:
            return False
        segmento = self._indices[ini:fin]
        pos = bisect.bisect_left(segmento, v)
        return pos < len(segmento) and int(segmento[pos]) == v

    def _candidatos_norma_id(self, norma: Dict[str, Any]) -> List[str]:
        """Genera IDs canónicos candidatos del grafo para una norma detectada por `citas_legales`."""
        art = str(norma.get("articulo") or "").strip().lower().replace(" ", "_")
        if norma.get("familia") == "codigo":
            obra = str(norma.get("obra") or "")
            sigla = _CODIGO_SIGLA_CORTO.get(obra, obra)
            cands = [f"norma:{sigla}"]
            if art:
                cands = [
                    f"norma:{sigla}:{art}",
                    f"norma_codigo_{obra}_art_{art}",
                    f"norma_art_{art}_{sigla}",
                    f"norma_{sigla}_art_{art}",
                    f"norma:{sigla}",
                ]
            return cands
        num = str(norma.get("numero") or "").strip()
        if not num:
            return []
        cands = [f"norma:ley-{num}", f"norma_ley_{num}"]
        if art:
            cands = [
                f"norma:ley-{num}:{art}",
                f"norma_ley_{num}_art_{art}",
                f"norma:ley-{num}",
                f"norma_ley_{num}",
            ]
        return cands

    def resolver_nodo(self, consulta: str) -> Optional[int]:
        """Resuelve un ID, norma chilena o término doctrinal al nodo más representativo del grafo."""
        if not self.modelo_disponible or not (consulta or "").strip():
            return None
        q_raw = consulta.strip()
        if q_raw in self._id_to_idx:
            return self._id_to_idx[q_raw]

        q_norm = normalizar_juridico(q_raw)
        if q_norm in self._norm_label_to_idxs:
            idxs = self._norm_label_to_idxs[q_norm]
            return max(idxs, key=lambda i: int(self._nodos[i][4]))

        try:
            from citas_legales import detectar_normas

            normas = detectar_normas(q_raw)
        except Exception:  # noqa: BLE001
            normas = []

        for norma in normas:
            for cid in self._candidatos_norma_id(norma):
                if cid in self._id_to_idx:
                    return self._id_to_idx[cid]

        q_toks = set(_tokens_limpios(q_raw))
        if not q_toks:
            return None

        mejor_idx: Optional[int] = None
        mejor_score = 0.0
        for idx, item in enumerate(self._nodos):
            lbl_norm = str(item[5]) if len(item) > 5 else normalizar_juridico(str(item[1]))
            l_toks = set(_tokens_limpios(lbl_norm))
            if not l_toks:
                continue
            inter = len(q_toks & l_toks)
            if inter == 0:
                continue
            jaccard = inter / float(len(q_toks | l_toks))
            deg_bonus = min(0.25, math.log1p(int(item[4])) * 0.03)
            contiene = 0.25 if q_norm in lbl_norm or lbl_norm in q_norm else 0.0
            score = jaccard + contiene + deg_bonus
            if score > mejor_score:
                mejor_score = score
                mejor_idx = idx

        return mejor_idx if mejor_score >= 0.30 else None

    def _scores_para_nodo(self, u_idx: int, rel_idx: int) -> np.ndarray:
        assert self._z is not None and self._rel_w is not None and self._rel_b is not None
        zu = self._z[u_idx] * self._rel_w[rel_idx]
        logits = self._tau * (self._z @ zu) + float(self._rel_b[rel_idx])
        return logits

    def _familia_idx(self, relacion: str) -> List[int]:
        rel = (relacion or "norma").strip().lower()
        if rel == "todas":
            return [0, 1, 2]
        if rel in self.familias:
            return [self.familias.index(rel)]
        if "juris" in rel or "sentencia" in rel:
            return [1]
        if "estruct" in rel or "inst" in rel:
            return [2]
        return [0]

    def predecir_enlaces(
        self,
        nodo_o_consulta: str,
        relacion: str = "norma",
        top_k: int = 10,
        tipos_destino: Optional[Sequence[str]] = None,
        incluir_existentes: bool = False,
    ) -> Dict[str, Any]:
        """Predice top-K enlaces estructurales faltantes o concordancias de alta probabilidad."""
        if not self.modelo_disponible or self._z is None:
            return {
                "modelo_disponible": False,
                "backend": self.backend,
                "consulta": nodo_o_consulta,
                "predicciones": [],
                "error": "Artefacto `legal_gnn_v1.npz` no disponible en `data/modelos/`.",
            }

        u_idx = self.resolver_nodo(nodo_o_consulta)
        if u_idx is None:
            return {
                "modelo_disponible": True,
                "backend": self.backend,
                "consulta": nodo_o_consulta,
                "nodo_origen": None,
                "predicciones": [],
                "nota_verificacion": "No se pudo anclar la consulta a un nodo del subgrafo sustantivo.",
            }

        u_item = self._nodos[u_idx]
        u_clave = _clave_dedup_norma(str(u_item[1]))
        fams = self._familia_idx(relacion)
        k_limite = max(1, min(50, int(top_k)))

        # Máscara opcional por tipos de destino
        cand_mask: Optional[np.ndarray] = None
        if tipos_destino:
            valid_indices: List[np.ndarray] = []
            for t in tipos_destino:
                arr = self._tipo_a_idxs.get(str(t).strip())
                if arr is not None and len(arr) > 0:
                    valid_indices.append(arr)
            if not valid_indices:
                return {
                    "modelo_disponible": True,
                    "backend": self.backend,
                    "consulta": nodo_o_consulta,
                    "nodo_origen": {
                        "id": u_item[0], "label": u_item[1], "node_type": u_item[2], "grado_sustantivo": u_item[4]
                    },
                    "predicciones": [],
                    "nota_verificacion": _NOTA_VERIFICACION,
                }
            cand_mask = np.unique(np.concatenate(valid_indices))

        mejores_por_v: Dict[int, Tuple[float, str]] = {}
        for r_idx in fams:
            logits = self._scores_para_nodo(u_idx, r_idx)
            fam_nombre = self.familias[r_idx]
            if cand_mask is not None:
                sub_scores = logits[cand_mask]
                top_local = np.argsort(sub_scores)[::-1][: k_limite * 4 + 25]
                candidatos = [(int(cand_mask[i]), float(sub_scores[i])) for i in top_local]
            else:
                top_glob = np.argsort(logits)[::-1][: k_limite * 5 + 30]
                candidatos = [(int(i), float(logits[i])) for i in top_glob]

            for v_idx, logit in candidatos:
                if v_idx == u_idx:
                    continue
                if v_idx not in mejores_por_v or logit > mejores_por_v[v_idx][0]:
                    mejores_por_v[v_idx] = (logit, fam_nombre)

        ordenados = sorted(mejores_por_v.items(), key=lambda x: x[1][0], reverse=True)
        salida: List[Dict[str, Any]] = []
        claves_vistas = {u_clave}

        for v_idx, (logit, fam_nombre) in ordenados:
            ya_existe = self._tiene_arista(u_idx, v_idx)
            if ya_existe and not incluir_existentes:
                continue
            v_item = self._nodos[v_idx]
            v_clave = _clave_dedup_norma(str(v_item[1]))
            if v_clave in claves_vistas:
                continue
            claves_vistas.add(v_clave)
            salida.append({
                "id": str(v_item[0]),
                "label": str(v_item[1]),
                "node_type": str(v_item[2]),
                "area": str(v_item[3]),
                "grado_sustantivo": int(v_item[4]),
                "relacion_predicha": fam_nombre,
                "probabilidad": round(_sigmoid(logit), 4),
                "ya_existe": ya_existe,
                "verificacion_requerida": True,
            })
            if len(salida) >= k_limite:
                break

        return {
            "modelo_disponible": True,
            "backend": self.backend,
            "consulta": nodo_o_consulta,
            "relacion": relacion,
            "nodo_origen": {
                "id": str(u_item[0]),
                "label": str(u_item[1]),
                "node_type": str(u_item[2]),
                "area": str(u_item[3]),
                "grado_sustantivo": int(u_item[4]),
            },
            "predicciones": salida,
            "nota_verificacion": _NOTA_VERIFICACION,
        }

    def auditar_brechas_escrito(self, texto: str, top_k: int = 8) -> Dict[str, Any]:
        """Detecta brechas normativas/doctrinales probables respecto a las normas citadas en un texto."""
        if not self.modelo_disponible or self._z is None:
            return {
                "modelo_disponible": False,
                "backend": self.backend,
                "nodos_ancla": [],
                "normas_sugeridas": [],
                "instituciones_sugeridas": [],
                "jurisprudencia_sugerida": [],
                "error": "Artefacto `legal_gnn_v1.npz` no disponible.",
            }

        cuerpo = (texto or "").strip()
        if not cuerpo:
            return {
                "modelo_disponible": True,
                "backend": self.backend,
                "nodos_ancla": [],
                "normas_sugeridas": [],
                "instituciones_sugeridas": [],
                "jurisprudencia_sugerida": [],
                "nota_verificacion": _NOTA_VERIFICACION,
            }

        try:
            from citas_legales import detectar_normas

            normas = detectar_normas(cuerpo)
        except Exception:  # noqa: BLE001
            normas = []

        anclas_idx: List[int] = []
        vistas_idx = set()
        for norma in normas[:8]:
            for cid in self._candidatos_norma_id(norma):
                if cid in self._id_to_idx:
                    idx = self._id_to_idx[cid]
                    if idx not in vistas_idx:
                        vistas_idx.add(idx)
                        anclas_idx.append(idx)
                    break

        if not anclas_idx:
            # Fallback por título/primeros 240 chars si no hay citas formales aún
            res_idx = self.resolver_nodo(cuerpo[:240])
            if res_idx is not None:
                anclas_idx.append(res_idx)
                vistas_idx.add(res_idx)

        if not anclas_idx:
            return {
                "modelo_disponible": True,
                "backend": self.backend,
                "nodos_ancla": [],
                "normas_sugeridas": [],
                "instituciones_sugeridas": [],
                "jurisprudencia_sugerida": [],
                "cobertura_estructural": {"anclas_detectadas": 0},
                "nota_verificacion": _NOTA_VERIFICACION,
            }

        k_lim = max(1, min(25, int(top_k)))
        texto_norm = normalizar_juridico(cuerpo)
        claves_presentes = {_clave_dedup_norma(str(self._nodos[i][1])) for i in anclas_idx}

        # Agregamos el máximo logit entre las anclas del escrito para cada familia
        max_logits_norma = np.full(len(self._nodos), -1e9, dtype=np.float32)
        max_logits_juris = np.full(len(self._nodos), -1e9, dtype=np.float32)
        max_logits_estruct = np.full(len(self._nodos), -1e9, dtype=np.float32)
        for u_idx in anclas_idx:
            max_logits_norma = np.maximum(max_logits_norma, self._scores_para_nodo(u_idx, 0))
            max_logits_juris = np.maximum(max_logits_juris, self._scores_para_nodo(u_idx, 1))
            max_logits_estruct = np.maximum(max_logits_estruct, self._scores_para_nodo(u_idx, 2))

        def _recoger(scores: np.ndarray, tipos: Tuple[str, ...], limite: int) -> List[Dict[str, Any]]:
            cands = [self._tipo_a_idxs[t] for t in tipos if t in self._tipo_a_idxs]
            if not cands:
                return []
            idxs_tipo = np.unique(np.concatenate(cands))
            sub = scores[idxs_tipo]
            orden = np.argsort(sub)[::-1][: limite * 6 + 30]
            out: List[Dict[str, Any]] = []
            for loc_i in orden:
                v_idx = int(idxs_tipo[int(loc_i)])
                if v_idx in vistas_idx:
                    continue
                item = self._nodos[v_idx]
                lbl = str(item[1])
                lbl_norm = str(item[5]) if len(item) > 5 else normalizar_juridico(lbl)
                clave = _clave_dedup_norma(lbl)
                if lbl_norm in texto_norm or clave in claves_presentes:
                    continue
                claves_presentes.add(clave)
                prob = round(_sigmoid(float(sub[int(loc_i)])), 4)
                if prob < 0.55:
                    continue
                out.append({
                    "id": str(item[0]),
                    "label": lbl,
                    "node_type": str(item[2]),
                    "area": str(item[3]),
                    "probabilidad": prob,
                    "verificacion_requerida": True,
                })
                if len(out) >= limite:
                    break
            return out

        normas_sug = _recoger(max_logits_norma, ("norma", "articulo_legal", "cuerpo_legal"), k_lim)
        inst_sug = _recoger(max_logits_estruct, ("institucion", "guia", "obra"), min(5, k_lim))
        juris_sug = _recoger(max_logits_juris, ("sentencia_cs", "jurisprudencia", "jurisprudencia_tc", "sentencia_ta"), min(5, k_lim))

        return {
            "modelo_disponible": True,
            "backend": self.backend,
            "nodos_ancla": [
                {"id": str(self._nodos[i][0]), "label": str(self._nodos[i][1]), "node_type": str(self._nodos[i][2])}
                for i in anclas_idx
            ],
            "normas_sugeridas": normas_sug,
            "instituciones_sugeridas": inst_sug,
            "jurisprudencia_sugerida": juris_sug,
            "cobertura_estructural": {
                "anclas_detectadas": len(anclas_idx),
                "brechas_normativas_sugeridas": len(normas_sug),
                "brechas_institucionales_sugeridas": len(inst_sug),
                "jurisprudencia_sugerida": len(juris_sug),
            },
            "nota_verificacion": _NOTA_VERIFICACION,
        }

    def estado_modelo(self) -> Dict[str, Any]:
        """Retorna el estado técnico y métricas de validación del modelo GNN cargado."""
        return {
            "modelo_disponible": self.modelo_disponible,
            "backend": self.backend,
            "nodos": len(self._nodos),
            "familias_relacion": list(self.familias),
            "metadata": self.metadata,
        }


_LOCK_GNN = threading.RLock()
_GNN_SINGLETON: Optional[LegalGNNEngine] = None


def obtener_motor_gnn() -> LegalGNNEngine:
    """Singleton thread-safe para `LegalGNNEngine` (carga perezosa)."""
    global _GNN_SINGLETON
    with _LOCK_GNN:
        if _GNN_SINGLETON is None:
            _GNN_SINGLETON = LegalGNNEngine()
        return _GNN_SINGLETON


def reiniciar_motor_gnn() -> None:
    """Reinicia la instancia cacheada en memoria (útil tras reentrenar o en pruebas)."""
    global _GNN_SINGLETON
    with _LOCK_GNN:
        _GNN_SINGLETON = None
