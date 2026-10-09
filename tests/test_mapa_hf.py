"""El mapa del corpus dentro de las herramientas de Hugging Face y del corpus («consultar siempre»).

Con el mapa activo (fixture `mapa_activo`: un mapa diminuto en `tmp_path`, sin red), la búsqueda
en el dataset resuelve primero lo exacto (rol, norma, entidad) y cita con la URL fijada a la
revisión de la fuente; el listado, el blob y la revisión que se baja salen del mapa. Con el mapa
apagado (lo normal en la suite), todo responde como antes. Nada de esto toca la red: el hub queda
prohibido y se cuentan las llamadas, sin medir milisegundos.
"""

import hashlib
import json

import networkx as nx
import pytest

import online_library_sync as ols
from conftest import FILAS_MAPA_MINIMO

SHA_FUENTE = "9" * 40  # la fuente que declara el estado.json del mapa diminuto
REPO = "pablobenavidesj/doctrina-jurisprudencia-chile"
RUTA_CS = "jurisprudencia_cs/2024/03/10641-2024.md"
RUTA_TA = "jurisprudencia_ambiental/3TA/R-21-2021.md"


@pytest.fixture(autouse=True)
def red_prohibida(tmp_path, monkeypatch):
    """La caché del corpus va a `tmp_path` y cualquier llamada al hub queda registrada y falla."""
    import huggingface_hub

    llamadas = []

    def _hub(nombre):
        def _prohibido(*a, **k):
            llamadas.append(nombre)
            raise AssertionError(f"la prueba no puede llamar al hub ({nombre})")
        return _prohibido

    monkeypatch.setattr(ols, "CACHE_HF", tmp_path / "hf_cache")
    monkeypatch.setattr(ols, "_ARCHIVOS_HF_CACHE", {})
    monkeypatch.setattr(huggingface_hub, "hf_hub_download", _hub("hf_hub_download"))
    monkeypatch.setattr(huggingface_hub, "HfApi", _hub("HfApi"))
    monkeypatch.setattr(ols, "_hf_api", _hub("_hf_api"))
    return llamadas


def _activar(monkeypatch, tmp_path, destino):
    """Enciende el cliente compartido sobre un mapa armado a medida (como `mapa_activo`)."""
    from mapa_corpus import cliente

    monkeypatch.setenv("OPENLEGAL_MAPA", "")
    monkeypatch.setenv("OPENLEGAL_MAPA_LOCAL", str(destino))
    monkeypatch.setenv("OPENLEGAL_MAPA_DIR", str(tmp_path / "cache_mapa_propio"))
    cliente.reiniciar_cliente()
    c = cliente.obtener_cliente()
    assert c.asegurar(bloquear=True, timeout=120), c.error
    return c


@pytest.fixture
def sin_cliente_al_salir():
    """Con `_activar`: al terminar, el próximo cliente vuelve a leer el entorno (mapa apagado)."""
    yield
    from mapa_corpus import cliente
    cliente.reiniciar_cliente()


# ── online_library_sync: listado, blob y descarga desde el mapa ──────────────────────────────────

def test_listado_y_blob_salen_del_mapa_sin_el_hub(mapa_activo, red_prohibida):
    archivos = ols._listar_archivos_hf(REPO)

    assert archivos == sorted(f["ruta"] for f in FILAS_MAPA_MINIMO)
    assert ols._blob_remoto(RUTA_CS, REPO) == "b" * 40
    assert red_prohibida == []


def test_sin_mapa_el_listado_es_el_de_siempre(monkeypatch, red_prohibida):
    """Mapa apagado: el listado vuelve a ser el del hub (aquí, prohibido → el error de siempre)."""
    assert ols.cliente_mapa(REPO) is None
    with pytest.raises(AssertionError):
        ols._listar_archivos_hf(REPO)
    assert red_prohibida == ["HfApi"]


def test_descarga_fijada_a_la_revision_de_la_fuente(mapa_activo, monkeypatch, tmp_path):
    import huggingface_hub

    pedidas = []

    def _descarga(**kwargs):
        pedidas.append(kwargs)
        origen = tmp_path / "bajado.md"
        origen.write_text("Vistos: la reclamación contra la SMA se acoge.", encoding="utf-8")
        return str(origen)
    monkeypatch.setattr(huggingface_hub, "hf_hub_download", _descarga)

    primero = ols._descargar_trozo_hf(RUTA_TA, REPO, ["reclamacion"])
    segundo = ols._descargar_trozo_hf(RUTA_TA, REPO, ["reclamacion"])

    assert "reclamación" in primero and segundo == primero
    assert len(pedidas) == 1, "la copia con el blob del mapa no se vuelve a bajar"
    assert pedidas[0]["revision"] == SHA_FUENTE
    assert pedidas[0]["filename"] == RUTA_TA


def test_copia_con_otro_blob_se_rebaja_fijada(mapa_activo, monkeypatch, tmp_path):
    import huggingface_hub

    pedidas = []

    def _descarga(**kwargs):
        pedidas.append(kwargs["revision"])
        origen = tmp_path / "bajado.md"
        origen.write_text("texto nuevo de la sentencia", encoding="utf-8")
        return str(origen)
    monkeypatch.setattr(huggingface_hub, "hf_hub_download", _descarga)
    repo_dir = ols._repo_cache_dir(REPO)
    copia = repo_dir / RUTA_TA
    copia.parent.mkdir(parents=True)
    copia.write_text("texto viejo de la sentencia", encoding="utf-8")
    (repo_dir / "_sincronia.json").write_text(
        json.dumps({"archivos": {RUTA_TA: {"blob_id": "blob-viejo", "verificado": 0}}}), encoding="utf-8")

    texto = ols._descargar_trozo_hf(RUTA_TA, REPO, ["sentencia"])

    assert "nuevo" in texto
    assert pedidas == [SHA_FUENTE]
    guardada = json.loads((repo_dir / "_sincronia.json").read_text(encoding="utf-8"))
    assert guardada["archivos"][RUTA_TA]["blob_id"] == "e" * 40


def test_copia_sin_registro_vale_si_su_blob_git_calza(fabrica_mapa, monkeypatch, tmp_path, red_prohibida,
                                                       sin_cliente_al_salir):
    contenido = "Vistos: se rechaza la reclamación.".encode("utf-8")
    blob = hashlib.sha1(b"blob %d\0" % len(contenido) + contenido, usedforsecurity=False).hexdigest()
    filas = [dict(f, blob=blob) if f["ruta"] == RUTA_TA else f for f in FILAS_MAPA_MINIMO]
    _activar(monkeypatch, tmp_path, fabrica_mapa(filas, destino=tmp_path / "mapa_blob"))
    copia = ols._repo_cache_dir(REPO) / RUTA_TA
    copia.parent.mkdir(parents=True)
    copia.write_bytes(contenido)

    assert "rechaza" in ols._descargar_trozo_hf(RUTA_TA, REPO, ["reclamacion"])
    assert red_prohibida == []


# ── consultar_huggingface_dataset ────────────────────────────────────────────────────────────────

def test_rol_exacto_con_url_fijada(mapa_activo, red_prohibida):
    res = ols.consultar_huggingface_dataset("10641-2024", limit=5)

    primero = res["resultados"][0]
    assert primero["archivo"] == RUTA_CS
    assert primero["relacion"] == "exacto" and primero["origen"] == "mapa_hf"
    assert f"/blob/{SHA_FUENTE}/{RUTA_CS}" in primero["url_huggingface"]
    assert primero["url_vigente"].endswith(f"/blob/main/{RUTA_CS}")
    assert primero["cita_oficial"] == "[CS - Rol N° 10.641-2024, Fecha: 04-03-2026]"
    assert "PÉREZ CON FISCO DE CHILE" in primero["extractos"][0]
    # Quién cita el rol: la sentencia del TC que lo menciona.
    assert [r["archivo"] for r in res["resultados"][1:]] == ["jurisprudencia_tc/2402-12-INA.md"]
    assert res["citas"][0]["url"] == primero["url_huggingface"]
    assert res["mapa"]["activo"] is True and res["mapa"]["sha_fuente"] == SHA_FUENTE
    assert res["mapa_consulta"]["ids"] == ["cs:10641-2024"]
    assert red_prohibida == []


def test_parametro_rol_sin_consulta(mapa_activo):
    res = ols.consultar_huggingface_dataset("", rol="Rol N° 10.641-2024", limit=1)

    assert [r["archivo"] for r in res["resultados"]] == [RUTA_CS]
    assert res["query"] == "Rol N° 10.641-2024"


def test_rol_ambiental_por_alias(mapa_activo):
    """La causa acumulada R-35-2021 vive en la ficha de la R-21-2021 (alias del mapa)."""
    res = ols.consultar_huggingface_dataset("", rol="R-35-2021", limit=1)

    assert res["resultados"][0]["archivo"] == RUTA_TA
    assert res["resultados"][0]["id"] == "ta:3ta:r-21-2021"


def test_norma_trae_quien_la_cita(mapa_activo, red_prohibida):
    res = ols.consultar_huggingface_dataset("", norma="art. 2314 del Código Civil", limit=5)

    assert [r["id"] for r in res["resultados"]] == ["tc:2402", "doc:revistas/rchd/2020/responsabilidad"]
    assert {r["relacion"] for r in res["resultados"]} == {"cita"}
    assert res["mapa_consulta"] == {"ids": ["norma:cc:2314"], "citantes_total": 2, "colecciones": []}
    assert all(SHA_FUENTE in r["url_huggingface"] for r in res["resultados"])
    assert red_prohibida == []


def test_coleccion_acota_la_norma_y_el_texto(mapa_activo, red_prohibida):
    por_norma = ols.consultar_huggingface_dataset("", norma="art. 2314 del Código Civil", coleccion="doctrina")
    por_texto = ols.consultar_huggingface_dataset("responsabilidad extracontractual", coleccion="tc")

    assert [r["id"] for r in por_norma["resultados"]] == ["doc:revistas/rchd/2020/responsabilidad"]
    assert por_norma["mapa_consulta"]["citantes_total"] == 1
    assert [r["id"] for r in por_texto["resultados"]] == ["tc:2402"]
    assert por_texto["resultados"][0]["relacion"] == "texto"
    assert red_prohibida == [], "lo que cae fuera de la colección ni se busca ni se baja"


def test_entidad_por_nombre(mapa_activo):
    res = ols.consultar_huggingface_dataset("", entidad="Ministra María Gajardo Harboe", limit=5)

    assert {r["id"] for r in res["resultados"]} == {"cs:10641-2024", "cs:1234-2023"}
    assert res["mapa_consulta"]["ids"] == ["ministro:maria-gajardo-harboe"]


def test_rol_que_no_esta_no_se_inventa(mapa_activo, red_prohibida):
    res = ols.consultar_huggingface_dataset("Rol 99999-2020", limit=5)

    assert res["resultados"] == [] and res["citas"] == []
    assert res["mapa_consulta"]["ids"] == ["cs:99999-2020"]
    assert red_prohibida == []


def test_sin_mapa_la_respuesta_es_la_de_siempre(monkeypatch):
    """Mapa apagado: mismas claves, mismas URLs de `main`, sin campos del mapa en los resultados;
    solo se suma `mapa` con `activo: false`."""
    monkeypatch.setattr(ols, "_listar_archivos_hf", lambda repo_id: ["doctrina/civil/simulacion.md", "data/x.jsonl"])
    monkeypatch.setattr(ols, "_descargar_trozo_hf",
                        lambda f, repo_id, tokens=None: "La simulación absoluta es un acto aparente." if f.endswith(".md") else "")

    res = ols.consultar_huggingface_dataset("simulación absoluta", limit=3)

    assert set(res) == {"dataset_origen", "space_interactivo", "query", "total_coincidencias", "resultados",
                        "citas", "cita_fuente", "mapa"}
    assert res["mapa"]["activo"] is False
    assert res["resultados"] == [{
        "archivo": "doctrina/civil/simulacion.md",
        "dataset": REPO,
        "url_huggingface": f"https://huggingface.co/datasets/{REPO}/blob/main/doctrina/civil/simulacion.md",
        "space_interactivo": "https://huggingface.co/spaces/pablobenavidesj/open-legal-chile-graph",
        "tipo": "doctrina_markdown",
        "cita_estandar": f"[Hugging Face - {REPO}, Archivo: doctrina/civil/simulacion.md]",
        "extractos": ["La simulación absoluta es un acto aparente."],
        "tiene_texto": True,
    }]
    assert res["citas"] == [{"formato": f"[Hugging Face - {REPO}, Archivo: doctrina/civil/simulacion.md]",
                             "texto": "La simulación absoluta es un acto aparente.",
                             "url": res["resultados"][0]["url_huggingface"], "fuente": "huggingface"}]


def test_catalogo_de_jurisprudencia_toma_la_ruta_del_mapa(mapa_activo, monkeypatch):
    sentencias = [{"tribunal": "Corte Suprema", "rol": "10641-2024", "fecha": "2026-03-04", "caratula": "PÉREZ",
                   "archivo_fuente": "data/jurisprudencia/cs_sentencias.jsonl"},
                  {"tribunal": "Corte Suprema", "rol": "777-2025", "fecha": "2025-01-02", "caratula": "SOTO",
                   "archivo_fuente": "data/jurisprudencia/cs_sentencias.jsonl"}]
    monkeypatch.setattr("pjud_connector.buscar_sentencias_locales", lambda q, limit=10: sentencias)

    res = ols._buscar_catalogo_jurisprudencia("rol", archivos=set(ols._listar_archivos_hf(REPO)))

    assert res[0]["archivo"] == RUTA_CS
    assert SHA_FUENTE in res[0]["url_huggingface"] and res[0]["url_vigente"].endswith(RUTA_CS)
    # El 777-2025 no está en el mapa: se cita el JSONL donde vive el registro, nunca una ruta armada.
    assert res[1]["archivo"] == "data/jurisprudencia/cs_sentencias.jsonl"
    assert "/blob/main/" in res[1]["url_huggingface"] and "url_vigente" not in res[1]


# ── servidor/corpus.py ───────────────────────────────────────────────────────────────────────────

@pytest.fixture
def servidor(monkeypatch):
    """mcp_server con los sondeos de red de consulta_maestra sustituidos (HF va de verdad)."""
    import mcp_server

    monkeypatch.setattr(mcp_server, "_doctrina_para_consulta", lambda q, lim=3: {"resultados": [], "citas": []})
    monkeypatch.setattr(mcp_server, "_normas_para_consulta", lambda q: [])
    monkeypatch.setattr(mcp_server, "_subgrafo_para_consulta", lambda q, hops=1: {})
    monkeypatch.setattr(mcp_server, "_organismos_para_consulta",
                        lambda q, lim=3: {"organismos": [], "resultados": {}, "citas": []})
    avances = []
    monkeypatch.setattr(mcp_server, "enviar_progreso", lambda mensaje, avance=0, total=None: avances.append(avance))
    monkeypatch.setattr(mcp_server, "avances_de_prueba", avances, raising=False)
    return mcp_server


def test_consulta_maestra_con_clave_mapa(mapa_activo, servidor, red_prohibida):
    res = servidor.handle_tool_call("consulta_maestra", {"consulta": "Rol 10641-2024"})

    assert res["mapa"]["activo"] is True and res["mapa"]["sha_fuente"] == SHA_FUENTE
    assert "avisos" not in res
    hf = res["hallazgos"]["huggingface"]
    assert hf[0]["archivo"] == RUTA_CS and SHA_FUENTE in hf[0]["url_huggingface"]
    assert "huggingface" not in res["faltantes"]
    assert sorted(servidor.avances_de_prueba) == [0, 1, 2, 3, 4, 5], "los 5 sondeos y sus avances"
    assert red_prohibida == []


def test_consulta_maestra_sin_mapa_avisa(servidor, monkeypatch):
    """`hf` puede no traer `mapa` (falló o es otra implementación): se lee aparte. Hay aviso solo si
    hay un mapa publicado que todavía no se descarga; apagado o sin publicar, nada que avisar."""
    from mapa_corpus import cliente as mod_cliente
    monkeypatch.setattr(servidor, "_hf_para_consulta", lambda q, lim=3: {"resultados": [], "citas": []})

    res = servidor.handle_tool_call("consulta_maestra", {"consulta": "simulación"})          # apagado
    assert res["mapa"]["activo"] is False and "avisos" not in res
    assert sorted(servidor.avances_de_prueba) == [0, 1, 2, 3, 4, 5]

    monkeypatch.setenv("OPENLEGAL_MAPA", "")
    try:
        monkeypatch.setattr(mod_cliente, "leer_puntero", lambda *a, **k: {"revision_mapa": None})
        mod_cliente.reiniciar_cliente()
        res = servidor.handle_tool_call("consulta_maestra", {"consulta": "simulación"})      # sin publicar
        assert res["mapa"]["publicado"] is False and "avisos" not in res

        monkeypatch.setattr(mod_cliente, "leer_puntero",
                            lambda *a, **k: {"revision_mapa": "1" * 40, "sha256_estado": "2" * 64})
        mod_cliente.reiniciar_cliente()
        res = servidor.handle_tool_call("consulta_maestra", {"consulta": "simulación"})      # publicado
        assert len(res["avisos"]) == 1 and "suite_instalar" in res["avisos"][0]
    finally:
        mod_cliente.reiniciar_cliente()


def test_huggingface_search_dataset_pasa_los_parametros(mapa_activo, servidor):
    res = servidor.handle_tool_call("huggingface_search_dataset",
                                    {"rol": "10641-2024", "coleccion": "cs", "limit": 3})

    assert [r["archivo"] for r in res["resultados"]] == [RUTA_CS]
    assert res["mapa_consulta"]["colecciones"] == ["cs"]
    assert "error" in servidor.handle_tool_call("huggingface_search_dataset", {"coleccion": "cs"})


def test_esquema_huggingface_search_dataset():
    import mcp_server

    esquema = next(t["inputSchema"] for t in mcp_server.TOOLS if t["name"] == "huggingface_search_dataset")
    assert {"rol", "norma", "coleccion", "entidad"} <= set(esquema["properties"])
    assert all(esquema["properties"][p]["type"] == "string" for p in ("rol", "norma", "coleccion", "entidad"))
    assert esquema["required"] == ["query"]


def _doctrina_local(n):
    return [{"id": i, "institucion": f"Institución {i}", "definicion": f"Definición {i}.", "snippet": "",
             "concordancias": "", "fallo_rector": "", "area": "Civil", "autor": "Ramos Pazos", "obra": "Tomo I",
             "operativa_procesal": "", "bm25_score": -1.0,
             "cita_oficial": f"[Doctrina - Ramos Pazos, Tomo I, Institución: Institución {i}]",
             "fuente_huggingface": f"https://huggingface.co/datasets/{REPO}"} for i in range(n)]


def test_doctrina_search_con_revista_del_mapa(mapa_activo, servidor, monkeypatch):
    monkeypatch.setattr(servidor, "search_doctrina", lambda query, area=None, autor=None, limit=5: _doctrina_local(5))

    items = servidor.handle_tool_call("doctrina_search", {"query": "responsabilidad extracontractual", "limit": 5})["resultados"]

    assert len(items) == 5
    assert [it.get("origen") for it in items] == [None, None, None, None, "mapa_hf"], "un tercio de los cupos"
    revista = items[-1]
    # El esquema que exige tests/test_mcp_e2e_live.py, con la fuente FIJADA a la revisión.
    assert "cita_oficial" in revista and "fuente_huggingface" in revista
    assert revista["cita_oficial"] == "Barros Bourie, Enrique (2020). Revista Chilena de Derecho, 47(1)."
    assert f"/blob/{SHA_FUENTE}/doctrina/revistas/rchd/2020/responsabilidad.md" in revista["fuente_huggingface"]
    assert revista["definicion"] == "Estudio sobre el artículo 2314 del Código Civil y el daño moral."
    assert revista["autor"] == "Enrique Barros Bourie"
    assert revista["concordancias"] == "Código Civil, Art. 2314"


def test_doctrina_search_llena_los_cupos_libres(mapa_activo, servidor, monkeypatch):
    monkeypatch.setattr(servidor, "search_doctrina", lambda query, area=None, autor=None, limit=5: _doctrina_local(1))

    items = servidor.handle_tool_call("doctrina_search", {"query": "responsabilidad", "limit": 5})["resultados"]

    assert [it.get("origen") for it in items] == [None, "mapa_hf"]
    assert items[1]["citas"][0]["url"].startswith("https://huggingface.co/datasets/")


def test_doctrina_search_sin_mapa_no_cambia(servidor, monkeypatch):
    locales = _doctrina_local(2)
    monkeypatch.setattr(servidor, "search_doctrina", lambda query, area=None, autor=None, limit=5: locales)

    items = servidor.handle_tool_call("doctrina_search", {"query": "responsabilidad", "limit": 5})["resultados"]

    assert [it["id"] for it in items] == [0, 1] and all("origen" not in it for it in items)


class _MotorFalso:
    """Un motor de grafo con una estrella de 40 vecinos (v00…v39, cada vNN con NN hojas propias:
    los de número alto son los más conectados), para ver que se use el compartido."""

    def __init__(self):
        self.is_built = True
        self.graph = nx.DiGraph()
        for i in range(40):
            self.graph.add_edge("centro", f"v{i:02d}")
            for k in range(i):
                self.graph.add_edge(f"v{i:02d}", f"hoja_{i:02d}_{k:02d}")

    def cargar_grafo_json(self):  # pragma: no cover — ya está cargado
        raise AssertionError("el motor compartido ya está cargado: no se relee el grafo")

    def _buscar_nodo_relevante(self, consulta):
        return "centro" if consulta == "centro" else None


def test_grafo_ver_corpus_usa_el_motor_compartido_y_acota_la_consulta(servidor, monkeypatch, tmp_path):
    import grafo_vista
    import legal_graphify

    monkeypatch.setattr(servidor, "legal_graphify_engine", _MotorFalso())
    monkeypatch.setattr(grafo_vista, "SALIDA_POR_DEFECTO", str(tmp_path))
    monkeypatch.setattr(legal_graphify, "LegalGraphifyEngine",
                        lambda *a, **k: pytest.fail("no se arma un motor nuevo: se usa el compartido"))

    acotado = servidor.handle_tool_call("grafo_ver_corpus", {"consulta": "centro", "max_nodos": 10})
    completo = servidor.handle_tool_call("grafo_ver_corpus", {"consulta": "centro"})
    nada = servidor.handle_tool_call("grafo_ver_corpus", {"consulta": "otra cosa"})

    assert acotado["nodos"] == 10 and acotado["muestra"] is True
    assert (tmp_path / "corpus.html").is_file()
    assert completo["nodos"] == 41 and completo["muestra"] is False
    assert "error" in nada


def test_grafo_ver_corpus_elige_los_vecinos_mas_conectados(servidor, monkeypatch, tmp_path):
    from servidor import corpus

    motor = _MotorFalso()
    salida = tmp_path / "vista.html"

    res = corpus._ver_corpus(motor, "centro", max_nodos=4, salida=str(salida))

    contenido = salida.read_text(encoding="utf-8")
    assert res["nodos"] == 4
    assert all(f"v{i}" in contenido for i in ("39", "38", "37"))
    assert "v00" not in contenido and "hoja_" not in contenido
    assert motor.graph.number_of_nodes() == 41 + sum(range(40)), "el grafo compartido no se modifica"


def test_rol_en_formato_oficial_sin_ruido(fabrica_mapa, monkeypatch, tmp_path, sin_cliente_al_salir, red_prohibida):
    """«Rol N° 10.641-2024»: la ficha exacta y quién la cita; no otros fallos de 2024 por texto."""
    ruido = [{"id": f"cs:{100 + i}-2024", "col": "cs", "ruta": f"jurisprudencia_cs/2024/04/{100 + i}-2024.md",
              "blob": f"{i:040d}", "bytes": 700, "fecha": "2024-04-01", "era": 2024, "rol": f"{100 + i}-2024",
              "titulo": f"CAUSA {i} CON FISCO", "sala": "sala:cs-3"} for i in range(30)]
    _activar(monkeypatch, tmp_path, fabrica_mapa(filas=FILAS_MAPA_MINIMO + ruido, destino=tmp_path / "ruido"))
    for consulta in ("Rol N° 10.641-2024", "rol n° 10641-2024"):
        res = ols.consultar_huggingface_dataset(consulta, limit=5)
        assert [r["archivo"] for r in res["resultados"]] == [RUTA_CS, "jurisprudencia_tc/2402-12-INA.md"]
        assert res["mapa_consulta"]["ids"] == ["cs:10641-2024"]
    assert red_prohibida == []
