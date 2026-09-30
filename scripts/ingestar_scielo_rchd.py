#!/usr/bin/env python3
"""
ingestar_scielo_rchd.py — Ingesta integral para la Revista Chilena de Derecho (RChD, UC).
Descarga vía repositorio oficial SciELO CONICYT (ISSN 0718-3437, 2006-2026),
convierte a Markdown canónico token-optimizado RAE/ASALE, genera citas estructuradas,
y prepara la sincronización con LegalGraphify y Hugging Face Hub.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

import defusedxml.ElementTree as ET

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))
from config import safe_urlopen
from online_library_sync import resolver_token_hf

DATA_DIR = ROOT_DIR / "data" / "rchd"
SCIELO_PDF_DIR = DATA_DIR / "pdfs_scielo"
OUTPUT_DIR = ROOT_DIR / "doctrina" / "revistas" / "rchd"
MANIFEST_SCIELO = DATA_DIR / "catalogo_articulos.jsonl"

OAI_SCIELO = "https://scielo.conicyt.cl/oai/scielo-oai.php"
ISSN_RCHD = "0718-3437"
NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
}

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


def slugify(texto: str, max_len: int = 60) -> str:
    texto = texto.lower()
    texto = re.sub(r"[áàäâ]", "a", texto)
    texto = re.sub(r"[éèëê]", "e", texto)
    texto = re.sub(r"[íìïî]", "i", texto)
    texto = re.sub(r"[óòöô]", "o", texto)
    texto = re.sub(r"[úùüû]", "u", texto)
    texto = re.sub(r"ñ", "n", texto)
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return texto.strip("_")[:max_len]


def formatear_autor(autor_raw: str) -> str:
    """Normaliza nombres como 'VERGARA BLANCO,ALEJANDRO' a 'Vergara Blanco, Alejandro'."""
    partes = [p.strip() for p in autor_raw.split(",") if p.strip()]
    if not partes:
        return autor_raw
    partes_formateadas = []
    for parte in partes:
        if parte.isupper() and len(parte) > 2:
            parte = parte.title()
        partes_formateadas.append(parte)
    return ", ".join(partes_formateadas)


def cosechar_catalogo_scielo(forzar: bool = False) -> List[Dict[str, Any]]:
    """Descarga todos los registros OAI-PMH de la Revista Chilena de Derecho en SciELO CONICYT."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not forzar and MANIFEST_SCIELO.exists() and MANIFEST_SCIELO.stat().st_size > 1000:
        with open(MANIFEST_SCIELO, "r", encoding="utf-8") as f:
            articulos = [json.loads(line) for line in f if line.strip()]
        print(f"[*] Catálogo SciELO RChD cargado desde disco: {len(articulos)} artículos.")
        return articulos

    print(f"[*] Cosechando catálogo SciELO CONICYT para Revista Chilena de Derecho (ISSN {ISSN_RCHD})...")
    articulos = []
    url = f"{OAI_SCIELO}?verb=ListRecords&metadataPrefix=oai_dc&set={ISSN_RCHD}"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) OpenLegalChile/1.0"}
    batch = 1

    while True:
        req = urllib.request.Request(url, headers=headers)
        with safe_urlopen(req, timeout=30) as resp:
            tree = ET.parse(resp)
        root = tree.getroot()
        records = root.findall(".//oai:record", NS)

        for rec in records:
            header = rec.find("oai:header", NS)
            if header is None or header.attrib.get("status") == "deleted":
                continue

            ident_elem = header.find("oai:identifier", NS)
            raw_id = ident_elem.text.strip() if ident_elem is not None and ident_elem.text else ""
            pid_match = re.search(r"(S\d{4}-\d{4}\d+)", raw_id)
            pid = pid_match.group(1) if pid_match else raw_id.split(":")[-1]

            metadata = rec.find("oai:metadata", NS)
            if metadata is None:
                continue
            dc = metadata.find("oai_dc:dc", NS)
            if dc is None:
                continue

            titles = [t.text.strip() for t in dc.findall("dc:title", NS) if t.text]
            title = titles[0] if titles else "Sin Título"
            creators_raw = [c.text.strip() for c in dc.findall("dc:creator", NS) if c.text]
            creators = [formatear_autor(c) for c in creators_raw]
            descriptions = [d.text.strip() for d in dc.findall("dc:description", NS) if d.text]
            abstract = descriptions[0] if descriptions else ""
            subjects = [s.text.strip() for s in dc.findall("dc:subject", NS) if s.text]
            sources = [s.text.strip() for s in dc.findall("dc:source", NS) if s.text]
            source = sources[0] if sources else ""
            dates = [d.text.strip() for d in dc.findall("dc:date", NS) if d.text]
            date_pub = dates[0] if dates else ""

            # Extraer volumen, número y año
            anio = ""
            vol = ""
            num = ""
            m_anio = re.search(r"\b(19\d{2}|20\d{2})\b", source or date_pub)
            if m_anio:
                anio = m_anio.group(1)
            m_vol = re.search(r"\bv\.(\d+)", source)
            if m_vol:
                vol = m_vol.group(1)
            m_num = re.search(r"\bn\.(\d+)", source)
            if m_num:
                num = m_num.group(1)

            articulos.append({
                "pid": pid,
                "title": title,
                "authors": creators,
                "abstract": abstract,
                "subjects": subjects,
                "source": source,
                "volumen": vol,
                "numero": num,
                "anio": anio,
                "date": date_pub,
                "url_scielo": f"https://www.scielo.cl/scielo.php?script=sci_arttext&pid={pid}",
                "url_sci_pdf": f"https://scielo.conicyt.cl/scielo.php?script=sci_pdf&pid={pid}",
            })

        token_elem = root.find(".//oai:resumptionToken", NS)
        if token_elem is not None and token_elem.text and token_elem.text.strip():
            url = f"{OAI_SCIELO}?verb=ListRecords&resumptionToken={token_elem.text.strip()}"
            print(f"  ✓ Lote {batch}: {len(records)} artículos procesados ({len(articulos)} acumulados)")
            batch += 1
            time.sleep(0.2)
        else:
            break

    with open(MANIFEST_SCIELO, "w", encoding="utf-8") as f:
        for a in articulos:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")

    print(f"[✓] Cosecha SciELO completada: {len(articulos)} artículos guardados en {MANIFEST_SCIELO}")
    return articulos


def resolver_y_descargar_pdf_scielo(articulo: Dict[str, Any]) -> Tuple[bool, str, Optional[pathlib.Path]]:
    """Resuelve la URL directa del PDF en SciELO CONICYT y lo guarda en disco."""
    pid = articulo.get("pid", "sin_pid")
    anio = articulo.get("anio") or "varios"
    subcarpeta = SCIELO_PDF_DIR / anio
    subcarpeta.mkdir(parents=True, exist_ok=True)
    slug = slugify(articulo.get("title", pid))
    destino = subcarpeta / f"{pid}_{slug}.pdf"

    if destino.exists() and destino.stat().st_size > 5120:
        return True, "ya_existe", destino

    url_sci = articulo.get("url_sci_pdf") or f"https://scielo.conicyt.cl/scielo.php?script=sci_pdf&pid={pid}"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

    try:
        req = urllib.request.Request(url_sci, headers=headers)
        with safe_urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # 1. Intentar redirección window.location
        m = re.search(r'window\.location="([^"]+\.pdf)"', html)
        if not m:
            # 2. Intentar enlace href directo
            m = re.search(r'href="([^"]+\.pdf)"', html)

        if not m:
            return False, f"No se encontró redirect PDF para {pid}", None

        pdf_url = m.group(1)
        if pdf_url.startswith("/"):
            pdf_url = "https://scielo.conicyt.cl" + pdf_url
        else:
            pdf_url = pdf_url.replace("http://www.scielo.cl/", "https://scielo.conicyt.cl/")

        req2 = urllib.request.Request(pdf_url, headers=headers)
        with safe_urlopen(req2, timeout=25) as resp2:
            pdf_bytes = resp2.read()

        if len(pdf_bytes) > 2048:
            with open(destino, "wb") as f_out:
                f_out.write(pdf_bytes)
            return True, f"descargado ({len(pdf_bytes)} bytes)", destino

        return False, "PDF vacío", None
    except Exception as e:
        return False, str(e), None


def extraer_texto_pdf(pdf_path: pathlib.Path) -> str:
    """Extrae texto desde PDF intentando pdftotext, luego PyMuPDF o pypdf."""
    # 1. Intentar pdftotext (layout limpio)
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

    # 2. PyMuPDF (fitz)
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

    # 3. pypdf
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


def extraer_texto_html_scielo(pid: str) -> str:
    """Extrae el cuerpo del artículo desde el HTML de sci_arttext en SciELO."""
    url = f"https://scielo.conicyt.cl/scielo.php?script=sci_arttext&pid={pid}"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with safe_urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        # Quitar scripts y estilos
        html = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
        # Convertir tags comunes
        html = re.sub(r"<p[^>]*>", "\n\n", html, flags=re.IGNORECASE)
        html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
        html = re.sub(r"<[^>]+>", "", html)
        texto = re.sub(r"\n{3,}", "\n\n", html).strip()
        return texto
    except Exception:
        return ""


def limpiar_texto_rchd(texto: str) -> str:
    """Limpia saltos de línea huérfanos, encabezados repetitivos y números de página."""
    texto = texto.replace("\x0c", "\n\n")
    texto = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", texto)

    patrones_encabezado = [
        r"Revista Chilena de Derecho.*?\n",
        r"Revista chilena de derecho.*?\n",
        r"RChD.*?\n",
        r"Pontificia Universidad Católica de Chile\s*Facultad de Derecho.*?\n",
    ]
    for p in patrones_encabezado:
        texto = re.sub(p, "", texto, flags=re.IGNORECASE)

    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


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


def extraer_instituciones_y_normas(texto: str) -> Tuple[List[str], List[str]]:
    """Detecta instituciones jurídicas clave y artículos de códigos chilenos citados."""
    normas = []
    instituciones = []

    citas_cc = re.findall(r"(?:art(?:ículo|\.)?\s*(\d+)\s*(?:inc(?:iso|\.)?\s*\d+)?\s*(?:del\s*)?(?:código civil|c\.?\s*c\.?))", texto, re.IGNORECASE)
    for c in citas_cc[:10]:
        normas.append(f"[BCN - Código Civil, Art. {c}]")

    citas_cpr = re.findall(r"(?:art(?:ículo|\.)?\s*(\d+)\s*(?:n[°º]?\s*\d+)?\s*(?:de la\s*)?(?:constitución|cpr))", texto, re.IGNORECASE)
    for c in citas_cpr[:5]:
        normas.append(f"[CPR 1980 - Art. {c}]")

    citas_ley = re.findall(r"(?:ley\s*n?[°º]?\s*(\d{2}\.\d{3}))", texto, re.IGNORECASE)
    for c in citas_ley[:5]:
        normas.append(f"[BCN - Ley N° {c}]")

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


def procesar_articulo_rchd(articulo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Descarga el PDF de SciELO y genera su Markdown canónico para RChD."""
    pid = articulo.get("pid", "sin_pid")
    anio = articulo.get("anio") or "varios"
    slug = slugify(articulo.get("title", pid))

    out_file = OUTPUT_DIR / anio / f"{pid}_{slug}.md"
    if out_file.exists() and out_file.stat().st_size > 500:
        return {"status": "ya_existe", "pid": pid, "output_path": str(out_file)}

    texto_raw = ""
    ok, msg, pdf_path = resolver_y_descargar_pdf_scielo(articulo)
    if ok and pdf_path and pdf_path.exists():
        texto_raw = extraer_texto_pdf(pdf_path)

    # Si pdftotext no obtuvo suficiente texto, intentar HTML de SciELO
    if not texto_raw or len(texto_raw.strip()) < 200:
        texto_html = extraer_texto_html_scielo(pid)
        if len(texto_html.strip()) > 300:
            texto_raw = texto_html

    # Si aún no tenemos texto íntegro, recurrir al abstract
    if not texto_raw or len(texto_raw.strip()) < 100:
        abstract = articulo.get("abstract", "")
        if abstract and len(abstract) > 80:
            texto_raw = f"{abstract}\n\n[Texto completo disponible en SciELO: {articulo.get('url_scielo')}]"
        else:
            return {"status": "error_extraccion", "pid": pid, "error": msg}

    texto_limpio = limpiar_texto_rchd(texto_raw)
    area = inferir_area(articulo.get("title", ""), texto_limpio)
    instituciones, normas = extraer_instituciones_y_normas(texto_limpio)

    autores = articulo.get("authors", [])
    autores_str = ", ".join(autores) if autores else "Doctrina Nacional"
    primer_autor = autores[0] if autores else "Doctrina Nacional"
    titulo = articulo.get("title", "Artículo sin título").strip()
    volumen = articulo.get("volumen", "")
    numero = articulo.get("numero", "")
    url_orig = articulo.get("url_scielo", "")

    # Cita canónica
    if volumen and numero and anio:
        cita_canonica = f"[RChD - Vol. {volumen} N° {numero} ({anio}), {primer_autor}, {titulo[:45]}...]"
    elif volumen and anio:
        cita_canonica = f"[RChD - Vol. {volumen} ({anio}), {primer_autor}, {titulo[:45]}...]"
    else:
        cita_canonica = f"[RChD - {primer_autor}, {titulo[:45]}...]"

    md_content = f"""---
id: "rchd_scielo_{pid}"
titulo: {json.dumps(titulo, ensure_ascii=False)}
autor: {json.dumps(autores_str, ensure_ascii=False)}
primer_autor: {json.dumps(primer_autor, ensure_ascii=False)}
revista: "Revista Chilena de Derecho"
institucion: "Pontificia Universidad Católica de Chile"
issn: "0718-3437"
volumen: {json.dumps(str(volumen))}
numero: {json.dumps(str(numero))}
anio: {anio or "null"}
fuente: {json.dumps(articulo.get('source', ''), ensure_ascii=False)}
area: {json.dumps(area)}
instituciones: {json.dumps(instituciones, ensure_ascii=False)}
normas_citadas: {json.dumps(normas, ensure_ascii=False)}
url_original: {json.dumps(url_orig)}
cita_canonica: {json.dumps(cita_canonica, ensure_ascii=False)}
---

# {titulo}

**Tratadista:** {primer_autor} | **Área:** {area.capitalize()} | **Materia:** {titulo[:60]}
**Autor(es):** {autores_str}  
**Revista:** Revista Chilena de Derecho (Pontificia Universidad Católica de Chile / SciELO)  
**Publicación:** {"Volumen " + volumen if volumen else ""} {"N° " + numero if numero else ""} ({anio})  
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

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    return {
        "status": "convertido",
        "pid": pid,
        "titulo": titulo,
        "area": area,
        "output_path": str(out_file),
    }


def ejecutar_ingesta_rchd(
    hilos: int = 8,
    limite: int = 0,
    forzar_cosecha: bool = False,
    subir_hf: bool = False,
    reindexar: bool = True,
) -> Dict[str, Any]:
    """Ejecuta la ingesta completa de la Revista Chilena de Derecho."""
    print("\n" + "=" * 70)
    print("🚀 INICIANDO INGESTA INTEGRAL: REVISTA CHILENA DE DERECHO (UC / SciELO)")
    print("=" * 70 + "\n")
    t0 = time.perf_counter()

    articulos = cosechar_catalogo_scielo(forzar=forzar_cosecha)
    if limite > 0:
        articulos = articulos[:limite]
        print(f"[*] Límite configurado: procesando {limite} artículos.")

    print(f"[*] Procesando {len(articulos)} artículos de RChD con {hilos} hilos concurrentes...")

    convertidos = 0
    ya_existentes = 0
    fallidos = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=hilos) as executor:
        futuros = {executor.submit(procesar_articulo_rchd, art): art for art in articulos}
        for i, fut in enumerate(concurrent.futures.as_completed(futuros), start=1):
            try:
                res = fut.result()
                if res and res.get("status") == "convertido":
                    convertidos += 1
                elif res and res.get("status") == "ya_existe":
                    ya_existentes += 1
                else:
                    fallidos += 1

                if i % 25 == 0 or i == len(articulos):
                    dur = round(time.perf_counter() - t0, 1)
                    print(f"  → Progreso RChD: {i}/{len(articulos)} ({convertidos} nuevos, {ya_existentes} cacheados, {fallidos} fallos) | {dur}s")
            except Exception as e:
                fallidos += 1
                print(f"  [!] Excepción en artículo: {e}")

    archivos_md = list(OUTPUT_DIR.glob("**/*.md"))
    print(f"\n[✓] Ingesta y conversión completada: {len(archivos_md)} artículos en Markdown en {OUTPUT_DIR}")

    if reindexar:
        print("\n[*] Reindexando FTS5 y actualizando LegalGraphify...")
        try:
            from doctrina_connector import index_all_doctrina
            total_fts = index_all_doctrina()
            print(f"  ✓ FTS5 actualizado: {total_fts} instituciones indexadas.")
        except Exception as e:
            print(f"  [!] Advertencia al indexar FTS5: {e}")

        try:
            from legal_graphify import DEFAULT_GRAPH_PATH, LegalGraphifyEngine
            engine = LegalGraphifyEngine(doctrina_dir=str(ROOT_DIR / "doctrina"))
            engine.construir_grafo_desde_doctrina()
            engine.guardar_grafo_json(DEFAULT_GRAPH_PATH)
            nodos = engine.graph.number_of_nodes()
            aristas = engine.graph.number_of_edges()
            print(f"  ✓ LegalGraphify actualizado ({nodos} nodos, {aristas} aristas).")
        except Exception as e:
            print(f"  [!] Advertencia LegalGraphify: {e}")

    if subir_hf:
        print("\n[*] Sincronizando con Hugging Face Dataset Hub...")
        token = resolver_token_hf()
        if not token:
            print("  [!] ERROR: No se encontró token de Hugging Face.")
        else:
            try:
                from huggingface_hub import HfApi
                api = HfApi(token=token)
                repo_id = "pablobenavidesj/doctrina-jurisprudencia-chile"

                # Regenerar catálogos
                print("  [*] Regenerando catálogos ligeros...")
                from online_library_sync import OnlineLibrarySyncManager
                mgr = OnlineLibrarySyncManager()
                mgr.generar_dataset_train_jsonl()

                # Ejecutar optimizar_catalogo_hf
                import subprocess
                subprocess.run([sys.executable, str(ROOT_DIR / "scripts" / "optimizar_catalogo_hf.py")], check=True)  # nosec B603

                print(f"  [*] Subiendo carpeta {OUTPUT_DIR} a {repo_id}...")
                api.upload_folder(
                    repo_id=repo_id,
                    folder_path=str(OUTPUT_DIR),
                    path_in_repo="doctrina/revistas/rchd",
                    commit_message=f"feat(doctrina): incorporar coleccion completa Revista Chilena de Derecho ({len(archivos_md)} articulos)",
                    commit_description="Ingesta masiva de la Revista Chilena de Derecho (Pontificia Universidad Católica de Chile / SciELO) con metadatos canonicales, citas legales y nodos de LegalGraphify.",
                    repo_type="dataset",
                )
                print("  ✓ Carpeta doctrina/revistas/rchd/ subida exitosamente a Hugging Face.")

                # Subir catálogos actualizados
                archivos_catalogo = [
                    (ROOT_DIR / "data" / "catalogo" / "train_lite.jsonl", "data/catalogo/train_lite.jsonl"),
                    (ROOT_DIR / "data" / "catalogo" / "instituciones_lite.jsonl", "data/catalogo/instituciones_lite.jsonl"),
                    (ROOT_DIR / "data" / "catalogo" / "indice_citas.jsonl", "data/catalogo/indice_citas.jsonl"),
                    (ROOT_DIR / "data" / "catalogo" / "indice_agentes.json", "data/catalogo/indice_agentes.json"),
                    (ROOT_DIR / "llms.txt", "llms.txt"),
                ]
                for local_f, repo_f in archivos_catalogo:
                    if local_f.exists():
                        api.upload_file(
                            path_or_fileobj=str(local_f),
                            path_in_repo=repo_f,
                            repo_id=repo_id,
                            repo_type="dataset",
                            commit_message=f"chore(catalogo): actualizar {local_f.name} con Revista Chilena de Derecho",
                        )
                        print(f"  ✓ {local_f.name} subido a Hugging Face.")

            except Exception as e:
                print(f"  [X] Error durante la subida a Hugging Face: {e}")

    dur_total = round(time.perf_counter() - t0, 1)
    print("\n" + "=" * 70)
    print(f"🎉 INGESTA RChD FINALIZADA en {dur_total} s ({round(dur_total / 60, 2)} min)")
    print("=" * 70 + "\n")

    return {
        "articulos_procesados": len(articulos),
        "convertidos": convertidos,
        "ya_existentes": ya_existentes,
        "fallidos": fallidos,
        "total_md": len(archivos_md),
    }


def main():
    parser = argparse.ArgumentParser(description="Ingesta y conversión de Revista Chilena de Derecho (UC / SciELO).")
    parser.add_argument("--hilos", type=int, default=8, help="Número de hilos concurrentes (default: 8).")
    parser.add_argument("--limite", type=int, default=0, help="Límite de artículos (0 = todos).")
    parser.add_argument("--forzar-cosecha", action="store_true", help="Volver a cosechar catálogo OAI-PMH.")
    parser.add_argument("--subir-hf", action="store_true", help="Subir a Hugging Face Dataset Hub tras la ingesta.")
    parser.add_argument("--no-reindexar", action="store_false", dest="reindexar", help="Omitir reindexación FTS5 y grafo.")
    args = parser.parse_args()

    ejecutar_ingesta_rchd(
        hilos=args.hilos,
        limite=args.limite,
        forzar_cosecha=args.forzar_cosecha,
        subir_hf=args.subir_hf,
        reindexar=args.reindexar,
    )


if __name__ == "__main__":
    main()
