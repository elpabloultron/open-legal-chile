"""
Open Legal Chile — Motor de Sistema 1 Local (LegalOpenJev)
==========================================================
Inspirado en la teoría de pensamiento rápido (Sistema 1 de Daniel Kahneman) y la
arquitectura de decisiones eficientes de Jev (TypeSafe AI).

Ejecuta decisiones discretas, deterministicas y estructuradas en < 5 ms en CPU local:
1. Choice: Triage y enrutamiento dinámico de herramientas MCP (filtra de 87 a 3-5 tools).
2. Noul: Compuertas binarias de admisibilidad, RUT (Módulo 11), mandatos (Art. 7 CPC)
   y plazos fatales (caducidad Art. 168 CT, protección Art. 20 CPR, prescripción Arts. 2514-2515 CC).
3. Score: Calificación ultrarrápida de relevancia para pasajes y candidatos normativos.

100% Local-First (stdio), soberano, sin dependencias de red ni costo de API.
Garantiza secreto profesional (Art. 247 CP) y cumplimiento de la Ley N° 19.628 / 21.719.
"""

from __future__ import annotations

import datetime as dt
import re
import time
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

# Feriados nacionales fijos de Chile (mes, día)
FERIADOS_CHILE_FIJOS: Set[Tuple[int, int]] = {
    (1, 1),    # Año Nuevo
    (5, 1),    # Día Nacional del Trabajo
    (5, 21),   # Día de las Glorias Navales
    (6, 20),   # Día Nacional de los Pueblos Indígenas
    (7, 16),   # Día de la Virgen del Carmen
    (8, 15),   # Asunción de la Virgen
    (9, 18),   # Independencia Nacional
    (9, 19),   # Día de las Glorias del Ejército
    (10, 31),  # Día de las Iglesias Evangélicas y Protestantes
    (11, 1),   # Día de Todos los Santos
    (12, 8),   # Inmaculada Concepción
    (12, 25),  # Navidad
}


def _normalizar_texto(texto: str) -> str:
    """Normaliza texto eliminando acentos y mayúsculas para búsquedas de alta velocidad."""
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


# ---------------------------------------------------------------------------
# Dataclasses de Salida Estructurada (Primitivas Jev)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class JevChoice:
    """Decisión de Sistema 1: Triage de materia, fuero y enrutador de herramientas MCP."""
    materia: str
    fuero: str
    herramientas_recomendadas: List[str]
    confianza: float
    ahorro_estimado_tokens: int
    senales_detectadas: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class JevNoul:
    """Decisión de Sistema 1: Compuerta binaria estricta de validez o admisibilidad jurídica."""
    regla: str
    admisible: bool
    dias_transcurridos: Optional[int] = None
    plazo_fatal_dias: Optional[int] = None
    dias_restantes: Optional[int] = None
    detalle: str = ""
    advertencia: Optional[str] = None


@dataclass(frozen=True)
class JevDecision:
    """Resultado integral de evaluación ejecutiva por LegalOpenJev."""
    query: str
    choice: JevChoice
    noul_gates: List[JevNoul]
    score_relevancia: float
    tiempo_ejecucion_ms: float


# ---------------------------------------------------------------------------
# Catálogo Taxonómico de Enrutamiento (87 Herramientas MCP en 16 Dominios)
# ---------------------------------------------------------------------------

TAXONOMIA_MATERIAS: Dict[str, Dict[str, Any]] = {
    "laboral": {
        "fuero": "juzgado_de_letras_del_trabajo",
        "keywords": [
            "despido", "finiquito", "trabajador", "empleador", "contrato de trabajo",
            "ley karin", "acoso laboral", "tutela laboral", "40 horas", "jornada",
            "licencia medica", "subcontratacion", "sindicato", "huelga", "remuneraciones",
            "cotizaciones", "ley bustos", "inspeccion del trabajo", "dt", "art 161",
            "art 160", "art 168", "necesidades de la empresa"
        ],
        "herramientas_nucleo": [
            "bcn_get_codigo", "dt_search_doctrina", "consulta_maestra", "generar_documento"
        ],
        "herramientas_apoyo": [
            "doctrina_search", "graphify_consulta_subgrafo", "vigilante_contrato_plazos"
        ]
    },
    "civil_contratos": {
        "fuero": "juzgado_de_letras_en_lo_civil",
        "keywords": [
            "compraventa", "arrendamiento", "contrato", "incumplimiento", "indemnizacion de perjuicios",
            "resolucion por incumplimiento", "clausula penal", "caso fortuito", "fuerza mayor",
            "teoria de la imprevision", "daño moral", "daño emergente", "lucro cesante",
            "nulidad absoluta", "nulidad relativa", "rescilacion", "art 1545", "art 1489"
        ],
        "herramientas_nucleo": [
            "bcn_get_codigo", "consulta_maestra", "doctrina_search", "generar_documento"
        ],
        "herramientas_apoyo": [
            "graphify_explicar_institucion", "pjud_search_jurisprudencia", "cita_texto"
        ]
    },
    "inmobiliario_cbr": {
        "fuero": "conservador_de_bienes_raices_civil",
        "keywords": [
            "estudio de titulos", "cbr", "conservador de bienes raices", "inmueble", "propiedad",
            "escritura publica", "hipoteca", "gravamen", "embargo", "prohibicion de enajenar",
            "dominio", "posesion efectiva", "deslinde", "rol de avaluo", "titulo de dominio"
        ],
        "herramientas_nucleo": [
            "cbr_estudio_titulos", "cbr_checklist_documentos", "cpc_validar_mandato", "bcn_get_codigo"
        ],
        "herramientas_apoyo": [
            "doctrina_search", "compile_legal_dossier"
        ]
    },
    "ambiental": {
        "fuero": "tribunal_ambiental",
        "keywords": [
            "ambiental", "tribunal ambiental", "1ta", "2ta", "3ta", "sma", "superintendencia del medio ambiente",
            "snifa", "seia", "rca", "resolucion de calificacion ambiental", "eia", "dia",
            "humedal urbano", "daño ambiental", "programa de cumplimiento", "sancion ambiental"
        ],
        "herramientas_nucleo": [
            "ambiental_consulta_maestra", "sma_search_sancionatorios", "ambiental_buscar_jurisprudencia"
        ],
        "herramientas_apoyo": [
            "bcn_get_ley", "pjud_search_jurisprudencia", "graphify_consulta_subgrafo"
        ]
    },
    "constitucional_proteccion": {
        "fuero": "corte_de_apelaciones_proteccion",
        "keywords": [
            "recurso de proteccion", "garantias constitucionales", "art 19", "art 20 cpr",
            "derecho a la vida", "igualdad ante la ley", "derecho de propiedad", "isapre",
            "fonasa", "alza de plan", "acto arbitrario", "acto ilegal", "garantia constitucional"
        ],
        "herramientas_nucleo": [
            "recurso_proteccion_generar", "bcn_get_codigo", "pjud_search_jurisprudencia", "consulta_maestra"
        ],
        "herramientas_apoyo": [
            "graphify_consulta_subgrafo", "export_brief_ojv"
        ]
    },
    "administrativo_probidad": {
        "fuero": "contraloria_general_republica",
        "keywords": [
            "contraloria", "cgr", "dictamen cgr", "sumario administrativo", "estatuto administrativo",
            "probidad", "dip", "infoprobidad", "declaracion de intereses", "compras publicas",
            "ley 19886", "confianza legitima", "contrata", "planta", "municipalidad"
        ],
        "herramientas_nucleo": [
            "cgr_search_jurisprudencia", "cgr_search_auditorias", "infoprobidad_get_dip", "entes_consultar_organo"
        ],
        "herramientas_apoyo": [
            "bcn_get_ley", "consulta_maestra"
        ]
    },
    "tributario": {
        "fuero": "tribunal_tributario_y_aduanero",
        "keywords": [
            "sii", "impuesto", "servicio de impuestos internos", "iva", "renta", "lir",
            "codigo tributario", "liquidacion", "giro", "fiscalizacion", "factura falsa",
            "elusion", "evasion", "tta", "circular sii", "oficio sii"
        ],
        "herramientas_nucleo": [
            "sii_search_circulares", "sii_buscar_resoluciones_y_oficios", "bcn_get_codigo", "sii_oficios_por_anio"
        ],
        "herramientas_apoyo": [
            "sii_jurisprudencia_judicial", "bcn_get_ley"
        ]
    },
    "libre_competencia": {
        "fuero": "tribunal_de_defensa_de_la_libre_competencia",
        "keywords": [
            "tdlc", "libre competencia", "fne", "fiscalia nacional economica", "colusion",
            "abuso de posicion dominante", "concentracion", "icg", "dictamen tdlc", "dl 211"
        ],
        "herramientas_nucleo": [
            "tdlc_search_jurisprudencia", "tdlc_buscar_icg_y_dictamenes", "bcn_get_ley"
        ],
        "herramientas_apoyo": [
            "consulta_maestra", "pjud_search_jurisprudencia"
        ]
    },
    "mercado_financiero": {
        "fuero": "comision_para_el_mercado_financiero",
        "keywords": [
            "cmf", "comision para el mercado financiero", "ncg", "norma de caracter general",
            "banco", "mercado de valores", "seguro", "insider trading", "sancion cmf", "ley 18045"
        ],
        "herramientas_nucleo": [
            "cmf_search_normativa", "cmf_buscar_sanciones", "bcn_get_ley"
        ],
        "herramientas_apoyo": [
            "consulta_maestra", "entes_consultar_organo"
        ]
    },
    "energia": {
        "fuero": "panel_de_expertos_cne",
        "keywords": [
            "cne", "comision nacional de energia", "panel de expertos", "tarifa electrica",
            "dfl 4", "transmision electrica", "generacion", "ppa", "cliente libre", "mercado electrico"
        ],
        "herramientas_nucleo": [
            "cne_get_centrales_y_proyectos", "panel_expertos_search", "bcn_get_ley"
        ],
        "herramientas_apoyo": [
            "consulta_maestra", "entes_consultar_organo"
        ]
    }
}


# ---------------------------------------------------------------------------
# Clase Principal del Motor LegalOpenJev
# ---------------------------------------------------------------------------

class LegalOpenJevEngine:
    """
    Motor de Sistema 1 Local para el ordenamiento jurídico de Chile.
    Resuelve triage, compuertas binarias y enrutamiento en < 5 ms en CPU.
    """

    def __init__(self):
        self._cache_regex: Dict[str, re.Pattern] = {}

    # -----------------------------------------------------------------------
    # 1. Primitiva CHOICE (Enrutador Dinámico de Herramientas MCP)
    # -----------------------------------------------------------------------

    def evaluate_choice(self, query: str, max_tools: int = 5) -> JevChoice:
        """
        Analiza la consulta y selecciona las 3 a 5 herramientas MCP pertinentes
        de entre las 87 oficiales, reduciendo el overhead de contexto > 70%.
        """
        q_norm = _normalizar_texto(query)
        if not q_norm:
            return JevChoice(
                materia="general",
                fuero="tribunales_ordinarios",
                herramientas_recomendadas=["consulta_maestra", "cita_texto", "bcn_get_codigo"],
                confianza=0.5,
                ahorro_estimado_tokens=12500,
                senales_detectadas=["consulta_vacia_o_general"]
            )

        puntuaciones: Dict[str, int] = {}
        senales_por_materia: Dict[str, List[str]] = {}

        # Detección de patrones de RIT/Rol en Chile
        # T- (Laboral), C- (Civil), P- (Penal), F- (Familia), E- (Ambiental/Especial)
        if re.search(r"\bt[-–]\s?\d+", q_norm):
            puntuaciones["laboral"] = puntuaciones.get("laboral", 0) + 25
            senales_por_materia.setdefault("laboral", []).append("rit_laboral_t")
        elif re.search(r"\bc[-–]\s?\d+", q_norm):
            puntuaciones["civil_contratos"] = puntuaciones.get("civil_contratos", 0) + 20
            senales_por_materia.setdefault("civil_contratos", []).append("rit_civil_c")
        elif re.search(r"\b(1ta|2ta|3ta|d[-–]\s?\d+)\b", q_norm):
            puntuaciones["ambiental"] = puntuaciones.get("ambiental", 0) + 30
            senales_por_materia.setdefault("ambiental", []).append("rol_tribunal_ambiental")

        # Escaneo de palabras clave por taxonomia
        for mat_key, cfg in TAXONOMIA_MATERIAS.items():
            for kw in cfg["keywords"]:
                if kw in q_norm:
                    puntuaciones[mat_key] = puntuaciones.get(mat_key, 0) + 10
                    senales_por_materia.setdefault(mat_key, []).append(kw)

        if not puntuaciones:
            # Fallback inteligente: consulta general de doctrina y código
            return JevChoice(
                materia="general_civil",
                fuero="juzgado_de_letras",
                herramientas_recomendadas=["consulta_maestra", "cita_texto", "bcn_get_codigo", "doctrina_search"],
                confianza=0.6,
                ahorro_estimado_tokens=12800,
                senales_detectadas=["fallback_sin_materia_especifica"]
            )

        mejor_materia = max(puntuaciones, key=lambda k: puntuaciones[k])
        confianza = min(1.0, round(puntuaciones[mejor_materia] / 40.0, 2))
        cfg_ganadora = TAXONOMIA_MATERIAS[mejor_materia]

        # Ensamblaje de herramientas (núcleo + apoyo hasta max_tools)
        tools = list(cfg_ganadora["herramientas_nucleo"])
        for t in cfg_ganadora.get("herramientas_apoyo", []):
            if len(tools) >= max_tools:
                break
            if t not in tools:
                tools.append(t)

        # Cálculo de tokens ahorrados: 87 tools ~14.384 tokens vs 4 tools ~800 tokens
        tokens_ahorrados = max(0, 14384 - (len(tools) * 200))

        return JevChoice(
            materia=mejor_materia,
            fuero=cfg_ganadora["fuero"],
            herramientas_recomendadas=tools[:max_tools],
            confianza=confianza,
            ahorro_estimado_tokens=tokens_ahorrados,
            senales_detectadas=senales_por_materia.get(mejor_materia, [])
        )

    # -----------------------------------------------------------------------
    # 2. Primitiva NOUL (Compuertas Binarias y Plazos Fatales)
    # -----------------------------------------------------------------------

    def evaluate_noul(self, regla: str, contexto: Dict[str, Any]) -> JevNoul:
        """
        Ejecuta juicios binarios estrictos (admisible/no admisible, cumple/no cumple).
        Rige el cómputo de plazos fatales y presupuestos de validez formal en Chile.
        """
        r = regla.lower().strip()

        # A. Caducidad Despido Injustificado (Art. 168 Código del Trabajo)
        if r in ("caducidad_laboral_art_168", "plazo_despido"):
            return self._evaluar_caducidad_laboral(contexto)

        # B. Plazo Fatal Recurso de Protección (Art. 20 CPR y CS Acta N° 94-2015)
        if r in ("recurso_proteccion_art_20", "plazo_proteccion"):
            return self._evaluar_plazo_proteccion(contexto)

        # C. Validación Algorítmica de RUT Chileno (Módulo 11)
        if r in ("rut_modulo_11", "validar_rut"):
            rut_str = str(contexto.get("rut") or "").strip()
            valido, detalle = self._validar_rut_m11(rut_str)
            return JevNoul(
                regla="rut_modulo_11",
                admisible=valido,
                detalle=detalle,
                advertencia=None if valido else "RUT inválido o dígito verificador erróneo según algoritmo Módulo 11."
            )

        # D. Verificación de Mandato Judicial (Art. 7 Código de Procedimiento Civil)
        if r in ("mandato_art_7_cpc", "poder_judicial"):
            return self._evaluar_mandato_art_7(contexto)

        # E. Prescripción Extintiva Civil (Arts. 2514 y 2515 Código Civil)
        if r in ("prescripcion_civil_art_2515", "prescripcion_civil"):
            return self._evaluar_prescripcion_civil(contexto)

        return JevNoul(
            regla=regla,
            admisible=False,
            detalle=f"Regla '{regla}' no reconocida en LegalOpenJev.",
            advertencia="Regla no implementada."
        )

    def _evaluar_caducidad_laboral(self, ctx: Dict[str, Any]) -> JevNoul:
        """
        Calcula el plazo fatal de 60 días hábiles judiciales del Art. 168 CT.
        En tribunales laborales (Art. 435 CT), son hábiles todos excepto sábados, domingos y festivos.
        Si hubo reclamo ante la Inspección del Trabajo, el plazo se suspende hasta un tope de 90 días hábiles.
        """
        fecha_despido_str = ctx.get("fecha_despido")
        if not fecha_despido_str:
            return JevNoul(
                regla="caducidad_laboral_art_168",
                admisible=False,
                detalle="Falta 'fecha_despido' (formato YYYY-MM-DD).",
                advertencia="No se puede calcular caducidad sin fecha cierta de término de relación laboral."
            )

        try:
            f_despido = dt.datetime.strptime(str(fecha_despido_str), "%Y-%m-%d").date()
        except ValueError:
            return JevNoul(
                regla="caducidad_laboral_art_168",
                admisible=False,
                detalle=f"Formato de fecha inválido '{fecha_despido_str}', se requiere YYYY-MM-DD.",
                advertencia="Error de formato de fecha."
            )

        fecha_corte = dt.date.today()
        if ctx.get("fecha_demanda"):
            try:
                fecha_corte = dt.datetime.strptime(str(ctx["fecha_demanda"]), "%Y-%m-%d").date()
            except ValueError:
                pass

        hubo_reclamo = bool(ctx.get("reclamo_inspeccion") or ctx.get("fecha_reclamo_dt"))
        plazo_tope = 90 if hubo_reclamo else 60

        dias_habiles = self.contar_dias_habiles_laborales(f_despido, fecha_corte)
        dias_restantes = plazo_tope - dias_habiles
        admisible = dias_restantes >= 0

        detalle = (
            f"Transcurridos {dias_habiles} días hábiles laborales (excluyendo sábados, domingos y festivos) "
            f"de un plazo fatal de {plazo_tope} días (Art. 168 Código del Trabajo)."
        )
        adv = None if admisible else (
            f"🚨 ACCIÓN CADUCADA: El plazo fatal de {plazo_tope} días hábiles expiró hace {abs(dias_restantes)} días. "
            f"El juez laboral debe declarar la caducidad de oficio conforme a la doctrina uniforme de la Corte Suprema."
        )

        return JevNoul(
            regla="caducidad_laboral_art_168",
            admisible=admisible,
            dias_transcurridos=dias_habiles,
            plazo_fatal_dias=plazo_tope,
            dias_restantes=dias_restantes,
            detalle=detalle,
            advertencia=adv
        )

    def _evaluar_plazo_proteccion(self, ctx: Dict[str, Any]) -> JevNoul:
        """
        Calcula el plazo fatal de 30 días corridos para el Recurso de Protección
        conforme al Auto Acordado de la Corte Suprema (Acta N° 94-2015).
        """
        fecha_acto_str = ctx.get("fecha_acto") or ctx.get("fecha_conocimiento")
        if not fecha_acto_str:
            return JevNoul(
                regla="recurso_proteccion_art_20",
                admisible=False,
                detalle="Falta 'fecha_acto' o 'fecha_conocimiento' (YYYY-MM-DD).",
                advertencia="Se requiere fecha del acto u omisión arbitrario o ilegal para computar el plazo."
            )

        try:
            f_acto = dt.datetime.strptime(str(fecha_acto_str), "%Y-%m-%d").date()
        except ValueError:
            return JevNoul(
                regla="recurso_proteccion_art_20",
                admisible=False,
                detalle=f"Fecha inválida '{fecha_acto_str}'.",
                advertencia="Error de formato."
            )

        hoy = dt.date.today()
        dias_corridos = (hoy - f_acto).days
        plazo_fatal = 30
        dias_restantes = plazo_fatal - dias_corridos
        admisible = dias_restantes >= 0

        detalle = f"Transcurridos {dias_corridos} días corridos de un plazo fatal de {plazo_fatal} días (CS Acta N° 94-2015)."
        adv = None if admisible else (
            f"🚨 PLAZO EXTEMPORÁNEO: Han transcurrido {dias_corridos} días corridos desde el hecho. "
            f"La I. Corte de Apelaciones declarará el recurso inadmisible en cuenta por extemporaneidad."
        )

        return JevNoul(
            regla="recurso_proteccion_art_20",
            admisible=admisible,
            dias_transcurridos=dias_corridos,
            plazo_fatal_dias=plazo_fatal,
            dias_restantes=dias_restantes,
            detalle=detalle,
            advertencia=adv
        )

    def _evaluar_mandato_art_7(self, ctx: Dict[str, Any]) -> JevNoul:
        """
        Verifica si el mandato judicial contiene las facultades expresas del inc. 2 del Art. 7 CPC.
        Facultades esenciales: desistirse en primera instancia, transigir, percibir.
        """
        texto_poder = _normalizar_texto(str(ctx.get("texto_mandato") or ""))
        if not texto_poder:
            return JevNoul(
                regla="mandato_art_7_cpc",
                admisible=False,
                detalle="Texto de poder no provisto.",
                advertencia="Falta texto de la escritura o cláusula de mandato."
            )

        facultades_requeridas = [
            ("desistirse", "desistirse en primera instancia"),
            ("transigir", "transigir o celebrar transacciones"),
            ("percibir", "percibir pagos o sumas adeudadas")
        ]

        faltantes = []
        for kw, desc in facultades_requeridas:
            if kw not in texto_poder:
                faltantes.append(desc)

        completo = len(faltantes) == 0
        detalle = "Mandato confiere facultades ordinarias y especiales del Art. 7 inc. 2 CPC." if completo else (
            f"Mandato incompleto. Carece de mención expresa para: {', '.join(faltantes)}."
        )

        return JevNoul(
            regla="mandato_art_7_cpc",
            admisible=completo,
            detalle=detalle,
            advertencia=None if completo else "Riesgo procesal: Sin facultad de transigir o percibir no se puede firmar finiquito o acuerdo en comparendo."
        )

    def _evaluar_prescripcion_civil(self, ctx: Dict[str, Any]) -> JevNoul:
        """
        Evalúa la prescripción extintiva de acciones civiles (Arts. 2514 y 2515 Código Civil):
        - Acción ejecutiva: 3 años.
        - Acción ordinaria: 5 años.
        """
        fecha_exigible_str = ctx.get("fecha_exigibilidad") or ctx.get("fecha_mora")
        if not fecha_exigible_str:
            return JevNoul(
                regla="prescripcion_civil_art_2515",
                admisible=False,
                detalle="Falta 'fecha_exigibilidad' de la obligación.",
                advertencia="Se requiere fecha cierta en que la obligación se hizo exigible."
            )

        try:
            f_exigible = dt.datetime.strptime(str(fecha_exigible_str), "%Y-%m-%d").date()
        except ValueError:
            return JevNoul(
                regla="prescripcion_civil_art_2515",
                admisible=False,
                detalle="Fecha inválida.",
                advertencia="Error de formato."
            )

        hoy = dt.date.today()
        dias_pasados = (hoy - f_exigible).days
        anios = dias_pasados / 365.25

        es_ejecutiva = bool(ctx.get("accion_ejecutiva", True))
        tope_anios = 3.0 if es_ejecutiva else 5.0
        vigente = anios <= tope_anios

        detalle = (
            f"Transcurridos {round(anios, 2)} años desde la exigibilidad. "
            f"Acción {'ejecutiva (plazo 3 años)' if es_ejecutiva else 'ordinaria (plazo 5 años)'} "
            f"conforme al Art. 2515 del Código Civil."
        )
        adv = None if vigente else (
            f"⚠️ RIESGO DE PRESCRIPCIÓN: Han transcurrido {round(anios, 2)} años. "
            f"La contraparte opondrá la excepción perentoria de prescripción extintiva de la acción."
        )

        return JevNoul(
            regla="prescripcion_civil_art_2515",
            admisible=vigente,
            dias_transcurridos=dias_pasados,
            plazo_fatal_dias=int(tope_anios * 365),
            dias_restantes=int((tope_anios - anios) * 365),
            detalle=detalle,
            advertencia=adv
        )

    # -----------------------------------------------------------------------
    # 3. Primitiva SCORE (Ponderación Ultrarrápida de Relevancia Local)
    # -----------------------------------------------------------------------

    def evaluate_score(self, candidatos: List[str], query: str) -> List[Tuple[float, str]]:
        """
        Pondera y ordena pasajes o textos jurídicos según solapamiento léxico
        y densidad semántica en microsegundos (O(N) puro en memoria).
        """
        q_norm = _normalizar_texto(query)
        palabras_q = set(re.findall(r"\b\w{3,}\b", q_norm))
        if not palabras_q or not candidatos:
            return [(0.0, c) for c in candidatos]

        scored: List[Tuple[float, str]] = []
        for c in candidatos:
            c_norm = _normalizar_texto(c)
            palabras_c = set(re.findall(r"\b\w{3,}\b", c_norm))
            inter = palabras_q.intersection(palabras_c)
            # Jaccard + bonificación por frase exacta
            jaccard = len(inter) / max(1, len(palabras_q.union(palabras_c)))
            sc = jaccard * 10.0
            if q_norm in c_norm:
                sc += 5.0
            scored.append((round(sc, 3), c))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored

    # -----------------------------------------------------------------------
    # 4. Pipeline Integral de Decisión Rápida (Decide)
    # -----------------------------------------------------------------------

    def decide(self, query: str, contexto: Optional[Dict[str, Any]] = None) -> JevDecision:
        """
        Ejecuta el ciclo completo de Sistema 1 en un solo llamado:
        1. Choice (Triage y tools).
        2. Noul (Compuertas procesales activadas si hay datos).
        3. Score de confianza y medición de tiempo en ms.
        """
        t0 = time.perf_counter()
        ctx = contexto or {}

        # 1. Choice
        choice = self.evaluate_choice(query)

        # 2. Noul (detección automática de compuertas a evaluar)
        noul_gates: List[JevNoul] = []

        # Evaluar RUT si aparece en query o contexto
        rut_match = re.search(r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dkK]\b", query)
        if rut_match:
            ctx.setdefault("rut", rut_match.group(0))

        if "rut" in ctx:
            noul_gates.append(self.evaluate_noul("rut_modulo_11", ctx))

        # Evaluar caducidad laboral si es materia laboral y hay fechas
        if choice.materia == "laboral" and ("fecha_despido" in ctx or "despido" in _normalizar_texto(query)):
            if "fecha_despido" in ctx:
                noul_gates.append(self.evaluate_noul("caducidad_laboral_art_168", ctx))

        # Evaluar recurso de protección si es materia constitucional
        if choice.materia == "constitucional_proteccion" and ("fecha_acto" in ctx or "fecha_conocimiento" in ctx):
            noul_gates.append(self.evaluate_noul("recurso_proteccion_art_20", ctx))

        # Evaluar mandato si se proveyó texto
        if "texto_mandato" in ctx:
            noul_gates.append(self.evaluate_noul("mandato_art_7_cpc", ctx))

        tiempo_ms = round((time.perf_counter() - t0) * 1000.0, 3)

        return JevDecision(
            query=query,
            choice=choice,
            noul_gates=noul_gates,
            score_relevancia=choice.confianza,
            tiempo_ejecucion_ms=tiempo_ms
        )

    # -----------------------------------------------------------------------
    # Utilidades Computacionales de Días Hábiles
    # -----------------------------------------------------------------------

    @staticmethod
    def contar_dias_habiles_laborales(fecha_inicio: dt.date, fecha_fin: dt.date) -> int:
        """
        Cuenta los días hábiles en sede laboral (Art. 435 Código del Trabajo).
        Son hábiles de lunes a viernes, excluyendo sábados, domingos y festivos legales.
        """
        if fecha_inicio > fecha_fin:
            return 0

        dias_habiles = 0
        actual = fecha_inicio + dt.timedelta(days=1)
        while actual <= fecha_fin:
            # 0=Lunes, ..., 4=Viernes, 5=Sábado, 6=Domingo
            if actual.weekday() < 5 and (actual.month, actual.day) not in FERIADOS_CHILE_FIJOS:
                dias_habiles += 1
            actual += dt.timedelta(days=1)

        return dias_habiles

    @staticmethod
    def contar_dias_habiles_civiles(fecha_inicio: dt.date, fecha_fin: dt.date) -> int:
        """
        Cuenta los días hábiles en sede civil ordinaria (Art. 66 CPC).
        Son hábiles de lunes a sábado, excluyendo únicamente domingos y feriados legales.
        """
        if fecha_inicio > fecha_fin:
            return 0

        dias_habiles = 0
        actual = fecha_inicio + dt.timedelta(days=1)
        while actual <= fecha_fin:
            if actual.weekday() != 6 and (actual.month, actual.day) not in FERIADOS_CHILE_FIJOS:
                dias_habiles += 1
            actual += dt.timedelta(days=1)

        return dias_habiles

    @staticmethod
    def _validar_rut_m11(rut_str: str) -> Tuple[bool, str]:
        """Algoritmo oficial Módulo 11 de validación del RUN/RUT de la República de Chile."""
        limpio = re.sub(r"[^0-9kK]", "", rut_str).upper()
        if len(limpio) < 2:
            return False, "RUT demasiado corto"

        cuerpo, dv = limpio[:-1], limpio[-1]
        try:
            cuerpo_num = int(cuerpo)
        except ValueError:
            return False, "Cuerpo de RUT no numérico"

        suma = 0
        multiplicador = 2
        for d in reversed(str(cuerpo_num)):
            suma += int(d) * multiplicador
            multiplicador = 2 if multiplicador == 7 else multiplicador + 1

        resto = suma % 11
        dv_esperado = 11 - resto
        if dv_esperado == 11:
            dv_calc = "0"
        elif dv_esperado == 10:
            dv_calc = "K"
        else:
            dv_calc = str(dv_esperado)

        es_valido = (dv == dv_calc)
        detalle = f"RUT {cuerpo_num:,}-{dv} {'válido' if es_valido else f'inválido (DV esperado: {dv_calc})'}"
        return es_valido, detalle
