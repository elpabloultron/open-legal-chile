"""
Open Legal Chile — Aplicación de Escritorio Nativa (Desktop App)
Inicia el servidor en segundo plano y abre una ventana nativa de escritorio (GUI)
utilizando Microsoft Edge WebView2 / pywebview.
"""

import os
import sys
import time
import threading
from http.server import HTTPServer
from server import OpenLegalHTTPHandler, PORT, WEB_DIR

def run_background_server():
    """Inicia el servidor HTTP en un hilo secundario."""
    os.makedirs(WEB_DIR, exist_ok=True)
    server_address = ("", PORT)
    try:
        httpd = HTTPServer(server_address, OpenLegalHTTPHandler)
        httpd.serve_forever()
    except Exception as e:
        print(f"Servidor HTTP en segundo plano: {e}")

def main():
    # 1. Iniciar servidor en segundo plano
    server_thread = threading.Thread(target=run_background_server, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    app_url = f"http://localhost:{PORT}"

    # 2. Intentar abrir como ventana de escritorio nativa con pywebview
    try:
        import webview
        print(f"🚀 Iniciando ventana nativa de escritorio para Open Legal Chile ({app_url})...")
        window = webview.create_window(
            title="⚖️ Open Legal Chile — Suite de Inteligencia Jurídica",
            url=app_url,
            width=1280,
            height=820,
            min_size=(900, 600),
            background_color="#0B0F19",
            resizable=True
        )
        webview.start()
    except ImportError:
        # Si no está instalado pywebview, abrir en navegador
        import webbrowser
        print(f"🌐 Abriendo Open Legal Chile en navegador: {app_url}")
        webbrowser.open(app_url)
        # Mantener el proceso vivo
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nCerrando Open Legal Chile.")

if __name__ == "__main__":
    main()
