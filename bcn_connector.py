"""
Open Legal Chile — Conector Oficial Biblioteca del Congreso Nacional (BCN Ley Chile)
Módulo para consultar, descargar, cachear e indexar leyes, decretos y códigos de la República de Chile.
"""

import contextlib
import os
import re
import json
import html
import tempfile
import threading
import time
import urllib.parse
import defusedxml.ElementTree as ET
from typing import Dict, Any, List, Optional

from config import BCN_API_KEY, pedir_http, registrar_tiempo

BCN_API_BASE = "https://www.bcn.cl/leychile/api/v1"
BCN_XML_BASE = "https://www.leychile.cl/Consulta/obtxml"
# Servicio vivo de LeyChile (el que usa su propio navegador) para versiones históricas.
BCN_SERVICIOS_BASE = "https://servicios-leychile.bcn.cl"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "bcn_cache")
# Las normas consolidadas cambian solo cuando una reforma las modifica: la copia local se
# revalida a los 30 días (vencida, se intenta refrescar; sin red, se entrega marcada).
_TTL_CACHE_SEGUNDOS = 30 * 24 * 60 * 60
# v2: el parser de artículos cambió (sufijos latinos con tilde: «25 quáter» ya no se guarda
# bajo la clave «25»); las copias viejas de parseo no se reutilizan.
# v3: el parser dejó de pisar artículos homónimos (medido sobre la caché real: 8 normas con
# claves pisadas; el Código Civil devolvía la Ley 16.271 en sus arts. 1 a 79). Las copias v2
# no se botan: se re-derivan sin red desde las `estructuras` que guardan (`_migrar_copia_anterior`).
_VERSION_PARSER = 3
# El lote de `cita_texto` pide el mismo código desde 6 hilos a la vez: sin esto, todos migrarían la
# misma copia al mismo tiempo.
_LOCK_MIGRACION = threading.Lock()

CODIGOS_REPUBLICA = {
    "civil": {"idNorma": 172986, "nombre": "Código Civil de Chile"},
    "trabajo": {"idNorma": 207436, "nombre": "Código del Trabajo (DFL 1 de 2003)"},
    "cpc": {"idNorma": 22740, "nombre": "Código de Procedimiento Civil"},
    "cpp": {"idNorma": 176595, "nombre": "Código Procesal Penal"},
    "penal": {"idNorma": 1984, "nombre": "Código Penal de Chile"},
    "comercio": {"idNorma": 1974, "nombre": "Código de Comercio"},
    "tributario": {"idNorma": 6368, "nombre": "Código Tributario (DL 830)"},
    "aguas": {"idNorma": 5605, "nombre": "Código de Aguas (DFL 1122)"},
    "mineria": {"idNorma": 29668, "nombre": "Código de Minería (Ley 18.248)"},
    "constitucion": {"idNorma": 242302, "nombre": "Constitución Política de la República"},
    "sanitario": {"idNorma": 5595, "nombre": "Código Sanitario (DFL 725)"}
}

LEYES_FRECUENTES = {
    "karin": 21643,
    "40horas": 21561,
    "datos": 19628,
    "consumidor": 19496,
    "sa": 18046,
    "arriendo": 18101,
    "devolveme": 21461,
    "tramitacion_digital": 20886,
    "delitos_economicos": 21595,
    "empresas_en_un_dia": 20659
}


# ── Artículos: cabeceras, cuerpos y búsqueda ────────────────────────────────────
#
# Por qué existe este bloque (medido el 2026-10-07 sobre bcn_cache/*_p2_*.json): el parser
# anterior recorría TODAS las estructuras, buscaba «Artículo N» con `re.search` sin anclar y el
# último con el mismo número pisaba al anterior. Con eso, 8 de las normas de la caché tenían
# claves pisadas: Código Civil 86, Código de Comercio 258, CPR 35, Código del Trabajo 32,
# Ley 18.700 26, Código Penal 12, CPP 4 y CPC 1. El caso más grave: `cita_texto("Código Civil
# art. 1")` entregaba un artículo de la Ley 16.271 (impuesto a las herencias), porque el DFL que
# refunde el Código trae sus leyes anexas en la misma lista de estructuras.

_CLASES_ORDINALES = (
    r"pr[ií]mer[oa]?|segund[oa]|tercer[oa]?|cuart[oa]|quint[oa]|sext[oa]|s[eé]ptim[oa]|octav[oa]|noven[oa]"
)
_RAICES_DECENAS = r"d[eé]cim|vig[eé]sim|trig[eé]sim|cuadrag[eé]sim|quincuag[eé]sim"
# «decimoctava» comparte la «o» de «décimo» con «octava»: la vocal de la decena es opcional.
_DECENAS_ORDINALES = r"(?:" + _RAICES_DECENAS + r")[oa]"
# «primero» … «décimo tercero» / «decimotercero» / «vigésimo primero»; el compuesto va primero
# para que «décimo tercero» no se lea como «décimo».
_ORDINAL = (
    r"(?:(?:" + _RAICES_DECENAS + r")[oa]?\s*(?:" + _CLASES_ORDINALES + r")"
    r"|und[eé]cim[oa]|duod[eé]cim[oa]|" + _DECENAS_ORDINALES + r"|" + _CLASES_ORDINALES + r")"
)
_SUFIJOS_LATINOS = (
    r"bis|ter|qu[aá]ter|quinquies|quinties|sexies|septies|octies|nonies|decies|undecies|duodecies"
)
# «No sigue una letra» (el \b de re no sirve con tildes ni con � en copias mal decodificadas).
_FIN_PALABRA = r"(?![^\W\d_])"
# Cabecera de un artículo, ANCLADA al inicio del texto de la estructura:
#   · leyenda previa de modificación («L. 9.382», «Ley 21257», «DEROGADO») y comillas de cita;
#   · «ARTÍCULO», «Artículo», «Art.», «Art» (sin punto) y la copia con carácter dañado «Art�culo»;
#   · número con subnúmero («548-2») y ordinal opcional (°, º, «.º», «1o», «.o»);
#   · o bien una palabra: ordinal («primero»), «único», «final» o «transitorio».
# Después del número vienen los sufijos (`_RE_SUFIJOS`), que se leen de a uno.
_RE_CABECERA = re.compile(
    r"^[\s\"“”«»']*"
    r"(?:(?:L\.|Ley)\s*N?[°º]?\s*[\d.]+\s*|(?i:derogado)\s*)?[\s\"“”«»']*"
    r"(?i:art(?:[íi�]culo)?)\.?\s*"
    r"(?:"
    r"(?P<num>\d+)"
    r"(?:\s*[-–]\s*(?P<sub>\d+)(?!\d))?"
    r"(?:\.?\s?[°º]|\.?o" + _FIN_PALABRA + r")?"
    r"|"
    r"(?P<pal>(?i:" + _ORDINAL + r"|[uú]nic[oa]|final|transitori[oa]))" + _FIN_PALABRA +
    r")"
)
_LETRA = r"[A-ZÑ]"
# Un sufijo a la vez, anclado donde quedó el anterior. Para no confundir «Artículo 25 Terminado…»
# con «25 ter» ni «Artículo 12 A los efectos…» con «12 A», cada forma exige su límite:
#   latino   «bis», «ter», «quáter»… con límite de palabra (admite «32. BIS» y «297 bis»);
#   letra    «183-A» / «183-AE» (1 o 2 letras pegadas al guion: 183-A no es 183-AE), «161 - A.»,
#            «12 A.-», «152 quáter O bis» (una mayúscula separada, seguida de puntuación o de otro
#            sufijo latino) y «319 a)» / «313° a.» (una minúscula pegada a su paréntesis o punto).
_RE_SUFIJOS = (
    ("-", re.compile(r"\s*[-–](?P<s>[A-Za-zÑñ]{1,2})" + _FIN_PALABRA)),
    ("-", re.compile(r"\s*[-–]\s+(?P<s>" + _LETRA + r")" + _FIN_PALABRA + r"(?=\s*[.:)])")),
    (" ", re.compile(r"\s*[-–.]?\s*(?i:(?P<s>" + _SUFIJOS_LATINOS + r"))" + _FIN_PALABRA)),
    (" ", re.compile(r"\s+(?P<s>" + _LETRA + r")" + _FIN_PALABRA
                     + r"(?=\s*[.\-–:)]|\s+(?i:" + _SUFIJOS_LATINOS + r")" + _FIN_PALABRA + r")")),
    (" ", re.compile(r"\.?\s+(?P<s>[a-zñ])(?=\))")),
    (" ", re.compile(r"\s+(?P<s>[a-zñ])(?=\.)")),
)
_RE_SIGUE_TRANSITORIO = re.compile(r"\s*(?i:transitori[oa])" + _FIN_PALABRA)
# Disposiciones transitorias de la Constitución: «PRIMERA.-», «VIGESIMA PRIMERA.-», con leyenda
# previa opcional («Ley 21257»).
_RE_CABECERA_TRANSITORIA = re.compile(
    r"^[\s\"“”«»']*(?:(?:L\.|Ley)\s*N?[°º]?\s*[\d.]+\s*)?"
    r"(?P<pal>(?i:" + _ORDINAL + r"))" + _FIN_PALABRA + r"\s*(?i:transitori[oa])?\s*[.\-–:]"
)
# Encabezados de sección («ARTÍCULOS TRANSITORIOS», «TITULO XII Disposiciones Transitorias»). Se exige
# que la frase CIERRE el encabezado: «Del contrato de servicios transitorios» (Código del Trabajo,
# Título VII) no es una sección de transitorios.
_RE_ENCABEZADO_TRANSITORIO = re.compile(
    r"(?i:(?:art[íi]culos?|disposiciones?|normas?)\s+transitori[oa]s?)\W*(?i:derogad[oa])?\W*$"
)
# Artículo del DFL que ordena refundir la ley siguiente: cierra la sección de transitorios de la ley
# anterior (en el Código Civil, «ARTICULO 7º: Fíjase el siguiente texto refundido…»).
_RE_FIJA_TEXTO = re.compile(r"(?i:f[ií]jase\s+el\s+siguiente\s+texto)")
_VALOR_UNIDAD = {
    "primer": 1, "segund": 2, "tercer": 3, "cuart": 4, "quint": 5,
    "sext": 6, "septim": 7, "octav": 8, "noven": 9,
}
_VALOR_DECENA = {"decim": 10, "vigesim": 20, "trigesim": 30, "cuadragesim": 40, "quincuagesim": 50}
# Ordinales escritos: se comparan sin género ni espacio («décimo tercero» ≡ «decimotercera»,
# «cuarto» ≡ «cuarta»), porque el rótulo del BCN y el pedido de quien consulta rara vez coinciden.
_RE_ORDINAL_COMPUESTO = re.compile(
    r"\b(decim|vigesim|trigesim|cuadragesim|quincuagesim)[oa]?\s*"
    r"(primer|segund|tercer|cuart|quint|sext|septim|octav|noven)[oa]?\b"
)
_RE_ORDINAL_SUELTO = re.compile(
    r"\b(primer|segund|tercer|cuart|quint|sext|septim|octav|noven|decim|undecim|duodecim|vigesim|"
    r"trigesim|cuadragesim|quincuagesim|unic)[oa]\b"
)


def _sin_tildes(texto: str) -> str:
    return texto.translate(str.maketrans("áéíóúüÁÉÍÓÚÜ", "aeiouuAEIOUU"))


def _clave_articulo(valor: Any) -> str:
    """Normaliza la clave de un artículo para comparar: «25 Quáter.» ≡ «25 quater» ≡ «25 quáter».

    También iguala «Art. 3º», «artículo 3» y «3» y une los ordinales compuestos («décimo tercero»
    ≡ «decimotercero»): el pedido llega escrito de muchas formas y la clave del mapa de una sola.
    """
    texto = _sin_tildes(str(valor).lower())
    texto = re.sub(r"^\W*art(?:iculos?|s)?(?![^\W\d_])\.?", "", texto)
    texto = re.sub(r"(?<=\d)\s*[°º]", "", texto)
    texto = re.sub(r"(?<=\d)\.?o(?![^\W\d_])", "", texto)
    texto = re.sub(r"[\s.\-–]+", " ", texto).strip()
    texto = _RE_ORDINAL_COMPUESTO.sub(r"\1\2", texto)
    return _RE_ORDINAL_SUELTO.sub(r"\1", texto)


def _valor_ordinal(palabra: str) -> Optional[int]:
    """Valor numérico de un ordinal escrito («tercero» 3, «décimo tercero» 13); None si no tiene.

    Sirve para detectar cuándo la numeración retrocede. «único» y «final» no tienen valor.
    """
    p = re.sub(r"\s+", "", _sin_tildes(palabra.lower()))
    p = re.sub(r"[oa]$", "", p)
    if p == "undecim":
        return 11
    if p == "duodecim":
        return 12
    if p in _VALOR_UNIDAD:
        return _VALOR_UNIDAD[p]
    for decena, valor in _VALOR_DECENA.items():
        if p == decena:
            return valor
        if p.startswith(decena):
            resto = p[len(decena):]
            for candidato in (resto, re.sub(r"^[oa]", "", resto)):    # «decimoctava» comparte la «o»
                if candidato in _VALOR_UNIDAD:
                    return valor + _VALOR_UNIDAD[candidato]
    return None


def _cabecera(texto: str, base: int = 0) -> Optional[Dict[str, Any]]:
    """Lee la cabecera de un artículo desde el INICIO de su texto, o None si no la tiene.

    Devuelve `clase` («num» u «ord»), `clave` (la que va al mapa: «183-a», «25 quáter», «16 b»,
    «primero»), `valor` (entero para detectar retrocesos), `transitorio` (la cabecera lo declara:
    «Artículo 1º transitorio») y `fin` (dónde termina la cabecera en el texto original).
    """
    m = _RE_CABECERA.match(texto)
    if not m:
        return None
    resto = texto[m.end():]
    transitorio = bool(_RE_SIGUE_TRANSITORIO.match(resto))
    if m.group("num") is not None:
        clave = m.group("num")
        if m.group("sub"):
            clave += "-" + m.group("sub")
        pos = m.end()
        for _ in range(3):
            for union, patron in _RE_SUFIJOS:
                s = patron.match(texto, pos)
                if s:
                    clave += union + s.group("s").lower()
                    pos = s.end()
                    break
            else:
                break
        transitorio = bool(_RE_SIGUE_TRANSITORIO.match(texto, pos))
        return {"clase": "num", "clave": clave, "valor": int(m.group("num")),
                "transitorio": transitorio, "fin": base + pos}
    palabra = re.sub(r"\s+", " ", m.group("pal").lower())
    if palabra == "final":
        # «Artículo Final» a secas, seguido del artículo real («Artículo Final\n\n Artículo 114.-»)
        # en la Ley 19.039: manda el artículo real, no el rótulo.
        interno = _cabecera(resto.lstrip(), base + m.end() + (len(resto) - len(resto.lstrip())))
        if interno is not None:
            return interno
    return {"clase": "ord", "clave": palabra, "valor": _valor_ordinal(palabra),
            "transitorio": transitorio or palabra.startswith("transitori"), "fin": base + m.end()}


def _cabecera_transitoria(texto: str) -> Optional[Dict[str, Any]]:
    """Cabecera de una disposición transitoria suelta («PRIMERA.-», «VIGESIMA PRIMERA.-»)."""
    m = _RE_CABECERA_TRANSITORIA.match(texto)
    if not m:
        return None
    palabra = re.sub(r"\s+", " ", m.group("pal").lower())
    return {"clase": "ord", "clave": palabra, "valor": _valor_ordinal(palabra),
            "transitorio": True, "fin": m.end()}


def _es_encabezado_transitorio(texto: str) -> bool:
    plano = " ".join((texto or "").split())
    return 0 < len(plano) <= 90 and bool(_RE_ENCABEZADO_TRANSITORIO.search(plano))


class _Cuerpo:
    """Un cuerpo normativo dentro de la lista de estructuras (un código o una ley anexa)."""

    def __init__(self) -> None:
        self.articulos: Dict[str, str] = {}
        self.transitorios: Dict[str, str] = {}
        self.prev_num: Optional[int] = None
        self.prev_ord: Optional[int] = None
        self.n_num = 0
        self.n_ord = 0

    def vacio(self) -> bool:
        return not self.articulos and not self.transitorios


def _segmentar_articulos(estructuras: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Arma el mapa de artículos sin que un artículo homónimo pise a otro.

    Reglas (cada una nace de un caso medido en la caché real):
    1. Solo las estructuras `Artículo` entran al mapa principal; las demás (títulos, párrafos,
       enumeraciones) no. Antes, un encabezado «Párrafo 1º … artículo 58 de la Constitución» del
       CPP se guardaba como el artículo 58.
    2. La cabecera se lee anclada al inicio. Antes, la disposición transitoria vigésima primera
       de la CPR (que menciona «artículo 19») pisaba al artículo 19.
    3. Los transitorios (secciones «ARTÍCULOS TRANSITORIOS», «DISPOSICIONES TRANSITORIAS», artículos
       que se declaran «transitorio») van aparte, en `articulos_transitorios`.
    4. Cuando la numeración retrocede o cambia de serie (numerados ↔ ordinales) empieza un cuerpo
       nuevo: el DFL 1/2000 trae su artículo 1-2, el Código Civil 1-2524 y luego cinco leyes anexas.
       El mapa principal es el cuerpo con más artículos; los otros quedan en `cuerpos_anexos`.
    5. Una clave repetida dentro de un mismo cuerpo conserva la primera y queda en el diagnóstico:
       perder un texto sin avisar es peor que dejar constancia de la duda.
    """
    cuerpos: List[_Cuerpo] = [_Cuerpo()]
    actual = cuerpos[0]
    modo_transitorio = False
    clase_transitoria: Optional[str] = None
    sin_cabecera = 0
    colisiones: List[str] = []

    def cuerpo_nuevo() -> _Cuerpo:
        nonlocal actual, modo_transitorio, clase_transitoria
        if not actual.vacio():
            actual = _Cuerpo()
            cuerpos.append(actual)
        modo_transitorio = False
        clase_transitoria = None
        return actual

    def guardar(destino: Dict[str, str], clave: str, texto: str, posicion: int, donde: str) -> None:
        if clave in destino:
            colisiones.append(f"{donde}:{clave}@{posicion}")
        else:
            destino[clave] = texto

    for posicion, est in enumerate(estructuras):
        tipo = _sin_tildes(str(est.get("tipoParte", "")).lower()).strip()
        texto = str(est.get("texto") or "")
        if tipo == "doble articulado":
            # Marca el comienzo del articulado de una ley dentro de otra (leyes anexas del DFL,
            # ley «aprobatoria» con el texto aprobado adentro).
            cuerpo_nuevo()
            continue
        if tipo != "articulo":
            tipo_transitorio = tipo in ("articulo transitorio", "disposicion transitoria")
            if tipo_transitorio or _es_encabezado_transitorio(texto):
                modo_transitorio = True
                clase_transitoria = None
            if tipo_transitorio and texto and not _es_encabezado_transitorio(texto):
                cab = _cabecera(texto) or _cabecera_transitoria(texto)
                if cab is not None:
                    guardar(actual.transitorios, cab["clave"], texto, posicion, "transitorio")
                elif len(texto) > 160 and not _es_encabezado_transitorio(texto):
                    sin_cabecera += 1
            continue

        cab = _cabecera(texto)
        if cab is None:
            # Encabezados sueltos o párrafos de la norma de aprobación («Que aprueba el Código…»).
            sin_cabecera += 1
            continue

        if modo_transitorio and not cab["transitorio"]:
            # La sección de transitorios termina cuando vuelve la ley exterior (artículos ordinales
            # tras transitorios numerados: Ley 20.285) o el DFL ordena refundir la ley siguiente.
            if _RE_FIJA_TEXTO.search(texto[:240]) or (
                clase_transitoria == "num" and cab["clase"] == "ord" and cab["valor"] is not None
            ):
                cuerpo_nuevo()
        if modo_transitorio or cab["transitorio"]:
            if modo_transitorio and clase_transitoria is None and cab["valor"] is not None:
                clase_transitoria = cab["clase"]
            guardar(actual.transitorios, cab["clave"], texto, posicion, "transitorio")
            continue

        valor = cab["valor"]
        dividir = False
        if cab["clase"] == "num":
            if actual.prev_num is not None and valor < actual.prev_num:
                dividir = True
            elif actual.prev_num is None and actual.n_ord > 0:
                dividir = True      # tras ordinales («primero»…) empiezan los artículos numerados
        elif valor is not None:
            if actual.prev_ord is not None and valor < actual.prev_ord:
                dividir = True
            elif actual.prev_ord is None and actual.n_num > 0:
                dividir = True      # tras artículos numerados vuelve la ley exterior («Segundo»…)
        if dividir:
            cuerpo_nuevo()
        guardar(actual.articulos, cab["clave"], texto, posicion, "articulo")
        if cab["clase"] == "num":
            actual.prev_num = valor
            actual.n_num += 1
        elif valor is not None:
            actual.prev_ord = valor
            actual.n_ord += 1

    utiles = [(i, c) for i, c in enumerate(cuerpos) if not c.vacio()]
    if not utiles:
        return {
            "articulos": {}, "articulos_transitorios": {}, "cuerpos_anexos": [],
            "cuerpo_principal": {"indice": 0, "desde": "", "hasta": "", "total": 0},
            "diagnostico_articulos": {"cuerpos": 0, "sin_cabecera": sin_cabecera,
                                      "colisiones": colisiones[:20]},
        }
    # El cuerpo dominante; a igualdad, el que aparece primero.
    principal_idx, principal = max(utiles, key=lambda par: (len(par[1].articulos), -par[0]))

    def resumen(indice: int, cuerpo: _Cuerpo) -> Dict[str, Any]:
        claves = list(cuerpo.articulos) or list(cuerpo.transitorios)
        return {"indice": indice, "desde": claves[0] if claves else "",
                "hasta": claves[-1] if claves else "", "total": len(cuerpo.articulos)}

    anexos = []
    for indice, cuerpo in utiles:
        if indice == principal_idx:
            continue
        item = resumen(indice, cuerpo)
        item["articulos"] = cuerpo.articulos
        if cuerpo.transitorios:
            item["articulos_transitorios"] = cuerpo.transitorios
        anexos.append(item)
    # «Dominante»: el cuerpo principal triplica al que le sigue (el Código Civil frente a sus leyes
    # anexas). Si no, la norma tiene varios cuerpos de peso parecido (Ley 20.416: artículos
    # ordinales y tres textos aprobados dentro de ellos) y la respuesta debe decirlo.
    segundo = max((len(c.articulos) for i, c in utiles if i != principal_idx), default=0)
    cuerpo_principal = resumen(principal_idx, principal)
    cuerpo_principal["dominante"] = len(principal.articulos) >= 3 * segundo
    return {
        "articulos": principal.articulos,
        "articulos_transitorios": principal.transitorios,
        "cuerpos_anexos": anexos,
        "cuerpo_principal": cuerpo_principal,
        "diagnostico_articulos": {"cuerpos": len(utiles), "sin_cabecera": sin_cabecera,
                                  "colisiones": colisiones[:20]},
    }


def _normalizar_pedido(pedido: Any) -> Any:
    """(clave normalizada, ¿pide un transitorio?) a partir de lo que escribió quien consulta."""
    clave = _clave_articulo(pedido)
    transitorio = bool(re.search(r"\btransitori[oa]s?\b", clave))
    if transitorio:
        clave = re.sub(r"\btransitori[oa]s?\b", " ", clave).strip() or "transitorio"
    return clave, transitorio


def _buscar_exacto(mapa: Dict[str, Any], objetivo: str):
    if objetivo in mapa:        # camino corto: la clave ya viene canónica (la mayoría de los pedidos)
        return objetivo, mapa[objetivo]
    for clave, texto in mapa.items():
        if _clave_articulo(clave) == objetivo:
            return clave, texto
    return None


def _resolver_articulo(datos: Dict[str, Any], pedido: Any):
    """Busca el artículo pedido en una norma ya parseada: (hallazgo, sugerencias).

    El hallazgo es `(clave, texto, extra)` o None. Solo coincide la clave canónica EXACTA: antes
    había respaldos difusos (prefijo y mención) que, ante un artículo inexistente, devolvían el
    texto de otro («183» entregaba el 183-A; «Art. 99» el primer artículo que mencionara el 99).
    En una cita legal, «no encontrado» es una respuesta correcta y un artículo ajeno no lo es.
    Los transitorios se piden diciéndolo («1 transitorio», «cuarta transitoria»).
    """
    objetivo, transitorio = _normalizar_pedido(pedido)
    principal = datos.get("articulos") or {}
    transitorios = datos.get("articulos_transitorios") or {}
    anexos = datos.get("cuerpos_anexos") or []

    if transitorio:
        hallado = _buscar_exacto(transitorios, objetivo)
        if hallado:
            return (hallado[0], hallado[1], {"transitorio": True}), []
        # En el Código de Comercio los transitorios quedan tras el Libro IV, que trae numeración
        # propia: viven en un cuerpo anexo. Si el rótulo está en uno solo, no hay ambigüedad.
        candidatos = []
        for anexo in anexos:
            h = _buscar_exacto(anexo.get("articulos_transitorios") or {}, objetivo)
            if h:
                candidatos.append((anexo, h))
        if len(candidatos) == 1:
            anexo, h = candidatos[0]
            return (h[0], h[1], {"transitorio": True, "cuerpo": "anexo",
                                 "cuerpo_indice": anexo.get("indice")}), []
    else:
        hallado = _buscar_exacto(principal, objetivo)
        if hallado:
            extra: Dict[str, Any] = {}
            cuerpo = datos.get("cuerpo_principal") or {}
            if anexos and cuerpo.get("dominante") is False:
                extra["aviso_cuerpos"] = (
                    f"La norma contiene {len(anexos) + 1} cuerpos con numeración propia y ninguno domina "
                    f"claramente; se entregó el de mayor tamaño (arts. {cuerpo.get('desde')} a "
                    f"{cuerpo.get('hasta')}, {cuerpo.get('total')} artículos). Confirme en el texto oficial "
                    "a cuál se refiere la cita."
                )
            return (hallado[0], hallado[1], extra), []
        # Una ley «aprobatoria» (Ley 20.393) trae «Artículo Segundo», «Tercero»… fuera del texto
        # aprobado. Si el rótulo es ordinal y está en un solo cuerpo anexo, no hay ambigüedad.
        if _valor_ordinal(objetivo) is not None or objetivo in ("unic", "final"):
            candidatos = []
            for anexo in anexos:
                h = _buscar_exacto(anexo.get("articulos") or {}, objetivo)
                if h:
                    candidatos.append((anexo, h))
            if len(candidatos) == 1:
                anexo, h = candidatos[0]
                return (h[0], h[1], {"cuerpo": "anexo", "cuerpo_indice": anexo.get("indice")}), []

    sugerencias: List[str] = []
    if not transitorio:
        variantes = [c for c in principal if _clave_articulo(c).startswith(objetivo + " ")]
        if variantes:
            sugerencias.append(
                "No existe ese número sin sufijo; existen: " + ", ".join(variantes[:6]) + "."
            )
        if _buscar_exacto(transitorios, objetivo):
            sugerencias.append(f"Existe un artículo transitorio con ese número: pídalo como «{objetivo} transitorio».")
        en_anexos = sum(1 for a in anexos if _buscar_exacto(a.get("articulos") or {}, objetivo))
        if en_anexos:
            sugerencias.append(
                f"Ese número existe en {en_anexos} cuerpo(s) anexo(s) de la misma norma (leyes que el "
                "decreto refunde junto al código); no se entrega sin indicar de cuál ley se trata."
            )
    return None, sugerencias


def _buscar_articulo(articulos: Dict[str, Any], pedido: str):
    """(clave, texto) del artículo pedido en un mapa, por clave canónica exacta; None si no está.

    Se conserva con esta firma por compatibilidad; las consultas completas pasan por
    `_resolver_articulo`, que además conoce los transitorios y los cuerpos anexos.
    """
    hallazgo, _ = _resolver_articulo({"articulos": articulos}, pedido)
    return (hallazgo[0], hallazgo[1]) if hallazgo else None


def reparsear_estructuras(datos: Dict[str, Any]) -> Dict[str, Any]:
    """Copia de una norma ya guardada con el mapa de artículos re-derivado de sus `estructuras`.

    Es la migración sin red de la v2 a la v3: las `estructuras` guardadas conservan tipo, id y texto
    de cada parte, que es todo lo que el parser necesita. Sin `estructuras` no se puede derivar nada
    y se devuelve la copia tal cual.
    """
    estructuras = datos.get("estructuras")
    if not isinstance(estructuras, list):
        return datos
    return {**datos, **_segmentar_articulos(estructuras), "version_parser": _VERSION_PARSER}


def cargar_articulos_cache(cache_dir: str, id_norma: Any) -> Dict[str, str]:
    """Mapa principal de artículos de una norma en la copia local, sin red ni escritura.

    Lee la copia del parser vigente; si falta y existe la anterior, la re-deriva en memoria. Lo usan
    los consumidores que leen la caché directamente (índice vectorial) y no deben ver artículos
    pisados de una copia vieja.
    """
    for version in (_VERSION_PARSER, _VERSION_PARSER - 1):
        datos = _leer_json_dict(os.path.join(cache_dir, f"norma_p{version}_{id_norma}.json"))
        if datos is None:
            continue
        if version != _VERSION_PARSER:
            if not isinstance(datos.get("estructuras"), list):
                continue
            datos = reparsear_estructuras(datos)
        articulos = datos.get("articulos")
        if isinstance(articulos, dict) and articulos:
            return articulos
    return {}


def _leer_json_dict(ruta: str) -> Optional[Dict[str, Any]]:
    """El JSON de una copia local como diccionario; None si no existe o no se puede leer."""
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            dato = json.load(f)
    except (OSError, ValueError):       # una copia ilegible no es una copia
        return None
    return dato if isinstance(dato, dict) else None


class BCNClient:
    def __init__(self, api_key: str = BCN_API_KEY, cache_dir: str = CACHE_DIR):
        self.api_key = api_key
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key_type: str, key_val: Any) -> str:
        if key_type in ("ley", "norma", "historica"):
            key_type = f"{key_type}_p{_VERSION_PARSER}"
        return os.path.join(self.cache_dir, f"{key_type}_{key_val}.json")

    def _fetch_xml(self, params: Dict[str, Any]) -> str:
        """Obtiene XML desde el servicio web de la BCN (conexión persistente por host)."""
        url = f"{BCN_XML_BASE}?{urllib.parse.urlencode(params)}"
        t0 = time.perf_counter()
        try:
            return pedir_http(url, timeout=30.0).decode("utf-8", errors="ignore")
        finally:
            registrar_tiempo("bcn.red", time.perf_counter() - t0)

    def _parse_norma_xml(self, xml_content: str) -> Dict[str, Any]:
        """Parsea el XML de una norma chilena a estructura de datos limpia."""
        root = ET.fromstring(xml_content)  # nosec B314
        # Limpiar namespaces
        for elem in root.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]

        norma_id = root.attrib.get('normaId', '')
        fecha_version = root.attrib.get('fechaVersion', '')
        derogado = root.attrib.get('derogado', 'no')

        # Buscar título en Metadatos o Identificador o Encabezado
        titulo = ""
        t_elem = root.find('.//Metadatos/TituloNorma')
        if t_elem is None:
            t_elem = root.find('.//TituloNorma')
        if t_elem is None:
            t_elem = root.find('.//Identificador/TituloNorma')
        if t_elem is not None and t_elem.text:
            titulo = t_elem.text.strip()

        # Buscar organismo
        organismo = ""
        o_elem = root.find('.//Identificador/Organismos/Organismo')
        if o_elem is None:
            o_elem = root.find('.//Organismo')
        if o_elem is not None and o_elem.text:
            organismo = o_elem.text.strip()

        # Buscar número oficial
        numero = ""
        n_elem = root.find('.//Identificador/TiposNumeros/TipoNumero/Numero')
        if n_elem is None:
            n_elem = root.find('.//Numero')
        if n_elem is not None and n_elem.text:
            numero = n_elem.text.strip()

        # Extraer articulado y estructuras funcionales
        estructuras = []

        for node in root.findall('.//EstructuraFuncional'):
            tipo = node.attrib.get('tipoParte', '')
            id_parte = node.attrib.get('idParte', '')
            texto_elem = node.find('Texto')
            texto = texto_elem.text.strip() if (texto_elem is not None and texto_elem.text) else ""

            estructuras.append({
                "tipoParte": tipo,
                "idParte": id_parte,
                "texto": texto
            })

        # El mapa de artículos se deriva de las estructuras ya extraídas (no del XML): así la
        # migración de una copia vieja sin red usa exactamente el mismo camino que la descarga.
        articulado = _segmentar_articulos(estructuras)

        historia_ley_url = f"https://www.bcn.cl/historiadelaley/historia-de-la-ley/vista-expandida/{norma_id}" if norma_id else ""

        return {
            "normaId": norma_id,
            "numero": numero,
            "titulo": titulo,
            "organismo": organismo,
            "fechaVersion": fecha_version,
            "derogado": derogado,
            "historiaLeyUrl": historia_ley_url,
            "totalEstructuras": len(estructuras),
            **articulado,
            "version_parser": _VERSION_PARSER,
            "estructuras": estructuras
        }

    def _cache_fresco(self, cache_file: str, ttl: float = _TTL_CACHE_SEGUNDOS) -> bool:
        """¿La copia local existe y está dentro del TTL? (el mtime es la fecha de descarga)."""
        return os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < ttl

    def _migrar_copia_anterior(self, cache_file: str) -> bool:
        """Si falta la copia del parser vigente y existe la anterior, la deriva sin red.

        La v2 guardó las `estructuras` completas (tipo, id y texto de cada parte), y de ellas sale el
        mapa v3: no hace falta volver a bajar el Código Civil (2,5 MB) ni el resto. Conserva la fecha
        de modificación de la copia vieja, que es la fecha de descarga y gobierna el TTL de 30 días.
        Las copias históricas por texto (`get_codigo_historico`) no dependen del parser y pasan tal cual.
        Devuelve True si dejó la copia nueva.
        """
        if os.path.exists(cache_file) or _VERSION_PARSER <= 1:
            return False
        directorio, nombre = os.path.split(cache_file)
        anterior = os.path.join(
            directorio,
            re.sub(rf"^(ley|norma|historica)_p{_VERSION_PARSER}_", rf"\1_p{_VERSION_PARSER - 1}_", nombre),
        )
        if anterior == cache_file or not os.path.exists(anterior):
            return False
        temporal = ""
        try:
            with _LOCK_MIGRACION:
                if os.path.exists(cache_file):      # otro hilo ya la dejó
                    return False
                dato = _leer_json_dict(anterior)
                if dato is None:
                    return False
                if isinstance(dato.get("estructuras"), list):
                    dato = reparsear_estructuras(dato)
                elif "articulos" in dato:
                    return False        # sin estructuras no hay de dónde derivar el mapa: se vuelve a bajar
                descriptor, temporal = tempfile.mkstemp(dir=directorio, prefix=nombre + ".", suffix=".tmp")
                with os.fdopen(descriptor, "w", encoding="utf-8") as f:
                    json.dump(dato, f, ensure_ascii=False, indent=2)
                os.replace(temporal, cache_file)
                temporal = ""
                marca = os.stat(anterior)
                os.utime(cache_file, (marca.st_atime, marca.st_mtime))
                return True
        except Exception:  # noqa: BLE001 - migrar es una cortesía; si falla se baja de nuevo
            return False
        finally:
            if temporal:
                with contextlib.suppress(OSError):
                    os.remove(temporal)

    def _leer_cache(self, cache_file: str) -> Optional[Dict[str, Any]]:
        """La copia local si se puede leer: una copia ilegible no es una copia."""
        self._migrar_copia_anterior(cache_file)
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                dato = json.load(f)
            return dato if isinstance(dato, dict) else None
        except Exception:  # noqa: BLE001
            return None

    def _descargar_norma(self, params: Dict[str, Any], cache_file: str) -> Dict[str, Any]:
        """Descarga una norma, la parsea y deja la copia local al día."""
        xml = self._fetch_xml(params)
        t0 = time.perf_counter()
        norma_data = self._parse_norma_xml(xml)
        registrar_tiempo("bcn.parseo", time.perf_counter() - t0)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(norma_data, f, ensure_ascii=False, indent=2)
        return norma_data

    def get_ley(self, id_ley: int, use_cache: bool = True) -> Dict[str, Any]:
        """Obtiene una ley chilena por su número oficial (ej. 21643).

        La copia local caduca a los 30 días: vencida, se intenta refrescar; si la red falla,
        se entrega la copia vencida marcada con `copia_local_vencida` (degradación honesta).
        """
        cache_file = self._get_cache_path("ley", id_ley)
        t0 = time.perf_counter()
        data = self._leer_cache(cache_file) if use_cache else None
        if data is not None and self._cache_fresco(cache_file):
            registrar_tiempo("bcn.cache", time.perf_counter() - t0)
            return data
        try:
            return self._descargar_norma({"opt": 7, "idLey": id_ley}, cache_file)
        except Exception:
            if data is not None:
                return {**data, "copia_local_vencida": True}
            raise

    def get_norma(self, id_norma: int, use_cache: bool = True) -> Dict[str, Any]:
        """Obtiene una norma chilena por su ID interno de BCN (ej. Códigos de la República)."""
        cache_file = self._get_cache_path("norma", id_norma)
        t0 = time.perf_counter()
        data = self._leer_cache(cache_file) if use_cache else None
        if data is not None and self._cache_fresco(cache_file):
            registrar_tiempo("bcn.cache", time.perf_counter() - t0)
            return data
        try:
            return self._descargar_norma({"opt": 7, "idNorma": id_norma}, cache_file)
        except Exception:
            if data is not None:
                return {**data, "copia_local_vencida": True}
            raise

    def get_codigo(self, codigo_nombre: str, articulo: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene un Código de la República (civil, trabajo, cpc, cpp, penal, comercio, tributario, mineria, aguas, constitucion, sanitario)."""
        c_key = codigo_nombre.lower().strip()
        if c_key not in CODIGOS_REPUBLICA:
            raise ValueError(f"Código '{codigo_nombre}' no reconocido. Opciones: {list(CODIGOS_REPUBLICA.keys())}")

        id_norma = int(str(CODIGOS_REPUBLICA[c_key]["idNorma"]))
        data = self.get_norma(id_norma)

        if articulo:
            encontrado, sugerencias = _resolver_articulo(data, str(articulo))
            if encontrado:
                clave, texto, extra = encontrado
                return {
                    "codigo": CODIGOS_REPUBLICA[c_key]["nombre"],
                    "articulo": clave,
                    "texto": texto,
                    "fechaVersion": data["fechaVersion"],
                    **extra,
                }
            return {
                "codigo": CODIGOS_REPUBLICA[c_key]["nombre"],
                "articulo": articulo,
                "error": " ".join([f"Artículo {articulo} no encontrado en el texto vigente."] + sugerencias),
                **({"sugerencias": sugerencias} if sugerencias else {}),
            }

        return data

    def get_articulo_ley(self, id_ley: int, articulo: str) -> Dict[str, Any]:
        """Obtiene un artículo específico de una ley (ej. Ley 21643, Art. 1)."""
        data = self.get_ley(id_ley)
        encontrado, sugerencias = _resolver_articulo(data, str(articulo))
        if encontrado:
            clave, texto, extra = encontrado
            return {
                "ley": id_ley,
                "titulo": data["titulo"],
                "articulo": clave,
                "texto": texto,
                "fechaVersion": data["fechaVersion"],
                **extra,
            }
        return {
            "ley": id_ley,
            "articulo": articulo,
            "error": " ".join([f"Artículo {articulo} no encontrado en la Ley {id_ley}."] + sugerencias),
            **({"sugerencias": sugerencias} if sugerencias else {}),
        }

    def get_ley_historica(self, id_ley: int, fecha_historica: str, articulo: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """Obtiene una ley chilena en una versión temporal histórica específica (YYYY-MM-DD)."""
        fecha_clean = fecha_historica.strip()
        cache_key = f"ley_{id_ley}_{fecha_clean}"
        cache_file = self._get_cache_path("historica", cache_key)

        data = self._leer_cache(cache_file) if use_cache else None
        if data is None:
            xml_data = self._fetch_xml({"opt": 7, "idLey": id_ley, "idVersion": fecha_clean})
            data = self._parse_norma_xml(xml_data)
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        if articulo:
            encontrado, sugerencias = _resolver_articulo(data, str(articulo))
            if encontrado:
                clave, texto, extra = encontrado
                return {
                    "ley": id_ley,
                    "fechaVersionSolicitada": fecha_clean,
                    "fechaVersionEfectiva": data["fechaVersion"],
                    "articulo": clave,
                    "texto": texto,
                    "historiaLeyUrl": data.get("historiaLeyUrl", ""),
                    **extra,
                }
            return {
                "ley": id_ley,
                "fechaVersionSolicitada": fecha_clean,
                "articulo": articulo,
                "error": " ".join([f"Artículo {articulo} no encontrado en la versión histórica {fecha_clean}."]
                                  + sugerencias),
                **({"sugerencias": sugerencias} if sugerencias else {}),
            }

        return data

    # ── Versiones históricas: servicio vivo de LeyChile ────────────────────
    def _fetch_json_servicios(self, ruta: str, params: Dict[str, Any], intentos: int = 3) -> Any:
        """Obtiene JSON del servicio de LeyChile que usa su propio navegador (reintenta: es intermitente)."""
        url = f"{BCN_SERVICIOS_BASE}/{ruta}?{urllib.parse.urlencode(params)}"
        ultimo_error: Optional[Exception] = None
        for intento in range(intentos):
            try:
                return json.loads(pedir_http(url, timeout=45.0).decode("utf-8", errors="ignore"))
            except Exception as error:  # noqa: BLE001 - red intermitente
                ultimo_error = error
                time.sleep(1.5 * (intento + 1))
        raise ultimo_error if ultimo_error else RuntimeError("sin respuesta de LeyChile")

    def _versiones_de(self, id_norma: int, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Lista de versiones de una norma (caché de un día: el historial cambia poco).

        Si el servicio intermitente de LeyChile no responde, se devuelve la copia vencida si
        existe: una lista de ayer sirve más que un error —y la fecha pedida decide más arriba—
        dejando marcado que se degradó para que el error final lo diga.
        """
        cache_file = self._get_cache_path("versiones", id_norma)
        if use_cache and os.path.exists(cache_file) and time.time() - os.path.getmtime(cache_file) < 86400:
            with open(cache_file, "r", encoding="utf-8") as f:
                self._versiones_degradadas = False
                return json.load(f)
        try:
            listado = self._fetch_json_servicios("Consulta/get_versiones", {"idNorma": id_norma, "formato": "json"})
        except Exception:  # noqa: BLE001 — el servicio de LeyChile falla seguido
            if os.path.exists(cache_file):
                self._versiones_degradadas = True
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            raise
        self._versiones_degradadas = False
        versiones = (listado.get("Versiones", {}) or {}).get("Version", []) or []
        if isinstance(versiones, dict):
            versiones = [versiones]
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(versiones, f, ensure_ascii=False)
        return versiones

    @staticmethod
    def _texto_version(data: Any) -> str:
        """Aplana el JSON de una versión de LeyChile (claves h/t) a texto corrido."""
        partes: List[str] = []

        def recorrer(obj: Any) -> None:
            if isinstance(obj, dict):
                for clave, valor in obj.items():
                    if clave in ("h", "t") and isinstance(valor, str):
                        partes.append(valor)
                    else:
                        recorrer(valor)
            elif isinstance(obj, list):
                for item in obj:
                    recorrer(item)

        recorrer(data)
        texto = html.unescape(re.sub(r"<[^>]+>", " ", " ".join(partes)))
        return re.sub(r"\s+", " ", texto).strip()

    @staticmethod
    def _version_para_fecha(versiones: List[Dict[str, Any]], fecha: str) -> Optional[Dict[str, Any]]:
        """Elige la versión de la norma vigente en la fecha pedida, si LeyChile la registra."""
        for version in versiones:
            desde = str(version.get("@vigenteDesde", "") or "")
            hasta = str(version.get("@vigenteHasta", "") or "")
            if not desde or desde == "2222-02-02":
                continue
            if desde <= fecha and (not hasta or fecha <= hasta):
                return version
        return None

    @staticmethod
    def _extraer_articulo(texto: str, articulo: str) -> Optional[str]:
        """Recorta el artículo pedido del texto corrido.

        Las versiones antiguas encabezan «Art. 162.» y las modernas «Artículo 162.-»;
        las referencias internas van en minúscula («el artículo 22»), así que no se cuelan.
        """
        objetivo = re.sub(r"\D", "", str(articulo))
        if not objetivo:
            return None
        cabeceras = list(re.finditer(r"\bArt(?:ículo)?\.?\s*(\d+)\s*[°º]?\s*[.\-–—]+(?=\s|$)", texto))
        for indice, coincidencia in enumerate(cabeceras):
            if coincidencia.group(1) == objetivo:
                fin = cabeceras[indice + 1].start() if indice + 1 < len(cabeceras) else len(texto)
                return texto[coincidencia.start():fin].strip()[:12000]
        return None

    def get_codigo_historico(self, codigo_nombre: str, fecha_historica: str, articulo: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """Código de la República en la versión vigente a una fecha (historial real de LeyChile)."""
        c_key = codigo_nombre.lower().strip()
        if c_key not in CODIGOS_REPUBLICA:
            raise ValueError(f"Código '{codigo_nombre}' no reconocido. Opciones: {list(CODIGOS_REPUBLICA.keys())}")

        id_norma = int(str(CODIGOS_REPUBLICA[c_key]["idNorma"]))
        nombre = CODIGOS_REPUBLICA[c_key]["nombre"]
        fecha_clean = fecha_historica.strip()
        url_norma = f"https://www.bcn.cl/leychile/navegar?idNorma={id_norma}"
        cache_file = self._get_cache_path("historica", f"v2_{id_norma}_{fecha_clean}")

        try:
            if use_cache:
                self._migrar_copia_anterior(cache_file)
            if use_cache and os.path.exists(cache_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    guardado = json.load(f)
            else:
                versiones = self._versiones_de(id_norma, use_cache=use_cache)
                version = self._version_para_fecha(versiones, fecha_clean)
                if version is None:
                    primeras = sorted(str(v.get("@vigenteDesde", "")) for v in versiones if str(v.get("@vigenteDesde", ""))[:2] != "22" and v.get("@vigenteDesde"))
                    aviso = (" (la lista de versiones pudo no actualizarse: el servicio de LeyChile está intermitente)"
                             if getattr(self, "_versiones_degradadas", False) else "")
                    return {
                        "codigo": nombre, "fechaVersionSolicitada": fecha_clean,
                        "error": (f"LeyChile no registra una versión de este código vigente al {fecha_clean}"
                                  + (f"; su historial parte el {primeras[0]}." if primeras else ".") + aviso),
                        "urlVersiones": url_norma,
                    }
                data = self._fetch_json_servicios("Navegar/get_norma_json",
                                                  {"idNorma": id_norma, "idVersion": fecha_clean, "agrupa_partes": 1})
                guardado = {
                    "texto": self._texto_version(data),
                    "fechaVersionEfectiva": str(version.get("@vigenteDesde", "")),
                    "tipoVersion": str(version.get("@tipoVersion", "")),
                    "versionUrl": str((version.get("UrlVersion", {}) or {}).get("$", "") or url_norma),
                }
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(guardado, f, ensure_ascii=False)
        except Exception as error:  # noqa: BLE001 - el servicio de LeyChile falla seguido
            return {
                "codigo": nombre, "fechaVersionSolicitada": fecha_clean,
                "error": f"LeyChile no entregó la versión de esa fecha ({type(error).__name__}: {str(error)[:120]}).",
                "urlVersiones": url_norma,
            }

        comun = {
            "codigo": nombre,
            "fechaVersionSolicitada": fecha_clean,
            "fechaVersionEfectiva": guardado.get("fechaVersionEfectiva", ""),
            "tipoVersion": guardado.get("tipoVersion", ""),
            "versionOficialUrl": guardado.get("versionUrl", ""),
        }
        texto = guardado.get("texto", "")
        if articulo:
            fragmento = self._extraer_articulo(texto, articulo)
            if fragmento:
                return {**comun, "articulo": articulo, "texto": fragmento}
            return {**comun, "articulo": articulo,
                    "error": f"Artículo {articulo} no encontrado en la versión vigente al {fecha_clean}."}
        return {**comun, "caracteres": len(texto), "texto_inicio": texto[:3000]}

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Búsqueda de normas chilenas por número de ley, palabra clave frecuente o código de la República."""
        q = query.strip()
        q_lower = q.lower()
        results: List[Dict[str, Any]] = []
        seen_nums = set()

        # 1. Números de ley explícitos (ej. "21.643" o "Ley 19.886")
        nums = re.findall(r'\d{3,6}', q.replace(".", ""))
        for n in nums[:3]:
            num = int(n)
            if 100 <= num <= 999999 and num not in seen_nums:
                try:
                    ley = self.get_ley(num)
                    if ley.get("titulo"):
                        results.append({
                            "tipo": "Ley",
                            "numero": str(num),
                            "titulo": ley.get("titulo", ""),
                            "fechaVersion": ley.get("fechaVersion", "")
                        })
                        seen_nums.add(num)
                except Exception:
                    pass

        # 2. Palabras clave de leyes frecuentes del ordenamiento chileno
        for kw, num in LEYES_FRECUENTES.items():
            if kw in q_lower and num not in seen_nums and len(results) < limit:
                try:
                    ley = self.get_ley(num)
                    if ley.get("titulo"):
                        results.append({
                            "tipo": "Ley",
                            "numero": str(num),
                            "titulo": ley.get("titulo", ""),
                            "fechaVersion": ley.get("fechaVersion", "")
                        })
                        seen_nums.add(num)
                except Exception:
                    pass

        # 3. Códigos de la República por nombre
        for cod_key, cod in CODIGOS_REPUBLICA.items():
            if cod_key in q_lower and len(results) < limit:
                results.append({
                    "tipo": "Código",
                    "codigo": cod_key,
                    "titulo": cod["nombre"],
                    "idNorma": cod["idNorma"]
                })

        if not results:
            # Esto NO es búsqueda de texto libre y no puede fingir que lo es: resuelve números de
            # ley, palabras clave de leyes frecuentes y nombres de códigos. Devolver [] a secas se
            # leía como "la BCN no tiene nada sobre esto", que es falso: simplemente no se buscó
            # por texto. El portal de la BCN sólo expone consultas por idNorma/número de ley
            # (obtxml), así que se dice qué no cubre y por dónde seguir.
            results.append({
                "tipo": "aviso",
                "titulo": f"La búsqueda de BCN no cubre «{q}»",
                "mensaje": (
                    "Este conector resuelve por número de ley (p. ej. '21.643'), por nombre de "
                    "código ('civil', 'trabajo', 'cpc') y por palabras clave de leyes frecuentes; "
                    "NO hace búsqueda de texto libre, porque la BCN sólo publica consultas por "
                    "idNorma/número. Para un concepto, consulta el artículo directo "
                    "(bcn_get_codigo con 'civil' y el número, p. ej. 1317) o busca en el corpus "
                    "doctrinal (doctrina_search), que sí recorre texto completo."
                ),
            })

        return results[:limit]


# ==============================================================================
# CLI DE CONSULTA RÁPIDA
# ==============================================================================
if __name__ == "__main__":
    import argparse
    import sys
    try:
        if hasattr(sys.stdout, "reconfigure"):
            getattr(sys.stdout, "reconfigure")(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Conector CLI Open Legal Chile - BCN Ley Chile")
    parser.add_argument("--ley", type=int, help="Número de Ley (ej. 21643)")
    parser.add_argument("--codigo", type=str, help="Nombre del Código (civil, trabajo, cpc, cpp, penal, comercio, tributario, mineria, aguas, constitucion, sanitario)")
    parser.add_argument("--art", type=str, help="Número de Artículo (ej. 1545, 161, 254)")
    args = parser.parse_args()

    client = BCNClient()

    if args.codigo:
        print(f"\n🏛️ Consultando {args.codigo.upper()}...")
        res = client.get_codigo(args.codigo, args.art)
        if args.art:
            print(f"\n[Artículo {args.art} — {res.get('codigo')}]")
            print(res.get('texto', res.get('error')))
            print(f"\n📅 Fecha Versión Vigente: {res.get('fechaVersion')}")
        else:
            print(f"Norma: {res.get('titulo')} | Total Artículos: {len(res.get('articulos', {}))}")
    elif args.ley:
        print(f"\n📜 Consultando Ley N° {args.ley}...")
        if args.art:
            res = client.get_articulo_ley(args.ley, args.art)
            print(f"\n[Ley {args.ley} — Art. {args.art}]")
            print(res.get('texto', res.get('error')))
        else:
            res = client.get_ley(args.ley)
            print(f"Ley N° {args.ley}: {res.get('titulo')}")
            print(f"Total Estructuras: {res.get('totalEstructuras')} | Versión: {res.get('fechaVersion')}")
    else:
        print("Uso: python bcn_connector.py --codigo [civil|trabajo|cpc|cpp|penal|comercio|tributario|mineria|aguas] --art [numero]")
        print("     python bcn_connector.py --ley [numero] [--art [numero]]")
