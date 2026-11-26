"""
Open Legal Chile — Conector Oficial Superintendencia de Seguridad Social (SUSESO).
Consulta compendios normativos, circulares, dictámenes y jurisprudencia administrativa
bajo la Ley N.° 16.744, licencias médicas, asignaciones familiares y CCAF.
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

BASE_URL = "https://www.suseso.gob.cl/612"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "suseso_cache")
_TTL_CACHE_SEGUNDOS = 7 * 24 * 60 * 60
_MAX_CACHE_RAM = 32

_FUENTES_SUSESO: Dict[str, Tuple[str, str]] = {
    "circulares": ("Circulares de SUSESO", f"{BASE_URL}/w3-propertyvalue-10371.html"),
    "dictamenes": ("Dictámenes SUSESO", f"{BASE_URL}/w3-propertyvalue-10372.html"),
    "compendio": ("Compendios Normativos SUSESO", f"{BASE_URL}/w3-propertyvalue-63550.html"),
}

_ALIASES_TIPO: Dict[str, str] = {
    "todos": "todos",
    "todo": "todos",
    "todas": "todos",
    "circulares": "circulares",
    "circular": "circulares",
    "dictamenes": "dictamenes",
    "dictamen": "dictamenes",
    "compendio": "compendio",
    "compendios": "compendio",
}

_STOPWORDS = frozenset({
    "al", "con", "de", "del", "el", "en", "la", "las", "ley", "lo", "los",
    "para", "por", "que", "se", "sin", "sobre", "su", "sus", "un", "una", "y",
})

# Caché en memoria validada por (mtime_ns, size) para respetar TTL y aislamiento por ruta.
_CACHE_RAM: Dict[str, Tuple[int, int, List[Dict[str, Any]]]] = {}


def _normalizar_tipo(tipo: str) -> Optional[str]:
    clave = config.sin_tildes(tipo or "todos").strip().lower()
    return _ALIASES_TIPO.get(clave)


def _leer_cache_index(ruta_cache: str, ttl_segundos: float) -> Tuple[Optional[List[Dict[str, Any]]], bool]:
    """Retorna (items, es_fresco) desde RAM o disco si el JSON es válido."""
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
        config.registrar_tiempo("suseso.cache_stat_error", 0.0)
        _ = exc


def _extraer_numero_suseso(titulo: str, categoria: str) -> str:
    if categoria == "circulares":
        m = re.search(r"Circular\s*(?:N[.\s°º]*)?(\d+(?:\.\d+)?)", titulo, re.IGNORECASE)
        if m:
            return m.group(1)
    elif categoria == "dictamenes":
        m = re.search(r"Dictamen\s+([A-Z0-9-]+(?:\s*[A-Z0-9-]+)?)", titulo, re.IGNORECASE)
        if m:
            return re.sub(r"\s+", "", m.group(1))
    return ""


def _parsear_suseso_html(html_text: str, categoria: str) -> List[Dict[str, Any]]:
    """Extrae normas, circulares, dictámenes o compendios desde HTML oficial de SUSESO."""
    soup = BeautifulSoup(html_text or "", "html.parser")
    items: List[Dict[str, Any]] = []
    vistos: set[str] = set()

    bloques = soup.select("div.recuadro")
    if not bloques:
        bloques = soup.select("article, tr")

    for bloque in bloques:
        enlace = bloque.select_one(
            "h3.titulo a, p.titulo a, h2 a, h4 a, a[href*='w3-article'], "
            "a[href*='w3-channel'], a[href*='w3-propertyname']"
        )
        if enlace is None:
            continue
        href = str(enlace.get("href") or "").strip()
        if not href or any(red in href.lower() for red in ("facebook.com", "twitter.com", "youtube.com")):
            continue
        titulo = config.texto_plano(enlace.get_text(" ", strip=True))
        if not titulo:
            continue

        url_doc = urllib.parse.urljoin(f"{BASE_URL}/", href)
        pdf_tag = bloque.select_one("a[href*='.pdf']")
        pdf_url = urllib.parse.urljoin(f"{BASE_URL}/", str(pdf_tag.get("href") or "").strip()) if pdf_tag else ""

        fecha = ""
        fecha_tag = bloque.select_one("h6.fecha, p.fecha, span.fecha, [class*='iso8601']")
        if fecha_tag is not None:
            fecha = config.texto_plano(fecha_tag.get_text(" ", strip=True))

        partes_materia: List[str] = []
        for p in bloque.find_all("p"):
            clases = " ".join(p.get("class") or [])
            txt_p = config.texto_plano(p.get_text(" ", strip=True))
            if not txt_p or txt_p == titulo or txt_p == fecha:
                continue
            if "fecha" in clases or "titulo" in clases:
                continue
            if txt_p.lower() in {"oficio", "resolución", "resolucion"}:
                continue
            partes_materia.append(txt_p)

        materia = " | ".join(partes_materia) or config.texto_plano(str(enlace.get("title") or "")) or titulo
        numero = _extraer_numero_suseso(titulo, categoria)
        clave = f"{categoria}:{url_doc}:{titulo}"
        if clave in vistos:
            continue
        vistos.add(clave)

        normas_rel: List[str] = []
        materia_low = config.sin_tildes(f"{titulo} {materia}").lower()
        if "16.744" in materia_low or "16744" in materia_low or "accidente" in materia_low or "profesional" in materia_low:
            normas_rel.append("Ley N.° 16.744")
        if "licencia" in materia_low or "subsidio" in materia_low:
            normas_rel.append("D.S. N.° 3/1984 MINSAL")
        if "sanna" in materia_low or "21.063" in materia_low:
            normas_rel.append("Ley N.° 21.063")

        items.append({
            "organismo": "SUSESO",
            "categoria": categoria,
            "titulo": titulo,
            "numero": numero,
            "fecha": fecha,
            "materia": materia,
            "resumen": materia[:500],
            "url": url_doc,
            "pdf_url": pdf_url,
            "normas_relacionadas": normas_rel,
        })

    return items


def _puntaje_item(item: Dict[str, Any], query: str) -> int:
    q = (query or "").strip()
    if not q:
        return 1
    cuerpo = f"{item.get('numero', '')} {item.get('titulo', '')} {item.get('materia', '')}"
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


def _construir_cita_suseso(item: Dict[str, Any]) -> Dict[str, str]:
    cat = item.get("categoria", "")
    titulo = str(item.get("titulo") or "Norma SUSESO").strip()
    numero = str(item.get("numero") or "").strip()
    fecha = str(item.get("fecha") or "").strip()
    url = str(item.get("url") or item.get("pdf_url") or f"{BASE_URL}/w3-channel.html")
    texto = str(item.get("materia") or titulo)[:900]

    if cat == "circulares":
        ident = f"Circular N.° {numero}" if numero else titulo
        if fecha:
            ident = f"{ident}, {fecha}"
        return formatear_cita("SUSESO", ident, url=url, texto=texto)
    if cat == "dictamenes":
        ident = numero or titulo
        if fecha:
            ident = f"{ident}, {fecha}"
        return formatear_cita("Dictamen SUSESO", ident, url=url, texto=texto)
    ident = f"Compendio Normativo: {titulo}"
    return formatear_cita("SUSESO", ident, url=url, texto=texto)


def _cargar_categoria(
    categoria: str,
    carpeta_cache: str,
    solo_cache: bool,
    ttl_segundos: float,
) -> Tuple[List[Dict[str, Any]], str, bool, List[Dict[str, Any]]]:
    titulo_fuente, url = _FUENTES_SUSESO[categoria]
    ruta_cache = os.path.join(carpeta_cache, f"suseso_{categoria}.json")
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
            "No existe copia local disponible y solo_cache=True impide consultar suseso.gob.cl.",
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
        config.registrar_tiempo(f"suseso.{categoria}.error", time.perf_counter() - t0)
        if items_cache is not None:
            aviso = config.aviso_conector(
                f"Fuente {titulo_fuente} sin conexión ({type(exc).__name__})",
                f"Se entrega copia local vencida de SUSESO tras error de red: {str(exc)[:140]}.",
            )
            return items_cache, "cache_vencida", True, [aviso]
        aviso = config.aviso_conector(
            f"No se pudo consultar {titulo_fuente}",
            f"El portal oficial de SUSESO no respondió ({str(exc)[:140]}). Sin fuente verificable.",
        )
        return [], "sin_datos", False, [aviso]

    config.registrar_tiempo(f"suseso.{categoria}.red", time.perf_counter() - t0)
    parseados = _parsear_suseso_html(crudo, categoria)
    if not parseados:
        if items_cache is not None:
            aviso = config.aviso_conector(
                f"Respuesta sin registros reconocibles en {titulo_fuente}",
                "Se mantiene la copia local vencida de SUSESO mientras se valida la estructura HTML.",
            )
            return items_cache, "cache_vencida", True, [aviso]
        aviso = config.aviso_conector(
            f"Sin registros parseables en {titulo_fuente}",
            "El HTML de SUSESO respondió sin bloques reconocibles de normativa.",
        )
        return [], "sin_datos", False, [aviso]

    _guardar_cache_index(ruta_cache, parseados)
    return parseados, "red", False, []


def suseso_buscar_normativa(
    query: str,
    tipo: str = "todos",
    limite: int = 10,
    solo_cache: bool = False,
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Busca circulares, dictámenes y compendios normativos oficiales de la SUSESO."""
    tipo_norm = _normalizar_tipo(tipo)
    if tipo_norm is None:
        return {
            "organismo": "SUSESO",
            "query": query,
            "tipo": tipo,
            "total": 0,
            "resultados": [],
            "citas": [],
            "sin_fuente_verificable": True,
            "error": f"Tipo '{tipo}' no válido. Use: todos, circulares, dictamenes o compendio.",
            "avisos": [
                config.aviso_conector(
                    "Parámetro 'tipo' inválido en SUSESO",
                    "Valores admitidos: 'todos', 'circulares', 'dictamenes', 'compendio'.",
                )
            ],
        }

    limite_seguro = max(1, min(int(limite), 50))
    carpeta = cache_dir or CACHE_DIR
    categorias = ["circulares", "dictamenes", "compendio"] if tipo_norm == "todos" else [tipo_norm]

    candidatos: List[Tuple[int, Dict[str, Any]]] = []
    avisos: List[Dict[str, Any]] = []
    fuentes_urls: List[str] = []
    origenes: List[str] = []
    hay_vencida = False
    hay_fuente_disponible = False

    for cat in categorias:
        fuentes_urls.append(_FUENTES_SUSESO[cat][1])
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
        cita = _construir_cita_suseso(item)
        enriquecido = {**item, "cita": cita, "citas": [cita]}
        seleccionados.append(enriquecido)
        citas.append(cita)

    if not seleccionados and hay_fuente_disponible and (query or "").strip():
        avisos.append(
            config.aviso_conector(
                f"Sin normativa SUSESO coincidente para «{query}»",
                "Se revisaron las fuentes oficiales cargadas de SUSESO sin coincidencias directas.",
            )
        )

    origen_global = (
        "cache_vencida"
        if hay_vencida
        else ("red" if "red" in origenes else ("cache" if "cache" in origenes else "sin_datos"))
    )
    sin_fuente = not hay_fuente_disponible

    return {
        "organismo": "SUSESO",
        "query": query,
        "tipo": tipo_norm,
        "total": len(seleccionados),
        "resultados": seleccionados,
        "citas": citas,
        "fuentes_consultadas": fuentes_urls,
        "origen": origen_global,
        "copia_local_vencida": hay_vencida,
        "sin_fuente_verificable": sin_fuente,
        "avisos": avisos,
    }
