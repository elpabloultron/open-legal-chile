"""Herramientas del corpus: consulta maestra, doctrina, grafo de conocimiento y biblioteca."""
from typing import TYPE_CHECKING, Any, Optional
from citas_legales import CODIGOS, detectar_normas, formatear_cita


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
        _doctrina_para_consulta,
        _hf_para_consulta,
        _items_del_organismo,
        _normas_para_consulta,
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
    """Trae los nombres compartidos de mcp_server.py (helpers, clientes, motores).

    Corre en cada despacho: los bloques movidos usan los mismos objetos vivos del servidor,
    incluidas las sustituciones que hagan las pruebas con monkeypatch."""
    from config import servidor_actual
    _m = servidor_actual()
    _g = globals()
    _g.update({k: v for k, v in vars(_m).items() if k not in _PROPIOS})


TOOLS = [
    {
        "name": "consulta_maestra",
        "description": "PRIMER PASO OBLIGATORIO de toda consulta jurídica: consulta el dataset de Hugging Face, "
                       "la doctrina canónica, el grafo y las normas chilenas detectadas en la consulta, y devuelve "
                       "las fuentes con su TEXTO LITERAL y su corchete de cita listo para pegar. Usala antes de "
                       "responder aunque creas saber la respuesta: el producto no cita de memoria. Si la materia "
                       "es ambiental (SMA, SEIA/RCA, daño ambiental, humedales, Tribunales Ambientales), el primer "
                       "paso es el módulo `ambiental_consulta_maestra`, que cubre además los anuarios, boletines y "
                       "la biblioteca ambiental completos.",
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
        "description": "Busca un término a la vez en los 10 organismos del Estado (BCN, CGR, DT, PJUD, TC, CNE, "
                       "Panel de Expertos, CMF, SII, SMA/TDLC) y devuelve los resultados con sus citas listas.",
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
        "description": "Busca en el canon dogmático de manuales y tratados jurídicos chilenos más citados (Barros Bourie, Ramos Pazos, Peñailillo, Maturana, Bermúdez, Cury, Gamonal, Cea Egaña) mediante búsqueda por relevancia semántica FTS5 y BM25.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término o concepto dogmático a buscar (ej. 'clausula penal', 'culpa infraccional', 'tutela laboral')"},
                "area": {"type": "string", "description": "Área del derecho (opcional: 'Civil', 'Procesal', 'Penal', 'Laboral', 'Administrativo', 'Constitucional')"},
                "autor": {"type": "string", "description": "Nombre o apellido del tratadista (opcional: 'Barros', 'Ramos Pazos', 'Cury')"},
                "limit": {"type": "integer", "description": "Cantidad máxima de resultados (por defecto 5)"}
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
        "description": "Convierte documentos (PDF, DOCX, TXT, MD) o textos a Markdown canónico de alta densidad dogmática (normas RAE/ASALE y citas chilenas BCN/CS) y actualiza automáticamente el Knowledge Graph (legal_knowledge_graph.json) y el índice SQLite FTS5 de doctrina.",
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
                    "description": "Si es True, asimila y reconstruye de inmediato el Knowledge Graph de LegalGraphify (legal_knowledge_graph.json).",
                    "default": True
                },
                "target_path": {
                    "type": "string",
                    "description": "Ruta de destino personalizada para el archivo .md generado (opcional)."
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
        "description": "Consulta el repositorio público oficial en Hugging Face Datasets Hub (pablobenavidesj/doctrina-jurisprudencia-chile) y recupera contexto y enlaces directos con citas oficiales.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término de búsqueda doctrinal o institucional (ej. 'responsabilidad', 'despido', 'contratos')"},
                "limit": {"type": "integer", "description": "Número máximo de archivos o recursos a devolver (por defecto 5)", "default": 5}
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
                "max_hops": {"type": "integer", "description": "Radio de saltos relacionales en el grafo (por defecto 1)", "default": 1},
                "incluir_mermaid": {"type": "boolean", "description": "Si es True, incluye el diagrama Mermaid renderizable del subgrafo", "default": False}
            },
            "required": ["query"]
        }
    },
    {
        "name": "graphify_trazar_camino",
        "description": "Calcula y traza los caminos relacionales mínimos entre dos conceptos o normas jurídicas en LegalGraphify, deduciendo cadenas de subsunción y argumentación dogmática.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "origen": {"type": "string", "description": "Concepto o norma jurídica de inicio (ej. 'simulacion', 'incumplimiento')"},
                "destino": {"type": "string", "description": "Concepto o norma jurídica de fin (ej. 'nulidad', 'indemnizacion')"},
                "max_caminos": {"type": "integer", "description": "Número máximo de rutas mínimas a retornar (por defecto 3)", "default": 3}
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
        "description": "Identifica los pilares dogmáticos estructurales (God Nodes) del sistema jurídico chileno según algoritmos de PageRank y centralidad sobre el Knowledge Graph de doctrina y normas.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "top_n": {"type": "integer", "description": "Cantidad de instituciones y normas principales a retornar (por defecto 10)", "default": 10}
            }
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
    return {"cita": formatear_cita("BCN", ident, url=url, texto=recorte)}


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
    return {
        "total": len(referencias),
        "citas": citas,
        "faltantes": faltantes,
        "resultados": resultados,
        "como_citar": ("Pegá cada cita con su texto literal; lo que esté en `faltantes` "
                       "se declara como «sin fuente verificable»."),
    }


def despachar(name: str, args: dict) -> Any:
    _refrescar()
    if name == "consulta_maestra":
        consulta = (args.get("consulta") or args.get("query") or args.get("q") or args.get("termino") or "").strip()
        if not consulta:
            return {"error": "El parámetro 'consulta' (o 'query') es obligatorio."}
        lim = int(args.get("max_fuentes") or 3)
        # Los cuatro sondeos son independientes (HF, doctrina, normas, subgrafo):
        # en paralelo la consulta espera al más lento, no a la suma.
        enviar_progreso("Consulta maestra: 4 sondeos en paralelo (Hugging Face, doctrina, BCN, subgrafo)",
                        0, 4)

        def _anunciar(etiqueta: str, hechos: int):
            def _envolver(fn):
                def _paso(*a, **k):
                    resultado = fn(*a, **k)
                    enviar_progreso(f"{etiqueta} listo", hechos, 4)
                    return resultado
                return _paso
            return _envolver

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="consulta") as pool:
            f_hf = pool.submit(_anunciar("Hugging Face", 1)(_hf_para_consulta), consulta, lim)
            f_doctrina = pool.submit(_anunciar("Doctrina", 2)(_doctrina_para_consulta), consulta, lim)
            f_normas = pool.submit(_anunciar("Normas BCN", 3)(_normas_para_consulta), consulta)
            f_subgrafo = pool.submit(_anunciar("Subgrafo", 4)(_subgrafo_para_consulta), consulta)
            hf, doctrina, normas, subgrafo = (f_hf.result(), f_doctrina.result(),
                                              f_normas.result(), f_subgrafo.result())
        citas: List[Dict[str, Any]] = list(hf.get("citas") or []) + list(doctrina.get("citas") or [])
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
        ) if not ok]
        return {
            "consulta": consulta,
            "hallazgos": {"huggingface": hf.get("resultados", []),
                          "doctrina": doctrina.get("resultados", []),
                          "normas": normas,
                          "subgrafo": subgrafo},
            "citas": citas,
            "faltantes": faltantes,
            "como_citar": "Pegá cada cita con su texto literal. En conversación: la respuesta primero y las "
                          "fuentes al final. En documentos: citas a pie de página (fuente · identificador · enlace).",
        }
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
        resultados = _registro_estatal().search_all(consulta)
        citas_halladas: List[Dict[str, Any]] = []
        if isinstance(resultados, dict):
            for organismo, valor in resultados.items():
                if organismo == "query":
                    continue
                for it in _items_del_organismo(valor)[:3]:
                    nombre = (it.get("nombre") or it.get("materia") or it.get("title")
                              or it.get("titulo") or it.get("docId"))
                    if not nombre:
                        continue
                    citas_halladas.append(formatear_cita(
                        str(organismo).upper(), str(nombre),
                        url=str(it.get("url") or it.get("pdfUrl") or it.get("enlace") or ""),
                        texto=str(it.get("texto") or it.get("conclusiones") or it.get("resumen")
                                  or it.get("snippet") or "")[:600]))
        return {"consulta": consulta, "resultados": resultados, "citas": citas_halladas}
    if name == "grafo_ver_corpus":
        return grafo_vista.ver_corpus(args.get("consulta"), int(args.get("max_nodos") or 250))
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
        return _citas_en_items({
            "query": q,
            "resultados": search_doctrina(
                query=q,
                area=args.get("area"),
                autor=args.get("autor"),
                limit=lim
            )
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
            target_path=args.get("target_path")
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
        if not q:
            return {"error": "El parámetro 'query' es obligatorio."}
        from online_library_sync import consultar_huggingface_dataset
        return consultar_huggingface_dataset(query=q, limit=int(args.get("limit") or 5))
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
        return _con_avisos(legal_graphify_engine.encontrar_camino(orig, dest, max_caminos=max_c))
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
        return _con_avisos(legal_graphify_engine.calcular_god_nodes(top_n=top))
    return None


_PROPIOS = frozenset(globals())
