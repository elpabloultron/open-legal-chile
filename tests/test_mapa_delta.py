"""Inventario, delta e incrementalidad del constructor del mapa (`mapa_corpus`).

Sobre un mini-dataset con archivos reales recortados (una sentencia del TC, una ficha 1TA, un
artículo de la REHJ y el índice de la Corte Suprema) y un descargador falso: sin red, sin
`~/.cache` y sin tocar archivos versionados.
"""

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from mapa_corpus import __main__ as cli
from mapa_corpus import constructor, inventario
from mapa_corpus.inventario import Archivo

FX = Path(__file__).parent / "fixtures" / "mapa" / "delta"
CURADO = str(FX / "curado.json")
SHA = "9" * 40
RUTA_TC = "jurisprudencia_tc/15907-06a-INA.md"
RUTA_TA = "jurisprudencia_ambiental/1TA/D-25-2023.md"
RUTA_REV = "doctrina/revistas/rehj/2015/rehj_2015_n37_791_una_fuente_poco_conocida_del_codigo_civil_chileno_la_memoria.md"
FUENTES = {
    RUTA_TC: "tc_15907-06a-INA.md",
    RUTA_TA: "ta_1TA_D-25-2023.md",
    RUTA_REV: "rev_rehj_2015_n37_791.md",
    constructor.INDICE_CS: "cs_sentencias_2anios.jsonl",
}
# Las fichas .md de la CS no se bajan: sus filas salen del índice (basta que estén en el inventario).
FICHAS_CS = ["jurisprudencia_cs/2024/03/10641-2024.md", "jurisprudencia_cs/2025/03/9126-2025.md",
             "jurisprudencia_cs/2017/08/4842-2017.md", "jurisprudencia_cs/2026/09/50838-2026.md"]
SOLO_INVENTARIO = ["README.md", "graphify/GRAPH_REPORT.md", "data/catalogo/indice_agentes.json"]


def _datos_base():
    return {ruta: (FX / nombre).read_bytes() for ruta, nombre in FUENTES.items()}


def _inventario(datos):
    inv = {r: Archivo(r, inventario.blob_git(b), len(b)) for r, b in datos.items()}
    for i, r in enumerate(FICHAS_CS + SOLO_INVENTARIO):
        inv[r] = Archivo(r, f"{i:040d}", 700)
    return inv


class DescargadorFalso:
    """Sirve bytes por ruta y anota qué se pidió (cuenta como una «petición» a HF)."""

    def __init__(self, datos):
        self.datos = datos
        self.pedidos = []
        self.peticiones = 0

    def obtener(self, a):
        self.pedidos.append(a.ruta)
        return self.datos[a.ruta]

    def obtener_varios(self, archivos, al_avanzar=None):
        return {a.ruta: self.obtener(a) for a in archivos}


def _construir(datos, destino, base=None):
    inv = _inventario(datos)
    desc = DescargadorFalso(datos)
    res = constructor.construir(inv, SHA, desc, CURADO, base=base, avisar=lambda m: None)
    estado = constructor.escribir(res, str(destino), (base or {}).get("estado"))
    return inv, desc, estado, res


def _bytes_de(directorio):
    return {str(p.relative_to(directorio)): p.read_bytes() for p in sorted(Path(directorio).rglob("*")) if p.is_file()}


# ── Construcción, idempotencia y validación ──────────────────────────────────────────────────
def test_construccion_completa_y_valida(tmp_path):
    inv, desc, estado, _ = _construir(_datos_base(), tmp_path / "m")
    # Solo se bajan los textos (TC, TA, revista) y el índice CS; nada de lo que es solo inventario.
    assert sorted(desc.pedidos) == sorted(FUENTES)
    assert constructor.validar(str(tmp_path / "m"), inv) == []
    filas = {f["id"]: f for f in constructor.leer_mapa(str(tmp_path / "m"))["filas"]}
    assert filas["cs:10641-2024"]["ruta"] == "jurisprudencia_cs/2024/03/10641-2024.md"
    assert estado["conteos"]["col_cs"] == 4 and estado["conteos"]["entradas"] == len(inv)
    assert estado["sha_fuente"] == SHA and estado["version_reglas"] == constructor.version_reglas()


def test_dos_construcciones_dan_los_mismos_bytes(tmp_path):
    _construir(_datos_base(), tmp_path / "a")
    _construir(_datos_base(), tmp_path / "b")
    assert _bytes_de(tmp_path / "a") == _bytes_de(tmp_path / "b")


def test_validar_detecta_una_particion_alterada(tmp_path):
    inv, _, estado, _ = _construir(_datos_base(), tmp_path / "m")
    rel = next(r for r in estado["archivos"] if r.startswith("entradas/tc"))
    ruta = tmp_path / "m" / rel
    ruta.write_bytes(ruta.read_bytes() + b"\x00")
    assert any("sha256_gz no calza" in p for p in constructor.validar(str(tmp_path / "m"), inv))


def test_validar_detecta_archivos_sin_entrada(tmp_path):
    inv, _, _, _ = _construir(_datos_base(), tmp_path / "m")
    inv["doctrina/civil/nuevo.md"] = Archivo("doctrina/civil/nuevo.md", "1" * 40, 10)
    assert any("sin entrada" in p for p in constructor.validar(str(tmp_path / "m"), inv))


# ── Delta ─────────────────────────────────────────────────────────────────────────────────────
def test_delta_procesa_solo_lo_cambiado_y_equivale_a_reconstruir(tmp_path):
    _construir(_datos_base(), tmp_path / "m")
    base = constructor.leer_mapa(str(tmp_path / "m"))
    antes = json.loads((tmp_path / "m" / "estado.json").read_text(encoding="utf-8"))["archivos"]

    datos = _datos_base()
    datos[RUTA_TA] += "\nLa demanda invoca el artículo 2314 del Código Civil.\n".encode("utf-8")
    _, desc, estado, res = _construir(datos, tmp_path / "m", base=base)

    assert desc.pedidos == [RUTA_TA]                              # solo se bajó lo modificado
    assert res["reporte"]["modificados"] == 1 and res["reporte"]["altas"] == 0
    assert estado["archivos"]["entradas/tc.jsonl.gz"] == antes["entradas/tc.jsonl.gz"]
    assert estado["archivos"]["entradas/ta-1ta.jsonl.gz"] != antes["entradas/ta-1ta.jsonl.gz"]
    # El delta deja exactamente el mismo mapa que una construcción completa desde cero.
    _construir(datos, tmp_path / "completo")
    assert _bytes_de(tmp_path / "m") == _bytes_de(tmp_path / "completo")


def test_baja_elimina_la_particion_vacia(tmp_path):
    _construir(_datos_base(), tmp_path / "m")
    base = constructor.leer_mapa(str(tmp_path / "m"))
    datos = _datos_base()
    del datos[RUTA_TA]
    _, desc, estado, res = _construir(datos, tmp_path / "m", base=base)
    assert desc.pedidos == [] and res["reporte"]["bajas"] == 1
    assert "entradas/ta-1ta.jsonl.gz" not in estado["archivos"]
    assert not (tmp_path / "m" / "entradas" / "ta-1ta.jsonl.gz").exists()


def test_cambio_de_reglas_reconstruye_todo(tmp_path):
    _construir(_datos_base(), tmp_path / "m")
    base = constructor.leer_mapa(str(tmp_path / "m"))
    base["estado"]["version_reglas"] = "reglas-viejas"
    _, desc, _, res = _construir(_datos_base(), tmp_path / "m", base=base)
    assert sorted(desc.pedidos) == sorted(FUENTES) and res["reporte"]["altas"] == len(_inventario(_datos_base()))


# ── Inventario y huella ──────────────────────────────────────────────────────────────────────
def test_inventario_de_una_llamada_con_exclusiones():
    siblings = [SimpleNamespace(rfilename=r, blob_id=b, size=n, lfs=lfs) for r, b, n, lfs in [
        (RUTA_TC, "a" * 40, 10, None),
        (constructor.INDICE_CS, "b" * 40, 99, SimpleNamespace(sha256="c" * 64)),
        ("data/mapa/estado.json", "d" * 40, 5, None),           # el propio mapa: nunca se inventaría
        (".gitattributes", "e" * 40, 5, None),
        ("jurisprudencia_tc/testrol2-34566.md", "f" * 40, 5, None),   # basura de prueba del scraper
    ]]
    llamadas = []

    class ApiFalsa:
        def dataset_info(self, repo_id, revision, files_metadata):
            llamadas.append((repo_id, revision, files_metadata))
            return SimpleNamespace(siblings=siblings)

    inv = inventario.inventario(SHA, api=ApiFalsa())
    assert sorted(inv) == sorted([RUTA_TC, constructor.INDICE_CS])
    assert inv[constructor.INDICE_CS].lfs_sha256 == "c" * 64
    assert llamadas == [(inventario.REPO_ID, SHA, True)]


def test_huella_ignora_graphify_y_cambia_con_el_contenido_y_las_reglas():
    inv = _inventario(_datos_base())
    h = inventario.huella(inv.values(), "r1")
    con_graphify = dict(inv, **{"graphify/x.json": Archivo("graphify/x.json", "1" * 40, 3)})
    assert inventario.huella(con_graphify.values(), "r1") == h
    assert inventario.huella(inv.values(), "r2") != h
    otro = dict(inv, **{RUTA_TA: Archivo(RUTA_TA, "2" * 40, 3)})
    assert inventario.huella(otro.values(), "r1") != h


def test_delta_por_blob():
    previo = {"a.md": "1", "b.md": "2", "c.md": "3"}
    actual = {"a.md": Archivo("a.md", "1", 1), "b.md": Archivo("b.md", "9", 1), "d.md": Archivo("d.md", "4", 1)}
    assert inventario.delta(previo, actual) == (["d.md"], ["b.md"], ["c.md"])


# ── Descargador y limitador ──────────────────────────────────────────────────────────────────
class _Respuesta:
    def __init__(self, contenido, estado=200, encabezados=None):
        self.content, self.status_code, self.headers = contenido, estado, encabezados or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_descargador_verifica_y_usa_la_cache(tmp_path, monkeypatch):
    datos = b"contenido real"
    pedidos = []
    sesion = SimpleNamespace(get=lambda url, timeout=None: pedidos.append(url) or _Respuesta(datos))
    monkeypatch.setattr(inventario, "_sesion", lambda token: sesion)
    d = inventario.Descargador(SHA, cache_dir=str(tmp_path), hilos=2)
    a = Archivo("doctrina/civil/x y z.md", inventario.blob_git(datos), len(datos))
    assert d.obtener(a) == datos and (tmp_path / a.blob).read_bytes() == datos
    assert pedidos == [f"{inventario.ENDPOINT}/datasets/{inventario.REPO_ID}/resolve/{SHA}/doctrina/civil/x%20y%20z.md"]
    assert d.obtener(a) == datos and len(pedidos) == 1           # segunda vez: de la caché


def test_descargador_rechaza_contenido_corrupto(tmp_path, monkeypatch):
    sesion = SimpleNamespace(get=lambda url, timeout=None: _Respuesta(b"otra cosa"))
    monkeypatch.setattr(inventario, "_sesion", lambda token: sesion)
    monkeypatch.setattr(inventario.time, "sleep", lambda s: None)
    d = inventario.Descargador(SHA, cache_dir=str(tmp_path), hilos=1)
    a = Archivo("x.md", inventario.blob_git(b"lo esperado"), 11)
    with pytest.raises(RuntimeError, match="no se pudo bajar"):
        d.obtener(a)
    assert not any(tmp_path.iterdir())                          # nada corrupto queda en caché


def test_descargador_verifica_lfs_por_sha256(tmp_path, monkeypatch):
    import hashlib
    datos = b"indice grande"
    sesion = SimpleNamespace(get=lambda url, timeout=None: _Respuesta(datos))
    monkeypatch.setattr(inventario, "_sesion", lambda token: sesion)
    d = inventario.Descargador(SHA, cache_dir=str(tmp_path), hilos=1)
    a = Archivo(constructor.INDICE_CS, "no-es-el-blob", len(datos), hashlib.sha256(datos).hexdigest())
    assert d.obtener(a) == datos and (tmp_path / a.lfs_sha256).exists()


def test_limitador_respeta_429_y_la_ventana():
    reloj = {"t": 0.0}
    dormidas = []

    def dormir(s):
        dormidas.append(round(s, 1))
        reloj["t"] += s

    lim = inventario.Limitador(por_ventana=2, ventana=10.0, dormir=dormir, reloj=lambda: reloj["t"])
    lim.antes(), lim.antes()
    lim.antes()                                                 # tercera en la misma ventana: espera
    assert dormidas == [10.5]
    lim.despues({"Retry-After": "30"}, 429)
    lim.antes()
    assert dormidas[-1] == 30.0
    lim.despues({"ratelimit": '"resolvers";r=5;t=12'}, 200)     # quedan pocas unidades: espera t
    lim.antes()
    assert dormidas[-1] == 13.0


# ── CLI: estado ───────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def cli_falso(tmp_path, monkeypatch):
    """`cmd_estado` con HF simulado: inventario del mini-dataset y, como base, su mapa publicado."""
    datos = _datos_base()
    inv, _, _, _ = _construir(datos, tmp_path / "publicado")
    base = constructor.leer_mapa(str(tmp_path / "publicado"))
    viejo = "2026-01-01T00:00:00.000Z"
    estado_hf = {"inv": inv, "modificado": viejo, "base": base}
    monkeypatch.setattr(cli, "CURADO", Path(CURADO))
    monkeypatch.setattr(cli, "_token", lambda: None)
    monkeypatch.setattr(cli.inventario, "sha_main", lambda token=None: (SHA, estado_hf["modificado"]))
    monkeypatch.setattr(cli.inventario, "inventario", lambda sha, token=None: dict(estado_hf["inv"]))
    monkeypatch.setattr(cli, "_bajar_base_hf", lambda destino, rev, token: estado_hf["base"])

    def correr(*extra):
        trabajo = tmp_path / "trabajo"
        salida = tmp_path / "github_output"
        assert cli.main(["estado", "--trabajo", str(trabajo), "--github-output", str(salida), *extra]) == 0
        return json.loads((trabajo / "plan.json").read_text(encoding="utf-8")), salida.read_text(encoding="utf-8")

    return SimpleNamespace(correr=correr, estado_hf=estado_hf)


def test_estado_sin_cambios_y_autorreferencia(cli_falso):
    plan, salida = cli_falso.correr()
    assert plan["cambio"] is False and "cambio=false" in salida
    # Publicar el mapa agrega data/mapa/** al dataset: el inventario real lo excluye, y graphify/**
    # queda fuera de la huella. La corrida siguiente sigue «sin cambios».
    cli_falso.estado_hf["inv"]["graphify/nuevo.json"] = Archivo("graphify/nuevo.json", "7" * 40, 9)
    assert cli_falso.correr()[0]["cambio"] is False


def test_estado_detecta_el_delta(cli_falso):
    cli_falso.estado_hf["inv"][RUTA_TA] = Archivo(RUTA_TA, "8" * 40, 99)
    plan, salida = cli_falso.correr()
    assert plan["cambio"] is True and plan["motivo"].startswith("delta: +0 ~1 -0")
    assert "modo=delta" in salida


def test_estado_espera_si_la_fuente_esta_en_movimiento(cli_falso):
    from datetime import datetime, timezone
    cli_falso.estado_hf["inv"][RUTA_TA] = Archivo(RUTA_TA, "8" * 40, 99)
    cli_falso.estado_hf["modificado"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    plan, _ = cli_falso.correr()
    assert plan["cambio"] is False and "movimiento" in plan["motivo"]
    assert cli_falso.correr("--ignorar-movimiento")[0]["cambio"] is True


def test_estado_reglas_nuevas_es_construccion_completa(cli_falso):
    cli_falso.estado_hf["base"]["estado"]["version_reglas"] = "reglas-viejas"
    cli_falso.estado_hf["base"]["estado"]["huella_fuente"] = "otra"
    plan, _ = cli_falso.correr()
    assert plan["cambio"] is True and plan["motivo"].startswith("completo")


def test_trabajo_dentro_de_data_se_rechaza():
    with pytest.raises(SystemExit):
        cli._trabajo(os.path.join(str(cli.REPO_RAIZ), "data", "mapa_trabajo"))


def test_estado_programado_sin_mapa_publicado_no_construye(cli_falso):
    cli_falso.estado_hf["base"] = None
    plan, salida = cli_falso.correr("--requiere-base")
    assert plan["cambio"] is False and "a mano" in plan["motivo"] and "cambio=false" in salida
    assert cli_falso.correr()[0]["cambio"] is True              # a mano (sin la marca) sí construye
