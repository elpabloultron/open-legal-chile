# Benchmarks de Open Legal Chile

Medido el 2026-09-28 19:48 en `Linux-7.2.8-1-cachyos-x86_64-with-glibc2.44` · Python 3.13.15.

> Estos números son una **serie**, no umbrales: la gracia es compararlos entre corridas.
> `.venv/bin/python scripts/bench_rendimiento.py --comparar` imprime los deltas.

| Medición | Segundos | Detalle |
|---|---:|---|
| import mcp_server | 0.42 | arranque en proceso nuevo: 295 ms (decisión 2026-09-28: sin arranque perezoso, YAGNI) |
| grafo (carga + subgrafo) | 0.39 | 14,050 nodos · subgrafo ok |
| subgrafo en frío (proceso nuevo) | 0.44 | 1ª consulta en proceso nuevo: 0.28 s (antes del arreglo: 62-70 s) · encontrado=True |
| fts trigram (200k líneas) | 1.52 | 200k líneas · indexado 1.18 s · consulta 1 ms (1 resultado) |
| consulta ambiental (fría/caliente) | 4.19 | 1ª 4.10 s (fría) · 2ª 0.09 s (caliente) · 5 y 5 resultados |
| consulta_maestra (armado) | 0.18 | armado sin red · faltantes: ['huggingface', 'doctrina', 'normas'] |

Notas: la carga del grafo (~0,4 s) desmintió la cifra falsa de «~72 s» que había quedado
de una corrida con la CPU saturada por OCR; el arranque del MCP (~0,40 s) cerró el ítem del
arranque perezoso como no-acción (YAGNI). El 2026-09-28 (noche) la 1ª consulta al grafo en
frío pasó de 62-70 s a ~1 s: el subgrafo carga primero el artefacto publicado y el server lo
precalienta en segundo plano al arrancar.
