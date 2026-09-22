"""Convierte las fuentes bajadas (PDF) al corpus de doctrina en Markdown.

El motor (LegalGraphify) lee archivos `.md` de `doctrina/` y de ahí saca nodos y relaciones: un
nodo por documento, y las secciones colgando de él. Este módulo hace ese paso:

    PDF  →  texto (pdftotext; si el PDF está escaneado, OCR con el modelo español)
         →  .md con encabezado (título, autor, área, materia, fuente) y secciones

Reglas que sigue, aprendidas a golpes:

- Si el PDF no trae capa de texto (escaneado), se pasa por OCR: un texto vacío no es un documento,
  es una página que no se pudo leer, y eso hay que decirlo, no publicarlo.
- La línea de encabezados y pies repetidos se limpia: si una línea se repite en muchas páginas, no
  es contenido.
- La materia y el área se infieren del catálogo y del nombre del archivo; si no se puede, se dice
  «General» en vez de inventar una materia.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = pathlib.Path(__file__).resolve().parent
DOCTRINA = BASE_DIR / "doctrina"
FUENTES = pathlib.Path.home() / ".openlegal" / "fuentes"

# Palabras que deciden área y materia, revisadas contra los nombres reales del catálogo.
MATERIAS = [
    ("penal", ("penal", "pena", "delito", "corrupcion", "corrupción", "penitenciario", "adolescente",
               "uso-de-la-fuerza", "uso de la fuerza", "nna", "imputado")),
    ("laboral", ("laboral", "trabajo", "trabajadores", "huelga", "sindic", "empleo", "previsional")),
    ("familia", ("familia", "matrimonial", "filiacion", "filiación", "alimentos", "tutela", "guardas",
                 "matrimonio", "gananciales", "menor", "nna", "cuidado-personal")),
    ("civil", ("civil", "obligacion", "obligación", "contrato", "bienes", "dominio", "posesion",
               "posesión", "prescripcion", "prescripción", "sucesorio", "donacion", "donación",
               "responsabilidad", "hipoteca", "prenda", "fianza", "arrendamiento", "propiedad")),
    ("procesal", ("procesal", "procedimiento", "juicio", "prueba", "recurso", "competencia",
                  "nulidad procesal", "case-management", "notificacion", "notificación")),
    ("administrativo", ("administrativo", "contratacion administrativa", "municipal", "municipio",
                        "servicio publico", "servicio público", "probidad", "transparencia")),
    ("constitucional", ("constitucional", "derechos humanos", "ddhh", "proteccion", "protección",
                        "amparo", "convencion", "convención", "discapacidad", "migrantes")),
    ("comercial", ("comercial", "sociedad", "quiebra", "concursal", "titulo valor", "titulo-valor",
                   "competencia", "consumidor", "libre competencia")),
]

JURISDICCIONES = {
    "academia_judicial": "Academia Judicial de Chile",
    "apuntes": "Juan Andrés Orrego Acuña",
    "manuales": "Manuales de estudio",
}


def _sin_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)).lower()


def inferir_materia(archivo: str, material: str = "") -> Tuple[str, str]:
    """Devuelve (área, materia). Si no hay señal suficiente, «General» — no se inventa."""
    pista = _sin_acentos(f"{archivo} {material}")
    for materia, palabras in MATERIAS:
        for palabra in palabras:
            if _sin_acentos(palabra) in pista:
                return materia.capitalize(), materia.capitalize()
    return "General", "General"


def _texto_de_pdf(ruta: pathlib.Path, max_paginas: Optional[int] = None) -> Tuple[str, str]:
    """Devuelve (texto, cómo). Intenta pdftotext y, si no hay capa de texto, OCR."""
    orden = ["pdftotext", "-layout"]
    if max_paginas:
        orden += ["-f", "1", "-l", str(max_paginas)]
    orden += [str(ruta), "-"]
    try:
        r = subprocess.run(orden, capture_output=True, text=True, timeout=600)
        texto = r.stdout or ""
    except Exception:
        texto = ""
    limpio = texto.strip()
    paginas = max(1, texto.count("\f"))
    if len(limpio) / paginas >= 120:  # hay capa de texto suficiente
        return texto, "pdftotext"
    # Escaneado (o casi): se rasteriza y pasa cada página por el OCR de la casa, con el modelo
    # español del sistema (el tesseract de acá arriba solo trae inglés: sin TESSDATA_PREFIX, las
    # palabras acentuadas se pierden y en derecho eso cambia el sentido).
    try:
        import forensic_ocr  # noqa: PLC0415 (dependencia opcional)

        motor = forensic_ocr.ForensicOCREngine()
        if not motor.is_available():
            return texto, "pdftotext (sin capa de texto y sin motor de OCR)"
        import tempfile  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as temporal:
            subprocess.run(["pdftoppm", "-r", "200", "-png", str(ruta), f"{temporal}/pag"],
                           capture_output=True, timeout=1800)
            partes = []
            for imagen in sorted(pathlib.Path(temporal).glob("*.png")):
                parte = motor._run_rapidocr(str(imagen)) if motor.is_rapidocr_available() else ""
                if not parte:
                    parte = motor._run_tesseract(str(imagen), lang="spa")
                if parte:
                    partes.append(parte)
            texto_ocr = "\n".join(partes)
        if len(texto_ocr.strip()) > 500:
            return texto_ocr, "ocr"
        return texto, f"pdftotext (el OCR sacó {len(texto_ocr.strip())} caracteres)"
    except Exception as e:  # noqa: BLE001
        return texto, f"pdftotext (OCR falló: {str(e)[:60]})"


def _limpiar(texto: str) -> str:
    """Saca encabezados y pies repetidos, números de página sueltos y guiones de corte."""
    lineas = texto.split("\n")
    conteo: Dict[str, int] = {}
    for linea in lineas:
        clave = linea.strip()
        if 5 < len(clave) < 90:
            conteo[clave] = conteo.get(clave, 0) + 1
    repetidas = {c for c, n in conteo.items() if n >= 6}
    salida = []
    for linea in lineas:
        clave = linea.strip()
        if clave in repetidas:
            continue
        if re.fullmatch(r"[-–—\s]*\d{1,4}[-–—\s]*", clave):  # sólo un número de página
            continue
        salida.append(linea.rstrip())
    texto = "\n".join(salida)
    texto = re.sub(r"(\w)-\n(\w)", r"\1\2", texto)          # palabra cortada por salto
    texto = re.sub(r"\n{3,}", "\n\n", texto)                 # aire de sobra
    return texto.strip()


def _es_titulo(linea: str) -> bool:
    """Heurística de encabezado: mayúsculas, numeración, «CAPÍTULO», o línea corta sin punto."""
    t = linea.strip()
    if not (4 <= len(t) <= 110):
        return False
    if t.endswith((".", ",", ";", ":")):
        return False
    if re.match(r"^(CAP[IÍ]TULO|T[IÍ]TULO|SECCI[OÓ]N|PARTE|AP[ÉE]NDICE|SUMARIO)\b", t, re.I):
        return True
    if re.match(r"^\d+(\.\d+)*\.?\s+[A-ZÁÉÍÓÚÑ]", t):
        return True
    letras = [c for c in t if c.isalpha()]
    return bool(letras) and sum(1 for c in letras if c.isupper()) / len(letras) > 0.8


def _a_markdown(texto: str, titulo: str) -> str:
    """Convierte el texto plano en algo con estructura: `##` donde parece haber secciones."""
    lineas = texto.split("\n")
    salida: List[str] = []
    en_seccion = False
    for linea in lineas:
        if _es_titulo(linea):
            if not en_seccion:
                en_seccion = True
            salida.append("")
            salida.append(f"## {linea.strip().capitalize() if linea.strip().isupper() else linea.strip()}")
            salida.append("")
        else:
            salida.append(linea)
    return "\n".join(salida).strip()


def convertir_pdf(ruta: pathlib.Path, titulo: str, autor: str, area: str, materia: str,
                  fuente: str, tipo: str) -> Tuple[str, Dict[str, Any]]:
    texto, como = _texto_de_pdf(ruta)
    texto = _limpiar(texto)
    if len(texto) < 500:
        # Un documento sin texto no es un documento: no se escribe nada. Se informa para que se
        # pase por OCR antes, en vez de dejar un archivo vacío en el corpus.
        return "", {"caracteres": len(texto), "extraccion": como, "secciones": 0, "vacio": True}
    cuerpo = _a_markdown(texto, titulo)
    documento = f"""---
titulo: {titulo}
autor: {autor}
area: {area}
materia: {materia}
tipo: {tipo}
fuente: {fuente}
paginas_o_caracteres: {len(texto)} caracteres
extraccion: {como}
---

# {titulo}

**Tratadistas:** {autor} | **Área:** {area} | **Materia:** {materia}

{cuerpo}
"""
    return documento, {"caracteres": len(texto), "extraccion": como,
                       "secciones": documento.count("\n## ")}


def convertir_todo(fuentes: pathlib.Path = FUENTES, doctrina: pathlib.Path = DOCTRINA,
                   limite: Optional[int] = None, desde: str = "") -> Dict[str, Any]:
    """Recorre las fuentes y escribe el corpus en Markdown. Devuelve el informe."""
    manifiesto = {}
    ruta_manifiesto = fuentes / "manifiesto.json"
    if ruta_manifiesto.is_file():
        for item in json.loads(ruta_manifiesto.read_text(encoding="utf-8")):
            manifiesto[item["archivo"]] = item

    informe: List[Dict[str, Any]] = []
    pendientes: List[Dict[str, Any]] = []
    hechos = 0
    for carpeta, autor in JURISDICCIONES.items():
        origen = fuentes / carpeta
        if not origen.is_dir():
            continue
        destino = doctrina / ("apuntes_orrego" if carpeta == "apuntes" else carpeta)
        destino.mkdir(parents=True, exist_ok=True)
        for pdf in sorted(origen.glob("*.pdf")):
            if desde and pdf.name < desde:
                continue
            datos = manifiesto.get(pdf.name, {})
            titulo = (datos.get("material") or datos.get("titulo_pdf") or pdf.stem)
            titulo = re.sub(r"\.pdf$", "", titulo).strip() or pdf.stem
            area, materia = inferir_materia(pdf.name, titulo)
            if carpeta == "academia_judicial":
                area = area if area != "General" else "Judicial"
            documento, meta = convertir_pdf(
                pdf, titulo=titulo, autor=autor, area=area, materia=materia,
                fuente=datos.get("url", ""), tipo=carpeta)
            if meta.get("vacio"):
                pendientes.append({"pdf": pdf.name, "motivo": meta.get("extraccion", "sin texto")})
                print(f"  ⚠ sin texto (queda pendiente de OCR): {pdf.name[:60]}", flush=True)
                continue
            salida = destino / (re.sub(r"[^\w\-\. ]", "", pdf.stem)[:90].strip() + ".md")
            salida.write_text(documento, encoding="utf-8")
            informe.append({"pdf": pdf.name, "md": str(salida.relative_to(BASE_DIR)),
                            "titulo": titulo, "area": area, **meta})
            hechos += 1
            if hechos % 10 == 0:
                print(f"  … {hechos} convertidos", flush=True)
            if limite and hechos >= limite:
                break
        if limite and hechos >= limite:
            break
    return {"convertidos": hechos, "detalle": informe, "pendientes": pendientes}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PDF → Markdown para el corpus de doctrina")
    parser.add_argument("--limite", type=int, default=None)
    parser.add_argument("--desde", type=str, default="")
    parser.add_argument("--informe", type=str, default="/tmp/ingesta_informe.json")
    args = parser.parse_args()
    resultado = convertir_todo(limite=args.limite, desde=args.desde)
    pathlib.Path(args.informe).write_text(json.dumps(resultado, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    print(f"\nCONVERTIDOS: {resultado['convertidos']}")
    print(f"informe: {args.informe}")
