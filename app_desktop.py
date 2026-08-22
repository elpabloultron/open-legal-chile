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

# Configurar encoding UTF-8 seguro para Windows cp1252
if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr is not None:
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from server import OpenLegalHTTPHandler, PORT, WEB_DIR

def run_background_server():
    """Inicia el servidor HTTP en un hilo secundario."""
    os.makedirs(WEB_DIR, exist_ok=True)
    server_address = ("", PORT)
    try:
        httpd = HTTPServer(server_address, OpenLegalHTTPHandler)
        httpd.serve_forever()
    except Exception as e:
        if sys.stdout:
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
        if sys.stdout:
            print(f"[Open Legal Chile] Iniciando ventana nativa de escritorio ({app_url})...")
        window = webview.create_window(
            title="Open Legal Chile — Suite de Inteligencia Jurídica",
            url=app_url,
            width=1280,
            height=820,
            min_size=(900, 600),
            background_color="#0B0F19",
            resizable=True
        )
        webview.start()
    except Exception as e:
        # Fallback a navegador
        import webbrowser
        if sys.stdout:
            print(f"[Open Legal Chile] Abriendo en navegador: {app_url} ({e})")
        webbrowser.open(app_url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
