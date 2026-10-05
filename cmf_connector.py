"""
Open Legal Chile — Conector Oficial Comisión para el Mercado Financiero (CMF)
Módulo para consultar, indexar y buscar Normas de Carácter General (NCG), Circulares,
Resoluciones y Oficios vinculantes para el mercado de valores, banca, seguros y Fintech en Chile.
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

BASE_URL = "https://www.cmfchile.cl/portal/normativa/624"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cmf_cache")
_TTL_CACHE_SEGUNDOS = 30 * 24 * 60 * 60      # normativa CMF: cambia lento, un mes
_TTL_SANCIONES_SEGUNDOS = 7 * 24 * 60 * 60   # sanciones: se publican al ritmo del día, una semana

# Las resoluciones sancionatorias viven en otra sección del sitio y vienen en una tabla con columnas
# N° | FECHA | MATERIA | ARCHIVO, una tabla por mercado: S seguros, V valores, B bancos.
BASE_SANCIONES = "https://www.cmfchile.cl/institucional/sanciones/sanciones_mercados_entidad.php"
MERCADOS_SANCIONES = {"S": "seguros", "V": "valores", "B": "bancos"}


def _texto_plano(trozo: str) -> str:
    """HTML -> texto: sin etiquetas, sin entidades (&Oacute;), sin espacios repetidos."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", trozo or ""))).strip()


def _aviso(titulo: str, mensaje: str) -> Dict[str, Any]:
    """Un vacío se explica: una lista vacía y muda se lee como «no existe», que es otra cosa."""
    return {"tipo": "aviso", "titulo": titulo, "mensaje": mensaje}


def _coincide(texto: str, consulta: str) -> bool:
    """Coincidencia por palabra completa, no por trozo («banco» no debe encontrar «bancario»)."""
    consulta = (consulta or "").strip()
    if not consulta:
        return False
    patron = r"\b" + r"\s+".join(re.escape(p) for p in consulta.split()) + r"\b"
    return re.search(patron, texto, re.IGNORECASE) is not None


def _parsear_sanciones_cmf(page_html: str) -> List[Dict[str, Any]]:
    """Extrae N°, fecha, MATERIA y archivo de cada fila de la tabla de sanciones de la CMF."""
    sanciones: List[Dict[str, Any]] = []
    for fila in re.findall(r"<tr[^>]*>(.*?)</tr>", page_html, re.IGNORECASE | re.DOTALL):
        celdas = re.findall(r"<td[^>]*>(.*?)</td>", fila, re.IGNORECASE | re.DOTALL)
        if len(celdas) < 3:
            continue  # la fila de encabezado usa <th>, no <td>
        numero = _texto_plano(celdas[0])
        fecha = _texto_plano(celdas[1])
        materia = _texto_plano(celdas[2])
        if not materia:
            continue
        url = ""
        for celda in celdas[3:]:
            # El enlace de descarga va SIN comillas en la página real («href=/sitio/aplic/serdoc/…»),
            # así que se acepta con o sin ellas y se busca en todas las celdas restantes.
            m_href = re.search(r'href=["\']?([^"\'\s>]+)', celda, re.IGNORECASE)
            if m_href:
                href = m_href.group(1)
                url = href if href.startswith("http") else \
                    "https://www.cmfchile.cl" + (href if href.startswith("/") else f"/{href}")
                break
        sanciones.append({
            "tipo": "Resolución Sancionatoria CMF",
            "numero": numero,
            "fecha": fecha,
            "materia": materia,
            "titulo": materia,  # compatibilidad con quien ya leía 'titulo'
            "url": url,
        })
    return sanciones


class CMFClient:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def get_index_normas(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Descarga e indexa el listado de Resoluciones, NCG y Circulares de la CMF."""
        cache_file = self._get_cache_path("index_normativa")
        data = leer_json_si_se_puede(cache_file) if use_cache else None
        if data is not None and cache_fresco(cache_file, _TTL_CACHE_SEGUNDOS):
            return data

        url = f"{BASE_URL}/w4-propertyvalue-49322.html"
        headers = {'User-Agent': 'OpenLegalChile/1.0 (Derecho Financiero Chile)'}
        req = urllib.request.Request(url, headers=headers)

        try:
            with safe_urlopen(req, timeout=30) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception:
            if data:
                return data  # copia vencida: mejor el índice viejo que ningún índice
            raise

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

    def get_sanciones(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Indexa las resoluciones sancionatorias que la CMF publica por mercado.

        La dirección que usaba este método (`/portal/prensa/604/w3-propertyvalue-24017.html`) devuelve
        404 desde que el sitio se reorganizó: llevaba tiempo devolviendo una lista vacía en silencio,
        que se lee como «la CMF no ha sancionado a nadie», y eso es falso. Ahora se leen las tablas
        vigentes —N° | FECHA | MATERIA | ARCHIVO— de los tres mercados: seguros, valores y bancos.
        """
        cache_file = self._get_cache_path("sanciones_cmf_v2")  # v2: la caché anterior estaba vacía
        data = leer_json_si_se_puede(cache_file) if use_cache else None
        if data is not None and cache_fresco(cache_file, _TTL_SANCIONES_SEGUNDOS):
            return data

        headers = {'User-Agent': 'OpenLegalChile/1.0 (Derecho Financiero Chile)'}
        sanciones: List[Dict[str, Any]] = []
        vistos = set()
        fallos: List[str] = []

        for mercado, nombre in MERCADOS_SANCIONES.items():
            url = f"{BASE_SANCIONES}?entidad=ALL&mercado={mercado}"
            try:
                req = urllib.request.Request(url, headers=headers)
                with safe_urlopen(req, timeout=45) as resp:
                    pagina = resp.read().decode("utf-8", errors="ignore")
            except Exception as e:
                fallos.append(f"mercado {nombre}: {e}")
                continue

            for s in _parsear_sanciones_cmf(pagina):
                clave = (s["numero"], s["fecha"], s["materia"])
                if clave in vistos:
                    continue
                vistos.add(clave)
                s["mercado"] = nombre
                sanciones.append(s)

        if sanciones:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(sanciones, f, ensure_ascii=False, indent=2)
            return sanciones

        if data:
            return data  # copia vencida: mejor la lista vieja que ningún listado

        detalle = "; ".join(fallos) if fallos else "las tablas respondieron pero sin filas reconocibles"
        return [_aviso(
            "No se pudieron cargar las resoluciones sancionatorias de la CMF",
            f"Ninguno de los tres mercados entregó sanciones ({detalle}). Esto NO significa que la "
            "CMF no haya sancionado: revisa la dirección del listado en el sitio del Servicio.",
        )]

    def search_sanciones(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Busca en el registro de sanciones de la CMF por número, entidad o materia."""
        sanciones = self.get_sanciones()
        if sanciones and isinstance(sanciones[0], dict) and sanciones[0].get("tipo") == "aviso":
            return sanciones

        q_lower = query.lower().strip()
        matches = [
            s for s in sanciones
            if _coincide(f"{s.get('materia', '')} {s.get('numero', '')}", q_lower)
        ][:limit]

        if matches:
            return matches

        return [_aviso(
            f"Sin sanciones de la CMF para «{query}»",
            f"Se buscó en el número y la materia de las {len(sanciones)} resoluciones sancionatorias "
            "indexadas (seguros, valores y bancos).",
        )]

    def descargar_documento_cmf(self, doc_url: str, identificador: str = "doc") -> Optional[str]:
        """Descarga el PDF oficial de una norma o sanción de la CMF."""
        if not doc_url:
            return None
        clean_id = re.sub(r'[^0-9]+', '_', str(identificador)).strip('_') or "doc"
        dest_folder = pathlib.Path(self.cache_dir) / "descargas_pdf"
        dest_folder.mkdir(parents=True, exist_ok=True)
        target_path = dest_folder / f"cmf_{clean_id}.pdf"

        if target_path.exists() and target_path.stat().st_size > 1000:
            return str(target_path)

        try:
            req = urllib.request.Request(doc_url, headers={'User-Agent': 'OpenLegalChile/1.0 (Derecho Financiero Chile)'})
            with safe_urlopen(req, timeout=30) as resp:
                pdf_bytes = resp.read()
            if len(pdf_bytes) > 1000:
                target_path.write_bytes(pdf_bytes)
                return str(target_path)
        except Exception:
            pass
        return None

    def get_normativa_integral(self, numero_o_titulo: str, descargar_formato: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene una norma o sanción CMF con texto integral y metadatos."""
        q = str(numero_o_titulo).strip()
        normas = self.search_normativa(q)
        match_item = None
        for n in normas:
            if isinstance(n, dict) and n.get("tipo") != "aviso":
                if q.lower() in n.get("titulo", "").lower() or _coincide(n.get("titulo", ""), q):
                    match_item = n
                    break
        if not match_item and normas and isinstance(normas[0], dict) and normas[0].get("tipo") != "aviso":
            match_item = normas[0]

        if not match_item:
            sanciones = self.search_sanciones(q)
            for s in sanciones:
                if isinstance(s, dict) and s.get("tipo") != "aviso":
                    match_item = s
                    break

        if not match_item:
            return {"error": f"Norma o resolución CMF '{numero_o_titulo}' no encontrada."}

        pdf_url = match_item.get("pdfUrl") or match_item.get("url") or ""
        m_num = re.search(r'N[°ºo\.\s]*([0-9]+)', match_item.get("titulo", "") or match_item.get("numero", ""), re.IGNORECASE)
        identificador = m_num.group(1) if m_num else str(match_item.get("numero") or q)

        ruta_pdf = self.descargar_documento_cmf(pdf_url, identificador=identificador) if pdf_url else None
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

        tipo_acto = "NCG" if "ncg" in match_item.get("titulo", "").lower() else "Resolución"
        materia = match_item.get("materia") or match_item.get("titulo") or ""
        texto_final = texto_pdf if len(texto_pdf) > 80 else materia

        doc = {
            "organismo": "CMF",
            "tipo_acto": tipo_acto,
            "identificador": identificador,
            "numero": identificador,
            "fecha": match_item.get("fecha", ""),
            "materia": materia,
            "titulo": match_item.get("titulo", ""),
            "texto": texto_final,
            "texto_integral": texto_final,
            "link_oficial": pdf_url or match_item.get("url", ""),
            "fuentes_legales": ["DFL 3/1997", "Ley 18.045", "Ley 21.000"],
        }

        if descargar_formato and descargar_formato.lower() == "pdf" and ruta_pdf:
            doc["archivo_descargado"] = ruta_pdf
            doc["formato_descargado"] = "pdf"

        return doc

    def procesar_y_graficar_cmf(
        self,
        ids_o_docs: List[Any],
        tema_relevante: Optional[str] = None,
        convertir_a_md: bool = True,
        descargar_formato: Optional[str] = None
    ) -> Dict[str, Any]:
        """Pipeline unificado para normativa y sanciones de la CMF."""
        from resolucion_administrativa2md import convertir_lote_dictamenes
        from resoluciones_parser import ResolucionesParserEngine
        from legal_graphify import LegalGraphifyEngine

        docs_procesar = []
        for item in ids_o_docs:
            if isinstance(item, str):
                doc_obj = self.get_normativa_integral(item, descargar_formato=descargar_formato)
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
            "organismo": "CMF",
            "total_normas": len(docs_procesar),
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
            "detalle_normas": analisis.get("documentos", [])
        }


# ==============================================================================
# CLI DE CONSULTA RÁPIDA DE NORMATIVA CMF
# ==============================================================================
if __name__ == "__main__":
    import argparse
    try:
        if hasattr(sys.stdout, "reconfigure"):
            getattr(sys.stdout, "reconfigure")(encoding="utf-8")
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
        for pos, item in enumerate(res):
            print(f"\n[{pos+1}] {item.get('titulo')}")
            print(f"  🔗 Ficha: {item.get('url')}")
            print(f"  📄 PDF: {item.get('pdfUrl')}")
    elif args.ultimas or len(sys.argv) == 1:
        print("\n🏢 Consultando Catálogo de Normas y Resoluciones CMF...")
        normas_catalogo = client.get_index_normas()
        print(f"Total normas indexadas: {len(normas_catalogo)}")
        print("\nMuestra de normas recientes:")
        for item in normas_catalogo[:5]:
            print(f" - {item.get('titulo')} -> {item.get('pdfUrl')}")
