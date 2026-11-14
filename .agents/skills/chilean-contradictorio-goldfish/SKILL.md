---
name: chilean-contradictorio-goldfish
description: Auditoría Contradictoria de Contexto Cero («Modelo Elephant-Goldfish», inspirado en google/elephant-goldfish-model) adaptada al litigio y dictámenes en Chile: separa al agente redactor con contexto («Elefante») de tres revisores de contexto cero («Pez Dorado»: Ministro Relator de Corte, Contraparte Litigante y Auditor de Citas BCN/HF) para eliminar el sesgo de confirmación.
---

# Habilidad: Auditoría Contradictoria de Contexto Cero — Modelo Elephant-Goldfish (chilean-contradictorio-goldfish)

## 📌 Principios Rectores
1. **Aislamiento Estructural de Contexto (Arquitectura *Elephant-Goldfish*):** Inspirada en la metodología `google/elephant-goldfish-model`, esta habilidad resuelve el principal defecto de los modelos de lenguaje en litigación: el **sesgo de confirmación**. Cuando el mismo agente que planificó y redactó una demanda o informe en derecho («Elefante», con toda la historia conversacional en memoria) revisa su propio borrador, tiende a justificar sus omisiones. Por ello, la auditoría se delega a un revisor de **contexto cero** («Pez Dorado» / *Goldfish*), que recibe **únicamente el documento final escrito**, exactamente igual que un juez o relator que abre el escrito por primera vez en la Oficina Judicial Virtual (OJV).
2. **Tríada de Revisores Contradictorios Chilenos:**
   - **Goldfish 1 — Ministro Relator (Corte de Apelaciones / Excma. Corte Suprema):** Examina admisibilidad formal, requisitos de los Arts. 254, 170, 767 y 772 del Código de Procedimiento Civil, Acta N.° 94-2015 en protección y cómputo de plazos fatales.
   - **Goldfish 2 — Abogado Litigante de la Contraparte:** Busca implacablemente excepciones dilatorias (Art. 303 CPC, especialmente ineptitud del libelo N.° 4), excepciones perentorias (prescripción, caducidad, falta de legitimación activa o pasiva) y orfandad probatoria frente al Art. 1698 del Código Civil.
   - **Goldfish 3 — Fiscalizador de Fuentes Positivas (BCN / Hugging Face):** Verifica que cada artículo citado contenga su transcripción literal entre comillas angulares (`« »`) y que no existan alucinaciones normativas o jurisprudenciales.
3. **Cero Terminología de Common Law:** Queda estrictamente prohibido el uso de términos anglosajones como *discovery*, *punitive damages*, *at-will employment*, *subpoena*, *grand jury* o *summary judgment*. Todo escrutinio procesal se rige por los códigos de la República de Chile.
4. **Iteración hasta Convergencia:** Si el revisor *Goldfish* detecta un hallazgo bloqueante (*FAIL*), el agente *Elefante* debe subsanar el escrito transcribiendo la norma faltante o corrigiendo el petitorio antes de entregarlo al usuario.

## 📎 Citas y formato de entrega

- **Documentos** (informe de auditoría contradictoria, pliego de observaciones de admisibilidad, escrito subsanado): se entregan en **Word (.docx), no en PDF**, para que se puedan modificar; las citas van **a pie de página**, numeradas, con fuente · identificador · enlace.
- **Conversación**: la respuesta va primero y las citas van **al final**, después del texto.

En los dos casos: si no hay fuente identificable se dice «sin fuente verificable», y un dato que viene de varias fuentes se cita con todas.

## 📚 Formato de Citación Obligatorio
* Norma procesal o sustantiva: `[BCN - Código de Procedimiento Civil, Art. <Número>]` o `[BCN - Código Civil, Art. 1698]`
* Doctrina canónica: `[Doctrina - <Autor>, <Tratado>, Institución: <Nombre>]`
* Repositorio Hugging Face: `[Hugging Face - pablobenavidesj/doctrina-jurisprudencia-chile, Archivo: <Ruta>]`
* Jurisprudencia CS: `[CS - Rol N° <Número>-<Año>, Fecha: <D-M-A>]`

## 🛠️ Herramientas MCP Disponibles
* `critique_documento`: Ejecuta con `modo="goldfish"` el dictamen contradictorio de contexto cero junto con la auditoría forense en 5 dimensiones sobre cualquier borrador judicial o informe en derecho.
* `cita_texto`: Recupera el texto positivo exacto desde BCN Ley Chile para subsanar cualquier cita que no haya sido transcrita literalmente en el borrador.
* `pjud_search_jurisprudencia`: Contrasta las tesis del borrador contra las líneas jurisprudenciales de la Corte Suprema y el Baremo Estadístico de Daño Moral.
* `generar_documento`: Recompila el escrito o informe en derecho ya subsanado en formato Word (`.docx`) con justificación completa y normas RAE/ASALE.

---

## 🎨 Presentación y Lenguaje Claro (Legal Design)

Reglas de [`docs/legal_design.md`](../../../docs/legal_design.md) aplicadas a esta skill. No cambian el fondo jurídico: cambian cómo se entrega.

- **Quién lee:** el socio litigante o abogado patrocinante que desea someter su demanda, contestación, recurso o informe en derecho a una prueba de ácido («red-team procesal») antes de firmarlo.
- **Lenguaje claro:** el primer término técnico de cada observación lleva su explicación directa entre paréntesis — `excepción de ineptitud del libelo (defensa procesal del Art. 303 N.° 4 del CPC mediante la cual el demandado pide paralizar el juicio porque la demanda es vaga, ininteligible o incumple los requisitos del Art. 254 del CPC)`.
- **Salida (estructura):** veredicto de admisibilidad (APROBADO PARA FIRMA / RECHAZADO — REQUIERE SUBSANACIÓN) + hallazgos bloqueantes (excepciones dilatorias, caducidad, citas sin texto) + observaciones sustantivas y probatorias (Art. 1698 CC) + observaciones formales OJV (Ley N.° 18.120 y Ley N.° 20.886) + propuesta de redacción subsanada + citas verificables.
- **Citas:** las de *Formato de Citación Obligatorio*, verificando cada artículo con `cita_texto`.
- **Compuerta:** ⚖️ Compuerta de Revisión Jurídica: la aprobación del revisor contradictorio no reemplaza el juicio profesional ni la responsabilidad del abogado patrocinante habilitado antes de ingresar el escrito en la Oficina Judicial Virtual (OJV).

---

## 🔄 Workflow: Ciclo de Revisión Contradictoria *Elephant → Goldfish*

1. **Fase Elefante (Planificación y Redacción con Contexto Completo):** El agente principal reúne los antecedentes con `consulta_maestra`, `bcn_get_codigo` y `pjud_search_jurisprudencia`, y redacta el borrador completo del escrito o informe en derecho.
2. **Fase Goldfish (Aislamiento y Ataque de Contexto Cero):**
   - Invocar `critique_documento(texto=borrador, modo="goldfish")` (y, cuando el harness soporte subagentes como Claude Code o Google Antigravity, invocar un subagente aislado pasándole **exclusivamente** el texto del borrador sin la historia previa del usuario).
   - Evaluar el texto bajo los tres lentes: Relator de Corte (admisibilidad), Contraparte (excepciones dilatorias y perentorias) y Auditor de Fuentes (transcripción literal de preceptos).
3. **Fase de Subsanación y Convergencia:** Corregir cada defecto bloqueante detectado, exportar la versión final en Word (`.docx`) con `generar_documento` e incluir la ⚖️ **Compuerta de Revisión Jurídica**.
