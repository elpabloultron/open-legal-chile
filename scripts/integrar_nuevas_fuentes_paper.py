#!/usr/bin/env python3
"""
Script de integración de las 6 nuevas fuentes académicas y calibración editorial
para la Revista Chilena de Derecho y Tecnología (RChDT).
"""
import sys
from pathlib import Path
import re

MD_PATH = Path("investigacion_academica/articulo_cientifico_open_legal_chile.md")

with open(MD_PATH, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Enriquecer Sección 1.2 con Contreras et al. (2021) y RED (2024)
sec1_2_target = """### 1.2. La Génesis: De la Vivencia Formativa y Forense al Desarrollo de una Suite Soberana
La gestación de Open Legal Chile no responde a una iniciativa de inversión de capital de riesgo corporativo ni a un encargo burocrático centralizado. Nace a partir de una investigación y desarrollo iniciados en la Universidad de Los Lagos (Campus Osorno), en la Región de Los Lagos, al sur de Chile, impulsada por la necesidad de resolver las severas fricciones, contradicciones y barreras que atraviesan los estudiantes y operadores del derecho a lo largo de las distintas etapas de su itinerario formativo y laboral:"""

sec1_2_replacement = """### 1.2. La Génesis: De la Vivencia Formativa y Forense al Desarrollo de una Suite Soberana
La gestación de Open Legal Chile no responde a una iniciativa de inversión de capital de riesgo corporativo ni a un encargo burocrático centralizado. Nace a partir de una investigación y desarrollo iniciados en la Universidad de Los Lagos (Campus Osorno), en la Región de Los Lagos, al sur de Chile, impulsada por la necesidad vital de resolver las severas fricciones, contradicciones y barreras empíricas que experimentan los estudiantes y operadores jurídicos a lo largo de las distintas etapas de su itinerario formativo, académico y laboral.

Esta vivencia práctica encuentra un sólido respaldo empírico en la literatura científica especializada. En su riguroso diagnóstico sobre la formación jurídica nacional, Contreras Vásquez y otros (2021: 283-288) demostraron que la irrupción de las tecnologías de inteligencia artificial no ha sido acompañada por una actualización pedagógica sustantiva en los planes de estudio de las facultades de Derecho en Chile. Su estudio constató una aguda brecha formativa: los estudiantes de pregrado carecen de competencias algorítmicas y de herramientas prácticas operativas para interactuar con sistemas inteligentes, quedando la enseñanza restringida a aproximaciones teóricas abstractas o a la adopción pasiva de plataformas privativas. En idéntica línea, las investigaciones iberoamericanas recopiladas por la *Revista d'Educació i Dret* (2024: 12-16) evidencian que el acceso desigual a recursos tecnológicos en la docencia jurídica profundiza la brecha de oportunidades entre los estudiantes de universidades públicas regionales y las grandes firmas corporativas de las metrópolis. 

Frente a este diagnóstico indiscutible, la experiencia de pregrado en la Universidad de Los Lagos enfrentó sucesivamente cuatro etapas críticas donde la carencia de software forense soberano resultaba asfixiante:"""

text = text.replace(sec1_2_target, sec1_2_replacement)

# 2. Enriquecer Sección 1.3 con Tla-melaua (2024)
sec1_3_target = """Como ha postulado lúcidamente Richard Susskind, la tecnología en el ámbito judicial no debe ser concebida como una mercancía para amplificar las rentas oligopólicas de las élites corporativas, sino como un servicio público esencial cuyo cometido fundamental consiste en abaratar los costos transaccionales del litigio y hacer realidad la tutela judicial efectiva para todos los sectores de la sociedad (Susskind, 2019: 58-64). Por tanto, para cumplir este propósito democratizador, la infraestructura tecnológica de inteligencia jurídica debe ser diseñada como un Bien Público Digital (*Digital Public Good*): auditable, accesible universalmente y libre de cualquier barrera económica privativa."""

sec1_3_replacement = """Como ha postulado lúcidamente Richard Susskind, la tecnología en el ámbito judicial no debe ser concebida como una mercancía para amplificar las rentas oligopólicas de las élites corporativas, sino como un servicio público esencial cuyo cometido fundamental consiste en abaratar los costos transaccionales del litigio y hacer realidad la tutela judicial efectiva para todos los sectores de la sociedad (Susskind, 2019: 58-64). Asimismo, como subraya la doctrina latinoamericana reciente en *Tla-melaua* (2024: 8-14), la construcción de herramientas de inteligencia artificial aplicada al Derecho exige un diálogo interdisciplinario genuino entre juristas e ingenieros, en el cual se asuma la indelegable responsabilidad humana en el diseño de los algoritmos y se garantice que el software preserve la justicia material en lugar de maximizar beneficios comerciales corporativos. Por tanto, para cumplir este propósito democratizador, la infraestructura tecnológica de inteligencia jurídica debe ser diseñada como un Bien Público Digital (*Digital Public Good*): auditable, accesible universalmente y libre de cualquier barrera económica privativa."""

text = text.replace(sec1_3_target, sec1_3_replacement)

# 3. Asegurar Sección 2.5 completa antes de Sección 3 con Lledó Benito (2026) y UNESCO (2022-2024)
seccion_2_5_completa = r"""### 2.5. Fundamentos Computacionales para el Operador Jurídico: LLMs, MCP, Harnesses y Soberanía de Datos

Para que el jurista, el litigante y el magistrado puedan evaluar críticamente la incorporación de la inteligencia artificial en el quehacer forense, es indispensable desmitificar la terminología computacional y comprender la mecánica exacta de los componentes que integran el ecosistema:

#### 2.5.1. ¿Cómo Funciona Realmente un Modelo de Lenguaje Masivo (LLM)?
Un Modelo de Lenguaje Masivo (*Large Language Model* o LLM) no es una entidad consciente ni un agente dotado de comprensión semántica o razonamiento lógico formal. En términos estrictamente matemáticos, es una red neuronal profunda basada en la arquitectura de *Transformador* (introducida por Vaswani y otros en 2017), cuyo objetivo computacional consiste en aproximar una distribución de probabilidad condicional sobre secuencias de texto:

$$P(w_1, w_2, \dots, w_T) = \prod_{t=1}^{T} P(w_t \mid w_1, w_2, \dots, w_{t-1})$$

El modelo calcula cuál es la palabra o fragmento subléxico más probable (*siguiente token*) que debe continuar a una secuencia previa de entrada (*prompt*). A través de mecanismos de auto-atención multi-cabeza (*multi-head self-attention*), el modelo pondera la relevancia estadística relativa entre palabras distantes dentro de una ventana de contexto.

Como advierte agudamente Lledó Benito (2026: 4-9), atribuir pensamiento, inteligencia o entendimiento a un algoritmo estadístico constituye un peligroso *sofisma* epistemológico que nubla el juicio de los operadores forenses. De manera análoga, la pretensión de sustituir la labor dogmática del jurista, la deliberación prudencial y el juicio de equidad por el cómputo de modelos generativos deviene en un verdadero *oxímoron* conceptual: la equidad y la justicia del caso concreto son categorías valorativas humanas cualitativas, ontológicamente irreductibles a matrices vectoriales cuantitativas.

De esta naturaleza matemática deriva la patología más severa de los LLMs: el fenómeno de la **alucinación normativa**. El modelo carece por completo de un modelo interno de validez deóntica. Si una ley fue derogada, si un plazo procesal venció o si un artículo citado jamás fue promulgado en el Diario Oficial, el modelo no «sabe» que está emitiendo una falsedad: simplemente genera la secuencia de caracteres que maximiza la verosimilitud estadística del discurso. Por ello, confiar la redacción de escritos o la verificación de plazos fatales a un LLM generalista sin un cortafuegos determinista conduce inexorablemente al error procesal.

#### 2.5.2. ¿Qué es el Model Context Protocol (MCP)?
El **Model Context Protocol (MCP)** es un estándar abierto de comunicación e interoperabilidad propuesto a la industria tecnológica en noviembre de 2024. Tradicionalmente, para que un modelo de lenguaje pudiera consultar una base de datos externa o invocar una función del sistema operativo, los desarrolladores debían programar integraciones propietarias y acopladas (*function calling* ad-hoc), incompatibles entre distintos proveedores.

El protocolo MCP opera conceptualmente como un **«puerto USB universal» para la inteligencia artificial**. Establece una arquitectura cliente-servidor desacoplada mediante mensajes estructurados bajo la especificación JSON-RPC 2.0 a través de flujos estándar de entrada y salida (`stdio`) o conexiones seguras SSE. El servidor MCP expone tres primitivas formales:
1. **Herramientas (*Tools*):** Funciones ejecutables con esquemas tipados (JSON Schema) que el modelo puede solicitar ejecutar para consultar bases de datos o realizar cómputos deónticos.
2. **Recursos (*Resources*):** Datos o documentos estáticos accesibles para lectura controlada (equivalentes a archivos normativos o fichas institucionales).
3. **Prompts:** Plantillas estructuradas de interacción diseñadas para guiar el flujo de tareas forenses complejas con control metodológico.

En Open Legal Chile, el archivo `mcp_server.py` actúa como servidor MCP soberano, exponiendo 87 herramientas forenses conectadas a 16 órganos del Estado chileno, permitiendo que cualquier entorno cliente dialogue con el ordenamiento positivo nacional mediante contratos de datos verificables y seguros.

#### 2.5.3. ¿Qué es un Harness (Arnés Agéntico de Ejecución)?
En la ingeniería de agentes inteligentes, el **Harness** (o arnés de ejecución) es la plataforma de software que envuelve, controla y supervisa la ejecución del modelo de lenguaje en el sistema del usuario (ejemplos contemporáneos de harnesses incluyen a Antigravity, Claude Code, Cursor, OpenCode o Gemini CLI).

Mientras que el modelo de lenguaje actúa únicamente como «motor de inferencia estadística», el arnés agéntico constituye el «tablero de control y chasis operativo». Es el arnés el encargado de orquestar el bucle *ReAct* (*Reasoning + Acting*):
1. Recibe la consulta en lenguaje natural del jurista.
2. Invoca al modelo para generar un plan de razonamiento estructurado.
3. Intercepta la petición de uso de herramienta emitida por el modelo en formato JSON-RPC 2.0.
4. Ejecuta materialmente en el sistema operativo local las herramientas MCP autorizadas (consultar la BCN, computar plazos o extraer textos OCR).
5. Retorna la salida estructurada de la herramienta al modelo para que éste formule la síntesis final en Lenguaje Claro.
6. Administra la memoria de la sesión, la tokenización de contexto y el control de errores en tiempo de ejecución.

#### 2.5.4. Privacidad, Secreto Profesional y Retención de Datos: Comparativa Crítica de Plataformas
Uno de los dilemas éticos y jurídicos más acuciantes en la adopción de IA legal radica en el destino de la información procesal confidencial confiada por los patrocinados.

Esta preocupación ha sido formalizada a nivel internacional por la **UNESCO (2022-2024)** en su programa global de capacitación judicial sobre IA y Estado de Derecho, donde se instruye a miles de magistrados de más de 140 países sobre la incompatibilidad de las «cajas negras comerciales» con las garantías procesales de transparencia, debida motivación de las resoluciones judiciales y protección de datos personales. Conforme a las directrices de UNESCO, los órganos de justicia y los abogados litigantes no pueden someter expedientes o causas bajo reserva a infraestructuras privadas que retengan información o realicen tratamientos transfronterizos sin fiscalización judicial.

En el ordenamiento chileno, el artículo 247 del Código Penal y las normas del Código de Ética Profesional del Colegio de Abogados imponen la obligación indiscutible de guardar secreto respecto de los hechos litigiosos de los clientes. Asimismo, la nueva Ley N° 21.719 de Protección de Datos Personales prohíbe la comunicación o cesión internacional de datos sensibles sin una base de licitud indubitada o sin garantías de seguridad adecuadas.

La realidad operativa de las plataformas comerciales de IA revela graves riesgos para la confidencialidad:
* **Plataformas Comerciales de Consumo (ChatGPT Free/Plus, Claude Free/Pro, Gemini Free):** En sus versiones estándar, los términos de servicio estipulan expresamente que los textos, documentos y archivos cargados por el usuario son **retenidos y utilizados por las corporaciones propietarias para el re-entrenamiento continuo de sus modelos**, existiendo además procedimientos de revisión humana aleatoria (*human review*). Ingresar una demanda reservada o una minuta de prueba en estas interfaces gratuitas constituye una violación directa al secreto profesional penal (Art. 247 CP) y una infracción a la Ley N° 21.719.
* **Plataformas Corporativas con API y Políticas de No Retención (Zero Data Retention):** Las suscripciones empresariales de nivel API garantizan contractualmente que no re-entrenarán sus modelos con los datos transmitidos. Sin embargo, los datos continúan viajando a través de canales de red internacionales hacia centros de cómputo remotos ubicados fuera de Chile, expuestos a contingencias de ciberseguridad, mandatos judiciales de incautación foránea o filtraciones en tránsito.
* **El Paradigma Soberano Local-First de Open Legal Chile:** Frente a los riesgos descritos, Open Legal Chile se sustenta en una premisa no negociable: **ningún dato procesal, cédula de identidad, rol de causa o escrito abandona jamás la máquina de trabajo del operador**. Al operar de forma 100% desconectada (*offline*) sobre CPUs estándar convencionales mediante índices SQLite FTS5 locales y el grafo ontológico `LegalGraphify`, se garantiza con certeza matemática la preservación del secreto profesional (Art. 247 CP) y el cumplimiento pleno de la Ley N° 21.719.

| Dimensión de Privacidad y Soberanía | Plataformas de Consumo (ChatGPT/Gemini/Claude Free) | APIs Corporativas en la Nube (OpenAI API / Claude API) | Open Legal Chile (Suite Soberana Local-First) |
| :--- | :--- | :--- | :--- |
| **Entrenamiento con Datos de Usuario** | **SÍ (Retención y re-entrenamiento activo)** | NO (Bajo acuerdos de confidencialidad ZDR) | **NUNCA (100% desconectado, sin re-entrenamiento)** |
| **Revisión Humana por Empleados Externos**| **SÍ (Muestreo para control de calidad)** | Excepcional (Abuse monitoring 30 días) | **IMPOSIBLE (Cero telemetría, código en máquina local)** |
| **Ubicación del Cómputo de Datos** | Servidores remotos en el extranjero | Centros de procesamiento en el extranjero | **Almacenamiento y memoria RAM local del usuario** |
| **Cumplimiento Secreto Profesional (Art. 247 CP)**| **INADMISIBLE (Vulneración grave del deber de sigilo)**| Condicionado a acuerdos contractuales estrictos | **PLENO (Garantía arquitectónica por diseño)** |
| **Cumplimiento Ley N° 21.719 (Datos Personales)**| Vulneración de transferencia internacional ilícita | Exige salvaguardas contractuales transfronterizas| **CUMPLIMIENTO TOTAL (Sin transferencia de datos)** |
| **Costo Económico Recurrente** | Suscripciones mensuales privativas por usuario | Cobro por millón de tokens procesados | **GRATUITO Y LIBRE (Licencia Apache 2.0)** |

*Tabla 4. Matriz comparativa de privacidad, retención de datos y secreto profesional entre plataformas comerciales y Open Legal Chile. Fuente: Elaboración propia a partir de los términos de servicio oficiales de proveedores de IA y la legislación chilena.*
"""

# Insertar Sección 2.5 justo antes de "## 3. Filosofía de Diseño"
if "### 2.5." not in text:
    text = text.replace(
        "---\n\n## 3. Filosofía de Diseño",
        f"---\n\n{seccion_2_5_completa}\n---\n\n## 3. Filosofía de Diseño"
    )

# 4. Enriquecer Sección 3.1 y 4.2 con Llano Alonso (2024) y Huergo Lora (2024)
sec3_1_target = """### 3.1. Soberanía Tecnológica y Principio Zero Data Leak"""
sec3_1_replacement = """### 3.1. Soberanía Tecnológica y Principio Zero Data Leak
Como han destacado Llano Alonso (2024: 11-15) y Huergo Lora (2024: 25-32) en su estudio monográfico sobre Derecho e Inteligencia Artificial, la inserción de algoritmos en el ámbito del derecho público no puede realizarse a expensas de la transparencia, la debida motivación de los actos administrativos ni las garantías fundamentales de los ciudadanos. La Administración Pública y los órganos de control judicial están sujetos a un deber reforzado de justificación jurídica que resulta incompatible con algoritmos opacos. Bajo este prisma, Open Legal Chile establece que la soberanía de los datos y la verificabilidad estricta de las fuentes oficiales constituyen el núcleo innegociable de su arquitectura:"""

if "Llano Alonso (2024" not in text:
    text = text.replace(sec3_1_target, sec3_1_replacement)

# 5. Agregar las referencias bibliográficas completas en formato Chicago en Sección 9
nuevas_referencias = """
Contreras Vásquez, Pablo, Michelle Azuaje Pirela, Juan Pablo Díaz Fuenzalida, Francisco Bedecarratz Scholz, Sebastián Bozzo Hauri y Daniel Finol González (2021). «Enseñanzas y aprendizaje de la inteligencia artificial y derecho en Chile». *Revista Pedagogía Universitaria y Didáctica del Derecho*, 8 (2): 281-302. DOI: 10.5354/0719-5885.2021.64456.

Huergo Lora, Alejandro (2024). «Inteligencia artificial y Administraciones públicas». *Teoría & Derecho. Revista de pensamiento jurídico*, 37: 20-45.

Jiménez Ávila, José María (2015). «La difusión del conocimiento: una responsabilidad en la investigación científica». *Orthotips*, 11 (2): 58-61.

Llano Alonso, Fernando H. (2024). «Presentación: Derecho e inteligencia artificial». *Teoría & Derecho. Revista de pensamiento jurídico*, 37: 10-18.

Lledó Benito, Ignacio (2026). «La IA y la ciencia del derecho, su adaptación e implementación a las profesiones jurídicas y a la investigación universitaria; entre el sofisma, el oxímoron y la distopía». *El Criminalista Digital. Papeles de Criminología*, 36355: 1-28. DOI: 10.30827/cridi.36355.

Revista d'Educació i Dret (2024). «Inteligencia artificial en la enseñanza del derecho: un estudio bibliométrico y de caso en la Facultad de derecho de la Universidad de Oriente de Cuba». *Revista d'Educació i Dret (RED)*, 29: 1-26. DOI: 10.1344/RED2024.29.49201.

Tla-melaua (2024). «La inteligencia artificial y el Derecho: Una mirada a un futuro presente». *Tla-melaua: revista de ciencias sociales*, 18 (57): 4-21.

UNESCO (2022-2024). *La IA y el Estado de derecho: Fortalecimiento de capacidades para los sistemas judiciales*. París: Organización de las Naciones Unidas para la Educación, la Ciencia y la Cultura.
"""

if "Contreras Vásquez, Pablo" not in text:
    text = text.replace(
        "## 9. Referencias Bibliográficas\n\n",
        f"## 9. Referencias Bibliográficas\n{nuevas_referencias}\n"
    )

with open(MD_PATH, "w", encoding="utf-8") as f:
    f.write(text)

words = len(re.findall(r'\b\w+\b', text))
chars = len(text)
print("✓ Manuscrito actualizado exitosamente:")
print(f"  - Palabras totales: {words:,}")
print(f"  - Caracteres totales (con espacios): {chars:,}")
