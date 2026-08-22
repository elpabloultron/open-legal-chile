# ⚖️ Open Legal Chile

<p align="center">
  <strong>Infraestructura Abierta de Inteligencia Jurídica, Servidor MCP y Conectores Oficiales para el Ordenamiento Jurídico de la República de Chile</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/openlegal-chile/"><img src="https://img.shields.io/pypi/v/openlegal-chile?style=for-the-badge&logo=pypi&logoColor=white&color=blue" alt="PyPI Version"/></a>
  <a href="https://github.com/elpabloultron/open-legal-chile/actions"><img src="https://img.shields.io/github/actions/workflow/status/elpabloultron/open-legal-chile/ci.yml?branch=main&style=for-the-badge&logo=github" alt="CI Status"/></a>
  <img src="https://img.shields.io/badge/MCP-Protocol_2024--11--05-8B5CF6?style=for-the-badge&logo=anthropic&logoColor=white" alt="MCP Compatible"/>
  <img src="https://img.shields.io/badge/Jurisdicci%C3%B3n-Chile_(Civil_Law)-0039A6?style=for-the-badge&logo=flag&logoColor=white" alt="Chile Flag"/>
  <img src="https://img.shields.io/badge/License-Apache_2.0-22C55E?style=for-the-badge" alt="License"/>
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Versions"/>
</p>

---

## 📑 Tabla de Contenidos
1. [🌟 Visión y Filosofía Jurídica](#-1-visión-y-filosofía-jurídica)
2. [🏗️ Arquitectura del Ecosistema](#-2-arquitectura-del-ecosistema)
3. [⚡ Instalación y Conexión Rápida](#-3-instalación-y-conexión-rápida)
4. [🔌 Catálogo de Herramientas MCP (13 Herramientas)](#-4-catálogo-de-herramientas-mcp)
5. [🏛️ Los 10 Conectores Oficiales del Estado de Chile](#-5-los-10-conectores-oficiales-del-estado-de-chile)
6. [🧠 Catálogo de Skills y Subagentes](#-6-catálogo-de-skills-y-subagentes)
7. [⚖️ Motor de Crítica Forense en 5 Dimensiones](#-7-motor-de-crítica-forense-en-5-dimensiones)
8. [📄 Exportación y Tramitación Digital OJV (Ley N° 20.886)](#-8-exportación-y-tramitación-digital-ojv)
9. [📊 Chilean Legal Eval (Benchmark Jurídico Chileno)](#-9-chilean-legal-eval-benchmark-jurídico-chileno)
10. [💻 Uso de la Consola CLI (`openlegal`)](#-10-uso-de-la-consola-cli-openlegal)
11. [🧪 Pruebas Automatizadas y CI/CD](#-11-pruebas-automatizadas-y-cicd)
12. [🛡️ Licencia, Ética Forense y Responsabilidad](#-12-licencia-ética-forense-y-responsabilidad)
13. [🌱 Cómo Contribuir](#-13-cómo-contribuir)

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

## 🔌 4. Catálogo de Herramientas MCP

El servidor expone **13 herramientas oficiales** que cualquier LLM puede invocar automáticamente:

| Herramienta MCP | Parámetros de Entrada | Descripción / Salida |
| :--- | :--- | :--- |
| `bcn_get_codigo` | `codigo` *(str)*, `articulo` *(str, opcional)* | Consulta artículos o estructura de los 9 Códigos de la República (civil, trabajo, cpc, penal, comercio, tributario, mineria, aguas, cpp) en la BCN. |
| `bcn_get_ley` | `numero` *(int)*, `articulo` *(str, opcional)* | Descarga el texto oficial y vigente de cualquier ley chilena por su número (ej. Ley 21.643 Karin, Ley 21.561 40h). |
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
| `export_brief_ojv` | `titulo`, `tribunal`, `comparecencia`, `hechos`, `derecho`, `peticiones`, `otrosies` | Genera y formatea un escrito judicial estructurado formalmente para la Oficina Judicial Virtual (OJV) en `.html`, `.md`, `.txt` y `.json`. |

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

## 🧠 6. Catálogo de Skills y Subagentes

El repositorio incluye **7 habilidades** listas para ser activadas automáticamente por agentes de IA en `.agents/skills/` y **7 perfiles de agente** en `agents/`:

* **`chilean-employment-legal`** (`agente-laboral`): Despidos (Art. 161/160 CT), Ley Karin 21.643, 40 Horas (21.561), contratación, investigaciones internas, RIHS y doctrina DT.
* **`chilean-litigation-legal`** (`agente-litigios`): Intake de causas, demandas, cronologías de hechos, tablas de elementos y escritos OJV (Ley 20.886), recursos de protección, apelaciones y casaciones.
* **`chilean-administrative-legal`** (`agente-regulatorio`): Dictámenes/auditorías CGR, compras públicas (19.886), vigilancia regulatoria (Diario Oficial, CMF, SII, DT, SMA) y análisis de brechas normativas.
* **`chilean-energy-legal`** (`agente-energia`): Contratos PPA para clientes libres, transmisión eléctrica Ley 20.936, servidumbres y discrepancias del Panel de Expertos.
* **`chilean-environmental-legal`** (`agente-ambiental`): Fiscalizaciones SMA (SNIFA), infracciones a RCAs y Programas de Cumplimiento (Ley 20.417).
* **`chilean-contract-legal`** (`agente-contratos`): Revisión de contratos de proveedores, triage de NDA, registro de renovaciones, cláusula penal (CC), Ley 19.496 y Ley 21.719.
* **`chilean-corporate-legal`** (`agente-corporativo`): Constitución de SpA (20.659) y S.A. (18.046), compliance SII/CMF, actas de directorio/juntas y checklist de cierre (FNE DL 211).

> Los workflows de estas habilidades están **importados y chilenizados** del proyecto [anthropics/claude-for-legal](https://github.com/anthropics/claude-for-legal) (Apache-2.0), adaptados estrictamente al Derecho Continental chileno: se eliminaron todos los institutos del *Common Law* (*discovery*, *subpoena*, *deposition*, *privilege log*, *Upjohn*, *FMLA*) y se reemplazaron por sus equivalentes chilenos (prueba del CPC, OJV, Ley Karin, fuero, Código del Trabajo).

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

## 🧪 11. Pruebas Automatizadas y CI/CD

El repositorio cuenta con una suite de pruebas completa con **100% de tasa de aprobación**:

```bash
python -m pytest tests/ -v
# ============================= 21 passed ==============================
```

* **`.github/workflows/ci.yml`:** Integración continua en Ubuntu y Windows con Python 3.10 a 3.14.
* **`.github/workflows/state-api-monitor.yml`:** Monitor programado diario (08:00 UTC) que valida el estado de los servicios web de las instituciones del Estado.

---

## 🛡️ 12. Licencia, Ética Forense y Responsabilidad

### 📜 Licencia de Código Abierto (Apache 2.0)
Este proyecto está licenciado bajo la **Licencia Apache 2.0** ([`LICENSE`](LICENSE)), la cual permite su uso, modificación, integración y distribución tanto en entornos académicos como comerciales, proporcionando concesión expresa de patentes y **limitación estricta de responsabilidad**.

### ⚖️ Compuerta de Revisión Jurídica Obligatoria
> ⚖️ **Aviso Legal:** Open Legal Chile es una herramienta de asistencia técnica e investigación jurídica. Todo borrador, escrito o análisis generado mediante inteligencia artificial debe ser obligatoriamente revisado y validado por un abogado habilitado para el ejercicio de la profesión antes de su firma, notificación o ingreso en la Oficina Judicial Virtual (OJV).

---

## 🌱 13. Cómo Contribuir

¿Quieres aportar un conector, una skill, una herramienta MCP o documentación? **Eres bienvenido.**

1. Lee la [Guía de Contribución](CONTRIBUTING.md) (entorno de desarrollo, arquitectura, convenciones de commits y checklist de PR).
2. Revisa el [Código de Conducta](CODE_OF_CONDUCT.md), la [Política de Seguridad](SECURITY.md) y el [Acuerdo de Contribución](CLA.md).
3. Abre un **issue** con las plantillas disponibles (🐞 bug / ✨ feature) o envía un **Pull Request** usando su plantilla.
4. Para agregar conectores estatales, sigue la guía de [CONNECTORS.md](CONNECTORS.md); para skills/agentes, el catálogo de [AGENTS.md](AGENTS.md).

**Recursos para desarrolladores:**
* [docs/architecture.md](docs/architecture.md) — arquitectura, capas y puntos de entrada.
* [docs/Ley Chile - Formulario de solicitud API KEY BCN.pdf](docs/Ley%20Chile%20-%20Formulario%20de%20solicitud%20API%20KEY%20BCN.pdf) — formulario oficial para solicitar la API key de la BCN.
* Suite de 21 pruebas en `tests/` + CI en 5 versiones de Python (3.10–3.14) + monitor diario de APIs estatales.

### 📦 Publicación automática de versiones

Cada push a `main` con una versión nueva publica **solo** (sin pasos manuales):

```bash
python scripts/bump_version.py patch   # 1.0.0 -> 1.0.1
git add pyproject.toml setup.py openlegal.manifest.json mcp_server.py
git commit -m "chore(release): v1.0.1"
git push origin main
```

El workflow `publish-pypi.yml` detecta la versión nueva comparando `pyproject.toml` con PyPI, construye el paquete, lo sube a PyPI y crea el **GitHub Release** `vX.Y.Z` con los artefactos. Requiere el secreto `PYPI_API_TOKEN` (Settings → Secrets and variables → Actions). Detalles en [CONTRIBUTING.md §8](CONTRIBUTING.md#-8-publicación-de-versiones-automática).
