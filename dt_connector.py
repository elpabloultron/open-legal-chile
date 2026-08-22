"""
Open Legal Chile — Conector Oficial Dirección del Trabajo (DT)
Módulo para consultar, indexar y buscar Dictámenes, Ordinarios y Doctrina Laboral vinculante
de la Dirección del Trabajo de Chile.
"""

import os
import sys
import re
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional

BASE_URL = "https://www.dt.gob.cl/legislacion/1624"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "dt_cache")


class DTClient:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def get_index_ordinarios(self, use_cache: bool = True) -> List[Dict[str, str]]:
        """Descarga e indexa el listado maestro de Ordinarios y Dictámenes de la DT."""
        cache_file = self._get_cache_path("index_ordinarios")
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        url = f"{BASE_URL}/w3-propertyvalue-147182.html"
        headers = {'User-Agent': 'OpenLegalChile/1.0 (Derecho Laboral Chile)'}
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            # Extraer enlaces a artículos de dictámenes
            items = re.findall(r'<a[^>]+href=["\']([^"\']*(?:w3-article-[0-9]+|article)[^"\']*)["\'][^>]*>(.*?)</a>', html)
            index_list = []
            seen = set()

            for link, title in items:
                clean_title = re.sub(r'<[^>]+>', '', title).strip()
                if clean_title and clean_title not in seen:
                    seen.add(clean_title)
                    # Normalizar link
                    article_id = ""
                    m_id = re.search(r'article-([0-9]+)', link)
                    if m_id:
                        article_id = m_id.group(1)

                    index_list.append({
                        "numero": clean_title,
                        "articleId": article_id,
                        "link": link if link.startswith("http") else f"{BASE_URL}/{link}"
                    })

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(index_list, f, ensure_ascii=False, indent=2)

            return index_list

    def get_dictamen_content(self, article_id_or_url: str, use_cache: bool = True) -> Dict[str, Any]:
        """Descarga y parsea el contenido completo, materias y doctrina de un dictamen de la DT."""
        if str(article_id_or_url).isdigit():
            article_id = str(article_id_or_url)
            url = f"{BASE_URL}/w3-article-{article_id}.html"
        elif "w3-article-" in article_id_or_url:
            m = re.search(r'article-([0-9]+)', article_id_or_url)
            article_id = m.group(1) if m else "doc"
            url = article_id_or_url if article_id_or_url.startswith("http") else f"{BASE_URL}/{article_id_or_url}"
        else:
            article_id = "doc"
            url = article_id_or_url

        cache_file = self._get_cache_path(f"doc_{article_id}")
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        headers = {'User-Agent': 'OpenLegalChile/1.0 (Derecho Laboral Chile)'}
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

            title_m = re.search(r'<title>(.*?)</title>', html)
            title = title_m.group(1).replace(" - DT - Normativa 3.0", "").strip() if title_m else ""

            # Extraer párrafos
            raw_p = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
            clean_paragraphs = []
            for p in raw_p:
                clean = re.sub(r'<[^>]+>', ' ', p).strip()
                clean = re.sub(r'\s+', ' ', clean)
                if clean and len(clean) > 15 and not clean.startswith("Inicio /") and "Dirección del Trabajo" not in clean:
                    clean_paragraphs.append(clean)

            # Extraer materias y doctrina
            materias = ""
            doctrina = ""
            if len(clean_paragraphs) > 0:
                materias = clean_paragraphs[0]
            if len(clean_paragraphs) > 1:
                doctrina = clean_paragraphs[1]

            doc_data = {
                "articleId": article_id,
                "titulo": title,
                "url": url,
                "materias": materias,
                "doctrina": doctrina,
                "parrafos": clean_paragraphs
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(doc_data, f, ensure_ascii=False, indent=2)

            return doc_data

    def search_dictamenes(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca dictámenes u ordinarios por número o palabra clave."""
        index = self.get_index_ordinarios()
        q_lower = query.lower().strip()
        matches = []

        for item in index:
            num = item.get("numero", "").lower()
            if q_lower in num or num.startswith(q_lower):
                matches.append(item)
                if len(matches) >= limit:
                    break

        # Si son pocos o no hubo coincidencia por número exacto, buscar en contenidos descargados
        results = []
        for m in matches:
            art_id = m.get("articleId")
            if art_id:
                try:
                    content = self.get_dictamen_content(art_id)
                    results.append(content)
                except Exception:
                    results.append({
                        "articleId": art_id,
                        "titulo": m.get("numero"),
                        "url": m.get("link")
                    })
            else:
                results.append(m)

        return results


# ==============================================================================
# CLI DE CONSULTA RÁPIDA DE DICTÁMENES DT
# ==============================================================================
if __name__ == "__main__":
    import argparse
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Conector Open Legal Chile — Dictámenes Dirección del Trabajo (DT)")
    parser.add_argument("--buscar", type=str, help="Número o término de búsqueda (ej. ORD.N°344 o 344)")
    parser.add_argument("--id", type=str, help="ID de artículo DT (ej. 129517)")
    parser.add_argument("--ultimos", action="store_true", help="Listar los últimos ordinarios publicados por la DT")
    args = parser.parse_args()

    client = DTClient()

    if args.id:
        print(f"\n💼 Consultando Dictamen ID {args.id} en la Dirección del Trabajo...")
        data = client.get_dictamen_content(args.id)
        print(f"\n[Título: {data.get('titulo')}]")
        print(f"📌 Materias: {data.get('materias')}")
        print(f"\n📜 Doctrina / Dictamen:\n{data.get('doctrina')}")
        print(f"\n🔗 Fuente: {data.get('url')}")
    elif args.buscar:
        print(f"\n💼 Buscando en la base de la Dirección del Trabajo: '{args.buscar}'...")
        res = client.search_dictamenes(args.buscar)
        print(f"Resultados encontrados: {len(res)}")
        for item in res:
            print(f"\n[{item.get('titulo')}]")
            if item.get("materias"):
                print(f"  📌 Materias: {item.get('materias')}")
            if item.get("doctrina"):
                print(f"  📜 Doctrina: {item.get('doctrina')[:250]}...")
            print(f"  🔗 Enlace: {item.get('url')}")
    elif args.ultimos or len(sys.argv) == 1:
        print("\n💼 Consultando Catálogo Maestro de Ordinarios de la DT...")
        idx = client.get_index_ordinarios()
        print(f"Total Ordinarios y Dictámenes indexados: {len(idx)}")
        print("\nMuestra de dictámenes recientes:")
        for item in idx[:5]:
            print(f" - {item.get('numero')} (ID: {item.get('articleId')}) -> {item.get('link')}")
