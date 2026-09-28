"""
Open Legal Chile — Servidor Maestro MCP (Model Context Protocol)
Expone los 10 conectores oficiales del Estado de Chile y herramientas forenses
para cualquier agente de IA (Antigravity/Gemini, Claude Code, Cursor, Codex)
a través del protocolo estándar MCP sobre stdio (JSON-RPC 2.0).
"""

import sys
import json
import os
import pathlib
import threading
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
from docx_compiler import WordDossierCompiler
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
from citas_legales import CODIGOS, detectar_normas, formatear_cita

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
word_compiler = WordDossierCompiler()
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


def _precalentar_hf() -> None:
    """Warmup del listado del dataset de Hugging Face (memoizado 10 min por proceso).

    Medido el 2026-09-28: la primera consulta HF de un proceso nuevo pagaba ~18 s de listado.
    Sin red o sin token se salta en silencio: cada herramienta lo declarará cuando se use.
    """
    from online_library_sync import _listar_archivos_hf
    _listar_archivos_hf("pablobenavidesj/doctrina-jurisprudencia-chile")


def precalentar_caches() -> None:
    """Deja calientes las cachés caras del arranque, sin bloquear el handshake MCP.

    El grafo publicado (0,3 s) y el listado de Hugging Face (~18 s la primera vez por proceso)
    se preparan en un hilo de fondo al arrancar el server. Nada de esto puede tumbar el server:
    si falta el artefacto o la red, se sigue — y las herramientas lo dirán al usarse.
    """
    try:
        legal_graphify_engine.cargar_grafo_json()
    except Exception:  # noqa: BLE001 — un precalentado caído no puede tumbar el server
        pass
    try:
        _precalentar_hf()
    except Exception:  # noqa: BLE001 — sin red o sin token, se dirá al usarla
        pass


import case_intake
import grafo_vista

# ── Herramientas: los esquemas y el despacho viven en servidor/ (un módulo por dominio) ──
# Acá quedan el protocolo, los helpers compartidos y el ensamblado; el orden original de
# listado se conserva porque los harnesses lo ven.
from servidor import ambiental as _ambiental, casos as _casos, conectores as _conectores
from servidor import corpus as _corpus, forense as _forense, suite as _suite

_DOMINIOS = (_ambiental, _corpus, _conectores, _forense, _casos, _suite)
_DOMINIOS_DESPACHO = tuple(_d.despachar for _d in _DOMINIOS)
_POR_NOMBRE: Dict[str, Dict[str, Any]] = {t["name"]: t for _d in _DOMINIOS for t in _d.TOOLS}
ORDEN_ORIGEN: List[str] = [
    "grafo_ver_corpus",
    "grafo_ver_caso",
    "caso_analizar",
    "caso_ejecutar",
    "bcn_get_codigo",
    "bcn_get_ley",
    "cgr_search_jurisprudencia",
    "cgr_search_auditorias",
    "dt_search_doctrina",
    "cne_get_centrales_y_proyectos",
    "panel_expertos_search",
    "cmf_search_normativa",
    "sii_search_circulares",
    "sma_search_sancionatorios",
    "tdlc_search_jurisprudencia",
    "pjud_search_jurisprudencia",
    "export_brief_ojv",
    "ocr_extract_pdf",
    "compile_legal_dossier",
    "infoprobidad_get_dip",
    "notebooklm_list_notebooks",
    "notebooklm_create_notebook",
    "notebooklm_add_source",
    "notebooklm_query",
    "generar_grafo_vinculos",
    "doctrina_search",
    "doctrina_get_institucion",
    "doctrina_list_obras",
    "doctrina_ingestar_documento",
    "grado_interrogar",
    "grado_generar_cedula",
    "grado_obtener_flashcards",
    "vigilante_analizar_resolucion",
    "vigilante_radar_normativo",
    "vigilante_contrato_plazos",
    "clinica_lenguaje_claro",
    "clinica_intake_social",
    "clinica_auditar_borrador",
    "privacidad_tramitar_arco",
    "inapi_cease_and_desist",
    "inapi_evaluar_marca",
    "cbr_estudio_titulos",
    "cbr_checklist_documentos",
    "cpc_validar_mandato",
    "bcn_get_ley_historica",
    "bcn_get_codigo_historico",
    "rut_validar_chile",
    "entes_consultar_organo",
    "pjud_analizar_sentencia",
    "pjud_interpretar_proveido",
    "sii_buscar_resoluciones_y_oficios",
    "sii_oficios_por_anio",
    "sii_descargar_oficio",
    "sii_actos_regionales",
    "sii_convenios_internacionales",
    "sii_jurisprudencia_judicial",
    "tdlc_buscar_icg_y_dictamenes",
    "cmf_buscar_sanciones",
    "ambiental_buscar_jurisprudencia",
    "ambiental_consulta_maestra",
    "academia_judicial_buscar_guias",
    "biblioteca_compilar_manifiesto",
    "huggingface_search_dataset",
    "suite_telemetria_stats",
    "suite_verificar_actualizacion",
    "suite_auto_update",
    "graphify_resumen_comunidades",
    "graphify_consulta_subgrafo",
    "graphify_trazar_camino",
    "graphify_explicar_institucion",
    "graphify_analizar_impacto",
    "graphify_god_nodes",
    "recurso_proteccion_generar",
    "agent_list",
    "agent_run",
    "agent_export_subagents",
    "consulta_maestra",
    "cita_texto",
    "suite_doctor",
    "suite_instalar",
    "ocr_plan_documento",
    "busqueda_universal",
    "critique_documento",
    "generar_documento",
    "entrevista_estudio",
    "skills_listar",
    "skill_ver",
]
if sorted(_POR_NOMBRE) != sorted(ORDEN_ORIGEN):
    raise RuntimeError("servidor/: los dominios no cubren exactamente las herramientas esperadas")
TOOLS: List[Dict[str, Any]] = [_POR_NOMBRE[_n] for _n in ORDEN_ORIGEN]

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


def _hf_para_consulta(query: str, lim: int = 3) -> Dict[str, Any]:
    """El corpus publicado en Hugging Face, con sus pasajes citables (paso 0 de toda consulta)."""
    try:
        from online_library_sync import consultar_huggingface_dataset
        return consultar_huggingface_dataset(query=query, limit=lim)
    except Exception as e:  # noqa: BLE001 — la respuesta no se cae si el Hub no está
        return {"resultados": [], "citas": [], "error": f"Hugging Face no respondió: {str(e)[:160]}"}


def _doctrina_para_consulta(query: str, lim: int = 3) -> Dict[str, Any]:
    """La doctrina canónica del corpus, con su corchete y su texto."""
    try:
        resultados = search_doctrina(query=query, limit=lim) or []
        citas = []
        for r in resultados:
            texto = str(r.get("definicion") or r.get("snippet") or "")[:900]
            if not texto:
                continue
            citas.append(formatear_cita("Doctrina", f"{r.get('autor') or 's/d'}, {r.get('obra') or 'obra'}",
                                        url=r.get("fuente_huggingface", ""), texto=texto))
        return {"resultados": resultados, "citas": citas}
    except Exception as e:  # noqa: BLE001
        return {"resultados": [], "citas": [], "error": str(e)[:160]}


def _url_codigo_bcn(obra: str) -> str:
    try:
        from bcn_connector import CODIGOS_REPUBLICA
        return f"https://www.bcn.cl/leychile/navegar?idNorma={CODIGOS_REPUBLICA[obra.lower()]['idNorma']}"
    except Exception:  # noqa: BLE001
        return "https://www.bcn.cl/leychile/"


def _normas_para_consulta(query: str) -> List[Dict[str, Any]]:
    """Trae el texto literal de las normas mencionadas en la consulta (códigos y leyes)."""
    try:
        normas = detectar_normas(query)[:3]
    except Exception:  # noqa: BLE001
        return []
    salida: List[Dict[str, Any]] = []
    for norma in normas:
        try:
            if norma["familia"] == "codigo":
                dato = bcn.get_codigo(norma["obra"], norma["articulo"])
                if dato.get("texto"):
                    dato["url"] = _url_codigo_bcn(norma["obra"])
                salida.append(dato)
            else:
                numero = int(norma["numero"])
                if norma.get("articulo"):
                    dato = bcn.get_articulo_ley(numero, norma["articulo"])
                    dato["url"] = f"https://www.bcn.cl/leychile/navegar?idLey={numero}"
                    dato["ley_numero"] = numero
                else:
                    dato = bcn.get_ley(numero)
                    dato["url"] = f"https://www.bcn.cl/leychile/navegar?idNorma={dato.get('normaId', '')}"
                salida.append(dato)
        except Exception as e:  # noqa: BLE001
            salida.append({"error": str(e)[:160], "etiqueta": norma.get("etiqueta", "")})
    return salida


def _bcn_para_citas():
    """Cliente BCN para resolver citas (indirección: permite probar sin red)."""
    return bcn


def _subgrafo_para_consulta(query: str, hops: int = 1) -> Dict[str, Any]:
    """El subgrafo dogmático alrededor de la consulta (si el grafo no responde, va vacío)."""
    try:
        return legal_graphify_engine.consultar_subgrafo(query, max_hops=hops)
    except Exception:  # noqa: BLE001
        return {}


def _con_citas(resultado: Any, fuente: str, identificador: str, url: str = "", campo_texto: str = "texto") -> Any:
    """Añade a un resultado individual la cita con su texto literal (aditivo, nunca reemplaza)."""
    if not isinstance(resultado, dict):
        return resultado
    texto = str(resultado.get(campo_texto) or "")
    if texto:
        resultado["citas"] = list(resultado.get("citas") or []) + [
            formatear_cita(fuente, identificador, url=url, texto=texto[:1200])]
    return resultado


def _citas_en_items(resultado: Any, fuente: str, campos_clave: tuple, campo_texto: str = "texto",
                    maximo: int = 3) -> Any:
    """Añade «citas» a cada ítem de una lista o de un dict con «resultados».

    Es aditivo a propósito: la forma de la respuesta (lista o dict) no cambia, para no romper a
    ningún consumidor; la cita viaja dentro del ítem, lista para pegar.
    """
    if isinstance(resultado, dict):
        items = None
        for clave in ("resultados", "dictamenes", "guias", "coincidencias", "items"):
            if isinstance(resultado.get(clave), list):
                items = resultado[clave]
                break
    elif isinstance(resultado, list):
        items = resultado
    else:
        return resultado
    for item in (items or [])[:maximo]:
        if not isinstance(item, dict):
            continue
        ident = ", ".join(str(item.get(c)).strip() for c in campos_clave if item.get(c))
        texto = str(item.get(campo_texto) or item.get("snippet") or item.get("resumen")
                    or item.get("materia") or "")
        if not ident or not texto:
            continue
        item["citas"] = list(item.get("citas") or []) + [
            formatear_cita(fuente, ident[:180], url=str(item.get("url") or item.get("url_pdf") or ""),
                           texto=texto[:900])]
    return resultado


def _registro_estatal():
    """Registro de conectores del Estado (indirección: permite probar sin red)."""
    from connectors.registry import StateRegistry
    return StateRegistry()


def _items_del_organismo(valor: Any) -> List[Dict[str, Any]]:
    """Normaliza la respuesta de un conector a una lista de resultados citables.

    Los conectores del Estado no son uniformes: unos devuelven listas (BCN, DT, PJUD) y otros un dict
    con «resultados» (CGR, SMA). Las listas traen además avisos honestos («este conector no cubre…»),
    que no son fuentes: acá se descartan para la cita y el payload completo los conserva.
    """
    if isinstance(valor, list):
        candidatos = valor
    elif isinstance(valor, dict):
        candidatos = next((valor[clave] for clave in ("resultados", "items", "docs")
                           if isinstance(valor.get(clave), list)), [])
    else:
        return []
    return [x for x in candidatos if isinstance(x, dict) and x.get("tipo") != "aviso"]


def _raiz() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent


def _listar_skills() -> Dict[str, Any]:
    """Las 18 skills y los 19 agentes reales del producto (el texto fijo de la CLI decía 7)."""
    skills = []
    for archivo in sorted((_raiz() / ".agents" / "skills").glob("*/SKILL.md")):
        texto = archivo.read_text(encoding="utf-8", errors="ignore")
        titulo = next((linea.lstrip("# ").strip() for linea in texto.splitlines() if linea.startswith("# ")),
                      archivo.parent.name)
        skills.append({"nombre": archivo.parent.name, "titulo": titulo})
    agentes = []
    for archivo in sorted((_raiz() / "agents").glob("*.json")):
        try:
            agentes.append(json.loads(archivo.read_text(encoding="utf-8")).get("name", archivo.stem))
        except Exception:  # noqa: BLE001 - un JSON roto no puede tumbar el listado
            agentes.append(archivo.stem)
    return {"skills": skills, "agentes": agentes}


def _texto_protocolo() -> str:
    """El protocolo de citación tal como está escrito en AGENTS.md (§2 quater)."""
    agentes = _raiz() / "AGENTS.md"
    if not agentes.exists():
        return "Protocolo no disponible: falta AGENTS.md en el paquete."
    texto = agentes.read_text(encoding="utf-8")
    inicio = texto.find("### 2 quater")
    if inicio == -1:
        return texto[:4000]
    fin = texto.find("\n---", inicio)
    return texto[inicio:fin if fin != -1 else inicio + 4000]


PROMPTS = [
    {
        "name": "protocolo_citas",
        "description": "Protocolo de respuesta obligatorio (§2 quater): Hugging Face primero, fuente oficial "
                       "después, cada cita con su texto literal y el formato de salida por tipo de documento.",
        "arguments": [],
        "_texto": (
            "Al responder una consulta jurídica chilena seguí este orden, sin excepciones:\n"
            "1. Primer paso: `consulta_maestra` (o `huggingface_search_dataset`). El corpus publicado en "
            "Hugging Face es la base citable; no respondas de memoria. Si la materia es ambiental (SMA, "
            "SEIA/RCA, daño ambiental, humedales, Tribunales Ambientales), el primer paso es el módulo "
            "`ambiental_consulta_maestra`.\n"
            "2. Después, la fuente oficial que corresponda: BCN (norma), DT/CGR/SII/CMF (dictamen), "
            "PJUD/TC/ambientales (fallo), Academia Judicial (guía).\n"
            "3. Antes de citar, traé el texto literal con `cita_texto` (o usá el bloque `citas` del "
            "resultado). Si la fuente no se pudo leer, decí «sin fuente verificable».\n"
            "4. Formato: en conversación, la respuesta primero y el bloque «Fuentes:» al final. En "
            "documentos, entregá Word (.docx editable) con citas a pie de página: fuente · identificador · enlace.\n"
            "5. Los corchetes van en el formato oficial: [BCN - Código Civil, Art. 1438], "
            "[Dictamen DT - ORD. N° …], [CS - Rol N° …], [CGR - …], [Academia Judicial - …], [SMAs/TA - …]."
        ),
    },
    {
        "name": "consulta_juridica_completa",
        "description": "Receta de punta a punta para una consulta o un caso: qué herramientas usar, en qué orden y "
                       "cómo cerrar la respuesta.",
        "arguments": [{"name": "consulta", "description": "La pregunta jurídica del usuario", "required": False}],
        "_texto": (
            "Consulta: {consulta}\n\n"
            "1. `consulta_maestra` con la consulta (trae corpus de Hugging Face + doctrina + grafo + normas, "
            "con texto literal y corchetes). Si la materia es ambiental, `ambiental_consulta_maestra`.\n"
            "2. Si hay que analizar documentos o una carpeta: `caso_analizar` y después `caso_ejecutar`.\n"
            "3. Para el texto de una norma puntual: `cita_texto`.\n"
            "4. Respondé primero y cerrá con el bloque «Fuentes:»; cada afirmación jurídica con su corchete y "
            "su texto literal. Lo que no se pudo traer se declara (campo `faltantes`), no se rellena."
        ),
    },
]


def _recursos_disponibles() -> List[Dict[str, str]]:
    return [
        {"uri": "openlegal://reglas/citacion", "name": "Protocolo de citación (§2 quater)",
         "description": "Cómo se responde y se cita: Hugging Face primero, texto literal obligatorio.",
         "mimeType": "text/markdown"},
        {"uri": "openlegal://catalogo/herramientas", "name": "Catálogo de herramientas MCP",
         "description": "Nombres y descripciones de todas las herramientas del servidor.",
         "mimeType": "application/json"},
        {"uri": "openlegal://reglas/integracion", "name": "Integración por harness",
         "description": "Comando por cliente (Antigravity, Claude Code, Cursor, VS Code, Codex, dsh) y verificación.",
         "mimeType": "text/markdown"},
    ]


def _leer_recurso(uri: str) -> Optional[Dict[str, str]]:
    if uri == "openlegal://reglas/citacion":
        return {"uri": uri, "mimeType": "text/markdown", "text": _texto_protocolo()}
    if uri == "openlegal://catalogo/herramientas":
        catalogo = [{"name": t["name"], "description": t.get("description", "")} for t in TOOLS]
        return {"uri": uri, "mimeType": "application/json",
                "text": json.dumps(catalogo, ensure_ascii=False, indent=2)}
    if uri == "openlegal://reglas/integracion":
        ruta = _raiz() / "docs" / "integracion-harness.md"
        if not ruta.exists():
            return None
        return {"uri": uri, "mimeType": "text/markdown", "text": ruta.read_text(encoding="utf-8")}
    return None


def handle_tool_call(name: str, args: Dict[str, Any]) -> Any:
    try:
        args = args or {}
        for _despachador in _DOMINIOS_DESPACHO:
            resultado = _despachador(name, args)
            if resultado is not None:
                return resultado
        return {"error": f"Herramienta '{name}' no encontrada."}
    except Exception as e:
        return {"error": f"Error ejecutando '{name}': {str(e)}"}

TOOL_PROFILES: Dict[str, List[str]] = {
    "laboral": [
        "caso_analizar", "caso_ejecutar", "bcn_get_codigo", "bcn_get_ley",
        "dt_search_doctrina", "pjud_search_jurisprudencia", "pjud_analizar_sentencia",
        "doctrina_search", "doctrina_get_institucion", "export_brief_ojv", "compile_legal_dossier"
    ],
    "inmobiliario": [
        "caso_analizar", "bcn_get_codigo", "bcn_get_ley", "cbr_estudio_titulos",
        "cbr_checklist_documentos", "cpc_validar_mandato", "doctrina_search",
        "doctrina_get_institucion", "export_brief_ojv", "compile_legal_dossier"
    ],
    "litigios": [
        "caso_analizar", "caso_ejecutar", "bcn_get_codigo", "bcn_get_ley",
        "pjud_search_jurisprudencia", "pjud_analizar_sentencia", "pjud_interpretar_proveido",
        "recurso_proteccion_generar", "cpc_validar_mandato", "doctrina_search",
        "doctrina_get_institucion", "export_brief_ojv", "compile_legal_dossier", "ocr_extract_pdf"
    ],
    "regulatorio": [
        "caso_analizar", "bcn_get_ley", "cgr_search_jurisprudencia", "cgr_search_auditorias",
        "infoprobidad_get_dip", "cmf_search_normativa", "cmf_buscar_sanciones",
        "sii_search_circulares", "sii_buscar_resoluciones_y_oficios", "sma_search_sancionatorios",
        "ambiental_buscar_jurisprudencia", "cne_get_centrales_y_proyectos", "panel_expertos_search",
        "tdlc_search_jurisprudencia", "tdlc_buscar_icg_y_dictamenes", "entes_consultar_organo",
        "export_brief_ojv"
    ],
    "corporativo": [
        "caso_analizar", "bcn_get_codigo", "bcn_get_ley", "cmf_search_normativa",
        "cmf_buscar_sanciones", "sii_search_circulares", "sii_buscar_resoluciones_y_oficios",
        "tdlc_search_jurisprudencia", "inapi_evaluar_marca", "inapi_cease_and_desist",
        "privacidad_tramitar_arco", "rut_validar_chile", "export_brief_ojv"
    ],
    "dogmatico": [
        "caso_analizar", "bcn_get_codigo", "bcn_get_ley", "doctrina_search",
        "doctrina_get_institucion", "doctrina_list_obras", "graphify_consulta_subgrafo",
        "graphify_trazar_camino", "graphify_explicar_institucion", "graphify_analizar_impacto",
        "graphify_god_nodes", "graphify_resumen_comunidades", "academia_judicial_buscar_guias",
        "grafo_ver_corpus", "huggingface_search_dataset"
    ],
    "clinica": [
        "clinica_lenguaje_claro", "clinica_intake_social", "clinica_auditar_borrador",
        "caso_analizar", "bcn_get_codigo", "bcn_get_ley", "export_brief_ojv"
    ]
}


def get_active_tools(profile_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Devuelve las herramientas activas según el perfil solicitado o la variable OPENLEGAL_PROFILE.
    
    Permite reducir la ventana de contexto de ~18.000 tokens a ~2.500 tokens para agentes especializados.
    """
    prof = (profile_name or os.environ.get("OPENLEGAL_PROFILE") or "").lower().strip()
    if prof and prof in TOOL_PROFILES:
        nombres = set(TOOL_PROFILES[prof])
        return [t for t in TOOLS if t["name"] in nombres]
    return TOOLS


def main():
    """Bucle principal JSON-RPC 2.0 para el servidor MCP."""
    profile_cli = None
    for i, a in enumerate(sys.argv):
        if a == "--profile" and i + 1 < len(sys.argv):
            profile_cli = sys.argv[i + 1]
        elif a.startswith("--profile="):
            profile_cli = a.split("=", 1)[1]

    tools_to_expose = get_active_tools(profile_cli)

    # Precalentado en segundo plano: la primera consulta no pagará el arranque en frío
    # (grafo publicado + listado HF). Si algo falla, el server sigue y se avisa al usar.
    threading.Thread(target=precalentar_caches, name="precalentado", daemon=True).start()

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
                            "tools": {},
                            # El harness no sólo ve las herramientas: también puede leer las reglas
                            # del producto (protocolo de citación) y el catálogo.
                            "prompts": {"listChanged": False},
                            "resources": {"listChanged": False, "subscribe": False}
                        },
                        "serverInfo": {
                            "name": "open-legal-chile-mcp",
                            "version": "1.10.0"
                        }
                    }
                }
            elif method == "prompts/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "prompts": [{clave: valor for clave, valor in prompt.items() if not clave.startswith("_")}
                                    for prompt in PROMPTS]
                    }
                }
            elif method == "prompts/get":
                nombre = params.get("name")
                elegido = next((p for p in PROMPTS if p["name"] == nombre), None)
                if elegido is None:
                    resp = {"jsonrpc": "2.0", "id": req_id,
                            "error": {"code": -32602, "message": f"Prompt desconocido: {nombre}"}}
                else:
                    texto = elegido["_texto"]
                    for clave, valor in (params.get("arguments") or {}).items():
                        texto = texto.replace("{" + str(clave) + "}", str(valor))
                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "description": elegido["description"],
                            "messages": [{"role": "user", "content": {"type": "text", "text": texto}}]
                        }
                    }
            elif method == "resources/list":
                resp = {"jsonrpc": "2.0", "id": req_id,
                        "result": {"resources": _recursos_disponibles()}}
            elif method == "resources/read":
                uri = params.get("uri", "")
                contenido = _leer_recurso(uri)
                if contenido is None:
                    resp = {"jsonrpc": "2.0", "id": req_id,
                            "error": {"code": -32602, "message": f"Recurso desconocido: {uri}"}}
                else:
                    resp = {"jsonrpc": "2.0", "id": req_id, "result": {"contents": [contenido]}}
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": tools_to_expose
                    }
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                res = handle_tool_call(tool_name, tool_args)
                is_error = isinstance(res, dict) and "error" in res

                # Formateo denso para ahorro de tokens (25-40% menos tokens que indent=2)
                if os.environ.get("OPENLEGAL_PRETTY", "").lower() in ("1", "true", "yes"):
                    payload_text = json.dumps(res, ensure_ascii=False, indent=2)
                else:
                    payload_text = json.dumps(res, ensure_ascii=False, separators=(',', ':'))

                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": payload_text
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

            sys.stdout.write(json.dumps(resp, ensure_ascii=False, separators=(',', ':')) + "\n")
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
