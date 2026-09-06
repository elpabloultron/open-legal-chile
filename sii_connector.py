"""
Open Legal Chile — Conector Oficial Servicio de Impuestos Internos (SII)
Módulo para consultar, indexar y buscar Circulares, Resoluciones e Instrucciones Tributarias
vinculantes del Director del Servicio de Impuestos Internos de Chile.
"""

import os
import sys
import re
import html
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
from config import safe_urlopen

BASE_URL = "https://www.sii.cl/normativa_legislacion"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "sii_cache")


class SIIClient:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def get_circulares_por_anio(self, anio: int = 2026, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Descarga e indexa el listado oficial de Circulares del SII para un año específico."""
        cache_key = f"circulares_{anio}"
        cache_file = self._get_cache_path(cache_key)

        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        url = f"{BASE_URL}/circulares/{anio}/indcir{anio}.htm"
        headers = {'User-Agent': 'OpenLegalChile/1.0 (Derecho Tributario Chile)'}
        req = urllib.request.Request(url, headers=headers)

        circulares_list = []
        try:
            with safe_urlopen(req, timeout=20) as resp:
                page_html = resp.read().decode("utf-8", errors="ignore")
                links = re.findall(r'<a[^>]+href=["\']([^"\']+\.pdf)["\'][^>]*>(.*?)</a>', page_html, re.IGNORECASE)

                for link, title in links:
                    clean_title = html.unescape(re.sub(r'<[^>]+>', '', title).strip())
                    clean_title = re.sub(r'\s+', ' ', clean_title)

                    # Extraer número de circular
                    num_match = re.search(r'Circular\s*N[°ºo\.\s]*([0-9]+)', clean_title, re.IGNORECASE)
                    num = num_match.group(1) if num_match else ""

                    full_pdf_url = link if link.startswith("http") else f"{BASE_URL}/circulares/{anio}/{link}"

                    circulares_list.append({
                        "anio": anio,
                        "numero": num,
                        "titulo": clean_title,
                        "pdfUrl": full_pdf_url
                    })

                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(circulares_list, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[Aviso] No se pudieron cargar circulares para el año {anio}: {e}")

        return circulares_list

    def get_resoluciones_por_anio(self, anio: int = 2026, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Descarga e indexa el listado oficial de Resoluciones Exentas del SII para un año específico."""
        cache_key = f"resoluciones_{anio}"
        cache_file = self._get_cache_path(cache_key)

        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        url = f"{BASE_URL}/resoluciones/{anio}/indres{anio}.htm"
        headers = {'User-Agent': 'OpenLegalChile/1.0 (Derecho Tributario Chile)'}
        req = urllib.request.Request(url, headers=headers)

        resoluciones_list = []
        try:
            with safe_urlopen(req, timeout=20) as resp:
                page_html = resp.read().decode("utf-8", errors="ignore")
                links = re.findall(r'<a[^>]+href=["\']([^"\']+\.pdf)["\'][^>]*>(.*?)</a>', page_html, re.IGNORECASE)

                for link, title in links:
                    clean_title = html.unescape(re.sub(r'<[^>]+>', '', title).strip())
                    clean_title = re.sub(r'\s+', ' ', clean_title)

                    num_match = re.search(r'Res(?:oluci[oó]n)?\s*Ex(?:enta)?\s*N[°ºo\.\s]*([0-9]+)', clean_title, re.IGNORECASE)
                    num = num_match.group(1) if num_match else ""

                    full_pdf_url = link if link.startswith("http") else f"{BASE_URL}/resoluciones/{anio}/{link}"

                    resoluciones_list.append({
                        "anio": anio,
                        "tipo": "Resolución Exenta SII",
                        "numero": num,
                        "titulo": clean_title,
                        "pdfUrl": full_pdf_url
                    })

                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(resoluciones_list, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[Aviso] No se pudieron cargar resoluciones para el año {anio}: {e}")

        return resoluciones_list

    def get_oficios_por_anio(self, anio: int = 2026, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Descarga e indexa la jurisprudencia administrativa (Oficios Ordinarios) del Director del SII (Art. 26 CT)."""
        cache_key = f"oficios_{anio}"
        cache_file = self._get_cache_path(cache_key)

        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        url = f"{BASE_URL}/jurisprudencia/administrativa/{anio}/indjad{anio}.htm"
        headers = {'User-Agent': 'OpenLegalChile/1.0 (Derecho Tributario Chile)'}
        req = urllib.request.Request(url, headers=headers)

        oficios_list = []
        try:
            with safe_urlopen(req, timeout=20) as resp:
                page_html = resp.read().decode("utf-8", errors="ignore")
                links = re.findall(r'<a[^>]+href=["\']([^"\']+\.htm[l]?|[^"\']+\.pdf)["\'][^>]*>(.*?)</a>', page_html, re.IGNORECASE)

                for link, title in links:
                    clean_title = html.unescape(re.sub(r'<[^>]+>', '', title).strip())
                    clean_title = re.sub(r'\s+', ' ', clean_title)

                    if len(clean_title) < 5 or "volver" in clean_title.lower():
                        continue

                    num_match = re.search(r'Oficio\s*N[°ºo\.\s]*([0-9]+)', clean_title, re.IGNORECASE)
                    num = num_match.group(1) if num_match else ""

                    full_url = link if link.startswith("http") else f"{BASE_URL}/jurisprudencia/administrativa/{anio}/{link}"

                    oficios_list.append({
                        "anio": anio,
                        "tipo": "Oficio Ordinario (Jurisprudencia Administrativa)",
                        "numero": num,
                        "titulo": clean_title,
                        "url": full_url
                    })

                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(oficios_list, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[Aviso] No se pudieron cargar oficios para el año {anio}: {e}")

        return oficios_list

    def search_resoluciones_y_oficios(self, query: str, anios: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Busca resoluciones exentas y oficios del SII por número o término tributario."""
        if not anios:
            anios = [2026, 2025, 2024, 2023]

        q_lower = query.lower().strip()
        matches = []

        for yr in anios:
            for r in self.get_resoluciones_por_anio(yr):
                if q_lower in r.get("titulo", "").lower() or q_lower == str(r.get("numero", "")).lower():
                    matches.append(r)

            for o in self.get_oficios_por_anio(yr):
                if q_lower in o.get("titulo", "").lower() or q_lower == str(o.get("numero", "")).lower():
                    matches.append(o)

        return matches

    def search_circulares(self, query: str, anios: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Busca circulares del SII por número o texto en los años seleccionados (por defecto 2020 a 2026)."""
        if not anios:
            anios = [2026, 2025, 2024, 2023, 2022, 2021, 2020]

        q_lower = query.lower().strip()
        matches = []

        for yr in anios:
            cir_list = self.get_circulares_por_anio(yr)
            for c in cir_list:
                titulo = c.get("titulo", "").lower()
                num = str(c.get("numero", "")).lower()
                if q_lower in titulo or q_lower == num or f"circular {q_lower}" in titulo:
                    matches.append(c)

        return matches


# ==============================================================================
# CLI DE CONSULTA RÁPIDA DE CIRCULARES SII
# ==============================================================================
if __name__ == "__main__":
    import argparse
    try:
        if hasattr(sys.stdout, "reconfigure"):
            getattr(sys.stdout, "reconfigure")(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Conector Open Legal Chile — Servicio de Impuestos Internos (SII)")
    parser.add_argument("--buscar", type=str, help="Número o término de búsqueda (ej. 'Circular 34' o '34')")
    parser.add_argument("--anio", type=int, default=2026, help="Año de consulta de circulares (ej. 2026, 2025)")
    args = parser.parse_args()

    client = SIIClient()

    if args.buscar:
        print(f"\n💰 Buscando en Circulares del SII: '{args.buscar}'...")
        res = client.search_circulares(args.buscar)
        print(f"Resultados encontrados: {len(res)}")
        for idx, item in enumerate(res):
            print(f"\n[{idx+1}] {item.get('titulo')}")
            print(f"  📄 PDF Oficial: {item.get('pdfUrl')}")
    else:
        print(f"\n💰 Consultando Circulares del SII año {args.anio}...")
        res = client.get_circulares_por_anio(args.anio)
        print(f"Total Circulares publicadas en {args.anio}: {len(res)}")
        print("\nMuestra de circulares:")
        for item in res[:5]:
            print(f" - {item.get('titulo')} -> {item.get('pdfUrl')}")
