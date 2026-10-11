"""Fichas del TC en el grafo curado: `--rehacer-tc` quita las armadas con documentos de otra causa
y las rearma desde los .md corregidos (rol oficial, gestión verificada y enlace por número de rol).
Sin red: grafo, índice y .md de prueba en una carpeta temporal."""

import json
import os
import sys

import pytest

from scripts import integrar_jurisprudencia_al_grafo as integrar

MD = """# INA-STC — Rol N° 15686-06a-INA

- **Tribunal:** Tribunal Constitucional de Chile
- **Rol:** Rol N° 15686-06a-INA
- **Rol oficial:** Rol N° 15686-24-INA
- **Fecha:** 2025-06-12
- **Gestión pendiente / carátula:** Causa Rol C-1-2024 del Juzgado de Letras de Arica
- **Documento oficial:** https://buscador-backend.tcchile.cl/api/extended/15686/download

---

Sentencia Rol 15.686-24 INA [12 de junio de 2025]. VISTOS: … se impugna el artículo 1545 del Código Civil …
conforme al artículo 84 de la Ley N° 17.997, Orgánica Constitucional del Tribunal Constitucional …
Rol N° 15.686-24-INA.
"""


@pytest.fixture
def base(tmp_path, monkeypatch):
    (tmp_path / "scripts").mkdir()
    real = os.path.join(os.path.dirname(integrar.__file__), "optimizar_catalogo_hf.py")
    (tmp_path / "scripts" / "optimizar_catalogo_hf.py").write_text(open(real, encoding="utf-8").read(), encoding="utf-8")
    (tmp_path / "jurisprudencia_tc").mkdir()
    (tmp_path / "jurisprudencia_tc" / "15686-06a-INA.md").write_text(MD, encoding="utf-8")
    datos = tmp_path / "data" / "jurisprudencia"
    datos.mkdir(parents=True)
    (datos / "tc_textos.jsonl").write_text(json.dumps({
        "rol": "Rol N° 15686-06a-INA", "fecha": "2025-06-12", "tipo": "INA-STC",
        "archivo_md": "jurisprudencia_tc/15686-06a-INA.md", "tokens_aprox": 50,
        "link_pdf": "https://buscador-backend.tcchile.cl/api/extended/15686/download"}, ensure_ascii=False) + "\n",
        encoding="utf-8")
    grafo = {"graph": {}, "nodes": [
        {"id": "organo_tc", "label": "Tribunal Constitucional de Chile", "node_type": "organo_estado"},
        {"id": "norma_codigo_civil_art_1545", "label": "Código Civil, Art. 1545", "node_type": "articulo_legal"},
        {"id": "norma_cpr_19_8", "label": "CPR Art. 19 N° 8", "node_type": "articulo_legal"},
        # Un artículo cuya etiqueta lleva el nombre de la ley antes del número de artículo.
        {"id": "norma_ley_n_17_997_organica_constitucional_del_tribunal_constitucional_art_79",
         "label": "Ley N° 17.997 Orgánica Constitucional del Tribunal Constitucional, Art. 79",
         "node_type": "articulo_legal"},
        # Ficha vieja: cabecera de 15686, texto y enlace de otra causa (extended/13336).
        {"id": "sent_tc_rol_n_15686_06a_ina", "label": "TC · Rol N° 15686-06a-INA — INA-STC",
         "node_type": "jurisprudencia_tc", "rol": "Rol N° 15686-06a-INA",
         "url": "https://buscador-backend.tcchile.cl/api/extended/13336/download"},
        {"id": "sent_tc_rol_n_99999_06a_ina", "label": "TC · Rol N° 99999-06a-INA", "node_type": "jurisprudencia_tc"},
    ], "edges": [
        {"source": "sent_tc_rol_n_15686_06a_ina", "target": "norma_cpr_19_8", "relation": "cita_norma", "weight": 1.0},
        {"source": "sent_tc_rol_n_99999_06a_ina", "target": "organo_tc", "relation": "dictada_por", "weight": 1.0},
    ]}
    (datos / "legal_knowledge_graph.json").write_text(json.dumps(grafo, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(integrar, "BASE", tmp_path)
    monkeypatch.setattr(integrar, "GRAFO", datos / "legal_knowledge_graph.json")
    monkeypatch.setattr(integrar, "TC_INDICE", datos / "tc_textos.jsonl")
    monkeypatch.setattr(integrar, "PUB_INDICE", datos / "no_hay.jsonl")
    monkeypatch.setattr(integrar, "BIB_INDICE", datos / "no_hay.jsonl")
    monkeypatch.setattr(integrar, "TC_CURADAS", datos / "no_hay.jsonl")
    return datos


def _correr(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["integrar", "--sin-comunidades", *args])
    assert integrar.main() == 0


def test_rehacer_tc_quita_lo_armado_con_otra_causa_y_lo_rearma_con_el_documento_correcto(base, monkeypatch):
    _correr(monkeypatch, "--rehacer-tc")
    g = json.loads((base / "legal_knowledge_graph.json").read_text(encoding="utf-8"))
    tc = {n["id"]: n for n in g["nodes"] if n.get("node_type") == "jurisprudencia_tc"}
    assert set(tc) == {"sent_tc_rol_n_15686_06a_ina"}                  # la ficha sin .md se retira
    nodo = tc["sent_tc_rol_n_15686_06a_ina"]
    assert nodo["url"].endswith("/extended/15686/download") and nodo["rol_oficial"] == "Rol N° 15686-24-INA"
    assert nodo["gestion"].startswith("Causa Rol C-1-2024") and nodo["label"].startswith("TC · Rol N° 15686-24-INA")
    aristas = {(a["source"], a["target"], a["relation"]) for a in g["edges"]}
    assert ("sent_tc_rol_n_15686_06a_ina", "norma_cpr_19_8", "cita_norma") not in aristas    # la de otra causa
    assert ("sent_tc_rol_n_15686_06a_ina", "norma_codigo_civil_art_1545", "cita_norma") in aristas
    assert ("sent_tc_rol_n_15686_06a_ina", "organo_tc", "resuelto_por") in aristas
    assert not any("99999" in a["source"] for a in g["edges"])
    # Cita el art. 84 de la LOC del TC: no se le atribuye el art. 79, que es otro artículo.
    assert not any(t.endswith("_art_79") for (s, t, r) in aristas if s == "sent_tc_rol_n_15686_06a_ina")


def test_sin_rehacer_no_se_toca_lo_que_ya_estaba(base, monkeypatch):
    antes = json.loads((base / "legal_knowledge_graph.json").read_text(encoding="utf-8"))
    _correr(monkeypatch)
    g = json.loads((base / "legal_knowledge_graph.json").read_text(encoding="utf-8"))
    viejo = next(n for n in g["nodes"] if n["id"] == "sent_tc_rol_n_15686_06a_ina")
    assert viejo == next(n for n in antes["nodes"] if n["id"] == "sent_tc_rol_n_15686_06a_ina")
