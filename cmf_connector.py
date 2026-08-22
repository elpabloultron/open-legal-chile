"""
Open Legal Chile — Conector Oficial Comisión para el Mercado Financiero (CMF)
Módulo para consultar, indexar y buscar Normas de Carácter General (NCG), Circulares,
Resoluciones y Oficios vinculantes para el mercado de valores, banca, seguros y Fintech en Chile.
"""

import os
import sys
import re
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional

BASE_URL = "https://www.cmfchile.cl/portal/normativa/624"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cmf_cache")


class CMFClient:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def get_index_normas(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Descarga e indexa el listado de Resoluciones, NCG y Circulares de la CMF."""
        cache_file = self._get_cache_path("index_normativa")
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        url = f"{BASE_URL}/w4-propertyvalue-49322.html"
        headers = {'User-Agent': 'OpenLegalChile/1.0 (Derecho Financiero Chile)'}
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            # Extraer enlaces a normas
            items = re.findall(r'<a[^>]+href=["\']([^"\']*(?:w4-article-[0-9]+|article)[^"\']*)["\'][^>]*>(.*?)</a>', html)
            index_list = []
            seen = set()

            for link, title in items:
                clean_title = re.sub(r'<[^>]+>', '', title).strip()
                if clean_title and clean_title not in seen:
                    seen.add(clean_title)
                    article_id = ""
                    m_id = re.search(r'article-([0-9]+)', link)
                    if m_id:
                        article_id = m_id.group(1)

                    index_list.append({
                        "titulo": clean_title,
                        "articleId": article_id,
                        "url": link if link.startswith("http") else f"{BASE_URL}/{link}",
                        "pdfUrl": f"{BASE_URL}/articles-{article_id}_doc_pdf.pdf" if article_id else ""
                    })

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(index_list, f, ensure_ascii=False, indent=2)

            return index_list

    def search_normativa(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Busca en el catálogo de normativa CMF por término, tipo (NCG, Circular, Resolución) o número."""
        index = self.get_index_normas()
        q_lower = query.lower().strip()
        matches = []

        for item in index:
            title = item.get("titulo", "").lower()
            if q_lower in title:
                matches.append(item)
                if len(matches) >= limit:
                    break

        return matches


# ==============================================================================
# CLI DE CONSULTA RÁPIDA DE NORMATIVA CMF
# ==============================================================================
if __name__ == "__main__":
    import argparse
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Conector Open Legal Chile — Comisión para el Mercado Financiero (CMF)")
    parser.add_argument("--buscar", type=str, help="Palabra clave o número de norma (ej. 'Resolución Nº 4521' o 'pensiones')")
    parser.add_argument("--ultimas", action="store_true", help="Mostrar últimas normas y resoluciones publicadas por la CMF")
    args = parser.parse_args()

    client = CMFClient()

    if args.buscar:
        print(f"\n🏢 Buscando en la base de la CMF: '{args.buscar}'...")
        res = client.search_normativa(args.buscar)
        print(f"Resultados encontrados: {len(res)}")
        for idx, item in enumerate(res):
            print(f"\n[{idx+1}] {item.get('titulo')}")
            print(f"  🔗 Ficha: {item.get('url')}")
            print(f"  📄 PDF: {item.get('pdfUrl')}")
    elif args.ultimas or len(sys.argv) == 1:
        print("\n🏢 Consultando Catálogo de Normas y Resoluciones CMF...")
        idx = client.get_index_normas()
        print(f"Total normas indexadas: {len(idx)}")
        print("\nMuestra de normas recientes:")
        for item in idx[:5]:
            print(f" - {item.get('titulo')} -> {item.get('pdfUrl')}")
