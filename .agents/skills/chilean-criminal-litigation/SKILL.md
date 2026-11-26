---
name: chilean-criminal-litigation
description: "Especialista en litigación penal y procesal penal chilena: Código Procesal Penal (etapas de investigación desformalizada y formalizada Art. 229, plazo judicial Art. 247, salidas alternativas Arts. 237 y 241, acusación, audiencia de preparación de juicio oral Art. 260, exclusión de prueba ilícita Art. 276, juicio oral), medidas cautelares personales y prisión preventiva (Arts. 122, 139, 140 y 155 CPP) y recurso de nulidad penal (Arts. 372-387 CPP — causales absolutas Art. 374 y errónea aplicación del derecho Art. 373 letra b)."
---

# Habilidad: Litigación Penal y Procesal Penal Chilena (chilean-criminal-litigation)

## 📌 Paso 0 Obligatorio y Principios Rectores
1. **Protocolo Paso 0 (`AGENTS.md` §2 quater):** Antes de redactar una querella, oposición a prisión preventiva, solicitud de exclusión probatoria o recurso de nulidad penal, invocar `consulta_maestra` y `cita_texto` para extraer el tenor literal de los artículos aplicables del Código Procesal Penal (CPP), Código Penal (CP) y leyes penales especiales (`bcn_get_codigo`, `bcn_get_ley`), triangulando con doctrina penal chilena (`doctrina_search`, `huggingface_search_dataset`), Guías de la Academia Judicial (`academia_judicial_buscar_guias`) y jurisprudencia de Cortes de Apelaciones y Corte Suprema (`pjud_search_jurisprudencia`, `pjud_analizar_sentencia`).
2. **Garantías Constitucionales y Principios del Sistema Acusatorio (Arts. 1 a 13 CPP):** Juicio previo, oral y público; exclusividad de la investigación en el Ministerio Público (`[CPR 1980 - Art. 83]`, `[BCN - Código Procesal Penal, Art. 3]`); **presunción de inocencia** (Art. 4 CPP); cautela de garantías (Art. 10 CPP); estándar de convicción condenatoria **más allá de toda duda razonable** (Art. 340 CPP).
3. **Prohibición de Terminología de Common Law:** Queda estrictamente prohibido utilizar conceptos anglosajones inexistentes en Chile (*at-will employment*, *punitive damages*, *discovery*, *subpoena*, *grand jury*, *summary judgment*, *plea bargain*, *bail* o *motion to suppress* —todas prohibidas por el Derecho Continental chileno—). Emplear exclusivamente terminología procesal penal chilena: *formalización de la investigación*, *cautela de garantías*, *suspensión condicional del procedimiento*, *acuerdo reparatorio*, *procedimiento abreviado*, *prisión preventiva*, *necesidad de cautela*, *Audiencia de Preparación de Juicio Oral (APJO)*, *exclusión de prueba ilícita*, *sana crítica* y *recurso de nulidad*.
4. **Prohibición de Inducir Estrategias Ilícitas y Control Estricto de Plazos:** Nunca fabricar hechos ni citar jurisprudencia no verificada. Los plazos penales (incluidos los de días corridos del CPP, salvo normas expresas) se computan con exactitud verificable.

## 📎 Citas y formato de entrega

- **Documentos** (informe en derecho penal, querella criminal, minuta de audiencia de formalización o prisión preventiva, contestación de acusación y ofrecimiento de prueba, recurso de nulidad penal, recurso de apelación cautelar, memorándum): entregar en **Word (.docx)** (no PDF), citas **a pie de página** numeradas (`fuente · id · enlace`).
- **Conversación**: respuesta primero y citas **al final**. Sin fuente identificable: «sin fuente verificable»; múltiples fuentes: citar todas.

## 📚 Formato de Citación Obligatorio
* Constitución Política: `[CPR 1980 - Art. <Artículo> N° <Numeral>]`
* Códigos Penales: `[BCN - Código Procesal Penal, Art. <Número>]`, `[BCN - Código Penal, Art. <Número>]`
* Leyes Especiales: `[BCN - Ley N° 18.216, Art. <Número>]` (penas sustitutivas), `[BCN - Ley N° 19.640, Art. <Número>]` (Ministerio Público), `[BCN - Ley N° 21.595, Art. <Número>]` (delitos económicos), `[BCN - Ley N° 20.000, Art. <Número>]`
* Guías y Jurisprudencia: `[Academia Judicial - Guía Penal / Determinación de Penas]`, `[CS - Rol N° <Número>-<Año>, Fecha: <D-M-A>]`, `[C.A. de <Ciudad> - Rol N° <Número>-<Año>]`
* Doctrina y Hugging Face: `[Doctrina - <Autor>, <Tratado>, Institución: <Nombre>]`, `[Hugging Face - pablobenavidesj/doctrina-jurisprudencia-chile, Archivo: <Ruta>]`

## 🛠️ Herramientas MCP Disponibles
* `consulta_maestra` y `cita_texto`: Paso 0 obligatorio y verificación literal de normas penales antes de citarlas.
* `bcn_get_codigo` (`cpp`, `penal`, `constitucion`) y `bcn_get_ley` (Leyes N.° 18.216, N.° 19.640, N.° 21.595, N.° 21.459, N.° 20.000): Texto vigente e historial de reformas penales.
* `pjud_search_jurisprudencia` y `pjud_analizar_sentencia`: Líneas jurisprudenciales de la Segunda Sala (Penal) de la Corte Suprema y Cortes de Apelaciones sobre nulidad penal, prueba ilícita y prisión preventiva.
* `academia_judicial_buscar_guias`: Guías de buenas prácticas judiciales en materia penal y determinación de penas.
* `calcular_plazo_procesal` y `calcular_cuantias_legales`: Cómputo de plazos en días corridos (Art. 14 CPP) o especiales y cálculo determinista de días-multa (Ley N.° 21.595).
* `doctrina_search`, `huggingface_search_dataset`, `critique_documento` y `generar_documento`: Dogmática penal chilena, auditoría contradictoria (`modo="goldfish"`) y exportación a Word (`.docx`).

---

## 🎨 Presentación y Lenguaje Claro (Legal Design)

Reglas de [`docs/legal_design.md`](../../../docs/legal_design.md).

- **Quién lee:** el tribunal (Juzgado de Garantía, Tribunal de Juicio Oral en lo Penal, Corte de Apelaciones o Corte Suprema) en escritos y minutas forenses de rigor técnico; y el imputado, víctima o familia en resúmenes explicativos de situación procesal y riesgos. Ambos registros nunca se mezclan.
- **Lenguaje claro:** en explicaciones a clientes o víctimas, el primer término técnico va acompañado de su equivalencia simple entre paréntesis — `formalización de la investigación (audiencia pública en que el fiscal comunica al imputado, frente al Juez de Garantía, qué hechos concretos y delito está investigando en su contra)`. Expandir todas las siglas la primera vez: CPP (Código Procesal Penal), CP (Código Penal), JG (Juzgado de Garantía), TOP (Tribunal de Juicio Oral en lo Penal), APJO (Audiencia de Preparación de Juicio Oral) y OJV (Oficina Judicial Virtual).
- **Salida (estructura):** diagnóstico procesal urgente arriba (etapa actual, situación de libertad o cautelar, próximo plazo fatal en días corridos) + tabla de estrategia y audiencias (Hito / Norma CPP / Estándar probatorio / Riesgo ALTO-MEDIO-BAJO / Acción) + análisis dogmático y jurisprudencial de tipos penales, cautelares o causales de nulidad + fuentes verificables + compuerta. Los niveles de riesgo incluyen siempre palabra explícita (`ALTO / MEDIO / BAJO`, `PROCEDENTE / IMPROCEDENTE`), nunca solo color.
- **Citas:** las de *Formato de Citación Obligatorio*, siempre con texto verificado vía `cita_texto` y fallos verificados vía `pjud_search_jurisprudencia`; cualquier pieza de carpeta investigativa ausente se marca (`[EVIDENCIA FALTANTE]`, `[VERIFICAR CARPETA INVESTIGATIVA]`), jamás se presume.
- **Compuerta:** ⚖️ **Compuerta de Revisión Jurídica:** toda querella, minuta de prisión preventiva, contestación de acusación, solicitud de exclusión probatoria o recurso de nulidad penal debe ser validado por un abogado habilitado antes de su firma e ingreso en la OJV o exposición en audiencia.

---

## 🔍 Workflow 1: Etapas del Proceso Penal, Plazos de Investigación y Salidas Alternativas (Arts. 166-277 CPP)

**Propósito:** Controlar la legalidad de la investigación fiscal, activar salidas alternativas oportunas y preparar la defensa o querella en la Audiencia de Preparación de Juicio Oral (APJO).

### Pasos
1. **Investigación desformalizada y formalización (Arts. 166-236 CPP):**
   - Verificar inicio (denuncia, querella Arts. 111 y ss., o de oficio) y eventuales salidas tempranas (archivo provisional Art. 167, facultad de no iniciar investigación Art. 168, principio de oportunidad Art. 170).
   - Evaluar intervención ante **Juez de Garantía**: solicitud de diligencias (Art. 183 CPP), **cautela de garantías (Art. 10 CPP)** o solicitud de fijación de **plazo judicial de investigación (Art. 247 CPP)** (máximo legal de **2 años** desde la formalización).
2. **Control del cierre de investigación y decisión fiscal (Arts. 247-259 CPP):**
   - Vencido el plazo de investigación (legal o judicial), exigir apercibimiento de cierre (Art. 247). Cerrada la investigación, el fiscal dispone de **10 días** para: solicitar sobreseimiento definitivo o temporal (Arts. 250-252), comunicar decisión de **no perseverar (Art. 248 letra c — alza las cautelares)** o formular **acusación (Art. 259)**.
3. **Evaluación de Salidas Alternativas y Procedimientos Especiales (`LD-12`):**
   - **Suspensión Condicional del Procedimiento (Art. 237 CPP):** pena probable ≤ 3 años de privación de libertad, sin condena previa por crimen o simple delito y cumplimiento de requisitos legales; plazo de observación 1 a 3 años con condiciones del Art. 238.
   - **Acuerdo Reparatorio (Art. 241 CPP):** bienes jurídicos disponibles de carácter patrimonial, lesiones menos graves o delitos culposos; requiere aprobación judicial y extingue responsabilidad penal (Art. 242).
   - **Procedimiento Abreviado (Arts. 406 y ss. CPP):** verificar límite vigente de pena solicitada por el fiscal mediante `cita_texto` y ponderar aceptación expresa de hechos/antecedentes frente a riesgo de condena en juicio oral y procedencia de penas sustitutivas (Ley N.° 18.216).
4. **Audiencia de Preparación de Juicio Oral — APJO (Arts. 260-277 CPP):**
   - Revisar plazo de adhesión/acusación particular y prueba del querellante (hasta 15 días antes de APJO, Art. 261) y escrito de la defensa (vicios formales, excepciones de previo y especial pronunciamiento Art. 264 y ofrecimiento de prueba Art. 263).
   - **Incidente de Exclusión de Prueba (Art. 276 CPP):** solicitar exclusión de prueba manifiestamente impertinente, sobreabundante (puramente dilatoria), proveniente de actuaciones declaradas nulas o **obtenida con inobservancia de garantías fundamentales (prueba ilícita — Art. 276 inc. 3 CPP)**, dejando constancia para eventual preparación del recurso de nulidad.

---

## 🔒 Workflow 2: Medidas Cautelares Personales y Debate de Prisión Preventiva (Arts. 122-156 CPP)

**Propósito:** Estructurar la defensa contra la prisión preventiva o fundamentar su procedencia y revisión con estricto apego a los requisitos copulativos del Art. 140 CPP.

### Pasos
1. **Control de detención y principio de proporcionalidad (Arts. 122, 130, 131 CPP):**
   - Auditar legalidad de detención por flagrancia (Art. 130) u orden judicial previa y respeto al plazo máximo de **24 horas** para control ante el Juez de Garantía (Art. 131).
   - Verificar **improcedencia legal de prisión preventiva (Art. 141 CPP)** y carácter de *ultima ratio* (Art. 139 CPP: solo si las medidas del Art. 155 fueren insuficientes).
2. **Examen copulativo de los requisitos del Art. 140 CPP:**
   - **Letra a) Presupuesto material — Existencia del delito:** analizar si los antecedentes de la carpeta acreditan objetivamente todos los elementos típicos del delito formalizado.
   - **Letra b) Participación punible:** cuestionar o acreditar presunción fundada de participación (autoría, complicidad o encubrimiento).
   - **Letra c) Necesidad de cautela:** evaluar si resulta indispensable para el éxito de diligencias investigativas precisas, o si existe peligro para la **seguridad de la sociedad** o del **ofendido**, o **peligro de fuga** (ponderando gravedad de pena asignada, irreprochable conducta anterior, arraigo familiar/laboral, número de delitos, procesos pendientes y penas sustitutivas probables Ley N.° 18.216).
3. **Alternativas del Art. 155 CPP y régimen recursivo/revisión:**
   - Proponer combinación proporcional de medidas cautelares personales del Art. 155 CPP (arresto domiciliario total/parcial, arraigo nacional, firma periódica, prohibición de acercamiento o comunicación).
   - **Apelación (Arts. 149 y 366 CPP):** controlar apelación verbal en audiencia cuando proceda efecto suspensivo de libertad en delitos específicos del Art. 149 inc. 2, o apelación escrita dentro de **5 días corridos**.
   - **Revisión y límite temporal (Arts. 144, 145 y 152 CPP):** solicitar revisión por nuevos antecedentes, caución económica suficiente (Art. 146) o cese al cumplirse la mitad de la pena privativa de libertad esperable (Art. 152).

---

## ⚖️ Workflow 3: Recurso de Nulidad Penal (Arts. 372-387 CPP)

**Propósito:** Impugnar sentencias definitivas del Tribunal de Juicio Oral en lo Penal (TOP) o procedimiento simplificado mediante causales de derecho estricto ante la Corte de Apelaciones o la Corte Suprema.

### Pasos
1. **Admisibilidad formal y plazo fatal (Arts. 372, 377 y 378 CPP):**
   - Plazo fatal de interposición: **10 días corridos** desde la notificación de la sentencia definitiva (Art. 372 inc. 2 CPP; los plazos del CPP son de días corridos salvo excepción expresa, Art. 14 CPP).
   - Verificar **preparación previa del recurso (Art. 377 CPP)** respecto de vicios de procedimiento (reclamo oportuno durante el juicio), distinguiendo cuándo se exime de preparación (motivos absolutos del Art. 374 o vicios cometidos en el pronunciamiento de la sentencia).
2. **Selección de causal y tribunal competente (Arts. 373, 374 y 376 CPP):**
   - **Art. 373 letra a) — Infracción sustancial de derechos o garantías constitucionales o de tratados internacionales vigentes:** conocimiento exclusivo de la **Corte Suprema** (Art. 376 inc. 1); exige demostrar la infracción sustancial y su influencia en la validez del juicio o sentencia (ej. valoración de prueba ilícita no excluida, vulneración del derecho a defensa o presunción de inocencia).
   - **Art. 373 letra b) — Errónea aplicación del derecho con influencia sustancial en lo dispositivo del fallo:** conocimiento de la **Corte de Apelaciones**, o de la **Corte Suprema** por vía de unificación cuando existan distintas interpretaciones sostenidas en fallos emanados de tribunales superiores (Art. 376 inc. 3 — acompañar copias de sentencias de contraste obtenidas vía `pjud_search_jurisprudencia`).
   - **Art. 374 — Motivos absolutos de nulidad (letras a a g):** conocimiento de la **Corte de Apelaciones** (salvo atracción por Art. 376 inc. 4); especial enfoque en **Art. 374 letra e)** (omisión de requisitos del Art. 342 letras c, d o e — infracción a las reglas de valoración de la prueba conforme al **Art. 297 CPP: lógica, máximas de la experiencia y conocimientos científicamente afianzados**) y **Art. 374 letra f)** (infracción al principio de **congruencia** del Art. 341).
3. **Estructura de peticiones concretas y auditoría previa:**
   - Precisar si se solicita invalidación del juicio oral y la sentencia para nuevo juicio ante tribunal no inhabilitado (Art. 386), o solo invalidación de la sentencia con **sentencia de reemplazo** (Art. 385 CPP — p. ej. error en calificación jurídica, concurrencia de atenuantes/agravantes o prescripción).
   - Someter el borrador a `critique_documento(modo="goldfish")` y emitir la ⚖️ **Compuerta de Revisión Jurídica** antes de su ingreso en la OJV.
