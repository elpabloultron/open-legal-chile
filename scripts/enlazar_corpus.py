#!/usr/bin/env python3
"""
Open Legal Chile — Enlaza el corpus: agrega al final de cada obra de ``doctrina/`` y de
``corpus_guias_aj/`` un bloque «Véase también» con las **conexiones reales** medidas en los
grafos (`data/legal_knowledge_graph.json`, `data/grafo_guias_aj.json`,
`data/enlaces_guias_corpus.json`).

El bloque es **aditivo y verificable**: nunca se toca nada de arriba, y el marcador guarda
el sha256 del cuerpo para probar que el contenido original quedó intacto.

    python scripts/enlazar_corpus.py            # aplica a todo el corpus (idempotente)
    python scripts/enlazar_corpus.py --limite 5 # ensayo
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
from collections import Counter, defaultdict

RAIZ = pathlib.Path(__file__).resolve().parent.parent
MARCADOR = "<!-- enlaces:generado"
HF_BASE = "https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile/blob/main"
GITHUB_BASE = "https://github.com/elpabloultron/open-legal-chile/blob/main"

COLECCIONES = (
    ("jurisprudencia_cs/README.md", "Fichas de la Corte Suprema"),
    ("jurisprudencia_tc/README.md", "Sentencias del Tribunal Constitucional"),
    ("jurisprudencia_ambiental/README.md", "Sentencias ambientales"),
    ("publicaciones_ambientales/README.md", "Publicaciones ambientales"),
)


def _normalizar(texto: str) -> str:
    return re.sub(r"[^a-z0-9]", "", texto.lower())


# ── escritura del bloque ──────────────────────────────────────────────────────────────
def _enlace(destino: str) -> str:
    """Destino de un enlace markdown: los espacios van percent-encoded (%20).

    Sin esto, «[t](../apuntes_orrego/De la X.md)» es un enlace roto para GitHub y
    para cualquier lector markdown: el destino termina en la primera palabra.
    """
    return destino.replace(" ", "%20")


def bloque_para(archivo: pathlib.Path, vecinos: list, guias: list, opciones: dict | None = None) -> str:
    """Arma el bloque «Véase también» para ``archivo``.

    vecinos / guias: [(ruta_relativa, título, motivo)] · opciones: {"obras": [...], "grafo": url}.
    """
    opciones = opciones or {}
    lineas = ["## Véase también", ""]

    lineas.append("**Obras del canon relacionadas** — por los temas y las normas que comparten:")
    if vecinos:
        for destino, titulo, motivo in vecinos:
            linea = f"- [{titulo}]({_enlace(destino)})"
            if motivo:
                linea += f" — {motivo}"
            lineas.append(linea)
    else:
        lineas.append("- (sin conexiones medidas todavía)")

    obras = opciones.get("obras") or []
    if obras:
        lineas.append("")
        lineas.append("**Obras del canon que esta guía trabaja:**")
        for destino, titulo in obras:
            lineas.append(f"- [{titulo}]({_enlace(destino)})")

    if guias:
        lineas.append("")
        lineas.append("**Guías de la Academia Judicial que usan esta obra:**")
        for destino, titulo, motivo in guias:
            lineas.append(f"- [{titulo}]({_enlace(destino)}) — {motivo}")

    if opciones.get("grafo"):
        lineas.append("")
        lineas.append(f"**Grafo de las guías:** <{opciones['grafo']}>")

    colecciones = []
    for relativo, nombre in COLECCIONES:
        destino = RAIZ / relativo
        if destino.exists():
            rel = os.path.relpath(destino, start=archivo.parent).replace("\\", "/")
            colecciones.append(f"[{nombre}]({_enlace(rel)})")
    if colecciones:
        lineas.append("")
        lineas.append("**Colecciones del corpus:** " + " · ".join(colecciones))

    try:
        publicado = archivo.relative_to(RAIZ).as_posix()
    except ValueError:
        publicado = archivo.name
    lineas.append("")
    lineas.append(f"**Publicado en Hugging Face:** <{HF_BASE}/{_enlace(publicado)}>")
    return "\n".join(lineas) + "\n"


def aplicar_bloque(archivo: pathlib.Path, bloque: str) -> bool:
    """Reemplaza (o agrega) el bloque al final. Devuelve True si el archivo cambió."""
    texto = archivo.read_text(encoding="utf-8")
    corte = texto.find(MARCADOR)
    cuerpo = (texto[:corte] if corte >= 0 else texto).rstrip() + "\n\n"
    sha = hashlib.sha256(cuerpo.strip().encode("utf-8")).hexdigest()
    nuevo = cuerpo + f"{MARCADOR} sha256:{sha} -->\n" + bloque
    if nuevo == texto:
        return False
    archivo.write_text(nuevo, encoding="utf-8")
    return True


# ── conexiones ────────────────────────────────────────────────────────────────────────
def _titulo(ruta: pathlib.Path) -> str:
    try:
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            if linea.startswith("# "):
                return linea[2:].strip()[:90]
    except OSError:
        pass
    return ruta.stem.replace("_", " ").replace("-", " ").strip()


def _vecinos_del_grafo(archivos: set[str]) -> dict[str, list[tuple[str, int]]]:
    """Para cada archivo del corpus, los otros con los que comparte nodos del grafo."""
    grafo = json.loads((RAIZ / "data" / "legal_knowledge_graph.json").read_text(encoding="utf-8"))
    nodos, aristas = grafo["nodes"], grafo.get("links") or grafo.get("edges") or []

    archivo_de_nodo = {n["id"]: n["source_file"] for n in nodos
                       if isinstance(n.get("source_file"), str) and n["source_file"].endswith(".md")}
    vecindad: dict[str, set[str]] = defaultdict(set)
    for arista in aristas:
        vecindad[str(arista.get("source"))].add(str(arista.get("target")))
        vecindad[str(arista.get("target"))].add(str(arista.get("source")))

    archivos_de_nodo: dict[str, set[str]] = defaultdict(set)
    for nodo_id, archivo in archivo_de_nodo.items():
        if archivo in archivos:
            archivos_de_nodo[nodo_id].add(archivo)
        for vecino_id in vecindad.get(nodo_id, ()):
            if archivo_de_nodo.get(vecino_id) in archivos:
                archivos_de_nodo[nodo_id].add(archivo_de_nodo[vecino_id])

    conteo: dict[str, Counter] = defaultdict(Counter)
    for conjunto in archivos_de_nodo.values():
        for a in conjunto:
            for b in conjunto:
                if a != b:
                    conteo[a][b] += 1
    return {a: c.most_common() for a, c in conteo.items()}


def _indice_de_guias() -> dict[str, pathlib.Path]:
    """Nombre normalizado de cada guía → archivo real en corpus_guias_aj/."""
    return {_normalizar(p.stem): p for p in (RAIZ / "corpus_guias_aj").glob("*.md")}


def _guias_que_tocan(archivos: set[str]) -> dict[str, list[str]]:
    """Inverso de data/enlaces_guias_corpus.json: obra de doctrina → guías que la tocan."""
    ruta = RAIZ / "data" / "enlaces_guias_corpus.json"
    if not ruta.exists():
        return {}
    datos = json.loads(ruta.read_text(encoding="utf-8")).get("enlaces", {})
    guias = _indice_de_guias()

    inverso: dict[str, list[str]] = defaultdict(list)
    for clave, entradas in datos.items():
        objetivo = guias.get(_normalizar(clave))
        if objetivo is None:
            continue
        vistos: set[str] = set()
        for entrada in entradas or []:
            archivo = "doctrina/" + str(entrada.get("archivo", ""))
            if archivo.endswith(".md") and archivo in archivos and archivo not in vistos:
                inverso[archivo].append(objetivo.stem)
                vistos.add(archivo)
    return inverso


def _conexiones_de_guias(archivos: set[str]) -> tuple[dict[str, list[tuple[str, int]]], dict[str, list[str]]]:
    """Para cada guía: guías hermanas (grafo de guías) y obras del canon que trabaja."""
    hermanas: dict[str, Counter] = defaultdict(Counter)
    ruta = RAIZ / "data" / "grafo_guias_aj.json"
    if ruta.exists():
        grafo = json.loads(ruta.read_text(encoding="utf-8"))
        nodos, aristas = grafo["nodes"], grafo.get("edges") or grafo.get("links") or []
        archivo_de_nodo = {n["id"]: n["source_file"] for n in nodos
                           if isinstance(n.get("source_file"), str)}
        vecindad: dict[str, set[str]] = defaultdict(set)
        for arista in aristas:
            vecindad[str(arista.get("source"))].add(str(arista.get("target")))
            vecindad[str(arista.get("target"))].add(str(arista.get("source")))
        for nodo_id, archivo in archivo_de_nodo.items():
            if archivo not in archivos:
                continue
            for vecino_id in vecindad.get(nodo_id, ()):
                otro = archivo_de_nodo.get(vecino_id, "")
                if otro in archivos and otro != archivo:
                    hermanas[archivo][otro] += 1

    obras_de_guia: dict[str, list[str]] = defaultdict(list)
    ruta_enlaces = RAIZ / "data" / "enlaces_guias_corpus.json"
    if ruta_enlaces.exists():
        datos = json.loads(ruta_enlaces.read_text(encoding="utf-8")).get("enlaces", {})
        guias = _indice_de_guias()
        for clave, entradas in datos.items():
            objetivo = guias.get(_normalizar(clave))
            if objetivo is None:
                continue
            for entrada in sorted(entradas or [], key=lambda e: -float(e.get("peso", 0)))[:5]:
                archivo = "doctrina/" + str(entrada.get("archivo", ""))
                if archivo in archivos and archivo not in obras_de_guia[objetivo.stem]:
                    obras_de_guia[objetivo.stem].append(archivo)

    return ({g: c.most_common() for g, c in hermanas.items()}, obras_de_guia)


def _rel(archivo: pathlib.Path, destino: pathlib.Path) -> str:
    return os.path.relpath(destino, start=archivo.parent).replace("\\", "/")


# ── principal ─────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="Enlaza el corpus con bloques «Véase también».")
    ap.add_argument("--limite", type=int, default=0, help="procesar sólo N archivos (ensayo)")
    args = ap.parse_args()

    directorios = [RAIZ / "doctrina", RAIZ / "corpus_guias_aj"]
    universo = {p.relative_to(RAIZ).as_posix() for d in directorios for p in d.rglob("*.md")
                if p.name != "README.md"}
    archivos = sorted(p for d in directorios for p in d.rglob("*.md") if p.name != "README.md")
    if args.limite:
        archivos = archivos[: args.limite]
    titulos = {p.relative_to(RAIZ).as_posix(): _titulo(p)
               for d in directorios for p in d.rglob("*.md") if p.name != "README.md"}

    print(f"══ {len(archivos)} archivos por enlazar (conexiones medidas sobre {len(universo)})")
    vecinos = _vecinos_del_grafo(universo)
    guias_de = _guias_que_tocan(universo)
    hermanas, obras_de_guia = _conexiones_de_guias(universo)

    cambiados = 0
    for archivo in archivos:
        rel = archivo.relative_to(RAIZ).as_posix()
        es_guia = rel.startswith("corpus_guias_aj/")
        lista_vecinos: list[tuple[str, str, str]] = []
        opciones: dict = {}

        if es_guia:
            for otro, peso in hermanas.get(archivo.stem, [])[:3]:
                lista_vecinos.append((_rel(archivo, RAIZ / otro), titulos.get(otro, otro),
                                      f"misma área temática ({peso} conexiones)"))
            opciones["obras"] = [(_rel(archivo, RAIZ / o), titulos.get(o, o))
                                 for o in obras_de_guia.get(archivo.stem, [])]
            opciones["grafo"] = f"{GITHUB_BASE}/data/grafo_guias_aj.json"
        else:
            for otro, peso in vecinos.get(rel, [])[:5]:
                if not titulos.get(otro):
                    continue
                motivo = "cita mutua" if peso >= 3 else f"mismo tema ({peso} conexiones)"
                lista_vecinos.append((_rel(archivo, RAIZ / otro), titulos.get(otro, otro), motivo))

        lista_guias = []
        for guia in guias_de.get(rel, [])[:3]:
            destino = RAIZ / "corpus_guias_aj" / f"{guia}.md"
            if destino.exists():
                lista_guias.append((_rel(archivo, destino),
                                    titulos.get(destino.relative_to(RAIZ).as_posix(), guia),
                                    "la usa como material de apoyo"))

        if aplicar_bloque(archivo, bloque_para(archivo, lista_vecinos, lista_guias, opciones)):
            cambiados += 1
    print(f"══ listo: {cambiados} archivos con bloque nuevo/actualizado de {len(archivos)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
