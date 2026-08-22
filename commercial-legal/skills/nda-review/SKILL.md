---
name: nda-review
description: >
  Revisión y triaje de Acuerdos de Confidencialidad (NDA / Non-Disclosure Agreement)
  bajo el derecho comercial y civil chileno. Clasifica en VERDE / AMARILLO / ROJO,
  verifica ley aplicable (República de Chile / CAM Santiago), vigencia, exclusiones,
  secreto empresarial (Ley 19.039), cláusula penal (Art. 1535 CC) y detecta
  cláusulas ocultas de no competencia o cesión de propiedad intelectual.
user-invocable: false
---

# /nda-review (Triaje de Acuerdos de Confidencialidad — Chile)

1. Cargar el playbook comercial y perfil de riesgo de la empresa (`commercial-legal/CLAUDE.md`).
2. Identificar la posición contractual: **Bilateral/Mutuo**, **Unilateral como Emisor (Divulgador)** o **Unilateral como Receptor**.
3. Realizar el escaneo de **Cláusulas Ocultas / Trampas Contractuales** (Cesión de IP, no competencia, exclusividades).
4. Evaluar las cláusulas clave bajo el **Código Civil chileno** (Art. 1545, 1546, 1535) y Ley de Propiedad Industrial (Ley 19.039).
5. Emitir veredicto de triaje: 🟢 **VERDE (Firma directa)** / 🟡 **AMARILLO (Ajustes puntuales)** / 🔴 **ROJO (Bloqueante - Requiere abogado)**.

---

## 1. Escaneo de Cláusulas Ocultas (Caballos de Troya)

> ⚠️ **Regla de Alerta Inmediata:** Si el NDA contiene alguna de las siguientes estipulaciones, se clasifica automáticamente como **🔴 ROJO / 🟡 AMARILLO**:
> * **Cesión o Licencia de Propiedad Intelectual encubierta:** Cualquier cláusula que sugiera que divulgar información transfiere derechos de autor, software o patentes.
> * **No Competencia (*Non-Compete*):** Prohibición general de operar en la misma industria (atenta contra la libre competencia y libertad de trabajo).
> * **No Contratación Desmedida (*Non-Solicit*):** Prohibición de contratar colaboradores sin excepciones razonables de postulaciones espontáneas.
> * **Jurisdicción Extranjera Forzosa:** Fijación de leyes o tribunales de Delaware, Nueva York o Inglaterra para operaciones exclusivamente locales en Chile.

---

## 2. Matriz de Evaluación de Términos (Checklist Chile)

| Cláusula | Estándar de Mercado Seguro en Chile | Bandera de Riesgo |
|---|---|---|
| **Ley Aplicable** | Leyes de la **República de Chile**. | 🔴 Si fija ley extranjera para negocios puramente chilenos. |
| **Solución de Controversias** | Tribunales Ordinarios de Santiago o Arbitraje **CAM Santiago** (Centro de Arbitraje y Mediación de la CCS). | 🟡 Si fija tribunales de otra región o arbitraje internacional de alto costo (ICC/AAA). |
| **Exclusiones de Confidencialidad** | Información de dominio público, en posesión previa legítima, desarrollada independientemente o requerida por ley/tribunal. | 🔴 Si NO incluye excepciones de orden judicial o dominio público. |
| **Vigencia de la Confidencialidad** | **2 a 5 años** desde la divulgación. Secretos empresariales conforme a Ley 19.039 mientras mantengan tal carácter. | 🟡 Si fija confidencialidad indefinida para información comercial ordinaria. |
| **Cláusula Penal (Art. 1535 CC)** | Monto razonable prefijado para indemnización de perjuicios (sujeto al límite de cláusula penal enorme del Art. 1544 CC). | 🟡 Si fija multas desproporcionadas no correlacionadas con el riesgo real. |
| **Devolución o Destrucción** | Obligación de restituir o destruir información confidencial a solicitud, permitiendo copia de resguardo legal/cumplimiento. | 🟡 Si exige destrucción de backups informáticos rutinarios imposibles de purgar. |

---

## 3. Formato del Dictamen de Revisión

```markdown
# INFORME DE TRIAJE DE ACUERDO DE CONFIDENCIALIDAD (NDA)
**Contraparte:** [Nombre Empresa / Persona]
**Tipo de NDA:** [Bilateral / Unilateral] | **Fecha de Revisión:** [Fecha]

---

### 1. Veredicto Ejecutivo
- **Calificación:** [🟢 VERDE — APTO PARA FIRMA / 🟡 AMARILLO — NEGOCIAR CAMBIOS / 🔴 ROJO — RECHAZAR]
- **Resumen:** [Síntesis en 2 líneas de los puntos críticos detectados].

---

### 2. Puntos Clave Auditados
- Ley y Tribunales: [✅ Chile / CAM Santiago | 🔴 Ley extranjera detectada]
- Plazo de Confidencialidad: [✅ 3 años | 🟡 Indefinido]
- Cláusulas Ocultas: [✅ Ninguna | 🔴 Cláusula de no competencia detectada en Art. X]
- Excepciones Legales: [✅ Completas | 🟡 Falta excepción por requerimiento de autoridad pública]

---

### 3. Redlines / Cambios Concretos Sugeridos
* **Cláusula [X] (Jurisdicción):**
  - *Texto actual:* "Las partes se someten a las leyes del Estado de Nueva York..."
  - *Redacción propuesta:* "El presente acuerdo se regirá e interpretará conforme a las leyes de la República de Chile. Toda controversia será sometida a los Tribunales Ordinarios de Justicia de la comuna de Santiago."

---

### 4. Siguientes Pasos
1. [ ] Enviar contrapropuesta con redlines a la contraparte.
2. [ ] Proceder a firma electrónica avanzada o simple si los cambios son aceptados.
```
