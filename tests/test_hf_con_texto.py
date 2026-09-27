"""La búsqueda en Hugging Face tiene que traer texto del corpus, no solo la ruta del archivo.

Nace de un reclamo concreto: el harness consultaba el dataset y recibía una lista de rutas,
así que no podía citar nada ni mostrar el pasaje de la obra. El corpus en Hugging Face es el
primer paso de toda respuesta (AGENTS.md §2 quater): un primer paso sin texto no sirve.
"""

import online_library_sync as ols


def test_consultar_hf_devuelve_extracto_y_cita_con_texto(monkeypatch, tmp_path):
    monkeypatch.setattr(ols, "CACHE_HF", tmp_path)
    monkeypatch.setattr(ols, "_listar_archivos_hf", lambda repo_id: ["doctrina/civil/05-simulacion.md"])
    monkeypatch.setattr(
        ols, "_descargar_trozo_hf",
        lambda archivo, repo_id, tokens=None: "La simulación es un vicio del consentimiento. Art. 1451 CC.")

    res = ols.consultar_huggingface_dataset("simulacion", limit=2)

    assert res["resultados"], "debe haber al menos una coincidencia"
    primero = res["resultados"][0]
    assert primero.get("extractos"), "cada coincidencia debe traer extractos de texto"
    assert res.get("citas"), "el resultado debe traer un bloque de citas"
    assert res["citas"][0]["texto"].strip(), "la cita debe traer texto literal"
    assert res["citas"][0]["formato"] == "[Hugging Face - pablobenavidesj/doctrina-jurisprudencia-chile, Archivo: doctrina/civil/05-simulacion.md]"


def test_extractos_encuentran_aunque_no_se_escriban_los_acentos():
    """Quien consulta escribe «simulacion»; el corpus dice «simulación». Tienen que encontrarse."""
    texto = "x" * 50 + "La simulación es un vicio del consentimiento." + "y" * 50
    piezas = ols._extractos_hf(texto, ["simulacion"])
    assert piezas and "simulación" in piezas[0]
