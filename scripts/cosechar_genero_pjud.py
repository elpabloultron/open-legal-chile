#!/usr/bin/env python3
"""
Open Legal Chile — Extractor del Repositorio y Concurso de Sentencias con Perspectiva de Género PJUD
Fuentes oficiales:
  1. https://secretariadegenero.pjud.cl/index.php/repositorio (241 PDFs: Sentencias + Matrices de Análisis)
  2. https://secretariadegenero.pjud.cl/index.php/repositorio/concurso-de-sentencias-con-perspectiva-de-genero
     (1.° a 5.° Concurso Nacional 2021-2026: Sentencias Destacadas, Menciones Honrosas y Cuadernos de Buenas Prácticas)
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import time
import urllib.parse
from typing import Any, Dict, List
import requests
from bs4 import BeautifulSoup

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
JSONL_OUT = BASE_DIR / "data" / "jurisprudencia" / "pjud_genero.jsonl"
MD_DIR = BASE_DIR / "jurisprudencia_genero"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


def _extraer_texto_pdf_bytes(pdf_bytes: bytes, max_paginas: int = 12) -> str:
    """Extrae texto limpio de los primeros `max_paginas` de un PDF usando PyMuPDF (fitz)."""
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        paginas = []
        for i in range(min(len(doc), max_paginas)):
            txt = doc[i].get_text("text") or ""
            if txt.strip():
                paginas.append(txt.strip())
        doc.close()
        texto = "\n\n".join(paginas)
        texto = re.sub(r"[ \t]+", " ", texto)
        return re.sub(r"\n{3,}", "\n\n", texto).strip()
    except Exception:
        return ""


class SecretariaGeneroScraper:
    URL_BASE = "https://secretariadegenero.pjud.cl"
    URL_REPOSITORIO = f"{URL_BASE}/index.php/repositorio"
    URL_CONCURSO = f"{URL_BASE}/index.php/repositorio/concurso-de-sentencias-con-perspectiva-de-genero"
    PAGINAS_CONCURSO = [
        "/index.php/resultados2021",
        "/index.php/29-concurso-de-sentencias/49-resultados-2022",
        "/index.php/29-concurso-de-sentencias/57-resultados-2023",
        "/index.php/29-concurso-de-sentencias/71-resultados-2024",
        "/index.php/29-concurso-de-sentencias/81-resultados-2026",
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept-Language": "es-CL,es;q=0.9",
        })

    def recolectar_catalogo_repositorio(self) -> List[Dict[str, Any]]:
        """Parsea el repositorio general de sentencias y agrupa cada fallo con su matriz de análisis."""
        r = self.session.get(self.URL_REPOSITORIO, timeout=25)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        pares: Dict[str, Dict[str, Any]] = {}
        for a in soup.find_all("a", href=True):
            href = str(a["href"]).strip()
            if ".pdf" not in href.lower():
                continue
            url_abs = urllib.parse.urljoin(self.URL_BASE, href)
            # Ejemplo: /images/documentos/fallos/repositorio/2020/1_fallo_Violencia_Intrafamiliar.pdf
            m = re.search(r"/repositorio/(\d{4})/(\d+)_(fallo|matriz)_([^/]+)\.pdf", href, re.IGNORECASE)
            if m:
                anio, num, clase, tema_raw = m.group(1), m.group(2), m.group(3).lower(), urllib.parse.unquote(m.group(4))
                clave = f"repo_{anio}_{num}"
                tema = tema_raw.replace("_", " ").strip()
                item = pares.setdefault(clave, {
                    "id": clave,
                    "rol": f"STG-{anio}-{num}",
                    "portal": "genero",
                    "coleccion_genero": "Repositorio de Sentencias con Perspectiva de Género",
                    "anio": anio,
                    "fecha": f"{anio}-01-01",
                    "tribunal": "Poder Judicial — Secretaría Técnica de Igualdad de Género y No Discriminación",
                    "sala": "Jurisprudencia con Perspectiva de Género",
                    "caratula": f"Sentencia y Matriz con Perspectiva de Género N.° {num} ({anio}): {tema}",
                    "materia": tema,
                    "recurso": "Fallo + Matriz de Análisis de Género",
                    "resultado": "Incorporada al Repositorio Oficial STG-PJUD",
                    "url_fallo": "",
                    "url_matriz": "",
                })
                if clase == "fallo":
                    item["url_fallo"] = url_abs
                else:
                    item["url_matriz"] = url_abs
            else:
                nombre = pathlib.PurePosixPath(urllib.parse.unquote(href)).stem.replace("_", " ")
                clave = f"repo_doc_{len(pares) + 1}"
                pares[clave] = {
                    "id": clave,
                    "rol": f"STG-DOC-{len(pares) + 1}",
                    "portal": "genero",
                    "coleccion_genero": "Repositorio de Sentencias con Perspectiva de Género",
                    "anio": "2024",
                    "fecha": "2024-01-01",
                    "tribunal": "Poder Judicial — Secretaría Técnica de Igualdad de Género y No Discriminación",
                    "sala": "Jurisprudencia con Perspectiva de Género",
                    "caratula": f"Documento STG-PJUD: {nombre}",
                    "materia": nombre,
                    "recurso": "Sentencia con Perspectiva de Género",
                    "resultado": "Repositorio Oficial STG-PJUD",
                    "url_fallo": url_abs,
                    "url_matriz": "",
                }
        return list(pares.values())

    def recolectar_catalogo_concurso(self) -> List[Dict[str, Any]]:
        """Parsea las páginas de resultados del 1.° al 5.° Concurso Nacional de Sentencias con Perspectiva de Género."""
        items: List[Dict[str, Any]] = []
        vistos_urls = set()

        urls_explorar = [self.URL_CONCURSO] + [urllib.parse.urljoin(self.URL_BASE, p) for p in self.PAGINAS_CONCURSO]
        for page_url in urls_explorar:
            try:
                r = self.session.get(page_url, timeout=20)
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, "html.parser")
                m_anio = re.search(r"(202\d)", page_url)
                anio = m_anio.group(1) if m_anio else "2025"

                for a in soup.find_all("a", href=True):
                    href = str(a["href"]).strip()
                    if ".pdf" not in href.lower():
                        continue
                    url_abs = urllib.parse.urljoin(self.URL_BASE, href)
                    if url_abs in vistos_urls:
                        continue
                    vistos_urls.add(url_abs)
                    nombre_archivo = pathlib.PurePosixPath(urllib.parse.unquote(href)).stem.replace("_", " ").replace("-", " ")
                    texto_link = " ".join(a.get_text(" ", strip=True).split()) or nombre_archivo
                    idx = len(items) + 1
                    items.append({
                        "id": f"concurso_{anio}_{idx}",
                        "rol": f"CONCURSO-GENERO-{anio}-{idx}",
                        "portal": "genero",
                        "coleccion_genero": f"Concurso Nacional de Sentencias con Perspectiva de Género ({anio})",
                        "anio": anio,
                        "fecha": f"{anio}-01-01",
                        "tribunal": "Poder Judicial — Concurso Nacional de Sentencias con Perspectiva de Género",
                        "sala": "Sentencia Destacada / Mención Honrosa",
                        "caratula": f"Concurso Perspectiva de Género ({anio}): {texto_link} — {nombre_archivo}",
                        "materia": f"Perspectiva de Género y No Discriminación — {nombre_archivo}",
                        "recurso": "Concurso Nacional STG-PJUD",
                        "resultado": "Sentencia Premiada / Destacada",
                        "url_fallo": url_abs,
                        "url_matriz": "",
                    })
            except Exception as exc:
                _ = exc
        return items

    def cosechar(self, max_descargas_pdf: int = 15, exportar_md: bool = True) -> Dict[str, Any]:
        repo_items = self.recolectar_catalogo_repositorio()
        concurso_items = self.recolectar_catalogo_concurso()
        todos = concurso_items + repo_items

        JSONL_OUT.parent.mkdir(parents=True, exist_ok=True)
        if exportar_md:
            MD_DIR.mkdir(parents=True, exist_ok=True)

        descargados = 0
        for it in todos:
            url_principal = it.get("url_matriz") or it.get("url_fallo") or ""
            it["url_corta"] = it.get("url_fallo") or url_principal
            it["url_origen"] = self.URL_CONCURSO if it["id"].startswith("concurso_") else self.URL_REPOSITORIO
            it["cita"] = f"[PJUD Secretaría de Género - {it['rol']}, Materia: {it['materia'][:60]}]"

            extracto_pdf = ""
            if descargados < max_descargas_pdf and url_principal:
                try:
                    resp_pdf = self.session.get(url_principal, timeout=20)
                    if resp_pdf.status_code == 200 and resp_pdf.content.startswith(b"%PDF"):
                        extracto_pdf = _extraer_texto_pdf_bytes(resp_pdf.content, max_paginas=6)
                        descargados += 1
                        time.sleep(0.1)
                except Exception:
                    pass

            resumen_base = (
                f"{it['caratula']}. Colección: {it['coleccion_genero']}. "
                f"Materia: {it['materia']}. "
                f"Fallo oficial: {it.get('url_fallo', 'N/D')}. "
                + (f"Matriz de análisis de género: {it['url_matriz']}." if it.get("url_matriz") else "")
            )
            it["texto_integral"] = f"{resumen_base}\n\n{extracto_pdf}".strip()
            it["extracto_relevante"] = (extracto_pdf[:600] if extracto_pdf else resumen_base)[:700]

            if exportar_md:
                slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", it["id"]).strip("_")[:60]
                rel_md = f"jurisprudencia_genero/{slug}.md"
                it["archivo_md"] = rel_md
                (BASE_DIR / rel_md).write_text(self._formatear_md(it), encoding="utf-8")

        with open(JSONL_OUT, "w", encoding="utf-8") as f:
            for it in todos:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")

        return {
            "total_repositorio": len(repo_items),
            "total_concurso": len(concurso_items),
            "total_registros": len(todos),
            "pdfs_procesados_con_texto": descargados,
            "archivo_jsonl": str(JSONL_OUT.relative_to(BASE_DIR)),
        }

    @staticmethod
    def _formatear_md(it: Dict[str, Any]) -> str:
        return (
            f"---\n"
            f"id: \"{it['id']}\"\n"
            f"rol: \"{it['rol']}\"\n"
            f"portal: \"genero\"\n"
            f"anio: \"{it['anio']}\"\n"
            f"coleccion: \"{it['coleccion_genero']}\"\n"
            f"url_fallo: \"{it.get('url_fallo', '')}\"\n"
            f"url_matriz: \"{it.get('url_matriz', '')}\"\n"
            f"---\n\n"
            f"# {it['caratula']}\n\n"
            f"- **Colección Oficial:** {it['coleccion_genero']}\n"
            f"- **Materia / Temática:** {it['materia']}\n"
            f"- **Cita Oficial:** `{it['cita']}`\n"
            f"- **Sentencia PDF:** {it.get('url_fallo') or 'No disponible'}\n"
            f"- **Matriz de Análisis de Género PDF:** {it.get('url_matriz') or 'No aplica'}\n\n"
            f"## Contenido y Síntesis con Perspectiva de Género\n\n"
            f"{it.get('texto_integral', '')}\n"
        )


def main():
    parser = argparse.ArgumentParser(description="Cosechador del Repositorio y Concurso de Género PJUD")
    parser.add_argument("--max-pdfs", type=int, default=15, help="Máximo de PDFs a descargar y extraer texto en esta corrida")
    parser.add_argument("--sin-md", action="store_true", help="No exportar fichas Markdown")
    args = parser.parse_args()
    scraper = SecretariaGeneroScraper()
    res = scraper.cosechar(max_descargas_pdf=args.max_pdfs, exportar_md=not args.sin_md)
    print(f"[+] Secretaría de Género PJUD cosechada: {res['total_registros']} registros "
          f"(Repositorio: {res['total_repositorio']}, Concurso: {res['total_concurso']}, "
          f"PDFs extraídos: {res['pdfs_procesados_con_texto']}) -> {res['archivo_jsonl']}")


if __name__ == "__main__":
    main()
