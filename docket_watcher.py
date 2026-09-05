"""
Open Legal Chile — Vigilante Procesal (Docket Watcher) y Radar Regulatorio
Monitorea resoluciones provistas en la OJV / Poder Judicial, detecta cargas procesales,
calcula plazos fatales en días hábiles (Art. 66 CPC) y audita publicaciones normativas.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

class DocketWatcherEngine:
    """Motor de análisis de resoluciones judiciales y cálculo de plazos fatales en Chile."""

    TRIGGERS = [
        {
            "patron": r"rec[ií]base\s+la\s+causa\s+a\s+prueba",
            "tipo_tramite": "AUTO DE PRUEBA / INTERLOCUTORIA DE PRUEBA",
            "plazos": [
                {"accion": "Reposición con apelación en subsidio", "dias_habiles": 3, "articulo": "Art. 319 CPC", "fatal": True},
                {"accion": "Presentar lista de testigos y minuta de puntos", "dias_habiles": 2, "articulo": "Art. 320 CPC", "fatal": True}
            ],
            "severidad": "CRÍTICA",
            "instruccion_abogado": "Notificada por el estado diario la interlocutoria de prueba, corren 3 días fatales para objetar los hechos sustanciales, pertinentes y controvertidos o apelar en subsidio."
        },
        {
            "patron": r"traslado",
            "tipo_tramite": "CONFERIMIENTO DE TRASLADO (INCIDENTE)",
            "plazos": [
                {"accion": "Evacuar traslado de la contraria", "dias_habiles": 3, "articulo": "Art. 89 CPC", "fatal": True}
            ],
            "severidad": "ALTA",
            "instruccion_abogado": "Tiene 3 días fatales para responder el incidente promovido por la contraparte; de lo contrario, el tribunal resolverá con el mérito de lo obrado."
        },
        {
            "patron": r"autos\s+para\s+fallo|c[ií]tese\s+a\s+las\s+partes\s+para\s+o[ií]r\s+sentencia",
            "tipo_tramite": "CITACIÓN A OÍR SENTENCIA",
            "plazos": [
                {"accion": "Plazo legal del tribunal para dictar sentencia definitiva", "dias_habiles": 60, "articulo": "Art. 162 CPC", "fatal": False}
            ],
            "severidad": "MEDIA",
            "instruccion_abogado": "Causa queda en estado de fallo. Precluye la facultad de las partes de presentar nuevos escritos o probanzas, salvo medidas para mejor resolver (Art. 159 CPC)."
        },
        {
            "patron": r"t[eé]ngase\s+por\s+contestada|evacuada\s+la\s+rebeld[ií]a",
            "tipo_tramite": "TÉRMINO DE LA ETAPA DE DISCUSIÓN",
            "plazos": [
                {"accion": "Llamado a conciliación obligatoria", "dias_habiles": 0, "articulo": "Art. 262 CPC", "fatal": False}
            ],
            "severidad": "MEDIA",
            "instruccion_abogado": "Evacuada la réplica y la dúplica, el tribunal debe convocar a audiencia de conciliación obligatoria antes de recibir la causa a prueba."
        },
        {
            "patron": r"conc[eé]dase\s+el\s+recurso\s+de\s+apelaci[oó]n",
            "tipo_tramite": "CONCESIÓN DE RECURSO DE APELACIÓN",
            "plazos": [
                {"accion": "Ingreso y tramitación en Corte de Apelaciones", "dias_habiles": 5, "articulo": "Ley 20.886 y Art. 200 CPC", "fatal": True}
            ],
            "severidad": "ALTA",
            "instruccion_abogado": "Concedida la apelación, se envía expediente electrónico a la I. Corte de Apelaciones respectiva. Revisar asignación de sala y certificado de ingreso."
        }
    ]

    @staticmethod
    def analizar_resolucion(resolucion_texto: str, procedimiento: str = "civil") -> Dict[str, Any]:
        """
        Analiza el texto de un proveído judicial, identifica las cargas procesales y los plazos fatales.
        """
        texto_limpio = resolucion_texto.strip().lower()
        detecciones = []

        for trig in DocketWatcherEngine.TRIGGERS:
            if re.search(trig["patron"], texto_limpio, re.IGNORECASE):
                detecciones.append(trig)

        if not detecciones:
            return {
                "encontrado": False,
                "mensaje": "Proveído de mero trámite o sin plazo fatal evidente (ej. 'Téngase presente' o 'Como se pide').",
                "texto_analizado": resolucion_texto[:200]
            }

        det = detecciones[0]
        return {
            "encontrado": True,
            "tipo_tramite": det["tipo_tramite"],
            "severidad": det["severidad"],
            "instruccion_abogado": det["instruccion_abogado"],
            "cargas_procesales_y_plazos": det["plazos"],
            "regla_computo": "Plazos de días del CPC son de días hábiles, suspendiéndose los feriados y domingos (Art. 66 CPC). En materia laboral y administrativa rigen reglas especiales de la Ley 19.880.",
            "alerta_plazo_fatal": any(p.get("fatal") for p in det["plazos"])
        }

    @staticmethod
    def radar_normativo_resumen(materia: str = "general", dias_atras: int = 15) -> Dict[str, Any]:
        """
        Simula y estructura una auditoría de vigilancia sobre las últimas publicaciones
        del Diario Oficial, dictámenes de la CGR y circulares del SII.
        """
        mat = materia.lower()
        alertas = []
        if "laboral" in mat or "general" in mat:
            alertas.append({
                "fuente": "Dirección del Trabajo / Diario Oficial",
                "norma": "Dictamen Ley Karin (N° 21.643)",
                "impacto": "Modifica protocolos de prevención de acoso laboral y sexual en empresas. Exige investigación en plazo máximo de 30 días."
            })
        if "administrativo" in mat or "general" in mat:
            alertas.append({
                "fuente": "Contraloría General de la República (CGR)",
                "norma": "Dictamen sobre Confianza Legítima en Contratas",
                "impacto": "Reitera criterio vinculante de renovación sucesiva por 2 años para exigir acto motivado."
            })
        if "tributario" in mat or "general" in mat:
            alertas.append({
                "fuente": "Servicio de Impuestos Internos (SII)",
                "norma": "Circular sobre Gastos Deducibles de Empresas",
                "impacto": "Aclara requisitos de correlación del gasto con el giro conforme al Art. 31 de la LIR."
            })

        return {
            "materia_auditada": materia,
            "periodo_dias": dias_atras,
            "total_alertas_detectadas": len(alertas),
            "alertas_regulatorias": alertas
        }

    @staticmethod
    def calcular_vencimiento_contrato(tipo_contrato: str, fecha_vencimiento: str, preaviso_dias: int = 60) -> Dict[str, Any]:
        """
        Calcula la ventana crítica para notificar término o desahucio de contratos.
        """
        try:
            exp_date = datetime.strptime(fecha_vencimiento, "%Y-%m-%d")
        except ValueError:
            return {"error": "Formato de fecha inválido. Utilice YYYY-MM-DD."}

        limite_aviso = exp_date - timedelta(days=preaviso_dias)
        hoy = datetime.now()
        dias_restantes_aviso = (limite_aviso - hoy).days

        return {
            "tipo_contrato": tipo_contrato,
            "fecha_termino": fecha_vencimiento,
            "dias_preaviso_requeridos": preaviso_dias,
            "fecha_limite_notificacion": limite_aviso.strftime("%Y-%m-%d"),
            "dias_para_enviar_aviso": dias_restantes_aviso,
            "estado": "EN PLAZO" if dias_restantes_aviso > 15 else ("URGENTE" if dias_restantes_aviso >= 0 else "VENCIDO / RENOVADO AUTOMÁTICAMENTE"),
            "marco_legal": "Ley N° 18.101 (Arrendamiento urbano) o Código de Comercio según corresponda."
        }
