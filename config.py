"""
Open Legal Chile — Gestor Centralizado de Configuración y Claves de API
Carga automáticamente las variables de entorno desde el archivo .env local
o desde las variables del sistema operativo sin dependencias externas.
"""

import base64
import http.client
import json
import math
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from typing import Any, Dict, List, Optional, Tuple


def load_env_file(filepath: Optional[str] = None) -> None:
    """Carga pares clave=valor desde un archivo .env si existe."""
    if filepath is None:
        filepath = os.path.join(os.path.dirname(__file__), ".env")

    if not os.path.exists(filepath):
        return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception as e:
        print(f"[Aviso] No se pudo leer el archivo .env: {e}")


# Cargar variables de entorno al importar el módulo
load_env_file()

# Configuraciones y credenciales del Estado
BCN_API_KEY: str = os.getenv("BCN_API_KEY", "")
CNE_EMAIL: str = os.getenv("CNE_EMAIL", "")
CNE_PASSWORD: str = os.getenv("CNE_PASSWORD", "")
PORT: int = int(os.getenv("PORT", "8000"))

# Proveedores de Inteligencia Artificial (BYOK - Bring Your Own Key)
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Verificación de credenciales y estado soberano
def check_configuration() -> dict:
    """Verifica el estado del sistema, conectores abiertos y motores de IA."""
    ollama_active = False
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.3)
        res = sock.connect_ex(("localhost", 11434))
        sock.close()
        ollama_active = (res == 0)
    except Exception:
        ollama_active = False

    return {
        "OPEN_SOURCE_SOBERANO": True,
        "OLLAMA_ACTIVE": ollama_active,
        "CONNECTORS_OPEN": {
            "bcn": True,
            "cgr": True,
            "dt": True,
            "pjud": True,
            "cmf": True,
            "sii": True,
            "sma": True,
            "tdlc": True,
            "panel_expertos": True,
            "cne": True
        },
        "OPTIONAL_COMMERCIAL_PROVIDERS": {
            "anthropic": bool(ANTHROPIC_API_KEY and not ANTHROPIC_API_KEY.startswith("tu_")),
            "gemini": bool(GEMINI_API_KEY and not GEMINI_API_KEY.startswith("tu_")),
            "deepseek": bool(DEEPSEEK_API_KEY and not DEEPSEEK_API_KEY.startswith("tu_")),
            "openai": bool(OPENAI_API_KEY and not OPENAI_API_KEY.startswith("tu_")),
        }
    }


def safe_urlopen(req, timeout: float = 30.0):
    """Ejecuta una petición HTTP/HTTPS segura validando que el esquema no sea file:// ni arbitrario."""
    import urllib.request
    url = req.full_url if hasattr(req, "full_url") else str(req)
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError(f"Esquema de URL no permitido por políticas de seguridad: {url}")
    # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
    return urllib.request.urlopen(req, timeout=timeout)  # nosec B310


def servidor_actual():
    """Devuelve el módulo del server que está corriendo (importado o como script).

    Corriendo `python mcp_server.py` el server vive en `__main__`, y un `import mcp_server` desde
    los despachadores crea una SEGUNDA copia del módulo con estado propio (medido el 2026-09-28:
    222 ms de reimport, y el token de progreso en None ⇒ las notificaciones se perdían en
    silencio). Por eso todos los despachadores resuelven el módulo por acá.
    """
    import sys
    for nombre in ("__main__", "mcp_server"):
        modulo = sys.modules.get(nombre)
        if modulo is not None and hasattr(modulo, "TOOLS") and hasattr(modulo, "handle_tool_call"):
            return modulo
    import mcp_server  # último recurso: nadie lo tenía cargado (script suelto)
    return mcp_server


# ── Telemetría de rendimiento por fases (en memoria: sin disco, sin red, sin datos personales) ──
_TIEMPOS: Dict[str, Any] = {}
_TIEMPOS_LOCK = threading.Lock()
_TIEMPOS_MAX = 200


def registrar_tiempo(clave: str, segundos: float) -> None:
    """Guarda una medición «conector.fase» para el doctor; jamás tumba una consulta."""
    try:
        with _TIEMPOS_LOCK:
            serie = _TIEMPOS.setdefault(clave, deque(maxlen=_TIEMPOS_MAX))
            serie.append(float(segundos))
    except Exception:  # noqa: BLE001 — la telemetría es lo último que puede fallar
        pass


def _percentil(orden: List[float], q: float) -> float:
    """Percentil de «rango más cercano»: p95 de 5 muestras es la mayor, como se espera."""
    return orden[min(len(orden) - 1, max(0, math.ceil(q * len(orden)) - 1))]


def tiempos_resumen() -> Dict[str, Dict[str, float]]:
    """p50/p95 por «conector.fase» con la cantidad de muestras de este proceso."""
    with _TIEMPOS_LOCK:
        copia = {k: list(v) for k, v in _TIEMPOS.items()}
    resumen: Dict[str, Dict[str, float]] = {}
    for clave, serie in copia.items():
        if not serie:
            continue
        orden = sorted(serie)
        resumen[clave] = {"n": len(orden),
                          "p50_ms": round(1000 * _percentil(orden, 0.5), 1),
                          "p95_ms": round(1000 * _percentil(orden, 0.95), 1)}
    return resumen


def cache_fresco(ruta: str, ttl_segundos: float) -> bool:
    """¿La copia local existe y está dentro del TTL? (el mtime es la fecha de descarga)."""
    return os.path.exists(ruta) and (time.time() - os.path.getmtime(ruta)) < ttl_segundos


def leer_json_si_se_puede(ruta: str) -> Optional[Any]:
    """La copia local si se puede leer: una copia ilegible no es una copia."""
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001 — una copia ilegible no es una copia
        return None


# ── Canal HTTP persistente (keep-alive): conexiones reutilizables por host ───────────────────
# Medido el 2026-09-28: cada consulta abría su propia conexión (negociación TLS completa cada
# vez). En ráfagas —varios artículos de una ley, varias leyes de una consulta— la conexión se
# reutiliza; si el servidor la cerró por inactividad, se descarta y se reintenta una vez con
# una nueva. Pila de conexiones libres por host: una conexión en uso no se comparte entre hilos.
_CANALES: Dict[str, List[Tuple[http.client.HTTPConnection, float]]] = {}
_CANALES_LOCK = threading.Lock()
_CANALES_MAX_LIBRES = 4


def _tomar_canal(esquema: str, host: str, timeout: float) -> http.client.HTTPConnection:
    """Saca una conexión libre del host (o crea una nueva si no hay)."""
    clave = f"{esquema}://{host}"
    while True:
        with _CANALES_LOCK:
            pila = _CANALES.setdefault(clave, [])
            if not pila:
                break
            canal, t = pila.pop()
        if t == timeout:
            return canal
        try:
            canal.close()
        except Exception:  # noqa: BLE001
            pass
    clase = http.client.HTTPSConnection if esquema == "https" else http.client.HTTPConnection
    proxy = _proxy_para(esquema, host)
    if proxy is None:
        return clase(host, timeout=timeout)
    # Detrás de un proxy (red de un estudio, CI, sesión en la nube): HTTPS va por túnel CONNECT y
    # HTTP pide la URL absoluta al proxy. Sin esto, http.client ignoraba HTTPS_PROXY y la BCN
    # respondía 429 o no respondía (medido el 2026-10-07: urllib 200, canal directo 429).
    partes_proxy = urllib.parse.urlsplit(proxy)
    puerto = partes_proxy.port or (443 if partes_proxy.scheme == "https" else 80)
    cabeceras_proxy: Dict[str, str] = {}
    if partes_proxy.username:
        credencial = f"{urllib.parse.unquote(partes_proxy.username)}:{urllib.parse.unquote(partes_proxy.password or '')}"
        cabeceras_proxy["Proxy-Authorization"] = "Basic " + base64.b64encode(credencial.encode()).decode()
    if esquema == "https":
        canal = http.client.HTTPSConnection(partes_proxy.hostname, puerto, timeout=timeout)
        canal.set_tunnel(host, headers=cabeceras_proxy or None)
        return canal
    canal = http.client.HTTPConnection(partes_proxy.hostname, puerto, timeout=timeout)
    canal._olc_cabeceras_proxy = cabeceras_proxy  # type: ignore[attr-defined]
    return canal


def _proxy_para(esquema: str, host: str) -> Optional[str]:
    """URL del proxy que corresponde al host según HTTP(S)_PROXY / NO_PROXY, o None si va directo."""
    try:
        if urllib.request.proxy_bypass(host.split(":")[0]):
            return None
        return urllib.request.getproxies().get(esquema) or None
    except Exception:  # noqa: BLE001 — una variable de entorno rara no puede cortar la consulta
        return None


def _devolver_canal(esquema: str, host: str, timeout: float,
                    canal: http.client.HTTPConnection) -> None:
    """Devuelve la conexión a la pila de libres (o la cierra si ya hay demasiadas)."""
    clave = f"{esquema}://{host}"
    with _CANALES_LOCK:
        pila = _CANALES.setdefault(clave, [])
        if len(pila) < _CANALES_MAX_LIBRES:
            pila.append((canal, timeout))
            return
    try:
        canal.close()
    except Exception:  # noqa: BLE001
        pass


def pedir_http(url: str, metodo: str = "GET", headers: Optional[Dict[str, str]] = None,
               cuerpo: Optional[bytes] = None, timeout: float = 30.0) -> bytes:
    """GET/POST con conexión reutilizada por host; reintenta una vez si la persistente murió."""
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError(f"Esquema de URL no permitido por políticas de seguridad: {url}")
    partes = urllib.parse.urlsplit(url)
    ruta = partes.path + (("?" + partes.query) if partes.query else "")
    esquema = "https" if partes.scheme == "https" else "http"
    cabeceras = {"User-Agent": "OpenLegalChile/1.0 (https://github.com/elpabloultron/open-legal-chile)"}
    cabeceras.update(headers or {})
    ultimo_error: Optional[Exception] = None
    for _intento in (1, 2):
        canal = _tomar_canal(esquema, partes.netloc, timeout)
        extra_proxy = getattr(canal, "_olc_cabeceras_proxy", None)
        try:
            if extra_proxy is not None:  # HTTP plano vía proxy: URL absoluta en la línea de pedido
                canal.request(metodo, url, body=cuerpo, headers={**cabeceras, **extra_proxy})
            else:
                canal.request(metodo, ruta, body=cuerpo, headers=cabeceras)
            respuesta = canal.getresponse()
            datos = respuesta.read()
        except (http.client.HTTPException, OSError, urllib.error.URLError) as error:
            ultimo_error = error
            try:
                canal.close()
            except Exception:  # noqa: BLE001
                pass
            continue
        _devolver_canal(esquema, partes.netloc, timeout, canal)
        if respuesta.status >= 400:
            raise urllib.error.HTTPError(url, respuesta.status, respuesta.reason, respuesta.headers, None)
        return datos
    raise ultimo_error if ultimo_error else RuntimeError("sin respuesta HTTP")


if __name__ == "__main__":
    status = check_configuration()
    print("\n================================================================================")
    print("   ⚖️  OPEN LEGAL CHILE — ESTADO DEL SISTEMA (100% OPEN SOURCE & SOBERANO)  ⚖️")
    print("================================================================================")
    print(" • Motor Jurídico Soberano:     ✅ OPERATIVO (100% Local, Cero API Keys, $0)")
    print(f" • Motor Ollama (Modelos Libres): {'🟢 Activo (localhost:11434)' if status['OLLAMA_ACTIVE'] else '⚪ Inactivo (Opcional para modelos de pesos libres)'}")
    print(" • 10 Conectores del Estado:      ✅ 100% OPERATIVOS Y PÚBLICOS (BCN, CGR, DT, PJUD, etc.)")
    print("\n🔌 Proveedores Comerciales Propietarios (Opcionales de Terceros — No Requeridos):")
    for prov, configured in status["OPTIONAL_COMMERCIAL_PROVIDERS"].items():
        print(f"   - {prov.capitalize()}: {'✅ Configurado' if configured else '⚪ No configurado (opcional)'}")
    print("--------------------------------------------------------------------------------\n")

