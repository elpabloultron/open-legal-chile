# 🏛️ Arquitectura del Sistema Open Legal Chile

> **Suite Abierta de Inteligencia Jurídica y Ecosistema de Agentes Autónomos para el Ordenamiento Jurídico de la República de Chile.**
> Diseñada bajo la filosofía de software **Local-First**, **Agent-Native** y **Sovereign-First**, con estricta adherencia al sistema codificado continental (*Civil Law*) y las normas ortotipográficas de la RAE y la Academia Chilena de la Lengua.

---

## 📐 1. Principios Fundacionales de Diseño

1. **Local-First, Privacidad Absoluta y Cero Fuga de Datos:**
   * Las 58 obras canónicas, el Knowledge Graph multidimensional, los índices SQLite FTS5 y los expedientes procesales residen localmente en el equipo del usuario.
   * Sin telemetría encubierta de contenido judicial ni almacenamiento de partes procesales o números de rol.

2. **Ecosistema de Agentes Jurídicos Autónomos (18 Perfiles Especializados):**
   * Runtime unificado en [`agents_runtime.py`](file:///home/pablo/Escritorio/Ultimaprensa/open-legal-chile/agents_runtime.py) con dos modalidades de operación:
     * **Modo Determinista Soberano (100 % Offline, Cero API Keys):** Ejecución de pipelines forenses estandarizados (litigios y recursos de protección, auditoría decenal de títulos CBR, probidad administrativa CGR, despidos y tutelas laborales, asimilación de doctrina).
     * **Modo Asistido por LLM (ReAct Multi-Proveedor):** Ciclos de *Pensamiento / Acción / Observación* integrando Ollama, DeepSeek, Claude, Gemini o OpenAI, con inyección de doctrina nacional.

3. **Compresión de Contexto Dogmático con LegalGraphify (mediana -99,9 % de tokens; ficha 91 vs. obra 96.536):**
   * En lugar de consumir la ventana de contexto inyectando manuales completos (135 a 1 612 tokens; mediana 847), el motor extrae subgrafos sintéticos en YAML hiper-denso de 58 a 544 tokens (mediana 170) con definiciones unificadas, normas concordantes BCN, roles rectores de la Excma. Corte Suprema y operativa forense. Medición reproducible: `.venv/bin/python scripts/medir_ahorro_tokens.py` → [`medicion_tokens.md`](medicion_tokens.md).

4. **10 Conectores Oficiales del Estado de Chile:**
   * Consultas dinámicas y verificables sin simulación: BCN Ley Chile, Contraloría General de la República (CGR), Dirección del Trabajo (DT), Comisión Nacional de Energía (CNE), Panel de Expertos, CMF, SII, SMA (SNIFA), TDLC y PJUD (Corte Suprema / Tribunal Constitucional).

5. **Servidor FastMCP Maestro (64 Herramientas Nativas):**
   * Implementación estricta de la especificación MCP (*Model Context Protocol*) para consumo inmediato en Claude Code, Cursor, Windsurf, Google Antigravity y Gemini CLI.

6. **Auditoría Forense y Auto-Crítica en 5 Dimensiones:**
   * 1. *Jerarquía Normativa y Legalidad (Art. 1 del Código Civil y Arts. 6-7 CPR)*
   * 2. *Doctrina y Jurisprudencia Aplicable (CGR, DT, CS, TC, TDLC)*
   * 3. *Estructura Procesal OJV (Ley N° 20.886 y CPC / Auto Acordado CS Acta N.° 94-2015)*
   * 4. *Consistencia Fáctica y Carga Probatoria (Art. 1698 Código Civil)*
   * 5. *Compuertas Éticas de Revisión Forense y Plazos Fatales*

---

## 🏗️ 2. Diagrama de Capas de la Suite

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   INTERFACES DE USUARIO                                 │
│                                                                                         │
│  [ Consola CLI: openlegal ]   [ IDEs Agentic: Claude Code / Cursor ]   [ Servidor FastMCP ]│
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼────────────────────────────────────────────────┐
│                   MOTOR DE AGENTES JURÍDICOS AUTÓNOMOS (agents_runtime.py)              │
│                                                                                         │
│  Catálogo de 18 Agentes Especializados (agents/*.json):                                 │
│  • Litigios OJV (Recursos de Protección)   • Auditor Inmobiliario & Títulos CBR         │
│  • Estratega Dogmático & LegalGraphify      • Agente Ingestor Doctrinal & Doc2Markdown   │
│  • Laboral & DT                            • Auditor Regulatorio & CGR                  │
│  • Probidad Pública & Declaraciones DIP    • Perito Forense Documental & OCR            │
│  • Vigilante Procesal & Plazos OJV         • Clínica Jurídica & Lenguaje Claro          │
│  • Interrogador Socrático de Grado         • Derecho Eléctrico & Energía CNE            │
│  • Ambiental & SMA                         • Auditor Contractual & Consumo              │
│  • Corporativo & Compliance CMF/SII        • Privacidad & Marcas INAPI                  │
│  • Compilador Pericial de Dossiers A4      • Investigador Asistido NotebookLM           │
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼────────────────────────────────────────────────┐
│                         NÚCLEO FORENSE Y DOCTRINAL DE ALTA DENSIDAD                     │
│                                                                                         │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐  ┌────────────────┐ │
│  │ LegalGraphify Engine         │  │ Doctrina FTS5 & BM25 Engine  │  │ Doc2Markdown   │ │
│  │ (967 nodos · 1 366 aristas)  │  │ (doctrina.db · 58 tratados)  │  │ Ingestor RAE   │ │
│  │ Subgrafos YAML -99,9% tokens │  │ Fichas dogmáticas unificadas │  │ PDF/DOCX/TXT/MD│ │
│  └──────────────────────────────┘  └──────────────────────────────┘  └────────────────┘ │
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼────────────────────────────────────────────────┐
│                     10 CONECTORES OFICIALES DEL ESTADO DE CHILE                          │
│                                                                                         │
│   BCN Ley Chile ── CGR Dictámenes ── DT Laboral ── CNE Energía ── Panel Expertos        │
│   CMF Valores ─── SII Circulares ─── SMA SNIFA ─── TDLC Libre Competencia               │
│   PJUD Corte Suprema y Tribunal Constitucional                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 3. Catálogo Funcional del Servidor MCP (64 Herramientas)

Las 64 herramientas del servidor maestro MCP se dividen en las siguientes categorías:

| Categoría Funcional | Cantidad | Herramientas Clave |
|---|:---:|---|
| **Agentes & IA Jurídica** | 3 | `agent_list`, `agent_run`, `agent_export_subagents` |
| **Doctrina & Graphify** | 11 | `doctrina_search`, `doctrina_get_institucion`, `doctrina_list_obras`, `doctrina_ingestar_documento`, `graphify_consulta_subgrafo`, `graphify_trazar_camino`, `graphify_explicar_institucion`, `graphify_analizar_impacto`, `graphify_god_nodes`, `generar_grafo_vinculos`, `biblioteca_compilar_manifiesto` |
| **BCN Legislación y Códigos** | 4 | `bcn_get_codigo`, `bcn_get_ley`, `bcn_get_ley_historica`, `bcn_get_codigo_historico` |
| **CBR Inmobiliario & Mandatos** | 4 | `cbr_estudio_titulos`, `cbr_checklist_documentos`, `cpc_validar_mandato`, `rut_validar_chile` |
| **Tribunales & Litigación PJUD** | 7 | `pjud_search_jurisprudencia`, `pjud_analizar_sentencia`, `pjud_interpretar_proveido`, `recurso_proteccion_generar`, `compile_legal_dossier`, `export_brief_ojv`, `ocr_extract_pdf` |
| **Regulatorio, Fiscal & Público** | 12 | `cgr_search_jurisprudencia`, `cgr_search_auditorias`, `dt_search_doctrina`, `sii_search_circulares`, `sii_buscar_resoluciones_y_oficios`, `cmf_search_normativa`, `cmf_buscar_sanciones`, `sma_search_sancionatorios`, `tdlc_search_jurisprudencia`, `tdlc_buscar_icg_y_dictamenes`, `entes_consultar_organo`, `infoprobidad_get_dip` |
| **Especialidades Forenses** | 10 | `cne_get_centrales_y_proyectos`, `panel_expertos_search`, `ambiental_buscar_jurisprudencia`, `academia_judicial_buscar_guias`, `privacidad_tramitar_arco`, `inapi_cease_and_desist`, `inapi_evaluar_marca`, `clinica_lenguaje_claro`, `clinica_intake_social`, `clinica_auditar_borrador` |
| **Examen de Grado & Vigilancia** | 6 | `grado_interrogar`, `grado_generar_cedula`, `grado_obtener_flashcards`, `vigilante_analizar_resolucion`, `vigilante_radar_normativo`, `vigilante_contrato_plazos` |
| **Investigación & Telemetría** | 7 | `notebooklm_list_notebooks`, `notebooklm_create_notebook`, `notebooklm_add_source`, `notebooklm_query`, `suite_telemetria_stats`, `suite_verificar_actualizacion`, `suite_auto_update` |

---

## 💻 4. Línea de Comandos Oficial (`openlegal`)

```bash
# Consola interactiva maestra
$ openlegal

# Gestión de agentes jurídicos autónomos
$ openlegal agent list
$ openlegal agent run litigios "Generar recurso de protección por corte arbitrario de agua potable"
$ openlegal agent run inmobiliario "Auditar cadena decenal de dominio CBR"
$ openlegal agent run ingestor /ruta/al/tratado.pdf
$ openlegal agent chat dogmatico
$ openlegal agent export --format antigravity

# Consultas directas de subgrafos ontológicos
$ openlegal graph "simulación"

# Servidor FastMCP para IDEs de inteligencia artificial
$ openlegal mcp
```

---

## 🧪 5. Verificación Continua y Calidad

* **167 pruebas unitarias automatizadas** con 100 % de aprobación en `pytest tests/ -v`.
* Tipado estricto verificado con `mypy` sin advertencias ni supresiones inseguras.
* Análisis estático de código con `ruff check`.
* Compatibilidad multi-sistema y soberanía de datos garantizada.
