"""La copia local del dataset HF tiene que revalidarse contra el hub (y refrescarse a pedido).

Caso real que lo motivó: el grafo del dataset se republicó el 2026-09-28 y una instalación
que ya lo tenía cacheado seguía viendo la revisión anterior sin ningún aviso.
"""

import json
import time
from types import SimpleNamespace

import online_library_sync as ols


def _preparar(tmp_path, monkeypatch, contenido=b"linea vieja\n"):
    monkeypatch.setattr(ols, "CACHE_HF", tmp_path)
    repo_dir = tmp_path / "repo__demo"
    archivo = repo_dir / "data" / "demo.jsonl"
    archivo.parent.mkdir(parents=True)
    archivo.write_bytes(contenido)
    return repo_dir, archivo


def _meta(repo_dir, blob, verificado):
    (repo_dir / "_sincronia.json").write_text(
        json.dumps({"archivos": {"data/demo.jsonl": {"blob_id": blob, "verificado": verificado}}}),
        encoding="utf-8")


def test_cache_fresca_no_consulta_el_hub(tmp_path, monkeypatch):
    repo_dir, _ = _preparar(tmp_path, monkeypatch)
    _meta(repo_dir, "abc", time.time())  # verificación fresca

    def _prohibido(*a, **k):
        raise AssertionError("no debe consultar el hub con la metadata fresca")
    monkeypatch.setattr(ols, "_blob_remoto", _prohibido)

    texto = ols._descargar_trozo_hf("data/demo.jsonl", "repo/demo", ["vieja"])

    assert "vieja" in texto  # responde con la copia local, sin llamar a _blob_remoto


def test_blob_cambiado_redescarga(tmp_path, monkeypatch):
    repo_dir, archivo = _preparar(tmp_path, monkeypatch)
    _meta(repo_dir, "viejo", time.time() - 99_999)  # verificación vencida
    monkeypatch.setattr(ols, "_blob_remoto", lambda archivo, repo_id: "nuevo")

    def _descarga_falsa(**kwargs):
        destino = repo_dir / "data" / "demo.jsonl"
        destino.write_bytes(b"linea nueva\n")
        return str(destino)
    import huggingface_hub
    monkeypatch.setattr(huggingface_hub, "hf_hub_download", _descarga_falsa)

    texto = ols._descargar_trozo_hf("data/demo.jsonl", "repo/demo", ["nueva"])

    assert "nueva" in texto
    assert archivo.read_text(encoding="utf-8").strip() == "linea nueva"


def test_sin_red_se_usa_la_copia_y_no_se_marca_verificada(tmp_path, monkeypatch):
    repo_dir, _ = _preparar(tmp_path, monkeypatch)
    _meta(repo_dir, "x", time.time() - 99_999)
    monkeypatch.setattr(ols, "_blob_remoto", lambda archivo, repo_id: None)  # sin respuesta

    texto = ols._descargar_trozo_hf("data/demo.jsonl", "repo/demo", ["vieja"])

    assert "vieja" in texto
    guardada = json.loads((repo_dir / "_sincronia.json").read_text(encoding="utf-8"))
    assert guardada["archivos"]["data/demo.jsonl"]["verificado"] < time.time() - 99_000  # no se refrescó


def test_refrescar_baja_solo_lo_cambiado(tmp_path, monkeypatch):
    repo_dir, archivo = _preparar(tmp_path, monkeypatch)
    _meta(repo_dir, "viejo", time.time())

    class _Api:
        def get_paths_info(self, repo_id, paths, repo_type=None):
            return [SimpleNamespace(path="data/demo.jsonl", blob_id="nuevo")]

    monkeypatch.setattr(ols, "_hf_api", lambda: _Api())

    def _descarga_falsa(**kwargs):
        ruta = tmp_path / "descarga_temporal.jsonl"
        ruta.write_bytes(b"linea nueva\n")
        return str(ruta)
    import huggingface_hub
    monkeypatch.setattr(huggingface_hub, "hf_hub_download", _descarga_falsa)

    res = ols.refrescar_cache_corpus(repo_id="repo/demo")

    assert res["actualizados"] == 1
    assert "nueva" in archivo.read_text(encoding="utf-8")
    guardada = json.loads((repo_dir / "_sincronia.json").read_text(encoding="utf-8"))
    assert guardada["archivos"]["data/demo.jsonl"]["blob_id"] == "nuevo"
