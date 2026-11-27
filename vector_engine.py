"""
Open Legal Chile — Motor Vectorial Local Integrado (vector_engine.py)
Indexa vectorialmente los 9 Códigos de la República y la Constitución Política de la República (CPR).
Ejecuta búsquedas densas por similitud coseno (vía NumPy/ONNX) y búsquedas léxicas (FTS5 BM25),
fusionándolas mediante Reciprocal Rank Fusion (RRF).
100 % Local, Zero Data Leak, $0 costo de inferencia.
"""

from __future__ import annotations

import os
import re
import json
import sqlite3
import hashlib
import unicodedata
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_DB_PATH = os.path.join(BASE_DIR, "codigos_vectorial.db")
BCN_CACHE_DIR = os.path.join(BASE_DIR, "bcn_cache")

EMBEDDING_DIM = 384

# Códigos canónicos chilenos
CODIGOS_INDEXABLES = {
    "civil": {"idNorma": 172986, "nombre": "Código Civil"},
    "trabajo": {"idNorma": 207436, "nombre": "Código del Trabajo"},
    "cpc": {"idNorma": 22740, "nombre": "Código de Procedimiento Civil"},
    "cpp": {"idNorma": 176595, "nombre": "Código Procesal Penal"},
    "penal": {"idNorma": 1984, "nombre": "Código Penal"},
    "comercio": {"idNorma": 1974, "nombre": "Código de Comercio"},
    "tributario": {"idNorma": 6368, "nombre": "Código Tributario"},
    "aguas": {"idNorma": 5605, "nombre": "Código de Aguas"},
    "mineria": {"idNorma": 29668, "nombre": "Código de Minería"},
    "constitucion": {"idNorma": 242302, "nombre": "Constitución Política de la República"},
}


def _normalizar_texto(texto: str) -> str:
    """Normaliza texto removiendo diacríticos y puntuación excesiva."""
    nfkd = unicodedata.normalize("NFKD", (texto or "").lower())
    sin_tildes = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sin_tildes).strip()


def is_fastembed_available() -> bool:
    """Indica si `fastembed` (ONNX CPU multilingüe sin PyTorch) está instalado."""
    try:
        import fastembed  # noqa: F401
        return True
    except ImportError:
        return False


def is_sqlite_vec_available() -> bool:
    """Indica si la extensión nativa `sqlite-vec` (`vec0`) está instalada."""
    try:
        import sqlite_vec  # noqa: F401
        return True
    except ImportError:
        return False


def _cargar_sqlite_vec(con: sqlite3.Connection) -> bool:
    """Carga `sqlite-vec` en una conexión SQLite si la extensión y `enable_load_extension` existen."""
    if not hasattr(con, "enable_load_extension"):
        return False
    try:
        import sqlite_vec
        con.enable_load_extension(True)
        sqlite_vec.load(con)
        con.enable_load_extension(False)
        return True
    except Exception:  # noqa: BLE001 — fallback transparente a NumPy
        return False


class SemanticEmbeddingEngine:
    """
    Motor local de embeddings para textos jurídicos chilenos (100 % CPU, sin PyTorch).

    Soporta dos backends explícitos:
    1. `fastembed` (ONNX multilingüe real, `intfloat/multilingual-e5-small`, 384-dim):
       se activa cuando `use_fastembed=True` o `OPENLEGAL_NEURAL_EMBEDDINGS=1` y el extra
       `fastembed` está instalado.
    2. `lexical_random_projection`: proyección ortogonal determinista de palabras + 3-gramas
       (cero descargas de modelos, ideal para entornos 100 % air-gapped y pruebas rápidas).
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        use_fastembed: Optional[bool] = None,
        fastembed_model: str = "intfloat/multilingual-e5-small",
        use_chile_neural: Optional[bool] = None,
    ):
        self.session = None
        self.dim = EMBEDDING_DIM
        self._rng = np.random.default_rng(seed=42)
        self._proj_cache: Dict[str, np.ndarray] = {}
        self._fastembed_model_name = fastembed_model
        self._fastembed_instance: Optional[Any] = None
        self._chile_neural: Optional[Any] = None
        self.backend = "lexical_random_projection"

        env_raw = os.environ.get("OPENLEGAL_NEURAL_EMBEDDINGS", "").strip().lower()
        env_neural = env_raw in ("1", "true", "yes")
        env_disabled = env_raw in ("0", "false", "no")
        wants_fastembed = env_neural if use_fastembed is None else bool(use_fastembed)

        if wants_fastembed and is_fastembed_available():
            try:
                from fastembed import TextEmbedding
                self._fastembed_instance = TextEmbedding(model_name=fastembed_model)
                self.backend = f"fastembed:{fastembed_model}"
            except Exception:  # noqa: BLE001 — degradación limpia si no hay modelo cacheado ni red
                self._fastembed_instance = None

        if self._fastembed_instance is None and model_path and os.path.exists(model_path):
            try:
                import onnxruntime as ort
                self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
                self.backend = f"onnx:{os.path.basename(model_path)}"
            except Exception:  # noqa: BLE001
                self.session = None

        wants_chile = (not env_disabled) if use_chile_neural is None else bool(use_chile_neural)
        if self._fastembed_instance is None and self.session is None and wants_chile:
            try:
                from neural_retriever import obtener_embedder_chileno

                eng_cl = obtener_embedder_chileno()
                if eng_cl.modelo_disponible:
                    self._chile_neural = eng_cl
                    self.dim = int(eng_cl.dim)
                    self.backend = eng_cl.backend
            except Exception:  # noqa: BLE001 — degradación transparente al fallback léxico
                self._chile_neural = None

    def encode(self, texto: str) -> np.ndarray:
        """Genera un vector unitario normalizado de dimensión EMBEDDING_DIM."""
        if not texto or not texto.strip():
            return np.zeros(self.dim, dtype=np.float32)

        # 1. Backend neuronal multilingüe real vía FastEmbed (ONNX Runtime CPU)
        if self._fastembed_instance is not None:
            try:
                vec_raw = next(iter(self._fastembed_instance.embed([texto.strip()])))
                vec_np = np.asarray(vec_raw, dtype=np.float32)
                norma = float(np.linalg.norm(vec_np))
                if norma > 0:
                    vec_np = vec_np / norma
                self.dim = int(vec_np.shape[0])
                return vec_np
            except Exception:  # noqa: BLE001
                pass

        # 1b. Backend neuronal chileno local (TF-IDF + SVD + InfoNCE CPU)
        if self._chile_neural is not None:
            try:
                vec_cl = np.asarray(self._chile_neural.encode(texto), dtype=np.float32)
                if vec_cl.shape[0] == self.dim and float(np.linalg.norm(vec_cl)) > 0:
                    return vec_cl
            except Exception:  # noqa: BLE001
                pass

        norm_txt = _normalizar_texto(texto)
        if not norm_txt:
            return np.zeros(self.dim, dtype=np.float32)

        # 2. Fallback determinista 100 % offline basado en palabras y 3-gramas de caracteres
        palabras = [p for p in re.split(r"[^\w]+", norm_txt) if len(p) >= 2]
        vec = np.zeros(self.dim, dtype=np.float32)

        for w in palabras:
            h = int(hashlib.md5(w.encode("utf-8"), usedforsecurity=False).hexdigest()[:8], 16)
            rng_word = np.random.default_rng(h)
            indices = rng_word.integers(0, self.dim, size=12)
            valores = rng_word.choice([-1.0, 1.0], size=12)
            for idx, val in zip(indices, valores, strict=True):
                vec[idx] += val

            for i in range(len(w) - 2):
                tri = w[i:i+3]
                h_tri = int(hashlib.md5(tri.encode("utf-8"), usedforsecurity=False).hexdigest()[:8], 16)
                rng_tri = np.random.default_rng(h_tri)
                indices_tri = rng_tri.integers(0, self.dim, size=4)
                valores_tri = rng_tri.choice([-0.5, 0.5], size=4)
                for idx, val in zip(indices_tri, valores_tri, strict=True):
                    vec[idx] += val

        norma_lex = float(np.linalg.norm(vec))
        if norma_lex > 0:
            vec /= norma_lex
        return vec.astype(np.float32)

    def encode_batch(self, textos: List[str]) -> np.ndarray:
        """Codifica un lote de textos a una matriz NumPy (N, dim)."""
        if self._fastembed_instance is not None and textos:
            try:
                vecs = [np.asarray(v, dtype=np.float32) for v in self._fastembed_instance.embed(textos)]
                mat = np.vstack(vecs)
                normas = np.linalg.norm(mat, axis=1, keepdims=True)
                normas[normas == 0] = 1.0
                return (mat / normas).astype(np.float32)
            except Exception:  # noqa: BLE001
                pass
        if self._chile_neural is not None and textos:
            try:
                return np.asarray(self._chile_neural.encode_batch(textos), dtype=np.float32)
            except Exception:  # noqa: BLE001
                pass
        return np.vstack([self.encode(t) for t in textos])


def init_vector_db(db_path: str = VECTOR_DB_PATH) -> sqlite3.Connection:
    """Inicializa la base de datos SQLite para vectores y FTS5."""
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS articulos_vectorial (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cuerpo_legal TEXT NOT NULL,
        articulo_id TEXT NOT NULL,
        etiqueta_bcn TEXT NOT NULL,
        texto TEXT NOT NULL,
        vector BLOB NOT NULL,
        dimension INTEGER NOT NULL
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_vec_cuerpo ON articulos_vectorial(cuerpo_legal);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_vec_art ON articulos_vectorial(articulo_id);")

    # Tabla FTS5 para búsqueda léxica
    cur.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS articulos_fts USING fts5(
        cuerpo_legal UNINDEXED,
        articulo_id UNINDEXED,
        etiqueta_bcn,
        texto,
        tokenize='unicode61'
    );
    """)

    # Tabla virtual sqlite-vec (vec0) opcional para KNN nativo en disco
    if _cargar_sqlite_vec(con):
        try:
            cur.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS articulos_vec0 USING vec0(
                articulo_rowid INTEGER PRIMARY KEY,
                embedding float[{EMBEDDING_DIM}] distance_metric=cosine
            );
            """)
        except sqlite3.OperationalError:
            pass

    con.commit()
    return con


class VectorLegalEngine:
    """Motor de búsqueda híbrida (Dense Vectorial + Sparse BM25) para los Códigos y CPR."""

    def __init__(self, db_path: str = VECTOR_DB_PATH, use_fastembed: Optional[bool] = None):
        self.db_path = db_path
        self.embedder = SemanticEmbeddingEngine(use_fastembed=use_fastembed)
        con_init = init_vector_db(self.db_path)
        self.usa_sqlite_vec = _cargar_sqlite_vec(con_init)
        con_init.close()
        self._cached_matrix: Optional[np.ndarray] = None
        self._cached_metadata: Optional[List[Dict[str, Any]]] = None

    def _conectar(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        if self.usa_sqlite_vec:
            _cargar_sqlite_vec(con)
        return con

    def total_articulos_indexados(self) -> int:
        """Devuelve el total de artículos en la base vectorial."""
        with self._conectar() as con:
            fila = con.execute("SELECT COUNT(*) FROM articulos_vectorial;").fetchone()
            return int(fila[0]) if fila else 0

    def indexar_cuerpo_legal(self, cuerpo_legal: str, articulos: Dict[str, str],
                             nombre_cuerpo: str, forzar: bool = False) -> int:
        """Indexa vectorialmente y en FTS5 los artículos de un cuerpo legal."""
        con = self._conectar()
        try:
            if not forzar:
                existe = con.execute("SELECT COUNT(*) FROM articulos_vectorial WHERE cuerpo_legal = ?",
                                     (cuerpo_legal,)).fetchone()[0]
                if existe > 0:
                    return existe

            # Eliminar previos si es forzado
            con.execute("DELETE FROM articulos_vectorial WHERE cuerpo_legal = ?", (cuerpo_legal,))
            con.execute("DELETE FROM articulos_fts WHERE cuerpo_legal = ?", (cuerpo_legal,))

            filas_vec = []
            filas_fts = []

            for art_id, texto in articulos.items():
                if not texto or not str(texto).strip():
                    continue
                texto_str = str(texto).strip()
                etiqueta = f"[BCN - {nombre_cuerpo}, Art. {art_id}]"
                vec = self.embedder.encode(f"{etiqueta}\n{texto_str}")
                filas_vec.append((cuerpo_legal, str(art_id), etiqueta, texto_str, vec.tobytes(), len(vec)))
                filas_fts.append((cuerpo_legal, str(art_id), etiqueta, texto_str))

            con.executemany("""
            INSERT INTO articulos_vectorial (cuerpo_legal, articulo_id, etiqueta_bcn, texto, vector, dimension)
            VALUES (?, ?, ?, ?, ?, ?);
            """, filas_vec)

            con.executemany("""
            INSERT INTO articulos_fts (cuerpo_legal, articulo_id, etiqueta_bcn, texto)
            VALUES (?, ?, ?, ?);
            """, filas_fts)

            # Sincronizar tabla vec0 nativa si sqlite-vec está activo
            if self.usa_sqlite_vec:
                try:
                    ids_filas = con.execute(
                        "SELECT id, vector FROM articulos_vectorial WHERE cuerpo_legal = ?;",
                        (cuerpo_legal,),
                    ).fetchall()
                    for rid, _ in ids_filas:
                        con.execute("DELETE FROM articulos_vec0 WHERE articulo_rowid = ?;", (rid,))
                    con.executemany(
                        "INSERT INTO articulos_vec0 (articulo_rowid, embedding) VALUES (?, ?);",
                        ids_filas,
                    )
                except sqlite3.OperationalError:
                    pass

            con.commit()
            self._cached_matrix = None
            self._cached_metadata = None
            return len(filas_vec)
        finally:
            con.close()

    def indexar_desde_bcn_cache(self, forzar: bool = False) -> Dict[str, int]:
        """Indexa todos los Códigos y CPR presentes en bcn_cache/."""
        from bcn_connector import CODIGOS_REPUBLICA, reconstruir_articulos_si_antiguo

        resumen = {}
        for clave, meta in CODIGOS_REPUBLICA.items():
            id_norma = meta["idNorma"]
            posibles_archivos = [
                os.path.join(BCN_CACHE_DIR, f"norma_p2_{id_norma}.json"),
                os.path.join(BCN_CACHE_DIR, f"norma_{id_norma}.json"),
            ]
            articulos = {}
            for ruta in posibles_archivos:
                if os.path.exists(ruta):
                    try:
                        with open(ruta, "r", encoding="utf-8") as f:
                            data = reconstruir_articulos_si_antiguo(json.load(f))
                            if data.get("articulos"):
                                articulos = data["articulos"]
                                break
                    except Exception:
                        pass
            if articulos:
                total = self.indexar_cuerpo_legal(clave, articulos, str(meta["nombre"]), forzar=forzar)
                resumen[clave] = total
        return resumen

    def _cargar_matriz_en_memoria(self, cuerpo_legal: Optional[str] = None) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """Carga en RAM los vectores como matriz NumPy para producto punto ultrarrápido."""
        con = self._conectar()
        try:
            if cuerpo_legal:
                cur = con.execute("""
                SELECT id, cuerpo_legal, articulo_id, etiqueta_bcn, texto, vector
                FROM articulos_vectorial WHERE cuerpo_legal = ?;
                """, (cuerpo_legal,))
            else:
                cur = con.execute("""
                SELECT id, cuerpo_legal, articulo_id, etiqueta_bcn, texto, vector
                FROM articulos_vectorial;
                """)
            filas = cur.fetchall()
            if not filas:
                return np.empty((0, self.embedder.dim), dtype=np.float32), []

            vectores = []
            metadatos = []
            for row in filas:
                vec = np.frombuffer(row[5], dtype=np.float32)
                vectores.append(vec)
                metadatos.append({
                    "id": row[0],
                    "cuerpo_legal": row[1],
                    "articulo_id": row[2],
                    "etiqueta_bcn": row[3],
                    "texto": row[4],
                })
            matrix = np.vstack(vectores)
            return matrix, metadatos
        finally:
            con.close()

    def buscar_vectorial(self, query: str, cuerpo_legal: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """Búsqueda densa semántica por similitud coseno (usa `sqlite-vec` KNN cuando está disponible)."""
        if not query.strip():
            return []

        q_vec = self.embedder.encode(query)

        # Ruta rápida nativa en disco con sqlite-vec (vec0) cuando no hay filtro de cuerpo
        if self.usa_sqlite_vec and not cuerpo_legal:
            con = self._conectar()
            try:
                filas = con.execute("""
                    SELECT v.articulo_rowid, v.distance, a.cuerpo_legal, a.articulo_id, a.etiqueta_bcn, a.texto
                    FROM articulos_vec0 v
                    JOIN articulos_vectorial a ON a.id = v.articulo_rowid
                    WHERE v.embedding MATCH ? AND k = ?
                    ORDER BY v.distance ASC;
                """, (q_vec.tobytes(), top_k)).fetchall()
                if filas:
                    return [
                        {
                            "id": r[0],
                            "cuerpo_legal": r[2],
                            "articulo_id": r[3],
                            "etiqueta_bcn": r[4],
                            "texto": r[5],
                            "similitud": round(float(1.0 - float(r[1])), 4),
                            "motor_vectorial": f"sqlite-vec+{self.embedder.backend}",
                        }
                        for r in filas
                    ]
            except sqlite3.OperationalError:
                pass
            finally:
                con.close()

        matrix, metadatos = self._cargar_matriz_en_memoria(cuerpo_legal=cuerpo_legal)
        if len(metadatos) == 0:
            return []

        # Producto punto sobre vectores normalizados (equivale a coseno)
        similitudes = np.dot(matrix, q_vec)
        top_indices = np.argsort(-similitudes)[:top_k]

        resultados = []
        for idx in top_indices:
            res = dict(metadatos[idx])
            res["similitud"] = round(float(similitudes[idx]), 4)
            res["motor_vectorial"] = f"numpy+{self.embedder.backend}"
            resultados.append(res)
        return resultados

    def buscar_lexica_fts(self, query: str, cuerpo_legal: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """Búsqueda exacta/léxica en SQLite FTS5 BM25."""
        if not query.strip():
            return []

        # Limpiar términos para sintaxis FTS5 segura
        palabras = [re.sub(r"[^\w]+", "", w) for w in query.split() if len(w) > 2]
        if not palabras:
            return []
        fts_query = " OR ".join(palabras[:8])

        con = self._conectar()
        try:
            params: Tuple[Any, ...]
            if cuerpo_legal:
                sql = """
                SELECT rowid, cuerpo_legal, articulo_id, etiqueta_bcn, texto, rank
                FROM articulos_fts
                WHERE articulos_fts MATCH ? AND cuerpo_legal = ?
                ORDER BY rank LIMIT ?;
                """
                params = (fts_query, cuerpo_legal, top_k)
            else:
                sql = """
                SELECT rowid, cuerpo_legal, articulo_id, etiqueta_bcn, texto, rank
                FROM articulos_fts
                WHERE articulos_fts MATCH ?
                ORDER BY rank LIMIT ?;
                """
                params = (fts_query, top_k)

            try:
                cur = con.execute(sql, params)
                filas = cur.fetchall()
            except sqlite3.OperationalError:
                return []

            resultados = []
            for r in filas:
                resultados.append({
                    "id": r[0],
                    "cuerpo_legal": r[1],
                    "articulo_id": r[2],
                    "etiqueta_bcn": r[3],
                    "texto": r[4],
                    "rank_bm25": round(float(r[5]), 4),
                })
            return resultados
        finally:
            con.close()

    def buscar_hibrido(self, query: str, cuerpo_legal: Optional[str] = None, top_k: int = 5,
                        w_bm25: float = 0.4, w_dense: float = 0.6, k: int = 60,
                        rerank: bool = True) -> List[Dict[str, Any]]:
        """
        Búsqueda híbrida Reciprocal Rank Fusion (RRF) combinando sparse FTS5 y dense vectorial,
        refinada opcionalmente con `ChileNeuralReranker`.
        """
        dense_hits = self.buscar_vectorial(query, cuerpo_legal=cuerpo_legal, top_k=top_k * 2)
        sparse_hits = self.buscar_lexica_fts(query, cuerpo_legal=cuerpo_legal, top_k=top_k * 2)

        puntajes_rrf: Dict[str, float] = {}
        documentos: Dict[str, Dict[str, Any]] = {}

        # Procesar ranking denso
        for rank, doc in enumerate(dense_hits, 1):
            key = f"{doc['cuerpo_legal']}_{doc['articulo_id']}"
            puntajes_rrf[key] = puntajes_rrf.get(key, 0.0) + (w_dense / (k + rank))
            documentos[key] = doc

        # Procesar ranking disperso
        for rank, doc in enumerate(sparse_hits, 1):
            key = f"{doc['cuerpo_legal']}_{doc['articulo_id']}"
            puntajes_rrf[key] = puntajes_rrf.get(key, 0.0) + (w_bm25 / (k + rank))
            if key not in documentos:
                documentos[key] = doc

        pool_n = max(top_k * 2, 10) if rerank else top_k
        ordenados = sorted(puntajes_rrf.items(), key=lambda x: -x[1])[:pool_n]

        resultados = []
        for key, score in ordenados:
            item = dict(documentos[key])
            item["puntaje_rrf"] = round(score, 6)
            resultados.append(item)

        if rerank and len(resultados) > 1:
            try:
                from neural_retriever import obtener_reranker_chileno

                reranker = obtener_reranker_chileno()
                if reranker.modelo_disponible:
                    return reranker.rerank(
                        query,
                        resultados,
                        title_key="etiqueta_bcn",
                        text_key="texto",
                        top_k=top_k,
                        peso_neuronal=0.55,
                    )
            except Exception:  # noqa: BLE001 — fallback al ranking RRF directo
                pass
        return resultados[:top_k]


# Instancia singleton para uso rápido
_instancia_vector: Optional[VectorLegalEngine] = None


def obtener_motor_vectorial() -> VectorLegalEngine:
    global _instancia_vector
    if _instancia_vector is None:
        _instancia_vector = VectorLegalEngine()
    return _instancia_vector
