"""Candado del saneador de URLs de la cosecha ambiental.

El HTML del sitio de los tribunales trae atributos malformados y `html.parser` deja
colas pegadas al href («"», «target=»); guardarlas convertía la sentencia en ficha.
"""
import importlib.util
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[1]


def _modulo():
    spec = importlib.util.spec_from_file_location(
        "harvest_amb", RAIZ / "scripts" / "harvest_all_tribunales_ambientales.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_quita_cola_de_atributo():
    mod = _modulo()
    sucia = ("https://tribunalambiental.cl/wp-content/uploads/2026/03/"
             "2025.12.22_Sentencia_D-45-2019.pdf target=")
    assert mod.limpiar_url_pdf(sucia).endswith("D-45-2019.pdf")


def test_quita_comilla_final():
    mod = _modulo()
    sucia = 'https://tribunalambiental.cl/wp-content/uploads/2021/03/Sentencia_R-296-2021.pdf"'
    assert mod.limpiar_url_pdf(sucia).endswith("R-296-2021.pdf")


def test_corrige_doble_f():
    mod = _modulo()
    sucia = "https://tribunalambiental.cl/wp-content/uploads/2016/05/Sentencia_C-5-2015.pdff"
    assert mod.limpiar_url_pdf(sucia).endswith("Sentencia_C-5-2015.pdf")


def test_url_limpia_no_se_toca():
    mod = _modulo()
    limpia = "https://tribunalambiental.cl/wp-content/uploads/2026/08/2026.08.25-Sentencia-R-574-2025.pdf"
    assert mod.limpiar_url_pdf(limpia) == limpia


def test_dominio_pelado_queda_sin_basura():
    mod = _modulo()
    assert mod.limpiar_url_pdf('"https://tribunalambiental.cl"') == "https://tribunalambiental.cl"
