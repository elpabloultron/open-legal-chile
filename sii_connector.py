"""
Open Legal Chile — Conector Oficial Servicio de Impuestos Internos (SII)
Módulo para consultar, indexar y buscar Circulares, Resoluciones e Instrucciones Tributarias
vinculantes del Director del Servicio de Impuestos Internos de Chile.
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

BASE_URL = "https://www.sii.cl/normativa_legislacion"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "sii_cache")


def _texto_plano(trozo: str) -> str:
    """HTML -> texto: sin etiquetas, sin entidades (&Oacute;), sin espacios repetidos."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", trozo or ""))).strip()


def _aviso(titulo: str, mensaje: str) -> Dict[str, Any]:
    """Un vacío se explica: una lista vacía y muda se lee como «no existe», que es otra cosa."""
    return {"tipo": "aviso", "titulo": titulo, "mensaje": mensaje}


def _coincide(texto: str, consulta: str) -> bool:
    """Coincidencia por palabra completa, no por trozo.

    Buscar «IVA» con un `in` simple encuentra «administratIVA» y devuelve circulares que no tienen
    nada que ver. Se exige límite de palabra (y se respeta una consulta de varias palabras).
    """
    consulta = (consulta or "").strip()
    if not consulta:
        return False
    patron = r"\b" + r"\s+".join(re.escape(p) for p in consulta.split()) + r"\b"
    return re.search(patron, texto, re.IGNORECASE) is not None


# La MATERIA de cada circular va en el párrafo que sigue al enlace. El índice del SII la publica ahí
# («<h5><a href='circu35.pdf'>Circular N° 35 del 31 de Agosto del 2026</a></h5><p>Actualiza
# instrucciones sobre mecanismos de impugnación administrativa…</p>») y antes se descartaba: se
# guardaba sólo «Circular N° 35 del 31 de Agosto del 2026», de modo que cualquier búsqueda por tema
# (renta, IVA, timbre) devolvía siempre cero, y eso se leía como que el SII no tenía nada sobre eso.
_PATRON_ITEM_SII = re.compile(
    r'<a[^>]+href=["\'](?P<link>[^"\']+\.(?:pdf|html?))["\'][^>]*>(?P<titulo>.*?)</a>'
    r'(?:\s*</h[0-9]>)?'
    r'(?:\s*<p[^>]*>(?P<materia>.*?)</p>)?'
    r'(?:\s*<span[^>]*>\s*<i>\s*(?P<fuente>Fuente:[^<]*)</i>)?',
    re.IGNORECASE | re.DOTALL,
)


def _parsear_indice_sii(page_html: str, anio: int, carpeta: str, base_url: str) -> List[Dict[str, Any]]:
    """Extrae número, título, MATERIA y fuente de cada ítem de un índice del SII.

    El número lo completa quien llama, porque cada serie (circulares, resoluciones, oficios) lo
    escribe distinto en el título.
    """
    items: List[Dict[str, Any]] = []
    for m in _PATRON_ITEM_SII.finditer(page_html):
        titulo = _texto_plano(m.group("titulo"))
        if not titulo:
            continue
        link = m.group("link")
        items.append({
            "anio": anio,
            "numero": "",
            "titulo": titulo,
            "materia": _texto_plano(m.group("materia")),
            "fuente": _texto_plano(m.group("fuente")),
            "pdfUrl": link if link.startswith("http") else f"{base_url}/{carpeta}/{anio}/{link}",
        })
    return items


class SIIClient:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def get_circulares_por_anio(self, anio: int = 2026, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Descarga e indexa el listado oficial de Circulares del SII para un año específico."""
        cache_key = f"circulares_{anio}_v2"  # v2: incluye la MATERIA (la caché anterior no la tenía)
        cache_file = self._get_cache_path(cache_key)

        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        url = f"{BASE_URL}/circulares/{anio}/indcir{anio}.htm"
        headers = {'User-Agent': 'OpenLegalChile/1.0 (Derecho Tributario Chile)'}
        req = urllib.request.Request(url, headers=headers)

        circulares_list: List[Dict[str, Any]] = []
        try:
            with safe_urlopen(req, timeout=20) as resp:
                page_html = resp.read().decode("utf-8", errors="ignore")
                circulares_list = _parsear_indice_sii(page_html, anio, "circulares", BASE_URL)
                for c in circulares_list:
                    m_num = re.search(r"Circular\s*N[°ºo\.\s]*([0-9]+)", c["titulo"], re.IGNORECASE)
                    c["numero"] = m_num.group(1) if m_num else ""

                if circulares_list:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(circulares_list, f, ensure_ascii=False, indent=2)
                else:
                    # Un parseo vacío NO se cachea: dejaría el índice envenenado para siempre.
                    circulares_list = [_aviso(
                        f"El índice de circulares {anio} no entregó ningún ítem",
                        "La página del SII respondió, pero no se reconoció ningún ítem en ella: "
                        "probablemente cambió su estructura y hay que actualizar el parser.",
                    )]

        except Exception as e:
            circulares_list = [_aviso(
                f"No se pudo cargar el índice de circulares {anio}",
                f"El SII no respondió o la dirección del índice cambió ({e}). Esto NO significa que "
                "no existan circulares de ese año.",
            )]

        return circulares_list

    def get_resoluciones_por_anio(self, anio: int = 2026, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Descarga e indexa el listado oficial de Resoluciones Exentas del SII para un año específico."""
        cache_key = f"resoluciones_{anio}"
        cache_file = self._get_cache_path(cache_key)

        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        url = f"{BASE_URL}/resoluciones/{anio}/indres{anio}.htm"
        headers = {'User-Agent': 'OpenLegalChile/1.0 (Derecho Tributario Chile)'}
        req = urllib.request.Request(url, headers=headers)

        resoluciones_list: List[Dict[str, Any]] = []
        try:
            with safe_urlopen(req, timeout=20) as resp:
                page_html = resp.read().decode("utf-8", errors="ignore")
                resoluciones_list = _parsear_indice_sii(page_html, anio, "resoluciones", BASE_URL)
                for r in resoluciones_list:
                    r["tipo"] = "Resolución Exenta SII"
                    m_num = re.search(r"Res(?:oluci[oó]n)?\s*Ex(?:enta)?\s*N[°ºo\.\s]*([0-9]+)",
                                      r["titulo"], re.IGNORECASE)
                    r["numero"] = m_num.group(1) if m_num else ""

                if resoluciones_list:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(resoluciones_list, f, ensure_ascii=False, indent=2)
                else:
                    resoluciones_list = [_aviso(
                        f"El índice de resoluciones {anio} no entregó ningún ítem",
                        "La página respondió pero no se reconoció ningún ítem: probablemente cambió "
                        "su estructura y hay que actualizar el parser.",
                    )]

        except Exception as e:
            resoluciones_list = [_aviso(
                f"No se pudo cargar el índice de resoluciones exentas {anio}",
                f"La dirección que usa este conector ya no responde ({e}). Verificado el 18-09-2026: "
                f"{url} devuelve 404 en todos los años probados (2023 a 2026). Es la URL la que está "
                "obsoleta, no la ausencia de resoluciones: hay que actualizarla a la nueva ubicación "
                "del SII. Mientras tanto, el SII publica cada resolución también en su buscador "
                "oficial, o se puede consultar por número en el sitio del Servicio.",
            )]

        return resoluciones_list

    def get_oficios_por_anio(self, anio: int = 2026, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Descarga e indexa la jurisprudencia administrativa (Oficios Ordinarios) del Director del SII (Art. 26 CT)."""
        cache_key = f"oficios_{anio}"
        cache_file = self._get_cache_path(cache_key)

        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        url = f"{BASE_URL}/jurisprudencia/administrativa/{anio}/indjad{anio}.htm"
        headers = {'User-Agent': 'OpenLegalChile/1.0 (Derecho Tributario Chile)'}
        req = urllib.request.Request(url, headers=headers)

        oficios_list: List[Dict[str, Any]] = []
        try:
            with safe_urlopen(req, timeout=20) as resp:
                page_html = resp.read().decode("utf-8", errors="ignore")
                oficios_list = [
                    o for o in _parsear_indice_sii(page_html, anio, "jurisprudencia/administrativa", BASE_URL)
                    if len(o["titulo"]) >= 5 and "volver" not in o["titulo"].lower()
                ]
                for o in oficios_list:
                    o["tipo"] = "Oficio Ordinario (Jurisprudencia Administrativa)"
                    m_num = re.search(r"Oficio\s*N[°ºo\.\s]*([0-9]+)", o["titulo"], re.IGNORECASE)
                    o["numero"] = m_num.group(1) if m_num else ""
                    o["url"] = o.pop("pdfUrl")

                if oficios_list:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(oficios_list, f, ensure_ascii=False, indent=2)
                else:
                    oficios_list = [_aviso(
                        f"El índice de oficios {anio} no entregó ningún ítem",
                        "La página respondió pero no se reconoció ningún ítem: probablemente cambió "
                        "su estructura y hay que actualizar el parser.",
                    )]

        except Exception as e:
            oficios_list = [_aviso(
                f"No se pudo cargar el índice de oficios (jurisprudencia administrativa) {anio}",
                f"La dirección que usa este conector ya no responde ({e}). Verificado el 18-09-2026: "
                f"{url} devuelve 404 en todos los años probados (2024 a 2026). Es la URL la que está "
                "obsoleta, no la ausencia de oficios: hay que actualizarla a la nueva ubicación del "
                "SII. Mientras tanto, cada oficio se consulta en el buscador de jurisprudencia "
                "administrativa del Servicio.",
            )]

        return oficios_list

    def search_resoluciones_y_oficios(self, query: str, anios: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Busca resoluciones exentas y oficios del SII por número o término tributario.

        Busca en el título y en la MATERIA (el resumen que publica el SII), no sólo en el número.
        Si las fuentes no responden, devuelve el aviso correspondiente en lugar de una lista vacía:
        «vacío» y «la fuente está caída» son cosas distintas y no deben confundirse.
        """
        if not anios:
            anios = [2026, 2025, 2024, 2023]

        q_lower = query.lower().strip()
        matches: List[Dict[str, Any]] = []
        avisos: List[Dict[str, Any]] = []

        for yr in anios:
            for lista in (self.get_resoluciones_por_anio(yr), self.get_oficios_por_anio(yr)):
                for item in lista:
                    if item.get("tipo") == "aviso":
                        avisos.append(item)
                        continue
                    texto = f"{item.get('titulo', '')} {item.get('materia', '')}"
                    if _coincide(texto, q_lower) or q_lower == str(item.get("numero", "")).lower():
                        matches.append(item)

        if matches:
            return matches

        if avisos:
            return avisos

        return [_aviso(
            f"Sin resoluciones ni oficios del SII para «{query}»",
            f"Se buscó en el número, el título y la materia de los años "
            f"{', '.join(str(a) for a in anios)}.",
        )]

    def search_circulares(self, query: str, anios: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Busca circulares del SII por número o por tema, en la MATERIA y no sólo en el título.

        El título de cada circular es sólo «Circular N° 35 del 31 de Agosto del 2026»; la materia
        («Actualiza instrucciones sobre mecanismos de impugnación administrativa…») va aparte y es lo
        único que sirve para buscar por tema. Antes se comparaba sólo contra el título, así que toda
        búsqueda temática devolvía cero resultados.
        """
        if not anios:
            anios = [2026, 2025, 2024, 2023, 2022, 2021, 2020]

        q_lower = query.lower().strip()
        matches: List[Dict[str, Any]] = []
        avisos: List[Dict[str, Any]] = []

        for yr in anios:
            for c in self.get_circulares_por_anio(yr):
                if c.get("tipo") == "aviso":
                    avisos.append(c)
                    continue
                num = str(c.get("numero", "")).lower()
                texto = f"{c.get('titulo', '')} {c.get('materia', '')}"
                if _coincide(texto, q_lower) or q_lower == num or _coincide(texto, f"circular {q_lower}"):
                    matches.append(c)

        if matches:
            return matches

        # Sin resultados se explica qué se buscó y dónde: un vacío mudo se lee como «no existe».
        matches.append(_aviso(
            f"Sin circulares del SII para «{query}» en los años consultados",
            "Se buscó en el número, el título y la materia de las circulares de "
            f"{', '.join(str(a) for a in anios)}. Si esperabas resultados, revisa el término o "
            "pide un año concreto con get_circulares_por_anio.",
        ))
        matches.extend(avisos)
        return matches


# ==============================================================================
# CLI DE CONSULTA RÁPIDA DE CIRCULARES SII
# ==============================================================================
if __name__ == "__main__":
    import argparse
    try:
        if hasattr(sys.stdout, "reconfigure"):
            getattr(sys.stdout, "reconfigure")(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Conector Open Legal Chile — Servicio de Impuestos Internos (SII)")
    parser.add_argument("--buscar", type=str, help="Número o término de búsqueda (ej. 'Circular 34' o '34')")
    parser.add_argument("--anio", type=int, default=2026, help="Año de consulta de circulares (ej. 2026, 2025)")
    args = parser.parse_args()

    client = SIIClient()

    if args.buscar:
        print(f"\n💰 Buscando en Circulares del SII: '{args.buscar}'...")
        res = client.search_circulares(args.buscar)
        print(f"Resultados encontrados: {len(res)}")
        for idx, item in enumerate(res):
            print(f"\n[{idx+1}] {item.get('titulo')}")
            print(f"  📄 PDF Oficial: {item.get('pdfUrl')}")
    else:
        print(f"\n💰 Consultando Circulares del SII año {args.anio}...")
        res = client.get_circulares_por_anio(args.anio)
        print(f"Total Circulares publicadas en {args.anio}: {len(res)}")
        print("\nMuestra de circulares:")
        for item in res[:5]:
            print(f" - {item.get('titulo')} -> {item.get('pdfUrl')}")
