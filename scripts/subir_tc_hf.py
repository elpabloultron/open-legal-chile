#!/usr/bin/env python3
"""
Open Legal Chile — Sube a Hugging Face (`jurisprudencia_tc/`) las sentencias del Tribunal
Constitucional convertidas a Markdown por `scripts/tc_pdfs_a_md.py`.

- Antes de subir, cada archivo pasa por el extractor del mapa del corpus: si su cabecera y su texto
  son de causas distintas, NO se sube.
- Se sube por lotes (un commit cada ~300 archivos): un commit gigante que falla pierde la corrida
  entera. Los archivos idénticos a los publicados no generan cambios.
- Al final, un commit borra los .md publicados que esta corrida no rehízo y que tienen la cabecera
  de una causa y el texto de otra (el defecto de la cosecha anterior), más los restos de prueba
  (`testrol*`). Es preferible que falten a que sigan publicados con el texto de otra causa.

El mapa del corpus los toma en su corrida diaria.

Uso: HF_TOKEN=… python scripts/subir_tc_hf.py [--carpeta jurisprudencia_tc] [--dry-run] [--exigir-subida]
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import pathlib
import sys
import time
from typing import Any, Callable, Dict, List, Optional

import requests

BASE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from mapa_corpus.extractores import fila_tc  # noqa: E402

REPO_ID = "pablobenavidesj/doctrina-jurisprudencia-chile"
RUTA_HF = "jurisprudencia_tc"
ENDPOINT = os.environ.get("HF_ENDPOINT", "https://huggingface.co").rstrip("/")
# Restos de pruebas que no son sentencias («testrol2-34566.md»): se borran del dataset.
BORRAR = ["testrol*"]
LOTE = 300


def _desalineado(ruta: str, datos: bytes) -> bool:
    return "cabecera_desalineada" in (fila_tc(ruta, datos, "").get("calidad") or [])


def revisar(carpeta: pathlib.Path) -> Dict[str, List[str]]:
    """Separa los .md que se pueden subir de los que tienen la cabecera de otra causa."""
    validos: List[str] = []
    rechazados: List[str] = []
    for md in sorted(carpeta.glob("*.md")):
        if md.name == "README.md":
            continue
        (rechazados if _desalineado(f"{RUTA_HF}/{md.name}", md.read_bytes()) else validos).append(md.name)
    return {"validos": validos, "rechazados": rechazados}


def _bajar_hf(token: Optional[str], repo_id: str) -> Callable[[str], bytes]:
    def bajar(ruta: str) -> bytes:
        cabeceras = {"Authorization": f"Bearer {token}"} if token else {}
        r = requests.get(f"{ENDPOINT}/datasets/{repo_id}/resolve/main/{ruta}", headers=cabeceras, timeout=60)
        r.raise_for_status()
        return r.content
    return bajar


def defectuosos_remotos(api: Any, repo_id: str, validos: List[str], bajar: Callable[[str], bytes]) -> List[str]:
    """Los .md publicados que esta corrida no rehízo y que tienen la cabecera de otra causa."""
    nuevos = set(validos)
    borrar: List[str] = []
    for entrada in api.list_repo_tree(repo_id, repo_type="dataset", path_in_repo=RUTA_HF):
        ruta = getattr(entrada, "path", "")
        nombre = ruta.rsplit("/", 1)[-1]
        if not ruta.endswith(".md") or nombre == "README.md" or nombre in nuevos:
            continue
        if any(fnmatch.fnmatch(nombre, patron) for patron in BORRAR) or _desalineado(ruta, bajar(ruta)):
            borrar.append(ruta)
    return sorted(borrar)


def _commit(api: Any, repo_id: str, operaciones: List[Any], mensaje: str, intentos: int = 3) -> str:
    for intento in range(intentos):
        try:
            info = api.create_commit(repo_id=repo_id, repo_type="dataset", operations=operaciones,
                                     commit_message=mensaje)
            return str(getattr(info, "oid", "") or info)
        except Exception as e:  # noqa: BLE001 — red o 5xx de HF: se reintenta el lote
            if intento == intentos - 1:
                raise
            print(f"  [HF] reintento del commit ({str(e)[:80]})", file=sys.stderr)
            time.sleep(10 * 2 ** intento)
    return ""


def subir(carpeta: pathlib.Path, token: Optional[str], repo_id: str = REPO_ID, api: Any = None,
          dry_run: bool = False, bajar: Optional[Callable[[str], bytes]] = None, lote: int = LOTE) -> Dict[str, Any]:
    revision = revisar(carpeta)
    validos = revision["validos"]
    if api is None:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
    borrar = defectuosos_remotos(api, repo_id, validos, bajar or _bajar_hf(token, repo_id))
    resumen: Dict[str, Any] = {"subibles": len(validos), "rechazados": revision["rechazados"], "borrar": borrar}
    if dry_run or not (validos or borrar):
        return {**resumen, "subido": False, "commits": []}

    from huggingface_hub import CommitOperationAdd, CommitOperationDelete
    commits: List[str] = []
    for i in range(0, len(validos), lote):
        tanda = validos[i:i + lote]
        if i == 0 and (carpeta / "README.md").exists():
            tanda = ["README.md"] + tanda       # la descripción de la carpeta viaja con el primer lote
        operaciones = [CommitOperationAdd(path_in_repo=f"{RUTA_HF}/{n}", path_or_fileobj=str(carpeta / n)) for n in tanda]
        commits.append(_commit(api, repo_id, operaciones,
                               f"TC: {len(tanda)} sentencias en Markdown (lote {i // lote + 1}; documento oficial "
                               "por número de rol, verificado)"))
    if borrar:
        commits.append(_commit(api, repo_id, [CommitOperationDelete(path_in_repo=r) for r in borrar],
                               f"TC: se retiran {len(borrar)} archivos con la cabecera de una causa y el texto de otra"))
    return {**resumen, "subido": True, "commits": commits}


def main() -> int:
    ap = argparse.ArgumentParser(description="Sube a HF las sentencias del TC en Markdown.")
    ap.add_argument("--carpeta", default=str(BASE / RUTA_HF))
    ap.add_argument("--dry-run", action="store_true", help="solo revisar (lee lo publicado, no sube ni borra)")
    ap.add_argument("--exigir-subida", action="store_true", help="error si no hay nada que subir")
    args = ap.parse_args()
    token = os.environ.get("HF_TOKEN") or None
    if not token and not args.dry_run:
        print("Falta HF_TOKEN (token con escritura en el dataset).", file=sys.stderr)
        return 2
    res = subir(pathlib.Path(args.carpeta), token, dry_run=args.dry_run)
    lineas = [f"### Subida del TC a Hugging Face{' (simulada)' if args.dry_run else ''}", "",
              f"- subibles: {res['subibles']}",
              f"- rechazados (cabecera de otra causa): {len(res['rechazados'])}",
              f"- se retiran de HF (defectuosos no rehechos y restos de prueba): {len(res['borrar'])}",
              f"- commits: {', '.join(c[:10] for c in res['commits']) or '—'}"]
    lineas += [f"  - retirado: `{r}`" for r in res["borrar"][:300]]
    lineas += [f"  - rechazado: `{r}`" for r in res["rechazados"][:100]]
    print("\n".join(lineas))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("\n".join(lineas) + "\n")
    if args.exigir_subida and not res["subibles"]:
        print("::error::No hay sentencias del TC para subir: revisa la cosecha y la conversión.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
