#!/usr/bin/env python3
"""
Open Legal Chile — Convierte a Markdown las sentencias del Tribunal Constitucional
de los últimos dos años (descarga el PDF oficial y extrae el texto íntegro).

Salida:
  · jurisprudencia_tc/pdf/<rol>.pdf   (caché del PDF oficial)
  · jurisprudencia_tc/<rol>.md        (texto íntegro en Markdown, con ficha de cita)
  · data/jurisprudencia/tc_textos.jsonl (índice rol → archivo, caracteres y tokens)

Reanudable y paralelo (3 descargas simultáneas, con reintentos).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import ingesta_fuentes as ing  # noqa: E402
from mapa_corpus.texto import fecha_resolucion  # noqa: E402
from scripts.cosechar_jurisprudencia_2anios import link_documento_tc  # noqa: E402

SENTENCIAS = BASE / "data" / "jurisprudencia" / "tc_sentencias_2anios.jsonl"
INDICE = BASE / "data" / "jurisprudencia" / "tc_textos.jsonl"
DIR_MD = BASE / "jurisprudencia_tc"
DIR_PDF = DIR_MD / "pdf"
UA = {"User-Agent": "OpenLegalChile/1.7.1 (Investigacion Juridica Soberana; Universidad de Los Lagos)"}
TRABAJADORES = 3
REINTENTABLES = {429, 500, 502, 503, 504}
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
    """El documento es de esa causa: nombra su rol al comienzo (sentencias: «Rol 15.686-24»,
    «Rol 15.738-2024», «Rol N° 15686-24-INA») o al pie (las resoluciones de inadmisibilidad solo lo
    nombran antes de las firmas: «Rol Nº 15.707-24 INA.»). También «Rol N° 16.615-INA» (sin año),
    las acumuladas «Rol 15.713 (15.777)-24» y las listas «Rol 11.315/11.317-21-CPT»."""
    if not numero:
        return False
    plano = " ".join(texto.split())
    zona = plano[:8000] + " … " + plano[-3000:]
    con_puntos = f"{numero:,}".replace(",", ".")
    num = rf"(?<![\d.])(?:{re.escape(con_puntos)}|{numero})(?!\d|\.\d)"
    patron = (rf"{num}\s*-\s*(?:\d{{4}}|\d{{2}}|[A-Z]{{2,5}})(?![\dA-Za-z])"
              rf"|(?i:\bRol(?:es)?)\s*(?:N[°º]?\s*)?(?:[\d.]+\s*(?:/|\(|y|,)\s*)*{num}\s*(?:/|\(|\))")
    return re.search(patron, zona) is not None


_RE_CORREO = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Identificadores de una gestión (RIT, RUC, Rol): «C-4106-2020», «1700797652-6», «Rol N° 49.322-2021».
_RE_ID_GESTION = re.compile(r"\d[\d.]{2,}\s*-\s*(?:\d{4}|\d{2}|[\dkK])(?![\dkK])|(?<![\d.])\d{1,2}\s*-\s*\d{4}(?!\d)")


def ocultar_correos(texto: str) -> str:
    """Las resoluciones traen impresos los correos de notificación (de abogados y partes)."""
    return _RE_CORREO.sub("[correo omitido]", texto)


def gestion_verificada(gestion: str, texto: str) -> str:
    """La gestión pendiente de la ficha solo si sus identificadores (RIT, RUC, Rol) aparecen en el
    documento: en las fichas antiguas del buscador suele ser la de otra causa."""
    ids = {re.sub(r"[.\s]", "", m.group()).upper() for m in _RE_ID_GESTION.finditer(gestion or "")}
    if not ids:
        return ""
    plano = re.sub(r"[.\s]", "", texto).upper()
    return gestion if any(re.search(rf"(?<!\d){re.escape(i)}(?![\dK])", plano) for i in ids) else ""


def rol_oficial(texto: str, numero: int) -> str:
    """El rol tal como lo cita el TC («Rol N° 9231-20-INA»), si el documento lo trae completo."""
    con_puntos = f"{numero:,}".replace(",", ".")
    m = re.search(rf"(?<![\d.])(?:{re.escape(con_puntos)}|{numero})\s*-\s*(\d{{2}})\s*-?\s*([A-Z]{{2,5}})\b",
                  " ".join(texto.split()))
    return f"Rol N° {numero}-{m.group(1)}-{m.group(2)}" if m else ""


def tipo_documento(texto: str, tipo_ficha: str) -> str:
    """El tipo según el documento: a veces la ficha dice «STC» y el PDF es una inadmisibilidad."""
    plano = " ".join(texto[:20000].split())
    es_sentencia = re.search(r"\bSentencia\b", plano[:600], re.IGNORECASE) is not None
    inadmisible = re.search(r"declara\s+inadmisible", plano, re.IGNORECASE) is not None
    if tipo_ficha.endswith("-STC") and not es_sentencia and inadmisible:
        return tipo_ficha[: -len("STC")] + "Inadmisibilidad"
    if tipo_ficha.endswith("-Inadmisibilidad") and es_sentencia and not inadmisible:
        return tipo_ficha[: -len("Inadmisibilidad")] + "STC"
    return tipo_ficha


def ajustar_con_documento(reg: dict, texto: str, numero: int) -> dict:
    """La ficha corregida con lo que dice el documento oficial: fecha, tipo, rol citable y gestión."""
    datos = dict(reg)
    fecha_doc = fecha_resolucion(texto)
    if fecha_doc and fecha_doc != reg.get("fecha"):
        datos["fecha"], datos["fecha_ficha"] = fecha_doc, reg.get("fecha", "")
    tipo = tipo_documento(texto, str(reg.get("tipo") or ""))
    if tipo != reg.get("tipo"):
        datos["tipo"], datos["tipo_ficha"] = tipo, reg.get("tipo", "")
    datos["rol_oficial"] = rol_oficial(texto, numero)
    datos["caratula"] = gestion_verificada(str(reg.get("caratula") or ""), texto)
    return datos


def descargar_pdf(url: str, intentos: int = 4) -> bytes:
    """El PDF oficial, con reintentos ante 429/5xx o cortes. Hay PDFs con bytes antes de «%PDF»
    (la norma admite basura en los primeros 1 024): se recortan."""
    for intento in range(intentos):
        try:
            r = requests.get(url, headers=UA, timeout=120)
            estado = getattr(r, "status_code", 200)
            if estado in REINTENTABLES:
                raise requests.ConnectionError(f"HTTP {estado}")
            r.raise_for_status()
            inicio = r.content.find(b"%PDF", 0, 1024)
            if inicio < 0:
                raise ValueError("la respuesta no es un PDF")
            return r.content[inicio:]
        except (requests.ConnectionError, requests.Timeout) as e:
            if intento == intentos - 1:
                raise ValueError(f"el TC no respondió: {str(e)[:60]}") from e
            time.sleep(3 * 2 ** intento)
    raise ValueError("el TC no respondió")


def _valor(reg: dict, clave: str) -> str:
    valor = str(reg.get(clave) or "").strip()
    return "" if valor in ("None", "null") else valor


def ficha(reg: dict, archivo: str) -> str:
    lineas = [
        f"# {reg.get('tipo') or 'Sentencia'} — {reg['rol']}",
        "",
        "- **Tribunal:** Tribunal Constitucional de Chile",
        f"- **Rol:** {reg['rol']}",
    ]
    if _valor(reg, "rol_oficial"):
        lineas.append(f"- **Rol oficial:** {_valor(reg, 'rol_oficial')}")
    lineas.append(f"- **Fecha:** {_valor(reg, 'fecha')}")
    for etiqueta, clave in (("Sala", "sala"), ("Gestión pendiente / carátula", "caratula"),
                            ("Precepto legal", "precepto"), ("Resultado", "resultado"),
                            ("Fecha en la ficha del buscador", "fecha_ficha"),
                            ("Tipo en la ficha del buscador", "tipo_ficha")):
        if _valor(reg, clave):
            lineas.append(f"- **{etiqueta}:** {_valor(reg, clave)}")
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
    numero = numero_rol(reg)
    try:
        # Con --rehacer se baja siempre: el PDF en caché puede ser el de otra causa (cosecha vieja).
        if rehacer or not pdf.exists():
            pdf.write_bytes(descargar_pdf(reg["link_pdf"]))
        texto, metodo = texto_completo(pdf)
        if len(texto.strip()) < 200:
            raise ValueError(f"texto insuficiente ({len(texto.strip())} chars, {metodo})")
        if not corresponde(texto, numero):
            pdf.unlink(missing_ok=True)
            raise ValueError(f"el documento no es de la causa Rol {numero}: no se escribe")
        datos = ajustar_con_documento(reg, texto, numero)
        cuerpo = ocultar_correos(ing._limpiar(texto))
        md.write_text(ficha(datos, f"{nombre}.md") + cuerpo + "\n", encoding="utf-8")
        for clave in ("fecha", "fecha_ficha", "tipo", "tipo_ficha", "rol_oficial", "caratula"):
            if datos.get(clave) != reg.get(clave):
                reg[clave] = datos.get(clave)
        return idx, f"ok|{nombre}|{len(cuerpo)}|{metodo}"
    except Exception as e:
        return idx, f"error|{nombre}|{type(e).__name__}: {str(e)[:70]}"


def resumen_github(lineas: list[str]) -> None:
    """Agrega el resumen al de la corrida de la Action (si corre en una)."""
    destino = os.environ.get("GITHUB_STEP_SUMMARY")
    if destino:
        with open(destino, "a", encoding="utf-8") as f:
            f.write("\n".join(lineas) + "\n")


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
    print(f"══ {len(pendientes)} sentencias del TC por convertir ({TRABAJADORES} en paralelo)")

    ok = saltadas = fallidas = 0
    errores: list[str] = []
    with ThreadPoolExecutor(max_workers=TRABAJADORES) as pool:
        futuros = {pool.submit(procesar, item, args.rehacer): item for item in pendientes}
        for n, fut in enumerate(as_completed(futuros), 1):
            idx, resultado = fut.result()
            partes = resultado.split("|")
            estado, nombre = partes[0], partes[1]
            reg = filas[idx]
            reg["archivo_md"] = f"jurisprudencia_tc/{nombre}.md"
            reg.pop("error_conversion", None)
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
                errores.append(f"{nombre}: {detalle}")
                reg.pop("archivo_md", None)  # el índice no apunta a un .md que no se escribió
                reg["error_conversion"] = detalle
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
    resumen_github([f"### Conversión del TC: {ok} convertidas · {saltadas} ya estaban · {fallidas} con problema", ""]
                   + [f"- {e}" for e in sorted(errores)[:200]])
    print(f"   → {DIR_MD} · índice: {INDICE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
