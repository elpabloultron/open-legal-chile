#!/usr/bin/env python3
"""
Open Legal Chile — Exportador Apache Parquet para Hugging Face & DuckDB (`scripts/exportar_parquet_hf.py`)

Convierte el corpus jurídico, la base doctrinal SQLite (`doctrina.db`), el Baremo Estadístico PJUD
y el Knowledge Graph multiplex (`LegalGraphify` + capa del mapa) en 5 tablas columnares Apache Parquet
con compresión Snappy y esquema tipado estricto:

1. `corpus_entradas.parquet`    — Catálogo estructurado de los ~82.674 archivos del dataset en HF
2. `doctrina_fichas.parquet`    — Las ~18.749 fichas dogmáticas limpias de `doctrina.db` (rutas relativas)
3. `baremo_dano_moral.parquet`  — Cuantiles numéricos UF/CLP de las 17 categorías del Baremo PJUD
4. `grafo_nodos.parquet`        — Nodos unificados (Base + Mapa) con centralidad sustantiva y comunidad
5. `grafo_aristas.parquet`      — Aristas tipificadas con clasificación multiplex (`es_sustantiva`, `peso_multiplex`)

Esto habilita el Dataset Viewer nativo de Hugging Face, consultas SQL instantáneas con DuckDB
(`SELECT * FROM 'hf://datasets/pablobenavidesj/doctrina-jurisprudencia-chile/data/parquet/corpus_entradas.parquet'`)
y análisis reproducible en Python, R y Stata sin parsear decenas de miles de archivos Markdown.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import zlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from jurimetria import (
    HF_REPO_DEFAULT,
    _cargar_baremo_local,
    _localizar_mapa_sqlite,
    es_articulo_plausible,
    normalizar_resultado_judicial,
)
from legal_graphify import (
    DEFAULT_GRAPH_PATH,
    LegalGraphifyEngine,
    es_arista_sustantiva,
    peso_multiplex,
)

SALIDA_DEFAULT = RAIZ / "data" / "parquet"
DOCTRINA_DB = RAIZ / "doctrina.db"


def _sha256_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _ruta_relativa_segura(filepath: str) -> str:
    """Convierte rutas locales absolutas en rutas relativas limpias al repositorio (sin filtrar HOME)."""
    raw = str(filepath or "").replace("\\", "/").strip()
    if not raw:
        return ""
    raiz_str = str(RAIZ).replace("\\", "/").rstrip("/") + "/"
    if raw.startswith(raiz_str):
        return raw[len(raiz_str):]
    for ancla in ("doctrina/", "corpus_guias_aj/", "data/", "jurisprudencia_"):
        idx = raw.find(ancla)
        if idx != -1:
            return raw[idx:]
    return os.path.basename(raw)


def _escribir_parquet(
    ruta: Path,
    columnas: Dict[str, List[Any]],
    schema: Any,
) -> Dict[str, Any]:
    import pyarrow as pa
    import pyarrow.parquet as pq

    tabla = pa.table(columnas, schema=schema)
    pq.write_table(tabla, str(ruta), compression="snappy", use_dictionary=True)
    return {
        "archivo": ruta.name,
        "filas": tabla.num_rows,
        "columnas": [f.name for f in tabla.schema],
        "bytes": ruta.stat().st_size,
        "mb": round(ruta.stat().st_size / (1024 * 1024), 3),
        "sha256": _sha256_archivo(ruta),
    }


def _exportar_corpus_entradas(
    destino: Path,
    mapa_sqlite_path: Optional[str] = None,
    usar_mapa: bool = True,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    import pyarrow as pa

    ruta_sqlite, meta = _localizar_mapa_sqlite(mapa_sqlite_path) if usar_mapa else (None, {})
    if ruta_sqlite is None:
        return None, {}

    sha_hf = str(meta.get("sha_fuente") or "main")
    cols: Dict[str, List[Any]] = {
        "id": [], "col": [], "ruta": [], "titulo": [], "fecha": [], "anio": [],
        "bytes": [], "rol": [], "sala": [], "recurso": [], "resultado": [],
        "resultado_normalizado": [], "ministros_n": [], "autores_n": [],
        "normas_citadas_n": [], "revista": [], "url_huggingface": [],
    }
    con = sqlite3.connect(f"{ruta_sqlite.resolve().as_uri()}?mode=ro&immutable=1", uri=True)
    try:
        for (blob_fila,) in con.execute("SELECT fila FROM entrada ORDER BY id"):
            f = json.loads(zlib.decompress(blob_fila).decode("utf-8"))
            fecha = str(f.get("fecha") or "")
            anio: Optional[int] = None
            if len(fecha) >= 4 and fecha[:4].isdigit():
                anio = int(fecha[:4])
            elif str(f.get("anio") or "").isdigit():
                anio = int(f["anio"])
            elif str(f.get("era") or "").isdigit():
                anio = int(f["era"])
            ruta_rel = str(f.get("ruta") or "")
            res_raw = str(f.get("resultado") or "")
            cols["id"].append(str(f.get("id") or ""))
            cols["col"].append(str(f.get("col") or ""))
            cols["ruta"].append(ruta_rel)
            cols["titulo"].append(str(f.get("titulo") or ""))
            cols["fecha"].append(fecha)
            cols["anio"].append(anio)
            cols["bytes"].append(int(f.get("bytes") or 0))
            cols["rol"].append(str(f.get("rol") or ""))
            cols["sala"].append(str(f.get("sala_txt") or f.get("sala") or ""))
            cols["recurso"].append(str(f.get("recurso_txt") or f.get("recurso") or ""))
            cols["resultado"].append(res_raw)
            cols["resultado_normalizado"].append(normalizar_resultado_judicial(res_raw))
            cols["ministros_n"].append(len(f.get("ministros") or []))
            cols["autores_n"].append(len(f.get("autores") or []))
            cols["normas_citadas_n"].append(len(f.get("normas") or []))
            cols["revista"].append(str(f.get("revista") or ""))
            cols["url_huggingface"].append(
                f"https://huggingface.co/datasets/{HF_REPO_DEFAULT}/blob/{sha_hf}/{ruta_rel}" if ruta_rel else ""
            )
    finally:
        con.close()

    schema = pa.schema([
        ("id", pa.string()),
        ("col", pa.string()),
        ("ruta", pa.string()),
        ("titulo", pa.string()),
        ("fecha", pa.string()),
        ("anio", pa.int32()),
        ("bytes", pa.int64()),
        ("rol", pa.string()),
        ("sala", pa.string()),
        ("recurso", pa.string()),
        ("resultado", pa.string()),
        ("resultado_normalizado", pa.string()),
        ("ministros_n", pa.int32()),
        ("autores_n", pa.int32()),
        ("normas_citadas_n", pa.int32()),
        ("revista", pa.string()),
        ("url_huggingface", pa.string()),
    ])
    info = _escribir_parquet(destino / "corpus_entradas.parquet", cols, schema)
    return info, meta


def _exportar_doctrina_fichas(destino: Path, db_path: Path = DOCTRINA_DB) -> Optional[Dict[str, Any]]:
    import pyarrow as pa

    if not db_path.exists():
        return None
    cols: Dict[str, List[Any]] = {
        "id": [], "area": [], "autor": [], "obra": [], "materia": [],
        "institucion": [], "definicion": [], "operativa_procesal": [],
        "concordancias": [], "fallo_rector": [], "archivo_relativo": [],
        "tokens_aprox": [], "chars_contenido": [],
    }
    con = sqlite3.connect(str(db_path))
    try:
        cur = con.execute(
            "SELECT id, area, autor, obra, materia, institucion, definicion, "
            "operativa_procesal, concordancias, fallo_rector, filepath, tokens_aprox, length(contenido) "
            "FROM doctrina_instituciones ORDER BY id"
        )
        for row in cur:
            cols["id"].append(int(row[0]))
            cols["area"].append(str(row[1] or ""))
            cols["autor"].append(str(row[2] or ""))
            cols["obra"].append(str(row[3] or ""))
            cols["materia"].append(str(row[4] or ""))
            cols["institucion"].append(str(row[5] or ""))
            cols["definicion"].append(str(row[6] or ""))
            cols["operativa_procesal"].append(str(row[7] or ""))
            cols["concordancias"].append(str(row[8] or ""))
            cols["fallo_rector"].append(str(row[9] or ""))
            cols["archivo_relativo"].append(_ruta_relativa_segura(str(row[10] or "")))
            cols["tokens_aprox"].append(int(row[11] or 0))
            cols["chars_contenido"].append(int(row[12] or 0))
    finally:
        con.close()

    schema = pa.schema([
        ("id", pa.int64()),
        ("area", pa.string()),
        ("autor", pa.string()),
        ("obra", pa.string()),
        ("materia", pa.string()),
        ("institucion", pa.string()),
        ("definicion", pa.string()),
        ("operativa_procesal", pa.string()),
        ("concordancias", pa.string()),
        ("fallo_rector", pa.string()),
        ("archivo_relativo", pa.string()),
        ("tokens_aprox", pa.int32()),
        ("chars_contenido", pa.int32()),
    ])
    return _escribir_parquet(destino / "doctrina_fichas.parquet", cols, schema)


def _exportar_baremo(destino: Path) -> Optional[Dict[str, Any]]:
    import pyarrow as pa

    filas = _cargar_baremo_local()
    if not filas:
        return None
    cols: Dict[str, List[Any]] = {
        "id": [r["id"] for r in filas],
        "parentesco": [r["parentesco"] for r in filas],
        "total_casos": [int(r["total_casos"]) for r in filas],
        "mediana_uf_pi": [float(r["mediana_uf_pi"]) for r in filas],
        "p25_uf_pi": [float(r["p25_uf_pi"]) for r in filas],
        "p75_uf_pi": [float(r["p75_uf_pi"]) for r in filas],
        "mediana_uf_ca": [float(r["mediana_uf_ca"]) for r in filas],
        "mediana_uf_cs": [float(r["mediana_uf_cs"]) for r in filas],
        "mediana_clp_pi": [float(r["mediana_clp_pi"]) for r in filas],
        "cita": [r["cita"] for r in filas],
    }
    schema = pa.schema([
        ("id", pa.string()),
        ("parentesco", pa.string()),
        ("total_casos", pa.int32()),
        ("mediana_uf_pi", pa.float64()),
        ("p25_uf_pi", pa.float64()),
        ("p75_uf_pi", pa.float64()),
        ("mediana_uf_ca", pa.float64()),
        ("mediana_uf_cs", pa.float64()),
        ("mediana_clp_pi", pa.float64()),
        ("cita", pa.string()),
    ])
    return _escribir_parquet(destino / "baremo_dano_moral.parquet", cols, schema)


def _exportar_grafo(
    destino: Path,
    graph_path: str = DEFAULT_GRAPH_PATH,
    usar_mapa: bool = True,
) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
    import networkx as nx
    import pyarrow as pa

    eng = LegalGraphifyEngine(usar_mapa=usar_mapa)
    if not eng.cargar_grafo_json(graph_path):
        raise RuntimeError(f"No se pudo cargar el grafo desde {graph_path}")
    if usar_mapa:
        eng.subir_capa_mapa()
    g = eng.graph

    # Calcular grado sustantivo y PageRank multiplex sobre el grafo completo
    g_multiplex = nx.DiGraph()
    g_multiplex.add_nodes_from(g.nodes())
    grado_sust: Dict[str, int] = {n: 0 for n in g.nodes()}
    aristas_cols: Dict[str, List[Any]] = {
        "source": [], "target": [], "relation": [], "capa": [],
        "es_sustantiva": [], "weight": [], "peso_multiplex": [],
    }
    for u, v, d in sorted(g.edges(data=True), key=lambda e: (str(e[0]), str(e[1]))):
        sust = es_arista_sustantiva(u, v, d, g)
        w_base = float(d.get("weight") or 1.0)
        w_mux = peso_multiplex(u, v, d, g)
        g_multiplex.add_edge(u, v, weight=w_mux)
        if sust:
            grado_sust[u] = grado_sust.get(u, 0) + 1
            grado_sust[v] = grado_sust.get(v, 0) + 1
        aristas_cols["source"].append(str(u))
        aristas_cols["target"].append(str(v))
        aristas_cols["relation"].append(str(d.get("relation") or ""))
        aristas_cols["capa"].append(str(d.get("capa") or "repo"))
        aristas_cols["es_sustantiva"].append(bool(sust))
        aristas_cols["weight"].append(w_base)
        aristas_cols["peso_multiplex"].append(w_mux)

    try:
        pr_mux = nx.pagerank(g_multiplex, alpha=0.85, weight="weight", max_iter=100)
    except Exception:  # noqa: BLE001
        pr_mux = {n: 0.0 for n in g.nodes()}

    nodos_cols: Dict[str, List[Any]] = {
        "id": [], "label": [], "node_type": [], "capa": [], "community": [],
        "area": [], "autor": [], "obra": [], "id_mapa": [], "id_canonico": [],
        "rango_norma_plausible": [], "grado_total": [], "grado_sustantivo": [],
        "pagerank_sustantivo": [],
    }
    for nid in sorted(g.nodes()):
        nd = g.nodes[nid]
        id_can = str(nd.get("id_canonico") or nd.get("id_mapa") or (nid if str(nid).startswith("norma:") else ""))
        nodos_cols["id"].append(str(nid))
        nodos_cols["label"].append(str(nd.get("label") or nid))
        nodos_cols["node_type"].append(str(nd.get("node_type") or ""))
        nodos_cols["capa"].append(str(nd.get("capa") or "repo"))
        nodos_cols["community"].append(str(nd.get("community") if nd.get("community") is not None else ""))
        nodos_cols["area"].append(str(nd.get("area") or ""))
        nodos_cols["autor"].append(str(nd.get("autor") or ""))
        nodos_cols["obra"].append(str(nd.get("obra") or ""))
        nodos_cols["id_mapa"].append(str(nd.get("id_mapa") or ""))
        nodos_cols["id_canonico"].append(id_can)
        nodos_cols["rango_norma_plausible"].append(es_articulo_plausible(id_can) if id_can.startswith("norma:") else True)
        nodos_cols["grado_total"].append(int(g.degree(nid)))
        nodos_cols["grado_sustantivo"].append(int(grado_sust.get(nid, 0)))
        nodos_cols["pagerank_sustantivo"].append(round(float(pr_mux.get(nid, 0.0)), 8))

    schema_nodos = pa.schema([
        ("id", pa.string()),
        ("label", pa.string()),
        ("node_type", pa.string()),
        ("capa", pa.string()),
        ("community", pa.string()),
        ("area", pa.string()),
        ("autor", pa.string()),
        ("obra", pa.string()),
        ("id_mapa", pa.string()),
        ("id_canonico", pa.string()),
        ("rango_norma_plausible", pa.bool_()),
        ("grado_total", pa.int32()),
        ("grado_sustantivo", pa.int32()),
        ("pagerank_sustantivo", pa.float64()),
    ])
    schema_aristas = pa.schema([
        ("source", pa.string()),
        ("target", pa.string()),
        ("relation", pa.string()),
        ("capa", pa.string()),
        ("es_sustantiva", pa.bool_()),
        ("weight", pa.float64()),
        ("peso_multiplex", pa.float64()),
    ])

    info_nodos = _escribir_parquet(destino / "grafo_nodos.parquet", nodos_cols, schema_nodos)
    info_aristas = _escribir_parquet(destino / "grafo_aristas.parquet", aristas_cols, schema_aristas)
    return info_nodos, info_aristas, eng.origen_grafo


def exportar_parquet_completo(
    carpeta_salida: Path = SALIDA_DEFAULT,
    graph_path: str = DEFAULT_GRAPH_PATH,
    db_path: Path = DOCTRINA_DB,
    mapa_sqlite_path: Optional[str] = None,
    usar_mapa: bool = True,
) -> Dict[str, Any]:
    """Ejecuta la exportación completa de las 5 tablas Parquet y escribe `manifiesto_parquet.json`."""
    try:
        import pyarrow  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "Se requiere `pyarrow` para exportar Apache Parquet. Instale con `pip install openlegal-chile[analytics]`."
        ) from exc

    destino = Path(carpeta_salida).expanduser().resolve()
    destino.mkdir(parents=True, exist_ok=True)

    tablas: Dict[str, Any] = {}
    faltantes: List[str] = []

    info_corpus, meta_mapa = _exportar_corpus_entradas(destino, mapa_sqlite_path=mapa_sqlite_path, usar_mapa=usar_mapa)
    if info_corpus:
        tablas["corpus_entradas"] = info_corpus
    else:
        faltantes.append("corpus_entradas (mapa.sqlite local no disponible o desactivado con --sin-mapa)")

    info_doc = _exportar_doctrina_fichas(destino, db_path=db_path)
    if info_doc:
        tablas["doctrina_fichas"] = info_doc
    else:
        faltantes.append(f"doctrina_fichas ({db_path} no existe)")

    info_baremo = _exportar_baremo(destino)
    if info_baremo:
        tablas["baremo_dano_moral"] = info_baremo
    else:
        faltantes.append("baremo_dano_moral (data/jurisprudencia/baremo_dano_moral.jsonl no existe)")

    info_nodos, info_aristas, origen_grafo = _exportar_grafo(destino, graph_path=graph_path, usar_mapa=usar_mapa)
    tablas["grafo_nodos"] = info_nodos
    tablas["grafo_aristas"] = info_aristas

    manifiesto = {
        "repo_hf": HF_REPO_DEFAULT,
        "origen_grafo": origen_grafo,
        "sha_fuente_hf": meta_mapa.get("sha_fuente", ""),
        "fecha_fuente_hf": meta_mapa.get("fecha_fuente", ""),
        "ruta_en_dataset": "data/parquet",
        "total_tablas": len(tablas),
        "total_bytes": sum(int(t["bytes"]) for t in tablas.values()),
        "total_mb": round(sum(int(t["bytes"]) for t in tablas.values()) / (1024 * 1024), 3),
        "tablas": tablas,
        "faltantes": faltantes,
    }
    (destino / "manifiesto_parquet.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifiesto


def subir_parquet_huggingface(
    carpeta: Path,
    repo_id: str = HF_REPO_DEFAULT,
    token: Optional[str] = None,
    actualizar_dataset_card: bool = False,
    subir_grafo_curado: bool = False,
) -> Dict[str, Any]:
    """Publica `data/parquet/` (y opcionalmente el grafo curado y la Dataset Card YAML) en HF Datasets."""
    import tempfile
    from huggingface_hub import HfApi
    from online_library_sync import OnlineLibrarySyncManager, resolver_token_hf

    tok = resolver_token_hf(token)
    if not tok:
        raise RuntimeError("Falta token de Hugging Face (HF_TOKEN o ~/.openlegal/hf_token) para publicar Parquet.")
    api = HfApi(token=tok)
    info = api.upload_folder(
        folder_path=str(carpeta),
        path_in_repo="data/parquet",
        repo_id=repo_id,
        repo_type="dataset",
        commit_message="analytics: actualiza tablas Apache Parquet para Dataset Viewer y DuckDB SQL",
    )
    resultado: Dict[str, Any] = {
        "publicado": True,
        "repo_id": repo_id,
        "url": str(getattr(info, "commit_url", "") or info),
    }
    if subir_grafo_curado and Path(DEFAULT_GRAPH_PATH).is_file():
        api.upload_file(
            path_or_fileobj=str(DEFAULT_GRAPH_PATH),
            path_in_repo="data/legal_knowledge_graph.json",
            repo_id=repo_id,
            repo_type="dataset",
            commit_message="graphify: actualiza data/legal_knowledge_graph.json enriquecido y podado",
        )
        resultado["grafo_curado_subido"] = True
    if actualizar_dataset_card:
        card_md = OnlineLibrarySyncManager().preparar_dataset_card_huggingface(repo_id=repo_id)
        with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as tmp:
            tmp.write(card_md)
            tmp_path = tmp.name
        try:
            api.upload_file(
                path_or_fileobj=tmp_path,
                path_in_repo="README.md",
                repo_id=repo_id,
                repo_type="dataset",
                commit_message="docs(hf): declara config analytics_parquet en Dataset Card YAML",
            )
            resultado["dataset_card_actualizada"] = True
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    return resultado


def main() -> None:
    parser = argparse.ArgumentParser(description="Exportador Apache Parquet para Hugging Face & DuckDB (Open Legal Chile)")
    parser.add_argument("--salida", default=str(SALIDA_DEFAULT), help="Carpeta de salida para los archivos .parquet")
    parser.add_argument("--graph", default=DEFAULT_GRAPH_PATH, help="Ruta al grafo JSON curado")
    parser.add_argument("--db", default=str(DOCTRINA_DB), help="Ruta a doctrina.db")
    parser.add_argument("--mapa-sqlite", default=None, help="Ruta explícita a mapa.sqlite (opcional)")
    parser.add_argument("--sin-mapa", action="store_true", help="Exporta solo datos locales sin cargar capa del mapa HF")
    parser.add_argument("--subir-hf", action="store_true", help="Publica data/parquet/ en Hugging Face Datasets Hub")
    parser.add_argument("--subir-grafo", action="store_true", help="Publica también data/legal_knowledge_graph.json")
    parser.add_argument("--subir-card", action="store_true", help="Actualiza también README.md (Dataset Card YAML) en HF")
    parser.add_argument("--repo-hf", default=HF_REPO_DEFAULT, help="Repositorio destino en Hugging Face")
    args = parser.parse_args()

    manifiesto = exportar_parquet_completo(
        carpeta_salida=Path(args.salida),
        graph_path=args.graph,
        db_path=Path(args.db),
        mapa_sqlite_path=args.mapa_sqlite,
        usar_mapa=not args.sin_mapa,
    )
    if args.subir_hf:
        manifiesto["publicacion_hf"] = subir_parquet_huggingface(
            Path(args.salida),
            repo_id=args.repo_hf,
            actualizar_dataset_card=args.subir_card,
            subir_grafo_curado=args.subir_grafo,
        )
    print(json.dumps(manifiesto, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
