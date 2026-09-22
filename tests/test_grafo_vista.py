"""El visor de grafos: que se pueda ver, y que se pueda pedir en lenguaje natural.

El motor arma grafos que hasta ahora sólo se miraban en la consola. Estas pruebas fijan que el
visor escriba un HTML de verdad (con los datos adentro), que no toque el grafo del corpus, que
diga lo que no pudo leer, y que las descripciones de las herramientas traigan el disparador en
lenguaje natural: es lo que hace que el modelo las use cuando la persona dice «mostrame el grafo».
"""

from __future__ import annotations

import os
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import grafo_vista  # noqa: E402


def _carpeta_de_prueba(raiz: str) -> str:
    carpeta = pathlib.Path(raiz) / "caso"
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "01_demanda.md").write_text(
        "# Demanda por despido injustificado\n\n## Hechos\nDespido sin aviso previo.\n\n"
        "## Normas invocadas\n- Artículo 161 del Código del Trabajo\n", encoding="utf-8")
    (carpeta / "02_informe.md").write_text(
        "# Informe del caso\n\n## Antecedentes\nContrato indefinido.\n", encoding="utf-8")
    return str(carpeta)


class TestVerCaso(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.salida = os.path.join(self.temporal.name, "vista.html")

    def test_arma_el_grafo_y_escribe_un_html_con_los_datos_adentro(self):
        resultado = grafo_vista.ver_caso(_carpeta_de_prueba(self.temporal.name), salida=self.salida)
        self.assertNotIn("error", resultado)
        self.assertGreaterEqual(resultado["nodos"], 4)
        self.assertGreaterEqual(resultado["aristas"], 3)
        contenido = pathlib.Path(self.salida).read_text(encoding="utf-8")
        self.assertIn("vis-network", contenido)
        self.assertIn("Demanda por despido injustificado", contenido)
        self.assertIn("vis.DataSet", contenido)  # los datos van adentro del HTML
        self.assertIn("const nodos = new vis.DataSet", contenido)
        self.assertIn("<html", contenido.lower())

    def test_dice_qué_documentos_leyó(self):
        resultado = grafo_vista.ver_caso(_carpeta_de_prueba(self.temporal.name), salida=self.salida)
        leidos = " ".join(d["archivo"] for d in resultado["documentos_leidos"])
        self.assertIn("01_demanda.md", leidos)
        self.assertIn("02_informe.md", leidos)
        self.assertEqual(resultado["saltados"], [])

    def test_una_carpeta_inexistente_lo_dice_sin_inventar(self):
        resultado = grafo_vista.ver_caso("/ruta/que/no/existe", salida=self.salida)
        self.assertIn("error", resultado)
        self.assertNotIn("nodos", resultado)

    def test_una_carpeta_vacía_lo_dice(self):
        vacia = pathlib.Path(self.temporal.name) / "vacia"
        vacia.mkdir()
        resultado = grafo_vista.ver_caso(str(vacia), salida=self.salida)
        self.assertIn("error", resultado)

    def test_un_archivo_ilegible_no_desaparece_sin_aviso(self):
        carpeta = pathlib.Path(_carpeta_de_prueba(self.temporal.name))
        (carpeta / "03_escaneo.pdf").write_bytes(b"%PDF-1.4 basura que no es un pdf de verdad")
        resultado = grafo_vista.ver_caso(str(carpeta), salida=self.salida)
        motivos = " ".join(s.get("motivo", "") for s in resultado.get("saltados", []))
        self.assertTrue("no se pudo leer" in motivos or "sin texto" in motivos or resultado.get("saltados"),
                        "el archivo ilegible tiene que aparecer en saltados")


class TestVerCorpus(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.salida = os.path.join(self.temporal.name, "corpus.html")

    def test_una_consulta_devuelve_un_subgrafo(self):
        resultado = grafo_vista.ver_corpus(consulta="despido", salida=self.salida)
        self.assertNotIn("error", resultado)
        self.assertFalse(resultado["muestra"])
        self.assertGreater(resultado["nodos"], 1)
        self.assertTrue(pathlib.Path(self.salida).is_file())

    def test_una_consulta_sin_resultado_lo_dice(self):
        resultado = grafo_vista.ver_corpus(consulta="zzzzqqq", salida=self.salida)
        self.assertIn("error", resultado)

    def test_el_recorte_avisa_que_es_un_recorte(self):
        resultado = grafo_vista.ver_corpus(max_nodos=40, salida=self.salida)
        self.assertTrue(resultado["muestra"])
        self.assertLessEqual(resultado["nodos"], 40)

    def test_no_toca_el_grafo_del_corpus(self):
        """Ver no puede modificar el grafo: es de sólo lectura."""
        import hashlib

        ruta = pathlib.Path(__file__).resolve().parent.parent / "data" / "legal_knowledge_graph.json"
        if not ruta.is_file():
            self.skipTest("no hay grafo construido")
        antes = hashlib.sha256(ruta.read_bytes()).hexdigest()
        grafo_vista.ver_corpus(max_nodos=30, salida=self.salida)
        self.assertEqual(antes, hashlib.sha256(ruta.read_bytes()).hexdigest())


class TestElDisparadorEnLenguajeNatural(unittest.TestCase):
    """Lo que hace que la persona pueda pedirlo sin nombrar nada."""

    def _descripcion(self, nombre: str) -> str:
        import mcp_server

        for t in mcp_server.TOOLS:
            if t["name"] == nombre:
                return t["description"]
        self.fail(f"no está la herramienta {nombre}")

    def test_las_herramientas_estan_en_el_catalogo(self):
        import mcp_server

        nombres = [t["name"] for t in mcp_server.TOOLS]
        self.assertIn("grafo_ver_corpus", nombres)
        self.assertIn("grafo_ver_caso", nombres)

    def test_la_descripcion_del_corpus_trae_los_pedidos_naturales(self):
        descripcion = self._descripcion("grafo_ver_corpus").lower()
        for frase in ("mostrame el grafo", "cómo se ve"):
            self.assertIn(frase, descripcion)

    def test_la_descripcion_del_caso_trae_los_pedidos_naturales(self):
        descripcion = self._descripcion("grafo_ver_caso").lower()
        for frase in ("graficá este caso", "cómo se ve"):
            self.assertIn(frase, descripcion)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
