"""
Conector de la CGR sin red: los cuatro defectos del issue #1 y lo que encontró la revisión del PR #2.

Las respuestas son registros reales de la API de la Contraloría (2026-10), recortados y sin datos
personales (`tests/fixtures/cgr/respuestas_api.json`). Un `safe_urlopen` falso las entrega según la
consulta —con el filtro por año y la paginación de la API— y registra cada petición.

1. La API cuenta las páginas desde 0: con `page=1` una consulta acotada traía `total` > 0 y nada.
2. `get_dictamen` devolvía el primer resultado: pedir E311060N23 entregaba 0E6541N25.
3. El identificador citable es `doc_id` («E311060N23»), no `numeric_doc_id` («E311060»; «I» en
   todos los instructivos); en auditorías es `número` («622/2026»).
4. El texto íntegro viaja en `documento_completo`; el conector leía campos que no existen.
"""

import copy
import io
import json
import pathlib

import pytest

import cgr_connector
from cgr_connector import CGRClient

RESPUESTAS = json.loads((pathlib.Path(__file__).parent / "fixtures" / "cgr" / "respuestas_api.json")
                        .read_text(encoding="utf-8"))


def _hit(doc_id, anio, materia="Materia de prueba", texto="Texto del dictamen."):
    """Un registro sintético con la forma de los reales (para paginar sin inflar los fixtures)."""
    numero = doc_id[:-3]
    return {"_id": doc_id, "_source": {
        "_tipo": "dictamenes", "doc_id": doc_id, "numeric_doc_id": numero, "n_dictamen": numero.lstrip("0"),
        "year_doc_id": anio, "fecha_documento": f"{anio}-06-01T00:00:00+00:00", "materia": materia,
        "documento_completo": texto}}


class _ApiFalsa:
    """Responde como la API: busca el registro grabado para la consulta, aplica el filtro por año
    (`options`) y entrega la página pedida de a 20. Anota cada petición."""

    def __init__(self, extra=None):
        self.peticiones = []
        self.respuestas = {**RESPUESTAS, **(extra or {})}

    def __call__(self, req, timeout=30):
        cuerpo = json.loads(req.data.decode("utf-8"))
        self.peticiones.append(cuerpo)
        clave = cuerpo["search"] if cuerpo["source"] == "dictamenes" else f"{cuerpo['source']}:{cuerpo['search']}"
        hits = list(self.respuestas.get(clave, {"hits": {"hits": []}})["hits"]["hits"])
        total = self.respuestas.get(clave, {"hits": {"total": {"value": 0}}})["hits"]["total"]["value"]
        filtros = cuerpo["options"] if isinstance(cuerpo["options"], list) else []
        for filtro in filtros:
            hits = [h for h in hits if h["_source"].get(filtro["field"]) == filtro["value"]]
            total = len(hits)
        total = max(total, len(hits))
        pagina = hits[cuerpo["page"] * 20:(cuerpo["page"] + 1) * 20]
        return io.BytesIO(json.dumps({"hits": {"total": {"value": total, "relation": "eq"},
                                               "hits": pagina}}).encode("utf-8"))


@pytest.fixture
def api(monkeypatch):
    falsa = _ApiFalsa()
    monkeypatch.setattr(cgr_connector, "safe_urlopen", falsa)
    return falsa


@pytest.fixture
def cgr(tmp_path, api):
    return CGRClient(cache_dir=str(tmp_path))


# --- 1. Página 0 ------------------------------------------------------------------------------

def test_las_tres_busquedas_piden_la_primera_pagina(cgr, api):
    res = cgr.search_jurisprudencia("oficina de partes virtual")
    cgr.search_auditorias("patrimonio cultural")
    cgr.search_instructivos("sumarios")

    assert [p["page"] for p in api.peticiones] == [0, 0, 0]
    assert res["total"] == 2 and len(res["resultados"]) == 2, "total > 0 con resultados vacíos: página equivocada"


# --- 3 y 4. Identificador citable, texto íntegro y enlaces -------------------------------------

def test_dictamen_con_identificador_citable_y_enlaces(cgr):
    d = cgr.search_jurisprudencia("oficina de partes virtual")["resultados"][0]

    assert d["docId"] == "E311060N23" and d["numero"] == "E311060" and d["anio"] == "2023"
    assert d["organismo"] == "CGR" and d["tipo_acto"] == "Dictamen"
    assert d["organismo_destinatario"] == "Secretario General de Carabineros de Chile"
    assert d["fuentes_legales"].startswith("Ley 21180") and d["descriptores"].startswith("Carabineros")
    assert d["pdfUrl"] == "https://www.contraloria.cl/pdfbuscador/dictamenes/E311060N23/pdf"
    assert d["urlHtml"] == "https://www.contraloria.cl/pdfbuscador/dictamenes/E311060N23/html"
    assert d["url"] == d["urlHtml"] and d["link_oficial"] == d["pdfUrl"]
    assert d["nombre"] == "Dictamen E311060", "sin nombre, la cita no tendría identificador"


def test_el_texto_integral_viene_con_el_dictamen_pedido(cgr):
    d = cgr.get_dictamen("E311060N23")
    assert d["texto"].startswith("Nº E311060") and d["texto"] == d["texto_integral"]


def test_una_lista_trae_la_materia_y_no_desborda_la_salida_mcp(tmp_path, monkeypatch):
    # Veinte dictámenes de 50.000 caracteres: en la lista va la materia, no el texto íntegro.
    grandes = {"pesada": {"hits": {"total": {"value": 20}, "hits": [
        _hit(f"E{n:06d}N24", "2024", materia=f"Materia {n}", texto="x" * 50_000) for n in range(20)]}}}
    monkeypatch.setattr(cgr_connector, "safe_urlopen", _ApiFalsa(grandes))
    res = CGRClient(cache_dir=str(tmp_path)).search_jurisprudencia("pesada")

    assert all(d["texto"] == d["materia"] == d["texto_integral"] for d in res["resultados"])
    assert len(json.dumps(res, ensure_ascii=False)) < 60_000


def test_sin_documento_completo_el_texto_sale_del_html():
    hit = copy.deepcopy(RESPUESTAS["oficina de partes virtual"]["hits"]["hits"][0])
    del hit["_source"]["documento_completo"]
    d = cgr_connector._normalizar_hit(hit, "dictamenes")
    assert d["texto"].startswith("Nº E311060") and "<" not in d["texto"]


def test_series_con_letras_conservan_su_prefijo(cgr):
    d289 = cgr.search_jurisprudencia("D289")["resultados"][0]
    of = cgr.search_jurisprudencia("OF131056")["resultados"][0]
    assert (d289["docId"], d289["numero"]) == ("D289N26", "D289"), "n_dictamen trae «289», sin la serie"
    assert (of["docId"], of["numero"]) == ("OF131056N26", "OF131056")


def test_auditoria_cita_numero_con_anio_y_destinatario_sin_html(cgr):
    a = cgr.search_auditorias("patrimonio cultural")["resultados"][0]

    assert a["docId"] == "622/2026" and a["tipo_acto"] == "Auditoría" and a["organismo"] == "CGR"
    assert a["organismo_destinatario"] == "MUNICIPALIDAD DE SALAMANCA"
    assert a["urlHtml"] == "", "la ruta pdfbuscador de una auditoría da 404"
    assert a["pdfUrl"].startswith("https://www.contraloria.cl/SicaProd/") and a["url"] == a["pdfUrl"]
    assert a["texto"].startswith("•"), "el resumen de una auditoría son sus conclusiones"


def test_instructivo_no_queda_con_identificador_i(cgr):
    i = cgr.search_instructivos("sumarios")["resultados"][0]
    assert i["docId"] == "IN29N26", "numeric_doc_id es «I» en todos los instructivos"
    assert i["tipo_acto"] == "Instructivo"
    assert i["pdfUrl"] == "https://www.contraloria.cl/pdfbuscador/instructivos/IN29N26/pdf"


# --- 2. El dictamen pedido, nunca otro ---------------------------------------------------------

def test_get_dictamen_devuelve_el_pedido_aunque_venga_segundo(cgr, api):
    # La API responde [0E6541N25, E311060N23]: quedarse con el primero era la cita falsa del issue #1.
    d = cgr.get_dictamen("E311060N23")
    assert d["docId"] == "E311060N23"
    assert len(api.peticiones) == 1


@pytest.mark.parametrize("pedido, esperado", [
    ("e311060n23", "E311060N23"),                    # minúsculas
    ("E311060 de 2023", "E311060N23"),               # como se cita en un escrito
    ("49495/2009", "049495N09"),                     # número/año, con el cero a la izquierda del código
    ("Dictamen N° 49.495, de 2009", "049495N09"),    # con punto de miles, «N°» y «, de»
    ("049495N12", "049495N12"),
    ("D289", "D289N26"),                             # sin año, pero uno solo
    ("OF131056N26", "OF131056N26"),                  # serie de dos letras
])
def test_get_dictamen_resuelve_las_formas_de_escribir_el_codigo(cgr, pedido, esperado):
    assert cgr.get_dictamen(pedido).get("docId") == esperado


def test_numero_sin_anio_que_calza_con_varios_es_error_con_candidatos(cgr):
    d = cgr.get_dictamen("49495")
    assert "error" in d and "año" in d["error"]
    assert d["candidatos"] == ["049495N09", "049495N12"]


def test_anio_que_no_calza_es_error_y_no_otro_dictamen(cgr):
    d = cgr.get_dictamen("E311060N24")
    assert "error" in d and "docId" not in d
    assert "E311060N23" in d["candidatos"]


def test_codigo_vacio_es_error_sin_ir_a_la_red(cgr, api):
    assert "error" in cgr.get_dictamen("  ")
    assert api.peticiones == []


def test_dictamen_muy_citado_se_halla_filtrando_por_anio(tmp_path, monkeypatch):
    # 85.700/2016: los dictámenes posteriores que lo citan llenan las primeras páginas (de lo más
    # nuevo a lo más antiguo); el pedido queda al final. Con el año, la API lo trae en la primera.
    citantes = [_hit(f"E{n:06d}N25", "2025") for n in range(140)]
    pagina = {"85700": {"hits": {"total": {"value": 141}, "hits": citantes + [_hit("085700N16", "2016")]}}}
    falsa = _ApiFalsa(pagina)
    monkeypatch.setattr(cgr_connector, "safe_urlopen", falsa)
    d = CGRClient(cache_dir=str(tmp_path)).get_dictamen("85700/2016")

    assert d.get("docId") == "085700N16", d
    assert any(p["options"] for p in falsa.peticiones), "debió filtrar por año en la API"


def test_numero_sin_anio_revisa_las_paginas_siguientes(tmp_path, monkeypatch):
    # «1034»: en la página 0 sólo aparece 001034N20; los de 2011, 2006 y 1992 están en la 1.
    hits = [_hit("001034N20", "2020")] + [_hit(f"E{n:06d}N20", "2020") for n in range(19)]
    hits += [_hit("001034N11", "2011"), _hit("001034N06", "2006"), _hit("001034N92", "1992")]
    monkeypatch.setattr(cgr_connector, "safe_urlopen", _ApiFalsa({"1034": {"hits": {"total": {"value": 23}, "hits": hits}}}))
    d = CGRClient(cache_dir=str(tmp_path)).get_dictamen("1034")

    assert "error" in d, "con sólo la página 0 habría devuelto 001034N20 como único"
    assert d["candidatos"] == ["001034N06", "001034N11", "001034N20", "001034N92"]


def test_numero_sin_anio_sin_ver_todo_no_se_da_por_unico(tmp_path, monkeypatch):
    hits = [_hit("000100N26", "2026")] + [_hit(f"E{n:06d}N26", "2026") for n in range(300)]
    monkeypatch.setattr(cgr_connector, "safe_urlopen", _ApiFalsa({"100": {"hits": {"total": {"value": 301}, "hits": hits}}}))
    d = CGRClient(cache_dir=str(tmp_path)).get_dictamen("100")

    assert "error" in d and "año" in d["error"]
    assert d["candidatos"] == ["000100N26"]


def test_consultas_distintas_no_comparten_copia_en_la_cache(cgr, tmp_path):
    cgr.search_jurisprudencia("49495/2009")
    cgr.search_jurisprudencia("49495 2009")
    archivos = [p for p in tmp_path.rglob("*") if p.is_file()]
    assert len(archivos) == 2, archivos
    assert all(p.parent == tmp_path and p.name.startswith("v2_") and not p.name.endswith(".tmp") for p in archivos)


# --- Consumidores --------------------------------------------------------------------------------

def test_el_pipeline_no_convierte_un_error_en_dictamen(cgr, monkeypatch):
    import resoluciones_parser
    import legal_graphify
    monkeypatch.setattr(legal_graphify.LegalGraphifyEngine, "ingerir_lote_dictamenes",
                        lambda self, insumos, guardar_disco=False: {})
    procesados = []
    original = resoluciones_parser.ResolucionesParserEngine.analizar_lote_resoluciones

    def espia(self, docs, tema_relevante=None):
        procesados.extend(docs)
        return original(self, docs, tema_relevante=tema_relevante)

    monkeypatch.setattr(resoluciones_parser.ResolucionesParserEngine, "analizar_lote_resoluciones", espia)
    res = cgr.procesar_y_graficar_dictamenes(["E311060N23", "49495"], convertir_a_md=False)

    assert [d["docId"] for d in procesados] == ["E311060N23"]
    assert [n["id"] for n in res["no_encontrados"]] == ["49495"]
    assert res["no_encontrados"][0]["candidatos"] == ["049495N09", "049495N12"]


def test_dos_dictamenes_del_mismo_numero_son_dos_nodos_del_grafo(cgr):
    from legal_graphify import LegalGraphifyEngine

    res = LegalGraphifyEngine().ingerir_lote_dictamenes(
        [cgr.get_dictamen("049495N12"), cgr.get_dictamen("49495/2009")], guardar_disco=False)
    ids = [d["dictamen_id"] for d in res["detalles"]]
    assert ids == ["dictamen_cgr_dictamen_49495_2012", "dictamen_cgr_dictamen_49495_2009"], res["detalles"]


def test_la_herramienta_cita_el_dictamen_en_el_formato_oficial(cgr, monkeypatch):
    import mcp_server
    monkeypatch.setattr(mcp_server, "cgr", cgr)
    res = mcp_server.handle_tool_call("cgr_search_jurisprudencia", {"query": "oficina de partes virtual"})

    cita = res["resultados"][0]["citas"][-1]
    assert cita["formato"] == "[Dictamen CGR N° E311060 (2023)]", cita
    assert cita["url"] == "https://www.contraloria.cl/pdfbuscador/dictamenes/E311060N23/html"
