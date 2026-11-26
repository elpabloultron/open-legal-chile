"""Herramientas de la suite (doctor, skills, telemetría y actualización)."""
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover — los bloques usan los objetos vivos de mcp_server
    from mcp_server import (
        _listar_skills,
        enviar_progreso,
    )

# Cuánto espera suite_instalar al mapa del corpus antes de responder (la descarga sigue en segundo
# plano si no alcanzó: el cliente del mapa la termina igual).
ESPERA_MAPA_INSTALAR = 120.0


def _refrescar() -> None:
    """Trae los nombres compartidos de mcp_server.py (helpers, clientes, motores)."""
    from servidor import refrescar_globals
    refrescar_globals(globals(), _PROPIOS, _DEFAULTS_LAZY)


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
                       "escribir=True, deja descargado el mapa del corpus de Hugging Face (verificado, con avances) "
                       "y devuelve el estado del doctor. Equivale a `openlegal instalar` en la terminal.",
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
        "description": "Lista las 26 skills jurídicas y los 24 agentes autónomos reales del producto, con su título.",
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
    {
        "name": "descubrir_herramientas",
        "description": "Búsqueda dinámica de herramientas MCP (perfil router / Tool Search): usa LegalOpenJev (<5 ms) y ranking léxico para devolver solo las herramientas relevantes y su inputSchema bajo demanda, reduciendo ~85 % el consumo de tokens de contexto.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "consulta": {"type": "string", "description": "Descripción de la tarea jurídica o palabra clave (ej. 'estudio de títulos CBR', 'sanción SMA ruido', 'comparar versiones ley')"},
                "limite": {"type": "integer", "description": "Máximo de herramientas sugeridas", "default": 6}
            },
            "required": ["consulta"]
        }
    },
    {
        "name": "invocar_herramienta",
        "description": "Invoca dinámicamente cualquier herramienta del catálogo completo de Open Legal Chile tras localizarla con `descubrir_herramientas` (útil en `OPENLEGAL_PROFILE=router`).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "nombre": {"type": "string", "description": "Nombre exacto de la herramienta MCP a ejecutar"},
                "argumentos": {"type": "object", "description": "Diccionario JSON con los parámetros de la herramienta", "default": {}}
            },
            "required": ["nombre"]
        }
    },
    {
        "name": "app_abrir_grafo",
        "description": "Abre el explorador visual interactivo LegalGraphify (MCP App ui://) con el resumen de comunidades o un subgrafo inicial por consulta.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Concepto jurídico o norma inicial (opcional; si se omite muestra el panorama por comunidades)"},
                "max_hops": {"type": "integer", "description": "Radio de saltos en el subgrafo", "default": 1},
                "top_n": {"type": "integer", "description": "Número de comunidades a mostrar cuando no hay consulta", "default": 8}
            }
        }
    },
    {
        "name": "app_abrir_calculadoras",
        "description": "Abre la estación interactiva de Calculadoras Forenses Deterministas (MCP App ui://): plazos procesales Chile, finiquito CT, cuantías y UF/UTM SII.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vista": {
                    "type": "string",
                    "enum": ["plazos", "finiquito", "cuantias", "indicadores"],
                    "description": "Pestaña inicial de calculadora (opcional)",
                    "default": "plazos"
                }
            }
        }
    },
    {
        "name": "app_abrir_expediente",
        "description": "Abre el Tablero Forense de Causa y Proveídos OJV (MCP App ui://) para analizar expedientes o resoluciones judiciales con Compuerta Jurídica.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entrada": {"type": "string", "description": "Relato del caso, ruta de expediente o consulta inicial (opcional)"},
                "tipo": {"type": "string", "enum": ["carpeta", "texto", "consulta"], "description": "Tipo de entrada (opcional)"},
                "consulta": {"type": "string", "description": "Objetivo jurídico específico (opcional)"}
            }
        }
    },
]


def _asegurar_mapa_con_avances(espera: float = ESPERA_MAPA_INSTALAR) -> dict:
    """Deja listo el mapa del corpus (descarga verificada + índice), informando avances al cliente
    MCP. Si no alcanza en `espera` segundos, responde igual: la descarga sigue en segundo plano."""
    import time
    try:
        from mapa_corpus.cliente import obtener_cliente
        cliente = obtener_cliente()
        if not cliente.habilitado:
            return cliente.estado_breve()
        cliente.asegurar()
        inicio = time.monotonic()
        while cliente.descargando and time.monotonic() - inicio < espera:
            enviar_progreso("Mapa del corpus de Hugging Face: descarga e índice", int(time.monotonic() - inicio),
                            int(espera))
            time.sleep(2.0)
        breve = dict(cliente.estado_breve())
        if cliente.descargando:
            breve["nota"] = "la descarga del mapa sigue en segundo plano: las herramientas lo usarán al terminar"
        if cliente.error:
            breve["error"] = cliente.error
        return breve
    except Exception as e:  # noqa: BLE001 — sin mapa, la instalación igual queda hecha
        return {"activo": False, "error": f"{type(e).__name__}: {str(e)[:160]}"}


def despachar(name: str, args: dict) -> Any:
    _refrescar()
    if name == "suite_doctor":
        from diagnostico import diagnostico_completo
        resumen = diagnostico_completo()
        try:
            from config import tiempos_resumen
            rendimiento = tiempos_resumen()
            if rendimiento:
                resumen["rendimiento"] = rendimiento
        except Exception:  # noqa: BLE001 — la telemetría no puede tumbar el doctor
            pass
        return resumen
    elif name == "suite_instalar":
        import integraciones_harness as ih
        from config import servidor_actual
        from diagnostico import diagnostico_completo

        carpeta = args.get("carpeta") or "."
        detectados = ih.detectar_instalados(carpeta)
        escritos = ih.escribir_todos(detectados, carpeta_base=carpeta) if (detectados and args.get("escribir")) else []
        mapa = _asegurar_mapa_con_avances()
        resumen = diagnostico_completo()
        return {
            "harnesses": detectados,
            "escritos": [{"cliente": r.get("cliente"), "archivo": r.get("archivo"), "estado": r.get("estado")} for r in escritos],
            "mapa": mapa,
            "doctor": {"estado": resumen["estado"]},
            # Las del servidor completo (87), no las de este módulo: `TOOLS` acá son solo las de la suite.
            "herramientas": len(getattr(servidor_actual(), "TOOLS", TOOLS)),
            "verificacion": "openlegal doctor",
            "nota": "con escribir=True deja la configuración escrita; el harness tiene que reiniciarse para verla",
        }
    elif name == "skills_listar":
        return _listar_skills()
    elif name == "skill_ver":
        nombre = (args.get("nombre") or "").strip()
        if not nombre or "/" in nombre or "\\" in nombre or ".." in nombre:
            return {"error": "El parámetro 'nombre' es obligatorio (nombre simple, sin barras)."}
        from recursos import ruta_recurso
        archivo = ruta_recurso(".agents/skills") / nombre / "SKILL.md"
        if not archivo.exists():
            return {"error": f"No existe la skill «{nombre}».", "disponibles": [s["nombre"] for s in _listar_skills()["skills"]]}
        return {"nombre": nombre, "contenido": archivo.read_text(encoding="utf-8", errors="ignore")}
    elif name == "suite_telemetria_stats":
        from stats_tracker import get_suite_adoption_metrics
        metricas = get_suite_adoption_metrics()
        try:
            from config import tiempos_resumen
            metricas["rendimiento_fases"] = tiempos_resumen()
        except Exception:  # noqa: BLE001 — la telemetría no puede tumbar las métricas
            pass
        return metricas
    elif name == "suite_verificar_actualizacion":
        from update_checker import check_for_updates
        force = bool(args.get("forzar", False))
        return check_for_updates(force=force)
    elif name == "suite_auto_update":
        from update_checker import run_auto_update
        return run_auto_update()
    elif name == "descubrir_herramientas":
        import re
        import unicodedata
        from config import servidor_actual

        consulta = str(args.get("consulta") or "").strip()
        if not consulta:
            return {"error": "El parámetro 'consulta' es obligatorio."}
        try:
            limite = max(1, min(15, int(args.get("limite", 6))))
        except (ValueError, TypeError):
            limite = 6

        def _norm(s: str) -> str:
            return "".join(c for c in unicodedata.normalize("NFD", (s or "").lower()) if unicodedata.category(c) != "Mn")

        todas = list(getattr(servidor_actual(), "TOOLS", TOOLS))
        recomendadas_jev: list[str] = []
        materia_detectada = "general"
        try:
            global _JEV_ENGINE
            if _JEV_ENGINE is None:
                from legal_open_jev import LegalOpenJevEngine
                _JEV_ENGINE = LegalOpenJevEngine()
            triaje = _JEV_ENGINE.evaluate_choice(consulta, max_tools=limite)
            recomendadas_jev = list(getattr(triaje, "herramientas_recomendadas", []) or [])
            materia_detectada = str(getattr(triaje, "materia", "general"))
        except Exception:  # noqa: BLE001
            pass

        tokens = [t for t in re.findall(r"[a-z0-9_]+", _norm(consulta)) if len(t) >= 3]
        puntuadas: list[tuple[float, dict[str, Any]]] = []
        for tool in todas:
            tname = str(tool.get("name", ""))
            if tname in ("descubrir_herramientas", "invocar_herramienta"):
                continue
            score = 0.0
            if tname in recomendadas_jev:
                score += 10.0 - (recomendadas_jev.index(tname) * 0.5)
            texto_busq = _norm(f"{tname.replace('_', ' ')} {tool.get('description', '')}")
            for tok in tokens:
                if tok in _norm(tname):
                    score += 4.0
                elif tok in texto_busq:
                    score += 1.5
            if score > 0:
                puntuadas.append((score, tool))

        puntuadas.sort(key=lambda x: (-x[0], str(x[1].get("name", ""))))
        elegidas = [t for _, t in puntuadas[:limite]]
        return {
            "consulta": consulta,
            "materia_detectada": materia_detectada,
            "total_catalogo": len(todas),
            "herramientas": [
                {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "inputSchema": t.get("inputSchema", {}),
                }
                for t in elegidas
            ],
        }
    elif name == "invocar_herramienta":
        from config import servidor_actual

        objetivo = str(args.get("nombre") or "").strip()
        if not objetivo:
            return {"error": "El parámetro 'nombre' es obligatorio."}
        if objetivo in ("invocar_herramienta", "descubrir_herramientas"):
            return {"error": f"No se permite la invocación recursiva de '{objetivo}'."}
        sub_args = args.get("argumentos")
        if sub_args is None:
            sub_args = {}
        if not isinstance(sub_args, dict):
            return {"error": "El parámetro 'argumentos' debe ser un objeto JSON."}
        despachador_raiz = getattr(servidor_actual(), "handle_tool_call", None)
        if not callable(despachador_raiz):
            return {"error": "Servidor MCP no disponible para despacho dinámico."}
        return despachador_raiz(objetivo, sub_args)
    elif name == "app_abrir_grafo":
        from config import servidor_actual

        motor = getattr(servidor_actual(), "legal_graphify_engine", None)
        if motor is None:
            from legal_graphify import LegalGraphifyEngine

            motor = LegalGraphifyEngine()
        q = str(args.get("query") or "").strip()
        if q:
            return motor.consultar_subgrafo(q, max_hops=int(args.get("max_hops") or 1))
        return motor.resumen_por_comunidades(top_n=int(args.get("top_n") or 8))
    elif name == "app_abrir_calculadoras":
        from datetime import date
        from calculadoras_chile import feriados_chile

        vista = str(args.get("vista") or "plazos").strip().lower()
        if vista not in ("plazos", "finiquito", "cuantias", "indicadores"):
            vista = "plazos"
        anio_hoy = date.today().year
        return {
            "vista": vista,
            "anio": anio_hoy,
            "total_feriados_anio": len(feriados_chile(anio_hoy)),
            "calculadoras": ["plazos", "finiquito", "cuantias", "indicadores"],
        }
    elif name == "app_abrir_expediente":
        from config import servidor_actual

        entrada = str(args.get("entrada") or "").strip()
        if entrada:
            ci = getattr(servidor_actual(), "case_intake", None)
            if ci is not None:
                return ci.caso_analizar(entrada, args.get("tipo"), args.get("consulta", ""))
            import case_intake as ci_mod

            return ci_mod.caso_analizar(entrada, args.get("tipo"), args.get("consulta", ""))
        return {
            "guia_inicial": True,
            "mensaje": "Ingrese un relato de caso, carpeta de expediente o texto de proveído OJV para iniciar el tablero.",
            "herramientas_disponibles": ["caso_analizar", "vigilante_analizar_resolucion"],
        }
    return None


from servidor import crear_proxies

_JEV_ENGINE: Any = None
_PROPIOS = frozenset(globals())
_DEFAULTS_LAZY = crear_proxies("_listar_skills", "enviar_progreso")
globals().update(_DEFAULTS_LAZY)
