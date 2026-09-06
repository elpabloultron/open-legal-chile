"""
Open Legal Chile — Estudio de Títulos Inmobiliarios, CBR y Poderes Judiciales
Módulo forense para auditar la cadena de dominio decenal (10 años, Arts. 2510-2511 Código Civil),
revisar inscripciones registrales en el Conservador de Bienes Raíces (CBR) y
verificar personerías y facultades del mandato judicial (Ley 18.120 y Art. 7 CPC).
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional


class CBRTitleStudyEngine:
    """Motor de auditoría para estudios de títulos de dominio decenal e inscripciones CBR en Chile."""

    REGISTROS_CBR = {
        "propiedad": "Registro de Propiedad (Dominio, transferencias y transmisiones)",
        "hipotecas": "Registro de Hipotecas y Gravámenes (Hipotecas, usufructos, servidumbres, fideicomisos)",
        "interdicciones": "Registro de Interdicciones y Prohibiciones de Enajenar (Embargos, precautorias Art. 290 CPC)",
        "repertorio": "Libro de Repertorio (Prioridad registral y plazo de reparos)"
    }

    CONSERVADORES_PRINCIPALES = [
        "Santiago", "San Miguel", "Valparaíso", "Viña del Mar", "Concepción",
        "La Serena", "Antofagasta", "Temuco", "Rancagua", "Talca", "Chillán",
        "Puerto Montt", "Iquique", "Arica", "Punta Arenas", "Copiapó", "Coquimbo"
    ]

    def __init__(self, anio_actual: Optional[int] = None):
        self.anio_referencia = anio_actual or datetime.now().year

    def validar_inscripcion(self, fojas: int, numero: int, anio: int, conservador: str, registro: str = "propiedad") -> Dict[str, Any]:
        """Valida formalmente los datos de una inscripción registral en el Conservador."""
        errores = []
        registro_clean = registro.lower().strip()

        if fojas <= 0:
            errores.append("Fojas debe ser un número entero positivo.")
        if numero <= 0:
            errores.append("Número de inscripción debe ser mayor a 0.")
        if anio < 1857 or anio > self.anio_referencia + 1:
            errores.append(f"Año {anio} inválido (el Reglamento del CBR rige desde 1857).")

        if registro_clean not in self.REGISTROS_CBR:
            errores.append(f"Registro '{registro}' no reconocido. Válidos: {list(self.REGISTROS_CBR.keys())}")

        conservador_match = any(c.lower() in conservador.lower() for c in self.CONSERVADORES_PRINCIPALES)

        es_valida = len(errores) == 0
        cita_formal = f"Inscrito a fojas {fojas} N° {numero} del {self.REGISTROS_CBR.get(registro_clean, registro)} del CBR de {conservador}, correspondiente al año {anio}."

        return {
            "valida": es_valida,
            "fojas": fojas,
            "numero": numero,
            "anio": anio,
            "conservador": conservador,
            "registro": registro_clean,
            "registro_descripcion": self.REGISTROS_CBR.get(registro_clean, ""),
            "conservador_reconocido": conservador_match,
            "cita_formal": cita_formal,
            "errores": errores
        }

    def auditar_cadena_dominio(self, inscripciones: List[Dict[str, Any]], anios_requeridos: int = 10) -> Dict[str, Any]:
        """
        Audita una cadena de títulos verificando el plazo de prescripción decenal (Arts. 2510 y 2511 del Código Civil).
        Revisa la continuidad ininterrumpida de los títulos por al menos 10 años.
        """
        if not inscripciones:
            return {
                "aprobado": False,
                "cobertura_anios": 0,
                "anios_requeridos": anios_requeridos,
                "banderas_rojas": ["No se proporcionaron títulos de dominio para auditar."],
                "títulos_auditados": 0
            }

        ordenadas = sorted(inscripciones, key=lambda x: x.get("anio", 0), reverse=True)
        t_actual = ordenadas[0]
        t_mas_antiguo = ordenadas[-1]

        anio_mas_antiguo = t_mas_antiguo.get("anio", self.anio_referencia)

        cobertura = self.anio_referencia - anio_mas_antiguo
        banderas_rojas = []
        observaciones = []

        # 1. Regla Decenal (Arts. 2510 y 2511 Código Civil)
        if cobertura < anios_requeridos:
            banderas_rojas.append(
                f"La cadena de títulos sólo cubre {cobertura} años (desde {anio_mas_antiguo}). "
                f"No cumple con el plazo de 10 años de prescripción adquisitiva extraordinaria (Art. 2511 Código Civil)."
            )
        else:
            observaciones.append(f"Cumple con la cobertura decenal de saneamiento ({cobertura} años acumulados).")

        # 2. Análisis de continuidad en la tradición
        for idx in range(len(ordenadas) - 1):
            curr = ordenadas[idx]
            prev = ordenadas[idx + 1]

            enajenante_curr = curr.get("antecesor", "").strip().lower()
            propietario_prev = prev.get("propietario", "").strip().lower()

            if enajenante_curr and propietario_prev and enajenante_curr != propietario_prev:
                banderas_rojas.append(
                    f"Ruptura en la cadena de tradición entre {curr.get('anio')} y {prev.get('anio')}: "
                    f"El enajenante '{curr.get('antecesor')}' no coincide con el adquirente previo '{prev.get('propietario')}'."
                )

        # 3. Verificación de herencias y posesiones efectivas (Art. 688 Código Civil)
        for t in ordenadas:
            modo = t.get("modo_adquirir", "").lower()
            if "herencia" in modo or "sucesion" in modo:
                if not t.get("inscripcion_especial_herencia", False):
                    banderas_rojas.append(
                        f"Inscripción del año {t.get('anio')} adquirida por sucesión por causa de muerte sin acreditar "
                        f"Inscripción Especial de Herencia (Art. 688 N° 2 Código Civil). Impide disponer libremente de inmuebles."
                    )
                if not t.get("posesion_efectiva_inscrita", False):
                    banderas_rojas.append(
                        f"Falta acreditar inscripción del Auto o Resolución de Posesión Efectiva (Art. 688 N° 1 Código Civil) para el título de {t.get('anio')}."
                    )

            if t.get("hipotecas_vigentes"):
                for hip in t.get("hipotecas_vigentes", []):
                    banderas_rojas.append(f"Gravamen hipotecario no alzado en título {t.get('anio')}: {hip}")

            if t.get("prohibiciones_vigentes"):
                for proh in t.get("prohibiciones_vigentes", []):
                    banderas_rojas.append(f"Prohibición de enajenar o medida precautoria vigente en título {t.get('anio')}: {proh}")

        aprobado = len(banderas_rojas) == 0

        return {
            "aprobado": aprobado,
            "dictamen": "TÍTULOS AJUSTADOS A DERECHO" if aprobado else "TÍTULOS CON REPAROS / OBSERVACIONES CRÍTICAS",
            "cobertura_anios": cobertura,
            "anios_requeridos": anios_requeridos,
            "titulo_vigente": {
                "propietario": t_actual.get("propietario"),
                "fojas": t_actual.get("fojas"),
                "numero": t_actual.get("numero"),
                "anio": t_actual.get("anio"),
                "conservador": t_actual.get("conservador")
            },
            "total_titulos_auditados": len(ordenadas),
            "banderas_rojas": banderas_rojas,
            "observaciones": observaciones
        }

    def checklist_documentacion_cbr(self, tipo_inmueble: str = "urbano") -> Dict[str, Any]:
        """Entrega el checklist exhaustivo de documentos obligatorios para un estudio de títulos en Chile."""
        documentos = [
            {
                "documento": "Copia de inscripción de dominio con vigencia",
                "emisor": "Conservador de Bienes Raíces respectivo",
                "antiguedad_maxima_dias": 30,
                "finalidad": "Acreditar el dominio actual de la propiedad y descartar cancelaciones."
            },
            {
                "documento": "Certificado de Hipotecas, Gravámenes, Interdicciones y Prohibiciones de Enajenar (GP)",
                "emisor": "Conservador de Bienes Raíces (por 30 años)",
                "antiguedad_maxima_dias": 30,
                "finalidad": "Verificar la inexistencia de hipotecas, servidumbres, litigios, embargos o precautorias."
            },
            {
                "documento": "Certificado de No Expropiación Municipal",
                "emisor": "Dirección de Obras Municipales (DOM)",
                "antiguedad_maxima_dias": 90,
                "finalidad": "Verificar que el predio no esté afecto a utilidad pública o ensanche de calles (LGUC)."
            },
            {
                "documento": "Certificado de No Expropiación SERVIU",
                "emisor": "Servicio de Vivienda y Urbanización (SERVIU)",
                "antiguedad_maxima_dias": 90,
                "finalidad": "Acreditar que el inmueble no se encuentra afecto a expropiación por planes habitacionales."
            },
            {
                "documento": "Certificado de Número Municipal y Afectación a Utilidad Pública",
                "emisor": "Dirección de Obras Municipales (DOM)",
                "antiguedad_maxima_dias": 180,
                "finalidad": "Concordancia de la dirección física con la singularización del título."
            },
            {
                "documento": "Certificado de Pago de Contribuciones (Deuda Cero)",
                "emisor": "Tesorería General de la República (TGR)",
                "antiguedad_maxima_dias": 30,
                "finalidad": "Acreditar que no existen deudas tributarias por Impuesto Territorial (Ley N° 17.235)."
            },
            {
                "documento": "Certificado de Recepción Final de Obras de Edificación",
                "emisor": "Dirección de Obras Municipales (DOM)",
                "antiguedad_maxima_dias": None,
                "finalidad": "Acreditar que las construcciones se encuentran regularizadas (Art. 145 LGUC)."
            }
        ]

        if tipo_inmueble.lower() in ("condominio", "departamento"):
            documentos.extend([
                {
                    "documento": "Copia de Inscripción del Reglamento de Copropiedad",
                    "emisor": "Registro de Hipotecas y Gravámenes del CBR",
                    "antiguedad_maxima_dias": None,
                    "finalidad": "Conocer derechos y deberes conforme a la Ley N° 21.442 de Copropiedad Inmobiliaria."
                },
                {
                    "documento": "Certificado de Gastos Comunes al Día",
                    "emisor": "Administración del Condominio",
                    "antiguedad_maxima_dias": 30,
                    "finalidad": "Acreditar inexistencia de deudas de gastos comunes que gozan de privilegio legal."
                }
            ])

        return {
            "tipo_inmueble": tipo_inmueble,
            "total_documentos_requeridos": len(documentos),
            "documentos": documentos
        }


class JudicialPowerVerifier:
    """Verificador forense de comparecencia en juicio y personerías (Ley 18.120 y Arts. 6 y 7 CPC)."""

    FACULTADES_EXTRAORDINARIAS_CPC = {
        "desistirse": "Desistirse en primera instancia de la acción deducida",
        "aceptar_demanda": "Aceptar la demanda contraria",
        "absolver_posiciones": "Absolver posiciones (confesión judicial)",
        "renunciar_recursos": "Renunciar los recursos o los términos legales",
        "transigir": "Transigir (celebrar transacción judicial o extrajudicial)",
        "comprometer": "Comprometer (someter el conflicto a juicio arbitral)",
        "arbitradores": "Otorgar a los árbitros facultades de arbitradores",
        "aprobar_convenios": "Aprobar convenios (en procedimientos concursales)",
        "percibir": "Percibir (recibir dineros o valores derivados del juicio)"
    }

    PATRONES_FACULTADES = {
        "desistirse": r"desistir(?:se)?(?:\s+en\s+primera\s+instancia)?",
        "aceptar_demanda": r"aceptar\s+la\s+demanda(?:\s+contraria)?|allanar(?:se)?",
        "absolver_posiciones": r"absolver\s+posiciones",
        "renunciar_recursos": r"renunciar(?:\s+a)?\s+los\s+recursos(?:\s+o\s+t[eé]rminos\s+legales)?",
        "transigir": r"transigir",
        "comprometer": r"comprometer",
        "arbitradores": r"facultades\s+de\s+arbitradores",
        "aprobar_convenios": r"aprobar\s+convenios",
        "percibir": r"percibir"
    }

    def auditar_mandato(self, texto_mandato: str) -> Dict[str, Any]:
        """
        Audita el texto de un mandato judicial o patrocinio y poder otorgado en un escrito o escritura pública.
        Verifica menciones a la Ley 18.120, facultades ordinarias (Art. 7 inc. 1) y facultades del Art. 7 inc. 2 CPC.
        """
        texto_lower = texto_mandato.lower()

        tiene_patrocinio = bool(re.search(r"patrocinio|designo(?:\s+como)?\s+abogado\s+patrocinante|abogado\s+patrocinante|patrocina", texto_lower))
        tiene_poder = bool(re.search(r"confiero\s+poder|mandato\s+judicial|apoderado|procurador|otorgo\s+poder", texto_lower))
        menciona_ley_18120 = bool(re.search(r"18\.?120|comparecencia\s+en\s+juicio", texto_lower))

        facultades_ordinarias = bool(re.search(
            r"ambos\s+incisos|primer\s+inciso|facultades\s+ordinarias|tomar\s+parte\s+del\s+mismo\s+modo|todas\s+las\s+facultades",
            texto_lower
        ))

        facultades_detectadas = {}
        for key, patron in self.PATRONES_FACULTADES.items():
            encontrada = bool(re.search(patron, texto_lower))
            facultades_detectadas[key] = {
                "concedida": encontrada,
                "descripcion": self.FACULTADES_EXTRAORDINARIAS_CPC[key]
            }

        formula_ambos_incisos = bool(re.search(r"ambos\s+incisos\s+del\s+art[íi]culo\s+7|las\s+de\s+ambos\s+incisos", texto_lower))
        concedidas_count = sum(1 for f in facultades_detectadas.values() if f["concedida"])

        dictamen = []
        if not tiene_patrocinio:
            dictamen.append("No se individualiza expresamente abogado patrocinante con patente al día (Ley 18.120 Art. 1).")
        if not tiene_poder:
            dictamen.append("No se confiere expresamente mandato o poder judicial (Ley 18.120 Art. 2).")

        if formula_ambos_incisos and concedidas_count == 0:
            dictamen.append("Se menciona 'ambos incisos del Art. 7', pero la jurisprudencia exige mención expresa de las facultades del inciso 2° para actos trascendentes como percibir o transigir.")

        cumple_completo = tiene_patrocinio and tiene_poder and (concedidas_count >= 5 or formula_ambos_incisos)

        return {
            "cumple_formalidad_patrocinio_poder": tiene_patrocinio and tiene_poder,
            "menciona_ley_18120": menciona_ley_18120,
            "facultades_ordinarias_reconocidas": facultades_ordinarias or formula_ambos_incisos,
            "formula_ambos_incisos_utilizada": formula_ambos_incisos,
            "total_facultades_extraordinarias_concedidas": concedidas_count,
            "detalle_facultades_art_7_inc_2": facultades_detectadas,
            "advertencias": dictamen,
            "resumen_ejecutivo": "MANDATO JUDICIAL COMPLETO Y SUFICIENTE" if cumple_completo else "MANDATO RESTRINGIDO O CON DEFICIT DE FACULTADES EXPRESAS"
        }
