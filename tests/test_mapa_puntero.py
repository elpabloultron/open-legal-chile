"""Puntero versionado y publicación del mapa (`mapa_corpus.publicador`, `verificacion`).

La publicación se prueba con una HfApi falsa inyectada y el puntero se escribe en `tmp_path`: el
`mapa_corpus/puntero.json` versionado no se toca nunca.
"""

import hashlib
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from mapa_corpus import RUTA_HF, publicador, verificacion
from mapa_corpus import __main__ as cli

RAIZ = Path(__file__).resolve().parent.parent
PUNTERO = RAIZ / "mapa_corpus" / "puntero.json"


# ── Puntero versionado ────────────────────────────────────────────────────────────────────────
def test_esquema_del_puntero_versionado():
    texto = PUNTERO.read_text(encoding="utf-8")
    datos = json.loads(texto)
    assert texto.endswith("\n") and list(datos) == sorted(datos)
    assert datos["repo_id"] == "pablobenavidesj/doctrina-jurisprudencia-chile" and datos["ruta"] == RUTA_HF
    assert datos["revision_mapa"] is None or re.fullmatch(r"[0-9a-f]{40}", datos["revision_mapa"])
    assert datos["sha256_estado"] is None or re.fullmatch(r"[0-9a-f]{64}", datos["sha256_estado"])
    assert datos["sha_fuente"] is None or re.fullmatch(r"[0-9a-f]{40}", datos["sha_fuente"])
    assert (datos["revision_mapa"] is None) == (datos["sha256_estado"] is None)


def test_versiones_fijadas_del_constructor():
    fijadas = publicador.versiones_fijadas()
    assert set(fijadas) == {"networkx", "huggingface-hub"}
    assert all(re.fullmatch(r"\d+(\.\d+)+", v) for v in fijadas.values())


# ── Publicación ───────────────────────────────────────────────────────────────────────────────
class ApiFalsa:
    def __init__(self, existentes=(), tags=()):
        self.existentes = set(existentes)
        self.tags = list(tags)
        self.commits = []
        self.tags_creados = []

    def get_paths_info(self, repo_id, paths, repo_type, revision):
        return [SimpleNamespace(path=p) for p in paths if p in self.existentes]

    def create_commit(self, repo_id, repo_type, operations, commit_message, parent_commit):
        self.commits.append({"operaciones": operations, "mensaje": commit_message, "padre": parent_commit})
        return SimpleNamespace(oid="c" * 40)

    def list_repo_refs(self, repo_id, repo_type):
        return SimpleNamespace(tags=[SimpleNamespace(name=t) for t in self.tags])

    def create_tag(self, repo_id, tag, revision, repo_type):
        self.tags_creados.append((tag, revision))


def _rutas(ops):
    return sorted((type(o).__name__, o.path_in_repo) for o in ops)


@pytest.fixture
def mapa(fabrica_mapa):
    return fabrica_mapa()


def test_publicar_sube_todo_la_primera_vez_y_escribe_el_puntero(mapa, tmp_path):
    api = ApiFalsa(tags=["mapa-1", "otro"])
    destino = tmp_path / "puntero.json"
    res = publicador.publicar(str(mapa), None, "a" * 40, None, api=api, forzar_versiones=True, ruta_puntero=destino)
    estado_bytes = (mapa / "estado.json").read_bytes()
    assert res["publicado"] and res["tag"] == "mapa-2" and api.tags_creados == [("mapa-2", "c" * 40)]
    commit = api.commits[0]
    assert commit["padre"] == "a" * 40                       # si main avanzó, HF rechaza el commit
    subidos = {o.path_in_repo for o in commit["operaciones"]}
    assert f"{RUTA_HF}/estado.json" in subidos and all(p.startswith(f"{RUTA_HF}/") for p in subidos)
    puntero = json.loads(destino.read_text(encoding="utf-8"))
    assert puntero["revision_mapa"] == "c" * 40
    assert puntero["sha256_estado"] == hashlib.sha256(estado_bytes).hexdigest()
    assert json.loads(PUNTERO.read_text(encoding="utf-8"))["revision_mapa"] is None   # el versionado, intacto


def test_publicar_solo_lo_cambiado_y_borra_lo_que_ya_no_existe(mapa, tmp_path):
    estado = json.loads((mapa / "estado.json").read_text(encoding="utf-8"))
    remoto = {"archivos": dict(estado["archivos"])}
    rel_cambiado = sorted(remoto["archivos"])[0]
    remoto["archivos"][rel_cambiado] = dict(remoto["archivos"][rel_cambiado], sha256_gz="0" * 64)
    remoto["archivos"]["entradas/vieja.jsonl.gz"] = {"sha256_gz": "1" * 64}
    remoto["archivos"]["entradas/fantasma.jsonl.gz"] = {"sha256_gz": "2" * 64}
    assert publicador.operaciones(str(mapa), remoto) == {
        "subir": [rel_cambiado], "borrar": ["entradas/fantasma.jsonl.gz", "entradas/vieja.jsonl.gz"]}
    api = ApiFalsa(existentes=[f"{RUTA_HF}/entradas/vieja.jsonl.gz"])
    publicador.publicar(str(mapa), remoto, "a" * 40, None, api=api, forzar_versiones=True,
                        ruta_puntero=tmp_path / "p.json")
    # Solo se borra lo que existe de verdad en HF (un Delete de algo inexistente hace fallar el commit).
    assert _rutas(api.commits[0]["operaciones"]) == sorted([
        ("CommitOperationAdd", f"{RUTA_HF}/{rel_cambiado}"),
        ("CommitOperationAdd", f"{RUTA_HF}/estado.json"),
        ("CommitOperationDelete", f"{RUTA_HF}/entradas/vieja.jsonl.gz")])


def test_sin_cambios_no_hay_commit(mapa, tmp_path):
    estado = json.loads((mapa / "estado.json").read_text(encoding="utf-8"))
    api = ApiFalsa()
    res = publicador.publicar(str(mapa), estado, "a" * 40, None, api=api, ruta_puntero=tmp_path / "p.json")
    assert res == {"publicado": False, "motivo": "sin cambios", "subir": [], "borrar": []}
    assert api.commits == [] and not (tmp_path / "p.json").exists()


def test_dry_run_no_llama_a_hf(mapa, tmp_path):
    api = ApiFalsa()
    res = publicador.publicar(str(mapa), None, "a" * 40, None, api=api, dry_run=True, ruta_puntero=tmp_path / "p.json")
    assert res["publicado"] is False and res["motivo"] == "dry-run" and res["subir"]
    assert api.commits == [] and not (tmp_path / "p.json").exists()


def test_versiones_distintas_bloquean_la_publicacion(mapa, tmp_path, monkeypatch):
    monkeypatch.setattr(publicador, "versiones_distintas", lambda: ["networkx==9.9 (se espera 3.7)"])
    with pytest.raises(RuntimeError, match="versiones distintas"):
        publicador.publicar(str(mapa), None, "a" * 40, None, api=ApiFalsa(), ruta_puntero=tmp_path / "p.json")
    res = publicador.publicar(str(mapa), None, "a" * 40, None, api=ApiFalsa(), forzar_versiones=True,
                              ruta_puntero=tmp_path / "p.json")
    assert res["publicado"]


def test_main_que_avanzo_deja_la_corrida_superada(mapa, tmp_path):
    class ApiRechaza(ApiFalsa):
        def create_commit(self, **kw):
            raise RuntimeError("412 Precondition Failed: parent commit is not the head")

    with pytest.raises(RuntimeError, match="parent commit"):
        publicador.publicar(str(mapa), None, "a" * 40, None, api=ApiRechaza(), forzar_versiones=True,
                            ruta_puntero=tmp_path / "p.json")
    assert not (tmp_path / "p.json").exists()                 # sin commit, el puntero no se mueve


# ── Verificación del puntero (job mapa-puntero de la CI) ─────────────────────────────────────
class _Resp:
    def __init__(self, contenido=b"", estado=200):
        self.content, self.status_code = contenido, estado


def _requests_falso(mapa, alterar=None):
    def get(url, params=None, timeout=None):
        if "/api/datasets/" in url:
            return _Resp(b"{}", 200)
        rel = url.split(f"/{RUTA_HF}/", 1)[1]
        ruta = Path(mapa) / rel
        if not ruta.exists():
            return _Resp(b"", 404)
        datos = ruta.read_bytes()
        return _Resp(datos + b"x" if rel == alterar else datos)
    return SimpleNamespace(get=get)


def _puntero_de(mapa):
    estado_bytes = (Path(mapa) / "estado.json").read_bytes()
    estado = json.loads(estado_bytes)
    return {"repo_id": "pablobenavidesj/doctrina-jurisprudencia-chile", "revision_mapa": "c" * 40,
            "sha256_estado": hashlib.sha256(estado_bytes).hexdigest(), "sha_fuente": estado["sha_fuente"]}


def test_verificar_puntero_integro(mapa, monkeypatch):
    monkeypatch.setitem(__import__("sys").modules, "requests", _requests_falso(mapa))
    assert verificacion.verificar_puntero(_puntero_de(mapa)) == []


def test_verificar_puntero_detecta_un_archivo_alterado(mapa, monkeypatch):
    estado = json.loads((mapa / "estado.json").read_text(encoding="utf-8"))
    alterado = sorted(estado["archivos"])[0]
    monkeypatch.setitem(__import__("sys").modules, "requests", _requests_falso(mapa, alterar=alterado))
    problemas = verificacion.verificar_puntero(_puntero_de(mapa))
    assert any(alterado in p for p in problemas)


def test_verificar_puntero_detecta_un_estado_que_no_calza(mapa, monkeypatch):
    monkeypatch.setitem(__import__("sys").modules, "requests", _requests_falso(mapa))
    puntero = dict(_puntero_de(mapa), sha256_estado="0" * 64)
    assert any("estado.json" in p for p in verificacion.verificar_puntero(puntero))


def test_cli_verificar_puntero_nulo_no_usa_la_red(tmp_path, monkeypatch):
    def prohibido(*a, **k):
        raise AssertionError("no debía usar la red")

    monkeypatch.setattr(verificacion, "verificar_puntero", prohibido)
    nulo = tmp_path / "puntero.json"
    nulo.write_text(json.dumps({"repo_id": "x", "revision_mapa": None}), encoding="utf-8")
    assert cli.main(["verificar-puntero", "--puntero", str(nulo)]) == 0
