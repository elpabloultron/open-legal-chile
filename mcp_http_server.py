"""Open Legal Chile — Servidor MCP Streamable HTTP (On-Premise, Zero Data Leak).

Implementado 100 % con la biblioteca estándar de Python (`http.server.ThreadingHTTPServer`)
para operar sin dependencias web externas en entornos locales, VPC o Docker Compose de
estudios jurídicos y departamentos legales.

Soporta en `/mcp`:
- `POST /mcp`: JSON-RPC 2.0 (solicitudes, lotes, notificaciones 202) en JSON o SSE (`text/event-stream`)
- `GET /mcp`: stream SSE inicial autenticado (`text/event-stream`)
- `DELETE /mcp`: revocación explícita de sesión `Mcp-Session-Id`
- `GET /health`: sonda de salud sin exposición de secretos

Controles de seguridad integrados:
- Bind por defecto en loopback (`127.0.0.1`); interfaces no loopback exigen `OPENLEGAL_AUTH_TOKEN`
  (salvo `--allow-insecure-no-auth` explícito).
- Validación `Bearer` en tiempo constante (`hmac.compare_digest`).
- Lista blanca de cabecera `Origin` (`OPENLEGAL_ALLOWED_ORIGINS`) para prevenir DNS rebinding.
- Límite de tamaño de payload (`<= 2 MiB`) y rate limiting por IP (`OPENLEGAL_HTTP_RPM`).
"""

from __future__ import annotations

import argparse
from collections import defaultdict, deque
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import os
import secrets
import sys
import threading
import time
from typing import Any, Deque, Dict, List, Optional, Tuple
from urllib.parse import urlparse

MAX_BODY_BYTES = 2 * 1024 * 1024
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_RPM = 120
SESSION_TTL_SECONDS = 8 * 3600


def es_host_loopback(host: str) -> bool:
    """Devuelve True si `host` apunta estrictamente a la interfaz local loopback."""
    limpio = (host or "").strip().lower().strip("[]")
    if limpio in ("localhost", "127.0.0.1", "::1"):
        return True
    try:
        return ipaddress.ip_address(limpio).is_loopback
    except ValueError:
        return False


def validar_configuracion_red(host: str, auth_token: str, allow_insecure: bool = False) -> None:
    """Impide exponer el servidor fuera de loopback sin token Bearer configurado."""
    if es_host_loopback(host) or auth_token.strip() or allow_insecure:
        return
    raise ValueError(
        "Seguridad Zero-Data-Leak: para escuchar fuera de loopback debe definir OPENLEGAL_AUTH_TOKEN "
        "o pasar explícitamente --allow-insecure-no-auth."
    )


def _patrones_origin(env_val: Optional[str]) -> List[str]:
    bruto = (env_val if env_val is not None else os.environ.get("OPENLEGAL_ALLOWED_ORIGINS", "")).strip()
    if not bruto:
        return ["http://localhost", "http://127.0.0.1", "http://[::1]", "https://localhost", "https://127.0.0.1"]
    return [p.strip().lower() for p in bruto.split(",") if p.strip()]


def origin_permitido(origin: Optional[str], patrones: List[str]) -> bool:
    """Valida cabecera `Origin` contra la allowlist para mitigar ataques DNS rebinding / CSRF."""
    if not origin:
        return True
    if "*" in patrones:
        return True
    parsed = urlparse(origin.strip())
    if not parsed.scheme or not parsed.netloc:
        return False
    host = (parsed.hostname or "").lower()
    base_sin_puerto = f"{parsed.scheme.lower()}://{host}"
    base_con_puerto = f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
    for pat in patrones:
        pat_l = pat.lower().rstrip("/")
        if pat_l.endswith(":*"):
            if base_sin_puerto == pat_l[:-2]:
                return True
        elif base_con_puerto == pat_l or base_sin_puerto == pat_l:
            return True
    return False


class _RateLimiter:
    """Limitador de tasa por ventana móvil de 60 segundos por dirección IP."""

    def __init__(self, max_rpm: int = DEFAULT_RPM) -> None:
        self.max_rpm = max(0, int(max_rpm))
        self._lock = threading.Lock()
        self._ventanas: Dict[str, Deque[float]] = defaultdict(deque)

    def permitir(self, ip: str, ahora: Optional[float] = None) -> Tuple[bool, int]:
        if self.max_rpm <= 0:
            return True, 0
        ts = ahora if ahora is not None else time.monotonic()
        corte = ts - 60.0
        with self._lock:
            q = self._ventanas[ip]
            while q and q[0] < corte:
                q.popleft()
            if len(q) >= self.max_rpm:
                retry = max(1, int(60.0 - (ts - q[0])))
                return False, retry
            q.append(ts)
            return True, 0


class _SessionStore:
    """Registro thread-safe de sesiones MCP HTTP identificadas por `Mcp-Session-Id`."""

    def __init__(self, ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._sesiones: Dict[str, float] = {}

    def crear(self) -> str:
        sid = secrets.token_urlsafe(24)
        ahora = time.monotonic()
        with self._lock:
            self._purgar_locked(ahora)
            self._sesiones[sid] = ahora
        return sid

    def validar_y_refrescar(self, sid: str) -> bool:
        ahora = time.monotonic()
        with self._lock:
            self._purgar_locked(ahora)
            if sid not in self._sesiones:
                return False
            self._sesiones[sid] = ahora
            return True

    def cerrar(self, sid: str) -> bool:
        with self._lock:
            return self._sesiones.pop(sid, None) is not None

    def total_activas(self) -> int:
        ahora = time.monotonic()
        with self._lock:
            self._purgar_locked(ahora)
            return len(self._sesiones)

    def _purgar_locked(self, ahora: float) -> None:
        expiradas = [k for k, ts in self._sesiones.items() if ahora - ts > self.ttl_seconds]
        for k in expiradas:
            self._sesiones.pop(k, None)


def _es_peticion_initialize(payload: Any) -> bool:
    if isinstance(payload, dict):
        return payload.get("method") == "initialize"
    if isinstance(payload, list):
        return any(isinstance(item, dict) and item.get("method") == "initialize" for item in payload)
    return False


class OpenLegalHTTPServer(ThreadingHTTPServer):
    """Servidor HTTP multi-hilo con estado MCP compartido y controles Zero-Data-Leak."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: Tuple[str, int],
        *,
        tools_to_expose: List[Dict[str, Any]],
        profile_name: str,
        version: str,
        auth_token: str = "",
        allowed_origins: Optional[List[str]] = None,
        max_rpm: int = DEFAULT_RPM,
        max_body_bytes: int = MAX_BODY_BYTES,
    ) -> None:
        self.tools_to_expose = tools_to_expose
        self.profile_name = profile_name
        self.version = version
        self.auth_token = auth_token
        self.allowed_origins = allowed_origins if allowed_origins is not None else _patrones_origin(None)
        self.rate_limiter = _RateLimiter(max_rpm=max_rpm)
        self.session_store = _SessionStore()
        self.max_body_bytes = max_body_bytes
        super().__init__(server_address, OpenLegalMCPHTTPHandler)


class OpenLegalMCPHTTPHandler(BaseHTTPRequestHandler):
    """Manejador de peticiones Streamable HTTP para `/mcp` y sonda `/health`."""

    protocol_version = "HTTP/1.1"
    server: OpenLegalHTTPServer

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        # Suprime el log estándar para emitir solo auditoría estructurada en stderr sin PII.
        return

    def _auditar(self, status: int, inicio: float, extra: str = "") -> None:
        ms = (time.perf_counter() - inicio) * 1000.0
        registro = {
            "ts": int(time.time()),
            "method": self.command,
            "path": urlparse(self.path).path,
            "status": status,
            "ip": self.client_address[0] if self.client_address else "-",
            "ms": round(ms, 2),
        }
        if extra:
            registro["note"] = extra
        sys.stderr.write(json.dumps(registro, ensure_ascii=False) + "\n")

    def _enviar_json(
        self,
        status: int,
        cuerpo: Any,
        headers_extra: Optional[Dict[str, str]] = None,
    ) -> None:
        datos = json.dumps(cuerpo, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "no-store")
        if headers_extra:
            for k, v in headers_extra.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(datos)

    def _enviar_vacio(self, status: int, headers_extra: Optional[Dict[str, str]] = None) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.send_header("Cache-Control", "no-store")
        if headers_extra:
            for k, v in headers_extra.items():
                self.send_header(k, v)
        self.end_headers()

    def _validar_seguridad_previa(self, inicio: float) -> bool:
        origin = self.headers.get("Origin")
        if not origin_permitido(origin, self.server.allowed_origins):
            self._enviar_json(403, {"error": "Origin no permitido en allowlist."})
            self._auditar(403, inicio, "origin_rejected")
            return False

        token_cfg = self.server.auth_token
        if token_cfg:
            auth = str(self.headers.get("Authorization") or "")
            prefijo = "Bearer "
            recibido = auth[len(prefijo):].strip() if auth.startswith(prefijo) else ""
            if not recibido or not hmac.compare_digest(recibido.encode("utf-8"), token_cfg.encode("utf-8")):
                self._enviar_json(
                    401,
                    {"error": "Autenticación Bearer requerida o inválida."},
                    headers_extra={"WWW-Authenticate": 'Bearer realm="open-legal-chile-mcp"'},
                )
                self._auditar(401, inicio, "unauthorized")
                return False

        ip = self.client_address[0] if self.client_address else "local"
        ok_rl, retry = self.server.rate_limiter.permitir(ip)
        if not ok_rl:
            self._enviar_json(
                429,
                {"error": "Límite de peticiones por minuto superado."},
                headers_extra={"Retry-After": str(retry)},
            )
            self._auditar(429, inicio, "rate_limited")
            return False
        return True

    def do_GET(self) -> None:
        inicio = time.perf_counter()
        ruta = urlparse(self.path).path
        if ruta == "/health":
            self._enviar_json(
                200,
                {
                    "status": "ok",
                    "service": "open-legal-chile-mcp-http",
                    "version": self.server.version,
                    "profile": self.server.profile_name,
                    "tools": len(self.server.tools_to_expose),
                    "auth_enabled": bool(self.server.auth_token),
                    "active_sessions": self.server.session_store.total_activas(),
                },
            )
            self._auditar(200, inicio)
            return

        if ruta == "/mcp":
            if not self._validar_seguridad_previa(inicio):
                return
            accept = str(self.headers.get("Accept") or "").lower()
            if "text/event-stream" not in accept:
                self._enviar_json(
                    405,
                    {"error": "GET /mcp requiere Accept: text/event-stream."},
                    headers_extra={"Allow": "GET, POST, DELETE"},
                )
                self._auditar(405, inicio)
                return
            evento = (
                f"event: ready\n"
                f"data: {json.dumps({'server': 'open-legal-chile-mcp', 'version': self.server.version})}\n\n"
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.send_header("Content-Length", str(len(evento)))
            self.end_headers()
            self.wfile.write(evento)
            self.wfile.flush()
            self._auditar(200, inicio, "sse_ready")
            return

        self._enviar_json(404, {"error": f"Ruta no encontrada: {ruta}"})
        self._auditar(404, inicio)

    def do_DELETE(self) -> None:
        inicio = time.perf_counter()
        ruta = urlparse(self.path).path
        if ruta != "/mcp":
            self._enviar_json(404, {"error": f"Ruta no encontrada: {ruta}"})
            self._auditar(404, inicio)
            return
        if not self._validar_seguridad_previa(inicio):
            return
        sid = str(self.headers.get("Mcp-Session-Id") or "").strip()
        if not sid or not self.server.session_store.cerrar(sid):
            self._enviar_json(404, {"error": "Sesión MCP desconocida o expirada."})
            self._auditar(404, inicio)
            return
        self._enviar_json(200, {"closed": True, "sessionId": sid})
        self._auditar(200, inicio, "session_closed")

    def do_POST(self) -> None:
        inicio = time.perf_counter()
        ruta = urlparse(self.path).path
        if ruta != "/mcp":
            self._enviar_json(404, {"error": f"Ruta no encontrada: {ruta}"})
            self._auditar(404, inicio)
            return
        if not self._validar_seguridad_previa(inicio):
            return

        raw_len = self.headers.get("Content-Length")
        try:
            length = int(raw_len or "0")
        except ValueError:
            self._enviar_json(400, {"error": "Cabecera Content-Length inválida."})
            self._auditar(400, inicio)
            return
        if length <= 0:
            self._enviar_json(400, {"error": "Se requiere cuerpo JSON-RPC 2.0 no vacío."})
            self._auditar(400, inicio)
            return
        if length > self.server.max_body_bytes:
            self._enviar_json(413, {"error": f"Payload excede límite máximo de {self.server.max_body_bytes} bytes."})
            self._auditar(413, inicio, "payload_too_large")
            return

        body_bytes = self.rfile.read(length)
        body_text = body_bytes.decode("utf-8", errors="replace")

        try:
            parsed = json.loads(body_text)
        except ValueError:
            from mcp_server import atender_linea

            resp_err = atender_linea(body_text, self.server.tools_to_expose)
            self._enviar_json(400, resp_err)
            self._auditar(400, inicio, "invalid_json")
            return

        sid = str(self.headers.get("Mcp-Session-Id") or "").strip()
        es_init = _es_peticion_initialize(parsed)
        if not es_init and sid and not self.server.session_store.validar_y_refrescar(sid):
            self._enviar_json(404, {"jsonrpc": "2.0", "id": None, "error": {"code": -32001, "message": "Sesión MCP expirada o inválida."}})
            self._auditar(404, inicio, "invalid_session")
            return

        from mcp_server import atender_linea

        resp = atender_linea(body_text, self.server.tools_to_expose)
        headers_extra: Dict[str, str] = {}
        if es_init and isinstance(resp, dict) and "result" in resp:
            headers_extra["Mcp-Session-Id"] = self.server.session_store.crear()

        if resp is None:
            self._enviar_vacio(202, headers_extra=headers_extra)
            self._auditar(202, inicio, "notification")
            return

        accept = str(self.headers.get("Accept") or "").lower()
        quiere_sse = "text/event-stream" in accept and "application/json" not in accept
        if quiere_sse:
            payload = (
                f"event: message\n"
                f"data: {json.dumps(resp, ensure_ascii=False, separators=(',', ':'))}\n\n"
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(payload)))
            for k, v in headers_extra.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(payload)
            self.wfile.flush()
            self._auditar(200, inicio, "post_sse")
            return

        self._enviar_json(200, resp, headers_extra=headers_extra)
        self._auditar(200, inicio)


def crear_servidor_http(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    *,
    profile: Optional[str] = None,
    auth_token: Optional[str] = None,
    allowed_origins: Optional[List[str]] = None,
    max_rpm: Optional[int] = None,
    allow_insecure: bool = False,
) -> OpenLegalHTTPServer:
    """Construye una instancia lista de `OpenLegalHTTPServer` con la configuración indicada."""
    from mcp_server import get_active_tools
    from update_checker import CURRENT_VERSION

    token = auth_token if auth_token is not None else os.environ.get("OPENLEGAL_AUTH_TOKEN", "")
    validar_configuracion_red(host, token, allow_insecure=allow_insecure)

    prof = (profile or os.environ.get("OPENLEGAL_PROFILE") or "router").strip()
    tools_activas = get_active_tools(prof)
    rpm = max_rpm if max_rpm is not None else int(os.environ.get("OPENLEGAL_HTTP_RPM", str(DEFAULT_RPM)) or DEFAULT_RPM)

    return OpenLegalHTTPServer(
        (host, int(port)),
        tools_to_expose=tools_activas,
        profile_name=prof,
        version=CURRENT_VERSION,
        auth_token=token,
        allowed_origins=allowed_origins,
        max_rpm=rpm,
    )


def main(argv: Optional[List[str]] = None) -> int:
    """Punto de entrada CLI `openlegal-mcp-http`."""
    parser = argparse.ArgumentParser(
        prog="openlegal-mcp-http",
        description="Servidor MCP Streamable HTTP on-premise de Open Legal Chile (Zero Data Leak).",
    )
    parser.add_argument("--host", default=os.environ.get("OPENLEGAL_HTTP_HOST", DEFAULT_HOST), help="Dirección de escucha (defecto 127.0.0.1)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("OPENLEGAL_HTTP_PORT", str(DEFAULT_PORT))), help="Puerto TCP (defecto 8765)")
    parser.add_argument("--profile", default=os.environ.get("OPENLEGAL_PROFILE", "router"), help="Perfil MCP (router, full, laboral, litigios, ...)")
    parser.add_argument("--allow-insecure-no-auth", action="store_true", help="Permite enlazar fuera de loopback sin OPENLEGAL_AUTH_TOKEN")
    args = parser.parse_args(argv)

    try:
        srv = crear_servidor_http(
            host=args.host,
            port=args.port,
            profile=args.profile,
            allow_insecure=args.allow_insecure_no_auth,
        )
    except ValueError as err:
        sys.stderr.write(f"ERROR: {err}\n")
        return 2

    sys.stderr.write(
        f"Open Legal Chile MCP HTTP v{srv.version} escuchando en http://{args.host}:{srv.server_address[1]}/mcp "
        f"(perfil={srv.profile_name}, herramientas={len(srv.tools_to_expose)}, auth={'on' if srv.auth_token else 'off'})\n"
    )
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
