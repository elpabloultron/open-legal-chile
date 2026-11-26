"""
Open Legal Chile — CLI Maestro Unificado
Consola interactiva de inteligencia jurídica y consulta en tiempo real de leyes,
dictámenes, auditorías y jurisprudencia administrativa de la República de Chile.
"""

import sys
import os
import json
import pathlib
import argparse
from typing import Optional

# Asegurar que el directorio de Open Legal Chile tenga prioridad en sys.path
_pkg_root = os.path.dirname(os.path.abspath(__file__))
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)

# Asegurar encoding UTF-8 en terminal de Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        getattr(sys.stdout, "reconfigure")(encoding='utf-8')
except Exception:
    pass

# Importar conectores oficiales
from bcn_connector import BCNClient
from cgr_connector import CGRClient
from dt_connector import DTClient
from cne_connector import CNEClient
from panel_expertos_connector import PanelExpertosClient
from cmf_connector import CMFClient
from sii_connector import SIIClient
from ambiental_connector import SMAClient
from tdlc_connector import TDLCClient

# Inicializar clientes
bcn_client = BCNClient()
cgr_client = CGRClient()
dt_client = DTClient()
cne_client = CNEClient()
panel_client = PanelExpertosClient()
cmf_client = CMFClient()
sii_client = SIIClient()
sma_client = SMAClient()
tdlc_client = TDLCClient()


def print_banner():
    banner = """
================================================================================
   ⚖️  OPEN LEGAL CHILE — CONSOLA MAESTRA DE INTELIGENCIA JURÍDICA  ⚖️
   Sistema de Derecho Continental Codificado (Civil Law) — República de Chile
================================================================================
 Fuentes Conectadas: BCN Ley Chile | CGR | DT | CNE | Panel de Expertos | CMF | SII | SMA | TDLC | PJUD (CS/TC)
--------------------------------------------------------------------------------
"""
    print(banner)


def _estado_mapa() -> dict:
    """Estado del mapa del corpus de Hugging Face, sin red."""
    try:
        from mapa_corpus.cliente import obtener_cliente
        return dict(obtener_cliente().estado_breve())
    except Exception as e:  # noqa: BLE001
        return {"activo": False, "error": f"{type(e).__name__}: {str(e)[:160]}"}


def _asegurar_mapa(espera: float) -> dict:
    """Deja listo el mapa del corpus (descarga verificada + índice local), esperando hasta `espera`
    segundos. Un fallo de red no es un error de la suite: queda informado en el estado."""
    try:
        from mapa_corpus.cliente import obtener_cliente
        cliente = obtener_cliente()
        if cliente.habilitado:
            cliente.asegurar(bloquear=True, timeout=espera)
        breve = dict(cliente.estado_breve())
        if cliente.descargando:
            breve["nota"] = "la descarga del mapa sigue en segundo plano"
        if cliente.error:
            breve["error"] = cliente.error
        return breve
    except Exception as e:  # noqa: BLE001
        return {"activo": False, "error": f"{type(e).__name__}: {str(e)[:160]}"}


def _imprimir_mapa(breve: dict, sangria: str = "") -> None:
    if breve.get("activo"):
        conteos = breve.get("conteos") or {}
        print(f"{sangria}🗺️ Mapa del corpus: fuente {str(breve.get('sha_fuente') or '')[:8]} del "
              f"{str(breve.get('fecha_fuente') or '')[:10] or 's/f'} · {conteos.get('entradas', '?')} entradas")
        extras = ["aviso", "nota", "error"]
    else:
        # Una descarga fallida se dice primero, y sin el aviso de «se descarga en segundo plano»:
        # en la CLI el proceso termina aquí y no queda nada descargando.
        principal = next((k for k in ("error", "motivo", "aviso") if breve.get(k)), "")
        print(f"{sangria}🗺️ Mapa del corpus: {breve.get(principal) or 'no disponible'}")
        extras = ["nota"] + ([] if breve.get("error") or principal == "aviso" else ["aviso"])
    for clave in extras:
        if breve.get(clave):
            print(f"{sangria}   ↳ {breve[clave]}")


def menu_interactivo(parser: Optional[argparse.ArgumentParser] = None) -> None:
    print_banner()
    if parser is not None:
        parser.print_help()
    else:
        print("Usa `openlegal --help` para ver los subcomandos o `openlegal mcp` para el servidor MCP.")



def main():
    parser = argparse.ArgumentParser(
        description="⚖️ Open Legal Chile — Suite de Inteligencia Jurídica y Conectores de Datos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  openlegal                   -> Muestra la ayuda de subcomandos
  openlegal mcp               -> Inicia el servidor MCP estándar para Antigravity/Claude/Cursor
  openlegal chat              -> Inicia el asistente jurídico IA en la terminal
  openlegal critique <doc>    -> Ejecuta la auditoría forense de 5 dimensiones sobre un escrito
  openlegal generate <tipo>   -> Genera un borrador judicial completo (demanda, recurso, contrato)
  openlegal skills            -> Lista las habilidades y plugins jurídicos de la suite
  openlegal export            -> Exporta un escrito judicial forense a HTML/MD
  openlegal check             -> Ejecuta el doctor real de la suite (mide OCR, corpus, grafo, MCP)
  openlegal doctor            -> Igual que check: diagnóstico medido, sin tableros fijos
  openlegal search "..."      -> Realiza una búsqueda jurídica universal
  openlegal grado [materia]   -> Inicia el interrogador socrático para Examen de Grado
  openlegal vigilar [texto]   -> Analiza proveídos judiciales y calcula plazos fatales
  openlegal clinica [texto]   -> Traduce resoluciones judiciales a Lenguaje Claro
  openlegal interview         -> Inicia la entrevista de arranque y perfil del despacho
  openlegal arco              -> Genera respuesta oficial a solicitud de Derechos ARCO
  openlegal inapi [marca]     -> Evalúa factibilidad marcaria y cartas C&D en INAPI
  openlegal audit             -> Ejecuta la auditoría integral 360° (seguridad, anti-bloat, calidad, tests)
  openlegal doctrina "..."    -> Busca en los tratados canónicos de Derecho Chileno (FTS5)
  openlegal guias "..."       -> Consulta las guías de formación de la Academia Judicial
  openlegal stats             -> Muestra estadísticas globales de adopción (PyPI/GitHub)
  openlegal update            -> Comprueba y ejecuta la auto-actualización de la Suite
  openlegal ambiental "..."   -> Módulo especial de derecho ambiental (sentencias, anuarios, boletines y biblioteca)
  openlegal graph "..."       -> Consulta el Knowledge Graph (LegalGraphify) con ahorro mediano de tokens del 99,9 %
  openlegal agent [list|run]  -> Orquesta agentes jurídicos autónomos especializados (24 perfiles)
  openlegal caso <texto/ruta> -> Abre o crea expediente local con ingesta MD y subgrafo del caso
  openlegal vector "..."      -> Búsqueda semántica híbrida en los 9 Códigos y CPR (Dense + BM25)
  openlegal plugin instalar   -> Instala el Plugin completo (MCP + 26 skills + 24 agentes + reglas) en tu harness
  openlegal integrar          -> Muestra y escribe la configuración MCP de tu harness (--escribir)
  openlegal serve-http        -> Inicia el servidor MCP Streamable HTTP on-premise (Zero Data Leak)
  openlegal mcpb              -> Valida y empaqueta la extensión 1-clic `.mcpb` para Desktop
  openlegal bench             -> Ejecuta el benchmark reproducible ChileLegalBench v1.0 (105 casos)
  openlegal ci                -> Supervisa GitHub Actions y auto-repara fallos en CI
        """
    )
    parser.add_argument("comando", nargs="?", default="menu", choices=["menu", "mcp", "serve-http", "mcpb", "bench", "chat", "check", "doctor", "instalar", "plugin", "integrar", "ocr", "search", "skills", "export", "critique", "generate", "grado", "vigilar", "clinica", "interview", "arco", "inapi", "audit", "doctrina", "guias", "ambiental", "stats", "update", "cache", "graph", "agent", "agents", "caso", "vector", "ci"], help="Comando a ejecutar")
    parser.add_argument("query", nargs="*", help="Términos de búsqueda si usas 'search', archivo para 'critique' o tipo para 'generate'")
    parser.add_argument("--provider", type=str, default=None, help="Proveedor de IA (gemini, anthropic, deepseek, openai, ollama). Si se omite, se detecta automáticamente.")
    parser.add_argument("--buscar", type=str, help="Búsqueda jurídica universal")
    parser.add_argument("--contexto", type=str, default=None, help="Con 'ocr': para qué se usará el documento (plazo, escritura, tabla…)")
    parser.add_argument("--escribir", action="store_true", help="Con 'integrar': escribe la configuración del harness (con respaldo)")
    parser.add_argument("--todos", action="store_true", help="Con 'integrar': configura todos los harness detectados en la máquina")
    parser.add_argument("--json", action="store_true", help="Con 'instalar'/'plugin': salida legible por máquinas")
    parser.add_argument("--uvx", action="store_true", help="Con 'integrar'/'instalar'/'plugin': lanzar el MCP con uvx (no requiere el paquete instalado, solo uv)")
    parser.add_argument("--global", dest="global_", action="store_true", help="Con 'integrar': escribir la configuración global (de usuario) del harness")
    parser.add_argument("--proyecto", action="store_true", help="Con 'plugin instalar': instalar el bundle del plugin en la carpeta del proyecto actual en vez del usuario")
    parser.add_argument("--grafo", action="store_true", help="Con 'ambiental': añade el subgrafo de LegalGraphify con su ahorro de tokens (la primera consulta carga su índice)")
    parser.add_argument("--refrescar", action="store_true", help="Con 'cache': baja del hub las revisiones nuevas de lo ya cacheado; con 'cache mapa': descarga y verifica el mapa del corpus")
    parser.add_argument("--forzar", action="store_true", help="Con 'cache --refrescar': vuelve a bajar todo lo cacheado, aunque no haya cambiado")
    parser.add_argument("--profile", type=str, default=None, help="Con 'mcp'/'serve-http': perfil temático de herramientas (router, full, laboral…); también OPENLEGAL_PROFILE")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Con 'serve-http': interfaz de escucha (defecto 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Con 'serve-http': puerto TCP (defecto 8765)")
    parser.add_argument("--out", type=str, default="", help="Con 'mcpb': ruta del archivo .mcpb de salida")
    parser.add_argument("--categoria", type=str, default="", help="Con 'bench': filtrar una categoría de ChileLegalBench")
    parser.add_argument("--md-out", type=str, default="", help="Con 'bench': ruta de reporte Markdown")
    parser.add_argument("--json-out", type=str, default="", help="Con 'bench': ruta de reporte JSON")
    args = parser.parse_args()

    if args.comando == "mcp":
        import mcp_server
        mcp_server.main()
        return

    if args.comando == "serve-http":
        import mcp_http_server
        argv_http = ["--host", args.host, "--port", str(args.port)]
        if args.profile:
            argv_http += ["--profile", args.profile]
        raise SystemExit(mcp_http_server.main(argv_http))

    if args.comando == "mcpb":
        from scripts.empaquetar_mcpb import main as mcpb_main
        argv_mcpb = ["--out", args.out] if args.out else ["--check"]
        raise SystemExit(mcpb_main(argv_mcpb))

    if args.comando == "bench":
        from evals.chile_legal_bench import main as bench_main
        argv_bench = []
        if args.categoria:
            argv_bench += ["--categoria", args.categoria]
        if args.md_out:
            argv_bench += ["--md-out", args.md_out]
        if args.json_out:
            argv_bench += ["--json-out", args.json_out]
        raise SystemExit(bench_main(argv_bench))

    # Comprobar actualizaciones en segundo plano (no intrusivo)
    try:
        from update_checker import check_for_updates, format_update_banner
        up_info = check_for_updates()
        up_banner = format_update_banner(up_info)
        if up_banner:
            print(up_banner)
    except Exception:
        pass

    if args.comando == "chat":
        from chat_engine import LegalChatEngine
        engine = LegalChatEngine()
        provider = args.provider or LegalChatEngine.detect_provider()
        print_banner()
        modalidad = "MOTOR SOBERANO (100% Libre / Cero API Keys)" if provider == "soberano" else f"PROVEEDOR: {provider.upper()}"
        print(f"🤖 INICIANDO CHAT JURÍDICO INTERACTIVO [{modalidad}]")
        print("Escribe tus consultas jurídicas. Para salir escribe 'exit' o 'salir'.\n" + "-"*80)

        history = []
        while True:
            try:
                msg = input("\n👤 Tú: ").strip()
                if not msg:
                    continue
                if msg.lower() in ["exit", "salir", "q"]:
                    print("\n👋 Cerrando chat jurídico Open Legal Chile.\n")
                    break

                print(f"⚖️ Asistente ({provider.upper()}): Pensando...")
                res = engine.chat(user_message=msg, provider=provider, history=history)

                if res.get("error"):
                    print(f"\n⚠️ {res.get('error')}")
                else:
                    if res.get("contextUsed"):
                        print("🛰️ [Contexto normativo chileno oficial inyectado automáticamente]")
                    print(f"\n{res.get('reply')}\n")
                    history.append({"role": "user", "content": msg})
                    history.append({"role": "assistant", "content": res.get("reply")})

            except KeyboardInterrupt:
                print("\n\n👋 Cerrando chat jurídico.\n")
                break

    if args.comando == "instalar":
        import integraciones_harness as ih
        from diagnostico import diagnostico_completo

        carpeta = pathlib.Path.cwd()
        detectados = ih.detectar_instalados(carpeta)
        if not detectados:
            print("No se detectó ningún harness en esta carpeta (se buscó .claude, .cursor, .vscode, .gemini, "
                  ".codex, .hermes, .dsh, opencode.json y .antigravity). Instala el plugin completo con: "
                  "openlegal plugin instalar antigravity|claude-code|codex|hermes")
        escritos = (
            ih.instalar_plugin_todos(detectados, carpeta_base=carpeta, global_=False, uvx=args.uvx)
            if detectados
            else []
        )
        # La instalación deja el mapa del corpus listo; un fallo de red no la hace fallar (queda el aviso).
        mapa = _asegurar_mapa(600.0)
        resumen = diagnostico_completo()
        from mcp_server import TOOLS as _TOOLS_MCP

        if args.json:
            print(json.dumps({
                "harnesses": detectados,
                "archivos": {r.get("cliente"): r.get("archivo") for r in escritos},
                "estado_config": [r.get("estado") for r in escritos],
                "plugins": escritos,
                "doctor": {"estado": resumen["estado"]},
                "herramientas": len(_TOOLS_MCP),
                "mapa": mapa,
                "verificacion": "openlegal doctor",
            }, ensure_ascii=False, indent=2))
        else:
            print_banner()
            print(f"\n📦 INSTALACIÓN COMPLETA DE PLUGIN — harness configurados: {', '.join(detectados) or 'ninguno'}")
            for r in escritos:
                print(
                    f"   • {r.get('cliente')}: {r.get('estado')} "
                    f"(skills: {r.get('skills', 0)}, agentes: {r.get('agents', 0)}, mcp: {r.get('archivo')})"
                )
            print(f"   {len(_TOOLS_MCP)} herramientas MCP · estado del sistema: {resumen['estado'].upper()}")
            _imprimir_mapa(mapa, sangria="   ")
            print("   Verificalo con: openlegal doctor\n")
        return

    if args.comando == "plugin":
        import integraciones_harness as ih

        sub = (args.query[0] if args.query else "").strip().lower()
        objetivos = [q.strip() for q in args.query[1:] if q.strip()] if sub in ("instalar", "install") else []

        if sub not in ("instalar", "install"):
            print_banner()
            print("\n🧩 PLUGIN COMPLETO OPEN LEGAL CHILE (MCP + 26 skills + 24 agentes + reglas chilenas)\n")
            print("Comandos de instalación en 1 paso:")
            print("  • Auto-detectar harnesses : openlegal plugin instalar")
            print("  • Google Antigravity      : openlegal plugin instalar antigravity")
            print("  • Claude Code             : openlegal plugin instalar claude-code")
            print("    (o nativo en Claude)    : /plugin marketplace add elpabloultron/open-legal-chile && /plugin install open-legal-chile")
            print("  • OpenAI Codex            : openlegal plugin instalar codex")
            print("    (o marketplace Codex)   : npx codex-marketplace add elpabloultron/open-legal-chile --plugins")
            print("  • Hermes Agent            : openlegal plugin instalar hermes")
            print("  • OpenCode                : openlegal plugin instalar opencode")
            print("  • Cursor / VS Code        : openlegal plugin instalar cursor | vscode")
            print("\nOpciones: --proyecto (instala en la carpeta actual en vez del usuario) · --uvx · --json\n")
            return

        es_global = not args.proyecto
        base_dest = pathlib.Path.cwd() if args.proyecto else None
        try:
            resultados = (
                ih.instalar_plugin_todos(objetivos, carpeta_base=base_dest, global_=es_global, uvx=args.uvx)
                if objetivos
                else ih.instalar_plugin_todos(None, carpeta_base=base_dest, global_=es_global, uvx=args.uvx)
            )
        except ValueError as exc:
            print(f"❌ {exc}")
            return

        if args.json:
            print(json.dumps({"alcance": "proyecto" if args.proyecto else "usuario", "plugins": resultados}, ensure_ascii=False, indent=2))
            return

        print_banner()
        if not resultados:
            print("\n⚠️  No se detectó ningún harness instalado automáticamente.")
            print("   Indica uno explícitamente, por ejemplo: openlegal plugin instalar antigravity\n")
            return
        print(f"\n🧩 PLUGIN COMPLETO INSTALADO ({'proyecto' if args.proyecto else 'usuario'}):\n")
        for r in resultados:
            print(
                f"  ✅ {r.get('cliente'):<14} · modo={r.get('modo')} · "
                f"skills={r.get('skills', 0)} · agentes={r.get('agents', 0)} · mcp={r.get('archivo')}"
            )
            if r.get("plugin_dir"):
                print(f"     carpeta plugin : {r['plugin_dir']}")
            if r.get("reglas"):
                print(f"     reglas chilenas: {r['reglas']}")
            if r.get("comando_nativo"):
                print(f"     marketplace    : {r['comando_nativo']}")
        print("\nReinicia tu harness y verifica con: openlegal doctor\n")
        return

    if args.comando == "integrar":
        from integraciones_harness import (clientes as clientes_ih, configuracion as config_ih,
                                           detectar_instalados, escribir as escribir_ih,
                                           escribir_todos as escribir_todos_ih)
        try:
            from mcp_server import TOOLS as _TOOLS_MCP
            total_mcp = len(_TOOLS_MCP)
        except Exception:  # noqa: BLE001
            total_mcp = 85

        cliente = (args.query[0] if args.query else "").strip()
        if args.todos:
            print_banner()
            detectados = detectar_instalados()
            if not detectados:
                print("\nNo detecté harness instalados en esta máquina. Opciones: " + ", ".join(clientes_ih()))
                print("Ejemplo: openlegal integrar claude-code --escribir\n")
                return
            print(f"\n🔌 Integrando {len(detectados)} harness detectados: {', '.join(detectados)}\n")
            for resultado in escribir_todos_ih(detectados, uvx=args.uvx):
                print(json.dumps(resultado, ensure_ascii=False))
            print(f"\n✅ Listo. Reiniciá cada harness: tienen que verse {total_mcp} herramientas MCP.\n")
            return
        if not cliente:
            print_banner()
            print(f"\n🔌 INTEGRAR OPEN LEGAL CHILE EN TU HARNESS ({total_mcp} herramientas MCP)\n")
            for nombre in clientes_ih():
                cfg = config_ih(nombre, uvx=args.uvx, global_=args.global_)
                print(f" • {nombre:<15} → {cfg['ruta']}")
            print("\nEjemplo: openlegal integrar claude-code --escribir")
            print("Sin --escribir, solo muestra el contenido listo para pegar. --global: configuración de usuario;")
            print("--uvx: lanza el servidor con uvx (no hace falta tener el paquete instalado, solo uv).\n")
            return
        try:
            cfg = config_ih(cliente, uvx=args.uvx, global_=args.global_)
        except ValueError as exc:
            print(f"❌ {exc}")
            return
        if not args.escribir:
            print(f"# {cfg['cliente']} → {cfg['ruta']} (agregá --escribir para guardarlo)\n")
            print(cfg["contenido"])
            return
        resultado = escribir_ih(cfg["cliente"], carpeta_base=pathlib.Path.home() if args.global_ else None,
                                uvx=args.uvx)
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        if resultado["estado"] in ("escrito", "fusionado", "agregado", "registrado"):
            print(f"\n✅ Listo. Reiniciá el harness y pedile «tools/list»: tienen que verse {total_mcp} herramientas.")
        return

    elif args.comando == "ocr":
        from ocr_decision import recomendar_ocr

        ruta = " ".join(args.query) if args.query else ""
        if not ruta:
            print("❌ Uso: openlegal ocr <ruta-del-pdf> [--contexto \"expediente con plazo corriendo\"]")
            return
        plan = recomendar_ocr(ruta, args.contexto or "")
        if plan.get("error"):
            print(f"❌ {plan['error']}")
            return
        print_banner()
        print(f"\n🔍 PLAN DE OCR — {plan['documento']}")
        print(f"   tipo: {plan['tipo_documento']} · páginas: {plan['senales']['paginas']} · "
              f"con capa de texto: {plan['senales']['paginas_con_texto']}")
        print(f"   recomendado: {plan['recomendado']}")
        for alternativa in plan["alternativas"]:
            print(f"   alternativa: {alternativa}")
        print("\n Razonamiento:")
        for linea in plan["razonamiento"]:
            print(f"   • {linea}")
        for aviso in plan["avisos"]:
            print(f"   ⚠️  {aviso}")
        print(f"\n Ejecutar con: {plan['como_ejecutar']['herramienta']} {plan['como_ejecutar']['argumentos']}\n")
        return

    elif args.comando in ("doctor", "check"):
        print_banner()
        from diagnostico import diagnostico_completo

        resumen = diagnostico_completo()
        iconos = {"ok": "✅", "aviso": "⚠️", "error": "❌", "omitido": "⚪"}
        print(f"\n🩺 DOCTOR DE OPEN LEGAL CHILE — estado: {resumen['estado'].upper()}\n")
        for chequeo in resumen["chequeos"]:
            print(f" {iconos.get(chequeo['estado'], '•')} {chequeo['nombre']:<18} {chequeo['detalle']}")
            if chequeo.get("sugerencia"):
                print(f"    ↳ {chequeo['sugerencia']}")
        print()

    elif args.comando == "search" or args.buscar:
        q = " ".join(args.query) if args.query else args.buscar
        if not q:
            print("❌ Debes especificar un término de búsqueda. Ejemplo: openlegal search 'Ley Karin'")
            return

        print_banner()
        print(f"\n🛰️ Búsqueda Jurídica Universal en los 10 organismos del Estado para: '{q}'...")
        import mcp_server
        res = mcp_server.handle_tool_call("busqueda_universal", {"consulta": q}).get("resultados", {})

        # BCN
        bcn_res = res.get("bcn", [])
        print(f"\n📜 BCN Ley Chile: {len(bcn_res)} normas")
        for it in bcn_res[:3]:
            if "error" in it:
                print(f"  * Error: {it['error']}")
            else:
                print(f"  * [{it.get('tipo')} {it.get('numero') or it.get('codigo')}] {it.get('titulo', '')}")

        # CGR
        cgr_res = res.get("cgr", {})
        print(f"\n🏛️ Contraloría (CGR): {cgr_res.get('total', 'error')} dictámenes")
        for it in (cgr_res.get("resultados") or [])[:3]:
            print(f"  * [Dictamen CGR N° {it.get('numero') or it.get('docId')} ({it.get('anio') or it.get('fecha')})] {it.get('materia')}")

        # DT
        dt_res = res.get("dt", [])
        print(f"\n💼 Dirección del Trabajo (DT): {len(dt_res)} encontrados")
        for it in dt_res[:3]:
            if "error" in it:
                print(f"  * Error: {it['error']}")
            else:
                detalle = (it.get('materias') or (it.get('doctrina') or '')[:120]) or "Sin resumen"
                print(f"  * [{it.get('titulo')}] {detalle}")

        # CNE
        cne_res = res.get("cne", [])
        print(f"\n⚡ CNE (Energía): {len(cne_res)} registros")
        for it in cne_res[:3]:
            if "error" in it:
                print(f"  * Error: {it['error']}")
            else:
                print(f"  * {str(it)[:150]}")

        # Panel de Expertos
        panel_res = res.get("panel", [])
        print(f"\n🔌 Panel de Expertos: {len(panel_res)} discrepancias")
        for it in panel_res[:3]:
            if "error" in it:
                print(f"  * Error: {it['error']}")
            else:
                print(f"  * Discrepancia N° {it.get('numero', '?')}: {it.get('materia') or 'Sin materia'}")

        # CMF
        cmf_res = res.get("cmf", [])
        print(f"\n🏢 CMF (Normativa): {len(cmf_res)} resultados")
        for it in cmf_res[:3]:
            if "error" in it:
                print(f"  * Error: {it['error']}")
            else:
                print(f"  * {it.get('titulo')}")

        # SII
        sii_res = res.get("sii", [])
        print(f"\n💰 SII (Circulares): {len(sii_res)} resultados")
        for it in sii_res[:3]:
            if "error" in it:
                print(f"  * Error: {it['error']}")
            else:
                print(f"  * [{it.get('anio')}] {it.get('titulo')}")

        # SMA
        sma_res = res.get("sma", {})
        print(f"\n🌱 SMA (Ambiental): {sma_res.get('total', 'error')} sancionatorios")
        for it in (sma_res.get("resultados") or [])[:3]:
            print(f"  * [{it.get('expediente')}] {it.get('titular')}")

        # TDLC
        tdlc_res = res.get("tdlc", [])
        print(f"\n🛒 TDLC (Libre Competencia): {len(tdlc_res)} sentencias")
        for it in tdlc_res[:3]:
            if "error" in it:
                print(f"  * Error: {it['error']}")
            else:
                print(f"  * {it.get('titulo')}")

        # PJUD
        pjud_res = res.get("pjud", [])
        print(f"\n⚖️ PJUD (Corte Suprema / TC): {len(pjud_res)} fallos")
        for it in pjud_res[:3]:
            if "error" in it:
                print(f"  * Error: {it['error']}")
            else:
                print(f"  * [CS - {it.get('rol')}, Fecha: {it.get('fecha')}] {it.get('caratula')}")

    elif args.comando == "skills":
        print_banner()
        print("\n🧩 HABILIDADES Y AGENTES JURÍDICOS ACTIVOS (Open Legal Chile)\n")
        try:
            from mcp_server import _listar_skills
            catalogo = _listar_skills()
            for indice, skill in enumerate(catalogo["skills"], 1):
                print(f" {indice:>2}. 🧩 {skill['nombre']:<32} {skill['titulo'][:60]}")
            print(f"\n🤖 Agentes autónomos ({len(catalogo['agentes'])}): " + ", ".join(catalogo["agentes"]))
            print("\nUsá `openlegal integrar --todos --escribir` para que tu harness vea todas las herramientas,")
            print("y `openlegal doctor` para comprobar qué quedó instalado.")
        except Exception as exc:  # noqa: BLE001 - el listado no puede tumbar la consola
            print(f"No pude listar las skills ({exc}). Reinstalá el paquete si falta el corpus.")
        print()


    elif args.comando == "export":
        from exporters import LegalDocumentExporter
        exporter = LegalDocumentExporter()
        print_banner()
        print("📄 GENERADOR Y EXPORTADOR FORENSE DE DOCUMENTOS LEGALES")
        res = exporter.export_brief(
            titulo_principal="DEMANDA ORDINARIA DE RESOLUCIÓN DE CONTRATO CON INDEMNIZACIÓN DE PERJUICIOS",
            tribunal="S.J.L. EN LO CIVIL DE SANTIAGO",
            presuma_data={
                "procedimiento": "ORDINARIO",
                "materia": "RESOLUCIÓN DE CONTRATO",
                "demandante": "PABLO BENAVIDES JORQUERA",
                "rut_dte": "XX.XXX.XXX-X",
                "abogado": "ABOGADO PATROCINANTE",
                "rut_abg": "XX.XXX.XXX-X",
                "demandado": "EMPRESA CONTRAPARTE S.A.",
                "rut_ddo": "76.XXX.XXX-X"
            },
            comparecencia="PABLO BENAVIDES JORQUERA, cédula nacional de identidad N° XX.XXX.XXX-X, domiciliado en Santiago, a US. respetuosamente digo:",
            hechos="1. Las partes suscribieron contrato de prestación de servicios.\n2. La demandada incumplió gravemente sus obligaciones.",
            derecho="Artículos 1489, 1545, 1546 y siguientes del Código Civil de la República de Chile.",
            peticiones="POR TANTO, A US. PIDO tener por interpuesta demanda ordinaria y declarar resuelto el contrato con costas.",
            otrosies=[
                {"numero": "PRIMER OTROSÍ", "titulo": "Patrocinio y Poder", "contenido": "Tener presente patrocinio y poder conferido bajo la Ley 18.120 y Ley 20.886."}
            ]
        )
        print("\n✅ Documento exportado con éxito en:")
        print(f" • HTML: {res['htmlPath']}")
        print(f" • MD:   {res['markdownPath']}\n")

    elif args.comando == "critique":
        from critique import LegalCritiqueEngine
        critique_engine = LegalCritiqueEngine()
        print_banner()
        target = " ".join(args.query) if args.query else ""
        if not target:
            print("❌ Especifica el archivo a auditar. Ejemplo: openlegal critique demanda.txt")
            return

        if os.path.exists(target):
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        else:
            content = target

        print(f"🔍 AUDITANDO DOCUMENTO BAJO LAS 5 DIMENSIONES FORENSES ({(args.provider or 'auto').upper()})...\n" + "-"*80)
        res = critique_engine.critique(content, provider=args.provider)
        print(res.get("critique", res.get("error")))

    elif args.comando == "generate":
        from exporters import LegalDocumentExporter
        exporter = LegalDocumentExporter()
        print_banner()
        doc_type = args.query[0].lower() if args.query else "demanda_civil"
        print(f"⚡ GENERANDO ARTEFACTO FORENSE OJV: [{doc_type.upper()}]...")

        templates = {
            "demanda_civil": {
                "titulo": "DEMANDA ORDINARIA DE RESOLUCIÓN DE CONTRATO E INDEMNIZACIÓN",
                "tribunal": "S.J.L. EN LO CIVIL DE SANTIAGO",
                "materia": "RESOLUCIÓN DE CONTRATO"
            },
            "proteccion": {
                "titulo": "RECURSO DE PROTECCIÓN CONSTITUCIONAL",
                "tribunal": "I. CORTE DE APELACIONES DE SANTIAGO",  # pragma: allowlist secret
                "materia": "GARANTÍAS CONSTITUCIONALES ART. 19 Y 20 CPR"
            },
            "laboral": {
                "titulo": "DEMANDA POR DESPIDO INJUSTIFICADO Y COBRO DE PRESTACIONES",
                "tribunal": "S.J.L. DEL TRABAJO DE SANTIAGO",
                "materia": "DESPIDO INJUSTIFICADO ART. 161"
            },
            "ppa": {
                "titulo": "CONTRATO DE SUMINISTRO DE ENERGÍA ELÉCTRICA (PPA CLIENTE LIBRE)",
                "tribunal": "ARBITRAJE COMERCIAL CAM SANTIAGO",
                "materia": "MERCADO ELÉCTRICO LEY 20.936"
            }
        }
        cfg = templates.get(doc_type, templates["demanda_civil"])
        res = exporter.export_brief(
            titulo_principal=cfg["titulo"],
            tribunal=cfg["tribunal"],
            presuma_data={"materia": cfg["materia"], "demandante": "COMPARECIENTE TITULAR", "rut_dte": "XX.XXX.XXX-X", "demandado": "PARTE CONTRAPARTE", "rut_ddo": "76.XXX.XXX-X", "abogado": "ABOGADO PATROCINANTE", "rut_abg": "XX.XXX.XXX-X"},
            comparecencia="COMPARECIENTE TITULAR, cédula nacional de identidad N° XX.XXX.XXX-X, a US. respetuosamente digo:",
            hechos="1. Antecedentes fácticos y cronológicos del caso.\n2. Infracción y perjuicios irrogados.",
            derecho="Artículos pertinentes del ordenamiento jurídico chileno.",
            peticiones="POR TANTO, A US. PIDO tener por interpuesta la acción y acogerla en todas sus partes con costas.",
            otrosies=[{"numero": "PRIMER OTROSÍ", "titulo": "Patrocinio y Poder", "contenido": "Tener presente patrocinio y poder conferido bajo la Ley 18.120 y Ley 20.886."}]
        )
        print("\n✅ Artefacto generado con éxito:")
        print(f" • HTML: {res['htmlPath']}")
        print(f" • MD:   {res['markdownPath']}\n")

    elif args.comando == "grado":
        from examen_grado import ExamenGradoEngine
        engine = ExamenGradoEngine()
        print_banner()
        mat = args.query[0] if args.query else "civil"
        res = engine.interrogar_socratico(materia=mat)
        print(f"🎓 INTERROGACIÓN SOCRÁTICA DE EXAMEN DE GRADO ({res['area']})")
        print(f"📌 Tema: {res['tema']}")
        print(f"❓ Pregunta de la Comisión: {res['pregunta_socratica']}\n")
        print("📖 Normas y Tratados Vinculados:")
        for a in res['articulos_vinculados']:
            print(f"  • {a}")
        print(f"  • Doctrina canónica: {res['autor_canonico']} ({res['obra_relevante']})\n")
        print(f"⚖️ Estándar de Aprobación:\n{res['estandar_evaluacion']}\n")

    elif args.comando == "vigilar":
        from docket_watcher import DocketWatcherEngine
        print_banner()
        texto = " ".join(args.query) if args.query else "Autos para fallo"
        res = DocketWatcherEngine.analizar_resolucion(texto)
        print("🕵️ VIGILANTE PROCESAL — ANÁLISIS DE RESOLUCIÓN:")
        print(f"Texto: '{texto}'\n" + "-"*60)
        if res.get("encontrado"):
            print(f"⚡ Trámite: {res['tipo_tramite']} (Severidad: {res['severidad']})")
            print(f"📋 Instrucción: {res['instruccion_abogado']}\n")
            print("⏳ Plazos Fatales Detectados:")
            for p in res.get("cargas_procesales_y_plazos", []):
                print(f"  • {p['accion']}: {p['dias_habiles']} días hábiles ({p['articulo']})")
        else:
            print(res.get("mensaje"))
        print()

    elif args.comando == "clinica":
        from clinica_juridica import ClinicaJuridicaEngine
        print_banner()
        texto = " ".join(args.query) if args.query else "Autos para fallo con citación"
        res = ClinicaJuridicaEngine.traducir_lenguaje_claro(texto)
        print("🤝 CLÍNICA JURÍDICA — TRADUCCIÓN A LENGUAJE CLARO:")
        print(f"Texto original: '{texto}'\n" + "-"*60)
        print(res.get("traduccion_lenguaje_claro"))
        print()

    elif args.comando == "interview":
        from cold_start import ColdStartInterviewEngine
        ColdStartInterviewEngine.run_interactive()

    elif args.comando == "arco":
        from privacidad_inapi import PrivacyARCOEngine
        print_banner()
        res = PrivacyARCOEngine.procesar_solicitud_arco("ACCESO", "Juan Pérez González", "15.123.456-7", "Historial de transacciones y perfilamiento")
        print("🛡️ MODELO OFICIAL DE RESPUESTA DERECHOS ARCO:")
        print(res.get("modelo_oficial_respuesta"))
        print()

    elif args.comando == "inapi":
        from privacidad_inapi import INAPIEngine
        print_banner()
        marca = args.query[0] if args.query else "LexChile"
        res = INAPIEngine.evaluar_factibilidad_marca(marca)
        print(f"🔍 EVALUACIÓN DE FACTIBILIDAD MARCARIA (INAPI): {marca}")
        print(f"Clase: {res['clase_niza']} ({res['descripcion_clase']})")
        print(f"Riesgo Preliminar: {res['nivel_riesgo_preliminar']}")
        for m in res['analisis_distintividad']:
            print(f"  • {m}")
        print(f"\n💡 Recomendación: {res['recomendacion']}\n")

    elif args.comando == "audit":
        audit_script = os.path.join(os.path.dirname(__file__), "audit.sh")
        if os.path.exists(audit_script):
            import subprocess
            subprocess.run(["bash", audit_script])  # nosec B603, B607
        else:
            print("❌ No se encontró el script audit.sh")

    elif args.comando == "doctrina":
        from doctrina_connector import search_doctrina
        print_banner()
        q = " ".join(args.query) if args.query else "nulidad"
        res = search_doctrina(q, limit=5)
        print(f"📚 BÚSQUEDA DOCTRINAL CANÓNICA (FTS5): '{q}'")
        print(f"Total coincidencias: {len(res)}\n" + "-"*60)
        for idx, item in enumerate(res):
            print(f"[{idx+1}] 🏛️ {item.get('institucion')} — {item.get('autor')} ({item.get('area')})")
            print(f"  📖 {item.get('obra')}")
            if item.get('definicion'):
                print(f"  📜 Definición: {item.get('definicion')[:250]}...")
            if item.get('concordancias'):
                print(f"  🔗 {item.get('concordancias')}")
            print()

    elif args.comando == "guias":
        from academia_judicial_connector import AcademiaJudicialClient
        print_banner()
        q = " ".join(args.query) if args.query else ""
        aj = AcademiaJudicialClient()
        res = aj.buscar_guias(q)
        print(f"⚖️ GUÍAS OFICIALES DE LA ACADEMIA JUDICIAL: '{q}'")
        print(f"Total guías encontradas: {len(res)}\n" + "-"*60)
        for idx, g in enumerate(res[:8]):
            print(f"[{idx+1}] 📘 {g.get('titulo')} [{g.get('materia')}]")
            print(f"  📄 {g.get('descripcion')}")
            print(f"  🔗 PDF: {g.get('url_pdf')}\n")

    elif args.comando == "ambiental":
        from modulo_ambiental import consulta_ambiental
        print_banner()
        q = " ".join(args.query) if args.query else ""
        if not q:
            print("⚠️ Uso: openlegal ambiental \"<consulta>\" [--grafo]")
            return 1
        res = consulta_ambiental(q, limite=8, incluir_subgrafo=bool(args.grafo))
        print(f"🌿 MÓDULO DE DERECHO AMBIENTAL: '{res['consulta']}'")
        print(f"Materia ambiental: {'sí' if res['materia_ambiental'] else 'no'} · resultados: {len(res['resultados'])}")
        print("-" * 65)
        for r in res["resultados"]:
            print(f"\n[{r.get('tipo', '')}] {r['titulo'][:100]}")
            print(f"  {r['cita']} {r['enlace']}")
            if r.get("fragmento"):
                print(f"  «{r['fragmento'][:240]}»")
        if res.get("subgrafo"):
            m = (res["subgrafo"] or {}).get("metricas_tokens") or {}
            if m:
                print(f"\nSubgrafo: ahorro {m.get('porcentaje_ahorro', '?')} % · factor {m.get('factor_reduccion', '?')}"
                      f" ({m.get('tokens_subgrafo', '?')} vs {m.get('tokens_texto_completo', '?')} tokens)")
        if res.get("faltantes"):
            print(f"Faltantes: {', '.join(res['faltantes'])}")
        print()

    elif args.comando == "stats":
        from stats_tracker import get_suite_adoption_metrics
        print_banner()
        m = get_suite_adoption_metrics()
        pypi = m.get("metricas_pypi", {})
        gh = m.get("metricas_github", {})
        loc = m.get("capacidades_locales", {})
        print("📊 ESTADÍSTICAS GLOBALES DE ADOPCIÓN Y DESCARGAS (OPEN LEGAL CHILE):")
        print(f"• PyPI Descargas Hoy: {pypi.get('descargas_ultimo_dia')}")
        print(f"• PyPI Descargas Última Semana: {pypi.get('descargas_ultima_semana')}")
        print(f"• PyPI Descargas Último Mes: {pypi.get('descargas_ultimo_mes')}")
        print(f"• PyPI Total Estimado: {pypi.get('descargas_totales_estimadas')}")
        print(f"• GitHub Estrellas: {gh.get('estrellas')} | Forks: {gh.get('forks')}")
        print(f"• Herramientas MCP: {loc.get('herramientas_mcp_oficiales')}")
        print(f"• Instituciones Doctrinales FTS5: {loc.get('instituciones_doctrinales_indexadas')}")
        print(f"• Documentos Biblioteca Markdown: {loc.get('documentos_biblioteca_markdown')}")
        print(f"🛡️ {loc.get('filosofia')}\n")

    elif args.comando == "update":
        from update_checker import run_auto_update
        print_banner()
        print("⏳ Ejecutando auto-actualización de Open Legal Chile Suite...")
        res = run_auto_update()
        if res.get("exito"):
            print("✅ ¡Actualización completada exitosamente!")
        else:
            print("⚠️ Nota sobre la actualización:")
        print(f"Mensaje: {res.get('mensaje')}")
        if res.get("salida"):
            print("\nDetalle:\n" + res.get("salida")[:500])
        print()

    elif args.comando == "cache":
        tokens = [t.lower() for t in (args.query or [])]
        if "warm" in tokens or "calentar" in tokens:
            from scripts.cache_warming import ejecutar_cache_warming
            ejecutar_cache_warming()
            return
        if "mapa" in tokens:
            print_banner()
            if args.refrescar:
                print("🗺️ Descargando y verificando el mapa del corpus de Hugging Face…")
            breve = _asegurar_mapa(1800.0) if args.refrescar else _estado_mapa()
            _imprimir_mapa(breve)
            print()
            return
        from online_library_sync import estado_cache_corpus, refrescar_cache_corpus
        print_banner()
        if args.refrescar:
            res = refrescar_cache_corpus(forzar=args.forzar)
            print(f"✅ Refresco del corpus cacheado: {res['actualizados']} actualizados de {res['revisados']} revisados")
            for e in res["errores"][:5]:
                print(f"  [!] {e}")
        else:
            est = estado_cache_corpus()
            print(f"🗂️ Caché del corpus: {est['archivos']} archivos · {est['mb']} MB")
            print(f"Desactualizados en el hub: {len(est['desactualizados'])}")
            for a in est["desactualizados"][:10]:
                print(f"  · {a}")
            if est.get("sin_registrar"):
                print(f"Sin registrar la revisión (se registra al refrescar): {len(est['sin_registrar'])}")
            if est["desactualizados"] or est.get("sin_registrar"):
                print("Refrescalos con: openlegal cache --refrescar")
        print()

    elif args.comando == "caso":
        import case_intake
        print_banner()
        entrada = " ".join(args.query).strip()
        if not entrada:
            entrada = input("👉 Ingresa la ruta de la carpeta, archivo o consulta del caso: ").strip()
        if entrada:
            print("\n📂 Analizando caso y creando espacio de trabajo local...")
            analisis = case_intake.caso_analizar(entrada)
            print("\n" + analisis.get("resumen", ""))
        return

    elif args.comando == "vector":
        from vector_engine import obtener_motor_vectorial
        print_banner()
        motor = obtener_motor_vectorial()
        tokens = args.query or []
        subcmd = tokens[0].lower() if tokens else ""
        if subcmd in ("indexar", "warm", "precalentar"):
            print("🧠 Indexando Códigos de la República y CPR vectorialmente...")
            res = motor.indexar_desde_bcn_cache(forzar=args.forzar)
            print(f"✅ Artículos indexados: {sum(res.values())}")
        else:
            consulta = " ".join(tokens).strip()
            if not consulta:
                consulta = input("🔍 Búsqueda vectorial híbrida (9 Códigos y CPR): ").strip()
            if consulta:
                hits = motor.buscar_hibrido(consulta, top_k=5)
                print(f"\n✨ Resultados Híbridos (Dense + BM25) para: '{consulta}'\n" + "-"*80)
                for i, h in enumerate(hits, 1):
                    print(f"[{i}] {h['etiqueta_bcn']} (RRF: {h.get('puntaje_rrf', 0):.4f})")
                    print(f"    {h['texto'][:200]}...\n")
        return

    elif args.comando == "graph":
        from legal_graphify import LegalGraphifyEngine
        print_banner()
        engine = LegalGraphifyEngine()
        tokens = args.query if args.query else []

        if tokens and tokens[0] == "path":
            if len(tokens) < 3:
                print("⚠️ Uso: openlegal graph path <origen> <destino>")
            else:
                orig, dest = tokens[1], tokens[2]
                res = engine.encontrar_camino(orig, dest)
                if not res.get("encontrado"):
                    print(f"⚠️ {res.get('mensaje')}")
                else:
                    print(f"🛤️ CAMINOS RELACIONALES: '{res['origen']}' ➔ '{res['destino']}'")
                    print("═"*65)
                    for idx, c in enumerate(res["caminos"], 1):
                        print(f"Ruta {idx} ({c['longitud_saltos']} saltos):\n  {c['trazado']}\n")

        elif tokens and tokens[0] == "explain":
            q_exp = " ".join(tokens[1:]) if len(tokens) > 1 else "simulacion"
            exp = engine.explicar_institucion(q_exp)
            if not exp.get("encontrado"):
                print(f"⚠️ {exp.get('mensaje')}")
            else:
                print(exp["explicacion_markdown"] + "\n")

        elif tokens and tokens[0] == "affected":
            norma = " ".join(tokens[1:]) if len(tokens) > 1 else "Art. 2515 CC"
            impact = engine.analizar_impacto_normativo(norma)
            if not impact.get("encontrado"):
                print(f"⚠️ {impact.get('mensaje')}")
            else:
                print(f"💥 ANÁLISIS DE IMPACTO (Blast Radius): {impact['objetivo']}")
                print("═"*65)
                print(f"Riesgo de Impacto:       {impact['nivel_riesgo_impacto']}")
                print(f"Afectados Directos (G1): {impact['metricas_impacto']['afectados_directos_grado_1']}")
                print(f"Afectados Cascada (G2):  {impact['metricas_impacto']['afectados_cascada_grado_2']}")
                print(f"Total Nodos en Riesgo:   {impact['metricas_impacto']['total_entidades_impactadas']}")
                print(f"\nDictamen:\n  {impact['dictamen_sintetico']}\n")
                print("Entidades Afectadas Directamente:")
                for it in impact["impacto_directo"]:
                    print(f"  • [{it['tipo']}] {it['label']}")
                print()

        elif tokens and tokens[0] in ("god-nodes", "godnodes"):
            top = 10
            if len(tokens) > 1 and tokens[1].isdigit():
                top = int(tokens[1])
            gn = engine.calcular_god_nodes(top_n=top)
            print(f"🏛️ PILARES ESTRUCTURALES DEL DERECHO (God Nodes - PageRank Top {top}):")
            print("═"*65)
            print("Instituciones Dogmáticas Rectoras:")
            for idx, it in enumerate(gn["god_instituciones"], 1):
                print(f"  {idx:2d}. {it['label']:<35} | PR: {it['pagerank']:.5f} | Conexiones: {it['grado_conexiones']}")
            print("\nNormas Positivas Centrales (BCN):")
            for idx, it in enumerate(gn["god_normas"], 1):
                print(f"  {idx:2d}. {it['label']:<35} | PR: {it['pagerank']:.5f} | Conexiones: {it['grado_conexiones']}")
            print()

        elif tokens and tokens[0] == "stats":
            print("📊 ESTADÍSTICAS TOPOLÓGICAS DE LEGALGRAPHIFY:")
            print("═"*65)
            print(f"  • Nodos Totales:   {engine.graph.number_of_nodes()}")
            print(f"  • Aristas Totales: {engine.graph.number_of_edges()}\n")

        elif tokens and tokens[0] == "mermaid":
            q_m = " ".join(tokens[1:]) if len(tokens) > 1 else "simulacion"
            print(engine.exportar_subgrafo_mermaid(q_m) + "\n")

        else:
            q = " ".join(tokens) if tokens else "simulacion"
            ahorro = engine.calcular_ahorro_tokens(q)
            if not ahorro.get("encontrado", True):
                print(f"⚠️ {ahorro.get('mensaje')}")
            else:
                m = ahorro["metricas"]
                print(f"🧠 SUBGRAFO JURÍDICO HIPER-DENSO (LegalGraphify): '{q}'")
                print("═"*65)
                print(ahorro["ficha_optimizada"])
                print("═"*65)
                print("⚡ MÉTRICAS DE OPTIMIZACIÓN DE CONTEXTO:")
                print(f"  • Tokens Texto Completo (Capítulo crudo): ~{m['tokens_texto_completo']} tokens")
                print(f"  • Tokens Subgrafo Sintético:             ~{m['tokens_subgrafo']} tokens")
                print(f"  • Tokens Ahorrados:                      ~{m['tokens_ahorrados']} tokens")
                print(f"  • 🚀 Reducción de Tokens:                {m['porcentaje_ahorro']}% ({m['factor_reduccion']})\n")

    elif args.comando in ("agent", "agents"):
        from agents_runtime import agent_runtime
        tokens = args.query if args.query else []
        subcmd = tokens[0].lower() if tokens else "list"

        if subcmd == "list":
            agentes = agent_runtime.list_agents()
            print_banner()
            print(f"🤖 CATÁLOGO DE AGENTES JURÍDICOS ESPECIALIZADOS ({len(agentes)} AGENTES)\n" + "═"*78)
            for a in agentes:
                print(f"• {a['name']:<24} | {a['display_name']}")
                print(f"  Herramientas ({a['tools_count']}): {', '.join(a['tools'][:6])}...")
                print(f"  Misión: {a['description'][:100]}...\n")

        elif subcmd == "run":
            if len(tokens) < 2:
                print("⚠️ Uso: openlegal agent run <nombre_agente> \"<misión o consulta>\"")
            else:
                ag_name = tokens[1]
                tarea = " ".join(tokens[2:]) if len(tokens) > 2 else "Ejecutar dictamen general"
                print_banner()
                print(f"⏳ Ejecutando agente '{ag_name}'...")
                res = agent_runtime.run_agent(ag_name, tarea, mode="deterministic")
                print("\n" + res.format_cli_summary())

        elif subcmd == "export":
            dest = tokens[1] if len(tokens) > 1 else "."
            res_exp = agent_runtime.export_subagents_config(dest)
            print(f"✅ Se exportaron {len(res_exp)} configuraciones de subagentes para Claude Code y Cursor en '{dest}'.")

        elif subcmd == "chat":
            ag_name = tokens[1] if len(tokens) > 1 else "litigios"
            ag = agent_runtime.get_agent(ag_name)
            if not ag:
                print(f"⚠️ Agente '{ag_name}' no encontrado. Ejecuta 'openlegal agent list' para ver disponibles.")
            else:
                print_banner()
                print(f"🤖 SESIÓN INTERACTIVA CON: {ag.display_name.upper()} ({ag.name})")
                print("Escribe tus consultas o 'salir' para terminar.\n" + "-"*78)
                while True:
                    q_user = input("\n⚖️ Consulta > ").strip()
                    if q_user.lower() in ("salir", "exit", "q"):
                        break
                    if q_user:
                        r = ag.run(q_user, mode="auto")
                        print("\n" + r.output)
        else:
            # Si el primer token es el nombre de un agente directamente: openlegal agent litigios "mision"
            ag = agent_runtime.get_agent(subcmd)
            if ag:
                tarea = " ".join(tokens[1:]) if len(tokens) > 1 else "Ejecutar dictamen general"
                print_banner()
                print(f"⏳ Ejecutando agente '{ag.name}'...")
                res = ag.run(tarea, mode="deterministic")
                print("\n" + res.format_cli_summary())
            else:
                print(f"⚠️ Comando o agente '{subcmd}' desconocido. Usa: openlegal agent [list|run|chat|export]")

    elif args.comando == "ci":
        from scripts.ci_watchdog import vigilar_y_reparar
        commit = args.query[0] if args.query else None
        rc = vigilar_y_reparar(commit_sha=commit, watch=True, auto_fix=True)
        sys.exit(rc)

    else:
        menu_interactivo(parser)


if __name__ == "__main__":
    main()
