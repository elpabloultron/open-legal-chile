#!/usr/bin/env python3
"""
Open Legal Chile — Convierte a Markdown las sentencias del Tribunal Constitucional
de los últimos dos años (descarga el PDF oficial y extrae el texto íntegro).

Salida:
  · jurisprudencia_tc/pdf/<rol>.pdf   (caché del PDF oficial)
  · jurisprudencia_tc/<rol>.md        (texto íntegro en Markdown, con ficha de cita)
  · data/jurisprudencia/tc_textos.jsonl (índice rol → archivo, caracteres y tokens)

Reanudable y paralelo (5 descargas simultáneas).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import ingesta_fuentes as ing  # noqa: E402
from scripts.cosechar_jurisprudencia_2anios import link_documento_tc  # noqa: E402

SENTENCIAS = BASE / "data" / "jurisprudencia" / "tc_sentencias_2anios.jsonl"
INDICE = BASE / "data" / "jurisprudencia" / "tc_textos.jsonl"
DIR_MD = BASE / "jurisprudencia_tc"
DIR_PDF = DIR_MD / "pdf"
UA = {"User-Agent": "OpenLegalChile/1.7.1 (Investigacion Juridica Soberana; Universidad de Los Lagos)"}
TRABAJADORES = 5
PDFTOTEXT = shutil.which("pdftotext") or "pdftotext"


def nombre_archivo(rol: str) -> str:
    limpio = re.sub(r"[^A-Za-z0-9._-]+", "_", rol.replace("Rol N° ", "").strip())
    return limpio or "sin_rol"


def numero_rol(reg: dict) -> int:
    """El número de rol de la sentencia: el folio de la ficha o, en registros viejos, el del rol."""
    m = re.search(r"\d[\d.]*", str(reg.get("folio") or reg.get("rol") or ""))
    return int(m.group().replace(".", "")) if m else 0


def link_oficial(reg: dict) -> str:
    """El PDF oficial pedido por número de rol. Los registros cosechados antes guardaban un enlace
    con el id de la ficha, que trae OTRA causa: se rehace siempre desde el rol."""
    numero = numero_rol(reg)
    return link_documento_tc(numero) if numero else str(reg.get("link_pdf") or "")


def corresponde(texto: str, numero: int) -> bool:
    """El documento es de esa causa: su comienzo nombra el rol («Rol 15.686-24», «Rol N° 15686-24-INA»,
    «Rol 15.738-2024»)."""
    if not numero:
        return False
    con_puntos = f"{numero:,}".replace(",", ".")
    patron = rf"(?<![\d.])(?:{re.escape(con_puntos)}|{numero})\s*-\s*(?:\d{{4}}|\d{{2}})(?!\d)"
    return re.search(patron, " ".join(texto[:8000].split())) is not None


def ficha(reg: dict, archivo: str) -> str:
    lineas = [
        f"# {reg.get('tipo', 'Sentencia')} — {reg['rol']}",
        "",
        "- **Tribunal:** Tribunal Constitucional de Chile",
        f"- **Rol:** {reg['rol']}",
        f"- **Fecha:** {reg.get('fecha', '')}",
    ]
    for etiqueta, clave in (("Gestión pendiente / carátula", "caratula"), ("Precepto legal", "precepto"), ("Resultado", "resultado")):
        if reg.get(clave):
            lineas.append(f"- **{etiqueta}:** {reg[clave]}")
    lineas.append(f"- **Documento oficial:** {reg.get('link_pdf', '')}")
    lineas.append(
        f"- **Fuente:** [Hugging Face - jurisprudencia_tc/{archivo}]"
        f"(https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile/blob/main/jurisprudencia_tc/{archivo})"
    )
    lineas += ["", "---", ""]
    return "\n".join(lineas)


def texto_completo(pdf: pathlib.Path) -> tuple[str, str]:
    """Texto íntegro si el PDF trae capa de texto; si es escaneo, OCR acotado."""
    prueba = subprocess.run([PDFTOTEXT, "-layout", "-f", "1", "-l", "5", str(pdf), "-"],  # nosec B603
                            capture_output=True, text=True, timeout=120)
    if len((prueba.stdout or "").strip()) / 5 >= 120:
        return ing._texto_de_pdf(pdf)
    return ing._texto_de_pdf(pdf, max_paginas=60)


def procesar(item: tuple[int, dict], rehacer: bool = False) -> tuple[int, str]:
    idx, reg = item
    nombre = nombre_archivo(reg["rol"])
    md = DIR_MD / f"{nombre}.md"
    pdf = DIR_PDF / f"{nombre}.pdf"
    if not rehacer and md.exists() and md.stat().st_size > 500:
        return idx, f"saltada|{nombre}|{md.stat().st_size}"
    reg["link_pdf"] = link_oficial(reg)
    try:
        if not pdf.exists():
            r = requests.get(reg["link_pdf"], headers=UA, timeout=120)
            r.raise_for_status()
            if not r.content.startswith(b"%PDF"):
                raise ValueError("la respuesta no es un PDF")
            pdf.write_bytes(r.content)
        texto, metodo = texto_completo(pdf)
        if len(texto.strip()) < 200:
            raise ValueError(f"texto insuficiente ({len(texto.strip())} chars, {metodo})")
        if not corresponde(texto, numero_rol(reg)):
            pdf.unlink(missing_ok=True)
            raise ValueError(f"el documento no es de la causa Rol {numero_rol(reg)}: no se escribe")
        cuerpo = ing._limpiar(texto)
        md.write_text(ficha(reg, f"{nombre}.md") + cuerpo + "\n", encoding="utf-8")
        return idx, f"ok|{nombre}|{len(cuerpo)}|{metodo}"
    except Exception as e:
        return idx, f"error|{nombre}|{type(e).__name__}: {str(e)[:70]}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Convierte a Markdown las sentencias del TC (últimos 2 años).")
    ap.add_argument("--limite", type=int, default=0, help="procesar solo las primeras N (prueba)")
    ap.add_argument("--rehacer", action="store_true",
                    help="reescribir también los .md que ya existen (p. ej., los que tenían el texto de otra causa)")
    args = ap.parse_args()
    DIR_PDF.mkdir(parents=True, exist_ok=True)
    filas = [json.loads(linea) for linea in open(SENTENCIAS, encoding="utf-8")]
    pendientes = [(i, r) for i, r in enumerate(filas)]
    if args.limite:
        pendientes = pendientes[: args.limite]
    print(f"══ {len(pendientes)} sentencias del TC por convertir (5 en paralelo)")

    ok = saltadas = fallidas = 0
    with ThreadPoolExecutor(max_workers=TRABAJADORES) as pool:
        futuros = {pool.submit(procesar, item, args.rehacer): item for item in pendientes}
        for n, fut in enumerate(as_completed(futuros), 1):
            idx, resultado = fut.result()
            partes = resultado.split("|")
            estado, nombre = partes[0], partes[1]
            reg = filas[idx]
            reg["archivo_md"] = f"jurisprudencia_tc/{nombre}.md"
            if estado == "ok":
                ok += 1
                reg["caracteres"] = int(partes[2])
                reg["tokens_aprox"] = int(partes[2]) // 4
                reg["metodo"] = partes[3] if len(partes) > 3 else "pdftotext"
            elif estado == "saltada":
                saltadas += 1
            else:
                fallidas += 1
                detalle = partes[2] if len(partes) > 2 else ""
                print(f"  [!] {nombre}: {detalle}")
                reg.setdefault("error_conversion", detalle)
            if n % 50 == 0:
                print(f"  [TC] {n}/{len(pendientes)} · ok {ok} · saltadas {saltadas} · fallidas {fallidas}")

    with open(SENTENCIAS, "w", encoding="utf-8") as f:
        for reg in filas:
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    with open(INDICE, "w", encoding="utf-8") as f:
        for reg in filas:
            if reg.get("archivo_md"):
                f.write(json.dumps({
                    "rol": reg["rol"], "fecha": reg.get("fecha"), "tipo": reg.get("tipo"),
                    "archivo_md": reg["archivo_md"], "caracteres": reg.get("caracteres"),
                    "tokens_aprox": reg.get("tokens_aprox"), "metodo": reg.get("metodo"),
                    "link_pdf": reg.get("link_pdf"),
                }, ensure_ascii=False) + "\n")
    print(f"══ listo: {ok} convertidas · {saltadas} ya estaban · {fallidas} con problema")
    print(f"   → {DIR_MD} · índice: {INDICE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
