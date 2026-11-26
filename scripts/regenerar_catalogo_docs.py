"""Regenera docs/tools.json y docs/assets/data/catalog-data.js desde mcp_server.TOOLS y agents/*.json."""

import glob
import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import mcp_server  # noqa: E402


def _clasificar_tool(nombre: str) -> str:
    n = nombre.lower()
    if n.startswith((
        "consulta_maestra", "cita_texto", "busqueda_universal", "caso_",
        "suite_", "skills_", "skill_", "entrevista_", "descubrir_", "invocar_",
    )):
        return "Orquestación y Protocolo"
    if n.startswith(("bcn_", "rut_")):
        return "Normativa BCN"
    if n.startswith((
        "pjud_", "recurso_proteccion", "cpc_", "vigilante_", "export_brief",
        "compile_legal", "critique_", "verificar_citas", "generar_documento", "ocr_",
        "calcular_plazo", "calcular_cuantias", "docx_", "diario_oficial_",
    )):
        return "Litigación y Forense"
    if n.startswith(("ambiental_", "sma_", "cne_", "panel_expertos")):
        return "Ambiental y Energía"
    if n.startswith(("dt_", "suseso_", "calcular_finiquito")):
        return "Laboral"
    if n.startswith(("cgr_", "infoprobidad_", "entes_", "compras_publicas_", "cplt_")):
        return "Administrativo y Probidad"
    if n.startswith(("sii_", "tta_", "cmf_", "tdlc_", "sernac_", "inapi_", "privacidad_", "indicadores_economicos_")):
        return "Corporativo, Tributario y Datos"
    if n.startswith(("cbr_",)):
        return "Inmobiliario y CBR"
    if n.startswith((
        "graphify_", "grafo_", "doctrina_", "huggingface_", "academia_judicial",
        "biblioteca_", "jurimetria_", "notebooklm_", "generar_grafo",
    )):
        return "Grafo, Doctrina y Jurimetría"
    if n.startswith(("grado_", "clinica_")):
        return "Academia y Clínicas"
    if n.startswith(("agent_",)):
        return "Agentes Autónomos"
    return "Suite General"


destino = RAIZ / "docs" / "tools.json"
destino.write_text(json.dumps(mcp_server.TOOLS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

tools_web = [
    {
        "name": t["name"],
        "category": _clasificar_tool(t["name"]),
        "description": (t.get("description") or "").strip().splitlines()[0][:240],
    }
    for t in mcp_server.TOOLS
]
agents_web = []
for p in sorted(glob.glob(str(RAIZ / "agents" / "*.json"))):
    d = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    agents_web.append({
        "name": d.get("name", pathlib.Path(p).stem),
        "displayName": d.get("displayName", d.get("name", "")),
        "description": d.get("description", ""),
        "toolsCount": len(d.get("tools") or []),
        "toolsSample": (d.get("tools") or [])[:4],
    })

catalog_js = (
    "/* Open Legal Chile — Catálogo oficial (herramientas MCP y agentes autónomos) */\n"
    "window.OLC_TOOLS_DATA = " + json.dumps(tools_web, ensure_ascii=False) + ";\n"
    "window.OLC_AGENTS_DATA = " + json.dumps(agents_web, ensure_ascii=False) + ";\n"
)
destino_js = RAIZ / "docs" / "assets" / "data" / "catalog-data.js"
destino_js.parent.mkdir(parents=True, exist_ok=True)
destino_js.write_text(catalog_js, encoding="utf-8")

print(
    f"docs/tools.json: {len(mcp_server.TOOLS)} herramientas · {destino.stat().st_size / 1024:.0f} KB | "
    f"catalog-data.js: {len(agents_web)} agentes · {destino_js.stat().st_size / 1024:.0f} KB"
)
