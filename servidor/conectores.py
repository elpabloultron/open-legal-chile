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
        "description": "Busca dictámenes vinculantes en la jurisprudencia administrativa de la Contraloría General de la República (CGR).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término de búsqueda jurídica (ej. 'confianza legitima contrata', 'probidad')"}
            },
            "required": ["query"]
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
        "description": "Busca dictámenes, pronunciamientos y doctrina laboral vinculante de la Dirección del Trabajo (DT).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Materia o número de dictamen (ej. 'acoso laboral ley karin', 'artículo 161', '344')"}
            },
            "required": ["query"]
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
        "description": "Busca dictámenes vinculantes y resolución de discrepancias técnicas y tarifarias en el Panel de Expertos de la Ley Eléctrica.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Materia o empresa en controversia (ej. 'peajes', 'coordinador electrico')"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "cmf_search_normativa",
        "description": "Busca Normas de Carácter General (NCG) y circulares de la Comisión para el Mercado Financiero (CMF).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término o número de NCG (ej. '461', 'gobierno corporativo', 'sostenibilidad')"}
            },
            "required": ["query"]
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
        "description": "Busca circulares e instrucciones oficiales del Director del Servicio de Impuestos Internos (SII) (2020-2026).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Materia tributaria o año (ej. 'iva servicios', 'gasto tributario', '2024')"}
            },
            "required": ["query"]
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
        "description": "Busca expedientes y procedimientos sancionatorios ambientales en el SNIFA de la Superintendencia del Medio Ambiente (SMA).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Nombre de empresa o titular sancionado (ej. 'Minera', 'Poblacion', 'D-160')"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "tdlc_search_jurisprudencia",
        "description": "Busca sentencias, resoluciones e instrucciones de carácter general del Tribunal de Defensa de la Libre Competencia (TDLC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Materia o empresa contenciosa (ej. 'colusion farmacias', 'abuso posicion dominante')"}
            },
            "required": ["query"]
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
        "description": "Desglosa estructuralmente una sentencia judicial chilena conforme al Art. 170 CPC (parte expositiva, considerandos de hecho/derecho, parte resolutiva, votos disidentes y costas Art. 144 CPC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "texto_sentencia": {"type": "string", "description": "Texto completo o extracto de la sentencia judicial"}
            },
            "required": ["texto_sentencia"]
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
        return _citas_en_items(cgr.search_jurisprudencia(args.get("query", "")), "CGR",
                               campos_clave=("nombre", "anio"), campo_texto="texto")
    elif name == "cgr_search_auditorias":
        return cgr.search_auditorias(args.get("query", ""))
    elif name == "dt_search_doctrina":
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
        return panel.search_dictamenes(args.get("query", ""))
    elif name == "cmf_search_normativa":
        return cmf.search_normativa(args.get("query", ""))
    elif name == "cmf_buscar_sanciones":
        q = args.get("query")
        if not q:
            return {"error": "El parámetro 'query' es obligatorio."}
        return cmf.search_sanciones(q)
    elif name == "sii_search_circulares":
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
        return sma.search_sancionatorios(nombre=args.get("query", ""))
    elif name == "tdlc_search_jurisprudencia":
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
        if not txt:
            return {"error": "El parámetro 'texto_sentencia' es obligatorio."}
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
