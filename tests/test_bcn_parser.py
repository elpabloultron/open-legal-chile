"""
Pruebas unitarias para el parser XML de la Biblioteca del Congreso Nacional (BCN).
Valida que la extracción de metadatos, artículos y estructuras funcionales funcione con precisión.
"""

from bcn_connector import BCNClient

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

def test_parse_norma_xml():
    client = BCNClient()
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
