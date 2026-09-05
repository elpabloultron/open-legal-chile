"""
Open Legal Chile — Compilador de Expedientes y Dossiers Periciales en PDF
Permite compilar escritos legales en Markdown a formato PDF judicial formal A4,
ensamblar anexos probatorios documentales y generar portadas separadoras institucionales.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import pymupdf
    from markdown_pdf import MarkdownPdf, Section
except ImportError:
    pymupdf = None
    MarkdownPdf = None


import tempfile


class LegalDossierCompiler:
    def __init__(self):
        pass

    def is_available(self) -> bool:
        """Verifica si PyMuPDF y markdown_pdf están disponibles."""
        return pymupdf is not None and MarkdownPdf is not None

    def _create_separator_page(self, title: str, subtitle: str, description: str = "") -> pymupdf.Document:
        """Genera una página A4 con diseño sobrio e institucional para separar anexos probatorios."""
        doc = pymupdf.open()
        page = doc.new_page(width=595, height=842)  # A4 estándar

        # Barra decorativa institucional
        page.draw_rect(pymupdf.Rect(50, 180, 545, 184), color=(0.1, 0.22, 0.4), fill=(0.1, 0.22, 0.4))

        # Número de Anexo (ej. "ANEXO N° 1")
        page.insert_textbox(
            pymupdf.Rect(50, 120, 545, 170),
            str(title or "ANEXO"),
            fontsize=24,
            fontname="helv",
            color=(0.06, 0.17, 0.36),
            align=pymupdf.TEXT_ALIGN_CENTER
        )

        # Subtítulo del Anexo
        page.insert_textbox(
            pymupdf.Rect(50, 210, 545, 290),
            str(subtitle or ""),
            fontsize=14,
            fontname="times-bold",
            color=(0.1, 0.1, 0.1),
            align=pymupdf.TEXT_ALIGN_CENTER
        )

        # Descripción y metadatos probatorios
        if description:
            page.insert_textbox(
                pymupdf.Rect(60, 310, 535, 550),
                str(description),
                fontsize=11,
                fontname="times-roman",
                color=(0.25, 0.25, 0.25),
                align=pymupdf.TEXT_ALIGN_CENTER
            )

        return doc

    def _img_to_pdf_doc(self, img_path: str) -> pymupdf.Document:
        """Convierte una imagen (png, jpg, jpeg) en página PDF limpia."""
        with pymupdf.open(img_path) as img_doc:
            pdf_bytes = img_doc.convert_to_pdf()
        return pymupdf.open("pdf", pdf_bytes)

    def compile(
        self,
        markdown_content: str,
        output_pdf_path: str,
        annexes: Optional[List[Dict[str, Any]]] = None,
        mobile_preview_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compila el escrito Markdown a PDF y adjunta correlativamente los anexos probatorios.
        
        Args:
            markdown_content: Texto en Markdown del escrito judicial o denuncia.
            output_pdf_path: Ruta del PDF final consolidado.
            annexes: Lista opcional de diccionarios:
                     [{"num": "ANEXO N° 1", "title": "...", "desc": "...", "path": "ruta.pdf"}, ...]
            mobile_preview_path: Ruta opcional para guardar solo el escrito principal en formato ligero.
        """
        if not self.is_available():
            return {"error": "pymupdf o markdown_pdf no están disponibles en el entorno."}

        if not output_pdf_path:
            return {"error": "Ruta de salida 'output_pdf_path' no proporcionada."}

        content = str(markdown_content or "")
        tmp_main_path = None
        final_doc = None

        try:
            # 1. Renderizar escrito principal usando archivo temporal único y seguro
            md_pdf = MarkdownPdf(toc_level=0)
            md_pdf.add_section(Section(content, toc=False, paper_size="A4", borders=(40, 40, -40, -40)))

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_f:
                tmp_main_path = tmp_f.name

            md_pdf.save(tmp_main_path)

            # Si se solicita versión ligera para móvil
            if mobile_preview_path:
                try:
                    p_movil = Path(mobile_preview_path)
                    p_movil.parent.mkdir(parents=True, exist_ok=True)
                    md_pdf.save(str(p_movil))
                except Exception:
                    pass

            final_doc = pymupdf.open(tmp_main_path)
            main_pages = len(final_doc)

            # 2. Adjuntar anexos si existen
            annexes_appended = 0
            annex_errors = []

            if annexes and isinstance(annexes, list):
                for item in annexes:
                    if not isinstance(item, dict):
                        continue
                    num = item.get("num", f"ANEXO N° {annexes_appended + 1}")
                    title = item.get("title", "Documento Anexo")
                    desc = item.get("desc", "")
                    fpath = item.get("path", "")

                    if not fpath or not os.path.exists(fpath):
                        annex_errors.append(f"Archivo no encontrado para '{title}': {fpath}")
                        continue

                    sep = None
                    anx_doc = None
                    try:
                        # Insertar separador
                        sep = self._create_separator_page(num, title, desc)
                        final_doc.insert_pdf(sep)

                        # Insertar anexo según formato
                        ext = Path(fpath).suffix.lower()
                        if ext in [".png", ".jpg", ".jpeg", ".webp"]:
                            anx_doc = self._img_to_pdf_doc(fpath)
                            final_doc.insert_pdf(anx_doc)
                        else:
                            anx_doc = pymupdf.open(fpath)
                            final_doc.insert_pdf(anx_doc)

                        annexes_appended += 1
                    except Exception as e:
                        annex_errors.append(f"Error procesando anexo '{title}': {str(e)}")
                    finally:
                        if sep:
                            sep.close()
                        if anx_doc:
                            anx_doc.close()

            out_path = Path(output_pdf_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            final_doc.save(str(out_path))

            file_size_mb = os.path.getsize(str(out_path)) / (1024 * 1024)

            res = {
                "output_pdf": str(out_path.resolve()),
                "total_pages": len(final_doc),
                "main_pages": main_pages,
                "annexes_count": annexes_appended,
                "size_mb": round(file_size_mb, 2),
                "mobile_preview_pdf": str(Path(mobile_preview_path).resolve()) if mobile_preview_path else None
            }
            if annex_errors:
                res["annex_errors"] = annex_errors
            return res

        except Exception as e:
            return {"error": f"Error al compilar expediente judicial: {str(e)}"}
        finally:
            if final_doc:
                final_doc.close()
            if tmp_main_path and os.path.exists(tmp_main_path):
                try:
                    os.unlink(tmp_main_path)
                except OSError:
                    pass


if __name__ == "__main__":
    if len(sys.argv) > 2:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            content = f.read()
        compiler = LegalDossierCompiler()
        res = compiler.compile(content, sys.argv[2])
        print(f"✓ Expediente compilado: {res}")
    else:
        print("Uso: python pdf_dossier_compiler.py <escrito.md> <salida.pdf>")
