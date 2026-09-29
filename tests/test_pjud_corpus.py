"""El corpus local cosechado (CS/TC) se busca: 70.523 sentencias CS + 966 TC + rectores."""
import json

import pjud_connector
from pjud_connector import PJUDClient, buscar_sentencias_locales


def _corpus_de_prueba(tmp_path):
    registros = [
        {"tribunal": "Corte Suprema", "sala": "Tercera Sala (Constitucional)", "rol": "7001-2025",
         "fecha": "2025-05-02", "caratula": "MINERA LOS OLORES CON SMA", "recurso": "RECLAMACIÓN",
         "resultado": "ACOGE RECLAMACIÓN Y ORDENA MEDIDAS CAUTELARES", "link_detalle": "https://juris.pjud.cl/x"},
        {"tribunal": "Tribunal Constitucional", "sala": "Pleno", "rol": "9001-2025-INA",
         "fecha": "2025-06-01", "tipo": "INA-STC", "caratula": "Inaplicabilidad ruido",
         "detalle": {"Gestión pendiente": "Juzgado de Policía Local", "Resultado": "Se acoge la inaplicabilidad por ruido ambiental"},
         "link_pdf": "https://tc.cl/y"},
    ]
    ruta = tmp_path / "corpus.jsonl"
    with open(ruta, "w", encoding="utf-8") as archivo:
        for registro in registros:
            archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return str(ruta)


def _parchear_corpus(monkeypatch, ruta):
    monkeypatch.setattr(pjud_connector, "_rutas_corpus_local", lambda: [ruta])
    pjud_connector._CORPUS_CACHE["clave"] = None


def test_buscar_sentencias_locales_cita_los_metadatos(tmp_path, monkeypatch):
    _parchear_corpus(monkeypatch, _corpus_de_prueba(tmp_path))

    res = buscar_sentencias_locales("reclamación medidas cautelares minera")

    assert res and res[0]["rol"] == "7001-2025"
    assert "MEDIDAS CAUTELARES" in res[0]["resultado"]
    assert res[0]["origen"] == "corpus_local"


def test_buscar_sentencias_locales_insensible_a_acentos(tmp_path, monkeypatch):
    _parchear_corpus(monkeypatch, _corpus_de_prueba(tmp_path))

    res = buscar_sentencias_locales("ruido ambiental")

    assert any(r["tribunal"] == "Tribunal Constitucional" for r in res)
    assert any("inaplicabilidad" in (r.get("detalle") or {}).get("Resultado", "").lower() for r in res)


def test_buscar_sentencias_locales_sin_corpus_no_rompe(tmp_path, monkeypatch):
    _parchear_corpus(monkeypatch, str(tmp_path / "no_existe.jsonl"))

    assert buscar_sentencias_locales("cualquier cosa") == []


def test_search_jurisprudencia_incluye_el_corpus_local(tmp_path, monkeypatch):
    _parchear_corpus(monkeypatch, _corpus_de_prueba(tmp_path))

    res = PJUDClient().search_jurisprudencia("minera olores cautelares")

    assert any(r.get("rol") == "7001-2025" for r in res)
    encontrado = next(r for r in res if r.get("rol") == "7001-2025")
    assert encontrado["origen"] == "corpus_local"
    assert encontrado["doctrina"] == "RECLAMACIÓN ACOGE RECLAMACIÓN Y ORDENA MEDIDAS CAUTELARES"


def test_search_jurisprudencia_conserva_los_fallos_rectores():
    res = PJUDClient().search_jurisprudencia("confianza legitima")

    assert res and "Corte Suprema" in res[0]["tribunal"]
    assert "Rol N° 23.456-2022" in res[0]["rol"]
