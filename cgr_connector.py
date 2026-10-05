"""
Open Legal Chile — Conector Oficial Contraloría General de la República (CGR)
Módulo para consultar, indexar y buscar Jurisprudencia Administrativa, Dictámenes,
Instructivos y Auditorías vinculantes de la Contraloría General de la República de Chile.
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

BASE_URL = "https://www.contraloria.cl/apibusca"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cgr_cache")
_TTL_CACHE_SEGUNDOS = 30 * 24 * 60 * 60  # la jurisprudencia de la CGR cambia lento: un mes


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

        clean_results = []
        for item in raw_items:
            src = item.get("_source", {})
            doc_id = src.get("numeric_doc_id") or src.get("doc_id") or src.get("número") or src.get("numero") or item.get("_id")
            fecha = src.get("fecha_documento") or src.get("fecha") or ""
            nombre = src.get("nombre") or src.get("title") or src.get("titulo") or ""
            materia = src.get("materia") or src.get("resena") or src.get("descriptores") or nombre or ""
            objetivo = src.get("objetivo") or ""
            conclusiones = src.get("conclusiones") or ""
            organismo = src.get("organismo") or src.get("organismos_destinatarios") or src.get("servicio_") or ""

            # Extracción limpia del texto completo desde _source["documento"]
            raw_doc_html = src.get("documento") or src.get("documento_raw") or ""
            clean_doc_text = ""
            if raw_doc_html:
                clean_doc_text = re.sub(r"<br\s*/?>", "\n", raw_doc_html)
                clean_doc_text = re.sub(r"<[^>]+>", " ", clean_doc_text)
                clean_doc_text = html.unescape(clean_doc_text)
                clean_doc_text = re.sub(r"[ \t]+", " ", clean_doc_text)
                clean_doc_text = re.sub(r"\n{3,}", "\n\n", clean_doc_text).strip()

            texto = clean_doc_text or src.get("texto_completo") or src.get("texto") or src.get("resumen") or conclusiones or objetivo or materia or ""

            # Resolución del enlace al PDF oficial firmado
            pdf_url = src.get("pdf") or ""
            if not pdf_url and doc_id and source == "dictamenes":
                year_2d = str(src.get("year_doc_id") or (fecha[:4] if len(fecha) >= 4 else "24"))[-2:]
                pdf_url = f"https://www.contraloria.cl/pdfbuscador/dictamenes/{doc_id}N{year_2d}/pdf"
            elif pdf_url and not pdf_url.startswith("http"):
                pdf_url = f"https://www.contraloria.cl{pdf_url}"

            clean_results.append({
                "docId": str(doc_id),
                "organismo": "CGR",
                "tipo_acto": "Dictamen" if source == "dictamenes" else ("Auditoría" if source == "auditoria" else "Instructivo"),
                "nombre": nombre.strip() if isinstance(nombre, str) else "",
                "fecha": fecha[:10] if len(fecha) >= 10 else fecha,
                "materia": materia.strip() if isinstance(materia, str) else "",
                "objetivo": objetivo.strip() if isinstance(objetivo, str) else "",
                "conclusiones": conclusiones.strip() if isinstance(conclusiones, str) else "",
                "organismo_destinatario": organismo if isinstance(organismo, str) else "",
                "texto": texto.strip() if isinstance(texto, str) else "",
                "texto_integral": texto.strip() if isinstance(texto, str) else "",
                "pdfUrl": pdf_url,
                "link_oficial": pdf_url or f"https://www.contraloria.cl/portal/dictamenes/{doc_id}"
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

    def descargar_pdf_oficial(self, doc_id: str, year: str = "") -> Optional[str]:
        """Descarga el PDF oficial firmado del dictamen desde el servidor de la Contraloría."""
        clean_id = str(doc_id).strip()
        y_2d = year[-2:] if year else "24"
        if "N" in clean_id:
            codigo_pdf = clean_id
        else:
            codigo_pdf = f"{clean_id}N{y_2d}"

        dest_folder = pathlib.Path(self.cache_dir) / "descargas_pdf"
        dest_folder.mkdir(parents=True, exist_ok=True)
        target_path = dest_folder / f"dictamen_cgr_{clean_id}.pdf"

        if target_path.exists() and target_path.stat().st_size > 1000:
            return str(target_path)

        url = f"https://www.contraloria.cl/pdfbuscador/dictamenes/{codigo_pdf}/pdf"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "OpenLegalChile/1.0 (Derecho Administrativo Chile)"})
            with safe_urlopen(req, timeout=30) as resp:
                pdf_bytes = resp.read()
            if len(pdf_bytes) > 1000:
                target_path.write_bytes(pdf_bytes)
                return str(target_path)
        except Exception:
            pass
        return None

    def get_dictamen_integral(self, doc_id: str, descargar_formato: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene el texto completo, metadatos y PDF oficial de un dictamen específico."""
        res = self.search_jurisprudencia(doc_id, source="dictamenes", exact=False)
        doc = None
        if res.get("resultados"):
            doc = res["resultados"][0]

        if not doc:
            return {"error": f"Dictamen {doc_id} no encontrado en la base de la CGR."}

        if descargar_formato and descargar_formato.lower() == "pdf":
            ruta_pdf = self.descargar_pdf_oficial(doc.get("docId", ""), year=doc.get("fecha", "")[:4])
            if ruta_pdf:
                doc["archivo_descargado"] = ruta_pdf
                doc["formato_descargado"] = "pdf"

        return doc

    def get_dictamen(self, doc_id: str) -> Dict[str, Any]:
        """Obtiene el texto de un dictamen (mantiene compatibilidad hacia atrás)."""
        return self.get_dictamen_integral(doc_id)

    def get_dictamenes_lote(self, doc_ids: List[str], descargar_formato: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene una lista de dictámenes en lote."""
        docs = []
        for did in doc_ids:
            docs.append(self.get_dictamen_integral(did, descargar_formato=descargar_formato))
        return docs

    def procesar_y_graficar_dictamenes(
        self,
        ids_o_docs: List[Any],
        tema_relevante: Optional[str] = None,
        convertir_a_md: bool = True,
        descargar_formato: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pipeline unificado para dictámenes de Contraloría:
        1. Resuelve documentos (busca texto íntegro).
        2. Convierte a Markdown Canónico (dictamen2md).
        3. Ingesta en LegalGraphify.
        4. Desglosa y rankea consideraciones con ResolucionesParserEngine.
        """
        from resolucion_administrativa2md import convertir_lote_dictamenes
        from resoluciones_parser import ResolucionesParserEngine
        from legal_graphify import LegalGraphifyEngine

        docs_procesar = []
        for item in ids_o_docs:
            if isinstance(item, str):
                doc_obj = self.get_dictamen_integral(item, descargar_formato=descargar_formato)
                docs_procesar.append(doc_obj)
            elif isinstance(item, dict):
                docs_procesar.append(item)

        # Conversión a Markdown Canónico
        rutas_md = []
        if convertir_a_md:
            try:
                rutas_md = [str(p) for p in convertir_lote_dictamenes(docs_procesar)]
                for i, r_path in enumerate(rutas_md):
                    if i < len(docs_procesar):
                        docs_procesar[i]["ruta_md"] = r_path
            except Exception:
                pass

        # Ingesta en LegalGraphify
        info_grafo = {}
        try:
            graph_engine = LegalGraphifyEngine()
            insumos = rutas_md if rutas_md else docs_procesar
            info_grafo = graph_engine.ingerir_lote_dictamenes(insumos, guardar_disco=False)
        except Exception as e:
            info_grafo = {"error": f"Error integrando con LegalGraphify: {str(e)}"}

        # Análisis y citación canónica
        parser_engine = ResolucionesParserEngine()
        analisis = parser_engine.analizar_lote_resoluciones(docs_procesar, tema_relevante=tema_relevante)

        return {
            "organismo": "CGR",
            "total_dictamenes": len(docs_procesar),
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
            "detalle_dictamenes": analisis.get("documentos", [])
        }

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
