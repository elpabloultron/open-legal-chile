"""
Open Legal Chile — Servidor Maestro MCP (Model Context Protocol)
Expone los 10 conectores oficiales del Estado de Chile y herramientas forenses
para cualquier agente de IA (Antigravity/Gemini, Claude Code, Cursor, Codex)
a través del protocolo estándar MCP sobre stdio (JSON-RPC 2.0).
"""

import sys
import json
import os
from datetime import datetime

# Asegurar que el directorio de Open Legal Chile tenga prioridad en sys.path
_pkg_root = os.path.dirname(os.path.abspath(__file__))
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)

from typing import Any, Dict, List, Optional, Union

# Configurar encoding seguro UTF-8
try:
    if hasattr(sys.stdout, "reconfigure"):
        getattr(sys.stdout, "reconfigure")(encoding='utf-8')
    if hasattr(sys.stdin, "reconfigure"):
        getattr(sys.stdin, "reconfigure")(encoding='utf-8')
except Exception:
    pass

from bcn_connector import BCNClient
from cgr_connector import CGRClient
from dt_connector import DTClient
from cne_connector import CNEClient
from panel_expertos_connector import PanelExpertosClient
from cmf_connector import CMFClient
from sii_connector import SIIClient
from ambiental_connector import SMAClient
from tdlc_connector import TDLCClient
from pjud_connector import PJUDClient
from exporters import LegalDocumentExporter
from forensic_ocr import ForensicOCREngine
from pdf_dossier_compiler import LegalDossierCompiler
from notebooklm_connector import NotebookLMConnector
from infoprobidad_connector import InfoProbidadClient
from grafo_vinculos import build_quick_graph
from doctrina_connector import search_doctrina, get_institucion as doctrina_get_inst, list_obras as doctrina_list_obras
from examen_grado import ExamenGradoEngine
from docket_watcher import DocketWatcherEngine
from clinica_juridica import ClinicaJuridicaEngine
from privacidad_inapi import PrivacyARCOEngine, INAPIEngine
from cbr_titles import CBRTitleStudyEngine, JudicialPowerVerifier
from entes_publicos import validar_rut, consultar_ente
from sentencias_parser import SentenciaParserEngine, ProveidosParser
from tribunales_ambientales_connector import TribunalesAmbientalesClient
from academia_judicial_connector import AcademiaJudicialClient
from online_library_sync import OnlineLibrarySyncManager
from legal_graphify import LegalGraphifyEngine

# Inicializar clientes
bcn = BCNClient()
cgr = CGRClient()
dt = DTClient()
cne = CNEClient()
panel = PanelExpertosClient()
cmf = CMFClient()
sii = SIIClient()
sma = SMAClient()
tdlc = TDLCClient()
pjud = PJUDClient()
exporter = LegalDocumentExporter()
ocr_engine = ForensicOCREngine()
compiler = LegalDossierCompiler()
nlm_client = NotebookLMConnector()
infoprobidad_client = InfoProbidadClient()
grado_engine = ExamenGradoEngine()
docket_engine = DocketWatcherEngine()
clinica_engine = ClinicaJuridicaEngine()
arco_engine = PrivacyARCOEngine()
inapi_engine = INAPIEngine()
cbr_engine = CBRTitleStudyEngine()
power_verifier = JudicialPowerVerifier()
sentencia_engine = SentenciaParserEngine()
proveidos_engine = ProveidosParser()
ambientales_client = TribunalesAmbientalesClient()
aj_client = AcademiaJudicialClient()
library_sync_mgr = OnlineLibrarySyncManager()
legal_graphify_engine = LegalGraphifyEngine()

import case_intake
import grafo_vista

TOOLS = [
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
        "name": "caso_analizar",
        "description": (
            "Usala SIEMPRE que la persona pida analizar un caso, una carpeta de expediente, un "
            "expediente, unos documentos o 'este caso', aunque no nombre ninguna herramienta: frases "
            "como «¿podés analizar esta carpeta?», «analizame el caso de Ailin», «¿por dónde empiezo "
            "con esto?» o «mirá estos documentos y decime de qué se trata» son exactamente su "
            "entrada. Devuelve un PLAN: de qué se trata, qué herramientas usar y en qué orden, y qué "
            "falta para poder avanzar. No modifica nada ni consulta servicios externos: sólo lee lo "
            "que le pasás. La materia la decide con reglas (Rol/RIT y palabras clave chilenas), no "
            "adivinando; si no alcanza la información, lo dice."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "entrada": {"type": "string", "description": "ruta de la carpeta o del archivo, o el texto mismo"},
                "tipo": {"type": "string", "enum": ["carpeta", "texto", "consulta"],
                         "description": "cómo interpretar la entrada (por defecto se deduce)"},
                "consulta": {"type": "string", "description": "la pregunta u objetivo, para que el plan apunte a eso"}
            },
            "required": ["entrada"]
        }
    },
    {
        "name": "caso_ejecutar",
        "description": (
            "Ejecuta el plan de `caso_analizar`: consulta los servicios del Estado (BCN, PJUD, CGR, DT, "
            "SII, CMF, SMA...), busca en la doctrina indexada y lee los documentos de la carpeta. Puede "
            "demorar, porque cada paso va a la fuente real. Un paso que falla queda anotado con su "
            "error: nunca devuelve un resultado inventado."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "entrada": {"type": "string"},
                "tipo": {"type": "string", "enum": ["carpeta", "texto", "consulta"]},
                "pasos": {"type": "array", "items": {"type": "integer"},
                          "description": "números de paso a ejecutar (por defecto, todos hasta el límite)"},
                "limite_pasos": {"type": "integer", "default": 12}
            },
            "required": ["entrada"]
        }
    },
    {
        "name": "bcn_get_codigo",
        "description": "Consulta artículos o estructura de los 9 Códigos de la República de Chile (civil, trabajo, cpc, penal, comercio, tributario, mineria, aguas, cpp) en la BCN.",
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
        "name": "pjud_search_jurisprudencia",
        "description": "Busca sentencias y fallos rectores de la Corte Suprema (Unificación Laboral, Constitucional, Civil) y Tribunal Constitucional (TC).",
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
        "name": "compile_legal_dossier",
        "description": "Compila un escrito judicial o denuncia en Markdown a formato PDF formal A4, ensamblando anexos probatorios con carátulas divisorias elegantes y marcadores jerárquicos nativos (TOC Bookmarks) para la OJV.",
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
        "name": "notebooklm_list_notebooks",
        "description": "Lista los cuadernos de investigación jurídica activos en Google NotebookLM con sus identificadores (notebook_id) y metadatos.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "notebooklm_create_notebook",
        "description": "Crea un nuevo cuaderno de investigación jurídica en Google NotebookLM y retorna su URL y notebook_id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Título del cuaderno de investigación"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "notebooklm_add_source",
        "description": "Sube un archivo local (PDF, escrito judicial, Markdown) como fuente documental a un cuaderno de Google NotebookLM.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "notebook_id": {"type": "string", "description": "ID del cuaderno en NotebookLM"},
                "file_path": {"type": "string", "description": "Ruta al archivo local a subir"},
                "title": {"type": "string", "description": "Título opcional para la fuente"}
            },
            "required": ["notebook_id", "file_path"]
        }
    },
    {
        "name": "notebooklm_query",
        "description": "Realiza una consulta fundada (grounded query) con citas sobre los documentos cargados en un cuaderno de NotebookLM.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "notebook_id": {"type": "string", "description": "ID del cuaderno en NotebookLM"},
                "prompt": {"type": "string", "description": "Pregunta o instrucción de análisis jurídico"}
            },
            "required": ["notebook_id", "prompt"]
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
        "description": "Consulta un Código de la República (civil, trabajo, cpc, penal, etc.) en una fecha histórica específica (YYYY-MM-DD) en la BCN.",
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
        "name": "ambiental_buscar_jurisprudencia",
        "description": "Busca en la jurisprudencia de los Tribunales Ambientales (1TA, 2TA, 3TA) y en los Compendios Anuales de Jurisprudencia Ambiental.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Materia ambiental (ej. 'humedales', 'daño ambiental', 'SEIA', 'consulta indigena')"},
                "tribunal": {"type": "string", "description": "Tribunal específico ('1TA', '2TA', '3TA') (opcional)"}
            },
            "required": ["query"]
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
        "name": "suite_telemetria_stats",
        "description": "Consulta estadísticas de adopción, descargas en PyPI, comunidad GitHub y métricas locales de la suite.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "suite_verificar_actualizacion",
        "description": "Comprueba si existe una versión más reciente de la Suite en PyPI o GitHub e informa la instrucción en lenguaje natural o comando para actualizarla.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "forzar": {"type": "boolean", "description": "Si es True, ignora la caché local de 24 horas y consulta en vivo", "default": False}
            }
        }
    },
    {
        "name": "suite_auto_update",
        "description": "Ejecuta la actualización automática y segura de Open Legal Chile Suite en el entorno local (vía git pull o pip install --upgrade).",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "graphify_consulta_subgrafo",
        "description": "Consulta el Knowledge Graph Jurídico de Doctrina Chilena (LegalGraphify), extrayendo subgrafos sintéticos hiper-densos (normas BCN, criterios CS, tratadistas y operativa procesal) con un ahorro medido del 31,9% al 90,5% de tokens según la institución (mediana 74,1%) respecto a la lectura del texto doctrinal completo. La medición es reproducible: docs/medicion_tokens.md.",
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
    {
        "name": "recurso_proteccion_generar",
        "description": "Genera y estandariza un Recurso de Protección conforme al Auto Acordado de la Corte Suprema (Acta N.° 94-2015) y OJV, produciendo escritos estructurados (.md, .html, .txt, .json) y expedientes PDF consolidando anexos con marcadores TOC.",
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
        "name": "agent_list",
        "description": "Lista el catálogo de los 17 agentes jurídicos especializados de Open Legal Chile con sus descripciones, competencias forenses y herramientas asignadas.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "agent_run",
        "description": "Ejecuta un agente jurídico especializado (ej. 'litigios', 'inmobiliario', 'probidad', 'laboral', 'dogmatico', 'forense', 'vigilante', 'clinica', 'regulatorio') para resolver un objetivo legal complejo coordinando autónomamente las herramientas de la suite en modo determinista soberano o LLM.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "Nombre o alias del agente a ejecutar (ej. 'litigios', 'inmobiliario', 'probidad', 'laboral', 'dogmatico', 'forense', 'vigilante', 'clinica', 'regulatorio')"
                },
                "task": {
                    "type": "string",
                    "description": "Misión, objetivo o consulta legal detallada para el agente"
                },
                "context": {
                    "type": "object",
                    "description": "Parámetros de contexto adicionales opcionales (ej. tribunal, fojas, cbr, fechas, hechos)"
                },
                "mode": {
                    "type": "string",
                    "description": "Modo de ejecución: 'auto' (detecta automáticamente), 'deterministic' (100% offline soberano) o 'llm'",
                    "default": "auto"
                }
            },
            "required": ["agent_name", "task"]
        }
    },
    {
        "name": "agent_export_subagents",
        "description": "Genera y exporta plantillas y perfiles de subagentes jurídicos para asistentes de IA como Claude Code (.claude/agents/*.md) y Cursor (.cursor/rules/*.mdc).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_dir": {
                    "type": "string",
                    "description": "Directorio destino para guardar los archivos de configuración (opcional)"
                }
            }
        }
    }
]

def _con_avisos(resultado):
    """
    Añade los avisos del motor del grafo al payload de la herramienta, si los hay.
    Nunca cambia la forma de la respuesta cuando no hay avisos (el harness ya depende
    de esas claves): solo agrega 'advertencias' cuando el motor tuvo que resolver algo
    de una manera que conviene que el agente sepa (p. ej. el grafo publicado estaba
    corrupto y se reconstruyó, o la consulta se resolvió por texto del corpus y no por
    nombre de institución).
    """
    avisos = list(getattr(legal_graphify_engine, "advertencias", []) or [])
    if avisos and isinstance(resultado, dict) and "error" not in resultado:
        return {**resultado, "advertencias": avisos}
    return resultado


def handle_tool_call(name: str, args: Dict[str, Any]) -> Any:
    try:
        args = args or {}
        if name == "grafo_ver_corpus":
            return grafo_vista.ver_corpus(args.get("consulta"), int(args.get("max_nodos") or 250))
        elif name == "grafo_ver_caso":
            return grafo_vista.ver_caso(args.get("ruta", ""))
        elif name == "caso_analizar":
            return case_intake.caso_analizar(args.get("entrada", ""), args.get("tipo"),
                                             args.get("consulta", ""))
        elif name == "caso_ejecutar":
            return case_intake.caso_ejecutar(args.get("entrada", ""), args.get("tipo"),
                                             args.get("pasos"), int(args.get("limite_pasos") or 12))
        if name == "bcn_get_codigo":
            cod = args.get("codigo")
            if not cod:
                return {"error": "El parámetro 'codigo' es obligatorio (ej. 'civil', 'trabajo', 'cpc')."}
            return bcn.get_codigo(cod, args.get("articulo"))
        elif name == "bcn_get_ley":
            try:
                num = int(args.get("numero") or 0)
            except (ValueError, TypeError):
                return {"error": f"Número de ley inválido: {args.get('numero')}"}
            if num <= 0:
                return {"error": "El número de ley debe ser un entero positivo."}
            art = args.get("articulo")
            return bcn.get_articulo_ley(num, art) if art else bcn.get_ley(num)
        elif name == "cgr_search_jurisprudencia":
            return cgr.search_jurisprudencia(args.get("query", ""))
        elif name == "cgr_search_auditorias":
            return cgr.search_auditorias(args.get("query", ""))
        elif name == "dt_search_doctrina":
            return dt.search_dictamenes(args.get("query", ""), limit=10)
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
        elif name == "sii_search_circulares":
            return sii.search_circulares(args.get("query", ""))
        elif name == "sma_search_sancionatorios":
            return sma.search_sancionatorios(nombre=args.get("query", ""))
        elif name == "tdlc_search_jurisprudencia":
            return tdlc.search_jurisprudencia(args.get("query", ""))
        elif name == "pjud_search_jurisprudencia":
            return pjud.search_jurisprudencia(args.get("query", ""), sala=args.get("sala"))
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
        elif name == "compile_legal_dossier":
            md_content = args.get("markdown_content")
            out_pdf = args.get("output_pdf_path")
            if not md_content or not out_pdf:
                return {"error": "Se requieren 'markdown_content' y 'output_pdf_path' para compilar el expediente."}
            return compiler.compile(
                markdown_content=md_content,
                output_pdf_path=out_pdf,
                annexes=args.get("annexes"),
                mobile_preview_path=args.get("mobile_preview_path"),
                main_pdf_path=args.get("main_pdf_path"),
                title=args.get("title")
            )
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

            # 2. Compilar expedientes PDF si está habilitado
            pdf_info = None
            if compilar_pdf and compiler.is_available():
                fn = export_res["filename"]
                exports_dir = export_res["exportsDir"]
                main_pdf_path = os.path.join(exports_dir, f"{fn}_Caratula_OJV.pdf")
                dossier_pdf_path = os.path.join(exports_dir, f"{fn}_Completo_con_Anexos.pdf")

                with open(export_res["markdownPath"], "r", encoding="utf-8") as f:
                    md_text = f.read()

                pdf_res = compiler.compile(
                    markdown_content=md_text,
                    output_pdf_path=dossier_pdf_path,
                    main_pdf_path=main_pdf_path,
                    annexes=anexos,
                    title=f"Recurso de Protección — {tribunal}"
                )
                pdf_info = pdf_res

            res_final = dict(export_res)
            if pdf_info:
                res_final["pdf_compilation"] = pdf_info
            return res_final
        elif name == "agent_list":
            from agents_runtime import agent_runtime
            return agent_runtime.list_agents()
        elif name == "agent_run":
            from agents_runtime import agent_runtime
            ag_name = str(args.get("agent_name") or "")
            task = str(args.get("task") or "")
            context = args.get("context") or {}
            mode = str(args.get("mode") or "auto")
            res_ag = agent_runtime.run_agent(agent_name=ag_name, task=task, context=context, mode=mode)
            return res_ag.to_dict()
        elif name == "agent_export_subagents":
            from agents_runtime import agent_runtime
            target_dir = args.get("target_dir")
            return agent_runtime.export_subagents_config(target_dir=target_dir)
        elif name == "infoprobidad_get_dip":
            q_url = args.get("query_or_url")
            if not q_url:
                return {"error": "El parámetro 'query_or_url' es obligatorio."}
            return infoprobidad_client.get_declaracion(q_url)
        elif name == "notebooklm_list_notebooks":
            return {"cuadernos": nlm_client.list_notebooks()}
        elif name == "notebooklm_create_notebook":
            title = args.get("title")
            if not title:
                return {"error": "El parámetro 'title' es obligatorio."}
            return nlm_client.create_notebook(title)
        elif name == "notebooklm_add_source":
            nb_id = args.get("notebook_id")
            fpath = args.get("file_path")
            if not nb_id or not fpath:
                return {"error": "Se requieren 'notebook_id' y 'file_path'."}
            return nlm_client.add_source(
                notebook_id=nb_id,
                file_path=fpath,
                title=args.get("title")
            )
        elif name == "notebooklm_query":
            nb_id = args.get("notebook_id")
            prompt = args.get("prompt")
            if not nb_id or not prompt:
                return {"error": "Se requieren 'notebook_id' y 'prompt'."}
            return nlm_client.query(
                notebook_id=nb_id,
                prompt=prompt
            )
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
            return {
                "query": q,
                "resultados": search_doctrina(
                    query=q,
                    area=args.get("area"),
                    autor=args.get("autor"),
                    limit=lim
                )
            }
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
        elif name == "cpc_validar_mandato":
            txt = args.get("texto_mandato")
            if not txt:
                return {"error": "El parámetro 'texto_mandato' es obligatorio."}
            return power_verifier.auditar_mandato(txt)
        elif name == "bcn_get_ley_historica":
            num = int(args.get("numero") or 0)
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
        elif name == "tdlc_buscar_icg_y_dictamenes":
            q = args.get("query")
            if not q:
                return {"error": "El parámetro 'query' es obligatorio."}
            return tdlc.search_jurisprudencia(q)
        elif name == "cmf_buscar_sanciones":
            q = args.get("query")
            if not q:
                return {"error": "El parámetro 'query' es obligatorio."}
            return cmf.search_sanciones(q)
        elif name == "ambiental_buscar_jurisprudencia":
            q = args.get("query")
            if not q:
                return {"error": "El parámetro 'query' es obligatorio."}
            return ambientales_client.search_jurisprudencia(q, args.get("tribunal"))
        elif name == "academia_judicial_buscar_guias":
            q = args.get("query")
            if not q:
                return {"error": "El parámetro 'query' es obligatorio."}
            return aj_client.search_guias(q, args.get("materia"))
        elif name == "biblioteca_compilar_manifiesto":
            bundles = bool(args.get("generar_bundles", False))
            manif = library_sync_mgr.compilar_manifiesto_corpus()
            if bundles:
                tar = library_sync_mgr.empaquetar_tar_gz()
                drive = library_sync_mgr.preparar_bundle_google_drive()
                manif["tar_gz"] = tar
                manif["drive_bundle"] = drive
            return manif
        elif name == "suite_telemetria_stats":
            from stats_tracker import get_suite_adoption_metrics
            return get_suite_adoption_metrics()
        elif name == "suite_verificar_actualizacion":
            from update_checker import check_for_updates
            force = bool(args.get("forzar", False))
            return check_for_updates(force=force)
        elif name == "suite_auto_update":
            from update_checker import run_auto_update
            return run_auto_update()
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
        else:
            return {"error": f"Herramienta '{name}' no encontrada."}
    except Exception as e:
        return {"error": f"Error ejecutando '{name}': {str(e)}"}

def main():
    """Bucle principal JSON-RPC 2.0 para el servidor MCP."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            if not isinstance(req, dict):
                continue
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if req_id is None:
                # Las notificaciones (como notifications/initialized) no deben recibir respuesta
                continue

            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "open-legal-chile-mcp",
                            "version": "1.5.11"
                        }
                    }
                }
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": TOOLS
                    }
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                res = handle_tool_call(tool_name, tool_args)
                is_error = isinstance(res, dict) and "error" in res
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(res, ensure_ascii=False, indent=2)
                            }
                        ],
                        "isError": is_error
                    }
                }
            elif method == "ping":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {}
                }
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Método no encontrado: {method}"
                    }
                }

            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()

        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)}
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
