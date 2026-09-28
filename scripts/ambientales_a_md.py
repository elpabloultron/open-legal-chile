#!/usr/bin/env python3
"""
Open Legal Chile — Convierte a Markdown las 886 sentencias ambientales
(1TA, 2TA y 3TA) descargando el PDF oficial y extrayendo el texto íntegro.

Salida:
  · jurisprudencia_ambiental/pdf/<tribunal>-<rol>.pdf   (caché del PDF oficial)
  · jurisprudencia_ambiental/<tribunal>/<rol>.md        (texto íntegro + ficha de cita)
  · data/jurisprudencia/ambiental_textos.jsonl          (índice archivo → caracteres)

Reanudable y paralelo (4 descargas simultáneas, con reintentos y pausa).
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

SENTENCIAS = BASE / "data" / "jurisprudencia" / "ambiental_sentencias.jsonl"
INDICE = BASE / "data" / "jurisprudencia" / "ambiental_textos.jsonl"
DIR_MD = BASE / "jurisprudencia_ambiental"
DIR_PDF = DIR_MD / "pdf"
UA = {"User-Agent": "OpenLegalChile/1.8.0 (Investigacion Juridica Soberana; Universidad de Los Lagos)"}
TRABAJADORES = 4
REINTENTOS = 3
PAUSA = 1.0
PDFTOTEXT = shutil.which("pdftotext") or "pdftotext"


def nombre_archivo(rol: str) -> str:
    limpio = re.sub(r"[^A-Za-z0-9._-]+", "_", str(rol).replace("Rol N° ", "").strip())
    return limpio or "sin_rol"


def ficha(reg: dict, archivo: str, nota: str = "") -> str:
    lineas = [
        f"# {reg.get('tipo', 'Sentencia')} — {reg['rol']}",
        "",
        f"- **Tribunal:** {reg.get('tribunal_nombre', reg.get('tribunal', ''))}",
        f"- **Jurisdicción:** {reg.get('jurisdiccion', '')}",
        f"- **Rol:** {reg['rol']}",
        f"- **Fecha:** {reg.get('fecha', '')}",
        f"- **Carátula:** {reg.get('caratula', '')}",
        f"- **Redactor:** {reg.get('redactor', '')}",
        f"- **Integración:** {reg.get('integracion', '')}",
        f"- **Materia:** {reg.get('materia', '')}",
        f"- **Resuelve:** {reg.get('resuelve', '')}",
        f"- **Documento oficial:** {reg.get('url_pdf', '')}",
        f"- **Expediente:** {reg.get('url_expediente', '')}",
    ]
    if nota:
        lineas += ["", f"> {nota}"]
    lineas += [
        f"- **Fuente:** [Hugging Face - jurisprudencia_ambiental/{archivo}]"
        f"(https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile/blob/main/jurisprudencia_ambiental/{archivo})",
        "", "---", "",
    ]
    return "\n".join(lineas)


def escribir_ficha(reg: dict, dir_md: pathlib.Path) -> str:
    """Ficha de metadatos cuando el PDF público no está disponible. Nunca se inventa texto."""
    relativo = f"{nombre_archivo(reg.get('tribunal', 'ta'))}/{nombre_archivo(reg['rol'])}.md"
    md = dir_md / relativo
    nota = ("Ficha de metadatos: el PDF público del tribunal ya no responde y no se puede "
            "extraer el texto íntegro. No se inventa contenido.")
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(ficha(reg, relativo, nota), encoding="utf-8")
    return relativo


def texto_completo(pdf: pathlib.Path) -> tuple[str, str]:
    """Texto íntegro si el PDF trae capa de texto; si es escaneo, OCR completo (tope 120 páginas)."""
    prueba = subprocess.run([PDFTOTEXT, "-layout", "-f", "1", "-l", "5", str(pdf), "-"],  # nosec B603
                            capture_output=True, text=True, timeout=120)
    if len((prueba.stdout or "").strip()) >= 600:
        return ing._texto_de_pdf(pdf)
    return ing._texto_de_pdf(pdf, max_paginas=120)


def convertir(reg: dict, pdf: pathlib.Path, dir_md: pathlib.Path) -> tuple[str, str, int, str]:
    """Convierte un PDF local a Markdown. Devuelve (estado, archivo relativo, caracteres, método)."""
    nombre = f"{nombre_archivo(reg.get('tribunal', 'ta'))}-{nombre_archivo(reg['rol'])}"
    relativo = f"{nombre_archivo(reg.get('tribunal', 'ta'))}/{nombre_archivo(reg['rol'])}.md"
    md = dir_md / relativo
    try:
        texto, metodo = texto_completo(pdf)
        if len(texto.strip()) < 200:
            raise ValueError(f"texto insuficiente ({len(texto.strip())} chars, {metodo})")
        cuerpo = ing._limpiar(texto)
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(ficha(reg, relativo) + cuerpo + "\n", encoding="utf-8")
        return "ok", relativo, len(cuerpo), metodo
    except Exception as e:  # noqa: BLE001 — cada fallo se reporta, no se inventa texto
        return "error", f"{nombre}|{type(e).__name__}: {str(e)[:70]}", 0, ""


def descargar(url: str, destino: pathlib.Path) -> None:
    ultimo: Exception = RuntimeError("sin intentos")
    for intento in range(1, REINTENTOS + 1):
        try:
            r = requests.get(url, headers=UA, timeout=120)
            r.raise_for_status()
            if not r.content.startswith(b"%PDF"):
                raise ValueError("la respuesta no es un PDF")
            destino.write_bytes(r.content)
            return
        except Exception as e:  # noqa: BLE001
            ultimo = e
            time.sleep(PAUSA * intento)
    raise ultimo


def procesar(item: tuple[int, dict]) -> tuple[int, str]:
    idx, reg = item
    nombre = f"{nombre_archivo(reg.get('tribunal', 'ta'))}-{nombre_archivo(reg['rol'])}"
    md = DIR_MD / nombre_archivo(reg.get("tribunal", "ta")) / f"{nombre_archivo(reg['rol'])}.md"
    pdf = DIR_PDF / f"{nombre}.pdf"
    if md.exists() and md.stat().st_size > 500:
        return idx, "saltada|" + str(md.relative_to(DIR_MD))
    try:
        if not pdf.exists():
            descargar(reg.get("url_pdf", ""), pdf)
            time.sleep(PAUSA)
    except Exception as e:  # sin PDF público → ficha con metadatos y enlaces
        relativo = escribir_ficha(reg, DIR_MD)
        return idx, f"ficha|{relativo}|{type(e).__name__}: {str(e)[:50]}"
    try:
        estado, archivo, caracteres, metodo = convertir(reg, pdf, DIR_MD)
        if estado == "ok":
            return idx, f"ok|{archivo}|{caracteres}|{metodo}"
        return idx, f"error|{nombre}|{archivo.split('|', 1)[-1]}"
    except Exception as e:  # noqa: BLE001
        return idx, f"error|{nombre}|{type(e).__name__}: {str(e)[:70]}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Convierte a Markdown las 886 sentencias ambientales.")
    ap.add_argument("--limite", type=int, default=0, help="procesar solo las primeras N (prueba)")
    args = ap.parse_args()
    DIR_PDF.mkdir(parents=True, exist_ok=True)
    filas = [json.loads(linea) for linea in open(SENTENCIAS, encoding="utf-8")]  # noqa: SIM115
    pendientes = [(i, r) for i, r in enumerate(filas)]
    if args.limite:
        pendientes = pendientes[: args.limite]
    print(f"══ {len(pendientes)} sentencias ambientales por convertir ({TRABAJADORES} en paralelo)")

    ok = saltadas = fallidas = fichas = 0
    with ThreadPoolExecutor(max_workers=TRABAJADORES) as pool:
        futuros = {pool.submit(procesar, item): item for item in pendientes}
        for n, fut in enumerate(as_completed(futuros), 1):
            idx, resultado = fut.result()
            partes = resultado.split("|")
            estado, nombre = partes[0], partes[1]
            reg = filas[idx]
            if estado == "ok":
                ok += 1
                reg["archivo_md"] = f"jurisprudencia_ambiental/{partes[1]}"
                reg["tipo_md"] = "texto_completo"
                reg["caracteres"] = int(partes[2])
                reg["tokens_aprox"] = int(partes[2]) // 4
                reg["metodo"] = partes[3] if len(partes) > 3 else "pdftotext"
            elif estado == "ficha":
                fichas += 1
                reg["archivo_md"] = f"jurisprudencia_ambiental/{partes[1]}"
                reg["tipo_md"] = "ficha"
                reg["motivo_ficha"] = partes[2] if len(partes) > 2 else ""
                reg.pop("error_conversion", None)
            elif estado == "saltada":
                saltadas += 1
                reg["archivo_md"] = f"jurisprudencia_ambiental/{nombre}"
                reg.setdefault("tipo_md", "texto_completo")
            else:
                fallidas += 1
                detalle = partes[2] if len(partes) > 2 else ""
                print(f"  [!] {nombre}: {detalle}")
                reg.setdefault("error_conversion", detalle)
            if n % 50 == 0:
                print(f"  [TA] {n}/{len(pendientes)} · texto {ok} · fichas {fichas} · "
                      f"saltadas {saltadas} · fallidas {fallidas}")

    with open(SENTENCIAS, "w", encoding="utf-8") as f:
        for reg in filas:
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    total_completo, total_fichas = escribir_salidas(filas)
    print(f"══ listo: {ok} con texto íntegro · {fichas} fichas · {saltadas} ya estaban · "
          f"{fallidas} con problema")
    print(f"   → {DIR_MD} · índice: {INDICE} · README: README.md · "
          f"texto íntegro {total_completo} · fichas {total_fichas}")
    return 0


def escribir_salidas(filas: list) -> tuple[int, int]:
    """Regenera el índice y el README de la colección desde las filas del registro.

    Se separa de main para que una recuperación puntual (p. ej. una URL que quedó sucia
    en la cosecha) pueda volver a escribir las salidas sin recorrer las 886 de nuevo.
    Devuelve (con texto íntegro, fichas).
    """
    with open(INDICE, "w", encoding="utf-8") as f:
        for reg in filas:
            if reg.get("archivo_md"):
                f.write(json.dumps({
                    "tribunal": reg.get("tribunal"), "rol": reg["rol"], "fecha": reg.get("fecha"),
                    "archivo_md": reg["archivo_md"], "tipo_md": reg.get("tipo_md"),
                    "caracteres": reg.get("caracteres"),
                    "tokens_aprox": reg.get("tokens_aprox"), "metodo": reg.get("metodo"),
                    "url_pdf": reg.get("url_pdf"),
                }, ensure_ascii=False) + "\n")

    conteo: dict[str, list[int]] = {}
    for reg in filas:
        if reg.get("archivo_md"):
            clave = reg.get("tribunal_nombre", reg.get("tribunal", "?"))
            par = conteo.setdefault(clave, [0, 0])
            par[0 if reg.get("tipo_md") == "texto_completo" else 1] += 1
    total_completo = sum(p[0] for p in conteo.values())
    total_fichas = sum(p[1] for p in conteo.values())
    readme = DIR_MD / "README.md"
    filas_readme = "\n".join(
        f"- {nombre}: {p[0]} con texto íntegro · {p[1]} "
        f"{'ficha' if p[1] == 1 else 'fichas'}" for nombre, p in sorted(conteo.items()))
    readme.write_text(
        "# Jurisprudencia ambiental\n\n"
        f"{total_completo + total_fichas} sentencias de los Tribunales Ambientales (1TA, 2TA y 3TA):\n"
        f"**{total_completo}** con su texto completo en Markdown —sin resumir— y su enlace al\n"
        f"documento oficial, y **{total_fichas}** como ficha de metadatos (el portal del tribunal\n"
        "ya no sirve su PDF público; no se inventa texto).\n\n"
        f"{filas_readme}\n\n"
        "- Cita: `[Hugging Face - jurisprudencia_ambiental/<tribunal>/<rol>.md]`\n"
        "- Fuente: portales de los Tribunales Ambientales de Chile (documentos públicos).\n",
        encoding="utf-8")
    return total_completo, total_fichas


if __name__ == "__main__":
    sys.exit(main())
