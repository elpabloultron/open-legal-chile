"""
Open Legal Chile — Servidor Maestro MCP (Model Context Protocol)
Expone los 8 conectores oficiales del Estado de Chile y herramientas forenses
para cualquier agente de IA (Antigravity/Gemini, Claude Code, Cursor, Codex)
a través del protocolo estándar MCP sobre stdio (JSON-RPC 2.0).
"""

import sys
import json
import os

# Configurar encoding seguro UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdin.reconfigure(encoding='utf-8')
except Exception:
    pass

from bcn_connector import BCNClient, CODIGOS_REPUBLICA
from cgr_connector import CGRClient
from dt_connector import DTClient
from cne_connector import CNEClient
from panel_expertos_connector import PanelExpertosClient
from cmf_connector import CMFClient
from sii_connector import SIIClient
from ambiental_connector import AmbientalClient
from tdlc_connector import TDLCClient
from pjud_connector import PJUDClient
from exporters import LegalDocumentExporter

# Inicializar clientes
bcn = BCNClient()
cgr = CGRClient()
dt = DTClient()
cne = CNEClient()
panel = PanelExpertosClient()
cmf = CMFClient()
sii = SIIClient()
sma = AmbientalClient()
tdlc = TDLCClient()
pjud = PJUDClient()
exporter = LegalDocumentExporter()

TOOLS = [
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
        "description": "Busca dictámenes vinculantes e instructivos en la jurisprudencia administrativa de la Contraloría General de la República (CGR).",
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
        "description": "Genera y exporta un escrito judicial estructurado formalmente para la Oficina Judicial Virtual (OJV - Ley N° 20.886) en formatos .html y .md.",
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
    }
]

def handle_tool_call(name: str, args: dict) -> dict:
    try:
        if name == "bcn_get_codigo":
            return bcn.get_codigo(args.get("codigo"), args.get("articulo"))
        elif name == "bcn_get_ley":
            num = int(args.get("numero", 0))
            art = args.get("articulo")
            return bcn.get_articulo_ley(num, art) if art else bcn.get_ley(num)
        elif name == "cgr_search_jurisprudencia":
            return cgr.search_jurisprudencia(args.get("query", ""))
        elif name == "cgr_search_auditorias":
            return cgr.search_auditorias(args.get("query", ""))
        elif name == "dt_search_doctrina":
            return dt.search_dictamenes(args.get("query", ""), limit=10)
        elif name == "cne_get_centrales_y_proyectos":
            capacidad = cne.get_capacidad_instalada()
            return {"total_registros": len(capacidad), "muestra": capacidad[:15]}
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
            return exporter.export_brief(
                titulo_principal=args.get("titulo"),
                tribunal=args.get("tribunal"),
                presuma_data={"materia": args.get("titulo"), "demandante": "COMPARECIENTE"},
                comparecencia=args.get("comparecencia", ""),
                hechos=args.get("hechos", ""),
                derecho=args.get("derecho", ""),
                peticiones=args.get("peticiones", ""),
                otrosies=args.get("otrosies", [])
            )
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
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

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
                            "version": "1.0.0"
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
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(res, ensure_ascii=False, indent=2)
                            }
                        ]
                    }
                }
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {}
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
