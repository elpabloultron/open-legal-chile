"""
Pruebas 100 % offline para los conectores oficiales públicos chilenos (v1.19.0):
- compras_publicas_connector (Mercado Público / ChileCompra OCDS + cruce InfoProbidad)
- transparencia_cplt_connector (CPLT Amparos Ley N.° 20.285 e InfoLobby Ley N.° 20.730)
- diario_oficial_connector (Diario Oficial por fecha/sección y CVE)
- docket_watcher.DocketWatcherEngine.radar_normativo_resumen (extensión retrocompatible)
"""

import json
import os
import time
import urllib.error

import compras_publicas_connector as cp
import config
import diario_oficial_connector as do_conn
from docket_watcher import DocketWatcherEngine
import infoprobidad_connector
import transparencia_cplt_connector as cplt


def _envejecer(ruta, dias=10):
    viejo = time.time() - dias * 24 * 60 * 60
    os.utime(ruta, (viejo, viejo))


def _payload_ocds_ejemplo():
    return {
        "releases": [
            {
                "ocid": "ocid-70d2nz-2323-12-LE26",
                "id": "CL-CHILECOMPRA-2323-12-LE26-1",
                "date": "2026-11-10T12:00:00Z",
                "buyer": {"name": "Municipalidad de Providencia", "id": "69.070.300-8"},
                "tender": {
                    "id": "2323-12-LE26",
                    "title": "Adquisición de equipamiento computacional",
                    "status": "complete",
                    "description": "Compra de computadores portátiles para escuelas municipales.",
                    "procurementMethod": "open",
                    "value": {"amount": 25000000, "currency": "CLP"},
                },
                "awards": [
                    {
                        "id": "1",
                        "status": "active",
                        "date": "2026-11-15T10:00:00Z",
                        "value": {"amount": 24500000, "currency": "CLP"},
                        "suppliers": [{"name": "Tecnología Austral SpA", "id": "76.123.456-0"}],
                    }
                ],
            },
            {
                "ocid": "ocid-70d2nz-4500-1-TD26",
                "id": "CL-CHILECOMPRA-4500-1-TD26-1",
                "date": "2026-11-12T09:00:00Z",
                "buyer": {"name": "Servicio de Salud Metropolitano", "id": "61.608.000-1"},
                "tender": {
                    "id": "4500-1-TD26",
                    "title": "Servicio de asesoría jurídica urgente",
                    "status": "active",
                    "procurementMethodDetails": "Trato Directo",
                },
                "awards": [
                    {
                        "id": "1",
                        "value": {"amount": 12000000, "currency": "CLP"},
                        "suppliers": [{"name": "Consultora Sur Ltda.", "id": "12345678-5"}],
                    }
                ],
            },
        ]
    }


# ────────────────────────── Compras Públicas ──────────────────────────


def test_compras_publicas_ocds_exito_y_cache_ttl(monkeypatch, tmp_path):
    llamadas = []

    def fake_http(url, headers=None, timeout=20.0):
        llamadas.append(url)
        return json.dumps(_payload_ocds_ejemplo()).encode("utf-8")

    monkeypatch.setattr(config, "pedir_http", fake_http)
    cp._MEM_CACHE.clear()

    res1 = cp.compras_publicas_buscar(
        query="computadores",
        tipo="licitaciones",
        organismo="Providencia",
        cache_dir=str(tmp_path),
    )
    assert len(llamadas) == 1
    assert res1["total"] == 1
    assert res1["sin_fuente_verificable"] is False
    assert res1["resultados"][0]["codigo"] == "2323-12-LE26"
    assert res1["citas"][0]["formato"].startswith("[ChileCompra - ")

    # Segunda llamada dentro del TTL: no debe ir a la red
    res2 = cp.compras_publicas_buscar(
        query="computadores",
        tipo="licitaciones",
        organismo="Providencia",
        cache_dir=str(tmp_path),
    )
    assert len(llamadas) == 1
    assert res2["desde_cache"] is True
    assert res2["resultados"][0]["codigo"] == "2323-12-LE26"


def test_compras_publicas_cache_vencido_y_degradacion_offline(monkeypatch, tmp_path):
    estado = {"online": True}

    def fake_http(url, headers=None, timeout=20.0):
        if not estado["online"]:
            raise urllib.error.URLError("sin conexión")
        return json.dumps(_payload_ocds_ejemplo()).encode("utf-8")

    monkeypatch.setattr(cp, "pedir_http", fake_http)
    cp._MEM_CACHE.clear()

    cp.compras_publicas_buscar("asesoria", tipo="tratos_directos", cache_dir=str(tmp_path))
    archivo_cache = next(tmp_path.glob("cp_*.json"))
    _envejecer(archivo_cache, dias=5)
    estado["online"] = False

    vencido = cp.compras_publicas_buscar("asesoria", tipo="tratos_directos", cache_dir=str(tmp_path))
    assert vencido["copia_local_vencida"] is True
    assert vencido["total"] == 1
    assert any(a["tipo"] == "aviso" for a in vencido["advertencias"])

    # Consulta no cacheada sin red -> sin_fuente_verificable
    sin_fuente = cp.compras_publicas_buscar("inexistente", tipo="ordenes_compra", cache_dir=str(tmp_path))
    assert sin_fuente["sin_fuente_verificable"] is True
    assert sin_fuente["resultados"] == []
    assert any(a["tipo"] == "aviso" for a in sin_fuente["advertencias"])

    # solo_cache sin copia previa -> sin_fuente_verificable sin tocar red
    solo_c = cp.compras_publicas_buscar("otra", solo_cache=True, cache_dir=str(tmp_path))
    assert solo_c["sin_fuente_verificable"] is True


def test_compras_publicas_ticket_opcional_y_tipos(monkeypatch, tmp_path):
    urls_vistas = []

    def fake_http(url, headers=None, timeout=20.0):
        urls_vistas.append(url)
        return json.dumps({
            "Listado": [
                {
                    "CodigoExterno": "9988-77-LP26",
                    "Nombre": "Licitación Software Contable",
                    "Estado": "Adjudicada",
                    "Comprador": {"NombreOrganismo": "Tesorería General", "RutUnidad": "60.805.000-0"},
                    "Proveedor": "Software Chile SpA",
                    "RutProveedor": "76.543.210-K",
                }
            ]
        }).encode("utf-8")

    monkeypatch.setenv("MERCADOPUBLICO_TICKET", "TICKET-PRUEBA-PUB")
    monkeypatch.setattr(config, "pedir_http", fake_http)
    cp._MEM_CACHE.clear()

    res = cp.compras_publicas_buscar(
        query="Software",
        tipo="licitaciones",
        codigo_licitacion="9988-77-LP26",
        cache_dir=str(tmp_path),
    )
    assert "ticket=TICKET-PRUEBA-PUB" in urls_vistas[0]
    assert res["total"] == 1
    assert res["resultados"][0]["codigo"] == "9988-77-LP26"

    invalido = cp.compras_publicas_buscar("algo", tipo="invalido", cache_dir=str(tmp_path))
    assert invalido["sin_fuente_verificable"] is True
    assert "error" in invalido


def test_compras_publicas_cruzar_probidad_rut_invalido_y_cruce_real(monkeypatch, tmp_path):
    cp._MEM_CACHE.clear()

    # 1. RUT inválido rechazado vía entes_publicos.validar_rut sin ir a red
    invalido = cp.compras_publicas_cruzar_probidad("12.345.678-9", cache_dir=str(tmp_path))
    assert invalido["rut_valido"] is False
    assert invalido["sin_fuente_verificable"] is True
    assert invalido["nivel_riesgo"] == "NO_VERIFICABLE"
    assert "error" in invalido

    # 2. Cruce real con RUT válido (12.345.678-5) + DIP HTML en InfoProbidad
    dip_html = """
    <html><body>
      <h1>Juan Pérez Soto</h1>
      <dl><dt>Institución:</dt><dd>Servicio de Salud Metropolitano</dd></dl>
      <h3>Participación en Sociedades</h3>
      <table>
        <tr><th>Razón Social</th><th>RUT</th></tr>
        <tr><td>Consultora Sur Ltda.</td><td>12.345.678-5</td></tr>
      </table>
    </body></html>
    """

    def fake_http(url, headers=None, timeout=20.0):
        if "infoprobidad.cl" in url:
            return dip_html.encode("utf-8")
        return json.dumps(_payload_ocds_ejemplo()).encode("utf-8")

    monkeypatch.setattr(config, "pedir_http", fake_http)

    cruce = cp.compras_publicas_cruzar_probidad(
        "12.345.678-5",
        nombre="Consultora Sur Ltda.",
        organismo="Servicio de Salud Metropolitano",
        cache_dir=str(tmp_path),
    )
    assert cruce["rut_valido"] is True
    assert cruce["rut_canonico"] == "12.345.678-5"
    assert cruce["cruce_completo"] is True
    assert cruce["sin_fuente_verificable"] is False
    assert cruce["nivel_riesgo"] == "ALTO"
    tipos_hallazgos = {h["tipo"] for h in cruce["hallazgos"]}
    assert "COINCIDENCIA_DECLARACION_PATRIMONIO" in tipos_hallazgos
    assert "ADJUDICACIONES_TRATO_DIRECTO" in tipos_hallazgos
    formatos_citas = [c["formato"] for c in cruce["citas"]]
    assert any(f.startswith("[BCN - Ley N.° 19.886, Art. 4]") for f in formatos_citas)
    assert any(f.startswith("[ChileCompra - ") for f in formatos_citas)
    assert any(f.startswith("[InfoProbidad - ") for f in formatos_citas)


def test_compras_publicas_cruzar_probidad_fuente_faltante_honesta(monkeypatch, tmp_path):
    cp._MEM_CACHE.clear()

    class _FakeInfoProbidad:
        def get_declaracion(self, _termino):
            return {"error": "Servicio InfoProbidad no disponible"}

    monkeypatch.setattr(infoprobidad_connector, "InfoProbidadClient", _FakeInfoProbidad)
    monkeypatch.setattr(
        config,
        "pedir_http",
        lambda url, headers=None, timeout=20.0: json.dumps(_payload_ocds_ejemplo()).encode("utf-8"),
    )

    cruce = cp.compras_publicas_cruzar_probidad("12.345.678-5", cache_dir=str(tmp_path))
    assert cruce["rut_valido"] is True
    assert cruce["cruce_completo"] is False
    assert cruce["sin_fuente_verificable"] is True
    assert "infoprobidad" in cruce["faltantes"]
    assert any("InfoProbidad" in a["titulo"] for a in cruce["advertencias"])


# ────────────────────────── CPLT e InfoLobby ──────────────────────────


def test_cplt_buscar_amparos_ckan_y_csv_y_cache(monkeypatch, tmp_path):
    cplt._MEM_CACHE.clear()
    llamadas = []

    def fake_http(url, headers=None, timeout=20.0):
        llamadas.append(url)
        if "recursos/amparos.csv" in url:
            return (
                "rol,organismo,estado,decision,fecha_decision,materia\n"
                "C4321-25,Ministerio de Hacienda,Resuelto,Acogido,2026-04-10,Acceso a actas de licitación\n"
            ).encode("utf-8")
        if "package_search" in url:
            return json.dumps({
                "success": True,
                "result": {
                    "results": [
                        {
                            "title": "Dataset Amparos",
                            "resources": [{"format": "CSV", "url": "https://datosabiertos.cplt.cl/recursos/amparos.csv"}],
                        }
                    ]
                },
            }).encode("utf-8")
        if "Hacienda" in url:
            raise urllib.error.URLError("datastore sin índice para esta consulta")
        return json.dumps({
            "success": True,
            "result": {
                "records": [
                    {
                        "rol": "C1024-26",
                        "organismo": "Municipalidad de Valparaíso",
                        "estado": "Acogido",
                        "decision": "Acoge amparo",
                        "fecha_decision": "2026-09-01",
                        "materia": "Entrega de contratos de aseo y ornato",
                    }
                ]
            },
        }).encode("utf-8")

    monkeypatch.setattr(config, "pedir_http", fake_http)

    res = cplt.cplt_buscar_amparos(
        query="aseo",
        organismo="Valparaíso",
        estado="Acogido",
        cache_dir=str(tmp_path),
    )
    assert len(llamadas) == 1
    assert res["total"] == 1
    assert res["resultados"][0]["rol"] == "C1024-26"
    assert res["citas"][0]["formato"] == "[CPLT - Amparo Rol C1024-26]"

    # Caché hit
    res_cache = cplt.cplt_buscar_amparos(
        query="aseo",
        organismo="Valparaíso",
        estado="Acogido",
        cache_dir=str(tmp_path),
    )
    assert len(llamadas) == 1
    assert res_cache["desde_cache"] is True

    # Fallback CKAN package_search -> CSV
    res_csv = cplt.cplt_buscar_amparos(
        query="actas",
        organismo="Hacienda",
        cache_dir=str(tmp_path),
    )
    assert res_csv["total"] == 1
    assert res_csv["resultados"][0]["rol"] == "C4321-25"


def test_cplt_buscar_lobby_y_degradacion_offline(monkeypatch, tmp_path):
    cplt._MEM_CACHE.clear()
    estado = {"online": True}

    def fake_http(url, headers=None, timeout=20.0):
        if not estado["online"]:
            raise RuntimeError("red caída")
        if "/viajes" in url or ("datastore_search" in url and "viajes" in url):
            raise urllib.error.URLError("endpoint rest no disponible")
        if "sparql" in url:
            return json.dumps({
                "results": {
                    "bindings": [
                        {
                            "viaje": {"value": "V-901"},
                            "institucion": {"value": "Ministerio de Energía"},
                            "sujeto_pasivo": {"value": "Subsecretario de Energía"},
                            "materia": {"value": "Seminario de Hidrógeno Verde en Antofagasta"},
                            "fecha": {"value": "2026-08-20"},
                        }
                    ]
                }
            }).encode("utf-8")
        return json.dumps({
            "data": [
                {
                    "identificador": "AUD-2026-55",
                    "institucion": "Ministerio de Salud",
                    "sujeto_pasivo": "Jefe de Gabinete",
                    "sujeto_activo": "Asociación de Clínicas",
                    "materia": "Reglamento de licencias médicas",
                    "fecha": "2026-10-05",
                }
            ]
        }).encode("utf-8")

    monkeypatch.setattr(cplt, "pedir_http", fake_http)

    aud = cplt.cplt_buscar_lobby("licencias", tipo="audiencias", institucion="Salud", cache_dir=str(tmp_path))
    assert aud["total"] == 1
    assert aud["citas"][0]["formato"].startswith("[InfoLobby - Audiencia")

    viajes = cplt.cplt_buscar_lobby("Hidrógeno", tipo="viajes", cache_dir=str(tmp_path))
    assert viajes["total"] == 1
    assert viajes["citas"][0]["formato"].startswith("[InfoLobby - Viaje")

    # Envejecer caché y cortar red -> copia_local_vencida
    for archivo in tmp_path.glob("cplt_lobby_audiencias_*.json"):
        _envejecer(archivo, dias=10)
    estado["online"] = False

    aud_vencido = cplt.cplt_buscar_lobby("licencias", tipo="audiencias", institucion="Salud", cache_dir=str(tmp_path))
    assert aud_vencido["copia_local_vencida"] is True
    assert aud_vencido["total"] == 1

    # Sin caché + offline -> sin_fuente_verificable
    don = cplt.cplt_buscar_lobby("algo", tipo="donativos", cache_dir=str(tmp_path))
    assert don["sin_fuente_verificable"] is True
    assert don["resultados"] == []

    # Tipo inválido
    inv = cplt.cplt_buscar_lobby("x", tipo="inexistente", cache_dir=str(tmp_path))
    assert inv["sin_fuente_verificable"] is True


# ────────────────────────── Diario Oficial + Docket Watcher ──────────────────────────


def test_diario_oficial_html_secciones_cve_y_cache(monkeypatch, tmp_path):
    do_conn._MEM_CACHE.clear()
    llamadas = []

    html_do = """
    <html><body>
      <h1>Edición N° 44.010</h1>
      <h2>Normas Generales</h2>
      <table>
        <tr>
          <td>Ministerio del Trabajo</td>
          <td><a href="/publicaciones/2026/11/26/ley_21855.pdf">Ley N° 21.855 sobre datos personales</a></td>
          <td>CVE 2589101</td>
        </tr>
      </table>
      <h2>Empresas y Cooperativas</h2>
      <ul>
        <li>
          <a href="/publicaciones/2026/11/26/extracto_spa.pdf">Constitución Tecnología Austral SpA</a> — CVE 2589222
        </li>
      </ul>
    </body></html>
    """

    def fake_http(url, headers=None, timeout=20.0):
        llamadas.append(url)
        return html_do.encode("utf-8")

    monkeypatch.setattr(config, "pedir_http", fake_http)

    res = do_conn.diario_oficial_consultar(
        fecha="2026-11-26",
        seccion="normas_generales",
        query="21.855",
        cache_dir=str(tmp_path),
    )
    assert len(llamadas) == 1
    assert res["edicion"] == "44.010"
    assert res["total"] == 1
    assert res["resultados"][0]["cve"] == "2589101"
    assert res["citas"][0]["formato"] == "[Diario Oficial - Edición 2026-11-26, CVE 2589101]"

    # Misma fecha desde caché (otra consulta)
    res_soc = do_conn.diario_oficial_consultar(
        fecha="2026-11-26",
        seccion="empresas_sociedades",
        query="Austral",
        cache_dir=str(tmp_path),
    )
    assert len(llamadas) == 2  # empresas_cooperativas usa archivo separado do_2026-11-26_empresas.json
    assert res_soc["total"] == 1
    assert res_soc["resultados"][0]["cve"] == "2589222"

    # Re-consulta exacta va a caché
    res_soc_2 = do_conn.diario_oficial_consultar(
        fecha="2026-11-26",
        seccion="empresas_sociedades",
        query="Austral",
        cache_dir=str(tmp_path),
    )
    assert len(llamadas) == 2
    assert res_soc_2["desde_cache"] is True


def test_diario_oficial_degradacion_y_validaciones(monkeypatch, tmp_path):
    do_conn._MEM_CACHE.clear()
    estado = {"online": True}

    def fake_http(url, headers=None, timeout=20.0):
        if not estado["online"]:
            raise ConnectionError("sin red")
        return json.dumps({
            "edicion": "44011",
            "normas_generales": [
                {
                    "titulo": "Decreto Supremo N° 100",
                    "cve": "2600001",
                    "organismo": "Ministerio de Hacienda",
                    "extracto": "Fija reglamento de compras públicas.",
                }
            ],
        }).encode("utf-8")

    monkeypatch.setattr(do_conn, "pedir_http", fake_http)

    ok = do_conn.diario_oficial_consultar(fecha="2026-11-25", cache_dir=str(tmp_path))
    assert ok["total"] == 1
    archivo = tmp_path / "do_2026-11-25_sumario.json"
    _envejecer(archivo, dias=5)
    estado["online"] = False

    vencido = do_conn.diario_oficial_consultar(fecha="2026-11-25", cache_dir=str(tmp_path))
    assert vencido["copia_local_vencida"] is True
    assert vencido["total"] == 1

    sin_red = do_conn.diario_oficial_consultar(fecha="2026-11-20", cache_dir=str(tmp_path))
    assert sin_red["sin_fuente_verificable"] is True

    fecha_mala = do_conn.diario_oficial_consultar(fecha="2026-99-99", cache_dir=str(tmp_path))
    assert fecha_mala["sin_fuente_verificable"] is True
    assert "error" in fecha_mala


def test_docket_watcher_radar_normativo_diario_oficial(monkeypatch, tmp_path):
    # 1. Defecto consultar_diario_oficial=False: retrocompatible, 0 llamadas de red
    def fallo_si_llama(*_a, **_k):
        raise AssertionError("No debía consultar Diario Oficial con consultar_diario_oficial=False")

    monkeypatch.setattr(config, "pedir_http", fallo_si_llama)
    radar_defecto = DocketWatcherEngine.radar_normativo_resumen("laboral", dias_atras=15)
    assert "diario_oficial" not in radar_defecto
    assert radar_defecto["total_alertas_detectadas"] >= 1

    # 2. Con consultar_diario_oficial=True: integra publicaciones del Diario Oficial
    do_conn._MEM_CACHE.clear()
    monkeypatch.setattr(do_conn, "CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(
        config,
        "pedir_http",
        lambda url, headers=None, timeout=20.0: json.dumps({
            "edicion": "44012",
            "normas_generales": [
                {
                    "titulo": "Ley N° 21.900 sobre modernización laboral",
                    "cve": "2611111",
                    "organismo": "Ministerio del Trabajo",
                    "extracto": "Publicación oficial de norma laboral.",
                }
            ],
        }).encode("utf-8"),
    )

    radar_do = DocketWatcherEngine.radar_normativo_resumen(
        "laboral",
        dias_atras=15,
        consultar_diario_oficial=True,
    )
    assert "diario_oficial" in radar_do
    assert radar_do["diario_oficial"]["total"] == 1
    assert radar_do["total_alertas_detectadas"] >= 2
    assert any("2611111" in a["norma"] for a in radar_do["alertas_regulatorias"])

    # 3. Error seguro si Diario Oficial falla en radar_normativo_resumen
    def fallo_do(**_kwargs):
        raise RuntimeError("caída simulada")

    monkeypatch.setattr(do_conn, "diario_oficial_consultar", fallo_do)
    radar_err = DocketWatcherEngine.radar_normativo_resumen(
        "tributario",
        dias_atras=7,
        consultar_diario_oficial=True,
    )
    assert radar_err["diario_oficial"]["sin_fuente_verificable"] is True
    assert radar_err["total_alertas_detectadas"] >= 1


def test_mcp_handle_tool_call_conectores_publicos_v119(monkeypatch, tmp_path):
    """Verifica el despacho MCP lazy e offline de los conectores públicos v1.19.0."""
    import mcp_server

    cp._MEM_CACHE.clear()
    cplt._MEM_CACHE.clear()
    do_conn._MEM_CACHE.clear()
    monkeypatch.setattr(cp, "CACHE_DIR", str(tmp_path / "cp"))
    monkeypatch.setattr(cplt, "CACHE_DIR", str(tmp_path / "cplt"))
    monkeypatch.setattr(do_conn, "CACHE_DIR", str(tmp_path / "do"))

    def fake_http(url, headers=None, timeout=20.0):
        u = str(url).lower()
        if "infoprobidad.cl" in u:
            return b"<html><body><h1>Consultora Sur Ltda.</h1></body></html>"
        if "chilecompra" in u or "mercadopublico" in u:
            return json.dumps(_payload_ocds_ejemplo()).encode("utf-8")
        if "amparo" in u or "cplt" in u or "ckan" in u:
            return json.dumps({
                "success": True,
                "result": {
                    "records": [
                        {
                            "rol": "C1111-26",
                            "organismo": "Ministerio de Hacienda",
                            "estado": "Acogido",
                            "materia": "Acceso a contratos de licitación",
                            "fecha": "2026-10-01",
                        }
                    ]
                },
            }).encode("utf-8")
        if "lobby" in u or "audiencia" in u:
            return json.dumps([
                {
                    "id": "aud-99",
                    "institucion": "Ministerio de Hacienda",
                    "sujeto_pasivo": "Subsecretario",
                    "materia": "Mesa técnica normativa",
                    "fecha": "2026-10-02",
                }
            ]).encode("utf-8")
        return json.dumps({
            "edicion": "44020",
            "normas_generales": [
                {
                    "titulo": "Decreto Supremo N° 120",
                    "cve": "2699999",
                    "organismo": "Ministerio de Hacienda",
                    "extracto": "Norma general presupuestaria.",
                }
            ],
        }).encode("utf-8")

    monkeypatch.setattr(config, "pedir_http", fake_http)

    # Validación de parámetros requeridos
    assert "error" in mcp_server.handle_tool_call("compras_publicas_buscar", {})
    assert "error" in mcp_server.handle_tool_call("compras_publicas_cruzar_probidad", {})
    assert "error" in mcp_server.handle_tool_call("cplt_buscar_amparos", {})
    assert "error" in mcp_server.handle_tool_call("cplt_buscar_lobby", {})

    r_cp = mcp_server.handle_tool_call("compras_publicas_buscar", {"query": "computadores", "limite": 5})
    assert r_cp["total"] >= 1

    r_prob = mcp_server.handle_tool_call(
        "compras_publicas_cruzar_probidad",
        {"rut_entidad_o_proveedor": "69.070.300-8", "nombre": "Providencia"},
    )
    assert "rut_valido" in r_prob

    r_amp = mcp_server.handle_tool_call("cplt_buscar_amparos", {"query": "licitacion"})
    assert r_amp["total"] >= 1

    r_lob = mcp_server.handle_tool_call("cplt_buscar_lobby", {"query": "Hacienda", "tipo": "audiencias"})
    assert isinstance(r_lob, dict) and "resultados" in r_lob

    r_do = mcp_server.handle_tool_call("diario_oficial_consultar", {"fecha": "2026-11-26"})
    assert r_do["total"] >= 1

    r_radar = mcp_server.handle_tool_call(
        "vigilante_radar_normativo",
        {"materia": "administrativo", "dias_atras": 10, "consultar_diario_oficial": True},
    )
    assert "diario_oficial" in r_radar

