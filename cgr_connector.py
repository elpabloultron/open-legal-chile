"""
Open Legal Chile — Conector Oficial Contraloría General de la República (CGR)
Módulo para consultar, indexar y buscar Jurisprudencia Administrativa, Dictámenes,
Instructivos y Auditorías vinculantes de la Contraloría General de la República de Chile.
"""

import os
import sys
import json
import re
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
from config import cache_fresco, leer_json_si_se_puede, safe_urlopen

BASE_URL = "https://www.contraloria.cl/apibusca"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cgr_cache")
_TTL_CACHE_SEGUNDOS = 30 * 24 * 60 * 60  # la jurisprudencia de la CGR cambia lento: un mes


def _normalizar_hit(item: Dict[str, Any]) -> Dict[str, Any]:
    """Traduce un registro crudo del indice de la CGR al formato citable de la suite."""
    src = item.get("_source", {})
    # doc_id ("E311060N23") es el identificador citable: incluye el anio.
    # numeric_doc_id ("E311060") lo omite y no sirve para citar.
    # En auditorias el identificador citable es "número" ("460/2026"); numeric_doc_id
    # trae solo el correlativo ("460") y pierde el anio.
    doc_id = (src.get("doc_id") or src.get("número") or src.get("numero")
              or src.get("numeric_doc_id") or item.get("_id"))
    fecha = src.get("fecha_documento") or src.get("fecha_promulgación") or src.get("fecha") or ""
    fecha = fecha[:10] if len(fecha) >= 10 else fecha
    nombre = src.get("nombre") or src.get("title") or src.get("titulo") or ""
    conclusiones = src.get("conclusiones") or ""
    objetivo = src.get("objetivo") or ""
    # El texto integro viaja en documento_completo dentro de la propia respuesta
    # de busqueda: no hace falta un segundo viaje al lector HTML del portal.
    texto = (src.get("documento_completo") or src.get("texto_completo") or src.get("texto")
             or src.get("resumen") or conclusiones or objetivo or "")
    organismo = (src.get("destinatarios") or src.get("organismo")
                 or src.get("organismos_destinatarios") or src.get("servicio_") or "")
    tipo = src.get("_tipo") or "dictamenes"
    # Procedencia citable. Ademas, los dictamenes anteriores a 2000 no traen
    # documento_completo en el indice pero si se leen en esta URL.
    url_html = f"https://www.contraloria.cl/pdfbuscador/{tipo}/{doc_id}/html"
    pdf_url = src.get("pdf") or ""
    if pdf_url and not pdf_url.startswith("http"):
        pdf_url = f"https://www.contraloria.cl{pdf_url}"

    def _txt(valor: Any) -> str:
        return valor.strip() if isinstance(valor, str) else ""

    return {
        "docId": str(doc_id),
        "numero": _txt(src.get("n_dictamen") or src.get("número") or src.get("numeric_doc_id") or ""),
        "anio": str(src.get("year_doc_id") or fecha[:4]),
        "nombre": _txt(nombre),
        "fecha": fecha,
        "materia": _txt(src.get("materia") or src.get("resena") or src.get("descriptores") or nombre),
        "descriptores": _txt(src.get("descriptores")),
        "fuentesLegales": _txt(src.get("fuentes_legales")),
        "objetivo": _txt(objetivo),
        "conclusiones": _txt(conclusiones),
        "organismo": _txt(organismo),
        "texto": _txt(texto),
        "pdfUrl": pdf_url,
        "urlHtml": url_html,
    }


class CGRClient:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def search_jurisprudencia(self, query: str, source: str = "dictamenes", page: int = 0, exact: bool = False, use_cache: bool = True) -> Dict[str, Any]:
        """Busca en el Sistema de Jurisprudencia de la Contraloría General de la República.

        La API de la CGR es 0-indexada y entrega 20 documentos por página:
        ``page=1`` devuelve la SEGUNDA página, y por eso una consulta acotada
        respondía ``total`` mayor que cero con ``resultados`` vacío.
        """
        clean_q = query.strip().replace(" ", "_").lower()
        cache_key = f"{source}_{clean_q}_p{page}"
        cache_file = self._get_cache_path(cache_key)

        data = leer_json_si_se_puede(cache_file) if use_cache else None
        if data is not None and cache_fresco(cache_file, _TTL_CACHE_SEGUNDOS):
            return data

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

        try:
            with safe_urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
        except Exception:
            if data is not None:
                return {**data, "copia_local_vencida": True}
            raise
        res_json = json.loads(raw)

        hits = res_json.get("hits", {})
        total_val = hits.get("total", {})
        total_count = total_val.get("value", 0) if isinstance(total_val, dict) else total_val
        raw_items = hits.get("hits", [])

        clean_results = [_normalizar_hit(item) for item in raw_items]

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
        """Obtiene un dictamen por su código oficial, validando el identificador.

        ``exact_search`` de la CGR no filtra: solo estrecha el análisis del texto.
        Quedarse con ``resultados[0]`` devolvía otro dictamen (pedir E311060N23
        entregaba 0E6541N25). Ante duda se retorna error con los candidatos:
        una cita falsa es peor que una búsqueda sin resultado.
        """
        buscado = doc_id.strip().upper().replace(" ", "")
        candidatos: List[Dict[str, Any]] = []
        for exact in (True, False):
            res = self.search_jurisprudencia(buscado, source="dictamenes", exact=exact)
            for item in res.get("resultados", []):
                if item["docId"].upper() == buscado or item.get("numero", "").upper() == buscado:
                    return item
                candidatos.append(item)
            # Fallback: <NUMERO>N<AA>, comparando número y año por separado.
            m = re.match(r"^(\d*[A-Z]?\d+)[N/-](\d{2,4})$", buscado)
            if m:
                numero, anio = m.group(1).lstrip("0"), m.group(2)[-2:]
                for item in res.get("resultados", []):
                    if item.get("numero", "").upper().lstrip("0") == numero and item.get("anio", "")[-2:] == anio:
                        return item
        return {
            "error": f"Dictamen {doc_id} no encontrado con identificador exacto en la base de la CGR.",
            "candidatos": [c["docId"] for c in candidatos[:5]],
        }

    def search_instructivos(self, query: str, page: int = 0) -> Dict[str, Any]:
        """Busca en los Instructivos y Circulares generales de la CGR."""
        return self.search_jurisprudencia(query, source="instructivos", page=page)

    def search_auditorias(self, query: str, page: int = 0) -> Dict[str, Any]:
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
