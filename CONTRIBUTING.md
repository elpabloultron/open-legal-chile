# 🤝 Guía de Contribución — Open Legal Chile

¡Gracias por tu interés en contribuir a **Open Legal Chile**! Nuestro objetivo es construir la plataforma de inteligencia jurídica y el ecosistema agéntico más riguroso, abierto y accesible para el Derecho Continental de la República de Chile.

Lee también: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) · [CLA.md](CLA.md) · [SECURITY.md](SECURITY.md) · [CONNECTORS.md](CONNECTORS.md) · [AGENTS.md](AGENTS.md)

---

## 🏛️ 1. Principios Jurídicos Inquebrantables

Toda contribución (código, conector, skill, prompt o documento) debe respetar:

* **Primacía de la Ley escrita** (Art. 1 Código Civil) y **efecto relativo de las sentencias** (Art. 3 inc. 2 Código Civil).
* **Prohibición absoluta de Common Law:** rechazamos terminología foránea inexistente en Chile (*at-will employment*, *punitive damages*, *discovery*, *subpoena*, *grand jury*, *deposition*, *privilege log*, *Title VII*, *FLSA*, *OSHA*, *Delaware C-Corp*). Usa solo terminología chilena (*necesidades de la empresa*, *finiquito*, *fuero*, *otrosí*, *casación*, *SpA*, etc.).
* **Citación oficial obligatoria** (ver [AGENTS.md §2](AGENTS.md)):
  * `[BCN - Código del Trabajo, Art. 161]` · `[BCN - Ley N° 21.643, Art. 2]`
  * `[CPR 1980 - Art. 19 N° 24]`
  * `[CS - Rol N° 12.345-2023, Fecha: 15-11-2023]` · `[C.A. de Santiago - Rol N° 456-2024]`
  * `[Dictamen DT N° 1234/15 de 2024]` · `[Dictamen CGR N° E123456 (2024)]`
  * `[Circular SII N° 45 (2023)]` · `[NCG CMF N° 461]` · `[SMA - Expediente SNIFA <Número>]`
* **Anti-alucinación:** si una norma no se verifica en una fuente oficial, márcala `[verificar]`. Nunca inventes citas ni roles de causa.

---

## 💻 2. Entorno de Desarrollo Local

Requisitos: **Python 3.10 – 3.14** (stdlib puro; no hay dependencias de runtime).

```bash
# 1. Clonar el repositorio
git clone https://github.com/elpabloultron/open-legal-chile.git
cd open-legal-chile

# 2. Instalar dependencias de desarrollo (pytest)
pip install -e ".[dev]"

# 3. (Opcional) Credenciales: copia .env.example a .env
#    - BCN_API_KEY, CNE_EMAIL/CNE_PASSWORD para APIs autenticadas
#    - Claves de IA (DEEPSEEK/ANTHROPIC/GEMINI/OPENAI) para chat/critique

# 4. Ejecutar toda la suite de pruebas (21 tests)
python -m pytest tests/ -v

# 5. Probar el servidor MCP (stdio JSON-RPC 2.0)
python openlegal.py mcp

# 6. Pruebas de humo por conector (CLI)
python bcn_connector.py --codigo civil --art 1545
python cgr_connector.py --buscar "probidad"
python openlegal.py check
```

---

## 🗺️ 3. Mapa del Repositorio

```
open-legal-chile/
├── mcp_server.py               # Servidor MCP (13 herramientas, JSON-RPC 2.0 sobre stdio)
├── openlegal.py                # CLI unificado: menu, mcp, chat, search, check, skills, export, critique, generate
├── chat_engine.py              # Motor multi-proveedor (DeepSeek, Claude, Gemini, OpenAI, Ollama) + RAG chileno
├── critique.py                 # Auditoría forense de 5 dimensiones
├── exporters.py                # Escritos OJV (Ley 20.886) → .html / .md / .txt / .json
├── config.py                   # Carga de .env y diagnóstico de credenciales
├── connectors/
│   └── registry.py             # StateRegistry: búsqueda universal en los 10 organismos + caché SQLite
├── domain/models.py            # Dataclasses de dominio (NormaBCN, DictamenCGR, EscritoOJV, ...)
├── *_connector.py              # 10 conectores estatales (BCN, CGR, DT, CNE, Panel, CMF, SII, SMA, TDLC, PJUD)
├── .agents/skills/*/SKILL.md   # 7 habilidades jurídicas (frontmatter + workflows + compuertas)
├── agents/*.json               # 7 perfiles de agente (systemPrompt + tools)
├── skills-lock.json            # Lock de skills con hash SHA-256 por archivo
├── .claude-plugin/marketplace.json  # Marketplace de plugins para Claude
├── evals/                      # Benchmark jurídico chileno (test_cases.json + benchmark.py)
├── tests/                      # Suite pytest (21 tests)
├── docs/architecture.md        # Arquitectura detallada
└── .github/workflows/          # CI (3.10–3.14), monitor de APIs estatales, publish a PyPI
```

---

## 🔌 4. Cómo Agregar un Conector Nuevo

1. **Crea `mi_organismo_connector.py`** con una clase `MiOrganismoClient` que siga el patrón de los existentes:
   * `CACHE_DIR = "mi_organismo_cache/"` + `os.makedirs(..., exist_ok=True)`.
   * Método principal de búsqueda (ej. `search_*(query, limit=10)`) con **degradación elegante**: ante fallo de red o falta de credenciales, retorna estructura vacía o `{"error": ...}` sin romper la sesión.
   * **Procedencia en cada resultado**: identificador citable (N° de dictamen, rol, expediente) y fecha.
2. **Registra la herramienta en `mcp_server.py`:**
   * Agrega el diccionario en `TOOLS` (name, description en español, inputSchema).
   * Agrega el despacho en `handle_tool_call()`.
3. **Agrega el cliente a `connectors/registry.py`:**
   * Importa la clase, instánciala en `__init__` y agrega su bloque en `search_all()` con la clave institucional.
4. **Documenta:** tabla de conectores en [CONNECTORS.md](CONNECTORS.md) y entrada `dataConnectors` en `openlegal.manifest.json`.
5. **Pruebas:** agrega un test en `tests/test_connectors.py` que verifique la **estructura** de la respuesta (nunca dependas de contenido exacto de una API viva).
6. **Cero mocks:** los conectores deben consultar fuentes reales; los tests pueden depender del caché local del repositorio para ser reproducibles offline.

---

## 🧩 5. Cómo Agregar una Skill o Agente

**Skill** (`.agents/skills/<nombre>/SKILL.md`):
* Frontmatter YAML obligatorio: `name` y `description` (en español, específica y orientada a disparo automático).
* Secciones: Principios Rectores → Formato de Citación → Herramientas MCP → Workflows (propósito, pasos numerados, compuertas, formato de salida).
* Incluye la **Compuerta de Revisión Jurídica** en toda salida de alto riesgo.
* Ejecuta `Get-FileHash` (o `sha256sum`) y actualiza `skills-lock.json` con el hash del archivo.

**Agente** (`agents/<nombre>.json`):
* `name`, `displayName`, `description`, `systemPrompt` (con formato de citas) y `tools` (solo nombres existentes en `TOOLS` de `mcp_server.py`).
* Si agregas un área nueva, crea la entrada en `AGENTS.md` §4 y en `README.md` §6.

---

## 🧪 6. Pruebas y Calidad

```bash
python -m pytest tests/ -v            # Suite completa (21 tests)
python -m pytest tests/test_mcp_server.py -v   # Solo servidor MCP
python -m pytest tests/test_connectors.py -v   # Solo conectores (usa APIs vivas con caché)
```

* Todo cambio en `mcp_server.py`, conectores o exporters debe mantener la suite verde.
* Todo cambio en los prompts (`chat_engine.py`, `critique.py`, skills) debe pasar `python evals/benchmark.py` con nota ≥ 7.0/10 y **cero** términos de Common Law penalizados.
* Estilo: código autoexplicativo, sin dependencias nuevas salvo justificación, docstrings en español, encoding UTF-8 explícito en archivos de salida.

---

## 🌿 7. Convención de Commits y Pull Requests

Sigue el historial del repo (Conventional Commits en español):
* `feat(connector): agrega conector SMA para expedientes sancionatorios`
* `fix(mcp): corrige manejo de región en cne_get_centrales_y_proyectos`
* `docs(readme): documenta claves .env y configuración de credenciales`
* `test(registry): cubre búsqueda universal en los 10 organismos`

**Checklist del PR:**
- [ ] Suite completa en verde (`python -m pytest tests/ -v`).
- [ ] Citas conforme al estándar oficial; sin terminología de Common Law.
- [ ] Conectores nuevos documentados en `CONNECTORS.md` y `openlegal.manifest.json`.
- [ ] Skills nuevas registradas en `skills-lock.json` (con hash), `AGENTS.md` y `README.md`.
- [ ] Ningún secreto (`.env`, claves) en el diff.
- [ ] PR vinculado a un issue (si existe).

---

## 🛡️ 8. Reportes y Soporte

* **Bugs / ideas:** abre un issue usando las plantillas de `.github/ISSUE_TEMPLATE/`.
* **Vulnerabilidades:** reporte responsable vía Security Advisory privado (ver [SECURITY.md](SECURITY.md)); nunca en issues públicos.
* **Dudas:** discusiones en el repositorio.

> ⚖️ **Recordatorio:** Open Legal Chile es una herramienta de asistencia técnica. Todo borrador generado debe ser validado por un abogado habilitado antes de su firma e ingreso a la OJV.
