"""
Pruebas unitarias para el Motor Jurídico Soberano y Auditor Forense 5D
Verifica que Open Legal Chile funcione 100% libre, local y con Cero API Keys.
"""

from chat_engine import LegalChatEngine
from critique import LegalCritiqueEngine
from config import check_configuration


def test_detect_provider_defaults_to_soberano_or_ollama():
    prov = LegalChatEngine.detect_provider()
    assert prov in ("soberano", "ollama")


def test_soberano_chat_laboral():
    engine = LegalChatEngine()
    res = engine.chat("¿Cuáles son los efectos y medidas de la Ley Karin 21643?", provider="soberano")
    assert "error" not in res
    assert res.get("provider") == "soberano"
    reply = res.get("reply", "")
    assert "Ley Karin" in reply or "21.643" in reply
    assert "Código del Trabajo" in reply or "CPT" in reply
    assert "1698" in reply  # Carga de la prueba


def test_soberano_chat_civil_contratos():
    engine = LegalChatEngine()
    res = engine.chat("Resolución de contrato por incumplimiento bilateral", provider="soberano")
    assert "error" not in res
    reply = res.get("reply", "")
    assert "1489" in reply or "Código Civil" in reply
    assert "pacta sunt servanda" in reply or "1545" in reply


def test_soberano_critique_forense_5d():
    engine = LegalCritiqueEngine()
    sample = """
    EN LO PRINCIPAL: Demanda ordinaria de resolución de contrato e indemnización.
    PRIMER OTROSÍ: Acompaña documentos.
    SEGUNDO OTROSÍ: Patrocinio y poder bajo la Ley 18.120.

    S.J.L. EN LO CIVIL DE SANTIAGO
    Comparece don Juan Pérez, domiciliado en Santiago, a US. respetuosamente digo:
    HECHOS: La contraparte incumplió el contrato válidamente celebrado.
    DERECHO: Artículos 1489 y 1545 del Código Civil.
    POR TANTO: Pido a US. acoger la demanda con costas.
    """
    res = engine.critique(sample, provider="soberano")
    assert "error" not in res
    assert res.get("provider") == "soberano"
    critique_text = res.get("critique", "")
    assert "INFORME DE AUDITORÍA FORENSE 5D" in critique_text
    assert "Calificación Global" in critique_text
    assert "Jerarquía Normativa" in critique_text
    assert "Estructura Forense" in critique_text


def test_soberano_critique_detecta_anglicismos_prohibidos():
    engine = LegalCritiqueEngine()
    bad_sample = "Solicitamos una etapa de discovery y el pago de punitive damages bajo la doctrina at-will."
    res = engine.critique(bad_sample, provider="soberano")
    critique_text = res.get("critique", "")
    assert "Common Law" in critique_text or "discovery" in critique_text


def test_check_configuration_sovereign():
    cfg = check_configuration()
    assert cfg.get("OPEN_SOURCE_SOBERANO") is True
    assert "bcn" in cfg.get("CONNECTORS_OPEN", {})


def test_critique_flag_informe_sin_hechos():
    engine = LegalCritiqueEngine()
    texto = ("INFORME\n\nI. Cuestión jurídica\n¿Procede la acción?\n\n"
             "III. Marco normativo\n[BCN - Código Civil, Art. 1545]\n")

    res = engine.critique(texto, provider="soberano")

    assert "hechos" in res["critique"].lower()


def test_critique_flag_cita_sin_transcripcion():
    engine = LegalCritiqueEngine()
    texto = ("HECHOS\n" + ("El proveedor incumplió el contrato durante meses. " * 8) +
             "\nLa norma aplicable es el artículo 1545 del Código Civil.")

    res = engine.critique(texto, provider="soberano")

    assert "texto literal" in res["critique"].lower()


def test_critique_conforme_con_hechos_y_transcripcion():
    engine = LegalCritiqueEngine()
    texto = ("HECHOS\n" + ("El proveedor incumplió el contrato durante meses. " * 8) +
             "\nEl artículo 1545 del Código Civil dispone: «" + ("La buena fe obliga a lo pactado. " * 6) + "»")

    res = engine.critique(texto, provider="soberano")
    crit = res["critique"]

    assert "No se describe un capítulo de hechos" not in crit
    assert "sin transcribir" not in crit.lower()


def test_critique_flag_documento_breve():
    """Los escritos forenses son extensos: uno breve se devuelve a desarrollar."""
    engine = LegalCritiqueEngine()
    texto = "HECHOS\n" + ("El proveedor incumplió el contrato durante meses. " * 8) + "\nPetitorio: se acoja."

    res = engine.critique(texto, provider="soberano")

    assert "breve" in res["critique"].lower()
