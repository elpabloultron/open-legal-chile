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
import contextlib
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
from recursos import ruta_recurso

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


# ── Progreso MCP: el cliente pone `params._meta.progressToken` en cada tools/call ─────────────
# Sin token no se escribe nada: los clientes que no saben de avances ven el protocolo de siempre.
_STDOUT_LOCK = threading.Lock()
_OUTPUT_STREAM: Optional[Any] = None
_TOKEN_PROGRESO: Any = None


def _fijar_token_progreso(token: Any) -> None:
    """Fija el token de avance de la llamada en curso (lo llama main por cada tools/call)."""
    global _TOKEN_PROGRESO
    _TOKEN_PROGRESO = token


def enviar_progreso(mensaje: str, avance: int = 0, total: Optional[int] = None) -> None:
    """Emite una notificación `notifications/progress` de la llamada en curso (no-op sin token).

    Se escribe bajo el mismo candado que las respuestas finales para que una notificación nunca
    parta a medias una respuesta del protocolo; sin token no se escribe nada.
    """
    token = _TOKEN_PROGRESO
    if token is None:
        return
    params: Dict[str, Any] = {"progressToken": token, "progress": avance}
    if total is not None:
        params["total"] = total
    if mensaje:
        params["message"] = mensaje
    linea = json.dumps({"jsonrpc": "2.0", "method": "notifications/progress", "params": params},
                       ensure_ascii=False, separators=(",", ":"))
    out = _OUTPUT_STREAM if _OUTPUT_STREAM is not None else sys.stdout
    with _STDOUT_LOCK:
        out.write(linea + "\n")
        out.flush()


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

# Metadatos de anotaciones oficiales MCP (readOnlyHint / openWorldHint) para Claude Opus y harnesses
_HERRAMIENTAS_ESCRITURA = {
    "recurso_proteccion_generar", "generar_documento", "compile_legal_dossier",
    "export_brief_ojv", "doctrina_ingestar_documento", "suite_auto_update", "suite_instalar"
}
# Las que cambian el entorno de la persona (git pull / pip install / archivos de configuración de
# sus harness): el cliente debe poder pedir confirmación antes de correrlas.
_HERRAMIENTAS_DESTRUCTIVAS = {"suite_auto_update", "suite_instalar"}
for _t in TOOLS:
    if "annotations" not in _t:
        _es_escritura = _t["name"] in _HERRAMIENTAS_ESCRITURA
        _t["annotations"] = {
            "readOnlyHint": not _es_escritura,
            "destructiveHint": _t["name"] in _HERRAMIENTAS_DESTRUCTIVAS,
            "openWorldHint": not _es_escritura,
        }

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


def _detectar_dominios_estatales(query: str) -> List[str]:
    """Determina los organismos públicos relevantes para la consulta según términos clave."""
    q = (query or "").lower()
    organismos: List[str] = []

    # Laboral
    if any(k in q for k in (
        "trabajador", "empleador", "despido", "finiquito", "laboral", "remuneracion",
        "ley karin", "40 horas", "sindicato", "huelga", "subcontratacion", "tutela",
        "inspeccion del trabajo", "direccion del trabajo", "dt", "art 161", "art 160",
        "necesidades de la empresa", "licencia medica", "fuero"
    )):
        organismos.append("dt")
        if "pjud" not in organismos:
            organismos.append("pjud")

    # Administrativo / Probidad
    if any(k in q for k in (
        "contraloria", "cgr", "dictamen cgr", "sumario", "estatuto administrativo",
        "probidad", "dip", "infoprobidad", "compras publicas", "licitacion", "mercado publico",
        "ley 19886", "confianza legitima", "contrata", "planta", "municipalidad", "funcionario publico"
    )):
        if "cgr" not in organismos:
            organismos.append("cgr")

    # Tributario
    if any(k in q for k in (
        "sii", "impuesto", "tributario", "iva", "renta", "lir", "factura",
        "elusion", "evasion", "tta", "circular sii", "oficio sii", "codigo tributario"
    )):
        if "sii" not in organismos:
            organismos.append("sii")

    # Ambiental
    if any(k in q for k in (
        "ambiental", "medio ambiente", "sma", "snifa", "seia", "rca", "eia", "dia",
        "humedal", "daño ambiental", "tribunal ambiental", "1ta", "2ta", "3ta"
    )):
        if "sma" not in organismos:
            organismos.append("sma")

    # Libre Competencia
    if any(k in q for k in (
        "tdlc", "libre competencia", "fne", "colusion", "monopolio", "concentracion",
        "abuso de posicion", "dl 211"
    )):
        if "tdlc" not in organismos:
            organismos.append("tdlc")

    # Financiero / Mercado de Valores / Bancario
    if any(k in q for k in (
        "cmf", "mercado de valores", "banco", "financiero", "insider trading",
        "ncg", "norma de caracter general", "accionista", "sociedad anonima", "ley 18045"
    )):
        if "cmf" not in organismos:
            organismos.append("cmf")

    # Energía
    if any(k in q for k in (
        "cne", "energia", "electrico", "tarifa electrica", "panel de expertos",
        "ppa", "transmision electrica", "generacion electrica"
    )):
        if "cne" not in organismos:
            organismos.append("cne")
        if "panel" not in organismos:
            organismos.append("panel")

    # Fallback judicial rector en Derecho Civil/General
    if not organismos or any(k in q for k in (
        "corte suprema", "corte de apelaciones", "recurso", "demanda", "prescripcion",
        "contrato", "responsabilidad", "indemnizacion", "daño moral", "casacion", "pjud", "juicio"
    )):
        if "pjud" not in organismos:
            organismos.append("pjud")

    return organismos[:3]


def _organismos_para_consulta(query: str, lim: int = 3) -> Dict[str, Any]:
    """Consulta a los organismos oficiales del Estado según la materia detectada."""
    try:
        reg = _registro_estatal()
        organismos = _detectar_dominios_estatales(query)
        resultados_org: Dict[str, Any] = {}
        citas_org: List[Dict[str, Any]] = []
        for org in organismos:
            res = None
            try:
                if org == "dt":
                    res = reg.dt.search_dictamenes(query, limit=lim)
                elif org == "cgr":
                    res = reg.cgr.search_jurisprudencia(query)
                elif org == "pjud":
                    res = reg.pjud.search_jurisprudencia(query, limit=lim)
                elif org == "sii":
                    res = reg.sii.search_circulares(query)
                elif org == "sma":
                    res = reg.sma.search_sancionatorios(nombre=query)
                elif org == "tdlc":
                    res = reg.tdlc.search_jurisprudencia(query)
                elif org == "cmf":
                    res = reg.cmf.search_normativa(query)
                elif org == "cne":
                    res = reg.cne.search(query)
                elif org == "panel":
                    res = reg.panel.search_dictamenes(query)
            except Exception:
                res = None

            if res is not None:
                resultados_org[org] = res
                items = _items_del_organismo(res)
                for it in items[:lim]:
                    ident = (it.get("rol") or it.get("numero") or it.get("nombre")
                             or it.get("materia") or it.get("title") or it.get("titulo")
                             or it.get("docId"))
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
                                or it.get("snippet") or "")[:800]
                    if not texto:
                        continue
                    url = str(it.get("url") or it.get("link") or it.get("pdfUrl") or it.get("enlace") or "")
                    citas_org.append(formatear_cita(
                        org.upper(), str(ident),
                        url=url,
                        texto=texto
                    ))
        return {"organismos": organismos, "resultados": resultados_org, "citas": citas_org}
    except Exception as e:
        return {"organismos": [], "resultados": {}, "citas": [], "error": str(e)[:160]}


def _listar_skills() -> Dict[str, Any]:
    """Las 18 skills y los 19 agentes reales del producto (el texto fijo de la CLI decía 7)."""
    skills = []
    for archivo in sorted(ruta_recurso(".agents/skills").glob("*/SKILL.md")):
        texto = archivo.read_text(encoding="utf-8", errors="ignore")
        titulo = next((linea.lstrip("# ").strip() for linea in texto.splitlines() if linea.startswith("# ")),
                      archivo.parent.name)
        skills.append({"nombre": archivo.parent.name, "titulo": titulo})
    agentes = []
    for archivo in sorted(ruta_recurso("agents").glob("*.json")):
        try:
            agentes.append(json.loads(archivo.read_text(encoding="utf-8")).get("name", archivo.stem))
        except Exception:  # noqa: BLE001 - un JSON roto no puede tumbar el listado
            agentes.append(archivo.stem)
    return {"skills": skills, "agentes": agentes}


def _texto_protocolo() -> str:
    """El protocolo de citación tal como está escrito en AGENTS.md (§2 quater)."""
    agentes = ruta_recurso("AGENTS.md")
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
        "description": "Protocolo de respuesta obligatorio (§2 quater): Hugging Face y conectores estatales siempre, "
                       "cada cita con su texto literal y el formato de salida por tipo de documento.",
        "arguments": [],
        "_texto": (
            "Al responder una consulta jurídica chilena seguí este orden, sin excepciones:\n"
            "1. Hugging Face y Conectores Estatales siempre: el primer paso es `consulta_maestra` (o `huggingface_search_dataset`). "
            "El corpus publicado en Hugging Face y las fuentes del Estado son la base citable; no respondas de memoria. "
            "Si la materia es ambiental (SMA, SEIA/RCA, daño ambiental, humedales, Tribunales Ambientales), el primer paso es el módulo "
            "`ambiental_consulta_maestra`.\n"
            "2. Conectores oficiales del Estado: `consulta_maestra` consulta automáticamente a los organismos estatales según la materia "
            "(DT y PJUD en laboral; CGR en administrativo; SII en tributario; SMA/TA en ambiental; PJUD en civil general, etc.). "
            "Si el harness o modelo decide invocar herramientas específicas por materia, debe consultar SIEMPRE tanto al conector estatal "
            "correspondiente como a la data de Hugging Face.\n"
            "3. Antes de citar, traé el texto literal con `cita_texto` (o usá el bloque `citas` del resultado). Si la fuente no se pudo leer, "
            "decí «sin fuente verificable».\n"
            "4. Formato: en conversación, la respuesta primero y el bloque «Fuentes:» al final. En documentos, entregá Word (.docx editable) "
            "con citas a pie de página: fuente · identificador · enlace.\n"
            "5. Los corchetes van en el formato oficial: [BCN - Código Civil, Art. 1438], [Dictamen DT - ORD. N° …], "
            "[CS - Rol N° …], [CGR - …], [Academia Judicial - …], [SMA - Expediente …]."
        ),
    },
    {
        "name": "consulta_juridica_completa",
        "description": "Receta de punta a punta para una consulta o un caso: qué herramientas usar, en qué orden y "
                       "cómo cerrar la respuesta.",
        "arguments": [{"name": "consulta", "description": "La pregunta jurídica del usuario", "required": False}],
        "_texto": (
            "Consulta: {consulta}\n\n"
            "1. `consulta_maestra` con la consulta (trae corpus de Hugging Face + organismos estatales + doctrina + grafo + normas, "
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
        ruta = ruta_recurso("docs/integracion-harness.md")
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

# Todo perfil lleva lo que exige el protocolo de citación: `consulta_maestra` como primer paso,
# `cita_texto` antes de citar y `suite_doctor` para diagnosticar. Antes ningún perfil traía las tres
# y el modo perfil contradecía el prompt `protocolo_citas`.
_PROTOCOLO_BASE: List[str] = ["consulta_maestra", "cita_texto", "suite_doctor"]

TOOL_PROFILES: Dict[str, List[str]] = {
    "laboral": _PROTOCOLO_BASE + [
        "caso_analizar", "caso_ejecutar", "bcn_get_codigo", "bcn_get_ley",
        "dt_search_doctrina", "pjud_search_jurisprudencia", "pjud_analizar_sentencia",
        "doctrina_search", "doctrina_get_institucion", "export_brief_ojv", "compile_legal_dossier"
    ],
    "inmobiliario": _PROTOCOLO_BASE + [
        "caso_analizar", "bcn_get_codigo", "bcn_get_ley", "cbr_estudio_titulos",
        "cbr_checklist_documentos", "cpc_validar_mandato", "doctrina_search",
        "doctrina_get_institucion", "export_brief_ojv", "compile_legal_dossier"
    ],
    "litigios": _PROTOCOLO_BASE + [
        "caso_analizar", "caso_ejecutar", "bcn_get_codigo", "bcn_get_ley",
        "pjud_search_jurisprudencia", "pjud_analizar_sentencia", "pjud_interpretar_proveido",
        "recurso_proteccion_generar", "cpc_validar_mandato", "doctrina_search",
        "doctrina_get_institucion", "export_brief_ojv", "compile_legal_dossier", "ocr_extract_pdf"
    ],
    "regulatorio": _PROTOCOLO_BASE + [
        "caso_analizar", "bcn_get_ley", "cgr_search_jurisprudencia", "cgr_search_auditorias",
        "infoprobidad_get_dip", "cmf_search_normativa", "cmf_buscar_sanciones",
        "sii_search_circulares", "sii_buscar_resoluciones_y_oficios", "sma_search_sancionatorios",
        "ambiental_consulta_maestra", "ambiental_buscar_jurisprudencia", "cne_get_centrales_y_proyectos", "panel_expertos_search",
        "tdlc_search_jurisprudencia", "tdlc_buscar_icg_y_dictamenes", "entes_consultar_organo",
        "export_brief_ojv"
    ],
    "corporativo": _PROTOCOLO_BASE + [
        "caso_analizar", "bcn_get_codigo", "bcn_get_ley", "cmf_search_normativa",
        "cmf_buscar_sanciones", "sii_search_circulares", "sii_buscar_resoluciones_y_oficios",
        "tdlc_search_jurisprudencia", "inapi_evaluar_marca", "inapi_cease_and_desist",
        "privacidad_tramitar_arco", "rut_validar_chile", "export_brief_ojv"
    ],
    "dogmatico": _PROTOCOLO_BASE + [
        "caso_analizar", "bcn_get_codigo", "bcn_get_ley", "doctrina_search",
        "doctrina_get_institucion", "doctrina_list_obras", "graphify_consulta_subgrafo",
        "graphify_trazar_camino", "graphify_explicar_institucion", "graphify_analizar_impacto",
        "graphify_god_nodes", "graphify_resumen_comunidades", "academia_judicial_buscar_guias",
        "grafo_ver_corpus", "huggingface_search_dataset"
    ],
    "clinica": _PROTOCOLO_BASE + [
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


# Versiones del protocolo MCP que este servidor habla, de la más nueva a la más antigua. Si el
# cliente pide una que no está, se responde con la más nueva (así lo pide la especificación) y el
# cliente decide si sigue; antes se respondía con la más antigua.
VERSIONES_PROTOCOLO = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")

# Lo que todo harness recibe en `initialize` (campo estándar `instructions`): el protocolo de
# citación llega aunque el cliente nunca pida prompts ni recursos.
INSTRUCCIONES = (
    "Open Legal Chile: derecho chileno (Civil Law) con fuentes oficiales del Estado. "
    "Primer paso de toda consulta jurídica: `consulta_maestra` (en materia ambiental, "
    "`ambiental_consulta_maestra`); trae el corpus de Hugging Face, los organismos estatales, la doctrina, "
    "el grafo y las normas con su texto literal. Antes de citar, usá `cita_texto` o el bloque `citas` del "
    "resultado; lo que no se pudo leer se declara «sin fuente verificable». Corchetes oficiales: "
    "[BCN - Código Civil, Art. 1438], [CS - Rol N° …], [Dictamen DT N° …], [CGR - …]. Nunca uses "
    "terminología de Common Law. Respuesta primero y bloque «Fuentes:» al final; los documentos se "
    "entregan en Word (.docx) con citas a pie de página. Protocolo completo: prompt `protocolo_citas` "
    "o recurso openlegal://reglas/citacion. Estado de la instalación: `suite_doctor`."
)


# Tope de salida por llamada, en caracteres del JSON. Claude Code corta las respuestas MCP por encima
# de ~25 000 tokens (MAX_MCP_OUTPUT_TOKENS) y en cualquier harness una respuesta gigante llena el
# contexto: medido el 2026-10-07, ocr_extract_pdf devolvía 3,2 M de caracteres por un manual y
# cgr_search_auditorias 220 mil. Lo que pasa del tope se guarda completo en disco y la respuesta lleva
# una versión recortada (misma forma, textos y listas acortados) con la ruta del archivo.
# OPENLEGAL_MAX_SALIDA=0 lo desactiva.
_RECORTES = ((4000, 50), (2000, 25), (1000, 12), (500, 6), (250, 3), (120, 2))


def _max_salida() -> int:
    try:
        return int(os.environ.get("OPENLEGAL_MAX_SALIDA", "60000"))
    except ValueError:
        return 60000


def _recortar(valor: Any, max_texto: int, max_items: int) -> Any:
    if isinstance(valor, str):
        if len(valor) <= max_texto:
            return valor
        return valor[:max_texto] + f" … [recortado: {len(valor)} caracteres en total]"
    if isinstance(valor, list):
        recortada = [_recortar(x, max_texto, max_items) for x in valor[:max_items]]
        if len(valor) > max_items:
            recortada.append(f"… [{len(valor) - max_items} elementos más en la salida completa]")
        return recortada
    if isinstance(valor, dict):
        return {k: _recortar(v, max_texto, max_items) for k, v in valor.items()}
    return valor


def _guardar_salida_completa(nombre: str, texto: str) -> Optional[str]:
    try:
        carpeta = pathlib.Path(os.environ.get("OPENLEGAL_SALIDAS_DIR") or pathlib.Path.home() / ".openlegal" / "salidas")
        carpeta.mkdir(parents=True, exist_ok=True)
        seguro = "".join(c if c.isalnum() or c in "-_" else "_" for c in nombre)[:60] or "herramienta"
        ruta = carpeta / f"{seguro}-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.json"
        ruta.write_text(texto, encoding="utf-8")
        return str(ruta)
    except OSError:
        return None


def ajustar_salida(nombre: str, resultado: Any) -> Any:
    """Devuelve el resultado tal cual si cabe en el tope; si no, una versión recortada con aviso."""
    tope = _max_salida()
    if tope <= 0:
        return resultado
    completo = json.dumps(resultado, ensure_ascii=False, separators=(",", ":"))
    if len(completo) <= tope:
        return resultado
    archivo = _guardar_salida_completa(nombre, completo)
    aviso = {
        "caracteres_originales": len(completo),
        "tope": tope,
        "archivo_completo": archivo,
        "nota": "La salida superaba el tope del canal MCP y se recortó (textos y listas acortados). "
                "La salida íntegra quedó en 'archivo_completo'; para menos volumen, acotá la consulta "
                "(artículo puntual, menos resultados o menos páginas).",
    }
    for max_texto, max_items in _RECORTES:
        recortado = _recortar(resultado, max_texto, max_items)
        envoltura = dict(recortado) if isinstance(recortado, dict) else {"resultado": recortado}
        envoltura["_salida_recortada"] = aviso
        if len(json.dumps(envoltura, ensure_ascii=False, separators=(",", ":"))) <= tope:
            return envoltura
    return {"_salida_recortada": aviso, "inicio": completo[: max(0, tope - 2000)]}


def _error(req_id: Any, codigo: int, mensaje: str) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": codigo, "message": mensaje}}


def _resultado(req_id: Any, resultado: Dict[str, Any]) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": resultado}


def procesar_mensaje(req: Any, tools_to_expose: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Atiende un mensaje JSON-RPC ya decodificado. Devuelve la respuesta, o None si no lleva.

    Las notificaciones (sin `id`, como notifications/initialized o notifications/cancelled) no
    reciben respuesta; un mensaje que no es un objeto recibe -32600 en vez de quedar sin respuesta.
    """
    if not isinstance(req, dict):
        return _error(None, -32600, "Petición inválida: se esperaba un objeto JSON-RPC")
    req_id = req.get("id")
    if req_id is None:
        return None
    method = req.get("method")
    params = req.get("params") or {}
    if not isinstance(method, str) or not isinstance(params, dict):
        return _error(req_id, -32600, "Petición inválida: falta 'method' o 'params' no es un objeto")

    try:
        if method == "initialize":
            solicitada = params.get("protocolVersion")
            return _resultado(req_id, {
                "protocolVersion": solicitada if solicitada in VERSIONES_PROTOCOLO else VERSIONES_PROTOCOLO[0],
                "capabilities": {
                    "tools": {},
                    # El harness no sólo ve las herramientas: también puede leer las reglas
                    # del producto (protocolo de citación) y el catálogo.
                    "prompts": {"listChanged": False},
                    "resources": {"listChanged": False, "subscribe": False}
                },
                "serverInfo": {
                    "name": "open-legal-chile-mcp",
                    "title": "Open Legal Chile",
                    "version": "1.13.0"
                },
                "instructions": INSTRUCCIONES,
            })
        if method == "ping":
            return _resultado(req_id, {})
        if method == "prompts/list":
            return _resultado(req_id, {
                "prompts": [{clave: valor for clave, valor in prompt.items() if not clave.startswith("_")}
                            for prompt in PROMPTS]
            })
        if method == "prompts/get":
            nombre = params.get("name")
            elegido = next((p for p in PROMPTS if p["name"] == nombre), None)
            if elegido is None:
                return _error(req_id, -32602, f"Prompt desconocido: {nombre}")
            texto = elegido["_texto"]
            for clave, valor in (params.get("arguments") or {}).items():
                texto = texto.replace("{" + str(clave) + "}", str(valor))
            return _resultado(req_id, {
                "description": elegido["description"],
                "messages": [{"role": "user", "content": {"type": "text", "text": texto}}]
            })
        if method == "resources/list":
            return _resultado(req_id, {"resources": _recursos_disponibles()})
        if method == "resources/templates/list":
            return _resultado(req_id, {"resourceTemplates": []})
        if method == "resources/read":
            uri = params.get("uri", "")
            contenido = _leer_recurso(uri)
            if contenido is None:
                return _error(req_id, -32602, f"Recurso desconocido: {uri}")
            return _resultado(req_id, {"contents": [contenido]})
        if method == "tools/list":
            return _resultado(req_id, {"tools": tools_to_expose})
        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments") or {}
            _fijar_token_progreso((params.get("_meta") or {}).get("progressToken"))
            try:
                # Blindaje contra stdout pollution: cualquier print espurio viaja a stderr
                with contextlib.redirect_stdout(sys.stderr):
                    res = handle_tool_call(tool_name, tool_args)
            finally:
                _fijar_token_progreso(None)
            is_error = isinstance(res, dict) and "error" in res
            res = ajustar_salida(str(tool_name), res)

            # Formateo denso para ahorro de tokens (25-40% menos tokens que indent=2)
            if os.environ.get("OPENLEGAL_PRETTY", "").lower() in ("1", "true", "yes"):
                payload_text = json.dumps(res, ensure_ascii=False, indent=2)
            else:
                payload_text = json.dumps(res, ensure_ascii=False, separators=(',', ':'))
            return _resultado(req_id, {"content": [{"type": "text", "text": payload_text}], "isError": is_error})
        return _error(req_id, -32601, f"Método no encontrado: {method}")
    except Exception as e:  # noqa: BLE001 — un error de una petición no puede tumbar el servidor
        return _error(req_id, -32603, str(e))


def _escribir(mensaje: Any) -> None:
    out = _OUTPUT_STREAM if _OUTPUT_STREAM is not None else sys.stdout
    with _STDOUT_LOCK:
        out.write(json.dumps(mensaje, ensure_ascii=False, separators=(',', ':')) + "\n")
        out.flush()


def atender_linea(line: str, tools_to_expose: List[Dict[str, Any]]) -> Any:
    """Decodifica una línea del canal stdio y devuelve lo que hay que contestar (o None).

    JSON inválido → -32700 con id null (antes el servidor moría si era la primera línea, y en las
    siguientes contestaba con el id de la petición anterior). Un lote JSON-RPC (array) se atiende
    elemento por elemento y se contesta con el array de respuestas.
    """
    try:
        req = json.loads(line)
    except ValueError as e:
        return _error(None, -32700, f"JSON inválido: {e}")
    if isinstance(req, list):
        if not req:
            return _error(None, -32600, "Petición inválida: lote vacío")
        respuestas = [r for r in (procesar_mensaje(item, tools_to_expose) for item in req) if r is not None]
        return respuestas or None
    return procesar_mensaje(req, tools_to_expose)


def _mensajes_de_librerias_a_stderr() -> None:
    """stdout es el canal del protocolo: nada que no sea JSON-RPC puede escribirse ahí.

    PyMuPDF guarda el sys.stdout real al importarse (forensic_ocr lo importa al arrancar) y escribe
    ahí sus avisos, por fuera del redirect_stdout de cada tools/call. Medido el 2026-10-07: el aviso
    de deprecación de `import fitz` llegaba al cliente como una línea no-JSON que el SDK oficial
    rechazaba. Sus mensajes van a stderr.
    """
    try:
        import pymupdf

        pymupdf.set_messages(stream=sys.stderr)
    except Exception:  # noqa: BLE001 — sin PyMuPDF (o una versión sin set_messages) no hay nada que desviar
        pass


def main():
    """Bucle principal JSON-RPC 2.0 para el servidor MCP."""
    global _OUTPUT_STREAM
    _OUTPUT_STREAM = sys.stdout
    _mensajes_de_librerias_a_stderr()
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
        respuesta = atender_linea(line, tools_to_expose)
        if respuesta is not None:
            _escribir(respuesta)

if __name__ == "__main__":
    main()
