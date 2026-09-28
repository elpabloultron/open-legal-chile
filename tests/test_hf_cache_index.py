"""Índice FTS5 del corpus cacheado: paridad con el escaneo y reconstrucción al cambiar la fuente."""

import json
import time

import hf_cache_index as idx


def _jsonl(tmp_path, n=5, contenidos=None):
    ruta = tmp_path / "demo.jsonl"
    contenidos = contenidos or [{"texto": f"parrafo numero {i} sin nada"} for i in range(n)]
    ruta.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in contenidos) + "\n",
                    encoding="utf-8")
    return ruta


def _legible(linea):
    return json.loads(linea).get("texto", linea)


def test_match_substring_como_el_escaneo(tmp_path, monkeypatch):
    monkeypatch.setattr(idx, "DIR_INDICES", tmp_path / "indices")
    ruta = _jsonl(tmp_path, contenidos=[
        {"texto": "El consentimiento informado del paciente"},
        {"texto": "Otra linea irrelevante"},
    ])
    lineas = idx.buscar(ruta, ["miento"], transformar=_legible)
    assert lineas == ["El consentimiento informado del paciente"], "substring interior debe calzar"


def test_sin_acentos(tmp_path, monkeypatch):
    monkeypatch.setattr(idx, "DIR_INDICES", tmp_path / "indices")
    ruta = _jsonl(tmp_path, contenidos=[{"texto": "La simulación es un vicio"}])
    assert idx.buscar(ruta, ["simulacion"], transformar=_legible)


def test_reconstruye_cuando_cambia_la_fuente(tmp_path, monkeypatch):
    monkeypatch.setattr(idx, "DIR_INDICES", tmp_path / "indices")
    ruta = _jsonl(tmp_path, contenidos=[{"texto": "vieja palabra"}])
    assert idx.buscar(ruta, ["vieja"], transformar=_legible)
    time.sleep(0.01)
    ruta.write_text(json.dumps({"texto": "nueva palabra"}, ensure_ascii=False) + "\n", encoding="utf-8")
    assert idx.buscar(ruta, ["nueva"], transformar=_legible)
    assert idx.buscar(ruta, ["vieja"], transformar=_legible) == []   # el índice viejo no sobrevive


def test_agujas_vacias_devuelve_las_primeras(tmp_path, monkeypatch):
    monkeypatch.setattr(idx, "DIR_INDICES", tmp_path / "indices")
    ruta = _jsonl(tmp_path, n=30)
    assert len(idx.buscar(ruta, [], transformar=_legible, maximo=20)) == 20


def test_indice_reutilizado_no_reindexa(tmp_path, monkeypatch):
    """La segunda consulta no puede volver a leer la fuente: ese es el punto del índice."""
    monkeypatch.setattr(idx, "DIR_INDICES", tmp_path / "indices")
    ruta = _jsonl(tmp_path, contenidos=[{"texto": "humedal urbano"}])
    llamadas = []
    original = idx.indexar

    def _cuenta(*a, **k):
        llamadas.append(1)
        return original(*a, **k)
    monkeypatch.setattr(idx, "indexar", _cuenta)

    assert idx.buscar(ruta, ["humedal"], transformar=_legible) == ["humedal urbano"]
    assert idx.buscar(ruta, ["humedal"], transformar=_legible) == ["humedal urbano"]
    assert len(llamadas) == 1, "la segunda consulta debe reutilizar el índice"
