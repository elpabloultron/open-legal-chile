"""
Open Legal Chile — Conector Oficial Tribunales Tributarios y Aduaneros (TTA).
Consulta el repositorio público de sentencias jurisdiccionales de los TTA (OJV TTA) y
fallos relevantes en tta.cl sobre Código Tributario (D.L. N.° 830) y Ley N.° 21.713.
"""

import hashlib
import json
import os
import re
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

import config
from citas_legales import formatear_cita

OJV_TTA_API_URL = "https://ojv.tta.cl/api/sentencias/jurisprudenciales"
TTA_WP_FALLOS_URL = "https://www.tta.cl/wp-json/wp/v2/posts"
OJV_TTA_PORTAL_URL = "https://ojv.tta.cl/#/instituciones/jurisprudencia"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "tta_cache")
_TTL_CACHE_SEGUNDOS = 7 * 24 * 60 * 60
_MAX_CACHE_RAM = 32

_STOPWORDS = frozenset({
    "al", "con", "de", "del", "el", "en", "la", "las", "ley", "lo", "los",
    "para", "por", "que", "se", "sin", "sobre", "su", "sus", "un", "una", "y",
})

_CACHE_RAM: Dict[str, Tuple[int, int, List[Dict[str, Any]]]] = {}


def _leer_cache_lista(ruta_cache: str, ttl_segundos: float) -> Tuple[Optional[List[Dict[str, Any]]], bool]:
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


def _guardar_cache_lista(ruta_cache: str, items: List[Dict[str, Any]]) -> None:
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
        config.registrar_tiempo("tta.cache_stat_error", 0.0)
        _ = exc


def _normalizar_sentencia_ojv(raw: Dict[str, Any]) -> Dict[str, Any]:
    rit = str(raw.get("RIT") or raw.get("rit") or "").strip()
    ruc = str(raw.get("RUC") or raw.get("ruc") or "").strip()
    fecha = str(raw.get("FECHA_SENTENCIA") or raw.get("fecha_sentencia") or raw.get("fecha") or "").strip()
    anio = str(raw.get("ANO") or raw.get("anio") or "").strip()
    if not anio and fecha:
        m_anio = re.search(r"\b(20\d{2}|19\d{2})\b", fecha)
        if m_anio:
            anio = m_anio.group(1)

    tribunal = str(raw.get("TRIBUNAL") or raw.get("tribunal") or "").strip()
    materia = str(raw.get("MATERIA_PRINCIPAL") or raw.get("materia") or "").strip()
    proceso = str(raw.get("NOMBRE_PROCESO") or raw.get("procedimiento") or "").strip()
    extracto = str(raw.get("EXTRACTO") or raw.get("extracto") or "").strip()
    etiquetas = str(raw.get("ETIQUETAS") or raw.get("etiquetas") or "").strip().strip("'")
    servicio = str(raw.get("SIGLA_SERVICIO") or raw.get("servicio") or "SII").strip()
    expediente_id = str(raw.get("EXPEIENTE") or raw.get("EXPEDIENTE") or raw.get("id") or "").strip()

    titulo = str(raw.get("titulo") or "").strip()
    if not titulo:
        partes_tit = [p for p in (rit, materia or proceso, tribunal) if p]
        titulo = " — ".join(partes_tit) if partes_tit else "Sentencia TTA"

    url = str(raw.get("url") or raw.get("link") or OJV_TTA_PORTAL_URL).strip()
    texto_resumen = " · ".join(p for p in (materia, extracto, etiquetas) if p) or titulo

    return {
        "organismo": "TTA",
        "rit": rit,
        "ruc": ruc,
        "tribunal": tribunal,
        "anio": anio,
        "fecha": fecha,
        "servicio": servicio,
        "procedimiento": proceso,
        "materia": materia,
        "etiquetas": etiquetas,
        "extracto": extracto,
        "titulo": titulo,
        "expediente_id": expediente_id,
        "url": url,
        "texto": texto_resumen,
        "normas_relacionadas": ["D.L. N.° 830 (Código Tributario)", "Ley N.° 20.322", "Ley N.° 21.713"],
    }


def _normalizar_post_wp(raw: Dict[str, Any]) -> Dict[str, Any]:
    raw_titulo = raw.get("title", {})
    titulo = config.texto_plano(raw_titulo.get("rendered", "") if isinstance(raw_titulo, dict) else str(raw_titulo))
    raw_exc = raw.get("excerpt", {})
    extracto = config.texto_plano(raw_exc.get("rendered", "") if isinstance(raw_exc, dict) else str(raw_exc))
    fecha = str(raw.get("date") or "")[:10]
    anio = fecha[:4] if len(fecha) >= 4 else ""
    link = str(raw.get("link") or "https://www.tta.cl/fallos_relevantes/").strip()

    m_rit = re.search(r"\b([A-Z]{1,3}-\d{1,2}-\d{3,6}-\d{4})\b", f"{titulo} {extracto}")
    rit = m_rit.group(1) if m_rit else f"TTA-{raw.get('id', 'fallo')}"
    m_trib = re.search(r"(Tribunal Tributario y Aduanero[^.,;]+|TTA[^.,;:]+)", f"{titulo} {extracto}", re.IGNORECASE)
    tribunal = m_trib.group(1).strip() if m_trib else "TTA"

    return {
        "organismo": "TTA",
        "rit": rit,
        "ruc": "",
        "tribunal": tribunal,
        "anio": anio,
        "fecha": fecha,
        "servicio": "SII/SNA",
        "procedimiento": "Reclamación Tributaria o Aduanera",
        "materia": titulo,
        "etiquetas": "",
        "extracto": extracto,
        "titulo": titulo or rit,
        "expediente_id": str(raw.get("id") or ""),
        "url": link,
        "texto": extracto or titulo,
        "normas_relacionadas": ["D.L. N.° 830 (Código Tributario)", "Ley N.° 20.322", "Ley N.° 21.713"],
    }


def _parsear_respuesta_tta(crudo: str) -> List[Dict[str, Any]]:
    datos = json.loads(crudo)
    if isinstance(datos, dict) and isinstance(datos.get("data"), list):
        return [_normalizar_sentencia_ojv(x) for x in datos["data"] if isinstance(x, dict)]
    if isinstance(datos, list):
        salida: List[Dict[str, Any]] = []
        for x in datos:
            if not isinstance(x, dict):
                continue
            if "RIT" in x or "MATERIA_PRINCIPAL" in x or "rit" in x:
                salida.append(_normalizar_sentencia_ojv(x))
            else:
                salida.append(_normalizar_post_wp(x))
        return salida
    return []


def _coincide_filtros(item: Dict[str, Any], query: str, tribunal: str, anio: str) -> int:
    if anio.strip():
        anio_limpio = anio.strip()
        if anio_limpio != str(item.get("anio") or "") and anio_limpio not in str(item.get("fecha") or ""):
            return 0

    if tribunal.strip():
        trib_st = config.sin_tildes(tribunal).strip().lower()
        campo_trib = config.sin_tildes(str(item.get("tribunal") or "")).lower()
        if trib_st not in campo_trib:
            return 0

    q = (query or "").strip()
    if not q:
        return 1

    cuerpo = (
        f"{item.get('rit', '')} {item.get('ruc', '')} {item.get('titulo', '')} "
        f"{item.get('materia', '')} {item.get('extracto', '')} {item.get('etiquetas', '')} "
        f"{item.get('procedimiento', '')} {item.get('tribunal', '')} {item.get('servicio', '')}"
    )
    cuerpo_st = config.sin_tildes(cuerpo).lower()
    q_st = config.sin_tildes(q).lower()

    patron_exacto = r"\b" + r"\s+".join(re.escape(p) for p in q_st.split()) + r"\b"
    if re.search(patron_exacto, cuerpo_st):
        return 3

    tokens = [t for t in re.findall(r"[a-z0-9.-]+", q_st) if len(t) >= 2 and t not in _STOPWORDS]
    if not tokens:
        return 0
    hits = sum(1 for tok in tokens if tok in cuerpo_st or tok.replace(".", "") in cuerpo_st.replace(".", ""))
    if hits == len(tokens):
        return 2
    if len(tokens) >= 2 and hits >= max(1, (len(tokens) + 1) // 2):
        return 1
    return 0


def _construir_cita_tta(item: Dict[str, Any]) -> Dict[str, str]:
    rit = str(item.get("rit") or item.get("ruc") or item.get("titulo") or "Sentencia TTA").strip()
    fecha = str(item.get("fecha") or "s/f").strip()
    ident = f"RIT {rit}, Fecha: {fecha}" if not rit.upper().startswith("RIT") else f"{rit}, Fecha: {fecha}"
    url = str(item.get("url") or OJV_TTA_PORTAL_URL)
    texto = str(item.get("texto") or item.get("extracto") or item.get("materia") or item.get("titulo") or "")[:900]
    return formatear_cita("TTA", ident, url=url, texto=texto)


def _consultar_red_tta(query: str, anio: str, limite: int) -> List[Dict[str, Any]]:
    params: Dict[str, str] = {
        "offset": "0",
        "limit": str(max(limite * 5, 50)),
    }
    if anio.strip().isdigit():
        params["ano"] = anio.strip()
    url_ojv = f"{OJV_TTA_API_URL}?{urllib.parse.urlencode(params)}"

    primer_error: Optional[Exception] = None
    try:
        crudo = config.pedir_http(url_ojv, headers={"Accept": "application/json"}, timeout=25.0).decode(
            "utf-8", errors="ignore"
        )
        sentencias = _parsear_respuesta_tta(crudo)
        if sentencias:
            return sentencias
    except Exception as exc:  # noqa: BLE001
        primer_error = exc

    wp_params: Dict[str, str] = {"categories": "86", "per_page": str(max(limite, 20))}
    if query.strip():
        wp_params["search"] = query.strip()
    url_wp = f"{TTA_WP_FALLOS_URL}?{urllib.parse.urlencode(wp_params)}"
    try:
        crudo_wp = config.pedir_http(url_wp, headers={"Accept": "application/json"}, timeout=25.0).decode(
            "utf-8", errors="ignore"
        )
        return _parsear_respuesta_tta(crudo_wp)
    except Exception as exc_wp:  # noqa: BLE001
        if primer_error is not None:
            raise primer_error from exc_wp
        raise


def tta_buscar_sentencias(
    query: str,
    tribunal: str = "",
    anio: str = "",
    limite: int = 10,
    solo_cache: bool = False,
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Busca sentencias de los Tribunales Tributarios y Aduaneros (TTA) con caché y citas."""
    limite_seguro = max(1, min(int(limite), 50))
    carpeta = cache_dir or CACHE_DIR
    clave_raw = f"{anio.strip()}|{tribunal.strip().lower()}|{query.strip().lower()}"
    clave_hash = hashlib.sha256(clave_raw.encode("utf-8")).hexdigest()[:16]
    ruta_cache = os.path.join(carpeta, f"tta_sentencias_{clave_hash}.json")

    items_cache, fresco = _leer_cache_lista(ruta_cache, _TTL_CACHE_SEGUNDOS)
    avisos: List[Dict[str, Any]] = []
    origen = "red"
    copia_vencida = False
    sin_fuente = False
    items_fuente: List[Dict[str, Any]] = []

    if items_cache is not None and fresco:
        items_fuente = items_cache
        origen = "cache"
    elif solo_cache:
        if items_cache is not None:
            items_fuente = items_cache
            origen = "cache_vencida"
            copia_vencida = True
            avisos.append(
                config.aviso_conector(
                    "Copia local vencida de sentencias TTA",
                    "Se utilizó la caché local expirada porque se solicitó solo_cache=True.",
                )
            )
        else:
            origen = "sin_datos"
            sin_fuente = True
            avisos.append(
                config.aviso_conector(
                    "Sin caché local de sentencias TTA",
                    "No existe copia local disponible y solo_cache=True impide consultar ojv.tta.cl.",
                )
            )
    else:
        t0 = time.perf_counter()
        try:
            items_fuente = _consultar_red_tta(query, anio, limite_seguro)
            config.registrar_tiempo("tta.red", time.perf_counter() - t0)
            if items_fuente:
                _guardar_cache_lista(ruta_cache, items_fuente)
            elif items_cache is not None:
                items_fuente = items_cache
                origen = "cache_vencida"
                copia_vencida = True
        except Exception as exc:  # noqa: BLE001
            config.registrar_tiempo("tta.error", time.perf_counter() - t0)
            if items_cache is not None:
                items_fuente = items_cache
                origen = "cache_vencida"
                copia_vencida = True
                avisos.append(
                    config.aviso_conector(
                        f"Portal TTA sin conexión ({type(exc).__name__})",
                        f"Se entrega copia local vencida tras error de red: {str(exc)[:140]}.",
                    )
                )
            else:
                origen = "sin_datos"
                sin_fuente = True
                avisos.append(
                    config.aviso_conector(
                        "No se pudo consultar el repositorio de sentencias TTA",
                        f"Los portales ojv.tta.cl y tta.cl no respondieron ({str(exc)[:140]}). Sin fuente verificable.",
                    )
                )

    candidatos: List[Tuple[int, Dict[str, Any]]] = []
    for item in items_fuente:
        score = _coincide_filtros(item, query, tribunal, anio)
        if score > 0:
            candidatos.append((score, item))

    candidatos.sort(key=lambda par: par[0], reverse=True)
    seleccionados: List[Dict[str, Any]] = []
    citas: List[Dict[str, str]] = []
    for _, item in candidatos[:limite_seguro]:
        cita = _construir_cita_tta(item)
        enriquecido = {**item, "cita": cita, "citas": [cita]}
        seleccionados.append(enriquecido)
        citas.append(cita)

    if not seleccionados and not sin_fuente and (query or "").strip():
        avisos.append(
            config.aviso_conector(
                f"Sin sentencias TTA para «{query}»",
                "No se encontraron fallos coincidentes con los filtros de materia, tribunal o año.",
            )
        )

    return {
        "organismo": "TTA",
        "query": query,
        "tribunal": tribunal,
        "anio": anio,
        "total": len(seleccionados),
        "resultados": seleccionados,
        "citas": citas,
        "fuentes_consultadas": [OJV_TTA_API_URL, TTA_WP_FALLOS_URL],
        "origen": origen,
        "copia_local_vencida": copia_vencida,
        "sin_fuente_verificable": sin_fuente,
        "avisos": avisos,
    }
