"""
Open Legal Chile — Módulo de Jurimetría e Investigación Académica Reproducible (`jurimetria.py`)

Provee análisis cuantitativo de redes de citación normativa y jurisprudencial (PageRank dirigido,
HITS Authority/Hub sobre el subgrafo sustantivo multiplex), estadísticas longitudinales exactas
sobre el corpus cosechado (`mapa.sqlite` / `data/jurisprudencia/*.jsonl`), muestreo estratificado
determinista para validación humana ciega (precisión, cobertura, F1, κ de Cohen) y exportación de
paquetes reproducibles de investigación (CSV, GraphML, Apache Parquet, BibTeX y memoria metodológica).

Principios de Derecho Continental (Chile):
- Primacía de la ley escrita (Art. 1 del Código Civil) y efecto relativo de las sentencias
  (Art. 3 inc. 2 del Código Civil): los indicadores jurimétricos describen tendencias empíricas
  de aplicación judicial y nunca precedentes vinculantes al estilo del sistema anglosajón.
- Honestidad metodológica: cada resultado declara universo exacto (N), revisión fijada del corpus
  en Hugging Face, ventana temporal y sesgos muestrales conocidos.
"""

from __future__ import annotations

import csv
import datetime as _dt
import json
import os
import random
import re
import sqlite3
import zlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import networkx as nx

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
JURISP_DIR = DATA_DIR / "jurisprudencia"
HF_REPO_DEFAULT = "pablobenavidesj/doctrina-jurisprudencia-chile"

# Límites máximos plausibles de artículos permanentes por cuerpo legal chileno.
# Sirve para auditar ruido OCR en revistas y PDFs antiguos (p. ej. `norma:cpr:1682`).
MAX_ARTICULO_POR_CUERPO: Dict[str, int] = {
    "cpr": 161,
    "cc": 2525,
    "cpc": 925,
    "cp": 501,
    "ct": 513,
    "cot": 607,
    "cpp": 485,
    "cpp1906": 697,
    "ctrib": 205,
    "ccom": 1250,
    "caguas": 317,
    "cmin": 244,
    "csan": 174,
    "cjm": 436,
    "losma": 66,
}

_RE_DIGITOS_INICIALES = re.compile(r"^(\d+)")


def es_articulo_plausible(norma_id: str) -> bool:
    """Valida si un ID canónico `norma:<cuerpo>:<art>[:...]` cae dentro del rango de artículos
    permanentes conocidos del cuerpo legal chileno (filtra alucinaciones OCR como `norma:cpr:1682`)."""
    if not norma_id or not norma_id.startswith("norma:"):
        return True
    partes = norma_id.split(":")
    if len(partes) < 3:
        return True
    cuerpo = partes[1].lower()
    art = partes[2].lower()
    if "transitorio" in art or "final" in art:
        return True
    m = _RE_DIGITOS_INICIALES.match(art)
    if not m:
        return True
    num = int(m.group(1))
    if num <= 0:
        return False
    tope = MAX_ARTICULO_POR_CUERPO.get(cuerpo)
    if tope is not None:
        return num <= tope
    # Para leyes numeradas (`ley-19300`, `dfl-1`), descartar años o roles capturados por error (> 2600)
    return num <= 2600


def normalizar_resultado_judicial(resultado: str) -> str:
    """Normaliza la etiqueta textual de resultado judicial a categorías jurimétricas estándar."""
    txt = (resultado or "").strip().upper()
    if not txt or txt in ("—", "-", "N/A", "SIN DATOS"):
        return "sin_datos"
    if "OFICIO" in txt and ("CASA" in txt or "ANULA" in txt or "INVALIDA" in txt):
        return "casacion_oficio"
    if "INADMISIB" in txt or "DESIERTO" in txt or "NO HA LUGAR A TRAMIT" in txt:
        return "inadmisible"
    if "NO SE HACE LUGAR" in txt or "NO HA LUGAR" in txt or "SIN LUGAR" in txt or "RECHAZ" in txt or "DESESTIM" in txt:
        return "rechaza"
    if "ACOG" in txt or "SE HACE LUGAR" in txt or "HA LUGAR" in txt:
        return "acoge"
    if "REVOC" in txt:
        return "revoca"
    if "CONFIRM" in txt:
        return "confirma"
    if "DESIST" in txt or "CONCILI" in txt or "AVENIM" in txt:
        return "termino_equivalente"
    return "otro"


def _localizar_mapa_sqlite(mapa_sqlite_path: Optional[str] = None) -> Tuple[Optional[Path], Dict[str, Any]]:
    """Resuelve la ruta de `mapa.sqlite` local (sin red) y sus metadatos de revisión."""
    if mapa_sqlite_path:
        p = Path(mapa_sqlite_path)
        if p.exists():
            return p, _leer_meta_sqlite(p)
        return None, {}
    try:
        from mapa_corpus.cliente import obtener_cliente

        cli = obtener_cliente()
        ind = cli.indice()
        if ind is not None and ind.ruta.exists():
            return ind.ruta, ind.meta()
    except Exception:  # noqa: BLE001 — fallback transparente al disco
        pass
    return None, {}


def _leer_meta_sqlite(ruta: Path) -> Dict[str, Any]:
    con = sqlite3.connect(f"{ruta.resolve().as_uri()}?mode=ro&immutable=1", uri=True)
    try:
        return {str(k): str(v) for k, v in con.execute("SELECT clave, valor FROM meta")}
    except sqlite3.Error:
        return {}
    finally:
        con.close()


def _cargar_baremo_local() -> List[Dict[str, Any]]:
    ruta = JURISP_DIR / "baremo_dano_moral.jsonl"
    if not ruta.exists():
        return []
    filas: List[Dict[str, Any]] = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea:
            continue
        reg = json.loads(linea)
        uf = reg.get("estadisticas_uf") or {}
        clp = reg.get("estadisticas_clp") or {}
        pi_uf = uf.get("primera_instancia") or {}
        ca_uf = uf.get("corte_apelaciones") or {}
        cs_uf = uf.get("corte_suprema") or {}
        pi_clp = clp.get("primera_instancia") or {}
        filas.append({
            "id": str(reg.get("id") or ""),
            "parentesco": str(reg.get("parentesco") or ""),
            "total_casos": int(reg.get("total_casos_analizados") or 0),
            "mediana_uf_pi": float(pi_uf.get("mediana") or 0.0),
            "p25_uf_pi": float(pi_uf.get("p25") or 0.0),
            "p75_uf_pi": float(pi_uf.get("p75") or 0.0),
            "mediana_uf_ca": float(ca_uf.get("mediana") or 0.0),
            "mediana_uf_cs": float(cs_uf.get("mediana") or 0.0),
            "mediana_clp_pi": float(pi_clp.get("mediana") or 0.0),
            "cita": str(reg.get("cita") or ""),
        })
    filas.sort(key=lambda r: (-int(r["total_casos"]), -float(r["mediana_uf_pi"]), str(r["parentesco"])))
    return filas


def analizar_red_citaciones(
    motor: Optional[Any] = None,
    coleccion: Optional[str] = None,
    norma_filtro: Optional[str] = None,
    top_k: int = 20,
    excluir_bibliograficos: bool = True,
) -> Dict[str, Any]:
    """
    Ejecuta análisis jurimétrico de red sobre el grafo de conocimiento (`LegalGraphify` + capa del mapa):
    - Separa la capa sustantiva (normas, sentencias, instituciones, vías procesales) de la capa
      bibliográfica (autores, obras, revistas).
    - Calcula PageRank dirigido y HITS (Authority y Hub) sobre el subgrafo de citaciones.
    - Audita resolución de entidades (duplicidad de Baremo, artículos OCR fuera de rango).
    """
    from legal_graphify import (
        TIPOS_HUB_EDITORIAL,
        _TIPOS_NORMA,
        _TIPOS_SENTENCIA,
        es_arista_sustantiva,
        obtener_motor_compartido,
        peso_multiplex,
    )

    eng = motor if motor is not None else obtener_motor_compartido()
    eng._preparar_consulta()
    g: nx.DiGraph = eng.graph

    if g.number_of_nodes() == 0:
        return {"error": "El grafo de conocimiento está vacío; ejecute la carga del corpus primero."}

    # Diagnóstico topológico global previo al recorte
    aristas_sust = 0
    aristas_bib = 0
    for u, v, d in g.edges(data=True):
        if es_arista_sustantiva(u, v, d, g):
            aristas_sust += 1
        else:
            aristas_bib += 1

    normas_fuera_rango: List[str] = []
    nodos_baremo = 0
    for nid, nd in g.nodes(data=True):
        nt = str(nd.get("node_type") or "")
        if nt == "baremo":
            nodos_baremo += 1
        elif nt in _TIPOS_NORMA and str(nid).startswith("norma:") and not es_articulo_plausible(str(nid)):
            normas_fuera_rango.append(str(nid))

    # Construir subgrafo de trabajo
    sub = nx.DiGraph()
    nodos_permitidos: Optional[Set[str]] = None

    if norma_filtro:
        centro = eng._buscar_nodo_relevante(norma_filtro)
        if not centro or not g.has_node(centro):
            return {
                "error": f"No se encontró el nodo para norma_filtro='{norma_filtro}'.",
                "origen_grafo": getattr(eng, "origen_grafo", "repo"),
            }
        # Vecindario sustantivo de radio 2
        vec1 = set(g.successors(centro)) | set(g.predecessors(centro)) | {centro}
        vec2 = set(vec1)
        for v in list(vec1)[:300]:
            vec2.update(list(g.successors(v))[:40])
            vec2.update(list(g.predecessors(v))[:40])
        nodos_permitidos = vec2

    col_norm = (coleccion or "").strip().lower()
    col_a_tipos: Dict[str, Set[str]] = {
        "cs": {"sentencia_cs", "jurisprudencia", "jurisprudencia_cs", "lineas", "salud", "extranjeria", "ddhh", "genero"},
        "tc": {"sentencia_tc", "jurisprudencia_tc"},
        "ta": {"sentencia_ta", "estudio", "publicacion", "estudio_ambiental", "anuario_boletin_ambiental"},
        "doc": {"institucion", "documento", "guia"},
        "baremo": {"baremo"},
    }
    tipos_col = col_a_tipos.get(col_norm)

    for u, v, d in g.edges(data=True):
        if nodos_permitidos is not None and (u not in nodos_permitidos or v not in nodos_permitidos):
            continue
        sust = es_arista_sustantiva(u, v, d, g)
        if excluir_bibliograficos and not sust:
            continue
        tu = str(g.nodes[u].get("node_type") or "")
        tv = str(g.nodes[v].get("node_type") or "")
        if excluir_bibliograficos and (tu in TIPOS_HUB_EDITORIAL or tv in TIPOS_HUB_EDITORIAL):
            continue
        if tipos_col is not None:
            # Conservar aristas donde al menos un extremo pertenece a la colección solicitada
            if tu not in tipos_col and tv not in tipos_col:
                continue
        if u not in sub:
            sub.add_node(u, **g.nodes[u])
        if v not in sub:
            sub.add_node(v, **g.nodes[v])
        sub.add_edge(u, v, relation=d.get("relation", ""), weight=peso_multiplex(u, v, d, g))

    if sub.number_of_nodes() == 0:
        return {
            "origen_grafo": getattr(eng, "origen_grafo", "repo"),
            "filtros": {"coleccion": coleccion, "norma_filtro": norma_filtro, "excluir_bibliograficos": excluir_bibliograficos},
            "metricas_red": {"nodos_subgrafo": 0, "aristas_subgrafo": 0},
            "normas_mas_citadas": [],
            "sentencias_autoridad": [],
            "instituciones_centrales": [],
            "documentos_hub": [],
        }

    # PageRank dirigido
    pr_metodo = "pagerank_dirigido"
    try:
        pr: Dict[str, float] = nx.pagerank(sub, alpha=0.85, weight="weight", max_iter=100)
    except Exception:  # noqa: BLE001 — degradación determinista
        pr_metodo = "grado_entrada_fallback"
        tot = max(1, sub.number_of_edges())
        pr = {n: float(sub.in_degree(n)) / tot for n in sub.nodes()}

    # HITS (Authority = fuente más citada por hubs relevantes; Hub = documento que sintetiza autoridades).
    # Se calcula sobre la subred de citación con pesos unitarios (excluyendo aristas agregadas de
    # orgánica judicial como `integra_sala`/`conoce_recurso`/`eleva_a`/`parte_de`, cuyos pesos de
    # decenas de miles dominarían el autovector principal y aplastarían las normas y sentencias).
    _RELS_ORGANICAS = frozenset({"integra_sala", "conoce_recurso", "eleva_a", "parte_de", "resuelto_por", "integrado_por"})
    sub_hits = nx.DiGraph()
    for u, v, d in sub.edges(data=True):
        if str(d.get("relation") or "") not in _RELS_ORGANICAS:
            sub_hits.add_edge(u, v, weight=1.0)
    if sub_hits.number_of_edges() == 0:
        sub_hits = sub

    hits_metodo = "hits_citacion_unitaria"
    try:
        hubs, authorities = nx.hits(sub_hits, max_iter=200, normalized=True)
    except Exception:  # noqa: BLE001 — fallback determinista por grado
        hits_metodo = "grado_fallback"
        tot_e = max(1, sub_hits.number_of_edges())
        hubs = {n: float(sub_hits.out_degree(n)) / tot_e for n in sub_hits.nodes()}
        authorities = {n: float(sub_hits.in_degree(n)) / tot_e for n in sub_hits.nodes()}

    top_k = max(1, min(100, int(top_k)))
    normas_rank: List[Dict[str, Any]] = []
    sentencias_rank: List[Dict[str, Any]] = []
    instituciones_rank: List[Dict[str, Any]] = []
    hubs_rank: List[Dict[str, Any]] = []

    for nid in sub.nodes():
        nd = sub.nodes[nid]
        nt = str(nd.get("node_type") or "")
        lbl = str(nd.get("label") or nid)
        in_d = int(sub.in_degree(nid))
        out_d = int(sub.out_degree(nid))
        pr_s = round(float(pr.get(nid, 0.0)), 6)
        auth_s = round(float(authorities.get(nid, 0.0)), 6)
        hub_s = round(float(hubs.get(nid, 0.0)), 6)

        item = {
            "id": nid,
            "label": lbl,
            "tipo": nt,
            "citas_recibidas": in_d,
            "citas_emitidas": out_d,
            "pagerank": pr_s,
            "hits_authority": auth_s,
            "hits_hub": hub_s,
        }
        if nt in _TIPOS_NORMA:
            plausible = es_articulo_plausible(str(nid))
            item["rango_articulo_plausible"] = plausible
            if plausible:
                normas_rank.append(item)
        elif nt in _TIPOS_SENTENCIA:
            sentencias_rank.append(item)
        elif nt == "institucion":
            instituciones_rank.append(item)
        if nt in ("documento", "institucion", "guia", "estudio", "publicacion") and out_d > 0:
            hubs_rank.append(item)

    normas_rank.sort(key=lambda x: (-x["citas_recibidas"], -x["hits_authority"], -x["pagerank"], x["id"]))
    sentencias_rank.sort(key=lambda x: (-x["citas_recibidas"], -x["hits_authority"], -x["pagerank"], x["id"]))
    instituciones_rank.sort(key=lambda x: (-x["pagerank"], -(x["citas_recibidas"] + x["citas_emitidas"]), x["id"]))
    hubs_rank.sort(key=lambda x: (-x["hits_hub"], -x["citas_emitidas"], x["id"]))

    # Componentes débilmente conexas del subgrafo sustantivo
    comp_tamanos = sorted((len(c) for c in nx.weakly_connected_components(sub)), reverse=True)
    gigante = comp_tamanos[0] if comp_tamanos else 0
    densidad = round(float(nx.density(sub)), 6) if sub.number_of_nodes() > 1 else 0.0

    # Instituciones con enlace sustantivo real en el grafo completo
    inst_totales = 0
    inst_con_norma = 0
    inst_con_jurisp = 0
    for nid, nd in g.nodes(data=True):
        if nd.get("node_type") != "institucion":
            continue
        inst_totales += 1
        vecinos = set(g.successors(nid)) | set(g.predecessors(nid))
        tipos_v = {str(g.nodes[v].get("node_type") or "") for v in vecinos}
        if tipos_v & set(_TIPOS_NORMA):
            inst_con_norma += 1
        if tipos_v & set(_TIPOS_SENTENCIA):
            inst_con_jurisp += 1

    return {
        "origen_grafo": getattr(eng, "origen_grafo", "repo"),
        "filtros": {
            "coleccion": coleccion,
            "norma_filtro": norma_filtro,
            "excluir_bibliograficos": excluir_bibliograficos,
        },
        "metodos": {"pagerank": pr_metodo, "hits": hits_metodo},
        "metricas_red": {
            "nodos_grafo_completo": g.number_of_nodes(),
            "aristas_grafo_completo": g.number_of_edges(),
            "aristas_sustantivas": aristas_sust,
            "aristas_bibliograficas": aristas_bib,
            "proporcion_sustantiva_pct": round(100.0 * aristas_sust / max(1, aristas_sust + aristas_bib), 2),
            "nodos_subgrafo_analizado": sub.number_of_nodes(),
            "aristas_subgrafo_analizado": sub.number_of_edges(),
            "densidad_subgrafo": densidad,
            "componentes_debilmente_conexas": len(comp_tamanos),
            "componente_gigante_nodos": gigante,
            "componente_gigante_pct": round(100.0 * gigante / max(1, sub.number_of_nodes()), 2),
        },
        "calidad_ontologica": {
            "instituciones_totales": inst_totales,
            "instituciones_enlazadas_a_norma": inst_con_norma,
            "instituciones_enlazadas_a_norma_pct": round(100.0 * inst_con_norma / max(1, inst_totales), 2),
            "instituciones_enlazadas_a_jurisprudencia": inst_con_jurisp,
            "instituciones_enlazadas_a_jurisprudencia_pct": round(100.0 * inst_con_jurisp / max(1, inst_totales), 2),
            "nodos_baremo_unicos": nodos_baremo,
            "normas_ocr_fuera_de_rango_detectadas": len(normas_fuera_rango),
            "ejemplos_ocr_fuera_de_rango": sorted(normas_fuera_rango)[:10],
        },
        "normas_mas_citadas": normas_rank[:top_k],
        "sentencias_autoridad": sentencias_rank[:top_k],
        "instituciones_centrales": instituciones_rank[:top_k],
        "documentos_hub": hubs_rank[:top_k],
    }


def _iterar_entradas_corpus(
    coleccion: Optional[str] = None,
    mapa_sqlite_path: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Itera entradas estructuradas desde `mapa.sqlite` (si está disponible) o respaldo JSONL local."""
    ruta_sqlite, meta = _localizar_mapa_sqlite(mapa_sqlite_path)
    col_filtro = (coleccion or "").strip().lower()

    if ruta_sqlite is not None:
        con = sqlite3.connect(f"{ruta_sqlite.resolve().as_uri()}?mode=ro&immutable=1", uri=True)
        try:
            if col_filtro and col_filtro != "todas":
                cur = con.execute("SELECT fila FROM entrada WHERE col = ? ORDER BY id", (col_filtro,))
            else:
                cur = con.execute("SELECT fila FROM entrada ORDER BY id")
            filas = [json.loads(zlib.decompress(row[0]).decode("utf-8")) for row in cur]
        finally:
            con.close()
        info = {
            "fuente_datos": "mapa_corpus_sqlite",
            "revision_mapa": meta.get("revision", ""),
            "sha_fuente_hf": meta.get("sha_fuente", ""),
            "fecha_fuente_hf": meta.get("fecha_fuente", ""),
            "repo_hf": HF_REPO_DEFAULT,
        }
        return filas, info

    # Fallback sin mapa local: leer archivos JSONL versionados en data/jurisprudencia/
    archivos_por_col: Dict[str, List[str]] = {
        "cs": ["cs_sentencias.jsonl", "cs_lineas_jurisprudenciales.jsonl", "cs_salud.jsonl",
               "cs_extranjeria.jsonl", "cs_ddhh.jsonl", "pjud_genero.jsonl"],
        "tc": ["tc_sentencias.jsonl", "tc_sentencias_2anios.jsonl"],
        "ta": ["ambiental_sentencias.jsonl"],
        "baremo": ["baremo_dano_moral.jsonl"],
    }
    candidatos: List[str] = (
        archivos_por_col.get(col_filtro) or []
        if col_filtro and col_filtro != "todas"
        else [fn for lista in archivos_por_col.values() for fn in lista]
    )
    filas_local: List[Dict[str, Any]] = []
    archivos_leidos: List[str] = []
    for nombre in dict.fromkeys(candidatos):
        p = JURISP_DIR / nombre
        if not p.exists():
            continue
        archivos_leidos.append(f"data/jurisprudencia/{nombre}")
        for idx, linea in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            linea = linea.strip()
            if not linea:
                continue
            reg = json.loads(linea)
            filas_local.append({
                "id": str(reg.get("id") or f"{p.stem}:{idx}"),
                "col": col_filtro or p.stem.split("_")[0],
                "fecha": str(reg.get("fecha") or reg.get("fecha_sentencia") or ""),
                "titulo": str(reg.get("caratula") or reg.get("titulo") or reg.get("parentesco") or ""),
                "rol": str(reg.get("rol") or ""),
                "sala": str(reg.get("sala") or ""),
                "sala_txt": str(reg.get("sala") or ""),
                "recurso_txt": str(reg.get("recurso") or reg.get("tipo_recurso") or ""),
                "resultado": str(reg.get("resultado") or reg.get("decision") or ""),
                "ruta": f"data/jurisprudencia/{nombre}",
            })
    info_local = {
        "fuente_datos": "jsonl_local_respaldo",
        "archivos_leidos": archivos_leidos,
        "revision_mapa": "",
        "sha_fuente_hf": "",
        "fecha_fuente_hf": "",
        "repo_hf": HF_REPO_DEFAULT,
    }
    return filas_local, info_local


def estadisticas_longitudinales(
    coleccion: str = "cs",
    agrupacion: str = "anio",
    incluir_baremo: bool = True,
    mapa_sqlite_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Calcula estadísticas longitudinales reproducibles sobre el corpus cosechado (`cs`, `tc`, `ta`, `doc`, `todas`),
    agregando series temporales, distribución por sala/tribunal, recursos, resultados normalizados,
    tasa empírica de acogimiento (cuando corresponde) y cuantiles del Baremo Estadístico PJUD en UF/CLP.
    """
    filas, info = _iterar_entradas_corpus(coleccion=coleccion, mapa_sqlite_path=mapa_sqlite_path)
    por_periodo: Counter = Counter()
    por_coleccion: Counter = Counter()
    por_sala: Counter = Counter()
    por_recurso: Counter = Counter()
    por_resultado_norm: Counter = Counter()
    por_resultado_bruto: Counter = Counter()
    por_anio_resultado: Dict[str, Counter] = defaultdict(Counter)

    agrup = (agrupacion or "anio").strip().lower()
    for f in filas:
        por_coleccion[str(f.get("col") or "sin_coleccion")] += 1
        fecha = str(f.get("fecha") or "").strip()
        periodo = "sin_fecha"
        if len(fecha) >= 7 and fecha[:4].isdigit() and agrup == "mes":
            periodo = fecha[:7]
        elif len(fecha) >= 4 and fecha[:4].isdigit():
            periodo = fecha[:4]
        elif f.get("anio"):
            periodo = str(f["anio"])
        elif f.get("era"):
            periodo = str(f["era"])
        por_periodo[periodo] += 1

        sala = str(f.get("sala_txt") or f.get("sala") or f.get("tribunal") or "").strip()
        if sala:
            por_sala[sala] += 1

        recurso = str(f.get("recurso_txt") or f.get("recurso") or "").strip()
        if recurso:
            por_recurso[recurso] += 1

        res_raw = str(f.get("resultado") or "").strip()
        res_norm = normalizar_resultado_judicial(res_raw)
        por_resultado_norm[res_norm] += 1
        if res_raw:
            por_resultado_bruto[res_raw] += 1
        if periodo != "sin_fecha":
            por_anio_resultado[periodo][res_norm] += 1

    acoge_n = int(por_resultado_norm.get("acoge", 0))
    rechaza_n = int(por_resultado_norm.get("rechaza", 0))
    denom_resueltos = acoge_n + rechaza_n
    tasa_acogimiento = round(100.0 * acoge_n / denom_resueltos, 2) if denom_resueltos > 0 else None

    advertencias: List[str] = [
        "Efecto relativo de las sentencias (Art. 3 inc. 2 del Código Civil): los agregados reflejan "
        "tendencias empíricas del corpus indexado y no sientan precedente obligatorio general.",
    ]
    if coleccion.lower() in ("cs", "todas"):
        advertencias.append(
            "Ventana temporal Corte Suprema: la cosecha pública PJUD concentra los últimos 2 años de "
            "fallos publicados (~70.523 sentencias); los registros con fecha anterior corresponden a causas "
            "históricas o portales temáticos y no representan un censo histórico uniforme."
        )
    if info["fuente_datos"] == "jsonl_local_respaldo":
        advertencias.append(
            "Mapa del corpus local (`mapa.sqlite`) no activo: las estadísticas se calcularon sobre los "
            "archivos JSONL locales de respaldo (`data/jurisprudencia/`). Para el universo completo (~82.674 "
            "archivos) active el mapa del corpus."
        )

    salida: Dict[str, Any] = {
        "coleccion": coleccion,
        "agrupacion": agrup,
        "universo_n": len(filas),
        "trazabilidad": info,
        "distribucion_colecciones": dict(por_coleccion.most_common()),
        "serie_temporal": dict(sorted(por_periodo.items())),
        "distribucion_salas_o_tribunales": dict(por_sala.most_common(12)),
        "top_recursos": dict(por_recurso.most_common(12)),
        "distribucion_resultados_normalizados": dict(por_resultado_norm.most_common()),
        "top_resultados_originales": dict(por_resultado_bruto.most_common(10)),
        "tasa_acogimiento_sobre_acoge_o_rechaza_pct": tasa_acogimiento,
        "base_tasa_acogimiento": {"acoge": acoge_n, "rechaza": rechaza_n, "denominador": denom_resueltos},
        "serie_resultados_por_periodo": {
            k: dict(v) for k, v in sorted(por_anio_resultado.items())[-12:]
        },
        "advertencias_metodologicas": advertencias,
    }
    if incluir_baremo:
        salida["baremo_dano_moral_uf_clp"] = _cargar_baremo_local()
    return salida


def generar_muestra_validacion_humana(
    coleccion: str = "cs",
    n: int = 100,
    semilla: int = 42,
    estratificar_por: str = "sala",
    mapa_sqlite_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Genera una muestra aleatoria estratificada determinista (fijada por `semilla`) para validación
    humana ciega por doble codificador (precisión, cobertura, F1 y coeficiente κ de Cohen),
    requisito metodológico para publicaciones empíricas en revistas jurídicas arbitradas.
    """
    filas, info = _iterar_entradas_corpus(coleccion=coleccion, mapa_sqlite_path=mapa_sqlite_path)
    n_objetivo = max(1, min(int(n), len(filas))) if filas else 0
    if n_objetivo == 0:
        return {
            "coleccion": coleccion,
            "semilla": semilla,
            "n_solicitado": n,
            "n_obtenido": 0,
            "trazabilidad": info,
            "muestra": [],
        }

    def _clave_estrato(f: Dict[str, Any]) -> str:
        if estratificar_por == "anio":
            fecha = str(f.get("fecha") or "")
            return fecha[:4] if len(fecha) >= 4 and fecha[:4].isdigit() else "sin_anio"
        if estratificar_por == "resultado":
            return normalizar_resultado_judicial(str(f.get("resultado") or ""))
        return str(f.get("sala_txt") or f.get("sala") or f.get("tribunal") or f.get("col") or "general").strip()

    estratos: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for f in filas:
        estratos[_clave_estrato(f)].append(f)

    rng = random.Random(int(semilla))
    total = len(filas)
    elegidos: List[Tuple[str, Dict[str, Any]]] = []
    restantes: List[Tuple[str, Dict[str, Any]]] = []

    for nombre_est in sorted(estratos):
        grupo = sorted(estratos[nombre_est], key=lambda r: str(r.get("id") or ""))
        rng.shuffle(grupo)
        cuota = max(1, round(n_objetivo * (len(grupo) / total))) if n_objetivo >= len(estratos) else int(n_objetivo * (len(grupo) / total))
        cuota = min(cuota, len(grupo))
        elegidos.extend((nombre_est, item) for item in grupo[:cuota])
        restantes.extend((nombre_est, item) for item in grupo[cuota:])

    # Ajustar exacto a n_objetivo manteniendo determinismo
    if len(elegidos) > n_objetivo:
        rng.shuffle(elegidos)
        elegidos = elegidos[:n_objetivo]
    elif len(elegidos) < n_objetivo and restantes:
        rng.shuffle(restantes)
        elegidos.extend(restantes[: n_objetivo - len(elegidos)])

    elegidos.sort(key=lambda pair: (pair[0], str(pair[1].get("id") or "")))
    sha = info.get("sha_fuente_hf") or "main"
    muestra_filas: List[Dict[str, Any]] = []
    conteo_estratos: Counter = Counter()
    for idx, (estrato, f) in enumerate(elegidos, 1):
        conteo_estratos[estrato] += 1
        ruta = str(f.get("ruta") or "")
        url_hf = f"https://huggingface.co/datasets/{HF_REPO_DEFAULT}/blob/{sha}/{ruta}" if ruta else ""
        muestra_filas.append({
            "orden_muestra": idx,
            "id": str(f.get("id") or ""),
            "coleccion": str(f.get("col") or coleccion),
            "estrato": estrato,
            "fecha": str(f.get("fecha") or ""),
            "rol": str(f.get("rol") or ""),
            "titulo": str(f.get("titulo") or "")[:160],
            "recurso": str(f.get("recurso_txt") or f.get("recurso") or ""),
            "resultado_automatico": normalizar_resultado_judicial(str(f.get("resultado") or "")),
            "resultado_original": str(f.get("resultado") or ""),
            "ruta": ruta,
            "url_huggingface": url_hf,
            "codificador_1_resultado": "",
            "codificador_2_resultado": "",
            "codificador_1_normas_ok": "",
            "codificador_2_normas_ok": "",
            "observaciones": "",
        })

    return {
        "coleccion": coleccion,
        "estratificar_por": estratificar_por,
        "semilla": int(semilla),
        "universo_n": total,
        "n_obtenido": len(muestra_filas),
        "estratos_muestra": dict(conteo_estratos.most_common()),
        "trazabilidad": info,
        "protocolo_validacion": {
            "metricas_recomendadas": ["Precisión (Precision)", "Cobertura (Recall)", "Puntaje F1", "Coeficiente κ de Cohen"],
            "umbral_publicacion_sugerido": "κ de Cohen >= 0,80 y F1 >= 0,85 sobre extracción de normas y resultados",
            "instrucciones": (
                "Entregar la plantilla CSV a dos revisores jurídicos independientes sin exponer la columna "
                "«resultado_automatico» durante la codificación ciega; luego calcular concordancia intercodificador."
            ),
        },
        "muestra": muestra_filas,
    }


def _valor_graphml(v: Any) -> Any:
    """Convierte atributos de nodo/arista a escalares válidos para el estándar GraphML."""
    if v is None:
        return ""
    if isinstance(v, (bool, int, float, str)):
        return v
    return json.dumps(v, ensure_ascii=False)


def _escribir_parquet_si_disponible(ruta: Path, filas: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """Escribe un archivo Apache Parquet si `pyarrow` está instalado; degrada limpiamente si no."""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        return False, "pyarrow no está instalado (instale el extra `pip install openlegal-chile[analytics]`)"
    if not filas:
        return False, "tabla vacía"
    columnas = list(filas[0].keys())
    datos_col = {c: [f.get(c) for f in filas] for c in columnas}
    tabla = pa.table(datos_col)
    pq.write_table(tabla, str(ruta), compression="snappy")
    return True, f"{len(filas)} filas ({ruta.stat().st_size:,} bytes)"


def exportar_paquete_investigacion(
    tema: str,
    carpeta_salida: str,
    formatos: Optional[Sequence[str]] = None,
    incluir_muestra_validacion: bool = True,
    n_muestra: int = 50,
    semilla: int = 42,
    coleccion_longitudinal: str = "cs",
    motor: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Genera un paquete reproducible de investigación jurídica académica para el `tema` indicado:
    - `nodos_subgrafo.csv` y `aristas_subgrafo.csv` (para R, Stata, SPSS y Python)
    - `red_citaciones.graphml` (para Gephi y Cytoscape)
    - `nodos_subgrafo.parquet` y `aristas_subgrafo.parquet` (si `pyarrow` está disponible)
    - `estadisticas_longitudinales.json` y `muestra_validacion_humana.csv`
    - `METODOLOGIA_REPRODUCIBLE.md` (con firma institucional Open Legal Chile y normas RAE/ASALE)
    - `referencia.bib` (citas BibTeX listas para artículos académicos y tesis).
    """
    from legal_graphify import (
        es_arista_sustantiva,
        obtener_motor_compartido,
        peso_multiplex,
    )

    dest = Path(carpeta_salida).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)
    fmts = {f.strip().lower() for f in (formatos or ("csv", "graphml", "parquet", "json", "md", "bib"))}

    eng = motor if motor is not None else obtener_motor_compartido()
    eng._preparar_consulta()
    g: nx.DiGraph = eng.graph

    tema_clean = (tema or "").strip()
    nodo_centro: Optional[str] = None
    if tema_clean and tema_clean not in ("*", "corpus", "todo"):
        nodo_centro = eng._buscar_nodo_relevante(tema_clean)

    # Extraer subgrafo sustantivo acotado (máx. 500 nodos)
    sub_nodos: Set[str] = set()
    if nodo_centro and g.has_node(nodo_centro):
        r1 = set(g.successors(nodo_centro)) | set(g.predecessors(nodo_centro)) | {nodo_centro}
        sub_nodos.update(r1)
        for v in sorted(r1):
            if len(sub_nodos) >= 500:
                break
            vec = sorted(set(g.successors(v)) | set(g.predecessors(v)))
            for w in vec[:25]:
                sub_nodos.add(w)
                if len(sub_nodos) >= 500:
                    break
    else:
        # Subgrafo top-300 por grado sustantivo si el tema es panorámico o no coincide con un único nodo
        grados = sorted(((g.degree(n), n) for n in g.nodes()), reverse=True)
        sub_nodos = {n for _, n in grados[:300]}

    sub = g.subgraph(sorted(sub_nodos)).copy()
    filas_nodos: List[Dict[str, Any]] = []
    for nid in sorted(sub.nodes()):
        nd = sub.nodes[nid]
        filas_nodos.append({
            "id": str(nid),
            "label": str(nd.get("label") or nid),
            "node_type": str(nd.get("node_type") or ""),
            "capa": str(nd.get("capa") or "repo"),
            "community": str(nd.get("community") if nd.get("community") is not None else ""),
            "area": str(nd.get("area") or ""),
            "autor": str(nd.get("autor") or ""),
            "obra": str(nd.get("obra") or ""),
            "id_mapa": str(nd.get("id_mapa") or ""),
            "grado_subgrafo": int(sub.degree(nid)),
            "grado_total": int(g.degree(nid)),
        })

    filas_aristas: List[Dict[str, Any]] = []
    for u, v, d in sorted(sub.edges(data=True), key=lambda e: (str(e[0]), str(e[1]))):
        sust = es_arista_sustantiva(u, v, d, g)
        filas_aristas.append({
            "source": str(u),
            "target": str(v),
            "relation": str(d.get("relation") or ""),
            "capa": str(d.get("capa") or "repo"),
            "es_sustantiva": bool(sust),
            "weight": float(d.get("weight") or 1.0),
            "peso_multiplex": float(peso_multiplex(u, v, d, g)),
        })

    archivos_generados: Dict[str, str] = {}
    advertencias: List[str] = []

    if "csv" in fmts:
        p_nodos_csv = dest / "nodos_subgrafo.csv"
        with p_nodos_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(filas_nodos[0].keys()) if filas_nodos else ["id"])
            writer.writeheader()
            writer.writerows(filas_nodos)
        archivos_generados["nodos_csv"] = str(p_nodos_csv)

        p_aristas_csv = dest / "aristas_subgrafo.csv"
        with p_aristas_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=list(filas_aristas[0].keys()) if filas_aristas else ["source", "target", "relation"],
            )
            writer.writeheader()
            writer.writerows(filas_aristas)
        archivos_generados["aristas_csv"] = str(p_aristas_csv)

    if "graphml" in fmts:
        gml = nx.DiGraph()
        for n_row in filas_nodos:
            nid = n_row["id"]
            gml.add_node(nid, **{k: _valor_graphml(val) for k, val in n_row.items() if k != "id"})
        for e_row in filas_aristas:
            gml.add_edge(
                e_row["source"],
                e_row["target"],
                **{k: _valor_graphml(val) for k, val in e_row.items() if k not in ("source", "target")},
            )
        p_gml = dest / "red_citaciones.graphml"
        nx.write_graphml(gml, str(p_gml))
        archivos_generados["graphml"] = str(p_gml)

    if "parquet" in fmts:
        ok_n, msg_n = _escribir_parquet_si_disponible(dest / "nodos_subgrafo.parquet", filas_nodos)
        if ok_n:
            archivos_generados["nodos_parquet"] = str(dest / "nodos_subgrafo.parquet")
        else:
            advertencias.append(f"Parquet nodos omitido: {msg_n}")
        ok_a, msg_a = _escribir_parquet_si_disponible(dest / "aristas_subgrafo.parquet", filas_aristas)
        if ok_a:
            archivos_generados["aristas_parquet"] = str(dest / "aristas_subgrafo.parquet")
        else:
            advertencias.append(f"Parquet aristas omitido: {msg_a}")

    red_stats = analizar_red_citaciones(
        motor=eng,
        norma_filtro=tema_clean if (nodo_centro and g.has_node(nodo_centro)) else None,
        top_k=15,
    )
    long_stats = estadisticas_longitudinales(coleccion=coleccion_longitudinal, incluir_baremo=True)
    if "json" in fmts:
        p_stats = dest / "estadisticas_longitudinales.json"
        p_stats.write_text(
            json.dumps({"red_citaciones": red_stats, "longitudinal": long_stats}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        archivos_generados["estadisticas_json"] = str(p_stats)

    muestra_info: Dict[str, Any] = {}
    if incluir_muestra_validacion:
        muestra_info = generar_muestra_validacion_humana(
            coleccion=coleccion_longitudinal,
            n=n_muestra,
            semilla=semilla,
        )
        if muestra_info.get("muestra"):
            p_muestra = dest / "muestra_validacion_humana.csv"
            with p_muestra.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(muestra_info["muestra"][0].keys()))
                writer.writeheader()
                writer.writerows(muestra_info["muestra"])
            archivos_generados["muestra_validacion_csv"] = str(p_muestra)

    traz = long_stats.get("trazabilidad") or {}
    sha_hf = str(traz.get("sha_fuente_hf") or "sin_mapa_local")
    fecha_hf = str(traz.get("fecha_fuente_hf") or _dt.date.today().isoformat())
    anio_actual = _dt.date.today().year
    hoy_iso = _dt.date.today().isoformat()

    if "bib" in fmts:
        bib_texto = (
            f"@misc{{openlegalchile_dataset_{anio_actual},\n"
            f"  author       = {{Benavides Jorquera, Pablo and {{Open Legal Chile Contributors}}}},\n"
            f"  title        = {{{{Corpus Jurídico, Doctrinal y Jurisprudencial de Chile (Open Legal Chile)}}}},\n"
            f"  year         = {{{anio_actual}}},\n"
            f"  publisher    = {{Hugging Face Datasets}},\n"
            f"  howpublished = {{\\url{{https://huggingface.co/datasets/{HF_REPO_DEFAULT}}}}},\n"
            f"  note         = {{Revisión fijada (SHA): {sha_hf}; consultado el {hoy_iso}}}\n"
            f"}}\n\n"
            f"@software{{openlegalchile_suite_{anio_actual},\n"
            f"  author       = {{Benavides Jorquera, Pablo}},\n"
            f"  title        = {{{{Open Legal Chile: Suite de Inteligencia Jurídica y Grafo LegalGraphify}}}},\n"
            f"  year         = {{{anio_actual}}},\n"
            f"  license      = {{Apache-2.0}},\n"
            f"  url          = {{https://github.com/elpabloultron/open-legal-chile}}\n"
            f"}}\n"
        )
        p_bib = dest / "referencia.bib"
        p_bib.write_text(bib_texto, encoding="utf-8")
        archivos_generados["bibtex"] = str(p_bib)

    if "md" in fmts:
        etiqueta_centro = str(g.nodes[nodo_centro].get("label", nodo_centro)) if (nodo_centro and g.has_node(nodo_centro)) else tema_clean or "Corpus completo"
        metodologia_md = f"""# OPEN LEGAL CHILE — Memoria Metodológica Reproducible

**Tema de investigación:** «{etiqueta_centro}»
**Fecha de generación:** {hoy_iso}
**Origen del grafo:** `{getattr(eng, 'origen_grafo', 'repo')}`
**Repositorio de datos (Hugging Face):** `https://huggingface.co/datasets/{HF_REPO_DEFAULT}`
**Revisión fijada del dataset (SHA):** `{sha_hf}` (fecha fuente: `{fecha_hf}`)

---

## I. Universo de Datos y Trazabilidad

- **Nodos en el subgrafo exportado:** {len(filas_nodos):,}
- **Aristas en el subgrafo exportado:** {len(filas_aristas):,} ({sum(1 for a in filas_aristas if a['es_sustantiva']):,} sustantivas y {sum(1 for a in filas_aristas if not a['es_sustantiva']):,} bibliográficas)
- **Universo longitudinal consultado (`{coleccion_longitudinal}`):** N = {long_stats.get('universo_n', 0):,} registros (`{traz.get('fuente_datos', 'local')}`)
- **Muestra de validación humana ciega:** n = {muestra_info.get('n_obtenido', 0)} (semilla determinista `seed={semilla}`)

## II. Arquitectura de Red Multiplex

El grafo distingue expresamente entre **aristas jurídicas sustantivas** (`cita_norma`, `cita_rol`, `fundamenta_en`, `aplica_norma`, `criterio_jurisprudencial`, `resuelto_por`, `similar_semantico`) con peso `1,0` y **aristas bibliográficas o editoriales** (`contenido_en`, `analizado_por`, `escrito_por`, `publicado_en`) atenuadas a `0,04`. Esta separación impide que súper-hubs editoriales distorsionen las métricas de centralidad (PageRank dirigido y HITS Authority/Hub).

## III. Limitaciones y Advertencias Metodológicas

1. **Principio de legalidad y efecto relativo de las sentencias:** En el sistema de Derecho Continental chileno (Art. 1 y Art. 3 inc. 2 del Código Civil), las redes de citación jurisprudencial miden convergencia argumentativa empírica y no obligatoriedad general del precedente.
2. **Ventana temporal de la Corte Suprema:** La colección pública cosechada desde PJUD concentra los últimos 2 años (~70 523 sentencias); toda inferencia longitudinal anterior a ese período debe acotarse a los portales temáticos especializados o a colecciones históricas complementarias.
3. **Auditoría OCR y validación humana:** Las citas extraídas automáticamente desde PDFs históricos pueden contener artefactos numéricos; este módulo filtra artículos fuera de rango normativo y genera la plantilla `muestra_validacion_humana.csv` para estimar precisión, cobertura, F1 y coeficiente κ de Cohen mediante doble codificación independiente.

## IV. Archivos Incluidos en el Paquete

""" + "\n".join(f"- **{k}:** `{Path(v).name}`" for k, v in sorted(archivos_generados.items())) + """

---
*Open Legal Chile — Un proyecto open source · Desarrollado por Pablo Benavides J. · Web: https://elpabloultron.github.io/open-legal-chile/*
"""
        p_md = dest / "METODOLOGIA_REPRODUCIBLE.md"
        p_md.write_text(metodologia_md, encoding="utf-8")
        archivos_generados["metodologia_md"] = str(p_md)

    return {
        "tema": tema_clean,
        "nodo_central": nodo_centro,
        "carpeta_salida": str(dest),
        "nodos_exportados": len(filas_nodos),
        "aristas_exportadas": len(filas_aristas),
        "sha_fuente_hf": sha_hf,
        "archivos": archivos_generados,
        "advertencias": advertencias,
    }
