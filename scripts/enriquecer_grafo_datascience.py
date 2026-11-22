#!/usr/bin/env python3
"""
Open Legal Chile — Enriquecimiento Data Science del Knowledge Graph (`scripts/enriquecer_grafo_datascience.py`)

Resuelve el principal cuello de botella detectado en la auditoría topológica del grafo curado:
el 96 % de los 10.040 nodos `institucion` solo tenía aristas bibliográficas (`obra` / `autor`),
sin enlaces sustantivos hacia normas positivas (BCN) ni jurisprudencia.

Qué hace este script (100 % determinista, offline y trazable):
1. Cruza cada nodo `institucion` sin enlaces sustantivos contra `doctrina.db` (18.749 fichas limpias).
2. Extrae citas normativas canónicas con `citas_legales.normas_canonicas()` y filtra artefactos OCR
   fuera de rango con `jurimetria.es_articulo_plausible()`.
3. Reutiliza los nodos `articulo_legal` existentes mediante resolución ontológica (`norma_de_etiqueta`)
   para evitar duplicación, y crea nodos canónicos limpios cuando la norma aún no existía.
4. Extrae citas de roles judiciales (`citas_legales.roles_canonicos`) y conecta las instituciones con
   los nodos de jurisprudencia existentes o nuevos (cuando el rol es inequívoco y verificado).
5. Etiqueta `id_canonico` en los nodos `articulo_legal` existentes sin borrar nodos curados ni alterar
   instituciones ya curadas (preserva determinismo de `simulacion` y compatibilidad con `mapa_corpus`).
6. Opcionalmente ejecuta enlace semántico latente (`--semantic`) para descubrir aristas `similar_semantico`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from citas_legales import etiqueta_norma, normas_canonicas, roles_canonicos
from jurimetria import es_articulo_plausible
from legal_graphify import (
    DEFAULT_GRAPH_PATH,
    LegalGraphifyEngine,
    _TIPOS_NORMA,
    _TIPOS_SENTENCIA,
    _normalize_str,
    _sanitize_id,
    es_nodo_ruido_institucion,
)
from mapa_corpus.grafo import norma_de_etiqueta

DOCTRINA_DB = RAIZ / "doctrina.db"
MAX_NORMAS_POR_INST = 12
MAX_ROLES_POR_INST = 5


def _cargar_indice_doctrina_db(db_path: Path) -> Dict[str, Tuple[str, str, str]]:
    """Indexa `doctrina.db` por título normalizado de institución → (texto_completo, concordancias, fallo_rector)."""
    if not db_path.exists():
        return {}
    con = sqlite3.connect(str(db_path))
    indice: Dict[str, Tuple[str, str, str]] = {}
    try:
        cur = con.execute(
            "SELECT institucion, definicion, contenido, operativa_procesal, concordancias, fallo_rector "
            "FROM doctrina_instituciones"
        )
        for inst, defin, cont, op, conc, fallo in cur:
            clave = _normalize_str(str(inst or ""))
            if not clave:
                continue
            texto = "\n".join(str(x or "") for x in (defin, cont, op, conc, fallo) if x)
            previo = indice.get(clave)
            # Conservar la fila más completa si la misma institución aparece dos veces
            if previo is None or len(texto) > len(previo[0]):
                indice[clave] = (texto, str(conc or ""), str(fallo or ""))
    finally:
        con.close()
    return indice


def _medir_cobertura_instituciones(eng: LegalGraphifyEngine) -> Dict[str, Any]:
    g = eng.graph
    inst_total = 0
    con_norma = 0
    con_jurisp = 0
    solo_bib = 0
    tipos_norma = set(_TIPOS_NORMA)
    tipos_sent = set(_TIPOS_SENTENCIA)
    for nid, nd in g.nodes(data=True):
        if nd.get("node_type") != "institucion":
            continue
        inst_total += 1
        vec = set(g.successors(nid)) | set(g.predecessors(nid))
        ts = {str(g.nodes[v].get("node_type") or "") for v in vec}
        has_n = bool(ts & tipos_norma)
        has_j = bool(ts & tipos_sent)
        if has_n:
            con_norma += 1
        if has_j:
            con_jurisp += 1
        if not has_n and not has_j:
            solo_bib += 1
    return {
        "nodos_totales": g.number_of_nodes(),
        "aristas_totales": g.number_of_edges(),
        "instituciones_totales": inst_total,
        "instituciones_con_norma": con_norma,
        "instituciones_con_norma_pct": round(100.0 * con_norma / max(1, inst_total), 2),
        "instituciones_con_jurisprudencia": con_jurisp,
        "instituciones_con_jurisprudencia_pct": round(100.0 * con_jurisp / max(1, inst_total), 2),
        "instituciones_solo_bibliograficas": solo_bib,
        "instituciones_solo_bibliograficas_pct": round(100.0 * solo_bib / max(1, inst_total), 2),
    }


def _extraer_ids_roles(texto: str) -> List[str]:
    """Normaliza la salida de `roles_canonicos(texto)` (puede ser tuplas `(id, n)` o `str`)."""
    salida: List[str] = []
    vistos: Set[str] = set()
    for item in roles_canonicos(texto):
        rid = str(item[0] if isinstance(item, (tuple, list)) else item)
        if rid and rid not in vistos:
            vistos.add(rid)
            salida.append(rid)
    return salida


def _indexar_roles_existentes(eng: LegalGraphifyEngine) -> Dict[str, str]:
    """Mapea ID canónico de rol (`cs:1234-2023`, `tc:2402`, `ta:...`) a nodos de jurisprudencia existentes."""
    mapa: Dict[str, str] = {}
    for nid, nd in sorted(eng.graph.nodes(data=True)):
        nt = str(nd.get("node_type") or "")
        if nt not in _TIPOS_SENTENCIA:
            continue
        texto_rol = f"{nd.get('rol') or ''} {nd.get('label') or ''}"
        for rid in _extraer_ids_roles(texto_rol):
            mapa.setdefault(rid, nid)
    return mapa


def _etiqueta_rol(rid: str) -> str:
    if rid.startswith("cs:"):
        return f"CS - Rol N.° {rid[3:]}"
    if rid.startswith("tc:"):
        return f"TC - Rol N.° {rid[3:]}"
    if rid.startswith("ta:"):
        partes = rid.split(":", 2)
        if len(partes) == 3:
            return f"{partes[1].upper()} - Rol {partes[2]}"
    return rid


def enriquecer_grafo(
    graph_path: str = DEFAULT_GRAPH_PATH,
    db_path: Path = DOCTRINA_DB,
    dry_run: bool = False,
    podar_ruido: bool = True,
    incluir_semantico: bool = False,
    max_nodos_semanticos: int = 350,
    umbral_semantico: float = 0.80,
) -> Dict[str, Any]:
    """Ejecuta el enriquecimiento determinista del grafo curado (con poda opcional de nodos ruido TOC/OCR)
    y devuelve el reporte antes/después."""
    eng = LegalGraphifyEngine(usar_mapa=False)
    if not eng.cargar_grafo_json(graph_path):
        raise RuntimeError(f"No se pudo cargar el grafo base desde {graph_path}")

    antes = _medir_cobertura_instituciones(eng)
    g = eng.graph

    # 1. Resolución ontológica de nodos de norma existentes: `canon_id -> node_id`
    canon_a_norma: Dict[str, str] = {}
    etiquetados_canon = 0
    for nid in sorted(g.nodes()):
        nd = g.nodes[nid]
        if nd.get("node_type") in ("articulo_legal", "cuerpo_legal"):
            canon = str(nd.get("id_canonico") or "") or norma_de_etiqueta(str(nd.get("label") or ""))
            if canon:
                if not nd.get("id_canonico"):
                    nd["id_canonico"] = canon
                    etiquetados_canon += 1
                canon_a_norma.setdefault(canon, nid)

    roles_existentes = _indexar_roles_existentes(eng)
    indice_db = _cargar_indice_doctrina_db(db_path)

    # 2. Enlazar instituciones huérfanas (sin norma ni jurisprudencia) contra doctrina.db + su propia etiqueta
    tipos_norma = set(_TIPOS_NORMA)
    tipos_sent = set(_TIPOS_SENTENCIA)
    nodos_norma_creados = 0
    aristas_norma_creadas = 0
    nodos_rol_creados = 0
    aristas_rol_creadas = 0
    normas_descartadas_ocr = 0
    inst_enriquecidas = 0
    nodos_ruido_podados = 0

    roles_por_inst: Dict[str, List[str]] = {}
    freq_roles: Counter = Counter()

    for nid in sorted(g.nodes()):
        nd = g.nodes[nid]
        if nd.get("node_type") != "institucion":
            continue
        vec = set(g.successors(nid)) | set(g.predecessors(nid))
        ts = {str(g.nodes[v].get("node_type") or "") for v in vec}
        tiene_norma = bool(ts & tipos_norma)
        tiene_jurisp = bool(ts & tipos_sent)
        if tiene_norma and tiene_jurisp:
            continue  # Ya curada por completo: no tocar (preserva determinismo de `simulacion`, etc.)

        clave_lbl = _normalize_str(str(nd.get("label") or ""))
        fila_db = indice_db.get(clave_lbl)
        texto_nodo = " ".join(
            str(nd.get(k) or "") for k in ("label", "definicion", "operativa_procesal", "materia")
        )
        texto = f"{texto_nodo}\n{fila_db[0]}" if fila_db else texto_nodo
        if len(texto.strip()) < 15:
            continue

        enriquecida = False
        if not tiene_norma:
            citas_norma = normas_canonicas(texto)
            validas: List[Tuple[str, int]] = []
            for cid, cnt in citas_norma:
                if not es_articulo_plausible(cid):
                    normas_descartadas_ocr += 1
                    continue
                # Priorizar artículos específicos (`norma:cc:1545`) sobre menciones genéricas del código completo
                validas.append((cid, int(cnt)))
            validas.sort(key=lambda pair: (-(1 if pair[0].count(":") >= 2 else 0), -pair[1], pair[0]))

            for cid, cnt in validas[:MAX_NORMAS_POR_INST]:
                norma_nid = canon_a_norma.get(cid)
                if norma_nid is None:
                    norma_nid = _sanitize_id(cid.replace(":", "_"), "norma")
                    if not g.has_node(norma_nid):
                        etiqueta = etiqueta_norma(cid)
                        nt_nuevo = "articulo_legal" if cid.count(":") >= 2 else "cuerpo_legal"
                        g.add_node(
                            norma_nid,
                            label=etiqueta,
                            node_type=nt_nuevo,
                            id_canonico=cid,
                            community=2,
                            origen="enriquecimiento_ds",
                        )
                        nodos_norma_creados += 1
                    canon_a_norma[cid] = norma_nid
                if not g.has_edge(nid, norma_nid):
                    g.add_edge(
                        nid,
                        norma_nid,
                        relation="fundamenta_en",
                        weight=round(min(5.0, float(cnt)), 2),
                        origen="enriquecimiento_ds",
                    )
                    aristas_norma_creadas += 1
                    enriquecida = True

        if not tiene_jurisp:
            rids = _extraer_ids_roles(texto)
            if rids:
                roles_por_inst[nid] = rids[:MAX_ROLES_POR_INST]
                for rid in rids[:MAX_ROLES_POR_INST]:
                    freq_roles[rid] += 1

        if enriquecida:
            inst_enriquecidas += 1

    # Vincular jurisprudencia verificada (roles existentes en el grafo o citados por >= 1 institución)
    for nid, rids in sorted(roles_por_inst.items()):
        for rid in rids:
            if rid not in roles_existentes and freq_roles[rid] < 1:
                continue
            j_nid = roles_existentes.get(rid)
            if j_nid is None:
                j_nid = _sanitize_id(rid.replace(":", "_"), "fallo")
                if not g.has_node(j_nid):
                    nt_j = "jurisprudencia_tc" if rid.startswith("tc:") else "jurisprudencia"
                    g.add_node(
                        j_nid,
                        label=_etiqueta_rol(rid),
                        node_type=nt_j,
                        id_canonico=rid,
                        rol=rid.split(":", 1)[-1],
                        community=3,
                        origen="enriquecimiento_ds",
                    )
                    nodos_rol_creados += 1
                roles_existentes[rid] = j_nid
            if not g.has_edge(nid, j_nid):
                g.add_edge(
                    nid,
                    j_nid,
                    relation="criterio_jurisprudencial",
                    weight=1.0,
                    origen="enriquecimiento_ds",
                )
                aristas_rol_creadas += 1

    # 3. Poda quirúrgica de nodos ruido (líneas TOC, notas al pie, créditos editoriales, OCR basura)
    #    SOLO cuando carecen por completo de enlaces normativos y jurisprudenciales tras el paso 2.
    if podar_ruido:
        a_podar: List[str] = []
        for nid in sorted(g.nodes()):
            nd = g.nodes[nid]
            if nd.get("node_type") != "institucion":
                continue
            vec = set(g.successors(nid)) | set(g.predecessors(nid))
            ts = {str(g.nodes[v].get("node_type") or "") for v in vec}
            if ts & (tipos_norma | tipos_sent):
                continue
            if es_nodo_ruido_institucion(
                str(nd.get("label") or ""),
                str(nd.get("definicion") or ""),
                str(nd.get("obra") or ""),
            ):
                a_podar.append(nid)
        g.remove_nodes_from(a_podar)
        nodos_ruido_podados = len(a_podar)
        # Retirar obras editoriales vacías si quedaron sin instituciones (ej. doctrina48981)
        obras_vacias = [
            nid for nid, nd in list(g.nodes(data=True))
            if nd.get("node_type") == "obra" and g.in_degree(nid) == 0 and str(nd.get("label") or "") == "doctrina48981"
        ]
        g.remove_nodes_from(obras_vacias)

    res_sem: Dict[str, Any] = {}
    if incluir_semantico:
        res_sem = eng.enriquecer_aristas_semanticas(
            max_nodos=max_nodos_semanticos,
            top_k=2,
            umbral=umbral_semantico,
            solo_sin_enlaces_sustantivos=True,
        )

    despues = _medir_cobertura_instituciones(eng)
    if not dry_run:
        eng.guardar_grafo_json(graph_path)

    return {
        "graph_path": str(graph_path),
        "dry_run": dry_run,
        "antes": antes,
        "despues": despues,
        "delta": {
            "instituciones_enriquecidas_con_norma": inst_enriquecidas,
            "nodos_norma_etiquetados_id_canonico": etiquetados_canon,
            "nodos_norma_creados": nodos_norma_creados,
            "aristas_norma_creadas": aristas_norma_creadas,
            "nodos_rol_creados": nodos_rol_creados,
            "aristas_rol_creadas": aristas_rol_creadas,
            "normas_ocr_descartadas": normas_descartadas_ocr,
            "nodos_ruido_podados": nodos_ruido_podados,
            "aristas_semanticas": res_sem,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Enriquecimiento Data Science del Knowledge Graph de Open Legal Chile")
    parser.add_argument("--graph", default=DEFAULT_GRAPH_PATH, help="Ruta al grafo JSON curado")
    parser.add_argument("--db", default=str(DOCTRINA_DB), help="Ruta a doctrina.db")
    parser.add_argument("--dry-run", action="store_true", help="Mide sin escribir en disco")
    parser.add_argument("--sin-podar-ruido", action="store_true", help="Omite la poda de nodos TOC/OCR")
    parser.add_argument("--semantic", action="store_true", help="Agregar también aristas semánticas latentes")
    parser.add_argument("--max-semantic", type=int, default=350, help="Máximo de nodos huérfanos para enlace semántico")
    parser.add_argument("--umbral-semantic", type=float, default=0.80, help="Umbral coseno para aristas semánticas")
    args = parser.parse_args()

    reporte = enriquecer_grafo(
        graph_path=args.graph,
        db_path=Path(args.db),
        dry_run=args.dry_run,
        podar_ruido=not args.sin_podar_ruido,
        incluir_semantico=args.semantic,
        max_nodos_semanticos=args.max_semantic,
        umbral_semantico=args.umbral_semantic,
    )
    print(json.dumps(reporte, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
