# 🏛️ Arquitectura del Sistema Open Legal Chile

> **Suite Abierta de Inteligencia Jurídica y Ecosistema de Agentes Autónomos para el Ordenamiento Jurídico de la República de Chile.**  
> Diseñada bajo la filosofía de software **Local-First**, **Agent-Native** y **Sovereign-First**, con estricta adherencia al sistema codificado continental (*Civil Law*) y las normas ortotipográficas de la RAE y la Academia Chilena de la Lengua.

---

## 📐 1. Principios Fundacionales de Diseño

1. **Local-First, Privacidad Absoluta y Cero Fuga de Datos:**
   * Las 7 399 obras doctrinales y artículos de revistas, el Knowledge Graph multidimensional (20 990 nodos y 51 590 aristas), los índices SQLite FTS5 y los expedientes procesales residen localmente en el equipo del usuario o en repositorios abiertos sin telemetría de contenido.
   * Sin fugas de secreto profesional (*Art. 247 del Código Penal* y *Ley N° 19.628 sobre Protección de la Vida Privada*).

2. **Ecosistema de Agentes Jurídicos Autónomos (19 Perfiles Especializados & 18 Skills):**
   * Runtime unificado en [`agents_runtime.py`](../agents_runtime.py) con dos modalidades de operación:
     * **Modo Determinista Soberano (100 % Offline, Cero API Keys):** Ejecución de pipelines forenses estandarizados (litigios y recursos de protección, auditoría decenal de títulos CBR, probidad administrativa CGR, despidos y tutelas laborales, asimilación de doctrina).
     * **Modo Asistido por LLM (ReAct Multi-Proveedor):** Ciclos de *Pensamiento / Acción / Observación* integrando Ollama, DeepSeek, Claude, Gemini o OpenAI, con inyección de doctrina nacional.

3. **Compresión de Contexto Dogmático con LegalGraphify (mediana -99,9 % de tokens; ficha 91 vs. obra 96 536):**
   * En lugar de consumir la ventana de contexto inyectando manuales completos (135 a 1 612 tokens; mediana 847), el motor extrae subgrafos sintéticos en YAML hiper-denso de 58 a 544 tokens (mediana 170) con definiciones unificadas, normas concordantes BCN, roles rectores de la Excma. Corte Suprema y operativa forense. Medición reproducible: `.venv/bin/python scripts/medir_ahorro_tokens.py` → [`medicion_tokens.md`](medicion_tokens.md).

4. **10 Conectores Oficiales del Estado de Chile:**
   * Consultas dinámicas y verificables sin simulación: BCN Ley Chile, Contraloría General de la República (CGR), Dirección del Trabajo (DT), Comisión Nacional de Energía (CNE), Panel de Expertos, CMF, SII, SMA (SNIFA), TDLC y PJUD (Corte Suprema / Tribunal Constitucional).

5. **Servidor FastMCP Maestro (87 Herramientas Oficiales):**
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
│  Catálogo de 19 Agentes Especializados (agents/*.json) & 18 Skills (.agents/skills/):   │
│  • Litigios OJV (Recursos de Protección)   • Auditor Inmobiliario & Títulos CBR         │
│  • Estratega Dogmático & LegalGraphify      • Agente Ingestor Doctrinal & Doc2Markdown   │
│  • Laboral & DT (Ley Karin / 40 Horas)     • Auditor Regulatorio & CGR                  │
│  • Probidad Pública & Declaraciones DIP    • Perito Forense Documental & OCR            │
│  • Vigilante Procesal & Plazos OJV         • Clínica Jurídica & Lenguaje Claro          │
│  • Interrogador Socrático de Grado         • Derecho Eléctrico & Energía CNE            │
│  • Ambiental & SMA / Tribunales Ambientales • Auditor Contractual & Consumo             │
│  • Corporativo & Compliance CMF/SII        • Privacidad & Marcas INAPI                  │
│  • Compilador Pericial de Dossiers A4      • Investigador Asistido NotebookLM           │
│  • Mesa de Entrada Forense (Intake)                                                     │
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼────────────────────────────────────────────────┐
│                         NÚCLEO FORENSE Y DOCTRINAL DE ALTA DENSIDAD                     │
│                                                                                         │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐  ┌────────────────┐ │
│  │ LegalGraphify Engine         │  │ Doctrina FTS5 & BM25 Engine  │  │ Doc2Markdown   │ │
│  │ (20.990 nodos · 51.590 ar.) │  │ (doctrina.db · 7.399 obras)  │  │ Ingestor RAE   │ │
│  │ 427 comunidades dogmáticas   │  │ 25.556 fichas densas         │  │ PDF/DOCX/TXT/MD│ │
│  │ Subgrafos YAML -99,9% tokens │  │ 11 Revistas Científicas Chile│  │ Fojas y Tablas │ │
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

## 🔌 3. Catálogo Funcional del Servidor MCP (87 Herramientas Oficiales)

Las 87 herramientas del servidor maestro MCP se estructuran en 16 dominios:

| N° | Categoría Funcional | Cantidad | Herramientas Clave |
|:---:|---|:---:|---|
| **1** | **BCN Legislación y Códigos** | 4 | `bcn_get_codigo`, `bcn_get_ley`, `bcn_get_codigo_historico`, `bcn_get_ley_historica` |
| **2** | **Protocolo de Citas y Texto Literal** | 2 | `consulta_maestra`, `cita_texto` |
| **3** | **Mesa de Entrada & Intake de Casos** | 2 | `caso_analizar`, `caso_ejecutar` |
| **4** | **Doctrina Canónica & FTS5** | 5 | `doctrina_search`, `doctrina_get_institucion`, `doctrina_list_obras`, `doctrina_ingestar_documento`, `huggingface_search_dataset` |
| **5** | **LegalGraphify Knowledge Graph** | 8 | `graphify_consulta_subgrafo`, `graphify_explicar_institucion`, `graphify_trazar_camino`, `graphify_analizar_impacto`, `graphify_god_nodes`, `graphify_resumen_comunidades`, `grafo_ver_corpus`, `grafo_ver_caso` |
| **6** | **Tribunales, Litigación & PJUD** | 7 | `pjud_search_jurisprudencia`, `pjud_analizar_sentencia`, `pjud_interpretar_proveido`, `recurso_proteccion_generar`, `compile_legal_dossier`, `export_brief_ojv`, `cpc_validar_mandato` |
| **7** | **Peritaje Forense & OCR** | 2 | `ocr_extract_pdf`, `ocr_plan_documento` |
| **8** | **CBR Inmobiliario & Registral** | 2 | `cbr_estudio_titulos`, `cbr_checklist_documentos` |
| **9** | **Derecho Administrativo & Probidad** | 4 | `cgr_search_jurisprudencia`, `cgr_search_auditorias`, `infoprobidad_get_dip`, `entes_consultar_organo` |
| **10** | **Derecho del Trabajo** | 1 | `dt_search_doctrina` |
| **11** | **Derecho Tributario & SII** | 7 | `sii_search_circulares`, `sii_buscar_resoluciones_y_oficios`, `sii_oficios_por_anio`, `sii_descargar_oficio`, `sii_actos_regionales`, `sii_convenios_internacionales`, `sii_jurisprudencia_judicial` |
| **12** | **Mercado Financiero & Libre Competencia** | 4 | `cmf_search_normativa`, `cmf_buscar_sanciones`, `tdlc_search_jurisprudencia`, `tdlc_buscar_icg_y_dictamenes` |
| **13** | **Derecho Ambiental & Energía** | 5 | `ambiental_consulta_maestra`, `ambiental_buscar_jurisprudencia`, `sma_search_sancionatorios`, `cne_get_centrales_y_proyectos`, `panel_expertos_search` |
| **14** | **Academia Judicial, Grado & Clínica** | 7 | `academia_judicial_buscar_guias`, `grado_interrogar`, `grado_generar_cedula`, `grado_obtener_flashcards`, `clinica_lenguaje_claro`, `clinica_intake_social`, `clinica_auditar_borrador` |
| **15** | **Vigilancia Procesal & Propiedad Intelectual** | 6 | `vigilante_analizar_resolucion`, `vigilante_radar_normativo`, `vigilante_contrato_plazos`, `privacidad_tramitar_arco`, `inapi_cease_and_desist`, `inapi_evaluar_marca` |
| **16** | **Agentes, Auditoría & Suite Runtime** | 21 | `agent_list`, `agent_run`, `agent_export_subagents`, `skills_listar`, `skill_ver`, `critique_documento`, `generar_documento`, `entrevista_estudio`, `busqueda_universal`, `generar_grafo_vinculos`, `rut_validar_chile`, `biblioteca_compilar_manifiesto`, `suite_doctor`, `suite_instalar`, `suite_telemetria_stats`, `suite_verificar_actualizacion`, `suite_auto_update`, `notebooklm_list_notebooks`, `notebooklm_create_notebook`, `notebooklm_add_source`, `notebooklm_query` |

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

## 🧪 5. Verificación Continua y Calidad 360°

* **507 pruebas unitarias y de integración automatizadas** con 100 % de aprobación en `pytest tests/ -v`.
* Tipado estricto verificado con `mypy` sobre los 252 módulos sin advertencias.
* Análisis estático de seguridad SAST con `bandit` y `semgrep`.
* Detección de fugas con `detect-secrets`.
* Análisis de complejidad ciclomática con `radon` y anti-bloat con `vulture` y `ponytail`.
* Compatibilidad multiplataforma garantizada en Linux y Windows (Python 3.10 a 3.14).
