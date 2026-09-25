"""
Prueba de determinismo del motor del grafo.

La misma consulta debe dar la misma respuesta, siempre. No lo daba: `consultar_subgrafo()`
recorría un `set` de nodos vecinos y recortaba las listas con rebanadas (`normas[:6]`,
`jurisprudencia[:3]`, `relaciones_conceptuales[:5]`), así que el orden dependía de la semilla
de hash del proceso: dos corridas del MISMO proceso daban fichas con artículos distintos, el
tamaño variaba ±3 tokens y el ahorro publicado ±1 pp. En una herramienta cuyos números se
citan en un expediente, eso no es un detalle.

Se arregló ordenando las listas antes de recortarlas. Esta prueba fija el resultado con un
hash: si alguien vuelve a introducir un recorrido de set (o cambia el contenido del corpus),
falla y hay que volver a medir — que es exactamente lo que corresponde.
"""

import hashlib
import os

import pytest

from legal_graphify import LegalGraphifyEngine, DEFAULT_GRAPH_PATH

# Ficha de 'simulacion' con el corpus y el grafo actuales (967 nodos / 1366 aristas).
# Si cambia el corpus o el motor a propósito, este valor se actualiza A MANO y se deja dicho
# en el mensaje del commit: nunca se ajusta para que la prueba pase.
FICHA_ESPERADA_SHA = "ffa0fc1b7320f82e"  # pragma: allowlist secret
TOKENS_ESPERADOS = 299


@pytest.fixture(scope="module")
def engine():
    eng = LegalGraphifyEngine()
    if not (os.path.exists(DEFAULT_GRAPH_PATH) and eng.cargar_grafo_json(DEFAULT_GRAPH_PATH)):
        eng.construir_grafo_desde_doctrina()
    return eng


def test_la_misma_consulta_da_la_misma_ficha(engine):
    """Dos corridas consecutivas, en el mismo proceso, deben coincidir bit a bit."""
    primera = engine.consultar_subgrafo("simulacion")
    segunda = engine.consultar_subgrafo("simulacion")
    assert primera["subgrafo_resumen_yaml"] == segunda["subgrafo_resumen_yaml"]
    assert primera["metricas_tokens"] == segunda["metricas_tokens"]


def test_la_ficha_coincide_con_el_valor_de_referencia(engine):
    """
    Valor de referencia con hash. Detecta la no-determinación entre procesos que no se ve
    comparando dos llamadas dentro del mismo proceso (que comparten semilla de hash).
    """
    r = engine.consultar_subgrafo("simulacion")
    ficha = r["subgrafo_resumen_yaml"]
    obtenido = hashlib.sha256(ficha.encode("utf-8")).hexdigest()[:16]

    assert r["metricas_tokens"]["tokens_subgrafo"] == TOKENS_ESPERADOS, (
        "el tamaño de la ficha cambió: si fue a propósito, vuelve a medir y actualiza "
        "docs/medicion_tokens.md y el hash de esta prueba en el mismo commit"
    )
    assert obtenido == FICHA_ESPERADA_SHA, (
        f"la ficha de 'simulacion' cambió (sha {obtenido} != {FICHA_ESPERADA_SHA}). "
        "Si el cambio es intencional, actualiza el hash y vuelve a medir el ahorro; si no, "
        "alguien volvió a introducir un recorrido de set en la construcción de la ficha."
    )


def test_las_listas_de_la_ficha_salen_ordenadas(engine):
    """El orden no puede depender del azar del hashing: sale ordenado, y se nota en la ficha."""
    import json
    import re

    ficha = engine.consultar_subgrafo("simulacion")["subgrafo_resumen_yaml"]
    for clave in ("normas_positivas", "criterios_cs", "vinculos_subgrafo"):
        crudo = re.search(rf"{clave}: (\[.*?\])", ficha)
        if not crudo:
            continue
        valores = json.loads(crudo.group(1))
        assert valores == sorted(valores), f"'{clave}' no sale ordenada en la ficha: {valores}"


def test_el_analisis_de_impacto_tambien_es_estable(engine):
    """El blast radius recorta con [:15]: sin orden, la misma consulta cambiaba de integrantes."""
    a = engine.analizar_impacto_normativo("Art. 1546")
    b = engine.analizar_impacto_normativo("Art. 1546")
    assert [x["id"] for x in a["impacto_directo"]] == [x["id"] for x in b["impacto_directo"]]
    assert [x["id"] for x in a["impacto_cascada"]] == [x["id"] for x in b["impacto_cascada"]]
    assert a["metricas_impacto"] == b["metricas_impacto"]
