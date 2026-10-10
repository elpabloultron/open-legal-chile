"""Extractores del mapa del corpus: una fila por archivo del dataset, con su ID canónico.

Los fixtures son archivos reales del dataset, recortados: una sentencia del TC cuya cabecera es de
otra causa, una ficha del 1TA sin texto, un artículo de la REHJ con YAML y fichas de la CS en .md
y en el índice JSONL. Los casos sintéticos cubren formas medidas en el dataset (coma de ancho
completo, causas acumuladas, síntesis, fechas en palabras, listas JSON en línea).
"""

import json
from pathlib import Path

import pytest

from mapa_corpus import extractores, inventario, particiones

FX = Path(__file__).parent / "fixtures" / "mapa"


def _extraer(ruta, contenido):
    datos = contenido.encode("utf-8") if isinstance(contenido, str) else contenido
    return extractores.extraer(ruta, datos, inventario.blob_git(datos))


# ── Tribunal Constitucional ───────────────────────────────────────────────────────────────────
def test_tc_identidad_por_el_cuerpo_y_no_por_la_cabecera():
    """El archivo se llama 15907-06a-INA, pero el fallo que trae es el Rol 13.139-22-INA (su
    documento oficial es extended/13139): la identidad es la del cuerpo y la cabecera queda como dato."""
    fila = _extraer("jurisprudencia_tc/15907-06a-INA.md", (FX / "delta" / "tc_15907-06a-INA.md").read_bytes())
    assert fila["id"] == "tc:13139" and fila["col"] == "tc"
    assert fila["cabecera"]["rol"] == "15907-06a-INA"
    assert "cabecera_desalineada" in fila["calidad"]
    assert "norma:cpr:93:n6" in dict(fila["normas"])          # la fórmula final de inaplicabilidad
    assert "tc:15907" not in fila.get("cita_tc", [])           # ninguna cita hacia la cabecera
    # La de la resolución («Santiago, seis de mayo de dos mil veintidós»), no la de presentación
    # del requerimiento («con fecha 7 de abril de 2022»), que es la primera fecha en cifras.
    assert fila["fecha"] == "2022-05-06"


def _md_tc(rol, fecha, cuerpo):
    numero = rol.split("-")[0]
    return (f"# INA-Inadmisibilidad — Rol N° {rol}\n\n- **Rol:** Rol N° {rol}\n- **Fecha:** {fecha}\n"
            f"- **Documento oficial:** https://buscador-backend.tcchile.cl/api/extended/{numero}/download\n\n---\n\n{cuerpo}")


def test_tc_el_encabezado_de_las_sentencias_identifica_la_causa():
    """«Sentencia Rol 9231-2020» (sin «N°») es el rol propio: identidad por el cuerpo, no por el enlace."""
    fila = _extraer("jurisprudencia_tc/9231-06a-INA.md",
                    _md_tc("9231-06a-INA", "2021-07-08", "Sentencia Rol 9231-2020 [8 de julio de 2021] VISTOS: …"))
    assert fila["id"] == "tc:9231" and not fila.get("calidad") and fila["fecha"] == "2021-07-08"


def test_tc_una_resolucion_que_cita_otro_rol_antes_del_suyo_no_queda_desalineada():
    """Las inadmisibilidades nombran su rol solo al pie; antes pueden citar un precedente."""
    cuerpo = ("Santiago, veintinueve de octubre de dos mil veinticuatro. VISTOS: con fecha 2 de septiembre de "
              "2024 se presentó un requerimiento; como resolvió la STC Rol N° 8536-20-INA, " + "considerando. " * 400
              + "SE DECLARA INADMISIBLE. Rol N° 15.068-24-INA.")
    fila = _extraer("jurisprudencia_tc/15068-06b-INA.md", _md_tc("15068-06b-INA", "2024-10-29", cuerpo))
    assert fila["id"] == "tc:15068" and not fila.get("calidad")
    assert fila["fecha"] == "2024-10-29"                    # la de la resolución, no la de presentación


def test_basura_de_prueba_del_scraper_no_se_inventaria():
    assert inventario.excluido("jurisprudencia_tc/testrol2-34566.md")
    assert not inventario.excluido("jurisprudencia_tc/2402-12-INA.md")


# ── Tribunales ambientales ────────────────────────────────────────────────────────────────────
def test_ta_ficha_sin_texto():
    fila = _extraer("jurisprudencia_ambiental/1TA/D-25-2023.md", (FX / "delta" / "ta_1TA_D-25-2023.md").read_bytes())
    assert fila["id"] == "ta:1ta:d-25-2023" and fila["tribunal"] == "organo:1ta"
    assert fila["fecha"] == "2025-07-31"                        # «31/07/2025»
    assert fila["redactor"] == "ministro:sandra-alvarez-torres"
    assert "ministro:marcelo-hernandez-rojas" in fila["ministros"]
    assert fila["tiene_texto"] is False and "normas" not in fila


FICHA_3TA = """# Reclamación — R-21-2021

- **Tribunal:** Tercer Tribunal Ambiental
- **Rol:** R-21-2021，R-35-2021
- **Fecha:** 4 de marzo de 2024
- **Carátula:** "Comunidad Indígena con SMA" Síntesis de la sentencia
- **Integración:** Javier Millar Silva, Sibel Villalobos Volpi

---
{cuerpo}
"""


def test_ta_acumuladas_coma_de_ancho_completo_y_fecha_en_palabras():
    cuerpo = ("VISTOS: la reclamación del artículo 17 N° 3 de la Ley N° 20.600 contra la resolución "
              "dictada conforme al artículo 35 de la LOSMA. " * 30)
    fila = _extraer("jurisprudencia_ambiental/3TA/R-21-2021.md", FICHA_3TA.format(cuerpo=cuerpo))
    assert fila["id"] == "ta:3ta:r-21-2021"
    assert fila["acumuladas"] == ["ta:3ta:r-35-2021"]
    assert fila["fecha"] == "2024-03-04"
    assert fila["titulo"] == "Comunidad Indígena con SMA"   # la síntesis pegada a la carátula se corta
    assert fila["tiene_texto"] is True
    normas = dict(fila["normas"])
    assert "norma:ley-20600:17:n3" in normas and "norma:losma:35" in normas


def test_ta_sintesis_lleva_su_tipo():
    fila = _extraer("jurisprudencia_ambiental/3TA/Descargar_S_ntesis_R-21-2021.md",
                    FICHA_3TA.format(cuerpo="breve"))
    assert fila["tipo"] == "sintesis" and fila["id"] == "ta:3ta:r-21-2021"


# ── Corte Suprema ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("rol, archivo, ruta", [
    ("29834-2024", "cs_29834-2024.md", "jurisprudencia_cs/2024/05/29834-2024.md"),
    ("49772-2024", "cs_49772-2024.md", "jurisprudencia_cs/2024/07/49772-2024.md"),
])
def test_cs_ficha_md_y_fila_del_indice_dan_lo_mismo(rol, archivo, ruta):
    """La fila sale del índice JSONL o, si una ficha no está en él, del .md: deben coincidir
    («—» es vacío en ambos). Solo el índice trae `documento_id`."""
    indice = {json.loads(linea)["rol"]: json.loads(linea)
              for linea in (FX / "extractores" / "cs_indice_2anios.jsonl").read_text(encoding="utf-8").splitlines()}
    md = extractores.fila_cs(extractores.registro_desde_md_cs((FX / "extractores" / archivo).read_text(encoding="utf-8")),
                             ruta, "b" * 40, 1)
    js = extractores.fila_cs(indice[rol], ruta, "b" * 40, 1)
    js.pop("documento_id", None)
    assert md == js
    assert md["id"] == f"cs:{rol}"


def test_cs_salas_y_ministros():
    indice = [json.loads(linea) for linea in (FX / "extractores" / "cs_indice_2anios.jsonl").read_text(encoding="utf-8").splitlines()]
    filas = {f["id"]: f for f in (extractores.fila_cs(r, "x", "b" * 40, 1) for r in indice)}
    assert filas["cs:29834-2024"]["sala"] == "sala:cs-3"
    assert filas["cs:49772-2024"]["sala"] == "sala:cs-pleno"       # «TRIBUNAL PLENO»
    assert "ministro:jean-pierre-matus-acuna" in filas["cs:29834-2024"]["ministros"]
    assert "ministros" not in filas["cs:49772-2024"]                # «—»: sin integración informada


# ── Doctrina y revistas ───────────────────────────────────────────────────────────────────────
def test_revista_con_yaml():
    ruta = "doctrina/revistas/rehj/2015/rehj_2015_n37_791_una_fuente.md"
    fila = _extraer(ruta, (FX / "delta" / "rev_rehj_2015_n37_791.md").read_bytes())
    assert fila["id"] == "doc:revistas/rehj/2015/rehj_2015_n37_791_una_fuente"
    assert fila["revista"] == "revista:rehj" and fila["sub"] == "revista"
    assert fila["autores"] == ["autor:barrientos_grandon_javier"]
    assert fila["anio"] == 2015 and fila["cita"].startswith("[REHJ - N° 37 (2015)")


REVISTA_JSON_EN_LINEA = """---
titulo: "Daño moral contractual"
autores: ["Ana Pérez Soto", "Comité Editorial"]
revista: "Revista Chilena de Derecho Privado"
anio: 2019
cita_canonica: "[RChDP - N° 32 (2019), Ana Pérez Soto, Daño moral contractual]"
normas_citadas: ["[BCN - Código Civil, Art. 1556]", "[CPR 1980 - Art. 19]"]
---

# Daño moral contractual

> Texto íntegro disponible en el sitio de la revista.
"""


def test_revista_listas_json_en_linea_y_solo_ficha():
    fila = _extraer("doctrina/revistas/rchdp/2019/perez_dano_moral.md", REVISTA_JSON_EN_LINEA)
    assert fila["autores"] == ["autor:ana_perez_soto"]               # «Comité Editorial» no es persona
    assert fila["cita"].startswith("[RChDP - N° 32 (2019)")          # cita_canonica en vez de cita_oficial
    assert set(dict(fila["normas"])) == {"norma:cc:1556", "norma:cpr:19"}
    assert fila["tiene_texto"] is False


def test_doctrina_con_espacios_en_la_ruta_da_un_id_sin_espacios():
    fila = _extraer("doctrina/apuntes_orrego/Contrato de Arrendamiento.md", "# Contrato de arrendamiento\n\nTexto.")
    assert fila["id"] == "doc:apuntes_orrego/Contrato_de_Arrendamiento"
    assert fila["ruta"] == "doctrina/apuntes_orrego/Contrato de Arrendamiento.md"


# ── Solo inventario y particiones ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ruta, esperado", [
    ("README.md", ("arch", "arch")),
    ("jurisprudencia_tc/README.md", ("arch", "arch")),
    ("data/catalogo/indice_agentes.json", ("dato", "dato")),
    ("graphify/GRAPH_REPORT.md", ("graphify", "graphify")),
    ("llms.txt", ("arch", "arch")),
    ("jurisprudencia_tc/2402-12-INA.md", None),
    ("doctrina/civil/obra.md", None),
])
def test_solo_inventario(ruta, esperado):
    assert extractores.solo_inventario(ruta) == esperado


@pytest.mark.parametrize("ruta, particion", [
    ("jurisprudencia_cs/2024/03/10641-2024.md", "entradas/cs-2024"),
    ("jurisprudencia_cs/README.md", "entradas/cs-indices"),
    ("jurisprudencia_tc/2402-12-INA.md", "entradas/tc"),
    ("jurisprudencia_ambiental/3TA/R-21-2021.md", "entradas/ta-3ta"),
    ("jurisprudencia_ambiental/anuarios/x.md", "entradas/ta-otros"),
    ("doctrina/revistas/rchd/2020/x.md", "entradas/doc-rev-rchd"),
    ("doctrina/civil/obra.md", "entradas/doc-civil"),
    ("guias_academia_judicial/guia.md", "entradas/guias"),
    ("biblioteca_ambiental/libro.md", "entradas/amb-biblioteca"),
    ("publicaciones_ambientales/boletin.md", "entradas/amb-publicaciones"),
    ("data/catalogo/x.json", "entradas/datos"),
    ("graphify/x.json", "entradas/graphify"),
    ("llms.txt", "entradas/raiz"),
])
def test_particion_de(ruta, particion):
    assert particiones.particion_de(ruta) == particion


def test_extraccion_determinista_y_sin_claves_vacias():
    datos = (FX / "delta" / "tc_15907-06a-INA.md").read_bytes()
    a = _extraer("jurisprudencia_tc/15907-06a-INA.md", datos)
    b = _extraer("jurisprudencia_tc/15907-06a-INA.md", datos)
    assert particiones.linea(a) == particiones.linea(b)
    assert all(v not in (None, "", [], {}) for v in a.values())
