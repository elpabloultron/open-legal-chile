# 🔌 Instalación en 1-Click / 1-Comando (Plugins & MCP)
## Open Legal Chile Suite v1.3.0

**Open Legal Chile Suite** implementa de forma nativa el protocolo estándar **MCP (Model Context Protocol)** y cuenta con manifiestos preconfigurados para su integración inmediata y sin fricción ("zero-config") en todos los entornos de agentes de Inteligencia Artificial líderes del mercado.

---

## ⚡ Métodos de Instalación en 1-Click / 1-Comando

### 1. 🤖 Claude Code (CLI Oficial de Anthropic)

#### Opción A: Como Plugin Nativo de Claude Code (Recomendado)
Desde cualquier terminal en tu proyecto:
```bash
claude plugin add elpabloultron/open-legal-chile
```
*Claude Code detectará automáticamente el archivo `.claude-plugin/plugin.json` y registrará las 54 herramientas jurídicas.*

#### Opción B: Como Servidor MCP en Claude Code
```bash
claude mcp add open-legal-chile python3 -m openlegal mcp
```
O si clonaste el repositorio localmente:
```bash
claude mcp add open-legal-chile python3 /ruta/a/open-legal-chile/mcp_server.py
```

---

### 2. ⚡ Cursor IDE (1-Click Workspace Auto-Detection)

El repositorio incluye el archivo `.cursor/mcp.json`. Al clonar o abrir la carpeta `open-legal-chile` en **Cursor**:
1. Abre Cursor en la carpeta del repositorio:
   ```bash
   cursor /ruta/a/open-legal-chile
   ```
2. Aparecerá una notificación emergente automática:
   > *"MCP Server detected: open-legal-chile. Do you want to enable it?"*
3. Haz clic en **Enable**.
4. ¡Listo! Ya puedes pedirle al agente de Cursor:
   > *"Analiza este borrador de demanda civil aplicando el Artículo 254 del CPC y revisa si el mandato judicial cumple con el Artículo 7 del CPC."*

*Configuración manual en Cursor (`Settings -> Features -> MCP -> Add New MCP Server`):*
- **Name:** `open-legal-chile`
- **Type:** `stdio`
- **Command:** `python3`
- **Args:** `mcp_server.py`

---

### 3. 🌊 VS Code / Windsurf / Cline / Roo Code

El repositorio incluye el archivo `.vscode/mcp.json`. Cuando abras la carpeta en **VS Code**, **Windsurf** o con extensiones como **Cline** o **Roo Code**, el servidor MCP se carga automáticamente.

Contenido del archivo de configuración (`.vscode/mcp.json`):
```json
{
  "mcpServers": {
    "open-legal-chile": {
      "command": "python3",
      "args": ["${workspaceFolder}/mcp_server.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

---

### 4. 🌐 Registro Global Smithery.ai (1-Comando Universal)

Gracias a la configuración `smithery.yaml`, puedes instalar Open Legal Chile en cualquier cliente soportado con un único comando:

#### Para Claude Desktop / Claude Code:
```bash
npx -y @smithery/cli install openlegal-chile --client claude
```

#### Para Cursor:
```bash
npx -y @smithery/cli install openlegal-chile --client cursor
```

---

### 5. 🪐 Google Antigravity (Multi-Agente Autónomo)

En **Google Antigravity**, la suite se conecta inmediatamente referenciando `mcp_config.json` en las configuraciones del workspace o en `~/.gemini/antigravity/mcp_config.json`:

```json
{
  "mcpServers": {
    "open-legal-chile": {
      "command": "python3",
      "args": ["/ruta/absoluta/open-legal-chile/mcp_server.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

---

### 6. 🍎 Claude Desktop (macOS / Windows / Linux)

Agrega lo siguiente en tu archivo de configuración de Claude Desktop:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "open-legal-chile": {
      "command": "python3",
      "args": ["/ruta/absoluta/open-legal-chile/mcp_server.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

---

## 🛠️ Verificación de Instalación

Para comprobar que el servidor MCP responde correctamente en tu máquina, ejecuta en la terminal:

```bash
python3 -c "
import subprocess, json
p = subprocess.Popen(['python3', 'mcp_server.py'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
stdout, _ = p.communicate(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}) + '\n', timeout=5)
tools = json.loads([l for l in stdout.splitlines() if 'result' in l][0])['result']['tools']
print(f'✅ Open Legal Chile Suite activa: {len(tools)} herramientas MCP disponibles.')
"
```

Salida esperada:
```text
✅ Open Legal Chile Suite activa: 54 herramientas MCP disponibles.
```

---

## 🛡️ Principios de Privacidad y Costo Cero
- **100% Código Abierto (Apache-2.0).**
- **Cero API Keys obligatorias:** Todas las consultas a BCN, CGR, DT, PJUD, SII, CMF, SMA, TDLC, Doctrina FTS5 y CBR se realizan de forma soberana o contra APIs públicas sin cobro.
- **Sin telemetría oculta ni bloqueo de proveedores:** El estándar MCP garantiza que el usuario es el dueño absoluto de sus datos y de su infraestructura de IA.
