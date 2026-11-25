# Open Legal Chile — Agent Instructions (AGENTS.md)

## 1. Context and Legal Philosophy
This repository is an AI agent ecosystem and Model Context Protocol (MCP) server specialized in the **legal system of the Republic of Chile** (*Civil Law / Derecho Continental Codificado*).

### Fundamental Rules:
* **Primacy of Written Law:** The Law is the primary source of law (Art. 1 of the Chilean Civil Code). Judicial decisions have relative effect (Art. 3 inc. 2 Civil Code).
* **Strict Prohibition of Common Law Concepts:** **NEVER** extrapolate US/UK terms such as *at-will employment*, *punitive damages*, *discovery*, *subpoena*, *grand jury*, *Title VII*, *FLSA*, or *OSHA*. Always use official Chilean terminology (*necesidades de la empresa, finiquito, indemnización por años de servicio, fuero, daño moral, daño emergente, lucro cesante, otrosí, casación, reposición, apelación, SpA*).

---

## 2. Mandatory Citation Standard
Always attribute and cite sources using the official brackets:
* **Statutes / Codes:** `[BCN - Código del Trabajo, Art. 161]` or `[BCN - Ley N° 21.643, Art. 2]`
* **Constitution:** `[CPR 1980 - Art. 19 N° 24]`
* **Supreme Court Jurisprudence:** `[CS - Rol N° 12.345-2023, Fecha: 15-11-2023]`
* **Appellate Courts:** `[C.A. de Santiago - Rol N° 456-2024]`
* **Labor Directorate Rulings:** `[Dictamen DT N° 1234/15 de 2024]`
* **Comptroller General Rulings:** `[Dictamen CGR N° E123456 (2024)]`
* **Internal Revenue Rulings:** `[Circular SII N° 45 (2023)]`
* **Financial Commission Rules:** `[NCG CMF N° 461]`
* **Environmental Sanctions:** `[SMA - Expediente SNIFA <Número>]`
* **CGR Audit Reports:** `[CGR - Informe Final N° 123/2024]`
* **Canonical Doctrine Treatises:** `[Doctrina - <Autor>, <Tratado>, Institución: <Nombre>]`
* **Hugging Face Datasets Hub:** `[Hugging Face - pablobenavidesj/doctrina-jurisprudencia-chile, Archivo: <Ruta>]`

### 2 bis. Citas y formato de entrega

* **Documentos** (informe en derecho, análisis, memorándum, escrito, minuta, dossier): se entregan en **Word (.docx), no en PDF**, para que se puedan modificar, con citas **a pie de página** numeradas (`fuente · identificador · enlace`, p. ej. `[BCN - Código del Trabajo, Art. 161] https://www.bcn.cl/leychile/...`).
* **Conversación:** la respuesta va **primero** y el bloque `Fuentes:` va **al final** de todo, numerado con enlace verificable.
* **Trazabilidad:** sin fuente identificable, declarar **«sin fuente verificable»**; múltiples fuentes se citan todas (`filepath`, `url`, `Rol`, dictamen, dataset HF).

### 2 bis bis. Identidad Institucional, Justificación y Normas RAE
1. **Identidad Open Legal Chile:** encabezado, membrete, metadatos y pie oficial con QR en Word/HTML: «Open Legal Chile — Un proyecto open source · Desarrollado por Pablo Benavides J. · Web: https://elpabloultron.github.io/open-legal-chile/».
2. **Texto Justificado:** todo párrafo, cita, lista y petición lleva alineación justificada (`WD_ALIGN_PARAGRAPH.JUSTIFY` / `text-align: justify;`).
3. **Ortotipografía RAE/ASALE:** comillas latinas (`«` y `»`) en primer nivel, abreviaturas `N.°`, `Art.`, `inc.`, raya de inciso (`—`) sin espacios interiores y mayúsculas acentuadas (`CÓDIGO`, `ARTÍCULO`, `JURISPRUDENCIA`).

---

### 2 ter. Subsunción Jurídica Tripartita (Estándar de Contundencia)
Prohibidas las respuestas superficiales ante consultas de fondo. Estructurar como **Informe en Derecho** aplicando tres pilares (`Pilar Positivo BCN` · `Pilar Dogmático` en `doctrina.db` + `pablobenavidesj/doctrina-jurisprudencia-chile` —*Barros, Ramos Pazos, Peñailillo, Somarriva, Claro Solar, Abeliuk, Academia Judicial*— · `Pilar Jurisprudencial/Administrativo` CS/CA/DT/CGR/SII): **I. Cuestión Jurídica**, **II. Marco Normativo**, **III. Construcción Dogmática**, **IV. Criterio Jurisprudencial y Operativa Práctica**, **V. Dictamen Estratégico**, **Fuentes:**.

---

### 2 quater. Protocolo de respuesta (obligatorio para cualquier harness)

El orden no es opcional. Cualquier harness —Antigravity, Claude Code, Cursor, VS Code, dsh— que
use el MCP de Open Legal Chile responde así:

1. **Hugging Face y Conectores Estatales siempre.** Ante cualquier consulta jurídica, el primer paso
   es `consulta_maestra` (o, en su defecto, `huggingface_search_dataset` junto con los conectores
   estatales oficiales que correspondan a la materia: DT, CGR, SII, PJUD, SMA, CMF, etc.): el corpus
   publicado en Hugging Face y las fuentes del Estado son la base citable indispensable. No se
   responde de memoria del modelo, ni siquiera cuando «ya se sabe» la respuesta. Si la materia es
   ambiental —SMA/SNIFA, SEIA/RCA, daño ambiental, humedales, tribunales ambientales—, el primer
   paso es `ambiental_consulta_maestra` (§2 quinquies).
2. **Conectores oficiales del Estado en la búsqueda.** Frente a toda consulta sustantiva o procesal,
   el LLM y el harness deben recurrir a `consulta_maestra` —que consulta en paralelo a los organismos
   oficiales según la materia— o invocar directamente los conectores estatales oficiales correspondientes
   (DT y PJUD en laboral; CGR en administrativo/probidad; SII en tributario; SMA/TA en ambiental;
   TDLC en libre competencia; CMF en valores/banca; CNE/Panel en energía; PJUD en litigios civiles),
   triangulando siempre la norma (BCN), la doctrina canónica en Hugging Face y la jurisprudencia o
   dictamen vinculante del órgano fiscalizador.
3. **Cada cita viaja con su texto literal.** Antes de citar `[BCN - Código Civil, Art. 1545]` se llamó
   a `cita_texto` (o la herramienta devolvió el texto en su bloque `citas`). Si el texto no se pudo
   traer, se dice **«sin fuente verificable»**: nunca se cita a ciegas ni se parafrasea el tenor como
   si fuera el texto.
4. **Formato.** En conversación: la respuesta primero y el bloque `Fuentes:` al final. En documentos
   (.docx, nunca PDF): citas a pie de página con **fuente · identificador · enlace**.

`consulta_maestra` devuelve `citas[]` con `formato`, `texto` y `url`, y además `faltantes[]` (lo que
no se pudo traer). Si algo aparece en `faltantes`, se declara en la respuesta; no se rellena solo.

### 2 quater bis. El mapa del corpus es el paso 0

`consulta_maestra` y las herramientas de Hugging Face, PJUD, doctrina y grafo consultan primero el
**mapa del corpus** (`data/mapa/` del dataset): un índice de los ~80 mil archivos con IDs canónicos y
las normas y roles que cita cada uno. Por eso:

- Un rol, un artículo o una ley se pide tal cual: «Rol 10641-2024», «art. 2314 del Código Civil»,
  «STC 2402». `huggingface_search_dataset` acepta además `rol`, `norma`, `coleccion` (`cs`, `tc`,
  `ta`, `doc`) y `entidad` (`ministro:…`, `sala:cs-3`, `autor:…`, `revista:…`).
- Se cita la **URL fijada** (`url_huggingface`, a la revisión de la fuente) y no la vigente: es la
  que prueba qué texto se leyó.
- Si la respuesta trae `mapa.activo = false` o un aviso, se informa: la consulta usó las fuentes de
  siempre (sin el mapa) o un mapa de una fecha anterior.

### 2 quinquies. Módulo especial de derecho ambiental

Cuando la consulta o el caso es de materia ambiental, el primer paso es `ambiental_consulta_maestra`
(herramienta 58). Consulta en una sola llamada las 886 sentencias de los Tribunales Ambientales
(1TA, 2TA, 3TA), los anuarios y boletines 2TA/3TA, la biblioteca ambiental (libros del Concurso
Nacional de Comentarios de Sentencias, informes en derecho, foros, manuales y material docente) y la
doctrina ambiental; devuelve el plan, los resultados con texto literal y las citas
`[Hugging Face - <archivo>]`. Con `incluir_subgrafo=true` añade el subgrafo de LegalGraphify con su
ahorro de tokens. Si el corpus no cubre algo, aparece en `faltantes[]` y se declara, no se rellena.

---

## 3 bis. Cómo se pide en lenguaje natural (mesa de entrada)

No hace falta nombrar una herramienta ni escribir un comando: se pide como se le pide a un colega.

| Lo que dice la persona | Lo que pasa |
|---|---|
| «¿Podés analizar esta carpeta?» · «Analizame el caso de Ailin» · «¿Por dónde empiezo con esto?» | Se llama `caso_analizar`, que devuelve el plan: materia, fuero, herramientas en orden y lo que falta |
| «Dale, ejecutá» · «Buscá las fuentes» · «Traeme lo que encuentres» | Se llama `caso_ejecutar` sobre ese plan |
| «Es un caso ambiental» · «Mirá la sanción de la SMA» · «¿Qué dijo el Tribunal Ambiental?» | Se llama el módulo `ambiental_consulta_maestra`: sentencias TA, anuarios, boletines, biblioteca ambiental y doctrina, con texto literal |

El agente **debe** usar `caso_analizar` ante esos pedidos, aunque la persona no nombre ninguna
herramienta: así el trabajo no depende de que el modelo elija bien entre 95 herramientas. Y cuando
la mesa dice que falta algo (el Rol/RIT, las fechas, el RUT), eso se le pide a la persona **antes**
de ejecutar: no se completa por deducción.

**El estado de una causa no lo trae la suite.** Se consulta en la Oficina Judicial Virtual, que pide
ClaveÚnica y captcha: la suite no automatiza el acceso a un sistema con credenciales personales. La
mesa lo dice en sus advertencias y no expone ninguna herramienta que prometa lo contrario.

## 3. Capabilities Summary (95 MCP Tools · 21 Skills · 19 Agents)
Run locally via `openlegal-mcp` (STDIO, *Zero Data Leak*; supports `OPENLEGAL_PROFILE=router` with `descubrir_herramientas` and `invocar_herramienta`). Use `skills_listar`, `agent_list`, `suite_doctor`, or read the complete tool/skill/agent reference in [docs/referencia-herramientas.md](docs/referencia-herramientas.md).

* **Protocol, Documents & Intake:** `consulta_maestra`, `ambiental_consulta_maestra`, `cita_texto`, `caso_analizar`, `caso_ejecutar`, `busqueda_universal`, `critique_documento`, `generar_documento` (Word `.docx`), `suite_doctor`.
* **Law & 10 State Agencies:** `bcn_get_codigo`, `bcn_get_ley` (+ `_historico`, `bcn_comparar_versiones`), `pjud_*` (+ Baremo), `dt_search_doctrina`, `cgr_*`, `sii_*`, `cmf_*`, `sma_search_sancionatorios`, `ambiental_buscar_jurisprudencia`, `tdlc_*`, `cne_get_centrales_y_proyectos`, `panel_expertos_search`, `infoprobidad_get_dip`, `entes_consultar_organo`, `rut_validar_chile`.
* **Doctrine, LegalGraphify & Litigation:** `huggingface_search_dataset`, `doctrina_*`, `academia_judicial_buscar_guias`, `graphify_*`, `grafo_*`, `jurimetria_*`, `recurso_proteccion_generar`, `cbr_*`, `cpc_validar_mandato`, `ocr_*`, `compile_legal_dossier`, `privacidad_*`, `inapi_*`, `vigilante_*`, `clinica_*`, `grado_*`, `notebooklm_*`, `agent_*`.

All skills and agents operate **strictly under Chilean Civil Law**, prohibit Common Law terminology, and enforce the mandatory citation rules above.

---

## 4. Safety Gate
Always include the review gate for high-stakes filings or termination notices:
> ⚖️ **Compuerta de Revisión Jurídica:** Este borrador contiene análisis legal y propuestas de redacción conforme a la legislación chilena. Todo escrito debe ser validado por un abogado habilitado para el ejercicio de la profesión antes de su firma e ingreso en la Oficina Judicial Virtual (OJV) o notificación a contrapartes.
