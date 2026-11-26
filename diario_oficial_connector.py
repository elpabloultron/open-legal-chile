"""
Open Legal Chile — Conector Oficial Diario Oficial de la República de Chile
Módulo para consultar sumarios, ediciones diarias por fecha (`diariooficial.interior.gob.cl`),
normas generales, normas particulares, avisos destacados y extractos societarios/judiciales
identificados por su Código de Verificación Electrónica (CVE).
"""

from datetime import date, datetime
import json
import os
import re
import threading
from typing import Any, Dict, List, Optional, Tuple
import urllib.parse

from bs4 import BeautifulSoup

from citas_legales import formatear_cita
import config
from config import (
    aviso_conector,
    cache_fresco,
    leer_json_si_se_puede,
    pedir_http,
    sin_tildes,
    texto_plano,
)

BASE_DIARIO_OFICIAL = "https://www.diariooficial.interior.gob.cl"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "diario_oficial_cache")
TTL_CACHE_SEGUNDOS = 24 * 60 * 60

SECCIONES_VALIDAS = (
    "todas",
    "normas_generales",
    "normas_particulares",
    "avisos_destacados",
    "empresas_sociedades",
)

_RE_CVE = re.compile(r"\bCVE[-:\s]*([0-9]{5,12})\b", re.IGNORECASE)
_RE_EDICION = re.compile(r"\bEdici[oó]n\s*(?:N[°º\.\s]*)?([0-9]{1,3}(?:\.[0-9]{3})+|[0-9]{4,7})\b", re.IGNORECASE)
_RE_TIPO_NUM = re.compile(
    r"\b(Ley\s+N[°º\.\s]*[0-9\.]+|D\.?F\.?L\.?\s+N[°º\.\s]*[0-9\.]+|Decreto(?:\s+Supremo)?\s+N[°º\.\s]*[0-9\.]+|Resoluci[oó]n(?:\s+Exenta)?\s+N[°º\.\s]*[0-9\.]+)\b",
    re.IGNORECASE,
)

_PEDIR_HTTP_BASE = pedir_http
_MEM_LOCK = threading.Lock()
_MEM_CACHE: Dict[str, Tuple[int, int, Dict[str, Any]]] = {}


def _http_get_bytes(url: str, headers: Optional[Dict[str, str]] = None, timeout: float = 20.0) -> bytes:
    """Ejecuta GET HTTP mediante `pedir_http` del módulo o de `config`."""
    fn = pedir_http if pedir_http is not _PEDIR_HTTP_BASE else config.pedir_http
    if headers:
        return fn(url, headers=headers, timeout=timeout)
    return fn(url, timeout=timeout)


def _normalizar_fecha(fecha: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Normaliza fecha ('' -> hoy) a (YYYY-MM-DD, DD-MM-YYYY, error)."""
    cruda = (fecha or "").strip()
    if not cruda:
        hoy = date.today()
        return hoy.isoformat(), hoy.strftime("%d-%m-%Y"), None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(cruda, fmt)
            return dt.strftime("%Y-%m-%d"), dt.strftime("%d-%m-%Y"), None
        except ValueError:
            continue
    return None, None, f"Fecha inválida: '{fecha}'. Use formato YYYY-MM-DD."


def _leer_cache(ruta_cache: str) -> Optional[Dict[str, Any]]:
    abs_path = os.path.abspath(ruta_cache)
    try:
        st = os.stat(abs_path)
    except OSError:
        return None
    with _MEM_LOCK:
        hit = _MEM_CACHE.get(abs_path)
        if hit is not None and hit[0] == st.st_mtime_ns and hit[1] == st.st_size:
            return dict(hit[2])
    dato = leer_json_si_se_puede(abs_path)
    if not isinstance(dato, dict):
        return None
    with _MEM_LOCK:
        _MEM_CACHE[abs_path] = (st.st_mtime_ns, st.st_size, dato)
    return dict(dato)


def _guardar_cache(ruta_cache: str, datos: Dict[str, Any]) -> None:
    abs_path = os.path.abspath(ruta_cache)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    temporal = f"{abs_path}.{os.getpid()}.tmp"
    try:
        with open(temporal, "w", encoding="utf-8") as fh:
            json.dump(datos, fh, ensure_ascii=False, indent=2)
        os.replace(temporal, abs_path)
        st = os.stat(abs_path)
        with _MEM_LOCK:
            _MEM_CACHE[abs_path] = (st.st_mtime_ns, st.st_size, datos)
    except OSError:
        try:
            os.remove(temporal)
        except OSError:
            pass


def _mapear_seccion(texto_sec: str, defecto: str = "normas_generales") -> str:
    norm = sin_tildes(texto_sec or "").lower().strip()
    if not norm:
        return defecto
    if "particular" in norm:
        return "normas_particulares"
    if "aviso" in norm or "destacado" in norm or "judicial" in norm:
        return "avisos_destacados"
    if "empresa" in norm or "sociedad" in norm or "cooperativa" in norm or "extracto" in norm:
        return "empresas_sociedades"
    if "general" in norm:
        return "normas_generales"
    return defecto


def _resolver_url_do(href: str, fecha_dmy: str) -> str:
    limpia = (href or "").strip()
    if limpia.startswith("http://") or limpia.startswith("https://"):
        return limpia
    if limpia.startswith("/"):
        return f"{BASE_DIARIO_OFICIAL}{limpia}"
    if limpia:
        return f"{BASE_DIARIO_OFICIAL}/{limpia.lstrip('./')}"
    return f"{BASE_DIARIO_OFICIAL}/edicionelectronica/index.php?date={urllib.parse.quote(fecha_dmy)}"


def _construir_item_do(
    titulo: str,
    seccion: str,
    cve: str,
    organismo: str,
    extracto: str,
    url: str,
    fecha_iso: str,
    fecha_dmy: str,
    tipo_acto: str = "",
    numero_norma: str = "",
) -> Dict[str, Any]:
    titulo_l = texto_plano(titulo)
    extracto_l = texto_plano(extracto) or titulo_l
    cve_l = str(cve or "").strip()
    if not cve_l:
        m_cve = _RE_CVE.search(f"{titulo_l} {extracto_l} {url}")
        cve_l = m_cve.group(1) if m_cve else ""

    if not numero_norma:
        m_norma = _RE_TIPO_NUM.search(titulo_l)
        numero_norma = m_norma.group(1) if m_norma else ""

    if not tipo_acto:
        if seccion == "empresas_sociedades":
            tipo_acto = "Extracto Societario"
        elif seccion == "avisos_destacados":
            tipo_acto = "Aviso Destacado"
        elif "ley" in titulo_l.lower():
            tipo_acto = "Ley"
        elif "decreto" in titulo_l.lower():
            tipo_acto = "Decreto"
        elif "resoluci" in titulo_l.lower():
            tipo_acto = "Resolución"
        else:
            tipo_acto = "Publicación Oficial"

    url_final = _resolver_url_do(url, fecha_dmy)
    ident_cita = f"Edición {fecha_iso}, CVE {cve_l}" if cve_l else f"Edición {fecha_iso} — {titulo_l[:80]}"
    cita = formatear_cita("Diario Oficial", ident_cita, url=url_final, texto=extracto_l[:900])

    return {
        "titulo": titulo_l,
        "seccion": seccion,
        "cve": cve_l,
        "organismo": texto_plano(organismo),
        "tipo_acto": tipo_acto,
        "numero_norma": numero_norma,
        "fecha": fecha_iso,
        "extracto": extracto_l,
        "url": url_final,
        "citas": [cita],
    }


def _parsear_json_do(
    data: Any,
    fecha_iso: str,
    fecha_dmy: str,
    seccion_defecto: str,
) -> Tuple[List[Dict[str, Any]], str]:
    items: List[Dict[str, Any]] = []
    edicion = ""

    def _agregar_lista(lista: Any, sec: str) -> None:
        if not isinstance(lista, list):
            return
        for reg in lista:
            if not isinstance(reg, dict):
                continue
            tit = str(reg.get("titulo") or reg.get("sumario") or reg.get("nombre") or reg.get("materia") or "")
            if not tit.strip():
                continue
            sec_reg = _mapear_seccion(str(reg.get("seccion") or ""), defecto=sec)
            items.append(
                _construir_item_do(
                    titulo=tit,
                    seccion=sec_reg,
                    cve=str(reg.get("cve") or reg.get("CVE") or ""),
                    organismo=str(reg.get("organismo") or reg.get("emisor") or reg.get("ministerio") or ""),
                    extracto=str(reg.get("extracto") or reg.get("texto") or reg.get("descripcion") or tit),
                    url=str(reg.get("url") or reg.get("pdf_url") or reg.get("link") or ""),
                    fecha_iso=str(reg.get("fecha") or fecha_iso)[:10],
                    fecha_dmy=fecha_dmy,
                    tipo_acto=str(reg.get("tipo_acto") or ""),
                    numero_norma=str(reg.get("numero_norma") or reg.get("numero") or ""),
                )
            )

    if isinstance(data, dict):
        edicion = str(data.get("edicion") or data.get("numero_edicion") or "")
        for clave_sec in ("normas_generales", "normas_particulares", "avisos_destacados", "empresas_sociedades"):
            if isinstance(data.get(clave_sec), list):
                _agregar_lista(data[clave_sec], clave_sec)
        for clave_lista in ("publicaciones", "resultados", "sumario", "items"):
            if isinstance(data.get(clave_lista), list):
                _agregar_lista(data[clave_lista], seccion_defecto)
    elif isinstance(data, list):
        _agregar_lista(data, seccion_defecto)

    return items, edicion


def _parsear_html_do(
    html_text: str,
    fecha_iso: str,
    fecha_dmy: str,
    seccion_defecto: str,
) -> Tuple[List[Dict[str, Any]], str]:
    soup = BeautifulSoup(html_text, "html.parser")
    edicion = ""
    m_ed = _RE_EDICION.search(soup.get_text(" ", strip=True))
    if m_ed:
        edicion = m_ed.group(1)

    items: List[Dict[str, Any]] = []
    vistos = set()
    seccion_actual = seccion_defecto if seccion_defecto != "todas" else "normas_generales"

    for elem in soup.find_all(["h1", "h2", "h3", "h4", "h5", "tr", "li"]):
        if elem.name in ("h1", "h2", "h3", "h4", "h5"):
            txt_h = elem.get_text(" ", strip=True)
            sec_detectada = _mapear_seccion(txt_h, defecto="")
            if sec_detectada:
                seccion_actual = sec_detectada
            continue

        # Filas de tabla o ítems de lista con publicación
        if elem.name == "li" and elem.find("tr") is not None:
            continue

        texto_bloque = elem.get_text(" ", strip=True)
        if len(texto_bloque) < 12:
            continue

        enlace = elem.find("a", href=True)
        href = str(enlace["href"]) if enlace else ""
        if href and any(omit in href.lower() for omit in ("javascript:", "#")):
            href = ""

        # Extraer celdas si es <tr>
        organismo = ""
        cve = ""
        titulo = texto_plano(enlace.get_text(" ", strip=True)) if enlace else ""
        if elem.name == "tr":
            celdas = [texto_plano(td.get_text(" ", strip=True)) for td in elem.find_all("td")]
            if not celdas:
                continue
            if not titulo:
                titulo = max(celdas, key=len)
            for c in celdas:
                m_c = _RE_CVE.search(c)
                if m_c:
                    cve = m_c.group(1)
                elif c != titulo and len(c) > 3 and not organismo:
                    organismo = c
        else:
            if not titulo or len(titulo) < 8:
                titulo = texto_bloque

        if not titulo or len(titulo) < 6:
            continue
        if any(nav in titulo.lower() for nav in ("ver edición anterior", "buscar por cve", "inicio")):
            continue

        clave_dup = (cve or titulo.lower()[:80], href)
        if clave_dup in vistos:
            continue
        vistos.add(clave_dup)

        items.append(
            _construir_item_do(
                titulo=titulo,
                seccion=seccion_actual,
                cve=cve,
                organismo=organismo,
                extracto=texto_bloque,
                url=href,
                fecha_iso=fecha_iso,
                fecha_dmy=fecha_dmy,
            )
        )

    return items, edicion


def _coincide_texto(haystack: str, needle: str) -> bool:
    if not needle.strip():
        return True
    h_norm = sin_tildes(haystack).lower()
    tokens = [t for t in sin_tildes(needle).lower().split() if t]
    return all(tok in h_norm for tok in tokens)


def _filtrar_y_armar_respuesta(
    base_edicion: Dict[str, Any],
    seccion_norm: str,
    query: str,
    limite_seg: int,
) -> Dict[str, Any]:
    crudos = list(base_edicion.get("resultados") or [])
    filtrados: List[Dict[str, Any]] = []
    for item in crudos:
        if seccion_norm != "todas" and item.get("seccion") != seccion_norm:
            continue
        if query.strip():
            texto_item = " ".join([
                item.get("titulo", ""),
                item.get("organismo", ""),
                item.get("cve", ""),
                item.get("numero_norma", ""),
                item.get("extracto", ""),
                item.get("tipo_acto", ""),
            ])
            if not _coincide_texto(texto_item, query):
                continue
        filtrados.append(item)
        if len(filtrados) >= limite_seg:
            break

    citas: List[Dict[str, str]] = []
    for item in filtrados:
        citas.extend(item.get("citas") or [])

    advertencias = list(base_edicion.get("advertencias") or [])
    if not filtrados and not base_edicion.get("sin_fuente_verificable"):
        advertencias.append(
            aviso_conector(
                "Sin publicaciones coincidentes en el Diario Oficial",
                f"La edición {base_edicion.get('fecha')} no registró publicaciones para los filtros indicados.",
            )
        )

    salida: Dict[str, Any] = {
        "fuente": "Diario Oficial de la República de Chile",
        "fecha": base_edicion.get("fecha", ""),
        "edicion": base_edicion.get("edicion", ""),
        "seccion": seccion_norm,
        "query": query,
        "total": len(filtrados),
        "resultados": filtrados,
        "citas": citas,
        "advertencias": advertencias,
        "desde_cache": bool(base_edicion.get("desde_cache")),
        "sin_fuente_verificable": bool(base_edicion.get("sin_fuente_verificable")),
    }
    if base_edicion.get("copia_local_vencida"):
        salida["copia_local_vencida"] = True
    if base_edicion.get("error"):
        salida["error"] = base_edicion["error"]
    return salida


def diario_oficial_consultar(
    fecha: str = "",
    seccion: str = "todas",
    query: str = "",
    limite: int = 15,
    solo_cache: bool = False,
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Consulta el sumario y publicaciones oficiales del Diario Oficial de Chile por fecha y sección.

    Soporta ``seccion`` en ``("todas", "normas_generales", "normas_particulares",
    "avisos_destacados", "empresas_sociedades")`` con caché por edición, soporte offline
    y citas oficiales ``[Diario Oficial - Edición YYYY-MM-DD, CVE ...]``.
    """
    fecha_iso, fecha_dmy, err_fecha = _normalizar_fecha(fecha)
    if err_fecha or not fecha_iso or not fecha_dmy:
        return {
            "fuente": "Diario Oficial de la República de Chile",
            "fecha": fecha,
            "seccion": seccion,
            "query": query,
            "error": err_fecha or "Fecha inválida.",
            "total": 0,
            "resultados": [],
            "citas": [],
            "advertencias": [aviso_conector("Fecha inválida", err_fecha or "Use YYYY-MM-DD.")],
            "desde_cache": False,
            "sin_fuente_verificable": True,
        }

    seccion_norm = (seccion or "todas").strip().lower()
    if seccion_norm not in SECCIONES_VALIDAS:
        return {
            "fuente": "Diario Oficial de la República de Chile",
            "fecha": fecha_iso,
            "seccion": seccion_norm,
            "query": query,
            "error": f"Sección inválida: '{seccion}'. Opciones: {', '.join(SECCIONES_VALIDAS)}.",
            "secciones_validas": list(SECCIONES_VALIDAS),
            "total": 0,
            "resultados": [],
            "citas": [],
            "advertencias": [aviso_conector("Sección inválida", "Especifique una sección del Diario Oficial.")],
            "desde_cache": False,
            "sin_fuente_verificable": True,
        }

    limite_seg = max(1, min(int(limite or 15), 100))
    carpeta = cache_dir or CACHE_DIR
    sufijo_sec = "empresas" if seccion_norm == "empresas_sociedades" else "sumario"
    ruta_cache = os.path.join(carpeta, f"do_{fecha_iso}_{sufijo_sec}.json")

    copia = _leer_cache(ruta_cache)
    if copia is not None:
        fresco = cache_fresco(ruta_cache, TTL_CACHE_SEGUNDOS)
        if solo_cache or fresco:
            base = dict(copia)
            base["desde_cache"] = True
            if not fresco:
                base["copia_local_vencida"] = True
                base["advertencias"] = list(base.get("advertencias") or []) + [
                    aviso_conector(
                        "Copia local vencida (solo caché)",
                        f"Se entrega edición local vencida del {fecha_iso} sin consultar la red.",
                    )
                ]
            return _filtrar_y_armar_respuesta(base, seccion_norm, query, limite_seg)

    if solo_cache:
        return {
            "fuente": "Diario Oficial de la República de Chile",
            "fecha": fecha_iso,
            "edicion": "",
            "seccion": seccion_norm,
            "query": query,
            "total": 0,
            "resultados": [],
            "citas": [],
            "advertencias": [
                aviso_conector(
                    "Sin copia en caché",
                    f"Modo solo_cache activo y no existe edición cacheada para {fecha_iso}.",
                )
            ],
            "desde_cache": False,
            "sin_fuente_verificable": True,
        }

    if seccion_norm == "empresas_sociedades":
        urls = [
            f"{BASE_DIARIO_OFICIAL}/edicionelectronica/empresas_cooperativas.php?date={urllib.parse.quote(fecha_dmy)}",
            f"{BASE_DIARIO_OFICIAL}/edicionelectronica/index.php?date={urllib.parse.quote(fecha_dmy)}",
        ]
    else:
        urls = [
            f"{BASE_DIARIO_OFICIAL}/edicionelectronica/index.php?date={urllib.parse.quote(fecha_dmy)}",
        ]

    errores: List[str] = []
    items_edicion: List[Dict[str, Any]] = []
    edicion_num = ""
    fuente_ok = False
    sec_def = "empresas_sociedades" if seccion_norm == "empresas_sociedades" else "normas_generales"

    for url in urls:
        raw_bytes: Optional[bytes] = None
        try:
            raw_bytes = _http_get_bytes(url, headers={"Accept": "application/json, text/html"}, timeout=20.0)
        except Exception as exc:
            errores.append(f"{url.split('?')[0]}: {str(exc)[:100]}")
        if raw_bytes is None:
            continue

        texto_resp = raw_bytes.decode("utf-8", errors="ignore").strip()
        if not texto_resp:
            errores.append(f"Respuesta vacía en {url.split('?')[0]}")
            continue

        if texto_resp.startswith("{") or texto_resp.startswith("["):
            try:
                data_json = json.loads(texto_resp)
                items_edicion, edicion_num = _parsear_json_do(data_json, fecha_iso, fecha_dmy, sec_def)
                fuente_ok = True
                break
            except ValueError as exc:
                errores.append(f"JSON inválido en Diario Oficial: {exc}")
                continue
        else:
            items_edicion, edicion_num = _parsear_html_do(texto_resp, fecha_iso, fecha_dmy, sec_def)
            fuente_ok = True
            if items_edicion:
                break

    if not fuente_ok:
        if copia is not None:
            base_v = dict(copia)
            base_v["desde_cache"] = True
            base_v["copia_local_vencida"] = True
            base_v["advertencias"] = list(base_v.get("advertencias") or []) + [
                aviso_conector(
                    "Fallo de red — copia local vencida",
                    f"No se pudo consultar el Diario Oficial ({'; '.join(errores[:2])}). Se entrega copia local vencida.",
                )
            ]
            return _filtrar_y_armar_respuesta(base_v, seccion_norm, query, limite_seg)

        return {
            "fuente": "Diario Oficial de la República de Chile",
            "fecha": fecha_iso,
            "edicion": "",
            "seccion": seccion_norm,
            "query": query,
            "total": 0,
            "resultados": [],
            "citas": [],
            "advertencias": [
                aviso_conector(
                    "Diario Oficial no disponible",
                    f"No se pudo obtener la edición del {fecha_iso} ({'; '.join(errores[:2])}).",
                )
            ],
            "error": "; ".join(errores[:2]) or "Sin respuesta del Diario Oficial",
            "desde_cache": False,
            "sin_fuente_verificable": True,
        }

    edicion_cacheada: Dict[str, Any] = {
        "fecha": fecha_iso,
        "edicion": edicion_num,
        "resultados": items_edicion,
        "advertencias": [],
        "desde_cache": False,
        "sin_fuente_verificable": False,
    }
    _guardar_cache(ruta_cache, edicion_cacheada)
    return _filtrar_y_armar_respuesta(edicion_cacheada, seccion_norm, query, limite_seg)
