"""El tablero de diagnóstico tiene que medir de verdad.

El `check` original imprimía doce líneas con ✅ fijos sin mirar nada: decía «BCN ✅ Operativo» con
la red caída y no mencionaba el OCR. Este doctor mide y, cuando algo falta, dice el paso exacto
para resolverlo — sin mandar a nadie a la terminal.
"""

import pathlib

import diagnostico

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def test_el_diagnostico_mide_y_devuelve_estado():
    res = diagnostico.diagnostico_completo()

    assert res["estado"] in ("ok", "degradado", "error")
    assert isinstance(res["chequeos"], list) and len(res["chequeos"]) >= 5
    for chequeo in res["chequeos"]:
        assert {"nombre", "estado", "detalle"} <= set(chequeo)
        assert chequeo["detalle"], f"{chequeo['nombre']} sin detalle: no mide nada"
        assert chequeo["estado"] in ("ok", "aviso", "error", "omitido")


def test_el_diagnostico_incluye_ocr_corpus_grafo_y_herramientas():
    nombres = {c["nombre"] for c in diagnostico.diagnostico_completo()["chequeos"]}

    assert {"ocr", "corpus", "grafo", "herramientas_mcp"} <= nombres


def test_el_chequeo_de_ocr_nombra_los_motores():
    ocr = next(c for c in diagnostico.diagnostico_completo()["chequeos"] if c["nombre"] == "ocr")

    assert "rapidocr" in ocr["detalle"].lower(), ocr["detalle"]


def test_el_chequeo_de_herramientas_cuenta_las_del_paso_0():
    cheq = next(c for c in diagnostico.diagnostico_completo()["chequeos"]
                if c["nombre"] == "herramientas_mcp")

    assert cheq["estado"] == "ok", cheq
    assert "consulta_maestra" in cheq["detalle"]


def test_el_doctor_no_manda_a_instalar_por_terminal():
    for chequeo in diagnostico.diagnostico_completo()["chequeos"]:
        sugerencia = (chequeo.get("sugerencia") or "").lower()
        assert "pip install rapidocr" not in sugerencia
        assert "pip install huggingface" not in sugerencia
        assert "apt install" not in sugerencia


def test_la_cli_expone_doctor():
    fuente = (RAIZ / "openlegal.py").read_text(encoding="utf-8")

    assert '"doctor"' in fuente, "la CLI tiene que ofrecer `openlegal doctor`"
    assert "diagnostico_completo" in fuente, "y tiene que usar el diagnóstico real"


def test_el_doctor_revisa_los_recursos_y_el_entorno():
    chequeos = {c["nombre"]: c for c in diagnostico.diagnostico_completo()["chequeos"]}
    assert chequeos["recursos"]["estado"] == "ok", chequeos["recursos"]
    assert "18 skills" in chequeos["recursos"]["detalle"] or "skills" in chequeos["recursos"]["detalle"]
    # Lo opcional informa, no degrada.
    assert chequeos["entorno"]["estado"] == "ok" and "uvx" in chequeos["entorno"]["detalle"]
    assert chequeos["harness"]["estado"] == "ok"


def test_token_de_hugging_face_por_entorno_cuenta(monkeypatch, tmp_path):
    """El plugin pasa el token por HF_TOKEN (userConfig): el doctor no puede decir que falta."""
    monkeypatch.setattr(diagnostico.pathlib.Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setenv("HF_TOKEN", "hf_prueba")
    assert diagnostico._chequeo_hugging_face()["estado"] == "ok"
    monkeypatch.setenv("HF_TOKEN", "")
    monkeypatch.delenv("HUGGING_FACE_HUB_TOKEN", raising=False)
    assert diagnostico._chequeo_hugging_face()["estado"] == "aviso"
