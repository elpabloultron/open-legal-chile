"""Pruebas del pipeline de ingesta masiva y grounding de citas (scripts/ingestar_lote_masivo.py)."""

import pathlib

import pytest

from scripts.ingestar_lote_masivo import ingestar_directorio, procesar_lote


@pytest.fixture(autouse=True)
def _sin_regenerar_catalogos(monkeypatch):
    """Al cerrar un lote, procesar_lote regenera los catálogos del corpus real: sin esto cada
    corrida reescribía (y vaciaba) data/catalogo/*.jsonl versionados y dejaba ~170 MB de JSONL
    en data/."""
    monkeypatch.setattr("online_library_sync.OnlineLibrarySyncManager.generar_dataset_train_jsonl", lambda self: {})
    monkeypatch.setattr("scripts.optimizar_catalogo_hf.generar_lite", lambda: {})
    monkeypatch.setattr("scripts.optimizar_catalogo_hf.generar_indice_citas", lambda: {})


def test_ingestar_lote_masivo_dry_run(tmp_path):
    """Verifica que el modo dry-run simule el proceso sin escribir en disco."""
    doc1 = tmp_path / "test1.txt"
    doc1.write_text("La buena fe contractual es un principio general del derecho chileno. Art. 1546 Código Civil.", encoding="utf-8")
    doc2 = tmp_path / "test2.md"
    doc2.write_text("# Contrato de Arrendamiento\nEl arrendamiento es un contrato bilateral. Art. 1915 CC.", encoding="utf-8")

    res = ingestar_directorio(
        directorio=tmp_path,
        area="civil",
        tratadista="Doctrina de Prueba",
        dry_run=True,
        verbose=False,
    )

    assert res["total_archivos"] == 2
    assert res["exitosos"] == 2
    assert res["dry_run"] is True


def test_ingestar_lote_masivo_ejecucion(tmp_path, monkeypatch):
    """Verifica la ejecución de un lote procesando archivos temporales con flags de grafo desactivado."""
    monkeypatch.setattr("doctrina_connector.index_all_doctrina", lambda: 10)

    doc = tmp_path / "cesion_creditos.txt"
    doc.write_text(
        "De la cesión de derechos y créditos.\n"
        "La cesión de un crédito personal no produce efecto contra el deudor ni terceros sino por la notificación o aceptación.\n"
        "Norma: Art. 1901 del Código Civil.",
        encoding="utf-8",
    )

    res = procesar_lote(
        archivos=[doc],
        area="civil",
        tratadista="Tratadista Civil",
        obra="Tratado de los Contratos",
        materia="Cesión de Créditos",
        destino_dir=tmp_path,
        actualizar_grafo=False,
        actualizar_catalogo=False,  # no reescribir data/catalogo/ del repositorio
        dry_run=False,
        verbose=False,
    )

    assert res["total_archivos"] == 1
    assert res["exitosos"] == 1
    assert res["fallidos"] == 0
    assert res["tokens_originales"] > 0
    assert res["tokens_markdown"] > 0
    assert res["fts_actualizado"] is True


def test_ingestar_lote_masivo_sin_fts(tmp_path):
    """Verifica que procesar_lote respete el flag actualizar_fts=False."""
    doc = tmp_path / "prueba_sin_fts.txt"
    doc.write_text("Contrato de mandato judicial. Art. 7 CPC.", encoding="utf-8")

    res = procesar_lote(
        archivos=[doc],
        area="procesal",
        tratadista="Procesal",
        destino_dir=tmp_path,
        actualizar_grafo=False,
        actualizar_fts=False,
        actualizar_catalogo=False,
        dry_run=False,
        verbose=False,
    )

    assert res["exitosos"] == 1
    assert res["fts_actualizado"] is False
