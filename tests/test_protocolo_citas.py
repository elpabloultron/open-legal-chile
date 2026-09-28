"""El protocolo de respuesta vive donde el harness lo puede leer.

Nace del reclamo: el asistente no consultaba Hugging Face de entrada y citaba sin el texto de lo
citado. El protocolo se escribe en `AGENTS.md` (lo leen los harness) y en el prompt del chat propio.
"""

import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def test_agents_declara_el_protocolo_de_respuesta():
    texto = (RAIZ / "AGENTS.md").read_text(encoding="utf-8")
    assert "2 quater" in texto, "AGENTS.md debe declarar el protocolo de respuesta (§2 quater)"
    assert "consulta_maestra" in texto, "el paso 0 debe estar nombrado en AGENTS.md"
    assert "huggingface_search_dataset" in texto
    assert "texto literal" in texto, "el protocolo exige el texto literal de lo citado"


def test_el_prompt_del_chat_exige_texto_literal():
    fuente = (RAIZ / "chat_engine.py").read_text(encoding="utf-8")
    assert "texto literal" in fuente.lower()


def test_el_prompt_del_chat_pide_el_plan_de_ocr_antes_de_citar():
    fuente = (RAIZ / "chat_engine.py").read_text(encoding="utf-8")
    assert "ocr_plan_documento" in fuente, "el chat pide el plan de OCR antes de citar un escaneo"
    assert "no se cita de ahí" in fuente
