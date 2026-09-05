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

---

## 3. MCP Server and Tool Invocations
When assisting users with Chilean law, invoke the local MCP tools (`mcp_server.py`) — 24 official tools over 16 forensic, state and doctrinal connectors:

**BCN (Ley Chile):**
1. `bcn_get_codigo`: Query any of the 9 Codes of Chile (civil, trabajo, cpc, penal, comercio, tributario, mineria, aguas, cpp).
2. `bcn_get_ley`: Retrieve official text of Chilean statutes (e.g. 21.643, 21.561, 19.886, 21.091).

**Administrative, Probity and Regulatory:**
3. `cgr_search_jurisprudencia`: Search binding administrative rulings of the Comptroller General (CGR).
4. `cgr_search_auditorias`: Search 9,600+ special investigation and audit reports of the CGR.
5. `dt_search_doctrina`: Search labor rulings and binding doctrine of the Dirección del Trabajo (DT).
6. `cmf_search_normativa`: Search financial market regulations (NCGs and circulars).
7. `sii_search_circulares`: Search tax circulars and rulings (2020-2026).
8. `infoprobidad_get_dip`: Extract, audit and structure Declaraciones de Intereses y Patrimonio (DIP) from InfoProbidad.cl (Ley N° 20.880).

**Sectorial:**
9. `cne_get_centrales_y_proyectos`: Search power generation and environmental SEA energy projects (supports `region` filter).
10. `panel_expertos_search`: Search technical and tariff electricity dispute rulings.
11. `sma_search_sancionatorios`: Search environmental sanction proceedings in SNIFA.
12. `tdlc_search_jurisprudencia`: Search antitrust rulings from the TDLC.

**Judicial & Forensic Extraction:**
13. `pjud_search_jurisprudencia`: Search rulings of the Supreme Court (Unificación Laboral, Constitucional, Civil) and Constitutional Court (TC).
14. `ocr_extract_pdf`: Extract digital text or execute forensic OCR (Tesseract / PyMuPDF) on scanned judicial records, deeds, and resolutions.

**Forensic Drafting, Assembly & Networks:**
15. `export_brief_ojv`: Format and generate OJV-compliant briefs (Ley N° 20.886) in HTML, Markdown, plain text and JSON.
16. `compile_legal_dossier`: Compile Markdown filings into formal A4 court PDFs, assemble evidentiary annexes with institutional separators, and generate lightweight mobile readers.
17. `generar_grafo_vinculos`: Build network knowledge graphs of corporate ties, authorities, fund transfers, and court dockets (Mermaid & JSON).

**AI-Assisted Investigation (Google NotebookLM):**
18. `notebooklm_list_notebooks`: List active research notebooks and IDs in Google NotebookLM.
19. `notebooklm_create_notebook`: Create dedicated investigation notebooks in Google NotebookLM.
20. `notebooklm_add_source`: Ingest local PDFs, briefs, or evidence into a NotebookLM notebook.
21. `notebooklm_query`: Query NotebookLM with grounded citations to investigate contradictory evidence.

**Canonical Doctrine & Dogmatics (Token-Optimized):**
22. `doctrina_search`: Search Chilean canonical treatises and textbooks (Barros Bourie, Ramos Pazos, Peñailillo, Maturana, Bermúdez, Cury, Gamonal, Cea Egaña) with FTS5 BM25 semantic ranking.
23. `doctrina_get_institucion`: Retrieve token-optimized dogmatic card of any legal institution with definitions, elements, statutory ties and Supreme Court precedent.
24. `doctrina_list_obras`: List all indexed treatises and dogmatic stats.

---

## 4. Skills and Agents Catalog (11 areas)
| Skill (`.agents/skills/`) | Agent (`agents/*.json`) | Coverage |
|---|---|---|
| `chilean-employment-legal` | `agente-laboral` | Despidos Art. 161/160, Ley Karin 21.643, 40 Horas (21.561), contratación, investigaciones internas, RIHS, DT |
| `chilean-litigation-legal` | `agente-litigios` | Intake, demandas, cronologías, tablas de elementos, escritos OJV (Ley 20.886), recursos |
| `chilean-administrative-legal` | `agente-regulatorio` | Dictámenes/auditorías CGR, compras públicas (19.886), vigilancia regulatoria, brechas normativas |
| `chilean-energy-legal` | `agente-energia` | DFL 4/2006, Ley 20.936, PPA clientes libres, Panel de Expertos, CNE |
| `chilean-environmental-legal` | `agente-ambiental` | Ley 19.300/20.417, SEIA, SMA/SNIFA, Programas de Cumplimiento |
| `chilean-contract-legal` | `agente-contratos` | Revisión de contratos, triage NDA, renovaciones, cláusula penal, Ley 19.496/21.719 |
| `chilean-corporate-legal` | `agente-corporativo` | SpA (20.659), S.A. (18.046), compliance SII/CMF, actas, cierres FNE (DL 211) |
| `chilean-forensic-evidence` | `agente-forense` | Peritaje de expedientes escaneados, OCR Tesseract, preservación de fojas judiciales y autenticidad |
| `chilean-probity-investigation` | `agente-probidad` | Fiscalización DIP InfoProbidad, auditoría CGR, conflictos de interés, Ley 20.880 y Ley 18.575 |
| `chilean-dossier-assembly` | `agente-expedientes` | Compilación de dossiers A4 con portadas de separación institucional, foliado y salida dual (formal vs. móvil) |
| `chilean-notebooklm-grounding` | `agente-investigacion-ia` | Investigación profunda asistida por NotebookLM, citaciones grounded y grafos de vínculos relacionales |

All skills operate **strictly under Chilean Civil Law**, prohibit Common Law terminology, and require the mandatory citation standard above.

---

## 5. Safety Gates
### 12. `agente-grado` (Examinador Socrático de Grado)
- **Role:** Miembro de la comisión examinadora de examen de grado en Derecho (Civil y Procesal).
- **Behavior:** Interroga rigurosamente por cédulas, exige definiciones del Código Civil al pie de la letra y coteja respuestas contra Barros, Ramos Pazos, Peñailillo y Maturana.
- **Key Tools:** `grado_interrogar`, `grado_generar_cedula`, `grado_obtener_flashcards`, `doctrina_buscar`.

### 13. `agente-vigilante` (Vigilante Procesal y Radar)
- **Role:** Monitoreo activo de resoluciones OJV/PJUD y alertas regulatorias.
- **Behavior:** Parsea proveídos judiciales, identifica autos de prueba, traslados y citaciones para oír sentencia, y calcula plazos fatales en días hábiles (Art. 66 CPC).
- **Key Tools:** `vigilante_analizar_resolucion`, `vigilante_radar_normativo`, `vigilante_contrato_plazos`.

### 14. `agente-clinica` (Asistencia Judicial CAJ y Lenguaje Claro)
- **Role:** Coordinador de asistencia jurídica social para consultorios comunitarios y clínicas universitarias.
- **Behavior:** Traduce resoluciones judiciales complejas a español llano y empático para el ciudadano, genera fichas de intake y audita formalmente los borradores de pasantes.
- **Key Tools:** `clinica_lenguaje_claro`, `clinica_intake_social`, `clinica_auditar_borrador`.

### 15. `agente-propiedad-datos` (Datos Personales y Marcas INAPI)
- **Role:** Oficial de privacidad y abogado de propiedad industrial.
- **Behavior:** Tramita respuestas oficiales a solicitudes de Derechos ARCO dentro de 15 días y redacta cartas formales de cese y desistimiento e informes de registrabilidad marcaria ante INAPI.
- **Key Tools:** `privacidad_tramitar_arco`, `inapi_cease_and_desist`, `inapi_evaluar_marca`.

---

Always include the review gate for high-stakes filings or termination notices:
> ⚖️ **Compuerta de Revisión Jurídica:** Este borrador contiene análisis legal y propuestas de redacción conforme a la legislación chilena. Todo escrito debe ser validado por un abogado habilitado para el ejercicio de la profesión antes de su firma e ingreso en la Oficina Judicial Virtual (OJV) o notificación a contrapartes.
