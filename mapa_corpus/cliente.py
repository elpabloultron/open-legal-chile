"""Cliente del mapa del corpus: descarga verificada, índice local y consultas sin red.

Open Legal Chile consulta el mapa SIEMPRE que exista, pero una consulta nunca descarga: solo
`asegurar()` usa la red, y corre en un hilo de fondo. Mientras el mapa no esté listo, las
consultas responden vacío con un aviso, y las herramientas siguen con sus fuentes de siempre.

Qué revisión se usa (en orden):

1. `OPENLEGAL_MAPA=off` → ninguna (la suite de pruebas lo fija en `tests/conftest.py`).
2. `OPENLEGAL_MAPA_LOCAL=<dir>` → un mapa construido en disco (`python -m mapa_corpus construir`).
3. `OPENLEGAL_MAPA=main` → el último mapa publicado en `main` de HF, fijado a su sha al descargarlo.
4. Por defecto, la revisión del puntero del paquete (`mapa_corpus/puntero.json`), verificada contra
   su `sha256_estado`. El puntero es un piso: es lo que se probó junto con esta versión del código.

Si esa revisión no está lista se usa la última caché lista (con aviso de qué fuente y de qué
fecha es); si no hay ninguna, el producto sigue sin mapa, con aviso para la herramienta.

La caché vive en `~/.openlegal/mapa/<revisión>/` (o `OPENLEGAL_MAPA_DIR`): las particiones
descargadas, `mapa.sqlite` y la marca `LISTO` con el sha256 del `estado.json`. Se conservan dos
revisiones. Un `filelock` entre procesos evita que dos servidores MCP descarguen a la vez.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

from mapa_corpus import REPO_ID, RUTA_HF, indice, particiones

log = logging.getLogger("mapa_corpus")

PUNTERO = Path(__file__).resolve().parent / "puntero.json"
ENDPOINT = os.environ.get("HF_ENDPOINT", "https://huggingface.co").rstrip("/")
REVISIONES_CONSERVADAS = 2
_RE_SHA = re.compile(r"^[0-9a-f]{40}$")


def _raiz() -> Path:
    return Path(os.environ.get("OPENLEGAL_MAPA_DIR") or Path.home() / ".openlegal" / "mapa")


def _sha256(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def leer_puntero(ruta: Path = PUNTERO) -> Dict[str, Any]:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


class MapaCliente:
    def __init__(self, puntero: Optional[Dict[str, Any]] = None, raiz: Optional[Path] = None,
                 sesion: Any = None) -> None:
        self.puntero = puntero if puntero is not None else leer_puntero()
        self.raiz = Path(raiz) if raiz else _raiz()
        self.modo = (os.environ.get("OPENLEGAL_MAPA") or "").strip().lower()
        self.local = os.environ.get("OPENLEGAL_MAPA_LOCAL") or ""
        self.repo_id = str(self.puntero.get("repo_id") or REPO_ID)
        self._sesion = sesion
        self._hilo: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._indice: Optional[indice.Indice] = None
        self._indice_dir: Optional[Path] = None
        self._aviso = ""
        self.error = ""

    # ── Estado ──────────────────────────────────────────────────────────────────────────────
    @property
    def habilitado(self) -> bool:
        return self.modo not in ("off", "0", "no", "false")

    def _objetivo(self) -> Tuple[Optional[str], Optional[str]]:
        """(revisión, sha256 esperado del estado) que corresponde usar, sin tocar la red."""
        if self.local:
            return "local", None
        if self.modo == "main":
            actual = self._leer_json(self.raiz / "main.json")
            return (actual.get("revision"), None) if actual else (None, None)
        rev = self.puntero.get("revision_mapa")
        return (str(rev), self.puntero.get("sha256_estado")) if rev else (None, None)

    @staticmethod
    def _leer_json(ruta: Path) -> Dict[str, Any]:
        try:
            return json.loads(ruta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _listo(self, rev: str, sha_estado: Optional[str] = None) -> bool:
        marca = self._leer_json(self.raiz / rev / "LISTO")
        if not self._compatible(marca) or not (self.raiz / rev / "mapa.sqlite").exists():
            return False
        return sha_estado is None or marca.get("sha256_estado") == sha_estado

    @staticmethod
    def _compatible(marca: Dict[str, Any]) -> bool:
        """Una base armada por otra versión del índice no se consulta: se rearma."""
        return bool(marca) and marca.get("indice") == indice.ESQUEMA_INDICE

    def _listas(self) -> List[Path]:
        """Revisiones listas en caché, la más reciente primero."""
        if not self.raiz.exists():
            return []
        listas = [d for d in self.raiz.iterdir() if d.is_dir() and (d / "mapa.sqlite").exists()
                  and self._compatible(self._leer_json(d / "LISTO"))]
        return sorted(listas, key=lambda d: (d / "LISTO").stat().st_mtime, reverse=True)

    def indice(self) -> Optional[indice.Indice]:
        """El índice que hay que consultar ahora, o None. Nunca usa la red."""
        if not self.habilitado:
            return None
        with self._lock:
            rev, sha_estado = self._objetivo()
            if rev and self._listo(rev, sha_estado):
                elegido, self._aviso = self.raiz / rev, ""
            else:
                otras = self._listas()
                if not otras:
                    self._indice, self._indice_dir = None, None
                    # Sin nada publicado no hay qué descargar ni qué forzar: sin aviso.
                    self._aviso = ("El mapa del corpus de Hugging Face aún no está descargado: la consulta usó "
                                   "las fuentes de siempre. Se descarga en segundo plano; para forzarlo, usa la "
                                   "herramienta suite_instalar.") if self.publicado else ""
                    return None
                elegido = otras[0]
                meta = self._leer_json(elegido / "LISTO")
                self._aviso = (f"Mapa del corpus de la fuente {str(meta.get('sha_fuente', ''))[:8]} del "
                               f"{str(meta.get('fecha_fuente', ''))[:10] or 's/f'}: la revisión vigente aún no se "
                               "descarga.")
            if self._indice_dir != elegido:
                self._indice, self._indice_dir = indice.Indice(elegido / "mapa.sqlite"), elegido
            return self._indice

    def directorio(self) -> Optional[Path]:
        """Carpeta del mapa en uso (particiones del grafo incluidas), para LegalGraphify."""
        return (self._indice_dir / "descarga") if self.indice() is not None and self._indice_dir else None

    def estado_breve(self) -> Dict[str, Any]:
        """Lo que una herramienta informa sobre el mapa: si está activo, qué fuente y qué avisos."""
        if not self.habilitado:
            return {"activo": False, "motivo": "desactivado (OPENLEGAL_MAPA=off)"}
        ind = self.indice()
        if ind is None and not self.publicado:
            return {"activo": False, "publicado": False,
                    "motivo": "aún no publicado para esta versión: se usan las fuentes de siempre"}
        if ind is None:
            return {"activo": False, "aviso": self._aviso, "descargando": self.descargando, "error": self.error or None}
        meta = ind.meta()
        salida: Dict[str, Any] = {"activo": True, "revision": meta.get("revision"), "sha_fuente": meta.get("sha_fuente"),
                                  "fecha_fuente": meta.get("fecha_fuente"),
                                  "conteos": json.loads(meta.get("conteos") or "{}")}
        if self._aviso:
            salida["aviso"] = self._aviso
        return salida

    @property
    def publicado(self) -> bool:
        """Hay algo que descargar: una revisión en el puntero, el modo `main` o un mapa local."""
        return bool(self.local or self.modo == "main" or self.puntero.get("revision_mapa"))

    @property
    def descargando(self) -> bool:
        return bool(self._hilo and self._hilo.is_alive())

    # ── Consultas (sin red) ─────────────────────────────────────────────────────────────────
    def entrada(self, id_: str) -> Optional[Dict[str, Any]]:
        ind = self.indice()
        return ind.entrada(id_) if ind else None

    def por_ruta(self, ruta: str) -> Optional[Dict[str, Any]]:
        ind = self.indice()
        return ind.por_ruta(ruta) if ind else None

    def rutas(self) -> Dict[str, str]:
        ind = self.indice()
        return ind.rutas() if ind else {}

    def buscar(self, consulta: str, colecciones: Optional[List[str]] = None, limite: int = 10) -> List[Dict[str, Any]]:
        ind = self.indice()
        return ind.buscar(consulta, colecciones, limite) if ind else []

    def citantes(self, ids: List[str], colecciones: Optional[List[str]] = None,
                 limite: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        ind = self.indice()
        return ind.citantes([ind.canonico(i) for i in ids], colecciones, limite) if ind else ([], 0)

    def entidad(self, id_: str) -> Optional[Dict[str, Any]]:
        ind = self.indice()
        return ind.entidad(id_) if ind else None

    def url(self, ruta: str, fijada: bool = True) -> str:
        """URL de un archivo del dataset: fijada a la revisión de la fuente del mapa, o la vigente."""
        ind = self.indice()
        sha = (ind.meta().get("sha_fuente") if ind else "") or "main"
        return f"{ENDPOINT}/datasets/{self.repo_id}/blob/{sha if fijada else 'main'}/{quote(ruta)}"

    # ── Descarga (única parte con red) ──────────────────────────────────────────────────────
    def asegurar(self, bloquear: bool = False, timeout: Optional[float] = None) -> bool:
        """Deja lista la revisión que corresponde (descarga verificada + índice). Con `bloquear`
        espera a que termine; si no, corre en un hilo de fondo. True si quedó un mapa usable."""
        if not self.habilitado:
            return False
        with self._lock:
            if not self.descargando:
                self.error = ""
                self._hilo = threading.Thread(target=self._asegurar_seguro, name="openlegal-mapa", daemon=True)
                self._hilo.start()
            hilo = self._hilo
        if bloquear and hilo:
            hilo.join(timeout)
        return self.indice() is not None

    def _asegurar_seguro(self) -> None:
        try:
            self._asegurar()
        except Exception as exc:  # noqa: BLE001 — sin mapa el producto sigue: el error queda informado
            self.error = f"{type(exc).__name__}: {exc}"
            log.warning("mapa del corpus: %s", self.error)

    def _cerrojo(self) -> Any:
        self.raiz.mkdir(parents=True, exist_ok=True)
        try:
            from filelock import FileLock
        except ImportError:  # pragma: no cover — filelock viene con huggingface_hub
            return threading.Lock()
        return FileLock(str(self.raiz / "mapa.lock"), timeout=1800)

    def _asegurar(self) -> None:
        with self._cerrojo():
            if self.local:
                self._armar_local(Path(self.local))
                return
            rev, sha_estado = self._objetivo()
            if self.modo == "main":
                rev, sha_estado = self._revision_main(), None
            if not rev:
                return
            if not self._listo(rev, sha_estado):
                self._descargar(rev, sha_estado)
            if self.modo == "main":
                (self.raiz / "main.json").write_text(json.dumps({"revision": rev}), encoding="utf-8")
            self._podar(rev)

    def _armar_local(self, origen: Path) -> None:
        estado_bytes = (origen / "estado.json").read_bytes()
        sha = _sha256(estado_bytes)
        if self._listo("local", sha) and self._leer_json(self.raiz / "local" / "LISTO").get("origen") == str(origen):
            return
        destino = self.raiz / "local"
        if (destino / "descarga").exists():
            shutil.rmtree(destino / "descarga")
        shutil.copytree(origen, destino / "descarga")
        self._armar(destino, "local", estado_bytes, origen=str(origen))

    def _s(self) -> Any:
        if self._sesion is None:
            import requests
            self._sesion = requests.Session()
            self._sesion.headers["User-Agent"] = "open-legal-chile-mapa"
        return self._sesion

    def _get(self, url: str, intentos: int = 4) -> bytes:
        for i in range(intentos):
            try:
                r = self._s().get(url, timeout=120)
                if r.status_code == 200:
                    return bytes(r.content)
                if r.status_code == 429 or r.status_code >= 500:
                    espera = float(r.headers.get("Retry-After") or 2 ** i)
                    time.sleep(min(espera, 60.0))
                    continue
                raise RuntimeError(f"HTTP {r.status_code} en {url}")
            except (OSError, ValueError) as exc:  # red caída o cortada: se reintenta
                if i == intentos - 1:
                    raise RuntimeError(f"no se pudo descargar {url}: {exc}") from exc
                time.sleep(2 ** i)
        raise RuntimeError(f"no se pudo descargar {url} tras {intentos} intentos")

    def _revision_main(self) -> str:
        url = f"{ENDPOINT}/api/datasets/{self.repo_id}/revision/main?expand[]=sha"
        sha = str(json.loads(self._get(url)).get("sha", ""))
        if not _RE_SHA.match(sha):
            raise RuntimeError(f"sha de main inválido: {sha!r}")
        return sha

    def _descargar(self, rev: str, sha_estado: Optional[str]) -> None:
        if not _RE_SHA.match(rev):
            raise RuntimeError(f"revisión del mapa inválida: {rev!r}")
        destino = self.raiz / rev
        descarga = destino / "descarga"
        descarga.mkdir(parents=True, exist_ok=True)
        base = f"{ENDPOINT}/datasets/{self.repo_id}/resolve/{rev}/{RUTA_HF}"
        estado_bytes = self._get(f"{base}/estado.json")
        if sha_estado and _sha256(estado_bytes) != sha_estado:
            raise RuntimeError("estado.json del mapa no coincide con el sha256 del puntero")
        estado = json.loads(estado_bytes.decode("utf-8"))
        for rel, meta in sorted(particiones.archivos_de(estado).items()):
            ruta = descarga / rel
            if ruta.exists() and _sha256(ruta.read_bytes()) == meta.get("sha256_gz"):
                continue
            datos = self._get(f"{base}/{quote(rel)}")
            if _sha256(datos) != meta.get("sha256_gz"):
                raise RuntimeError(f"{rel}: sha256 distinto al de estado.json (descarga corrupta)")
            ruta.parent.mkdir(parents=True, exist_ok=True)
            tmp = ruta.with_name(ruta.name + ".tmp")
            tmp.write_bytes(datos)
            indice.reemplazar(tmp, ruta)
        (descarga / "estado.json").write_bytes(estado_bytes)
        self._armar(destino, rev, estado_bytes)

    def _armar(self, destino: Path, rev: str, estado_bytes: bytes, origen: str = "") -> None:
        estado = json.loads(estado_bytes.decode("utf-8"))
        sha = _sha256(estado_bytes)
        marca = destino / "LISTO"
        if marca.exists():
            marca.unlink()
        indice.armar(destino / "descarga", destino / "mapa.sqlite", rev, sha)
        datos = {"revision": rev, "sha256_estado": sha, "sha_fuente": estado.get("sha_fuente"),
                 "fecha_fuente": estado.get("fecha_fuente"), "origen": origen, "indice": indice.ESQUEMA_INDICE}
        marca.write_text(json.dumps(datos, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    def _podar(self, vigente: str) -> None:
        """Conserva la revisión vigente y la anterior lista; borra el resto."""
        conservar = {vigente, "local"}
        for d in self._listas():
            if len(conservar) >= REVISIONES_CONSERVADAS + 1:
                break
            conservar.add(d.name)
        for d in self.raiz.iterdir():
            if d.is_dir() and d.name not in conservar and _RE_SHA.match(d.name):
                shutil.rmtree(d, ignore_errors=True)


_CLIENTE: Optional[MapaCliente] = None
_CLIENTE_LOCK = threading.Lock()


def obtener_cliente() -> MapaCliente:
    """Cliente compartido por el proceso (el servidor MCP y sus herramientas)."""
    global _CLIENTE
    with _CLIENTE_LOCK:
        if _CLIENTE is None:
            _CLIENTE = MapaCliente()
        return _CLIENTE


def reiniciar_cliente() -> None:
    """Para las pruebas: el próximo `obtener_cliente()` relee el entorno y el puntero."""
    global _CLIENTE
    with _CLIENTE_LOCK:
        _CLIENTE = None
