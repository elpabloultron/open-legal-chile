"""Pruebas unitarias para el espacio de trabajo local de casos y LegalGraphify (case_workspace.py)."""

import json
import shutil
import tempfile
from pathlib import Path
import pytest

from case_workspace import CaseWorkspace, crear_o_cargar_caso, generar_id_caso, slugify


@pytest.fixture
def tmp_cases_dir(tmp_path):
    """Directorio temporal para aislar casos de prueba."""
    casos_dir = tmp_path / "casos_test"
    casos_dir.mkdir(parents=True, exist_ok=True)
    return casos_dir


def test_slugify():
    assert slugify("Despido injustificado y cobro de prestaciones") == "despido-injustificado-cobro-prestaciones"
    assert slugify("") == "caso-general"
    assert slugify("!!! ???") == "caso-general"


def test_generar_id_caso_con_rit_y_rol():
    # RIT Laboral
    id_rit = generar_id_caso("Demanda por despido injustificado causa RIT T-456-2024 ante Juzgado del Trabajo")
    assert id_rit == "rit-t-456-2024"

    # Rol Civil
    id_rol = generar_id_caso("Juicio ordinario de menor cuantía Rol C-1234-2025")
    assert id_rol == "rol-c-1234-2025"

    # Con lista de roles explícita
    id_exp = generar_id_caso("Consulta general", roles=["L-789-2023"])
    assert id_exp == "rit-l-789-2023"

    # Sin rol: fecha + slug
    id_sin_rol = generar_id_caso("Consulta sobre arrendamiento de predio urbano", materia="arrendamiento")
    assert "arrendamiento" in id_sin_rol


def test_creacion_estructura_workspace(tmp_cases_dir):
    ws_path = tmp_cases_dir / "caso_prueba"
    ws = CaseWorkspace(ws_path, id_caso="caso_prueba")

    assert ws.raw_dir.exists()
    assert ws.md_dir.exists()
    assert ws.grafo_dir.exists()
    assert ws.salidas_dir.exists()
    assert ws.id_caso == "caso_prueba"


def test_metadatos_workspace(tmp_cases_dir):
    ws = CaseWorkspace(tmp_cases_dir / "caso_meta", id_caso="caso_meta")
    ws.guardar_metadatos({"materia": "laboral", "cliente": "Juan Pérez"})

    meta = ws.leer_metadatos()
    assert meta["id_caso"] == "caso_meta"
    assert meta["materia"] == "laboral"
    assert meta["cliente"] == "Juan Pérez"
    assert "fecha_actualizacion" in meta


def test_agregar_documento_a_markdown_y_grafo(tmp_cases_dir, tmp_path):
    ws = CaseWorkspace(tmp_cases_dir / "caso_doc", id_caso="caso_doc")

    # Crear documento de prueba simulando escrito judicial
    doc_origen = tmp_path / "demanda.txt"
    doc_origen.write_text(
        "EN LO PRINCIPAL: Demanda de despido injustificado. PRIMER OTROSÍ: Acompaña documentos.\n"
        "DEMANDANTE: Juan Pérez, RUT 12.345.678-9\n"
        "DEMANDADO: Empresa SpA, RUT 76.123.456-7\n"
        "Se demandó por incumplimiento del Art. 161 del Código del Trabajo el 15-03-2024.\n"
        "Se solicita indemnización de $2.500.000 de pesos.",
        encoding="utf-8"
    )

    resultado = ws.agregar_documento(doc_origen)
    assert Path(resultado["documento_raw"]).exists()
    assert Path(resultado["documento_md"]).exists()

    # Verificar que el markdown contiene cabecera y normalización
    md_content = Path(resultado["documento_md"]).read_text(encoding="utf-8")
    assert "Documento: demanda.txt" in md_content
    assert "Código del Trabajo" in md_content

    # Verificar que el grafo se generó
    grafo_json = ws.grafo_dir / "grafo_caso.json"
    grafo_html = ws.grafo_dir / "grafo_caso.html"
    assert grafo_json.exists()
    assert grafo_html.exists()

    datos_grafo = json.loads(grafo_json.read_text(encoding="utf-8"))
    assert "nodes" in datos_grafo
    assert "edges" in datos_grafo
    assert any("Empresa SpA" in n["label"] or "Trabajo" in n["label"] for n in datos_grafo["nodes"])


def test_enriquecer_con_huggingface_mock(tmp_cases_dir, monkeypatch):
    ws = CaseWorkspace(tmp_cases_dir / "caso_hf", id_caso="caso_hf")

    def fake_consultar(termino, limit=4):
        return {
            "resultados": [
                {
                    "archivo": "doctrina/laboral/gamonal.md",
                    "cita_estandar": "[Hugging Face - pablobenavidesj/doctrina-jurisprudencia-chile, Archivo: doctrina/laboral/gamonal.md]",
                    "extractos": ["El despido por necesidades de la empresa requiere causa objetiva."],
                }
            ],
            "citas": [
                {
                    "formato": "[Hugging Face - pablobenavidesj/doctrina-jurisprudencia-chile, Archivo: doctrina/laboral/gamonal.md]",
                    "texto": "El despido por necesidades de la empresa requiere causa objetiva.",
                    "archivo": "doctrina/laboral/gamonal.md",
                }
            ],
        }

    import online_library_sync
    monkeypatch.setattr(online_library_sync, "consultar_huggingface_dataset", fake_consultar)

    res = ws.enriquecer_con_huggingface("despido injustificado")
    assert res["total_fuentes"] == 1
    assert (ws.md_dir / "fuentes_hf.md").exists()
    assert "[Hugging Face" in res["citas"][0]

    meta = ws.leer_metadatos()
    assert len(meta.get("fuentes_huggingface", [])) == 1


def test_crear_o_cargar_caso_integrado(tmp_cases_dir, monkeypatch):
    def fake_consultar(termino, limit=4):
        return {"resultados": [], "citas": []}

    import online_library_sync
    monkeypatch.setattr(online_library_sync, "consultar_huggingface_dataset", fake_consultar)

    ws = crear_o_cargar_caso(
        "Consulta sobre despido verbal en causa RIT T-999-2024",
        consulta="despido verbal indemnizaciones",
        metadatos={"materia": "laboral"},
        directorio_base=tmp_cases_dir
    )

    assert ws.id_caso == "rit-t-999-2024"
    assert ws.path.exists()
    resumen = ws.obtener_resumen()
    assert resumen["id_caso"] == "rit-t-999-2024"
    assert (ws.grafo_dir / "grafo_caso.json").exists()

