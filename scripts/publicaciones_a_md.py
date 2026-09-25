#!/usr/bin/env python3
"""
Open Legal Chile — Convierte a Markdown las publicaciones oficiales de los Tribunales
Ambientales (anuarios y boletines de jurisprudencia): descarga el PDF y extrae el texto.

Salida:
  · publicaciones_ambientales/pdf/<nombre>.pdf   (caché del PDF oficial)
  · publicaciones_ambientales/<nombre>.md        (texto íntegro en Markdown, con ficha de cita)
  · data/jurisprudencia/publicaciones_textos.jsonl (índice → archivo, caracteres y tokens)

Reanudable y paralelo (4 descargas simultáneas). Los escaneos se OCR-ean solo en la muestra inicial.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import ingesta_fuentes as ing  # noqa: E402

PUBLICACIONES = BASE / "data" / "jurisprudencia" / "ambiental_boletines_anuarios.jsonl"
INDICE = BASE / "data" / "jurisprudencia" / "publicaciones_textos.jsonl"
DIR_MD = BASE / "publicaciones_ambientales"
DIR_PDF = DIR_MD / "pdf"
UA = {"User-Agent": "OpenLegalChile/1.6.5 (Investigacion Juridica Soberana; Universidad de Los Lagos)"}
TRABAJADORES = 4
PDFINFO = shutil.which("pdfinfo") or "pdfinfo"
PDFTOTEXT = shutil.which("pdftotext") or "pdftotext"
MAX_PAGINAS_OCR = 60  # escaneos enormes: OCR solo de la muestra inicial


def nombre_archivo(reg: dict) -> str:
    trib = reg.get("tribunal", "ta").lower()
    if str(reg.get("tipo", "")).startswith("Boletín"):
        return f"{trib}_boletin_{reg.get('numero', 'S-N')}"
    anio = str(reg.get("anio") or "s-a")
    return f"{trib}_anuario_{re.sub(r'[^0-9]', '', anio) or 's-a'}"


def ficha(reg: dict, archivo: str) -> str:
    lineas = [
        f"# {reg.get('titulo', 'Publicación')}",
        "",
        f"- **Tribunal:** {reg.get('tribunal_nombre', '')}",
        f"- **Tipo:** {reg.get('tipo', '')}",
        f"- **Jurisdicción:** {reg.get('jurisdiccion', '')}",
        f"- **Documento oficial:** {reg.get('url_pdf', '')}",
        f"- **Fuente:** [Hugging Face - publicaciones_ambientales/{archivo}]"
        f"(https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile/blob/main/publicaciones_ambientales/{archivo})",
        "",
        "---",
        "",
    ]
    return "\n".join(lineas)


def procesar(item: tuple[int, dict]) -> tuple[int, str]:
    idx, reg = item
    nombre = nombre_archivo(reg)
    md = DIR_MD / f"{nombre}.md"
    pdf = DIR_PDF / f"{nombre}.pdf"
    if md.exists() and md.stat().st_size > 500:
        return idx, f"saltada|{nombre}|{md.stat().st_size}"
    try:
        if not pdf.exists():
            r = requests.get(reg.get("url_pdf", ""), headers=UA, timeout=300)
            r.raise_for_status()
            if not r.content.startswith(b"%PDF"):
                raise ValueError("la respuesta no es un PDF")
            pdf.write_bytes(r.content)
            time.sleep(0.2)
        paginas = 0
        try:
            info = subprocess.run([PDFINFO, str(pdf)], capture_output=True, text=True, timeout=60)  # nosec B603
            for linea in info.stdout.splitlines():
                if linea.startswith("Pages:"):
                    paginas = int(linea.split()[1])
        except Exception:
            pass
        prueba = subprocess.run([PDFTOTEXT, "-layout", "-f", "1", "-l", "5", str(pdf), "-"],  # nosec B603
                                capture_output=True, text=True, timeout=120)
        if len((prueba.stdout or "").strip()) / 5 >= 120:
            texto, metodo = ing._texto_de_pdf(pdf)                      # texto íntegro
        else:
            texto, metodo = ing._texto_de_pdf(pdf, max_paginas=MAX_PAGINAS_OCR)  # escaneo: OCR acotado
            metodo += f" (escaneo: OCR de {MAX_PAGINAS_OCR} de {paginas or '?'} páginas)"
        if len(texto.strip()) < 200:
            raise ValueError(f"texto insuficiente ({len(texto.strip())} chars, {metodo})")
        cuerpo = ing._limpiar(texto)
        md.write_text(ficha(reg, f"{nombre}.md") + cuerpo + "\n", encoding="utf-8")
        return idx, f"ok|{nombre}|{len(cuerpo)}|{metodo}|{paginas}"
    except Exception as e:
        return idx, f"error|{nombre}|{type(e).__name__}: {str(e)[:80]}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Convierte a Markdown las publicaciones de los Tribunales Ambientales.")
    ap.add_argument("--limite", type=int, default=0, help="procesar solo las primeras N (prueba)")
    args = ap.parse_args()
    DIR_PDF.mkdir(parents=True, exist_ok=True)
    filas = [json.loads(linea) for linea in open(PUBLICACIONES, encoding="utf-8")]
    pendientes = [(i, r) for i, r in enumerate(filas)]
    if args.limite:
        pendientes = pendientes[: args.limite]
    print(f"══ {len(pendientes)} publicaciones ambientales por convertir (4 en paralelo)")

    ok = saltadas = fallidas = 0
    with ThreadPoolExecutor(max_workers=TRABAJADORES) as pool:
        futuros = {pool.submit(procesar, item): item for item in pendientes}
        for fut in as_completed(futuros):
            idx, resultado = fut.result()
            partes = resultado.split("|")
            estado, nombre = partes[0], partes[1]
            reg = filas[idx]
            reg["archivo_md"] = f"publicaciones_ambientales/{nombre}.md"
            if estado == "ok":
                ok += 1
                reg["caracteres"] = int(partes[2])
                reg["tokens_aprox"] = int(partes[2]) // 4
                reg["metodo"] = partes[3]
                try:
                    reg["paginas_pdf"] = int(partes[4]) or None
                except (IndexError, ValueError):
                    pass
                print(f"  ✓ {nombre} · {int(partes[2]):,} chars · {partes[3]}")
            elif estado == "saltada":
                saltadas += 1
            else:
                fallidas += 1
                print(f"  [!] {nombre}: {partes[2] if len(partes) > 2 else ''}")

    with open(PUBLICACIONES, "w", encoding="utf-8") as f:
        for reg in filas:
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    with open(INDICE, "w", encoding="utf-8") as f:
        for reg in filas:
            if reg.get("archivo_md") and reg.get("caracteres"):
                f.write(json.dumps({
                    "tribunal": reg.get("tribunal"), "tipo": reg.get("tipo"),
                    "numero": reg.get("numero"), "anio": reg.get("anio"), "titulo": reg.get("titulo"),
                    "archivo_md": reg["archivo_md"], "caracteres": reg.get("caracteres"),
                    "tokens_aprox": reg.get("tokens_aprox"), "metodo": reg.get("metodo"),
                    "url_pdf": reg.get("url_pdf"),
                }, ensure_ascii=False) + "\n")
    print(f"══ listo: {ok} convertidas · {saltadas} ya estaban · {fallidas} con problema")
    print(f"   → {DIR_MD} · índice: {INDICE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
