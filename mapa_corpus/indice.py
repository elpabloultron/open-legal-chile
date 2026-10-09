"""Índice local del mapa: SQLite + FTS5 armado desde las particiones publicadas en HF.

Una base por revisión del mapa, de solo lectura una vez armada (≈ 120 MB para los 80 mil archivos):

- `entrada`: una fila por archivo del dataset (id, colección, ruta, blob, título, fecha y la fila
  JSON comprimida con zlib).
- `entrada_fts`: texto buscable (título, resumen, carátula, autores, ministros, rol, ruta…), con
  `unicode61 remove_diacritics 2` para que «indemnizacion» calce con «indemnización». Es
  *contentless*: guarda el índice invertido, no una segunda copia del texto (se une por `rowid`).
- `ref` + `cita`: cada referencia de una entrada a una entidad o a otra entrada (normas, roles,
  autores, ministros, sala, recurso, tribunal, revista), con el campo de origen como relación y su
  peso; los IDs van como enteros y la clave primaria (destino, rel, origen) es el índice.
- `entidad`: normas, autores, revistas, ministros, salas, tribunales y recursos con sus conteos.
- `alias`: los IDs equivalentes (causas acumuladas, nodos curados de LegalGraphify).
- `meta`: revisión, fuente y sha256 del `estado.json` con que se armó.

Las listas `IN` se pasan como JSON con `json_each(?)`: ningún SQL se arma concatenando texto.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
import zlib
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

from mapa_corpus import particiones

# Prefijos de los IDs que una fila puede referenciar (el resto de los textos no son citas).
PREFIJOS_REFERENCIA = ("norma:", "autor:", "ministro:", "sala:", "recurso:", "revista:", "organo:",
                       "tribunal:", "cs:", "tc:", "ta:")
# Campos de la fila que no son texto buscable (identificadores técnicos).
_NO_BUSCABLE = {"blob", "bytes", "chars", "col", "id", "documento_id", "era", "secciones", "url_oficial"}
# Cambia cuando cambia el esquema de la base: una caché armada con otro esquema se rearma.
ESQUEMA_INDICE = "2"
_ESQUEMA_SQL = """
CREATE TABLE entrada (n INTEGER PRIMARY KEY, id TEXT NOT NULL UNIQUE, col TEXT NOT NULL, ruta TEXT,
                      blob TEXT, bytes INTEGER, titulo TEXT, fecha TEXT, fila BLOB NOT NULL);
CREATE INDEX entrada_ruta ON entrada(ruta);
CREATE VIRTUAL TABLE entrada_fts USING fts5(titulo, texto, content = '',
                                            tokenize = 'unicode61 remove_diacritics 2');
CREATE TABLE ref (n INTEGER PRIMARY KEY, id TEXT NOT NULL UNIQUE);
CREATE TABLE cita (destino INTEGER NOT NULL, rel TEXT NOT NULL, origen INTEGER NOT NULL, n INTEGER NOT NULL,
                   PRIMARY KEY (destino, rel, origen)) WITHOUT ROWID;
CREATE TABLE entidad (id TEXT PRIMARY KEY, tipo TEXT NOT NULL, label TEXT, fila TEXT NOT NULL);
CREATE INDEX entidad_tipo ON entidad(tipo);
CREATE TABLE alias (alias TEXT PRIMARY KEY, id TEXT NOT NULL);
CREATE TABLE meta (clave TEXT PRIMARY KEY, valor TEXT NOT NULL);
"""


def _json(valor: Any) -> str:
    return json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _comprimir(fila: Dict[str, Any]) -> bytes:
    return zlib.compress(_json(fila).encode("utf-8"), 6)


def _fila(blob: bytes) -> Dict[str, Any]:
    datos: Dict[str, Any] = json.loads(zlib.decompress(blob).decode("utf-8"))
    return datos


def _referencias(fila: Dict[str, Any]) -> Iterator[Tuple[str, str, int]]:
    """(destino, relación, peso) de cada ID que la fila menciona fuera de su propio `id`."""
    propio = fila.get("id")
    for campo, valor in sorted(fila.items()):
        if campo == "id":
            continue
        items: Iterable[Any] = valor if isinstance(valor, list) else [valor]
        for item in items:
            destino, n = (item[0], int(item[1])) if isinstance(item, list) and len(item) == 2 else (item, 1)
            if isinstance(destino, str) and destino != propio and destino.startswith(PREFIJOS_REFERENCIA):
                yield destino, campo, n


def _texto_buscable(fila: Dict[str, Any]) -> str:
    partes: List[str] = []
    for campo, valor in sorted(fila.items()):
        if campo in _NO_BUSCABLE or campo == "titulo":
            continue
        for item in valor if isinstance(valor, list) else [valor]:
            if isinstance(item, str) and not item.startswith(PREFIJOS_REFERENCIA):
                partes.append(item)
            elif isinstance(item, dict):
                partes.extend(str(v) for v in item.values() if isinstance(v, str))
    # La ruta se busca por sus palabras («jurisprudencia_cs/2024/03/10641-2024.md»).
    if fila.get("ruta"):
        partes.append(str(fila["ruta"]).replace("/", " ").replace("_", " "))
    return "\n".join(partes)


def armar(dir_mapa: Path, destino: Path, revision: str, sha256_estado: str) -> Dict[str, int]:
    """Arma `destino` (SQLite) desde un mapa en disco. Escribe en un temporal y lo reemplaza al
    final: un proceso que muera a mitad no deja una base a medias con el nombre definitivo."""
    estado = json.loads((dir_mapa / "estado.json").read_text(encoding="utf-8"))
    tmp = destino.with_name(destino.name + ".tmp")
    if tmp.exists():
        tmp.unlink()
    conteos = {"entradas": 0, "citas": 0, "entidades": 0, "alias": 0}
    refs_n: Dict[str, int] = {}

    def _ref(id_: str) -> int:
        if id_ not in refs_n:
            refs_n[id_] = len(refs_n) + 1
        return refs_n[id_]

    con = sqlite3.connect(str(tmp))
    try:
        con.executescript("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF; PRAGMA page_size=8192;" + _ESQUEMA_SQL)
        citas: List[Tuple[int, str, int, int]] = []
        for rel in sorted(estado.get("archivos", {})):
            filas = particiones.leer((dir_mapa / rel).read_bytes())
            if rel.startswith("entradas/"):
                for f in filas:
                    cur = con.execute("INSERT OR IGNORE INTO entrada (id, col, ruta, blob, bytes, titulo, fecha, fila) "
                                      "VALUES (?,?,?,?,?,?,?,?)",
                                      (f["id"], f.get("col", ""), f.get("ruta"), f.get("blob"), f.get("bytes"),
                                       f.get("titulo"), f.get("fecha"), _comprimir(f)))
                    if not cur.rowcount:
                        continue  # ID repetido entre particiones: el mapa validado no lo tiene
                    n = int(cur.lastrowid or 0)
                    con.execute("INSERT INTO entrada_fts (rowid, titulo, texto) VALUES (?,?,?)",
                                (n, f.get("titulo") or "", _texto_buscable(f)))
                    refs = list(_referencias(f))
                    citas.extend((_ref(d), r, n, k) for d, r, k in refs)
                    for d, r, _ in refs:
                        if r == "alias":
                            con.execute("INSERT OR IGNORE INTO alias VALUES (?,?)", (d, f["id"]))
                    conteos["entradas"] += 1
                    conteos["citas"] += len(refs)
            elif rel.startswith("entidades/"):
                con.executemany("INSERT OR REPLACE INTO entidad VALUES (?,?,?,?)",
                                [(f["id"], f.get("tipo", ""), f.get("label"), _json(f)) for f in filas])
                conteos["entidades"] += len(filas)
            elif rel.startswith("grafo/alias"):
                con.executemany("INSERT OR REPLACE INTO alias VALUES (?,?)", [(f["id"], f["a"]) for f in filas])
                conteos["alias"] += len(filas)
        con.executemany("INSERT INTO ref VALUES (?,?)", sorted((n, i) for i, n in refs_n.items()))
        con.executemany("INSERT OR IGNORE INTO cita VALUES (?,?,?,?)", sorted(citas))
        meta = {"revision": revision, "sha256_estado": sha256_estado, "sha_fuente": estado.get("sha_fuente") or "",
                "fecha_fuente": estado.get("fecha_fuente") or "", "esquema": str(estado.get("esquema", "")),
                "esquema_indice": ESQUEMA_INDICE, "conteos": _json(estado.get("conteos", {}))}
        con.executemany("INSERT INTO meta VALUES (?,?)", sorted(meta.items()))
        con.execute("INSERT INTO entrada_fts (entrada_fts) VALUES ('optimize')")
        con.commit()
        con.execute("PRAGMA optimize")
    finally:
        con.close()
    reemplazar(tmp, destino)
    return conteos


def reemplazar(origen: Path, destino: Path, intentos: int = 10) -> None:
    """`os.replace` con reintentos: en Windows falla si otro proceso tiene el archivo abierto."""
    for i in range(intentos):
        try:
            os.replace(origen, destino)
            return
        except PermissionError:
            if i == intentos - 1:
                raise
            time.sleep(0.2 * (i + 1))


class Indice:
    """Consultas de solo lectura sobre un índice armado. Abre una conexión por consulta
    (`mode=ro&immutable=1`): sin bloqueos entre hilos y sin escribir nunca la base."""

    def __init__(self, ruta: Path) -> None:
        self.ruta = ruta
        self._uri = ruta.resolve().as_uri() + "?mode=ro&immutable=1"

    def _con(self) -> sqlite3.Connection:
        con = sqlite3.connect(self._uri, uri=True, check_same_thread=False)
        con.row_factory = sqlite3.Row
        return con

    def _filas(self, sql: str, parametros: Tuple[Any, ...] = ()) -> List[sqlite3.Row]:
        con = self._con()
        try:
            return list(con.execute(sql, parametros))
        finally:
            con.close()

    def meta(self) -> Dict[str, str]:
        return {r["clave"]: r["valor"] for r in self._filas("SELECT clave, valor FROM meta")}

    def canonico(self, id_: str) -> str:
        r = self._filas("SELECT id FROM alias WHERE alias = ?", (id_,))
        return str(r[0]["id"]) if r else id_

    def entradas(self, ids: List[str]) -> List[Dict[str, Any]]:
        if not ids:
            return []
        filas = self._filas("SELECT e.fila FROM json_each(?) AS j JOIN entrada AS e ON e.id = j.value "
                            "ORDER BY j.key", (_json(ids),))
        return [_fila(r["fila"]) for r in filas]

    def entrada(self, id_: str) -> Optional[Dict[str, Any]]:
        r = self.entradas([self.canonico(id_)])
        return r[0] if r else None

    def por_ruta(self, ruta: str) -> Optional[Dict[str, Any]]:
        r = self._filas("SELECT fila FROM entrada WHERE ruta = ?", (ruta,))
        return _fila(r[0]["fila"]) if r else None

    def rutas(self) -> Dict[str, str]:
        """{ruta: blob} de todo el dataset inventariado (reemplaza el listado del hub)."""
        return {r["ruta"]: r["blob"] or "" for r in self._filas("SELECT ruta, blob FROM entrada WHERE ruta IS NOT NULL")}

    def entidad(self, id_: str) -> Optional[Dict[str, Any]]:
        r = self._filas("SELECT fila FROM entidad WHERE id = ?", (self.canonico(id_),))
        return json.loads(r[0]["fila"]) if r else None

    def citantes(self, destinos: List[str], colecciones: Optional[List[str]] = None,
                 limite: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """Entradas que citan alguno de `destinos` (más citas primero, luego más recientes) y el total."""
        if not destinos:
            return [], 0
        cols = _json(colecciones or [])
        base = ("FROM ref AS r JOIN cita AS c ON c.destino = r.n JOIN entrada AS e ON e.n = c.origen "
                "WHERE r.id IN (SELECT value FROM json_each(?)) "
                "AND (json_array_length(?) = 0 OR e.col IN (SELECT value FROM json_each(?)))")
        total = self._filas("SELECT COUNT(DISTINCT c.origen) AS n " + base, (_json(destinos), cols, cols))[0]["n"]
        filas = self._filas("SELECT e.fila, SUM(c.n) AS peso " + base +
                            " GROUP BY e.n ORDER BY peso DESC, e.fecha DESC, e.id LIMIT ?",
                            (_json(destinos), cols, cols, int(limite)))
        return [_fila(r["fila"]) for r in filas], int(total)

    def buscar(self, consulta: str, colecciones: Optional[List[str]] = None, limite: int = 10) -> List[Dict[str, Any]]:
        """Búsqueda de texto (BM25, el título pesa el triple). La consulta se pasa como frase de
        términos entre comillas: ninguna sintaxis FTS5 del usuario llega al motor."""
        terminos = [t for t in "".join(ch if ch.isalnum() else " " for ch in consulta).split() if len(t) > 1]
        if not terminos:
            return []
        cols = _json(colecciones or [])
        filas: List[sqlite3.Row] = []
        # Primero todos los términos; si nada calza, cualquiera de ellos.
        for union in (" ", " OR "):
            expresion = union.join(f'"{t}"' for t in terminos[:12])
            filas = self._filas(
                "SELECT e.fila FROM entrada_fts AS f JOIN entrada AS e ON e.n = f.rowid "
                "WHERE entrada_fts MATCH ? AND (json_array_length(?) = 0 OR e.col IN (SELECT value FROM json_each(?))) "
                "ORDER BY bm25(entrada_fts, 3.0, 1.0), e.id LIMIT ?", (expresion, cols, cols, int(limite)))
            if filas or len(terminos) == 1:
                break
        return [_fila(r["fila"]) for r in filas]
