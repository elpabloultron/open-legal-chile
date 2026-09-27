"""Formato único de citas (AGENTS.md §2) y detección de normas en texto libre.

Nace de un problema concreto: cada herramienta armaba sus corchetes a mano y el texto de la
norma citada no viajaba con la cita, así que quien respondía citaba de memoria o sin texto.
Acá viven el formato oficial, el bloque de fuentes y el detector que permite ir a buscar el
texto literal de una norma mencionada en lenguaje natural.
"""

import re
from typing import Any, Dict, List

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
}

_OBRAS = "|".join(sorted(CODIGOS, key=len, reverse=True))
_ART = r"\d+[a-zA-Z]?"
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
            obra = m.group("obra").lower()
            articulo = m.group("art")
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
            articulo = m.group("art")
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
