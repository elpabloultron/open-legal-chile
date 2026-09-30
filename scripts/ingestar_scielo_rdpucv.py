#!/usr/bin/env python3
"""
ingestar_scielo_rdpucv.py — Ingesta de alta velocidad para la Revista de Derecho PUCV
a través del repositorio oficial SciELO CONICYT (2002 - 2023).
Descarga PDFs mediante CDN directa sin rate limits, los convierte a Markdown canónico
y los integra con el catálogo de Open Legal Chile.
"""

import concurrent.futures
import json
import os
import pathlib
import re
import sys
import time
import urllib.request
import defusedxml.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))
from config import safe_urlopen

from scripts.convert_rdpucv_to_md import inferir_area, extraer_instituciones_y_normas, limpiar_texto_articulo, extraer_texto_pdf

DATA_DIR = ROOT_DIR / "data" / "rdpucv"
SCIELO_PDF_DIR = DATA_DIR / "pdfs_scielo"
OUTPUT_DIR = ROOT_DIR / "doctrina" / "revistas" / "rdpucv"
MANIFEST_SCIELO = DATA_DIR / "catalogo_scielo.jsonl"

OAI_SCIELO = "https://scielo.conicyt.cl/oai/scielo-oai.php"
NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
}


def slugify(texto: str, max_len: int = 60) -> str:
    texto = texto.lower()
    texto = re.sub(r"[áàäâ]", "a", texto)
    texto = re.sub(r"[éèëê]", "e", texto)
    texto = re.sub(r"[íìïî]", "i", texto)
    texto = re.sub(r"[óòöô]", "o", texto)
    texto = re.sub(r"[úùüû]", "u", texto)
    texto = re.sub(r"ñ", "n", texto)
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return texto.strip("_")[:max_len]


def cosechar_catalogo_scielo() -> List[Dict[str, Any]]:
    """Descarga todos los registros OAI-PMH de la Revista de Derecho en SciELO CONICYT."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if MANIFEST_SCIELO.exists() and MANIFEST_SCIELO.stat().st_size > 1000:
        with open(MANIFEST_SCIELO, "r", encoding="utf-8") as f:
            articulos = [json.loads(line) for line in f if line.strip()]
        print(f"[*] Catálogo SciELO existente cargado: {len(articulos)} artículos.")
        return articulos

    print("[*] Cosechando catálogo SciELO CONICYT (ISSN 0718-6851)...")
    articulos = []
    url = f"{OAI_SCIELO}?verb=ListRecords&metadataPrefix=oai_dc&set=0718-6851"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) OpenLegalChile/1.0"}
    batch = 1

    while True:
        req = urllib.request.Request(url, headers=headers)
        with safe_urlopen(req, timeout=30) as resp:
            tree = ET.parse(resp)  # nosec B314
        root = tree.getroot()
        records = root.findall(".//oai:record", NS)

        for rec in records:
            header = rec.find("oai:header", NS)
            if header is None or header.attrib.get("status") == "deleted":
                continue

            ident_elem = header.find("oai:identifier", NS)
            raw_id = ident_elem.text.strip() if ident_elem is not None and ident_elem.text else ""
            pid_match = re.search(r"(S\d{4}-\d{4}\d+)", raw_id)
            pid = pid_match.group(1) if pid_match else raw_id.split(":")[-1]

            metadata = rec.find("oai:metadata", NS)
            if metadata is None:
                continue
            dc = metadata.find("oai_dc:dc", NS)
            if dc is None:
                continue

            titles = [t.text.strip() for t in dc.findall("dc:title", NS) if t.text]
            title = titles[0] if titles else "Sin Título"
            creators = [c.text.strip() for c in dc.findall("dc:creator", NS) if c.text]
            descriptions = [d.text.strip() for d in dc.findall("dc:description", NS) if d.text]
            abstract = descriptions[0] if descriptions else ""
            subjects = [s.text.strip() for s in dc.findall("dc:subject", NS) if s.text]
            sources = [s.text.strip() for s in dc.findall("dc:source", NS) if s.text]
            source = sources[0] if sources else ""
            dates = [d.text.strip() for d in dc.findall("dc:date", NS) if d.text]
            date_pub = dates[0] if dates else ""

            # Extraer volumen, número y año
            anio = ""
            vol_num = ""
            m_anio = re.search(r"\b(19\d{2}|20\d{2})\b", source or date_pub)
            if m_anio:
                anio = m_anio.group(1)
            m_num = re.search(r"n\.(\d+)", source)
            if m_num:
                vol_num = m_num.group(1)

            articulos.append({
                "pid": pid,
                "title": title,
                "authors": creators,
                "abstract": abstract,
                "subjects": subjects,
                "source": source,
                "volumen": vol_num,
                "anio": anio,
                "date": date_pub,
                "url_scielo": f"https://www.scielo.cl/scielo.php?script=sci_arttext&pid={pid}",
                "url_sci_pdf": f"https://scielo.conicyt.cl/scielo.php?script=sci_pdf&pid={pid}",
            })

        token_elem = root.find(".//oai:resumptionToken", NS)
        if token_elem is not None and token_elem.text and token_elem.text.strip():
            url = f"{OAI_SCIELO}?verb=ListRecords&resumptionToken={token_elem.text.strip()}"
            print(f"  ✓ Lote {batch}: {len(records)} artículos procesados ({len(articulos)} acumulados)")
            batch += 1
            time.sleep(0.3)
        else:
            break

    with open(MANIFEST_SCIELO, "w", encoding="utf-8") as f:
        for a in articulos:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")

    print(f"[✓] Cosecha SciELO completada: {len(articulos)} artículos guardados en {MANIFEST_SCIELO}")
    return articulos


def resolver_y_descargar_pdf_scielo(articulo: Dict[str, Any]) -> Tuple[bool, str, Optional[pathlib.Path]]:
    """Resuelve la URL directa del PDF en SciELO CONICYT y lo guarda en disco."""
    pid = articulo.get("pid", "sin_pid")
    anio = articulo.get("anio") or "varios"
    subcarpeta = SCIELO_PDF_DIR / anio
    subcarpeta.mkdir(parents=True, exist_ok=True)
    slug = slugify(articulo.get("title", pid))
    destino = subcarpeta / f"{pid}_{slug}.pdf"

    if destino.exists() and destino.stat().st_size > 5120:
        return True, "ya_existe", destino

    url_sci = articulo.get("url_sci_pdf") or f"https://scielo.conicyt.cl/scielo.php?script=sci_pdf&pid={pid}"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

    try:
        req = urllib.request.Request(url_sci, headers=headers)
        with safe_urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        m = re.search(r'window\.location="([^"]+\.pdf)"', html)
        if not m:
            return False, f"No se encontró redirect PDF para {pid}", None

        pdf_url = m.group(1).replace("http://www.scielo.cl/", "https://scielo.conicyt.cl/")
        req2 = urllib.request.Request(pdf_url, headers=headers)
        with safe_urlopen(req2, timeout=25) as resp2:
            pdf_bytes = resp2.read()

        if len(pdf_bytes) > 2048:
            with open(destino, "wb") as f_out:
                f_out.write(pdf_bytes)
            return True, f"descargado ({len(pdf_bytes)} bytes)", destino

        return False, "PDF vacío", None
    except Exception as e:
        return False, str(e), None


def procesar_articulo_scielo(articulo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Descarga el PDF de SciELO y genera de inmediato su Markdown canónico."""
    pid = articulo.get("pid", "sin_pid")
    anio = articulo.get("anio") or "varios"
    slug = slugify(articulo.get("title", pid))

    out_file = OUTPUT_DIR / anio / f"{pid}_{slug}.md"
    if out_file.exists() and out_file.stat().st_size > 500:
        return {"status": "ya_existe", "pid": pid, "output_path": str(out_file)}

    ok, msg, pdf_path = resolver_y_descargar_pdf_scielo(articulo)
    if not ok or not pdf_path or not pdf_path.exists():
        return {"status": "error_descarga", "pid": pid, "error": msg}

    texto_raw = extraer_texto_pdf(pdf_path)
    if not texto_raw or len(texto_raw.strip()) < 100:
        # Si el PDF no extrajo suficiente texto pero tenemos el abstract oficial de SciELO
        if articulo.get("abstract") and len(articulo.get("abstract", "")) > 100:
            texto_raw = f"{articulo.get('abstract')}\n\n[Texto completo disponible en PDF: {articulo.get('url_scielo')}]"
        else:
            return {"status": "error_extraccion", "pid": pid}

    texto_limpio = limpiar_texto_articulo(texto_raw)
    area = inferir_area(articulo.get("title", ""), texto_limpio)
    instituciones, normas = extraer_instituciones_y_normas(texto_limpio)

    autores = articulo.get("authors", [])
    autores_str = ", ".join(autores) if autores else "Doctrina Nacional"
    primer_autor = autores[0] if autores else "Doctrina Nacional"
    titulo = articulo.get("title", "Artículo sin título").strip()
    volumen = articulo.get("volumen", "")
    url_orig = articulo.get("url_scielo", "")

    cita_canonica = (
        f"[RDPUCV - Núm. {volumen} ({anio}), {primer_autor}, {titulo[:45]}...]"
        if volumen and anio
        else f"[RDPUCV - {primer_autor}, {titulo[:45]}...]"
    )

    md_content = f"""---
id: "rdpucv_scielo_{pid}"
titulo: {json.dumps(titulo, ensure_ascii=False)}
autor: {json.dumps(autores_str, ensure_ascii=False)}
primer_autor: {json.dumps(primer_autor, ensure_ascii=False)}
revista: "Revista de Derecho de la Pontificia Universidad Católica de Valparaíso"
volumen: {json.dumps(str(volumen))}
anio: {anio or "null"}
fuente: {json.dumps(articulo.get('source', ''), ensure_ascii=False)}
area: {json.dumps(area)}
instituciones: {json.dumps(instituciones, ensure_ascii=False)}
normas_citadas: {json.dumps(normas, ensure_ascii=False)}
url_original: {json.dumps(url_orig)}
cita_canonica: {json.dumps(cita_canonica, ensure_ascii=False)}
---

# {titulo}

**Autor(es):** {autores_str}  
**Revista:** Revista de Derecho de la Pontificia Universidad Católica de Valparaíso (Pro Jure / SciELO)  
**Publicación:** Número {volumen} ({anio})  
**Área Dogmática:** {area.capitalize()}  
**Cita Canónica:** `{cita_canonica}`  
**Fuente Original:** [{url_orig}]({url_orig})

---

## 🏛️ Instituciones y Conceptos Jurídicos Relevantes
{', '.join(f'`{inst}`' for inst in instituciones) if instituciones else '_Análisis dogmático general_.'}

## ⚖️ Normas y Cuerpos Legales Citados
{chr(10).join(f'* {n}' for n in normas) if normas else '_Sin citas normativas directas identificadas en extracto_.'}

---

## Contenido del Artículo

{texto_limpio}
"""

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    return {
        "status": "convertido",
        "pid": pid,
        "titulo": titulo,
        "area": area,
        "output_path": str(out_file),
    }


def ejecutar_ingesta_scielo(hilos: int = 5) -> Dict[str, Any]:
    """Ejecuta la ingesta completa desde SciELO CONICYT."""
    articulos = cosechar_catalogo_scielo()
    print(f"[*] Procesando {len(articulos)} artículos de SciELO CONICYT con {hilos} hilos concurrentes...")

    convertidos = 0
    ya_existentes = 0
    fallidos = 0
    t0 = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=hilos) as executor:
        futuros = {executor.submit(procesar_articulo_scielo, art): art for art in articulos}
        for i, fut in enumerate(concurrent.futures.as_completed(futuros), start=1):
            try:
                res = fut.result()
                if res and res.get("status") == "convertido":
                    convertidos += 1
                elif res and res.get("status") == "ya_existe":
                    ya_existentes += 1
                else:
                    fallidos += 1

                if i % 25 == 0 or i == len(articulos):
                    dur = round(time.perf_counter() - t0, 1)
                    print(f"  → Progreso SciELO: {i}/{len(articulos)} ({convertidos} nuevos, {ya_existentes} cacheados, {fallidos} fallos) | {dur}s")
            except Exception as e:
                fallidos += 1
                print(f"  [!] Excepción: {e}")

    duracion = round(time.perf_counter() - t0, 2)
    print("\n" + "=" * 60)
    print("RESUMEN INGESTA SCIELO CONICYT:")
    print(f"  Total procesados: {len(articulos)}")
    print(f"  Nuevos convertidos: {convertidos}")
    print(f"  Preexistentes: {ya_existentes}")
    print(f"  Fallidos: {fallidos}")
    print(f"  Tiempo: {duracion} s")
    print("=" * 60)

    return {
        "convertidos": convertidos,
        "ya_existentes": ya_existentes,
        "fallidos": fallidos,
        "duracion": duracion,
    }


if __name__ == "__main__":
    ejecutar_ingesta_scielo()
