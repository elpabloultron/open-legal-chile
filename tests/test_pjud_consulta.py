"""La consulta de causas por Rol/RIT: lo que se puede hacer y lo que se dice que no.

Esta herramienta existe porque la Oficina Judicial Virtual —el único lugar donde vive el estado de
una causa— pide ClaveÚnica y captcha. La suite no automatiza eso. Lo que sí hace es validar el RIT,
decir a qué jurisdicción apunta y dejar la consulta armada con sus pasos. Y lo dice de frente: no
devuelve el estado de la causa porque no lo tiene.
"""

from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import pjud_connector as pjud  # noqa: E402


class TestAnalizarRit(unittest.TestCase):
    def test_las_letras_conocidas(self):
        casos = {
            "C-1234-2026": "civil",
            "T-1234-2026": "laboral",
            "L-1234-2026": "laboral",
            "F-1234-2026": "familia",
            "P-1234-2026": "penal",
        }
        desajustes = []
        for rit, jurisdiccion in casos.items():
            analisis = pjud.analizar_rit(rit)
            if not analisis["valido"]:
                desajustes.append(f"{rit}: no lo dio por valido")
            elif analisis["jurisdiccion"] != jurisdiccion:
                desajustes.append(f"{rit}: esperaba {jurisdiccion}, dio {analisis['jurisdiccion']}")
            elif analisis["anio"] != 2026:
                desajustes.append(f"{rit}: año {analisis['anio']}")
        self.assertFalse(desajustes, "; ".join(desajustes))

    def test_un_rol_sin_letra_no_afirma_jurisdiccion(self):
        analisis = pjud.analizar_rit("Rol 45123-2021")
        self.assertTrue(analisis["valido"])
        self.assertIsNone(analisis["jurisdiccion"])
        self.assertTrue(any("sin letra" in a for a in analisis["advertencias"]))

    def test_una_letra_desconocida_advierte(self):
        analisis = pjud.analizar_rit("X-12-2026")
        self.assertTrue(analisis["valido"])
        self.assertIsNone(analisis["jurisdiccion"])
        self.assertTrue(any("no está entre las que se conocen" in a for a in analisis["advertencias"]))

    def test_un_formato_invalido_lo_dice_con_ejemplos(self):
        analisis = pjud.analizar_rit("1234")
        self.assertFalse(analisis["valido"])
        self.assertIn("T-1234-2026", analisis["error"])

    def test_vacio_no_falla(self):
        self.assertIn("error", pjud.analizar_rit(""))

    def test_un_anio_imposible_se_rechaza(self):
        analisis = pjud.analizar_rit("C-1234-1801")
        self.assertFalse(analisis["valido"])


class TestElPlanDeLaMesaLoUsa(unittest.TestCase):
    """La mesa valida el RIT y avisa dónde se consulta, pero NO expone una herramienta que
    prometa traer el estado de la causa: eso vive en la OJV y ahí no entra ningún sistema solo."""

    def test_no_hay_herramienta_que_prometa_el_estado_de_la_causa(self):
        import mcp_server

        nombres = [t["name"] for t in mcp_server.TOOLS]
        self.assertNotIn("pjud_consultar_causa", nombres)
        # y ninguna otra promete consultar el expediente
        sospechosas = [n for n in nombres if "causa" in n and "ejecutar" not in n and "analizar" not in n]
        self.assertEqual(sospechosas, [])

    def test_la_mesa_avisa_donde_se_consulta_la_causa(self):
        import case_intake

        analisis = case_intake.caso_analizar(
            "Causa T-1234-2026 del Segundo Juzgado de Letras del Trabajo: despido sin aviso previo."
        )
        avisos = " ".join(analisis["advertencias"]).lower()
        self.assertIn("oficina judicial virtual", avisos)
        self.assertIn("clave", avisos)

    def test_un_rit_mal_escrito_se_advierte(self):
        import case_intake

        analisis = case_intake.caso_analizar("Causa X-12-2026 por despido injustificado.")
        self.assertTrue(any("no está entre las que se conocen" in a for a in analisis["advertencias"]))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
