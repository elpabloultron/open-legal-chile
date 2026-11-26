"""
Open Legal Chile — Privacidad (Derechos ARCO) y Propiedad Intelectual (INAPI)
Herramientas especializadas para la Nueva Ley de Protección de Datos Personales
y tramitaciones de marcas y cartas de cese y desistimiento bajo la Ley 19.039 y Ley 17.336.
"""

from datetime import datetime, timedelta
import hashlib
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import urllib.parse

from bs4 import BeautifulSoup

import config
from citas_legales import formatear_cita

INAPI_CACHE_DIR = os.path.join(os.path.dirname(__file__), "inapi_cache")
_TTL_INAPI_SEGUNDOS = 7 * 24 * 60 * 60
_MAX_INAPI_CACHE_RAM = 32
_CKAN_API_BASE = "https://datos.gob.cl/api/3/action"
_INAPI_OPEN_DATA_HTML = "https://www.inapi.cl/datos-abiertos"
_INAPI_BUSCADOR_URL = "https://buscadormarcas.inapi.cl/"
_CKAN_RECURSOS_DEFECTO = (
    "7269cbb5-baa0-42a6-a2ef-eb7f79e659f2",  # Registros recientes INAPI
    "32ff4c3e-b208-49e2-8ac1-792bb84aeaad",  # Solicitudes recientes INAPI
)
_INAPI_MEM_CACHE: Dict[str, Tuple[int, int, List[Dict[str, Any]]]] = {}


def _leer_inapi_cache(ruta_cache: str, ttl_segundos: float) -> Tuple[Optional[List[Dict[str, Any]]], bool]:
    abs_ruta = os.path.abspath(ruta_cache)
    try:
        st = os.stat(abs_ruta)
    except OSError:
        return None, False

    fresco = config.cache_fresco(abs_ruta, ttl_segundos)
    en_ram = _INAPI_MEM_CACHE.get(abs_ruta)
    if en_ram is not None and en_ram[0] == st.st_mtime_ns and en_ram[1] == st.st_size:
        return en_ram[2], fresco

    leido = config.leer_json_si_se_puede(abs_ruta)
    if not isinstance(leido, list):
        return None, False

    if len(_INAPI_MEM_CACHE) >= _MAX_INAPI_CACHE_RAM:
        _INAPI_MEM_CACHE.clear()
    _INAPI_MEM_CACHE[abs_ruta] = (int(st.st_mtime_ns), int(st.st_size), leido)
    return leido, fresco


def _guardar_inapi_cache(ruta_cache: str, registros: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(ruta_cache), exist_ok=True)
    abs_ruta = os.path.abspath(ruta_cache)
    with open(abs_ruta, "w", encoding="utf-8") as fh:
        json.dump(registros, fh, ensure_ascii=False, indent=2)
    try:
        st = os.stat(abs_ruta)
        if len(_INAPI_MEM_CACHE) >= _MAX_INAPI_CACHE_RAM:
            _INAPI_MEM_CACHE.clear()
        _INAPI_MEM_CACHE[abs_ruta] = (int(st.st_mtime_ns), int(st.st_size), registros)
    except OSError as exc:
        config.registrar_tiempo("inapi.cache_stat_error", 0.0)
        _ = exc


def _normalizar_registro_inapi(raw: Dict[str, Any]) -> Dict[str, Any]:
    brand = str(raw.get("BrandName") or raw.get("marca") or raw.get("denominacion") or "").strip()
    clases = str(raw.get("NizaClasses") or raw.get("clase_niza") or raw.get("clase") or "").strip()
    reg_num = str(raw.get("RegistrationNumber") or raw.get("registro") or "").strip()
    app_num = str(raw.get("ApplicationNumber") or raw.get("solicitud") or "").strip()
    titular = str(raw.get("Applicants") or raw.get("titular") or "").strip()
    estado = str(raw.get("Status") or raw.get("estado") or "").strip()
    tipo_signo = str(raw.get("SignType") or raw.get("tipo_signo") or "").strip()
    fecha_pres = str(raw.get("FilingDate") or raw.get("fecha_solicitud") or "")[:10]
    fecha_reg = str(raw.get("RegistrationDate") or raw.get("fecha_registro") or "")[:10]
    fecha_venc = str(raw.get("ExpirationDate") or raw.get("fecha_vencimiento") or "")[:10]
    proteccion = str(raw.get("ProtectionDescription") or raw.get("descripcion") or "").strip()
    url_img = str(raw.get("IMAGE") or raw.get("url") or "").strip()
    url = url_img or (f"{_INAPI_BUSCADOR_URL}?s={app_num}" if app_num else _INAPI_OPEN_DATA_HTML)

    resumen_partes = [
        f"Marca: {brand}" if brand else "",
        f"Estado: {estado}" if estado else "",
        f"Clase(s) Niza: {clases}" if clases else "",
        f"N.° Registro: {reg_num}" if reg_num else "",
        f"N.° Solicitud: {app_num}" if app_num else "",
        f"Titular: {titular}" if titular else "",
        proteccion,
    ]
    resumen = " · ".join(p for p in resumen_partes if p)

    return {
        "organismo": "INAPI",
        "marca": brand,
        "clase_niza": clases,
        "numero_registro": reg_num,
        "numero_solicitud": app_num,
        "titular": titular,
        "estado": estado,
        "tipo_signo": tipo_signo,
        "fecha_solicitud": fecha_pres,
        "fecha_registro": fecha_reg,
        "fecha_vencimiento": fecha_venc,
        "proteccion": proteccion,
        "url": url,
        "texto": resumen,
    }


def _extraer_registros_ckan(payload: Dict[str, Any]) -> Tuple[Optional[List[Dict[str, Any]]], List[str]]:
    """Extrae registros directos si vienen en `records` y resource_ids activos si vienen en `resources`."""
    res = payload.get("result")
    if not isinstance(res, dict):
        return None, []

    if isinstance(res.get("records"), list):
        return [
            _normalizar_registro_inapi(r)
            for r in res["records"]
            if isinstance(r, dict) and (r.get("BrandName") or r.get("marca") or r.get("denominacion"))
        ], []

    recursos: List[str] = []
    if isinstance(res.get("resources"), list):
        for r in res["resources"]:
            if isinstance(r, dict) and r.get("datastore_active") and r.get("id"):
                recursos.append(str(r["id"]))
    elif isinstance(res.get("results"), list):
        for pkg in res["results"]:
            if not isinstance(pkg, dict):
                continue
            for r in pkg.get("resources") or []:
                if isinstance(r, dict) and r.get("datastore_active") and r.get("id"):
                    recursos.append(str(r["id"]))
    return None, recursos


def _parsear_html_inapi_fallback(crudo: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(crudo, "html.parser")
    items: List[Dict[str, Any]] = []
    for fila in soup.select("tr, div.marca, div.recuadro"):
        txt = config.texto_plano(fila.get_text(" ", strip=True))
        if not txt or len(txt) < 4:
            continue
        enlace = fila.find("a", href=True)
        url = str(enlace.get("href") or _INAPI_OPEN_DATA_HTML) if enlace else _INAPI_OPEN_DATA_HTML
        items.append({
            "organismo": "INAPI",
            "marca": txt[:120],
            "clase_niza": "",
            "numero_registro": "",
            "numero_solicitud": "",
            "titular": "",
            "estado": "Publicado en datos abiertos",
            "tipo_signo": "",
            "fecha_solicitud": "",
            "fecha_registro": "",
            "fecha_vencimiento": "",
            "proteccion": "",
            "url": url,
            "texto": txt[:400],
        })
    return items


def _consultar_inapi_red(marca: str, limite: int) -> List[Dict[str, Any]]:
    q_clean = (marca or "").strip()
    pkg_url = f"{_CKAN_API_BASE}/package_show?id=registros-de-marcas"
    recursos_ids: List[str] = []
    primer_error: Optional[Exception] = None

    try:
        raw_pkg = config.pedir_http(pkg_url, headers={"Accept": "application/json"}, timeout=20.0).decode(
            "utf-8", errors="ignore"
        )
        if raw_pkg.lstrip().startswith("{"):
            directos, recursos_ids = _extraer_registros_ckan(json.loads(raw_pkg))
            if directos is not None:
                return directos
    except Exception as exc:  # noqa: BLE001
        primer_error = exc

    if not recursos_ids:
        recursos_ids = list(_CKAN_RECURSOS_DEFECTO)
    else:
        recursos_ids = list(reversed(recursos_ids))[:2]

    registros: List[Dict[str, Any]] = []
    vistos: set[str] = set()
    errores_ds: List[Exception] = []

    for rid in recursos_ids:
        params = {"resource_id": rid, "limit": str(max(limite * 4, 25))}
        if q_clean:
            params["q"] = q_clean
        ds_url = f"{_CKAN_API_BASE}/datastore_search?{urllib.parse.urlencode(params)}"
        try:
            raw_ds = config.pedir_http(ds_url, headers={"Accept": "application/json"}, timeout=20.0).decode(
                "utf-8", errors="ignore"
            )
            if raw_ds.lstrip().startswith("<"):
                for item in _parsear_html_inapi_fallback(raw_ds):
                    clave = f"{item['marca']}|{item['url']}"
                    if clave not in vistos:
                        vistos.add(clave)
                        registros.append(item)
                continue
            parsed = json.loads(raw_ds)
            if isinstance(parsed, dict):
                recs, _ = _extraer_registros_ckan(parsed)
                for item in recs or []:
                    clave = f"{item['marca']}|{item['numero_solicitud']}|{item['numero_registro']}"
                    if clave not in vistos:
                        vistos.add(clave)
                        registros.append(item)
            elif isinstance(parsed, list):
                for raw_item in parsed:
                    if isinstance(raw_item, dict):
                        item = _normalizar_registro_inapi(raw_item)
                        clave = f"{item['marca']}|{item['numero_solicitud']}|{item['numero_registro']}"
                        if clave not in vistos:
                            vistos.add(clave)
                            registros.append(item)
        except Exception as exc:  # noqa: BLE001
            errores_ds.append(exc)

    if not registros and errores_ds and (len(errores_ds) == len(recursos_ids) or primer_error is not None):
        raise errores_ds[0]
    return registros


def _coincide_marca_y_clase(item: Dict[str, Any], marca: str, clase_niza: str) -> int:
    clase_obj = str(clase_niza or "").strip()
    if clase_obj:
        clases_item = {c.strip() for c in re.split(r"[,;/\s]+", str(item.get("clase_niza") or "")) if c.strip()}
        if clases_item and clase_obj not in clases_item:
            return 0

    m_st = config.sin_tildes(marca or "").strip().lower()
    if not m_st:
        return 1
    nombre_st = config.sin_tildes(str(item.get("marca") or "")).strip().lower()
    if nombre_st == m_st:
        return 3
    if re.search(rf"\b{re.escape(m_st)}\b", nombre_st) or m_st in nombre_st:
        return 2
    tokens = [t for t in re.findall(r"[a-z0-9]+", m_st) if len(t) >= 2]
    if tokens and any(t in nombre_st for t in tokens):
        return 1
    return 0


def _construir_cita_inapi(item: Dict[str, Any]) -> Dict[str, str]:
    marca = str(item.get("marca") or "Marca").strip()
    reg = str(item.get("numero_registro") or "").strip()
    sol = str(item.get("numero_solicitud") or "").strip()
    clases = str(item.get("clase_niza") or "").strip()

    detalles_id = []
    if reg:
        detalles_id.append(f"Reg. {reg}")
    elif sol:
        detalles_id.append(f"Sol. {sol}")
    if clases:
        detalles_id.append(f"Clase Niza {clases}")

    sufijo = f" ({', '.join(detalles_id)})" if detalles_id else ""
    ident = f"Registro/Datos Abiertos {marca}{sufijo}"
    url = str(item.get("url") or _INAPI_OPEN_DATA_HTML)
    texto = str(item.get("texto") or marca)[:900]
    return formatear_cita("INAPI", ident[:200], url=url, texto=texto)


class PrivacyARCOEngine:
    """Motor de gestión de solicitudes de Derechos ARCO bajo la legislación chilena de datos."""

    DERECHOS_VALIDOS = ["ACCESO", "RECTIFICACIÓN", "CANCELACIÓN", "OPOSICIÓN", "PORTABILIDAD"]

    @staticmethod
    def procesar_solicitud_arco(tipo_derecho: str, solicitante: str, rut: str, datos_solicitados: str) -> Dict[str, Any]:
        tipo = tipo_derecho.upper()
        if tipo not in PrivacyARCOEngine.DERECHOS_VALIDOS:
            tipo = "ACCESO"

        fecha_solicitud = datetime.now()
        plazo_legal_dias = 15
        fecha_limite = fecha_solicitud + timedelta(days=plazo_legal_dias)

        modelo_respuesta = (
            f"REF: RESPUESTA A SOLICITUD DE EJERCICIO DE DERECHO DE {tipo}\n"
            f"FECHA: {fecha_solicitud.strftime('%d de %B de %Y')}\n"
            f"A: {solicitante.upper()} (RUT: {rut})\n\n"
            f"Estimado/a titular:\n\n"
            f"En cumplimiento de la Ley de Protección de los Datos Personales de la República de Chile, "
            f"acusamos recibo de su solicitud de fecha {fecha_solicitud.strftime('%d/%m/%Y')} mediante la cual ejerce su derecho de {tipo} "
            f"respecto de los siguientes datos: '{datos_solicitados}'.\n\n"
            f"Se informa que su requerimiento ha sido admitido a tramitación. Conforme al artículo correspondiente, "
            f"esta entidad responderá de fondo en un plazo máximo de {plazo_legal_dias} días corridos, a más tardar el {fecha_limite.strftime('%d/%m/%Y')}.\n\n"
            f"Atentamente,\n"
            f"Oficial de Cumplimiento y Protección de Datos Personales"
        )

        return {
            "solicitante": solicitante,
            "rut": rut,
            "tipo_derecho": tipo,
            "plazo_legal_dias": plazo_legal_dias,
            "fecha_limite_respuesta": fecha_limite.strftime("%Y-%m-%d"),
            "modelo_oficial_respuesta": modelo_respuesta,
            "organismo_fiscalizador": "Agencia de Protección de Datos Personales de Chile",
            "estatus": "ADMITIDA A TRÁMITE",
            "regimen_vigencia": {
                "ley_vigente_actual": "Ley N.° 19.628 (vigente hasta el 14-10-2027)",
                "ley_modernizada": "Ley N.° 21.719 (entrada en vigencia plena el 15-10-2027, modificada por Ley N.° 21.855, D.O. 23-11-2026)",
                "consejo_directivo_agencia": "5 consejeros (propuesta al Senado hasta el 15-01-2027)",
            },
        }


class INAPIEngine:
    """Motor para evaluación de factibilidad marcaria y cartas de cese y desistimiento."""

    NIZA_CLASSES_FREQ = {
        "9": "Software, aplicaciones, sistemas de IA y equipos electrónicos",
        "35": "Servicios de publicidad, gestión de negocios y comercialización online",
        "42": "Servicios científicos, tecnológicos, desarrollo de software y computación",
        "45": "Servicios jurídicos, de asesoría legal, auditoría y litigación"
    }

    @staticmethod
    def redactar_cease_and_desist(marca_afectada: str, titular: str, infractor: str, hechos_infraccion: str) -> Dict[str, Any]:
        """
        Redacta una carta notarial/formal de Cese y Desistimiento por infracción marcaria o de autor.
        """
        hoy = datetime.now().strftime("%d de %B de %Y")
        carta = (
            f"Santiago, {hoy}\n\n"
            f"A: {infractor.upper()}\n"
            f"DE: {titular.upper()} (Titular de derechos)\n"
            f"MATERIA: INTIMACIÓN FORMAL DE CESE Y DESISTIMIENTO — INFRACCIÓN MARCARIA Y PROPIEDAD INTELECTUAL\n\n"
            f"De nuestra consideración:\n\n"
            f"Nos dirigimos a usted en representación de {titular}, legítimo titular del signo distintivo '{marca_afectada}', "
            f"debidamente registrado y protegido ante el Instituto Nacional de Propiedad Industrial (INAPI) conforme a la Ley N° 19.039 "
            f"y la Ley N° 17.336 de Propiedad Intelectual.\n\n"
            f"Ha llegado a nuestro conocimiento que usted o su empresa ha estado utilizando el signo '{marca_afectada}' o variantes idénticas o confusamente similares, "
            f"específicamente: {hechos_infraccion}.\n\n"
            f"Dicho uso no consentido constituye una infracción flagrante a los derechos exclusivos de nuestro mandante, induciendo a error al público consumidor "
            f"y configurando actos de competencia desleal tipificados en la Ley N° 20.169.\n\n"
            f"POR TANTO, INTIMAMOS A USTED PARA QUE, DENTRO DEL PLAZO FATAL DE 5 DÍAS HÁBILES A CONTAR DE ESTA NOTIFICACIÓN:\n"
            f"1. Cese de manera inmediata y definitiva todo uso de la denominación '{marca_afectada}'.\n"
            f"2. Retire del comercio material publicitario, dominios web, cuentas de redes sociales o productos que ostenten el signo infractor.\n\n"
            f"Hacemos expresa reserva de iniciar las acciones civiles de indemnización de perjuicios y querellas penales tipificadas en el Título X de la Ley N° 19.039.\n\n"
            f"Atentamente,\n"
            f"{titular} — Dirección de Asuntos Legales y Propiedad Intelectual"
        )

        return {
            "marca": marca_afectada,
            "titular": titular,
            "infractor": infractor,
            "carta_completa": carta,
            "leyes_invocadas": ["Ley N° 19.039 (Propiedad Industrial)", "Ley N° 17.336 (Propiedad Intelectual)", "Ley N° 20.169 (Competencia Desleal)"],
            "plazo_intimacion_dias": 5
        }

    @staticmethod
    def buscar_marcas_datos_abiertos(
        marca: str,
        clase_niza: str = "",
        limite: int = 10,
        solo_cache: bool = False,
        cache_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Consulta marcas registradas y solicitadas en datos abiertos oficiales de INAPI."""
        marca_limpia = (marca or "").strip()
        clase_limpia = str(clase_niza or "").strip()
        limite_seguro = max(1, min(int(limite), 50))
        carpeta = cache_dir or INAPI_CACHE_DIR
        clave_hash = hashlib.sha256(f"{marca_limpia.lower()}|{clase_limpia}".encode("utf-8")).hexdigest()[:16]
        ruta_cache = os.path.join(carpeta, f"inapi_marcas_{clave_hash}.json")

        registros_cache, fresco = _leer_inapi_cache(ruta_cache, _TTL_INAPI_SEGUNDOS)
        avisos: List[Dict[str, Any]] = []
        origen = "red"
        copia_vencida = False
        sin_fuente = False
        registros_fuente: List[Dict[str, Any]] = []

        if registros_cache is not None and fresco:
            registros_fuente = registros_cache
            origen = "cache"
        elif solo_cache:
            if registros_cache is not None:
                registros_fuente = registros_cache
                origen = "cache_vencida"
                copia_vencida = True
                avisos.append(
                    config.aviso_conector(
                        "Copia local vencida de datos abiertos INAPI",
                        "Se utilizó la caché local expirada porque se solicitó solo_cache=True.",
                    )
                )
            else:
                origen = "sin_datos"
                sin_fuente = True
                avisos.append(
                    config.aviso_conector(
                        "Sin caché local de datos abiertos INAPI",
                        "No existe copia local disponible y solo_cache=True impide consultar datos.gob.cl.",
                    )
                )
        else:
            t0 = time.perf_counter()
            try:
                registros_fuente = _consultar_inapi_red(marca_limpia, limite_seguro)
                config.registrar_tiempo("inapi.datos_abiertos.red", time.perf_counter() - t0)
                if registros_fuente:
                    _guardar_inapi_cache(ruta_cache, registros_fuente)
                elif registros_cache is not None:
                    registros_fuente = registros_cache
                    origen = "cache_vencida"
                    copia_vencida = True
            except Exception as exc:  # noqa: BLE001
                config.registrar_tiempo("inapi.datos_abiertos.error", time.perf_counter() - t0)
                if registros_cache is not None:
                    registros_fuente = registros_cache
                    origen = "cache_vencida"
                    copia_vencida = True
                    avisos.append(
                        config.aviso_conector(
                            f"Datos abiertos INAPI sin conexión ({type(exc).__name__})",
                            f"Se entrega copia local vencida tras error de red: {str(exc)[:140]}.",
                        )
                    )
                else:
                    origen = "sin_datos"
                    sin_fuente = True
                    avisos.append(
                        config.aviso_conector(
                            "No se pudieron consultar los datos abiertos de INAPI",
                            f"El Portal de Datos Abiertos del Estado (datos.gob.cl) no respondió ({str(exc)[:140]}). Sin fuente verificable.",
                        )
                    )

        candidatos: List[Tuple[int, Dict[str, Any]]] = []
        for item in registros_fuente:
            score = _coincide_marca_y_clase(item, marca_limpia, clase_limpia)
            if score > 0:
                candidatos.append((score, item))

        candidatos.sort(key=lambda par: par[0], reverse=True)
        seleccionados: List[Dict[str, Any]] = []
        citas: List[Dict[str, str]] = []
        for _, item in candidatos[:limite_seguro]:
            cita = _construir_cita_inapi(item)
            enriquecido = {**item, "cita": cita, "citas": [cita]}
            seleccionados.append(enriquecido)
            citas.append(cita)

        if not seleccionados and not sin_fuente and marca_limpia:
            avisos.append(
                config.aviso_conector(
                    f"Sin antecedentes marcarios en datos abiertos INAPI para «{marca_limpia}»",
                    "No se encontraron coincidencias directas en los registros públicos consultados.",
                )
            )

        return {
            "organismo": "INAPI",
            "marca": marca_limpia,
            "clase_niza": clase_limpia,
            "total": len(seleccionados),
            "resultados": seleccionados,
            "citas": citas,
            "fuentes_consultadas": [f"{_CKAN_API_BASE}/package_show?id=registros-de-marcas", _INAPI_OPEN_DATA_HTML],
            "origen": origen,
            "copia_local_vencida": copia_vencida,
            "sin_fuente_verificable": sin_fuente,
            "avisos": avisos,
        }

    @staticmethod
    def evaluar_factibilidad_marca(
        marca_propuesta: str,
        clase_niza: str = "45",
        consultar_inapi: bool = False,
    ) -> Dict[str, Any]:
        """
        Evalúa preliminarmente la viabilidad de registro de una marca en INAPI.
        """
        clase_desc = INAPIEngine.NIZA_CLASSES_FREQ.get(str(clase_niza), "Clase del Clasificador Internacional de Niza")
        nombre = marca_propuesta.strip()

        es_generica = nombre.lower() in ["abogados", "ley", "justicia", "tribunal", "derecho", "legal"]
        es_descriptiva = len(nombre.split()) > 4

        riesgo = "BAJO"
        motivos = []
        if es_generica:
            riesgo = "ALTO"
            motivos.append("El signo parece incurrir en la causal de irregistrabilidad del Art. 20 letra e) de la Ley 19.039 (signos genéricos o de uso común).")
        elif es_descriptiva:
            riesgo = "MEDIO"
            motivos.append("El signo puede considerarse descriptivo de los servicios prestados.")
        else:
            motivos.append("El signo posee distintividad de fantasía preliminar. Se sugiere solicitar búsqueda formal en la base de datos oficial de INAPI.")

        resultado: Dict[str, Any] = {
            "marca_propuesta": marca_propuesta,
            "clase_niza": clase_niza,
            "descripcion_clase": clase_desc,
            "nivel_riesgo_preliminar": riesgo,
            "analisis_distintividad": motivos,
            "recomendacion": "Efectuar búsqueda fonética y de figuras en el portal web de INAPI (inapi.cl) antes del pago de derechos arancelarios."
        }

        if consultar_inapi:
            try:
                consulta = INAPIEngine.buscar_marcas_datos_abiertos(
                    marca_propuesta,
                    clase_niza=str(clase_niza or ""),
                )
            except Exception as exc:  # noqa: BLE001
                consulta = {
                    "organismo": "INAPI",
                    "marca": nombre,
                    "clase_niza": str(clase_niza or ""),
                    "total": 0,
                    "resultados": [],
                    "citas": [],
                    "origen": "sin_datos",
                    "copia_local_vencida": False,
                    "sin_fuente_verificable": True,
                    "avisos": [
                        config.aviso_conector(
                            "Error al consultar datos abiertos INAPI",
                            f"No se pudo completar el contraste marcario en línea ({str(exc)[:140]}).",
                        )
                    ],
                }

            resultado["consulta_inapi"] = consulta
            if consulta.get("citas"):
                resultado["citas"] = consulta["citas"]

            hallazgos = consulta.get("resultados") or []
            if hallazgos:
                exactos = [
                    h for h in hallazgos
                    if config.sin_tildes(str(h.get("marca") or "")).strip().lower()
                    == config.sin_tildes(nombre).lower()
                ]
                if exactos:
                    resultado["nivel_riesgo_preliminar"] = "ALTO"
                    motivos.append(
                        f"Se detectaron {len(exactos)} coincidencia(s) idéntica(s) en datos abiertos de INAPI "
                        f"(Art. 20 letras f) y h) Ley N.° 19.039)."
                    )
                else:
                    if resultado["nivel_riesgo_preliminar"] == "BAJO":
                        resultado["nivel_riesgo_preliminar"] = "MEDIO"
                    motivos.append(
                        f"Se detectaron {len(hallazgos)} marca(s) similar(es) en datos abiertos de INAPI "
                        f"para la clase Niza {clase_niza}."
                    )
            elif consulta.get("sin_fuente_verificable"):
                motivos.append(
                    "No se pudo contrastar con los datos abiertos de INAPI (sin fuente verificable)."
                )

        return resultado
