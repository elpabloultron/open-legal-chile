---
name: chilean-probity-investigation
description: Auditoría de probidad administrativa, cruce de Declaraciones de Intereses y Patrimonio (DIP) de InfoProbidad, detección de conflictos de interés y fiscalización bajo la Ley 20.880 y Ley 18.575.
---

# Habilidad: Auditoría de Probidad y Patrimonio Público (chilean-probity-investigation)

## 📌 Principios Rectores
1. **Principio de Probidad Administrativa:** Consagrado en el Art. 8° de la Constitución y Art. 52 de la Ley N° 18.575 (Bases Generales de la Administración del Estado). Implica una conducta funcionaria moralmente intachable y una entrega honesta y leal al desempeño de su cargo.
2. **Publicidad Obligatoria de Patrimonio e Intereses:** Ley N° 20.880 y su reglamento. Todo sujeto pasivo debe declarar oportunamente sus actividades profesionales, participaciones en sociedades, bienes inmuebles, vehículos y pasivos relevantes.
3. **Inhabilidades e Incompatibilidades:** Prohibición estricta de intervenir en decisiones donde exista interés personal, de cónyuge o parientes hasta el tercer grado de consanguinidad o segundo de afinidad (Art. 62 N° 6 Ley 18.575).

## 📚 Formato de Citación Obligatorio
* Declaración DIP: `[InfoProbidad - Declaración ID <ID>, Autoridad: <Nombre>]`
* Ley de Probidad: `[BCN - Ley N° 20.880, Art. <Número>]`
* Ley de Bases Generales: `[BCN - Ley N° 18.575, Art. <Número>]`
* Dictamen Contraloría: `[Dictamen CGR N° <Número> de <Año>]`
* Informe de Auditoría CGR: `[CGR - Informe Final de Auditoría N° <Número>/<Año>]`

## 🛠️ Herramientas MCP Disponibles
* `infoprobidad_get_dip`: Descarga y estructura la Declaración de Intereses y Patrimonio de la autoridad.
* `cgr_search_auditorias`: Cruza hallazgos con los informes de auditoría e investigaciones especiales de la CGR.
* `cgr_search_jurisprudencia`: Jurisprudencia administrativa sobre faltas a la probidad, destituciones y sanciones.
* `bcn_get_ley`: Consulta Ley 20.880, Ley 18.575, Ley 19.886 y Ley 21.094.

---

## 🏛️ Workflow 1: Auditoría Patrimonial Integral

### Pasos
1. **Extracción de la Declaración:** Invocar `infoprobidad_get_dip` ingresando la URL o identificador de la autoridad en InfoProbidad.
2. **Revisión de Secciones Clave:**
   - **Actividades y Empleos Anteriores:** Cotejar si existió paso de regulador a regulado ("puerta giratoria") o asesorías incompatibles.
   - **Bienes Inmuebles:** Analizar avalúo fiscal, fecha de adquisición y congruencia con ingresos declarados.
   - **Sociedades y Derechos:** Identificar RUTs de sociedades donde tenga participación él o sus familiares.
   - **Pasivos:** Detectar créditos o deudas con proveedores del Estado o instituciones intervenidas.
3. **Cruce con Compras Públicas y Auditorías:**
   - Buscar en `cgr_search_auditorias` si el organismo público donde ejerce la autoridad ha sido auditado por contrataciones irregulares.
4. **Matriz de Hallazgos:** Redactar reporte estructurado con hechos contrastados y tipificación normativa.

### Compuertas de Seguridad
- Presunción de inocencia administrativa: distinguir entre irregularidades formales (errores de llenado) y faltas graves a la probidad (ocultamiento deliberado de sociedades o conflictos directos).
- ⚖️ **Compuerta de Revisión:** Todo informe pericial o denuncia ante la CGR debe ser visado antes de su presentación oficial.
