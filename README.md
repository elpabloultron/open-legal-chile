# ⚖️ Open Legal Chile

<p align="center">
  <img src="web/favicon.ico" alt="Open Legal Chile Logo" width="80" height="80" onerror="this.style.display='none'"/>
</p>

<p align="center">
  <strong>Plataforma de Inteligencia Jurídica, Asistente Forense y Conectores Oficiales del Estado de Chile</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Jurisdicci%C3%B3n-Rep%C3%BAblica_de_Chile-0039A6?style=for-the-badge&logo=flag&logoColor=white" alt="Chile Flag"/>
  <img src="https://img.shields.io/badge/Sistema-Civil_Law_(Continental)-D9381E?style=for-the-badge" alt="Civil Law"/>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version"/>
  <img src="https://img.shields.io/badge/License-Apache_2.0-22C55E?style=for-the-badge" alt="License"/>
  <img src="https://img.shields.io/badge/BYOK-Multi--IA_Enabled-8B5CF6?style=for-the-badge" alt="BYOK Multi-IA"/>
</p>

---

## 🌟 Visión del Proyecto

**Open Legal Chile** es una suite de código abierto, local-first y multi-agente diseñada para revolucionar la práctica legal y el acceso a la información jurídica en Chile. Desarrollada bajo los principios del **Sistema de Derecho Continental (*Civil Law*)**, integra en tiempo real las bases de datos de las principales instituciones públicas del país con modelos de inteligencia artificial de última generación (**Claude 3.7, Gemini 3.x, DeepSeek-R1, OpenAI y Ollama**).

---

## 🚀 4 Modos de Ejecución Disponibles

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   OPEN LEGAL CHILE                                      │
├─────────────────────┬─────────────────────┬─────────────────────┬───────────────────────┤
│ 1. SOFTWARE DESKTOP │     2. MODO CLI     │     3. MODO WEB     │     4. MODO AGENTE    │
│ (Windows / Linux)   │   (Terminal/TUI)    │  (Workspace Local)  │   (Claude/Antigravity)│
│                     │                     │                     │                       │
│ Doble clic en       │ `openlegal`         │ `openlegal web`     │ Asistente IA con RAG  │
│ `OpenLegalChile.exe`│ `openlegal chat`    │ -> http://          │ en vivo de leyes y    │
│ o ejecutable Linux  │ `openlegal export`  │    localhost:8000   │ dictámenes chilenos   │
└─────────────────────┴─────────────────────┴─────────────────────┴───────────────────────┘
```

---

## ⚡ Instalación y Ejecución por Plataforma

### 🪟 Windows (Software .exe Nativo)
1. **Ejecutable Directo:** Haz doble clic en **`OpenLegalChile.exe`** en la raíz del proyecto para abrir la ventana de software de escritorio nativa.
2. **Instalador PowerShell:**
   ```powershell
   .\install.ps1
   ```
3. **Lanzador Rápido:** Doble clic en `install.bat`.

---

### 🐧 Linux (Ubuntu / Linux Mint / Debian / Pop!_OS)
1. **Compilar e instalar lanzador de menú (.desktop):**
   ```bash
   chmod +x build_linux.sh install.sh
   ./build_linux.sh
   ```
2. **Aparición en el Menú:** Aparecerá automáticamente en el menú de aplicaciones de **Linux Mint (Cinnamon)** y **Ubuntu (GNOME/Dash)**.

---

### 🏹 Arch Linux / Manjaro / EndeavourOS
1. **Instalar vía PKGBUILD:**
   ```bash
   makepkg -si
   ```
2. **O ejecución directa:**
   ```bash
   ./build_linux.sh
   ```

---

### 🍎 macOS (Apple Silicon / Intel)
1. **Compilar paquete nativo .app:**
   ```bash
   chmod +x build_macos.sh
   ./build_macos.sh
   # Se genera en dist/OpenLegalChile.app listo para tu carpeta /Applications
   ```

---

### 📱 iOS & iPadOS (iPhone / iPad)
1. Abre `http://localhost:8000` (o tu IP local) en **Safari**.
2. Toca el botón **Compartir** (`Share`).
3. Selecciona **"Agregar a la pantalla de inicio"** (*Add to Home Screen*).
4. La aplicación se instalará como una **App Nativa PWA** a pantalla completa con tema oscuro.

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
