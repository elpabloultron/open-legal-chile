#!/usr/bin/env python3
"""
Mide el ahorro de tokens de LegalGraphify sobre todas las instituciones del grafo (~9.900).

Qué hace:
    1. Carga el grafo publicado (data/legal_knowledge_graph.json) con el motor real
       (`LegalGraphifyEngine`), no con una copia de la lógica.
    2. Consulta el subgrafo de cada institución con `consultar_subgrafo()` y lee las
       métricas que devuelve el propio motor (`metricas_tokens`).
    3. Reconstruye la tabla completa y la escribe en docs/medicion_tokens.md
       (+ docs/medicion_tokens.json para consumo programático).

Uso:
    .venv/bin/python scripts/medir_ahorro_tokens.py
    .venv/bin/python scripts/medir_ahorro_tokens.py --no-write    # solo imprime
    .venv/bin/python scripts/medir_ahorro_tokens.py --md otra/ruta.md --json otra/ruta.json

Por qué la tabla es reproducible:
    Cuando se escribió este script, `consultar_subgrafo()` recorría un `set` de nodos vecinos
    y recortaba las listas con rebanadas (`normas[:6]`, `jurisprudencia[:3]`,
    `relaciones_conceptuales[:5]`), así que el tamaño exacto de la ficha YAML dependía de la
    semilla de hash y variaba ±3 tokens entre procesos. Eso se arregló en el motor (las
    listas se ordenan antes de recortar) y se verificó con tres semillas distintas dando el
    mismo hash de ficha. Por eso este script ya NO re-ejecuta nada para fijar la semilla:
    la misma consulta debe dar la misma respuesta sin trucos.
"""

import os
import sys

import argparse
import json
import statistics  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from legal_graphify import LegalGraphifyEngine  # noqa: E402

DEFAULT_MD = os.path.join(BASE_DIR, "docs", "medicion_tokens.md")
DEFAULT_JSON = os.path.join(BASE_DIR, "docs", "medicion_tokens.json")


def medir() -> dict:
    """Corre el motor real sobre las 105 instituciones y devuelve las filas medidas."""
    engine = LegalGraphifyEngine()
    if not engine.cargar_grafo_json():
        raise SystemExit(
            "No se encontró el grafo en data/legal_knowledge_graph.json. "
            "Genéralo primero (el motor lo reconstruye desde doctrina/ si no existe)."
        )

    filas = []
    sin_resolver = []
    for nid, data in engine.graph.nodes(data=True):
        if data.get("node_type") != "institucion":
            continue
        label = data.get("label", nid)
        res = engine.consultar_subgrafo(label)
        if not res.get("encontrado") or res.get("nodo_id") != nid:
            sin_resolver.append((nid, label, res.get("nodo_id")))
            continue
        m = res["metricas_tokens"]
        filas.append(
            {
                "nodo_id": nid,
                "institucion": label,
                "area": data.get("area", ""),
                "obra": data.get("obra", ""),
                "tokens_texto_completo": m["tokens_texto_completo"],
                "tokens_subgrafo": m["tokens_subgrafo"],
                "tokens_ahorrados": m["tokens_ahorrados"],
                "porcentaje_ahorro": m["porcentaje_ahorro"],
                "factor_reduccion": m["factor_reduccion"],
            }
        )

    filas.sort(key=lambda f: (-f["porcentaje_ahorro"], f["institucion"]))

    pcts = [f["porcentaje_ahorro"] for f in filas]
    subs = [f["tokens_subgrafo"] for f in filas]
    fulls = [f["tokens_texto_completo"] for f in filas]

    stats = {
        "n_instituciones": len(filas),
        "ahorro_minimo": min(pcts),
        "ahorro_mediano": round(statistics.median(pcts), 1),
        "ahorro_maximo": max(pcts),
        "ahorro_medio": round(statistics.mean(pcts), 1),
        "instituciones_sobre_85": sum(1 for p in pcts if p >= 85),
        "instituciones_sobre_80": sum(1 for p in pcts if p >= 80),
        "instituciones_bajo_70": sum(1 for p in pcts if p < 70),
        "subgrafo_tokens_min": min(subs),
        "subgrafo_tokens_mediana": int(statistics.median(subs)),
        "subgrafo_tokens_max": max(subs),
        "texto_completo_tokens_min": min(fulls),
        "texto_completo_tokens_mediana": int(statistics.median(fulls)),
        "texto_completo_tokens_max": max(fulls),
        "nodos_grafo": engine.graph.number_of_nodes(),
        "aristas_grafo": engine.graph.number_of_edges(),
        "advertencias_motor": list(engine.advertencias),
        "instituciones_sin_resolver": sin_resolver,
    }
    return {"filas": filas, "stats": stats}


def construir_markdown(medicion: dict) -> str:
    filas, s = medicion["filas"], medicion["stats"]
    generado = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def num(v):
        """Formatea con coma decimal, como el resto de la documentación."""
        return f"{v}".replace(".", ",")

    lineas = [
        "# Medición del ahorro de tokens de LegalGraphify",
        "",
        f"*Generado por `scripts/medir_ahorro_tokens.py` el {generado} "
        "(PYTHONHASHSEED=0).*",
        "",
        "## Método",
        "",
        "**Qué se mide.** Para cada una de las instituciones del grafo se comparan dos números:",
        "",
        "- **Texto completo (tokens):** el tamaño del archivo doctrinal completo de la obra que",
        "  contiene a la institución, es decir `max(1, palabras_del_archivo * 1.3)`. Es el baseline",
        "  que el motor registra en `tokens_archivo`: lo que costaría inyectar el documento entero",
        "  en el prompt en lugar del subgrafo.",
        "- **Subgrafo (tokens):** el tamaño de la ficha YAML hiper-densa que el motor realmente",
        "  devuelve al consultar esa institución (`consultar_subgrafo()`), medida igual:",
        "  `palabras_de_la_ficha * 1.3`.",
        "- **Ahorro (%):** `(texto_completo - subgrafo) / texto_completo * 100`.",
        "",
        "Ambos números los calcula el motor (`legal_graphify.py`, campo `metricas_tokens`);",
        "este script solo los recorre y los tabula. El grafo medido tiene "
        f"{s['nodos_grafo']} nodos y {s['aristas_grafo']} aristas.",
        "",
        "**Qué NO se mide.**",
        "",
        "- **No hay tokenizador real.** El factor `palabras * 1.3` es una estimación (del orden",
        "  del BPE de GPT/Llama para texto español), no el conteo de un tokenizador concreto.",
        "  Otro tokenizador daría cifras distintas en ambos lados de la comparación.",
        "- **No se mide lo que costaría un RAG convencional** ni la lectura de manuales enteros",
        "  por otro mecanismo: se compara subgrafo contra el archivo doctrinal fuente, que es el",
        "  baseline que el motor registra en `tokens_archivo`.",
        "- **No se mide calidad, precisión ni alucinación.** Es una medición de tamaño de texto,",
        "  no de utilidad de la respuesta.",
        "- **No es el ahorro de todo el pipeline.** El corpus crudo → Markdown de alta densidad",
        "  (`scripts/doctrina_parser.py`, `doc2md_ingestor.py`) es otra métrica y no se mide aquí.",
        "",
        "**Nota de reproducibilidad.** El tamaño exacto de la ficha depende del orden de iteración",
        "de un `set` dentro de `legal_graphify.py`, que varía con la semilla de hash de Python;",
        "por eso el script se re-ejecuta con `PYTHONHASHSEED=0`. Entre semillas la diferencia es de",
        "unos pocos tokens por institución y no cambia el rango publicado.",
        "",
        "## Resultado global",
        "",
        f"- **Instituciones medidas:** {s['n_instituciones']}",
        f"- **Ahorro por institución:** mínimo {num(s['ahorro_minimo'])} %, "
        f"mediana {num(s['ahorro_mediano'])} %, máximo {num(s['ahorro_maximo'])} % "
        f"(media {num(s['ahorro_medio'])} %)",
        f"- **Subgrafos devueltos:** entre {s['subgrafo_tokens_min']} y "
        f"{s['subgrafo_tokens_max']} tokens (mediana {s['subgrafo_tokens_mediana']})",
        f"- **Textos completos de las obras:** entre {s['texto_completo_tokens_min']} y "
        f"{s['texto_completo_tokens_max']} tokens "
        f"(mediana {s['texto_completo_tokens_mediana']})",
        f"- **Instituciones con ahorro ≥ 85 %:** {s['instituciones_sobre_85']} "
        f"de {s['n_instituciones']}",
        f"- **Instituciones con ahorro ≥ 80 %:** {s['instituciones_sobre_80']} "
        f"de {s['n_instituciones']}",
        f"- **Instituciones con ahorro < 70 %:** {s['instituciones_bajo_70']} "
        f"de {s['n_instituciones']}",
        "",
        "## Tabla completa (105 instituciones)",
        "",
        "| # | Institución | Área | Texto completo (tokens) | Subgrafo (tokens) | Ahorro | Factor |",
        "|---:|---|---|---:|---:|---:|---:|",
    ]

    for i, f in enumerate(filas, 1):
        inst = f["institucion"].replace("|", "\\|")
        area = (f["area"] or "").replace("|", "\\|")
        lineas.append(
            f"| {i} | {inst} | {area} | {f['tokens_texto_completo']} | "
            f"{f['tokens_subgrafo']} | {num(f['porcentaje_ahorro'])} % | "
            f"{num(f['factor_reduccion'])} |"
        )

    if s["instituciones_sin_resolver"]:
        lineas += ["", "## Avisos", ""]
        lineas.append(
            f"- {len(s['instituciones_sin_resolver'])} instituciones no resolvieron "
            "al nodo esperado:"
        )
        for nid, label, got in s["instituciones_sin_resolver"]:
            lineas.append(f"  - `{nid}` ({label}) → `{got}`")

    lineas += [
        "",
        "---",
        "",
        "Regenerar esta tabla:",
        "",
        "```bash",
        ".venv/bin/python scripts/medir_ahorro_tokens.py",
        "```",
        "",
    ]
    return "\n".join(lineas)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Reconstruye la tabla de ahorro de tokens de LegalGraphify."
    )
    ap.add_argument("--md", default=DEFAULT_MD, help="ruta del Markdown de salida")
    ap.add_argument("--json", default=DEFAULT_JSON, help="ruta del JSON de salida")
    ap.add_argument(
        "--no-write", action="store_true", help="solo imprime, no escribe archivos"
    )
    args = ap.parse_args()

    medicion = medir()
    filas, s = medicion["filas"], medicion["stats"]

    print(
        f"Instituciones medidas: {s['n_instituciones']}  |  "
        f"grafo: {s['nodos_grafo']} nodos / {s['aristas_grafo']} aristas"
    )
    print(
        f"Ahorro: mínimo {s['ahorro_minimo']} %  |  mediana {s['ahorro_mediano']} %  |  "
        f"máximo {s['ahorro_maximo']} %  (media {s['ahorro_medio']} %)"
    )
    print(
        f"Subgrafos: {s['subgrafo_tokens_min']}-{s['subgrafo_tokens_max']} tokens "
        f"(mediana {s['subgrafo_tokens_mediana']})  |  "
        f"Textos completos: {s['texto_completo_tokens_min']}-"
        f"{s['texto_completo_tokens_max']} tokens"
    )
    print(
        f"≥85 %: {s['instituciones_sobre_85']}  |  ≥80 %: {s['instituciones_sobre_80']}  |  "
        f"<70 %: {s['instituciones_bajo_70']}"
    )
    for adv in s["advertencias_motor"]:
        print(f"AVISO del motor: {adv}", file=sys.stderr)
    if s["instituciones_sin_resolver"]:
        print(
            f"AVISO: {len(s['instituciones_sin_resolver'])} instituciones no resolvieron",
            file=sys.stderr,
        )

    print()
    print(f"{'#':>3}  {'Ahorro':>7}  {'Texto':>6}  {'Subgrafo':>8}  Institución")
    print("-" * 100)
    for i, f in enumerate(filas, 1):
        print(
            f"{i:>3}  {f['porcentaje_ahorro']:>6}%  {f['tokens_texto_completo']:>6}  "
            f"{f['tokens_subgrafo']:>8}  {f['institucion']}"
        )

    if not args.no_write:
        md = construir_markdown(medicion)
        for path, content in ((args.md, md),):
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
            print(f"\nEscrito: {path}")
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(medicion, fh, ensure_ascii=False, indent=2)
        print(f"Escrito: {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
