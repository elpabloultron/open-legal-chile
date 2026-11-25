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
import pathlib
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
from config import cache_fresco, leer_json_si_se_puede, safe_urlopen

BASE_URL = "https://www.tdlc.cl/wp-json/wp/v2"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "tdlc_cache")
_TTL_CACHE_SEGUNDOS = 30 * 24 * 60 * 60  # la jurisprudencia del TDLC cambia lento: un mes


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

        copia = leer_json_si_se_puede(cache_file) if use_cache else None
        if copia is not None and cache_fresco(cache_file, _TTL_CACHE_SEGUNDOS):
            return copia

        url = f"{BASE_URL}/tdlc-sentencias?page={page}&per_page={per_page}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "OpenLegalChile/1.0 (Libre Competencia Chile)",
                "Accept": "application/json"
            }
        )

        try:
            with safe_urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        except Exception:
            if copia:
                return copia  # copia vencida: mejor la lista vieja que ninguna
            raise

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
        cache_key = f"dictamenes_p{page}_s{per_page}"
        cache_file = self._get_cache_path(cache_key)

        copia = leer_json_si_se_puede(cache_file) if use_cache else None
        if copia is not None and cache_fresco(cache_file, _TTL_CACHE_SEGUNDOS):
            return copia

        url = f"{BASE_URL}/dictamenes?page={page}&per_page={per_page}"
        req = urllib.request.Request(url, headers={"User-Agent": "OpenLegalChile/1.0", "Accept": "application/json"})
        try:
            with safe_urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                res = [{
                    "id": item.get("id"),
                    "tipo": "Dictamen No Contencioso TDLC",
                    "titulo": html.unescape(re.sub(r'<[^>]+>', '', item.get("title", {}).get("rendered", "")).strip()),
                    "fecha": item.get("date", "")[:10],
                    "link": item.get("link", "")
                } for item in data]
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(res, f, ensure_ascii=False, indent=2)
                return res
        except Exception:
            return copia if copia else []

    def get_instrucciones_generales(self, page: int = 1, per_page: int = 10, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Obtiene las Instrucciones de Carácter General (ICG) emitidas por el TDLC."""
        cache_key = f"icg_p{page}_s{per_page}"
        cache_file = self._get_cache_path(cache_key)

        copia = leer_json_si_se_puede(cache_file) if use_cache else None
        if copia is not None and cache_fresco(cache_file, _TTL_CACHE_SEGUNDOS):
            return copia

        url = f"{BASE_URL}/instrucciones-generales?page={page}&per_page={per_page}"
        req = urllib.request.Request(url, headers={"User-Agent": "OpenLegalChile/1.0", "Accept": "application/json"})
        try:
            with safe_urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                res = [{
                    "id": item.get("id"),
                    "tipo": "Instrucción de Carácter General (ICG) TDLC",
                    "titulo": html.unescape(re.sub(r'<[^>]+>', '', item.get("title", {}).get("rendered", "")).strip()),
                    "fecha": item.get("date", "")[:10],
                    "link": item.get("link", "")
                } for item in data]
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(res, f, ensure_ascii=False, indent=2)
                return res
        except Exception:
            return copia if copia else []

    def _buscar_wp_endpoint(self, endpoint: str, tipo: str, query: str, per_page: int = 15) -> List[Dict[str, Any]]:
        """Consulta la búsqueda nativa (?search=) de la REST API WordPress del TDLC con caché."""
        q_clean = query.strip()
        if not q_clean:
            return []
        safe_key = re.sub(r"[^a-z0-9]+", "_", q_clean.lower()).strip("_")[:48] or "q"
        cache_file = self._get_cache_path(f"search_{endpoint}_{safe_key}_{per_page}")
        copia = leer_json_si_se_puede(cache_file)
        if copia is not None and cache_fresco(cache_file, _TTL_CACHE_SEGUNDOS):
            return copia

        url = f"{BASE_URL}/{endpoint}?search={urllib.parse.quote(q_clean)}&per_page={per_page}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "OpenLegalChile/1.0 (Libre Competencia Chile)", "Accept": "application/json"},
        )
        try:
            with safe_urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            if not isinstance(data, list):
                return []
            res: List[Dict[str, Any]] = []
            for item in data:
                raw_title = item.get("title", {}).get("rendered", "")
                raw_excerpt = item.get("excerpt", {}).get("rendered", "")
                clean_title = html.unescape(re.sub(r"<[^>]+>", "", raw_title).strip())
                clean_excerpt = html.unescape(re.sub(r"<[^>]+>", " ", raw_excerpt))
                clean_excerpt = re.sub(r"\s+", " ", clean_excerpt).strip()[:400]
                entry: Dict[str, Any] = {
                    "id": item.get("id"),
                    "tipo": tipo,
                    "titulo": clean_title,
                    "fecha": item.get("date", "")[:10],
                    "link": item.get("link", ""),
                }
                if clean_excerpt:
                    entry["extracto"] = clean_excerpt
                res.append(entry)
            if res:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(res, f, ensure_ascii=False, indent=2)
            return res
        except Exception:
            return copia if isinstance(copia, list) else []

    def search_jurisprudencia(self, query: str, max_pages: int = 3) -> List[Dict[str, Any]]:
        """Busca en sentencias, dictámenes e instrucciones generales del TDLC vía ?search= y fallback por título."""
        q_clean = query.strip()
        if not q_clean:
            return self.get_sentencias(page=1, per_page=20)

        # 1. Búsqueda de texto completo nativa de WordPress REST API (?search= busca en cuerpo y extracto)
        variantes = [q_clean]
        # Equivalencias frecuentes sin tilde (ej. colusion -> colusión)
        _tildes = {
            "colusion": "colusión",
            "posicion": "posición",
            "fusion": "fusión",
            "concentracion": "concentración",
            "resolucion": "resolución",
            "licitacion": "licitación",
            "interlocking": "interlocking",
        }
        q_low = q_clean.lower()
        for k, v in _tildes.items():
            if k in q_low and v not in q_low:
                variantes.append(re.sub(re.escape(k), v, q_low, flags=re.IGNORECASE))

        matches: List[Dict[str, Any]] = []
        vistos: set = set()
        endpoints = [
            ("tdlc-sentencias", "Sentencia TDLC"),
            ("dictamenes", "Dictamen No Contencioso TDLC"),
            ("instrucciones-generales", "Instrucción de Carácter General (ICG) TDLC"),
        ]
        for var in variantes:
            for ep, tipo in endpoints:
                for item in self._buscar_wp_endpoint(ep, tipo, var, per_page=15):
                    clave = (ep, item.get("id") or item.get("titulo"))
                    if clave not in vistos:
                        vistos.add(clave)
                        matches.append(item)
            if matches:
                break

        if matches:
            return matches

        # 2. Fallback por páginas recientes (cubre caché offline o títulos sin índice WP)
        q_lower = q_clean.lower()
        for p in range(1, max_pages + 1):
            sentencias = self.get_sentencias(page=p, per_page=20)
            for s in sentencias:
                if q_lower in s.get("titulo", "").lower():
                    matches.append(s)

            dictamenes = self.get_dictamenes(page=p, per_page=20)
            for d in dictamenes:
                if q_lower in d.get("titulo", "").lower():
                    matches.append(d)

            icgs = self.get_instrucciones_generales(page=p, per_page=20)
            for i in icgs:
                if q_lower in i.get("titulo", "").lower():
                    matches.append(i)

            if len(sentencias) < 20 and len(dictamenes) < 20:
                break

        return matches

    def descargar_sentencia_pdf(self, sentencia_id_o_url: str, pdf_url: Optional[str] = None) -> Optional[str]:
        """Descarga el PDF oficial firmado de una sentencia o resolución del TDLC."""
        clean_id = re.sub(r'[^0-9]+', '_', str(sentencia_id_o_url)).strip('_') or "doc"
        target_path = pathlib.Path(self.cache_dir) / "descargas_pdf" / f"sentencia_tdlc_{clean_id}.pdf"
        if target_path.exists() and target_path.stat().st_size > 1000:
            return str(target_path)

        url_final = pdf_url
        if not url_final and str(sentencia_id_o_url).startswith("http"):
            try:
                req_page = urllib.request.Request(sentencia_id_o_url, headers={"User-Agent": "OpenLegalChile/1.0"})
                with safe_urlopen(req_page, timeout=20) as resp:
                    page_html = resp.read().decode("utf-8", errors="ignore")
                pdf_matches = re.findall(r'href=["\']([^"\']*\.pdf)["\']', page_html, re.IGNORECASE)
                if pdf_matches:
                    url_final = pdf_matches[0]
            except Exception:
                pass

        if not url_final:
            return None

        from forensic_ocr import descargar_pdf_cacheado
        return descargar_pdf_cacheado(url_final, target_path, user_agent="OpenLegalChile/1.0 (Libre Competencia Chile)")

    def get_sentencia_integral(self, numero_o_id: str, descargar_formato: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene una sentencia o pronunciamiento del TDLC con texto integral y metadatos."""
        q = str(numero_o_id).strip()
        matches = self.search_jurisprudencia(q, max_pages=2)
        match_item = None
        for m in matches:
            if q.lower() in m.get("titulo", "").lower() or str(m.get("id")) == q:
                match_item = m
                break
        if not match_item and matches:
            match_item = matches[0]

        if not match_item:
            return {"error": f"Sentencia o pronunciamiento '{numero_o_id}' no encontrado en el TDLC."}

        link_post = match_item.get("link", "")
        ruta_pdf = self.descargar_sentencia_pdf(match_item.get("id", "doc"), pdf_url=None)
        if not ruta_pdf and link_post:
            ruta_pdf = self.descargar_sentencia_pdf(link_post)

        from forensic_ocr import extraer_texto_pdf_con_ocr
        texto_pdf = extraer_texto_pdf_con_ocr(ruta_pdf)

        m_num = re.search(r'N[°ºo\.\s]*([0-9]+(?:/[0-9]+)?)', match_item.get("titulo", ""), re.IGNORECASE)
        identificador = m_num.group(1) if m_num else str(match_item.get("id", q))
        texto_final = texto_pdf if len(texto_pdf) > 80 else match_item.get("titulo", "")

        doc = {
            "organismo": "TDLC",
            "tipo_acto": "Sentencia",
            "identificador": identificador,
            "numero": identificador,
            "fecha": match_item.get("fecha", ""),
            "materia": match_item.get("titulo", ""),
            "titulo": match_item.get("titulo", ""),
            "texto": texto_final,
            "texto_integral": texto_final,
            "link_oficial": link_post,
            "fuentes_legales": ["DL 211"],
        }

        if descargar_formato and descargar_formato.lower() == "pdf" and ruta_pdf:
            doc["archivo_descargado"] = ruta_pdf
            doc["formato_descargado"] = "pdf"

        return doc

    def get_sentencias_lote(self, numeros_o_ids: List[str], descargar_formato: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene una lista de sentencias del TDLC en lote."""
        docs = []
        for nid in numeros_o_ids:
            docs.append(self.get_sentencia_integral(nid, descargar_formato=descargar_formato))
        return docs

    def procesar_y_graficar_tdlc(
        self,
        ids_o_docs: List[Any],
        tema_relevante: Optional[str] = None,
        convertir_a_md: bool = True,
        descargar_formato: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Pipeline unificado para sentencias y resoluciones del TDLC."""
        from resoluciones_parser import procesar_y_graficar_lote

        return procesar_y_graficar_lote(
            ids_o_docs,
            lambda item: self.get_sentencia_integral(item, descargar_formato=descargar_formato),
            organismo="TDLC",
            clave_total="total_sentencias",
            clave_detalle="detalle_sentencias",
            tema_relevante=tema_relevante,
            convertir_a_md=convertir_a_md,
        )


# ==============================================================================
# CLI DE CONSULTA RÁPIDA DE LIBRE COMPETENCIA (TDLC)
# ==============================================================================
if __name__ == "__main__":
    import argparse
    try:
        if hasattr(sys.stdout, "reconfigure"):
            getattr(sys.stdout, "reconfigure")(encoding="utf-8")
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
