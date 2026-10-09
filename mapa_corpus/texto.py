"""Lectura tolerante de los formatos del dataset: front matter YAML, viñetas y fechas."""

from __future__ import annotations

import json
import re
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
