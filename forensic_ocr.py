"""
Open Legal Chile — Motor Forense de OCR y Extracción de Documentos Judiciales
Permite extraer texto nativo o aplicar OCR (Tesseract / RapidOCR) sobre
expedientes PDF escaneados, sentencias judiciales, actas y escrituras notariales.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import pymupdf
except ImportError:
    pymupdf = None


class ForensicOCREngine:
    def __init__(self, tesseract_cmd: Optional[str] = None):
        if tesseract_cmd and os.path.exists(tesseract_cmd):
            self.tesseract_cmd = tesseract_cmd
        elif shutil.which("tesseract"):
            self.tesseract_cmd = shutil.which("tesseract")
        elif os.path.exists("/usr/bin/tesseract"):
            self.tesseract_cmd = "/usr/bin/tesseract"
        else:
            self.tesseract_cmd = "tesseract"
        self._available_langs: Optional[List[str]] = None

    def is_available(self) -> bool:
        """Verifica si PyMuPDF y el binario de Tesseract están disponibles."""
        return pymupdf is not None and bool(shutil.which(self.tesseract_cmd) or os.path.exists(self.tesseract_cmd))

    def get_available_languages(self) -> List[str]:
        """Obtiene la lista de modelos de lenguaje instalados en Tesseract."""
        if self._available_langs is not None:
            return self._available_langs
        try:
            res = subprocess.run(
                [self.tesseract_cmd, "--list-langs"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if res.returncode == 0:
                lines = [line.strip() for line in res.stdout.splitlines() if line.strip() and not line.startswith("List of")]
                self._available_langs = lines
                return lines
        except Exception:
            pass
        self._available_langs = ["eng"]
        return self._available_langs

    def _select_valid_lang(self, requested_lang: str) -> str:
        """Selecciona el idioma solicitado o retrocede a 'eng' si no está disponible."""
        available = self.get_available_languages()
        if requested_lang in available:
            return requested_lang
        if "eng" in available:
            return "eng"
        return available[0] if available else "eng"

    def extract_from_pdf(
        self,
        pdf_path: str,
        start_page: int = 1,
        end_page: Optional[int] = None,
        force_ocr: bool = False,
        dpi: int = 150,
        lang: str = "eng"
    ) -> Dict[str, Any]:
        """
        Extrae texto de un archivo PDF página por página.
        Si la página contiene texto seleccionable (>80 caracteres), lo extrae directamente.
        Si la página es un escaneo de imagen o force_ocr=True, ejecuta OCR de alta precisión.
        """
        if not pdf_path:
            return {"error": "Ruta de archivo PDF no proporcionada."}

        path = Path(pdf_path)
        if not path.exists():
            return {"error": f"Archivo no encontrado: {pdf_path}"}

        if pymupdf is None:
            return {"error": "PyMuPDF no está instalado en el entorno."}

        try:
            doc = pymupdf.open(str(path))
        except Exception as e:
            return {"error": f"No se pudo abrir el archivo PDF '{path.name}': {str(e)}"}

        try:
            if doc.is_encrypted:
                return {"error": f"El archivo '{path.name}' está encriptado o protegido con contraseña."}

            total_pages = len(doc)
            if total_pages == 0:
                return {
                    "file": path.name,
                    "total_pages_in_pdf": 0,
                    "processed_pages": 0,
                    "native_pages": 0,
                    "ocr_pages": 0,
                    "pages": [],
                    "full_text": ""
                }

            start = max(1, start_page)
            if end_page is not None:
                end = max(start, min(int(end_page), total_pages))
            else:
                end = total_pages

            if start > total_pages:
                return {
                    "error": f"Página de inicio ({start}) excede el total de páginas del documento ({total_pages})."
                }

            chosen_lang = self._select_valid_lang(lang)

            pages_data = []
            full_text_list = []
            ocr_pages_count = 0
            native_pages_count = 0

            for pno in range(start - 1, end):
                page_num = pno + 1
                try:
                    page = doc[pno]
                    native_text = page.get_text().strip()
                except Exception:
                    native_text = ""

                if len(native_text) > 80 and not force_ocr:
                    # Texto seleccionable
                    method = "native"
                    text = native_text
                    native_pages_count += 1
                else:
                    # Aplicar OCR mediante PyMuPDF rendering + Tesseract
                    method = "ocr"
                    ocr_pages_count += 1
                    tmp_file_path = None
                    try:
                        pix = page.get_pixmap(dpi=dpi)
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                            tmp_file_path = tmp.name
                        pix.save(tmp_file_path)

                        res = subprocess.run(
                            [self.tesseract_cmd, tmp_file_path, "stdout", "-l", chosen_lang, "--oem", "1"],
                            capture_output=True,
                            text=True,
                            timeout=45
                        )
                        if res.returncode == 0:
                            text = res.stdout.strip()
                        else:
                            err_msg = res.stderr.strip() or f"Código {res.returncode}"
                            text = f"[Aviso OCR página {page_num}: {err_msg}]"
                    except subprocess.TimeoutExpired:
                        text = f"[Error OCR página {page_num}: Timeout tras 45s]"
                    except Exception as e:
                        text = f"[Error OCR página {page_num}: {str(e)}]"
                    finally:
                        if tmp_file_path and os.path.exists(tmp_file_path):
                            try:
                                os.unlink(tmp_file_path)
                            except OSError:
                                pass

                page_entry = {
                    "page": page_num,
                    "method": method,
                    "length": len(text),
                    "text": text
                }
                pages_data.append(page_entry)
                full_text_list.append(f"=== PÁGINA {page_num} [{method.upper()}] ===\n{text}")

            return {
                "file": path.name,
                "total_pages_in_pdf": total_pages,
                "processed_pages": len(pages_data),
                "native_pages": native_pages_count,
                "ocr_pages": ocr_pages_count,
                "ocr_language": chosen_lang,
                "pages": pages_data,
                "full_text": "\n\n".join(full_text_list)
            }
        finally:
            doc.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        engine = ForensicOCREngine()
        res = engine.extract_from_pdf(sys.argv[1], start_page=1, end_page=int(sys.argv[2]) if len(sys.argv) > 2 else 3)
        print(f"Procesado: {res.get('file')} ({res.get('processed_pages')} págs)")
        print(res.get("full_text")[:1000])
    else:
        print("Uso: python forensic_ocr.py <archivo.pdf> [paginas_max]")
