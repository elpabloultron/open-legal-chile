"""
Open Legal Chile — Entes Públicos de Chile y Validador Procesal de RUT
Módulo para validar y formatear RUTs chilenos con el algoritmo oficial Módulo 11,
y directorio exhaustivo de órganos del Estado, leyes orgánicas, facultades fiscalizadoras
y vías de impugnación administrativa y judicial.
"""

import re
from typing import Dict, Any, List, Optional


def calcular_dv_rut(cuerpo: int) -> str:
    """Calcula el dígito verificador oficial de un RUT chileno usando el algoritmo Módulo 11."""
    if cuerpo <= 0:
        return ""
    suma = 0
    multiplicador = 2

    for c in reversed(str(cuerpo)):
        suma += int(c) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1

    resto = suma % 11
    resultado = 11 - resto

    if resultado == 11:
        return "0"
    elif resultado == 10:
        return "K"
    else:
        return str(resultado)


def validar_rut(rut_str: str) -> Dict[str, Any]:
    """
    Valida un RUT chileno (personas naturales o jurídicas).
    Retorna el estado de validez, cuerpo numérico, dígito verificador y formato canónico.
    """
    if not rut_str or not isinstance(rut_str, str):
        return {"valido": False, "error": "RUT no proporcionado o formato inválido."}

    limpio = re.sub(r"[^0-9kK]", "", rut_str).upper()
    if len(limpio) < 2:
        return {"valido": False, "error": "RUT demasiado corto."}

    cuerpo_str = limpio[:-1]
    dv_ingresado = limpio[-1]

    if not cuerpo_str.isdigit():
        return {"valido": False, "error": "El cuerpo del RUT debe contener sólo dígitos."}

    cuerpo = int(cuerpo_str)
    dv_esperado = calcular_dv_rut(cuerpo)
    es_valido = dv_ingresado == dv_esperado

    # Formateo con puntos y guion: 12.345.678-K
    cuerpo_formateado = f"{cuerpo:,}".replace(",", ".")
    rut_canonico = f"{cuerpo_formateado}-{dv_ingresado}"

    # Clasificación preliminar por rango
    if cuerpo < 50_000_000:
        tipo_persona = "Persona Natural"
    elif cuerpo >= 50_000_000 and cuerpo < 100_000_000:
        tipo_persona = "Persona Jurídica / Empresa"
    else:
        tipo_persona = "Persona Jurídica Especial / Rango Superior"

    return {
        "valido": es_valido,
        "rut_canonico": rut_canonico,
        "rut_plano": f"{cuerpo}{dv_ingresado}",
        "cuerpo": cuerpo,
        "dv": dv_ingresado,
        "dv_esperado": dv_esperado,
        "tipo_persona_estimado": tipo_persona,
        "mensaje": "RUT válido conforme a algoritmo Módulo 11" if es_valido else f"Dígito verificador incorrecto. Se esperaba '{dv_esperado}' pero se recibió '{dv_ingresado}'."
    }


ENTES_PUBLICOS_CATALOGO: Dict[str, Dict[str, Any]] = {
    "sii": {
        "sigla": "SII",
        "nombre": "Servicio de Impuestos Internos",
        "ley_organica": "DFL N° 7 de 1980 (Ley Orgánica del SII) y Código Tributario (DL 830)",
        "ministerio": "Ministerio de Hacienda",
        "competencia": "Aplicación y fiscalización de todos los impuestos internos fiscales en Chile.",
        "facultades": [
            "Interpretar administrativamente las disposiciones tributarias (Art. 6 Letra A N° 1 y Art. 26 CT)",
            "Fiscalizar el cumplimiento tributario, liquidar y girar impuestos",
            "Sancionar infracciones tributarias que no tengan pena corporal",
            "Deducir querellas o denuncias por delitos tributarios (Art. 162 CT)"
        ],
        "recursos_administrativos": [
            {"nombre": "Reposición Administrativa Voluntaria (RAV)", "plazo": "30 días hábiles", "norma": "Art. 123 bis Código Tributario"},
            {"nombre": "Revisión de la Actuación Fiscalizadora (RAF)", "plazo": "Sin plazo fatal pero antes del cobro", "norma": "Circular N° 13 de 2010 SII"}
        ],
        "recursos_judiciales": [
            {"tribunal": "Tribunal Tributario y Aduanero (TTA)", "accion": "Reclamo General de Liquidaciones o Giros", "plazo": "90 días hábiles", "norma": "Ley N° 20.322 y Art. 124 CT"},
            {"tribunal": "Corte de Apelaciones respectiva", "accion": "Recurso de Apelación contra sentencia del TTA", "plazo": "15 días hábiles", "norma": "Art. 139 CT"}
        ]
    },
    "cmf": {
        "sigla": "CMF",
        "nombre": "Comisión para el Mercado Financiero",
        "ley_organica": "Decreto Ley N° 3.538 (creada por Ley N° 21.000)",
        "ministerio": "Ministerio de Hacienda",
        "competencia": "Supervisión y regulación del mercado de valores, seguros, bancos e instituciones financieras (integró a la ex SBIF) y entidades FinTech (Ley 21.521).",
        "facultades": [
            "Emitir Normas de Carácter General (NCG) y Circulares vinculantes",
            "Instruir investigaciones y formular cargos a través de la Unidad de Investigación",
            "Aplicar sanciones de censura, multas millonarias, revocación de autorizaciones y cancelación de registros",
            "Fijar estándares prudenciales de solvencia y Basilea III"
        ],
        "recursos_administrativos": [
            {"nombre": "Recurso de Reposición", "plazo": "5 días hábiles", "norma": "Art. 69 DL 3.538"}
        ],
        "recursos_judiciales": [
            {"tribunal": "Corte de Apelaciones de Santiago o del domicilio", "accion": "Reclamo de Ilegalidad", "plazo": "10 días hábiles desde la notificación", "norma": "Art. 70 DL 3.538"}
        ]
    },
    "cgr": {
        "sigla": "CGR",
        "nombre": "Contraloría General de la República",
        "ley_organica": "Ley N° 10.336 de Organización y Atribuciones de la Contraloría",
        "ministerio": "Órgano Constitucional Autónomo",
        "competencia": "Control de la legalidad de los actos de la Administración del Estado (Toma de Razón), fiscalización del ingreso e inversión de fondos fiscales y examen y juzgamiento de cuentas.",
        "facultades": [
            "Emitir dictámenes jurídicos vinculantes para toda la Administración activa",
            "Efectuar Toma de Razón de decretos y resoluciones que afecten la legalidad",
            "Instruir sumarios administrativos e investigaciones especiales",
            "Sustanciar el Juicio de Cuentas para hacer efectiva la responsabilidad civil de funcionarios"
        ],
        "recursos_administrativos": [
            {"nombre": "Solicitud de Reconsideración de Dictamen", "plazo": "No sujeto a plazo estricto pero aconsejable antes de 1 año", "norma": "Art. 9 y 10 Ley 10.336"}
        ],
        "recursos_judiciales": [
            {"tribunal": "Corte Suprema", "accion": "Recurso de Apelación en Juicio de Cuentas de Segunda Instancia", "plazo": "15 días", "norma": "Art. 119 Ley 10.336"},
            {"tribunal": "Corte de Apelaciones respectiva", "accion": "Recurso de Protección (Art. 20 CPR) por arbitrariedad o ilegalidad", "plazo": "30 días corridos", "norma": "Auto Acordado CS"}
        ]
    },
    "dt": {
        "sigla": "DT",
        "nombre": "Dirección del Trabajo",
        "ley_organica": "DFL N° 2 de 1967 del Ministerio del Trabajo y Previsión Social",
        "ministerio": "Ministerio del Trabajo y Previsión Social",
        "competencia": "Fiscalización de la legislación laboral, previsional y de seguridad y salud en el trabajo, y fijación del sentido y alcance de las leyes laborales.",
        "facultades": [
            "Emitir dictámenes de interpretación del Código del Trabajo vinculantes para los inspectores",
            "Fiscalizar empresas y cursar multas administrativas por infracciones laborales",
            "Promover la mediación laboral y la conciliación en comparendos individuales y colectivos",
            "Fiscalizar el cumplimiento de la Ley Karin (Ley N° 21.643)"
        ],
        "recursos_administrativos": [
            {"nombre": "Reconsideración Administrativa de Multa", "plazo": "30 días hábiles", "norma": "Art. 511 Código del Trabajo"}
        ],
        "recursos_judiciales": [
            {"tribunal": "Juzgado de Letras del Trabajo", "accion": "Reclamo Judicial de Multa", "plazo": "15 días hábiles administrativos", "norma": "Art. 503 Código del Trabajo"}
        ]
    },
    "sernac": {
        "sigla": "SERNAC",
        "nombre": "Servicio Nacional del Consumidor",
        "ley_organica": "Ley N° 19.496 sobre Protección de los Derechos de los Consumidores",
        "ministerio": "Ministerio de Economía, Fomento y Turismo",
        "competencia": "Defensa, información y educación de los consumidores y vigilancia del mercado en relaciones de consumo.",
        "facultades": [
            "Llevar a cabo Procedimientos Voluntarios Colectivos (PVC) con proveedores",
            "Interponer demandas colectivas en defensa del interés colectivo o difuso de los consumidores",
            "Fiscalizar el cumplimiento de la normativa de consumo y citar obligatoriamente a proveedores",
            "Denunciar infracciones ante los Juzgados de Policía Local"
        ],
        "recursos_administrativos": [
            {"nombre": "Reposición Administrativa", "plazo": "5 días hábiles", "norma": "Ley 19.880"}
        ],
        "recursos_judiciales": [
            {"tribunal": "Juzgado de Policía Local", "accion": "Denuncia infraccional y demanda civil de indemnización de perjuicios", "plazo": "2 años desde la infracción", "norma": "Art. 50 A Ley 19.496"}
        ]
    },
    "fne": {
        "sigla": "FNE",
        "nombre": "Fiscalía Nacional Económica",
        "ley_organica": "Decreto Ley N° 211 de 1973 (Fija normas para la defensa de la libre competencia)",
        "ministerio": "Ministerio de Economía (servicio descentralizado)",
        "competencia": "Investigación de todo hecho, acto o convención que tienda a impedir, restringir o entorpecer la libre competencia o que tienda a producir dichos efectos.",
        "facultades": [
            "Instruir investigaciones de oficio o por denuncia sobre conductas anticompetitivas",
            "Interponer requerimientos ante el TDLC solicitando multas, disolución de personas jurídicas o prohibición de contratar",
            "Revisar y autorizar o prohibir operaciones de concentración empresarial",
            "Ejercer facultades intrusivas (allanamientos, incautaciones, interceptaciones telefónicas autorizadas por la Corte de Apelaciones)",
            "Administrar el programa de Delación Compensada (Art. 39 bis DL 211)"
        ],
        "recursos_administrativos": [
            {"nombre": "Recurso de Revisión Especial de Operaciones de Concentración", "plazo": "10 días hábiles", "norma": "Art. 57 DL 211"}
        ],
        "recursos_judiciales": [
            {"tribunal": "Tribunal de Defensa de la Libre Competencia (TDLC)", "accion": "Revisión de resoluciones prohibitivas de concentración", "plazo": "10 días hábiles", "norma": "Art. 57 DL 211"},
            {"tribunal": "Corte Suprema", "accion": "Recurso de Reclamación contra sentencias y dictámenes del TDLC", "plazo": "10 días hábiles", "norma": "Art. 27 DL 211"}
        ]
    },
    "sma": {
        "sigla": "SMA",
        "nombre": "Superintendencia del Medio Ambiente",
        "ley_organica": "Ley N° 20.417 (LOSMA)",
        "ministerio": "Ministerio del Medio Ambiente",
        "competencia": "Fiscalización y sanción ambiental sobre instrumentos de gestión ambiental (RCA, normas de emisión, planes de descontaminación).",
        "facultades": [
            "Iniciar procedimientos sancionatorios ambientales por infracciones leves, graves y gravísimas",
            "Aprobar o rechazar Programas de Cumplimiento (PDC) presentados por infractores",
            "Aplicar sanciones de clausura, revocación de RCA y multas hasta 10.000 UTA",
            "Dictar medidas cautelares o provisionales pre y post sancionatorias"
        ],
        "recursos_administrativos": [
            {"nombre": "Recurso de Reposición Administrativa", "plazo": "5 días hábiles", "norma": "Art. 55 Ley 20.417"}
        ],
        "recursos_judiciales": [
            {"tribunal": "Tribunales Ambientales (1TA, 2TA o 3TA)", "accion": "Reclamación de Ilegalidad", "plazo": "15 días hábiles judiciales", "norma": "Art. 56 Ley 20.417 y Art. 17 N° 3 Ley 20.600"}
        ]
    },
    "cplt": {
        "sigla": "CPLT",
        "nombre": "Consejo para la Transparencia",
        "ley_organica": "Ley N° 20.285 sobre Acceso a la Información Pública",
        "ministerio": "Corporación autónoma de derecho público",
        "competencia": "Promover la transparencia de la función pública, fiscalizar el cumplimiento de las normas sobre transparencia activa y amparar el derecho de acceso a la información.",
        "facultades": [
            "Resolver los reclamos y amparos deducidos por denegación de información pública",
            "Instruir sumarios y aplicar sanciones de suspensión y multas a autoridades infractoras",
            "Dictar Instrucciones Generales vinculantes sobre transparencia activa y pasiva"
        ],
        "recursos_administrativos": [
            {"nombre": "Recurso de Reposición", "plazo": "5 días hábiles", "norma": "Ley 19.880"}
        ],
        "recursos_judiciales": [
            {"tribunal": "Corte de Apelaciones respectiva", "accion": "Reclamo de Ilegalidad", "plazo": "15 días corridos", "norma": "Art. 28 a 30 Ley 20.285"}
        ]
    }
}


def consultar_ente(query: str) -> Dict[str, Any]:
    """Busca y retorna la información legal completa de un ente público por sigla o nombre."""
    q = query.lower().strip()

    if q in ENTES_PUBLICOS_CATALOGO:
        return {"encontrado": True, "ente": ENTES_PUBLICOS_CATALOGO[q]}

    for data in ENTES_PUBLICOS_CATALOGO.values():
        if q == data["sigla"].lower() or q in data["nombre"].lower() or q in data["competencia"].lower():
            return {"encontrado": True, "ente": data}

    return {
        "encontrado": False,
        "query": query,
        "sugerencias": list(ENTES_PUBLICOS_CATALOGO.keys()),
        "error": f"Ente '{query}' no encontrado en el catálogo principal."
    }


def listar_entes() -> List[Dict[str, Any]]:
    """Retorna un resumen de todos los entes del Estado catalogados con sus siglas y leyes orgánicas."""
    return [
        {
            "sigla": v["sigla"],
            "nombre": v["nombre"],
            "ley_organica": v["ley_organica"],
            "ministerio": v["ministerio"]
        }
        for v in ENTES_PUBLICOS_CATALOGO.values()
    ]
