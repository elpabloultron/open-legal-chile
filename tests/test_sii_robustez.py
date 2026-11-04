"""
El buscador del SII tenía que encontrar lo que el SII sí publicó, y dejar leerlo.

Caso real (02-10-2026): consultando por una sociedad de profesionales, «sociedad de profesionales»
no encontraba la Res. Ex. 82/2024, porque su materia dice «sociedades de profesionales»; y
«profesionales» no encontraba la Circular 50/2022, cuya materia sólo nombra «la Ley N° 21.420».
Además, el PDF de un oficio se descargaba y se descartaba si no se indicaba destino, y no había
forma de leer el texto íntegro de una circular, resolución u oficio: la materia es un resumen de una
línea y con eso no se puede citar.

Estas pruebas fijan, sin tocar la red:
 1. que la búsqueda no dependa de tildes, plural ni orden, sin volver a confundir «IVA» con
    «administratIVA», y que «21420» encuentre «21.420»;
 2. que la frase exacta y el número salgan antes que las coincidencias por palabras, y que un año
    caído se avise aunque otros años sí traigan resultados;
 3. que `leer_documento` ubique el documento, baje el PDF a la caché, devuelva su texto y avise
    si es un escaneo o si el número es ambiguo;
 4. que la herramienta MCP pase los años pedidos y exponga la lectura.
"""

import pymupdf
import pytest

import mcp_server
import sii_connector
from sii_connector import SIIClient, _coincide, _puntaje

RES_82 = {
    "anio": 2024, "numero": "82", "tipo": "Resolución Exenta SII",
    "titulo": "Resolución Exenta SII N° 82 del 29 de Agosto del 2024",
    "materia": "Procedimiento de exclusión del registro de sociedades de profesionales por "
               "incumplimiento de requisitos.",
    "pdfUrl": "https://www.sii.cl/normativa_legislacion/resoluciones/2024/reso82.pdf",
}
CIRC_50 = {
    "anio": 2022, "numero": "50", "titulo": "Circular N° 50 del 27 de Octubre del 2022",
    "materia": "Imparte instrucciones sobre las modificaciones introducidas por los números 1 y 2 "
               "del artículo 6 de la Ley N° 21.420, a los artículos 2° N° 2°) y 12 letra E de la Ley "
               "sobre Impuesto a las Ventas y Servicios.",
    "pdfUrl": "https://www.sii.cl/normativa_legislacion/circulares/2022/circu50.pdf",
}


def _oficio(numero, fecha, serie, materia):
    return {
        "anio": 2026, "numero": numero, "fecha": fecha, "serie": serie, "materia": materia,
        "materia_legal": "", "titulo": f"Oficio N° {numero} de {fecha}",
        "descarga": {"nombreDocumento": f"{numero}.pdf", "extension": "pdf", "id": "abc",
                     "mediaType": "application/pdf"},
    }


def _pdf(texto=None) -> bytes:
    doc = pymupdf.open()
    pagina = doc.new_page()
    if texto:
        pagina.insert_text((72, 72), texto)
    contenido = doc.tobytes()
    doc.close()
    return contenido


class _Respuesta:
    def __init__(self, contenido):
        self._contenido = contenido

    def read(self):
        return self._contenido

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


# --- 1. Tildes, plural, orden y números ---------------------------------------------------------

def test_singular_encuentra_plural_y_sin_tildes():
    materia = RES_82["materia"]
    assert _coincide(materia, "sociedad de profesionales")
    assert _coincide(materia, "profesionales sociedad")
    assert _coincide(materia, "exclusion registro")
    assert _coincide("Sociedad de profesionales acogida a las normas de primera categoría.",
                     "primera categoria")


def test_iva_sigue_sin_confundirse_con_administrativa():
    texto = "Actualiza instrucciones sobre mecanismos de impugnación administrativa"
    assert _coincide(texto, "IVA") is False
    assert _coincide(texto, "impugnaciones administrativas")


def test_un_numero_de_ley_se_encuentra_con_o_sin_puntos():
    assert _coincide(CIRC_50["materia"], "21420")
    assert _coincide(CIRC_50["materia"], "21.420")
    assert _coincide(CIRC_50["materia"], "Ley 21.420")
    assert not _coincide(CIRC_50["materia"], "21.421")


def test_una_consulta_de_solo_palabras_vacias_no_trae_el_indice_entero():
    assert _puntaje(CIRC_50["materia"], "de la") == 2  # la frase sí está tal cual
    assert _puntaje(CIRC_50["materia"], "para con") == 0


def test_la_frase_exacta_puntua_mas_que_las_palabras_sueltas():
    assert _puntaje(RES_82["materia"], "sociedades de profesionales") == 2
    assert _puntaje(RES_82["materia"], "sociedad de profesionales") == 1


# --- 2. Orden de resultados y avisos parciales --------------------------------------------------

def test_resoluciones_y_oficios_ordena_por_relevancia_y_avisa_el_anio_caido(monkeypatch, tmp_path):
    sii = SIIClient(cache_dir=str(tmp_path))
    exacto = _oficio("1873", "29/07/2026", "Renta",
                     "Sociedad de profesionales acogida a las normas de primera categoría.")
    caido = {"tipo": "aviso", "titulo": "No se pudo cargar la jurisprudencia administrativa del SII de 2023",
             "mensaje": "servicio caído"}
    monkeypatch.setattr(sii, "get_resoluciones_por_anio",
                        lambda anio, use_cache=True: [RES_82] if anio == 2024 else [])
    monkeypatch.setattr(sii, "get_oficios_por_anio",
                        lambda anio, use_cache=True: [exacto] if anio == 2026 else ([caido] if anio == 2023 else []))

    res = sii.search_resoluciones_y_oficios("sociedad de profesionales", anios=[2026, 2024, 2023])

    assert [r.get("numero") for r in res[:2]] == ["1873", "82"], "la frase exacta va primero"
    assert res[-1]["tipo"] == "aviso", "un año caído no puede desaparecer porque otro sí respondió"


def test_el_numero_exacto_gana_y_tolera_ceros_a_la_izquierda(monkeypatch, tmp_path):
    sii = SIIClient(cache_dir=str(tmp_path))
    monkeypatch.setattr(sii, "get_resoluciones_por_anio", lambda anio, use_cache=True: [])
    monkeypatch.setattr(sii, "get_oficios_por_anio", lambda anio, use_cache=True: [
        _oficio("0026", "07/01/2026", "IVA", "Servicios publicitarios prestados a sociedad de profesionales"),
    ])

    res = sii.search_resoluciones_y_oficios("26", anios=[2026])

    assert res and res[0]["numero"] == "0026"


def test_circulares_encuentra_por_la_ley_que_nombra_la_materia(monkeypatch, tmp_path):
    sii = SIIClient(cache_dir=str(tmp_path))
    monkeypatch.setattr(sii, "get_circulares_por_anio",
                        lambda anio=2026, use_cache=True: [CIRC_50] if anio == 2022 else [])

    assert [c["numero"] for c in sii.search_circulares("21420", anios=[2022])] == ["50"]
    vacio = sii.search_circulares("profesionales", anios=[2022])
    assert vacio[0]["tipo"] == "aviso" and "21.420" in vacio[0]["mensaje"], \
        "el aviso debe orientar a buscar por la norma"


def test_los_anios_por_defecto_siguen_al_calendario(monkeypatch):
    class _Reloj:
        @staticmethod
        def now():
            from datetime import datetime
            return datetime(2031, 3, 1)

    monkeypatch.setattr(sii_connector, "datetime", _Reloj)
    assert sii_connector._anios_recientes(3) == [2031, 2030, 2029]


# --- 3. Leer el texto íntegro -------------------------------------------------------------------

def test_leer_una_circular_baja_el_pdf_y_devuelve_el_texto(monkeypatch, tmp_path):
    sii = SIIClient(cache_dir=str(tmp_path))
    monkeypatch.setattr(sii, "get_circulares_por_anio", lambda anio=2026, use_cache=True: [CIRC_50])
    pedidas = []

    def falso_urlopen(req, timeout=None):
        pedidas.append(req.full_url)
        return _Respuesta(_pdf("Sociedades de profesionales: requisitos."))

    monkeypatch.setattr(sii_connector, "safe_urlopen", falso_urlopen)

    res = sii.leer_documento("circular", "50", 2022)

    assert res["ok"] is True
    assert "Sociedades de profesionales" in res["texto"]
    assert res["paginas"] == 1 and res["truncado"] is False
    assert pedidas == [CIRC_50["pdfUrl"]]
    with open(res["archivo_texto"], encoding="utf-8") as f:
        assert "requisitos" in f.read()

    # La segunda lectura sale de la caché, sin red.
    monkeypatch.setattr(sii_connector, "safe_urlopen", lambda *a, **k: pytest.fail("no debía ir a la red"))
    assert sii.leer_documento("Circular", "050", 2022)["texto"] == res["texto"]


def test_leer_trunca_pero_conserva_el_texto_completo_en_disco(monkeypatch, tmp_path):
    sii = SIIClient(cache_dir=str(tmp_path))
    monkeypatch.setattr(sii, "get_resoluciones_por_anio", lambda anio=2026, use_cache=True: [RES_82])
    monkeypatch.setattr(sii_connector, "safe_urlopen",
                        lambda req, timeout=None: _Respuesta(_pdf("Procedimiento de exclusion del registro.")))

    res = sii.leer_documento("resolución", "82", 2024, max_caracteres=10)

    assert res["truncado"] is True and len(res["texto"]) == 10
    with open(res["archivo_texto"], encoding="utf-8") as f:
        assert len(f.read()) == res["caracteres"] > 10


def test_un_escaneo_se_avisa_en_vez_de_devolver_texto_vacio(monkeypatch, tmp_path):
    sii = SIIClient(cache_dir=str(tmp_path))
    monkeypatch.setattr(sii, "get_circulares_por_anio", lambda anio=2026, use_cache=True: [CIRC_50])
    monkeypatch.setattr(sii_connector, "safe_urlopen", lambda req, timeout=None: _Respuesta(_pdf()))

    res = sii.leer_documento("circular", "50", 2022)

    assert res["ok"] is True and res["texto"] == ""
    assert "ocr_extract_pdf" in res["aviso"]


def test_un_oficio_con_numero_repetido_pide_la_fecha(monkeypatch, tmp_path):
    sii = SIIClient(cache_dir=str(tmp_path))
    monkeypatch.setattr(sii, "get_oficios_por_anio", lambda anio=2026, use_cache=True: [
        _oficio("120", "10/01/2026", "Renta", "Uno"),
        _oficio("120", "15/03/2026", "IVA", "Otro"),
    ])

    res = sii.leer_documento("oficio", "120", 2026)

    assert res["ok"] is False and len(res["candidatos"]) == 2

    monkeypatch.setattr(sii_connector, "safe_urlopen",
                        lambda req, timeout=None: _Respuesta(_pdf("Texto del oficio de IVA.")))
    res = sii.leer_documento("oficio", "120", 2026, fecha="15/03/2026")
    assert res["ok"] is True and "IVA" in res["texto"]


def test_un_documento_que_no_esta_en_el_indice_lo_dice(monkeypatch, tmp_path):
    sii = SIIClient(cache_dir=str(tmp_path))
    monkeypatch.setattr(sii, "get_circulares_por_anio", lambda anio=2026, use_cache=True: [CIRC_50])

    res = sii.leer_documento("circular", "51", 2022)
    assert res["ok"] is False and "51" in res["error"]
    assert sii.leer_documento("dictamen", "1", 2022)["ok"] is False


def test_descargar_oficio_sin_destino_lo_guarda_en_la_cache(monkeypatch, tmp_path):
    sii = SIIClient(cache_dir=str(tmp_path))
    monkeypatch.setattr(sii_connector, "safe_urlopen", lambda req, timeout=None: _Respuesta(_pdf("x")))

    res = sii.descargar_oficio(_oficio("1873", "29/07/2026", "Renta", "m"))

    assert res["ok"] and res["es_pdf"]
    assert res["destino"].startswith(str(tmp_path)) and res["destino"].endswith(".pdf")
    with open(res["destino"], "rb") as f:
        assert f.read(4) == b"%PDF"


# --- 4. Herramientas MCP ------------------------------------------------------------------------

def test_la_herramienta_de_circulares_respeta_los_anios_pedidos(monkeypatch):
    vistos = []
    monkeypatch.setattr(mcp_server.sii, "search_circulares",
                        lambda query, anios=None: vistos.append((query, anios)) or [])

    mcp_server.handle_tool_call("sii_search_circulares", {"query": "21.420", "anios": [2022]})

    assert vistos == [("21.420", [2022])]


def test_la_herramienta_de_lectura_valida_y_delega(monkeypatch):
    llamadas = []
    monkeypatch.setattr(mcp_server.sii, "leer_documento",
                        lambda *a: llamadas.append(a) or {"ok": True})

    falta = mcp_server.handle_tool_call("sii_leer_documento", {"tipo": "oficio"})
    mcp_server.handle_tool_call("sii_leer_documento",
                                {"tipo": "oficio", "numero": "1873", "anio": 2026, "fecha": "29/07/2026"})

    assert "obligatorios" in str(falta)
    assert llamadas == [("oficio", "1873", 2026, "29/07/2026", 60000)]
    assert any(t["name"] == "sii_leer_documento" for t in mcp_server.TOOLS)
