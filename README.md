# ⚖️ Open Legal Chile

<p align="center">
  <strong>Infraestructura Abierta de Inteligencia Jurídica, Servidor MCP y Conectores Oficiales para el Ordenamiento Jurídico de la República de Chile</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/openlegal-chile/"><img src="https://img.shields.io/pypi/v/openlegal-chile?style=for-the-badge&logo=pypi&logoColor=white&color=blue" alt="PyPI Version"/></a>
  <a href="https://github.com/elpabloultron/open-legal-chile/actions"><img src="https://img.shields.io/github/actions/workflow/status/elpabloultron/open-legal-chile/ci.yml?branch=main&style=for-the-badge&logo=github" alt="CI Status"/></a>
  <img src="https://img.shields.io/badge/Auditor%C3%ADa_360%C2%B0-Distinci%C3%B3n_M%C3%A1xima-success?style=for-the-badge&logo=security&logoColor=white" alt="Auditoría 360"/>
  <img src="https://img.shields.io/badge/Zero_Data_Leak-Passed-brightgreen?style=for-the-badge&logo=shield" alt="Zero Data Leak"/>
  <img src="https://img.shields.io/badge/MCP-Protocol_2024--11--05-8B5CF6?style=for-the-badge&logo=anthropic&logoColor=white" alt="MCP Compatible"/>
  <img src="https://img.shields.io/badge/Jurisdicci%C3%B3n-Chile_(Civil_Law)-0039A6?style=for-the-badge&logo=flag&logoColor=white" alt="Chile Flag"/>
  <img src="https://img.shields.io/badge/Tests-60%2F60_Passed-blue?style=for-the-badge&logo=pytest&logoColor=white" alt="Tests"/>
  <img src="https://img.shields.io/badge/License-Apache_2.0-22C55E?style=for-the-badge" alt="License"/>
</p>

---

## 📑 Tabla de Contenidos
1. [🌟 Visión y Filosofía Jurídica](#-1-visión-y-filosofía-jurídica)
2. [🏗️ Arquitectura del Ecosistema](#-2-arquitectura-del-ecosistema)
3. [⚡ Instalación y Conexión Rápida](#-3-instalación-y-conexión-rápida)
4. [🔌 Catálogo de Herramientas MCP (24 Herramientas)](#-4-catálogo-de-herramientas-mcp)
5. [🏛️ Los 10 Conectores Oficiales del Estado de Chile](#-5-los-10-conectores-oficiales-del-estado-de-chile)
6. [🧠 Catálogo de Skills y Subagentes](#-6-catálogo-de-skills-y-subagentes)
7. [⚖️ Motor de Crítica Forense en 5 Dimensiones](#-7-motor-de-crítica-forense-en-5-dimensiones)
8. [📄 Exportación y Tramitación Digital OJV (Ley N° 20.886)](#-8-exportación-y-tramitación-digital-ojv)
9. [📊 Chilean Legal Eval (Benchmark Jurídico Chileno)](#-9-chilean-legal-eval-benchmark-jurídico-chileno)
10. [💻 Uso de la Consola CLI (`openlegal`)](#-10-uso-de-la-consola-cli-openlegal)
11. [🛡️ Auditoría Institucional 360° y Seguridad (AUDIT.md)](#-11-auditoría-institucional-360-y-seguridad)
12. [🧪 Pruebas Automatizadas y CI/CD](#-12-pruebas-automatizadas-y-cicd)
13. [🛡️ Licencia, Ética Forense y Responsabilidad](#-13-licencia-ética-forense-y-responsabilidad)
14. [🌱 Cómo Contribuir](#-14-cómo-contribuir)

---

## 🌟 1. Visión y Filosofía Jurídica

**Open Legal Chile** es una infraestructura de software de código abierto diseñada para transformar la práctica legal, el análisis regulatorio y el desarrollo de agentes de inteligencia artificial en Chile. 

A diferencia de los asistentes genéricos diseñados para el *Common Law* anglosajón, este proyecto está construido **desde sus cimientos para el Sistema de Derecho Continental (*Civil Law*) de la República de Chile**:

### 🏛️ Principios Fundamentales del Sistema Chileno
* **Primacía de la Ley Escrita:** La Ley es la fuente primordial del derecho (*Art. 1 del Código Civil*). 
* **Efecto Relativo de las Sentencias:** Las resoluciones judiciales solo tienen fuerza obligatoria respecto de las causas en que actualmente se pronunciaren (*Art. 3 inc. 2 del Código Civil*). No existe el *stare decisis* obligatorio, aunque los fallos de unificación de la Corte Suprema y la doctrina administrativa de la Contraloría (CGR) y Dirección del Trabajo (DT) fijan criterios interpretativos de máxima relevancia.
* **Prohibición Estricta de Términos de *Common Law*:** Queda terminantemente prohibido extrapolar conceptos foráneos inexistentes en Chile (*at-will employment, punitive damages, discovery, subpoena, grand jury, Title VII, FLSA, OSHA*). Se utiliza exclusivamente terminología forense y sustantiva chilena (*necesidades de la empresa, finiquito con reserva de derechos, fuero, tutela laboral, daño moral, daño emergente, lucro cesante, otrosí, casación, reposición, apelación, SpA*).
* **Estándar Obligatorio de Citación Oficial:**
  * Norma legal: `[BCN - Código del Trabajo, Art. 161]` o `[BCN - Ley N° 21.643, Art. 2]`
  * Constitución: `[CPR 1980 - Art. 19 N° 24]`
  * Jurisprudencia Corte Suprema: `[CS - Rol N° 12.345-2023, Fecha: 15-11-2023]`
  * Dictamen DT: `[Dictamen DT N° 1234/15 de 2024]`
  * Dictamen CGR: `[Dictamen CGR N° E123456 (2024)]`
  * Circular SII: `[Circular SII N° 45 (2023)]`
  * Norma CMF: `[NCG CMF N° 461]`

---

## 🏗️ 2. Arquitectura del Ecosistema

Inspirada en el modelo **Local-First**, **Agent-Native** y **BYOK (Bring Your Own Key / Agent)**, la suite opera a través del protocolo estándar **Model Context Protocol (MCP)**:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           CLIENTES Y AGENTES DE IA SOPORTADOS                           │
│                                                                                         │
│   Google Antigravity      Claude Code (CLI)      Claude Desktop      Cursor / VS Code   │
│   (Google AI Pro)         (Anthropic)            (Cowork)            (Codex / Roo Code) │
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                         │ JSON-RPC 2.0 (stdio)
┌────────────────────────────────────────▼────────────────────────────────────────────────┐
│                       SERVIDOR MAESTRO MCP (mcp_server.py)                              │
│                                                                                         │
│   • 13 Herramientas Forenses Registradas                                                │
│   • Módulo Profundo de Registro Estatal (connectors/registry.py)                        │
│   • Almacenamiento en Caché Local SQLite Ultrarrápido (openlegal_cache.db)              │
│   • Motor de Crítica Forense en 5 Dimensiones (critique.py)                             │
│   • Formateador y Exportador de Escritos OJV Ley N° 20.886 (exporters.py)               │
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                         │ Peticiones HTTPS / REST / SOAP
┌────────────────────────────────────────▼────────────────────────────────────────────────┐
│                     10 CONECTORES OFICIALES DEL ESTADO DE CHILE                         │
│                                                                                         │
│   [BCN Ley Chile]   [Contraloría CGR]   [Dirección del Trabajo DT]   [PJUD / Suprema]   │
│   [Tribunal Const.] [CNE Energía]       [Panel de Expertos]          [CMF Valores]      │
│   [SII Tributario]  [SMA SNIFA Ambient] [TDLC Libre Competencia]                        │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ 3. Instalación y Conexión Rápida

### Opción A: Instalación vía PyPI (Recomendado)
```bash
pip install openlegal-chile
```

### Opción B: Conectar en Google Antigravity o Cursor
Agrega Open Legal Chile a tu archivo de configuración MCP (`mcp_config.json`):
```json
{
  "mcpServers": {
    "open-legal-chile": {
      "command": "python",
      "args": ["mcp_server.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

### Opción C: Conectar en Claude Code (Terminal)
```bash
claude mcp add open-legal-chile python mcp_server.py
```

### Opción D: Conectar vía Smithery (1 Clic)
```bash
npx -y @smithery/cli install open-legal-chile --client claude
```

### 🔑 Configuración de Credenciales (`.env`)

Copia `.env.example` a `.env` y completa las claves que tengas (el archivo `.env` está protegido en `.gitignore`):

| Variable | Función |
|----------|---------|
| `BCN_API_KEY` | API v1 de BCN Ley Chile (el XML público no la requiere) |
| `CNE_EMAIL` / `CNE_PASSWORD` | Autenticación de Energía Abierta (CNE) |
| `DEEPSEEK_API_KEY` | Chat jurídico con DeepSeek |
| `ANTHROPIC_API_KEY` | Chat jurídico con Claude |
| `GEMINI_API_KEY` | Chat jurídico con Gemini |
| `OPENAI_API_KEY` | Chat jurídico con OpenAI |
| `OLLAMA_HOST` | Modelo local vía Ollama |

> El chat (`openlegal chat`) y la crítica forense (`openlegal critique`) **autodetectan** el primer proveedor con API key configurada; usa `--provider` para forzar uno.

---

## 🔌 4. Catálogo de Herramientas MCP (36 Herramientas)

El servidor expone **36 herramientas oficiales** que cualquier LLM puede invocar automáticamente:

| Herramienta MCP | Parámetros de Entrada | Descripción / Salida |
| :--- | :--- | :--- |
| `bcn_get_codigo` | `codigo` *(str)*, `articulo` *(str, opcional)* | Consulta artículos o estructura de los 9 Códigos de la República (civil, trabajo, cpc, penal, comercio, tributario, mineria, aguas, cpp) en la BCN. |
| `bcn_get_ley` | `numero` *(int)*, `articulo` *(str, opcional)* | Descarga el texto oficial y vigente de cualquier ley chilena por su número (ej. Ley 21.643 Karin, Ley 21.561 40h, Ley 21.091). |
| `cgr_search_jurisprudencia` | `query` *(str)* | Busca dictámenes vinculantes en la jurisprudencia administrativa de la Contraloría (CGR). |
| `cgr_search_auditorias` | `query` *(str)* | Consulta el catálogo de más de 9.600 Informes Finales de Auditoría e investigaciones especiales de la CGR. |
| `dt_search_doctrina` | `query` *(str)* | Busca dictámenes y doctrina laboral obligatoria de la Dirección del Trabajo (DT). |
| `pjud_search_jurisprudencia` | `query` *(str)*, `sala` *(str, opcional)* | Busca fallos rectores de la Corte Suprema (Unificación Laboral, Constitucional, Civil) y sentencias del Tribunal Constitucional (TC). |
| `cne_get_centrales_y_proyectos` | `region` *(str, opcional)* | Consulta el registro de centrales generadoras activas, capacidad instalada y proyectos SEA de la Comisión Nacional de Energía. |
| `panel_expertos_search` | `query` *(str)* | Busca dictámenes vinculantes y resolución de discrepancias técnicas y tarifarias en el Panel de Expertos de la Ley Eléctrica. |
| `cmf_search_normativa` | `query` *(str)* | Consulta Normas de Carácter General (NCG) y circulares de la Comisión para el Mercado Financiero (CMF). |
| `sii_search_circulares` | `query` *(str)* | Consulta circulares e instrucciones oficiales del Director del SII (2020 a 2026). |
| `sma_search_sancionatorios` | `query` *(str)* | Consulta expedientes sancionatorios ambientales en el SNIFA de la Superintendencia del Medio Ambiente (SMA). |
| `tdlc_search_jurisprudencia` | `query` *(str)* | Consulta sentencias, resoluciones e instrucciones de carácter general del Tribunal de Defensa de la Libre Competencia (TDLC). |
| `infoprobidad_get_dip` | `query_or_url` *(str)* | **[NUEVO]** Extrae y estructura las Declaraciones de Intereses y Patrimonio (DIP) de autoridades públicas desde InfoProbidad (Ley 20.880). |
| `ocr_extract_pdf` | `pdf_path` *(str)*, `start_page`, `end_page`, `force_ocr`, `dpi`, `lang` | **[NUEVO]** Extrae texto nativo o ejecuta OCR pericial (Tesseract) sobre expedientes PDF judiciales, actas y escrituras escaneadas. |
| `compile_legal_dossier` | `markdown_content`, `output_pdf_path`, `annexes`, `mobile_preview_path` | **[NUEVO]** Compila escritos Markdown en PDF formal A4, ensambla anexos documentales con separadores institucionales foliados y versión móvil. |
| `export_brief_ojv` | `titulo`, `tribunal`, `comparecencia`, `hechos`, `derecho`, `peticiones`, `otrosies` | Genera y formatea un escrito judicial estructurado formalmente para la Oficina Judicial Virtual (OJV) en `.html`, `.md`, `.txt` y `.json`. |
| `generar_grafo_vinculos` | `nodes`, `edges`, `title` | **[NUEVO]** Modela redes corporativas y relaciones de interés entre autoridades, empresas (SpA/Ltda) y causas en formato Mermaid y JSON. |
| `notebooklm_list_notebooks`| *(ninguno)* | **[NUEVO]** Lista todos los cuadernos de investigación jurídica creados en Google NotebookLM con sus IDs y metadatos. |
| `notebooklm_create_notebook`| `title` *(str)* | **[NUEVO]** Crea un nuevo cuaderno de investigación jurídica en Google NotebookLM. |
| `notebooklm_add_source` | `notebook_id` *(str)*, `file_path` *(str)*, `title` *(str, opc)* | **[NUEVO]** Ingesta un expediente, sentencia o escrito local como fuente probatoria en NotebookLM. |
| `notebooklm_query` | `notebook_id` *(str)*, `prompt` *(str)* | **[NUEVO]** Realiza consultas analíticas fundadas con citas exactas (grounded citations) sobre las fuentes del cuaderno. |
| `doctrina_search` | `query` *(str)*, `area` *(str, opc)*, `autor` *(str, opc)*, `limit` *(int)* | **[NUEVO]** Busca en el canon dogmático de tratados chilenos (Barros, Ramos Pazos, Peñailillo, Maturana, Bermúdez, Cury, Gamonal, Cea Egaña) vía FTS5 BM25. |
| `doctrina_get_institucion` | `nombre` *(str)*, `area` *(str, opc)* | **[NUEVO]** Recupera la ficha dogmática de alta densidad (requisitos, concordancias BCN y fallos rectores CS/TC) de una institución jurídica. |
| `doctrina_list_obras` | *(ninguno)* | **[NUEVO]** Lista todos los tratados dogmáticos chilenos indexados, sus autores, materias y estadísticas de tokens. |
| `grado_interrogar` | `materia` *(str)*, `dificultad` *(str)* | **[NUEVO]** Interroga socráticamente con preguntas de examen de grado en Chile evaluando respuestas con doctrina canónica. |
| `grado_generar_cedula` | `tema` *(str)* | **[NUEVO]** Genera una cédula completa de examen de grado con preguntas, normas vinculadas, doctrina y pauta de evaluación. |
| `grado_obtener_flashcards` | `area` *(str)*, `tipo` *(str)* | **[NUEVO]** Obtiene fichas mnemotécnicas de definiciones sacramentales y plazos fatales procesales para examen de grado. |
| `vigilante_analizar_resolucion` | `resolucion_texto` *(str)*, `procedimiento` *(str)* | **[NUEVO]** Analiza resoluciones judiciales de OJV/PJUD, detecta cargas procesales y calcula plazos fatales en días hábiles (Art. 66 CPC). |
| `vigilante_radar_normativo` | `materia` *(str)*, `dias_atras` *(int)* | **[NUEVO]** Monitorea publicaciones recientes del Diario Oficial, dictámenes de la Contraloría (CGR) y circulares del SII. |
| `vigilante_contrato_plazos` | `tipo_contrato` *(str)*, `fecha_vencimiento` *(str)*, `preaviso_dias` *(int)* | **[NUEVO]** Calcula plazos de preaviso, desahucio y ventanas críticas de renovación automática para contratos civiles y comerciales. |
| `clinica_lenguaje_claro` | `texto_resolucion` *(str)*, `destinatario` *(str)* | **[NUEVO]** Traduce resoluciones judiciales densas a lenguaje claro, accesible y empático para usuarios de consultorios CAJ. |
| `clinica_intake_social` | `materia` *(str)*, `datos_usuario` *(dict)* | **[NUEVO]** Genera ficha sociojurídica de ingreso para consultorios de asistencia judicial en familia, alimentos y precario. |
| `clinica_auditar_borrador` | `borrador_texto` *(str)*, `tribunal` *(str)* | **[NUEVO]** Audita formalmente el borrador de un escrito redactado por un pasante antes de la firma del tutor (presuma, patrocinio y petitorio). |
| `privacidad_tramitar_arco` | `tipo_derecho`, `solicitante`, `rut`, `datos_solicitados` | **[NUEVO]** Tramita y genera modelo oficial de respuesta a Derechos ARCO bajo la Nueva Ley de Protección de Datos Personales. |
| `inapi_cease_and_desist` | `marca_afectada`, `titular`, `infractor`, `hechos_infraccion` | **[NUEVO]** Redacta carta notarial formal de Cese y Desistimiento por infracción de marca (Ley 19.039) o autor (Ley 17.336). |
| `inapi_evaluar_marca` | `marca_propuesta` *(str)*, `clase_niza` *(str)* | **[NUEVO]** Evalúa preliminarmente la viabilidad y distintividad de un signo marcario en el Clasificador de Niza ante INAPI. |

---

## 🏛️ 5. Los 10 Conectores Oficiales del Estado de Chile

Todos los conectores operan con consultas en tiempo real y almacenamiento en caché inteligente SQLite:

1. **📜 Biblioteca del Congreso Nacional (BCN Ley Chile):** Web Service SOAP y REST de toda la legislación positiva chilena y los 9 Códigos de la República.
2. **🏛️ Contraloría General de la República (CGR):** Más de 50.000 dictámenes vinculantes sobre estatuto administrativo, confianza legítima, probidad y más de 9.600 informes de auditoría.
3. **💼 Dirección del Trabajo (DT):** Más de 7.800 dictámenes y doctrina laboral sobre despidos (Art. 161), Ley Karin (Ley 21.643), reducción de jornada 40 Horas (Ley 21.561) y finiquitos.
4. **⚖️ Poder Judicial (PJUD) & Corte Suprema:** Fallos de Unificación de Doctrina Laboral (Art. 483 Código del Trabajo), Recursos de Protección Constitucional y Casación Civil.
5. **🛡️ Tribunal Constitucional (TC):** Sentencias sobre requerimientos de inaplicabilidad por inconstitucionalidad (*Art. 93 N° 6 CPR*).
6. **⚡ Comisión Nacional de Energía (CNE):** Capacidad instalada (MW), 1.342 centrales activas, 3.754 proyectos SEA, peajes de transmisión y costos marginales.
7. **🔌 Panel de Expertos de la Ley Eléctrica:** Dictámenes vinculantes e inapelables sobre discrepancias tarifarias y técnicas de la Ley General de Servicios Eléctricos (*DFL 4/2006*).
8. **🏢 Comisión para el Mercado Financiero (CMF):** Normas de Carácter General (NCG 461, gobiernos corporativos, sostenibilidad) y circulares del mercado de valores y bancario.
9. **💰 Servicio de Impuestos Internos (SII):** Circulares oficiales, oficios e instrucciones tributarias 2020 a 2026.
10. **🌱 Superintendencia del Medio Ambiente (SMA / SNIFA):** Catálogo oficial de más de 3.450 expedientes sancionatorios ambientales y Programas de Cumplimiento (PdC).

---

## 🧠 6. Catálogo de Skills y Subagentes (15 Especialidades)

El repositorio incluye **15 habilidades y perfiles de agente** en `agents/` listos para ser activados por cualquier LLM:

* **`chilean-employment-legal`** (`agente-laboral`): Despidos (Art. 161/160 CT), Ley Karin 21.643, 40 Horas (21.561), contratación, investigaciones internas, RIHS y doctrina DT.
* **`chilean-litigation-legal`** (`agente-litigios`): Intake de causas, demandas, cronologías de hechos, tablas de elementos y escritos OJV (Ley 20.886), recursos de protección, apelaciones y casaciones.
* **`chilean-administrative-legal`** (`agente-regulatorio`): Dictámenes/auditorías CGR, compras públicas (19.886), vigilancia regulatoria (Diario Oficial, CMF, SII, DT, SMA) y análisis de brechas normativas.
* **`chilean-energy-legal`** (`agente-energia`): Contratos PPA para clientes libres, transmisión eléctrica Ley 20.936, servidumbres y discrepancias del Panel de Expertos.
* **`chilean-environmental-legal`** (`agente-ambiental`): Fiscalizaciones SMA (SNIFA), infracciones a RCAs y Programas de Cumplimiento (Ley 20.417).
* **`chilean-contract-legal`** (`agente-contratos`): Revisión de contratos de proveedores, triage de NDA, registro de renovaciones, cláusula penal (CC), Ley 19.496 y Ley 21.719.
* **`chilean-corporate-legal`** (`agente-corporativo`): Constitución de SpA (20.659) y S.A. (18.046), compliance SII/CMF, actas de directorio/juntas y checklist de cierre (FNE DL 211).
* **`chilean-forensic-evidence`** (`agente-forense`): Peritaje documental de expedientes escaneados, OCR neuronal y Tesseract, extracción fidedigna de fojas judiciales y preservación de autenticidad.
* **`chilean-probity-investigation`** (`agente-probidad`): Auditoría patrimonial de autoridades públicas, cruce de DIP InfoProbidad, detección de conflictos de interés (Ley 20.880 y Ley 18.575).
* **`chilean-dossier-assembly`** (`agente-expedientes`): Ensamblaje pericial de expedientes A4, foliado digital, inserción de separadores institucionales con metadatos probatorios y salida dual (formal vs. móvil).
* **`chilean-notebooklm-grounding`** (`agente-investigacion-ia`): Investigación analítica asistida por IA con Google NotebookLM, consultas grounded y modelado de grafos de vínculos societarios/políticos.
* **`chilean-socratic-bar-exam`** (`agente-grado`): **[NUEVO]** Interrogador socrático para egresados de derecho que preparan su Examen de Grado en Civil y Procesal, basado en los 8 tratados canónicos y códigos BCN.
* **`chilean-docket-watcher`** (`agente-vigilante`): **[NUEVO]** Monitoreo de proveídos y resoluciones de la OJV/PJUD, cálculo de plazos fatales en días hábiles (Art. 66 CPC) y radar del Diario Oficial.
* **`chilean-legal-clinic`** (`agente-clinica`): **[NUEVO]** Asistencia jurídica social para consultorios CAJ y clínicas universitarias, traductor a Lenguaje Claro y auditoría de borradores de pasantes.
* **`chilean-privacy-ip`** (`agente-propiedad-datos`): **[NUEVO]** Tramitación formal de Derechos ARCO bajo la Nueva Ley de Protección de Datos Personales e informes de factibilidad marcaria y cartas C&D en INAPI.

> Los workflows de estas habilidades están **importados y chilenizados** del proyecto [anthropics/claude-for-legal](https://github.com/anthropics/claude-for-legal) (Apache-2.0), adaptados estrictamente al Derecho Continental chileno: se eliminaron todos los institutos del *Common Law* (*discovery*, *subpoena*, *deposition*, *privilege log*, *Upjohn*, *FMLA*) y se reemplazaron por sus equivalentes chilenos (prueba del CPC, OJV, Ley Karin, fuero, Código del Trabajo).

> 📚 **Base Doctrinal Canónica (Token-Optimized):** Los agentes cuentan con indexación FTS5 de los 8 manuales y tratados más citados de Chile (Barros Bourie, Ramos Pazos, Peñailillo, Maturana, Bermúdez, Cury, Gamonal, Cea Egaña), permitiendo fundar pretensiones y dictámenes en dogmática pura reduciendo en un 88% el consumo de tokens de contexto.

---

## ⚖️ 7. Motor de Crítica Forense en 5 Dimensiones

Inspirado en los mecanismos de auto-crítica de alta precisión, [`critique.py`](critique.py) evalúa cualquier borrador bajo 5 ejes estrictos:

1. **Jerarquía Normativa y Legalidad (Art. 1 Código Civil / CPR 1980):**
   * ¿Respeta la jerarquía Constitución > Ley > Reglamento?
   * ¿Cita los artículos vigentes y prohíbe terminología de *Common Law*?
2. **Doctrina y Jurisprudencia Aplicable (CGR, DT, CS, TC):**
   * ¿Incorpora la doctrina vinculante y cita en formato oficial `[BCN - ...]`, `[Dictamen DT ...]`?
3. **Estructura Forense y Tramitación Digital (Ley N° 20.886 / CPC):**
   * ¿Cumple con la Presuma OJV, comparecencia, capítulos de Hechos, Derecho, Por Tanto y Otrosíes?
4. **Coherencia Fáctica y Carga de la Prueba (Art. 1698 Código Civil):**
   * ¿Los hechos sustentan lógicamente el petitum y la prueba ofrecida es idónea?
5. **Compuertas Éticas y Plazos Fatales:**
   * ¿Advierte plazos fatales procesales y contiene la compuerta de validación profesional?

---

## 📄 8. Exportación y Tramitación Digital OJV

[`exporters.py`](exporters.py) genera escritos procesales con tipografía jurídica estándar (Times New Roman / Calibri, espaciado interlineal, numeración y justificación) exportando simultáneamente a formatos:
* **HTML:** Listo para impresión profesional o conversión a PDF.
* **Markdown:** Optimizado para lectura en terminal o editores de texto.
* **Texto Plano:** Para copiar/pegar en la Oficina Judicial Virtual.
* **JSON:** Para intercambio LegalTech con otros sistemas.

---

## 📊 9. Chilean Legal Eval (Benchmark Jurídico Chileno)

Open Legal Chile incluye un banco de evaluación estandarizado en [`evals/`](evals/):
* **Dataset Forense (`evals/test_cases.json`):** Casos reales sobre Ley Karin, Confianza Legítima a contrata en la CGR, Recursos de Protección Constitucional, Sancionatorios Ambientales SMA y Contratos PPA Eléctricos.
* **Motor Evaluador (`evals/benchmark.py`):** Califica las respuestas de cualquier modelo (0.0 a 10.0), otorgando puntaje por citas oficiales y penalizando con -3.0 puntos cada alucinación de términos de *Common Law*.

```bash
python evals/benchmark.py
```

---

## 💻 10. Uso de la Consola CLI (`openlegal`)

```bash
# Iniciar el servidor MCP estándar
python openlegal.py mcp

# Búsqueda jurídica universal en los 10 organismos a la vez
python openlegal.py search "confianza legitima contrata"

# Auditar un escrito bajo las 5 dimensiones forenses
python openlegal.py critique demanda.txt

# Generar un borrador procesal formal OJV
python openlegal.py generate demanda_civil

# Sesión interactiva de chat con RAG chileno
python openlegal.py chat

# Diagnóstico de conectores
python openlegal.py check
```

---

## 🛡️ 11. Auditoría Institucional 360° y Seguridad (AUDIT.md)

Open Legal Chile está certificado mediante una suite de auditoría integral de 9 capas ejecutada periódicamente en integración continua y verificable localmente vía `./audit.sh`.

Para consultar el informe institucional completo con análisis normativo (Ley N° 19.628 de Protección de Datos, Ley N° 21.643 Karin, Secreto Profesional Art. 247 CP), consulta [`AUDIT.md`](AUDIT.md).

```bash
# Ejecutar auditoría integral de 9 capas
./audit.sh
# O vía CLI oficial:
python openlegal.py audit
```

| Capa / Dimensión | Motor Estándar | Estado / Certificación |
| :--- | :--- | :--- |
| **1. Vulnerabilidades SCA** | `pypa/pip-audit` | **0 vulnerabilidades conocidas** (CVEs neutralizados) |
| **2. Seguridad SAST** | `PyCQA/bandit` | **0 fallas de inyección o deserialización** |
| **3. Semántica OWASP** | `semgrep/semgrep` | **0 hallazgos bloqueantes** (201 reglas analizadas) |
| **4. Fuga de Secretos** | `Yelp/detect-secrets` | **Zero Data Leak** (0 llaves o credenciales expuestas) |
| **5. Tipado Estático** | `python/mypy` | **0 errores en 45 archivos fuente** |
| **6. Linter & PEP** | `astral-sh/ruff` | **100% de reglas de sintaxis y arquitectura aprobadas** |
| **7. Anti-Sobreingeniería**| `Ponytail` & `vulture`| **Filosofía Ponytail: Cero código muerto (*Lean already. Ship*)** |
| **8. Mantenibilidad** | `rubik/radon` | **Rango A en lógica sustantiva y conectores** |
| **9. Pruebas Funcionales** | `pytest-dev/pytest` | **60/60 pruebas unitarias superadas (100%)** |

---

## 🧪 12. Pruebas Automatizadas y CI/CD

El repositorio cuenta con una suite de pruebas completa con **100% de tasa de aprobación**:

```bash
python -m pytest tests/ -v
# ============================= 60 passed in 1.35s ==============================
```

* **`.github/workflows/ci.yml`:** Integración continua en Ubuntu y Windows con Python 3.10 a 3.14.
* **`.github/workflows/state-api-monitor.yml`:** Monitor programado diario (08:00 UTC) que valida el estado de los servicios web de las instituciones del Estado.
* **`audit.sh`:** Script ejecutable de una sola línea para auditorías de cumplimiento institucional.

---

## 🛡️ 13. Licencia, Ética Forense y Responsabilidad

### 📜 Licencia de Código Abierto (Apache 2.0)
Este proyecto está licenciado bajo la **Licencia Apache 2.0** ([`LICENSE`](LICENSE)), la cual permite su uso, modificación, integración y distribución tanto en entornos académicos como comerciales, proporcionando concesión expresa de patentes y **limitación estricta de responsabilidad**.

### ⚖️ Compuerta de Revisión Jurídica Obligatoria
> ⚖️ **Aviso Legal:** Open Legal Chile es una herramienta de asistencia técnica e investigación jurídica. Todo borrador, escrito o análisis generado mediante inteligencia artificial debe ser obligatoriamente revisado y validado por un abogado habilitado para el ejercicio de la profesión antes de su firma, notificación o ingreso en la Oficina Judicial Virtual (OJV).

---

## 🌱 14. Cómo Contribuir

¿Quieres aportar un conector, una skill, una herramienta MCP o documentación? **Eres bienvenido.**

1. Lee la [Guía de Contribución](CONTRIBUTING.md) (entorno de desarrollo, arquitectura, convenciones de commits y checklist de PR).
2. Revisa el [Código de Conducta](CODE_OF_CONDUCT.md), la [Política de Seguridad](SECURITY.md) y el [Acuerdo de Contribución](CLA.md).
3. Abre un **issue** con las plantillas disponibles (🐞 bug / ✨ feature) o envía un **Pull Request** usando su plantilla.
4. Para agregar conectores estatales, sigue la guía de [CONNECTORS.md](CONNECTORS.md); para skills/agentes, el catálogo de [AGENTS.md](AGENTS.md).

**Recursos para desarrolladores:**
* [docs/architecture.md](docs/architecture.md) — arquitectura, capas y puntos de entrada.
* [docs/Ley Chile - Formulario de solicitud API KEY BCN.pdf](docs/Ley%20Chile%20-%20Formulario%20de%20solicitud%20API%20KEY%20BCN.pdf) — formulario oficial para solicitar la API key de la BCN.
* Suite de 60 pruebas en `tests/` + CI en 5 versiones de Python (3.10–3.14) + monitor diario de APIs estatales.

### 📦 Publicación automática de versiones

Cada push a `main` con una versión nueva publica **solo** (sin pasos manuales):

```bash
python scripts/bump_version.py patch   # 1.0.0 -> 1.0.1
git add pyproject.toml setup.py openlegal.manifest.json mcp_server.py
git commit -m "chore(release): v1.0.1"
git push origin main
```

El workflow `publish-pypi.yml` detecta la versión nueva comparando `pyproject.toml` con PyPI, construye el paquete, lo sube a PyPI y crea el **GitHub Release** `vX.Y.Z` con los artefactos. Requiere el secreto `PYPI_API_TOKEN` (Settings → Secrets and variables → Actions). Detalles en [CONTRIBUTING.md §8](CONTRIBUTING.md#-8-publicación-de-versiones-automática).
