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


class TestInstruccionesDeConsulta(unittest.TestCase):
    def test_trae_el_enlace_los_pasos_y_la_seccion(self):
        datos = pjud.instrucciones_de_consulta("T-1234-2026")
        consulta = datos["consulta"]
        self.assertIn("oficinajudicialvirtual.pjud.cl", consulta["enlace"])
        self.assertTrue(any("Laboral" in paso for paso in consulta["pasos"]))
        self.assertTrue(any("ClaveÚnica" in x for x in consulta["que_vas_a_necesitar"]))
        self.assertIn("captcha", consulta["por_que_no_lo_hace_la_suite"])
        self.assertIn("T-1234-2026", " ".join(consulta["pasos"]))

    def test_dice_para_que_si_sirve_la_suite(self):
        datos = pjud.instrucciones_de_consulta("C-1-2026")
        utilidades = " ".join(datos["consulta"]["lo_que_si_puede_hacer_la_suite"])
        self.assertIn("pjud_search_jurisprudencia", utilidades)

    def test_no_devuelve_el_estado_de_la_causa(self):
        """Lo más importante: que no simule un resultado que no tiene."""
        datos = pjud.instrucciones_de_consulta("T-1234-2026")
        prohibidas = ("estado", "tramitacion", "tramitación", "ultimo_proveido", "proveido", "fecha_ultimo")
        for clave in prohibidas:
            self.assertNotIn(clave, datos, f"no debería devolver «{clave}»")

    def test_un_rit_invalido_no_arma_instrucciones(self):
        datos = pjud.instrucciones_de_consulta("no es un rit")
        self.assertNotIn("consulta", datos)
        self.assertIn("error", datos)


class TestElPlanDeLaMesaLoUsa(unittest.TestCase):
    def test_la_mesa_valida_el_rit_antes_de_buscar(self):
        import case_intake

        analisis = case_intake.caso_analizar(
            "Causa T-1234-2026 del Segundo Juzgado de Letras del Trabajo: despido sin aviso previo."
        )
        usadas = [p["herramienta"] for p in analisis["plan"]]
        self.assertIn("pjud_consultar_causa", usadas)
        self.assertLess(usadas.index("pjud_consultar_causa"), usadas.index("pjud_search_jurisprudencia"))

    def test_el_paso_lleva_el_rit_con_letra(self):
        import case_intake

        analisis = case_intake.caso_analizar("Causa T-1234-2026 por despido injustificado.")
        paso = next(p for p in analisis["plan"] if p["herramienta"] == "pjud_consultar_causa")
        self.assertEqual(paso["argumentos"]["rit"], "T-1234-2026")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
