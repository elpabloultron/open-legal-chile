"""
Open Legal Chile — Motor Forense de Recursos de Protección
Generador estandarizado de Recursos de Protección y expedientes judiciales para las
Ilustrísimas Cortes de Apelaciones de Chile conforme al Auto Acordado de la Excma.
Corte Suprema (Acta N.° 94-2015, BCN ID 1080916), la Ley N.° 20.886 y normas RAE/ASALE.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union


class RecursoProteccionEngine:
    """Motor forense para la redacción, estructuración y validación de Recursos de Protección."""

    GARANTIAS_CATALOGO: Dict[str, Dict[str, Any]] = {
        "19_1": {
            "nombre": "Art. 19 N.° 1 de la Constitución Política de la República",
            "epigrafe": "Derecho a la vida y a la integridad física y psíquica",
            "fundamento": (
                "La garantía del artículo 19 N.° 1 asegura a todas las personas el derecho a la vida "
                "y a la integridad física y psíquica. El acto u omisión impugnado conculca directamente "
                "la indemnidad emocional y psíquica del recurrente, sometiéndole a una situación de zozobra, "
                "angustia y desprotección injustificada que amenaza de modo inminente su bienestar integral."
            ),
            "preferente": True
        },
        "19_2": {
            "nombre": "Art. 19 N.° 2 de la Constitución Política de la República",
            "epigrafe": "Igualdad ante la ley y prohibición de discriminación arbitraria",
            "fundamento": (
                "El artículo 19 N.° 2 consagra la igualdad ante la ley y prohíbe taxativamente que la autoridad "
                "o los particulares establezcan diferencias arbitrarias. En la especie, la recurrida ha dispensado "
                "un trato desigual, carente de justificación objetiva y desprovisto de proporcionalidad, discriminando "
                "al recurrente en relación con otros sujetos que se hallan en idéntica posición jurídica o institucional."
            ),
            "preferente": False
        },
        "19_3_5": {
            "nombre": "Art. 19 N.° 3 inciso quinto de la Constitución Política de la República",
            "epigrafe": "Debido proceso, prohibición de comisiones especiales y juez natural",
            "fundamento": (
                "El artículo 19 N.° 3, inciso quinto, preceptúa que nadie puede ser juzgado por comisiones "
                "especiales, sino por el tribunal que señalare la ley y que se hallare establecido por ésta con "
                "anterioridad a la perpetración del hecho. La actuación de la recurrida adolece de flagrante "
                "ilegalidad al constituirse en una verdadera comisión especial de facto, adoptando determinaciones "
                "sancionatorias o prohibitivas al margen de todo procedimiento racional y justo, preteriendo la "
                "garantía inalienable de audiencia previa, derecho a defensa y contradicción."
            ),
            "preferente": True
        },
        "19_4": {
            "nombre": "Art. 19 N.° 4 de la Constitución Política de la República",
            "epigrafe": "Respeto y protección a la vida privada y a la honra de la persona y su familia",
            "fundamento": (
                "El artículo 19 N.° 4 garantiza el respeto y protección a la vida privada y a la honra de la "
                "persona y su familia. La difusión indebida de acusaciones infundadas o sanciones no formalizadas "
                "por la recurrida afecta directamente la consideración, estima social e indemnidad moral de las partes."
            ),
            "preferente": False
        },
        "19_10": {
            "nombre": "Art. 19 N.° 10 de la Constitución Política de la República",
            "epigrafe": "Derecho a la educación y derecho preferente de los padres a educar a sus hijos",
            "fundamento": (
                "El artículo 19 N.° 10 tutela el derecho a la educación y consagra de modo expreso el derecho "
                "preferente y el deber correlativo de los padres de educar a sus hijos. La conducta de la recurrida "
                "impide o entorpece de modo flagrante el ejercicio de este derecho constitucional esencial, sustrayendo "
                "al menor de su entorno formativo o vulnerando los compromisos pedagógicos e institucionales vigentes."
            ),
            "preferente": False
        },
        "19_11": {
            "nombre": "Art. 19 N.° 11 de la Constitución Política de la República",
            "epigrafe": "Libertad de emitir opinión y de informar",
            "fundamento": (
                "El artículo 19 N.° 11 asegura la libertad de emitir opinión y la de informar, sin censura previa, "
                "en cualquier forma y por cualquier medio, respondiendo de los delitos y abusos cometidos en el "
                "ejercicio de estas libertades."
            ),
            "preferente": False
        },
        "19_12": {
            "nombre": "Art. 19 N.° 12 de la Constitución Política de la República",
            "epigrafe": "Derecho de reunión pacífica sin permiso previo",
            "fundamento": (
                "El artículo 19 N.° 12 garantiza el derecho a reunirse pacíficamente sin permiso previo y sin armas."
            ),
            "preferente": False
        },
        "19_15": {
            "nombre": "Art. 19 N.° 15 de la Constitución Política de la República",
            "epigrafe": "Derecho de asociación",
            "fundamento": (
                "El artículo 19 N.° 15 asegura el derecho de asociarse sin permiso previo. La determinación lesiva "
                "impide la libre participación y permanencia en la corporación, club o entidad sin causa legal."
            ),
            "preferente": False
        },
        "19_16": {
            "nombre": "Art. 19 N.° 16 de la Constitución Política de la República",
            "epigrafe": "Libertad de trabajo y su libre elección",
            "fundamento": (
                "El artículo 19 N.° 16 consagra la libertad de trabajo y su protección. La determinación impugnada "
                "impone impedimentos de facto que privan o restringen indebidamente la actividad laboral o profesional."
            ),
            "preferente": False
        },
        "19_21": {
            "nombre": "Art. 19 N.° 21 de la Constitución Política de la República",
            "epigrafe": "Derecho a desarrollar cualquiera actividad económica",
            "fundamento": (
                "El artículo 19 N.° 21 reconoce el derecho a desarrollar cualquiera actividad económica que no sea "
                "contraria a la moral, al orden público o a la seguridad nacional, respetando las normas legales "
                "que la regulen."
            ),
            "preferente": False
        },
        "19_24": {
            "nombre": "Art. 19 N.° 24 de la Constitución Política de la República",
            "epigrafe": "Derecho de propiedad en sus diversas especies",
            "fundamento": (
                "El artículo 19 N.° 24 protege el derecho de propiedad sobre toda clase de bienes corporales e "
                "incorporales, incluyendo los derechos adquiridos válidamente nacidos de relaciones contractuales, "
                "matrículas, membresías o estatutos vigentes, los que no pueden ser conculcados por vías de hecho."
            ),
            "preferente": False
        }
    }

    ESTATUTOS_ESPECIALES: Dict[str, Dict[str, str]] = {
        "ninez_21430": {
            "titulo": "Ley N.° 21.430 sobre Garantías y Protección Integral de los Derechos de la Niñez y Adolescencia",
            "citas": "Artículos 7, 8, 11 y 12 de la Ley N.° 21.430",
            "texto": (
                "De conformidad con los artículos 7, 8, 11 y 12 de la Ley N.° 21.430, el Estado, las instituciones "
                "privadas y toda autoridad u organización están obligados a considerar primordialmente el interés "
                "superior del niño, niña o adolescente, garantizando su efectividad, el derecho a ser oído y la "
                "prohibición de toda forma de discriminación o menoscabo arbitrario. Toda medida que vulnere "
                "estos principios adolece de nulidad sustantiva por infracción a garantías de orden público tuteladas."
            )
        },
        "tea_21545": {
            "titulo": "Ley N.° 21.545 de Inclusión, Atención Integral y Protección de Personas con TEA",
            "citas": "Artículos 3, 4 y 18 de la Ley N.° 21.545",
            "texto": (
                "Al tenor de la Ley N.° 21.545, se garantiza el principio de inclusión social, respeto a la neurodivergencia "
                "y el deber irrenunciable de implementar ajustes razonables en ámbitos educativos, recreativos, formativos "
                "y comunitarios. Sancionar, excluir o marginar a una persona neurodivergente sin protocolo ni ajustes "
                "constituye un acto de discriminación arbitraria flagrante que vulnera el ordenamiento protectorio nacional."
            )
        },
        "deporte_19712_ds22": {
            "titulo": "Ley N.° 19.712 (Ley del Deporte) y Decreto Supremo N.° 22/2020 del Mindep",
            "citas": "Ley N.° 19.712 y Decreto Supremo N.° 22/2020 del Ministerio del Deporte",
            "texto": (
                "La Ley N.° 19.712 y el D.S. N.° 22/2020 del Mindep consagran el protocolo obligatorio para la prevención "
                "y sanción de conductas de acoso sexual, abuso sexual, discriminación y maltrato en la actividad deportiva. "
                "Cualquier sanción o exclusión adoptada por una entidad deportiva sin ajustarse a la normativa de debido "
                "proceso disciplinario federado carece de personería y validez jurídica."
            )
        },
        "denuncia_cpp": {
            "titulo": "Artículos 175 y 176 del Código Procesal Penal (Obligación de Denuncia)",
            "citas": "Artículos 175 letra e) y 176 del Código Procesal Penal",
            "texto": (
                "De conformidad con el artículo 175, letra e), del Código Procesal Penal, los directores, profesores "
                "y encargados de establecimientos educacionales o formativos tienen la obligación inexcusable de denunciar "
                "los delitos cometidos en el establecimiento o que afecten a menores dentro de las 24 horas siguientes, "
                "constituyendo una gravísima omisión ilegal silenciar irregularidades o desviar procedimientos disciplinarios."
            )
        }
    }

    @classmethod
    def compute_deadline(
        cls,
        fecha_acto: Union[str, date],
        fecha_interposicion: Optional[Union[str, date]] = None
    ) -> Dict[str, Any]:
        """
        Calcula y certifica el cumplimiento del plazo fatal de 30 días corridos
        conforme al Numeral 1.° del Auto Acordado CS (Acta N.° 94-2015).
        """
        if isinstance(fecha_acto, str):
            f_acto = datetime.strptime(fecha_acto, "%Y-%m-%d").date()
        else:
            f_acto = fecha_acto

        if fecha_interposicion is None:
            f_interp = date.today()
        elif isinstance(fecha_interposicion, str):
            f_interp = datetime.strptime(fecha_interposicion, "%Y-%m-%d").date()
        else:
            f_interp = fecha_interposicion

        delta_dias = (f_interp - f_acto).days
        es_tempestivo = (delta_dias >= 0) and (delta_dias <= 30)
        es_extemporaneo = delta_dias > 30

        fecha_acto_formateada = f_acto.strftime("%d de %B de %Y")
        meses = {
            "January": "enero", "February": "febrero", "March": "marzo",
            "April": "abril", "May": "mayo", "June": "junio",
            "July": "julio", "August": "agosto", "September": "septiembre",
            "October": "octubre", "November": "noviembre", "December": "diciembre"
        }
        for eng, esp in meses.items():
            fecha_acto_formateada = fecha_acto_formateada.replace(eng, esp)

        if es_tempestivo:
            clausula = (
                f"El presente recurso se interpone estrictamente dentro del plazo fatal de treinta días corridos "
                f"establecido en el Numeral 1.° del Auto Acordado de la Excma. Corte Suprema sobre Tramitación y "
                f"Fallo del Recurso de Protección de las Garantías Constitucionales (Acta N.° 94-2015), toda vez "
                f"que el acto u omisión lesivo se ejecutó o se tomó conocimiento fehaciente del mismo con fecha "
                f"{fecha_acto_formateada} (a la fecha de ingreso han transcurrido exactamente {delta_dias} días corridos)."
            )
        else:
            clausula = (
                f"ADVERTENCIA PROCESAL DE EXTEMPORANEIDAD: El plazo de 30 días corridos computado desde la fecha "
                f"{fecha_acto_formateada} arroja {delta_dias} días transcurridos. Si existen actos de tracto sucesivo "
                f"o conocimiento posterior, debe justificarse la fecha de conocimiento cierto."
            )

        return {
            "fecha_acto": str(f_acto),
            "fecha_interposicion": str(f_interp),
            "dias_transcurridos": delta_dias,
            "es_tempestivo": es_tempestivo,
            "es_extemporaneo": es_extemporaneo,
            "clausula_plazo": clausula
        }

    @classmethod
    def format_presuma_recurso_proteccion(
        cls,
        tribunal: str,
        recurrente_nombre: str,
        recurrente_run: str,
        recurrente_domicilio: str,
        recurrente_email: str,
        recurrido_nombre: str,
        recurrido_rut: Optional[str] = None,
        recurrido_domicilio: Optional[str] = None,
        recurrido_email: Optional[str] = None,
        representante_legal: Optional[str] = None,
        representado_nombre: Optional[str] = None,
        representado_run: Optional[str] = None,
        quinto_otrosi_titulo: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Formatea la presuma y suma formal para la Oficina Judicial Virtual (OJV)
        evitando el colapso de texto mediante saltos de línea discretos (<br/> y preformateo).
        """
        if representado_nombre:
            rec_line = f"{recurrente_nombre.upper()} (por sí y en representación legal de {representado_nombre.upper()})"
            run_line = f"{recurrente_run} (RUN representado: {representado_run or 'Se acreditará'})"
        else:
            rec_line = recurrente_nombre.upper()
            run_line = recurrente_run

        dom_rec = f"{recurrente_domicilio} ({recurrente_email})"

        rut_rec = recurrido_rut or "Se desconoce / No consta (Personalidad Jurídica inscrita en Registro Civil / Municipio)"
        dom_rdo = f"{recurrido_domicilio or 'Domicilio conocido en la comuna'} ({recurrido_email or 'correo electrónico por notificar'})"

        rep_line = representante_legal or "Representante legal registrado estatutariamente; individualizando además a representantes de hecho si existiere usurpación de funciones o directiva no regularizada"

        otrosies_suma_lines = [
            "EN LO PRINCIPAL: RECURSO DE PROTECCIÓN;",
            "PRIMER OTROSÍ: ACOMPAÑA DOCUMENTOS;",
            "EN EL SEGUNDO OTROSÍ: ORDEN DE NO INNOVAR;",
            "TERCER OTROSÍ: SOLICITUD QUE INDICA (COMPARECENCIA PERSONAL EN VIRTUD DEL ARTÍCULO 2.° DEL AUTO ACORDADO Y FORMA DE NOTIFICACIÓN ELECTRÓNICA);",
            "CUARTO OTROSÍ: SOLICITA OFICIOS A ORGANISMOS PÚBLICOS E INSTITUCIONES QUE INDICA;"
        ]
        if quinto_otrosi_titulo:
            otrosies_suma_lines.append(f"QUINTO OTROSÍ: {quinto_otrosi_titulo.upper()};")

        suma_block = "\n".join(otrosies_suma_lines)
        suma_block_html = "<br/>\n".join(otrosies_suma_lines)

        presuma_txt = f"""TRIBUNAL : {tribunal}
MATERIA  : RECURSO DE PROTECCIÓN

RECURRENTE : {rec_line}
C.I. / RUN : {run_line}
DOMICILIO  : {dom_rec}

RECURRIDO  : {recurrido_nombre.upper()}
C.I. / RUT : {rut_rec}
DOMICILIO  : {dom_rdo}

REP LEGAL  : {rep_line}

{suma_block}

{tribunal.upper()}"""

        presuma_html = f"""<div style="font-family: monospace, Courier, sans-serif; font-size: 10pt; border: 1.5px solid #4a5568; padding: 14px 18px; line-height: 1.45; background-color: #f8fafc; color: #1a202c; margin-bottom: 24px;">
<strong>TRIBUNAL :</strong> {tribunal}<br/>
<strong>MATERIA  :</strong> RECURSO DE PROTECCIÓN<br/>
<br/>
<strong>RECURRENTE :</strong> {rec_line}<br/>
<strong>C.I. / RUN :</strong> {run_line}<br/>
<strong>DOMICILIO  :</strong> {dom_rec}<br/>
<br/>
<strong>RECURRIDO  :</strong> {recurrido_nombre.upper()}<br/>
<strong>C.I. / RUT :</strong> {rut_rec}<br/>
<strong>DOMICILIO  :</strong> {dom_rdo}<br/>
<br/>
<strong>REP LEGAL  :</strong> {rep_line}<br/>
<br/>
{suma_block_html}<br/>
</div>"""

        return {
            "plain_text": presuma_txt,
            "html": presuma_html,
            "suma": "; ".join([line.rstrip(";") for line in otrosies_suma_lines])
        }

    @classmethod
    def generate_full_brief(
        cls,
        tribunal: str,
        recurrente: Dict[str, Any],
        recurrido: Dict[str, Any],
        acto_lesivo: str,
        fecha_acto: Union[str, date],
        hechos: List[Union[str, Dict[str, str]]],
        garantias: List[str],
        estatutos_especiales: Optional[List[str]] = None,
        oni_data: Optional[Dict[str, Any]] = None,
        oficios: Optional[List[Dict[str, str]]] = None,
        anexos: Optional[List[Dict[str, str]]] = None,
        quinto_otrosi: Optional[Dict[str, str]] = None,
        petitorio_concreto: Optional[str] = None,
        fecha_interposicion: Optional[Union[str, date]] = None
    ) -> Dict[str, Any]:
        """
        Genera el escrito judicial completo estructurado en capítulos delimitados
        con rigor forense, aplicando las directrices del Auto Acordado CS y RAE/ASALE.
        """
        deadline_info = cls.compute_deadline(fecha_acto, fecha_interposicion)

        invoca_preferente = any(
            g in ["19_1", "19_3_5", "19 N.° 1", "19 N.° 3 inc. 5.°"]
            for g in garantias
        )

        quinto_titulo = quinto_otrosi.get("titulo") if quinto_otrosi else None
        presuma_dict = cls.format_presuma_recurso_proteccion(
            tribunal=tribunal,
            recurrente_nombre=recurrente.get("nombre", "RECURRENTE"),
            recurrente_run=recurrente.get("run", "XX.XXX.XXX-X"),
            recurrente_domicilio=recurrente.get("domicilio", "Domicilio en la comuna"),
            recurrente_email=recurrente.get("email", "contacto@correo.cl"),
            recurrido_nombre=recurrido.get("nombre", "PARTE RECURRIDA"),
            recurrido_rut=recurrido.get("rut"),
            recurrido_domicilio=recurrido.get("domicilio"),
            recurrido_email=recurrido.get("email"),
            representante_legal=recurrido.get("representante_legal"),
            representado_nombre=recurrente.get("representado_nombre"),
            representado_run=recurrente.get("representado_run"),
            quinto_otrosi_titulo=quinto_titulo
        )

        if recurrente.get("representado_nombre"):
            comparecencia = (
                f"{recurrente.get('nombre', '').upper()}, cédula nacional de identidad N.° {recurrente.get('run', '')}, "
                f"{recurrente.get('profesion_oficio', 'de profesión u oficio que se acreditará')}, "
                f"domiciliado en {recurrente.get('domicilio', '')}, correo electrónico {recurrente.get('email', '')}, "
                f"por sí y en representación legal de su hijo(a) menor de edad {recurrente.get('representado_nombre', '').upper()}, "
                f"cédula de identidad N.° {recurrente.get('representado_run', 'se acompañará')}, "
                f"a S.S.I. con el debido respeto comparezco y digo:"
            )
        else:
            comparecencia = (
                f"{recurrente.get('nombre', '').upper()}, cédula nacional de identidad N.° {recurrente.get('run', '')}, "
                f"{recurrente.get('profesion_oficio', 'de profesión u oficio que se acreditará')}, "
                f"domiciliado en {recurrente.get('domicilio', '')}, correo electrónico {recurrente.get('email', '')}, "
                f"a S.S.I. con el debido respeto comparezco y digo:"
            )

        objeto_text = (
            f"Que, de conformidad con lo establecido en el artículo 20 de la Constitución Política de la República "
            f"y lo dispuesto en el Auto Acordado de la Excma. Corte Suprema sobre Tramitación y Fallo del Recurso de "
            f"Protección de las Garantías Constitucionales (Acta N.° 94-2015), vengo en interponer formal RECURSO DE "
            f"PROTECCIÓN en contra de {recurrido.get('nombre', '').upper()}, ya individualizada, con ocasión del "
            f"acto u omisión arbitrario e ilegal consistente en: {acto_lesivo}.\n\n"
            f"{deadline_info['clausula_plazo']}"
        )

        hechos_lines = []
        for idx, h in enumerate(hechos, start=1):
            if isinstance(h, dict):
                texto_h = h.get("texto", "")
                anexo_ref = h.get("anexo")
                if anexo_ref:
                    hechos_lines.append(f"**{idx}.** {texto_h} (según consta en el **«{anexo_ref}»** acompañado a estos autos).")
                else:
                    hechos_lines.append(f"**{idx}.** {texto_h}")
            else:
                hechos_lines.append(f"**{idx}.** {str(h)}")
        hechos_text = "\n\n".join(hechos_lines)

        derecho_sections = [
            "### 1. Naturaleza Cautelar de la Acción Constitucional de Protección",
            (
                "La acción constitucional de protección consagrada en el artículo 20 de la Carta Fundamental "
                "constituye un arbitrio jurisdiccional extraordinario, expedito y de tutela inmediata, destinado "
                "a restablecer el imperio del derecho y brindar la debida protección ante actos u omisiones "
                "arbitrarios o ilegales que priven, perturben o amenacen el legítimo ejercicio de las garantías "
                "constitucionales taxativamente consagradas.\n\n"
                "Para la procedencia de esta acción, la jurisprudencia uniforme y constante de la Excma. Corte Suprema "
                "ha establecido que deben concurrir copulativamente: a) La existencia de una acción u omisión; "
                "b) Que dicha acción u omisión sea arbitraria (carente de sustento racional y proporcionalidad, caprichosa) "
                "o ilegal (contraria a la normativa constitucional, legal o reglamentaria vigente); y c) Que de ello se "
                "derive privación, perturbación o amenaza en el legítimo ejercicio de una o más garantías protegidas."
            )
        ]

        derecho_sections.append("### 2. Garantías Constitucionales Específicamente Conculcadas")
        for g_code in garantias:
            clean_code = g_code.replace(" ", "").replace("N.°", "").replace("Art.19", "19_").replace("inc.5.°", "5")
            matched_g = None
            for key, val in cls.GARANTIAS_CATALOGO.items():
                if key in clean_code or clean_code in key:
                    matched_g = val
                    break
            if not matched_g and g_code in cls.GARANTIAS_CATALOGO:
                matched_g = cls.GARANTIAS_CATALOGO[g_code]

            if matched_g:
                derecho_sections.append(f"#### {matched_g['nombre']} ({matched_g['epigrafe']})\n{matched_g['fundamento']}")
            else:
                derecho_sections.append(f"#### Garantía Constitucional Invocada: {g_code}\nLa actuación de la recurrida afecta directamente la garantía fundamental citada.")

        if estatutos_especiales:
            derecho_sections.append("### 3. Integración con Estatutos Legales de Protección Reforzada")
            for est in estatutos_especiales:
                if est in cls.ESTATUTOS_ESPECIALES:
                    item_est = cls.ESTATUTOS_ESPECIALES[est]
                    derecho_sections.append(f"#### {item_est['titulo']}\n{item_est['texto']}")
                else:
                    derecho_sections.append(f"#### Régimen Normativo Especial\n{est}")

        derecho_text = "\n\n".join(derecho_sections)

        preferencia_clausula = ""
        if invoca_preferente:
            preferencia_clausula = (
                " y declarar que la presente causa goza de tramitación y fallo preferente en un plazo fatal de "
                "dos días hábiles conforme al Numeral 10.° del Auto Acordado de la Excma. Corte Suprema,"
            )

        peticion_defecto = (
            "1. Acoger a tramitación el presente Recurso de Protección;\n"
            "2. Dejar sin efecto de forma inmediata y definitiva el acto u omisión arbitrario e ilegal impugnado;\n"
            "3. Ordenar el cese inmediato de toda medida o vía de hecho que prive, perturbe o amenace los derechos tutelados;\n"
            "4. Adoptar de inmediato todas las providencias y resguardos que S.S.I. estime pertinentes para restablecer el imperio del derecho; y\n"
            "5. Condenar a la recurrida al pago de las costas de la causa."
        )
        peticiones_texto = petitorio_concreto or peticion_defecto

        por_tanto_text = (
            f"POR TANTO, en mérito de lo expuesto, antecedentes acompañados, normas legales citadas y lo prescrito "
            f"en el artículo 20 de la Constitución Política de la República y el Auto Acordado de la Excma. Corte "
            f"Suprema sobre Tramitación y Fallo del Recurso de Protección de las Garantías Constitucionales (Acta N.° 94-2015),\n\n"
            f"PIDO A S.S.I.: Tener por interpuesto formal Recurso de Protección en contra de {recurrido.get('nombre', '').upper()}, "
            f"acogerlo a tramitación{preferencia_clausula} y, en definitiva, declarar que se acoge con expresa condena en costas, "
            f"disponiendo:\n\n{peticiones_texto}"
        )

        otrosies_list = []

        anexos_items = anexos or []
        doc_lines = []
        for a in anexos_items:
            num = a.get("num", "ANEXO")
            tit = a.get("title", "Documento")
            desc = a.get("desc", "")
            doc_lines.append(f"- **«{num}»**: {tit}. {desc}")

        if not doc_lines:
            doc_lines = ["- **«Anexo 1»**: Documentos fundantes de la acción constitucional de protección."]

        otrosies_list.append({
            "numero": "PRIMER OTROSÍ",
            "titulo": "ACOMPAÑA DOCUMENTOS",
            "contenido": (
                "Ruego a S.S.I. tener por acompañados, bajo el mérito de los apercibimientos legales y con citación, "
                "los siguientes documentos probatorios y antecedentes fundantes:\n\n" + "\n".join(doc_lines)
            )
        })

        oni = oni_data or {}
        solicita_oni = oni.get("solicita", True)
        if solicita_oni:
            fumus = oni.get(
                "fumus_boni_iuris",
                "Se encuentra plenamente acreditada la apariencia de buen derecho (fumus boni iuris) en virtud de los antecedentes fácticos expuestos y los instrumentos acompañados en el Primer Otrosí, los que dan cuenta fehaciente de la ilegalidad manifiesta de la actuación recurrida."
            )
            periculum = oni.get(
                "periculum_in_mora",
                "Existe un peligro grave e inminente en la demora (periculum in mora), toda vez que de mantenerse vigente el acto lesivo mientras se sustancia el presente recurso, se consolidará un daño irreparable sobre los derechos fundamentales invocados, tornando ilusoria la sentencia de fondo."
            )
            medida_susp = oni.get(
                "medida_suspension",
                f"La suspensión inmediata de los efectos del acto u omisión impugnado, ordenando a {recurrido.get('nombre', '').upper()} abstenerse de ejecutar cualquier medida lesiva mientras no se resuelva el recurso."
            )

            otrosies_list.append({
                "numero": "SEGUNDO OTROSÍ",
                "titulo": "ORDEN DE NO INNOVAR (ONI)",
                "contenido": (
                    f"De conformidad con lo dispuesto en el Numeral 3.° inciso final del Auto Acordado de la Excma. "
                    f"Corte Suprema sobre Tramitación y Fallo del Recurso de Protección, solicito a S.S.I. decretar ORDEN "
                    f"DE NO INNOVAR, disponiendo {medida_susp}.\n\n"
                    f"Lo anterior se funda de manera copulativa en:\n"
                    f"a) **Apariencia de buen derecho (fumus boni iuris):** {fumus}\n"
                    f"b) **Peligro en la demora (periculum in mora):** {periculum}\n\n"
                    f"POR TANTO, ruego a S.S.I. conceder la Orden de No Innovar impetrada en los términos solicitados."
                )
            })

        email_notif = recurrente.get("email", "contacto@correo.cl")
        otrosies_list.append({
            "numero": "TERCER OTROSÍ",
            "titulo": "SOLICITUD QUE INDICA (COMPARECENCIA PERSONAL EN VIRTUD DEL ARTÍCULO 2.° DEL AUTO ACORDADO Y FORMA DE NOTIFICACIÓN ELECTRÓNICA)",
            "contenido": (
                f"En virtud de lo dispuesto en el artículo 20 de la Constitución Política de la República y en el "
                f"Numeral 2.° del Auto Acordado de la Excma. Corte Suprema sobre Tramitación y Fallo del Recurso de "
                f"Protección (Acta N.° 94-2015), vengo en comparecer personalmente a la interposición y tramitación "
                f"de este recurso, sin requerir patrocinio de abogado ni mandato judicial. Asimismo, vengo en fijar "
                f"como medio formal y exclusivo para la práctica de todas las notificaciones electrónicas en esta "
                f"causa la siguiente casilla de correo electrónico: **{email_notif}**.\n\n"
                f"POR TANTO, ruego a S.S.I. tener presente la comparecencia personal y acceder a la forma de notificación señalada."
            )
        })

        oficios_items = oficios or []
        oficios_lines = []
        for of in oficios_items:
            org = of.get("organismo", "Organismo público")
            mat = of.get("materia", "Informar al tenor del recurso")
            oficios_lines.append(f"- A **{org}**, a fin de que informe sobre: {mat}.")

        if not oficios_lines:
            oficios_lines = [
                f"- A la recurrida **{recurrido.get('nombre', '').upper()}**, a fin de que remita todos los antecedentes y actas vinculadas al acto impugnado dentro de plazo de 8 días bajo apercibimiento legal."
            ]

        otrosies_list.append({
            "numero": "CUARTO OTROSÍ",
            "titulo": "SOLICITA OFICIOS A ORGANISMOS PÚBLICOS E INSTITUCIONES QUE INDICA",
            "contenido": (
                "De conformidad con lo dispuesto en el Numeral 5.° del Auto Acordado de la Excma. Corte Suprema, "
                "solicito a S.S.I. se sirva requerir informe a las siguientes entidades bajo el apercibimiento de "
                "prescindir de ellos o aplicar las medidas disciplinarias pertinentes si no fueren evacuados dentro de plazo:\n\n"
                + "\n".join(oficios_lines) +
                "\n\nPOR TANTO, ruego a S.S.I. oficiar conforme a lo solicitado."
            )
        })

        if quinto_otrosi:
            otrosies_list.append({
                "numero": "QUINTO OTROSÍ",
                "titulo": quinto_otrosi.get("titulo", "SOLICITUD ESPECIAL").upper(),
                "contenido": quinto_otrosi.get("contenido", "")
            })

        otrosies_md_sections = []
        for ot in otrosies_list:
            otrosies_md_sections.append(f"**{ot['numero']}: {ot['titulo']}**\n\n{ot['contenido']}")

        full_md = f"""{presuma_dict['html']}

# {presuma_dict['suma']}

**{tribunal.upper()}**

{comparecencia}

{objeto_text}

---

## I. LOS HECHOS (CRONOLOGÍA FUNDANTE)

{hechos_text}

---

## II. EL DERECHO Y GARANTÍAS CONSTITUCIONALES AFECTADAS

{derecho_text}

---

## POR TANTO,

{por_tanto_text}

---

{chr(10).join(otrosies_md_sections)}
"""

        return {
            "titulo": "RECURSO DE PROTECCIÓN",
            "tribunal": tribunal,
            "presuma_plain": presuma_dict["plain_text"],
            "presuma_html": presuma_dict["html"],
            "comparecencia": comparecencia,
            "objeto": objeto_text,
            "hechos": hechos_text,
            "derecho": derecho_text,
            "por_tanto": por_tanto_text,
            "otrosies": otrosies_list,
            "markdown_full": full_md,
            "deadline_info": deadline_info,
            "preferente": invoca_preferente
        }
