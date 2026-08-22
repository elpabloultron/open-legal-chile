# Guía de Inicio Rápido (Quickstart)

**Configuración en 60 segundos** para comenzar a usar Open Legal Chile en tu agente de IA preferido (**Antigravity**, **Claude Code**, **Cursor**, **OpenCode**, **Codex**).

---

## 🔑 1. Configurar credenciales (opcional)

Copia `.env.example` a `.env` y completa las claves que tengas:

| Variable | Para qué |
|----------|----------|
| `BCN_API_KEY` | API v1 de BCN Ley Chile (el XML público no la requiere) |
| `CNE_EMAIL` / `CNE_PASSWORD` | API autenticada de Energía Abierta (CNE) |
| `DEEPSEEK_API_KEY` | Chat jurídico con DeepSeek |
| `ANTHROPIC_API_KEY` | Chat jurídico con Claude |
| `GEMINI_API_KEY` | Chat jurídico con Gemini |
| `OPENAI_API_KEY` | Chat jurídico con OpenAI |
| `OLLAMA_HOST` | Modelo local vía Ollama |
| `PORT` | Reservado para futuros servicios HTTP |

> Si no configuras ninguna clave de IA, el chat usa Ollama local si está disponible. `openlegal check` muestra el diagnóstico completo.

---

## 🤖 2. Conectar el servidor MCP a tu agente

**Antigravity (Google Gemini) / Cursor** — agrega a `mcp_config.json`:

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

**Claude Code**:

```bash
claude mcp add open-legal-chile python mcp_server.py
```

**OpenCode** — ya viene configurado en `opencode.json` (usa `mcp_server.py` relativo al proyecto).

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

Open Legal Chile incluye **7 habilidades** (`.agents/skills/`) y **7 agentes** (`agents/*.json`):

| Área | Skill | Agente |
|------|-------|--------|
| Laboral | `chilean-employment-legal` | `agente-laboral` |
| Litigación OJV | `chilean-litigation-legal` | `agente-litigios` |
| Administrativo / CGR | `chilean-administrative-legal` | `agente-regulatorio` |
| Energía | `chilean-energy-legal` | `agente-energia` |
| Ambiental / SMA | `chilean-environmental-legal` | `agente-ambiental` |
| Contratos | `chilean-contract-legal` | `agente-contratos` |
| Corporativo | `chilean-corporate-legal` | `agente-corporativo` |

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
