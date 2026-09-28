"""Candado del nombrado y la ficha de la biblioteca ambiental (libros, informes, foros, manuales)."""
from __future__ import annotations

import importlib.util
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[1]


def _modulo():
    spec = importlib.util.spec_from_file_location("bib", RAIZ / "scripts" / "biblioteca_ambiental_a_md.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_nombre_libro_de_concurso():
    mod = _modulo()
    assert mod.nombre_archivo({"tipo": "libro_concurso", "numero": "4"}) == "3ta_libro_concurso_4"


def test_nombre_informe():
    mod = _modulo()
    assert mod.nombre_archivo({"tipo": "informe", "numero": "03"}) == "2ta_informe_derecho_03"


def test_nombre_foro():
    mod = _modulo()
    assert mod.nombre_archivo({"tipo": "foro", "slug": "1"}) == "2ta_foro_1"
    assert mod.nombre_archivo({"tipo": "foro", "slug": "5_programa"}) == "2ta_foro_5_programa"


def test_nombre_manual_local():
    mod = _modulo()
    reg = {"tipo": "libro", "stem": "Manual_de_Derecho_Ambiental_Chileno"}
    assert mod.nombre_archivo(reg) == "libro_manual_de_derecho_ambiental_chileno"


def test_nombre_docencia_slugifica():
    mod = _modulo()
    reg = {"tipo": "docencia", "stem": "Módulo 2 - Ley N° 19.300.pdf"}
    assert mod.nombre_archivo(reg) == "docencia_modulo-2-ley-n-19-300"


def test_ficha_cita_huggingface():
    mod = _modulo()
    reg = {"tipo": "informe", "numero": "03", "titulo": "Informe en derecho — R-06-2013",
           "autor": "Rodrigo Silva Montes", "url_pdf": "https://tribunalambiental.cl/x.pdf"}
    texto = mod.ficha(reg, "2ta_informe_derecho_03.md")
    assert "[Hugging Face - biblioteca_ambiental/2ta_informe_derecho_03.md]" in texto
    assert "Rodrigo Silva Montes" in texto
