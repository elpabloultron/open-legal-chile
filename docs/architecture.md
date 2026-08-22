# 🏛️ Arquitectura de Open Legal Chile

> **Suite Abierta de Inteligencia Jurídica y Asistente Forense para el Ordenamiento Jurídico de la República de Chile.**
> Diseñada bajo la filosofía de software **Local-First**, **Agent-Native** y **BYOK (Bring Your Own Key / Agent)**, inspirada en los estándares de arquitectura de **Open Design** (`nexu-io/open-design`).

---

## 📐 1. Principios de Diseño

1. **Local-First & Privacidad Total:**
   * Todos los expedientes, demandas, dictámenes consultados y configuraciones residen exclusivamente en la máquina del usuario (`$HOME/Desktop/Open Legal Chile` o directorio de trabajo).
   * Cero telemetría no solicitada y aislamiento estricto de secretos en `.env`.

2. **Agent-Native & BYOK (Bring Your Own Key):**
   * Compatible con cualquier agente de codificación o modelo de lenguaje disponible:
     * **Anthropic Claude:** `claude-3-7-sonnet` (Thinking Híbrido), `claude-3-opus`, `claude-3-5-sonnet`.
     * **Google Gemini:** `gemini-2.0-flash`, `gemini-2.0-flash-thinking`, `gemini-1.5-pro` (con Google AI Pro y OAuth2 tokens).
     * **DeepSeek:** `deepseek-reasoner` (R1) y `deepseek-chat` (V3).
     * **OpenAI:** `o3-mini`, `o1`, `gpt-4o`.
     * **Ollama Local:** `deepseek-r1:8b`, `llama3.3:70b`, `qwen2.5` (100% Offline).

3. **Cero Simulación (100% Datos y Conexiones Reales):**
   * Todos los conectores consultan las APIs y servicios web oficiales en tiempo real:
     * **BCN Ley Chile:** SOAP / REST de 9 Códigos y leyes vigentes.
     * **Contraloría (CGR):** Jurisprudencia administrativa y 9.600+ auditorías.
     * **Dirección del Trabajo (DT):** 7.800+ dictámenes y doctrina laboral.
     * **CNE & Panel de Expertos:** Mercado eléctrico, proyectos SEA y discrepancias.
     * **CMF, SII, SMA (SNIFA) y TDLC:** Normativa financiera, tributaria, ambiental y libre competencia.

4. **Generación de Artefactos Forenses OJV (Ley N° 20.886):**
   * Generación de demandas civiles, recursos de protección, demandas laborales y contratos PPA en formatos estandarizados (`.html` tipográfico, `.md`, `.txt` y `.json`).

5. **Motor de Crítica Forense en 5 Dimensiones:**
   * 1. *Jerarquía Normativa y Legalidad (Art. 1 Código Civil)*
   * 2. *Doctrina y Jurisprudencia Aplicable (CGR, DT, CS, TDLC)*
   * 3. *Estructura Procesal OJV (Ley 20.886 y CPC)*
   * 4. *Consistencia Fáctica y Carga Probatoria (Art. 1698 CC)*
   * 5. *Compuertas Éticas y Plazos Fatales*

---

## 🏗️ 2. Diagrama de Capas de la Suite

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   INTERFACES DE USUARIO                                 │
│                                                                                         │
│  [ CLI (openlegal) ]    [ Desktop .exe / .app ]    [ Web Workspace ]    [ Coding Agent ]│
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼────────────────────────────────────────────────┐
│                           MOTOR MAESTRO OPEN LEGAL CHILE                                │
│                                                                                         │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌─────────────────────────────┐  │
│  │   Chat & RAG Engine   │  │   Document Exporter   │  │   5D Legal Critique Engine  │  │
│  │  (Multi-Model BYOK)   │  │   (OJV Ley 20.886)    │  │   (Civil Law Audit)         │  │
│  └───────────────────────┘  └───────────────────────┘  └─────────────────────────────┘  │
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

## 🛠️ 3. Puntos de Entrada y Comandos de la Suite

* `openlegal chat`: Sesión interactiva de chat forense con inyección de doctrina chilena (autodetecta el proveedor con API key).
* `openlegal generate <tipo>`: Genera borradores judiciales (demanda, recurso, contrato, finiquito).
* `openlegal critique <archivo>`: Ejecuta la auditoría en 5 dimensiones sobre un documento.
* `openlegal search <consulta>`: Búsqueda jurídica universal en los 10 conectores estatales (vía `connectors/registry.py`).
* `openlegal skills`: Lista las 7 habilidades y agentes jurídicos chilenos.
* `openlegal mcp`: Levanta el servidor MCP estándar (13 herramientas).
* `openlegal export`: Exporta artefactos procesales a formatos OJV (`.html`, `.md`, `.txt`, `.json` en `/exports/`).
* `openlegal check`: Verifica estado de conectores y credenciales en tiempo real.
