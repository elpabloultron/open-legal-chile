"""
Open Legal Chile — LegalCanvas (Motor de Dashboards Visuales e Interfaz de Entrega)
=====================================================================================
Genera artefactos visuales interactivos y micro-UIs de alta densidad de información
(filosofía Thariq Shihipar / Claude Code) en un único archivo HTML autocontenido, con
CSS y SVG embebidos y CERO dependencias externas (sin CDN, sin npm, 100% offline).

Componentes del Dashboard:
1. Carátula Forense y Metadatos Procesales (RIT/Rol, Tribunal, RUTs, Materia).
2. Estadísticas Resumen y Semáforo de Riesgo (Compuertas Noul de LegalOpenJev).
3. ⚖️ Compuerta de Revisión Jurídica Obligatoria (Art. 247 CP, Ley 20.886).
4. Línea de Tiempo Cronológica Interactiva en SVG puro.
5. Checklist Probatorio y Auditoría de Faltantes con casillas interactivas.
6. Visor Dogmático y Cajón de Citas Oficiales con botón Click-to-Copy.
7. Árbol de Decisión Procesal ("¿Qué sigue?").
"""

from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union


class LegalCanvasEngine:
    """Motor de generación de dashboards HTML/SVG autónomos para Open Legal Chile."""

    COMPUERTA_TEXTO = (
        "⚖️ Compuerta de Revisión Jurídica (Open Legal Chile): Este dashboard contiene análisis "
        "y propuestas de redacción técnica conforme a la legislación de la República de Chile. "
        "Todo escrito, presentación o cómputo fatal debe ser validado por un abogado habilitado "
        "para el ejercicio de la profesión antes de su firma e ingreso en la Oficina Judicial Virtual (OJV)."
    )

    @classmethod
    def render_case_dashboard(
        cls,
        analisis: Dict[str, Any],
        jev_decision: Optional[Any] = None,
        subgrafo: Optional[Dict[str, Any]] = None,
        titulo_caso: Optional[str] = None
    ) -> str:
        """Genera un dashboard HTML autónomo para un análisis de caso (mesa de entrada)."""
        deteccion = analisis.get("deteccion", {}) if isinstance(analisis.get("deteccion"), dict) else {}
        materia_etiqueta = analisis.get("materia_etiqueta") or analisis.get("materia") or "Materia General"
        fuero = analisis.get("fuero_probable") or "Letras / Ordinario"
        roles = deteccion.get("roles", []) or []
        rol_display = ", ".join(roles) if roles else "Sin RIT/Rol asignado (Pre-judicial)"
        titulo = titulo_caso or f"Causa: {materia_etiqueta.title()} — {rol_display}"
        fecha_str = analisis.get("fecha_analisis") or datetime.now().strftime("%Y-%m-%d")

        # 1. Hitos para la línea de tiempo SVG
        hitos: List[Dict[str, Any]] = []
        fechas_detectadas = deteccion.get("fechas", []) or []
        for f in fechas_detectadas:
            if isinstance(f, dict):
                hitos.append({
                    "fecha": f.get("fecha") or f.get("texto") or "Fecha clave",
                    "etiqueta": f.get("contexto") or f.get("tipo") or "Hito fáctico",
                    "tipo": "factico"
                })
            elif isinstance(f, str):
                hitos.append({"fecha": f, "etiqueta": "Fecha identificada en autos", "tipo": "factico"})

        # Hitos de plazos si jev_decision está presente
        if jev_decision and hasattr(jev_decision, "noul_gates"):
            for gate in jev_decision.noul_gates:
                regla_nom = getattr(gate, "regla", getattr(gate, "regla_evaluada", "Plazo legal"))
                d_rest = gate.dias_restantes if gate.dias_restantes is not None else 0
                d_trans = gate.dias_transcurridos if gate.dias_transcurridos is not None else 0
                p_fatal = gate.plazo_fatal_dias if gate.plazo_fatal_dias is not None else 0
                hitos.append({
                    "fecha": f"Día {d_trans}/{p_fatal}",
                    "etiqueta": f"{regla_nom} ({d_rest} días restantes)",
                    "tipo": "fatal" if not gate.admisible else "alerta" if d_rest <= 5 else "plazo"
                })

        if not hitos:
            hitos.append({"fecha": fecha_str, "etiqueta": "Ingreso y Análisis Inicial en Mesa", "tipo": "inicio"})

        # 2. Checklist probatorio
        documentos = deteccion.get("documentos", []) or []
        faltantes = analisis.get("faltan", []) or []

        # 3. Citas oficiales
        citas_raw = analisis.get("citas", []) or []
        normas_raw = deteccion.get("normas", []) or []
        citas_list: List[str] = []
        for c in citas_raw:
            if isinstance(c, dict):
                citas_list.append(c.get("formato") or c.get("texto") or str(c))
            elif isinstance(c, str):
                citas_list.append(c)
        for n in normas_raw:
            if isinstance(n, dict):
                citas_list.append(f"[BCN - Ley N° {n.get('numero')}, Art. {n.get('articulos', ['1'])[0]}]")

        # 4. Plan de herramientas
        plan = analisis.get("plan", []) or []

        return cls._build_html_page(
            titulo=titulo,
            subtitulo=f"Tribunal / Fuero: {fuero} · Materia: {materia_etiqueta}",
            rol=rol_display,
            fecha=fecha_str,
            materia=materia_etiqueta,
            fuero=fuero,
            jev_decision=jev_decision,
            hitos=hitos,
            documentos=documentos,
            faltantes=faltantes,
            plan=plan,
            subgrafo=subgrafo,
            citas=citas_list,
            advertencias=analisis.get("advertencias", [])
        )

    @classmethod
    def render_brief_dashboard(
        cls,
        titulo_principal: str,
        tribunal: str,
        presuma_data: Dict[str, str],
        comparecencia: str,
        hechos: str,
        derecho: str,
        peticiones: str,
        otrosies: Optional[List[Dict[str, Any]]] = None,
        citas: Optional[List[Union[str, Dict[str, Any]]]] = None,
        jev_decision: Optional[Any] = None
    ) -> str:
        """Genera un dashboard interactivo de revisión forense para un escrito judicial (export_brief_ojv)."""
        otrosies = otrosies or []
        citas = citas or []
        materia = presuma_data.get("materia", "ORDINARIO")
        procedimiento = presuma_data.get("procedimiento", "DECLARATIVO")
        demandante = presuma_data.get("demandante", "PARTE DEMANDANTE")
        demandado = presuma_data.get("demandado", "PARTE DEMANDADA")
        fecha_str = datetime.now().strftime("%Y-%m-%d")

        # Hitos procesales derivados del escrito
        hitos: List[Dict[str, Any]] = [
            {"fecha": "Redacción", "etiqueta": f"{titulo_principal}", "tipo": "inicio"},
            {"fecha": "OJV", "etiqueta": "Ingreso a distribución / Corte", "tipo": "plazo"}
        ]

        # Checklist de secciones y otrosíes
        documentos: List[Dict[str, Any]] = [
            {"nombre": "Presuma OJV", "tipo": "Formalidad Ley 20.886", "estado": "OK"},
            {"nombre": "Comparecencia y Mandato", "tipo": "Art. 6-7 CPC", "estado": "OK"},
            {"nombre": "Capítulo I: Hechos", "tipo": "Carga de la Prueba", "estado": "OK" if hechos.strip() else "Incompleto"},
            {"nombre": "Capítulo II: Derecho", "tipo": "Fundamentación Positiva", "estado": "OK" if derecho.strip() else "Incompleto"},
            {"nombre": "Peticiones Concretas", "tipo": "Art. 254 N° 5 CPC", "estado": "OK" if peticiones.strip() else "Incompleto"},
        ]
        for ot in otrosies:
            num = ot.get("numero", "Otrosí")
            tit = ot.get("titulo", "Petición accesoria")
            documentos.append({"nombre": f"{num}: {tit}", "tipo": "Otrosí Procesal", "estado": "OK"})

        citas_list: List[str] = []
        for c in citas:
            if isinstance(c, dict):
                citas_list.append(c.get("formato") or c.get("texto") or str(c))
            elif isinstance(c, str):
                citas_list.append(c)

        return cls._build_html_page(
            titulo=f"Revisión Forense: {titulo_principal}",
            subtitulo=f"Tribunal: {tribunal} · Procedimiento: {procedimiento}",
            rol=f"Partes: {demandante} c/ {demandado}",
            fecha=fecha_str,
            materia=materia,
            fuero=tribunal,
            jev_decision=jev_decision,
            hitos=hitos,
            documentos=documentos,
            faltantes=[],
            plan=[],
            subgrafo=None,
            citas=citas_list,
            texto_escrito={
                "comparecencia": comparecencia,
                "hechos": hechos,
                "derecho": derecho,
                "peticiones": peticiones,
                "otrosies": otrosies
            }
        )

    @classmethod
    def export_dashboard(cls, html_content: str, output_path: str) -> str:
        """Guarda el contenido del dashboard en el archivo de destino y retorna la ruta absoluta."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return os.path.abspath(output_path)

    # --------------------------------------------------------------------------
    # Sub-componentes internos de renderizado (HTML / CSS / SVG)
    # --------------------------------------------------------------------------

    @classmethod
    def _build_html_page(
        cls,
        titulo: str,
        subtitulo: str,
        rol: str,
        fecha: str,
        materia: str,
        fuero: str,
        jev_decision: Optional[Any],
        hitos: List[Dict[str, Any]],
        documentos: List[Dict[str, Any]],
        faltantes: List[str],
        plan: List[Dict[str, Any]],
        subgrafo: Optional[Dict[str, Any]],
        citas: List[str],
        advertencias: Optional[List[str]] = None,
        texto_escrito: Optional[Dict[str, Any]] = None
    ) -> str:
        """Ensambla el documento HTML completo sin dependencias externas."""
        advertencias = advertencias or []

        # 1. Indicadores clave (KPIs)
        total_docs = len(documentos)
        total_faltantes = len(faltantes)
        total_citas = len(citas)

        # Semáforo de riesgo por LegalOpenJev
        estado_badge = "🟢 EN REGLA"
        estado_color = "#10b981"
        if jev_decision and hasattr(jev_decision, "noul_gates"):
            for g in jev_decision.noul_gates:
                if not g.admisible:
                    estado_badge = "🔴 PLAZO CADUCADO / CRÍTICO"
                    estado_color = "#ef4444"
                    break
                elif g.dias_restantes is not None and g.dias_restantes <= 5:
                    estado_badge = "🟠 ALERTA URGENTE (<5 DÍAS)"
                    estado_color = "#f59e0b"
        elif total_faltantes > 2:
            estado_badge = "🟡 ANTECEDENTES PENDIENTES"
            estado_color = "#f59e0b"

        # SVG Timeline
        timeline_svg = cls._render_timeline_svg(hitos)

        # SVG Risk Gauge
        gauge_svg = cls._render_risk_gauge(jev_decision)

        # HTML Escaping seguro
        titulo_esc = html.escape(titulo)
        subtitulo_esc = html.escape(subtitulo)
        rol_esc = html.escape(rol)
        fecha_esc = html.escape(fecha)
        materia_esc = html.escape(materia)
        fuero_esc = html.escape(fuero)
        compuerta_esc = html.escape(cls.COMPUERTA_TEXTO)

        # Filas de documentos
        docs_rows = []
        for idx, doc in enumerate(documentos, 1):
            if isinstance(doc, dict):
                nom = html.escape(str(doc.get("nombre") or doc.get("archivo") or f"Doc #{idx}"))
                tip = html.escape(str(doc.get("tipo") or doc.get("extension") or "Documento"))
                est = html.escape(str(doc.get("estado") or "Detectado"))
            else:
                nom = html.escape(str(doc))
                tip = "Documento"
                est = "Detectado"
            docs_rows.append(f"""
            <tr>
                <td><input type="checkbox" checked class="chk-doc" aria-label="Verificado"></td>
                <td><strong>{nom}</strong></td>
                <td><span class="badge badge-neutral">{tip}</span></td>
                <td><span class="badge badge-success">{est}</span></td>
            </tr>
            """)

        for flt in faltantes:
            flt_esc = html.escape(str(flt))
            docs_rows.append(f"""
            <tr class="row-faltante">
                <td><input type="checkbox" class="chk-doc" aria-label="Faltante"></td>
                <td><strong class="text-danger">{flt_esc}</strong></td>
                <td><span class="badge badge-warning">Requerimiento</span></td>
                <td><span class="badge badge-danger">FALTANTE</span></td>
            </tr>
            """)

        # Citas en formato Click-to-Copy
        citas_cards = []
        for idx, c in enumerate(citas, 1):
            c_esc = html.escape(c)
            citas_cards.append(f"""
            <div class="citation-pill">
                <span class="citation-text" id="cite-{idx}">{c_esc}</span>
                <button class="btn-copy" onclick="copyCitation('cite-{idx}', this)" title="Copiar cita oficial">📋 Copiar</button>
            </div>
            """)
        if not citas_cards:
            citas_cards.append("""<div class="empty-state">No se registraron citas específicas en este paso.</div>""")

        # Plan de acción o secciones del escrito
        plan_cards = []
        for p in plan:
            num = p.get("paso", "")
            herr = html.escape(str(p.get("herramienta", "")))
            mot = html.escape(str(p.get("motivo", "")))
            plan_cards.append(f"""
            <div class="plan-step">
                <div class="step-num">{num}</div>
                <div class="step-info">
                    <strong><code>{herr}</code></strong>
                    <p>{mot}</p>
                </div>
            </div>
            """)

        # Subgrafo dogmático si existe
        subgrafo_html = cls._render_subgraph_section(subgrafo)

        # Sección de texto si es un escrito
        escrito_section = ""
        if texto_escrito:
            hechos_fmt = html.escape(texto_escrito.get("hechos", "")).replace("\n", "<br>")
            derecho_fmt = html.escape(texto_escrito.get("derecho", "")).replace("\n", "<br>")
            peticiones_fmt = html.escape(texto_escrito.get("peticiones", "")).replace("\n", "<br>")
            comparecencia_fmt = html.escape(texto_escrito.get("comparecencia", ""))
            escrito_section = f"""
            <section class="card">
                <h2>📜 Contenido del Escrito Forense</h2>
                <div class="brief-box">
                    <p><strong>Comparecencia:</strong> {comparecencia_fmt}</p>
                    <hr>
                    <h3>I. Los Hechos</h3>
                    <p class="forensic-p">{hechos_fmt}</p>
                    <hr>
                    <h3>II. El Derecho</h3>
                    <p class="forensic-p">{derecho_fmt}</p>
                    <hr>
                    <h3>Por Tanto / Peticiones Concretas</h3>
                    <p class="forensic-p">{peticiones_fmt}</p>
                </div>
            </section>
            """

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo_esc} — LegalCanvas</title>
    <style>
        :root {{
            --bg-page: #f8fafc;
            --bg-card: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
            --primary: #1e3a8a;
            --primary-light: #eff6ff;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-page);
            color: var(--text-main);
            line-height: 1.5;
            padding: 24px;
        }}
        .container {{
            max-width: 1140px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px 24px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        }}
        .header-forense {{
            border-top: 4px solid var(--primary);
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 16px;
        }}
        .header-title h1 {{
            font-size: 1.5rem;
            color: var(--primary);
            font-weight: 700;
            margin-bottom: 4px;
        }}
        .header-title p {{
            color: var(--text-muted);
            font-size: 0.95rem;
        }}
        .meta-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            font-size: 0.78rem;
            font-weight: 600;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}
        .badge-status {{ background: {estado_color}20; color: {estado_color}; border: 1px solid {estado_color}40; }}
        .badge-neutral {{ background: #f1f5f9; color: #475569; }}
        .badge-success {{ background: #dcfce7; color: #166534; }}
        .badge-warning {{ background: #fef3c7; color: #92400e; }}
        .badge-danger {{ background: #fee2e2; color: #991b1b; }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
        }}
        .kpi-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        .kpi-num {{
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--primary);
            line-height: 1.2;
        }}
        .kpi-label {{
            font-size: 0.8rem;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-top: 4px;
        }}

        .gate-banner {{
            background: #fffbeb;
            border: 1.5px solid #f59e0b;
            border-radius: 6px;
            padding: 14px 18px;
            font-size: 0.88rem;
            color: #92400e;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .visual-split {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
        }}
        @media (max-width: 860px) {{
            .visual-split {{ grid-template-columns: 1fr; }}
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
            margin-top: 10px;
        }}
        th, td {{
            padding: 10px 12px;
            border-bottom: 1px solid var(--border-color);
            text-align: left;
        }}
        th {{
            background: #f8fafc;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            font-size: 0.75rem;
        }}
        tr:hover {{ background: #f8fafc; }}
        .row-faltante {{ background: #fff5f5; }}
        .text-danger {{ color: var(--danger); }}

        .citations-list {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 12px;
        }}
        .citation-pill {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #f8fafc;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 8px 12px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.85rem;
            color: #1e293b;
        }}
        .btn-copy {{
            background: #ffffff;
            border: 1px solid #cbd5e1;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.75rem;
            font-weight: 600;
            transition: all 0.15s ease;
        }}
        .btn-copy:hover {{
            background: var(--primary-light);
            border-color: var(--primary);
            color: var(--primary);
        }}

        .plan-step {{
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 10px 0;
            border-bottom: 1px solid var(--border-color);
        }}
        .step-num {{
            background: var(--primary-light);
            color: var(--primary);
            font-weight: 700;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            flex-shrink: 0;
        }}
        .step-info p {{
            font-size: 0.88rem;
            color: var(--text-muted);
            margin-top: 2px;
        }}

        .brief-box {{
            background: #fafaf9;
            border: 1px solid #e7e5e4;
            padding: 16px;
            border-radius: 6px;
            font-family: "Georgia", "Times New Roman", serif;
            font-size: 0.95rem;
            line-height: 1.6;
        }}
        .forensic-p {{
            margin: 10px 0;
            text-align: justify;
        }}
        
        .footer-note {{
            text-align: center;
            font-size: 0.78rem;
            color: var(--text-muted);
            padding: 16px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 1. CARÁTULA FORENSE -->
        <header class="card header-forense">
            <div class="header-title">
                <h1>{titulo_esc}</h1>
                <p>{subtitulo_esc}</p>
            </div>
            <div class="meta-badges">
                <span class="badge badge-status">{estado_badge}</span>
                <span class="badge badge-neutral">RIT/ROL: {rol_esc}</span>
                <span class="badge badge-neutral">FUERO: {fuero_esc}</span>
                <span class="badge badge-neutral">FECHA: {fecha_esc}</span>
            </div>
        </header>

        <!-- 2. COMPUERTA DE REVISIÓN ÉTICO-JURÍDICA -->
        <div class="gate-banner">
            <div>{compuerta_esc}</div>
        </div>

        <!-- 3. KPI RESUMEN -->
        <section class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-num">{total_docs}</div>
                <div class="kpi-label">Documentos / Autos</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-num" style="color: {'#ef4444' if total_faltantes > 0 else '#10b981'};">{total_faltantes}</div>
                <div class="kpi-label">Antecedentes Faltantes</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-num">{total_citas}</div>
                <div class="kpi-label">Citas de Ley / Doctrina</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-num" style="font-size: 1.1rem; padding-top: 10px;">{materia_esc}</div>
                <div class="kpi-label">Materia Jurídica</div>
            </div>
        </section>

        <!-- 4. LÍNEA DE TIEMPO SVG & SEMÁFORO DE RIESGO -->
        <section class="visual-split">
            <div class="card">
                <h2 style="font-size: 1.1rem; margin-bottom: 12px; color: var(--primary);">⏱️ Cronología & Plazos Fatales (SVG)</h2>
                {timeline_svg}
            </div>
            <div class="card" style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <h2 style="font-size: 1.1rem; margin-bottom: 12px; color: var(--primary);">🚦 Semáforo de Caducidad</h2>
                {gauge_svg}
            </div>
        </section>

        <!-- 5. CHECKLIST PROBATORIO & FALTANTES -->
        <section class="card">
            <h2 style="font-size: 1.1rem; margin-bottom: 8px; color: var(--primary);">📋 Checklist de Documentos y Evidencia</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width: 40px;">Cotejo</th>
                        <th>Documento / Elemento de Prueba</th>
                        <th>Naturaleza</th>
                        <th>Estado Procesal</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(docs_rows)}
                </tbody>
            </table>
        </section>

        <!-- 6. SUBGRAFO DOGMÁTICO (SI APLICA) -->
        {subgrafo_html}

        <!-- 7. CAJÓN DE CITAS OFICIALES -->
        <section class="card">
            <h2 style="font-size: 1.1rem; margin-bottom: 8px; color: var(--primary);">📚 Atribución y Citas Oficiales (Click-to-Copy)</h2>
            <div class="citations-list">
                {''.join(citas_cards)}
            </div>
        </section>

        <!-- 8. ESCRITO FORENSE (SI PROCEDE) -->
        {escrito_section}

        <!-- 9. PLAN DE ACCIÓN / DECISIÓN PROCESAL -->
        {cls._render_plan_section(plan_cards)}

        <footer class="footer-note">
            Generado con <strong>LegalCanvas</strong> · Open Legal Chile · 100% Local-First & Soberano
        </footer>
    </div>

    <script>
        function copyCitation(elementId, btn) {{
            var el = document.getElementById(elementId);
            if (!el) return;
            var text = el.innerText || el.textContent;
            navigator.clipboard.writeText(text).then(function() {{
                var original = btn.innerText;
                btn.innerText = "✓ Copiado";
                btn.style.color = "#10b981";
                btn.style.borderColor = "#10b981";
                setTimeout(function() {{
                    btn.innerText = original;
                    btn.style.color = "";
                    btn.style.borderColor = "";
                }}, 1800);
            }}).catch(function(err) {{
                console.error("Error al copiar: ", err);
            }});
        }}
    </script>
</body>
</html>"""

    @classmethod
    def _render_timeline_svg(cls, hitos: List[Dict[str, Any]]) -> str:
        """Genera una línea de tiempo horizontal en SVG puro sin librerías externas."""
        if not hitos:
            hitos = [{"fecha": "Hoy", "etiqueta": "Ingreso", "tipo": "inicio"}]

        width = 680
        height = 110
        total_puntos = len(hitos)
        step = (width - 100) / max(1, total_puntos - 1) if total_puntos > 1 else 0

        svg_parts = [
            f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" xmlns="http://www.w3.org/2000/svg">',
            f'<line x1="50" y1="50" x2="{width - 50}" y2="50" stroke="#cbd5e1" stroke-width="3" stroke-linecap="round"/>'
        ]

        for i, hito in enumerate(hitos):
            cx = 50 + (i * step) if total_puntos > 1 else width / 2
            cy = 50
            tipo = hito.get("tipo", "factico")
            color = "#10b981" if tipo == "inicio" else "#ef4444" if tipo == "fatal" else "#f59e0b" if tipo == "alerta" else "#3b82f6"
            f_esc = html.escape(str(hito.get("fecha", "")))
            e_esc = html.escape(str(hito.get("etiqueta", "")))

            # Círculo del hito
            svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="7" fill="#ffffff" stroke="{color}" stroke-width="3"/>')
            # Fecha (arriba)
            svg_parts.append(
                f'<text x="{cx}" y="{cy - 14}" font-size="10" font-weight="600" fill="#475569" text-anchor="middle">'
                f'{f_esc}</text>'
            )
            # Etiqueta (abajo)
            short_e = e_esc if len(e_esc) <= 24 else e_esc[:22] + "…"
            svg_parts.append(
                f'<text x="{cx}" y="{cy + 22}" font-size="9.5" fill="#1e293b" text-anchor="middle">'
                f'{short_e}</text>'
            )

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    @classmethod
    def _render_risk_gauge(cls, jev_decision: Optional[Any]) -> str:
        """Genera un medidor/semáforo visual en SVG puro según las compuertas de LegalOpenJev."""
        dias_restantes = 60
        plazo_total = 60
        admisible = True
        regla = "Prescripción / Caducidad"

        if jev_decision and hasattr(jev_decision, "noul_gates") and jev_decision.noul_gates:
            gate = jev_decision.noul_gates[0]
            dias_restantes = gate.dias_restantes if gate.dias_restantes is not None else 0
            plazo_total = max(1, gate.plazo_fatal_dias) if gate.plazo_fatal_dias is not None else 60
            admisible = gate.admisible
            regla = getattr(gate, "regla", getattr(gate, "regla_evaluada", "Prescripción / Caducidad"))

        pct = max(0.0, min(1.0, dias_restantes / plazo_total)) if admisible else 0.0
        color = "#10b981" if pct > 0.4 else "#f59e0b" if pct > 0.1 else "#ef4444"
        regla_short = regla.replace("plazo_caducidad_", "").replace("_", " ").upper()

        # Arco SVG de 180 grados
        return f"""
        <svg viewBox="0 0 200 130" width="200" height="130" xmlns="http://www.w3.org/2000/svg">
            <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#e2e8f0" stroke-width="16" stroke-linecap="round"/>
            <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="{color}" stroke-width="16" 
                  stroke-dasharray="251.2" stroke-dashoffset="{251.2 * (1 - pct)}" stroke-linecap="round"/>
            <text x="100" y="85" font-size="22" font-weight="700" fill="{color}" text-anchor="middle">{dias_restantes}d</text>
            <text x="100" y="105" font-size="9" fill="#64748b" text-anchor="middle">restantes de {plazo_total}d</text>
            <text x="100" y="124" font-size="8.5" font-weight="600" fill="#334155" text-anchor="middle">{html.escape(regla_short[:24])}</text>
        </svg>
        """

    @classmethod
    def _render_subgraph_section(cls, subgrafo: Optional[Dict[str, Any]]) -> str:
        """Renderiza una sección visual para los nodos del subgrafo de LegalGraphify."""
        if not subgrafo or not isinstance(subgrafo, dict):
            return ""

        inst = html.escape(str(subgrafo.get("institucion", "")))
        norma = html.escape(str(subgrafo.get("norma_fundante", "")))
        vecinos = subgrafo.get("vecinos", []) or []

        vecinos_cards = []
        for v in vecinos[:6]:
            nom = html.escape(str(v.get("nombre") or v.get("id") or ""))
            rel = html.escape(str(v.get("relacion") or "VINCULO"))
            vecinos_cards.append(f"""
            <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 12px; font-size: 0.82rem;">
                <span class="badge badge-neutral" style="font-size: 0.7rem;">{rel}</span>
                <div style="font-weight: 600; margin-top: 4px; color: #1e3a8a;">{nom}</div>
            </div>
            """)

        return f"""
        <section class="card">
            <h2 style="font-size: 1.1rem; margin-bottom: 8px; color: var(--primary);">🧠 Topología Dogmática (LegalGraphify)</h2>
            <p style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 12px;">
                Institución Canónica Central: <strong>{inst}</strong> {f'· Norma: {norma}' if norma else ''}
            </p>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px;">
                {''.join(vecinos_cards)}
            </div>
        </section>
        """

    @classmethod
    def _render_plan_section(cls, plan_cards: List[str]) -> str:
        """Renderiza el plan de acción procesal si hay pasos planificados."""
        if not plan_cards:
            return ""
        return f"""
        <section class="card">
            <h2 style="font-size: 1.1rem; margin-bottom: 12px; color: var(--primary);">🚀 Plan de Acción Procesal Recomendado</h2>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                {''.join(plan_cards)}
            </div>
        </section>
        """
