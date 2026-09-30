#!/usr/bin/env python3
"""
convert_rdpucv_to_md.py — Conversor a Markdown canónico token-optimizado
de los artículos de la Revista de Derecho PUCV (Pro Jure).
Genera metadatos YAML enriquecidos, estandariza citas legales RAE/ASALE
y prepara las concordancias para LegalGraphify y Hugging Face.
"""

import argparse
import concurrent.futures
import json
import os
import pathlib
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

DATA_DIR = pathlib.Path(__file__).parent.parent / "data" / "rdpucv"
MANIFEST_PATH = DATA_DIR / "catalogo_articulos.jsonl"
PDF_DIR = DATA_DIR / "pdfs"
OUTPUT_DIR = pathlib.Path(__file__).parent.parent / "doctrina" / "revistas" / "rdpucv"

AREAS_KEYWORDS = {
    "civil": [
        "codigo civil", "contrato", "obligacion", "responsabilidad civil", "danos", "propiedad",
        "dominio", "posesion", "prescripcion", "herencia", "testamento", "sucesorio", "familia",
        "matrimonio", "arrendamiento", "compraventa", "hipoteca", "prenda", "bienes", "acto juridico"
    ],
    "constitucional": [
        "constitucion", "derecho fundamental", "recurso de proteccion", "tribunal constitucional",
        "soberania", "cpr", "derechos humanos", "garantias constitucionales", "accion de proteccion"
    ],
    "administrativo": [
        "administracion publica", "acto administrativo", "procedimiento administrativo", "cgr",
        "contraloria", "sancion administrativa", "urbanismo", "plan regulador", "expropiacion",
        "servicio publico", "desviacion de poder", "responsabilidad del estado", "ley 19.880"
    ],
    "comercial": [
        "codigo de comercio", "sociedad", "spa", "sociedad anonima", "concursal", "quiebra",
        "insolvencia", "titulos de credito", "letra de cambio", "pagare", "seguros", "consumidor"
    ],
    "laboral": [
        "codigo del trabajo", "trabajador", "empleador", "despido", "finiquito", "remuneracion",
        "huelga", "sindicato", "ley karin", "direccion del trabajo", "accidente del trabajo"
    ],
    "penal": [
        "codigo penal", "delito", "pena", "imputado", "culpabilidad", "tipicidad", "tentativa",
        "homicidio", "estafa", "lavado de activos", "corrupcion", "prescripcion penal"
    ],
    "procesal": [
        "codigo de procedimiento civil", "cpc", "demanda", "excepcion", "prueba", "sentencia",
        "recurso de apelacion", "casacion", "tribunal", "jurisdiccion", "debido proceso", "cpp"
    ],
    "ambiental": [
        "medio ambiente", "ley 19.300", "seia", "sma", "tribunal ambiental", "dano ambiental",
        "evaluacion de impacto ambiental", "humedal", "snifa", "norma de emision"
    ],
}


def inferir_area(titulo: str, texto: str) -> str:
    """Clasifica el artículo en un área dogmática según vocabulario y citas normativas."""
    corpus_eval = (titulo.lower() + " " + texto[:4000].lower())
    puntuaciones: Dict[str, int] = {area: 0 for area in AREAS_KEYWORDS}

    for area, kws in AREAS_KEYWORDS.items():
        for kw in kws:
            if kw in corpus_eval:
                puntuaciones[area] += 2 if kw in titulo.lower() else 1

    mejor_area = max(puntuaciones, key=puntuaciones.get)  # type: ignore
    return mejor_area if puntuaciones[mejor_area] > 0 else "civil"


def extraer_texto_pdf(pdf_path: pathlib.Path) -> str:
    """Extrae texto desde un PDF intentando primero pdftotext -layout, luego PyMuPDF (fitz)."""
    # 1. Intentar pdftotext (rápido y preserva espaciado columnar)
    try:
        proc = subprocess.run(  # nosec B603, B607
            ["pdftotext", "-layout", str(pdf_path), "-"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if proc.returncode == 0 and len(proc.stdout.strip()) > 300:
            return proc.stdout
    except Exception:
        pass

    # 2. Intentar PyMuPDF (fitz)
    try:
        import fitz  # type: ignore
        doc = fitz.open(str(pdf_path))
        paginas = [p.get_text() for p in doc]
        doc.close()
        texto = "\n\n".join(paginas).strip()
        if len(texto) > 300:
            return texto
    except Exception:
        pass

    # 3. Intentar pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(str(pdf_path))
        paginas = [p.extract_text() or "" for p in reader.pages]
        texto = "\n\n".join(paginas).strip()
        if len(texto) > 300:
            return texto
    except Exception:
        pass

    return ""


def limpiar_texto_articulo(texto: str) -> str:
    """Limpia saltos de línea huérfanos, numeración repetitiva y encabezados de página."""
    # Eliminar saltos de página form feed
    texto = texto.replace("\x0c", "\n\n")

    # Unir palabras cortadas con guion al final de línea (ej: "expro- \n piatoria" -> "expropiatoria")
    texto = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", texto)

    # Eliminar encabezados repetitivos de la revista
    patrones_encabezado = [
        r"Pro Jure Revista de Derecho.*?\n",
        r"Revista de Derecho de la Pontificia Universidad Católica de Valparaíso.*?\n",
        r"Revista de Derecho PUCV.*?\n",
    ]
    for p in patrones_encabezado:
        texto = re.sub(p, "", texto, flags=re.IGNORECASE)

    # Normalizar múltiples saltos de línea a máximo 2
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def extraer_instituciones_y_normas(texto: str) -> Tuple[List[str], List[str]]:
    """Detecta instituciones jurídicas clave y artículos de códigos chilenos citados."""
    normas = []
    instituciones = []

    # Normas: Código Civil, Código del Trabajo, etc.
    citas_cc = re.findall(r"(?:art(?:ículo|\.)?\s*(\d+)\s*(?:inc(?:iso|\.)?\s*\d+)?\s*(?:del\s*)?(?:código civil|c\.?\s*c\.?))", texto, re.IGNORECASE)
    for c in citas_cc[:10]:
        normas.append(f"[BCN - Código Civil, Art. {c}]")

    citas_cpr = re.findall(r"(?:art(?:ículo|\.)?\s*(\d+)\s*(?:n[°º]?\s*\d+)?\s*(?:de la\s*)?(?:constitución|cpr))", texto, re.IGNORECASE)
    for c in citas_cpr[:5]:
        normas.append(f"[CPR 1980 - Art. {c}]")

    citas_ley = re.findall(r"(?:ley\s*n?[°º]?\s*(\d{2}\.\d{3}))", texto, re.IGNORECASE)
    for c in citas_ley[:5]:
        normas.append(f"[BCN - Ley N° {c}]")

    # Instituciones
    vocabulario = [
        "Buena fe", "Responsabilidad contractual", "Responsabilidad extracontractual",
        "Daño moral", "Daño emergente", "Lucro cesante", "Cláusula penal",
        "Enriquecimiento sin causa", "Prescripción extintiva", "Dominio", "Posesión",
        "Tradición", "Acto jurídico", "Nulidad absoluta", "Nulidad relativa",
        "Desviación de poder", "Debido proceso", "Principio de legalidad",
        "Proporcionalidad", "Confianza legítima", "Fuerza mayor", "Caso fortuito"
    ]
    corpus_lower = texto.lower()
    for inst in vocabulario:
        if inst.lower() in corpus_lower:
            instituciones.append(inst)

    return list(dict.fromkeys(instituciones)), list(dict.fromkeys(normas))


def generar_markdown_articulo(
    articulo: Dict[str, Any],
    texto_raw: str,
    output_path: pathlib.Path,
) -> Dict[str, Any]:
    """Genera el archivo Markdown canónico estructurado y lo guarda en disco."""
    art_id = articulo.get("article_id", "sin_id")
    titulo = articulo.get("title", "Artículo sin título").strip()
    autores = articulo.get("authors", [])
    autores_str = ", ".join(autores) if autores else "Doctrina Nacional"
    primer_autor = autores[0] if autores else "Doctrina Nacional"
    volumen = articulo.get("volumen", "")
    anio = articulo.get("anio", "")
    fuente = articulo.get("fuente", "")
    url_orig = articulo.get("view_url", "")

    texto_limpio = limpiar_texto_articulo(texto_raw)
    area = inferir_area(titulo, texto_limpio)
    instituciones, normas = extraer_instituciones_y_normas(texto_limpio)

    cita_canonica = (
        f"[RDPUCV - Vol. {volumen} ({anio}), {primer_autor}, {titulo[:45]}...]"
        if volumen and anio
        else f"[RDPUCV - {primer_autor}, {titulo[:45]}...]"
    )

    tokens_aprox_orig = int(len(texto_raw.split()) * 1.3)
    tokens_aprox_md = int(len(texto_limpio.split()) * 1.3)
    ahorro_pct = round(((tokens_aprox_orig - tokens_aprox_md) / tokens_aprox_orig) * 100, 1) if tokens_aprox_orig > 0 else 0.0

    # Construcción de Markdown canónico con Frontmatter YAML completo
    md_content = f"""---
id: "rdpucv_art_{art_id}"
titulo: {json.dumps(titulo, ensure_ascii=False)}
autor: {json.dumps(autores_str, ensure_ascii=False)}
primer_autor: {json.dumps(primer_autor, ensure_ascii=False)}
revista: "Revista de Derecho de la Pontificia Universidad Católica de Valparaíso"
volumen: {json.dumps(str(volumen))}
anio: {anio or "null"}
fuente: {json.dumps(fuente, ensure_ascii=False)}
area: {json.dumps(area)}
instituciones: {json.dumps(instituciones, ensure_ascii=False)}
normas_citadas: {json.dumps(normas, ensure_ascii=False)}
url_original: {json.dumps(url_orig)}
cita_canonica: {json.dumps(cita_canonica, ensure_ascii=False)}
---

# {titulo}

**Autor(es):** {autores_str}  
**Revista:** Revista de Derecho de la Pontificia Universidad Católica de Valparaíso (Pro Jure)  
**Publicación:** Volumen {volumen} ({anio})  
**Área Dogmática:** {area.capitalize()}  
**Cita Canónica:** `{cita_canonica}`  
**Fuente Original:** [{url_orig}]({url_orig})

---

## 🏛️ Instituciones y Conceptos Jurídicos Relevantes
{', '.join(f'`{inst}`' for inst in instituciones) if instituciones else '_Análisis dogmático general_.'}

## ⚖️ Normas y Cuerpos Legales Citados
{chr(10).join(f'* {n}' for n in normas) if normas else '_Sin citas normativas directas identificadas en extracto_.'}

---

## Contenido del Artículo

{texto_limpio}
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return {
        "article_id": art_id,
        "titulo": titulo,
        "autor": autores_str,
        "area": area,
        "volumen": volumen,
        "anio": anio,
        "output_path": str(output_path),
        "tokens_original": tokens_aprox_orig,
        "tokens_md": tokens_aprox_md,
        "ahorro_tokens_pct": ahorro_pct,
        "instituciones": len(instituciones),
        "normas": len(normas),
    }


def procesar_un_articulo(articulo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Busca el PDF correspondiente a un artículo, lo extrae y genera su Markdown."""
    art_id = str(articulo.get("article_id", ""))
    anio = str(articulo.get("anio") or "sin_anio")
    volumen = str(articulo.get("volumen") or "vol_x")

    subcarpeta_pdf = PDF_DIR / f"vol_{volumen}_{anio}"
    if not subcarpeta_pdf.exists():
        return None

    candidatos = list(subcarpeta_pdf.glob(f"{art_id}_*.pdf"))
    if not candidatos:
        return None

    pdf_path = candidatos[0]
    out_dir_anio = OUTPUT_DIR / (anio if anio != "sin_anio" else "varios")
    slug = pdf_path.stem
    out_file = out_dir_anio / f"{slug}.md"

    if out_file.exists() and out_file.stat().st_size > 500:
        return {"status": "ya_existe", "article_id": art_id, "path": str(out_file)}

    texto = extraer_texto_pdf(pdf_path)
    if not texto or len(texto.strip()) < 100:
        return {"status": "error_extraccion", "article_id": art_id, "pdf": str(pdf_path)}

    meta = generar_markdown_articulo(articulo, texto, out_file)
    meta["status"] = "convertido"
    return meta


def procesar_todos_articulos(hilos: int = 4, limite: int = 0) -> Dict[str, Any]:
    """Procesa y convierte en paralelo todos los artículos disponibles en el catálogo."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Catálogo no encontrado: {MANIFEST_PATH}")

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        articulos = [json.loads(line) for line in f if line.strip()]

    if limite > 0:
        articulos = articulos[:limite]

    print(f"[*] Iniciando conversión a Markdown de {len(articulos)} artículos con {hilos} hilos...")
    t0 = time.perf_counter()
    convertidos = 0
    ya_existentes = 0
    fallidos = 0
    sin_pdf = 0
    total_tokens_orig = 0
    total_tokens_md = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=hilos) as executor:
        futuros = {executor.submit(procesar_un_articulo, art): art for art in articulos}
        for i, fut in enumerate(concurrent.futures.as_completed(futuros), start=1):
            art = futuros[fut]
            try:
                res = fut.result()
                if not res:
                    sin_pdf += 1
                elif res.get("status") == "ya_existe":
                    ya_existentes += 1
                elif res.get("status") == "convertido":
                    convertidos += 1
                    total_tokens_orig += res.get("tokens_original", 0)
                    total_tokens_md += res.get("tokens_md", 0)
                else:
                    fallidos += 1

                if i % 50 == 0 or i == len(articulos):
                    dur = round(time.perf_counter() - t0, 1)
                    print(f"  → Progreso: {i}/{len(articulos)} ({convertidos} convertidos, {ya_existentes} cacheados, {sin_pdf} sin PDF local) | {dur}s")

            except Exception as e:
                fallidos += 1
                print(f"  [!] Error procesando {art.get('article_id')}: {e}")

    duracion = round(time.perf_counter() - t0, 2)
    ahorro_total_pct = (
        round(((total_tokens_orig - total_tokens_md) / total_tokens_orig) * 100, 1)
        if total_tokens_orig > 0
        else 0.0
    )

    print("\n" + "=" * 60)
    print("RESUMEN DE CONVERSIÓN A MARKDOWN CANÓNICO:")
    print(f"  Total procesados: {len(articulos)}")
    print(f"  Convertidos exitosamente: {convertidos}")
    print(f"  Preexistentes: {ya_existentes}")
    print(f"  Sin PDF en disco: {sin_pdf}")
    print(f"  Fallidos: {fallidos}")
    print(f"  Tokens totales: {total_tokens_orig:,} → {total_tokens_md:,} (-{ahorro_total_pct}%)")
    print(f"  Tiempo transcurrido: {duracion} s")
    print("=" * 60)

    return {
        "convertidos": convertidos,
        "ya_existentes": ya_existentes,
        "sin_pdf": sin_pdf,
        "fallidos": fallidos,
        "duracion": duracion,
    }


def main():
    parser = argparse.ArgumentParser(description="Conversor de artículos RDPUCV a Markdown canónico.")
    parser.add_argument("--limite", type=int, default=0, help="Límite de artículos a procesar (0 = todos).")
    parser.add_argument("--hilos", type=int, default=4, help="Número de hilos concurrentes.")
    args = parser.parse_args()

    procesar_todos_articulos(hilos=args.hilos, limite=args.limite)


if __name__ == "__main__":
    main()
