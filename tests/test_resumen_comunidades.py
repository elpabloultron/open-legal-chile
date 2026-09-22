"""El resumen por comunidades: el panorama del grafo en unos cientos de tokens.

Es la idea de GraphRAG (arXiv:2404.16130): comunidades que se resumen, y se lee el resumen en vez
de recorrer los nodos. Estas pruebas fijan que el resumen exista, que sea mucho más chico que el
corpus, que diga cuántas comunidades hay, y que las herramientas lo ofrezcan cuando la persona pide
un panorama en lenguaje natural.
"""

from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


def _motor():
    import legal_graphify

    m = legal_graphify.LegalGraphifyEngine()
    if not m.cargar_grafo_json():
        raise unittest.SkipTest("no hay grafo construido")
    return m


class TestResumenPorComunidades(unittest.TestCase):
    def test_resume_el_grafo_y_dice_cuantas_comunidades_hay(self):
        r = _motor().resumen_por_comunidades(top_n=5)
        self.assertNotIn("error", r)
        self.assertGreater(r["comunidades_totales"], 5)
        self.assertGreater(r["nodos_totales"], 1000)
        self.assertEqual(len(r["comunidades"]), 5)

    def test_cada_comunidad_trae_tamano_area_y_representativos(self):
        r = _motor().resumen_por_comunidades(top_n=3)
        for comunidad in r["comunidades"]:
            self.assertGreater(comunidad["tamano"], 0)
            self.assertTrue(comunidad["area_principal"])
            self.assertTrue(comunidad["representativos"])
            self.assertTrue(all(isinstance(x, str) and x for x in comunidad["representativos"]))

    def test_el_resumen_es_minimo_al_lado_del_corpus(self):
        """Lo que importa para el ahorro: que el panorama cueste cientos de tokens, no miles."""
        r = _motor().resumen_por_comunidades(top_n=12)
        self.assertLess(r["tokens_aproximados"], 5000,
                        "el resumen dejó de ser un resumen")
        self.assertGreater(r["tokens_aproximados"], 100)

    def test_las_comunidades_estan_ordenadas_por_tamano(self):
        r = _motor().resumen_por_comunidades(top_n=8)
        tamanos = [c["tamano"] for c in r["comunidades"]]
        self.assertEqual(tamanos, sorted(tamanos, reverse=True))


class TestElDisparadorEnLenguajeNatural(unittest.TestCase):
    def _descripcion(self, nombre: str) -> str:
        import mcp_server

        for t in mcp_server.TOOLS:
            if t["name"] == nombre:
                return str(t["description"])
        self.fail(f"no está la herramienta {nombre}")

    def test_esta_en_el_catalogo(self):
        import mcp_server

        self.assertIn("graphify_resumen_comunidades", [t["name"] for t in mcp_server.TOOLS])

    def test_la_descripcion_trae_los_pedidos_de_panorama(self):
        d = self._descripcion("graphify_resumen_comunidades").lower()
        for frase in ("qué hay en el corpus", "resumen general", "panorama"):
            self.assertIn(frase, d)

    def test_la_descripcion_manda_al_detalle_cuando_hace_falta(self):
        d = self._descripcion("graphify_resumen_comunidades")
        self.assertIn("graphify_consulta_subgrafo", d)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
