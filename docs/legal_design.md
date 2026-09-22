# 🎨 Principios de Legal Design de Open Legal Chile

Este documento dice de dónde salen los principios de diseño legal que adoptamos, cómo se traduce cada
uno a una regla concreta de este repositorio, y cómo se verifica que se cumple. No es un póster: cada
principio termina en algo que se puede cumplir o incumplir, y dice quién lo revisa.

**Alcance:** las 17 skills de `.agents/skills/`, las herramientas MCP, los documentos que genera el
sistema y la documentación del proyecto. **No cambia el fondo jurídico de nada**: cambia cómo se
presenta el trabajo, a quién está dirigido y qué se declara cuando no se pudo hacer.

---

## 1. De dónde salen los principios

1. **Legal Design Manifesto (v1)** — escrito y firmado por Rossana Ducato (UCLouvain / Université
   Saint-Louis-Bruxelles), Helena Haapio (Lexpert / Universidad de Vaasa), Margaret Hagan (Stanford
   Legal Design Lab), Monica Palmirani (Universidad de Bologna, CIRSFID), Stefania Passera
   (diseñadora de información y contratos) y Arianna Rossi (Universidad de Luxemburgo). Texto oficial
   en <https://www.legaldesignalliance.org/> (sección *The Legal Design Manifesto*). El dominio
   `legaldesignmanifesto.org`, que circula en las citas, ya no resuelve: el texto vigente se consultó
   el 22-09-2026 en el sitio de la Legal Design Alliance.
2. **Margaret Hagan / Stanford Legal Design Lab** — <https://law.stanford.edu/legal-design-lab/> y su
   libro abierto *Law by Design* (<https://lawbydesign.co/legal-design/>). Define el legal design
   como «la aplicación del diseño centrado en las personas al mundo del derecho, para que los
   sistemas jurídicos sean más humanos, usables y satisfactorios».

El Manifiesto lista **25 principios** agrupados en tres bloques: *actitudes* (human-centered,
proactivity, prevention, awareness, effectiveness, interdisciplinarity, learning by doing,
theory-based, open access, win-win), *propósitos* (clarity, applicability, trust, certainty,
value-add, scientific-based, problem based, domain-oriented) y *enfoques* (communication,
visual-first, simplification, prototyping, empirical evaluation, standards & patterns, semantic
web-oriented).

No los copiamos: los traducimos. Varios apuntan al mismo comportamiento, así que quedan **12 reglas**
(LD-01 a LD-12). El mapa completo principio → regla está en la sección 3; ninguna queda sin destino.

---

## 2. Las 12 reglas

### LD-01 — Lenguaje claro por defecto

* **Fuente:** HUMAN-CENTERED («Create information, services and systems with the community, based on
  their needs and abilities, rather than starting with the needs of lawyers and courts»); CLARITY
  («Seek clarity of the fundamental meaning and consequences of a communication, rather than just
  precise wording»); SIMPLIFICATION.
* **Regla:** todo texto que lee una persona se escribe en español de Chile corriente. La **primera
  vez** que aparece un término técnico en un documento, va seguido de su equivalencia simple entre
  paréntesis — `preclusión (se venció el plazo y ya no se puede hacer ese trámite)`. Ninguna sigla
  sin su expansión la primera vez (`RIHS (Reglamento Interno de Orden, Higiene y Seguridad)`). No
  cuenta como cumplimiento escribir «elegante» ni latinizar de más.
* **Dónde vive:** las 17 skills, el bloque *Lenguaje claro* de cada una; la clínica
  (`clinica_juridica.py`, glosario de traducción a lenguaje claro).
* **Verificación:** revisión humana con `docs/legal_design_checklist.md` cuando la salida la lee
  alguien que no es abogado. Es la regla menos automatizable y se dice: el test solo comprueba que la
  regla esté declarada en las 17 skills, no que el texto sea claro.

### LD-02 — Primero el efecto práctico, después el fundamento

* **Fuente:** CLARITY; APPLICABILITY («Foster the application of legal concepts, rights, and norms in
  everyday use, rather than just proposing legal arguments»); EFFECTIVENESS.
* **Regla:** toda salida parte por lo que significa para quien la lee: **qué debe hacer, para cuándo
  y qué pasa si no lo hace**. El fundamento normativo va después. Los plazos se escriben con fecha o
  con su regla de cómputo (días hábiles o corridos, y desde cuándo), nunca como «pronto», «a la
  brevedad» ni «en el corto plazo».
* **Dónde vive:** el campo *Salida (estructura)* de cada skill; la primera línea de cada memo, ficha
  y resumen de chat.
* **Verificación:** revisión; el test comprueba que las 17 skills declaren su estructura de salida.

### LD-03 — Estructura antes que prosa

* **Fuente:** VISUAL-FIRST («Use visual thinking and communication to secure shared understanding,
  rather than just relying on words»); COMMUNICATION («Craft information and interactions with
  purposeful design rather than just drafting it»); SIMPLIFICATION; STANDARDS & PATTERNS.
* **Regla:** si hay más de tres datos, van en tabla, lista o esquema; la prosa queda solo para lo que
  no cabe en la estructura. El orden de la salida es siempre el mismo: **conclusión → tabla → detalle
  → fuentes → compuerta**. Si un estado se marca con color o emoji, la palabra va igual
  (`VERDE / AMARILLO / ROJO`, `ALTO / MEDIO / BAJO`): el color nunca es el único portador del dato.
* **Dónde vive:** campo *Salida (estructura)* de las 17 skills.
* **Verificación:** automática — `tests/test_legal_design.py` exige el bloque de diseño con su campo
  de salida en las 17 skills.

### LD-04 — Cita o marca, nunca relleno

* **Fuente:** SEMANTIC WEB-ORIENTED («Digital solutions are made ready for the semantic web paradigm,
  supporting digital applications and multichannel-devices»); THEORY-BASED; CERTAINTY.
* **Regla:** toda afirmación normativa, jurisprudencial o administrativa sale con su cita en el
  formato de `AGENTS.md` §2 (`[BCN - Ley N° 21.643, Art. 2]`, `[CS - Rol N° 12.345-2023, Fecha:
  15-11-2023]`, `[Dictamen CGR N° E123456 (2024)]`). Lo que no se pudo verificar se **marca**, no se
  rellena: `[VERIFICAR]`, `[CITA FALTANTE]`, `[ESTADO DE VIGENCIA NO VERIFICADO]`,
  `[ILEGIBLE EN ORIGINAL: Fs. X]`, `[EVIDENCIA FALTANTE]`, `[cálculo — verificar]`, `[PLACEHOLDER]`.
  Ninguna cifra sin su fuente o su comando reproducible.
* **Dónde vive:** sección *Formato de Citación Obligatorio* de cada skill; `AGENTS.md` §2.
* **Verificación:** automática (el test exige que cada skill cite el estándar) y revisión humana del
  fondo de cada cita.

### LD-05 — Decir lo que no se pudo hacer

* **Fuente:** AWARENESS («Enable people to be aware of their rights, responsibilities, obligations
  and prohibitions, rather than just apply prescriptive norms»); CERTAINTY; EMPIRICAL EVALUATION;
  TRUST.
* **Regla:** cuando una fuente del Estado no responde, un documento está ilegible, una herramienta no
  cubre el punto o el modelo no tiene la norma, la salida lo dice **en el mismo lugar donde hubiera
  ido la respuesta**. Prohibido tapar el hueco con texto plausible, con un ejemplo «tipo» o con
  silencio. Ejemplos que ya existían en el repo y se mantienen:
  `[ESTADO DE VIGENCIA NO VERIFICADO]` (brecha normativa), `[ILEGIBLE EN ORIGINAL: Fs. X]` (OCR
  pericial), «sin silencio suplementario» (doctrina DT), «nunca fabricar discusión: usar
  `[PLACEHOLDER]`» (actas de directorio).
* **Dónde vive:** las 17 skills y los conectores.
* **Verificación:** automática en parte (`tests/test_legal_graphify_honesto.py` ya fija el principio
  «cero relleno» en el grafo) y revisión con el checklist.

### LD-06 — Compuerta de revisión humana en todo producto de alto riesgo

* **Fuente:** TRUST («Facilitate sustainable long-term relationships rather than just quick wins or
  one-shot connections»); PROACTIVITY; PREVENTION; WIN-WIN.
* **Regla:** todo producto de alto riesgo — escrito judicial, carta de despido o finiquito, informe de
  investigación Ley Karin, denuncia o informe a CGR/SMA/CMF/SII, minuta para firma, comunicación a
  contraparte — termina con la **Compuerta de Revisión Jurídica** redactada en `AGENTS.md` §5, sin
  abreviarla. Ninguna skill ni herramienta promete «listo para presentar» ni «listo para firmar»:
  entrega borrador, compuerta y lista de lo que falta.
* **Dónde vive:** las 17 skills (en las 11 de dominio legal, textual).
* **Verificación:** automática — `tests/test_legal_design.py` exige la compuerta en las 17 skills.

### LD-07 — Transparencia sobre la IA y los datos

* **Fuente:** OPEN ACCESS («We encourage open access and open data, and we recommend to make research
  outcomes available for checking, validating, and replicating the results»); AWARENESS; TRUST.
* **Regla:** cuando una respuesta pasa por un modelo de lenguaje, se dice **qué motor** se usó:
  `soberano` (local, sin salida a internet), `ollama` (local) o el proveedor externo por su nombre
  (`anthropic`, `deepseek`, `gemini`, `openai`). Lo que sale del equipo se declara antes de que salga.
  Queda prohibido decir «100 % local» si se usó un proveedor externo, y prohibido callar que se usó
  uno. `chat_engine.LegalChatEngine.chat()` ya devuelve `provider` y `model` en su respuesta, y
  `detect_provider()` responde `soberano` mientras no haya llaves configuradas.
* **Dónde vive:** README §3 (*Modos de Inferencia*), `.env.example`, `agents_runtime` (campo `mode`).
* **Verificación:** revisión con el checklist. La parte comprobable hoy es que el motor efectivamente
  declara el proveedor y que el modo por defecto es soberano.

### LD-08 — Accesibilidad de lo que se entrega

* **Fuente:** HUMAN-CENTERED; SIMPLIFICATION; VISUAL-FIRST; y el estándar de accesibilidad que Hagan
  usa en el Legal Design Lab (documentos usables con lector de pantalla, sin depender del color).
* **Regla:** los documentos que genera el sistema van en **A4** (595 × 842 pt), con jerarquía por
  encabezados y no por color, cuerpo de 11 pt o más, y **numeración visible de páginas** cuando pasan
  de una hoja. Los anexos llevan su número correlativo en la portada (`ANEXO N° 1`) y el título
  oficial del documento. Ninguna información puede existir **solo** como color o ícono.
* **Dónde vive:** `pdf_dossier_compiler.py` y `exporters.py`.
* **Verificación:** `compile_legal_dossier` fija A4 (595 × 842 pt), carátulas correlativas y
  marcadores de navegación (TOC). **La numeración de página del PDF consolidado todavía no está
  implementada** — el pie institucional no lleva número de página. Es la brecha declarada de la
  sección 5; no se declara cumplido lo que no está.

### LD-09 — Nada de prometer lo que no existe

* **Fuente:** CERTAINTY; EMPIRICAL EVALUATION; VALUE-ADD; PROBLEM BASED («Focus on real-life needs and
  problems to put aside differences and overcome disciplinary barriers»).
* **Regla:** la documentación describe **lo que el repositorio hace hoy y se puede correr**. Toda
  cifra (número de herramientas, pruebas que pasan, ahorro de tokens) se escribe junto al comando que
  la reproduce. Una función planificada, un stub o una rama sin implementar se declara como tal:
  «planificado», «no implementado», «requiere credencial»; nunca en presente como si existiera.
* **Dónde vive:** `README.md`, `docs/*.md`, `AGENTS.md`, este documento.
* **Verificación:** revisión con el checklist; el README §11 ya publica el comando de pytest junto al
  número de pruebas.

### LD-10 — Patrones reutilizables, no soluciones sueltas

* **Fuente:** STANDARDS & PATTERNS («Create new solutions with an eye towards making them replicable,
  systematized, and extensible, rather than relying on a jungle of bespoke different solutions»);
  DOMAIN-ORIENTED; INTERDISCIPLINARITY.
* **Regla:** la estructura de salida y los formatos de citación se repiten entre skills y documentos
  (conclusión → tabla → detalle → fuentes → compuerta; citas de `AGENTS.md` §2, no de la inventiva de
  cada skill). Si una skill necesita una variante, se justifica en una línea dentro de la misma skill.
* **Dónde vive:** el bloque `## 🎨 Presentación y Lenguaje Claro (Legal Design)` que se repite, con el
  mismo esqueleto, en las 17 skills.
* **Verificación:** automática — el test exige el bloque y sus campos en las 17.

### LD-11 — Probar antes de decir que sirve

* **Fuente:** PROTOTYPING («Develop solutions through quick rounds of iteration and experimentation
  rather than being planned into existence or aiming at perfection from day 1»); EMPIRICAL
  EVALUATION; SCIENTIFIC-BASED; LEARNING BY DOING.
* **Regla:** ninguna función se documenta como operativa sin una prueba en `tests/` o un caso en
  `evals/test_cases.json` que la ejercite. Las pruebas que dependen de portales del Estado se saltan
  con `pytest.skip` y **no se dan por pasadas**. La corrida de referencia se publica con su comando.
* **Dónde vive:** `tests/`, `evals/`, README §11, `.github/workflows/ci.yml`.
* **Verificación:** `.venv/bin/python -m pytest -q` (hoy: 197 pruebas verdes, más las que agrega este
  cambio).

### LD-12 — Prevención antes que juicio, y sin prometer el resultado

* **Fuente:** PROACTIVITY («Drive desirable outcomes, rather than just deal with the consequences of
  failure or punishment»); PREVENTION («Prevent problems rather than only intervene to resolve
  conflicts that have arisen»); WIN-WIN; APPLICABILITY.
* **Regla:** donde la ley chilena ofrece una salida no contenciosa — mediación previa
  (`[BCN - Ley N° 19.968, Art. 106]`), programa de cumplimiento (PdC, Ley 20.417), protocolo de
  prevención de la Ley 21.643, carta de cese y desistimiento antes de la demanda, cumplimiento
  voluntario antes del juicio ejecutivo — la salida **la nombra antes de proponer la vía judicial**,
  con su norma citada. Y el sistema no promete resultados: describe escenarios y marca toda
  estimación como estimación, nunca como pronóstico.
* **Dónde vive:** skills de litigios, contratos, ambiental, laboral y clínica.
* **Verificación:** revisión con el checklist.

---

## 3. Mapa: los 25 principios del Manifiesto → reglas de este repo

| Bloque | Principio (Manifiesto v1) | Regla |
|---|---|---|
| Actitudes | HUMAN-CENTERED | LD-01, LD-08 |
| Actitudes | PROACTIVITY | LD-06, LD-12 |
| Actitudes | PREVENTION | LD-06, LD-12 |
| Actitudes | AWARENESS | LD-05, LD-07 |
| Actitudes | EFFECTIVENESS | LD-02 |
| Actitudes | INTERDISCIPLINARITY | LD-10 |
| Actitudes | LEARNING BY DOING | LD-11 |
| Actitudes | THEORY-BASED | LD-04 |
| Actitudes | OPEN ACCESS | LD-07 |
| Actitudes | WIN-WIN | LD-06, LD-12 |
| Propósitos | CLARITY | LD-01, LD-02 |
| Propósitos | APPLICABILITY | LD-02, LD-12 |
| Propósitos | TRUST | LD-05, LD-06, LD-07 |
| Propósitos | CERTAINTY | LD-04, LD-05, LD-09 |
| Propósitos | VALUE-ADD | LD-09 |
| Propósitos | SCIENTIFIC-BASED | LD-11 |
| Propósitos | PROBLEM BASED | LD-09 |
| Propósitos | DOMAIN-ORIENTED | LD-10 |
| Enfoques | COMMUNICATION | LD-03 |
| Enfoques | VISUAL-FIRST | LD-03, LD-08 |
| Enfoques | SIMPLIFICATION | LD-01, LD-03, LD-08 |
| Enfoques | PROTOTYPING | LD-11 |
| Enfoques | EMPIRICAL EVALUATION | LD-05, LD-09, LD-11 |
| Enfoques | STANDARDS & PATTERNS | LD-03, LD-10 |
| Enfoques | SEMANTIC WEB-ORIENTED | LD-04 |

---

## 4. Cómo se aplica, archivo por archivo

| Dónde | Qué se hizo |
|---|---|
| `docs/legal_design.md` | Este documento: principios, reglas y su verificación. |
| `docs/legal_design_checklist.md` | Lista corta para revisar una skill, una herramienta o un documento antes de publicarlo. |
| `.agents/skills/**/SKILL.md` | Las 17 skills llevan el bloque `## 🎨 Presentación y Lenguaje Claro (Legal Design)` con: quién lee la salida, lenguaje claro, el término técnico con su equivalencia entre paréntesis, estructura de salida, citas y compuerta. |
| `README.md` | Sección que declara la adopción de estos principios y enlaza a este documento. |
| `tests/test_legal_design.py` | Lo que se puede verificar automáticamente: existencia y contenido de las 17 skills, compuerta y citación en cada una, ausencia de figuras de Common Law en texto propio, existencia y contenido mínimo de este documento y del checklist, enlace desde el README y vigencia de `skills-lock.json`. |

---

## 5. Límites: lo que no se aplicó, lo que no se puede verificar solo y lo que falta

Se declara, porque una de las reglas es justamente decir lo que no se pudo hacer (LD-05).

1. **La claridad real no se prueba con un test.** El test comprueba que la regla esté escrita y que el
   esqueleto de salida exista; que un texto quede claro lo decide una persona leyéndolo. Para eso está
   el checklist.
2. **Las 6 skills `ponytail-*` no son de dominio jurídico.** Son skills de simplificación de código
   (MIT, de terceros: <https://github.com/DietrichGebert/ponytail>) y están en inglés. No se reescribió
   su sustancia ni su idioma. Sí se les agregó el bloque de diseño, y su compuerta es **condicional**:
   se activa solo si la salida de esa skill termina en un producto jurídico. A una skill que solo
   borra código no se le puede exigir el refrendo de un abogado, y decir lo contrario sería ruido.
3. **Numeración de página en el PDF consolidado: pendiente.** `compile_legal_dossier` fija A4 y
   carátulas correlativas, pero el pie institucional no imprime número de página. Queda como estándar
   declarado, no como función existente.
4. **Los tres bloques en inglés del Manifiesto se citaron en su idioma original** y se tradujeron al
   lado. Traducir una cita y presentarla como si fuera el original sería inventar la fuente.
5. **INTERDISCIPLINARITY y LEARNING BY DOING quedan cubiertos solo parcialmente.** LD-10 cubre los
   formatos compartidos, y LD-11 cubre la parte de aprender haciendo pruebas; ninguno obliga a
   trabajar con gente de otras disciplinas, que es algo que el repositorio no puede forzar.
6. **No se tocó el contenido jurídico de ninguna skill**: ni causales, ni plazos, ni citas, ni
   workflows. Lo que se agregó es la capa de presentación: a quién se le habla, en qué orden, con qué
   marcas y con qué compuerta.
7. **El catálogo de especialidades cuenta más nombres que archivos.** `README.md` §8 y `AGENTS.md` §4
   catalogan 18 especialidades por nombre, pero en `.agents/skills/` hay **17 archivos `SKILL.md`**: 11
   `chilean-*` (las de dominio legal chileno) y 6 de la familia `ponytail`. Varias especialidades del
   catálogo todavía no tienen su `SKILL.md` en el disco. Se declara acá para que nadie cuente
   habilidades que no existen; crear las que faltan es otra tarea.

---

## 6. Fuentes

* **Legal Design Manifesto v1** — Ducato, R.; Haapio, H.; Hagan, M.; Palmirani, M.; Passera, S.;
  Rossi, A. Texto en <https://www.legaldesignalliance.org/> (*The Legal Design Manifesto*),
  consultado el 22-09-2026. Cita de referencia interna: *(Legal Design Manifesto, 2018)*.
* **Stanford Legal Design Lab** — Margaret Hagan, directora. <https://law.stanford.edu/legal-design-lab/>
* **Law by Design** — Margaret Hagan. <https://lawbydesign.co/legal-design/>
* **Legal Design Patterns** — Rossi, A.; Ducato, R.; Haapio, H.; Passera, S.; Palmirani, M. «Legal
  Design Patterns: New Language for Legal Information Design» (patrones de lenguaje claro, tipografía
  legible, tablas y gráficos, capas de información). Base de la regla LD-03 y LD-08.
* **Estándares internos del repo** — `AGENTS.md` §2 (citación) y §5 (compuerta de revisión);
  `CONTRIBUTING.md` (prohibición de figuras de Common Law); `README.md` §1 y §12.
