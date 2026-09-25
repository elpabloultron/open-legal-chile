#!/usr/bin/env python3
"""
Cosechador Exhaustivo de Jurisprudencia de los Tribunales Ambientales de Chile
(1.er TA Antofagasta, 2.º TA Santiago y 3.er TA Valdivia)

Extrae el universo histórico completo de sentencias definitivas y resoluciones:
- 1TA: API REST oficial (2018-2026) -> ~110 sentencias
- 2TA: Tabla histórica oficial de sentencias -> ~444 sentencias
- 3TA: Secciones oficiales de Reclamaciones, Demandas, Solicitudes SMA y Consultas -> ~338 causas

Total consolidado: ~892 sentencias con roles, carátulas, fechas, materias,
sentido del fallo, ministros redactores y enlaces oficiales a sentencias en PDF y expedientes electrónicos.
"""

import os
import sys
import json
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "jurisprudencia")
OUT_JSONL = os.path.join(DATA_DIR, "ambiental_sentencias.jsonl")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8"
}

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def harvest_1ta() -> list:
    print("[1TA] Cosechando Primer Tribunal Ambiental (Antofagasta)...")
    sentencias_1ta = []
    base_url = "https://www.portaljudicial1ta.cl/sgc-ws/rest/sentencia/search"
    
    for year in range(2018, 2027):
        url = f"{base_url}?year={year}&month=0"
        try:
            resp = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=12)
            if resp.status_code != 200:
                continue
            data = resp.json()
            raw_items = data.get("response")
            if not raw_items:
                continue
            items = json.loads(raw_items) if isinstance(raw_items, str) else raw_items
            for it in items:
                rol = clean_text(it.get("rol", ""))
                caratula = clean_text(it.get("caratula", ""))
                cod_doc = it.get("codDocumento", "")
                fecha = clean_text(it.get("fechaSentencia", ""))
                redactor = clean_text(it.get("redactor", ""))
                integracion = clean_text(it.get("integracion", ""))
                
                # URL de descarga de sentencia si existe codDocumento
                pdf_url = f"https://www.portaljudicial1ta.cl/sgc-ws/rest/sentencia/download?codDocumento={cod_doc}" if cod_doc else "https://1ta.cl"
                
                sentencias_1ta.append({
                    "tribunal": "1TA",
                    "tribunal_nombre": "Primer Tribunal Ambiental de Antofagasta",
                    "jurisdiccion": "Arica y Parinacota, Tarapacá, Antofagasta, Atacama y Coquimbo",
                    "rol": rol,
                    "tipo": "Reclamación" if rol.startswith("R") else ("Demanda Daño Ambiental" if rol.startswith("D") else "Causa Ambiental"),
                    "caratula": caratula,
                    "fecha": fecha,
                    "redactor": redactor,
                    "integracion": integracion,
                    "materia": "Contencioso Ambiental / SMA / SEA" if rol.startswith("R") else "Reparación Daño Ambiental",
                    "resuelve": "Sentencia Definitiva",
                    "url_pdf": pdf_url,
                    "url_expediente": f"https://www.portaljudicial1ta.cl/sgc-web/causa.html?rol={urllib.parse.quote(rol)}"
                })
        except Exception as e:
            print(f"[1TA] Error en año {year}: {e}")
            
    print(f"[1TA] Cosechadas {len(sentencias_1ta)} sentencias.")
    return sentencias_1ta

def harvest_2ta() -> list:
    print("[2TA] Cosechando Segundo Tribunal Ambiental (Santiago)...")
    sentencias_2ta = []
    url = "https://tribunalambiental.cl/sentencias/"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            rows = soup.find_all("tr")
            
            for tr in rows:
                tds = tr.find_all("td")
                if len(tds) < 2:
                    continue
                rol = clean_text(tds[0].get_text())
                desc = clean_text(tds[1].get_text())
                if not rol or "Rol" in rol:
                    continue
                
                # Extraer enlaces
                links = tr.find_all("a", href=True)
                pdf_url = "https://tribunalambiental.cl"
                expediente_url = "https://causas.tribunalambiental.cl"
                for a in links:
                    h = str(a.get("href", ""))
                    if ".pdf" in h.lower():
                        pdf_url = h
                    elif "causas.tribunalambiental.cl" in h:
                        expediente_url = h
                
                # Parsear campos de la descripción
                # Ej: Geo Pub S.A. en contra de la Superintendencia del Medio Ambiente... Región:... Fecha del fallo:... Resuelve:...
                region_match = re.search(r"Región:\s*([^.]+?)(?:\.|$)", desc, re.I)
                fecha_match = re.search(r"Fecha del fallo:\s*([^.]+?)(?:\.|$)", desc, re.I)
                resuelve_match = re.search(r"Resuelve:\s*([^.]+?)(?:\.|$)", desc, re.I)
                
                region = clean_text(region_match.group(1)) if region_match else "Región Metropolitana / Centro"
                fecha = clean_text(fecha_match.group(1)) if fecha_match else ""
                resuelve = clean_text(resuelve_match.group(1)) if resuelve_match else "Sentencia Definitiva"
                
                # Extraer carátula (primera oración antes de Relacionado con o antes de punto)
                caratula_part = desc
                if "Relacionado con:" in caratula_part:
                    caratula_part = caratula_part.split("Relacionado con:")[0]
                elif "Región:" in caratula_part:
                    caratula_part = caratula_part.split("Región:")[0]
                caratula = clean_text(caratula_part)[:180]
                
                sentencias_2ta.append({
                    "tribunal": "2TA",
                    "tribunal_nombre": "Segundo Tribunal Ambiental de Santiago",
                    "jurisdiccion": "Valparaíso, Metropolitana de Santiago, O'Higgins y Maule",
                    "rol": rol,
                    "tipo": "Reclamación" if rol.startswith("R") else ("Demanda Daño Ambiental" if rol.startswith("D") else "Causa Ambiental"),
                    "caratula": caratula,
                    "descripcion_detallada": desc,
                    "region": region,
                    "fecha": fecha,
                    "resuelve": resuelve,
                    "materia": "Contencioso Administrativo Ambiental / Sancionatorio SMA / SEA",
                    "url_pdf": pdf_url,
                    "url_expediente": expediente_url
                })
    except Exception as e:
        print(f"[2TA] Error cosechando 2TA: {e}")
        
    print(f"[2TA] Cosechadas {len(sentencias_2ta)} sentencias.")
    return sentencias_2ta

def harvest_3ta() -> list:
    print("[3TA] Cosechando Tercer Tribunal Ambiental (Valdivia / Macrozona Sur)...")
    sentencias_3ta = []
    
    secciones = [
        ("Reclamaciones", "https://3ta.cl/sentencias/", "17 N°1 / 17 N°3 (Reclamación Administrativa)"),
        ("Demandas Daño", "https://3ta.cl/sentencias/demandas/", "17 N°2 (Demanda por Daño Ambiental)"),
        ("Solicitudes SMA", "https://3ta.cl/sentencias/solicitudes/", "17 N°4 (Medidas Cautelares y Provisionales SMA)"),
        ("Consultas", "https://3ta.cl/sentencias/consultas/", "Consultas de Sanciones Graves SMA")
    ]
    
    for nombre_sec, url, materia_default in secciones:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            rows = soup.find_all("tr")
            for tr in rows:
                tds = tr.find_all("td")
                if len(tds) < 3:
                    continue
                
                # tds[1]: Rol, tds[2]: Carátula / Sentencia
                rol_raw = clean_text(tds[1].get_text())
                caratula_raw = clean_text(tds[2].get_text())
                
                # Extraer rol limpio
                rol_match = re.search(r"([RDS]-\d+-\d{4}|C-\d+-\d{4})", rol_raw)
                rol = rol_match.group(1) if rol_match else rol_raw.replace("Expediente electrónico", "").strip()
                if not rol or "Rol" in rol:
                    continue
                    
                fecha = clean_text(tds[3].get_text()) if len(tds) > 3 else ""
                redactor = clean_text(tds[4].get_text()) if len(tds) > 4 else ""
                materia = clean_text(tds[5].get_text()) if len(tds) > 5 else materia_default
                
                # Limpiar carátula
                caratula = caratula_raw
                caratula = re.sub(r"Sentencia [RDS]-\d+-\d{4}", "", caratula)
                caratula = re.sub(r"Video Audiencia.*", "", caratula)
                caratula = re.sub(r"Resolución [RDS]-\d+-\d{4}", "", caratula)
                caratula = clean_text(caratula)
                
                # Enlaces
                pdf_url = "https://3ta.cl"
                expediente_url = "https://causas.3ta.cl"
                for a in tr.find_all("a", href=True):
                    h = str(a.get("href", ""))
                    if ".pdf" in h.lower():
                        pdf_url = h
                    elif "causas.3ta.cl" in h:
                        expediente_url = h
                        
                sentencias_3ta.append({
                    "tribunal": "3TA",
                    "tribunal_nombre": "Tercer Tribunal Ambiental de Valdivia",
                    "jurisdiccion": "Ñuble, Biobío, La Araucanía, Los Ríos, Los Lagos, Aysén y Magallanes",
                    "rol": rol,
                    "tipo": "Reclamación (Art. 17 N° 1/3)" if rol.startswith("R") else (
                        "Demanda Daño Ambiental (Art. 17 N° 2)" if rol.startswith("D") else (
                            "Medida Cautelar / Provisional SMA (Art. 17 N° 4)" if rol.startswith("S") else "Consulta SMA"
                        )
                    ),
                    "caratula": caratula,
                    "fecha": fecha,
                    "redactor": redactor,
                    "materia": materia or materia_default,
                    "resuelve": "Sentencia Definitiva / Resolución",
                    "url_pdf": pdf_url,
                    "url_expediente": expediente_url
                })
        except Exception as e:
            print(f"[3TA] Error cosechando {nombre_sec}: {e}")
            
    print(f"[3TA] Cosechadas {len(sentencias_3ta)} sentencias.")
    return sentencias_3ta

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    total_sentencias = []
    
    # 1. 1TA
    s1 = harvest_1ta()
    total_sentencias.extend(s1)
    
    # 2. 2TA
    s2 = harvest_2ta()
    total_sentencias.extend(s2)
    
    # 3. 3TA
    s3 = harvest_3ta()
    total_sentencias.extend(s3)
    
    # Guardar en JSONL
    print(f"\n[TOTAL] Consolidando {len(total_sentencias)} sentencias en {OUT_JSONL}...")
    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for s in total_sentencias:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
            
    print(f"✓ Éxito: {len(total_sentencias)} sentencias de los Tribunales Ambientales guardadas en {OUT_JSONL}")

if __name__ == "__main__":
    main()
