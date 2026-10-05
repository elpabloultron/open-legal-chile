"""Herramientas de los conectores oficiales del Estado (BCN, CGR, DT, CNE, CMF, SII, SMA, TDLC, PJUD…)."""
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover — los bloques usan los objetos vivos de mcp_server
    from mcp_server import (
        CODIGOS,
        _citas_en_items,
        _con_citas,
        _url_codigo_bcn,
        bcn,
        cgr,
        cmf,
        cne,
        consultar_ente,
        datetime,
        dt,
        infoprobidad_client,
        json,
        panel,
        pjud,
        proveidos_engine,
        sentencia_engine,
        sii,
        sma,
        tdlc,
        validar_rut,
    )


def _refrescar() -> None:
    """Trae los nombres compartidos de mcp_server.py (helpers, clientes, motores).

    Corre en cada despacho: los bloques movidos usan los mismos objetos vivos del servidor,
    incluidas las sustituciones que hagan las pruebas con monkeypatch."""
    from config import servidor_actual
    _m = servidor_actual()
    _g = globals()
    _g.update({k: v for k, v in vars(_m).items() if k not in _PROPIOS})


TOOLS = [
    {
        "name": "bcn_get_codigo",
        "description": "Consulta artículos o estructura de los 9 Códigos de la República de Chile (civil, trabajo, cpc, cpp, penal, comercio, tributario, minería, aguas), la Constitución Política y el Código Sanitario, en la BCN.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "codigo": {"type": "string", "description": "Nombre del código (ej. 'civil', 'trabajo', 'cpc')"},
                "articulo": {"type": "string", "description": "Número de artículo a consultar (opcional)"}
            },
            "required": ["codigo"]
        }
    },
    {
        "name": "bcn_get_ley",
        "description": "Consulta el texto oficial y vigente de una ley chilena por su número (ej. Ley 21.643 Karin, Ley 21.561 40 Horas, Ley 19.886 Compras Públicas).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "numero": {"type": "integer", "description": "Número de la ley"},
                "articulo": {"type": "string", "description": "Artículo específico (opcional)"}
            },
            "required": ["numero"]
        }
    },
    {
        "name": "bcn_get_ley_historica",
        "description": "Consulta el texto de una ley chilena vigente en una fecha histórica específica (YYYY-MM-DD) en la BCN para control de derecho intertemporal.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "numero": {"type": "integer", "description": "Número de la ley (ej. 21643)"},
                "fecha": {"type": "string", "description": "Fecha histórica en formato YYYY-MM-DD (ej. '2024-01-15')"},
                "articulo": {"type": "string", "description": "Artículo específico a consultar (opcional)"}
            },
            "required": ["numero", "fecha"]
        }
    },
    {
        "name": "bcn_get_codigo_historico",
        "description": "Consulta un Código de la República (civil, trabajo, cpc, penal, etc.) en la versión vigente a una fecha histórica (YYYY-MM-DD), con el historial real de versiones de LeyChile. Devuelve la versión efectiva, su enlace oficial y —si se pide— el texto del artículo a esa fecha. Ideal para ver cómo cambió una norma (p. ej. la jornada de 45 a 40 horas).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "codigo": {"type": "string", "description": "Nombre del código (ej. 'trabajo', 'civil', 'cpc')"},
                "fecha": {"type": "string", "description": "Fecha histórica en formato YYYY-MM-DD"},
                "articulo": {"type": "string", "description": "Artículo específico (opcional)"}
            },
            "required": ["codigo", "fecha"]
        }
    },
    {
        "name": "cgr_search_jurisprudencia",
        "description": "Busca dictámenes vinculantes en la jurisprudencia administrativa de la Contraloría General de la República (CGR). Permite buscar por término o analizar dictámenes individuales o en lote (doc_id/doc_ids), descargar PDF oficial firmado, convertir a Markdown canónico, ingestar en LegalGraphify y desglosar consideraciones relevantes por tema.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término de búsqueda jurídica (ej. 'confianza legitima contrata', 'probidad')"},
                "doc_id": {"type": "string", "description": "Código o número de dictamen CGR a buscar o analizar a fondo (ej. 'D286N26', 'E123456')"},
                "doc_ids": {"type": "array", "items": {"type": "string"}, "description": "Lista de códigos de dictámenes CGR para análisis en lote"},
                "tema_relevante": {"type": "string", "description": "Punto de derecho o tema controvertido para rankear y citar consideraciones específicas"},
                "descargar_formato": {"type": "string", "enum": ["pdf"], "description": "Descargar el PDF oficial firmado desde la CGR ('pdf')"},
                "convertir_a_md_y_graficar": {"type": "boolean", "default": False, "description": "Convierte a Markdown canónico e ingesta en el grafo LegalGraphify"}
            }
        }
    },
    {
        "name": "cgr_search_auditorias",
        "description": "Busca en el catálogo de más de 9.600 Informes Finales de Auditoría e investigaciones especiales de la Contraloría (CGR).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Entidad o materia auditada (ej. 'Municipalidad de Santiago', 'Hospital')"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "dt_search_doctrina",
        "description": "Busca dictámenes, pronunciamientos y doctrina laboral vinculante de la Dirección del Trabajo (DT). Permite buscar por materia o número, o analizar dictámenes individuales o en lote (numero/numeros/articleId), descargar PDF oficial, aplicar OCR forense si está escaneado, convertir a Markdown canónico, ingestar en LegalGraphify y desglosar consideraciones relevantes por tema.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Materia o número de dictamen (ej. 'acoso laboral ley karin', 'artículo 161', '344')"},
                "numero": {"type": "string", "description": "Número u orden de dictamen DT a analizar (ej. 'ORD. N° 344', '129517')"},
                "numeros": {"type": "array", "items": {"type": "string"}, "description": "Lista de dictámenes u ordinarios DT para análisis en lote"},
                "tema_relevante": {"type": "string", "description": "Punto laboral controvertido para rankear y citar la doctrina o consideración específica"},
                "descargar_formato": {"type": "string", "enum": ["pdf"], "description": "Descargar el PDF oficial adjunto ('pdf')"},
                "convertir_a_md_y_graficar": {"type": "boolean", "default": False, "description": "Convierte a Markdown canónico e ingesta en el grafo LegalGraphify"}
            }
        }
    },
    {
        "name": "cne_get_centrales_y_proyectos",
        "description": "Consulta el registro de centrales generadoras activas y proyectos energéticos en el SEA de la Comisión Nacional de Energía (CNE).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "region": {"type": "string", "description": "Región de Chile (opcional)"}
            }
        }
    },
    {
        "name": "panel_expertos_search",
        "description": "Busca dictámenes vinculantes y resolución de discrepancias técnicas y tarifarias en el Panel de Expertos de la Ley Eléctrica. Permite buscar por término o analizar dictámenes en lote/individuales, descargar PDF oficial, convertir a Markdown canónico, ingestar en LegalGraphify y desglosar consideraciones por tema.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Materia, número de discrepancia o empresa en controversia (ej. 'peajes', '12-2023')"},
                "numero": {"type": "string", "description": "Número de dictamen o discrepancia a analizar (ej. '12-2023')"},
                "numeros": {"type": "array", "items": {"type": "string"}, "description": "Lista de dictámenes o discrepancias para análisis en lote"},
                "tema_relevante": {"type": "string", "description": "Tema controvertido para rankear y citar la determinación técnica pertinente"},
                "descargar_formato": {"type": "string", "enum": ["pdf"], "description": "Descargar el PDF oficial firmado del dictamen ('pdf')"},
                "convertir_a_md_y_graficar": {"type": "boolean", "default": False, "description": "Convierte a Markdown canónico e ingesta en LegalGraphify"}
            }
        }
    },
    {
        "name": "cmf_search_normativa",
        "description": "Busca Normas de Carácter General (NCG) y circulares de la Comisión para el Mercado Financiero (CMF). Permite buscar por término o analizar normas en lote/individuales, descargar PDF oficial, convertir a Markdown canónico, ingestar en LegalGraphify y desglosar disposiciones por tema.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término o número de NCG (ej. '461', 'gobierno corporativo', 'sostenibilidad')"},
                "numero": {"type": "string", "description": "Número de NCG o resolución a analizar (ej. '461')"},
                "numeros": {"type": "array", "items": {"type": "string"}, "description": "Lista de números de NCG para análisis en lote"},
                "tema_relevante": {"type": "string", "description": "Punto de mercado o regulatorio controvertido para rankear y citar disposiciones específicas"},
                "descargar_formato": {"type": "string", "enum": ["pdf"], "description": "Descargar el PDF oficial de la norma ('pdf')"},
                "convertir_a_md_y_graficar": {"type": "boolean", "default": False, "description": "Convierte a Markdown canónico e ingesta en LegalGraphify"}
            }
        }
    },
    {
        "name": "cmf_buscar_sanciones",
        "description": "Busca en el registro oficial de Resoluciones Sancionatorias y procedimientos de sanción aplicados por la CMF.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Nombre de la entidad sancionada, infracción o número de resolución"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "sii_search_circulares",
        "description": "Busca circulares e instrucciones oficiales del Director del Servicio de Impuestos Internos (SII) (2020-2026). Permite buscar por término o analizar circulares en lote/individuales, descargar PDF oficial, convertir a Markdown canónico, ingestar en LegalGraphify y desglosar instrucciones por tema.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Materia tributaria o año (ej. 'iva servicios', 'gasto tributario', '2024')"},
                "numero": {"type": "string", "description": "Número de circular a analizar (ej. '45', '35')"},
                "numeros": {"type": "array", "items": {"type": "string"}, "description": "Lista de circulares para análisis en lote"},
                "tema_relevante": {"type": "string", "description": "Tema tributario controvertido para rankear y citar la instrucción pertinente"},
                "descargar_formato": {"type": "string", "enum": ["pdf"], "description": "Descargar el PDF oficial de la circular ('pdf')"},
                "convertir_a_md_y_graficar": {"type": "boolean", "default": False, "description": "Convierte a Markdown canónico e ingesta en LegalGraphify"}
            }
        }
    },
    {
        "name": "sii_buscar_resoluciones_y_oficios",
        "description": "Busca Resoluciones Exentas y Oficios Ordinarios de Jurisprudencia Administrativa del Director del SII (Art. 26 CT).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término de búsqueda tributaria o número de resolución/oficio"},
                "anios": {"type": "array", "description": "Años a consultar (por defecto 2023 a 2026)", "items": {"type": "integer"}}
            },
            "required": ["query"]
        }
    },
    {
        "name": "sii_oficios_por_anio",
        "description": "Lista la jurisprudencia administrativa del SII (oficios y pronunciamientos del Director) de un año, por serie (Renta, IVA, Otras normas), con el resumen oficial y la referencia normativa que cada uno cita.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "anio": {"type": "integer", "description": "Año a listar (por defecto, el año en curso)"}
            }
        }
    },
    {
        "name": "sii_descargar_oficio",
        "description": "Descarga el PDF de un oficio de la jurisprudencia administrativa del SII, identificándolo por su número y su fecha de publicación.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "numero": {"type": "string", "description": "Número del oficio tal como aparece en el listado (p. ej. 2407 o 0358)"},
                "fecha": {"type": "string", "description": "Fecha de publicación del oficio, formato dd/mm/aaaa"},
                "anio": {"type": "integer", "description": "Año del índice a consultar (por defecto, el año en curso)"},
                "destino": {"type": "string", "description": "Ruta donde guardar el PDF (opcional: si se omite, sólo se informa el tamaño descargado)"}
            },
            "required": ["numero", "fecha"]
        }
    },
    {
        "name": "sii_actos_regionales",
        "description": "Lista o busca los actos y resoluciones que las direcciones regionales y unidades del SII publican por año, con número, fecha, materia y enlace al PDF.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término de búsqueda o número del acto (opcional: sin él se listan los del año)"},
                "anio": {"type": "integer", "description": "Año a consultar (por defecto, el año en curso)"},
                "direccion": {"type": "string", "description": "Dirección regional o unidad (p. ej. 'valparaiso', 'centro', 'grandes contribuyentes', 'fiscalizacion')"},
                "limite": {"type": "integer", "description": "Máximo de resultados (por defecto 50)"}
            }
        }
    },
    {
        "name": "sii_convenios_internacionales",
        "description": "Consulta los convenios tributarios internacionales del SII (doble imposición, intercambio de información, transporte internacional y convención multilateral) por país, materia o documento relacionado.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "País, materia o documento relacionado (opcional: sin él se listan todos)"}
            }
        }
    },
    {
        "name": "sii_jurisprudencia_judicial",
        "description": "Busca sentencias de la jurisprudencia judicial del SII (Tribunales Tributarios y Aduaneros, Cortes de Apelaciones y Corte Suprema) por partes, materia, código, RUC o artículo citado, con filtros de fecha y tribunal.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Partes, materia, código de sentencia (p. ej. 112-2026), RUC o número de artículo"},
                "desde": {"type": "string", "description": "Fecha mínima, formato aaaa-mm-dd (opcional)"},
                "hasta": {"type": "string", "description": "Fecha máxima, formato aaaa-mm-dd (opcional)"},
                "tribunal": {"type": "string", "description": "Nombre del tribunal (opcional, p. ej. 'Corte Suprema')"},
                "limite": {"type": "integer", "description": "Máximo de resultados (por defecto 20)"}
            }
        }
    },
    {
        "name": "sma_search_sancionatorios",
        "description": "Busca expedientes y procedimientos sancionatorios ambientales en el SNIFA de la Superintendencia del Medio Ambiente (SMA). Permite analizar expedientes individuales o en lote, estructurar la formulación de cargos, convertir a Markdown canónico e ingestar en LegalGraphify.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Nombre de empresa o titular sancionado (ej. 'Minera', 'Poblacion', 'D-160')"},
                "expediente": {"type": "string", "description": "Rol de expediente SNIFA a analizar (ej. 'D-045-2023', 'D-160-2026')"},
                "expedientes": {"type": "array", "items": {"type": "string"}, "description": "Lista de expedientes SNIFA para análisis en lote"},
                "tema_relevante": {"type": "string", "description": "Punto ambiental controvertido para rankear y citar infracciones específicas"},
                "convertir_a_md_y_graficar": {"type": "boolean", "default": False, "description": "Convierte a Markdown canónico e ingesta en LegalGraphify"}
            }
        }
    },
    {
        "name": "tdlc_search_jurisprudencia",
        "description": "Busca sentencias, resoluciones e instrucciones de carácter general del Tribunal de Defensa de la Libre Competencia (TDLC). Permite analizar sentencias individuales o en lote, descargar PDF oficial, aplicar OCR forense si es necesario, convertir a Markdown canónico, ingestar en LegalGraphify y desglosar consideraciones y resolutivos por tema.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Materia o empresa contenciosa (ej. 'colusion farmacias', 'abuso posicion dominante')"},
                "numero": {"type": "string", "description": "Número de sentencia o resolución TDLC a analizar (ej. '216/2026', '180/2022')"},
                "numeros": {"type": "array", "items": {"type": "string"}, "description": "Lista de sentencias TDLC para análisis en lote"},
                "tema_relevante": {"type": "string", "description": "Punto controvertido de libre competencia para rankear y citar el resolutivo pertinente"},
                "descargar_formato": {"type": "string", "enum": ["pdf"], "description": "Descargar el PDF oficial firmado ('pdf')"},
                "convertir_a_md_y_graficar": {"type": "boolean", "default": False, "description": "Convierte a Markdown canónico e ingesta en LegalGraphify"}
            }
        }
    },
    {
        "name": "tdlc_buscar_icg_y_dictamenes",
        "description": "Busca en la jurisprudencia del TDLC: sentencias contenciosas, dictámenes no contenciosos e Instrucciones de Carácter General (ICG).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término de búsqueda, materia o empresa involucrada"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "pjud_search_jurisprudencia",
        "description": "Busca jurisprudencia en el corpus local cosechado —70.523 sentencias de la Corte Suprema de los últimos dos años, 966 del Tribunal Constitucional y los fallos rectores CS/TC— por carátula, materia, recurso, resultado y doctrina; insensible a acentos.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término de búsqueda (ej. 'confianza legitima 2 años', 'descuento afc despido', 'isapres')"},
                "sala": {"type": "string", "description": "Sala opcional (ej. 'Tercera', 'Cuarta', 'Primera')"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "pjud_analizar_sentencia",
        "description": "Desglosa estructuralmente sentencias judiciales chilenas conforme al Art. 170 CPC. Soporta fallos individuales o lotes (roles múltiples/línea jurisprudencial), descarga oficial en PDF/DOCX desde juris.pjud.cl, conversión a Markdown canónico, ingesta en LegalGraphify y ranking/citación de considerandos relevantes por tema.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "texto_sentencia": {"type": "string", "description": "Texto completo o extracto de una sentencia judicial (opcional si se especifica 'rol' o 'roles')"},
                "rol": {"type": "string", "description": "Rol de la causa judicial a buscar y analizar en vivo (ej. '14076-2026', '504-2026')"},
                "roles": {"type": "array", "items": {"type": "string"}, "description": "Lista de Roles de causas para análisis en lote y construcción de líneas jurisprudenciales (ej. ['14076-2026', '45123-2021'])"},
                "corte": {"type": "string", "enum": ["cs", "ca"], "default": "cs", "description": "Tribunal a consultar: 'cs' (Corte Suprema) o 'ca' (Cortes de Apelaciones)"},
                "tema_relevante": {"type": "string", "description": "Tema o punto controvertido del caso para rankear y citar el considerando pertinente (ej. 'descuento de AFC', 'confianza legítima')"},
                "descargar_formato": {"type": "string", "enum": ["pdf", "docx"], "description": "Formato de archivo oficial a descargar desde juris.pjud.cl ('pdf' o 'docx')"},
                "convertir_a_md_y_graficar": {"type": "boolean", "default": True, "description": "Si es True, convierte a Markdown canónico (sentencia2md) e ingesta en LegalGraphify"}
            }
        }
    },
    {
        "name": "pjud_interpretar_proveido",
        "description": "Interpreta el significado jurídico y las cargas procesales de proveídos frecuentes en la tramitación judicial de la OJV ('Téngase presente', 'Como se pide', 'Traslado', 'Autos para fallo').",
        "inputSchema": {
            "type": "object",
            "properties": {
                "texto_proveido": {"type": "string", "description": "Texto del proveído o resolución judicial breve"}
            },
            "required": ["texto_proveido"]
        }
    },
    {
        "name": "infoprobidad_get_dip",
        "description": "Descarga y analiza la Declaración de Intereses y Patrimonio (DIP) de una autoridad pública desde InfoProbidad (CGR/CPLT) por URL o identificador.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query_or_url": {"type": "string", "description": "URL de la declaración o ID numérico/hash (ej. '1698949')"}
            },
            "required": ["query_or_url"]
        }
    },
    {
        "name": "rut_validar_chile",
        "description": "Valida un RUT chileno de persona natural o jurídica usando el algoritmo oficial Módulo 11 y entrega su formato canónico.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rut": {"type": "string", "description": "RUT chileno a validar (con o sin puntos/guion)"}
            },
            "required": ["rut"]
        }
    },
    {
        "name": "entes_consultar_organo",
        "description": "Consulta la ley orgánica, facultades fiscalizadoras y vías de reclamo judicial/administrativo de órganos públicos (SII, CMF, CGR, DT, SERNAC, FNE, SMA, CPLT).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "organo": {"type": "string", "description": "Sigla o nombre del órgano público (ej. 'SII', 'CMF', 'DT', 'FNE')"}
            },
            "required": ["organo"]
        }
    },
]


def despachar(name: str, args: dict) -> Any:
    _refrescar()
    if name == "bcn_get_codigo":
        cod = args.get("codigo")
        if not cod:
            return {"error": "El parámetro 'codigo' es obligatorio (ej. 'civil', 'trabajo', 'cpc')."}
        dato = bcn.get_codigo(cod, args.get("articulo"))
        if isinstance(dato, dict) and dato.get("texto"):
            articulo = dato.get("articulo") or args.get("articulo") or ""
            ident = CODIGOS.get(str(cod).lower(), str(cod)) + (f", Art. {articulo}" if articulo else "")
            dato = _con_citas(dato, "BCN", ident, url=_url_codigo_bcn(str(cod).lower()))
        return dato
    elif name == "bcn_get_ley":
        try:
            raw = str(args.get("numero") or args.get("ley") or args.get("ley_numero") or "").strip()
            num = int(re.sub(r"[^\d]", "", raw) or 0)
        except (ValueError, TypeError):
            return {"error": f"Número de ley inválido: {args.get('numero')}"}
        if num <= 0:
            return {"error": "El número de ley debe ser un entero positivo (ej. 21643 o '21.643')."}
        art = args.get("articulo")
        dato = bcn.get_articulo_ley(num, art) if art else bcn.get_ley(num)
        if isinstance(dato, dict) and dato.get("texto"):
            ident = f"Ley N° {num}" + (f", Art. {art}" if art else "")
            url = (f"https://www.bcn.cl/leychile/navegar?idLey={num}" if art
                   else f"https://www.bcn.cl/leychile/navegar?idNorma={dato.get('normaId', '')}")
            dato = _con_citas(dato, "BCN", ident, url=url)
        return dato
    elif name == "bcn_get_ley_historica":
        raw = str(args.get("numero") or args.get("ley") or args.get("ley_numero") or "").strip()
        num = int(re.sub(r"[^\d]", "", raw) or 0)
        fecha = args.get("fecha")
        if not num or not fecha:
            return {"error": "Los parámetros 'numero' y 'fecha' (YYYY-MM-DD) son obligatorios."}
        return bcn.get_ley_historica(num, fecha, args.get("articulo"))
    elif name == "bcn_get_codigo_historico":
        cod = args.get("codigo")
        fecha = args.get("fecha")
        if not cod or not fecha:
            return {"error": "Los parámetros 'codigo' y 'fecha' (YYYY-MM-DD) son obligatorios."}
        return bcn.get_codigo_historico(cod, fecha, args.get("articulo"))
    elif name == "cgr_search_jurisprudencia":
        doc_id = args.get("doc_id")
        doc_ids = args.get("doc_ids")
        tema = args.get("tema_relevante")
        convertir_md = bool(args.get("convertir_a_md_y_graficar", False))
        descargar = args.get("descargar_formato")

        if doc_id or doc_ids or tema or convertir_md or descargar:
            lista_ids = []
            if doc_id:
                lista_ids.append(str(doc_id).strip())
            if isinstance(doc_ids, list):
                lista_ids.extend([str(d).strip() for d in doc_ids if str(d).strip()])
            if not lista_ids and args.get("query"):
                sr = cgr.search_jurisprudencia(args.get("query", ""))
                res_items = sr.get("resultados", []) if isinstance(sr, dict) else []
                lista_ids = [r.get("docId") for r in res_items[:3] if r.get("docId")]
            if lista_ids:
                return cgr.procesar_y_graficar_dictamenes(
                    lista_ids,
                    tema_relevante=tema,
                    convertir_a_md=convertir_md,
                    descargar_formato=descargar
                )
        return _citas_en_items(cgr.search_jurisprudencia(args.get("query", "")), "CGR",
                               campos_clave=("nombre", "anio"), campo_texto="texto")
    elif name == "cgr_search_auditorias":
        return cgr.search_auditorias(args.get("query", ""))
    elif name == "dt_search_doctrina":
        numero = args.get("numero") or args.get("article_id")
        numeros = args.get("numeros")
        tema = args.get("tema_relevante")
        convertir_md = bool(args.get("convertir_a_md_y_graficar", False))
        descargar = args.get("descargar_formato")

        if numero or numeros or tema or convertir_md or descargar:
            lista_ids = []
            if numero:
                lista_ids.append(str(numero).strip())
            if isinstance(numeros, list):
                lista_ids.extend([str(d).strip() for d in numeros if str(d).strip()])
            if not lista_ids and args.get("query"):
                sr_dt = dt.search_dictamenes(args.get("query", ""), limit=3)
                if isinstance(sr_dt, list):
                    lista_ids = [str(r.get("articleId") or r.get("numero")) for r in sr_dt if isinstance(r, dict) and (r.get("articleId") or r.get("numero"))]
            if lista_ids:
                return dt.procesar_y_graficar_dictamenes(
                    lista_ids,
                    tema_relevante=tema,
                    convertir_a_md=convertir_md,
                    descargar_formato=descargar
                )
        return _citas_en_items(dt.search_dictamenes(args.get("query", ""), limit=10), "Dictamen DT",
                               campos_clave=("titulo", "fecha"), campo_texto="materia")
    elif name == "cne_get_centrales_y_proyectos":
        region = (args.get("region") or "").strip()
        capacidad = cne.get_capacidad_instalada()
        proyectos = cne.get_proyectos_sea()
        if isinstance(capacidad, list) and region:
            r_lower = region.lower()
            capacidad = [c for c in capacidad if isinstance(c, dict) and r_lower in json.dumps(c, ensure_ascii=False).lower()]
        if isinstance(proyectos, list) and region:
            r_lower = region.lower()
            proyectos = [p for p in proyectos if isinstance(p, dict) and r_lower in json.dumps(p, ensure_ascii=False).lower()]
        cap_list = capacidad if isinstance(capacidad, list) else []
        proy_list = proyectos if isinstance(proyectos, list) else []
        return {
            "region": region or "todas",
            "centrales_total": len(cap_list),
            "centrales_muestra": cap_list[:15],
            "proyectos_sea_total": len(proy_list),
            "proyectos_sea_muestra": proy_list[:15]
        }
    elif name == "panel_expertos_search":
        numero = args.get("numero")
        numeros = args.get("numeros")
        tema = args.get("tema_relevante")
        convertir_md = bool(args.get("convertir_a_md_y_graficar", False))
        descargar = args.get("descargar_formato")
        if numero or numeros or tema or convertir_md or descargar:
            lista_ids = []
            if numero:
                lista_ids.append(str(numero).strip())
            if isinstance(numeros, list):
                lista_ids.extend([str(d).strip() for d in numeros if str(d).strip()])
            if not lista_ids and args.get("query"):
                sr_panel = panel.search_dictamenes(args.get("query", ""), max_pages=1)
                lista_ids = [str(d.get("numero")) for d in sr_panel[:3] if d.get("numero")]
            if lista_ids:
                return panel.procesar_y_graficar_panel(
                    lista_ids,
                    tema_relevante=tema,
                    convertir_a_md=convertir_md,
                    descargar_formato=descargar
                )
        return panel.search_dictamenes(args.get("query", ""))
    elif name == "cmf_search_normativa":
        numero = args.get("numero")
        numeros = args.get("numeros")
        tema = args.get("tema_relevante")
        convertir_md = bool(args.get("convertir_a_md_y_graficar", False))
        descargar = args.get("descargar_formato")
        if numero or numeros or tema or convertir_md or descargar:
            lista_ids = []
            if numero:
                lista_ids.append(str(numero).strip())
            if isinstance(numeros, list):
                lista_ids.extend([str(d).strip() for d in numeros if str(d).strip()])
            if not lista_ids and args.get("query"):
                sr_cmf = cmf.search_normativa(args.get("query", ""))
                lista_ids = [str(d.get("titulo")) for d in sr_cmf[:3] if isinstance(d, dict) and d.get("tipo") != "aviso" and d.get("titulo")]
            if lista_ids:
                return cmf.procesar_y_graficar_cmf(
                    lista_ids,
                    tema_relevante=tema,
                    convertir_a_md=convertir_md,
                    descargar_formato=descargar
                )
        return cmf.search_normativa(args.get("query", ""))
    elif name == "cmf_buscar_sanciones":
        q = args.get("query")
        if not q:
            return {"error": "El parámetro 'query' es obligatorio."}
        return cmf.search_sanciones(q)
    elif name == "sii_search_circulares":
        numero = args.get("numero")
        numeros = args.get("numeros")
        tema = args.get("tema_relevante")
        convertir_md = bool(args.get("convertir_a_md_y_graficar", False))
        descargar = args.get("descargar_formato")
        if numero or numeros or tema or convertir_md or descargar:
            lista_ids = []
            if numero:
                lista_ids.append(str(numero).strip())
            if isinstance(numeros, list):
                lista_ids.extend([str(d).strip() for d in numeros if str(d).strip()])
            if not lista_ids and args.get("query"):
                sr_sii = sii.search_circulares(args.get("query", ""))
                lista_ids = [str(d.get("numero") or d.get("titulo")) for d in sr_sii[:3] if isinstance(d, dict) and d.get("tipo") != "aviso" and (d.get("numero") or d.get("titulo"))]
            if lista_ids:
                return sii.procesar_y_graficar_sii(
                    lista_ids,
                    tema_relevante=tema,
                    tipo="circular",
                    convertir_a_md=convertir_md,
                    descargar_formato=descargar
                )
        return sii.search_circulares(args.get("query", ""))
    elif name == "sii_buscar_resoluciones_y_oficios":
        q = args.get("query")
        if not q:
            return {"error": "El parámetro 'query' es obligatorio."}
        return sii.search_resoluciones_y_oficios(q, args.get("anios"))
    elif name == "sii_oficios_por_anio":
        return sii.get_oficios_por_anio(int(args.get("anio") or datetime.now().year))
    elif name == "sii_descargar_oficio":
        numero = str(args.get("numero") or "").strip()
        fecha = str(args.get("fecha") or "").strip()
        if not numero or not fecha:
            return {"error": "Los parámetros 'numero' y 'fecha' son obligatorios."}
        anio = int(args.get("anio") or datetime.now().year)
        oficios = sii.get_oficios_por_anio(anio)
        # El listado trae números con ceros a la izquierda («0358»), así que se compara sin ellos.
        encontrado = next(
            (o for o in oficios
             if str(o.get("numero", "")).lstrip("0") == numero.lstrip("0")
             and str(o.get("fecha", "")).strip() == fecha),
            None,
        )
        if encontrado is None:
            return {"error": (
                f"No se encontró el oficio {numero} de {fecha} en el índice de {anio}. "
                "Usa sii_oficios_por_anio para ver los oficios disponibles de ese año."
            )}
        return sii.descargar_oficio(encontrado, destino=args.get("destino"))
    elif name == "sii_actos_regionales":
        anio = int(args.get("anio") or datetime.now().year)
        limite = int(args.get("limite") or 50)
        consulta = args.get("query")
        res_actos: Any
        if consulta:
            res_actos = sii.buscar_actos_regionales(str(consulta), anio=anio, direccion=args.get("direccion"))
        else:
            res_actos = sii.get_actos_direcciones_regionales(anio=anio, direccion=args.get("direccion"))
        return res_actos[:limite] if isinstance(res_actos, list) else res_actos
    elif name == "sii_convenios_internacionales":
        consulta = args.get("query")
        return sii.buscar_convenios(str(consulta)) if consulta else sii.get_convenios_internacionales()
    elif name == "sii_jurisprudencia_judicial":
        return sii.buscar_jurisprudencia_judicial(
            query=str(args.get("query") or ""),
            desde=args.get("desde"),
            hasta=args.get("hasta"),
            tribunal=args.get("tribunal"),
            limite=int(args.get("limite") or 20),
        )
    elif name == "sma_search_sancionatorios":
        exp = args.get("expediente")
        exps = args.get("expedientes")
        tema = args.get("tema_relevante")
        convertir_md = bool(args.get("convertir_a_md_y_graficar", False))
        descargar = args.get("descargar_formato")
        if exp or exps or tema or convertir_md:
            lista_ids = []
            if exp:
                lista_ids.append(str(exp).strip())
            if isinstance(exps, list):
                lista_ids.extend([str(d).strip() for d in exps if str(d).strip()])
            if not lista_ids and args.get("query"):
                sr = sma.search_sancionatorios(nombre=args.get("query", ""))
                res_items = sr.get("resultados", []) if isinstance(sr, dict) else []
                lista_ids = [r.get("expediente") for r in res_items[:3] if r.get("expediente")]
            if lista_ids:
                return sma.procesar_y_graficar_sma(
                    lista_ids,
                    tema_relevante=tema,
                    convertir_a_md=convertir_md,
                    descargar_formato=descargar
                )
        return sma.search_sancionatorios(nombre=args.get("query", ""))
    elif name == "tdlc_search_jurisprudencia":
        numero = args.get("numero")
        numeros = args.get("numeros")
        tema = args.get("tema_relevante")
        convertir_md = bool(args.get("convertir_a_md_y_graficar", False))
        descargar = args.get("descargar_formato")
        if numero or numeros or tema or convertir_md or descargar:
            lista_ids = []
            if numero:
                lista_ids.append(str(numero).strip())
            if isinstance(numeros, list):
                lista_ids.extend([str(d).strip() for d in numeros if str(d).strip()])
            if not lista_ids and args.get("query"):
                sr_tdlc = tdlc.search_jurisprudencia(args.get("query", ""), max_pages=1)
                lista_ids = [str(d.get("titulo")) for d in sr_tdlc[:3] if d.get("titulo")]
            if lista_ids:
                return tdlc.procesar_y_graficar_tdlc(
                    lista_ids,
                    tema_relevante=tema,
                    convertir_a_md=convertir_md,
                    descargar_formato=descargar
                )
        return tdlc.search_jurisprudencia(args.get("query", ""))
    elif name == "tdlc_buscar_icg_y_dictamenes":
        q = args.get("query")
        if not q:
            return {"error": "El parámetro 'query' es obligatorio."}
        return tdlc.search_jurisprudencia(q)
    elif name == "pjud_search_jurisprudencia":
        return pjud.search_jurisprudencia(args.get("query", ""), sala=args.get("sala"))
    elif name == "pjud_analizar_sentencia":
        txt = args.get("texto_sentencia")
        rol = args.get("rol")
        roles = args.get("roles")
        tema_relevante = args.get("tema_relevante")
        corte = args.get("corte", "cs")
        descargar_formato = args.get("descargar_formato")
        convertir_a_md_y_graficar = args.get("convertir_a_md_y_graficar", True)

        items_procesar = []
        if roles and isinstance(roles, list):
            items_procesar = roles
        elif rol:
            items_procesar = [rol]

        if items_procesar:
            return pjud.procesar_y_graficar_sentencias(
                roles_o_docs=items_procesar,
                corte=corte,
                tema_relevante=tema_relevante,
                convertir_a_md=convertir_a_md_y_graficar,
                descargar_formato=descargar_formato
            )

        if not txt:
            return {"error": "Debe especificar 'texto_sentencia', 'rol' o 'roles' para analizar."}

        if tema_relevante or convertir_a_md_y_graficar:
            doc_simulado = {
                "rol": "S-N",
                "tribunal": "Corte Suprema" if corte == "cs" else "Corte de Apelaciones",
                "texto_integral": txt
            }
            return pjud.procesar_y_graficar_sentencias(
                roles_o_docs=[doc_simulado],
                corte=corte,
                tema_relevante=tema_relevante,
                convertir_a_md=convertir_a_md_y_graficar
            )
        return sentencia_engine.parsear_sentencia(txt)
    elif name == "pjud_interpretar_proveido":
        txt = args.get("texto_proveido")
        if not txt:
            return {"error": "El parámetro 'texto_proveido' es obligatorio."}
        return proveidos_engine.interpretar_proveido(txt)
    elif name == "infoprobidad_get_dip":
        q_url = args.get("query_or_url")
        if not q_url:
            return {"error": "El parámetro 'query_or_url' es obligatorio."}
        return infoprobidad_client.get_declaracion(q_url)
    elif name == "rut_validar_chile":
        rut = args.get("rut")
        if not rut:
            return {"error": "El parámetro 'rut' es obligatorio."}
        return validar_rut(rut)
    elif name == "entes_consultar_organo":
        org = args.get("organo")
        if not org:
            return {"error": "El parámetro 'organo' es obligatorio."}
        return consultar_ente(org)
    return None


_PROPIOS = frozenset(globals())
