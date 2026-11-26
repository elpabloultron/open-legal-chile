"""Pruebas 100 % offline para los conectores sectoriales v1.19.0 (SUSESO, SERNAC, TTA e INAPI)."""

import json
import os
import time

import config
import privacidad_inapi
from privacidad_inapi import INAPIEngine
from sernac_connector import sernac_buscar_consumidor
from suseso_connector import suseso_buscar_normativa
from tta_connector import tta_buscar_sentencias


def _envejecer(ruta, dias: int = 15) -> None:
    viejo = time.time() - dias * 24 * 60 * 60
    os.utime(ruta, (viejo, viejo))


# ─────────────────────────── Fixtures HTML / JSON realistas ───────────────────────────

HTML_SUSESO_CIRCULARES = """
<div class="recuadro">
  <div class="figure"><a href="articles-795300_archivo_01.pdf">Circular 3491</a></div>
  <h3 class="titulo"><a href="w3-article-795300.html">Circular 3491</a></h3>
  <h6 class="fecha">23/11/2026</h6>
  <p class="pn-attr">Instrucciones sobre seguro social de accidentes del trabajo Ley N.° 16.744 y licencias médicas.</p>
</div>
<div class="recuadro">
  <h3 class="titulo"><a href="w3-article-794641.html">Circular 3940</a></h3>
  <h6 class="fecha">13/11/2026</h6>
  <p class="pn-attr">Cajas de Compensación de Asignación Familiar (CCAF) y régimen de crédito social.</p>
</div>
"""

HTML_SUSESO_DICTAMENES = """
<div class="recuadro">
  <h3 class="titulo"><a href="w3-article-795314.html">Dictamen O-S-01-05028-2026</a></h3>
  <p class="margen-0 fecha">18 de noviembre de 2026</p>
  <p class="margen-0">Tema: Calificación de accidente del trabajo en trayecto bajo Ley N.° 16.744.</p>
</div>
"""

HTML_SUSESO_COMPENDIO = """
<div class="recuadro">
  <p class="titulo"><a href="/613/w3-channel.html">Compendio de Normas del Seguro Social de Accidentes del Trabajo y Enfermedades Profesionales</a></p>
  <p class="abstract">Sistematiza la normativa vigente de la Ley N.° 16.744 y mutualidades de empleadores.</p>
</div>
"""

HTML_SERNAC_CIRCULARES = """
<div class="recuadro">
  <div class="media-left"><a href="articles-89719_archivo_01.pdf">Circular Interpretativa</a></div>
  <div class="media-body">
    <h3 class="titulo"><a href="w3-article-89719.html">Deber de información y garantía legal bajo la Ley N.° 19.496</a></h3>
    <p class="fecha">15 de octubre de 2026</p>
    <p>Fija criterios interpretativos sobre derecho a garantía legal y deber de información veraz y oportuna.</p>
  </div>
</div>
"""

HTML_SERNAC_ALERTAS = """
<div class="recuadro">
  <div class="media-body">
    <h3 class="titulo"><a href="w3-article-85856.html">Alerta de Seguridad: Baterías portátiles modelo X-200 por riesgo de sobrecalentamiento</a></h3>
    <p class="fecha">04 de noviembre de 2026</p>
    <p>Llamado a revisión y retiro preventivo del mercado conforme al Art. 46 de la Ley N.° 19.496.</p>
  </div>
</div>
"""

HTML_SERNAC_JUICIOS = """
<div class="recuadro">
  <div class="media-body">
    <h3 class="titulo"><a href="w3-article-88460.html">Juicio: SERNAC - BANCO EJEMPLO (cobros indebidos)</a></h3>
    <div>Mecanismo de protección: Juicios Colectivos</div>
    <div>Proveedor: BANCO EJEMPLO S.A.</div>
  </div>
</div>
"""

JSON_TTA_OJV = {
    "data": [
        {
            "MATERIA_PRINCIPAL": "Gastos rechazados y crédito fiscal IVA",
            "SIGLA_SERVICIO": "SII",
            "ANO": "2025",
            "TRIBUNAL": "Tribunal R. Metropolitana. Cuarto",
            "NOMBRE_PROCESO": "Procedimiento general de reclamación",
            "RUC": "24-9-0000124-K",
            "RIT": "GR-18-00013-2025",
            "FECHA_SENTENCIA": "14-03-2025",
            "EXPEIENTE": "exp-001",
            "ETIQUETAS": "'Código Tributario Art. 124; Ley N.° 21.713'",
            "EXTRACTO": "Acoge parcialmente el reclamo contra liquidación de IVA por acreditación fehaciente.",
        },
        {
            "MATERIA_PRINCIPAL": "Clasificación arancelaria aduanera",
            "SIGLA_SERVICIO": "SNA",
            "ANO": "2024",
            "TRIBUNAL": "Tribunal Regional de Valparaíso",
            "NOMBRE_PROCESO": "Reclamo aduanero",
            "RUC": "23-9-0000444-1",
            "RIT": "AD-05-00088-2024",
            "FECHA_SENTENCIA": "20-08-2024",
            "EXPEIENTE": "exp-002",
            "ETIQUETAS": "'Ordenanza de Aduanas'",
            "EXTRACTO": "Confirma cargo formulado por el Servicio Nacional de Aduanas.",
        },
    ]
}

JSON_INAPI_PKG = {
    "success": True,
    "result": {
        "resources": [
            {"id": "res-inapi-2026", "name": "Registers-2026.xlsx", "datastore_active": True},
        ]
    },
}

JSON_INAPI_RECORDS = {
    "success": True,
    "result": {
        "records": [
            {
                "BrandName": "ANDESLEGAL",
                "NizaClasses": "45",
                "RegistrationNumber": "1500111",
                "ApplicationNumber": "1650001",
                "Applicants": "(CL) Estudio Andes SpA",
                "Status": "Registrada",
                "SignType": "Denominativa",
                "FilingDate": "2025-01-10 00:00:00",
                "RegistrationDate": "2025-09-01 00:00:00",
                "ExpirationDate": "2035-09-01 00:00:00",
                "ProtectionDescription": "Servicios jurídicos de asesoría legal.",
                "IMAGE": "https://buscadormarcas.inapi.cl/etiqueta/?s=1650001",
            },
            {
                "BrandName": "ANDESCLOUD",
                "NizaClasses": "9, 42",
                "RegistrationNumber": "",
                "ApplicationNumber": "1660002",
                "Applicants": "(CL) Tech Andes Ltda.",
                "Status": "En trámite",
                "SignType": "Denominativa",
                "FilingDate": "2026-02-15 00:00:00",
            },
        ]
    },
}


# ─────────────────────────── 1. SUSESO ───────────────────────────


def test_suseso_busqueda_citas_y_cache_ttl(monkeypatch, tmp_path):
    llamadas = []

    def fake_http(url, metodo="GET", headers=None, cuerpo=None, timeout=25.0):
        llamadas.append(url)
        if "10371" in url:
            return HTML_SUSESO_CIRCULARES.encode("utf-8")
        if "10372" in url:
            return HTML_SUSESO_DICTAMENES.encode("utf-8")
        return HTML_SUSESO_COMPENDIO.encode("utf-8")

    monkeypatch.setattr(config, "pedir_http", fake_http)

    res = suseso_buscar_normativa("16.744", tipo="todos", cache_dir=str(tmp_path))
    assert res["organismo"] == "SUSESO"
    assert res["total"] == 3
    assert res["origen"] == "red"
    assert res["sin_fuente_verificable"] is False
    formatos = [c["formato"] for c in res["citas"]]
    assert any(f.startswith("[SUSESO - Circular N.° 3491") for f in formatos)
    assert any(f.startswith("[Dictamen SUSESO - O-S-01-05028-2026") for f in formatos)
    assert len(llamadas) == 3

    # Caché fresca: sin nuevas llamadas HTTP
    res_cache = suseso_buscar_normativa("16.744", tipo="circulares", cache_dir=str(tmp_path))
    assert res_cache["total"] == 1
    assert res_cache["origen"] == "cache"
    assert len(llamadas) == 3

    # Vence caché + red caída -> entrega copia vencida marcada
    archivo_circ = tmp_path / "suseso_circulares.json"
    _envejecer(archivo_circ, dias=20)
    monkeypatch.setattr(config, "pedir_http", lambda *a, **k: (_ for _ in ()).throw(OSError("sin red")))

    res_vencida = suseso_buscar_normativa("3491", tipo="circulares", cache_dir=str(tmp_path))
    assert res_vencida["total"] == 1
    assert res_vencida["copia_local_vencida"] is True
    assert res_vencida["origen"] == "cache_vencida"
    assert res_vencida["avisos"]


def test_suseso_offline_sin_cache_y_solo_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "pedir_http", lambda *a, **k: (_ for _ in ()).throw(OSError("red caída")))

    res = suseso_buscar_normativa("licencia medica", tipo="dictamenes", cache_dir=str(tmp_path))
    assert res["total"] == 0
    assert res["resultados"] == []
    assert res["sin_fuente_verificable"] is True
    assert res["avisos"] and res["avisos"][0]["tipo"] == "aviso"

    res_sc = suseso_buscar_normativa("licencia", tipo="circulares", solo_cache=True, cache_dir=str(tmp_path))
    assert res_sc["sin_fuente_verificable"] is True
    assert res_sc["resultados"] == []

    res_inv = suseso_buscar_normativa("licencia", tipo="invalido", cache_dir=str(tmp_path))
    assert res_inv["sin_fuente_verificable"] is True
    assert "error" in res_inv


# ─────────────────────────── 2. SERNAC ───────────────────────────


def test_sernac_busqueda_citas_y_cache_ttl(monkeypatch, tmp_path):
    llamadas = []

    def fake_http(url, metodo="GET", headers=None, cuerpo=None, timeout=25.0):
        llamadas.append(url)
        if "21072" in url:
            return HTML_SERNAC_CIRCULARES.encode("utf-8")
        if "62727" in url:
            return HTML_SERNAC_ALERTAS.encode("utf-8")
        return HTML_SERNAC_JUICIOS.encode("utf-8")

    monkeypatch.setattr(config, "pedir_http", fake_http)

    res_circ = sernac_buscar_consumidor("garantía legal", categoria="circulares", cache_dir=str(tmp_path))
    assert res_circ["organismo"] == "SERNAC"
    assert res_circ["total"] == 1
    assert res_circ["citas"][0]["formato"].startswith("[SERNAC - Circular Interpretativa ")

    res_alerta = sernac_buscar_consumidor("baterías", categoria="alertas", cache_dir=str(tmp_path))
    assert res_alerta["total"] == 1
    assert res_alerta["citas"][0]["formato"].startswith("[SERNAC - Alerta de Seguridad")

    res_juicio = sernac_buscar_consumidor("BANCO EJEMPLO", categoria="juicios_colectivos", cache_dir=str(tmp_path))
    assert res_juicio["total"] == 1
    assert res_juicio["resultados"][0]["proveedor"] == "BANCO EJEMPLO S.A."
    assert len(llamadas) == 3

    # Caché fresca evita llamada HTTP
    res_todas = sernac_buscar_consumidor("19.496", categoria="todas", cache_dir=str(tmp_path))
    assert res_todas["origen"] == "cache"
    assert len(llamadas) == 3

    # Expiración TTL con red caída -> degradación honesta
    _envejecer(tmp_path / "sernac_alertas.json", dias=15)
    monkeypatch.setattr(config, "pedir_http", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("timeout")))
    res_venc = sernac_buscar_consumidor("baterías", categoria="alertas", cache_dir=str(tmp_path))
    assert res_venc["copia_local_vencida"] is True
    assert res_venc["total"] == 1


def test_sernac_offline_sin_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "pedir_http", lambda *a, **k: (_ for _ in ()).throw(OSError("offline")))
    res = sernac_buscar_consumidor("garantía", categoria="circulares", cache_dir=str(tmp_path))
    assert res["total"] == 0
    assert res["sin_fuente_verificable"] is True
    assert res["avisos"]

    res_sc = sernac_buscar_consumidor("garantía", categoria="alertas", solo_cache=True, cache_dir=str(tmp_path))
    assert res_sc["sin_fuente_verificable"] is True

    res_inv = sernac_buscar_consumidor("garantía", categoria="desconocida", cache_dir=str(tmp_path))
    assert "error" in res_inv


# ─────────────────────────── 3. TTA ───────────────────────────


def test_tta_sentencias_filtros_citas_y_cache(monkeypatch, tmp_path):
    llamadas = []

    def fake_http(url, metodo="GET", headers=None, cuerpo=None, timeout=25.0):
        llamadas.append(url)
        return json.dumps(JSON_TTA_OJV).encode("utf-8")

    monkeypatch.setattr(config, "pedir_http", fake_http)

    res = tta_buscar_sentencias("IVA", tribunal="Cuarto", anio="2025", cache_dir=str(tmp_path))
    assert res["organismo"] == "TTA"
    assert res["total"] == 1
    assert res["resultados"][0]["rit"] == "GR-18-00013-2025"
    assert res["citas"][0]["formato"] == "[TTA - RIT GR-18-00013-2025, Fecha: 14-03-2025]"
    assert len(llamadas) == 1

    # Caché fresca
    res2 = tta_buscar_sentencias("IVA", tribunal="Cuarto", anio="2025", cache_dir=str(tmp_path))
    assert res2["origen"] == "cache"
    assert len(llamadas) == 1

    # Vencida + red caída -> copia vencida
    cache_file = next(tmp_path.glob("tta_sentencias_*.json"))
    _envejecer(cache_file, dias=10)
    monkeypatch.setattr(config, "pedir_http", lambda *a, **k: (_ for _ in ()).throw(OSError("offline")))

    res3 = tta_buscar_sentencias("IVA", tribunal="Cuarto", anio="2025", cache_dir=str(tmp_path))
    assert res3["copia_local_vencida"] is True
    assert res3["total"] == 1


def test_tta_fallback_wp_y_sin_cache(monkeypatch, tmp_path):
    def fake_wp_only(url, metodo="GET", headers=None, cuerpo=None, timeout=25.0):
        if "ojv.tta.cl" in url:
            raise OSError("OJV caída")
        return json.dumps([
            {
                "id": 99,
                "date": "2026-05-10T12:00:00",
                "title": {"rendered": "Fallo relevante RIT GR-01-00010-2026 sobre Ley 21.713"},
                "excerpt": {"rendered": "<p>Tribunal Tributario y Aduanero de Iquique acoge reclamo.</p>"},
                "link": "https://www.tta.cl/fallo-99/",
            }
        ]).encode("utf-8")

    monkeypatch.setattr(config, "pedir_http", fake_wp_only)
    res = tta_buscar_sentencias("21.713", cache_dir=str(tmp_path))
    assert res["total"] == 1
    assert res["citas"][0]["formato"] == "[TTA - RIT GR-01-00010-2026, Fecha: 2026-05-10]"

    monkeypatch.setattr(config, "pedir_http", lambda *a, **k: (_ for _ in ()).throw(OSError("offline")))
    res_sc = tta_buscar_sentencias("renta", solo_cache=True, cache_dir=str(tmp_path))
    assert res_sc["sin_fuente_verificable"] is True
    assert res_sc["resultados"] == []


# ─────────────────────────── 4. INAPI DATOS ABIERTOS ───────────────────────────


def test_inapi_datos_abiertos_y_factibilidad(monkeypatch, tmp_path):
    monkeypatch.setattr(privacidad_inapi, "INAPI_CACHE_DIR", str(tmp_path))
    llamadas = []

    def fake_inapi(url, metodo="GET", headers=None, cuerpo=None, timeout=20.0):
        llamadas.append(url)
        if "package_show" in url:
            return json.dumps(JSON_INAPI_PKG).encode("utf-8")
        return json.dumps(JSON_INAPI_RECORDS).encode("utf-8")

    monkeypatch.setattr(config, "pedir_http", fake_inapi)

    res = INAPIEngine.buscar_marcas_datos_abiertos("ANDESLEGAL", clase_niza="45", cache_dir=str(tmp_path))
    assert res["organismo"] == "INAPI"
    assert res["total"] == 1
    assert res["resultados"][0]["numero_registro"] == "1500111"
    assert res["citas"][0]["formato"].startswith("[INAPI - Registro/Datos Abiertos ANDESLEGAL")
    assert len(llamadas) == 2

    # Caché fresca
    res_cache = INAPIEngine.buscar_marcas_datos_abiertos("ANDESLEGAL", clase_niza="45", cache_dir=str(tmp_path))
    assert res_cache["origen"] == "cache"
    assert len(llamadas) == 2

    # Retrocompatibilidad con consultar_inapi=False (no llama a la red)
    llamadas.clear()
    eval_sin_red = INAPIEngine.evaluar_factibilidad_marca("VindexLegal", clase_niza="45")
    assert eval_sin_red["nivel_riesgo_preliminar"] == "BAJO"
    assert "consulta_inapi" not in eval_sin_red
    assert llamadas == []

    # Con consultar_inapi=True detecta coincidencia idéntica y eleva riesgo a ALTO
    eval_con_inapi = INAPIEngine.evaluar_factibilidad_marca("ANDESLEGAL", clase_niza="45", consultar_inapi=True)
    assert "consulta_inapi" in eval_con_inapi
    assert eval_con_inapi["nivel_riesgo_preliminar"] == "ALTO"
    assert eval_con_inapi["consulta_inapi"]["total"] == 1
    assert eval_con_inapi["citas"]

    # Coincidencia parcial (contiene término) eleva riesgo de BAJO a MEDIO
    eval_parcial = INAPIEngine.evaluar_factibilidad_marca("ANDES", clase_niza="45", consultar_inapi=True)
    assert eval_parcial["nivel_riesgo_preliminar"] == "MEDIO"


def test_inapi_offline_vencido_y_factibilidad_segura(monkeypatch, tmp_path):
    monkeypatch.setattr(privacidad_inapi, "INAPI_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(config, "pedir_http", lambda *a, **k: json.dumps(JSON_INAPI_RECORDS).encode("utf-8"))
    INAPIEngine.buscar_marcas_datos_abiertos("ANDESCLOUD", clase_niza="42", cache_dir=str(tmp_path))

    cache_file = next(tmp_path.glob("inapi_marcas_*.json"))
    _envejecer(cache_file, dias=20)
    monkeypatch.setattr(config, "pedir_http", lambda *a, **k: (_ for _ in ()).throw(OSError("offline")))

    res_venc = INAPIEngine.buscar_marcas_datos_abiertos("ANDESCLOUD", clase_niza="42", cache_dir=str(tmp_path))
    assert res_venc["copia_local_vencida"] is True
    assert res_venc["total"] == 1

    # solo_cache sin archivo previo -> sin fuente verificable
    res_sc = INAPIEngine.buscar_marcas_datos_abiertos("MARCA_NO_CACHE", solo_cache=True, cache_dir=str(tmp_path))
    assert res_sc["sin_fuente_verificable"] is True
    assert res_sc["resultados"] == []

    # Sin caché + red caída -> sin fuente verificable, sin excepción en evaluar_factibilidad_marca
    eval_off = INAPIEngine.evaluar_factibilidad_marca("MarcaInexistenteTest", clase_niza="35", consultar_inapi=True)
    assert "consulta_inapi" in eval_off
    assert eval_off["consulta_inapi"]["sin_fuente_verificable"] is True
    assert eval_off["nivel_riesgo_preliminar"] == "BAJO"

    # Si buscar_marcas_datos_abiertos fallara inesperadamente, evaluar_factibilidad_marca no revienta
    monkeypatch.setattr(
        INAPIEngine,
        "buscar_marcas_datos_abiertos",
        staticmethod(lambda *a, **k: (_ for _ in ()).throw(RuntimeError("fallo inesperado"))),
    )
    eval_err = INAPIEngine.evaluar_factibilidad_marca("MarcaResiliente", clase_niza="45", consultar_inapi=True)
    assert eval_err["consulta_inapi"]["sin_fuente_verificable"] is True
    assert eval_err["nivel_riesgo_preliminar"] == "BAJO"


def test_mcp_handle_tool_call_conectores_sectoriales_v119(monkeypatch, tmp_path):
    """Verifica el despacho MCP lazy e offline de SUSESO, SERNAC, TTA e INAPI."""
    import mcp_server
    import sernac_connector
    import suseso_connector
    import tta_connector

    monkeypatch.setattr(suseso_connector, "CACHE_DIR", str(tmp_path / "suseso"))
    monkeypatch.setattr(sernac_connector, "CACHE_DIR", str(tmp_path / "sernac"))
    monkeypatch.setattr(tta_connector, "CACHE_DIR", str(tmp_path / "tta"))
    monkeypatch.setattr(privacidad_inapi, "INAPI_CACHE_DIR", str(tmp_path / "inapi"))

    def fake_http(url, headers=None, timeout=20.0):
        u = str(url).lower()
        if "suseso" in u:
            return HTML_SUSESO_CIRCULARES.encode("utf-8")
        if "sernac" in u:
            return HTML_SERNAC_CIRCULARES.encode("utf-8")
        if "tta" in u:
            return json.dumps(JSON_TTA_OJV).encode("utf-8")
        if "package_show" in u:
            return json.dumps(JSON_INAPI_PKG).encode("utf-8")
        return json.dumps(JSON_INAPI_RECORDS).encode("utf-8")

    monkeypatch.setattr(config, "pedir_http", fake_http)

    assert "error" in mcp_server.handle_tool_call("suseso_buscar_normativa", {})
    assert "error" in mcp_server.handle_tool_call("sernac_buscar_consumidor", {})
    assert "error" in mcp_server.handle_tool_call("tta_buscar_sentencias", {})
    assert "error" in mcp_server.handle_tool_call("inapi_buscar_marcas", {})

    r_sus = mcp_server.handle_tool_call("suseso_buscar_normativa", {"query": "16.744", "tipo": "circulares"})
    assert isinstance(r_sus, dict) and r_sus["total"] >= 1

    r_ser = mcp_server.handle_tool_call("sernac_buscar_consumidor", {"query": "garantía", "categoria": "circulares"})
    assert isinstance(r_ser, dict) and r_ser["total"] >= 1

    r_tta = mcp_server.handle_tool_call("tta_buscar_sentencias", {"query": "gasto rechazado"})
    assert isinstance(r_tta, dict) and r_tta["total"] >= 1

    r_ina = mcp_server.handle_tool_call("inapi_buscar_marcas", {"marca": "ANDESLEGAL", "clase_niza": "45"})
    assert isinstance(r_ina, dict) and r_ina["total"] >= 1

    r_eval = mcp_server.handle_tool_call(
        "inapi_evaluar_marca",
        {"marca_propuesta": "ANDESLEGAL", "clase_niza": "45", "consultar_inapi": True},
    )
    assert "consulta_inapi" in r_eval and r_eval["consulta_inapi"]["total"] >= 1

