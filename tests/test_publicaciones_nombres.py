"""Candado del nombrado de las publicaciones ambientales.

El registro traía como «2014» el anuario que en realidad era de 2016 (la carpeta de subida
se usaba como año) y los dos tomos de 2018 colisionaban en un solo archivo. El año sale
ahora del nombre del PDF y los tomos llevan sufijo propio.
"""
import importlib.util
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[1]


def _modulo():
    spec = importlib.util.spec_from_file_location(
        "publicaciones_a_md", RAIZ / "scripts" / "publicaciones_a_md.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_anio_sale_del_nombre_no_de_la_carpeta():
    mod = _modulo()
    # el Anuario 2015 vive en la carpeta 2014/09 del sitio
    url = "https://tribunalambiental.cl/wp-content/uploads/2014/09/Anuario-2015-del-Tribunal-Ambiental-de-Santiago-1.pdf"
    assert mod.anio_de_url(url) == "2015"


def test_anio_usa_la_ultima_mencion_del_nombre():
    mod = _modulo()
    url = "https://tribunalambiental.cl/wp-content/uploads/2019/06/Anuario-2018_Tomo-I_Tribunal-Ambiental-Santiago.pdf"
    assert mod.anio_de_url(url) == "2018"


def test_anio_respaldo_cuando_no_hay_numero():
    mod = _modulo()
    assert mod.anio_de_url("https://x.cl/wp-content/uploads/2014/08/Anuario-web.pdf", "2013") == "2013"


def test_los_tomos_no_colisionan():
    mod = _modulo()
    base = {"tribunal": "2TA", "tipo": "Anuario de Jurisprudencia Ambiental", "anio": "2018"}
    assert mod.nombre_archivo({**base, "tomo": "1"}) == "2ta_anuario_2018_tomo1"
    assert mod.nombre_archivo({**base, "tomo": "2"}) == "2ta_anuario_2018_tomo2"
    assert mod.nombre_archivo(base) == "2ta_anuario_2018"


def test_boletines_sin_cambios():
    mod = _modulo()
    reg = {"tribunal": "3TA", "tipo": "Boletín de Jurisprudencia Ambiental", "numero": "n45"}
    assert mod.nombre_archivo(reg) == "3ta_boletin_n45"
