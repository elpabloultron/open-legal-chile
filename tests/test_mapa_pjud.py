"""Jurisprudencia y casos con el mapa del corpus: primero el mapa, después el corpus local.

Con el mapa diminuto de `tests/conftest.py` (sin red). Sin mapa (el estado por defecto de la
suite), todo responde exactamente como antes.
"""

import case_intake
import pjud_connector
from pjud_connector import buscar_sentencias_locales

SALA_3 = "TERCERA, CONSTITUCIONAL"


def test_rol_exacto_viene_del_mapa_con_url_fijada(mapa_activo):
    res = buscar_sentencias_locales("Rol 10641-2024", limit=5)
    primero = res[0]
    assert primero["origen"] == "mapa_hf" and primero["id_mapa"] == "cs:10641-2024"
    assert primero["tribunal"] == "Corte Suprema" and primero["rol"] == "10641-2024"
    assert primero["sala"] == SALA_3 and primero["ministros"] == "MARÍA GAJARDO HARBOE"
    assert primero["link"] == primero["url_huggingface"]
    assert f"/blob/{'9' * 40}/jurisprudencia_cs/2024/03/10641-2024.md" in primero["url_huggingface"]
    assert primero["url_vigente"].endswith("/blob/main/jurisprudencia_cs/2024/03/10641-2024.md")


def test_fallos_de_una_ministra(mapa_activo):
    for consulta in ("María Gajardo Harboe", "ministra María Gajardo Harboe"):
        ids = [r["id_mapa"] for r in buscar_sentencias_locales(consulta, limit=5) if r["origen"] == "mapa_hf"]
        assert set(ids) == {"cs:10641-2024", "cs:1234-2023"}


def test_tribunal_ambiental_por_su_rol(mapa_activo):
    res = [r for r in buscar_sentencias_locales("R-21-2021 del Tercer Tribunal Ambiental", limit=3)
           if r["origen"] == "mapa_hf"]
    assert res and res[0]["id_mapa"] == "ta:3ta:r-21-2021" and res[0]["rol"] == "R-21-2021"


def test_no_repite_lo_que_el_mapa_ya_trajo(mapa_activo, monkeypatch):
    local = {"tribunal": "Corte Suprema", "sala": "Tercera Sala", "rol": "Rol N° 10.641-2024", "fecha": "2026-03-04",
             "caratula": "Pérez con Fisco", "_texto": "rol 10641-2024 perez con fisco"}
    otro = {"tribunal": "Corte Suprema", "rol": "Rol N° 777-2020", "fecha": "2020-01-01",
            "caratula": "Otra causa", "_texto": "rol 10641-2024 otra causa citada"}
    monkeypatch.setattr(pjud_connector, "_cargar_corpus_local", lambda: [local, otro])
    res = buscar_sentencias_locales("10641-2024", limit=10)
    assert [r["origen"] for r in res] == ["mapa_hf", "corpus_local"]
    assert res[1]["rol"] == "Rol N° 777-2020"


def test_tc_local_se_reconoce_por_su_documento_oficial():
    """La cabecera de los registros del TC suele ser de otra causa: la identidad sale del
    documento oficial, igual que en el mapa."""
    registro = {"tribunal": "Tribunal Constitucional", "rol": "Rol N° 16674-06a-INA",
                "link": "https://buscador-backend.tcchile.cl/api/extended/13532/download"}
    assert pjud_connector._id_canonico_registro(registro) == "tc:13532"
    assert pjud_connector._id_canonico_registro({"tribunal": "Corte Suprema", "rol": "Rol N° 45.123-2021"}) == \
        "cs:45123-2021"
    assert pjud_connector._id_canonico_registro({"tribunal": "3TA", "rol": "R-21-2021"}) == "ta:3ta:r-21-2021"


def test_sin_mapa_es_el_corpus_local_de_siempre(monkeypatch):
    registros = [{"tribunal": "Corte Suprema", "rol": "Rol N° 1-2024", "fecha": "2024-01-01",
                  "caratula": "Despido injustificado", "_texto": "despido injustificado"}]
    monkeypatch.setattr(pjud_connector, "_cargar_corpus_local", lambda: registros)
    res = buscar_sentencias_locales("despido injustificado", limit=5)
    assert res == [{"tribunal": "Corte Suprema", "rol": "Rol N° 1-2024", "fecha": "2024-01-01",
                    "caratula": "Despido injustificado", "origen": "corpus_local"}]


def test_pjud_search_pasa_los_campos_del_mapa(mapa_activo, tmp_path):
    cliente = pjud_connector.PJUDClient(db_path=str(tmp_path / "pjud.db"))
    res = [r for r in cliente.search_jurisprudencia("10641-2024", limit=5) if r.get("origen") == "mapa_hf"]
    assert res and res[0]["id_mapa"] == "cs:10641-2024" and res[0]["url_huggingface"].startswith("https://")
    assert res[0]["sala"] == SALA_3


def test_mesa_de_entrada_trae_la_ficha_del_rol(mapa_activo, monkeypatch):
    monkeypatch.setattr("case_workspace.crear_o_cargar_caso", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    analisis = case_intake.caso_analizar("Recurso de protección ante la Corte Suprema, Rol N° 10.641-2024, "
                                         "sobre la cobertura de una isapre.")
    fichas = analisis["fichas_mapa"]
    assert [f["id_mapa"] for f in fichas] == ["cs:10641-2024"]
    assert fichas[0]["url_huggingface"].startswith("https://huggingface.co/datasets/")


def test_mesa_de_entrada_ignora_un_rit_y_no_inventa_fichas(mapa_activo, monkeypatch):
    monkeypatch.setattr("case_workspace.crear_o_cargar_caso", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    analisis = case_intake.caso_analizar("Juicio laboral RIT O-1234-2023 ante el Juzgado de Letras del Trabajo.")
    assert "fichas_mapa" not in analisis


def test_mesa_de_entrada_sin_mapa_no_agrega_la_clave(monkeypatch):
    monkeypatch.setattr("case_workspace.crear_o_cargar_caso", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    analisis = case_intake.caso_analizar("Corte Suprema, Rol N° 10.641-2024.")
    assert "fichas_mapa" not in analisis


def test_espacio_del_caso_cita_con_url_fijada_y_guarda_la_revision(tmp_path, monkeypatch):
    import online_library_sync
    from case_workspace import CaseWorkspace

    url = "https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile/blob/" + "9" * 40 + \
        "/jurisprudencia_cs/2024/03/10641-2024.md"
    respuesta = {
        "resultados": [{"archivo": "jurisprudencia_cs/2024/03/10641-2024.md", "url_huggingface": url,
                        "cita_estandar": "[CS - Rol N° 10.641-2024, Fecha: 04-03-2026]"}],
        "citas": [{"formato": "[CS - Rol N° 10.641-2024, Fecha: 04-03-2026]",
                   "archivo": "jurisprudencia_cs/2024/03/10641-2024.md", "texto": "Confirma."}],
        "mapa": {"activo": True, "revision": "local", "sha_fuente": "9" * 40, "fecha_fuente": "2026-10-01"},
    }
    monkeypatch.setattr(online_library_sync, "consultar_huggingface_dataset", lambda *a, **k: respuesta)
    ws = CaseWorkspace(tmp_path / "caso")
    ws.enriquecer_con_huggingface("Rol 10641-2024")
    meta = ws.leer_metadatos()
    assert meta["fuentes_huggingface"] == [{"cita": "[CS - Rol N° 10.641-2024, Fecha: 04-03-2026]",
                                            "archivo": "jurisprudencia_cs/2024/03/10641-2024.md", "url": url}]
    assert meta["corpus_huggingface"] == {"revision": "local", "sha_fuente": "9" * 40, "fecha_fuente": "2026-10-01"}
    assert url in (tmp_path / "caso" / "markdown" / "fuentes_hf.md").read_text(encoding="utf-8")
