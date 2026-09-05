"""
Open Legal Chile — Buscador y Descargador de Fuentes Doctrinales Abiertas
Permite consultar e indexar repositorios jurídicos abiertos de Chile (Memoria Chilena,
Biblioteca del Congreso Nacional, Repositorio Universidad de Chile, Dialnet, SciELO)
para descargar tratados, obras históricas y estudios dogmáticos canónicos.
"""

import os
import sys
import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]


# Catálogo curado de tratados y obras dogmáticas abiertas de libre acceso en Chile
FUENTES_DOCTRINALES_ABIERTAS = [
    {
        "id": "claro_solar_civil",
        "area": "civil",
        "autor": "Luis Claro Solar",
        "obra": "Explicaciones de Derecho Civil Chileno y Comparado",
        "tomo": "De las Obligaciones (Tomo X al XII)",
        "url_fuente": "https://archive.org/download/explicacionesded00clar/explicacionesded00clar.pdf",
        "descripcion": "Tratado monumental clásico de las obligaciones y fuentes en el Código Civil chileno."
    },
    {
        "id": "alessandri_responsabilidad",
        "area": "civil",
        "autor": "Arturo Alessandri Rodríguez",
        "obra": "De la Responsabilidad Extracontractual en el Derecho Civil Chileno",
        "tomo": "Edición canónica",
        "url_fuente": "https://www.memoriachilena.gob.cl/archivos2/pdfs/MC0014761.pdf",
        "descripcion": "Obra fundacional sobre la culpa, daño y nexo causal bajo los Arts. 2314 y ss. del Código Civil."
    },
    {
        "id": "alessandri_compraventa",
        "area": "civil",
        "autor": "Arturo Alessandri Rodríguez",
        "obra": "De la Compraventa y de la Promesa de Venta",
        "tomo": "Tomos I y II",
        "url_fuente": "https://www.memoriachilena.gob.cl/archivos2/pdfs/MC0014762.pdf",
        "descripcion": "Tratado rector sobre el contrato de compraventa, tradición, evicción y vicios redhibitorios."
    },
    {
        "id": "soto_kloss_derecho_administrativo",
        "area": "administrativo",
        "autor": "Eduardo Soto Kloss",
        "obra": "El Derecho Administrativo en el Estado Constitucional",
        "tomo": "Estudios Dogmáticos",
        "url_fuente": "https://scielo.conicyt.cl/scielo.php?script=sci_arttext&pid=S0718-09502002000200003",
        "descripcion": "Fundamentos de la nulidad de derecho público, legalidad administrativa y tutela judicial efectiva."
    },
    {
        "id": "bermudez_sancionador",
        "area": "administrativo",
        "autor": "Jorge Bermúdez Soto",
        "obra": "El Derecho Administrativo Sancionador: Principios y Límites",
        "tomo": "Monografía Doctrinal",
        "url_fuente": "https://www.scielo.cl/scielo.php?script=sci_arttext&pid=S0718-09502013000200007",
        "descripcion": "Estudio canónico sobre tipicidad, culpabilidad y proporcionalidad en sanciones administrativas del Estado."
    }
]


class DoctrinaDownloader:
    def __init__(self, raw_dir: str = "/home/pablo/Escritorio/Ultimaprensa/open-legal-chile/doctrina_raw"):
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def list_curated_sources(self, area: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista las obras y tratados disponibles en el catálogo abierto."""
        if not area:
            return FUENTES_DOCTRINALES_ABIERTAS
        return [f for f in FUENTES_DOCTRINALES_ABIERTAS if f["area"].lower() == area.lower()]

    def download_source(self, source_id: str) -> Dict[str, Any]:
        """Descarga una obra del catálogo a doctrina_raw/."""
        match = next((f for f in FUENTES_DOCTRINALES_ABIERTAS if f["id"] == source_id), None)
        if not match:
            return {"error": f"Fuente con id '{source_id}' no encontrada en el catálogo."}

        url = match["url_fuente"]
        ext = ".pdf" if ".pdf" in url.lower() else ".html"
        dest = self.raw_dir / f"{source_id}{ext}"

        if dest.exists() and dest.stat().st_size > 1000:
            return {
                "source_id": source_id,
                "cached": True,
                "path": str(dest.resolve()),
                "size_kb": round(dest.stat().st_size / 1024, 1)
            }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OpenLegalChile/1.0"
        }
        try:
            from config import safe_urlopen
            req = urllib.request.Request(url, headers=headers)
            with safe_urlopen(req, timeout=30) as resp, open(dest, "wb") as f:
                f.write(resp.read())

            return {
                "source_id": source_id,
                "cached": False,
                "path": str(dest.resolve()),
                "size_kb": round(dest.stat().st_size / 1024, 1)
            }
        except Exception as e:
            return {"error": f"Error descargando {url}: {str(e)}"}


if __name__ == "__main__":
    dl = DoctrinaDownloader()
    print(f"Fuentes disponibles en el catálogo abierto: {len(dl.list_curated_sources())}")
    for s in dl.list_curated_sources():
        print(f" - [{s['area'].upper()}] {s['autor']} — {s['obra']}")
