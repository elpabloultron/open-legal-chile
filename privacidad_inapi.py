"""
Open Legal Chile — Privacidad (Derechos ARCO) y Propiedad Intelectual (INAPI)
Herramientas especializadas para la Nueva Ley de Protección de Datos Personales
y tramitaciones de marcas y cartas de cese y desistimiento bajo la Ley 19.039 y Ley 17.336.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

class PrivacyARCOEngine:
    """Motor de gestión de solicitudes de Derechos ARCO bajo la legislación chilena de datos."""

    DERECHOS_VALIDOS = ["ACCESO", "RECTIFICACIÓN", "CANCELACIÓN", "OPOSICIÓN", "PORTABILIDAD"]

    @staticmethod
    def procesar_solicitud_arco(tipo_derecho: str, solicitante: str, rut: str, datos_solicitados: str) -> Dict[str, Any]:
        tipo = tipo_derecho.upper()
        if tipo not in PrivacyARCOEngine.DERECHOS_VALIDOS:
            tipo = "ACCESO"

        fecha_solicitud = datetime.now()
        plazo_legal_dias = 15
        fecha_limite = fecha_solicitud + timedelta(days=plazo_legal_dias)

        modelo_respuesta = (
            f"REF: RESPUESTA A SOLICITUD DE EJERCICIO DE DERECHO DE {tipo}\n"
            f"FECHA: {fecha_solicitud.strftime('%d de %B de %Y')}\n"
            f"A: {solicitante.upper()} (RUT: {rut})\n\n"
            f"Estimado/a titular:\n\n"
            f"En cumplimiento de la Ley de Protección de los Datos Personales de la República de Chile, "
            f"acusamos recibo de su solicitud de fecha {fecha_solicitud.strftime('%d/%m/%Y')} mediante la cual ejerce su derecho de {tipo} "
            f"respecto de los siguientes datos: '{datos_solicitados}'.\n\n"
            f"Se informa que su requerimiento ha sido admitido a tramitación. Conforme al artículo correspondiente, "
            f"esta entidad responderá de fondo en un plazo máximo de {plazo_legal_dias} días corridos, a más tardar el {fecha_limite.strftime('%d/%m/%Y')}.\n\n"
            f"Atentamente,\n"
            f"Oficial de Cumplimiento y Protección de Datos Personales"
        )

        return {
            "solicitante": solicitante,
            "rut": rut,
            "tipo_derecho": tipo,
            "plazo_legal_dias": plazo_legal_dias,
            "fecha_limite_respuesta": fecha_limite.strftime("%Y-%m-%d"),
            "modelo_oficial_respuesta": modelo_respuesta,
            "organismo_fiscalizador": "Agencia de Protección de Datos Personales de Chile",
            "estatus": "ADMITIDA A TRÁMITE"
        }


class INAPIEngine:
    """Motor para evaluación de factibilidad marcaria y cartas de cese y desistimiento."""

    NIZA_CLASSES_FREQ = {
        "9": "Software, aplicaciones, sistemas de IA y equipos electrónicos",
        "35": "Servicios de publicidad, gestión de negocios y comercialización online",
        "42": "Servicios científicos, tecnológicos, desarrollo de software y computación",
        "45": "Servicios jurídicos, de asesoría legal, auditoría y litigación"
    }

    @staticmethod
    def redactar_cease_and_desist(marca_afectada: str, titular: str, infractor: str, hechos_infraccion: str) -> Dict[str, Any]:
        """
        Redacta una carta notarial/formal de Cese y Desistimiento por infracción marcaria o de autor.
        """
        hoy = datetime.now().strftime("%d de %B de %Y")
        carta = (
            f"Santiago, {hoy}\n\n"
            f"A: {infractor.upper()}\n"
            f"DE: {titular.upper()} (Titular de derechos)\n"
            f"MATERIA: INTIMACIÓN FORMAL DE CESE Y DESISTIMIENTO — INFRACCIÓN MARCARIA Y PROPIEDAD INTELECTUAL\n\n"
            f"De nuestra consideración:\n\n"
            f"Nos dirigimos a usted en representación de {titular}, legítimo titular del signo distintivo '{marca_afectada}', "
            f"debidamente registrado y protegido ante el Instituto Nacional de Propiedad Industrial (INAPI) conforme a la Ley N° 19.039 "
            f"y la Ley N° 17.336 de Propiedad Intelectual.\n\n"
            f"Ha llegado a nuestro conocimiento que usted o su empresa ha estado utilizando el signo '{marca_afectada}' o variantes idénticas o confusamente similares, "
            f"específicamente: {hechos_infraccion}.\n\n"
            f"Dicho uso no consentido constituye una infracción flagrante a los derechos exclusivos de nuestro mandante, induciendo a error al público consumidor "
            f"y configurando actos de competencia desleal tipificados en la Ley N° 20.169.\n\n"
            f"POR TANTO, INTIMAMOS A USTED PARA QUE, DENTRO DEL PLAZO FATAL DE 5 DÍAS HÁBILES A CONTAR DE ESTA NOTIFICACIÓN:\n"
            f"1. Cese de manera inmediata y definitiva todo uso de la denominación '{marca_afectada}'.\n"
            f"2. Retire del comercio material publicitario, dominios web, cuentas de redes sociales o productos que ostenten el signo infractor.\n\n"
            f"Hacemos expresa reserva de iniciar las acciones civiles de indemnización de perjuicios y querellas penales tipificadas en el Título X de la Ley N° 19.039.\n\n"
            f"Atentamente,\n"
            f"{titular} — Dirección de Asuntos Legales y Propiedad Intelectual"
        )

        return {
            "marca": marca_afectada,
            "titular": titular,
            "infractor": infractor,
            "carta_completa": carta,
            "leyes_invocadas": ["Ley N° 19.039 (Propiedad Industrial)", "Ley N° 17.336 (Propiedad Intelectual)", "Ley N° 20.169 (Competencia Desleal)"],
            "plazo_intimacion_dias": 5
        }

    @staticmethod
    def evaluar_factibilidad_marca(marca_propuesta: str, clase_niza: str = "45") -> Dict[str, Any]:
        """
        Evalúa preliminarmente la viabilidad de registro de una marca en INAPI.
        """
        clase_desc = INAPIEngine.NIZA_CLASSES_FREQ.get(str(clase_niza), "Clase del Clasificador Internacional de Niza")
        nombre = marca_propuesta.strip()

        es_generica = nombre.lower() in ["abogados", "ley", "justicia", "tribunal", "derecho", "legal"]
        es_descriptiva = len(nombre.split()) > 4

        riesgo = "BAJO"
        motivos = []
        if es_generica:
            riesgo = "ALTO"
            motivos.append("El signo parece incurrir en la causal de irregistrabilidad del Art. 20 letra e) de la Ley 19.039 (signos genéricos o de uso común).")
        elif es_descriptiva:
            riesgo = "MEDIO"
            motivos.append("El signo puede considerarse descriptivo de los servicios prestados.")
        else:
            motivos.append("El signo posee distintividad de fantasía preliminar. Se sugiere solicitar búsqueda formal en la base de datos oficial de INAPI.")

        return {
            "marca_propuesta": marca_propuesta,
            "clase_niza": clase_niza,
            "descripcion_clase": clase_desc,
            "nivel_riesgo_preliminar": riesgo,
            "analisis_distintividad": motivos,
            "recomendacion": "Efectuar búsqueda fonética y de figuras en el portal web de INAPI (inapi.cl) antes del pago de derechos arancelarios."
        }
