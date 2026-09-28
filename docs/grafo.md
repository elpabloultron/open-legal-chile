# El grafo jurídico: cómo se construye y cómo se consulta

El motor vive **dentro** de la suite (`legal_graphify.py`). No es un proyecto aparte ni un servicio
externo: es una biblioteca del paquete, con sus herramientas MCP y su comando de consola
(`openlegal graph "…"`).

## El recorrido (Hugging Face → Markdown → grafo → lenguaje natural)

1. **Corpus en Markdown** — 228 obras de doctrina + 24 guías de la Academia Judicial + 967
   sentencias del TC, 886 ambientales y 55 publicaciones; las 70.523 fichas de la Corte Suprema y
   los índices viven en Hugging Face y se leen desde ahí.
2. **Ingesta** — `LegalGraphifyEngine.construir_grafo_desde_doctrina()` lee el corpus y extrae
   instituciones, normas (`norm_label`), obras, autores y vías procesales;
   `scripts/integrar_jurisprudencia_al_grafo.py` suma la jurisprudencia al mismo grafo.
3. **Comunidades y jerarquía** — Louvain sobre las aristas → **52 comunidades** (modularidad
   **0,641**) y PageRank → «god nodes»: pilares dogmáticos y normas centrales.
4. **Consulta en lenguaje natural** — el harness pide un subgrafo o una explicación y recibe una
   ficha hiper-densa con citas verificables, en vez de leer la obra completa.

## Taxonomía: área → institución → materia

- **Área** — 19 medidas; 10.229 nodos la traen (Civil, Penal, Procesal, Administrativo, Laboral,
  Familia, Constitucional…).
- **Institución** — «simulación», «objeto ilícito», «compensación económica»…: cada nodo trae
  definición, normas BCN y criterios de jurisprudencia.
- **Materia / comunidad** — agrupación densa del grafo (27), útil para «¿qué va con qué?».
- La jurisprudencia (TC, CS, ambiental) se ancla a la misma taxonomía por `area`/`materia`.

## Los tres grafos

| Grafo | Qué es | Dónde |
|---|---|---|
| **Jurídico** | doctrina + normas + jurisprudencia + vías procesales (13.938 nodos · 30.746 aristas) | `data/legal_knowledge_graph.json` |
| **De las guías AJ** | las guías de la Academia Judicial y sus normas (autor · obra · norma) | `data/grafo_guias_aj.json` |
| **Del caso** | se arma con los documentos de la carpeta del caso (escritos, PDFs, notas) | `generar_grafo_vinculos` + `grafo_ver_caso` |

## Cómo se consulta

```bash
openlegal graph "compensacion economica"                 # subgrafo + ahorro medido
openlegal graph path "simulacion" "inoponibilidad"       # caminos multi-salto
openlegal graph explain "objeto_ilicito"                 # explicación dogmática 360°
openlegal graph affected "Art. 1464 CC"                  # impacto normativo en cascada
openlegal graph god-nodes 10                             # pilares por PageRank
```

Y desde cualquier harness, por MCP: `graphify_consulta_subgrafo`, `graphify_trazar_camino`,
`graphify_explicar_institucion`, `graphify_analizar_impacto`, `graphify_god_nodes`,
`graphify_resumen_comunidades` — más `grafo_ver_corpus`, `grafo_ver_caso` y `generar_grafo_vinculos`.

## El ahorro y su medición

Mediana de **99,9 %** de reducción de tokens sobre 9.863 consultas (ficha mediana de 91 tokens
frente a una obra mediana de 96.536). El método, y la historia de la cifra falsa que se corrigió en
1.5.3, están en [`medicion_tokens.md`](medicion_tokens.md); el script que lo reproduce es
`scripts/medir_ahorro_tokens.py`. Visualizador interactivo:
[Space del grafo](https://huggingface.co/spaces/pablobenavidesj/open-legal-chile-graph).
