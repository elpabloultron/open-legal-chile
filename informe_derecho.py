"""Informe en Derecho: hechos + análisis + triple pilar + transcripción literal de cada norma.

Regla del producto (AGENTS.md §2 y §2 ter): un informe describe los hechos del caso, desarrolla el
análisis jurídico (subsunción), cita la ley con su texto literal transcrito íntegro en el cuerpo, la
doctrina y la jurisprudencia aplicables —buscadas solas en el material local cuando no se las
entregan— y cierra con el dictamen y las fuentes numeradas. Se entrega en Word (.docx editable),
más HTML/MD/TXT/JSON — nunca PDF como entregable de trabajo.
"""
from __future__ import annotations

import html
import json
import os
import re
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional

from citas_legales import bloque_fuentes, detectar_normas
from exporters import EXPORTS_DIR

ESTRUCTURA = ["I. Cuestión jurídica planteada", "II. Los hechos", "III. Marco normativo vigente",
              "IV. Análisis jurídico", "V. Doctrina", "VI. Jurisprudencia", "VII. Dictamen", "Fuentes"]
_MIN_HECHOS = 120     # bajo esto los hechos son un placeholder: se rechaza
_MIN_ANALISIS = 200   # bajo esto el «análisis» es un relleno: se rechaza
_MIN_INFORME = 8000   # un informe breve no es informe: se advierte para que se desarrolle
_TOPE_TEXTO = 8000    # una ley entera no cabe en el cuerpo; los artículos sí entran completos
_MAX_DOCTRINA = 5


def _textos_de_normas(referencias: List[str]) -> Dict[str, Any]:
    """El texto literal COMPLETO de cada norma (sin el recorte de 1200 de la conversación)."""
    from servidor import corpus as _corpus

    _corpus._refrescar()  # inyecta los globales del servidor (clientes y helpers) como en el despacho
    return _corpus._citas_por_lote(list(referencias), limite=None)


def _limpiar(texto: Any) -> str:
    """Espacios colapsados: los extractos vienen con saltos y sangrías del PDF original."""
    return re.sub(r"\s+", " ", str(texto or "")).strip()


_TERMINOS_GENERICOS = {"procedente", "cautelares", "cautelar", "medida", "medidas", "recurso", "recursos",
                       "sentencia", "sentencias", "denuncia", "denunciar", "presente", "solicita", "objeto",
                       "respecto", "efectos", "mediante", "acuerdo", "conforme", "puede", "debe", "tiene"}


def _sin_acentos(texto: str) -> str:
    """Sin tildes: «adopción» calza con «adopcion»."""
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _calza_doctrina(entrada: Dict[str, Any], claves: List[str]) -> bool:
    """El calce mínimo de una entrada canónica: dos términos del objeto, o uno bien específico.

    «procedente» o «cautelares» aparecen en cualquier repertorio: con una sola coincidencia
    así, la sección se llenaba de doctrina penal o de familia en un informe ambiental.
    """
    texto = _sin_acentos(_limpiar(entrada.get("texto")).lower())
    hallados = [t for t in claves if _sin_acentos(t) in texto]
    return len(hallados) >= 2 or any(len(t) >= 9 for t in hallados)


def _doctrina_para(termino: str, limite: int = _MAX_DOCTRINA) -> List[Dict[str, Any]]:
    """Doctrina canónica del FTS5 local para el término dado (best-effort: si falla, vacío).

    Una entrada sin texto utilizable no es citable: se salta (el snippet reemplaza a la definición
    cuando esta viene vacía).
    """
    if not termino.strip():
        return []
    try:
        from doctrina_connector import search_doctrina

        salida: List[Dict[str, Any]] = []
        for d in search_doctrina(termino, limit=limite):
            texto = _limpiar(d.get("definicion")) or _limpiar(re.sub(r"[【】]", "", str(d.get("snippet") or "")))
            if len(texto) < 60:
                continue
            salida.append({"obra": d.get("obra") or "", "autor": d.get("autor") or "",
                           "institucion": d.get("institucion") or "", "texto": texto})
        return salida
    except Exception:  # noqa: BLE001 — sin doctrina se declara, no se inventa
        return []


def _fallos_rectores(consulta: str, limite: int) -> List[Dict[str, Any]]:
    """Los fallos rectores CS/TC del índice local, con la forma de los resultados ambientales."""
    from pjud_connector import PJUDClient

    resultados: List[Dict[str, Any]] = []
    for r in PJUDClient().search_jurisprudencia(consulta, limit=limite):
        if r.get("error") or not _limpiar(r.get("doctrina")):
            continue
        prefijo = "TC" if "Constitucional" in str(r.get("tribunal") or "") else "CS"
        fecha = str(r.get("fecha") or "").strip()
        cita = f"[{prefijo} - {r.get('rol', '')}" + (f", {fecha}" if fecha else "") + "]"
        if r.get("caratula"):
            cita += f" {r['caratula']}"
        resultados.append({"coleccion": "fallos_rectores", "titulo": r.get("caratula") or r.get("materia") or "",
                           "tipo": r.get("materia") or "", "fragmento": _limpiar(r.get("doctrina")),
                           "cita": cita, "enlace": r.get("link") or ""})
    return resultados


def _material_local(consulta: str, limite: int = 8) -> Dict[str, List[Dict[str, Any]]]:
    """Jurisprudencia y doctrina del material local del producto (best-effort, nada inventado).

    Materia ambiental: las 886 sentencias de los Tribunales Ambientales y la biblioteca ambiental
    (informes en derecho, foros, manuales) vía el módulo especial. Otras materias: los fallos
    rectores CS/TC indexados en `jurisprudencia_judicial.db`.
    """
    consulta = (consulta or "").strip()
    if not consulta:
        return {"jurisprudencia": [], "doctrina": []}
    try:
        from modulo_ambiental import consulta_ambiental, es_materia_ambiental

        if es_materia_ambiental(consulta):
            paquete = consulta_ambiental(consulta, limite=max(4, limite))
        else:
            paquete = {"resultados": _fallos_rectores(consulta, limite)}
    except Exception:  # noqa: BLE001 — sin material se declara, no se inventa
        return {"jurisprudencia": [], "doctrina": []}

    jurisprudencia: List[Dict[str, Any]] = []
    doctrina: List[Dict[str, Any]] = []
    for r in paquete.get("resultados") or []:
        texto = _limpiar(r.get("fragmento"))
        cita = str(r.get("cita") or "").strip()
        if not texto or not cita:
            continue
        if r.get("coleccion") in ("jurisprudencia_ambiental", "fallos_rectores"):
            jurisprudencia.append({"cita": cita, "texto": texto, "url": r.get("enlace") or ""})
        else:
            doctrina.append({"cita": cita, "texto": texto, "url": r.get("enlace") or "",
                             "obra": r.get("titulo") or "", "autor": "",
                             "institucion": r.get("tipo") or "biblioteca"})
    return {"jurisprudencia": jurisprudencia, "doctrina": doctrina}


def _normas_del_caso(objeto: str, hechos: str, derecho: str, normas: List[str]) -> List[str]:
    """Las normas a transcribir: las pedidas explícitas + las detectadas en los textos."""
    referencias: List[str] = [str(n).strip() for n in (normas or []) if str(n).strip()]
    for trozo in (objeto, hechos, derecho):
        for norma in detectar_normas(trozo or ""):
            etiqueta = norma.get("etiqueta") or ""
            if etiqueta and etiqueta not in referencias:
                referencias.append(etiqueta)
    return referencias


def _numerar_hechos(hechos: Any) -> List[str]:
    """Los hechos como lista numerable: acepta lista o texto de varios párrafos/líneas."""
    if isinstance(hechos, list):
        return [str(h).strip() for h in hechos if str(h).strip()]
    bruto = str(hechos or "")
    items = [p.strip() for p in bruto.split("\n\n") if p.strip()]
    if len(items) <= 1:
        items = [p.strip() for p in bruto.split("\n") if p.strip()]
    return items


def _cita_doctrina(entrada: Dict[str, Any]) -> str:
    """El corchete de la doctrina: el propio ([Hugging Face - …]) o [Doctrina - Autor, Obra, Institución: X]."""
    if str(entrada.get("cita") or "").strip():
        return str(entrada["cita"]).strip()
    etiqueta = ", ".join(p for p in (entrada.get("autor") or "", entrada.get("obra") or "") if p)
    if entrada.get("institucion"):
        etiqueta += f", Institución: {entrada['institucion']}"
    return f"[Doctrina - {etiqueta}]"


def exportar_informe_en_derecho(
    objeto: str,
    hechos: Any,
    analisis: Any = "",
    dictamen: str = "",
    materia: str = "",
    caso: str = "",
    derecho: str = "",
    normas: Optional[List[str]] = None,
    doctrina: Optional[List[Dict[str, Any]]] = None,
    jurisprudencia: Optional[List[Dict[str, Any]]] = None,
    filename_base: Optional[str] = None,
) -> Dict[str, Any]:
    """Arma el informe en derecho completo (extenso) y lo entrega en Word + HTML/MD/TXT/JSON."""
    objeto = (objeto or "").strip()
    dictamen = (dictamen or "").strip()
    if isinstance(analisis, list):
        analisis = "\n\n".join(str(p).strip() for p in analisis if str(p).strip())
    analisis = str(analisis or "").strip()
    items_hechos = _numerar_hechos(hechos)
    texto_hechos = " ".join(items_hechos)

    if len(objeto) < 20:
        return {"error": "Falta la cuestión jurídica ('objeto', mínimo 20 caracteres): un informe "
                         "en derecho parte planteando el problema jurídico."}
    if len(texto_hechos) < _MIN_HECHOS:
        return {"error": "Los hechos del caso llegan vacíos o de mentira: descríbalos con fechas, "
                         "conductas y circunstancias. Sin hechos no hay informe en derecho."}
    if len(analisis) < _MIN_ANALISIS:
        return {"error": "Falta el análisis jurídico ('analisis'): es el cuerpo del informe — la "
                         "subsunción de los hechos en las normas, con doctrina y jurisprudencia, y los "
                         "contraargumentos. Un informe sin análisis sale breve y no sirve."}
    if not dictamen:
        return {"error": "Falta el dictamen (la conclusión del informe; 'peticiones' sirve de respaldo)."}

    advertencias: List[str] = []
    faltantes: List[str] = []
    if len(texto_hechos) < 600:
        advertencias.append(f"La descripción de hechos es escueta ({len(texto_hechos)} caracteres): "
                            "se recomienda desarrollarla con fechas y circunstancias.")
    if len(analisis) < 800:
        advertencias.append(f"El análisis jurídico es escueto ({len(analisis)} caracteres): "
                            "se recomienda desarrollar la subsunción y los contraargumentos.")

    # III. Normas: transcripción literal + cita (regla: no se cita sin texto)
    referencias = _normas_del_caso(objeto, texto_hechos, derecho, list(normas or []))
    lote = _textos_de_normas(referencias) if referencias else {"citas": [], "faltantes": []}
    citas_normas = list(lote.get("citas") or [])
    faltantes.extend(lote.get("faltantes") or [])
    for cita in citas_normas:
        if len(cita.get("texto") or "") > _TOPE_TEXTO:
            cita["texto"] = cita["texto"][:_TOPE_TEXTO].rstrip() + "…"
            advertencias.append(f"Se recorta {cita['formato']} a {_TOPE_TEXTO} caracteres "
                                "(texto mayor que un artículo: se transcribe lo esencial y el enlace).")

    # V y VI · Doctrina y jurisprudencia: las entregadas o, si no, el material local del producto
    entradas_doctrina = [d for d in (doctrina or []) if _limpiar(d.get("texto"))]
    entradas_juris = [j for j in (jurisprudencia or []) if _limpiar(j.get("texto"))]
    material: Dict[str, List[Dict[str, Any]]] = {"jurisprudencia": [], "doctrina": []}
    if not entradas_doctrina or not entradas_juris:
        material = _material_local(f"{objeto} {texto_hechos[:200]}".strip())

    if not entradas_juris:
        entradas_juris = list(material["jurisprudencia"])[:4]
        if entradas_juris:
            advertencias.append("La jurisprudencia se buscó automáticamente en el material local "
                                "(sentencias de los Tribunales Ambientales y fallos rectores CS/TC).")
    if not entradas_juris:
        faltantes.append("jurisprudencia")
        advertencias.append("Sin jurisprudencia: el material local no registró fallos aplicables; "
                            "búsquela por organismo (pjud_search_jurisprudencia, ambiental_buscar_jurisprudencia, "
                            "cgr_search_jurisprudencia…) y vuelva a generar el informe.")

    if not entradas_doctrina:
        # La biblioteca del caso manda; el corpus canónico (FTS) entra solo si calza de verdad.
        claves = [t for t in re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ-]{6,}", objeto.lower())
                  if t not in _TERMINOS_GENERICOS]
        entradas_doctrina = [d for d in material["doctrina"][:3] if _limpiar(d.get("texto"))]
        for d in _doctrina_para(objeto[:120] or materia):
            if not _limpiar(d.get("texto")):
                continue
            if not claves or _calza_doctrina(d, claves):
                entradas_doctrina.append(d)
        entradas_doctrina = entradas_doctrina[:_MAX_DOCTRINA]
        if entradas_doctrina:
            advertencias.append("La doctrina se buscó automáticamente (biblioteca ambiental y corpus canónico).")
        else:
            faltantes.append("doctrina")

    # ── Cuerpo del documento ────────────────────────────────────────────────────────────────
    lineas: List[str] = ["# INFORME EN DERECHO", ""]
    if materia:
        lineas.append(f"**Materia:** {materia}")
    if caso:
        lineas.append(f"**Caso:** {caso}")
    lineas += [f"**Fecha:** {datetime.now().strftime('%d-%m-%Y')}", "", "---", ""]

    lineas += ["## I. Cuestión jurídica planteada", "", objeto, ""]

    lineas += ["## II. Los hechos", ""]
    for i, hecho in enumerate(items_hechos, 1):
        lineas += [f"{i}. {hecho}", ""]

    lineas += ["## III. Marco normativo vigente", ""]
    if citas_normas:
        for cita in citas_normas:
            lineas += [f"**{cita['formato']}**", "", f"> «{cita['texto'].strip()}»", "",
                       f"Cita: {cita['cita_completa']}", ""]
    else:
        lineas += ["_No se detectaron normas citables en el caso (sin fuente verificable)._", ""]
    normas_faltantes = [f for f in faltantes if f not in ("doctrina", "jurisprudencia")]
    if normas_faltantes:
        lineas += ["### Normas que no se pudieron transcribir", ""]
        for f in normas_faltantes:
            lineas += [f"- {f}: sin fuente verificable (no se cita a ciegas).", ""]

    lineas += ["## IV. Análisis jurídico", ""]
    for parrafo in [p.strip() for p in analisis.split("\n\n") if p.strip()]:
        lineas += [parrafo, ""]

    lineas += ["## V. Doctrina", ""]
    if entradas_doctrina:
        for d in entradas_doctrina:
            lineas += [f"**{_cita_doctrina(d)}**", "", f"> «{str(d.get('texto')).strip()}»", ""]
    else:
        lineas += ["_Sin fuente verificable en el corpus para este término._", ""]

    lineas += ["## VI. Jurisprudencia", ""]
    if entradas_juris:
        for j in entradas_juris:
            lineas += [f"**{j.get('cita') or '[Fuente sin identificar]'}**", "",
                       f"> «{str(j.get('texto')).strip()}»", ""]
    else:
        lineas += ["_No se citó jurisprudencia ni dictamen administrativo (ver advertencias)._", ""]

    lineas += ["## VII. Dictamen", "", dictamen, ""]

    citas_fuentes = list(citas_normas)
    for d in entradas_doctrina:
        citas_fuentes.append({"formato": _cita_doctrina(d), "url": d.get("url", "")})
    for j in entradas_juris:
        citas_fuentes.append({"formato": j.get("cita") or "", "url": j.get("url", "")})
    lineas += [bloque_fuentes(citas_fuentes), "", "---", "",
               "⚖️ **Compuerta de Revisión Jurídica:** Este informe contiene análisis y propuesta "
               "de redacción conforme al ordenamiento jurídico de Chile. Debe ser validado por un "
               "abogado habilitado antes de su firma o presentación."]
    md_content = "\n".join(lineas)
    if len(md_content) < _MIN_INFORME:
        advertencias.append(f"El informe mide {len(md_content)} caracteres: los informes en derecho "
                            "son extensos — desarrolle los hechos y el análisis antes de firmarlo.")

    # ── Salidas: Word (entregable) + HTML/MD/TXT/JSON (misma carpeta que los escritos) ──────
    filename = filename_base or f"informe_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    rutas = {ext: os.path.join(EXPORTS_DIR, f"{filename}.{ext}")
             for ext in ("md", "html", "txt", "json", "docx")}
    with open(rutas["md"], "w", encoding="utf-8") as archivo:
        archivo.write(md_content)
    with open(rutas["txt"], "w", encoding="utf-8") as archivo:
        archivo.write(md_content)
    with open(rutas["html"], "w", encoding="utf-8") as archivo:
        archivo.write(_html_del_informe(md_content))
    with open(rutas["json"], "w", encoding="utf-8") as archivo:
        json.dump({"fecha_generacion": datetime.now().isoformat(timespec="seconds"),
                   "tipo": "informe_en_derecho", "estructura": ESTRUCTURA, "materia": materia,
                   "caso": caso, "objeto": objeto, "hechos": items_hechos, "analisis": analisis,
                   "normas": [{"cita": c["formato"], "texto": c["texto"], "url": c["url"]}
                              for c in citas_normas],
                   "doctrina": entradas_doctrina, "jurisprudencia": entradas_juris,
                   "dictamen": dictamen, "faltantes": faltantes, "advertencias": advertencias},
                  archivo, ensure_ascii=False, indent=2)

    from docx_compiler import WordDossierCompiler

    compilado = WordDossierCompiler().compile(md_content, rutas["docx"], title="INFORME EN DERECHO")

    return {
        "tipo": "informe", "entregable": "word", "estructura": ESTRUCTURA,
        "archivos": {"filename": filename, "markdownPath": rutas["md"], "htmlPath": rutas["html"],
                     "textPath": rutas["txt"], "jsonPath": rutas["json"],
                     "docxPath": rutas["docx"] if compilado.get("ok") else "", "exportsDir": EXPORTS_DIR},
        "citas": citas_fuentes, "faltantes": faltantes, "advertencias": advertencias,
    }


def _html_del_informe(md_content: str) -> str:
    """HTML simple y legible del informe (el entregable de trabajo es el .docx)."""
    cuerpo: List[str] = []
    for linea in md_content.split("\n"):
        t = linea.strip().replace("**", "")
        if not t:
            continue
        if t.startswith("## "):
            cuerpo.append(f"<h2>{html.escape(t[3:])}</h2>")
        elif t.startswith("# "):
            cuerpo.append(f"<h1>{html.escape(t[2:])}</h1>")
        elif t.startswith("> "):
            cuerpo.append(f"<blockquote>{html.escape(t[2:])}</blockquote>")
        elif t == "---":
            cuerpo.append("<hr>")
        else:
            cuerpo.append(f"<p>{html.escape(t)}</p>")
    return ("<!DOCTYPE html>\n<html lang=\"es\">\n<head><meta charset=\"UTF-8\">"
            "<title>Informe en Derecho — Open Legal Chile</title>\n"
            "<style>body{font-family:'Times New Roman',serif;max-width:820px;margin:40px auto;"
            "padding:30px;line-height:1.4;}blockquote{margin-left:24px;padding-left:14px;"
            "border-left:3px solid #999;font-style:italic;}p{text-align:justify;}</style>"
            "</head>\n<body>\n" + "\n".join(cuerpo) + "\n</body>\n</html>\n")
