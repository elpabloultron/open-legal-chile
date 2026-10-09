"""Cliente del mapa del corpus: índice SQLite/FTS5, descarga verificada y cadena de respaldo.

Todo corre sobre un mapa diminuto armado en `tmp_path` y una sesión HTTP falsa: ni red, ni
`~/.openlegal`, ni archivos versionados.
"""

import hashlib
import json
import sqlite3
import threading

import pytest

from mapa_corpus import cliente as mod_cliente
from mapa_corpus import indice, particiones

SHA_FUENTE = "a" * 40
REV_1 = "1" * 40
REV_2 = "2" * 40

FILAS = {
    "entradas/cs-2024": [
        {"id": "cs:10641-2024", "col": "cs", "ruta": "jurisprudencia_cs/2024/03/10641-2024.md", "blob": "b" * 40,
         "bytes": 800, "fecha": "2026-03-04", "rol": "10641-2024", "titulo": "PÉREZ CON FISCO",
         "sala": "sala:cs-3", "recurso": "recurso:proteccion", "recurso_txt": "PROTECCIÓN",
         "ministros": ["ministro:maria-gajardo-harboe"], "ministros_txt": ["MARÍA GAJARDO HARBOE"]},
    ],
    "entradas/tc": [
        {"id": "tc:2402", "col": "tc", "ruta": "jurisprudencia_tc/2402-12-INA.md", "blob": "c" * 40, "bytes": 9000,
         "fecha": "2013-05-02", "titulo": "Requerimiento de inaplicabilidad",
         "resumen": "La indemnización de perjuicios y la responsabilidad del Estado.",
         "normas": [["norma:cc:2314", 3], ["norma:cpr:19:n3", 1]], "cita_cs": ["cs:10641-2024"]},
    ],
    "entradas/doc-rev-rchd": [
        {"id": "doc:revistas/rchd/2020/x", "col": "doc", "ruta": "doctrina/revistas/rchd/2020/x.md", "blob": "d" * 40,
         "bytes": 5000, "titulo": "Responsabilidad extracontractual", "autores": ["autor:barros_bourie_enrique"],
         "autores_txt": ["Enrique Barros Bourie"], "normas": [["norma:cc:2314", 1]], "revista": "revista:rchd"},
    ],
    "entradas/ta-3ta": [
        {"id": "ta:3ta:r-21-2021", "col": "ta", "ruta": "jurisprudencia_ambiental/3TA/R-21-2021.md", "blob": "e" * 40,
         "bytes": 7000, "titulo": "Reclamación", "alias": ["ta:3ta:r-35-2021"], "tribunal": "organo:3ta"},
    ],
    "entidades/normas": [{"id": "norma:cc:2314", "tipo": "norma", "label": "Código Civil, Art. 2314",
                          "citas": {"doc": 1, "tc": 1}}],
    "grafo/alias": [{"id": "norma_responsabilidad_extracontractual", "a": "norma:cc:2314"}],
}


def _escribir_mapa(destino):
    """Un mapa con la misma forma que publica el constructor (particiones + estado.json)."""
    archivos = {}
    for nombre, filas in FILAS.items():
        crudo = particiones.serializar(filas)
        gz = particiones.comprimir(crudo)
        rel = nombre + particiones.EXTENSION
        (destino / rel).parent.mkdir(parents=True, exist_ok=True)
        (destino / rel).write_bytes(gz)
        archivos[rel] = {"filas": len(filas), "sha256_contenido": particiones.sha256(crudo),
                         "sha256_gz": particiones.sha256(gz), "bytes": len(gz)}
    estado = {"esquema": 1, "sha_fuente": SHA_FUENTE, "fecha_fuente": "2026-10-01T13:03:51.000Z",
              "conteos": {"entradas": 4}, "archivos": archivos}
    datos = (json.dumps(estado, sort_keys=True, indent=1) + "\n").encode("utf-8")
    (destino / "estado.json").write_bytes(datos)
    return datos


@pytest.fixture
def mapa_local(tmp_path):
    origen = tmp_path / "mapa"
    origen.mkdir()
    _escribir_mapa(origen)
    return origen


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENLEGAL_MAPA_DIR", str(tmp_path / "cache"))
    monkeypatch.delenv("OPENLEGAL_MAPA", raising=False)
    monkeypatch.delenv("OPENLEGAL_MAPA_LOCAL", raising=False)
    mod_cliente.reiniciar_cliente()
    yield tmp_path
    mod_cliente.reiniciar_cliente()


class _Respuesta:
    def __init__(self, contenido, estado=200):
        self.content = contenido
        self.status_code = estado
        self.headers = {}


class SesionFalsa:
    """Sirve `resolve/<rev>/data/mapa/<rel>` desde carpetas locales; cuenta las peticiones."""

    def __init__(self, revisiones):
        self.revisiones = revisiones
        self.pedidos = []
        self.corromper = set()
        self._lock = threading.Lock()

    def get(self, url, timeout=None):
        with self._lock:
            self.pedidos.append(url)
        for rev, carpeta in self.revisiones.items():
            marca = f"/resolve/{rev}/data/mapa/"
            if marca in url:
                rel = url.split(marca, 1)[1]
                ruta = carpeta / rel
                if not ruta.exists():
                    return _Respuesta(b"", 404)
                datos = ruta.read_bytes()
                return _Respuesta(datos + b"x" if rel in self.corromper else datos)
        return _Respuesta(b"", 404)


def _puntero(rev, estado_bytes):
    return {"repo_id": "pablobenavidesj/doctrina-jurisprudencia-chile", "revision_mapa": rev,
            "sha256_estado": hashlib.sha256(estado_bytes).hexdigest()}


# ── Índice ────────────────────────────────────────────────────────────────────────────────────
def test_indice_consultas(mapa_local, tmp_path):
    destino = tmp_path / "mapa.sqlite"
    conteos = indice.armar(mapa_local, destino, "local", "x")
    assert conteos["entradas"] == 4
    ind = indice.Indice(destino)
    assert ind.entrada("cs:10641-2024")["ruta"] == "jurisprudencia_cs/2024/03/10641-2024.md"
    # Alias: la causa acumulada y el nodo curado apuntan al ID canónico.
    assert ind.entrada("ta:3ta:r-35-2021")["id"] == "ta:3ta:r-21-2021"
    assert ind.canonico("norma_responsabilidad_extracontractual") == "norma:cc:2314"
    citantes, total = ind.citantes(["norma:cc:2314"])
    assert total == 2 and [f["id"] for f in citantes] == ["tc:2402", "doc:revistas/rchd/2020/x"]
    solo_doc, _ = ind.citantes(["norma:cc:2314"], colecciones=["doc"])
    assert [f["id"] for f in solo_doc] == ["doc:revistas/rchd/2020/x"]
    assert [f["id"] for f in ind.citantes(["ministro:maria-gajardo-harboe"])[0]] == ["cs:10641-2024"]
    assert [f["id"] for f in ind.citantes(["cs:10641-2024"])[0]] == ["tc:2402"]
    assert ind.entidad("norma:cc:2314")["citas"] == {"doc": 1, "tc": 1}
    assert ind.rutas()["jurisprudencia_tc/2402-12-INA.md"] == "c" * 40
    assert ind.por_ruta("doctrina/revistas/rchd/2020/x.md")["id"] == "doc:revistas/rchd/2020/x"


@pytest.mark.parametrize("consulta, esperado", [
    ("indemnizacion perjuicios", "tc:2402"),            # sin tildes calza con «indemnización»
    ("Barros Bourie", "doc:revistas/rchd/2020/x"),
    ("gajardo", "cs:10641-2024"),
    ("10641-2024", "cs:10641-2024"),                    # el rol y la ruta también son texto buscable
    ('"; DROP TABLE entrada; --', None),                # la sintaxis del usuario no llega al motor
])
def test_indice_busqueda_de_texto(mapa_local, tmp_path, consulta, esperado):
    destino = tmp_path / "mapa.sqlite"
    indice.armar(mapa_local, destino, "local", "x")
    ids = [f["id"] for f in indice.Indice(destino).buscar(consulta)]
    assert (ids[0] if ids else None) == esperado


def test_indice_es_de_solo_lectura(mapa_local, tmp_path):
    destino = tmp_path / "mapa.sqlite"
    indice.armar(mapa_local, destino, "local", "x")
    con = indice.Indice(destino)._con()
    try:
        with pytest.raises(sqlite3.OperationalError):
            con.execute("DELETE FROM entrada")
    finally:
        con.close()


def test_reemplazo_reintenta_en_windows(tmp_path, monkeypatch):
    """En Windows `os.replace` falla mientras otro proceso tiene abierta la base: se reintenta."""
    origen, destino = tmp_path / "a", tmp_path / "b"
    origen.write_bytes(b"1")
    real, fallos = indice.os.replace, []

    def replace(a, b):
        if not fallos:
            fallos.append(1)
            raise PermissionError("en uso")
        real(a, b)

    monkeypatch.setattr(indice.os, "replace", replace)
    monkeypatch.setattr(indice.time, "sleep", lambda s: None)
    indice.reemplazar(origen, destino)
    assert destino.read_bytes() == b"1" and fallos == [1]


# ── Cliente ───────────────────────────────────────────────────────────────────────────────────
def test_apagado_no_consulta_nada(entorno, monkeypatch):
    monkeypatch.setenv("OPENLEGAL_MAPA", "off")
    c = mod_cliente.MapaCliente(puntero={"revision_mapa": REV_1})
    assert not c.habilitado and c.indice() is None and c.buscar("x") == []
    assert c.asegurar(bloquear=True) is False
    assert c.estado_breve()["activo"] is False


def test_puntero_nulo_sin_mapa_y_con_aviso(entorno):
    c = mod_cliente.MapaCliente(puntero={"revision_mapa": None})
    assert c.indice() is None and c.entrada("cs:10641-2024") is None
    breve = c.estado_breve()
    assert breve["activo"] is False and "suite_instalar" in breve["aviso"]


def test_mapa_local(entorno, mapa_local, monkeypatch):
    monkeypatch.setenv("OPENLEGAL_MAPA_LOCAL", str(mapa_local))
    c = mod_cliente.MapaCliente(puntero={})
    assert c.indice() is None
    assert c.asegurar(bloquear=True, timeout=60) is True, c.error
    breve = c.estado_breve()
    assert breve["activo"] and breve["revision"] == "local" and breve["sha_fuente"] == SHA_FUENTE
    assert c.entrada("cs:10641-2024")["sala"] == "sala:cs-3"
    assert c.url("jurisprudencia_tc/2402-12-INA.md").endswith(f"/blob/{SHA_FUENTE}/jurisprudencia_tc/2402-12-INA.md")
    assert c.url("x.md", fijada=False).endswith("/blob/main/x.md")
    assert (c.directorio() / "grafo" / "alias.jsonl.gz").exists()


def test_descarga_verificada_y_consultas_sin_red(entorno, mapa_local):
    estado = (mapa_local / "estado.json").read_bytes()
    sesion = SesionFalsa({REV_1: mapa_local})
    c = mod_cliente.MapaCliente(puntero=_puntero(REV_1, estado), sesion=sesion)
    assert c.asegurar(bloquear=True, timeout=60) is True, c.error
    pedidos = len(sesion.pedidos)
    assert pedidos == 1 + len(FILAS)           # estado.json + una petición por partición
    assert all(f"/resolve/{REV_1}/" in u for u in sesion.pedidos)
    # Ninguna consulta toca la red.
    c.buscar("indemnizacion"), c.entrada("tc:2402"), c.citantes(["norma:cc:2314"]), c.rutas(), c.estado_breve()
    assert len(sesion.pedidos) == pedidos
    # Una segunda vez no descarga: la revisión ya está LISTA.
    assert c.asegurar(bloquear=True, timeout=60) is True
    assert len(sesion.pedidos) == pedidos


def test_estado_alterado_se_rechaza(entorno, mapa_local):
    sesion = SesionFalsa({REV_1: mapa_local})
    c = mod_cliente.MapaCliente(puntero=_puntero(REV_1, b"otro estado"), sesion=sesion)
    assert c.asegurar(bloquear=True, timeout=60) is False
    assert "sha256" in c.error and c.indice() is None


def test_particion_corrupta_se_rechaza(entorno, mapa_local):
    estado = (mapa_local / "estado.json").read_bytes()
    sesion = SesionFalsa({REV_1: mapa_local})
    sesion.corromper.add("entradas/tc.jsonl.gz")
    c = mod_cliente.MapaCliente(puntero=_puntero(REV_1, estado), sesion=sesion)
    assert c.asegurar(bloquear=True, timeout=60) is False
    assert "corrupta" in c.error and not (entorno / "cache" / REV_1 / "LISTO").exists()


def test_respaldo_a_la_ultima_cache_con_aviso(entorno, mapa_local, tmp_path):
    estado = (mapa_local / "estado.json").read_bytes()
    sesion = SesionFalsa({REV_1: mapa_local})
    viejo = mod_cliente.MapaCliente(puntero=_puntero(REV_1, estado), sesion=sesion)
    assert viejo.asegurar(bloquear=True, timeout=60)
    # El paquete se actualiza a un puntero nuevo cuya revisión aún no se descarga.
    nuevo = mod_cliente.MapaCliente(puntero=_puntero(REV_2, estado), sesion=SesionFalsa({}))
    assert nuevo.entrada("tc:2402")["id"] == "tc:2402"
    breve = nuevo.estado_breve()
    assert breve["activo"] and breve["revision"] == REV_1 and SHA_FUENTE[:8] in breve["aviso"]
    # Sin red, asegurar falla pero el respaldo sigue sirviendo.
    assert nuevo.asegurar(bloquear=True, timeout=60) is True
    assert nuevo.error


def test_se_conservan_dos_revisiones(entorno, mapa_local, tmp_path):
    estado = (mapa_local / "estado.json").read_bytes()
    sesion = SesionFalsa({REV_1: mapa_local, REV_2: mapa_local, "3" * 40: mapa_local})
    for rev in (REV_1, REV_2, "3" * 40):
        c = mod_cliente.MapaCliente(puntero=_puntero(rev, estado), sesion=sesion)
        assert c.asegurar(bloquear=True, timeout=60), c.error
    restantes = sorted(d.name for d in (entorno / "cache").iterdir() if d.is_dir())
    assert len(restantes) == 2 and "3" * 40 in restantes


def test_dos_clientes_descargan_una_sola_vez(entorno, mapa_local):
    """El cerrojo entre procesos (filelock) serializa la descarga: el segundo encuentra LISTO."""
    estado = (mapa_local / "estado.json").read_bytes()
    sesion = SesionFalsa({REV_1: mapa_local})
    a = mod_cliente.MapaCliente(puntero=_puntero(REV_1, estado), sesion=sesion)
    b = mod_cliente.MapaCliente(puntero=_puntero(REV_1, estado), sesion=sesion)
    a.asegurar(), b.asegurar()
    a._hilo.join(60), b._hilo.join(60)
    assert a.indice() is not None and b.indice() is not None
    assert len(sesion.pedidos) == 1 + len(FILAS)


def test_cliente_compartido(entorno, monkeypatch):
    monkeypatch.setenv("OPENLEGAL_MAPA", "off")
    mod_cliente.reiniciar_cliente()
    primero = mod_cliente.obtener_cliente()
    assert mod_cliente.obtener_cliente() is primero and not primero.habilitado
    monkeypatch.setenv("OPENLEGAL_MAPA", "")
    mod_cliente.reiniciar_cliente()
    assert mod_cliente.obtener_cliente().habilitado


def test_cache_de_otro_esquema_de_indice_se_rearma(entorno, mapa_local):
    """Una base armada por una versión anterior del índice no se consulta: se vuelve a armar."""
    estado = (mapa_local / "estado.json").read_bytes()
    sesion = SesionFalsa({REV_1: mapa_local})
    c = mod_cliente.MapaCliente(puntero=_puntero(REV_1, estado), sesion=sesion)
    assert c.asegurar(bloquear=True, timeout=60)
    marca = entorno / "cache" / REV_1 / "LISTO"
    vieja = json.loads(marca.read_text(encoding="utf-8"))
    vieja["indice"] = "1"
    marca.write_text(json.dumps(vieja), encoding="utf-8")
    nuevo = mod_cliente.MapaCliente(puntero=_puntero(REV_1, estado), sesion=sesion)
    assert nuevo.indice() is None                                  # no se consulta una base incompatible
    assert nuevo.asegurar(bloquear=True, timeout=60) and nuevo.entrada("tc:2402")
    assert json.loads(marca.read_text(encoding="utf-8"))["indice"] == mod_cliente.indice.ESQUEMA_INDICE


def test_estado_con_rutas_fuera_del_mapa_se_rechaza_sin_escribir(entorno, mapa_local, tmp_path):
    """Con OPENLEGAL_MAPA=main el estado no se verifica contra un sha256 del repo: sus rutas son un
    dato no confiable y ninguna puede escribir fuera de la caché."""
    malo = (json.dumps({"archivos": {"entradas/../../../escape.jsonl.gz": {"sha256_gz": "0" * 64}}}) + "\n").encode()
    (mapa_local / "estado.json").write_bytes(malo)
    sesion = SesionFalsa({REV_1: mapa_local})
    c = mod_cliente.MapaCliente(puntero=_puntero(REV_1, malo), sesion=sesion)
    assert c.asegurar(bloquear=True, timeout=60) is False
    assert "inválida" in c.error and c.indice() is None
    assert [u for u in sesion.pedidos if "escape" in u] == []
    assert not list(tmp_path.rglob("escape.jsonl.gz"))
