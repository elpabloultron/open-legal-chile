"""
Los buscadores por TEMA tenían que funcionar de verdad.

Los índices del SII, la DT y la CMF publican, junto a cada documento, su MATERIA (el resumen
oficial), y los conectores la descartaban: guardaban sólo el número —«Circular N° 35 del 31 de
Agosto del 2026», «ORD.N°377»— de modo que buscar «renta», «despido» o «impugnación» devolvía
SIEMPRE cero resultados, y eso se lee como «no hay nada sobre esto».

Caso real que lo destapó (18-09-2026): al auditar el conector ante una consulta tributaria, cuatro
de las búsquedas institucionales devolvían vacío. Además, dos índices del SII (resoluciones y
oficios) apuntaban a direcciones que hoy devuelven 404, y el de sanciones de la CMF también.

Estas pruebas fijan tres cosas, sin tocar la red:
 1. que la materia se extraiga del HTML oficial (con sus entidades y su estructura reales),
 2. que la búsqueda por tema la use —y que no confunda «IVA» con «administratIVA»—,
 3. que un vacío o una fuente caída se EXPLIQUEN, en vez de devolver una lista muda.
"""

import cmf_connector
from cmf_connector import CMFClient, _parsear_sanciones_cmf
from dt_connector import DTClient, _parsear_indice_dt
from sii_connector import SIIClient, _coincide, _parsear_indice_sii

# --- HTML de ejemplo, calcado de las páginas oficiales -----------------------------------------

HTML_SII = """
<h5 style='margin-bottom:0px;'><a href='circu35.pdf' target='_blank'>Circular N&deg; 35 del 31 de
Agosto del 2026</a></h5> <p style='margin-top:0px;margin-bottom:0px;'>Actualiza instrucciones sobre
mecanismos de impugnaci&oacute;n administrativa: RAV, RAF y Recurso Jer&aacute;rquico.</p>
<span style='font-size:12px;margin-bottom:10px;'><i>Fuente: Subdirecci&oacute;n Jur&iacute;dica</i></span>
<h5 style='margin-bottom:0px;'><a href='circu36.pdf' target='_blank'>Circular N&deg; 36 del 10 de
Septiembre del 2026</a></h5> <p style='margin-top:0px;margin-bottom:0px;'>Informa tabla de
c&aacute;lculos de reajustes y multas para el mes de octubre 2026</p>
"""

HTML_DT = """
<div class="recuadro"><h3 class="titulo aid-129618 cid-900"><a href="w3-article-129618.html"
title="1) La gente de mar comprendida en el régimen especial...">ORD.N°377</a></h3><h6
class="fecha cid-900 aid-129639 pnid-2294 iso8601-20260831T0000000400">31/08/2026</h6><p
class="abstract aid-129639 cid-900">La reducci&oacute;n de la jornada ordinaria de trabajo dispuesta
por la Ley N&ordm;21.561 no es aplicable a los asistentes de la educaci&oacute;n.</p></div>
<div class="recuadro"><h3 class="titulo aid-129600 cid-900"><a href="w3-article-129600.html"
title="Despido por el artículo 161...">ORD.N°138</a></h3><h6
class="fecha cid-900 aid-129600 iso8601-20260217T0000000400">17/02/2026</h6><p
class="abstract aid-129600 cid-900">El empleador, s&oacute;lo en el caso de despido por el
art&iacute;culo 161 del C&oacute;digo del Trabajo, se encuentra facultado para descontar de la
indemnizaci&oacute;n.</p></div>
"""

HTML_CMF = """
<table>
<tr><th>N&ordm;</th><th>FECHA</th><th>MATERIA</th><th>ARCHIVO</th></tr>
<tr><td>8401</td><td>11.08.2026</td><td>APLICA SANCI&Oacute;N A UNIDAD MUTUOS HIPOTECARIOS S.A.</td>
<td> <a href=/sitio/aplic/serdoc/ver_sgd.php?s567=abc123&secuencia=-1&t=1789759464 class="mime_doc">Descargar</a> </td></tr>
<tr><td>6491</td><td>20.06.2026</td><td>RESUELVE REPOSICI&Oacute;N DEDUCIDA POR ORSAN SEGUROS DE
CR&Eacute;DITO y GARANT&Iacute;A S.A.</td><td><a href="articles-456_doc_pdf.pdf">Descargar</a></td></tr>
</table>
"""


# --- 1. La materia se extrae del HTML ----------------------------------------------------------

def test_la_materia_del_sii_se_extrae_y_se_limpia():
    items = _parsear_indice_sii(HTML_SII, 2026, "circulares", "https://www.sii.cl/normativa_legislacion")

    assert len(items) == 2
    primero = items[0]
    assert primero["numero"] == ""          # el número lo completa el conector con su propio patrón
    assert "Circular N° 35" in primero["titulo"]
    assert "mecanismos de impugnación administrativa" in primero["materia"]
    assert primero["fuente"] == "Fuente: Subdirección Jurídica"
    assert primero["pdfUrl"].startswith("https://www.sii.cl/normativa_legislacion/circulares/2026/")


def test_la_materia_del_dt_se_extrae_con_fecha():
    items = _parsear_indice_dt(HTML_DT, "https://www.dt.gob.cl/legislacion/1624")

    assert [i["numero"] for i in items] == ["ORD.N°377", "ORD.N°138"]
    assert items[0]["articleId"] == "129618"
    assert items[0]["fecha"] == "31/08/2026"
    assert "jornada ordinaria de trabajo" in items[0]["materia"]
    assert items[1]["materia"].startswith("El empleador, sólo en el caso de despido")
    assert items[0]["link"] == "https://www.dt.gob.cl/legislacion/1624/w3-article-129618.html"


def test_las_sanciones_del_cmf_se_extraen_de_la_tabla():
    filas = _parsear_sanciones_cmf(HTML_CMF)

    assert len(filas) == 2, "la fila de encabezado no es una sanción"
    assert filas[0]["numero"] == "8401"
    assert filas[0]["fecha"] == "11.08.2026"
    assert filas[0]["materia"] == "APLICA SANCIÓN A UNIDAD MUTUOS HIPOTECARIOS S.A."
    # El enlace real viene sin comillas y relativo: hay que dejarlo absoluto igualmente.
    assert filas[0]["url"].startswith("https://www.cmfchile.cl/sitio/aplic/serdoc/ver_sgd.php")
    assert filas[1]["url"].endswith("articles-456_doc_pdf.pdf")


# --- 2. La búsqueda por tema usa la materia ----------------------------------------------------

def test_el_sii_encuentra_por_tema_y_no_confunde_iva_con_administrativa(monkeypatch, tmp_path):
    sii = SIIClient(cache_dir=str(tmp_path))
    monkeypatch.setattr(
        sii, "get_circulares_por_anio",
        lambda anio=2026, use_cache=True: _parsear_indice_sii(
            HTML_SII, anio, "circulares", "https://www.sii.cl/normativa_legislacion"),
    )

    assert len(sii.search_circulares("impugnación", anios=[2026])) == 1
    assert len(sii.search_circulares("reajustes", anios=[2026])) == 1

    # «IVA» está dentro de «administratIVA»: coincidencia por trozo daría un falso positivo.
    assert _coincide("Actualiza instrucciones sobre mecanismos de impugnación administrativa", "IVA") is False
    res = sii.search_circulares("IVA", anios=[2026])
    assert res and res[0]["tipo"] == "aviso", f"«IVA» no debía encontrar nada, llegó: {res}"
    assert "impugnación" in res[0]["titulo"] or "IVA" in res[0]["titulo"]


def test_el_dt_encuentra_por_tema(monkeypatch, tmp_path):
    dt = DTClient(cache_dir=str(tmp_path))
    monkeypatch.setattr(
        dt, "get_index_ordinarios",
        lambda use_cache=True: _parsear_indice_dt(HTML_DT, "https://www.dt.gob.cl/legislacion/1624"),
    )

    res = dt.search_dictamenes("despido", limit=5)
    assert [r["numero"] for r in res] == ["ORD.N°138"], "la búsqueda por tema es sobre la materia"
    assert "despido" in res[0]["materia"]

    res = dt.search_dictamenes("jornada", limit=5)
    assert [r["numero"] for r in res] == ["ORD.N°377"]


def test_la_cmf_encuentra_por_materia(monkeypatch, tmp_path):
    cmf = CMFClient(cache_dir=str(tmp_path))
    monkeypatch.setattr(cmf, "get_sanciones", lambda use_cache=True: _parsear_sanciones_cmf(HTML_CMF))

    res = cmf.search_sanciones("mutuos hipotecarios", limit=5)
    assert len(res) == 1 and res[0]["numero"] == "8401"

    res = cmf.search_sanciones("no existe este término", limit=5)
    assert res and res[0]["tipo"] == "aviso", "un vacío tiene que explicarse"


# --- 3. Un vacío o una fuente caída se explican ------------------------------------------------

def test_un_indice_caido_avisa_y_no_miente_con_un_vacio(monkeypatch, tmp_path):
    """La dirección del SII para resoluciones y oficios devuelve 404: hay que decirlo."""
    sii = SIIClient(cache_dir=str(tmp_path))
    monkeypatch.setattr(
        sii, "get_resoluciones_por_anio",
        lambda anio=2026, use_cache=True: [{
            "tipo": "aviso",
            "titulo": f"No se pudo cargar el índice de resoluciones exentas {anio}",
            "mensaje": "La dirección ya no responde (404)…",
        }],
    )
    monkeypatch.setattr(sii, "get_oficios_por_anio", lambda anio=2026, use_cache=True: [])

    res = sii.search_resoluciones_y_oficios("renta", anios=[2026])

    assert res, "no puede volver vacío"
    assert res[0]["tipo"] == "aviso"
    assert "404" in res[0]["mensaje"]


def test_la_cmf_avisa_cuando_no_puede_cargar_sanciones(monkeypatch, tmp_path):
    def sin_red(*argumentos, **clave):
        raise RuntimeError("sin red")

    monkeypatch.setattr(cmf_connector, "safe_urlopen", sin_red)
    cmf = CMFClient(cache_dir=str(tmp_path))

    res = cmf.get_sanciones()

    assert res and res[0]["tipo"] == "aviso"
    assert "NO significa" in res[0]["mensaje"], "el aviso debe aclarar que no es «no existen»"


# --- 4. SII: resoluciones exentas y jurisprudencia administrativa ------------------------------

def test_el_numero_de_una_resolucion_exenta_sale_del_titulo_real():
    from sii_connector import _numero_resolucion_sii

    # El título real lleva «SII» entre «Exenta» y el número.
    assert _numero_resolucion_sii("Resolución Exenta SII N° 128 del 16 de Septiembre del 2026") == "128"
    assert _numero_resolucion_sii("Resoluci&oacute;n Exenta SII N&deg; 6 del 05 de Enero del 2026") == ""
    assert _numero_resolucion_sii("Resolución Exenta N° 77 de 2022") == "77"
    assert _numero_resolucion_sii("Circular N° 35 del 31 de Agosto del 2026") == ""


def test_la_jurisprudencia_administrativa_se_normaliza_con_su_cita_legal():
    """La API del SII entrega pubResumen (materia) y pubLegal (referencia normativa que cita)."""
    from sii_connector import _normalizar_oficio

    dato = {
        "pubNumOficio": "2407",
        "pubFechaPubli": "16/09/2026",
        "pubResumen": "Inversión en acciones o derechos sociales efectuada por sociedad autorizada.",
        "pubLegal": "Renta – Ley sobre Impuesto a la – Art. 29, Art. 30 – Código Tributario – Art. 18",
        "tipoArchPublica": "Oficio",
        "extensionArchPublica": "pdf",
        "idBlobArchPublica": "123456",
        "mTypeArchPublica": "application/pdf",
    }
    oficio = _normalizar_oficio(dato, 2026, "Renta", "ley_impuesto_renta", "https://www.sii.cl/normativa_legislacion")

    assert oficio["numero"] == "2407"
    assert oficio["fecha"] == "16/09/2026"
    assert "Inversión en acciones" in oficio["materia"]
    assert "Art. 30" in oficio["materia_legal"]
    assert oficio["descarga"]["nombreDocumento"] == "2407-16/09/2026.pdf"
    assert oficio["descarga"]["id"] == "123456"
    assert oficio["url"].endswith("ley_impuesto_renta/2026/ley_impuesto_renta_jadm2026.htm")


def test_descargar_oficio_sin_datos_de_descarga_no_hace_la_peticion(tmp_path):
    """Sin el identificador del archivo no hay nada que bajar: se dice, no se falla en silencio."""
    sii = SIIClient(cache_dir=str(tmp_path))

    res = sii.descargar_oficio({"numero": "2407", "fecha": "16/09/2026", "descarga": {}})

    assert res["ok"] is False
    assert "id" in res["error"]


def test_la_jurisprudencia_administrativa_avisa_si_el_servicio_no_responde(monkeypatch, tmp_path):
    import sii_connector

    def sin_red(*argumentos, **clave):
        raise RuntimeError("servicio caído")

    monkeypatch.setattr(sii_connector, "safe_urlopen", sin_red)
    sii = SIIClient(cache_dir=str(tmp_path))

    res = sii.get_oficios_por_anio(2026)

    assert res and res[0]["tipo"] == "aviso"
    assert "NO significa" in res[0]["mensaje"]


# --- 5. SII: actos regionales, convenios internacionales y jurisprudencia judicial --------------

HTML_ACTOS = """
<table>
<tr><td></td><td></td><td></td><td></td><td>Nombre/título</td><td></td><td></td>
<td>Breve descripción del objeto del acto</td><td></td><td></td><td></td></tr>
<tr><td>2026</td><td>Julio</td><td>Instrucciones, dictámenes y circulares</td><td>Resolución</td>
<td>1305370</td><td>24-07-2026</td><td>CONDONACIÓN</td><td>OTORGA CONDONACIÓN QUE INDICA</td>
<td>6-8-2026</td><td>Sitio Web Institucional</td>
<td><a href="reso1305370_83902.pdf">Ver Documento</a></td><td>NO</td><td>No</td><td>No aplica</td>
<td>No aplica</td></tr>
</table>
"""

HTML_CONVENIOS = """
<h3>Convenios para evitar la doble imposición</h3>
<table>
<tr><th>País/ Country</th><th>Texto/Text</th><th>Autoridad Competente</th>
<th>Fecha de Aplicación en Chile</th><th>Documentos Relacionados</th></tr>
<tr><td>Argentina</td><td><a href="chile_argentina.pdf">Español</a></td>
<td>Ministro de Hacienda y Director SII</td><td>01.01.2017</td>
<td><a href="circu27.pdf">Circular N° 27 de 2019</a></td></tr>
</table>
<h3>Convenios de intercambio de información</h3>
<table>
<tr><th>País/ Country</th><th>Texto/Text</th></tr>
<tr><td>Bermudas</td><td><a href="bermudas.pdf">Español</a></td></tr>
</table>
<h3>Convenios de transporte internacional</h3>
<table>
<tr><td>Alemania (marítimo)</td></tr>
</table>
"""


def test_los_actos_regionales_se_extraen_y_no_entra_la_fila_de_instrucciones():
    from sii_connector import _parsear_actos_ddrr

    actos = _parsear_actos_ddrr(HTML_ACTOS, "D. R. Metropolitana Centro",
                                "https://www.sii.cl/documentos/normativa_ddrr/2026/centro")

    assert len(actos) == 1, f"la fila de instrucciones no es un acto: {actos}"
    acto = actos[0]
    assert acto["numero"] == "1305370"
    assert acto["fecha"] == "24-07-2026"
    assert acto["materia"] == "CONDONACIÓN"
    assert acto["tipo"] == "Resolución"
    assert acto["direccion"] == "D. R. Metropolitana Centro"
    assert acto["pdfUrl"].endswith("/documentos/normativa_ddrr/2026/centro/reso1305370_83902.pdf")


def test_los_convenios_se_extraen_de_todas_las_tablas():
    """La página tiene ocho tablas de 5, 3, 2 y 1 columnas: hay que leerlas todas."""
    from sii_connector import _parsear_convenios

    convenios = _parsear_convenios(HTML_CONVENIOS)

    assert len(convenios) == 3, f"se esperaban los tres convenios: {convenios}"
    doble = next(c for c in convenios if c["pais"] == "Argentina")
    assert doble["fecha_aplicacion_chile"] == "01.01.2017"
    assert doble["autoridad_competente"].startswith("Ministro de Hacienda")
    assert "doble imposición" in doble["seccion"]
    assert doble["archivos"][0]["url"] == "chile_argentina.pdf"

    intercambio = next(c for c in convenios if c["pais"] == "Bermudas")
    assert "intercambio de información" in intercambio["seccion"], "la sección se arrastra del título"

    transporte = next(c for c in convenios if "Alemania" in c["pais"])
    assert "transporte" in transporte["seccion"]


def test_la_sentencia_judicial_se_normaliza_con_tribunal_decision_y_articulos():
    from sii_connector import _normalizar_sentencia

    dato = {
        "id": 24515,
        "partes": "SII con Tercer Tribunal Tributario y Aduanero de la Región Metropolitana",
        "ruc": "25-9-0000146-4",
        "fecha": "2026-04-15",
        "codigoPronunciamiento": "112-2026",
        "contenido": "Extracto de la sentencia.",
        "urlDocumento": None,
        "instancia": {"id": 7, "nombre": "Corte de Apelaciones de Santiago"},
        "decision": {"id": 1, "nombre": "Ha Lugar"},
        "resultado": {"nombre": "Revoca"},
        "tipoPronunciamiento": {"nombre": "Sentencia"},
        "pronunciamientosArticulos": [{
            "articulo": {"numero": 31, "nombre": "Artículo 31",
                         "tituloBO": {"cuerpoNormativo": {"nombre": "Ley sobre Impuesto a la Renta"}}}
        }],
    }

    s = _normalizar_sentencia(dato)

    assert s["codigo"] == "112-2026"
    assert s["fecha"] == "2026-04-15"
    assert s["tribunal"] == "Corte de Apelaciones de Santiago"
    assert s["decision"] == "Ha Lugar"
    assert s["resultado"] == "Revoca"
    assert s["extracto"] == "Extracto de la sentencia."
    assert s["articulos"][0]["cuerpo_normativo"] == "Ley sobre Impuesto a la Renta"
    assert "112-2026" in s["titulo"]


def test_el_sobre_de_la_jurisprudencia_judicial_usa_el_token_del_sitio():
    """El protocolo es POST con metaData/data; el token es el respaldo que usa la propia página."""
    import json as _json

    from sii_connector import SII_JUDICIAL_TOKEN, _sobre_acjui

    cuerpo = _json.loads(_sobre_acjui("filterPronunciamientos", {"conditions": []}))

    assert SII_JUDICIAL_TOKEN == "####"
    assert cuerpo["metaData"]["conversationId"] == SII_JUDICIAL_TOKEN
    assert cuerpo["metaData"]["namespace"].endswith(
        "InternetApplicationService/filterPronunciamientos")
    assert cuerpo["data"] == {"conditions": []}


def test_la_jurisprudencia_judicial_avisa_si_el_servicio_no_responde(monkeypatch, tmp_path):
    import sii_connector

    def sin_red(*argumentos, **clave):
        raise RuntimeError("servicio caído")

    monkeypatch.setattr(sii_connector, "safe_urlopen", sin_red)
    sii = SIIClient(cache_dir=str(tmp_path))

    res = sii.get_jurisprudencia_judicial()

    assert res and res[0]["tipo"] == "aviso"
    assert "NO significa" in res[0]["mensaje"]
