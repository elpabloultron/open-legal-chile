"""Publicación del mapa en HF (un commit con solo lo que cambió) y escritura del puntero.

- `create_commit(parent_commit=<HEAD leído al empezar>)`: si `main` avanzó entretanto, HF
  rechaza el commit y la corrida termina como «superada» (la próxima toma lo nuevo).
- Antes de cada borrado se verifica que la ruta exista (un Delete de algo inexistente falla).
- Cada publicación queda con un tag `mapa-<n>`: las revisiones que fijan los paquetes ya
  instalados no deben desaparecer (nunca se aplasta el historial del dataset).
- Se niega a publicar si las versiones de NetworkX / huggingface_hub no son las fijadas para el
  constructor: otra versión de Louvain cambiaría las comunidades sin que cambie el corpus.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mapa_corpus import ESQUEMA, REPO_ID, RUTA_HF

log = logging.getLogger("mapa_corpus")

PUNTERO = Path(__file__).resolve().parent / "puntero.json"
RESTRICCIONES = Path(__file__).resolve().parent / "constraints-constructor.txt"


def versiones_fijadas() -> Dict[str, str]:
    salida: Dict[str, str] = {}
    for linea in RESTRICCIONES.read_text(encoding="utf-8").splitlines():
        linea = linea.split("#", 1)[0].strip()
        if "==" in linea:
            nombre, version = linea.split("==", 1)
            salida[nombre.strip().lower()] = version.strip()
    return salida


def versiones_distintas() -> List[str]:
    from importlib.metadata import PackageNotFoundError, version
    problemas = []
    for nombre, esperada in versiones_fijadas().items():
        try:
            instalada = version(nombre)
        except PackageNotFoundError:
            instalada = "ausente"
        if instalada != esperada:
            problemas.append(f"{nombre}=={instalada} (se espera {esperada})")
    return problemas


def operaciones(dir_mapa: str, estado_remoto: Optional[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Qué subir y qué borrar comparando el estado local con el publicado."""
    local = json.loads((Path(dir_mapa) / "estado.json").read_text(encoding="utf-8"))
    remoto = (estado_remoto or {}).get("archivos", {})
    subir = sorted(rel for rel, meta in local["archivos"].items()
                   if remoto.get(rel, {}).get("sha256_gz") != meta["sha256_gz"])
    borrar = sorted(rel for rel in remoto if rel not in local["archivos"])
    return {"subir": subir, "borrar": borrar}


def escribir_puntero(estado_bytes: bytes, revision: Optional[str], ruta: Optional[Path] = None) -> Dict[str, Any]:
    estado = json.loads(estado_bytes.decode("utf-8"))
    puntero = {
        "esquema": ESQUEMA,
        "repo_id": estado.get("repo", REPO_ID),
        "ruta": RUTA_HF,
        "revision_mapa": revision,
        "sha_fuente": estado.get("sha_fuente"),
        "fecha_fuente": estado.get("fecha_fuente"),
        "sha256_estado": hashlib.sha256(estado_bytes).hexdigest(),
        "constructor": estado.get("constructor"),
        "conteos": estado.get("conteos", {}),
    }
    (ruta or PUNTERO).write_bytes((json.dumps(puntero, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    return puntero


def publicar(dir_mapa: str, estado_remoto: Optional[Dict[str, Any]], parent_commit: str,
             token: Optional[str], repo_id: str = REPO_ID, dry_run: bool = False,
             forzar_versiones: bool = False, api: Any = None,
             ruta_puntero: Optional[Path] = None) -> Dict[str, Any]:
    ops = operaciones(dir_mapa, estado_remoto)
    estado_bytes = (Path(dir_mapa) / "estado.json").read_bytes()
    if not ops["subir"] and not ops["borrar"]:
        return {"publicado": False, "motivo": "sin cambios", **ops}
    if dry_run:
        return {"publicado": False, "motivo": "dry-run", **ops}
    problemas = versiones_distintas()
    if problemas and not forzar_versiones:
        raise RuntimeError("versiones distintas a las fijadas para el constructor: " + "; ".join(problemas))
    if api is None:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
    from huggingface_hub import CommitOperationAdd, CommitOperationDelete
    operaciones_hf: List[Any] = [
        CommitOperationAdd(path_in_repo=f"{RUTA_HF}/{rel}", path_or_fileobj=(Path(dir_mapa) / rel).read_bytes())
        for rel in ops["subir"]]
    if ops["borrar"]:
        existentes = {p.path for p in api.get_paths_info(repo_id, [f"{RUTA_HF}/{r}" for r in ops["borrar"]],
                                                         repo_type="dataset", revision=parent_commit)}
        operaciones_hf += [CommitOperationDelete(path_in_repo=f"{RUTA_HF}/{r}") for r in ops["borrar"]
                           if f"{RUTA_HF}/{r}" in existentes]
    operaciones_hf.append(CommitOperationAdd(path_in_repo=f"{RUTA_HF}/estado.json", path_or_fileobj=estado_bytes))
    estado = json.loads(estado_bytes)
    mensaje = (f"mapa: fuente {str(estado.get('sha_fuente'))[:8]} · {len(ops['subir'])} archivos, "
               f"{len(ops['borrar'])} bajas")
    info = api.create_commit(repo_id=repo_id, repo_type="dataset", operations=operaciones_hf,
                             commit_message=mensaje, parent_commit=parent_commit)
    revision = str(info.oid)
    refs = api.list_repo_refs(repo_id, repo_type="dataset")
    n = sum(1 for t in (refs.tags or []) if str(t.name).startswith("mapa-")) + 1
    api.create_tag(repo_id, tag=f"mapa-{n}", revision=revision, repo_type="dataset")
    puntero = escribir_puntero(estado_bytes, revision, ruta_puntero)
    return {"publicado": True, "revision_mapa": revision, "tag": f"mapa-{n}", "puntero": puntero, **ops}
