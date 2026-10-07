"""
Pruebas unitarias para el parser XML de la Biblioteca del Congreso Nacional (BCN).
Valida que la extracción de metadatos, artículos y estructuras funcionales funcione con precisión.

Frente 0 (2026-10-07): el parser pisaba artículos homónimos. Medido sobre la caché real, 8 normas
tenían claves pisadas (Código Civil 86, Comercio 258, CPR 35, Trabajo 32, Ley 18.700 26, Penal 12,
CPP 4, CPC 1) y `cita_texto("Código Civil art. 1")` entregaba un artículo de la Ley 16.271. Cada
prueba de abajo fija un patrón de esos casos con un XML mínimo; la última sección verifica los
casos reales contra la caché local y se salta si no existe.
"""

import glob
import json
import os
import shutil
import time
from xml.sax.saxutils import escape

import pytest

import bcn_connector
from bcn_connector import BCNClient, _resolver_articulo, _segmentar_articulos

SAMPLE_XML_LEY = """<?xml version="1.0" encoding="UTF-8"?>
<Norma normaId="1200096" fechaVersion="2025-01-03" derogado="no derogado">
  <Identificador fechaPromulgacion="2024-01-05" fechaPublicacion="2024-01-15">
    <TiposNumeros>
      <TipoNumero>
        <Numero>21643</Numero>
      </TipoNumero>
    </TiposNumeros>
    <Organismos>
      <Organismo>MINISTERIO DEL TRABAJO Y PREVISIÓN SOCIAL</Organismo>
    </Organismos>
  </Identificador>
  <Metadatos>
    <TituloNorma>MODIFICA EL CÓDIGO DEL TRABAJO EN MATERIA DE PREVENCIÓN, INVESTIGACIÓN Y SANCIÓN DEL ACOSO LABORAL, SEXUAL O DE VIOLENCIA EN EL TRABAJO</TituloNorma>
  </Metadatos>
  <EstructurasFuncionales>
    <EstructuraFuncional tipoParte="Artículo" idParte="1">
      <Texto>Artículo 1.- Modifícase el Código del Trabajo en los términos siguientes: 1. En el artículo 2...</Texto>
    </EstructuraFuncional>
    <EstructuraFuncional tipoParte="Artículo" idParte="2">
      <Texto>Artículo 2.- La presente ley entrará en vigencia el primer día del mes siguiente a su publicación.</Texto>
    </EstructuraFuncional>
  </EstructurasFuncionales>
</Norma>
"""


def _cliente(tmp_path):
    return BCNClient(cache_dir=str(tmp_path))


def test_parse_norma_xml(tmp_path):
    client = _cliente(tmp_path)
    parsed = client._parse_norma_xml(SAMPLE_XML_LEY)

    assert parsed["normaId"] == "1200096"
    assert parsed["numero"] == "21643"
    assert "ACOSO LABORAL" in parsed["titulo"]
    assert "MINISTERIO DEL TRABAJO" in parsed["organismo"]
    assert parsed["fechaVersion"] == "2025-01-03"
    assert parsed["totalEstructuras"] == 2
    assert "1" in parsed["articulos"]
    assert "2" in parsed["articulos"]
    assert "Artículo 1" in parsed["articulos"]["1"]
    assert "Artículo 2" in parsed["articulos"]["2"]


# ── Fixtures mínimos ────────────────────────────────────────────────────────────

def _xml(partes):
    """XML mínimo de una norma a partir de [(tipoParte, texto), ...]."""
    cuerpo = "".join(
        f'<EstructuraFuncional tipoParte="{escape(tipo)}" idParte="{i}"><Texto>{escape(texto)}</Texto>'
        "</EstructuraFuncional>"
        for i, (tipo, texto) in enumerate(partes, 1)
    )
    return ('<Norma normaId="1" fechaVersion="2026-01-01" derogado="no derogado">'
            "<Metadatos><TituloNorma>Norma de prueba</TituloNorma></Metadatos>"
            f"<EstructurasFuncionales>{cuerpo}</EstructurasFuncionales></Norma>")


def _parsear(tmp_path, partes):
    return _cliente(tmp_path)._parse_norma_xml(_xml(partes))


# Un DFL que refunde un código y trae una ley anexa (el patrón del Código Civil: DFL 1/2000).
DFL_CON_ANEXA = [
    ("Artículo", "Artículo 1º.- Déjase sin efecto el D.F.L. Nº 1 del año anterior."),
    ("Artículo", "Artículo 2º.- Fíjase el siguiente texto refundido, coordinado y sistematizado del Código Civil:"),
    ("Doble Articulado", ""),
    ("Título", "TITULO PRELIMINAR"),
    ("Enumeración", "§ 1. De la ley"),
    ("Artículo", "Artículo 1º. La ley es una declaración de la voluntad soberana que, manifestada en la forma prescrita por la Constitución, manda, prohíbe o permite."),
    ("Artículo", "Art. 2º. La costumbre no constituye derecho sino en los casos en que la ley se remite a ella."),
    ("Artículo", "Art. 3º. Sólo toca al legislador explicar o interpretar la ley de un modo generalmente obligatorio."),
    ("Artículo", "Art. 4. Las disposiciones contenidas en los Códigos de Comercio, de Minería y otros."),
    ("Artículo", "Artículo final. El presente Código comenzará a regir desde el 1.º de enero de 1857."),
    ("Artículo", "ARTICULO 3º: Fíjase el siguiente texto refundido, coordinado y sistematizado de la Ley Nº 4.808."),
    ("Doble Articulado", ""),
    ("Título", "Título I\n     DISPOSICIONES GENERALES"),
    ("Artículo", "Artículo 1.º Las inscripciones de los nacimientos, matrimonios y defunciones se harán en el Registro Civil."),
    ("Artículo", "Art. 2.º El Registro Civil se llevará por duplicado."),
    ("Artículo", "Art. 3.º En el libro de los nacimientos se inscribirán los nacimientos."),
    ("Artículo", "L. 9.382\n      Art. 21. Si se extraviaren o destruyeren uno o ambos libros."),
]


def test_dfl_con_ley_anexa_no_pisa_el_codigo(tmp_path):
    """Art. 1 del Código Civil es «La ley es una declaración…», no el de la Ley 4.808."""
    datos = _parsear(tmp_path, DFL_CON_ANEXA)

    assert datos["articulos"]["1"].startswith("Artículo 1º. La ley es una declaración de la voluntad soberana")
    assert datos["articulos"]["3"].startswith("Art. 3º. Sólo toca al legislador")
    assert set(datos["articulos"]) == {"1", "2", "3", "4", "final"}

    # El DFL y la ley anexa no se pierden: quedan en sus cuerpos, con su rango, sin pisar nada.
    anexos = {(a["desde"], a["hasta"]): a for a in datos["cuerpos_anexos"]}
    assert ("1", "2") in anexos, "los artículos 1 y 2 del propio DFL"
    ley_4808 = next(a for a in datos["cuerpos_anexos"] if "Las inscripciones" in a["articulos"].get("1", ""))
    assert ley_4808["articulos"]["2"].startswith("Art. 2.º El Registro Civil")
    assert ley_4808["articulos"]["21"].startswith("L. 9.382"), "la leyenda de modificación no oculta el artículo 21"
    assert datos["cuerpo_principal"]["total"] == 5
    assert datos["diagnostico_articulos"]["colisiones"] == []


def test_la_numeracion_que_retrocede_abre_un_cuerpo_nuevo_sin_marcador(tmp_path):
    """Sin «Doble Articulado» de por medio, el retroceso 3 → 1 también separa las leyes."""
    partes = [("Artículo", f"Artículo {n}.- texto del código {n}") for n in range(1, 8)]
    partes += [("Artículo", f"Artículo {n}.- texto de la ley anexa {n}") for n in (1, 2)]
    datos = _parsear(tmp_path, partes)

    assert datos["articulos"]["1"] == "Artículo 1.- texto del código 1"
    assert len(datos["articulos"]) == 7
    assert datos["cuerpos_anexos"][0]["articulos"]["2"] == "Artículo 2.- texto de la ley anexa 2"


def test_solo_la_estructura_articulo_entra_al_mapa_principal(tmp_path):
    """Un encabezado de Párrafo que menciona un artículo no es ese artículo (CPP art. 58)."""
    datos = _parsear(tmp_path, [
        ("Párrafo", "Párrafo 1º\nDe la responsabilidad conforme al artículo 58 de la Constitución"),
        ("Enumeración", "Artículo 59 de la ley. Rótulo suelto"),
        ("Artículo", "Artículo 58.- Responsabilidad penal. La acción penal no puede entablarse sino contra el imputado."),
    ])
    assert list(datos["articulos"]) == ["58"]
    assert datos["articulos"]["58"].startswith("Artículo 58.- Responsabilidad penal")


def test_la_cabecera_se_ancla_al_inicio_del_texto(tmp_path):
    """Un artículo que MENCIONA otro («el artículo 19») no se guarda bajo ese número."""
    datos = _parsear(tmp_path, [
        ("Artículo", "Artículo 19.- La Constitución asegura a todas las personas: 1º.- El derecho a la vida."),
        ("Artículo", "Artículo 20.- El que por causa de actos u omisiones arbitrarios o ilegales sufra privación, conforme al artículo 19, podrá ocurrir."),
        ("Disposición Transitoria", "DISPOSICIONES TRANSITORIAS"),
        ("Disposición Transitoria", "VIGESIMA PRIMERA.- La reforma introducida en el numeral 10º del artículo 19, que establece la obligatoriedad de la educación media."),
    ])
    assert datos["articulos"]["19"].startswith("Artículo 19.- La Constitución asegura")
    assert set(datos["articulos"]) == {"19", "20"}


def test_transitorias_de_la_constitucion_van_aparte(tmp_path):
    datos = _parsear(tmp_path, [
        ("Artículo", "Artículo 1°.- Las personas nacen libres e iguales en dignidad y derechos."),
        ("Disposición Transitoria", "DISPOSICIONES TRANSITORIAS"),
        ("Disposición Transitoria", "PRIMERA.- Mientras se dictan las disposiciones que den cumplimiento a lo prescrito en el artículo 1°..."),
        ("Disposición Transitoria", "VIGESIMA PRIMERA.- La reforma introducida en el numeral 10º del artículo 19."),
        ("Disposición Transitoria", "DECIMOCTAVA.- Las modificaciones dispuestas en el artículo 5°."),
        ("Disposición Transitoria", "Ley 21257\n     CUADRAGÉSIMA PRIMERA. Regla especial."),
    ])
    assert list(datos["articulos"]) == ["1"]
    assert list(datos["articulos_transitorios"]) == [
        "primera", "vigesima primera", "decimoctava", "cuadragésima primera"]
    # Se piden diciendo que son transitorias, con o sin género ni espacio.
    for pedido, esperado in (("primera transitoria", "primera"), ("Vigésimo primero transitorio", "vigesima primera"),
                             ("décimo octava transitoria", "decimoctava")):
        hallazgo, _ = _resolver_articulo(datos, pedido)
        assert hallazgo and hallazgo[0] == esperado and hallazgo[2]["transitorio"] is True, pedido


def test_articulos_transitorios_de_una_ley_con_encabezado_de_seccion(tmp_path):
    """«ARTICULOS TRANSITORIOS» + «Art. 1o» no pisa al artículo 1 del código (CT art. 1)."""
    datos = _parsear(tmp_path, [
        ("Título", "TITULO PRELIMINAR"),
        ("Artículo", "Artículo 1.o Las relaciones laborales entre los empleadores y los trabajadores se regularán por este Código."),
        ("Artículo", "Art.2.o Reconócese la función social que cumple el trabajo."),
        ("Artículo", "Art. 519.- La Dirección del Trabajo podrá hacerse parte."),
        ("Artículo Transitorio", "ARTICULOS TRANSITORIOS"),
        ("Artículo", "Art. 1o Las disposiciones de este Código no alteran las normas y regímenes generales."),
        ("Artículo", "Art. 2o Los trabajadores con contrato vigente al 15 de junio de 1978."),
    ])
    assert datos["articulos"]["1"].startswith("Artículo 1.o Las relaciones laborales")
    assert datos["articulos"]["2"].startswith("Art.2.o Reconócese")
    assert datos["articulos_transitorios"]["1"].startswith("Art. 1o Las disposiciones de este Código")
    assert "ARTICULOS TRANSITORIOS" not in datos["articulos_transitorios"].values()


def test_secciones_de_transitorios_con_otros_rotulos(tmp_path):
    """«Título … Disposiciones Transitorias», «Artículos Transitorios» (párrafo) y «Artículo 1º transitorio»."""
    for rotulo_tipo, rotulo in (("Título", "DISPOSICIONES TRANSITORIAS"),
                                ("Título", "TITULO XII\n               Disposiciones Transitorias"),
                                ("Párrafo", "Artículos Transitorios"),
                                ("Título", "ARTÍCULOS TRANSITORIOS")):
        datos = _parsear(tmp_path, [
            ("Artículo", "Artículo 1.- Regla permanente."),
            ("Artículo", "Artículo 2.- Otra regla permanente."),
            (rotulo_tipo, rotulo),
            ("Artículo", "Artículo primero.- Entrada en vigencia."),
            ("Artículo", "Artículo segundo.- Plazo para reglamentos."),
        ])
        assert set(datos["articulos"]) == {"1", "2"}, rotulo
        assert set(datos["articulos_transitorios"]) == {"primero", "segundo"}, rotulo

    datos = _parsear(tmp_path, [
        ("Artículo", "Artículo 1.- Regla permanente."),
        ("Artículo", "Artículo 1º transitorio.- Plazo."),
        ("Artículo", "Artículo transitorio.- El mayor gasto se financiará con cargo al presupuesto."),
    ])
    assert set(datos["articulos"]) == {"1"}
    assert set(datos["articulos_transitorios"]) == {"1", "transitorio"}


def test_un_encabezado_de_servicios_transitorios_no_abre_la_seccion(tmp_path):
    """«Del contrato de servicios transitorios» (Código del Trabajo) no es una sección de transitorios."""
    datos = _parsear(tmp_path, [
        ("Título", "Título VII\nDel trabajo en empresas de servicios transitorios"),
        ("Artículo", "Artículo 183-F.- Para los fines de este Código, se entiende por empresa de servicios transitorios."),
        ("Artículo", "Artículo 183-G.- Otra regla."),
    ])
    assert set(datos["articulos"]) == {"183-f", "183-g"}
    assert datos["articulos_transitorios"] == {}


def test_ordinal_y_sufijos_latinos(tmp_path):
    """CPC: «Artículo 3º bis» (el ordinal «º» no rompe el sufijo) y «Artículo 25 Terminado» no es «25 ter»."""
    datos = _parsear(tmp_path, [
        ("Artículo", "Art. 3° Se aplicará el procedimiento ordinario en todas las gestiones."),
        ("Artículo", "Artículo 3º bis.- Es deber de los abogados y de los jueces actuar con lealtad."),
        ("Artículo", "Artículo 25 Terminado el plazo, el tribunal dictará resolución."),
        ("Artículo", "Artículo 26 quáter.- Regla intermedia."),
        ("Artículo", "ART. 27 BIS.- Regla en mayúsculas."),
        ("Artículo", "Artículo 28 ter.- Regla."),
    ])
    assert set(datos["articulos"]) == {"3", "3 bis", "25", "26 quáter", "27 bis", "28 ter"}
    assert datos["articulos"]["3"].startswith("Art. 3° Se aplicará")
    assert datos["articulos"]["3 bis"].startswith("Artículo 3º bis.- Es deber")


def test_sufijos_de_letra(tmp_path):
    """CT: 183-A no es 183-AE; Ley 19.496: el artículo 16 no es el 16 B; «12 A los efectos» no es «12 A»."""
    datos = _parsear(tmp_path, [
        ("Artículo", "Artículo 16.- No producirán efecto alguno en los contratos de adhesión las cláusulas."),
        ("Artículo", "Artículo 16 A.- Regla A."),
        ("Artículo", "Artículo 16 B. El procedimiento a que se sujetará la tramitación de las acciones."),
        ("Artículo", "Artículo 17 A los efectos de esta ley se entenderá por consumidor."),
        ("Artículo", "Artículo 152 quáter O bis.- El empleador deberá ofrecer a la persona trabajadora."),
        ("Artículo", "ART. 161 - A.\n    Se castigará con la pena de reclusión menor."),
        ("Artículo", "Artículo 183-A.- Es trabajo en régimen de subcontratación."),
        ("Artículo", "Artículo 183-AE.- Las trabajadoras contratadas bajo el régimen contemplado en este Párrafo."),
        ("Artículo", "Artículo 183-Ñ.- Podrá celebrarse un contrato de puesta a disposición."),
        ("Artículo", "Artículo 211-B bis.- En caso de acoso sexual."),
        ("Artículo", "Artículo 248- Cierre de la investigación. Practicadas las diligencias."),
        ("Artículo", "Artículo 249 .- Con espacio antes del punto."),
        ("Artículo", "ART. 319 a).     Derogado."),
        ("Artículo", "Artículo 548-2. Los estatutos de las personas jurídicas."),
    ])
    llaves = set(datos["articulos"])
    assert llaves == {"16", "16 a", "16 b", "17", "183-a", "183-ae", "183-ñ", "211-b bis", "248", "249",
                      "548-2", "152 quáter o bis", "161-a", "319 a"}
    assert datos["articulos"]["16"].startswith("Artículo 16.- No producirán")
    assert datos["articulos"]["183-a"].startswith("Artículo 183-A.-")
    assert datos["articulos"]["183-ae"].startswith("Artículo 183-AE.-")
    assert datos["articulos"]["17"].startswith("Artículo 17 A los efectos")


@pytest.mark.parametrize("texto, clave", [
    ("Artículo 183 -A.- Con espacio antes del guion.", "183-a"),
    ("Artículo 183- A.- Con espacio después del guion.", "183-a"),
    ("Artículo 25 Terminado el plazo, el tribunal resolverá.", "25"),
    ("Artículo 10 A partir de la fecha, rige esta regla.", "10"),
    ("Artículo 248- Un juez conocerá del asunto.", "248"),
    ("Art. 2.º Será juez competente.", "2"),
    ("Art.2.o Reconócese la función social.", "2"),
    ("Artículo 6º ter.- Regla.", "6 ter"),
    ("Artículo 21° BIS.- Derogado.", "21 bis"),
    ("ART. 32. BIS\n\n     La imposición del presidio perpetuo calificado.", "32 bis"),
    ("ART. 250 bis A. Derogado", "250 bis a"),
    ("Artículo 54 Ñ.- La comparecencia de los proveedores.", "54 ñ"),
    ("Art. 5° (6°). Si durante el juicio fallece alguna de las partes.", "5"),
    ("Art. 446. (468). Aunque pague el deudor antes del requerimiento.", "446"),
    ("Artículo 1792-14. El patrimonio final resultará de deducir.", "1792-14"),
    ("DEROGADO\n    ARTICULO 5º: Derógase la ley Nº 17.999.", "5"),
])
def test_cabecera_formas_de_escritura(texto, clave):
    cab = bcn_connector._cabecera(texto)
    assert cab is not None and cab["clave"] == clave, (texto, cab)


@pytest.mark.parametrize("texto", [
    "Que aprueba el Código de Procedimiento Civil",
    "el artículo 19 de la Constitución dispone",
    "Párrafo 1º artículo 58",
    "Artículos 1 y 2 de esta ley",
    "",
])
def test_lo_que_no_es_cabecera_no_se_lee_como_articulo(texto):
    assert bcn_connector._cabecera(texto) is None


def test_palabras_ordinales_unico_y_final(tmp_path):
    datos = _parsear(tmp_path, [
        ("Artículo", "Artículo primero.- Apruébase el reglamento."),
        ("Artículo", "ARTICULO UNICO._ Declárase feriado el día 12 de octubre."),
        ("Artículo", "Artículo Décimo Tercero.- Cambio de denominación."),
        ("Artículo", "Artículo final. El presente texto comenzará a regir."),
    ])
    assert set(datos["articulos"]) == {"primero", "unico", "décimo tercero", "final"}
    for pedido, esperado in (("decimotercero", "décimo tercero"), ("Artículo único", "unico"),
                             ("primer", "primero")):
        hallazgo, _ = _resolver_articulo(datos, pedido)
        assert hallazgo and hallazgo[0] == esperado, pedido

    # «Artículo Final» como rótulo suelto seguido del artículo real (Ley 19.039): manda el real.
    datos = _parsear(tmp_path, [
        ("Artículo", "Artículo 113.- Podrán solicitarse como medidas prejudiciales."),
        ("Artículo", "Artículo Final\n\n    Artículo 114.- Derógase el decreto ley N° 958."),
    ])
    assert set(datos["articulos"]) == {"113", "114"}
    assert datos["articulos"]["114"].startswith("Artículo Final")


def test_cabecera_con_comillas_sin_punto_y_caracter_danado(tmp_path):
    datos = _parsear(tmp_path, [
        ("Artículo", '"Artículo 1.- Modifícase el Código del Trabajo de la siguiente forma:'),
        ("Artículo", "Art. 10 (11). Todo procurador legalmente constituido conservará su carácter."),
        ("Artículo", "Art\ufffdculo 78.- Vencido un plazo judicial para la realización de un acto procesal."),
        ("Artículo", "Art 531. Siniestro. Presunción de cobertura y excepciones."),
        ("Artículo", "Que aprueba el Código de Procedimiento Civil\n    Por cuanto el Congreso Nacional ha dado su aprobación."),
    ])
    assert set(datos["articulos"]) == {"1", "531", "78", "10"}
    assert datos["diagnostico_articulos"]["sin_cabecera"] == 1, "el preámbulo de aprobación no es un artículo"


def test_ley_aprobatoria_con_el_texto_aprobado_adentro(tmp_path):
    """Ley 20.393: «Artículo Primero» aprueba un texto con artículos 1° a N; «Segundo» y «Tercero» siguen fuera."""
    partes = [("Artículo", "Artículo Primero.- Apruébase la siguiente ley sobre responsabilidad penal."),
              ("Doble Articulado", "")]
    partes += [("Artículo", f"Artículo {n}°.- Regla {n} del texto aprobado.") for n in range(1, 9)]
    partes += [("Artículo", "Artículo Segundo.- Introdúcese una modificación al Código Penal."),
               ("Artículo", "Artículo Tercero.- Introdúcese una modificación a la ley Nº 19.913.")]
    datos = _parsear(tmp_path, partes)

    assert set(datos["articulos"]) == {str(n) for n in range(1, 9)}
    hallazgo, _ = _resolver_articulo(datos, "Artículo segundo")
    assert hallazgo and hallazgo[1].startswith("Artículo Segundo") and hallazgo[2]["cuerpo"] == "anexo"
    hallazgo, _ = _resolver_articulo(datos, "primero")
    assert hallazgo and hallazgo[1].startswith("Artículo Primero.- Apruébase")


def test_ley_exterior_que_vuelve_tras_transitorios_numerados(tmp_path):
    """Ley 20.285: tras los transitorios del texto aprobado vuelven «Artículo segundo» … de la ley exterior."""
    partes = [("Artículo", "Artículo primero.- Apruébase la siguiente ley de transparencia."),
              ("Doble Articulado", "")]
    partes += [("Artículo", f"Artículo {n}.- Regla {n}.") for n in range(1, 6)]
    partes += [("Título", "TÍTULO VII\n\n           Disposiciones Transitorias"),
               ("Artículo", "Artículo 1°.- De conformidad a la disposición cuarta transitoria."),
               ("Artículo", "Artículo 2º.- La primera designación de consejeros."),
               ("Artículo", "Artículo segundo.- Introdúcense modificaciones a la Ley Orgánica."),
               ("Artículo", "Artículo tercero.- Reemplázase el inciso segundo del artículo 16.")]
    datos = _parsear(tmp_path, partes)

    assert set(datos["articulos"]) == {"1", "2", "3", "4", "5"}
    assert set(datos["articulos_transitorios"]) == {"1", "2"}
    assert "segundo" not in datos["articulos_transitorios"]
    assert any("segundo" in a["articulos"] for a in datos["cuerpos_anexos"])


def test_el_dfl_que_ordena_refundir_la_ley_siguiente_cierra_los_transitorios(tmp_path):
    """En el Código Civil, «ARTICULO 7º: Fíjase el siguiente texto refundido» no es un transitorio de la ley previa."""
    datos = _parsear(tmp_path, [
        ("Artículo", "Art. 1. Regla de la ley anexa."),
        ("Artículo", "Art. 2. Otra regla."),
        ("Título", "ARTICULOS TRANSITORIOS"),
        ("Artículo", "Artículo primero. Mientras se establezcan los jueces."),
        ("Artículo", "ARTICULO 7º: Fíjase el siguiente texto refundido, coordinado y sistematizado de la ley siguiente."),
        ("Doble Articulado", ""),
        ("Artículo", "Artículo 1º De los juicios de alimentos conocerá el juez."),
    ])
    todas = [datos["articulos"], datos["articulos_transitorios"]] + [a["articulos"] for a in datos["cuerpos_anexos"]]
    transitorios = datos["articulos_transitorios"]
    assert "7" not in transitorios and all("7" not in t for t in
                                           [a.get("articulos_transitorios", {}) for a in datos["cuerpos_anexos"]])
    assert any("7" in mapa for mapa in todas)


def test_clave_repetida_en_un_cuerpo_conserva_la_primera_y_lo_declara(tmp_path):
    datos = _parsear(tmp_path, [
        ("Artículo", "Artículo 5.- Primera redacción."),
        ("Artículo", "Artículo 5.- Segunda redacción duplicada."),
        ("Artículo", "Artículo 6.- Otra."),
    ])
    assert datos["articulos"]["5"] == "Artículo 5.- Primera redacción."
    assert datos["diagnostico_articulos"]["colisiones"] == ["articulo:5@1"]


def test_el_tipo_de_parte_se_compara_sin_tildes_ni_mayusculas(tmp_path):
    datos = _parsear(tmp_path, [("articulo", "Artículo 1.- uno"), ("ARTÍCULO", "Artículo 2.- dos")])
    assert set(datos["articulos"]) == {"1", "2"}


def test_las_estructuras_se_guardan_completas_y_el_parser_declara_su_version(tmp_path):
    datos = _parsear(tmp_path, DFL_CON_ANEXA)
    assert datos["totalEstructuras"] == len(DFL_CON_ANEXA) == len(datos["estructuras"])
    assert datos["version_parser"] == bcn_connector._VERSION_PARSER == 3
    assert [e["tipoParte"] for e in datos["estructuras"]][:3] == ["Artículo", "Artículo", "Doble Articulado"]


# ── Búsqueda ───────────────────────────────────────────────────────────────────

def test_un_articulo_inexistente_es_no_encontrado_y_no_el_texto_de_otro(tmp_path, monkeypatch):
    """Se elimina el respaldo por mención: pedir el 99 no devuelve el artículo que dice «artículo 99»."""
    cliente = _cliente(tmp_path)
    datos = cliente._parse_norma_xml(_xml([
        ("Artículo", "Artículo 5.- Remite a lo dispuesto en el artículo 99 de esta ley."),
        ("Artículo", "Artículo 25 bis.- Regla bis."),
        ("Artículo", "Artículo 183-A.- Es trabajo en régimen de subcontratación."),
    ]))
    monkeypatch.setattr(cliente, "get_ley", lambda id_ley, use_cache=True: datos)

    res = cliente.get_articulo_ley(1, "99")
    assert "texto" not in res and "no encontrado" in res["error"]

    # 183 no existe aunque sí 183-A; 25 no existe aunque sí 25 bis: antes devolvía el sufijado.
    res = cliente.get_articulo_ley(1, "183")
    assert "texto" not in res and "183-a" in res["error"], res
    res = cliente.get_articulo_ley(1, "25")
    assert "texto" not in res and "25 bis" in res["sugerencias"][0], res
    assert cliente.get_articulo_ley(1, "183-A")["texto"].startswith("Artículo 183-A")
    assert cliente.get_articulo_ley(1, "Art. 25 bis")["texto"].startswith("Artículo 25 bis")


def test_pedir_un_numero_que_solo_existe_en_un_anexo_no_entrega_el_del_anexo(tmp_path):
    datos = _parsear(tmp_path, DFL_CON_ANEXA)
    hallazgo, sugerencias = _resolver_articulo(datos, "21")
    assert hallazgo is None
    assert any("anexo" in s for s in sugerencias)


def test_varios_cuerpos_de_peso_parecido_se_avisan(tmp_path):
    """Ley 20.416: si ningún cuerpo triplica al siguiente, la respuesta lo dice."""
    partes = [("Artículo", f"Artículo {n}.- Regla {n} del primer texto.") for n in range(1, 7)]
    partes += [("Artículo", f"Artículo {n}.- Regla {n} del segundo texto.") for n in range(1, 5)]
    datos = _parsear(tmp_path, partes)
    assert datos["cuerpo_principal"]["dominante"] is False
    hallazgo, _ = _resolver_articulo(datos, "3")
    assert hallazgo and "aviso_cuerpos" in hallazgo[2]
    assert "2 cuerpos" in hallazgo[2]["aviso_cuerpos"]


def test_get_codigo_entrega_transitorio_pedido_expresamente(tmp_path, monkeypatch):
    cliente = _cliente(tmp_path)
    datos = cliente._parse_norma_xml(_xml([
        ("Artículo", "Artículo 1.o Las relaciones laborales."),
        ("Artículo Transitorio", "ARTICULOS TRANSITORIOS"),
        ("Artículo", "Art. 1o Las disposiciones de este Código no alteran las normas."),
    ]))
    monkeypatch.setattr(cliente, "get_norma", lambda id_norma, use_cache=True: datos)
    assert cliente.get_codigo("trabajo", "1")["texto"].startswith("Artículo 1.o")
    transitorio = cliente.get_codigo("trabajo", "Art. 1º transitorio")
    assert transitorio["texto"].startswith("Art. 1o Las disposiciones") and transitorio["transitorio"] is True
    assert "texto" not in cliente.get_codigo("trabajo", "2 transitorio")


# ── Copias locales: v2 → v3 sin red ───────────────────────────────────────────

def _escribir_copia_v2(carpeta, nombre, partes, dias=1):
    """Una copia v2 como la dejaba el parser anterior: mapa pisado + estructuras."""
    datos = _cliente(carpeta)._parse_norma_xml(_xml(partes))
    datos.pop("version_parser", None)
    datos["articulos"] = {"1": partes[-1][1]}      # el mapa pisado de la v2
    for clave in ("articulos_transitorios", "cuerpos_anexos", "cuerpo_principal", "diagnostico_articulos"):
        datos.pop(clave, None)
    ruta = carpeta / nombre
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    marca = time.time() - dias * 86400
    os.utime(ruta, (marca, marca))
    return ruta


def test_la_copia_v2_se_migra_a_v3_sin_red(tmp_path, monkeypatch):
    cliente = _cliente(tmp_path)
    v2 = _escribir_copia_v2(tmp_path, "norma_p2_172986.json", DFL_CON_ANEXA, dias=3)
    antes = os.path.getmtime(v2)

    def _sin_red(*_a, **_k):
        raise AssertionError("la migración no puede ir a la red")

    monkeypatch.setattr(cliente, "_fetch_xml", _sin_red)
    res = cliente.get_codigo("civil", "1")

    assert res["texto"].startswith("Artículo 1º. La ley es una declaración de la voluntad soberana")
    v3 = tmp_path / "norma_p3_172986.json"
    assert v3.exists() and v2.exists(), "la copia nueva se escribe y la vieja no se borra"
    assert abs(os.path.getmtime(v3) - antes) < 2, "conserva la fecha de descarga, que gobierna el TTL de 30 días"
    guardada = json.loads(v3.read_text(encoding="utf-8"))
    assert guardada["version_parser"] == 3 and guardada["cuerpos_anexos"]


def test_la_migracion_concurrente_deja_una_sola_copia_integra(tmp_path, monkeypatch):
    """El lote de cita_texto pide el mismo código desde 6 hilos: la copia nueva sale entera, sin temporales."""
    from concurrent.futures import ThreadPoolExecutor

    cliente = _cliente(tmp_path)
    _escribir_copia_v2(tmp_path, "norma_p2_172986.json", DFL_CON_ANEXA, dias=2)
    monkeypatch.setattr(cliente, "_fetch_xml", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("red")))

    with ThreadPoolExecutor(max_workers=6) as pool:
        textos = list(pool.map(lambda _: cliente.get_codigo("civil", "1")["texto"], range(12)))

    assert all(t.startswith("Artículo 1º. La ley es una declaración") for t in textos)
    json.loads((tmp_path / "norma_p3_172986.json").read_text(encoding="utf-8"))
    assert not list(tmp_path.glob("*.tmp")), "no quedan temporales"


def test_la_copia_v2_vencida_migra_y_sale_marcada_si_no_hay_red(tmp_path, monkeypatch):
    cliente = _cliente(tmp_path)
    _escribir_copia_v2(tmp_path, "ley_p2_99999.json", DFL_CON_ANEXA, dias=45)

    def _sin_red(*_a, **_k):
        raise RuntimeError("red caída")

    monkeypatch.setattr(cliente, "_fetch_xml", _sin_red)
    res = cliente.get_articulo_ley(99999, "2")
    assert res["texto"].startswith("Art. 2º. La costumbre")
    assert cliente.get_ley(99999).get("copia_local_vencida") is True, "migrar no rejuvenece la copia"


def test_una_copia_v2_sin_estructuras_no_se_migra(tmp_path, monkeypatch):
    """Sin `estructuras` no hay de dónde derivar el mapa: se vuelve a bajar, no se reutiliza el pisado."""
    cliente = _cliente(tmp_path)
    (tmp_path / "ley_p2_5.json").write_text(json.dumps({"titulo": "x", "articulos": {"1": "pisado"}}), encoding="utf-8")
    monkeypatch.setattr(cliente, "_fetch_xml", lambda params: _xml([("Artículo", "Artículo 1.- texto bueno")]))
    assert cliente.get_ley(5)["articulos"]["1"] == "Artículo 1.- texto bueno"


def test_la_copia_historica_por_texto_pasa_tal_cual_a_v3(tmp_path, monkeypatch):
    """`get_codigo_historico` guarda texto corrido, que no depende del parser: no se vuelve a bajar."""
    cliente = _cliente(tmp_path)
    ruta = tmp_path / "historica_p2_v2_172986_2020-01-01.json"
    ruta.write_text(json.dumps({"texto": "Artículo 1º. La ley es una declaración. Art. 2º. La costumbre.",
                                "fechaVersionEfectiva": "2019-05-01", "tipoVersion": "Original",
                                "versionUrl": ""}), encoding="utf-8")

    def _sin_red(*_a, **_k):
        raise AssertionError("no debía ir a la red")

    monkeypatch.setattr(cliente, "_fetch_json_servicios", _sin_red)
    res = cliente.get_codigo_historico("civil", "2020-01-01", articulo="1")
    assert "La ley es una declaración" in res["texto"]
    assert (tmp_path / "historica_p3_v2_172986_2020-01-01.json").exists()


def test_cargar_articulos_cache_lee_v3_y_rederiva_v2_sin_escribir(tmp_path):
    carpeta = tmp_path
    _escribir_copia_v2(carpeta, "norma_p2_172986.json", DFL_CON_ANEXA)
    articulos = bcn_connector.cargar_articulos_cache(str(carpeta), 172986)
    assert articulos["1"].startswith("Artículo 1º. La ley es una declaración")
    assert not (carpeta / "norma_p3_172986.json").exists(), "solo lee: no escribe"
    assert bcn_connector.cargar_articulos_cache(str(carpeta), 1) == {}


def test_segmentar_sin_estructuras_devuelve_mapas_vacios():
    r = _segmentar_articulos([])
    assert r["articulos"] == {} and r["cuerpos_anexos"] == [] and r["articulos_transitorios"] == {}


# ── Regresión sobre la caché real (se salta si no existe) ──────────────────────

_NORMAS_REALES = {
    "civil": "norma_%s_172986.json", "comercio": "norma_%s_1974.json", "penal": "norma_%s_1984.json",
    "trabajo": "norma_%s_207436.json", "cpc": "norma_%s_22740.json", "cpp": "norma_%s_176595.json",
    "constitucion": "norma_%s_242302.json",
}


def _plano(texto):
    """Los textos oficiales vienen cortados en líneas de ~60 caracteres: se comparan sin saltos."""
    return " ".join(texto.split())


def _carpeta_cache_real():
    candidatos = [os.environ.get("OPENLEGAL_BCN_CACHE_REAL", ""),
                  os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bcn_cache")]
    for carpeta in candidatos:
        if carpeta and os.path.isdir(carpeta):
            return carpeta
    return ""


def _copiar_real(origen, destino, nombre_buscado):
    """Copia la norma real (p3 o p2: ambas guardan `estructuras`) como p2 para ejercitar la migración."""
    for version in ("p3", "p2"):
        ruta = os.path.join(origen, nombre_buscado % version)
        if os.path.exists(ruta):
            copia = os.path.join(destino, nombre_buscado % "p2")
            shutil.copyfile(ruta, copia)
            ahora = time.time()
            os.utime(copia, (ahora, ahora))      # fresca: el TTL de 30 días no manda a la red
            with open(copia, encoding="utf-8") as f:
                return "estructuras" in json.load(f)
    return False


@pytest.fixture(scope="module")
def cache_real(tmp_path_factory):
    origen = _carpeta_cache_real()
    if not origen:
        pytest.skip("no hay caché real de BCN (bcn_cache/ u OPENLEGAL_BCN_CACHE_REAL)")
    destino = tmp_path_factory.mktemp("bcn_real")
    faltan = [n for n in _NORMAS_REALES.values() if not _copiar_real(origen, str(destino), n)]
    if faltan:
        pytest.skip("la caché real de BCN no está completa: se necesitan los 7 códigos con sus estructuras")
    for numero in (19496, 18700):
        ruta = os.path.join(origen, f"ley_p2_{numero}.json")
        if os.path.exists(ruta):
            shutil.copyfile(ruta, str(destino / f"ley_p2_{numero}.json"))
            ahora = time.time()
            os.utime(str(destino / f"ley_p2_{numero}.json"), (ahora, ahora))
    cliente = BCNClient(cache_dir=str(destino))

    def _sin_red(*_a, **_k):
        raise AssertionError("la regresión sobre la caché real no puede ir a la red")

    cliente._fetch_xml = _sin_red     # type: ignore[method-assign]
    return cliente, destino


@pytest.mark.parametrize("codigo, articulo, empieza", [
    ("civil", "1", "Artículo 1º. La ley es una declaración de la voluntad soberana"),
    ("civil", "3", "Art. 3º. Sólo toca al legislador explicar o interpretar la ley"),
    ("civil", "44", "Art. 44. La ley distingue tres especies de culpa o descuido"),
    ("civil", "45", "Art. 45. Se llama fuerza mayor o caso fortuito"),
    ("civil", "50", "Art. 50. En los plazos que se señalaren"),
    ("civil", "1438", "Art. 1438. Contrato o convención es un acto"),
    ("constitucion", "19", "Artículo 19.- La Constitución asegura a todas las personas"),
    ("constitucion", "1", "Artículo 1°.- Las personas nacen libres e iguales en dignidad y derechos"),
    ("trabajo", "1", "Artículo 1.o Las relaciones laborales"),
    ("trabajo", "161", "Art. 161. Sin perjuicio de lo señalado en los"),
    ("trabajo", "183-A", "Artículo 183-A.- Es trabajo en régimen de subcontratación"),
    ("trabajo", "183-AE", "Artículo 183-AE.-"),
    ("cpc", "3", "Art. 3° Se aplicará el procedimiento ordinario"),
    ("cpc", "3 bis", "Artículo 3º bis.-"),
    ("penal", "1", "ARTÍCULO 1."),
    ("comercio", "1", "Artículo 1°. El Código de Comercio rige"),
    ("cpp", "58", "Artículo 58.- Responsabilidad penal"),
])
def test_casos_reales_devuelven_el_articulo_correcto(cache_real, codigo, articulo, empieza):
    cliente, _ = cache_real
    res = cliente.get_codigo(codigo, articulo)
    assert "error" not in res, res
    assert _plano(res["texto"]).startswith(empieza), (codigo, articulo, res["texto"][:120])


def test_casos_reales_ley_19496_art_16_no_es_el_16_b(cache_real):
    cliente, destino = cache_real
    if not (destino / "ley_p2_19496.json").exists():
        pytest.skip("sin la Ley 19.496 en la caché")
    assert _plano(cliente.get_articulo_ley(19496, "16")["texto"]).startswith(
        "Artículo 16.- No producirán efecto alguno")
    assert _plano(cliente.get_articulo_ley(19496, "16 B")["texto"]).startswith("Artículo 16 B.")


def test_casos_reales_inexistente_y_transitorios(cache_real):
    cliente, _ = cache_real
    assert "no encontrado" in cliente.get_codigo("civil", "99999")["error"]
    assert "texto" not in cliente.get_codigo("civil", "17 bis")        # solo existe en una ley anexa
    assert _plano(cliente.get_codigo("constitucion", "cuarta transitoria")["texto"]).startswith("CUARTA.-")
    assert _plano(cliente.get_codigo("trabajo", "1 transitorio")["texto"]).startswith(
        "Art. 1o Las disposiciones de este Código")


def test_casos_reales_cita_texto_trae_el_articulo_correcto(cache_real, monkeypatch):
    """El síntoma original: `cita_texto("Código Civil art. 1")` entregaba la Ley 16.271."""
    import mcp_server

    cliente, _ = cache_real
    monkeypatch.setattr(mcp_server, "_bcn_para_citas", lambda: cliente)
    res = mcp_server.handle_tool_call("cita_texto", {"referencias": [
        "Código Civil art. 1", "Código Civil art. 50", "Código Civil art. 1438", "Constitución Política art. 19"]})
    assert res["faltantes"] == [], res
    textos = {c["formato"]: _plano(c["texto"]) for c in res["citas"]}
    assert textos["[BCN - Código Civil, Art. 1]"].startswith("Artículo 1º. La ley es una declaración")
    assert textos["[BCN - Código Civil, Art. 50]"].startswith("Art. 50. En los plazos que se señalaren")
    assert textos["[BCN - Código Civil, Art. 1438]"].startswith("Art. 1438. Contrato o convención")
    assert textos["[BCN - Constitución Política de la República, Art. 19]"].startswith(
        "Artículo 19.- La Constitución asegura a todas las personas")


def test_casos_reales_ningun_cuerpo_pisa_su_numeracion(cache_real):
    """En el mapa principal la numeración no retrocede y cada clave encabeza su propio texto."""
    cliente, _ = cache_real
    for codigo in ("civil", "comercio", "penal", "trabajo", "cpc", "cpp", "constitucion"):
        datos = cliente.get_codigo(codigo)
        assert datos["version_parser"] == 3
        anterior = 0
        for clave, texto in datos["articulos"].items():
            cab = bcn_connector._cabecera(texto)
            assert cab is not None and cab["clave"] == clave, (codigo, clave, texto[:60])
            if cab["clase"] == "num":
                assert cab["valor"] >= anterior, (codigo, clave)
                anterior = cab["valor"]


def test_casos_reales_el_codigo_civil_separa_sus_leyes_anexas(cache_real):
    cliente, _ = cache_real
    datos = cliente.get_codigo("civil")
    assert len(datos["articulos"]) >= 2524
    assert all(str(n) in datos["articulos"] for n in range(1, 2525) if n not in _SIN_ROTULO_CIVIL)
    assert datos["cuerpo_principal"]["dominante"] is True
    assert len(datos["cuerpos_anexos"]) >= 5
    assert any(a["desde"] == "1" and a["hasta"] == "55" for a in datos["cuerpos_anexos"]), "Ley 4.808"


# Números del Código Civil que BCN no publica como estructura propia (si aparece alguno, se anota aquí).
_SIN_ROTULO_CIVIL: set = set()
