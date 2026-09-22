"""La mesa de entrada: de un caso a un plan.

Dos familias de pruebas:

* **Decisión**: la tabla de casos. Entra un caso real de la práctica chilena y se verifica qué
  materia detecta y qué herramientas propone. Sin red: esto es el clasificador.
* **Ejecución**: con un despachador de mentira se comprueba que los pasos se ejecutan, que un
  paso que falla queda anotado con su error, que los pasos sin parámetros se saltean en vez de
  inventarlos y que ninguna salida promete más de lo que pasó.
"""

from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import case_intake  # noqa: E402
import mcp_server  # noqa: E402


class TestDecision(unittest.TestCase):
    """La tabla: caso → materia → herramientas."""

    CASOS = [
        # (descripción, texto, materia esperada, herramienta que NO puede faltar)
        ("laboral por texto",
         "Me despidieron sin aviso previo luego de 6 años. El finiquito está mal calculado y "
         "quiero reclamar las indemnizaciones.", "laboral", "dt_search_doctrina"),
        ("laboral con RIT",
         "Causa T-1234-2026, Segundo Juzgado de Letras del Trabajo. Despido por necesidades de "
         "la empresa sin aviso previo.", "laboral", "bcn_get_codigo"),
        ("familia",
         "Necesito pedir el aumento de la pensión de alimentos y regular el cuidado personal de "
         "mis dos hijos.", "familia", "pjud_search_jurisprudencia"),
        ("penal",
         "Mi hermano quedó con prisión preventiva por una querella por estafa; necesito revisar "
         "la carpeta de la fiscalía.", "penal", "bcn_get_codigo"),
        ("civil",
         "El arrendatario no paga desde marzo y quiero cobrar las rentas y terminar el contrato "
         "de arriendo.", "civil", "bcn_get_codigo"),
        ("inmobiliario",
         "Hay que hacer el estudio de títulos de una propiedad inscrita en el Conservador de "
         "Bienes Raíces: el certificado de hipoteca y gravámenes muestra una prohibición.",
         "inmobiliario", "cbr_estudio_titulos"),
        ("ambiental",
         "La SMA abrió un procedimiento sancionatorio (SNIFA) por incumplir la RCA.", "ambiental",
         "sma_search_sancionatorios"),
        ("competencia",
         "Hay una colusión en el mercado de alimentos y queremos presentar un requerimiento "
         "ante el TDLC.", "competencia", "tdlc_search_jurisprudencia"),
        ("energía",
         "Discusión por la tarifa de distribución eléctrica ante el Panel de Expertos.",
         "energia", "cne_get_centrales_y_proyectos"),
        ("administrativo",
         "La Municipalidad rechazó la patente y quiero reclamar ante la Contraloría.",
         "administrativo", "cgr_search_jurisprudencia"),
        ("tributario",
         "El SII me hizo una fiscalización por IVA y quiero revisar las circulares vigentes.",
         "tributario", "sii_search_circulares"),
        ("consumidor",
         "Compré un auto con publicidad engañosa y el vendedor no respeta la garantía legal.",
         "consumidor", "bcn_get_ley"),
        ("protección",
         "Quiero presentar un recurso de protección por la garantía constitucional del art. 20 "
         "contra una isapre.", "proteccion", "pjud_search_jurisprudencia"),
        ("datos personales",
         "Un cliente pide sus datos personales bajo la 19.628 y quieren responder con las "
         "reglas de la Ley 21.719.", "datos", "bcn_get_ley"),
        ("propiedad industrial",
         "Quiero inscribir una marca en INAPI y preparar una carta de cese y desistimiento "
         "para quien la está usando.", "propiedad_industrial", "inapi_evaluar_marca"),
    ]

    def test_la_tabla_de_casos(self):
        """Las 15 filas de la tabla, de una sola pasada.

        Sin `subTest` a propósito: en Windows el sub-test se cae al finalizar su contexto
        (UnicodeDecodeError en el capturador de pytest, con la salida en cp1252) y arrastra a
        todas las pruebas que vienen después. Un recorrido que junta los desajustes y falla una
        sola vez prueba lo mismo y no depende de la maquinaria del capturador. Los rótulos van
        sin acentos por la misma razón: el archivo es UTF-8, pero la consola de Windows no.
        """
        desajustes = []
        for numero, (descripcion, texto, materia, herramienta) in enumerate(self.CASOS, 1):
            analisis = case_intake.caso_analizar(texto)
            usadas = [p["herramienta"] for p in analisis["plan"]]
            if analisis["materia"] != materia:
                desajustes.append(
                    f"caso {numero} ({descripcion}): esperaba materia={materia}, "
                    f"detecto {analisis['materia']}"
                )
            if herramienta not in usadas:
                desajustes.append(
                    f"caso {numero} ({descripcion}): falta la herramienta {herramienta} "
                    f"en el plan {usadas}"
                )
        self.assertFalse(desajustes, "\n".join(desajustes))

    def test_sin_senales_no_inventa_materia(self):
        analisis = case_intake.caso_analizar("tengo un problema con mi vecino por la reja")
        self.assertIsNone(analisis["materia"])
        self.assertTrue(analisis["advertencias"])
        self.assertIn("la materia", " ".join(analisis["faltantes"]))

    def test_una_sola_senal_avisa(self):
        analisis = case_intake.caso_analizar("hubo un despido")
        self.assertEqual(analisis["materia"], "laboral")
        self.assertTrue(any("una sola señal" in a for a in analisis["advertencias"]))

    def test_detecta_instituciones_y_sus_herramientas(self):
        analisis = case_intake.caso_analizar(
            "Necesito revisar las circulares del SII y los dictámenes de la Dirección del Trabajo.")
        self.assertIn("SII", analisis["instituciones"])
        usadas = [p["herramienta"] for p in analisis["plan"]]
        self.assertIn("sii_search_circulares", usadas)
        self.assertIn("dt_search_doctrina", usadas)

    def test_la_carpeta_se_lee_por_sus_documentos(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = pathlib.Path(tmp)
            (raiz / "01_demanda_civil.pdf").write_bytes(b"%PDF-1.4 falso")
            (raiz / "02_contestacion.docx").write_bytes(b"PK falso")
            (raiz / "notas.txt").write_text("el cliente dice que firmó el contrato en 2021",
                                             encoding="utf-8")
            analisis = case_intake.caso_analizar(str(raiz), tipo="carpeta")
            self.assertEqual(analisis["tipo_entrada"], "carpeta")
            tipos = analisis["deteccion"]["tipos_de_documento"]
            self.assertIn("demanda", tipos)
            self.assertIn("contestacion", tipos)
            self.assertIn("ocr_extract_pdf", [p["herramienta"] for p in analisis["plan"]])

    def test_una_carpeta_que_no_existe_lo_dice(self):
        analisis = case_intake.caso_analizar("/no/existe/esta/carpeta", tipo="carpeta")
        self.assertTrue(any("no existe la carpeta" in n for n in analisis["deteccion"]["notas"]))

    def test_entrada_vacia_no_falla(self):
        analisis = case_intake.caso_analizar("")
        self.assertIn("error", analisis)

    def test_todos_los_pasos_de_busqueda_llevan_consulta(self):
        analisis = case_intake.caso_analizar(
            "Despido injustificado: quiero la indemnización.", consulta="cuánto me corresponde")
        for paso in analisis["plan"]:
            if paso["herramienta"] in case_intake.HERRAMIENTAS_DE_BUSQUEDA:
                self.assertTrue(paso["argumentos"].get("query"),
                                f"{paso['herramienta']} quedó sin consulta")

    def test_el_plan_lleva_la_compuerta_de_revision(self):
        analisis = case_intake.caso_analizar("Despido injustificado con finiquito mal calculado.")
        self.assertIn("revisión jurídica", analisis["resumen"])
        self.assertIn("abogado habilitado", analisis["resumen"])


class TestEjecucion(unittest.TestCase):
    """La ejecución con un despachador de mentira: acá se prueba la honestidad, no la red."""

    TEXTO = "Causa T-1234-2026. Despido sin aviso previo, finiquito mal calculado."

    def setUp(self):
        self.llamadas: list = []
        self.original = mcp_server.handle_tool_call

        def falso(nombre, argumentos):
            self.llamadas.append((nombre, dict(argumentos)))
            if nombre == "explota":
                raise RuntimeError("el servicio del Estado no responde")
            return {"ok": nombre, "argumentos": argumentos}

        mcp_server.handle_tool_call = falso

    def tearDown(self):
        mcp_server.handle_tool_call = self.original

    def test_ejecuta_los_pasos_del_plan(self):
        resultado = case_intake.caso_ejecutar(self.TEXTO, limite_pasos=3)
        self.assertEqual(len(resultado["resultados"]), 3)
        self.assertTrue(all(r["estado"] == "ok" for r in resultado["resultados"]))
        self.assertEqual([n for n, _ in self.llamadas][0], "pjud_consultar_causa")

    def test_un_paso_que_falla_queda_anotado_y_no_tumba_la_mesa(self):
        def falso(nombre, argumentos):
            self.llamadas.append((nombre, dict(argumentos)))
            raise RuntimeError("el servicio del Estado no responde")

        mcp_server.handle_tool_call = falso
        resultado = case_intake.caso_ejecutar(self.TEXTO, limite_pasos=2)
        self.assertEqual(len(resultado["resultados"]), 2)
        for paso in resultado["resultados"]:
            self.assertEqual(paso["estado"], "error")
            self.assertIn("no responde", paso["motivo"])
        self.assertIn("fallaron 2", resultado["resumen"])

    def test_los_pasos_sin_parametros_se_saltean_y_se_dicen(self):
        resultado = case_intake.caso_ejecutar(self.TEXTO, pasos=[6], limite_pasos=6)
        salteados = [r for r in resultado["resultados"] if r["estado"] == "salteado"]
        self.assertTrue(salteados)
        self.assertTrue(all("motivo" in s for s in salteados))

    def test_seleccionar_pasos_por_numero(self):
        resultado = case_intake.caso_ejecutar(self.TEXTO, pasos=[3])
        self.assertEqual(len(resultado["resultados"]), 1)
        self.assertEqual(resultado["resultados"][0]["herramienta"], "dt_search_doctrina")

    def test_no_se_inventa_una_salida_para_un_paso_fallado(self):
        def falso(nombre, argumentos):
            raise RuntimeError("caído")

        mcp_server.handle_tool_call = falso
        resultado = case_intake.caso_ejecutar(self.TEXTO, limite_pasos=1)
        self.assertNotIn("salida", resultado["resultados"][0])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
