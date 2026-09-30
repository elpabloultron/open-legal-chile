"""Pruebas del catálogo rápido en memoria y grounding de citas de Hugging Face.

Verifica que las consultas sobre el dataset de Hugging Face alcancen tanto
las 11.858 instituciones canónicas de doctrina como la jurisprudencia judicial cosechada,
devolviendo extractos literales verificables y citas oficiales en formato de corchetes.
"""

import online_library_sync as ols


def test_busqueda_instituciones_canonica():
    """Búsqueda de conceptos sustantivos devuelve doctrina con extractos y citas oficiales."""
    res = ols.consultar_huggingface_dataset("responsabilidad extracontractual culpa", limit=3)
    assert not res.get("error"), f"Error en búsqueda: {res.get('error')}"
    assert len(res["resultados"]) >= 1, "Debe encontrar al menos una coincidencia en el catálogo"
    assert res.get("citas"), "Debe devolver bloque de citas"

    primera_cita = res["citas"][0]
    assert "Hugging Face" in primera_cita["formato"]
    assert "Archivo:" in primera_cita["formato"]
    assert primera_cita["texto"].strip(), "La cita debe incluir texto literal"
    assert primera_cita["fuente"] == "huggingface"


def test_busqueda_jurisprudencia_por_rol():
    """Búsqueda de un Rol específico devuelve la ficha de jurisprudencia judicial."""
    res = ols.consultar_huggingface_dataset("45.123-2021", limit=3)
    assert not res.get("error")
    assert res["resultados"], "Debe encontrar resultados para un Rol válido"

    primero = res["resultados"][0]
    assert primero["tipo"] == "jurisprudencia_cs"
    assert "45.123-2021" in primero["archivo"]
    assert res["citas"][0]["formato"].startswith("[Hugging Face - ")


def test_invalidacion_cache_catalogo():
    """Prueba que invalidar_cache_catalogo() limpie la caché en memoria."""
    # Asegurar que esté cargado
    items, indice = ols._obtener_catalogo_instituciones()
    assert items and indice
    assert ols._CATALOGO_INSTITUCIONES is not None

    ols.invalidar_cache_catalogo()
    assert ols._CATALOGO_INSTITUCIONES is None
    assert ols._INDICE_INSTITUCIONES is None


def test_descargar_trozo_hf_local():
    """Verifica que un archivo local se lea directamente sin depender del Hub remoto."""
    archivo_local = "doctrina/laboral/gamonal_derecho_del_trabajo/02_contrato_individual_y_despido.md"
    texto = ols._descargar_trozo_hf(archivo_local, "pablobenavidesj/doctrina-jurisprudencia-chile")
    assert "Sergio Gamonal Contreras" in texto
    assert "DESPIDO" in texto
