# Integrar Open Legal Chile en cualquier harness

Una instalación, todos los clientes. El objetivo es que **ningún usuario tenga que abrir una
terminal más que para este comando** ni editar archivos de configuración a mano.

Hay dos caminos y los dos dejan las **87 herramientas MCP** visibles:

| Camino | Requisito | Comando del servidor |
|---|---|---|
| **uvx** (recomendado para plugins y extensiones) | tener [uv](https://docs.astral.sh/uv/) | `uvx --from openlegal-chile openlegal-mcp` |
| **pip** | `pip install openlegal-chile` | `openlegal-mcp` (o su ruta absoluta) |

La primera ejecución de uvx descarga las dependencias (~150 MB: onnxruntime, opencv, pymupdf, scipy).
Para que el primer arranque no supere el tiempo de espera del harness, precalentalo una vez:

```bash
uvx --from openlegal-chile openlegal-mcp < /dev/null
```

## Claude Code

**Plugin (recomendado)**: trae el servidor MCP, las 18 skills y los 19 agentes.

```bash
claude plugin marketplace add elpabloultron/open-legal-chile
claude plugin install open-legal-chile@open-legal-chile
```

Al activarlo, Claude Code pide dos valores opcionales: el **perfil** de herramientas (vacío = las 87)
y el **token de Hugging Face**. Las skills por materia (`chilean-employment-legal`, etc.) también se
pueden instalar sueltas; cada una trae el plugin principal como dependencia.

**Solo el servidor MCP** (sin skills ni agentes):

```bash
claude mcp add open-legal-chile -- uvx --from openlegal-chile openlegal-mcp    # proyecto actual
claude mcp add -s user open-legal-chile -- uvx --from openlegal-chile openlegal-mcp  # todos tus proyectos
```

El `--` es obligatorio: separa las opciones de `claude mcp add` de las del servidor.

**Trabajando dentro de este repositorio**: el `.mcp.json` de la raíz lanza `python3 mcp_server.py`.
No lo actives junto con el plugin, porque verías cada herramienta dos veces.

Verificación: `/mcp` dentro de la sesión, o `claude mcp list`.

## Gemini CLI

**Extensión (recomendado)**:

```bash
gemini extensions install https://github.com/elpabloultron/open-legal-chile
```

La extensión lanza el servidor con uvx y agrega `GEMINI.md` (reglas de citación) al contexto. Se
configura con `gemini extensions config open-legal-chile` (perfil y token de Hugging Face).

Solo el servidor: `openlegal integrar gemini --escribir` (escribe `.gemini/settings.json`).

## Resto de los clientes: `openlegal integrar`

```bash
pip install openlegal-chile && openlegal instalar     # detecta los harness de la carpeta y los configura
openlegal integrar                                    # lista clientes y archivos
openlegal integrar <cliente> --escribir               # configuración del proyecto
openlegal integrar <cliente> --escribir --global      # configuración de usuario
openlegal integrar <cliente> --escribir --uvx         # lanzar con uvx en vez de openlegal-mcp
```

Por defecto se escribe la **ruta absoluta** de `openlegal-mcp`. Las apps de escritorio (Claude
Desktop, Cursor o VS Code abiertos desde el dock) no heredan el PATH de la terminal, y un
`openlegal-mcp` a secas no se encontraría.

| Harness | Cliente | Archivo del proyecto | Archivo global (`--global`) |
|---|---|---|---|
| Claude Code | `claude-code` | `.mcp.json` | se registra con `claude mcp add -s user` |
| Claude Desktop | `claude-desktop` | — | `claude_desktop_config.json` en la carpeta de soporte del SO |
| Cursor | `cursor` | `.cursor/mcp.json` | `~/.cursor/mcp.json` |
| VS Code (Copilot) | `vscode` | `.vscode/mcp.json` (clave `servers`) | `Code/User/mcp.json` en la carpeta de soporte del SO |
| Gemini CLI | `gemini` | `.gemini/settings.json` | `~/.gemini/settings.json` |
| Antigravity | `antigravity` | `mcp_config.json` | `~/.gemini/antigravity/mcp_config.json` |
| Windsurf | `windsurf` | — | `~/.codeium/windsurf/mcp_config.json` |
| Codex | `codex` | `.codex/config.toml` | `~/.codex/config.toml` |
| OpenCode | `opencode` | `opencode.json` (clave `mcp`) | `opencode/opencode.json` en la carpeta de configuración |
| dsh (DeepSeek Harness) | `dsh` | `cordis.patch.yml` | `~/cordis.patch.yml` |
| Genérico (MCP estándar) | `generic` | `.mcp.json` | `~/.mcp.json` |

Ningún archivo se pisa: los JSON se **fusionan** (tus otros servidores MCP siguen ahí), el TOML de
Codex y el parche Cordis de dsh se **agregan**, y siempre queda un `.bak` del archivo anterior.

Otros registros: el servidor está publicado en el registro MCP (`server.json`, paquete PyPI
`openlegal-chile`, ejecutable `openlegal-chile`) y en Smithery (`smithery.yaml`).

## Límites de herramientas por cliente

Algunos clientes limitan cuántas herramientas MCP admiten en total. Si ya tenés otros servidores,
las 87 pueden pasarse del límite. En ese caso usá un **perfil**, que expone entre 10 y 21
herramientas y siempre incluye `consulta_maestra`, `cita_texto` y `suite_doctor`:

```bash
OPENLEGAL_PROFILE=laboral openlegal-mcp          # o: openlegal-mcp --profile laboral
```

Perfiles: `laboral`, `inmobiliario`, `litigios`, `regulatorio`, `corporativo`, `dogmatico`, `clinica`.

## Cómo verificar que tu harness usa todo

**1. El servidor responde y ve todas las herramientas**

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | openlegal-mcp | \
  python -c "import sys,json; print(len(json.loads(sys.stdin.readline())['result']['tools']), 'herramientas')"
# Esperado: 87 herramientas
```

**2. El doctor no encuentra errores**

```bash
openlegal doctor
# Revisa versión, OCR, corpus, grafo, índices, citas, herramientas MCP, recursos (skills, agentes y
# protocolo), Hugging Face, entorno (uvx, poppler, nlm) y la configuración MCP de la carpeta.
```

**3. La prueba funcional (el protocolo §2 quater)**

Pedile a tu harness:

> ¿Qué dice el artículo 1438 del Código Civil?

La respuesta correcta **primero consulta el corpus de Hugging Face** (`consulta_maestra`) y trae el
corchete `[BCN - Código Civil, Art. 1438]` **con su texto literal**, no un resumen de memoria. Si
la fuente no responde, el producto dice «sin fuente verificable» en vez de inventar el tenor.

## Las reglas viajan con el producto

El servidor envía el protocolo de citación en el campo `instructions` del `initialize`, así que
todo harness compatible con MCP lo recibe sin configurar nada. Además está el prompt
`protocolo_citas`, el recurso `openlegal://reglas/citacion` y `AGENTS.md` §2 quater. Las
herramientas devuelven el bloque `citas` con el texto literal en cada resultado citable.

## Si algo no se ve

| Síntoma | Causa habitual | Qué hacer |
|---|---|---|
| El harness no muestra herramientas | No reiniciaste el cliente tras escribir la config | Reiniciá el harness: los servidores MCP se lanzan al arrancar |
| `uvx: command not found` | uv no está instalado | Instalá uv, o usá el camino pip: `openlegal integrar <cliente> --escribir` |
| El primer arranque se corta por tiempo | uvx todavía está descargando dependencias | Precalentá con `uvx --from openlegal-chile openlegal-mcp < /dev/null`; en Claude Code también sirve `MCP_TIMEOUT=60000` |
| `openlegal-mcp: command not found` | El paquete no está en el PATH del cliente | Volvé a correr `openlegal integrar <cliente> --escribir`, que escribe la ruta absoluta |
| Aparecen menos de 87 herramientas | Hay un perfil activo (`OPENLEGAL_PROFILE` o `--profile`) | Quitá el perfil para ver todas |
| Una respuesta cita sin texto | El harness no siguió §2 quater | Agregá a su prompt de sistema: «usá `consulta_maestra` primero y no cites sin `cita_texto`» |
