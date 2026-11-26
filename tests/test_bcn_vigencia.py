"""Pruebas deterministas de vigencia BCN, normalización de número de ley y reforma Ley 21.855."""

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from bcn_connector import BCNClient, _normalizar_id_ley, evaluar_vigencia_norma
from privacidad_inapi import PrivacyARCOEngine
from servidor.corpus import _cita_de_norma

RAIZ = Path(__file__).resolve().parent.parent

_XML_LEY_21719_MUESTRA = """<?xml version="1.0" encoding="utf-8"?>
<Norma xmlns="http://www.leychile.cl/esquemas" normaId="1209272" fechaVersion="2026-02-05" derogado="no derogado">
  <Identificador fechaPromulgacion="2024-11-25" fechaPublicacion="2024-12-13">
    <TiposNumeros><TipoNumero><Numero>21719</Numero></TipoNumero></TiposNumeros>
    <Organismos><Organismo>MINISTERIO SECRETARÍA GENERAL DE LA PRESIDENCIA</Organismo></Organismos>
  </Identificador>
  <Metadatos>
    <TituloNorma>REGULA LA PROTECCIÓN Y EL TRATAMIENTO DE LOS DATOS PERSONALES</TituloNorma>
    <IdentificacionFuente>Diario Oficial</IdentificacionFuente>
    <NumeroFuente>44023</NumeroFuente>
  </Metadatos>
  <EstructurasFuncionales>
    <EstructuraFuncional tipoParte="Artículo" idParte="1">
      <Texto>Artículo 1.- Objeto de la ley.</Texto>
    </EstructuraFuncional>
  </EstructurasFuncionales>
</Norma>
"""


def test_normalizar_id_ley_acepta_puntos_y_prefijos():
    assert _normalizar_id_ley("21.719") == 21719
    assert _normalizar_id_ley("Ley N° 21.855") == 21855
    assert _normalizar_id_ley(21643) == 21643
    for malo in ("", "sin-numero", 0, -5, True):
        with pytest.raises(ValueError):
            _normalizar_id_ley(malo)  # type: ignore[arg-type]


def test_evaluar_vigencia_norma_detecta_vacancia_ley_21719_y_estados():
    dato = {"normaId": "1209272", "numero": "21719", "fechaVersion": "2026-02-05", "derogado": "no derogado"}
    v_2026 = evaluar_vigencia_norma(dato, hoy=date(2026, 11, 26))
    assert v_2026["estado"] == "vacancia_legal"
    assert v_2026["fecha_entrada_vigencia"] == "2027-10-15"
    assert "21.855" in v_2026["modificada_por"]
    assert "19.628" in v_2026["regimen_transitorio"]

    v_2027 = evaluar_vigencia_norma(dato, hoy=date(2027, 10, 15))
    assert v_2027["estado"] == "vigente"

    v_derogada = evaluar_vigencia_norma({"derogado": "derogado", "fechaVersion": "2020-01-01"}, hoy=date(2026, 11, 26))
    assert v_derogada["estado"] == "derogada"

    v_futura = evaluar_vigencia_norma({"derogado": "no derogado", "fechaVersion": "2028-05-01"}, hoy=date(2026, 11, 26))
    assert v_futura["estado"] == "vacancia_legal"
    assert v_futura["fecha_entrada_vigencia"] == "2028-05-01"


def test_parse_norma_xml_extrae_publicacion_y_get_ley_normaliza_parametro(tmp_path):
    cliente = BCNClient(cache_dir=str(tmp_path))
    params_recibidos = []

    def fake_fetch(params):
        params_recibidos.append(dict(params))
        return _XML_LEY_21719_MUESTRA

    with patch.object(cliente, "_fetch_xml", side_effect=fake_fetch):
        res = cliente.get_ley("21.719")
        art = cliente.get_articulo_ley("21.719", "1")

    assert params_recibidos == [{"opt": 7, "idLey": 21719}]
    assert res["fechaPromulgacion"] == "2024-11-25"
    assert res["fechaPublicacion"] == "2024-12-13"
    assert res["fuenteOficial"] == "Diario Oficial"
    assert res["numeroFuente"] == "44023"
    assert res["vigencia"]["estado"] == "vacancia_legal"
    assert art["ley"] == 21719
    assert art["vigencia"]["fecha_entrada_vigencia"] == "2027-10-15"


def test_cita_de_norma_solo_adjunta_vigencia_si_hay_alerta():
    class ClienteFake:
        def get_codigo(self, obra, art):
            return {"texto": "Todo contrato legalmente celebrado...", "vigencia": {"estado": "vigente"}}

        def get_articulo_ley(self, num, art):
            return {
                "texto": "Artículo 1.- Objeto...",
                "vigencia": {"estado": "vacancia_legal", "fecha_entrada_vigencia": "2027-10-15"},
            }

    ok = _cita_de_norma(ClienteFake(), {"familia": "codigo", "obra": "civil", "articulo": "1545"})
    assert list(ok["cita"].keys()) == ["formato", "texto", "url", "fuente"]

    vac = _cita_de_norma(ClienteFake(), {"familia": "ley", "numero": "21719", "articulo": "1"})
    assert vac["cita"]["vigencia"]["estado"] == "vacancia_legal"
    assert vac["cita"]["vigencia"]["fecha_entrada_vigencia"] == "2027-10-15"


def test_privacidad_arco_y_skill_reflejan_ley_21855():
    arco = PrivacyARCOEngine.procesar_solicitud_arco("ACCESO", "Juan Pérez", "12.345.678-5", "Historial")
    assert "regimen_vigencia" in arco
    assert "15-10-2027" in arco["regimen_vigencia"]["ley_modernizada"]
    assert "21.855" in arco["regimen_vigencia"]["ley_modernizada"]

    skill_txt = (RAIZ / ".agents" / "skills" / "chilean-privacy-ip" / "SKILL.md").read_text(encoding="utf-8")
    assert "21.855" in skill_txt
    assert "15 de octubre de 2027" in skill_txt
    assert "privacidad_tramitar_arco" in skill_txt
    assert "inapi_cease_and_desist" in skill_txt
    assert "privacidad_generar_arco" not in skill_txt
    assert "inapi_carta_cese_desistimiento" not in skill_txt
