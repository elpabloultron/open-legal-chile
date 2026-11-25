"""
Open Legal Chile — Conector Oficial Dirección del Trabajo (DT)
Módulo para consultar, indexar y buscar Dictámenes, Ordinarios y Doctrina Laboral vinculante
de la Dirección del Trabajo de Chile.
"""

import os
import sys
import re
import json
import functools
import pathlib
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional, Pattern, Tuple
from config import aviso_conector as _aviso, cache_fresco, leer_json_si_se_puede, safe_urlopen, sin_tildes as _sin_tildes, texto_plano as _texto_plano

BASE_URL = "https://www.dt.gob.cl/legislacion/1624"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "dt_cache")
_TTL_CACHE_SEGUNDOS = 7 * 24 * 60 * 60  # la DT publica a diario, pero el listado cambia poco
_FilaPreparadaDT = Tuple[Dict[str, Any], str, str, str, str, str, str]
# Caché RAM por archivo absoluto validada por (mtime_ns, size): evita re-parsear 4,2 MB JSON
# y re-normalizar los 7 938 ordinarios en cada búsqueda.
_INDEX_RAM_DT: Dict[str, Tuple[int, int, List[Dict[str, Any]], List[_FilaPreparadaDT]]] = {}


@functools.lru_cache(maxsize=512)
def _patrones_coincidencia(consulta: str) -> Optional[Tuple[Pattern[str], Pattern[str]]]:
    """Compila una vez el par de regex (exacto y sin tildes) para una consulta o alias."""
    limpia = (consulta or "").strip()
    if not limpia:
        return None
    patron = r"\b" + r"\s+".join(re.escape(p) for p in limpia.split()) + r"\b"
    patron_st = r"\b" + r"\s+".join(re.escape(p) for p in _sin_tildes(limpia).split()) + r"\b"
    return re.compile(patron, re.IGNORECASE), re.compile(patron_st, re.IGNORECASE)


def _preparar_filas_dt(index: List[Dict[str, Any]]) -> List[_FilaPreparadaDT]:
    """Pre-normaliza los campos buscables una sola vez sin mutar los dicts del índice."""
    filas: List[_FilaPreparadaDT] = []
    for item in index:
        if not isinstance(item, dict):
            continue
        num_raw = str(item.get("numero") or "")
        mat_raw = str(item.get("materia") or "")
        num_st = _sin_tildes(num_raw)
        mat_st = _sin_tildes(mat_raw)
        filas.append((
            item,
            num_raw,
            num_raw.lower(),
            num_st,
            mat_raw,
            mat_st,
            f"{num_st} {mat_st}".lower(),
        ))
    return filas


def _coincide_pre(patrones: Optional[Tuple[Pattern[str], Pattern[str]]], raw: str, norm_st: str) -> bool:
    if patrones is None:
        return False
    p_raw, p_st = patrones
    return p_raw.search(raw) is not None or p_st.search(norm_st) is not None


def _coincide(texto: str, consulta: str) -> bool:
    """Coincidencia por palabra completa: buscar «acta» no debe encontrar «contacto»."""
    patrones = _patrones_coincidencia((consulta or "").strip())
    if patrones is None:
        return False
    raw = texto or ""
    p_raw, p_st = patrones
    if p_raw.search(raw) is not None:
        return True
    return p_st.search(_sin_tildes(raw)) is not None


ALIAS_MATERIAS_DT: Dict[str, List[str]] = {
    "ley karin": ["21.643", "acoso laboral", "acoso sexual", "violencia en el trabajo"],
    "karin": ["21.643", "acoso laboral", "acoso sexual", "violencia en el trabajo"],
    "acoso laboral": ["acoso laboral", "21.643", "acoso"],
    "40 horas": ["21.561", "reducción de la jornada", "jornada de 40 horas", "cuarenta horas"],
    "cuarenta horas": ["21.561", "reducción de la jornada", "jornada de 40 horas"],
    "jornada 40 horas": ["21.561", "reducción de la jornada"],
    "gratificacion": ["gratificación", "artículo 47", "artículo 50", "gratificacion legal"],
    "gratificación": ["gratificación", "artículo 47", "artículo 50", "gratificacion legal"],
    "finiquito": ["finiquito", "terminación del contrato", "161", "160", "reserva de derechos"],
    "finiquitos": ["finiquito", "terminación del contrato", "161", "160"],
    "tutela laboral": ["tutela laboral", "derechos fundamentales", "vulneración de derechos"],
    "tutela": ["tutela laboral", "derechos fundamentales"],
    "subcontratacion": ["subcontratación", "183-a", "empresa principal", "contratista"],
    "subcontratación": ["subcontratación", "183-a", "empresa principal", "contratista"],
    "sala cuna": ["sala cuna", "artículo 203", "bono compensatorio"],
    "teletrabajo": ["teletrabajo", "trabajo a distancia", "152 quater"],
    "trabajo a distancia": ["teletrabajo", "trabajo a distancia", "152 quater"],
    "licencia medica": ["licencia médica", "subsidio por incapacidad", "incapacidad laboral"],
    "licencia médica": ["licencia médica", "subsidio por incapacidad", "incapacidad laboral"],
    "necesidades de la empresa": ["necesidades de la empresa", "161", "artículo 161"],
    "despido injustificado": ["despido injustificado", "168", "artículo 161"],
    "afc": ["afc", "seguro de cesantía", "19.728", "cesantía", "aporte del empleador"],
    "descuento afc": ["afc", "seguro de cesantía", "19.728", "cesantía", "imputación", "descuento"],
    "seguro de cesantia": ["seguro de cesantía", "afc", "19.728", "cesantía"],
    "seguro de cesantía": ["seguro de cesantía", "afc", "19.728", "cesantía"],
}


_STOPWORDS_DT = frozenset({
    "el", "la", "los", "las", "de", "del", "en", "y", "o", "por", "para", "con", "sin",
    "un", "una", "unos", "unas", "al", "se", "su", "sus", "que", "es", "son", "como",
})


def _tokens_significativos_dt(consulta: str) -> List[str]:
    norm = _sin_tildes((consulta or "").lower())
    return [t for t in re.findall(r"[a-z0-9]+", norm) if len(t) >= 3 and t not in _STOPWORDS_DT]


# Cada dictamen de la DT viene en un bloque «recuadro» con su número, su fecha, su MATERIA (el
# párrafo «abstract», que es el resumen oficial) y el enlace al texto completo. Antes se guardaba
# sólo el texto del enlace —«ORD.N°377»—, así que buscar por tema («despido», «jornada») devolvía
# siempre cero resultados aunque el índice tenga 4.880 dictámenes, y eso se leía como que la DT no
# tenía nada sobre el tema.
_PATRON_RECUADRO_DT = re.compile(r'<div class="recuadro">(.*?)</div>', re.IGNORECASE | re.DOTALL)
_PATRON_ENLACE_DT = re.compile(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
_PATRON_FECHA_DT = re.compile(r'<h6[^>]*class="[^"]*fecha[^"]*"[^>]*>(.*?)</h6>', re.IGNORECASE | re.DOTALL)
_PATRON_RESUMEN_DT = re.compile(r'<p[^>]*class="[^"]*abstract[^"]*"[^>]*>(.*?)</p>', re.IGNORECASE | re.DOTALL)


def _parsear_indice_dt(page_html: str, base_url: str) -> List[Dict[str, Any]]:
    """Extrae número, fecha, MATERIA (resumen oficial) y enlace de cada dictamen del índice."""
    items: List[Dict[str, Any]] = []
    for bloque in _PATRON_RECUADRO_DT.findall(page_html):
        enlace = _PATRON_ENLACE_DT.search(bloque)
        if not enlace:
            continue
        numero = _texto_plano(enlace.group(2))
        if not numero:
            continue
        href = enlace.group(1)
        m_id = re.search(r"article-([0-9]+)", href)
        m_fecha = _PATRON_FECHA_DT.search(bloque)
        m_resumen = _PATRON_RESUMEN_DT.search(bloque)
        items.append({
            "numero": numero,
            "articleId": m_id.group(1) if m_id else "",
            "fecha": _texto_plano(m_fecha.group(1)) if m_fecha else "",
            "materia": _texto_plano(m_resumen.group(1)) if m_resumen else "",
            "link": href if href.startswith("http") else f"{base_url}/{href.lstrip('/')}",
        })
    return items


class DTClient:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def get_index_ordinarios(self, use_cache: bool = True) -> List[Dict[str, str]]:
        """Descarga e indexa el listado maestro de Ordinarios y Dictámenes de la DT."""
        cache_file = self._get_cache_path("index_ordinarios_v2")  # v2: incluye la MATERIA de cada uno
        abs_cache = os.path.abspath(cache_file)
        fresco = use_cache and cache_fresco(cache_file, _TTL_CACHE_SEGUNDOS)
        data: Any = None
        if use_cache:
            try:
                st = os.stat(abs_cache)
                cac = _INDEX_RAM_DT.get(abs_cache)
                if cac is not None and cac[0] == st.st_mtime_ns and cac[1] == st.st_size:
                    if fresco:
                        return cac[2]
                    data = cac[2]
                else:
                    leido = leer_json_si_se_puede(cache_file)
                    if isinstance(leido, list):
                        if len(_INDEX_RAM_DT) >= 8:
                            _INDEX_RAM_DT.clear()
                        _INDEX_RAM_DT[abs_cache] = (int(st.st_mtime_ns), int(st.st_size), leido, _preparar_filas_dt(leido))
                        data = leido
                        if fresco:
                            return leido
            except OSError:
                data = None

        if data is not None and fresco:
            return data

        url = f"{BASE_URL}/w3-propertyvalue-147182.html"
        headers = {'User-Agent': 'OpenLegalChile/1.0 (Derecho Laboral Chile)'}
        req = urllib.request.Request(url, headers=headers)

        try:
            with safe_urlopen(req, timeout=60) as resp:
                page_html = resp.read().decode("utf-8", errors="ignore")
            index_list = _parsear_indice_dt(page_html, BASE_URL)
        except Exception as e:
            if data:
                return data  # copia vencida: mejor el índice viejo que ningún índice
            return [_aviso(
                "No se pudo cargar el índice de dictámenes y ordinarios de la DT",
                f"El sitio de la DT no respondió ({e}). Esto NO significa que no existan dictámenes "
                "de ese tipo.",
            )]

        if not index_list:
            return [_aviso(
                "El índice de dictámenes de la DT no entregó ningún ítem",
                "La página respondió pero no se reconoció ningún bloque de dictamen: probablemente "
                "cambió su estructura y hay que actualizar el parser.",
            )]

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(index_list, f, ensure_ascii=False, indent=2)
        try:
            st = os.stat(abs_cache)
            if len(_INDEX_RAM_DT) >= 8:
                _INDEX_RAM_DT.clear()
            _INDEX_RAM_DT[abs_cache] = (int(st.st_mtime_ns), int(st.st_size), index_list, _preparar_filas_dt(index_list))
        except OSError:
            pass

        return index_list

    def descargar_pdf_oficial(self, article_id_or_url: str, pdf_url: Optional[str] = None) -> Optional[str]:
        """Descarga el PDF oficial firmado del dictamen u ordinario de la DT."""
        from forensic_ocr import descargar_pdf_cacheado

        art_id = str(article_id_or_url).strip()
        m = re.search(r'article-([0-9]+)', art_id)
        if m:
            clean_id = m.group(1)
        elif art_id.isdigit():
            clean_id = art_id
        else:
            clean_id = re.sub(r'[^0-9]+', '', art_id) or "doc"

        target_path = pathlib.Path(self.cache_dir) / "descargas_pdf" / f"dictamen_dt_{clean_id}.pdf"
        url = pdf_url or f"{BASE_URL}/articles-{clean_id}_recurso_pdf.pdf"
        return descargar_pdf_cacheado(url, target_path, user_agent="OpenLegalChile/1.0 (Derecho Laboral Chile)")

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
        data = leer_json_si_se_puede(cache_file) if use_cache else None
        if data is not None and cache_fresco(cache_file, _TTL_CACHE_SEGUNDOS) and data.get("texto_integral"):
            return data

        headers = {'User-Agent': 'OpenLegalChile/1.0 (Derecho Laboral Chile)'}
        req = urllib.request.Request(url, headers=headers)

        html = ""
        try:
            with safe_urlopen(req, timeout=20) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception:
            if data is not None:
                return {**data, "copia_local_vencida": True}
            raise

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

        # Detección de PDF oficial adjunto
        pdf_match = re.search(r'href=["\']([^"\']*articles-[^"\']*_recurso[^"\']*\.pdf)["\']', html, re.IGNORECASE)
        pdf_url = ""
        if pdf_match:
            raw_pdf = pdf_match.group(1)
            pdf_url = raw_pdf if raw_pdf.startswith("http") else f"{BASE_URL}/{raw_pdf.lstrip('/')}"
        elif article_id.isdigit():
            pdf_url = f"{BASE_URL}/articles-{article_id}_recurso_pdf.pdf"

        # Extraer texto profundo del PDF si el HTML sólo trae resumen
        from forensic_ocr import extraer_texto_pdf_con_ocr

        ruta_pdf_descargado = self.descargar_pdf_oficial(article_id, pdf_url=pdf_url) if pdf_url else None
        texto_pdf = extraer_texto_pdf_con_ocr(ruta_pdf_descargado)

        texto_integral = texto_pdf if len(texto_pdf) > 80 else "\n\n".join(clean_paragraphs)

        doc_data = {
            "articleId": article_id,
            "titulo": title,
            "url": url,
            "pdfUrl": pdf_url,
            "materias": materias,
            "doctrina": doctrina,
            "parrafos": clean_paragraphs,
            "texto": texto_integral,
            "texto_integral": texto_integral,
            "archivo_descargado": ruta_pdf_descargado
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(doc_data, f, ensure_ascii=False, indent=2)

        return doc_data

    def get_dictamen_integral(self, numero_o_id: str, descargar_formato: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene el texto completo, metadatos y PDF oficial de un dictamen u ordinario DT."""
        art_id = str(numero_o_id).strip()
        doc_meta = None

        if not art_id.isdigit():
            idx = self.get_index_ordinarios()
            q = art_id.lower().strip()
            q_num = re.sub(r'^(?:ord\.?\s*(?:n[°º]?)?\s*|dictamen\s*(?:n[°º]?)?\s*)', '', q).strip()
            for item in idx:
                if isinstance(item, dict):
                    num_item = str(item.get("numero", "")).lower().strip()
                    num_item_clean = re.sub(r'^(?:ord\.?\s*(?:n[°º]?)?\s*|dictamen\s*(?:n[°º]?)?\s*)', '', num_item).strip()
                    if q == num_item or q_num == num_item_clean or _coincide(num_item, q):
                        art_id = item.get("articleId", "")
                        doc_meta = item
                        break

        if not art_id:
            return {"error": f"Dictamen u ordinario '{numero_o_id}' no encontrado en el índice de la DT."}

        raw_doc = self.get_dictamen_content(art_id)
        if not raw_doc or not isinstance(raw_doc, dict):
            return {"error": f"No se pudo obtener el contenido del dictamen ID {art_id}."}

        identificador = doc_meta.get("numero") if doc_meta else (raw_doc.get("titulo") or f"ORD. N° {art_id}")
        fecha = doc_meta.get("fecha", "") if doc_meta else ""
        materia = (doc_meta.get("materia", "") if doc_meta and doc_meta.get("materia") else raw_doc.get("materias", "")).strip()

        doc = {
            "organismo": "DT",
            "tipo_acto": "Dictamen",
            "identificador": identificador,
            "numero": identificador,
            "fecha": fecha,
            "materia": materia,
            "doctrina": raw_doc.get("doctrina", ""),
            "texto": raw_doc.get("texto_integral") or raw_doc.get("texto") or raw_doc.get("doctrina") or materia,
            "texto_integral": raw_doc.get("texto_integral") or raw_doc.get("texto") or raw_doc.get("doctrina") or materia,
            "link_oficial": raw_doc.get("url", ""),
            "url": raw_doc.get("url", ""),
            "pdfUrl": raw_doc.get("pdfUrl", ""),
            "articleId": art_id
        }

        if descargar_formato and descargar_formato.lower() == "pdf":
            ruta_pdf = self.descargar_pdf_oficial(art_id, pdf_url=raw_doc.get("pdfUrl"))
            if ruta_pdf:
                doc["archivo_descargado"] = ruta_pdf
                doc["formato_descargado"] = "pdf"

        return doc

    def get_dictamenes_lote(self, numeros_o_ids: List[str], descargar_formato: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene una lista de dictámenes DT en lote."""
        docs = []
        for nid in numeros_o_ids:
            docs.append(self.get_dictamen_integral(nid, descargar_formato=descargar_formato))
        return docs

    def procesar_y_graficar_dictamenes(
        self,
        ids_o_docs: List[Any],
        tema_relevante: Optional[str] = None,
        convertir_a_md: bool = True,
        descargar_formato: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Pipeline unificado para dictámenes de la Dirección del Trabajo."""
        from resoluciones_parser import procesar_y_graficar_lote

        return procesar_y_graficar_lote(
            ids_o_docs,
            lambda item: self.get_dictamen_integral(item, descargar_formato=descargar_formato),
            organismo="DT",
            clave_total="total_dictamenes",
            clave_detalle="detalle_dictamenes",
            tema_relevante=tema_relevante,
            convertir_a_md=convertir_a_md,
        )

    def search_dictamenes(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca dictámenes y ordinarios de la DT por número o por tema.

        La búsqueda por tema se hace sobre la MATERIA —el resumen que publica la propia DT— y no
        sólo sobre el número: antes se comparaba únicamente contra «ORD.N°344», de modo que consultas
        como «despido» o «jornada» devolvían siempre cero aunque el índice tenga 4.880 dictámenes, y
        eso se leía como que la DT no tenía nada sobre el tema.

        Si la consulta coincide con números, se descarga el texto completo de esos dictámenes. Si es
        una búsqueda temática, se devuelven las coincidencias con su resumen y su fecha —descargar
        diez textos completos por consulta haría la búsqueda inútilmente lenta—; el texto completo de
        cualquiera de ellas se obtiene con get_dictamen_content(articleId).
        """
        index = self.get_index_ordinarios()
        if index and isinstance(index[0], dict) and index[0].get("tipo") == "aviso":
            return index

        abs_cache = os.path.abspath(self._get_cache_path("index_ordinarios_v2"))
        cac = _INDEX_RAM_DT.get(abs_cache)
        filas = cac[3] if (cac is not None and cac[2] is index) else _preparar_filas_dt(index)

        q = query.lower().strip()
        pat_q = _patrones_coincidencia(q)

        por_numero = [
            item for item, num_raw, num_low, num_st, _, _, _ in filas
            if q == num_low or _coincide_pre(pat_q, num_raw, num_st)
        ]
        if por_numero:
            results: List[Dict[str, Any]] = []
            for m in por_numero[:limit]:
                art_id = m.get("articleId")
                if art_id:
                    try:
                        results.append(self.get_dictamen_content(art_id))
                        continue
                    except Exception:
                        pass
                results.append({
                    "articleId": art_id,
                    "titulo": m.get("numero"),
                    "materia": m.get("materia", ""),
                    "fecha": m.get("fecha", ""),
                    "url": m.get("link"),
                })
            return results

        por_tema = [
            item for item, num_raw, _, num_st, mat_raw, mat_st, _ in filas
            if _coincide_pre(pat_q, mat_raw, mat_st) or _coincide_pre(pat_q, num_raw, num_st)
        ]
        if por_tema:
            return por_tema[:limit]

        # Coincidencia multi-palabra (todos los tokens significativos presentes en cualquier orden)
        tokens_q = _tokens_significativos_dt(q)
        coincidencias_parcial: List[tuple] = []
        if len(tokens_q) >= 2:
            coincidencias_all: List[Dict[str, Any]] = []
            patrones_tok = [re.compile(rf"\b{re.escape(tok)}") for tok in tokens_q]
            for item, _, _, _, _, _, combo_st in filas:
                hits = sum(1 for pat in patrones_tok if pat.search(combo_st) is not None)
                if hits == len(patrones_tok):
                    coincidencias_all.append(item)
                elif hits > 0:
                    coincidencias_parcial.append((hits, item))
            if coincidencias_all:
                return coincidencias_all[:limit]
            # Si hay tokens muy específicos (siglas o números como afc/161/21643), priorizar parciales con mayor score
            if coincidencias_parcial:
                coincidencias_parcial.sort(key=lambda x: x[0], reverse=True)
                # Intentar primero alias exactos antes de devolver parciales de 1 solo token genérico
                pass

        # Respaldo por auto-expansión de alias/sugerencias oficiales
        q_norm = _sin_tildes(q)
        terminos_respaldo: List[str] = []
        for alias_key, terminos in ALIAS_MATERIAS_DT.items():
            alias_key_norm = _sin_tildes(alias_key)
            if alias_key_norm in q_norm or q_norm in alias_key_norm or _coincide(q_norm, alias_key_norm):
                for t in terminos:
                    if t not in terminos_respaldo and _sin_tildes(t) != q_norm:
                        terminos_respaldo.append(t)

        if terminos_respaldo:
            resultados_alias: List[Dict[str, Any]] = []
            vistos: set = set()
            for termino in terminos_respaldo:
                pat_termino = _patrones_coincidencia(termino.strip())
                for item, num_raw, _, num_st, mat_raw, mat_st, _ in filas:
                    clave_item = item.get("articleId") or num_raw
                    if clave_item in vistos:
                        continue
                    if _coincide_pre(pat_termino, mat_raw, mat_st) or _coincide_pre(pat_termino, num_raw, num_st):
                        vistos.add(clave_item)
                        resultados_alias.append(item)
                        if len(resultados_alias) >= limit:
                            break
                if len(resultados_alias) >= limit:
                    break
            if resultados_alias:
                return resultados_alias[:limit]

        if len(tokens_q) >= 2 and coincidencias_parcial:
            return [it for _, it in coincidencias_parcial[:limit]]

        return [_aviso(
            f"Sin dictámenes de la DT para «{query}»",
            "Se buscó en el número, la fecha y la materia de los 4.880 dictámenes del índice. Si "
            "esperabas resultados, revisa el término: la materia es el resumen oficial que publica "
            "la DT, así que conviene probar con la palabra que usaría el Servicio.",
        )]


# ==============================================================================
# CLI DE CONSULTA RÁPIDA DE DICTÁMENES DT
# ==============================================================================
if __name__ == "__main__":
    import argparse
    try:
        if hasattr(sys.stdout, "reconfigure"):
            getattr(sys.stdout, "reconfigure")(encoding="utf-8")
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
                print(f"  📜 Doctrina: {str(item.get('doctrina'))[:250]}...")
            print(f"  🔗 Enlace: {item.get('url')}")
    elif args.ultimos or len(sys.argv) == 1:
        print("\n💼 Consultando Catálogo Maestro de Ordinarios de la DT...")
        idx = client.get_index_ordinarios()
        print(f"Total Ordinarios y Dictámenes indexados: {len(idx)}")
        print("\nMuestra de dictámenes recientes:")
        for item in idx[:5]:
            print(f" - {item.get('numero')} (ID: {item.get('articleId')}) -> {item.get('link')}")
