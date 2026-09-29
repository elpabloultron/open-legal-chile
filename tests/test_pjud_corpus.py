"""El corpus local cosechado (CS/TC) se busca: 70.523 sentencias CS + 966 TC + rectores."""
import json
import pathlib

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
    monkeypatch.setattr(pjud_connector, "BASE_DIR", str(pathlib.Path(ruta).parent))
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


def test_el_tc_se_cita_con_su_texto_completo(tmp_path, monkeypatch):
    """El TC publica sus textos completos: el pasaje literal entra a la cita."""
    (tmp_path / "jurisprudencia_tc").mkdir()
    (tmp_path / "jurisprudencia_tc" / "9001-2025-INA.md").write_text(
        "Considerando: la inaplicabilidad por ruido ambiental debe acogerse, pues el debido "
        "proceso lo exige. " + "q" * 6000, encoding="utf-8")
    ruta = tmp_path / "corpus.jsonl"
    registro = {"tribunal": "Tribunal Constitucional", "sala": "Pleno", "rol": "9001-2025-INA",
                "fecha": "2025-06-01", "caratula": "Inaplicabilidad ruido",
                "archivo_md": "jurisprudencia_tc/9001-2025-INA.md"}
    ruta.write_text(json.dumps(registro, ensure_ascii=False) + "\n", encoding="utf-8")
    _parchear_corpus(monkeypatch, str(ruta))

    res = PJUDClient().search_jurisprudencia("inaplicabilidad ruido ambiental")

    entrada = next(r for r in res if r.get("rol") == "9001-2025-INA")
    assert "debe acogerse" in entrada["doctrina"]


def test_las_fichas_de_la_cs_no_se_citan_como_texto(tmp_path, monkeypatch):
    """La CS publica fichas de ~1 KB: se cita el digesto, sin inventarle texto."""
    (tmp_path / "jurisprudencia_cs" / "2025" / "07").mkdir(parents=True)
    (tmp_path / "jurisprudencia_cs" / "2025" / "07" / "3000-2025.md").write_text(
        "# Ficha\n- **Recurso:** CASACIÓN\n> Ficha de jurisprudencia: el texto se consulta en el buscador.",
        encoding="utf-8")
    ruta = tmp_path / "corpus.jsonl"
    registro = {"tribunal": "Corte Suprema", "sala": "Primera", "rol": "3000-2025", "fecha": "2025-07-03",
                "caratula": "X con Y", "recurso": "CASACIÓN", "resultado": "SE RECHAZA EL RECURSO"}
    ruta.write_text(json.dumps(registro, ensure_ascii=False) + "\n", encoding="utf-8")
    _parchear_corpus(monkeypatch, str(ruta))

    res = PJUDClient().search_jurisprudencia("casación recurso rechaza")

    entrada = next(r for r in res if r.get("rol") == "3000-2025")
    assert entrada["doctrina"] == "CASACIÓN SE RECHAZA EL RECURSO"


def test_el_pasaje_del_tc_sale_del_cuerpo_y_no_de_la_ficha(tmp_path, monkeypatch):
    """El fallo del TC viene después del primer separador: no se cita la ficha de metadata."""
    (tmp_path / "jurisprudencia_tc").mkdir()
    (tmp_path / "jurisprudencia_tc" / "8002-2025-INA.md").write_text(
        "# INA-STC — Rol N° 8002-2025-INA\n\n- **Rol:** Rol N° 8002-2025-INA\n"
        "- **Carátula:** gestión por cautelares de ruido\n\n---\n"
        "Considerando: la cautelar de ruido se acoge en el cuerpo del fallo. " + "w" * 6000,
        encoding="utf-8")
    ruta = tmp_path / "corpus.jsonl"
    registro = {"tribunal": "Tribunal Constitucional", "rol": "8002-2025-INA", "fecha": "2025-09-01",
                "caratula": "gestión por cautelares de ruido", "archivo_md": "jurisprudencia_tc/8002-2025-INA.md"}
    ruta.write_text(json.dumps(registro, ensure_ascii=False) + "\n", encoding="utf-8")
    _parchear_corpus(monkeypatch, str(ruta))

    res = PJUDClient().search_jurisprudencia("cautelares ruido cuerpo")

    entrada = next(r for r in res if r.get("rol") == "8002-2025-INA")
    assert "cuerpo del fallo" in entrada["doctrina"]
    assert "**Rol:**" not in entrada["doctrina"]
