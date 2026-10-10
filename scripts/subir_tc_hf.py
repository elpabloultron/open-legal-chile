#!/usr/bin/env python3
"""
Open Legal Chile — Sube a Hugging Face (`jurisprudencia_tc/`) las sentencias del Tribunal
Constitucional convertidas a Markdown por `scripts/tc_pdfs_a_md.py`.

- Antes de subir, cada archivo pasa por el extractor del mapa del corpus: si su cabecera y su texto
  son de causas distintas, NO se sube.
- Se sube por lotes (un commit cada ~300 archivos): un commit gigante que falla pierde la corrida
  entera. Los archivos idénticos a los publicados no generan cambios.
- Al final, un commit borra los .md publicados que esta corrida no rehízo y que tienen la cabecera
  de una causa y el texto de otra (el defecto de la cosecha anterior), los restos de prueba
  (`testrol*`) y los de causas que el TC marcó como reservadas. Es preferible que falten a que sigan
  publicados con el texto de otra causa. Lo que no se pudo leer no se borra.

El mapa del corpus los toma en su corrida diaria.

Uso: HF_TOKEN=… python scripts/subir_tc_hf.py [--carpeta jurisprudencia_tc] [--dry-run] [--exigir-subida]
                                             [--reservadas tc_reservadas.txt]
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import pathlib
import sys
import time
from typing import Any, Callable, Dict, Iterable, List, Optional

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
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    sesion = requests.Session()
    sesion.mount("https://", HTTPAdapter(max_retries=Retry(
        total=5, backoff_factor=2, status_forcelist=(429, 500, 502, 503, 504), allowed_methods=("GET",))))
    if token:
        sesion.headers["Authorization"] = f"Bearer {token}"

    def bajar(ruta: str) -> bytes:
        r = sesion.get(f"{ENDPOINT}/datasets/{repo_id}/resolve/main/{ruta}", timeout=60)
        r.raise_for_status()
        return r.content
    return bajar


def defectuosos_remotos(api: Any, repo_id: str, validos: List[str], bajar: Callable[[str], bytes],
                        reservadas: Iterable[str] = ()) -> Dict[str, List[str]]:
    """Los .md publicados que hay que retirar: los que esta corrida no rehízo y tienen la cabecera de
    otra causa, los restos de prueba y los de causas que el TC marcó como reservadas (estos sin
    descargarlos). Lo que no se puede leer NO se retira: queda en `sin_revisar`."""
    nuevos, reservados = set(validos), set(reservadas)
    borrar: List[str] = []
    sin_revisar: List[str] = []
    for entrada in api.list_repo_tree(repo_id, repo_type="dataset", path_in_repo=RUTA_HF):
        ruta = getattr(entrada, "path", "")
        nombre = ruta.rsplit("/", 1)[-1]
        if not ruta.endswith(".md") or nombre == "README.md" or nombre in nuevos:
            continue
        if nombre in reservados or any(fnmatch.fnmatch(nombre, patron) for patron in BORRAR):
            borrar.append(ruta)
            continue
        try:
            datos = bajar(ruta)
        except Exception as e:  # noqa: BLE001 — red o HF: sin leerlo no se decide retirarlo
            print(f"  [HF] no se pudo revisar {ruta}: {str(e)[:80]}", file=sys.stderr)
            sin_revisar.append(ruta)
            continue
        if _desalineado(ruta, datos):
            borrar.append(ruta)
    return {"borrar": sorted(borrar), "sin_revisar": sorted(sin_revisar)}


def _reintentable(e: Exception) -> bool:
    """Red y 5xx/429 sí; un 4xx (permiso, ruta inexistente, conflicto) o un error del programa no se
    arreglan reintentando."""
    estado = getattr(getattr(e, "response", None), "status_code", None)
    if estado is not None:
        return estado >= 500 or estado == 429
    return isinstance(e, (requests.ConnectionError, requests.Timeout, OSError)) or type(e).__module__.startswith("httpx")


def _commit(api: Any, repo_id: str, operaciones: Callable[[], List[Any]], mensaje: str,
            intentos: int = 3) -> str:
    """Un commit en HF. Las operaciones se recrean en cada intento (las ya usadas guardan el estado
    remoto de antes y reenviarían un lote que sí entró). Devuelve "" si no hubo nada que cambiar."""
    for intento in range(intentos):
        ops = operaciones()
        if not ops:
            return ""
        try:
            antes = str(getattr(api.repo_info(repo_id, repo_type="dataset"), "sha", "") or "")
            info = api.create_commit(repo_id=repo_id, repo_type="dataset", operations=ops, commit_message=mensaje)
            oid = str(getattr(info, "oid", "") or info)
            return "" if oid and oid == antes else oid      # lote sin cambios: HF no crea commit
        except Exception as e:  # noqa: BLE001 — se decide abajo si vale la pena reintentar
            if intento == intentos - 1 or not _reintentable(e):
                raise
            print(f"  [HF] reintento del commit ({str(e)[:80]})", file=sys.stderr)
            time.sleep(10 * 2 ** intento)
    return ""


def subir(carpeta: pathlib.Path, token: Optional[str], repo_id: str = REPO_ID, api: Any = None,
          dry_run: bool = False, bajar: Optional[Callable[[str], bytes]] = None, lote: int = LOTE,
          reservadas: Iterable[str] = ()) -> Dict[str, Any]:
    revision = revisar(carpeta)
    validos = revision["validos"]
    if api is None:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
    bajar = bajar or _bajar_hf(token, repo_id)
    resumen: Dict[str, Any] = {"subibles": len(validos), "rechazados": revision["rechazados"]}
    if dry_run:
        return {**resumen, **defectuosos_remotos(api, repo_id, validos, bajar, reservadas), "subido": False,
                "commits": []}

    from huggingface_hub import CommitOperationAdd, CommitOperationDelete
    commits: List[str] = []
    for i in range(0, len(validos), lote):
        tanda = validos[i:i + lote]
        if i == 0 and (carpeta / "README.md").exists():
            tanda = ["README.md"] + tanda       # la descripción de la carpeta viaja con el primer lote
        def altas(t: List[str] = tanda) -> List[Any]:
            return [CommitOperationAdd(path_in_repo=f"{RUTA_HF}/{n}", path_or_fileobj=str(carpeta / n)) for n in t]
        commits.append(_commit(api, repo_id, altas,
                               f"TC: {len(tanda)} sentencias en Markdown (lote {i // lote + 1}; documento oficial "
                               "por número de rol, verificado)"))
    # El barrido va después de las altas: si falla, lo nuevo ya quedó publicado.
    remotos = defectuosos_remotos(api, repo_id, validos, bajar, reservadas)

    def bajas() -> List[Any]:
        if not remotos["borrar"]:
            return []
        existentes = {p.path for p in api.get_paths_info(repo_id, remotos["borrar"], repo_type="dataset")}
        return [CommitOperationDelete(path_in_repo=r) for r in remotos["borrar"] if r in existentes]

    commits.append(_commit(api, repo_id, bajas, f"TC: se retiran {len(remotos['borrar'])} archivos con la cabecera "
                                               "de una causa y el texto de otra, de prueba o de causas reservadas"))
    reales = [c for c in commits if c]
    return {**resumen, **remotos, "subido": bool(reales), "commits": reales}


def main() -> int:
    ap = argparse.ArgumentParser(description="Sube a HF las sentencias del TC en Markdown.")
    ap.add_argument("--carpeta", default=str(BASE / RUTA_HF))
    ap.add_argument("--dry-run", action="store_true", help="solo revisar (lee lo publicado, no sube ni borra)")
    ap.add_argument("--exigir-subida", action="store_true", help="error si no hay nada que subir")
    ap.add_argument("--reservadas", default="", help="archivo con los nombres de las causas reservadas (se retiran)")
    args = ap.parse_args()
    token = os.environ.get("HF_TOKEN") or None
    if not token and not args.dry_run:
        print("Falta HF_TOKEN (token con escritura en el dataset).", file=sys.stderr)
        return 2
    reservadas = []
    if args.reservadas and pathlib.Path(args.reservadas).exists():
        reservadas = [n.strip() for n in pathlib.Path(args.reservadas).read_text(encoding="utf-8").splitlines() if n.strip()]
    res = subir(pathlib.Path(args.carpeta), token, dry_run=args.dry_run, reservadas=reservadas)
    lineas = [f"### Subida del TC a Hugging Face{' (simulada)' if args.dry_run else ''}", "",
              f"- subibles: {res['subibles']}",
              f"- rechazados (cabecera de otra causa): {len(res['rechazados'])}",
              f"- se retiran de HF (defectuosos no rehechos, de prueba o reservados): {len(res['borrar'])}",
              f"- no se pudieron revisar (se dejan como están): {len(res['sin_revisar'])}",
              f"- commits: {', '.join(c[:10] for c in res['commits']) or '—'}"]
    lineas += [f"  - retirado: `{r}`" for r in res["borrar"]]
    lineas += [f"  - sin revisar: `{r}`" for r in res["sin_revisar"]]
    lineas += [f"  - rechazado: `{r}`" for r in res["rechazados"]]
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
