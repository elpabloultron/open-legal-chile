"""Lectura tolerante de los formatos del dataset: front matter YAML, viñetas y fechas."""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import date
from typing import Any, Dict, Optional, Tuple

from citas_legales import normalizar_texto_juridico

_MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
          "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}
_RE_VINETA = re.compile(r"\*\*(?P<k>[^*:]{1,60}):\*\*\s*(?P<v>.*?)(?=\s*·\s*\*\*[^*:]{1,60}:\*\*|$)")


def normalizar_cuerpo(texto: str) -> str:
    return normalizar_texto_juridico(texto)


def leer_front_matter(texto: str) -> Tuple[Dict[str, Any], str]:
    """(metadatos, cuerpo). Admite listas YAML en bloque y listas JSON en línea.

    Usa PyYAML (viene con huggingface_hub) y, si el bloque no es YAML válido, un lector línea a
    línea que conserva escalares y listas.
    """
    if not texto.startswith("---"):
        return {}, texto
    fin = texto.find("\n---", 3)
    if fin < 0:
        return {}, texto
    bruto = texto[3:fin].strip("\n")
    cuerpo = texto[fin + 4:]
    if cuerpo.startswith("\n"):
        cuerpo = cuerpo[1:]
    meta: Dict[str, Any] = {}
    try:
        import yaml  # type: ignore[import-untyped]
        cargado = yaml.safe_load(bruto)
        if isinstance(cargado, dict):
            meta = {str(k): v for k, v in cargado.items()}
    except Exception:  # noqa: BLE001 — YAML roto: se lee a mano
        meta = {}
    if not meta:
        clave = None
        for linea in bruto.splitlines():
            m = re.match(r"^([A-Za-z_][\w\-]*):\s*(.*)$", linea)
            if m:
                clave, valor = m.group(1), m.group(2).strip()
                if valor.startswith("[") and valor.endswith("]"):
                    try:
                        meta[clave] = json.loads(valor)
                        continue
                    except ValueError:
                        pass
                meta[clave] = valor.strip('"').strip("'") if valor else []
            elif clave and re.match(r"^\s*-\s+", linea) and isinstance(meta.get(clave), list):
                meta[clave].append(re.sub(r"^\s*-\s+", "", linea).strip().strip('"').strip("'"))
    for k, v in list(meta.items()):
        if isinstance(v, str) and v.startswith("[") and v.endswith("]"):
            try:
                meta[k] = json.loads(v)
            except ValueError:
                pass
    return meta, cuerpo


def leer_vinetas(texto: str, limite: int = 6000) -> Dict[str, str]:
    """Campos `- **Clave:** valor` de la cabecera (varias claves por línea con « · »)."""
    campos: Dict[str, str] = {}
    for linea in texto[:limite].splitlines():
        linea = linea.strip()
        if not linea.startswith(("- **", "* **", "**")):
            continue
        for m in _RE_VINETA.finditer(linea):
            clave = m.group("k").strip().lower()
            if clave not in campos:
                campos[clave] = m.group("v").strip()
    return campos


_UNIDADES = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once",
             "doce", "trece", "catorce", "quince", "dieciseis", "diecisiete", "dieciocho", "diecinueve",
             "veinte", "veintiuno", "veintidos", "veintitres", "veinticuatro", "veinticinco", "veintiseis",
             "veintisiete", "veintiocho", "veintinueve", "treinta"]
_NUMEROS = {p: i for i, p in enumerate(_UNIDADES) if p}
_NUMEROS.update({"un": 1, "primero": 1, "veintiun": 21, "treinta y uno": 31})
_PALABRA_NUM = r"(?:\d{1,2}°?|treinta y uno|[a-z]+)"
_RE_FECHA_RESOLUCION = re.compile(
    r"\[\s*(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})\s*\]"
    rf"|\bsantiago\s*,?\s*(?:a\s+)?({_PALABRA_NUM})\s+de\s+([a-z]+)\s+(?:de|del)\s+"
    r"(\d{4}|dos\s+mil(?:\s+(?:treinta y uno|[a-z]+))?)\b")


_ROL_LISTA = (r"\bRol(?:es)?\s*N[°º]?\s*((?:[\d.]+\s*(?:-\s*\d{2,4})?\s*(?:-?\s*[A-Z]{2,5})?\s*"
              r"(?:/|\(|\by\b|,)\s*(?:N[°º]?\s*)?)*[\d.]+\s*\)?\s*"
              r"(?:-\s*\d{2,4}(?![\d])(?:\s*-?\s*[A-Z]{2,5}\b)?|-?\s*[A-Z]{2,5}\b))")
_RE_PIE_TC = re.compile(_ROL_LISTA)


def _numeros(fragmento: str) -> set:
    return {int(n.replace(".", "")) for n in re.findall(r"(?<![\d.])\d{1,3}(?:\.\d{3})+|(?<![\d.])\d{3,6}(?![\d])",
                                                          fragmento)}


def nombra_rol_tc(texto: str, numero: int) -> bool:
    """El documento del TC es de la causa `numero`: lo nombra donde el TC pone el rol propio, no en
    una cita cualquiera. Encabezado de las sentencias («Sentencia Rol 15.686-24 INA», «Sentencia Rol
    9231-2020», acumuladas «Sentencia Roles N° 16.122-25-INHP y N° 16.138-25-INHP», «15.713
    (15.777)-24») o el ÚLTIMO rol del documento, el del pie antes de las firmas («Rol Nº 15.707-24
    INA.», «Rol N° 16.615-INA»). Un precedente citado («STC Rol N° 8536-20», «como se resolvió en
    causa Rol N° 16.067-24 INA») no cuenta."""
    if not numero:
        return False
    plano = " ".join(str(texto or "").split())
    con_puntos = f"{numero:,}".replace(",", ".")
    num = rf"(?<![\d.])(?:{re.escape(con_puntos)}|{numero})(?![\d]|\.\d)"
    otro = r"[\d.]+\s*(?:-\s*\d{2,4})?\s*(?:-?\s*[A-Z]{2,5})?\s*(?:/|\(|\by\b|,)\s*(?:N[°º]?\s*)?"
    if re.search(rf"\bSentencia\s+Rol(?:es)?\s*(?:N[°º]?\s*)?(?:{otro})*{num}", plano[:1500]):
        return True
    # Algunas resoluciones traen anexados los correos de notificación («Enviado el: … Asunto: …»),
    # que nombran otros roles (la gestión, la causa): el pie propio es el de antes del primer correo.
    correo = re.search(r"\bEnviado(?: el)?:\s", plano)
    zona = plano[:correo.start()] if correo else plano
    pies = list(_RE_PIE_TC.finditer(zona[-2500:]))
    return bool(pies) and numero in _numeros(pies[-1].group(1))


def _sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _numero(palabra: str) -> Optional[int]:
    palabra = palabra.strip().rstrip("°")
    return int(palabra) if palabra.isdigit() else _NUMEROS.get(palabra)


def fecha_resolucion(texto: Any, alcance: int = 3000) -> Optional[str]:
    """La fecha de la resolución o sentencia del TC, en ISO: «[8 de julio de 2021]» bajo el rol de
    las sentencias o «Santiago, quince de abril de dos mil veintiuno.» al comienzo de las
    resoluciones (la primera fecha en cifras de estas es la de presentación del requerimiento)."""
    s = _sin_tildes(" ".join(str(texto or "")[: alcance * 2].split())[:alcance].lower())
    for m in _RE_FECHA_RESOLUCION.finditer(s):
        if m.group(1):
            dia, mes, anio = int(m.group(1)), _MESES.get(m.group(2)), int(m.group(3))
        else:
            dia, mes = _numero(m.group(4)) or 0, _MESES.get(m.group(5))
            texto_anio = " ".join(m.group(6).split())
            if texto_anio.isdigit():
                anio = int(texto_anio)
            else:
                resto = texto_anio[len("dos mil"):].strip()
                sufijo = _numero(resto) if resto else 0
                if sufijo is None:
                    continue
                anio = 2000 + sufijo
        if mes and 1900 <= anio <= 2100:
            try:
                return date(anio, mes, dia).isoformat()
            except ValueError:
                continue
    return None


def fecha_iso(texto: Any) -> Optional[str]:
    """La primera fecha válida en ISO (AAAA-MM-DD): ISO, d-m-a, d/m/a o «d de mes de a»."""
    s = str(texto or "").strip().lower()
    if not s:
        return None
    candidatos = []
    for m in re.finditer(r"(\d{4})-(\d{1,2})-(\d{1,2})", s):
        candidatos.append((m.start(), int(m.group(1)), int(m.group(2)), int(m.group(3))))
    for m in re.finditer(r"(?<!\d)(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})(?!\d)", s):
        candidatos.append((m.start(), int(m.group(3)), int(m.group(2)), int(m.group(1))))
    for m in re.finditer(r"(\d{1,2})°?\s+de\s+([a-z]+)\s+(?:de|del)\s+(\d{4})", s):
        mes = _MESES.get(m.group(2))
        if mes:
            candidatos.append((m.start(), int(m.group(3)), mes, int(m.group(1))))
    for _, a, mes, d in sorted(candidatos):
        if 1900 <= a <= 2100:
            try:
                return date(a, mes, d).isoformat()
            except ValueError:  # «31-02-2024»: no es una fecha
                continue
    return None
