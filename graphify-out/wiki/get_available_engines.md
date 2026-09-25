# .get_available_engines

> 12 nodes · cohesion 0.21

## Key Concepts

- **.get_available_engines()** (6 connections) — `forensic_ocr.py`
- **.is_available()** (5 connections) — `forensic_ocr.py`
- **.is_paddleocr_available()** (5 connections) — `forensic_ocr.py`
- **.is_rapidocr_available()** (5 connections) — `forensic_ocr.py`
- **._resolve_engine()** (5 connections) — `forensic_ocr.py`
- **.is_tesseract_available()** (4 connections) — `forensic_ocr.py`
- **Resuelve el motor de OCR a utilizar según disponibilidad.** (1 connections) — `forensic_ocr.py`
- **Verifica si RapidOCR (modelos de PaddleOCR en ONNX) está disponible.** (1 connections) — `forensic_ocr.py`
- **Verifica si el framework PaddleOCR nativo está disponible.** (1 connections) — `forensic_ocr.py`
- **Verifica si el binario del sistema Tesseract está disponible.** (1 connections) — `forensic_ocr.py`
- **Verifica si PyMuPDF y al menos un motor de OCR están disponibles.** (1 connections) — `forensic_ocr.py`
- **Retorna la lista de motores de extracción y OCR actualmente utilizables.** (1 connections) — `forensic_ocr.py`

## Relationships

- [ForensicOCREngine](ForensicOCREngine.md) (6 shared connections)
- [.extract_from_pdf](extract_from_pdf.md) (2 shared connections)

## Source Files

- `forensic_ocr.py`

## Audit Trail

- EXTRACTED: 22 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*