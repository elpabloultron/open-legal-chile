"""
Open Legal Chile — Conector Oficial de Compras Públicas (ChileCompra / Mercado Público)
Módulo para consultar procesos de contratación pública bajo estándar OCDS y datos abiertos
de Mercado Público (`api.mercadopublico.cl`, `datos-abiertos.chilecompra.cl`), así como
realizar cruces preliminares de probidad e inhabilidades con InfoProbidad (Ley N.° 19.886,
Ley N.° 21.634, Ley N.° 20.880 y Ley N.° 18.575).
"""

from datetime import date
import hashlib
import json
import os
import re
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
from entes_publicos import validar_rut
import infoprobidad_connector

BASE_API_MP = "https://api.mercadopublico.cl"
BASE_API_OCDS = "https://api.mercadopublico.cl/APISOCDS/OCDS"
BASE_DATOS_CHILECOMPRA = "https://datos-abiertos.chilecompra.cl"
BASE_INFOPROBIDAD = "https://www.infoprobidad.cl"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "compras_publicas_cache")
TTL_CACHE_SEGUNDOS = 24 * 60 * 60

TIPOS_CONSULTA_VALIDOS = ("licitaciones", "ordenes_compra", "proveedores", "tratos_directos")

_URL_LEY_19886 = "https://www.bcn.cl/leychile/navegar?idNorma=213004"
_URL_LEY_18575 = "https://www.bcn.cl/leychile/navegar?idNorma=191865"
_URL_LEY_20880 = "https://www.bcn.cl/leychile/navegar?idNorma=1086062"

_PEDIR_HTTP_BASE = pedir_http
_INFOPROBIDAD_CLS_BASE = infoprobidad_connector.InfoProbidadClient
_INFOPROBIDAD_GET_BASE = infoprobidad_connector.InfoProbidadClient.get_declaracion

_MEM_LOCK = threading.Lock()
_MEM_CACHE: Dict[str, Tuple[int, int, Dict[str, Any]]] = {}


def _http_get_bytes(url: str, headers: Optional[Dict[str, str]] = None, timeout: float = 20.0) -> bytes:
    """Ejecuta GET HTTP usando `pedir_http` del módulo o de `config` (compatible con mocks)."""
    fn = pedir_http if pedir_http is not _PEDIR_HTTP_BASE else config.pedir_http
    if headers:
        return fn(url, headers=headers, timeout=timeout)
    return fn(url, timeout=timeout)


def _clave_cache(prefijo: str, partes: List[str]) -> str:
    crudo = json.dumps(partes, ensure_ascii=False)
    huella = hashlib.sha256(crudo.encode("utf-8")).hexdigest()[:16]
    return f"{prefijo}_{huella}.json"


def _leer_cache(ruta_cache: str, usar_cache: bool) -> Optional[Dict[str, Any]]:
    if not usar_cache:
        return None
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


def _obtener_ticket_opcional() -> str:
    return (os.getenv("MERCADOPUBLICO_TICKET") or os.getenv("CHILECOMPRA_TICKET") or "").strip()


def _limpiar_texto(valor: Any) -> str:
    return texto_plano(str(valor)) if valor is not None else ""


def _etiqueta_tipo(tipo: str) -> str:
    etiquetas = {
        "licitaciones": "Licitación Pública",
        "ordenes_compra": "Orden de Compra",
        "proveedores": "Proveedor del Estado",
        "tratos_directos": "Trato Directo",
    }
    return etiquetas.get(tipo, "Proceso de Compra Pública")


def _extraer_monto_y_moneda(obj: Any) -> Tuple[Optional[float], str]:
    if not isinstance(obj, dict):
        return None, "CLP"
    bruto = obj.get("amount") if obj.get("amount") is not None else obj.get("monto")
    moneda = str(obj.get("currency") or obj.get("moneda") or "CLP")
    if bruto is None:
        return None, moneda
    try:
        return float(bruto), moneda
    except (TypeError, ValueError):
        return None, moneda


def _normalizar_proveedores_ocds(release: Dict[str, Any]) -> List[Dict[str, str]]:
    proveedores: List[Dict[str, str]] = []
    vistos = set()
    for award in release.get("awards") or []:
        if not isinstance(award, dict):
            continue
        for sup in award.get("suppliers") or []:
            if not isinstance(sup, dict):
                continue
            nombre = _limpiar_texto(sup.get("name") or sup.get("nombre"))
            rut = _limpiar_texto(sup.get("id") or sup.get("rut"))
            clave = (nombre.lower(), rut.lower())
            if (nombre or rut) and clave not in vistos:
                vistos.add(clave)
                proveedores.append({"nombre": nombre, "rut": rut})
    for party in release.get("parties") or []:
        if not isinstance(party, dict):
            continue
        roles = [str(r).lower() for r in (party.get("roles") or [])]
        if "supplier" in roles or "tenderer" in roles:
            raw_ident = party.get("identifier")
            ident: Dict[str, Any] = raw_ident if isinstance(raw_ident, dict) else {}
            nombre = _limpiar_texto(party.get("name"))
            rut = _limpiar_texto(ident.get("id") or party.get("id"))
            clave = (nombre.lower(), rut.lower())
            if (nombre or rut) and clave not in vistos:
                vistos.add(clave)
                proveedores.append({"nombre": nombre, "rut": rut})
    return proveedores


def _normalizar_release_ocds(release: Dict[str, Any], tipo: str) -> Dict[str, Any]:
    raw_tender = release.get("tender")
    tender: Dict[str, Any] = raw_tender if isinstance(raw_tender, dict) else {}
    raw_buyer = release.get("buyer")
    buyer: Dict[str, Any] = raw_buyer if isinstance(raw_buyer, dict) else {}
    raw_awards = release.get("awards")
    awards = raw_awards if isinstance(raw_awards, list) else []
    raw_primer = awards[0] if awards else None
    primer_award: Dict[str, Any] = raw_primer if isinstance(raw_primer, dict) else {}

    ocid = _limpiar_texto(release.get("ocid"))
    codigo = _limpiar_texto(tender.get("id") or release.get("id") or ocid)
    titulo = _limpiar_texto(tender.get("title") or primer_award.get("title") or f"{_etiqueta_tipo(tipo)} {codigo}")
    descripcion = _limpiar_texto(tender.get("description") or primer_award.get("description"))
    estado = _limpiar_texto(tender.get("status") or primer_award.get("status"))
    modalidad = _limpiar_texto(tender.get("procurementMethodDetails") or tender.get("procurementMethod"))
    organismo = _limpiar_texto(buyer.get("name"))
    rut_org = _limpiar_texto(buyer.get("id"))
    fecha = _limpiar_texto(release.get("date") or primer_award.get("date"))[:10]

    monto, moneda = _extraer_monto_y_moneda(primer_award.get("value") or tender.get("value"))
    proveedores = _normalizar_proveedores_ocds(release)
    url = _limpiar_texto(release.get("url") or tender.get("url"))
    if not url and codigo:
        url = f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?qs={urllib.parse.quote(codigo)}"

    tipo_proc = _etiqueta_tipo(tipo)
    if modalidad and ("trato" in modalidad.lower() or "direct" in modalidad.lower()):
        tipo_proc = "Trato Directo"

    resumen = f"{titulo} — Organismo: {organismo or 'N/D'} — Estado: {estado or 'N/D'}"
    if proveedores:
        nombres_prov = ", ".join(p["nombre"] or p["rut"] for p in proveedores[:3])
        resumen += f" — Proveedor(es): {nombres_prov}"
    cita = formatear_cita("ChileCompra", f"{tipo_proc} {codigo or ocid or 's/n'}", url=url, texto=resumen[:900])

    return {
        "codigo": codigo,
        "ocid": ocid,
        "titulo": titulo,
        "descripcion": descripcion,
        "estado": estado,
        "tipo_proceso": tipo_proc,
        "modalidad": modalidad,
        "organismo": organismo,
        "rut_organismo": rut_org,
        "fecha": fecha,
        "monto": monto,
        "moneda": moneda,
        "proveedores": proveedores,
        "url": url,
        "citas": [cita],
    }


def _normalizar_registro_plano(item: Dict[str, Any], tipo: str) -> Dict[str, Any]:
    raw_comp = item.get("Comprador")
    comprador: Dict[str, Any] = raw_comp if isinstance(raw_comp, dict) else {}
    codigo = _limpiar_texto(
        item.get("CodigoExterno")
        or item.get("codigo")
        or item.get("ocid")
        or item.get("CodigoEmpresa")
        or item.get("id")
    )
    ocid = _limpiar_texto(item.get("ocid"))
    titulo = _limpiar_texto(
        item.get("Nombre")
        or item.get("titulo")
        or item.get("NombreEmpresa")
        or item.get("RazonSocial")
        or f"{_etiqueta_tipo(tipo)} {codigo}"
    )
    descripcion = _limpiar_texto(item.get("Descripcion") or item.get("descripcion") or item.get("Glosa"))
    estado = _limpiar_texto(item.get("Estado") or item.get("estado") or item.get("CodigoEstado"))
    organismo = _limpiar_texto(
        comprador.get("NombreOrganismo")
        or item.get("NombreOrganismo")
        or item.get("organismo")
        or item.get("Entidad")
    )
    rut_org = _limpiar_texto(comprador.get("RutUnidad") or item.get("RutOrganismo") or item.get("rut_organismo"))
    fecha = _limpiar_texto(item.get("FechaCierre") or item.get("FechaCreacion") or item.get("fecha"))[:10]
    monto, moneda = _extraer_monto_y_moneda(
        {"amount": item.get("MontoTotal") or item.get("monto"), "currency": item.get("Moneda") or "CLP"}
    )

    proveedores: List[Dict[str, str]] = []
    if isinstance(item.get("proveedores"), list):
        for p in item["proveedores"]:
            if isinstance(p, dict):
                proveedores.append({
                    "nombre": _limpiar_texto(p.get("nombre") or p.get("name")),
                    "rut": _limpiar_texto(p.get("rut") or p.get("id")),
                })
    else:
        nom_p = _limpiar_texto(item.get("Proveedor") or item.get("NombreEmpresa") or item.get("RazonSocial"))
        rut_p = _limpiar_texto(item.get("RutProveedor") or item.get("RutEmpresa") or item.get("rut_proveedor"))
        if nom_p or rut_p:
            proveedores.append({"nombre": nom_p, "rut": rut_p})

    url = _limpiar_texto(item.get("url") or item.get("link"))
    if not url and codigo:
        url = f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?qs={urllib.parse.quote(codigo)}"

    tipo_proc = _etiqueta_tipo(tipo)
    resumen = f"{titulo} — Organismo: {organismo or 'N/D'} — Estado: {estado or 'N/D'}"
    cita = formatear_cita("ChileCompra", f"{tipo_proc} {codigo or 's/n'}", url=url, texto=resumen[:900])

    return {
        "codigo": codigo,
        "ocid": ocid,
        "titulo": titulo,
        "descripcion": descripcion,
        "estado": estado,
        "tipo_proceso": tipo_proc,
        "modalidad": _limpiar_texto(item.get("Tipo") or item.get("modalidad") or tipo_proc),
        "organismo": organismo,
        "rut_organismo": rut_org,
        "fecha": fecha,
        "monto": monto,
        "moneda": moneda,
        "proveedores": proveedores,
        "url": url,
        "citas": [cita],
    }


def _extraer_items_respuesta(payload: Any, tipo: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if isinstance(payload, dict):
        if isinstance(payload.get("releases"), list):
            for rel in payload["releases"]:
                if isinstance(rel, dict):
                    items.append(_normalizar_release_ocds(rel, tipo))
            return items
        if isinstance(payload.get("records"), list):
            for rec in payload["records"]:
                if isinstance(rec, dict) and isinstance(rec.get("compiledRelease"), dict):
                    items.append(_normalizar_release_ocds(rec["compiledRelease"], tipo))
            return items
        for clave_lista in ("Listado", "resultados", "results", "data"):
            cand = payload.get(clave_lista)
            if isinstance(cand, list):
                for reg in cand:
                    if isinstance(reg, dict):
                        items.append(_normalizar_registro_plano(reg, tipo))
                return items
        res_ckan = payload.get("result")
        if isinstance(res_ckan, dict):
            recs = res_ckan.get("records") or res_ckan.get("results") or []
            if isinstance(recs, list):
                for reg in recs:
                    if isinstance(reg, dict):
                        items.append(_normalizar_registro_plano(reg, tipo))
                return items
    elif isinstance(payload, list):
        for reg in payload:
            if isinstance(reg, dict):
                if "tender" in reg or "ocid" in reg:
                    items.append(_normalizar_release_ocds(reg, tipo))
                else:
                    items.append(_normalizar_registro_plano(reg, tipo))
    return items


_RE_RUT_CAND = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dkK]\b")


def _normalizar_para_busqueda(texto: str) -> str:
    norm = sin_tildes(texto).lower()
    extras: List[str] = []
    for match in _RE_RUT_CAND.finditer(norm):
        sin_puntos = match.group(0).replace(".", "")
        extras.append(sin_puntos)
        extras.append(sin_puntos.replace("-", ""))
    return f"{norm} {' '.join(extras)}" if extras else norm


def _coincide_texto(haystack: str, needle: str) -> bool:
    if not needle.strip():
        return True
    h_norm = _normalizar_para_busqueda(haystack)
    tokens = [t for t in sin_tildes(needle).lower().split() if t]
    for tok in tokens:
        tok_cmp = tok.replace(".", "") if _RE_RUT_CAND.fullmatch(tok) else tok
        if tok_cmp not in h_norm and tok not in h_norm:
            return False
    return True


def _filtrar_items(
    items: List[Dict[str, Any]],
    query: str,
    organismo: str,
    codigo_licitacion: str,
    limite: int,
) -> List[Dict[str, Any]]:
    cod_buscado = codigo_licitacion.strip().lower()
    org_buscado = organismo.strip()
    q_buscada = query.strip()

    filtrados: List[Dict[str, Any]] = []
    for item in items:
        if cod_buscado:
            cod_item = f"{item.get('codigo', '')} {item.get('ocid', '')}".lower()
            if cod_buscado not in cod_item:
                continue
        if org_buscado and not _coincide_texto(item.get("organismo", ""), org_buscado):
            continue
        if q_buscada:
            prov_txt = " ".join(
                f"{p.get('nombre', '')} {p.get('rut', '')}" for p in (item.get("proveedores") or [])
            )
            cuerpo = " ".join([
                item.get("codigo", ""),
                item.get("ocid", ""),
                item.get("titulo", ""),
                item.get("descripcion", ""),
                item.get("organismo", ""),
                item.get("rut_organismo", ""),
                prov_txt,
            ])
            if not _coincide_texto(cuerpo, q_buscada):
                continue
        filtrados.append(item)
        if len(filtrados) >= limite:
            break
    return filtrados


def _construir_urls_busqueda(
    tipo: str,
    query: str,
    codigo_licitacion: str,
    limite: int,
) -> List[str]:
    hoy = date.today()
    tope = max(50, limite * 5)
    ticket = _obtener_ticket_opcional()
    urls: List[str] = []

    if ticket and codigo_licitacion.strip() and tipo in ("licitaciones", "ordenes_compra"):
        endpoint = "licitaciones.json" if tipo == "licitaciones" else "ordenesdecompra.json"
        urls.append(
            f"{BASE_API_MP}/servicios/v1/publico/{endpoint}"
            f"?codigo={urllib.parse.quote(codigo_licitacion.strip())}"
            f"&ticket={urllib.parse.quote(ticket)}"
        )
    if ticket and tipo == "proveedores" and query.strip():
        urls.append(
            f"{BASE_API_MP}/servicios/v1/publico/Empresas/BuscarProveedor"
            f"?rutempresaproveedor={urllib.parse.quote(query.strip())}"
            f"&ticket={urllib.parse.quote(ticket)}"
        )

    if tipo == "tratos_directos":
        urls.append(f"{BASE_API_OCDS}/listaOCDSAgnoMesTratoDirecto/{hoy.year}/{hoy.month:02d}/0/{tope}")
    else:
        urls.append(f"{BASE_API_OCDS}/listaOCDSAgnoMes/{hoy.year}/{hoy.month:02d}/0/{tope}")

    q_ckan = query.strip() or codigo_licitacion.strip() or tipo.replace("_", " ")
    urls.append(f"{BASE_DATOS_CHILECOMPRA}/api/3/action/package_search?q={urllib.parse.quote(q_ckan)}")
    return urls


def compras_publicas_buscar(
    query: str,
    tipo: str = "licitaciones",
    organismo: str = "",
    codigo_licitacion: str = "",
    limite: int = 10,
    solo_cache: bool = False,
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Busca procesos de contratación pública en Mercado Público / ChileCompra (OCDS y datos abiertos).

    Soporta ``tipo`` en ``("licitaciones", "ordenes_compra", "proveedores", "tratos_directos")``
    con caché en memoria y disco (TTL 24 h) y degradación honesta sin internet.
    """
    tipo_norm = (tipo or "licitaciones").strip().lower()
    if tipo_norm not in TIPOS_CONSULTA_VALIDOS:
        return {
            "fuente": "ChileCompra / Mercado Público",
            "tipo": tipo_norm,
            "error": f"Tipo de consulta no válido: '{tipo}'. Opciones: {', '.join(TIPOS_CONSULTA_VALIDOS)}.",
            "tipos_validos": list(TIPOS_CONSULTA_VALIDOS),
            "total": 0,
            "resultados": [],
            "citas": [],
            "advertencias": [aviso_conector("Parámetro inválido", "Especifique un tipo de búsqueda válido.")],
            "desde_cache": False,
            "sin_fuente_verificable": True,
        }

    limite_seg = max(1, min(int(limite or 10), 100))
    carpeta = cache_dir or CACHE_DIR
    ruta_cache = os.path.join(
        carpeta,
        _clave_cache("cp", [tipo_norm, query.strip().lower(), organismo.strip().lower(), codigo_licitacion.strip().lower()]),
    )

    copia = _leer_cache(ruta_cache, usar_cache=True)
    if copia is not None:
        fresco = cache_fresco(ruta_cache, TTL_CACHE_SEGUNDOS)
        if solo_cache or fresco:
            res_cache = dict(copia)
            res_cache["resultados"] = list(copia.get("resultados") or [])[:limite_seg]
            res_cache["total"] = len(res_cache["resultados"])
            res_cache["desde_cache"] = True
            if not fresco:
                res_cache["copia_local_vencida"] = True
                res_cache["advertencias"] = list(res_cache.get("advertencias") or []) + [
                    aviso_conector(
                        "Copia local vencida (solo caché)",
                        "Se entrega copia local vencida de ChileCompra sin consultar la red.",
                    )
                ]
            return res_cache

    if solo_cache:
        return {
            "fuente": "ChileCompra / Mercado Público",
            "tipo": tipo_norm,
            "query": query,
            "organismo": organismo,
            "codigo_licitacion": codigo_licitacion,
            "total": 0,
            "resultados": [],
            "citas": [],
            "advertencias": [
                aviso_conector(
                    "Sin copia en caché",
                    "Modo solo_cache activo y no existe copia local para esta consulta en ChileCompra.",
                )
            ],
            "desde_cache": False,
            "sin_fuente_verificable": True,
        }

    urls = _construir_urls_busqueda(tipo_norm, query, codigo_licitacion, limite_seg)
    errores: List[str] = []
    crudos_totales: List[Dict[str, Any]] = []
    fuente_exitosa = False

    for url in urls:
        raw_bytes: Optional[bytes] = None
        try:
            raw_bytes = _http_get_bytes(url, headers={"Accept": "application/json"}, timeout=20.0)
        except Exception as exc:
            errores.append(f"{url.split('?')[0]}: {str(exc)[:100]}")
        if raw_bytes is None:
            continue

        try:
            payload = json.loads(raw_bytes.decode("utf-8", errors="ignore"))
        except ValueError as exc:
            errores.append(f"Respuesta JSON inválida en {url.split('?')[0]}: {exc}")
            continue

        extraidos = _extraer_items_respuesta(payload, tipo_norm)
        fuente_exitosa = True
        if extraidos:
            crudos_totales = extraidos
            break

    if not fuente_exitosa:
        if copia is not None:
            res_vencido = dict(copia)
            res_vencido["resultados"] = list(copia.get("resultados") or [])[:limite_seg]
            res_vencido["total"] = len(res_vencido["resultados"])
            res_vencido["desde_cache"] = True
            res_vencido["copia_local_vencida"] = True
            res_vencido["advertencias"] = list(res_vencido.get("advertencias") or []) + [
                aviso_conector(
                    "Fallo de red — copia local vencida",
                    f"No se pudo actualizar desde ChileCompra ({'; '.join(errores[:2])}). Se entrega copia local vencida.",
                )
            ]
            return res_vencido

        return {
            "fuente": "ChileCompra / Mercado Público",
            "tipo": tipo_norm,
            "query": query,
            "organismo": organismo,
            "codigo_licitacion": codigo_licitacion,
            "total": 0,
            "resultados": [],
            "citas": [],
            "advertencias": [
                aviso_conector(
                    "Fuente ChileCompra no disponible",
                    f"No se pudo conectar con Mercado Público / ChileCompra ({'; '.join(errores[:2])}).",
                )
            ],
            "error": "; ".join(errores[:2]) or "Sin respuesta de ChileCompra",
            "desde_cache": False,
            "sin_fuente_verificable": True,
        }

    filtrados_todos = _filtrar_items(crudos_totales, query, organismo, codigo_licitacion, max(limite_seg, 100))
    filtrados = filtrados_todos[:limite_seg]
    citas: List[Dict[str, str]] = []
    for item in filtrados:
        citas.extend(item.get("citas") or [])

    advertencias: List[Dict[str, Any]] = []
    if not filtrados:
        advertencias.append(
            aviso_conector(
                "Sin coincidencias en ChileCompra",
                "La fuente oficial respondió correctamente, pero no registró procesos coincidentes con los filtros.",
            )
        )

    a_guardar: Dict[str, Any] = {
        "fuente": "ChileCompra / Mercado Público",
        "tipo": tipo_norm,
        "query": query,
        "organismo": organismo,
        "codigo_licitacion": codigo_licitacion,
        "total": len(filtrados_todos),
        "resultados": filtrados_todos,
        "citas": [c for it in filtrados_todos for c in (it.get("citas") or [])],
        "advertencias": advertencias,
        "desde_cache": False,
        "sin_fuente_verificable": False,
    }
    _guardar_cache(ruta_cache, a_guardar)

    return {
        "fuente": "ChileCompra / Mercado Público",
        "tipo": tipo_norm,
        "query": query,
        "organismo": organismo,
        "codigo_licitacion": codigo_licitacion,
        "total": len(filtrados),
        "resultados": filtrados,
        "citas": citas,
        "advertencias": advertencias,
        "desde_cache": False,
        "sin_fuente_verificable": False,
    }


def _consultar_infoprobidad_seguro(
    termino: str,
    solo_cache: bool,
    carpeta_cache: str,
) -> Dict[str, Any]:
    """Consulta InfoProbidad usando `InfoProbidadClient` si fue mockeado o `pedir_http` con caché."""
    cliente_cls = infoprobidad_connector.InfoProbidadClient
    cls_modificada = (
        cliente_cls is not _INFOPROBIDAD_CLS_BASE
        or cliente_cls.get_declaracion is not _INFOPROBIDAD_GET_BASE
    )
    if cls_modificada and not solo_cache:
        try:
            cliente = cliente_cls()
            dip = cliente.get_declaracion(termino)
            if isinstance(dip, dict) and not dip.get("error"):
                return {"ok": True, "declaraciones": [dip], "desde_cache": False}
            return {
                "ok": False,
                "declaraciones": [],
                "error": (dip or {}).get("error", "Sin declaración encontrada en InfoProbidad."),
            }
        except Exception as exc:
            return {"ok": False, "declaraciones": [], "error": str(exc)}

    ruta_dip = os.path.join(carpeta_cache, _clave_cache("dip", [termino.lower()]))
    copia = _leer_cache(ruta_dip, usar_cache=True)
    if copia is not None:
        fresco = cache_fresco(ruta_dip, TTL_CACHE_SEGUNDOS)
        if solo_cache or fresco:
            res = dict(copia)
            res["desde_cache"] = True
            if not fresco:
                res["copia_local_vencida"] = True
            return res

    if solo_cache:
        return {
            "ok": False,
            "declaraciones": [],
            "error": "Modo solo_cache sin copia local de InfoProbidad.",
        }

    url = f"{BASE_INFOPROBIDAD}/Declaracion/BuscarDeclaracion?busqueda={urllib.parse.quote(termino)}"
    try:
        raw_bytes = _http_get_bytes(url, headers={"Accept": "text/html,application/json"}, timeout=20.0)
    except Exception as exc:
        if copia is not None:
            res_v = dict(copia)
            res_v["desde_cache"] = True
            res_v["copia_local_vencida"] = True
            res_v["advertencia"] = str(exc)
            return res_v
        return {"ok": False, "declaraciones": [], "error": str(exc)}

    texto_resp = raw_bytes.decode("utf-8", errors="ignore").strip()
    declaraciones: List[Dict[str, Any]] = []
    if texto_resp.startswith("{") or texto_resp.startswith("["):
        try:
            data_json = json.loads(texto_resp)
            if isinstance(data_json, dict):
                lista = data_json.get("declaraciones") or data_json.get("resultados") or [data_json]
                declaraciones = [d for d in lista if isinstance(d, dict) and not d.get("error")]
            elif isinstance(data_json, list):
                declaraciones = [d for d in data_json if isinstance(d, dict)]
        except ValueError:
            declaraciones = []
    else:
        parsed = infoprobidad_connector.InfoProbidadClient().parse_html_string(texto_resp, ident=termino)
        if isinstance(parsed, dict) and not parsed.get("error"):
            tiene_datos = parsed.get("total_secciones", 0) > 0 or parsed.get("declarante") != "Declarante Desconocido"
            if tiene_datos:
                declaraciones = [parsed]

    resultado = {"ok": True, "declaraciones": declaraciones, "url": url}
    _guardar_cache(ruta_dip, resultado)
    return resultado


def _aplanar_texto_dip(dip: Dict[str, Any]) -> str:
    partes = [str(dip.get("declarante") or "")]
    for k, v in (dip.get("metadatos") or {}).items():
        partes.append(f"{k} {v}")
    for sec_nom, filas in (dip.get("secciones") or {}).items():
        partes.append(str(sec_nom))
        if isinstance(filas, list):
            for fila in filas:
                partes.append(json.dumps(fila, ensure_ascii=False) if isinstance(fila, (dict, list)) else str(fila))
    return sin_tildes(" ".join(partes)).lower()


def compras_publicas_cruzar_probidad(
    rut_entidad_o_proveedor: str,
    nombre: str = "",
    organismo: str = "",
    solo_cache: bool = False,
    cache_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Valida RUT vía ``entes_publicos.validar_rut`` y realiza cruce real de probidad.

    Contrasta antecedentes públicos de ChileCompra con Declaraciones de Intereses y
    Patrimonio (DIP, Ley N.° 20.880) en InfoProbidad para detectar potenciales conflictos
    de interés o inhabilidades del Art. 4 de la Ley N.° 19.886 (Ley N.° 21.634) y Art. 54
    de la Ley N.° 18.575. Nunca inventa hallazgos ni oculta datos faltantes.
    """
    cita_19886 = formatear_cita(
        "BCN",
        "Ley N.° 19.886, Art. 4",
        url=_URL_LEY_19886,
        texto="Inhabilidades e incompatibilidades para contratar con la Administración (modificada por Ley N.° 21.634; verificar texto literal vigente en BCN).",
    )
    cita_18575 = formatear_cita(
        "BCN",
        "Ley N.° 18.575, Art. 54",
        url=_URL_LEY_18575,
        texto="Inhabilidades de ingreso y conflicto de interés en la Administración del Estado (verificar texto literal vigente en BCN).",
    )
    cita_20880 = formatear_cita(
        "BCN",
        "Ley N.° 20.880",
        url=_URL_LEY_20880,
        texto="Sobre probidad en la función pública y prevención de los conflictos de intereses (DIP).",
    )

    rut_crudo = (rut_entidad_o_proveedor or "").strip()
    validacion_rut: Dict[str, Any] = {"valido": False, "error": "RUT no proporcionado."}
    if rut_crudo:
        validacion_rut = validar_rut(rut_crudo)
        if not validacion_rut.get("valido"):
            return {
                "rut_consultado": rut_crudo,
                "rut_valido": False,
                "rut_canonico": "",
                "validacion_rut": validacion_rut,
                "nombre": nombre,
                "organismo": organismo,
                "error": validacion_rut.get("mensaje") or validacion_rut.get("error") or "RUT inválido.",
                "adjudicaciones_encontradas": [],
                "declaraciones_infoprobidad": [],
                "hallazgos": [],
                "nivel_riesgo": "NO_VERIFICABLE",
                "cruce_completo": False,
                "sin_fuente_verificable": True,
                "faltantes": ["rut_valido"],
                "advertencias": [
                    aviso_conector(
                        "RUT inválido",
                        validacion_rut.get("mensaje") or validacion_rut.get("error") or "El RUT no supera Módulo 11.",
                    )
                ],
                "citas": [cita_19886, cita_18575],
            }

    rut_canonico = str(validacion_rut.get("rut_canonico") or "")
    rut_plano = str(validacion_rut.get("rut_plano") or "")
    termino_busqueda = rut_canonico or nombre.strip() or organismo.strip()
    if not termino_busqueda:
        return {
            "rut_consultado": rut_crudo,
            "rut_valido": False,
            "rut_canonico": "",
            "validacion_rut": validacion_rut,
            "error": "Debe indicar al menos un RUT válido, nombre o razón social para el cruce.",
            "adjudicaciones_encontradas": [],
            "declaraciones_infoprobidad": [],
            "hallazgos": [],
            "nivel_riesgo": "NO_VERIFICABLE",
            "cruce_completo": False,
            "sin_fuente_verificable": True,
            "faltantes": ["identificador_consulta"],
            "advertencias": [aviso_conector("Falta identificador", "Proporcione RUT válido o nombre.")],
            "citas": [cita_19886],
        }

    carpeta = cache_dir or CACHE_DIR
    advertencias: List[Dict[str, Any]] = []
    faltantes: List[str] = []
    citas: List[Dict[str, str]] = [cita_19886, cita_18575, cita_20880]

    if not rut_crudo:
        faltantes.append("rut")
        advertencias.append(
            aviso_conector(
                "Consulta sin RUT",
                "No se proporcionó RUT; el cruce por razón social o nombre puede tener menor precisión.",
            )
        )

    res_lic = compras_publicas_buscar(
        query=termino_busqueda,
        tipo="licitaciones",
        organismo=organismo,
        limite=20,
        solo_cache=solo_cache,
        cache_dir=carpeta,
    )
    res_td = compras_publicas_buscar(
        query=termino_busqueda,
        tipo="tratos_directos",
        organismo=organismo,
        limite=20,
        solo_cache=solo_cache,
        cache_dir=carpeta,
    )

    adjudicaciones: List[Dict[str, Any]] = []
    vistos_cod = set()
    for bloque in (res_lic, res_td):
        for item in bloque.get("resultados") or []:
            cod = item.get("codigo") or item.get("ocid") or item.get("titulo")
            if cod not in vistos_cod:
                vistos_cod.add(cod)
                adjudicaciones.append(item)
                citas.extend(item.get("citas") or [])

    chilecompra_disponible = (
        not res_lic.get("sin_fuente_verificable") or not res_td.get("sin_fuente_verificable")
    )
    if not chilecompra_disponible:
        faltantes.append("chilecompra")
        advertencias.append(
            aviso_conector(
                "Sin fuente verificable en ChileCompra",
                "No fue posible verificar adjudicaciones o tratos directos en Mercado Público.",
            )
        )

    termino_dip = nombre.strip() or rut_canonico
    res_dip = _consultar_infoprobidad_seguro(termino_dip, solo_cache=solo_cache, carpeta_cache=carpeta)
    declaraciones = list(res_dip.get("declaraciones") or [])
    infoprobidad_disponible = bool(res_dip.get("ok"))

    if not infoprobidad_disponible:
        faltantes.append("infoprobidad")
        advertencias.append(
            aviso_conector(
                "Sin fuente verificable en InfoProbidad",
                f"No fue posible obtener declaraciones DIP en InfoProbidad ({res_dip.get('error', 'sin datos')}).",
            )
        )
    elif not declaraciones:
        faltantes.append("declaraciones_dip")
        advertencias.append(
            aviso_conector(
                "Sin declaraciones DIP encontradas",
                f"InfoProbidad no devolvió declaraciones públicas coincidentes para «{termino_dip}».",
            )
        )

    for dip in declaraciones:
        ident_dip = str(dip.get("identificador") or dip.get("declarante") or termino_dip)
        declarante = str(dip.get("declarante") or "Declarante")
        url_dip = f"{BASE_INFOPROBIDAD}/Declaracion/Declaracion?ID={urllib.parse.quote(ident_dip)}"
        citas.append(
            formatear_cita(
                "InfoProbidad",
                f"DIP {ident_dip} — {declarante}",
                url=url_dip,
                texto=f"Declaración de Intereses y Patrimonio de {declarante} (secciones: {', '.join((dip.get('secciones') or {}).keys()) or 'metadatos'}).",
            )
        )

    hallazgos: List[Dict[str, Any]] = []
    rut_sin_puntos = rut_canonico.replace(".", "") if rut_canonico else ""
    candidatos_obj = [rut_canonico, rut_sin_puntos, rut_plano, nombre.strip()]
    for adj in adjudicaciones:
        for prov in adj.get("proveedores") or []:
            candidatos_obj.append(str(prov.get("nombre") or ""))
            candidatos_obj.append(str(prov.get("rut") or ""))
    objetivos_norm = list(
        dict.fromkeys(
            sin_tildes(x).lower().strip()
            for x in candidatos_obj
            if x and len(x.strip()) >= 4
        )
    )
    for dip in declaraciones:
        cuerpo_dip = _normalizar_para_busqueda(_aplanar_texto_dip(dip))
        coincidencias = [
            obj for obj in objetivos_norm
            if obj in cuerpo_dip or obj.replace(".", "") in cuerpo_dip
        ]
        meta_dip = dip.get("metadatos") or {}
        org_dip = sin_tildes(str(meta_dip.get("Institución") or meta_dip.get("Organismo") or "")).lower()

        if coincidencias:
            hallazgos.append({
                "tipo": "COINCIDENCIA_DECLARACION_PATRIMONIO",
                "severidad": "ALTA",
                "norma": "Art. 4 inc. 6 Ley N.° 19.886 / Art. 54 Ley N.° 18.575",
                "detalle": (
                    f"La declaración DIP '{dip.get('identificador')}' ({dip.get('declarante')}) "
                    f"menciona el identificador o razón social consultada ({', '.join(coincidencias)})."
                ),
            })
        if organismo.strip() and org_dip and sin_tildes(organismo).lower() in org_dip:
            hallazgos.append({
                "tipo": "VINCULO_ORGANISMO_COMPRADOR",
                "severidad": "MEDIA",
                "norma": "Art. 4 Ley N.° 19.886 / Ley N.° 20.880",
                "detalle": (
                    f"El declarante '{dip.get('declarante')}' registra vínculo institucional con "
                    f"'{organismo}' en su DIP; verificar eventual inhabilidad o parentesco."
                ),
            })

    tratos_dir = [a for a in adjudicaciones if "trato directo" in str(a.get("tipo_proceso", "")).lower()]
    if tratos_dir:
        hallazgos.append({
            "tipo": "ADJUDICACIONES_TRATO_DIRECTO",
            "severidad": "MEDIA",
            "norma": "Art. 8 Ley N.° 19.886 (modificada por Ley N.° 21.634)",
            "detalle": (
                f"Se detectaron {len(tratos_dir)} proceso(s) bajo modalidad de trato directo; "
                "verificar resolución fundada y causales taxativas legales."
            ),
        })

    cruce_completo = chilecompra_disponible and infoprobidad_disponible and bool(declaraciones)
    sin_fuente = not chilecompra_disponible or not infoprobidad_disponible
    if any(h["severidad"] == "ALTA" for h in hallazgos):
        nivel_riesgo = "ALTO"
    elif hallazgos:
        nivel_riesgo = "MEDIO"
    elif cruce_completo:
        nivel_riesgo = "BAJO"
    else:
        nivel_riesgo = "NO_VERIFICABLE"

    return {
        "rut_consultado": rut_crudo,
        "rut_valido": bool(validacion_rut.get("valido")),
        "rut_canonico": rut_canonico,
        "validacion_rut": validacion_rut,
        "nombre": nombre,
        "organismo": organismo,
        "marco_legal": [
            "Ley N.° 19.886 (Art. 4)",
            "Ley N.° 21.634",
            "Ley N.° 18.575 (Art. 54)",
            "Ley N.° 20.880",
        ],
        "adjudicaciones_encontradas": adjudicaciones,
        "declaraciones_infoprobidad": declaraciones,
        "hallazgos": hallazgos,
        "nivel_riesgo": nivel_riesgo,
        "cruce_completo": cruce_completo,
        "sin_fuente_verificable": sin_fuente,
        "faltantes": faltantes,
        "advertencias": advertencias,
        "citas": citas,
    }
