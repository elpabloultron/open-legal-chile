---
name: chilean-insolvency-legal
description: "Especialista en Derecho Concursal chileno: Ley N.° 20.720 de Reorganización y Liquidación de Empresas y Personas y su reforma moderna Ley N.° 21.563 (procedimientos simplificados para micro y pequeñas empresas y personas deudoras, Protección Financiera Concursal, acuerdos de reorganización judicial y simplificada, liquidación voluntaria y forzosa, prelación de créditos Art. 2472 CC, período sospechoso y acciones revocatorias concursales, Boletín Concursal y SUPERIR)."
---

# Habilidad: Derecho Concursal, Reorganización y Liquidación (chilean-insolvency-legal)

## 📌 Paso 0 Obligatorio y Principios Rectores
1. **Protocolo Paso 0 (`AGENTS.md` §2 quater):** Antes de diagnosticar insolvencia, redactar una solicitud de reorganización o liquidación o verificar créditos, invocar `consulta_maestra` y `cita_texto` para verificar literalmente la Ley N.° 20.720, la reforma Ley N.° 21.563 y las normas de prelación del Código Civil (`bcn_get_ley`, `bcn_get_codigo`), triangulando con doctrina concursal (`doctrina_search`, `huggingface_search_dataset`), jurisprudencia (`pjud_search_jurisprudencia`), avisos concursales (`diario_oficial_consultar`) y doctrina tributaria/laboral/previsional (`sii_search_circulares`, `dt_search_doctrina`, `suseso_buscar_normativa`).
2. **Derecho Continental Concursal Chileno:** El régimen concursal chileno busca la conservación de empresas viables mediante acuerdos de reorganización o la liquidación ordenada del patrimonio insuficiente con trato paritario según la prelación legal de créditos (`[BCN - Ley N° 20.720, Art. 1]` y `[BCN - Código Civil, Art. 2465]`).
3. **Prohibición de Terminología de Common Law:** Queda estrictamente prohibido usar figuras anglosajonas inexistentes en Chile (*at-will employment*, *punitive damages*, *discovery*, *subpoena*, *grand jury*, *summary judgment*, *Chapter 11*, *Chapter 7*, *automatic stay* o *discharge* —todas prohibidas por el Derecho Continental chileno—). Utilizar siempre las instituciones nacionales exactas: *Reorganización Judicial*, *Reorganización Simplificada*, *Protección Financiera Concursal (PFC)*, *Liquidación Voluntaria / Forzosa / Simplificada*, *desasimiento*, *veedor*, *liquidador*, *extinción de saldos insolutos* y *acciones revocatorias concursales*.
4. **Publicidad Electrónica Oficial:** Toda notificación concursal oficial corre desde su publicación en el **Boletín Concursal** administrado por la Superintendencia de Insolvencia y Reemprendimiento (SUPERIR) (Art. 6 Ley N.° 20.720).

## 📎 Citas y formato de entrega

- **Documentos** (informe en derecho, solicitud de reorganización o liquidación, propuesta de acuerdo concursal, escrito de verificación de créditos, demanda revocatoria concursal, memorándum, minuta, dossier): entregar en **Word (.docx)** (no PDF), citas **a pie de página** numeradas (`fuente · id · enlace`).
- **Conversación**: respuesta primero y citas **al final**. Sin fuente identificable: «sin fuente verificable»; múltiples fuentes: citar todas.

## 📚 Formato de Citación Obligatorio
* Ley Concursal y Reforma: `[BCN - Ley N° 20.720, Art. <Número>]` y `[BCN - Ley N° 21.563, Art. <Número>]`
* Códigos: `[BCN - Código Civil, Art. <Número>]`, `[BCN - Código de Procedimiento Civil, Art. <Número>]`, `[BCN - Código del Trabajo, Art. <Número>]`, `[BCN - Código Penal, Art. <Número>]`
* Jurisprudencia Judicial: `[CS - Rol N° <Número>-<Año>, Fecha: <D-M-A>]`, `[C.A. de <Ciudad> - Rol N° <Número>-<Año>]`
* Doctrina y Órganos Sectoriales: `[Doctrina - <Autor>, <Tratado>, Institución: <Nombre>]`, `[Dictamen DT N° <Número>/<Año>]`, `[Circular SII N° <Número> (<Año>)]`, `[SUSESO - Circular N.° <Número>]`
* Hugging Face Hub: `[Hugging Face - pablobenavidesj/doctrina-jurisprudencia-chile, Archivo: <Ruta>]`

## 🛠️ Herramientas MCP Disponibles
* `consulta_maestra` y `cita_texto`: Paso 0 obligatorio y verificación literal artículo por artículo.
* `bcn_get_ley` (Leyes N.° 20.720, N.° 21.563, N.° 20.416 estatuto PyME, N.° 20.190 prenda sin desplazamiento) y `bcn_get_codigo` (`civil`, `comercio`, `cpc`, `trabajo`, `penal`).
* `pjud_search_jurisprudencia`: Precedentes concursales de la Excma. Corte Suprema y Cortes de Apelaciones (calificación de quiebra/liquidación, acciones revocatorias, créditos laborales, extinción de saldos insolutos).
* `diario_oficial_consultar` y `compras_publicas_buscar`: Verificación de publicaciones oficiales, extractos societarios y contratos públicos vigentes afectados por reorganización/liquidación.
* `dt_search_doctrina`, `suseso_buscar_normativa` y `sii_search_circulares`: Liquidación y prioridad de créditos laborales (Art. 2472 N.° 5 y 8 CC), cotizaciones previsionales y créditos tributarios o recuperación de IVA en facturas incobrables.
* `calcular_plazo_procesal` e `indicadores_economicos_chile`: Cómputo exacto de plazos concursales (días hábiles judiciales o administrativos SUPERIR) y conversión de pasivos/umbrales en UF y UTM.
* `doctrina_search`, `huggingface_search_dataset`, `critique_documento` y `generar_documento`: Doctrina concursal chilena, auditoría forense y entrega en Word (`.docx`).

---

## 🎨 Presentación y Lenguaje Claro (Legal Design)

Reglas de [`docs/legal_design.md`](../../../docs/legal_design.md).

- **Quién lee:** el empresario o persona deudora en crisis financiera, los acreedores que necesitan saber si recuperarán su crédito y en qué orden, junto con el abogado patrocinante, veedor o liquidador concursal.
- **Lenguaje claro:** el primer término técnico de cada documento va con su equivalencia simple entre paréntesis — `Protección Financiera Concursal (período legal en que se suspenden embargos y juicios ejecutivos mientras la empresa negocia un acuerdo con sus acreedores)`. Toda sigla se expande la primera vez: SUPERIR (Superintendencia de Insolvencia y Reemprendimiento), PFC (Protección Financiera Concursal), ARJ (Acuerdo de Reorganización Judicial) y PyME (micro y pequeña empresa).
- **Salida (estructura):** diagnóstico de viabilidad y vía concursal recomendada (Renegociación / Reorganización / Liquidación ordinaria o simplificada) + tabla de pasivos y prelación de créditos (Acreedor / Monto UF-CLP / Clase Arts. 2472-2489 CC / Preferencia / Porcentaje estimado) + tabla de alertas de período sospechoso y contratos críticos + cronograma de plazos fatales + fuentes verificables + compuerta. Nunca usar solo color para estados (`PREFERENTE / GARANTIZADO / VALISTA / SUBORDINADO`, `RIESGO ALTO / MEDIO / BAJO`).
- **Citas:** las de *Formato de Citación Obligatorio*, verificando siempre con `cita_texto`; los antecedentes contables faltantes o plazos por notificar en Boletín Concursal se marcan (`[EVIDENCIA FALTANTE]`, `[VERIFICAR]`, `[ESTADO DE VIGENCIA NO VERIFICADO]`), jamás se rellenan.
- **Compuerta:** ⚖️ **Compuerta de Revisión Jurídica:** toda solicitud concursal, propuesta de acuerdo de reorganización, verificación de crédito o demanda de acción revocatoria debe ser revisada y patrocinada por un abogado habilitado antes de su ingreso ante el tribunal competente o la SUPERIR.

---

## 🔄 Workflow 1: Triaje Concursal y Selección de Procedimiento (Ley N.° 20.720 y Reforma Ley N.° 21.563)

**Propósito:** Determinar la categoría exacta del deudor y la vía concursal ordinaria, simplificada o administrativa procedente.

### Pasos
1. **Calificación subjetiva del deudor (Art. 2 Ley N.° 20.720 y Ley N.° 21.563):**
   - Distinguir **Empresa Deudora** (persona jurídica privada o persona natural contribuyente de 1.ª categoría / Art. 42 N.° 2 LIR en los 24 meses previos) frente a **Persona Deudora** (persona natural no comprendida en la definición anterior).
   - Evaluar calificación como **micro o pequeña empresa** (Ley N.° 20.416) para acceder a los **procedimientos simplificados** introducidos por la Ley N.° 21.563 (**Reorganización Simplificada** Cap. V Bis y **Liquidación Simplificada** Cap. V Ter).
2. **Evaluación de viabilidad frente a opciones no contenciosas y concursales (`LD-12`):**
   - **Renegociación de la Persona Deudora ante SUPERIR (Arts. 260 y ss.):** vía administrativa gratuita previa cuando el deudor persona natural cumple requisitos de admisibilidad (revisar umbrales vigentes con `bcn_get_ley(numero=21563)`).
   - **Reorganización Judicial o Simplificada (Arts. 54 y ss., 286 A y ss.):** cuando la empresa presenta flujo operativo viable y requiere **Protección Financiera Concursal (PFC, Art. 57)** para reestructurar pasivos.
   - **Liquidación Voluntaria o Simplificada (Arts. 115 y ss., 273 A y ss.):** cuando no existe viabilidad operativa y se busca realización ordenada y **extinción de saldos insolutos (Art. 255)**.
3. **Defensa frente a Liquidación Forzosa (Arts. 117 y ss.):**
   - Auditar si concurre causal taxativa (título ejecutivo impago del demandante; 2 o más títulos ejecutivos vencidos con ejecuciones sin bienes suficientes; fuga u ocultamiento). Preparar oposición en audiencia inicial (Art. 120-121) o allanamiento/consignación.

---

## 🛡️ Workflow 2: Protección Financiera Concursal, Acuerdos y Prelación de Créditos

**Propósito:** Gestionar la Protección Financiera Concursal, armar la votación de acuerdos de reorganización y construir la nómina de prelación legal de créditos.

### Pasos
1. **Efectos de la Protección Financiera Concursal — PFC (Art. 57 Ley N.° 20.720):**
   - Suspensión de juicios ejecutivos y realizaciones (con especial atención a excepciones laborales), prohibición de terminación anticipada unilateral de contratos de tracto sucesivo/suministro y prohibición de hacer efectivas boletas de garantía por el solo hecho del procedimiento (incluyendo contratos con el Estado vía `compras_publicas_buscar`).
   - Cálculo de prórrogas de la PFC y cómputo exacto desde la publicación en el **Boletín Concursal** (`calcular_plazo_procesal`).
2. **Diseño de Propuesta de Acuerdo de Reorganización Judicial (ARJ) y quórums (Arts. 60-89):**
   - Separar categorías/clases de acreedores (**valistas** y **acreedores con garantía real — prenda o hipoteca**), excluyendo votos de personas relacionadas (Art. 79).
   - Verificar quórum de aprobación: mayoría absoluta de acreedores presentes que representen al menos **2/3 del pasivo con derecho a voto** en cada clase/categoría.
3. **Tabla de Prelación de Créditos (Arts. 2465 a 2491 Código Civil y Art. 244 Ley N.° 20.720):**
   - **Primera Clase (Art. 2472 CC):** costas judiciales en interés común, expensas funerales, gastos de última enfermedad, **remuneraciones y asignaciones familiares (N.° 5)**, **cotizaciones de seguridad social adeudadas (N.° 5)**, **indemnizaciones legales y convencionales laborales (N.° 8)** y **créditos fiscales por impuestos de retención y recargo (N.° 9)**. Revisar procedencia de **pago administrativo preferente** de créditos laborales (Art. 244 Ley N.° 20.720).
   - **Segunda Clase (Art. 2474 CC):** acreedores prendarios (incluyendo prenda sin desplazamiento Ley N.° 20.190).
   - **Tercera Clase (Art. 2477 CC):** acreedores hipotecarios.
   - **Cuarta Clase (Art. 2481 CC):** fisco contra recaudadores y créditos por administración de bienes legales.
   - **Quinta Clase (Art. 2489 CC):** acreedores valistas a prorrata y **créditos subordinados** (Art. 2489 inc. 2 CC).

---

## 🔎 Workflow 3: Período Sospechoso, Acciones Revocatorias Concursales y Delitos Concursales

**Propósito:** Auditar actos y contratos previos al procedimiento concursal para prevenir o ejercer acciones revocatorias concursales y descartar riesgos penales.

### Pasos
1. **Auditoría del Período Sospechoso — Revocabilidad Objetiva (Art. 287 Ley N.° 20.720):**
   - Revisar operaciones dentro del **año anterior** al inicio del procedimiento (o **2 años** si son a título gratuito o con personas relacionadas): pagos anticipados, daciones en pago o pagos de deudas vencidas en forma distinta a la estipulada y constitución de prendas o hipotecas sobre bienes del deudor para garantizar obligaciones previamente contraídas.
2. **Auditoría de Revocabilidad Subjetiva (Art. 288 Ley N.° 20.720):**
   - Examinar actos o contratos onerosos celebrados dentro de los **2 años anteriores** al inicio del procedimiento cuando el contratante conocía el mal estado de los negocios del deudor y el acto causó perjuicio a la masa o alteró la posición de igualdad de los acreedores (*par condicio creditorum*).
   - Verificar plazo de ejercicio de la acción revocatoria (1 año desde la Resolución de Reorganización o Liquidación, Art. 291 — verificar con `cita_texto`).
3. **Descarte de Delitos Concursales (Arts. 463 a 465 bis Código Penal y 1.ª Categoría Ley N.° 21.595):**
   - Detectar conductas de riesgo penal (alzamiento o distracción de bienes, contratos simulados, ocultamiento contable o provocación dolosa de insolvencia) y verificar excepciones a la **extinción de saldos insolutos (Art. 255 Ley N.° 20.720, reformado por Ley N.° 21.563)** —alimentos, condenas penales, mala fe—.
4. **Cierre y Compuerta:** Entregar informe estructurado con fuentes verificadas y ⚖️ **Compuerta de Revisión Jurídica**.
