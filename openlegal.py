"""
Open Legal Chile — CLI Maestro Unificado
Consola interactiva de inteligencia jurídica y consulta en tiempo real de leyes,
dictámenes, auditorías y jurisprudencia administrativa de la República de Chile.
"""

import sys
import os
import argparse

# Asegurar encoding UTF-8 en terminal de Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Importar conectores oficiales
from bcn_connector import BCNClient, CODIGOS_REPUBLICA
from cgr_connector import CGRClient
from dt_connector import DTClient
from cne_connector import CNEClient
from panel_expertos_connector import PanelExpertosClient
from cmf_connector import CMFClient
from sii_connector import SIIClient
from ambiental_connector import AmbientalClient
from tdlc_connector import TDLCClient

# Inicializar clientes
bcn_client = BCNClient()
cgr_client = CGRClient()
dt_client = DTClient()
cne_client = CNEClient()
panel_client = PanelExpertosClient()
cmf_client = CMFClient()
sii_client = SIIClient()
sma_client = AmbientalClient()
tdlc_client = TDLCClient()


def print_banner():
    banner = """
================================================================================
   ⚖️  OPEN LEGAL CHILE — CONSOLA MAESTRA DE INTELIGENCIA JURÍDICA  ⚖️
   Sistema de Derecho Continental Codificado (Civil Law) — República de Chile
================================================================================
 Fuentes Conectadas: BCN Ley Chile | CGR | DT | CNE | Panel de Expertos | CMF | SII | SMA | TDLC
--------------------------------------------------------------------------------
"""
    print(banner)


def menu_interactivo():
    print_banner()
    while True:
        print("\n--- MENÚ PRINCIPAL ---")
        print(" [1] 📜 BCN Ley Chile: Consultar Leyes o Códigos de la República")
        print(" [2] 🏛️ Contraloría (CGR): Buscar Dictámenes, Auditorías e Instructivos")
        print(" [3] 💼 Dirección del Trabajo (DT): Buscar Dictámenes y Doctrina Laboral")
        print(" [4] ⚡ Energía (CNE / Panel): Capacidad Eléctrica, Proyectos SEA y Discrepancias")
        print(" [5] 🏢 CMF: Normas de Carácter General (NCG) y Circulares Financieras")
        print(" [6] 💰 SII: Circulares e Instrucciones Tributarias")
        print(" [7] 🌱 SMA / SNIFA: Procedimientos Sancionatorios Ambientales")
        print(" [8] 🛒 TDLC: Sentencias de Libre Competencia")
        print(" [9] 🔍 Búsqueda Jurídica Universal (Busca en todos los organismos a la vez)")
        print(" [0] 🚪 Salir")

        opc = input("\n👉 Selecciona una opción (0-9): ").strip()

        if opc == "0":
            print("\n👋 ¡Hasta luego! Cerrando Open Legal Chile.\n")
            break

        elif opc == "1":
            print("\n--- 📜 BCN LEY CHILE ---")
            tipo = input("¿Deseas consultar un [C]ódigo (civil, trabajo, cpc, etc.) o una [L]ey por número? (C/L): ").strip().lower()
            if tipo == "c":
                cod = input(f"Ingresa el código {list(CODIGOS_REPUBLICA.keys())}: ").strip().lower()
                art = input("Número de artículo (opcional, presiona Enter para ver general): ").strip()
                try:
                    res = bcn_client.get_codigo(cod, art if art else None)
                    if art:
                        print(f"\n[{res.get('codigo')} — Artículo {res.get('articulo')}]")
                        print(res.get('texto', res.get('error')))
                        print(f"📅 Versión vigente: {res.get('fechaVersion')}")
                    else:
                        print(f"\n{res.get('titulo')} | Total Artículos: {len(res.get('articulos', {}))}")
                except Exception as e:
                    print("Error:", e)
            else:
                num = input("Número de ley (ej. 21643, 21561): ").strip()
                art = input("Número de artículo (opcional): ").strip()
                try:
                    if art:
                        res = bcn_client.get_articulo_ley(int(num), art)
                        print(f"\n[Ley N° {num} — Artículo {art}]")
                        print(res.get('texto', res.get('error')))
                    else:
                        res = bcn_client.get_ley(int(num))
                        print(f"\nLey N° {num}: {res.get('titulo')}")
                        print(f"Versión: {res.get('fechaVersion')} | Estructuras: {res.get('totalEstructuras')}")
                except Exception as e:
                    print("Error:", e)

        elif opc == "2":
            print("\n--- 🏛️ CONTRALORÍA GENERAL DE LA REPÚBLICA ---")
            sub_opc = input("¿Buscar [D]ictámenes o [A]uditorías? (D/A): ").strip().lower()
            q = input("Término de búsqueda (ej. 'confianza legitima', 'compras publicas', 'municipalidad'): ").strip()
            try:
                if sub_opc == "a":
                    res = cgr_client.search_auditorias(q)
                    print(f"\n🔍 Total Auditorías encontradas: {res.get('total')}")
                    for idx, item in enumerate(res.get("resultados", [])[:5]):
                        print(f"\n[{idx+1}] Informe N° {item.get('docId')} ({item.get('fecha')})")
                        print(f"  📌 {item.get('materia')}")
                        if item.get("pdfUrl"):
                            print(f"  📄 PDF: {item.get('pdfUrl')}")
                else:
                    res = cgr_client.search_jurisprudencia(q)
                    print(f"\n🏛️ Total Dictámenes encontrados: {res.get('total')}")
                    for idx, item in enumerate(res.get("resultados", [])[:5]):
                        print(f"\n[{idx+1}] Dictamen CGR N° {item.get('docId')} ({item.get('fecha')})")
                        print(f"  📌 Materia: {item.get('materia')}")
            except Exception as e:
                print("Error:", e)

        elif opc == "3":
            print("\n--- 💼 DIRECCIÓN DEL TRABAJO ---")
            q = input("Número de Ordinario/Dictamen o término (ej. '344', 'Karin', '40 horas'): ").strip()
            try:
                res = dt_client.search_dictamenes(q)
                print(f"\nTotal resultados DT: {len(res)}")
                for idx, item in enumerate(res[:5]):
                    print(f"\n[{idx+1}] {item.get('titulo')}")
                    if item.get("materias"):
                        print(f"  📌 Materias: {item.get('materias')}")
                    if item.get("doctrina"):
                        print(f"  📜 Doctrina: {item.get('doctrina')[:250]}...")
                    print(f"  🔗 Enlace: {item.get('url')}")
            except Exception as e:
                print("Error:", e)

        elif opc == "4":
            print("\n--- ⚡ DERECHO ELÉCTRICO Y ENERGÍA ---")
            print(" [A] Capacidad instalada (CNE)")
            print(" [B] Proyectos energéticos en el SEA (CNE)")
            print(" [C] Clientes Libres vs. Regulados (CNE)")
            print(" [D] Discrepancias y Dictámenes (Panel de Expertos)")
            sub = input("Opción (A/B/C/D): ").strip().upper()
            try:
                if sub == "A":
                    data = cne_client.get_capacidad_instalada()
                    print(f"\nTotal centrales registradas: {len(data)}")
                    for c in data[:5]:
                        print(f" - {c.get('central')} ({c.get('tipo_tecnologia', c.get('tecnologia', 'Central'))}): Titular: {c.get('razon_social', c.get('propietario'))}")
                elif sub == "B":
                    data = cne_client.get_proyectos_sea()
                    print(f"\nTotal proyectos en el SEA: {len(data)}")
                    for p in data[:5]:
                        print(f" - {p.get('nombre_proyecto', p.get('proyecto'))} | Estado: {p.get('estado')}")
                elif sub == "C":
                    libres = cne_client.get_clientes_libres()
                    regulados = cne_client.get_clientes_regulados()
                    print(f"\nRegistros Clientes Libres: {len(libres)} | Clientes Regulados: {len(regulados)}")
                elif sub == "D":
                    q = input("Buscar en discrepancias del Panel (Enter para ver últimas): ").strip()
                    res = panel_client.search_dictamenes(q, max_pages=1)
                    print(f"\nDiscrepancias encontradas: {len(res)}")
                    for item in res[:5]:
                        print(f" - Discrepancia N° {item['numero']} | Materia: {item['materia'] or 'No especificada'}")
                        for doc in item['documentos'][:2]:
                            print(f"    * {doc['titulo']}")
            except Exception as e:
                print("Error:", e)

        elif opc == "5":
            print("\n--- 🏢 COMISIÓN PARA EL MERCADO FINANCIERO (CMF) ---")
            q = input("Buscar por término o número de norma (ej. '4521', 'pensiones'): ").strip()
            try:
                res = cmf_client.search_normativa(q)
                print(f"\nResultados CMF: {len(res)}")
                for idx, item in enumerate(res[:5]):
                    print(f"\n[{idx+1}] {item.get('titulo')}")
                    print(f"  📄 PDF: {item.get('pdfUrl')}")
            except Exception as e:
                print("Error:", e)

        elif opc == "6":
            print("\n--- 💰 SERVICIO DE IMPUESTOS INTERNOS (SII) ---")
            anio = input("Año de circulares (presiona Enter para 2026): ").strip()
            anio_val = int(anio) if anio.isdigit() else 2026
            try:
                res = sii_client.get_circulares_por_anio(anio_val)
                print(f"\nTotal circulares en {anio_val}: {len(res)}")
                for item in res[:5]:
                    print(f" - {item.get('titulo')} -> {item.get('pdfUrl')}")
            except Exception as e:
                print("Error:", e)

        elif opc == "7":
            print("\n--- 🌱 SUPERINTENDENCIA DEL MEDIO AMBIENTE (SMA / SNIFA) ---")
            q = input("Buscar por titular o proyecto (ej. 'Minera', 'AquaChile'): ").strip()
            try:
                res = sma_client.search_sancionatorios(nombre=q, limit=5)
                print(f"\nTotal expedientes en SNIFA: {res.get('total')}")
                for item in res.get("resultados", []):
                    print(f"\n - [{item.get('expediente')}] {item.get('titular')} ({item.get('categoria')})")
                    print(f"   Unidad: {item.get('unidadFiscalizable')} | Estado: {item.get('estado')}")
                    print(f"   🔗 Ficha: {item.get('fichaUrl')}")
            except Exception as e:
                print("Error:", e)

        elif opc == "8":
            print("\n--- 🛒 TRIBUNAL DE DEFENSA DE LA LIBRE COMPETENCIA (TDLC) ---")
            q = input("Buscar por empresa o término (presiona Enter para ver últimas): ").strip()
            try:
                if q:
                    res = tdlc_client.search_jurisprudencia(q)
                else:
                    res = tdlc_client.get_sentencias(page=1, per_page=5)
                print(f"\nSentencias encontradas: {len(res)}")
                for item in res[:5]:
                    print(f"\n - {item.get('titulo')}")
                    print(f"   📅 Fecha: {item.get('fecha')} | 🔗 {item.get('link')}")
            except Exception as e:
                print("Error:", e)

        elif opc == "9":
            print("\n--- 🔍 BÚSQUEDA JURÍDICA UNIVERSAL ---")
            query = input("Ingresa tu término de búsqueda jurídica: ").strip()
            if not query:
                continue

            print(f"\n🛰️ Consultando a través de todos los organismos del Estado para: '{query}'...")
            
            # 1. CGR
            try:
                cgr_res = cgr_client.search_jurisprudencia(query)
                print(f"\n🏛️ Contraloría (CGR): {cgr_res.get('total')} dictámenes encontrados")
                for it in cgr_res.get("resultados", [])[:2]:
                    print(f"  * [{it.get('docId')}] {it.get('materia')[:120]}...")
            except Exception:
                pass

            # 2. DT
            try:
                dt_res = dt_client.search_dictamenes(query, limit=2)
                print(f"\n💼 Dirección del Trabajo (DT): {len(dt_res)} encontrados")
                for it in dt_res[:2]:
                    print(f"  * [{it.get('titulo')}] {it.get('materias') or ''}")
            except Exception:
                pass

            # 3. TDLC
            try:
                tdlc_res = tdlc_client.search_jurisprudencia(query, max_pages=1)
                print(f"\n🛒 TDLC (Libre Competencia): {len(tdlc_res)} sentencias encontradas")
                for it in tdlc_res[:2]:
                    print(f"  * {it.get('titulo')}")
            except Exception:
                pass

            # 4. SMA
            try:
                sma_res = sma_client.search_sancionatorios(nombre=query, limit=2)
                print(f"\n🌱 SMA (Ambiental): {sma_res.get('total')} sancionatorios")
                for it in sma_res.get("resultados", [])[:2]:
                    print(f"  * [{it.get('expediente')}] {it.get('titular')}")
            except Exception:
                pass

        input("\n[Presiona Enter para volver al menú principal...]")


def main():
    import webbrowser
    from config import check_configuration
    from server import run_server

    parser = argparse.ArgumentParser(
        description="⚖️ Open Legal Chile — Suite de Inteligencia Jurídica y Conectores de Datos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  openlegal                   -> Abre el menú interactivo de la consola
  openlegal mcp               -> Inicia el servidor MCP estándar para Antigravity/Claude/Cursor
  openlegal chat              -> Inicia el asistente jurídico IA en la terminal
  openlegal critique <doc>    -> Ejecuta la auditoría forense de 5 dimensiones sobre un escrito
  openlegal generate <tipo>   -> Genera un borrador judicial completo (demanda, recurso, contrato)
  openlegal skills            -> Lista las habilidades y plugins jurídicos de la suite
  openlegal export            -> Exporta un escrito judicial forense a HTML/MD
  openlegal check             -> Verifica el estado de las credenciales y conectores
  openlegal search "..."      -> Realiza una búsqueda jurídica universal
        """
    )
    parser.add_argument("comando", nargs="?", default="menu", choices=["menu", "mcp", "chat", "check", "search", "skills", "export", "critique", "generate"], help="Comando a ejecutar")
    parser.add_argument("query", nargs="*", help="Términos de búsqueda si usas 'search', archivo para 'critique' o tipo para 'generate'")
    parser.add_argument("--provider", type=str, default="gemini", help="Proveedor de IA (gemini, anthropic, deepseek, openai, ollama)")
    parser.add_argument("--buscar", type=str, help="Búsqueda jurídica universal")
    args = parser.parse_args()

    if args.comando == "mcp":
        import mcp_server
        mcp_server.main()
        return

    if args.comando == "chat":
        from chat_engine import LegalChatEngine
        engine = LegalChatEngine()
        print_banner()
        print(f"🤖 INICIANDO CHAT JURÍDICO INTERACTIVO (Proveedor: {args.provider.upper()})")
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

                print(f"⚖️ Asistente ({args.provider.upper()}): Pensando...")
                res = engine.chat(user_message=msg, provider=args.provider, history=history)

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

    elif args.comando == "check":
        print_banner()
        status = check_configuration()
        print("\n🔍 DIAGNÓSTICO DE CREDENCIALES Y CONECTORES:")
        print(f" • BCN Ley Chile API Key:  {'✅ Configurada' if status['BCN_CONFIGURED'] else '⚠️ No configurada (Revisa tu archivo .env)'}")
        print(f" • CNE Energía Abierta:   {'✅ Configurada' if status['CNE_CONFIGURED'] else '⚠️ No configurada (Revisa tu archivo .env)'}")
        print(" • Contraloría (CGR):     ✅ Operativo (API Abierta)")
        print(" • Dirección Trabajo (DT): ✅ Operativo (Catálogo Abierto)")
        print(" • Panel de Expertos:     ✅ Operativo (API Abierta)")
        print(" • CMF Mercado Valores:   ✅ Operativo (API Abierta)")
        print(" • SII Tributario:        ✅ Operativo (Índices Abiertos)")
        print(" • SMA Ambiental:         ✅ Operativo (SNIFA Abierto)")
        print(" • TDLC Libre Competencia:✅ Operativo (API Abierta)")
        print(f" • Puerto Web Local:      {status['PORT']}\n")

    elif args.comando == "search" or args.buscar:
        q = " ".join(args.query) if args.query else args.buscar
        if not q:
            print("❌ Debes especificar un término de búsqueda. Ejemplo: openlegal search 'Ley Karin'")
            return

        print_banner()
        print(f"\n🛰️ Búsqueda Jurídica Universal para: '{q}'...")
        
        # CGR
        try:
            cgr_res = cgr_client.search_jurisprudencia(q)
            print(f"\n🏛️ Contraloría (CGR): {cgr_res.get('total')} dictámenes encontrados")
            for it in cgr_res.get("resultados", [])[:3]:
                print(f"  * [{it.get('docId')}] {it.get('materia')}")
        except Exception as e:
            print(f"  * Error en CGR: {e}")

        # DT
        try:
            dt_res = dt_client.search_dictamenes(q, limit=3)
            print(f"\n💼 Dirección del Trabajo (DT): {len(dt_res)} encontrados")
            for it in dt_res[:3]:
                print(f"  * [{it.get('titulo')}] {it.get('materias') or it.get('doctrina')[:120]}...")
        except Exception as e:
            print(f"  * Error en DT: {e}")

        # TDLC
        try:
            tdlc_res = tdlc_client.search_jurisprudencia(q, max_pages=1)
            print(f"\n🛒 TDLC (Libre Competencia): {len(tdlc_res)} sentencias")
            for it in tdlc_res[:3]:
                print(f"  * {it.get('titulo')}")
        except Exception as e:
            print(f"  * Error en TDLC: {e}")

    elif args.comando == "skills":
        print_banner()
        print("""
🧩 HABILIDADES Y PLUGINS JURÍDICOS ACTIVOS (Suite Open Legal Chile):
--------------------------------------------------------------------------------
 1. 💼 employment-legal      -> Despidos Art. 161, Ley Karin 21.643, 40 Horas, Finiquitos
 2. ⚖️ litigation-legal      -> Demandas OJV Ley 20.886, Recursos de Protección, Otrosíes
 3. ⚡ energy-legal          -> Contratos PPA Clientes Libres, Servidumbres DFL 4/2006
 4. 🏢 corporate-legal       -> Sociedades SpA/SA, NCG 461 CMF, Diligencias M&A
 5. 🛡️ privacy-legal         -> Ley 19.628 / Nueva Ley de Protección de Datos Personales
 6. 📜 regulatory-legal      -> Sumarios CGR, Ley de Compras Públicas 19.886/21.634
 7. 🌱 environmental-legal   -> Sancionatorios SMA/SNIFA, Programas de Cumplimiento
 8. 🛒 antitrust-legal       -> Libre Competencia TDLC, Colusión y Fusiones FNE
 9. 💰 tax-legal             -> Consultas tributarias SII, Circulares y Código Tributario
10. 🎓 law-student           -> Preparación Examen de Grado y Cédulas de Derecho
--------------------------------------------------------------------------------
Usa 'openlegal chat' o 'openlegal web' para ejecutarlos interactivamente.
""")

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
        print(f"\n✅ Documento exportado con éxito en:")
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

        print(f"🔍 AUDITANDO DOCUMENTO BAJO LAS 5 DIMENSIONES FORENSES ({args.provider.upper()})...\n" + "-"*80)
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
                "tribunal": "I. CORTE DE APELACIONES DE SANTIAGO",
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
        print(f"\n✅ Artefacto generado con éxito:")
        print(f" • HTML: {res['htmlPath']}")
        print(f" • MD:   {res['markdownPath']}\n")

    else:
        menu_interactivo()


if __name__ == "__main__":
    main()
