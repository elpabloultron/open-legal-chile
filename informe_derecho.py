"""Informe en Derecho: hechos del caso + triple pilar + transcripción literal de cada norma.

Regla del producto (AGENTS.md §2 y §2 ter): un informe describe los hechos del caso, cita la ley
con su texto literal transcrito íntegro en el cuerpo, la doctrina y la jurisprudencia aplicables,
y cierra con el dictamen y las fuentes numeradas. Este módulo arma ese documento y lo entrega en
Word (.docx editable), más HTML/MD/TXT/JSON — nunca PDF como entregable de trabajo.
"""
from __future__ import annotations

import html
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from citas_legales import bloque_fuentes, detectar_normas
from exporters import EXPORTS_DIR

ESTRUCTURA = ["I. Cuestión jurídica planteada", "II. Los hechos", "III. Marco normativo vigente",
              "IV. Doctrina", "V. Jurisprudencia", "VI. Dictamen", "Fuentes"]
_MIN_HECHOS = 120  # bajo esto los hechos son un placeholder: se rechaza
_TOPE_TEXTO = 8000  # una ley entera no cabe en el cuerpo; los artículos sí entran completos


def _textos_de_normas(referencias: List[str]) -> Dict[str, Any]:
    """El texto literal COMPLETO de cada norma (sin el recorte de 1200 de la conversación)."""
    from servidor import corpus as _corpus

    _corpus._refrescar()  # inyecta los globales del servidor (clientes y helpers) como en el despacho
    return _corpus._citas_por_lote(list(referencias), limite=None)


def _doctrina_para(termino: str, limite: int = 3) -> List[Dict[str, Any]]:
    """Doctrina canónica del FTS5 local para el término dado (best-effort: si falla, vacío)."""
    if not termino.strip():
        return []
    try:
        from doctrina_connector import search_doctrina

        return [{"obra": d.get("obra") or "", "autor": d.get("autor") or "",
                 "institucion": d.get("institucion") or "", "texto": d.get("definicion") or ""}
                for d in search_doctrina(termino, limit=limite)]
    except Exception:  # noqa: BLE001 — sin doctrina se declara, no se inventa
        return []


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
    """Corchete oficial de doctrina: [Doctrina - Autor, Obra, Institución: X]."""
    etiqueta = ", ".join(p for p in (entrada.get("autor") or "", entrada.get("obra") or "") if p)
    if entrada.get("institucion"):
        etiqueta += f", Institución: {entrada['institucion']}"
    return f"[Doctrina - {etiqueta}]"


def exportar_informe_en_derecho(
    objeto: str,
    hechos: Any,
    dictamen: str,
    materia: str = "",
    caso: str = "",
    derecho: str = "",
    normas: Optional[List[str]] = None,
    doctrina: Optional[List[Dict[str, Any]]] = None,
    jurisprudencia: Optional[List[Dict[str, Any]]] = None,
    filename_base: Optional[str] = None,
) -> Dict[str, Any]:
    """Arma el informe en derecho completo y lo entrega en Word + HTML/MD/TXT/JSON."""
    objeto = (objeto or "").strip()
    dictamen = (dictamen or "").strip()
    items_hechos = _numerar_hechos(hechos)
    texto_hechos = " ".join(items_hechos)

    if len(objeto) < 20:
        return {"error": "Falta la cuestión jurídica ('objeto', mínimo 20 caracteres): un informe "
                         "en derecho parte planteando el problema jurídico."}
    if len(texto_hechos) < _MIN_HECHOS:
        return {"error": "Los hechos del caso llegan vacíos o de mentira: descríbalos con fechas, "
                         "conductas y circunstancias. Sin hechos no hay informe en derecho."}
    if not dictamen:
        return {"error": "Falta el dictamen (la conclusión del informe; 'peticiones' sirve de respaldo)."}

    advertencias: List[str] = []
    if len(texto_hechos) < 400:
        advertencias.append(f"La descripción de hechos es escueta ({len(texto_hechos)} caracteres): "
                            "se recomienda desarrollarla con fechas y circunstancias.")

    # III. Normas: transcripción literal + cita (regla: no se cita sin texto)
    referencias = _normas_del_caso(objeto, texto_hechos, derecho, list(normas or []))
    lote = _textos_de_normas(referencias) if referencias else {"citas": [], "faltantes": []}
    citas_normas = list(lote.get("citas") or [])
    faltantes: List[str] = list(lote.get("faltantes") or [])
    for cita in citas_normas:
        if len(cita.get("texto") or "") > _TOPE_TEXTO:
            cita["texto"] = cita["texto"][:_TOPE_TEXTO].rstrip() + "…"
            advertencias.append(f"Se recorta {cita['formato']} a {_TOPE_TEXTO} caracteres "
                                "(texto mayor que un artículo: se transcribe lo esencial y el enlace).")

    # IV. Doctrina: la pedida o, por defecto, el FTS5 canónico
    entradas_doctrina = [d for d in (doctrina or []) if str(d.get("texto") or "").strip()]
    if not entradas_doctrina:
        entradas_doctrina = _doctrina_para(objeto[:120] or materia)
        if entradas_doctrina:
            advertencias.append("La doctrina se buscó automáticamente en el corpus canónico (FTS5).")
        else:
            faltantes.append("doctrina")

    # V. Jurisprudencia: la pedida; si no hay, se declara (se busca por organismo)
    entradas_juris = [j for j in (jurisprudencia or []) if str(j.get("texto") or "").strip()]
    if not entradas_juris:
        faltantes.append("jurisprudencia")
        advertencias.append("Sin jurisprudencia citada: búsquela por organismo "
                            "(pjud_search_jurisprudencia, sma_search_sancionatorios, "
                            "cgr_search_jurisprudencia…) y vuelva a generar el informe.")

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

    lineas += ["## IV. Doctrina", ""]
    if entradas_doctrina:
        for d in entradas_doctrina:
            lineas += [f"**{_cita_doctrina(d)}**", "", f"> «{str(d.get('texto')).strip()}»", ""]
    else:
        lineas += ["_Sin fuente verificable en el corpus para este término._", ""]

    lineas += ["## V. Jurisprudencia", ""]
    if entradas_juris:
        for j in entradas_juris:
            lineas += [f"**{j.get('cita') or '[Fuente sin identificar]'}**", "",
                       f"> «{str(j.get('texto')).strip()}»", ""]
    else:
        lineas += ["_No se citó jurisprudencia ni dictamen administrativo (ver advertencias)._", ""]

    lineas += ["## VI. Dictamen", "", dictamen, ""]

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
                   "caso": caso, "objeto": objeto, "hechos": items_hechos,
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
