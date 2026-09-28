"""Herramientas del módulo especial de derecho ambiental."""
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover — los bloques usan los objetos vivos de mcp_server
    from mcp_server import (
        ambientales_client,
    )


def _refrescar() -> None:
    """Trae los nombres compartidos de mcp_server.py (helpers, clientes, motores).

    Corre en cada despacho: los bloques movidos usan los mismos objetos vivos del servidor,
    incluidas las sustituciones que hagan las pruebas con monkeypatch."""
    import mcp_server as _m
    _g = globals()
    _g.update({k: v for k, v in vars(_m).items() if k not in _PROPIOS})


TOOLS = [
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
        "name": "ambiental_consulta_maestra",
        "description": "Módulo especial de derecho ambiental: PRIMERA consulta cuando la consulta o el caso es de materia ambiental (SMA, SEIA/RCA, daño ambiental, tribunales ambientales, humedales, LO-SMA). Busca en un solo paso entre las 886 sentencias de los Tribunales Ambientales, los anuarios y boletines 2TA/3TA, la biblioteca ambiental (libros del Concurso Nacional de Comentarios de Sentencias, informes en derecho, foros, manuales y material docente) y la doctrina ambiental; devuelve el plan, los resultados con texto literal y las citas [Hugging Face - <archivo>]. Con incluir_subgrafo=true añade el subgrafo de LegalGraphify y su ahorro de tokens.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "consulta": {"type": "string", "description": "Consulta o caso de materia ambiental (ej. 'daño ambiental en humedales urbanos', 'sanción SMA por incumplimiento de RCA')"},
                "limite": {"type": "integer", "description": "Máximo de resultados (por defecto 8)", "default": 8},
                "incluir_subgrafo": {"type": "boolean", "description": "Añade el subgrafo de LegalGraphify con su ahorro de tokens (por defecto False: el primer subgrafo de cada proceso carga su índice)", "default": False}
            },
            "required": ["consulta"]
        }
    },
]


def despachar(name: str, args: dict) -> Any:
    _refrescar()
    if name == "ambiental_buscar_jurisprudencia":
        q = args.get("query")
        if not q:
            return {"error": "El parámetro 'query' es obligatorio."}
        return ambientales_client.search_jurisprudencia(q, args.get("tribunal"))
    elif name == "ambiental_consulta_maestra":
        consulta = (args.get("consulta") or "").strip()
        if not consulta:
            return {"error": "El parámetro 'consulta' es obligatorio."}
        from modulo_ambiental import consulta_ambiental
        return consulta_ambiental(consulta, limite=int(args.get("limite") or 8),
                                  incluir_subgrafo=bool(args.get("incluir_subgrafo", False)))
    return None


_PROPIOS = frozenset(globals())
