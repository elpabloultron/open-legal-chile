"""Serialización determinista de las particiones del mapa (JSONL comprimido).

Misma entrada ⇒ mismos bytes: filas ordenadas por `id`, claves ordenadas, cadenas en NFC, sin
floats, `\\n` como fin de línea (se escribe en bytes: Windows no mete `\\r\\n`) y gzip con
`mtime=0`. Las decisiones de «cambió / no cambió» se toman sobre el contenido descomprimido
(`sha256_contenido`), que no depende de la versión de zlib.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import unicodedata
from typing import Any, Dict, Iterable, List

EXTENSION = ".jsonl.gz"


def nfc(valor: Any) -> Any:
    """La fila tal como queda escrita: textos en NFC (el mismo nombre con tildes compuestas o
    descompuestas es UN nombre), sin floats."""
    if isinstance(valor, str):
        return unicodedata.normalize("NFC", valor)
    if isinstance(valor, dict):
        return {nfc(k): nfc(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [nfc(v) for v in valor]
    if isinstance(valor, float):
        raise TypeError("el mapa no admite floats (rompen el determinismo): usa enteros")
    return valor


def linea(fila: Dict[str, Any]) -> str:
    return json.dumps(nfc(fila), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def serializar(filas: Iterable[Dict[str, Any]]) -> bytes:
    """Filas → bytes JSONL (sin comprimir), ordenadas por `id` y luego por la línea completa."""
    lineas = sorted((str(f.get("id", "")), linea(f)) for f in filas)
    return "".join(texto + "\n" for _, texto in lineas).encode("utf-8")


def comprimir(datos: bytes) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=9, mtime=0, filename="") as gz:
        gz.write(datos)
    return buf.getvalue()


def descomprimir(datos_gz: bytes) -> bytes:
    return gzip.decompress(datos_gz)


def leer(datos: bytes) -> List[Dict[str, Any]]:
    """Bytes (comprimidos o no) → filas."""
    if datos[:2] == b"\x1f\x8b":
        datos = descomprimir(datos)
    return [json.loads(x) for x in datos.decode("utf-8").splitlines() if x.strip()]


def sha256(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def particion_de(ruta: str) -> str:
    """Partición (sin extensión) en la que vive la entrada de un archivo del dataset."""
    partes = ruta.split("/")
    raiz = partes[0]
    if raiz == "jurisprudencia_cs":
        if len(partes) >= 4 and partes[1].isdigit():
            return f"entradas/cs-{partes[1]}"
        return "entradas/cs-indices"
    if raiz == "jurisprudencia_tc":
        return "entradas/tc"
    if raiz == "jurisprudencia_ambiental":
        if len(partes) >= 3 and partes[1].upper() in ("1TA", "2TA", "3TA"):
            return f"entradas/ta-{partes[1].lower()}"
        return "entradas/ta-otros"
    if raiz == "doctrina":
        if len(partes) >= 4 and partes[1] == "revistas":
            return f"entradas/doc-rev-{partes[2].lower()}"
        if len(partes) >= 3:
            return f"entradas/doc-{partes[1].lower()}"
        return "entradas/doc-otros"
    if raiz == "guias_academia_judicial":
        return "entradas/guias"
    if raiz == "biblioteca_ambiental":
        return "entradas/amb-biblioteca"
    if raiz == "publicaciones_ambientales":
        return "entradas/amb-publicaciones"
    if raiz == "data":
        return "entradas/datos"
    if raiz == "graphify":
        return "entradas/graphify"
    return "entradas/raiz"
