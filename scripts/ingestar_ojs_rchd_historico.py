#!/usr/bin/env python3
"""
ingestar_ojs_rchd_historico.py — Ingesta integral de la colección histórica de la
Revista Chilena de Derecho (Facultad de Derecho UC, 1974-2005).

Cosecha los 84 números históricos directamente desde el portal oficial OJS
(https://revistachilenadederecho.uc.cl/index.php/Rchd/issue/archive) utilizando
curl_cffi para sortear el firewall de Cloudflare, extrae metadata completa,
descarga los PDFs, convierte a Markdown canónico token-optimizado RAE/ASALE,
e integra al catálogo de Hugging Face Hub y LegalGraphify.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
from curl_cffi import requests

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))
from online_library_sync import resolver_token_hf

DATA_DIR = ROOT_DIR / "data" / "rchd"
DATA_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR = DATA_DIR / "pdfs_historicos"
PDF_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = ROOT_DIR / "doctrina" / "revistas" / "rchd"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CATALOGO_HISTORICO = DATA_DIR / "catalogo_historico.jsonl"

BASE_URL = "https://revistachilenadederecho.uc.cl/index.php/Rchd"
ISSN_PRINT = "0716-0747"
ISSN_ELEC = "0718-3437"

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
    "filosofia_e_historia": [
        "filosofia del derecho", "historia del derecho", "derecho romano", "ius", "derecho natural",
        "teoria de la justicia", "aristoteles", "tomas de aquino", "kelsen", "hermeneutica"
    ],
    "internacional": [
        "derecho internacional", "tratado", "convencion", "cidh", "corte interamericana",
        "costumbre internacional", "soberania", "mercosur", "derecho del mar"
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
        return "Facultad de Derecho UC"
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
        return "Doctrina General"
    area_ganadora = max(puntajes, key=lambda k: puntajes[k])
    mapeo = {
        "civil": "Civil",
        "constitucional": "Constitucional",
        "administrativo": "Administrativo",
        "comercial": "Comercial",
        "laboral": "Laboral",
        "penal": "Penal",
        "procesal": "Procesal",
        "ambiental": "Ambiental",
        "filosofia_e_historia": "Filosofía e Historia del Derecho",
        "internacional": "Internacional",
    }
    return mapeo.get(area_ganadora, "Doctrina General")


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

    patron_ley = re.findall(r"ley\s+(?:n[°º]?\s*)?(\d{2,5}\.?\d{0,3})", texto, re.I)
    for ley_match in patron_ley[:5]:
        limpio = ley_match.replace(".", "").strip()
        citas.add(f"[BCN - Ley N° {limpio}]")

    return sorted(list(citas))


def limpiar_texto_pdf(texto: str) -> str:
    """Normaliza texto extraído con pdftotext eliminando artefactos y encabezados reiterados."""
    texto = texto.replace("\x0c", "\n\n")
    texto = re.sub(r"[\x00-\x08\x0b\x0e-\x1f\x7f]", "", texto)
    # Unir palabras cortadas por guion de fin de línea
    texto = re.sub(r"(\w+)-\n(\w+)", r"\1\2", texto)
    # Limpiar encabezados comunes de la RChD
    texto = re.sub(r"Revista Chilena de Derecho,\s*Vol\.\s*\d+.*?\n", "\n", texto, flags=re.I)
    texto = re.sub(r"Revista Chilena de Derecho\s*\[\d{4}\].*?\n", "\n", texto, flags=re.I)
    # Eliminar líneas huérfanas de números de página
    texto = re.sub(r"\n\s*\d{1,4}\s*\n", "\n\n", texto)
    # Reducir secuencias excesivas de saltos de línea
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def cosechar_issues_historicos() -> List[Dict[str, Any]]:
    """Recorre las 6 páginas del archivo OJS y extrae los 84 números de 1974 a 2005."""
    print("  [*] Cosechando números históricos (1974-2005) desde el portal OJS UC...")
    issues: List[Dict[str, Any]] = []
    
    for page in range(1, 7):
        url = f"{BASE_URL}/issue/archive/{page}"
        try:
            r = requests.get(url, impersonate="chrome124", timeout=20)
            if r.status_code != 200:
                print(f"    [!] Error al obtener página {page}: status {r.status_code}")
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=re.compile(r"/issue/view/\d+")):
                txt = a.get_text(strip=True)
                m = re.search(r"\((\d{4})\)", txt)
                if m:
                    year = int(m.group(1))
                    if 1974 <= year <= 2005:
                        href = a["href"]
                        if not any(iss["href"] == href for iss in issues):
                            vol_m = re.search(r"Vol\.\s*(\d+)", txt, re.I)
                            num_m = re.search(r"N[uú]m\.\s*([\d-]+)", txt, re.I)
                            issues.append({
                                "title": txt,
                                "year": year,
                                "volume": vol_m.group(1) if vol_m else "1",
                                "numero": num_m.group(1) if num_m else "1",
                                "href": href
                            })
        except Exception as e:
            print(f"    [!] Excepción en página {page}: {e}")

    # Ordenar cronológicamente (1974 primero)
    issues.sort(key=lambda x: (x["year"], int(x["volume"]) if x["volume"].isdigit() else 0, x["title"]))
    print(f"  ✓ {len(issues)} números históricos catalogados (años {issues[0]['year']} a {issues[-1]['year']}).")
    return issues


def cosechar_articulos_de_issue(iss: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extrae todos los artículos de un número específico en OJS."""
    url = iss["href"]
    try:
        r = requests.get(url, impersonate="chrome124", timeout=25)
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        articulos = []
        for art_el in soup.select(".obj_article_summary"):
            title_el = art_el.select_one(".title") or art_el.select_one("h3") or art_el.select_one("h4")
            authors_el = art_el.select_one(".authors")
            pages_el = art_el.select_one(".pages")
            galleys = art_el.select(".galleys_links a, .obj_galley_link")

            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue
            a_tag = title_el.find("a") if title_el else None
            art_url = str(a_tag["href"]) if a_tag and "href" in a_tag.attrs else ""
            authors_raw = authors_el.get_text(strip=True) if authors_el else ""
            pages = pages_el.get_text(strip=True) if pages_el else ""

            # Extraer ID del artículo
            art_id_m = re.search(r"/article/view/(\d+)", art_url)
            art_id = art_id_m.group(1) if art_id_m else str(hash(title))[:8]

            pdf_download_url = ""
            for g in galleys:
                ghref = str(g.get("href", ""))
                if "/article/view/" in ghref:
                    pdf_download_url = ghref.replace("/article/view/", "/article/download/")
                    break

            articulos.append({
                "art_id": art_id,
                "title": title,
                "url": art_url,
                "pdf_url": pdf_download_url,
                "authors_raw": authors_raw,
                "pages": pages,
                "year": iss["year"],
                "volume": iss["volume"],
                "numero": iss["numero"],
                "issue_title": iss["title"],
                "issue_url": iss["href"]
            })
        return articulos
    except Exception as e:
        print(f"    [!] Error al cosechar {iss['title']}: {e}")
        return []


def procesar_articulo(art: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Descarga el PDF, extrae el texto con pdftotext y genera el Markdown canónico."""
    year = art["year"]
    art_id = art["art_id"]
    title = art["title"]
    authors_fmt = formatear_autor(art["authors_raw"])
    vol = art["volume"]
    num = art["numero"]
    pages = art["pages"]
    pdf_url = art["pdf_url"]

    slug = slugify(title)
    if not slug:
        slug = f"articulo_{art_id}"
    md_filename = f"{art_id}_{slug}.md"
    year_dir = OUTPUT_DIR / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)
    target_md = year_dir / md_filename

    # Si ya existe y tiene más de 1KB, no re-procesar
    if target_md.exists() and target_md.stat().st_size > 1024:
        return {"art_id": art_id, "year": year, "md_path": target_md, "nuevo": False}

    texto_cuerpo = ""
    if pdf_url:
        try:
            r = requests.get(pdf_url, impersonate="chrome124", timeout=30)
            if r.status_code == 200 and len(r.content) > 1000 and r.content.startswith(b"%PDF"):
                with tempfile.NamedTemporaryFile(suffix=".pdf") as tf:
                    tf.write(r.content)
                    tf.flush()
                    pdftotext_bin = shutil.which("pdftotext") or "/usr/bin/pdftotext"
                    res = subprocess.run(
                        [pdftotext_bin, tf.name, "-"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if res.returncode == 0 and res.stdout.strip():
                        texto_cuerpo = limpiar_texto_pdf(res.stdout)
        except Exception:
            pass

    # Si no se pudo extraer texto del PDF, construir contenido mínimo con metadata
    if not texto_cuerpo or len(texto_cuerpo) < 150:
        texto_cuerpo = (
            f"El texto íntegro digitalizado de este artículo histórico se encuentra preservado "
            f"en los archivos de la Revista Chilena de Derecho.\n\n"
            f"Referencia de publicación: Volumen {vol}, Número {num}, páginas {pages}.\n\n"
            f"Repositorio oficial: {art['url']}"
        )

    area = inferir_area(title, texto_cuerpo)
    normas = extraer_normas_citadas(texto_cuerpo)

    # Corchete oficial de citación estándar de la suite
    cita_oficial = f"[RChD - Vol. {vol} N° {num} ({year}), {authors_fmt}, {title}]"

    frontmatter = [
        "---",
        f'titulo: "{title}"',
        f'autores: "{authors_fmt}"',
        'revista: "Revista Chilena de Derecho"',
        f'issn_impreso: "{ISSN_PRINT}"',
        f'issn_electronico: "{ISSN_ELEC}"',
        f'volumen: "{vol}"',
        f'numero: "{num}"',
        f"anio: {year}",
        f'paginas: "{pages}"',
        f'area_derecho: "{area}"',
        f'url_ojs: "{art["url"]}"',
        f'cita_oficial: "{cita_oficial}"',
        "normas_citadas:",
    ]
    for n in normas:
        frontmatter.append(f'  - "{n}"')
    frontmatter.append("---\n")

    md_content = "\n".join(frontmatter) + f"\n# {title}\n\n**Autor:** {authors_fmt}\n\n**Cita Oficial:** {cita_oficial}\n\n---\n\n{texto_cuerpo}\n"

    target_md.write_text(md_content, encoding="utf-8")
    return {"art_id": art_id, "year": year, "md_path": target_md, "nuevo": True}


def subir_articulos_a_huggingface(repo_id: str = "pablobenavidesj/doctrina-jurisprudencia-chile") -> bool:
    """Sube la colección histórica de RChD al dataset de Hugging Face Hub."""
    token = resolver_token_hf()
    if not token:
        print("  [!] No se encontró HF_TOKEN en el entorno o en el almacén seguro.")
        return False

    from huggingface_hub import HfApi
    api = HfApi(token=token)

    print(f"  [*] Subiendo artículos históricos RChD (1974-2005) a Hugging Face: {repo_id}...")
    try:
        api.upload_folder(
            folder_path=str(OUTPUT_DIR),
            repo_id=repo_id,
            repo_type="dataset",
            path_in_repo="doctrina/revistas/rchd",
            commit_message="feat(doctrina): ingesta de coleccion historica Revista Chilena de Derecho (1974-2005)",
        )
        print("  ✓ Carpeta doctrina/revistas/rchd subida con éxito a Hugging Face.")
        return True
    except Exception as e:
        print(f"  [!] Error al subir a Hugging Face: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Ingesta histórica de la Revista Chilena de Derecho (1974-2005)")
    parser.add_argument("--solo-cosecha", action="store_true", help="Solo cosechar catálogo de artículos sin descargar")
    parser.add_argument("--subir-hf", action="store_true", help="Subir artículos convertidos a Hugging Face Hub")
    parser.add_argument("--workers", type=int, default=8, help="Número de hilos para descarga y procesamiento")
    parser.add_argument("--limite", type=int, default=0, help="Límite de artículos a procesar (0 para todos)")
    args = parser.parse_args()

    print("=" * 70)
    print("  INGESTA HISTÓRICA: REVISTA CHILENA DE DERECHO UC (1974-2005)")
    print("=" * 70)

    # 1. Cosechar los 84 números históricos
    issues = cosechar_issues_historicos()

    # 2. Cosechar artículos de cada número
    print(f"  [*] Extrayendo artículos de los {len(issues)} números históricos...")
    todos_articulos: List[Dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(cosechar_articulos_de_issue, iss): iss for iss in issues}
        for fut in concurrent.futures.as_completed(futures):
            arts = fut.result()
            todos_articulos.extend(arts)

    # Ordenar por año, volumen, ID
    todos_articulos.sort(key=lambda x: (x["year"], x["volume"], x["art_id"]))
    print(f"  ✓ Total de artículos históricos identificados: {len(todos_articulos)}")

    # Guardar manifiesto
    with open(CATALOGO_HISTORICO, "w", encoding="utf-8") as f:
        for art in todos_articulos:
            f.write(json.dumps(art, ensure_ascii=False) + "\n")
    print(f"  ✓ Catálogo guardado en {CATALOGO_HISTORICO.relative_to(ROOT_DIR)}")

    if args.solo_cosecha:
        print("  [i] Modo --solo-cosecha activo. Finalizando.")
        return

    articulos_a_procesar = todos_articulos
    if args.limite > 0:
        articulos_a_procesar = todos_articulos[:args.limite]
        print(f"  [i] Procesando muestra limitada a {len(articulos_a_procesar)} artículos.")

    # 3. Descarga y conversión paralela a Markdown
    print(f"  [*] Descargando y convirtiendo {len(articulos_a_procesar)} artículos históricos con {args.workers} hilos...")
    procesados = 0
    nuevos = 0
    t0 = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(procesar_articulo, art): art for art in articulos_a_procesar}
        for fut in concurrent.futures.as_completed(futures):
            res = fut.result()
            procesados += 1
            if res and res.get("nuevo"):
                nuevos += 1
            if procesados % 50 == 0 or procesados == len(articulos_a_procesar):
                elapsed = time.time() - t0
                tasa = procesados / elapsed if elapsed > 0 else 0
                print(f"    -> {procesados}/{len(articulos_a_procesar)} artículos procesados ({nuevos} nuevos, {tasa:.1f} art/seg)...")

    print(f"  ✓ Proceso de conversión finalizado: {procesados} artículos procesados en {time.time() - t0:.1f}s.")

    # 4. Regenerar catálogos
    print("  [*] Generando dataset base train.jsonl para indexación de obras...")
    from online_library_sync import OnlineLibrarySyncManager
    mgr = OnlineLibrarySyncManager()
    mgr.generar_dataset_train_jsonl()

    print("  [*] Regenerando catálogos ligeros y de citas...")
    subprocess.run([sys.executable, str(ROOT_DIR / "scripts" / "optimizar_catalogo_hf.py")], cwd=str(ROOT_DIR), check=True)

    # 5. Subida opcional a Hugging Face
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
                            commit_message=f"chore(catalogo): sincronizar {repo_path} con coleccion historica RChD (1974-2005)",
                        )
                        print(f"  ✓ {repo_path} actualizado en Hugging Face.")
                    except Exception as e:
                        print(f"  [!] Error al subir {repo_path}: {e}")

    print("\n" + "=" * 70)
    print("  INGESTA HISTÓRICA COMPLETADA")
    print("=" * 70)


if __name__ == "__main__":
    main()
