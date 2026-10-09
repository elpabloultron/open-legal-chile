"""Capa conectora del grafo del mapa: entidades + documentos + aristas, alias y comunidades.

El grafo curado del repositorio (`data/legal_knowledge_graph.json`) NO viaja en el mapa: el
cliente lo une con esta capa en memoria, así las ingestas locales siguen visibles y no hay dos
copias divergentes. El constructor sí usa el curado del checkout para dos cosas: los alias
(IDs legados → canónicos) y las comunidades, que se calculan sobre la unión para que el cliente
las aplique tal cual.

Los 70.523 fallos de la Corte Suprema no son nodos: entran como aristas agregadas y ponderadas
entre ministros, salas, recursos y tribunales de origen (y como nodos solo los fallos citados
por otra entrada). El cliente los materializa por consulta desde el índice.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from citas_legales import etiqueta_norma, normas_canonicas, rol_canonico
from mapa_corpus import ids

SEMILLA_LOUVAIN = 42
ORGANOS = {"organo:tc": "Tribunal Constitucional", "organo:cs": "Corte Suprema",
           "organo:1ta": "Primer Tribunal Ambiental", "organo:2ta": "Segundo Tribunal Ambiental",
           "organo:3ta": "Tercer Tribunal Ambiental"}
# Recurso de la CS → vía procesal curada (solo si el nodo curado existe).
_RECURSO_A_VIA = [("proteccion", "via_recurso_de_proteccion"), ("casacion", "via_recurso_de_casacion"),
                  ("apelacion", "via_recurso_de_apelacion"), ("tutela", "via_tutela_laboral")]


def padres_norma(norma_id: str) -> List[Tuple[str, str]]:
    """`norma:cpr:19:n3` → [(…:n3, …:19), (…:19, norma:cpr)]: aristas `parte_de`."""
    partes = norma_id.split(":")
    aristas = []
    while len(partes) > 2:
        hijo = ":".join(partes)
        partes = partes[:-1]
        aristas.append((hijo, ":".join(partes)))
    return aristas


class Grafo:
    """Acumulador determinista de nodos y aristas (sin NetworkX hasta las comunidades)."""

    def __init__(self) -> None:
        self.nodos: Dict[str, Dict[str, Any]] = {}
        self.aristas: Dict[Tuple[str, str, str], int] = {}

    def nodo(self, nid: str, tipo: str, label: str, **attrs: Any) -> None:
        if nid not in self.nodos:
            self.nodos[nid] = {"id": nid, "tipo": tipo, "label": label}
        for k, v in attrs.items():
            if v not in (None, "", [], {}):
                self.nodos[nid][k] = v

    def arista(self, s: str, t: str, rel: str, w: int = 1) -> None:
        if s == t:
            return
        clave = (s, t, rel)
        self.aristas[clave] = self.aristas.get(clave, 0) + int(w)


def _por_id(filas: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {f["id"]: f for f in filas}


def construir_capa(filas: List[Dict[str, Any]], entidades: Dict[str, List[Dict[str, Any]]],
                   vias_curadas: Set[str]) -> Grafo:
    """La capa conectora a partir de todas las filas del mapa y sus entidades."""
    g = Grafo()
    entradas = _por_id(filas)
    for oid, label in ORGANOS.items():
        g.nodo(oid, "organo", label)
    for tipo, lista in entidades.items():
        for e in lista:
            g.nodo(e["id"], e.get("tipo", tipo.rstrip("s")), e.get("label", e["id"]))
    for e in entidades.get("normas", []):
        for hijo, padre in padres_norma(e["id"]):
            if padre not in g.nodos:
                g.nodo(padre, "norma", etiqueta_norma(padre))
            g.arista(hijo, padre, "parte_de")

    citados_cs: Set[str] = set()
    for f in filas:
        col = f.get("col")
        if col in ("doc", "tc", "ta", "guia", "bib", "pub"):
            attrs = {k: f[k] for k in ("col", "fecha", "anio", "ruta") if k in f}
            g.nodo(f["id"], {"doc": "documento", "tc": "sentencia_tc", "ta": "sentencia_ta",
                             "guia": "guia", "bib": "estudio", "pub": "publicacion"}[col],
                   f.get("titulo") or f["id"], **attrs)
            for norma, n in f.get("normas", []):
                if norma in g.nodos:
                    g.arista(f["id"], norma, "cita_norma", n)
            for rel in ("cita_cs", "cita_tc", "cita_ta"):
                for destino in f.get(rel, []):
                    if destino in entradas:
                        g.arista(f["id"], destino, "cita_rol")
                        if destino.startswith("cs:"):
                            citados_cs.add(destino)
        if col == "doc":
            for a in f.get("autores", []):
                g.arista(f["id"], a, "escrito_por")
            if f.get("revista"):
                g.arista(f["id"], f["revista"], "publicado_en")
        elif col == "tc":
            g.arista(f["id"], "organo:tc", "resuelto_por")
            for destino in f.get("gestion_cs", []):
                if destino in entradas:
                    g.arista(f["id"], destino, "gestion_pendiente")
                    citados_cs.add(destino)
        elif col == "ta":
            if f.get("tribunal"):
                g.arista(f["id"], f["tribunal"], "resuelto_por")
            for m in f.get("ministros", []):
                g.arista(f["id"], m, "integrado_por")
            if f.get("redactor"):
                g.arista(f["id"], f["redactor"], "redactado_por")
            for acu in f.get("acumuladas", []):
                if acu in entradas:
                    g.arista(f["id"], acu, "acumula")

    # Corte Suprema: agregados ponderados (no un nodo por fallo).
    for f in filas:
        if f.get("col") != "cs":
            continue
        sala, recurso, origen = f.get("sala"), f.get("recurso"), f.get("origen")
        if sala:
            g.arista(sala, "organo:cs", "parte_de")
            for m in f.get("ministros", []):
                g.arista(m, sala, "integra_sala")
            if recurso:
                g.arista(sala, recurso, "conoce_recurso")
            if origen:
                g.arista(origen, sala, "eleva_a")
    for e in entidades.get("recursos", []):
        for clave, via in _RECURSO_A_VIA:
            if clave in e["id"] and via in vias_curadas:
                g.arista(e["id"], via, "equivale_a")
                break
    for cs in sorted(citados_cs):
        f = entradas[cs]
        g.nodo(cs, "sentencia_cs", f.get("titulo") or cs, col="cs", fecha=f.get("fecha"), ruta=f.get("ruta"))
        for m in f.get("ministros", []):
            g.arista(cs, m, "integrado_por")
        if f.get("sala"):
            g.arista(cs, f["sala"], "resuelto_por")
    return g


def alias_curados(curado: Dict[str, Any], g: Grafo, filas: List[Dict[str, Any]]) -> Tuple[Dict[str, str], List[Tuple[str, str, str]]]:
    """(alias legado→canónico, aristas puente). Solo alias inequívocos; lo dudoso va como arista.

    - `norma_*` → `norma:*` cuando su etiqueta da exactamente un ID canónico.
    - `obra_*`, `bib_amb_*`, `pub_amb_*` → la entrada cuya ruta es su `source_file`.
    - `organo_*` → `organo:*`; `autor_*` → `autor:*` si el nombre coincide.
    - `sent_tc_*`: su cabecera es de otra causa (ver extractores), así que NO se fusiona: se
      enlaza con `mismo_documento` a la entrada del documento oficial (`extended/<id>`).
    - `sent_amb_*` → `ta:*` por tribunal + rol; `fallo_*`/`sent_cs_*` → `cs:*` solo si el fallo
      existe en el corpus cosechado.
    """
    por_ruta = {f["ruta"]: f["id"] for f in filas if f.get("ruta")}
    alias: Dict[str, str] = {}
    puentes: List[Tuple[str, str, str]] = []
    for n in curado.get("nodes", []):
        nid = str(n.get("id"))
        tipo = n.get("node_type")
        label = str(n.get("label") or "")
        fuente = str(n.get("source_file") or "")
        destino: Optional[str] = None
        if tipo in ("articulo_legal", "cuerpo_legal") and nid.startswith("norma_"):
            canon = [i for i, _ in normas_canonicas(label)]
            if len(canon) == 1 and canon[0] in g.nodos:
                destino = canon[0]
        elif tipo in ("obra", "estudio_ambiental", "anuario_boletin_ambiental") and fuente in por_ruta:
            destino = por_ruta[fuente]
        elif tipo == "organo_estado" and nid.startswith("organo_"):
            organo = "organo:" + nid[len("organo_"):]
            destino = organo if organo in g.nodos else None
        elif tipo == "autor":
            autor = ids.autor_id(label)
            destino = autor if autor and autor in g.nodos else None
        elif tipo == "jurisprudencia_tc":
            m = re.search(r"/extended/(\d+)/", str(n.get("url") or ""))
            if m and f"tc:{m.group(1)}" in g.nodos:
                puentes.append((nid, f"tc:{m.group(1)}", "mismo_documento"))
        elif nid.startswith("sent_amb_"):
            trib = str(n.get("tribunal") or "").lower()
            ta = rol_canonico(str(n.get("rol") or ""), trib) if trib in ("1ta", "2ta", "3ta") else None
            destino = ta if ta and ta in g.nodos else None
        elif tipo in ("jurisprudencia", "jurisprudencia_cs"):
            cs = rol_canonico(re.sub(r",?\s*Fecha.*$", "", label.split("·")[-1].split("—")[0]).replace("CS - ", ""), "cs")
            if cs and cs in g.nodos:
                puentes.append((nid, cs, "refiere_a"))
        if destino and destino != nid:
            alias[nid] = destino
    return dict(sorted(alias.items())), sorted(puentes)


def comunidades(curado: Dict[str, Any], g: Grafo, alias: Dict[str, str],
                puentes: List[Tuple[str, str, str]]) -> Dict[str, int]:
    """Louvain con semilla sobre la unión curado + capa; numeradas por (-tamaño, menor id)."""
    import networkx as nx
    pesos: Dict[Tuple[str, str], int] = defaultdict(int)

    def _sumar(a: str, b: str, w: int) -> None:
        a, b = alias.get(a, a), alias.get(b, b)
        if a != b:
            pesos[(a, b) if a < b else (b, a)] += w

    nodos: Set[str] = set(g.nodos)
    for n in curado.get("nodes", []):
        nodos.add(alias.get(str(n["id"]), str(n["id"])))
    for e in curado.get("edges", curado.get("links", [])):
        _sumar(str(e["source"]), str(e["target"]), 1)
    for (s, t, _), w in g.aristas.items():
        _sumar(s, t, w)
    for s, t, _ in puentes:
        _sumar(s, t, 1)
    G = nx.Graph()
    G.add_nodes_from(sorted(nodos))
    G.add_weighted_edges_from(sorted((a, b, w) for (a, b), w in pesos.items()))
    grupos = nx.community.louvain_communities(G, weight="weight", seed=SEMILLA_LOUVAIN)
    ordenados = sorted((sorted(c) for c in grupos), key=lambda c: (-len(c), c[0]))
    salida: Dict[str, int] = {}
    for i, c in enumerate(ordenados):
        for nid in c:
            salida[nid] = i
    for legado, canon in alias.items():
        if canon in salida:
            salida[legado] = salida[canon]
    return salida


def exportar(g: Grafo, alias: Dict[str, str], puentes: List[Tuple[str, str, str]],
             comunidad: Dict[str, int]) -> Dict[str, List[Dict[str, Any]]]:
    """Particiones del grafo: nodos-<tipo>, aristas-<relación>, alias, comunidades."""
    partes: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for nid in sorted(g.nodos):
        nodo = dict(g.nodos[nid])
        if nid in comunidad:
            nodo["c"] = comunidad[nid]
        partes[f"grafo/nodos-{nodo['tipo']}"].append(nodo)
    for (s, t, rel), w in sorted(g.aristas.items()):
        partes[f"grafo/aristas-{rel}"].append({"id": f"{s}>{t}", "s": s, "t": t, "w": w})
    for s, t, rel in puentes:
        partes[f"grafo/aristas-{rel}"].append({"id": f"{s}>{t}", "s": s, "t": t, "w": 1})
    partes["grafo/alias"] = [{"id": a, "a": b} for a, b in sorted(alias.items())]
    partes["grafo/comunidades"] = [{"id": k, "c": v} for k, v in sorted(comunidad.items())]
    return dict(partes)


def cargar_curado(ruta: str) -> Dict[str, Any]:
    with open(ruta, encoding="utf-8") as f:
        datos: Dict[str, Any] = json.load(f)
    return datos


def vias_de(curado: Dict[str, Any]) -> Set[str]:
    return {str(n["id"]) for n in curado.get("nodes", []) if n.get("node_type") == "via_procesal"}


def resumen_tipos(g: Grafo) -> Dict[str, int]:
    return dict(sorted(Counter(n["tipo"] for n in g.nodos.values()).items()))
