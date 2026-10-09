"""Formato único de citas (AGENTS.md §2) y detección de normas en texto libre.

Nace de un problema concreto: cada herramienta armaba sus corchetes a mano y el texto de la
norma citada no viajaba con la cita, así que quien respondía citaba de memoria o sin texto.
Acá viven el formato oficial, el bloque de fuentes y el detector que permite ir a buscar el
texto literal de una norma mencionada en lenguaje natural.
"""

import bisect
import re
import unicodedata
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

CODIGOS = {
    "civil": "Código Civil",
    "trabajo": "Código del Trabajo",
    "cpc": "Código de Procedimiento Civil",
    "cpp": "Código Procesal Penal",
    "penal": "Código Penal",
    "comercio": "Código de Comercio",
    "tributario": "Código Tributario",
    "aguas": "Código de Aguas",
    "mineria": "Código de Minería",
    "constitucion": "Constitución Política de la República",
    "sanitario": "Código Sanitario",
}

# Alias de escritura frecuente: «CPR», «Constitución Política», «Código Sanitario» y los nombres
# completos de los códigos procesales. Sin estos dos últimos, «Código de Procedimiento Civil art. 66»
# se resolvía como Código Civil art. 66 y «Código Procesal Penal art. 140» como Código Penal art. 140
# (medido el 2026-10-07: cita_texto devolvía el artículo de otro código con su corchete oficial).
_ALIAS_OBRA = {
    "constitucion": r"(?:constituci[oó]n(?:\s+pol[ií]tica)?|cpr)",
    "sanitario": r"(?:c[oó]digo\s+sanitario|sanitario)",
    "cpc": r"(?:procedimiento\s+civil|cpc)",
    "cpp": r"(?:procesal\s+penal|cpp)",
}


def _alternacion_obras() -> str:
    """Alternación de nombres de obra: los alias por sí solos y después las claves simples."""
    partes = list(_ALIAS_OBRA.values())
    partes += [re.escape(k) for k in CODIGOS if k not in _ALIAS_OBRA]
    return "|".join(sorted(partes, key=len, reverse=True))


def _obra_canonica(capturada: str) -> str:
    """«Constitución Política»/«CPR» → «constitucion»; «Procedimiento Civil» → «cpc»; etc."""
    texto = " ".join(capturada.lower().split())
    for clave, patron in _ALIAS_OBRA.items():
        if re.fullmatch(patron, texto):
            return clave
    return texto


_OBRAS = _alternacion_obras()
# Sufijos latinos completos, con la tilde real de «quáter» (la que envenenó la caché).
_SUFIJOS_LATINOS = r"(?:bis|ter|qu[aá]ter|quinquies|sexies|septies|octies|nonies|decies)"
_ART = r"\d+(?:\s*[-–]\s*[a-zA-Z]|\s*" + _SUFIJOS_LATINOS + r")?"
_NUM_LEY = r"\d{2,6}(?:\.\d{3})?(?!\d)"
_PREFIJO_CODIGO = r"(?:c[oó]digo\s+(?:de\s+l[ao]s?\s+|del\s+|de\s+)?)?"
_ARTICULO = r"(?:art[íi]culos?|arts?\.?)\s*"

# «Código Civil art. 1545» y «Código del Trabajo, artículo 161»
_RE_CODIGO_ADELANTE = re.compile(
    _PREFIJO_CODIGO + r"\b(?P<obra>" + _OBRAS + r")[\s\S]{0,20}" + _ARTICULO + r"(?P<art>" + _ART + r")",
    re.IGNORECASE)
# «el artículo 1545 del Código Civil»
_RE_CODIGO_ATRAS = re.compile(
    _ARTICULO + r"(?P<art>" + _ART + r")[\s\S]{0,20}" + _PREFIJO_CODIGO + r"\b(?P<obra>" + _OBRAS + r")\b",
    re.IGNORECASE)
# «Ley 21.643 art. 2» y «Ley N° 21.643»
_RE_LEY_ADELANTE = re.compile(
    r"ley\s*n?[°º]?\s*(?P<num>" + _NUM_LEY + r")(?:[\s\S]{0,25}" + _ARTICULO + r"(?P<art>" + _ART + r"))?",
    re.IGNORECASE)
# «el artículo 2 de la Ley 21.643»
_RE_LEY_ATRAS = re.compile(
    _ARTICULO + r"(?P<art>" + _ART + r")[\s\S]{0,20}(?:de\s+l[ao]s?\s+)?ley\s*n?[°º]?\s*(?P<num>" + _NUM_LEY + r")",
    re.IGNORECASE)


def formatear_cita(fuente: str, identificador: str, url: str = "", texto: str = "") -> Dict[str, str]:
    """Devuelve la cita en el formato oficial del producto, con su texto literal."""
    formato = f"[{fuente} - {identificador}]"
    return {
        "formato": formato,
        "texto": texto,
        "url": url,
        "fuente": fuente,
        "cita_completa": f"{formato} {url}".strip(),
    }


def bloque_fuentes(citas: List[Dict[str, str]]) -> str:
    """Bloque de fuentes para el final de una respuesta o el pie de un documento."""
    lineas = ["---", "Fuentes:"]
    for i, c in enumerate(citas, 1):
        lineas.append(f"{i}. {c.get('formato', '')} {c.get('url', '')}".rstrip())
    return "\n".join(lineas)


def detectar_normas(texto: str) -> List[Dict[str, Any]]:
    """Detecta menciones de códigos y leyes con artículo, para ir a buscar su texto literal.

    Devuelve, por norma: familia ('codigo' | 'ley'), obra o número, artículo (si se mencionó)
    y la etiqueta lista para el corchete oficial.
    """
    salida: List[Dict[str, Any]] = []
    vistos = set()
    for regex in (_RE_CODIGO_ADELANTE, _RE_CODIGO_ATRAS):
        for m in regex.finditer(texto or ""):
            obra = _obra_canonica(m.group("obra"))
            capturado = m.group("art")
            articulo = " ".join(capturado.split()).lower() if capturado else None
            clave = ("codigo", obra, articulo)
            if clave in vistos:
                continue
            vistos.add(clave)
            salida.append({
                "familia": "codigo", "obra": obra, "articulo": articulo,
                "etiqueta": f"BCN - {CODIGOS[obra]}, Art. {articulo}",
            })
    for regex in (_RE_LEY_ADELANTE, _RE_LEY_ATRAS):
        for m in regex.finditer(texto or ""):
            numero = m.group("num").replace(".", "")
            capturado = m.group("art")
            articulo = " ".join(capturado.split()).lower() if capturado else None
            clave = ("ley", numero, articulo)
            if clave in vistos:
                continue
            vistos.add(clave)
            etiqueta = f"BCN - Ley N° {numero}"
            if articulo:
                etiqueta += f", Art. {articulo}"
            salida.append({"familia": "ley", "numero": numero, "articulo": articulo, "etiqueta": etiqueta})
    # Una misma norma puede aparecer mencionada con y sin artículo («la Ley 21.643» y «el
    # artículo 2 de la Ley 21.643»): se conserva la mención con artículo y se evita el duplicado.
    con_articulo = {(n["familia"], n.get("obra") or n.get("numero")) for n in salida if n.get("articulo")}
    return [n for n in salida
            if n.get("articulo") or (n["familia"], n.get("obra") or n.get("numero")) not in con_articulo]


# ════════════════════════════════════════════════════════════════════════════════════════════
# Gramática canónica de normas y roles (mapa del corpus)
# ════════════════════════════════════════════════════════════════════════════════════════════
#
# `detectar_normas` sirve para ir a buscar el texto de la norma que alguien escribió en una
# consulta; no sirve para indexar 9.000 documentos largos. Medido el 2026-10-08 sobre los
# cuerpos del TC y de las revistas: leía «Código de Procedimiento Civil» como Código Civil,
# «Código Procesal Penal» como Código Penal y «Ley Orgánica Constitucional» como la CPR;
# tomaba «la acción civil. Artículo 59» por CC 59; no reconocía «Ley N° 4.808», «art. 1.545»,
# los artículos bis o transitorios ni los numerales de la CPR. Esta gramática es la única fuente
# de IDs canónicos (`norma:<cuerpo>[:<art>[:n<numeral>]]`, `cs:`, `tc:`, `ta:`) y es
# determinista: sin ventanas de texto libre entre el artículo y su cuerpo legal.

# Nombre legible de cada cuerpo (también lo usa etiqueta_norma, que debe volver a reconocerse).
CUERPOS: Dict[str, str] = {
    "cc": "Código Civil", "cp": "Código Penal", "ct": "Código del Trabajo",
    "cpc": "Código de Procedimiento Civil", "cpp": "Código Procesal Penal",
    "cpp1906": "Código de Procedimiento Penal", "cot": "Código Orgánico de Tribunales",
    "cpr": "Constitución Política de la República", "ctrib": "Código Tributario",
    "ccom": "Código de Comercio", "caguas": "Código de Aguas", "cmin": "Código de Minería",
    "csan": "Código Sanitario", "cjm": "Código de Justicia Militar", "losma": "LOSMA",
}

# «Constitución española», «Constitución de 1925», «Constitución Política de la República de
# Guatemala»: no son la CPR vigente.
_PAISES = (r"guatemala|colombia|ecuador|bolivia|per[uú]|venezuela|paraguay|uruguay|m[eé]xico|cuba|honduras|"
           r"nicaragua|panam[aá]|costa\s+rica|el\s+salvador|argentina|brasil|portugal|espa[ñn]a|italia|francia|"
           r"alemania|b[eé]lgica")
_NO_EXTRANJERA = (r"(?!\s+(?:pol[ií]tica\s+)?(?:de\s+la\s+rep[uú]blica\s+)?(?:de|del)\s+(?:" + _PAISES + r")\b)"
                  r"(?!\s+(?:espa[ñn]ola|francesa|alemana|italiana|argentina|colombiana|peruana|mexicana|"
                  r"brasile[ñn]a|ecuatoriana|boliviana|portuguesa|federal|europea|estadounidense|norteamericana|"
                  r"de\s+(?:los\s+)?(?:estados|ee\.?\s?uu|espa|alemania|italia|francia|1925|1833|1828|1823|1822|1818)"
                  r"|de\s+la\s+(?:naci[oó]n\s+argentina|rep[uú]blica\s+(?:federal|de\s+(?!chile)))))")
# «Código Penal español», «Código Civil francés», «Código Civil y Comercial de la Nación»: derecho
# comparado, no el código chileno (la doctrina los cita a menudo junto a los nuestros).
_NO_EXTRANJERO = (r"(?!\s+(?:espa[ñn]ol|franc[eé]s|alem[aá]n|italiano|belga|argentino|peruano|colombiano|"
                  r"mexicano|uruguayo|ecuatoriano|boliviano|venezolano|paraguayo|brasile[ñn]o|portugu[eé]s|suizo|"
                  r"austr[ií]aco|holand[eé]s|japon[eé]s|napole[oó]nico|modelo|tipo|y\s+comercial|"
                  r"de\s+(?:napole[oó]n|v[eé]lez|quebec|la\s+naci[oó]n|espa[ñn]a|francia|alemania|italia|"
                  r"b[eé]lgica|argentina|per[uú]|colombia|m[eé]xico|uruguay|ecuador|bolivia|brasil|portugal|suiza))"
                  r"(?![^\W\d_]))")
# Nombres de cuerpos: del más largo al más corto, para que «Código de Procedimiento Civil» gane
# a «Código Civil» y «Código Procesal Penal» a «Código Penal». Insensibles a mayúsculas.
_CUERPOS_NOMBRE: List[Tuple[str, str]] = [(p + _NO_EXTRANJERO, c) for p, c in (
    (r"c[oó]digo\s+de\s+procedimiento\s+civil", "cpc"),
    (r"c[oó]digo\s+de\s+procedimiento\s+penal", "cpp1906"),
    (r"c[oó]digo\s+procesal\s+penal", "cpp"),
    (r"c[oó]digo\s+org[aá]nico\s+de\s+tribunales", "cot"),
    (r"c[oó]digo\s+de\s+justicia\s+militar", "cjm"),
    (r"c[oó]digo\s+civil", "cc"),
    (r"c[oó]digo\s+penal", "cp"),
    (r"c[oó]digo\s+del\s+trabajo", "ct"),
    (r"c[oó]digo\s+tributario", "ctrib"),
    (r"c[oó]digo\s+de\s+comercio", "ccom"),
    (r"c[oó]digo\s+de\s+aguas", "caguas"),
    (r"c[oó]digo\s+de\s+miner[ií]a", "cmin"),
    (r"c[oó]digo\s+sanitario", "csan"),
)] + [
    (r"ley\s+org[aá]nica\s+(?:constitucional\s+)?de\s+la\s+superintendencia\s+del\s+medio\s+ambiente", "losma"),
    (r"ley\s+org[aá]nica\s+constitucional\s+del\s+tribunal\s+constitucional", "ley-17997"),
    (r"ley\s+(?:org[aá]nica\s+constitucional\s+)?de\s+bases\s+generales\s+de\s+la\s+administraci[oó]n\s+del\s+estado", "ley-18575"),
    (r"ley\s+(?:sobre\s+|de\s+)?bases\s+generales\s+del\s+medio\s+ambiente", "ley-19300"),
    (r"ley\s+(?:de\s+)?bases\s+de\s+(?:los\s+)?procedimientos?\s+administrativos?", "ley-19880"),
    (r"ley\s+(?:sobre\s+|de\s+)?protecci[oó]n\s+de\s+los\s+derechos\s+de\s+los\s+consumidores", "ley-19496"),
    (r"ley\s+(?:que\s+crea\s+los\s+|de\s+)?tribunales\s+ambientales", "ley-20600"),
    (r"ley\s+org[aá]nica\s+constitucional\s+(?:sobre\s+|de\s+)?concesiones\s+mineras", "ley-18097"),
    (r"constituci[oó]n\s+pol[ií]tica(?:\s+de\s+la\s+rep[uú]blica)?(?:\s+de\s+chile)?" + _NO_EXTRANJERA, "cpr"),
    (r"carta\s+(?:fundamental|pol[ií]tica)" + _NO_EXTRANJERA, "cpr"),
    (r"(?<!comisi[oó]n de )(?<!comisi[oó]n de la )constituci[oó]n" + _NO_EXTRANJERA, "cpr"),
]
# Siglas: sensibles a mayúsculas («cc» en minúscula no es el Código Civil).
_CUERPOS_SIGLA: List[Tuple[str, str]] = [
    (r"C\.\s?P\.\s?C\.?|CPC", "cpc"), (r"C\.\s?P\.\s?P\.?|CPP", "cpp"), (r"C\.\s?O\.\s?T\.?|COT", "cot"),
    (r"C\.\s?P\.\s?R\.?|CPR", "cpr"), (r"C\.\s?del\s?T\.?|CT", "ct"), (r"C\.\s?C\.?|CC", "cc"),
    (r"C\.\s?P\.?|CP", "cp"), (r"LOSMA", "losma"), (r"LBGMA", "ley-19300"), (r"LBPA", "ley-19880"),
    (r"LOCBGAE", "ley-18575"), (r"LOC\s+del\s+TC|LOC\s?TC", "ley-17997"), (r"LPDC", "ley-19496"),
    (r"LTA", "ley-20600"),
]
# Las siglas «sueltas» (sin artículo) son ruido frecuente: solo estas generan el ID del cuerpo.
_SIGLAS_DISTINTIVAS = {"losma", "ley-19300", "ley-19880", "ley-18575", "ley-17997", "ley-19496", "ley-20600"}

_NUM_MILES = r"\d{1,3}(?:\.\d{3})+|\d{1,6}"
# Los `(?=[…])` iniciales no cambian qué calza: dejan que el motor descarte de inmediato las
# posiciones que no pueden empezar una mención (medido: de 3 a 10 veces más rápido en cuerpos de
# 50 MB, con exactamente las mismas coincidencias).
_NUM_MILES_COMA = r"\d{1,3}(?:[.,]\d{3})+|\d{1,6}"
_RE_NUMERADA = re.compile(
    r"(?=[dD](?:[eE][cC]|\.|[fFlL])|[lL][eE][yY])\b(?P<tipo>decreto\s+con\s+fuerza\s+de\s+ley|d\.\s?f\.\s?l\.|dfl|decreto\s+ley|d\.\s?l\.?|dl|ley)"
    r"(?:\s+(?:(?:(?-i:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)|de|del|la|los|las|y|sobre|que)\s+){1,8}(?=N°))?"
    # Tras el número: ni otro dígito ni otro grupo de miles; sí una llamada al pie tras la coma
    # («Ley N° 20.370,4»). «Mensaje N° 1167-362» o un boletín «9885-07» no son leyes.
    r"\s*(?P<nro>N°\s*)?(?P<num>" + _NUM_MILES_COMA + r")(?!\d|[.,]\d{3}(?!\d)|\s?-\s?\d)",
    re.IGNORECASE)
_RE_CUERPO_NOMBRE = re.compile(
    r"(?=[cC][oOóÓaA]|[lL][eE][yY])\b(?:" + "|".join(f"(?P<n{i}>{p})" for i, (p, _) in enumerate(_CUERPOS_NOMBRE)) + r")(?![^\W\d_])",
    re.IGNORECASE)
_RE_CUERPO_SIGLA = re.compile(
    r"(?=[CL])(?<![\w.])(?:" + "|".join(f"(?P<s{i}>{p})" for i, (p, _) in enumerate(_CUERPOS_SIGLA)) + r")(?![\w])")

_SUFIJO = r"bis|ter|qu[aá]ter|quinquies|sexies|septies|octies|nonies|decies"
_ART_TOKEN = re.compile(
    r"(?P<num>\d{1,3}(?:\.\d{3})+|\d{1,5})(?![\d]|[.,]\d)(?:\s*\.?\s*°)?"
    r"(?:\s*[-–]?\s*(?P<suf>(?i:" + _SUFIJO + r"))\b|\s*[-–]\s*(?P<letra>[A-MO-Z])\b|\s(?P<letra2>[A-MO-Z])(?![\w.°])"
    # «331 a, 331 b» (CPP): letras minúsculas en lista son literales del mismo artículo 331.
    r"|\s(?P<literal>[a-z])(?=\s*,))?"
    r"(?:\s+(?P<trans>transitori[oa]s?)\b)?")
_RE_ARTICULO = re.compile(r"(?=[aA][rR][tT])\b(?:art[íi]culos?|arts?\.?|art)\s*(?=\d)", re.IGNORECASE)
_UNIDADES_ORD = (r"primer[oa]?|segund[oa]|tercer[oa]?|cuart[oa]|quint[oa]|sext[oa]|s[eé]ptim[oa]|"
                 r"octav[oa]|noven[oa]")
_ORDINAL_CARDINAL = (r"(?:" + _UNIDADES_ORD + r"|und[eé]cim[oa]|duod[eé]cim[oa]|"
                     r"d[eé]cim[oa](?:\s*(?:" + _UNIDADES_ORD + r"))?|vig[eé]sim[oa](?:\s*(?:" + _UNIDADES_ORD + r"))?)")
_ORDINAL_PALABRA = r"(?:" + _ORDINAL_CARDINAL + r"|final|[uú]ltim[oa]|pen[uú]ltim[oa])"
_ORDINAL_NUM = {"primero": 1, "primer": 1, "primera": 1, "segundo": 2, "segunda": 2, "tercero": 3, "tercer": 3,
                "tercera": 3, "cuarto": 4, "cuarta": 4, "quinto": 5, "quinta": 5, "sexto": 6, "sexta": 6,
                "septimo": 7, "septima": 7, "octavo": 8, "octava": 8, "noveno": 9, "novena": 9,
                "decimo": 10, "decima": 10, "undecimo": 11, "undecima": 11, "duodecimo": 12, "duodecima": 12,
                "vigesimo": 20, "vigesima": 20}
# «numeral 3 del artículo 19» / «del numeral tercero, del artículo 19» / «el N° 7 del art. 434» /
# «los números 1 y 2 del artículo 61»
_NUMERAL_PREVIO_ITEM = r"(?:\d{1,3}|" + _ORDINAL_CARDINAL + r")"
_RE_NUMERAL_PREVIO = re.compile(
    r"(?=[nN](?:°|[uUúÚ][mM][eE][rR]))\b(?:numeral(?:es)?|n[úu]meros|N°s?)\s*"
    r"(?P<k>" + _NUMERAL_PREVIO_ITEM + r"(?:\s*°?\s*(?:,\s*|\s+[ye]\s+)" + _NUMERAL_PREVIO_ITEM + r")*)"
    r"\s*°?\s*,?\s+del\s+art(?:[íi]culo\s+|\.\s*)(?=\d)",
    re.IGNORECASE)
_RE_NUMERAL_PREVIO_ITEM = re.compile(_NUMERAL_PREVIO_ITEM, re.IGNORECASE)
_SEP_ITEM = r"\s*(?:,\s*(?:(?:y|e)\s+)?|(?:y|e)\s+)"
_INCISO_ITEM = r"(?:\d{1,2}\s*°?|" + _ORDINAL_PALABRA + r")"
# En una lista de incisos, «SEGUNDA» seguida de «FRASE» ya no es otro inciso sino la frase del anterior.
_INCISO_ITEM_LISTA = r"(?:\d{1,2}\s*°?|" + _ORDINAL_PALABRA + r"(?!\s+(?:parte|frase|oraci[oó]n)\b))"
_PARENTESIS_CORTO = r"(?:\s*\([^()]{1,40}\))?"
_NUMERAL_ITEM = r"\d{1,3}\s*°?" + _PARENTESIS_CORTO
# En «arts. 17 N° 2, 18 N° 7 y 20», el «18» que trae su propio N° ya es otro artículo.
_NUMERAL_ITEM_LISTA = r"\d{1,3}(?!\d|\s*°?\s*N°)\s*°?" + _PARENTESIS_CORTO
_LETRA_ITEM = r"[a-zñ]\)?(?!\w)"
_RE_MODIFICADOR = re.compile(
    r"\s*,?\s*(?:(?:y|e)\s+)?(?:"
    r"(?P<inciso>inc(?:isos?|s?\.)\s*" + _INCISO_ITEM + r"(?:" + _SEP_ITEM + _INCISO_ITEM_LISTA + r")*)"
    r"|(?P<numeral>(?:del\s+)?(?:N°s?|numeral(?:es)?)\s*" + _NUMERAL_ITEM +
    r"(?:" + _SEP_ITEM + r"(?:N°\s*)?" + _NUMERAL_ITEM_LISTA + r")*)"
    r"|(?P<numeral_palabra>(?:del\s+)?numeral\s+" + _ORDINAL_CARDINAL + r")"
    r"|(?P<letra>(?:letras?|literal(?:es)?)\s+" + _LETRA_ITEM + r"(?:\s*(?:,|y|e)\s*" + _LETRA_ITEM + r")*"
    r"|[a-zñ]\)(?!\w))"
    r"|(?P<parte>(?:parte|frase|oraci[oó]n)\s+(?:final|primera|segunda|tercera)|"
    r"(?:primera|segunda|tercera)\s+(?:parte|frase|oraci[oó]n))"
    r"|(?P<sigs>y\s+sig(?:uientes|s?\.)|y\s+dem[aá]s\s+pertinentes)"
    r"|(?P<salvo>salvo\s+(?:lo\s+relativo\s+(?:a|en)\s+)?(?:sus?|el|la|los|las)\b)"
    # «incisos primero, N° 6°, y decimoprimero»: el ordinal suelto continúa la lista de incisos.
    r"|(?P<ordinal>" + _ORDINAL_CARDINAL + r")(?!\s+(?:parte|frase|oraci[oó]n|transitori)|\w)"
    r")", re.IGNORECASE)
# Tras «artículos» (plural), un N° singular rige solo al artículo que lo trae: en «los artículos
# 17 N° 4 y 32 de la Ley N° 20.600» el 32 es otro artículo, no el numeral 32 del artículo 17.
_RE_NUMERAL_UNO = re.compile(
    r"\s*,?\s*(?:(?:y|e)\s+)?(?:del\s+)?(?:N°|numeral)\s*" + _NUMERAL_ITEM + r"(?![^\W_])", re.IGNORECASE)
_RE_SEPARADOR_LISTA = re.compile(
    r"\s*(?:,|;)?\s*(?:y|e|o|u|ni|a|al|hasta|en\s+relaci[oó]n\s+(?:con|al))?\s*(?:el|los|con\s+el)?\s*"
    r"(?:art[íi]culos?\s*|arts?\.\s*)?(?=\d)", re.IGNORECASE)
_RE_CONECTOR = re.compile(
    r"\s*,?\s*(?:(?:sustitutiv[oa]|permanente)\s+)?"
    # Fórmula de los fallos del TC: «… y en las demás disposiciones citadas y pertinentes de la Constitución»
    r"(?:,?\s*y\s+(?:en\s+)?(?:las\s+)?dem[aá]s\s+(?:disposiciones|normas|preceptos)\s+(?:citad[oa]s\s+y\s+)?"
    r"pertinentes\s+)?"
    # «de 1a Ley N° 20.600»: el OCR de los fallos ambientales lee «la» como «1a».
    r"\(?\s*(?:(?:del|de\s+la|de\s+1a|de\s+los|de\s+las|de|a\s+la|al)\s+"
    r"(?:(?:citad[oa]|actual|vigente|antiguo|nuevo|referid[oa]|mismo|nuestr[oa]|"
    r"texto\s+(?:original|refundido|vigente)\s+del?)\s+)*)?",
    re.IGNORECASE)
# Entre un cuerpo y el artículo que lo sigue: «Código Civil, artículo 1545», «(Código Civil, 2000, art. 2505)»,
# «de la Carta Fundamental, tales como los artículos 19…».
_RE_HUECO_ADELANTE = re.compile(
    r"^\s*(?:,|:)?\s*(?:\(\s*(?:\d{4}\s*,?\s*)?)?"
    r"(?:(?:tales\s+como|como|en\s+especial|especialmente|particularmente|en\s+particular)\s+(?:(?:el|los|la|las|sus?)\s+)?)?"
    r"(?:en\s+(?:su|el|sus|los)\s+)?$", re.IGNORECASE)
# «la Carta Fundamental garantiza en su artículo 19 N° 16»: el cuerpo es el sujeto de la oración.
_RE_HUECO_EN_SU = re.compile(r"^[^.;:()\[\]]{0,50}?\ben\s+sus?\s+$", re.IGNORECASE)
_MAX_HUECO, _MAX_HUECO_EN_SU = 30, 60
# «Ley N° 19.300, artículo 73 del Decreto Supremo N° 40»: el artículo trae su propio cuerpo, aunque
# la gramática no lo reconozca; nunca se le asigna el cuerpo que lo precede.
_RE_OTRO_CUERPO = re.compile(
    r"\s*,?\s*(?:del|de\s+la|de\s+los|de\s+las|de|al|a\s+la)\s+(?:decreto|d\.\s?s\.|reglamento|resoluci[oó]n|"
    r"circular|auto\s+acordado|acta|convenio|tratado|convenci[oó]n|pacto|c[oó]digo|ley|constituci[oó]n|"
    r"estatuto|ordenanza)(?![^\W\d_])", re.IGNORECASE)
# Artículo sin la palabra «artículo»: «el 19 N° 3 de nuestra Carta Fundamental», «del 146 del COT».
_RE_ARTICULO_IMPLICITO = re.compile(
    r"(?=[eEaA][lL]\s+\d|[dD][eE][lL]\s+\d)\b(?:el|del|al)\s+(?=\d{1,4}(?![\d°]|[.,]\d)(?:\s*,?\s*(?:N°|inciso|letra|literal|numeral)|"
    r"\s+(?:del|de\s+la|de\s+nuestr[oa])\s))", re.IGNORECASE)
_RE_CONTINUACION = re.compile(
    # «… DEL D.L. N° 3.500, QUE ESTABLECE NUEVO SISTEMA DE PENSIONES, Y 22, INCISOS …»: se salta la
    # cláusula descriptiva del cuerpo si después viene otro artículo (que igual debe traer su cuerpo).
    r"(?:\s*,\s*(?:que|de|del|sobre|relativ[oa]|en\s+materia)\s[^;()]{1,160}?"
    r"(?=\s*,?\s*(?:y|e)\s+(?:el\s+|los\s+|al\s+)?(?:art[íi]culos?\s*|arts?\.\s*)?\d))?"
    r"\s*(?:,|;)?\s*(?:y|e|o|u|así\s+como)\s+(?:el\s+|los\s+|al\s+)?(?:art[íi]culos?\s*|arts?\.\s*)?(?=\d)",
    re.IGNORECASE)
_RE_NUMERALES = re.compile(r"\d{1,3}")
_ORDINALES_F = {"primera": 1, "segunda": 2, "tercera": 3, "cuarta": 4, "quinta": 5, "sexta": 6,
                "septima": 7, "séptima": 7, "octava": 8, "novena": 9, "decima": 10, "décima": 10,
                "undecima": 11, "undécima": 11, "duodecima": 12, "duodécima": 12, "vigesima": 20, "vigésima": 20}
_RE_TRANSITORIA = re.compile(
    r"(?=[dD])\bdisposici[oó]n(?:es)?\s+(?P<ord>" + "|".join(sorted(_ORDINALES_F, key=len, reverse=True)) +
    r"|\d{1,2}\s*°?)\s+transitoria", re.IGNORECASE)


_RE_GUION_CORTADO = re.compile(r"(?=-[ \t]*\n)(?<=\w)-[ \t]*\n\s*(?=\w)")
_RE_NUMERO_ABREV = re.compile(
    r"(?=[Nn](?:\s*\.?\s*°|[Rr][Oo]|[ÚúUu][Mm]))\b(?:N\s*\.?\s*°|Nro\.?|N[úu]m\.|n[úu]mero)\s*(?=\d)", re.IGNORECASE)
_RE_NO_OCR = re.compile(r"(?=No)\bNo\.?\s+(?=\d)")
_PALABRA_NUMERO = (r"(?:CERO|UNO?|UNA|DOS|TRES|CUATRO|CINCO|SEIS|SIETE|OCHO|NUEVE|DIEZ|ONCE|DOCE|TRECE|CATORCE|"
                   r"QUINCE|DIECI[A-ZÁÉÍÓÚ]+|VEINTE|VEINTI[A-ZÁÉÍÓÚ]+|TREINTA|CUARENTA|CINCUENTA|SESENTA|SETENTA|"
                   r"OCHENTA|NOVENTA|CIEN|CIENTO|DOSCIENTOS|TRESCIENTOS|CUATROCIENTOS|QUINIENTOS|SEISCIENTOS|"
                   r"SETECIENTOS|OCHOCIENTOS|NOVECIENTOS|MIL)")
# Timbre de foja de los fallos del TC que pdftotext intercala en el texto: «0000177 CIENTO SETENTA Y SIETE».
_RE_TIMBRE_FOJA = re.compile(
    r"(?=0)\b0\d{5,7} " + _PALABRA_NUMERO + r"(?: (?:Y )?" + _PALABRA_NUMERO + r")*\b ?")


def normalizar_texto_juridico(texto: str) -> str:
    """Texto listo para la gramática: NFKC, guiones blandos, cortes de pdftotext, «N°» único.

    «º» (ordinal) se pasa a «°» ANTES de NFKC, que si no lo convierte en «o».
    """
    t = (texto or "").replace("º", "°").replace("­", "")
    if not unicodedata.is_normalized("NFKC", t):
        t = unicodedata.normalize("NFKC", t)
    t = _RE_GUION_CORTADO.sub("", t)
    t = " ".join(t.split())
    t = _RE_NUMERO_ABREV.sub("N° ", t)
    # El OCR de pdftotext lee «N°» como «No» («Ley No 20.600», «artículo 17 No 2»); solo con
    # mayúscula, para no tocar el «no» de una negación.
    t = _RE_NO_OCR.sub("N° ", t)
    t = _RE_TIMBRE_FOJA.sub("", t)
    return t.strip()


def _num(s: str) -> int:
    return int(s.replace(".", "").replace(",", ""))


def _ordinal_a_int(palabra: str) -> int:
    """«tercero» → 3, «decimoprimero» / «décimo primero» → 11, «vigésimo cuarto» → 24; 0 si no es ordinal."""
    p = unicodedata.normalize("NFKD", palabra.lower()).encode("ascii", "ignore").decode()
    p = re.sub(r"\s+", "", p)
    if p.isdigit():
        return int(p)
    for base, valor in (("decim", 10), ("vigesim", 20)):
        if p.startswith(base) and len(p) > len(base) + 1:
            return valor + _ORDINAL_NUM.get(p[len(base) + 1:], 0)
    return _ORDINAL_NUM.get(p, 0)


def _art_id(m: "re.Match[str]") -> str:
    art = str(_num(m.group("num")))
    if m.group("suf"):
        art += unicodedata.normalize("NFKD", m.group("suf").lower()).encode("ascii", "ignore").decode()
    elif m.group("letra") or m.group("letra2"):
        art += (m.group("letra") or m.group("letra2")).lower()
    if m.group("trans"):
        art += "-transitorio"
    return art


def _cuerpos_en(t: str) -> List[Tuple[int, int, str]]:
    """Menciones de cuerpos legales (inicio, fin, cuerpo), sin solaparse."""
    hallados: List[Tuple[int, int, str]] = []
    for m in _RE_NUMERADA.finditer(t):
        tipo = m.group("tipo").lower().replace(" ", "").replace(".", "")
        num = _num(m.group("num"))
        if tipo == "ley":
            antes = t[max(0, m.start() - 9):m.start()].lower()
            if antes.endswith("decreto ") or antes.endswith("fuerza de "):
                continue
            # «la ley 20 años»: sin N° y con menos de 3 dígitos no es una ley citada.
            if len(str(num)) < 3:
                continue
            cuerpo = f"ley-{num}"
        elif tipo in ("decretoley", "dl"):
            cuerpo = f"dl-{num}"
        else:
            cuerpo = f"dfl-{num}"
        hallados.append((m.start(), m.end(), cuerpo))
    for m in _RE_CUERPO_NOMBRE.finditer(t):
        for i, (_, cuerpo) in enumerate(_CUERPOS_NOMBRE):
            if m.group(f"n{i}"):
                hallados.append((m.start(), m.end(), cuerpo))
                break
    for m in _RE_CUERPO_SIGLA.finditer(t):
        for i, (_, cuerpo) in enumerate(_CUERPOS_SIGLA):
            if m.group(f"s{i}"):
                hallados.append((m.start(), m.end(), "sigla:" + cuerpo))
                break
    # Sin solapes: gana la mención que empieza antes y, a igualdad, la más larga.
    hallados.sort(key=lambda h: (h[0], -(h[1] - h[0])))
    limpios: List[Tuple[int, int, str]] = []
    fin = -1
    for h in hallados:
        if h[0] >= fin:
            limpios.append(h)
            fin = h[1]
    return limpios


_RE_NUMERAL_O_PARENTESIS = re.compile(r"[()]|\d{1,3}")
_RE_GRADO = re.compile(r"\s*°?")
# El artículo 19 de la CPR tiene 26 numerales: en «los artículos 19 N° 2 y 3 de la Constitución» el
# 3 es un numeral; en «los artículos 19 N° 3 y 76 de la Carta Fundamental» el 76 es otro artículo.
_NUMERALES_CPR_19 = 26


def _numerales_hasta(grupo: str, tope: int) -> Tuple[List[int], int]:
    """Numerales de un grupo («N° 2, 3 y 76») hasta el primero, después del primero, que pasa
    `tope`: (numerales, largo consumido). Lo que va entre paréntesis no cuenta."""
    numerales: List[int] = []
    fin, profundidad = len(grupo), 0
    for m in _RE_NUMERAL_O_PARENTESIS.finditer(grupo):
        s = m.group()
        if s in "()":
            profundidad += 1 if s == "(" else -1
            continue
        if profundidad > 0:
            continue
        if numerales and int(s) > tope:
            break
        numerales.append(int(s))
        fin = _RE_GRADO.match(grupo, m.end()).end()  # type: ignore[union-attr]
    else:
        fin = len(grupo)
    return numerales, fin


def _lista_articulos(t: str, pos: int, plural: bool = False,
                     tope: Optional[int] = None) -> Tuple[List[Tuple[str, List[int]]], int]:
    """Desde `pos` (justo después de «artículo»): artículos con sus numerales, y dónde termina.

    `plural` («artículos», «arts.»): un N° singular toma un solo numeral y lo que sigue en la
    lista son otros artículos. `tope`: una lista de numerales sigue solo con números hasta el
    tope (el resto son otros artículos)."""
    arts: List[Tuple[str, List[int]]] = []
    while True:
        m = _ART_TOKEN.match(t, pos)
        if not m:
            break
        art = _art_id(m)
        pos = m.end()
        numerales: List[int] = []
        while True:
            mod = _RE_MODIFICADOR.match(t, pos)
            if not mod or mod.end() == pos:
                break
            fin_mod = mod.end()
            if mod.group("numeral"):
                uno = _RE_NUMERAL_UNO.match(t, pos) if plural else None
                if uno:
                    fin_mod = uno.end()
                if tope is not None and not uno:
                    hasta, largo = _numerales_hasta(t[pos:fin_mod], tope)
                    numerales.extend(hasta)
                    fin_mod = pos + largo
                else:
                    sin_parentesis = re.sub(r"\([^()]*\)", "", t[pos:fin_mod])
                    numerales.extend(int(k) for k in _RE_NUMERALES.findall(sin_parentesis))
            elif mod.group("numeral_palabra"):
                palabra = re.sub(r"^(?:del\s+)?numeral\s+", "", mod.group("numeral_palabra"), flags=re.IGNORECASE)
                k = _ordinal_a_int(palabra)
                if k:
                    numerales.append(k)
            pos = fin_mod
        arts.append((art, numerales))
        sep = _RE_SEPARADOR_LISTA.match(t, pos)
        if not sep or not _ART_TOKEN.match(t, sep.end()):
            break
        pos = sep.end()
    return arts, pos


def _ids_de(cuerpo: str, arts: List[Tuple[str, List[int]]]) -> List[str]:
    ids: List[str] = []
    for art, numerales in arts:
        if numerales:
            ids.extend(f"norma:{cuerpo}:{art}:n{k}" for k in numerales)
        else:
            ids.append(f"norma:{cuerpo}:{art}")
    return ids


def normas_canonicas(texto: str) -> List[Tuple[str, int]]:
    """IDs canónicos de las normas mencionadas y cuántas veces, ordenados por ID.

    Un artículo solo se asigna al cuerpo legal que lo acompaña de inmediato («el artículo 1545
    del Código Civil», «Código Civil, artículo 1545», «art. 19 N° 3 CPR»); sin cuerpo explícito
    no hay ID. Un cuerpo mencionado sin artículo produce el ID del cuerpo solo.
    """
    return _normas_de(normalizar_texto_juridico(texto))


def normas_y_roles(texto: str) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]:
    """`normas_canonicas` y `roles_canonicos` normalizando el texto una sola vez."""
    t = normalizar_texto_juridico(texto)
    return _normas_de(t), _roles_de(t)


def _normas_de(t: str) -> List[Tuple[str, int]]:
    if not t:
        return []
    cuerpos = _cuerpos_en(t)
    por_inicio = {c[0]: c for c in cuerpos}
    por_fin = {c[1]: c for c in cuerpos}
    usados: set = set()
    cuenta: Counter = Counter()

    def _cuerpo_real(c: Tuple[int, int, str]) -> str:
        return c[2][6:] if c[2].startswith("sigla:") else c[2]

    def _cuerpo_tras(pos: int) -> Optional[Tuple[int, int, str]]:
        con = _RE_CONECTOR.match(t, pos)
        return por_inicio.get(con.end()) if con else None

    fines = sorted(por_fin)

    def _cuerpo_antes(pos: int) -> Optional[Tuple[int, int, str]]:
        """«Código Civil, artículo 1545» / «Ley N° 19.300, art. 11» / «CPR art. 19 N° 3»: el cuerpo
        más cercano hacia atrás, si lo que media entre ambos es solo un hueco admitido."""
        i = bisect.bisect_right(fines, pos) - 1
        if i < 0:
            return None
        hueco = t[fines[i]:pos]
        if (len(hueco) <= _MAX_HUECO and _RE_HUECO_ADELANTE.match(hueco)) or \
                (len(hueco) <= _MAX_HUECO_EN_SU and _RE_HUECO_EN_SU.match(hueco)):
            return por_fin[fines[i]]
        return None

    previos = {m.end(): [k for k in map(_ordinal_a_int, _RE_NUMERAL_PREVIO_ITEM.findall(m.group("k"))) if k]
               for m in _RE_NUMERAL_PREVIO.finditer(t)}
    inicios = sorted([(m.start(), m.end(), False) for m in _RE_ARTICULO.finditer(t)] +
                     [(m.start(), m.end(), True) for m in _RE_ARTICULO_IMPLICITO.finditer(t)])
    consumido = -1  # hasta dónde llegó la última frase (con sus continuaciones): no se recuenta
    for inicio, tras_palabra, implicito in inicios:
        if inicio < consumido:
            continue
        palabra = t[inicio:tras_palabra].rstrip().lower()
        plural = not implicito and (palabra.endswith("s") or palabra.startswith("arts"))
        arts, fin = _lista_articulos(t, tras_palabra, plural)
        if not arts:
            continue
        if previos.get(tras_palabra) and not arts[0][1]:
            arts[0] = (arts[0][0], previos[tras_palabra])
        cuerpo = _cuerpo_tras(fin)
        if implicito:
            # Sin la palabra «artículo» solo vale con un código, la CPR o una sigla justo después
            # (y nunca un año: «la reforma del 2005 de la Constitución»).
            if cuerpo is None or (_cuerpo_real(cuerpo).startswith(("ley-", "dl-", "dfl-"))
                                  and not cuerpo[2].startswith("sigla:")):
                continue
            if _cuerpo_real(cuerpo) == "cpr" and not (arts[0][0].isdigit() and int(arts[0][0]) <= 200):
                continue
        elif cuerpo is None and not _RE_OTRO_CUERPO.match(t, fin):
            cuerpo = _cuerpo_antes(inicio)
        if cuerpo is None:
            continue
        if plural and _cuerpo_real(cuerpo) == "cpr" and any(a == "19" for a, _ in arts):
            # «los artículos 19 N° 2 y 3 de la CPR»: en el artículo 19 de la CPR, sus numerales.
            arts19, fin19 = _lista_articulos(t, tras_palabra, False, _NUMERALES_CPR_19)
            if not t[min(fin, fin19):max(fin, fin19)].strip():   # la misma frase, leída de otro modo
                arts = arts19
                if previos.get(tras_palabra) and not arts[0][1]:
                    arts[0] = (arts[0][0], previos[tras_palabra])
        usados.add(cuerpo)
        cuenta.update(_ids_de(_cuerpo_real(cuerpo), arts))
        # «artículo 3 de la Ley N° 19.880 y 19 de la Constitución»
        pos = cuerpo[1] if cuerpo[0] >= fin else fin
        consumido = pos
        while True:
            cont = _RE_CONTINUACION.match(t, pos)
            if not cont:
                break
            mas, fin2 = _lista_articulos(t, cont.end(), plural)
            otro = _cuerpo_tras(fin2) if mas else None
            if otro is None:
                break
            usados.add(otro)
            cuenta.update(_ids_de(_cuerpo_real(otro), mas))
            pos = otro[1]
            consumido = pos
    # «la disposición segunda transitoria de la Constitución» → norma:cpr:2-transitorio
    for m in _RE_TRANSITORIA.finditer(t):
        cuerpo = _cuerpo_tras(m.end())
        if cuerpo is None:
            continue
        ordinal = m.group("ord").lower().strip(" °")
        k = _ORDINALES_F.get(ordinal) or (int(ordinal) if ordinal.isdigit() else 0)
        if k:
            usados.add(cuerpo)
            cuenta[f"norma:{_cuerpo_real(cuerpo)}:{k}-transitorio"] += 1
    # «LOC de Concesiones Mineras (Ley N° 18.097, 1982)»: la reformulación entre paréntesis es la misma mención.
    for a, b in zip(cuerpos, cuerpos[1:], strict=False):
        if (a in usados or b in usados) and _cuerpo_real(a) == _cuerpo_real(b) and \
                re.fullmatch(r"\s*\(\s*", t[a[1]:b[0]]):
            usados.update((a, b))
    for c in cuerpos:
        if c in usados:
            continue
        if c[2].startswith("sigla:") and c[2][6:] not in _SIGLAS_DISTINTIVAS:
            continue
        if c[2] == "cpr" and t[c[0]] == "c" and t[c[0]:c[1]].lower().startswith("constituci"):
            continue  # «la constitución de la concesión»: sustantivo común, no la CPR
        cuenta[f"norma:{_cuerpo_real(c)}"] += 1
    return sorted(cuenta.items())


def _miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def etiqueta_norma(norma_id: str) -> str:
    """Etiqueta legible de un ID canónico que `normas_canonicas` vuelve a reconocer igual."""
    partes = norma_id.split(":")
    if len(partes) < 2 or partes[0] != "norma":
        raise ValueError(f"ID de norma inválido: {norma_id!r}")
    cuerpo = partes[1]
    if cuerpo.startswith("ley-"):
        nombre = f"Ley N° {_miles(int(cuerpo[4:]))}"
    elif cuerpo.startswith("dl-"):
        nombre = f"Decreto Ley N° {_miles(int(cuerpo[3:]))}"
    elif cuerpo.startswith("dfl-"):
        nombre = f"DFL N° {_miles(int(cuerpo[4:]))}"
    else:
        nombre = CUERPOS[cuerpo]
    if len(partes) < 3:
        return nombre
    m = re.fullmatch(r"(\d+)(bis|ter|quater|quinquies|sexies|septies|octies|nonies|decies|[a-z])?(-transitorio)?",
                     partes[2])
    if not m:
        raise ValueError(f"Artículo inválido en {norma_id!r}")
    art = m.group(1)
    if m.group(2):
        art += f" {m.group(2)}" if len(m.group(2)) > 1 else f" {m.group(2).upper()}"
    if m.group(3):
        art = f"{m.group(1)}° transitorio" if not m.group(2) else art + " transitorio"
    etiqueta = f"{nombre}, Art. {art}"
    if len(partes) > 3 and partes[3].startswith("n"):
        etiqueta += f" N° {partes[3][1:]}"
    return etiqueta


# ── Roles ────────────────────────────────────────────────────────────────────────────────────
_RE_ROL_TC_SUFIJO = re.compile(
    r"(?=\d)(?<![\d.])(?P<n>" + _NUM_MILES + r")-\d{2}-"
    r"(?P<suf>INA|CPR|CDS|CAA|CCO|CPT|INC|INHM|INHP|CPN|CRR|CEN|ENCC|AUTO|OTR|PROY)\b", re.IGNORECASE)
_NUM_ROL = r"(?:\d{1,3}(?:\.\d{3})+|\d{1,6})(?![\d]|\.\d)(?:\s*[-/]\s*\d{2,4}(?:-[A-Z]{2,5})?)?"
_RE_STC = re.compile(
    r"(?=[sS][tT][cC]|[rR][oO][lL][eE][sS])\b(?:STC|roles)\s*(?:,?\s*rol(?:es)?\s*)?(?:N°s?\s*)?(?P<lista>" + _NUM_ROL +
    r"(?:\s*(?:[,;]|y|e)\s*(?:(?:y|e)\s+)?(?:STC\s*)?(?:Rol\s*)?(?:N°\s*)?" + _NUM_ROL + r")*)", re.IGNORECASE)
_RE_NUM_EN_LISTA = re.compile(r"(\d{1,3}(?:\.\d{3})+|\d{1,6})(?![\d]|\.\d)(?:\s*[-/]\s*\d{2,4}(?:-[A-Z]{2,5})?)?")
_RE_ROL_ANIO = re.compile(r"(?=[rR][oO][lL])\brol(?:es)?\s*(?:N°\s*)?(?P<n>" + _NUM_MILES + r")-(?P<anio>\d{4})(?![\d])", re.IGNORECASE)
_RE_ROL_TA = re.compile(r"(?=[rR])\brol\s*(?:N°\s*)?(?P<l>[RDSC])\s*-?\s*(?P<n>\d{1,4})\s*-\s*(?P<anio>\d{4})(?![\d])",
                        re.IGNORECASE)
_RE_CONTEXTO_CS = re.compile(r"corte\s+suprema|excma\.?\s+corte|e\.\s*corte|m[aá]ximo\s+tribunal|\bCS\b|"
                             r"\bC\.\s?S\.", re.IGNORECASE)
_RE_CONTEXTO_TC = re.compile(r"tribunal\s+constitucional|\bTC\b|\bSTC\b|esta\s+magistratura|"
                             r"requerimiento\s+de\s+(?:inaplicabilidad|inconstitucionalidad)", re.IGNORECASE)
# Rol del TC con año («Rol N° 541-2006», «1564-09») o tras «Tribunal Constitucional» sin la palabra rol.
_RE_ROL_TC_ANIO = re.compile(
    r"(?=[rR\d])(?:\brol(?:es)?\s*(?:N°\s*)?)?(?<![\d.\-])(?P<n>" + _NUM_MILES + r")-(?P<anio>\d{4}|\d{2})(?![\d\-])",
    re.IGNORECASE)
_RE_ROL_TA_LIBRE = re.compile(
    r"(?=[rR][oO][lL]|[rRdDsScC]\s*-\s*\d)(?<![\w\-])(?:rol\s*(?:N°\s*)?)?(?P<l>[RDSC])\s*-\s*(?P<n>\d{1,4})\s*-\s*(?P<anio>\d{4})(?![\d])",
    re.IGNORECASE)
_RE_TA_DESPUES = re.compile(r"\s*,?\s*(?:del|de\s+la|ante\s+el|en\s+el)\s+(?P<k>primer|segundo|tercer|1°|2°|3°|1er|2do|3er)"
                            r"\s+tribunal\s+ambiental", re.IGNORECASE)
_RE_SEP_LISTA_ROL = re.compile(r"^\s*(?:,|y|e)\s*(?:(?:,|y|e)\s*)?$", re.IGNORECASE)
_RE_CONTEXTO_NO_CS = re.compile(r"corte\s+de\s+apelaciones|\bC\.\s?A\.|iltma\.?|juzgado|\bRIT\b|\bRUC\b|"
                                r"tribunal\s+constitucional|tribunal\s+ambiental|\bTC\b", re.IGNORECASE)
_RE_CONTEXTO_TA = re.compile(r"(?P<k>primer|segundo|tercer|1°|2°|3°|1er|2do|3er)\s+tribunal\s+ambiental",
                             re.IGNORECASE)
_TA_ORDINAL = {"primer": "1ta", "1°": "1ta", "1er": "1ta", "segundo": "2ta", "2°": "2ta", "2do": "2ta",
               "tercer": "3ta", "3°": "3ta", "3er": "3ta"}


def _ultimo(regex: "re.Pattern[str]", texto: str) -> int:
    ultimo = -1
    for m in regex.finditer(texto):
        ultimo = m.end()
    return ultimo


def roles_canonicos(texto: str) -> List[Tuple[str, int]]:
    """Roles de jurisprudencia citados en un texto: `cs:`, `tc:` y `ta:`, con su frecuencia.

    Un rol con año solo es de la Corte Suprema si su contexto inmediato lo dice (y no dice Corte
    de Apelaciones, juzgado, RIT…): los números de rol se repiten entre tribunales.
    """
    return _roles_de(normalizar_texto_juridico(texto))


def _roles_de(t: str) -> List[Tuple[str, int]]:
    cuenta: Counter = Counter()
    ocupados: List[Tuple[int, int]] = []
    for m in _RE_ROL_TC_SUFIJO.finditer(t):
        cuenta[f"tc:{_num(m.group('n'))}"] += 1
        ocupados.append((m.start(), m.end()))
    for m in _RE_STC.finditer(t):
        if any(a <= m.start() < b for a, b in ocupados):
            continue
        # «roles N°s 280, 1153…» solo es del TC si el contexto lo dice; «STC …» siempre lo es.
        if m.group(0)[:3].lower() != "stc":
            antes = t[max(0, m.start() - 120):m.start()]
            if _ultimo(_RE_CONTEXTO_TC, antes) < 0:
                continue
        for n in _RE_NUM_EN_LISTA.finditer(m.group("lista")):
            cuenta[f"tc:{_num(n.group(1))}"] += 1
        ocupados.append((m.start(), m.end()))
    # Ambientales: «R-23-2019 del Primer Tribunal Ambiental», listas «R-21-2021, R-35-2021 y R-29-2020
    # del Tercer Tribunal Ambiental» o el tribunal dicho antes («Segundo Tribunal Ambiental, 2019, R-141-2017»).
    ta = list(_RE_ROL_TA_LIBRE.finditer(t))
    grupos: List[List["re.Match[str]"]] = []
    for m in ta:
        if grupos and _RE_SEP_LISTA_ROL.match(t[grupos[-1][-1].end():m.start()]):
            grupos[-1].append(m)
        else:
            grupos.append([m])
    for grupo in grupos:
        despues = _RE_TA_DESPUES.match(t, grupo[-1].end())
        if despues:
            tribunal = _TA_ORDINAL[despues.group("k").lower()]
        else:
            ctx = list(_RE_CONTEXTO_TA.finditer(t[max(0, grupo[0].start() - 150):grupo[0].start()]))
            if not ctx:
                continue
            tribunal = _TA_ORDINAL[ctx[-1].group("k").lower()]
        for m in grupo:
            cuenta[f"ta:{tribunal}:{m.group('l').lower()}-{int(m.group('n'))}-{m.group('anio')}"] += 1
            ocupados.append((m.start(), m.end()))
    for m in _RE_ROL_ANIO.finditer(t):
        if any(a <= m.start() < b for a, b in ocupados):
            continue
        antes = t[max(0, m.start() - 80):m.start()]
        tras = t[m.end():m.end() + 40]
        pos_cs = max(_ultimo(_RE_CONTEXTO_CS, antes), -1)
        pos_no = max(_ultimo(_RE_CONTEXTO_NO_CS, antes), -1)
        cs_despues = _RE_CONTEXTO_CS.search(tras)
        no_despues = _RE_CONTEXTO_NO_CS.search(tras)
        if (pos_cs > pos_no) or (pos_cs < 0 and pos_no < 0 and cs_despues and not no_despues):
            cuenta[f"cs:{_num(m.group('n'))}-{m.group('anio')}"] += 1
            ocupados.append((m.start(), m.end()))
    # TC con año: el contexto más cercano antes del rol tiene que ser el Tribunal Constitucional.
    for m in _RE_ROL_TC_ANIO.finditer(t):
        if any(a <= m.start() < b for a, b in ocupados):
            continue
        antes = t[max(0, m.start() - 120):m.start()]
        pos_tc = _ultimo(_RE_CONTEXTO_TC, antes)
        pos_otro = max(_ultimo(_RE_CONTEXTO_CS, antes),
                       _ultimo(re.compile(r"corte\s+de\s+apelaciones|\bC\.\s?A\.|juzgado|\bRIT\b|\bRUC\b|"
                                          r"tribunal\s+ambiental", re.IGNORECASE), antes))
        sin_rol = not m.group(0).lower().startswith("rol")
        despues_tc = len(m.group("anio")) == 2 and pos_tc < 0 and pos_otro < 0 and \
            _RE_CONTEXTO_TC.search(t[m.end():m.end() + 60]) is not None
        if despues_tc or (pos_tc > pos_otro and (not sin_rol or len(antes) - pos_tc <= 12)):
            cuenta[f"tc:{_num(m.group('n'))}"] += 1
            ocupados.append((m.start(), m.end()))
    return sorted(cuenta.items())


def rol_canonico(texto: str, tribunal: Optional[str] = None) -> Optional[str]:
    """ID canónico de UN rol («Rol N° 29.635-2018», «10822-21-INA», «R-32-2020»), o None si es
    ambiguo. `tribunal` ∈ {"cs", "tc", "1ta", "2ta", "3ta"} resuelve los casos sin contexto."""
    t = normalizar_texto_juridico(texto)
    t = re.sub(r"^(?:STC|rol(?:es)?|causa)\s*(?:N°\s*)?", "", t, flags=re.IGNORECASE).strip()
    t = re.sub(r"^N°\s*", "", t).strip()
    tc = re.fullmatch(r"(" + _NUM_MILES + r")-\d{2}-[A-Za-z]{2,5}", t)
    if tc:
        return f"tc:{_num(tc.group(1))}"
    ta = re.fullmatch(r"([RDSC])\s*-?\s*(\d{1,4})\s*-\s*(\d{4})", t, re.IGNORECASE)
    if ta and tribunal in ("1ta", "2ta", "3ta"):
        return f"ta:{tribunal}:{ta.group(1).lower()}-{int(ta.group(2))}-{ta.group(3)}"
    cs = re.fullmatch(r"(" + _NUM_MILES + r")-(\d{4})", t)
    if cs and tribunal in (None, "cs"):
        return f"cs:{_num(cs.group(1))}-{cs.group(2)}"
    solo = re.fullmatch(r"(" + _NUM_MILES + r")", t)
    if solo and tribunal == "tc":
        return f"tc:{_num(solo.group(1))}"
    return None


# «n°» va aparte: «°» no es letra y un `\b` tras él no calzaría nunca («Rol N° 10.641-2024»).
_RE_RUIDO_CONSULTA = re.compile(
    r"\b(?:rol(?:es)?|causa|sentencia|fallo|de|del|la|el|en|corte\s+suprema|excma\.?|cs|recurso|ficha)\b|\bn°",
    re.IGNORECASE)
_RE_CONSULTA_NO_CS = re.compile(r"corte\s+de\s+apelaciones|\bC\.\s?A\.|juzgado|\bRIT\b|\bRUC\b|\bC-\d", re.IGNORECASE)


def resolver_consulta(consulta: str) -> List[str]:
    """IDs canónicos a los que apunta una consulta, solo si es esencialmente un identificador
    («Rol 1234-2023», «STC 2402», «art. 1545 del Código Civil», «Ley 19.300») o trae contexto.

    Una consulta en prosa («¿qué es el contrato? art. 1545») no se secuestra: devuelve solo las
    normas con artículo o número explícito, nunca un rol sin contexto.
    """
    q = normalizar_texto_juridico(consulta)
    if not q:
        return []
    ids = [i for i, _ in normas_canonicas(q) if i.count(":") >= 2 or re.match(r"norma:(?:ley|dl|dfl)-", i)]
    ids += [i for i, _ in roles_canonicos(q)]
    resto = _RE_RUIDO_CONSULTA.sub(" ", q)
    resto = re.sub(r"[^\w.\-]+", " ", resto).strip()
    if re.fullmatch(_NUM_MILES + r"-\d{2}-[A-Za-z]{2,5}", resto):
        ids.append(rol_canonico(resto) or "")
    elif re.fullmatch(r"(?:" + _NUM_MILES + r")-\d{4}", resto) and not _RE_CONSULTA_NO_CS.search(q):
        # «2019-2023» sin la palabra rol es un rango de años, no una causa.
        anio_suelto = re.fullmatch(r"(?:19|20)\d{2}-\d{4}", resto) and not re.search(r"\brol\b", q, re.IGNORECASE)
        if not anio_suelto:
            ids.append(rol_canonico(resto, "cs") or "")
    vistos: List[str] = []
    for i in ids:
        if i and i not in vistos:
            vistos.append(i)
    return vistos
