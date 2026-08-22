---
name: client-intake
description: >
  Intake y atención socio-jurídica para Clínicas Jurídicas universitarias y
  Corporaciones de Asistencia Judicial (CAJ) en Chile. Clasifica materias de alta
  demanda: Arrendamiento y Ley Devuélveme mi Casa (Ley 18.101/21.461), Derecho de
  Familia (Alimentos, Cuidado Personal, Divorcio, Mediación previa - Ley 19.968) y
  Tercerías de Posesión frente a embargos ejecutivos (CPC).
argument-hint: "[describe la consulta del usuario, situación socioeconómica o materia]"
---

# /client-intake (Atención y Triage de Clínica Jurídica — Chile)

1. Cargar perfil de la clínica jurídica o servicio de asistencia pro bono (`legal-clinic/CLAUDE.md`).
2. Identificar la materia principal: **Arrendamiento**, **Familia**, **Laboral**, **Tercerías Civiles** o **Vecinal/Consumidor**.
3. Verificar presupuestos de admisibilidad y requisitos procesales previos (ej. mediación familiar frustrada obligatoria en materias de familia).
4. Estructurar la ficha de atención socio-jurídica y definir la estrategia de patrocinio o derivación.

---

## 1. Materias de Alta Frecuencia en Asistencia Jurídica en Chile

### A. Juicios de Arrendamiento y Ley "Devuélveme mi Casa" (Ley N° 21.461 y Ley N° 18.101)
* **Procedimiento Monitorio de Cobro de Rentas y Restitución:** Requiere contrato de arriendo (escrito o verbal con comprobantes de pago) y rentas/gastos comunes impagos.
* **Medida Cautelar de Restitución Anticipada:** Procedente en casos de destrucción grave del inmueble o uso indebido.

### B. Derecho de Familia (Ley N° 19.968)
* **Pensión de Alimentos (Ley N° 14.908 / Registro Nacional de Deudores Ley N° 21.389):** Cómputo de necesidades del alimentario vs. capacidad económica de ambos progenitores. Fijación en Unidades Tributarias Mensuales (UTM).
* **Mediación Previa Obligatoria:** Requisito indispensable de procesabilidad. La demanda no es admisible sin el **Certificado de Mediación Frustrada** emitido por mediador acreditado.
* **Divorcio (Ley N° 19.947):** Mutuo acuerdo (1 año de cese de convivencia acreditado) o Unilateral (3 años de cese de convivencia acreditado con prueba documental o judicial). Compensación económica.

### C. Tercerías de Posesión y Dominio (CPC)
* En juicios ejecutivos civiles cuando se traba embargo sobre bienes muebles en el domicilio del deudor pero que pertenecen a un tercero conviviente o familiar.
* Requisito de interposición oportuna antes del remate, acompañando boletas, facturas o guías a nombre del tercerista y lista de testigos.

---

## Formato de Ficha de Atención Clínica

```markdown
# FICHA DE ATENCIÓN SOCIO-JURÍDICA — CLÍNICA JURÍDICA
**N° de Ficha:** [ID] | **Fecha de Atención:** [Fecha]
**Postulante / Alumno/a:** [Nombre] | **Profesor/a Guía:** [Nombre Abogado/a]

---

### 1. Antecedentes del Usuario/a
- **Nombre Completo:** [Nombre], RUT: [XX.XXX.XXX-X]
- **Domicilio y Comuna:** [Dirección, Comuna] | **Contacto:** [Teléfono / Correo]
- **Calificación Socioeconómica:** [RSH / Nivel de Vulnerabilidad / Aprobado Pro Bono]

---

### 2. Materia y Pretensión Jurídica
- **Rama:** [Arrendamiento / Alimentos / Cuidado Personal / Divorcio / Tercería de Posesión]
- **Pretensión:** [Ej. Obtener la restitución de inmueble por no pago de rentas / Regularizar alimentos en UTM]

---

### 3. Checklist de Requisitos y Documentos Recibidos
- [ ] Cédula de identidad vigente.
- [ ] Certificado de Mediación Frustrada (si es materia de Familia).
- [ ] Contrato de arriendo / Certificado de dominio vigente / Boletas de servicios.
- [ ] Certificados de nacimiento de hijos menores de edad (si aplica).

---

### 4. Diagnóstico y Plan de Acción
- **Viabilidad Jurídica:** [🟢 ALTA / 🟡 MEDIA / 🔴 INADMISIBLE O PRESCRITO]
- **Acción Procesal Recomendada:** [Redactar demanda monitoria / Interponer tercería / Solicitar mediación].
```
