"""
Open Legal Chile — Asistencia Jurídica Social, Clínicas Universitarias y Lenguaje Claro
Herramientas para consultorios de la Corporación de Asistencia Judicial (CAJ),
traducción a Lenguaje Claro y control de calidad de escritos por el abogado supervisor.
"""

import re
from typing import Dict, Any, List, Optional

class ClinicaJuridicaEngine:
    """Motor de gestión para clínicas jurídicas y asistencia judicial comunitaria en Chile."""

    GLOSARIO_LENGUAJE_CLARO = {
        r"\bautos\s+para\s+fallo\b": "el juez ya terminó de escuchar a las partes y ahora tiene el expediente en su escritorio para escribir la sentencia final",
        r"\bt[eé]ngase\s+presente\b": "el tribunal leyó su documento y lo dejó registrado en la carpeta del juicio",
        r"\btraslado\b": "el juez le dio un plazo obligatorio a la otra parte (o a usted) para que responda por escrito lo que opina",
        r"\blitisconsorcio\b": "situación en que hay más de una persona demandando o demandada en el mismo juicio",
        r"\bpreclusi[oó]n\b": "se venció el plazo fatal establecido por la ley y ya no se puede realizar ese trámite",
        r"\ba\s+quo\b": "el juez de primera instancia que dictó la resolución inicial",
        r"\bad\s+quem\b": "la Corte de Apelaciones que revisará si el juez inicial se equivocó",
        r"\binterlocutoria\b": "resolución del juez que resuelve un problema importante del juicio sin terminarlo completamente"
    }

    @staticmethod
    def traducir_lenguaje_claro(texto_resolucion: str, destinatario: str = "usuario_caj") -> Dict[str, Any]:
        """
        Traduce una resolución judicial chilena densa a lenguaje claro y comprensible para el ciudadano.
        """
        explicacion_simple = texto_resolucion
        terminos_explicados = []

        for patron, reemplazo in ClinicaJuridicaEngine.GLOSARIO_LENGUAJE_CLARO.items():
            if re.search(patron, texto_resolucion, re.IGNORECASE):
                terminos_explicados.append({
                    "termino_legal": patron.replace(r"\b", "").replace(r"\s+", " "),
                    "significado_sencillo": reemplazo
                })

        # Resumen estructurado
        mensaje_ciudadano = (
            f"Estimado/a usuario/a:\n\n"
            f"El tribunal ha dictado una resolución en su causa. En palabras simples:\n"
            f"1. Lo que resolvió el tribunal: La causa avanza según el procedimiento legal.\n"
            f"2. Lo que usted debe saber: No se preocupe, su abogado/a de la Corporación de Asistencia Judicial está tramitando el expediente.\n"
            f"3. Términos jurídicos presentes: " + (", ".join([t["termino_legal"] for t in terminos_explicados]) if terminos_explicados else "Trámite regular sin complicaciones.") + "\n\n"
            f"Ante cualquier duda, acérquese a su consultorio de la CAJ con su cédula de identidad."
        )

        return {
            "texto_original": texto_resolucion,
            "terminos_tecnicos_identificados": terminos_explicados,
            "traduccion_lenguaje_claro": mensaje_ciudadano,
            "principio_rector": "Acceso a la Justicia y Derecho al Lenguaje Claro (Carta de Derechos de los Ciudadanos ante la Justicia en Chile)."
        }

    @staticmethod
    def generar_intake_social(materia: str, datos_usuario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera la ficha sociojurídica inicial de atención en consultorio de asistencia judicial.
        """
        mat = materia.lower()
        requisitos_documentales = []
        pasos_procesales = []

        if "alimentos" in mat:
            requisitos_documentales = [
                "Certificado de nacimiento del alimentario (para acreditar parentesco)",
                "Certificado de mediación previa frustrada (obligatorio bajo la Ley 19.968)",
                "Comprobantes de gastos de los menores (salud, educación, vivienda, vestuario)",
                "Antecedentes de ingresos o trabajo del demandado (si se conocen)"
            ]
            pasos_procesales = [
                "Verificar mediación previa frustrada",
                "Solicitar alimentos provisorios en el primer otrosí",
                "Fijar audiencia preparatoria"
            ]
        elif "precario" in mat:
            requisitos_documentales = [
                "Copia de inscripción de dominio con vigencia del Conservador de Bienes Raíces (CBR)",
                "Certificado de número municipal de la propiedad",
                "Constatación de testigos o de Carabineros sobre la ocupación por mera tolerancia"
            ]
            pasos_procesales = [
                "Redactar demanda de comodato precario (Art. 2195 inciso 2° CC)",
                "Juicio sumario civil (Art. 680 N° 6 CPC)"
            ]
        else:
            requisitos_documentales = [
                "Cédula de identidad vigente",
                "Registro Social de Hogares (RSH) para evaluación socioeconómica",
                "Documentos fundantes del hecho"
            ]
            pasos_procesales = ["Evaluación por abogado supervisor"]

        return {
            "ficha_atencion": {
                "materia": materia.upper(),
                "usuario": datos_usuario.get("nombre", "POR DETERMINAR"),
                "rut": datos_usuario.get("rut", "POR DETERMINAR"),
                "telefono": datos_usuario.get("telefono", "NO REGISTRA"),
                "tramo_rsh": datos_usuario.get("tramo_rsh", "VULNERABLE (HASTA 60%)"),
                "documentos_exigidos": requisitos_documentales,
                "ruta_procesal_sugerida": pasos_procesales
            },
            "estado_atencion": "ADMISIBLE PARA ASISTENCIA JUDICIAL GRATUITA",
            "ley_aplicable": "Ley N° 19.968 (Tribunales de Familia) o Código de Procedimiento Civil."
        }

    @staticmethod
    def auditar_borrador_supervisor(borrador_texto: str, tribunal: str = "Civil") -> Dict[str, Any]:
        """
        Audita formalmente el borrador de un escrito jurídico redactado por un pasante
        antes de la firma del abogado jefe de consultorio o tutor.
        """
        checklist = {}
        texto = borrador_texto.upper()

        # 1. Presuma OJV
        checklist["presuma_presente"] = any(k in texto for k in ["PROCEDIMIENTO:", "MATERIA:", "DEMANDANTE:", "DEMANDADO:"])
        # 2. Comparecencia y Ley 18.120
        checklist["patrocinio_poder"] = "PATROCINIO Y PODER" in texto or "LEY 18.120" in texto
        # 3. Peticiones concretas
        checklist["petitorio_por_tanto"] = "POR TANTO" in texto and "PIDO" in texto
        # 4. Fundamentos de derecho
        checklist["fundamentos_derecho"] = any(k in texto for k in ["CÓDIGO CIVIL", "CÓDIGO DEL TRABAJO", "C.P.C.", "LEY N°", "ARTÍCULO"])

        score = sum(1 for v in checklist.values() if v)
        aprobado = score >= 3

        observaciones = []
        if not checklist["presuma_presente"]:
            observaciones.append("Falta la presuma obligatoria con los códigos OJV de tramitación.")
        if not checklist["patrocinio_poder"]:
            observaciones.append("Debe incluir en el otrosí el patrocinio y poder conforme a la Ley N° 18.120 y Ley N° 20.886 de Tramitación Electrónica.")
        if not checklist["petitorio_por_tanto"]:
            observaciones.append("El petitorio no contiene la fórmula sacramental 'POR TANTO, A US. PIDO'.")

        return {
            "tribunal": tribunal,
            "auditoria_formal": checklist,
            "puntaje_formal": f"{score}/4",
            "aprobado_para_firma": aprobado,
            "observaciones_supervisor": observaciones if observaciones else ["Borrador cumple con los estándares formales requeridos para ingresar a la OJV."]
        }
