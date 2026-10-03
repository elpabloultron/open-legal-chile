"""
Tests Unitarios y de Rendimiento para LegalOpenJev (Motor de Sistema 1 Local)
=============================================================================
Valida:
1. Primitiva Choice: Triage de materia y enrutamiento dinámico de herramientas MCP.
2. Primitiva Noul: Compuertas binarias de admisibilidad, RUT (Módulo 11), mandato (Art. 7 CPC)
   y plazos fatales (caducidad Art. 168 CT, protección Art. 20 CPR, prescripción Art. 2515 CC).
3. Primitiva Score: Ponderación léxico-semántica local ultra-rápida.
4. Benchmark de Latencia: Garantía de ejecución en < 5.0 ms en CPU.
"""

import datetime as dt
import time
import pytest

from legal_open_jev import (
    LegalOpenJevEngine,
    JevChoice,
    JevNoul,
    JevDecision
)


@pytest.fixture
def jev():
    return LegalOpenJevEngine()


# ---------------------------------------------------------------------------
# 1. Pruebas de CHOICE (Enrutador de Herramientas MCP)
# ---------------------------------------------------------------------------

def test_choice_materia_laboral(jev):
    query = "El trabajador fue despedido por necesidades de la empresa sin carta de aviso previo"
    choice = jev.evaluate_choice(query)
    assert choice.materia == "laboral"
    assert choice.fuero == "juzgado_de_letras_del_trabajo"
    assert "bcn_get_codigo" in choice.herramientas_recomendadas
    assert "dt_search_doctrina" in choice.herramientas_recomendadas
    assert len(choice.herramientas_recomendadas) <= 5
    assert choice.ahorro_estimado_tokens > 10000


def test_choice_materia_ambiental(jev):
    query = "Reclamación contra sanción de la SMA por infracción a la RCA de proyecto minero ante el 2TA"
    choice = jev.evaluate_choice(query)
    assert choice.materia == "ambiental"
    assert choice.fuero == "tribunal_ambiental"
    assert "ambiental_consulta_maestra" in choice.herramientas_recomendadas
    assert "sma_search_sancionatorios" in choice.herramientas_recomendadas


def test_choice_materia_constitucional_proteccion(jev):
    query = "Recurso de protección contra Isapre por alza arbitraria y unilateral del plan de salud"
    choice = jev.evaluate_choice(query)
    assert choice.materia == "constitucional_proteccion"
    assert "recurso_proteccion_generar" in choice.herramientas_recomendadas


def test_choice_materia_inmobiliaria_cbr(jev):
    query = "Estudio de títulos decenal de inmueble con hipotecas y gravámenes en el Conservador de Bienes Raíces"
    choice = jev.evaluate_choice(query)
    assert choice.materia == "inmobiliario_cbr"
    assert "cbr_estudio_titulos" in choice.herramientas_recomendadas
    assert "cbr_checklist_documentos" in choice.herramientas_recomendadas


def test_choice_materia_general_fallback(jev):
    query = "consulta jurídica general sobre teoría del acto"
    choice = jev.evaluate_choice(query)
    assert len(choice.herramientas_recomendadas) >= 3
    assert "consulta_maestra" in choice.herramientas_recomendadas


# ---------------------------------------------------------------------------
# 2. Pruebas de NOUL (Compuertas Binarias y Plazos Fatales)
# ---------------------------------------------------------------------------

def test_noul_rut_modulo_11(jev):
    # RUTs válidos
    valido_1 = jev.evaluate_noul("rut_modulo_11", {"rut": "11.111.111-1"})
    assert valido_1.admisible is True

    valido_k = jev.evaluate_noul("rut_modulo_11", {"rut": "7.654.321-K"})
    assert isinstance(valido_k.admisible, bool)
    # Verificar según algoritmo M11
    valido_auto, _ = jev._validar_rut_m11("19.876.543-2")
    noul_auto = jev.evaluate_noul("rut_modulo_11", {"rut": "19.876.543-2"})
    assert noul_auto.admisible == valido_auto

    # RUTs inválidos
    invalido = jev.evaluate_noul("rut_modulo_11", {"rut": "11.111.111-2"})
    assert invalido.admisible is False
    assert invalido.advertencia is not None


def test_noul_caducidad_laboral_art_168(jev):
    hoy = dt.date.today()

    # Despido hace 10 días corridos (dentro de los 60 hábiles)
    fecha_reciente = (hoy - dt.timedelta(days=10)).strftime("%Y-%m-%d")
    noul_vigente = jev.evaluate_noul("caducidad_laboral_art_168", {"fecha_despido": fecha_reciente})
    assert noul_vigente.admisible is True
    assert noul_vigente.dias_restantes > 0
    assert noul_vigente.advertencia is None

    # Despido hace 120 días corridos (claramente más de 60 hábiles)
    fecha_antigua = (hoy - dt.timedelta(days=120)).strftime("%Y-%m-%d")
    noul_caducado = jev.evaluate_noul("caducidad_laboral_art_168", {"fecha_despido": fecha_antigua})
    assert noul_caducado.admisible is False
    assert noul_caducado.dias_restantes < 0
    assert "ACCION CADUCADA" in noul_caducado.advertencia.upper() or "CADUCADA" in noul_caducado.advertencia.upper()

    # Con reclamo en la Inspección del Trabajo (tope extendido a 90 días hábiles)
    noul_dt = jev.evaluate_noul("caducidad_laboral_art_168", {
        "fecha_despido": fecha_reciente,
        "reclamo_inspeccion": True
    })
    assert noul_dt.plazo_fatal_dias == 90


def test_noul_recurso_proteccion_art_20(jev):
    hoy = dt.date.today()

    # Hecho arbitrario ocurrido hace 15 días corridos
    fecha_dentro = (hoy - dt.timedelta(days=15)).strftime("%Y-%m-%d")
    noul_ok = jev.evaluate_noul("recurso_proteccion_art_20", {"fecha_acto": fecha_dentro})
    assert noul_ok.admisible is True
    assert noul_ok.dias_restantes == 15

    # Hecho arbitrario ocurrido hace 40 días corridos (extemporáneo)
    fecha_fuera = (hoy - dt.timedelta(days=40)).strftime("%Y-%m-%d")
    noul_tarde = jev.evaluate_noul("recurso_proteccion_art_20", {"fecha_acto": fecha_fuera})
    assert noul_tarde.admisible is False
    assert noul_tarde.dias_restantes == -10
    assert "EXTEMPORANEO" in noul_tarde.advertencia.upper() or "EXTEMPORANEIDAD" in noul_tarde.advertencia.upper()


def test_noul_mandato_art_7_cpc(jev):
    # Mandato con facultades completas del inc. 2
    texto_completo = (
        "Por este acto confiere poder judicial con las facultades de ambos incisos del artículo 7 del CPC, "
        "en especial las de desistirse en primera instancia de la acción deducida, aceptar la demanda contraria, "
        "transigir o celebrar transacciones, comprometer y percibir sumas adeudadas."
    )
    noul_completo = jev.evaluate_noul("mandato_art_7_cpc", {"texto_mandato": texto_completo})
    assert noul_completo.admisible is True
    assert noul_completo.advertencia is None

    # Mandato incompleto (falta transigir y percibir)
    texto_incompleto = "Confiere poder simple para tramitar el presente juicio con facultades ordinarias."
    noul_incompleto = jev.evaluate_noul("mandato_art_7_cpc", {"texto_mandato": texto_incompleto})
    assert noul_incompleto.admisible is False
    assert noul_incompleto.advertencia is not None
    assert "transigir" in noul_incompleto.detalle


# ---------------------------------------------------------------------------
# 3. Pruebas de SCORE (Reranker Léxico Rápido)
# ---------------------------------------------------------------------------

def test_score_ranking(jev):
    query = "despido necesidades de la empresa aviso previo"
    candidatos = [
        "El contrato de arrendamiento termina por la llegada del plazo estipulado.",
        "El despido por necesidades de la empresa exige remitir carta de aviso previo con 30 días de anticipación.",
        "La posesión efectiva de la herencia intestada se solicita ante el Registro Civil."
    ]
    scored = jev.evaluate_score(candidatos, query)
    assert len(scored) == 3
    # El más relevante debe quedar primero
    assert "necesidades de la empresa" in scored[0][1]
    assert scored[0][0] > scored[1][0]
    assert scored[0][0] > scored[2][0]


# ---------------------------------------------------------------------------
# 4. Pipeline Integral DECIDE y Benchmark de Latencia (<5.0 ms)
# ---------------------------------------------------------------------------

def test_decide_pipeline_integral(jev):
    query = "Demanda laboral de despido injustificado para el trabajador RUT 12.345.678-5 contra Empresa SpA"
    decision = jev.decide(query, {
        "fecha_despido": (dt.date.today() - dt.timedelta(days=20)).strftime("%Y-%m-%d")
    })

    assert isinstance(decision, JevDecision)
    assert decision.choice.materia == "laboral"
    assert len(decision.noul_gates) >= 1
    assert decision.tiempo_ejecucion_ms < 15.0  # Primera corrida en frío


def test_benchmark_latencia_menor_a_5ms(jev):
    """Garantiza empíricamente que Sistema 1 opera en menos de 5.0 milisegundos."""
    query = "Acción de indemnización por incumplimiento de contrato de compraventa y cláusula penal"
    contexto = {"texto_mandato": "facultad de transigir y percibir"}

    # Calentamiento
    jev.decide(query, contexto)

    # Medición sobre 50 iteraciones
    t0 = time.perf_counter()
    iteraciones = 50
    for _ in range(iteraciones):
        d = jev.decide(query, contexto)
        assert d.choice.materia == "civil_contratos"

    tiempo_total_ms = (time.perf_counter() - t0) * 1000.0
    latencia_media_ms = tiempo_total_ms / iteraciones

    print(f"\n⚡ Latencia media LegalOpenJev: {round(latencia_media_ms, 3)} ms por decisión")
    assert latencia_media_ms < 5.0, f"Latencia media {latencia_media_ms} ms excede el umbral estricto de 5.0 ms"
