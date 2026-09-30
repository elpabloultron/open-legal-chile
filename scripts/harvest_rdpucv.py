#!/usr/bin/env python3
"""
harvest_rdpucv.py — Cosechador OAI-PMH para la Revista de Derecho PUCV (Pro Jure).
Extrae los metadatos completos (título, autor, volumen, año, URLs de descarga)
de todos los artículos publicados en https://www.projurepucv.cl/index.php/rderecho/oai.
"""

import json
import os
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request
import defusedxml.ElementTree as ET
from typing import Any, Dict, List, Optional

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))
from config import safe_urlopen

OAI_ENDPOINT = "https://www.projurepucv.cl/index.php/rderecho/oai"
DATA_DIR = ROOT_DIR / "data" / "rdpucv"
MANIFEST_PATH = DATA_DIR / "catalogo_articulos.jsonl"

NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
}


def slugify(texto: str, max_len: int = 60) -> str:
    """Genera un slug limpio y legible a partir de un texto."""
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


def parsear_registro(rec_elem: ET.Element) -> Optional[Dict[str, Any]]:
    """Extrae la información estructurada de un elemento <record> de OAI-PMH."""
    header = rec_elem.find("oai:header", NS)
    if header is None:
        return None

    status = header.attrib.get("status")
    if status == "deleted":
        return None

    ident_elem = header.find("oai:identifier", NS)
    raw_ident = ident_elem.text.strip() if ident_elem is not None and ident_elem.text else ""
    article_id_match = re.search(r"article/(\d+)$", raw_ident)
    article_id = article_id_match.group(1) if article_id_match else raw_ident

    datestamp_elem = header.find("oai:datestamp", NS)
    datestamp = datestamp_elem.text.strip() if datestamp_elem is not None and datestamp_elem.text else ""

    metadata = rec_elem.find("oai:metadata", NS)
    if metadata is None:
        return None

    dc = metadata.find("oai_dc:dc", NS)
    if dc is None:
        return None

    # Título (priorizar español)
    titles = [t.text.strip() for t in dc.findall("dc:title", NS) if t.text]
    title = titles[0] if titles else "Sin Título"

    # Autores / Creadores
    creators = [c.text.strip() for c in dc.findall("dc:creator", NS) if c.text]

    # Fuente / Volumen / Número
    sources = [s.text.strip() for s in dc.findall("dc:source", NS) if s.text]
    volumen_str = ""
    anio_str = ""
    for s in sources:
        m = re.search(r"(?:Vol\.|Volumen|Núm\.|No\.)\s*(\d+)", s, re.IGNORECASE)
        if m and not volumen_str:
            volumen_str = m.group(1)
        my = re.search(r"\b(19\d{2}|20\d{2})\b", s)
        if my and not anio_str:
            anio_str = my.group(1)

    # Fecha de publicación
    dates = [d.text.strip() for d in dc.findall("dc:date", NS) if d.text]
    date_pub = dates[0] if dates else datestamp
    if not anio_str and date_pub:
        my = re.search(r"\b(19\d{2}|20\d{2})\b", date_pub)
        if my:
            anio_str = my.group(1)

    # URLs
    identifiers = [i.text.strip() for i in dc.findall("dc:identifier", NS) if i.text]
    relations = [r.text.strip() for r in dc.findall("dc:relation", NS) if r.text]

    view_url = identifiers[0] if identifiers else ""
    galley_url = ""
    for r in relations:
        if "/article/view/" in r and r != view_url:
            galley_url = r
            break

    download_url = ""
    if galley_url:
        # e.g. https://www.projurepucv.cl/index.php/rderecho/article/view/1/1 -> download/1/1
        download_url = re.sub(r"/article/view/(\d+)/(\d+)", r"/article/download/\1/\2", galley_url)
    elif view_url and article_id:
        download_url = f"https://www.projurepucv.cl/index.php/rderecho/article/download/{article_id}/{article_id}"

    # Materias / Secciones
    subjects = [sub.text.strip() for sub in dc.findall("dc:subject", NS) if sub.text]

    return {
        "article_id": article_id,
        "raw_oai_id": raw_ident,
        "title": title,
        "authors": creators,
        "volumen": volumen_str,
        "anio": anio_str,
        "fecha": date_pub,
        "fuente": sources[0] if sources else "",
        "subjects": subjects,
        "view_url": view_url,
        "galley_url": galley_url,
        "download_url": download_url,
    }


def cosechar_catalogo_completo(max_reintentos: int = 5) -> List[Dict[str, Any]]:
    """Descarga todos los registros de OAI-PMH manejando resumptionToken."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    articulos = []
    resumption_token: Optional[str] = None
    batch_num = 1
    total_esperado: Optional[int] = None

    headers = {"User-Agent": "OpenLegalChile-Ingestor/1.0 (https://github.com/elpabloultron/open-legal-chile)"}

    print("[*] Iniciando cosecha OAI-PMH de Revista de Derecho PUCV (Pro Jure)...")

    while True:
        if resumption_token:
            url = f"{OAI_ENDPOINT}?verb=ListRecords&resumptionToken={urllib.parse.quote(resumption_token)}"
        else:
            url = f"{OAI_ENDPOINT}?verb=ListRecords&metadataPrefix=oai_dc"

        exito = False
        for intento in range(1, max_reintentos + 1):
            try:
                req = urllib.request.Request(url, headers=headers)
                with safe_urlopen(req, timeout=30) as resp:
                    raw_xml = resp.read()
                tree = ET.fromstring(raw_xml)  # nosec B314
                exito = True
                break
            except Exception as e:
                print(f"  [!] Reintento {intento}/{max_reintentos} en lote {batch_num}: {e}")
                time.sleep(2 * intento)

        if not exito:
            print(f"[X] Falló definitivamente la obtención del lote {batch_num}.")
            break

        records = tree.findall(".//oai:record", NS)
        for r in records:
            item = parsear_registro(r)
            if item:
                articulos.append(item)

        token_elem = tree.find(".//oai:resumptionToken", NS)
        if token_elem is not None and token_elem.text and token_elem.text.strip():
            resumption_token = token_elem.text.strip()
            if total_esperado is None:
                size_str = token_elem.attrib.get("completeListSize")
                if size_str and size_str.isdigit():
                    total_esperado = int(size_str)
            print(f"  ✓ Lote {batch_num}: {len(records)} artículos procesados ({len(articulos)}/{total_esperado or '?'})")
            batch_num += 1
            time.sleep(0.5)  # Respeto al servidor universitario
        else:
            print(f"  ✓ Último lote ({batch_num}): {len(records)} artículos procesados.")
            break

    # Guardar en JSONL
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        for a in articulos:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")

    print(f"[✓] Cosecha finalizada. {len(articulos)} artículos guardados en {MANIFEST_PATH}")
    return articulos


if __name__ == "__main__":
    cosechar_catalogo_completo()
