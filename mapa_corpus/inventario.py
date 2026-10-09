"""Inventario del dataset en HF, delta por blob y descarga con cupos.

- `sha_main`: una llamada barata (~200 B) para saber si HF cambió.
- `inventario`: los ~80 mil archivos con su blob y tamaño en UNA llamada (`blobs=true`).
- `Descargador`: GET a `resolve/<sha>/<ruta>` fijado a una revisión, verificado contra el blob
  git (o el sha256 de LFS), con caché direccionada por contenido y un limitador que respeta el
  encabezado `ratelimit` de HF (cada archivo gasta 2 unidades de «resolvers» por la redirección).
"""

from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from mapa_corpus import REPO_ID, RUTA_HF

log = logging.getLogger("mapa_corpus")

ENDPOINT = os.environ.get("HF_ENDPOINT", "https://huggingface.co").rstrip("/")
# Lo que NO es corpus: el propio mapa (autorreferencia) y la metadata de git.
EXCLUIDOS_PREFIJO = (RUTA_HF + "/",)
EXCLUIDOS_EXACTOS = {".gitattributes"}
# Se inventaría (para que la wiki siga apareciendo en búsquedas) pero no cuenta para la huella:
# es el grafo de CÓDIGO, que se regenera aparte.
FUERA_DE_HUELLA_PREFIJO = ("graphify/",)
# Archivos de prueba publicados por error.
BASURA = ("jurisprudencia_tc/testrol",)


@dataclass(frozen=True)
class Archivo:
    ruta: str
    blob: str
    bytes: int
    lfs_sha256: Optional[str] = None


def excluido(ruta: str) -> bool:
    return ruta in EXCLUIDOS_EXACTOS or ruta.startswith(EXCLUIDOS_PREFIJO) or ruta.startswith(BASURA)


def _sesion(token: Optional[str]) -> Any:
    import requests  # dependencia directa del paquete
    s = requests.Session()
    s.headers["User-Agent"] = "open-legal-chile-mapa/1"
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    return s


def sha_main(repo_id: str = REPO_ID, token: Optional[str] = None, revision: str = "main") -> Tuple[str, str]:
    """(sha, lastModified ISO) de la revisión, con ~200 bytes de respuesta."""
    r = _sesion(token).get(f"{ENDPOINT}/api/datasets/{repo_id}/revision/{revision}",
                           params={"expand[]": ["sha", "lastModified"]}, timeout=60)
    r.raise_for_status()
    datos = r.json()
    return str(datos["sha"]), str(datos.get("lastModified") or "")


def inventario(sha: str, repo_id: str = REPO_ID, token: Optional[str] = None,
               api: Any = None) -> Dict[str, Archivo]:
    """Todos los archivos de la revisión `sha` (40 hex), sin los excluidos, en una llamada."""
    if api is None:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
    info = api.dataset_info(repo_id, revision=sha, files_metadata=True)
    salida: Dict[str, Archivo] = {}
    for s in info.siblings or []:
        if excluido(s.rfilename):
            continue
        lfs = getattr(s, "lfs", None)
        salida[s.rfilename] = Archivo(s.rfilename, str(s.blob_id), int(s.size or 0),
                                      str(lfs.sha256) if lfs is not None else None)
    return salida


def huella(archivos: Iterable[Archivo], version_reglas: str) -> str:
    """sha256 del inventario filtrado (sin graphify/) + la versión de las reglas de extracción."""
    h = hashlib.sha256()
    for a in sorted((a for a in archivos if not a.ruta.startswith(FUERA_DE_HUELLA_PREFIJO)), key=lambda a: a.ruta):
        h.update(f"{a.ruta}\t{a.blob}\n".encode("utf-8"))
    h.update(f"reglas\t{version_reglas}\n".encode("utf-8"))
    return "sha256:" + h.hexdigest()


def delta(previo: Dict[str, str], actual: Dict[str, Archivo]) -> Tuple[List[str], List[str], List[str]]:
    """(altas, modificados, bajas) comparando ruta→blob. Un renombre es baja + alta."""
    altas = sorted(r for r in actual if r not in previo)
    mods = sorted(r for r in actual if r in previo and previo[r] != actual[r].blob)
    bajas = sorted(r for r in previo if r not in actual)
    return altas, mods, bajas


def blob_git(datos: bytes) -> str:
    """El oid de git de un blob: sha1("blob <n>\\0" + datos). No es un uso criptográfico."""
    h = hashlib.sha1(usedforsecurity=False)
    h.update(b"blob %d\x00" % len(datos))
    h.update(datos)
    return h.hexdigest()


class Limitador:
    """Cupo de «resolvers» de HF (3.000 por 5 min sin token; cada archivo gasta 2 unidades).

    Lleva su propia ventana y además obedece el encabezado `ratelimit: "resolvers";r=…;t=…`: si
    quedan pocas unidades, espera `t` segundos. Ante un 429 espera lo que diga el servidor.
    """

    def __init__(self, por_ventana: int = 1400, ventana: float = 300.0,
                 dormir: Callable[[float], None] = time.sleep, reloj: Callable[[], float] = time.monotonic):
        self.por_ventana = por_ventana
        self.ventana = ventana
        self._dormir = dormir
        self._reloj = reloj
        self._lock = threading.Lock()
        self._marcas: List[float] = []
        self._esperar_hasta = 0.0

    def antes(self) -> None:
        with self._lock:
            ahora = self._reloj()
            if self._esperar_hasta > ahora:
                self._dormir(self._esperar_hasta - ahora)
                ahora = self._reloj()
            self._marcas = [m for m in self._marcas if ahora - m < self.ventana]
            if len(self._marcas) >= self.por_ventana:
                self._dormir(max(0.0, self.ventana - (ahora - self._marcas[0])) + 0.5)
                ahora = self._reloj()
                self._marcas = [m for m in self._marcas if ahora - m < self.ventana]
            self._marcas.append(ahora)

    def despues(self, encabezados: Dict[str, str], estado: int) -> None:
        espera = 0.0
        rl = encabezados.get("ratelimit") or encabezados.get("RateLimit") or ""
        partes = dict(p.split("=", 1) for p in rl.replace(" ", "").split(";")[1:] if "=" in p)
        try:
            restantes = int(partes.get("r", "999999"))
            t = float(partes.get("t", "0"))
        except ValueError:
            restantes, t = 999999, 0.0
        if estado == 429:
            espera = max(t, float(encabezados.get("Retry-After") or 0), 5.0)
        elif restantes < 20:
            espera = t + 1.0
        if espera:
            with self._lock:
                self._esperar_hasta = max(self._esperar_hasta, self._reloj() + espera)


class Descargador:
    """Baja archivos de una revisión fija, verificados, con caché por blob y 8 hilos."""

    def __init__(self, sha: str, repo_id: str = REPO_ID, token: Optional[str] = None,
                 cache_dir: Optional[str] = None, hilos: int = 8, limitador: Optional[Limitador] = None):
        self.sha = sha
        self.repo_id = repo_id
        self.hilos = hilos
        self.cache = Path(cache_dir or os.environ.get("OPENLEGAL_MAPA_FUENTES")
                          or Path.home() / ".cache" / "openlegal-mapa" / "fuente")
        self.cache.mkdir(parents=True, exist_ok=True)
        self.limitador = limitador or Limitador(por_ventana=1400 if not token else 5000)
        self._token = token
        self._local = threading.local()
        self.peticiones = 0

    def _s(self) -> Any:
        if not hasattr(self._local, "s"):
            self._local.s = _sesion(self._token)
        return self._local.s

    def _verifica(self, a: Archivo, datos: bytes) -> bool:
        if a.lfs_sha256:
            return hashlib.sha256(datos).hexdigest() == a.lfs_sha256
        return blob_git(datos) == a.blob

    def obtener(self, a: Archivo) -> bytes:
        destino = self.cache / (a.lfs_sha256 or a.blob)
        if destino.exists():
            datos = destino.read_bytes()
            if self._verifica(a, datos):
                return datos
        url = f"{ENDPOINT}/datasets/{self.repo_id}/resolve/{self.sha}/{urllib.parse.quote(a.ruta)}"
        ultimo_error: Optional[Exception] = None
        for intento in range(6):
            self.limitador.antes()
            try:
                r = self._s().get(url, timeout=120)
                self.peticiones += 1
                self.limitador.despues(dict(r.headers), r.status_code)
                if r.status_code == 429 or r.status_code >= 500:
                    raise RuntimeError(f"HTTP {r.status_code} en {a.ruta}")
                r.raise_for_status()
                datos = r.content
                if not self._verifica(a, datos):
                    raise RuntimeError(f"el contenido de {a.ruta} no calza con su blob {a.blob}")
                tmp = destino.with_suffix(".tmp")
                tmp.write_bytes(datos)
                os.replace(tmp, destino)
                return datos
            except Exception as exc:  # noqa: BLE001 — se reintenta con espera creciente
                ultimo_error = exc
                time.sleep(min(60.0, 2.0 ** intento))
        raise RuntimeError(f"no se pudo bajar {a.ruta}: {ultimo_error}")

    def obtener_varios(self, archivos: List[Archivo],
                       al_avanzar: Optional[Callable[[int, int], None]] = None) -> Dict[str, bytes]:
        salida: Dict[str, bytes] = {}
        total = len(archivos)
        with ThreadPoolExecutor(max_workers=self.hilos) as ex:
            for i, (a, datos) in enumerate(zip(archivos, ex.map(self.obtener, archivos), strict=True), 1):
                salida[a.ruta] = datos
                if al_avanzar and (i % 250 == 0 or i == total):
                    al_avanzar(i, total)
        return salida

    def podar(self, vigentes: Iterable[Archivo]) -> int:
        """Borra de la caché los blobs que ya no están en el inventario (para no crecer sin fin)."""
        conservar = {a.lfs_sha256 or a.blob for a in vigentes}
        borrados = 0
        for p in self.cache.iterdir():
            if p.is_file() and p.name not in conservar:
                p.unlink(missing_ok=True)
                borrados += 1
        return borrados
