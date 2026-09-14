"""
Open Legal Chile — Compilador de Expedientes y Dossiers Periciales en PDF
Permite compilar escritos legales en Markdown a formato PDF judicial formal A4,
ensamblar anexos probatorios documentales con carátulas divisorias elegantes
y generar marcadores jerárquicos nativos (TOC Bookmarks) para la Oficina Judicial Virtual (OJV).
"""

from __future__ import annotations

import os
import sys
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import pymupdf
except ImportError:
    pymupdf = None  # type: ignore[assignment]

try:
    from markdown_pdf import MarkdownPdf, Section
except ImportError:
    MarkdownPdf = None  # type: ignore[misc,assignment]
    Section = None  # type: ignore[misc,assignment]


class LegalDossierCompiler:
    """Compila escritos judiciales y ensambla expedientes consolidados con marcadores TOC y carátulas divisorias."""

    def __init__(self):
        pass

    def is_available(self) -> bool:
        """Verifica si PyMuPDF y markdown_pdf están disponibles."""
        return pymupdf is not None and MarkdownPdf is not None

    def _create_separator_page(self, title: str, subtitle: str, description: str = "") -> Any:
        """
        Genera una página A4 con diseño sobrio e institucional para separar anexos probatorios,
        con marco gris/sobrio de doble filete conforme a los estándares de la Corte de Apelaciones y OJV.
        """
        doc = pymupdf.open()
        page = doc.new_page(width=595, height=842)  # A4 estándar

        # Marco exterior e interior elegante (gris sobrio / institucional)
        page.draw_rect(pymupdf.Rect(36, 36, 559, 806), color=(0.55, 0.58, 0.62), width=1.2)
        page.draw_rect(pymupdf.Rect(42, 42, 553, 800), color=(0.78, 0.81, 0.84), width=0.6)

        # Encabezado institucional superior
        page.insert_textbox(
            pymupdf.Rect(50, 65, 545, 110),
            "ILUSTRÍSIMA CORTE DE APELACIONES\nEXPEDIENTE JUDICIAL DIGITAL · LEY N.° 20.886",
            fontsize=9.5,
            fontname="helv",
            color=(0.35, 0.38, 0.42),
            align=pymupdf.TEXT_ALIGN_CENTER
        )

        page.draw_line(pymupdf.Point(70, 115), pymupdf.Point(525, 115), color=(0.75, 0.78, 0.82), width=0.8)

        # Identificador del Anexo (ej. «ANEXO N.° 1»)
        anexo_label = str(title or "ANEXO").strip()
        if not anexo_label.startswith("«") and not anexo_label.endswith("»"):
            anexo_label = f"«{anexo_label}»"

        page.insert_textbox(
            pymupdf.Rect(60, 220, 535, 275),
            anexo_label,
            fontsize=24,
            fontname="times-bold",
            color=(0.1, 0.15, 0.22),
            align=pymupdf.TEXT_ALIGN_CENTER
        )

        page.draw_line(pymupdf.Point(180, 285), pymupdf.Point(415, 285), color=(0.1, 0.15, 0.22), width=1.5)

        # Subtítulo o nombre formal del Documento
        if subtitle:
            page.insert_textbox(
                pymupdf.Rect(60, 310, 535, 380),
                str(subtitle).upper(),
                fontsize=14,
                fontname="times-bold",
                color=(0.1, 0.1, 0.1),
                align=pymupdf.TEXT_ALIGN_CENTER
            )

        # Descripción probatoria y alcance legal
        if description:
            page.insert_textbox(
                pymupdf.Rect(70, 400, 525, 580),
                str(description),
                fontsize=11.5,
                fontname="times-roman",
                color=(0.25, 0.25, 0.25),
                align=pymupdf.TEXT_ALIGN_CENTER
            )

        # Pie de página institucional
        page.draw_line(pymupdf.Point(70, 730), pymupdf.Point(525, 730), color=(0.75, 0.78, 0.82), width=0.8)
        page.insert_textbox(
            pymupdf.Rect(50, 740, 545, 785),
            "DOCUMENTO ACOMPAÑADO EN EL PRIMER OTROSÍ\nCotejado y ensamblado digitalmente para la Oficina Judicial Virtual (OJV)",
            fontsize=8.5,
            fontname="helv",
            color=(0.4, 0.43, 0.48),
            align=pymupdf.TEXT_ALIGN_CENTER
        )

        return doc

    def _img_to_pdf_doc(self, img_path: str) -> Any:
        """Convierte una imagen (png, jpg, jpeg, webp) en página PDF limpia."""
        with pymupdf.open(img_path) as img_doc:
            pdf_bytes = img_doc.convert_to_pdf()
        return pymupdf.open("pdf", pdf_bytes)

    def compile(
        self,
        markdown_content: str,
        output_pdf_path: str,
        annexes: Optional[List[Dict[str, Any]]] = None,
        mobile_preview_path: Optional[str] = None,
        main_pdf_path: Optional[str] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compila el escrito Markdown a PDF, ensambla correlativamente los anexos probatorios
        con carátulas divisorias elegantes e inyecta marcadores jerárquicos nativos (TOC Bookmarks).
        
        Produce dos salidas para la OJV:
        1. Escrito principal solo (ligero para carga en el portal).
        2. Expediente consolidado completo con todos los anexos probatorios y navegación por marcadores.
        """
        if not self.is_available():
            return {"error": "pymupdf o markdown_pdf no están disponibles en el entorno."}

        if not output_pdf_path:
            return {"error": "Ruta de salida 'output_pdf_path' no proporcionada."}

        content = str(markdown_content or "")
        tmp_main_path = None
        final_doc = None

        try:
            # 1. Renderizar escrito principal
            md_pdf = MarkdownPdf(toc_level=0)
            md_pdf.add_section(Section(content, toc=False, paper_size="A4", borders=(36, 36, -36, -36)))

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_f:
                tmp_main_path = tmp_f.name

            md_pdf.save(tmp_main_path)

            # Salida 1: Escrito principal solo (ligero para OJV)
            primary_main_dest = main_pdf_path or mobile_preview_path
            if primary_main_dest:
                try:
                    p_main = Path(primary_main_dest)
                    p_main.parent.mkdir(parents=True, exist_ok=True)
                    md_pdf.save(str(p_main))
                except Exception:
                    pass

            final_doc = pymupdf.open(tmp_main_path)
            main_pages = len(final_doc)

            # Construir marcadores jerárquicos de navegación (TOC Bookmarks)
            main_title = title or "Escrito Principal: Recurso de Protección"
            toc = [
                [1, main_title, 1],
                [2, "Presuma y Comparecencia", 1]
            ]

            # Detectar páginas de secciones clave en el escrito principal
            for p_no in range(main_pages):
                text_page = final_doc[p_no].get_text().upper()
                if "LOS HECHOS" in text_page and not any(str(item[1]) == "I. Los Hechos" for item in toc):
                    toc.append([2, "I. Los Hechos (Cronología Fundante)", p_no + 1])
                if "EL DERECHO" in text_page and not any("El Derecho" in str(item[1]) for item in toc):
                    toc.append([2, "II. El Derecho y Garantías Constitucionales", p_no + 1])
                if "POR TANTO" in text_page and not any(str(item[1]) == "Por Tanto" for item in toc):
                    toc.append([2, "Por Tanto (Peticiones Concretas)", p_no + 1])
                if "OTROSÍ" in text_page and not any("Otrosíes" in str(item[1]) for item in toc):
                    toc.append([2, "Otrosíes y Medidas Cautelares (ONI)", p_no + 1])

            # 2. Adjuntar anexos con carátulas divisorias
            annexes_appended = 0
            annex_errors = []

            if annexes and isinstance(annexes, list):
                for item in annexes:
                    if not isinstance(item, dict):
                        continue
                    num = item.get("num", f"ANEXO N.° {annexes_appended + 1}")
                    doc_title = item.get("title", "Documento Anexo")
                    desc = item.get("desc", "")
                    fpath = item.get("path", "")

                    if not fpath or not os.path.exists(fpath):
                        annex_errors.append(f"Archivo no encontrado para '{doc_title}': {fpath}")
                        continue

                    sep = None
                    anx_doc = None
                    try:
                        # Página donde comenzará este anexo
                        sep_page_idx = len(final_doc) + 1

                        # Inyectar marcador TOC para el Anexo
                        anexo_clean_num = num.replace("«", "").replace("»", "")
                        toc.append([1, f"«{anexo_clean_num}» {doc_title}", sep_page_idx])

                        # Insertar separador institucional
                        sep = self._create_separator_page(num, doc_title, desc)
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
                        annex_errors.append(f"Error procesando anexo '{doc_title}': {str(e)}")
                    finally:
                        if sep:
                            sep.close()
                        if anx_doc:
                            anx_doc.close()

            # 3. Aplicar tabla de marcadores PDF nativos (TOC)
            try:
                final_doc.set_toc(toc)
            except Exception:
                pass

            # 4. Guardar expediente consolidado final
            out_path = Path(output_pdf_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            final_doc.save(str(out_path))

            file_size_mb = os.path.getsize(str(out_path)) / (1024 * 1024)

            res: Dict[str, Any] = {
                "output_pdf": str(out_path.resolve()),
                "main_only_pdf": str(Path(primary_main_dest).resolve()) if primary_main_dest else None,
                "total_pages": len(final_doc),
                "main_pages": main_pages,
                "annexes_count": annexes_appended,
                "size_mb": round(file_size_mb, 2),
                "toc_bookmarks_count": len(toc),
                "mobile_preview_pdf": str(Path(primary_main_dest).resolve()) if primary_main_dest else None
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
