#!/usr/bin/env python3
"""
ingestar_revistas_cientificas.py — Ingesta integral de revistas científicas jurídicas de Chile:
  1. Revista de Derecho Ambiental (CDA, Universidad de Chile, 2002-2026) -> RDA-UChile
  2. Revista de Derecho (Coquimbo, Universidad Católica del Norte, 1993-2026) -> RDUCN
  3. Revista de Derecho (Valdivia, Universidad Austral de Chile, 1990-2026) -> RDUACh
  4. Revista de Estudios Histórico-Jurídicos (PUCV, 1976-2026) -> REHJ

Cosecha la colección de artículos vía OAI-PMH oficial, extrae metadata estructurada multilingüe,
descarga los PDFs con safe_urlopen, convierte a Markdown canónico token-optimizado RAE/ASALE
con corchetes de citación oficiales, y sincroniza con Hugging Face Hub y LegalGraphify.
"""

from __future__ import annotations

import argparse
import concurrent.futures
from dataclasses import dataclass
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
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Set, Tuple

import defusedxml.ElementTree as ET  # type: ignore[import-untyped]

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))
from config import safe_urlopen
from online_library_sync import resolver_token_hf

NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
}

PALABRAS_ES = {
    "de", "la", "el", "en", "y", "los", "del", "las", "un", "por", "con", "una",
    "su", "para", "al", "lo", "como", "mas", "derecho", "ley", "chile", "sobre",
    "responsabilidad", "contrato", "obligaciones", "dano", "penal", "civil", "procesal",
    "ambiental", "historico", "romano", "constitucional", "administrativo", "trabajo"
}

AREAS_KEYWORDS: Dict[str, List[str]] = {
    "civil_obligaciones_contratos": [
        "obligacion", "contrato", "responsabilidad civil", "lucro cesante", "dano emergente",
        "dano moral", "incumplimiento", "resolucion", "clausula penal", "buena fe", "culpa",
        "caso fortuito", "fuerza mayor", "remedios contractuales", "autonomia privada"
    ],
    "civil_bienes_derechos_reales": [
        "bienes", "propiedad", "dominio", "posesion", "prescripcion", "reivindicatoria",
        "usufructo", "servidumbre", "hipoteca", "prenda", "cbr", "estudio de titulos", "tradicion"
    ],
    "civil_familia_sucesorio": [
        "familia", "matrimonio", "divorcio", "filiacion", "alimentos", "cuidado personal",
        "procedimiento de familia", "violencia intrafamiliar", "herencia", "testamento", "sucesorio", "legitima"
    ],
    "procesal_civil_organico": [
        "procedimiento civil", "cpc", "demanda", "excepcion", "prueba", "sentencia", "apelacion",
        "casacion", "cosa juzgada", "arbitraje", "colaboracion procesal", "debido proceso", "tribunales"
    ],
    "penal_criminologia": [
        "derecho penal", "delito", "pena", "tipicidad", "antijuridicidad", "culpabilidad",
        "homicidio", "estafa", "legitima defensa", "cpp", "proceso penal", "prision preventiva", "maltrato"
    ],
    "constitucional_fundamental": [
        "constitucion", "constitucional", "cpr", "derechos fundamentales", "igualdad",
        "recurso de proteccion", "tribunal constitucional", "democracia", "soberania"
    ],
    "administrativo_probidad": [
        "derecho administrativo", "acto administrativo", "servicio publico", "probidad",
        "contraloria", "cgr", "responsabilidad del estado", "falta de servicio", "sancionatorio administrativo"
    ],
    "laboral_previsional": [
        "codigo del trabajo", "contrato de trabajo", "despido", "art 161", "indemnizacion por anos de servicio",
        "tutela laboral", "sindicato", "huelga", "negociacion colectiva", "seguridad social"
    ],
    "comercial_societario": [
        "codigo de comercio", "sociedad", "sociedad anonima", "spa", "directores", "insolvencia",
        "concursal", "quiebra", "titulos de credito", "seguros", "gobierno corporativo"
    ],
    "ambiental_recursos_naturales": [
        "derecho ambiental", "medio ambiente", "seia", "rca", "dano ambiental", "aguas",
        "mineria", "cambio climatico", "recursos naturales", "biodiversidad", "humedales"
    ],
    "historia_del_derecho_romano": [
        "derecho romano", "historia del derecho", "digesto", "fuentes romanas", "pandectas",
        "derecho indiano", "ius commune", "codificacion", "fuero real", "siete partidas"
    ],
    "derecho_internacional_ddhh": [
        "derecho internacional", "tratados internacionales", "corte interamericana",
        "derechos humanos", "derecho internacional privado", "soberania", "cidh"
    ]
}


@dataclass
class RevistaConfig:
    key: str
    nombre: str
    institucion: str
    oai_url: str
    issn_print: str
    issn_elec: str
    prefix_cita: str
    has_volume: bool
    noise_titles: Set[str]

    @property
    def data_dir(self) -> pathlib.Path:
        d = ROOT_DIR / "data" / self.key
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def pdf_dir(self) -> pathlib.Path:
        d = self.data_dir / "pdfs"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def output_dir(self) -> pathlib.Path:
        d = ROOT_DIR / "doctrina" / "revistas" / self.key
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def catalogo_path(self) -> pathlib.Path:
        return self.data_dir / "catalogo_articulos.jsonl"


REVISTAS: Dict[str, RevistaConfig] = {
    "rda_uchile": RevistaConfig(
        key="rda_uchile",
        nombre="Revista de Derecho Ambiental",
        institucion="Centro de Derecho Ambiental (CDA), Facultad de Derecho, Universidad de Chile",
        oai_url="https://revistaderechoambiental.uchile.cl/index.php/RDA/oai",
        issn_print="",
        issn_elec="0719-6369",
        prefix_cita="RDA-UChile",
        has_volume=False,
        noise_titles={
            "editorial", "presentacion", "indice", "sumario", "normas de publicacion",
            "portada", "contraportada", "cubierta", "tabla de contenido"
        },
    ),
    "rducn": RevistaConfig(
        key="rducn",
        nombre="Revista de Derecho (Coquimbo)",
        institucion="Escuela de Derecho Coquimbo, Facultad de Ciencias Jurídicas, Universidad Católica del Norte",
        oai_url="https://revistaderecho.ucn.cl/index.php/revista-derecho/oai",
        issn_print="0717-5345",
        issn_elec="0718-9753",
        prefix_cita="RDUCN",
        has_volume=True,
        noise_titles={
            "editorial", "presentacion", "indice", "sumario", "normas de publicacion",
            "portada", "contraportada", "cubierta", "tabla de contenido"
        },
    ),
    "rduach": RevistaConfig(
        key="rduach",
        nombre="Revista de Derecho (Valdivia)",
        institucion="Facultad de Ciencias Jurídicas y Sociales, Universidad Austral de Chile",
        oai_url="https://revistaderechovaldivia.cl/index.php/revde/oai",
        issn_print="0717-0599",
        issn_elec="0718-0950",
        prefix_cita="RDUACh",
        has_volume=True,
        noise_titles={
            "editorial", "presentacion", "indice", "sumario", "normas de publicacion",
            "portada", "contraportada", "cubierta", "tabla de contenido", "actas de la facultad"
        },
    ),
    "rehj": RevistaConfig(
        key="rehj",
        nombre="Revista de Estudios Histórico-Jurídicos",
        institucion="Escuela de Derecho, Pontificia Universidad Católica de Valparaíso",
        oai_url="https://rehj.cl/index.php/rehj/oai",
        issn_print="0716-5455",
        issn_elec="0717-6260",
        prefix_cita="REHJ",
        has_volume=False,
        noise_titles={
            "editorial", "presentacion", "indice", "sumario", "normas para los autores",
            "portada", "contraportada", "cubierta", "tabla de contenido", "bibliografia",
            "recensiones", "cronica", "documentos", "obituario"
        },
    ),
}


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


def seleccionar_titulos(titles: List[str]) -> Tuple[str, Optional[str]]:
    """Selecciona el título principal en español y el alternativo si existe."""
    if not titles:
        return "", None
    if len(titles) == 1:
        return titles[0], None

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


def inferir_area(titulo: str, texto: str) -> str:
    """Infiere el área dogmática según palabras clave en título y cuerpo."""
    corpus = (titulo + " " + texto[:5000]).lower()
    corpus_sin = sin_tildes(corpus)

    conteo: Dict[str, int] = {}
    for area, keywords in AREAS_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in corpus_sin:
                score += 2 if kw in sin_tildes(titulo).lower() else 1
        if score > 0:
            conteo[area] = score

    if conteo:
        area_max = max(conteo.items(), key=lambda x: x[1])[0]
        mapa_nombres = {
            "civil_obligaciones_contratos": "Derecho Civil (Obligaciones y Contratos)",
            "civil_bienes_derechos_reales": "Derecho Civil (Bienes y Derechos Reales)",
            "civil_familia_sucesorio": "Derecho Civil (Familia y Sucesorio)",
            "procesal_civil_organico": "Derecho Procesal Civil y Orgánico",
            "penal_criminologia": "Derecho Penal y Procesal Penal",
            "constitucional_fundamental": "Derecho Constitucional y Derechos Fundamentales",
            "administrativo_probidad": "Derecho Administrativo y Probidad Pública",
            "laboral_previsional": "Derecho del Trabajo y Seguridad Social",
            "comercial_societario": "Derecho Comercial y Societario",
            "ambiental_recursos_naturales": "Derecho Ambiental y Recursos Naturales",
            "historia_del_derecho_romano": "Historia del Derecho y Derecho Romano",
            "derecho_internacional_ddhh": "Derecho Internacional y Derechos Humanos",
        }
        return mapa_nombres.get(area_max, "Doctrina Jurídica General")

    return "Doctrina Jurídica General"


def extraer_normas_citadas(texto: str) -> List[str]:
    """Detecta citas canónicas de leyes y códigos chilenos en el texto."""
    patrones = [
        r"(?:art(?:ículo)?s?\.?\s*\d+(?:\s*(?:bis|ter|quater|inciso\s*\d+|inc\.\s*\d+))?(?:\s*(?:del|de\s*la))?\s*(?:Código\s+Civil|Código\s+del\s+Trabajo|Código\s+de\s+Comercio|Código\s+Penal|Código\s+de\s+Procedimiento\s+Civil|CPC|CPP))",
        r"(?:Ley\s*(?:N[°o]\s*)?\d{1,2}\.\d{3})",
        r"(?:DFL\s*(?:N[°o]\s*)?\d+)",
        r"(?:D\.?L\.?\s*(?:N[°o]\s*)?\d+)",
        r"(?:Constitución\s+Política\s+de\s+la\s+República|CPR)",
    ]
    normas: Set[str] = set()
    for pat in patrones:
        for m in re.finditer(pat, texto, re.IGNORECASE):
            norma = m.group(0).strip()
            norma = re.sub(r"\s+", " ", norma)
            normas.add(norma)
    return sorted(list(normas))[:15]


def limpiar_texto_pdf(texto: str) -> str:
    """Limpia saltos de línea y encabezados espurios respetando reglas RAE/ASALE."""
    texto = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", texto)
    texto = re.sub(r"(\w+)-\n(\w+)", r"\1\2", texto)
    texto = re.sub(r"Revista de Derecho.*?\n", "\n", texto, flags=re.I)
    texto = re.sub(r"Revista de Estudios Histórico-Jurídicos.*?\n", "\n", texto, flags=re.I)
    texto = re.sub(r"\n\s*\d{1,4}\s*\n", "\n\n", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def cosechar_articulos_oai(cfg: RevistaConfig) -> List[Dict[str, Any]]:
    """Cosecha todos los artículos de la revista vía OAI-PMH oficial."""
    if cfg.catalogo_path.exists() and cfg.catalogo_path.stat().st_size > 1024:
        try:
            articulos_cacheados = []
            with open(cfg.catalogo_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        articulos_cacheados.append(json.loads(line))
            if articulos_cacheados:
                print(f"  ✓ [{cfg.key}] Usando catálogo previo en caché ({len(articulos_cacheados)} artículos).")
                return articulos_cacheados
        except Exception:  # nosec B110
            pass

    print(f"  [*] Cosechando catálogo completo de {cfg.nombre} vía OAI-PMH...")
    articulos: List[Dict[str, Any]] = []
    url: Optional[str] = f"{cfg.oai_url}?verb=ListRecords&metadataPrefix=oai_dc"
    lote = 1

    while url:
        xml_raw = None
        for reintento in range(4):
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OpenLegalChile/1.0"}
                )
                with safe_urlopen(req, timeout=45) as resp:
                    xml_raw = resp.read()
                break
            except Exception as e:
                if reintento == 3:
                    print(f"    [!] Error definitivo en cosecha OAI lote {lote} para {cfg.key}: {e}")
                    url = None
                    break
                time.sleep(2.0)

        if not xml_raw:
            break

        try:
            xml_cleaned = clean_xml(xml_raw)
            root = ET.fromstring(xml_cleaned.encode("utf-8"))

            records = root.findall(".//oai:record", NS)
            print(f"    -> [{cfg.key}] Lote {lote}: {len(records)} registros obtenidos...")

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

                primer_tit_sin = sin_tildes(raw_titles[0].lower()).strip()
                if any(noise in primer_tit_sin for noise in cfg.noise_titles) and len(primer_tit_sin.split()) <= 4:
                    continue

                title, alt_title = seleccionar_titulos(raw_titles)
                if not title or len(title) < 4:
                    continue

                # Autores
                raw_creators = [c.text.strip() for c in metadata.findall("dc:creator", NS) if c.text and c.text.strip()]
                autores_list = [formatear_autor(c) for c in raw_creators]
                autores_fmt = "; ".join(autores_list) if autores_list else "Autor no especificado"

                # Relaciones y descarga PDF
                relations = [r.text.strip() for r in metadata.findall("dc:relation", NS) if r.text and r.text.strip()]
                pdf_download_url: Optional[str] = None
                url_ojs = ""

                for rel in relations:
                    if "/article/view/" in rel:
                        url_ojs = rel
                        pdf_download_url = rel.replace("/article/view/", "/article/download/")
                        break

                identifier = rec.find("oai:header/oai:identifier", NS)
                id_str = identifier.text.strip() if identifier is not None and identifier.text else ""
                art_id = id_str.split("/")[-1] if "/" in id_str else (id_str.split(":")[-1] if ":" in id_str else "0")

                if not pdf_download_url and relations:
                    for rel in relations:
                        if "/download/" in rel:
                            pdf_download_url = rel
                            break

                source = metadata.find("dc:source", NS)
                source_str = source.text.strip() if source is not None and source.text else ""

                date_el = metadata.find("dc:date", NS)
                date_str = date_el.text.strip() if date_el is not None and date_el.text else ""

                # Volumen, Número y Año
                volumen = "s_v"
                numero = "s_n"
                anio = 0
                paginas = ""

                m_vol = re.search(r"Vol\.?\s*(\d+)", source_str, re.IGNORECASE)
                if m_vol:
                    volumen = m_vol.group(1)

                m_num = re.search(r"N[oóuú]m?\.?\s*(\d+)", source_str, re.IGNORECASE)
                if m_num:
                    numero = m_num.group(1)

                m_yr = re.search(r"\((\d{4})\)", source_str) or re.search(r"\b(19\d{2}|20\d{2})\b", source_str)
                if m_yr:
                    anio = int(m_yr.group(1))
                elif date_str:
                    m_d = re.search(r"\b(19\d{2}|20\d{2})\b", date_str)
                    if m_d:
                        anio = int(m_d.group(1))

                # Páginas
                m_pg = re.search(r"(?:P[aá]g\.?|pp?\.?|;)\s*(\d+[-–]\d+)", source_str, re.IGNORECASE)
                if m_pg:
                    paginas = m_pg.group(1).replace("–", "-")

                if anio == 0:
                    anio = 2020

                # Resumen
                descs = [d.text.strip() for d in metadata.findall("dc:description", NS) if d.text and d.text.strip()]
                resumen, _ = seleccionar_titulos(descs)

                # Palabras clave
                subjects = [s.text.strip() for s in metadata.findall("dc:subject", NS) if s.text and s.text.strip()]

                # DOI
                doi = ""
                for ident in metadata.findall("dc:identifier", NS):
                    if ident.text and ("10." in ident.text or "doi.org" in ident.text):
                        doi = ident.text.strip()
                        break

                articulos.append({
                    "art_id": art_id,
                    "title": title,
                    "alt_title": alt_title,
                    "autores": autores_fmt,
                    "subjects": subjects,
                    "resumen": resumen,
                    "url_ojs": url_ojs or f"{cfg.oai_url.replace('/oai', '')}/article/view/{art_id}",
                    "pdf_url": pdf_download_url,
                    "doi": doi,
                    "volumen": volumen,
                    "numero": numero,
                    "anio": anio,
                    "paginas": paginas,
                    "revista": cfg.nombre,
                    "todas_relaciones": relations,
                })

            token_el = root.find(".//oai:resumptionToken", NS)
            if token_el is not None and token_el.text:
                token = token_el.text.strip()
                url = f"{cfg.oai_url}?verb=ListRecords&resumptionToken={urllib.parse.quote(token)}"
                lote += 1
                time.sleep(0.4)
            else:
                url = None

        except Exception as e:
            print(f"    [!] Error en cosecha OAI lote {lote} para {cfg.key}: {e}")
            break

    # Ordenar cronológicamente
    articulos.sort(key=lambda x: (x["anio"], int(x["numero"]) if x["numero"].isdigit() else 0, x["art_id"]))
    if articulos:
        print(f"  ✓ [{cfg.key}] {len(articulos)} artículos cosechados con éxito (años {articulos[0]['anio']} a {articulos[-1]['anio']}).")
    else:
        print(f"  [!] [{cfg.key}] No se encontraron artículos válidos.")
    return articulos


_UNREACHABLE_HOSTS: Set[str] = set()


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
        host = urllib.parse.urlparse(url).netloc
        if host in _UNREACHABLE_HOSTS:
            continue

        timeout = 4 if "rehj.cl" in host else 35
        retries = 1 if "rehj.cl" in host else 3
        if "rehj.cl" in url:
            time.sleep(0.35)
        for _reintento in range(retries):
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OpenLegalChile/1.0"}
                )
                with safe_urlopen(req, timeout=timeout) as resp:
                    data = resp.read()
                if len(data) > 1000 and data.startswith(b"%PDF"):
                    return data
            except Exception:  # nosec B110 B112
                if "rehj.cl" in host:
                    _UNREACHABLE_HOSTS.add(host)
                    break
                time.sleep(1.0)
    return b""


def procesar_articulo(art: Dict[str, Any], cfg: RevistaConfig) -> Optional[Dict[str, Any]]:
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

    slug = slugify(title)
    if not slug:
        slug = f"articulo_{art_id}"

    if cfg.has_volume:
        md_filename = f"{cfg.key}_{anio}_v{volumen}_n{numero}_{art_id}_{slug}.md"
        cita_oficial = f"[{cfg.prefix_cita} - Vol. {volumen} N° {numero} ({anio}), {autores}, {title}]"
    else:
        md_filename = f"{cfg.key}_{anio}_n{numero}_{art_id}_{slug}.md"
        cita_oficial = f"[{cfg.prefix_cita} - N° {numero} ({anio}), {autores}, {title}]"

    year_dir = cfg.output_dir / str(anio)
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

    frontmatter = [
        "---",
        f'titulo: "{title}"',
    ]
    if alt_title:
        frontmatter.append(f'titulo_alternativo: "{alt_title}"')
    frontmatter.extend([
        f'autores: "{autores}"',
        f'revista: "{cfg.nombre}"',
        f'institucion: "{cfg.institucion}"',
        f'issn_impreso: "{cfg.issn_print}"',
        f'issn_electronico: "{cfg.issn_elec}"',
        f"anio: {anio}",
        f'volumen: "{volumen}"',
        f'numero: "{numero}"',
        f'paginas: "{paginas}"',
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
        f"> **Publicación oficial:** {cfg.nombre}, {cfg.institucion}.  \n"
        f"> **Identificador DOI:** `{doi}` | **URL:** {url_ojs}\n\n"
        f"{extra_bloque}\n"
        f"## Texto del Artículo\n\n{texto_cuerpo}\n"
    )

    md_content = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", md_content)
    target_md.write_text(md_content, encoding="utf-8")
    return {"art_id": art_id, "anio": anio, "md_path": target_md, "nuevo": True}


def subir_revista_a_huggingface(cfg: RevistaConfig, repo_id: str = "pablobenavidesj/doctrina-jurisprudencia-chile") -> bool:
    """Sube la colección de la revista al dataset de Hugging Face Hub."""
    token = resolver_token_hf()
    if not token:
        print("  [!] No se encontró HF_TOKEN en el entorno o en el almacén seguro.")
        return False

    from huggingface_hub import HfApi
    api = HfApi(token=token)

    path_in_repo = f"doctrina/revistas/{cfg.key}"
    print(f"  [*] Subiendo artículos {cfg.nombre} a Hugging Face: {repo_id} ({path_in_repo})...")
    try:
        subcarpetas = [d for d in cfg.output_dir.iterdir() if d.is_dir()]
        if len(subcarpetas) > 1:
            for sub in sorted(subcarpetas):
                path_sub = f"{path_in_repo}/{sub.name}"
                api.upload_folder(
                    folder_path=str(sub),
                    repo_id=repo_id,
                    repo_type="dataset",
                    path_in_repo=path_sub,
                    commit_message=f"feat(doctrina): ingesta de {cfg.nombre} ({sub.name})",
                )
        else:
            api.upload_folder(
                folder_path=str(cfg.output_dir),
                repo_id=repo_id,
                repo_type="dataset",
                path_in_repo=path_in_repo,
                commit_message=f"feat(doctrina): ingesta de {cfg.nombre} ({cfg.institucion})",
            )
        print(f"  ✓ Carpeta {path_in_repo} subida con éxito a Hugging Face.")
        return True
    except Exception as e:
        print(f"  [!] Error al subir a Hugging Face: {e}")
        return False


def regenerar_catalogos_ligeros(subir_hf: bool = False) -> None:
    """Regenera los catálogos ligeros train_lite.jsonl, instituciones_lite.jsonl e indice_citas.jsonl."""
    print("\n  [*] Sincronizando dataset base train.jsonl e instituciones...")
    from online_library_sync import OnlineLibrarySyncManager
    mgr = OnlineLibrarySyncManager()
    mgr.generar_dataset_train_jsonl()

    print("  [*] Regenerando catálogos ligeros y de citas para Hugging Face...")
    script_opt = ROOT_DIR / "scripts" / "optimizar_catalogo_hf.py"
    if script_opt.exists():
        subprocess.run([sys.executable, str(script_opt)], cwd=str(ROOT_DIR), check=True)  # nosec B603

    if subir_hf:
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
            print("  [*] Actualizando catálogos ligeros en Hugging Face Hub...")
            for local_path, repo_path in archivos_catalogo:
                if local_path.exists():
                    try:
                        api.upload_file(
                            path_or_fileobj=str(local_path),
                            path_in_repo=repo_path,
                            repo_id=repo_id,
                            repo_type="dataset",
                            commit_message=f"chore(catalogo): actualizar {local_path.name} con nuevas revistas científicas",
                        )
                        print(f"    ✓ {local_path.name} subido exitosamente.")
                    except Exception as e:
                        print(f"    [!] Error al subir {local_path.name}: {e}")


def procesar_revista(cfg: RevistaConfig, skip_download: bool = False, subir_hf: bool = False, concurrencia: int = 8) -> int:
    """Ejecuta el ciclo de ingesta para una revista específica."""
    print("=" * 78)
    print(f" OPEN LEGAL CHILE — INGESTA {cfg.nombre.upper()}")
    print(f" {cfg.institucion}")
    print("=" * 78)

    t0 = time.time()
    articulos = cosechar_articulos_oai(cfg)
    if not articulos:
        print(f"  [!] No se recuperaron artículos para {cfg.key}.")
        return 0

    # Guardar catálogo estructurado
    with open(cfg.catalogo_path, "w", encoding="utf-8") as f:
        for art in articulos:
            art_clean = {k: v for k, v in art.items() if k != "todas_relaciones"}
            f.write(json.dumps(art_clean, ensure_ascii=False) + "\n")
    print(f"  ✓ Catálogo estructurado guardado en {cfg.catalogo_path.relative_to(ROOT_DIR)} ({cfg.catalogo_path.stat().st_size / 1024:.1f} KB)")

    if skip_download:
        print("  [i] Flag --skip-download activada. Omitiendo descarga.")
        if subir_hf:
            subir_revista_a_huggingface(cfg)
        return len(articulos)

    print(f"  [*] Procesando {len(articulos)} artículos con {concurrencia} hilos concurrentes...")
    procesados = 0
    nuevos = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrencia) as executor:
        futuros = {executor.submit(procesar_articulo, art, cfg): art for art in articulos}
        for fut in concurrent.futures.as_completed(futuros):
            try:
                res = fut.result()
                if res:
                    procesados += 1
                    if res.get("nuevo"):
                        nuevos += 1
                if procesados % 25 == 0 or procesados == len(articulos):
                    print(f"    -> [{cfg.key}] {procesados}/{len(articulos)} artículos procesados ({nuevos} nuevos generados)...")
            except Exception as e:
                art_err = futuros[fut]
                print(f"    [!] Error en artículo {art_err.get('art_id')}: {e}")

    duracion = time.time() - t0
    print(f"  ✓ [{cfg.key}] Proceso completado: {procesados} artículos procesados ({nuevos} nuevos) en {duracion:.1f}s.")

    if subir_hf:
        subir_revista_a_huggingface(cfg)

    return procesados


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingesta masiva de revistas científicas jurídicas de Chile")
    parser.add_argument(
        "--revista",
        choices=["rda_uchile", "rducn", "rduach", "rehj", "todas"],
        default="todas",
        help="Revista científica a procesar o 'todas'"
    )
    parser.add_argument("--skip-download", action="store_true", help="Omitir descarga si ya existen")
    parser.add_argument("--subir-hf", action="store_true", help="Subir a Hugging Face Hub al finalizar")
    parser.add_argument("--concurrencia", type=int, default=8, help="Hilos concurrentes para descarga y extracción")
    args = parser.parse_args()

    t_global = time.time()
    revistas_a_ejecutar = list(REVISTAS.keys()) if args.revista == "todas" else [args.revista]

    total_articulos = 0
    for key in revistas_a_ejecutar:
        cfg = REVISTAS[key]
        n = procesar_revista(cfg, skip_download=args.skip_download, subir_hf=args.subir_hf, concurrencia=args.concurrencia)
        total_articulos += n

    # Regenerar catálogos al final
    if not args.skip_download and total_articulos > 0:
        regenerar_catalogos_ligeros(subir_hf=args.subir_hf)

    print("\n" + "=" * 78)
    print(f" CICLO DE INGESTA CIENTÍFICA FINALIZADO: {total_articulos} artículos procesados en {time.time() - t_global:.1f}s")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
