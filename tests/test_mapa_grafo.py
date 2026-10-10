"""Capa conectora del mapa (`mapa_corpus.grafo`): nodos, aristas, alias curados y comunidades.

Sobre archivos reales recortados del dataset, el índice CS de fixture y un grafo curado mínimo.
Las comunidades se comparan DENTRO del mismo proceso (otro orden de inserción, misma partición):
no se fijan hashes que dependan de la versión de NetworkX de cada entorno de la CI.
"""

import json
import random
from pathlib import Path

import pytest

from mapa_corpus import constructor, extractores, grafo, inventario, particiones
from pjud_connector import ruta_hf_corte_suprema

FX = Path(__file__).parent / "fixtures" / "mapa" / "delta"
CURADO = json.loads((FX / "curado.json").read_text(encoding="utf-8"))


def _filas():
    filas = []
    for ruta, nombre in [("jurisprudencia_tc/15907-06a-INA.md", "tc_15907-06a-INA.md"),
                         ("jurisprudencia_ambiental/1TA/D-25-2023.md", "ta_1TA_D-25-2023.md"),
                         ("doctrina/revistas/rehj/2015/rehj_791.md", "rev_rehj_2015_n37_791.md")]:
        datos = (FX / nombre).read_bytes()
        filas.append(extractores.extraer(ruta, datos, inventario.blob_git(datos)))
    for linea in (FX / "cs_sentencias_2anios.jsonl").read_text(encoding="utf-8").splitlines():
        registro = json.loads(linea)
        filas.append(extractores.fila_cs(registro, ruta_hf_corte_suprema(registro), "b" * 40, 1))
    filas.append(extractores.fila_cs({"rol": "777-2024", "era": 2024, "fecha": "2024-06-01",
                                      "sala": "TERCERA, CONSTITUCIONAL", "recurso": "(CIVIL) APELACIÓN PROTECCIÓN",
                                      "tribunal_origen": "C.A. de Valparaíso", "ministros": "MARIA GAJARDO HARBOE"},
                                     "jurisprudencia_cs/2024/06/777-2024.md", "c" * 40, 1))
    filas.append({"id": "doc:civil/obra", "col": "doc", "ruta": "doctrina/civil/obra.md", "blob": "d" * 40, "bytes": 1,
                  "titulo": "Obra", "cita_cs": ["cs:10641-2024", "cs:99999-2020"], "cita_tc": ["tc:13139"],
                  "normas": [["norma:cpr:19:n3", 2]]})
    return filas


def _capa(filas=None, curado=CURADO):
    filas = filas or _filas()
    ents = constructor.entidades(filas)
    capa = grafo.construir_capa(filas, ents, grafo.vias_de(curado))
    alias, puentes = grafo.alias_curados(curado, capa, filas)
    return capa, alias, puentes


def _rels(capa, rel):
    return sorted((s, t) for (s, t, r) in capa.aristas if r == rel)


def test_citas_de_rol_solo_hacia_entradas_existentes():
    capa, _, _ = _capa()
    citas = _rels(capa, "cita_rol")
    assert ("doc:civil/obra", "cs:10641-2024") in citas and ("doc:civil/obra", "tc:13139") in citas
    assert not any(t == "cs:99999-2020" for _, t in citas)       # rol que el dataset no tiene


def test_fallos_cs_no_son_nodos_salvo_que_alguien_los_cite():
    capa, _, _ = _capa()
    nodos_cs = sorted(n for n in capa.nodos if n.startswith("cs:"))
    assert nodos_cs == ["cs:10641-2024"]                         # el único citado
    # Lo que aportan las fichas CS va en aristas agregadas y ponderadas.
    assert ("ministro:maria-gajardo-harboe", "sala:cs-2") in _rels(capa, "integra_sala")
    assert ("sala:cs-2", "recurso:penal-queja") in _rels(capa, "conoce_recurso")
    assert ("tribunal:ca-santiago", "sala:cs-2") in _rels(capa, "eleva_a")
    pesos = {(s, t): w for (s, t, r), w in capa.aristas.items() if r == "integra_sala"}
    assert pesos[("ministro:maria-gajardo-harboe", "sala:cs-2")] >= 1


def test_recurso_equivale_a_la_via_procesal_curada():
    capa, _, _ = _capa()
    assert ("recurso:civil-apelacion-proteccion", "via_recurso_de_proteccion") in _rels(capa, "equivale_a")


def test_normas_cuelgan_de_su_articulo_y_su_cuerpo():
    assert grafo.padres_norma("norma:cpr:19:n3") == [("norma:cpr:19:n3", "norma:cpr:19"), ("norma:cpr:19", "norma:cpr")]
    assert grafo.padres_norma("norma:cc") == []
    capa, _, _ = _capa()
    partes = _rels(capa, "parte_de")
    assert ("norma:cpr:19:n3", "norma:cpr:19") in partes and ("norma:cpr:19", "norma:cpr") in partes
    assert ("tc:13139", "norma:cpr:93:n6") in _rels(capa, "cita_norma")


def test_alias_curados_y_puente_del_tc():
    _, alias, puentes = _capa()
    assert alias["organo_tc"] == "organo:tc" and alias["norma_ley_17997"] == "norma:ley-17997"
    # La ficha curada del TC está mal atribuida (cabecera de otra causa): no se fusiona, se tiende
    # un puente por el documento oficial (extended/13139) hacia la identidad real.
    assert "sent_tc_rol_n_15907_06a_ina" not in alias
    assert ("sent_tc_rol_n_15907_06a_ina", "tc:13139", "mismo_documento") in puentes


def test_comunidades_no_dependen_del_orden_de_insercion():
    filas = _filas()
    capa, alias, puentes = _capa(filas)
    a = grafo.comunidades(CURADO, capa, alias, puentes)
    revueltas = list(filas)
    random.Random(7).shuffle(revueltas)
    capa2, alias2, puentes2 = _capa(revueltas)
    b = grafo.comunidades(CURADO, capa2, alias2, puentes2)
    assert a == b
    assert all(n in a for n in capa.nodos)                       # 100 % de los nodos con comunidad


def test_exportar_es_determinista():
    def exportado():
        capa, alias, puentes = _capa()
        partes = grafo.exportar(capa, alias, puentes, grafo.comunidades(CURADO, capa, alias, puentes))
        return {k: particiones.serializar(v) for k, v in partes.items()}

    primero = exportado()
    assert primero == exportado()
    assert {"grafo/alias", "grafo/comunidades", "grafo/nodos-norma", "grafo/aristas-cita_norma"} <= set(primero)


def test_entidades_cuentan_por_coleccion():
    ents = constructor.entidades(_filas())
    normas = {e["id"]: e for e in ents["normas"]}
    assert normas["norma:cpr:19:n3"]["citas"] == {"doc": 2, "tc": 1}
    ministros = {e["id"]: e for e in ents["ministros"]}
    assert ministros["ministro:maria-gajardo-harboe"]["fallos_cs"] == 3   # 2 del índice + la 777-2024


@pytest.mark.parametrize("orden", [0, 1])
def test_resolver_colisiones_determinista(orden):
    filas = [{"id": "tc:1", "ruta": "jurisprudencia_tc/b.md", "col": "tc"},
             {"id": "tc:1", "ruta": "jurisprudencia_tc/a.md", "col": "tc"}]
    if orden:
        filas.reverse()
    resueltas, colisiones = constructor.resolver_colisiones(filas)
    assert colisiones == 1
    assert sorted((f["ruta"], f["id"]) for f in resueltas) == sorted(
        (f["ruta"], f["id"]) for f in constructor.resolver_colisiones(list(reversed(filas)))[0])
    assert len({f["id"] for f in resueltas}) == 2
