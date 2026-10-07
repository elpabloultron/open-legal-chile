# .extract_from_pdf

> 16 nodes · cohesion 0.15

## Key Concepts

- **.extract_from_pdf()** (9 connections) — `forensic_ocr.py`
- **.resolve_language()** (7 connections) — `forensic_ocr.py`
- **._select_valid_lang()** (5 connections) — `forensic_ocr.py`
- **.get_available_languages()** (4 connections) — `forensic_ocr.py`
- **._run_tesseract()** (4 connections) — `forensic_ocr.py`
- **._run_paddleocr()** (3 connections) — `forensic_ocr.py`
- **._run_rapidocr()** (3 connections) — `forensic_ocr.py`
- **._aviso_idioma()** (2 connections) — `forensic_ocr.py`
- **Any** (2 connections)
- **Ejecuta RapidOCR (modelos PaddleOCR v4 en ONNX).** (1 connections) — `forensic_ocr.py`
- **Ejecuta PaddleOCR oficial.** (1 connections) — `forensic_ocr.py`
- **Ejecuta Tesseract OCR mediante subproceso CLI.** (1 connections) — `forensic_ocr.py`
- **Obtiene la lista de modelos de lenguaje instalados en Tesseract.** (1 connections) — `forensic_ocr.py`
- **Selecciona el idioma solicitado o retrocede a 'eng' si no está disponible.** (1 connections) — `forensic_ocr.py`
- **Resuelve el idioma del OCR y deja constancia de cualquier rebaja. Un expediente…** (1 connections) — `forensic_ocr.py`
- **Extrae texto de un archivo PDF página por página. Si la página contiene texto…** (1 connections) — `forensic_ocr.py`

## Relationships

- [ForensicOCREngine](ForensicOCREngine.md) (8 shared connections)
- [.get_available_engines](get_available_engines.md) (2 shared connections)

## Source Files

- `forensic_ocr.py`

## Audit Trail

- EXTRACTED: 28 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*