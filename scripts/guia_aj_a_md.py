#!/usr/bin/env python3
"""Convierte una guía de la Academia Judicial (PDF) a Markdown con el formato del corpus.

Uso:
    python scripts/guia_aj_a_md.py --pdf <ruta.pdf> --titulo "Guía …" \\
        --area "Familia" --materia "Consejería técnica" --fuente "https://…"

Deja el archivo en `corpus_guias_aj/` con la misma cabecera que el resto de las guías
(autor, área, materia, tipo, fuente, caracteres, extracción) y el texto íntegro del PDF:
nada se resume ni se recorta.
"""
import argparse
import pathlib
import re
import shutil
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "corpus_guias_aj"
PDFTOTEXT = shutil.which("pdftotext") or "pdftotext"

PLANTILLA = """---
titulo: {titulo}
autor: Academia Judicial de Chile
area: {area}
materia: {materia}
tipo: guia_academia_judicial
fuente: {fuente}
paginas_o_caracteres: {caracteres} caracteres
extraccion: pdftotext
---

# {titulo}

**Tratadistas:** Academia Judicial de Chile | **Área:** {area} | **Materia:** {materia}

{texto}"""


def texto_del_pdf(ruta: pathlib.Path) -> str:
    corrida = subprocess.run([PDFTOTEXT, "-q", str(ruta), "-"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
    return corrida.stdout.strip()


def nombre_de_archivo(titulo: str) -> str:
    limpio = re.sub(r"[^0-9A-Za-zÁÉÍÓÚáéíóúÑñü]+", "_", titulo.strip()).strip("_")
    return f"{limpio}.md"


def main() -> int:
    ap = argparse.ArgumentParser(description="Guía AJ de PDF a Markdown (texto íntegro).")
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--titulo", required=True)
    ap.add_argument("--area", required=True)
    ap.add_argument("--materia", required=True)
    ap.add_argument("--fuente", default="https://guias.academiajudicial.cl/")
    ap.add_argument("--nombre", default=None, help="nombre del archivo sin .md (por defecto, del título)")
    args = ap.parse_args()

    pdf = pathlib.Path(args.pdf)
    if not pdf.exists():
        print(f"no existe: {pdf}", file=sys.stderr)
        return 1

    texto = texto_del_pdf(pdf)
    if len(texto) < 200:
        print(f"el PDF no rinde texto ({len(texto)} caracteres): se convierte a mano u OCR, no se inventa",
              file=sys.stderr)
        return 2

    contenido = PLANTILLA.format(titulo=args.titulo, area=args.area, materia=args.materia,
                                 fuente=args.fuente, caracteres=len(texto), texto=texto)
    salida = DESTINO / (f"{args.nombre}.md" if args.nombre else nombre_de_archivo(args.titulo))
    salida.write_text(contenido, encoding="utf-8")
    print(f"{salida.relative_to(RAIZ)} · {len(texto)} caracteres")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
