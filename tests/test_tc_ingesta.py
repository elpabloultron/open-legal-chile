"""Ingesta del Tribunal Constitucional: el documento oficial se pide por número de rol.

La cosecha anterior armaba el enlace con el id de la ficha (`extended/<id>`), que trae la causa
cuyo rol es ese número: las 965 sentencias del dataset quedaron con la cabecera de una causa y el
texto de otra. Sin red: la API, el PDF y Hugging Face se simulan.
"""

import pathlib
from types import SimpleNamespace

from scripts import cosechar_jurisprudencia_2anios as cosecha
from scripts import subir_tc_hf
from scripts import tc_pdfs_a_md as tc

FX = pathlib.Path(__file__).parent / "fixtures" / "mapa" / "delta"
FICHA_API = {"id": "13336", "codigo": "06a-INA", "folio": "15686", "fecha_sentencia": "2025-06-12 00:00:00",
             "template": {"nombre": "INA-STC"}, "detalle": []}


def test_la_ficha_apunta_al_documento_de_su_rol():
    reg = cosecha.tc_compacto(FICHA_API)
    assert reg["rol"] == "Rol N° 15686-06a-INA"
    assert reg["link_pdf"] == "https://buscador-backend.tcchile.cl/api/extended/15686/download"
    assert reg["ficha_id"] == "13336" and reg["folio"] == "15686"


def test_los_registros_viejos_rehacen_el_enlace_desde_el_rol():
    viejo = {"rol": "Rol N° 15686-06a-INA", "link_pdf": "https://buscador-backend.tcchile.cl/api/extended/13336/download"}
    assert tc.link_oficial(viejo).endswith("/extended/15686/download")


def test_el_documento_tiene_que_nombrar_su_rol():
    assert tc.corresponde("Sentencia\nRol 15.686-24 INA\nSantiago", 15686)
    assert tc.corresponde("Sentencia Rol 15.738-2024 EN EL PROCESO ROL N° 12-2024", 15738)
    assert tc.corresponde("Rol N° 15686-24-INA", 15686)
    assert not tc.corresponde("Comunica Resolución Rol N° 13.336-22-INA", 15686)   # el error de antes
    assert not tc.corresponde("Rol 115.686-24", 15686)
    assert not tc.corresponde("Rol 15.686-24", 0)


def test_un_pdf_de_otra_causa_no_se_escribe(tmp_path, monkeypatch):
    monkeypatch.setattr(tc, "DIR_MD", tmp_path)
    monkeypatch.setattr(tc, "DIR_PDF", tmp_path / "pdf")
    (tmp_path / "pdf").mkdir()
    pedidos = []

    def get(url, headers=None, timeout=None):
        pedidos.append(url)
        return SimpleNamespace(content=b"%PDF-1.4 falso", raise_for_status=lambda: None)

    monkeypatch.setattr(tc.requests, "get", get)
    monkeypatch.setattr(tc, "texto_completo", lambda pdf: ("Comunica Resolución Rol N° 13.336-22-INA. " * 20, "pdftotext"))
    reg = {"rol": "Rol N° 15686-06a-INA", "link_pdf": "https://buscador-backend.tcchile.cl/api/extended/13336/download"}
    _, estado = tc.procesar((0, reg))
    assert estado.startswith("error|15686-06a-INA|") and "no es de la causa" in estado
    assert pedidos == ["https://buscador-backend.tcchile.cl/api/extended/15686/download"]
    assert not (tmp_path / "15686-06a-INA.md").exists() and not (tmp_path / "pdf" / "15686-06a-INA.pdf").exists()

    monkeypatch.setattr(tc, "texto_completo", lambda pdf: ("Sentencia Rol 15.686-24 INA. VISTOS: " * 20, "pdftotext"))
    _, estado = tc.procesar((0, reg))
    assert estado.startswith("ok|15686-06a-INA|")
    md = (tmp_path / "15686-06a-INA.md").read_text(encoding="utf-8")
    assert "extended/15686/download" in md and "extended/13336" not in md


def test_solo_se_suben_las_sentencias_con_cabecera_y_texto_de_la_misma_causa(tmp_path):
    (tmp_path / "README.md").write_text("# TC\n", encoding="utf-8")
    # El archivo de la cosecha anterior: cabecera de una causa, texto de otra → no se sube.
    (tmp_path / "15907-06a-INA.md").write_bytes((FX / "tc_15907-06a-INA.md").read_bytes())
    (tmp_path / "15686-06a-INA.md").write_text(
        "# INA-STC — Rol N° 15686-06a-INA\n\n- **Tribunal:** Tribunal Constitucional de Chile\n"
        "- **Rol:** Rol N° 15686-06a-INA\n- **Fecha:** 2025-06-12\n"
        "- **Documento oficial:** https://buscador-backend.tcchile.cl/api/extended/15686/download\n\n---\n\n"
        "Sentencia\nRol 15.686-24 INA\n\nVISTOS: … CONSIDERANDO: …\n", encoding="utf-8")
    revision = subir_tc_hf.revisar(tmp_path)
    assert revision == {"validos": ["15686-06a-INA.md"], "rechazados": ["15907-06a-INA.md"]}

    llamadas = []

    class Api:
        def upload_folder(self, **kw):
            llamadas.append(kw)
            return SimpleNamespace(oid="c" * 40)

    res = subir_tc_hf.subir(tmp_path, "hf_x", api=Api())
    assert res["subido"] and res["commit"] == "c" * 40 and res["rechazados"] == ["15907-06a-INA.md"]
    assert llamadas[0]["allow_patterns"] == ["15686-06a-INA.md"] and llamadas[0]["path_in_repo"] == "jurisprudencia_tc"
    assert llamadas[0]["delete_patterns"] == ["testrol*"] and llamadas[0]["repo_type"] == "dataset"
    assert subir_tc_hf.subir(tmp_path, None, dry_run=True)["subido"] is False


def test_la_ampliacion_recorre_todo_el_rango_pedido(tmp_path, monkeypatch):
    # Antes había un tope de 1 200 días: desde 2021 la cosecha se cortaba en 2023 sin avisar.
    monkeypatch.setattr(cosecha, "DATA_DIR", tmp_path)
    monkeypatch.setattr(cosecha, "PAUSA", 0)
    monkeypatch.setattr(cosecha.time, "sleep", lambda s: None)
    dias = []

    def por_dia(fecha, page, s):
        dias.append(fecha)
        if fecha != "2021-01-04":
            return {"data": [], "meta": {"total": 0, "per_page": 5}}
        return {"data": [dict(FICHA_API, folio="9876", fecha_sentencia="2021-01-04 00:00:00")],
                "meta": {"total": 1, "per_page": 5}}

    monkeypatch.setattr(cosecha, "tc_por_dia", por_dia)
    salida = cosecha.cosechar_tc("2021-01-01", hasta="2024-12-31")
    assert len(dias) == 1461 and dias[0] == "2024-12-31" and dias[-1] == "2021-01-01"
    filas = salida.read_text(encoding="utf-8").splitlines()
    assert len(filas) == 1 and "extended/9876/download" in filas[0]
