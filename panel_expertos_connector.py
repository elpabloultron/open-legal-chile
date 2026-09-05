"""
Open Legal Chile — Conector Oficial Panel de Expertos de la Ley Eléctrica
Módulo para consultar, indexar y buscar Dictámenes, Discrepancias, Audiencias y Documentos
vinculantes del Panel de Expertos de la Ley General de Servicios Eléctricos (DFL 4/2006).
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
from config import safe_urlopen

BASE_URL = "https://discrepancias.panelexpertos.cl/api/v1"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "panel_expertos_cache")


class PanelExpertosClient:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def get_discrepancies(self, page: int = 1, size: int = 20, use_cache: bool = True) -> Dict[str, Any]:
        """Obtiene el listado paginado de discrepancias y dictámenes del Panel de Expertos."""
        cache_key = f"discrepancies_p{page}_s{size}"
        cache_file = self._get_cache_path(cache_key)

        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        url = f"{BASE_URL}/discrepancies?page={page}&size={size}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "OpenLegalChile/1.0 (Derecho Energetico Chile)",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )

        with safe_urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return data

    def search_dictamenes(self, query: str, max_pages: int = 5, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Busca dictámenes y discrepancias por texto (empresa, materia, número, palabra clave)."""
        q_lower = query.lower().strip()
        results = []

        for p in range(1, max_pages + 1):
            page_data = self.get_discrepancies(page=p, size=20, use_cache=use_cache)

            objects = page_data.get("objects", {})
            discrepancies = objects.get("discrepancies", {})
            documents = objects.get("documents", {})
            legal_sub_matters = objects.get("legalSubMatters", {})

            for d_id, d_val in discrepancies.items():
                num = str(d_val.get("number", ""))
                sub_matter_id = str(d_val.get("legalSubMatterId", ""))
                sub_matter_name = legal_sub_matters.get(sub_matter_id, {}).get("name", "")

                # Buscar en documentos asociados (títulos de dictámenes)
                doc_matches = []
                for doc_id, doc_val in documents.items():
                    if str(doc_val.get("discrepancyId")) == str(d_id):
                        doc_title = doc_val.get("title", "")
                        doc_matches.append({
                            "id": doc_id,
                            "titulo": doc_title,
                            "tipo": doc_val.get("documentTypeId"),
                            "url": doc_val.get("url")
                        })

                doc_titles_str = " ".join([d["titulo"] for d in doc_matches]).lower()
                combined_text = f"discrepancia {num} {sub_matter_name} {doc_titles_str}".lower()

                if q_lower in combined_text or not query:
                    results.append({
                        "id": d_id,
                        "numero": num,
                        "materia": sub_matter_name,
                        "fecha_inicio": d_val.get("createdAt"),
                        "fecha_termino": d_val.get("endedAt"),
                        "documentos": doc_matches
                    })

            if p >= page_data.get("totalPages", 1):
                break

        return results

    def get_dictamen_detalles(self, discrepancy_id: int) -> Dict[str, Any]:
        """Obtiene el expediente completo y documentos de una discrepancia."""
        # Buscamos en caché o páginas
        data = self.get_discrepancies(page=1, size=50)
        objects = data.get("objects", {})
        disc = objects.get("discrepancies", {}).get(str(discrepancy_id))
        docs = [d for d in objects.get("documents", {}).values() if str(d.get("discrepancyId")) == str(discrepancy_id)]

        return {
            "discrepancia": disc,
            "documentos": docs
        }


# ==============================================================================
# CLI DEL PANEL DE EXPERTOS
# ==============================================================================
if __name__ == "__main__":
    import argparse
    try:
        if hasattr(sys.stdout, "reconfigure"):
            getattr(sys.stdout, "reconfigure")(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Conector Open Legal Chile — Panel de Expertos de la Ley Eléctrica")
    parser.add_argument("--buscar", type=str, help="Palabra clave o empresa a buscar en los dictámenes")
    parser.add_argument("--ultimos", action="store_true", help="Mostrar últimas discrepancias tramitadas")
    parser.add_argument("--discrepancia", type=int, help="ID de discrepancia para ver expediente")
    args = parser.parse_args()

    client = PanelExpertosClient()

    if args.buscar:
        print(f"\n⚖️ Buscando en el Panel de Expertos: '{args.buscar}'...")
        res = client.search_dictamenes(args.buscar)
        print(f"Resultados encontrados: {len(res)}")
        for item in res[:5]:
            print(f"\n[Discrepancia N° {item['numero']} — ID: {item['id']}]")
            print(f"  Materia: {item['materia'] or 'No especificada'}")
            print(f"  Fecha: {item['fecha_inicio']}")
            print(f"  Documentos ({len(item['documentos'])}):")
            for doc in item['documentos'][:3]:
                print(f"   - {doc['titulo']}")
    elif args.ultimos or len(sys.argv) == 1:
        print("\n⚡ Consultando Últimas Discrepancias y Dictámenes del Panel de Expertos...")
        res = client.search_dictamenes("", max_pages=1)
        print(f"Total discrepancias recientes: {len(res)}")
        for item in res[:5]:
            print(f" - Discrepancia N° {item['numero']} (ID: {item['id']}) | Materia: {item['materia'] or 'Suministro/Peajes'}")
            for doc in item['documentos'][:2]:
                print(f"    * Doc: {doc['titulo']}")
