# Integración con Graphify: el grafo de código y el grafo jurídico

[Graphify](https://github.com/Graphify-Labs/graphify) es una herramienta **de terceros** que
construye un grafo de conocimiento de un repositorio (código y AST). Open Legal Chile **no la
incluye ni la forkea**: la consume. Esta página dice exactamente cómo se conectan y qué se midió,
para que nadie tenga que creer una cifra de folleto.

## Qué aporta cada uno

| | Graphify | Open Legal Chile |
|---|---|---|
| Qué grafica | el código del repositorio y sus dependencias (AST) | 58 tratados de doctrina chilena, normas BCN, criterios de la Corte Suprema, vías procesales y autores |
| Artefacto | `graphify-out/graph.json` (Node-Link), **local y no versionado**; su alcance lo fija `.graphifyignore` | `data/legal_knowledge_graph.json` (Node-Link) |
| Cómo se produce | `graphify update .` (solo AST, sin costo de API, ~9 s; en la nube lo corre `.claude/hooks/graphify-sesion.sh`) | `LegalGraphifyEngine.construir_grafo_desde_doctrina()` (0,15 s sobre el corpus) |
| Cómo se consulta | CLI de Graphify (`graphify query/path/explain`) | herramientas MCP `graphify_*` y `openlegal graph "concepto"` |

## Cómo se fusionan

`legal_graphify.integrar_con_graphify("graphify-doctrinal/graph.json")` carga el grafo doctrinal de Graphify y le
agrega los nodos y enlaces jurídicos que faltan, marcándolos `_origin: "legal_graphify"`; los del
código quedan como `_origin: "ast"`. La comparación es por la terna `(origen, destino, relación)`,
así que la integración es **idempotente**: correrla dos, tres o diez veces no duplica nada
(verificado: la primera corrida agrega 967 nodos y 1.366 enlaces; las siguientes, 0 y 0).

El resultado se exporta a `graph.html` (vis.js) y abarca **el código del repositorio y el derecho
chileno en el mismo grafo**.

## Dos grafos de Graphify, dos carpetas (07-10-2026)

Hasta 1.13.1 `graphify-out/` hacía dos trabajos incompatibles: era el grafo que CLAUDE.md mandaba
consultar para preguntas de **código** y, a la vez, el grafo **doctrinal** cuyos visualizadores y
wiki publica `online_library_sync.py` en Hugging Face. Medido sobre el artefacto versionado:
21.521 nodos (68 % secciones de doctrina, 2.103 de código, sin `recursos.py`), 37 MB, y sus nodos
más conectados eran «Academia Judicial de Chile» (8.073 aristas) y «doctrina48981».

- `graphify-doctrinal/`: el grafo doctrinal, movido byte a byte (mismo blob en git, cero costo).
  Lo leen `online_library_sync.py` (tarjeta y Space de Hugging Face) y
  `scripts/enrich_legal_graphify_interconnections.py`. `graphify update` no lo toca.
- `graphify-out/`: el grafo del código, local. Con `.graphifyignore`, 3.740 nodos en ~9 s (4,5 MB),
  idéntico byte a byte entre dos clones; los nodos más conectados pasan a ser
  `LegalGraphifyEngine`, `handle_tool_call()`, `safe_urlopen()` y `BCNClient`. No se versiona porque
  cada cambio de código renumera comunidades: agregar una función reescribía ~16.000 líneas de
  `graph.json`.

Por qué no se regeneró en su lugar: con `.graphifyignore`, `graphify update .` sobre la carpeta vieja
se niega a escribir (el grafo «se achicaría» de 21.521 a 4.798 nodos) y con `--force` deja 1.113
nodos jurídicos sin archivo de origen que nunca se desalojan.

## Números medidos (18-09-2026)

- Grafo jurídico: **967 nodos / 1.366 aristas** — 105 instituciones, 572 artículos, 205 criterios de
  jurisprudencia, 57 obras y 13 vías procesales; cero nodos aislados.
- Fusión con el grafo de código: **1.716 nodos / 2.782 enlaces** (749 nodos del AST).
- Consultar una institución en vez de leer la obra completa ahorra **una mediana de 99,9 % de tokens** (ficha mediana de 91 tokens frente a la
  obra completa, cuya mediana es 96.536; medido sobre 9.863 instituciones; el detalle está en
  [`medicion_tokens.md`](medicion_tokens.md) y el script que lo reproduce en
  `scripts/medir_ahorro_tokens.py`).
- Las consultas son **deterministas**: la misma pregunta devuelve la misma ficha, bit a bit
  (verificado con varias semillas de hash dando el mismo SHA).

> **Si leíste una cifra de «85 % a 95 %» en este proyecto, era falsa.** El denominador del ahorro se
> calculaba con un piso de 1.200 tokens aplicado al tamaño de cada obra, y como 54 de las 58 obras
> están bajo ese piso, el 93 % de las instituciones declaraba un tamaño que no era el suyo. Se
> corrigió en la versión 1.5.3: ahora el número es el real del archivo y el rango publicado es el
> medido. Los tokens del subgrafo se estiman como `palabras × 1,3`, no con un tokenizador real: eso
> también está dicho en la nota metodológica.

## Por qué no mantenemos un fork

Un fork de Graphify tendría que reescribirse cada vez que el proyecto original cambia (va por 0.9.63
y publica sus versiones en PyPI como `graphifyy`), y este repositorio solo necesita **consumir** su
salida. Por eso: se instala la versión publicada, se ejecuta `graphify update .` (versión fijada en
`.claude/hooks/graphify-sesion.sh`) para regenerar `graphify-out/`, y el grafo jurídico se integra con `integrar_con_graphify()`. Si algún día hace
falta la estructura modular de Graphify dentro de este proyecto, se rehace aquí, con la API en
español y las pruebas de esta suite como red — no al revés.

## El gemelo `legal-graphify`: archivado, y nada de valor vive sólo allí

El repositorio `elpabloultron/legal-graphify` quedó **archivado el 18-09-2026** (público, 0
estrellas, 0 forks) y su README ya apunta acá. **No se toca**: todo se hace en open-legal-chile.

Paridad verificada función por función (27-09-2026):

| Pieza del gemelo | Dónde vive hoy en open-legal-chile |
|---|---|
| `core/engine.py`, `reasoning.py`, `centrality.py` | `legal_graphify.py`: `consultar_subgrafo()`, `encontrar_camino()`, `explicar_institucion()`, `analizar_impacto_normativo()`, `calcular_god_nodes()` |
| `mermaid.py` | `exportar_subgrafo_mermaid()` |
| extractores bcn / doc2md / doctrine | `bcn_connector`, `doc2md_ingestor`, `doctrina_connector` |
| `agents/doc2md_agent.py` | `agente-ingestor` |
| `cli.py` / `server.py` | `openlegal graph` + las 6 herramientas `graphify_*` del MCP |
| `benchmark_token_savings.py` | `scripts/medir_ahorro_tokens.py` + `docs/medicion_tokens.md` (99,9 % medido) |
| parser de artículos (lo único irrepetible) | rescatado como `extract_articulos_de_codigo()` / `ingerir_codigo_bcn()`, ya arreglado |

Su propio README admite que su `data/legal_knowledge_graph.json` era un artefacto de este proyecto
que no podía reconstruir: **947 nodos / 1.215 aristas** frente a los **14.050 / 31.017** de acá.
