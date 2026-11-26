"""Herramientas del corpus: consulta maestra, doctrina, grafo de conocimiento y biblioteca."""
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional


def _url_codigo_bcn(obra: str) -> str:
    try:
        from bcn_connector import CODIGOS_REPUBLICA
        return f"https://www.bcn.cl/leychile/navegar?idNorma={CODIGOS_REPUBLICA[obra.lower()]['idNorma']}"
    except Exception:
        return "https://www.bcn.cl/leychile/"

if TYPE_CHECKING:  # pragma: no cover — los bloques usan los objetos vivos de mcp_server
    from mcp_server import (
        CODIGOS,
        Dict,
        List,
        _citas_en_items,
        _con_avisos,
        _detectar_dominios_estatales,
        _doctrina_para_consulta,
        _hf_para_consulta,
        _items_del_organismo,
        _normas_para_consulta,
        _organismos_para_consulta,
        _registro_estatal,
        _subgrafo_para_consulta,
        aj_client,
        build_quick_graph,
        detectar_normas,
        doctrina_get_inst,
        doctrina_list_obras,
        enviar_progreso,
        formatear_cita,
        grafo_vista,
        legal_graphify_engine,
        library_sync_mgr,
        search_doctrina,
    )


def _bcn_para_citas():
    from config import servidor_actual
    _m = servidor_actual()
    return getattr(_m, "_bcn_para_citas", lambda: None)()


def _refrescar() -> None:
    """Trae los nombres compartidos de mcp_server.py (helpers, clientes, motores)."""
    from servidor import refrescar_globals
    refrescar_globals(globals(), _PROPIOS, _DEFAULTS_LAZY)


TOOLS = [
    {
        "name": "consulta_maestra",
        "description": "PRIMER PASO OBLIGATORIO de toda consulta jurídica: consulta simultáneamente el dataset "
                       "de Hugging Face, la doctrina canónica, el grafo, las normas chilenas (BCN) y los organismos "
                       "oficiales del Estado según la materia detectada (DT, CGR, SII, PJUD, SMA, CMF, etc.), "
                       "devolviendo las fuentes con su TEXTO LITERAL y su corchete de cita listo para pegar. Usala "
                       "antes de responder aunque creas saber la respuesta: el producto no cita de memoria. Si la "
                       "materia es ambiental (SMA, SEIA/RCA, daño ambiental, humedales, Tribunales Ambientales), el "
                       "primer paso es el módulo `ambiental_consulta_maestra`, que cubre además los anuarios, "
                       "boletines y la biblioteca ambiental completos.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "consulta": {
                    "type": "string",
                    "description": "La consulta jurídica tal como la hizo la persona"
                },
                "max_fuentes": {
                    "type": "integer",
                    "description": "Cuántas fuentes por familia (por defecto 3)"
                }
            },
            "required": ["consulta"]
        }
    },
    {
        "name": "cita_texto",
        "description": "Devuelve el TEXTO LITERAL de una norma citada, con su corchete oficial y su enlace. "
                       "Usala antes de citar cualquier artículo: el producto no cita sin texto. "
                       "Para verificar varias de una vez, pasá `referencias` (lote): una sola llamada, "
                       "una pasada de red por norma única.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "referencia": {
                    "type": "string",
                    "description": "Ej.: 'Código Civil art. 1438', 'Ley 21.643 art. 2'"
                },
                "referencias": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lote de normas a verificar juntas (ej. ['Ley 19.300 art. 47', 'Ley 20.417 art. 48']). Lo que falle queda en `faltantes`."
                }
            }
        }
    },
    {
        "name": "busqueda_universal",
        "description": "Busca un término a la vez en el dataset de Hugging Face y en los 10 organismos del Estado "
                       "(BCN, CGR, DT, PJUD, TC, CNE, Panel de Expertos, CMF, SII, SMA/TDLC), devolviendo los "
                       "resultados con sus citas listas y texto literal.",
        "inputSchema": {
            "type": "object",
            "properties": {"consulta": {"type": "string", "description": "Término o frase a buscar"}},
            "required": ["consulta"]
        }
    },
    {
        "name": "grafo_ver_corpus",
        "description": (
            "Usala cuando pidan ver el grafo: «mostrame el grafo», «cómo se ve el corpus», «graficá "
            "el conocimiento jurídico», «mostrame el grafo de despido». Escribe un archivo HTML "
            "interactivo (nodos, relaciones, detalle al pasar el mouse) que se abre en el navegador, "
            "para el corpus completo o un subgrafo de una consulta. Devuelve la ruta del archivo."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "consulta": {"type": "string", "description": "Tema a mirar (p. ej. 'despido'); sin esto, el corpus completo"},
                "max_nodos": {"type": "integer", "description": "Cuántos nodos mostrar como máximo (por defecto 250, recortados por PageRank)"}
            }
        }
    },
    {
        "name": "grafo_ver_caso",
        "description": (
            "Usala cuando pidan «graficá este caso», «mostrame el expediente como grafo», «cómo se ve "
            "esta carpeta» o quieran ver las relaciones entre los documentos de un caso. Lee la "
            "carpeta, arma el grafo (cada documento un nodo, cada sección colgando de él) y escribe "
            "un HTML que se abre en el navegador. Dice qué documentos leyó y cuáles saltó, con el "
            "motivo."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "ruta": {"type": "string", "description": "Carpeta del caso (con sus documentos)"}
            },
            "required": ["ruta"]
        }
    },
    {
        "name": "generar_grafo_vinculos",
        "description": "Construye una red de vínculos societarios, políticos y judiciales entre personas, empresas y organismos, retornando código Mermaid y JSON.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "nodes": {
                    "type": "array",
                    "description": "Lista de nodos: [{'id': 'ula', 'label': 'U Lagos', 'category': 'sociedad'}, ...]",
                    "items": {"type": "object"}
                },
                "edges": {
                    "type": "array",
                    "description": "Lista de aristas: [{'source': 'ula', 'target': 'kimun', 'relation': 'traspaso $130M'}, ...]",
                    "items": {"type": "object"}
                },
                "title": {"type": "string", "description": "Título del diagrama de vínculos"}
            },
            "required": ["nodes", "edges"]
        }
    },
    {
        "name": "doctrina_search",
        "description": "Busca en el canon dogmático de manuales y tratados jurídicos chilenos más citados (Barros Bourie, Ramos Pazos, Peñailillo, Maturana, Bermúdez, Cury, Gamonal, Cea Egaña) mediante búsqueda FTS5 BM25 y modo híbrido semántico opcional (Reciprocal Rank Fusion local).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término o concepto dogmático a buscar (ej. 'clausula penal', 'culpa infraccional', 'tutela laboral')"},
                "area": {"type": "string", "description": "Área del derecho (opcional: 'Civil', 'Procesal', 'Penal', 'Laboral', 'Administrativo', 'Constitucional')"},
                "autor": {"type": "string", "description": "Nombre o apellido del tratadista (opcional: 'Barros', 'Ramos Pazos', 'Cury')"},
                "limit": {"type": "integer", "description": "Cantidad máxima de resultados (por defecto 5)"},
                "hibrido": {"type": "boolean", "description": "Si es True, fusiona BM25 con similitud vectorial local (RRF) para consultas en lenguaje coloquial", "default": False}
            },
            "required": ["query"]
        }
    },
    {
        "name": "doctrina_get_institucion",
        "description": "Recupera la ficha dogmática y forense completa sobre una institución jurídica específica: definición canónica, requisitos copulativos, operativa procesal forense (vía procesal, tribunal competente, legitimación, carga probatoria, medidas precautorias, plazos y excepciones), concordancias legales BCN y fallos rectores.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "nombre": {"type": "string", "description": "Nombre exacto o aproximado de la institución (ej. 'Legítima Defensa', 'Recurso de Protección', 'Acción Reivindicatoria')"},
                "area": {"type": "string", "description": "Área del derecho (opcional)"}
            },
            "required": ["nombre"]
        }
    },
    {
        "name": "doctrina_list_obras",
        "description": "Lista todos los tratados y manuales dogmáticos de doctrina chilena indexados en la base de datos de Open Legal Chile con sus autores y estadísticas.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "doctrina_ingestar_documento",
        "description": "Convierte documentos (PDF, DOCX, TXT, MD) o textos a Markdown canónico de alta densidad dogmática (normas RAE/ASALE y citas chilenas BCN/CS) y agrega de forma incremental solo ese documento al índice SQLite FTS5 de doctrina y al Knowledge Graph (legal_knowledge_graph.json), sin reconstruirlos: tarda segundos.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Ruta al archivo (.pdf, .docx, .txt, .md) o texto crudo a procesar."
                },
                "area": {
                    "type": "string",
                    "description": "Área del derecho (ej. 'civil', 'procesal', 'laboral', 'penal', 'constitucional', 'administrativo'). Por defecto 'civil'.",
                    "default": "civil"
                },
                "tratadista": {
                    "type": "string",
                    "description": "Nombre del autor o tratadista (ej. 'René Ramos Pazos', 'Enrique Barros Bourie')."
                },
                "obra": {
                    "type": "string",
                    "description": "Título de la obra, tratado o manual jurídico."
                },
                "materia": {
                    "type": "string",
                    "description": "Materia dogmática específica tratada en el documento."
                },
                "actualizar_grafo": {
                    "type": "boolean",
                    "description": "Si es True, agrega de inmediato los nodos del documento al Knowledge Graph de LegalGraphify (legal_knowledge_graph.json), sin reconstruirlo.",
                    "default": True
                },
                "target_path": {
                    "type": "string",
                    "description": "Ruta de destino personalizada para el archivo .md generado."
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "academia_judicial_buscar_guias",
        "description": "Busca en las Guías Oficiales de Buenas Prácticas Judiciales de la Academia Judicial de Chile (penal, determinación de penas, laboral, familia, ética, IA).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término de búsqueda o materia"},
                "materia": {"type": "string", "description": "Materia ('Penal', 'Laboral', 'Familia', 'Ética Judicial') (opcional)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "biblioteca_compilar_manifiesto",
        "description": "Compila el catálogo y métricas de la biblioteca online de Markdown de doctrina y genera los paquetes para Hugging Face, GitHub y Google Drive.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "generar_bundles": {"type": "boolean", "description": "Si es True, empaqueta el tar.gz y prepara la carpeta para Google Drive", "default": False}
            }
        }
    },
    {
        "name": "huggingface_search_dataset",
        "description": "Consulta el repositorio público oficial en Hugging Face Datasets Hub (pablobenavidesj/doctrina-jurisprudencia-chile) y recupera contexto y enlaces directos con citas oficiales. "
                       "Con el mapa del corpus busca primero lo exacto (rol, norma o entidad: la ficha y quién la cita) y "
                       "cita con la URL fijada a la revisión del dataset.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término de búsqueda doctrinal o institucional (ej. 'responsabilidad', 'despido', 'contratos')"},
                "limit": {"type": "integer", "description": "Número máximo de archivos o recursos a devolver", "default": 5},
                "rol": {"type": "string", "description": "Rol exacto de una causa (ej. '10641-2024' de la Corte Suprema, '2402-12-INA' del TC, 'R-21-2021' ambiental): trae su ficha y los documentos que la citan (opcional)"},
                "norma": {"type": "string", "description": "Norma citada (ej. 'art. 1545 del Código Civil', 'Ley 19.300'): los documentos del dataset que la citan (opcional)"},
                "coleccion": {"type": "string", "description": "Acota a una colección: 'cs' (Corte Suprema), 'tc', 'ta' (tribunales ambientales), 'doc' (doctrina y revistas), 'guia', 'bib' o 'pub' (opcional)"},
                "entidad": {"type": "string", "description": "Ministro, autor, revista, sala o recurso, por nombre o ID del mapa (ej. 'María Gajardo Harboe', 'revista:rchd'): los documentos vinculados (opcional)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "graphify_resumen_comunidades",
        "description": (
            "Usala cuando pidan un panorama: «¿qué hay en el corpus?», «dame el resumen general», "
            "«qué temas cubre», «resumen por comunidades», o cuando la consulta sea amplia y no "
            "apunte a una institución concreta. Devuelve el resumen jerárquico del grafo (GraphRAG): "
            "cada comunidad con su tamaño, su área y sus nodos representativos, en unos cientos de "
            "tokens en vez de recorrer miles de nodos. Para el detalle de una institución, usar "
            "graphify_consulta_subgrafo."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "top_n": {"type": "integer", "description": "Cuántas comunidades mostrar (por defecto 12)"}
            }
        }
    },
    {
        "name": "graphify_consulta_subgrafo",
        "description": "Consulta el Knowledge Graph Jurídico de Doctrina Chilena (LegalGraphify), extrayendo subgrafos sintéticos hiper-densos (normas BCN, criterios CS, tratadistas y operativa procesal) con un ahorro mediano del 99,9% de tokens (ficha mediana: 91 tokens frente a la obra completa: 96.536) respecto a la lectura del texto doctrinal completo. La medición es reproducible: docs/medicion_tokens.md.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Concepto jurídico, institución, norma o materia a consultar en el subgrafo (ej. 'simulacion', 'imprevision', 'nulidad', 'tutela laboral')"},
                "max_hops": {"type": "integer", "description": "Radio de saltos relacionales en el grafo", "default": 1},
                "incluir_mermaid": {"type": "boolean", "description": "Si es True, incluye el diagrama Mermaid renderizable del subgrafo", "default": False}
            },
            "required": ["query"]
        }
    },
    {
        "name": "graphify_trazar_camino",
        "description": "Calcula y traza los caminos relacionales mínimos entre dos conceptos o normas jurídicas en LegalGraphify, deduciendo cadenas de subsunción y argumentación dogmática. Con `solo_sustantivo=True` usa la capa sustantiva del grafo multiplex (excluye puentes bibliográficos de autor, obra o revista).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "origen": {"type": "string", "description": "Concepto o norma jurídica de inicio (ej. 'simulacion', 'incumplimiento')"},
                "destino": {"type": "string", "description": "Concepto o norma jurídica de fin (ej. 'nulidad', 'indemnizacion')"},
                "max_caminos": {"type": "integer", "description": "Número máximo de rutas mínimas a retornar", "default": 3},
                "solo_sustantivo": {"type": "boolean", "description": "Si es True, prioriza rutas jurídicas sustantivas excluyendo súper-hubs editoriales", "default": False}
            },
            "required": ["origen", "destino"]
        }
    },
    {
        "name": "graphify_explicar_institucion",
        "description": "Genera una explicación dogmática 360° de una institución jurídica en LegalGraphify: definición, sustento positivo BCN, criterios de la Corte Suprema, operativas procesales y grado topológico.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Institución dogmática, concepto o materia a explicar (ej. 'simulacion', 'imprevision', 'nulidad')"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "graphify_analizar_impacto",
        "description": "Calcula el radio de afectación topológico (Blast Radius) cuando una norma legal o institución jurídica sufre una reforma legal o giro jurisprudencial, identificando entidades afectadas en grado 1 (directo) y grado 2 (cascada).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "objetivo": {"type": "string", "description": "Norma legal o institución a evaluar ante reformas (ej. 'Art. 2515 CC', 'Art. 1545 CC', 'Buena Fe')"}
            },
            "required": ["objetivo"]
        }
    },
    {
        "name": "graphify_god_nodes",
        "description": "Identifica los pilares dogmáticos estructurales (God Nodes) del sistema jurídico chileno según algoritmos de PageRank y centralidad sobre el Knowledge Graph de doctrina y normas. Con `solo_sustantivo=True` aplica ponderación multiplex atenuando súper-hubs editoriales.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "top_n": {"type": "integer", "description": "Cantidad de instituciones y normas principales a retornar", "default": 10},
                "solo_sustantivo": {"type": "boolean", "description": "Si es True, atenúa aristas bibliográficas y excluye contenedores editoriales de los pilares", "default": False}
            }
        }
    },
    {
        "name": "jurimetria_analizar_corpus",
        "description": (
            "Análisis jurimétrico e investigación académica empírica sobre el corpus chileno (LegalGraphify + mapa HF): "
            "calcula PageRank dirigido y HITS (Authority y Hub) sobre la red sustantiva de citaciones (excluyendo súper-hubs "
            "bibliográficos), audita la resolución de entidades y ruido OCR normativo, y entrega estadísticas longitudinales "
            "exactas (por año, sala de la Corte Suprema, recurso, resultado normalizado y cuantiles del Baremo UF/CLP) "
            "declarando el universo N, la revisión fijada en Hugging Face y las advertencias muestrales."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "modo": {
                    "type": "string",
                    "enum": ["completo", "red_citaciones", "longitudinal", "muestra_validacion"],
                    "description": "Tipo de análisis jurimétrico a ejecutar (por defecto 'completo')",
                    "default": "completo"
                },
                "coleccion": {
                    "type": "string",
                    "description": "Colección a analizar ('cs', 'tc', 'ta', 'doc', 'todas'; por defecto 'cs')"
                },
                "norma_filtro": {
                    "type": "string",
                    "description": "Norma o institución opcional para acotar la red de citaciones (ej. 'Art. 1545 CC', 'Art. 19 N 24 CPR')"
                },
                "agrupacion": {
                    "type": "string",
                    "enum": ["anio", "mes"],
                    "description": "Granularidad temporal para estadísticas longitudinales ('anio' o 'mes'; por defecto 'anio')",
                    "default": "anio"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Cantidad máxima de normas, sentencias e instituciones en el ranking de red",
                    "default": 15
                },
                "n_muestra": {
                    "type": "integer",
                    "description": "Tamaño de muestra estratificada cuando modo='muestra_validacion'",
                    "default": 50
                },
                "semilla": {
                    "type": "integer",
                    "description": "Semilla determinista para reproducibilidad de la muestra estratificada",
                    "default": 42
                }
            }
        }
    },
    {
        "name": "jurimetria_exportar_investigacion",
        "description": (
            "Exporta un paquete reproducible de investigación jurídica académica para artículos, tesis o ponencias: "
            "genera tablas CSV (R/Stata/Python), red GraphML (Gephi/Cytoscape), Apache Parquet (si pyarrow está instalado), "
            "muestra estratificada ciega para validación intercodificador (precisión, cobertura, F1 y κ de Cohen), "
            "METODOLOGIA_REPRODUCIBLE.md con revisión fijada de Hugging Face y citas BibTeX listas en referencia.bib."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "tema": {
                    "type": "string",
                    "description": "Institución, norma o materia central a exportar (ej. 'simulacion', 'Art. 2314 CC', 'dano moral' o 'corpus')"
                },
                "carpeta_salida": {
                    "type": "string",
                    "description": "Carpeta local donde se escribirá el paquete reproducible (si se omite, se crea bajo exports/investigacion/)"
                },
                "formatos": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Formatos a exportar (por defecto ['csv', 'graphml', 'parquet', 'json', 'md', 'bib'])"
                },
                "coleccion_longitudinal": {
                    "type": "string",
                    "description": "Colección para las estadísticas longitudinales y muestra de validación ('cs', 'tc', 'ta', 'doc'; por defecto 'cs')",
                    "default": "cs"
                },
                "n_muestra": {
                    "type": "integer",
                    "description": "Tamaño de la muestra estratificada de validación humana",
                    "default": 50
                },
                "semilla": {
                    "type": "integer",
                    "description": "Semilla aleatoria fija para reproducibilidad",
                    "default": 42
                }
            },
            "required": ["tema"]
        }
    },
]


def _cita_de_norma(cliente: Any, norma: dict, limite: Optional[int] = 1200) -> dict:
    """Resuelve el texto literal de una norma ya identificada: cita lista o error declarado.

    `limite=None` entrega el texto COMPLETO (para documentos); por defecto recorta a 1200
    caracteres, que es lo correcto para una respuesta de conversación.
    """
    try:
        if norma["familia"] == "codigo":
            dato = cliente.get_codigo(norma["obra"], norma["articulo"])
            ident = f"{CODIGOS[norma['obra']]}, Art. {norma['articulo']}"
            url = _url_codigo_bcn(norma["obra"])
        else:
            numero_ley = int(norma["numero"])
            if norma.get("articulo"):
                dato = cliente.get_articulo_ley(numero_ley, norma["articulo"])
                ident = f"Ley N° {numero_ley}, Art. {norma['articulo']}"
                url = f"https://www.bcn.cl/leychile/navegar?idLey={numero_ley}"
            else:
                dato = cliente.get_ley(numero_ley)
                ident = f"Ley N° {numero_ley}"
                url = f"https://www.bcn.cl/leychile/navegar?idNorma={dato.get('normaId', '')}"
    except Exception as e:  # noqa: BLE001 — se declara, no se inventa
        return {"error": f"No pude traer el texto: {str(e)[:160]}", "sin_fuente_verificable": True}
    texto = str(dato.get("texto") or "")
    if not texto:
        return {"error": "La fuente respondió sin texto: no se cita lo que no se pudo leer.",
                "sin_fuente_verificable": True, "detalle": str(dato)[:300]}
    recorte = texto if limite is None else texto[:limite]
    cita = formatear_cita("BCN", ident, url=url, texto=recorte)
    vig = dato.get("vigencia")
    if isinstance(vig, dict) and vig.get("estado") in ("vacancia_legal", "derogada"):
        cita["vigencia"] = vig
    return {"cita": cita}


def _citas_por_lote(referencias: list, limite: Optional[int] = 1200) -> dict:
    """Verifica varias normas en una sola llamada: una pasada de red por norma única.

    Los artículos de una misma ley comparten descarga (detección → dedupe → pool de 6) y lo
    que no se pudo traer queda aparte en `faltantes`, declarado y sin rellenar.
    """
    from concurrent.futures import ThreadPoolExecutor

    pendientes: list = []
    resultados: list = []
    for referencia in referencias:
        normas = detectar_normas(referencia)
        if not normas:
            resultados.append({"referencia": referencia,
                               "error": f"No pude reconocer una norma en «{referencia}».",
                               "sin_fuente_verificable": True})
            continue
        pendientes.append((referencia, normas[0]))

    try:
        cliente = _bcn_para_citas()
    except Exception as e:  # noqa: BLE001
        return {"error": f"No pude traer los textos: {str(e)[:160]}",
                "sin_fuente_verificable": True, "faltantes": list(referencias)}

    claves: dict = {}
    for _, norma in pendientes:
        clave = (norma["familia"], norma["obra"] if norma["familia"] == "codigo"
                 else norma["numero"])
        claves.setdefault(clave, norma)

    def _calentar(item):
        clave, norma = item
        try:
            if norma["familia"] == "codigo":
                cliente.get_codigo(norma["obra"])
            else:
                cliente.get_ley(int(norma["numero"]))
            return clave, ""
        except Exception as e:  # noqa: BLE001
            return clave, str(e)[:160]

    errores: dict = {}
    with ThreadPoolExecutor(max_workers=min(6, max(1, len(claves))),
                            thread_name_prefix="citas") as pool:
        for clave, error in pool.map(_calentar, list(claves.items())):
            if error:
                errores[clave] = error

    for referencia, norma in pendientes:
        clave = (norma["familia"], norma["obra"] if norma["familia"] == "codigo"
                 else norma["numero"])
        if clave in errores:
            resultados.append({"referencia": referencia,
                               "error": f"No pude traer el texto: {errores[clave]}",
                               "sin_fuente_verificable": True})
            continue
        resultados.append({"referencia": referencia, **_cita_de_norma(cliente, norma, limite=limite)})

    citas = [r["cita"] for r in resultados if "cita" in r]
    faltantes = [r["referencia"] for r in resultados if "error" in r]
    resultados = [{k: v for k, v in r.items() if k != "cita"} for r in resultados]
    return {
        "total": len(referencias),
        "citas": citas,
        "faltantes": faltantes,
        "resultados": resultados,
        "como_citar": ("Pegá cada cita con su texto literal; lo que esté en `faltantes` "
                       "se declara como «sin fuente verificable»."),
    }


def _estado_mapa() -> dict:
    """Estado del mapa del corpus de Hugging Face (sin red); nunca lanza."""
    try:
        from online_library_sync import estado_mapa
        return estado_mapa()
    except Exception as e:  # noqa: BLE001 — sin mapa la consulta sigue con sus fuentes de siempre
        return {"activo": False, "error": f"{type(e).__name__}: {str(e)[:160]}"}


def _aviso_mapa(mapa: dict) -> str:
    """El aviso de la consulta cuando el mapa no está activo (o responde con una caché anterior).
    Apagado o aún sin publicar no hay nada que avisar: no falta nada que el usuario pueda hacer
    (igual que `suite_doctor`)."""
    if mapa.get("aviso"):
        return str(mapa["aviso"])
    if mapa.get("activo") or mapa.get("publicado") is False or str(mapa.get("motivo", "")).startswith("desactivado"):
        return ""
    motivo = mapa.get("motivo") or mapa.get("error") or "no hay un mapa listo"
    return (f"El mapa del corpus de Hugging Face no está activo ({motivo}): la consulta usó las fuentes de "
            "siempre, sin la búsqueda exacta por rol, norma ni entidad del mapa.")


def _con_revistas_del_mapa(locales: Any, consulta: str, limite: int, area: Any = None, autor: Any = None) -> Any:
    """`doctrina_search` se completa con los artículos de las revistas del dataset (vía el mapa del
    corpus): llenan los cupos que la doctrina local deja libres y, desde `limit` 3, un tercio de
    los cupos es para ellas. Sin mapa listo, los resultados locales tal cual."""
    try:
        from online_library_sync import revistas_del_mapa
        revistas = revistas_del_mapa(str(consulta), limite, area=area, autor=autor)
    except Exception:  # noqa: BLE001 — el mapa suma, nunca tumba la búsqueda de doctrina
        revistas = []
    if not revistas or not isinstance(locales, list):
        return locales
    cupo = min(len(revistas), max(limite - len(locales), limite // 3))
    return locales[:max(0, limite - cupo)] + revistas[:cupo]


def _compactar_item_organismo(item: Any) -> Any:
    if not isinstance(item, dict):
        return item
    omitir = {"texto", "texto_integral", "link_oficial", "url_vigente"}
    if item.get("doctrina") is not None and item.get("doctrina") == item.get("resultado"):
        omitir.add("doctrina")
    return {k: v for k, v in item.items() if k not in omitir}


def _compactar_organismos_hallazgos(resultados_org: Any, con_citas: bool) -> Any:
    if not con_citas or not isinstance(resultados_org, dict):
        return resultados_org
    compacto: Dict[str, Any] = {}
    for org, valor in resultados_org.items():
        if isinstance(valor, list):
            compacto[org] = [_compactar_item_organismo(x) for x in valor]
        elif isinstance(valor, dict):
            copia = dict(valor)
            for clave in ("resultados", "items", "docs"):
                if isinstance(copia.get(clave), list):
                    copia[clave] = [_compactar_item_organismo(x) for x in copia[clave]]
            compacto[org] = copia
        else:
            compacto[org] = valor
    return compacto


def _ver_corpus(motor: Any, consulta: Optional[str], max_nodos: int = 250, salida: Optional[str] = None) -> dict:
    """`grafo_ver_corpus` sobre el motor COMPARTIDO del servidor: el grafo que ya está en memoria
    (con la capa del mapa del corpus, si la hay), sin volver a leerlo del disco. `max_nodos` acota
    también el subgrafo de una consulta: una norma del mapa puede tener miles de vecinos."""
    import contextlib
    import os

    import grafo_vista as vista

    max_nodos = max(1, int(max_nodos))
    if not getattr(motor, "is_built", False) and not motor.cargar_grafo_json():
        return {"error": "no se pudo cargar el grafo del corpus: construilo con "
                         "`python legal_graphify.py --build`"}
    # Si el motor expone su candado (carga y cambio del grafo), el recorte se hace bajo él.
    candado: Any = getattr(motor, "_lock", None)
    if not hasattr(candado, "__enter__"):
        candado = contextlib.nullcontext()
    with candado:
        grafo = motor.graph
        muestra = False
        if consulta:
            encontrado = motor._buscar_nodo_relevante(consulta)  # noqa: SLF001 (API interna del motor)
            if not encontrado or not grafo.has_node(encontrado):
                return {"error": f"no encontré nada en el grafo para «{consulta}»",
                        "sugerencia": "probá con una palabra sola (despido, posesión, nulidad)"}
            vecinos = (set(grafo.successors(encontrado)) | set(grafo.predecessors(encontrado))) - {encontrado}
            if len(vecinos) + 1 > max_nodos:
                # Los vecinos más conectados, en orden determinista; el nodo consultado, siempre.
                vecinos = set(sorted(vecinos, key=lambda n: (-grafo.degree(n), str(n)))[:max_nodos - 1])
                muestra = True
            grafo = grafo.subgraph(vecinos | {encontrado}).copy()
            titulo = f"Grafo del corpus — subgrafo de «{consulta}»"
            nota = (f"El nodo de «{consulta}» y {grafo.number_of_nodes() - 1} de sus vecinos más conectados "
                    "(recorte para que se pueda leer)." if muestra else
                    f"El nodo de «{consulta}» y sus vecinos en el corpus indexado por LegalGraphify.")
        else:
            if grafo.number_of_nodes() > max_nodos:
                import networkx as nx

                try:
                    rango = nx.pagerank(grafo, alpha=0.85, max_iter=100)
                except Exception:  # noqa: BLE001 — sin convergencia, el grado basta para elegir
                    rango = {n: grafo.degree(n) for n in grafo.nodes}
                elegidos = [n for n, _ in sorted(rango.items(), key=lambda x: (-x[1], str(x[0])))[:max_nodos]]
                grafo = grafo.subgraph(elegidos).copy()
                muestra = True
            else:
                grafo = grafo.copy()
            titulo = "El grafo del derecho chileno"
            nota = (f"El corpus completo indexado por LegalGraphify. Acá se muestran {grafo.number_of_nodes()} "
                    "de los nodos más conectados (PageRank) para que se pueda leer." if muestra else
                    "El corpus completo indexado por LegalGraphify.")
    archivo = salida or os.path.join(vista.SALIDA_POR_DEFECTO, "corpus.html")
    vista._html_del_grafo(grafo, titulo, nota, archivo)  # noqa: SLF001 (mismo HTML que grafo_vista)
    return {"archivo": archivo, "nodos": grafo.number_of_nodes(), "aristas": grafo.number_of_edges(),
            "muestra": muestra, "como_abrirlo": f"abrilo en el navegador: {archivo}"}


def despachar(name: str, args: dict) -> Any:
    _refrescar()
    if name == "consulta_maestra":
        consulta = (args.get("consulta") or args.get("query") or args.get("q") or args.get("termino") or "").strip()
        if not consulta:
            return {"error": "El parámetro 'consulta' (o 'query') es obligatorio."}
        lim = int(args.get("max_fuentes") or 3)
        # Los cinco sondeos son independientes (HF, doctrina, normas, subgrafo, organismos del Estado):
        # en paralelo la consulta espera al más lento, no a la suma.
        enviar_progreso("Consulta maestra: 5 sondeos en paralelo (Hugging Face, doctrina, BCN, subgrafo, organismos)",
                        0, 5)

        def _anunciar(etiqueta: str, hechos: int):
            def _envolver(fn):
                def _paso(*a, **k):
                    resultado = fn(*a, **k)
                    enviar_progreso(f"{etiqueta} listo", hechos, 5)
                    return resultado
                return _paso
            return _envolver

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=5, thread_name_prefix="consulta") as pool:
            f_hf = pool.submit(_anunciar("Hugging Face", 1)(_hf_para_consulta), consulta, lim)
            f_doctrina = pool.submit(_anunciar("Doctrina", 2)(_doctrina_para_consulta), consulta, lim)
            f_normas = pool.submit(_anunciar("Normas BCN", 3)(_normas_para_consulta), consulta)
            f_subgrafo = pool.submit(_anunciar("Subgrafo", 4)(_subgrafo_para_consulta), consulta)
            f_organismos = pool.submit(_anunciar("Organismos Estado", 5)(_organismos_para_consulta), consulta, lim)
            hf, doctrina, normas, subgrafo, organismos = (
                f_hf.result(), f_doctrina.result(),
                f_normas.result(), f_subgrafo.result(), f_organismos.result()
            )
        citas: List[Dict[str, Any]] = (
            list(hf.get("citas") or []) +
            list(doctrina.get("citas") or []) +
            list(organismos.get("citas") or [])
        )
        for n in normas:
            texto = str(n.get("texto") or "")
            if not texto:
                continue
            if n.get("codigo"):
                ident = f"{n['codigo']}, Art. {n.get('articulo', '')}".strip().rstrip(",")
            else:
                titulo = n.get("titulo") or f"Ley N° {n.get('ley_numero') or n.get('ley', '')}"
                ident = f"{titulo}, Art. {n.get('articulo', '')}".strip().rstrip(",")
            citas.append(formatear_cita("BCN", ident, url=n.get("url", ""), texto=texto[:1200]))
        faltantes = [clave for clave, ok in (
            ("huggingface", bool(hf.get("citas"))),
            ("doctrina", bool(doctrina.get("resultados"))),
            ("normas", bool([n for n in normas if n.get("texto")])),
            ("organismos", bool(organismos.get("citas"))),
        ) if not ok]
        # El mapa del corpus viaja con el sondeo de Hugging Face; si ese sondeo no lo trae (falló
        # o lo sustituyó otra implementación), se lee aparte, sin red.
        mapa = hf.get("mapa") if isinstance(hf.get("mapa"), dict) else _estado_mapa()
        hf_res = hf.get("resultados", [])
        if hf.get("citas") and isinstance(hf_res, list):
            _hf_omitir = {"extractos", "url_vigente", "space_interactivo", "dataset"}
            hf_res = [{k: v for k, v in r.items() if k not in _hf_omitir} if isinstance(r, dict) else r for r in hf_res]
        doc_res = doctrina.get("resultados", [])
        if doctrina.get("citas") and isinstance(doc_res, list):
            _doc_omitir = {"definicion", "contenido", "snippet"}
            doc_res = [{k: v for k, v in r.items() if k not in _doc_omitir} if isinstance(r, dict) else r for r in doc_res]
        normas_res = [
            {k: v for k, v in n.items() if k != "texto"} if isinstance(n, dict) and n.get("texto") else n
            for n in normas
        ]
        org_res = _compactar_organismos_hallazgos(
            organismos.get("resultados", {}), bool(organismos.get("citas"))
        )
        mapa_compacto = {k: v for k, v in mapa.items() if k != "conteos"} if isinstance(mapa, dict) else mapa
        respuesta = {
            "consulta": consulta,
            "hallazgos": {"huggingface": hf_res,
                          "doctrina": doc_res,
                          "normas": normas_res,
                          "subgrafo": subgrafo,
                          "organismos": org_res},
            "citas": citas,
            "faltantes": faltantes,
            "como_citar": "Pegá cada cita con su texto literal. En conversación: la respuesta primero y las "
                          "fuentes al final. En documentos: citas a pie de página (fuente · identificador · enlace).",
            "mapa": mapa_compacto,
        }
        aviso = _aviso_mapa(mapa)
        if aviso:
            respuesta["avisos"] = [aviso]
        return respuesta
    elif name == "cita_texto":
        lote = args.get("referencias")
        if isinstance(lote, str):
            lote = lote.replace(";", "\n").split("\n")
        if isinstance(lote, list):
            lote = [str(una).strip() for una in lote if str(una).strip()]
        else:
            lote = []
        if lote:
            return _citas_por_lote(lote)
        referencia = (args.get("referencia") or "").strip()
        normas = detectar_normas(referencia)
        if not normas:
            return {"error": f"No pude reconocer una norma en «{referencia}». Probá con «Código Civil art. 1438».",
                    "sin_fuente_verificable": True}
        try:
            cliente = _bcn_para_citas()
        except Exception as e:  # noqa: BLE001
            return {"error": f"No pude traer el texto: {str(e)[:160]}", "sin_fuente_verificable": True}
        resultado = _cita_de_norma(cliente, normas[0])
        if "cita" in resultado:
            return {"referencia": referencia, "normas_detectadas": normas, "citas": [resultado["cita"]]}
        return resultado
    elif name == "busqueda_universal":
        consulta = (args.get("consulta") or args.get("query") or args.get("q") or args.get("termino") or "").strip()
        if not consulta:
            return {"error": "El parámetro 'consulta' (o 'query') es obligatorio."}

        import concurrent.futures

        reg = _registro_estatal()
        if hasattr(reg, "search_all") and not hasattr(reg, "bcn"):
            with concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="universal") as pool:
                fut_reg = pool.submit(reg.search_all, consulta)
                fut_hf = pool.submit(_hf_para_consulta, consulta, 3)
                resultados = fut_reg.result()
                try:
                    hf = fut_hf.result(timeout=8.0)
                except Exception as e:
                    hf = {"resultados": [], "citas": [], "error": f"Hugging Face no respondió: {str(e)[:160]}"}
        else:
            cached = getattr(reg, "_get_cached", lambda *a: None)("all", consulta)
            if cached and isinstance(cached, dict):
                resultados = cached
                hf = _hf_para_consulta(consulta, lim=3)
            else:
                resultados = {
                    "query": consulta,
                    "bcn": [], "cgr": {}, "dt": [], "cne": [], "panel": [],
                    "cmf": [], "sii": [], "sma": {}, "tdlc": [], "pjud": []
                }

                def _invocar_conector(clave: str):
                    if clave == "cne":
                        if not (os.environ.get("CNE_EMAIL") and os.environ.get("CNE_PASSWORD")):
                            return clave, []
                        return clave, reg.cne.search(consulta)
                    elif clave == "bcn":
                        return clave, reg.bcn.search(consulta)
                    elif clave == "cgr":
                        return clave, reg.cgr.search_jurisprudencia(consulta)
                    elif clave == "dt":
                        return clave, reg.dt.search_dictamenes(consulta, limit=5)
                    elif clave == "panel":
                        return clave, reg.panel.search_dictamenes(consulta)
                    elif clave == "cmf":
                        return clave, reg.cmf.search_normativa(consulta)
                    elif clave == "sii":
                        return clave, reg.sii.search_circulares(consulta)
                    elif clave == "sma":
                        return clave, reg.sma.search_sancionatorios(nombre=consulta)
                    elif clave == "tdlc":
                        return clave, reg.tdlc.search_jurisprudencia(consulta)
                    elif clave == "pjud":
                        return clave, reg.pjud.search_jurisprudencia(consulta, limit=5)
                    return clave, []

                claves = ["bcn", "cgr", "dt", "cne", "panel", "cmf", "sii", "sma", "tdlc", "pjud"]
                with concurrent.futures.ThreadPoolExecutor(max_workers=11, thread_name_prefix="universal") as pool:
                    fut_hf = pool.submit(_hf_para_consulta, consulta, 3)
                    futuros = {pool.submit(_invocar_conector, k): k for k in claves}
                    for fut in concurrent.futures.as_completed(futuros):
                        k = futuros[fut]
                        try:
                            _, res = fut.result(timeout=6.0)
                        except (concurrent.futures.TimeoutError, TimeoutError):
                            res = [{"error": "timeout"}] if k not in ("cgr", "sma") else {"error": "timeout"}
                        except Exception as e:
                            res = [{"error": str(e)}] if k not in ("cgr", "sma") else {"error": str(e)}
                        resultados[k] = res
                    try:
                        hf = fut_hf.result(timeout=8.0)
                    except (concurrent.futures.TimeoutError, TimeoutError):
                        hf = {"resultados": [], "citas": [], "error": "Hugging Face no respondió: timeout"}
                    except Exception as e:
                        hf = {"resultados": [], "citas": [], "error": f"Hugging Face no respondió: {str(e)[:160]}"}

                if hasattr(reg, "_set_cached"):
                    try:
                        reg._set_cached("all", consulta, resultados)
                    except Exception:
                        pass

        citas_halladas: List[Dict[str, Any]] = []
        if isinstance(resultados, dict):
            resultados["huggingface"] = hf.get("resultados", [])
        if isinstance(resultados, dict):
            for organismo, valor in resultados.items():
                if organismo in ("query", "huggingface"):
                    continue
                for it in _items_del_organismo(valor)[:3]:
                    ident = str(it.get("rol") or it.get("numero") or it.get("nombre")
                                or it.get("materia") or it.get("title") or it.get("titulo")
                                or it.get("docId") or "")
                    if it.get("rol") and it.get("caratula"):
                        ident = f"{it['rol']} ({it['caratula']})"
                    elif it.get("numero") and it.get("fecha"):
                        ident = f"Dictamen {it['numero']} de {it['fecha']}"
                    elif it.get("numero"):
                        ident = f"Dictamen {it['numero']}"

                    if not ident:
                        continue
                    texto = str(it.get("texto") or it.get("doctrina") or it.get("materia")
                                or it.get("conclusiones") or it.get("resumen")
                                or it.get("snippet") or "")[:600]
                    url = str(it.get("url") or it.get("url_huggingface") or it.get("link") or it.get("pdfUrl") or it.get("enlace") or "")
                    citas_halladas.append(formatear_cita(
                        str(organismo).upper(), str(ident),
                        url=url,
                        texto=texto))
        citas_halladas.extend(hf.get("citas") or [])
        return {"consulta": consulta, "resultados": resultados, "citas": citas_halladas}
    if name == "grafo_ver_corpus":
        return _ver_corpus(legal_graphify_engine, args.get("consulta"), int(args.get("max_nodos") or 250))
    elif name == "grafo_ver_caso":
        return grafo_vista.ver_caso(args.get("ruta", ""))
    elif name == "generar_grafo_vinculos":
        return build_quick_graph(
            nodes_list=args.get("nodes", []),
            edges_list=args.get("edges", []),
            title=args.get("title", "Red de Vínculos")
        )
    elif name == "doctrina_search":
        q = args.get("query")
        if not q:
            return {"error": "El parámetro 'query' es obligatorio."}
        try:
            lim = int(args.get("limit", 5))
        except (ValueError, TypeError):
            lim = 5
        kwargs_doc: Dict[str, Any] = {
            "query": q,
            "area": args.get("area"),
            "autor": args.get("autor"),
            "limit": lim,
        }
        if args.get("hibrido"):
            kwargs_doc["hibrido"] = True
        locales = search_doctrina(**kwargs_doc)
        return _citas_en_items({
            "query": q,
            "resultados": _con_revistas_del_mapa(locales, q, lim, args.get("area"), args.get("autor"))
        }, "Doctrina", campos_clave=("autor", "obra"), campo_texto="definicion")
    elif name == "doctrina_get_institucion":
        nom = args.get("nombre")
        if not nom:
            return {"error": "El parámetro 'nombre' es obligatorio."}
        res = doctrina_get_inst(nombre_o_termino=nom, area=args.get("area"))
        if not res:
            return {"error": f"No se encontró institución doctrinal para '{nom}'."}
        return res
    elif name == "doctrina_list_obras":
        return {"obras_indexadas": doctrina_list_obras()}
    elif name == "doctrina_ingestar_documento":
        fp = args.get("file_path")
        if not fp:
            return {"error": "El parámetro 'file_path' es obligatorio."}
        from doc2md_ingestor import ingestar_documento_doctrinal
        return ingestar_documento_doctrinal(
            file_path=fp,
            area=args.get("area", "civil"),
            tratadista=args.get("tratadista", ""),
            obra=args.get("obra", ""),
            materia=args.get("materia", ""),
            actualizar_grafo=bool(args.get("actualizar_grafo", True)),
            target_path=args.get("target_path"),
            motor_grafo=legal_graphify_engine
        )
    elif name == "academia_judicial_buscar_guias":
        q = args.get("query")
        if not q:
            return {"error": "El parámetro 'query' es obligatorio."}
        return _citas_en_items(aj_client.search_guias(q, args.get("materia")), "Academia Judicial",
                               campos_clave=("titulo", "materia"), campo_texto="descripcion")
    elif name == "biblioteca_compilar_manifiesto":
        bundles = bool(args.get("generar_bundles", False))
        manif = library_sync_mgr.compilar_manifiesto_corpus()
        if bundles:
            tar = library_sync_mgr.empaquetar_tar_gz()
            drive = library_sync_mgr.preparar_bundle_google_drive()
            manif["tar_gz"] = tar
            manif["drive_bundle"] = drive
        return manif
    elif name == "huggingface_search_dataset":
        q = args.get("query")
        filtros: Dict[str, Any] = {clave: args[clave] for clave in ("rol", "norma", "coleccion", "entidad")
                                   if args.get(clave)}
        if not q and not (set(filtros) - {"coleccion"}):
            return {"error": "El parámetro 'query' es obligatorio."}
        from online_library_sync import consultar_huggingface_dataset
        return consultar_huggingface_dataset(query=q or "", limit=int(args.get("limit") or 5), **filtros)
    elif name == "graphify_resumen_comunidades":
        return legal_graphify_engine.resumen_por_comunidades(int(args.get("top_n") or 12))
    elif name == "graphify_consulta_subgrafo":
        q = args.get("query")
        if not q:
            return {"error": "El parámetro 'query' es obligatorio (ej. 'simulacion', 'imprevision', 'nulidad')."}
        hops = int(args.get("max_hops", 1))
        incluir_mermaid = bool(args.get("incluir_mermaid", False))
        res = legal_graphify_engine.consultar_subgrafo(q, max_hops=hops)
        if incluir_mermaid and res.get("encontrado"):
            res["diagrama_mermaid"] = legal_graphify_engine.exportar_subgrafo_mermaid(q, max_hops=hops)
        return _con_avisos(res)
    elif name == "graphify_trazar_camino":
        orig = args.get("origen")
        dest = args.get("destino")
        if not orig or not dest:
            return {"error": "Se requieren 'origen' y 'destino' para trazar el camino relacional."}
        max_c = int(args.get("max_caminos", 3))
        solo_sust = bool(args.get("solo_sustantivo", False))
        return _con_avisos(legal_graphify_engine.encontrar_camino(orig, dest, max_caminos=max_c, solo_sustantivo=solo_sust))
    elif name == "graphify_explicar_institucion":
        q = args.get("query")
        if not q:
            return {"error": "El parámetro 'query' es obligatorio."}
        return _con_avisos(legal_graphify_engine.explicar_institucion(q))
    elif name == "graphify_analizar_impacto":
        obj = args.get("objetivo")
        if not obj:
            return {"error": "El parámetro 'objetivo' es obligatorio (norma o institución)."}
        return _con_avisos(legal_graphify_engine.analizar_impacto_normativo(obj))
    elif name == "graphify_god_nodes":
        top = int(args.get("top_n", 10))
        solo_sust = bool(args.get("solo_sustantivo", False))
        return _con_avisos(legal_graphify_engine.calcular_god_nodes(top_n=top, solo_sustantivo=solo_sust))
    elif name == "jurimetria_analizar_corpus":
        import jurimetria

        modo = str(args.get("modo") or "completo").strip().lower()
        coleccion = str(args.get("coleccion") or "cs").strip().lower()
        norma_filtro = args.get("norma_filtro")
        agrupacion = str(args.get("agrupacion") or "anio").strip().lower()
        top_k = int(args.get("top_k") or 15)

        if modo == "red_citaciones":
            return _con_avisos(jurimetria.analizar_red_citaciones(
                motor=legal_graphify_engine,
                coleccion=args.get("coleccion"),
                norma_filtro=norma_filtro,
                top_k=top_k,
            ))
        if modo == "longitudinal":
            return jurimetria.estadisticas_longitudinales(
                coleccion=coleccion,
                agrupacion=agrupacion,
                incluir_baremo=True,
            )
        if modo == "muestra_validacion":
            return jurimetria.generar_muestra_validacion_humana(
                coleccion=coleccion,
                n=int(args.get("n_muestra") or 50),
                semilla=int(args.get("semilla") or 42),
            )
        return _con_avisos({
            "modo": "completo",
            "red_citaciones": jurimetria.analizar_red_citaciones(
                motor=legal_graphify_engine,
                coleccion=args.get("coleccion"),
                norma_filtro=norma_filtro,
                top_k=top_k,
            ),
            "estadisticas_longitudinales": jurimetria.estadisticas_longitudinales(
                coleccion=coleccion,
                agrupacion=agrupacion,
                incluir_baremo=True,
            ),
        })
    elif name == "jurimetria_exportar_investigacion":
        import re as _re
        import jurimetria

        tema = str(args.get("tema") or "").strip()
        if not tema:
            return {"error": "El parámetro 'tema' es obligatorio."}
        carpeta = str(args.get("carpeta_salida") or "").strip()
        if not carpeta:
            slug_t = _re.sub(r"[^a-z0-9]+", "_", tema.lower()).strip("_")[:48] or "corpus"
            carpeta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exports", "investigacion", slug_t)
        return jurimetria.exportar_paquete_investigacion(
            tema=tema,
            carpeta_salida=carpeta,
            formatos=args.get("formatos"),
            incluir_muestra_validacion=True,
            n_muestra=int(args.get("n_muestra") or 50),
            semilla=int(args.get("semilla") or 42),
            coleccion_longitudinal=str(args.get("coleccion_longitudinal") or "cs"),
            motor=legal_graphify_engine,
        )
    return None


from servidor import crear_proxies

_PROPIOS = frozenset(globals())
_DEFAULTS_LAZY = crear_proxies(
    "CODIGOS", "_citas_en_items", "_con_avisos", "_detectar_dominios_estatales",
    "_doctrina_para_consulta", "_hf_para_consulta", "_items_del_organismo",
    "_normas_para_consulta", "_organismos_para_consulta", "_registro_estatal",
    "_subgrafo_para_consulta", "aj_client", "build_quick_graph", "detectar_normas",
    "doctrina_get_inst", "doctrina_list_obras", "enviar_progreso", "formatear_cita",
    "grafo_vista", "legal_graphify_engine", "library_sync_mgr", "search_doctrina",
)
globals().update(_DEFAULTS_LAZY)
