"""
Open Legal Chile — Servidor Web y API Local
Servidor HTTP nativo en Python (sin dependencias externas) que expone la API JSON
y sirve la interfaz web de LegalTech en http://localhost:8000.
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any

# Asegurar encoding UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Importar configuración y conectores oficiales
from config import PORT, check_configuration
from bcn_connector import BCNClient, CODIGOS_REPUBLICA
from cgr_connector import CGRClient
from dt_connector import DTClient
from cne_connector import CNEClient
from panel_expertos_connector import PanelExpertosClient
from cmf_connector import CMFClient
from sii_connector import SIIClient
from ambiental_connector import AmbientalClient
from tdlc_connector import TDLCClient
from chat_engine import LegalChatEngine
from exporters import LegalDocumentExporter

# Directorio de archivos estáticos de la web
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")

# Clientes
bcn_client = BCNClient()
cgr_client = CGRClient()
dt_client = DTClient()
cne_client = CNEClient()
panel_client = PanelExpertosClient()
cmf_client = CMFClient()
sii_client = SIIClient()
sma_client = AmbientalClient()
tdlc_client = TDLCClient()
chat_engine = LegalChatEngine()
exporter = LegalDocumentExporter()


class OpenLegalHTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def _send_json(self, data: Any, status: int = 200):
        """Envía una respuesta JSON estructurada."""
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/chat":
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw_body = self.rfile.read(length).decode("utf-8")
                payload = json.loads(raw_body)

                message = payload.get("message", "").strip()
                provider = payload.get("provider", "deepseek").lower()
                model = payload.get("model")
                api_key = payload.get("apiKey")
                history = payload.get("history", [])

                if not message:
                    self._send_json({"error": "El mensaje no puede estar vacío"}, 400)
                    return

                res = chat_engine.chat(
                    user_message=message,
                    provider=provider,
                    api_key=api_key,
                    model=model,
                    history=history
                )
                self._send_json(res)

            except Exception as e:
                self._send_json({"error": f"Error procesando chat: {str(e)}"}, 500)
            return

        elif path == "/api/verify-key":
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw_body = self.rfile.read(length).decode("utf-8")
                payload = json.loads(raw_body)

                provider = payload.get("provider", "gemini").lower()
                api_key = payload.get("apiKey", "").strip()
                model = payload.get("model")

                if not api_key:
                    self._send_json({"valid": False, "error": "Debes ingresar una clave o token."}, 400)
                    return

                res = chat_engine.verify_credentials(provider, api_key, model)
                self._send_json(res)
            except Exception as e:
                self._send_json({"valid": False, "error": f"Error al verificar: {str(e)}"}, 500)
            return

        elif path == "/api/export":
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw_body = self.rfile.read(length).decode("utf-8")
                payload = json.loads(raw_body)

                res = exporter.export_brief(
                    titulo_principal=payload.get("titulo_principal", "DEMANDA ORDINARIA DE INDEMNIZACIÓN DE PERJUICIOS"),
                    tribunal=payload.get("tribunal", "S.J.L. EN LO CIVIL DE SANTIAGO"),
                    presuma_data=payload.get("presuma", {}),
                    comparecencia=payload.get("comparecencia", ""),
                    hechos=payload.get("hechos", ""),
                    derecho=payload.get("derecho", ""),
                    peticiones=payload.get("peticiones", ""),
                    otrosies=payload.get("otrosies", [])
                )
                self._send_json(res)

            except Exception as e:
                self._send_json({"error": f"Error exportando escrito: {str(e)}"}, 500)
            return

        self._send_json({"error": "Ruta POST no encontrada"}, 404)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Rutas de API JSON
        if path.startswith("/api/"):
            try:
                if path == "/api/status":
                    self._send_json({
                        "app": "Open Legal Chile",
                        "version": "1.0.0",
                        "status": "online",
                        "config": check_configuration()
                    })

                elif path == "/api/buscar":
                    q = query.get("q", [""])[0]
                    if not q:
                        self._send_json({"error": "Debe especificar un término de búsqueda 'q'"}, 400)
                        return

                    resultados = {
                        "query": q,
                        "cgr": cgr_client.search_jurisprudencia(q).get("resultados", [])[:5],
                        "dt": dt_client.search_dictamenes(q, limit=5),
                        "tdlc": tdlc_client.search_jurisprudencia(q, max_pages=1)[:5],
                        "sma": sma_client.search_sancionatorios(nombre=q, limit=5).get("resultados", [])
                    }
                    self._send_json(resultados)

                elif path == "/api/cgr":
                    q = query.get("q", [""])[0]
                    source = query.get("source", ["dictamenes"])[0]
                    res = cgr_client.search_jurisprudencia(q, source=source)
                    self._send_json(res)

                elif path == "/api/dt":
                    q = query.get("q", [""])[0]
                    res = dt_client.search_dictamenes(q, limit=10)
                    self._send_json({"resultados": res})

                elif path == "/api/bcn/codigo":
                    cod = query.get("nombre", ["civil"])[0].lower()
                    art = query.get("art", [""])[0]
                    res = bcn_client.get_codigo(cod, art if art else None)
                    self._send_json(res)

                elif path == "/api/bcn/ley":
                    num = query.get("numero", ["21643"])[0]
                    art = query.get("art", [""])[0]
                    if art:
                        res = bcn_client.get_articulo_ley(int(num), art)
                    else:
                        res = bcn_client.get_ley(int(num))
                    self._send_json(res)

                elif path == "/api/cne/capacidad":
                    res = cne_client.get_capacidad_instalada()[:50]
                    self._send_json({"total": len(res), "datos": res})

                elif path == "/api/cne/proyectos":
                    res = cne_client.get_proyectos_sea()[:50]
                    self._send_json({"total": len(res), "datos": res})

                elif path == "/api/panel":
                    q = query.get("q", [""])[0]
                    res = panel_client.search_dictamenes(q, max_pages=1)
                    self._send_json({"total": len(res), "datos": res})

                elif path == "/api/cmf":
                    q = query.get("q", [""])[0]
                    res = cmf_client.search_normativa(q) if q else cmf_client.get_index_normas()[:20]
                    self._send_json({"total": len(res), "datos": res})

                elif path == "/api/sii":
                    anio = int(query.get("anio", ["2026"])[0])
                    res = sii_client.get_circulares_por_anio(anio)
                    self._send_json({"total": len(res), "anio": anio, "datos": res})

                elif path == "/api/sma":
                    nombre = query.get("nombre", [""])[0]
                    expediente = query.get("expediente", [""])[0]
                    res = sma_client.search_sancionatorios(nombre=nombre, expediente=expediente, limit=15)
                    self._send_json(res)

                elif path == "/api/tdlc":
                    q = query.get("q", [""])[0]
                    res = tdlc_client.search_jurisprudencia(q) if q else tdlc_client.get_sentencias(page=1, per_page=10)
                    self._send_json({"datos": res})

                else:
                    self._send_json({"error": "Endpoint de API no encontrado"}, 404)

            except Exception as e:
                self._send_json({"error": f"Error interno procesando solicitud: {str(e)}"}, 500)
            return

        # Para cualquier otra ruta, servir archivos estáticos (HTML/CSS/JS)
        super().do_GET()


def run_server(port: int = PORT):
    os.makedirs(WEB_DIR, exist_ok=True)
    server_address = ("", port)
    httpd = HTTPServer(server_address, OpenLegalHTTPHandler)
    print(f"""
================================================================================
   ⚖️  OPEN LEGAL CHILE — SERVIDOR WEB LEGALTECH ACTIVO  ⚖️
================================================================================
   🌐 Interfaz Web:  http://localhost:{port}
   🔌 API REST:      http://localhost:{port}/api/status
   📁 Carpeta Web:   {WEB_DIR}
--------------------------------------------------------------------------------
   Presiona Ctrl + C para detener el servidor.
================================================================================
""")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo servidor web Open Legal Chile...")
        httpd.server_close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Servidor Web LegalTech Open Legal Chile")
    parser.add_argument("--port", type=int, default=PORT, help="Puerto del servidor HTTP")
    args = parser.parse_args()
    run_server(args.port)
