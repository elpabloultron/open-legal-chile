"""
Open Legal Chile — Conector Oficial Dirección del Trabajo (DT)
Módulo para consultar, indexar y buscar Dictámenes, Ordinarios y Doctrina Laboral vinculante
de la Dirección del Trabajo de Chile.
"""

import os
import sys
import re
import html
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
from config import safe_urlopen

BASE_URL = "https://www.dt.gob.cl/legislacion/1624"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "dt_cache")


def _texto_plano(trozo: str) -> str:
    """HTML -> texto: sin etiquetas, sin entidades, sin espacios repetidos."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", trozo or ""))).strip()


def _aviso(titulo: str, mensaje: str) -> Dict[str, Any]:
    """Un vacío se explica: una lista vacía y muda se lee como «no existe», que es otra cosa."""
    return {"tipo": "aviso", "titulo": titulo, "mensaje": mensaje}


def _coincide(texto: str, consulta: str) -> bool:
    """Coincidencia por palabra completa: buscar «acta» no debe encontrar «contacto»."""
    consulta = (consulta or "").strip()
    if not consulta:
        return False
    patron = r"\b" + r"\s+".join(re.escape(p) for p in consulta.split()) + r"\b"
    return re.search(patron, texto, re.IGNORECASE) is not None


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
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        url = f"{BASE_URL}/w3-propertyvalue-147182.html"
        headers = {'User-Agent': 'OpenLegalChile/1.0 (Derecho Laboral Chile)'}
        req = urllib.request.Request(url, headers=headers)

        try:
            with safe_urlopen(req, timeout=60) as resp:
                page_html = resp.read().decode("utf-8", errors="ignore")
            index_list = _parsear_indice_dt(page_html, BASE_URL)
        except Exception as e:
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

        with safe_urlopen(req, timeout=20) as resp:
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

        q = query.lower().strip()

        por_numero = [
            i for i in index
            if q == str(i.get("numero", "")).lower() or _coincide(i.get("numero", ""), q)
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
            i for i in index
            if _coincide(i.get("materia", ""), q) or _coincide(i.get("numero", ""), q)
        ]
        if por_tema:
            return por_tema[:limit]

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
