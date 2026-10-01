#!/usr/bin/env python3
"""
ingestar_rchdcp_uct.py — Ingesta integral de la Revista Chilena de Derecho y Ciencia Política
(Universidad Católica de Temuco, 2010-2026).

Cosecha la colección completa de artículos vía OAI-PMH oficial (336 artículos),
extrae metadata estructurada, descarga los PDFs con safe_urlopen, convierte a Markdown canónico
token-optimizado RAE/ASALE con corchetes de citación [RChDCP - Vol. X N° Y (Año), Autor, Título],
y sincroniza con Hugging Face Hub y LegalGraphify.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import pathlib
import re
import shutil
import subprocess  # nosec B404
import sys
import tempfile
import time
import urllib.request
from typing import Any, Dict, List, Optional

import defusedxml.ElementTree as ET

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))
from config import safe_urlopen
from online_library_sync import resolver_token_hf

DATA_DIR = ROOT_DIR / "data" / "rchdcp"
DATA_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR = DATA_DIR / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = ROOT_DIR / "doctrina" / "revistas" / "rchdcp"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CATALOGO_RCHDCP = DATA_DIR / "catalogo_articulos.jsonl"

OAI_URL = "https://derechoycienciapolitica.uct.cl/index.php/RDCP/oai"
ISSN_PRINT = "0718-9389"
ISSN_ELEC = "0719-2150"

NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
}

AREAS_KEYWORDS = {
    "constitucional_politico": [
        "constitucion", "constitucional", "democracia", "partidos politicos", "sistema electoral",
        "presidencialismo", "gobierno", "derecho politico", "ciencia politica", "parlamento", "ciudadania",
        "regimen politico", "poder judicial", "separacion de poderes"
    ],
    "derechos_humanos_indigena": [
        "derechos humanos", "pueblos originarios", "indigena", "convenio 169", "oit", "corte interamericana",
        "corte idh", "igualdad", "no discriminacion", "pueblo mapuche", "interculturalidad", "migracion"
    ],
    "administrativo_ambiental": [
        "derecho administrativo", "acto administrativo", "servicio publico", "probidad", "contraloria",
        "ambiental", "medio ambiente", "recursos naturales", "aguas", "sancionatorio administrativo"
    ],
    "penal_criminologia": [
        "derecho penal", "delito", "pena", "responsabilidad penal", "tipicidad", "culpabilidad",
        "criminologia", "proceso penal", "cpp", "garantias penales", "carcel", "sistema penitenciario"
    ],
    "internacional": [
        "derecho internacional", "tratado internacional", "soberania", "relaciones internacionales",
        "corte internacional", "integracion regional", "derecho comparado"
    ],
    "civil_obligaciones": [
        "obligacion", "contrato", "responsabilidad civil", "danos", "incumplimiento", "clausula penal",
        "resolucion", "remedios contractuales", "buena fe", "culpa", "caso fortuito", "fuerza mayor"
    ],
    "civil_bienes": [
        "propiedad", "dominio", "posesion", "prescripcion adquisitiva", "reivindicatoria", "usufructo",
        "servidumbre", "hipoteca", "prenda", "bienes", "cbr", "tradicion", "estudio de titulos"
    ],
    "civil_familia_sucesorio": [
        "familia", "matrimonio", "divorcio", "filiacion", "alimentos", "cuidado personal", "herencia",
        "testamento", "sucesorio", "legitima", "particion", "indignidad sucesoria"
    ],
    "consumidor": [
        "consumidor", "ley 19.496", "sernac", "clausula abusiva", "publicidad enganosa", "garantia legal",
        "interes colectivo", "accion colectiva", "sobreendeudamiento"
    ],
    "comercial_societario": [
        "codigo de comercio", "sociedad", "spa", "sociedad anonima", "gobierno corporativo", "directores",
        "quiebra", "concursal", "insolvencia", "titulos de credito", "letra de cambio", "pagare", "seguros"
    ],
    "procesal_civil": [
        "codigo de procedimiento civil", "cpc", "demanda", "excepcion", "prueba", "sentencia",
        "recurso de apelacion", "casacion", "arbitraje", "cosa juzgada", "ejecucion forzada"
    ],
    "teoria_general": [
        "acto juridico", "autonomia privada", "abuso del derecho", "teoria del negocio juridico",
        "interpretacion del contrato", "principios del derecho", "filosofia del derecho", "hermeneutica"
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
    """Normaliza nombres de autores a formato Capitalizado."""
    if not autor_raw or not autor_raw.strip():
        return "Universidad Católica de Temuco"
    partes = [p.strip() for p in autor_raw.split(",") if p.strip()]
    if not partes:
        return autor_raw
    partes_formateadas = []
    for parte in partes:
        if parte.isupper() and len(parte) > 2:
            partes_formateadas.append(parte.title())
        else:
            partes_formateadas.append(parte)
    return ", ".join(partes_formateadas)


def inferir_area(titulo: str, texto: str) -> str:
    corpus = f"{titulo} {texto[:4000]}".lower()
    puntajes: Dict[str, int] = {}
    for area, kw_list in AREAS_KEYWORDS.items():
        score = sum(1 for kw in kw_list if kw in corpus)
        if score > 0:
            puntajes[area] = score
    if not puntajes:
        return "Derecho y Ciencia Política (General)"
    area_ganadora = max(puntajes, key=lambda k: puntajes[k])
    mapeo = {
        "constitucional_politico": "Derecho Constitucional y Ciencia Política",
        "derechos_humanos_indigena": "Derechos Humanos y Pueblos Originarios",
        "administrativo_ambiental": "Derecho Administrativo y Ambiental",
        "penal_criminologia": "Derecho Penal y Procesal Penal",
        "internacional": "Derecho Internacional y Relaciones Internacionales",
        "civil_obligaciones": "Derecho Civil (Obligaciones y Contratos)",
        "civil_bienes": "Derecho Civil (Bienes y Derechos Reales)",
        "civil_familia_sucesorio": "Derecho Civil (Familia y Sucesiones)",
        "consumidor": "Derecho del Consumo",
        "comercial_societario": "Derecho Comercial y Societario",
        "procesal_civil": "Derecho Procesal Civil",
        "teoria_general": "Teoría y Filosofía del Derecho",
    }
    return mapeo.get(area_ganadora, "Derecho y Ciencia Política (General)")


def extraer_normas_citadas(texto: str) -> List[str]:
    citas = set()
    patron_cc = re.findall(r"(?:art(?:[íi]culo)?\.?\s*)(\d+[\s\wº°]*)(?:del\s+c[oó]digo\s+civil)", texto, re.I)
    for c in patron_cc[:5]:
        num = re.match(r"\d+", c.strip())
        if num:
            citas.add(f"[BCN - Código Civil, Art. {num.group(0)}]")

    patron_cpc = re.findall(r"(?:art(?:[íi]culo)?\.?\s*)(\d+[\s\wº°]*)(?:del\s+c[oó]digo\s+de\s+procedimiento\s+civil|del\s+cpc)", texto, re.I)
    for c in patron_cpc[:5]:
        num = re.match(r"\d+", c.strip())
        if num:
            citas.add(f"[BCN - CPC, Art. {num.group(0)}]")

    patron_cpr = re.findall(r"(?:art(?:[íi]culo)?\.?\s*)(\d+[\s\wº°]*)(?:de\s+la\s+constituci[oó]n|de\s+la\s+cpr)", texto, re.I)
    for c in patron_cpr[:5]:
        num = re.match(r"\d+", c.strip())
        if num:
            citas.add(f"[CPR 1980 - Art. {num.group(0)}]")

    patron_cpp = re.findall(r"(?:art(?:[íi]culo)?\.?\s*)(\d+[\s\wº°]*)(?:del\s+c[oó]digo\s+procesal\s+penal|del\s+cpp)", texto, re.I)
    for c in patron_cpp[:5]:
        num = re.match(r"\d+", c.strip())
        if num:
            citas.add(f"[BCN - Código Procesal Penal, Art. {num.group(0)}]")

    patron_ley = re.findall(r"ley\s+(?:n[°º]?\s*)?(\d{2,5}\.?\d{0,3})", texto, re.I)
    for ley_match in patron_ley[:5]:
        limpio = ley_match.replace(".", "").strip()
        citas.add(f"[BCN - Ley N° {limpio}]")

    return sorted(list(citas))


def limpiar_texto_pdf(texto: str) -> str:
    """Normaliza texto extraído con pdftotext eliminando artefactos y encabezados reiterados."""
    texto = texto.replace("\x0c", "\n\n")
    texto = re.sub(r"[\x00-\x08\x0b\x0e-\x1f\x7f]", "", texto)
    texto = re.sub(r"(\w+)-\n(\w+)", r"\1\2", texto)
    texto = re.sub(r"Revista Chilena de Derecho y Ciencia Política.*?\n", "\n", texto, flags=re.I)
    texto = re.sub(r"\n\s*\d{1,4}\s*\n", "\n\n", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def cosechar_articulos_oai() -> List[Dict[str, Any]]:
    """Cosecha todos los artículos de la RChDCP a través del protocolo OAI-PMH."""
    print("  [*] Cosechando catálogo completo de la RChDCP vía OAI-PMH...")
    articulos: List[Dict[str, Any]] = []
    url: Optional[str] = f"{OAI_URL}?verb=ListRecords&metadataPrefix=oai_dc"
    lote = 1

    while url:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with safe_urlopen(req, timeout=30) as resp:
                xml_data = resp.read()
            root = ET.fromstring(xml_data)

            records = root.findall(".//oai:record", NS)
            print(f"    -> Lote {lote}: {len(records)} registros obtenidos...")

            for rec in records:
                header = rec.find("oai:header", NS)
                if header is not None and header.get("status") == "deleted":
                    continue

                metadata = rec.find(".//oai_dc:dc", NS)
                if metadata is None:
                    continue

                titles = [t.text.strip() for t in metadata.findall("dc:title", NS) if t.text and t.text.strip()]
                title = titles[0] if titles else ""
                if not title or title.lower() in ("editorial", "tabla de contenido", "índice", "sumario"):
                    continue

                creators = [c.text.strip() for c in metadata.findall("dc:creator", NS) if c.text and c.text.strip()]
                creator_str = creators[0] if creators else ""

                # Filtrar tomos completos agregados
                if re.match(r"^Vol\.?\s*\d+[\s,]*N[°º]?\s*\d+", title, re.I) and "derecho y ciencia política" in creator_str.lower():
                    continue

                subjects = [s.text.strip() for s in metadata.findall("dc:subject", NS) if s.text and s.text.strip()]
                sources = [s.text.strip() for s in metadata.findall("dc:source", NS) if s.text and s.text.strip()]
                relations = [r.text.strip() for r in metadata.findall("dc:relation", NS) if r.text and r.text.strip()]
                identifiers = [i.text.strip() for i in metadata.findall("dc:identifier", NS) if i.text and i.text.strip()]
                dates = [d.text.strip() for d in metadata.findall("dc:date", NS) if d.text and d.text.strip()]
                descriptions = [desc.text.strip() for desc in metadata.findall("dc:description", NS) if desc.text and desc.text.strip()]

                url_ojs = ""
                doi = ""
                art_id = ""
                for ident in identifiers:
                    if "article/view/" in ident:
                        url_ojs = ident
                        id_m = re.search(r"/article/view/(\d+)", ident)
                        if id_m:
                            art_id = id_m.group(1)
                    elif ident.startswith("10."):
                        doi = ident

                if not art_id:
                    oai_id = header.find("oai:identifier", NS) if header is not None else None
                    if oai_id is not None and oai_id.text:
                        id_m = re.search(r"article/(\d+)", oai_id.text)
                        if id_m:
                            art_id = id_m.group(1)

                if not art_id:
                    art_id = str(abs(hash(title)))[:8]

                pdf_download_url = ""
                for rel in relations:
                    if "/article/view/" in rel:
                        pdf_download_url = rel.replace("/article/view/", "/article/download/")
                        break

                volumen = "1"
                numero = "1"
                anio = None
                paginas = ""

                for src in sources:
                    v_m = re.search(r"Vol\.?\s*(\d+)", src, re.I)
                    if v_m:
                        volumen = v_m.group(1)
                    num_m = re.search(r"(?:Núm|No|n|N)[\.\s]*(\d+)", src, re.I)
                    if num_m:
                        numero = num_m.group(1)
                    anio_m = re.search(r"\((\d{4})\)", src)
                    if anio_m:
                        anio = int(anio_m.group(1))
                    p_m = re.search(r";\s*(\d+\s*-\s*\d+)", src)
                    if p_m:
                        paginas = p_m.group(1).replace(" ", "")

                if not anio and dates:
                    d_m = re.search(r"(\d{4})", dates[0])
                    if d_m:
                        anio_cand = int(d_m.group(1))
                        if 2010 <= anio_cand <= 2026:
                            anio = anio_cand

                if not anio:
                    try:
                        anio = 2009 + int(volumen)
                    except ValueError:
                        anio = 2010

                autores_fmt = "; ".join([formatear_autor(c) for c in creators]) if creators else "Universidad Católica de Temuco"
                resumen = descriptions[0] if descriptions else ""

                articulos.append({
                    "art_id": art_id,
                    "title": title,
                    "autores": autores_fmt,
                    "subjects": subjects,
                    "resumen": resumen,
                    "url_ojs": url_ojs,
                    "pdf_url": pdf_download_url,
                    "doi": doi,
                    "volumen": volumen,
                    "numero": numero,
                    "anio": anio,
                    "paginas": paginas,
                    "revista": "Revista Chilena de Derecho y Ciencia Política",
                })

            token_el = root.find(".//oai:resumptionToken", NS)
            if token_el is not None and token_el.text:
                token = token_el.text.strip()
                url = f"{OAI_URL}?verb=ListRecords&resumptionToken={token}"
                lote += 1
            else:
                url = None

        except Exception as e:
            print(f"    [!] Error en cosecha OAI lote {lote}: {e}")
            break

    # Ordenar cronológicamente
    articulos.sort(key=lambda x: (x["anio"], int(x["volumen"]) if x["volumen"].isdigit() else 0, int(x["numero"]) if x["numero"].isdigit() else 0, x["art_id"]))
    print(f"  ✓ {len(articulos)} artículos cosechados con éxito (años {articulos[0]['anio']} a {articulos[-1]['anio']}).")
    return articulos


def procesar_articulo(art: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Descarga el PDF, extrae el texto y genera el Markdown canónico."""
    art_id = art["art_id"]
    anio = art["anio"]
    volumen = art["volumen"]
    numero = art["numero"]
    paginas = art.get("paginas", "")
    title = art["title"]
    autores = art["autores"]
    pdf_url = art["pdf_url"]
    doi = art.get("doi", "")
    url_ojs = art["url_ojs"]
    resumen = art.get("resumen", "")
    subjects = art.get("subjects", [])

    slug = slugify(title)
    if not slug:
        slug = f"articulo_{art_id}"
    md_filename = f"rchdcp_{anio}_v{volumen}_n{numero}_{art_id}_{slug}.md"

    year_dir = OUTPUT_DIR / str(anio)
    year_dir.mkdir(parents=True, exist_ok=True)
    target_md = year_dir / md_filename

    if target_md.exists() and target_md.stat().st_size > 1024:
        return {"art_id": art_id, "anio": anio, "md_path": target_md, "nuevo": False}

    texto_cuerpo = ""
    if pdf_url:
        try:
            req = urllib.request.Request(pdf_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with safe_urlopen(req, timeout=30) as resp:
                pdf_bytes = resp.read()
            if len(pdf_bytes) > 1000 and pdf_bytes.startswith(b"%PDF"):
                with tempfile.NamedTemporaryFile(suffix=".pdf") as tf:
                    tf.write(pdf_bytes)
                    tf.flush()
                    pdftotext_bin = shutil.which("pdftotext") or "/usr/bin/pdftotext"
                    res = subprocess.run(  # nosec B603
                        [pdftotext_bin, tf.name, "-"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if res.returncode == 0 and res.stdout.strip():
                        texto_cuerpo = limpiar_texto_pdf(res.stdout)
        except Exception as e:
            print(f"    [!] Error al descargar/extraer PDF art_id={art_id} ({pdf_url}): {e}")

    if not texto_cuerpo:
        # Fallback a resumen
        texto_cuerpo = (
            f"{resumen}\n\n"
            f"Nota de archivo: Texto íntegro disponible en la edición oficial en PDF.\n"
            f"Repositorio oficial: {url_ojs}"
        )

    area = inferir_area(title, texto_cuerpo)
    normas = extraer_normas_citadas(texto_cuerpo)

    cita_oficial = f"[RChDCP - Vol. {volumen} N° {numero} ({anio}), {autores}, {title}]"

    frontmatter = [
        "---",
        f'titulo: "{title}"',
        f'autores: "{autores}"',
        'revista: "Revista Chilena de Derecho y Ciencia Política"',
        'institucion: "Universidad Católica de Temuco"',
        f'issn_impreso: "{ISSN_PRINT}"',
        f'issn_electronico: "{ISSN_ELEC}"',
        f"anio: {anio}",
        f'volumen: "{volumen}"',
        f'numero: "{numero}"',
        f'paginas: "{paginas}"',
        f'area_derecho: "{area}"',
        f'doi: "{doi}"',
        f'url_ojs: "{url_ojs}"',
        f'cita_oficial: "{cita_oficial}"',
        "normas_citadas:",
    ]
    for n in normas:
        frontmatter.append(f'  - "{n}"')
    frontmatter.append("---\n")

    secciones_extra = []
    if resumen:
        secciones_extra.append(f"## Resumen\n\n{resumen}\n")
    if subjects:
        kw_str = ", ".join(subjects)
        secciones_extra.append(f"## Palabras Clave\n\n{kw_str}\n")

    extra_bloque = "\n".join(secciones_extra) + "\n---\n" if secciones_extra else ""

    md_content = (
        "\n".join(frontmatter)
        + f"\n# {title}\n\n"
        f"> **Cita canónica:** `{cita_oficial}`  \n"
        f"> **Publicación oficial:** Revista Chilena de Derecho y Ciencia Política, Universidad Católica de Temuco.  \n"
        f"> **Identificador DOI:** `{doi}` | **URL:** {url_ojs}\n\n"
        f"{extra_bloque}\n"
        f"## Texto del Artículo\n\n{texto_cuerpo}\n"
    )

    target_md.write_text(md_content, encoding="utf-8")
    return {"art_id": art_id, "anio": anio, "md_path": target_md, "nuevo": True}


def subir_articulos_a_huggingface(repo_id: str = "pablobenavidesj/doctrina-jurisprudencia-chile") -> bool:
    """Sube la colección RChDCP al dataset de Hugging Face Hub."""
    token = resolver_token_hf()
    if not token:
        print("  [!] No se encontró HF_TOKEN en el entorno o en el almacén seguro.")
        return False

    from huggingface_hub import HfApi
    api = HfApi(token=token)

    print(f"  [*] Subiendo artículos RChDCP (2010-2026) a Hugging Face: {repo_id}...")
    try:
        api.upload_folder(
            folder_path=str(OUTPUT_DIR),
            repo_id=repo_id,
            repo_type="dataset",
            path_in_repo="doctrina/revistas/rchdcp",
            commit_message="feat(doctrina): ingesta de Revista Chilena de Derecho y Ciencia Política (UCT, 2010-2026)",
        )
        print("  ✓ Carpeta doctrina/revistas/rchdcp subida con éxito a Hugging Face.")
        return True
    except Exception as e:
        print(f"  [!] Error al subir a Hugging Face: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Ingesta de la Revista Chilena de Derecho y Ciencia Política (2010-2026)")
    parser.add_argument("--solo-cosecha", action="store_true", help="Solo cosechar catálogo de artículos sin descargar")
    parser.add_argument("--subir-hf", action="store_true", help="Subir artículos convertidos a Hugging Face Hub")
    parser.add_argument("--workers", type=int, default=10, help="Número de hilos para descarga y procesamiento")
    parser.add_argument("--limite", type=int, default=0, help="Límite de artículos a procesar (0 para todos)")
    args = parser.parse_args()

    print("=" * 70)
    print("  INGESTA: REVISTA CHILENA DE DERECHO Y CIENCIA POLÍTICA (UCT, 2010-2026)")
    print("=" * 70)

    # 1. Cosechar vía OAI-PMH
    articulos = cosechar_articulos_oai()

    # Guardar catálogo
    with open(CATALOGO_RCHDCP, "w", encoding="utf-8") as f:
        for art in articulos:
            f.write(json.dumps(art, ensure_ascii=False) + "\n")
    print(f"  ✓ Catálogo guardado en {CATALOGO_RCHDCP.relative_to(ROOT_DIR)}")

    if args.solo_cosecha:
        print("  [i] Modo --solo-cosecha activado. Finalizando.")
        return

    # 2. Descargar y procesar artículos
    articulos_a_procesar = articulos[:args.limite] if args.limite > 0 else articulos
    print(f"\n  [*] Procesando {len(articulos_a_procesar)} artículos con {args.workers} workers...")

    procesados = 0
    nuevos = 0
    t0 = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futuros = {executor.submit(procesar_articulo, art): art for art in articulos_a_procesar}
        for fut in concurrent.futures.as_completed(futuros):
            procesados += 1
            res = fut.result()
            if res and res.get("nuevo"):
                nuevos += 1
            if procesados % 50 == 0 or procesados == len(articulos_a_procesar):
                elapsed = time.time() - t0
                tasa = procesados / elapsed if elapsed > 0 else 0
                print(f"    -> {procesados}/{len(articulos_a_procesar)} artículos procesados ({nuevos} nuevos, {tasa:.1f} art/seg)...")

    print(f"  ✓ Conversión finalizada: {procesados} artículos procesados en {time.time() - t0:.1f}s.")

    # 3. Regenerar catálogos
    print("  [*] Generando dataset base train.jsonl para indexación de obras...")
    from online_library_sync import OnlineLibrarySyncManager
    mgr = OnlineLibrarySyncManager()
    mgr.generar_dataset_train_jsonl()

    print("  [*] Regenerando catálogos ligeros y de citas...")
    subprocess.run([sys.executable, str(ROOT_DIR / "scripts" / "optimizar_catalogo_hf.py")], cwd=str(ROOT_DIR), check=True)  # nosec B603

    # 4. Subida opcional a Hugging Face
    if args.subir_hf:
        subir_articulos_a_huggingface()
        token = resolver_token_hf()
        if token:
            from huggingface_hub import HfApi
            api = HfApi(token=token)
            repo_id = "pablobenavidesj/doctrina-jurisprudencia-chile"
            archivos_catalogo = [
                (ROOT_DIR / "data" / "catalogo" / "train_lite.jsonl", "data/catalogo/train_lite.jsonl"),
                (ROOT_DIR / "data" / "catalogo" / "instituciones_lite.jsonl", "data/catalogo/instituciones_lite.jsonl"),
                (ROOT_DIR / "data" / "catalogo" / "indice_citas.jsonl", "data/catalogo/indice_citas.jsonl"),
                (ROOT_DIR / "data" / "catalogo" / "indice_agentes.json", "data/catalogo/indice_agentes.json"),
                (ROOT_DIR / "llms.txt", "llms.txt"),
            ]
            for local_path, repo_path in archivos_catalogo:
                if local_path.exists():
                    try:
                        api.upload_file(
                            path_or_fileobj=str(local_path),
                            path_in_repo=repo_path,
                            repo_id=repo_id,
                            repo_type="dataset",
                            commit_message=f"chore(catalogo): sincronizar {repo_path} con RChDCP",
                        )
                        print(f"  ✓ {repo_path} actualizado en Hugging Face.")
                    except Exception as e:
                        print(f"  [!] Error al subir {repo_path}: {e}")

    print("\n" + "=" * 70)
    print("  INGESTA RChDCP COMPLETADA CON ÉXITO")
    print("=" * 70)


if __name__ == "__main__":
    main()
