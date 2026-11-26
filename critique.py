"""
Open Legal Chile — Motor de Crítica Forense en 5 Dimensiones (Legal Critique Engine)
Inspirado en el sistema de auto-crítica de 5 dimensiones de Open Design, adaptado
estrictamente para el Ordenamiento Jurídico de la República de Chile (Civil Law).
"""

import re
import sys
from typing import Dict, Any, Optional
from chat_engine import LegalChatEngine

_TERMINOS_COMMON_LAW_PROHIBIDOS = (
    "at-will",
    "punitive damages",
    "treble damages",
    "discovery",
    "subpoena",
    "grand jury",
    "summary judgment",
    "title vii",
    "flsa",
    "osha",
)


def _descripcion_de_hechos(texto: str) -> str:
    """El bloque de hechos del documento ('' si no hay capítulo identificable)."""
    encabezado = re.search(r"(?im)^[^\n]{0,80}\bhechos\b[^\n]{0,80}$", texto)
    if not encabezado:
        return ""
    resto = texto[encabezado.end():]
    corte = re.search(
        r"(?im)^[^\n]{0,80}\b(?:derecho|marco normativo|doctrina|jurisprudencia|por tanto|"
        r"peticiones|dictamen|fundamentos)\b[^\n]{0,80}$", resto)
    return resto[: corte.start()] if corte else resto[:3000]


def _citas_sin_transcripcion(texto: str) -> list:
    """Las normas citadas que no vienen acompañadas de su texto literal (transcripción)."""
    from citas_legales import detectar_normas

    normas = detectar_normas(texto)
    if not normas:
        return []
    if re.search(r"«[^»]{80,}»", texto):
        return []
    return [n.get("etiqueta", "") for n in normas]

CRITIQUE_SYSTEM_PROMPT = """Eres el Auditor Forense Principal de Open Legal Chile.
Tu misión es auditar y criticar exhaustivamente un escrito judicial, contrato o dictamen
bajo el Derecho Continental Chileno (Civil Law) a través de 5 dimensiones estrictas:

1. JERARQUÍA NORMATIVA Y LEGALIDAD (Art. 1 Código Civil / CPR 1980):
   - ¿Se respetan las fuentes formales del derecho? (Constitución > Ley > Decreto/Reglamento).
   - ¿Se citan los artículos vigentes y pertinentes de los Códigos o Leyes especiales?
   - Prohibición estricta de términos de Common Law (sin discovery, punitive damages, at-will).

2. DOCTRINA Y JURISPRUDENCIA APLICABLE (CGR, DT, CS, C.A., TDLC):
   - ¿Se incorpora la doctrina administrativa vinculante o judicial relevante?
   - ¿Se cita correctamente el formato [BCN - ...], [Dictamen DT N° X/AAAA], [Dictamen CGR N° X (AAAA)], [CS - Rol N° ..., Fecha: ...]?
   - Toda norma citada viaja con su TEXTO LITERAL transcrito en el cuerpo del documento; una cita
     sin texto es un hallazgo («sin fuente verificable» si no se pudo traer).

3. ESTRUCTURA FORENSE Y TRAMITACIÓN DIGITAL (Ley 20.886 / CPC):
   - ¿Cumple con la Presuma OJV, comparecencia, capítulos de Hechos y Derecho, Por Tanto y Otrosíes?

4. COHERENCIA FÁCTICA Y CARGA DE LA PRUEBA (Art. 1698 Código Civil):
   - ¿Los hechos sustentan lógicamente las peticiones concretas?
   - ¿Se ofrece prueba idónea para los hechos controvertidos?

5. COMPUERTAS ÉTICAS Y PLAZOS FATALES:
   - ¿Se advierten plazos fatales (recursos, apelaciones, descargos)?
   - ¿Contiene la compuerta de revisión para el abogado habilitado?

Devuelve tu informe estructurado con puntuación (1 a 10) por dimensión y recomendaciones concretas de corrección."""

GOLDFISH_SYSTEM_PROMPT = """Eres un Tribunal Contradictorio de Contexto Cero («Modelo Elephant-Goldfish») para el Derecho de la República de Chile.
NO conoces ni debes asumir ninguna intención previa del redactor. Evalúa EXCLUSIVAMENTE el texto recibido desde tres roles independientes:

1. MINISTRO RELATOR (Corte de Apelaciones / Corte Suprema):
   - Detecta causales de ineptitud del libelo (Art. 254 y Art. 303 N.° 4 CPC), defectos de competencia, falta de peticiones concretas («Por Tanto») o vicios formales de tramitación digital (Ley N.° 20.886 / Ley N.° 18.120).

2. ABOGADO LITIGANTE DE LA CONTRAPARTE:
   - Ataca prescripción/caducidad (Art. 168 CT, 30 días corridos Acta N.° 94-2015, Arts. 2332/2515 CC), falta de legitimación activa/pasiva, orfandad probatoria (Art. 1698 CC) y contradicciones fácticas.

3. AUDITOR DE CITAS BCN / HUGGING FACE:
   - Rechaza cualquier figura del Common Law prohibida en Chile (punitive damages, at-will employment, discovery, subpoena, grand jury).
   - Marca como bloqueante toda norma citada sin tenor literal o con numeración manifiestamente errónea o derogada.

Emite un veredicto binario (APROBADO PARA FIRMA o RECHAZADO — REQUIERE SUBSANACIÓN) seguido de:
1) Hallazgos Bloqueantes, 2) Observaciones Sustantivas e Importantes, 3) Observaciones Formales Menores."""


_MAX_ARTICULO_CODIGO: Dict[str, int] = {
    "civil": 2525,
    "trabajo": 513,
    "cpc": 925,
    "penal": 501,
    "cpp": 485,
    "comercio": 1250,
    "tributario": 206,
    "aguas": 318,
    "mineria": 245,
}


def _detectar_articulos_imposibles(texto: str) -> list:
    """Detecta artículos con numeración imposible respecto del máximo legal del Código citado."""
    from citas_legales import detectar_normas

    imposibles = []
    for n in detectar_normas(texto):
        if n.get("familia") == "codigo":
            obra = str(n.get("obra", "")).lower()
            max_art = _MAX_ARTICULO_CODIGO.get(obra)
            art_raw = re.sub(r"\D", "", str(n.get("articulo", "")))
            if max_art and art_raw.isdigit() and int(art_raw) > max_art:
                imposibles.append(f"{n.get('etiqueta', '')} (máximo legal del código: Art. {max_art})")
    return imposibles


def verificar_citas_escrito(texto: str, consultar_bcn: bool = True, max_normas: int = 12) -> Dict[str, Any]:
    """Auditoría determinista post-redacción de citas normativas, roles y prohibiciones Common Law.

    Extrae todas las normas con `citas_legales.detectar_normas()`, detecta artículos fuera de rango
    legal, verifica el tenor literal contra BCN (caché/red) y señala cualquier figura del Common Law.
    """
    from citas_legales import detectar_normas

    t_lower = (texto or "").lower()
    common_law = [
        term for term in _TERMINOS_COMMON_LAW_PROHIBIDOS
        if term in t_lower
    ]
    normas = detectar_normas(texto or "")
    imposibles = _detectar_articulos_imposibles(texto or "")
    roles = sorted(set(re.findall(r"\b(?:Rol|RIT|RUC)\s*(?:N[°º.]*\s*)?[A-Z]?-?\d{1,6}-\d{4}\b", texto or "", re.IGNORECASE)))

    verificadas: list = []
    no_verificadas: list = []

    if consultar_bcn and normas:
        from bcn_connector import BCNClient
        bcn = BCNClient()
        for norma in normas[:max_normas]:
            etiqueta = str(norma.get("etiqueta") or "")
            if any(etiqueta and etiqueta in imp for imp in imposibles):
                no_verificadas.append({"etiqueta": etiqueta, "motivo": "Artículo fuera de rango legal del Código"})
                continue
            try:
                if norma.get("familia") == "codigo":
                    dato = bcn.get_codigo(str(norma.get("obra", "")), str(norma.get("articulo", "")))
                else:
                    num = int(str(norma.get("numero", "0")))
                    art = norma.get("articulo")
                    dato = bcn.get_articulo_ley(num, str(art)) if art else bcn.get_ley(num)
                if isinstance(dato, dict) and dato.get("texto") and not dato.get("error"):
                    verificadas.append({
                        "etiqueta": etiqueta,
                        "fechaVersion": dato.get("fechaVersion", ""),
                        "extracto": str(dato.get("texto", ""))[:240],
                    })
                else:
                    no_verificadas.append({
                        "etiqueta": etiqueta,
                        "motivo": str(dato.get("error", "Sin texto verificable en BCN")) if isinstance(dato, dict) else "Sin respuesta BCN",
                    })
            except Exception as e:  # noqa: BLE001
                no_verificadas.append({"etiqueta": etiqueta, "motivo": f"Error BCN: {str(e)[:120]}"})

    sin_transcripcion = _citas_sin_transcripcion(texto or "")
    bloqueante = bool(common_law or imposibles or no_verificadas)
    estado = "OBSERVADO" if bloqueante else "VERIFICADO"

    return {
        "estado": estado,
        "total_normas_detectadas": len(normas),
        "normas_verificadas": verificadas,
        "normas_no_verificadas": no_verificadas,
        "articulos_imposibles": imposibles,
        "normas_sin_transcripcion_literal": sin_transcripcion,
        "common_law_prohibido": common_law,
        "roles_detectados": roles,
    }


class LegalCritiqueEngine:
    def __init__(self):
        self.chat_engine = LegalChatEngine()

    @staticmethod
    def critique_soberano_local(text: str) -> str:
        """
        Auditor Forense Determinista en 5 Dimensiones (100% Offline / Cero API Keys).
        Evalúa el texto conforme a los estándares de la Ley 20.886, Código Civil,
        Código de Procedimiento Civil, Código del Trabajo y práctica forense chilena.
        """
        t_lower = text.lower()

        # --- Dimensión 1: Jerarquía Normativa y Legalidad ---
        d1_findings = []
        d1_score = 5
        leyes_detectadas = []
        for kw in ["código civil", "código del trabajo", "código de procedimiento civil", "código penal", "código de comercio", "constitución", "cpr", "ley n°", "ley 2", "dfl"]:
            if kw in t_lower:
                leyes_detectadas.append(kw.upper())
        if leyes_detectadas:
            d1_score += min(5, len(leyes_detectadas) * 2)
            d1_findings.append(f"Cita fuentes legales formales: {', '.join(set(leyes_detectadas))}.")
        else:
            d1_score = 3
            d1_findings.append("No se observan citas directas a Códigos de la República o Leyes especiales.")

        # Anglicismos prohibidos (Common Law)
        anglicismos = []
        for term in ["discovery", "punitive damages", "at-will", "at will", "subpoena", "interrogatories", "grand jury", "deposition", "tort of"]:
            if term in t_lower:
                anglicismos.append(term)
        if anglicismos:
            d1_score = max(1, d1_score - 4)
            d1_findings.append(f"ALERTA: Se detectaron términos de Common Law prohibidos en Chile: {', '.join(anglicismos)}.")
        else:
            d1_findings.append("Cumplimiento estricto de terminología de Derecho Continental (Civil Law).")

        # Transcripción: regla del producto — la norma citada viaja con su texto literal en el cuerpo.
        normas_sin_texto = _citas_sin_transcripcion(text)
        if normas_sin_texto:
            d1_score = max(1, d1_score - 2)
            d1_findings.append(
                "Se citan normas sin transcribir su texto literal en el cuerpo "
                f"({', '.join(normas_sin_texto[:3])}): transcripción completa + cita, no solo la cita.")

        d1_score = max(1, min(10, d1_score))

        # --- Dimensión 2: Doctrina y Jurisprudencia Aplicable ---
        d2_findings = []
        d2_score = 4
        fuentes_juris = []
        for kw in ["dictamen", "contraloría", "cgr", "dirección del trabajo", "dt", "corte suprema", "corte de apelaciones", "rol n°", "tribunal constitucional", "tc", "tdlc", "claro solar", "alessandri", "somarriva"]:
            if kw in t_lower:
                fuentes_juris.append(kw.title())
        if fuentes_juris:
            d2_score += min(6, len(fuentes_juris) * 2)
            d2_findings.append(f"Incorpora referencias a jurisprudencia/doctrina: {', '.join(set(fuentes_juris))}.")
        else:
            d2_findings.append("Se recomienda incorporar dictámenes administrativos (CGR/DT) o fallos de unificación de la Corte Suprema.")

        d2_score = max(1, min(10, d2_score))

        # --- Dimensión 3: Estructura Forense y OJV (Ley 20.886 / CPC) ---
        d3_findings = []
        d3_score = 3
        elementos_ojv = []
        if any(w in t_lower for w in ["en lo principal", "presuma", "suma:", "procedimiento:"]):
            elementos_ojv.append("Presuma/Suma")
        if any(w in t_lower for w in ["s.j.l.", "i. corte", "juzgado de letras"]):
            elementos_ojv.append("Tribunal Encabezado")
        if any(w in t_lower for w in ["a us.", "respetuosamente digo", "rut", "cédula", "domiciliado"]):
            elementos_ojv.append("Comparecencia Formal")
        if any(w in t_lower for w in ["hechos", "antecedentes", "en lo fáctico"]):
            elementos_ojv.append("Capítulo de Hechos")
        if any(w in t_lower for w in ["derecho", "fundamentos de derecho"]):
            elementos_ojv.append("Capítulo de Derecho")
        if any(w in t_lower for w in ["por tanto", "pido a us.", "ruego a us."]):
            elementos_ojv.append("Peticiones Concretas (Por Tanto)")
        if any(w in t_lower for w in ["otrosí", "primer otrosí", "patrocinio"]):
            elementos_ojv.append("Otrosíes / Poder")

        d3_score += len(elementos_ojv)
        if len(elementos_ojv) >= 4:
            d3_findings.append(f"Estructura procesal OJV identificada: {', '.join(elementos_ojv)}.")
        else:
            d3_findings.append(f"Estructura procesal incompleta para OJV. Solo contiene: {', '.join(elementos_ojv) if elementos_ojv else 'Formato libre'}.")

        # Hechos del caso: un informe no puede no describirlos.
        bloque_hechos = _descripcion_de_hechos(text)
        if not bloque_hechos:
            d3_score = max(1, d3_score - 2)
            d3_findings.append("No se describe un capítulo de hechos del caso: el informe debe "
                               "relatar los hechos (fechas, conductas, circunstancias).")
        elif len(bloque_hechos.strip()) < 300:
            d3_score = max(1, d3_score - 1)
            d3_findings.append(f"Los hechos están descritos de manera insuficiente "
                               f"({len(bloque_hechos.strip())} caracteres).")
        else:
            d3_findings.append("Capítulo de hechos presente y desarrollado.")

        # Extensión: los escritos forenses son extensos; uno breve se devuelve a desarrollar.
        if len(text.strip()) < 6000:
            d3_score = max(1, d3_score - 1)
            d3_findings.append(f"El documento es breve para un escrito judicial ({len(text.strip())} "
                               "caracteres): desarrolle los hechos, el análisis jurídico y la jurisprudencia.")

        d3_score = max(1, min(10, d3_score))

        # --- Dimensión 4: Coherencia Fáctica y Carga de la Prueba (Art. 1698 CC) ---
        d4_findings = []
        d4_score = 5
        if any(w in t_lower for w in ["prueba", "documental", "testigos", "testifical", "peritaje", "pericial", "confesional", "art. 1698", "art. 341"]):
            d4_score += 4
            d4_findings.append("Ofrece y articula medios de prueba conforme al Art. 341 CPC y Art. 1698 CC.")
        else:
            d4_score = 4
            d4_findings.append("Débil fundamentación probatoria: no se individualizan medios de prueba específicos para acreditar los hechos controvertidos.")

        d4_score = max(1, min(10, d4_score))

        # --- Dimensión 5: Compuertas Éticas y Plazos Fatales ---
        d5_findings = []
        d5_score = 5
        if any(w in t_lower for w in ["plazo", "días hábiles", "fatal", "caducidad", "prescripción"]):
            d5_score += 2
            d5_findings.append("Identifica plazos procesales o fatales.")
        else:
            d5_findings.append("No advierte expresamente sobre los plazos fatales para deducir excepciones o recursos.")

        if any(w in t_lower for w in ["ley 18.120", "patrocinio", "poder", "abogado habilitado"]):
            d5_score += 3
            d5_findings.append("Cumple con la advertencia de patrocinio letrado obligatorio (Ley 18.120).")
        else:
            d5_findings.append("Omitió la mención formal de patrocinio y poder bajo la Ley 18.120.")

        d5_score = max(1, min(10, d5_score))

        # Nota Promedio Ponderado
        promedio = round((d1_score * 0.25) + (d2_score * 0.20) + (d3_score * 0.20) + (d4_score * 0.20) + (d5_score * 0.15), 1)

        report = [
            "### 📋 INFORME DE AUDITORÍA FORENSE 5D — OPEN LEGAL CHILE",
            "**Modalidad:** Motor Soberano Local (100% Offline / Cero API Keys)",
            f"**Calificación Global:** **{promedio} / 10.0**\n",
            "| Dimensión Forense | Calificación | Estado |",
            "| :--- | :---: | :--- |",
            f"| **1. Jerarquía Normativa y Legalidad (Civil Law)** | **{d1_score}/10** | {'✅ Conforme' if d1_score >= 7 else '⚠️ Mejorable'} |",
            f"| **2. Doctrina y Jurisprudencia Vinculante** | **{d2_score}/10** | {'✅ Conforme' if d2_score >= 7 else '⚠️ Requiere citas'} |",
            f"| **3. Estructura Forense y OJV (Ley 20.886 / CPC)** | **{d3_score}/10** | {'✅ Conforme' if d3_score >= 7 else '⚠️ Incompleta'} |",
            f"| **4. Carga de la Prueba (Art. 1698 CC / Art. 341 CPC)** | **{d4_score}/10** | {'✅ Conforme' if d4_score >= 7 else '⚠️ Sin prueba idónea'} |",
            f"| **5. Plazos Fatales y Patrocinio (Ley 18.120)** | **{d5_score}/10** | {'✅ Conforme' if d5_score >= 7 else '⚠️ Falta advertencia'} |\n",
            "#### 🔍 Hallazgos por Dimensión:",
            "1. **Legalidad:** " + " ".join(d1_findings),
            "2. **Jurisprudencia:** " + " ".join(d2_findings),
            "3. **Estructura OJV:** " + " ".join(d3_findings),
            "4. **Carga Probatoria:** " + " ".join(d4_findings),
            "5. **Ética y Plazos:** " + " ".join(d5_findings) + "\n",
            "#### 🛠️ Recomendaciones de Subsanación:",
            "• Incorporar Presuma formal y desglose de Otrosíes para tramitación en Oficina Judicial Virtual.",
            "• Reforzar el petitorio con ofrecimiento expreso de prueba documental y testimonial bajo apercibimiento.",
            "• Añadir otrosí de patrocinio y poder ratificando el cumplimiento de la Ley 18.120."
        ]

        return "\n".join(report)

    @staticmethod
    def critique_goldfish_local(text: str) -> str:
        """
        Revisor Contradictorio de Contexto Cero («Goldfish Adversarial Reviewer», inspirado en
        google/elephant-goldfish-model).
        Evalúa únicamente el artefacto escrito aislado de toda historia conversacional o intención
        del redactor («Elefante»), simulando a un Ministro Relator de Corte de Apelaciones/Corte
        Suprema y al abogado litigante de la contraparte buscando causales de ineptitud del libelo
        (Art. 303 N.° 4 CPC), caducidad/prescripción, orfandad probatoria (Art. 1698 CC) y citas
        sin respaldo literal.
        """
        t_lower = text.lower()
        hallazgos_bloqueantes = []
        hallazgos_importantes = []
        hallazgos_menores = []

        # 1. Control de Ineptitud del Libelo (Art. 303 N.° 4 y Art. 254 CPC)
        if not any(w in t_lower for w in ["por tanto", "pido a us.", "ruego a us.", "peticiones concretas"]):
            hallazgos_bloqueantes.append(
                "[INEPTITUD DEL LIBELO — Art. 254 N.° 5 y Art. 303 N.° 4 CPC] El documento carece de "
                "peticiones concretas sometidas al fallo del tribunal («Por Tanto»)."
            )
        if not any(w in t_lower for w in ["rut", "cédula de identidad", "domiciliado"]):
            hallazgos_importantes.append(
                "[EXCEPCIÓN DILATORIA — Art. 254 N.° 2 y 3 CPC] Individualización incompleta de las partes "
                "(nombre, profesión u oficio y domicilio)."
            )

        # 2. Control de Citas sin Transcripción Literal, Artículos Imposibles y Common Law
        common_law_hits = [
            term for term in _TERMINOS_COMMON_LAW_PROHIBIDOS
            if term in t_lower
        ]
        if common_law_hits:
            hallazgos_bloqueantes.append(
                f"[CONTAMINACIÓN COMMON LAW PROHIBIDA] Se detectan figuras inexistentes en el Derecho Civil "
                f"chileno ({', '.join(common_law_hits)}). Eliminar y reconducir a instituciones chilenas."
            )

        articulos_imposibles = _detectar_articulos_imposibles(text)
        if articulos_imposibles:
            hallazgos_bloqueantes.append(
                f"[NORMA INEXISTENTE / ALUCINACIÓN NUMÉRICA] Artículos fuera de rango del Código citado: "
                f"{', '.join(articulos_imposibles[:4])}. Verificar con `cita_texto` en BCN Ley Chile."
            )

        normas_sin_texto = _citas_sin_transcripcion(text)
        if normas_sin_texto:
            hallazgos_bloqueantes.append(
                f"[CITA SIN TENOR LITERAL] Se invocan preceptos ({', '.join(normas_sin_texto[:4])}) sin "
                "transcribir su texto positivo entre comillas angulares (« »). Bajo revisión de contexto cero, "
                "toda norma no transcrita se presume no verificada."
            )

        # 3. Control de Orfandad Fáctica y Probatoria (Art. 1698 CC)
        bloque_hechos = _descripcion_de_hechos(text)
        if not bloque_hechos or len(bloque_hechos.strip()) < 250:
            hallazgos_bloqueantes.append(
                "[ORFANDAD FÁCTICA — Art. 254 N.° 4 CPC] Relato de hechos inexistente o meramente conclusivo; "
                "la contraparte opondrá excepción de ineptitud del libelo por falta de determinación circunstanciada."
            )
        if not any(w in t_lower for w in ["documental", "testigos", "pericial", "confesional", "oficios", "art. 1698", "medios de prueba"]):
            hallazgos_importantes.append(
                "[RIESGO PROBATORIO — Art. 1698 Código Civil] No se vinculan las afirmaciones fácticas con "
                "medios de prueba específicos (instrumentos, testigos, peritajes u oficios)."
            )

        # 4. Control de Caducidad, Prescripción y Patrocinio (Ley 18.120)
        if not any(w in t_lower for w in ["plazo", "días hábiles", "oportunidad", "temporaneidad", "prescripción", "caducidad"]):
            hallazgos_importantes.append(
                "[CONTROL DE ADMISIBILIDAD Y CADUCIDAD] El escrito no acredita expresamente el cómputo de "
                "oportunidad procesal o interrupción civil de la prescripción."
            )
        if not any(w in t_lower for w in ["patrocinio", "poder", "ley 18.120", "abogado habilitado"]):
            hallazgos_menores.append(
                "[APERCIBIMIENTO LEY N.° 18.120] Falta designación expresa de abogado patrocinante y apoderado "
                "habilitado para la tramitación en la Oficina Judicial Virtual (Ley N.° 20.886)."
            )

        veredicto = "APROBADO PARA FIRMA (PASS)" if not hallazgos_bloqueantes else "RECHAZADO — REQUIERE SUBSANACIÓN (FAIL)"
        lineas = [
            "### 🐠 DICTAMEN CONTRADICTORIO DE CONTEXTO CERO (MODELO ELEPHANT-GOLDFISH)",
            "**Rol del Auditor:** Ministro Relator / Contraparte Litigante (Aislamiento de Contexto)",
            f"**Veredicto de Admisibilidad:** **{veredicto}**\n",
            "#### 🚨 Hallazgos Bloqueantes (Excepciones y Admisibilidad):",
        ]
        if hallazgos_bloqueantes:
            lineas.extend(f"- {h}" for h in hallazgos_bloqueantes)
        else:
            lineas.append("- Sin vicios bloqueantes de admisibilidad o ineptitud del libelo detectados.")

        lineas.append("\n#### ⚠️ Observaciones Sustantivas e Importantes:")
        if hallazgos_importantes:
            lineas.extend(f"- {h}" for h in hallazgos_importantes)
        else:
            lineas.append("- Coherencia fáctica, probatoria y de oportunidad procesal verificada.")

        lineas.append("\n#### 📎 Observaciones Formales Menores:")
        if hallazgos_menores:
            lineas.extend(f"- {h}" for h in hallazgos_menores)
        else:
            lineas.append("- Formalidades de patrocinio y tramitación digital conformes.")

        return "\n".join(lineas)

    def critique(
        self,
        text: str,
        provider: Optional[str] = None,
        api_key: str = "",
        model: str = "",
        modo: str = "5d",
    ) -> Dict[str, Any]:
        """Ejecuta una auditoría forense completa sobre el texto legal provisto ('5d' o 'goldfish')."""
        if not text or not text.strip():
            return {"error": "El texto para auditar no puede estar vacío."}

        prov = (provider or LegalChatEngine.detect_provider()).lower().strip()
        modo_norm = (modo or "5d").lower().strip()

        # Si opera bajo el motor soberano por defecto (100% open source y sin API keys):
        if prov in ("soberano", "local"):
            if modo_norm in ("goldfish", "contradictorio", "adversarial"):
                critique_text = (
                    self.critique_goldfish_local(text)
                    + "\n\n---\n\n"
                    + self.critique_soberano_local(text)
                )
            else:
                critique_text = self.critique_soberano_local(text)
            return {
                "documentLength": len(text),
                "modo": modo_norm,
                "critique": critique_text,
                "provider": "soberano",
                "model": "soberano-v1-offline"
            }

        # Si el usuario solicitó explícitamente un proveedor externo o modelo LLM:
        es_goldfish = modo_norm in ("goldfish", "contradictorio", "adversarial")
        prompt_sistema = GOLDFISH_SYSTEM_PROMPT if es_goldfish else CRITIQUE_SYSTEM_PROMPT
        instruccion_usuario = (
            f"Audita este artefacto en aislamiento total de contexto (Modo Goldfish):\n\n{text}"
            if es_goldfish
            else f"Por favor realiza la auditoría de 5 dimensiones sobre este texto:\n\n{text}"
        )
        res = self.chat_engine.chat(
            user_message=instruccion_usuario,
            provider=prov,
            api_key=api_key,
            model=model,
            history=[],
            system_prompt=prompt_sistema
        )

        return {
            "documentLength": len(text),
            "modo": modo_norm,
            "critique": res.get("reply", res.get("error", "Error generando crítica")),
            "provider": res.get("provider"),
            "model": res.get("model")
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        engine = LegalCritiqueEngine()
        result = engine.critique(content)
        print(result["critique"])
    else:
        print("Uso: python critique.py <archivo_a_auditar.txt>")
