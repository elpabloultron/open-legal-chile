#!/usr/bin/env python3
"""
Open Legal Chile — Integra la jurisprudencia nueva al gran mapa de relaciones.

Añade al grafo (data/legal_knowledge_graph.json):
  · las 966 sentencias del Tribunal Constitucional (últimos 2 años) con su texto en Markdown,
    enlazadas al órgano y a las normas que citan;
  · las publicaciones oficiales de los Tribunales Ambientales (anuarios y boletines) con su
    texto en Markdown, enlazadas al tribunal y a las normas que citan;
  · recalcula las comunidades con el mismo algoritmo del motor (modularidad voraz).

Uso:
    python scripts/integrar_jurisprudencia_al_grafo.py [--sin-comunidades]
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import pathlib
import re
import shutil
import sys
import tempfile
import time
import unicodedata

import networkx as nx

BASE = pathlib.Path(__file__).resolve().parent.parent
GRAFO = BASE / "data" / "legal_knowledge_graph.json"
TC_INDICE = BASE / "data" / "jurisprudencia" / "tc_textos.jsonl"
PUB_INDICE = BASE / "data" / "jurisprudencia" / "publicaciones_textos.jsonl"


def _cargar_modulo(nombre: str, ruta: pathlib.Path):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    if not spec or not spec.loader:
        raise RuntimeError(f"no se pudo cargar {ruta}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sin_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def slug(texto: str) -> str:
    t = sin_acentos(texto.lower())
    t = re.sub(r"[^a-z0-9]+", "_", t)
    return t.strip("_")[:90]


def indices_de_normas(nodos: list[dict]) -> tuple[dict[tuple, str], dict[str, str]]:
    """Índices del grafo existente: (código, artículo) → nodo, y ley → nodo."""
    idx: dict[tuple, str] = {}
    leyes: dict[str, str] = {}
    for n in nodos:
        nid = str(n.get("id", ""))
        if not nid.startswith("norma_"):
            continue
        m = re.match(r"norma_([a-z_]+?)_art_(\d+)(?:_[a-z]+)?$", nid)
        if m:
            idx.setdefault((m.group(1), m.group(2)), nid)
            continue
        m = re.match(r"norma_art_(\d+)_([a-z]+)$", nid)
        if m:
            idx.setdefault((m.group(2), m.group(1)), nid)
            continue
        m = re.match(r"norma_ley_(\d+)$", nid)
        if m:
            leyes.setdefault(m.group(1), nid)
    return idx, leyes


# siglas del extractor de citas (scripts/optimizar_catalogo_hf.py) → claves del grafo
SIGLAS = {
    "CC": ("codigo_civil", "cc"), "CP": ("codigo_penal", "cp"),
    "CT": ("codigo_del_trabajo", "ct"), "CPC": ("codigo_de_procedimiento_civil", "cpc"),
    "CPP": ("codigo_de_procedimiento_penal", "cpp"), "CPP2": ("codigo_de_procedimiento_penal", "cpp"),
    "COT": ("codigo_organico_de_tribunales", "cot"), "CPR": ("cpr", "constitucion"),
    "CTRIB": ("codigo_tributario", "ctrib"), "LDC": ("ley_19496", "ldc"),
}


def normas_citadas(texto: str, claves_mod, idx_normas: dict[tuple, str], idx_leyes: dict[str, str],
                   tope: int = 25) -> list[str]:
    """Hasta `tope` nodos de norma citados en el texto (por frecuencia de cita)."""
    contador: collections.Counter = collections.Counter()
    for clave in claves_mod._claves(texto[:400_000]):
        sigla, _, art = clave.partition("|")
        if not art:
            continue
        if sigla == "LEY":
            nid = idx_leyes.get(art.replace(".", ""))
            if nid:
                contador[nid] += 1
            continue
        art_num = art.replace("art_", "").split("-")[0]
        for codigo in SIGLAS.get(sigla, ()):  # type: ignore[arg-type]
            nid = idx_normas.get((codigo, art_num))
            if nid:
                contador[nid] += 1
                break
    return [nid for nid, _ in contador.most_common(tope)]


def main() -> int:
    ap = argparse.ArgumentParser(description="Integra jurisprudencia nueva al grafo jurídico.")
    ap.add_argument("--sin-comunidades", action="store_true", help="no recalcular comunidades (rápido)")
    args = ap.parse_args()

    claves_mod = _cargar_modulo("optimizar_catalogo_hf", BASE / "scripts" / "optimizar_catalogo_hf.py")
    grafo = json.loads(GRAFO.read_text(encoding="utf-8"))
    nodos: list[dict] = grafo["nodes"]
    aristas: list[dict] = grafo["edges"]
    ids = {n["id"] for n in nodos}
    idx_normas, idx_leyes = indices_de_normas(nodos)
    print(f"══ grafo de partida: {len(nodos):,} nodos · {len(aristas):,} aristas")
    print(f"   índice de normas: {len(idx_normas):,} artículos con nodo")

    respaldo = pathlib.Path(tempfile.gettempdir()) / "legal_knowledge_graph_pre_juris.json"
    shutil.copy2(GRAFO, respaldo)

    # 1 · órgano del TC (si no existe)
    if "organo_tc" not in ids:
        nodos.append({
            "id": "organo_tc", "label": "Tribunal Constitucional de Chile", "node_type": "organo_estado",
            "subtipo": "tribunal_constitucional", "jurisdiccion": "Nacional",
        })
        ids.add("organo_tc")

    # 2 · sentencias del TC (últimos 2 años) con su Markdown
    nuevos_tc = 0
    enlaces_norma = 0
    if TC_INDICE.exists():
        for linea in open(TC_INDICE, encoding="utf-8"):
            reg = json.loads(linea)
            nid = "sent_tc_" + slug(reg["rol"].replace("Rol N° ", "rol_n_"))
            if nid in ids:
                continue
            md = BASE / reg["archivo_md"]
            if not md.exists():
                continue
            nodos.append({
                "id": nid, "label": f"TC · {reg['rol']} — {str(reg.get('tipo') or '')[:60]}",
                "node_type": "jurisprudencia_tc", "file_type": "legal_judgment",
                "rol": reg["rol"], "fecha": reg.get("fecha"), "tipo": reg.get("tipo"),
                "source_file": reg["archivo_md"], "tokens_archivo": reg.get("tokens_aprox"),
                "url": "https://buscador.tcchile.cl",
            })
            ids.add(nid)
            aristas.append({"source": nid, "target": "organo_tc", "relation": "resuelto_por", "weight": 1.0})
            texto = md.read_text(encoding="utf-8", errors="replace")
            for norm_id in normas_citadas(texto, claves_mod, idx_normas, idx_leyes):
                aristas.append({"source": nid, "target": norm_id, "relation": "cita_norma", "weight": 1.0})
                enlaces_norma += 1
            nuevos_tc += 1
    print(f"══ TC: +{nuevos_tc} sentencias · +{enlaces_norma} enlaces a normas")

    # 3 · publicaciones ambientales con su Markdown
    nuevos_pub = 0
    por_titulo = {slug(n.get("label", "")): n for n in nodos if n.get("node_type") == "anuario_boletin_ambiental"}
    if PUB_INDICE.exists():
        for linea in open(PUB_INDICE, encoding="utf-8"):
            reg = json.loads(linea)
            if not reg.get("caracteres"):
                continue
            clave = slug(reg.get("titulo", ""))
            existente = por_titulo.get(clave)
            md_rel = reg["archivo_md"]
            if existente is not None:
                existente["source_file"] = md_rel
                existente["tokens_archivo"] = reg.get("tokens_aprox")
                nid = existente["id"]
            else:
                nid = "pub_amb_" + clave
                if nid in ids:
                    continue
                nodos.append({
                    "id": nid, "label": reg.get("titulo", ""), "node_type": "anuario_boletin_ambiental",
                    "tribunal": reg.get("tribunal"), "tipo": reg.get("tipo"),
                    "numero": reg.get("numero"), "anio": reg.get("anio"),
                    "source_file": md_rel, "tokens_archivo": reg.get("tokens_aprox"),
                    "url": reg.get("url_pdf"),
                })
                ids.add(nid)
                por_titulo[clave] = nodos[-1]
            organo = f"organo_{(reg.get('tribunal') or 'ta').lower()}"
            if organo in ids:
                aristas.append({"source": nid, "target": organo, "relation": "publicado_por", "weight": 1.0})
            md = BASE / md_rel
            if md.exists():
                texto = md.read_text(encoding="utf-8", errors="replace")
                for norm_id in normas_citadas(texto, claves_mod, idx_normas, idx_leyes, tope=15):
                    aristas.append({"source": nid, "target": norm_id, "relation": "cita_norma", "weight": 1.0})
                    enlaces_norma += 1
            nuevos_pub += 1
    print(f"══ Publicaciones ambientales: +{nuevos_pub} con texto · enlaces a normas acumulados {enlaces_norma}")

    # 4 · comunidades con el mismo algoritmo del motor
    comunidades = 0
    if not args.sin_comunidades:
        t0 = time.time()
        try:
            G = nx.DiGraph()
            G.add_nodes_from(n["id"] for n in nodos)
            for e in aristas:
                try:
                    G.add_edge(e["source"], e["target"], weight=float(e.get("weight", 1.0)))
                except (KeyError, TypeError, ValueError):
                    continue
            comms = nx.algorithms.community.greedy_modularity_communities(G.to_undirected())
            asignacion = {nodo: i for i, com in enumerate(comms) for nodo in com}
            for n in nodos:
                if n["id"] in asignacion:
                    n["community"] = asignacion[n["id"]]
            comunidades = len(comms)
            print(f"══ comunidades recalculadas: {comunidades} · modularidad voraz · {time.time() - t0:.1f}s")
        except Exception as e:
            print(f"  [!] no se pudieron recalcular las comunidades: {e}")

    grafo["nodes"] = nodos
    grafo["edges"] = aristas
    grafo["links"] = aristas
    GRAFO.write_text(json.dumps(grafo, ensure_ascii=False), encoding="utf-8")
    print(f"══ grafo final: {len(nodos):,} nodos · {len(aristas):,} aristas · {comunidades or '?'} comunidades")
    print(f"   respaldo previo: {respaldo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
