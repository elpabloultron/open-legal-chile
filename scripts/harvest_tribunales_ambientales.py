#!/usr/bin/env python3
"""
Open Legal Chile — Cosechador e Ingestor de Jurisprudencia de los Tribunales Ambientales (1TA, 2TA y 3TA)
Especial foco académico: Tercer Tribunal Ambiental de Valdivia (jurisdicción Los Lagos).
Descarga anuarios, boletines y sentencias oficiales, normaliza en Markdown canónico RAE/ASALE
y prepara el dataset estructurado para Hugging Face (pablobenavidesj/doctrina-jurisprudencia-chile).
"""

import os
import sys
import json
import re
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "ambiental")
DOC_DIR = os.path.join(BASE_DIR, "doctrina", "ambiental")
OUTPUT_JSONL = os.path.join(BASE_DIR, "data", "jurisprudencia", "ambiental_sentencias.jsonl")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DOC_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_JSONL), exist_ok=True)

HEADERS = {
    "User-Agent": "OpenLegalChile/1.6.5 (Universidad de Los Lagos; Investigacion Ambiental Soberana)"
}

def harvest_3ta_anuarios() -> List[Dict[str, Any]]:
    """Descarga e indexa los Anuarios del Tercer Tribunal Ambiental de Valdivia."""
    url = "https://3ta.cl/publicaciones/anuario-de-jurisprudencia-ambiental/"
    results = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            for a in soup.find_all("a", href=True):
                href = str(a.get("href", ""))
                if ".pdf" in href.lower() and "anuario" in href.lower():
                    # Extraer año del nombre
                    m = re.search(r"20\d\d", href)
                    anio = m.group(0) if m else "Reciente"
                    nom_archivo = os.path.basename(href.split("?")[0])
                    results.append({
                        "tribunal": "3TA",
                        "tribunal_nombre": "Tercer Tribunal Ambiental de Valdivia",
                        "jurisdiccion": "Ñuble, Biobío, La Araucanía, Los Ríos, Los Lagos, Aysén y Magallanes",
                        "tipo": "Anuario de Jurisprudencia Ambiental",
                        "anio": anio,
                        "titulo": f"Anuario de Jurisprudencia Ambiental {anio} — 3TA Valdivia",
                        "url_pdf": href,
                        "archivo_local": nom_archivo,
                        "materia": "Jurisprudencia ambiental del sur: humedales urbanos, acuicultura, bordes costeros y áreas protegidas"
                    })
    except Exception as e:
        print(f"[!] Error cosechando Anuarios 3TA: {e}", file=sys.stderr)
    return results

def harvest_3ta_boletines(limit: int = 15) -> List[Dict[str, Any]]:
    """Obtiene los enlaces y fichas de los Boletines de Jurisprudencia del 3TA."""
    url = "https://3ta.cl/publicaciones/boletin-jurisprudencia-ambiental/"
    results = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            post_links: List[tuple] = []
            for a in soup.find_all("a", href=True):
                t = a.get_text(strip=True)
                h = str(a.get("href", ""))
                if "boletin-n" in h.lower() and h not in [pl[1] for pl in post_links]:
                    post_links.append((t, h))

            for titulo, post_url in post_links[:limit]:
                try:
                    r_p = requests.get(post_url, headers=HEADERS, timeout=8)
                    if r_p.status_code == 200:
                        s_p = BeautifulSoup(r_p.content, "html.parser")
                        pdf_url = ""
                        for pa in s_p.find_all("a", href=True):
                            pa_href = str(pa.get("href", ""))
                            if ".pdf" in pa_href.lower():
                                pdf_url = pa_href
                                break
                        
                        m = re.search(r"N°?\s*(\d+)", titulo, re.IGNORECASE)
                        num = m.group(1) if m else "S/N"
                        results.append({
                            "tribunal": "3TA",
                            "tribunal_nombre": "Tercer Tribunal Ambiental de Valdivia",
                            "jurisdiccion": "Ñuble, Biobío, La Araucanía, Los Ríos, Los Lagos, Aysén y Magallanes",
                            "tipo": "Boletín de Jurisprudencia Ambiental",
                            "numero": num,
                            "titulo": f"Boletín N° {num} de Jurisprudencia Ambiental — 3TA",
                            "url_post": post_url,
                            "url_pdf": pdf_url if pdf_url else post_url,
                            "materia": "Doctrina y resoluciones del Tercer Tribunal Ambiental"
                        })
                except Exception:
                    pass
    except Exception as e:
        print(f"[!] Error cosechando Boletines 3TA: {e}", file=sys.stderr)
    return results

def harvest_2ta_anuarios() -> List[Dict[str, Any]]:
    """Obtiene los Anuarios del Segundo Tribunal Ambiental de Santiago."""
    url = "https://tribunalambiental.cl/informacion-institucional/sobre-el-tribunal-ambiental/anuario/"
    results = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            vistos = set()
            for a in soup.find_all("a", href=True):
                href = str(a.get("href", ""))
                if ".pdf" in href.lower() and "anuario" in href.lower() and href not in vistos:
                    vistos.add(href)
                    m = re.search(r"20\d\d", href)
                    anio = m.group(0) if m else "Reciente"
                    full_url = href if href.startswith("http") else f"https://tribunalambiental.cl{href}"
                    results.append({
                        "tribunal": "2TA",
                        "tribunal_nombre": "Segundo Tribunal Ambiental de Santiago",
                        "jurisdiccion": "Valparaíso, Metropolitana, O'Higgins y Maule",
                        "tipo": "Anuario de Jurisprudencia Ambiental",
                        "anio": anio,
                        "titulo": f"Anuario de Jurisprudencia Ambiental {anio} — 2TA Santiago",
                        "url_pdf": full_url,
                        "materia": "Sanciones SMA, reclamaciones de RCA, humedales urbanos y daño ambiental en la zona central"
                    })
    except Exception as e:
        print(f"[!] Error cosechando Anuarios 2TA: {e}", file=sys.stderr)
    return results

def harvest_1ta_sentencias(limit: int = 25) -> List[Dict[str, Any]]:
    """Obtiene las sentencias del Primer Tribunal Ambiental de Antofagasta vía su API REST oficial."""
    url = "https://www.portaljudicial1ta.cl/sgc-ws/rest/sentencia/search?year=2025&month=0"
    results = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            docs_raw = data.get("response", [])
            docs = json.loads(docs_raw) if isinstance(docs_raw, str) else docs_raw

            for d in docs[:limit]:
                rol = d.get("rol", "")
                caratula = d.get("caratula", "")
                f_sentencia = d.get("fechaSentencia", "")
                redactor = d.get("redactor", "")
                cod_doc = d.get("codDocumento", "")
                link_pdf = f"https://www.portaljudicial1ta.cl/sgc-ws/rest/servlet/download-file?file={cod_doc}" if cod_doc else "https://www.portaljudicial1ta.cl/sgc-web/sentencias.html"

                results.append({
                    "tribunal": "1TA",
                    "tribunal_nombre": "Primer Tribunal Ambiental de Antofagasta",
                    "jurisdiccion": "Arica y Parinacota, Tarapacá, Antofagasta, Atacama y Coquimbo",
                    "tipo": "Sentencia Definitiva SGC",
                    "rol": rol,
                    "caratula": caratula,
                    "fecha": f_sentencia,
                    "redactor": redactor,
                    "titulo": f"Causa {rol} — {caratula}",
                    "url_pdf": link_pdf,
                    "materia": "Minería, recursos hídricos, salares y comunidades indígenas del norte"
                })
    except Exception as e:
        print(f"[!] Error cosechando Sentencias 1TA: {e}", file=sys.stderr)
    return results

def generar_fichas_markdown(documentos: List[Dict[str, Any]]):
    """Crea fichas canónicas de doctrina ambiental en Markdown RAE/ASALE."""
    resumen_path = os.path.join(DOC_DIR, "COMPENDIO_JURISPRUDENCIA_AMBIENTAL.md")
    
    with open(resumen_path, "w", encoding="utf-8") as f:
        f.write("# Compendio Oficial de Jurisprudencia Ambiental de Chile\n\n")
        f.write("## Judicatura Ambiental Especializada (Ley N° 20.600)\n\n")
        f.write("Corpus sistematizado para la **Universidad de Los Lagos** y el foro nacional. Comprende resoluciones, boletines doctrinales y anuarios oficiales del **Primer Tribunal Ambiental (Antofagasta)**, **Segundo Tribunal Ambiental (Santiago)** y **Tercer Tribunal Ambiental (Valdivia)**.\n\n")
        f.write("---\n\n")

        for d in documentos:
            titulo = d.get("titulo", "")
            materia = d.get("materia", "")
            enlace = d.get("url_pdf", "")
            f.write(f"### {titulo}\n")
            f.write(f"- **Tribunal:** {d.get('tribunal_nombre')}\n")
            f.write(f"- **Jurisdicción:** {d.get('jurisdiccion')}\n")
            f.write(f"- **Tipo de publicación:** {d.get('tipo')}\n")
            if d.get("rol"):
                f.write(f"- **Rol:** `{d.get('rol')}` | **Fecha:** {d.get('fecha', 'N/D')}\n")
            if d.get("redactor"):
                f.write(f"- **Ministro Redactor:** {d.get('redactor')}\n")
            f.write(f"- **Materia analizada:** {materia}\n")
            f.write(f"- **Documento oficial:** [{titulo}]({enlace})\n\n")

    print(f"[✓] Compendio Markdown generado en: {resumen_path}")

def main():
    print("=== Open Legal Chile · Harvest Tribunales Ambientales (1TA, 2TA, 3TA) ===")
    todos = []

    print("[*] 1. Cosechando Anuarios del 3TA de Valdivia (Los Lagos)...")
    anuarios_3ta = harvest_3ta_anuarios()
    todos.extend(anuarios_3ta)
    print(f"    -> {len(anuarios_3ta)} anuarios encontrados.")

    print("[*] 2. Cosechando Boletines Temáticos del 3TA...")
    boletines_3ta = harvest_3ta_boletines(limit=15)
    todos.extend(boletines_3ta)
    print(f"    -> {len(boletines_3ta)} boletines procesados.")

    print("[*] 3. Cosechando Anuarios del 2TA de Santiago...")
    anuarios_2ta = harvest_2ta_anuarios()
    todos.extend(anuarios_2ta)
    print(f"    -> {len(anuarios_2ta)} anuarios encontrados.")

    print("[*] 4. Cosechando Sentencias Definitivas del 1TA de Antofagasta...")
    sentencias_1ta = harvest_1ta_sentencias(limit=25)
    todos.extend(sentencias_1ta)
    print(f"    -> {len(sentencias_1ta)} sentencias encontradas.")

    print(f"\n[*] Total de documentos ambientales consolidados: {len(todos)}")

    # Exportar JSONL
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for it in todos:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(f"[✓] Archivo JSONL listo para Hugging Face: {OUTPUT_JSONL}")

    # Generar Markdown
    generar_fichas_markdown(todos)

if __name__ == "__main__":
    main()
