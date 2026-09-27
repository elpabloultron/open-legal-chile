# ⚖️ Integración Legal CRM + Harness + Open Legal Chile

> **Documento de Especificación y Diseño de Arquitectura**  
> **Proyecto:** Open Legal Chile (`open-legal-chile`)  
> **Fecha:** Septiembre 2026  

---

## 1. Visión General

Conectar la suite de inteligencia jurídica **Open Legal Chile** (Mesa de entrada, conectores PJUD, cálculo de plazos fatales, doctrina y jurisprudencia) con cualquier **Harness de IA** (Google Antigravity, Claude Code, Codex, Hermes, OpenCode, etc.) y un **CRM Legal Web**.

El objetivo es automatizar el ciclo completo de tramitación judicial:
1. El abogado o harness analiza un expediente, escrito o proveído judicial del PJUD.
2. La suite Open Legal Chile (`case_intake.py`, `docket_watcher.py`, `pjud_connector.py`) extrae automáticamente el perfil estructurado del caso: datos del cliente, tribunal, RIT/ROL, audiencias y plazos fatales.
3. Esta información se ingesta automáticamente en un **Legal CRM Web** dockerizado.
4. El CRM activa un **motor de alertas y notificaciones multicanal** (Telegram, WhatsApp, Correo electrónico, SMS) para el abogado o el estudio jurídico.

---

## 2. Diagrama de Flujo del Ecosistema

```mermaid
flowchart TD
    subgraph PJUD ["1. Fuentes Judiciales Chile"]
        Docs["Expedientes, Demandas, Resoluciones OJV / PJUD"]
    end

    subgraph HarnessSuite ["2. Harness + Open Legal Chile"]
        Harness["Harness de IA (Antigravity / Claude Code / OpenCode)"]
        OLSuite["Open Legal Chile (MCP / CLI)\n- caso_analizar & caso_ejecutar\n- docket_watcher (vigilar plazos)\n- pjud_connector (jurisprudencia)"]
        Extractor["Perfilador Forense del Caso (JSON)"]
    end

    subgraph CRM ["3. Legal CRM Web (Docker)"]
        API["API REST / Ingesta Webhook"]
        CRM_MCP["Servidor MCP del CRM"]
        DB[(Base de Datos: Causas, Clientes, Plazos)]
        Dashboard["Dashboard Web (Kanban, Calendario, Fichas 360°)"]
        Scheduler["Worker de Monitoreo & Notificaciones"]
    end

    subgraph Canales ["4. Alertas al Abogado / Estudio"]
        Tel["Telegram (Bot interactivo)"]
        WA["WhatsApp (Evolution API / Twilio)"]
        Mail["Correo Electrónico (Resend / SMTP)"]
        SMS["SMS (Twilio / AWS SNS)"]
    end

    Docs --> Harness
    Harness <--> OLSuite
    Harness --> Extractor
    Extractor -- "POST /api/cases/ingest o MCP tool" --> API
    API --> DB
    CRM_MCP <--> DB
    DB --> Dashboard
    DB --> Scheduler
    Scheduler --> Tel
    Scheduler --> WA
    Scheduler --> Mail
    Scheduler --> SMS
```

---

## 3. Esquema Estructurado de la Causa (JSON Schema)

La salida generada por Open Legal Chile hacia el CRM responde al siguiente estándar:

```json
{
  "causa_id": "C-1234-2026_2JCS",
  "identificacion": {
    "rit_rol": "C-1234-2026",
    "tribunal": "2° Juzgado Civil de Santiago",
    "caratulado": "GONZÁLEZ / BANCO DE CHILE",
    "materia": "Civil - Juicio Ordinario de Mayor Cuantía",
    "estado_procesal": "Término probatorio",
    "fecha_ingreso": "2026-03-15"
  },
  "partes": {
    "cliente": {
      "nombre": "Juan Pérez González",
      "rut": "12.345.678-9",
      "rol_procesal": "Demandante",
      "contacto": {
        "email": "juan.perez@email.cl",
        "telefono": "+56912345678"
      }
    },
    "contraparte": {
      "nombre": "Banco de Chile",
      "rut": "97.004.000-5",
      "rol_procesal": "Demandado",
      "abogado_patrocinante": "Estudio Jurídico Claro & Cía."
    }
  },
  "resumen_caso": {
    "sintesis": "Demanda de indemnización de perjuicios por responsabilidad contractual derivada de cobros indebidos y vulneración de la Ley del Consumidor.",
    "cuantia": "CLP 45.000.000",
    "ultima_resolucion": "Resolución de 24 de septiembre: Recibe la causa a prueba y fija puntos de prueba.",
    "estrategia_sugerida": "Acompañar lista de testigos dentro de los primeros 2 días del probatorio."
  },
  "hitos_criticos": [
    {
      "tipo": "audiencia",
      "subtipo": "audiencia_testimonial",
      "fecha": "2026-10-14T10:00:00-03:00",
      "sala": "Sala 1 / Vía Zoom",
      "enlace_audiencia": "https://pjud-zoom.cl/j/12345678",
      "descripcion": "Audiencia de recepción de prueba testimonial de la parte demandante."
    },
    {
      "tipo": "plazo_fatal",
      "subtipo": "lista_testigos",
      "fecha_vencimiento": "2026-09-29T23:59:59-03:00",
      "dias_restantes": 3,
      "urgencia": "alta",
      "descripcion": "Plazo fatal para presentar nómina de testigos y minuta de puntos de prueba."
    }
  ]
}
```

---

## 4. Componentes a Desarrollar

### 4.1. Conector en Open Legal Chile (`openlegal_crm_bridge.py`)
* Función o herramienta MCP que toma el resultado de `caso_analizar` / `caso_ejecutar` y lo despacha al CRM vía HTTP o MCP client.
* Integración con `openlegal vigilar` para monitoreo continuo de proveídos en la OJV.

### 4.2. Legal CRM Backend (FastAPI / Docker)
* **Endpoints:**
  * `POST /api/cases/ingest`: Ingesta y actualización idempotente de causas.
  * `GET /api/cases`: Listado y filtros por tribunal, abogado asignado y urgencia.
  * `GET /api/calendar`: Eventos unificados de audiencias y plazos fatales.
  * `POST /api/cases/{id}/notes`: Registro de bitácora y resoluciones.
* **Servidor MCP:** Expone herramientas para que Antigravity/Claude Code puedan consultar la base de datos de causas directamente.

### 4.3. Motor de Notificaciones (`notifications_worker.py`)
* Monitorea plazos y audiencias cada hora.
* Reglas de aviso:
  * **Audiencias:** Alertas en T-7d, T-48h, T-24h y a las 08:00 AM del día de la audiencia.
  * **Plazos fatales:** Alertas diarias escalonadas con nivel de urgencia semafórico (Verde > 5 días, Amarillo 3-5 días, Rojo < 48 hrs).
* Conectores:
  * **Telegram:** Mensajes con teclado inline (`[Ver Causa en CRM]`, `[Marcar Escrito Presentado]`).
  * **WhatsApp:** Mensajes formateados a través de Evolution API / Twilio.
  * **Email:** Resumen ejecutivo con formato formal para el estudio jurídico.
  * **SMS:** Recordatorio breve de alta prioridad.

### 4.4. Frontend Web (Dashboard)
* Vista Kanban de causas organizadas por etapa procesal (Ingreso, Discusión, Prueba, Sentencia, Recursos).
* Ficha 360° del cliente con todas sus causas asociadas.
* Calendario interactivo con plazos fatales y enlaces directos a las audiencias.

---

## 5. Dockerización del Sistema

Un archivo `docker-compose.yml` para levantar la infraestructura con un solo comando:

```yaml
version: '3.8'

services:
  legal-crm-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: legal_crm
      POSTGRES_USER: openlegal
      POSTGRES_PASSWORD: openlegal_secret
    volumes:
      - crm_db_data:/var/lib/postgresql/data
    networks:
      - legal_net

  legal-crm-backend:
    build: ./crm-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://openlegal:openlegal_secret@legal-crm-db:5432/legal_crm
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - RESEND_API_KEY=${RESEND_API_KEY}
    depends_on:
      - legal-crm-db
    networks:
      - legal_net

  legal-crm-web:
    build: ./crm-frontend
    ports:
      - "3000:3000"
    depends_on:
      - legal-crm-backend
    networks:
      - legal_net

volumes:
  crm_db_data:

networks:
  legal_net:
    driver: bridge
```
