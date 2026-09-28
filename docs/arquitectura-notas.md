# Notas de arquitectura

Decisiones de la pasada de mejoras de eficiencia/arquitectura/datos (2026-09), para que quien
venga no reabra lo ya cerrado ni repita el análisis.

## 1. Los conectores se quedan en la raíz (no se mueven a `connectors/`)

Decisión explícita: **no** mover los conectores (`bcn_connector.py`, `cgr_connector.py`, …) a
`connectors/`. Están declarados como módulos planos en `[tool.setuptools] py-modules` y se importan
por su nombre raíz desde decenas de sitios (`mcp_server.py`, `agents_runtime.py`, `openlegal.py`,
`case_intake.py`, tests…): moverlos obligaría a tocar todos los imports y el empaquetado, con riesgo
alto y beneficio cosmético. `connectors/` conserva su rol actual (registro de fuentes). La parte con
valor real —la caché homogénea— se atendió donde dolía: la caché del corpus HF tiene TTL y
revalidación por `blob_id` (comando `openlegal cache`), y LeyChile degrada a la copia local vencida
cuando el servicio no responde.

## 2. `mcp_server.py` delega en `servidor/` (un módulo por dominio)

Las 87 herramientas viven en `servidor/` — `ambiental.py`, `corpus.py`, `conectores.py`,
`forense.py`, `casos.py`, `suite.py` — cada una con sus esquemas (`TOOLS`) y su despacho
(`despachar(name, args)`). `mcp_server.py` conserva el protocolo, los recursos/prompts, los helpers
compartidos y el ensamblado de `TOOLS` en el orden original de listado. Los bloques despachados usan
los objetos vivos del servidor: cada módulo los trae a su espacio de nombres en cada llamada
(`_refrescar()`), lo que mantiene las sustituciones de las pruebas (monkeypatch) y evita copias que
deriven. Guardas que lo protegen: `tests/test_paridad_cli_mcp.py`, `tests/test_mcp_e2e_live.py`
(87 herramientas), `tests/test_empaquetado.py` (el paquete viaja en el wheel) y la comprobación de
conteo al importar `mcp_server`.

## 3. El arranque del MCP queda como está (sin lazy loading)

Medido en esta pasada: `import mcp_server` tarda 0,40 s en esta máquina. El arranque perezoso por
herramienta (PEP 562 sobre las instanciaciones de clientes) fue evaluado y **descartado**: el
ahorro no paga el riesgo de que un cliente se construya tarde y cambie errores tempranos por
errores sutiles. Si algún día arranca lento de verdad, el apéndice A del plan (2026-09) tiene el
bosquejo y `scripts/bench_rendimiento.py` mide el antes/después.
