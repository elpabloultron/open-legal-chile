#!/usr/bin/env python3
"""
Open Legal Chile — Biblioteca ambiental: libros, informes, foros, manuales y material
docente de derecho ambiental, convertidos a Markdown con ficha de cita.

Contenido:
  · 3TA — libros del Concurso Nacional de Comentarios de Sentencias (6).
  · 2TA — informes en derecho de las causas R-06-2013, R-07-2013, R-16-2013, R-40-2014 y R-45-2014 (14).
  · 2TA — documentos y programas de los Foros de Justicia Ambiental.
  · Manuales y material docente aportados en `ambiental/` (extraídos de los .zip).

Los PDF ya están descargados: en `biblioteca_ambiental/pdf/` los oficiales, bajo `ambiental/`
los del usuario. Este script no descarga; convierte lo que está en disco y declara lo que falte.

Salida:
  · biblioteca_ambiental/<nombre>.md               (texto íntegro + ficha de cita)
  · data/jurisprudencia/biblioteca_ambiental.jsonl (índice → archivo, caracteres y tokens)
  · biblioteca_ambiental/README.md                 (versionado en git; los .md no)

Reanudable y paralelo (4 conversiones simultáneas). Los escaneos se OCR-ean solo en la muestra inicial.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import ingesta_fuentes as ing  # noqa: E402

DIR_MD = BASE / "biblioteca_ambiental"
DIR_PDF = DIR_MD / "pdf"
INDICE = BASE / "data" / "jurisprudencia" / "biblioteca_ambiental.jsonl"
AMBIENTAL = BASE / "ambiental"
EXTRAIDO = AMBIENTAL / "extraido"
TRABAJADORES = 4
MAX_PAGINAS_OCR = 60
PDFINFO = shutil.which("pdfinfo") or "pdfinfo"
PDFTOTEXT = shutil.which("pdftotext") or "pdftotext"

TIPO_LEGIBLE = {
    "libro_concurso": "Libros del Concurso Nacional de Comentarios de Sentencias (3TA)",
    "informe": "Informes en derecho (2TA)",
    "foro": "Foros de justicia ambiental (2TA)",
    "libro": "Manuales y libros de derecho ambiental",
    "docencia": "Material docente de derecho ambiental",
}

# ── Fuentes remotas (PDF ya descargados en biblioteca_ambiental/pdf/) ──────────────────────

LIBROS_CONCURSO = {
    "1": ("Primer Concurso Nacional de Comentarios de Sentencias — 3TA",
          "https://3ta.cl/wp-content/uploads/Libro-Primer-Concurso-Nacional-de-Comentarios-de-Sentencias-del-Tercer-Tribunal-Ambiental-061119.pdf"),
    "2": ("Segundo Concurso Nacional de Comentarios de Sentencias — 3TA",
          "https://3ta.cl/wp-content/uploads/2021/02/SEGUNDO-CONCURSO-NACIONAL-DE-COMENTARIOS-DE-SENTENCIAS-VERSI%C3%93N-WEB-1.pdf"),
    "3": ("Tercer Concurso Nacional de Comentarios de Sentencias — 3TA",
          "https://3ta.cl/wp-content/uploads/2021/10/libro-comentario-sentencias.pdf"),
    "4": ("Cuarto Concurso Nacional de Comentarios de Sentencias — 3TA",
          "https://3ta.cl/wp-content/uploads/2023/04/IVConcurso_versionweb.pdf"),
    "5": ("Quinto Concurso Nacional de Comentarios de Sentencias — 3TA",
          "https://3ta.cl/wp-content/uploads/2023/11/QUINTO-CONCURSO-DE-COMENTARIOS-DE-SENTENCIAS-27-NOV.pdf"),
    "6": ("Sexto Concurso Nacional de Comentarios de Sentencias — 3TA",
          "https://3ta.cl/wp-content/uploads/2024/12/Libro-VI-Concurso-Version-Corregida-digital.pdf"),
}

INFORMES = [
    ("01", "", "El concurso infraccional imperfecto", "Jean Pierre Matus",
     "https://tribunalambiental.cl/wp-content/uploads/2014/07/Informe-en-derecho-concurso-infraccional-imperfecto-Jean-Pierre-Matus.pdf"),
    ("02", "", "Terceros coadyuvantes en casación", "Alejandro Romero Seguel",
     "https://tribunalambiental.cl/wp-content/uploads/2014/07/Informe_en_derecho-_Terceros_Coadyuvantes_en_Casacion-_A-Romero-Seguel.pdf"),
    ("03", "R-06-2013", "Informe en derecho", "Rodrigo Silva Montes",
     "https://tribunalambiental.cl/wp-content/uploads/2014/07/R-06-2013-Informe-en-derecho-de-don-Rodrigo-Silva-Montes1.pdf"),
    ("04", "R-06-2013", "Informe en derecho", "Patricio Leyton Flórez",
     "https://tribunalambiental.cl/wp-content/uploads/2014/07/R-06-2013_Informe_en_Derecho_Sr-Patricio-Leyton-Florez.pdf"),
    ("05", "R-07-2013", "Informe en derecho", "Alejandro Romero Seguel",
     "https://tribunalambiental.cl/wp-content/uploads/2014/07/R-07-2013-Informe-en-derecho-de-don-Alejandro-Romero-Seguel1.pdf"),
    ("06", "R-16-2013", "Informe en derecho", "Alejandro Romero Seguel",
     "https://tribunalambiental.cl/wp-content/uploads/2014/07/R-16-2013-Informe-Alejandro-Romero-Sequel.pdf"),
    ("07", "R-40-2014", "Informe en derecho", "Claudio Moraga",
     "https://tribunalambiental.cl/wp-content/uploads/2014/07/R-40-2014-Informe-en-Derecho-Claudio-Moraga.pdf"),
    ("08", "R-40-2014", "Informe en derecho", "Andrés Bordalí",
     "https://tribunalambiental.cl/wp-content/uploads/2014/07/R-40-Informe-en-Derecho-Andres-Bordali.pdf"),
    ("09", "R-40-2014", "Informe en derecho", "Cristián Maturana y Jaime Jara",
     "https://tribunalambiental.cl/wp-content/uploads/2014/07/R-40-Informe-en-Derecho-Cristian-Maturana-y-Jaime-Jara.pdf"),
    ("10", "R-40-2014", "Opinión legal", "Cristián Maturana",
     "https://tribunalambiental.cl/wp-content/uploads/2014/07/R-40-Opinion-Legal-Cristian-Maturana.pdf"),
    ("11", "R-45-2014", "Informe en derecho", "Luis Cordero Vega",
     "https://tribunalambiental.cl/wp-content/uploads/2014/07/R-45-2014-06-01-2015-Doc.-Informe-en-Derecho-Luis-Cordero-Vega..pdf"),
    ("12", "R-06-2013", "Informe en derecho", "Gabriel del Favero Valdés",
     "https://tribunalambiental.cl/wp-content/uploads/2015/10/R-06-2013-Informe-en-derecho-de-don-Gabriel-Del-Favero-Valdes.pdf"),
    ("13", "R-06-2013", "Informe en derecho", "Luis Cordero Vega",
     "https://tribunalambiental.cl/wp-content/uploads/2015/10/R-06-2013-Informe-en-derecho-de-don-Luis-Cordero-Vega.pdf"),
    ("14", "R-06-2013", "Informe en derecho", "Jorge Bermúdez Soto",
     "https://tribunalambiental.cl/wp-content/uploads/2018/09/R-06-2013-Informe-en-derecho-de-don-Jorge-Bermudez-Soto.pdf"),
]

FOROS = [
    ("1", "1er Foro Internacional de Justicia Ambiental — libro",
     "https://tribunalambiental.cl/wp-content/uploads/2021/05/1er-Foro-Internacional-de-Justicia-Ambiental.pdf"),
    ("2", "II Foro Internacional de Justicia Ambiental — libro",
     "https://tribunalambiental.cl/wp-content/uploads/2021/05/II-Foro-Internacional-de-Justicia-Ambiental.pdf"),
    ("1_2014_programa", "Programa — Foro Interamericano de Justicia Ambiental (2014)",
     "https://tribunalambiental.cl/wp-content/uploads/2021/04/Programa_Foro-Interamericano-Justicia-Ambiental-01-10-2014.pdf"),
    ("5_programa", "Programa — V Foro Internacional de Justicia Ambiental (2022)",
     "https://tribunalambiental.cl/wp-content/uploads/2022/11/Programa-V_Foro-Internacional-Justicia-Ambiental-8-11-2022.pdf"),
    ("5_programa_preliminar", "Programa preliminar — V Foro Internacional de Justicia Ambiental (2022)",
     "https://tribunalambiental.cl/wp-content/uploads/2022/11/Programa_Preliminar_V_Foro-Internacional-Justicia-Ambiental-2-11-2022.pdf"),
]

LIBROS_LOCALES = [
    ("Responsabilidad_ambiental_en_Chile",
     "Responsabilidad ambiental en Chile — Sistematización de los regímenes de reparación, indemnización, administrativo y penal (Asesoría Técnica Parlamentaria, mayo 2026)",
     "20260507responsabilidadambiental_EDITPA_final.pdf"),
    ("Guia_de_acceso_a_la_justicia_ambiental_v1.3",
     "Guía de acceso a la justicia ambiental (v1.3)",
     "Guia-de-Acceso-a-la-Justicia-v1.3.pdf"),
    ("Manual_de_Derecho_Ambiental_Chileno",
     "Manual de Derecho Ambiental Chileno",
     "Manual_de_Derecho_Ambiental_Chileno.pdf"),
    ("Manual_de_acceso_a_la_justicia_ambiental_Tomo_1",
     "Manual de acceso a la justicia ambiental — Tomo 1",
     "MANUAL_JUSTICIAAMBIENTAL.pdf"),
    ("Nueva_institucionalidad_ambiental",
     "Nueva institucionalidad ambiental — Camila Boettiger (Revista Actualidad Jurídica N° 22, 2010)",
     "Nueva_Institucionalidad_Ambiental_-_Actu.pdf"),
]


# ── Nombres, fichas y conversión ───────────────────────────────────────────────────────────

def slug(texto: str) -> str:
    """Identificador estable para nombres de archivo: sin acentos, sin espacios."""
    texto = re.sub(r"\.pdf$", "", (texto or "").strip(), flags=re.I)
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9_]+", "-", texto)
    return re.sub(r"-{2,}", "-", texto).strip("-")


def nombre_archivo(reg: dict) -> str:
    tipo = reg.get("tipo", "")
    if tipo == "libro_concurso":
        return f"3ta_libro_concurso_{reg.get('numero', 's-n')}"
    if tipo == "informe":
        return f"2ta_informe_derecho_{reg.get('numero', 's-n')}"
    if tipo == "foro":
        return f"2ta_foro_{reg.get('slug', 's-n')}"
    if tipo == "libro":
        return f"libro_{slug(reg.get('stem', ''))}"
    if tipo == "docencia":
        return f"docencia_{slug(reg.get('stem', ''))}"
    return slug(reg.get("titulo", "documento"))


def ficha(reg: dict, archivo: str) -> str:
    lineas = [
        f"# {reg.get('titulo', 'Documento')}",
        "",
        f"- **Colección:** Biblioteca ambiental — {TIPO_LEGIBLE.get(reg.get('tipo', ''), reg.get('tipo', ''))}",
    ]
    if reg.get("autor"):
        lineas.append(f"- **Autor:** {reg['autor']}")
    if reg.get("rol"):
        lineas.append(f"- **Rol:** {reg['rol']}")
    if reg.get("tribunal_nombre"):
        lineas.append(f"- **Tribunal:** {reg['tribunal_nombre']}")
    if reg.get("origen"):
        lineas.append(f"- **Material:** {reg['origen']}")
    if reg.get("url_pdf"):
        lineas.append(f"- **Documento oficial:** {reg['url_pdf']}")
    lineas += [
        f"- **Fuente:** [Hugging Face - biblioteca_ambiental/{archivo}]"
        f"(https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile/blob/main/biblioteca_ambiental/{archivo})",
        "",
        "---",
        "",
    ]
    return "\n".join(lineas)


def procesar(item: tuple[int, dict]) -> tuple[int, str]:
    idx, reg = item
    nombre = reg.get("nombre") or nombre_archivo(reg)
    md = DIR_MD / f"{nombre}.md"
    pdf = pathlib.Path(reg.get("ruta_pdf") or (DIR_PDF / f"{nombre}.pdf"))
    if md.exists() and md.stat().st_size > 500:
        chars = len(md.read_text(encoding="utf-8", errors="replace"))
        return idx, f"saltada|{nombre}|{chars}"
    try:
        if not pdf.exists():
            raise FileNotFoundError(f"falta el PDF {pdf}")
        paginas = 0
        try:
            info = subprocess.run([PDFINFO, str(pdf)], capture_output=True, text=True, encoding="utf-8", timeout=60)  # nosec B603
            for linea in info.stdout.splitlines():
                if linea.startswith("Pages:"):
                    paginas = int(linea.split()[1])
        except Exception:
            pass
        prueba = subprocess.run([PDFTOTEXT, "-layout", "-f", "1", "-l", "5", str(pdf), "-"],  # nosec B603
                                capture_output=True, text=True, encoding="utf-8", timeout=120)
        if len((prueba.stdout or "").strip()) / 5 >= 120:
            texto, metodo = ing._texto_de_pdf(pdf)
        else:
            texto, metodo = ing._texto_de_pdf(pdf, max_paginas=MAX_PAGINAS_OCR)
            metodo += f" (escaneo: OCR de {MAX_PAGINAS_OCR} de {paginas or '?'} páginas)"
        if len(texto.strip()) < 200:
            raise ValueError(f"texto insuficiente ({len(texto.strip())} chars, {metodo})")
        cuerpo = ing._limpiar(texto)
        md.write_text(ficha(reg, f"{nombre}.md") + cuerpo + "\n", encoding="utf-8")
        return idx, f"ok|{nombre}|{len(cuerpo)}|{metodo}|{paginas}"
    except Exception as e:
        return idx, f"error|{nombre}|{type(e).__name__}: {str(e)[:90]}"


def escribir_salidas(filas: list) -> None:
    """Índice .jsonl y README versionado de la colección."""
    incorporadas = [r for r in filas if r.get("archivo_md") and r.get("caracteres")]
    with open(INDICE, "w", encoding="utf-8") as f:
        for r in incorporadas:
            f.write(json.dumps({
                "tipo": r.get("tipo"), "numero": r.get("numero"), "titulo": r.get("titulo"),
                "autor": r.get("autor"), "rol": r.get("rol"), "tribunal": r.get("tribunal"),
                "origen": r.get("origen"), "url_pdf": r.get("url_pdf"),
                "archivo_md": r["archivo_md"], "caracteres": r.get("caracteres"),
                "tokens_aprox": r.get("tokens_aprox"), "metodo": r.get("metodo"),
            }, ensure_ascii=False) + "\n")
    chars = sum(int(r.get("caracteres") or 0) for r in incorporadas)
    por_tipo: dict[str, list] = {}
    for r in incorporadas:
        por_tipo.setdefault(r.get("tipo", "otro"), []).append(r)
    lineas = [
        "# Biblioteca ambiental — Tribunales Ambientales de Chile",
        "",
        "Markdown íntegro del **módulo de derecho ambiental**: libros del Concurso Nacional de",
        "Comentarios de Sentencias (3TA), informes en derecho (2TA), foros de justicia ambiental,",
        "manuales y material docente. Los PDF se conservan en `biblioteca_ambiental/pdf/` y en",
        "`ambiental/` (material del usuario); los `.md` se publican en Hugging Face.",
        "",
        f"**Cobertura:** {len(incorporadas)} documentos · {chars:,} caracteres · "
        f"{chars // 4:,} tokens aprox. · cita: `[Hugging Face - biblioteca_ambiental/<archivo>.md]`",
        "",
        "Los PPTX y DOC del material docente (presentaciones de clases) quedan fuera de esta",
        "colección y se declaran como pendientes.",
        "",
    ]
    for tipo, regs in por_tipo.items():
        lineas.append(f"### {TIPO_LEGIBLE.get(tipo, tipo)} ({len(regs)})")
        lineas.append("")
        lineas.append("| Documento | Autor / Rol | Archivo | Caracteres |")
        lineas.append("|---|---|---|---|")
        for r in sorted(regs, key=lambda x: str(x.get("numero") or x.get("titulo"))):
            autor = r.get("autor") or ""
            if r.get("rol"):
                autor = f"{r['rol']} — {autor}".strip(" —")
            lineas.append(f"| {r.get('titulo', '')} | {autor} | `{r['archivo_md'].split('/')[-1]}` | {int(r.get('caracteres') or 0):,} |")
        lineas.append("")
    (DIR_MD / "README.md").write_text("\n".join(lineas), encoding="utf-8")


# ── Armado de la lista de trabajos ─────────────────────────────────────────────────────────

def _sha256(ruta: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def materiales(aplicar_dedupe: bool = True) -> list[dict]:
    filas: list[dict] = []
    for numero, (titulo, url) in sorted(LIBROS_CONCURSO.items()):
        filas.append({"tipo": "libro_concurso", "numero": numero, "titulo": titulo, "url_pdf": url,
                      "tribunal": "3TA", "tribunal_nombre": "Tercer Tribunal Ambiental de Valdivia"})
    for numero, rol, titulo, autor, url in INFORMES:
        filas.append({"tipo": "informe", "numero": numero, "rol": rol,
                      "titulo": f"{titulo} — {rol} — {autor}" if rol else f"{titulo} — {autor}",
                      "autor": autor, "url_pdf": url,
                      "tribunal": "2TA", "tribunal_nombre": "Segundo Tribunal Ambiental de Santiago"})
    for slug_, titulo, url in FOROS:
        filas.append({"tipo": "foro", "slug": slug_, "titulo": titulo, "url_pdf": url,
                      "tribunal": "2TA", "tribunal_nombre": "Segundo Tribunal Ambiental de Santiago"})
    for stem, titulo, archivo in LIBROS_LOCALES:
        ruta = AMBIENTAL / archivo
        filas.append({"tipo": "libro", "stem": stem, "titulo": titulo, "ruta_pdf": str(ruta),
                      "origen": "ambiental/"})
    if EXTRAIDO.exists():
        for pdf in sorted(EXTRAIDO.rglob("*.pdf")):
            if not pdf.is_file():
                continue
            origen = str(pdf.parent.relative_to(EXTRAIDO))
            filas.append({"tipo": "docencia", "stem": pdf.stem, "titulo": pdf.stem.replace("_", " ").strip(),
                          "ruta_pdf": str(pdf), "origen": origen})

    if aplicar_dedupe:
        vistos: dict[str, str] = {}
        unicas: list[dict] = []
        nombres: set[str] = set()
        for reg in filas:
            ruta = pathlib.Path(reg.get("ruta_pdf") or (DIR_PDF / f"{nombre_archivo(reg)}.pdf"))
            if ruta.exists() and ruta.is_file():
                sha = _sha256(ruta)
                if sha in vistos:
                    print(f"  · duplicado de {vistos[sha]}: {ruta.name}")
                    continue
                vistos[sha] = ruta.name
            nombre = nombre_archivo(reg)
            if nombre in nombres:
                sufijo = _sha256(ruta)[:6] if ruta.exists() else "dup"
                nombre = f"{nombre}-{sufijo}"
            nombres.add(nombre)
            reg["nombre"] = nombre
            unicas.append(reg)
        filas = unicas
    return filas


def main() -> int:
    ap = argparse.ArgumentParser(description="Convierte a Markdown la biblioteca ambiental.")
    ap.add_argument("--limite", type=int, default=0, help="procesar solo las primeras N (prueba)")
    args = ap.parse_args()
    DIR_MD.mkdir(parents=True, exist_ok=True)
    DIR_PDF.mkdir(parents=True, exist_ok=True)
    filas = materiales()
    pendientes = [(i, r) for i, r in enumerate(filas)]
    if args.limite:
        pendientes = pendientes[: args.limite]
    print(f"══ {len(pendientes)} documentos de la biblioteca ambiental por convertir (4 en paralelo)")

    ok = saltadas = fallidas = 0
    with ThreadPoolExecutor(max_workers=TRABAJADORES) as pool:
        futuros = {pool.submit(procesar, item): item for item in pendientes}
        for fut in as_completed(futuros):
            idx, resultado = fut.result()
            partes = resultado.split("|")
            estado, nombre = partes[0], partes[1]
            reg = filas[idx]
            reg["archivo_md"] = f"biblioteca_ambiental/{nombre}.md"
            if estado == "ok":
                ok += 1
                reg["caracteres"] = int(partes[2])
                reg["tokens_aprox"] = int(partes[2]) // 4
                reg["metodo"] = partes[3]
                try:
                    reg["paginas_pdf"] = int(partes[4]) or None
                except (IndexError, ValueError):
                    pass
                print(f"  ✓ {nombre} · {int(partes[2]):,} chars · {partes[3]}")
            elif estado == "saltada":
                saltadas += 1
                if len(partes) > 2 and partes[2].isdigit() and not reg.get("caracteres"):
                    reg["caracteres"] = int(partes[2])
                    reg["tokens_aprox"] = int(partes[2]) // 4
                    reg["metodo"] = "ya estaba"
                    print(f"  · {nombre} · {int(partes[2]):,} chars (ya estaba)")
            else:
                fallidas += 1
                print(f"  [!] {nombre}: {partes[2] if len(partes) > 2 else ''}")

    escribir_salidas(filas)
    print(f"══ listo: {ok} convertidas · {saltadas} ya estaban · {fallidas} con problema")
    print(f"   → {DIR_MD} · índice: {INDICE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
