"""Pruebas offline deterministas para indicadores SII, feriados, plazos, finiquito y cuantías."""

from datetime import date
from unittest.mock import patch

import calculadoras_chile as calc
from docket_watcher import DocketWatcherEngine
import mcp_server

_HTML_UF_2026 = """
<html><body>
<table>
  <tr><th colspan="6">Abril</th></tr>
  <tr><th>1</th><td>40.000,00</td><th>11</th><td>40.050,25</td><th>21</th><td>40.100,50</td></tr>
  <tr><th>30</th><td>40.150,75</td><th></th><td></td><th></th><td></td></tr>
</table>
</body></html>
"""

_HTML_UTM_2026 = """
<html><body>
<table id="table_export">
  <tr><th>2026</th><th>UTM (1)</th><th>UTA (2)</th><th>IPC</th><th>Var M</th><th>Var Acum</th><th>12M</th></tr>
  <tr><th>Abril</th><td>69.751</td><td>837.012</td><td>110,25</td><td>0,5</td><td>1,2</td><td>3,1</td></tr>
</table>
</body></html>
"""


def test_parseo_e_indicadores_sii_con_cache_y_degradacion(tmp_path):
    uf = calc.parsear_html_uf_sii(_HTML_UF_2026, 2026)
    utm = calc.parsear_html_utm_sii(_HTML_UTM_2026, 2026)
    assert uf["2026-04-01"] == 40000.0
    assert uf["2026-04-30"] == 40150.75
    assert utm[4]["utm"] == 69751
    assert utm[4]["uta"] == 837012
    assert utm[4]["ipc_puntos"] == 110.25

    def fake_http(url, timeout=10.0):
        return _HTML_UF_2026.encode("utf-8") if "/uf/" in url else _HTML_UTM_2026.encode("utf-8")

    with patch.object(calc, "pedir_http", side_effect=fake_http) as mock_http:
        res1 = calc.obtener_indicadores_sii(anio=2026, fecha="2026-04-11", cache_dir=str(tmp_path))
        assert res1["uf_fecha"] == 40050.25
        assert res1["utm_mes"]["utm"] == 69751
        assert mock_http.call_count == 2

        # Segunda llamada dentro del TTL lee caché sin red
        res2 = calc.obtener_indicadores_sii(anio=2026, fecha="2026-04-30", cache_dir=str(tmp_path))
        assert res2["uf_fecha"] == 40150.75
        assert mock_http.call_count == 2

    # Sin caché ni red responde degradación honesta
    with patch.object(calc, "pedir_http", side_effect=OSError("sin red")):
        err = calc.obtener_indicadores_sii(anio=2025, fecha="2025-05-01", cache_dir=str(tmp_path))
        assert err["sin_fuente_verificable"] is True


def test_convertir_moneda_legal_offline_con_overrides():
    r1 = calc.convertir_moneda_legal(90, "UF", "CLP", uf_override=40000.0)
    assert r1["monto_destino"] == 3600000
    r2 = calc.convertir_moneda_legal(697510, "CLP", "UTM", utm_override=69751.0)
    assert r2["monto_destino"] == 10.0
    r3 = calc.convertir_moneda_legal(1, "UTA", "CLP", utm_override=70000.0)
    assert r3["monto_destino"] == 840000


def test_feriados_chile_y_reglas_moviles():
    f2026 = calc.feriados_chile(2026)
    assert date(2026, 4, 3) in f2026 and "Viernes Santo" in f2026[date(2026, 4, 3)]
    assert date(2026, 4, 4) in f2026 and "Sábado Santo" in f2026[date(2026, 4, 4)]
    assert date(2026, 6, 21) in f2026  # Solsticio 2026
    assert date(2026, 6, 29) in f2026  # 29 jun 2026 es lunes
    assert date(2026, 10, 12) in f2026  # 12 oct 2026 es lunes
    assert date(2026, 9, 17) not in f2026 and date(2026, 9, 20) not in f2026  # 18 sep es viernes

    f2027 = calc.feriados_chile(2027)
    assert date(2027, 6, 28) in f2027  # 29 jun 2027 es martes -> lunes 28
    assert date(2027, 10, 11) in f2027  # 12 oct 2027 es martes -> lunes 11

    f2029 = calc.feriados_chile(2029)
    assert date(2029, 9, 17) in f2029  # 18 sep 2029 es martes -> Ley 20.215 agrega 17 sep


def test_calcular_plazo_procesal_cpc_administrativo_laboral_y_vigilante():
    # Notificado miércoles 2026-04-01: jue 2 (1), vie 3 Viernes Santo (inhábil), sáb 4 Sábado Santo (inhábil),
    # dom 5 (inhábil), lun 6 (2), mar 7 (3) -> Art. 66 CPC vence martes 2026-04-07.
    cpc = calc.calcular_plazo_procesal("2026-04-01", 3, regimen="judicial_cpc", fecha_referencia="2026-04-02")
    assert cpc["fecha_vencimiento"] == "2026-04-07"
    assert cpc["estado"] == "EN PLAZO"
    assert len(cpc["feriados_en_ventana"]) == 2

    # Notificado viernes 2026-04-10 por 3 días:
    # CPC (sábado sí es hábil): sáb 11 (1), dom 12 (inhábil), lun 13 (2), mar 14 (3)
    cpc_sab = calc.calcular_plazo_procesal("2026-04-10", 3, regimen="judicial_cpc")
    assert cpc_sab["fecha_vencimiento"] == "2026-04-14"
    # Administrativo Ley 19.880 (sábado inhábil): lun 13 (1), mar 14 (2), mié 15 (3)
    adm = calc.calcular_plazo_procesal("2026-04-10", 3, regimen="administrativo")
    assert adm["fecha_vencimiento"] == "2026-04-15"

    # Laboral con suspensión DT topada en 90 días (Art. 168 CT)
    lab = calc.calcular_plazo_procesal("2026-03-02", 60, regimen="laboral", dias_suspension_dt=45)
    assert lab["plazo_efectivo_dias"] == 90

    # Vigilante enriquecido con fecha_notificacion (sin mutar TRIGGERS)
    vig = DocketWatcherEngine.analizar_resolucion(
        "Traslado al incidente promovido.",
        procedimiento="civil",
        fecha_notificacion="2026-04-01",
    )
    assert vig["cargas_procesales_y_plazos"][0]["fecha_vencimiento"] == "2026-04-07"
    assert "fecha_vencimiento" not in DocketWatcherEngine.TRIGGERS[1]["plazos"][0]


def test_calcular_finiquito_laboral_tope_90uf_11anios_afc_y_recargo():
    res = calc.calcular_finiquito_laboral(
        fecha_ingreso="2013-01-10",
        fecha_termino="2026-05-15",
        remuneracion_mensual_clp=5_000_000,
        causal="161",
        aviso_previo_dado=False,
        dias_feriado_pendientes=10.0,
        aporte_empleador_afc_clp=1_500_000,
        aplicar_tope_90_uf=True,
        uf_valor=40_000.0,
        meses_cotizaciones_impagas_ley_bustos=2,
    )
    assert res["antiguedad"]["anios_indemnizables"] == 11  # Tope 11 años (13 años 4 meses)
    assert res["base_calculo"]["tope_90_uf_aplicado"] is True
    assert res["base_calculo"]["base_indemnizatoria_clp"] == 3_600_000

    fin = res["finiquito_base"]
    assert fin["indemnizacion_sustitutiva_aviso_previo_clp"] == 3_600_000
    assert fin["indemnizacion_anios_servicio_clp"] == 39_600_000
    assert fin["descuento_afc_empleador_clp"] == 1_500_000
    # Feriado proporcional usa remuneración SIN tope 90 UF
    feriado = fin["feriado_proporcional_clp"]
    assert feriado == round((5_000_000 / 30.0) * res["base_calculo"]["dias_corridos_feriado"])

    jud = res["escenario_demanda_judicial"]
    assert jud["recargo_art_168_porcentaje"] == 30
    assert jud["recargo_art_168_clp"] == round(39_600_000 * 0.30)
    assert jud["restitucion_afc_clp"] == 1_500_000
    assert jud["estimacion_ley_bustos_clp"] == 10_000_000

    renuncia = calc.calcular_finiquito_laboral(
        fecha_ingreso="2024-01-01",
        fecha_termino="2026-05-01",
        remuneracion_mensual_clp=1_200_000,
        causal="renuncia",
        uf_valor=40_000.0,
    )
    assert renuncia["finiquito_base"]["indemnizacion_anios_servicio_clp"] == 0
    assert renuncia["escenario_demanda_judicial"]["total_demanda_estimado_clp"] == renuncia["finiquito_base"]["feriado_proporcional_clp"]


def test_calcular_cuantias_legales_y_despacho_mcp():
    nat = calc.calcular_cuantias_legales(
        tipo="dias_multa_natural",
        utm_valor=70_000.0,
        grado_pena="presidio_menor_medio",
        ingreso_diario_liquido_clp=140_000.0,
        dias_multa=60,
    )
    assert nat["rango_dias_multa"]["min"] == 51 and nat["rango_dias_multa"]["max"] == 100
    assert nat["valor_dia_multa"]["utm"] == 2.0
    assert nat["multa_especifica_clp"] == 60 * 140_000

    pj = mcp_server.handle_tool_call("calcular_cuantias_legales", {
        "tipo": "dias_multa_persona_juridica",
        "utm_valor": 70_000.0,
        "dias_multa": 100,
        "valor_dia_utm": 10.0,
        "ventas_linea_clp": 1_000_000_000,
    })
    assert pj["multa_calculada_clp"] == 70_000_000
    assert pj["tope_especial_comiso_imposible_clp"] == 300_000_000

    alim = mcp_server.handle_tool_call("calcular_cuantias_legales", {
        "tipo": "alimentos_utm",
        "numero_hijos": 2,
        "imm_clp": 500_000,
        "utm_valor": 70_000.0,
        "ingreso_liquido_alimentante_clp": 1_000_000,
    })
    assert alim["pension_minima"]["clp"] == 300_000
    assert alim["pension_minima"]["utm"] == round(300_000 / 70_000.0, 5)
    assert alim["tope_50_por_ciento_rentas"]["clp"] == 500_000

    conv = mcp_server.handle_tool_call("indicadores_economicos_chile", {
        "accion": "convertir",
        "monto": 10,
        "desde": "UF",
        "hacia": "CLP",
        "uf_valor": 40_000.0,
    })
    assert conv["monto_destino"] == 400_000
