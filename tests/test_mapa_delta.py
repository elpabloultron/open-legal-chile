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
    from mapa_corpus import particiones
    ruta.write_bytes(particiones.comprimir(particiones.descomprimir(ruta.read_bytes()) + b'{"id":"tc:1"}\n'))
    assert any("sha256_gz no calza" in p for p in constructor.validar(str(tmp_path / "m"), inv))
    ruta.write_bytes(b"no es gzip")
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


# ── Regresiones: el delta tiene que dar exactamente lo mismo que reconstruir ────────────────────
def _revista(autor):
    return (f'---\ntitulo: "Estudio"\nautores: "{autor}"\nrevista: "Revista Chilena de Derecho"\nanio: 2020\n---\n\n'
            "# Estudio\n\nTexto.\n").encode("utf-8")


def test_nombres_en_nfd_y_nfc_son_el_mismo_autor_en_delta_y_completo(tmp_path):
    """En memoria las filas recién extraídas pueden traer tildes descompuestas (NFD); en disco van
    en NFC. Si las entidades se cuentan antes de normalizar, el rótulo del autor cambia según la
    construcción sea completa o delta."""
    import unicodedata
    nfd = unicodedata.normalize("NFD", "Fernández Toledo, Raúl")
    datos = dict(_datos_base(), **{
        "doctrina/revistas/rchd/2020/a.md": _revista(nfd),
        "doctrina/revistas/rchd/2021/b.md": _revista("Fernández Toledo, Raúl"),
        "doctrina/revistas/rchd/2022/c.md": _revista("Raúl Fernández Toledo"),
        "doctrina/revistas/rchd/2023/d.md": _revista("Raúl Fernández Toledo"),
    })
    # Completo: NFD 1 + NFC 1 frente a «Raúl…» 2 → ganaba «Raúl…»; el delta (filas de disco, NFC)
    # contaba 2 contra 2 y el desempate elegía «Fernández…»: dos mapas distintos del mismo dataset.
    previos = {k: v for k, v in datos.items() if not k.endswith("d.md")}
    _construir(previos, tmp_path / "m")
    _construir(datos, tmp_path / "m", base=constructor.leer_mapa(str(tmp_path / "m")))
    _construir(datos, tmp_path / "completo")
    assert _bytes_de(tmp_path / "m") == _bytes_de(tmp_path / "completo")


def _ficha_ta(extra=""):
    return ("# Reclamación — R-21-2021\n\n- **Tribunal:** Tercer Tribunal Ambiental\n- **Rol:** R-21-2021\n"
            f"- **Fecha:** 2021-11-02\n{extra}").encode("utf-8")


def test_colision_de_ids_se_resuelve_igual_en_delta_cuando_cae_el_principal(tmp_path):
    a, b = "jurisprudencia_ambiental/3TA/R-21-2021.md", "jurisprudencia_ambiental/3TA/R-21-2021_copia.md"
    datos = dict(_datos_base(), **{a: _ficha_ta(), b: _ficha_ta("- **Materia:** copia\n")})
    _, _, estado, _ = _construir(datos, tmp_path / "m")
    filas = {f["ruta"]: f for f in constructor.leer_mapa(str(tmp_path / "m"))["filas"]}
    assert filas[a]["id"] == "ta:3ta:r-21-2021" and filas[b]["id"].startswith("ta:3ta:r-21-2021:")
    assert estado["calidad"]["ids_compartidos"] == 1
    # Desaparece el archivo que tenía el ID: la copia lo recupera, igual que si se reconstruyera todo.
    sin_a = {k: v for k, v in datos.items() if k != a}
    _, _, estado_delta, _ = _construir(sin_a, tmp_path / "m", base=constructor.leer_mapa(str(tmp_path / "m")))
    filas = {f["ruta"]: f for f in constructor.leer_mapa(str(tmp_path / "m"))["filas"]}
    assert filas[b]["id"] == "ta:3ta:r-21-2021" and "id_base" not in filas[b]
    assert estado_delta["calidad"].get("ids_compartidos", 0) == 0
    _construir(sin_a, tmp_path / "completo")
    assert _bytes_de(tmp_path / "m") == _bytes_de(tmp_path / "completo")


# ── Rutas del estado (dato no confiable), nombres de partición y NFC ─────────────────────────
@pytest.mark.parametrize("rel", ["entradas/../../x.jsonl.gz", "../estado.jsonl.gz", "entradas/a/b.jsonl.gz",
                                 "entradas\\..\\x.jsonl.gz", "estado.json", "/etc/x.jsonl.gz", "entradas/.jsonl.gz"])
def test_archivos_de_rechaza_rutas_fuera_del_mapa(rel):
    from mapa_corpus import particiones
    with pytest.raises(ValueError, match="inválida"):
        particiones.archivos_de({"archivos": {rel: {"sha256_gz": "0" * 64}}})


def test_particiones_con_nombres_seguros():
    from mapa_corpus import particiones
    assert particiones.particion_de("doctrina/Derecho Civil/x.md") == "entradas/doc-derecho_civil"
    assert particiones.particion_de("doctrina/revistas/Rev. Ñuñoa/2020/x.md") == "entradas/doc-rev-rev_nunoa"
    nombre = particiones.particion_de("doctrina/../../x/y.md") + particiones.EXTENSION
    assert particiones.archivos_de({"archivos": {nombre: {}}})


def test_nfc_deja_rutas_y_enlaces_literales():
    import unicodedata
    from mapa_corpus import particiones
    nfd = unicodedata.normalize("NFD", "doctrina/civil/Teoría.md")
    fila = particiones.nfc({"ruta": nfd, "titulo": nfd, "url": nfd})
    assert fila["ruta"] == nfd and fila["url"] == nfd                 # la ruta de HF, tal cual
    assert fila["titulo"] == unicodedata.normalize("NFC", nfd)


def test_ruta_nfd_valida_y_no_se_vuelve_a_bajar(tmp_path):
    import unicodedata
    ruta = unicodedata.normalize("NFD", "doctrina/civil/Teoría del contrato.md")
    datos = dict(_datos_base(), **{ruta: "# Teoría\n\nEl artículo 1545 del Código Civil.\n".encode("utf-8")})
    inv, _, _, _ = _construir(datos, tmp_path / "m")
    assert constructor.validar(str(tmp_path / "m"), inv) == []
    _, desc, _, _ = _construir(datos, tmp_path / "m", base=constructor.leer_mapa(str(tmp_path / "m")))
    assert desc.pedidos == []


# ── El delta da el mismo estado que reconstruir, también en la calidad ───────────────────────
def test_calidad_de_un_archivo_omitido_se_conserva_en_el_delta(tmp_path, monkeypatch):
    monkeypatch.setattr(constructor, "MAX_BYTES", 1000)            # la revista (más grande) se omite
    datos = _datos_base()
    _construir(datos, tmp_path / "m")
    datos[RUTA_TA] += b"\nOtro parrafo.\n"
    _, _, estado, _ = _construir(datos, tmp_path / "m", base=constructor.leer_mapa(str(tmp_path / "m")))
    _construir(datos, tmp_path / "completo")
    assert estado["calidad"].get("fila:omitido_por_tamano", 0) >= 1
    assert _bytes_de(tmp_path / "m") == _bytes_de(tmp_path / "completo")


def _fichas_cs_md():
    salida = {}
    for ruta in FICHAS_CS:
        rol, era = ruta.rsplit("/", 1)[1][:-3], ruta.split("/")[1]
        salida[ruta] = (f"# Ficha\n\n- **Tribunal:** Corte Suprema — TERCERA, CONSTITUCIONAL\n"
                        f"- **Rol:** {rol} · **Era:** {era} · **Fecha:** {era}-03-04\n").encode("utf-8")
    return salida


def test_indice_cs_borrado_el_delta_relee_las_fichas(tmp_path):
    datos = dict(_datos_base(), **_fichas_cs_md())
    _construir(datos, tmp_path / "m")
    sin_indice = {k: v for k, v in datos.items() if k != constructor.INDICE_CS}
    _, desc, _, _ = _construir(sin_indice, tmp_path / "m", base=constructor.leer_mapa(str(tmp_path / "m")))
    assert sorted(desc.pedidos) == sorted(FICHAS_CS)               # sin índice, las fichas salen del .md
    _construir(sin_indice, tmp_path / "completo")
    assert _bytes_de(tmp_path / "m") == _bytes_de(tmp_path / "completo")


# ── Colisiones con el mismo nombre de archivo ────────────────────────────────────────────────
def test_mismo_rol_en_tres_meses_da_ids_distintos(tmp_path):
    rutas = [f"jurisprudencia_ambiental/3TA/{m}/R-21-2021.md" for m in ("a", "b", "c")]
    datos = dict(_datos_base(), **{r: _ficha_ta(f"- **Materia:** {r}\n") for r in rutas})
    inv, _, estado, _ = _construir(datos, tmp_path / "m")
    assert constructor.validar(str(tmp_path / "m"), inv) == []
    ids_ = {f["ruta"]: f["id"] for f in constructor.leer_mapa(str(tmp_path / "m"))["filas"] if f["ruta"] in rutas}
    assert len(set(ids_.values())) == 3 and estado["calidad"]["ids_compartidos"] == 2


# ── validar acepta una partición recomprimida con otro zlib si el contenido es el mismo ───────
def test_validar_acepta_otra_compresion_del_mismo_contenido(tmp_path):
    import gzip
    from mapa_corpus import particiones
    inv, _, estado, _ = _construir(_datos_base(), tmp_path / "m")
    rel = next(r for r in estado["archivos"] if r.startswith("entradas/tc"))
    ruta = tmp_path / "m" / rel
    otra = gzip.compress(particiones.descomprimir(ruta.read_bytes()), compresslevel=1, mtime=0)
    assert otra != ruta.read_bytes()
    ruta.write_bytes(otra)
    assert constructor.validar(str(tmp_path / "m"), inv) == []


# ── CLI: el puntero que no llegó se rehace; un mapa publicado entretanto deja la corrida superada ──
def test_estado_sin_cambios_pero_puntero_atrasado(cli_falso, tmp_path, monkeypatch):
    from mapa_corpus import publicador
    publicado = tmp_path / "publicado" / "estado.json"
    monkeypatch.setattr(cli, "_bajar_base_hf", lambda destino, rev, token: (
        destino.mkdir(parents=True, exist_ok=True), (destino / "estado.json").write_bytes(publicado.read_bytes()),
        cli_falso.estado_hf["base"])[-1])
    puntero = tmp_path / "puntero.json"
    puntero.write_text(json.dumps({"revision_mapa": None, "sha256_estado": None}), encoding="utf-8")
    monkeypatch.setattr(publicador, "PUNTERO", puntero)
    plan, salida = cli_falso.correr()
    assert plan["cambio"] is False and plan["puntero_pendiente"] is True and "puntero=true" in salida
    trabajo = tmp_path / "trabajo"
    assert cli.main(["puntero", "--trabajo", str(trabajo), "--github-output", str(tmp_path / "out2")]) == 0
    nuevo = json.loads(puntero.read_text(encoding="utf-8"))
    assert nuevo["revision_mapa"] == SHA and nuevo["sha256_estado"] == \
        __import__("hashlib").sha256(publicado.read_bytes()).hexdigest()
    assert "revision_mapa=" + SHA in (tmp_path / "out2").read_text(encoding="utf-8")
    assert (trabajo / "reporte.md").exists()
    # Con el puntero al día, nada pendiente.
    assert cli_falso.correr()[0]["puntero_pendiente"] is False


@pytest.mark.parametrize("remoto, codigo", [("igual", 0), ("otro", 3)])
def test_publicar_superado_si_el_mapa_publicado_cambio(tmp_path, monkeypatch, remoto, codigo):
    trabajo = tmp_path / "trabajo"
    (trabajo / "base").mkdir(parents=True)
    (trabajo / "base" / "estado.json").write_bytes(b'{"base": 1}')
    (trabajo / "plan.json").write_text(json.dumps({"sha": SHA, "base": "hf:main", "prefijos": []}), encoding="utf-8")
    monkeypatch.setattr(cli, "_token", lambda: None)
    monkeypatch.setattr(cli.inventario, "sha_main", lambda token=None: ("h" * 40, None))
    monkeypatch.setattr(cli, "_bajar_estado", lambda rev, token: b'{"base": 1}' if remoto == "igual" else b'{"x": 2}')
    llamadas = []
    monkeypatch.setattr(cli.publicador, "publicar", lambda d, rem, padre, token, **k: (
        llamadas.append((rem, padre)), {"publicado": False, "motivo": "dry-run"})[-1])
    assert cli.main(["publicar", "--trabajo", str(trabajo)]) == codigo
    assert llamadas == ([({"base": 1}, "h" * 40)] if codigo == 0 else [])
