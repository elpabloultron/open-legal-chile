#!/usr/bin/env python3
"""
Open Legal Chile — Extiende y verifica el índice de publicaciones periódicas
de los Tribunales Ambientales (anuarios y boletines de jurisprudencia).

Fuentes oficiales:
  · 3TA Valdivia → https://3ta.cl/publicaciones/{anuario-de-jurisprudencia-ambiental, boletin-jurisprudencia-ambiental}
  · 2TA Santiago → https://tribunalambiental.cl/informacion-institucional/sobre-el-tribunal-ambiental/anuario/

Lee el JSONL existente, agrega lo que falte (sin duplicar) y lo reescribe ordenado.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "jurisprudencia"
JSONL = DATA / "ambiental_boletines_anuarios.jsonl"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
PAUSA = 0.35

JURIS = {
    "1TA": "Arica y Parinacota, Tarapacá, Antofagasta, Atacama y Coquimbo",
    "2TA": "Valparaíso, Metropolitana, O'Higgins y Maule",
    "3TA": "Ñuble, Biobío, La Araucanía, Los Ríos, Los Lagos, Aysén y Magallanes",
}
NOMBRES = {
    "1TA": "Primer Tribunal Ambiental de Antofagasta",
    "2TA": "Segundo Tribunal Ambiental de Santiago",
    "3TA": "Tercer Tribunal Ambiental de Valdivia",
}


def cargar() -> list[dict]:
    if not JSONL.exists():
        return []
    return [json.loads(linea) for linea in open(JSONL, encoding="utf-8")]


def clave(r: dict) -> tuple:
    return (r.get("tribunal"), r.get("tipo"), r.get("numero") or r.get("anio") or r.get("url_pdf"))


def primer_pdf(url: str) -> str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.content, "html.parser")
        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            if ".pdf" in href.lower():
                return href
    except Exception:
        pass
    return ""


def cosechar_3ta_boletines() -> list[dict]:
    """Recorre el listado de boletines del 3TA (paginado) y saca el PDF de cada uno."""
    nuevos: list[dict] = []
    vistos: set[str] = set()
    base = "https://3ta.cl/publicaciones/boletin-jurisprudencia-ambiental/"
    posts: list[str] = []
    for pagina in range(1, 9):
        url = base if pagina == 1 else f"{base}page/{pagina}/"
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
        except Exception:
            break
        if r.status_code != 200:
            break
        encontrados = sorted(set(re.findall(r'href="(https://3ta\.cl/noticias/boletin-n[^"]+)"', r.text)))
        nuevos_en_pagina = [p for p in encontrados if p not in vistos]
        if not nuevos_en_pagina:
            break
        vistos.update(nuevos_en_pagina)
        posts.extend(nuevos_en_pagina)
        time.sleep(PAUSA)
    print(f"  [3TA boletines] {len(posts)} avisos encontrados en el listado")
    for p in posts:
        m = re.search(r"boletin-n(\d+)", p)
        numero = m.group(1) if m else "S/N"
        pdf = primer_pdf(p)
        nuevos.append({
            "tribunal": "3TA",
            "tribunal_nombre": NOMBRES["3TA"],
            "jurisdiccion": JURIS["3TA"],
            "tipo": "Boletín de Jurisprudencia Ambiental",
            "numero": numero,
            "titulo": f"Boletín N° {numero} de Jurisprudencia y Actualidad Normativa — 3TA",
            "url_post": p,
            "url_pdf": pdf or p,
            "materia": "Doctrina y resoluciones del Tercer Tribunal Ambiental",
        })
        time.sleep(PAUSA)
    return nuevos


def cosechar_anuarios(tribunal: str, url: str) -> list[dict]:
    """Anuarios publicados en una página institucional."""
    res: list[dict] = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        if r.status_code != 200:
            return res
        soup = BeautifulSoup(r.content, "html.parser")
        vistos: set[str] = set()
        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            if ".pdf" not in href.lower() or "anuari" not in href.lower() or href in vistos:
                continue
            vistos.add(href)
            full = href if href.startswith("http") else f"https://{'3ta.cl' if tribunal == '3TA' else 'tribunalambiental.cl'}{href}"
            m = re.search(r"20\d\d", full)
            anio = m.group(0) if m else "Reciente"
            res.append({
                "tribunal": tribunal,
                "tribunal_nombre": NOMBRES[tribunal],
                "jurisdiccion": JURIS[tribunal],
                "tipo": "Anuario de Jurisprudencia Ambiental",
                "anio": anio,
                "titulo": f"Anuario de Jurisprudencia Ambiental {anio} — {tribunal} {NOMBRES[tribunal].split('de')[0].strip()}",
                "url_pdf": full,
                "archivo_local": full.rsplit("/", 1)[-1],
                "materia": "Jurisprudencia ambiental sistematizada por el tribunal",
            })
    except Exception as e:
        print(f"  [!] {tribunal}: {e}", file=sys.stderr)
    return res


def boletines_historicos(ya: set[str]) -> list[dict]:
    """Los boletines antiguos (n1..n39) no están en el listado; se buscan en el sitio."""
    res: list[dict] = []
    for n in range(1, 40):
        if str(n) in ya:
            continue
        posts: list[str] = []
        try:
            r = requests.get("https://3ta.cl/", params={"s": f"boletin n{n}"}, headers=HEADERS, timeout=25)
            if r.status_code == 200:
                posts = sorted(set(re.findall(r'href="(https://3ta\.cl/noticias/boletin-n' + str(n) + r'(?!\d)[^"]+)"', r.text)))
        except requests.RequestException as e:
            print(f"    [!] búsqueda del boletín n{n}: {e}", file=sys.stderr)
        for p in posts[:1]:
            pdf = primer_pdf(p)
            res.append({
                "tribunal": "3TA",
                "tribunal_nombre": NOMBRES["3TA"],
                "jurisdiccion": JURIS["3TA"],
                "tipo": "Boletín de Jurisprudencia Ambiental",
                "numero": str(n),
                "titulo": f"Boletín N° {n} de Jurisprudencia y Actualidad Normativa — 3TA",
                "url_post": p,
                "url_pdf": pdf or p,
                "materia": "Doctrina y resoluciones del Tercer Tribunal Ambiental",
            })
            print(f"    + histórico n{n}: {p[-60:]}")
        time.sleep(PAUSA)
    return res


def main() -> int:
    actuales = cargar()
    print(f"══ índice actual: {len(actuales)} publicaciones")
    claves = {clave(r) for r in actuales}

    print("══ cosechando novedades ══")
    candidatos: list[dict] = []
    candidatos += cosechar_3ta_boletines()
    numeros_ya = {str(r.get("numero")) for r in actuales if str(r.get("tipo", "")).startswith("Boletín")}
    print(f"  [3TA boletines] históricos: buscando los números que faltan ({sorted(numeros_ya)[:5]}…)")
    candidatos += boletines_historicos(numeros_ya)
    candidatos += cosechar_anuarios("3TA", "https://3ta.cl/publicaciones/anuario-de-jurisprudencia-ambiental/")
    candidatos += cosechar_anuarios("2TA", "https://tribunalambiental.cl/informacion-institucional/sobre-el-tribunal-ambiental/anuario/")

    nuevos = []
    for c in candidatos:
        k = clave(c)
        if k in claves:
            continue
        # para boletines, si ya existe el número, no duplicar por URL distinta
        claves.add(k)
        nuevos.append(c)

    print(f"══ nuevos: {len(nuevos)}")
    for n in nuevos[:40]:
        print(f"  + {n['tribunal']} {n['tipo'][:28]:30} {n.get('numero') or n.get('anio'):>5} · {n['titulo'][:60]}")

    todos = actuales + nuevos
    todos.sort(key=lambda r: (r.get("tipo", ""), r.get("tribunal", ""), str(r.get("numero") or r.get("anio") or "")))
    with open(JSONL, "w", encoding="utf-8") as f:
        for r in todos:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"══ total final: {len(todos)} publicaciones → {JSONL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
