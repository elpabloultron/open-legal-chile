#!/usr/bin/env python3
"""
Open Legal Chile — Extractor y Sincronizador Oficial de Jurisprudencia del Tribunal Constitucional (TC)
Consulta directamente la API oficial REST de https://buscador.tcchile.cl
e indexa las sentencias de Inaplicabilidad (INA) e Inconstitucionalidad (INC)
en la base de datos local SQLite (jurisprudencia_judicial.db) y exporta a JSONL para Hugging Face.
"""

import os
import sys
import json
import sqlite3
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional

# Rutas del repositorio
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "jurisprudencia_judicial.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "jurisprudencia")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TC_API_URL = "https://buscador-backend.tcchile.cl/api/buscadorexterno/ficha"

SEARCH_TERMS = [
    "tutela laboral",
    "despido",
    "confianza legitima",
    "ley karin",
    "salud isapres",
    "medio ambiente",
    "debido proceso",
    "prescripcion",
    "derecho de propiedad",
    "igualdad ante la ley"
]

def fetch_tc_sentencias(search_term: str, limit: int = 15) -> List[Dict[str, Any]]:
    """Consulta la API oficial del Tribunal Constitucional de Chile."""
    filter_data = {
        "search": search_term,
        "palabra_clave": None,
        "rol": None,
        "fecha_sentencia": None,
        "tipo_accion": None,
        "resultado": None,
        "competencia": None,
        "articulo_constitucion": None,
        "ministro": None,
        "cuerpo_legal": None
    }

    params = urllib.parse.urlencode({"filter": json.dumps(filter_data)})
    url = f"{TC_API_URL}?{params}"
    headers = {
        "User-Agent": "OpenLegalChile/1.6.5 (Investigacion Juridica Soberana; Universidad de Los Lagos)",
        "Accept": "application/json"
    }

    req = urllib.request.Request(url, headers=headers)
    results = []

    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("data", [])
            for it in items[:limit]:
                folio = it.get("folio", "")
                codigo = it.get("codigo", "INA")
                rol_str = f"Rol N° {folio}-{codigo}" if folio else "Rol S/N"
                fecha = (it.get("fecha_sentencia") or "")[:10]
                
                # Extraer parametros del detalle
                detalles = it.get("detalle", [])
                gestion_pendiente = ""
                precepto = ""
                resultado = ""
                for d in detalles:
                    param_nom = d.get("parametro", {}).get("nombre", "")
                    val = d.get("valor", "")
                    if "gestión" in param_nom.lower() or "gestion" in param_nom.lower():
                        gestion_pendiente = val
                    elif "precepto" in param_nom.lower() or "norma" in param_nom.lower() or "ley" in param_nom.lower():
                        precepto = val
                    elif "resultado" in param_nom.lower() or "pronunciamiento" in param_nom.lower():
                        resultado = val

                template_name = it.get("template", {}).get("complete_name", "Inaplicabilidad de Precepto Legal")
                doc_id = it.get("id")
                pdf_link = f"https://buscador-backend.tcchile.cl/api/extended/{doc_id}/download" if doc_id else "https://buscador.tcchile.cl"

                doctrina = f"{template_name}. Conflicto: {search_term}. "
                if resultado:
                    doctrina += f"Resultado: {resultado}. "
                if gestion_pendiente:
                    doctrina += f"Gestión pendiente: {gestion_pendiente}"

                results.append({
                    "tribunal": "Tribunal Constitucional",
                    "sala": "Pleno",
                    "rol": rol_str,
                    "fecha": fecha,
                    "caratula": gestion_pendiente[:180] if gestion_pendiente else f"Requerimiento sobre {search_term}",
                    "materia": f"Constitucional / {search_term.title()}",
                    "doctrina": doctrina.strip(),
                    "normas": precepto if precepto else "CPR Art. 19 y Art. 93 N° 6",
                    "link": pdf_link
                })
    except Exception as e:
        print(f"[!] Error consultando '{search_term}' en TC API: {e}", file=sys.stderr)

    return results

def sync_to_db_and_jsonl(sentencias: List[Dict[str, Any]]):
    """Inserta las sentencias en SQLite y las vuelca a un archivo JSONL."""
    if not sentencias:
        print("[-] No se encontraron sentencias nuevas.")
        return

    # 1. SQLite
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sentencias_judiciales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tribunal TEXT,
            sala TEXT,
            rol TEXT UNIQUE,
            fecha TEXT,
            caratula TEXT,
            materia TEXT,
            doctrina TEXT,
            normas TEXT,
            link TEXT
        )
    """)

    insertados = 0
    for s in sentencias:
        try:
            cur.execute("""
                INSERT OR REPLACE INTO sentencias_judiciales (
                    tribunal, sala, rol, fecha, caratula, materia, doctrina, normas, link
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                s["tribunal"], s["sala"], s["rol"], s["fecha"],
                s["caratula"], s["materia"], s["doctrina"], s["normas"], s["link"]
            ))
            insertados += 1
        except Exception as e:
            print(f"[!] Error insertando {s.get('rol')}: {e}", file=sys.stderr)

    conn.commit()
    conn.close()

    # 2. JSONL para Hugging Face
    jsonl_path = os.path.join(OUTPUT_DIR, "tc_sentencias.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for s in sentencias:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"[✓] Sincronización exitosa: {insertados} sentencias del TC procesadas.")
    print(f"[✓] Guardadas en: {DB_PATH}")
    print(f"[✓] Exportadas a JSONL para Hugging Face: {jsonl_path}")

def main():
    print("=== Open Legal Chile · Harvest Tribunal Constitucional ===")
    all_sentencias = {}
    for term in SEARCH_TERMS:
        print(f"[*] Consultando '{term}'...")
        res = fetch_tc_sentencias(term, limit=10)
        for s in res:
            all_sentencias[s["rol"]] = s

    lista_final = list(all_sentencias.values())
    print(f"[*] Total de sentencias únicas del TC obtenidas: {len(lista_final)}")
    sync_to_db_and_jsonl(lista_final)

if __name__ == "__main__":
    main()
