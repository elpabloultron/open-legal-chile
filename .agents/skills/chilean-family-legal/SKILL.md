---
name: chilean-family-legal
description: "Especialista en Derecho de Familia chileno: Tribunales de Familia (Ley N.° 19.968, procedimiento ordinario, audiencias preparatoria y de juicio, mediación previa obligatoria Art. 106), pensión de alimentos en UTM (Ley N.° 14.908), Registro Nacional de Deudores de Pensiones de Alimentos (Ley N.° 21.389) y pago efectivo con fondos bancarios y previsionales (Ley N.° 21.484), Violencia Intrafamiliar (Ley N.° 20.066 — medidas cautelares Arts. 7 y 92), cuidado personal, relación directa y regular (Arts. 224-229 CC) y divorcio / compensación económica (Ley N.° 19.947)."
---

# Habilidad: Derecho de Familia y Protección Integral en Chile (chilean-family-legal)

## 📌 Paso 0 Obligatorio y Principios Rectores
1. **Protocolo Paso 0 (`AGENTS.md` §2 quater):** Antes de redactar una demanda, contestación, liquidación de deuda o dictamen familiar, invocar `consulta_maestra` y `cita_texto` para verificar el texto literal de las normas vigentes (`bcn_get_ley`, `bcn_get_codigo`), triangulando con doctrina nacional (`doctrina_search`, `huggingface_search_dataset`), Guías de la Academia Judicial (`academia_judicial_buscar_guias`) y jurisprudencia de los Tribunales Superiores (`pjud_search_jurisprudencia`).
2. **Interés Superior del Niño, Niña o Adolescente y Corresponsabilidad:** Principio rector obligatorio en toda resolución y estrategia de familia (`[BCN - Ley N° 19.968, Art. 16]`, `[BCN - Ley N° 21.430, Art. 7]`, `[BCN - Código Civil, Art. 222]`). El derecho del niño, niña o adolescente a ser oído debe ponderarse según su edad y madurez.
3. **Mediación Previa Obligatoria y su Prohibición en VIF (`LD-12`):** En materias de alimentos, cuidado personal y relación directa y regular es requisito de procesabilidad acompañar **acta o certificado de mediación frustrada** (`[BCN - Ley N° 19.968, Art. 106]`). Queda **estrictamente prohibida la mediación** en causas de Violencia Intrafamiliar (Art. 106 inc. 5).
4. **Prohibición de Terminología de Common Law:** Queda estrictamente prohibido utilizar conceptos anglosajones inexistentes en Chile (*at-will employment*, *punitive damages*, *discovery*, *subpoena*, *grand jury*, *summary judgment*, *child support*, *alimony* o *joint custody* —todas prohibidas por el Derecho Continental chileno—). Utilizar exclusivamente terminología oficial chilena: *pensión de alimentos en UTM*, *cuidado personal*, *cuidado personal compartido*, *relación directa y regular*, *patria potestad*, *compensación económica*, *Registro Nacional de Deudores de Pensiones de Alimentos (RNDPA)* y *Violencia Intrafamiliar (VIF)*.

## 📎 Citas y formato de entrega

- **Documentos** (informe en derecho, demanda de alimentos o cuidado personal, contestación, liquidación de deuda alimentaria, solicitud de pago especial o extraordinario Ley N.° 21.484, denuncia o solicitud de medidas cautelares VIF, memorándum, minuta): entregar en **Word (.docx)** (no PDF), citas **a pie de página** numeradas (`fuente · id · enlace`).
- **Conversación**: respuesta primero y citas **al final**. Sin fuente identificable: «sin fuente verificable»; múltiples fuentes: citar todas.

## 📚 Formato de Citación Obligatorio
* Ley de Tribunales de Familia: `[BCN - Ley N° 19.968, Art. <Número>]`
* Pensiones Alimenticias y Registro/Pago Efectivo: `[BCN - Ley N° 14.908, Art. <Número>]`, `[BCN - Ley N° 21.389, Art. <Número>]`, `[BCN - Ley N° 21.484, Art. <Número>]`
* Violencia Intrafamiliar y Niñez: `[BCN - Ley N° 20.066, Art. <Número>]`, `[BCN - Ley N° 21.430, Art. <Número>]`
* Código Civil y Matrimonio Civil: `[BCN - Código Civil, Art. <Número>]`, `[BCN - Ley N° 19.947, Art. <Número>]`
* Guías y Jurisprudencia: `[Academia Judicial - Guía de Familia / Alimentos]`, `[CS - Rol N° <Número>-<Año>, Fecha: <D-M-A>]`, `[C.A. de <Ciudad> - Rol N° <Número>-<Año>]`
* Doctrina y Hugging Face: `[Doctrina - <Autor>, <Tratado>, Institución: <Nombre>]`, `[Hugging Face - pablobenavidesj/doctrina-jurisprudencia-chile, Archivo: <Ruta>]`

## 🛠️ Herramientas MCP Disponibles
* `consulta_maestra` y `cita_texto`: Paso 0 obligatorio y verificación literal de normas antes de citarlas.
* `bcn_get_ley` (Leyes N.° 19.968, N.° 14.908, N.° 21.389, N.° 21.484, N.° 20.066, N.° 19.947, N.° 21.430, N.° 20.680) y `bcn_get_codigo` (`civil`, `cpc`).
* `calcular_cuantias_legales`: Cálculo determinista con `tipo="alimentos_utm"` (pensión mínima 40 % IMM para 1 hijo / 30 % por hijo para 2 o más hijos, tope máximo 50 % de rentas del alimentante y conversión oficial a UTM/CLP).
* `indicadores_economicos_chile`: Consulta de valor oficial de UTM y UF del SII para liquidaciones y reajustes.
* `calcular_plazo_procesal`: Cómputo de plazos hábiles judiciales (contestación con 5 días de anticipación a la audiencia preparatoria, apelación 5 o 10 días hábiles según resolución, Art. 67 Ley N.° 19.968).
* `pjud_search_jurisprudencia` y `academia_judicial_buscar_guias`: Criterios de Corte Suprema y guías de buenas prácticas en Familia.
* `clinica_lenguaje_claro`: Traducción a español cotidiano comprensible cuando el destinatario sea madre, padre, cuidador o parte no abogada.
* `doctrina_search`, `huggingface_search_dataset`, `critique_documento` y `generar_documento`: Sustento dogmático, auditoría y entrega en Word (`.docx`).

---

## 🎨 Presentación y Lenguaje Claro (Legal Design)

Reglas de [`docs/legal_design.md`](../../../docs/legal_design.md).

- **Quién lee:** por un lado, el Juzgado de Familia competente en escritos forenses con técnica procesal estricta; por otro, madres, padres, cuidadores o víctimas en minutas explicativas que requieren máxima claridad y contención. Ambos registros no se mezclan.
- **Lenguaje claro:** el primer término técnico de cada minuta o explicación ciudadana va siempre seguido de su equivalencia cotidiana entre paréntesis — `alimentos provisorios (pensión temporal que el tribunal fija al admitir la demanda para cubrir gastos urgentes mientras dura el juicio)`. Expandir todas las siglas la primera vez: UTM (Unidad Tributaria Mensual), IMM (Ingreso Mínimo Mensual), RNDPA (Registro Nacional de Deudores de Pensiones de Alimentos), VIF (Violencia Intrafamiliar), AFP (Administradora de Fondos de Pensiones) y OJV (Oficina Judicial Virtual).
- **Salida (estructura):** decisión o medida urgente arriba (¿hay riesgo VIF? / ¿requiere mediación previa? / monto mínimo y tope en UTM) + tabla de pretensiones y requisitos (Materia / Norma / Prueba requerida / Estado / Acción) + ruta procedimental (mediación, audiencia preparatoria, audiencia de juicio) + cálculo determinista en UTM/CLP + fuentes verificables + compuerta. Los estados llevan siempre palabra explícita (`URGENTE / REQUIERE MEDIACIÓN / COMPLETO / BRECHA`), nunca solo color.
- **Citas:** las de *Formato de Citación Obligatorio*, siempre con texto verificado vía `cita_texto`; los datos socioeconómicos, ingresos o certificados no acompañados se marcan (`[EVIDENCIA FALTANTE]`, `[VERIFICAR]`), nunca se suponen.
- **Compuerta:** ⚖️ **Compuerta de Revisión Jurídica:** toda demanda de familia, solicitud de apremios, retención de fondos AFP/bancarios o denuncia/solicitud cautelar por Violencia Intrafamiliar debe ser validada por un abogado habilitado antes de su ingreso en la OJV o presentación ante el tribunal.

---

## ⚖️ Workflow 1: Procedimiento Ordinario ante Tribunales de Familia y Mediación Previa (Ley N.° 19.968)

**Propósito:** Preparar la demanda o contestación ante el Juzgado de Familia respetando el requisito de mediación previa, la estructura de doble audiencia y las cargas probatorias.

### Pasos
1. **Filtro de admisibilidad — Mediación Previa vs. Urgencia VIF (Art. 106 Ley N.° 19.968):**
   - Si la materia es **alimentos, cuidado personal o relación directa y regular**, exigir **acta de mediación frustrada** antes de presentar demanda (`LD-12`).
   - Si existe **Violencia Intrafamiliar (VIF)**, la mediación está **prohibida**; activar de inmediato medidas cautelares (Workflow 3).
2. **Estructura de Demanda y Peticiones Iniciales (Arts. 55-58 Ley N.° 19.968):**
   - Presuma OJV, tribunal competente (domicilio del alimentario/niño o demandado según materia), individualización con RUN y patrocinio y poder (Ley N.° 18.120).
   - En demanda de alimentos: solicitar expresamente **alimentos provisorios (Art. 4 Ley N.° 14.908)** en el primer otrosí o cuerpo principal acompañando antecedentes de necesidades e ingresos, fijados en **UTM**.
   - **Contestación y reconvención (Art. 58):** presentar por escrito al menos **5 días antes** de la fecha fijada para la Audiencia Preparatoria.
3. **Audiencia Preparatoria (Art. 61) y Audiencia de Juicio (Art. 63):**
   - Preparar minuta de conciliación posible, delimitación del objeto del juicio y hechos a probar, ofrecimiento de toda la prueba (documental, oficios a SII/AFP/empleador/bancos, testigos, pericial, intervención del Consejo Técnico) y objeción de prueba ilícita o sobreabundante (Art. 31).
   - En Audiencia de Juicio: orden de rendición, observaciones a la prueba y control de plazos recursivos (Art. 67 Ley N.° 19.968).

---

## 💰 Workflow 2: Pensión de Alimentos en UTM, Registro Nacional de Deudores y Pago Efectivo (Leyes N.° 14.908, N.° 21.389 y N.° 21.484)

**Propósito:** Cuantificar pensiones en UTM, gestionar la inscripción en el RNDPA y activar el cobro compulsivo sobre cuentas bancarias y fondos previsionales.

### Pasos
1. **Cálculo determinista en UTM y control de mínimos y topes (Arts. 3 y 7 Ley N.° 14.908):**
   - Invocar `indicadores_economicos_chile` y `calcular_cuantias_legales(tipo="alimentos_utm", imm_clp=..., numero_hijos=..., ingreso_liquido_alimentante_clp=...)` para obtener monto mínimo legal (**40 % IMM** para 1 hijo; **30 % IMM** por cada hijo si son 2 o más), conversión exacta a **UTM** y verificación del **tope máximo del 50 %** de las rentas del alimentante.
2. **Inscripción y efectos del Registro Nacional de Deudores — RNDPA (Ley N.° 21.389, Arts. 20 y ss. Ley N.° 14.908):**
   - Verificar causal objetiva: **3 mensualidades consecutivas** o **5 discontinuas** impagas (totales o parciales) tras liquidación firme.
   - Activar retenciones obligatorias: devolución de impuestos (TGR), operaciones de crédito bancarias ≥ 50 UF (Art. 28), compraventa de inmuebles o vehículos ante CBR/Registro Civil (Art. 29), bloqueo de renovación de licencia de conducir/pasaporte (Art. 33) y **retención por empleador con responsabilidad solidaria** (Arts. 13 y 36).
   - Evaluar apremios tradicionales (Arts. 14 y 16): arresto nocturno, arresto íntegro, arraigo nacional y suspensión de licencia de conducir, además de agravamiento por violencia económica.
3. **Procedimiento Especial y Extraordinario de Pago Efectivo (Ley N.° 21.484 — Arts. 19 quater y 19 quinquies Ley N.° 14.908):**
   - **Procedimiento Especial (Art. 19 quater):** tras 1 o más cuotas impagas liquidadas, solicitar interconexión judicial (CMF/SII/bancos) para retener y pagar directamente desde cuentas bancarias, cuentas de ahorro o instrumentos financieros del deudor.
   - **Procedimiento Extraordinario en AFP (Art. 19 quinquies):** si no existen fondos bancarios suficientes tras 3 mensualidades impagas, solicitar pago con cargo a la cuenta de capitalización individual obligatoria del deudor en su AFP, respetando los límites porcentuales según cercanía a la edad de jubilación (verificar texto literal con `cita_texto`).

---

## 🛡️ Workflow 3: Violencia Intrafamiliar (Ley N.° 20.066), Cuidado Personal y Divorcio / Compensación Económica

**Propósito:** Brindar protección cautelar inmediata en contextos de VIF y estructurar pretensiones de corresponsabilidad parental, cuidado personal, relación directa y regular y compensación económica.

### Pasos
1. **Protección urgente ante Violencia Intrafamiliar (Ley N.° 20.066 y Arts. 81-101 Ley N.° 19.968):**
   - Evaluar factores de riesgo vital y remitir a Fiscalía si existe **maltrato habitual (Art. 14 Ley N.° 20.066)** o lesiones/amenazas constitutivas de delito.
   - Solicitar **medidas cautelares urgentes (Art. 7 Ley N.° 20.066 y Art. 92 Ley N.° 19.968)**: prohibición de acercamiento, salida del ofensor del hogar común, entrega de efectos personales, alimentos provisorios, reserva de identidad de la víctima y prohibición de porte de armas.
   - Verificar **violencia económica** (incumplimiento reiterado de alimentos para menoscabar autonomía, Art. 5 inc. final Ley N.° 20.066).
2. **Cuidado Personal y Relación Directa y Regular (Arts. 224, 225, 225-2 y 229 Código Civil):**
   - Verificar si existe acuerdo por escritura pública o acta ante Oficial de Registro Civil subinscrita dentro de 30 días (Art. 225 inc. 1 CC).
   - En juicio, estructurar la prueba según los criterios legales taxativos del **Art. 225-2 CC** (vinculación afectiva, aptitud para garantizar bienestar, contribución a la mantención, actitud de cooperación para el vínculo con el otro padre, opinión del hijo).
   - Diseñar calendario detallado de **relación directa y regular (Art. 229 CC)** (días ordinarios, fines de semana, vacaciones de invierno/verano, fiestas patrias, navidad/año nuevo y cumpleaños).
3. **Divorcio y Compensación Económica (Ley N.° 19.947):**
   - Verificar causal (mutuo acuerdo Art. 55 inc. 1 —1 año cese convivencia—; unilateral Art. 55 inc. 3 —3 años cese convivencia + **cláusula de dureza** por incumplimiento reiterado de alimentos—; por culpa Art. 54) y acreditación fehaciente de fecha cierta del cese (Arts. 22 y 25, cuando el matrimonio sea posterior al 17-11-2004).
   - Cuantificar **compensación económica (Arts. 61-66 Ley N.° 19.947)** por menoscabo económico derivado de dedicación al cuidado de los hijos o labores del hogar común.
4. **Cierre y Compuerta:** Emitir tabla, fuentes verificadas y ⚖️ **Compuerta de Revisión Jurídica**.
