"""
Open Legal Chile — Conector Oficial Tribunal de Defensa de la Libre Competencia (TDLC)
Módulo para consultar, indexar y buscar Sentencias, Dictámenes, Instrucciones de Carácter General (ICG)
y Resoluciones en materia de Libre Competencia, Abuso de Posición Dominante y Colusión en Chile (DL 211).
"""

import os
import sys
import re
import html
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional

BASE_URL = "https://www.tdlc.cl/wp-json/wp/v2"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "tdlc_cache")


class TDLCClient:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def get_sentencias(self, page: int = 1, per_page: int = 10, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Obtiene el listado oficial de Sentencias del TDLC."""
        cache_key = f"sentencias_p{page}_s{per_page}"
        cache_file = self._get_cache_path(cache_key)

        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        url = f"{BASE_URL}/tdlc-sentencias?page={page}&per_page={per_page}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "OpenLegalChile/1.0 (Libre Competencia Chile)",
                "Accept": "application/json"
            }
        )

        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))

            clean_results = []
            for item in data:
                raw_title = item.get("title", {}).get("rendered", "")
                clean_title = html.unescape(re.sub(r'<[^>]+>', '', raw_title).strip())
                clean_results.append({
                    "id": item.get("id"),
                    "titulo": clean_title,
                    "fecha": item.get("date", "")[:10],
                    "link": item.get("link", "")
                })

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(clean_results, f, ensure_ascii=False, indent=2)

            return clean_results

    def get_dictamenes(self, page: int = 1, per_page: int = 10, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Obtiene el listado oficial de Dictámenes no contenciosos del TDLC."""
        url = f"{BASE_URL}/dictamenes?page={page}&per_page={per_page}"
        req = urllib.request.Request(url, headers={"User-Agent": "OpenLegalChile/1.0", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                return [{
                    "id": item.get("id"),
                    "titulo": html.unescape(re.sub(r'<[^>]+>', '', item.get("title", {}).get("rendered", "")).strip()),
                    "fecha": item.get("date", "")[:10],
                    "link": item.get("link", "")
                } for item in data]
        except Exception:
            return []

    def search_jurisprudencia(self, query: str, max_pages: int = 3) -> List[Dict[str, Any]]:
        """Busca en sentencias y dictámenes del TDLC por término o empresa involucrada."""
        q_lower = query.lower().strip()
        matches = []

        for p in range(1, max_pages + 1):
            sentencias = self.get_sentencias(page=p, per_page=20)
            for s in sentencias:
                if q_lower in s.get("titulo", "").lower():
                    matches.append(s)
            if len(sentencias) < 20:
                break

        return matches


# ==============================================================================
# CLI DE CONSULTA RÁPIDA DE LIBRE COMPETENCIA (TDLC)
# ==============================================================================
if __name__ == "__main__":
    import argparse
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Conector Open Legal Chile — Tribunal de Defensa de la Libre Competencia (TDLC)")
    parser.add_argument("--buscar", type=str, help="Palabra clave o empresa (ej. 'Metrogas', 'Banco', 'FNE')")
    parser.add_argument("--ultimas", action="store_true", help="Mostrar últimas sentencias emitidas por el TDLC")
    args = parser.parse_args()

    client = TDLCClient()

    if args.buscar:
        print(f"\n🛒 Buscando en el TDLC: '{args.buscar}'...")
        res = client.search_jurisprudencia(args.buscar)
        print(f"Resultados encontrados: {len(res)}")
        for idx, item in enumerate(res):
            print(f"\n[{idx+1}] {item.get('titulo')}")
            print(f"  📅 Fecha: {item.get('fecha')} | 🔗 Sentencia: {item.get('link')}")
    else:
        print("\n🛒 Consultando Últimas Sentencias del TDLC...")
        res = client.get_sentencias(page=1, per_page=5)
        print(f"Total mostradas: {len(res)}")
        for item in res:
            print(f"\n - {item.get('titulo')}")
            print(f"   📅 Fecha: {item.get('fecha')} | 🔗 {item.get('link')}")
