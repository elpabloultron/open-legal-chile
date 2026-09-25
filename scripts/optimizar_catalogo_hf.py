#!/usr/bin/env python3
"""
Open Legal Chile — Catálogo eficiente para Hugging Face.

Genera los artefactos que hacen al dataset más liviano y más fácil de consumir
por un harness o un LLM (con citas verificables):

  1. data/catalogo/instituciones_lite.jsonl  → fichas densas sin el contenido íntegro
  2. data/catalogo/train_lite.jsonl          → índice de obras sin el texto completo
  3. data/catalogo/indice_citas.jsonl        → archivo · secciones · enlace directo
  4. data/catalogo/indice_agentes.json       → rutas «pregunta → archivo» y formato de cita
  5. llms.txt                                → mapa del corpus para agentes (raíz del dataset)
  6. data/enlaces_guias_corpus.json          → enlaces guías ↔ corpus por norma compartida

Uso:
    python scripts/optimizar_catalogo_hf.py
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import unicodedata
from collections import Counter, defaultdict

BASE = pathlib.Path(__file__).resolve().parent.parent
DATA = BASE / "data"
CATALOGO = DATA / "catalogo"
CATALOGO.mkdir(parents=True, exist_ok=True)
REPO_ID = "pablobenavidesj/doctrina-jurisprudencia-chile"
URL_BASE = f"https://huggingface.co/datasets/{REPO_ID}/blob/main/"


def sin_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


# ── 1 y 2 · versiones «puntero» ────────────────────────────────────────────────

def _contar(ruta: pathlib.Path) -> int:
    if not ruta.exists():
        return 0
    with open(ruta, encoding="utf-8") as f:
        return sum(1 for _ in f)


def generar_lite() -> dict:
    resumen: dict[str, dict] = {}

    origen = DATA / "instituciones.jsonl"
    destino = CATALOGO / "instituciones_lite.jsonl"
    if not origen.exists():
        print("  [!] sin data/instituciones.jsonl: se omite la versión ligera de las fichas")
    else:
        n = 0
        with open(origen, encoding="utf-8") as f_in, open(destino, "w", encoding="utf-8") as f_out:
            for linea in f_in:
                r = json.loads(linea)
                r.pop("contenido", None)
                r["ruta_hf"] = URL_BASE + "doctrina/" + str(r.get("archivo", ""))
                f_out.write(json.dumps(r, ensure_ascii=False) + "\n")
                n += 1
        resumen["instituciones_lite"] = {"filas": n, "mb": destino.stat().st_size / 1e6, "origen_mb": origen.stat().st_size / 1e6}

    origen = DATA / "train.jsonl"
    destino = CATALOGO / "train_lite.jsonl"
    if not origen.exists():
        print("  [!] sin data/train.jsonl: se omite el índice ligero de obras")
    else:
        n = 0
        with open(origen, encoding="utf-8") as f_in, open(destino, "w", encoding="utf-8") as f_out:
            for linea in f_in:
                r = json.loads(linea)
                r.pop("texto_completo", None)
                r["ruta_hf"] = URL_BASE + "doctrina/" + str(r.get("archivo", ""))
                f_out.write(json.dumps(r, ensure_ascii=False) + "\n")
                n += 1
        resumen["train_lite"] = {"filas": n, "mb": destino.stat().st_size / 1e6, "origen_mb": origen.stat().st_size / 1e6}
    return resumen


# ── 3 · índice de citas por archivo y sección ─────────────────────────────────

def _secciones(md: str) -> list[dict]:
    secs: list[dict] = []
    for linea in md.splitlines():
        m = re.match(r"^(#{1,3})\s+(.{3,120})$", linea.strip())
        if m:
            secs.append({"nivel": len(m.group(1)), "titulo": m.group(2).strip()[:110]})
    return secs[:80]


def generar_indice_citas() -> dict:
    destino = CATALOGO / "indice_citas.jsonl"
    total = 0
    with open(destino, "w", encoding="utf-8") as f_out:
        for carpeta, prefijo in ((BASE / "doctrina", "doctrina/"), (BASE / "corpus_guias_aj", "guias_academia_judicial/")):
            if not carpeta.is_dir():
                continue
            for archivo in sorted(carpeta.rglob("*.md")):
                try:
                    md = archivo.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                rel = prefijo + archivo.relative_to(carpeta).as_posix()
                m_titulo = re.search(r"^#\s+(.+)$", md, re.M)
                reg = {
                    "archivo": rel,
                    "titulo": (m_titulo.group(1) if m_titulo else archivo.stem)[:110],
                    "secciones": _secciones(md),
                    "url": URL_BASE + rel,
                }
                f_out.write(json.dumps(reg, ensure_ascii=False) + "\n")
                total += 1
    return {"archivos": total, "mb": destino.stat().st_size / 1e6}


# ── 4 · índice de agentes (rutas y formato de cita) ───────────────────────────

def _areas_desde_fichas(limite: int = 18) -> list[dict]:
    ruta = DATA / "instituciones.jsonl"
    if not ruta.exists():
        return []
    fichas: list[dict] = []
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            r = json.loads(linea)
            fichas.append({"area": r.get("area", ""), "archivo": r.get("archivo", ""), "autor": r.get("autor", "")})
    por_area: dict[str, Counter] = defaultdict(Counter)
    for r in fichas:
        por_area[r["area"]][r["archivo"]] += 1
    rutas = []
    for area, contador in sorted(por_area.items(), key=lambda kv: -sum(kv[1].values()))[:limite]:
        rutas.append({
            "area": area,
            "fichas": sum(contador.values()),
            "abrir": ["doctrina/" + a for a, _ in contador.most_common(3)],
        })
    return rutas


def generar_llms_y_agentes() -> dict:
    fuente_fichas = DATA / "instituciones.jsonl"
    if not fuente_fichas.exists():
        print("  [!] sin data/instituciones.jsonl: se conservan llms.txt e indice_agentes.json ya existentes")
        return {"fichas": 0, "obras": 0, "guias": 0, "doctrina": 0, "juris": 0}
    n_fichas = _contar(fuente_fichas)
    n_obras = _contar(DATA / "train.jsonl")
    n_guias = len(list((BASE / "corpus_guias_aj").glob("*.md")))
    n_doctrina = len(list((BASE / "doctrina").rglob("*.md")))
    n_juris = sum(_contar(f) for f in (DATA / "jurisprudencia").glob("*.jsonl"))
    nodos = aristas = 0
    try:
        grafo = json.loads((DATA / "legal_knowledge_graph.json").read_text(encoding="utf-8"))
        nodos, aristas = len(grafo.get("nodes", [])), len(grafo.get("edges", []))
    except (OSError, ValueError):
        pass

    llms = f"""# Open Legal Chile — corpus jurídico chileno en Markdown
> Doctrina íntegra ({n_doctrina} documentos), guías oficiales de la Academia Judicial ({n_guias}),
> fichas dogmáticas densas ({n_fichas:,}), jurisprudencia ({n_juris:,} registros de los Tribunales
> Ambientales, Corte Suprema y Tribunal Constitucional) y un grafo de conocimiento con
> reducción masiva de tokens.

## Para agentes y LLM
- Fichas de ~91 tokens (mediana) en vez de obras de ~96.536 tokens: `data/catalogo/instituciones_lite.jsonl`
- Índice de obras (sin texto) con ruta al documento íntegro: `data/catalogo/train_lite.jsonl`
- Índice de citas por archivo y sección: `data/catalogo/indice_citas.jsonl`
- Rutas «tema → archivo»: `data/catalogo/indice_agentes.json`
- Grafo (nodos y relaciones con archivo de origen): `data/legal_knowledge_graph.json`
- Texto íntegro de cada obra: `doctrina/<ruta>.md` · Guías: `guias_academia_judicial/<ruta>.md`
- Jurisprudencia: `data/jurisprudencia/*.jsonl` (ambiental, Corte Suprema, Tribunal Constitucional)

## Formato de cita
- Conversación: primero la respuesta y, al final, la lista de fuentes.
- Documento (informe, memorándum, escrito): cita a pie de página numerada.
- Cada fuente: `[Hugging Face - <ruta en el dataset>]`. Ejemplo: `[Hugging Face - doctrina/civil/ramos_pazos_obligaciones/01_concepto.md]`
- Sin fuente identificable se dice «sin fuente verificable»; un dato con varias fuentes se cita con todas.

## Licencia
Documentos de terceros redistribuidos con atribución (ver la tarjeta del dataset).
"""
    (BASE / "llms.txt").write_text(llms, encoding="utf-8")

    agentes = {
        "dataset": REPO_ID,
        "resumen": {
            "documentos_doctrina": n_doctrina, "guias_academia_judicial": n_guias, "fichas": n_fichas,
            "obras_indexadas": n_obras, "registros_jurisprudencia": n_juris,
            "nodos_grafo": nodos, "aristas_grafo": aristas,
        },
        "como_citar": {"formato": "[Hugging Face - <ruta>]", "url": URL_BASE + "<ruta>"},
        "rutas": _areas_desde_fichas(),
        "archivos_clave": {
            "fichas_lite": "data/catalogo/instituciones_lite.jsonl",
            "obras_lite": "data/catalogo/train_lite.jsonl",
            "indice_citas": "data/catalogo/indice_citas.jsonl",
            "grafo": "data/legal_knowledge_graph.json",
            "llms": "llms.txt",
        },
    }
    (CATALOGO / "indice_agentes.json").write_text(json.dumps(agentes, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"fichas": n_fichas, "obras": n_obras, "guias": n_guias, "doctrina": n_doctrina, "juris": n_juris}


# ── 5 · enlaces guías ↔ corpus por norma compartida ───────────────────────────

RE_ART = re.compile(r"\b(?:art[íi]culo|art[s]?\.?)\s*(\d{1,4})\s*(bis|ter|qu[áa]ter)?", re.I)
RE_LEY = re.compile(r"\bley\s*n?[°º]?\s*(\d{1,2}(?:\.\d{3})*)\b", re.I)
CODIGOS = {
    "codigo civil": "CC", "codigo penal": "CP", "codigo del trabajo": "CT",
    "codigo procesal penal": "CPP", "codigo de procedimiento civil": "CPC",
    "codigo de procedimiento penal": "CPP2", "codigo organico de tribunales": "COT",
    "constitucion": "CPR", "codigo tributario": "CTRIB", "ley del consumidor": "LDC",
}


def _claves(texto: str) -> set[str]:
    t = sin_acentos(texto.lower())
    claves: set[str] = set()
    for m in RE_ART.finditer(t):
        ventana = t[max(0, m.start() - 120):m.start()]
        codigo = ""
        for nombre, sigla in CODIGOS.items():
            if nombre in ventana:
                codigo = sigla
        if codigo:
            sufijo = f"-{m.group(2)}" if m.group(2) else ""
            claves.add(f"{codigo}|art_{m.group(1)}{sufijo}")
    for m in RE_LEY.finditer(t):
        claves.add(f"LEY|{m.group(1).replace('.', '')}")
    return claves


def generar_enlaces_guias_corpus(max_por_guia: int = 6) -> dict:
    guias: dict[str, set[str]] = {}
    for archivo in sorted((BASE / "corpus_guias_aj").glob("*.md")):
        guias[archivo.stem] = _claves(archivo.read_text(encoding="utf-8", errors="replace"))
    corpus: dict[str, set[str]] = {}
    for archivo in sorted((BASE / "doctrina").rglob("*.md")):
        corpus[archivo.relative_to(BASE / "doctrina").as_posix()] = _claves(archivo.read_text(encoding="utf-8", errors="replace"))

    todas = set().union(*[c for c in corpus.values()] or [set()])
    enlaces: dict[str, list[dict]] = {}
    for guia, claves_g in guias.items():
        if not claves_g:
            continue
        puntajes = []
        for doc, claves_d in corpus.items():
            comunes = claves_g & claves_d
            if comunes:
                puntajes.append((len(comunes) / len(claves_g | claves_d), len(comunes), doc, sorted(comunes)[:6]))
        puntajes.sort(reverse=True)
        enlaces[guia] = [
            {"archivo": doc, "peso": round(p, 3), "claves": comunes}
            for p, _, doc, comunes in puntajes[:max_por_guia]
        ]

    salida = {
        "guias": len(guias),
        "claves_de_norma_en_el_corpus": len(todas),
        "enlaces": enlaces,
        "actualizado": "2026-09-25",
    }
    (DATA / "enlaces_guias_corpus.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"guias": len(guias), "claves": len(todas), "con_enlaces": len(enlaces)}


def main() -> int:
    print("══ 1-2 · versiones «puntero» ══")
    for nombre, d in generar_lite().items():
        print(f"  {nombre:20} {d['filas']:>7,} filas · {d['mb']:6.1f} MB (origen {d['origen_mb']:6.1f} MB)")
    print("══ 3 · índice de citas ══")
    print("  archivos con secciones:", generar_indice_citas())
    print("══ 4 · llms.txt e índice de agentes ══")
    print("  ", generar_llms_y_agentes())
    print("══ 5 · enlaces guías ↔ corpus ══")
    print("  ", generar_enlaces_guias_corpus())
    return 0


if __name__ == "__main__":
    sys.exit(main())
