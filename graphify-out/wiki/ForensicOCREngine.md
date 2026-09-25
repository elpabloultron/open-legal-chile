# ForensicOCREngine

> 15 nodes · cohesion 0.24

## Key Concepts

- **ForensicOCREngine** (36 connections) — `forensic_ocr.py`
- **test_ocr_idioma.py** (17 connections) — `tests/test_ocr_idioma.py`
- **_pdf_escaneado()** (5 connections) — `tests/test_ocr_idioma.py`
- **test_extract_informa_idioma_pedido_y_usado()** (3 connections) — `tests/test_ocr_idioma.py`
- **test_rapidocr_no_advierte_por_tesseract()** (3 connections) — `tests/test_ocr_idioma.py`
- **test_un_fallo_de_ocr_no_pasa_por_texto_del_documento()** (3 connections) — `tests/test_ocr_idioma.py`
- **_esquema_ocr()** (2 connections) — `tests/test_ocr_idioma.py`
- **test_avisa_cuando_falta_el_modelo_de_espanol()** (2 connections) — `tests/test_ocr_idioma.py`
- **test_default_del_motor_es_espanol()** (2 connections) — `tests/test_ocr_idioma.py`
- **test_la_herramienta_declara_idioma_y_dpi()** (2 connections) — `tests/test_ocr_idioma.py`
- **test_mezcla_de_idiomas_conserva_lo_que_existe()** (2 connections) — `tests/test_ocr_idioma.py`
- **test_no_avisa_cuando_el_modelo_esta_instalado()** (2 connections) — `tests/test_ocr_idioma.py`
- **.__init__()** (1 connections) — `forensic_ocr.py`
- **Pruebas del idioma del OCR en el motor forense. El problema que cubren:…** (1 connections) — `tests/test_ocr_idioma.py`
- **Un PDF sin capa de texto útil: obliga a pasar por OCR.** (1 connections) — `tests/test_ocr_idioma.py`

## Relationships

- [.extract_from_pdf](extract_from_pdf.md) (8 shared connections)
- [.get_available_engines](get_available_engines.md) (6 shared connections)
- [doc2md_ingestor.py](doc2md_ingestor.py.md) (2 shared connections)
- [mcp_server.py](mcp_server.py.md) (2 shared connections)
- [handle_tool_call](handle_tool_call.md) (2 shared connections)
- [test_ocr_pagina_ilegible.py](test_ocr_pagina_ilegible.py.md) (2 shared connections)
- [os](os.md) (2 shared connections)
- [test_ocr_engine_available_engines_and_instructions](test_ocr_engine_available_engines_and_instructions.md) (1 shared connections)
- [test_ocr_engine_force_ocr](test_ocr_engine_force_ocr.md) (1 shared connections)
- [test_ocr_engine_invalid_inputs](test_ocr_engine_invalid_inputs.md) (1 shared connections)
- [test_ocr_engine_native_extraction](test_ocr_engine_native_extraction.md) (1 shared connections)
- [test_ocr_engine_rapidocr_selection](test_ocr_engine_rapidocr_selection.md) (1 shared connections)

## Source Files

- `forensic_ocr.py`
- `tests/test_ocr_idioma.py`

## Audit Trail

- EXTRACTED: 56 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*