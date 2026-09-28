"""Herramientas de la mesa de entrada, los agentes y NotebookLM."""
import threading
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover — los bloques usan los objetos vivos de mcp_server
    from mcp_server import (
        case_intake,
        nlm_client,
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
                "consulta": {"type": "string", "description": "la pregunta u objetivo, para que el plan apunte a eso"},
                "estudio_completo": {"type": "boolean",
                                     "description": "Si es True, realiza en un solo paso local el análisis, consulta de marco normativo BCN y doctrina FTS5, consolidando la respuesta sin turnos adicionales"}
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
    },
    {
        "name": "entrevista_estudio",
        "description": "Entrevista de arranque del estudio, sin consola: sin argumentos devuelve el cuestionario y "
                       "el perfil actual; con 'pregunta' y 'respuesta' guarda cada clave del perfil de práctica.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pregunta": {"type": "string", "description": "La clave o el texto de la pregunta (ej. 'tono procesal')"},
                "respuesta": {"type": "string", "description": "La respuesta del usuario (ej. '2' o 'formal')"},
                "base_dir": {"type": "string", "description": "Carpeta donde vive el perfil (por defecto, la actual)"}
            }
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
]


def _precalentar_normas_caso(analisis: dict) -> None:
    """Adelanta en segundo plano las leyes que menciona el caso (best-effort, hilo daemon).

    Medido el 2026-09-28: la primera consulta a cada ley paga red; adelantarla deja la caché
    caliente para cuando el abogado pregunte. Nada de esto puede fallar hacia afuera: es un
    adelanto, no una promesa.
    """
    import json as _json

    from citas_legales import detectar_normas

    numeros: list = []
    for norma in detectar_normas(_json.dumps(analisis, ensure_ascii=False)[:200_000]):
        if norma["familia"] != "ley":
            continue
        try:
            numero = int(norma["numero"])
        except (TypeError, ValueError):
            continue
        if 9000 <= numero <= 30000 and numero not in numeros:
            numeros.append(numero)
    if not numeros:
        return

    def _trabajo() -> None:
        try:
            from bcn_connector import BCNClient

            cliente = BCNClient()
            for numero in numeros[:8]:
                try:
                    cliente.get_ley(numero)
                except Exception:  # noqa: BLE001 — cada ley que falle se declara al usarla
                    continue
        except Exception:  # noqa: BLE001 — adelanto best-effort
            return

    threading.Thread(target=_trabajo, name="precalentar-normas", daemon=True).start()


def despachar(name: str, args: dict) -> Any:
    _refrescar()
    if name == "caso_analizar":
        if bool(args.get("estudio_completo", False)):
            resultado = case_intake.caso_estudio_completo(args.get("entrada", ""), args.get("tipo"),
                                                          args.get("consulta", ""))
        else:
            resultado = case_intake.caso_analizar(args.get("entrada", ""), args.get("tipo"),
                                                  args.get("consulta", ""))
        if isinstance(resultado, dict) and "error" not in resultado:
            _precalentar_normas_caso(resultado)
        return resultado
    elif name == "caso_ejecutar":
        return case_intake.caso_ejecutar(args.get("entrada", ""), args.get("tipo"),
                                         args.get("pasos"), int(args.get("limite_pasos") or 12))
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
    elif name == "entrevista_estudio":
        from cold_start import ColdStartInterviewEngine
        return ColdStartInterviewEngine.responder(args.get("pregunta", ""), args.get("respuesta", ""),
                                                  base_dir=args.get("base_dir", "."))
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
    return None


_PROPIOS = frozenset(globals())
