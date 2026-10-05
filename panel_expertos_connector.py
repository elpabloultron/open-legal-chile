"""
Open Legal Chile — Conector Oficial Panel de Expertos de la Ley Eléctrica
Módulo para consultar, indexar y buscar Dictámenes, Discrepancias, Audiencias y Documentos
vinculantes del Panel de Expertos de la Ley General de Servicios Eléctricos (DFL 4/2006).
"""

import os
import sys
import re
import json
import pathlib
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
from config import cache_fresco, leer_json_si_se_puede, safe_urlopen

BASE_URL = "https://discrepancias.panelexpertos.cl/api/v1"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "panel_expertos_cache")
_TTL_CACHE_SEGUNDOS = 30 * 24 * 60 * 60  # los dictámenes del Panel cambian lento: un mes


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

        copia = leer_json_si_se_puede(cache_file) if use_cache else None
        if copia is not None and cache_fresco(cache_file, _TTL_CACHE_SEGUNDOS):
            return copia

        url = f"{BASE_URL}/discrepancies?page={page}&size={size}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "OpenLegalChile/1.0 (Derecho Energetico Chile)",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )

        try:
            with safe_urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        except Exception:
            if copia is not None:
                try:
                    return {**copia, "copia_local_vencida": True}
                except TypeError:
                    return copia
            raise

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

    def descargar_dictamen_pdf(self, doc_url: str, numero: str = "doc") -> Optional[str]:
        """Descarga el PDF oficial de un dictamen o discrepancia del Panel de Expertos."""
        if not doc_url:
            return None
        clean_id = re.sub(r'[^0-9]+', '_', str(numero)).strip('_') or "doc"
        dest_folder = pathlib.Path(self.cache_dir) / "descargas_pdf"
        dest_folder.mkdir(parents=True, exist_ok=True)
        target_path = dest_folder / f"dictamen_panel_{clean_id}.pdf"

        if target_path.exists() and target_path.stat().st_size > 1000:
            return str(target_path)

        try:
            req = urllib.request.Request(doc_url, headers={'User-Agent': 'OpenLegalChile/1.0 (Derecho Energetico Chile)'})
            with safe_urlopen(req, timeout=30) as resp:
                pdf_bytes = resp.read()
            if len(pdf_bytes) > 1000:
                target_path.write_bytes(pdf_bytes)
                return str(target_path)
        except Exception:
            pass
        return None

    def get_dictamen_integral(self, numero_o_id: str, descargar_formato: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene un dictamen del Panel de Expertos con texto integral y metadatos."""
        q = str(numero_o_id).strip()
        matches = self.search_dictamenes(q, max_pages=2)
        match_item = None
        for m in matches:
            if q.lower() in m.get("numero", "").lower() or str(m.get("id")) == q:
                match_item = m
                break
        if not match_item and matches:
            match_item = matches[0]

        if not match_item:
            return {"error": f"Dictamen o discrepancia '{numero_o_id}' no encontrado en el Panel de Expertos."}

        docs_list = match_item.get("documentos", [])
        pdf_url = ""
        for d in docs_list:
            if d.get("url") and "dictamen" in d.get("titulo", "").lower():
                pdf_url = d.get("url")
                break
        if not pdf_url and docs_list:
            pdf_url = docs_list[0].get("url", "")

        identificador = match_item.get("numero", q)
        ruta_pdf = self.descargar_dictamen_pdf(pdf_url, numero=identificador) if pdf_url else None
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

        materia = match_item.get("materia", "")
        texto_final = texto_pdf if len(texto_pdf) > 80 else f"Discrepancia {identificador}: {materia}"

        doc = {
            "organismo": "PANEL",
            "tipo_acto": "Dictamen",
            "identificador": identificador,
            "numero": identificador,
            "fecha": match_item.get("fecha_inicio", ""),
            "materia": materia,
            "texto": texto_final,
            "texto_integral": texto_final,
            "link_oficial": pdf_url,
            "fuentes_legales": ["DFL 4/2006", "Ley 20.936"],
        }

        if descargar_formato and descargar_formato.lower() == "pdf" and ruta_pdf:
            doc["archivo_descargado"] = ruta_pdf
            doc["formato_descargado"] = "pdf"

        return doc

    def procesar_y_graficar_panel(
        self,
        ids_o_docs: List[Any],
        tema_relevante: Optional[str] = None,
        convertir_a_md: bool = True,
        descargar_formato: Optional[str] = None
    ) -> Dict[str, Any]:
        """Pipeline unificado para dictámenes del Panel de Expertos."""
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
            "organismo": "PANEL",
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
