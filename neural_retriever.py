"""Open Legal Chile — Retriever Neuronal Local (Bi-Encoder Contrastivo + Reranker CPU).

Motor 100 % local (*Zero Data Leak*) basado en `numpy` y `onnxruntime` opcional, entrenado
sobre el corpus jurídico chileno (`data/parquet/`). Mantiene compatibilidad de 384 dimensiones
con `vector_engine.py`, degradación honesta sin artefacto y cero impacto en cold start STDIO
mediante carga estrictamente perezosa.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import re
import threading
import unicodedata
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

EMBEDDING_DIM = 384
DEFAULT_MODEL_FILENAME = "chile_embed_v1.npz"

_SINONIMOS_JURIDICOS_CHILE: Tuple[Tuple[str, ...], ...] = (
    ("autodespido", "despido indirecto", "art 171", "art. 171"),
    ("dano moral por rebote", "victima por repercusion", "art 2329", "legitimacion activa"),
    ("precario", "mera tolerancia", "sin previo contrato", "art 2195"),
    ("invalidacion", "art 53", "nulidad de derecho publico", "ley 19880"),
    ("tutela laboral", "derechos fundamentales", "indicios", "art 485"),
    ("necesidades de la empresa", "art 161", "descuento afc", "recargo 30"),
    ("ley karin", "acoso laboral", "acoso sexual", "violencia trabajo", "ley 21643"),
    ("datos personales", "arco", "ley 19628", "ley 21719", "ley 21855", "vacancia"),
    ("delitos economicos", "persona juridica", "prevencion delitos", "ley 21595", "ley 20393"),
    ("recurso de proteccion", "accion cautelar", "acto arbitrario", "art 20 cpr"),
    ("posesion inscrita", "conservador bienes raices", "art 724", "art 728", "art 2505"),
    ("pension alimentos", "alimentos utm", "registro deudores", "ley 14908", "ley 21389"),
)

_STOPWORDS_ES = frozenset({
    "de", "la", "el", "en", "y", "a", "los", "las", "del", "al", "por", "con", "para",
    "un", "una", "unos", "unas", "se", "su", "sus", "que", "es", "son", "o", "lo", "como",
    "mas", "pero", "si", "no", "sin", "sobre", "entre", "ante", "bajo", "desde", "hasta",
    "art", "articulo", "articulos", "inc", "inciso", "num", "numero", "nro", "ley",
})


def normalizar_juridico(texto: str) -> str:
    """Normaliza texto en español preservando dígitos y removiendo diacríticos."""
    nfkd = unicodedata.normalize("NFKD", (texto or "").lower())
    sin_tildes = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sin_tildes).strip()


def extraer_terminos_juridicos(texto: str) -> List[str]:
    """Extrae unigramas, bigramas legales y afijos morfológicos en orden determinista."""
    norm = normalizar_juridico(texto)
    if not norm:
        return []
    palabras = [p for p in re.findall(r"[a-z0-9]{2,}", norm) if p not in _STOPWORDS_ES]
    tokens: List[str] = list(palabras)
    for i in range(len(palabras) - 1):
        tokens.append(f"{palabras[i]}_{palabras[i + 1]}")
    for w in palabras:
        if len(w) >= 5 and not w.isdigit():
            tokens.append(f"@p:{w[:5]}")
            tokens.append(f"@s:{w[-4:]}")
    return tokens


def _gelu(x: np.ndarray) -> np.ndarray:
    return 0.5 * x * (1.0 + np.tanh(math.sqrt(2.0 / math.pi) * (x + 0.044715 * (x ** 3))))


def _sigmoid(x: float) -> float:
    xc = max(-30.0, min(30.0, float(x)))
    return 1.0 / (1.0 + math.exp(-xc))


def _l2_normalize(vec: np.ndarray) -> np.ndarray:
    norma = float(np.linalg.norm(vec))
    if norma > 1e-12:
        return (vec / norma).astype(np.float32)
    return np.zeros_like(vec, dtype=np.float32)


def _hash_tfidf_128(sparse_vec: Dict[int, float], vocab_rev: List[str], dim_lex: int = 128) -> np.ndarray:
    """Proyección determinista TF-IDF dispersa hacia un subespacio compacto (sin peso en disco)."""
    vec = np.zeros(dim_lex, dtype=np.float32)
    for idx, weight in sparse_vec.items():
        tok = vocab_rev[idx] if idx < len(vocab_rev) else str(idx)
        digest = hashlib.md5(tok.encode("utf-8"), usedforsecurity=False).digest()
        b1 = int.from_bytes(digest[:4], "little") % dim_lex
        b2 = int.from_bytes(digest[4:8], "little") % dim_lex
        s1 = 1.0 if (digest[8] & 1) == 0 else -1.0
        s2 = 1.0 if (digest[9] & 1) == 0 else -1.0
        vec[b1] += weight * s1
        vec[b2] += 0.7 * weight * s2
    return _l2_normalize(vec)


def _normas_normalizadas(texto: str) -> set[str]:
    try:
        from citas_legales import detectar_normas
    except Exception:  # noqa: BLE001
        return set()
    encontradas = set()
    for n in detectar_normas(texto or ""):
        fam = str(n.get("familia") or "")
        if fam == "codigo":
            encontradas.add(f"c:{n.get('obra')}:{n.get('articulo', '')}")
        elif fam == "ley":
            encontradas.add(f"l:{n.get('numero')}:{n.get('articulo', '')}")
    return encontradas


def _puntaje_sinonimos(q_norm: str, d_norm: str) -> float:
    hits = 0.0
    for grupo in _SINONIMOS_JURIDICOS_CHILE:
        q_in = any(pat in q_norm for pat in grupo)
        d_in = any(pat in d_norm for pat in grupo)
        if q_in and d_in:
            hits += 1.0
    return min(1.0, hits / 2.0)


def calcular_features_reranker(
    query: str,
    titulo: str,
    texto: str,
    cos_neural: float = 0.0,
    cos_tfidf: float = 0.0,
) -> np.ndarray:
    """Construye el vector de 10 características jurídicas interpretables `(query, documento)`."""
    q_norm = normalizar_juridico(query)
    t_norm = normalizar_juridico(titulo)
    d_norm = normalizar_juridico(f"{titulo} {texto}".strip())

    q_words = [w for w in re.findall(r"[a-z0-9]{3,}", q_norm) if w not in _STOPWORDS_ES]
    d_words_list = re.findall(r"[a-z0-9]{3,}", d_norm)
    d_words = set(d_words_list)
    t_words = set(re.findall(r"[a-z0-9]{3,}", t_norm))

    if q_words:
        cov_unigram = sum(1 for w in q_words if w in d_words) / float(len(q_words))
        title_overlap = sum(1 for w in q_words if w in t_words) / float(len(q_words))
        q_stems = [w[:5] for w in q_words if len(w) >= 5]
        d_stems = {w[:5] for w in d_words if len(w) >= 5}
        stem_overlap = (
            sum(1 for s in q_stems if s in d_stems) / float(len(q_stems))
            if q_stems
            else cov_unigram
        )
    else:
        cov_unigram = 0.0
        title_overlap = 0.0
        stem_overlap = 0.0

    q_bigrams = [f"{q_words[i]}_{q_words[i + 1]}" for i in range(len(q_words) - 1)]
    d_bigrams = {f"{d_words_list[i]}_{d_words_list[i + 1]}" for i in range(len(d_words_list) - 1)}
    cov_bigram = (
        sum(1 for bg in q_bigrams if bg in d_bigrams) / float(len(q_bigrams))
        if q_bigrams
        else cov_unigram
    )

    q_normas = _normas_normalizadas(query)
    d_normas = _normas_normalizadas(f"{titulo} {texto}")
    norm_match = (len(q_normas & d_normas) / float(len(q_normas))) if q_normas else 0.0
    sinonimos = _puntaje_sinonimos(q_norm, d_norm)
    log_len = min(1.0, math.log1p(len(d_norm)) / 8.0)
    norm_density = min(1.0, len(d_normas) / 3.0)

    return np.asarray(
        [
            max(-1.0, min(1.0, float(cos_neural))),
            max(-1.0, min(1.0, float(cos_tfidf))),
            cov_unigram,
            cov_bigram,
            norm_match,
            sinonimos,
            title_overlap,
            log_len,
            norm_density,
            stem_overlap,
        ],
        dtype=np.float32,
    )


def resolver_ruta_modelo(filename: str = DEFAULT_MODEL_FILENAME) -> Optional[pathlib.Path]:
    """Resuelve la ruta al artefacto neuronal empacado o en caché `~/.openlegal/models`."""
    env_dir = os.environ.get("OPENLEGAL_MODELS_DIR", "").strip()
    if env_dir:
        p_env = pathlib.Path(env_dir) / filename
        if p_env.is_file():
            return p_env

    cache_p = pathlib.Path.home() / ".openlegal" / "models" / filename
    if cache_p.is_file():
        return cache_p

    from recursos import ruta_recurso

    bundled = ruta_recurso(f"data/modelos/{filename}")
    if bundled.is_file():
        return bundled
    return None


class ChileNeuralEmbedder:
    """Bi-Encoder neuronal chileno (384-dim) con soporte ONNX opcional y pesos locales NPZ."""

    def __init__(self, model_path: Optional[str | pathlib.Path] = None) -> None:
        self.dim = EMBEDDING_DIM
        self.backend = "unavailable"
        self.modelo_disponible = False
        self.metadata: Dict[str, Any] = {}

        self._vocab_list: List[str] = []
        self._vocab: Dict[str, int] = {}
        self._idf: Optional[np.ndarray] = None
        self._svd_proj: Optional[np.ndarray] = None
        self._w_res: Optional[np.ndarray] = None
        self._b_res: Optional[np.ndarray] = None
        self._w1: Optional[np.ndarray] = None
        self._b1: Optional[np.ndarray] = None
        self._w2: Optional[np.ndarray] = None
        self._b2: Optional[np.ndarray] = None
        self._peso_semantico: float = 0.65
        self._peso_lexico: float = 0.75

        self._rr_mean: Optional[np.ndarray] = None
        self._rr_std: Optional[np.ndarray] = None
        self._rr_w1: Optional[np.ndarray] = None
        self._rr_b1: Optional[np.ndarray] = None
        self._rr_w2: Optional[np.ndarray] = None
        self._rr_b2: Optional[np.ndarray] = None

        self._onnx_session: Any = None
        self._onnx_tokenizer: Any = None

        if self._intentar_cargar_onnx_externo():
            return

        ruta = pathlib.Path(model_path) if model_path else resolver_ruta_modelo(DEFAULT_MODEL_FILENAME)
        if ruta and ruta.is_file():
            self._cargar_npz(ruta)

    def _intentar_cargar_onnx_externo(self) -> bool:
        onnx_dir = os.environ.get("OPENLEGAL_ONNX_EMBED_DIR", "").strip()
        if not onnx_dir:
            cand = pathlib.Path.home() / ".openlegal" / "models" / "embed_onnx"
            if cand.is_dir():
                onnx_dir = str(cand)
        if not onnx_dir:
            return False
        base = pathlib.Path(onnx_dir)
        model_file = base / "model_quantized.onnx"
        if not model_file.is_file():
            model_file = base / "model.onnx"
        tok_file = base / "tokenizer.json"
        if not model_file.is_file() or not tok_file.is_file():
            return False
        try:
            import onnxruntime as ort
            from tokenizers import Tokenizer

            self._onnx_tokenizer = Tokenizer.from_file(str(tok_file))
            self._onnx_tokenizer.enable_truncation(max_length=256)
            self._onnx_session = ort.InferenceSession(str(model_file), providers=["CPUExecutionProvider"])
            self.backend = f"chile_onnx:{model_file.name}"
            self.modelo_disponible = True
            return True
        except Exception:  # noqa: BLE001 — fallback transparente al artefacto NPZ
            self._onnx_session = None
            self._onnx_tokenizer = None
            return False

    def _cargar_npz(self, ruta: pathlib.Path) -> None:
        with np.load(str(ruta), allow_pickle=False) as npz:
            vocab_json = bytes(npz["vocab_utf8"].tolist()).decode("utf-8")
            vocab_list: List[str] = json.loads(vocab_json)
            self._vocab_list = vocab_list
            self._vocab = {tok: idx for idx, tok in enumerate(vocab_list)}
            meta_json = bytes(npz["meta_utf8"].tolist()).decode("utf-8")
            self.metadata = json.loads(meta_json)

            self._idf = np.asarray(npz["idf"], dtype=np.float32)
            self._svd_proj = np.asarray(npz["svd_proj"], dtype=np.float32)
            self._w_res = np.asarray(npz["w_res"], dtype=np.float32)
            self._b_res = np.asarray(npz["b_res"], dtype=np.float32)
            self._w1 = np.asarray(npz["w1"], dtype=np.float32)
            self._b1 = np.asarray(npz["b1"], dtype=np.float32)
            self._w2 = np.asarray(npz["w2"], dtype=np.float32)
            self._b2 = np.asarray(npz["b2"], dtype=np.float32)
            self._peso_semantico = float(self.metadata.get("peso_semantico", 0.65))
            self._peso_lexico = float(self.metadata.get("peso_lexico", 0.75))

            self._rr_mean = np.asarray(npz["rr_mean"], dtype=np.float32)
            self._rr_std = np.asarray(npz["rr_std"], dtype=np.float32)
            self._rr_w1 = np.asarray(npz["rr_w1"], dtype=np.float32)
            self._rr_b1 = np.asarray(npz["rr_b1"], dtype=np.float32)
            self._rr_w2 = np.asarray(npz["rr_w2"], dtype=np.float32)
            self._rr_b2 = np.asarray(npz["rr_b2"], dtype=np.float32)

        sem_dim = int(self._w2.shape[1]) if self._w2 is not None else 256
        lex_dim = int(self.metadata.get("lex_dim", EMBEDDING_DIM - sem_dim))
        self.dim = sem_dim + lex_dim
        self.backend = str(self.metadata.get("backend") or "chile_neural_embed_v1")
        self.modelo_disponible = True

    def tfidf_vector_disperso(self, texto: str) -> Dict[int, float]:
        """Calcula pesos TF-IDF L2-normalizados en el vocabulario jurídico."""
        if not self._vocab or self._idf is None:
            return {}
        tf: Dict[int, float] = {}
        for tok in extraer_terminos_juridicos(texto):
            idx = self._vocab.get(tok)
            if idx is not None:
                tf[idx] = tf.get(idx, 0.0) + 1.0
        if not tf:
            return {}
        ponderados: Dict[int, float] = {}
        norm_sq = 0.0
        for idx, count in tf.items():
            w = (1.0 + math.log(count)) * float(self._idf[idx])
            ponderados[idx] = w
            norm_sq += w * w
        if norm_sq <= 1e-12:
            return {}
        inv_norm = 1.0 / math.sqrt(norm_sq)
        for idx in ponderados:
            ponderados[idx] *= inv_norm
        return ponderados

    def similitud_tfidf(self, texto_a: str, texto_b: str) -> float:
        """Similitud coseno TF-IDF exacta entre dos textos en vocabulario legal chileno."""
        va = self.tfidf_vector_disperso(texto_a)
        vb = self.tfidf_vector_disperso(texto_b)
        if not va or not vb:
            return 0.0
        if len(va) > len(vb):
            va, vb = vb, va
        return float(sum(w * vb[idx] for idx, w in va.items() if idx in vb))

    def encode(self, texto: str) -> np.ndarray:
        """Codifica un texto jurídico chileno en vector unitario L2 de dimensión 384."""
        if not texto or not texto.strip() or not self.modelo_disponible:
            return np.zeros(self.dim, dtype=np.float32)

        if self._onnx_session is not None and self._onnx_tokenizer is not None:
            try:
                enc = self._onnx_tokenizer.encode(texto.strip())
                ids = np.asarray([enc.ids], dtype=np.int64)
                mask = np.asarray([enc.attention_mask], dtype=np.int64)
                feeds = {"input_ids": ids, "attention_mask": mask}
                if any(i.name == "token_type_ids" for i in self._onnx_session.get_inputs()):
                    feeds["token_type_ids"] = np.zeros_like(ids, dtype=np.int64)
                out = self._onnx_session.run(None, feeds)[0]
                if out.ndim == 3:
                    m_exp = mask[:, :, None].astype(np.float32)
                    pooled = (out * m_exp).sum(axis=1) / np.maximum(m_exp.sum(axis=1), 1e-6)
                    vec_onnx = pooled[0]
                else:
                    vec_onnx = out[0]
                return _l2_normalize(vec_onnx.astype(np.float32))
            except Exception:  # noqa: BLE001
                return np.zeros(self.dim, dtype=np.float32)

        if (
            self._svd_proj is None
            or self._w_res is None
            or self._b_res is None
            or self._w1 is None
            or self._b1 is None
            or self._w2 is None
            or self._b2 is None
        ):
            return np.zeros(self.dim, dtype=np.float32)

        sparse_vec = self.tfidf_vector_disperso(texto)
        if not sparse_vec:
            return np.zeros(self.dim, dtype=np.float32)

        k_dim = self._svd_proj.shape[1]
        z = np.zeros(k_dim, dtype=np.float32)
        for idx, weight in sparse_vec.items():
            z += weight * self._svd_proj[idx]
        z = _l2_normalize(z)

        h = _gelu(z @ self._w1 + self._b1)
        out_sem = _l2_normalize((z @ self._w_res + self._b_res) + (h @ self._w2 + self._b2))
        lex_dim = max(0, self.dim - out_sem.shape[0])
        if lex_dim > 0:
            out_lex = _hash_tfidf_128(sparse_vec, self._vocab_list, dim_lex=lex_dim)
            combinado = np.concatenate([self._peso_semantico * out_sem, self._peso_lexico * out_lex])
            return _l2_normalize(combinado)
        return out_sem

    def encode_batch(self, textos: Sequence[str]) -> np.ndarray:
        """Codifica un lote de textos en matriz `(N, dim)` L2-normalizada."""
        if not textos:
            return np.empty((0, self.dim), dtype=np.float32)
        return np.vstack([self.encode(t) for t in textos]).astype(np.float32)

    def rerank_weights(self) -> Optional[Tuple[np.ndarray, ...]]:
        """Devuelve los pesos entrenados del MLP reranker si están disponibles."""
        if (
            self._rr_mean is None
            or self._rr_std is None
            or self._rr_w1 is None
            or self._rr_b1 is None
            or self._rr_w2 is None
            or self._rr_b2 is None
        ):
            return None
        return (self._rr_mean, self._rr_std, self._rr_w1, self._rr_b1, self._rr_w2, self._rr_b2)


class ChileNeuralReranker:
    """Reranker neuronal pairwise entrenado para precisión jurídica chilena Top-K."""

    def __init__(self, embedder: Optional[ChileNeuralEmbedder] = None) -> None:
        self.embedder = embedder or obtener_embedder_chileno()
        self.modelo_disponible = self.embedder.rerank_weights() is not None
        self.backend = (
            f"chile_reranker_v1+{self.embedder.backend}"
            if self.modelo_disponible
            else "heuristic_fallback"
        )

    def score(self, query: str, titulo: str, texto: str, cos_neural: Optional[float] = None) -> float:
        """Retorna probabilidad de relevancia en `[0.0, 1.0]` para el par `(query, candidato)`."""
        if not (query or "").strip() or not f"{titulo} {texto}".strip():
            return 0.0

        c_neural = cos_neural
        if c_neural is None:
            if self.embedder.modelo_disponible:
                qv = self.embedder.encode(query)
                dv = self.embedder.encode(f"{titulo}. {texto[:800]}".strip())
                c_neural = float(np.dot(qv, dv))
            else:
                c_neural = 0.0
        c_tfidf = self.embedder.similitud_tfidf(query, f"{titulo}. {texto[:1200]}") if self.embedder.modelo_disponible else 0.0
        feats = calcular_features_reranker(query, titulo, texto, cos_neural=c_neural, cos_tfidf=c_tfidf)

        weights = self.embedder.rerank_weights()
        if weights is None:
            # Fallback lineal interpretable si el artefacto aún no existe
            raw = 0.35 * feats[0] + 0.25 * feats[2] + 0.20 * feats[4] + 0.15 * feats[5] + 0.05 * feats[6]
            return round(max(0.0, min(1.0, float(raw))), 6)

        mean, std, w1, b1, w2, b2 = weights
        x_norm = (feats - mean) / np.maximum(std, 1e-6)
        h = np.maximum(0.0, x_norm @ w1 + b1)
        logit = float((h @ w2 + b2).item())
        return round(_sigmoid(logit), 6)

    def rerank(
        self,
        query: str,
        candidatos: List[Dict[str, Any]],
        *,
        title_key: str = "etiqueta_bcn",
        text_key: str = "texto",
        top_k: Optional[int] = None,
        peso_neuronal: float = 0.65,
    ) -> List[Dict[str, Any]]:
        """Reordena candidatos combinando score previo normalizado y puntaje neuronal."""
        if len(candidatos) <= 1 or not (query or "").strip():
            return candidatos[:top_k] if top_k else list(candidatos)

        qv = self.embedder.encode(query) if self.embedder.modelo_disponible else None
        crudos: List[Tuple[float, int, Dict[str, Any]]] = []
        n_total = float(len(candidatos))

        for pos, item in enumerate(candidatos):
            copia = dict(item)
            titulo = str(
                copia.get(title_key)
                or copia.get("institucion")
                or copia.get("titulo")
                or copia.get("label")
                or ""
            )
            texto = str(
                copia.get(text_key)
                or copia.get("definicion")
                or copia.get("snippet")
                or copia.get("operativa_procesal")
                or ""
            )
            cos_n: Optional[float] = None
            if qv is not None and self.embedder.modelo_disponible:
                dv = self.embedder.encode(f"{titulo}. {texto[:800]}".strip())
                cos_n = float(np.dot(qv, dv))
            sc_rr = self.score(query, titulo, texto, cos_neural=cos_n)
            copia["puntaje_reranker"] = sc_rr
            copia["motor_reranker"] = self.backend
            crudos.append((sc_rr, pos, copia))

        sc_vals = [x[0] for x in crudos]
        sc_min = min(sc_vals)
        sc_span = max(sc_vals) - sc_min
        evaluados: List[Tuple[float, int, Dict[str, Any]]] = []
        for sc_rr, pos, copia in crudos:
            sc_rel = ((sc_rr - sc_min) / sc_span) if sc_span > 1e-6 else sc_rr
            prior = 1.0 - (pos / max(1.0, n_total))
            combinado = peso_neuronal * (0.5 * sc_rr + 0.5 * sc_rel) + (1.0 - peso_neuronal) * prior
            evaluados.append((combinado, -pos, copia))

        evaluados.sort(key=lambda x: (x[0], x[1]), reverse=True)
        ordenados = [x[2] for x in evaluados]
        return ordenados[:top_k] if top_k else ordenados


_LOCK_NEURAL = threading.RLock()
_EMBEDDER_SINGLETON: Optional[ChileNeuralEmbedder] = None
_RERANKER_SINGLETON: Optional[ChileNeuralReranker] = None


def obtener_embedder_chileno() -> ChileNeuralEmbedder:
    """Singleton thread-safe del bi-encoder chileno (carga perezosa)."""
    global _EMBEDDER_SINGLETON
    with _LOCK_NEURAL:
        if _EMBEDDER_SINGLETON is None:
            _EMBEDDER_SINGLETON = ChileNeuralEmbedder()
        return _EMBEDDER_SINGLETON


def obtener_reranker_chileno() -> ChileNeuralReranker:
    """Singleton thread-safe del reranker neuronal chileno."""
    global _RERANKER_SINGLETON
    embedder = obtener_embedder_chileno()
    with _LOCK_NEURAL:
        if _RERANKER_SINGLETON is None:
            _RERANKER_SINGLETON = ChileNeuralReranker(embedder=embedder)
        return _RERANKER_SINGLETON


def reiniciar_modelos_neurales() -> None:
    """Reinicia singletons en memoria (útil en pruebas o tras reentrenar)."""
    global _EMBEDDER_SINGLETON, _RERANKER_SINGLETON
    with _LOCK_NEURAL:
        _EMBEDDER_SINGLETON = None
        _RERANKER_SINGLETON = None
