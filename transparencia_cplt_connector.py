"""
Open Legal Chile — Conector Oficial Consejo para la Transparencia (CPLT) e InfoLobby
Módulo para consultar amparos de acceso a la información pública (Ley N.° 20.285)
y registros públicos de audiencias, viajes, donativos y sujetos pasivos de la Ley
N.° 20.730 (InfoLobby / Datos Abiertos CPLT / CKAN / SPARQL).
"""

import csv
import hashlib
import io
import json
import os
import threading
from typing import Any, Dict, List, Optional, Tuple
import urllib.parse

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

BASE_CPLT_DATOS = "https://datosabiertos.cplt.cl"
BASE_PORTAL_TRANSPARENCIA = "https://www.portaltransparencia.cl"
BASE_LEYLOBBY_API = "https://www.leylobby.gob.cl/api/v1"
BASE_INFOLOBBY = "https://www.infolobby.cl"
BASE_INFOLOBBY_SPARQL = "https://datos.infolobby.cl/sparql"
BASE_DATOS_GOB = "https://datos.gob.cl"

CACHE_DIR = os.path.join(os.path.dirname(__file__), "transparencia_cplt_cache")
TTL_CACHE_SEGUNDOS = 7 * 24 * 60 * 60

TIPOS_LOBBY_VALIDOS = ("audiencias", "viajes", "donativos", "sujetos_pasivos")

_PEDIR_HTTP_BASE = pedir_http
_MEM_LOCK = threading.Lock()
_MEM_CACHE: Dict[str, Tuple[int, int, Dict[str, Any]]] = {}


def _http_get_bytes(url: str, headers: Optional[Dict[str, str]] = None, timeout: float = 20.0) -> bytes:
    """Ejecuta GET HTTP mediante `pedir_http` del módulo o de `config`."""
    fn = pedir_http if pedir_http is not _PEDIR_HTTP_BASE else config.pedir_http
    if headers:
        return fn(url, headers=headers, timeout=timeout)
    return fn(url, timeout=timeout)


def _clave_cache(prefijo: str, partes: List[str]) -> str:
    huella = hashlib.sha256(json.dumps(partes, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
    return f"{prefijo}_{huella}.json"


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


def _limpiar(valor: Any) -> str:
    return texto_plano(str(valor)) if valor is not None else ""


def _coincide_texto(haystack: str, needle: str) -> bool:
    if not needle.strip():
        return True
    h_norm = sin_tildes(haystack).lower()
    tokens = [t for t in sin_tildes(needle).lower().split() if t]
    return all(tok in h_norm for tok in tokens)


def _valor_sparql(binding: Dict[str, Any], *claves: str) -> str:
    for cl in claves:
        celda = binding.get(cl)
        if isinstance(celda, dict) and celda.get("value"):
            return _limpiar(celda["value"])
        if isinstance(celda, str) and celda.strip():
            return _limpiar(celda)
    return ""


def _parsear_csv_dicts(raw_text: str) -> List[Dict[str, Any]]:
    muestra = raw_text[:2048]
    delim = ";" if muestra.count(";") > muestra.count(",") else ","
    lector = csv.DictReader(io.StringIO(raw_text), delimiter=delim)
    return [dict(fila) for fila in lector if any(str(v or "").strip() for v in fila.values())]


def _extraer_filas_genericas(
    raw_bytes: bytes,
    errores: List[str],
    profundidad: int = 0,
) -> Tuple[List[Dict[str, Any]], bool]:
    """Parsea respuestas CKAN (records o recursos), SPARQL JSON, REST JSON o CSV."""
    texto = raw_bytes.decode("utf-8", errors="ignore").lstrip("\ufeff").strip()
    if not texto:
        return [], False

    if texto.startswith("{") or texto.startswith("["):
        try:
            data = json.loads(texto)
        except ValueError as exc:
            errores.append(f"JSON inválido: {exc}")
            return [], False

        if isinstance(data, list):
            return [r for r in data if isinstance(r, dict)], True

        if not isinstance(data, dict):
            return [], False

        # SPARQL JSON (`datos.infolobby.cl/sparql`)
        results_sparql = data.get("results")
        if isinstance(results_sparql, dict) and isinstance(results_sparql.get("bindings"), list):
            filas_sp = []
            for b in results_sparql["bindings"]:
                if isinstance(b, dict):
                    filas_sp.append({k: (v.get("value") if isinstance(v, dict) else v) for k, v in b.items()})
            return filas_sp, True

        # CKAN datastore_search / package_search
        res_ckan = data.get("result")
        if isinstance(res_ckan, dict):
            if isinstance(res_ckan.get("records"), list):
                return [r for r in res_ckan["records"] if isinstance(r, dict)], True
            if isinstance(res_ckan.get("results"), list):
                paquetes = [r for r in res_ckan["results"] if isinstance(r, dict)]
                # Si es un listado de paquetes CKAN con resources JSON/CSV, intentamos descargar el primero
                if profundidad == 0:
                    for pkg in paquetes:
                        for rec in pkg.get("resources") or []:
                            if not isinstance(rec, dict):
                                continue
                            fmt = str(rec.get("format") or "").upper()
                            rec_url = str(rec.get("url") or "").strip()
                            if rec_url.startswith("http") and fmt in ("JSON", "CSV", ""):
                                try:
                                    sub_bytes = _http_get_bytes(rec_url, timeout=20.0)
                                    sub_filas, ok_sub = _extraer_filas_genericas(sub_bytes, errores, profundidad=1)
                                    if ok_sub and sub_filas:
                                        return sub_filas, True
                                except Exception as exc:
                                    errores.append(f"Recurso CKAN {rec_url}: {str(exc)[:80]}")
                return paquetes, True

        for clave in ("resultados", "amparos", "audiencias", "viajes", "donativos", "sujetos_pasivos", "data", "items"):
            cand = data.get(clave)
            if isinstance(cand, list):
                return [r for r in cand if isinstance(r, dict)], True

        return [], True

    # CSV fallback
    if "," in texto or ";" in texto:
        filas_csv = _parsear_csv_dicts(texto)
        if filas_csv:
            return filas_csv, True

    return [], False


def _normalizar_amparo(reg: Dict[str, Any]) -> Dict[str, Any]:
    rol = _limpiar(
        reg.get("rol")
        or reg.get("Rol")
        or reg.get("codigo")
        or reg.get("id_caso")
        or reg.get("numero_amparo")
        or reg.get("id")
    )
    organismo = _limpiar(
        reg.get("organismo")
        or reg.get("Organismo")
        or reg.get("institucion")
        or reg.get("sujeto_obligado")
        or reg.get("reclamado")
    )
    estado = _limpiar(reg.get("estado") or reg.get("Estado") or reg.get("estado_tramitacion"))
    decision = _limpiar(reg.get("decision") or reg.get("Decision") or reg.get("resultado") or reg.get("tipo_decision"))
    fecha = _limpiar(
        reg.get("fecha_decision")
        or reg.get("fecha_ingreso")
        or reg.get("fecha")
        or reg.get("Fecha")
    )[:10]
    materia = _limpiar(
        reg.get("materia")
        or reg.get("Materia")
        or reg.get("resumen")
        or reg.get("descripcion")
        or reg.get("titulo")
        or reg.get("title")
    )
    descripcion = _limpiar(reg.get("descripcion") or reg.get("extracto") or reg.get("notes") or materia)
    url = _limpiar(reg.get("url") or reg.get("link") or reg.get("enlace"))
    if not url:
        if rol:
            url = f"{BASE_PORTAL_TRANSPARENCIA}/portal/casos/amparos?rol={urllib.parse.quote(rol)}"
        else:
            url = f"{BASE_CPLT_DATOS}/"

    texto_cita = f"Amparo Rol {rol or 's/n'} — Organismo: {organismo or 'N/D'} — Estado: {estado or decision or 'N/D'}. {materia}"
    cita = formatear_cita("CPLT", f"Amparo Rol {rol or 's/n'}", url=url, texto=texto_cita[:900])

    return {
        "rol": rol,
        "organismo": organismo,
        "estado": estado,
        "decision": decision,
        "fecha": fecha,
        "materia": materia,
        "descripcion": descripcion,
        "url": url,
        "citas": [cita],
    }


def _normalizar_lobby(reg: Dict[str, Any], tipo: str) -> Dict[str, Any]:
    etiquetas = {
        "audiencias": "Audiencia",
        "viajes": "Viaje",
        "donativos": "Donativo",
        "sujetos_pasivos": "Sujeto Pasivo",
    }
    etiqueta = etiquetas.get(tipo, "Registro")
    ident = _limpiar(
        reg.get("identificador")
        or reg.get("id")
        or reg.get("codigo")
        or reg.get("audiencia_id")
        or _valor_sparql(reg, "audiencia", "viaje", "donativo", "sujeto")
    )
    institucion = _limpiar(
        reg.get("institucion")
        or reg.get("Institucion")
        or reg.get("organismo")
        or reg.get("servicio")
        or reg.get("sujeto_pasivo_institucion")
        or _valor_sparql(reg, "institucion", "organismo")
    )
    sujeto_pasivo = _limpiar(
        reg.get("sujeto_pasivo")
        or reg.get("nombre_sujeto_pasivo")
        or reg.get("autoridad")
        or reg.get("nombre")
        or _valor_sparql(reg, "sujeto_pasivo", "autoridad", "nombre")
    )
    cargo = _limpiar(reg.get("cargo_sujeto_pasivo") or reg.get("cargo") or _valor_sparql(reg, "cargo"))
    sujeto_activo = _limpiar(
        reg.get("sujeto_activo")
        or reg.get("asistentes")
        or reg.get("lobista")
        or reg.get("donante")
        or reg.get("financista")
        or _valor_sparql(reg, "sujeto_activo", "lobista", "asistentes")
    )
    materia = _limpiar(
        reg.get("materia")
        or reg.get("materia_tratada")
        or reg.get("objeto")
        or reg.get("destino")
        or reg.get("descripcion")
        or _valor_sparql(reg, "materia", "objeto", "destino", "descripcion")
    )
    fecha = _limpiar(
        reg.get("fecha")
        or reg.get("fecha_audiencia")
        or reg.get("fecha_inicio")
        or reg.get("fecha_recepcion")
        or _valor_sparql(reg, "fecha")
    )[:10]
    detalle = _limpiar(reg.get("detalle") or reg.get("observaciones") or reg.get("lugar") or materia)
    url = _limpiar(reg.get("url") or reg.get("link"))
    if not url:
        url = f"{BASE_INFOLOBBY}/"

    sufijo_cita = ident or f"{sujeto_pasivo or institucion or 'registro'} ({fecha or 's/f'})"
    texto_cita = (
        f"{etiqueta} Ley N.° 20.730 — Institución: {institucion or 'N/D'} — "
        f"Sujeto pasivo: {sujeto_pasivo or 'N/D'} — Materia: {materia or detalle or 'N/D'}"
    )
    cita = formatear_cita("InfoLobby", f"{etiqueta} {sufijo_cita}", url=url, texto=texto_cita[:900])

    return {
        "identificador": ident,
        "tipo": tipo,
        "institucion": institucion,
        "sujeto_pasivo": sujeto_pasivo,
        "cargo_sujeto_pasivo": cargo,
        "sujeto_activo": sujeto_activo,
        "materia": materia,
        "fecha": fecha,
        "detalle": detalle,
        "url": url,
        "citas": [cita],
    }


def _consultar_con_cache(
    prefijo: str,
    partes_clave: List[str],
    urls: List[str],
    solo_cache: bool,
    cache_dir: Optional[str],
    fuente_nombre: str,
    limite: int,
    normalizador: Any,
    filtrador: Any,
    extra_meta: Dict[str, Any],
) -> Dict[str, Any]:
    carpeta = cache_dir or CACHE_DIR
    ruta_cache = os.path.join(carpeta, _clave_cache(prefijo, partes_clave))

    copia = _leer_cache(ruta_cache)
    if copia is not None:
        fresco = cache_fresco(ruta_cache, TTL_CACHE_SEGUNDOS)
        if solo_cache or fresco:
            res_c = dict(copia)
            res_c["resultados"] = list(copia.get("resultados") or [])[:limite]
            res_c["total"] = len(res_c["resultados"])
            res_c["desde_cache"] = True
            if not fresco:
                res_c["copia_local_vencida"] = True
                res_c["advertencias"] = list(res_c.get("advertencias") or []) + [
                    aviso_conector(
                        "Copia local vencida (solo caché)",
                        f"Se entrega copia local vencida de {fuente_nombre} sin consultar la red.",
                    )
                ]
            return res_c

    if solo_cache:
        return {
            **extra_meta,
            "fuente": fuente_nombre,
            "total": 0,
            "resultados": [],
            "citas": [],
            "advertencias": [
                aviso_conector(
                    "Sin copia en caché",
                    f"Modo solo_cache activo y no existe copia local de {fuente_nombre} para esta consulta.",
                )
            ],
            "desde_cache": False,
            "sin_fuente_verificable": True,
        }

    errores: List[str] = []
    filas_brutas: List[Dict[str, Any]] = []
    fuente_ok = False
    for url in urls:
        raw_bytes: Optional[bytes] = None
        try:
            raw_bytes = _http_get_bytes(url, headers={"Accept": "application/json, text/csv"}, timeout=20.0)
        except Exception as exc:
            errores.append(f"{url.split('?')[0]}: {str(exc)[:100]}")
        if raw_bytes is None:
            continue

        filas, ok_formato = _extraer_filas_genericas(raw_bytes, errores)
        if ok_formato:
            fuente_ok = True
            if filas:
                filas_brutas = filas
                break

    if not fuente_ok:
        if copia is not None:
            res_v = dict(copia)
            res_v["resultados"] = list(copia.get("resultados") or [])[:limite]
            res_v["total"] = len(res_v["resultados"])
            res_v["desde_cache"] = True
            res_v["copia_local_vencida"] = True
            res_v["advertencias"] = list(res_v.get("advertencias") or []) + [
                aviso_conector(
                    "Fallo de red — copia local vencida",
                    f"No se pudo conectar a {fuente_nombre} ({'; '.join(errores[:2])}). Se entrega copia local vencida.",
                )
            ]
            return res_v

        return {
            **extra_meta,
            "fuente": fuente_nombre,
            "total": 0,
            "resultados": [],
            "citas": [],
            "advertencias": [
                aviso_conector(
                    f"Fuente {fuente_nombre} no disponible",
                    f"No se pudieron obtener datos de {fuente_nombre} ({'; '.join(errores[:2])}).",
                )
            ],
            "error": "; ".join(errores[:2]) or f"Sin respuesta de {fuente_nombre}",
            "desde_cache": False,
            "sin_fuente_verificable": True,
        }

    normalizados = [normalizador(f) for f in filas_brutas]
    filtrados_todos = filtrador(normalizados)
    filtrados = filtrados_todos[:limite]
    citas: List[Dict[str, str]] = []
    for item in filtrados:
        citas.extend(item.get("citas") or [])

    advertencias: List[Dict[str, Any]] = []
    if not filtrados:
        advertencias.append(
            aviso_conector(
                f"Sin coincidencias en {fuente_nombre}",
                "La fuente oficial respondió correctamente, pero no hubo registros coincidentes con los filtros.",
            )
        )

    a_guardar: Dict[str, Any] = {
        **extra_meta,
        "fuente": fuente_nombre,
        "total": len(filtrados_todos),
        "resultados": filtrados_todos,
        "citas": [c for it in filtrados_todos for c in (it.get("citas") or [])],
        "advertencias": advertencias,
        "desde_cache": False,
        "sin_fuente_verificable": False,
    }
    _guardar_cache(ruta_cache, a_guardar)

    return {
        **extra_meta,
        "fuente": fuente_nombre,
        "total": len(filtrados),
        "resultados": filtrados,
        "citas": citas,
        "advertencias": advertencias,
        "desde_cache": False,
        "sin_fuente_verificable": False,
    }


def cplt_buscar_amparos(
    query: str,
    organismo: str = "",
    estado: str = "",
    limite: int = 10,
    solo_cache: bool = False,
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Busca decisiones y amparos de acceso a la información pública en el CPLT (Ley N.° 20.285)."""
    limite_seg = max(1, min(int(limite or 10), 100))
    q_api = " ".join(p for p in (query.strip(), organismo.strip(), estado.strip()) if p) or "amparos"
    urls = [
        f"{BASE_CPLT_DATOS}/api/3/action/datastore_search?q={urllib.parse.quote(q_api)}&limit={max(30, limite_seg * 3)}",
        f"{BASE_CPLT_DATOS}/api/3/action/package_search?q={urllib.parse.quote('amparos ' + q_api)}&rows=5",
        f"{BASE_DATOS_GOB}/api/3/action/package_search?q={urllib.parse.quote('consejo para la transparencia amparos ' + q_api)}&rows=5",
    ]

    def _filtrar(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for it in items:
            if organismo.strip() and not _coincide_texto(it.get("organismo", ""), organismo):
                continue
            if estado.strip() and not _coincide_texto(f"{it.get('estado', '')} {it.get('decision', '')}", estado):
                continue
            if query.strip():
                texto_it = " ".join([
                    it.get("rol", ""),
                    it.get("organismo", ""),
                    it.get("estado", ""),
                    it.get("decision", ""),
                    it.get("materia", ""),
                    it.get("descripcion", ""),
                ])
                if not _coincide_texto(texto_it, query):
                    continue
            out.append(it)
        return out

    return _consultar_con_cache(
        prefijo="cplt_amparos",
        partes_clave=[query.strip().lower(), organismo.strip().lower(), estado.strip().lower()],
        urls=urls,
        solo_cache=solo_cache,
        cache_dir=cache_dir,
        fuente_nombre="Consejo para la Transparencia (CPLT)",
        limite=limite_seg,
        normalizador=_normalizar_amparo,
        filtrador=_filtrar,
        extra_meta={
            "marco_legal": "Ley N.° 20.285 sobre Acceso a la Información Pública",
            "query": query,
            "organismo": organismo,
            "estado": estado,
        },
    )


def cplt_buscar_lobby(
    query: str,
    tipo: str = "audiencias",
    institucion: str = "",
    limite: int = 10,
    solo_cache: bool = False,
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Busca registros públicos de la Ley del Lobby N.° 20.730 (InfoLobby / LeyLobby)."""
    tipo_norm = (tipo or "audiencias").strip().lower()
    if tipo_norm not in TIPOS_LOBBY_VALIDOS:
        return {
            "fuente": "InfoLobby / Consejo para la Transparencia (CPLT)",
            "marco_legal": "Ley N.° 20.730 que regula el Lobby",
            "tipo": tipo_norm,
            "error": f"Tipo no válido: '{tipo}'. Opciones: {', '.join(TIPOS_LOBBY_VALIDOS)}.",
            "tipos_validos": list(TIPOS_LOBBY_VALIDOS),
            "total": 0,
            "resultados": [],
            "citas": [],
            "advertencias": [aviso_conector("Parámetro inválido", "Especifique audiencias, viajes, donativos o sujetos_pasivos.")],
            "desde_cache": False,
            "sin_fuente_verificable": True,
        }

    limite_seg = max(1, min(int(limite or 10), 100))
    q_api = " ".join(p for p in (query.strip(), institucion.strip()) if p) or tipo_norm
    sparql_q = (
        "SELECT ?sujeto_pasivo ?institucion ?materia ?fecha WHERE { "
        "?s a ?t ; <http://www.w3.org/2000/01/rdf-schema#label> ?materia . "
        f"}} LIMIT {max(30, limite_seg * 3)}"
    )
    urls = [
        f"{BASE_LEYLOBBY_API}/{tipo_norm}?search={urllib.parse.quote(q_api)}&limit={max(30, limite_seg * 3)}",
        f"{BASE_CPLT_DATOS}/api/3/action/datastore_search?q={urllib.parse.quote(tipo_norm + ' ' + q_api)}&limit={max(30, limite_seg * 3)}",
        f"{BASE_INFOLOBBY_SPARQL}?query={urllib.parse.quote(sparql_q)}&format={urllib.parse.quote('application/sparql-results+json')}",
    ]

    def _filtrar(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for it in items:
            if institucion.strip() and not _coincide_texto(it.get("institucion", ""), institucion):
                continue
            if query.strip():
                texto_it = " ".join([
                    it.get("identificador", ""),
                    it.get("institucion", ""),
                    it.get("sujeto_pasivo", ""),
                    it.get("cargo_sujeto_pasivo", ""),
                    it.get("sujeto_activo", ""),
                    it.get("materia", ""),
                    it.get("detalle", ""),
                ])
                if not _coincide_texto(texto_it, query):
                    continue
            out.append(it)
        return out

    return _consultar_con_cache(
        prefijo=f"cplt_lobby_{tipo_norm}",
        partes_clave=[tipo_norm, query.strip().lower(), institucion.strip().lower()],
        urls=urls,
        solo_cache=solo_cache,
        cache_dir=cache_dir,
        fuente_nombre="InfoLobby / Consejo para la Transparencia (CPLT)",
        limite=limite_seg,
        normalizador=lambda reg: _normalizar_lobby(reg, tipo_norm),
        filtrador=_filtrar,
        extra_meta={
            "marco_legal": "Ley N.° 20.730 que regula el Lobby",
            "tipo": tipo_norm,
            "query": query,
            "institucion": institucion,
        },
    )
