/* Open Legal Chile — Taxonomía Oficial de las 8 Áreas del Derecho y Simulaciones Explicativas */
window.OLC_AREAS_DATA = [
  {
    id: "civil",
    shortName: "Litigación, Penal & Familia",
    name: "Litigación Civil, Penal, Familia & OJV",
    tagline: "Demandas, protección, litigación penal (CPP), alimentos UTM/RNDP, Baremo PJUD, MCP Apps interactivas y auditoría Goldfish.",
    badge: "Área 01 · Litigación, Penal y Familia",
    summary: "Acompaña todo el ciclo del litigio chileno bajo la Ley N.° 20.886: litigación civil y constitucional, litigación penal acusatoria (CPP Art. 140 y recurso de nulidad), Tribunales de Familia (alimentos en UTM Ley N.° 14.908, Registro Nacional de Deudores Ley N.° 21.389 y VIF Ley N.° 20.066), calculadoras deterministas (plazos CPC, cuantías y Baremo PJUD), MCP App de tablero forense y revisión adversarial Goldfish.",
    connectors: ["BCN Ley Chile (CPC, CC, CPP, CPR)", "PJUD Corte Suprema (70.523 fallos)", "Tribunal Constitucional", "Baremo Daño Moral PJUD (17 vínculos)", "Calculadoras Forenses + MCP App ui://"],
    agents: ["agente-litigios", "agente-penal", "agente-familia", "agente-vigilante", "agente-forense", "agente-expedientes"],
    skills: ["chilean-litigation-legal", "chilean-criminal-litigation", "chilean-family-legal", "chilean-contradictorio-goldfish", "chilean-docket-watcher", "chilean-forensic-evidence"],
    deliverables: [
      "Demanda civil, recurso de protección (Acta N.° 94-2015), defensa penal CPP (cautelares Art. 140 / nulidad Arts. 372–387) o demanda de familia (alimentos UTM, RDR, VIF) en Word (.docx).",
      "Tablero visual e interactivo en MCP App (app_abrir_expediente y app_abrir_calculadoras) + informe de daño moral cruzado con Baremo PJUD.",
      "Auditoría forense Goldfish (revisión sin sesgo desde 3 roles: Ministro Relator, Contraparte y Auditor BCN).",
      "Cómputo de plazos fatales en días hábiles judiciales (Arts. 59 y 66 CPC) y dossiers foliados A4."
    ],
    trainingTitle: "Taller de Litigación Civil, OJV y Auditoría Goldfish",
    trainingFocus: "Cómo estructurar causas complejas, redactar escritos con citas verificables en Word (.docx), cuantificar daño moral con el Baremo PJUD y detectar debilidades probatorias antes de presentar.",
    simulation: {
      scenario: "Estudio litigante prepara demanda de indemnización por responsabilidad extracontractual y daño moral por fallecimiento en accidente carretero.",
      prompt: "«Analiza la carpeta del accidente, triangula Arts. 2314 y 2329 del Código Civil con Barros Bourie, cuantifica daño moral para cónyuge e hijo según el Baremo PJUD y prepara el borrador en Word (.docx) pasando por auditoría Goldfish.»",
      steps: [
        {
          label: "Consulta local (Zero Data Leak)",
          title: "1. Recepción privada del expediente en tu equipo",
          detail: "La carpeta de prueba y el relato del cliente se procesan 100 % en tu propio computador mediante tu asistente IA (Antigravity, Claude Code o Cursor). Ningún documento privado se sube a servidores de Open Legal Chile.",
          chips: ["caso_analizar", "ocr_extract_pdf", "100 % local en tu PC"],
          outputLabel: "Plan detectado automáticamente",
          output: "Materia: Responsabilidad Civil Extracontractual · Fuero: Juzgado de Letras en lo Civil · Reglas activas: Arts. 2314 y 2329 CC, Ley N.° 20.886 (OJV), Baremo PJUD."
        },
        {
          label: "Triangulación oficial",
          title: "2. Cruce simultáneo de ley, doctrina y Baremo PJUD",
          detail: "consulta_maestra obtiene el tenor literal de BCN Ley Chile, extrae el subgrafo dogmático de Barros Bourie con 99,9 % menos tokens y consulta el Baremo Estadístico PJUD (398 casos Cónyuge · 549 casos Hijo).",
          chips: ["[BCN - Código Civil, Art. 2314]", "[Doctrina - Barros Bourie]", "[PJUD Baremo Daño Moral]"],
          outputLabel: "Fuentes verificadas con texto literal",
          output: "Mediana 1.ª instancia Cónyuge: 1.156,21 UF (398 fallos) · Hijo(a): 836,54 UF (549 fallos) · Criterio CS: acción de daño moral por rebote es originaria (Art. 2329 CC)."
        },
        {
          label: "Auditoría Goldfish",
          title: "3. Control de citas y examen contradictorio previo",
          detail: "El modo Goldfish evalúa el borrador con contexto cero desde la perspectiva de un Ministro Relator, la contraparte litigante y un auditor de citas BCN/HF, eliminando el sesgo de confirmación.",
          chips: ["critique_documento (goldfish)", "verificar_citas_escrito", "0 alucinaciones"],
          outputLabel: "Hallazgos preventivos detectados",
          output: "✓ Todas las normas verificadas contra BCN · ⚠ Sugerencia: reforzar nexo causal y acompañar certificado de vínculo afectivo antes del término probatorio."
        },
        {
          label: "Entregable Word .docx",
          title: "4. Borrador forense editable con citas a pie de página",
          detail: "generar_documento entrega un Word (.docx) en formato A4 justificado, con presuma, comparecencia, hechos, derecho con texto normativo literal, otrosíes (Ley N.° 18.120) y compuerta de validación del abogado.",
          chips: ["demanda_civil.docx", "Citas a pie de página", "Norma RAE/ASALE"],
          outputLabel: "Listo para revisión del abogado habilitado",
          output: "Archivo editable generado en tu carpeta local · Incluye cuadro comparativo del Baremo PJUD y lista de verificación documental previa a OJV."
        }
      ]
    }
  },
  {
    id: "laboral",
    shortName: "Laboral & Ley Karin",
    name: "Derecho del Trabajo & Ley Karin",
    tagline: "Despidos Art. 160/161, investigaciones Ley N.° 21.643, jornada 40 Horas, dictámenes de la Dirección del Trabajo y tutela laboral.",
    badge: "Área 02 · Laboral y Cumplimiento",
    summary: "Conecta directamente el Código del Trabajo vigente en BCN con la doctrina administrativa vinculante de la Dirección del Trabajo (DT), la seguridad social SUSESO (Ley N.° 16.744) y la Cuarta Sala de la Corte Suprema para asesorar despidos, defensas de tutela, protocolos Ley Karin y cálculo determinista de finiquitos e indemnizaciones.",
    connectors: ["BCN Ley Chile (Código del Trabajo, Ley 21.643, Ley 21.561)", "Dirección del Trabajo (Dictámenes y Ordinarios)", "SUSESO (Seguridad Social y Ley N.° 16.744)", "PJUD Corte Suprema (Cuarta Sala Laboral)", "Calculadora de Finiquito CT + MCP App ui://"],
    agents: ["agente-laboral", "agente-litigios", "agente-vigilante"],
    skills: ["chilean-employment-legal", "chilean-contradictorio-goldfish", "chilean-case-intake"],
    deliverables: [
      "Informe en derecho en Word (.docx) sobre procedencia de causal de despido (Art. 161 inc. 1.° o Art. 160), tope 11 años / 90 UF y recargos Art. 168 CT (30 %–100 %).",
      "Liquidación determinista con calcular_finiquito_laboral / app_abrir_calculadoras y verificación de criterios SUSESO sobre accidentes del trabajo.",
      "Evaluación de protocolo e investigación interna bajo Ley Karin (Ley N.° 21.643) con medidas de resguardo y plazos DT.",
      "Análisis de validez del descuento AFC en finiquito según criterio unificado de la Cuarta Sala CS.",
      "Borrador de demanda o contestación laboral y cronología de pruebas para audiencia preparatoria."
    ],
    trainingTitle: "Taller de IA Aplicada a Derecho Laboral y Ley Karin",
    trainingFocus: "Automatización responsable de cartas de despido, informes de investigación interna Ley N.° 21.643, búsqueda de dictámenes DT y control de riesgos ante tutela laboral.",
    simulation: {
      scenario: "Gerencia legal evalúa despido por necesidades de la empresa (Art. 161) y consulta riesgo de impugnación y procedencia del descuento AFC.",
      prompt: "«Evalúa la suficiencia de los hechos de reestructuración bajo el Art. 161 del Código del Trabajo, revisa dictámenes de la DT sobre descuento AFC y doctrina reciente de la Cuarta Sala, y emite un informe ejecutivo en Word (.docx).»",
      steps: [
        {
          label: "Consulta local",
          title: "1. Intake confidencial de antecedentes laborales",
          detail: "Los contratos, anexos y respaldo financiero de la reestructuración permanecen en el entorno local del abogado o fiscalía, protegiendo datos sensibles de trabajadores (Ley N.° 21.719).",
          chips: ["caso_analizar", "privacidad_anonimizar_documento", "Reserva total"],
          outputLabel: "Encuadre normativo inicial",
          output: "Materia: Terminación de Contrato (Art. 161 inc. 1.° CT) · Riesgos a auditar: carta genérica (Art. 162 y 454 N.° 1 CT), fuero, descuento AFC (Art. 13 Ley N.° 19.728)."
        },
        {
          label: "Triangulación DT + CS",
          title: "2. Búsqueda paralela en BCN, DT y Cuarta Sala CS",
          detail: "consulta_maestra consulta el tenor literal de los Arts. 161, 162 y 168 CT en BCN, recupera dictámenes vigentes en dt_search_doctrina y verifica fallos de unificación de la Cuarta Sala en PJUD.",
          chips: ["[BCN - Código del Trabajo, Art. 161]", "[Dictamen DT]", "[CS - Cuarta Sala]"],
          outputLabel: "Criterio unificado verificado",
          output: "Si el despido por Art. 161 se declara injustificado, la Cuarta Sala CS ha unificado que el empleador debe restituir el descuento del aporte patronal AFC (Art. 13 Ley N.° 19.728) más recargo del 30 %."
        },
        {
          label: "Chequeo probatorio",
          title: "3. Auditoría de la carta de despido antes de notificar",
          detail: "Verifica que la carta exponga hechos económicos concretos, permanentes y ajenos a la mera voluntad del empleador, previniendo la preclusión probatoria del Art. 454 N.° 1 CT.",
          chips: ["critique_documento (5d)", "Control Art. 454 N.° 1 CT", "Riesgo cuantificado"],
          outputLabel: "Matriz de riesgo preventivo",
          output: "⚠ Riesgo alto si la carta solo invoca «baja de ventas» sin cifras ni causalidad con el cargo específico · Se recomiendan 4 antecedentes contables obligatorios."
        },
        {
          label: "Entregable Word .docx",
          title: "4. Informe en derecho + matriz de decisión en Word",
          detail: "Entrega el informe en Word (.docx) con citas literales a pie de página, escenarios comparados (finiquito con acuerdo vs. contingencia judicial) y lista de verificación de formalidades.",
          chips: ["informe_art161.docx", "Citas BCN + DT + CS", "Editable"],
          outputLabel: "Listo para sesión de directorio o RR. HH.",
          output: "Documento corporativo editable con dictamen estratégico, cursos de acción y cita exacta a cada dictamen de la Dirección del Trabajo."
        }
      ]
    }
  },
  {
    id: "ambiental",
    shortName: "Ambiental & Energía",
    name: "Derecho Ambiental, SEIA & Energía",
    tagline: "886 sentencias de los Tribunales Ambientales (1TA, 2TA, 3TA), sancionatorios SMA/SNIFA, Programas de Cumplimiento, PPA y Panel de Expertos.",
    badge: "Área 03 · Ambiental y Regulación Energética",
    summary: "Cuenta con un módulo maestro especializado (ambiental_consulta_maestra) que integra las 886 sentencias de los Tribunales Ambientales, anuarios, boletines, biblioteca ambiental y expedientes SNIFA de la SMA, junto a conectores de la CNE y el Panel de Expertos Eléctrico.",
    connectors: ["Tribunales Ambientales (886 fallos 1TA/2TA/3TA)", "SMA / SNIFA (Sancionatorios y PdC)", "Anuarios, Boletines y Biblioteca Ambiental HF", "CNE y Panel de Expertos Eléctrico", "BCN (Ley 19.300, LO-SMA, DFL 4/2006)"],
    agents: ["agente-ambiental", "agente-energia", "agente-dogmatico"],
    skills: ["chilean-environmental-legal", "chilean-energy-legal", "chilean-dogmatic-graphify"],
    deliverables: [
      "Análisis estratégico frente a formulación de cargos SMA: descargos vs. Programa de Cumplimiento (PdC, Art. 42 LO-SMA).",
      "Informe jurisprudencial comparado de 1TA, 2TA y 3TA sobre reclamaciones RCA, invalidación o daño ambiental.",
      "Revisión de contratos PPA para clientes libres y discrepancias técnicas ante el Panel de Expertos.",
      "Mapeo de precedentes de humedales urbanos (Ley N.° 21.202) y criterios del SEIA."
    ],
    trainingTitle: "Taller Especializado en IA para Derecho Ambiental y Energía",
    trainingFocus: "Búsqueda jurisprudencial avanzada en 1TA/2TA/3TA, auditoría de expedientes sancionatorios SNIFA, diseño de Programas de Cumplimiento y contratos eléctricos PPA.",
    simulation: {
      scenario: "Titular de proyecto enfrenta formulación de cargos de la SMA por presunto incumplimiento de RCA y evalúa presentar Programa de Cumplimiento.",
      prompt: "«Ejecuta ambiental_consulta_maestra sobre aprobación de Programas de Cumplimiento por incumplimiento de RCA con efectos negativos subsanables, cruza expedientes SNIFA similares y criterios del 2TA y 3TA.»",
      steps: [
        {
          label: "Módulo maestro ambiental",
          title: "1. Activación de ambiental_consulta_maestra",
          detail: "El sistema detecta materia ambiental y prioriza el corpus especializado de 886 sentencias TA, 78 boletines/anuarios, 87 obras de biblioteca ambiental y la base SNIFA de la SMA.",
          chips: ["ambiental_consulta_maestra", "sma_search_sancionatorios", "Ley N.° 20.417"],
          outputLabel: "Cobertura activada en 1 llamada",
          output: "Cruce simultáneo: Arts. 42 LO-SMA y D.S. N.° 30/2012 MMA · 1TA/2TA/3TA · Biblioteca Ambiental HF · Expedientes SNIFA por infracción equivalente."
        },
        {
          label: "Jurisprudencia 1TA/2TA/3TA",
          title: "2. Contraste de criterios de integridad, eficacia y verificabilidad",
          detail: "Extrae los párrafos literales exactos donde los Tribunales Ambientales revisaron el estándar de descarte o contención de efectos negativos en un PdC.",
          chips: ["[2TA / 3TA - Sentencia]", "[SMA - Expediente SNIFA]", "[Hugging Face - Biblioteca TA]"],
          outputLabel: "Doctrina y fallos alineados",
          output: "Estándar consolidado: el PdC exige descripción técnica fundada de efectos negativos y metas medibles con plazos fatales; de lo contrario la SMA lo rechaza."
        },
        {
          label: "Cruce energético / técnico",
          title: "3. Integración con plazos fatales y normativa sectorial",
          detail: "Verifica el plazo de 10 días hábiles para presentar PdC (Art. 42 LO-SMA) o 15 días hábiles para descargos (Art. 49) y cruza normativa sectorial CNE/DFL 4 si corresponde a proyecto eléctrico.",
          chips: ["Plazos Ley N.° 19.880", "cne_get_centrales_y_proyectos", "panel_expertos_search"],
          outputLabel: "Calendario regulatorio crítico",
          output: "Plazo PdC: 10 días hábiles desde notificación (ampliable hasta 5 días antes del vencimiento) · Checklist de 6 requisitos del D.S. N.° 30/2012."
        },
        {
          label: "Entregable Word .docx",
          title: "4. Minuta estratégica SMA en Word editable",
          detail: "Entrega minuta técnica y jurídica en Word (.docx) con tabla comparativa de precedentes 2TA/3TA, matriz de acciones del PdC y citas verificables a pie de página.",
          chips: ["minuta_sma_pdc.docx", "Citas SNIFA + TA", "100 % verificable"],
          outputLabel: "Preparado para comité técnico-legal",
          output: "Documento listo para alinear consultores ambientales y abogados defensores antes de la reunión de asistencia al cumplimiento ante la SMA."
        }
      ]
    }
  },
  {
    id: "administrativo",
    shortName: "Administrativo & CGR",
    name: "Administrativo, Probidad & Compras Públicas",
    tagline: "Dictámenes e informes CGR, Mercado Público OCDS + cruce InfoProbidad, amparos CPLT/Lobby y Diario Oficial.",
    badge: "Área 04 · Sector Público y Regulación",
    summary: "Diseñada para fiscalías públicas, municipalidades, litigantes administrativos y proveedores del Estado. Cruza el Estatuto Administrativo, la Ley N.° 19.880, Mercado Público / ChileCompra OCDS (Leyes N.° 19.886 y 21.634), más de 9.600 informes de auditoría CGR, amparos de Transparencia (CPLT) e InfoLobby, Diario Oficial y Declaraciones de Intereses y Patrimonio (InfoProbidad).",
    connectors: ["Contraloría General (Dictámenes y +9.600 Auditorías)", "Mercado Público / ChileCompra OCDS + cruce InfoProbidad", "CPLT (Amparos Ley N.° 20.285 e InfoLobby Ley N.° 20.730)", "Diario Oficial (Normas y Extractos Societarios)", "BCN + PJUD Corte Suprema (Tercera Sala)"],
    agents: ["agente-regulatorio", "agente-probidad", "agente-vigilante"],
    skills: ["chilean-administrative-legal", "chilean-probity-investigation", "chilean-docket-watcher"],
    deliverables: [
      "Informe jurídico administrativo con jurisprudencia vinculante de la CGR y criterios de la Tercera Sala CS (ej. confianza legítima).",
      "Auditoría de conflictos de interés cruzando declaraciones DIP de InfoProbidad y normativa Ley N.° 20.880 / 18.575.",
      "Revisión de bases de licitación, trato directo y recursos de impugnación bajo Ley N.° 19.886 / 21.634.",
      "Análisis de vicios de legalidad en sumarios administrativos y plazos de la Ley N.° 19.880."
    ],
    trainingTitle: "Taller de IA Soberana para Sector Público, CGR y Compras Públicas",
    trainingFocus: "Redacción de decretos, oficios e informes en derecho con dictámenes CGR verificados, fiscalización de probidad y gestión de licitaciones bajo Ley N.° 21.634.",
    simulation: {
      scenario: "Dirección jurídica municipal analiza la no renovación de una contrata con más de dos anualidades y revisa el estándar vigente de confianza legítima.",
      prompt: "«Triangula el criterio actual de la Contraloría General y la Tercera Sala de la Corte Suprema sobre confianza legítima en contratas, cita dictámenes CGR y fallos CS verificados y redacta minuta de riesgo.»",
      steps: [
        {
          label: "Consulta CGR + CS",
          title: "1. Detección de conflicto entre CGR y Tercera Sala",
          detail: "consulta_maestra identifica materia administrativa y consulta en paralelo el Estatuto Administrativo en BCN, dictámenes de la CGR y las líneas jurisprudenciales de la Tercera Sala CS.",
          chips: ["cgr_search_jurisprudencia", "pjud_search_jurisprudencia (Tercera)", "Ley N.° 19.880"],
          outputLabel: "Fuentes oficiales conectadas",
          output: "BCN Ley N.° 18.883 y Ley N.° 19.880 (Arts. 11 y 41) · Dictámenes CGR sobre confianza legítima · Líneas jurisprudenciales Tercera Sala Corte Suprema."
        },
        {
          label: "Contraste de estándares",
          title: "2. Separación nítida de criterio administrativo vs. judicial",
          detail: "Diferencia con precisión el umbral exigido por la jurisprudencia administrativa y judicial, y verifica el deber de fundamentación reforzada del acto administrativo terminal.",
          chips: ["[Dictamen CGR]", "[CS - Tercera Sala]", "[BCN - Ley N.° 19.880, Art. 11]"],
          outputLabel: "Subsunción dogmática y práctica",
          output: "La omisión de fundamentos objetivos y verificables en el decreto de no renovación expone al municipio a recurso de protección con orden de reincorporación y pago de remuneraciones."
        },
        {
          label: "Control de probidad",
          title: "3. Verificación complementaria de inhabilidades y plazos",
          detail: "Revisa si existen sumarios pendientes, fuero gremial o eventuales conflictos de interés auditables vía InfoProbidad y comprueba plazos fatales de notificación.",
          chips: ["infoprobidad_get_dip", "cgr_search_auditorias", "Plazo 30 días Art. 19 CPR"],
          outputLabel: "Checklist de legalidad preventiva",
          output: "✓ Verificación de calificaciones previas · ✓ Motivación presupuestaria y de desempeño acreditable · ✓ Notificación formal conforme Arts. 45–47 Ley N.° 19.880."
        },
        {
          label: "Entregable Word .docx",
          title: "4. Informe jurídico listo para firma institucional",
          detail: "Genera minuta formal en Word (.docx) justificada, con citas literales de la Ley N.° 19.880, dictámenes CGR y sentencias de la Tercera Sala a pie de página.",
          chips: ["informe_administrativo.docx", "Citas CGR + CS", "Sin fugas de datos"],
          outputLabel: "Estándar de control preventivo",
          output: "Permite a jefaturas jurídicas y alcaldías decidir con evidencia verificada, reduciendo nulidades de derecho público y condenas en costas."
        }
      ]
    }
  },
  {
    id: "corporativo",
    shortName: "Corporativo, Tributario & Compliance",
    name: "Corporativo, Tributario, Concursal & Compliance Penal",
    tagline: "SpA/S.A., Compliance Ley N.° 21.595 / 20.393 / ANCI, SII + TTA, Concursal (Ley 20.720), SERNAC, INAPI, Redline XML y Datos Ley N.° 21.719.",
    badge: "Área 05 · Empresa, Tributario, Concursal y Datos",
    summary: "Integra en servidor local u on-premise (HTTP + Docker Zero-Data-Leak) toda la práctica corporativa y regulatoria: Compliance Penal y Ciberseguridad (Leyes N.° 21.595, 20.393 y 21.663 ANCI), litigación tributaria ante TTA y SII (Ley N.° 21.713), procedimientos concursales PyME/Persona y SUPERIR (Leyes N.° 20.720 / 21.563), protección al consumidor SERNAC, marcas INAPI Datos Abiertos, Redlining XML nativo en Word y anonimización local Ley N.° 21.719.",
    connectors: ["SII (Circulares, Oficios) + TTA (Sentencias Tributarias)", "CMF · TDLC · SERNAC (Ley N.° 19.496) · INAPI Datos Abiertos", "Compliance (Leyes 21.595 / 20.393 / 21.663 ANCI) + SUPERIR", "BCN (SpA 20.659, S.A. 18.046, 21.719, 20.720)", "docx_aplicar_redline XML + Anonimización ARCO+"],
    agents: ["agente-corporativo", "agente-contratos", "agente-compliance", "agente-tributario", "agente-concursal", "agente-propiedad-datos"],
    skills: ["chilean-corporate-legal", "chilean-contract-legal", "chilean-criminal-compliance", "chilean-tax-litigation", "chilean-insolvency-legal", "chilean-privacy-ip"],
    deliverables: [
      "Matriz de riesgos corporativos, Modelos de Prevención de Delitos (MPD Ley N.° 20.393 / 21.595), días-multa y reporte ANCI (Ley N.° 21.663).",
      "Reclamaciones ante TTA (Ley N.° 20.322 / Ley N.° 21.713), reposiciones RAV Art. 123 bis CT y acuerdos concursales bajo Ley N.° 20.720 / 21.563.",
      "Revisión de contratos y NDA con Control de Cambios XML nativo (docx_aplicar_redline) y anonimización reversible Ley N.° 21.719.",
      "Búsqueda en datos abiertos INAPI, alertas/juicios colectivos SERNAC y cartas de cese y desistimiento (Ley N.° 19.039)."
    ],
    trainingTitle: "Taller para Fiscalías Corporativas: Contratos, Compliance y Ley N.° 21.719",
    trainingFocus: "Cómo revisar contratos en minutos sin filtrar secretos comerciales, anonimizar documentos localmente y cruzar criterios SII, CMF y TDLC en un flujo corporativo auditable.",
    simulation: {
      scenario: "Fiscalía corporativa recibe un contrato de servicios SaaS con cláusulas de ley extranjera, cesión amplia de datos personales y limitación asimétrica de responsabilidad.",
      prompt: "«Anonimiza primero los datos sensibles, audita las cláusulas de responsabilidad y tratamiento de datos frente al Código Civil y la Ley N.° 21.719, y propone redacción alternativa conforme a derecho chileno.»",
      steps: [
        {
          label: "Anonimización local",
          title: "1. Protección preventiva de PII y secreto comercial",
          detail: "Antes de analizar el borrador, privacidad_anonimizar_documento detecta y enmascara RUTs, correos, teléfonos, direcciones y montos confidenciales localmente en tu PC.",
          chips: ["privacidad_anonimizar_documento", "Ley N.° 21.719", "Zero Data Leak"],
          outputLabel: "Sanitización verificada",
          output: "Entidades sensibles sustituidas por tokens reversibles locales · Trazabilidad completa para cumplimiento de protección de datos personales."
        },
        {
          label: "Auditoria normativa",
          title: "2. Cruce con Código Civil, Ley N.° 21.719 y SII/CMF",
          detail: "Contrasta cláusulas de exoneración de dolo (nula por Art. 1465 CC), cláusula penal enorme (Art. 1544 CC), base de licitud para transferencia internacional de datos y efectos tributarios SII.",
          chips: ["[BCN - Código Civil, Art. 1465]", "[BCN - Ley N.° 21.719]", "[Circular SII]"],
          outputLabel: "Semáforo de cláusulas críticas",
          output: "🔴 Exoneración total de responsabilidad (contraria a Art. 1465 CC) · 🟡 Subencargados fuera de Chile sin cláusulas tipo · 🟢 Propiedad intelectual delimitada."
        },
        {
          label: "Propuesta de redline",
          title: "3. Redacción de contrapropuesta bajo derecho continental chileno",
          detail: "Reemplaza conceptos importados del Common Law (indemnities genéricos, punitive damages) por terminología chilena exacta (daño emergente, lucro cesante, multa convencional, arbitraje CAM).",
          chips: ["Sin terminología Common Law", "Doctrina Abeliuk / Ramos Pazos", "Art. 1545 CC"],
          outputLabel: "Cláusulas corregidas listas",
          output: "Tabla comparativa «Cláusula original → Riesgo en Chile → Redacción sugerida» con respaldo normativo literal."
        },
        {
          label: "Entregable Word .docx",
          title: "4. Informe de negociación en Word (.docx)",
          detail: "Genera minuta ejecutiva para gerencia comercial con puntos intransables, textos de reemplazo y checklist de cierre societario/regulatorio.",
          chips: ["revision_contrato.docx", "Listo para negociación", "Auditado"],
          outputLabel: "Ahorro de horas de revisión",
          output: "Estandariza el criterio de toda la fiscalía corporativa usando plantillas y playbooks privados del propio equipo."
        }
      ]
    }
  },
  {
    id: "inmobiliario",
    shortName: "Inmobiliario & CBR",
    name: "Derecho Inmobiliario & Registral (CBR)",
    tagline: "Estudio de títulos decenal (10 años, Arts. 2510–2511 CC), gravámenes, hipotecas, checklist Conservador de Bienes Raíces y mandatos Art. 7 CPC.",
    badge: "Área 06 · Bienes Raíces y Notarial",
    summary: "Estructura el análisis registral chileno sobre los 10 años de prescripción adquisitiva extraordinaria: encadena escrituras, inscripciones de dominio, certificados de hipotecas, gravámenes y prohibiciones (GP), litigios, poderes y validaciones de mandato.",
    connectors: ["BCN Ley Chile (Código Civil Libro II y Reglamento CBR)", "Doctrina Peñailillo y Somarriva (Posesión Inscrita)", "PJUD Corte Suprema (Primera Sala Civil)", "Validadores de Mandato Art. 7 CPC y RUT"],
    agents: ["agente-inmobiliario", "agente-forense", "agente-contratos"],
    skills: ["chilean-real-estate-cbr", "chilean-forensic-evidence", "chilean-dogmatic-graphify"],
    deliverables: [
      "Informe de estudio de títulos decenal (10 años) en Word (.docx) con cadena de dominio cronológica y reparos clasificados.",
      "Checklist documental obligatorio previo a compraventa e inscripción ante el Conservador de Bienes Raíces.",
      "Verificación de mandatos civiles y judiciales (Art. 2116 CC y Art. 7 inc. 2.° CPC) y vigencia de personerías.",
      "Extracción OCR estructurada de inscripciones antiguas, copias de fojas y escrituras escaneadas."
    ],
    trainingTitle: "Taller de Estudios de Títulos e Inmobiliario con IA Local",
    trainingFocus: "Cómo acelerar la revisión de carpetas de 10 años de escrituras e inscripciones escaneadas, detectar reparos críticos sin alucinaciones y emitir informes estandarizados.",
    simulation: {
      scenario: "Estudio inmobiliario revisa carpeta de 12 escrituras y certificados del CBR para compraventa con financiamiento hipotecario.",
      prompt: "«Extrae el texto de las inscripciones escaneadas, arma la cadena de dominio de 10 años (Arts. 2510–2511 CC), verifica gravámenes y facultades del mandatario y genera el informe de títulos en Word (.docx).»",
      steps: [
        {
          label: "OCR forense local",
          title: "1. Digitalización privada de escrituras y fojas CBR",
          detail: "ocr_extract_pdf extrae texto limpio de copias autorizadas escaneadas, inscripciones de dominio y certificados de hipotecas y gravámenes directamente en el computador del estudio.",
          chips: ["ocr_extract_pdf", "100 % offline", "Preservación de fojas"],
          outputLabel: "Datos registrales estructurados",
          output: "Fojas, número y año de cada inscripción · Deslindes · Repertorios notariales · Estado civil de comparecientes (control Art. 1749 CC)."
        },
        {
          label: "Estudio decenal",
          title: "2. Auditoría de la cadena de 10 años y gravámenes",
          detail: "cbr_estudio_titulos verifica continuidad de transferencias por 10 años (Arts. 2510 y 2511 CC), vigencias, alzamientos pendientes, autorización conyugal (Art. 1749) y servidumbres.",
          chips: ["cbr_estudio_titulos", "[BCN - Código Civil, Art. 2511]", "[Doctrina - Peñailillo]"],
          outputLabel: "Reparos detectados automáticamente",
          output: "⚠ Falta acreditar alzamiento de prohibición de gravar y enajenar del año 2019 · ✓ Cadena de inscripciones continua desde 2014 (12 años)."
        },
        {
          label: "Mandatos y checklist",
          title: "3. Validación de poderes y documentos faltantes",
          detail: "cpc_validar_mandato y cbr_checklist_documentos comprueban si el representante cuenta con facultades expresas de enajenar, percibir y alzar, y listan certificados faltantes (tesorería, avalúo, no expropiación).",
          chips: ["cbr_checklist_documentos", "cpc_validar_mandato", "rut_validar_chile"],
          outputLabel: "Checklist de cierre CBR",
          output: "Faltan: certificado de deudas de contribuciones al día y vigencia de poder social < 60 días."
        },
        {
          label: "Informe en Word .docx",
          title: "4. Informe de títulos listo para el banco o cliente",
          detail: "Genera el informe decenal en Word (.docx) con tabla de inscripciones, sección de observaciones subsanables y conclusión condicional clara.",
          chips: ["estudio_titulos.docx", "Formato estudio jurídico", "Editable"],
          outputLabel: "Revisión ordenada y trazable",
          output: "Reduce horas de transcripción manual de fojas y asegura que ningún reparo registral pase inadvertido."
        }
      ]
    }
  },
  {
    id: "investigacion",
    shortName: "Investigación & Jurimetría",
    name: "Investigación Jurídica, Ciencia de Datos & Jurimetría",
    tagline: "82.717 documentos en Hugging Face, grafo LegalGraphify + MCP App visual, 5 tablas Apache Parquet, DuckDB y ChileLegalBench v1.0 (105/105).",
    badge: "Área 07 · Investigación y Publicaciones",
    summary: "Convierte el corpus jurídico chileno en un laboratorio empírico reproducible para tesis de magíster/doctorado, artículos científicos (WoS/Scielo/RChD), observatorios judiciales y centros de estudio: análisis de redes de citación (PageRank + HITS), explorador visual MCP App (app_abrir_grafo), benchmark reproducible ChileLegalBench v1.0 (105 casos deterministas, 100 % offline) y muestreo ciego con κ de Cohen.",
    connectors: ["Hugging Face (82.717 entradas con SHA fijado)", "5 Tablas Apache Parquet (12,45 MB) + DuckDB SQL", "LegalGraphify Multiplex + MCP App ui:// (app_abrir_grafo)", "ChileLegalBench v1.0 (105 casos · 100 %)", "Módulo jurimetria.py (PageRank, HITS, κ de Cohen)"],
    agents: ["agente-dogmatico", "agente-investigacion-ia", "agente-ingestor"],
    skills: ["chilean-dogmatic-graphify", "chilean-doctrine-ingestion", "chilean-notebooklm-grounding"],
    deliverables: [
      "Paquete de investigación reproducible: CSV, GraphML (Gephi/Cytoscape), Apache Parquet, METODOLOGIA_REPRODUCIBLE.md y referencia.bib.",
      "Análisis de redes de citación normativa (PageRank dirigido + HITS Authority/Hub) con auditoría de ruido OCR.",
      "Estadísticas longitudinales sobre 70.523 sentencias de la Corte Suprema por sala, recurso y resultado normalizado.",
      "Muestra estratificada ciega lista para validación intercodificador humana (cálculo de coeficiente κ de Cohen)."
    ],
    trainingTitle: "Seminario de Jurimetría, Grafos de Conocimiento e Investigación Empírica",
    trainingFocus: "Cómo diseñar artículos publicables en Derecho usando Hugging Face, DuckDB SQL sobre Apache Parquet, grafos de citaciones en Gephi y validación metodológica reproducible.",
    simulation: {
      scenario: "Equipo académico prepara un artículo empírico sobre tasas de acogimiento por sala de la Corte Suprema y normas constitucionales más citadas.",
      prompt: "«Ejecuta jurimetria_analizar_corpus en modo completo sobre la Corte Suprema, exporta la red de citaciones en GraphML + Parquet y genera una muestra ciega de 100 fallos con metodología reproducible y BibTeX.»",
      steps: [
        {
          label: "Dataset fijado (SHA)",
          title: "1. Trazabilidad científica con revisión inmutable de Hugging Face",
          detail: "Cada consulta fija el hash exacto del dataset (pablobenavidesj/doctrina-jurisprudencia-chile) para que cualquier árbitro o lector pueda replicar exactamente los mismos números años después.",
          chips: ["jurimetria_analizar_corpus", "SHA fijado HF", "82.717 entradas"],
          outputLabel: "Universo empírico delimitado",
          output: "70.523 fallos CS · 1.433 sentencias TC · 886 sentencias TA · 17 tramos Baremo · 11.579 fichas doctrinales en 5 tablas Apache Parquet."
        },
        {
          label: "Red multiplex y HITS",
          title: "2. Centralidad sustantiva sin sesgo editorial",
          detail: "El grafo multiplex atenúa las aristas bibliográficas (peso 0,04) y calcula PageRank dirigido + HITS Authority/Hub sobre la subred de citación normativa pura.",
          chips: ["PageRank dirigido", "HITS Authority/Hub", "Filtro anti-ruido OCR"],
          outputLabel: "Métricas de red obtenidas",
          output: "Top autoridades normativas detectadas sin colapso espectral: CPR Art. 19, Código Civil Arts. 1545/1698/2314, Código del Trabajo Art. 161."
        },
        {
          label: "Validación humana (κ)",
          title: "3. Muestra estratificada ciega para confiabilidad intercodificador",
          detail: "Genera automáticamente una plantilla CSV ciega estratificada por sala y resultado para doble codificación jurídica y cálculo del coeficiente κ de Cohen en el cuaderno DuckDB.",
          chips: ["Muestra ciega estratificada", "κ de Cohen", "DuckDB zero-copy"],
          outputLabel: "Rigor listo para revisión por pares",
          output: "Previene la crítica típica a estudios automatizados: combina extracción masiva con validación humana auditable."
        },
        {
          label: "Paquete publicable",
          title: "4. Exportación integral para Gephi, Python y LaTeX",
          detail: "jurimetria_exportar_investigacion genera la carpeta lista para anexo de artículo: red_citaciones.graphml, tablas CSV/Parquet, METODOLOGIA_REPRODUCIBLE.md (citando Art. 3 inc. 2.° CC) y referencia.bib.",
          chips: ["red_citaciones.graphml", "METODOLOGIA_REPRODUCIBLE.md", "referencia.bib"],
          outputLabel: "Listo para revista indexada o tesis",
          output: "Incluye nota metodológica de Derecho Continental (efecto relativo de las sentencias) y citas reproducibles con URL fijada."
        }
      ]
    }
  },
  {
    id: "academia",
    shortName: "Academia & Grado",
    name: "Academia, Examen de Grado & Clínicas Jurídicas",
    tagline: "Simulador socrático oral en Derecho Civil y Procesal, traducción a Lenguaje Claro, privilegio de pobreza y apoyo a Clínicas Jurídicas (CAJ).",
    badge: "Área 08 · Formación Universitaria y Acceso a la Justicia",
    summary: "Acerca el rigor dogmático chileno a facultades de Derecho, estudiantes de examen de grado y clínicas jurídicas de asistencia social: interrogación socrática por cédulas con rúbrica de 3 pilares, traducción a Lenguaje Claro para ciudadanos y evaluación de privilegio de pobreza.",
    connectors: ["228 Obras Doctrinales Canónicas (7.399 documentos HF)", "21 Guías Oficiales de la Academia Judicial", "BCN Ley Chile (Código Civil, CPC, COT)", "Módulos grado_* y clinica_*"],
    agents: ["agente-grado", "agente-clinica", "agente-dogmatico"],
    skills: ["chilean-socratic-bar-exam", "chilean-legal-clinic", "chilean-dogmatic-graphify"],
    deliverables: [
      "Sesiones socráticas de examen de grado por cédula (Obligaciones, Bienes, Responsabilidad, Contratos, Procesal) con rúbrica de 3 pilares.",
      "Tarjetas de estudio (flashcards) con definiciones legales literales del Código Civil y fallos rectores.",
      "Traducciones de resoluciones judiciales y escritos complejos a Lenguaje Claro para usuarios de clínicas jurídicas (CAJ).",
      "Intake socio-jurídico y evaluación de privilegio de pobreza (Arts. 591–600 COT y Arts. 129–137 CPC)."
    ],
    trainingTitle: "Convenios Universitarios, Talleres de Grado y Laboratorios de Clínicas Jurídicas",
    trainingFocus: "Implementación del Simulador Socrático de Grado y flujos de IA ética y trazable para docentes, estudiantes de clínicas jurídicas y programas de postgrado.",
    simulation: {
      scenario: "Clínica Jurídica universitaria atiende a usuaria con resolución compleja en juicio civil y un estudiante prepara su cédula de examen de grado.",
      prompt: "«Traduce este proveído judicial a Lenguaje Claro para la usuaria evaluando privilegio de pobreza (Arts. 591–600 COT) y genera una cédula socrática sobre posesión inscrita (Arts. 728 y 2505 CC).»",
      steps: [
        {
          label: "Atención clínica",
          title: "1. Comprensión del proveído y evaluación social",
          detail: "pjud_interpretar_proveido decodifica el trámite y carga procesal exacta de la resolución, mientras clinica_intake_social evalúa los presupuestos de asistencia jurídica gratuita.",
          chips: ["pjud_interpretar_proveido", "clinica_intake_social", "Arts. 591–600 COT"],
          outputLabel: "Diagnóstico procesal inmediato",
          output: "Resolución «Téngase por contestada la demanda, traslado para réplica» → Plazo fatal: 6 días hábiles judiciales (Art. 311 CPC)."
        },
        {
          label: "Lenguaje Claro",
          title: "2. Traducción ciudadana sin perder precisión jurídica",
          detail: "clinica_lenguaje_claro transforma tecnicismos procesales en una guía comprensible que explica qué ocurrió, qué plazo corre y qué documentos debe traer la persona atendida.",
          chips: ["clinica_lenguaje_claro", "Acceso a la justicia", "Guías Academia Judicial"],
          outputLabel: "Comunicación centrada en la persona",
          output: "Entrega explicación clara de 1 página para el usuario + ficha técnica interna con plazos para el estudiante tutor."
        },
        {
          label: "Interrogación de grado",
          title: "3. Simulación oral exigente con 3 pilares",
          detail: "En modo examen de grado, agente-grado sortea una cédula y evalúa definición legal literal del Código Civil, debate doctrinal (Somarriva / Peñailillo) y criterio uniforme de la Corte Suprema.",
          chips: ["grado_generar_cedula", "grado_interrogar", "grado_obtener_flashcards"],
          outputLabel: "Rúbrica académica de evaluación",
          output: "No acepta respuestas vagas: exige citar Arts. 724, 728 y 2505 CC y contrastar tesis de garantía absoluta vs. posesión material."
        },
        {
          label: "Impacto formativo",
          title: "4. Laboratorios universitarios 100 % abiertos y auditables",
          detail: "Las facultades pueden desplegar la suite gratuitamente en sus salas de computación o notebooks estudiantiles con acompañamiento docente y talleres presenciales u online.",
          chips: ["Licencia Apache 2.0", "Trazabilidad total", "Convenios universitarios"],
          outputLabel: "Formación jurídica moderna",
          output: "Enseña a futuros abogados a usar IA verificando siempre la fuente primaria —nunca delegando el criterio jurídico."
        }
      ]
    }
  }
];
