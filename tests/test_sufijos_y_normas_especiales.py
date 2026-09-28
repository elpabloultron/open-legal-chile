"""Los sufijos latinos viajan con el artículo, y la Constitución y el Código Sanitario se citan.

Falencias medidas el 2026-09-28: (1) «Ley 19.300 art. 25 quinquies» devolvía el texto del
25 quáter — la copia local tenía el quáter guardado bajo la clave «25» porque el parser no
aceptaba la tilde de «quáter»; (2) la Constitución y el Código Sanitario no estaban en el
catálogo y no se podían citar (el recurso de protección los necesita).
"""

import citas_legales
import mcp_server
from bcn_connector import BCNClient


# ── 1. Sufijos latinos en el detector ──────────────────────────────────────────

def test_detectar_normas_conserva_el_sufijo():
    normas = citas_legales.detectar_normas("revisá la Ley 19.300 art. 25 quinquies, por favor")
    assert normas, "debe detectar la ley con su artículo"
    assert normas[0]["familia"] == "ley" and normas[0]["numero"] == "19300"
    assert normas[0]["articulo"] == "25 quinquies", normas[0]
    assert normas[0]["etiqueta"] == "BCN - Ley N° 19300, Art. 25 quinquies"


def test_detectar_normas_acepta_quater_con_tilde():
    normas = citas_legales.detectar_normas("el artículo 25 quáter de la Ley 19.300")
    assert normas and normas[0]["articulo"] == "25 quáter", normas


def test_detectar_normas_sufijos_y_guion():
    for texto, esperado in (
        ("Ley 20.417 art. 47", "47"),
        ("Código Civil art. 183-A", "183-a"),
        ("Ley 19.300 art. 25 sexies", "25 sexies"),
        ("el artículo 25 bis de la Ley 19.300", "25 bis"),
    ):
        normas = citas_legales.detectar_normas(texto)
        assert normas and normas[0]["articulo"] == esperado, (texto, normas)


def test_detectar_normas_reconoce_constitucion_y_sanitario():
    cpr = citas_legales.detectar_normas("el artículo 20 CPR")
    assert cpr and cpr[0]["familia"] == "codigo" and cpr[0]["obra"] == "constitucion", cpr
    assert cpr[0]["articulo"] == "20"
    san = citas_legales.detectar_normas("Código Sanitario art. 67")
    assert san and san[0]["obra"] == "sanitario" and san[0]["articulo"] == "67", san
    const = citas_legales.detectar_normas("Constitución Política art. 19")
    assert const and const[0]["obra"] == "constitucion" and const[0]["articulo"] == "19", const


# ── 2. El parser y el buscador de artículos del conector ───────────────────────

def test_parser_separa_quater_con_tilde(tmp_path):
    xml = (
        '<Norma normaId="1" fechaVersion="2026-01-01" derogado="no">'
        '<Metadatos><TituloNorma>Prueba</TituloNorma></Metadatos>'
        '<EstructuraFuncional tipoParte="articulo" idParte="1"><Texto>Artículo 25.- base</Texto></EstructuraFuncional>'
        '<EstructuraFuncional tipoParte="articulo" idParte="2"><Texto>Artículo 25 quáter.- medio</Texto></EstructuraFuncional>'
        '<EstructuraFuncional tipoParte="articulo" idParte="3"><Texto>Artículo 25 quinquies.- final</Texto></EstructuraFuncional>'
        '</Norma>'
    )
    cliente = BCNClient(cache_dir=str(tmp_path))
    datos = cliente._parse_norma_xml(xml)
    assert set(datos["articulos"]) == {"25", "25 quáter", "25 quinquies"}, datos["articulos"]


def test_get_articulo_ley_encuentra_el_sufijo_con_o_sin_tilde(monkeypatch, tmp_path):
    cliente = BCNClient(cache_dir=str(tmp_path))
    monkeypatch.setattr(cliente, "get_ley", lambda id_ley, use_cache=True: {
        "normaId": 1, "numero": id_ley, "titulo": "Ley de prueba", "fechaVersion": "2026-01-01",
        "articulos": {
            "25": "Artículo 25.- regla general",
            "25 quáter": "Artículo 25 quáter.- regla intermedia",
            "25 quinquies": "Artículo 25 quinquies.- revisión extraordinaria",
        },
    })
    assert cliente.get_articulo_ley(9999, "25 quinquies")["texto"].startswith("Artículo 25 quinquies")
    assert cliente.get_articulo_ley(9999, "25 quater")["texto"].startswith("Artículo 25 quáter")
    assert cliente.get_articulo_ley(9999, "25")["texto"].startswith("Artículo 25.-")


def test_las_copias_de_parseo_van_a_la_version_2(tmp_path):
    """La copia envenenada (quáter bajo la clave «25») no se reutiliza: nombres nuevos."""
    cliente = BCNClient(cache_dir=str(tmp_path))
    assert cliente._get_cache_path("ley", 19300).endswith("ley_p2_19300.json")
    assert cliente._get_cache_path("norma", 242302).endswith("norma_p2_242302.json")
    assert cliente._get_cache_path("versiones", 123).endswith("versiones_123.json")


# ── 3. Integración con cita_texto (lote) ───────────────────────────────────────

class _BCNFalso:
    def get_ley(self, id_ley, use_cache=True):
        return {"normaId": 1, "numero": id_ley, "titulo": f"Ley {id_ley}", "articulos": {}}

    def get_articulo_ley(self, id_ley, articulo):
        return {"ley": id_ley, "articulo": articulo,
                "texto": f"Artículo {articulo} de la Ley {id_ley}."}

    def get_codigo(self, codigo, articulo=None):
        if articulo is None:
            return {"codigo": codigo, "articulos": {}}
        return {"codigo": codigo, "articulo": articulo,
                "texto": f"Artículo {articulo} del {codigo}."}


def test_cita_texto_lote_con_sufijos_y_normas_especiales(monkeypatch):
    monkeypatch.setattr(mcp_server, "_bcn_para_citas", lambda: _BCNFalso())
    res = mcp_server.handle_tool_call("cita_texto", {"referencias": [
        "Ley 19.300 art. 25 quinquies",
        "Constitución Política art. 20",
        "Código Sanitario art. 67",
    ]})
    assert res["faltantes"] == [], res
    formatos = [c["formato"] for c in res["citas"]]
    assert "[BCN - Ley N° 19300, Art. 25 quinquies]" in formatos, formatos
    assert "[BCN - Constitución Política de la República, Art. 20]" in formatos, formatos
    assert "[BCN - Código Sanitario, Art. 67]" in formatos, formatos
