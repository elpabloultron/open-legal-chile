"""El informe en derecho: hechos + análisis + triple pilar + transcripción literal de cada norma."""
import pathlib

import informe_derecho


def _cita_de_prueba():
    return {"formato": "[BCN - Código Civil, Art. 1545]",
            "texto": "TEXTO LITERAL DE PRUEBA " * 10,
            "url": "https://www.bcn.cl/leychile/navegar?idNorma=172986",
            "cita_completa": "[BCN - Código Civil, Art. 1545] https://www.bcn.cl/leychile/navegar?idNorma=172986"}


HECHOS = ("1. La empresa operó la planta desde 2017 con una RCA que autorizaba 4.000 toneladas mensuales. "
          "2. Desde el invierno la comunidad registra olores ofensivos. "
          "3. El estero que abastece de agua potable rural recibió escorrentías de lixiviados.")
OBJETO = "¿Es procedente la denuncia ambiental y la adopción de medidas cautelares?"
ANALISIS = (
    "La operación de la planta se encuentra amparada por una RCA vigente, de modo que el reproche "
    "ambiental no puede construirse sobre la ausencia de autorización, sino sobre el incumplimiento "
    "sobreviniente de sus condiciones. El artículo 25 quinquies de la Ley 19.300 habilita la revisión "
    "extraordinaria de la RCA cuando las variables evaluadas en el plan de seguimiento varían "
    "sustantivamente respecto de lo proyectado, hipótesis que se configura con los episodios "
    "reiterados de olores y las escorrentías de lixiviados descritos en los hechos. En paralelo, la "
    "conducta encuadra en las infracciones de la LO-SMA, que entrega a la Superintendencia las "
    "facultades cautelares del artículo 48; la cautelar resulta procedente pues existe un riesgo "
    "inminente para la salud de la población escolar y para la fuente de agua potable rural, y el "
    "beneficio que reporta su adopción excede largamente el perjuicio que irroga al titular.")


def _sin_material_local(monkeypatch):
    monkeypatch.setattr(informe_derecho, "_material_local",
                        lambda consulta, limite=8: {"jurisprudencia": [], "doctrina": []})


def test_exige_los_hechos_del_caso(tmp_path, monkeypatch):
    monkeypatch.setattr(informe_derecho, "EXPORTS_DIR", str(tmp_path))

    res = informe_derecho.exportar_informe_en_derecho(objeto=OBJETO, hechos="", analisis=ANALISIS,
                                                      dictamen="Se acoja.")

    assert "error" in res and "hechos" in res["error"]


def test_exige_la_cuestion_juridica(tmp_path, monkeypatch):
    monkeypatch.setattr(informe_derecho, "EXPORTS_DIR", str(tmp_path))

    res = informe_derecho.exportar_informe_en_derecho(objeto="", hechos=HECHOS, analisis=ANALISIS,
                                                      dictamen="Se acoja.")

    assert "error" in res and "objeto" in res["error"]


def test_exige_el_analisis_juridico(tmp_path, monkeypatch):
    """Un informe sin análisis es un formulario breve: se rechaza."""
    monkeypatch.setattr(informe_derecho, "EXPORTS_DIR", str(tmp_path))

    res = informe_derecho.exportar_informe_en_derecho(objeto=OBJETO, hechos=HECHOS, dictamen="Se acoja.")

    assert "error" in res and "análisis" in res["error"]


def test_incluye_la_seccion_de_analisis(tmp_path, monkeypatch):
    monkeypatch.setattr(informe_derecho, "EXPORTS_DIR", str(tmp_path))
    _sin_material_local(monkeypatch)
    monkeypatch.setattr(informe_derecho, "_textos_de_normas",
                        lambda referencias: {"citas": [], "faltantes": []})
    monkeypatch.setattr(informe_derecho, "_doctrina_para", lambda termino, limite=5: [])

    res = informe_derecho.exportar_informe_en_derecho(objeto=OBJETO, hechos=HECHOS, analisis=ANALISIS,
                                                      dictamen="Se acoja.")
    texto = pathlib.Path(res["archivos"]["markdownPath"]).read_text(encoding="utf-8")

    assert "## IV. Análisis jurídico" in texto
    assert ANALISIS[:60] in texto
    assert "IV. Análisis jurídico" in res["estructura"]


def test_transcribe_la_norma_completa_y_la_cita(tmp_path, monkeypatch):
    monkeypatch.setattr(informe_derecho, "EXPORTS_DIR", str(tmp_path))
    _sin_material_local(monkeypatch)
    monkeypatch.setattr(informe_derecho, "_textos_de_normas",
                        lambda referencias: {"citas": [_cita_de_prueba()], "faltantes": []})
    monkeypatch.setattr(informe_derecho, "_doctrina_para", lambda termino, limite=5: [])

    res = informe_derecho.exportar_informe_en_derecho(objeto=OBJETO, hechos=HECHOS, analisis=ANALISIS,
                                                      dictamen="Se acoja.", normas=["Código Civil art. 1545"])
    texto = pathlib.Path(res["archivos"]["markdownPath"]).read_text(encoding="utf-8")

    assert "TEXTO LITERAL DE PRUEBA" in texto           # transcripción en el cuerpo
    assert "[BCN - Código Civil, Art. 1545]" in texto   # la cita
    assert "Fuentes:" in texto                           # bloque de fuentes numerado
    assert pathlib.Path(res["archivos"]["docxPath"]).exists()
    assert res["entregable"] == "word"


def test_doctrina_automatica_cuando_no_la_piden(tmp_path, monkeypatch):
    monkeypatch.setattr(informe_derecho, "EXPORTS_DIR", str(tmp_path))
    _sin_material_local(monkeypatch)
    monkeypatch.setattr(informe_derecho, "_textos_de_normas",
                        lambda referencias: {"citas": [], "faltantes": []})
    monkeypatch.setattr(informe_derecho, "_doctrina_para",
                        lambda termino, limite=5: [{"obra": "Tratado de Responsabilidad",
                                                    "autor": "Barros Bourie", "institucion": "Daño moral",
                                                    "texto": "La responsabilidad ambiental se acredita por presunciones."}])

    res = informe_derecho.exportar_informe_en_derecho(objeto=OBJETO, hechos=HECHOS, analisis=ANALISIS,
                                                      dictamen="Se acoja.")
    texto = pathlib.Path(res["archivos"]["markdownPath"]).read_text(encoding="utf-8")

    assert "[Doctrina - Barros Bourie" in texto
    assert any("automáticamente" in a for a in res["advertencias"])


def test_jurisprudencia_automatica_del_material_local(tmp_path, monkeypatch):
    """La sección V no puede salir vacía habiendo sentencias: se busca en el corpus local."""
    monkeypatch.setattr(informe_derecho, "EXPORTS_DIR", str(tmp_path))
    monkeypatch.setattr(informe_derecho, "_textos_de_normas",
                        lambda referencias: {"citas": [], "faltantes": []})
    monkeypatch.setattr(informe_derecho, "_doctrina_para", lambda termino, limite=5: [])
    monkeypatch.setattr(informe_derecho, "_material_local", lambda consulta, limite=8: {
        "jurisprudencia": [{"cita": "[Hugging Face - jurisprudencia_ambiental/2TA/R-281-2021.md]",
                            "texto": "Que el daño ambiental en humedales se repara in natura …",
                            "url": "https://huggingface.co/datasets/pablobenavidesj/x/blob/main/y.md"}],
        "doctrina": []})

    res = informe_derecho.exportar_informe_en_derecho(objeto=OBJETO, hechos=HECHOS, analisis=ANALISIS,
                                                      dictamen="Se acoja.")
    texto = pathlib.Path(res["archivos"]["markdownPath"]).read_text(encoding="utf-8")

    assert "R-281-2021" in texto                        # la sentencia entra al cuerpo
    assert "jurisprudencia" not in res["faltantes"]      # ya no se declara faltante
    assert any("automáticamente" in a for a in res["advertencias"])
    assert any("jurisprudencia_ambiental" in c.get("formato", "") for c in res["citas"])


def test_doctrina_ambiental_de_la_biblioteca(tmp_path, monkeypatch):
    """La biblioteca ambiental también es doctrina citable cuando no la entregan."""
    monkeypatch.setattr(informe_derecho, "EXPORTS_DIR", str(tmp_path))
    monkeypatch.setattr(informe_derecho, "_textos_de_normas",
                        lambda referencias: {"citas": [], "faltantes": []})
    monkeypatch.setattr(informe_derecho, "_doctrina_para", lambda termino, limite=5: [])
    monkeypatch.setattr(informe_derecho, "_material_local", lambda consulta, limite=8: {
        "jurisprudencia": [],
        "doctrina": [{"cita": "[Hugging Face - biblioteca_ambiental/informes/IT-3-2023.md]",
                      "texto": "El estándar de reparación exige medidas in natura del ecosistema …",
                      "url": "", "obra": "Informe en derecho TA", "autor": "", "institucion": "biblioteca"}]})

    res = informe_derecho.exportar_informe_en_derecho(objeto=OBJETO, hechos=HECHOS, analisis=ANALISIS,
                                                      dictamen="Se acoja.")
    texto = pathlib.Path(res["archivos"]["markdownPath"]).read_text(encoding="utf-8")

    assert "[Hugging Face - biblioteca_ambiental/informes/IT-3-2023.md]" in texto
    assert any("biblioteca_ambiental" in c.get("formato", "") for c in res["citas"])


def test_declara_lo_que_no_pudo_traer(tmp_path, monkeypatch):
    monkeypatch.setattr(informe_derecho, "EXPORTS_DIR", str(tmp_path))
    _sin_material_local(monkeypatch)
    monkeypatch.setattr(informe_derecho, "_textos_de_normas",
                        lambda referencias: {"citas": [], "faltantes": ["Ley 19.300"]})
    monkeypatch.setattr(informe_derecho, "_doctrina_para", lambda termino, limite=5: [])

    res = informe_derecho.exportar_informe_en_derecho(objeto=OBJETO, hechos=HECHOS, analisis=ANALISIS,
                                                      dictamen="Se acoja.", normas=["Ley 19.300"])
    texto = pathlib.Path(res["archivos"]["markdownPath"]).read_text(encoding="utf-8")

    assert "sin fuente verificable" in texto and "Ley 19.300" in texto
    assert "Ley 19.300" in res["faltantes"]


def test_detecta_normas_mencionadas_en_los_textos(tmp_path, monkeypatch):
    monkeypatch.setattr(informe_derecho, "EXPORTS_DIR", str(tmp_path))
    _sin_material_local(monkeypatch)
    capturadas = {}

    def _falso(referencias):
        capturadas["refs"] = list(referencias)
        return {"citas": [], "faltantes": []}

    monkeypatch.setattr(informe_derecho, "_textos_de_normas", _falso)
    monkeypatch.setattr(informe_derecho, "_doctrina_para", lambda termino, limite=5: [])

    informe_derecho.exportar_informe_en_derecho(
        objeto="¿Procede invocar el artículo 1545 del Código Civil y la Ley 19.300 art. 25 quinquies?",
        hechos=HECHOS, analisis=ANALISIS, dictamen="Se acoja.")

    assert any("Código Civil" in r for r in capturadas["refs"])


def test_textos_de_normas_refresca_el_servidor_y_pide_sin_recorte(monkeypatch):
    """El lote real corre con los globales del servidor inyectados y sin el recorte de 1200."""
    import servidor.corpus as corpus

    visto = {}

    def _refrescar():
        visto["refrescado"] = True

    def _lote(referencias, limite=1200):
        visto["limite"] = limite
        return {"citas": [], "faltantes": []}

    monkeypatch.setattr(corpus, "_refrescar", _refrescar)
    monkeypatch.setattr(corpus, "_citas_por_lote", _lote)

    res = informe_derecho._textos_de_normas(["Código Civil art. 1545"])

    assert visto == {"refrescado": True, "limite": None}
    assert res == {"citas": [], "faltantes": []}
