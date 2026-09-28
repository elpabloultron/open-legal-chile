"""El grafo publicado se carga antes de reconstruir: el arranque en frío no puede costar minutos.

Medido el 2026-09-28: en un proceso nuevo, la primera consulta al grafo reconstruía el corpus
doctrinal completo (~62-70 s) teniendo el artefacto JSON publicado a mano (~0,3 s de carga).
Estas pruebas fijan el orden correcto: artefacto primero, reconstrucción como último recurso.
"""

import json

import networkx as nx

import legal_graphify
import mcp_server
from legal_graphify import LegalGraphifyEngine


def _grafo_de_prueba(destino):
    """Un grafo Node-Link mínimo con una institución consultable."""
    g = nx.DiGraph()
    g.add_node("inst_simulacion", label="Simulación", node_type="institucion")
    g.add_node("art_1545", label="Art. 1545", node_type="articulo_legal")
    g.add_edge("inst_simulacion", "art_1545", relation="cita_a")
    destino.write_text(json.dumps(nx.node_link_data(g), ensure_ascii=False), encoding="utf-8")
    return str(destino)


def test_consultar_subgrafo_carga_el_json_antes_de_reconstruir(monkeypatch, tmp_path):
    """Con el artefacto disponible, consultar no puede reconstruir desde doctrina."""
    ruta = _grafo_de_prueba(tmp_path / "grafo.json")
    monkeypatch.setattr(legal_graphify, "DEFAULT_GRAPH_PATH", ruta)
    engine = LegalGraphifyEngine(doctrina_dir=str(tmp_path / "sin_doctrina"))

    def _no_reconstruir(*_a, **_k):
        raise AssertionError("no debía reconstruir desde doctrina teniendo el JSON disponible")

    monkeypatch.setattr(engine, "construir_grafo_desde_doctrina", _no_reconstruir)

    resultado = engine.consultar_subgrafo("simulacion")

    assert engine.is_built is True
    assert resultado.get("encontrado") is True, resultado


def test_sin_artefacto_reconstruye_con_su_aviso(monkeypatch, tmp_path):
    """Sin artefacto, la reconstrucción clásica sigue viva — y avisa."""
    monkeypatch.setattr(legal_graphify, "DEFAULT_GRAPH_PATH", str(tmp_path / "no_existe.json"))
    engine = LegalGraphifyEngine(doctrina_dir=str(tmp_path / "sin_doctrina"))
    llamados = []
    original = engine.construir_grafo_desde_doctrina

    def _contar(*a, **k):
        llamados.append(True)
        return original(*a, **k)

    monkeypatch.setattr(engine, "construir_grafo_desde_doctrina", _contar)

    resultado = engine.consultar_subgrafo("simulacion")

    assert llamados, "sin artefacto debe reconstruir"
    assert any("No existe el grafo" in aviso for aviso in engine.advertencias)
    assert resultado.get("encontrado") is False


def test_precalentar_deja_el_grafo_cargado(monkeypatch):
    """precalentar_caches() carga el artefacto del server sin bloquear el arranque."""
    llamados = []
    monkeypatch.setattr(mcp_server.legal_graphify_engine, "cargar_grafo_json",
                        lambda *a, **k: llamados.append(True) or True)
    monkeypatch.setattr(mcp_server, "_precalentar_hf", lambda: None)

    mcp_server.precalentar_caches()

    assert llamados, "precalentar debe cargar el grafo publicado"


def test_precalentar_resiste_fallos(monkeypatch):
    """Si algo del precalentado falla (sin JSON, sin red), no puede tumbar el server."""
    def _romper(*_a, **_k):
        raise RuntimeError("sin artefacto")

    monkeypatch.setattr(mcp_server.legal_graphify_engine, "cargar_grafo_json", _romper)
    monkeypatch.setattr(mcp_server, "_precalentar_hf", _romper)

    assert mcp_server.precalentar_caches() is None
