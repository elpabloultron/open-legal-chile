"""El informe en derecho: hechos + triple pilar + transcripción literal de cada norma."""
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


def test_exige_los_hechos_del_caso(tmp_path, monkeypatch):
    monkeypatch.setattr(informe_derecho, "EXPORTS_DIR", str(tmp_path))

    res = informe_derecho.exportar_informe_en_derecho(objeto=OBJETO, hechos="", dictamen="Se acoja.")

    assert "error" in res and "hechos" in res["error"]


def test_exige_la_cuestion_juridica(tmp_path, monkeypatch):
    monkeypatch.setattr(informe_derecho, "EXPORTS_DIR", str(tmp_path))

    res = informe_derecho.exportar_informe_en_derecho(objeto="", hechos=HECHOS, dictamen="Se acoja.")

    assert "error" in res and "objeto" in res["error"]


def test_transcribe_la_norma_completa_y_la_cita(tmp_path, monkeypatch):
    monkeypatch.setattr(informe_derecho, "EXPORTS_DIR", str(tmp_path))
    monkeypatch.setattr(informe_derecho, "_textos_de_normas",
                        lambda referencias: {"citas": [_cita_de_prueba()], "faltantes": []})
    monkeypatch.setattr(informe_derecho, "_doctrina_para", lambda termino, limite=3: [])

    res = informe_derecho.exportar_informe_en_derecho(objeto=OBJETO, hechos=HECHOS,
                                                      dictamen="Se acoja.", normas=["Código Civil art. 1545"])
    texto = pathlib.Path(res["archivos"]["markdownPath"]).read_text(encoding="utf-8")

    assert "TEXTO LITERAL DE PRUEBA" in texto           # transcripción en el cuerpo
    assert "[BCN - Código Civil, Art. 1545]" in texto   # la cita
    assert "Fuentes:" in texto                           # bloque de fuentes numerado
    assert pathlib.Path(res["archivos"]["docxPath"]).exists()
    assert res["entregable"] == "word"


def test_doctrina_automatica_cuando_no_la_piden(tmp_path, monkeypatch):
    monkeypatch.setattr(informe_derecho, "EXPORTS_DIR", str(tmp_path))
    monkeypatch.setattr(informe_derecho, "_textos_de_normas",
                        lambda referencias: {"citas": [], "faltantes": []})
    monkeypatch.setattr(informe_derecho, "_doctrina_para",
                        lambda termino, limite=3: [{"obra": "Tratado de Responsabilidad",
                                                    "autor": "Barros Bourie", "institucion": "Daño moral",
                                                    "texto": "El daño moral se acredita por presunciones."}])

    res = informe_derecho.exportar_informe_en_derecho(objeto=OBJETO, hechos=HECHOS, dictamen="Se acoja.")
    texto = pathlib.Path(res["archivos"]["markdownPath"]).read_text(encoding="utf-8")

    assert "[Doctrina - Barros Bourie" in texto
    assert any("automáticamente" in a for a in res["advertencias"])


def test_declara_lo_que_no_pudo_traer(tmp_path, monkeypatch):
    monkeypatch.setattr(informe_derecho, "EXPORTS_DIR", str(tmp_path))
    monkeypatch.setattr(informe_derecho, "_textos_de_normas",
                        lambda referencias: {"citas": [], "faltantes": ["Ley 19.300"]})
    monkeypatch.setattr(informe_derecho, "_doctrina_para", lambda termino, limite=3: [])

    res = informe_derecho.exportar_informe_en_derecho(objeto=OBJETO, hechos=HECHOS,
                                                      dictamen="Se acoja.", normas=["Ley 19.300"])
    texto = pathlib.Path(res["archivos"]["markdownPath"]).read_text(encoding="utf-8")

    assert "sin fuente verificable" in texto and "Ley 19.300" in texto
    assert "Ley 19.300" in res["faltantes"]


def test_detecta_normas_mencionadas_en_los_textos(tmp_path, monkeypatch):
    monkeypatch.setattr(informe_derecho, "EXPORTS_DIR", str(tmp_path))
    capturadas = {}

    def _falso(referencias):
        capturadas["refs"] = list(referencias)
        return {"citas": [], "faltantes": []}

    monkeypatch.setattr(informe_derecho, "_textos_de_normas", _falso)
    monkeypatch.setattr(informe_derecho, "_doctrina_para", lambda termino, limite=3: [])

    informe_derecho.exportar_informe_en_derecho(
        objeto="¿Procede invocar el artículo 1545 del Código Civil y la Ley 19.300 art. 25 quinquies?",
        hechos=HECHOS, dictamen="Se acoja.")

    assert any("Código Civil" in r for r in capturadas["refs"])
