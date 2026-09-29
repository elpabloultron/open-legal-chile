"""Herramientas forenses y pedagógicas (OCR, crítica, documentos, clínica, grados…)."""
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover — los bloques usan los objetos vivos de mcp_server
    from mcp_server import (
        LegalDocumentExporter,
        arco_engine,
        cbr_engine,
        clinica_engine,
        compiler,
        docket_engine,
        exporter,
        grado_engine,
        inapi_engine,
        ocr_engine,
        os,
        power_verifier,
        word_compiler,
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
        "name": "ocr_plan_documento",
        "description": "Recomienda —con razonamiento del sistema jurídico chileno— cómo extraer el texto de un PDF: "
                       "nativo si ya trae capa de texto; si está escaneado, OCR con motor y DPI según el tipo "
                       "(expediente_judicial, escritura_notarial, sentencia_antigua, documento_administrativo, "
                       "tabla_o_liquidacion) y doble pasada cuando hay plazos o cifras en juego (art. 66 CPC). "
                       "Devuelve el plan, su fundamento y las alternativas: la decisión es del harness.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pdf_path": {"type": "string", "description": "Ruta del PDF a medir"},
                "contexto": {"type": "string", "description": "Para qué se usará (consulta o caso en curso)"},
                "tipo_documento": {"type": "string", "description": "Opcional: expediente_judicial, escritura_notarial, sentencia_antigua, documento_administrativo o tabla_o_liquidacion"}
            },
            "required": ["pdf_path"]
        }
    },
    {
        "name": "ocr_extract_pdf",
        "description": "Extrae texto nativo o ejecuta OCR (Tesseract) sobre expedientes PDF judiciales, actas notariales o resoluciones públicas escaneadas.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pdf_path": {"type": "string", "description": "Ruta absoluta o relativa al archivo PDF"},
                "start_page": {"type": "integer", "description": "Página de inicio (1-indexed, por defecto 1)"},
                "end_page": {"type": "integer", "description": "Página final a procesar (opcional)"},
                "force_ocr": {"type": "boolean", "description": "Forzar OCR incluso si hay texto digital"},
                "lang": {
                    "type": "string",
                    "description": (
                        "Modelo de idioma del OCR. Por defecto 'spa' (español), que es lo que necesitan "
                        "los expedientes chilenos. Si el modelo no está instalado, la respuesta trae una "
                        "advertencia en 'advertencias' y el idioma realmente usado en 'ocr_language'."
                    ),
                    "default": "spa",
                    "enum": ["spa", "spa+eng", "eng", "osd"],
                },
                "dpi": {
                    "type": "integer",
                    "description": "Resolución de rasterizado para el OCR (por defecto 150; 300 para documentos borrosos)",
                    "default": 150,
                },
                "engine": {
                    "type": "string",
                    "description": "Motor de OCR: 'auto' (detecta el mejor disponible), 'rapidocr' (PaddleOCR ONNX de alta precisión), 'paddleocr' o 'tesseract'",
                    "enum": ["auto", "rapidocr", "paddleocr", "tesseract"]
                }
            },
            "required": ["pdf_path"]
        }
    },
    {
        "name": "critique_documento",
        "description": "Auditoría forense de un borrador judicial (5 dimensiones: hecho, derecho, prueba, "
                       "procedimiento y estrategia) con el motor de crítica del producto.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "texto": {"type": "string", "description": "El borrador a auditar"},
                "provider": {"type": "string", "description": "Proveedor de IA opcional (si se omite, usa el motor local)"}
            },
            "required": ["texto"]
        }
    },
    {
        "name": "generar_documento",
        "description": "Genera un documento de trabajo completo y lo entrega en Word (.docx editable, hoja A4, texto "
                       "justificado) más HTML/MD/TXT/JSON. Tipos: demanda civil, recurso de protección, demanda laboral, "
                       "contrato PPA, o «informe» — el informe en derecho EXTENSO: describe los hechos del caso, desarrolla "
                       "el análisis jurídico y transcribe ÍNTEGRO el artículo de cada norma citada (con su cita y enlace); "
                       "la doctrina y la jurisprudencia se buscan solas en el material local (sentencias TA, biblioteca "
                       "ambiental, fallos rectores CS/TC) cuando no se las entregan. Regla del producto: no se cita sin texto.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tipo": {"type": "string", "enum": ["informe", "demanda_civil", "proteccion", "laboral", "ppa"]},
                "tribunal": {"type": "string"},
                "demandante": {"type": "string"},
                "rut": {"type": "string"},
                "demandado": {"type": "string"},
                "comparecencia": {"type": "string"},
                "objeto": {"type": "string", "description": "Informe: la cuestión jurídica planteada (obligatoria)"},
                "materia": {"type": "string", "description": "Informe: materia (laboral, civil, ambiental…)"},
                "caso": {"type": "string", "description": "Informe: identificación del caso"},
                "hechos": {"type": "string", "description": "Los hechos del caso — narración extensa (fechas, conductas, circunstancias, perjuicios)"},
                "analisis": {"type": "string", "description": "Informe: el análisis jurídico extenso (subsunción de los hechos en las normas, contraargumentos) — es el cuerpo del informe"},
                "derecho": {"type": "string"},
                "normas": {"type": "array", "items": {"type": "string"},
                           "description": "Informe: normas a transcribir («Código Civil art. 1545»); las mencionadas en los textos se detectan solas"},
                "doctrina": {"type": "array", "items": {"type": "object"},
                             "description": "Informe: doctrina ya reunida ({obra, autor, institucion, texto}); si se omite se busca en el corpus canónico"},
                "jurisprudencia": {"type": "array", "items": {"type": "object"},
                                   "description": "Informe: fallos o dictámenes ({cita, texto})"},
                "dictamen": {"type": "string", "description": "Informe: la conclusión (si se omite se usa 'peticiones')"},
                "peticiones": {"type": "string"},
                "otrosies": {"type": "array", "items": {"type": "object"}}
            },
            "required": ["tipo", "hechos"]
        }
    },
    {
        "name": "export_brief_ojv",
        "description": "Genera y exporta un escrito judicial estructurado formalmente para la Oficina Judicial Virtual (OJV - Ley N° 20.886) en formatos .html, .md, .txt y .json.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "titulo": {"type": "string", "description": "Título principal (ej. DEMANDA ORDINARIA DE RESOLUCIÓN DE CONTRATO)"},
                "tribunal": {"type": "string", "description": "Designación del tribunal (ej. S.J.L. EN LO CIVIL DE SANTIAGO)"},
                "comparecencia": {"type": "string", "description": "Individualización de la parte compareciente"},
                "hechos": {"type": "string", "description": "Capítulo I. Los Hechos"},
                "derecho": {"type": "string", "description": "Capítulo II. El Derecho"},
                "peticiones": {"type": "string", "description": "Capítulo Por Tanto / Peticiones Concretas"},
                "otrosies": {"type": "array", "items": {"type": "object"}, "description": "Otrosíes (patrocinio y poder, documentos)"}
            },
            "required": ["titulo", "tribunal", "hechos", "derecho", "peticiones"]
        }
    },
    {
        "name": "compile_legal_dossier",
        "description": "Compila un escrito judicial o denuncia en Markdown a PDF formal A4 (carátulas divisorias y marcadores TOC para la OJV) y entrega además el documento de trabajo en Word (.docx, editable): los documentos se entregan en Word, no en PDF.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "markdown_content": {"type": "string", "description": "Texto del escrito o informe en formato Markdown"},
                "output_pdf_path": {"type": "string", "description": "Ruta de salida para el PDF consolidado con anexos"},
                "annexes": {
                    "type": "array",
                    "description": "Lista de anexos a adjuntar con sus metadatos",
                    "items": {
                        "type": "object",
                        "properties": {
                            "num": {"type": "string", "description": "Número de anexo (ej. '«ANEXO N.° 1»')"},
                            "title": {"type": "string", "description": "Título formal del documento probatorio"},
                            "desc": {"type": "string", "description": "Descripción probatoria y alcance legal"},
                            "path": {"type": "string", "description": "Ruta al archivo PDF o imagen (.png, .jpg) del anexo"}
                        },
                        "required": ["title", "path"]
                    }
                },
                "main_pdf_path": {"type": "string", "description": "Ruta opcional para guardar solo el escrito principal firmado en formato ligero para carga directa en OJV"},
                "mobile_preview_path": {"type": "string", "description": "Ruta opcional para generar versión ligera de lectura para celular"},
                "title": {"type": "string", "description": "Título institucional para los marcadores de navegación TOC (ej. 'Recurso de Protección — Iltma. Corte de Apelaciones')"}
            },
            "required": ["markdown_content", "output_pdf_path"]
        }
    },
    {
        "name": "recurso_proteccion_generar",
        "description": "Genera y estandariza un Recurso de Protección conforme al Auto Acordado de la Corte Suprema (Acta N.° 94-2015) y OJV. Entrega el documento de trabajo en Word (.docx, editable) junto a los formatos estructurados (.md, .html, .txt, .json); el PDF consolidado (carátula OJV + anexos con marcadores TOC) es para presentación.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tribunal": {"type": "string", "description": "Corte de Apelaciones competente (ej. 'Ilustrísima Corte de Apelaciones de Santiago')"},
                "recurrente": {
                    "type": "object",
                    "description": "Datos del recurrente: nombre, run, domicilio, email, profesion_oficio, representado_nombre (opcional), representado_run (opcional)",
                    "required": ["nombre", "run", "domicilio", "email"]
                },
                "recurrido": {
                    "type": "object",
                    "description": "Datos de la recurrida: nombre, rut (opcional o 'se desconoce'), domicilio (opcional), email (opcional), representante_legal (opcional)",
                    "required": ["nombre"]
                },
                "acto_lesivo": {"type": "string", "description": "Descripción precisa del acto u omisión arbitrario e ilegal impugnado"},
                "fecha_acto": {"type": "string", "description": "Fecha del acto lesivo o de su conocimiento fehaciente (formato YYYY-MM-DD) para cómputo fatal de 30 días corridos"},
                "hechos": {
                    "type": "array",
                    "description": "Cronología de hechos numerados. Cada elemento puede ser texto o dict con 'texto' y 'anexo' (ej. 'Anexo 1')",
                    "items": {"type": ["string", "object"]}
                },
                "garantias": {
                    "type": "array",
                    "description": "Garantías del Art. 19 CPR invocadas (ej. ['19_1', '19_2', '19_3_5', '19_10', '19_24'])",
                    "items": {"type": "string"}
                },
                "estatutos_especiales": {
                    "type": "array",
                    "description": "Estatutos protectores especiales (ej. ['ninez_21430', 'tea_21545', 'deporte_19712_ds22', 'denuncia_cpp'])",
                    "items": {"type": "string"}
                },
                "orden_de_no_innovar": {
                    "type": "object",
                    "description": "Configuración de la ONI: solicita (bool), fumus_boni_iuris, periculum_in_mora, medida_suspension"
                },
                "oficios": {
                    "type": "array",
                    "description": "Lista de oficios solicitados bajo apercibimiento del Numeral 5.°: [{'organismo': '...', 'materia': '...'}]",
                    "items": {"type": "object"}
                },
                "anexos": {
                    "type": "array",
                    "description": "Lista de anexos probatorios: [{'num': 'ANEXO N.° 1', 'title': '...', 'desc': '...', 'path': 'ruta.pdf'}]",
                    "items": {"type": "object"}
                },
                "quinto_otrosi": {
                    "type": "object",
                    "description": "Quinto otrosí especial opcional: {'titulo': '...', 'contenido': '...'}"
                },
                "petitorio_concreto": {"type": "string", "description": "Peticiones concretas específicas (opcional)"},
                "fecha_interposicion": {"type": "string", "description": "Fecha de interposición (opcional, por defecto hoy YYYY-MM-DD)"},
                "compilar_pdf": {"type": "boolean", "description": "Si es True, compila automáticamente el PDF principal y el dossier consolidado con anexos y marcadores TOC", "default": True}
            },
            "required": ["tribunal", "recurrente", "recurrido", "acto_lesivo", "fecha_acto", "hechos", "garantias"]
        }
    },
    {
        "name": "cpc_validar_mandato",
        "description": "Audita formalmente el texto de un mandato judicial y patrocinio (Ley 18.120), verificando facultades ordinarias (Art. 7 inc. 1) y extraordinarias expresas (Art. 7 inc. 2 CPC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "texto_mandato": {"type": "string", "description": "Texto del otrosí de patrocinio y poder o escritura pública de mandato"}
            },
            "required": ["texto_mandato"]
        }
    },
    {
        "name": "grado_interrogar",
        "description": "Interroga socráticamente al egresado de derecho con preguntas de examen de grado en Chile, evaluando su precisión con la doctrina canónica y códigos.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "materia": {"type": "string", "description": "Área del derecho ('civil', 'procesal')", "default": "civil"},
                "dificultad": {"type": "string", "description": "Dificultad ('facil', 'media', 'alta')", "default": "media"}
            }
        }
    },
    {
        "name": "grado_generar_cedula",
        "description": "Genera una cédula completa de examen de grado con preguntas, normas vinculadas, doctrina canónica y pauta de evaluación.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tema": {"type": "string", "description": "Tema de la cédula (ej. 'Obligaciones', 'Responsabilidad', 'Posesión', 'Recursos')"}
            },
            "required": ["tema"]
        }
    },
    {
        "name": "grado_obtener_flashcards",
        "description": "Obtiene fichas mnemotécnicas de definiciones sacramentales y plazos fatales procesales para el examen de grado.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "area": {"type": "string", "description": "Área ('civil', 'procesal')"},
                "tipo": {"type": "string", "description": "Tipo ('definicion', 'plazo')"}
            }
        }
    },
    {
        "name": "clinica_lenguaje_claro",
        "description": "Traduce una resolución judicial chilena densa a lenguaje claro, accesible y empático para usuarios de consultorios jurídicos (CAJ).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "texto_resolucion": {"type": "string", "description": "Texto de la resolución a traducir"},
                "destinatario": {"type": "string", "description": "Perfil del destinatario", "default": "usuario_caj"}
            },
            "required": ["texto_resolucion"]
        }
    },
    {
        "name": "clinica_intake_social",
        "description": "Genera la ficha sociojurídica de ingreso para consultorios de asistencia judicial gratuita en materias de familia, civil o laboral.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "materia": {"type": "string", "description": "Materia jurídica ('alimentos', 'precario', 'cuidado_personal')"},
                "datos_usuario": {"type": "object", "description": "Diccionario con nombre, rut, telefono y situación socioeconómica"}
            },
            "required": ["materia"]
        }
    },
    {
        "name": "clinica_auditar_borrador",
        "description": "Audita formalmente el borrador de un escrito redactado por un pasante antes de la firma electrónica del abogado tutor.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "borrador_texto": {"type": "string", "description": "Texto del escrito judicial a auditar"},
                "tribunal": {"type": "string", "description": "Tribunal de destino", "default": "Civil"}
            },
            "required": ["borrador_texto"]
        }
    },
    {
        "name": "vigilante_analizar_resolucion",
        "description": "Analiza una resolución judicial provista en OJV/PJUD, detecta cargas procesales y calcula plazos fatales en días hábiles (Art. 66 CPC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "resolucion_texto": {"type": "string", "description": "Texto del proveído o resolución judicial"},
                "procedimiento": {"type": "string", "description": "Procedimiento ('civil', 'laboral', 'familia')", "default": "civil"}
            },
            "required": ["resolucion_texto"]
        }
    },
    {
        "name": "vigilante_radar_normativo",
        "description": "Rastrea publicaciones recientes del Diario Oficial, dictámenes de la Contraloría (CGR) y circulares del SII.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "materia": {"type": "string", "description": "Materia ('laboral', 'administrativo', 'tributario', 'general')", "default": "general"},
                "dias_atras": {"type": "integer", "description": "Días de historial a revisar", "default": 15}
            }
        }
    },
    {
        "name": "vigilante_contrato_plazos",
        "description": "Calcula plazos de preaviso, desahucio y ventanas críticas de renovación automática para contratos civiles y comerciales.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tipo_contrato": {"type": "string", "description": "Tipo de contrato (ej. 'Arrendamiento', 'Prestación de Servicios')"},
                "fecha_vencimiento": {"type": "string", "description": "Fecha de vencimiento en formato YYYY-MM-DD"},
                "preaviso_dias": {"type": "integer", "description": "Días de preaviso pactados", "default": 60}
            },
            "required": ["tipo_contrato", "fecha_vencimiento"]
        }
    },
    {
        "name": "privacidad_tramitar_arco",
        "description": "Procesa y genera el modelo oficial de respuesta a solicitudes de Derechos ARCO bajo la Nueva Ley de Protección de Datos Personales.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tipo_derecho": {"type": "string", "description": "Derecho a ejercer ('ACCESO', 'RECTIFICACIÓN', 'CANCELACIÓN', 'OPOSICIÓN')"},
                "solicitante": {"type": "string", "description": "Nombre del titular de los datos"},
                "rut": {"type": "string", "description": "RUT del solicitante"},
                "datos_solicitados": {"type": "string", "description": "Descripción de los datos requeridos"}
            },
            "required": ["tipo_derecho", "solicitante", "rut", "datos_solicitados"]
        }
    },
    {
        "name": "inapi_cease_and_desist",
        "description": "Redacta una carta formal de Cese y Desistimiento por infracción de marca comercial (Ley 19.039) o propiedad intelectual (Ley 17.336).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "marca_afectada": {"type": "string", "description": "Nombre de la marca o signo afectado"},
                "titular": {"type": "string", "description": "Nombre o razón social del titular legítimo"},
                "infractor": {"type": "string", "description": "Nombre o razón social del infractor"},
                "hechos_infraccion": {"type": "string", "description": "Descripción de los hechos infractores"}
            },
            "required": ["marca_afectada", "titular", "infractor", "hechos_infraccion"]
        }
    },
    {
        "name": "inapi_evaluar_marca",
        "description": "Evalúa preliminarmente la viabilidad y distintividad de una marca comercial en el Clasificador de Niza ante INAPI.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "marca_propuesta": {"type": "string", "description": "Nombre del signo marcario a evaluar"},
                "clase_niza": {"type": "string", "description": "Número de clase Niza (ej. '9', '35', '42', '45')", "default": "45"}
            },
            "required": ["marca_propuesta"]
        }
    },
    {
        "name": "cbr_estudio_titulos",
        "description": "Audita una cadena de títulos de dominio decenal (10 años, Arts. 2510-2511 Código Civil) e inscripciones CBR detectando rupturas en la tradición, gravámenes no alzados o falta de posesión efectiva.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "inscripciones": {
                    "type": "array",
                    "description": "Lista de títulos con propietario, antecesor, anio, fojas, numero, conservador, modo_adquirir, etc.",
                    "items": {"type": "object"}
                },
                "anios_requeridos": {"type": "integer", "description": "Plazo mínimo en años para prescribir (por defecto 10)", "default": 10}
            },
            "required": ["inscripciones"]
        }
    },
    {
        "name": "cbr_checklist_documentos",
        "description": "Retorna el checklist oficial de documentos requeridos para un estudio de títulos en Chile (GP 30 años, dominio vigente, certificados DOM, TGR).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tipo_inmueble": {"type": "string", "description": "Tipo de inmueble ('urbano', 'rural', 'condominio', 'departamento')", "default": "urbano"}
            }
        }
    },
]


def despachar(name: str, args: dict) -> Any:
    _refrescar()
    if name == "ocr_plan_documento":
        from ocr_decision import recomendar_ocr
        return recomendar_ocr(args.get("pdf_path") or "", args.get("contexto", ""),
                              args.get("tipo_documento"))
    elif name == "ocr_extract_pdf":
        pdf_path = args.get("pdf_path")
        if not pdf_path:
            return {"error": "El parámetro 'pdf_path' es obligatorio."}
        try:
            start_p = int(args.get("start_page", 1)) if args.get("start_page") is not None else 1
        except (ValueError, TypeError):
            start_p = 1
        try:
            end_p = int(str(args.get("end_page"))) if args.get("end_page") is not None else None
        except (ValueError, TypeError):
            end_p = None
        return ocr_engine.extract_from_pdf(
            pdf_path=pdf_path,
            start_page=start_p,
            end_page=end_p,
            force_ocr=bool(args.get("force_ocr", False)),
            dpi=int(args.get("dpi", 150)) if args.get("dpi") is not None else 150,
            lang=str(args.get("lang", "spa")),
            engine=str(args.get("engine", "auto"))
        )
    elif name == "critique_documento":
        texto = (args.get("texto") or "").strip()
        if not texto:
            return {"error": "El parámetro 'texto' es obligatorio (el borrador a auditar)."}
        from critique import LegalCritiqueEngine
        informe = LegalCritiqueEngine().critique(texto, provider=args.get("provider"))
        if not isinstance(informe, dict):
            return {"informe": str(informe), "citas": []}
        return {"informe": informe.get("critique") or informe.get("error", ""),
                "citas": informe.get("citas", [])}
    elif name == "generar_documento":
        tipo = (args.get("tipo") or "demanda_civil").lower()
        if tipo == "informe":
            from informe_derecho import exportar_informe_en_derecho

            return exportar_informe_en_derecho(
                objeto=str(args.get("objeto") or ""),
                hechos=args.get("hechos") or "",
                analisis=str(args.get("analisis") or ""),
                dictamen=str(args.get("dictamen") or args.get("peticiones") or ""),
                materia=str(args.get("materia") or ""),
                caso=str(args.get("caso") or ""),
                derecho=str(args.get("derecho") or ""),
                normas=args.get("normas") if isinstance(args.get("normas"), list) else [],
                doctrina=args.get("doctrina") if isinstance(args.get("doctrina"), list) else [],
                jurisprudencia=(args.get("jurisprudencia")
                                if isinstance(args.get("jurisprudencia"), list) else []),
            )
        plantillas = {
            "demanda_civil": "DEMANDA ORDINARIA DE RESOLUCIÓN DE CONTRATO E INDEMNIZACIÓN DE PERJUICIOS",
            "proteccion": "RECURSO DE PROTECCIÓN CONSTITUCIONAL",
            "laboral": "DEMANDA POR DESPIDO INJUSTIFICADO Y COBRO DE PRESTACIONES",
            "ppa": "CONTRATO DE SUMINISTRO DE ENERGÍA ELÉCTRICA (PPA CLIENTE LIBRE)",
        }
        if tipo not in plantillas:
            return {"error": f"Tipo desconocido: {tipo}. Opciones: informe, {', '.join(plantillas)}"}
        if not (args.get("hechos") or args.get("peticiones")):
            return {"error": "Faltan los hechos o las peticiones: sin eso el escrito sale en blanco."}
        exportado = LegalDocumentExporter.export_brief(
            titulo_principal=plantillas[tipo],
            tribunal=args.get("tribunal", ""),
            presuma_data={"materia": args.get("materia", ""), "demandante": args.get("demandante", ""),
                          "rut_dte": args.get("rut", ""), "demandado": args.get("demandado", "")},
            comparecencia=args.get("comparecencia", ""),
            hechos=args.get("hechos", ""),
            derecho=args.get("derecho", ""),
            peticiones=args.get("peticiones", ""),
            otrosies=args.get("otrosies") or [],
        )
        return {"tipo": tipo, "entregable": "word", "archivos": exportado, "citas": exportado.get("citas", [])}
    elif name == "export_brief_ojv":
        tit = str(args.get("titulo") or "ESCRITO JUDICIAL")
        trib = str(args.get("tribunal") or "TRIBUNAL COMPETENTE")
        return exporter.export_brief(
            titulo_principal=tit,
            tribunal=trib,
            presuma_data={"materia": tit, "demandante": "COMPARECIENTE"},
            comparecencia=str(args.get("comparecencia") or ""),
            hechos=str(args.get("hechos") or ""),
            derecho=str(args.get("derecho") or ""),
            peticiones=str(args.get("peticiones") or ""),
            otrosies=args.get("otrosies") if isinstance(args.get("otrosies"), list) else []
        )
    elif name == "compile_legal_dossier":
        md_content = args.get("markdown_content")
        out_pdf = args.get("output_pdf_path")
        if not md_content or not out_pdf:
            return {"error": "Se requieren 'markdown_content' y 'output_pdf_path' para compilar el expediente."}
        res_comp = compiler.compile(
            markdown_content=md_content,
            output_pdf_path=out_pdf,
            annexes=args.get("annexes"),
            mobile_preview_path=args.get("mobile_preview_path"),
            main_pdf_path=args.get("main_pdf_path"),
            title=args.get("title")
        )
        if word_compiler.is_available():
            res_comp["word_document"] = word_compiler.compile(
                markdown_content=md_content,
                output_docx_path=os.path.splitext(out_pdf)[0] + ".docx",
                title=args.get("title") or ""
            )
        return res_comp
    elif name == "recurso_proteccion_generar":
        tribunal = str(args.get("tribunal") or "ILUSTRÍSIMA CORTE DE APELACIONES DE SANTIAGO")
        recurrente = args.get("recurrente")
        recurrido = args.get("recurrido")
        acto_lesivo = str(args.get("acto_lesivo") or "")
        fecha_acto = str(args.get("fecha_acto") or "")
        hechos = args.get("hechos") or []
        garantias = args.get("garantias") or []

        if not recurrente or not isinstance(recurrente, dict):
            return {"error": "Se requiere el objeto 'recurrente' con nombre, run, domicilio y email."}
        if not recurrido or not isinstance(recurrido, dict):
            return {"error": "Se requiere el objeto 'recurrido' con nombre."}
        if not acto_lesivo:
            return {"error": "Se requiere la descripción del 'acto_lesivo'."}
        if not fecha_acto:
            return {"error": "Se requiere 'fecha_acto' (YYYY-MM-DD) para el cómputo de 30 días corridos."}
        if not hechos:
            return {"error": "Se requiere al menos un hecho en la lista de 'hechos'."}
        if not garantias:
            return {"error": "Se requiere al menos una garantía constitucional en 'garantias'."}

        anexos = args.get("anexos") or []
        compilar_pdf = bool(args.get("compilar_pdf", True))
        filename_base = args.get("filename_base")

        # 1. Exportar en formatos texto (.md, .html, .txt, .json)
        export_res = exporter.export_recurso_proteccion(
            tribunal=tribunal,
            recurrente=recurrente,
            recurrido=recurrido,
            acto_lesivo=acto_lesivo,
            fecha_acto=fecha_acto,
            hechos=hechos,
            garantias=garantias,
            estatutos_especiales=args.get("estatutos_especiales"),
            oni_data=args.get("orden_de_no_innovar"),
            oficios=args.get("oficios"),
            anexos=anexos,
            quinto_otrosi=args.get("quinto_otrosi"),
            petitorio_concreto=args.get("petitorio_concreto"),
            fecha_interposicion=args.get("fecha_interposicion"),
            filename_base=filename_base
        )

        # 2. Documento de trabajo en Word (.docx): editable, como manda la casa
        md_text = ""
        with open(export_res["markdownPath"], "r", encoding="utf-8") as f:
            md_text = f.read()

        res_final = dict(export_res)
        if word_compiler.is_available():
            res_final["word_document"] = word_compiler.compile(
                markdown_content=md_text,
                output_docx_path=os.path.join(export_res["exportsDir"],
                                              f"{export_res['filename']}_Documento.docx"),
                title=f"Recurso de Protección — {tribunal}"
            )

        # 3. PDF para presentación (la OJV lo pide; el documento de trabajo es el Word)
        pdf_info = None
        if compilar_pdf and compiler.is_available():
            fn = export_res["filename"]
            exports_dir = export_res["exportsDir"]
            pdf_res = compiler.compile(
                markdown_content=md_text,
                output_pdf_path=os.path.join(exports_dir, f"{fn}_Completo_con_Anexos.pdf"),
                main_pdf_path=os.path.join(exports_dir, f"{fn}_Caratula_OJV.pdf"),
                annexes=anexos,
                title=f"Recurso de Protección — {tribunal}"
            )
            pdf_info = pdf_res
        if pdf_info:
            res_final["pdf_compilation"] = pdf_info
        return res_final
    elif name == "cpc_validar_mandato":
        txt = args.get("texto_mandato")
        if not txt:
            return {"error": "El parámetro 'texto_mandato' es obligatorio."}
        return power_verifier.auditar_mandato(txt)
    elif name == "grado_interrogar":
        return grado_engine.interrogar_socratico(
            materia=args.get("materia", "civil"),
            dificultad=args.get("dificultad", "media")
        )
    elif name == "grado_generar_cedula":
        tema = args.get("tema")
        if not tema:
            return {"error": "El parámetro 'tema' es obligatorio."}
        return grado_engine.generar_cedula_completa(tema)
    elif name == "grado_obtener_flashcards":
        return {
            "flashcards": grado_engine.get_flashcards(
                area=args.get("area"),
                tipo=args.get("tipo")
            )
        }
    elif name == "clinica_lenguaje_claro":
        txt = args.get("texto_resolucion")
        if not txt:
            return {"error": "El parámetro 'texto_resolucion' es obligatorio."}
        return clinica_engine.traducir_lenguaje_claro(
            texto_resolucion=txt,
            destinatario=args.get("destinatario", "usuario_caj")
        )
    elif name == "clinica_intake_social":
        mat = args.get("materia")
        if not mat:
            return {"error": "El parámetro 'materia' es obligatorio."}
        return clinica_engine.generar_intake_social(
            materia=mat,
            datos_usuario=args.get("datos_usuario") or {}
        )
    elif name == "clinica_auditar_borrador":
        borr = args.get("borrador_texto")
        if not borr:
            return {"error": "El parámetro 'borrador_texto' es obligatorio."}
        return clinica_engine.auditar_borrador_supervisor(
            borrador_texto=borr,
            tribunal=args.get("tribunal", "Civil")
        )
    elif name == "vigilante_analizar_resolucion":
        txt = args.get("resolucion_texto")
        if not txt:
            return {"error": "El parámetro 'resolucion_texto' es obligatorio."}
        return docket_engine.analizar_resolucion(
            resolucion_texto=txt,
            procedimiento=args.get("procedimiento", "civil")
        )
    elif name == "vigilante_radar_normativo":
        try:
            dias = int(args.get("dias_atras", 15))
        except (ValueError, TypeError):
            dias = 15
        return docket_engine.radar_normativo_resumen(
            materia=args.get("materia", "general"),
            dias_atras=dias
        )
    elif name == "vigilante_contrato_plazos":
        tc = args.get("tipo_contrato")
        fv = args.get("fecha_vencimiento")
        if not tc or not fv:
            return {"error": "Los parámetros 'tipo_contrato' y 'fecha_vencimiento' son obligatorios."}
        try:
            pre = int(args.get("preaviso_dias", 60))
        except (ValueError, TypeError):
            pre = 60
        return docket_engine.calcular_vencimiento_contrato(tc, fv, pre)
    elif name == "privacidad_tramitar_arco":
        td = args.get("tipo_derecho")
        sol = args.get("solicitante")
        rut = args.get("rut")
        dat = args.get("datos_solicitados")
        if not td or not sol or not rut or not dat:
            return {"error": "Todos los campos 'tipo_derecho', 'solicitante', 'rut' y 'datos_solicitados' son obligatorios."}
        return arco_engine.procesar_solicitud_arco(td, sol, rut, dat)
    elif name == "inapi_cease_and_desist":
        mar_af = str(args.get("marca_afectada") or "").strip()
        tit_af = str(args.get("titular") or "").strip()
        inf_af = str(args.get("infractor") or "").strip()
        hec_af = str(args.get("hechos_infraccion") or "").strip()
        if not mar_af or not tit_af or not inf_af or not hec_af:
            return {"error": "Todos los campos 'marca_afectada', 'titular', 'infractor' y 'hechos_infraccion' son obligatorios."}
        return inapi_engine.redactar_cease_and_desist(mar_af, tit_af, inf_af, hec_af)
    elif name == "inapi_evaluar_marca":
        mar = args.get("marca_propuesta")
        if not mar:
            return {"error": "El parámetro 'marca_propuesta' es obligatorio."}
        return inapi_engine.evaluar_factibilidad_marca(
            marca_propuesta=mar,
            clase_niza=args.get("clase_niza", "45")
        )
    elif name == "cbr_estudio_titulos":
        insc = args.get("inscripciones")
        if not insc or not isinstance(insc, list):
            return {"error": "El parámetro 'inscripciones' debe ser una lista de títulos registrales."}
        return cbr_engine.auditar_cadena_dominio(insc, int(args.get("anios_requeridos", 10)))
    elif name == "cbr_checklist_documentos":
        return cbr_engine.checklist_documentacion_cbr(args.get("tipo_inmueble", "urbano"))
    return None


_PROPIOS = frozenset(globals())
