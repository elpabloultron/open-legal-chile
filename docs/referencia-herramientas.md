# Open Legal Chile — Referencia Completa de Herramientas, Skills y Agentes

Catálogo completo de las **95 herramientas MCP**, **21 skills jurídicas** (`.agents/skills/`) y **19 agentes autónomos** (`agents/*.json`) de Open Legal Chile. Consultar también `skills_listar`, `agent_list`, `suite_doctor` o `descubrir_herramientas` (en perfil `OPENLEGAL_PROFILE=router`).

---

## 1. Catálogo por Área y Dominio (MCP Server `mcp_server.py` · `servidor/`)

**BCN (Ley Chile):**
1. `bcn_get_codigo`: Consulta los Códigos de la República (`civil`, `trabajo`, `cpc`, `penal`, `comercio`, `tributario`, `mineria`, `aguas`, `cpp`).
2. `bcn_get_ley`: Texto oficial vigente de leyes chilenas (ej. `21.643`, `21.561`, `19.886`, `21.091`).
3. `bcn_get_ley_historica`: Texto histórico de una ley a fecha específica (`YYYY-MM-DD`).
4. `bcn_get_codigo_historico`: Texto histórico de un Código a fecha específica (`YYYY-MM-DD`).
5. `bcn_comparar_versiones`: Comparación entre versiones históricas/vigentes de una norma.

**Administrativo, Probidad y Regulatorio:**
6. `cgr_search_jurisprudencia`: Dictámenes vinculantes de la Contraloría General de la República (CGR).
7. `cgr_search_auditorias`: Más de 9 600 informes finales de auditoría e investigaciones especiales de la CGR.
8. `dt_search_doctrina`: Ordinarios y dictámenes vinculantes de la Dirección del Trabajo (DT).
9. `cmf_search_normativa`: Normas de Carácter General (NCG) y circulares de la CMF.
10. `cmf_buscar_sanciones`: Sanciones administrativas de la CMF.
11. `sii_search_circulares`: Circulares tributarias del SII (2020–2026).
12. `sii_buscar_resoluciones_y_oficios`, `sii_oficios_por_anio`, `sii_descargar_oficio`, `sii_leer_documento`, `sii_actos_regionales`, `sii_convenios_internacionales`, `sii_jurisprudencia_judicial`.
13. `infoprobidad_get_dip`: Declaraciones de Intereses y Patrimonio (DIP) desde InfoProbidad.cl (Ley N.° 20.880).
14. `entes_consultar_organo`: Competencias orgánicas, leyes orgánicas y recursos administrativos/judiciales.
15. `rut_validar_chile`: Validación Módulo 11 y formato chileno de RUT / RUN.

**Sectoriales (Energía, Ambiental, Libre Competencia):**
16. `cne_get_centrales_y_proyectos`: Centrales de generación eléctrica y proyectos SEA (filtra por `region`).
17. `panel_expertos_search`: Dictámenes técnicos y tarifarios del Panel de Expertos Eléctrico.
18. `sma_search_sancionatorios`: Expedientes sancionatorios ambientales en SNIFA (SMA).
19. `ambiental_buscar_jurisprudencia`: Sentencias de Tribunales Ambientales (1TA, 2TA, 3TA).
20. `ambiental_consulta_maestra`: Módulo especial ambiental (886 sentencias TA, anuarios/boletines 2TA/3TA, biblioteca ambiental, doctrina y subgrafo opcional).
21. `tdlc_search_jurisprudencia` y `tdlc_buscar_icg_y_dictamenes`: Jurisprudencia, ICG y dictámenes del TDLC.

**Judicial, Inmobiliario CBR, Privacidad, Marcas y Evidencia Forense:**
22. `pjud_search_jurisprudencia`: 70 523 sentencias CS, 966 TC, portales PJUD y Baremo de Daño Moral (UF/CLP).
23. `pjud_analizar_sentencia`: Desglose Art. 170 CPC (expositiva, considerativa, resolutiva).
24. `pjud_interpretar_proveido`: Proveídos OJV y cómputo de cargas y plazos procesales.
25. `recurso_proteccion_generar`: Acción constitucional estandarizada conforme al Auto Acordado CS Acta N.° 94-2015.
26. `cbr_estudio_titulos` y `cbr_checklist_documentos`: Cadena de dominio decenal (10 años, Arts. 2510–2511 CC) y checklist registral CBR.
27. `cpc_validar_mandato`: Verificación de mandato judicial y facultades especiales (Art. 7 CPC).
28. `ocr_plan_documento` y `ocr_extract_pdf`: Planificación y extracción OCR de expedientes PDF escaneados.
29. `export_brief_ojv`, `compile_legal_dossier`, `generar_documento`: Exportación de escritos/informes (Word `.docx` editable, HTML/MD y dossier PDF formal A4).
30. `privacidad_anonimizar_documento`, `privacidad_tramitar_arco`, `verificar_citas_escrito`.
31. `inapi_evaluar_marca`, `inapi_cease_and_desist`.
32. `vigilante_analizar_resolucion`, `vigilante_radar_normativo`, `vigilante_contrato_plazos`.
33. `clinica_lenguaje_claro`, `clinica_intake_social`, `clinica_auditar_borrador`.
34. `grado_interrogar`, `grado_generar_cedula`, `grado_obtener_flashcards`.
35. `notebooklm_list_notebooks`, `notebooklm_create_notebook`, `notebooklm_add_source`, `notebooklm_query`, `generar_grafo_vinculos`.

**Doctrina Canónica, Hugging Face Hub, LegalGraphify y Jurimetría:**
36. `huggingface_search_dataset`: Búsqueda en `pablobenavidesj/doctrina-jurisprudencia-chile` (vía mapa del corpus cuando está activo).
37. `academia_judicial_buscar_guias` y `biblioteca_compilar_manifiesto`.
38. `doctrina_search`, `doctrina_get_institucion`, `doctrina_list_obras`, `doctrina_ingestar_documento`.
39. `grafo_ver_corpus`, `grafo_ver_caso`, `graphify_resumen_comunidades`, `graphify_consulta_subgrafo`, `graphify_trazar_camino`, `graphify_explicar_institucion`, `graphify_analizar_impacto`, `graphify_god_nodes`.
40. `jurimetria_analizar_corpus` y `jurimetria_exportar_investigacion` (CSV, GraphML, Parquet, muestra estratificada para $\kappa$ de Cohen, `referencia.bib`).

**Protocolo (§2 quater), Mesa de Entrada, Agentes y Suite:**
41. `consulta_maestra`, `cita_texto`, `busqueda_universal`, `critique_documento`.
42. `caso_analizar`, `caso_ejecutar`, `entrevista_estudio`.
43. `agent_list`, `agent_run`, `agent_export_subagents`.
44. `suite_doctor`, `suite_instalar`, `suite_telemetria_stats`, `suite_verificar_actualizacion`, `suite_auto_update`, `skills_listar`, `skill_ver`, `descubrir_herramientas`, `invocar_herramienta`.

---

## 2. Catálogo de Skills y Agentes (21 Skills · 19 Agentes)

| Skill (`.agents/skills/`) | Agente (`agents/*.json`) | Cobertura principal |
|---|---|---|
| `chilean-employment-legal` | `agente-laboral` | Despidos Art. 161/160 CT, Ley Karin 21.643, 40 Horas (21.561), investigaciones internas, finiquitos, DT |
| `chilean-litigation-legal` | `agente-litigios` | Intake, demandas, recurso de protección (Acta N.° 94-2015), cronologías, escritos OJV |
| `chilean-real-estate-cbr` | `agente-inmobiliario` | Estudio de títulos decenal (10 años), inscripciones CBR, gravámenes, mandatos Art. 7 CPC |
| `chilean-dogmatic-graphify` | `agente-dogmatico` | Subsunción dogmática, doctrina canónica, subgrafos LegalGraphify y análisis de impacto |
| `chilean-doctrine-ingestion` | `agente-ingestor` | Ingesta y normalización RAE/ASALE (`.pdf`, `.docx`, `.txt`, `.md`), FTS5 y grafo |
| `chilean-administrative-legal` | `agente-regulatorio` | Dictámenes/auditorías CGR, compras públicas (Ley 19.886/21.634), vigilancia regulatoria |
| `chilean-energy-legal` | `agente-energia` | DFL 4/2006, Ley 20.936, PPA clientes libres, Panel de Expertos, CNE |
| `chilean-environmental-legal` | `agente-ambiental` | Ley 19.300/20.417, SEIA, SMA/SNIFA, Programas de Cumplimiento |
| `chilean-contract-legal` | `agente-contratos` | Revisión de contratos, NDA, renovaciones, cláusula penal, Ley 19.496/21.719 |
| `chilean-corporate-legal` | `agente-corporativo` | SpA (20.659), S.A. (18.046), compliance SII/CMF, actas, cierres FNE (DL 211) |
| `chilean-forensic-evidence` | `agente-forense` | Peritaje de expedientes escaneados, OCR RapidOCR/Tesseract, preservación de fojas |
| `chilean-probity-investigation` | `agente-probidad` | Fiscalización DIP InfoProbidad, auditoría CGR, conflictos de interés (Ley 20.880 / 18.575) |
| `chilean-dossier-assembly` | `agente-expedientes` | Dossiers A4 institucionales con separadores, foliado, marcadores TOC y salida dual |
| `chilean-notebooklm-grounding` | `agente-investigacion-ia` | Investigación probatoria asistida por NotebookLM y grafos de vínculos |
| `chilean-socratic-bar-exam` | `agente-grado` | Simulador socrático de examen de grado (Civil y Procesal) con cédulas y flashcards |
| `chilean-case-intake` | `agente-mesa` | Mesa de entrada en lenguaje natural: clasificación chilena, plan de herramientas y gaps |
| `chilean-docket-watcher` | `agente-vigilante` | Interpretación de proveídos OJV/PJUD y cómputo de plazos fatales (Art. 66 CPC) |
| `chilean-legal-clinic` | `agente-clinica` | Asistencia jurídica social (CAJ), Lenguaje Claro y auditoría de borradores |
| `chilean-privacy-ip` | `agente-propiedad-datos` | Derechos ARCO+ (Ley 19.628 / 21.719), factibilidad marcaria INAPI y cese y desistimiento |
| `chilean-contradictorio-goldfish` | *(vía `critique_documento`)* | Auditoría contradictoria de contexto cero (Ministro Relator, Contraparte y Auditor BCN/HF) |
| `chilean-workspace-legal-flow` | *(orquestación Workspace)* | Flujo entre análisis forense chileno y Drive/Docs/Sheets/Calendar |

Todas las skills operan estrictamente bajo el Derecho Continental chileno (prohibida toda terminología de *Common Law*).

---

## 3. Especializaciones de Agentes Destacadas

* `agente-grado`: interrogación socrática por cédulas (Civil y Procesal) cotejada contra Barros, Ramos Pazos, Peñailillo y Maturana (`grado_*`, `doctrina_search`).
* `agente-vigilante`: monitoreo OJV/PJUD, proveídos y plazos fatales en días hábiles Art. 66 CPC (`vigilante_*`).
* `agente-clinica`: asistencia social CAJ, traducción a Lenguaje Claro y revisión de borradores (`clinica_*`).
* `agente-propiedad-datos`: respuestas ARCO+ y marcas INAPI (`privacidad_*`, `inapi_*`).
* `agente-inmobiliario`: estudio de títulos decenal (10 años) y mandatos Art. 7 CPC (`cbr_*`, `cpc_validar_mandato`).
* `agente-dogmatico`: subsunción dogmática y subgrafos LegalGraphify (`graphify_*`, `doctrina_*`).
* `agente-ingestor`: ingesta y normalización RAE/ASALE al índice FTS5 y grafo (`doctrina_ingestar_documento`, `ocr_extract_pdf`).
