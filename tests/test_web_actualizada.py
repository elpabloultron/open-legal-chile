"""Candado de la web y el README: que no vuelvan las cifras viejas ni el gemelo archivado."""
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PROHIBIDO_INDEX = ["75 Herramientas", "75 herramientas", "75 Tools", "248 documentos", "248 Documentos",
                   "227 tratados", "legal-graphify", "legal_graphify query", "Windsurf", "PaddleOCR"]
PROHIBIDO_README = ["75 Herramientas", "75 herramientas", "LegalGraphify: repositorio"]


def test_la_web_no_vuelve_a_las_cifras_viejas():
    texto = (RAIZ / "docs" / "index.html").read_text(encoding="utf-8")
    quedan = [p for p in PROHIBIDO_INDEX if p in texto]
    assert not quedan, f"docs/index.html todavía dice: {quedan}"


def test_el_readme_no_vuelve_a_las_cifras_viejas():
    texto = (RAIZ / "README.md").read_text(encoding="utf-8")
    quedan = [p for p in PROHIBIDO_README if p in texto]
    assert not quedan, f"README.md todavía dice: {quedan}"


def test_las_cifras_nuevas_estan_presentes():
    web = (RAIZ / "docs" / "index.html").read_text(encoding="utf-8")
    minuscula = web.lower()
    assert "86 herramientas mcp" in minuscula or "86 herramientas" in minuscula
    assert "228 obras" in web or "228 Obras" in web
    assert "openlegal instalar" in web


def test_la_pagina_del_grafo_existe_y_se_enlaza():
    web = (RAIZ / "docs" / "index.html").read_text(encoding="utf-8")
    assert (RAIZ / "docs" / "grafo.md").exists(), "falta docs/grafo.md"
    assert "docs/grafo.md" in web, "la web no enlaza la página del grafo"
    assert "openlegal graph" in web


def test_el_gemelo_queda_como_constancia_y_no_como_proyecto():
    """El repo archivado se nombra en la constancia (docs/), nunca como producto en la web."""
    constancia = (RAIZ / "docs" / "integracion_graphify.md").read_text(encoding="utf-8")
    assert "archivado" in constancia and "legal-graphify" in constancia
