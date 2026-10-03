"""
Tests unitarios para LegalCanvas (legal_canvas.py)
===================================================
Verifica:
1. Generación de dashboards HTML autónomos (un solo archivo).
2. 0 dependencias externas (sin CDN, sin Google Fonts, sin trackers de terceros).
3. Presencia obligatoria de la ⚖️ Compuerta de Revisión Jurídica.
4. Sanitización XSS de entradas del usuario.
5. Integración armónica con LegalOpenJev y LegalGraphify.
"""

import os
import re
import tempfile
import pytest

from legal_canvas import LegalCanvasEngine
from legal_open_jev import LegalOpenJevEngine


def test_render_case_dashboard_estructura_base():
    analisis = {
        "materia": "laboral",
        "materia_etiqueta": "Derecho del Trabajo",
        "fuero_probable": "Juzgado de Letras del Trabajo",
        "fecha_analisis": "2026-10-03",
        "deteccion": {
            "roles": ["O-1234-2026"],
            "fechas": [{"fecha": "2026-08-01", "contexto": "Carta de despido"}],
            "documentos": [{"nombre": "contrato_trabajo.pdf", "tipo": "pdf", "estado": "OK"}],
            "normas": [{"numero": 21643, "articulos": ["2"]}]
        },
        "faltan": ["Comprobante de reclamo ante la Inspección del Trabajo"],
        "plan": [
            {"paso": 1, "herramienta": "bcn_get_codigo", "motivo": "Consultar Art. 161 y 168 CT"}
        ],
        "citas": ["[BCN - Código del Trabajo, Art. 168]"]
    }

    jev_engine = LegalOpenJevEngine()
    decision = jev_engine.decide(
        query="Despido injustificado y cobro de prestaciones",
        contexto={
            "tipo_regla": "plazo_caducidad_despido_art_168_ct",
            "fecha_despido": "2026-09-01",
            "fecha_actual": "2026-09-20",
            "reclamo_dt": True
        }
    )

    html_out = LegalCanvasEngine.render_case_dashboard(analisis, jev_decision=decision)

    assert "<!DOCTYPE html>" in html_out
    assert "LegalCanvas" in html_out
    assert "O-1234-2026" in html_out
    assert "Derecho del Trabajo" in html_out
    assert "⚖️ Compuerta de Revisión Jurídica" in html_out
    assert "contrato_trabajo.pdf" in html_out
    assert "Comprobante de reclamo ante la Inspección del Trabajo" in html_out
    assert "<svg" in html_out
    assert "</svg>" in html_out
    assert "copyCitation" in html_out


def test_cero_dependencias_externas():
    """El dashboard debe ser 100% offline: no debe cargar scripts, estilos o fuentes remotas."""
    analisis = {
        "materia": "civil",
        "deteccion": {"roles": ["C-500-2026"], "fechas": [], "documentos": []}
    }
    html_out = LegalCanvasEngine.render_case_dashboard(analisis)

    # No debe haber referencias a CDN o URLs remotas en src o href externos
    enlaces_remotos = re.findall(r'(?:src|href)=["\']https?://[^"\']+["\']', html_out)
    # Excluir solo el xmlns de SVG estándar si aparece
    enlaces_filtrados = [e for e in enlaces_remotos if "w3.org/2000/svg" not in e]
    assert not enlaces_filtrados, f"Se detectaron llamadas externas prohibidas: {enlaces_filtrados}"


def test_sanitizacion_xss_en_entradas_de_usuario():
    """Cualquier entrada con tags maliciosos debe escaparse adecuadamente."""
    analisis_malicioso = {
        "materia": "<script>alert('xss')</script>",
        "deteccion": {
            "roles": ['<img src="x" onerror="alert(1)">'],
            "documentos": [{"nombre": "<b>archivo_inseguro.pdf</b>"}],
        },
        "faltan": ["<script>eval('bad')</script>"]
    }
    html_out = LegalCanvasEngine.render_case_dashboard(analisis_malicioso)

    assert "<script>alert('xss')</script>" not in html_out
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in html_out
    assert '<img src="x" onerror="alert(1)">' not in html_out
    assert "&lt;script&gt;eval(&#x27;bad&#x27;)&lt;/script&gt;" in html_out


def test_render_brief_dashboard():
    html_brief = LegalCanvasEngine.render_brief_dashboard(
        titulo_principal="DEMANDA ORDINARIA DE COBRO DE PESOS",
        tribunal="S.J.L. EN LO CIVIL DE SANTIAGO",
        presuma_data={
            "materia": "COBRO DE PESOS",
            "procedimiento": "ORDINARIO",
            "demandante": "INVERSIONES ALFA SPA",
            "demandado": "COMERCIAL BETA LIMITADA"
        },
        comparecencia="Juan Pérez, abogado, en representación de...",
        hechos="El demandado adeuda la suma de...",
        derecho="Conforme a los Arts. 1545 y 1489 del Código Civil...",
        peticiones="Se condene al demandado al pago...",
        otrosies=[
            {"numero": "1° OTROSÍ", "titulo": "Acompaña documentos", "contenido": "Facturas y pagaré"},
            {"numero": "2° OTROSÍ", "titulo": "Patrocinio y poder", "contenido": "Se tenga presente"}
        ],
        citas=["[BCN - Código Civil, Art. 1545]"]
    )

    assert "DEMANDA ORDINARIA DE COBRO DE PESOS" in html_brief
    assert "S.J.L. EN LO CIVIL DE SANTIAGO" in html_brief
    assert "INVERSIONES ALFA SPA" in html_brief
    assert "1° OTROSÍ: Acompaña documentos" in html_brief
    assert "[BCN - Código Civil, Art. 1545]" in html_brief
    assert "⚖️ Compuerta de Revisión Jurídica" in html_brief


def test_export_dashboard_guarda_archivo_correctamente():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "test_dashboard.html")
        contenido = "<html><body><h1>Dashboard Test</h1></body></html>"
        guardado = LegalCanvasEngine.export_dashboard(contenido, out_file)

        assert os.path.exists(guardado)
        with open(guardado, "r", encoding="utf-8") as f:
            assert f.read() == contenido


def test_render_subgrafo_dogmatico():
    subgrafo = {
        "institucion": "Régimen Jurídico de la Nulidad Civil",
        "norma_fundante": "Art. 1681 Código Civil",
        "vecinos": [
            {"nombre": "Nulidad Absoluta", "relacion": "ESPECIE_DE"},
            {"nombre": "Nulidad Relativa", "relacion": "ESPECIE_DE"},
            {"nombre": "CS Rol N° 12.345-2023", "relacion": "RESUELVE_CON_FALLO_RECTOR"}
        ]
    }
    analisis = {
        "materia": "civil",
        "deteccion": {"roles": ["C-12-2025"], "fechas": [], "documentos": []}
    }
    html_out = LegalCanvasEngine.render_case_dashboard(analisis, subgrafo=subgrafo)

    assert "Régimen Jurídico de la Nulidad Civil" in html_out
    assert "Art. 1681 Código Civil" in html_out
    assert "Nulidad Absoluta" in html_out
    assert "RESUELVE_CON_FALLO_RECTOR" in html_out


def test_caso_analizar_con_generar_dashboard():
    from case_intake import caso_analizar

    res = caso_analizar("Causa O-450-2026 sobre despido injustificado", generar_dashboard=True)
    assert isinstance(res, dict)
    assert "dashboard_html" in res
    assert "<!DOCTYPE html>" in res["dashboard_html"]
    assert "LegalCanvas" in res["dashboard_html"]
    assert "O-450-2026" in res["dashboard_html"]
    assert "⚖️ Compuerta de Revisión Jurídica" in res["dashboard_html"]

