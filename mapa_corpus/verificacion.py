"""Verificación de un puntero publicado (la usa el job `mapa-puntero` de la CI)."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from mapa_corpus import RUTA_HF, constructor, inventario, particiones


def verificar_puntero(puntero: Dict[str, Any]) -> List[str]:
    import requests
    problemas: List[str] = []
    repo, rev = puntero["repo_id"], puntero["revision_mapa"]
    base = f"{inventario.ENDPOINT}/datasets/{repo}/resolve/{rev}/{RUTA_HF}"
    r = requests.get(f"{base}/estado.json", timeout=60)
    if r.status_code != 200:
        return [f"no se pudo leer estado.json@{rev}: HTTP {r.status_code}"]
    if hashlib.sha256(r.content).hexdigest() != puntero.get("sha256_estado"):
        problemas.append("sha256 de estado.json no calza con el puntero")
    estado = json.loads(r.content)
    if estado.get("sha_fuente") != puntero.get("sha_fuente"):
        problemas.append("sha_fuente del estado no calza con el puntero")
    existe = requests.get(f"{inventario.ENDPOINT}/api/datasets/{repo}/revision/{puntero.get('sha_fuente')}",
                          params={"expand[]": "sha"}, timeout=60)
    if existe.status_code != 200:
        problemas.append(f"sha_fuente {puntero.get('sha_fuente')} no existe en el dataset")
    with tempfile.TemporaryDirectory() as tmp:
        destino = Path(tmp)
        (destino / "estado.json").write_bytes(r.content)
        for rel, meta in estado.get("archivos", {}).items():
            d = requests.get(f"{base}/{rel}", timeout=120)
            if d.status_code != 200 or particiones.sha256(d.content) != meta["sha256_gz"]:
                problemas.append(f"archivo publicado distinto o ausente: {rel}")
                continue
            (destino / rel).parent.mkdir(parents=True, exist_ok=True)
            (destino / rel).write_bytes(d.content)
        if not problemas:
            problemas += constructor.validar(str(destino))
    return problemas
