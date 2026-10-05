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

    def search_jurisprudencia(self, query: str, max_pages: int = 3) -> List[Dict[str, Any]]:
        """Busca en sentencias, dictámenes e instrucciones generales del TDLC por término o empresa involucrada."""
        q_lower = query.lower().strip()
        matches = []

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
        dest_folder = pathlib.Path(self.cache_dir) / "descargas_pdf"
        dest_folder.mkdir(parents=True, exist_ok=True)
        target_path = dest_folder / f"sentencia_tdlc_{clean_id}.pdf"

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

        try:
            req = urllib.request.Request(url_final, headers={'User-Agent': 'OpenLegalChile/1.0 (Libre Competencia Chile)'})
            with safe_urlopen(req, timeout=30) as resp:
                pdf_bytes = resp.read()
            if len(pdf_bytes) > 1000:
                target_path.write_bytes(pdf_bytes)
                return str(target_path)
        except Exception:
            pass
        return None

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

        texto_pdf = ""
        if ruta_pdf:
            try:
                import pymupdf
                pdf_doc: Any = pymupdf.open(ruta_pdf)
                t_paginas = [pdf_doc[i].get_text() for i in range(len(pdf_doc))]
                texto_extraido = "\n\n".join([t.strip() for t in t_paginas if t.strip()])
                if len(texto_extraido) > 80:
                    texto_pdf = texto_extraido
                else:
                    from forensic_ocr import ForensicOCREngine
                    ocr_res = ForensicOCREngine().extract_from_pdf(ruta_pdf, start_page=1, end_page=min(4, len(pdf_doc)))
                    texto_pdf = "\n\n".join([p.get("text", "") for p in ocr_res.get("pages", []) if p.get("text")]).strip()
            except Exception:
                pass

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
        descargar_formato: Optional[str] = None
    ) -> Dict[str, Any]:
        """Pipeline unificado para sentencias y resoluciones del TDLC."""
        from resolucion_administrativa2md import convertir_lote_dictamenes
        from resoluciones_parser import ResolucionesParserEngine
        from legal_graphify import LegalGraphifyEngine

        docs_procesar = []
        for item in ids_o_docs:
            if isinstance(item, str):
                doc_obj = self.get_sentencia_integral(item, descargar_formato=descargar_formato)
                docs_procesar.append(doc_obj)
            elif isinstance(item, dict):
                docs_procesar.append(item)

        rutas_md = []
        if convertir_a_md:
            try:
                rutas_md = [str(p) for p in convertir_lote_dictamenes(docs_procesar)]
                for i, r_path in enumerate(rutas_md):
                    if i < len(docs_procesar):
                        docs_procesar[i]["ruta_md"] = r_path
            except Exception:
                pass

        info_grafo = {}
        try:
            graph_engine = LegalGraphifyEngine()
            insumos = rutas_md if rutas_md else docs_procesar
            info_grafo = graph_engine.ingerir_lote_dictamenes(insumos, guardar_disco=False)
        except Exception as e:
            info_grafo = {"error": f"Error integrando con LegalGraphify: {str(e)}"}

        parser_engine = ResolucionesParserEngine()
        analisis = parser_engine.analizar_lote_resoluciones(docs_procesar, tema_relevante=tema_relevante)

        return {
            "organismo": "TDLC",
            "total_sentencias": len(docs_procesar),
            "tema_relevante": tema_relevante or "General",
            "citas_destacadas": analisis.get("citas_destacadas", []),
            "grafo_impacto": {
                "nodos_nuevos": info_grafo.get("nodos_nuevos_totales", 0),
                "enlaces_nuevos": info_grafo.get("enlaces_nuevos_totales", 0),
                "grafo_total": info_grafo.get("grafo", {})
            },
            "archivos_generados": {
                "markdown": rutas_md,
                "descargas_oficiales": [d.get("archivo_descargado") for d in docs_procesar if d.get("archivo_descargado")]
            },
            "detalle_sentencias": analisis.get("documentos", [])
        }


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
