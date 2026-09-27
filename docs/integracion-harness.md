# Integrar Open Legal Chile en cualquier harness

Una instalación, todos los clientes. El objetivo es que **ningún usuario tenga que abrir una
terminal más que para este comando** ni editar archivos de configuración a mano.

```bash
pip install openlegal-chile
openlegal integrar --todos --escribir      # detecta tus harnesses y los configura
```

Sin argumentos, `openlegal integrar` muestra los siete clientes y el archivo de cada uno. Con
`--escribir` guarda la configuración (y **respalda** lo que ya existía en un `.bak`).

## Comando por cliente

| Harness | Comando | Archivo | Verificación |
|---|---|---|---|
| Antigravity | `openlegal integrar antigravity --escribir` | `mcp_config.json` | `tools/list` → 77 |
| Claude Code | `openlegal integrar claude-code --escribir` (o `claude mcp add open-legal-chile openlegal-mcp`) | `.mcp.json` | `/mcp` dentro de la sesión |
| Cursor | `openlegal integrar cursor --escribir` | `.cursor/mcp.json` | panel MCP de Cursor |
| VS Code / Windsurf / Cline | `openlegal integrar vscode --escribir` | `.vscode/mcp.json` | paleta de comandos → MCP |
| Codex | `openlegal integrar codex --escribir` | `.codex/config.toml` | `codex mcp list` |
| dsh (DeepSeek Harness) | `openlegal integrar dsh --escribir` | `cordis.patch.yml` (capa de parche Cordis) | `tools/list` tras reiniciar el perfil |
| Genérico (MCP estándar) | `openlegal integrar generic --escribir` | `.mcp.json` | lo que use tu cliente |

Ningún archivo se pisa: los JSON se **fusionan** (tu otros servidores MCP siguen ahí), el TOML de
Codex y el parche Cordis de dsh se **agregan**, y siempre queda un `.bak` del archivo anterior.

## Cómo verificar que tu harness usa todo

**1. El servidor responde y ve todas las herramientas**

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | openlegal-mcp | \
  python -c "import sys,json; print(len(json.loads(sys.stdin.readline())['result']['tools']), 'herramientas')"
# Esperado: 77 herramientas
```

**2. El doctor no encuentra errores**

```bash
openlegal doctor
# Esperado: estado: OK y las 8 líneas (version, ocr, corpus, grafo, indices, citas, herramientas_mcp, hugging_face)
```

**3. La prueba funcional (el protocolo §2 quater)**

Pedile a tu harness:

> ¿Qué dice el artículo 1438 del Código Civil?

La respuesta correcta **primero consulta el corpus de Hugging Face** (`consulta_maestra`), y trae el
corchete `[BCN - Código Civil, Art. 1438]` **con su texto literal** — no un resumen de memoria. Si
la fuente no responde, el producto dice «sin fuente verificable» en vez de inventar el tenor.

## Las reglas viajan con el producto

`AGENTS.md` (y su espejo `CLAUDE.md`) documenta el protocolo en **§2 quater**: Hugging Face primero,
fuente oficial después, cada cita con su texto literal, y dos formatos de salida (conversación:
respuesta y bloque `Fuentes:` al final; documentos `.docx`: citas a pie de página). Los harness que
leen `AGENTS.md`/`CLAUDE.md` lo toman solos; el resto lo obtiene igual porque **las herramientas
devuelven el bloque `citas` con el texto** en cada resultado citable.

## Si algo no se ve

| Síntoma | Causa habitual | Qué hacer |
|---|---|---|
| El harness no muestra herramientas | No reiniciaste el cliente tras escribir la config | Reiniciá el harness (los hijos MCP se lanzan al arrancar) |
| `openlegal-mcp: command not found` | El paquete no está en el `PATH` del cliente | Reinstalá con `pip install --force-reinstall openlegal-chile` y verificá `which openlegal-mcp` |
| Aparecen menos de 77 herramientas | Perfil restringido del plugin (`laboral`, `dogmatico`…) | Usá el perfil `completo`/`full` |
| Una respuesta cita sin texto | El harness no siguió §2 quater | Agregá a su prompt de sistema: «usá `consulta_maestra` primero y no cites sin `cita_texto`» |
