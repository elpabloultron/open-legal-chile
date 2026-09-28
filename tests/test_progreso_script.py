"""Regresión: en modo script (`python mcp_server.py`, el modo del harness) el progreso sale igual.

Causa raíz que cubre: el server como script vive en `__main__`; si los despachadores hacen
`import mcp_server`, Python crea una SEGUNDA copia del módulo (medido: +222 ms de reimport) con
su propio `_TOKEN_PROGRESO` en None, y las notificaciones de progreso se pierden en silencio.
"""

import json
import pathlib
import subprocess
import sys
import threading

REPO = pathlib.Path(__file__).resolve().parents[1]


def _linea_con_limite(proceso, segundos: float = 120.0) -> str:
    """readline con límite de tiempo: si el server se cuelga, la prueba no se cuelga con él."""
    caja: dict = {}

    def _leer() -> None:
        try:
            caja["linea"] = proceso.stdout.readline()
        except Exception as error:  # noqa: BLE001 — se reporta como fallo de la prueba
            caja["error"] = error

    hilo = threading.Thread(target=_leer, daemon=True)
    hilo.start()
    hilo.join(segundos)
    if "linea" not in caja:
        raise AssertionError(f"el server no escribió nada en {segundos:.0f} s (error: {caja.get('error')})")
    return caja["linea"]


def test_el_progreso_sale_con_el_server_corriendo_como_script():
    proceso = subprocess.Popen([sys.executable, "mcp_server.py"], cwd=REPO,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                               encoding="utf-8")
    try:
        def enviar(objeto):
            proceso.stdin.write(json.dumps(objeto) + "\n")
            proceso.stdin.flush()

        enviar({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                           "clientInfo": {"name": "prueba-script", "version": "1"}}})
        respuesta = json.loads(_linea_con_limite(proceso))
        assert respuesta.get("id") == 1 and "result" in respuesta

        enviar({"jsonrpc": "2.0", "method": "notifications/initialized"})
        enviar({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "consulta_maestra",
                           "arguments": {"consulta": "humedales", "max_fuentes": 1},
                           "_meta": {"progressToken": "prueba-1"}}})

        notificacion = json.loads(_linea_con_limite(proceso))
        assert notificacion.get("method") == "notifications/progress", notificacion
        assert notificacion["params"]["progressToken"] == "prueba-1"
        assert notificacion["params"]["progress"] == 0
    finally:
        proceso.terminate()
        try:
            proceso.wait(timeout=10)
        except subprocess.TimeoutExpired:  # pragma: no cover — se fuerza la salida
            proceso.kill()
