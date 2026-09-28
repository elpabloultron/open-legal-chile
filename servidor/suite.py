"""Herramientas de la suite (doctor, skills, telemetría y actualización)."""
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover — los bloques usan los objetos vivos de mcp_server
    from mcp_server import (
        _listar_skills,
        _raiz,
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
        "name": "suite_doctor",
        "description": "Diagnóstico REAL de la instalación (versión, OCR y sus motores, corpus doctrinal, grafo, "
                       "índice FTS, formateador de citas y herramientas MCP). Usalo para comprobar que todo está "
                       "disponible antes de prometer algo.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "suite_instalar",
        "description": "Deja el harness configurado y verificado en un paso: detecta los harnesses de la carpeta "
                       "(Claude Code, Cursor, VS Code, dsh, Codex, Antigravity), escribe su configuración MCP si "
                       "escribir=True y devuelve el estado del doctor. Equivale a `openlegal instalar` en la terminal.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "carpeta": {"type": "string", "description": "Carpeta a revisar (por defecto, la actual)"},
                "escribir": {"type": "boolean", "description": "true para dejar la configuración escrita (con respaldo)"}
            }
        }
    },
    {
        "name": "skills_listar",
        "description": "Lista las 18 skills jurídicas y los 19 agentes autónomos reales del producto, con su título.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "skill_ver",
        "description": "Devuelve el contenido completo de una skill (por su nombre, ej. 'chilean-employment-legal'): "
                       "así el harness aplica el criterio del producto sin abrir archivos a mano.",
        "inputSchema": {
            "type": "object",
            "properties": {"nombre": {"type": "string", "description": "Nombre de la skill (carpeta en .agents/skills)"}},
            "required": ["nombre"]
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
]


def despachar(name: str, args: dict) -> Any:
    _refrescar()
    if name == "suite_doctor":
        from diagnostico import diagnostico_completo
        return diagnostico_completo()
    elif name == "suite_instalar":
        import integraciones_harness as ih
        from diagnostico import diagnostico_completo

        carpeta = args.get("carpeta") or "."
        detectados = ih.detectar_instalados(carpeta)
        escritos = ih.escribir_todos(detectados, carpeta_base=carpeta) if (detectados and args.get("escribir")) else []
        resumen = diagnostico_completo()
        return {
            "harnesses": detectados,
            "escritos": [{"cliente": r.get("cliente"), "archivo": r.get("archivo"), "estado": r.get("estado")} for r in escritos],
            "doctor": {"estado": resumen["estado"]},
            "herramientas": len(TOOLS),
            "verificacion": "openlegal doctor",
            "nota": "con escribir=True deja la configuración escrita; el harness tiene que reiniciarse para verla",
        }
    elif name == "skills_listar":
        return _listar_skills()
    elif name == "skill_ver":
        nombre = (args.get("nombre") or "").strip()
        if not nombre or "/" in nombre or "\\" in nombre or ".." in nombre:
            return {"error": "El parámetro 'nombre' es obligatorio (nombre simple, sin barras)."}
        archivo = _raiz() / ".agents" / "skills" / nombre / "SKILL.md"
        if not archivo.exists():
            return {"error": f"No existe la skill «{nombre}».", "disponibles": [s["nombre"] for s in _listar_skills()["skills"]]}
        return {"nombre": nombre, "contenido": archivo.read_text(encoding="utf-8", errors="ignore")}
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
    return None


_PROPIOS = frozenset(globals())
