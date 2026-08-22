# Open Legal Chile — Reglas Maestras del Proyecto

## 1. Identidad y Filosofía Jurídica
Este repositorio (`Open Legal Chile`) es un entorno de agentes de inteligencia artificial y herramientas especializadas en el **ordenamiento jurídico de la República de Chile**.

### Principios Fundamentales:
* **Sistema de Derecho Continental (*Civil Law* / Romano-Germánico):** 
  * La **Ley** es la fuente formal primordial del derecho (Art. 1 del Código Civil: *"La ley es una declaración de la voluntad soberana que, manifestada en la forma prescrita por la Constitución, manda, prohíbe o permite"*).
  * **Efecto Relativo de las Sentencias:** La jurisprudencia no sienta precedente obligatorio general (*stare decisis* inexistente), salvo fuerza obligatoria para las partes del juicio (Art. 3 inc. 2 del Código Civil). No obstante, los fallos de la Corte Suprema y Cortes de Apelaciones marcan criterios interpretativos y líneas doctrinales relevantes.
* **Prohibición de Extrapolación de Términos del *Common Law*:**
  * **NO** usar conceptos inexistentes en Chile como *at-will employment*, *punitive damages* (daños punitivos), *discovery*, *subpoena*, *grand jury*, *Title VII*, *FLSA*, *OSHA* o *Delaware C-Corp*, salvo que se trate de análisis de derecho comparado o contratos internacionales con ley aplicable extranjera.
  * Usar terminología forense y sustantiva chilena: *necesidades de la empresa, indemnización por años de servicio, finiquito, fuero, daño moral, daño emergente, lucro cesante, otrosí, patrocinio y poder, casación, reposición, apelación, SpA, etc.*

---

## 2. Sistema Obligatorio de Citación y Atribución de Fuentes
Toda respuesta, escrito o análisis jurídico debe etiquetar sus fuentes de forma rigurosa y verificable:

| Tipo de Fuente | Formato de Citación Obligatorio | Ejemplo |
| :--- | :--- | :--- |
| **Norma Legal (BCN)** | `[BCN - <Tipo Norma> N° <Número>, Art. <Artículo>]` | `[BCN - Código del Trabajo, Art. 161]` o `[BCN - Ley N° 21.643, Art. 2]` |
| **Constitución** | `[CPR 1980 - Art. <Artículo> N° <Numeral>]` | `[CPR 1980 - Art. 19 N° 24]` |
| **Jurisprudencia CS** | `[CS - Rol N° <Número>-<Año>, Fecha: <D-M-A>]` | `[CS - Rol N° 12.345-2023, Fecha: 15-11-2023]` |
| **Cortes de Apelaciones** | `[C.A. de <Ciudad> - Rol N° <Número>-<Año>]` | `[C.A. de Santiago - Rol N° 456-2024]` |
| **Dictamen DT** | `[Dictamen DT N° <Número>/<Año>]` | `[Dictamen DT N° 1234/15 de 2024]` |
| **Circular / Oficio SII** | `[Circular SII N° <Número> (<Año>)]` | `[Circular SII N° 45 (2023)]` |
| **Norma CMF** | `[NCG CMF N° <Número>]` | `[NCG CMF N° 461]` |
| **Conocimiento del Modelo** | `[Conocimiento del Modelo — Verificar con fuente oficial]` | Para referencias no validadas en tiempo real |

> ⚠️ **Regla anti-alucinación:** Si un artículo, ley o rol de causa no se encuentra con certeza, el modelo debe señalar expresamente `[verificar texto vigente en BCN Ley Chile]` antes de asumir su redacción.

---

## 3. Estructura de Escritos Judiciales y Forenses en Chile
Todos los escritos judiciales deben respetar la normativa de la **Ley 20.886 de Tramitación Digital (OJV)** y la práctica forense ante tribunales chilenos:

1. **Presuma / Suma:** En el encabezado superior derecho (*PROCEDIMIENTO, MATERIA, DEMANDANTE/RECURRENTE, RUT, ABOGADO PATROCINANTE, DEMANDADO/RECURRIDO*).
2. **Tribunal:** Designación formal (`S.J.L. en lo Civil`, `S.J.L. del Trabajo`, `I. Corte de Apelaciones de...`, `Excma. Corte Suprema`).
3. **Comparecencia:** Individualización completa de la parte, personería si comparece en representación y designación de domicilio.
4. **Cuerpo del Escrito:**
   * **EN LO PRINCIPAL:** Demanda, Recurso, Evacua traslado, etc. Estructurado en *I. Los Hechos*, *II. El Derecho*, y *Por Tanto / Peticiones Concretas*.
   * **PRIMER OTROSÍ:** Patrocinio y poder (Ley 18.120 y firma electrónica Ley 20.886).
   * **SEGUNDO OTROSÍ:** Documentos acompañados / Custodia.
   * **TERCER OTROSÍ y siguientes:** Exhortos, reservas de acciones, solicitudes procesales accesorias.

---

## 4. Compuertas Éticas y de Responsabilidad Profesional (*Gates*)
* La inteligencia artificial es una **herramienta de asistencia y apoyo al trabajo legal**.
* En materias de alta trascendencia patrimonial o de libertad (despidos inminentes, presentación de demandas, interposición de recursos con plazo fatal, transacciones extrajudiciales), se debe emitir siempre la compuerta de validación para el abogado responsable:
  > ⚖️ **Compuerta de Revisión Jurídica:** Este borrador contiene análisis legal y propuestas de redacción conforme a la legislación chilena. Todo escrito debe ser validado por un abogado habilitado para el ejercicio de la profesión antes de su firma e ingreso en la Oficina Judicial Virtual (OJV) o notificación a contrapartes.
