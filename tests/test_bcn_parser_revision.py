"""
Revisión adversarial del Frente 0 (parser de artículos de la BCN): casos que las pruebas originales no
fijaban y que, al mutar el código, sobrevivían.

Medido el 2026-10-07:
  · «Artículo 10-De los plazos» se leía como el artículo «10-de» (dos letras pegadas al guion);
  · el Código Penal «Artículo 313° c Las penas…» colisionaba con el 313 y se perdía;
  · un «Artículo» seguido de más de 4.300 dígitos reventaba el parser con ValueError;
  · un pedido que no estaba en el mapa recorría las 2.567 claves del Código Civil normalizándolas
    (25 ms por consulta; 200 consultas fallidas de un lote, 5 s);
  · «cuarta disposición transitoria» y «4 transitoria» no llegaban a la disposición «CUARTA.-».
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

import bcn_connector
from bcn_connector import _cabecera, _resolver_articulo, _segmentar_articulos

from test_bcn_parser import DFL_CON_ANEXA, _carpeta_cache_real, _cliente, _parsear


# ── Cabeceras ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("texto, clave", [
    ("Artículo 10-De los plazos.- Los plazos", "10"),
    ("Artículo 10-El plazo se cuenta", "10"),
    ("Artículo 248- Cierre de la investigación. Practicadas", "248"),
    ("Artículo 183-AE.- Las trabajadoras", "183-ae"),
    ("Artículo 183-A.- Es trabajo", "183-a"),
    ("Artículo 12-A del presente Código", "12-a"),
    # La leyenda «L. 19.250» de la ley modificatoria no es el sufijo «l».
    ("Art. 67\n                  L. 19.250", "67"),
    ("Art. 12 A.- Texto", "12 a"),
])
def test_una_palabra_de_dos_letras_pegada_al_guion_no_es_un_sufijo(texto, clave):
    assert _cabecera(texto)["clave"] == clave


@pytest.mark.parametrize("texto, clave", [
    ("Artículo 313° c Las penas señaladas en los artículos precedentes", "313 c"),
    ("Artículo 313° a. El que, careciendo de título", "313 a"),
    ("Artículo 313º d El que fabricare", "313 d"),
    # Sin el signo ordinal, «a» es una palabra de la frase y no parte del rótulo.
    ("Artículo 12 a Los efectos de esta ley", "12"),
    ("Artículo 12° a los efectos de esta ley", "12"),
])
def test_letra_minuscula_tras_el_signo_ordinal(texto, clave):
    assert _cabecera(texto)["clave"] == clave


def test_el_codigo_penal_313_c_no_pisa_ni_se_pierde(tmp_path):
    datos = _parsear(tmp_path, [
        ("Artículo", "ART. 313.\n\n El que, sin hallarse competentemente autorizado, elaborare sustancias"),
        ("Artículo", "Artículo 313° a. El que, careciendo de título profesional competente"),
        ("Artículo", "Artículo 313° b. El que, estando legalmente habilitado"),
        ("Artículo", "Artículo 313° c Las penas señaladas en los artículos precedentes"),
        ("Artículo", "Artículo 313° d. El que fabricare o a sabiendas expendiere"),
        ("Artículo", "Artículo 314° El que, a cualquier título, expendiere otras sustancias"),
    ])
    assert list(datos["articulos"]) == ["313", "313 a", "313 b", "313 c", "313 d", "314"]
    assert datos["articulos"]["313"].startswith("ART. 313.")
    assert datos["articulos"]["313 c"].startswith("Artículo 313° c Las penas")
    assert datos["diagnostico_articulos"]["colisiones"] == []


def test_un_numero_desmesurado_no_es_una_cabecera_ni_revienta():
    assert _cabecera("Artículo " + "9" * 5000 + ".- texto") is None
    assert _cabecera("Artículo 1" + "-" + "9" * 5000) is not None   # «Artículo 1» y un guion: sigue siendo el 1
    resultado = _segmentar_articulos([{"tipoParte": "Artículo", "texto": "Artículo " + "1" * 6000}])
    assert resultado["articulos"] == {}


# ── Resolución de pedidos ──────────────────────────────────────────────────────

def _con_anexos(anexos):
    """Un cuerpo principal 1..8 y los anexos dados, cada uno tras su marcador `Doble Articulado`."""
    partes = [("Artículo", f"Artículo {n}.- Regla {n} del texto principal.") for n in range(1, 9)]
    for anexo in anexos:
        partes.append(("Doble Articulado", ""))
        partes.extend(anexo)
    return partes


def test_un_ordinal_que_esta_en_dos_anexos_no_se_entrega(tmp_path):
    """«Artículo Segundo» en dos leyes anexas distintas: elegir una sería adivinar."""
    anexo_1 = [("Artículo", "Artículo Primero.- Uno de la primera ley."),
               ("Artículo", "Artículo Segundo.- Dos de la primera ley.")]
    anexo_2 = [("Artículo", "Artículo Primero.- Uno de la segunda ley."),
               ("Artículo", "Artículo Segundo.- Dos de la segunda ley.")]
    datos = _parsear(tmp_path, _con_anexos([anexo_1, anexo_2]))
    assert len(datos["cuerpos_anexos"]) == 2
    hallazgo, _ = _resolver_articulo(datos, "Artículo Segundo")
    assert hallazgo is None

    # Con un solo anexo que lo tenga, no hay ambigüedad y la respuesta lo marca.
    datos = _parsear(tmp_path, _con_anexos([anexo_1]))
    hallazgo, _ = _resolver_articulo(datos, "Artículo Segundo")
    assert hallazgo and hallazgo[1].startswith("Artículo Segundo.- Dos de la primera") \
        and hallazgo[2]["cuerpo"] == "anexo"


def test_un_transitorio_que_esta_en_dos_anexos_no_se_entrega(tmp_path):
    anexo_1 = [("Artículo", "Artículo 1.- Regla de la primera ley."),
               ("Artículo Transitorio", "ARTICULOS TRANSITORIOS"),
               ("Artículo", "Artículo 1º transitorio.- Transitorio de la primera ley.")]
    anexo_2 = [("Artículo", "Artículo 1.- Regla de la segunda ley."),
               ("Artículo Transitorio", "ARTICULOS TRANSITORIOS"),
               ("Artículo", "Artículo 1º transitorio.- Transitorio de la segunda ley.")]
    datos = _parsear(tmp_path, _con_anexos([anexo_1, anexo_2]))
    assert all(a.get("articulos_transitorios") for a in datos["cuerpos_anexos"])
    hallazgo, _ = _resolver_articulo(datos, "1 transitorio")
    assert hallazgo is None

    datos = _parsear(tmp_path, _con_anexos([anexo_1]))
    hallazgo, _ = _resolver_articulo(datos, "1 transitorio")
    assert hallazgo and "primera ley" in hallazgo[1] and hallazgo[2]["cuerpo"] == "anexo"


CPR_TRANSITORIAS = [
    ("Artículo", "Artículo 1°.- Las personas nacen libres e iguales en dignidad y derechos."),
    ("Artículo", "Artículo 2°.- El Estado reconoce la familia como núcleo fundamental."),
    ("Disposición Transitoria", "DISPOSICIONES TRANSITORIAS"),
    ("Disposición Transitoria", "PRIMERA.- Se entenderá que las leyes actualmente en vigor siguen rigiendo."),
    ("Disposición Transitoria", "CUARTA.- Se entenderá que las leyes actualmente en vigor siguen rigiendo."),
    ("Disposición Transitoria", "DECIMOPRIMERA.- En el año siguiente a la fecha de publicación."),
]


@pytest.mark.parametrize("pedido", [
    "cuarta transitoria", "cuarta disposición transitoria", "Disposición transitoria cuarta",
    "4 transitoria", "4ª transitoria", "Art. 4 transitorio", "transitoria 4",
])
def test_un_transitorio_ordinal_se_pide_con_numero_o_con_palabra(tmp_path, pedido):
    datos = _parsear(tmp_path, CPR_TRANSITORIAS)
    hallazgo, _ = _resolver_articulo(datos, pedido)
    assert hallazgo and hallazgo[1].startswith("CUARTA.-") and hallazgo[2]["transitorio"] is True, pedido


def test_el_numero_equivale_al_ordinal_tambien_con_undecima(tmp_path):
    datos = _parsear(tmp_path, CPR_TRANSITORIAS)
    for pedido in ("11 transitoria", "undécima transitoria", "decimoprimera transitoria"):
        hallazgo, _ = _resolver_articulo(datos, pedido)
        assert hallazgo and hallazgo[1].startswith("DECIMOPRIMERA.-"), pedido
    hallazgo, _ = _resolver_articulo(datos, "7 transitoria")
    assert hallazgo is None, "no hay séptima: no se entrega la más cercana"


def test_el_ordinal_a_secas_no_trae_la_transitoria_pero_la_sugiere(tmp_path):
    """«cuarta» sin la palabra transitoria no es un artículo del articulado permanente."""
    datos = _parsear(tmp_path, CPR_TRANSITORIAS)
    hallazgo, sugerencias = _resolver_articulo(datos, "cuarta")
    assert hallazgo is None
    assert sugerencias and "transitorio" in sugerencias[0] and "cuarta" in sugerencias[0]


def test_el_numero_y_el_ordinal_no_se_adivinan_si_hay_dos_candidatos(tmp_path):
    datos = _parsear(tmp_path, [
        ("Artículo", "Artículo 1.- Regla."),
        ("Artículo Transitorio", "ARTICULOS TRANSITORIOS"),
        ("Artículo", "Artículo segundo.- Transitorio ordinal."),
        ("Artículo", "Artículo undécimo.- Transitorio undécimo."),
    ])
    hallazgo, _ = _resolver_articulo(datos, "2 transitorio")
    assert hallazgo and hallazgo[1].startswith("Artículo segundo.-")
    hallazgo, _ = _resolver_articulo(datos, "11 transitorio")
    assert hallazgo and hallazgo[1].startswith("Artículo undécimo.-")
    # «undécimo» y «décimo primero» valen 11: con los dos presentes, «11» no puede elegir.
    datos["articulos_transitorios"]["décimo primero"] = "Artículo décimo primero.- Otro con el mismo valor."
    hallazgo, _ = _resolver_articulo(datos, "11 transitorio")
    assert hallazgo is None
    hallazgo, _ = _resolver_articulo(datos, "undécimo transitorio")
    assert hallazgo and hallazgo[1].startswith("Artículo undécimo.-"), "la clave exacta manda"


# ── Rendimiento de la comparación de claves ────────────────────────────────────

def test_las_claves_se_normalizan_una_sola_vez(tmp_path):
    partes = [("Artículo", f"Artículo {n}.- Regla {n}.") for n in range(1, 400)]
    partes.insert(25, ("Artículo", "Artículo 25 quáter.- Regla quáter."))
    datos = _parsear(tmp_path, partes)
    bcn_connector._clave_articulo_texto.cache_clear()
    hallazgo, _ = _resolver_articulo(datos, "25 quater")      # camino lento: recorre las claves
    assert hallazgo and hallazgo[0] == "25 quáter"
    _resolver_articulo(datos, "9999")                         # inexistente: las recorre todas
    antes = bcn_connector._clave_articulo_texto.cache_info()
    t0 = time.perf_counter()
    for _ in range(50):
        _resolver_articulo(datos, "25 quater")
        _resolver_articulo(datos, "9999")
    segundo_recorrido = bcn_connector._clave_articulo_texto.cache_info()
    assert segundo_recorrido.misses == antes.misses, "la segunda consulta no vuelve a normalizar las claves"
    assert time.perf_counter() - t0 < 2.0


def test_un_pedido_gigante_no_se_queda_en_la_cache():
    pedido = "Artículo " + "x" * 100000
    assert len(bcn_connector._clave_articulo(pedido)) <= 200


# ── Migración concurrente: una sola re-derivación ──────────────────────────────

def test_la_migracion_concurrente_deriva_una_sola_vez(tmp_path, monkeypatch):
    """El candado evita que 6 hilos re-deriven (y reescriban) la misma copia al mismo tiempo."""
    from test_bcn_parser import _escribir_copia_v2

    cliente = _cliente(tmp_path)
    _escribir_copia_v2(tmp_path, "norma_p2_172986.json", DFL_CON_ANEXA, dias=2)
    monkeypatch.setattr(cliente, "_fetch_xml", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("red")))
    llamadas = []
    original = bcn_connector.reparsear_estructuras

    def _lenta(datos):
        llamadas.append(1)
        time.sleep(0.15)
        return original(datos)

    monkeypatch.setattr(bcn_connector, "reparsear_estructuras", _lenta)
    with ThreadPoolExecutor(max_workers=6) as pool:
        textos = list(pool.map(lambda _: cliente.get_codigo("civil", "1")["texto"], range(6)))
    assert all(t.startswith("Artículo 1º. La ley es una declaración") for t in textos)
    assert len(llamadas) == 1, f"se re-derivó {len(llamadas)} veces"


# ── Caché real: cada clave del mapa devuelve su propio texto ──────────────────

_CODIGOS = ("norma_p2_172986.json", "norma_p2_176595.json", "norma_p2_1974.json", "norma_p2_1984.json",
            "norma_p2_207436.json", "norma_p2_22740.json", "norma_p2_242302.json")


def _normas_reales():
    carpeta = _carpeta_cache_real()
    salida = []
    for nombre in _CODIGOS:
        for version in (nombre, nombre.replace("_p2_", "_p3_")):
            ruta = os.path.join(carpeta, version) if carpeta else ""
            if ruta and os.path.exists(ruta):
                with open(ruta, encoding="utf-8") as f:
                    datos = json.load(f)
                if datos.get("estructuras"):
                    salida.append((nombre, bcn_connector.reparsear_estructuras(datos)))
                    break
    return salida


def test_casos_reales_cada_clave_devuelve_su_propio_texto():
    """Propiedad: pedir una clave del mapa principal entrega el texto de ESA clave.

    Falla si dos claves distintas se normalizan igual («183-a» y «183 a») y una tapa a la otra.
    """
    normas = _normas_reales()
    if not normas:
        pytest.skip("no hay caché real de BCN (bcn_cache/ u OPENLEGAL_BCN_CACHE_REAL)")
    for nombre, datos in normas:
        for clave, texto in datos["articulos"].items():
            hallazgo, _ = _resolver_articulo(datos, clave)
            assert hallazgo and hallazgo[1] == texto, (nombre, clave)
            assert hallazgo[0] == clave, (nombre, clave, hallazgo[0])


def test_casos_reales_ninguna_clave_es_una_palabra_cortada():
    """Ninguna clave real termina en un sufijo de dos letras que sea una palabra («10-de», «248-si»)."""
    normas = _normas_reales()
    if not normas:
        pytest.skip("no hay caché real de BCN (bcn_cache/ u OPENLEGAL_BCN_CACHE_REAL)")
    sospechosas = []
    for nombre, datos in normas:
        for clave in datos["articulos"]:
            if clave[-3:-2] == "-" and clave[-2:] in {"de", "el", "la", "lo", "en", "si", "al", "se", "no", "un", "es"}:
                sospechosas.append((nombre, clave))
    assert not sospechosas, sospechosas


def test_casos_reales_codigo_penal_313_c():
    normas = dict(_normas_reales())
    datos = normas.get("norma_p2_1984.json")
    if datos is None:
        pytest.skip("no hay caché real del Código Penal")
    assert datos["diagnostico_articulos"]["colisiones"] == []
    hallazgo, _ = _resolver_articulo(datos, "313 c")
    assert hallazgo and "Las penas señaladas" in hallazgo[1]
    hallazgo, _ = _resolver_articulo(datos, "313")
    assert hallazgo and hallazgo[1].startswith("ART. 313.")


# ── Versión histórica (texto corrido): el sufijo cuenta ───────────────────────

TEXTO_CORRIDO = (
    "Previo. Artículo 161.- Sin perjuicio de lo señalado, el empleador podrá poner término. "
    "Artículo 161 bis.- La invalidez, total o parcial, no es justa causa. "
    "Artículo 183-A.- Es trabajo en régimen de subcontratación. "
    "Artículo 183-AE.- Las trabajadoras contratadas bajo el régimen. "
    "Artículo 184.- El empleador estará obligado. "
    "Art. 185. Se aplicará lo dispuesto en el artículo 161 y en el Art. 12 A los efectos de esta ley. "
    "Art. 186 N° 1 D.O. 02.09.2020 siga. Art. 187. Último."
)


def test_la_version_historica_distingue_el_sufijo_del_articulo():
    extraer = bcn_connector.BCNClient._extraer_articulo
    assert extraer(TEXTO_CORRIDO, "161").startswith("Artículo 161.-")
    assert "invalidez" not in extraer(TEXTO_CORRIDO, "161"), "el 161 no arrastra el 161 bis"
    assert extraer(TEXTO_CORRIDO, "161 bis").startswith("Artículo 161 bis.-")
    assert extraer(TEXTO_CORRIDO, "Art. 161-bis").startswith("Artículo 161 bis.-")
    assert extraer(TEXTO_CORRIDO, "183-A").startswith("Artículo 183-A.-")
    assert "subcontratación" in extraer(TEXTO_CORRIDO, "183-A") and "183-AE" not in extraer(TEXTO_CORRIDO, "183-A")
    assert extraer(TEXTO_CORRIDO, "183 AE").startswith("Artículo 183-AE.-")


def test_la_version_historica_no_entrega_otro_articulo_si_el_sufijo_no_existe():
    extraer = bcn_connector.BCNClient._extraer_articulo
    assert extraer(TEXTO_CORRIDO, "161 ter") is None
    assert extraer(TEXTO_CORRIDO, "184-A") is None
    assert extraer(TEXTO_CORRIDO, "12") is None, "«Art. 12 A los efectos» es una frase, no una cabecera"
    assert extraer(TEXTO_CORRIDO, "186") is None, "una nota de modificación no es una cabecera"
    assert extraer(TEXTO_CORRIDO, "sin número") is None
    assert extraer(TEXTO_CORRIDO, "185").startswith("Art. 185.")
