# Guía de Inicio Rápido (Quickstart)

**Configuración en 60 segundos** para comenzar a usar Open Legal Chile en tu agente de IA preferido (**Claude Code**, **Gemini CLI**, **Cursor**, **VS Code**, **Claude Desktop**, **Antigravity**, **Windsurf**, **OpenCode**, **Codex**).

---

## 🔑 1. Configurar credenciales (opcional)

Copia `.env.example` a `.env` y completa las claves que tengas:

> **🛡️ 100% Libre y Soberano:** Open Legal Chile opera directamente con su **Motor Soberano Local integrado** y los **10 conectores públicos del Estado** sin requerir ninguna API key ni cuentas corporativas.
> Si deseas conectar voluntariamente proveedores comerciales opcionales, puedes definir sus claves en `.env`:

| Variable Opcional | Para qué |
|----------|----------|
| `DEEPSEEK_API_KEY` | Chat jurídico opcional con DeepSeek |
| `ANTHROPIC_API_KEY` | Chat jurídico opcional con Claude |
| `GEMINI_API_KEY` | Chat jurídico opcional con Gemini |
| `OPENAI_API_KEY` | Chat jurídico opcional con OpenAI |
| `OLLAMA_HOST` | Host para Ollama local (por defecto `http://localhost:11434`) |

> Ejecuta `openlegal doctor` para verificar el estado de la instalación (OCR, corpus, grafo, herramientas, skills y agentes).

---

## 🤖 2. Conectar el servidor MCP a tu agente

**Claude Code**: plugin con MCP, 18 skills y 19 agentes (requiere [uv](https://docs.astral.sh/uv/)):

```bash
claude plugin marketplace add elpabloultron/open-legal-chile
claude plugin install open-legal-chile@open-legal-chile
```

Solo el servidor: `claude mcp add open-legal-chile -- uvx --from openlegal-chile openlegal-mcp`

**Gemini CLI**: `gemini extensions install https://github.com/elpabloultron/open-legal-chile`

**Cursor, VS Code, Claude Desktop, Antigravity, Windsurf, Codex, OpenCode, dsh**:

```bash
pip install openlegal-chile
openlegal instalar                         # detecta los harness de la carpeta y los configura
openlegal integrar <cliente> --escribir    # o un cliente puntual (--global: configuración de usuario)
```

Dentro de este repositorio ya vienen configurados `.mcp.json` (Claude Code), `.cursor/mcp.json`,
`.vscode/mcp.json` y `opencode.json`. Detalle por cliente: [docs/integracion-harness.md](docs/integracion-harness.md).

---

## 💻 3. Usar la Consola CLI

```bash
# Iniciar servidor MCP
python openlegal.py mcp

# Búsqueda jurídica universal en los 10 organismos del Estado
python openlegal.py search "confianza legitima contrata"

# Chat jurídico interactivo (autodetecta el proveedor con API key)
python openlegal.py chat

# Auditoría forense de 5 dimensiones sobre un escrito
python openlegal.py critique demanda.txt

# Generar borrador forense OJV (demanda_civil, proteccion, laboral, ppa)
python openlegal.py generate laboral

# Verificar credenciales y conectores
python openlegal.py check
```

---

## 🧩 4. Habilidades y agentes jurídicos chilenos

Open Legal Chile incluye **18 habilidades** (`.agents/skills/`) y **19 agentes** (`agents/*.json`, con
su versión `agents/*.md` para Claude Code). Algunos ejemplos por área:

| Área | Skill | Agente |
|------|-------|--------|
| Laboral | `chilean-employment-legal` | `agente-laboral` |
| Litigación OJV | `chilean-litigation-legal` | `agente-litigios` |
| Administrativo / CGR | `chilean-administrative-legal` | `agente-regulatorio` |
| Probidad | `chilean-probity-investigation` | `agente-probidad` |
| Energía | `chilean-energy-legal` | `agente-energia` |
| Ambiental / SMA | `chilean-environmental-legal` | `agente-ambiental` |
| Contratos | `chilean-contract-legal` | `agente-contratos` |
| Corporativo | `chilean-corporate-legal` | `agente-corporativo` |
| Mesa de entrada | `chilean-case-intake` | `agente-mesa` |
| Peritaje y OCR | `chilean-forensic-evidence` | `agente-forense` |

La lista completa sale con `openlegal skills` o con la herramienta MCP `skills_listar`.

Cada skill y agente opera **estrictamente bajo Derecho Continental chileno** (Civil Law), prohíbe terminología de Common Law y exige el estándar de citación oficial de [AGENTS.md](AGENTS.md).

---

## ⚠️ 5. Reglas de seguridad

- **Todo borrador es para revisión de abogado habilitado.** Los escritos generados incluyen la **Compuerta de Revisión Jurídica** y deben validarse antes de su ingreso a la OJV o notificación a contrapartes.
- **Nunca** subas `.env` al repositorio (está en `.gitignore`).
- Las citas siempre llevan su fuente oficial (`[BCN - ...]`, `[Dictamen DT N° ...]`, `[CS - Rol N° ..., Fecha: ...]`).

---

## ❓ Problemas frecuentes

- **"Falta DEEPSEEK_API_KEY"** → configura la clave en `.env` o usa `--provider` con un proveedor configurado.
- **Sin datos de CNE** → completa `CNE_EMAIL`/`CNE_PASSWORD` en `.env` (sin credenciales, el conector usa caché local si existe).
- **Encoding roto en Windows** → los comandos fuerzan UTF-8; usa PowerShell o Windows Terminal moderno.
- **Más ayuda** → `python openlegal.py --help` y [README.md](README.md).
