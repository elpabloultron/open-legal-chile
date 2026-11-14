---
name: chilean-workspace-legal-flow
description: Orquestador de Flujo Jurídico entre Open Legal Chile y Google Workspace en Antigravity / Claude Code (inspirado en el codelab oficial google-workspace-mcp-antigravity): conecta el análisis forense chileno con Google Drive (expedientes), Google Docs (informes en derecho colaborativos), Google Sheets (matrices de riesgos, plazos y Baremo) y Google Calendar (hitos y audiencias judiciales).
---

# Habilidad: Flujo Jurídico Integrado con Google Workspace (chilean-workspace-legal-flow)

## 📌 Principios Rectores
1. **Interoperabilidad Soberana (Open Legal Chile + Google Workspace):** Inspirada en la arquitectura oficial de Google (`codelabs.developers.google.com/google-workspace-mcp-antigravity`), esta habilidad coordina las 88 herramientas jurídicas de Open Legal Chile con los plugins y habilidades de Google Workspace (`gdrive`, `gdocs`, `gsheets`, `gcalendar`, `gslides`) dentro de Google Antigravity y entornos MCP compatibles.
2. **Regla de Oro de Entrega Documental:** Todo informe en derecho, demanda o minuta generado localmente se compila primero en **Word (`.docx`) editable** con justificación completa, normas ortotipográficas RAE/ASALE (`« »`, `N.°`) e identidad institucional de Open Legal Chile; y, cuando el usuario trabaja en la nube de su estudio jurídico, se sincroniza o exporta hacia Google Docs (`gdocs`) o Google Drive (`gdrive`) preservando íntegramente las citas a pie de página.
3. **Cero Terminología de Common Law:** Queda estrictamente prohibido introducir en documentos colaborativos, hojas de cálculo de riesgos o eventos de calendario términos anglosajones como *discovery*, *punitive damages*, *at-will employment*, *subpoena*, *grand jury* o *summary judgment*. Utilizar siempre nomenclatura procesal y sustantiva chilena (*término probatorio*, *audiencia preparatoria*, *audiencia de juicio*, *plazo fatal de días hábiles CPC*, *indemnización por daño moral según Baremo PJUD*).
4. **Control Estricto de Plazos y Confidencialidad:** Antes de agendar un vencimiento en Google Calendar o registrar una contingencia en Google Sheets, el cómputo procesal debe verificarse con `vigilante_analizar_resolucion` conforme a los Arts. 59, 64 y 66 del Código de Procedimiento Civil.

## 📎 Citas y formato de entrega

- **Documentos** (informe en derecho, minuta ejecutiva, escrito judicial): se generan y entregan en **Word (.docx), no en PDF**, para que se puedan modificar (y opcionalmente se sincronizan en Google Docs cuando el usuario lo solicita); las citas van **a pie de página**, numeradas, con fuente · identificador · enlace.
- **Conversación**: la respuesta va primero y las citas van **al final**, después del texto.

En los dos casos: si no hay fuente identificable se dice «sin fuente verificable», y un dato que viene de varias fuentes se cita con todas.

## 📚 Formato de Citación Obligatorio
* Norma legal: `[BCN - Código de Procedimiento Civil, Art. <Número>]` o `[BCN - Código Civil, Art. <Número>]`
* Jurisprudencia CS y Baremo: `[CS - Rol N° <Número>-<Año>, Fecha: <D-M-A>]`
* Doctrina canónica: `[Doctrina - <Autor>, <Tratado>, Institución: <Nombre>]`
* Repositorio Hugging Face: `[Hugging Face - pablobenavidesj/doctrina-jurisprudencia-chile, Archivo: <Ruta>]`

## 🛠️ Herramientas MCP Disponibles
* **Núcleo Open Legal Chile:**
  - `caso_analizar` y `caso_ejecutar`: Analizan la carpeta del cliente y ejecutan el plan de búsqueda jurídica.
  - `consulta_maestra` y `cita_texto`: Obtienen la normativa BCN con texto literal, doctrina de Hugging Face y jurisprudencia.
  - `vigilante_analizar_resolucion`: Calcula los plazos fatales en días hábiles judiciales a partir de proveídos OJV.
  - `pjud_search_jurisprudencia`: Consulta fallos de la Corte Suprema, portales especializados y el Baremo Estadístico de Daño Moral (`coleccion="baremo"`).
  - `generar_documento` y `critique_documento`: Generan el documento Word (`.docx`) y ejecutan la auditoría forense (`5d` o `goldfish`).
* **Integración Google Workspace (cuando el usuario tiene activos `gdrive`, `gdocs`, `gsheets`, `gcalendar`):**
  - **Drive (`gdrive`):** Lectura de piezas del expediente almacenadas en carpetas compartidas del estudio y subida del `.docx` compilado.
  - **Docs (`gdocs`):** Creación o actualización de borradores colaborativos de informes en derecho y minutas para revisión simultánea de socios.
  - **Sheets (`gsheets`):** Construcción de matrices de contingencia judicial, liquidaciones laborales o comparativas en UF/CLP del Baremo de Daño Moral.
  - **Calendar (`gcalendar`):** Agendamiento de audiencias preparatorias, audiencias de juicio, vistas de la causa y recordatorios anticipados de plazos fatales.

---

## 🎨 Presentación y Lenguaje Claro (Legal Design)

Reglas de [`docs/legal_design.md`](../../../docs/legal_design.md) aplicadas a esta skill. No cambian el fondo jurídico: cambian cómo se entrega.

- **Quién lee:** socios de estudios jurídicos, gerentes legales (*general counsel*) y equipos de litigación que gestionan sus carpetas, escritos y calendarios de audiencias en Google Workspace.
- **Lenguaje claro:** el primer término técnico de cada flujo lleva su explicación clara entre paréntesis — `término probatorio ordinario (período de 20 días hábiles judiciales en el juicio ordinario civil durante el cual las partes deben rendir sus pruebas ante el tribunal, conforme al Art. 328 del CPC)`.
- **Salida (estructura):** resumen ejecutivo del flujo ejecutado + resultado del análisis jurídico tripartito (norma, doctrina y jurisprudencia) + enlace al archivo Word (`.docx`) local y artefactos sincronizados en Workspace (Doc, Sheet o evento de Calendar) + tabla de plazos fatales + citas verificables.
- **Citas:** las de *Formato de Citación Obligatorio*, conservadas íntegramente tanto en el `.docx` local como en el documento colaborativo.
- **Compuerta:** ⚖️ Compuerta de Revisión Jurídica: ningún documento sincronizado en Google Docs/Drive ni hito agendado en Google Calendar sustituye la revisión y firma del abogado patrocinante habilitado en la Oficina Judicial Virtual (OJV).

---

## 🔄 Workflow: Del Expediente en Drive al Informe en Derecho y Agenda Judicial

1. **Ingesta desde Carpeta Local o Google Drive:** Leer los antecedentes de la causa y ejecutar `caso_analizar` seguido de `consulta_maestra` para triangular legislación vigente (BCN), doctrina en Hugging Face y jurisprudencia aplicable.
2. **Cuantificación y Matriz en Hojas de Cálculo (`gsheets`):** Cuando el caso involucre indemnización de perjuicios o cobro laboral, consultar `pjud_search_jurisprudencia(query="daño moral", coleccion="baremo")` para obtener los percentiles P25, Mediana y P75 en UF/CLP y estructurar la tabla comparativa de exposición patrimonial.
3. **Redacción Forense, Auditoría Goldfish y Exportación Dual (`.docx` + `gdocs`):** Generar el informe en derecho o escrito con `generar_documento`, auditarlo con `critique_documento(modo="goldfish")` y entregar el archivo `.docx` editable.
4. **Agendamiento Procesal (`gcalendar`) y Compuerta:** Si existe una resolución notificada, calcular el vencimiento exacto con `vigilante_analizar_resolucion`, proponer el bloqueo de agenda con recordatorio previo e incluir la ⚖️ **Compuerta de Revisión Jurídica**.
