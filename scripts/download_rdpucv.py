#!/usr/bin/env python3
"""
download_rdpucv.py — Descarga resiliente y concurrente de PDFs de la Revista de Derecho PUCV.
Soporta reanudación automática, reintentos con backoff exponencial y registro de estado.
"""

import argparse
import concurrent.futures
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Tuple

DATA_DIR = pathlib.Path(__file__).parent.parent / "data" / "rdpucv"
MANIFEST_PATH = DATA_DIR / "catalogo_articulos.jsonl"
PDF_DIR = DATA_DIR / "pdfs"
LOG_PATH = DATA_DIR / "descargas_log.jsonl"


def limpiar_nombre(texto: str, max_len: int = 80) -> str:
    """Genera un nombre de archivo seguro y limpio a partir del título."""
    texto = texto.lower()
    texto = re.sub(r"[áàäâ]", "a", texto)
    texto = re.sub(r"[éèëê]", "e", texto)
    texto = re.sub(r"[íìïî]", "i", texto)
    texto = re.sub(r"[óòöô]", "o", texto)
    texto = re.sub(r"[úùüû]", "u", texto)
    texto = re.sub(r"ñ", "n", texto)
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    texto = texto.strip("_")
    return texto[:max_len]


def cargar_catalogo(filtro_anio: str = "", limite: int = 0) -> List[Dict[str, Any]]:
    """Carga los artículos desde el catálogo JSONL."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"No se encontró el catálogo en {MANIFEST_PATH}. Ejecuta harvest_rdpucv.py primero.")

    articulos = []
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            if filtro_anio and str(item.get("anio", "")) != filtro_anio:
                continue
            articulos.append(item)

    if limite > 0:
        articulos = articulos[:limite]

    return articulos


def descargar_articulo(articulo: Dict[str, Any], reintentos: int = 4) -> Tuple[bool, str, int]:
    """
    Descarga un PDF de un artículo. Retorna (exito, mensaje, bytes).
    """
    art_id = articulo.get("article_id", "sin_id")
    anio = str(articulo.get("anio") or "sin_anio")
    volumen = str(articulo.get("volumen") or "vol_x")
    titulo = articulo.get("title", "articulo")
    url = articulo.get("download_url")

    if not url:
        return False, f"Sin URL de descarga para artículo {art_id}", 0

    subcarpeta = PDF_DIR / f"vol_{volumen}_{anio}"
    subcarpeta.mkdir(parents=True, exist_ok=True)

    slug = limpiar_nombre(titulo)
    destino = subcarpeta / f"{art_id}_{slug}.pdf"

    # Si ya existe y pesa más de 5 KB, ya está descargado
    if destino.exists() and destino.stat().st_size > 5120:
        return True, f"Ya existe: {destino.name}", destino.stat().st_size

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/pdf,application/xhtml+xml,text/html;q=0.9,*/*;q=0.8",
    }

    for intento in range(1, reintentos + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as resp:
                # Comprobar si redirigió a un visor HTML o entregó PDF
                content_type = resp.headers.get("Content-Type", "")
                datos = resp.read()

                # Si OJS devolvió HTML con un iframe de PDF o visor
                if "application/pdf" not in content_type and len(datos) < 50000:
                    html_text = datos.decode("utf-8", errors="ignore")
                    m = re.search(r'href="([^"]+/article/download/[^"]+)"', html_text)
                    if m:
                        url_directa = m.group(1).replace("&amp;", "&")
                        req_directa = urllib.request.Request(url_directa, headers=headers)
                        with urllib.request.urlopen(req_directa, timeout=45) as resp2:
                            datos = resp2.read()

                if len(datos) > 1024:
                    with open(destino, "wb") as f_out:
                        f_out.write(datos)
                    return True, f"Descargado ({len(datos):,} bytes): {destino.name}", len(datos)

        except Exception as e:
            if intento == reintentos:
                return False, f"Error tras {reintentos} intentos en art {art_id}: {e}", 0
            time.sleep(1.5 * intento)

    return False, f"Fallo desconocido en art {art_id}", 0


def descargar_lote_concurrente(articulos: List[Dict[str, Any]], hilos: int = 4) -> Dict[str, Any]:
    """Descarga concurrentemente la lista de artículos."""
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    total = len(articulos)
    print(f"[*] Iniciando descarga de {total} artículos con {hilos} hilos concurrentes...")

    exitos = 0
    fallidos = 0
    ya_existentes = 0
    bytes_totales = 0
    t0 = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=hilos) as executor:
        futuros = {executor.submit(descargar_articulo, art): art for art in articulos}
        for i, fut in enumerate(concurrent.futures.as_completed(futuros), start=1):
            art = futuros[fut]
            try:
                ok, msg, tam = fut.result()
                if ok:
                    if "Ya existe" in msg:
                        ya_existentes += 1
                    else:
                        exitos += 1
                    bytes_totales += tam
                else:
                    fallidos += 1
                    print(f"  [X] ({i}/{total}) {msg}")

                if i % 25 == 0 or i == total:
                    dur = round(time.perf_counter() - t0, 1)
                    mb = round(bytes_totales / (1024 * 1024), 1)
                    print(f"  → Progreso: {i}/{total} ({exitos} nuevos, {ya_existentes} cacheados, {fallidos} fallos) | {mb} MB | {dur}s")

            except Exception as e:
                fallidos += 1
                print(f"  [!] Excepción procesando {art.get('article_id')}: {e}")

    duracion = round(time.perf_counter() - t0, 2)
    mb_totales = round(bytes_totales / (1024 * 1024), 2)
    print("\n" + "=" * 60)
    print("RESUMEN DE DESCARGAS:")
    print(f"  Total procesados: {total}")
    print(f"  Descargados nuevos: {exitos}")
    print(f"  Preexistentes en caché: {ya_existentes}")
    print(f"  Fallidos: {fallidos}")
    print(f"  Volumen total: {mb_totales} MB")
    print(f"  Tiempo total: {duracion} s")
    print("=" * 60)

    return {
        "total": total,
        "exitos": exitos,
        "ya_existentes": ya_existentes,
        "fallidos": fallidos,
        "mb_totales": mb_totales,
        "duracion_segundos": duracion,
    }


def main():
    parser = argparse.ArgumentParser(description="Descargador concurrente de Revista de Derecho PUCV.")
    parser.add_argument("--anio", default="", help="Filtrar por año (ej. '2024').")
    parser.add_argument("--limite", type=int, default=0, help="Límite de artículos a descargar (0 = todos).")
    parser.add_argument("--hilos", type=int, default=4, help="Número de hilos concurrentes.")
    args = parser.parse_args()

    articulos = cargar_catalogo(filtro_anio=args.anio, limite=args.limite)
    descargar_lote_concurrente(articulos, hilos=args.hilos)


if __name__ == "__main__":
    main()
