"""
Open Legal Chile — Tests de la Expansión del Ecosistema de Derecho Chileno
Valida los nuevos módulos forenses, regulatorios, judiciales y de biblioteca:
- cbr_titles.py (Estudio decenal, CBR, Mandatos Art. 7 CPC)
- entes_publicos.py (RUT Módulo 11 y Directorio Orgánico del Estado)
- sentencias_parser.py (Art. 170 CPC y Proveídos OJV)
- tribunales_ambientales_connector.py (1TA, 2TA, 3TA y Compendios)
- academia_judicial_connector.py (Guías de Práctica Judicial)
- online_library_sync.py (Corpus Markdown, HuggingFace y Drive)
- mcp_server.py (Nuevas herramientas MCP)
"""

import os
import pytest
from cbr_titles import CBRTitleStudyEngine, JudicialPowerVerifier
from entes_publicos import validar_rut, calcular_dv_rut, consultar_ente, listar_entes
from sentencias_parser import SentenciaParserEngine, ProveidosParser
from tribunales_ambientales_connector import TribunalesAmbientalesClient
from academia_judicial_connector import AcademiaJudicialClient
from online_library_sync import OnlineLibrarySyncManager
from mcp_server import handle_tool_call, TOOLS


class TestCBRTitlesAndMandates:
    def setup_method(self):
        self.cbr = CBRTitleStudyEngine(anio_actual=2026)
        self.verifier = JudicialPowerVerifier()

    def test_validar_inscripcion_cbr(self):
        res = self.cbr.validar_inscripcion(fojas=1234, numero=567, anio=2020, conservador="Santiago", registro="propiedad")
        assert res["valida"] is True
        assert "Inscrito a fojas 1234 N° 567" in res["cita_formal"]
        assert res["conservador_reconocido"] is True

        res_invalida = self.cbr.validar_inscripcion(fojas=-1, numero=0, anio=1800, conservador="Santiago", registro="invalido")
        assert res_invalida["valida"] is False
        assert len(res_invalida["errores"]) >= 3

    def test_auditar_cadena_dominio_aprobada(self):
        cadena = [
            {"propietario": "Juan Pérez", "antecesor": "María González", "anio": 2026, "fojas": 100, "numero": 10, "conservador": "Santiago"},
            {"propietario": "María González", "antecesor": "Pedro Soto", "anio": 2018, "fojas": 200, "numero": 20, "conservador": "Santiago"},
            {"propietario": "Pedro Soto", "antecesor": "Ana Silva", "anio": 2010, "fojas": 300, "numero": 30, "conservador": "Santiago"}
        ]
        res = self.cbr.auditar_cadena_dominio(cadena, anios_requeridos=10)
        assert res["aprobado"] is True
        assert res["cobertura_anios"] == 16
        assert len(res["banderas_rojas"]) == 0

    def test_auditar_cadena_dominio_con_banderas_rojas(self):
        # Ruptura en la tradición y gravamen no alzado
        cadena = [
            {
                "propietario": "Juan Pérez",
                "antecesor": "Desconocido Inc.",
                "anio": 2025,
                "hipotecas_vigentes": ["Hipoteca Banco Santander con CGG vigente"],
                "modo_adquirir": "herencia",
                "inscripcion_especial_herencia": False
            },
            {"propietario": "María González", "antecesor": "Pedro Soto", "anio": 2022}
        ]
        res = self.cbr.auditar_cadena_dominio(cadena, anios_requeridos=10)
        assert res["aprobado"] is False
        assert any("Ruptura en la cadena de tradición" in b for b in res["banderas_rojas"])
        assert any("Hipoteca" in b for b in res["banderas_rojas"])
        assert any("Inscripción Especial de Herencia" in b for b in res["banderas_rojas"])

    def test_checklist_documentacion(self):
        chk = self.cbr.checklist_documentacion_cbr("condominio")
        assert chk["total_documentos_requeridos"] >= 8
        nombres = [d["documento"] for d in chk["documentos"]]
        assert any("Reglamento de Copropiedad" in n for n in nombres)
        assert any("Hipotecas, Gravámenes" in n for n in nombres)

    def test_auditar_mandato_judicial_completo(self):
        texto = """
        En lo principal: Designo como abogado patrocinante y confiero poder a doña Carolina Paz, 
        abogado habilitado para el ejercicio de la profesión, con todas las facultades de ambos incisos del artículo 7° 
        del Código de Procedimiento Civil, en especial las de desistirse en primera instancia, aceptar la demanda contraria, 
        absolver posiciones, renunciar los recursos, transigir, comprometer, otorgar a los árbitros facultades de arbitradores, 
        aprobar convenios y percibir.
        """
        res = self.verifier.auditar_mandato(texto)
        assert res["cumple_formalidad_patrocinio_poder"] is True
        assert res["total_facultades_extraordinarias_concedidas"] >= 7
        assert res["detalle_facultades_art_7_inc_2"]["transigir"]["concedida"] is True
        assert res["detalle_facultades_art_7_inc_2"]["percibir"]["concedida"] is True


class TestEntesPublicosYRUT:
    def test_algoritmo_modulo_11_rut(self):
        assert calcular_dv_rut(11111111) == "1"
        assert calcular_dv_rut(76086428) == "5"

    def test_validar_rut_chileno(self):
        res_ok = validar_rut("76.086.428-5")
        assert res_ok["valido"] is True
        assert res_ok["rut_canonico"] == "76.086.428-5"
        assert res_ok["tipo_persona_estimado"] == "Persona Jurídica / Empresa"

        res_err = validar_rut("11.111.111-9")
        assert res_err["valido"] is False
        assert res_err["dv_esperado"] == "1"

        res_invalido = validar_rut("abc")
        assert res_invalido["valido"] is False

    def test_consultar_entes_publicos(self):
        res_sii = consultar_ente("SII")
        assert res_sii["encontrado"] is True
        assert "Impuestos Internos" in res_sii["ente"]["nombre"]
        assert len(res_sii["ente"]["recursos_administrativos"]) >= 1

        res_fne = consultar_ente("Fiscalía Nacional Económica")
        assert res_fne["encontrado"] is True
        assert res_fne["ente"]["sigla"] == "FNE"

        res_inexistente = consultar_ente("Ministerio de Magia")
        assert res_inexistente["encontrado"] is False

    def test_listar_entes(self):
        lista = listar_entes()
        assert len(lista) >= 6
        siglas = [e["sigla"] for e in lista]
        assert "SII" in siglas and "CMF" in siglas and "CGR" in siglas


class TestSentenciasParser:
    def setup_method(self):
        self.parser = SentenciaParserEngine()
        self.proveidos = ProveidosParser()

    def test_parsear_sentencia_completa(self):
        sentencia_sample = """
        Santiago, diez de enero de dos mil veintiséis.
        Rol N° C-1234-2025.
        1° Juzgado de Letras en lo Civil de Santiago.
        VISTOS:
        Comparece don Juan Pérez deduciendo demanda ejecutiva en contra de don Pedro Soto.
        El demandado opuso la excepción de pago contemplada en el Art. 464 N° 9 del CPC.
        CONSIDERANDO:
        PRIMERO. Que en cuanto a los hechos acreditados en autos, la parte ejecutante acompañó pagaré a la vista.
        SEGUNDO. Que respecto al derecho aplicable, conforme al artículo 464 del Código de Procedimiento Civil...
        TERCERO. Que no se acreditó el pago efectivo de la obligación.
        POR ESTAS CONSIDERACIONES, y visto lo dispuesto en el artículo 144 del CPC:
        SE RESUELVE:
        I. Se rechaza la excepción de pago deducida por el demandado.
        II. Se condena en costas al demandado por haber sido totalmente vencido sin motivo plausible.
        Notifíquese por el estado diario.
        """
        res = self.parser.parsear_sentencia(sentencia_sample)
        assert res["rol"] == "C-1234-2025"
        assert "Juzgado de Letras" in res["tribunal"]
        assert res["total_considerandos"] >= 2
        assert "CONDENA EN COSTAS" in res["regimen_costas"]
        assert res["estructura_art_170_cpc"]["evaluacion_por_numeral"]["num_6_resolutiva"] is True

    def test_interpretar_proveidos(self):
        res_traslado = self.proveidos.interpretar_proveido("A lo principal: Traslado.")
        assert res_traslado["total_formulas_detectadas"] >= 1
        assert res_traslado["interpretaciones"][0]["tipo"] == "TRASLADO"

        res_citacion = self.proveidos.interpretar_proveido("Como se pide, con citación. Autos para fallo.")
        assert res_citacion["total_formulas_detectadas"] >= 2


class TestTribunalesAmbientalesYAcademiaJudicial:
    def test_tribunales_ambientales_clasificacion_rol(self):
        client = TribunalesAmbientalesClient()
        clas_r = client.clasificar_causa_rol("R-15-2025")
        assert clas_r["letra_tipo"] == "R"
        assert "Reclamaciones" in clas_r["tipo_procedimiento"]

        clas_d = client.clasificar_causa_rol("D-4-2024")
        assert clas_d["letra_tipo"] == "D"
        assert "Daño Ambiental" in clas_d["tipo_procedimiento"]

    def test_tribunales_ambientales_compendios(self):
        client = TribunalesAmbientalesClient()
        comp = client.get_compendios()
        assert len(comp) >= 3
        search_res = client.search_compendios("humedales")
        assert len(search_res) >= 1

    def test_academia_judicial_guias(self):
        client = AcademiaJudicialClient()
        guias = client.get_todas_las_guias()
        assert len(guias) >= 12
        search_penas = client.search_guias("determinacion de penas")
        assert len(search_penas) >= 1
        assert search_penas[0]["materia"] == "Penal"


class TestOnlineLibrarySync:
    def test_compilar_manifiesto(self):
        mgr = OnlineLibrarySyncManager()
        manif = mgr.compilar_manifiesto_corpus()
        assert manif["total_documentos"] >= 10
        assert manif["total_palabras"] > 500
        assert manif["licencia"] == "Apache-2.0 / Open Access"

    def test_preparar_card_y_bundle(self):
        mgr = OnlineLibrarySyncManager()
        card = mgr.preparar_dataset_card_huggingface()
        assert os.path.exists(card)
        with open(card, "r", encoding="utf-8") as f:
            content = f.read()
            assert "license: apache-2.0" in content
            assert "open-legal-chile/doctrina-jurisprudencia-chile" in content

    def test_publicar_hf_sin_token(self):
        mgr = OnlineLibrarySyncManager()
        # Asegurarse de que no falle con excepción si no hay token
        res = mgr.publicar_en_huggingface(token=None)
        # Si no hay variable HF_TOKEN en el entorno, debe dar error controlado
        if not os.environ.get("HF_TOKEN"):
            assert res["exito"] is False
            assert "HF_TOKEN" in res["error"]



class TestMCPServerNewTools:
    def test_mcp_rut_validar(self):
        res = handle_tool_call("rut_validar_chile", {"rut": "76.086.428-5"})
        assert res["valido"] is True
        assert res["rut_canonico"] == "76.086.428-5"

    def test_mcp_entes_consultar(self):
        res = handle_tool_call("entes_consultar_organo", {"organo": "CMF"})
        assert res["encontrado"] is True
        assert "Mercado Financiero" in res["ente"]["nombre"]

    def test_mcp_cbr_checklist(self):
        res = handle_tool_call("cbr_checklist_documentos", {"tipo_inmueble": "urbano"})
        assert res["total_documentos_requeridos"] >= 6

    def test_mcp_cpc_validar_mandato(self):
        res = handle_tool_call("cpc_validar_mandato", {"texto_mandato": "Designo abogado patrocinante y confiero poder para transigir y percibir."})
        assert res["cumple_formalidad_patrocinio_poder"] is True

    def test_mcp_academia_judicial(self):
        res = handle_tool_call("academia_judicial_buscar_guias", {"query": "penas"})
        assert isinstance(res, list)
        assert len(res) >= 1

    def test_mcp_total_tools_count(self):
        assert len(TOOLS) == 54
