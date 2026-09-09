"""
Open Legal Chile — Motor Forense de OCR y Extracción de Documentos Judiciales
Permite extraer texto nativo o aplicar OCR de alta precisión (RapidOCR / PaddleOCR / Tesseract)
sobre expedientes PDF escaneados, sentencias judiciales, actas y escrituras notariales.
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
    pymupdf = None  # type: ignore[assignment]


class ForensicOCREngine:
    def __init__(self, tesseract_cmd: Optional[str] = None, default_engine: str = "auto"):
        which_tess = shutil.which("tesseract") or shutil.which("tesseract.exe")
        if tesseract_cmd and os.path.exists(tesseract_cmd):
            self.tesseract_cmd = tesseract_cmd
        elif which_tess:
            self.tesseract_cmd = which_tess
        elif os.path.exists("/usr/bin/tesseract"):
            self.tesseract_cmd = "/usr/bin/tesseract"
        elif sys.platform == "win32":
            # Rutas estándar del repositorio oficial de Windows (winget install UB-Mannheim.TesseractOCR)
            win_candidates = [
                os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"), "Tesseract-OCR", "tesseract.exe"),
                os.path.join(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"), "Tesseract-OCR", "tesseract.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Tesseract-OCR", "tesseract.exe"),
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ]
            found = None
            for cand in win_candidates:
                if cand and os.path.exists(cand):
                    found = cand
                    break
            self.tesseract_cmd = found if found else "tesseract.exe"
        else:
            self.tesseract_cmd = "tesseract"

        self.default_engine = default_engine
        self._available_langs: Optional[List[str]] = None
        self._rapidocr_instance: Optional[Any] = None
        self._paddleocr_instance: Optional[Any] = None

    @staticmethod
    def get_install_instructions() -> Dict[str, str]:
        """Instrucciones de instalación de los motores de OCR por sistema operativo y python."""
        return {
            "rapidocr_python": "pip install rapidocr-onnxruntime",
            "paddleocr_python": "pip install paddleocr paddlepaddle",
            "windows_winget": "winget install UB-Mannheim.TesseractOCR",
            "linux_apt": "sudo apt update && sudo apt install -y tesseract-ocr tesseract-ocr-spa",
            "macos_brew": "brew install tesseract tesseract-lang"
        }

    @staticmethod
    def is_rapidocr_available() -> bool:
        """Verifica si RapidOCR (modelos de PaddleOCR en ONNX) está disponible."""
        try:
            import rapidocr_onnxruntime  # noqa: F401
            return True
        except ImportError:
            return False

    @staticmethod
    def is_paddleocr_available() -> bool:
        """Verifica si el framework PaddleOCR nativo está disponible."""
        try:
            import paddleocr  # noqa: F401
            return True
        except ImportError:
            return False

    def is_tesseract_available(self) -> bool:
        """Verifica si el binario del sistema Tesseract está disponible."""
        return bool(shutil.which(self.tesseract_cmd) or os.path.exists(self.tesseract_cmd))

    def is_available(self) -> bool:
        """Verifica si PyMuPDF y al menos un motor de OCR están disponibles."""
        if pymupdf is None:
            return False
        return self.is_rapidocr_available() or self.is_paddleocr_available() or self.is_tesseract_available()

    def get_available_engines(self) -> List[str]:
        """Retorna la lista de motores de extracción y OCR actualmente utilizables."""
        engines = ["native"]
        if self.is_rapidocr_available():
            engines.append("rapidocr")
        if self.is_paddleocr_available():
            engines.append("paddleocr")
        if self.is_tesseract_available():
            engines.append("tesseract")
        return engines

    def _resolve_engine(self, requested: str) -> str:
        """Resuelve el motor de OCR a utilizar según disponibilidad."""
        req = (requested or self.default_engine or "auto").lower().strip()
        if req == "rapidocr":
            return "rapidocr" if self.is_rapidocr_available() else "tesseract"
        if req == "paddleocr":
            return "paddleocr" if self.is_paddleocr_available() else "tesseract"
        if req == "tesseract":
            return "tesseract"
        # Modo 'auto': Prefiere RapidOCR (PaddleOCR ONNX) por precisión en expedientes judiciales, luego PaddleOCR, luego Tesseract
        if self.is_rapidocr_available():
            return "rapidocr"
        if self.is_paddleocr_available():
            return "paddleocr"
        return "tesseract"

    def _run_rapidocr(self, img_path: str) -> str:
        """Ejecuta RapidOCR (modelos PaddleOCR v4 en ONNX)."""
        if self._rapidocr_instance is None:
            from rapidocr_onnxruntime import RapidOCR
            self._rapidocr_instance = RapidOCR()
        result, _ = self._rapidocr_instance(img_path)
        if not result:
            return ""
        lines = [item[1] for item in result if len(item) > 1 and item[1]]
        return "\n".join(lines).strip()

    def _run_paddleocr(self, img_path: str, lang: str = "es") -> str:
        """Ejecuta PaddleOCR oficial."""
        if self._paddleocr_instance is None:
            from paddleocr import PaddleOCR
            p_lang = "es" if lang in ("spa", "es", "spanish") else "en"
            self._paddleocr_instance = PaddleOCR(use_angle_cls=True, lang=p_lang, show_log=False)
        result = self._paddleocr_instance.ocr(img_path, cls=True)
        if not result or not result[0]:
            return ""
        lines = [line[1][0] for line in result[0] if len(line) > 1 and line[1]]
        return "\n".join(lines).strip()

    def _run_tesseract(self, img_path: str, lang: str = "eng") -> str:
        """Ejecuta Tesseract OCR mediante subproceso CLI."""
        chosen_lang = self._select_valid_lang(lang)
        res = subprocess.run(
            [self.tesseract_cmd, img_path, "stdout", "-l", chosen_lang, "--oem", "1"],
            capture_output=True,
            text=True,
            timeout=45
        )
        if res.returncode == 0:
            return res.stdout.strip()
        err_msg = res.stderr.strip() or f"Código {res.returncode}"
        return f"[Aviso OCR Tesseract: {err_msg}]"

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
        lang: str = "eng",
        engine: str = "auto"
    ) -> Dict[str, Any]:
        """
        Extrae texto de un archivo PDF página por página.
        Si la página contiene texto seleccionable (>80 caracteres) y force_ocr=False, lo extrae directamente.
        Si la página es un escaneo de imagen o force_ocr=True, ejecuta OCR de alta precisión (RapidOCR/PaddleOCR/Tesseract).
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
            resolved_engine = self._resolve_engine(engine)

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
                    # Texto digital seleccionable nativo
                    method = "native"
                    page_engine = "native"
                    text = native_text
                    native_pages_count += 1
                else:
                    # Aplicar OCR mediante renderizado PyMuPDF + Motor seleccionado
                    method = "ocr"
                    page_engine = resolved_engine
                    ocr_pages_count += 1
                    tmp_file_path = None
                    try:
                        pix = page.get_pixmap(dpi=dpi)
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                            tmp_file_path = tmp.name
                        pix.save(tmp_file_path)

                        if resolved_engine == "rapidocr":
                            text = self._run_rapidocr(tmp_file_path)
                        elif resolved_engine == "paddleocr":
                            text = self._run_paddleocr(tmp_file_path, lang=chosen_lang)
                        else:
                            text = self._run_tesseract(tmp_file_path, lang=chosen_lang)
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
                    "engine": page_engine,
                    "length": len(text),
                    "text": text
                }
                pages_data.append(page_entry)
                header_info = f"=== PÁGINA {page_num} [{method.upper()} · {page_engine.upper()}] ==="
                full_text_list.append(f"{header_info}\n{text}")

            return {
                "file": path.name,
                "total_pages_in_pdf": total_pages,
                "processed_pages": len(pages_data),
                "native_pages": native_pages_count,
                "ocr_pages": ocr_pages_count,
                "ocr_engine_used": resolved_engine if ocr_pages_count > 0 else "native",
                "available_engines": self.get_available_engines(),
                "ocr_language": chosen_lang,
                "pages": pages_data,
                "full_text": "\n\n".join(full_text_list)
            }
        finally:
            doc.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        engine = ForensicOCREngine()
        print(f"Motores disponibles: {engine.get_available_engines()}")
        res = engine.extract_from_pdf(sys.argv[1], start_page=1, end_page=int(sys.argv[2]) if len(sys.argv) > 2 else 3)
        print(f"Procesado: {res.get('file')} ({res.get('processed_pages')} págs) - Motor: {res.get('ocr_engine_used')}")
        print(str(res.get("full_text") or "")[:1000])
    else:
        print("Uso: python forensic_ocr.py <archivo.pdf> [paginas_max]")
        engine = ForensicOCREngine()
        print(f"Motores disponibles detectados: {engine.get_available_engines()}")
