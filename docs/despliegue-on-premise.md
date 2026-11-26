# Despliegue On-Premise en Estudios Jurídicos y Gerencias Legales (Docker + Streamable HTTP)

Open Legal Chile v2.0.0 incorpora el transporte oficial **MCP Streamable HTTP** (`mcp_http_server.py`) junto con empaquetado **Docker / Docker Compose** endurecido para operar en la red interna (*VPC* o servidor privado) de un estudio jurídico, fiscalía corporativa o repartición pública con **Zero Data Leak**.

---

## 1. Arquitectura de Seguridad y Privacidad (Ley N.° 21.719 / Art. 247 CP)

* **Ejecución en servidor propio:** Ningún expediente ni escrito sale a servidores de Open Legal Chile.
* **Autenticación Bearer en tiempo constante:** Al exponer el servidor fuera de `127.0.0.1`, `OPENLEGAL_AUTH_TOKEN` es obligatorio (`hmac.compare_digest`); sin token, el arranque se bloquea automáticamente.
* **Protección contra DNS Rebinding:** Validación estricta de la cabecera `Origin` mediante `OPENLEGAL_ALLOWED_ORIGINS`.
* **Sistema de archivos de solo lectura:** El contenedor monta `/` en modo `read_only: true`, usuario no-root (`openlegal`, UID `10001`), `no-new-privileges:true` y persistencia acotada al volumen `openlegal_data`.
* **Registro de auditoría sin PII:** Los logs en `stderr` solo registran marca temporal, método HTTP, ruta, estado, IP y latencia en ms — jamás el texto de consultas ni tokens.

---

## 2. Arranque Rápido con Docker Compose

```bash
# 1. Definir token fuerte (mínimo 32 bytes aleatorios)
export OPENLEGAL_AUTH_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"

# 2. Construir y levantar el servicio privado en 127.0.0.1:8765
docker compose up -d --build

# 3. Verificar estado saludable
curl -sf http://127.0.0.1:8765/health
```

---

## 3. Arranque Directo sin Docker (Python Local)

```bash
# Modo local exclusivo en loopback (sin exponer a la red)
openlegal-mcp-http --profile router --port 8765

# O vía CLI unificado
openlegal serve-http --profile router --port 8765
```

Para publicar hacia clientes de la red interna detrás de un proxy inverso TLS (Nginx o Caddy):

```bash
export OPENLEGAL_AUTH_TOKEN="tu-token-corporativo-largo"
export OPENLEGAL_ALLOWED_ORIGINS="https://ia.tu-estudio.cl,http://localhost"
openlegal-mcp-http --host 0.0.0.0 --port 8765 --profile router
```

---

## 4. Endpoints del Protocolo

| Método y Ruta | Propósito | Cabeceras Relevantes |
| :--- | :--- | :--- |
| `POST /mcp` | Solicitudes JSON-RPC 2.0 (`initialize`, `tools/list`, `tools/call`, `resources/list`) | `Authorization: Bearer ...`, `Mcp-Session-Id`, `Accept: application/json` o `text/event-stream` |
| `GET /mcp` | Stream SSE inicial | `Authorization: Bearer ...`, `Accept: text/event-stream` |
| `DELETE /mcp` | Cierre explícito de sesión | `Authorization: Bearer ...`, `Mcp-Session-Id` |
| `GET /health` | Sonda de salud (`200 OK`) | Ninguna (no expone secretos) |

---

## 5. Instalación 1-Clic Desktop (`.mcpb`)

Para usuarios de **Claude Desktop** sin consola:

```bash
openlegal mcpb --out dist/open-legal-chile-2.0.0.mcpb
```

El bundle `.mcpb` resultante empaqueta `mcpb/manifest.json` (`manifest_version: "0.3"`), configura el perfil `router` por defecto y solicita el `HF_TOKEN` opcional de forma cifrada en el almacén de credenciales del sistema.
