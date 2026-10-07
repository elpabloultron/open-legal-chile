# 🔌 Instalación en 1-Click / 1-Comando (Plugins & MCP)
## Open Legal Chile Suite v1.13.0

> El camino directo es un solo comando: `pip install openlegal-chile && openlegal instalar`. Esta
> página reúne las **vías por harness** (plugins, extensiones, registros). La guía completa, con
> archivos y verificación por cliente, está en [docs/integracion-harness.md](docs/integracion-harness.md).

**Open Legal Chile Suite** implementa el protocolo estándar **MCP (Model Context Protocol)** y trae
manifiestos listos para los harness de agentes más usados. Todos exponen las mismas **87 herramientas**.

**Requisito para plugins y extensiones:** [uv](https://docs.astral.sh/uv/) (`uvx`). El servidor se
lanza con `uvx --from openlegal-chile openlegal-mcp`, que instala el paquete de PyPI en un entorno
aislado. La primera vez descarga ~150 MB; precalentalo con
`uvx --from openlegal-chile openlegal-mcp < /dev/null` para que el primer arranque no se corte.

---

## ⚡ Métodos de Instalación

### 1. 🤖 Claude Code (CLI oficial de Anthropic)

#### Opción A: plugin (recomendado): MCP + 18 skills + 19 agentes
```bash
claude plugin marketplace add elpabloultron/open-legal-chile
claude plugin install open-legal-chile@open-legal-chile
```
El marketplace también ofrece las skills por materia (`chilean-employment-legal`,
`chilean-litigation-legal`, …). Cada una instala el plugin principal como dependencia, porque usa
sus herramientas MCP.

#### Opción B: solo el servidor MCP
```bash
claude mcp add open-legal-chile -- uvx --from openlegal-chile openlegal-mcp
```
Con el paquete ya instalado (`pip install openlegal-chile`): `claude mcp add open-legal-chile -- openlegal-mcp`.
El `--` separa las opciones de `claude mcp add` de las del servidor y es obligatorio.

---

### 2. ♊ Gemini CLI

```bash
gemini extensions install https://github.com/elpabloultron/open-legal-chile
```
La extensión (`gemini-extension.json`) lanza el servidor con uvx y agrega `GEMINI.md` al contexto.

---

### 3. ⚡ Cursor IDE

El repositorio incluye `.cursor/mcp.json`: al abrir la carpeta en Cursor aparece la opción de
habilitar el servidor `open-legal-chile`. En cualquier otro proyecto:
```bash
openlegal integrar cursor --escribir          # o --global para ~/.cursor/mcp.json
```

---

### 4. 🌊 VS Code (Copilot)

El repositorio incluye `.vscode/mcp.json`. VS Code usa la clave **`servers`** (no `mcpServers`):
```json
{
  "servers": {
    "open-legal-chile": {
      "type": "stdio",
      "command": "python3",
      "args": ["${workspaceFolder}/mcp_server.py"],
      "env": { "PYTHONIOENCODING": "utf-8", "PYTHONPATH": "${workspaceFolder}" }
    }
  }
}
```
En otro proyecto: `openlegal integrar vscode --escribir` (o `--global` para tu configuración de usuario).

---

### 5. 🏄 Windsurf, Codex, OpenCode, dsh

```bash
openlegal integrar windsurf --escribir      # ~/.codeium/windsurf/mcp_config.json
openlegal integrar codex --escribir         # .codex/config.toml
openlegal integrar opencode --escribir      # opencode.json
openlegal integrar dsh --escribir           # cordis.patch.yml
```

---

### 6. 🪐 Google Antigravity

`mcp_config.json` del repositorio ya es portable (usa `openlegal-mcp`). Para tu usuario:
```bash
openlegal integrar antigravity --escribir --global    # ~/.gemini/antigravity/mcp_config.json
```

---

### 7. 🍎 Claude Desktop (macOS / Windows / Linux)

```bash
openlegal integrar claude-desktop --escribir
```
Escribe la ruta absoluta de `openlegal-mcp` en `claude_desktop_config.json`. Claude Desktop no hereda
el PATH de la terminal, así que un `openlegal-mcp` a secas no funcionaría. Con `--uvx` usa uvx.

---

### 8. 🌐 Registros: MCP Registry y Smithery

- **MCP Registry**: `server.json` publica el paquete PyPI `openlegal-chile` (ejecutable `openlegal-chile`, `uvx openlegal-chile`).
- **Smithery**: [smithery.ai/servers/pablobenavidesjorquera/open-legal-chile](https://smithery.ai/servers/pablobenavidesjorquera/open-legal-chile)
  ```bash
  npx -y smithery mcp add pablobenavidesjorquera/open-legal-chile
  ```

---

### ⚡ 9. Perfiles temáticos livianos (ahorro de tokens)

Para ahorrar contexto, o para no pasarte del límite de herramientas de clientes como Cursor o
Windsurf, limitá el catálogo con `--profile <nombre>` o con la variable `OPENLEGAL_PROFILE`. En el
plugin de Claude Code se elige al activarlo. Todo perfil incluye `consulta_maestra`, `cita_texto` y
`suite_doctor`, que el protocolo de citación exige.

| Perfil | Herramientas | Foco |
|---|---|---|
| `laboral` | 14 | BCN, DT, PJUD, doctrina, escritos OJV |
| `inmobiliario` | 13 | CBR, mandato Art. 7 CPC, BCN civil |
| `litigios` | 17 | PJUD, proveídos, recurso de protección, OCR |
| `regulatorio` | 21 | CGR, InfoProbidad, CMF, SII, SMA, CNE, Panel, TDLC |
| `corporativo` | 16 | CMF, SII, TDLC, INAPI, derechos ARCO, RUT |
| `dogmatico` | 18 | doctrina, LegalGraphify, Academia Judicial, Hugging Face |
| `clinica` | 10 | lenguaje claro, intake, auditoría de borradores |
| (sin perfil) | 87 | todo |

```bash
openlegal-mcp --profile laboral        # o: openlegal mcp --profile laboral
```

---

## 🛠️ Verificación de Instalación

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | openlegal-mcp | \
  python3 -c "import sys,json; print('✅', len(json.loads(sys.stdin.readline())['result']['tools']), 'herramientas MCP')"
openlegal doctor
```

Salida esperada: `✅ 87 herramientas MCP` y el doctor sin ❌.

---

## 🛡️ Principios de Privacidad y Costo Cero
- **100% código abierto (Apache-2.0).**
- **Cero API keys obligatorias:** BCN, CGR, DT, PJUD, SII, CMF, SMA, TDLC, doctrina y CBR se consultan contra fuentes públicas sin cobro. El token de Hugging Face es opcional: solo da más cuota de descarga.
- **Sin telemetría oculta ni bloqueo de proveedores:** con MCP, el usuario es dueño de sus datos y de su infraestructura de IA.
