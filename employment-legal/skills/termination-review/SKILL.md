---
name: termination-review
description: >
  Revisión de término de contrato de trabajo en Chile (Código del Trabajo).
  Detecta causales (Art. 159, 160, 161), banderas de alto riesgo (fueros,
  Ley Bustos, Ley Karin, tutela laboral por vulneración de derechos
  fundamentales), calcula indemnizaciones (años de servicio con tope 90 UF,
  mes de aviso sustitutivo, feriado proporcional y descuento AFC) y valida
  requisitos de la carta de despido y finiquito.
argument-hint: "[describe el despido/término, adjunta antecedentes o carta de despido]"
---

# /termination-review (Revisión de Término de Contrato — Chile)

1. Cargar contexto laboral de la empresa (`employment-legal/CLAUDE.md`).
2. Ejecutar el flujo de verificación de legalidad bajo el **Código del Trabajo de la República de Chile**.
3. Realizar el escaneo exhaustivo de **Banderas Rojas / Alto Riesgo** (Fueros, Ley Bustos, Tutela Laboral, Ley Karin).
4. Calcular o verificar montos indemnizatorios y plazos de comunicación (Carta de despido e Inspección del Trabajo).
5. Emitir compuerta de validación legal (*Attorney Review Gate*) antes de cualquier acción irrevocable.

---

## Propósito

El término de una relación laboral en Chile está estrictamente reglado por el principio de **estabilidad relativa en el empleo**. Los despidos injustificados, indebidos, improcedentes o nulos acarrean recargos legales del 30% al 100% sobre la indemnización por años de servicio (Art. 168), nulidad del despido con devengo de remuneraciones (Ley Bustos - Art. 162) o indemnizaciones adicionales de 6 a 11 meses por vulneración de derechos fundamentales (Tutela Laboral - Art. 485 y ss.).

Este skill analiza los hechos, califica la causal legal, verifica formalidades y mitiga riesgos judiciales antes de que la decisión se comunique al trabajador.

---

## Flujo de Trabajo (Workflow)

### Paso 1: Antecedentes Básicos del Trabajador y Relación Laboral
- Nombre / Identificador del trabajador y cargo.
- Fecha de ingreso y fecha proyectada de término (para cómputo de antigüedad).
- Última remuneración mensual bruta y base de cálculo (Art. 172 Código del Trabajo: sueldo base, gratificación legal, asignaciones imponibles fijas o promedio de variables de los últimos 3 meses; exclusión de viáticos y movilización que no constituyan remuneración ordinaria).
- Valor de la UF a la fecha de término (para aplicación del tope de 90 UF del Art. 172).
- Causal invocada preliminarmente.
- ¿Se cuenta con contrato escriturado y comprobantes de remuneraciones firmados?

---

### Paso 2: Escaneo de Banderas Rojas de Alto Riesgo (*High-Risk Flags*)

Este paso es obligatorio e intransable. Evalúa las siguientes contingencias críticas:

| Bandera de Riesgo | Fundamento Legal (Chile) | Contingencia y Efecto Jurídico | Verificación Obligatoria |
|---|---|---|---|
| 🔴 **Fuero Maternal** | Art. 201 y 174 Código del Trabajo | Despido NULO absoluto. Requiere autorización judicial previa (juicio de desafuero) ante el Juzgado de Letras del Trabajo. | ¿La trabajadora está embarazada, en descanso maternal o hasta 1 año después de expirado el postnatal? |
| 🔴 **Fuero Sindical / Negociación** | Art. 243 y 309 Código del Trabajo | Despido NULO sin desafuero judicial. | ¿Es dirigente sindical, delegada/o o parte de una comisión negociadora colectiva reglada? |
| 🔴 **Fuero Comité Paritario** | Art. 243 inc. final Código del Trabajo | Despido NULO sin desafuero previo. | ¿Es representante titular de los trabajadores en el Comité Paritario de Higiene y Seguridad? |
| 🔴 **Ley Bustos (Cotizaciones Impagas)** | Art. 162 inc. 5 a 7 Código del Trabajo | **Nulidad del despido**. El empleador debe seguir pagando remuneraciones mensuales y cotizaciones hasta que convalide el despido acreditando el pago íntegro. | ¿Están 100% pagadas e informadas las cotizaciones en AFP, Salud (Fonasa/Isapre), AFC y Mutualidad hasta el último día del mes anterior al despido? |
| 🔴 **Denuncia Ley Karin Reciente** | Ley N° 21.643 / Art. 2 y 160 Código del Trabajo | Presunción de **represalia / Tutela Laboral**. | ¿El trabajador denunció acoso laboral, sexual o violencia en el trabajo en los últimos 6 meses? |
| 🔴 **Licencia Médica Vigente** | Art. 161 inc. 3 Código del Trabajo | **Prohibición expresa de despido por necesidades de la empresa** (Art. 161). Despido nulo e ineficaz. | ¿El trabajador se encuentra con licencia médica por enfermedad común, profesional o accidente laboral al momento de la comunicación? |
| 🔴 **Riesgo de Tutela Laboral** | Art. 485 y ss. Código del Trabajo | Demanda con recargo de 6 a 11 meses de remuneración por vulneración de derechos fundamentales (garantía de indemnidad, no discriminación, libertad sindical). | ¿El despido coincide con reclamos ante la DT, testimonios en juicios o ejercicio de derechos fundamentales? |

---

### Paso 3: Análisis y Calificación de la Causal Legal

#### A. Art. 159 — Causales Objetivas (Sin indemnización por años de servicio)
1. *N° 1: Mutuo acuerdo de las partes* (Debe constar por escrito y ratificarse ante ministro de fe — Art. 177).
2. *N° 2: Renuncia del trabajador* (Aviso con 30 días de anticipación; ratificada ante ministro de fe).
3. *N° 3: Muerte del trabajador*.
4. *N° 4: Vencimiento del plazo convenido en el contrato* (Cuidado: transformación tácita a indefinido si continúa prestando servicios o por segunda renovación).
5. *N° 5: Conclusión del trabajo o servicio que dio origen al contrato*.
6. *N° 6: Caso fortuito o fuerza mayor*.

#### B. Art. 160 — Causales Subjetivas Imputables (Despido Disciplinario / Sin indemnización)
* Requieren estándar probatorio riguroso en juicio. Si el tribunal declara el despido injustificado, se condena al pago de IAS con **recargo legal del 80% o 100%** (Art. 168 letras b y c).
* *N° 1:* Falta de probidad, conductas de acoso sexual, acoso laboral (conforme a Ley Karin) o injurias proferidas al empleador.
* *N° 3:* No concurrencia a labores sin causa justificada durante 2 días seguidos, 2 lunes en el mes o 3 días en el mes.
* *N° 7:* Incumplimiento grave de las obligaciones que impone el contrato (debe acreditarse gravedad y proporcionalidad objetiva).

#### C. Art. 161 — Necesidades de la Empresa y Desahucio
* **Inciso 1 (Necesidades de la empresa):** Requiere hechos objetivos, técnicos o económicos (racionalización, modernización, bajas de productividad). No puede fundarse en la sola voluntad del empleador ni en desempeño individual subjetivo. Origina pago de IAS y mes de aviso. Recargo judicial si se declara injustificado: **30% sobre la IAS** (Art. 168 letra a).
* **Inciso 2 (Desahucio escrito):** Aplicable EXCLUSIVAMENTE a trabajadores con facultades de administración (gerentes, subgerentes) y cargos de exclusiva confianza del empleador.

---

### Paso 4: Liquidación de Indemnizaciones y Haberes

1. **Indemnización por Años de Servicio (IAS - Art. 163):**
   * Antigüedad: 1 año completo o fracción superior a 6 meses = 1 mes de sueldo.
   * Tope de años: Máximo 11 años (salvo contratos anteriores al 14 de agosto de 1981).
   * Tope de remuneración mensual: Máximo **90 UF** al último día del mes anterior al término (Art. 172).
   
2. **Indemnización Sustitutiva del Aviso Previo (Mes de Aviso - Art. 161 inc. 2):**
   * Corresponde a 1 última remuneración si no se entrega la carta de despido con 30 días de anticipación a la fecha de efectividad.
   
3. **Feriado Legal y Feriado Proporcional (Art. 73):**
   * Compensación en dinero de días de vacaciones pendientes devengados (15 días hábiles al año) más fracción proporcional por meses trabajados.
   
4. **Descuento del Aporte del Empleador a la AFC (Art. 13 Ley 19.728):**
   * En caso de despido por Art. 161 (Necesidades de la empresa), el empleador tiene derecho a deducir de la IAS el saldo total acumulado de su aporte al Fondo de Cesantía del trabajador (Cuenta Individual por Cesantía - CIC), según cartola oficial emitida por AFC Chile.

---

### Paso 5: Requisitos Formales de la Carta de Despido (Art. 162)

1. **Envío y Plazos:**
   * Entrega personal con firma de recepción o envío por carta certificada al domicilio fijado en el contrato.
   * Plazo: Dentro de los **3 días hábiles** siguientes a la separación (o 6 días hábiles si la causal es Art. 159 N° 6 caso fortuito).
2. **Notificación a la Inspección del Trabajo:**
   * Envío de copia idéntica a la DT dentro del mismo plazo (a través del portal digital de la DT).
3. **Contenido Obligatorio del Escrito:**
   * Causal legal invocada con mención expresa del artículo e inciso del Código del Trabajo.
   * **Fundamentación circunstanciada de los hechos** (jurisprudencia unánime: no basta con citar el artículo, deben detallarse las razones fácticas; en juicio no se podrán alegar hechos distintos).
   * Estado de pago de las cotizaciones previsionales con adjunción de los certificados de AFP, Salud y AFC.
   * Monto propuesto de liquidación de indemnizaciones si corresponde.

---

### Paso 6: Finiquito de Trabajo (Art. 177)

* Debe ser otorgado por el empleador y puesto a disposición del trabajador dentro de los **10 días hábiles** siguientes a la separación.
* Debe ser ratificado ante ministro de fe (Inspector del Trabajo, Notario Público, dirigente sindical respectivo o plataforma de Finiquito Electrónico de la DT).
* Posibilidad de **Reserva de Derechos**: El trabajador puede estampar de puño y letra (o digitalmente en portal DT) su reserva de derechos para demandar despido injustificado, cobro de prestaciones o indemnización de perjuicios.

---

## Formato de Salida / Entregable

```markdown
# INFORME DE REVISIÓN DE TÉRMINO LABORAL
**Fecha:** [Fecha]
**Trabajador:** [Nombre/Cargo]
**Antigüedad:** [X años y Y meses] | **Remuneración base cálculo:** [$X / UF Y]
**Causal propuesta:** [Art. 161 inc. 1 / Art. 160 N° X / Art. 159 N° X]

---

### 1. Veredicto Ejecutivo (Bottom Line)
- **Estado:** [🟢 VIABLE / 🟡 VIABLE CON PRECAUCIONES / 🔴 NO PROCEDER - BLOQUEADO]
- **Síntesis del riesgo:** [Explicación en 2 líneas del escenario legal y contingencias económicas].

---

### 2. Escaneo de Banderas Rojas y Fueros
- Fuero Maternal: [✅ Descartado / 🔴 DETECTADO - Desafuero judicial requerido]
- Fuero Sindical / Paritario: [✅ Descartado / 🔴 DETECTADO]
- Estado Ley Bustos (Cotizaciones): [✅ Al día con certificados / 🔴 PENDIENTE - Nulidad inminente]
- Licencia Médica Vigente: [✅ Sin licencia / 🔴 CON LICENCIA - Prohibido Art. 161]
- Riesgo Tutela / Ley Karin: [✅ Bajo / 🟡 Medio / 🔴 Alto]

---

### 3. Liquidación Proyectada de Indemnizaciones
- **Indemnización por Años de Servicio ([N] años):** $[Monto] `[BCN - Código del Trabajo, Art. 163]`
- **Mes de Aviso Sustitutivo:** $[Monto]
- **Feriado Legal y Proporcional ([D] días):** $[Monto]
- **Descuento Aporte Patronal AFC (si aplica Art. 161):** -$[Monto]
- **TOTAL FINIQUITO ESTIMADO:** $[Monto Total]

---

### 4. Checklist para el Día del Término
- [ ] Certificados de cotizaciones previsionales al día descargados de Previred / instituciones.
- [ ] Carta de despido redactada con fundamentación circunstanciada de hechos.
- [ ] Envío de carta certificada por Correos de Chile / Notificación personal firmada.
- [ ] Notificación digital del despido en el portal Mi DT (dentro de 3 días hábiles).
- [ ] Finiquito preparado para firma ante Notaría o Finiquito Electrónico DT (plazo 10 días hábiles).

---

### 5. Árbol de Siguientes Pasos
1. **Redactar Carta de Despido Formal:** Elaborar borrador con fundamentos fácticos blindados para Chile.
2. **Simular Finiquito Completo:** Confeccionar borrador de finiquito con cláusula de finiquito y reserva de derechos.
3. **Evaluar Salida Negociada / Mutuo Acuerdo:** Estructurar propuesta de mutuo acuerdo (Art. 159 N° 1) con bonificación voluntaria.
```

---

## Compuerta de Validación Legal (*Attorney Gate*)

> ⚖️ **Compuerta de Responsabilidad Profesional:**
> Las decisiones de término de contrato de trabajo en Chile generan obligaciones patrimoniales y potenciales demandas laborales en sede judicial o reclamaciones administrativas ante la Inspección del Trabajo. Este análisis debe ser revisado y visado por un abogado o el área de relaciones laborales antes de cursar la comunicación formal al trabajador o a la Dirección del Trabajo.
