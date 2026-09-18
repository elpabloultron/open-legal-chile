# Integración con Graphify: el grafo de código y el grafo jurídico

[Graphify](https://github.com/Graphify-Labs/graphify) es una herramienta **de terceros** que
construye un grafo de conocimiento de un repositorio (código y AST). Open Legal Chile **no la
incluye ni la forkea**: la consume. Esta página dice exactamente cómo se conectan y qué se midió,
para que nadie tenga que creer una cifra de folleto.

## Qué aporta cada uno

| | Graphify | Open Legal Chile |
|---|---|---|
| Qué grafica | el código del repositorio y sus dependencias (AST) | 58 tratados de doctrina chilena, normas BCN, criterios de la Corte Suprema, vías procesales y autores |
| Artefacto | `graphify-out/graph.json` (Node-Link) | `data/legal_knowledge_graph.json` (Node-Link) |
| Cómo se produce | `graphify update .` (solo AST, sin costo de API) | `LegalGraphifyEngine.construir_grafo_desde_doctrina()` (0,15 s sobre el corpus) |
| Cómo se consulta | CLI de Graphify | herramientas MCP `graphify_*` y `openlegal graph "concepto"` |

## Cómo se fusionan

`legal_graphify.integrar_con_graphify("graphify-out/graph.json")` carga el grafo de Graphify y le
agrega los nodos y enlaces jurídicos que faltan, marcándolos `_origin: "legal_graphify"`; los del
código quedan como `_origin: "ast"`. La comparación es por la terna `(origen, destino, relación)`,
así que la integración es **idempotente**: correrla dos, tres o diez veces no duplica nada
(verificado: la primera corrida agrega 967 nodos y 1.366 enlaces; las siguientes, 0 y 0).

El resultado se exporta a `graph.html` (vis.js) y abarca **el código del repositorio y el derecho
chileno en el mismo grafo**.

## Números medidos (18-09-2026)

- Grafo jurídico: **967 nodos / 1.366 aristas** — 105 instituciones, 572 artículos, 205 criterios de
  jurisprudencia, 57 obras y 13 vías procesales; cero nodos aislados.
- Fusión con el grafo de código: **1.716 nodos / 2.782 enlaces** (749 nodos del AST).
- Consultar una institución en vez de leer la obra completa ahorra **entre 31,9 % y 90,5 % de
  tokens, con mediana 74,1 %** (medido sobre las 105 instituciones; el detalle está en
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
salida. Por eso: se instala la versión publicada, se ejecuta `graphify update .` para regenerar
`graphify-out/`, y el grafo jurídico se integra con `integrar_con_graphify()`. Si algún día hace
falta la estructura modular de Graphify dentro de este proyecto, se rehace aquí, con la API en
español y las pruebas de esta suite como red — no al revés.
