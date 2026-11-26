"""Compilador de documentos Word (.docx) para los escritos y dossieres de la suite.

Regla de la casa: **los documentos se entregan en Word, no en PDF**, para que el abogado pueda
corregirlos. El PDF, cuando haga falta (presentación, notificación), se obtiene después desde Word
o con LibreOffice — pero el documento de trabajo es editable.

Convierte el Markdown del escrito (encabezados `#`, `##`, `###`, negritas `**…**`, viñetas)
en un .docx con tipografía forense: Times New Roman 12, cuerpo justificado, hoja A4 (u oficio).
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import functools
import io
import os
import re
from typing import Any, Dict, List, Optional

try:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt, RGBColor

    _DOCX_DISPONIBLE = True
except ImportError:
    Document = None  # type: ignore[misc,assignment]
    WD_ALIGN_PARAGRAPH = None  # type: ignore[misc,assignment]
    Cm = None  # type: ignore[misc,assignment]
    Pt = None  # type: ignore[misc,assignment]
    RGBColor = None  # type: ignore[misc,assignment]
    _DOCX_DISPONIBLE = False


@functools.lru_cache(maxsize=1)
def qr_institucional_png() -> bytes:
    """Genera y cachea en memoria los bytes PNG del código QR institucional de Open Legal Chile."""
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=3, border=1)
        qr.add_data("https://elpabloultron.github.io/open-legal-chile/")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return b""


class WordDossierCompiler:
    """Convierte el Markdown de un escrito en un .docx editable."""

    def is_available(self) -> bool:
        """True si python-docx está instalado y se puede compilar Word."""
        return _DOCX_DISPONIBLE

    def compile(self, markdown_content: str, output_docx_path: str, title: str = "",
                tamano: str = "a4") -> Dict[str, Any]:
        """Escribe `markdown_content` como documento Word en `output_docx_path`.

        `tamano`: "a4" (por defecto) u "oficio" chileno (21,59 × 33,02 cm) — nunca carta gringa.
        Todo el texto va rigurosamente justificado y formateado con tipografía institucional Open Legal Chile.
        """
        if not _DOCX_DISPONIBLE or Document is None or Pt is None or Cm is None or WD_ALIGN_PARAGRAPH is None:
            return {"ok": False, "motivo": "python-docx no está instalado"}
        documento = Document()
        self._configurar_pagina(documento, tamano)
        self._configurar_estilos(documento)
        if title:
            documento.core_properties.title = title
        documento.core_properties.author = "Open Legal Chile"
        documento.core_properties.comments = "Documento emitido por Open Legal Chile conforme a normas RAE y estándar forense chileno"
        for linea in markdown_content.split("\n"):
            self._agregar_linea(documento, linea)
        carpeta = os.path.dirname(os.path.abspath(output_docx_path))
        os.makedirs(carpeta, exist_ok=True)
        documento.save(output_docx_path)
        return {"ok": True, "ruta": output_docx_path, "caracteres": len(markdown_content)}

    @staticmethod
    def _configurar_estilos(documento: Any) -> None:
        """Configura la tipografía forense formal: Times New Roman, color negro estricto y espaciado armónico sin saltos gigantes."""
        if Pt is None or RGBColor is None or WD_ALIGN_PARAGRAPH is None:
            return
        negro = RGBColor(0, 0, 0)
        # 1. Estilo Normal
        normal: Any = documento.styles["Normal"]
        normal.font.name = "Times New Roman"
        normal.font.size = Pt(12)
        normal.font.color.rgb = negro
        normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        normal.paragraph_format.line_spacing = 1.15
        normal.paragraph_format.space_before = Pt(0)
        normal.paragraph_format.space_after = Pt(3)

        # 2. Estilos de Encabezados (elimina el azul por defecto de Word y reduce márgenes)
        for estilo_nombre, pt_sz, pt_before, pt_after in [
            ("Heading 1", 13, 6, 2),
            ("Heading 2", 12, 5, 2),
            ("Heading 3", 12, 4, 2),
            ("Title", 14, 0, 4)
        ]:
            if estilo_nombre in documento.styles:
                st = documento.styles[estilo_nombre]
                st.font.name = "Times New Roman"
                st.font.size = Pt(pt_sz)
                st.font.bold = True
                st.font.color.rgb = negro
                st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                st.paragraph_format.line_spacing = 1.15
                st.paragraph_format.space_before = Pt(pt_before)
                st.paragraph_format.space_after = Pt(pt_after)

    @staticmethod
    def _configurar_pagina(documento: Any, tamano: str) -> None:
        """Hoja forense: A4 (por defecto) u oficio chileno; con membrete, pie institucional y QR de Open Legal Chile."""
        dimensiones = {"a4": (21.0, 29.7), "oficio": (21.59, 33.02)}
        ancho_cm, alto_cm = dimensiones.get(str(tamano).strip().lower(), dimensiones["a4"])
        for seccion in documento.sections:
            seccion.page_width = Cm(ancho_cm)
            seccion.page_height = Cm(alto_cm)

            # Membrete superior institucional Open Legal Chile
            try:
                header = seccion.header
                header_p = header.paragraphs[0]
                header_p.text = "OPEN LEGAL CHILE — PLATAFORMA DE INTELIGENCIA JURÍDICA"
                header_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                if header_p.runs and Pt is not None and RGBColor is not None:
                    run = header_p.runs[0]
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(8.5)
                    run.font.italic = True
                    run.font.color.rgb = RGBColor(128, 128, 128)
            except Exception:
                pass

            # Pie de página institucional Open Legal Chile: Open Source, Autor y Código QR
            try:
                footer = seccion.footer
                footer_p = footer.paragraphs[0]
                footer_p.text = (
                    "Open Legal Chile — Un proyecto open source · Desarrollado por Pablo Benavides J. · "
                    "Web: https://elpabloultron.github.io/open-legal-chile/"
                )
                footer_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                if footer_p.runs and Pt is not None and RGBColor is not None:
                    run = footer_p.runs[0]
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(8.0)
                    run.font.italic = True
                    run.font.color.rgb = RGBColor(110, 110, 110)

                qr_bytes = qr_institucional_png()
                if qr_bytes and Cm is not None and Pt is not None:
                    qr_p = footer.add_paragraph()
                    qr_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    qr_p.paragraph_format.space_before = Pt(1)
                    qr_p.paragraph_format.space_after = Pt(0)
                    qr_run = qr_p.add_run()
                    qr_run.add_picture(io.BytesIO(qr_bytes), width=Cm(1.2), height=Cm(1.2))
            except Exception:
                pass

    @staticmethod
    def normalizar_ortotipografia_rae(texto: str) -> str:
        """Aplica normas de ortotipografía de la RAE y ASALE (Ortografía 2010).

        - Comillas latinas/españolas (« ») como comillas de primer nivel.
        - Abreviatura académica de número (N.° con punto y volada).
        - Rayas de inciso (em-dash: ' — ') en lugar de guiones dobles ' -- '.
        - Supresión de emojis, cajas ASCII y símbolos informáticos impropios de la práctica forense.
        - Normalización de importes monetarios ($ 120.000.000) sin guiones finales redundantes.
        - Normalización de espacios múltiples.
        """
        if not texto:
            return ""
        # 1. Supresión de emojis y pictogramas impropios de documentos judiciales
        res = re.sub(r'[\U00010000-\U0010ffff]|\u2696|\ufe0f|[\u2600-\u27bf]|[\u2300-\u23ff]', '', texto)
        # 2. Comillas rectas dobles a comillas latinas (« »)
        res = re.sub(r'(^|[\s\(\[\{])\"([^\"]+)\"([\s\.,;:!\?\)\-\]\}]|$)', r'\1«\2»\3', res)
        # 3. Abreviatura N° / Nº / No. a N.° según norma RAE
        res = re.sub(r'\bN°\s*(\d+)', r'N.° \1', res)
        res = re.sub(r'\bNº\s*(\d+)', r'N.° \1', res)
        # 4. Rayas de inciso (em-dash) y limpieza de guiones dobles
        res = re.sub(r'\s+--\s+', ' — ', res)
        # 5. Normalizar importes en pesos: asegurar espacio tras el signo peso y eliminar guion final '.-'
        res = re.sub(r'\$(\s*\d[\d\.]*)\.-', r'$ \1', res)
        res = re.sub(r'\$(\d)', r'$ \1', res)
        # 6. Limpieza de espacios redundantes
        res = re.sub(r'[ \t]+', ' ', res)
        return res

    # ── internos ────────────────────────────────────────────────────────────────────────────
    def _agregar_linea(self, documento: Any, linea: str) -> None:
        t = linea.rstrip()
        if not t.strip():
            return
        # Descartar líneas de marcos o tablas ASCII (como +---+ o |---|)
        if re.match(r'^[+\-| ]{4,}$', t.strip()):
            return
        despojado = self.normalizar_ortotipografia_rae(t.strip())
        if not despojado:
            return
        if despojado.startswith("### "):
            h = documento.add_heading(despojado[4:].strip(), level=2)
            h.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            for r in h.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
                r.font.bold = True
                r.font.color.rgb = RGBColor(0, 0, 0)
        elif despojado.startswith("## "):
            h = documento.add_heading(despojado[3:].strip(), level=1)
            h.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            for r in h.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
                r.font.bold = True
                r.font.color.rgb = RGBColor(0, 0, 0)
        elif despojado.startswith("# "):
            h = documento.add_heading(despojado[2:].strip(), level=0)
            h.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            for r in h.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(13)
                r.font.bold = True
                r.font.color.rgb = RGBColor(0, 0, 0)
        elif despojado in {"---", "***", "___"}:
            # Separador de capítulo: espaciado mínimo para no generar saltos o vacíos gigantescos
            p = documento.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.0
        elif despojado.startswith("> "):
            parrafo = documento.add_paragraph()
            parrafo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            parrafo.paragraph_format.left_indent = Pt(24)
            parrafo.paragraph_format.space_before = Pt(2)
            parrafo.paragraph_format.space_after = Pt(3)
            self._runs_con_formato(parrafo, despojado[2:].strip())
            for run in parrafo.runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(11)
                run.italic = True
                run.font.color.rgb = RGBColor(0, 0, 0)
        elif despojado.startswith(("- ", "* ")) and len(despojado) > 2:
            # En escritos y dictámenes forenses chilenos se suprimen viñetas de guiones o asteriscos
            # Se aplica sangría limpia y tipografía de cuerpo
            parrafo = documento.add_paragraph()
            parrafo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            parrafo.paragraph_format.left_indent = Pt(18)
            parrafo.paragraph_format.space_before = Pt(0)
            parrafo.paragraph_format.space_after = Pt(2)
            self._runs_con_formato(parrafo, despojado[2:].strip())
            for run in parrafo.runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(12)
                run.font.color.rgb = RGBColor(0, 0, 0)
        else:
            parrafo = documento.add_paragraph()
            parrafo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            parrafo.paragraph_format.space_before = Pt(0)
            parrafo.paragraph_format.space_after = Pt(3)
            self._runs_con_formato(parrafo, despojado)
            for run in parrafo.runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(12)
                run.font.color.rgb = RGBColor(0, 0, 0)

    @staticmethod
    def _runs_con_formato(parrafo: Any, texto: str) -> None:
        """Negritas e itálicas del Markdown, como runs del párrafo."""
        for parte in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", texto):
            if not parte:
                continue
            if parte.startswith("**") and parte.endswith("**") and len(parte) > 4:
                parrafo.add_run(parte[2:-2]).bold = True
            elif parte.startswith("*") and parte.endswith("*") and len(parte) > 2:
                parrafo.add_run(parte[1:-1]).italic = True
            else:
                parrafo.add_run(parte)

    def aplicar_redline(
        self,
        input_docx_path: str,
        cambios: List[Dict[str, Any]],
        output_docx_path: Optional[str] = None,
        autor: str = "Open Legal Chile",
    ) -> Dict[str, Any]:
        """Aplica control de cambios nativo OOXML (`w:del`/`w:ins`) y comentarios (`word/comments.xml`) a un `.docx`."""
        if not _DOCX_DISPONIBLE or Document is None:
            return {"ok": False, "motivo": "python-docx no está instalado"}
        ruta_in = os.path.abspath(str(input_docx_path or "").strip())
        if not input_docx_path or not os.path.exists(ruta_in):
            return {"ok": False, "error": f"Archivo .docx no encontrado: {input_docx_path}"}
        if not isinstance(cambios, list) or not cambios:
            return {"ok": False, "error": "Debe indicar una lista no vacía de cambios ({buscar, reemplazar, comentario})."}

        from docx.opc.packuri import PackURI
        from docx.opc.part import Part
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn

        documento = Document(ruta_in)
        parrafos = _iterar_parrafos_unicos(documento)
        fecha_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        autor_limpio = str(autor or "Open Legal Chile").strip() or "Open Legal Chile"

        rel_comments = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
        ct_comments = "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"
        parte_existente = None
        for rel in documento.part.rels.values():
            if rel.reltype == rel_comments:
                parte_existente = rel.target_part
                break

        max_cid = _max_xml_id(documento, qn("w:commentRangeStart"))
        if parte_existente is not None and hasattr(parte_existente, "_element"):
            max_cid = max(max_cid, _max_xml_id(parte_existente._element, qn("w:comment")))

        estado: Dict[str, Any] = {
            "next_rev_id": max(_max_xml_id(documento, qn("w:del")), _max_xml_id(documento, qn("w:ins"))) + 1,
            "next_cid": max_cid + 1,
            "comentarios": [],
        }

        aplicados = 0
        no_encontrados: List[str] = []
        for item in cambios:
            if not isinstance(item, dict):
                continue
            buscar = str(item.get("buscar") or "")
            if not buscar:
                continue
            reemplazar_raw = item.get("reemplazar")
            reemplazar = str(reemplazar_raw) if reemplazar_raw is not None else None
            comentario_raw = item.get("comentario")
            comentario = (
                self.normalizar_ortotipografia_rae(str(comentario_raw).strip())
                if comentario_raw and str(comentario_raw).strip()
                else None
            )
            hallado = False
            for p in parrafos:
                if _aplicar_cambio_en_parrafo(
                    p._p,
                    buscar=buscar,
                    reemplazar=reemplazar,
                    comentario=comentario,
                    autor=autor_limpio,
                    fecha_iso=fecha_iso,
                    estado=estado,
                ):
                    aplicados += 1
                    hallado = True
                    break
            if not hallado:
                no_encontrados.append(buscar[:120])

        comentarios_nuevos: List[tuple[int, str]] = estado["comentarios"]
        if comentarios_nuevos:
            iniciales = "".join(ch[0].upper() for ch in autor_limpio.split()[:3]) or "OLC"
            if parte_existente is not None and hasattr(parte_existente, "_element"):
                for cid, c_texto in comentarios_nuevos:
                    parte_existente._element.append(
                        _crear_comment_xml(cid, autor_limpio, fecha_iso, iniciales, c_texto)
                    )
            else:
                comments_el = OxmlElement("w:comments")
                if parte_existente is not None:
                    import defusedxml.ElementTree as DET

                    prev_root = DET.fromstring(parte_existente.blob)
                    for prev in list(prev_root):
                        c_el = OxmlElement("w:comment")
                        for attr_k, attr_v in prev.attrib.items():
                            c_el.set(attr_k, attr_v)
                        texto_prev = "".join(prev.itertext()).strip()
                        p_el = OxmlElement("w:p")
                        p_el.append(_crear_run_xml(texto_prev))
                        c_el.append(p_el)
                        comments_el.append(c_el)

                for cid, c_texto in comentarios_nuevos:
                    comments_el.append(
                        _crear_comment_xml(cid, autor_limpio, fecha_iso, iniciales, c_texto)
                    )

                blob = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + comments_el.xml).encode("utf-8")
                if parte_existente is not None:
                    parte_existente._blob = blob
                else:
                    nueva_parte = Part(PackURI("/word/comments.xml"), ct_comments, blob, documento.part.package)
                    documento.part.relate_to(nueva_parte, rel_comments)

        if output_docx_path and str(output_docx_path).strip():
            ruta_out = os.path.abspath(str(output_docx_path).strip())
        else:
            stem, ext = os.path.splitext(ruta_in)
            ruta_out = f"{stem}_redline{ext or '.docx'}"

        os.makedirs(os.path.dirname(ruta_out), exist_ok=True)
        documento.save(ruta_out)
        return {
            "ok": True,
            "ruta_entrada": ruta_in,
            "ruta_salida": ruta_out,
            "autor": autor_limpio,
            "cambios_aplicados": aplicados,
            "comentarios_insertados": len(comentarios_nuevos),
            "no_encontrados": no_encontrados,
        }


_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


def _iterar_parrafos_unicos(documento: Any) -> List[Any]:
    """Devuelve todos los párrafos del cuerpo y tablas (incluidas anidadas), sin duplicados."""
    parrafos: List[Any] = []
    vistos: set[int] = set()

    def _agregar(lista: Any) -> None:
        for p in lista:
            ident = id(p._p)
            if ident not in vistos:
                vistos.add(ident)
                parrafos.append(p)

    def _recorrer_tablas(tablas: Any) -> None:
        for t in tablas:
            for row in t.rows:
                for cell in row.cells:
                    _agregar(cell.paragraphs)
                    if cell.tables:
                        _recorrer_tablas(cell.tables)

    _agregar(documento.paragraphs)
    _recorrer_tablas(documento.tables)
    return parrafos


def _max_xml_id(raiz_o_doc: Any, tag_qn: str) -> int:
    from docx.oxml.ns import qn

    raiz = getattr(raiz_o_doc, "element", raiz_o_doc)
    attr_id = qn("w:id")
    maximo = 0
    for el in raiz.iter(tag_qn):
        raw = el.get(attr_id)
        if raw and str(raw).isdigit():
            maximo = max(maximo, int(raw))
    return maximo


def _crear_comment_xml(cid: int, autor: str, fecha_iso: str, iniciales: str, texto: str) -> Any:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    c_el = OxmlElement("w:comment")
    c_el.set(qn("w:id"), str(cid))
    c_el.set(qn("w:author"), autor)
    c_el.set(qn("w:date"), fecha_iso)
    c_el.set(qn("w:initials"), iniciales)
    p_el = OxmlElement("w:p")
    p_el.append(_crear_run_xml(texto))
    c_el.append(p_el)
    return c_el


def _crear_run_xml(texto: str, rpr: Optional[Any] = None, eliminado: bool = False) -> Any:
    from docx.oxml import OxmlElement

    run_el = OxmlElement("w:r")
    if rpr is not None:
        run_el.append(copy.deepcopy(rpr))
    t_el = OxmlElement("w:delText" if eliminado else "w:t")
    t_el.set(_XML_SPACE, "preserve")
    t_el.text = texto
    run_el.append(t_el)
    return run_el


def _aplicar_cambio_en_parrafo(
    p_el: Any,
    buscar: str,
    reemplazar: Optional[str],
    comentario: Optional[str],
    autor: str,
    fecha_iso: str,
    estado: Dict[str, Any],
) -> bool:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    r_tag = f"{{{_W_NS}}}r"
    t_tag = f"{{{_W_NS}}}t"
    rpr_tag = f"{{{_W_NS}}}rPr"

    runs: List[tuple[Any, str, int, int, Any]] = []
    pos = 0
    for child in list(p_el):
        if child.tag != r_tag:
            continue
        t_els = child.findall(t_tag)
        if not t_els:
            continue
        txt = "".join(t.text or "" for t in t_els)
        if not txt:
            continue
        runs.append((child, txt, pos, pos + len(txt), child.find(rpr_tag)))
        pos += len(txt)

    if not runs:
        return False

    completo = "".join(r[1] for r in runs)
    idx = completo.find(buscar)
    if idx < 0:
        return False
    end_idx = idx + len(buscar)

    spanned = [r for r in runs if r[3] > idx and r[2] < end_idx]
    if not spanned:
        return False

    anchor_idx = list(p_el).index(spanned[0][0])
    prefix = spanned[0][1][: idx - spanned[0][2]]
    suffix = spanned[-1][1][end_idx - spanned[-1][2] :]
    rpr_ini = spanned[0][4]
    rpr_fin = spanned[-1][4]

    for r_el, _, _, _, _ in spanned:
        p_el.remove(r_el)

    nuevos: List[Any] = []
    if prefix:
        nuevos.append(_crear_run_xml(prefix, rpr_ini))

    cid: Optional[int] = None
    if comentario:
        cid = int(estado["next_cid"])
        estado["next_cid"] = cid + 1
        c_start = OxmlElement("w:commentRangeStart")
        c_start.set(qn("w:id"), str(cid))
        nuevos.append(c_start)

    if reemplazar is not None and reemplazar != buscar:
        del_id = int(estado["next_rev_id"])
        estado["next_rev_id"] = del_id + 1
        w_del = OxmlElement("w:del")
        w_del.set(qn("w:id"), str(del_id))
        w_del.set(qn("w:author"), autor)
        w_del.set(qn("w:date"), fecha_iso)
        w_del.append(_crear_run_xml(buscar, rpr_ini, eliminado=True))
        nuevos.append(w_del)

        if reemplazar != "":
            ins_id = int(estado["next_rev_id"])
            estado["next_rev_id"] = ins_id + 1
            w_ins = OxmlElement("w:ins")
            w_ins.set(qn("w:id"), str(ins_id))
            w_ins.set(qn("w:author"), autor)
            w_ins.set(qn("w:date"), fecha_iso)
            w_ins.append(_crear_run_xml(reemplazar, rpr_ini, eliminado=False))
            nuevos.append(w_ins)
    else:
        nuevos.append(_crear_run_xml(buscar, rpr_ini))

    if cid is not None and comentario:
        c_end = OxmlElement("w:commentRangeEnd")
        c_end.set(qn("w:id"), str(cid))
        nuevos.append(c_end)
        c_ref_r = OxmlElement("w:r")
        c_ref = OxmlElement("w:commentReference")
        c_ref.set(qn("w:id"), str(cid))
        c_ref_r.append(c_ref)
        nuevos.append(c_ref_r)
        estado["comentarios"].append((cid, comentario))

    if suffix:
        nuevos.append(_crear_run_xml(suffix, rpr_fin))

    for offset, nodo in enumerate(nuevos):
        p_el.insert(anchor_idx + offset, nodo)
    return True
