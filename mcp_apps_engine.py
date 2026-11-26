"""Open Legal Chile — Registro liviano de MCP Apps (SEP-1865 / ui://).

Diseñado sin dependencias pesadas al importar (stdlib pura) para mantener el cold start
STDIO <= 25 ms. Provee metadatos `_meta.ui`, entrypoints de panel lateral (`aux_pane`) y
barra global (`global`), más la lectura de HTML autocontenidos `ui://open-legal-chile/*.html`.
"""

from __future__ import annotations

import os
import pathlib
from typing import Any, Dict, List, Optional

MIME_MCP_APP = "text/html;profile=mcp-app"
MAX_BYTES_HTML = 10 * 1024 * 1024

URI_GRAPHIFY = "ui://open-legal-chile/graphify.html"
URI_CALCULADORAS = "ui://open-legal-chile/calculadoras.html"
URI_EXPEDIENTE = "ui://open-legal-chile/expediente.html"

_ARCHIVOS_POR_URI: Dict[str, str] = {
    URI_GRAPHIFY: "graphify.html",
    URI_CALCULADORAS: "calculadoras.html",
    URI_EXPEDIENTE: "expediente.html",
}

UI_RESOURCES: List[Dict[str, Any]] = [
    {
        "uri": URI_GRAPHIFY,
        "name": "LegalGraphify Interactivo",
        "title": "Explorador LegalGraphify",
        "description": "Explorador visual interactivo del grafo de doctrina y normas BCN de Open Legal Chile.",
        "mimeType": MIME_MCP_APP,
        "_meta": {"ui": {"prefersBorder": False}},
    },
    {
        "uri": URI_CALCULADORAS,
        "name": "Calculadoras Forenses Chile",
        "title": "Calculadoras Forenses",
        "description": "Calculadoras deterministas de plazos procesales, finiquito CT, cuantías y UF/UTM SII.",
        "mimeType": MIME_MCP_APP,
        "_meta": {"ui": {"prefersBorder": False}},
    },
    {
        "uri": URI_EXPEDIENTE,
        "name": "Tablero de Expediente y Proveídos",
        "title": "Tablero Forense de Causa",
        "description": "Mesa de entrada interactiva y análisis de proveídos judiciales OJV con Compuerta Jurídica.",
        "mimeType": MIME_MCP_APP,
        "_meta": {"ui": {"prefersBorder": False}},
    },
]

TOOL_UI_META: Dict[str, Dict[str, Any]] = {
    "app_abrir_grafo": {
        "ui": {"resourceUri": URI_GRAPHIFY},
        "com.google.antigravity/ui": {
            "entrypoints": [
                {"type": "aux_pane", "title": "Grafo LegalGraphify"},
                {"type": "global", "title": "LegalGraphify"},
            ]
        },
    },
    "app_abrir_calculadoras": {
        "ui": {"resourceUri": URI_CALCULADORAS},
        "com.google.antigravity/ui": {
            "entrypoints": [
                {"type": "aux_pane", "title": "Calculadoras Legales"},
                {"type": "global", "title": "Calculadoras Chile"},
            ]
        },
    },
    "app_abrir_expediente": {
        "ui": {"resourceUri": URI_EXPEDIENTE},
        "com.google.antigravity/ui": {
            "entrypoints": [
                {"type": "aux_pane", "title": "Tablero de Causa"},
                {"type": "global", "title": "Mesa Jurídica"},
            ]
        },
    },
    "graphify_consulta_subgrafo": {"ui": {"resourceUri": URI_GRAPHIFY}},
    "calcular_plazo_procesal": {"ui": {"resourceUri": URI_CALCULADORAS}},
    "calcular_finiquito_laboral": {"ui": {"resourceUri": URI_CALCULADORAS}},
    "calcular_cuantias_legales": {"ui": {"resourceUri": URI_CALCULADORAS}},
    "caso_analizar": {"ui": {"resourceUri": URI_EXPEDIENTE}},
    "vigilante_analizar_resolucion": {"ui": {"resourceUri": URI_EXPEDIENTE}},
}


def _directorio_apps() -> pathlib.Path:
    """Resuelve el directorio donde viven los HTML compilados de `mcp_apps/`."""
    override = os.environ.get("OPENLEGAL_APPS_DIR", "").strip()
    if override:
        return pathlib.Path(override)
    from recursos import ruta_recurso

    return ruta_recurso("mcp_apps")


def listar_recursos_ui() -> List[Dict[str, Any]]:
    """Retorna la lista de recursos `ui://` declarados por Open Legal Chile."""
    return [dict(item) for item in UI_RESOURCES]


def leer_recurso_ui(uri: str) -> Optional[Dict[str, Any]]:
    """Lee un recurso HTML `ui://` en formato `text/html;profile=mcp-app` (<= 10 MiB)."""
    archivo_rel = _ARCHIVOS_POR_URI.get(uri)
    if not archivo_rel:
        return None
    ruta = _directorio_apps() / archivo_rel
    if not ruta.is_file():
        return None
    crudo = ruta.read_bytes()
    if not crudo or len(crudo) > MAX_BYTES_HTML:
        return None
    meta = next((dict(r.get("_meta") or {}) for r in UI_RESOURCES if r["uri"] == uri), {})
    return {
        "uri": uri,
        "mimeType": MIME_MCP_APP,
        "text": crudo.decode("utf-8"),
        "_meta": meta,
    }


def enriquecer_herramientas_ui(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Adjunta `_meta` UI a las herramientas que tienen MCP App asociada sin mutar originales."""
    salida: List[Dict[str, Any]] = []
    for tool in tools:
        nombre = str(tool.get("name") or "")
        ui_meta = TOOL_UI_META.get(nombre)
        if not ui_meta:
            salida.append(tool)
            continue
        copia = dict(tool)
        meta_actual = dict(copia.get("_meta") or {})
        meta_actual.update(ui_meta)
        copia["_meta"] = meta_actual
        salida.append(copia)
    return salida
