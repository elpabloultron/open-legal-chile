#!/usr/bin/env python3
"""
ingestar_rchdt_uchile.py — Ingesta integral de la Revista Chilena de Derecho y Tecnología (RChDT)
(Facultad de Derecho, Universidad de Chile, 2012-2026).

Cosecha la colección completa de artículos vía OAI-PMH oficial (230+ artículos),
extrae metadata estructurada multilingüe, descarga los PDFs con safe_urlopen, convierte a Markdown canónico
token-optimizado RAE/ASALE con corchetes de citación [RChDT - Vol. X N° Y (Año), Autor, Título],
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
import unicodedata
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

import defusedxml.ElementTree as ET

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))
from config import safe_urlopen
from online_library_sync import resolver_token_hf

DATA_DIR = ROOT_DIR / "data" / "rchdt"
DATA_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR = DATA_DIR / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = ROOT_DIR / "doctrina" / "revistas" / "rchdt"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CATALOGO_RCHDT = DATA_DIR / "catalogo_articulos.jsonl"

OAI_URL = "https://rchdt.uchile.cl/index.php/RCHDT/oai"
ISSN_PRINT = "0719-2576"
ISSN_ELEC = "0719-2584"

NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
}

PALABRAS_ES = {
    "de", "la", "el", "en", "y", "los", "del", "las", "un", "por", "con", "una",
    "su", "para", "al", "lo", "como", "mas", "derecho", "ley", "chile", "sobre",
    "responsabilidad", "informacion", "proteccion", "datos", "inteligencia", "artificial",
    "software", "tecnologia", "digital", "juridico", "redes", "seguridad"
}

AREAS_KEYWORDS = {
    "derecho_tecnologia_ia": [
        "inteligencia artificial", "algoritmo", "algoritmico", "machine learning", "deep learning",
        "redes neuronales", "automatizacion", "robot", "robotica", "sistemas inteligentes",
        "toma de decisiones automatizada", "sesgo algoritmico", "explicabilidad", "caja negra"
    ],
    "datos_privacidad": [
        "datos personales", "proteccion de datos", "privacidad", "autodeterminacion informativa",
        "ley 19.628", "habeas data", "consentimiento informado", "cookies", "perfilamiento",
        "vigilancia masiva", "anonimizacion", "derecho al olvido", "seguridad de datos"
    ],
    "ciberseguridad_cibercrimen": [
        "ciberseguridad", "cibercrimen", "delitos informaticos", "ley 21.459", "convenio de budapest",
        "hacking", "phishing", "malware", "ransomware", "evidencia digital", "peritaje informatico",
        "cadena de custodia digital", "ataques informaticos", "infraestructura critica"
    ],
    "propiedad_intelectual_software": [
        "software", "propiedad intelectual", "derechos de autor", "copyright", "licencia", "gpl",
        "codigo abierto", "open source", "patente", "ingenieria inversa", "medidas tecnologicas",
        "elusion", "dominio publico", "inapi", "obras digitales"
    ],
    "comercio_electronico_contratos": [
        "comercio electronico", "e-commerce", "firma electronica", "ley 19.799", "smart contract",
        "blockchain", "criptoactivos", "criptomonedas", "tokens", "consumidor digital",
        "contratacion electronica", "terminos y condiciones", "clausulas abusivas digitales"
    ],
    "telecomunicaciones_plataformas": [
        "telecomunicaciones", "neutralidad de la red", "plataformas digitales", "redes sociales",
        "intermediarios", "responsabilidad de intermediarios", "libertad de expresion", "desinformacion",
        "moderacion de contenidos", "internet", "gobernanza de internet"
    ],
    "gobierno_digital_justicia": [
        "gobierno digital", "transformacion digital", "ley 21.180", "expediente electronico",
        "tramitacion digital", "ley 20.886", "ciberjusticia", "justicia digital", "ojv",
        "interoperabilidad", "administracion electronica"
    ],
    "bioetica_neuroderechos": [
        "neuroderechos", "neurotecnologia", "cerebro", "datos biometricos", "reconocimiento facial",
        "genetica", "bioetica", "transhumanismo", "identidad biometrica"
    ],
    "constitucional_fundamental": [
        "constitucion", "constitucional", "derechos fundamentales", "igualdad", "libertad de expresion",
        "recurso de proteccion", "tribunal constitucional", "democracia digital"
    ],
    "civil_responsabilidad": [
        "responsabilidad civil", "danos", "culpa", "caso fortuito", "riesgo creado", "contrato",
        "incumplimiento", "indemnizacion", "lucro cesante", "dano moral"
    ],
    "penal_procesal": [
        "derecho penal", "tipo penal", "culpabilidad", "proceso penal", "garantias procesales",
        "prueba ilicita", "debido proceso", "tribunales"
    ],
}

PATRONES_NORMAS = [
    r"Ley\s+N[°º]?\s*[\d\.]+",
    r"D\.?F\.?L\.?\s+N[°º]?\s*\d+",
    r"D\.?L\.?\s+N[°º]?\s*\d+",
    r"Código\s+Civil",
    r"Código\s+de\s+Comercio",
    r"Código\s+Penal",
    r"Código\s+del\s+Trabajo",
    r"Código\s+de\s+Procedimiento\s+Civil",
    r"Código\s+Procesal\s+Penal",
    r"Constitución\s+Política",
    r"CPR",
    r"Convenio\s+de\s+Budapest",
    r"Reglamento\s+General\s+de\s+Protección\s+de\s+Datos",
    r"RGPD",
    r"GDPR",
]


def sin_tildes(texto: str) -> str:
    """Elimina marcas diacríticas para comparaciones léxicas."""
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def slugify(texto: str) -> str:
    """Genera un slug seguro y limpio para nombres de archivo."""
    s = sin_tildes(texto).lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:60]


def clean_xml(raw_bytes: bytes) -> str:
    """Limpia caracteres no permitidos en XML 1.0."""
    text = raw_bytes.decode("utf-8", errors="replace")
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)


def formatear_autor(autor_raw: str) -> str:
    """Normaliza nombres de autores desde 'Apellido, Nombre' a 'Nombre Apellido'."""
    autor_raw = autor_raw.strip()
    if "," in autor_raw:
        partes = [p.strip() for p in autor_raw.split(",", 1)]
        if len(partes) == 2 and partes[1]:
            return f"{partes[1]} {partes[0]}"
    return autor_raw


def seleccionar_titulos(titles: List[str], lang: str) -> Tuple[str, Optional[str]]:
    """Selecciona el título principal (español si el idioma o contenido lo indica) y el alternativo."""
    if not titles:
        return "", None
    if len(titles) == 1:
        return titles[0], None

    lang_low = lang.lower().strip()
    if lang_low.startswith("spa") or not lang_low:
        # Puntuamos por presencia de palabras en español
        mejor = titles[0]
        mejor_score = -1
        for t in titles:
            palabras = set(re.findall(r"\b\w+\b", sin_tildes(t).lower()))
            score = len(palabras & PALABRAS_ES)
            if score > mejor_score:
                mejor_score = score
                mejor = t
        alt = titles[0] if mejor != titles[0] else titles[1]
        return mejor, alt
    else:
        return titles[0], titles[1] if len(titles) > 1 else None


def inferir_area(titulo: str, texto: str) -> str:
    """Infiere el área dogmática según palabras clave en título y cuerpo."""
    corpus = (titulo + " " + texto[:5000]).lower()
    corpus_sin = sin_tildes(corpus)

    conteo: Dict[str, int] = {}
    for area, keywords in AREAS_KEYWORDS.items():
        score = 0
        for kw in keywords:
            kw_sin = sin_tildes(kw.lower())
            if " " in kw_sin:
                score += corpus_sin.count(kw_sin) * 3
            else:
                score += len(re.findall(rf"\b{re.escape(kw_sin)}\b", corpus_sin))
        conteo[area] = score

    mejor_area, mejor_score = max(conteo.items(), key=lambda x: x[1])
    return mejor_area if mejor_score > 0 else "derecho_tecnologia_ia"


def extraer_normas_citadas(texto: str) -> List[str]:
    """Extrae normas y leyes chilenas citadas en el texto del artículo."""
    normas = set()
    fragmento = texto[:35000]
    for pat in PATRONES_NORMAS:
        for m in re.finditer(pat, fragmento, re.I):
            norma = m.group(0).strip()
            norma = re.sub(r"\s+", " ", norma)
            normas.add(norma)
    return sorted(list(normas))[:15]


def limpiar_texto_pdf(texto: str) -> str:
    """Limpia saltos de línea y encabezados espurios respetando reglas RAE/ASALE."""
    texto = re.sub(r"(\w+)-\n(\w+)", r"\1\2", texto)
    texto = re.sub(r"Revista Chilena de Derecho y Tecnología.*?\n", "\n", texto, flags=re.I)
    texto = re.sub(r"\n\s*\d{1,4}\s*\n", "\n\n", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def cosechar_articulos_oai() -> List[Dict[str, Any]]:
    """Cosecha todos los artículos de la RChDT a través del protocolo OAI-PMH oficial."""
    print("  [*] Cosechando catálogo completo de la RChDT vía OAI-PMH...")
    articulos: List[Dict[str, Any]] = []
    url: Optional[str] = f"{OAI_URL}?verb=ListRecords&metadataPrefix=oai_dc"
    lote = 1

    while url:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OpenLegalChile/1.0"})
            with safe_urlopen(req, timeout=30) as resp:
                xml_raw = resp.read()
            xml_cleaned = clean_xml(xml_raw)
            root = ET.fromstring(xml_cleaned.encode("utf-8"))

            records = root.findall(".//oai:record", NS)
            print(f"    -> Lote {lote}: {len(records)} registros obtenidos...")

            for rec in records:
                header = rec.find("oai:header", NS)
                if header is not None and header.get("status") == "deleted":
                    continue

                metadata = rec.find(".//oai_dc:dc", NS)
                if metadata is None:
                    continue

                raw_titles = [t.text.strip() for t in metadata.findall("dc:title", NS) if t.text and t.text.strip()]
                if not raw_titles:
                    continue

                # Filtrar preliminares, editoriales vacíos o sumarios
                primer_tit = raw_titles[0].lower()
                if primer_tit in ("editorial", "tabla de contenido", "índice", "sumario", "presentación", "normas editoriales"):
                    continue

                languages = [lang_elem.text.strip() for lang_elem in metadata.findall("dc:language", NS) if lang_elem.text and lang_elem.text.strip()]
                lang_main = languages[0] if languages else "spa"

                title, alt_title = seleccionar_titulos(raw_titles, lang_main)
                if not title or title.lower() in ("editorial", "sumario", "índice"):
                    continue

                creators = [c.text.strip() for c in metadata.findall("dc:creator", NS) if c.text and c.text.strip()]
                creator_str = creators[0] if creators else ""

                # Filtrar posibles tomos completos concatenados
                if re.match(r"^Vol\.?\s*\d+[\s,]*N[°º]?\s*\d+", title, re.I) and "tecnología" in creator_str.lower():
                    continue

                subjects = [s.text.strip() for s in metadata.findall("dc:subject", NS) if s.text and s.text.strip()]
                sources = [s.text.strip() for s in metadata.findall("dc:source", NS) if s.text and s.text.strip()]
                relations = [r.text.strip() for r in metadata.findall("dc:relation", NS) if r.text and r.text.strip()]
                formats = [f.text.strip().lower() for f in metadata.findall("dc:format", NS) if f.text and f.text.strip()]
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

                # Identificar URL directa de descarga de PDF
                pdf_download_url = ""
                # Primero emparejar con format == application/pdf
                for fmt, rel in zip(formats, relations, strict=False):
                    if fmt == "application/pdf":
                        pdf_download_url = rel.replace("/article/view/", "/article/download/")
                        break
                if not pdf_download_url:
                    for rel in relations:
                        if "pdf" in rel.lower():
                            pdf_download_url = rel.replace("/article/view/", "/article/download/")
                            break
                if not pdf_download_url and relations:
                    # En OJS de UChile relations[-1] usualmente es la galerada PDF principal
                    pdf_download_url = relations[-1].replace("/article/view/", "/article/download/")

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
                        if 2012 <= anio_cand <= 2026:
                            anio = anio_cand

                if not anio:
                    try:
                        anio = 2011 + int(volumen)
                    except ValueError:
                        anio = 2012

                autores_fmt = "; ".join([formatear_autor(c) for c in creators]) if creators else "Facultad de Derecho, Universidad de Chile"
                resumen = descriptions[0] if descriptions else ""

                articulos.append({
                    "art_id": art_id,
                    "title": title,
                    "alt_title": alt_title,
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
                    "idioma": lang_main,
                    "revista": "Revista Chilena de Derecho y Tecnología",
                    "todas_relaciones": relations,
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


def descargar_pdf_resiliente(art: Dict[str, Any]) -> bytes:
    """Descarga el PDF del artículo probando las galeradas candidatas si es necesario."""
    candidatos = []
    if art.get("pdf_url"):
        candidatos.append(art["pdf_url"])
    for rel in art.get("todas_relaciones", []):
        cand = rel.replace("/article/view/", "/article/download/")
        if cand not in candidatos:
            candidatos.append(cand)

    for url in candidatos:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OpenLegalChile/1.0"})
            with safe_urlopen(req, timeout=25) as resp:
                data = resp.read()
            if len(data) > 1000 and data.startswith(b"%PDF"):
                return data
        except Exception:  # nosec B110 B112
            pass
    return b""


def procesar_articulo(art: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Descarga el PDF, extrae el texto y genera el Markdown canónico."""
    art_id = art["art_id"]
    anio = art["anio"]
    volumen = art["volumen"]
    numero = art["numero"]
    paginas = art.get("paginas", "")
    title = art["title"]
    alt_title = art.get("alt_title")
    autores = art["autores"]
    doi = art.get("doi", "")
    url_ojs = art["url_ojs"]
    resumen = art.get("resumen", "")
    subjects = art.get("subjects", [])
    idioma = art.get("idioma", "spa")

    slug = slugify(title)
    if not slug:
        slug = f"articulo_{art_id}"
    md_filename = f"rchdt_{anio}_v{volumen}_n{numero}_{art_id}_{slug}.md"

    year_dir = OUTPUT_DIR / str(anio)
    year_dir.mkdir(parents=True, exist_ok=True)
    target_md = year_dir / md_filename

    if target_md.exists() and target_md.stat().st_size > 1024:
        return {"art_id": art_id, "anio": anio, "md_path": target_md, "nuevo": False}

    texto_cuerpo = ""
    pdf_bytes = descargar_pdf_resiliente(art)
    if pdf_bytes:
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

    if not texto_cuerpo:
        texto_cuerpo = (
            f"{resumen}\n\n"
            f"Nota de archivo: Texto íntegro disponible en la edición oficial en PDF.\n"
            f"Repositorio oficial: {url_ojs}"
        )

    area = inferir_area(title, texto_cuerpo)
    normas = extraer_normas_citadas(texto_cuerpo)

    cita_oficial = f"[RChDT - Vol. {volumen} N° {numero} ({anio}), {autores}, {title}]"

    frontmatter = [
        "---",
        f'titulo: "{title}"',
    ]
    if alt_title:
        frontmatter.append(f'titulo_alternativo: "{alt_title}"')
    frontmatter.extend([
        f'autores: "{autores}"',
        'revista: "Revista Chilena de Derecho y Tecnología"',
        'institucion: "Facultad de Derecho, Universidad de Chile"',
        f'issn_impreso: "{ISSN_PRINT}"',
        f'issn_electronico: "{ISSN_ELEC}"',
        f"anio: {anio}",
        f'volumen: "{volumen}"',
        f'numero: "{numero}"',
        f'paginas: "{paginas}"',
        f'idioma: "{idioma}"',
        f'area_derecho: "{area}"',
        f'doi: "{doi}"',
        f'url_ojs: "{url_ojs}"',
        f'cita_oficial: "{cita_oficial}"',
        "normas_citadas:",
    ])
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
        f"> **Publicación oficial:** Revista Chilena de Derecho y Tecnología, Centro de Estudios en Derecho, Tecnología y Sociedad, Facultad de Derecho, Universidad de Chile.  \n"
        f"> **Identificador DOI:** `{doi}` | **URL:** {url_ojs}\n\n"
        f"{extra_bloque}\n"
        f"## Texto del Artículo\n\n{texto_cuerpo}\n"
    )

    target_md.write_text(md_content, encoding="utf-8")
    return {"art_id": art_id, "anio": anio, "md_path": target_md, "nuevo": True}


def subir_articulos_a_huggingface(repo_id: str = "pablobenavidesj/doctrina-jurisprudencia-chile") -> bool:
    """Sube la colección RChDT al dataset de Hugging Face Hub."""
    token = resolver_token_hf()
    if not token:
        print("  [!] No se encontró HF_TOKEN en el entorno o en el almacén seguro.")
        return False

    from huggingface_hub import HfApi
    api = HfApi(token=token)

    print(f"  [*] Subiendo artículos RChDT (2012-2026) a Hugging Face: {repo_id}...")
    try:
        api.upload_folder(
            folder_path=str(OUTPUT_DIR),
            repo_id=repo_id,
            repo_type="dataset",
            path_in_repo="doctrina/revistas/rchdt",
            commit_message="feat(doctrina): ingesta de Revista Chilena de Derecho y Tecnología (UChile, 2012-2026)",
        )
        print("  ✓ Carpeta doctrina/revistas/rchdt subida con éxito a Hugging Face.")
        return True
    except Exception as e:
        print(f"  [!] Error al subir a Hugging Face: {e}")
        return False


def actualizar_catalogo_hf() -> None:
    """Regenera los catálogos ligeros train_lite.jsonl, instituciones_lite.jsonl e indice_citas.jsonl."""
    print("  [*] Regenerando catálogos ligeros para Hugging Face...")
    script_opt = ROOT_DIR / "scripts" / "optimizar_catalogo_hf.py"
    if script_opt.exists():
        subprocess.run([sys.executable, str(script_opt)], cwd=str(ROOT_DIR), check=True)  # nosec B603


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingesta masiva de Revista Chilena de Derecho y Tecnología")
    parser.add_argument("--skip-download", action="store_true", help="Omitir cosecha y descarga si ya existen")
    parser.add_argument("--subir-hf", action="store_true", help="Subir a Hugging Face Hub al finalizar")
    parser.add_argument("--concurrencia", type=int, default=6, help="Hilos concurrentes para descarga y extracción")
    args = parser.parse_args()

    print("=" * 78)
    print(" OPEN LEGAL CHILE — INGESTA REVISTA CHILENA DE DERECHO Y TECNOLOGÍA (RChDT)")
    print(" Facultad de Derecho, Universidad de Chile (2012-2026)")
    print("=" * 78)

    t0 = time.time()

    # 1. Cosecha OAI-PMH
    articulos = cosechar_articulos_oai()
    if not articulos:
        print("  [!] No se recuperaron artículos. Abortando.")
        return 1

    # Guardar catálogo estructurado
    with open(CATALOGO_RCHDT, "w", encoding="utf-8") as f:
        for art in articulos:
            art_clean = {k: v for k, v in art.items() if k != "todas_relaciones"}
            f.write(json.dumps(art_clean, ensure_ascii=False) + "\n")
    print(f"  ✓ Catálogo estructurado guardado en {CATALOGO_RCHDT.relative_to(ROOT_DIR)} ({CATALOGO_RCHDT.stat().st_size / 1024:.1f} KB)")

    if args.skip_download:
        print("  [i] Flag --skip-download activada. Finalizando.")
        return 0

    # 2. Descarga y procesamiento concurrente
    print(f"  [*] Procesando {len(articulos)} artículos con {args.concurrencia} hilos concurrentes...")
    procesados = 0
    nuevos = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrencia) as executor:
        futuros = {executor.submit(procesar_articulo, art): art for art in articulos}
        for fut in concurrent.futures.as_completed(futuros):
            try:
                res = fut.result()
                if res:
                    procesados += 1
                    if res.get("nuevo"):
                        nuevos += 1
                if procesados % 25 == 0 or procesados == len(articulos):
                    print(f"    -> {procesados}/{len(articulos)} artículos procesados ({nuevos} nuevos generados)...")
            except Exception as e:
                art_err = futuros[fut]
                print(f"    [!] Error en artículo {art_err.get('art_id')}: {e}")

    duracion = time.time() - t0
    print(f"  ✓ Proceso completado: {procesados} artículos procesados ({nuevos} nuevos) en {duracion:.1f}s.")

    # 3. Subir a Hugging Face Hub si se solicita
    if args.subir_hf:
        subir_articulos_a_huggingface()
        actualizar_catalogo_hf()

    print("=" * 78)
    print(" INGESTA DE RChDT FINALIZADA CON ÉXITO")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
