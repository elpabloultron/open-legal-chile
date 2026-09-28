"""Índice FTS5 (trigram) de archivos de texto del corpus: substring real, con o sin acentos.

Los índices viven fuera del corpus (~/.openlegal/indices), se identifican por la ruta resuelta
del archivo fuente y se reconstruyen cuando cambia su (tamaño, mtime). Si el SQLite no soporta
el tokenizador 'trigram' —o falla la construcción— se levanta la excepción: quien llama decide
el *fallback* (el escaneo clásico nunca se rompe).

Contrato de las agujas: llegan YA normalizadas por el llamador (el escaneo clásico hace lo
mismo: `a in _normalizar_para_buscar(linea).lower()`). El índice guarda el texto legible
(para devolverlo) y su versión normalizada (para calzar).
"""

import hashlib
import pathlib
import re
import sqlite3
import unicodedata
from typing import Callable, List, Optional

DIR_INDICES = pathlib.Path.home() / ".openlegal" / "indices"


def _normalizar(texto: str) -> str:
    """Minúsculas y sin acentos (NFKD + se quitan las marcas combinantes)."""
    nfkd = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _ruta_indice(ruta: pathlib.Path) -> pathlib.Path:
    DIR_INDICES.mkdir(parents=True, exist_ok=True)
    clave = hashlib.sha1(str(ruta.resolve()).encode("utf-8")).hexdigest()[:16]
    return DIR_INDICES / f"{clave}.f5.db"


def _conectar(ruta_indice: pathlib.Path) -> sqlite3.Connection:
    con = sqlite3.connect(ruta_indice)
    con.execute("PRAGMA journal_mode=WAL;")
    try:
        con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS lineas "
                    "USING fts5(bajo, original UNINDEXED, tokenize='trigram')")
        con.execute("CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)")
    except sqlite3.OperationalError as error:   # p. ej. SQLite sin trigram
        con.close()
        raise RuntimeError(f"FTS5 trigram no disponible: {error}") from error
    return con


def _huella(ruta: pathlib.Path) -> str:
    st = ruta.stat()
    return f"{st.st_size}:{st.st_mtime_ns}"


def _indice_al_dia(con: sqlite3.Connection, ruta: pathlib.Path) -> bool:
    fila = con.execute("SELECT v FROM meta WHERE k='huella'").fetchone()
    return bool(fila) and fila[0] == _huella(ruta)


def indexar(ruta: pathlib.Path, transformar: Optional[Callable[[str], str]] = None,
            normalizar: Optional[Callable[[str], str]] = None,
            max_lineas: int = 200_000, forzar: bool = False) -> int:
    """Construye o refresca el índice del archivo. Devuelve el número de líneas indexadas."""
    ruta = pathlib.Path(ruta)
    ruta_indice = _ruta_indice(ruta)
    con = _conectar(ruta_indice)
    try:
        if not forzar and _indice_al_dia(con, ruta):
            return int(con.execute("SELECT COUNT(*) FROM lineas").fetchone()[0])
        con.execute("DELETE FROM lineas")
        con.execute("DELETE FROM meta")
        normalizar = normalizar or _normalizar
        filas = []
        with open(ruta, encoding="utf-8", errors="ignore") as f:
            for i, linea in enumerate(f):
                if i >= max_lineas:
                    break
                original = transformar(linea.rstrip("\n")) if transformar else linea.rstrip("\n")
                if original.strip():
                    filas.append((normalizar(original), original))
        con.executemany("INSERT INTO lineas(bajo, original) VALUES (?, ?)", filas)
        con.execute("INSERT INTO meta(k, v) VALUES ('huella', ?)", (_huella(ruta),))
        con.commit()
        return len(filas)
    finally:
        con.close()


def buscar(ruta: pathlib.Path, agujas: List[str], maximo: int = 20,
           transformar: Optional[Callable[[str], str]] = None,
           normalizar: Optional[Callable[[str], str]] = None) -> List[str]:
    """Líneas que contienen alguna aguja (substring, sin acentos). Indexa si hace falta."""
    ruta = pathlib.Path(ruta)
    con = _conectar(_ruta_indice(ruta))
    try:
        if not _indice_al_dia(con, ruta):
            con.close()
            indexar(ruta, transformar=transformar, normalizar=normalizar)
            con = _conectar(_ruta_indice(ruta))
        # El trigram calza substrings de 3+ caracteres; los llamadores ya filtran len > 2
        # (el largo no cambia al normalizar), acá se repite el guard por si acaso.
        limpias = [_limpiar_aguja(a) for a in (agujas or [])]
        limpias = [a for a in limpias if len(a) >= 3]
        if not limpias:
            filas = con.execute("SELECT original FROM lineas LIMIT ?", (maximo,)).fetchall()
            return [f[0] for f in filas]
        consulta = " OR ".join(f'"{a}"' for a in limpias)
        filas = con.execute(
            "SELECT original FROM lineas WHERE lineas MATCH ? LIMIT ?", (consulta, maximo)).fetchall()
        return [f[0] for f in filas]
    finally:
        con.close()


def _limpiar_aguja(aguja: str) -> str:
    """Quita las comillas (romperían la sintaxis del MATCH) y el ruido de espacios."""
    return re.sub(r"\s+", " ", str(aguja).replace('"', " ").strip())
