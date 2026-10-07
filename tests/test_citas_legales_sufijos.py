"""
El detector de citas tenía la misma falla que el parser de la BCN, un paso antes: cortaba el sufijo del
artículo y `cita_texto` entregaba OTRO artículo con su corchete oficial.

Medido el 2026-10-07 sobre la caché real:
  · «Código del Trabajo art. 183-AE» se leía «183-a» (entregaba el 183-A);
  · «Código del Trabajo art. 161-bis» se leía «161-b» (no existe: «no encontrado» por un guion);
  · «Código Penal art. 313 c» y «Código del Trabajo art. 183 A» se leían «313» y «183» (otro artículo);
  · «art. 25 Terminado» se leía «25 ter»;
  · «art. 1° transitorio» se leía «1» (el artículo 1 del articulado permanente).
"""

import pytest

from citas_legales import detectar_normas


def _art(texto):
    normas = detectar_normas(texto)
    assert len(normas) == 1, (texto, normas)
    return normas[0]["articulo"]


@pytest.mark.parametrize("texto, esperado", [
    ("Código del Trabajo art. 183-A", "183-a"),
    ("Código del Trabajo art. 183-AE", "183-ae"),
    ("Código del Trabajo art. 183 AE", "183 ae"),
    ("el artículo 183-AE del Código del Trabajo", "183-ae"),
    ("Código del Trabajo art. 161-bis", "161 bis"),
    ("Código del Trabajo art. 161 bis", "161 bis"),
    ("Código del Trabajo art. 152 quáter A", "152 quáter a"),
    ("Código del Trabajo art. 145-A", "145-a"),
    ("Ley 19.496 art. 16 B", "16 b"),
    ("Ley 19.496 art. 16 B de la ley", "16 b"),
    ("el artículo 16 B de la Ley 19.496", "16 b"),
    ("Código Penal art. 313 c", "313 c"),
    ("Código Penal art. 313° c.", "313 c"),
    ("Código Civil art. 3º bis", "3 bis"),
    ("Código del Trabajo art. 1° transitorio", "1 transitorio"),
    ("Constitución art. 4 Transitoria", "4 transitoria"),
])
def test_el_sufijo_del_articulo_se_lee_completo(texto, esperado):
    assert _art(texto) == esperado


@pytest.mark.parametrize("texto, esperado", [
    # Una letra o una palabra que sigue al número NO es sufijo si no cierra la mención.
    ("Ley 19.496 art. 12 A los efectos de esta ley", "12"),
    ("Código Civil art. 25 Terminado el plazo", "25"),
    ("Código Civil art. 1545 y 1546", "1545"),
    ("Código del Trabajo art. 5 N° 1", "5"),
    ("Código del Trabajo art. 161 inciso 1°", "161"),
    ("arts. 5 o 6 del Código Civil", "5"),
    ("Código Civil art. 3-De los plazos", "3"),
])
def test_lo_que_no_es_sufijo_no_se_agrega(texto, esperado):
    assert _art(texto) == esperado
