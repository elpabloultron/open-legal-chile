"""Un extractor puro por colección del dataset: (ruta, bytes) → fila del mapa.

Las filas son livianas: metadatos, IDs canónicos de lo que citan y un resumen de 600 caracteres.
El texto íntegro sigue en HF y se baja (con la revisión fijada) solo cuando hay que citarlo.

Reglas aprendidas de los datos reales (rev 9378453d, 2026-10):
- TC: la cabecera de los 965 archivos describe OTRA causa que el cuerpo. La identidad de la
  entrada es la del cuerpo (su «Rol N°» o el `extended/<id>` del documento oficial); la cabecera
  queda como metadato y la fila se marca `cabecera_desalineada`.
- Ambientales: fechas en varios formatos, roles con basura («R 14-2021  Descargar Síntesis»),
  causas acumuladas en el nombre, carátulas de 3TA con la síntesis pegada, OCR con «No» por «N°».
- Revistas: el YAML cambia por revista (autor|autores, cita_oficial|cita_canonica,
  url_ojs|url_original) y `normas_citadas` viene en lista YAML, JSON en línea o como texto.
- CS: las fichas salen del índice `cs_sentencias_2anios.jsonl` (misma información que los .md
  más `documento_id`), así la construcción completa y la incremental dan los mismos bytes.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from citas_legales import normalizar_texto_juridico, normas_canonicas, normas_y_roles, roles_canonicos
from mapa_corpus import ids
from mapa_corpus.texto import fecha_iso, fecha_resolucion, leer_front_matter, leer_vinetas, nombra_rol_tc

RESUMEN = 600
# Reglas de extracción: subir este número fuerza una reconstrucción completa del mapa.
VERSION_EXTRACTORES = "2"


def _decodificar(datos: bytes) -> str:
    try:
        return datos.decode("utf-8")
    except UnicodeDecodeError:
        return datos.decode("latin-1")


def _titulo(texto: str) -> str:
    m = re.search(r"^#\s+(.+)$", texto, re.MULTILINE)
    return " ".join(m.group(1).split()) if m else ""


def _cuerpo_tras_cabecera(texto: str) -> str:
    """El texto después de la primera línea `---` (las fichas ponen ahí el texto íntegro)."""
    m = re.search(r"\n---\s*\n", texto)
    return texto[m.end():] if m else ""


_LINEA_META = re.compile(r"^\s*(?:#|>|- \*\*|\*\*(?:Tratadistas?|Autor|Revista|Publicaci|[ÁA]rea|Cita)|---)")


def _resumen(texto: str, desde: Tuple[str, ...] = ()) -> str:
    """600 caracteres de prosa: sin títulos, viñetas de metadatos ni citas en bloque."""
    texto = "\n".join(x for x in texto.splitlines()[:400] if not _LINEA_META.match(x)) + "\n" + \
        "\n".join(texto.splitlines()[400:])
    t = normalizar_texto_juridico(texto)
    for marca in desde:
        i = t.lower().find(marca.lower())
        if i >= 0:
            t = t[i:]
            break
    if len(t) <= RESUMEN:
        return t
    corte = t.rfind(" ", 0, RESUMEN)
    return t[:corte if corte > RESUMEN // 2 else RESUMEN] + " …"


def _citas(texto: str, propio: Optional[str] = None) -> Dict[str, Any]:
    """normas [[id, n]], y roles citados separados por tribunal (sin el propio)."""
    normas_n, roles_n = normas_y_roles(texto)
    normas = [[i, n] for i, n in normas_n]
    roles = [i for i, _ in roles_n if i != propio]
    return {
        "normas": normas,
        "cita_cs": sorted(r for r in roles if r.startswith("cs:")),
        "cita_tc": sorted(r for r in roles if r.startswith("tc:")),
        "cita_ta": sorted(r for r in roles if r.startswith("ta:")),
    }


def _base(col: str, ruta: str, blob: str, n_bytes: int, id_: str, titulo: str) -> Dict[str, Any]:
    return {"id": id_, "col": col, "ruta": ruta, "blob": blob, "bytes": n_bytes, "titulo": titulo}


def _limpiar_vacios(fila: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in fila.items() if v not in (None, "", [], {})}


# ── Corte Suprema ─────────────────────────────────────────────────────────────────────────
def _txt(valor: Any) -> str:
    """Texto de un campo de ficha con espacios normalizados; «—» (sin dato) es vacío."""
    t = " ".join(str(valor or "").split())
    return "" if t in ("—", "-", "–") else t


def fila_cs(registro: Dict[str, Any], ruta: str, blob: str, n_bytes: int) -> Optional[Dict[str, Any]]:
    """Una fila del índice CS (o los campos leídos del .md, con las mismas claves) → fila."""
    id_ = ids.id_cs(str(registro.get("rol") or ""))
    if not id_:
        return None
    fila = _base("cs", ruta, blob, n_bytes, id_, _txt(registro.get("caratula")))
    era = registro.get("era")
    fila.update({
        "rol": id_[3:],
        "era": int(str(era)) if str(era or "").isdigit() else int(id_.rsplit("-", 1)[1]),
        "fecha": fecha_iso(registro.get("fecha")),
        "sala": ids.sala_id(_txt(registro.get("sala"))),
        "sala_txt": _txt(registro.get("sala")),
        "recurso": ids.recurso_id(_txt(registro.get("recurso"))),
        "recurso_txt": _txt(registro.get("recurso")),
        "resultado": _txt(registro.get("resultado")),
        "origen": ids.tribunal_id(_txt(registro.get("tribunal_origen"))),
        "origen_txt": _txt(registro.get("tribunal_origen")),
        "ministros": ids.ministros(str(registro.get("ministros") or "")),
        "ministros_txt": [" ".join(m.split()) for m in re.split(r"\s*,\s*", str(registro.get("ministros") or ""))
                          if m.strip() and m.strip() not in ("—", "-")],
        "publicacion": _txt(registro.get("publicacion")),
    })
    doc = registro.get("documento_id")
    if isinstance(doc, int) or (isinstance(doc, str) and doc.isdigit()):
        fila["documento_id"] = int(doc)
    return _limpiar_vacios(fila)


def registro_desde_md_cs(texto: str) -> Dict[str, Any]:
    """Los campos de una ficha .md de la CS con las claves del índice JSONL."""
    v = leer_vinetas(texto)
    tribunal = v.get("tribunal", "")
    sala = tribunal.split("—", 1)[1].strip() if "—" in tribunal else ""
    return {"rol": v.get("rol", ""), "era": v.get("era", ""), "fecha": v.get("fecha", ""),
            "caratula": _titulo(texto), "sala": sala, "recurso": v.get("recurso", ""),
            "resultado": v.get("resultado", ""), "tribunal_origen": v.get("tribunal de origen", ""),
            "ministros": v.get("ministros", ""), "publicacion": v.get("publicación", v.get("publicacion", ""))}


# ── Tribunal Constitucional ───────────────────────────────────────────────────────────────
# El rol propio en el cuerpo: con sufijo del TC («13.139-22-INA») o tras «Sentencia»/«STC».
# «N°» es opcional: el encabezado de las sentencias es «Sentencia Rol 15.686-24 INA» y el pie de las
# resoluciones «Rol Nº 15.707-24 INA.» (la sigla puede ir sin guion).
_RE_ROL_CUERPO_TC = re.compile(
    r"\bRol(?:es)?\s*(?:N[°º]?\s*)?(\d{1,3}(?:\.\d{3})+|\d{1,6})\s*-\s*\d{2}\s*-?\s*[A-Z]{2,5}\b"
    r"|\b(?:Sentencia|STC)\s+Rol\s*(?:N[°º]?\s*)?(\d{1,3}(?:\.\d{3})+|\d{1,6})\s*-\s*\d{2,4}", re.IGNORECASE)
_RE_EXTENDED = re.compile(r"/extended/(\d+)/")


def fila_tc(ruta: str, datos: bytes, blob: str) -> Dict[str, Any]:
    texto = _decodificar(datos)
    v = leer_vinetas(texto)
    titulo = _titulo(texto)
    cuerpo = _cuerpo_tras_cabecera(texto)
    cab_rol = re.sub(r"^Rol\s*N°?\s*", "", v.get("rol", ""), flags=re.IGNORECASE).strip()
    cab_num = re.match(r"(\d+)", cab_rol)
    inicio = normalizar_texto_juridico(cuerpo[:4000])
    candidatos = [int((m.group(1) or m.group(2)).replace(".", "")) for m in _RE_ROL_CUERPO_TC.finditer(inicio)]
    m_ext = _RE_EXTENDED.search(v.get("documento oficial", ""))
    ext = int(m_ext.group(1)) if m_ext else None
    # Las resoluciones nombran su rol solo al pie y pueden citar otro rol antes («STC Rol N° 8536-20»):
    # si el documento oficial nombra su número donde el TC pone el rol propio, esa es su identidad
    # (el mismo criterio con que tc_pdfs_a_md decide escribirlo).
    if ext is not None and ext not in candidatos and nombra_rol_tc(cuerpo, ext):
        candidatos.insert(0, ext)
    if ext is not None and ext in candidatos:
        numero, fuente_id = ext, "cuerpo"
    elif candidatos:
        numero, fuente_id = candidatos[0], "cuerpo"
    elif ext is not None:
        numero, fuente_id = ext, "documento_oficial"
    elif cab_num:
        numero = int(cab_num.group(1))
        fuente_id = "cabecera"
    else:
        numero = 0
        fuente_id = "ninguna"
    id_ = f"tc:{numero}"
    fila = _base("tc", ruta, blob, len(datos), id_, titulo)
    calidad: List[str] = []
    if cab_num and int(cab_num.group(1)) != numero:
        calidad.append("cabecera_desalineada")
    if fuente_id != "cuerpo":
        calidad.append(f"identidad_por_{fuente_id}")
    fila.update({
        "rol": str(numero),
        "tipo": titulo.split("—", 1)[0].strip() if "—" in titulo else "",
        # La fecha de la cabecera, cuando la cabecera es de esta causa: en las resoluciones la primera
        # fecha en cifras del cuerpo es la de presentación del requerimiento.
        "fecha": (fecha_iso(v.get("fecha")) if "cabecera_desalineada" not in calidad else None)
                 or fecha_resolucion(cuerpo) or fecha_iso(inicio[:1500]) or fecha_iso(v.get("fecha")),
        "cabecera": _limpiar_vacios({"rol": cab_rol, "fecha": fecha_iso(v.get("fecha")),
                                     "gestion": " ".join(v.get("gestión pendiente / carátula", "").split()),
                                     "resultado": v.get("resultado", "") if v.get("resultado") != "None" else ""}),
        "url_oficial": v.get("documento oficial", ""),
        "calidad": calidad,
        "chars": len(cuerpo),
        "resumen": _resumen(cuerpo, ("VISTOS", "CONSIDERANDO")),
    })
    fila.update(_citas(cuerpo, propio=id_))
    # Las citas de la gestión pendiente (cabecera) son de su propia causa: se guardan aparte.
    gestion = fila["cabecera"].get("gestion", "")
    fila["gestion_cs"] = [i for i, _ in roles_canonicos(gestion) if i.startswith("cs:")]
    return _limpiar_vacios(fila)


# ── Tribunales ambientales ────────────────────────────────────────────────────────────────
_RE_ROL_TA = re.compile(r"([RDSC])\s*[-_ ]?\s*0*(\d{1,4})\s*-\s*(\d{4})", re.IGNORECASE)
_TRIBUNAL_TA = {"primer": "1ta", "segundo": "2ta", "tercer": "3ta"}


def fila_ta(ruta: str, datos: bytes, blob: str) -> Dict[str, Any]:
    texto = _decodificar(datos)
    v = leer_vinetas(texto)
    partes = ruta.split("/")
    tribunal = partes[1].lower() if len(partes) > 2 else ""
    for palabra, k in _TRIBUNAL_TA.items():
        if v.get("tribunal", "").lower().startswith(palabra):
            tribunal = k
    roles = [(m.group(1).lower(), int(m.group(2)), m.group(3))
             for m in _RE_ROL_TA.finditer(v.get("rol", "") + " " + partes[-1])]
    sintesis = "descargar" in (v.get("rol", "") + partes[-1]).lower()
    if roles:
        letra, num, anio = roles[0]
        id_ = f"ta:{tribunal}:{letra}-{num}-{anio}"
    else:
        id_ = f"ta:{tribunal}:{ids.slug(partes[-1][:-3])}"
    acumuladas = sorted({f"ta:{tribunal}:{le}-{n}-{a}" for le, n, a in roles[1:]} - {id_})
    caratula = re.split(r"\s+S[ií]ntesis\b", v.get("carátula", v.get("caratula", "")), maxsplit=1)[0]
    cuerpo = _cuerpo_tras_cabecera(texto)
    tiene_texto = len(cuerpo.strip()) > 2000 and "no se puede extraer el texto" not in texto[:3000]
    fila = _base("ta", ruta, blob, len(datos), id_, " ".join(caratula.split()).strip('"'))
    fila.update({
        "tribunal": f"organo:{tribunal}" if tribunal else "",
        "rol": id_.split(":", 2)[2],
        "tipo": "sintesis" if sintesis else (_titulo(texto).split("—", 1)[0].strip() if "—" in _titulo(texto) else ""),
        "fecha": fecha_iso(v.get("fecha")),
        "materia": " ".join(v.get("materia", "").split()),
        "resuelve": " ".join(v.get("resuelve", "").split()),
        "redactor": ids.ministro_id(v.get("redactor", "")) if v.get("redactor", "").strip() else None,
        "ministros": ids.ministros(v.get("integración", v.get("integracion", ""))),
        "acumuladas": acumuladas,
        "url_oficial": v.get("documento oficial", ""),
        "tiene_texto": tiene_texto,
        "chars": len(cuerpo),
        "resumen": _resumen(cuerpo, ("VISTOS", "Vistos")) if tiene_texto else "",
    })
    if tiene_texto:
        fila.update(_citas(cuerpo))
    return _limpiar_vacios(fila)


# ── Doctrina: revistas y obras ────────────────────────────────────────────────────────────
_SOLO_FICHA = re.compile(r"texto [ií]ntegro disponible", re.IGNORECASE)


def normas_de_lista(normas: Any) -> List[str]:
    """`normas_citadas` del YAML («[BCN - Código Civil, Art. 1071]», «[CPR 1980 - Art. 19]»,
    «Código Civil») → IDs canónicos."""
    if isinstance(normas, str):
        normas = [normas]
    salida: List[str] = []
    for n in normas or []:
        s = str(n).strip().strip("`").strip("[]").strip()
        s = re.sub(r"^BCN\s*-\s*", "", s)
        s = re.sub(r"^CPR(?:\s*1980)?\s*-\s*", "Constitución, ", s)
        salida.extend(i for i, _ in normas_canonicas(s))
    return sorted(set(salida))


def _autores(meta: Dict[str, Any], vinetas_doc: Dict[str, str]) -> List[str]:
    crudo = meta.get("autores") or meta.get("autor") or vinetas_doc.get("autor(es)") or ""
    if isinstance(crudo, list):
        nombres = [str(x) for x in crudo]
    else:
        nombres = ids.separar_autores(str(crudo))
    return [n for n in nombres if ids.es_persona(n)]


def fila_doc(ruta: str, datos: bytes, blob: str) -> Dict[str, Any]:
    texto = _decodificar(datos)
    meta, cuerpo = leer_front_matter(texto)
    partes = ruta.split("/")
    es_revista = len(partes) >= 4 and partes[1] == "revistas"
    titulo = " ".join(str(meta.get("titulo") or _titulo(texto) or partes[-1][:-3]).split())
    fila = _base("doc", ruta, blob, len(datos), ids.id_ruta("doc", ruta, "doctrina/"), titulo)
    m_trat = re.search(r"\*\*Tratadistas?:\*\*\s*([^|\n]+)", texto[:5000])
    autores_txt = _autores(meta, {}) if (meta.get("autores") or meta.get("autor")) else (
        ids.separar_autores(m_trat.group(1)) if m_trat else [])
    autores = sorted({a for a in (ids.autor_id(x) for x in autores_txt) if a})
    normas = {i: n for i, n in normas_canonicas(cuerpo)}
    for i in normas_de_lista(meta.get("normas_citadas")):
        normas.setdefault(i, 1)
    fila.update({
        "sub": "revista" if es_revista else partes[1] if len(partes) > 2 else "",
        "revista": ids.revista_id(partes[2]) if es_revista else None,
        "revista_txt": str(meta.get("revista") or ""),
        "autores": autores,
        "autores_txt": [" ".join(a.split()) for a in autores_txt],
        "anio": int(meta["anio"]) if str(meta.get("anio") or "").isdigit() else None,
        "volumen": str(meta.get("volumen") or ""),
        "numero": str(meta.get("numero") or ""),
        "paginas": str(meta.get("paginas") or ""),
        "doi": str(meta.get("doi") or ""),
        "url": str(meta.get("url_ojs") or meta.get("url_original") or meta.get("fuente") or ""),
        "cita": str(meta.get("cita_oficial") or meta.get("cita_canonica") or ""),
        "area_declarada": str(meta.get("area_derecho") or meta.get("area") or ""),
        "instituciones": sorted({" ".join(str(x).split()) for x in (meta.get("instituciones") or [])
                                 if isinstance(meta.get("instituciones"), list) and str(x).strip()}),
        "tiene_texto": not _SOLO_FICHA.search(cuerpo[:5000]) and len(cuerpo) > 3000,
        "secciones": len(re.findall(r"^##\s", cuerpo, re.MULTILINE)),
        "normas": [[i, normas[i]] for i in sorted(normas)],
        "resumen": _resumen(cuerpo, ("## Resumen", "Resumen", "## Texto del Artículo")),
    })
    roles = _citas(cuerpo)
    fila.update({k: roles[k] for k in ("cita_cs", "cita_tc", "cita_ta")})
    return _limpiar_vacios(fila)


def fila_simple(col: str, prefijo: str, raiz: str, ruta: str, datos: bytes, blob: str,
                con_citas: bool = True) -> Dict[str, Any]:
    """Guías, biblioteca y publicaciones ambientales: título + viñetas + citas del cuerpo."""
    texto = _decodificar(datos)
    meta, cuerpo = leer_front_matter(texto)
    v = leer_vinetas(texto)
    rel = ruta[len(raiz):] if ruta.startswith(raiz) else ruta
    if rel.endswith(".md"):
        rel = rel[:-3]
    titulo = " ".join(str(meta.get("titulo") or _titulo(texto) or rel).split())
    fila = _base(col, ruta, blob, len(datos), ids.id_ruta(prefijo, ruta, raiz), titulo)
    texto_util = _cuerpo_tras_cabecera(texto) or cuerpo
    fila.update({
        "tribunal": " ".join(v.get("tribunal", "").split()),
        "tipo": " ".join((v.get("tipo") or str(meta.get("tipo") or "")).split()),
        "autor": " ".join((v.get("autor") or str(meta.get("autor") or "")).split()),
        "url": v.get("documento oficial", str(meta.get("fuente") or "")),
        "resumen": _resumen(texto_util),
    })
    if con_citas:
        fila.update(_citas(texto_util))
    return _limpiar_vacios(fila)


def fila_archivo(col: str, prefijo: str, ruta: str, blob: str, n_bytes: int) -> Dict[str, Any]:
    """`data/**`, la raíz y `graphify/**`: solo inventario (no se extrae nada)."""
    nombre = ruta.rsplit("/", 1)[-1]
    return _base(col, ruta, blob, n_bytes, prefijo + ":" + re.sub(r"\s+", "_", ruta), nombre)


def extraer(ruta: str, datos: bytes, blob: str) -> Optional[Dict[str, Any]]:
    """Despacho por colección. La CS se arma desde su índice (ver `fila_cs`), no desde aquí,
    salvo las fichas que falten en el índice."""
    raiz = ruta.split("/", 1)[0]
    if raiz == "jurisprudencia_cs":
        if ruta.split("/")[1].isdigit():
            return fila_cs(registro_desde_md_cs(_decodificar(datos)), ruta, blob, len(datos))
        return fila_simple("cs_indice", "csidx", "jurisprudencia_cs/", ruta, datos, blob, con_citas=False)
    if raiz == "jurisprudencia_tc":
        return fila_tc(ruta, datos, blob)
    if raiz == "jurisprudencia_ambiental":
        if ruta.count("/") >= 2:
            return fila_ta(ruta, datos, blob)
        return fila_simple("ta_indice", "taidx", "jurisprudencia_ambiental/", ruta, datos, blob, con_citas=False)
    if raiz == "doctrina":
        return fila_doc(ruta, datos, blob)
    if raiz == "guias_academia_judicial":
        return fila_simple("guia", "guia", "guias_academia_judicial/", ruta, datos, blob)
    if raiz == "biblioteca_ambiental":
        return fila_simple("bib", "bib", "biblioteca_ambiental/", ruta, datos, blob)
    if raiz == "publicaciones_ambientales":
        return fila_simple("pub", "pub", "publicaciones_ambientales/", ruta, datos, blob)
    return None


def solo_inventario(ruta: str) -> Optional[Tuple[str, str]]:
    """(col, prefijo) de los archivos que se inventarían sin descargarse."""
    if ruta.rsplit("/", 1)[-1].lower() == "readme.md":
        return ("arch", "arch")
    if not ruta.endswith(".md") and not ruta.startswith(("data/", "graphify/")):
        return ("arch", "arch")
    if ruta.startswith("data/"):
        return ("dato", "dato")
    if ruta.startswith("graphify/"):
        return ("graphify", "graphify")
    if "/" not in ruta:
        return ("arch", "arch")
    return None
