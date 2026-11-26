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

    TRIGGERS: List[Dict[str, Any]] = [
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
    def analizar_resolucion(
        resolucion_texto: str,
        procedimiento: str = "civil",
        fecha_notificacion: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analiza el texto de un proveído judicial, identifica las cargas procesales y los plazos fatales.
        """
        texto_limpio = resolucion_texto.strip().lower()
        detecciones = []

        for trig in DocketWatcherEngine.TRIGGERS:
            if re.search(str(trig["patron"]), texto_limpio, re.IGNORECASE):
                detecciones.append(trig)

        if not detecciones:
            return {
                "encontrado": False,
                "mensaje": "Proveído de mero trámite o sin plazo fatal evidente (ej. 'Téngase presente' o 'Como se pide').",
                "texto_analizado": resolucion_texto[:200]
            }

        det = detecciones[0]
        plazos = [dict(p) for p in det["plazos"]]
        if fecha_notificacion and str(fecha_notificacion).strip():
            from calculadoras_chile import calcular_plazo_procesal

            proc_low = str(procedimiento or "civil").lower()
            reg = "laboral" if "labor" in proc_low else ("administrativo" if "admin" in proc_low else "judicial_cpc")
            for p in plazos:
                dias = int(p.get("dias_habiles") or 0)
                if dias > 0:
                    calc = calcular_plazo_procesal(str(fecha_notificacion).strip(), dias, regimen=reg)
                    if not calc.get("error"):
                        p["fecha_vencimiento"] = calc["fecha_vencimiento"]
                        p["dia_semana_vencimiento"] = calc["dia_semana_vencimiento"]
                        p["estado"] = calc["estado"]
                        p["dias_corridos_restantes"] = calc["dias_corridos_restantes"]

        return {
            "encontrado": True,
            "tipo_tramite": det["tipo_tramite"],
            "severidad": det["severidad"],
            "instruccion_abogado": det["instruccion_abogado"],
            "cargas_procesales_y_plazos": plazos,
            "regla_computo": "Plazos de días del CPC son de días hábiles, suspendiéndose los feriados y domingos (Art. 66 CPC). En materia laboral y administrativa rigen reglas especiales de la Ley 19.880.",
            "alerta_plazo_fatal": any(isinstance(p, dict) and p.get("fatal") for p in det.get("plazos", []))
        }

    @staticmethod
    def radar_normativo_resumen(
        materia: str = "general",
        dias_atras: int = 15,
        consultar_diario_oficial: bool = False,
    ) -> Dict[str, Any]:
        """
        Simula y estructura una auditoría de vigilancia sobre las últimas publicaciones
        del Diario Oficial, dictámenes de la CGR y circulares del SII.

        Cuando ``consultar_diario_oficial=True``, consulta en línea (o desde caché)
        el sumario del Diario Oficial vía ``diario_oficial_consultar`` e incorpora sus
        publicaciones bajo la clave ``diario_oficial`` de forma retrocompatible.
        """
        mat = materia.lower()
        alertas: List[Dict[str, Any]] = []
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

        res_do: Optional[Dict[str, Any]] = None
        if consultar_diario_oficial:
            try:
                from diario_oficial_connector import diario_oficial_consultar

                q_do = "" if mat.strip() in ("", "general", "todas") else materia.strip()
                res_do = diario_oficial_consultar(query=q_do, limite=10)
                for item in res_do.get("resultados") or []:
                    cve = str(item.get("cve") or "").strip()
                    norma_txt = str(item.get("titulo") or "Publicación Diario Oficial")
                    if cve:
                        norma_txt = f"{norma_txt} (CVE {cve})"
                    alertas.append({
                        "fuente": "Diario Oficial de la República de Chile",
                        "norma": norma_txt,
                        "impacto": str(item.get("extracto") or item.get("seccion") or ""),
                        "fecha": str(item.get("fecha") or ""),
                        "seccion": str(item.get("seccion") or ""),
                        "cve": cve,
                        "url": str(item.get("url") or ""),
                    })
            except Exception as exc:  # noqa: BLE001 — degradación segura sin romper el radar
                res_do = {
                    "fuente": "Diario Oficial de la República de Chile",
                    "total": 0,
                    "resultados": [],
                    "sin_fuente_verificable": True,
                    "error": str(exc),
                }

        salida: Dict[str, Any] = {
            "materia_auditada": materia,
            "periodo_dias": dias_atras,
            "total_alertas_detectadas": len(alertas),
            "alertas_regulatorias": alertas,
        }
        if res_do is not None:
            salida["diario_oficial"] = res_do
        return salida

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
