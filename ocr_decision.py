"""Recomienda el plan de OCR de un documento con razonamiento del sistema jurídico chileno.

No decide por el usuario: mide el PDF, aplica reglas explícitas y devuelve 1–3 opciones con su
justificación. El harness elige. Reglas de fondo: la cita es literal (§2 quater), un dígito mal
leído mueve plazos (art. 66 CPC) y un OCR que no lee una página lo dice en vez de inventar.
"""
from __future__ import annotations

import pathlib
from typing import Any, Dict, List

TIPOS = {
    "expediente_judicial": {"engine": "rapidocr", "dpi": 300, "motivo":
        "los escritos y resoluciones se citan literalmente: se prioriza fidelidad sobre velocidad"},
    "escritura_notarial": {"engine": "rapidocr", "dpi": 400, "doble_pasada": True, "motivo":
        "fechas, folios y repertorios mandan en plazos y prescripción: se cotejan cifras con un segundo motor"},
    "sentencia_antigua": {"engine": "rapidocr", "dpi": 300, "doble_pasada": True, "motivo":
        "máquina de escribir y papel carbón: segunda pasada para números y fechas"},
    "documento_administrativo": {"engine": "tesseract", "dpi": 200, "motivo":
        "tipografía moderna de un documento público: el motor liviano alcanza"},
    "tabla_o_liquidacion": {"engine": "rapidocr", "dpi": 300, "aviso":
        "las columnas se pierden en el OCR: las cifras se revisan contra el original antes de citarlas"},
}


def _ruta_existe(ruta: str) -> bool:
    return pathlib.Path(ruta).exists()


def senales_del_pdf(ruta: str) -> Dict[str, Any]:
    import fitz  # PyMuPDF

    doc = fitz.open(str(ruta))
    chars = [len(p.get_text("text") or "") for p in doc]
    imagenes = [len(p.get_images(full=True)) for p in doc]
    paginas = doc.page_count
    con_texto = sum(1 for c in chars if c > 80)
    return {
        "paginas": paginas,
        "paginas_con_texto": con_texto,
        "chars_mediana": sorted(chars)[paginas // 2] if paginas else 0,
        "paginas_solo_imagen": sum(1 for c, i in zip(chars, imagenes, strict=False) if c <= 80 and i),
        "capa_de_texto": con_texto >= max(1, paginas // 2),
    }


def _detectar_tipo(contexto: str, senales: Dict[str, Any]) -> str:
    texto = (contexto or "").lower()
    if any(p in texto for p in ("escritura", "notarial", "notario", "protocolo")):
        return "escritura_notarial"
    if any(p in texto for p in ("liquidación", "planilla", "tabla", "cuadro")):
        return "tabla_o_liquidacion"
    if any(p in texto for p in ("resolución", "dictamen", "oficio", "circular", "boletín")):
        return "documento_administrativo"
    if any(p in texto for p in ("antiguo", "máquina de escribir", "carbón", "197", "198")):
        return "sentencia_antigua"
    return "expediente_judicial"


def recomendar_ocr(ruta: str, contexto: str = "", tipo_documento: str | None = None) -> Dict[str, Any]:
    if not _ruta_existe(ruta):
        return {"error": f"No existe el archivo: {ruta}"}
    try:
        senales = senales_del_pdf(ruta)
    except Exception:  # PDF ilegible: se dice, no se inventa
        senales = {"paginas": 0, "paginas_con_texto": 0, "chars_mediana": 0,
                   "paginas_solo_imagen": 0, "capa_de_texto": False, "ilegible": True}
    razonamiento: List[str] = []
    avisos: List[str] = []

    if senales.get("ilegible"):
        avisos.append("El PDF no se pudo abrir para medirlo (¿dañado o con clave?): "
                      "revísalo antes de confiar en cualquier extracción.")

    if senales["capa_de_texto"]:
        razonamiento.append(
            "El PDF ya trae capa de texto: se extrae tal cual (modo nativo). No se reinterpreta lo que "
            "la fuente ya dice — un OCR sobre texto correcto sólo puede empeorarlo.")
        opciones = [{"modo": "nativo", "engine": "nativo", "dpi": 0, "lang": "spa", "force_ocr": False}]
        tipo = "con_texto"
    else:
        tipo = tipo_documento or _detectar_tipo(contexto, senales)
        regla = TIPOS[tipo]
        razonamiento.append(
            f"Documento sin capa de texto ({senales['paginas_solo_imagen']} de {senales['paginas']} páginas "
            f"sólo imagen) y de tipo «{tipo}»: {regla['motivo']}.")
        opciones = [{"modo": "ocr", "engine": regla["engine"], "dpi": regla["dpi"], "lang": "spa",
                     "force_ocr": True}]
        if regla.get("doble_pasada"):
            opciones.append({"modo": "ocr", "engine": "tesseract", "dpi": regla["dpi"], "lang": "spa+eng",
                             "force_ocr": True})
            razonamiento.append(
                "Se agrega una segunda pasada con otro motor para cotejar dígitos y fechas: una fecha mal "
                "leída mueve un plazo (arts. 66 y siguientes del Código de Procedimiento Civil) o la "
                "prescripción, y el error no se nota leyendo.")
        if any(p in (contexto or "").lower() for p in ("plazo", "notificación", "emplazamiento")):
            razonamiento.append(
                "Hay un plazo en juego: el texto extraído se coteja con el original en las fechas antes "
                "de computarlo (art. 66 CPC: el plazo corre desde la notificación y un dígito cambia el día).")
        if regla.get("aviso"):
            avisos.append(regla["aviso"])
        if senales["paginas"] > 40:
            avisos.append(f"Son {senales['paginas']} páginas: conviene procesar por rangos y revisar el "
                          "contrato de cada página (ok/length) antes de citar.")

    return {
        "documento": ruta,
        "senales": senales,
        "tipo_documento": tipo_documento or tipo,
        "recomendado": opciones[0],
        "alternativas": opciones[1:],
        "razonamiento": razonamiento,
        "como_ejecutar": {"herramienta": "ocr_extract_pdf",
                          "argumentos": {k: v for k, v in opciones[0].items() if k != "modo"}},
        "avisos": avisos,
    }
