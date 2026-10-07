# Auditoría E2E: suite, servidor MCP y harness (2026-10-07, v1.13.0)

Objetivo: que las 87 herramientas MCP, las 18 skills y los 19 agentes funcionen completos en Claude
Code (CLI, web y plugin) y en cualquier otro harness.

Cómo se midió:
- Suite pytest completa.
- `claude plugin validate` y `claude --plugin-dir . plugin details`.
- Claude Code real en modo headless: llamada MCP a través del plugin y un subagente que usa `bcn_get_codigo`.
- `gemini extensions validate`.
- Validación de `server.json` contra el schema del registro MCP.
- Wheel construido e instalado en un venv limpio.
- Barrido de las 87 herramientas con el cliente oficial del SDK de MCP (Python, `mcp` 2.x).

## Resultado

| Medición | Antes | Después |
|---|---|---|
| Suite pytest | 543 pasan, 2 fallan (BCN 429 tras proxy) | 700 pasan, 2 se saltan, 0 fallan |
| Plugin Claude Code (`plugin details`) | Skills (0) · Agents (0) · MCP (1) | Skills (18) · Agents (19) · MCP (1) |
| Wheel instalado: `skills_listar` / `agent_list` | 0 / 0 (no viajaban) | 18 / 19 |
| Barrido de 87 herramientas (SDK oficial) | 79 ok, salidas de hasta 3,7 M caracteres, 1 línea no-JSON en stdout | 82 ok, máximo 53 mil caracteres, stdout limpio |
| Monitor diario de APIs del Estado | verde falso (ModuleNotFoundError tapado) | instala la suite, falla de verdad y abre un issue |

Las 4 herramientas que siguen en `error` en el barrido son errores controlados con mensaje útil:
`notebooklm_*` necesita la CLI `nlm`; `infoprobidad_get_dip`, `sii_descargar_oficio` y
`generar_documento` rechazan los datos de muestra del barrido. `suite_auto_update` se omitió a
propósito, porque hace `git pull` / `pip install`.

## Hallazgos y estado

| # | Severidad | Hallazgo | Estado |
|---|---|---|---|
| 1 | Crítico | El plugin de Claude Code cargaba 0 skills y 0 agentes | ✅ `skills` en `plugin.json`; agentes `.md` generados desde los JSON |
| 2 | Crítico | MCP del plugin con `python3 -m openlegal mcp`: solo andaba con el paquete instalado en ese python3, y no en Windows | ✅ `uvx --from openlegal-chile==<versión> openlegal-mcp` |
| 3 | Crítico | `marketplace.json` sin el plugin principal y sin 5 skills | ✅ suite completa primero; las skills dependen de ella |
| 4 | Crítico | El wheel no llevaba `AGENTS.md`, skills, agentes ni la guía de integración | ✅ data-files en `share/openlegal-chile` + `recursos.ruta_recurso()` |
| 5 | Crítico | `.vscode/mcp.json` con la clave `mcpServers` (VS Code la ignora) | ✅ `servers` + `type: stdio` |
| 6 | Crítico | `mcp_config.json` con la ruta `/home/pablo/...` | ✅ portable |
| 7 | Crítico | Hooks `graphify` fallaban en cada herramienta si graphify no estaba instalado | ✅ tolerantes |
| 8 | Crítico | Monitor de APIs del Estado falsamente en verde | ✅ |
| 9 | Alto | JSON inválido en la primera línea mataba el servidor; ids equivocados después | ✅ `-32700` con id null |
| 10 | Alto | Versión de protocolo desconocida negociada a la más antigua; lotes JSON-RPC ignorados | ✅ |
| 11 | Alto | Esquema de `recurso_proteccion_generar` rechazado por clientes estrictos (unión de tipos, `required` sin `properties`) | ✅ + prueba sobre las 87 herramientas |
| 12 | Alto | Los perfiles no exponían `consulta_maestra`/`cita_texto`, que exige el protocolo | ✅ |
| 13 | Alto | `agents/examen_grado.json` usaba `doctrina_buscar` (no existe); los subagentes exportados quedaban sin herramientas | ✅ |
| 14 | Alto | `uvx openlegal-chile` / registro MCP sin ejecutable con el nombre del paquete | ✅ alias `openlegal-chile` |
| 15 | Alto | Faltaban Gemini CLI, Windsurf, Claude Desktop y OpenCode; rutas globales equivocadas; `~/.mcp.json` como alcance de usuario de Claude Code | ✅ `integraciones_harness` + `gemini-extension.json` |
| 16 | Alto | Sin `instructions` en `initialize` (protocolo de citación) | ✅ |
| 17 | Alto | **`config.pedir_http` ignoraba HTTP(S)_PROXY/NO_PROXY**: tras un proxy (estudio, CI, nube) la BCN respondía 429 o no respondía | ✅ túnel CONNECT y NO_PROXY |
| 18 | Alto | **Salidas gigantes**: `caso_ejecutar` 3,7 M de caracteres (pedía Códigos completos), `ocr_extract_pdf` 3,2 M, `cgr_search_auditorias` 220 mil; Claude Code corta las respuestas sobre ~25 000 tokens | ✅ `caso_ejecutar` pide artículos puntuales; tope genérico `OPENLEGAL_MAX_SALIDA` con la salida completa en disco |
| 19 | Alto | **PyMuPDF escribía en el stdout del protocolo** (aviso de `import fitz`), fuera del `redirect_stdout` | ✅ mensajes a stderr; `import pymupdf` |
| 20 | Medio | Las pruebas reescribían `data/catalogo/*.jsonl` (versionados) | ✅ `procesar_lote(actualizar_catalogo=False)` |
| 21 | Medio | `query_openlegal_laws.py` (ruta personal, red y escritura al importar) viajaba en el wheel | ✅ movido a `scripts/`; su salida a `exports/` |
| 22 | Medio | `smithery.yaml` fuera de formato; `server.json` sin `runtimeHint` | ✅ |
| 23 | Medio | `suite_auto_update`/`suite_instalar` anotadas como no destructivas | ✅ |
| 24 | Medio | Documentación con comandos inexistentes (`claude plugin add`), sin `--` y con totales de 7/13/75/77/85 | ✅ |
| 25 | Bajo | `openlegal mcp --profile` no se aceptaba | ✅ |

## Pendientes (fuera de este cambio)

- `doctrina_ingestar_documento` tarda ~170 s por documento: reindexa el corpus completo. Algunos
  clientes cortan las herramientas a los 60 s.
- Paquetes de primer nivel con nombres genéricos (`data`, `connectors`, `domain`) en site-packages,
  con riesgo de choque con otros paquetes. uvx lo evita porque aísla el entorno.
- Las correcciones llegan a quien usa uvx o pip cuando se publique una versión nueva en PyPI
  (`python scripts/bump_version.py patch`). Hasta entonces, plugin y extensión lanzan 1.13.0.

## Qué instalar

| Componente | Necesario para |
|---|---|
| Python ≥ 3.10 + `openlegal-chile` | CLI y `openlegal integrar` |
| `uv` (`uvx`) | Plugin de Claude Code, extensión de Gemini, `--uvx` |
| poppler-utils | Solo las ingestas masivas de PDF (el OCR usa PyMuPDF y RapidOCR) |
| CLI `nlm` | Solo `notebooklm_*` |
| `HF_TOKEN` | Opcional: más cuota del Hub de Hugging Face |
| graphify (`uv tool install graphifyy`) | Solo desarrollo del repo |

Ningún plugin de terceros de Claude Code es necesario: el repositorio es el plugin.
