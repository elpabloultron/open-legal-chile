"""
Open Legal Chile — Conector Oficial Contraloría General de la República (CGR)
Módulo para consultar, indexar y buscar Jurisprudencia Administrativa, Dictámenes,
Instructivos y Auditorías vinculantes de la Contraloría General de la República de Chile.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
from config import safe_urlopen

BASE_URL = "https://www.contraloria.cl/apibusca"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cgr_cache")


class CGRClient:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def search_jurisprudencia(self, query: str, source: str = "dictamenes", page: int = 1, exact: bool = False, use_cache: bool = True) -> Dict[str, Any]:
        """Busca en el Sistema de Jurisprudencia de la Contraloría General de la República."""
        clean_q = query.strip().replace(" ", "_").lower()
        cache_key = f"{source}_{clean_q}_p{page}"
        cache_file = self._get_cache_path(cache_key)

        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        url = f"{BASE_URL}/search/{source}"
        date_name = "fecha_promulgación" if source == "legislacion" else "fecha_documento"

        payload = {
            "search": query,
            "exact_search": exact,
            "options": {},
            "order": "desc",
            "date_name": date_name,
            "source": source,
            "page": page
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "OpenLegalChile/1.0 (Derecho Administrativo Chile)"
            }
        )

        with safe_urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
            res_json = json.loads(raw)

            hits = res_json.get("hits", {})
            total_val = hits.get("total", {})
            total_count = total_val.get("value", 0) if isinstance(total_val, dict) else total_val
            raw_items = hits.get("hits", [])

            clean_results = []
            for item in raw_items:
                src = item.get("_source", {})
                doc_id = src.get("numeric_doc_id") or src.get("doc_id") or src.get("número") or src.get("numero") or item.get("_id")
                fecha = src.get("fecha_documento") or src.get("fecha") or ""
                nombre = src.get("nombre") or src.get("title") or src.get("titulo") or ""
                materia = src.get("materia") or src.get("resena") or src.get("descriptores") or nombre or ""
                objetivo = src.get("objetivo") or ""
                conclusiones = src.get("conclusiones") or ""
                texto = src.get("texto_completo") or src.get("texto") or src.get("resumen") or conclusiones or objetivo or ""
                organismo = src.get("organismo") or src.get("organismos_destinatarios") or src.get("servicio_") or ""
                pdf_url = src.get("pdf") or ""

                clean_results.append({
                    "docId": str(doc_id),
                    "nombre": nombre.strip(),
                    "fecha": fecha[:10] if len(fecha) >= 10 else fecha,
                    "materia": materia.strip(),
                    "objetivo": objetivo.strip() if isinstance(objetivo, str) else "",
                    "conclusiones": conclusiones.strip() if isinstance(conclusiones, str) else "",
                    "organismo": organismo if isinstance(organismo, str) else "",
                    "texto": texto.strip() if isinstance(texto, str) else "",
                    "pdfUrl": pdf_url if pdf_url.startswith("http") else (f"https://www.contraloria.cl{pdf_url}" if pdf_url else "")
                })

            output_data = {
                "query": query,
                "source": source,
                "total": total_count,
                "page": page,
                "resultados": clean_results
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            return output_data

    def get_dictamen(self, doc_id: str) -> Dict[str, Any]:
        """Obtiene el texto completo de un dictamen específico por su número/código oficial."""
        res = self.search_jurisprudencia(doc_id, source="dictamenes", exact=True)
        if res.get("resultados"):
            return res["resultados"][0]
        # Búsqueda abierta si no es exacto
        res = self.search_jurisprudencia(doc_id, source="dictamenes", exact=False)
        if res.get("resultados"):
            return res["resultados"][0]
        return {"error": f"Dictamen {doc_id} no encontrado en la base de la CGR."}

    def search_instructivos(self, query: str, page: int = 1) -> Dict[str, Any]:
        """Busca en los Instructivos y Circulares generales de la CGR."""
        return self.search_jurisprudencia(query, source="instructivos", page=page)

    def search_auditorias(self, query: str, page: int = 1) -> Dict[str, Any]:
        """Busca en los Informes Finales de Auditoría de la CGR."""
        return self.search_jurisprudencia(query, source="auditoria", page=page)


# ==============================================================================
# CLI DE CONSULTA RÁPIDA DE JURISPRUDENCIA CGR
# ==============================================================================
if __name__ == "__main__":
    import argparse
    try:
        if hasattr(sys.stdout, "reconfigure"):
            getattr(sys.stdout, "reconfigure")(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Conector Open Legal Chile — Contraloría General de la República (CGR)")
    parser.add_argument("--buscar", type=str, help="Término de búsqueda o materia (ej. 'confianza legitima' o 'compras publicas')")
    parser.add_argument("--id", type=str, help="Código de Dictamen (ej. D286N26)")
    parser.add_argument("--instructivos", type=str, help="Buscar en Instructivos de la CGR")
    parser.add_argument("--auditorias", type=str, help="Buscar en Informes de Auditoría de la CGR")
    args = parser.parse_args()

    client = CGRClient()

    if args.id:
        print(f"\n🏛️ Consultando Dictamen CGR N° {args.id}...")
        data = client.get_dictamen(args.id)
        if data and isinstance(data, dict):
            fecha = data.get('fecha', '')
            anio = fecha[:4] if fecha else 's/f'
            print(f"\n[Dictamen CGR N° {data.get('docId')} ({anio})]")
            print(f"📌 Materia / Criterio:\n{data.get('materia')}")
            if data.get("texto"):
                print(f"\n📜 Texto:\n{str(data.get('texto'))[:500]}...")
        else:
            print("❌ Dictamen no encontrado o error en respuesta.")
    elif args.instructivos:
        print(f"\n📜 Buscando Instructivos CGR: '{args.instructivos}'...")
        res = client.search_instructivos(args.instructivos)
        print(f"Total encontrados: {res.get('total')}")
        for idx, item in enumerate(res.get("resultados", [])[:5]):
            print(f"\n[{idx+1}] Instructivo N° {item.get('docId')} ({item.get('fecha')})")
            print(f"  📌 {item.get('materia')[:200]}...")
    elif args.auditorias:
        print(f"\n🔍 Buscando Informes de Auditoría CGR: '{args.auditorias}'...")
        res = client.search_auditorias(args.auditorias)
        print(f"Total encontrados: {res.get('total')}")
        for idx, item in enumerate(res.get("resultados", [])[:5]):
            print(f"\n[{idx+1}] Informe N° {item.get('docId')} ({item.get('fecha')})")
            print(f"  📌 {item.get('materia')[:200]}...")
    elif args.buscar or len(sys.argv) == 1:
        q = args.buscar or "compras publicas"
        print(f"\n🏛️ Buscando Dictámenes en la Contraloría: '{q}'...")
        res = client.search_jurisprudencia(q)
        print(f"Total Dictámenes encontrados: {res.get('total')}")
        for idx, item in enumerate(res.get("resultados", [])[:5]):
            print(f"\n[{idx+1}] Dictamen CGR N° {item.get('docId')} ({item.get('fecha')})")
            print(f"  📌 Materia: {item.get('materia')}")
