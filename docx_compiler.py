"""Compilador de documentos Word (.docx) para los escritos y dossieres de la suite.

Regla de la casa: **los documentos se entregan en Word, no en PDF**, para que el abogado pueda
corregirlos. El PDF, cuando haga falta (presentación, notificación), se obtiene después desde Word
o con LibreOffice — pero el documento de trabajo es editable.

Convierte el Markdown del escrito (encabezados `#`, `##`, `###`, negritas `**…**`, viñetas)
en un .docx con tipografía forense: Times New Roman 12, cuerpo justificado, hoja A4 (u oficio).
"""
from __future__ import annotations

import os
import re
import tempfile
from typing import Any, Dict, Optional

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

    @classmethod
    def _configurar_estilos(cls, documento: Any) -> None:
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

    @classmethod
    def _generar_qr_institucional(cls) -> Optional[str]:
        """Genera un archivo PNG temporal con el código QR institucional de Open Legal Chile."""
        try:
            import qrcode
            qr = qrcode.QRCode(version=1, box_size=3, border=1)
            qr.add_data("https://elpabloultron.github.io/open-legal-chile/")
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            tmp_qr = os.path.join(tempfile.gettempdir(), "openlegal_qr.png")
            img.save(tmp_qr)
            return tmp_qr
        except Exception:
            return None

    @classmethod
    def _configurar_pagina(cls, documento: Any, tamano: str) -> None:
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

                tmp_qr = cls._generar_qr_institucional()
                if tmp_qr and os.path.exists(tmp_qr) and Cm is not None and Pt is not None:
                    qr_p = footer.add_paragraph()
                    qr_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    qr_p.paragraph_format.space_before = Pt(1)
                    qr_p.paragraph_format.space_after = Pt(0)
                    qr_run = qr_p.add_run()
                    qr_run.add_picture(tmp_qr, width=Cm(1.2), height=Cm(1.2))
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
