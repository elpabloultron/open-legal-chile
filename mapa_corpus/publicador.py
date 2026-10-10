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
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from mapa_corpus import ESQUEMA, REPO_ID, RUTA_HF, particiones

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
    local = particiones.archivos_de(json.loads((Path(dir_mapa) / "estado.json").read_text(encoding="utf-8")))
    remoto = particiones.archivos_de(estado_remoto or {})
    subir = sorted(rel for rel, meta in local.items()
                   if remoto.get(rel, {}).get("sha256_gz") != meta["sha256_gz"])
    borrar = sorted(rel for rel in remoto if rel not in local)
    return {"subir": subir, "borrar": borrar}


def siguiente_tag(nombres: List[str]) -> str:
    """`mapa-<n>` con n = el mayor publicado + 1 (contar los tags chocaría si alguno se borró)."""
    numeros = [int(m.group(1)) for m in map(re.compile(r"mapa-(\d+)").fullmatch, nombres) if m]
    return f"mapa-{max(numeros, default=0) + 1}"


def revision_publicada(estado_bytes: bytes, bajar_estado: Callable[[str], Optional[bytes]],
                       token: Optional[str] = None, repo_id: str = REPO_ID, api: Any = None,
                       maximo: int = 5) -> Optional[str]:
    """El commit del tag `mapa-<n>` más reciente (entre los `maximo` últimos) cuyo estado.json es
    `estado_bytes`, o None si ninguno calza."""
    if api is None:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
    tags = []
    for t in api.list_repo_refs(repo_id, repo_type="dataset").tags or []:
        m = re.fullmatch(r"mapa-(\d+)", str(t.name))
        if m:
            tags.append((int(m.group(1)), str(t.target_commit)))
    objetivo = hashlib.sha256(estado_bytes).hexdigest()
    for _, commit in sorted(tags, reverse=True)[:maximo]:
        datos = bajar_estado(commit)
        if datos is not None and hashlib.sha256(datos).hexdigest() == objetivo:
            return commit
    return None


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
    # Sin particiones distintas el estado igual puede haber cambiado (otras reglas o fuente con el
    # mismo resultado): se publica solo el estado, o la próxima corrida reconstruiría otra vez.
    if not ops["subir"] and not ops["borrar"] and json.loads(estado_bytes) == estado_remoto:
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
    # El puntero primero: el commit ya está en HF y es lo que importa; un tag que falle no lo pierde.
    puntero = escribir_puntero(estado_bytes, revision, ruta_puntero)
    refs = api.list_repo_refs(repo_id, repo_type="dataset")
    tag = siguiente_tag([str(t.name) for t in (refs.tags or [])])
    try:
        api.create_tag(repo_id, tag=tag, revision=revision, repo_type="dataset")
    except Exception as exc:  # noqa: BLE001 — sin tag la revisión igual queda fijada por el puntero
        log.warning("no se pudo crear el tag %s: %s", tag, exc)
        tag = ""
    return {"publicado": True, "revision_mapa": revision, "tag": tag, "puntero": puntero, **ops}
