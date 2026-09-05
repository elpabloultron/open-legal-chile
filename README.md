# ⚖️ Open Legal Chile

<p align="center">
  <strong>Infraestructura Abierta de Inteligencia Jurídica, Servidor MCP y Conectores Oficiales para el Ordenamiento Jurídico de la República de Chile</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/openlegal-chile/"><img src="https://img.shields.io/pypi/v/openlegal-chile?style=for-the-badge&logo=pypi&logoColor=white&color=blue" alt="PyPI Version"/></a>
  <a href="https://github.com/elpabloultron/open-legal-chile/actions"><img src="https://img.shields.io/github/actions/workflow/status/elpabloultron/open-legal-chile/ci.yml?branch=main&style=for-the-badge&logo=github" alt="CI Status"/></a>
  <img src="https://img.shields.io/badge/Auditor%C3%ADa_360%C2%B0-Distinci%C3%B3n_M%C3%A1xima-success?style=for-the-badge&logo=security&logoColor=white" alt="Auditoría 360"/>
  <img src="https://img.shields.io/badge/Zero_Data_Leak-Passed-brightgreen?style=for-the-badge&logo=shield" alt="Zero Data Leak"/>
  <img src="https://img.shields.io/badge/MCP-Protocol_2024--11--05-8B5CF6?style=for-the-badge&logo=anthropic&logoColor=white" alt="MCP Compatible"/>
  <img src="https://img.shields.io/badge/Jurisdicci%C3%B3n-Chile_(Civil_Law)-0039A6?style=for-the-badge&logo=flag&logoColor=white" alt="Chile Flag"/>
  <img src="https://img.shields.io/badge/Tests-70%2F70_Passed-blue?style=for-the-badge&logo=pytest&logoColor=white" alt="Tests"/>
  <img src="https://img.shields.io/badge/License-Apache_2.0-22C55E?style=for-the-badge" alt="License"/>
</p>

---

## 📑 Tabla de Contenidos
1. [🌟 Visión, Filosofía y Soberanía Jurídica](#-1-visión-filosofía-y-soberanía-jurídica)
2. [🏗️ Arquitectura del Ecosistema](#-2-arquitectura-del-ecosistema)
3. [⚡ Instalación y Puesta en Marcha](#-3-instalación-y-puesta-en-marcha)
4. [🔌 Catálogo Exhaustivo de Herramientas MCP (36 Herramientas)](#-4-catálogo-exhaustivo-de-herramientas-mcp-36-herramientas)
5. [🏛️ Los 10 Conectores Oficiales del Estado de Chile](#-5-los-10-conectores-oficiales-del-estado-de-chile)
6. [📚 La Base Doctrinal Canónica y la Dimensión Procesal Forense](#-6-la-base-doctrinal-canónica-y-la-dimensión-procesal-forense)
7. [⚖️ Módulos Forenses y Pedagógicos de Especialidad](#-7-módulos-forenses-y-pedagógicos-de-especialidad)
8. [🧠 Catálogo de Skills y Subagentes (15 Especialidades)](#-8-catálogo-de-skills-y-subagentes-15-especialidades)
9. [💻 Guía Completa de la Consola CLI (`openlegal`)](#-9-guía-completa-de-la-consola-cli-openlegal)
10. [🛡️ Certificación de Auditoría Institucional 360° (AUDIT.md)](#-10-certificación-de-auditoría-institucional-360-auditmd)
11. [🧪 Pruebas Automatizadas y Verificación Continua](#-11-pruebas-automatizadas-y-verificación-continua)
12. [📜 Licencia, Ética Forense y Responsabilidad Profesional](#-12-licencia-ética-forense-y-responsabilidad-profesional)
13. [🌱 Cómo Contribuir](#-13-cómo-contribuir)

---

## 🌟 1. Visión, Filosofía y Soberanía Jurídica

**Open Legal Chile** es una infraestructura de software de código abierto diseñada para transformar la práctica legal, la docencia universitaria y la investigación forense en la República de Chile.

A diferencia de los modelos de inteligencia artificial genéricos y comerciales diseñados bajo la óptica del *Common Law* anglosajón, Open Legal Chile fue concebido **desde sus cimientos para el Sistema de Derecho Continental (*Civil Law*) chileno**:

### 🏛️ Principios Fundamentales del Sistema Jurídico Chileno
* **Primacía de la Ley Escrita:** La ley es una declaración de la voluntad soberana que, manifestada en la forma prescrita por la Constitución, manda, prohíbe o permite (*Art. 1 del Código Civil*). 
* **Efecto Relativo de las Sentencias:** Las sentencias judiciales no tienen fuerza obligatoria sino respecto de las causas en que actualmente se pronunciaren (*Art. 3 inc. 2 del Código Civil*). No rige el precedente vinculante anglosajón (*stare decisis*), pero la unificación jurisprudencial de la Corte Suprema y la doctrina administrativa de la Contraloría (CGR) y la Dirección del Trabajo (DT) fijan los criterios rectores del ordenamiento.
* **Prohibición Absoluta de Anglicismos y Figuras Foráneas:** Queda terminantemente vetada la extrapolación de conceptos ajenos a la tradición procesal chilena (*at-will employment, punitive damages, discovery, subpoena, grand jury, deposition, Title VII, FLSA*). Se emplea exclusivamente el léxico forense y sustantivo chileno (*necesidades de la empresa, finiquito con reserva de derechos, fuero laboral, tutela de derechos fundamentales, daño moral, daño emergente, lucro cesante, otrosí, reposición, apelación, casación en la forma y en el fondo, presuma OJV*).
* **Estándar Obligatorio de Citación Oficial:**
  * Ley o Código: `[BCN - Código Civil, Art. 1545]` o `[BCN - Ley N° 21.643 Ley Karin, Art. 2]`
  * Constitución: `[BCN - CPR, Art. 19 N° 1]`
  * Fallo Corte Suprema: `[CS - Rol N° 12.345-2023, Fecha: 15-11-2023]`
  * Dictamen DT: `[Dictamen DT N° 1234/15 de 2024]`
  * Dictamen CGR: `[Dictamen CGR N° E123456 (2024)]`
  * Circular SII: `[Circular SII N° 45 (2023)]`
  * Norma CMF: `[NCG CMF N° 461]`

### 🛡️ Soberanía Tecnológica y Secreto Profesional ($0 y Cero API Keys)
El ejercicio del Derecho exige reserva y confidencialidad absoluta:
1. **100% Gratuito y Libre:** No requiere licencias comerciales, tokens de pago ni tarjetas de crédito.
2. **Cero Fuga de Datos (Zero Data Leak):** El **Motor Soberano Local** y los modelos abiertos vía **Ollama** (`llama3.2`, `deepseek-r1`, `qwen2.5`) procesan causas, contratos y escritos judicialmente confidenciales de manera 100% local en tu propio computador, preservando el secreto profesional (*Art. 247 del Código Penal*) y la *Ley N° 19.628 sobre Protección de la Vida Privada*.
3. **Acceso Público a Fuentes del Estado:** Las conexiones con la BCN, CGR, DT, PJUD, CNE, CMF, SII, SMA y TDLC operan contra repositorios públicos abiertos del Estado de Chile sin necesidad de registro ni llaves de pago.

---

## 🏗️ 2. Arquitectura del Ecosistema

La suite opera bajo el estándar internacional **Model Context Protocol (MCP)**, permitiendo a cualquier agente o entorno interactuar con la infraestructura jurídica chilena:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           CLIENTES Y AGENTES DE IA SOPORTADOS                           │
│                                                                                         │
│   Google Antigravity      Claude Code (CLI)      Claude Desktop      Cursor / VS Code   │
│   (Google AI Pro)         (Anthropic)            (Cowork)            (Codex / Roo Code) │
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                         │ JSON-RPC 2.0 (stdio)
┌────────────────────────────────────────▼────────────────────────────────────────────────┐
│                       SERVIDOR MAESTRO MCP (mcp_server.py)                              │
│                                                                                         │
│   • 36 Herramientas Forenses Registradas                                                │
│   • Motor de Doctrina Canónica FTS5 BM25 (doctrina_connector.py)                        │
│   • Motor de Crítica Forense en 5 Dimensiones (critique.py)                             │
│   • Vigilante de Proveídos y Plazos Fatales OJV (docket_watcher.py)                     │
│   • Simulador Socrático de Examen de Grado (examen_grado.py)                            │
│   • Asistente Social de Clínica Jurídica y Lenguaje Claro (clinica_juridica.py)         │
│   • Módulo de Peritaje OCR y Compilador de Expedientes A4 (pdf_dossier_compiler.py)     │
│   • Modelador de Grafos de Vínculos y Probidad Pública (grafo_vinculos.py)              │
│   • Exportador Forense OJV Ley N° 20.886 (exporters.py)                                 │
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                         │ Consultas Locales y Red Oficial
┌────────────────────────────────────────▼────────────────────────────────────────────────┐
│                     10 CONECTORES OFICIALES DEL ESTADO DE CHILE                         │
│                                                                                         │
│   [BCN Ley Chile XML]   [Contraloría CGR]   [Dirección del Trabajo DT]  [PJUD / Suprema]│
│   [Tribunal Const.]     [CNE Energía]       [Panel de Expertos]         [CMF Valores]   │
│   [SII Tributario]      [SMA SNIFA Ambient] [TDLC Libre Competencia]                    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ 3. Instalación y Puesta en Marcha

### Opción A: Instalación vía PyPI (Recomendado para Producción)
```bash
pip install openlegal-chile
```

### Opción B: Instalación desde Código Fuente (Modo Desarrollo)
```bash
git clone https://github.com/elpabloultron/open-legal-chile.git
cd open-legal-chile
pip install -e .
```

### Opción C: Integración en Google Antigravity, Cursor o VS Code
Agrega la suite a tu archivo de configuración de servidores MCP (`mcp_config.json`):
```json
{
  "mcpServers": {
    "open-legal-chile": {
      "command": "python3",
      "args": ["-m", "openlegal", "mcp"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

### Opción D: Integración en Claude Code (Terminal)
```bash
claude mcp add open-legal-chile python3 -m openlegal mcp
```

### ⚙️ Modos de Inferencia: Soberano vs. Modelos Externos
Open Legal Chile opera **por defecto en Modo Soberano** (100% gratuito y sin enviar datos al exterior):
* **Motor Soberano:** Se activa automáticamente sin necesidad de configurar claves.
* **Ollama Local (Opcional):** Si tienes Ollama corriendo en `localhost:11434`, la suite detecta y utiliza tus modelos locales de forma inmediata.
* **Proveedores Comerciales (Opcionales):** Si decides voluntariamente conectar APIs comerciales de pago, puedes configurar las variables en tu archivo `.env`:
  ```bash
  # Totalmente opcionales (el sistema funciona al 100% sin ellas)
  ANTHROPIC_API_KEY="sk-ant-..."
  GEMINI_API_KEY="AIzaSy..."
  DEEPSEEK_API_KEY="sk-..."
  OPENAI_API_KEY="sk-..."
  ```

---

## 🔌 4. Catálogo Exhaustivo de Herramientas MCP (36 Herramientas)

El servidor MCP expone **36 herramientas oficiales** categorizadas funcionalmente:

### A. Legislación y Códigos de la República
| Herramienta MCP | Parámetros | Descripción de Operatividad |
| :--- | :--- | :--- |
| `bcn_get_codigo` | `codigo` *(str)*, `articulo` *(str, opc)* | Consulta artículos o estructura de los 9 Códigos fundamentales chilenos (Civil, Trabajo, Procedimiento Civil, Penal, Comercio, Tributario, Minería, Aguas, Procesal Penal) en la BCN. |
| `bcn_get_ley` | `numero` *(int)*, `articulo` *(str, opc)* | Descarga y parsea el texto oficial de cualquier ley de la República (ej. Ley 21.643 Karin, Ley 21.561 40 Horas, Ley 20.886 OJV). |

### B. Jurisprudencia y Dictámenes Vinculantes
| Herramienta MCP | Parámetros | Descripción de Operatividad |
| :--- | :--- | :--- |
| `cgr_search_jurisprudencia` | `query` *(str)* | Busca dictámenes vinculantes en la jurisprudencia administrativa de la Contraloría General de la República. |
| `cgr_search_auditorias` | `query` *(str)* | Consulta el catálogo de más de 9.600 Informes Finales de Auditoría e investigaciones especiales de la CGR. |
| `dt_search_doctrina` | `query` *(str)* | Busca dictámenes y doctrina laboral vinculante de la Dirección del Trabajo (DT) con enlace al texto completo. |
| `pjud_search_jurisprudencia` | `query` *(str)*, `sala` *(str, opc)* | Busca fallos rectores de la Corte Suprema (Unificación Laboral, Tercera Sala Constitucional, Primera Sala Civil) y fallos del Tribunal Constitucional (TC). |

### C. Regulación Sectorial e Instituciones Públicas
| Herramienta MCP | Parámetros | Descripción de Operatividad |
| :--- | :--- | :--- |
| `cne_get_centrales_y_proyectos` | `region` *(str, opc)* | Consulta centrales generadoras activas, capacidad instalada y proyectos energéticos en el SEA de la Comisión Nacional de Energía. |
| `panel_expertos_search` | `query` *(str)* | Busca dictámenes vinculantes e inapelables sobre discrepancias técnicas y tarifarias en el Panel de Expertos de la Ley Eléctrica. |
| `cmf_search_normativa` | `query` *(str)* | Consulta Normas de Carácter General (NCG) y circulares de la Comisión para el Mercado Financiero (CMF). |
| `sii_search_circulares` | `query` *(str)* | Consulta circulares oficiales e instrucciones del Director del Servicio de Impuestos Internos (SII). |
| `sma_search_sancionatorios` | `query` *(str)* | Consulta expedientes sancionatorios ambientales y Programas de Cumplimiento (PdC) en el SNIFA de la SMA. |
| `tdlc_search_jurisprudencia` | `query` *(str)* | Consulta sentencias y resoluciones del Tribunal de Defensa de la Libre Competencia (TDLC). |

### D. Doctrina Dogmática y Dimensión Procesal Forense
| Herramienta MCP | Parámetros | Descripción de Operatividad |
| :--- | :--- | :--- |
| `doctrina_search` | `query` *(str)*, `area` *(str, opc)*, `autor` *(str, opc)*, `limit` *(int)* | Búsqueda por relevancia semántica FTS5 y BM25 en tratados chilenos (Peñailillo, Ramos Pazos, Barros Bourie, Gamonal, Bermúdez, Cury, Maturana, Cea Egaña). |
| `doctrina_get_institucion` | `nombre` *(str)*, `area` *(str, opc)* | Recupera la ficha dogmática y forense completa: definición canónica, requisitos, operativa procesal forense, concordancias BCN y fallos rectores. |
| `doctrina_list_obras` | *(ninguno)* | Lista todos los manuales y tratados dogmáticos indexados con sus estadísticas de instituciones y tokens. |

### E. Docencia y Examen de Grado
| Herramienta MCP | Parámetros | Descripción de Operatividad |
| :--- | :--- | :--- |
| `grado_interrogar` | `materia` *(str)*, `dificultad` *(str)* | Simula una interrogación socrática de examen de grado en Derecho Civil o Procesal, evaluando respuestas con pauta dogmática estricta. |
| `grado_generar_cedula` | `tema` *(str)* | Genera una cédula completa de examen de grado con casos prácticos, artículos legales vinculados, doctrina canónica y pauta de evaluación. |
| `grado_obtener_flashcards` | `area` *(str)*, `tipo` *(str)* | Genera fichas mnemotécnicas de definiciones sacramentales y plazos procesales fatales para estudio intensivo. |

### F. Vigilancia Procesal y Proveídos Judiciales
| Herramienta MCP | Parámetros | Descripción de Operatividad |
| :--- | :--- | :--- |
| `vigilante_analizar_resolucion` | `resolucion_texto` *(str)*, `procedimiento` *(str)* | Analiza proveídos judiciales de la OJV (*"traslado"*, *"autos para resolver"*, *"téngase por contestada"*), clasifica sus efectos y calcula plazos fatales en días hábiles (Art. 66 CPC). |
| `vigilante_radar_normativo` | `materia` *(str)*, `dias_atras` *(int)* | Monitorea novedades normativas del Diario Oficial, dictámenes de la Contraloría y circulares tributarias. |
| `vigilante_contrato_plazos` | `tipo_contrato` *(str)*, `fecha_vencimiento` *(str)*, `preaviso_dias` *(int)* | Calcula ventanas de preaviso, plazos de desahucio y cláusulas de tácita reconducción para contratos civiles y mercantiles. |

### G. Clínica Jurídica y Lenguaje Claro
| Herramienta MCP | Parámetros | Descripción de Operatividad |
| :--- | :--- | :--- |
| `clinica_lenguaje_claro` | `texto_resolucion` *(str)*, `destinatario` *(str)* | Traduce proveídos y sentencias técnicas a lenguaje ciudadano, empático y comprensible para personas en situación de vulnerabilidad. |
| `clinica_intake_social` | `materia` *(str)*, `datos_usuario` *(dict)* | Genera la ficha sociojurídica de ingreso para consultorios de asistencia judicial en materias de familia, precario y alimentos. |
| `clinica_auditar_borrador` | `borrador_texto` *(str)*, `tribunal` *(str)* | Audita formalmente el borrador de un escrito redactado por un pasante o alumno antes del visado del tutor (presuma, patrocinio y petitorio). |

### H. Transparencia, Probidad y Modelado de Redes
| Herramienta MCP | Parámetros | Descripción de Operatividad |
| :--- | :--- | :--- |
| `infoprobidad_get_dip` | `query_or_url` *(str)* | Extrae y estructura las Declaraciones de Intereses y Patrimonio (DIP) de autoridades públicas desde InfoProbidad (Ley N° 20.880). |
| `generar_grafo_vinculos` | `nodes`, `edges`, `title` | Modela redes societarias, parentescos y relaciones de interés público en diagramas Mermaid y exportaciones JSON. |

### I. Peritaje Documental y Tramitación OJV
| Herramienta MCP | Parámetros | Descripción de Operatividad |
| :--- | :--- | :--- |
| `ocr_extract_pdf` | `pdf_path`, `start_page`, `end_page`, `force_ocr`, `dpi`, `lang` | Extrae texto nativo o ejecuta OCR pericial (Tesseract) sobre expedientes judiciales escaneados y escrituras públicas notariales. |
| `compile_legal_dossier` | `markdown_content`, `output_pdf_path`, `annexes` | Compila escritos judiciales en formato PDF A4 institucional, ensambla anexos documentales foliados y genera versión optimizada. |
| `export_brief_ojv` | `titulo`, `tribunal`, `comparecencia`, `hechos`, `derecho`, `peticiones`, `otrosies` | Genera y formatea un escrito judicial formal para la Oficina Judicial Virtual (OJV) en `.html`, `.md`, `.txt` y `.json`. |

### J. Privacidad (ARCO) y Propiedad Industrial (INAPI)
| Herramienta MCP | Parámetros | Descripción de Operatividad |
| :--- | :--- | :--- |
| `privacidad_tramitar_arco` | `tipo_derecho`, `solicitante`, `rut`, `datos_solicitados` | Tramita y redacta modelos oficiales de respuesta a solicitudes de Acceso, Rectificación, Cancelación u Oposición (Ley N° 19.628). |
| `inapi_cease_and_desist` | `marca_afectada`, `titular`, `infractor`, `hechos_infraccion` | Redacta cartas notariales formales de Cese y Desistimiento por infracción marcaria (Ley N° 19.039) o derechos de autor (Ley N° 17.336). |
| `inapi_evaluar_marca` | `marca_propuesta`, `clase_niza` | Evalúa la viabilidad y distintividad de un signo en el Clasificador de Niza ante el registro marcario de INAPI. |

### K. Investigación Analítica Asistida (Google NotebookLM)
| Herramienta MCP | Parámetros | Descripción de Operatividad |
| :--- | :--- | :--- |
| `notebooklm_list_notebooks` | *(ninguno)* | Lista todos los cuadernos de investigación jurídica creados con metadatos y fuentes. |
| `notebooklm_create_notebook` | `title` *(str)* | Crea un nuevo cuaderno de investigación jurídica estructurado en NotebookLM. |
| `notebooklm_add_source` | `notebook_id`, `file_path`, `title` | Ingesta expedientes, sentencias o doctrina local como fuentes probatorias en el cuaderno. |
| `notebooklm_query` | `notebook_id`, `prompt` | Ejecuta consultas de alta precisión con citas exactas referenciadas (*grounded citations*). |

---

## 🏛️ 5. Los 10 Conectores Oficiales del Estado de Chile

Cada conector fue desarrollado para comunicarse directamente con las plataformas públicas del Estado, almacenando respuestas en una base de datos local SQLite (`openlegal_cache.db`) para garantizar velocidad y funcionamiento offline:

1. **📜 Biblioteca del Congreso Nacional (BCN Ley Chile):**
   * *Mecanismo:* Consulta directa al portal público XML de la BCN (`leychile.cl/Consulta/obtxml`).
   * *Cobertura:* Toda la legislación de la República y los 9 Códigos positivos actualizados en tiempo real. **No requiere registro ni API key**.
2. **🏛️ Contraloría General de la República (CGR):**
   * *Mecanismo:* API REST abierta de jurisprudencia administrativa.
   * *Cobertura:* Más de 50.000 dictámenes sobre confianza legítima a contrata, estatuto administrativo y probidad, más 9.600 Informes de Auditoría.
3. **💼 Dirección del Trabajo (DT):**
   * *Mecanismo:* Catálogo institucional abierto de dictámenes y pronunciamientos doctrinales.
   * *Cobertura:* Jurisprudencia vinculante sobre despidos (Art. 161), Ley Karin (Ley 21.643), reducción de jornada 40 Horas (Ley 21.561) y finiquitos.
4. **⚖️ Poder Judicial (PJUD) & Corte Suprema:**
   * *Mecanismo:* Base estructurada local (`jurisprudencia_judicial.db`) con indexación de fallos rectores.
   * *Cobertura:* Sentencias de Unificación de Doctrina Laboral (Art. 483 CT), Recursos de Protección y Casación Civil.
5. **🛡️ Tribunal Constitucional (TC):**
   * *Mecanismo:* Repositorio de requerimientos de inaplicabilidad por inconstitucionalidad (*Art. 93 N° 6 CPR*) y sentencias de inconstitucionalidad (*Art. 93 N° 7 CPR*).
6. **⚡ Comisión Nacional de Energía (CNE):**
   * *Mecanismo:* Portal de Datos Abiertos *Energía Abierta*.
   * *Cobertura:* Capacidad instalada (MW), 1.342 centrales generadoras, 3.754 proyectos en el Sistema de Evaluación de Impacto Ambiental (SEA).
7. **🔌 Panel de Expertos de la Ley Eléctrica:**
   * *Mecanismo:* API pública de discrepancias técnicas y tarifarias.
   * *Cobertura:* Dictámenes vinculantes e inapelables sobre la Ley General de Servicios Eléctricos (*DFL 4/2006*).
8. **🏢 Comisión para el Mercado Financiero (CMF):**
   * *Mecanismo:* Servicio público de consulta normativa.
   * *Cobertura:* Normas de Carácter General (NCG 461, gobiernos corporativos, sostenibilidad) y circulares del mercado bancario y de valores.
9. **💰 Servicio de Impuestos Internos (SII):**
   * *Mecanismo:* Índice oficial de resoluciones y circulares tributarias (2020 a 2026).
10. **🌱 Superintendencia del Medio Ambiente (SMA / SNIFA):**
    * *Mecanismo:* Sistema Nacional de Información de Fiscalización Ambiental (SNIFA).
    * *Cobertura:* Expedientes sancionatorios ambientales y Programas de Cumplimiento (PdC).

---

## 📚 6. La Base Doctrinal Canónica y la Dimensión Procesal Forense

En la tradición jurídica chilena, un manual o tratado nunca es un compendio puramente teórico o abstracto: **no hay derecho subjetivo sin acción procesal que lo tutele**.

Open Legal Chile cuenta con una base dogmática de tratados canónicos indexados en SQLite con búsqueda de texto completo **FTS5 y ranking BM25** (`doctrina.db`):

### 📖 Tratadistas Canónicos Digitalizados
* **Bienes y Derechos Reales:** Daniel Peñailillo Arévalo
* **Obligaciones y Efectos Contractuales:** René Ramos Pazos
* **Responsabilidad Extracontractual:** Enrique Barros Bourie
* **Derecho del Trabajo y Relaciones Laborales:** Sergio Gamonal Contreras
* **Derecho Administrativo General:** Jorge Bermúdez Soto
* **Derecho Penal (Parte General):** Enrique Cury Urzúa
* **Teoría General de los Recursos Procesales:** Mario Mosquera Ruiz y Cristián Maturana Miquel
* **Derecho Constitucional y Acciones:** José Luis Cea Egaña

### 🏛️ Los 7 Pilares de la Dimensión Procesal Forense
Cada institución doctrinal no solo define el instituto, sino que detalla su aplicación práctica en tribunales:

1. **Vía Procesal / Tipo de Procedimiento:** Juicio Ordinario de Mayor Cuantía (Art. 254 CPC), Juicio Sumario (Art. 680 CPC), Juicio Ejecutivo (Art. 434 CPC), Tutela Laboral (Art. 485 CT), Recurso de Protección (Art. 20 CPR).
2. **Tribunal Competente:** Reglas de competencia absoluta (materia, cuantía, fuero) y relativa (territorio) del Código Orgánico de Tribunales (COT).
3. **Legitimación Procesal:** Quién puede demandar (legitimación activa: ej. dueño, poseedor regular en acción publiciana Art. 894 CC, trabajador, sindicato) y contra quién se dirige la pretensión (legitimación pasiva).
4. **Carga Probatoria (*Onus Probandi*):** Asignación de la prueba según el Art. 1698 del Código Civil, estándar de prueba tasada vs. sana crítica, y prueba por indicios (Art. 493 CT).
5. **Medidas Precautorias y Cautelares:** Medidas prejudiciales (Arts. 273 y 279 CPC) y precautorias de aseguramiento del Art. 290 del CPC (secuestro, interventor, retención y prohibición de celebrar actos y contratos).
6. **Plazos Fatales y Términos Probatorios:** Emplazamiento (15/18 días + tabla), términos probatorios (20 días ordinario, 8 días sumario, 10 días ejecutivo) y plazos de recursos (apelación 5/10 días, casación 15 días, protección 30 días corridos).
7. **Defensas y Excepciones Típicas:** Excepciones dilatorias (Art. 303 CPC), excepciones de fondo y perentorias (*exceptio non adimpleti contractus* Art. 1552 CC, caducidad, prescripción extintiva).

### 💡 Optimización Extrema de Tokens (Reducción > 80%)
Mediante el compilador [`scripts/doctrina_parser.py`](scripts/doctrina_parser.py), los textos crudos y transcripciones doctrinales son depurados de ruido editorial y convertidos en **Markdown de Alta Densidad Dogmática**, reduciendo entre un 80% y un 92% el consumo de tokens en la ventana de contexto de los agentes de IA.

---

## ⚖️ 7. Módulos Forenses y Pedagógicos de Especialidad

### 🔍 A. Motor de Crítica Forense en 5 Dimensiones (`critique.py`)
Inspirado en los mecanismos de auto-revisión y auditoría de calidad de escritos judiciales, evalúa borradores en 5 dimensiones obligatorias:
1. **Jerarquía Normativa y Legalidad:** Comprueba conformidad con la Constitución y leyes vigentes, purga de terminología de *Common Law* y estándar de citación oficial.
2. **Doctrina y Jurisprudencia Aplicable:** Exige fundamentación en los criterios rectores de la Corte Suprema, CGR o DT.
3. **Estructura Forense OJV (Ley N° 20.886):** Fiscaliza la presencia de presuma, comparecencia, relación fáctica, fundamentación de derecho, petitorio y otrosíes.
4. **Coherencia Fáctica y Carga Probatoria (Art. 1698 CC):** Evalúa la congruencia entre hechos afirmados y la pretensión deducida.
5. **Compuertas Éticas y Plazos Fatales:** Advierte sobre riesgos de preclusión y exige la validación humana de un abogado habilitado.

### ⏱️ B. Vigilante Procesal de Proveídos (`docket_watcher.py`)
Automatiza el control procesal del despacho:
* **Lectura de Proveídos:** Detecta y clasifica resoluciones judiciales de la OJV (*"traslado"*, *"autos para resolver"*, *"téngase por contestada"*, *"recibida la causa a prueba"*).
* **Cómputo de Plazos Fatales:** Calcula automáticamente el vencimiento de plazos en días hábiles judiciales (excluyendo domingos y feriados conforme al Art. 66 del CPC).
* **Vigilancia Contractual:** Monitorea ventanas críticas de desahucio y preaviso en contratos civiles y comerciales.

### 🎓 C. Simulador Socrático de Examen de Grado (`examen_grado.py`)
Diseñado para la preparación rigurosa del examen final de licenciatura en Derecho:
* **Interrogador Dinámico:** Plantea preguntas doctrinales y contrapreguntas socráticas exigiendo exactitud conceptual.
* **Generador de Cédulas:** Genera cédulas completas por materia (Derecho Civil y Derecho Procesal) con pauta de corrección para el docente.
* **Flashcards Mnemotécnicas:** Fichas de estudio rápido con definiciones sacramentales y plazos procesales fatales.

### 🤝 D. Clínica Jurídica y Lenguaje Claro (`clinica_juridica.py`)
Herramienta de vinculación con el medio y asistencia judicial social:
* **Traductor a Lenguaje Claro:** Transforma resoluciones judiciales densas en explicaciones accesibles y pedagógicas para usuarios de escasos recursos.
* **Triaje Social de Casos:** Fichas de ingreso estructuradas para causas de alimentos, violencia intrafamiliar y juicios de precario.
* **Auditoría de Pasantes:** Revisa formalmente los escritos de estudiantes en práctica antes del visado y firma del abogado tutor.

### 🌐 E. Modelado de Redes y Probidad Pública (`grafo_vinculos.py` e `infoprobidad_connector.py`)
* **Extracción InfoProbidad:** Parsea Declaraciones de Intereses y Patrimonio (DIP) bajo la Ley N° 20.880.
* **Grafos de Vínculos:** Modela relaciones societarias, vínculos familiares y relaciones contractuales con el Estado en diagramas Mermaid y estructuras JSON.

### 📑 F. Peritaje OCR y Compilador de Expedientes (`forensic_ocr.py` y `pdf_dossier_compiler.py`)
* **OCR Pericial:** Extracción de texto de fojas escaneadas con preservación de fidelidad documental.
* **Compilador A4 Foliado:** Ensambla demandas, recursos y anexos probatorios en un expediente único con carátula institucional y foliado electrónico.

---

## 🧠 8. Catálogo de Skills y Subagentes (15 Especialidades)

El directorio `agents/` incluye **15 perfiles de especialidad jurídica** adaptados al sistema continental chileno (importados y des-anglosajonizados de *claude-for-legal*):

1. **`chilean-employment-legal`** (`agente-laboral`): Despidos (Art. 161/160 CT), Ley Karin (21.643), 40 Horas (21.561), finiquitos y doctrina DT.
2. **`chilean-litigation-legal`** (`agente-litigios`): Demandas OJV Ley N° 20.886, cronología de hechos, recursos procesales y medidas precautorias.
3. **`chilean-administrative-legal`** (`agente-regulatorio`): Dictámenes e informes CGR, compras públicas (Ley 19.886) y vigilancia regulatoria.
4. **`chilean-energy-legal`** (`agente-energia`): Contratos PPA de clientes libres, transmisión eléctrica Ley 20.936 y discrepancias del Panel de Expertos.
5. **`chilean-environmental-legal`** (`agente-ambiental`): Fiscalizaciones SMA (SNIFA), infracciones a RCAs y Programas de Cumplimiento.
6. **`chilean-contract-legal`** (`agente-contratos`): Revisión de contratos, NDAs, cláusula penal (CC) y Ley 19.496 de Protección al Consumidor.
7. **`chilean-corporate-legal`** (`agente-corporativo`): Constitución de SpA (Ley 20.659) y S.A. (18.046), compliance CMF/SII y libre competencia (DL 211).
8. **`chilean-forensic-evidence`** (`agente-forense`): Peritaje documental de expedientes escaneados y OCR de resoluciones ilegibles.
9. **`chilean-probity-investigation`** (`agente-probidad`): Cruce de declaraciones patrimoniales DIP (InfoProbidad) y conflictos de interés.
10. **`chilean-dossier-assembly`** (`agente-expedientes`): Ensamblaje pericial de expedientes foliados con separadores probatorios.
11. **`chilean-notebooklm-grounding`** (`agente-investigacion-ia`): Investigación con citas fidedignas conectada a Google NotebookLM.
12. **`chilean-socratic-bar-exam`** (`agente-grado`): Interrogador socrático para egresados de derecho que preparan su Examen de Grado.
13. **`chilean-docket-watcher`** (`agente-vigilante`): Monitoreo de proveídos de la OJV y cálculo de plazos fatales en días hábiles judiciales.
14. **`chilean-legal-clinic`** (`agente-clinica`): Asistencia jurídica social para consultorios CAJ y traductor a Lenguaje Claro.
15. **`chilean-privacy-ip`** (`agente-propiedad-datos`): Tramitación de Derechos ARCO (Ley 19.628) y factibilidad marcaria ante INAPI.

---

## 💻 9. Guía Completa de la Consola CLI (`openlegal`)

Open Legal Chile incluye una potente interfaz de línea de comandos accesible mediante `openlegal`:

```bash
# Menú interactivo de la consola
openlegal

# Servidor MCP estándar para agentes de IA
openlegal mcp

# Chat jurídico interactivo con RAG soberano chileno
openlegal chat

# Búsqueda jurídica universal cruzada en los 10 organismos del Estado
openlegal search "confianza legitima contrata"

# Auditar un escrito bajo las 5 dimensiones forenses
openlegal critique escrito.txt

# Generar un borrador procesal formal OJV
openlegal generate demanda_civil

# Iniciar interrogación socrática para Examen de Grado
openlegal grado civil

# Analizar un proveído judicial y calcular sus plazos fatales
openlegal vigilar "Téngase por contestada la demanda y traslado para réplica"

# Traducir una resolución a Lenguaje Claro para usuarios de consultorio
openlegal clinica "Autos para fallo"

# Tramitar solicitud de Derechos ARCO de datos personales
openlegal arco

# Evaluar viabilidad de marca en INAPI
openlegal inapi "InnoJuris"

# Ejecutar auditoría integral 360° del sistema
openlegal audit

# Exportar escrito formal OJV a HTML, Markdown y JSON
openlegal export

# Diagnóstico de estado de los conectores
openlegal check
```

---

## 🛡️ 10. Certificación de Auditoría Institucional 360° (AUDIT.md)

Open Legal Chile está certificado mediante una suite de auditoría integral de **9 capas** que se ejecuta tanto localmente como en GitHub Actions:

```bash
./audit.sh
# O vía CLI:
openlegal audit
```

| Capa / Dimensión | Herramienta Estándar | Estado / Certificación |
| :--- | :--- | :--- |
| **1. Vulnerabilidades SCA** | `pypa/pip-audit` | **0 vulnerabilidades conocidas** (CVEs neutralizados) |
| **2. Seguridad SAST** | `PyCQA/bandit` | **0 fallas de inyección o deserialización** |
| **3. Semántica OWASP** | `semgrep/semgrep` | **0 hallazgos bloqueantes** (201 reglas analizadas) |
| **4. Fuga de Secretos** | `Yelp/detect-secrets` | **Zero Data Leak** (Cero llaves o credenciales expuestas) |
| **5. Tipado Estático** | `python/mypy` | **0 errores en modo estricto en 46 archivos fuente** |
| **6. Linter & PEP** | `astral-sh/ruff` | **100% de reglas de arquitectura y estilo aprobadas** |
| **7. Anti-Sobreingeniería**| `Ponytail` & `vulture`| **Filosofía Ponytail: Cero código muerto (*Lean already. Ship*)** |
| **8. Mantenibilidad** | `rubik/radon` | **Rango A en lógica sustantiva y conectores** |
| **9. Pruebas Funcionales** | `pytest-dev/pytest` | **70/70 pruebas unitarias superadas satisfactoriamente** |

Consulta el informe institucional pormenorizado en [`AUDIT.md`](AUDIT.md).

---

## 🧪 11. Pruebas Automatizadas y Verificación Continua

```bash
python3 -m pytest tests/ -v
# ============================== 70 passed in 1.35s ==============================
```

* **`.github/workflows/ci.yml`:** Matriz de integración continua en Ubuntu y Windows probando Python 3.10, 3.11, 3.12, 3.13 y 3.14.
* **`.github/workflows/audit.yml`:** Auditoría de seguridad y calidad estricta en cada commit y Pull Request.
* **`.github/workflows/state-api-monitor.yml`:** Monitor programado diario que verifica la disponibilidad y tiempos de respuesta de los portales del Estado de Chile.

---

## 📜 12. Licencia, Ética Forense y Responsabilidad Profesional

### Licencia Apache 2.0
Open Legal Chile está licenciado bajo la **Licencia Apache 2.0** ([`LICENSE`](LICENSE)). Permite el uso libre, estudio, modificación y redistribución tanto en ámbitos académicos como profesionales y comerciales.

### Compuerta de Validación Profesional Obligatoria
> ⚖️ **Aviso Forense y Deontológico:** Open Legal Chile es una infraestructura de asistencia técnica, investigación y docencia. Todo borrador, escrito, dictamen o análisis producido mediante inteligencia artificial debe ser obligatoriamente revisado y refrendado por un abogado habilitado para el ejercicio de la profesión antes de su firma, patrocinio o ingreso formal en la Oficina Judicial Virtual (OJV) o sede administrativa.

---

## 🌱 13. Cómo Contribuir

Las contribuciones académicas y técnicas de estudiantes, docentes y abogados son bienvenidas:

1. Revisa la [Guía de Contribución](CONTRIBUTING.md) y el [Código de Conducta](CODE_OF_CONDUCT.md).
2. Abre un **issue** o envía un **Pull Request** con nuevas fichas doctrinales o mejoras a los conectores.
3. Para sumar nuevas obras a la biblioteca dogmática, utiliza la herramienta [`scripts/doctrina_parser.py`](scripts/doctrina_parser.py) siguiendo el estándar de compresión de tokens.

---

<p align="center">
  <em>Desarrollado con vocación pública y rigor dogmático para la comunidad jurídica de la República de Chile.</em>
</p>
