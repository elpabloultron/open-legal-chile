#!/usr/bin/env python3
"""
Script para generar la versión consolidada de 26 láminas de la presentación de Open Legal Chile
para la Universidad de Los Lagos.
"""

import re
import os

HTML_PATH = "/home/pablo/Escritorio/charla-open-legal-chile/presentacion.html"

# 1. Definición de las 26 láminas
LAMINAS = [
    # ── L1 · Portada ──
    ("""
<div class="a" style="position:absolute;inset:0"><canvas class="red" id="redHero"></canvas></div>
<div class="encima a" style="margin-top:auto">
  <div class="ceja">Facultad de Ciencias Jurídicas y Políticas · Universidad de Los Lagos</div>
  <h1 class="a">Open Legal Chile</h1>
</div>
<div class="encima a" style="margin-top:auto;max-width:880px">
  <p class="a" style="font-size:clamp(16px,2vw,22px);line-height:1.48;color:#E8E5DD">
    Inteligencia artificial soberana, Model Context Protocol y doctrina canónica para el derecho chileno.
  </p>
</div>
<div class="encima a" style="margin-top:auto">
  <div class="regla a"></div>
  <p class="a" style="font-size:12.6px;color:#9AA7B4;margin-top:10px">
    Pablo Benavides · Septiembre 2026 · Producción Estable (v1.6.5) · 259 pruebas en verde
  </p>
</div>""", "red"),

    # ── L2 · Génesis y Propósito (2, 3 y 4) ──
    ("""
<div class="a"><div class="ceja">Génesis y Propósito</div><h2 class="a">Por qué nació, para qué es y el puente hacia las fuentes</h2>
<p class="a" style="margin-top:6px">La IA comercial inventa y extrapola categorías foráneas; Open Legal Chile ancla el modelo a las fuentes del Estado.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1.05fr 1.05fr 0.9fr;gap:14px;align-items:stretch">
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="color:var(--rojo);font-size:13.5px">Por qué nació · La falla del mercado</b>
    <div id="pqChips" style="display:flex;gap:4px;flex-wrap:wrap"></div>
    <div class="consola" id="pqConsola" style="min-height:95px;font-size:11px;padding:8px"></div>
    <p class="gris" id="pqNota" style="font-size:11.2px;min-height:2.2em">—</p>
  </div>
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="color:var(--azul);font-size:13.5px">Para qué es · Los dos caminos</b>
    <div id="praPartes" style="display:flex;flex-direction:column;gap:6px"></div>
  </div>
  <div class="tarjeta a acento" style="display:flex;flex-direction:column;justify-content:center;padding:16px;border-left-color:var(--bronce)">
    <div class="ceja" style="color:var(--bronce)">El principio rector</div>
    <p class="serif" id="puenteFrase" style="font-size:clamp(15px,1.4vw,18px);line-height:1.4;color:var(--tinta);margin:12px 0">
      «La inteligencia artificial soberana no sustituye al jurista: eleva su rigor técnico y lo acerca a sus fuentes oficiales».
    </p>
    <div id="puentePistas" style="display:flex;flex-direction:column;gap:5px"></div>
  </div>
</div>""", "porque paraQue puente"),

    # ── L3 · El Mapa de la suite (5) ──
    ("""
<div class="a"><div class="ceja">Los cimientos</div><h2 class="a">El mapa: de la IA a tus fuentes</h2>
<p class="a" style="margin-top:6px">Cinco niveles ordenados: cada uno hace lo suyo y ninguno se confunde.</p></div>
<div class="cuerpo" style="justify-content:center">
  <div style="display:flex;flex-direction:column;gap:11px;max-width:880px;width:100%" id="mapaPistas"></div>
  <p class="a gris" id="mapaNota" style="text-align:center;font-size:12.7px;min-height:2em;margin-top:6px">—</p>
</div>""", "mapa"),

    # ── L4 · Límites del LLM y Riesgo Deontológico (6, 7 y 8) ──
    ("""
<div class="a"><div class="ceja">Fundamentos Teóricos</div><h2 class="a">Arquitectura matemática del LLM, límites y riesgo deontológico</h2>
<p class="a" style="margin-top:6px">El modelo es un calculador probabilístico de tokens; sin anclaje normativo oficial, la alucinación es inevitable.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <div style="display:flex;justify-content:space-between;align-items:baseline">
      <b style="font-size:13.2px;color:var(--tinta)">1 · ¿Qué es un LLM por dentro? (Vaswani 2017)</b>
      <span class="chip" style="font-size:10.5px">Softmax / Entropía</span>
    </div>
    <div class="consola" id="llmConsola" style="min-height:100px;font-size:11.2px;padding:8px"></div>
    <p class="gris" id="llmNota" style="font-size:11.5px;min-height:2em">—</p>
    <div style="border-top:1px solid var(--linea);padding-top:6px">
      <b style="font-size:12px;color:var(--rojo)">Riesgo forense: Mata v. Avianca (2023)</b>
      <p style="font-size:11px;color:var(--gris);margin-top:2px">Sanción disciplinaria por citar jurisprudencia inexistente. En Chile: deber de lealtad procesal (Art. 72 CPC) y secreto profesional (Art. 247 CP).</p>
    </div>
  </div>
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="font-size:13.2px;color:var(--tinta)">2 · Los 4 límites estructurales del modelo aislado</b>
    <div class="consola" id="limConsola" style="min-height:90px;font-size:11.2px;padding:8px"></div>
    <div style="height:6px;background:rgba(14,22,33,.08);border-radius:4px;overflow:hidden">
      <div id="limBarra" style="height:100%;background:var(--rojo);width:0%;transition:width 1.2s"></div>
    </div>
    <p class="gris" id="limNota" style="font-size:11.5px;min-height:2em">—</p>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
      <div id="limOlvido" style="display:flex;flex-direction:column;gap:4px"></div>
      <div id="limArchivo" style="display:flex;flex-direction:column;gap:4px"></div>
    </div>
  </div>
</div>""", "llm limites riesgo"),

    # ── L5 · ReAct y Harness (9, 10 y 11) ──
    ("""
<div class="a"><div class="ceja">Arquitectura Agéntica</div><h2 class="a">Del motor estocástico al agente gobernado: ReAct + Harness</h2>
<p class="a" style="margin-top:6px">Sustituir la adivinación probabilística por un método científico auditable de cuatro fases.</p></div>
<div class="cuerpo" style="display:flex;flex-direction:column;gap:14px">
  <div class="tarjeta a" style="padding:12px">
    <b style="font-size:13px;color:var(--tinta)">El Ciclo ReAct (Yao et al., 2022): Razonamiento, Acción y Observación</b>
    <div id="bucleNodos" style="display:flex;gap:8px;margin-top:8px"></div>
    <p class="gris" id="bucleNota" style="font-size:12px;margin-top:7px;min-height:1.6em">—</p>
  </div>
  <div class="tarjeta a" style="padding:12px">
    <div style="display:flex;justify-content:space-between;align-items:baseline">
      <b style="font-size:13px;color:var(--tinta)">El Harness (Arnés de Gobernanza Forense)</b>
      <span class="chip" style="font-size:11px;border-color:var(--bronce)">Claude Code · Google Antigravity · OLC</span>
    </div>
    <div id="harPartes" style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:8px"></div>
  </div>
</div>""", "bucle harness"),

    # ── L6 · MCP: El Estándar Abierto (12 y 13) ──
    ("""
<div class="a"><div class="ceja">Interoperabilidad</div><h2 class="a">Model Context Protocol: el estándar abierto de conexión</h2>
<p class="a" style="margin-top:6px">El estándar abierto (Anthropic/comunidad) que conecta cualquier LLM con herramientas locales.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1fr 1.15fr;gap:18px">
  <div style="display:flex;flex-direction:column;gap:9px">
    <div class="tarjeta a acento">
      <b>El USB-C de la inteligencia artificial</b>
      <p>Un solo conector universal para todo el software legal. Open Legal Chile expone 75 herramientas tipadas.</p>
    </div>
    <div id="mcpPistas" style="display:flex;flex-direction:column;gap:6px"></div>
    <p class="gris" id="mcpNota" style="font-size:12px;min-height:1.8em">—</p>
  </div>
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:6px">
    <b style="font-size:12.6px;color:var(--tinta)">Llamada real en vivo: JSON-RPC 2.0 sobre stdio</b>
    <div class="consola" id="mcpConsola" style="min-height:220px;font-size:11.4px"></div>
  </div>
</div>""", "mcp mcpDetalle"),

    # ── L7 · Herramientas, Skills y Agentes (14, 15 y 16) ──
    ("""
<div class="a"><div class="ceja">Los cimientos</div><h2 class="a">Herramienta, skill y agente: quién es quién</h2>
<p class="a" style="margin-top:6px">Tres conceptos distintos que la jerga comercial suele confundir. Así se entienden en un estudio jurídico.</p></div>
<div class="cuerpo" style="justify-content:center">
  <div class="tarjeta a" style="padding:0;overflow:hidden">
    <table style="width:100%;border-collapse:collapse" id="comparaTabla"></table>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:10px" class="a">
    <div class="tarjeta" id="toolTarjeta" style="font-family:monospace;font-size:11.8px;padding:9px 13px"></div>
    <div class="tarjeta" style="padding:9px 13px">
      <b style="font-size:12.8px">La regla del flujo:</b>
      <p style="font-size:12px;color:var(--gris);margin-top:3px">El <b>agente</b> consulta su <b>skill</b> (manual procesal), ejecuta la <b>herramienta</b> oficial y entrega el borrador con la fuente exacta para revisión del abogado.</p>
    </div>
  </div>
</div>""", "compara tool"),

    # ── L8 · Arquitectura por Capas (17) ──
    ("""
<div class="a"><div class="ceja">Los cimientos</div><h2 class="a">Todo junto, por capas: La anatomía de Open Legal Chile</h2>
<p class="a" style="margin-top:6px">De abajo hacia arriba: cada capa descansa sobre la anterior y ninguna se salta.</p></div>
<div class="cuerpo" style="justify-content:center">
  <div style="display:flex;flex-direction:column;gap:8px;max-width:820px;width:100%">
    <div class="tarjeta a acento" style="border-left-color:var(--tinta)"><b>5 · El abogado patrocinante</b> — revisa, califica y firma con su ClaveÚnica o firma electrónica avanzada (Ley 20.886). La responsabilidad es indelegable.</div>
    <div class="tarjeta a acento" style="border-left-color:var(--bronce)"><b>4 · Skills y reglas de procedimiento</b> — manuales forenses: compuerta humana obligatoria, subsunción tripartita y prohibición de Common Law.</div>
    <div class="tarjeta a acento" style="border-left-color:var(--azul)"><b>3 · Herramientas y servidor MCP</b> — 75 funciones tipadas con acceso a BCN, CGR, DT, PJUD, TC, CMF y el corpus canónico.</div>
    <div class="tarjeta a acento" style="border-left-color:var(--verde)"><b>2 · El Harness (arnés)</b> — gestiona memoria del caso, sandbox estricto de confidencialidad y rastro de auditoría inmutable.</div>
    <div class="tarjeta a acento" style="border-left-color:var(--gris)"><b>1 · El motor de lenguaje (LLM)</b> — procesa sintaxis, redacta y traduce; no inventa hechos ni asume normas.</div>
  </div>
</div>""", ""),

    # ── L9 · Separador Parte 2 (18) ──
    ("""
<div class="a" style="position:absolute;inset:0"><canvas class="red" id="redSeccion"></canvas></div>
<div class="encima a" style="margin-top:auto">
  <div class="ceja" style="color:var(--bronce2)">Parte 2</div>
  <h1 class="a" style="font-size:clamp(36px,5.4vw,70px)">El conocimiento</h1>
</div>
<div class="encima a" style="margin-top:auto;max-width:840px">
  <p class="a" style="color:#C9CDD4">El corpus chileno en Markdown · cómo se construyó el grafo · el ahorro de tokens
  medido · y cómo operan las citas.</p>
</div>""", "red2"),

    # ── L10 · RAG Plano vs. GraphRAG Ontológico y Ahorro Medido (19, 21 y 22) ──
    ("""
<div class="a"><div class="ceja">El conocimiento</div><h2 class="a">RAG plano vs. GraphRAG ontológico: ahorro del 74,1 %</h2>
<p class="a" style="margin-top:6px">Trocear textos legales a ciegas (*chunking* plano) separa la regla de su excepción; el grafo preserva la sistematicidad.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1.1fr 1fr;gap:20px">
  <div style="display:flex;flex-direction:column;gap:12px">
    <div class="grid2">
      <div class="a"><div class="num" data-contador="17006">0</div><small>nodos: normas, fallos y doctrina</small></div>
      <div class="a"><div class="num" data-contador="18710">0</div><small>aristas tipadas (citas y relaciones)</small></div>
      <div class="a"><div class="num" data-contador="358">0</div><small>comunidades temáticas (Leiden)</small></div>
      <div class="a"><div class="num" data-contador="74.1" data-decimales="1" data-sufijo=" %">0</div><small>reducción mediana de tokens auditada</small></div>
    </div>
    <div class="tarjeta a" style="padding:10px 14px">
      <div class="fila"><span class="etq">RAG ingenuo</span><span class="pista-bar"><span class="barra-i b1" data-barra="100"></span></span><span class="val">113.458 tokens</span></div>
      <div class="fila"><span class="etq">GraphRAG OLC</span><span class="pista-bar"><span class="barra-i b2" data-barra="2"></span></span><span class="val">123 tokens (113,6x)</span></div>
      <p class="gris" id="ahorroNota" style="font-size:11.8px;margin-top:6px;min-height:1.5em">—</p>
    </div>
  </div>
  <div class="tarjeta a" style="display:flex;flex-direction:column;justify-content:center;align-items:center;padding:10px">
    <canvas id="cvEgo" width="600" height="380" style="width:100%;height:auto"></canvas>
    <p class="gris" style="font-size:11.8px;text-align:center;margin-top:4px">Ego-network de una institución: sólo viaja el vecindario relevante</p>
  </div>
</div>""", "miniGrafo ahorro"),

    # ── L11 · Construcción del Grafo (20) ──
    ("""
<div class="a"><div class="ceja">El conocimiento</div><h2 class="a">Cómo se construyó el grafo de conocimiento</h2>
<p class="a" style="margin-top:6px">De los tratados en papel y PDFs al mapa ontológico navegable de la República.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1fr 1.1fr;gap:22px">
  <ul class="lista" id="gPasos">
    <li>1 · <b>58 tratados y 21 guías de la Academia Judicial</b> en OCR pericial.</li>
    <li>2 · <b>Markdown canónico</b> con fichas institucionales y definiciones RAE/ASALE.</li>
    <li>3 · Cada institución, norma y fallo es un <b>nodo estructurado</b> (17.006 nodos).</li>
    <li>4 · Las remisiones cruzadas y citas jurisprudenciales son las <b>aristas</b> (18.710 relaciones).</li>
    <li>5 · <b>358 comunidades temáticas</b> detectadas mediante algoritmo de Leiden.</li>
    <li>6 · <b>369 artículos en la Wiki Doctrinal</b> para ingesta ultra-rápida por agentes.</li>
  </ul>
  <div class="tarjeta a" style="padding:8px"><canvas id="cvGrafo" width="900" height="600" style="width:100%;height:auto;display:block"></canvas></div>
</div>""", "grafo"),

    # ── L12 · Trazabilidad y Citas en Word (23, 24 y 25) ──
    ("""
<div class="a"><div class="ceja">Trazabilidad y Entrega</div><h2 class="a">Trazabilidad procesal: de la consulta al escrito en Word</h2>
<p class="a" style="margin-top:6px">El sistema no inventa: triangula tres pilares y entrega un documento editable con citas a pie de página.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1.05fr 1.15fr;gap:18px">
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="font-size:13px;color:var(--tinta)">Estándar de citación formal</b>
    <div id="citasPasos" style="display:flex;flex-direction:column;gap:6px"></div>
    <p class="gris" id="citasNota" style="font-size:11.8px;min-height:2.2em">—</p>
    <div class="chip" style="border-color:var(--verde);background:#F0F7F4;font-size:11.5px">
      ✓ Documento de trabajo en <b>Word (.docx)</b> para revisión y edición del letrado
    </div>
  </div>
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="font-size:13px;color:var(--tinta)">El caso real: de punta a punta</b>
    <div id="casoPasos" style="display:flex;flex-direction:column;gap:6px"></div>
    <p class="gris" id="casoNota" style="font-size:11.8px;min-height:2.2em">—</p>
  </div>
</div>""", "citas caso"),

    # ── L13 · Separador Parte 3 (26) ──
    ("""
<div class="a" style="position:absolute;inset:0"><canvas class="red" id="redHerramientas"></canvas></div>
<div class="encima a" style="margin-top:auto">
  <div class="ceja" style="color:var(--bronce2)">Parte 3</div>
  <h1 class="a" style="font-size:clamp(36px,5.4vw,70px)">Las herramientas</h1>
</div>
<div class="encima a" style="margin-top:auto;max-width:840px">
  <p class="a" style="color:#C9CDD4">75 funciones tipadas · 16 conectores oficiales · 19 agentes especializados.</p>
</div>""", "red3"),

    # ── L14 · Conectores Oficiales del Estado (27 y 28) ──
    ("""
<div class="a"><div class="ceja">Conectividad Oficial</div><h2 class="a">De dónde salen los datos: 10 conectores contra el Estado</h2>
<p class="a" style="margin-top:6px">Conexión directa a bases de datos públicas, sin intermediarios y con caché local.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1fr 1.1fr;gap:20px">
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="font-size:13px;color:var(--tinta)">El viaje de una consulta oficial</b>
    <div id="apiViaje" style="display:flex;flex-direction:column;gap:6px"></div>
    <p class="gris" id="apiNota" style="font-size:11.8px;min-height:2em">—</p>
  </div>
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="font-size:13px;color:var(--tinta)">Los conectores oficiales de la suite</b>
    <div id="conNodos" style="display:grid;grid-template-columns:1fr 1fr;gap:6px"></div>
    <p class="gris" id="conNota" style="font-size:11.8px;min-height:2em">—</p>
  </div>
</div>""", "api conectores"),

    # ── L15 · Catálogo de 75 Herramientas y 19 Agentes (29 y 30) ──
    ("""
<div class="a"><div class="ceja">Capacidades de la Suite</div><h2 class="a">75 herramientas oficiales y 19 agentes especializados</h2>
<p class="a" style="margin-top:6px">Cobertura forense integral distribuida en familias funcionales y roles agénticos.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1.05fr 1fr;gap:18px">
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="font-size:13px;color:var(--tinta)">Familias de herramientas</b>
    <div id="herGrid" style="display:flex;flex-direction:column;gap:5px"></div>
    <p class="gris" id="herNota" style="font-size:11.8px;min-height:1.8em">—</p>
  </div>
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="font-size:13px;color:var(--tinta)">19 Agentes especializados</b>
    <div id="ageGrid" style="display:grid;grid-template-columns:1fr 1fr;gap:5px"></div>
    <p class="gris" id="ageNota" style="font-size:11.8px;min-height:1.8em">—</p>
  </div>
</div>""", "herramientas agentes"),

    # ── L16 · Mesa de Entrada y Redacción Procesal (31 y 32) ──
    ("""
<div class="a"><div class="ceja">Operativa Forense</div><h2 class="a">Mesa de entrada inteligente y generación procesal</h2>
<p class="a" style="margin-top:6px">El letrado ingresa el caso en lenguaje natural; el agente clasifica, planifica y redacta conforme a la OJV.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1fr 1fr;gap:18px">
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="font-size:13px;color:var(--tinta)">Mesa de entrada: caso_analizar</b>
    <div class="consola" id="mesaConsola" style="min-height:180px;font-size:11.2px"></div>
    <p class="gris" id="mesaNota" style="font-size:11.8px;min-height:2em">—</p>
  </div>
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="font-size:13px;color:var(--tinta)">Estructura procesal de escritos (Ley 20.886)</b>
    <div id="docPasos" style="display:flex;flex-direction:column;gap:6px"></div>
    <p class="gris" id="docNota" style="font-size:11.8px;min-height:2em">—</p>
  </div>
</div>""", "mesa documentos"),

    # ── L17 · Doctrina Canónica e Interrogación de Subgrafos (33 y 34) ──
    ("""
<div class="a"><div class="ceja">Dogmática y Grafos</div><h2 class="a">Doctrina canónica e interrogación de subgrafos</h2>
<p class="a" style="margin-top:6px">Búsqueda BM25 sobre 11 853 instituciones y trazabilidad topológica de deducción.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1fr 1.05fr;gap:18px">
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="font-size:13px;color:var(--tinta)">Búsqueda dogmática (doctrina_search)</b>
    <div id="docBusqueda" style="display:flex;flex-direction:column;gap:6px"></div>
    <p class="gris" id="docNota" style="font-size:11.8px;min-height:2em">—</p>
  </div>
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="font-size:13px;color:var(--tinta)">Consultas al grafo (LegalGraphify)</b>
    <div id="ghPasos" style="display:flex;flex-direction:column;gap:6px"></div>
    <p class="gris" id="ghNota" style="font-size:11.8px;min-height:2em">—</p>
  </div>
</div>""", "doctrina grafoHerramientas"),

    # ── L18 · Docencia, Clínica y Hugging Face (35 y 36) ──
    ("""
<div class="a"><div class="ceja">Ecosistema Académico</div><h2 class="a">Docencia, clínica jurídica y Hugging Face Hub</h2>
<p class="a" style="margin-top:6px">Formación de pregrado y democratización científica del corpus chileno.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1fr 1.15fr;gap:18px">
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="font-size:13px;color:var(--tinta)">Pregrado, Grado y Clínica</b>
    <div id="estPasos" style="display:flex;flex-direction:column;gap:6px"></div>
    <p class="gris" id="estNota" style="font-size:11.8px;min-height:2em">—</p>
  </div>
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="font-size:13px;color:var(--tinta)">Hugging Face: Dataset público y Space 3D</b>
    <div id="hfViaje" style="display:flex;flex-direction:column;gap:6px"></div>
    <div id="hfExtra" style="display:flex;gap:6px;flex-wrap:wrap"></div>
    <p class="gris" id="hfNota" style="font-size:11.8px;min-height:2em">—</p>
  </div>
</div>""", "estudio huggingface"),

    # ── L19 · Cumplimiento y Plazos Fatales (37) ──
    ("""
<div class="a"><div class="ceja">Vigilancia Procesal</div><h2 class="a">Vigilancia procesal, radar normativo y plazos fatales</h2>
<p class="a" style="margin-top:6px">Monitoreo continuo de proveídos en la OJV y cómputo de días hábiles del Art. 66 CPC.</p></div>
<div class="cuerpo" style="justify-content:center">
  <div style="display:flex;flex-direction:column;gap:10px;max-width:860px;width:100%" id="cumPasos"></div>
  <p class="a gris" id="cumNota" style="text-align:center;font-size:12.7px;min-height:2em;margin-top:8px">—</p>
</div>""", "cumplimiento"),

    # ── L20 · Separador Parte 4 (38) ──
    ("""
<div class="a" style="position:absolute;inset:0"><canvas class="red" id="redPrivacidad"></canvas></div>
<div class="encima a" style="margin-top:auto">
  <div class="ceja" style="color:var(--bronce2)">Parte 4</div>
  <h1 class="a" style="font-size:clamp(36px,5.4vw,70px)">Privacidad y secreto profesional</h1>
</div>
<div class="encima a" style="margin-top:auto;max-width:840px">
  <p class="a" style="color:#C9CDD4">Soberanía local · el expediente no sale · derechos ARCO · y la compuerta humana.</p>
</div>""", "red5"),

    # ── L21 · Soberanía de Datos y ARCO (39, 40 y 41) ──
    ("""
<div class="a"><div class="ceja">Soberanía y Privacidad</div><h2 class="a">Soberanía de datos: el caso nunca sale del estudio</h2>
<p class="a" style="margin-top:6px">Garantía estricta de secreto profesional (Art. 247 CP) y tramitación de derechos ARCO (Ley 19.628 y 21.719).</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1fr 1fr;gap:18px">
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="font-size:13px;color:var(--tinta)">Las 4 fronteras de confidencialidad en disco</b>
    <div id="frBorde" style="display:flex;flex-direction:column;gap:6px"></div>
    <p class="gris" id="frNota" style="font-size:11.8px;min-height:2em">—</p>
  </div>
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px">
    <b style="font-size:13px;color:var(--tinta)">Derechos ARCO y auditoría de seguridad</b>
    <div id="arcoChips" style="display:flex;gap:4px"></div>
    <div class="consola" id="arcoConsola" style="min-height:85px;font-size:11px;padding:8px"></div>
    <p class="gris" id="arcoNota" style="font-size:11.8px;min-height:2em">—</p>
    <div id="saleSellos" style="display:flex;gap:4px;flex-wrap:wrap"></div>
    <ul id="saleSi" style="display:none"><li></li></ul><ul id="saleNo" style="display:none"><li></li></ul>
  </div>
</div>""", "frontera arco sale"),

    # ── L22 · Secreto Profesional y Compuerta Humana (42) ──
    ("""
<div class="a"><div class="ceja">Deontología Forense</div><h2 class="a">Secreto profesional y la compuerta humana indelegable</h2>
<p class="a" style="margin-top:6px">El sistema no firma nada: propone, se auto-critica en 5 dimensiones y espera el visado del letrado.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1.05fr 1fr;gap:22px">
  <ul class="lista a" style="align-self:center">
    <li><b>El deber primero:</b> El secreto profesional (Art. 247 CP) y la confidencialidad mandan sobre la comodidad técnica.</li>
    <li><b>Compuerta Human-in-the-Loop:</b> Ningún escrito sale sin visado formal; el abogado patrocina y asume la responsabilidad.</li>
    <li><b>Auto-crítica en 5 dimensiones:</b> Legalidad positiva, doctrina canónica, estructura OJV, coherencia fáctica y ética.</li>
    <li><b>Rastro inmutable de auditoría:</b> Registro exacto de herramientas invocadas, fuentes contrastadas y argumentos descartados.</li>
  </ul>
  <div class="tarjeta a" style="display:flex;flex-direction:column;gap:8px;justify-content:center">
    <div id="cpFlujo" style="display:flex;flex-direction:column;gap:7px"></div>
    <p class="gris" id="cpNota" style="font-size:12px;min-height:2.2em">—</p>
  </div>
</div>""", "compuerta"),

    # ── L23 · Madurez Técnica y Radiografía Operativa v1.6.5 (43 y 44) ──
    ("""
<div class="a"><div class="ceja">Producción Estable</div><h2 class="a">Estado actual del desarrollo y radiografía operativa (v1.6.5)</h2>
<p class="a" style="margin-top:6px">Software en General Availability en PyPI y GitHub con certificación empírica en Linux y Windows.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1.05fr 1fr;gap:18px">
  <div style="display:flex;flex-direction:column;gap:8px">
    <div class="tarjeta a acento" style="padding:8px 12px"><b style="font-size:12.6px">1 · Interoperabilidad MCP:</b> 75 herramientas tipadas bajo protocolo estándar.</div>
    <div class="tarjeta a acento" style="padding:8px 12px;border-left-color:var(--verde)"><b style="font-size:12.6px">2 · Capa Agéntica Soberana:</b> 19 perfiles duales (ReAct / Soberano local).</div>
    <div class="tarjeta a acento" style="padding:8px 12px;border-left-color:var(--bronce)"><b style="font-size:12.6px">3 · Dogmática y Grafos:</b> 58 tratados, 11 853 fichas FTS5 y -74,1 % tokens.</div>
    <div class="tarjeta a acento" style="padding:8px 12px;border-left-color:var(--azul)"><b style="font-size:12.6px">4 · QA y CI/CD:</b> 259 pruebas en verde, Bandit, Semgrep y Mypy estricto.</div>
    <div class="tarjeta a acento" style="padding:8px 12px;border-left-color:var(--rojo)"><b style="font-size:12.6px">5 · Ecosistema:</b> Space interactivo 3D en Hugging Face y material docente.</div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px" class="a">
    <div class="tarjeta" style="padding:8px 11px">
      <b style="font-size:12.4px">Herramientas MCP</b><br>
      <span class="chip" style="font-size:10.5px;border-color:var(--verde);color:var(--verde);margin-top:4px">75 operativas</span>
    </div>
    <div class="tarjeta" style="padding:8px 11px">
      <b style="font-size:12.4px">Agentes activos</b><br>
      <span class="chip" style="font-size:10.5px;border-color:var(--azul);color:var(--azul);margin-top:4px">19 perfiles</span>
    </div>
    <div class="tarjeta" style="padding:8px 11px">
      <b style="font-size:12.4px">Tratados y guías</b><br>
      <span class="chip" style="font-size:10.5px;border-color:var(--bronce);color:var(--bronce);margin-top:4px">58 tratados / 21 AJ</span>
    </div>
    <div class="tarjeta" style="padding:8px 11px">
      <b style="font-size:12.4px">Instituciones FTS5</b><br>
      <span class="chip" style="font-size:10.5px;border-color:var(--tinta);color:var(--tinta);margin-top:4px">11 853 fichas</span>
    </div>
    <div class="tarjeta" style="padding:8px 11px">
      <b style="font-size:12.4px">Pruebas en verde</b><br>
      <span class="chip" style="font-size:10.5px;border-color:var(--verde);color:var(--verde);margin-top:4px">259 pruebas</span>
    </div>
    <div class="tarjeta" style="padding:8px 11px">
      <b style="font-size:12.4px">Fidelidad doctrinal</b><br>
      <span class="chip" style="font-size:10.5px;border-color:var(--bronce);color:var(--bronce);margin-top:4px">10,0 / 10,0 pts</span>
    </div>
  </div>
</div>""", ""),

    # ── L24 · Posicionamiento Nacional e Internacional (45 y 46) ──
    ("""
<div class="a"><div class="ceja">Posicionamiento Estratégico</div><h2 class="a">Posicionamiento: soberanía nacional y vanguardia del Civil Law</h2>
<p class="a" style="margin-top:6px">Superación de monopolios privados en Chile y liderazgo agéntico para el Derecho Continental en el mundo.</p></div>
<div class="cuerpo" style="display:grid;grid-template-columns:1fr 1fr;gap:18px">
  <div class="tarjeta a acento" style="padding:12px 14px">
    <b style="font-size:13.2px;color:var(--tinta)">Impacto Nacional (Chile)</b>
    <ul class="lista" style="margin-top:8px">
      <li><b>Ruptura de silos cerrados:</b> Supera bases propietarias costosas (vLex, Thomson); OLC es 100 % abierto y programable con cualquier LLM.</li>
      <li><b>Secreto profesional absoluto:</b> Modo soberano 100 % local; los expedientes nunca viajan al extranjero (Art. 247 CP).</li>
      <li><b>Fidelidad institucional:</b> Conectores directos a BCN, CGR, DT, SMA y estándares procesales OJV.</li>
    </ul>
  </div>
  <div class="tarjeta a acento" style="padding:12px 14px;border-left-color:var(--bronce)">
    <b style="font-size:13.2px;color:var(--tinta)">Impacto Global (Civil Law)</b>
    <ul class="lista" style="margin-top:8px">
      <li><b>Vanguardia Continental:</b> Frente al 90 % de Legal AI anglosajón (Harvey, CoCounsel), OLC es el caso de estudio de modelado para Civil Law.</li>
      <li><b>Tokenómica GraphRAG:</b> Ahorro del 74,1 % de tokens sin perder contexto dogmático.</li>
      <li><b>Ciencia abierta:</b> Corpus libre en Hugging Face para evaluar modelos fundacionales en español.</li>
    </ul>
  </div>
</div>""", ""),

    # ── L25 · Cifras y Reglas de la Casa (47 y 48) ──
    ("""
<div class="a"><div class="ceja">El sistema</div><h2 class="a">Open Legal Chile en cifras y reglas de la casa</h2>
<p class="a" style="margin-top:6px">Indicadores auditados y mandatos epistemológicos innegociables para el ejercicio forense.</p></div>
<div class="cuerpo" style="display:flex;flex-direction:column;gap:14px">
  <div class="grid4" style="row-gap:10px">
    <div class="a"><div class="num" data-contador="75">0</div><small>herramientas MCP</small></div>
    <div class="a"><div class="num" data-contador="16">0</div><small>conectores oficiales</small></div>
    <div class="a"><div class="num" data-contador="17006">0</div><small>nodos del grafo</small></div>
    <div class="a"><div class="num" data-contador="259">0</div><small>pruebas en verde</small></div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px" class="a">
    <div class="tarjeta acento" style="padding:8px 12px">
      <b style="font-size:12.4px">1 · Subsunción Jurídica Tripartita</b>
      <p style="font-size:11.4px;margin-top:2px">Positivo (BCN) + Dogmático (Tratados) + Jurisprudencial (PJUD/CGR).</p>
    </div>
    <div class="tarjeta acento" style="padding:8px 12px;border-left-color:var(--rojo)">
      <b style="font-size:12.4px">2 · Prohibición de Common Law</b>
      <p style="font-size:11.4px;margin-top:2px">Prohibición estricta de discovery, punitive damages o at-will employment; derecho patrio.</p>
    </div>
    <div class="tarjeta acento" style="padding:8px 12px;border-left-color:var(--verde)">
      <b style="font-size:12.4px">3 · Toda fuente se cita con triplete</b>
      <p style="font-size:11.4px;margin-top:2px">Citas verificables; documentos entregados en Word (.docx editable).</p>
    </div>
    <div class="tarjeta acento" style="padding:8px 12px;border-left-color:var(--azul)">
      <b style="font-size:12.4px">4 · Secreto profesional y compuerta humana</b>
      <p style="font-size:11.4px;margin-top:2px">La IA no firma ni patrocina: la responsabilidad jurídica radica en el letrado.</p>
    </div>
  </div>
</div>""", ""),

    # ── L26 · Prueba en Vivo y Fuentes (49 y 50) ──
    ("""
<div class="a" style="position:absolute;inset:0"><canvas class="red" id="redCierre"></canvas></div>
<div class="encima a" style="margin-top:auto">
  <div class="ceja">Prueba en vivo · Pregunten lo que quieran</div>
  <h1 class="a" style="font-size:clamp(30px,4.5vw,56px)">En vivo: prueba interactiva y fuentes</h1>
</div>
<div class="encima a" style="margin-top:auto;max-width:940px">
  <p class="a" style="color:#C9CDD4;font-size:14.5px;line-height:1.6">
    Casos, plazos fatales, dictámenes, doctrina o análisis de documentos. Van a ver las herramientas trabajar y las fuentes oficiales aparecer al final.
  </p>
  <div style="background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);border-radius:10px;padding:10px 14px;margin-top:10px" class="a">
    <b style="color:var(--bronce2);font-size:12.5px">Fuentes oficiales del ecosistema:</b>
    <p style="font-size:11.8px;color:#CAD2DC;line-height:1.7;margin-top:3px">
      • Código y CI: <b>github.com/elpabloultron/open-legal-chile</b> (259 pruebas en verde)<br>
      • Paquete PyPI: <b>pypi.org/project/openlegal-chile</b> (v1.6.5)<br>
      • Corpus y Space 3D: <b>huggingface.co/datasets/pablobenavidesj/doctrina-jurisprudencia-chile</b><br>
      • Fuentes estatales: BCN Ley Chile · Contraloría General · Dirección del Trabajo · PJUD
    </p>
  </div>
</div>""", "red4")
]

# 2. Definición de las 26 notas de orador (correspondencia biunívoca)
NOTAS = [
    "Abrir la charla en la U. de Los Lagos: enfatizar que no es una demo comercial armada, sino software científico abierto y auditable para el foro y la academia.",
    "El triple origen: por qué nació (alucinaciones de la IA comercial), para qué es (ejercicio y docencia) y el puente (acercar al jurista a sus fuentes de la República).",
    "Mostrar el recorrido de los 5 niveles: desde la pregunta en lenguaje natural hasta el texto positivo oficial de la ley o dictamen.",
    "Fundamentos matemáticos y riesgo ético: explicar Softmax y el cálculo estocástico vs. la deontología procesal (Mata v. Avianca y Art. 72 CPC / 247 CP).",
    "El paradigma ReAct (Thought-Action-Observation-Reflection) y el Harness como sistema operativo forense para secreto profesional.",
    "MCP como estándar abierto universal (el USB-C del software agéntico); mostrar la consola de llamada real JSON-RPC 2.0 sobre stdio.",
    "La analogía del estudio jurídico: la herramienta es el formulario, la skill es el protocolo procesal y el agente es el letrado o pasante que los opera.",
    "Recapitular la arquitectura por capas: la ley arriba y el abogado en la cúspide validando y firmando.",
    "Transición a la Parte 2: El conocimiento, el corpus chileno en Markdown y el grafo de conocimiento.",
    "El problema del contexto: por qué el RAG plano falla en el derecho codificado y cómo LegalGraphify ahorra 74,1 % de tokens sin perder rigor.",
    "Las 6 fases de construcción del grafo: 58 tratados canónicos, 21 guías de la Academia Judicial, 17.006 nodos y 358 comunidades temáticas.",
    "Trazabilidad procesal completa: subsunción de 3 pilares, notas a pie de página formales y entrega de borradores editables en Word (.docx).",
    "Transición a la Parte 3: Las herramientas oficiales del Estado de Chile.",
    "De dónde salen los datos: las APIs oficiales sin intermediarios (BCN, CGR, DT, PJUD, TC, SMA, CMF, SII).",
    "El catálogo completo: 75 herramientas forenses agrupadas por familias y 19 agentes especializados para cada área del derecho.",
    "La mesa de entrada (caso_analizar): triaje automático de materias, detección de antecedentes faltantes y redacción judicial bajo CS Acta 94-2015.",
    "Doctrina canónica en SQLite FTS5 (11.853 fichas) e interrogación topológica de subgrafos con análisis de impacto y caminos.",
    "Docencia y ciencia abierta: el simulador de examen de grado, la clínica jurídica de lenguaje claro y el repositorio público en Hugging Face con su Space 3D.",
    "Vigilancia procesal activa: proveídos OJV, alertas normativas y cómputo riguroso de plazos fatales en días hábiles judiciales (Art. 66 CPC).",
    "Transición a la Parte 4: Privacidad, soberanía y secreto profesional indelegable.",
    "Soberanía de datos: el expediente no sale del computador, tramitación de derechos ARCO (Ley 19.628 / 21.719) y auditoría continua detect-secrets.",
    "Secreto profesional (Art. 247 CP) y la compuerta humana: auto-crítica en 5 dimensiones; el abogado patrocina y es el único responsable de la firma.",
    "Producción estable (General Availability v1.6.5): 5 capas arquitectónicas integradas y tabla de métricas auditadas con 259 pruebas en verde.",
    "Posicionamiento estratégico: ruptura de monopolios cerrados en Chile y liderazgo internacional del Civil Law continental y GraphRAG.",
    "Resumen en cifras y las cuatro reglas de la casa: subsunción tripartita, erradicación de Common Law, citas verificables y compuerta humana.",
    "Abrir la sesión de preguntas en vivo: invitar a los profesores a desafiar al sistema con cualquier caso, artículo o dictamen real."
]

def build():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Reemplazar comentario de láminas en el script
    content = re.sub(
        r"Open Legal Chile — presentación en HTML, minimalista, \d+ láminas animadas",
        "Open Legal Chile — presentación en HTML, minimalista, 26 láminas animadas",
        content
    )

    # Reemplazar la definición de láminas
    laminas_code = "\n".join([
        f'    /* ── Lámina {i+1} ── */\n    lamina(`{html}`, "{escena}");'
        for i, (html, escena) in enumerate(LAMINAS)
    ])

    idx_start = content.find("const L = [];")
    idx_end = content.find("const deck = document.getElementById(\"deck\");")
    if idx_start == -1 or idx_end == -1:
        raise ValueError("No se encontraron los delimitadores de L y deck")

    new_laminas_block = f"""const L = [];
    function lamina(html, escena) {{ L.push({{ html, escena }}); }}

{laminas_code}

    /* ══════════════════════════════════════════════════════════════════════════════════════════
       Motor
       ══════════════════════════════════════════════════════════════════════════════════════════ */
    """
    content = content[:idx_start] + new_laminas_block + content[idx_end:]

    # Actualizar animar(s) para que soporte múltiples escenas separadas por espacio
    old_animar = 'const esc = s.dataset.escena;'
    new_animar = '''const esc = s.dataset.escena || "";
      const escenas = esc.split(/\\s+/).filter(Boolean);
      escenas.forEach(e => {'''
    content = content.replace(old_animar, new_animar)

    # Reemplazar if (esc === ...) por if (e === ...) dentro de animar
    content = content.replace('if (esc === ', 'if (e === ')

    old_compuerta = 'if (e === "compuerta") escenaCompuerta(s);'
    new_compuerta = '''if (e === "compuerta") escenaCompuerta(s);
        if (e === "porque") escenaPorQue(s);
        if (e === "paraQue") escenaParaQue(s);
        if (e === "puente") escenaPuente(s);
        if (e === "huggingface") escenaHuggingFace(s);
        if (e === "frontera") escenaFrontera(s);
        if (e === "arco") escenaArco(s);
        if (e === "sale") escenaSale(s);
      });'''
    content = content.replace(old_compuerta, new_compuerta)

    # Actualizar NOTAS array
    notas_code = "const NOTAS = [\n" + "\n".join([f'      "{n}",' for n in NOTAS]) + "\n    ];"
    content = re.sub(r'const NOTAS = \[.*?\];', notas_code, content, flags=re.DOTALL)

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("Construcción exitosa de presentacion.html con 26 láminas y 26 notas.")

if __name__ == "__main__":
    build()
