#!/usr/bin/env python3
"""
Script canónico para actualizar docs/index.html con:
1. Las 88 herramientas MCP exactas en 8 categorías.
2. Estadísticas actualizadas: 7.399 obras, 25.556 instituciones, 20.990 nodos, 51.590 aristas,
   8 portales especializados PJUD en Hugging Face y 27 skills.
3. Buscador Interactivo Multi-Corpus PJUD / Hugging Face, Calculadora Estadística del Baremo
   de Daño Moral PJUD (17 categorías en UF y CLP) y Arquitectura Data Science (Okapi BM25F +
   Personalized PageRank α=0.85 + Modelo Contradictorio Elephant-Goldfish).
4. Sección de Formación Ejecutiva, Consultoría «Llave en Mano» On-Premise y Alianzas
   Institucionales (Propuestas 1, 2 y 4) con contacto directo a pablobenavidesjorquera@gmail.com.
"""

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
INDEX_HTML_PATH = RAIZ / "docs" / "index.html"


def build_all_tools_dataset():
    from mcp_server import TOOLS

    categories = {
        "consulta_maestra": "Protocolo & Citas",
        "cita_texto": "Protocolo & Citas",
        "agent_list": "Agentes & IA Jurídica",
        "agent_run": "Agentes & IA Jurídica",
        "agent_export_subagents": "Agentes & IA Jurídica",
        "skills_listar": "Agentes & IA Jurídica",
        "skill_ver": "Agentes & IA Jurídica",
        "caso_analizar": "Agentes & IA Jurídica",
        "caso_ejecutar": "Agentes & IA Jurídica",
        "doctrina_search": "Doctrina & Graphify",
        "doctrina_get_institucion": "Doctrina & Graphify",
        "doctrina_list_obras": "Doctrina & Graphify",
        "doctrina_ingestar_documento": "Doctrina & Graphify",
        "grafo_ver_corpus": "Doctrina & Graphify",
        "grafo_ver_caso": "Doctrina & Graphify",
        "generar_grafo_vinculos": "Doctrina & Graphify",
        "huggingface_search_dataset": "Doctrina & Graphify",
        "graphify_resumen_comunidades": "Doctrina & Graphify",
        "graphify_consulta_subgrafo": "Doctrina & Graphify",
        "graphify_trazar_camino": "Doctrina & Graphify",
        "graphify_explicar_institucion": "Doctrina & Graphify",
        "graphify_analizar_impacto": "Doctrina & Graphify",
        "graphify_god_nodes": "Doctrina & Graphify",
        "biblioteca_compilar_manifiesto": "Doctrina & Graphify",
        "bcn_get_codigo": "BCN Normativo",
        "bcn_get_ley": "BCN Normativo",
        "bcn_get_ley_historica": "BCN Normativo",
        "bcn_get_codigo_historico": "BCN Normativo",
        "cbr_estudio_titulos": "CBR Inmobiliario",
        "cbr_checklist_documentos": "CBR Inmobiliario",
        "pjud_search_jurisprudencia": "Tribunales & PJUD",
        "pjud_analizar_sentencia": "Tribunales & PJUD",
        "pjud_interpretar_proveido": "Tribunales & PJUD",
        "recurso_proteccion_generar": "Tribunales & PJUD",
        "critique_documento": "Tribunales & PJUD",
        "generar_documento": "Tribunales & PJUD",
        "ocr_plan_documento": "Tribunales & PJUD",
        "ocr_extract_pdf": "Tribunales & PJUD",
        "cpc_validar_mandato": "Tribunales & PJUD",
        "cgr_search_jurisprudencia": "Regulatorio & Fiscal",
        "cgr_search_auditorias": "Regulatorio & Fiscal",
        "dt_search_doctrina": "Regulatorio & Fiscal",
        "cmf_search_normativa": "Regulatorio & Fiscal",
        "cmf_buscar_sanciones": "Regulatorio & Fiscal",
        "sii_search_circulares": "Regulatorio & Fiscal",
        "sii_buscar_resoluciones_y_oficios": "Regulatorio & Fiscal",
        "sii_oficios_por_anio": "Regulatorio & Fiscal",
        "sii_descargar_oficio": "Regulatorio & Fiscal",
        "sii_leer_documento": "Regulatorio & Fiscal",
        "sii_actos_regionales": "Regulatorio & Fiscal",
        "sii_convenios_internacionales": "Regulatorio & Fiscal",
        "sii_jurisprudencia_judicial": "Regulatorio & Fiscal",
        "tdlc_search_jurisprudencia": "Regulatorio & Fiscal",
        "tdlc_buscar_icg_y_dictamenes": "Regulatorio & Fiscal",
        "sma_search_sancionatorios": "Regulatorio & Fiscal",
        "entes_consultar_organo": "Regulatorio & Fiscal",
        "busqueda_universal": "Regulatorio & Fiscal",
    }

    tools_list = []
    for t in TOOLS:
        name = t["name"]
        cat = categories.get(name, "Suite & Utilidades")
        desc = t.get("description", "").strip()
        first_line = desc.split("\n")[0].strip()
        if len(first_line) > 130:
            first_line = first_line[:127] + "..."
        tools_list.append(
            {
                "name": name,
                "category": cat,
                "description": first_line,
                "full_description": desc,
            }
        )
    return tools_list


def build_baremo_dataset():
    baremo_path = RAIZ / "data" / "jurisprudencia" / "baremo_dano_moral.jsonl"
    if not baremo_path.exists():
        return []
    rows = [json.loads(line) for line in baremo_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows.sort(key=lambda x: -x.get("total_casos_analizados", 0))
    out = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "parentesco": r["parentesco"],
                "casos": r["total_casos_analizados"],
                "uf": r["estadisticas_uf"],
                "clp": r["estadisticas_clp"],
                "cita": r["cita"],
                "muestra": r.get("fallos_muestra", [])[:4],
            }
        )
    return out


def build_pjud_corpus_samples():
    files = [
        ("lineas_cs", "Líneas Jurisprudenciales CS", "cs_lineas_jurisprudenciales.jsonl", 6),
        ("salud_cs", "Salud e Isapres CS", "cs_salud.jsonl", 6),
        ("extranjeria_cs", "Compendio Extranjería CS", "cs_extranjeria.jsonl", 5),
        ("ddhh", "Derechos Humanos PJUD", "cs_ddhh.jsonl", 6),
        ("genero", "Secretaría de Género PJUD", "pjud_genero.jsonl", 6),
    ]
    samples = []
    for col_id, col_label, fname, limit in files:
        fpath = RAIZ / "data" / "jurisprudencia" / fname
        if not fpath.exists():
            continue
        count = 0
        for line in fpath.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            samples.append(
                {
                    "coleccion": col_id,
                    "coleccion_nombre": col_label,
                    "rol": row.get("rol", ""),
                    "fecha": row.get("fecha", ""),
                    "tribunal": row.get("tribunal", "Excma. Corte Suprema"),
                    "sala": row.get("sala", ""),
                    "caratula": (row.get("caratula") or "")[:120],
                    "materia": (row.get("materia") or row.get("descriptores") or "")[:180],
                    "extracto": (row.get("extracto_relevante") or row.get("sumario") or "")[:280],
                    "cita": row.get("cita", ""),
                    "url": row.get("url_origen") or "https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile",
                }
            )
            count += 1
            if count >= limit:
                break
    return samples


NEW_CSS_STYLES = """
    /* --- Buscador Multi-Corpus, Baremo & Formación Consultoría --- */
    .corpus-hub-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 14px;
      margin-bottom: 26px;
    }
    @media (max-width: 980px) {
      .corpus-hub-grid { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 560px) {
      .corpus-hub-grid { grid-template-columns: 1fr; }
    }
    .portal-stat-card {
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px 18px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: all 0.2s ease;
    }
    .portal-stat-card:hover {
      border-color: #0284c7;
      box-shadow: 0 8px 24px rgba(2, 132, 199, 0.08);
      transform: translateY(-2px);
    }
    .portal-stat-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 8px;
    }
    .portal-stat-badge {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 999px;
      background: #e0f2fe;
      color: #0369a1;
    }
    .portal-stat-title {
      font-weight: 700;
      font-size: 14.5px;
      color: var(--foreground);
      margin-bottom: 4px;
    }
    .portal-stat-desc {
      font-size: 12.5px;
      color: var(--muted);
      line-height: 1.45;
      margin-bottom: 10px;
    }
    .portal-stat-link {
      font-size: 11.5px;
      font-family: var(--font-mono);
      color: #0284c7;
      text-decoration: none;
      font-weight: 600;
    }
    .portal-stat-link:hover { text-decoration: underline; }

    .baremo-Explorer-box {
      background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
      border: 1px solid #cbd5e1;
      border-radius: 16px;
      padding: 28px;
      margin-bottom: 28px;
      box-shadow: 0 12px 32px rgba(15, 23, 42, 0.05);
    }
    .baremo-header-row {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 20px;
      padding-bottom: 16px;
      border-bottom: 1px solid #e2e8f0;
    }
    .baremo-select {
      padding: 10px 16px;
      border-radius: 10px;
      border: 1px solid #0284c7;
      background: #f0f9ff;
      color: #0f172a;
      font-weight: 600;
      font-size: 14px;
      font-family: var(--font-sans);
      cursor: pointer;
      outline: none;
      min-width: 270px;
    }
    .baremo-instances-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-bottom: 20px;
    }
    @media (max-width: 860px) {
      .baremo-instances-grid { grid-template-columns: 1fr; }
    }
    .baremo-inst-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 18px;
      position: relative;
      overflow: hidden;
    }
    .baremo-inst-card.pi { border-top: 4px solid #0284c7; }
    .baremo-inst-card.ca { border-top: 4px solid #059669; }
    .baremo-inst-card.cs { border-top: 4px solid #7c3aed; }
    .baremo-inst-title {
      font-size: 12px;
      font-family: var(--font-mono);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-weight: 700;
      color: #475569;
      margin-bottom: 6px;
      display: flex;
      justify-content: space-between;
    }
    .baremo-mediana-uf {
      font-family: var(--font-display);
      font-size: 26px;
      font-weight: 700;
      color: #0f172a;
      line-height: 1.15;
    }
    .baremo-mediana-clp {
      font-size: 13px;
      color: #059669;
      font-weight: 600;
      font-family: var(--font-mono);
      margin-bottom: 12px;
    }
    .baremo-range-bar {
      height: 8px;
      border-radius: 999px;
      background: #e2e8f0;
      position: relative;
      margin: 10px 0;
      overflow: hidden;
    }
    .baremo-range-fill {
      height: 100%;
      border-radius: 999px;
      background: linear-gradient(90deg, #38bdf8, #0284c7, #7c3aed);
    }
    .baremo-stat-row {
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      color: #475569;
      margin-top: 4px;
      font-family: var(--font-mono);
    }
    .baremo-samples-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12.5px;
      margin-top: 12px;
    }
    .baremo-samples-table th,
    .baremo-samples-table td {
      padding: 8px 10px;
      text-align: left;
      border-bottom: 1px solid #e2e8f0;
    }
    .baremo-samples-table th {
      font-family: var(--font-mono);
      font-size: 11px;
      text-transform: uppercase;
      color: #64748b;
      background: #f8fafc;
    }
    .ds-triad-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 18px;
      margin-top: 24px;
    }
    @media (max-width: 880px) {
      .ds-triad-grid { grid-template-columns: 1fr; }
    }
    .ds-card {
      background: #07281f;
      color: #f4f8f6;
      border: 1px solid rgba(74, 222, 128, 0.28);
      border-radius: 14px;
      padding: 22px;
    }
    .ds-card-tag {
      font-family: var(--font-mono);
      font-size: 11px;
      color: #86efac;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 8px;
      display: block;
    }
    .ds-card-title {
      font-family: var(--font-display);
      font-size: 18px;
      font-weight: 700;
      margin-bottom: 8px;
      color: #ffffff;
    }
    .ds-card-desc {
      font-size: 13px;
      line-height: 1.55;
      color: rgba(255, 255, 255, 0.8);
    }

    /* --- Propuestas 1, 2 y 4 (Formación & Consultoría) --- */
    .consulting-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 22px;
      margin-top: 24px;
    }
    @media (max-width: 960px) {
      .consulting-grid { grid-template-columns: 1fr; }
    }
    .consulting-card {
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 28px 24px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: all 0.25s ease;
      position: relative;
    }
    .consulting-card.featured {
      border: 2px solid #0284c7;
      background: linear-gradient(180deg, #ffffff 0%, #f0f9ff 100%);
      box-shadow: 0 14px 34px rgba(2, 132, 199, 0.10);
    }
    .consulting-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      padding: 4px 10px;
      border-radius: 999px;
      margin-bottom: 14px;
      width: fit-content;
    }
    .consulting-title {
      font-family: var(--font-display);
      font-size: 21px;
      font-weight: 700;
      color: var(--foreground);
      margin-bottom: 10px;
      line-height: 1.25;
    }
    .consulting-desc {
      font-size: 13.5px;
      color: var(--muted);
      line-height: 1.6;
      margin-bottom: 16px;
      text-align: justify;
    }
    .consulting-list {
      list-style: none;
      margin-bottom: 22px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .consulting-list li {
      font-size: 13px;
      color: #1e293b;
      line-height: 1.5;
      display: flex;
      align-items: flex-start;
      gap: 8px;
      text-align: justify;
    }
    .consulting-cta {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      width: 100%;
      padding: 12px 18px;
      border-radius: 10px;
      font-weight: 600;
      font-size: 13.5px;
      text-decoration: none;
      transition: all 0.2s ease;
    }
    .consulting-cta.primary {
      background: #0284c7;
      color: #ffffff;
    }
    .consulting-cta.primary:hover {
      background: #0369a1;
    }
    .consulting-cta.dark {
      background: #062a22;
      color: #ffffff;
    }
    .consulting-cta.dark:hover {
      background: #0b3d32;
    }
"""


NEW_SECTIONS_HTML = """  <!-- Step 04B: Buscador Interactivo Multi-Corpus, Baremo Daño Moral PJUD & Motor Data Science -->
  <section id="buscador-corpus" class="step-section">
    <span class="eyebrow-step">Data Science Jurídico · Hugging Face &amp; PJUD en Vivo</span>
    <h2 class="step-h2">Buscador Multi-Corpus &amp; Calculadora Oficial del Baremo de Daño Moral PJUD</h2>
    <p class="step-desc">
      Explora en tiempo real las <strong>8 colecciones jurisprudenciales especializadas del Poder Judicial</strong> integradas en Hugging Face (<code>pablobenavidesj/doctrina-jurisprudencia-chile</code>) y calcula rangos indemnizatorios en <strong>UF y pesos chilenos (CLP)</strong> sobre <strong>2.137 sentencias reales sistematizadas por parentesco e instancia</strong> (Primera Instancia, Cortes de Apelaciones y Excma. Corte Suprema).
    </p>

    <!-- 8 Portales Especializados PJUD Grid -->
    <div class="corpus-hub-grid">
      <div class="portal-stat-card">
        <div>
          <div class="portal-stat-top">
            <span class="portal-stat-badge">70.536 Fichas</span>
            <span>🏛️</span>
          </div>
          <div class="portal-stat-title">Corte Suprema General</div>
          <p class="portal-stat-desc">Sentencias de todas las salas de la Excma. Corte Suprema con rol, fecha, ministros, descriptores y sumario.</p>
        </div>
        <a href="https://juris.pjud.cl/busqueda?Corte_Suprema" target="_blank" rel="noreferrer" class="portal-stat-link">juris.pjud.cl/Corte_Suprema →</a>
      </div>

      <div class="portal-stat-card">
        <div>
          <div class="portal-stat-top">
            <span class="portal-stat-badge">457 Líneas</span>
            <span>🧭</span>
          </div>
          <div class="portal-stat-title">Líneas Jurisprudenciales CS</div>
          <p class="portal-stat-desc">Criterios doctrinales rectores sistematizados por la Dirección de Estudios de la Corte Suprema.</p>
        </div>
        <a href="https://juris.pjud.cl/busqueda?Lineas_Jurisprudenciales" target="_blank" rel="noreferrer" class="portal-stat-link">Lineas_Jurisprudenciales →</a>
      </div>

      <div class="portal-stat-card">
        <div>
          <div class="portal-stat-top">
            <span class="portal-stat-badge">311 Fallos</span>
            <span>🏥</span>
          </div>
          <div class="portal-stat-title">Compendio Salud / Isapres</div>
          <p class="portal-stat-desc">Jurisprudencia de la Tercera Sala Constitucional sobre adecuación de planes, GES, tabla de factores y medicamentos de alto costo.</p>
        </div>
        <a href="https://juris.pjud.cl/busqueda?Salud_CS" target="_blank" rel="noreferrer" class="portal-stat-link">juris.pjud.cl/Salud_CS →</a>
      </div>

      <div class="portal-stat-card">
        <div>
          <div class="portal-stat-top">
            <span class="portal-stat-badge">162 Fallos</span>
            <span>🛂</span>
          </div>
          <div class="portal-stat-title">Compendio de Extranjería</div>
          <p class="portal-stat-desc">Sentencias sobre expulsiones administrativas, arraigo familiar, debido proceso migratorio y refugio (Ley N.° 21.325).</p>
        </div>
        <a href="https://juris.pjud.cl/busqueda?Compendio_Extranjer%C3%ADa" target="_blank" rel="noreferrer" class="portal-stat-link">Compendio_Extranjería →</a>
      </div>

      <div class="portal-stat-card">
        <div>
          <div class="portal-stat-top">
            <span class="portal-stat-badge">418 Fallos</span>
            <span>🕊️</span>
          </div>
          <div class="portal-stat-title">Derechos Humanos PJUD</div>
          <p class="portal-stat-desc">Buscador especializado de sentencias de Derechos Humanos, crímenes de lesa humanidad, imprescriptibilidad y estándares CIDH.</p>
        </div>
        <a href="https://busddhh.pjud.cl/buscador/sentencias-derechos-humanos" target="_blank" rel="noreferrer" class="portal-stat-link">busddhh.pjud.cl →</a>
      </div>

      <div class="portal-stat-card">
        <div>
          <div class="portal-stat-top">
            <span class="portal-stat-badge">188 Registros</span>
            <span>💜</span>
          </div>
          <div class="portal-stat-title">Secretaría de Género PJUD</div>
          <p class="portal-stat-desc">Repositorio oficial y Concurso de Sentencias con Perspectiva de Género, no discriminación e interseccionalidad.</p>
        </div>
        <a href="https://secretariadegenero.pjud.cl/index.php/repositorio" target="_blank" rel="noreferrer" class="portal-stat-link">secretariadegenero.pjud.cl →</a>
      </div>

      <div class="portal-stat-card">
        <div>
          <div class="portal-stat-top">
            <span class="portal-stat-badge">17 Vínculos · 2.137 Fallos</span>
            <span>📊</span>
          </div>
          <div class="portal-stat-title">Baremo de Daño Moral PJUD</div>
          <p class="portal-stat-desc">Estadística oficial PJUD-UdeC de indemnizaciones por daño moral por muerte en UF y CLP según vínculo de parentesco.</p>
        </div>
        <a href="https://baremo.pjud.cl/BAREMOWEB/" target="_blank" rel="noreferrer" class="portal-stat-link">baremo.pjud.cl/BAREMOWEB →</a>
      </div>

      <div class="portal-stat-card">
        <div>
          <div class="portal-stat-top">
            <span class="portal-stat-badge">1.853 Fallos Íntegros</span>
            <span>🌿</span>
          </div>
          <div class="portal-stat-title">TC (967) &amp; Ambientales (886)</div>
          <p class="portal-stat-desc">Sentencias a texto completo del Tribunal Constitucional y de los tres Tribunales Ambientales (1TA, 2TA y 3TA) + 79 boletines.</p>
        </div>
        <a href="https://huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile" target="_blank" rel="noreferrer" class="portal-stat-link">Dataset Hugging Face →</a>
      </div>
    </div>

    <!-- Interactive Baremo Calculator -->
    <div class="baremo-Explorer-box">
      <div class="baremo-header-row">
        <div>
          <span class="claim-tag" style="background:#e0f2fe; color:#0369a1; border-color:#bae6fd;">[ESTADÍSTICA OFICIAL PJUD · ARTS. 2314 Y 2329 CC]</span>
          <h3 style="font-family: var(--font-display); font-size: 22px; font-weight: 700; color: #0f172a; margin-top: 6px;">
            Calculadora Estadística del Baremo de Daño Moral por Muerte (UF y CLP)
          </h3>
        </div>
        <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
          <label for="baremoParentescoSelect" style="font-size: 13px; font-weight: 600; color: #334155;">Vínculo del Demandante:</label>
          <select id="baremoParentescoSelect" class="baremo-select"></select>
        </div>
      </div>

      <div class="baremo-instances-grid" id="baremoInstancesGrid"></div>

      <div style="background: #f1f5f9; border-radius: 10px; padding: 14px 16px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px;">
        <div style="font-size: 12.5px; color: #1e293b;">
          <strong>Corchete Oficial verificable:</strong> <code id="baremoCitationCode" style="background:#ffffff; padding:3px 8px; border-radius:4px; border:1px solid #cbd5e1; font-family:var(--font-mono);"></code>
        </div>
        <button id="btnCopyBaremoCita" class="btn-socratic-action" style="padding: 7px 14px; font-size: 12px;">
          📋 Copiar Cita Oficial
        </button>
      </div>

      <div style="margin-top: 18px;">
        <div style="font-size: 12px; font-family: var(--font-mono); text-transform: uppercase; color: #475569; font-weight: 700; margin-bottom: 6px;">
          Sentencias Reales Destacadas en este Vínculo (con descarga directa en baremo.pjud.cl):
        </div>
        <div style="overflow-x: auto;">
          <table class="baremo-samples-table" id="baremoSamplesTable">
            <thead>
              <tr>
                <th>Rol / Instancia</th>
                <th>Corte de Apelaciones</th>
                <th>Juzgado de Origen</th>
                <th>Fecha</th>
                <th>Monto (UF / CLP)</th>
                <th>Sentencia Oficial</th>
              </tr>
            </thead>
            <tbody id="baremoSamplesBody"></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Interactive Multi-Corpus Sample Explorer -->
    <div style="background: #ffffff; border: 1px solid var(--border); border-radius: 16px; padding: 24px;">
      <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px;">
        <div>
          <h3 style="font-family: var(--font-display); font-size: 19px; font-weight: 700; color: var(--foreground);">
            Explorador Rápido de Fallos Especializados (Líneas CS, Salud, Extranjería, DD.HH. y Género)
          </h3>
          <p style="font-size: 13px; color: var(--muted);">
            Filtra por colección especializada o busca por materia, rol o descriptor para previsualizar el formato canónico con cita oficial.
          </p>
        </div>
        <div class="mcp-filter-bar" id="pjudCorpusFilterBar" style="margin-bottom: 0;">
          <button class="filter-btn active" data-pjud-col="all">Todas las Colecciones</button>
          <button class="filter-btn" data-pjud-col="lineas_cs">Líneas CS</button>
          <button class="filter-btn" data-pjud-col="salud_cs">Salud / Isapres</button>
          <button class="filter-btn" data-pjud-col="extranjeria_cs">Extranjería</button>
          <button class="filter-btn" data-pjud-col="ddhh">Derechos Humanos</button>
          <button class="filter-btn" data-pjud-col="genero">Perspectiva de Género</button>
        </div>
      </div>

      <input type="text" id="pjudCorpusSearchInput" class="search-input-legal" style="width: 100%; margin-bottom: 16px;" placeholder="Buscar en fallos especializados (ej: isapre, ges, expulsión, arraigo, lesa humanidad, violencia, cuidado personal)..." />

      <div class="tools-grid" id="pjudCorpusGrid"></div>
    </div>

    <!-- Data Science Architecture Triad -->
    <div class="ds-triad-grid">
      <div class="ds-card">
        <span class="ds-card-tag">1. Recuperación Léxico-Morfológica</span>
        <div class="ds-card-title">Okapi BM25F + 4-Gramas en Memoria</div>
        <p class="ds-card-desc">
          El motor de sincronización con Hugging Face (<code>online_library_sync.py</code>) indexa las 25.556 instituciones con pesos IDF por campo (título ×3.5, palabras clave ×2.5, ruta ×1.8) y saturación no lineal (k1=1.5, b=0.75), más un índice de 4-gramas de caracteres y <code>ThreadPoolExecutor</code> paralelo para tolerar variaciones morfológicas sin latencia de red.
        </p>
      </div>

      <div class="ds-card">
        <span class="ds-card-tag">2. Topología de Grafos Jurídicos</span>
        <div class="ds-card-title">Personalized PageRank (α = 0.85)</div>
        <p class="ds-card-desc">
          <code>LegalGraphifyEngine</code> resuelve el nodo semilla ponderando la especificidad IDF de cada término jurídico y ejecuta <em>Random Walk with Restart</em> sobre el ego-subgrafo de 2 saltos (<code>ranking_ppr_subgrafo</code>), priorizando los artículos BCN y fallos de la Corte Suprema estructuralmente más centrales para la institución consultada.
        </p>
      </div>

      <div class="ds-card">
        <span class="ds-card-tag">3. Revisión Adversarial Aislada</span>
        <div class="ds-card-title">Modelo Contradictorio Elephant-Goldfish</div>
        <p class="ds-card-desc">
          Inspirado en <code>google/elephant-goldfish-model</code>, la herramienta <code>critique_documento(modo="goldfish")</code> separa al agente redactor (<em>Elefante</em>, con memoria del caso) del auditor contradictorio (<em>Goldfish</em>, con amnesia deliberada de las excusas del litigante), auditando ineptitud del libelo (Art. 303 N.° 4 CPC), caducidad, prescripción y orfandad probatoria.
        </p>
      </div>
    </div>
  </section>

  <!-- Step 05B: Formación Ejecutiva, Consultoría On-Premise y Alianzas Institucionales -->
  <section id="formacion-consultoria" class="step-section">
    <span class="eyebrow-step">Sostenibilidad Open Source · Formación, Consultoría &amp; Alianzas</span>
    <h2 class="step-h2">Capacitación Ejecutiva, Despliegue Privado On-Premise y Alianzas Académicas</h2>
    <p class="step-desc">
      El núcleo de <strong>Open Legal Chile</strong> (sus 88 herramientas MCP, 19 agentes autónomos, 27 skills y el corpus en Hugging Face) es un <strong>bien público digital 100 % gratuito bajo licencia Apache 2.0</strong>. Para estudios jurídicos, gerencias legales, organismos públicos y universidades que buscan dominar la IA jurídica soberana o desplegar infraestructura privada en sus propios servidores, ofrecemos tres modalidades de trabajo directo:
    </p>

    <div class="consulting-grid">
      <!-- Propuesta 1 -->
      <div class="consulting-card featured">
        <div>
          <span class="consulting-badge" style="background:#0284c7; color:#ffffff;">🎓 Propuesta 1 · Más Solicitada</span>
          <h3 class="consulting-title">Charlas Magistrales, Bootcamps y Capacitación In-Company</h3>
          <p class="consulting-desc">
            Programas de formación ejecutiva y talleres prácticos diseñados para socios y equipos de estudios jurídicos, fiscalías corporativas, reparticiones del Estado, colegios de abogados y postgrados universitarios.
          </p>
          <ul class="consulting-list">
            <li><span>✅</span><span><strong>IA Jurídica sin Alucinaciones:</strong> Triangulación estricta entre ley positiva (BCN), doctrina canónica (Hugging Face) y jurisprudencia vinculante (PJUD, CGR, DT, SII).</span></li>
            <li><span>✅</span><span><strong>Litigación OJV y Auditoría Goldfish:</strong> Redacción forense en Word (.docx) con citas a pie de página, cálculo de daño moral con el Baremo PJUD y examen contradictorio previo al ingreso judicial.</span></li>
            <li><span>✅</span><span><strong>Dominio de Harnesses de Vanguardia:</strong> Configuración práctica de Google Antigravity, Claude Code, Cursor y automatización de despacho con Google Workspace MCP.</span></li>
          </ul>
        </div>
        <a href="mailto:pablobenavidesjorquera@gmail.com?subject=Consulta%20Charla%20o%20Capacitaci%C3%B3n%20In-Company%20-%20Open%20Legal%20Chile" class="consulting-cta primary">
          ✉️ Solicitar Programa de Capacitación
        </a>
      </div>

      <!-- Propuesta 2 -->
      <div class="consulting-card">
        <div>
          <span class="consulting-badge" style="background:#dcfce7; color:#166534;">🛡️ Propuesta 2 · Zero Data Leak</span>
          <h3 class="consulting-title">Consultoría «Llave en Mano» y Despliegue Privado On-Premise</h3>
          <p class="consulting-desc">
            Instalación y personalización de una instancia soberana de Open Legal Chile dentro de los servidores locales, nube privada (VPC) o estaciones de trabajo de su estudio jurídico o gerencia legal.
          </p>
          <ul class="consulting-list">
            <li><span>🔒</span><span><strong>Ingesta Privada del Conocimiento del Estudio:</strong> Indexación con Okapi BM25F, SQLite FTS5 y subgrafos <code>LegalGraphify</code> sobre sus propios contratos históricos, informes en derecho y escritos judiciales.</span></li>
            <li><span>🔒</span><span><strong>Plantillas y Estilo Institucional:</strong> Adaptación de <code>generar_documento</code> a los formatos, membretes, matrices de riesgo y cláusulas corporativas del despacho.</span></li>
            <li><span>🔒</span><span><strong>Secreto Profesional Absoluto:</strong> Ejecución 100 % local o con modelos privados (Ollama / vLLM / endpoints corporativos), en estricto cumplimiento de la Ley N.° 21.719 de Datos Personales.</span></li>
          </ul>
        </div>
        <a href="mailto:pablobenavidesjorquera@gmail.com?subject=Consulta%20Implementaci%C3%B3n%20On-Premise%20Llave%20en%20Mano%20-%20Open%20Legal%20Chile" class="consulting-cta dark">
          🛡️ Agendar Diagnóstico de Arquitectura
        </a>
      </div>

      <!-- Propuesta 4 -->
      <div class="consulting-card">
        <div>
          <span class="consulting-badge" style="background:#f3e8ff; color:#7e22ce;">🤝 Propuesta 4 · Academia &amp; I+D</span>
          <h3 class="consulting-title">Alianzas Universitarias, Clínicas Jurídicas y Patrocinios</h3>
          <p class="consulting-desc">
            Convenios de colaboración académica, patrocinios institucionales y postulación conjunta a fondos de investigación y bienes públicos digitales para democratizar el acceso a la justicia en Chile.
          </p>
          <ul class="consulting-list">
            <li><span>🏛️</span><span><strong>Laboratorios de IA y Simulador de Grado:</strong> Despliegue del Simulador Socrático de Examen de Grado y herramientas de Lenguaje Claro en facultades de Derecho y Clínicas Jurídicas (CAJ).</span></li>
            <li><span>🏛️</span><span><strong>Digitalización y Co-Edición Científica:</strong> Incorporación de revistas jurídicas universitarias, anuarios y compendios sectoriales al mapa de conocimiento en Hugging Face.</span></li>
            <li><span>🏛️</span><span><strong>Patrocinios y Fondos Concursables:</strong> Alianzas para proyectos ANID, innovación pública e infraestructura jurídica abierta a nivel latinoamericano.</span></li>
          </ul>
        </div>
        <a href="mailto:pablobenavidesjorquera@gmail.com?subject=Alianza%20Acad%C3%A9mica%20o%20Patrocinio%20Institucional%20-%20Open%20Legal%20Chile" class="consulting-cta dark">
          🤝 Proponer Alianza o Patrocinio
        </a>
      </div>
    </div>

    <!-- Direct Contact Banner -->
    <div style="margin-top: 26px; background: linear-gradient(135deg, #062a22 0%, #0b3d32 100%); border-radius: 16px; padding: 24px 28px; color: #ffffff; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 18px; border: 1px solid rgba(74, 222, 128, 0.3);">
      <div>
        <div style="font-size: 12px; font-family: var(--font-mono); color: #86efac; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">
          Contacto Directo con el Autor y Director del Proyecto
        </div>
        <div style="font-family: var(--font-display); font-size: 20px; font-weight: 700; color: #ffffff;">
          Pablo Benavides Jorquera · <a href="mailto:pablobenavidesjorquera@gmail.com" style="color: #38bdf8; text-decoration: underline;">pablobenavidesjorquera@gmail.com</a>
        </div>
        <div style="font-size: 13px; color: rgba(255, 255, 255, 0.78); margin-top: 4px;">
          Escríbenos directamente para coordinar charlas magistrales, talleres prácticos para tu equipo legal, despliegues privados on-premise o convenios universitarios.
        </div>
      </div>
      <div style="display: flex; gap: 10px; flex-wrap: wrap;">
        <a href="mailto:pablobenavidesjorquera@gmail.com" class="btn-hero-primary" style="background: #38bdf8; color: #062a22; font-weight: 700; border: none;">
          📬 pablobenavidesjorquera@gmail.com
        </a>
      </div>
    </div>
  </section>
"""


def main():
    content = INDEX_HTML_PATH.read_text(encoding="utf-8")

    # 1. Update Tools Dataset (88 tools)
    tools_data = build_all_tools_dataset()
    tools_json = json.dumps(tools_data, ensure_ascii=False, indent=2)
    content = re.sub(
        r"const ALL_TOOLS = \[.*?\];",
        f"const ALL_TOOLS = {tools_json};",
        content,
        flags=re.DOTALL,
    )

    # 2. Update Tool Filter Buttons (88 tools)
    old_filter_bar = r'<div class="mcp-filter-bar" id="toolFilterBar">.*?</div>'
    new_filter_bar = """<div class="mcp-filter-bar" id="toolFilterBar">
        <button class="filter-btn active" data-cat="all">Todas (88)</button>
        <button class="filter-btn" data-cat="Protocolo & Citas">Protocolo & Citas (2)</button>
        <button class="filter-btn" data-cat="Agentes & IA Jurídica">Agentes & IA Jurídica (7)</button>
        <button class="filter-btn" data-cat="Doctrina & Graphify">Doctrina & Graphify (15)</button>
        <button class="filter-btn" data-cat="BCN Normativo">BCN Normativo (4)</button>
        <button class="filter-btn" data-cat="CBR Inmobiliario">CBR Inmobiliario (2)</button>
        <button class="filter-btn" data-cat="Tribunales & PJUD">Tribunales & PJUD (9)</button>
        <button class="filter-btn" data-cat="Regulatorio & Fiscal">Regulatorio & Fiscal (17)</button>
        <button class="filter-btn" data-cat="Suite & Utilidades">Suite & Utilidades (32)</button>
      </div>"""
    content = re.sub(old_filter_bar, new_filter_bar, content, count=1, flags=re.DOTALL)

    # 3. Update Navigation Links (Header & Mobile Drawer)
    if 'href="#buscador-corpus"' not in content:
        content = content.replace(
            '<a href="#herramientas" class="nav-link">88 Herramientas MCP</a>',
            '<a href="#buscador-corpus" class="nav-link" style="color:#38bdf8; font-weight:600;">🔎 Buscador &amp; Baremo</a>\n        <a href="#herramientas" class="nav-link">88 Herramientas MCP</a>\n        <a href="#formacion-consultoria" class="nav-link" style="color:#86efac; font-weight:600;">🎓 Capacitación &amp; Consultoría</a>',
        )
        content = content.replace(
            '<a href="#herramientas" class="mobile-nav-item">⚡ 88 Herramientas MCP</a>',
            '<a href="#buscador-corpus" class="mobile-nav-item">🔎 Buscador Multi-Corpus &amp; Baremo PJUD</a>\n        <a href="#herramientas" class="mobile-nav-item">⚡ 88 Herramientas MCP</a>\n        <a href="#formacion-consultoria" class="mobile-nav-item">🎓 Capacitación, Consultoría &amp; Alianzas</a>',
        )

    # 4. Update stats (88 tools, 27 skills)
    content = content.replace(
        '<div class="stat-num" data-target="87" data-suffix="">87</div>',
        '<div class="stat-num" data-target="88" data-suffix="">88</div>',
    )
    content = content.replace(
        '<span class="suite-layer-title">⚡ Servidor MCP Nativo (87 Tools)</span>',
        '<span class="suite-layer-title">⚡ Servidor MCP Nativo (88 Tools)</span>',
    )
    content = content.replace(
        '<span class="claim-tag">[18 SKILLS]</span>',
        '<span class="claim-tag">[27 SKILLS]</span>',
    )
    content = content.replace(
        '<span class="suite-layer-meta">18 Skills · Espacio casos/ · Grafo Local</span>',
        '<span class="suite-layer-meta">27 Skills · Espacio casos/ · Grafo Local</span>',
    )

    # 5. Add new CSS styles
    if "/* --- Buscador Multi-Corpus, Baremo & Formación Consultoría --- */" not in content:
        content = content.replace("</style>", NEW_CSS_STYLES + "\n  </style>")

    # 6. Insert #buscador-corpus and #formacion-consultoria before <footer class="footer-section">
    if 'id="buscador-corpus"' not in content:
        content = content.replace(
            '  <!-- Footer (Graphify Aesthetic) -->\n  <footer class="footer-section">',
            NEW_SECTIONS_HTML + '\n  <!-- Footer (Graphify Aesthetic) -->\n  <footer class="footer-section">',
        )

    # 7. Update Footer with direct contact email pablobenavidesjorquera@gmail.com
    if "pablobenavidesjorquera@gmail.com" not in content.split('<footer class="footer-section">')[-1]:
        content = content.replace(
            '<span class="claim-tag" style="margin-top: 8px;">Licencia Apache 2.0 · Open Source</span>',
            '<span class="claim-tag" style="margin-top: 8px;">Licencia Apache 2.0 · Open Source</span>\n        <p style="font-size: 12.5px; color: rgba(255,255,255,0.85); margin-top: 10px; font-family: var(--font-mono);">📬 Contacto &amp; Consultoría: <a href="mailto:pablobenavidesjorquera@gmail.com" style="color: #38bdf8; text-decoration: underline;">pablobenavidesjorquera@gmail.com</a></p>',
        )
        content = content.replace(
            '<li><a href="#graphify" class="footer-link">Grafo jurídico</a></li>',
            '<li><a href="#graphify" class="footer-link">Grafo jurídico</a></li>\n          <li><a href="#buscador-corpus" class="footer-link">Baremo Daño Moral PJUD</a></li>\n          <li><a href="#formacion-consultoria" class="footer-link">Capacitación &amp; Consultoría On-Premise</a></li>',
        )

    # 8. Clean up duplicated JS inside .filter-btn and inject Baremo + Multi-Corpus interactive logic
    baremo_data = build_baremo_dataset()
    pjud_samples = build_pjud_corpus_samples()
    baremo_json = json.dumps(baremo_data, ensure_ascii=False)
    pjud_samples_json = json.dumps(pjud_samples, ensure_ascii=False)

    # Fix broken filter-btn block where interactive_scripts was accidentally injected earlier
    broken_pattern = re.compile(
        r"// Filter Buttons listeners\s*document\.querySelectorAll\('\.filter-btn'\)\.forEach\(btn => \{.*?// Mobile Drawer Menu Toggle",
         flags=re.DOTALL,
    )
    clean_filter_js = """// Filter Buttons listeners
    document.querySelectorAll('#toolFilterBar .filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#toolFilterBar .filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentCategory = btn.dataset.cat;
        renderTools();
      });
    });

    const toolSearchEl = document.getElementById('toolSearchInput');
    if (toolSearchEl) {
      toolSearchEl.addEventListener('input', (e) => {
        currentSearchTerm = e.target.value.toLowerCase().trim();
        renderTools();
      });
    }

    // Mobile Drawer Menu Toggle"""

    if broken_pattern.search(content):
        content = broken_pattern.sub(clean_filter_js, content, count=1)

    baremo_and_corpus_js = f"""
    // ==========================================
    // 4. BAREMO DAÑO MORAL PJUD & MULTI-CORPUS EXPLORER
    // ==========================================
    (function initBaremoAndCorpusExplorer() {{
      const BAREMO_DATA = {baremo_json};
      const PJUD_SAMPLES = {pjud_samples_json};

      const selectEl = document.getElementById('baremoParentescoSelect');
      const gridEl = document.getElementById('baremoInstancesGrid');
      const citaEl = document.getElementById('baremoCitationCode');
      const samplesBody = document.getElementById('baremoSamplesBody');
      const btnCopyCita = document.getElementById('btnCopyBaremoCita');

      function fmtUF(val) {{
        if (!val || val <= 0) return 'Sin registros';
        return val.toLocaleString('es-CL', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }}) + ' UF';
      }}

      function fmtCLP(val) {{
        if (!val || val <= 0) return '—';
        return '$' + Math.round(val).toLocaleString('es-CL') + ' CLP';
      }}

      function renderBaremoCategory(item) {{
        if (!item || !gridEl) return;
        const instances = [
          {{ key: 'primera_instancia', label: 'Primera Instancia (Juzgados Civiles)', cls: 'pi' }},
          {{ key: 'corte_apelaciones', label: 'Cortes de Apelaciones (2ª Instancia)', cls: 'ca' }},
          {{ key: 'corte_suprema', label: 'Excma. Corte Suprema (Casación)', cls: 'cs' }}
        ];

        gridEl.innerHTML = instances.map(inst => {{
          const uf = (item.uf && item.uf[inst.key]) || {{ n: 0, min: 0, p25: 0, mediana: 0, promedio: 0, p75: 0, max: 0 }};
          const clp = (item.clp && item.clp[inst.key]) || {{ n: 0, mediana: 0 }};
          const maxRef = Math.max(uf.max || 1, 1);
          const leftPct = Math.min(85, Math.max(4, Math.round(((uf.p25 || 0) / maxRef) * 100)));
          const widthPct = Math.min(100 - leftPct, Math.max(12, Math.round((((uf.p75 || 0) - (uf.p25 || 0)) / maxRef) * 100)));

          return `
            <div class="baremo-inst-card ${{inst.cls}}">
              <div class="baremo-inst-title">
                <span>${{inst.label}}</span>
                <span style="color:#0284c7;">n = ${{uf.n}} fallos</span>
              </div>
              <div class="baremo-mediana-uf">${{fmtUF(uf.mediana)}}</div>
              <div class="baremo-mediana-clp">Mediana: ${{fmtCLP(clp.mediana)}}</div>
              <div class="baremo-range-bar" title="Rango Intercuartil P25 - P75">
                <div class="baremo-range-fill" style="margin-left:${{leftPct}}%; width:${{widthPct}}%;"></div>
              </div>
              <div class="baremo-stat-row">
                <span>P25: ${{fmtUF(uf.p25)}}</span>
                <span>P75: ${{fmtUF(uf.p75)}}</span>
              </div>
              <div class="baremo-stat-row">
                <span>Promedio: ${{fmtUF(uf.promedio)}}</span>
                <span>Máx: ${{fmtUF(uf.max)}}</span>
              </div>
            </div>
          `;
        }}).join('');

        if (citaEl) citaEl.textContent = item.cita;
        if (samplesBody) {{
          samplesBody.innerHTML = (item.muestra || []).map(m => `
            <tr>
              <td style="font-family:var(--font-mono); font-weight:600; color:#0284c7;">Rol ${{m.rol}}</td>
              <td>${{m.corte_apelaciones || '—'}}</td>
              <td>${{m.juzgado_origen || '—'}}</td>
              <td style="font-family:var(--font-mono);">${{m.fecha || '—'}}</td>
              <td style="font-family:var(--font-mono); font-weight:600;">${{fmtUF(m.monto_uf)}} <span style="color:#64748b; font-weight:400;">(${{fmtCLP(m.monto_clp)}})</span></td>
              <td><a href="${{m.url_descarga_sentencia}}" target="_blank" rel="noreferrer" style="color:#059669; font-family:var(--font-mono); font-weight:600; text-decoration:none;">📄 Descargar Fallo</a></td>
            </tr>
          `).join('');
        }}
      }}

      if (selectEl && BAREMO_DATA.length) {{
        selectEl.innerHTML = BAREMO_DATA.map((b, idx) =>
          `<option value="${{idx}}">${{b.parentesco}} (${{b.casos}} sentencias analizadas — Mediana PI: ${{b.uf.primera_instancia.mediana}} UF)</option>`
        ).join('');
        selectEl.addEventListener('change', (e) => {{
          const item = BAREMO_DATA[parseInt(e.target.value, 10)] || BAREMO_DATA[0];
          renderBaremoCategory(item);
        }});
        renderBaremoCategory(BAREMO_DATA[0]);
      }}

      if (btnCopyCita && citaEl) {{
        btnCopyCita.addEventListener('click', () => {{
          navigator.clipboard.writeText(citaEl.textContent || '').then(() => {{
            const orig = btnCopyCita.textContent;
            btnCopyCita.textContent = '✅ ¡Cita Copiada!';
            setTimeout(() => {{ btnCopyCita.textContent = orig; }}, 2000);
          }});
        }});
      }}

      // Multi-Corpus PJUD Sample Explorer
      const pjudGrid = document.getElementById('pjudCorpusGrid');
      const pjudSearch = document.getElementById('pjudCorpusSearchInput');
      let currentPjudCol = 'all';
      let currentPjudTerm = '';

      function renderPjudSamples() {{
        if (!pjudGrid) return;
        const filtered = PJUD_SAMPLES.filter(s => {{
          const mCol = (currentPjudCol === 'all') || (s.coleccion === currentPjudCol);
          const mTerm = !currentPjudTerm ||
            s.rol.toLowerCase().includes(currentPjudTerm) ||
            s.caratula.toLowerCase().includes(currentPjudTerm) ||
            s.materia.toLowerCase().includes(currentPjudTerm) ||
            s.extracto.toLowerCase().includes(currentPjudTerm) ||
            s.coleccion_nombre.toLowerCase().includes(currentPjudTerm);
          return mCol && mTerm;
        }}).slice(0, 9);

        pjudGrid.innerHTML = filtered.map(s => `
          <div class="tool-card" style="display:flex; flex-direction:column; justify-content:space-between;">
            <div>
              <div class="tool-header-row">
                <span class="tool-name">Rol ${{s.rol}}</span>
                <span class="tool-cat-badge">${{s.coleccion_nombre}}</span>
              </div>
              <div style="font-size:12px; font-weight:600; color:#0f172a; margin:6px 0 4px;">${{s.caratula || s.materia}}</div>
              <p class="tool-desc" style="font-size:12px; line-height:1.45;">${{s.extracto || s.materia}}</p>
            </div>
            <div style="margin-top:10px; padding-top:8px; border-top:1px solid #f1f5f9; display:flex; justify-content:space-between; align-items:center; gap:8px;">
              <code style="font-size:10.5px; color:#0369a1; background:#f0f9ff; padding:2px 6px; border-radius:4px;">${{s.cita}}</code>
              <a href="${{s.url}}" target="_blank" rel="noreferrer" style="font-size:11px; font-family:var(--font-mono); color:#059669; text-decoration:none; font-weight:600;">Ver fuente →</a>
            </div>
          </div>
        `).join('');
      }}

      document.querySelectorAll('[data-pjud-col]').forEach(btn => {{
        btn.addEventListener('click', () => {{
          document.querySelectorAll('[data-pjud-col]').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          currentPjudCol = btn.dataset.pjudCol;
          renderPjudSamples();
        }});
      }});

      if (pjudSearch) {{
        pjudSearch.addEventListener('input', (e) => {{
          currentPjudTerm = e.target.value.toLowerCase().trim();
          renderPjudSamples();
        }});
      }}

      renderPjudSamples();
    }})();
"""

    if "initBaremoAndCorpusExplorer" not in content:
        content = content.replace("</script>\n</body>", baremo_and_corpus_js + "\n  </script>\n</body>")

    INDEX_HTML_PATH.write_text(content, encoding="utf-8")
    print(f"Successfully updated {INDEX_HTML_PATH}")
    print(f"Total tools in updated HTML: {len(tools_data)}")
    print(f"Total Baremo categories embedded: {len(baremo_data)}")
    print(f"Total PJUD specialized samples embedded: {len(pjud_samples)}")


if __name__ == "__main__":
    main()
