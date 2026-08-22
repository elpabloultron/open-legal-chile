# ⚖️ Open Legal Chile

<p align="center">
  <strong>Suite de Inteligencia Jurídica y Servidor MCP Oficial para el Ordenamiento Jurídico de la República de Chile</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/openlegal-chile/"><img src="https://img.shields.io/pypi/v/openlegal-chile?color=blue&style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI Version"/></a>
  <a href="https://github.com/elpabloultron/open-legal-chile/actions"><img src="https://img.shields.io/github/actions/workflow/status/elpabloultron/open-legal-chile/ci.yml?branch=main&style=for-the-badge&logo=github" alt="CI Status"/></a>
  <img src="https://img.shields.io/badge/MCP-Protocol_2024--11--05-8B5CF6?style=for-the-badge&logo=anthropic&logoColor=white" alt="MCP Compatible"/>
  <img src="https://img.shields.io/badge/Jurisdicci%C3%B3n-Chile_(Civil_Law)-0039A6?style=for-the-badge&logo=flag&logoColor=white" alt="Chile Flag"/>
  <img src="https://img.shields.io/badge/License-Apache_2.0-22C55E?style=for-the-badge" alt="License"/>
</p>

---

## ⚡ Instalación Global en 1 Línea

```bash
# Vía PyPI (Recomendado)
pip install openlegal-chile

# Vía Smithery (Para Claude Desktop & Cursor)
npx -y @smithery/cli install open-legal-chile --client claude
```

---

## 🤖 Arquitectura Agéntica (MCP Servers + Agents + Skills)

Igual que **Claude for Legal**, Open Legal Chile funciona de forma nativa dentro de tus entornos de desarrollo de IA (**Antigravity / Gemini**, **Claude Code**, **Cursor**, **Codex**) sin necesidad de interfaces intermedias ni APIs adicionales:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           OPEN LEGAL CHILE — AGENTIC ECOSYSTEM                          │
├─────────────────────────┬─────────────────────────┬─────────────────────────────────────┤
│   1. SERVIDOR MCP       │   2. SKILLS JURÍDICAS   │          3. CLI / AUTOMATION        │
│    (Model Context)      │    (Catálogo Chile)     │                                     │
│                         │                         │                                     │
│ `openlegal mcp`         │ • employment-legal      │ `openlegal search "Ley Karin"`      │
│ Herramientas JSON-RPC   │ • litigation-legal      │ `openlegal critique demanda.txt`    │
│ para consultar BCN,     │ • energy-legal          │ `openlegal generate demanda_civil`  │
│ CGR, DT, CNE, CMF, TDLC │ • environmental-legal   │ `openlegal check`                   │
│ directo desde tu agente │ • antitrust-legal       │ `openlegal export`                  │
└─────────────────────────┴─────────────────────────┴─────────────────────────────────────┘
```

---

## ⚡ Conexión Inmediata a tu Agente de IA

### 🤖 En Antigravity (Google Gemini) o Cursor:
Añade Open Legal Chile a tu configuración MCP (`mcp_config.json`):
```json
{
  "mcpServers": {
    "open-legal-chile": {
      "command": "python",
      "args": ["mcp_server.py"]
    }
  }
}
```

### 🧠 En Claude Code:
Ejecuta el comando para registrar el servidor MCP:
```bash
claude mcp add open-legal-chile python mcp_server.py
```

---

---

## 💻 Uso de la Consola CLI (`openlegal`)

Open Legal Chile incluye una potente consola para terminal:

```bash
# Iniciar el servidor MCP estándar
python openlegal.py mcp

# Búsqueda jurídica universal en los 8 conectores a la vez
python openlegal.py search "Ley Karin acoso laboral"

# Auditar un escrito bajo las 5 dimensiones forenses (Civil Law)
python openlegal.py critique demanda.txt

# Generar un borrador procesal formal OJV
python openlegal.py generate demanda_civil

# Verificar conectividad con los servicios del Estado
python openlegal.py check
```

---

## 🧪 Ejecución de Pruebas Automatizadas

```bash
# Ejecutar suite de pruebas de conectores y servidor MCP
python -m pytest tests/ -v

# Ejecutar el Benchmark Jurídico Chileno (Chilean Legal Eval)
python evals/benchmark.py
```

---

## 🤖 Catálogo de Modelos de Inteligencia Artificial Soportados (BYOK)

Open Legal Chile permite utilizar tu modelo preferido con inyección automática de doctrina de la DT, leyes de la BCN, dictámenes de la CGR y fallos del TDLC:

| Proveedor | Modelos & Niveles de Razonamiento | Especialidad Forense en Chile |
| :--- | :--- | :--- |
| **⚡ Google Gemini** | • `Gemini 3.7 Flash High`<br>• `Gemini 3.6 Flash Medium (Fast)`<br>• `Gemini 3.5 Flash Medium (Fast)`<br>• `Gemini 3.1 Pro Low`<br>• `Gemini 2.5 Pro` | **Análisis masivo de expedientes, contratos PPA y licitaciones públicas. Conexión directa con cuenta Google.** |
| **✨ Anthropic Claude** | • `Claude 3.7 Sonnet Thinking (High)`<br>• `Claude 3.7 Sonnet (Standard)`<br>• `Claude 3.5 Sonnet`<br>• `Claude 3 Opus`<br>• `Claude 3.5 Haiku` | **Máxima precisión y calidad formal en redacción de escritos judiciales, demandas y recursos de protección.** |
| **🧠 DeepSeek** | • `DeepSeek-R1 Reasoner (High Logic)`<br>• `DeepSeek-V3 Chat (Fast)` | **Razonamiento lógico paso a paso de ultra bajo costo y auditoría de contradicciones probatorias.** |
| **🟢 OpenAI** | • `o3-mini (High Reasoning)`<br>• `o1`<br>• `GPT-4o` / `GPT-4o mini` | **Razonamiento estructurado y modelos rápidos de propósito general.** |
| **🦙 Ollama (Local)** | • `DeepSeek-R1 8B`<br>• `Llama 3.3 70B`<br>• `Qwen 2.5` | **100% privado y offline (sin enviar ningún dato a servidores externos).** |

---

## 🏛️ Conectores Oficiales del Estado de Chile (8/8)

Todos los conectores están verificados y operan en tiempo real:

| Institución Pública | Módulo | Funcionalidad Clave | Estado |
| :--- | :--- | :--- | :--- |
| **Biblioteca del Congreso Nacional (BCN)** | `bcn_connector.py` | Web Service SOAP y REST de los 9 Códigos de la República y leyes vigentes. | ✅ Oficial |
| **Contraloría General de la República (CGR)** | `cgr_connector.py` | Consulta de jurisprudencia administrativa y más de 9.600 informes de auditoría. | ✅ Oficial |
| **Dirección del Trabajo (DT)** | `dt_connector.py` | Catálogo de más de 7.800 dictámenes, ordinarios y doctrina laboral obligatoria. | ✅ Oficial |
| **Comisión Nacional de Energía (CNE)** | `cne_connector.py` | 1.342 centrales activas, 3.754 proyectos SEA, peajes y costos marginales. | ✅ Oficial |
| **Panel de Expertos de la Ley Eléctrica** | `panel_expertos_connector.py` | Dictámenes vinculantes y resolución de discrepancias tarifarias y técnicas. | ✅ Oficial |
| **Comisión para el Mercado Financiero (CMF)** | `cmf_connector.py` | Normas de Carácter General (NCG), circulares y resoluciones bancarias y de valores. | ✅ Oficial |
| **Servicio de Impuestos Internos (SII)** | `sii_connector.py` | Circulares oficiales, oficios y jurisprudencia tributaria 2020 a 2026. | ✅ Oficial |
| **Superintendencia del Medio Ambiente (SMA)** | `ambiental_connector.py` | Catálogo del SNIFA con más de 3.450 expedientes sancionatorios ambientales. | ✅ Oficial |
| **Tribunal de Defensa de la Libre Competencia (TDLC)**| `tdlc_connector.py` | Sentencias, resoluciones e instrucciones generales sobre libre competencia. | ✅ Oficial |

---

## ⚖️ Redactor Forense & Exportador OJV (Ley N° 20.886)

El módulo `exporters.py` y la pestaña web **Redactor Forense** permiten generar borradores judiciales estructurados según la práctica forense chilena:

* **Presuma OJV Formal:** Procedimiento, Materia, Demandante, RUT, Abogado Patrocinante y Demandado.
* **Cuerpo Estructurado:** En lo principal, I. Los Hechos, II. El Derecho, Por Tanto y Otrosíes (Patrocinio y poder Ley N° 18.120).
* **Exportación en 1 Clic:** Generación automática de archivos `.html` y `.md` en la carpeta `/exports/`.

---

## 💻 Comandos del CLI (`openlegal`)

```bash
# Menú interactivo
openlegal

# Chat interactivo con IA
openlegal chat --provider anthropic
openlegal chat --provider gemini

# Levantar el Dashboard Web
openlegal web

# Listar todas las habilidades y plugins
openlegal skills

# Generar y exportar un escrito forense
openlegal export

# Búsqueda jurídica universal
openlegal search "confianza legitima contrata"

# Diagnóstico de conectores y credenciales
openlegal check
```

---

## 🔐 Configuración y Variables de Entorno

Copia el archivo `.env.example` como `.env`:

```bash
cp .env.example .env
```

```ini
# BCN Ley Chile (Gratuita en https://www.bcn.cl/leychile/consulta_ws)
BCN_API_KEY=tu_api_key_aqui

# CNE Energía Abierta (Gratuita en https://api.cne.cl/)
CNE_EMAIL=tu_correo@ejemplo.cl
CNE_PASSWORD=tu_contraseña_cne

# Proveedores de IA (Opcionales - BYOK)
ANTHROPIC_API_KEY=tu_anthropic_key
GEMINI_API_KEY=tu_gemini_key
DEEPSEEK_API_KEY=tu_deepseek_key
OPENAI_API_KEY=tu_openai_key
OLLAMA_HOST=http://localhost:11434
```

---

## ⚖️ Compuerta de Responsabilidad Ética

> ⚠️ **Aviso Profesional:** Open Legal Chile es una herramienta de asistencia y apoyo al trabajo jurídico basada en inteligencia artificial. Todo escrito, análisis o borrador debe ser validado por un abogado habilitado para el ejercicio de la profesión antes de su firma e ingreso en la Oficina Judicial Virtual (OJV) o notificación a terceros.

---

## 📄 Licencia

Este proyecto está licenciado bajo la **Licencia Apache 2.0**.
