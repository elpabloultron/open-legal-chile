"""Ubica los recursos del producto que no son código: skills, agentes, protocolo y guías.

En el repositorio viven en la raíz (`.agents/skills/`, `agents/`, `AGENTS.md`, `docs/`). El wheel
no puede llevarlos como paquetes —`.agents` no es un nombre importable y `agents` chocaría con el
paquete del mismo nombre de otros SDK—, así que viajan como data-files en
`<prefijo>/share/openlegal-chile/`. Hasta 1.13.0 no viajaban: instalado con pip o uvx,
`skills_listar` y `agent_list` quedaban vacíos y el recurso del protocolo de citación decía
«Protocolo no disponible».
"""

from __future__ import annotations

import os
import pathlib
import sys
import sysconfig
from typing import Iterator

RAIZ = pathlib.Path(__file__).resolve().parent
_SUBCARPETA = pathlib.Path("share") / "openlegal-chile"


def _bases() -> Iterator[pathlib.Path]:
    """Lugares donde puede estar un recurso, del más cercano al más lejano."""
    yield RAIZ
    prefijos = [sys.prefix, sys.base_prefix, sysconfig.get_path("data")]
    try:  # pip install --user
        prefijos.append(sysconfig.get_path("data", f"{os.name}_user"))
    except KeyError:
        pass
    for prefijo in dict.fromkeys(p for p in prefijos if p):
        yield pathlib.Path(prefijo) / _SUBCARPETA


def ruta_recurso(relativa: str) -> pathlib.Path:
    """Ruta del recurso (archivo o carpeta) relativo a la raíz del proyecto.

    Si no está en ningún lado devuelve la ruta en la raíz del código, para que el llamador
    informe el faltante con una ruta reconocible.
    """
    for base in _bases():
        candidata = base / relativa
        if candidata.exists():
            return candidata
    return RAIZ / relativa
