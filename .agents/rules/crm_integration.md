---
description: Reglas y directrices para la integración entre Open Legal Chile, el Harness de agentes y el Legal CRM con alertas multicanal.
---

# Regla: Integración Legal CRM & Harness

Cuando se trabaje en la ingesta o análisis de causas judiciales orientadas a seguimiento:
1. **Extracción Estructurada:** Toda causa analizada por la Mesa de Entrada (`chilean-case-intake` o `case_intake.py`) debe producir el esquema definido en `docs/CRM_HARNESS_INTEGRATION.md`.
2. **Identificación Procesal Chilena:** Asegurar la captura estricta de:
   - Rol/RIT y Tribunal exacto.
   - Partes con su RUT verificado y rol procesal (Demandante, Demandado, Tercero).
   - Fechas de audiencias y enlaces de conexión virtual (Zoom PJUD).
   - Plazos fatales procesales calculados en días hábiles judiciales.
3. **Despacho al CRM:** El resultado debe ser compatible tanto con la API REST (`POST /api/cases/ingest`) como con el servidor MCP del CRM.
