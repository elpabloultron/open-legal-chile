---
trigger: always_on
description: Grafo del CÓDIGO de la suite (graphify-out/, local). El derecho chileno se consulta con las herramientas MCP graphify_*, no con esta CLI.
---

## graphify (grafo del código)

`graphify-out/` es el grafo del código (módulos, herramientas MCP, conectores, pruebas). Es local y
no se versiona; se construye con `uvx --from graphifyy==0.9.79 graphify update .` y su alcance lo
fija `.graphifyignore` (sin doctrina, datos ni skills). El grafo jurídico es
`data/legal_knowledge_graph.json` (herramientas MCP `graphify_*`); para derecho chileno, primero
`consulta_maestra` y `cita_texto`.

Reglas:
- Pregunta sobre el código: si existe `graphify-out/graph.json`, primero `graphify query "<pregunta>"`;
  `graphify path "<A>" "<B>"` para relaciones y `graphify explain "<símbolo>"` para un nodo.
- `graphify-out/GRAPH_REPORT.md`, solo para una revisión amplia de arquitectura.
- Después de modificar código, `graphify update .` (solo AST, sin costo de API; no ensucia git).
