"""
Open Legal Chile — Conector Oficial Servicio Nacional del Consumidor (SERNAC).
Consulta circulares interpretativas (Ley N.° 19.496), alertas de seguridad de productos
y demandas o juicios colectivos públicos publicados por SERNAC.
"""

import json
import os
import re
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

import config
from citas_legales import formatear_cita

BASE_URL = "https://www.sernac.cl"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "sernac_cache")
_TTL_CACHE_SEGUNDOS = 7 * 24 * 60 * 60
_MAX_CACHE_RAM = 32

_FUENTES_SERNAC: Dict[str, Tuple[str, str, str]] = {
    "circulares": (
        "Circulares Interpretativas SERNAC",
        f"{BASE_URL}/portal/618/w3-propertyvalue-21072.html",
        f"{BASE_URL}/portal/618/",
    ),
    "alertas": (
        "Alertas de Seguridad de Productos SERNAC",
        f"{BASE_URL}/portal/618/w3-propertyvalue-62727.html",
        f"{BASE_URL}/portal/618/",
    ),
    "juicios_colectivos": (
        "Juicios Colectivos y Demandas SERNAC",
        f"{BASE_URL}/portal/609/w3-propertyvalue-59114.html",
        f"{BASE_URL}/portal/609/",
    ),
}

_ALIASES_CATEGORIA: Dict[str, str] = {
    "todas": "todas",
    "todos": "todas",
    "todo": "todas",
    "circulares": "circulares",
    "circular": "circulares",
    "alertas": "alertas",
    "alerta": "alertas",
    "juicios_colectivos": "juicios_colectivos",
    "juicios": "juicios_colectivos",
    "demandas_colectivas": "juicios_colectivos",
}

_STOPWORDS = frozenset({
    "al", "con", "de", "del", "el", "en", "la", "las", "ley", "lo", "los",
    "para", "por", "que", "se", "sin", "sobre", "su", "sus", "un", "una", "y",
})

_CACHE_RAM: Dict[str, Tuple[int, int, List[Dict[str, Any]]]] = {}


def _normalizar_categoria(categoria: str) -> Optional[str]:
    clave = config.sin_tildes(categoria or "todas").strip().lower()
    return _ALIASES_CATEGORIA.get(clave)


def _leer_cache_index(ruta_cache: str, ttl_segundos: float) -> Tuple[Optional[List[Dict[str, Any]]], bool]:
    abs_ruta = os.path.abspath(ruta_cache)
    try:
        st = os.stat(abs_ruta)
    except OSError:
        return None, False

    fresco = config.cache_fresco(abs_ruta, ttl_segundos)
    en_ram = _CACHE_RAM.get(abs_ruta)
    if en_ram is not None and en_ram[0] == st.st_mtime_ns and en_ram[1] == st.st_size:
        return en_ram[2], fresco

    leido = config.leer_json_si_se_puede(abs_ruta)
    if not isinstance(leido, list):
        return None, False

    if len(_CACHE_RAM) >= _MAX_CACHE_RAM:
        _CACHE_RAM.clear()
    _CACHE_RAM[abs_ruta] = (int(st.st_mtime_ns), int(st.st_size), leido)
    return leido, fresco


def _guardar_cache_index(ruta_cache: str, items: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(ruta_cache), exist_ok=True)
    abs_ruta = os.path.abspath(ruta_cache)
    with open(abs_ruta, "w", encoding="utf-8") as fh:
        json.dump(items, fh, ensure_ascii=False, indent=2)
    try:
        st = os.stat(abs_ruta)
        if len(_CACHE_RAM) >= _MAX_CACHE_RAM:
            _CACHE_RAM.clear()
        _CACHE_RAM[abs_ruta] = (int(st.st_mtime_ns), int(st.st_size), items)
    except OSError as exc:
        config.registrar_tiempo("sernac.cache_stat_error", 0.0)
        _ = exc


def _parsear_sernac_html(html_text: str, categoria: str, base_portal: str) -> List[Dict[str, Any]]:
    """Extrae circulares interpretativas, alertas de seguridad o juicios colectivos de SERNAC."""
    soup = BeautifulSoup(html_text or "", "html.parser")
    items: List[Dict[str, Any]] = []
    vistos: set[str] = set()

    bloques = soup.select("div.recuadro")
    if not bloques:
        bloques = soup.select("article, tr")

    for bloque in bloques:
        enlace = bloque.select_one(
            "h3.titulo a, h2 a, h4 a, p.titulo a, a[href*='w3-article'], a[href*='w3-propertyvalue']"
        )
        if enlace is None:
            continue
        href = str(enlace.get("href") or "").strip()
        if not href or any(red in href.lower() for red in ("facebook.com", "twitter.com", "youtube.com")):
            continue

        titulo = config.texto_plano(enlace.get_text(" ", strip=True))
        if not titulo:
            continue

        url_doc = urllib.parse.urljoin(base_portal, href)
        pdf_tag = bloque.select_one("a[href*='.pdf']")
        pdf_url = urllib.parse.urljoin(base_portal, str(pdf_tag.get("href") or "").strip()) if pdf_tag else ""

        fecha = ""
        fecha_tag = bloque.select_one("p.fecha, h6.fecha, span.fecha, [class*='iso8601']")
        if fecha_tag is not None:
            fecha = config.texto_plano(fecha_tag.get_text(" ", strip=True))

        detalles: List[str] = []
        for nodo in bloque.find_all(["p", "div"]):
            if nodo.find("div", class_="recuadro"):
                continue
            clases = " ".join(nodo.get("class") or [])
            if "fecha" in clases or "media-left" in clases or "media-body" in clases:
                continue
            txt = config.texto_plano(nodo.get_text(" ", strip=True))
            if not txt or txt == titulo or txt == fecha or txt in detalles:
                continue
            detalles.append(txt)

        resumen = " | ".join(detalles) or config.texto_plano(str(enlace.get("title") or "")) or titulo
        proveedor = ""
        m_prov = re.search(r"Proveedor:\s*([^|]+)", resumen, re.IGNORECASE)
        if m_prov:
            proveedor = m_prov.group(1).strip()

        clave = f"{categoria}:{url_doc}:{titulo}"
        if clave in vistos:
            continue
        vistos.add(clave)

        items.append({
            "organismo": "SERNAC",
            "categoria": categoria,
            "titulo": titulo,
            "fecha": fecha,
            "proveedor": proveedor,
            "materia": resumen,
            "resumen": resumen[:500],
            "url": url_doc,
            "pdf_url": pdf_url,
            "normas_relacionadas": ["Ley N.° 19.496"],
        })

    return items


def _puntaje_item(item: Dict[str, Any], query: str) -> int:
    q = (query or "").strip()
    if not q:
        return 1
    cuerpo = f"{item.get('titulo', '')} {item.get('proveedor', '')} {item.get('materia', '')}"
    cuerpo_st = config.sin_tildes(cuerpo).lower()
    q_st = config.sin_tildes(q).lower()

    patron_exacto = r"\b" + r"\s+".join(re.escape(p) for p in q_st.split()) + r"\b"
    if re.search(patron_exacto, cuerpo_st):
        return 3

    tokens = [t for t in re.findall(r"[a-z0-9.]+", q_st) if len(t) >= 2 and t not in _STOPWORDS]
    if not tokens:
        return 0

    cuerpo_sin_puntos = cuerpo_st.replace(".", "")
    hits = sum(
        1
        for tok in tokens
        if re.search(rf"\b{re.escape(tok.replace('.', ''))}\b", cuerpo_sin_puntos) is not None
        or tok.replace(".", "") in cuerpo_sin_puntos
    )
    if hits == len(tokens):
        return 2
    if len(tokens) >= 2 and hits >= max(1, (len(tokens) + 1) // 2):
        return 1
    return 0


def _construir_cita_sernac(item: Dict[str, Any]) -> Dict[str, str]:
    cat = item.get("categoria", "")
    titulo = str(item.get("titulo") or "Acto SERNAC").strip()
    fecha = str(item.get("fecha") or "").strip()
    url = str(item.get("url") or item.get("pdf_url") or f"{BASE_URL}/portal/618/w3-propertyvalue-14522.html")
    texto = str(item.get("materia") or titulo)[:900]

    if cat == "circulares":
        ident = f"Circular Interpretativa {titulo}"
    elif cat == "alertas":
        ident = titulo if titulo.lower().startswith("alerta de seguridad") else f"Alerta de Seguridad {titulo}"
    else:
        ident = titulo if titulo.lower().startswith("juicio") else f"Juicio Colectivo {titulo}"

    if fecha:
        ident = f"{ident} ({fecha})"
    return formatear_cita("SERNAC", ident[:200], url=url, texto=texto)


def _cargar_categoria(
    categoria: str,
    carpeta_cache: str,
    solo_cache: bool,
    ttl_segundos: float,
) -> Tuple[List[Dict[str, Any]], str, bool, List[Dict[str, Any]]]:
    titulo_fuente, url, base_portal = _FUENTES_SERNAC[categoria]
    ruta_cache = os.path.join(carpeta_cache, f"sernac_{categoria}.json")
    items_cache, fresco = _leer_cache_index(ruta_cache, ttl_segundos)

    if items_cache is not None and fresco:
        return items_cache, "cache", False, []

    if solo_cache:
        if items_cache is not None:
            aviso = config.aviso_conector(
                f"Copia local vencida en {titulo_fuente}",
                "Se utilizó la caché local expirada porque se solicitó solo_cache=True.",
            )
            return items_cache, "cache_vencida", True, [aviso]
        aviso = config.aviso_conector(
            f"Sin caché local para {titulo_fuente}",
            "No existe copia local disponible y solo_cache=True impide consultar sernac.cl.",
        )
        return [], "sin_datos", False, [aviso]

    t0 = time.perf_counter()
    try:
        crudo = config.pedir_http(
            url,
            headers={"Accept": "text/html,application/xhtml+xml"},
            timeout=25.0,
        ).decode("utf-8", errors="ignore")
    except Exception as exc:  # noqa: BLE001
        config.registrar_tiempo(f"sernac.{categoria}.error", time.perf_counter() - t0)
        if items_cache is not None:
            aviso = config.aviso_conector(
                f"Fuente {titulo_fuente} sin conexión ({type(exc).__name__})",
                f"Se entrega copia local vencida de SERNAC tras error de red: {str(exc)[:140]}.",
            )
            return items_cache, "cache_vencida", True, [aviso]
        aviso = config.aviso_conector(
            f"No se pudo consultar {titulo_fuente}",
            f"El portal oficial de SERNAC no respondió ({str(exc)[:140]}). Sin fuente verificable.",
        )
        return [], "sin_datos", False, [aviso]

    config.registrar_tiempo(f"sernac.{categoria}.red", time.perf_counter() - t0)
    parseados = _parsear_sernac_html(crudo, categoria, base_portal)
    if not parseados:
        if items_cache is not None:
            aviso = config.aviso_conector(
                f"Respuesta sin registros reconocibles en {titulo_fuente}",
                "Se mantiene la copia local vencida de SERNAC mientras se valida el portal.",
            )
            return items_cache, "cache_vencida", True, [aviso]
        aviso = config.aviso_conector(
            f"Sin registros parseables en {titulo_fuente}",
            "El HTML de SERNAC respondió sin bloques reconocibles para la categoría.",
        )
        return [], "sin_datos", False, [aviso]

    _guardar_cache_index(ruta_cache, parseados)
    return parseados, "red", False, []


def sernac_buscar_consumidor(
    query: str,
    categoria: str = "todas",
    limite: int = 10,
    solo_cache: bool = False,
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Busca circulares interpretativas, alertas de seguridad y juicios colectivos en SERNAC."""
    cat_norm = _normalizar_categoria(categoria)
    if cat_norm is None:
        return {
            "organismo": "SERNAC",
            "query": query,
            "categoria": categoria,
            "total": 0,
            "resultados": [],
            "citas": [],
            "sin_fuente_verificable": True,
            "error": f"Categoría '{categoria}' no válida. Use: todas, circulares, alertas o juicios_colectivos.",
            "avisos": [
                config.aviso_conector(
                    "Parámetro 'categoria' inválido en SERNAC",
                    "Valores admitidos: 'todas', 'circulares', 'alertas', 'juicios_colectivos'.",
                )
            ],
        }

    limite_seguro = max(1, min(int(limite), 50))
    carpeta = cache_dir or CACHE_DIR
    categorias = ["circulares", "alertas", "juicios_colectivos"] if cat_norm == "todas" else [cat_norm]

    candidatos: List[Tuple[int, Dict[str, Any]]] = []
    avisos: List[Dict[str, Any]] = []
    fuentes_urls: List[str] = []
    origenes: List[str] = []
    hay_vencida = False
    hay_fuente_disponible = False

    for cat in categorias:
        fuentes_urls.append(_FUENTES_SERNAC[cat][1])
        items_cat, origen_cat, vencida_cat, avisos_cat = _cargar_categoria(
            cat, carpeta, solo_cache, _TTL_CACHE_SEGUNDOS
        )
        origenes.append(origen_cat)
        avisos.extend(avisos_cat)
        if vencida_cat:
            hay_vencida = True
        if items_cat:
            hay_fuente_disponible = True
        for item in items_cat:
            score = _puntaje_item(item, query)
            if score > 0:
                candidatos.append((score, item))

    candidatos.sort(key=lambda par: par[0], reverse=True)
    seleccionados: List[Dict[str, Any]] = []
    citas: List[Dict[str, str]] = []
    for _, item in candidatos[:limite_seguro]:
        cita = _construir_cita_sernac(item)
        enriquecido = {**item, "cita": cita, "citas": [cita]}
        seleccionados.append(enriquecido)
        citas.append(cita)

    if not seleccionados and hay_fuente_disponible and (query or "").strip():
        avisos.append(
            config.aviso_conector(
                f"Sin registros de SERNAC para «{query}»",
                "Se revisaron las fuentes oficiales de SERNAC sin coincidencias directas.",
            )
        )

    origen_global = (
        "cache_vencida"
        if hay_vencida
        else ("red" if "red" in origenes else ("cache" if "cache" in origenes else "sin_datos"))
    )

    return {
        "organismo": "SERNAC",
        "query": query,
        "categoria": cat_norm,
        "total": len(seleccionados),
        "resultados": seleccionados,
        "citas": citas,
        "fuentes_consultadas": fuentes_urls,
        "origen": origen_global,
        "copia_local_vencida": hay_vencida,
        "sin_fuente_verificable": not hay_fuente_disponible,
        "avisos": avisos,
    }
