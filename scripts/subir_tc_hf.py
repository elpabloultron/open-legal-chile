#!/usr/bin/env python3
"""
Open Legal Chile — Sube a Hugging Face (`jurisprudencia_tc/`) las sentencias del Tribunal
Constitucional convertidas a Markdown por `scripts/tc_pdfs_a_md.py`.

Antes de subir, cada archivo pasa por el extractor del mapa del corpus: si su cabecera y su texto
son de causas distintas (el defecto de la cosecha anterior), NO se sube. Solo se suben los
archivos que cambiaron (upload_folder compara con lo publicado). El mapa del corpus los toma en su
corrida diaria.

Uso: HF_TOKEN=… python scripts/subir_tc_hf.py [--carpeta jurisprudencia_tc] [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
from typing import Any, Dict, List, Optional

BASE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from mapa_corpus.extractores import fila_tc  # noqa: E402

REPO_ID = "pablobenavidesj/doctrina-jurisprudencia-chile"
RUTA_HF = "jurisprudencia_tc"
# Restos de pruebas que no son sentencias («testrol2-34566.md»): se borran del dataset.
BORRAR = ["testrol*"]


def revisar(carpeta: pathlib.Path) -> Dict[str, List[str]]:
    """Separa los .md que se pueden subir de los que tienen la cabecera de otra causa."""
    validos: List[str] = []
    rechazados: List[str] = []
    for md in sorted(carpeta.glob("*.md")):
        if md.name == "README.md":
            continue
        fila = fila_tc(f"{RUTA_HF}/{md.name}", md.read_bytes(), "")
        if "cabecera_desalineada" in (fila.get("calidad") or []):
            rechazados.append(md.name)
        else:
            validos.append(md.name)
    return {"validos": validos, "rechazados": rechazados}


def subir(carpeta: pathlib.Path, token: Optional[str], repo_id: str = REPO_ID, api: Any = None,
          dry_run: bool = False) -> Dict[str, Any]:
    revision = revisar(carpeta)
    resumen: Dict[str, Any] = {"subibles": len(revision["validos"]), "rechazados": revision["rechazados"]}
    if dry_run or not revision["validos"]:
        return {**resumen, "subido": False}
    if api is None:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
    info = api.upload_folder(
        repo_id=repo_id, repo_type="dataset", folder_path=str(carpeta), path_in_repo=RUTA_HF,
        allow_patterns=revision["validos"], delete_patterns=BORRAR,
        commit_message=f"TC: {len(revision['validos'])} sentencias en Markdown (documento oficial por número de rol)",
    )
    return {**resumen, "subido": True, "commit": str(getattr(info, "oid", "") or info)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Sube a HF las sentencias del TC en Markdown.")
    ap.add_argument("--carpeta", default=str(BASE / RUTA_HF))
    ap.add_argument("--dry-run", action="store_true", help="solo revisar, sin subir")
    args = ap.parse_args()
    token = os.environ.get("HF_TOKEN") or None
    if not token and not args.dry_run:
        print("Falta HF_TOKEN (token con escritura en el dataset).", file=sys.stderr)
        return 2
    res = subir(pathlib.Path(args.carpeta), token, dry_run=args.dry_run)
    print(f"subibles: {res['subibles']} · rechazados (cabecera de otra causa): {len(res['rechazados'])}"
          f" · subido: {res['subido']} {res.get('commit', '')}")
    for nombre in res["rechazados"][:20]:
        print(f"  [!] {nombre}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
