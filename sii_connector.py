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
import uuid
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


def _numero_resolucion_sii(titulo: str) -> str:
    """Número de una resolución exenta del SII a partir del título del índice.

    El título real es «Resolución Exenta SII N° 128 del 16 de Septiembre del 2026», con «SII» entre
    «Exenta» y el número: un patrón que exija el número justo después de «Exenta» no lo encuentra.
    """
    m = re.search(r"Res(?:oluci[oó]n)?\s+Ex(?:enta)?(?:\s+SII)?\s*N[°ºo\.\s]*([0-9]+)",
                  titulo, re.IGNORECASE)
    return m.group(1) if m else ""


# La jurisprudencia administrativa (oficios y pronunciamientos) no está en HTML: cada serie se carga
# por JavaScript desde un servicio del propio SII, con el cuerpo {"key": …, "year": …}. Se consulta
# ese servicio directamente. Las claves son las que usa el sitio: RENTA, IVA y OTROS.
SII_JADM_API = "https://www3.sii.cl/getPublicacionesCTByMateria"
SII_JADM_DESCARGA = "https://www4.sii.cl/gabineteAdmInternet/descargaArchivo"
SII_JADM_SERIES = {
    "RENTA": ("Renta", "ley_impuesto_renta"),
    "IVA": ("IVA", "ley_impuesto_ventas"),
    "OTROS": ("Otras normas", "otras_normas"),
}


def _normalizar_oficio(dato: Dict[str, Any], anio: int, serie: str, carpeta: str, base_url: str) -> Dict[str, Any]:
    """Traduce una publicación del buscador de jurisprudencia administrativa a la forma del conector.

    El resumen oficial («pubResumen») es la materia, y «pubLegal» es la referencia normativa que el
    oficio cita: ambas se indexan para poder buscar por tema o por artículo.
    """
    numero = str(dato.get("pubNumOficio", "")).strip()
    fecha = str(dato.get("pubFechaPubli", "")).strip()
    return {
        "anio": anio,
        "serie": serie,
        "tipo": "Oficio / pronunciamiento (jurisprudencia administrativa SII)",
        "numero": numero,
        "fecha": fecha,
        "titulo": f"Oficio N° {numero} de {fecha}" if numero else str(dato.get("pubLegal", "")).strip(),
        "materia": str(dato.get("pubResumen") or "").strip(),
        "materia_legal": str(dato.get("pubLegal") or "").strip(),
        "tipo_documento": dato.get("tipoArchPublica", ""),
        # El PDF no tiene URL directa: el sitio envía un formulario POST con estos datos
        # (ver descargar_oficio).
        "descarga": {
            "nombreDocumento": f"{numero}-{fecha}.pdf",
            "extension": dato.get("extensionArchPublica", ""),
            "id": dato.get("idBlobArchPublica", ""),
            "mediaType": dato.get("mTypeArchPublica", ""),
        },
        "url": f"{base_url}/jurisprudencia_administrativa/{carpeta}/{anio}/{carpeta}_jadm{anio}.htm",
    }


# Actos y resoluciones de las direcciones regionales: la página maestra del año enlaza un índice por
# dirección, y cada índice es una tabla de 15 columnas (año, mes, sección, tipo, número, fecha,
# materia, descripción, fecha de publicación, origen, «Ver Documento» → PDF, y cuatro marcas).
SII_ACTOS_MAESTRO = "{base}/actos_y_resoluciones_{anio}.html"


def _parsear_actos_ddrr(pagina: str, direccion: str, base_pdfs: str) -> List[Dict[str, Any]]:
    """Extrae los actos y resoluciones de una dirección regional desde su índice anual."""
    actos: List[Dict[str, Any]] = []
    for fila in re.findall(r"<tr[^>]*>(.*?)</tr>", pagina, re.IGNORECASE | re.DOTALL):
        celdas = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", fila, re.IGNORECASE | re.DOTALL)
        if len(celdas) < 11:
            continue
        numero = _texto_plano(celdas[4])
        descripcion = _texto_plano(celdas[7])
        if not (numero or descripcion):
            continue
        # La tabla trae una fila de instrucciones («Nombre/título», «Breve descripción del objeto
        # del acto») que no es un acto y se colaba como si lo fuera.
        if "breve descripción del objeto" in descripcion.lower() or numero.lower().startswith("nombre"):
            continue
        m_href = re.search(r'href=["\']?([^"\'\s>]+)', celdas[10], re.IGNORECASE)
        pdf = ""
        if m_href:
            href = m_href.group(1)
            pdf = href if href.startswith("http") else f"{base_pdfs}/{href}"
        tipo = _texto_plano(celdas[3])
        fecha = _texto_plano(celdas[5])
        actos.append({
            "anio": _texto_plano(celdas[0]),
            "mes": _texto_plano(celdas[1]),
            "seccion": _texto_plano(celdas[2]),
            "tipo": tipo,
            "numero": numero,
            "fecha": fecha,
            "materia": _texto_plano(celdas[6]),
            "descripcion": descripcion,
            "fecha_publicacion": _texto_plano(celdas[8]),
            "direccion": direccion,
            "titulo": f"{tipo} N° {numero} de {fecha}".strip(),
            "pdfUrl": pdf,
        })
    return actos


def _parsear_convenios(pagina: str) -> List[Dict[str, Any]]:
    """Extrae el cuadro completo de convenios tributarios internacionales.

    La página publica ocho tablas de formas distintas —doble imposición (5 columnas), circulares
    (3), intercambio de información y protocolos (2) y transporte internacional (1)—, y cada una va
    bajo su propio título. Un parser que asumiera un solo formato leía apenas la primera y devolvía
    36 convenios de los más de 70 que el Servicio publica. Aquí se recorre el documento en orden,
    recordando el título vigente, y se adapta a las columnas que tenga cada tabla.
    """
    convenios: List[Dict[str, Any]] = []
    seccion = ""

    for bloque in re.finditer(r"<h[1-4][^>]*>(.*?)</h[1-4]>|<table[^>]*>(.*?)</table>",
                              pagina, re.IGNORECASE | re.DOTALL):
        if bloque.group(1) is not None:
            titulo = _texto_plano(bloque.group(1))
            if titulo:
                seccion = titulo
            continue

        for fila in re.findall(r"<tr[^>]*>(.*?)</tr>", bloque.group(2), re.IGNORECASE | re.DOTALL):
            celdas = [_texto_plano(c) for c in
                      re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", fila, re.IGNORECASE | re.DOTALL)]
            if not celdas or not celdas[0]:
                continue
            if celdas[0].lower().startswith(("país", "texto de la convención", "documentos")):
                continue  # fila de encabezado
            archivos = [
                {"texto": _texto_plano(texto), "url": href.strip()}
                for href, texto in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
                                              fila, re.IGNORECASE | re.DOTALL)
            ]
            registro: Dict[str, Any] = {
                "seccion": seccion,
                "pais": celdas[0],
                "archivos": archivos,
            }
            if len(celdas) >= 5:
                registro.update({
                    "texto": celdas[1],
                    "autoridad_competente": celdas[2],
                    "fecha_aplicacion_chile": celdas[3],
                    "documentos_relacionados": celdas[4],
                })
            elif len(celdas) == 3:
                registro.update({"circular": celdas[1], "documentos_relacionados": celdas[2]})
            elif len(celdas) == 2:
                registro.update({"texto": celdas[1]})
            convenios.append(registro)

    return convenios


# Jurisprudencia judicial del SII (acjui): no es un sitio estático, es una aplicación AngularJS
# cuyo bundle define su protocolo. Las consultas van por POST con un sobre metaData/data, usando el
# token de conversación que la propia aplicación emplea cuando no hay sesión («####», del bundle:
# `token = getCookie("TOKEN") || "####"`). El listado completo de sentencias se obtiene con
# `pronunciamientos/filter`; los demás métodos (find-articulos, find-instancias) sirven de apoyo.
SII_JUDICIAL_BASE = "https://www4.sii.cl/acjui"
SII_JUDICIAL_NS = "cl.sii.sdi.lob.juridica.acj.data.impl.InternetApplicationService/"
SII_JUDICIAL_CONVERSACION = "####"


def _sobre_acjui(metodo: str, datos: Dict[str, Any]) -> bytes:
    """Cuerpo que espera el servicio de jurisprudencia judicial del SII."""
    return json.dumps({
        "metaData": {
            "namespace": SII_JUDICIAL_NS + metodo,
            "conversationId": SII_JUDICIAL_CONVERSACION,
            "transactionId": str(uuid.uuid4()),
            "page": None,
        },
        "data": datos,
    }).encode("utf-8")


def _normalizar_sentencia(dato: Dict[str, Any]) -> Dict[str, Any]:
    """Traduce una sentencia del buscador judicial del SII a la forma del conector."""

    def nombre(campo: str) -> str:
        valor = dato.get(campo)
        if isinstance(valor, dict):
            return str(valor.get("nombre") or "")
        return str(valor or "")

    articulos = []
    for relacion in dato.get("pronunciamientosArticulos") or []:
        articulo = (relacion or {}).get("articulo") or {}
        if not articulo:
            continue
        cuerpo = (articulo.get("tituloBO") or {}).get("cuerpoNormativo") or {}
        articulos.append({
            "cuerpo_normativo": str(cuerpo.get("nombre") or ""),
            "numero": str(articulo.get("numero") or ""),
            "nombre": str(articulo.get("nombre") or ""),
        })

    codigo = str(dato.get("codigoPronunciamiento") or "")
    fecha = str(dato.get("fecha") or "")
    partes = str(dato.get("partes") or "")
    return {
        "tipo": "Sentencia (jurisprudencia judicial SII)",
        "codigo": codigo,
        "fecha": fecha,
        "ruc": str(dato.get("ruc") or ""),
        "partes": partes,
        "tribunal": nombre("instancia"),
        "decision": nombre("decision"),
        "resultado": nombre("resultado"),
        "extracto": str(dato.get("contenido") or "").strip(),
        "articulos": articulos,
        "url_documento": str(dato.get("urlDocumento") or ""),
        "titulo": f"Sentencia {codigo} de {fecha}" + (f" — {partes[:70]}" if partes else ""),
    }


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

        url = f"{BASE_URL}/resoluciones/{anio}/res_ind{anio}.htm"
        headers = {'User-Agent': 'OpenLegalChile/1.0 (Derecho Tributario Chile)'}
        req = urllib.request.Request(url, headers=headers)

        resoluciones_list: List[Dict[str, Any]] = []
        try:
            with safe_urlopen(req, timeout=20) as resp:
                page_html = resp.read().decode("utf-8", errors="ignore")
                resoluciones_list = _parsear_indice_sii(page_html, anio, "resoluciones", BASE_URL)
                for r in resoluciones_list:
                    r["tipo"] = "Resolución Exenta SII"
                    r["numero"] = _numero_resolucion_sii(r["titulo"])

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
        """Indexa la jurisprudencia administrativa del SII (oficios y pronunciamientos) de un año.

        Este listado no está en HTML: cada serie —Renta, IVA y Otras normas— se carga por JavaScript
        desde el servicio `getPublicacionesCTByMateria` del propio Servicio, así que el conector
        consulta ese servicio directamente (las tres claves que usa el sitio: RENTA, IVA, OTROS).

        La dirección anterior (/jurisprudencia/administrativa/{anio}/indjad{anio}.htm) devuelve 404 en
        todos los años: el método llevaba tiempo devolviendo una lista vacía, que se lee como «no hay
        jurisprudencia administrativa», y eso es falso. Lo que se indexa es el resumen oficial
        (`pubResumen`) y la referencia normativa que cita el oficio (`pubLegal`).
        """
        cache_key = f"oficios_{anio}_v2"  # v2: la caché anterior estaba vacía
        cache_file = self._get_cache_path(cache_key)

        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        headers = {
            'User-Agent': 'OpenLegalChile/1.0 (Derecho Tributario Chile)',
            'Content-Type': 'application/json',
        }
        oficios_list: List[Dict[str, Any]] = []
        fallos: List[str] = []

        for clave, (nombre_serie, carpeta) in SII_JADM_SERIES.items():
            cuerpo = json.dumps({"key": clave, "year": str(anio)}).encode("utf-8")
            try:
                req = urllib.request.Request(SII_JADM_API, data=cuerpo, headers=headers)
                with safe_urlopen(req, timeout=45) as resp:
                    datos = json.loads(resp.read().decode("utf-8", errors="ignore"))
            except Exception as e:
                fallos.append(f"{nombre_serie}: {e}")
                continue

            for dato in datos or []:
                if isinstance(dato, dict):
                    oficios_list.append(
                        _normalizar_oficio(dato, anio, nombre_serie, carpeta, BASE_URL))

        if oficios_list:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(oficios_list, f, ensure_ascii=False, indent=2)
            return oficios_list

        detalle = "; ".join(fallos) if fallos else "el servicio respondió sin publicaciones"
        return [_aviso(
            f"No se pudo cargar la jurisprudencia administrativa del SII de {anio}",
            f"Ninguna de las tres series (Renta, IVA, Otras normas) entregó publicaciones ({detalle}). "
            "Esto NO significa que no existan oficios de ese año.",
        )]

    def descargar_oficio(self, item: Dict[str, Any], destino: Optional[str] = None) -> Dict[str, Any]:
        """Descarga el PDF de un oficio de la jurisprudencia administrativa.

        No hay URL directa: la página del SII arma un formulario —`<form name="frm" target="_blank">`,
        sin atributo `method`— y lo envía con los datos del documento. Al no declarar método, el
        navegador usa GET, de modo que el archivo se obtiene por parámetros en la URL (con POST el
        servicio responde 405 Method Not Allowed).
        """
        descarga = item.get("descarga") or {}
        if not descarga.get("id"):
            return {"ok": False, "error": "el ítem no trae los datos de descarga (falta el id del archivo)"}

        parametros = urllib.parse.urlencode({
            "nombreDocumento": descarga.get("nombreDocumento", ""),
            "extension": descarga.get("extension", ""),
            "acc": "download",
            "id": descarga.get("id", ""),
            "mediaType": descarga.get("mediaType", ""),
        })
        req = urllib.request.Request(
            f"{SII_JADM_DESCARGA}?{parametros}",
            headers={'User-Agent': 'OpenLegalChile/1.0 (Derecho Tributario Chile)'},
        )
        try:
            with safe_urlopen(req, timeout=60) as resp:
                contenido = resp.read()
        except Exception as e:
            return {"ok": False, "error": f"no se pudo descargar: {e}"}

        if destino:
            with open(destino, "wb") as f:
                f.write(contenido)

        return {
            "ok": True,
            "bytes": len(contenido),
            "destino": destino or "",
            "nombreDocumento": descarga.get("nombreDocumento", ""),
            "es_pdf": contenido[:4] == b"%PDF",
        }

    def get_actos_direcciones_regionales(self, anio: int = 2026, direccion: Optional[str] = None,
                                        use_cache: bool = True) -> List[Dict[str, Any]]:
        """Indexa los actos y resoluciones que las direcciones regionales y unidades del SII publican por año.

        La página maestra del año enlaza un índice por dirección (Metropolitana Centro, Valparaíso,
        Grandes Contribuyentes, Fiscalización…), y cada índice es una tabla con el número, la fecha,
        la materia y el PDF del acto. Se puede pedir una sola dirección —`direccion="valparaiso"`—
        para no traer el país entero cuando se busca un caso puntual.
        """
        cache_key = f"actos_ddrr_{anio}"
        cache_file = self._get_cache_path(cache_key)
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    actos = json.load(f)
                return self._filtrar_por_direccion(actos, direccion)
            except Exception:
                pass

        maestro = SII_ACTOS_MAESTRO.format(base=BASE_URL, anio=anio)
        headers = {'User-Agent': 'OpenLegalChile/1.0 (Derecho Tributario Chile)'}
        try:
            with safe_urlopen(urllib.request.Request(maestro, headers=headers), timeout=30) as resp:
                html_maestro = resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            return [_aviso(
                f"No se pudo cargar el índice de actos y resoluciones {anio}",
                f"La página maestra del SII no respondió ({e}). Esto NO significa que no haya actos "
                "publicados ese año.",
            )]

        indices = []
        for href, texto in re.findall(r'<a[^>]+href=["\']([^"\']*normativa_ddrr[^"\']*)["\'][^>]*>(.*?)</a>',
                                      html_maestro, re.IGNORECASE | re.DOTALL):
            url_indice = urllib.parse.urljoin(maestro, href.strip())
            indices.append({"direccion": _texto_plano(texto), "url": url_indice})

        if not indices:
            return [_aviso(
                f"El índice de actos y resoluciones {anio} no listó direcciones",
                "La página respondió pero sin enlaces a índices de direcciones: probablemente cambió "
                "su estructura y hay que actualizar el parser.",
            )]

        actos: List[Dict[str, Any]] = []
        fallos: List[str] = []
        for indice in indices:
            base_pdfs = indice["url"].rsplit("/", 1)[0]
            try:
                with safe_urlopen(urllib.request.Request(indice["url"], headers=headers), timeout=45) as resp:
                    pagina = resp.read().decode("utf-8", errors="ignore")
            except Exception as e:
                fallos.append(f"{indice['direccion']}: {e}")
                continue
            actos.extend(_parsear_actos_ddrr(pagina, indice["direccion"], base_pdfs))

        if actos:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(actos, f, ensure_ascii=False, indent=2)
            return self._filtrar_por_direccion(actos, direccion, fallos)

        return [_aviso(
            f"No se pudieron leer los actos y resoluciones {anio}",
            "Ninguna dirección entregó actos (" + ("; ".join(fallos) if fallos else "índices vacíos") +
            "). Esto NO significa que no existan actos de ese año.",
        )]

    @staticmethod
    def _filtrar_por_direccion(actos: List[Dict[str, Any]], direccion: Optional[str],
                               fallos: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if not direccion:
            return actos
        foco = _texto_plano(direccion).lower()
        filtrados = [a for a in actos if foco in str(a.get("direccion", "")).lower()]
        if filtrados:
            return filtrados
        disponibles = sorted({str(a.get("direccion", "")) for a in actos})
        return [_aviso(
            f"No se encontró una dirección que coincida con «{direccion}»",
            "Direcciones disponibles: " + "; ".join(disponibles),
        )]

    def buscar_actos_regionales(self, query: str, anio: int = 2026,
                                direccion: Optional[str] = None) -> List[Dict[str, Any]]:
        """Busca en los actos y resoluciones de las direcciones regionales del SII por número o tema."""
        actos = self.get_actos_direcciones_regionales(anio=anio, direccion=direccion)
        if actos and isinstance(actos[0], dict) and actos[0].get("tipo") == "aviso":
            return actos

        q = query.lower().strip()
        matches = [
            a for a in actos
            if q == str(a.get("numero", "")).lower()
            or _coincide(f"{a.get('materia', '')} {a.get('descripcion', '')} {a.get('titulo', '')}", q)
        ]
        if matches:
            return matches

        return [_aviso(
            f"Sin actos regionales para «{query}» en {anio}",
            f"Se buscó en el número, la materia y la descripción de los {len(actos)} actos indexados "
            "de ese año.",
        )]

    def get_convenios_internacionales(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Indexa el cuadro de convenios tributarios internacionales que publica el SII.

        Incluye convenios para evitar la doble imposición, la convención multilateral, convenios de
        transporte internacional y convenios de intercambio de información, con el país, la fecha de
        aplicación en Chile, la autoridad competente y los textos en español e inglés.
        """
        cache_file = self._get_cache_path("convenios_internacionales")
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        url = f"{BASE_URL}/convenios_internacionales.html"
        headers = {'User-Agent': 'OpenLegalChile/1.0 (Derecho Tributario Chile)'}
        try:
            with safe_urlopen(urllib.request.Request(url, headers=headers), timeout=30) as resp:
                pagina = resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            return [_aviso(
                "No se pudo cargar el cuadro de convenios tributarios internacionales",
                f"El sitio del SII no respondió ({e}). Esto NO significa que no existan convenios.",
            )]

        convenios = _parsear_convenios(pagina)
        if not convenios:
            return [_aviso(
                "El cuadro de convenios internacionales no entregó filas",
                "La página respondió pero no se reconoció ninguna fila: probablemente cambió su "
                "estructura y hay que actualizar el parser.",
            )]

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(convenios, f, ensure_ascii=False, indent=2)
        return convenios

    def buscar_convenios(self, query: str) -> List[Dict[str, Any]]:
        """Busca un convenio tributario internacional por país, documento relacionado o autoridad."""
        convenios = self.get_convenios_internacionales()
        if convenios and isinstance(convenios[0], dict) and convenios[0].get("tipo") == "aviso":
            return convenios

        q = query.lower().strip()
        matches = [
            c for c in convenios
            if _coincide(f"{c.get('pais', '')} {c.get('documentos_relacionados', '')} "
                         f"{c.get('autoridad_competente', '')}", q)
        ]
        if matches:
            return matches

        paises = sorted({str(c.get("pais", "")) for c in convenios})
        return [_aviso(
            f"Sin convenio tributario para «{query}»",
            "Se buscó en el país, la autoridad competente y los documentos relacionados. Países con "
            "convenio vigente o en trámite: " + ", ".join(paises),
        )]

    def get_jurisprudencia_judicial(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Indexa las sentencias de la jurisprudencia judicial del SII (tribunales tributarios y cortes).

        Son las sentencias en que el SII ha sido parte (Tribunales Tributarios y Aduaneros, Cortes de
        Apelaciones, Corte Suprema): 3.613 pronunciamientos entre 2008 y 2026, con las partes, el RUC,
        la decisión, el resultado y los artículos que cada sentencia cita.
        """
        cache_file = self._get_cache_path("jurisprudencia_judicial")
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        datos = {
            "orderByField": "fecha",
            "orderByOrder": "desc",
            "conditions": [{"field": "codigoPronunciamiento", "operator": "like",
                            "value": "%", "caseInsensitive": True}],
        }
        req = urllib.request.Request(
            f"{SII_JUDICIAL_BASE}/services/data/internetService/pronunciamientos/filter",
            data=_sobre_acjui("filterPronunciamientos", datos),
            headers={'User-Agent': 'OpenLegalChile/1.0 (Derecho Jurisprudencial Chile)',
                     'Content-Type': 'application/json'},
        )
        try:
            with safe_urlopen(req, timeout=120) as resp:
                respuesta = json.loads(resp.read().decode("utf-8", errors="ignore"))
        except Exception as e:
            return [_aviso(
                "No se pudo cargar la jurisprudencia judicial del SII",
                f"El servicio no respondió ({e}). Esto NO significa que no existan sentencias.",
            )]

        errores = (respuesta.get("metaData") or {}).get("errors")
        if errores:
            return [_aviso(
                "El servicio de jurisprudencia judicial del SII respondió con error",
                f"{errores}. Suele ocurrir si el Servicio cambia el protocolo de su buscador.",
            )]

        sentencias = [_normalizar_sentencia(d) for d in (respuesta.get("data") or []) if isinstance(d, dict)]
        if not sentencias:
            return [_aviso(
                "El buscador judicial del SII no entregó sentencias",
                "Respondió sin datos: probablemente cambió el formato de su respuesta.",
            )]

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(sentencias, f, ensure_ascii=False, indent=2)
        return sentencias

    def buscar_jurisprudencia_judicial(self, query: str = "", desde: Optional[str] = None,
                                       hasta: Optional[str] = None,
                                       tribunal: Optional[str] = None,
                                       limite: int = 20) -> List[Dict[str, Any]]:
        """Busca sentencias de la jurisprudencia judicial del SII por partes, materia, código o artículo.

        `desde` y `hasta` son fechas ISO (aaaa-mm-dd) y `tribunal` filtra por nombre de tribunal.
        """
        sentencias = self.get_jurisprudencia_judicial()
        if sentencias and isinstance(sentencias[0], dict) and sentencias[0].get("tipo") == "aviso":
            return sentencias

        q = (query or "").lower().strip()
        foco_tribunal = (tribunal or "").lower().strip()
        encontradas = []
        for s in sentencias:
            if desde and str(s.get("fecha", "")) < desde:
                continue
            if hasta and str(s.get("fecha", "")) > hasta:
                continue
            if foco_tribunal and foco_tribunal not in str(s.get("tribunal", "")).lower():
                continue
            if q:
                articulos = " ".join(
                    f"{a.get('cuerpo_normativo', '')} {a.get('numero', '')} {a.get('nombre', '')}"
                    for a in s.get("articulos") or []
                )
                texto = (f"{s.get('partes', '')} {s.get('extracto', '')} {s.get('codigo', '')} "
                         f"{s.get('ruc', '')} {s.get('decision', '')} {s.get('resultado', '')} "
                         f"{s.get('tribunal', '')} {articulos}")
                if not _coincide(texto, q):
                    continue
            encontradas.append(s)
            if len(encontradas) >= limite:
                break

        if encontradas:
            return encontradas

        return [_aviso(
            f"Sin sentencias del SII para «{query}»"
            + (f" entre {desde} y {hasta}" if desde or hasta else ""),
            f"Se buscó en las partes, el extracto, el código, el RUC, la decisión y los artículos "
            f"citados de las {len(sentencias)} sentencias indexadas. El buscador del SII mezcla "
            "nombres de contribuyentes: si buscas una materia, prueba con la palabra que usaría el "
            "Servicio o con el número de artículo.",
        )]

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
                    texto = (f"{item.get('titulo', '')} {item.get('materia', '')} "
                             f"{item.get('materia_legal', '')}")
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
