# Medición del ahorro de tokens de LegalGraphify

*Generado por `scripts/medir_ahorro_tokens.py` el 2026-11-22 16:18 UTC (PYTHONHASHSEED=0).*

## Método

**Qué se mide.** Para cada una de las instituciones del grafo se comparan dos números:

- **Texto completo (tokens):** el tamaño del archivo doctrinal completo de la obra que
  contiene a la institución, es decir `max(1, palabras_del_archivo * 1.3)`. Es el baseline
  que el motor registra en `tokens_archivo`: lo que costaría inyectar el documento entero
  en el prompt en lugar del subgrafo.
- **Subgrafo (tokens):** el tamaño de la ficha YAML hiper-densa que el motor realmente
  devuelve al consultar esa institución (`consultar_subgrafo()`), medida igual:
  `palabras_de_la_ficha * 1.3`.
- **Ahorro (%):** `(texto_completo - subgrafo) / texto_completo * 100`.

Ambos números los calcula el motor (`legal_graphify.py`, campo `metricas_tokens`);
este script solo los recorre y los tabula. El grafo medido tiene 18954 nodos y 57246 aristas.

**Qué NO se mide.**

- **No hay tokenizador real.** El factor `palabras * 1.3` es una estimación (del orden
  del BPE de GPT/Llama para texto español), no el conteo de un tokenizador concreto.
  Otro tokenizador daría cifras distintas en ambos lados de la comparación.
- **No se mide lo que costaría un RAG convencional** ni la lectura de manuales enteros
  por otro mecanismo: se compara subgrafo contra el archivo doctrinal fuente, que es el
  baseline que el motor registra en `tokens_archivo`.
- **No se mide calidad, precisión ni alucinación.** Es una medición de tamaño de texto,
  no de utilidad de la respuesta.
- **No es el ahorro de todo el pipeline.** El corpus crudo → Markdown de alta densidad
  (`scripts/doctrina_parser.py`, `doc2md_ingestor.py`) es otra métrica y no se mide aquí.

**Nota de reproducibilidad.** El tamaño exacto de la ficha depende del orden de iteración
de un `set` dentro de `legal_graphify.py`, que varía con la semilla de hash de Python;
por eso el script se re-ejecuta con `PYTHONHASHSEED=0`. Entre semillas la diferencia es de
unos pocos tokens por institución y no cambia el rango publicado.

## Resultado global

- **Instituciones medidas:** 7677
- **Ahorro por institución:** mínimo 0,0 %, mediana 99,9 %, máximo 100,0 % (media 99,5 %)
- **Subgrafos devueltos:** entre 29 y 544 tokens (mediana 100)
- **Textos completos de las obras:** entre 135 y 313985 tokens (mediana 95131)
- **Instituciones con ahorro ≥ 85 %:** 7584 de 7677
- **Instituciones con ahorro ≥ 80 %:** 7603 de 7677
- **Instituciones con ahorro < 70 %:** 43 de 7677

## Tabla completa (105 instituciones)

| # | Institución | Área | Texto completo (tokens) | Subgrafo (tokens) | Ahorro | Factor |
|---:|---|---|---:|---:|---:|---:|
| 1 | (art. 470 n° 6) | General | 313985 | 53 | 100,0 % | 5924,2x |
| 2 | (arts. 193 y 194) | General | 313985 | 75 | 100,0 % | 4186,5x |
| 3 | (arts. 240 y 240 bis) | General | 313985 | 44 | 100,0 % | 7136,0x |
| 4 | (sólo cuando se trata de la primer venta de una unidad que forma parte | Civil | 153962 | 63 | 100,0 % | 2443,8x |
| 5 | (sólo cuando se trata de la venta de una unidad que forma parte de un | Civil | 153962 | 57 | 100,0 % | 2701,1x |
| 6 | (‘ds 66’).50 | Judicial | 134465 | 57 | 100,0 % | 2359,0x |
| 7 | 1 Comité para la Prevención de la Tortura, Prevención de la tortura y situación de | Penal | 194788 | 68 | 100,0 % | 2864,5x |
| 8 | 1 Corte Interamericana de Derechos Humanos, caso Tribunal Constitucional con | Judicial | 144656 | 44 | 100,0 % | 3287,6x |
| 9 | 1 Más información sobre los tribunales de tratamiento de drogas disponible en | Penal | 194788 | 75 | 100,0 % | 2597,2x |
| 10 | 1 Por ello en este libro se comprende también, en un capítulo aparte, el tema de | Penal | 194788 | 78 | 100,0 % | 2497,3x |
| 11 | 1 Pueblo latino que se asentó en el valle de las siete colinas y del que se dice que | Constitucional | 177323 | 74 | 100,0 % | 2396,3x |
| 12 | 1. Cuando se impongan sanciones penales previstas por la legislación | Judicial | 134465 | 67 | 100,0 % | 2006,9x |
| 13 | 1. La identificación de los principios en cuanto tales, vale decir, la | Judicial | 144656 | 58 | 100,0 % | 2494,1x |
| 14 | 1. Mesa intersectorial para la protección de Sitios de Memoria (ID | Constitucional | 177323 | 85 | 100,0 % | 2086,2x |
| 15 | 1. No será aplicable lo dispuesto en la letra a) del inciso tercero del artícu- | Penal | 194788 | 96 | 100,0 % | 2029,0x |
| 16 | 1. Regla general: se constituirán en primera citación con la asistencia de los | Civil | 192585 | 94 | 100,0 % | 2048,8x |
| 17 | 1. Si existe querellante particular que hubiere deducido acusación | Penal | 211066 | 92 | 100,0 % | 2294,2x |
| 18 | 1. Todos los programas de cooperación para el desarrollo, las políticas | Constitucional | 177323 | 83 | 100,0 % | 2136,4x |
| 19 | 1.1                Concepto | Constitucional | 112823 | 40 | 100,0 % | 2820,6x |
| 20 | 1.1                Conceptos básicos: la criminalidad de | Penal | 119528 | 59 | 100,0 % | 2025,9x |
| 21 | 1.1           Presupuesto de la responsabilidad | Civil | 142015 | 66 | 100,0 % | 2151,7x |
| 22 | 1.1.1 De la informática jurídica a la inteligencia | Judicial | 96536 | 42 | 100,0 % | 2298,5x |
| 23 | 1.2.4.1.2. Derechos sociales | Constitucional | 115835 | 53 | 100,0 % | 2185,6x |
| 24 | 1.3.11.2 Consecuencias del incumplimiento del deber de | Civil | 142015 | 68 | 100,0 % | 2088,5x |
| 25 | 1.4              El aporte alemán: derecho a la | Constitucional | 104063 | 40 | 100,0 % | 2601,6x |
| 26 | 1.4              Las estrategias para lidiar con las | Constitucional | 112823 | 55 | 100,0 % | 2051,3x |
| 27 | 1.4           El contenido del | Civil | 142015 | 40 | 100,0 % | 3550,4x |
| 28 | 1.4     Garantías fundamentales y tecnologías de | Judicial | 96536 | 41 | 100,0 % | 2354,5x |
| 29 | 1.4.8 Las consecuencias de la infracción de | Civil | 142015 | 59 | 100,0 % | 2407,0x |
| 30 | 1.5               La autodeterminación informativa | Constitucional | 104063 | 45 | 100,0 % | 2312,5x |
| 31 | 10 Artículo 79 del Código Penal: No podrá ejecutarse pena alguna sino en virtud | Penal | 194788 | 83 | 100,0 % | 2346,8x |
| 32 | 10 Estos casos de imprudencia en materia de prevaricación han fundado el valor | Penal | 178516 | 58 | 100,0 % | 3077,9x |
| 33 | 10 Nº 11) | General | 313985 | 45 | 100,0 % | 6977,4x |
| 34 | 10 Para Rodríguez Collao y Ossandón Widow (2021: 366), las dos hipótesis del | Penal | 178516 | 65 | 100,0 % | 2746,4x |
| 35 | 10 Sentencia Corte de Apelaciones de Santiago, rol 2.100-2021, 11 de noviembre | Penal | 178516 | 65 | 100,0 % | 2746,4x |
| 36 | 10.1     Los títulos ejecutivos de | Laboral | 100583 | 49 | 100,0 % | 2052,7x |
| 37 | 10.5     Normas | Laboral | 100583 | 49 | 100,0 % | 2052,7x |
| 38 | 100               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 55 | 100,0 % | 5708,8x |
| 39 | 102               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 54 | 100,0 % | 5814,5x |
| 40 | 103   Cuaderno de buenas prácticas en materia de política de género, del Poder Judicial. Disponible en http:// | Penal | 211066 | 68 | 100,0 % | 3103,9x |
| 41 | 104               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 68 | 100,0 % | 4617,4x |
| 42 | 106               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 57 | 100,0 % | 5508,5x |
| 43 | 107 Sentencia Corte de Apelaciones de Santiago, 22 de mayo de 2017, rol ingreso | Judicial | 144656 | 55 | 100,0 % | 2630,1x |
| 44 | 108 Sentencia Corte Suprema de 2 de octubre de 2017, rol de ingreso número | Judicial | 144656 | 48 | 100,0 % | 3013,7x |
| 45 | 108. Corte Suprema, Contra Gómez (2008): sentencia 24 enero 2008, rol Nº | Penal | 121924 | 58 | 100,0 % | 2102,1x |
| 46 | 11        Prisión en su grado mínimo | Penal | 194788 | 87 | 100,0 % | 2238,9x |
| 47 | 11. Contrato libremente discutido, para quienes concurren a su celebración: sin perjuicio | Civil | 192585 | 74 | 100,0 % | 2602,5x |
| 48 | 11. Coordinación de acciones regionales para la educación sobre el | Constitucional | 177323 | 78 | 100,0 % | 2273,4x |
| 49 | 11. Razonabilidad: los controles implementados por la persona | Penal | 119528 | 59 | 100,0 % | 2025,9x |
| 50 | 11.2. Origen y evolución de la noción de Estado de Derecho en la época previa | General | 129559 | 54 | 100,0 % | 2399,2x |
| 51 | 11.3. El Estado de Derecho en la época previa a la del constitucionalismo | General | 129559 | 49 | 100,0 % | 2644,1x |
| 52 | 11.6. Elementos del Estado de Derecho en las normas internacionales | General | 129559 | 53 | 100,0 % | 2444,5x |
| 53 | 110               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 58 | 100,0 % | 5413,5x |
| 54 | 110   PEÑAILILLO (2003), p. 498 | Civil | 142015 | 49 | 100,0 % | 2898,3x |
| 55 | 112               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 49 | 100,0 % | 6407,9x |
| 56 | 113 Acta 128 de 2015 de la Corte Suprema de 17 de agosto de 2015. Disponible en | Judicial | 144656 | 49 | 100,0 % | 2952,2x |
| 57 | 113 Nieva (2010: 136) considera que el juicio jurisdiccional no es aleatorio, sino | Judicial | 150341 | 50 | 100,0 % | 3006,8x |
| 58 | 116               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 53 | 100,0 % | 5924,2x |
| 59 | 118               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 59 | 100,0 % | 5321,8x |
| 60 | 119 Código Sanitario, todavía sería posible no considerar su sanción penal si la | General | 313985 | 58 | 100,0 % | 5413,5x |
| 61 | 12 D.L. N° 26 de 1924, que declara como instrumentos públicos los documentos | General | 313985 | 93 | 100,0 % | 3376,2x |
| 62 | 12 Decreto Supremo 381, que promulga la Convención sobre el Derecho de los | Constitucional | 177323 | 84 | 100,0 % | 2111,0x |
| 63 | 12 Para Guzmán Dálbora, no es asimilable la figura porque, a diferencia del hurto | Penal | 178516 | 68 | 100,0 % | 2625,2x |
| 64 | 12 Se ha cuestionado esta referencia por estimarse precisamente redundante, al ya | Penal | 178516 | 54 | 100,0 % | 3305,9x |
| 65 | 12 Sentencia de la Corte de Apelaciones de Santiago, rol 726-2010, 13 de junio de | Penal | 178516 | 55 | 100,0 % | 3245,7x |
| 66 | 12 Ya hemos señalado que no necesariamente todo delito especial propio es un | Penal | 178516 | 48 | 100,0 % | 3719,1x |
| 67 | 12. Habilitar en la página Web del Poder Judicial un hipervínculo | Constitucional | 177323 | 85 | 100,0 % | 2086,2x |
| 68 | 12.1             Origen y noción | Laboral | 100583 | 42 | 100,0 % | 2394,8x |
| 69 | 120               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 75 | 100,0 % | 4186,5x |
| 70 | 121 Juzgados de | Procesal | 94881 | 36 | 100,0 % | 2635,6x |
| 71 | 122               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 61 | 100,0 % | 5147,3x |
| 72 | 124               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 67 | 100,0 % | 4686,3x |
| 73 | 126               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 68 | 100,0 % | 4617,4x |
| 74 | 126. En cualquier materia, inclusive en la laboral y la administrativa, la | Judicial | 144656 | 68 | 100,0 % | 2127,3x |
| 75 | 128                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 76 | 100,0 % | 4131,4x |
| 76 | 13 Este último término sí se considera en el inciso segundo de la norma, donde | Penal | 178516 | 75 | 100,0 % | 2380,2x |
| 77 | 13 Sentencia de la Corte de Apelaciones de Concepción, 15de julio de 2016, rol | Judicial | 150341 | 63 | 100,0 % | 2386,4x |
| 78 | 13)DISPOSICIONES COMUNES A TODO PROCEDIMIENTO.Carlos | Procesal | 95124 | 46 | 100,0 % | 2067,9x |
| 79 | 13. No se deberá negar a los menores privados de libertad, por razón de | Penal | 194788 | 93 | 100,0 % | 2094,5x |
| 80 | 13.2   Procedimiento de | Penal | 211066 | 66 | 100,0 % | 3198,0x |
| 81 | 13.3             Despido discriminatorio | Laboral | 100583 | 46 | 100,0 % | 2186,6x |
| 82 | 13.3. Irrenunciabilidad de la acción rescisoria por lesión enorme. 13.4. Efectos de la | Civil | 153962 | 70 | 100,0 % | 2199,5x |
| 83 | 13.3.1 Plazo judicial para el cierre de la investigación | Penal | 211066 | 101 | 100,0 % | 2089,8x |
| 84 | 13.4          Medidas | Penal | 211066 | 49 | 100,0 % | 4307,5x |
| 85 | 13.5.4 Sustitución de la prisión preventiva por caución | Penal | 211066 | 93 | 100,0 % | 2269,5x |
| 86 | 13.5.7 Ejecución de la prisión preventiva | Penal | 211066 | 93 | 100,0 % | 2269,5x |
| 87 | 13.5.8 Duración de la prisión preventiva | Penal | 211066 | 91 | 100,0 % | 2319,4x |
| 88 | 13.6   Análisis de casos de prisión preventiva | Penal | 211066 | 80 | 100,0 % | 2638,3x |
| 89 | 131   Un desarrollo de dichas exigencias puede encontrarse en LÓPEZ y ELORRIAGA (2017), pp. 445 y ss.; y en | Civil | 142015 | 70 | 100,0 % | 2028,8x |
| 90 | 132               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 52 | 100,0 % | 6038,2x |
| 91 | 134               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 53 | 100,0 % | 5924,2x |
| 92 | 136               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 76 | 100,0 % | 4131,4x |
| 93 | 14           Si hay eximentes pero están incompletas, se aplica el artículo 11 número 1 o el | Penal | 194788 | 62 | 100,0 % | 3141,7x |
| 94 | 14 Ministerio Público, «Instrucción general que imparte criterios de actuación | Penal | 178516 | 89 | 100,0 % | 2005,8x |
| 95 | 14 Para conocer el detalle de las metas establecidas para cada Objetivo, véase | Constitucional | 177323 | 50 | 100,0 % | 3546,5x |
| 96 | 14 Sentencia del Tribunal Constitucional 977, considerando vigesimoprimero. En | Judicial | 144656 | 72 | 100,0 % | 2009,1x |
| 97 | 14 Sentencia del Tribunal Oral en lo Penal de Quillota, RIT 83-2013, 26 de octubre | Penal | 178516 | 50 | 100,0 % | 3570,3x |
| 98 | 14. DUCE, Mauricio (2014): “Derecho a confrontación y uso de declaraciones | Penal | 211066 | 75 | 100,0 % | 2814,2x |
| 99 | 14. Incorporación de la variable Riesgo de Desastres en Proyectos de | Constitucional | 177323 | 81 | 100,0 % | 2189,2x |
| 100 | 14. Los siguientes asuntos que se susciten entre cónyuges, relativos al régimen | Familia | 190697 | 91 | 100,0 % | 2095,6x |
| 101 | 14. Pacto de Integridad en Licitaciones Públicas (ID 596). Cumpli- | Constitucional | 177323 | 87 | 100,0 % | 2038,2x |
| 102 | 14. Planes de Prevención y/o Descontaminación Atmosférica (ID | Constitucional | 177323 | 85 | 100,0 % | 2086,2x |
| 103 | 14. Velar por la adecuada representación judicial especializada de las | Constitucional | 177323 | 79 | 100,0 % | 2244,6x |
| 104 | 14.1     Características del | Laboral | 100583 | 42 | 100,0 % | 2394,8x |
| 105 | 14.3     Las cotizaciones obligatorias del régimen de | Laboral | 100583 | 50 | 100,0 % | 2011,7x |
| 106 | 14.3   Reapertura de la | Penal | 211066 | 55 | 100,0 % | 3837,6x |
| 107 | 14.4   Los sobreseimientos | Penal | 211066 | 97 | 100,0 % | 2175,9x |
| 108 | 14.5     Los depósitos | Laboral | 100583 | 46 | 100,0 % | 2186,6x |
| 109 | 14.5.1 La decisión de no perseverar en el procedimiento | Penal | 211066 | 94 | 100,0 % | 2245,4x |
| 110 | 14.6          Análisis de casos de sobreseimientos definitivos | Penal | 211066 | 71 | 100,0 % | 2972,8x |
| 111 | 14.6     Las cotizaciones | Laboral | 100583 | 42 | 100,0 % | 2394,8x |
| 112 | 140               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 101 | 100,0 % | 3108,8x |
| 113 | 142               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 67 | 100,0 % | 4686,3x |
| 114 | 144               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 133 | 100,0 % | 2360,8x |
| 115 | 144   Al respecto, véase PANTALEÓN (1991), pp. 1580-1582; MORALES MORENO (2010), pp. 157-158; y DE LA MAZA | Civil | 142015 | 70 | 100,0 % | 2028,8x |
| 116 | 146                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 50 | 100,0 % | 6279,7x |
| 117 | 15 Como tal, entonces, junto a la probabilidad matemática o pascaliana existiría | Judicial | 150341 | 72 | 100,0 % | 2088,1x |
| 118 | 15 Nº 2 y puede ser perfectamente castigado por su inducción a la negociación | General | 313985 | 65 | 100,0 % | 4830,5x |
| 119 | 15 Sentencia Tribunal Oral en lo Penal de Castro, RIT 36-2009, 7 de octubre de | Penal | 178516 | 87 | 100,0 % | 2051,9x |
| 120 | 15 Sentencia de la Corte de Apelaciones de Santiago, 28 de octubre de 2021, rol | Judicial | 150341 | 55 | 100,0 % | 2733,5x |
| 121 | 15.1.3 Actuaciones eventuales del acusado | Penal | 211066 | 68 | 100,0 % | 3103,9x |
| 122 | 15.2.1 Verificación de asistencia | Penal | 211066 | 104 | 100,0 % | 2029,5x |
| 123 | 15.2.10 Llamado a conciliación en la acción civil | Penal | 211066 | 93 | 100,0 % | 2269,5x |
| 124 | 15.2.11 Exclusión de prueba | Penal | 211066 | 102 | 100,0 % | 2069,3x |
| 125 | 15.2.12 Oportunidad para reclamar | Penal | 211066 | 92 | 100,0 % | 2294,2x |
| 126 | 15.2.6 Posibilidad de procedimiento abreviado | Penal | 211066 | 94 | 100,0 % | 2245,4x |
| 127 | 15.2.9 Decisión acerca de las excepciones | Penal | 211066 | 93 | 100,0 % | 2269,5x |
| 128 | 15.4   Análisis de casos de exclusión | Penal | 211066 | 59 | 100,0 % | 3577,4x |
| 129 | 150 B debiera, en estricto rigor, considerarse consumida o, más bien, copenada | General | 313985 | 63 | 100,0 % | 4983,9x |
| 130 | 16 Organización de las Naciones Unidas, «Resolución aprobada por la Asamblea | Constitucional | 177323 | 57 | 100,0 % | 3110,9x |
| 131 | 16 Sentencia Corte de Apelaciones de Puerto Montt, rol 77-2011, 19 de mayo de | Penal | 178516 | 71 | 100,0 % | 2514,3x |
| 132 | 16.1   Suspensión condicional | Penal | 211066 | 52 | 100,0 % | 4059,0x |
| 133 | 16.2           Requisitos de | Penal | 211066 | 83 | 100,0 % | 2543,0x |
| 134 | 16.6.1 Oportunidad | Penal | 211066 | 87 | 100,0 % | 2426,0x |
| 135 | 16.6.2 Requisitos de procedencia | Penal | 211066 | 81 | 100,0 % | 2605,8x |
| 136 | 16.6.3 Efectos | Penal | 211066 | 85 | 100,0 % | 2483,1x |
| 137 | 16.6.4 Registro | Penal | 211066 | 80 | 100,0 % | 2638,3x |
| 138 | 16.7   Análisis de casos de suspensiones | Penal | 211066 | 88 | 100,0 % | 2398,5x |
| 139 | 162               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 50 | 100,0 % | 6279,7x |
| 140 | 164   Para más información, veáse www.deis.cl | Constitucional | 121906 | 55 | 100,0 % | 2216,5x |
| 141 | 168   Referencias | Judicial | 87950 | 37 | 100,0 % | 2377,0x |
| 142 | 17 En los países anglosajones, incluso, los casos se denominan como «el Estado | Judicial | 144656 | 57 | 100,0 % | 2537,8x |
| 143 | 17 Para más información, véase Díez de Velasco (2007: 673-676) y Consejo de | Constitucional | 177323 | 66 | 100,0 % | 2686,7x |
| 144 | 17.1      Concepto | Laboral | 100583 | 40 | 100,0 % | 2514,6x |
| 145 | 17.1.1 Características del procedimiento abreviado | Penal | 211066 | 85 | 100,0 % | 2483,1x |
| 146 | 17.1.4 Actividad de otros intervinientes | Penal | 211066 | 70 | 100,0 % | 3015,2x |
| 147 | 17.1.5 La decisión del juez de garantía ante la | Penal | 211066 | 89 | 100,0 % | 2371,5x |
| 148 | 17.1.8 La sentencia del abreviado (art. 412 CPP) | Penal | 211066 | 93 | 100,0 % | 2269,5x |
| 149 | 17.1.9 Recursos en contra de la sentencia | Penal | 211066 | 84 | 100,0 % | 2512,7x |
| 150 | 17.2         Procedimiento | Penal | 211066 | 53 | 100,0 % | 3982,4x |
| 151 | 17.2.1 Ámbito de aplicación | Penal | 211066 | 79 | 100,0 % | 2671,7x |
| 152 | 17.2.4 Características del procedimiento simplificado | Penal | 211066 | 80 | 100,0 % | 2638,3x |
| 153 | 17.2.5 Simplificado del 393 bis CPP | Penal | 211066 | 100 | 100,0 % | 2110,7x |
| 154 | 17.3.1 Estatuto aplicable | Penal | 211066 | 74 | 100,0 % | 2852,2x |
| 155 | 17.3.5 Imparcialidad del juzgador | Penal | 211066 | 76 | 100,0 % | 2777,2x |
| 156 | 17.4   Análisis de casos de procedimientos abreviados | Penal | 211066 | 74 | 100,0 % | 2852,2x |
| 157 | 174               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 137 | 100,0 % | 2291,9x |
| 158 | 176               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 53 | 100,0 % | 5924,2x |
| 159 | 178               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 57 | 100,0 % | 5508,5x |
| 160 | 18 En este sentido, véase la sentencia de la Corte Suprema, 2 de julio de 2008, rol | Familia | 123490 | 59 | 100,0 % | 2093,1x |
| 161 | 18 Sentencia de a Corte de Apelaciones de Concepción, 17 de febrero de 2022, rol | Judicial | 150341 | 58 | 100,0 % | 2592,1x |
| 162 | 18.1   Estructura del | Penal | 211066 | 52 | 100,0 % | 4059,0x |
| 163 | 18.2      Obligación de afiliación | Laboral | 100583 | 48 | 100,0 % | 2095,5x |
| 164 | 18.2.7 La declaración de los testigos | Penal | 211066 | 85 | 100,0 % | 2483,1x |
| 165 | 18.3.1.1 Artículo 295: Libertad de prueba | Penal | 211066 | 89 | 100,0 % | 2371,5x |
| 166 | 18.3.1.2 El sistema de valoración libre | Penal | 211066 | 102 | 100,0 % | 2069,3x |
| 167 | 18.3.5 Contenido del acta de deliberación | Penal | 211066 | 88 | 100,0 % | 2398,5x |
| 168 | 180               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 48 | 100,0 % | 6541,4x |
| 169 | 186                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 76 | 100,0 % | 4131,4x |
| 170 | 186. Ministro de Fuero, Riquelme con Lecaros y otros (2005): sentencia 14 enero | Penal | 121924 | 58 | 100,0 % | 2102,1x |
| 171 | 187   DOMÍNGUEZ (2012), pp. 1-4 (en El Mercurio Legal). Para un comentario acerca de la entrevista, véase CAR- | Civil | 142015 | 71 | 100,0 % | 2000,2x |
| 172 | 19            Hay delitos en que se obliga a imponer la pena superior en grado (por ejemplo, el | Penal | 194788 | 97 | 100,0 % | 2008,1x |
| 173 | 19 Artículo 240 numeral 7, artículo 287, artículo 287 ter y artículo 470 numeral 11 | Penal | 178516 | 48 | 100,0 % | 3719,1x |
| 174 | 19 Organización de las Naciones Unidas, «Procedimientos especiales del Consejo | Constitucional | 177323 | 67 | 100,0 % | 2646,6x |
| 175 | 19.1           Juez de garantía y control | Penal | 211066 | 55 | 100,0 % | 3837,6x |
| 176 | 190               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 61 | 100,0 % | 5147,3x |
| 177 | 191      Heine (2006), p. 553 | Penal | 119528 | 44 | 100,0 % | 2716,5x |
| 178 | 192               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 72 | 100,0 % | 4360,9x |
| 179 | 193 Nº 2): aquí lo importante no es tanto suponer la participación de per- | General | 313985 | 80 | 100,0 % | 3924,8x |
| 180 | 193 Nº 8) | General | 313985 | 52 | 100,0 % | 6038,2x |
| 181 | 194               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 84 | 100,0 % | 3737,9x |
| 182 | 196                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 70 | 100,0 % | 4485,5x |
| 183 | 198                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 63 | 100,0 % | 4983,9x |
| 184 | 1996. Sostiene que siendo el banco el actual titular de 77 unidades del Edificio, y por ser | Civil | 192585 | 93 | 100,0 % | 2070,8x |
| 185 | 1997 Convención sobre la prohibición del empleo, almacenamiento, producción y | Penal | 121924 | 57 | 100,0 % | 2139,0x |
| 186 | 2 Así aparece en motivo séptimo de la sentencia de la Corte de Apelaciones de | Penal | 194788 | 89 | 100,0 % | 2188,6x |
| 187 | 2 Habida cuenta que en el propio párrafo 5 las figuras de malversación se hacen | Penal | 178516 | 85 | 100,0 % | 2100,2x |
| 188 | 2 Para más información, véase HRBA Portal, «The Human Rights Based Approach | Constitucional | 177323 | 62 | 100,0 % | 2860,0x |
| 189 | 2 Sentencia del Tribunal Constitucional, 19-07-2018, rol 3996-2017, considerando | Judicial | 150341 | 66 | 100,0 % | 2277,9x |
| 190 | 2 Véase Garrido Montt (1997: 330 y ss.), Novoa Monreal (2005), Varas Videla | Penal | 178516 | 55 | 100,0 % | 3245,7x |
| 191 | 2 utm                  1       4 | Judicial | 81476 | 39 | 100,0 % | 2089,1x |
| 192 | 2. Diseño e implementación de protocolos sobre sitios de memoria | Constitucional | 177323 | 81 | 100,0 % | 2189,2x |
| 193 | 2. Doble estándar en materia de indisolubilidad matrimonial: fin de una hipocresía real | Familia | 190697 | 94 | 100,0 % | 2028,7x |
| 194 | 2. El condenado no podrá ser favorecido con ninguno de los benefi- | Penal | 194788 | 91 | 100,0 % | 2140,5x |
| 195 | 2. En las obligaciones de medios, la necesaria consideración de la | Civil | 142015 | 70 | 100,0 % | 2028,8x |
| 196 | 2. Para tratar las materias señaladas en los números 1 al 5 del inc. 5° del art. 17º, se | Civil | 192585 | 94 | 100,0 % | 2048,8x |
| 197 | 2. Que la complejidad del caso no permitiere pronunciar inmedia- | Penal | 211066 | 62 | 100,0 % | 3404,3x |
| 198 | 2.1               En torno a la historia y | Judicial | 96536 | 45 | 100,0 % | 2145,2x |
| 199 | 2.1          Alcances prácticosde la | Judicial | 83934 | 37 | 100,0 % | 2268,5x |
| 200 | 2.1 Las disposiciones pertinentes de las presentes reglas se aplicarán a | Penal | 194788 | 89 | 100,0 % | 2188,6x |
| 201 | 2.1.5.5 Debate: responsabilidades de | Constitucional | 112823 | 53 | 100,0 % | 2128,7x |
| 202 | 2.12.7 Jurisprudencia en sede de protección | Judicial | 134465 | 57 | 100,0 % | 2359,0x |
| 203 | 2.2              El principio constitucional | Judicial | 81476 | 33 | 100,0 % | 2469,0x |
| 204 | 2.2           El derecho | Constitucional | 121906 | 53 | 100,0 % | 2300,1x |
| 205 | 2.2     Estructura de la | Administrativo | 89720 | 41 | 100,0 % | 2188,3x |
| 206 | 2.2 Actas de la Corte Suprema                                                        76 | Procesal | 94881 | 44 | 100,0 % | 2156,4x |
| 207 | 2.2 Las reglas se aplicarán sin discriminación alguna por motivos de | Penal | 194788 | 75 | 100,0 % | 2597,2x |
| 208 | 2.2. Según se compre un inmueble (o mueble, según Rodríguez Grez) con valores | Familia | 136567 | 59 | 100,0 % | 2314,7x |
| 209 | 2.2.2 La obligación de proteger interpretada | Constitucional | 112823 | 50 | 100,0 % | 2256,5x |
| 210 | 2.2.2 Tratamiento de datos personales | Judicial | 96536 | 40 | 100,0 % | 2413,4x |
| 211 | 2.3                Diferencias | Judicial | 81476 | 35 | 100,0 % | 2327,9x |
| 212 | 2.3               Reflexiones breves respecto a la RPPJy el | Penal | 119528 | 54 | 100,0 % | 2213,5x |
| 213 | 2.3             El error | Civil | 142015 | 40 | 100,0 % | 3550,4x |
| 214 | 2.3           El derecho a la protección | Constitucional | 121906 | 46 | 100,0 % | 2650,1x |
| 215 | 2.3     Los medios | Familia | 100107 | 50 | 100,0 % | 2002,1x |
| 216 | 2.3     Plan anual | Procesal | 94881 | 36 | 100,0 % | 2635,6x |
| 217 | 2.3.2 Culpabilidad                                                                                        113 | Penal | 119528 | 57 | 100,0 % | 2097,0x |
| 218 | 2.4                 Ley N° 20.609 que establece medidas | Judicial | 81476 | 39 | 100,0 % | 2089,1x |
| 219 | 2.4           Posible conexión entre el derecho a | Constitucional | 121906 | 54 | 100,0 % | 2257,5x |
| 220 | 2.5     Material complementario | Constitucional | 121906 | 42 | 100,0 % | 2902,5x |
| 221 | 2.5 Se considerará la posibilidad de ocuparse de los delincuentes en | Penal | 194788 | 72 | 100,0 % | 2705,4x |
| 222 | 2.6                Cambios en el ámbito de los derechos a partir de la | Judicial | 96536 | 48 | 100,0 % | 2011,2x |
| 223 | 2.7     El procedimiento de habeas data | Judicial | 96536 | 44 | 100,0 % | 2194,0x |
| 224 | 2.7 La utilización de medidas no privativas de la libertad será parte de | Penal | 194788 | 83 | 100,0 % | 2346,8x |
| 225 | 2.8                Reglamentación interna de la consulta | Judicial | 134465 | 59 | 100,0 % | 2279,1x |
| 226 | 2.9     La acción de protección del derecho | Judicial | 96536 | 42 | 100,0 % | 2298,5x |
| 227 | 20 Para más información, véase Schindler (1979: 10): «Eso se ve, por ejemplo, en el | Constitucional | 177323 | 54 | 100,0 % | 3283,8x |
| 228 | 20 Patricio Orellana, «Corrupción y probidad: Problema y soluciones», Probidad | Penal | 178516 | 45 | 100,0 % | 3967,0x |
| 229 | 20 Sentencia de la Corte de Apelaciones de Concepción, rol 13.060-2002, 7 de | Penal | 178516 | 50 | 100,0 % | 3570,3x |
| 230 | 20. Entregar copia del plan de emergencia y de los planos respectivos a la unidad de | Civil | 192585 | 79 | 100,0 % | 2437,8x |
| 231 | 200 CPP y del Art. 13 Ley Nº 20.000; b) la rotura de sellos puestos sobre efectos o | General | 313985 | 154 | 100,0 % | 2038,9x |
| 232 | 202               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 57 | 100,0 % | 5508,5x |
| 233 | 2022-a-1842 | Penal | 119528 | 35 | 100,0 % | 3415,1x |
| 234 | 2022-a-1846 | Judicial | 93914 | 36 | 100,0 % | 2608,7x |
| 235 | 204                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 130 | 100,0 % | 2415,3x |
| 236 | 21 Antes, en el mismo sentido, Sentencia Tribunal Constitucional rol 2744, de 8 | Judicial | 144656 | 66 | 100,0 % | 2191,8x |
| 237 | 21 Sentencia Tribunal Constitucional 2658, considerando decimoquinto. En el | Judicial | 144656 | 58 | 100,0 % | 2494,1x |
| 238 | 210               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 110 | 100,0 % | 2854,4x |
| 239 | 214               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 55 | 100,0 % | 5708,8x |
| 240 | 22                                                              Índice | General | 313985 | 29 | 100,0 % | 10827,1x |
| 241 | 22            Ver si hay normas que rebajan la penalidad (por ejemplo, artículos 142 bis y 456 | Penal | 194788 | 85 | 100,0 % | 2291,6x |
| 242 | 220               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 62 | 100,0 % | 5064,3x |
| 243 | 222               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 67 | 100,0 % | 4686,3x |
| 244 | 224 Nº1 y 225 Nº1), sí podrían ser responsables eventualmente de prevari- | General | 313985 | 59 | 100,0 % | 5321,8x |
| 245 | 228               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 67 | 100,0 % | 4686,3x |
| 246 | 23 Delitos contemplados en los números 8 y 9 del mismo artículo respecto de los | Penal | 178516 | 68 | 100,0 % | 2625,2x |
| 247 | 23 Incluso, para establecer un criterio diferenciador con el derecho administrativo | Penal | 178516 | 80 | 100,0 % | 2231,4x |
| 248 | 23. Capacitar a funcionarios/as de Establecimientos Penitenciarios | Constitucional | 177323 | 67 | 100,0 % | 2646,6x |
| 249 | 230               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 128 | 100,0 % | 2453,0x |
| 250 | 232                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 78 | 100,0 % | 4025,4x |
| 251 | 234   Referencias | Familia | 123490 | 32 | 100,0 % | 3859,1x |
| 252 | 236                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 58 | 100,0 % | 5413,5x |
| 253 | 24 En el caso de Colombia se puede citar a Suárez Sánchez (2000). En el caso de | Penal | 178516 | 54 | 100,0 % | 3305,9x |
| 254 | 24 Sentencia de la Corte de Apelaciones de Santiago, 17 de diciembre de 2019, rol | Judicial | 150341 | 53 | 100,0 % | 2836,6x |
| 255 | 24. Cuando corresponda, confeccionar un reglamento interno de Orden, Higiene y | Civil | 192585 | 87 | 100,0 % | 2213,6x |
| 256 | 242                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 71 | 100,0 % | 4422,3x |
| 257 | 244               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 71 | 100,0 % | 4422,3x |
| 258 | 246                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 70 | 100,0 % | 4485,5x |
| 259 | 25 Cabe advertir que incluso bajo el reconocimiento de estos delitos como figuras | Penal | 178516 | 59 | 100,0 % | 3025,7x |
| 260 | 25 Para más detalle, véase Diez de Velasco (2007: 700 y 701) sobre los mecanismos | Constitucional | 177323 | 63 | 100,0 % | 2814,7x |
| 261 | 25. Educación en derechos humanos para funcionarios/as públicos | Constitucional | 177323 | 72 | 100,0 % | 2462,8x |
| 262 | 256               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 87 | 100,0 % | 3609,0x |
| 263 | 258                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 70 | 100,0 % | 4485,5x |
| 264 | 26                             Abreviaturas | General | 313985 | 35 | 100,0 % | 8971,0x |
| 265 | 26 Agrega también: «un hombre [sic] razonable nunca se declarará convencido de | Judicial | 150341 | 66 | 100,0 % | 2277,9x |
| 266 | 26 Este fallo marcó un precedente dentro de la escasa jurisprudencia de la Ley | Penal | 178516 | 80 | 100,0 % | 2231,4x |
| 267 | 26 Juzgados | Procesal | 94881 | 37 | 100,0 % | 2564,4x |
| 268 | 26. Educación en derechos humanos a funcionarios/as del Consejo | Constitucional | 177323 | 88 | 100,0 % | 2015,0x |
| 269 | 262               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 61 | 100,0 % | 5147,3x |
| 270 | 264               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 66 | 100,0 % | 4757,3x |
| 271 | 268               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 45 | 100,0 % | 6977,4x |
| 272 | 268 sexies) | General | 313985 | 97 | 100,0 % | 3237,0x |
| 273 | 27                Presidio, reclusión y relegación      Inhabilitación absoluta perpetua para | Penal | 194788 | 87 | 100,0 % | 2238,9x |
| 274 | 27 Sentencias de la Corte Suprema 23.930-2014 y 25.003-2014; 25-02-2022, rol | Judicial | 150341 | 52 | 100,0 % | 2891,2x |
| 275 | 270               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 59 | 100,0 % | 5321,8x |
| 276 | 272                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 57 | 100,0 % | 5508,5x |
| 277 | 274               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 93 | 100,0 % | 3376,2x |
| 278 | 276                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 57 | 100,0 % | 5508,5x |
| 279 | 277      Sentencia de 2 de junio de 2016, 8° Juzgado de Garantía de Santiago. Causa RUC 1200084351-0, RIT Nº | Constitucional | 112823 | 54 | 100,0 % | 2089,3x |
| 280 | 278               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 58 | 100,0 % | 5413,5x |
| 281 | 28                                  Introducción | General | 313985 | 44 | 100,0 % | 7136,0x |
| 282 | 280               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 148 | 100,0 % | 2121,5x |
| 283 | 284               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 118 | 100,0 % | 2660,9x |
| 284 | 284 CJM, que castiga con pena corporal al que “ofendiere o injuriare de palabra | General | 313985 | 70 | 100,0 % | 4485,5x |
| 285 | 288               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 50 | 100,0 % | 6279,7x |
| 286 | 29 La jurisprudencia ha precisado al respecto: «En ese contexto, el hecho que la | Familia | 123490 | 57 | 100,0 % | 2166,5x |
| 287 | 29 Según los autores, en los países donde hay más corrupción el lucro doméstico | Penal | 178516 | 74 | 100,0 % | 2412,4x |
| 288 | 29. Capacitaciones del Observatorio de participación ciudadana y no | Constitucional | 177323 | 75 | 100,0 % | 2364,3x |
| 289 | 290               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 93 | 100,0 % | 3376,2x |
| 290 | 294               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 55 | 100,0 % | 5708,8x |
| 291 | 296                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 59 | 100,0 % | 5321,8x |
| 292 | 3 Acuerdos de Subsidios con organizaciones de la sociedad civil | Constitucional | 177323 | 52 | 100,0 % | 3410,1x |
| 293 | 3 Así sucedió en el caso Penta, en el cual el entonces fiscal nacional Sabas Chahuán | Penal | 178516 | 71 | 100,0 % | 2514,3x |
| 294 | 3 Reglas mínimas de las Naciones Unidas sobre las medidas no privativas de la | Penal | 194788 | 70 | 100,0 % | 2782,7x |
| 295 | 3 Un interesante relato sobre la forma de enfrentar el fenómeno de la corrupción | Penal | 178516 | 85 | 100,0 % | 2100,2x |
| 296 | 3. A los compromisarios, peritos y otras personas que, ejerciendo atri- | Penal | 178516 | 72 | 100,0 % | 2479,4x |
| 297 | 3. Considerar las distintas opciones o alternativas programáticas de | Constitucional | 177323 | 78 | 100,0 % | 2273,4x |
| 298 | 3. Efectuar los actos necesarios para realizar la certificación de las instalaciones de gas 65 y | Civil | 192585 | 76 | 100,0 % | 2534,0x |
| 299 | 3. El régimen penitenciario consistirá en un tratamiento cuya finalidad | Penal | 194788 | 87 | 100,0 % | 2238,9x |
| 300 | 3. Impulsar mesas de trabajos colaborativas o interinstitucionales | Constitucional | 177323 | 78 | 100,0 % | 2273,4x |
| 301 | 3. La expresión sucinta del porqué esos hechos se encuentran | Penal | 211066 | 88 | 100,0 % | 2398,5x |
| 302 | 3. La no discriminación arbitraria en el trato que deben dar el Estado y | Constitucional | 177323 | 59 | 100,0 % | 3005,5x |
| 303 | 3. Las asambleas extraordinarias para tratar modificaciones al reglamento de | Civil | 192585 | 57 | 100,0 % | 3378,7x |
| 304 | 3. Los Estados parte se asegurarán de que las instituciones, servicios | Constitucional | 177323 | 52 | 100,0 % | 3410,1x |
| 305 | 3. Normas reglamentarias | Civil | 192585 | 53 | 100,0 % | 3633,7x |
| 306 | 3. Se considerará que un recurso presenta interés casacional cuando la sentencia | General | 129559 | 62 | 100,0 % | 2089,7x |
| 307 | 3.1            Suspensión del | Laboral | 100583 | 48 | 100,0 % | 2095,5x |
| 308 | 3.1           El Poder Judicial ante el derecho | Constitucional | 112823 | 46 | 100,0 % | 2452,7x |
| 309 | 3.1         La realidad de las personas | Judicial | 93914 | 41 | 100,0 % | 2290,6x |
| 310 | 3.1     Los problemas de la falta de tipificación y | Judicial | 96536 | 44 | 100,0 % | 2194,0x |
| 311 | 3.1.2 Recepción de las normas internacionales | Penal | 121924 | 58 | 100,0 % | 2102,1x |
| 312 | 3.2              Directrices | Judicial | 96536 | 29 | 100,0 % | 3328,8x |
| 313 | 3.2           Derechos constitucionales | Laboral | 113458 | 45 | 100,0 % | 2521,3x |
| 314 | 3.2       Responsabilidad civil de la figura médica por la | Civil | 142015 | 50 | 100,0 % | 2840,3x |
| 315 | 3.2     Igualdad y no | Judicial | 89476 | 35 | 100,0 % | 2556,5x |
| 316 | 3.2     Procedimiento regulado en | Judicial | 81476 | 36 | 100,0 % | 2263,2x |
| 317 | 3.2.3 Derecho de defensa | Penal | 211066 | 53 | 100,0 % | 3982,4x |
| 318 | 3.2.4 Derecho a la presunción de inocencia | Penal | 211066 | 97 | 100,0 % | 2175,9x |
| 319 | 3.2.5 Inadmisibilidad de la persecución penal múltiple | Penal | 211066 | 61 | 100,0 % | 3460,1x |
| 320 | 3.3             El bien jurídico protegido y las características | Judicial | 96536 | 44 | 100,0 % | 2194,0x |
| 321 | 3.3     Violencia intrafamiliar | Familia | 95131 | 41 | 100,0 % | 2320,3x |
| 322 | 3.3.2 Derecho a juicio oral | Penal | 211066 | 68 | 100,0 % | 3103,9x |
| 323 | 3.4     Contenido de la | Judicial | 93914 | 39 | 100,0 % | 2408,1x |
| 324 | 3.4 Comisiones precalificadoras                                                        144 | Procesal | 101194 | 40 | 100,0 % | 2529,8x |
| 325 | 3.4.2 Principios relativos al derecho | Judicial | 93914 | 42 | 100,0 % | 2236,0x |
| 326 | 3.4.3 Garantías asociadas al derecho | Judicial | 93914 | 42 | 100,0 % | 2236,0x |
| 327 | 3.4.5 Procedimientos de solicitud de | Judicial | 93914 | 45 | 100,0 % | 2087,0x |
| 328 | 3.5     Material complementario | Constitucional | 121906 | 42 | 100,0 % | 2902,5x |
| 329 | 3.5 Las decisiones sobre la imposición de medidas no privativas de la | Penal | 194788 | 72 | 100,0 % | 2705,4x |
| 330 | 3.6     Ponderación y prueba | Laboral | 113458 | 48 | 100,0 % | 2363,7x |
| 331 | 3.7               Protección ambiental de las tierras | Judicial | 134465 | 58 | 100,0 % | 2318,4x |
| 332 | 3.7           Sentencia definitiva y los | Laboral | 113458 | 52 | 100,0 % | 2181,9x |
| 333 | 3.8           El singular problema de la llamada | Judicial | 96536 | 37 | 100,0 % | 2609,1x |
| 334 | 3.8.2 Estatus de las Áreas de Desarrollo Indígena | Judicial | 134465 | 63 | 100,0 % | 2134,4x |
| 335 | 3.8.3   Constitución de servidumbres mineras sobre tierras indígenas. Relación con las | Judicial | 134465 | 54 | 100,0 % | 2490,1x |
| 336 | 3.9           A diez años del procedimiento | Laboral | 113458 | 50 | 100,0 % | 2269,2x |
| 337 | 300               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 53 | 100,0 % | 5924,2x |
| 338 | 302               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 66 | 100,0 % | 4757,3x |
| 339 | 308               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 70 | 100,0 % | 4485,5x |
| 340 | 31 Corte Constitucional de Colombia, acción de tutela incoada por el defensor del | Constitucional | 177323 | 66 | 100,0 % | 2686,7x |
| 341 | 31. MERA, Jorge (2002): “Discrecionalidad del Ministerio Público, calificación | Penal | 211066 | 78 | 100,0 % | 2706,0x |
| 342 | 316                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 57 | 100,0 % | 5508,5x |
| 343 | 32                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 91 | 100,0 % | 3450,4x |
| 344 | 32 En el caso de Alemania no existe responsabilidad penal de las personas, sino | Penal | 178516 | 87 | 100,0 % | 2051,9x |
| 345 | 32 Sentencia de la Corte de Apelaciones de Santiago, rol 2.735-2010, 24 de enero | Penal | 178516 | 45 | 100,0 % | 3967,0x |
| 346 | 322               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 58 | 100,0 % | 5413,5x |
| 347 | 324               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 52 | 100,0 % | 6038,2x |
| 348 | 326               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 101 | 100,0 % | 3108,8x |
| 349 | 328               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 61 | 100,0 % | 5147,3x |
| 350 | 33 Subsecretaría de Derechos Humanos, «Segundo Plan Nacional de Derechos | Constitucional | 177323 | 66 | 100,0 % | 2686,7x |
| 351 | 33. MIRANDA Manuel, CERDA Rodrigo y HERMOSILLA Francisco (2012): La | Penal | 211066 | 91 | 100,0 % | 2319,4x |
| 352 | 330                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 58 | 100,0 % | 5413,5x |
| 353 | 332               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 72 | 100,0 % | 4360,9x |
| 354 | 334   RÍOS y SILVA (2014), p. 267 | Civil | 142015 | 63 | 100,0 % | 2254,2x |
| 355 | 336               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 119 | 100,0 % | 2638,5x |
| 356 | 34                 Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 75 | 100,0 % | 4186,5x |
| 357 | 34 Sentencia de la Corte de Apelaciones de Santiago, 726-2010, 21 de junio de | Penal | 178516 | 44 | 100,0 % | 4057,2x |
| 358 | 340                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 76 | 100,0 % | 4131,4x |
| 359 | 342               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 53 | 100,0 % | 5924,2x |
| 360 | 347 a 352) | General | 313985 | 46 | 100,0 % | 6825,8x |
| 361 | 348               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 66 | 100,0 % | 4757,3x |
| 362 | 35 Documento creado colaborativamente por la Secretaría Técnica de Igualdad de | Constitucional | 177323 | 63 | 100,0 % | 2814,7x |
| 363 | 35 En sentencia Corte Suprema rol 5554-2011, de 6 de junio de 2013, se explica que | Judicial | 144656 | 71 | 100,0 % | 2037,4x |
| 364 | 35 Informe Nacional, presentado de conformidad con el párrafo 32, destaca que | Constitucional | 177323 | 65 | 100,0 % | 2728,0x |
| 365 | 350 Corte Suprema, 11 de mayo de 2017, Rol Nº 47936-2016. En igual sentido, véase Corte Suprema, 26 de di- | Civil | 142015 | 68 | 100,0 % | 2088,5x |
| 366 | 351 CPP, a menos de ser más favorables para el condenado las reglas del concurso | General | 313985 | 117 | 100,0 % | 2683,6x |
| 367 | 352                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 61 | 100,0 % | 5147,3x |
| 368 | 36 Como se decidió en sentencia Corte Suprema rol 31272-2018, de 29 de agosto | Judicial | 144656 | 68 | 100,0 % | 2127,3x |
| 369 | 36 Sentencia de la Corte de Apelaciones de Santiago, 16 de octubre de 2020, rol | Judicial | 150341 | 53 | 100,0 % | 2836,6x |
| 370 | 360                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 58 | 100,0 % | 5413,5x |
| 371 | 362               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 53 | 100,0 % | 5924,2x |
| 372 | 367 bis y al delito del art. 374 | General | 313985 | 48 | 100,0 % | 6541,4x |
| 373 | 368                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 49 | 100,0 % | 6407,9x |
| 374 | 374               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 58 | 100,0 % | 5413,5x |
| 375 | 38 Sentencia de la Corte de Apelaciones de Antofagasta, rol 47-2006, 21 de abril | Penal | 178516 | 54 | 100,0 % | 3305,9x |
| 376 | 38. Apoyar y fortalecer las capacidades técnicas de funcionarios/as | Constitucional | 177323 | 79 | 100,0 % | 2244,6x |
| 377 | 382               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 117 | 100,0 % | 2683,6x |
| 378 | 387   Referencias | Penal | 194788 | 41 | 100,0 % | 4750,9x |
| 379 | 387. Primero, contiene las disposiciones generales sobre ellos, luego | Penal | 211066 | 88 | 100,0 % | 2398,5x |
| 380 | 39 Sentencia Tribunal Constitucional de 17 de enero de 2023, rol ingreso número | Judicial | 144656 | 66 | 100,0 % | 2191,8x |
| 381 | 39 Sentencia del caso Educer, Tribunal de Juicio Oral en lo Penal de Talca, RIT | Penal | 178516 | 63 | 100,0 % | 2833,6x |
| 382 | 390               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 85 | 100,0 % | 3693,9x |
| 383 | 392                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 55 | 100,0 % | 5708,8x |
| 384 | 4 Juzgados | Procesal | 94881 | 39 | 100,0 % | 2432,8x |
| 385 | 4 Reglas de las Naciones Unidas para el tratamiento de las reclusas y medidas no | Penal | 194788 | 76 | 100,0 % | 2563,0x |
| 386 | 4 Sentencia de la Corte de Apelaciones de Santiago, rol 13.268-2006, 16 de agosto | Penal | 178516 | 79 | 100,0 % | 2259,7x |
| 387 | 4.    ALEXY, Robert (1986): Teoría de los derechos fundamentales, Madrid, Centro | Constitucional | 121906 | 55 | 100,0 % | 2216,5x |
| 388 | 4. Considerar la posibilidad de brindar un ajuste razonable en caso | Constitucional | 177323 | 79 | 100,0 % | 2244,6x |
| 389 | 4. Diagnóstico | Penal | 211066 | 67 | 100,0 % | 3150,2x |
| 390 | 4. Ejecutarlo en el contexto de violencia física o psicológica habitual del | Penal | 194788 | 87 | 100,0 % | 2238,9x |
| 391 | 4. El administrador deberá presentar el acta (original o fotocopia simple) de su | Civil | 192585 | 88 | 100,0 % | 2188,5x |
| 392 | 4. El componen te indígena | Judicial | 134465 | 58 | 100,0 % | 2318,4x |
| 393 | 4. La prestación de tales servicios de salud deberá coordinarse | Judicial | 134465 | 65 | 100,0 % | 2068,7x |
| 394 | 4. Programa de núcleo básico de derechos humanos para las Fuerzas | Constitucional | 177323 | 87 | 100,0 % | 2038,2x |
| 395 | 4.1         Política de Igualdad de Género y No | Judicial | 93914 | 46 | 100,0 % | 2041,6x |
| 396 | 4.1     El Convenio 169 y la reinterpretación de los | Judicial | 134465 | 59 | 100,0 % | 2279,1x |
| 397 | 4.10     El repositorio documental del notario considerando | Judicial | 96536 | 44 | 100,0 % | 2194,0x |
| 398 | 4.2               Principio general | Constitucional | 104063 | 40 | 100,0 % | 2601,6x |
| 399 | 4.2           Comité de | Familia | 100107 | 44 | 100,0 % | 2275,2x |
| 400 | 4.2        Derechos sexuales y reproductivos en las personas | Judicial | 89476 | 42 | 100,0 % | 2130,4x |
| 401 | 4.2     Conceptos generales: documento | Judicial | 96536 | 42 | 100,0 % | 2298,5x |
| 402 | 4.3                   Principio de transparencia | Constitucional | 104063 | 49 | 100,0 % | 2123,7x |
| 403 | 4.3           Derechos sexuales y reproductivos en | Judicial | 89476 | 42 | 100,0 % | 2130,4x |
| 404 | 4.3     Principios jurídicos de la | Judicial | 96536 | 45 | 100,0 % | 2145,2x |
| 405 | 4.3.1 Legislación | Constitucional | 121906 | 52 | 100,0 % | 2344,3x |
| 406 | 4.4             Principio | Constitucional | 104063 | 45 | 100,0 % | 2312,5x |
| 407 | 4.4            Análisis del panorama de textos | Constitucional | 121906 | 54 | 100,0 % | 2257,5x |
| 408 | 4.4          Consejo | Familia | 100107 | 42 | 100,0 % | 2383,5x |
| 409 | 4.4     Reconocimiento de identidad de género para | Judicial | 93914 | 46 | 100,0 % | 2041,6x |
| 410 | 4.4.2   La comunidad sancionadora: el deber del juez de considerar las instituciones | Judicial | 134465 | 61 | 100,0 % | 2204,3x |
| 411 | 4.4.2 Regulación en Chile | Constitucional | 112823 | 54 | 100,0 % | 2089,3x |
| 412 | 4.6   La discapacidad | Constitucional | 121906 | 42 | 100,0 % | 2902,5x |
| 413 | 4.6.2 Dos cuestiones previas: ni lucro | Civil | 142015 | 59 | 100,0 % | 2407,0x |
| 414 | 4.6.5 Conclusiones | Civil | 142015 | 70 | 100,0 % | 2028,8x |
| 415 | 4.7     Material complementario | Constitucional | 121906 | 42 | 100,0 % | 2902,5x |
| 416 | 4.7     Responsabilidad de los prestadores | Judicial | 96536 | 42 | 100,0 % | 2298,5x |
| 417 | 4.8.3   Fiscalización                                                                                      166 | Judicial | 96536 | 48 | 100,0 % | 2011,2x |
| 418 | 40 Parte de estas propuestas se incluyen en un proyecto de ley que actualmente | Penal | 178516 | 62 | 100,0 % | 2879,3x |
| 419 | 40. ROMERO, Alejandro (2017): “Comentario sobre el derecho al juez natural en | Penal | 211066 | 93 | 100,0 % | 2269,5x |
| 420 | 402               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 53 | 100,0 % | 5924,2x |
| 421 | 408               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 65 | 100,0 % | 4830,5x |
| 422 | 41 Adoptadas en la XIV Cumbre Judicial Iberoamericana celebrada en Brasilia | Constitucional | 177323 | 57 | 100,0 % | 3110,9x |
| 423 | 41 El amparo constitucional a nivel latinoamericano es homologable a nuestra | Judicial | 144656 | 70 | 100,0 % | 2066,5x |
| 424 | 41 Sentencia de la Corte de Apelaciones de Valparaíso, 17 de febrero de 2022, rol | Judicial | 150341 | 55 | 100,0 % | 2733,5x |
| 425 | 412               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 52 | 100,0 % | 6038,2x |
| 426 | 416               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 79 | 100,0 % | 3974,5x |
| 427 | 42                 Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 55 | 100,0 % | 5708,8x |
| 428 | 42 Para más información, véase Poder Judicial (2015-2020: 79): «Negación del | Constitucional | 177323 | 85 | 100,0 % | 2086,2x |
| 429 | 42 Sentencia de la Corte de Apelaciones de Santiago, 28 de diciembre de 2012, rol | Judicial | 150341 | 53 | 100,0 % | 2836,6x |
| 430 | 424               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 63 | 100,0 % | 4983,9x |
| 431 | 436                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 48 | 100,0 % | 6541,4x |
| 432 | 44                 Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 54 | 100,0 % | 5814,5x |
| 433 | 44 Defensoría de la Niñez, «Datos clave y estadísticas de la niñez y adolescencia | Constitucional | 177323 | 54 | 100,0 % | 3283,8x |
| 434 | 44 Ley Nº 19.974, de 2.10.2004); la del contenido de las solicitudes realizadas | General | 313985 | 97 | 100,0 % | 3237,0x |
| 435 | 44 Para mayores antecedentes sobre la prueba ilícita en sede penal en Chile véase | Judicial | 150341 | 61 | 100,0 % | 2464,6x |
| 436 | 44 Sentencia de la Corte de Apelaciones de Santiago, 24 de febrero de 2020, rol | Judicial | 150341 | 53 | 100,0 % | 2836,6x |
| 437 | 440               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 52 | 100,0 % | 6038,2x |
| 438 | 442               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 87 | 100,0 % | 3609,0x |
| 439 | 444               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 133 | 100,0 % | 2360,8x |
| 440 | 446                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 68 | 100,0 % | 4617,4x |
| 441 | 448               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 101 | 100,0 % | 3108,8x |
| 442 | 45 Esto se materializó inmediatamente, toda vez que, al publicarse la Ley 20.977 | Penal | 178516 | 81 | 100,0 % | 2203,9x |
| 443 | 45 Sentencia de la Corte de Apelaciones de Santiago, 21 de diciembre de 2021, rol | Judicial | 150341 | 63 | 100,0 % | 2386,4x |
| 444 | 45 Tribunales | Procesal | 94881 | 36 | 100,0 % | 2635,6x |
| 445 | 450               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 88 | 100,0 % | 3568,0x |
| 446 | 454   AGÜERO y ZAMBRANO (2009), p. 34 | Constitucional | 121906 | 53 | 100,0 % | 2300,1x |
| 447 | 458               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 53 | 100,0 % | 5924,2x |
| 448 | 46 Los dos fallos anteriores a que se refiere corresponden a los casos Pehuenche | Penal | 178516 | 45 | 100,0 % | 3967,0x |
| 449 | 46 Sentencia de la Corte de Apelaciones de Santiago, 14 de diciembre de 2021, rol | Judicial | 150341 | 58 | 100,0 % | 2592,1x |
| 450 | 46. SCHÜNEMANN Bernard: “¿Crisis del procedimiento penal? (¿Marcha | Penal | 211066 | 75 | 100,0 % | 2814,2x |
| 451 | 460                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 118 | 100,0 % | 2660,9x |
| 452 | 47 Como veremos más adelante, a propósito de las estrategias normativas, en la | Penal | 178516 | 49 | 100,0 % | 3643,2x |
| 453 | 47 Sentencia del Tribunal de Juicio Oral en lo Pena de Concepción, 04 de mayo | Judicial | 150341 | 57 | 100,0 % | 2637,6x |
| 454 | 470               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 44 | 100,0 % | 7136,0x |
| 455 | 470 n° 9) | General | 313985 | 44 | 100,0 % | 7136,0x |
| 456 | 472               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 72 | 100,0 % | 4360,9x |
| 457 | 474               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 57 | 100,0 % | 5508,5x |
| 458 | 476 N° 3) o se provoque un incendio que afectare gravemente las condiciones | General | 313985 | 61 | 100,0 % | 5147,3x |
| 459 | 48 Sentencia de la Corte de Apelaciones de Santiago, 13 de agosto de 2021, rol | Judicial | 150341 | 58 | 100,0 % | 2592,1x |
| 460 | 48. UNIVERSIDAD DIEGO PORTALES (2007): “La responsabilidad juvenil y los | Penal | 211066 | 65 | 100,0 % | 3247,2x |
| 461 | 480                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 70 | 100,0 % | 4485,5x |
| 462 | 484. Además, fuera del Código penal el Art. 23 ter de la Ley de Bosques castiga | General | 313985 | 62 | 100,0 % | 5064,3x |
| 463 | 488               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 71 | 100,0 % | 4422,3x |
| 464 | 49 Por ejemplo, se destaca el hecho de que desde 2020 se coordina el trabajo | Penal | 178516 | 67 | 100,0 % | 2664,4x |
| 465 | 490               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 62 | 100,0 % | 5064,3x |
| 466 | 496                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 92 | 100,0 % | 3412,9x |
| 467 | 498                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 58 | 100,0 % | 5413,5x |
| 468 | 5 Deberá indemnizarse plenamente a las personas | Judicial | 134465 | 66 | 100,0 % | 2037,3x |
| 469 | 5 En la Ley 21.527 esta sanción se reemplaza por la de libertad asistida especial con | Penal | 194788 | 76 | 100,0 % | 2563,0x |
| 470 | 5 Promulgada por el Decreto 162 del Ministerio de Relaciones Exteriores de 1 de | Judicial | 144656 | 68 | 100,0 % | 2127,3x |
| 471 | 5 Sentencia de la Corte Suprema, rol 2.321-2007, 19 de mayo de 2008 (el destacado | Penal | 178516 | 59 | 100,0 % | 3025,7x |
| 472 | 5 Sentencia de la Corte Suprema, rol 496-2011, 4 de diciembre de 2012; y sentencia | Penal | 178516 | 67 | 100,0 % | 2664,4x |
| 473 | 5. Deberá indemnizarse plenamente a las personas trasladadas y | Judicial | 134465 | 66 | 100,0 % | 2037,3x |
| 474 | 5. El proceso penal debe ser público, salvo en lo que sea necesario para | Constitucional | 177323 | 55 | 100,0 % | 3224,1x |
| 475 | 5. Fortalecimiento del Comité Espejo, asesor del Punto Nacional de | Constitucional | 177323 | 65 | 100,0 % | 2728,0x |
| 476 | 5. La enunciación del voto de minoría de alguno de los jueces de | Penal | 211066 | 97 | 100,0 % | 2175,9x |
| 477 | 5. La extinción de la responsabilidad penal | Penal | 211066 | 96 | 100,0 % | 2198,6x |
| 478 | 5. Que, los requisitos legales del caso son, entre otros, los contemplados | Penal | 194788 | 88 | 100,0 % | 2213,5x |
| 479 | 5. Sistematización, comunicación | Judicial | 134465 | 61 | 100,0 % | 2204,3x |
| 480 | 5.1              Jueces de | Penal | 211066 | 74 | 100,0 % | 2852,2x |
| 481 | 5.1           Ideas | Civil | 142015 | 39 | 100,0 % | 3641,4x |
| 482 | 5.2                Tribunal de juicio oral | Penal | 211066 | 55 | 100,0 % | 3837,6x |
| 483 | 5.2         Presupuesto para el ejercicio de la acción | Civil | 142015 | 57 | 100,0 % | 2491,5x |
| 484 | 5.2     Protección de datos | Constitucional | 104063 | 37 | 100,0 % | 2812,5x |
| 485 | 5.2 Presupuesto para el ejercicio de la acción indemnizatoria de daños en contra de un | Civil | 142015 | 63 | 100,0 % | 2254,2x |
| 486 | 5.3          Análisis de caso de falta de | Penal | 211066 | 74 | 100,0 % | 2852,2x |
| 487 | 5.3     Ley | Procesal | 94881 | 35 | 100,0 % | 2710,9x |
| 488 | 5.3     Procedimiento | Procesal | 101194 | 39 | 100,0 % | 2594,7x |
| 489 | 5.3.3   La tutela jurisdiccional en los procedimientos de evaluación ambiental: el acceso | Judicial | 134465 | 59 | 100,0 % | 2279,1x |
| 490 | 5.4         Régimen | Civil | 142015 | 42 | 100,0 % | 3381,3x |
| 491 | 5.5               Enfoque de riesgos y gestión de | Constitucional | 104063 | 49 | 100,0 % | 2123,7x |
| 492 | 5.5     Audiencia de | Familia | 100107 | 45 | 100,0 % | 2224,6x |
| 493 | 5.6           Las infecciones | Civil | 142015 | 61 | 100,0 % | 2328,1x |
| 494 | 5.6 Las infecciones intrahospitalarias                                                    266 | Civil | 142015 | 65 | 100,0 % | 2184,8x |
| 495 | 5.7.2   Educación                                                                                          285 | Judicial | 134465 | 44 | 100,0 % | 3056,0x |
| 496 | 50 Sentencia de la Corte Suprema, rol 2.924-2008, 15 de julio de 2009; sentencia | Penal | 178516 | 72 | 100,0 % | 2479,4x |
| 497 | 50 Sentencia de la Corte de Apelaciones de San Miguel, 15 de febrero de 2022, rol | Judicial | 150341 | 57 | 100,0 % | 2637,6x |
| 498 | 500               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 52 | 100,0 % | 6038,2x |
| 499 | 502                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 79 | 100,0 % | 3974,5x |
| 500 | 504                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 48 | 100,0 % | 6541,4x |
| 501 | 506                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 50 | 100,0 % | 6279,7x |
| 502 | 508                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 80 | 100,0 % | 3924,8x |
| 503 | 51 Para más información, véase Declaración Universal de los Derechos Humanos | Constitucional | 177323 | 62 | 100,0 % | 2860,0x |
| 504 | 510                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 59 | 100,0 % | 5321,8x |
| 505 | 512               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 75 | 100,0 % | 4186,5x |
| 506 | 514               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 53 | 100,0 % | 5924,2x |
| 507 | 516                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 94 | 100,0 % | 3340,3x |
| 508 | 518                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 74 | 100,0 % | 4243,0x |
| 509 | 52 Especial atención requiere, en este contexto, el Manual de actuaciones mínimas | Constitucional | 177323 | 63 | 100,0 % | 2814,7x |
| 510 | 52 Supreme Court, Daubert versus Merrel Dow Pharmaceuticals (92-102), 509 | Judicial | 150341 | 50 | 100,0 % | 3006,8x |
| 511 | 520                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 46 | 100,0 % | 6825,8x |
| 512 | 524                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 63 | 100,0 % | 4983,9x |
| 513 | 53 Luego, es esencial incorporar una perspectiva de género que otorgue especial | Constitucional | 177323 | 67 | 100,0 % | 2646,6x |
| 514 | 53 Sentencia del Tribunal de Juicio Oral en lo Penal de Arica, 11 de octubre de | Judicial | 150341 | 59 | 100,0 % | 2548,2x |
| 515 | 534               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 70 | 100,0 % | 4485,5x |
| 516 | 54                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 67 | 100,0 % | 4686,3x |
| 517 | 54 En lo que aparece de manera transversal a lo largo del informe, pero aquí re- | Penal | 178516 | 71 | 100,0 % | 2514,3x |
| 518 | 54 Se ha señalado que esta graduación de la pena privativa de libertad, al igual | Penal | 178516 | 74 | 100,0 % | 2412,4x |
| 519 | 54 Un desarrollo más extenso y pormenorizado puede verse en Vázquez, 2015: 91 | Judicial | 150341 | 52 | 100,0 % | 2891,2x |
| 520 | 55 Los propios actores del sistema, como jueces y fiscales, han reconocido que | Penal | 178516 | 75 | 100,0 % | 2380,2x |
| 521 | 55 Para más información, véase Bill of Rights inglés de 1689, la Declaración de | Constitucional | 177323 | 76 | 100,0 % | 2333,2x |
| 522 | 56                 Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 85 | 100,0 % | 3693,9x |
| 523 | 56 Para más información, véase el Cuaderno de buenas prácticas para incorporar | Constitucional | 177323 | 70 | 100,0 % | 2533,2x |
| 524 | 58                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 146 | 100,0 % | 2150,6x |
| 525 | 59 Según el mismo autor: «que todos los hechos comprobados no bastan para | Judicial | 150341 | 72 | 100,0 % | 2088,1x |
| 526 | 6 DFL número 1/19.563, que fija texto refundido, coordinado y sistematizado de | Judicial | 144656 | 48 | 100,0 % | 3013,7x |
| 527 | 6 Matus y Ramírez señalan que, es «dominante la doctrina que estima necesario | Penal | 194788 | 97 | 100,0 % | 2008,1x |
| 528 | 6 Mismo criterio se sigue en sentencia Corte Suprema rol 60655-2021, de 7 de | Judicial | 144656 | 53 | 100,0 % | 2729,4x |
| 529 | 6 Promulgada por el Decreto 830 del Ministerio de Relaciones Exteriores de 14 | Judicial | 144656 | 68 | 100,0 % | 2127,3x |
| 530 | 6. Contrato plurilateral: se presenta esta variante de los contratos bilaterales, pues | Civil | 192585 | 96 | 100,0 % | 2006,1x |
| 531 | 6. Incorpora ampliamente la participación de la sociedad civil y el | Constitucional | 177323 | 67 | 100,0 % | 2646,6x |
| 532 | 6. La indicación de que la participación de el o los acusados, en | Penal | 211066 | 92 | 100,0 % | 2294,2x |
| 533 | 6. Las penas privativas de la libertad tendrán como finalidad esencial la | Penal | 194788 | 57 | 100,0 % | 3417,3x |
| 534 | 6. Ley N° 5.750 de 2 de diciembre de 1935, que permitió investigar la paternidad | Familia | 190697 | 93 | 100,0 % | 2050,5x |
| 535 | 6. Plan de Formación Ciudadana: Apoyo a la implementación (ID | Constitucional | 177323 | 84 | 100,0 % | 2111,0x |
| 536 | 6. Que conforme a lo anterior el derecho que se alega vulnerado no es | Penal | 194788 | 94 | 100,0 % | 2072,2x |
| 537 | 6. Velar por la observancia de las disposiciones legales y reglamentarias sobre | Civil | 192585 | 88 | 100,0 % | 2188,5x |
| 538 | 6.1               Reglas | Procesal | 94881 | 33 | 100,0 % | 2875,2x |
| 539 | 6.1              Derecho | Constitucional | 104063 | 52 | 100,0 % | 2001,2x |
| 540 | 6.1           Ministerio | Penal | 211066 | 70 | 100,0 % | 3015,2x |
| 541 | 6.1       Concepto de | Familia | 100107 | 37 | 100,0 % | 2705,6x |
| 542 | 6.1 En el procedimiento penal solo se recurrirá a la prisión preventiva | Penal | 194788 | 75 | 100,0 % | 2597,2x |
| 543 | 6.2           Derecho | Constitucional | 104063 | 33 | 100,0 % | 3153,4x |
| 544 | 6.2          Defensoría Penal | Penal | 211066 | 48 | 100,0 % | 4397,2x |
| 545 | 6.2     Secretaría Técnica de Igualdad de | Procesal | 94881 | 42 | 100,0 % | 2259,1x |
| 546 | 6.2     Sobre la regulación del | Judicial | 96536 | 35 | 100,0 % | 2758,2x |
| 547 | 6.3     Carabineros y Policía | Penal | 211066 | 72 | 100,0 % | 2931,5x |
| 548 | 6.3     El juez | Laboral | 100583 | 46 | 100,0 % | 2186,6x |
| 549 | 6.4            Formación del | Judicial | 96536 | 36 | 100,0 % | 2681,6x |
| 550 | 6.4     Derecho | Constitucional | 104063 | 33 | 100,0 % | 3153,4x |
| 551 | 6.4     Las unidades | Laboral | 100583 | 45 | 100,0 % | 2235,2x |
| 552 | 6.4     Procedimiento de | Procesal | 94881 | 35 | 100,0 % | 2710,9x |
| 553 | 6.4 Procedimiento de investigación                                                      260 | Procesal | 101194 | 39 | 100,0 % | 2594,7x |
| 554 | 6.4 Procedimiento de investigación                                     250 | Procesal | 94881 | 45 | 100,0 % | 2108,5x |
| 555 | 6.5                Cambios en el ámbito de los derechos a partir | Constitucional | 104063 | 50 | 100,0 % | 2081,3x |
| 556 | 6.5              Sename e instituciones | Penal | 211066 | 49 | 100,0 % | 4307,5x |
| 557 | 6.5     La ley de protección de derechos | Judicial | 96536 | 37 | 100,0 % | 2609,1x |
| 558 | 6.6              Aplicación del derecho de cancelacióna | Constitucional | 104063 | 42 | 100,0 % | 2477,7x |
| 559 | 6.6     Análisis de casos en que funcionarios | Penal | 211066 | 74 | 100,0 % | 2852,2x |
| 560 | 6.6     Nuevas formas de contratación | Judicial | 96536 | 41 | 100,0 % | 2354,5x |
| 561 | 6.6     Presupuesto, contabilidad | Laboral | 100583 | 50 | 100,0 % | 2011,7x |
| 562 | 6.7     Escalafón de empleados | Laboral | 100583 | 49 | 100,0 % | 2052,7x |
| 563 | 6.9            Definición | Laboral | 100583 | 46 | 100,0 % | 2186,6x |
| 564 | 60 Juzgados | Procesal | 94881 | 35 | 100,0 % | 2710,9x |
| 565 | 61 Para más información, véase CTMF, 1990, artículo 23; Observación General 2 | Constitucional | 177323 | 84 | 100,0 % | 2111,0x |
| 566 | 62 No hay que olvidar que en aquellos casos en que el SII ya había presentado una | Penal | 178516 | 87 | 100,0 % | 2051,9x |
| 567 | 63 Sentencia del Tribunal de Juicio Oral en lo Penal 13 de marzo de 2011, RIT | Judicial | 150341 | 74 | 100,0 % | 2031,6x |
| 568 | 64 Ministerio Público, «Boletín estadístico anual: Enero-diciembre 2021», 18 de | Penal | 178516 | 71 | 100,0 % | 2514,3x |
| 569 | 65 Convención sobre los derechos de las personas con discapacidad, disponible | Constitucional | 177323 | 87 | 100,0 % | 2038,2x |
| 570 | 67 Sentencia de la Corte de Apelaciones de Santiago, 21 de diciembre de 2021, rol | Judicial | 150341 | 55 | 100,0 % | 2733,5x |
| 571 | 68                 Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 66 | 100,0 % | 4757,3x |
| 572 | 68 En el caso de ciertas autoridades, se incluye la obligación de incluir el nombre | Penal | 178516 | 80 | 100,0 % | 2231,4x |
| 573 | 68 Sentencia de la Corte de Apelaciones de Valparaíso, 25 de marzo de 2011, rol | Familia | 123490 | 58 | 100,0 % | 2129,1x |
| 574 | 7 CPP, esto es, antes de la primera actuación del procedimiento dirigida en su | General | 313985 | 49 | 100,0 % | 6407,9x |
| 575 | 7 En este sentido, Maccormick (2007: 211). Sin embargo, debemos considerar que | Judicial | 150341 | 68 | 100,0 % | 2210,9x |
| 576 | 7 Sentencia de la Corte de Apelaciones de Santiago, 4 de enero de 2023, rol de | Judicial | 144656 | 70 | 100,0 % | 2066,5x |
| 577 | 7 También Ferrajoli (2014: 139): «Y ha terminado por transformarse en un tosco | Judicial | 150341 | 62 | 100,0 % | 2424,9x |
| 578 | 7 También sobre este principio, véase Horvitz y López (2002: 353 y 354) y en lo | Judicial | 144656 | 71 | 100,0 % | 2037,4x |
| 579 | 7. Asegurar que la persona mayor tenga acceso efectivo a la justicia en | Constitucional | 177323 | 83 | 100,0 % | 2136,4x |
| 580 | 7. Ayudar a que la persona con discapacidad visual comprenda mejor | Constitucional | 177323 | 85 | 100,0 % | 2086,2x |
| 581 | 7. Ley N° 7.612 de 21 de octubre de 1943, en virtud de la cual se permite alterar las | Familia | 190697 | 66 | 100,0 % | 2889,3x |
| 582 | 7. Permitir la presencia de alguna persona de su confianza que les | Constitucional | 177323 | 81 | 100,0 % | 2189,2x |
| 583 | 7. Que, es evidente que el derecho del imputado a la prescripción de | Penal | 194788 | 80 | 100,0 % | 2434,8x |
| 584 | 7.1            Autoridades | Constitucional | 104063 | 33 | 100,0 % | 3153,4x |
| 585 | 7.1          Rol de la | Penal | 211066 | 52 | 100,0 % | 4059,0x |
| 586 | 7.1 Cuando exista la posibilidad de preparar informes de investigación | Penal | 194788 | 71 | 100,0 % | 2743,5x |
| 587 | 7.11 Sentencia                                                                                       198 | Familia | 100107 | 37 | 100,0 % | 2705,6x |
| 588 | 7.13      El recurso | Laboral | 100583 | 41 | 100,0 % | 2453,2x |
| 589 | 7.14              Recurso de unificación | Laboral | 100583 | 49 | 100,0 % | 2052,7x |
| 590 | 7.2    Derechos de la víctima | Penal | 211066 | 81 | 100,0 % | 2605,8x |
| 591 | 7.2    El nuevo derecho | Constitucional | 104063 | 41 | 100,0 % | 2538,1x |
| 592 | 7.3    El documento y firma electrónicaen los | Judicial | 96536 | 42 | 100,0 % | 2298,5x |
| 593 | 7.3    Notificación de vulneraciones | Constitucional | 104063 | 36 | 100,0 % | 2890,6x |
| 594 | 7.3. Por la comprobación judicial de la muerte de uno de los convivientes civiles | Familia | 190697 | 92 | 100,0 % | 2072,8x |
| 595 | 7.3.4 Prohibición de la querella | Penal | 211066 | 98 | 100,0 % | 2153,7x |
| 596 | 7.3.5 Desistimiento de la querella | Penal | 211066 | 100 | 100,0 % | 2110,7x |
| 597 | 7.3.8 Tipos de acciones civiles | Penal | 211066 | 79 | 100,0 % | 2671,7x |
| 598 | 7.4    Requisitos | Judicial | 96536 | 29 | 100,0 % | 3328,8x |
| 599 | 7.4    Régimen | Constitucional | 104063 | 32 | 100,0 % | 3252,0x |
| 600 | 7.4 Requisitos comunes                                                                              241 | Judicial | 96536 | 33 | 100,0 % | 2925,3x |
| 601 | 7.9     La audiencia | Laboral | 100583 | 46 | 100,0 % | 2186,6x |
| 602 | 70                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 83 | 100,0 % | 3783,0x |
| 603 | 70 Para más información, véase el artículo 1, sobre Protocolo facultativo de la | Constitucional | 177323 | 58 | 100,0 % | 3057,3x |
| 604 | 71 Específicamente en la propuesta 12, consistente en «perfeccionar y ampliar las | Penal | 178516 | 65 | 100,0 % | 2746,4x |
| 605 | 71 Sentencia de la Corte de Apelaciones de Rancagua, 16 de marzo de 2016, rol | Familia | 123490 | 59 | 100,0 % | 2093,1x |
| 606 | 73 Sentencia Corte Suprema rol 5165-2013, de 14 de abril de 2014 y sentencia Corte | Judicial | 144656 | 71 | 100,0 % | 2037,4x |
| 607 | 74 Consejo Asesor Presidencial Contra los Conflictos de Interés, el Tráfico de | Penal | 178516 | 67 | 100,0 % | 2664,4x |
| 608 | 74 El autor considera que los modelos psicológicos sugieren que el proceso de | Judicial | 150341 | 65 | 100,0 % | 2312,9x |
| 609 | 74 Para más información, véase artículo 2, sobre Convención Interamericana | Constitucional | 177323 | 71 | 100,0 % | 2497,5x |
| 610 | 74 Sentencia de la Corte de Apelaciones de San Miguel, 19 de julio de 2021, rol | Judicial | 150341 | 57 | 100,0 % | 2637,6x |
| 611 | 75 CP y 351 CPP y las discusiones acerca de su pertinencia y efectos en los casos | General | 313985 | 48 | 100,0 % | 6541,4x |
| 612 | 75 Organismo público internacional incluye a cualquier organismo internacional | Penal | 178516 | 84 | 100,0 % | 2125,2x |
| 613 | 75 Sentencia de la Corte de Apelaciones de Antofagasta, 15 de febrero de 2022, rol | Judicial | 150341 | 66 | 100,0 % | 2277,9x |
| 614 | 76 Sentencia de la Corte de Apelaciones de Santiago, rol 1420-2014, 21 de julio de | Penal | 178516 | 68 | 100,0 % | 2625,2x |
| 615 | 77 Sentencia de la Corte de Apelaciones de Santiago, 11 de febrero de 2022, rol | Judicial | 150341 | 61 | 100,0 % | 2464,6x |
| 616 | 78 Decreto 2.421 de 1964, que Fija el Texto Refundido de la Ley de Organización y | Penal | 178516 | 58 | 100,0 % | 3077,9x |
| 617 | 79 Sin perjuicio de que, como veremos en la sección siguiente, la amplitud de | Penal | 178516 | 62 | 100,0 % | 2879,3x |
| 618 | 8   Código Procesal Penal modelo para Latinoamérica. Disponible en: http://biblioteca.cejamericas.org/hand- | Penal | 211066 | 63 | 100,0 % | 3350,3x |
| 619 | 8 En este sentido Nieva (2010: 89) dice: «aquello que se deduce de la sana crítica | Judicial | 150341 | 72 | 100,0 % | 2088,1x |
| 620 | 8. Cumplimiento de Acuerdo de Solución Amistosa caso César Pe- | Constitucional | 177323 | 84 | 100,0 % | 2111,0x |
| 621 | 8. Suscribir –previo acuerdo adoptado en asamblea extraordinaria especialmente citada | Civil | 192585 | 70 | 100,0 % | 2751,2x |
| 622 | 8.1               Características de un sistema de justicia | Penal | 211066 | 65 | 100,0 % | 3247,2x |
| 623 | 8.1           El procedimiento | Laboral | 100583 | 40 | 100,0 % | 2514,6x |
| 624 | 8.1           Legitimación para | Constitucional | 104063 | 46 | 100,0 % | 2262,2x |
| 625 | 8.10                Acción de tutela de | Laboral | 100583 | 50 | 100,0 % | 2011,7x |
| 626 | 8.11                Derechos | Laboral | 100583 | 45 | 100,0 % | 2235,2x |
| 627 | 8.15     Prueba | Laboral | 100583 | 41 | 100,0 % | 2453,2x |
| 628 | 8.3     Actuación administrativa | Laboral | 100583 | 46 | 100,0 % | 2186,6x |
| 629 | 8.3     Análisis de casos de determinación de penas | Penal | 211066 | 83 | 100,0 % | 2543,0x |
| 630 | 83 Recordar lo que anotábamos respecto del comportamiento estratégico de los | Judicial | 150341 | 53 | 100,0 % | 2836,6x |
| 631 | 84                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 87 | 100,0 % | 3609,0x |
| 632 | 88 Es un principio metodológico y filosófico atribuido a Guillermo de Ockham | Judicial | 150341 | 68 | 100,0 % | 2210,9x |
| 633 | 89 Por ejemplo, la tramitación de recursos de inaplicabilidad ante el Tribunal | Penal | 178516 | 75 | 100,0 % | 2380,2x |
| 634 | 9 Donde se ha discutido no solo cuál es el objeto de tutela, sino también si existe | Penal | 178516 | 84 | 100,0 % | 2125,2x |
| 635 | 9 Puede considerarse una irregularidad administrativa contraria a la probidad el | Penal | 178516 | 66 | 100,0 % | 2704,8x |
| 636 | 9. Dejar constancia de los acuerdos de la asamblea en un libro de actas foliado, que | Civil | 192585 | 94 | 100,0 % | 2048,8x |
| 637 | 9. Pedir al tribunal competente que aplique los apremios o sanciones que procedan al | Civil | 192585 | 92 | 100,0 % | 2093,3x |
| 638 | 9.1           Apreciación prueba de peritos | Penal | 211066 | 78 | 100,0 % | 2706,0x |
| 639 | 9.1     Los títulos | Laboral | 100583 | 46 | 100,0 % | 2186,6x |
| 640 | 9.2         Análisis de casos de valoración | Penal | 211066 | 81 | 100,0 % | 2605,8x |
| 641 | 9.2     El “targeting”, los algoritmos y la | Constitucional | 104063 | 41 | 100,0 % | 2538,1x |
| 642 | 9.4               Videovigilancia e imágenes | Constitucional | 104063 | 42 | 100,0 % | 2477,7x |
| 643 | 90 Asamblea General de las Naciones Unidas, «Informe del relator especial sobre | Penal | 178516 | 62 | 100,0 % | 2879,3x |
| 644 | 90 OEA, «Relatoría sobre los Derechos de las Personas Privadas de Libertad y | Constitucional | 177323 | 61 | 100,0 % | 2906,9x |
| 645 | 91 Juzgados | Procesal | 101194 | 35 | 100,0 % | 2891,3x |
| 646 | 94                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 76 | 100,0 % | 4131,4x |
| 647 | 96                 Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 65 | 100,0 % | 4830,5x |
| 648 | 98                 Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 52 | 100,0 % | 6038,2x |
| 649 | A 245) | General | 313985 | 66 | 100,0 % | 4757,3x |
| 650 | A la vida | General | 313985 | 80 | 100,0 % | 3924,8x |
| 651 | APLICACIÓN DE LA LEY Nº 19.223 Y DE LA LEY GENERAL DE | General | 313985 | 40 | 100,0 % | 7849,6x |
| 652 | Abigeato y receptación del cp (arts. 449 a 456 bis) | General | 313985 | 54 | 100,0 % | 5814,5x |
| 653 | Administración de justicia | General | 313985 | 46 | 100,0 % | 6825,8x |
| 654 | Art. 12) | General | 313985 | 46 | 100,0 % | 6825,8x |
| 655 | Bien jurídico y constitución | General | 313985 | 102 | 100,0 % | 3078,3x |
| 656 | Capitulo ii: concepto, regulación, naturaleza y | Familia | 136567 | 49 | 100,0 % | 2787,1x |
| 657 | Capitulo viii: la permuta | Civil | 153962 | 76 | 100,0 % | 2025,8x |
| 658 | Capítulo 1 | General | 313985 | 57 | 100,0 % | 5508,5x |
| 659 | Capítulo 10 | General | 313985 | 42 | 100,0 % | 7475,8x |
| 660 | Capítulo 2 | General | 313985 | 57 | 100,0 % | 5508,5x |
| 661 | Capítulo 3 | General | 313985 | 67 | 100,0 % | 4686,3x |
| 662 | Capítulo 5 | General | 313985 | 67 | 100,0 % | 4686,3x |
| 663 | Capítulo 6 | General | 313985 | 58 | 100,0 % | 5413,5x |
| 664 | Capítulo 7 | General | 313985 | 33 | 100,0 % | 9514,7x |
| 665 | Capítulo 8 | General | 313985 | 50 | 100,0 % | 6279,7x |
| 666 | Certificados y licencias médicas (arts. 199 a 207) | General | 313985 | 71 | 100,0 % | 4422,3x |
| 667 | Comunicaciones privadas | General | 313985 | 52 | 100,0 % | 6038,2x |
| 668 | Condominio acogido a la ley de copropiedad inmobiliaria, art. 6, inc. 3° | Civil | 153962 | 49 | 100,0 % | 3142,1x |
| 669 | Contrato de compraventa289 | Civil | 153962 | 32 | 100,0 % | 4811,3x |
| 670 | Control judicial | Procesal | 96699 | 36 | 100,0 % | 2686,1x |
| 671 | Copropiedad inmobiliaria1 | Civil | 192585 | 35 | 100,0 % | 5502,4x |
| 672 | Criterios jurisprudenciales | Civil | 192585 | 78 | 100,0 % | 2469,0x |
| 673 | Cuarta parte: del concubinato | Familia | 190697 | 81 | 100,0 % | 2354,3x |
| 674 | De la sociedad conyugal | Familia | 136567 | 37 | 100,0 % | 3691,0x |
| 675 | Del aborto voluntario en tres causales | General | 313985 | 54 | 100,0 % | 5814,5x |
| 676 | Del periodismo | General | 313985 | 76 | 100,0 % | 4131,4x |
| 677 | ESTRICTO. MODALIDADES DE TRÁFICO (ART. 3º INC. 1º) | General | 313985 | 59 | 100,0 % | 5321,8x |
| 678 | En caso de tratarse de un inmueble situado en zona fronteriza, las | Civil | 153962 | 52 | 100,0 % | 2960,8x |
| 679 | En cuanto al recurso de casación en el fondo deducido del | Civil | 171433 | 79 | 100,0 % | 2170,0x |
| 680 | En particular: delitos y cuasidelitos civiles | Civil | 96458 | 41 | 100,0 % | 2352,6x |
| 681 | Enriquecimiento por apropiación | General | 313985 | 49 | 100,0 % | 6407,9x |
| 682 | Especial, el delito de desacato del art. 240 cpc | General | 313985 | 62 | 100,0 % | 5064,3x |
| 683 | Estupefacientes | General | 313985 | 87 | 100,0 % | 3609,0x |
| 684 | Evaluación de riesgos | Familia | 95131 | 41 | 100,0 % | 2320,3x |
| 685 | Falsas (art. 207) | General | 313985 | 42 | 100,0 % | 7475,8x |
| 686 | Falsedades documentales | General | 313985 | 65 | 100,0 % | 4830,5x |
| 687 | I.- del pasivo de la sociedad conyugal y de los conyuges en | Familia | 136567 | 50 | 100,0 % | 2731,3x |
| 688 | I.- generalidades sobre la familia | Familia | 190697 | 83 | 100,0 % | 2297,6x |
| 689 | Ii.- del pasivo de la sociedad conyugal y de los conyuges en | Familia | 136567 | 50 | 100,0 % | 2731,3x |
| 690 | Ii.- el parentesco | Familia | 190697 | 87 | 100,0 % | 2191,9x |
| 691 | Iii.- el derecho de familia y los derechos de familia | Familia | 190697 | 92 | 100,0 % | 2072,8x |
| 692 | Isbn: 978-84-9190-111-2 | General | 313985 | 32 | 100,0 % | 9812,0x |
| 693 | Iv.- mutabilidad del régimen de participación en los gananciales y de los | Familia | 136567 | 61 | 100,0 % | 2238,8x |
| 694 | Ley 18.314) | General | 313985 | 49 | 100,0 % | 6407,9x |
| 695 | Leyes especiales | General | 313985 | 46 | 100,0 % | 6825,8x |
| 696 | Libertad e integridad sexuales | General | 313985 | 41 | 100,0 % | 7658,2x |
| 697 | Libertades de opinión e información y ejercicio del periodis- | General | 313985 | 61 | 100,0 % | 5147,3x |
| 698 | Los derechos garantidos por la consitución | General | 313985 | 50 | 100,0 % | 6279,7x |
| 699 | Moral | General | 313985 | 42 | 100,0 % | 7475,8x |
| 700 | PRIVADAS (ART. 161-A INC. 2º) | General | 313985 | 53 | 100,0 % | 5924,2x |
| 701 | PROTOCOLO_DIGITAL_FINAL.pdf | Constitucional | 177323 | 76 | 100,0 % | 2333,2x |
| 702 | Parte III: Guía para Juzgar con Perspectiva de Género | Judicial | 93914 | 46 | 100,0 % | 2041,6x |
| 703 | Personas (art. 474) | General | 313985 | 49 | 100,0 % | 6407,9x |
| 704 | Piratería (art. 434) | General | 313985 | 66 | 100,0 % | 4757,3x |
| 705 | PregUnta:COMO ELTRIBUNAL CONSTITUCIONAL CONOCE ESTA | Procesal | 95124 | 45 | 100,0 % | 2113,9x |
| 706 | Pregunta: &CUALES SON ESAS EXCEPCIONES ESTABLECIDAS EN | Procesal | 95124 | 46 | 100,0 % | 2067,9x |
| 707 | Pregunta: &PUEDE PEDIRLAS EL DEMANDADO EN ALGUN CASO? | Procesal | 95124 | 46 | 100,0 % | 2067,9x |
| 708 | Pregunta: 2COMO SE NOTIFICA LA RESOLUCION QUE RECIBE A | Procesal | 95124 | 46 | 100,0 % | 2067,9x |
| 709 | Pregunta: CUAL ES LA FORMA NORMAL DE TERMINAR EL JUICIO | Procesal | 95124 | 46 | 100,0 % | 2067,9x |
| 710 | Pregunta: CUALES SON LOS FACTORES QUE DETERMINAN LA | Procesal | 95124 | 44 | 100,0 % | 2161,9x |
| 711 | Pregunta: EN QUE PLAZO DEBEN CUMPLIRSE LAS MEDIDAS PARA | Procesal | 95124 | 45 | 100,0 % | 2113,9x |
| 712 | Pregunta: EXCEPCIONES EN LAS QUE OBLIGACIONES QUE DEBAN | Procesal | 95124 | 45 | 100,0 % | 2113,9x |
| 713 | Pregunta: JQUE PARTICULARIDAD TIENE LA TRAMITACION DE | Procesal | 95124 | 44 | 100,0 % | 2161,9x |
| 714 | Pregunta: PUEDE APELARSE DE LA RESOLUCION QUE DESECHA | Procesal | 95124 | 44 | 100,0 % | 2161,9x |
| 715 | Pregunta: QUE PASA SI NO DEMANDA DENTRO DE ESE PLAZO? | Procesal | 95124 | 46 | 100,0 % | 2067,9x |
| 716 | Pregunta: REQUIEREN TASACION PREVIA ESTOS BIENES PARA | Procesal | 95124 | 42 | 100,0 % | 2264,9x |
| 717 | Pregunta:CONTRA QUE RESOLUCIOWES PROCEDE LA REPOSL | Procesal | 95124 | 41 | 100,0 % | 2320,1x |
| 718 | Pregunta:CUALES SON LAS CARACTERISTICAS DEL AMPARO | Procesal | 95124 | 41 | 100,0 % | 2320,1x |
| 719 | Pregunta:PUEDE SOLICITARSE AUMENTO EXTRAORDINARIO | Procesal | 95124 | 45 | 100,0 % | 2113,9x |
| 720 | Prevalecer aquella que ampara a quien también tiene la posesión material del | Civil | 171433 | 74 | 100,0 % | 2316,7x |
| 721 | Primera parte: conceptos fundamentales | Civil | 92843 | 39 | 100,0 % | 2380,6x |
| 722 | Primera parte: la familia | Familia | 190697 | 74 | 100,0 % | 2577,0x |
| 723 | Progunta:CUALESELTRIBUNAL COMPETENTE PARA CONOCER | Procesal | 95124 | 42 | 100,0 % | 2264,9x |
| 724 | Prostitución (art. 411 ter) | General | 313985 | 52 | 100,0 % | 6038,2x |
| 725 | Pública | General | 313985 | 53 | 100,0 % | 5924,2x |
| 726 | QUE DECRETA UNA MEDIDA PARA MEJOR RESOLPregunta: &COMO SE DECRETAN? | Procesal | 95124 | 46 | 100,0 % | 2067,9x |
| 727 | Que se pueden extraer de éstas.1 | Civil | 171433 | 67 | 100,0 % | 2558,7x |
| 728 | Quinquies, y 367) | General | 313985 | 45 | 100,0 % | 6977,4x |
| 729 | Quinta parte: de la mediación familiar | Familia | 190697 | 74 | 100,0 % | 2577,0x |
| 730 | Res/45/17 | Constitucional | 177323 | 68 | 100,0 % | 2607,7x |
| 731 | Rit: 96-2022 | Penal | 194788 | 50 | 100,0 % | 3895,8x |
| 732 | Seccion primera: del haber o activo de la sociedad conyugal | Familia | 136567 | 62 | 100,0 % | 2202,7x |
| 733 | Seccion segunda: de la administracion | Familia | 136567 | 67 | 100,0 % | 2038,3x |
| 734 | Sexta parte: del acuerdo de unión civil | Familia | 190697 | 81 | 100,0 % | 2354,3x |
| 735 | Suministros (art. 447 bis) | General | 313985 | 46 | 100,0 % | 6825,8x |
| 736 | Titulo iii: de la seguridad del condominio y del termino o modificacion de | Civil | 192585 | 85 | 100,0 % | 2265,7x |
| 737 | Trata de personas | General | 313985 | 58 | 100,0 % | 5413,5x |
| 738 | Título I: Consecuencias de la declaración de | Penal | 194788 | 85 | 100,0 % | 2291,6x |
| 739 | Título II: Procedimiento | Penal | 194788 | 62 | 100,0 % | 3141,7x |
| 740 | Título III: De la ejecución de las sanciones y medidas | Penal | 194788 | 53 | 100,0 % | 3675,2x |
| 741 | Título IV del Libro II, “de las falsedades vertidas en el proceso y del perjurio”. Ello | General | 313985 | 83 | 100,0 % | 3783,0x |
| 742 | V.- de la nulidad del matrimonio | Familia | 190697 | 49 | 100,0 % | 3891,8x |
| 743 | Viii.- de la ley aplicable al matrimonio y del reconocimiento de | Familia | 190697 | 80 | 100,0 % | 2383,7x |
| 744 | X                   x       x | Constitucional | 104063 | 33 | 100,0 % | 3153,4x |
| 745 | X.- diferencias entre el régimen de participación en los gananciales y el | Familia | 136567 | 46 | 100,0 % | 2968,8x |
| 746 | Xi.- diferencias entre el régimen de participación en los gananciales y el | Familia | 136567 | 53 | 100,0 % | 2576,7x |
| 747 | Y 232) | General | 313985 | 128 | 100,0 % | 2453,0x |
| 748 | Y de la honra. régimen de prensa | General | 313985 | 62 | 100,0 % | 5064,3x |
| 749 | c) SEGUN LA | Procesal | 95124 | 44 | 100,0 % | 2161,9x |
| 750 | capítulo II referido a la regulación de la celebración del matrimonio, en | Familia | 123490 | 50 | 100,0 % | 2469,8x |
| 751 | capítulo teórico finaliza con una sentencia para analizar y material | Penal | 211066 | 89 | 100,0 % | 2371,5x |
| 752 | capítulo trataremos las garantías como límites constitucionales al | Penal | 211066 | 55 | 100,0 % | 3837,6x |
| 753 | e) SEGUN | Procesal | 95124 | 44 | 100,0 % | 2161,9x |
| 754 | parte a su vez de la llamada carrera funcionaria, que es asegurada por | Procesal | 101194 | 50 | 100,0 % | 2023,9x |
| 755 | parte con la antigua idea de eutanasia pasiva, aunque se diferencia de ésta por la | General | 313985 | 67 | 100,0 % | 4686,3x |
| 756 | parte de la comunidad de sordos (Cultura Sorda) rechaza este procedimiento médico pues teme que dicha | Constitucional | 121906 | 58 | 100,0 % | 2101,8x |
| 757 | parte de una automotora de un vehículo entregado para reparaciones, alegando | General | 313985 | 54 | 100,0 % | 5814,5x |
| 758 | parte denunciante, para que se aumente la suma fijada por indemnización de daño | Civil | 192585 | 79 | 100,0 % | 2437,8x |
| 759 | parte en conflicto.171 | Penal | 121924 | 59 | 100,0 % | 2066,5x |
| 760 | parte limita el elemento negativo al destino que a las sustancias que se tratan | General | 313985 | 80 | 100,0 % | 3924,8x |
| 761 | parte o colabore en la comisión del delito que se ejecuta mediante el documento que | General | 313985 | 141 | 100,0 % | 2226,8x |
| 762 | parte resolutiva del fallo, donde la sala por unanimidad, o bien por | Penal | 211066 | 92 | 100,0 % | 2294,2x |
| 763 | parte soporta el riesgo de la falta de tal prueba, el cual se traduce en una decisión | Judicial | 150341 | 55 | 100,0 % | 2733,5x |
| 764 | parte técnica con la subsecretaría de Derechos Humanos, más en | Constitucional | 177323 | 78 | 100,0 % | 2273,4x |
| 765 | parte, como en el ejemplo de Politoff, la apropiación de una chimenea de mármol | General | 313985 | 135 | 100,0 % | 2325,8x |
| 766 | parte, de los fines que se pretenda alcanzar con la pena y la naturaleza | Penal | 194788 | 54 | 100,0 % | 3607,2x |
| 767 | parte, el 83 de la Ley Orgánica del Servicio de Correos y Telégrafos, reproduce | General | 313985 | 96 | 100,0 % | 3270,7x |
| 768 | parte, entre el método lógico tradicional y por otra parte, los métodos nuevos o | General | 125500 | 59 | 100,0 % | 2127,1x |
| 769 | parte, reforzando la prohibición señalada, en el Art. 17 Ley Nº 20.120 se establece | General | 313985 | 65 | 100,0 % | 4830,5x |
| 770 | parte. Resta, entonces, revisar la forma en que el Convenio aborda | Judicial | 134465 | 53 | 100,0 % | 2537,1x |
| 771 | sección Calle Freire, se acercó desde atrás el imputado Hugo, quien le | Penal | 194788 | 89 | 100,0 % | 2188,6x |
| 772 | su nombre). (EN EL EVENTO DE QUE EL DERECHO DE USO Y GOCE EXCLUSIVO SOBRE | Civil | 153962 | 61 | 100,0 % | 2524,0x |
| 773 | título de parricida, pudiendo considerarse el envenenamiento como circunstancia | General | 313985 | 58 | 100,0 % | 5413,5x |
| 774 | título es transmisible a todos los partícipes y está sujeto a las reglas generales de | General | 313985 | 53 | 100,0 % | 5924,2x |
| 775 | título translaticio de dominio, por mandato del art. 703. A su vez, en el primer caso, el | Familia | 136567 | 66 | 100,0 % | 2069,2x |
| 776 | título, el procedimiento por delito de acción privada se regirá por las normas | Penal | 211066 | 100 | 100,0 % | 2110,7x |
| 777 | §1. bien jurídico protegido y despenalización parcial del aborto | General | 313985 | 45 | 100,0 % | 6977,4x |
| 778 | §1. bien jurídico protegido y déficits normativos | General | 313985 | 66 | 100,0 % | 4757,3x |
| 779 | §10. FALTA DE OMISIÓN DE SOCORRO (ART. 494 Nº 14) | General | 313985 | 61 | 100,0 % | 5147,3x |
| 780 | §10. FRAUDE EN LA OBTENCIÓN DE SUBVENCIONES (ART. 470 Nº | General | 313985 | 50 | 100,0 % | 6279,7x |
| 781 | §11. abusos contra particulares (arts. 255 a 259) | General | 313985 | 53 | 100,0 % | 5924,2x |
| 782 | §11. obstrucción a la investigación (art. 269 bis) | General | 313985 | 81 | 100,0 % | 3876,4x |
| 783 | §13. otras formas de obstrucción a la justicia. en especial, el | General | 313985 | 52 | 100,0 % | 6038,2x |
| 784 | §13. robos calificados (art. 433) | General | 313985 | 49 | 100,0 % | 6407,9x |
| 785 | §13. usurpación de atribuciones (arts. 221 y 222) | General | 313985 | 130 | 100,0 % | 2415,3x |
| 786 | §14. robo por sorpresa como forma privilegida (art. 436 | General | 313985 | 37 | 100,0 % | 8486,1x |
| 787 | §16. APROPIACIÓN INDEBIDA (ART. 470 Nº 1) | General | 313985 | 59 | 100,0 % | 5321,8x |
| 788 | §16. abigeato (art. 448 bis a sexies) | General | 313985 | 58 | 100,0 % | 5413,5x |
| 789 | §17. receptación (art. 456 bis a) | General | 313985 | 84 | 100,0 % | 3737,9x |
| 790 | §18. usura (art. 472) | General | 313985 | 50 | 100,0 % | 6279,7x |
| 791 | §19. disposiciones comunes a los delitos de hurto, robo, abigeato | General | 313985 | 68 | 100,0 % | 4617,4x |
| 792 | §2. HOMICIDIO SIMPLE (ART. 391 Nº 2) | General | 313985 | 132 | 100,0 % | 2378,7x |
| 793 | §2. lesiones menos graves (art. 399) | General | 313985 | 48 | 100,0 % | 6541,4x |
| 794 | §2. prevaricación judicial (arts. 223 a 227) | General | 313985 | 52 | 100,0 % | 6038,2x |
| 795 | §2. problemas comunes a los delitos cometidos por empleados | General | 313985 | 41 | 100,0 % | 7658,2x |
| 796 | §2. tráfico de migrantes (art. 411 bis) | General | 313985 | 66 | 100,0 % | 4757,3x |
| 797 | §2. tráfico ilícito de estupefacientes en sentido amplio | General | 313985 | 41 | 100,0 % | 7658,2x |
| 798 | §20. PIRATERÍA AÉREA O SECUESTRO DE AERONAVES (ART. 2 Nº 2 LEY | General | 313985 | 50 | 100,0 % | 6279,7x |
| 799 | §22. otros delitos de apropiación comprendidos en leyes especia- | General | 313985 | 58 | 100,0 % | 5413,5x |
| 800 | §3. enriquecimiento ilícito (art. 241 bis) | General | 313985 | 40 | 100,0 % | 7849,6x |
| 801 | §3. violación impropia (art. 362) | General | 313985 | 70 | 100,0 % | 4485,5x |
| 802 | §4. DERECHO A LA PRIVACIDAD EN INTERNET. APLICACIÓN DE LA LEY Nº | General | 313985 | 53 | 100,0 % | 5924,2x |
| 803 | §4. MICROTRÁFICO, FIGURA PRIVILEGIADA (ART. 4º) | General | 313985 | 52 | 100,0 % | 6038,2x |
| 804 | §4. amenazas (arts. 296 a 298) | General | 313985 | 71 | 100,0 % | 4422,3x |
| 805 | §4. injurias (art. 416) | General | 313985 | 75 | 100,0 % | 4186,5x |
| 806 | §4. malversación de caudales públicos (arts. 233 a 235) | General | 313985 | 53 | 100,0 % | 5924,2x |
| 807 | §4. parricidio (art. 390) | General | 313985 | 44 | 100,0 % | 7136,0x |
| 808 | §4. usurpación de aguas (arts. 459 a 461) | General | 313985 | 75 | 100,0 % | 4186,5x |
| 809 | §5. ESTAFAS CON CAUSA ILÍCITA (ARTS. 469 Nº 5 470 Nº 7) | General | 313985 | 92 | 100,0 % | 3412,9x |
| 810 | §5. FEMICIDIO (ART. 390, INC. 2º) | General | 313985 | 52 | 100,0 % | 6038,2x |
| 811 | §5. calumnias (art. 412) | General | 313985 | 33 | 100,0 % | 9514,7x |
| 812 | §5. estupro (art. 363) | General | 313985 | 32 | 100,0 % | 9812,0x |
| 813 | §5. hurto de uso | General | 313985 | 44 | 100,0 % | 7136,0x |
| 814 | §5. lesiones agravadas por la forma de su ejecución (mutilacio- | General | 313985 | 55 | 100,0 % | 5708,8x |
| 815 | §5. prevaricación administrativa (art. 228) | General | 313985 | 63 | 100,0 % | 4983,9x |
| 816 | §6. abusos sexuales (arts. 365 bis a 366 ter) | General | 313985 | 72 | 100,0 % | 4360,9x |
| 817 | §6. delitos de maltrato (art. 403 bis) | General | 313985 | 66 | 100,0 % | 4757,3x |
| 818 | §6. suministro abusivo de sustancias estupefacientes | General | 313985 | 42 | 100,0 % | 7475,8x |
| 819 | §7. DELITOS ESPECIALES CONTEMPLADOS EN LA LEY Nº 19.733, SOBRE | General | 313985 | 37 | 100,0 % | 8486,1x |
| 820 | §7. auxilio al suicidio (art. 393) | General | 313985 | 68 | 100,0 % | 4617,4x |
| 821 | §7. detención arbitraria (art. 143) | General | 313985 | 67 | 100,0 % | 4686,3x |
| 822 | §7. falsedades vertidas en el proceso (art. 206) | General | 313985 | 50 | 100,0 % | 6279,7x |
| 823 | §7. sustracción fraudulenta de expedientes (art. 470 n° 5) | General | 313985 | 65 | 100,0 % | 4830,5x |
| 824 | §7. uso de información privilegiada (art. 247 bis) | General | 313985 | 52 | 100,0 % | 6038,2x |
| 825 | §8. cohecho (arts. 248 a 251) | General | 313985 | 76 | 100,0 % | 4131,4x |
| 826 | §8. disposiciones comunes a los delitos de los arts. 361 a 367 bis | General | 313985 | 49 | 100,0 % | 6407,9x |
| 827 | §8. hurto de hallazgo (art. 448) | General | 313985 | 70 | 100,0 % | 4485,5x |
| 828 | §8. suscripción engañosa de documentos (art. 470 n°. 4) | General | 313985 | 78 | 100,0 % | 4025,4x |
| 829 | §9.   faltas contra la salud pública relativas al consumo perso- | General | 313985 | 46 | 100,0 % | 6825,8x |
| 830 | §9. perjurio (art. 212) | General | 313985 | 48 | 100,0 % | 6541,4x |
| 831 | (1977), p. 625; LACHS (1980), p. 206; ZOGLIN (1986), p. 306; REUTER (1982), p. 49; MINAGAWA (1968), p. 8; SATO | Penal | 121924 | 137 | 99,9 % | 890,0x |
| 832 | (2005), pp. 37, 38, 74; FERDINANDUSSE (2006), p. 257; ÁLVAREZ (2008), p. 28; CASSESE (2008), p. 439; SHAW | Penal | 121924 | 61 | 99,9 % | 1998,8x |
| 833 | (2018-i)/82555137005/ | Judicial | 87237 | 75 | 99,9 % | 1163,2x |
| 834 | (acnudh, 2009: 14) | Constitucional | 177323 | 184 | 99,9 % | 963,7x |
| 835 | (empam) | Judicial | 82507 | 50 | 99,9 % | 1650,1x |
| 836 | .- des gnac ón de los guardadores | Familia | 85324 | 83 | 99,9 % | 1028,0x |
| 837 | 1   La primera versión es de 2016 y más tarde fue publicada dentro de la colección Cuadernos Jurídicos de la | Judicial | 105809 | 137 | 99,9 % | 772,3x |
| 838 | 1   PODER JUDICIAL, Acta N° 162-2019, p. 2 | Procesal | 94881 | 72 | 99,9 % | 1317,8x |
| 839 | 1 Academia Judicial de Chile (2020). «Informe de Detección de Necesidades | Laboral | 53293 | 62 | 99,9 % | 859,6x |
| 840 | 1 Adicionalmente, en el artículo 6 letra h) de la Ley 21.302 se habla de «supervisión | Constitucional | 46896 | 66 | 99,9 % | 710,5x |
| 841 | 1 Artículo 25. Los tribunales de la Federación ampararán a cualquier habitante | Constitucional | 177323 | 141 | 99,9 % | 1257,6x |
| 842 | 1 Con Acta de Radicación a su favor | Judicial | 82507 | 57 | 99,9 % | 1447,5x |
| 843 | 1 El Glosario de términos legales se puede encontrar en el siguiente enlace: https:// | Judicial | 53521 | 54 | 99,9 % | 991,1x |
| 844 | 1 El artículo 37 de la Convención señala: «Los Estados parte velarán porque: a) | Penal | 194788 | 188 | 99,9 % | 1036,1x |
| 845 | 1 El autor considera que «si una cultura social incluye entre sus valores a la justicia | Judicial | 150341 | 141 | 99,9 % | 1066,2x |
| 846 | 1 Empleamos el término comunicabilidad por ser ampliamente utilizado por la | Penal | 178516 | 127 | 99,9 % | 1405,6x |
| 847 | 1 En dicha trilogía, como se referirá en el capítulo pertinente, el precedente central | Procesal | 86112 | 93 | 99,9 % | 925,9x |
| 848 | 1 En lo sucesivo, al citar artículos sin señalar una ley se entenderá que pertenecen | Laboral | 74025 | 55 | 99,9 % | 1345,9x |
| 849 | 1 En materia de protección se ha verificado un cambio normativo e institucional | Familia | 97488 | 136 | 99,9 % | 716,8x |
| 850 | 1 En nuestro país, Aldunate (2008: 278 y 279) niega que la pugna de derechos sea | Judicial | 144656 | 167 | 99,9 % | 866,2x |
| 851 | 1 En opinión del profesor Marín González (2008: 64), «se llegó a un escenario | Penal | 194788 | 205 | 99,9 % | 950,2x |
| 852 | 1 Entiéndase por régimen tributario como aquél que comprende un conjunto de | Judicial | 62888 | 61 | 99,9 % | 1031,0x |
| 853 | 1 Este numeral contemplaba la denominada prevaricación-cohecho, numeral que | Penal | 178516 | 114 | 99,9 % | 1565,9x |
| 854 | 1 Extraído del material de estudio del Máster Interdisciplinar en Prevención y | Judicial | 82507 | 84 | 99,9 % | 982,2x |
| 855 | 1 Fundación Europea para la Mejora de las Condiciones de Vida y de Trabajo | Laboral | 98828 | 120 | 99,9 % | 823,6x |
| 856 | 1 Juzgado de Letras de Talca, RIT I-8-2018 del 20 de abril de 2018, considerando | Laboral | 98828 | 61 | 99,9 % | 1620,1x |
| 857 | 1 La aparición y el desarrollo del virus covid-19 provocó la masificación temprana | Judicial | 87950 | 79 | 99,9 % | 1113,3x |
| 858 | 1 La derogación del artículo 365 del Código Penal, el 24 de agosto de 2022, estuvo | Familia | 123490 | 102 | 99,9 % | 1210,7x |
| 859 | 1 Obviamente dichas normas sobre inadmisibilidad de medios probatorios se | Procesal | 86112 | 100 | 99,9 % | 861,1x |
| 860 | 1 Oficio FN 936 (2017: 19-20). Al respecto, recientemente, Corte Suprema, rol | Penal | 97633 | 79 | 99,9 % | 1235,9x |
| 861 | 1 Organización Mundial de la Salud. Nota Descriptiva 389 sobre la protección de | Laboral | 53293 | 62 | 99,9 % | 859,6x |
| 862 | 1 Otros ejemplos se encuentran en los delitos de los artículos 106, 107, 108, 109 y | Penal | 194788 | 114 | 99,9 % | 1708,7x |
| 863 | 1 Para García Pino y Contreras Vásquez el derecho a tutela judicial y el derecho | Judicial | 144656 | 159 | 99,9 % | 909,8x |
| 864 | 1 Para ello, se consideró inicialmente que los principales desafíos en materia de | Penal | 178516 | 109 | 99,9 % | 1637,8x |
| 865 | 1 Para la evolución del régimen civil del matrimonio en Chile, véase Del Picó | Familia | 123490 | 72 | 99,9 % | 1715,1x |
| 866 | 1 Para saber más sobre la Década del Envejecimiento Saludable (2021-2030), véase | Judicial | 82507 | 46 | 99,9 % | 1793,6x |
| 867 | 1 Por ejemplo, como ocurría en nuestro país con el trabajo que se presta a través | Laboral | 98828 | 110 | 99,9 % | 898,4x |
| 868 | 1 Por esta solución se inclina la sentencia Corte Suprema rol 36787-2015, de 14 de | Judicial | 144656 | 137 | 99,9 % | 1055,9x |
| 869 | 1 Proyecto de Ley, iniciado en mensaje de la presidenta de la República, que crea el | Penal | 86906 | 104 | 99,9 % | 835,6x |
| 870 | 1 Requiere dicha «ostentación» para la sanción de la falta en estudio, Corte de | Penal | 97633 | 93 | 99,9 % | 1049,8x |
| 871 | 1 Se entienden como juzgados de familia de menor tamaño aquellos compuestos | Familia | 97488 | 76 | 99,9 % | 1282,7x |
| 872 | 1 Se puede revisar con más detalle la evolución de este proceso de modernización | Judicial | 42513 | 58 | 99,9 % | 733,0x |
| 873 | 1 Sentencia Corte Suprema de 12 de noviembre 2019, ingreso rol 18.587-2019 y | Judicial | 144656 | 100 | 99,9 % | 1446,6x |
| 874 | 1 Sobre el origen de esta categoría de análisis y sobre la incorporación del análisis | Judicial | 92792 | 89 | 99,9 % | 1042,6x |
| 875 | 1 Sobre un análisis profundo del concepto de inteligencia moral en la relación | Judicial | 87950 | 61 | 99,9 % | 1441,8x |
| 876 | 1 Un ejemplo de ello es la charla de Viviana Bilezker con Isolina Dabove sobre los | Judicial | 82507 | 61 | 99,9 % | 1352,6x |
| 877 | 1)DERECHO PROCESAL.JUICIO ORDINARIOY RECURSOS PROPregunta:COMO SE SOLICITA? | Procesal | 95124 | 126 | 99,9 % | 755,0x |
| 878 | 1.    Contraloría General de la República, dictamen Nº | Judicial | 105809 | 71 | 99,9 % | 1490,3x |
| 879 | 1.    Ley Nº 20.886 sobre tramitación electrónica de los | Judicial | 83934 | 55 | 99,9 % | 1526,1x |
| 880 | 1.   American Bar Association (1999): Standards of         9.    BCN (2008): Historia de la Ley Nº 20.286, que | Familia | 100107 | 107 | 99,9 % | 935,6x |
| 881 | 1.   Caso Cantos v. Argentina; Corte Interamericana de Derechos | Procesal | 96699 | 91 | 99,9 % | 1062,6x |
| 882 | 1.   Desde la perspectiva constitucional, ¿cuáles son las normas que involucra el principio de | Judicial | 105809 | 152 | 99,9 % | 696,1x |
| 883 | 1.   OBERG YÁÑEZ, Héctor: “Juzgados de Garantía y | Penal | 57066 | 81 | 99,9 % | 704,5x |
| 884 | 1.   Revisar y aplicar las normas que conciernen al caso teniendo en cuenta que, en materia de | Familia | 100107 | 75 | 99,9 % | 1334,8x |
| 885 | 1.   Rules of Civil Procedure Ontario (2020), disponible en World Wide | Procesal | 96699 | 109 | 99,9 % | 887,1x |
| 886 | 1. Adecuación de marco normativo en virtud de las modificaciones | Constitucional | 177323 | 93 | 99,9 % | 1906,7x |
| 887 | 1. Adoptar medidas para prevenir, sancionar y erradicar aquellas | Judicial | 82507 | 114 | 99,9 % | 723,7x |
| 888 | 1. Al aplicar las disposiciones | Judicial | 134465 | 109 | 99,9 % | 1233,6x |
| 889 | 1. Aplicación de Principios Rectores de Naciones Unidas en tratados | Constitucional | 177323 | 135 | 99,9 % | 1313,5x |
| 890 | 1. Artículo 16 de la Ley de Tribunales de Familia: «El interés superior | Familia | 97488 | 94 | 99,9 % | 1037,1x |
| 891 | 1. Artículo 5 letra c), en virtud del cual el consejero técnico debe, a | Familia | 100107 | 78 | 99,9 % | 1283,4x |
| 892 | 1. Atender otros factores que pueden dar origen a la discriminación | Constitucional | 177323 | 92 | 99,9 % | 1927,4x |
| 893 | 1. Atentado contra la vida o malos tratamientos graves contra la integridad física o | Familia | 190697 | 98 | 99,9 % | 1945,9x |
| 894 | 1. Boletín 3810-18 y 4.149-18, refundidos. Proyecto de ley que | Judicial | 89476 | 74 | 99,9 % | 1209,1x |
| 895 | 1. Búsqueda: Que la persona a quien debe notificarse personalmente | Judicial | 89450 | 85 | 99,9 % | 1052,4x |
| 896 | 1. Cada uno de los Estados partes en el presente Pacto se compromete | Constitucional | 177323 | 119 | 99,9 % | 1490,1x |
| 897 | 1. Casas, Lidia, y Lagos, Catalina. “Análisis crítico de la acción de no | Judicial | 87237 | 114 | 99,9 % | 765,2x |
| 898 | 1. Caso Duque contra Colombia | Judicial | 87237 | 68 | 99,9 % | 1282,9x |
| 899 | 1. Certificado de nacimiento del adolescente, en que consta que | Judicial | 93914 | 79 | 99,9 % | 1188,8x |
| 900 | 1. Claro. El consentimiento es activo. Se expresa mediante palabras | Judicial | 89476 | 85 | 99,9 % | 1052,7x |
| 901 | 1. Comentario a La historia de la sexualidad, partes 1, 2 y 3. Por Darin | Judicial | 87237 | 70 | 99,9 % | 1246,2x |
| 902 | 1. Comisión Interamericana de Derechos Humanos. Violencia y | Judicial | 87237 | 88 | 99,9 % | 991,3x |
| 903 | 1. Como un derecho sustantivo, del cual surge la obligación corre- | Judicial | 89476 | 70 | 99,9 % | 1278,2x |
| 904 | 1. Comparece don Jorge Figueroa Urrea, en representación de don | Penal | 194788 | 184 | 99,9 % | 1058,6x |
| 905 | 1. Comparecer, conjuntamente con el administrador, en representación de la asamblea | Civil | 192585 | 117 | 99,9 % | 1646,0x |
| 906 | 1. Convocatoria | Judicial | 79146 | 75 | 99,9 % | 1055,3x |
| 907 | 1. Cuando hayan sido cometidos por un empleado público que | Penal | 178516 | 118 | 99,9 % | 1512,8x |
| 908 | 1. Cuando la actuación del tribunal que conoció originalmente el | Judicial | 144656 | 79 | 99,9 % | 1831,1x |
| 909 | 1. De los artículos 2º y 3º comunes a los cuatro Convenios de | Penal | 121924 | 97 | 99,9 % | 1256,9x |
| 910 | 1. De los orígenes a la Baja Edad Media, 14ª edición, Madrid, Alianza Universidad | General | 129559 | 161 | 99,9 % | 804,7x |
| 911 | 1. De su integración | Penal | 57066 | 67 | 99,9 % | 851,7x |
| 912 | 1. Deberán adoptarse las medidas especiales que se precisen para | Judicial | 134465 | 74 | 99,9 % | 1817,1x |
| 913 | 1. Declaración Universal de Derechos Humanos (1948) | Judicial | 89476 | 65 | 99,9 % | 1376,6x |
| 914 | 1. Dentro del límite del grado o grados señalados por la ley como pena | Penal | 194788 | 101 | 99,9 % | 1928,6x |
| 915 | 1. Desde luego, es preciso que exista una pretensión de un particular | Judicial | 105809 | 119 | 99,9 % | 889,2x |
| 916 | 1. Diagnóstico | Procesal | 94881 | 89 | 99,9 % | 1066,1x |
| 917 | 1. Discriminación es cualquier distinción, exclusión, restricción o | Judicial | 93914 | 101 | 99,9 % | 929,8x |
| 918 | 1. Don M.G.G.G., proporcionará una pensión de alimentos en favor de su hijo A.R.G.P., la | Judicial | 79146 | 113 | 99,9 % | 700,4x |
| 919 | 1. El Estado es responsable por la violación del derecho a la igualdad | Judicial | 87237 | 128 | 99,9 % | 681,5x |
| 920 | 1. El Estado parte en el territorio de cuya jurisdicción sea hallada la | Judicial | 78893 | 114 | 99,9 % | 692,0x |
| 921 | 1. El acuerdo de las voluntades de los sujetos concernidos en un contrato, si bien | Civil | 110175 | 159 | 99,9 % | 692,9x |
| 922 | 1. El artículo 5º inciso segundo de la Constitución de 1980, apli- | Penal | 121924 | 102 | 99,9 % | 1195,3x |
| 923 | 1. El case management en Estados Unidos | Procesal | 96699 | 143 | 99,9 % | 676,2x |
| 924 | 1. El derecho de acceso de las mujeres a la justicia es esencial para | Judicial | 93914 | 109 | 99,9 % | 861,6x |
| 925 | 1. El presente Estatuto será aplicable por igual a todos sin distinción alguna basada en el cargo oficial. En | Penal | 121924 | 114 | 99,9 % | 1069,5x |
| 926 | 1. El primer caso: Caso Van Oosterwijck contra Bélgica (1980) | Judicial | 87237 | 87 | 99,9 % | 1002,7x |
| 927 | 1. El tribunal firma la resolución. Se inicia el ciclo con la resolución | Judicial | 89450 | 89 | 99,9 % | 1005,1x |
| 928 | 1. En el momento del ingreso, se deberá consignar el número de los hijos | Penal | 194788 | 163 | 99,9 % | 1195,0x |
| 929 | 1. Encontrarse       La motivación no es el aborto, no obstante, lo más pro- | Familia | 95131 | 94 | 99,9 % | 1012,0x |
| 930 | 1. Encuesta Nacional de Clima Escolar en Chile 2016, realizada por | Judicial | 87237 | 79 | 99,9 % | 1104,3x |
| 931 | 1. Escuela Sindical (ID 583). Cumplimiento total. Se fusionaron las | Constitucional | 177323 | 119 | 99,9 % | 1490,1x |
| 932 | 1. Establece que los actos y documentos que han sido objeto de | Administrativo | 89720 | 100 | 99,9 % | 897,2x |
| 933 | 1. Establecer una jurisdicción especializada con competencia | Familia | 100107 | 80 | 99,9 % | 1251,3x |
| 934 | 1. Existir probabilidad y verosimilitud de que un derecho pueda | Familia | 100107 | 63 | 99,9 % | 1589,0x |
| 935 | 1. Fallos que acogen requerimiento | Penal | 211066 | 114 | 99,9 % | 1851,5x |
| 936 | 1. Fase de solicitud de información por vía administrativa: Confor- | Administrativo | 89720 | 114 | 99,9 % | 787,0x |
| 937 | 1. Función de las máximas de experiencia. Para Taruffo, las máximas | Judicial | 150341 | 165 | 99,9 % | 911,2x |
| 938 | 1. Incorporar a la Subsecretaría de Derechos Humanos y al Instituto | Constitucional | 177323 | 156 | 99,9 % | 1136,7x |
| 939 | 1. Incumplimiento de los deberes de dirección y supervisión. El | Constitucional | 112823 | 75 | 99,9 % | 1504,3x |
| 940 | 1. Informe 42/08 Admisibilidad Caso 12.502, Karen Atala e hijas | Judicial | 87237 | 71 | 99,9 % | 1228,7x |
| 941 | 1. Intervención del legislad r: como señala Brebbia, “El primer remedio y, tal vez el más | Civil | 110175 | 163 | 99,9 % | 675,9x |
| 942 | 1. La Corte podrá, con sujeción a lo dispuesto en el artículo 110, imponer a la persona declarada culpable | Penal | 121924 | 132 | 99,9 % | 923,7x |
| 943 | 1. La Declaración Universal de los Derechos Humanos (1948). El | Judicial | 87237 | 76 | 99,9 % | 1147,9x |
| 944 | 1. La adopción por los Estados Partes de medidas especiales de | Judicial | 89476 | 117 | 99,9 % | 764,8x |
| 945 | 1. La condición positiva y suspensiva que es física o moralmente imposible o concebida | Civil | 118177 | 127 | 99,9 % | 930,5x |
| 946 | 1. La crudeza y larga duración de la guerra contra el pueblo mapuche | Penal | 178516 | 93 | 99,9 % | 1919,5x |
| 947 | 1. La designación de una Ministra de la Excma. Corte Suprema | Judicial | 81476 | 96 | 99,9 % | 848,7x |
| 948 | 1. La familia es el elemento natural y fundamental de la sociedad y | Judicial | 89476 | 57 | 99,9 % | 1569,8x |
| 949 | 1. La identificación de la organización que presenta el proyecto y | Laboral | 100583 | 104 | 99,9 % | 967,1x |
| 950 | 1. La igualdad ante la ley e igual protección de la ley en el ejercicio | Judicial | 89476 | 85 | 99,9 % | 1052,7x |
| 951 | 1. La obligación que los actos y documentos que han sido objeto de | Administrativo | 89720 | 100 | 99,9 % | 897,2x |
| 952 | 1. La sentencia definitiva de primera instancia:25 «Cuando han trans- | Judicial | 89450 | 66 | 99,9 % | 1355,3x |
| 953 | 1. Landa, César. “De los derechos fundamentales de los grupos | Judicial | 87237 | 102 | 99,9 % | 855,3x |
| 954 | 1. Las fuentes de la obligación de fallar con perspectiva de género. Desde | Judicial | 150341 | 196 | 99,9 % | 767,0x |
| 955 | 1. Las leyes dictadas con posterioridad a la Novísima Recopilación, que era la más | Civil | 90056 | 128 | 99,9 % | 703,6x |
| 956 | 1. Las medidas de revisión y control de las personas, de sus efectos | Laboral | 113458 | 117 | 99,9 % | 969,7x |
| 957 | 1. Las medidas que se decretaron como cautelares y pueden | Familia | 100107 | 100 | 99,9 % | 1001,1x |
| 958 | 1. Las personas físicas o jurídicas, públicas o privadas, podrán llevar a cabo el tratamiento de imágenes a | Constitucional | 104063 | 83 | 99,9 % | 1253,8x |
| 959 | 1. Las resoluciones que, debiendo notificarse por cédula, lo han sido | Judicial | 89450 | 122 | 99,9 % | 733,2x |
| 960 | 1. Las restitutorias, con las que se busca obtener o bien la cosa mis- | Penal | 211066 | 135 | 99,9 % | 1563,5x |
| 961 | 1. Llevar de forma ordenada todos los libros de la secretaría, como | Judicial | 52128 | 75 | 99,9 % | 695,0x |
| 962 | 1. Lo esencial, lo que caracteriza al concepto de incumplimiento | Civil | 142015 | 85 | 99,9 % | 1670,8x |
| 963 | 1. Los Estados | Penal | 72395 | 107 | 99,9 % | 676,6x |
| 964 | 1. Los Estados Partes adoptarán todas las medidas adecuadas para | Judicial | 89476 | 104 | 99,9 % | 860,3x |
| 965 | 1. Los Estados Partes adoptarán todas las medidas apropiadas para | Judicial | 89476 | 97 | 99,9 % | 922,4x |
| 966 | 1. Los Estados Partes en esta Convención se comprometen a respetar los derechos y libertades reconocidos | Constitucional | 115835 | 157 | 99,9 % | 737,8x |
| 967 | 1. Los delitos a que se hace referencia en el artículo 4 se considerarán | Judicial | 78893 | 110 | 99,9 % | 717,2x |
| 968 | 1. Los empleadores podrán tratar las imágenes obtenidas a través de sistemas de cámaras o videocámaras | Constitucional | 104063 | 137 | 99,9 % | 759,6x |
| 969 | 1. Los gobiernos deberán asumir la responsabilidad de desarrollar, con | Judicial | 134465 | 83 | 99,9 % | 1620,1x |
| 970 | 1. Los riesgos atípicos. Según se ha visto, la información debe recaer | Civil | 142015 | 110 | 99,9 % | 1291,0x |
| 971 | 1. Macarena Sáez, abogada y profesora universitaria. Comentario | Judicial | 87237 | 75 | 99,9 % | 1163,2x |
| 972 | 1. Mecanismo para promover y coordinar la participación de la so- | Constitucional | 177323 | 163 | 99,9 % | 1087,9x |
| 973 | 1. Modelos normativos, lógicos o sintácticos. Los modelos normativos | Judicial | 150341 | 109 | 99,9 % | 1379,3x |
| 974 | 1. Muerte presunta: El artículo 81 numeral 2 del Código Civil dispo- | Judicial | 89450 | 131 | 99,9 % | 682,8x |
| 975 | 1. Mónica González Contró (Abogada, académica UNAM) | Judicial | 87237 | 57 | 99,9 % | 1530,5x |
| 976 | 1. No Discriminación de Género: el objetivo de este eje estratégico | Judicial | 81476 | 96 | 99,9 % | 848,7x |
| 977 | 1. No es necesaria la comparecencia ante la Corte de Apelaciones | Familia | 100107 | 74 | 99,9 % | 1352,8x |
| 978 | 1. No tenemos casos de acción afirmativa que el TC haya debido | Judicial | 81476 | 59 | 99,9 % | 1380,9x |
| 979 | 1. Normas constitucionales | Civil | 192585 | 150 | 99,9 % | 1283,9x |
| 980 | 1. Nota de prensa “Stonewall, la histórica noche en que los gays se | Judicial | 87237 | 85 | 99,9 % | 1026,3x |
| 981 | 1. Nuestro Derecho reconoce una estructura basada en el reconocimiento de la validez | Familia | 190697 | 162 | 99,9 % | 1177,1x |
| 982 | 1. Objeto | Procesal | 95124 | 70 | 99,9 % | 1358,9x |
| 983 | 1. Opinión Consultiva 24/17 de la Corte Interamericana de Derechos | Judicial | 87237 | 87 | 99,9 % | 1002,7x |
| 984 | 1. Oír la relación breve y sintética, del contenido de la demanda, la | Familia | 100107 | 113 | 99,9 % | 885,9x |
| 985 | 1. Política de Igualdad de Género y No Discriminación del Poder | Judicial | 87237 | 122 | 99,9 % | 715,1x |
| 986 | 1. Poseen dos jueces (bicéfalos), uno de los cuales cumple el rol de | Judicial | 52128 | 68 | 99,9 % | 766,6x |
| 987 | 1. Primero, por una razón de texto, esto es, que el artículo 4 inciso fi- | Penal | 194788 | 157 | 99,9 % | 1240,7x |
| 988 | 1. Priorizar, previa coordinación con las instituciones respectivas, la | Constitucional | 177323 | 122 | 99,9 % | 1453,5x |
| 989 | 1. Procesamiento de documentos, donde la máquina puede | Judicial | 83934 | 72 | 99,9 % | 1165,8x |
| 990 | 1. Procurar la mayor eficiencia del sistema de justicia producto de la | Judicial | 89450 | 88 | 99,9 % | 1016,5x |
| 991 | 1. Promoción y prevención | Judicial | 81476 | 85 | 99,9 % | 958,5x |
| 992 | 1. Promover la prevención de la tortura en el sector de salud: Creación | Constitucional | 177323 | 132 | 99,9 % | 1343,4x |
| 993 | 1. Propuestas metodológicas | Judicial | 87237 | 98 | 99,9 % | 890,2x |
| 994 | 1. Que el informe psicosocial de Gendarmería de Chile, elaborado en | Penal | 194788 | 118 | 99,9 % | 1650,7x |
| 995 | 1. Que en esta causa de la Reforma Procesal Penal, RIT 3345-2015, RUC | Penal | 194788 | 170 | 99,9 % | 1145,8x |
| 996 | 1. Que la Comisión recurrida rechazó el otorgamiento de la libertad | Penal | 194788 | 171 | 99,9 % | 1139,1x |
| 997 | 1. Que la medida esté expresamente contemplada en el reglamento de copropiedad del | Civil | 192585 | 171 | 99,9 % | 1126,2x |
| 998 | 1. Que mediante el Decreto 975 de 13 de agosto de 2008 del Ministerio | Judicial | 144656 | 171 | 99,9 % | 845,9x |
| 999 | 1. Que se condena a Jeremy, cédula nacional de identidad número | Penal | 194788 | 169 | 99,9 % | 1152,6x |
| 1000 | 1. Que se haya pronunciado una resolución en el expediente que no | Judicial | 89450 | 93 | 99,9 % | 961,8x |
| 1001 | 1. Reforma Procesal Penal: Integrada por funcionarios provenientes | Judicial | 89450 | 126 | 99,9 % | 709,9x |
| 1002 | 1. Relación de la demanda | Laboral | 71986 | 55 | 99,9 % | 1308,8x |
| 1003 | 1. Reparación celosa del mal causado o impedir sus ulteriores | Penal | 119528 | 111 | 99,9 % | 1076,8x |
| 1004 | 1. Respetar los derechos humanos, lo cual significa que han | Constitucional | 112823 | 76 | 99,9 % | 1484,5x |
| 1005 | 1. Resumen general del flujo del nuevo Servicio Mejor Niñez | Constitucional | 44292 | 62 | 99,9 % | 714,4x |
| 1006 | 1. Se deberá prestar atención adecuada a los procedimientos de ingreso | Penal | 194788 | 118 | 99,9 % | 1650,7x |
| 1007 | 1. Se oficie a Colegio Establecimiento Escuela, Comuna de Xxxxx, para informe respecto | Judicial | 79146 | 87 | 99,9 % | 909,7x |
| 1008 | 1. Se procede a incorporar mediante su lectura el acuerdo presentado por las partes, el cual | Judicial | 79146 | 110 | 99,9 % | 719,5x |
| 1009 | 1. Se sustituyó la sanción de internación en régimen semicerrado con | Penal | 86906 | 91 | 99,9 % | 955,0x |
| 1010 | 1. Si el afectado es un trabajador: la víctima, el sindicato al que | Laboral | 113458 | 79 | 99,9 % | 1436,2x |
| 1011 | 1. Si fallece el acreedor condicional, su derecho en germen se transmite a sus | Civil | 118177 | 172 | 99,9 % | 687,1x |
| 1012 | 1. Si la pena señalada al delito es una indivisible o un solo grado de otra | Penal | 194788 | 150 | 99,9 % | 1298,6x |
| 1013 | 1. Sistema Francés o del Régimen administrativo | Judicial | 105809 | 85 | 99,9 % | 1244,8x |
| 1014 | 1. Síndrome de la mujer maltratada y sus sesgos. En Estado Unidos | Judicial | 150341 | 183 | 99,9 % | 821,5x |
| 1015 | 1. Tener siempre presente el interés superior del niño, esto es, en todas las | Judicial | 81476 | 87 | 99,9 % | 936,5x |
| 1016 | 1. Tesis contraria a estimar que trabajadores remunerados a | Judicial | 79146 | 68 | 99,9 % | 1163,9x |
| 1017 | 1. Toda persona privada de libertad será tratada humanamente y con el | Penal | 194788 | 130 | 99,9 % | 1498,4x |
| 1018 | 1. Toda persona que se halle legalmente en el territorio de un Estado tiene derecho a circular por el mismo | Constitucional | 115835 | 159 | 99,9 % | 728,5x |
| 1019 | 1. Toda persona tiene derecho a la libertad de pensamiento y de | Judicial | 89476 | 96 | 99,9 % | 932,0x |
| 1020 | 1. Toda persona tiene derecho a que su causa sea oída equitativa, públicamente y | Judicial | 144656 | 174 | 99,9 % | 831,4x |
| 1021 | 1. Toda persona tiene derecho a ser oída, con las debidas garantías y | Constitucional | 177323 | 113 | 99,9 % | 1569,2x |
| 1022 | 1. Toda persona tiene derecho a un nivel de vida adecuado que le | Judicial | 89476 | 120 | 99,9 % | 745,6x |
| 1023 | 1. Toda persona tiene derecho a un recurso sencillo y rápido o a cual- | Judicial | 144656 | 146 | 99,9 % | 990,8x |
| 1024 | 1. Todos los Estados tienen la obligación de extraditar o juzgar a | Penal | 121924 | 67 | 99,9 % | 1819,8x |
| 1025 | 1. Usar un lenguaje no ofensivo y no discriminatorio para referirse | Constitucional | 177323 | 91 | 99,9 % | 1948,6x |
| 1026 | 1.1                  Corte Suprema | Judicial | 52128 | 52 | 99,9 % | 1002,5x |
| 1027 | 1.1              Concepto de | Administrativo | 89720 | 92 | 99,9 % | 975,2x |
| 1028 | 1.1              Regulación Orgánica | Procesal | 94881 | 84 | 99,9 % | 1129,5x |
| 1029 | 1.1           Breve reseña a la evolución del | Judicial | 64632 | 53 | 99,9 % | 1219,5x |
| 1030 | 1.1           Concepto y | Familia | 65085 | 44 | 99,9 % | 1479,2x |
| 1031 | 1.1     Definición y | Laboral | 71986 | 54 | 99,9 % | 1333,1x |
| 1032 | 1.1     Definición, facultades | Judicial | 44331 | 55 | 99,9 % | 806,0x |
| 1033 | 1.1     Principio de juridicidad administrativa | Judicial | 105809 | 75 | 99,9 % | 1410,8x |
| 1034 | 1.1. De la unidimensionalidad a la tridimensionalidad de objetivos del proceso civil | Procesal | 96699 | 70 | 99,9 % | 1381,4x |
| 1035 | 1.1. Gastos correspondientes a las expensas ordinarias: serán de cargo de la sociedad | Familia | 62470 | 74 | 99,9 % | 844,2x |
| 1036 | 1.1. Presunción de dominio: establece el art. 1739, inc. 1º una presunción de dominio | Familia | 136567 | 171 | 99,9 % | 798,6x |
| 1037 | 1.1. Sobre la inexistencia de un derecho a inmigrar | Constitucional | 115835 | 107 | 99,9 % | 1082,6x |
| 1038 | 1.1. Sobre las causas posibles de la migración. Migración voluntaria y forzada | Constitucional | 115835 | 141 | 99,9 % | 821,5x |
| 1039 | 1.1.1 Concepto | Penal | 121924 | 96 | 99,9 % | 1270,0x |
| 1040 | 1.1.1 Criminalidad organizada y delincuencia empresarial | Penal | 119528 | 119 | 99,9 % | 1004,4x |
| 1041 | 1.1.1 El registro de los actos procesales | Judicial | 83934 | 94 | 99,9 % | 892,9x |
| 1042 | 1.1.1 La dimensión normativa y | Judicial | 134465 | 85 | 99,9 % | 1581,9x |
| 1043 | 1.1.1 La sexualidad en las manifestaciones | Judicial | 93914 | 94 | 99,9 % | 999,1x |
| 1044 | 1.1.1 Nociones previas | Administrativo | 89720 | 111 | 99,9 % | 808,3x |
| 1045 | 1.1.1 Oralidad | Familia | 100107 | 92 | 99,9 % | 1088,1x |
| 1046 | 1.1.1 Principio protector | Laboral | 100583 | 96 | 99,9 % | 1047,7x |
| 1047 | 1.1.1 Violencia como un problema de salud pública | Familia | 95131 | 81 | 99,9 % | 1174,5x |
| 1048 | 1.1.1.1 La regla in dubio pro operario | Laboral | 100583 | 85 | 99,9 % | 1183,3x |
| 1049 | 1.1.1.2 La regla de la norma favorable | Laboral | 100583 | 98 | 99,9 % | 1026,4x |
| 1050 | 1.1.1.3 La regla de la condición más beneficiosa | Laboral | 100583 | 113 | 99,9 % | 890,1x |
| 1051 | 1.1.2 Aspectos psicosociales de la violencia | Familia | 95131 | 97 | 99,9 % | 980,7x |
| 1052 | 1.1.2 Cambio tecnológico vinculado | Judicial | 83934 | 83 | 99,9 % | 1011,3x |
| 1053 | 1.1.2 Como se interpreta el Convenio | Judicial | 134465 | 94 | 99,9 % | 1430,5x |
| 1054 | 1.1.2 Disposiciones legales | Procesal | 94881 | 120 | 99,9 % | 790,7x |
| 1055 | 1.1.2 Distinción entre la criminalidad empresarial | Penal | 119528 | 88 | 99,9 % | 1358,3x |
| 1056 | 1.1.2 Importancia de la transparencia | Administrativo | 89720 | 84 | 99,9 % | 1068,1x |
| 1057 | 1.1.2 La mirada desde los discursos científicos | Judicial | 93914 | 94 | 99,9 % | 999,1x |
| 1058 | 1.1.2 Objetivos | Penal | 121924 | 100 | 99,9 % | 1219,2x |
| 1059 | 1.1.2 Principio de la irrenunciabilidad | Laboral | 100583 | 65 | 99,9 % | 1547,4x |
| 1060 | 1.1.2.1 La garantía de satisfacción6 | Laboral | 100583 | 105 | 99,9 % | 957,9x |
| 1061 | 1.1.2.2 La garantía de negociación7 | Laboral | 100583 | 102 | 99,9 % | 986,1x |
| 1062 | 1.1.3 Aspectos psicosociales de la violencia | Familia | 95131 | 52 | 99,9 % | 1829,4x |
| 1063 | 1.1.3 Características del derecho informático | Judicial | 96536 | 98 | 99,9 % | 985,1x |
| 1064 | 1.1.3 Delito económico y criminalidad empresarial | Penal | 119528 | 107 | 99,9 % | 1117,1x |
| 1065 | 1.1.3 Inmediación | Familia | 100107 | 65 | 99,9 % | 1540,1x |
| 1066 | 1.1.3 La Ley N° 19.968 y la reforma a la justicia de familia | Judicial | 83934 | 102 | 99,9 % | 822,9x |
| 1067 | 1.1.3 La cláusula de flexibilidad | Judicial | 134465 | 72 | 99,9 % | 1867,6x |
| 1068 | 1.1.3 La transparencia como concepto | Administrativo | 89720 | 97 | 99,9 % | 924,9x |
| 1069 | 1.1.3 Principio de continuidad de la relación laboral | Laboral | 100583 | 101 | 99,9 % | 995,9x |
| 1070 | 1.1.3.4 Modelos explicativos de la violencia | Familia | 95131 | 88 | 99,9 % | 1081,0x |
| 1071 | 1.1.3.5 Modelos explicativos de la violencia | Familia | 95131 | 94 | 99,9 % | 1012,0x |
| 1072 | 1.1.3.7 Modelos explicativos de la violencia | Familia | 95131 | 84 | 99,9 % | 1132,5x |
| 1073 | 1.1.4 Desformalización | Familia | 100107 | 98 | 99,9 % | 1021,5x |
| 1074 | 1.1.4 La informática y las telecomunicaciones | Judicial | 96536 | 83 | 99,9 % | 1163,1x |
| 1075 | 1.1.4 Otros instrumentos de protección de los | Judicial | 134465 | 87 | 99,9 % | 1545,6x |
| 1076 | 1.1.4 Principio de la primacía de la realidad | Laboral | 100583 | 135 | 99,9 % | 745,1x |
| 1077 | 1.1.4.1 Principio de juez natural | Penal | 57066 | 74 | 99,9 % | 771,2x |
| 1078 | 1.1.4.1 Sistema de Naciones Unidas | Judicial | 134465 | 91 | 99,9 % | 1477,6x |
| 1079 | 1.1.4.2 El sistema interamericano | Judicial | 134465 | 88 | 99,9 % | 1528,0x |
| 1080 | 1.1.4.6 Protección a la víctima | Penal | 57066 | 65 | 99,9 % | 877,9x |
| 1081 | 1.1.5 Acta N° 98-2009 | Judicial | 83934 | 89 | 99,9 % | 943,1x |
| 1082 | 1.1.5 Actuación de oficio | Familia | 100107 | 122 | 99,9 % | 820,5x |
| 1083 | 1.1.6 Colaboración | Familia | 100107 | 110 | 99,9 % | 910,1x |
| 1084 | 1.1.6 Reforma a la justicia laboral | Judicial | 83934 | 93 | 99,9 % | 902,5x |
| 1085 | 1.1.7 Publicidad/Protección a la intimidad | Familia | 100107 | 123 | 99,9 % | 813,9x |
| 1086 | 1.1.7 Tramitación digital en materia civil | Judicial | 83934 | 105 | 99,9 % | 799,4x |
| 1087 | 1.1.7.1 Expediente electrónico | Judicial | 83934 | 100 | 99,9 % | 839,3x |
| 1088 | 1.1.7.2 Firma electrónica | Judicial | 83934 | 101 | 99,9 % | 831,0x |
| 1089 | 1.1.8 Contradicción | Familia | 100107 | 94 | 99,9 % | 1065,0x |
| 1090 | 1.12     Corte Suprema, 22 de mayo de 2014,“Consejo de Pueblos | Judicial | 134465 | 75 | 99,9 % | 1792,9x |
| 1091 | 1.14     Corte de Apelaciones de Temuco, 16 de noviembre de | Judicial | 134465 | 109 | 99,9 % | 1233,6x |
| 1092 | 1.2                 Tramitación | Judicial | 83934 | 42 | 99,9 % | 1998,4x |
| 1093 | 1.2           La óptica actual de | Familia | 65192 | 61 | 99,9 % | 1068,7x |
| 1094 | 1.2           Ley N° 20.720 sobre Reorganización y liquidación | Judicial | 64632 | 57 | 99,9 % | 1133,9x |
| 1095 | 1.2          Procedimientos | Judicial | 39447 | 41 | 99,9 % | 962,1x |
| 1096 | 1.2     Derechos fundamentales protegidos | Laboral | 100583 | 67 | 99,9 % | 1501,2x |
| 1097 | 1.2 Entrega de información general de utilidad para el | Judicial | 52128 | 62 | 99,9 % | 840,8x |
| 1098 | 1.2. Derecho personal y obligación. 1.3. Definición de obligación. 1.4. Elementos de | Civil | 118177 | 110 | 99,9 % | 1074,3x |
| 1099 | 1.2. Educación | Constitucional | 115835 | 88 | 99,9 % | 1316,3x |
| 1100 | 1.2. Estadísticas a nivel mundial | Constitucional | 115835 | 123 | 99,9 % | 941,7x |
| 1101 | 1.2. Nuestra propuesta conceptual | Procesal | 96699 | 102 | 99,9 % | 948,0x |
| 1102 | 1.2. Por falta de gravedad del delito para tener la entidad | Constitucional | 115835 | 140 | 99,9 % | 827,4x |
| 1103 | 1.2. Presunción en orden a que los bienes adquiridos a título oneroso se han adquirido | Familia | 136567 | 178 | 99,9 % | 767,2x |
| 1104 | 1.2.1 Bhopal (Union Carbide) | Constitucional | 112823 | 98 | 99,9 % | 1151,3x |
| 1105 | 1.2.1 Convenios de Ginebra de 1949 | Penal | 121924 | 84 | 99,9 % | 1451,5x |
| 1106 | 1.2.1 El concepto de identidad y cómo se construye | Judicial | 87237 | 124 | 99,9 % | 703,5x |
| 1107 | 1.2.1 El contexto organizacional y su | Penal | 119528 | 93 | 99,9 % | 1285,2x |
| 1108 | 1.2.1 El fallo del Tribunal Constitucional de 2000 | Judicial | 134465 | 100 | 99,9 % | 1344,7x |
| 1109 | 1.2.1 Igualdad y no discriminación en los | Judicial | 81476 | 88 | 99,9 % | 925,9x |
| 1110 | 1.2.1 La ponderación judicial: el dilema | Laboral | 113458 | 93 | 99,9 % | 1220,0x |
| 1111 | 1.2.1 La revocación | Judicial | 105809 | 115 | 99,9 % | 920,1x |
| 1112 | 1.2.1 La variedad infinita de la diversidad sexual | Judicial | 93914 | 102 | 99,9 % | 920,7x |
| 1113 | 1.2.1 Principios | Procesal | 94881 | 104 | 99,9 % | 912,3x |
| 1114 | 1.2.1 Proyecciones del principio de transparencia | Administrativo | 89720 | 104 | 99,9 % | 862,7x |
| 1115 | 1.2.1 Sexo: En un sentido estricto, el término “sexo” se refiere “a | Judicial | 89476 | 104 | 99,9 % | 860,3x |
| 1116 | 1.2.1 Violencia y agresividad | Familia | 95131 | 74 | 99,9 % | 1285,6x |
| 1117 | 1.2.1. Etapas del desarrollo del lenguaje | Judicial | 79146 | 78 | 99,9 % | 1014,7x |
| 1118 | 1.2.1.1 Personas intersex: Desde la perspectiva del sexo, además | Judicial | 89476 | 101 | 99,9 % | 885,9x |
| 1119 | 1.2.2 Análisis de antecedentes en instrumentos | Administrativo | 89720 | 79 | 99,9 % | 1135,7x |
| 1120 | 1.2.2 Carta de Derechos de las Personas | Familia | 100107 | 92 | 99,9 % | 1088,1x |
| 1121 | 1.2.2 Caso Wiwa (Ogoniland) | Constitucional | 112823 | 80 | 99,9 % | 1410,3x |
| 1122 | 1.2.2 Desarrollo legislativo           ulterior y aplicación     directa | Judicial | 134465 | 132 | 99,9 % | 1018,7x |
| 1123 | 1.2.2 El sexo de las personas y sus distintas expresiones | Judicial | 93914 | 104 | 99,9 % | 903,0x |
| 1124 | 1.2.2 Género: La diferencia entre sexo y género radica en que el | Judicial | 89476 | 110 | 99,9 % | 813,4x |
| 1125 | 1.2.2 Igualdad y no discriminación en los instrumentos | Judicial | 81476 | 91 | 99,9 % | 895,3x |
| 1126 | 1.2.2 La autonomía de la voluntad | Judicial | 96536 | 81 | 99,9 % | 1191,8x |
| 1127 | 1.2.2 La crítica a la eficacia horizontal | Laboral | 113458 | 111 | 99,9 % | 1022,1x |
| 1128 | 1.2.2 La invalidación | Judicial | 105809 | 117 | 99,9 % | 904,4x |
| 1129 | 1.2.2 Protocolos adicionales | Penal | 121924 | 80 | 99,9 % | 1524,0x |
| 1130 | 1.2.2 Signo lingüístico | Judicial | 79146 | 91 | 99,9 % | 869,7x |
| 1131 | 1.2.2.1 Argumento histórico | Laboral | 113458 | 106 | 99,9 % | 1070,4x |
| 1132 | 1.2.2.1 Expediente digital | Judicial | 83934 | 85 | 99,9 % | 987,5x |
| 1133 | 1.2.2.2 Supuesta objetividad del legislador | Laboral | 113458 | 102 | 99,9 % | 1112,3x |
| 1134 | 1.2.2.3 Afectación de la autonomía privada | Laboral | 113458 | 98 | 99,9 % | 1157,7x |
| 1135 | 1.2.2.4 Aumento de la discrecionalidad judicial | Laboral | 113458 | 74 | 99,9 % | 1533,2x |
| 1136 | 1.2.2.4 Interconexiones | Judicial | 83934 | 85 | 99,9 % | 987,5x |
| 1137 | 1.2.2.5 Transparencia y acceso al expediente | Judicial | 83934 | 91 | 99,9 % | 922,4x |
| 1138 | 1.2.2.6 Notificaciones electrónicas | Judicial | 83934 | 98 | 99,9 % | 856,5x |
| 1139 | 1.2.2.7 Disminución de los costos asociados | Judicial | 83934 | 100 | 99,9 % | 839,3x |
| 1140 | 1.2.2.8 Disminución de costos y | Judicial | 83934 | 55 | 99,9 % | 1526,1x |
| 1141 | 1.2.3   Análisis de antecedentes a la dictación de la Ley Nº 20.285: Ley Nº 20.050 de Reforma | Administrativo | 89720 | 79 | 99,9 % | 1135,7x |
| 1142 | 1.2.3 Análisis de antecedentes a la dictación de la Ley | Administrativo | 89720 | 94 | 99,9 % | 954,5x |
| 1143 | 1.2.3 El aumento de la oportunidad delictiva | Penal | 119528 | 83 | 99,9 % | 1440,1x |
| 1144 | 1.2.3 El principio de buena fe y sus manifestaciones | Judicial | 96536 | 91 | 99,9 % | 1060,8x |
| 1145 | 1.2.3 Igualdad y no discriminación en los instrumentos | Judicial | 81476 | 102 | 99,9 % | 798,8x |
| 1146 | 1.2.3 Implementación de la ley | Judicial | 83934 | 98 | 99,9 % | 856,5x |
| 1147 | 1.2.3 La orientación sexual | Judicial | 93914 | 94 | 99,9 % | 999,1x |
| 1148 | 1.2.3 Lengua | Judicial | 79146 | 97 | 99,9 % | 815,9x |
| 1149 | 1.2.3 Orientación sexual: La orientación sexual de una persona es | Judicial | 89476 | 111 | 99,9 % | 806,1x |
| 1150 | 1.2.3 Otras normas especiales | Penal | 121924 | 89 | 99,9 % | 1369,9x |
| 1151 | 1.2.3 Protocolo Iberoamericano de Actuación Judicial | Familia | 100107 | 92 | 99,9 % | 1088,1x |
| 1152 | 1.2.3. La medida de expulsión | Constitucional | 115835 | 128 | 99,9 % | 905,0x |
| 1153 | 1.2.3.1 Dialecto | Judicial | 79146 | 91 | 99,9 % | 869,7x |
| 1154 | 1.2.3.1 Dimensión colectiva | Judicial | 134465 | 94 | 99,9 % | 1430,5x |
| 1155 | 1.2.3.1 En el caso de los NNA | Familia | 100107 | 94 | 99,9 % | 1065,0x |
| 1156 | 1.2.3.1 Heterosexualidad: Hace referencia a la capacidad de una | Judicial | 89476 | 81 | 99,9 % | 1104,6x |
| 1157 | 1.2.3.10 Fortalecimiento de la        plataforma     tecnológica | Judicial | 83934 | 105 | 99,9 % | 799,4x |
| 1158 | 1.2.3.2 Ajustes a los sistemas de tramitación | Judicial | 83934 | 109 | 99,9 % | 770,0x |
| 1159 | 1.2.3.2 En el caso de personas, comunidades y pueblos | Familia | 100107 | 79 | 99,9 % | 1267,2x |
| 1160 | 1.2.3.2 Homosexualidad: Hace referencia a la capacidad de cada | Judicial | 89476 | 96 | 99,9 % | 932,0x |
| 1161 | 1.2.3.2 Jerga y argot | Judicial | 79146 | 63 | 99,9 % | 1256,3x |
| 1162 | 1.2.3.3 En el caso de personas con discapacidad | Familia | 100107 | 100 | 99,9 % | 1001,1x |
| 1163 | 1.2.3.3 Reglamentación interna | Judicial | 83934 | 111 | 99,9 % | 756,2x |
| 1164 | 1.2.3.6 Nuevas aplicaciones | Judicial | 83934 | 85 | 99,9 % | 987,5x |
| 1165 | 1.2.3.7 Estado diario | Judicial | 83934 | 58 | 99,9 % | 1447,1x |
| 1166 | 1.2.3.8 Firma electrónica | Judicial | 83934 | 88 | 99,9 % | 953,8x |
| 1167 | 1.2.3.9 Notificación electrónica | Judicial | 83934 | 101 | 99,9 % | 831,0x |
| 1168 | 1.2.4 Dimensión individual | Judicial | 134465 | 100 | 99,9 % | 1344,7x |
| 1169 | 1.2.4 El habla | Judicial | 79146 | 104 | 99,9 % | 761,0x |
| 1170 | 1.2.4 Fundamentos para innovar en la | Judicial | 83934 | 92 | 99,9 % | 912,3x |
| 1171 | 1.2.4 Identidad de género | Judicial | 93914 | 75 | 99,9 % | 1252,2x |
| 1172 | 1.2.4 La igualdad ante la ley como principio base | Judicial | 96536 | 111 | 99,9 % | 869,7x |
| 1173 | 1.2.4 Protocolo de Actuación Judicial | Familia | 100107 | 93 | 99,9 % | 1076,4x |
| 1174 | 1.2.4 Resolución 1/2018 Comisión Interamericana de | Administrativo | 89720 | 100 | 99,9 % | 897,2x |
| 1175 | 1.2.4. Derechos de las personas migrantes | Constitucional | 115835 | 59 | 99,9 % | 1963,3x |
| 1176 | 1.2.4.1 Incremento sostenido del ingreso de causas | Judicial | 83934 | 109 | 99,9 % | 770,0x |
| 1177 | 1.2.4.2 Aumento del presupuesto PJUD | Judicial | 83934 | 104 | 99,9 % | 807,1x |
| 1178 | 1.2.4.2 Transexualismo: Las personas transexuales se sienten y | Judicial | 89476 | 96 | 99,9 % | 932,0x |
| 1179 | 1.2.4.3 Cobertura tecnológica en Chile | Judicial | 83934 | 109 | 99,9 % | 770,0x |
| 1180 | 1.2.4.4 Prospección y experiencia internacional | Judicial | 83934 | 101 | 99,9 % | 831,0x |
| 1181 | 1.2.4.5 Mayor disponibilidad tecnológica | Judicial | 83934 | 100 | 99,9 % | 839,3x |
| 1182 | 1.2.5   Reconocimiento jurisprudencial en el Tribunal Constitucional, Consejo para la Transparencia | Administrativo | 89720 | 55 | 99,9 % | 1631,3x |
| 1183 | 1.2.5 Derechos específicos | Familia | 100107 | 109 | 99,9 % | 918,4x |
| 1184 | 1.2.5 La neutralidad tecnológica: equivalencia | Judicial | 96536 | 76 | 99,9 % | 1270,2x |
| 1185 | 1.2.5 Los diferentes tipos de lenguaje | Judicial | 79146 | 106 | 99,9 % | 746,7x |
| 1186 | 1.2.5 Pertenencia y autoidentificación | Judicial | 134465 | 111 | 99,9 % | 1211,4x |
| 1187 | 1.2.5 Reconocimiento jurisprudencial en el Tribunal | Administrativo | 89720 | 84 | 99,9 % | 1068,1x |
| 1188 | 1.2.5.1 Principio de protección del cónyuge más débil | Familia | 100107 | 119 | 99,9 % | 841,2x |
| 1189 | 1.2.5.1. Niñez migrante | Constitucional | 115835 | 128 | 99,9 % | 905,0x |
| 1190 | 1.2.5.2 Principio de prevalencia del interés superior del NNA | Familia | 100107 | 114 | 99,9 % | 878,1x |
| 1191 | 1.2.5.2. Víctimas de trata o tráfico de personas | Constitucional | 115835 | 172 | 99,9 % | 673,5x |
| 1192 | 1.2.6 Niveles de lenguaje: formal, coloquial y vulgar | Judicial | 79146 | 93 | 99,9 % | 851,0x |
| 1193 | 1.2.8 Lenguaje denotativo y lenguaje connotativo | Judicial | 79146 | 96 | 99,9 % | 824,4x |
| 1194 | 1.3                  Tribunales de | Judicial | 52128 | 55 | 99,9 % | 947,8x |
| 1195 | 1.3         Sistematización y | Familia | 65192 | 50 | 99,9 % | 1303,8x |
| 1196 | 1.3     La nueva justicia concursal en cifras, a | Judicial | 64632 | 59 | 99,9 % | 1095,5x |
| 1197 | 1.3     Principio de impugnabilidad de | Judicial | 105809 | 54 | 99,9 % | 1959,4x |
| 1198 | 1.3     Tipologías y/o manifestaciones de la | Familia | 95131 | 52 | 99,9 % | 1829,4x |
| 1199 | 1.3 Presentación de aspectos administrativos del | Judicial | 52128 | 61 | 99,9 % | 854,6x |
| 1200 | 1.3.1 Acumulación necesaria | Familia | 100107 | 78 | 99,9 % | 1283,4x |
| 1201 | 1.3.1 Antecedentes generales de la sociedad de | Judicial | 96536 | 97 | 99,9 % | 995,2x |
| 1202 | 1.3.1 El concepto de identidad | Judicial | 93914 | 109 | 99,9 % | 861,6x |
| 1203 | 1.3.1 Impugnación mediante recursos administrativos | Judicial | 105809 | 120 | 99,9 % | 881,7x |
| 1204 | 1.3.1 Presentación | Civil | 142015 | 101 | 99,9 % | 1406,1x |
| 1205 | 1.3.1 Principios de los Convenios de | Penal | 121924 | 91 | 99,9 % | 1339,8x |
| 1206 | 1.3.1 Secretarios | Procesal | 94881 | 80 | 99,9 % | 1186,0x |
| 1207 | 1.3.1.1 Artículo primero: imperativo de civilización | Penal | 121924 | 68 | 99,9 % | 1793,0x |
| 1208 | 1.3.1.1 La información como eje central de la sociedad | Judicial | 96536 | 105 | 99,9 % | 919,4x |
| 1209 | 1.3.1.1 La supuesta ineficacia de la | Penal | 119528 | 74 | 99,9 % | 1615,2x |
| 1210 | 1.3.1.1 Violencia física | Familia | 95131 | 104 | 99,9 % | 914,7x |
| 1211 | 1.3.1.2 Artículo segundo: principio de reciprocidad | Penal | 121924 | 104 | 99,9 % | 1172,3x |
| 1212 | 1.3.1.2 Convergencia y digitalización | Judicial | 96536 | 59 | 99,9 % | 1636,2x |
| 1213 | 1.3.1.2 El refuerzo disuasivo a través de la | Penal | 119528 | 87 | 99,9 % | 1373,9x |
| 1214 | 1.3.1.3 Artículo tercero: principio de humanidad | Penal | 121924 | 92 | 99,9 % | 1325,3x |
| 1215 | 1.3.1.3 Desmaterialización aparente | Judicial | 96536 | 101 | 99,9 % | 955,8x |
| 1216 | 1.3.1.3 La función de fomento de la autorregulación | Penal | 119528 | 87 | 99,9 % | 1373,9x |
| 1217 | 1.3.1.3 Violencia sexual | Familia | 95131 | 91 | 99,9 % | 1045,4x |
| 1218 | 1.3.1.4 Artículo octavo: control de | Penal | 121924 | 67 | 99,9 % | 1819,8x |
| 1219 | 1.3.1.4 Eliminación de fronteras y límites difusos | Judicial | 96536 | 89 | 99,9 % | 1084,7x |
| 1220 | 1.3.1.5 Artículo 11: conciliación facultativa | Penal | 121924 | 83 | 99,9 % | 1469,0x |
| 1221 | 1.3.1.5 Globalización | Judicial | 96536 | 100 | 99,9 % | 965,4x |
| 1222 | 1.3.1.5 Negligencia o abandono | Familia | 95131 | 102 | 99,9 % | 932,7x |
| 1223 | 1.3.1.6 Abuso de la vivienda de la persona mayor | Familia | 95131 | 117 | 99,9 % | 813,1x |
| 1224 | 1.3.1.6 Nuevo orden social | Judicial | 96536 | 98 | 99,9 % | 985,1x |
| 1225 | 1.3.1.6 Prohibición de represalias | Penal | 121924 | 66 | 99,9 % | 1847,3x |
| 1226 | 1.3.1.7 Modificación de los sistemas productivos | Judicial | 96536 | 80 | 99,9 % | 1206,7x |
| 1227 | 1.3.1.7 Universalidad de la represión | Penal | 121924 | 102 | 99,9 % | 1195,3x |
| 1228 | 1.3.1.8 Modificación de los esquemas | Judicial | 96536 | 88 | 99,9 % | 1097,0x |
| 1229 | 1.3.1.9 Modificaciones en la organización del trabajo | Judicial | 96536 | 88 | 99,9 % | 1097,0x |
| 1230 | 1.3.10 Incumplimiento del deber de | Civil | 142015 | 117 | 99,9 % | 1213,8x |
| 1231 | 1.3.10 Nulidad | Familia | 100107 | 76 | 99,9 % | 1317,2x |
| 1232 | 1.3.11 Los incidentes | Familia | 100107 | 114 | 99,9 % | 878,1x |
| 1233 | 1.3.11.1 Generalidades | Civil | 142015 | 100 | 99,9 % | 1420,2x |
| 1234 | 1.3.12 Facultades del juez o la jueza en la audiencia | Familia | 100107 | 145 | 99,9 % | 690,4x |
| 1235 | 1.3.13 Normas supletorias | Familia | 100107 | 101 | 99,9 % | 991,2x |
| 1236 | 1.3.2 Administradores de los tribunales | Procesal | 94881 | 110 | 99,9 % | 862,6x |
| 1237 | 1.3.2 Comparecencia en juicio | Familia | 100107 | 89 | 99,9 % | 1124,8x |
| 1238 | 1.3.2 El sexo de las personas y sus distintas expresiones | Judicial | 87237 | 96 | 99,9 % | 908,7x |
| 1239 | 1.3.2 Impugnación ante la Contraloría | Judicial | 105809 | 120 | 99,9 % | 881,7x |
| 1240 | 1.3.2 La diversidad en la identidad de género | Judicial | 93914 | 120 | 99,9 % | 782,6x |
| 1241 | 1.3.2 La información previa como | Civil | 142015 | 106 | 99,9 % | 1339,8x |
| 1242 | 1.3.2 Los sujetos pasivos, víctimas/ | Familia | 95131 | 85 | 99,9 % | 1119,2x |
| 1243 | 1.3.2 Principios fundamentales de la Cruz Roja | Penal | 121924 | 105 | 99,9 % | 1161,2x |
| 1244 | 1.3.2 Servicio universal de | Judicial | 96536 | 74 | 99,9 % | 1304,5x |
| 1245 | 1.3.2.1 Conceptos de servicio y acceso | Judicial | 96536 | 81 | 99,9 % | 1191,8x |
| 1246 | 1.3.2.1 Humanidad | Penal | 121924 | 89 | 99,9 % | 1369,9x |
| 1247 | 1.3.2.1 RPPJ y aumento de la conciencia social respecto a | Penal | 119528 | 96 | 99,9 % | 1245,1x |
| 1248 | 1.3.2.1 Violencia ejercida contra la mujer | Familia | 95131 | 54 | 99,9 % | 1761,7x |
| 1249 | 1.3.2.2 Igualdad o no discriminación | Penal | 121924 | 98 | 99,9 % | 1244,1x |
| 1250 | 1.3.2.2 Normativa internacional | Judicial | 96536 | 83 | 99,9 % | 1163,1x |
| 1251 | 1.3.2.2 Reconocimiento de responsabilidad autónoma | Penal | 119528 | 92 | 99,9 % | 1299,2x |
| 1252 | 1.3.2.3 Normativa nacional | Judicial | 96536 | 96 | 99,9 % | 1005,6x |
| 1253 | 1.3.2.4 Tipos de servicios de telecomunicaciones | Judicial | 96536 | 97 | 99,9 % | 995,2x |
| 1254 | 1.3.2.4 Violencia hacia las personas con discapacidad | Familia | 95131 | 76 | 99,9 % | 1251,7x |
| 1255 | 1.3.2.5 Independencia | Penal | 121924 | 105 | 99,9 % | 1161,2x |
| 1256 | 1.3.2.6 Universalidad | Penal | 121924 | 94 | 99,9 % | 1297,1x |
| 1257 | 1.3.3 Comparecencia personal a las | Familia | 100107 | 109 | 99,9 % | 918,4x |
| 1258 | 1.3.3 Consejos Técnicos | Procesal | 94881 | 119 | 99,9 % | 797,3x |
| 1259 | 1.3.3 El consentimiento informado | Civil | 142015 | 93 | 99,9 % | 1527,0x |
| 1260 | 1.3.3 Impugnación mediante acciones | Judicial | 105809 | 104 | 99,9 % | 1017,4x |
| 1261 | 1.3.3 La orientación sexual | Judicial | 87237 | 109 | 99,9 % | 800,3x |
| 1262 | 1.3.3.1 Expresión de género | Judicial | 93914 | 113 | 99,9 % | 831,1x |
| 1263 | 1.3.3.2 Identidad de género y orientación sexual | Judicial | 93914 | 91 | 99,9 % | 1032,0x |
| 1264 | 1.3.3.3 Identidad de género y disforia de género | Judicial | 93914 | 106 | 99,9 % | 886,0x |
| 1265 | 1.3.3.4 Cisnormatividad | Judicial | 93914 | 111 | 99,9 % | 846,1x |
| 1266 | 1.3.4 Debida representación de NNA e incapaces | Familia | 100107 | 97 | 99,9 % | 1032,0x |
| 1267 | 1.3.4 Incompatibilidad entre las vías de | Judicial | 105809 | 71 | 99,9 % | 1490,3x |
| 1268 | 1.3.4 La identidad de género | Judicial | 87237 | 91 | 99,9 % | 958,6x |
| 1269 | 1.3.4.2 Identidad de género y orientación sexual | Judicial | 87237 | 102 | 99,9 % | 855,3x |
| 1270 | 1.3.5 El deber de informar aspectos distintos | Civil | 142015 | 100 | 99,9 % | 1420,2x |
| 1271 | 1.3.5 Interrupción del plazo del recurso jurisdiccional | Judicial | 105809 | 145 | 99,9 % | 729,7x |
| 1272 | 1.3.5 Suspensión convencional de la audiencia | Familia | 100107 | 117 | 99,9 % | 855,6x |
| 1273 | 1.3.6 Abandono del procedimiento | Familia | 100107 | 119 | 99,9 % | 841,2x |
| 1274 | 1.3.6 Formalidades del deber de información | Civil | 142015 | 111 | 99,9 % | 1279,4x |
| 1275 | 1.3.7 Límites al deber de información | Civil | 142015 | 97 | 99,9 % | 1464,1x |
| 1276 | 1.3.7 Potestad cautelar | Familia | 100107 | 128 | 99,9 % | 782,1x |
| 1277 | 1.3.8 Los límites al consentimiento informado | Civil | 142015 | 111 | 99,9 % | 1279,4x |
| 1278 | 1.3.8 Notificaciones | Familia | 100107 | 104 | 99,9 % | 962,6x |
| 1279 | 1.3.9 Causalidad hipotética y | Civil | 142015 | 93 | 99,9 % | 1527,0x |
| 1280 | 1.3.9 Competencia territorial | Familia | 100107 | 118 | 99,9 % | 848,4x |
| 1281 | 1.4   Unidades de los Juzgados | Judicial | 39447 | 50 | 99,9 % | 788,9x |
| 1282 | 1.4.1 Conflicto armado internacional | Penal | 121924 | 97 | 99,9 % | 1256,9x |
| 1283 | 1.4.1 De los estudios de mujeres a los estudios | Judicial | 87237 | 102 | 99,9 % | 855,3x |
| 1284 | 1.4.1 La doctrina de la entidad empresarial | Constitucional | 112823 | 110 | 99,9 % | 1025,7x |
| 1285 | 1.4.1 La separación entre las funciones | Procesal | 94881 | 65 | 99,9 % | 1459,7x |
| 1286 | 1.4.1 Raza y color | Judicial | 81476 | 59 | 99,9 % | 1380,9x |
| 1287 | 1.4.1 Regla general en materia de recursos | Familia | 100107 | 119 | 99,9 % | 841,2x |
| 1288 | 1.4.1.3 Diferentes tipos de feminismos | Judicial | 87237 | 94 | 99,9 % | 928,1x |
| 1289 | 1.4.1.7 Órdenes, regímenes e ideologías de género | Judicial | 87237 | 96 | 99,9 % | 908,7x |
| 1290 | 1.4.2 El Comité de Jueces y el presidente(a) | Procesal | 94881 | 101 | 99,9 % | 939,4x |
| 1291 | 1.4.2 Iniciativas legales relativas a | Constitucional | 112823 | 79 | 99,9 % | 1428,1x |
| 1292 | 1.4.2 La lex artis médica | Civil | 142015 | 92 | 99,9 % | 1543,6x |
| 1293 | 1.4.2 Los derechos fundamentales reconocidos | Judicial | 96536 | 88 | 99,9 % | 1097,0x |
| 1294 | 1.4.2 Origen nacional | Judicial | 81476 | 96 | 99,9 % | 848,7x |
| 1295 | 1.4.2 Perspectivas críticas del género | Judicial | 87237 | 122 | 99,9 % | 715,1x |
| 1296 | 1.4.2 Recurso de reposición | Familia | 100107 | 98 | 99,9 % | 1021,5x |
| 1297 | 1.4.2.1 Disturbios interiores | Penal | 121924 | 89 | 99,9 % | 1369,9x |
| 1298 | 1.4.2.1 El derecho a la vida y las TIC | Judicial | 96536 | 110 | 99,9 % | 877,6x |
| 1299 | 1.4.2.2 Guerra civil | Penal | 121924 | 98 | 99,9 % | 1244,1x |
| 1300 | 1.4.2.2 La igualdad ante la ley | Judicial | 96536 | 106 | 99,9 % | 910,7x |
| 1301 | 1.4.2.3 Conflicto armado regional de orden | Penal | 121924 | 88 | 99,9 % | 1385,5x |
| 1302 | 1.4.2.3 Igualdad ante la justicia | Judicial | 96536 | 101 | 99,9 % | 955,8x |
| 1303 | 1.4.2.4 El derecho a la educación y libertad de enseñanza | Judicial | 96536 | 85 | 99,9 % | 1135,7x |
| 1304 | 1.4.2.5 Libertad de expresión, derecho a la | Judicial | 96536 | 100 | 99,9 % | 965,4x |
| 1305 | 1.4.2.6 Protección a la vida privada y honra de las | Judicial | 96536 | 101 | 99,9 % | 955,8x |
| 1306 | 1.4.2.7 La privacidad en la sociedad red | Judicial | 96536 | 72 | 99,9 % | 1340,8x |
| 1307 | 1.4.3 Iniciativas referentes a las asimetrías entre los | Constitucional | 112823 | 85 | 99,9 % | 1327,3x |
| 1308 | 1.4.3 Organización interna de la | Procesal | 94881 | 92 | 99,9 % | 1031,3x |
| 1309 | 1.4.3 Origen social, posición económica y nacimiento | Judicial | 81476 | 76 | 99,9 % | 1072,1x |
| 1310 | 1.4.3 Recurso de apelación | Familia | 100107 | 89 | 99,9 % | 1124,8x |
| 1311 | 1.4.3.1 Recurso excepcional | Familia | 100107 | 106 | 99,9 % | 944,4x |
| 1312 | 1.4.3.2 Resoluciones inapelables | Familia | 100107 | 87 | 99,9 % | 1150,7x |
| 1313 | 1.4.3.3 Reglas de la apelación | Familia | 100107 | 100 | 99,9 % | 1001,1x |
| 1314 | 1.4.3.4 Problemas con la inmediación en segunda instancia | Familia | 100107 | 122 | 99,9 % | 820,5x |
| 1315 | 1.4.3.5 Prueba en segunda instancia | Familia | 100107 | 111 | 99,9 % | 901,9x |
| 1316 | 1.4.4 El juez(a) presidente y su | Procesal | 94881 | 122 | 99,9 % | 777,7x |
| 1317 | 1.4.4 Iniciativas destinadas a fortalecer los | Constitucional | 112823 | 88 | 99,9 % | 1282,1x |
| 1318 | 1.4.4 Los deberes del médico: entre | Civil | 142015 | 75 | 99,9 % | 1893,5x |
| 1319 | 1.4.4 Sexo | Judicial | 81476 | 87 | 99,9 % | 936,5x |
| 1320 | 1.4.5 Idioma | Judicial | 81476 | 89 | 99,9 % | 915,5x |
| 1321 | 1.4.5 Obligaciones y deberes del paciente | Civil | 142015 | 105 | 99,9 % | 1352,5x |
| 1322 | 1.4.5 Patrocinio en el recurso de casación48 | Familia | 100107 | 92 | 99,9 % | 1088,1x |
| 1323 | 1.4.6 Los deberes de colaboración del | Civil | 142015 | 101 | 99,9 % | 1406,1x |
| 1324 | 1.4.6 Religión | Judicial | 81476 | 84 | 99,9 % | 970,0x |
| 1325 | 1.4.7 La infracción del deber de colaboración | Civil | 142015 | 100 | 99,9 % | 1420,2x |
| 1326 | 1.4.7 Opiniones políticas o de cualquier índole | Judicial | 81476 | 89 | 99,9 % | 915,5x |
| 1327 | 1.4.7 Resoluciones no susceptibles de recurso | Familia | 100107 | 72 | 99,9 % | 1390,4x |
| 1328 | 1.4.8 Cualquier otra condición social | Judicial | 81476 | 91 | 99,9 % | 895,3x |
| 1329 | 1.4.8 Recursos en otras leyes de familia | Familia | 100107 | 119 | 99,9 % | 841,2x |
| 1330 | 1.4.8.1 El incumplimiento imputable al paciente | Civil | 142015 | 100 | 99,9 % | 1420,2x |
| 1331 | 1.4.8.2 La contribución a la producción del daño | Civil | 142015 | 80 | 99,9 % | 1775,2x |
| 1332 | 1.4.8.3 La regla de la mitigación149 | Civil | 142015 | 105 | 99,9 % | 1352,5x |
| 1333 | 1.5     Tribunales de | Laboral | 71986 | 40 | 99,9 % | 1799,7x |
| 1334 | 1.5 Los Estados miembros introducirán medidas no privativas de la li- | Penal | 194788 | 111 | 99,9 % | 1754,8x |
| 1335 | 1.5. Efectos de la sentencia que determina la filiación, contra la oposición del | Familia | 62470 | 76 | 99,9 % | 822,0x |
| 1336 | 1.5.1 Derecho a la intimidad | Judicial | 89476 | 98 | 99,9 % | 913,0x |
| 1337 | 1.5.1 Medios preventivos | Penal | 121924 | 91 | 99,9 % | 1339,8x |
| 1338 | 1.5.1 Tipos de sociedades | Constitucional | 112823 | 67 | 99,9 % | 1683,9x |
| 1339 | 1.5.2 Derecho a la propia imagen | Judicial | 89476 | 97 | 99,9 % | 922,4x |
| 1340 | 1.5.2 Grupos empresariales | Constitucional | 112823 | 88 | 99,9 % | 1282,1x |
| 1341 | 1.5.2 Medios de control | Penal | 121924 | 65 | 99,9 % | 1875,8x |
| 1342 | 1.5.2.1 Formas de organización contractual | Constitucional | 112823 | 83 | 99,9 % | 1359,3x |
| 1343 | 1.5.2.2 Grupos basados en relaciones de propiedad | Constitucional | 112823 | 97 | 99,9 % | 1163,1x |
| 1344 | 1.5.3 El principio de corresponsabilidad | Familia | 65192 | 88 | 99,9 % | 740,8x |
| 1345 | 1.6        Transparencia | Laboral | 71986 | 40 | 99,9 % | 1799,7x |
| 1346 | 1.6     Conceptos esenciales: datos, banco de | Constitucional | 104063 | 55 | 99,9 % | 1892,1x |
| 1347 | 1.6.1 Empresas de propiedad del Estado (EPE) | Constitucional | 112823 | 85 | 99,9 % | 1327,3x |
| 1348 | 1.6.1 Legal | Familia | 65192 | 79 | 99,9 % | 825,2x |
| 1349 | 1.6.2 Servicios públicos privatizados | Constitucional | 112823 | 89 | 99,9 % | 1267,7x |
| 1350 | 1.6.3 Compras públicas | Constitucional | 112823 | 79 | 99,9 % | 1428,1x |
| 1351 | 1.7            Categorías de datos personales y sus | Constitucional | 104063 | 75 | 99,9 % | 1387,5x |
| 1352 | 1.7        Criterios para el establecimiento | Familia | 65192 | 53 | 99,9 % | 1230,0x |
| 1353 | 1.7     La Ética | Laboral | 71986 | 39 | 99,9 % | 1845,8x |
| 1354 | 10 A esta pauta se ajustó el actuar policial en el caso conocido en sentencia Corte | Judicial | 144656 | 149 | 99,9 % | 970,8x |
| 1355 | 10 COT: “los tribunales no podrán ejercer su ministerio sino a | Procesal | 94881 | 109 | 99,9 % | 870,5x |
| 1356 | 10 Declaración adoptada por la 31.ª Reunión de la Conferencia General de la | Judicial | 81675 | 55 | 99,9 % | 1485,0x |
| 1357 | 10 En dicha comunidad los bienes adquiridos a título oneroso durante la vigencia | Familia | 123490 | 132 | 99,9 % | 935,5x |
| 1358 | 10 En la Ley 21.090 sólo se utiliza una vez el término «niñas» en una norma que | Penal | 86906 | 104 | 99,9 % | 835,6x |
| 1359 | 10 Estos son los hechos tal como se resumen por la propia Corte, disponible en | Judicial | 92792 | 50 | 99,9 % | 1855,8x |
| 1360 | 10 Juzgado de Letras del Trabajo de Valparaíso, RIT T-288-2017, 20 de octubre de | Laboral | 53374 | 58 | 99,9 % | 920,2x |
| 1361 | 10 Lo mismo se aplica en casos no judicializados en que personas de sesenta o | Judicial | 82507 | 96 | 99,9 % | 859,4x |
| 1362 | 10 Naciones Unidas, «Treaty collection: Status of treaties». Disponible en https:// | Judicial | 81675 | 79 | 99,9 % | 1033,9x |
| 1363 | 10 Para más información, véase Corte de Apelaciones de Santiago, rol 1.399-2022 | Judicial | 87950 | 130 | 99,9 % | 676,5x |
| 1364 | 10 Se basó en la doctrina emanada de la Comisión de Expertos de la Organización | Laboral | 74025 | 89 | 99,9 % | 831,7x |
| 1365 | 10 Se trata, según Hernández (2011: 13), del denominado «atentado impropio» | Judicial | 62514 | 48 | 99,9 % | 1302,4x |
| 1366 | 10 Sentencia de la Corte Suprema, 8 de noviembre de 2022, rol 4659-2022. En igual | Familia | 123490 | 91 | 99,9 % | 1357,0x |
| 1367 | 10 Sentencia de la Corte Suprema, rol 122.925, del 29 de mayo de 2023. En igual | Penal | 178516 | 114 | 99,9 % | 1565,9x |
| 1368 | 10 Sentencia de la Corte de Apelaciones de San Miguel, rol 3.417-1998, 9 de agosto | Penal | 178516 | 184 | 99,9 % | 970,2x |
| 1369 | 10 Sobre esto, el informe de la OCDE en relación con las instrucciones vigentes y | Penal | 178516 | 167 | 99,9 % | 1069,0x |
| 1370 | 10 Tribunal Superior de Justicia de Asturias, en la causa rol del recurso 252/2022 | Laboral | 98828 | 66 | 99,9 % | 1497,4x |
| 1371 | 10 Véase, por ejemplo, rol 160-2005 Corte Suprema: La votación fue de tres a | Constitucional | 177323 | 193 | 99,9 % | 918,8x |
| 1372 | 10.       Revisado en https://eacnur.org/blog/proteccion-internacional-la-esperanza-de millones de- personas/ | Judicial | 81476 | 55 | 99,9 % | 1481,4x |
| 1373 | 10. A mayor abundamiento, es de toda evidencia, que el objeto de la ley | Penal | 194788 | 167 | 99,9 % | 1166,4x |
| 1374 | 10. APARICIO, Joaquín (1992), “Empresas ideológicas | Laboral | 113458 | 101 | 99,9 % | 1123,3x |
| 1375 | 10. Boletín N° 11.126-07 y 11.522-07. Proyecto de ley que modifica | Judicial | 89476 | 75 | 99,9 % | 1193,0x |
| 1376 | 10. CALAMANDREI, Piero (1996): Introducción al es- | Familia | 100107 | 74 | 99,9 % | 1352,8x |
| 1377 | 10. CS, “Empresa Nacional de Electricidad”, 10 de | Judicial | 105809 | 74 | 99,9 % | 1429,9x |
| 1378 | 10. DFL N° 1, Código Civil. Diario Oficial, 30 de mayo | Familia | 100107 | 96 | 99,9 % | 1042,8x |
| 1379 | 10. Diseño de instrumentos de financiamiento descentralizados para | Constitucional | 177323 | 94 | 99,9 % | 1886,4x |
| 1380 | 10. El Comité considera que la nueva tipificación del delito de tortura | Judicial | 78893 | 92 | 99,9 % | 857,5x |
| 1381 | 10. En el evento que se acoja la demanda, régimen comunicacional más beneficioso a cumplir | Judicial | 79146 | 68 | 99,9 % | 1163,9x |
| 1382 | 10. En tribunales con competencia en materia de familia el | Procesal | 94881 | 110 | 99,9 % | 862,6x |
| 1383 | 10. Estado de derecho: es la expresión histórica que | Judicial | 105809 | 130 | 99,9 % | 813,9x |
| 1384 | 10. FLORES, Juan Carlos (2017): “La caducidad de | Judicial | 105809 | 85 | 99,9 % | 1244,8x |
| 1385 | 10. Implementar medidas e incentivos apropiados para pro- | Constitucional | 112823 | 91 | 99,9 % | 1239,8x |
| 1386 | 10. Las partes podran comparecer y defenderse personalmenDEARRENDAMIENTO DELALEY18.101? | Procesal | 95124 | 83 | 99,9 % | 1146,1x |
| 1387 | 10. Ley N° 14.908, de 5 de octubre de 1962, sobre abandono de familia y pago de | Familia | 190697 | 104 | 99,9 % | 1833,6x |
| 1388 | 10. Ley N° 19.874. Facilita la denuncia en caso de atentados sexuales | Judicial | 89476 | 97 | 99,9 % | 922,4x |
| 1389 | 10. Ley N° 20.005, que tipifica y sanciona el Acoso              ro de 2009 (despido atentatorio de dere- | Laboral | 113458 | 140 | 99,9 % | 810,4x |
| 1390 | 10. Observar y cumplir las instrucciones que, en uso de sus facultades | Judicial | 52128 | 74 | 99,9 % | 704,4x |
| 1391 | 10. Ofrecer apoyo para la realización de trámites en plataformas digi- | Judicial | 82507 | 100 | 99,9 % | 825,1x |
| 1392 | 10. Participación de organizaciones de sociedad civil en procesos de | Constitucional | 177323 | 150 | 99,9 % | 1182,2x |
| 1393 | 10. Que como lo ha señalado la doctrina la inoponibilidad consiste en que los actos jurídicos | Judicial | 79146 | 84 | 99,9 % | 942,2x |
| 1394 | 10. Realizar el informe de cuadratura de lo devengado y lo existente | Judicial | 52128 | 76 | 99,9 % | 685,9x |
| 1395 | 10. Relatoría especial sobre verdad, justicia, reparación y garantías | Constitucional | 177323 | 114 | 99,9 % | 1555,5x |
| 1396 | 10. Sacar fotocopias tanto de uso interno como de las compulsas | Judicial | 52128 | 68 | 99,9 % | 766,6x |
| 1397 | 10. Tener en cuenta la brecha digital, es decir, las dificultades para | Constitucional | 177323 | 92 | 99,9 % | 1927,4x |
| 1398 | 10. Un juez(a) deberá tener la habilidad de evitar contactos reiterados | Procesal | 94881 | 92 | 99,9 % | 1031,3x |
| 1399 | 10.1           Ley N° 20.603 | Penal | 211066 | 163 | 99,9 % | 1294,9x |
| 1400 | 10.1.1 La remisión condicional | Penal | 211066 | 124 | 99,9 % | 1702,1x |
| 1401 | 10.1.4 La libertad vigilada y la libertad vigilada intensiva | Penal | 211066 | 165 | 99,9 % | 1279,2x |
| 1402 | 10.1.5 Expulsión de extranjeros | Penal | 211066 | 131 | 99,9 % | 1611,2x |
| 1403 | 10.2                Derecho a la protección | Penal | 72395 | 50 | 99,9 % | 1447,9x |
| 1404 | 10.2.1 Explotación sexual comercial infantil (ESCI) | Penal | 72395 | 62 | 99,9 % | 1167,7x |
| 1405 | 10.2.2 Situación de los NNA migrantes | Penal | 72395 | 101 | 99,9 % | 716,8x |
| 1406 | 10.2.2.1 Regulación de los NNA migrantes | Penal | 72395 | 65 | 99,9 % | 1113,8x |
| 1407 | 10.2.2.2 Los derechos del NNA migrante | Penal | 72395 | 66 | 99,9 % | 1096,9x |
| 1408 | 10.2.2.2.1 Sentencia de la segunda sala (Penal) de la | Penal | 72395 | 66 | 99,9 % | 1096,9x |
| 1409 | 10.2.5. Protección del NNA respecto | Penal | 72395 | 104 | 99,9 % | 696,1x |
| 1410 | 10.2.6. Protección de la salud del NNA | Penal | 72395 | 106 | 99,9 % | 683,0x |
| 1411 | 10.3     Las excepciones en el procedimiento | Laboral | 100583 | 101 | 99,9 % | 995,9x |
| 1412 | 10.3.2 La libertad de expresión, asociación, reunión pacífica y vida privada    155 | Penal | 72395 | 57 | 99,9 % | 1270,1x |
| 1413 | 10.4                Ley N° 21.067, que crea la Defensoría | Penal | 72395 | 58 | 99,9 % | 1248,2x |
| 1414 | 100 En el artículo 4 de su capítulo V, la Constitución de 1791 prescribía, sobre el | Judicial | 144656 | 92 | 99,9 % | 1572,3x |
| 1415 | 100. CORTE SUPREMA, rol Nº 4.807-2017, de veinti-          115. CORTE SUPREMA, rol N° 18.707-2018, de veinti- | Familia | 65085 | 96 | 99,9 % | 678,0x |
| 1416 | 100. De acuerdo con ello, el Estado, en su calidad de garante de | Judicial | 93914 | 111 | 99,9 % | 846,1x |
| 1417 | 100. GARCÍA SUÁREZ, Ignacio (2013), “La prueba | Laboral | 113458 | 102 | 99,9 % | 1112,3x |
| 1418 | 100. SMITH-CASTRO, Vanessa (2010): “Experiencias de Discriminación Social | Judicial | 81476 | 75 | 99,9 % | 1086,3x |
| 1419 | 100. Salinero, Sebastián y Galleguillos, Sebastián | Penal | 119528 | 91 | 99,9 % | 1313,5x |
| 1420 | 101 Se hace necesario establecer que la existencia de fueros especiales debido al | Judicial | 144656 | 126 | 99,9 % | 1148,1x |
| 1421 | 101 rojas pascual (2015) | Judicial | 89476 | 61 | 99,9 % | 1466,8x |
| 1422 | 101. CORTE SUPREMA, rol N° 8.089-2017, de seis de          116. CORTE SUPREMA, rol N° 16.521-2018, de veintio- | Familia | 65085 | 94 | 99,9 % | 692,4x |
| 1423 | 101. GHEZZI, Giorgio y ROMAGNOLI, Umberto (1987), Il | Laboral | 113458 | 120 | 99,9 % | 945,5x |
| 1424 | 102 Taruffo (2009a: 279). El autor considera que la simplificación probatoria de | Judicial | 150341 | 107 | 99,9 % | 1405,1x |
| 1425 | 102. CORTE SUPREMA, rol N° 7.163-2017, de veinti-          117. CORTE SUPREMA, rol N° 6.385-2018, de veintio- | Familia | 65085 | 96 | 99,9 % | 678,0x |
| 1426 | 102. Dirección de Estudios Corte Suprema (2020): “Mecanismos de ejecución de | Penal | 121924 | 76 | 99,9 % | 1604,3x |
| 1427 | 102. SUPERINTENDENCIA DE EDUCACIÓN, Ministerio de Educación Chile | Judicial | 81476 | 72 | 99,9 % | 1131,6x |
| 1428 | 102. VALENZUELA, Cecilia y ZÚÑIGA, Alejandra (2014): “Leyes de cuotas elec- | Constitucional | 121906 | 68 | 99,9 % | 1792,7x |
| 1429 | 102. VONSTRITZKY, Johannes (2013): “El desarrollo | Judicial | 89476 | 106 | 99,9 % | 844,1x |
| 1430 | 103   Este recurso fue introducido en la Constitución de 1925 por la Ley Nº 12.548, pero haciéndolo procedente | Judicial | 105809 | 115 | 99,9 % | 920,1x |
| 1431 | 103 Por ejemplo, Tribe (1972:1376 considera: «One element, at least, of that ritual | Judicial | 150341 | 171 | 99,9 % | 879,2x |
| 1432 | 103 Se reconocen dos tipos de acuerdos de arbitraje: la cláusula compromisoria y el | Judicial | 144656 | 176 | 99,9 % | 821,9x |
| 1433 | 103. CORTE SUPREMA, rol N° 31.968-2017, de tres de         118. CORTE SUPREMA, rol N° 29.841-2018, de dieci- | Familia | 65085 | 96 | 99,9 % | 678,0x |
| 1434 | 104. CORTE SUPREMA, rol N° 14.544-2017, de veinti-         119. TRIBUNAL EUROPEO DE DERECHOS HUMA- | Familia | 65085 | 96 | 99,9 % | 678,0x |
| 1435 | 105. Drnas de Clément, Zlata (2002): “Las normas imperativas de derecho | Penal | 121924 | 75 | 99,9 % | 1625,7x |
| 1436 | 105. SORDI, Bárbara (2015): “Programas de rehabilitación para agresores en | Familia | 95131 | 78 | 99,9 % | 1219,6x |
| 1437 | 105. VILLAVICENCIO, Luis (2015): “Una concepción de la ciudadanía para una | Constitucional | 121906 | 80 | 99,9 % | 1523,8x |
| 1438 | 106 La verdad sea dicha, esta crítica más que objetar la aplicación del teorema | Judicial | 150341 | 162 | 99,9 % | 928,0x |
| 1439 | 106. Dubois, Dan (2009): “The Authority of Peremptory Norms in International | Penal | 121924 | 71 | 99,9 % | 1717,2x |
| 1440 | 106. VIVANCO, Ángela. (2006): Curso de Derecho Constitucional: Aspectos | Judicial | 81476 | 52 | 99,9 % | 1566,8x |
| 1441 | 107   CONTRERAS, Pablo (2009), Poder privado y derechos. Eficacia horizontal y ponderación de los derechos | Laboral | 113458 | 76 | 99,9 % | 1492,9x |
| 1442 | 108     Referencias | Penal | 51155 | 45 | 99,9 % | 1136,8x |
| 1443 | 108 Por ejemplo: ¿Debe introducirse un valor negativo en el valor prior probability | Judicial | 150341 | 143 | 99,9 % | 1051,3x |
| 1444 | 108. El Comité considera que el Estado Parte viola el artículo 37 (a) | Penal | 72395 | 100 | 99,9 % | 724,0x |
| 1445 | 108. Sentencia Tribunal Constitucional. Rol Nº 2246- | Administrativo | 89720 | 80 | 99,9 % | 1121,5x |
| 1446 | 108. UNICEF y CEPAL (2009): “Maltrato infantil: una dolorosa realidad puertas | Familia | 95131 | 78 | 99,9 % | 1219,6x |
| 1447 | 109 Taruffo (2009a: 197 y 198) señala que hasta ahora la posibilidad de que el | Judicial | 150341 | 182 | 99,9 % | 826,0x |
| 1448 | 11 Caso Cantos con Argentina, 2002. Las notas incluidas en algunos párrafos del | Judicial | 144656 | 93 | 99,9 % | 1555,4x |
| 1449 | 11 Comisión Interamericana de Derechos Humanos, Informe 35/96, Caso 10.832 | Judicial | 78893 | 63 | 99,9 % | 1252,3x |
| 1450 | 11 De 30 de enero de 1987, sobre el habeas corpus bajo suspensión de garantías | Judicial | 144656 | 76 | 99,9 % | 1903,4x |
| 1451 | 11 El Considerando cuarto de la sentencia de rol 15-2016, de la ICA, confirmada | Constitucional | 177323 | 137 | 99,9 % | 1294,3x |
| 1452 | 11 En el mismo sentido sentencia Corte Suprema rol 1724-2008, de 14 de octubre | Judicial | 144656 | 97 | 99,9 % | 1491,3x |
| 1453 | 11 En lógica proposicional la implicación material se define conforme a sus valores | Judicial | 92792 | 130 | 99,9 % | 713,8x |
| 1454 | 11 Estos son los hechos tal como se resumen por la propia Corte, disponible en | Judicial | 92792 | 50 | 99,9 % | 1855,8x |
| 1455 | 11 Hand (1901: 54): «But how can the jury judge between two statements each | Judicial | 150341 | 91 | 99,9 % | 1652,1x |
| 1456 | 11 Inciso final artículo 18 Ley 19.968: «Tratándose de los procedimientos señalados | Familia | 97488 | 128 | 99,9 % | 761,6x |
| 1457 | 11 La Ley 20.084, que establece un sistema de responsabilidad de los adolescentes | Judicial | 144656 | 205 | 99,9 % | 705,6x |
| 1458 | 11 La jurisprudencia ha señalado que «este tipo penal está construido sobre la base | Penal | 178516 | 163 | 99,9 % | 1095,2x |
| 1459 | 11 Ley que lleva el nombre de Daniel Zamudio Vera, joven asesinado en razón | Constitucional | 177323 | 144 | 99,9 % | 1231,4x |
| 1460 | 11 Se ha observado acertadamente que la incorporación de esta segunda variante | Penal | 178516 | 166 | 99,9 % | 1075,4x |
| 1461 | 11 Se trata de un poder más bien fáctico y no de una posición de garante, pues es | Judicial | 78893 | 70 | 99,9 % | 1127,0x |
| 1462 | 11 Segundo Juzgado de Letras del Trabajo de Santiago, RIT O-5244-2019, 5 de | Laboral | 53374 | 58 | 99,9 % | 920,2x |
| 1463 | 11 Sentencia de la Corte de Apelaciones de Santiago, rol 275-2021, 18 de febrero | Familia | 97488 | 68 | 99,9 % | 1433,6x |
| 1464 | 11 Si se produjo durante el periodo de convivencia conyugal, no procede alegarlo | Familia | 123490 | 185 | 99,9 % | 667,5x |
| 1465 | 11 Sobre los fundamentos y distinciones entre los modelos reglados y los modelos | Procesal | 86112 | 102 | 99,9 % | 844,2x |
| 1466 | 11.   Barrientos, Elías (2019): La culpabilidad en el de- | Penal | 119528 | 74 | 99,9 % | 1615,2x |
| 1467 | 11.   Corte de Apelaciones de Santiago, rol N° 313-          te-en-procedimientos-de-materias-de-fami- | Familia | 100107 | 122 | 99,9 % | 820,5x |
| 1468 | 11.   Ley Nº 20.379, crea sistema intersectorial de protección social e institu- | Constitucional | 121906 | 75 | 99,9 % | 1625,4x |
| 1469 | 11. A los efectos de las presentes reglas, deben aplicarse las definiciones | Penal | 194788 | 156 | 99,9 % | 1248,6x |
| 1470 | 11. Boletín N° 11.144-07 y 11.092. Proyecto de ley que modifica la | Judicial | 89476 | 84 | 99,9 % | 1065,2x |
| 1471 | 11. Definición y vinculación de acciones de estratégicas del | Procesal | 94881 | 110 | 99,9 % | 862,6x |
| 1472 | 11. Las causas relativas al maltrato de niños, niñas o adolescentes de acuerdo a lo dispuesto | Familia | 100107 | 76 | 99,9 % | 1317,2x |
| 1473 | 11. Que en el presente caso el actor dedujo la acción de inoponibilidad en razón que el acto | Judicial | 79146 | 114 | 99,9 % | 694,3x |
| 1474 | 11. Que, aplicando este último criterio interpretativo, si se acogiese la | Penal | 194788 | 126 | 99,9 % | 1545,9x |
| 1475 | 11. Se permite habitualmente a un juez(a) que acepte invitaciones | Procesal | 94881 | 97 | 99,9 % | 978,2x |
| 1476 | 11.1 Los órganos judiciales tienen autoridad y capacidad, en la | Constitucional | 112823 | 88 | 99,9 % | 1282,1x |
| 1477 | 11.1 Origen y noción del acoso sexual                                                          174 | Laboral | 100583 | 52 | 99,9 % | 1934,3x |
| 1478 | 11.2      Definición en Chile | Laboral | 100583 | 53 | 99,9 % | 1897,8x |
| 1479 | 11.2 En cada caso, las sanciones impuestas a las empresas: a) | Constitucional | 112823 | 96 | 99,9 % | 1175,2x |
| 1480 | 11.3           Reposición | Penal | 211066 | 137 | 99,9 % | 1540,6x |
| 1481 | 11.3 En la medida de lo posible, se consulta debidamente a | Constitucional | 112823 | 83 | 99,9 % | 1359,3x |
| 1482 | 11.3.1 Sujeto activo | Laboral | 100583 | 100 | 99,9 % | 1005,8x |
| 1483 | 11.3.2 Sujeto pasivo | Laboral | 100583 | 80 | 99,9 % | 1257,3x |
| 1484 | 11.3.3.1 Acoso sexual y contenido del reglamento interno: en | Laboral | 100583 | 101 | 99,9 % | 995,9x |
| 1485 | 11.3.3.2 Procedimiento de investigación: se inicia con una | Laboral | 100583 | 114 | 99,9 % | 882,3x |
| 1486 | 11.3.3.3 Medidas de resguardo: el empleador, una vez recibida la | Laboral | 100583 | 81 | 99,9 % | 1241,8x |
| 1487 | 11.3.3.4 Denuncia ante el empleador: la investigación de los | Laboral | 100583 | 120 | 99,9 % | 838,2x |
| 1488 | 11.3.3.5 Medidas post investigación: si la investigación fuese | Laboral | 100583 | 72 | 99,9 % | 1397,0x |
| 1489 | 11.3.3.6 Causal de despido: con independencia de las sanciones | Laboral | 100583 | 149 | 99,9 % | 675,1x |
| 1490 | 11.4     Jurisprudencia | Laboral | 100583 | 109 | 99,9 % | 922,8x |
| 1491 | 11.7. Algunos planteamientos acerca del Estado de Derecho en la doctrina | General | 129559 | 72 | 99,9 % | 1799,4x |
| 1492 | 110      ICA La Serena, rol N° 178-2019, sentencia 22 de mayo de 2019, C. 11 | Familia | 95131 | 92 | 99,9 % | 1034,0x |
| 1493 | 110 La referencia es a los árbitros que fallan conforme a derecho, pues es requisito | Judicial | 144656 | 97 | 99,9 % | 1491,3x |
| 1494 | 110. En conclusión, la Corte Interamericana observa que al ser, en abstracto, el | Judicial | 93914 | 122 | 99,9 % | 769,8x |
| 1495 | 111. Federación Internacional de los Derechos Humanos (2004): Informe final de | Penal | 121924 | 91 | 99,9 % | 1339,8x |
| 1496 | 111. Una determinación a partir de presunciones infundadas y estereotipadas | Judicial | 93914 | 114 | 99,9 % | 823,8x |
| 1497 | 112      DE NO-LOUIS Y CABALLERO, Eduardo, “El working-house informático o tele-trabajo”. En Revista Iberoame- | Judicial | 96536 | 88 | 99,9 % | 1097,0x |
| 1498 | 112   BARBAGELATA, Héctor-Hugo (2009), El particularismo del derecho del trabajo y los derechos humanos la- | Laboral | 113458 | 102 | 99,9 % | 1112,3x |
| 1499 | 112   Chilectra (2001), p. 79 | Familia | 100107 | 70 | 99,9 % | 1430,1x |
| 1500 | 112 Ahora se establece como derecho del consumidor en el artículo 3 letra g) el | Judicial | 144656 | 166 | 99,9 % | 871,4x |
| 1501 | 112 En este sentido, Taruffo (2009a: 201) cita como ejemplo la determinación de | Judicial | 150341 | 178 | 99,9 % | 844,6x |
| 1502 | 113   ABELIUK (2000), p. 151 | Familia | 65085 | 61 | 99,9 % | 1067,0x |
| 1503 | 113. Fernández Flores de Fúnes, José Luis (2005): “De la jurisdicción territorial a | Penal | 121924 | 76 | 99,9 % | 1604,3x |
| 1504 | 114. Fernández Neira, Karinna y Sferrazza Taibi, Pietro (2009): “La aplicación de | Penal | 121924 | 78 | 99,9 % | 1563,1x |
| 1505 | 115 En el mismo sentido, Taruffo (2009a; 205.): la aplicación de este teorema de | Judicial | 150341 | 101 | 99,9 % | 1488,5x |
| 1506 | 115. De conformidad con lo anterior, se puede concluir que | Judicial | 93914 | 115 | 99,9 % | 816,6x |
| 1507 | 115. Fraidenraij, Susana (1998): “Convención sobre prohibición o restricciones del | Penal | 121924 | 97 | 99,9 % | 1256,9x |
| 1508 | 116   ARELLANO ORTIZ, Pablo (2012): “Marco del análisis del sistema de pensiones chileno después de la reforma | Laboral | 100583 | 83 | 99,9 % | 1211,8x |
| 1509 | 116 Este tercero puede ser la entidad administradora del arbitraje, por haberse | Judicial | 144656 | 126 | 99,9 % | 1148,1x |
| 1510 | 116. De acuerdo a lo anterior, la respuesta a la primera | Judicial | 93914 | 89 | 99,9 % | 1055,2x |
| 1511 | 117. Con la finalidad de que las personas interesadas puedan | Judicial | 93914 | 98 | 99,9 % | 958,3x |
| 1512 | 117. Van Weezel, Alex (2017): “Sobre la necesidad de | Penal | 119528 | 81 | 99,9 % | 1475,7x |
| 1513 | 117. ZAIKOSKI, Daniela (2018): “Comentario a la Recomendación General N° 35 | Familia | 95131 | 78 | 99,9 % | 1219,6x |
| 1514 | 118. Vásquez, Mª Fernanda (2019): Sociedades. Co- | Penal | 119528 | 85 | 99,9 % | 1406,2x |
| 1515 | 119 En arbitraje comercial internacional, a diferencia del doméstico, a falta de | Judicial | 144656 | 107 | 99,9 % | 1351,9x |
| 1516 | 119. Frontaura Rivera, Carlos (1999): “Territorialidad, prescripción e inmunidad en | Penal | 121924 | 85 | 99,9 % | 1434,4x |
| 1517 | 12 A modo de ejemplo, y sin perjuicio de que volveremos sobre ello en la sección | Penal | 178516 | 169 | 99,9 % | 1056,3x |
| 1518 | 12 Aunque sostienen estos autores que tampoco «representa necesariamente un | Penal | 178516 | 163 | 99,9 % | 1095,2x |
| 1519 | 12 Cisternas (2011: 68) explica que antes de la entrada en vigor de la Ley 20.000 se | Penal | 97633 | 65 | 99,9 % | 1502,0x |
| 1520 | 12 Convención Interamericana para Prevenir, Sancionar y Erradicar la Violencia | Laboral | 53374 | 52 | 99,9 % | 1026,4x |
| 1521 | 12 Corresponde a la cantidad de proyectos del área de Justicia Juvenil en los que se | Penal | 86906 | 109 | 99,9 % | 797,3x |
| 1522 | 12 El 11 de diciembre de 2021 se publicó en el Diario Oficial el Reglamento que | Judicial | 89450 | 97 | 99,9 % | 922,2x |
| 1523 | 12 En el mismo sentido, Roberts y Zuckermann (2010: 258) sostienen que «the | Judicial | 150341 | 78 | 99,9 % | 1927,4x |
| 1524 | 12 En publicaciones posteriores, el propio MacCormick (1992; 2005) reconocerá | Judicial | 92792 | 71 | 99,9 % | 1306,9x |
| 1525 | 12 Juzgado de Letras del Trabajo de Concepción, RIT T-94-2015, 9 de octubre de | Laboral | 53374 | 76 | 99,9 % | 702,3x |
| 1526 | 12 LTF. Se agregan los demás posibles vicios procesales, regulados | Familia | 100107 | 61 | 99,9 % | 1641,1x |
| 1527 | 12 Matus y Ramírez (2019: 504) señalan que las conductas que se mencionan en el | Penal | 97633 | 79 | 99,9 % | 1235,9x |
| 1528 | 12 N° 1, letra c), y 13 de la Ley N° 19.253, infiere que es correcta la decisión impugnada en | Civil | 171433 | 152 | 99,9 % | 1127,8x |
| 1529 | 12 Organización Mundial de la Salud, La salud sexual y su relación con la salud | Judicial | 81675 | 67 | 99,9 % | 1219,0x |
| 1530 | 12 Politoff, Matus y Ramírez (2009: 619), refiriéndose a la calificante de la letra g) | Penal | 97633 | 118 | 99,9 % | 827,4x |
| 1531 | 12 Sentencia Corte Suprema rol 7051-2007, de 13 de octubre de 2009. El fallo de | Judicial | 144656 | 183 | 99,9 % | 790,5x |
| 1532 | 12 Sentencia absolutoria, Cuarto Tribunal Oral en lo Penal de Santiago, causa RIT | Procesal | 86112 | 58 | 99,9 % | 1484,7x |
| 1533 | 12 Sentencia de la Corte Suprema, rol 134.271-2022, 13 de diciembre de 2022. En el | Familia | 97488 | 100 | 99,9 % | 974,9x |
| 1534 | 12 Véase la campaña de la cámara de diputados sobre la mejora de las políticas | Judicial | 82507 | 91 | 99,9 % | 906,7x |
| 1535 | 12.   Ley Nº 19.628. Sobre Protección de la vida priva- | Administrativo | 89720 | 61 | 99,9 % | 1470,8x |
| 1536 | 12. Actualizar los Instrumentos de Planificación Territorial desde un | Constitucional | 177323 | 159 | 99,9 % | 1115,2x |
| 1537 | 12. Adquirir y abastecer de material de trabajo al tribunal, en confor- | Judicial | 52128 | 78 | 99,9 % | 668,3x |
| 1538 | 12. Asistir o no a una firma de abogados, exige que el juez(a) indague | Procesal | 94881 | 101 | 99,9 % | 939,4x |
| 1539 | 12. CS, “Endesa con Dirección General de Aguas”, rol | Judicial | 105809 | 114 | 99,9 % | 928,1x |
| 1540 | 12. Contrato de adhesión, cuando se trate del reglamento de copropiedad dictado por el | Civil | 192585 | 182 | 99,9 % | 1058,2x |
| 1541 | 12. Convención Interamericana para la Eliminación de Todas las | Judicial | 89476 | 53 | 99,9 % | 1688,2x |
| 1542 | 12. Cristina Hormazábal Andrade con GD Ingeniería            de Salud de Concepción (2012): Corte de Apela- | Civil | 142015 | 87 | 99,9 % | 1632,4x |
| 1543 | 12. Enumeración de los considerandos con números o | Judicial | 79146 | 63 | 99,9 % | 1256,3x |
| 1544 | 12. Evaluación | Procesal | 94881 | 96 | 99,9 % | 988,3x |
| 1545 | 12. Incorporar Formación en derechos humanos para funcionarios/ | Constitucional | 177323 | 144 | 99,9 % | 1231,4x |
| 1546 | 12. Proceso de participación y consulta de la propuesta reglamentaria | Judicial | 89476 | 97 | 99,9 % | 922,4x |
| 1547 | 12. Que, adicionalmente, y tal como se ha señalado en sentencia de | Penal | 194788 | 187 | 99,9 % | 1041,6x |
| 1548 | 12.2      Regulación del | Laboral | 100583 | 53 | 99,9 % | 1897,8x |
| 1549 | 12.3.1 Sanciones por infracción al reglamento interno | Laboral | 100583 | 113 | 99,9 % | 890,1x |
| 1550 | 12.3.2 Autodespido | Laboral | 100583 | 109 | 99,9 % | 922,8x |
| 1551 | 12.3.3 Enfermedad profesional | Laboral | 100583 | 120 | 99,9 % | 838,2x |
| 1552 | 12.3.4 Tutela de derechos | Laboral | 100583 | 106 | 99,9 % | 948,9x |
| 1553 | 12.3.5 Eventuales sanciones para el o la denunciante | Laboral | 100583 | 104 | 99,9 % | 967,1x |
| 1554 | 12.4.1 Vulneración de integridad psíquica | Laboral | 100583 | 87 | 99,9 % | 1156,1x |
| 1555 | 12.4.2 Acción parcialmente acogida | Laboral | 100583 | 55 | 99,9 % | 1828,8x |
| 1556 | 12.4.3 Tratos inadecuados | Laboral | 100583 | 87 | 99,9 % | 1156,1x |
| 1557 | 12.4.4 Cámara de videovigilancia | Laboral | 100583 | 113 | 99,9 % | 890,1x |
| 1558 | 12.4.5 Tutela por autodespido | Laboral | 100583 | 93 | 99,9 % | 1081,5x |
| 1559 | 12.5.1 Diligencias de investigación | Penal | 211066 | 124 | 99,9 % | 1702,1x |
| 1560 | 120 Corte de Apelaciones de París, 19 de octubre de 2021, Pôle 5-Ch.16, Société | Judicial | 144656 | 159 | 99,9 % | 909,8x |
| 1561 | 120. Corte Suprema, Toro y otros con Contreras y otros (2009): sentencia de | Penal | 121924 | 71 | 99,9 % | 1717,2x |
| 1562 | 120. En concordancia con lo expresado, en cuanto a los efectos de | Judicial | 93914 | 113 | 99,9 % | 831,1x |
| 1563 | 121       Bermúdez (2014); p. 262 | Judicial | 134465 | 84 | 99,9 % | 1600,8x |
| 1564 | 121   Corte Suprema, 25 de abril de 2017, Rol Nº 38151-2016; también véase Corte Suprema, 13 de noviembre de | Civil | 142015 | 74 | 99,9 % | 1919,1x |
| 1565 | 121 DL Nº 2.128) | Familia | 65085 | 55 | 99,9 % | 1183,4x |
| 1566 | 122      RALLO LOMBARTE, Artemi: “El debate europeo sobre el derecho al olvido en internet”. En Hacia un Nuevo | Constitucional | 104063 | 79 | 99,9 % | 1317,3x |
| 1567 | 123   Corte Suprema, 22 de agosto de 2012, Rol Nº 3240-2012; así también véase Corte Suprema, 5 de junio de | Civil | 142015 | 78 | 99,9 % | 1820,7x |
| 1568 | 123. Gaeta, Paola (2007): “On What Conditions Can a State be Held Responsible | Penal | 121924 | 68 | 99,9 % | 1793,0x |
| 1569 | 124 Es preciso advertir a los y las lectoras que en un recurso de anulación los | Judicial | 144656 | 80 | 99,9 % | 1808,2x |
| 1570 | 125      En el mismo sentido, DEL MORAL GARCÍA (1999), p. 325; GARCÍA y DEL CARPIO (2000), pp. 67-68; MAQUEDA | Familia | 95131 | 62 | 99,9 % | 1534,4x |
| 1571 | 125 En forma detallada, Coca (2013), p. 51, de acuerdo con quien este sistema “alude a la forma de regulación | Penal | 119528 | 133 | 99,9 % | 898,7x |
| 1572 | 125. La Corte observa que el elenco de garantías mínimas establecido en | Judicial | 144656 | 140 | 99,9 % | 1033,3x |
| 1573 | 127 Bermejo (2017), p. 81. Como se podrá apreciar más adelante, por eso se reconoce la importancia de las di- | Penal | 119528 | 91 | 99,9 % | 1313,5x |
| 1574 | 127. Corte Suprema, Contra Aravena y otro (2012): sentencia 7 marzo 2012, rol | Penal | 121924 | 61 | 99,9 % | 1998,8x |
| 1575 | 127. Gamboa Serazzi, Fernando (1999): “El caso Pinochet, historial y algunos | Penal | 121924 | 76 | 99,9 % | 1604,3x |
| 1576 | 128. LOVERA Domingo (2017), “Destinatarios de los | Laboral | 113458 | 80 | 99,9 % | 1418,2x |
| 1577 | 128. La Corte Europea se ha pronunciado sobre este tema, señalando | Judicial | 144656 | 128 | 99,9 % | 1130,1x |
| 1578 | 129      CÓRDOBA CASTROVERDE, Diego y DÍEZ-PICAZO GIMÉNEZ, Ignacio: “Reflexiones sobre los retos de la | Constitucional | 104063 | 132 | 99,9 % | 788,4x |
| 1579 | 129 J de la Ordenanza de Aduanas, se suspende la prescripción de tres | Judicial | 62888 | 92 | 99,9 % | 683,6x |
| 1580 | 13       Debe tenerse presente que el derecho a la protección de los datos personales como tal (no nos estamos | Constitucional | 104063 | 143 | 99,9 % | 727,7x |
| 1581 | 13   E. Corte Suprema en rol Nº 2054-2015, citado en Correa Selamé, Jorge Danilo. Curso de Derecho procesal | Procesal | 94881 | 94 | 99,9 % | 1009,4x |
| 1582 | 13 Aplican en este caso las normas del párrafo tercero del título XXXIV del libro | Familia | 123490 | 140 | 99,9 % | 882,1x |
| 1583 | 13 Artículo 532, numeral 2: censura por escrito; numeral 3: multa de uno a quince | Judicial | 89450 | 98 | 99,9 % | 912,8x |
| 1584 | 13 Así lo señala al comparar la interpretación de la Constitución, que incorpora | Judicial | 92792 | 75 | 99,9 % | 1237,2x |
| 1585 | 13 Así, por ejemplo, en el fallo de la Corte Suprema, rol 5.396-2014 del 18 de junio | Judicial | 87950 | 111 | 99,9 % | 792,3x |
| 1586 | 13 Bien lo constatan Rodríguez Collao y Ossandón Widow al señalar que ha sido | Penal | 178516 | 161 | 99,9 % | 1108,8x |
| 1587 | 13 Caso Godoy con Fisco, en Revista de Derecho y Jurisprudencia (1913), segunda | Judicial | 92792 | 65 | 99,9 % | 1427,6x |
| 1588 | 13 Cisternas (2011: 33 y 34; 2013: 13) y Rettig (2013: 68). En Corte Suprema, rol | Penal | 97633 | 100 | 99,9 % | 976,3x |
| 1589 | 13 Como explica Cammack (2013: 4 y 5), la Corte Suprema estadounidense ha | Judicial | 144656 | 115 | 99,9 % | 1257,9x |
| 1590 | 13 Como explica Cea (2008: 312), si la Corte rechaza la acción, no queda más que | Constitucional | 177323 | 92 | 99,9 % | 1927,4x |
| 1591 | 13 El artículo 141 del Código Civil fija un ámbito de aplicación amplio al establecer | Familia | 123490 | 172 | 99,9 % | 718,0x |
| 1592 | 13 En abril de 2022 se descubrió que una asistente de fiscal se dedicaba a exigir | Penal | 178516 | 133 | 99,9 % | 1342,2x |
| 1593 | 13 Gascón (2010: 179), considera que «la confirmación es, pues, una inferencia | Judicial | 150341 | 122 | 99,9 % | 1232,3x |
| 1594 | 13 Matus (1999: 222) complementa que lo mismo puede decirse de los actos de | Penal | 97633 | 67 | 99,9 % | 1457,2x |
| 1595 | 13 N° 2), Venezuela (art. 21), Puerto Rico (art. 2°, sección 1), Brasil | Judicial | 87237 | 110 | 99,9 % | 793,1x |
| 1596 | 13 O la declaración de parte en la Ley 19.968 que crea los Tribunales de Familia y | Procesal | 86112 | 63 | 99,9 % | 1366,9x |
| 1597 | 13 Segundo Juzgado de Letras del Trabajo de Santiago, RIT T-309-2018, 7 de junio | Laboral | 53374 | 58 | 99,9 % | 920,2x |
| 1598 | 13 Según Rey (1999: 74), se debe acoger una exégesis del texto penal que permita | Penal | 97633 | 101 | 99,9 % | 966,7x |
| 1599 | 13 Valentina Paredes, «Perseguidas por abortar: 366 mujeres han sido imputadas | Penal | 86906 | 66 | 99,9 % | 1316,8x |
| 1600 | 13 Véase las Reglas de Beijing (número 26.4), la Observación General número 17 | Penal | 86906 | 102 | 99,9 % | 852,0x |
| 1601 | 13.   Ley Nº 20.422. Establece normas sobre igualdad | Administrativo | 89720 | 89 | 99,9 % | 1008,1x |
| 1602 | 13. Aceptar la propuesta del administrador o presentar una alternativa distinta, en el | Civil | 192585 | 157 | 99,9 % | 1226,7x |
| 1603 | 13. BRANTT, María Graciela (2008): “Los deberes | Civil | 142015 | 114 | 99,9 % | 1245,7x |
| 1604 | 13. Caso “Majmud c/ Ministerio de Obras Publicas”.                   Normas jurídicas citadas | Judicial | 89476 | 93 | 99,9 % | 962,1x |
| 1605 | 13. Con la misma cautela deben evaluarse las visitas al antiguo bufete | Procesal | 94881 | 70 | 99,9 % | 1355,4x |
| 1606 | 13. Contrato colectivo: el contrato obligará no sólo a quienes hayan concurrido con su | Civil | 192585 | 208 | 99,9 % | 925,9x |
| 1607 | 13. Cristóbal Tienken Fernández con Clínica Las          27.   Carlos Henríquez Durán y otro (2007): Corte de | Civil | 142015 | 92 | 99,9 % | 1543,6x |
| 1608 | 13. Cultura organizacional: conjunto de reglas y | Penal | 119528 | 75 | 99,9 % | 1593,7x |
| 1609 | 13. Juicio de cuentas: procedimiento jurisdiccional | Judicial | 105809 | 104 | 99,9 % | 1017,4x |
| 1610 | 13. Levantamiento y diagnóstico de las familias que no cuentan con | Constitucional | 177323 | 98 | 99,9 % | 1809,4x |
| 1611 | 13. Ley Nº 20.178, que regula la relación laboral de | Laboral | 113458 | 118 | 99,9 % | 961,5x |
| 1612 | 13. Ley Nº 20.422, establece normas sobre igualdad de oportunidades e inclu- | Constitucional | 121906 | 67 | 99,9 % | 1819,5x |
| 1613 | 13. Pacto de Integridad en Convenio Marco (ID 595). Cumplimiento | Constitucional | 177323 | 170 | 99,9 % | 1043,1x |
| 1614 | 13. Preparar la agenda de audiencias entregando la carpeta al juez | Judicial | 52128 | 65 | 99,9 % | 802,0x |
| 1615 | 13. Que la acción de autos en síntesis está dirigida en contra de la demandada, en razón de | Judicial | 79146 | 113 | 99,9 % | 700,4x |
| 1616 | 13. Que, de conformidad a lo indicado precedentemente, se debe con- | Penal | 194788 | 141 | 99,9 % | 1381,5x |
| 1617 | 13. Señale ejemplos en los que tribunales ordinarios sean considerados como competentes | Judicial | 105809 | 78 | 99,9 % | 1356,5x |
| 1618 | 13.1               Conceptualización | Laboral | 100583 | 114 | 99,9 % | 882,3x |
| 1619 | 13.2               Procedimiento | Laboral | 100583 | 58 | 99,9 % | 1734,2x |
| 1620 | 13.3 La relación de causalidad entre el dolo o la culpa o el hecho del | Civil | 96458 | 83 | 99,9 % | 1162,1x |
| 1621 | 13.3 La relación de causalidad entre el dolo, la culpa y el daño; y | Civil | 96458 | 83 | 99,9 % | 1162,1x |
| 1622 | 13.3.3 La prueba anticipada | Penal | 211066 | 133 | 99,9 % | 1587,0x |
| 1623 | 13.4             Comentario crítico de la | Laboral | 100583 | 58 | 99,9 % | 1734,2x |
| 1624 | 13.4.1 Las medidas que contempla el artículo 155 CPP | Penal | 211066 | 109 | 99,9 % | 1936,4x |
| 1625 | 13.4.2 Las medidas especiales que | Penal | 211066 | 120 | 99,9 % | 1758,9x |
| 1626 | 13.4.3 Las medidas cautelares reales | Penal | 211066 | 107 | 99,9 % | 1972,6x |
| 1627 | 13.5.1 Requisitos de la prisión preventiva | Penal | 211066 | 109 | 99,9 % | 1936,4x |
| 1628 | 13.5.2 Situaciones de improcedencia | Penal | 211066 | 106 | 99,9 % | 1991,2x |
| 1629 | 13.5.3 Excepciones a la improcedencia | Penal | 211066 | 109 | 99,9 % | 1936,4x |
| 1630 | 13.5.5 Procedimiento para decretar la prisión preventiva | Penal | 211066 | 113 | 99,9 % | 1867,8x |
| 1631 | 13.5.6 Renovación de la discusión acerca | Penal | 211066 | 123 | 99,9 % | 1716,0x |
| 1632 | 13.5.9 Recursos relacionados con la prisión | Penal | 211066 | 127 | 99,9 % | 1661,9x |
| 1633 | 130      ICA La Serena, rol N° 103-2017, sentencia 13 de abril de 2017, C. 6 | Familia | 95131 | 70 | 99,9 % | 1359,0x |
| 1634 | 130. Goodwin-Gill, Guy S. (1999): “Crime in International Law: Obligations erga | Penal | 121924 | 88 | 99,9 % | 1385,5x |
| 1635 | 130. Los directores generales y las juntas directivas de las empresas | Judicial | 144656 | 101 | 99,9 % | 1432,2x |
| 1636 | 131. Gómez Campelo, Esther (2000): “El Derecho Penal Internacional ante el caso | Penal | 121924 | 88 | 99,9 % | 1385,5x |
| 1637 | 1317. Pero dicha partición no implicaría poner término al pacto de comunidad, sino que | Familia | 190697 | 153 | 99,9 % | 1246,4x |
| 1638 | 132   Cabe hacer presente que las personas trabajadoras del sector público también ejecutan su labor en forma | Laboral | 113458 | 124 | 99,9 % | 915,0x |
| 1639 | 132. En el caso en estudio, el acto administrativo sancionatorio es el | Judicial | 144656 | 115 | 99,9 % | 1257,9x |
| 1640 | 133      Causa rol Nº 5/2020 (reclamación administrativa) de la Corte de Apelaciones de Antofagasta, de 30 de | Constitucional | 112823 | 61 | 99,9 % | 1849,6x |
| 1641 | 133      MUÑOZ MASSOUH, Ana María: “Eliminación de datos personales en internet: el reconocimiento del derecho | Constitucional | 104063 | 110 | 99,9 % | 946,0x |
| 1642 | 133   La jurisprudencia más reciente ha refrendado la fuerza integradora de la buena fe objetiva. Véase Corte | Civil | 142015 | 122 | 99,9 % | 1164,1x |
| 1643 | 133. González, Felipe: “Derechos Humanos y Derecho Humanitario: un análisis | Penal | 121924 | 76 | 99,9 % | 1604,3x |
| 1644 | 133. Las víctimas de esta causa no fueron sometidas a un procedimiento | Judicial | 144656 | 154 | 99,9 % | 939,3x |
| 1645 | 133; JANIS y NOYES (2006), p. 149; CADENA (2010), pp. 236-237; SANDOVAL (2010), pp. 204-206; STEPHEN | Penal | 121924 | 139 | 99,9 % | 877,2x |
| 1646 | 134. González-Ruiz, Cristián D. y Mijares, Víctor M. (2020): “Los fuertes hacen | Penal | 121924 | 78 | 99,9 % | 1563,1x |
| 1647 | 134. No escapa a la Corte que los despidos, efectuados sin las garantías | Judicial | 144656 | 140 | 99,9 % | 1033,3x |
| 1648 | 135   Ministra señoras Araneda y Egnem; ministros señores Valdés, Silva, Brito y Jacob; abogados integrantes | Judicial | 105809 | 79 | 99,9 % | 1339,4x |
| 1649 | 135. Gowlland-Debbas, Vera (1994): “Security Council Enforcement Action and | Penal | 121924 | 66 | 99,9 % | 1847,3x |
| 1650 | 135. MARCUS, Richard (2014): The right of access to justice. The Experience | Procesal | 96699 | 132 | 99,9 % | 732,6x |
| 1651 | 137      DAVARA FERNÁNDEZ DE MARCOS, Elena: “El Reglamento Europeo de Protección de Datos”. En Derecho | Constitucional | 104063 | 96 | 99,9 % | 1084,0x |
| 1652 | 137      TOP Quillota, rol N° 17-2019, sentencia 17 de abril de 2019, C.9 | Familia | 95131 | 128 | 99,9 % | 743,2x |
| 1653 | 137   CS, rol N° 2837-98, de 3 de septiembre de 1998. Ver otros fallos de la misma Corte Suprema de Justicia | Judicial | 105809 | 153 | 99,9 % | 691,6x |
| 1654 | 137. Grossrieder, Paul: “¿Un porvenir para el derecho internacional humanitario y | Penal | 121924 | 79 | 99,9 % | 1543,3x |
| 1655 | 138. Sobre el principio de igualdad ante la ley y la no discriminación, la | Constitucional | 177323 | 172 | 99,9 % | 1030,9x |
| 1656 | 14 Antecedentes generales sobre esta unidad pueden verse en Defensoría Penal | Penal | 86906 | 58 | 99,9 % | 1498,4x |
| 1657 | 14 Convenio 190 sobre la Violencia y el Acoso de la Organización Internacional | Laboral | 53374 | 55 | 99,9 % | 970,4x |
| 1658 | 14 De manera similar, en sentencia Tribunal Constitucional 783-07, de 31 de agosto | Judicial | 144656 | 126 | 99,9 % | 1148,1x |
| 1659 | 14 En este sentido, resulta interesante la opinión de Cury Urzúa (1986: 226), quien | Penal | 178516 | 152 | 99,9 % | 1174,4x |
| 1660 | 14 Este autor destaca que lo contrario a la notoriedad no es la imposibilidad, sino | Judicial | 150341 | 85 | 99,9 % | 1768,7x |
| 1661 | 14 Juzgado de Letras del Trabajo de Iquique, O-190-2012 del 24 de septiembre de | Laboral | 98828 | 57 | 99,9 % | 1733,8x |
| 1662 | 14 La Ley 21.120 de 2018 originalmente consideraba como causal directa de término | Familia | 123490 | 100 | 99,9 % | 1234,9x |
| 1663 | 14 Poder Judicial, Cuaderno de buenas prácticas para incorporar la perspectiva de | Judicial | 81675 | 58 | 99,9 % | 1408,2x |
| 1664 | 14 Por ello no es del todo acertado entenderla como «la obtención de cualquier | Penal | 178516 | 127 | 99,9 % | 1405,6x |
| 1665 | 14 Rebolledo (2016a: 112) señala que el desvío de precursores químicos no son | Penal | 97633 | 117 | 99,9 % | 834,5x |
| 1666 | 14 Sentencia de la Corte de Apelaciones de Santiago, rol 1.525-2019, 9 de julio de | Familia | 97488 | 65 | 99,9 % | 1499,8x |
| 1667 | 14 Véase «Las mujeres indígenas y sus derechos humanos en las Américas» (OEA/ | Judicial | 60665 | 65 | 99,9 % | 933,3x |
| 1668 | 14.   Ley Nº 19.880. Establece bases de los procedi- | Administrativo | 89720 | 88 | 99,9 % | 1019,5x |
| 1669 | 14. Boletín N° 12.024-11. Proyecto de ley que modifica el decreto | Judicial | 89476 | 100 | 99,9 % | 894,8x |
| 1670 | 14. CASAS, Lidia (2014): “Análisis crítico de la acción de no discriminación | Judicial | 81476 | 70 | 99,9 % | 1163,9x |
| 1671 | 14. Caso “O.B.C”. Rol 70584-16, Corte Suprema (sen- | Judicial | 89476 | 67 | 99,9 % | 1335,5x |
| 1672 | 14. Corte de Apelaciones de Santiago, rol N° 84- | Familia | 100107 | 80 | 99,9 % | 1251,3x |
| 1673 | 14. Cultura organizacional criminógena: aquel tipo de | Penal | 119528 | 80 | 99,9 % | 1494,1x |
| 1674 | 14. Directores del Complejo Hospitalario San José        28. Hugo Aedo Gallardo con Nazar Logística Limita- | Civil | 142015 | 96 | 99,9 % | 1479,3x |
| 1675 | 14. En consecuencia, siendo la última condena del imputado del año | Penal | 194788 | 152 | 99,9 % | 1281,5x |
| 1676 | 14. Formación y capacitación en derechos humanos: Implementación | Constitucional | 177323 | 117 | 99,9 % | 1515,6x |
| 1677 | 14. Hay abundante jurisprudencia. Así, por ejemplo, se ha fallado que ‘si una de las | Civil | 120848 | 144 | 99,9 % | 839,2x |
| 1678 | 14. La protección de los derechos individuales de los menores por lo | Penal | 194788 | 149 | 99,9 % | 1307,3x |
| 1679 | 14. Ley N° 20.077. Reestablece la bonificación fiscal para enferme- | Judicial | 89476 | 79 | 99,9 % | 1132,6x |
| 1680 | 14. Los siguientes asuntos que se susciten entre cónyuges, relativos al régimen patrimonial | Familia | 100107 | 72 | 99,9 % | 1390,4x |
| 1681 | 14. Nulidad de derecho público: sanción de ineficacia | Judicial | 105809 | 109 | 99,9 % | 970,7x |
| 1682 | 14. PONCE DE LEÓN SALUCCI, Sandra (2014): “La | Judicial | 105809 | 94 | 99,9 % | 1125,6x |
| 1683 | 14. Que de acuerdo a las escrituras públicas acompañadas a los autos se encuentra acreditado | Judicial | 79146 | 88 | 99,9 % | 899,4x |
| 1684 | 14. Resolución Exenta N° 3.207 que Instruye sobre | Penal | 72395 | 72 | 99,9 % | 1005,5x |
| 1685 | 14. SANTAMARÍA PASTOR, Juan (1999): Principios | Judicial | 105809 | 71 | 99,9 % | 1490,3x |
| 1686 | 14.2 Responsabilidad por el hecho ajeno; y | Civil | 96458 | 83 | 99,9 % | 1162,1x |
| 1687 | 14.3. La posesión de los bienes raíces | Civil | 36671 | 48 | 99,9 % | 764,0x |
| 1688 | 14.5.2 El forzamiento de la acusación | Penal | 211066 | 109 | 99,9 % | 1936,4x |
| 1689 | 14.908. Para realizar las presentaciones judiciales deberá disponerse de | Familia | 97488 | 89 | 99,9 % | 1095,4x |
| 1690 | 140     Normativa citada | Procesal | 66012 | 42 | 99,9 % | 1571,7x |
| 1691 | 141   FERNÁNDEZ, Miguel Ángel (2003), p. 74. Ver sentencias de la Corte Suprema de los años 1998 y 2000 pro- | Judicial | 105809 | 141 | 99,9 % | 750,4x |
| 1692 | 142      Ver Consejo de Europa: “Recommendation CM/Rec(2016)3 of the Committee of Ministers to member States | Constitucional | 112823 | 66 | 99,9 % | 1709,4x |
| 1693 | 142. En la Convención Americana no se encuentra determinado un concepto | Judicial | 93914 | 102 | 99,9 % | 920,7x |
| 1694 | 142. Henríquez Viñas, Miriam Lorena (2005): “Las transformaciones en el | Penal | 121924 | 76 | 99,9 % | 1604,3x |
| 1695 | 142. MELIS VALENCIA, Christian (2001a), “En torno al | Laboral | 113458 | 92 | 99,9 % | 1233,2x |
| 1696 | 143. En el caso Velásquez Paiz y otros vs. Guatemala, la Corte reiteró | Constitucional | 177323 | 162 | 99,9 % | 1094,6x |
| 1697 | 144      REDESCA y CIDH: “Empresas y Derechos Humanos: Estándares Interamericanos” OEA/Ser.L/V/II CIDH/RE- | Constitucional | 112823 | 68 | 99,9 % | 1659,2x |
| 1698 | 144. En particular, la Corte ha reconocido que los prejuicios personales | Constitucional | 177323 | 150 | 99,9 % | 1182,2x |
| 1699 | 145. Corte Suprema, Carátula reservada (2016): sentencia, 3 octubre 2016, rol Nº | Penal | 121924 | 68 | 99,9 % | 1793,0x |
| 1700 | 145. El Tribunal ya se posicionó anteriormente sobre la importancia de | Constitucional | 177323 | 162 | 99,9 % | 1094,6x |
| 1701 | 1457. Pensamos que, si uno de los contratantes alega y prueba que celebró el contrato | General | 166275 | 145 | 99,9 % | 1146,7x |
| 1702 | 146 Ver Gómez-Jara (2005), p. 142, según el cual en este tipo de modelos “más bien parece tratarse de una | Penal | 119528 | 78 | 99,9 % | 1532,4x |
| 1703 | 146. NEUMANN, Franz L. (1983), Il diritto del lavoro fra      158. RAMÍREZ COLINA, Sulmer Paola (2013), “La | Laboral | 113458 | 111 | 99,9 % | 1022,1x |
| 1704 | 147   GAMONAL C., Sergio y GUIDI MOGGIA, Caterina (2015), Manual del contrato de trabajo, 4ª edición revisada | Laboral | 113458 | 91 | 99,9 % | 1246,8x |
| 1705 | 148   Corte Suprema, 3 de marzo de 2020, Rol Nº 12473-2018. En este caso, un viñedo demanda al Banco BBVA | Civil | 142015 | 163 | 99,9 % | 871,3x |
| 1706 | 1486. En este caso, la compraventa no puede formarse por falta de objeto y por lo | Civil | 153962 | 130 | 99,9 % | 1184,3x |
| 1707 | 149   CS rol N° 5.016-2010, 21 de octubre de 2010 | Familia | 65085 | 74 | 99,9 % | 879,5x |
| 1708 | 149. En lo que respecta a la regulación de los procedimientos de | Judicial | 93914 | 122 | 99,9 % | 769,8x |
| 1709 | 15 Al igual que los acuerdos, toda resolución que fije una pensión de alimentos | Familia | 97488 | 96 | 99,9 % | 1015,5x |
| 1710 | 15 Al respecto, recomendamos leer a Rocío Lorca (2021). «Extrema pobreza y poder | Penal | 86906 | 74 | 99,9 % | 1174,4x |
| 1711 | 15 Calamandrei (1933: 559) dice: «Ciertamente si procuramos llegar hasta la raíz | Judicial | 150341 | 98 | 99,9 % | 1534,1x |
| 1712 | 15 Corte Suprema, rol 58.246-21, del 20 marzo de 2022. En el mismo sentido, con | Penal | 97633 | 109 | 99,9 % | 895,7x |
| 1713 | 15 Desde la entrada en vigor de la Ley 21.515 de 2022 el procedimiento de la Ley | Familia | 123490 | 98 | 99,9 % | 1260,1x |
| 1714 | 15 En este caso, la Contraloría General de la República detectó irregularidades | Penal | 178516 | 107 | 99,9 % | 1668,4x |
| 1715 | 15 Juzgado de Letras del Trabajo de Puerto Montt, RIT T-11-2016, 11 de mayo de | Laboral | 53374 | 58 | 99,9 % | 920,2x |
| 1716 | 15 La actividad concertada protegida o acción concertada está consagrada en la | Laboral | 98828 | 113 | 99,9 % | 874,6x |
| 1717 | 15 N° 6 inciso 2°, que indica que todo acuerdo de los propietarios reunidos en asamblea | Civil | 192585 | 180 | 99,9 % | 1069,9x |
| 1718 | 15 Para más información, véase el preámbulo, artículo 1, 55.c y 62.2 de la CONU | Constitucional | 177323 | 126 | 99,9 % | 1407,3x |
| 1719 | 15 Sentencia Corte de Apelaciones de Valparaíso rol 3876-2001, de 11 de marzo de | Judicial | 144656 | 79 | 99,9 % | 1831,1x |
| 1720 | 15 Sentencia de la Corte Suprema, rol 36.584, 13 de abril de 2016, considerando | Familia | 97488 | 72 | 99,9 % | 1354,0x |
| 1721 | 15 Sentencia de la Corte de Apelaciones de Coyhaique, causa rol 52-2017 (Civil), 3 | Judicial | 89450 | 113 | 99,9 % | 791,6x |
| 1722 | 15 Una relación de la evolución del derecho administrativo sancionador de los | Penal | 178516 | 92 | 99,9 % | 1940,4x |
| 1723 | 15. Boletín N° 12.026-13. Proyecto de ley que crea el beneficio social | Judicial | 89476 | 70 | 99,9 % | 1278,2x |
| 1724 | 15. CA San Miguel, “Cementos Melón”, 17 de abril de | Judicial | 105809 | 137 | 99,9 % | 772,3x |
| 1725 | 15. CASAS BECERRA, Lidia y LAGOS TSCHORNE, Catalina (2014): “Análisis | Judicial | 81476 | 71 | 99,9 % | 1147,5x |
| 1726 | 15. Caso “F.P.M”. Rol 8712-2018, Corte de Apelacio- | Judicial | 89476 | 72 | 99,9 % | 1242,7x |
| 1727 | 15. Denunciar la ocurrencia de todo hecho ilícito acaecido al interior del Condominio, a | Civil | 192585 | 118 | 99,9 % | 1632,1x |
| 1728 | 15. Figura No. 15. Interposición de acciones judiciales por extranjeros | Constitucional | 115835 | 150 | 99,9 % | 772,2x |
| 1729 | 15. Informar, previo a la realización de una actuación judicial acerca | Constitucional | 177323 | 152 | 99,9 % | 1166,6x |
| 1730 | 15. Ley N° 20.032, establece Sistema de Atención | Familia | 100107 | 130 | 99,9 % | 770,1x |
| 1731 | 15. Ley Nº 20.260, que modifica el Libro V del Código | Laboral | 113458 | 111 | 99,9 % | 1022,1x |
| 1732 | 15. MACCHIAVELLO, Guido (1986): Derecho del | Laboral | 100583 | 88 | 99,9 % | 1143,0x |
| 1733 | 15. No es recomendable que un juez(a) pertenezca a una sociedad | Procesal | 94881 | 83 | 99,9 % | 1143,1x |
| 1734 | 15. Observar y cumplir las instrucciones que, en uso de sus facultades | Judicial | 52128 | 72 | 99,9 % | 724,0x |
| 1735 | 15. Orientar y atender presencial y telefónicamente a los usuarios | Judicial | 44331 | 66 | 99,9 % | 671,7x |
| 1736 | 15. comité de los derechos del niño de | Penal | 72395 | 105 | 99,9 % | 689,5x |
| 1737 | 15.1 Sujeto activo de la acción. 15.2 Sujeto pasivo de la acción. 15.3 Caso de | Civil | 96458 | 109 | 99,9 % | 884,9x |
| 1738 | 15.1.1 La fase escrita | Penal | 211066 | 114 | 99,9 % | 1851,5x |
| 1739 | 15.1.2 Actuaciones eventuales del querellante | Penal | 211066 | 119 | 99,9 % | 1773,7x |
| 1740 | 15.2.13 Alcance de la exclusión | Penal | 211066 | 124 | 99,9 % | 1702,1x |
| 1741 | 15.2.14 Pruebas aceptadas | Penal | 211066 | 119 | 99,9 % | 1773,7x |
| 1742 | 15.2.2 Declaración de inicio de la audiencia | Penal | 211066 | 115 | 99,9 % | 1835,4x |
| 1743 | 15.2.3 Exposición de las presentaciones escritas | Penal | 211066 | 115 | 99,9 % | 1835,4x |
| 1744 | 15.2.4 Eventual defensa oral del acusado | Penal | 211066 | 109 | 99,9 % | 1936,4x |
| 1745 | 15.2.5 Posibilidad de salidas alternativas | Penal | 211066 | 120 | 99,9 % | 1758,9x |
| 1746 | 15.2.7 Corrección de vicios formales | Penal | 211066 | 133 | 99,9 % | 1587,0x |
| 1747 | 15.2.8 Control de congruencia | Penal | 211066 | 126 | 99,9 % | 1675,1x |
| 1748 | 150   El comité también formula recomendaciones sobre cualquier cuestión que afecte a las mujeres, a la que | Judicial | 89476 | 106 | 99,9 % | 844,1x |
| 1749 | 150 C. Para condenar el tribunal señaló que el bien jurídico afectado no | Judicial | 78893 | 113 | 99,9 % | 698,2x |
| 1750 | 150. Asimismo, esta Corte ha entendido que la debida protección | Judicial | 93914 | 107 | 99,9 % | 877,7x |
| 1751 | 151. Del mismo modo, de acuerdo a la jurisprudencia de esta | Judicial | 93914 | 111 | 99,9 % | 846,1x |
| 1752 | 152   Ver estado de nuestra jurisprudencia en cuanto al alcance del recurso de amparo económico; si puede ca- | Judicial | 105809 | 149 | 99,9 % | 710,1x |
| 1753 | 152. Al respecto, resulta útil recordar que el principio de interés | Judicial | 93914 | 102 | 99,9 % | 920,7x |
| 1754 | 1526 N° 1 y 2408, puede decirse que cada parte del inmueble hipotecado | Civil | 66868 | 100 | 99,9 % | 668,7x |
| 1755 | 153      Exposición de hechos del fallo de primera instancia del 29º Juzgado Civil de Santiago, causa rol Nº | Constitucional | 112823 | 66 | 99,9 % | 1709,4x |
| 1756 | 153   Un razonamiento es una secuencia de enunciados donde al menos uno desempeña la función de conclusión | Constitucional | 121906 | 144 | 99,9 % | 846,6x |
| 1757 | 153. Por otro lado, en el marco de los casos contenciosos, este | Judicial | 93914 | 117 | 99,9 % | 802,7x |
| 1758 | 154. De conformidad con lo anterior, esta Corte entiende que | Judicial | 93914 | 107 | 99,9 % | 877,7x |
| 1759 | 1547. En conclusión, la prueba de la culpa no se plantea siempre de la misma manera | Civil | 118177 | 174 | 99,9 % | 679,2x |
| 1760 | 155. En el mismo sentido, los principios de Yogyakarta han | Judicial | 93914 | 67 | 99,9 % | 1401,7x |
| 1761 | 156      CESC – U de Chile (2011), p.40.-43 | Familia | 95131 | 63 | 99,9 % | 1510,0x |
| 1762 | 156     Referencias | Laboral | 74025 | 53 | 99,9 % | 1396,7x |
| 1763 | 156. Por último, y como un ejemplo de una buena práctica con | Judicial | 93914 | 94 | 99,9 % | 999,1x |
| 1764 | 1567 N° 9). La condición resolutoria cumplida opera retroactivamente. Así, la | Civil | 118177 | 170 | 99,9 % | 695,2x |
| 1765 | 157      UNIÓN INTERNACIONAL DE TELECOMUNICACIONES. Descripción general de Internet de los objetos. Reco- | Constitucional | 104063 | 118 | 99,9 % | 881,9x |
| 1766 | 157. Existen en el presente caso evidencias numerosas y concurrentes | Judicial | 78893 | 111 | 99,9 % | 710,7x |
| 1767 | 157. Knoops, Geert-Jan Alexander (2004): “International criminal law liability for | Penal | 121924 | 75 | 99,9 % | 1625,7x |
| 1768 | 159 Nº 6 del Código del Trabajo, con ocasión del terremoto que | Laboral | 100583 | 72 | 99,9 % | 1397,0x |
| 1769 | 15; JUSTE y CASTILLO (2002), p. 118; CRAWFORD (2004), pp. 232 y 293; KAPLAN (2004), p. 1909; CASSESE | Penal | 121924 | 102 | 99,9 % | 1195,3x |
| 1770 | 16 Bien se señala que, excepcionalmente, el artículo 238 del Código Penal extiende | Penal | 178516 | 158 | 99,9 % | 1129,8x |
| 1771 | 16 Cabe señalar que con esto no se agotan los problemas de comunicabilidad y de | Penal | 178516 | 126 | 99,9 % | 1416,8x |
| 1772 | 16 Carocca (2000: 203) agrega: «El que sea “notorio” es una cuestión fáctica que | Judicial | 150341 | 105 | 99,9 % | 1431,8x |
| 1773 | 16 Caso Kimel con Argentina, sentencia de 2 de mayo de 2008; caso Usón Ramírez | Judicial | 144656 | 109 | 99,9 % | 1327,1x |
| 1774 | 16 Centro de Medidas Cautelares, rol 7289-2016 sentencia, 12 de diciembre de | Judicial | 82507 | 79 | 99,9 % | 1044,4x |
| 1775 | 16 Corte Interamericana de Derechos Humanos, caso Atala Riffo y niñas versus | Penal | 86906 | 68 | 99,9 % | 1278,0x |
| 1776 | 16 Desde ya puede advertirse una diferencia con apremios ilegítimos de calidad y | Judicial | 78893 | 54 | 99,9 % | 1461,0x |
| 1777 | 16 Dirección del Trabajo, Dictamen Ord. 1389/007 del 8 de abril de 2020, citado | Laboral | 98828 | 100 | 99,9 % | 988,3x |
| 1778 | 16 La referencia al principio de integración lo hacemos con el resguardo de las | Judicial | 62888 | 70 | 99,9 % | 898,4x |
| 1779 | 16 Ley 19.998), para lo cual, el tribunal debe nombrarle un curador | Familia | 100107 | 66 | 99,9 % | 1516,8x |
| 1780 | 16 N° 3). Según la Guía del Convenio, “el artículo 16(3) estipula | Judicial | 134465 | 120 | 99,9 % | 1120,5x |
| 1781 | 16 Observatorio Niñez y Adolescencia [ONA] (2020). Violencia Estatal contra | Judicial | 78893 | 65 | 99,9 % | 1213,7x |
| 1782 | 16 Recomendaciones sobre Lenguaje Claro que tuvieron por objeto | Judicial | 79146 | 106 | 99,9 % | 746,7x |
| 1783 | 16 Sentencia de la Corte Suprema, rol 16.960-2018, 30 de julio 2018, prevención | Familia | 97488 | 93 | 99,9 % | 1048,3x |
| 1784 | 16 Sentencia de la Corte de Apelaciones de Coihaique, 04 de junio de 2021, rol | Judicial | 150341 | 80 | 99,9 % | 1879,3x |
| 1785 | 16 Una de las empresas que participaba de las licitaciones de Chiledeportes era | Penal | 178516 | 161 | 99,9 % | 1108,8x |
| 1786 | 16.   Braithwaite, John (1982a): “Challenging Just | Penal | 119528 | 100 | 99,9 % | 1195,3x |
| 1787 | 16.   Ley Nº 19.862. Establece Registros de las Perso- | Administrativo | 89720 | 113 | 99,9 % | 794,0x |
| 1788 | 16. Asesorar y canalizar inquietudes y necesidades de los Consejos | Constitucional | 177323 | 101 | 99,9 % | 1755,7x |
| 1789 | 16. Es necesario actuar con cautela y considerar la posibilidad de | Procesal | 94881 | 119 | 99,9 % | 797,3x |
| 1790 | 16. Implementación y difusión de acciones comprometidas en el Plan | Constitucional | 177323 | 106 | 99,9 % | 1672,9x |
| 1791 | 16. La amenaza, en cambio, requiere el empleo de fuerza moral. En este sentido se | General | 166275 | 184 | 99,9 % | 903,7x |
| 1792 | 16. Ley N° 20.607, que modifica el Código del Traba- | Laboral | 113458 | 100 | 99,9 % | 1134,6x |
| 1793 | 16. Manuel Eugenio Elgueta Ariztía con Pizarreño S.A     30. Jacqueline González Cantillana y otros con | Civil | 142015 | 96 | 99,9 % | 1479,3x |
| 1794 | 16. Rol 24.668-2020 Corte Suprema y rol Nº 339- | Judicial | 105809 | 117 | 99,9 % | 904,4x |
| 1795 | 16. Tribunal Constitucional de Chile. Roles: STC 1732 | Judicial | 89476 | 80 | 99,9 % | 1118,5x |
| 1796 | 16.1      Conceptos de accidente del trabajo | Laboral | 100583 | 52 | 99,9 % | 1934,3x |
| 1797 | 16.12. Acuerdo de pago “serio y suficiente” de las pensiones de alimentos | Familia | 81198 | 44 | 99,9 % | 1845,4x |
| 1798 | 16.14. Obligaciones de consulta, retención y pago, en las operaciones de | Familia | 81198 | 58 | 99,9 % | 1400,0x |
| 1799 | 16.15. Obligaciones de consulta, retención y pago, en los procedimientos | Familia | 81198 | 41 | 99,9 % | 1980,4x |
| 1800 | 16.16. Obligaciones de consulta, retención y pago, en los procedimientos | Familia | 81198 | 67 | 99,9 % | 1211,9x |
| 1801 | 16.18. Sanciones para quienes no cumplan las obligaciones previstas en el | Familia | 81198 | 44 | 99,9 % | 1845,4x |
| 1802 | 16.2      Las obligaciones del empleador en el | Laboral | 100583 | 80 | 99,9 % | 1257,3x |
| 1803 | 16.20. Restricciones para comprar y adquirir ciertos bienes por el deudor | Familia | 81198 | 46 | 99,9 % | 1765,2x |
| 1804 | 16.22. Obligación de la entidad que deba practicar una inscripción en el | Familia | 81198 | 70 | 99,9 % | 1160,0x |
| 1805 | 16.23. Sanciones en caso de infringir lo dispuesto en los incisos 1º a 4º del | Familia | 81198 | 83 | 99,9 % | 978,3x |
| 1806 | 16.28. Restricción para la obtención de beneficios económicos que otorguen | Familia | 81198 | 70 | 99,9 % | 1160,0x |
| 1807 | 16.29. Imposibilidad de adjudicación de programas o instrumentos | Familia | 81198 | 49 | 99,9 % | 1657,1x |
| 1808 | 16.30. Obligación que se impone a funcionarios públicos y a personas que | Familia | 81198 | 49 | 99,9 % | 1657,1x |
| 1809 | 16.32. Directores y gerentes generales de sociedades anónimas abiertas con | Familia | 81198 | 42 | 99,9 % | 1933,3x |
| 1810 | 16.33. Deber de consulta y de información que se le impone al oficial del | Familia | 81198 | 58 | 99,9 % | 1400,0x |
| 1811 | 16.34. Comisión de Coordinación y Evaluación del Nuevo Sistema de | Familia | 81198 | 52 | 99,9 % | 1561,5x |
| 1812 | 16.35. Incidencia de la inscripción en el Registro de Deudores, en la | Familia | 81198 | 57 | 99,9 % | 1424,5x |
| 1813 | 16.36. Incidencia de la inscripción en el Registro de Deudores, en la salida de | Familia | 81198 | 54 | 99,9 % | 1503,7x |
| 1814 | 16.37. Incidencia de la inscripción en el Registro de Deudores,                                  en | Familia | 81198 | 87 | 99,9 % | 933,3x |
| 1815 | 16.4     Daño moral. Acción, competencia, sujetos | Laboral | 100583 | 85 | 99,9 % | 1183,3x |
| 1816 | 16.4. Funciones del Servicio de Registro Civil e Identificación en lo que | Familia | 81198 | 105 | 99,9 % | 773,3x |
| 1817 | 160 CA Coyhaique rol 13-2006, de 15 de febrero de 2007, confirmado por CS rol 1143-2007, de 15 de marzo de | Judicial | 105809 | 154 | 99,9 % | 687,1x |
| 1818 | 160 La CIDH entiende que esta discriminación puede manifestarse de manera directa (intencional o “por objeto”) | Judicial | 89476 | 91 | 99,9 % | 983,3x |
| 1819 | 160. Lachs, Manfred (1968): “The Law of Treaties (Some General Reflections | Penal | 121924 | 96 | 99,9 % | 1270,0x |
| 1820 | 160. Los Estados cuentan con la posibilidad de establecer y | Judicial | 93914 | 110 | 99,9 % | 853,8x |
| 1821 | 162   LANATA FUENZALIDA, Gabriela (2006), Contrato individual de trabajo, Universidad de Concepción, Colección | Laboral | 113458 | 149 | 99,9 % | 761,5x |
| 1822 | 162 CT (Ley Bustos): el plazo de prescripción es de seis meses | Laboral | 100583 | 127 | 99,9 % | 792,0x |
| 1823 | 162. RIVERO, Jean y SAVATIER, Jean (1993), Droit du | Laboral | 113458 | 75 | 99,9 % | 1512,8x |
| 1824 | 163. Corte Suprema, Sardy c. Fisco de Chile (2016): sentencia 29 marzo 2016, rol | Penal | 121924 | 68 | 99,9 % | 1793,0x |
| 1825 | 164. RODRÍGUEZ-PIÑERO, Miguel (2004), “Libertad | Laboral | 113458 | 84 | 99,9 % | 1350,7x |
| 1826 | 166. Llanos Mansilla, Hugo (2007): II Teoría y Práctica del Derecho Internacional | Penal | 121924 | 71 | 99,9 % | 1717,2x |
| 1827 | 168. Llanos Mansilla, Hugo (2011): IV Teoría y Práctica del Derecho Internacional | Penal | 121924 | 70 | 99,9 % | 1741,8x |
| 1828 | 169   Esto es importante, porque la Ley Nº 20.422 sólo usa la palabra “consecuencia”. Más adelante se trata | Constitucional | 121906 | 61 | 99,9 % | 1998,5x |
| 1829 | 169. Con todo, hay todavía inconvenientes prácticos. Por ejemplo, y | Judicial | 134465 | 122 | 99,9 % | 1102,2x |
| 1830 | 169. Corte Suprema, Pereira y otros c. Luzoro y otro (2017): sentencia de casa- | Penal | 121924 | 68 | 99,9 % | 1793,0x |
| 1831 | 169. Para la Corte, en el presente caso ha quedado demostrado | Administrativo | 89720 | 113 | 99,9 % | 794,0x |
| 1832 | 17 Además, falta regulación sobre conflictos de interés e inhabilitaciones que | Penal | 178516 | 105 | 99,9 % | 1700,2x |
| 1833 | 17 Agrega también: «Las nociones que componen este patrimonio adquieren así | Judicial | 150341 | 144 | 99,9 % | 1044,0x |
| 1834 | 17 Con todo, la puesta en marcha de un sistema automatizado de liquidación de | Familia | 97488 | 109 | 99,9 % | 894,4x |
| 1835 | 17 Consejo de Derechos Humanos de las Naciones Unidas, «Información básica | Judicial | 81675 | 52 | 99,9 % | 1570,7x |
| 1836 | 17 Cortes de | Procesal | 94881 | 75 | 99,9 % | 1265,1x |
| 1837 | 17 Dictada el año 2005, relativa a «La igualdad de derechos del hombre y la mujer | Judicial | 81675 | 62 | 99,9 % | 1317,3x |
| 1838 | 17 Matus y Ramírez (2019: 514). Comparten este predicamento García (2013: 45) y | Penal | 97633 | 55 | 99,9 % | 1775,1x |
| 1839 | 17 Otra cuestión ocurre con la reciente incorporación del femicidio no íntimo en | Judicial | 78893 | 72 | 99,9 % | 1095,7x |
| 1840 | 17 Referidos a la determinación de la existencia del menoscabo económico, la | Familia | 123490 | 70 | 99,9 % | 1764,1x |
| 1841 | 17 Sentencia ministro en visita extraordinaria Alfredo Pfeiffer, rol 39.800-91, del 27 | Judicial | 62514 | 88 | 99,9 % | 710,4x |
| 1842 | 17 Véanse Matus y Ramírez (2019: 504), Politoff, Matus y Ramírez (2009: 585); Ruiz | Penal | 97633 | 61 | 99,9 % | 1600,5x |
| 1843 | 17 Ya fue dicho que el artículo 368 del Código Penal español de 1995 señala los | Penal | 97633 | 94 | 99,9 % | 1038,6x |
| 1844 | 17.   Ley N° 20.084, establece un Sistema de Respon- | Familia | 100107 | 91 | 99,9 % | 1100,1x |
| 1845 | 17.   Ley N° 20.940 de 2016, que Moderniza el Siste- | Laboral | 113458 | 92 | 99,9 % | 1233,2x |
| 1846 | 17.   Rodrigo Erazo Reyes con Treizman Sacks Lucy        31. Marco Antonio Jaramillo Amoyao con Fisco de | Civil | 142015 | 83 | 99,9 % | 1711,0x |
| 1847 | 17. Boletín N° 12.148-11. Proyecto de ley que establece derechos en | Judicial | 89476 | 75 | 99,9 % | 1193,0x |
| 1848 | 17. Corregir devoluciones de proyectos de resolución realizados por | Judicial | 52128 | 78 | 99,9 % | 668,3x |
| 1849 | 17. Cuando un juez(a) tiene una relación sentimental con una persona | Procesal | 94881 | 96 | 99,9 % | 988,3x |
| 1850 | 17. Informar de manera oportuna y clara a la persona mayor sobre | Constitucional | 177323 | 117 | 99,9 % | 1515,6x |
| 1851 | 17. Ley N° 20.348. Resguarda el derecho a la igualdad en las remu- | Judicial | 89476 | 48 | 99,9 % | 1864,1x |
| 1852 | 17. Realizar visitas bimensuales a la secretaría del tribunal, con el | Judicial | 52128 | 76 | 99,9 % | 685,9x |
| 1853 | 17. Se presume que los menores detenidos bajo arresto o en espera de | Penal | 194788 | 166 | 99,9 % | 1173,4x |
| 1854 | 17. Toda otra materia que la ley les encomiende (por ejemplo, arts. 13 y 18 de la Ley | Familia | 190697 | 223 | 99,9 % | 855,1x |
| 1855 | 17.1.2 Presupuestos o condiciones de | Penal | 211066 | 126 | 99,9 % | 1675,1x |
| 1856 | 17.1.2.1 La solicitud del Ministerio Público | Penal | 211066 | 133 | 99,9 % | 1587,0x |
| 1857 | 17.1.2.2 La aceptación por parte del acusado | Penal | 211066 | 124 | 99,9 % | 1702,1x |
| 1858 | 17.1.2.3 La conformidad manifestada expresamente por el | Penal | 211066 | 119 | 99,9 % | 1773,7x |
| 1859 | 17.1.3 La aceptación de la solicitud de procedimiento | Penal | 211066 | 149 | 99,9 % | 1416,6x |
| 1860 | 17.1.6 Resolución de la solicitud (art. 410 CPP) | Penal | 211066 | 133 | 99,9 % | 1587,0x |
| 1861 | 17.1.7 Tramitación del procedimiento | Penal | 211066 | 106 | 99,9 % | 1991,2x |
| 1862 | 17.2.2 El conocimiento y fallo de las faltas | Penal | 211066 | 153 | 99,9 % | 1379,5x |
| 1863 | 17.3.2 Tramitación | Penal | 211066 | 135 | 99,9 % | 1563,5x |
| 1864 | 17.3.3 La resolución del juez de garantía | Penal | 211066 | 119 | 99,9 % | 1773,7x |
| 1865 | 17.3.6 La acción civil en el procedimiento monitorio | Penal | 211066 | 119 | 99,9 % | 1773,7x |
| 1866 | 17.5.1 Forma de pago de las prestaciones del FCS | Laboral | 100583 | 101 | 99,9 % | 995,9x |
| 1867 | 170   En esta materia, revisar causas: Rol C-20750-2012 del 22º Juzgado de Letras de Santiago; Rol C-41-2013 | Judicial | 89476 | 70 | 99,9 % | 1278,2x |
| 1868 | 170   No se refiere a personas con discapacidad sino a personas lisiadas, lo que es un problema lingüístico en | Constitucional | 121906 | 145 | 99,9 % | 840,7x |
| 1869 | 170 N° 6 del mismo texto legal, esto es, le reprocha al fallo haber omitido la decisión del | Civil | 192585 | 175 | 99,9 % | 1100,5x |
| 1870 | 170. El Tribunal estima que el derecho a conocer la verdad tiene | Administrativo | 89720 | 117 | 99,9 % | 766,8x |
| 1871 | 171. Corte Suprema, Tapia y otros c. Moren y otros (2017): sentencia 10 abril | Penal | 121924 | 65 | 99,9 % | 1875,8x |
| 1872 | 171. En consideración del deber del Estado de otorgar la nacionalidad | Penal | 72395 | 104 | 99,9 % | 696,1x |
| 1873 | 172. SEIFERT, Achim (2012), “L’effet horizontal des | Laboral | 113458 | 91 | 99,9 % | 1246,8x |
| 1874 | 1725, n° 5°”.25 | Familia | 136567 | 81 | 99,9 % | 1686,0x |
| 1875 | 1725. La expresión “devengar”, significa “adquirir derecho a alguna percepción o | Familia | 136567 | 167 | 99,9 % | 817,8x |
| 1876 | 1727 N° 2 del Código Civil, que reza: “No obstante lo dispuesto en el art. 1725 no | Familia | 136567 | 153 | 99,9 % | 892,6x |
| 1877 | 173.   Matus Acuña, Jean Pierre (2006): “Informe pericial ante CtIDH sobre apli- | Penal | 121924 | 81 | 99,9 % | 1505,2x |
| 1878 | 173. SINGER, Reinhard (2007), “Direitos fundamentais | Laboral | 113458 | 92 | 99,9 % | 1233,2x |
| 1879 | 1736 Nº 2, respecto de la sociedad conyugal). La ratificación, que como sabemos | Familia | 136567 | 135 | 99,9 % | 1011,6x |
| 1880 | 174. SUPIOT, Alain (1996), Crítica del derecho del | Laboral | 113458 | 83 | 99,9 % | 1367,0x |
| 1881 | 175   Cámara de Diputados (2019). Boletín 11.791-13 | Judicial | 89476 | 61 | 99,9 % | 1466,8x |
| 1882 | 175   GAMONAL C., Sergio (2004b), “La Cibervigilancia dentro de la empresa: comentario a una sentencia de la | Laboral | 113458 | 83 | 99,9 % | 1367,0x |
| 1883 | 1750. Se comprenden también en este grupo las deudas propia- | Familia | 123490 | 174 | 99,9 % | 709,7x |
| 1884 | 1757. En las que correspondían a la enseñanza jurídica, se designó a los siguientes | General | 129559 | 183 | 99,9 % | 708,0x |
| 1885 | 176.   Medina Quiroga, Cecilia (1994): “El Derecho Internacional de los Derechos | Penal | 121924 | 78 | 99,9 % | 1563,1x |
| 1886 | 177. Sin perjuicio de su importancia trascendental, la Corte también | Judicial | 89476 | 104 | 99,9 % | 860,3x |
| 1887 | 179     Referencias | Familia | 97488 | 66 | 99,9 % | 1477,1x |
| 1888 | 18       GURREA MARTÍNEZ, A. (2018): El Derecho concursal en España: Problemas estructurales y propuestas de | Judicial | 64632 | 67 | 99,9 % | 964,7x |
| 1889 | 18   BCN (1998), disponible en https://www.bcn.cl/obtienearchivo?id=recursoslegales/10221.3/4231/1/HL19585.pdf | Familia | 65085 | 67 | 99,9 % | 971,4x |
| 1890 | 18 Conclusiones del abogado general Pedro Cruz Villalón presentadas el 26 de | Judicial | 144656 | 110 | 99,9 % | 1315,1x |
| 1891 | 18 Consejo de Derechos Humanos de las Naciones Unidas, «Información básica | Judicial | 81675 | 52 | 99,9 % | 1570,7x |
| 1892 | 18 Esta encuesta estuvo dirigida a personas mayores de 20 años con algún tipo | Laboral | 98828 | 83 | 99,9 % | 1190,7x |
| 1893 | 18 Extracto de los argumentos expuestos por la defensa en su recurso de nulidad a | Judicial | 62514 | 54 | 99,9 % | 1157,7x |
| 1894 | 18 La Corte de Apelaciones de Concepción, en autos civiles rol 1.517-2019, sobre | Judicial | 87950 | 120 | 99,9 % | 732,9x |
| 1895 | 18 La familia es el lugar en que las personas conocen las normas sociales y sus | Familia | 97488 | 80 | 99,9 % | 1218,6x |
| 1896 | 18 Laudan (2013: 61) va más allá con la crítica: sostiene que el estándar de la duda | Judicial | 150341 | 91 | 99,9 % | 1652,1x |
| 1897 | 18 Obsérvese que la Corte Suprema, mediante Acta número 304-2008, de 23 de | Judicial | 144656 | 178 | 99,9 % | 812,7x |
| 1898 | 18 Proyecto de ley presentado en abril de 2021 que moderniza el nombramiento | Penal | 178516 | 120 | 99,9 % | 1487,6x |
| 1899 | 18 Sentencia de la Corte de Apelaciones de Coyhaique, rol 31-2009, 28 de abril de | Penal | 178516 | 156 | 99,9 % | 1144,3x |
| 1900 | 18 Sobre la coexistencia entre prueba reglada y prueba no reglada y las técnicas | Procesal | 86112 | 59 | 99,9 % | 1459,5x |
| 1901 | 18 Tribunal Constitucional Español, Sentencia causa 224/1999, 13 de diciembre de | Laboral | 53374 | 53 | 99,9 % | 1007,1x |
| 1902 | 18 Véase la Observación General número 4 (párrafo 22), la Observación General | Penal | 86906 | 94 | 99,9 % | 924,5x |
| 1903 | 18.   Campaña “JUSTICIA DE GENERO” - La Defensa - Fundación AVON y | Familia | 95131 | 58 | 99,9 % | 1640,2x |
| 1904 | 18. Boletín N° 12.335-11. Proyecto de ley que modifica la Ley N° | Judicial | 89476 | 83 | 99,9 % | 1078,0x |
| 1905 | 18. DFL Nº 2/1996, fija el texto refundido, coordinado y sistematizado del | Constitucional | 121906 | 80 | 99,9 % | 1523,8x |
| 1906 | 18. Deber de advertencia de la peligrosidad: mandato | Penal | 119528 | 91 | 99,9 % | 1313,5x |
| 1907 | 18. Estado de Chile con Minimal Enterprises Com-         32. John Durson Wagner y otros con Luciano Basauri | Civil | 142015 | 98 | 99,9 % | 1449,1x |
| 1908 | 18. Evaluación final del Plan de Acción Nacional Derechos Humanos | Constitucional | 177323 | 161 | 99,9 % | 1101,4x |
| 1909 | 18. Las condiciones de detención de un menor que no haya sido juzga- | Penal | 194788 | 196 | 99,9 % | 993,8x |
| 1910 | 18. Ley Nº 20.379. Aprueba reglamento del subsis- | Judicial | 89476 | 115 | 99,9 % | 778,1x |
| 1911 | 18. Supervigilar el adecuado desarrollo de las labores del tribunal, en | Judicial | 52128 | 71 | 99,9 % | 734,2x |
| 1912 | 18.1      Alcances del artículo 184 CT y la | Laboral | 100583 | 66 | 99,9 % | 1524,0x |
| 1913 | 18.2.1 La prueba testimonial | Penal | 211066 | 144 | 99,9 % | 1465,7x |
| 1914 | 18.2.10 Las palabras finales del artículo 338 del CPP | Penal | 211066 | 140 | 99,9 % | 1507,6x |
| 1915 | 18.2.2 La procedencia del informe pericial | Penal | 211066 | 137 | 99,9 % | 1540,6x |
| 1916 | 18.2.3 Lectura de apoyo de memoria en el juicio oral | Penal | 211066 | 146 | 99,9 % | 1445,7x |
| 1917 | 18.2.3 Otros medios de prueba (323 CPP) | Penal | 211066 | 118 | 99,9 % | 1788,7x |
| 1918 | 18.2.5 Prueba nueva y prueba sobre prueba (336 CPP) | Penal | 211066 | 139 | 99,9 % | 1518,5x |
| 1919 | 18.2.6 Declaración del acusado como medio de defensa | Penal | 211066 | 123 | 99,9 % | 1716,0x |
| 1920 | 18.2.8 La declaración de los peritos | Penal | 211066 | 126 | 99,9 % | 1675,1x |
| 1921 | 18.2.9 Interrogatorios y contrainterrogatorios | Penal | 211066 | 133 | 99,9 % | 1587,0x |
| 1922 | 18.216. Transcurrido el plazo previsto en el inciso anterior sin que el imputado | Penal | 211066 | 167 | 99,9 % | 1263,9x |
| 1923 | 18.287. Pues bien, esta última ley, en su art. 9º previene que “El juez será competente | Civil | 192585 | 210 | 99,9 % | 917,1x |
| 1924 | 18.3     Sanciones aplicables por incumplimiento | Laboral | 100583 | 54 | 99,9 % | 1862,6x |
| 1925 | 18.3.7 Contenido de la sentencia penal | Penal | 211066 | 135 | 99,9 % | 1563,5x |
| 1926 | 180. La Corte considera que en caso de violaciones de derechos | Administrativo | 89720 | 97 | 99,9 % | 924,9x |
| 1927 | 1811. En tal sentido, un fallo de la Corte de Talca, de 17 de marzo de 1914, puntualiza | Civil | 153962 | 218 | 99,9 % | 706,2x |
| 1928 | 182 BENALCÁZAR, Isabelle De (2003), Droit du travail et nouvelles technologies, Paris, Montchrestien Gualino | Laboral | 113458 | 62 | 99,9 % | 1830,0x |
| 1929 | 183   ÁLVAREZ VALENZUELA, Daniel (2004), “Inviolabilidad de las comunicaciones electrónicas”, Revista Chilena | Laboral | 113458 | 96 | 99,9 % | 1181,9x |
| 1930 | 184   En fallo del TTA de Magallanes, de 25 de mayo de 2011, se declaró que no podía acogerse a tramitación la | Judicial | 105809 | 148 | 99,9 % | 714,9x |
| 1931 | 184. Asimismo, se podrá cautelar la demanda civil, solicitando alguna de | Penal | 211066 | 170 | 99,9 % | 1241,6x |
| 1932 | 188. WALKER ERRÁZURIZ, Francisco (2003), Derecho           12. Ley Nº 20.123, que regula el trabajo en régimen | Laboral | 113458 | 118 | 99,9 % | 961,5x |
| 1933 | 189   CA Valdivia, rol N° 89-2012, 24 de julio de 2012 | Familia | 65085 | 88 | 99,9 % | 739,6x |
| 1934 | 189   Un comentario de este fallo desde la perspectiva del principio de protección en: ARELLANO ORTIZ, Pablo y | Laboral | 113458 | 163 | 99,9 % | 696,1x |
| 1935 | 1899. Postula que la noción de causa es ajena al derecho romano y además falsa e | General | 166275 | 208 | 99,9 % | 799,4x |
| 1936 | 19 Adoptada por la Asamblea General de las Naciones Unidas en Nueva York el 20 | Penal | 86906 | 52 | 99,9 % | 1671,3x |
| 1937 | 19 Caso Castañeda Gutman con Estados Unidos Mexicanos, sentencia de 6 de | Judicial | 144656 | 83 | 99,9 % | 1742,8x |
| 1938 | 19 Comenta Tomasello que este sistema difiere del contemplado en el proyecto del | Familia | 123490 | 109 | 99,9 % | 1132,9x |
| 1939 | 19 Comisión Interamericana de Derechos Humanos, «Relatoría Especial sobre los | Judicial | 81675 | 55 | 99,9 % | 1485,0x |
| 1940 | 19 Como explican García y Contreras (2013: 235) el Tribunal Constitucional ha | Judicial | 144656 | 101 | 99,9 % | 1432,2x |
| 1941 | 19 Dingel y Neiman, en un estudio realizado en abril de 2020, afirmaron que el | Laboral | 98828 | 109 | 99,9 % | 906,7x |
| 1942 | 19 El autor menciona como ejemplo —mirándolos desde el cohecho del particular | Penal | 178516 | 205 | 99,9 % | 870,8x |
| 1943 | 19 En abono de lo expuesto, tras la reforma de la Ley 20.286 incluso se entrega la | Procesal | 86112 | 120 | 99,9 % | 717,6x |
| 1944 | 19 En este sentido, Cohen considera: «In fact, over a lifetime, most people tacitly | Judicial | 150341 | 100 | 99,9 % | 1503,4x |
| 1945 | 19 Esta exclusión también se contempla en la vejación injusta del artículo 255, que | Judicial | 78893 | 61 | 99,9 % | 1293,3x |
| 1946 | 19 La tesis es desarrollada a lo largo de su obra El derecho de familia de 1947, a su | Familia | 123490 | 65 | 99,9 % | 1899,8x |
| 1947 | 19 No debe olvidarse que otro desafío pendiente relacionado se refiere a asegurar | Penal | 178516 | 170 | 99,9 % | 1050,1x |
| 1948 | 19 N° 12, referente al derecho que tiene todo ciudadano de este | Laboral | 113458 | 120 | 99,9 % | 945,5x |
| 1949 | 19 N° 16 de nuestra Carta Fundamental, por cuanto la garantía a no | Laboral | 113458 | 101 | 99,9 % | 1123,3x |
| 1950 | 19 N° 24 de la Constitución); acción por desconocimiento o privación de la nacionalidad | Judicial | 105809 | 133 | 99,9 % | 795,6x |
| 1951 | 19 N° 24 inc. 2° y 20 de nuestra Constitución Política, art. 582 del Código Civil y art. 9 del | Civil | 192585 | 111 | 99,9 % | 1735,0x |
| 1952 | 19 N°6 de la Constitución, en el sentido que toda creencia religiosa | Judicial | 81476 | 85 | 99,9 % | 958,5x |
| 1953 | 19 Nº 3, como el procedimiento mediante el cual el requirente | Penal | 211066 | 123 | 99,9 % | 1716,0x |
| 1954 | 19 Nº 7 letra i). Jorge Malem señala que el error judicial implica la existencia | Constitucional | 121906 | 123 | 99,9 % | 991,1x |
| 1955 | 19 Para más información, véase Schindler (1979: 3): «El derecho internacional | Constitucional | 177323 | 94 | 99,9 % | 1886,4x |
| 1956 | 19 Primer Juzgado de Letras del Trabajo de Santiago, RIT T-12- 2015, 24 de abril de | Laboral | 53374 | 59 | 99,9 % | 904,6x |
| 1957 | 19 Se ha resuelto que «la notificación personal puede usarse en todo caso, aun en | Judicial | 89450 | 79 | 99,9 % | 1132,3x |
| 1958 | 19 Sentencia de la Corte de Apelaciones de Valparaíso, 04 de febrero de 2022, rol | Judicial | 150341 | 91 | 99,9 % | 1652,1x |
| 1959 | 19 Sentencia del Tribunal Constitucional 2856, considerando sexto. En el mismo | Judicial | 144656 | 84 | 99,9 % | 1722,1x |
| 1960 | 19 Véase «Informe Núm. 138/18, Petición 687-11. Solución Amistosa G.B.B. y | Judicial | 60665 | 59 | 99,9 % | 1028,2x |
| 1961 | 19.   Eugenio Domínguez Delpiano y otro con René         33. José Ibáñez Castillo con Instituto Hijas de San | Civil | 142015 | 94 | 99,9 % | 1510,8x |
| 1962 | 19.   RUAY, Francisco (2018): “Simulación y subter- | Laboral | 100583 | 94 | 99,9 % | 1070,0x |
| 1963 | 19. Boletín No 12.338-34. Proyecto de ley que modifica el Código | Judicial | 89476 | 72 | 99,9 % | 1242,7x |
| 1964 | 19. Criterios que sirven para definir quién es la Corte de Apelaciones habilitada para conocer | Judicial | 105809 | 158 | 99,9 % | 669,7x |
| 1965 | 19. Curso E-learning “Curso de inducción a las políticas proequidad | Constitucional | 177323 | 146 | 99,9 % | 1214,5x |
| 1966 | 19. Deber de gestión de riesgos: deber de dirección y | Penal | 119528 | 74 | 99,9 % | 1615,2x |
| 1967 | 19. Desarrollar la Planificación Ecológica para 36 municipios de las | Constitucional | 177323 | 131 | 99,9 % | 1353,6x |
| 1968 | 19. Implementación de la Política Nacional de la Lectura y el Libro | Constitucional | 177323 | 101 | 99,9 % | 1755,7x |
| 1969 | 19. Principio de Apertura: Toda información en poder | Administrativo | 89720 | 68 | 99,9 % | 1319,4x |
| 1970 | 19. Si constare en el proceso que en contra del alimentante su hubiere decretado dos veces alguno de los | Familia | 136567 | 143 | 99,9 % | 955,0x |
| 1971 | 19.1.1 Mediación | Laboral | 100583 | 126 | 99,9 % | 798,3x |
| 1972 | 19.1.2 Negociación | Laboral | 100583 | 94 | 99,9 % | 1070,0x |
| 1973 | 19.1.3 Conciliación | Laboral | 100583 | 81 | 99,9 % | 1241,8x |
| 1974 | 19.2 En cada caso, las medidas de resarcimiento con arreglo | Constitucional | 112823 | 97 | 99,9 % | 1163,1x |
| 1975 | 19.4 Los órganos judiciales y/o los organismos pertinentes | Constitucional | 112823 | 100 | 99,9 % | 1128,2x |
| 1976 | 19.537. En la especie, la misiva que se viene analizando, es un reconocimiento por parte | Civil | 192585 | 210 | 99,9 % | 917,1x |
| 1977 | 19.6 El ordenamiento jurídico interno garantiza, mediante | Constitucional | 112823 | 92 | 99,9 % | 1226,3x |
| 1978 | 19.966. De esa forma, aunque la mediación fracase, la requirente no | Civil | 142015 | 72 | 99,9 % | 1972,4x |
| 1979 | 190   VALDÉS PRIETO, Domingo, Exposición ante las Comisiones de la Cámara de Diputados. Historia de la Ley N° | Judicial | 105809 | 122 | 99,9 % | 867,3x |
| 1980 | 1900 CC)                  preso (art. 187 | Familia | 65085 | 61 | 99,9 % | 1067,0x |
| 1981 | 191   COUSO SALAS, Jaime (2018), “Relevancia penal de la intromisión del empleador en los correos electrónicos | Laboral | 113458 | 106 | 99,9 % | 1070,4x |
| 1982 | 1912. Es el propio Georgi quien en la 7ª edición de su obra dice: ‘nos consideramos | Civil | 118177 | 130 | 99,9 % | 909,1x |
| 1983 | 192. SORABJI, John, (2013): Prospects for proportionality: Jackson | Procesal | 96699 | 135 | 99,9 % | 716,3x |
| 1984 | 1938. Se sintetiza esta corriente en los siguientes términos: “Están inhabilitados para | General | 166275 | 193 | 99,9 % | 861,5x |
| 1985 | 194.   Nogueira Alcalá, Humberto (1993): “Los derechos humanos en el derecho | Penal | 121924 | 85 | 99,9 % | 1434,4x |
| 1986 | 1943. Sin embargo, nada se dijo en esta oportunidad, acerca de la posibilidad de liquidar la sociedad | Familia | 136567 | 149 | 99,9 % | 916,6x |
| 1987 | 195     Varios de los significados de términos que incluye | Judicial | 105809 | 91 | 99,9 % | 1162,7x |
| 1988 | 195.   Nogueira Alcalá, Humberto (1996): “Los tratados internacionales en el orde- | Penal | 121924 | 71 | 99,9 % | 1717,2x |
| 1989 | 1966. El vacío de la Carta en cuanto a no contener una enumeración | Constitucional | 177323 | 137 | 99,9 % | 1294,3x |
| 1990 | 1968 Nº 2 en relación con el art. 1902 del Código Civil español: “Art. 1968. Prescriben | Civil | 96458 | 115 | 99,9 % | 838,8x |
| 1991 | 1969. Luego, ninguno de estos instrumentos internacionales reconoce | Constitucional | 177323 | 118 | 99,9 % | 1502,7x |
| 1992 | 197. El Tribunal también ha establecido que el artículo 13 de la | Administrativo | 89720 | 109 | 99,9 % | 823,1x |
| 1993 | 198   Tribunal Europeo de Derechos Humanos, TEDH/2017/61, ECLI:CE:ECHR:2017:0905JUD006149608, de 5 de | Laboral | 113458 | 61 | 99,9 % | 1860,0x |
| 1994 | 1992. En su artículo 26 establece la existencia de un asiento de | Constitucional | 121906 | 68 | 99,9 % | 1792,7x |
| 1995 | 1999 Segundo Protocolo de la Convención de la Haya para la protección de los | Penal | 121924 | 61 | 99,9 % | 1998,8x |
| 1996 | 1999. Este cuerpo legal ha permitido que puedan gozar del estatuto de | Familia | 123490 | 163 | 99,9 % | 757,6x |
| 1997 | 1999. La llamada “Ley de Filiación”, supuso la reforma más profunda al Código Civil en | Familia | 190697 | 132 | 99,9 % | 1444,7x |
| 1998 | 1° CC)           1° CC)                                      2 y 3 CC) | Familia | 65085 | 71 | 99,9 % | 916,7x |
| 1999 | 2        Específicamente el artículo nace como una forma de reacción de Samuel D. Warren, adinerado empresario | Constitucional | 104063 | 137 | 99,9 % | 759,6x |
| 2000 | 2 A diferencia de lo previsto en la nulidad procesal en el CPP, cuyo artículo 164 | Judicial | 144656 | 120 | 99,9 % | 1205,5x |
| 2001 | 2 A título ejemplar téngase presente la presunción legal de paternidad del marido | Familia | 123490 | 127 | 99,9 % | 972,4x |
| 2002 | 2 Balmaceda sostiene acertadamente que en caso de justificarse que las especies | Penal | 97633 | 118 | 99,9 % | 827,4x |
| 2003 | 2 Como se ha indicado más arriba, el Proyecto de Ley planteaba la limitación en la | Penal | 86906 | 120 | 99,9 % | 724,2x |
| 2004 | 2 Con la modernización del Estado de Chile en la primera mitad del siglo XX, se | Penal | 178516 | 170 | 99,9 % | 1050,1x |
| 2005 | 2 Con posterioridad a esta modificación, se dicta la Ley 20.393 del 2 de diciembre | Judicial | 62514 | 93 | 99,9 % | 672,2x |
| 2006 | 2 Corresponde al Dictamen E370752, del 20 de julio de 2023. Lo novedoso sobre | Penal | 178516 | 152 | 99,9 % | 1174,4x |
| 2007 | 2 Decreto que reglamenta el ejercicio de la función docente | Judicial | 134465 | 92 | 99,9 % | 1461,6x |
| 2008 | 2 Dicho testigo experto, además de ser de un destacado sicólogo e inventor en su | Procesal | 86112 | 111 | 99,9 % | 775,8x |
| 2009 | 2 Diputada María Rozas, Cámara de Diputados, sesión 12, legislatura 343, 7 de | Laboral | 53374 | 55 | 99,9 % | 970,4x |
| 2010 | 2 Dirección del Trabajo, Circular 63 del 29 de julio de 2020, que informa aspectos | Laboral | 98828 | 84 | 99,9 % | 1176,5x |
| 2011 | 2 Directrices de Riad, Asamblea General de las Naciones Unidas, 1990, principio | Penal | 86906 | 46 | 99,9 % | 1889,3x |
| 2012 | 2 El Manual para el uso del lenguaje inclusivo no sexista en el Poder Judicial se | Judicial | 53521 | 65 | 99,9 % | 823,4x |
| 2013 | 2 El artículo 3 letra a) del Código del Trabajo define empleador como «la persona | Laboral | 98828 | 88 | 99,9 % | 1123,0x |
| 2014 | 2 El autor agrega: «y si bien el derecho vigente ha ampliado sustancialmente el | Judicial | 150341 | 111 | 99,9 % | 1354,4x |
| 2015 | 2 El término responsabilidad tiene su origen en la palabra responsable que, a su | Penal | 194788 | 128 | 99,9 % | 1521,8x |
| 2016 | 2 Esta clasificación (normas con disposición o texto y normas sin disposición o | Judicial | 92792 | 55 | 99,9 % | 1687,1x |
| 2017 | 2 Esta propuesta arranca de la Declaración de Brasilia de 2007, que propuso hacer | Judicial | 82507 | 79 | 99,9 % | 1044,4x |
| 2018 | 2 Esto se ve reflejado en el contexto nacional por la promulgación en 2009 de | Penal | 178516 | 187 | 99,9 % | 954,6x |
| 2019 | 2 García Ramírez (2006: 667) cita varios fallos, como el caso Fermín Ramírez, de | Judicial | 144656 | 88 | 99,9 % | 1643,8x |
| 2020 | 2 Ha quedado obsoleta la referencia del artículo 227 numeral 2 a subdelegados e | Penal | 178516 | 96 | 99,9 % | 1859,5x |
| 2021 | 2 Incluso algunos autores señalan, en sentido contrario, que la sana crítica —en su | Procesal | 86112 | 110 | 99,9 % | 782,8x |
| 2022 | 2 La Asamblea General adoptó, en diciembre del 2015, la revisión de las «Reglas | Penal | 194788 | 166 | 99,9 % | 1173,4x |
| 2023 | 2 Naciones Unidas, «Vienna Convention on the Law of Treaties». Disponible en | Judicial | 81675 | 80 | 99,9 % | 1020,9x |
| 2024 | 2 Para el catálogo completo de las conductas terroristas bajo el imperio del texto | Judicial | 62514 | 52 | 99,9 % | 1202,2x |
| 2025 | 2 Para más información sobre normas de gestión y desarrollo de personas del | Laboral | 53293 | 57 | 99,9 % | 935,0x |
| 2026 | 2 Por ejemplo, todos en el Código Civil, supuestos de abejas fugitivas (artículo | Judicial | 92792 | 96 | 99,9 % | 966,6x |
| 2027 | 2 Por ello, para distinguir de la malversación propia, algunos llaman malversación | Penal | 178516 | 165 | 99,9 % | 1081,9x |
| 2028 | 2 Preámbulo de la Constitución de la Organización Mundial de la Salud, que fue | Judicial | 87950 | 113 | 99,9 % | 778,3x |
| 2029 | 2 Principios relativos a la investigación y documentación eficaces de la tortura y | Judicial | 78893 | 92 | 99,9 % | 857,5x |
| 2030 | 2 Que del mérito de los antecedentes, aparece de manifiesto que res- | Penal | 194788 | 202 | 99,9 % | 964,3x |
| 2031 | 2 R versus Sussex Justices; ex parte McCarthy [1924] 1 KB 256, 259. Como hecho | Judicial | 144656 | 165 | 99,9 % | 876,7x |
| 2032 | 2 Roche Azaña y otros versus Nicaragua. Comisión Interamericana de Derechos | Penal | 51155 | 58 | 99,9 % | 882,0x |
| 2033 | 2 Se ha resuelto que «la correcta notificación de la demanda a la parte demandada | Judicial | 89450 | 118 | 99,9 % | 758,1x |
| 2034 | 2 Se trata de un acuerdo voluntario cuyo objetivo consistía en negociar convenios | Laboral | 98828 | 135 | 99,9 % | 732,1x |
| 2035 | 2 Segundo Juzgado de Letras del Trabajo de Santiago, RIT 1218-2019, 21 de abril de | Laboral | 53374 | 66 | 99,9 % | 808,7x |
| 2036 | 2 Según la necesidad del solicitante | Judicial | 82507 | 54 | 99,9 % | 1527,9x |
| 2037 | 2 Solo a modo de ejemplo, el artículo 63 bis de la Ley 19.968 que crea los Tribunales | Procesal | 86112 | 120 | 99,9 % | 717,6x |
| 2038 | 2 Sus antecedentes más remotos pueden situarse en el derecho romano. En el | Judicial | 150341 | 175 | 99,9 % | 859,1x |
| 2039 | 2 Todos los casos contenciosos y no contenciosos sobre derechos de los pueblos | Judicial | 60665 | 55 | 99,9 % | 1103,0x |
| 2040 | 2 Voto disidente en sentencia de la Corte Suprema, de 15 de abril de 2009, rol | Familia | 123490 | 102 | 99,9 % | 1210,7x |
| 2041 | 2 Véase Visiones de Control Social (Cohen, 1998, traducción de E. Larrauri) y Ley y | Penal | 86906 | 101 | 99,9 % | 860,5x |
| 2042 | 2.       Elabore un plan de investigación que incluya: título tentativo del trabajo, pregunta | Judicial | 79146 | 65 | 99,9 % | 1217,6x |
| 2043 | 2.    Ackerman, J. (2013): Los retos de la transparencia | Administrativo | 89720 | 113 | 99,9 % | 794,0x |
| 2044 | 2.    Ley Nº 19.799 sobre documento electrónico y | Judicial | 83934 | 53 | 99,9 % | 1583,7x |
| 2045 | 2.    Requerimiento de inaplicabilidad por inconstitucionalidad de Banco de | Constitucional | 115835 | 110 | 99,9 % | 1053,0x |
| 2046 | 2.   Características del régimen jurídico de la res- | Civil | 142015 | 115 | 99,9 % | 1234,9x |
| 2047 | 2.   Código Orgánico de Tribunales, Diario Oficial de 09 de julio de 1943.         pjud.cl/ | Procesal | 96699 | 120 | 99,9 % | 805,8x |
| 2048 | 2.   Las causas relativas al derecho y el deber del padre o de la madre que no tenga el | Familia | 100107 | 83 | 99,9 % | 1206,1x |
| 2049 | 2.   Ley Nº 17.238, concede a los profesionales y técnicos chilenos que regre- | Constitucional | 121906 | 124 | 99,9 % | 983,1x |
| 2050 | 2. A fin de impedir la discriminación contra la mujer por razones de | Judicial | 89476 | 120 | 99,9 % | 745,6x |
| 2051 | 2. A los efectos de determinar si existen esas razones, las autoridades | Judicial | 78893 | 94 | 99,9 % | 839,3x |
| 2052 | 2. A los padres u otras personas encargadas del niño les incumbe | Penal | 72395 | 88 | 99,9 % | 822,7x |
| 2053 | 2. Abordaje del acoso sexual | Judicial | 81476 | 85 | 99,9 % | 958,5x |
| 2054 | 2. Activo en su puesto | Laboral | 71986 | 62 | 99,9 % | 1161,1x |
| 2055 | 2. Alta complejidad: existen dos técnicas para producir embriones | Judicial | 89476 | 100 | 99,9 % | 894,8x |
| 2056 | 2. Aplicar, en caso de que las instalaciones no prevean los | Judicial | 81476 | 79 | 99,9 % | 1031,3x |
| 2057 | 2. Aquellos que permitan a los copropietarios el uso y goce de las unidades de su dominio | Civil | 192585 | 159 | 99,9 % | 1211,2x |
| 2058 | 2. Argumentos de solución: parte considerativa de la sentencia | Judicial | 79146 | 104 | 99,9 % | 761,0x |
| 2059 | 2. Asegurar la puntualidad en el inicio de las audiencias, el | Judicial | 81476 | 74 | 99,9 % | 1101,0x |
| 2060 | 2. Asistencia a salas o a audiencias específicas conforme a la tipología | Familia | 100107 | 93 | 99,9 % | 1076,4x |
| 2061 | 2. Automatización de tareas repetitivas, donde la máquina debe | Judicial | 83934 | 71 | 99,9 % | 1182,2x |
| 2062 | 2. Autorizar al administrador para suspender o requerir la suspensión del servicio | Civil | 192585 | 100 | 99,9 % | 1925,8x |
| 2063 | 2. Boletín N° 7.567-07. Proyecto de ley que modifica Código Civil | Judicial | 89476 | 106 | 99,9 % | 844,1x |
| 2064 | 2. Caso Flor Freire contra Ecuador | Judicial | 87237 | 70 | 99,9 % | 1246,2x |
| 2065 | 2. Certificado de psiquiatra DDDD que da cuenta de diagnóstico de | Judicial | 93914 | 55 | 99,9 % | 1707,5x |
| 2066 | 2. Coherente. La gente incapacitada por las drogas o el alcohol | Judicial | 89476 | 107 | 99,9 % | 836,2x |
| 2067 | 2. Colaborar en labores administrativas del secretario como es en la | Judicial | 52128 | 68 | 99,9 % | 766,6x |
| 2068 | 2. Como un principio jurídico interpretativo del que se colige | Judicial | 89476 | 100 | 99,9 % | 894,8x |
| 2069 | 2. Con presidio mayor en sus grados mínimo a medio, al que suminis- | Penal | 97633 | 120 | 99,9 % | 813,6x |
| 2070 | 2. Conducta: el abandono naturalmente se entiende como dejar de | Judicial | 82507 | 122 | 99,9 % | 676,3x |
| 2071 | 2. Contestar demanda reconvencional oralmente, en su caso, esto | Familia | 100107 | 124 | 99,9 % | 807,3x |
| 2072 | 2. Contrato oneroso: el contrato reporta utilidad para todos los contratantes, quienes | Civil | 192585 | 172 | 99,9 % | 1119,7x |
| 2073 | 2. Cuando el imputado fuere objeto de una nueva formalización por | Penal | 194788 | 131 | 99,9 % | 1486,9x |
| 2074 | 2. Cuando excepcionalmente el traslado y la | Judicial | 134465 | 85 | 99,9 % | 1581,9x |
| 2075 | 2. Cuando excepcionalmente el traslado y la reubicación de esos | Judicial | 134465 | 94 | 99,9 % | 1430,5x |
| 2076 | 2. Cuando hayan sido cometidos por un empleado público con ocasión | Penal | 178516 | 154 | 99,9 % | 1159,2x |
| 2077 | 2. Cuando la ausencia de vigilancia o de control por parte de | Judicial | 96536 | 87 | 99,9 % | 1109,6x |
| 2078 | 2. Debe dejarse constancia de ella en el expediente, que adopta nor- | Judicial | 89450 | 93 | 99,9 % | 961,8x |
| 2079 | 2. Debe probarse por un conjunto de testimonios y antecedentes | Familia | 65085 | 68 | 99,9 % | 957,1x |
| 2080 | 2. Definición de medios y facultades del encargado de preven- | Penal | 119528 | 93 | 99,9 % | 1285,2x |
| 2081 | 2. Derechos vigentes | Judicial | 82507 | 84 | 99,9 % | 982,2x |
| 2082 | 2. Desarrollo y fortalecimiento de los servicios | Judicial | 82507 | 67 | 99,9 % | 1231,4x |
| 2083 | 2. Dichos pueblos deberán tener el derecho de conservar sus costumbres | Constitucional | 177323 | 105 | 99,9 % | 1688,8x |
| 2084 | 2. Efectividad de haber vulnerado los denunciados respecto de | Constitucional | 121906 | 156 | 99,9 % | 781,4x |
| 2085 | 2. Efectuar una capacitación al trabajador acerca de las princi- | Judicial | 96536 | 98 | 99,9 % | 985,1x |
| 2086 | 2. Ejemplos de jurisprudencia para revisar | Judicial | 87237 | 102 | 99,9 % | 855,3x |
| 2087 | 2. El Estado es responsable por la violación del derecho a la igualdad | Judicial | 87237 | 122 | 99,9 % | 715,1x |
| 2088 | 2. El Pacto Internacional de Derechos Civiles y Políticos (PIDCP) | Judicial | 87237 | 81 | 99,9 % | 1077,0x |
| 2089 | 2. El derecho a la reunificación familiar | Constitucional | 115835 | 157 | 99,9 % | 737,8x |
| 2090 | 2. El ejercicio del derecho previsto en el inciso precedente no puede | Judicial | 89476 | 109 | 99,9 % | 820,9x |
| 2091 | 2. El estatuto especial de los solicitantes de asilo y | Constitucional | 115835 | 110 | 99,9 % | 1053,0x |
| 2092 | 2. El juez(a) debe ser consciente de la necesidad de evitar los | Procesal | 94881 | 75 | 99,9 % | 1265,1x |
| 2093 | 2. El laudo arbitral solo podrá ser anulado por la respectiva Corte de | Judicial | 144656 | 167 | 99,9 % | 866,2x |
| 2094 | 2. El lugar o los lugares donde se prestarán los servicios, salvo | Judicial | 96536 | 83 | 99,9 % | 1163,1x |
| 2095 | 2. El lugar o lugares donde el trabajador prestará los servicios, que | Laboral | 98828 | 106 | 99,9 % | 932,3x |
| 2096 | 2. El mejoramiento de las condiciones de vida y de trabajo y del nivel | Judicial | 89476 | 106 | 99,9 % | 844,1x |
| 2097 | 2. El notificado, teniendo habitación conocida, se oculta o evita la pre- | Judicial | 89450 | 128 | 99,9 % | 698,8x |
| 2098 | 2. El presente artículo no impedirá someter a restricciones legales | Laboral | 100583 | 75 | 99,9 % | 1341,1x |
| 2099 | 2. Elaborar el proyecto de Plan Sectorial de Desarrollo para la Rama | Judicial | 54457 | 76 | 99,9 % | 716,5x |
| 2100 | 2. En caso afirmativo deberá ordenar —si es que persiste la conducta | Laboral | 74025 | 91 | 99,9 % | 813,5x |
| 2101 | 2. En cualquier procedimiento entablado de conformidad con | Penal | 72395 | 84 | 99,9 % | 861,8x |
| 2102 | 2. En cualquier procedimiento entablado de conformidad con el | Penal | 72395 | 85 | 99,9 % | 851,7x |
| 2103 | 2. En el proceso penal seguido en contra de las personas naturales | Penal | 119528 | 118 | 99,9 % | 1012,9x |
| 2104 | 2. En la fecha en que se cometieron los ilícitos existía un conflicto | Penal | 121924 | 119 | 99,9 % | 1024,6x |
| 2105 | 2. En los casos en los que las cuestiones planteadas merezcan | Constitucional | 112823 | 65 | 99,9 % | 1735,7x |
| 2106 | 2. En ningún caso se admitirá la instalación de sistemas de grabación de sonidos ni de videovigilancia en | Constitucional | 104063 | 78 | 99,9 % | 1334,1x |
| 2107 | 2. En segundo lugar, debe tenerse en cuenta que la Ley 18.216 es ac- | Penal | 194788 | 175 | 99,9 % | 1113,1x |
| 2108 | 2. En segundo lugar, se establece que el usuario puede colaborar en | Judicial | 87950 | 113 | 99,9 % | 778,3x |
| 2109 | 2. En su segundo informe, el de finales de agosto de 2010, el Estado | Judicial | 87237 | 89 | 99,9 % | 980,2x |
| 2110 | 2. Enfoque de género en el acceso a la justicia: este eje tiene por | Judicial | 81476 | 96 | 99,9 % | 848,7x |
| 2111 | 2. Entre las medidas que deberán adoptar los Estados Partes en el | Judicial | 89476 | 123 | 99,9 % | 727,4x |
| 2112 | 2. Esta relación especial de sujeción es una fuente de restricción de | Penal | 211066 | 221 | 99,9 % | 955,0x |
| 2113 | 2. Fallo de la Cuarta Sala de la Corte Suprema, de fecha 31 de mayo | Judicial | 87237 | 98 | 99,9 % | 890,2x |
| 2114 | 2. Fallos que rechazan el requerimiento | Penal | 211066 | 131 | 99,9 % | 1611,2x |
| 2115 | 2. Falta de Autonomía del Encargado de Prevención de Delitos. Se | Constitucional | 112823 | 96 | 99,9 % | 1175,2x |
| 2116 | 2. Fernández, Mariano, “La protección contra la discriminación por | Judicial | 87237 | 117 | 99,9 % | 745,6x |
| 2117 | 2. H m l gación de l s c ntrat s: una segunda vía utilizada por el legislador para | Civil | 110175 | 127 | 99,9 % | 867,5x |
| 2118 | 2. Impulsar el desarrollo de políticas y acciones | Judicial | 82507 | 102 | 99,9 % | 808,9x |
| 2119 | 2. Incentivar las capacitaciones de los integrantes de los tribunales | Constitucional | 177323 | 96 | 99,9 % | 1847,1x |
| 2120 | 2. Incorporación de enfoque de Derechos Humanos en el quehacer | Constitucional | 177323 | 89 | 99,9 % | 1992,4x |
| 2121 | 2. Informar a las notificadoras y a los notificadores que la persona a | Constitucional | 177323 | 111 | 99,9 % | 1597,5x |
| 2122 | 2. Jeffrey Weeks | Judicial | 87237 | 118 | 99,9 % | 739,3x |
| 2123 | 2. La Unidad de Cobranza Laboral y Previsional y de los Juzgados | Judicial | 89450 | 119 | 99,9 % | 751,7x |
| 2124 | 2. La adopción por los Estados Partes de medidas especiales, incluso | Judicial | 89476 | 62 | 99,9 % | 1443,2x |
| 2125 | 2. La condición positiva y resolutoria física o moralmente imposible o ininteligible, se | Civil | 118177 | 166 | 99,9 % | 711,9x |
| 2126 | 2. La consulta será firmada por el Presidente del Comité de Administración y por el | Civil | 192585 | 107 | 99,9 % | 1799,9x |
| 2127 | 2. La decisión judicial significa una intervención donde alguien | Familia | 100107 | 71 | 99,9 % | 1410,0x |
| 2128 | 2. La definición de crimen será interpretada estrictamente y | Penal | 121924 | 75 | 99,9 % | 1625,7x |
| 2129 | 2. La discriminación en el derecho a la vida privada (primera | Judicial | 87237 | 98 | 99,9 % | 890,2x |
| 2130 | 2. La discriminación en el ámbito de la familia | Judicial | 87237 | 78 | 99,9 % | 1118,4x |
| 2131 | 2. La existencia de contratos forzosos, en principio cuestionable por consistir en una | Civil | 110175 | 162 | 99,9 % | 680,1x |
| 2132 | 2. La extensión del artículo 1698 a los cumplimientos imper- | Civil | 142015 | 118 | 99,9 % | 1203,5x |
| 2133 | 2. La igualdad ante la ley. En Chile no hay persona ni grupos privile- | Constitucional | 177323 | 101 | 99,9 % | 1755,7x |
| 2134 | 2. La internalización que tengan los hijos e hijas de esta figura: por | Familia | 95131 | 111 | 99,9 % | 857,0x |
| 2135 | 2. La irrenunciabilidad e imprescriptibilidad es propia de este tipo | Familia | 65085 | 76 | 99,9 % | 856,4x |
| 2136 | 2. La maternidad y la infancia tienen derecho a cuidados y asistencia | Judicial | 89476 | 68 | 99,9 % | 1315,8x |
| 2137 | 2. La medida que limita el derecho no debe ser arbitraria o des- | Laboral | 113458 | 88 | 99,9 % | 1289,3x |
| 2138 | 2. La provisión de los medios y facultades suficientes para el | Penal | 178516 | 127 | 99,9 % | 1405,6x |
| 2139 | 2. La recurrente funda su acción en la Ley de Copropiedad Inmobiliaria, remitiéndose a su | Civil | 192585 | 111 | 99,9 % | 1735,0x |
| 2140 | 2. La reforma hecha al Código Civil por la Ley N° 10.271 no desmiente la conclusión | Familia | 136567 | 111 | 99,9 % | 1230,3x |
| 2141 | 2. La señalética interior se entiende con facilidad | Laboral | 71986 | 63 | 99,9 % | 1142,6x |
| 2142 | 2. La situación de los privados de razón, las emergencias y su | Civil | 142015 | 126 | 99,9 % | 1127,1x |
| 2143 | 2. La subordinación puede ser total o parcial. En el primer caso, ninguna parte del | Civil | 120848 | 110 | 99,9 % | 1098,6x |
| 2144 | 2. Las consultas llevadas a cabo en aplicación de | Judicial | 134465 | 87 | 99,9 % | 1545,6x |
| 2145 | 2. Las diversas calidades migratorias de los extranjeros | Constitucional | 115835 | 163 | 99,9 % | 710,6x |
| 2146 | 2. Las inmunidades y las normas de procedimiento especiales que conlleve el cargo oficial de una persona, con | Penal | 121924 | 81 | 99,9 % | 1505,2x |
| 2147 | 2. Las medidas de revisión y control deben ser idóneas a los objetivos | Laboral | 113458 | 113 | 99,9 % | 1004,1x |
| 2148 | 2. Las reparatorias, que persiguen el cumplimiento de prestaciones | Penal | 211066 | 144 | 99,9 % | 1465,7x |
| 2149 | 2. Libertad contractual significa que –con tal que se respeten las normas legales imperativas | Civil | 110175 | 124 | 99,9 % | 888,5x |
| 2150 | 2. Los Estados Partes velarán por la aplicación de estos derechos | Penal | 72395 | 97 | 99,9 % | 746,3x |
| 2151 | 2. Los Estados Partes velarán por la aplicación de estos derechos de conformidad con | Familia | 62470 | 83 | 99,9 % | 752,7x |
| 2152 | 2. Los Estados parte se comprometen a asegurar al niño la protección y | Constitucional | 177323 | 98 | 99,9 % | 1809,4x |
| 2153 | 2. Los Estados partes en el presente Pacto se comprometen a garantizar | Judicial | 81675 | 97 | 99,9 % | 842,0x |
| 2154 | 2. Los Estados partes garantizarán en la máxima medida posible la su- | Constitucional | 44292 | 58 | 99,9 % | 763,7x |
| 2155 | 2. Los servicios de salud deberán organizarse, en la medida de lo | Judicial | 134465 | 102 | 99,9 % | 1318,3x |
| 2156 | 2. MacKinnon, Catharine, Feminismo inmodificado. Discursos sobre la | Judicial | 87237 | 88 | 99,9 % | 991,3x |
| 2157 | 2. Mapa sobre la orientación sexual en el mundo, diciembre de 2019 | Judicial | 87237 | 88 | 99,9 % | 991,3x |
| 2158 | 2. Modelos contextuales. Dentro de estos modelos se encuentran los | Judicial | 150341 | 170 | 99,9 % | 884,4x |
| 2159 | 2. Muñoz, Fernando; “El núcleo fundamental de la sociedad: los | Judicial | 87237 | 105 | 99,9 % | 830,8x |
| 2160 | 2. Nada de lo dispuesto en este artículo se opondrá al juicio ni a la | Penal | 121924 | 89 | 99,9 % | 1369,9x |
| 2161 | 2. Nadie puede ser arrestado o detenido, sujeto a prisión preventiva | Penal | 194788 | 195 | 99,9 % | 998,9x |
| 2162 | 2. No es posible sostener que al interior del país existieron fuerzas | Penal | 121924 | 92 | 99,9 % | 1325,3x |
| 2163 | 2. No existe un patrón de relación de superioridad masculina | Familia | 100107 | 78 | 99,9 % | 1283,4x |
| 2164 | 2. Normas legales | Civil | 192585 | 136 | 99,9 % | 1416,1x |
| 2165 | 2. Otras formas de notificación: Cualquiera de las partes podrá pro- | Judicial | 89450 | 59 | 99,9 % | 1516,1x |
| 2166 | 2. Pagar los pasivos de la persona jurídica, incluidos los derivados de | Penal | 119528 | 117 | 99,9 % | 1021,6x |
| 2167 | 2. Para los efectos de la interpretación de un tratado. el contexto comprenderá, además del texto, incluidos | Judicial | 134465 | 124 | 99,9 % | 1084,4x |
| 2168 | 2. Plataforma digital con información sobre desempeño de Chile en | Constitucional | 177323 | 110 | 99,9 % | 1612,0x |
| 2169 | 2. Población migrante en Chile. Chile como polo de | Constitucional | 115835 | 85 | 99,9 % | 1362,8x |
| 2170 | 2. Posibilitar que las personas de edad | Judicial | 82507 | 63 | 99,9 % | 1309,6x |
| 2171 | 2. Presentando derechamente la demanda civil, ante el juez de garan- | Penal | 211066 | 117 | 99,9 % | 1804,0x |
| 2172 | 2. Primer contacto: las instrucciones en este caso son reducir el | Penal | 72395 | 80 | 99,9 % | 904,9x |
| 2173 | 2. Que al examinar estos sentenciadores la sentencia de primer grado, aparece que los vi- | Judicial | 79146 | 118 | 99,9 % | 670,7x |
| 2174 | 2. Que el amparado se encuentra cumpliendo una pena de diez años y | Penal | 194788 | 131 | 99,9 % | 1486,9x |
| 2175 | 2. Que el recurso de apelacion se hubiere interpuesto dentro | Procesal | 95124 | 107 | 99,9 % | 889,0x |
| 2176 | 2. Que el reglamento de copropiedad autorice al administrador para que suspenda o | Civil | 192585 | 132 | 99,9 % | 1459,0x |
| 2177 | 2. Que la ley 19.856 se refiere en su Título I al «beneficio de reducción | Penal | 194788 | 98 | 99,9 % | 1987,6x |
| 2178 | 2. Que la parte a quien afecta la notificación defectuosa o la falta | Judicial | 89450 | 94 | 99,9 % | 951,6x |
| 2179 | 2. Que no obstante lo anterior, mediante la resolución de veintinue- | Judicial | 144656 | 136 | 99,9 % | 1063,6x |
| 2180 | 2. Que se acredite esta circunstancia mediante un certificado exten- | Judicial | 89450 | 85 | 99,9 % | 1052,4x |
| 2181 | 2. Que, actualmente la recurrente se encuentra en territorio extranjero | Judicial | 144656 | 128 | 99,9 % | 1130,1x |
| 2182 | 2. Que, al dictarlo, se hubiere incurrido en manifiesto error de hecho | Judicial | 144656 | 93 | 99,9 % | 1555,4x |
| 2183 | 2. Que, la cuestión debatida, tal y como quedó claro de los alegatos de | Penal | 194788 | 163 | 99,9 % | 1195,0x |
| 2184 | 2. Que, la defensa del condenado se alza deduciendo apelación subsi- | Penal | 194788 | 189 | 99,9 % | 1030,6x |
| 2185 | 2. Rebajando la multa, cuando se acredite fehacientemente | Laboral | 100583 | 66 | 99,9 % | 1524,0x |
| 2186 | 2. Recepcionar las llamadas telefónicas, dando información a quien | Judicial | 52128 | 70 | 99,9 % | 744,7x |
| 2187 | 2. Reclamar de esas observaciones ante el Juzgado de Letras del Tra- | Laboral | 74025 | 104 | 99,9 % | 711,8x |
| 2188 | 2. Recomendacio- 2.1. Recomendaciones sobre | Judicial | 81476 | 67 | 99,9 % | 1216,1x |
| 2189 | 2. Reemplázase en el inciso primero la frase «y esta designación se | Judicial | 89450 | 104 | 99,9 % | 860,1x |
| 2190 | 2. Reemplázase, en el inciso segundo, la frase «el tribunal ordenará que | Judicial | 89450 | 101 | 99,9 % | 885,6x |
| 2191 | 2. Resolución | Judicial | 54457 | 70 | 99,9 % | 778,0x |
| 2192 | 2. Resumen flujo de interconexión | Constitucional | 44292 | 49 | 99,9 % | 903,9x |
| 2193 | 2. Régimen permanente que faculta a las Cortes de Apelaciones y a | Judicial | 89450 | 98 | 99,9 % | 912,8x |
| 2194 | 2. Se elabore informe psicológico respecto de las partes al tenor del objeto de juicio a ela- | Judicial | 79146 | 101 | 99,9 % | 783,6x |
| 2195 | 2. Se oficie al Instituto Psiquiátrico Dr. José Miguel Bulnes de la Comuna de Recoleta, para | Judicial | 79146 | 75 | 99,9 % | 1055,3x |
| 2196 | 2. Se “reserva” el derecho de recurrir de reposición, con apelación | Familia | 100107 | 80 | 99,9 % | 1251,3x |
| 2197 | 2. Ser la víctima    Niña: Ser humano menor de 14 años (niña) y adolescen- | Familia | 95131 | 117 | 99,9 % | 813,1x |
| 2198 | 2. Serán recurribles en casación las sentencias dictadas en segunda instancia por las | General | 129559 | 149 | 99,9 % | 869,5x |
| 2199 | 2. Señalar, de ser el caso, las afirmaciones realizadas por una parte | Familia | 100107 | 92 | 99,9 % | 1088,1x |
| 2200 | 2. Si existen vacíos legales el juez no puede negarse a resolver el | Laboral | 113458 | 80 | 99,9 % | 1418,2x |
| 2201 | 2. Sin perjuicio de lo dispuesto en el párrafo 1 supra, los Estados | Judicial | 89476 | 96 | 99,9 % | 932,0x |
| 2202 | 2. Sistema Inglés, Judicialista o de la Regla de | Judicial | 105809 | 110 | 99,9 % | 961,9x |
| 2203 | 2. Solicitar al receptor judicial que en las notificaciones, realizadas a | Constitucional | 177323 | 93 | 99,9 % | 1906,7x |
| 2204 | 2. Solicitud al tribunal: Condición que se desprende de la expresión | Judicial | 89450 | 128 | 99,9 % | 698,8x |
| 2205 | 2. Solo podrán captarse imágenes de la vía pública en la medida que resulte imprescindible para la finalidad | Constitucional | 104063 | 122 | 99,9 % | 853,0x |
| 2206 | 2. Solo se podrá privar de libertad a los menores de conformidad con | Penal | 194788 | 156 | 99,9 % | 1248,6x |
| 2207 | 2. Tabla N° 2: estereotipos masculinos y femeninos, es decir, cuáles son las cualidades que se asignana | Judicial | 81476 | 79 | 99,9 % | 1031,3x |
| 2208 | 2. Tener en cuenta los diversos tipos de discapacidad, a fin de | Judicial | 81476 | 65 | 99,9 % | 1253,5x |
| 2209 | 2. Toda persona inculpada de delito tiene derecho a que se presuma | Constitucional | 177323 | 157 | 99,9 % | 1129,4x |
| 2210 | 2. Toda persona tiene derecho a la libertad de expresión; este | Administrativo | 89720 | 97 | 99,9 % | 924,9x |
| 2211 | 2. Toda persona tiene derecho a salir de cualquier país, incluso del propio, y a regresar a su país” | Constitucional | 115835 | 104 | 99,9 % | 1113,8x |
| 2212 | 2. Todo Estado parte incluirá esta prohibición en las normas o instruc- | Judicial | 78893 | 68 | 99,9 % | 1160,2x |
| 2213 | 2. Todo Estado parte tomará, asimismo, las medidas necesarias para | Judicial | 78893 | 110 | 99,9 % | 717,2x |
| 2214 | 2. Trasgresión grave y reiterada de los deberes de convivencia, socorro y fidelidad | Familia | 190697 | 204 | 99,9 % | 934,8x |
| 2215 | 2. Tratándose de condenados reincidentes en los términos de las cir- | Penal | 194788 | 131 | 99,9 % | 1486,9x |
| 2216 | 2. Tratándose de contratos bilaterales, no admite la ley, en las obligaciones de dar, por | Civil | 120848 | 98 | 99,9 % | 1233,1x |
| 2217 | 2. Tres ideas centrales: proporcionalidad, justicia | Procesal | 96699 | 92 | 99,9 % | 1051,1x |
| 2218 | 2. Tutela restitutoria: el juez deberá velar para que la situación se | Laboral | 113458 | 75 | 99,9 % | 1512,8x |
| 2219 | 2. Término del emplazamiento: El término de emplazamiento para | Judicial | 89450 | 102 | 99,9 % | 877,0x |
| 2220 | 2. Una modalidad de notificación personal: Se ha indicado que es | Judicial | 89450 | 117 | 99,9 % | 764,5x |
| 2221 | 2. Una versión del tratado en idioma distinto de aquel en que haya sido autenticado el texto será considerada | Judicial | 134465 | 98 | 99,9 % | 1372,1x |
| 2222 | 2. Una vez finalizada su confección o estampada la última firma, si | Judicial | 96536 | 74 | 99,9 % | 1304,5x |
| 2223 | 2. Utilización plena de las posibilidades | Judicial | 82507 | 58 | 99,9 % | 1422,5x |
| 2224 | 2. Velar por el interés superior del niño. En toda decisión los tribunales | Penal | 86906 | 109 | 99,9 % | 797,3x |
| 2225 | 2. Voluntariedad: la mediación es eminentemente voluntaria, de manera que los | Familia | 190697 | 171 | 99,9 % | 1115,2x |
| 2226 | 2.1                Definición y | Judicial | 52128 | 62 | 99,9 % | 840,8x |
| 2227 | 2.1                El problema del “modelo de imputación”en | Penal | 119528 | 79 | 99,9 % | 1513,0x |
| 2228 | 2.1                Igualdad ante | Familia | 65085 | 36 | 99,9 % | 1807,9x |
| 2229 | 2.1     Corte de | Judicial | 54457 | 58 | 99,9 % | 938,9x |
| 2230 | 2.1     Nociones generales acerca de la igualdad en el | Judicial | 81476 | 42 | 99,9 % | 1939,9x |
| 2231 | 2.1     Ámbito | Judicial | 64632 | 45 | 99,9 % | 1436,3x |
| 2232 | 2.1. El decreto judicial o la resolución administrativa que da la posesión | Civil | 92843 | 87 | 99,9 % | 1067,2x |
| 2233 | 2.1. La acción especial de reclamación del artículo 89 del Decreto Ley No. 1.094 de 1975 | Constitucional | 115835 | 162 | 99,9 % | 715,0x |
| 2234 | 2.1. Proporcionalidad | Procesal | 96699 | 143 | 99,9 % | 676,2x |
| 2235 | 2.1. Toda deuda contraída por el marido durante la vigencia de la sociedad conyugal | Familia | 136567 | 169 | 99,9 % | 808,1x |
| 2236 | 2.1.1 Concepto | Penal | 121924 | 88 | 99,9 % | 1385,5x |
| 2237 | 2.1.1 Convenio Nº 108 del Consejo de | Constitucional | 104063 | 102 | 99,9 % | 1020,2x |
| 2238 | 2.1.1 Historia y definiciones básicas de los | Constitucional | 112823 | 93 | 99,9 % | 1213,2x |
| 2239 | 2.1.1 Igualdad y no discriminación en los | Judicial | 93914 | 89 | 99,9 % | 1055,2x |
| 2240 | 2.1.1 Ley N° 20.628 | Procesal | 94881 | 119 | 99,9 % | 797,3x |
| 2241 | 2.1.1 Orígenes de esta noción | Laboral | 113458 | 107 | 99,9 % | 1060,4x |
| 2242 | 2.1.1 Principio de oficialidad | Penal | 211066 | 119 | 99,9 % | 1773,7x |
| 2243 | 2.1.1 Propuestas de justificación de la RPPJ con | Penal | 119528 | 63 | 99,9 % | 1897,3x |
| 2244 | 2.1.1 Una misma anatomía del incumplimiento | Civil | 142015 | 101 | 99,9 % | 1406,1x |
| 2245 | 2.1.1 Ámbito de aplicación de la Ley Nº 20.886 | Judicial | 83934 | 122 | 99,9 % | 688,0x |
| 2246 | 2.1.1.    El paradigma de la separación entre funciones jurisdiccionales y administrativas.       48 | Procesal | 96699 | 50 | 99,9 % | 1934,0x |
| 2247 | 2.1.1.1 Aplicación de las normas de la Ley Nº 20.886 | Judicial | 83934 | 113 | 99,9 % | 742,8x |
| 2248 | 2.1.1.1 Aspectos básicos del principio | Penal | 119528 | 98 | 99,9 % | 1219,7x |
| 2249 | 2.1.1.2 Criterios atributivos de responsabilidad | Penal | 119528 | 87 | 99,9 % | 1373,9x |
| 2250 | 2.1.1.2 Las Líneas Directrices de la OCDE | Constitucional | 112823 | 67 | 99,9 % | 1683,9x |
| 2251 | 2.1.1.3 Los instrumentos de la Organización | Constitucional | 112823 | 85 | 99,9 % | 1327,3x |
| 2252 | 2.1.1.4 Los instrumentos de la Organización | Constitucional | 112823 | 83 | 99,9 % | 1359,3x |
| 2253 | 2.1.10.1 Atención de usuarios y usuarias | Judicial | 83934 | 81 | 99,9 % | 1036,2x |
| 2254 | 2.1.10.2 Audiencias | Judicial | 83934 | 118 | 99,9 % | 711,3x |
| 2255 | 2.1.10.3 Teletrabajo | Judicial | 83934 | 85 | 99,9 % | 987,5x |
| 2256 | 2.1.2 Artículo 101 Código Orgánico de Tribunales | Procesal | 94881 | 105 | 99,9 % | 903,6x |
| 2257 | 2.1.2 El determinante fallo del Tribunal Constitucional | Constitucional | 104063 | 97 | 99,9 % | 1072,8x |
| 2258 | 2.1.2 Igualdad y no discriminación en | Judicial | 93914 | 80 | 99,9 % | 1173,9x |
| 2259 | 2.1.2 Incumplimiento e imputabilidad | Civil | 142015 | 94 | 99,9 % | 1510,8x |
| 2260 | 2.1.2 Materialización de los principios de | Judicial | 83934 | 105 | 99,9 % | 799,4x |
| 2261 | 2.1.2 Principio de investigación | Penal | 211066 | 117 | 99,9 % | 1804,0x |
| 2262 | 2.1.2.1 Documento y firma electrónica | Judicial | 83934 | 104 | 99,9 % | 807,1x |
| 2263 | 2.1.2.2 Carpeta electrónica | Judicial | 83934 | 122 | 99,9 % | 688,0x |
| 2264 | 2.1.3 Cumplimiento e incumplimiento | Civil | 142015 | 100 | 99,9 % | 1420,2x |
| 2265 | 2.1.3 Directiva 95/46/CE, del Parlamento Europeo | Constitucional | 104063 | 94 | 99,9 % | 1107,1x |
| 2266 | 2.1.3 Modificación al artículo 1° | Procesal | 94881 | 115 | 99,9 % | 825,1x |
| 2267 | 2.1.3 Principio acusatorio | Penal | 211066 | 106 | 99,9 % | 1991,2x |
| 2268 | 2.1.3 Uso obligatorio de los sistemas informáticos | Judicial | 83934 | 111 | 99,9 % | 756,2x |
| 2269 | 2.1.4 El incumplimiento y la culpa de la persona | Civil | 142015 | 119 | 99,9 % | 1193,4x |
| 2270 | 2.1.4 Excepciones al ingreso de presentaciones | Judicial | 83934 | 84 | 99,9 % | 999,2x |
| 2271 | 2.1.4 Normativa complementaria | Procesal | 94881 | 52 | 99,9 % | 1824,6x |
| 2272 | 2.1.4 Principio de legalidad y oportunidad | Penal | 211066 | 115 | 99,9 % | 1835,4x |
| 2273 | 2.1.4 Reglamento General de Protección de | Constitucional | 104063 | 98 | 99,9 % | 1061,9x |
| 2274 | 2.1.4.1 Curtidos Bas | Constitucional | 112823 | 59 | 99,9 % | 1912,3x |
| 2275 | 2.1.4.1 Horario de funcionamiento de la OJV | Judicial | 83934 | 120 | 99,9 % | 699,5x |
| 2276 | 2.1.4.2 Ducto de Mehuin | Constitucional | 112823 | 78 | 99,9 % | 1446,4x |
| 2277 | 2.1.4.4 Represa Ralco | Constitucional | 112823 | 89 | 99,9 % | 1267,7x |
| 2278 | 2.1.5 Acerca de lo debido en las obligaciones | Civil | 142015 | 132 | 99,9 % | 1075,9x |
| 2279 | 2.1.5 Contenido y alcance del deber empresarial | Constitucional | 112823 | 87 | 99,9 % | 1296,8x |
| 2280 | 2.1.5 Presentación de documentos | Judicial | 83934 | 85 | 99,9 % | 987,5x |
| 2281 | 2.1.5.1 La debida diligencia empresarial | Constitucional | 112823 | 89 | 99,9 % | 1267,7x |
| 2282 | 2.1.5.1 Patrocinio y mandato judicial | Judicial | 83934 | 63 | 99,9 % | 1332,3x |
| 2283 | 2.1.5.2 Estándares de cuidado por parte de | Constitucional | 112823 | 81 | 99,9 % | 1392,9x |
| 2284 | 2.1.5.2 Presentación de documentos | Judicial | 83934 | 88 | 99,9 % | 953,8x |
| 2285 | 2.1.5.3 Gobernanza y debida diligencia | Constitucional | 112823 | 94 | 99,9 % | 1200,2x |
| 2286 | 2.1.5.3 Interconexión con instituciones privadas y | Judicial | 83934 | 100 | 99,9 % | 839,3x |
| 2287 | 2.1.5.4 Habilitación de transferencias bancarias | Judicial | 83934 | 96 | 99,9 % | 874,3x |
| 2288 | 2.1.5.4 Sistemas de evaluación de impactos | Constitucional | 112823 | 93 | 99,9 % | 1213,2x |
| 2289 | 2.1.6 Acceso a remedio y reparaciones | Constitucional | 112823 | 106 | 99,9 % | 1064,4x |
| 2290 | 2.1.6 La función de la diligencia exigible | Civil | 142015 | 123 | 99,9 % | 1154,6x |
| 2291 | 2.1.6 Patrocinio y poder electrónico | Judicial | 83934 | 97 | 99,9 % | 865,3x |
| 2292 | 2.1.6.1 Modificaciones a la Ley Nº 20.886 | Judicial | 83934 | 78 | 99,9 % | 1076,1x |
| 2293 | 2.1.7 Síntesis | Civil | 142015 | 100 | 99,9 % | 1420,2x |
| 2294 | 2.1.7.1 Modificaciones introducidas por la Ley Nº 20.886 | Judicial | 83934 | 105 | 99,9 % | 799,4x |
| 2295 | 2.1.7.2 Normas que establecen medios alternativos | Judicial | 83934 | 119 | 99,9 % | 705,3x |
| 2296 | 2.1.7.3 Modificaciones en el boletín Nº 13.752-07 | Judicial | 83934 | 124 | 99,9 % | 676,9x |
| 2297 | 2.1.8 La excepción: la obligación de | Civil | 142015 | 115 | 99,9 % | 1234,9x |
| 2298 | 2.1.9 Relación con otras instituciones | Judicial | 83934 | 59 | 99,9 % | 1422,6x |
| 2299 | 2.1.9.1 Beneficios de la interconexión | Judicial | 83934 | 101 | 99,9 % | 831,0x |
| 2300 | 2.1.9.2 La Ley Nº 20.886 y la relación | Judicial | 83934 | 88 | 99,9 % | 953,8x |
| 2301 | 2.1.9.3 Comunicaciones y mecanismos utilizados | Judicial | 83934 | 98 | 99,9 % | 856,5x |
| 2302 | 2.10    La tramitación de un procedimiento de | Laboral | 71986 | 79 | 99,9 % | 911,2x |
| 2303 | 2.10. Cosas comerciables e incomerciables | Civil | 42954 | 35 | 99,9 % | 1227,3x |
| 2304 | 2.11      Los acuerdos de las | Judicial | 54457 | 80 | 99,9 % | 680,7x |
| 2305 | 2.11     El reclamo de multas y | Laboral | 71986 | 55 | 99,9 % | 1308,8x |
| 2306 | 2.11. De la emancipación | Familia | 62470 | 59 | 99,9 % | 1058,8x |
| 2307 | 2.12.1 Qué medidas se consultan | Judicial | 134465 | 118 | 99,9 % | 1139,5x |
| 2308 | 2.12.2 En qué casos de consulta (medidas susceptibles | Judicial | 134465 | 71 | 99,9 % | 1893,9x |
| 2309 | 2.12.3 Como se consulta | Judicial | 134465 | 109 | 99,9 % | 1233,6x |
| 2310 | 2.12.4 A quién se consulta | Judicial | 134465 | 70 | 99,9 % | 1920,9x |
| 2311 | 2.12.5 Qué consecuencias tiene | Judicial | 134465 | 111 | 99,9 % | 1211,4x |
| 2312 | 2.12.6 Qué sucede si la comunidad no participa | Judicial | 134465 | 79 | 99,9 % | 1702,1x |
| 2313 | 2.14     Los presidentes de | Judicial | 54457 | 63 | 99,9 % | 864,4x |
| 2314 | 2.2           Derecho a la | Familia | 65085 | 36 | 99,9 % | 1807,9x |
| 2315 | 2.2           Supuesto | Judicial | 64632 | 44 | 99,9 % | 1468,9x |
| 2316 | 2.2      Su competencia en | Laboral | 71986 | 79 | 99,9 % | 911,2x |
| 2317 | 2.2     Categorías de | Judicial | 54457 | 75 | 99,9 % | 726,1x |
| 2318 | 2.2     Funcionamiento, composicióny | Judicial | 52128 | 40 | 99,9 % | 1303,2x |
| 2319 | 2.2 Principales instrumentos internacionales y el trabajo de órganos internacionales en los sistemas | Judicial | 93914 | 71 | 99,9 % | 1322,7x |
| 2320 | 2.2. Derechos sociales | Constitucional | 115835 | 154 | 99,9 % | 752,2x |
| 2321 | 2.2. En la transacción (art. 2463). Como expresa Vodanovic, “La solución de la ley | Civil | 120848 | 169 | 99,9 % | 715,1x |
| 2322 | 2.2. La acción de amparo constitucional como vía de reclamación en contra de | Constitucional | 115835 | 74 | 99,9 % | 1565,3x |
| 2323 | 2.2. Los bienes raíces adquiridos durante la vigencia de la sociedad conyugal a título | Familia | 136567 | 169 | 99,9 % | 808,1x |
| 2324 | 2.2. Situación del hijo póstumo o cuando alguno de los progenitores fallece dentro del | Familia | 62470 | 83 | 99,9 % | 752,7x |
| 2325 | 2.2.1 Aproximación a la noción de igualdad | Judicial | 81476 | 65 | 99,9 % | 1253,5x |
| 2326 | 2.2.1 Confusión entre el derecho a la | Constitucional | 121906 | 102 | 99,9 % | 1195,2x |
| 2327 | 2.2.1 Convención sobre la Eliminación de todas las | Familia | 95131 | 96 | 99,9 % | 990,9x |
| 2328 | 2.2.1 Evolución y desarrollos en el sistema | Judicial | 93914 | 80 | 99,9 % | 1173,9x |
| 2329 | 2.2.1 Fondo | Judicial | 79146 | 75 | 99,9 % | 1055,3x |
| 2330 | 2.2.1 Instrumentos internacionales de | Constitucional | 112823 | 83 | 99,9 % | 1359,3x |
| 2331 | 2.2.1 La introducción de los criterios de “defecto de | Penal | 119528 | 89 | 99,9 % | 1343,0x |
| 2332 | 2.2.1 La pregunta | Civil | 142015 | 74 | 99,9 % | 1919,1x |
| 2333 | 2.2.1 Libertad probatoria | Familia | 100107 | 91 | 99,9 % | 1100,1x |
| 2334 | 2.2.1 Líneas jurisprudenciales de la Corte | Familia | 65085 | 80 | 99,9 % | 813,6x |
| 2335 | 2.2.1 Subcontratación | Laboral | 100583 | 120 | 99,9 % | 838,2x |
| 2336 | 2.2.1.1 Casos emblemáticos del sistema europeo | Judicial | 93914 | 106 | 99,9 % | 886,0x |
| 2337 | 2.2.1.1 Coherencia | Judicial | 79146 | 100 | 99,9 % | 791,5x |
| 2338 | 2.2.1.1 Concepto | Judicial | 96536 | 107 | 99,9 % | 902,2x |
| 2339 | 2.2.1.1 Potestad de mando | Laboral | 113458 | 67 | 99,9 % | 1693,4x |
| 2340 | 2.2.1.2 Contenido interesante | Judicial | 79146 | 106 | 99,9 % | 746,7x |
| 2341 | 2.2.1.2 Potestad de reglamentación | Laboral | 113458 | 146 | 99,9 % | 777,1x |
| 2342 | 2.2.1.3 Fundamentación de las ideas | Judicial | 79146 | 111 | 99,9 % | 713,0x |
| 2343 | 2.2.1.3 Potestad disciplinaria | Laboral | 113458 | 89 | 99,9 % | 1274,8x |
| 2344 | 2.2.1.4 Concordancia, orden y precisión de las ideas | Judicial | 79146 | 93 | 99,9 % | 851,0x |
| 2345 | 2.2.1.5 Fluidez | Judicial | 79146 | 101 | 99,9 % | 783,6x |
| 2346 | 2.2.1.6 Originalidad y efectividad del mensaje | Judicial | 79146 | 110 | 99,9 % | 719,5x |
| 2347 | 2.2.1.7 Vocabulario acertado y diverso | Judicial | 79146 | 104 | 99,9 % | 761,0x |
| 2348 | 2.2.2 Acta N° 41-2020 de la Corte Suprema | Procesal | 94881 | 105 | 99,9 % | 903,6x |
| 2349 | 2.2.2 Conclusiones preliminares relativas al modelo | Penal | 119528 | 120 | 99,9 % | 996,1x |
| 2350 | 2.2.2 Confusión entre el derecho a la vida | Constitucional | 121906 | 115 | 99,9 % | 1060,1x |
| 2351 | 2.2.2 Declaración y Plan de Acción de Viena (1993) | Familia | 95131 | 101 | 99,9 % | 941,9x |
| 2352 | 2.2.2 Forma | Judicial | 79146 | 98 | 99,9 % | 807,6x |
| 2353 | 2.2.2 La igualdad en la ley y ante la ley | Judicial | 81476 | 119 | 99,9 % | 684,7x |
| 2354 | 2.2.2 Medios tecnológicos y control del | Laboral | 113458 | 78 | 99,9 % | 1454,6x |
| 2355 | 2.2.2 Modificaciones al Acta 71-2016 de la | Procesal | 101194 | 149 | 99,9 % | 679,2x |
| 2356 | 2.2.2 Ofrecimiento de prueba | Familia | 100107 | 110 | 99,9 % | 910,1x |
| 2357 | 2.2.2.1 La cibervigilancia del trabajador | Laboral | 113458 | 109 | 99,9 % | 1040,9x |
| 2358 | 2.2.2.1 Márgenes | Judicial | 79146 | 83 | 99,9 % | 953,6x |
| 2359 | 2.2.2.1 Opinión Consultiva 24/17, de | Judicial | 93914 | 109 | 99,9 % | 861,6x |
| 2360 | 2.2.2.1 Prueba no solicitada oportunamente | Familia | 100107 | 101 | 99,9 % | 991,2x |
| 2361 | 2.2.2.1.3. Apelación de las decisiones de case management | Procesal | 96699 | 122 | 99,9 % | 792,6x |
| 2362 | 2.2.2.2 El correo electrónico corporativo | Laboral | 113458 | 110 | 99,9 % | 1031,4x |
| 2363 | 2.2.2.2 Jurisprudencia contenciosa del sistema | Judicial | 93914 | 96 | 99,9 % | 978,3x |
| 2364 | 2.2.2.2 Prueba sobre prueba | Familia | 100107 | 109 | 99,9 % | 918,4x |
| 2365 | 2.2.2.3 La actividad en redes sociales | Laboral | 113458 | 84 | 99,9 % | 1350,7x |
| 2366 | 2.2.2.3 Otras iniciativas del sistema interamericano | Judicial | 93914 | 57 | 99,9 % | 1647,6x |
| 2367 | 2.2.2.4 Legibilidad | Judicial | 79146 | 74 | 99,9 % | 1069,5x |
| 2368 | 2.2.2.5 La recomendación de la CIDH de hacer | Constitucional | 112823 | 89 | 99,9 % | 1267,7x |
| 2369 | 2.2.2.5 Ortografía | Judicial | 79146 | 104 | 99,9 % | 761,0x |
| 2370 | 2.2.2.6 Puntuación | Judicial | 79146 | 104 | 99,9 % | 761,0x |
| 2371 | 2.2.2.7 Distribución de las ideas en párrafos | Judicial | 79146 | 114 | 99,9 % | 694,3x |
| 2372 | 2.2.2.8 Estructura adecuada | Judicial | 79146 | 72 | 99,9 % | 1099,2x |
| 2373 | 2.2.3 Convenciones probatorias | Familia | 100107 | 93 | 99,9 % | 1076,4x |
| 2374 | 2.2.3 Declaración sobre la Eliminación de | Familia | 95131 | 93 | 99,9 % | 1022,9x |
| 2375 | 2.2.3 Extraterritorialidad, forum necesitatis | Constitucional | 112823 | 92 | 99,9 % | 1226,3x |
| 2376 | 2.2.3 La prueba del incumplimiento y la presunción | Civil | 142015 | 100 | 99,9 % | 1420,2x |
| 2377 | 2.2.3 Registro o banco de datos | Judicial | 96536 | 109 | 99,9 % | 885,7x |
| 2378 | 2.2.3. Derecho al acceso a la vivienda | Constitucional | 115835 | 162 | 99,9 % | 715,0x |
| 2379 | 2.2.3.1 Efectos extraterritoriales de la | Constitucional | 112823 | 93 | 99,9 % | 1213,2x |
| 2380 | 2.2.3.2 Adjudicación de hechos ocurridos | Constitucional | 112823 | 81 | 99,9 % | 1392,9x |
| 2381 | 2.2.3.3 La cooperación judicial como complemento a la | Constitucional | 112823 | 98 | 99,9 % | 1151,3x |
| 2382 | 2.2.3.4 Proceso para la adopción de un | Constitucional | 112823 | 84 | 99,9 % | 1343,1x |
| 2383 | 2.2.4 Configuraciones posibles y un par de prevenciones | Constitucional | 121906 | 120 | 99,9 % | 1015,9x |
| 2384 | 2.2.4 Convención Interamericana para | Familia | 95131 | 81 | 99,9 % | 1174,5x |
| 2385 | 2.2.4 Exclusión de prueba | Familia | 100107 | 126 | 99,9 % | 794,5x |
| 2386 | 2.2.4 Responsable del banco de datos y encargados | Judicial | 96536 | 104 | 99,9 % | 928,2x |
| 2387 | 2.2.5 Declaración sobre el Femicidio | Familia | 95131 | 100 | 99,9 % | 951,3x |
| 2388 | 2.2.5 Valoración de acuerdo a las | Familia | 100107 | 58 | 99,9 % | 1726,0x |
| 2389 | 2.2.6 Recomendación General 35 del Comité CEDAW | Familia | 95131 | 101 | 99,9 % | 941,9x |
| 2390 | 2.3              Interés superior | Familia | 65085 | 44 | 99,9 % | 1479,2x |
| 2391 | 2.3             Competencia de los juzgadosno | Judicial | 52128 | 68 | 99,9 % | 766,6x |
| 2392 | 2.3           Principal jurisprudencia sobre igualdad | Judicial | 87237 | 63 | 99,9 % | 1384,7x |
| 2393 | 2.3          Principio de corresponsabilidad, Cuidado | Familia | 65192 | 63 | 99,9 % | 1034,8x |
| 2394 | 2.3       La competencia en razón | Laboral | 71986 | 65 | 99,9 % | 1107,5x |
| 2395 | 2.3     Contenido y alcance del Principio de | Administrativo | 89720 | 81 | 99,9 % | 1107,7x |
| 2396 | 2.3     Estándares internacionales sobre identidad de | Judicial | 93914 | 50 | 99,9 % | 1878,3x |
| 2397 | 2.3     Principios en materia de protección de datos | Constitucional | 104063 | 66 | 99,9 % | 1576,7x |
| 2398 | 2.3     Supuesto | Judicial | 64632 | 61 | 99,9 % | 1059,5x |
| 2399 | 2.3 A fin de asegurar una mayor flexibilidad, compatible con el tipo y la | Penal | 194788 | 159 | 99,9 % | 1225,1x |
| 2400 | 2.3. Toda deuda contraída por la mujer con mandato general o especial del marido | Familia | 136567 | 180 | 99,9 % | 758,7x |
| 2401 | 2.3.1 El plan estratégico institucional | Procesal | 94881 | 115 | 99,9 % | 825,1x |
| 2402 | 2.3.1 Obligaciones del Estado en materia | Familia | 95131 | 67 | 99,9 % | 1419,9x |
| 2403 | 2.3.1 Principio general de legitimación | Judicial | 96536 | 89 | 99,9 % | 1084,7x |
| 2404 | 2.3.1 Prueba testimonial | Familia | 100107 | 52 | 99,9 % | 1925,1x |
| 2405 | 2.3.1.1 Tipicidad objetiva | Penal | 119528 | 113 | 99,9 % | 1057,8x |
| 2406 | 2.3.1.2 Tipicidad subjetiva | Penal | 119528 | 101 | 99,9 % | 1183,4x |
| 2407 | 2.3.1.3.3. Multy Track | Procesal | 96699 | 126 | 99,9 % | 767,5x |
| 2408 | 2.3.2 Acciones afirmativas en el | Judicial | 81476 | 101 | 99,9 % | 806,7x |
| 2409 | 2.3.2 Estándares jurídicos relacionados | Familia | 95131 | 58 | 99,9 % | 1640,2x |
| 2410 | 2.3.2 Juicio oral | Penal | 57066 | 84 | 99,9 % | 679,4x |
| 2411 | 2.3.2 Principio de lealtad y legalidad | Judicial | 96536 | 100 | 99,9 % | 965,4x |
| 2412 | 2.3.2 Producción de la prueba testimonial | Familia | 100107 | 120 | 99,9 % | 834,2x |
| 2413 | 2.3.2.1 El “problema” de la culpabilidad | Penal | 119528 | 98 | 99,9 % | 1219,7x |
| 2414 | 2.3.2.2 De la culpabilidad sin juicio de reproche a | Penal | 119528 | 113 | 99,9 % | 1057,8x |
| 2415 | 2.3.3 Auto acordado N° 71-2016 de la Corte Suprema | Procesal | 94881 | 115 | 99,9 % | 825,1x |
| 2416 | 2.3.3 Estándares especiales aplicables a los casos | Familia | 95131 | 87 | 99,9 % | 1093,5x |
| 2417 | 2.3.3 Principio de finalidad | Judicial | 96536 | 65 | 99,9 % | 1485,2x |
| 2418 | 2.3.3 Prueba pericial | Familia | 100107 | 66 | 99,9 % | 1516,8x |
| 2419 | 2.3.3.3 El problema de las “excusas” que podría esgrimir | Penal | 119528 | 126 | 99,9 % | 948,6x |
| 2420 | 2.3.4 Declaración de partes | Familia | 100107 | 76 | 99,9 % | 1317,2x |
| 2421 | 2.3.4 Material complementario | Familia | 95131 | 58 | 99,9 % | 1640,2x |
| 2422 | 2.3.4 Proporcionalidad | Judicial | 96536 | 92 | 99,9 % | 1049,3x |
| 2423 | 2.3.5 Calidad | Judicial | 96536 | 107 | 99,9 % | 902,2x |
| 2424 | 2.3.5 Medios de prueba no regulados expresamente | Familia | 100107 | 102 | 99,9 % | 981,4x |
| 2425 | 2.3.6 Principio de transparencia | Judicial | 96536 | 101 | 99,9 % | 955,8x |
| 2426 | 2.3.6 Valoración de la prueba | Familia | 100107 | 106 | 99,9 % | 944,4x |
| 2427 | 2.3.6.1 El juez y los hechos | Familia | 100107 | 123 | 99,9 % | 813,9x |
| 2428 | 2.3.6.1 Oportunidad | Judicial | 96536 | 54 | 99,9 % | 1787,7x |
| 2429 | 2.3.6.2 Requisitos | Judicial | 96536 | 98 | 99,9 % | 985,1x |
| 2430 | 2.3.6.3 Consagración legal en Chile | Judicial | 96536 | 111 | 99,9 % | 869,7x |
| 2431 | 2.3.6.3 Errores de razonamiento | Familia | 100107 | 102 | 99,9 % | 981,4x |
| 2432 | 2.3.6.4 Requisitos de la fundamentación | Familia | 100107 | 96 | 99,9 % | 1042,8x |
| 2433 | 2.3.7 Principio de responsabilidad | Judicial | 96536 | 87 | 99,9 % | 1109,6x |
| 2434 | 2.4           Libre investigación de la | Familia | 65085 | 68 | 99,9 % | 957,1x |
| 2435 | 2.4           Los deberes de quienes realizan | Judicial | 96536 | 58 | 99,9 % | 1664,4x |
| 2436 | 2.4        Definición | Familia | 65192 | 49 | 99,9 % | 1330,4x |
| 2437 | 2.4     El procedimiento de distribución | Procesal | 94881 | 55 | 99,9 % | 1725,1x |
| 2438 | 2.4     Formas en que las Cortes de Apelaciones conocen | Judicial | 54457 | 66 | 99,9 % | 825,1x |
| 2439 | 2.4     Principios que guían el establecimiento | Administrativo | 89720 | 89 | 99,9 % | 1008,1x |
| 2440 | 2.4    Algunas cuestiones importantes en | Laboral | 71986 | 50 | 99,9 % | 1439,7x |
| 2441 | 2.4.    Los arts. 988 a 990 y el 992 y la Ley Nº 20.830, al regular la sucesión | Familia | 190697 | 176 | 99,9 % | 1083,5x |
| 2442 | 2.4. El case management, los acuerdos y la solución alternativa de conflictos | Procesal | 96699 | 119 | 99,9 % | 812,6x |
| 2443 | 2.4. Toda deuda contraída por los cónyuges conjuntamente o en que la mujer se | Familia | 136567 | 156 | 99,9 % | 875,4x |
| 2444 | 2.4.1 Propósito y fines de la ley | Judicial | 81476 | 92 | 99,9 % | 885,6x |
| 2445 | 2.4.1 Sus límites y deberes | Laboral | 100583 | 114 | 99,9 % | 882,3x |
| 2446 | 2.4.1 Violencia respecto de NNA como un | Familia | 95131 | 89 | 99,9 % | 1068,9x |
| 2447 | 2.4.2 Definición de discriminación arbitraria | Judicial | 81476 | 44 | 99,9 % | 1851,7x |
| 2448 | 2.4.2 El derecho de las personas mayores a vivir | Familia | 95131 | 96 | 99,9 % | 990,9x |
| 2449 | 2.4.2.1 Principios de las Naciones Unidas | Familia | 95131 | 93 | 99,9 % | 1022,9x |
| 2450 | 2.4.2.2 Convención Interamericana sobre | Familia | 95131 | 87 | 99,9 % | 1093,5x |
| 2451 | 2.4.3 Categorías sospechosas | Judicial | 81476 | 118 | 99,9 % | 690,5x |
| 2452 | 2.4.3 El derecho de las personas con discapacidad | Familia | 95131 | 88 | 99,9 % | 1081,0x |
| 2453 | 2.4.3 Obediencia, fidelidad, lealtad | Laboral | 100583 | 100 | 99,9 % | 1005,8x |
| 2454 | 2.4.3.1 Principios para la protección de los | Familia | 95131 | 85 | 99,9 % | 1119,2x |
| 2455 | 2.4.3.2 Convención sobre los Derechos | Familia | 95131 | 92 | 99,9 % | 1034,0x |
| 2456 | 2.4.4 Prescripción de los derechos laborales y de | Laboral | 100583 | 71 | 99,9 % | 1416,7x |
| 2457 | 2.4.4.1 Ideología, opinión política, religión | Judicial | 81476 | 67 | 99,9 % | 1216,1x |
| 2458 | 2.4.4.2 Nacionalidad/nación | Judicial | 81476 | 84 | 99,9 % | 970,0x |
| 2459 | 2.4.4.3 Raza, etnia o grupo social | Judicial | 81476 | 48 | 99,9 % | 1697,4x |
| 2460 | 2.4.4.4 Sexo, la orientación sexual e identidad de género | Judicial | 81476 | 53 | 99,9 % | 1537,3x |
| 2461 | 2.4.4.5 Edad y filiación | Judicial | 81476 | 68 | 99,9 % | 1198,2x |
| 2462 | 2.4.4.6 Apariencia personal | Judicial | 81476 | 88 | 99,9 % | 925,9x |
| 2463 | 2.4.4.7 Enfermedad o discapacidad | Judicial | 81476 | 49 | 99,9 % | 1662,8x |
| 2464 | 2.4.5.1 Situación socioeconómica | Judicial | 81476 | 89 | 99,9 % | 915,5x |
| 2465 | 2.4.5.2 Idioma | Judicial | 81476 | 94 | 99,9 % | 866,8x |
| 2466 | 2.4.5.3 La sindicación o participación en | Judicial | 81476 | 83 | 99,9 % | 981,6x |
| 2467 | 2.4.5.4 El estado civil | Judicial | 81476 | 91 | 99,9 % | 895,3x |
| 2468 | 2.4.5.5 La maternidad, la lactancia | Judicial | 81476 | 76 | 99,9 % | 1072,1x |
| 2469 | 2.4.5.6 Expresión de género | Judicial | 81476 | 53 | 99,9 % | 1537,3x |
| 2470 | 2.4.6 Agravante de cometer un delito con | Judicial | 81476 | 105 | 99,9 % | 776,0x |
| 2471 | 2.4.6.1 Ámbito de aplicación de la agravante | Judicial | 81476 | 65 | 99,9 % | 1253,5x |
| 2472 | 2.4.6.2 Fundamento de la agravante | Judicial | 81476 | 78 | 99,9 % | 1044,6x |
| 2473 | 2.4.6.3 Las causales de discriminación contenidas | Judicial | 81476 | 100 | 99,9 % | 814,8x |
| 2474 | 2.4.6.4 El error en las cualidades de la víctima | Judicial | 81476 | 93 | 99,9 % | 876,1x |
| 2475 | 2.4.6.5 La comunicabilidad de la circunstancia | Judicial | 81476 | 79 | 99,9 % | 1031,3x |
| 2476 | 2.5               Acuerdo de Asociación entre la Comunidad | Constitucional | 104063 | 54 | 99,9 % | 1927,1x |
| 2477 | 2.5     Disposiciones generales | Judicial | 64632 | 48 | 99,9 % | 1346,5x |
| 2478 | 2.5     El funcionamiento | Judicial | 54457 | 53 | 99,9 % | 1027,5x |
| 2479 | 2.5   Organización | Laboral | 71986 | 93 | 99,9 % | 774,0x |
| 2480 | 2.5 Acuerdo de Asociación entre la Comunidad Europea y Chile y sus efectos en materia de protección | Constitucional | 104063 | 55 | 99,9 % | 1892,1x |
| 2481 | 2.5.1 Derecho de acceso | Judicial | 96536 | 105 | 99,9 % | 919,4x |
| 2482 | 2.5.1 Determinación convencional | Familia | 65192 | 83 | 99,9 % | 785,4x |
| 2483 | 2.5.1 El perfil de cargo | Procesal | 94881 | 104 | 99,9 % | 912,3x |
| 2484 | 2.5.1 La jurisdicción internacional | Penal | 121924 | 98 | 99,9 % | 1244,1x |
| 2485 | 2.5.1 Obligaciones y derechos que provienen | Administrativo | 89720 | 92 | 99,9 % | 975,2x |
| 2486 | 2.5.2 Derecho de rectificación | Judicial | 96536 | 96 | 99,9 % | 1005,6x |
| 2487 | 2.5.2 La descripción de cargo | Procesal | 94881 | 96 | 99,9 % | 988,3x |
| 2488 | 2.5.2 La máxima aut dedere, aut judicare | Penal | 121924 | 102 | 99,9 % | 1195,3x |
| 2489 | 2.5.2 Obligaciones y derechos que provienen del | Administrativo | 89720 | 128 | 99,9 % | 700,9x |
| 2490 | 2.5.3 Derecho de cancelación o supresión | Judicial | 96536 | 87 | 99,9 % | 1109,6x |
| 2491 | 2.5.3 La jurisdicción penal internacional | Penal | 121924 | 96 | 99,9 % | 1270,0x |
| 2492 | 2.5.6 Plazos | Judicial | 64632 | 84 | 99,9 % | 769,4x |
| 2493 | 2.6       Compensación | Familia | 65192 | 57 | 99,9 % | 1143,7x |
| 2494 | 2.6     Reclamos, plazos | Administrativo | 89720 | 76 | 99,9 % | 1180,5x |
| 2495 | 2.6.1 Concepto | Judicial | 79146 | 100 | 99,9 % | 791,5x |
| 2496 | 2.6.1 Derecho de oposición | Judicial | 96536 | 91 | 99,9 % | 1060,8x |
| 2497 | 2.6.1 Juez y Administración | Procesal | 101194 | 52 | 99,9 % | 1946,0x |
| 2498 | 2.6.1.1 Misión y objetivo principal del cargo | Procesal | 94881 | 94 | 99,9 % | 1009,4x |
| 2499 | 2.6.1.2 Deberes y responsabilidades | Procesal | 94881 | 61 | 99,9 % | 1555,4x |
| 2500 | 2.6.1.2 Principios y características de los procedimientos | Laboral | 71986 | 88 | 99,9 % | 818,0x |
| 2501 | 2.6.1.3 Principales funciones | Procesal | 94881 | 66 | 99,9 % | 1437,6x |
| 2502 | 2.6.1.4 Instancias con las que se relaciona | Procesal | 94881 | 106 | 99,9 % | 895,1x |
| 2503 | 2.6.2 Administrador | Procesal | 94881 | 52 | 99,9 % | 1824,6x |
| 2504 | 2.6.2 Derecho a no ser objeto de | Judicial | 96536 | 101 | 99,9 % | 955,8x |
| 2505 | 2.6.2 Estructura | Judicial | 79146 | 91 | 99,9 % | 869,7x |
| 2506 | 2.6.2.1 Misión y objetivo principal del cargo | Procesal | 94881 | 106 | 99,9 % | 895,1x |
| 2507 | 2.6.2.2 Deberes y responsabilidades | Procesal | 94881 | 75 | 99,9 % | 1265,1x |
| 2508 | 2.6.2.3 Principales funciones | Procesal | 94881 | 119 | 99,9 % | 797,3x |
| 2509 | 2.6.2.4 Instancias con las que se relaciona | Procesal | 94881 | 122 | 99,9 % | 777,7x |
| 2510 | 2.6.3 Clasificación | Judicial | 79146 | 88 | 99,9 % | 899,4x |
| 2511 | 2.6.3 Derecho a la limitación del tratamiento | Judicial | 96536 | 72 | 99,9 % | 1340,8x |
| 2512 | 2.6.4 Derecho a la portabilidad de los datos personales | Judicial | 96536 | 65 | 99,9 % | 1485,2x |
| 2513 | 2.6.4 Procedimientos de desarrollo del párrafo | Judicial | 79146 | 105 | 99,9 % | 753,8x |
| 2514 | 2.6.5 Técnicas y recursos para organizar | Judicial | 79146 | 96 | 99,9 % | 824,4x |
| 2515 | 2.7     Consejo para la | Administrativo | 89720 | 98 | 99,9 % | 915,5x |
| 2516 | 2.7     RDR con los abuelos | Familia | 65192 | 66 | 99,9 % | 987,8x |
| 2517 | 2.7. Bienes muebles e inmuebles adquiridos por la mujer en virtud del art. 166 del | Familia | 136567 | 175 | 99,9 % | 780,4x |
| 2518 | 2.7.1 Cohesión del párrafo y frases desordenadas | Judicial | 79146 | 110 | 99,9 % | 719,5x |
| 2519 | 2.7.1 Procedimiento de aplicación general | Laboral | 71986 | 101 | 99,9 % | 712,7x |
| 2520 | 2.7.2 Procedimiento monitorio | Laboral | 71986 | 70 | 99,9 % | 1028,4x |
| 2521 | 2.7.3 Procedimiento de reclamación de multas y demás | Laboral | 71986 | 106 | 99,9 % | 679,1x |
| 2522 | 2.7.4 Procedimiento de tutela laboral | Laboral | 71986 | 94 | 99,9 % | 765,8x |
| 2523 | 2.8               El régimen infraccional | Judicial | 96536 | 81 | 99,9 % | 1191,8x |
| 2524 | 2.8     Excepciones al deber | Administrativo | 89720 | 55 | 99,9 % | 1631,3x |
| 2525 | 2.8    La tramitación de un procedimiento | Laboral | 71986 | 45 | 99,9 % | 1599,7x |
| 2526 | 2.8. Bienes inmuebles adquiridos por la mujer por prescripción, en virtud del | Familia | 136567 | 152 | 99,9 % | 898,5x |
| 2527 | 2.8.1 El debido cumplimiento de las funciones del órgano | Administrativo | 89720 | 131 | 99,9 % | 684,9x |
| 2528 | 2.8.1 Reglamentación temprana de la consulta del | Judicial | 134465 | 106 | 99,9 % | 1268,5x |
| 2529 | 2.8.1 Reglas de la ortografía acentual | Judicial | 79146 | 110 | 99,9 % | 719,5x |
| 2530 | 2.8.1.1 Otras reglas de acentuación ortográfica | Judicial | 79146 | 65 | 99,9 % | 1217,6x |
| 2531 | 2.8.2 Los derechos de las personas | Administrativo | 89720 | 89 | 99,9 % | 1008,1x |
| 2532 | 2.8.2 Principales reglas de la ortografía literal | Judicial | 79146 | 88 | 99,9 % | 899,4x |
| 2533 | 2.8.2 Reglamentación doméstica actualmente | Judicial | 134465 | 71 | 99,9 % | 1893,9x |
| 2534 | 2.8.2.2 Uso de la letra v | Judicial | 79146 | 97 | 99,9 % | 815,9x |
| 2535 | 2.8.2.3 Uso de la letra h | Judicial | 79146 | 54 | 99,9 % | 1465,7x |
| 2536 | 2.8.2.4 Uso de la letra g | Judicial | 79146 | 88 | 99,9 % | 899,4x |
| 2537 | 2.8.2.5 Uso de la letra j | Judicial | 79146 | 89 | 99,9 % | 889,3x |
| 2538 | 2.8.2.6 Uso de las letras c y s | Judicial | 79146 | 84 | 99,9 % | 942,2x |
| 2539 | 2.8.2.7 Uso de la letra z | Judicial | 79146 | 74 | 99,9 % | 1069,5x |
| 2540 | 2.8.2.8 Uso de la rr y de la y | Judicial | 79146 | 105 | 99,9 % | 753,8x |
| 2541 | 2.8.2.9 Palabras homófonas | Judicial | 79146 | 55 | 99,9 % | 1439,0x |
| 2542 | 2.8.3 La seguridad de la nación | Administrativo | 89720 | 105 | 99,9 % | 854,5x |
| 2543 | 2.8.4 El interés nacional | Administrativo | 89720 | 109 | 99,9 % | 823,1x |
| 2544 | 2.8.5 Causal genérica | Administrativo | 89720 | 128 | 99,9 % | 700,9x |
| 2545 | 2.8.5 La audiencia de juicio (art. 454 del CT) | Laboral | 71986 | 106 | 99,9 % | 679,1x |
| 2546 | 2.8.6 La sentencia | Laboral | 71986 | 101 | 99,9 % | 712,7x |
| 2547 | 2.8.7 Eventuales recursos | Laboral | 71986 | 81 | 99,9 % | 888,7x |
| 2548 | 2.9.1 La fase administrativa | Laboral | 71986 | 89 | 99,9 % | 808,8x |
| 2549 | 2.9.2   Inicio del procedimiento | Laboral | 71986 | 72 | 99,9 % | 999,8x |
| 2550 | 2.9.3 Análisis de admisibilidad y | Laboral | 71986 | 104 | 99,9 % | 692,2x |
| 2551 | 2.9.5 Reclamo de la resolución en el | Laboral | 71986 | 89 | 99,9 % | 808,8x |
| 2552 | 2.9.6 La audiencia única | Laboral | 71986 | 85 | 99,9 % | 846,9x |
| 2553 | 20 Así entendida, numerosos autores sostienen que la idea de progresividad y no | Judicial | 81675 | 118 | 99,9 % | 692,2x |
| 2554 | 20 Considerando tercero: «Que ahora la madre señala estar en condiciones de | Familia | 97488 | 136 | 99,9 % | 716,8x |
| 2555 | 20 Corte Suprema, rol 25.388-21, del 5 de julio de 2021. Expone la evolución de la | Penal | 97633 | 123 | 99,9 % | 793,8x |
| 2556 | 20 El resto de las medidas consistía en extender la cobertura del Sistema de Alta | Penal | 178516 | 149 | 99,9 % | 1198,1x |
| 2557 | 20 La subinscripción mediante anotación marginal en el Registro de Propiedad | Familia | 123490 | 110 | 99,9 % | 1122,6x |
| 2558 | 20 Para más información, véase «Historia de la Ley 20.393», pp. 3-4, disponible en | Judicial | 62514 | 81 | 99,9 % | 771,8x |
| 2559 | 20 Para un modelo prescriptivo de esquemas interpretativos, como el de Alexy, la | Judicial | 92792 | 113 | 99,9 % | 821,2x |
| 2560 | 20 Principios básicos sobre la utilización de programas de justicia restaurativa en | Penal | 86906 | 76 | 99,9 % | 1143,5x |
| 2561 | 20 Se evidencia que la distinción del legislador de 2016 sigue en este punto las | Judicial | 78893 | 113 | 99,9 % | 698,2x |
| 2562 | 20 Sentencia del caso Inspección Provincial del Trabajo de Valdivia/ Transportes | Laboral | 74025 | 63 | 99,9 % | 1175,0x |
| 2563 | 20 Sentencia del caso Sindicato Nacional de Trabajadores de Empresa Banco Ripley | Laboral | 74025 | 105 | 99,9 % | 705,0x |
| 2564 | 20 También puede proceder en el caso de término del matrimonio conforme al | Familia | 123490 | 81 | 99,9 % | 1524,6x |
| 2565 | 20.   Elena, S. (2015): Datos abiertos para una justi- | Administrativo | 89720 | 105 | 99,9 % | 854,5x |
| 2566 | 20. Boletín N° 12.430-04. Proyecto de ley que modifica la Ley | Judicial | 89476 | 87 | 99,9 % | 1028,5x |
| 2567 | 20. Corte de Apelaciones de Santiago, rol N° 1090- | Familia | 100107 | 84 | 99,9 % | 1191,8x |
| 2568 | 20. Defecto de organización: concepto usado para | Penal | 119528 | 78 | 99,9 % | 1532,4x |
| 2569 | 20. Expresa al afecto la parte final de este inciso: “Con todo, los depósitos convenidos | Familia | 136567 | 179 | 99,9 % | 762,9x |
| 2570 | 20. Implementación del Plan Nacional de la Lectura 2015 – 2020 (ID | Constitucional | 177323 | 159 | 99,9 % | 1115,2x |
| 2571 | 20. Ley N° 20.480. Modifica el Código Penal y la Ley Nº 20.066 sobre | Judicial | 89476 | 71 | 99,9 % | 1260,2x |
| 2572 | 20. Principio de Relevancia: Se presume relevante | Administrativo | 89720 | 72 | 99,9 % | 1246,1x |
| 2573 | 20. Si se viere comprometida la seguridad o conservación de los bienes comunes o de las | Civil | 192585 | 122 | 99,9 % | 1578,6x |
| 2574 | 20. Velar por que los no ciudadanos detenidos o encarcelados en la | Judicial | 62514 | 79 | 99,9 % | 791,3x |
| 2575 | 20. ZAVALA O., José Luis (2009): Recurso de protec- | Judicial | 105809 | 96 | 99,9 % | 1102,2x |
| 2576 | 20.084. Si la pena privativa o restrictiva de libertad se extiende entre | Penal | 194788 | 192 | 99,9 % | 1014,5x |
| 2577 | 20.393. Referencia al modelo de responsabilidad | Penal | 119528 | 102 | 99,9 % | 1171,8x |
| 2578 | 20.609. En efecto, solo se enumeran una serie de garantías | Judicial | 81476 | 92 | 99,9 % | 885,6x |
| 2579 | 20.830. La segunda, carente de regulación sistemática, pues diversas normas | Familia | 190697 | 195 | 99,9 % | 977,9x |
| 2580 | 2000. Serie C número 68, párrafo 101; y caso de los «Niños de la Calle» | Judicial | 144656 | 170 | 99,9 % | 850,9x |
| 2581 | 200027. Se trata de un caso en el que se demanda el cumplimiento | Civil | 142015 | 146 | 99,9 % | 972,7x |
| 2582 | 2001. Este documento no ha sido oficialmente promulgado como | Constitucional | 121906 | 65 | 99,9 % | 1875,5x |
| 2583 | 2002. La Corte tiene su sede en La Haya, Países Bajos, y posee tres | Penal | 121924 | 66 | 99,9 % | 1847,3x |
| 2584 | 2005. En los últimos tres años, se registraron aumentos significativos en | Constitucional | 177323 | 172 | 99,9 % | 1030,9x |
| 2585 | 2005. Esta ley dispone un juicio ejecutivo muy rápido y expedito para | Laboral | 100583 | 81 | 99,9 % | 1241,8x |
| 2586 | 2008. Asimismo, realiza actividad do- | Laboral | 100583 | 63 | 99,9 % | 1596,6x |
| 2587 | 2008.423 En ella se reconocen los derechos de todo individuo en especial para | Constitucional | 121906 | 117 | 99,9 % | 1041,9x |
| 2588 | 2009. Esta prohibición le ha producido una perturbación psicológica, por el estrés y la | Civil | 192585 | 150 | 99,9 % | 1283,9x |
| 2589 | 2011. Fabián Elorriaga de Bonis (coordinador), (Santiago de Chile, AbeledoPerrot – Thomson | Civil | 171433 | 179 | 99,9 % | 957,7x |
| 2590 | 2012. Párrafo 271.                                           materia de identidad de género. [aut. libro] | Judicial | 93914 | 65 | 99,9 % | 1444,8x |
| 2591 | 2015. Ello se tradujo en un tiempo muy reducido para ejecutar todas | Judicial | 83934 | 110 | 99,9 % | 763,0x |
| 2592 | 2015.08.31 Acta Nº 142-2015, texto refundido del auto acordado | Procesal | 94881 | 55 | 99,9 % | 1725,1x |
| 2593 | 2018 TUAC Comments Paris, 12 October 2018: “Current OECD reports suggest that minority shareholders | Constitucional | 112823 | 133 | 99,9 % | 848,3x |
| 2594 | 202   DOMÍNGUEZ (2011), pp. 34 y 45. El problema de la culpa presunta contractual y las obligaciones de medios | Civil | 142015 | 114 | 99,9 % | 1245,7x |
| 2595 | 2020. El 15 de noviembre de 2020, los cónyuges disuelven la sociedad conyugal y se | Familia | 136567 | 137 | 99,9 % | 996,8x |
| 2596 | 2022-a-1838 | Judicial | 64632 | 46 | 99,9 % | 1405,0x |
| 2597 | 2022-a-1840 | Judicial | 81476 | 110 | 99,9 % | 740,7x |
| 2598 | 2022. En un contexto de incipiente puesta en marcha de la nueva legislación y los | Familia | 97488 | 97 | 99,9 % | 1005,0x |
| 2599 | 2022. Se acreditó que mientras estuvo rebelde no cometió nuevos delitos | Penal | 194788 | 221 | 99,9 % | 881,4x |
| 2600 | 206 Tabla de creación propia en base a la información obtenida de las Normas Nacionales sobre Regulación de | Judicial | 89476 | 81 | 99,9 % | 1104,6x |
| 2601 | 207 Existen dos procedimientos judiciales para la interdicción de una persona con discapacidad intelectual. El | Constitucional | 121906 | 84 | 99,9 % | 1451,3x |
| 2602 | 208 Esta afirmación no implica que los pacientes de esquizofrenia tengan un deterioro cognitivo que afecta su | Constitucional | 121906 | 93 | 99,9 % | 1310,8x |
| 2603 | 21        Cf. www.celade.cepal.org | Judicial | 134465 | 124 | 99,9 % | 1084,4x |
| 2604 | 21       Artículo 62 inciso cuarto del Acta Nº 71-2016 | Judicial | 83934 | 57 | 99,9 % | 1472,5x |
| 2605 | 21 Al tratarse de una figura penal distinta del artículo 248 inciso primero, bien | Penal | 178516 | 141 | 99,9 % | 1266,1x |
| 2606 | 21 Así lo ha precisado la jurisprudencia: «No es la compensación económica una | Familia | 123490 | 158 | 99,9 % | 781,6x |
| 2607 | 21 Cohen (1977: 247 y 248); Taruffo (2009: 227). Resulta sorprenden observar que | Judicial | 150341 | 78 | 99,9 % | 1927,4x |
| 2608 | 21 Este criterio también puede ser utilizado para distinguir la calidad de servidor | Penal | 178516 | 102 | 99,9 % | 1750,2x |
| 2609 | 21 Maturana (2015: 434) explica que existe ultra petita también cuando se altera la | Judicial | 144656 | 166 | 99,9 % | 871,4x |
| 2610 | 21 Nº 3) e inclusión educacional (art. 21 Nº 3) e inclusión escolar | Constitucional | 121906 | 81 | 99,9 % | 1505,0x |
| 2611 | 21 Se trata del primer fallo de una corte internacional que de manera expresa | Penal | 178516 | 171 | 99,9 % | 1044,0x |
| 2612 | 21 Sentencia ministro en visita extraordinaria Juan Araya, rol 3.557-1992, del 28 de | Judicial | 62514 | 59 | 99,9 % | 1059,6x |
| 2613 | 21.   Decreto Supremo N° 26. Ministerio Secretaría | Administrativo | 89720 | 100 | 99,9 % | 897,2x |
| 2614 | 21.   República del Perú. Ley de Transparencia y Acce- | Administrativo | 89720 | 107 | 99,9 % | 838,5x |
| 2615 | 21. CORNEJO, Pablo (2011): “La importancia de las medidas afirmativas para la | Constitucional | 121906 | 94 | 99,9 % | 1296,9x |
| 2616 | 21. Capacitación a funcionarios/as de la Defensoría Penal Pública en | Constitucional | 177323 | 102 | 99,9 % | 1738,5x |
| 2617 | 21. Dar avisos o recordatorios de audiencias, debiendo considerar la | Constitucional | 177323 | 131 | 99,9 % | 1353,6x |
| 2618 | 21. El requisito de imparcialidad tiene dos aspectos. En primer | Judicial | 93914 | 113 | 99,9 % | 831,1x |
| 2619 | 21. Fijarle al copropietario de una unidad que fuere omiso en efectuar las reparaciones | Civil | 192585 | 167 | 99,9 % | 1153,2x |
| 2620 | 21. Las obligaciones de la mujer de tener hijos y criarlos afectan a | Judicial | 89476 | 114 | 99,9 % | 784,9x |
| 2621 | 21. Lex artis: En materia médica, el estándar de | Civil | 142015 | 92 | 99,9 % | 1543,6x |
| 2622 | 21. Nayade Fernández Medel con Clínica Las Condes            Clínica San Carlos S.A. y otro (2018): Corte Su- | Civil | 142015 | 140 | 99,9 % | 1014,4x |
| 2623 | 21. Principio de Oportunidad: Los órganos de la | Administrativo | 89720 | 78 | 99,9 % | 1150,3x |
| 2624 | 21. Proponer al Comité de Administración la adopción de medidas para resguardar el | Civil | 192585 | 98 | 99,9 % | 1965,2x |
| 2625 | 21. Que en relación a este aspecto hay que tener presente que las partes, demandante y de- | Judicial | 79146 | 114 | 99,9 % | 694,3x |
| 2626 | 21. Reclamo de ilegalidad respecto de las actuacio- | Judicial | 105809 | 115 | 99,9 % | 920,1x |
| 2627 | 21. Sobre la igualdad en el matrimonio y en las | Judicial | 89476 | 92 | 99,9 % | 972,6x |
| 2628 | 21. Transversalización de la educación en Derechos Humanos (ID | Constitucional | 177323 | 140 | 99,9 % | 1266,6x |
| 2629 | 21. Un juez(a) puede participar en la discusión de una ley con fines | Procesal | 94881 | 96 | 99,9 % | 988,3x |
| 2630 | 210 BUCKLEY, Timothy J. (2013), “Password Protection Now: An Elaboration on the Need for Federal Password | Laboral | 113458 | 92 | 99,9 % | 1233,2x |
| 2631 | 211 Es importante considerar que para otro sector importante más bien derivaría de “necesidades de vigencia | Penal | 119528 | 131 | 99,9 % | 912,4x |
| 2632 | 212. Palwankar, Umesh (1994): “Medidas que pueden tomar los Estados para | Penal | 121924 | 83 | 99,9 % | 1469,0x |
| 2633 | 214. Pasquier, André (1985): “Derecho Internacional Humanitario y actividades | Penal | 121924 | 89 | 99,9 % | 1369,9x |
| 2634 | 216   CUARTO: Que el artículo 2º de la ley enuncia ejemplarmente como casos de discriminación arbitraria ac- | Constitucional | 121906 | 145 | 99,9 % | 840,7x |
| 2635 | 216. Paul, Vladimir (1971): “Legal Consequences of Conflict between a Treaty and | Penal | 121924 | 76 | 99,9 % | 1604,3x |
| 2636 | 219   SÉPTIMO: Que tras una amplísima relación de los antecedentes, la sentencia enfoca correctamente el con- | Constitucional | 121906 | 148 | 99,9 % | 823,7x |
| 2637 | 219. Párr. 230),34 al señalar que en cuanto al Derecho a la libertad de | Administrativo | 89720 | 107 | 99,9 % | 838,5x |
| 2638 | 22       Causa rol Nº 6030-2018 de la Corte Suprema | Judicial | 83934 | 54 | 99,9 % | 1554,3x |
| 2639 | 22   Sentencia de la Corte Suprema rol 7728-13, Sociedad Concesiones Iquique S.A. con Ilustre Municipalidad de | Judicial | 105809 | 109 | 99,9 % | 970,7x |
| 2640 | 22 Artículo 255 inciso segundo: «Si la conducta descrita en el inciso precedente se | Judicial | 78893 | 110 | 99,9 % | 717,2x |
| 2641 | 22 Cfr. Sentencia del caso Poblete Vilches y otros con Chile, Corte IDH, serie C | Judicial | 81675 | 63 | 99,9 % | 1296,4x |
| 2642 | 22 Considera que: «In fact, this kind of reliance on a whole mesh of evidence is | Judicial | 150341 | 184 | 99,9 % | 817,1x |
| 2643 | 22 Considerando cuarto: «El niño ha asistido al mismo colegio desde que vive con | Familia | 97488 | 119 | 99,9 % | 819,2x |
| 2644 | 22 En ese sentido Vidal Olivares (2009b: 18-20). Por su parte, Corral Talciani | Familia | 123490 | 141 | 99,9 % | 875,8x |
| 2645 | 22 Juzgado de Garantía de Concepción, rit 10510-2012 sentencia, 5 de marzo de | Judicial | 82507 | 55 | 99,9 % | 1500,1x |
| 2646 | 22 La reforma de 1999 no había sido suficiente, ya que se vio severamente afectado | Penal | 178516 | 174 | 99,9 % | 1026,0x |
| 2647 | 22 Para más información, confrontar con STS español, 2/1997 del 29 de noviembre | Judicial | 62514 | 52 | 99,9 % | 1202,2x |
| 2648 | 22 Se destaca la aparición del sistema unido al fenómeno del panamericanismo | Constitucional | 177323 | 153 | 99,9 % | 1159,0x |
| 2649 | 22 Sentencia Tribunal Constitucional 3005, de 22 de noviembre de 2016, califica | Judicial | 144656 | 75 | 99,9 % | 1928,7x |
| 2650 | 22 Sentencia de la Corte de Apelaciones de Concepción, 30 de abril de 2021, rol | Judicial | 150341 | 83 | 99,9 % | 1811,3x |
| 2651 | 22 Sentencia del caso Yáñez con Comercial CCU S. A., Corte de Apelaciones de | Laboral | 74025 | 92 | 99,9 % | 804,6x |
| 2652 | 22 Tal como señala Ferrer (2002), esta premisa también puede afirmar que no se | Judicial | 92792 | 88 | 99,9 % | 1054,5x |
| 2653 | 22. Boletín N° 12.542-04. Proyecto de ley que modifica la Ley N° | Judicial | 89476 | 102 | 99,9 % | 877,2x |
| 2654 | 22. CORTE DE APELACIONES DE CONCEPCIÓN, rol | Familia | 65085 | 68 | 99,9 % | 957,1x |
| 2655 | 22. Corte de Apelaciones de Rancagua, rol N° | Familia | 100107 | 91 | 99,9 % | 1100,1x |
| 2656 | 22. Disolución de la persona jurídica o cancelación de    35. Modelos de imputación: aspectos generales que | Penal | 119528 | 119 | 99,9 % | 1004,4x |
| 2657 | 22. En algunos informes se revelan prácticas coercitivas que tienen | Judicial | 89476 | 106 | 99,9 % | 844,1x |
| 2658 | 22. Incorporar enfoque de derechos humanos en la formación de las | Constitucional | 177323 | 154 | 99,9 % | 1151,4x |
| 2659 | 22. Principio de Gratuidad: Obliga a los órganos y | Administrativo | 89720 | 97 | 99,9 % | 924,9x |
| 2660 | 22. Proveer información y vincular a familias de campamentos no | Constitucional | 177323 | 153 | 99,9 % | 1159,0x |
| 2661 | 22. Si como consecuencia de la decisión que hubiese de adoptar | Procesal | 94881 | 97 | 99,9 % | 978,2x |
| 2662 | 22. UGARTE José Luis (2009): Tutela de derechos | Laboral | 100583 | 79 | 99,9 % | 1273,2x |
| 2663 | 221   NOVENO: Que todos estos razonamientos conducen al rechazo de la apelación presentada por el Senado de | Constitucional | 121906 | 163 | 99,9 % | 747,9x |
| 2664 | 225   Tribunal Constitucional. Requerimiento de inconstitucionalidad presentado por un grupo de senadores que | Judicial | 89476 | 128 | 99,9 % | 699,0x |
| 2665 | 226 Gómez-Jara (2012), p. 168. Se debe considerar que el autor asume como dogma la teoría de los sistemas | Penal | 119528 | 144 | 99,9 % | 830,1x |
| 2666 | 226. Precht Pizarro, Jorge Enrique (1967): “Los tratados internacionales como | Penal | 121924 | 74 | 99,9 % | 1647,6x |
| 2667 | 227.- FICARELLI (2011), p. 74 | Procesal | 96699 | 109 | 99,9 % | 887,1x |
| 2668 | 228 De acuerdo con Pastor (2006), p. 3, la tesis de Gómez-Jara puede resumirse en los siguientes términos: “… | Penal | 119528 | 115 | 99,9 % | 1039,4x |
| 2669 | 229. Con todo, el derecho de acceder a la información pública | Administrativo | 89720 | 111 | 99,9 % | 808,3x |
| 2670 | 229. Puceiro Ripoll, Roberto (2005): “Las normas de jus cogens en el campo del | Penal | 121924 | 91 | 99,9 % | 1339,8x |
| 2671 | 23       Artículo 3º del Acta Nº 85-2019 | Judicial | 83934 | 62 | 99,9 % | 1353,8x |
| 2672 | 23 Antes de la modificación de 2016, incluso se consideran como formas genéricas | Judicial | 78893 | 72 | 99,9 % | 1095,7x |
| 2673 | 23 Esta Observación fue reemplazada por la Observación General número 24 del | Penal | 86906 | 63 | 99,9 % | 1379,5x |
| 2674 | 23 Los autores refieren también la doctrina española en referencia a su Código | Penal | 178516 | 102 | 99,9 % | 1750,2x |
| 2675 | 23 Se ha señalado correctamente que, en caso de existir un error de tipo, referido | Penal | 178516 | 107 | 99,9 % | 1668,4x |
| 2676 | 23 Véase la Convención sobre los Derechos del Niño (artículo 77 letra a), las Reglas | Penal | 86906 | 72 | 99,9 % | 1207,0x |
| 2677 | 23.   CARRASCO-JIMÉNEZ, Edison (2018): “Incriminación del maltrato corpo- | Familia | 95131 | 92 | 99,9 % | 1034,0x |
| 2678 | 23. Boletín N° 12.600-34. Proyecto de ley que modifica el Código del | Judicial | 89476 | 84 | 99,9 % | 1065,2x |
| 2679 | 23. CORTE INTERAMERICANA DE DERECHOS HUMANOS (2018): Cuadernillos | Judicial | 81476 | 49 | 99,9 % | 1662,8x |
| 2680 | 23. Costos Directos de Reproducción: Todos los | Administrativo | 89720 | 87 | 99,9 % | 1031,3x |
| 2681 | 23. Decreto Nº 300/1994, autoriza la organización y funcionamiento de cursos | Constitucional | 121906 | 70 | 99,9 % | 1741,5x |
| 2682 | 23. Fresia Gutiérrez Sánchez con Servicio de Salud             Suprema, 29 de agosto de 2017, Rol N° 101769- | Civil | 142015 | 74 | 99,9 % | 1919,1x |
| 2683 | 23. Hay amplio acuerdo en que cuando se dispone libremente de | Judicial | 89476 | 102 | 99,9 % | 877,2x |
| 2684 | 23. Instituto Nacional de Estadísticas (2017): Infor- | Familia | 65085 | 76 | 99,9 % | 856,4x |
| 2685 | 23. Ley N° 20.609. Establece medidas contra la | Judicial | 89476 | 115 | 99,9 % | 778,1x |
| 2686 | 23. Reducir brecha digital y conectividad para grupos excluidos (ID | Constitucional | 177323 | 152 | 99,9 % | 1166,6x |
| 2687 | 23. VALDÉS DAL-RE, Fernando (2002): “Poderes del | Laboral | 100583 | 76 | 99,9 % | 1323,5x |
| 2688 | 230. Asimismo, para garantizar el ejercicio pleno y efectivo de | Administrativo | 89720 | 106 | 99,9 % | 846,4x |
| 2689 | 231. Igualmente, la Corte destaca la obligación de garantizar la | Administrativo | 89720 | 104 | 99,9 % | 862,7x |
| 2690 | 231. Reece Thomas, Katherine y Small, Joan (2003): “Human Rights and State | Penal | 121924 | 75 | 99,9 % | 1625,7x |
| 2691 | 233. Requa, Marny A. (2012): “A Human Rights Triumph? Dictatorship-era Crimes | Penal | 121924 | 68 | 99,9 % | 1793,0x |
| 2692 | 235. La Corte reitera que el estereotipo de género se refiere a una | Judicial | 87237 | 128 | 99,9 % | 681,5x |
| 2693 | 237. Ríos Rodríguez, Jacobo (2007): “Límites y beneficiarios de la inmunidad de | Penal | 121924 | 78 | 99,9 % | 1563,1x |
| 2694 | 24   Corte IDH (2005), caso Hermanas Serrano Cruz vs. El Salvador, voto disidente del juez Manuel E. Ventura | Familia | 65085 | 62 | 99,9 % | 1049,8x |
| 2695 | 24 Alexy (1993: 81-115) en el capítulo sobre estructura de las normas de derecho | Judicial | 92792 | 66 | 99,9 % | 1405,9x |
| 2696 | 24 Artículo 49, inciso segundo: «En los juicios seguidos ante tribunales inferiores | Judicial | 89450 | 113 | 99,9 % | 791,6x |
| 2697 | 24 BCN, Historia de la Ley 20.968, (p.30): «El objetivo era incrementar la pena del | Judicial | 78893 | 101 | 99,9 % | 781,1x |
| 2698 | 24 Como refiere Montero La Rubia (2007: 68), la jurisprudencia española ha re- | Penal | 97633 | 87 | 99,9 % | 1122,2x |
| 2699 | 24 Como se adelantó, en caso de no pago de la multa impuesta por la comisión de | Penal | 97633 | 109 | 99,9 % | 895,7x |
| 2700 | 24 Conforme destaca Diez de Velasco (2007: 700), esta última facultad de visitas | Constitucional | 177323 | 169 | 99,9 % | 1049,2x |
| 2701 | 24 Considerando noveno: «En relación al niño, el evaluador deja constancia de | Familia | 97488 | 135 | 99,9 % | 722,1x |
| 2702 | 24 De ahí la clasificación ampliamente aceptada por la doctrina sobre cohecho | Penal | 178516 | 97 | 99,9 % | 1840,4x |
| 2703 | 24 En este sentido, véase Corte de Apelaciones de Arica, causa rol 45-2022; Corte | Judicial | 87950 | 111 | 99,9 % | 792,3x |
| 2704 | 24 En la sección anterior señalábamos que resultaba más adecuada denominar la | Penal | 178516 | 97 | 99,9 % | 1840,4x |
| 2705 | 24 Ilustrísima Corte de Apelaciones de Puerto Montt, rol 741-2020 sentencia, 9 | Judicial | 82507 | 66 | 99,9 % | 1250,1x |
| 2706 | 24 La distinción entre diversos capítulos de imparcialidad de la persona experta | Procesal | 86112 | 81 | 99,9 % | 1063,1x |
| 2707 | 24 Los supuestos básicos del debido proceso en los instrumentos internacionales | Penal | 86906 | 79 | 99,9 % | 1100,1x |
| 2708 | 24 Salvo excepciones, como la prueba anticipada que se produce en la audiencia | Procesal | 86112 | 127 | 99,9 % | 678,0x |
| 2709 | 24 Sentencia de la Corte de Apelaciones de Valdivia, rol 642-05, 2 de septiembre | Familia | 123490 | 102 | 99,9 % | 1210,7x |
| 2710 | 24 Véase «PwC Women in Work Index: Chile es el país de la OCDE que más | Laboral | 98828 | 85 | 99,9 % | 1162,7x |
| 2711 | 24. BARROS BOURIE, Enrique (2007), Tratado de res- | Laboral | 113458 | 106 | 99,9 % | 1070,4x |
| 2712 | 24. Boletín N° 12.702-34. Proyecto de ley que modifica la Ley | Judicial | 89476 | 94 | 99,9 % | 951,9x |
| 2713 | 24. CORTE DE APELACIONES DE CONCEPCIÓN, rol | Familia | 65085 | 72 | 99,9 % | 904,0x |
| 2714 | 24. National Human Genome Research Institute | Familia | 65085 | 91 | 99,9 % | 715,2x |
| 2715 | 24. Realizar visitas anuales al Museo de la Memoria y los Derechos | Constitucional | 177323 | 114 | 99,9 % | 1555,5x |
| 2716 | 24. Si no hay acuerdo en la forma de entrega del bien expropiado ¿qué debe hacer el ente | Judicial | 105809 | 148 | 99,9 % | 714,9x |
| 2717 | 24. Un juez(a) que aprovecha sus funciones jurisdiccionales para | Procesal | 94881 | 101 | 99,9 % | 939,4x |
| 2718 | 240. Rodríguez Yagüe, Cristina (2007): “Criterios de resolución de conflictos entre la | Penal | 121924 | 98 | 99,9 % | 1244,1x |
| 2719 | 242   Esto sería consecuencia directa de su alto grado de indeterminación respecto de las conductas que regula | Constitucional | 121906 | 81 | 99,9 % | 1505,0x |
| 2720 | 244      Cfr. FERDINANDUSSE (2006), pp. 239-240; AGUILAR (2008), p. 152; DOBOVSEK (2008) pp. 58-66; JESSBER- | Penal | 121924 | 102 | 99,9 % | 1195,3x |
| 2721 | 244. Salinas Burgos, Hernán (1998): “El Derecho Internacional Humanitario y los | Penal | 121924 | 87 | 99,9 % | 1401,4x |
| 2722 | 246. Santos Vara, Juan (2006): “La jurisdicción de los tribunales españoles para | Penal | 121924 | 83 | 99,9 % | 1469,0x |
| 2723 | 247. Sato, Tetsuo (1987): “Review of Professor Takeshi Minagawa’s Kokusaiho Kenkyu | Penal | 121924 | 80 | 99,9 % | 1524,0x |
| 2724 | 25       Dicom, después Dicom-Equifax o solo Equifax, es una empresa con amplia presencia en el mercado de la | Judicial | 96536 | 85 | 99,9 % | 1135,7x |
| 2725 | 25 Artículo 7: «El tribunal no podrá fijar como monto de la pensión una suma o | Judicial | 89450 | 96 | 99,9 % | 931,8x |
| 2726 | 25 Corresponde a una conducta activa, a diferencia de la omisiva sancionada en el | Penal | 97633 | 131 | 99,9 % | 745,3x |
| 2727 | 25 Eso explica la Convención para Combatir el Cohecho a Servidores Públicos | Penal | 178516 | 104 | 99,9 % | 1716,5x |
| 2728 | 25 N° 1 del Pacto de San José de Costa Rica en relación con el 1° N° | Judicial | 87237 | 128 | 99,9 % | 681,5x |
| 2729 | 25 Para más información, véase Comité Internacional de la Cruz Roja (2006: 6 y | Constitucional | 177323 | 180 | 99,9 % | 985,1x |
| 2730 | 25 Para más información, véase «Historia de la Ley 19.906», disponible en https:// | Judicial | 62514 | 42 | 99,9 % | 1488,4x |
| 2731 | 25 Se debiera entender que se refiere al sobreseimiento definitivo, regulado en el | Penal | 86906 | 75 | 99,9 % | 1158,7x |
| 2732 | 25 Sin embargo, si el fundamento del delito fuese principalmente la infracción al | Penal | 178516 | 97 | 99,9 % | 1840,4x |
| 2733 | 25 Todos pueden ser solo cometidos por funcionarios públicos, o por quien ejerza | Judicial | 78893 | 113 | 99,9 % | 698,2x |
| 2734 | 25 Véase sobre «derecho al olvido» sentencia Corte Suprema rol 25159-2018, de | Judicial | 144656 | 185 | 99,9 % | 781,9x |
| 2735 | 25. Corte Suprema, rol Nº 12.559-2011, de 9 de abril | Familia | 100107 | 57 | 99,9 % | 1756,3x |
| 2736 | 25. Un juez(a) no utilizará o prestará el prestigio de las funciones | Procesal | 94881 | 75 | 99,9 % | 1265,1x |
| 2737 | 250 Proclamación de Teherán (adoptada en la Conferencia Internacional de Derechos Humanos en Teherán 13 de | Judicial | 89476 | 55 | 99,9 % | 1626,8x |
| 2738 | 2506 CC). Además, el fundamento de esta restricción no procede de la introducción de un | Civil | 171433 | 204 | 99,9 % | 840,4x |
| 2739 | 251. Scheuner, Ulrich (1967): “Conflict of Treaty Provisions with a Peremptory | Penal | 121924 | 85 | 99,9 % | 1434,4x |
| 2740 | 252. Schindler, Dietrich (1979): “El Comité Internacional de la Cruz Roja y los | Penal | 121924 | 74 | 99,9 % | 1647,6x |
| 2741 | 253. Schindler, Dietrich (1999): “Importancia de los Convenios de Ginebra para el | Penal | 121924 | 80 | 99,9 % | 1524,0x |
| 2742 | 256      OMS (1996). Véase también OMS (2010). Para una discusión del concepto, véase Urzúa y Caqueo-Urízar | Constitucional | 112823 | 70 | 99,9 % | 1611,8x |
| 2743 | 257   Según algunos su ámbito de aplicación también alcanza la etapa precontractual laboral, como veremos al | Laboral | 113458 | 148 | 99,9 % | 766,6x |
| 2744 | 258. Tomando en cuenta lo anterior, y en aplicación del artículo | Administrativo | 89720 | 102 | 99,9 % | 879,6x |
| 2745 | 26   Así, reconociendo al MOP como empresa principal, sentencia 2º JLT Santiago, RIT O-1.065-2011; reconocien- | Laboral | 100583 | 84 | 99,9 % | 1197,4x |
| 2746 | 26 Artículo 66 inciso tercero: «[…] infringiere las resoluciones que determinen el | Judicial | 89450 | 101 | 99,9 % | 885,6x |
| 2747 | 26 Conforme con el artículo 387 del CPP si en un primer juicio oral se absolvió | Judicial | 144656 | 110 | 99,9 % | 1315,1x |
| 2748 | 26 En extenso sobre este tema, no solo referido a delitos sobre corrupción, véase | Penal | 178516 | 166 | 99,9 % | 1075,4x |
| 2749 | 26 Matus (2000: 454 y 455) afirma que definidos el grado o los grados de que se | Penal | 97633 | 130 | 99,9 % | 751,0x |
| 2750 | 26 N° 10 reconoce como función del Administrador el efectuar la denuncia ante el | Civil | 192585 | 204 | 99,9 % | 944,0x |
| 2751 | 26 Sentencia del Tribunal Oral en lo Penal de Quillota, RIT 83-2013, 26 de octubre | Penal | 178516 | 97 | 99,9 % | 1840,4x |
| 2752 | 26 Véase Mario Marcel, «Presentación del informe de política monetaria ante la | Laboral | 98828 | 106 | 99,9 % | 932,3x |
| 2753 | 26 Ídem, Chile ha logrado una amplia cobertura en el saneamiento básico de | Judicial | 81675 | 84 | 99,9 % | 972,3x |
| 2754 | 26. Boletín N° 12.854-18. Proyecto de ley que modifica la Ley | Judicial | 89476 | 55 | 99,9 % | 1626,8x |
| 2755 | 26. CORTE DE APELACIONES DE CONCEPCIÓN, rol | Familia | 65085 | 70 | 99,9 % | 929,8x |
| 2756 | 26. DÍAZ DE VALDÉS, José Manuel (2017): “Cuatro años de la ley Zamudio: aná- | Constitucional | 121906 | 71 | 99,9 % | 1717,0x |
| 2757 | 26. En su declaración de 2011 sobre las obligaciones de los | Constitucional | 112823 | 92 | 99,9 % | 1226,3x |
| 2758 | 26. Es incorrecto que un juez(a) utilice o trate de utilizar su situación | Procesal | 94881 | 120 | 99,9 % | 790,7x |
| 2759 | 26. La seguridad de que los preceptos legales que por mandato de la | Constitucional | 177323 | 98 | 99,9 % | 1809,4x |
| 2760 | 26. Poner en conocimiento de todos los copropietarios, la demanda interpuesta por uno | Civil | 192585 | 208 | 99,9 % | 925,9x |
| 2761 | 26. Señale casos de acciones protectoras de derechos fundamentales que hayan sido | Judicial | 105809 | 158 | 99,9 % | 669,7x |
| 2762 | 261. Sobre esta disposición, hemos de concluir algo similar a lo señalado | Judicial | 62514 | 61 | 99,9 % | 1024,8x |
| 2763 | 266 En un comienzo, ello era una forma de extraer la actividad comercial de la esfera de la autoridad soberana | Penal | 121924 | 126 | 99,9 % | 967,7x |
| 2764 | 269. Suárez Crothers, Christian (2016): “Caso Omar Humberto Maldonado Var- | Penal | 121924 | 81 | 99,9 % | 1505,2x |
| 2765 | 27 Aunque, como aclara Alvarado (2020: 519), estas posiciones encontradas están | Judicial | 144656 | 102 | 99,9 % | 1418,2x |
| 2766 | 27 Con referencia especial a la consideración de los delitos de infracción de deber | Penal | 178516 | 114 | 99,9 % | 1565,9x |
| 2767 | 27 Debe tenerse presente que en ese momento no existía legislación que tipificara | Penal | 178516 | 158 | 99,9 % | 1129,8x |
| 2768 | 27 El texto previo a la reforma aludía a las conductas antisindicales o desleales | Laboral | 74025 | 97 | 99,9 % | 763,1x |
| 2769 | 27 En términos semejantes, el artículo 15 de la Ley 20.830 regula el pacto de los | Familia | 123490 | 176 | 99,9 % | 701,6x |
| 2770 | 27 Juzgado de Garantía de Pitrufquen, rit 1201-2017 sentencia, de 11 de junio de | Judicial | 82507 | 49 | 99,9 % | 1683,8x |
| 2771 | 27 Una alusión sintética a las cinco principales posiciones sobre el significado de | Familia | 123490 | 75 | 99,9 % | 1646,5x |
| 2772 | 27 Véase el artículo 73 letra b) de la Convención de los Derechos del Niño y la regla | Penal | 86906 | 59 | 99,9 % | 1473,0x |
| 2773 | 27.   CORTE DE APELACIONES DE COPIAPÓ, rol N° | Familia | 65085 | 87 | 99,9 % | 748,1x |
| 2774 | 27.   CS, “Celcon S.A. con Instituto Nacional de Nor-     50. CA Coyhaique, rol 13-2006, de 15 de febrero de | Judicial | 105809 | 91 | 99,9 % | 1162,7x |
| 2775 | 27.   Decreto Nº 223/2006, aprueba reglamento de la Ley Nº 19.284, que regula | Constitucional | 121906 | 83 | 99,9 % | 1468,7x |
| 2776 | 27.   Ley N° 20.987. Modifica Ley N° 19.779. Establece | Judicial | 89476 | 109 | 99,9 % | 820,9x |
| 2777 | 27. Boletín N° 12.955-04. Proyecto de ley que establece bases | Judicial | 89476 | 79 | 99,9 % | 1132,6x |
| 2778 | 27. CUMBRE IBEROAMERICANA: Reglas de Brasilia sobre acceso a la justiciade las | Judicial | 81476 | 54 | 99,9 % | 1508,8x |
| 2779 | 27. Capacitación a funcionarios/as del Ministerio de Obras Públicas | Constitucional | 177323 | 139 | 99,9 % | 1275,7x |
| 2780 | 27. En materia de legitimación activa ¿hay diferencia entre el recurso de protección y el de | Judicial | 105809 | 110 | 99,9 % | 961,9x |
| 2781 | 27. Esas obligaciones extraterritoriales de los Estados en virtud | Constitucional | 112823 | 92 | 99,9 % | 1226,3x |
| 2782 | 271. Tapia Valdés, Jorge (2003): “Efectos de los tratados sobre derechos huma- | Penal | 121924 | 100 | 99,9 % | 1219,2x |
| 2783 | 272. Téllez Soto, Claudia (1998): “Valor jurídico de los tratados internacionales en | Penal | 121924 | 66 | 99,9 % | 1847,3x |
| 2784 | 274 ZAPPALÀ (2001), p. 601; WIRTH (2002), p. 888; NAQVI (2003), p. 623; AKANDE (2004), pp. 413-415; AMBOS | Penal | 121924 | 89 | 99,9 % | 1369,9x |
| 2785 | 274. Tomuschat, Christian (2005): “Informe de la Comisión sobre la jurisdicción | Penal | 121924 | 74 | 99,9 % | 1647,6x |
| 2786 | 275. En el presente caso, se alega discriminación por tres motivos: 1) la | Judicial | 92792 | 115 | 99,9 % | 806,9x |
| 2787 | 276. Uribe Vargas, Diego (1985): “Problemas de derechos humanos y seguridad | Penal | 121924 | 98 | 99,9 % | 1244,1x |
| 2788 | 278   Corte Suprema, 2 de mayo de 2017, Rol Nº 100796-2016. En el mismo sentido: Corte Suprema, 5 de marzo de | Civil | 142015 | 74 | 99,9 % | 1919,1x |
| 2789 | 278 La Corte estuvo por afirmar la existencia de una norma de derecho internacional consuetudinario que en- | Penal | 121924 | 140 | 99,9 % | 870,9x |
| 2790 | 28   GAMONAL C., Sergio (2008), El procedimiento de tutela de derechos laborales, 2ª edición revisada y actua- | Laboral | 113458 | 101 | 99,9 % | 1123,3x |
| 2791 | 28 Como se invocó por el recurrente en Corte Suprema, rol 4.949-2015, del 4 de | Penal | 97633 | 145 | 99,9 % | 673,3x |
| 2792 | 28 De acuerdo con SCHINDLER (1999), pp. 715-728, “en aquella época prevalecía la creencia de que la Liga de | Penal | 121924 | 150 | 99,9 % | 812,8x |
| 2793 | 28 El autor agrega: «más que decir que el proceso de implementación de políticas | Judicial | 150341 | 92 | 99,9 % | 1634,1x |
| 2794 | 28 Por ejemplo, Ferrer (2007: 29). En relación con lo contraepistémico en que se | Judicial | 150341 | 210 | 99,9 % | 715,9x |
| 2795 | 28 Sentencia de la Corte de Apelaciones de San Miguel, rol 404-2020, 7 de julio de | Familia | 97488 | 66 | 99,9 % | 1477,1x |
| 2796 | 28 Sobre el deber de fundamentar las sentencias, ver también sentencia Corte | Judicial | 144656 | 124 | 99,9 % | 1166,6x |
| 2797 | 28 Véase la Observación General número 20 (párrafo 70), las Directrices de Riad | Penal | 86906 | 79 | 99,9 % | 1100,1x |
| 2798 | 28. Boletín N° 13.018-13. Proyecto de ley que modifica el Código del | Judicial | 89476 | 101 | 99,9 % | 885,9x |
| 2799 | 28. CS, “Rojas Alarcón, Claudio con Ministerio Públi- | Judicial | 105809 | 92 | 99,9 % | 1150,1x |
| 2800 | 28. Explique la tesis histórica y la tesis literalista en materia de legitimación pasiva de la | Judicial | 105809 | 158 | 99,9 % | 669,7x |
| 2801 | 28. FERRADA, Ricardo (1996): “El juez y la interpreta- | Penal | 72395 | 106 | 99,9 % | 683,0x |
| 2802 | 28. Osborne, Raquel y Guasch, Oscar. 2003. “Avances | Judicial | 87237 | 83 | 99,9 % | 1051,0x |
| 2803 | 280 Véase ARELLANO ORTIZ, Pablo (2013a) “¿Quién protege al defensor frente a las intromisiones en su vida | Laboral | 113458 | 96 | 99,9 % | 1181,9x |
| 2804 | 282   EVANS DE LA CUADRA, Enrique (2004), Los derechos constitucionales, Tomo I, 3ª edición actualizada por | Laboral | 113458 | 115 | 99,9 % | 986,6x |
| 2805 | 282. Los jueces y órganos vinculados a la administración de | Judicial | 93914 | 107 | 99,9 % | 877,7x |
| 2806 | 282. Weisburd, Arthur (1995): “The Emptiness of the Concept of jus cogens. As | Penal | 121924 | 74 | 99,9 % | 1647,6x |
| 2807 | 284   CEA EGAÑA, José Luis (2004), Derecho constitucional chileno, Tomo II Derechos, Deberes y Garantías, San- | Laboral | 113458 | 124 | 99,9 % | 915,0x |
| 2808 | 285. La Corte constata que la discriminación contra Talía ha estado | Judicial | 92792 | 88 | 99,9 % | 1054,5x |
| 2809 | 286. Wouters, Jand y Verhoeven, Sten (2005): “The Prohibition of Genocide as a | Penal | 121924 | 81 | 99,9 % | 1505,2x |
| 2810 | 287   Se trata de un producto que beneficia a los clientes con una carga de $20.000 cada vez que adquieren | Laboral | 113458 | 104 | 99,9 % | 1090,9x |
| 2811 | 288. Zappalá, Salvatore (2001): “Do Heads of State in Office Enjoy Immunity | Penal | 121924 | 81 | 99,9 % | 1505,2x |
| 2812 | 29   Entre otros, ver ARÓSTICA, Iván (1989), pp. 455-464; REYES RIVEROS, Jorge (2002); CORDERO VEGA, Luis | Judicial | 105809 | 98 | 99,9 % | 1079,7x |
| 2813 | 29 Artículo 2: «Responsabilidad de las personas morales. Cada parte tomará las | Penal | 178516 | 146 | 99,9 % | 1222,7x |
| 2814 | 29 Confrontar con Bassiouni (1996: 63 y 65-66). Con respecto a los efectos que se | Constitucional | 177323 | 178 | 99,9 % | 996,2x |
| 2815 | 29 Considerando duodécimo: «En el campo de las cooperaciones mutuas, ha sido | Familia | 97488 | 115 | 99,9 % | 847,7x |
| 2816 | 29 Corte IDH, caso Furlan y familiares con Argentina, sentencia del 31 de agosto de | Laboral | 53374 | 62 | 99,9 % | 860,9x |
| 2817 | 29 El Digesto de la CIDH (disponible en https://bit.ly/3P6glDG) cita diversos casos | Judicial | 144656 | 201 | 99,9 % | 719,7x |
| 2818 | 29 En este sentido, Van Erp (2018), p. 1, da cuenta de cómo este fenómeno ha sido estudiado preferentemente | Penal | 119528 | 118 | 99,9 % | 1012,9x |
| 2819 | 29 Manuales de estructura y diseño de tribunales del país, aprobado en 2010 por la | Judicial | 89450 | 53 | 99,9 % | 1687,7x |
| 2820 | 29 Sentencia de la Corte de Apelaciones de Santiago, 18 de noviembre de 2020, rol | Judicial | 150341 | 115 | 99,9 % | 1307,3x |
| 2821 | 29 Véase el artículo 37 letra b) de la Convención de los Derechos del Niño y la regla | Penal | 86906 | 127 | 99,9 % | 684,3x |
| 2822 | 29 Ídem, indica que las personas que no pueden continuar pagando el alquiler de | Judicial | 81675 | 110 | 99,9 % | 742,5x |
| 2823 | 29.   Heim, Daniela. 2016. Mujeres y acceso a la jus-               SELA. Derecho y sexualidades. Seminario en | Judicial | 93914 | 88 | 99,9 % | 1067,2x |
| 2824 | 29. Boletín N° 13.080-34. Proyecto de ley que modifica el Código | Judicial | 89476 | 92 | 99,9 % | 972,6x |
| 2825 | 29. CADIET, Loïc et al (2012): Better administering for better judging, en | Procesal | 96699 | 91 | 99,9 % | 1062,6x |
| 2826 | 29. CS, “Felipe González con Municipalidad de Antu- | Judicial | 105809 | 78 | 99,9 % | 1356,5x |
| 2827 | 29. DE LA ROSA Paola y SANDOVAL, Víctor (2016): “Los sesgos cognitivos y | Judicial | 81476 | 98 | 99,9 % | 831,4x |
| 2828 | 29. En general un juez(a) no debe ofrecerse para prestar testimonios | Procesal | 94881 | 119 | 99,9 % | 797,3x |
| 2829 | 29. Inversiones Clarkson y Compañía Limitada con | Civil | 142015 | 89 | 99,9 % | 1595,7x |
| 2830 | 29. La obligación extraterritorial de respetar requiere que | Constitucional | 112823 | 102 | 99,9 % | 1106,1x |
| 2831 | 29. Prueba de la culpa: En materia de responsabilidad | Civil | 142015 | 130 | 99,9 % | 1092,4x |
| 2832 | 29. RÍOS, Víctor (2016): La prescripción extintiva | Familia | 65192 | 75 | 99,9 % | 869,2x |
| 2833 | 291. Zúñiga Urbina, Francisco (2008): “Derechos humanos en la jurisprudencia | Penal | 121924 | 70 | 99,9 % | 1741,8x |
| 2834 | 299. Al respecto, la corte observa que las violaciones declaradas | Judicial | 87237 | 124 | 99,9 % | 703,5x |
| 2835 | 3   Ya el texto del mensaje presidencial señala expresamente “en segundo lugar”, para designar a los procedi- | Judicial | 64632 | 84 | 99,9 % | 769,4x |
| 2836 | 3 Acto administrativo que crea un Área de Desarrollo Indígena | Judicial | 134465 | 102 | 99,9 % | 1318,3x |
| 2837 | 3 Artículo 64 del Código Penal: «Las circunstancias atenuantes o agravantes que | Penal | 178516 | 150 | 99,9 % | 1190,1x |
| 2838 | 3 Corte de Apelaciones de Concepción, rol 74.724-2022 del 29 de noviembre de | Judicial | 87950 | 67 | 99,9 % | 1312,7x |
| 2839 | 3 Dirección del Trabajo, Circular 63 del 29 de julio de 2020, que informa aspectos | Laboral | 98828 | 93 | 99,9 % | 1062,7x |
| 2840 | 3 El Servicio Civil cuenta con un banco de buenas prácticas laborales del sector | Laboral | 53293 | 66 | 99,9 % | 807,5x |
| 2841 | 3 El argumento basado en el uso de precedente suele tratarse en la literatura como | Judicial | 92792 | 88 | 99,9 % | 1054,5x |
| 2842 | 3 El artículo 453 alude a la etapa previa al juicio oral o audiencia preparatoria. Si se | Procesal | 86112 | 107 | 99,9 % | 804,8x |
| 2843 | 3 El artículo 5 número 4 de la Ley 19.947, dispone: «Los que se hallaren privados | Familia | 123490 | 109 | 99,9 % | 1132,9x |
| 2844 | 3 El derecho al recurso no debe entenderse en un sentido procesal, es decir, como | Judicial | 144656 | 123 | 99,9 % | 1176,1x |
| 2845 | 3 En esta afirmación entendemos que el concepto adulto mayor era el que en esos | Judicial | 82507 | 84 | 99,9 % | 982,2x |
| 2846 | 3 En sentencia Corte Suprema rol 26838-2015, de 12 de enero de 2016, se declara | Judicial | 144656 | 139 | 99,9 % | 1040,7x |
| 2847 | 3 Entre estos se encuentra el texto To err is human de 1999, sin embargo, estudios | Judicial | 87950 | 126 | 99,9 % | 698,0x |
| 2848 | 3 Existen razones históricas y legislativas que permiten calificar al contrato de | Laboral | 98828 | 81 | 99,9 % | 1220,1x |
| 2849 | 3 Juzgado de Letras del Trabajo de Osorno, RIT T-6-2010, 24 de septiembre de | Laboral | 53374 | 54 | 99,9 % | 988,4x |
| 2850 | 3 La dogmática civil suele referirse a «hechos jurídicos» y a las clasificaciones de | Judicial | 92792 | 117 | 99,9 % | 793,1x |
| 2851 | 3 Ley que introduce modificaciones en el Decreto Ley 3.346 del Ministerio de | Constitucional | 177323 | 130 | 99,9 % | 1364,0x |
| 2852 | 3 Ministra del Sernam, Adriana Delpiano Puelma, Cámara de Diputados, sesión | Laboral | 53374 | 59 | 99,9 % | 904,6x |
| 2853 | 3 OIT, «Las dificultades y oportunidades del teletrabajo para los trabajadores y | Laboral | 98828 | 114 | 99,9 % | 866,9x |
| 2854 | 3 Obviamente antecede incluso a las expresas reglas de evidencia sobre prueba | Procesal | 86112 | 115 | 99,9 % | 748,8x |
| 2855 | 3 Otro catálogo ha sido explicado por Vacarezza (2000) a partir de los principios | Judicial | 87950 | 91 | 99,9 % | 966,5x |
| 2856 | 3 Para más información, confrontar con Hernández (2011: 20). El destacado es | Judicial | 62514 | 41 | 99,9 % | 1524,7x |
| 2857 | 3 Para más información, véase la sentencia del 6.º Tribunal Oral en lo Penal de | Judicial | 62514 | 85 | 99,9 % | 735,5x |
| 2858 | 3 Se trata de Carlos Cruz Lorenzen, acusado por el delito de fraude al fisco, quien | Penal | 178516 | 117 | 99,9 % | 1525,8x |
| 2859 | 3 Sentencia Tribunal Constitucional 2.693, considerando decimoctavo, y en el | Judicial | 144656 | 79 | 99,9 % | 1831,1x |
| 2860 | 3 Sentencia del caso Fundación Educacional Colegios Asuncionistas con Inspección | Laboral | 74025 | 71 | 99,9 % | 1042,6x |
| 2861 | 3 Sentencia del caso Reyes con Carter, Corte Suprema, rol 6214-2018, 14 de agosto | Laboral | 74025 | 81 | 99,9 % | 913,9x |
| 2862 | 3 Sobre este particular, cobra especial relevancia la utilización de metaperitajes | Procesal | 86112 | 92 | 99,9 % | 936,0x |
| 2863 | 3 Tipologías recogidas en el Informe de la Defensoría de la Niñez, Informe de | Judicial | 78893 | 58 | 99,9 % | 1360,2x |
| 2864 | 3 Todo esto según la Corte Suprema en causa rol 21.632-2014 | Judicial | 87950 | 91 | 99,9 % | 966,5x |
| 2865 | 3 Una de las obras más importantes en relación con la willful blindness, es aquella | Penal | 97633 | 123 | 99,9 % | 793,8x |
| 2866 | 3 Véase también la Encuesta Nacional de Calidad de Vida (Encavi) del Ministerio | Laboral | 53293 | 71 | 99,9 % | 750,6x |
| 2867 | 3 Véase «Lenguaje inclusivo en cuanto al género», Organización de las Naciones | Judicial | 60665 | 57 | 99,9 % | 1064,3x |
| 2868 | 3.    ALESSANDRI, Arturo (1983): De la responsabili- | Civil | 142015 | 101 | 99,9 % | 1406,1x |
| 2869 | 3.    Carmona, Encarnación. 2015. La perspectiva de          13. Gauché Marchetti, Ximena. 2011. Sexualidad | Judicial | 87237 | 111 | 99,9 % | 785,9x |
| 2870 | 3.    Caso Vélez Loor vs. Panamá (2010): Corte Interamericana de Dere- | Constitucional | 115835 | 130 | 99,9 % | 891,0x |
| 2871 | 3.    Ley N° 20.609, establece medidas contra la discriminación, Diario Oficial, 24 | Judicial | 81476 | 46 | 99,9 % | 1771,2x |
| 2872 | 3.    Ley Nº 20.285 sobre transparencia y acceso a la | Judicial | 83934 | 81 | 99,9 % | 1036,2x |
| 2873 | 3.   ALESSANDRI BESA, Arturo (1955): Reformas                     treatybodyexternal/TBSearch.aspx?Lang=es&- | Familia | 65085 | 58 | 99,9 % | 1122,2x |
| 2874 | 3.   Consecuencia del incumplimiento del deber de               derecho a ser informada, en forma oportuna y | Civil | 142015 | 137 | 99,9 % | 1036,6x |
| 2875 | 3.   Consejeros técnicos: auxiliares de la administra-         procesal de parte agraviada con determinadas | Familia | 100107 | 143 | 99,9 % | 700,0x |
| 2876 | 3.   Ley Nº 16.768, otorga el beneficio de pago del 50% del arancel aduanero | Constitucional | 121906 | 83 | 99,9 % | 1468,7x |
| 2877 | 3.   Organización Mundial de la Salud (Oficina Regional para Europa). Declara- | Constitucional | 121906 | 71 | 99,9 % | 1717,0x |
| 2878 | 3. Accesibles y Utilizables: Asegurarse de que los datos sean legibles por | Administrativo | 89720 | 113 | 99,9 % | 794,0x |
| 2879 | 3. Actualizar los instrumentos de levantamiento de información de | Constitucional | 177323 | 143 | 99,9 % | 1240,0x |
| 2880 | 3. Adopten un comportamiento intimidatorio, provocativo o | Familia | 100107 | 128 | 99,9 % | 782,1x |
| 2881 | 3. Aplicación práctica de la Ley Nº 20.609                                                               95 | Judicial | 81476 | 59 | 99,9 % | 1380,9x |
| 2882 | 3. Arrubia, Eduardo y Brocca, Mariana. “La construcción del estigma | Judicial | 87237 | 91 | 99,9 % | 958,6x |
| 2883 | 3. Artículo 61 N° 5, según el cual el tribunal, en la audiencia pre- | Familia | 100107 | 78 | 99,9 % | 1283,4x |
| 2884 | 3. Cada uno de los Estados parte en el presente Pacto se compromete a | Constitucional | 177323 | 111 | 99,9 % | 1597,5x |
| 2885 | 3. Calificar los tratos crueles, inhumanos o degradantes considerando | Penal | 86906 | 67 | 99,9 % | 1297,1x |
| 2886 | 3. Caso Azul contra Perú | Judicial | 87237 | 68 | 99,9 % | 1282,9x |
| 2887 | 3. Como una norma de procedimiento que genera la obligación de | Judicial | 89476 | 98 | 99,9 % | 913,0x |
| 2888 | 3. Condena ejecutoriada por la comisión de alguno de los crímenes o simples delitos | Familia | 190697 | 176 | 99,9 % | 1083,5x |
| 2889 | 3. Cuando no hubo intención real de someter al responsable a la ac- | Judicial | 144656 | 172 | 99,9 % | 841,0x |
| 2890 | 3. Cumplimiento de sentencia caso Norin Catriman en materia de | Constitucional | 177323 | 115 | 99,9 % | 1541,9x |
| 2891 | 3. Deberán instituirse procedimientos adecuados en el marco del sistema jurídico nacional para solucionar | Judicial | 134465 | 171 | 99,9 % | 786,3x |
| 2892 | 3. Debilitamiento de la autoridad paterna: hoy, hablamos de “autoridad parental”, para | Familia | 190697 | 131 | 99,9 % | 1455,7x |
| 2893 | 3. Decisión: parte resolutiva del fallo | Judicial | 79146 | 105 | 99,9 % | 753,8x |
| 2894 | 3. Decretar medidas cautelares, de oficio o a petición de parte, sean | Familia | 100107 | 102 | 99,9 % | 981,4x |
| 2895 | 3. Decreto Ley N° 328 de 1925 y la Ley N° 5.521 de 19 de diciembre de 1934, que | Familia | 190697 | 189 | 99,9 % | 1009,0x |
| 2896 | 3. Dentro del título 5, los artículos 229 y 230 utilizan el término respecto del sujeto | Penal | 178516 | 107 | 99,9 % | 1668,4x |
| 2897 | 3. Desafíos y recomendaciones para los Estados | Constitucional | 115835 | 67 | 99,9 % | 1728,9x |
| 2898 | 3. Dimensiones del case management. El macro y | Procesal | 96699 | 92 | 99,9 % | 1051,1x |
| 2899 | 3. Documental | Judicial | 87237 | 50 | 99,9 % | 1744,7x |
| 2900 | 3. Ejecutarlo en     El fundamento sería el honor o la dignidad de estos pa- | Familia | 95131 | 104 | 99,9 % | 914,7x |
| 2901 | 3. El Estado debe realizar las publicaciones indicadas en el párrafo | Judicial | 87237 | 84 | 99,9 % | 1038,5x |
| 2902 | 3. El Estado es responsable por la violación del derecho a la vida | Judicial | 87237 | 119 | 99,9 % | 733,1x |
| 2903 | 3. El PIDCP se complementa con dos Protocolos Facultativos. El | Judicial | 87237 | 89 | 99,9 % | 980,2x |
| 2904 | 3. El case management en Francia | Procesal | 96699 | 110 | 99,9 % | 879,1x |
| 2905 | 3. El desarrollo de criterios jurisprudenciales de los | Constitucional | 115835 | 67 | 99,9 % | 1728,9x |
| 2906 | 3. El ejercicio del derecho previsto en el párrafo 2° de este artículo | Administrativo | 89720 | 55 | 99,9 % | 1631,3x |
| 2907 | 3. El establecimiento de un sistema de prevención de delitos, que | Penal | 178516 | 153 | 99,9 % | 1166,8x |
| 2908 | 3. El padre asume el pago del 50% de gastos de educación, en los siguientes ítems: útiles | Judicial | 79146 | 93 | 99,9 % | 851,0x |
| 2909 | 3. El periodo de duración del acuerdo de trabajo a distancia | Judicial | 96536 | 70 | 99,9 % | 1379,1x |
| 2910 | 3. El período de duración de este acuerdo, que puede ser indefinido | Laboral | 98828 | 145 | 99,9 % | 681,6x |
| 2911 | 3. El sistema de asistencia sanitaria deberá dar la preferencia a | Judicial | 134465 | 91 | 99,9 % | 1477,6x |
| 2912 | 3. El sistema de asistencia sanitaria deberá dar la preferencia a la | Judicial | 89476 | 87 | 99,9 % | 1028,5x |
| 2913 | 3. El tribunal podrá imponer una o más de las condiciones señaladas en | Penal | 194788 | 148 | 99,9 % | 1316,1x |
| 2914 | 3. En el caso que el proyecto de convenio colectivo se presente a dos | Laboral | 74025 | 107 | 99,9 % | 691,8x |
| 2915 | 3. En el trámite de obtención de Rut deben participar todos los miembros o integrantes | Civil | 192585 | 118 | 99,9 % | 1632,1x |
| 2916 | 3. En lo que atañe a los hechos controvertidos, detallar los medios | Familia | 100107 | 109 | 99,9 % | 918,4x |
| 2917 | 3. En tercer término, la correcta interpretación de la ley no puede desa- | Penal | 194788 | 200 | 99,9 % | 973,9x |
| 2918 | 3. En todos los casos anteriores pueden hacerse parte la DT y la | Laboral | 113458 | 91 | 99,9 % | 1246,8x |
| 2919 | 3. En un tercer significado, límite a la libertad contractual significa prohibición de concluir | Civil | 110175 | 92 | 99,9 % | 1197,6x |
| 2920 | 3. Escenario adverso ante integración de la sala | Judicial | 79146 | 93 | 99,9 % | 851,0x |
| 2921 | 3. Esforzarse por prevenir y atenuar los impactos negativos | Constitucional | 112823 | 81 | 99,9 % | 1392,9x |
| 2922 | 3. Establece la posibilidad de reclamar para el caso que no se cumpla | Administrativo | 89720 | 97 | 99,9 % | 924,9x |
| 2923 | 3. Establecimient de c ntrat s-tip bilaterales, ac rdad s p r grup s c n intereses | Civil | 110175 | 161 | 99,9 % | 684,3x |
| 2924 | 3. Estudio de jurisprudencia y evaluación de modificación normativa | Constitucional | 177323 | 131 | 99,9 % | 1353,6x |
| 2925 | 3. Evaluar, a requerimiento del juez, la pertinencia de derivar a | Judicial | 52128 | 74 | 99,9 % | 704,4x |
| 2926 | 3. Evitar la victimización secundaria: Desarrollar todas las acciones | Judicial | 53521 | 76 | 99,9 % | 704,2x |
| 2927 | 3. Falta de incorporación del Modelo de Prevención a los contratos | Constitucional | 112823 | 75 | 99,9 % | 1504,3x |
| 2928 | 3. Fama | Familia | 65085 | 59 | 99,9 % | 1103,1x |
| 2929 | 3. Fortalecimiento y reconocimiento de la | Judicial | 82507 | 66 | 99,9 % | 1250,1x |
| 2930 | 3. Función de prueba: Función relacionada con el principio de segu- | Judicial | 89450 | 78 | 99,9 % | 1146,8x |
| 2931 | 3. Garantizar en todo tipo de juicios el derecho de las personas con | Constitucional | 177323 | 100 | 99,9 % | 1773,2x |
| 2932 | 3. Incorporar el Protocolo de Estambul en los procedimientos de | Constitucional | 177323 | 136 | 99,9 % | 1303,8x |
| 2933 | 3. Informar al secretario respecto a la administración de personal y | Judicial | 52128 | 72 | 99,9 % | 724,0x |
| 2934 | 3. Informe de atención psicológica, emitido por HHHH, que da | Judicial | 93914 | 66 | 99,9 % | 1422,9x |
| 2935 | 3. La condición negativa y suspensiva, cuando es físicamente imposible, se tiene por | Civil | 118177 | 119 | 99,9 % | 993,1x |
| 2936 | 3. La creación de la Secretaría Técnica de igualdad de género y no | Judicial | 81476 | 93 | 99,9 % | 876,1x |
| 2937 | 3. La decisión les será comunicada en un idioma que puedan entender. Les será comunicada por escrito si lo | Constitucional | 115835 | 143 | 99,9 % | 810,0x |
| 2938 | 3. La discriminación en el derecho a la vida privada (segunda | Judicial | 87237 | 124 | 99,9 % | 703,5x |
| 2939 | 3. La discriminación en la actividad militar | Judicial | 87237 | 98 | 99,9 % | 890,2x |
| 2940 | 3. La existencia previa de un debido proceso, para que como | Procesal | 94881 | 72 | 99,9 % | 1317,8x |
| 2941 | 3. La frase que se incorporó por la Ley N° 10.271 “…y celebrar entre ellos cualesquier | Familia | 136567 | 165 | 99,9 % | 827,7x |
| 2942 | 3. La legislación protectora relacionada con las cuestiones compren- | Judicial | 89476 | 117 | 99,9 % | 764,8x |
| 2943 | 3. La migración irregular, el ingreso clandestino y otras | Constitucional | 115835 | 140 | 99,9 % | 827,4x |
| 2944 | 3. La persona detenida de conformidad con el párrafo 1 del presente | Judicial | 78893 | 104 | 99,9 % | 758,6x |
| 2945 | 3. La posibilidad de reclamar para el caso que no se cumpla con la | Administrativo | 89720 | 61 | 99,9 % | 1470,8x |
| 2946 | 3. La utilización de sistemas similares a los referidos en los | Judicial | 96536 | 118 | 99,9 % | 818,1x |
| 2947 | 3. La utilización de sistemas similares a los referidos en los apartados anteriores para la grabación de soni- | Constitucional | 104063 | 146 | 99,9 % | 712,8x |
| 2948 | 3. La utilización del término «pueblos» en este Convenio no deberá | Judicial | 60665 | 80 | 99,9 % | 758,3x |
| 2949 | 3. Las causas relativas al ejercicio, suspensión o pérdida de la patria potestad; a la | Familia | 190697 | 123 | 99,9 % | 1550,4x |
| 2950 | 3. Las personas con discapacidad mental o psicosocial en algunas | Constitucional | 177323 | 98 | 99,9 % | 1809,4x |
| 2951 | 3. Ley de transparencia y acceso a la información: se dispuso | Administrativo | 89720 | 97 | 99,9 % | 924,9x |
| 2952 | 3. Lo dispuesto en este artículo no impide la imposición de | Laboral | 100583 | 80 | 99,9 % | 1257,3x |
| 2953 | 3. Los Estados Partes adoptarán todas las medidas apropiadas para | Penal | 72395 | 87 | 99,9 % | 832,1x |
| 2954 | 3. Los avisos deben contener los mismos requisitos y menciones que | Judicial | 89450 | 111 | 99,9 % | 805,9x |
| 2955 | 3. Los datos serán suprimidos en el plazo máximo de un mes desde su captación, salvo cuando hubieran de | Constitucional | 104063 | 143 | 99,9 % | 727,7x |
| 2956 | 3. Los distintos tipos de audiencia que, de acuerdo a la materia que | Judicial | 52128 | 78 | 99,9 % | 668,3x |
| 2957 | 3. Los gobiernos deberán velar por que, siempre que haya lugar, se | Judicial | 89476 | 111 | 99,9 % | 806,1x |
| 2958 | 3. Los permisos de residencia | Constitucional | 115835 | 107 | 99,9 % | 1082,6x |
| 2959 | 3. Mediante Decreto Ley Nº 3 de 1973 se declaró en estado de sitio | Penal | 121924 | 104 | 99,9 % | 1172,3x |
| 2960 | 3. Muñoz León, Fernando. “La Ley Zamudio en acción: sentencias | Judicial | 87237 | 88 | 99,9 % | 991,3x |
| 2961 | 3. Nada de lo dispuesto en el presente artículo afectará a la tipifi- | Penal | 121924 | 71 | 99,9 % | 1717,2x |
| 2962 | 3. Nada de lo dispuesto en este artículo autorizará a los Estados | Laboral | 100583 | 113 | 99,9 % | 890,1x |
| 2963 | 3. No parece posible aplicar a los contratos forzosos fictos o heterodoxos el distingo que | Civil | 110175 | 106 | 99,9 % | 1039,4x |
| 2964 | 3. No se favorecerá al condenado por las leyes que concedan amnis- | Penal | 194788 | 148 | 99,9 % | 1316,1x |
| 2965 | 3. No violencia de género: este eje tiene como objetivo erradicar | Judicial | 81476 | 106 | 99,9 % | 768,6x |
| 2966 | 3. Oficina de Protección de Derechos de Niños, Niñas y Adoles- | Judicial | 89476 | 49 | 99,9 % | 1826,0x |
| 2967 | 3. Otros antecedentes de que disponga la ley o el juez para la debida | Judicial | 89450 | 91 | 99,9 % | 983,0x |
| 2968 | 3. Personas migrantes y sujetas a protección | Judicial | 82507 | 80 | 99,9 % | 1031,3x |
| 2969 | 3. Podrá utilizarse un mecanismo de certificación aprobado con arreglo al artículo 42 como elemento que | Constitucional | 104063 | 136 | 99,9 % | 765,2x |
| 2970 | 3. Por último, se reconocerá como circunstancia atenuante la de | Penal | 119528 | 97 | 99,9 % | 1232,2x |
| 2971 | 3. Problema de la doble evaluación: Previo-De ingreso, que | Familia | 100107 | 68 | 99,9 % | 1472,2x |
| 2972 | 3. Procedimiento relativo a los actos de violencia intrafamiliar. Este | Familia | 97488 | 91 | 99,9 % | 1071,3x |
| 2973 | 3. Procesamiento de voz, donde la máquina es capaz de procesar | Judicial | 83934 | 88 | 99,9 % | 953,8x |
| 2974 | 3. Proporcionalidad en sentido estricto. Es decir, que en un juicio | Judicial | 144656 | 162 | 99,9 % | 892,9x |
| 2975 | 3. Que al informar la recurrida, argumenta no haber incurrido en actos ilegales o | Civil | 192585 | 178 | 99,9 % | 1081,9x |
| 2976 | 3. Que cause privación, perturbación o amenaza en el ejercicio | Judicial | 81476 | 78 | 99,9 % | 1044,6x |
| 2977 | 3. Que el imputado no tuviere vigente una suspensión condicional | Penal | 194788 | 209 | 99,9 % | 932,0x |
| 2978 | 3. Que el intento de mantenerse cerca de sus hijos e hijas, no se | Familia | 95131 | 81 | 99,9 % | 1174,5x |
| 2979 | 3. Que no se ha afectado el contenido esencial del derecho | Laboral | 113458 | 70 | 99,9 % | 1620,8x |
| 2980 | 3. Que, a diferencia de lo señalado por la Comisión, considerando los | Penal | 194788 | 101 | 99,9 % | 1928,6x |
| 2981 | 3. Que, considerando los argumentos esgrimidos en el fundamento | Judicial | 144656 | 114 | 99,9 % | 1268,9x |
| 2982 | 3. Que, en este estado de cosas, aparece que mantener la medida de | Judicial | 144656 | 176 | 99,9 % | 821,9x |
| 2983 | 3. Que, sin perjuicio de lo anterior, conviene aclarar que aun cuando | Penal | 194788 | 136 | 99,9 % | 1432,3x |
| 2984 | 3. Reclamo de Ilegalidad ante la Corte de Apelaciones: en contra | Administrativo | 89720 | 107 | 99,9 % | 838,5x |
| 2985 | 3. Reconociera públicamente su responsabilidad internacional y | Judicial | 87237 | 87 | 99,9 % | 1002,7x |
| 2986 | 3. Reparación en salud: Atención a personas reconocidas en Comi- | Constitucional | 177323 | 100 | 99,9 % | 1773,2x |
| 2987 | 3. Resolución que fija fecha de juicio | Penal | 57066 | 70 | 99,9 % | 815,2x |
| 2988 | 3. Respecto de niños, niñas o adolescentes menores de 18 años de | Judicial | 82507 | 118 | 99,9 % | 699,2x |
| 2989 | 3. Se puede hacer valer en di | Procesal | 95124 | 136 | 99,9 % | 699,4x |
| 2990 | 3. Servicios | Penal | 57066 | 80 | 99,9 % | 713,3x |
| 2991 | 3. Si es una sentencia condenatoria debe señalar la pena concreta que | Penal | 194788 | 166 | 99,9 % | 1173,4x |
| 2992 | 3. Si la aceptación de un Estado que no sea Parte en el presente Estatuto fuere necesaria de conformidad | Penal | 121924 | 139 | 99,9 % | 877,2x |
| 2993 | 3. Si lo anterior es cierto, implica que no hay diferencias cualitativas y | Judicial | 92792 | 98 | 99,9 % | 946,9x |
| 2994 | 3. Si se cometiere por el posadero, fondista u otra persona que hospede | Penal | 194788 | 137 | 99,9 % | 1421,8x |
| 2995 | 3. Si se trata de contratos unilaterales que originan obligaciones de dar, no existe | Civil | 120848 | 124 | 99,9 % | 974,6x |
| 2996 | 3. Si un precepto laboral vulnera los derechos fundamentales, el | Laboral | 113458 | 97 | 99,9 % | 1169,7x |
| 2997 | 3. Si, tratándose del delito establecido en el inciso cuarto del artículo | Penal | 194788 | 140 | 99,9 % | 1391,3x |
| 2998 | 3. Siempre que sea posible, estos pueblos deberán | Judicial | 134465 | 72 | 99,9 % | 1867,6x |
| 2999 | 3. Siempre que sea posible, estos pueblos deberán tener el derecho de | Judicial | 134465 | 72 | 99,9 % | 1867,6x |
| 3000 | 3. Sistemas mixtos (Alemania, Italia, Países Bajos) | Judicial | 105809 | 127 | 99,9 % | 833,1x |
| 3001 | 3. Tercero, desde los 3 a 5 años. Es la “etapa fálica”, pues todo gira | Judicial | 87237 | 111 | 99,9 % | 785,9x |
| 3002 | 3. Todo juez(a) debe aceptar restricciones personales que los | Procesal | 94881 | 88 | 99,9 % | 1078,2x |
| 3003 | 3. Todos los informes acompañados como prueba dan cuenta de | Judicial | 93914 | 58 | 99,9 % | 1619,2x |
| 3004 | 3. Tutela resarcitoria: el juez indicará en forma concreta las medidas | Laboral | 113458 | 94 | 99,9 % | 1207,0x |
| 3005 | 3. Un tercer significado de la libertad contractual, implícito en el anterior, es el de la | Civil | 110175 | 104 | 99,9 % | 1059,4x |
| 3006 | 3. Una vez concluidos los procedimientos y después de | Constitucional | 112823 | 93 | 99,9 % | 1213,2x |
| 3007 | 3. Unidad Juzgados de Cobranza Laboral y Previsional y Juzgados | Judicial | 89450 | 96 | 99,9 % | 931,8x |
| 3008 | 3. Voluntario. El consentimiento jamás se otorga bajo presión. No | Judicial | 89476 | 93 | 99,9 % | 962,1x |
| 3009 | 3.1               Marco | Procesal | 94881 | 57 | 99,9 % | 1664,6x |
| 3010 | 3.1              La reforma constitucional | Constitucional | 104063 | 100 | 99,9 % | 1040,6x |
| 3011 | 3.1            Reformas legales y | Laboral | 113458 | 85 | 99,9 % | 1334,8x |
| 3012 | 3.1           Procedimiento de Reorganización | Judicial | 64632 | 81 | 99,9 % | 797,9x |
| 3013 | 3.1         Introducción | Judicial | 134465 | 93 | 99,9 % | 1445,9x |
| 3014 | 3.1     Conciliación | Familia | 100107 | 104 | 99,9 % | 962,6x |
| 3015 | 3.1     El fundamento del derecho de | Familia | 65192 | 55 | 99,9 % | 1185,3x |
| 3016 | 3.1     Respecto de | Judicial | 105809 | 58 | 99,9 % | 1824,3x |
| 3017 | 3.1     Síntesis de la evolución legislativa | Familia | 95131 | 50 | 99,9 % | 1902,6x |
| 3018 | 3.1. Aplicación de la Convención Americana sobre Derechos Humanos | Constitucional | 115835 | 109 | 99,9 % | 1062,7x |
| 3019 | 3.1. Las contraídas por el marido durante la vigencia de la sociedad conyugal, en virtud | Familia | 136567 | 128 | 99,9 % | 1066,9x |
| 3020 | 3.1. Testamento otorgado en país extranjero en conformidad a la ley | Civil | 50203 | 70 | 99,9 % | 717,2x |
| 3021 | 3.1.1 Bases del ejercicio de la Transparencia | Administrativo | 89720 | 102 | 99,9 % | 879,6x |
| 3022 | 3.1.1 Concepto | Judicial | 79146 | 92 | 99,9 % | 860,3x |
| 3023 | 3.1.1 Derecho al juez independiente | Penal | 211066 | 117 | 99,9 % | 1804,0x |
| 3024 | 3.1.1 Expresar libre y autónomamente | Judicial | 89476 | 110 | 99,9 % | 813,4x |
| 3025 | 3.1.1 La RPPJ como un supuesto de | Penal | 119528 | 94 | 99,9 % | 1271,6x |
| 3026 | 3.1.1 La crisis como motor de cambio | Judicial | 83934 | 113 | 99,9 % | 742,8x |
| 3027 | 3.1.1 La ejecución de la prestación | Civil | 142015 | 94 | 99,9 % | 1510,8x |
| 3028 | 3.1.1 Necesidad de una mirada interdisciplinaria | Judicial | 81476 | 87 | 99,9 % | 936,5x |
| 3029 | 3.1.1 Procedimiento ordinario de mayor cuantía | Judicial | 52128 | 76 | 99,9 % | 685,9x |
| 3030 | 3.1.1 Teorías que explican las relaciones entre el | Penal | 121924 | 97 | 99,9 % | 1256,9x |
| 3031 | 3.1.1. Artículo 22 sobre derecho de circulación y de residencia (legalidad y motivación de la medi- | Constitucional | 115835 | 107 | 99,9 % | 1082,6x |
| 3032 | 3.1.1.1 Teoría dualista o pluralista326 | Penal | 121924 | 96 | 99,9 % | 1270,0x |
| 3033 | 3.1.1.1 Trámites del procedimiento o | Judicial | 52128 | 67 | 99,9 % | 778,0x |
| 3034 | 3.1.1.2 Teoría monista | Penal | 121924 | 107 | 99,9 % | 1139,5x |
| 3035 | 3.1.1.3 Teoría de la coordinación | Penal | 121924 | 102 | 99,9 % | 1195,3x |
| 3036 | 3.1.11 Tomar decisiones relativas a la | Judicial | 89476 | 102 | 99,9 % | 877,2x |
| 3037 | 3.1.12 Elección libre del tipo de familia | Judicial | 89476 | 124 | 99,9 % | 721,6x |
| 3038 | 3.1.2 Consideraciones sobre acceso a la justicia | Constitucional | 112823 | 76 | 99,9 % | 1484,5x |
| 3039 | 3.1.2 Derecho al juez imparcial | Penal | 211066 | 128 | 99,9 % | 1649,0x |
| 3040 | 3.1.2 Portal de Transparencia del Poder Judicial | Administrativo | 89720 | 109 | 99,9 % | 823,1x |
| 3041 | 3.1.2 Unidad de Sala | Laboral | 71986 | 80 | 99,9 % | 899,8x |
| 3042 | 3.1.2. Reconocimiento de la identidad de género | Judicial | 89476 | 114 | 99,9 % | 784,9x |
| 3043 | 3.1.2.1 Incorporación automática de las normas | Penal | 121924 | 85 | 99,9 % | 1434,4x |
| 3044 | 3.1.2.1 La conducta | Judicial | 81476 | 52 | 99,9 % | 1566,8x |
| 3045 | 3.1.2.1 Tipos de remedios | Constitucional | 112823 | 74 | 99,9 % | 1524,6x |
| 3046 | 3.1.2.2 Barreras de acceso a la justicia | Constitucional | 112823 | 93 | 99,9 % | 1213,2x |
| 3047 | 3.1.2.2 Incorporación automática de las normas | Penal | 121924 | 100 | 99,9 % | 1219,2x |
| 3048 | 3.1.2.2 Los estereotipos | Judicial | 81476 | 84 | 99,9 % | 970,0x |
| 3049 | 3.1.2.5 Algunas consecuencias de la discriminación | Judicial | 81476 | 59 | 99,9 % | 1380,9x |
| 3050 | 3.1.3 Algunos procesos psicológicos que | Judicial | 81476 | 54 | 99,9 % | 1508,8x |
| 3051 | 3.1.3 Autonomía para adoptar | Judicial | 89476 | 92 | 99,9 % | 972,6x |
| 3052 | 3.1.3 Características | Judicial | 79146 | 81 | 99,9 % | 977,1x |
| 3053 | 3.1.3 Comisión de Transparencia del Poder Judicial | Administrativo | 89720 | 109 | 99,9 % | 823,1x |
| 3054 | 3.1.3 Eventuales problemas relativos | Penal | 119528 | 131 | 99,9 % | 912,4x |
| 3055 | 3.1.3 Unidad de Cumplimiento | Laboral | 71986 | 105 | 99,9 % | 685,6x |
| 3056 | 3.1.3. Impugnación de la paternidad tratándose de los hijos nacidos antes del | Familia | 62470 | 87 | 99,9 % | 718,0x |
| 3057 | 3.1.3.1 La integralidad de la persona que | Judicial | 81476 | 80 | 99,9 % | 1018,5x |
| 3058 | 3.1.3.2 A quién se puede reconocer | Familia | 65085 | 91 | 99,9 % | 715,2x |
| 3059 | 3.1.3.2 Sesgos cognitivos | Judicial | 81476 | 94 | 99,9 % | 866,8x |
| 3060 | 3.1.3.5 Quién puede repudiar | Familia | 65085 | 78 | 99,9 % | 834,4x |
| 3061 | 3.1.4 Cargos y funciones principales en la | Laboral | 71986 | 57 | 99,9 % | 1262,9x |
| 3062 | 3.1.4 El incumplimiento del médico debido | Civil | 142015 | 114 | 99,9 % | 1245,7x |
| 3063 | 3.1.4 Procedimientos | Judicial | 79146 | 83 | 99,9 % | 953,6x |
| 3064 | 3.1.5 Aplicación en el derecho | Judicial | 79146 | 85 | 99,9 % | 931,1x |
| 3065 | 3.1.5 Elección de las y los compañeros sexuales | Judicial | 89476 | 120 | 99,9 % | 745,6x |
| 3066 | 3.1.5 La responsabilidad del médico | Civil | 142015 | 130 | 99,9 % | 1092,4x |
| 3067 | 3.1.6 Decisión libre y responsable sobre el | Judicial | 89476 | 133 | 99,9 % | 672,8x |
| 3068 | 3.1.6 El médico responde por el hecho de los | Civil | 142015 | 126 | 99,9 % | 1127,1x |
| 3069 | 3.1.7 Decisión libre y responsable sobre el número | Judicial | 89476 | 96 | 99,9 % | 932,0x |
| 3070 | 3.1.8 Tener relaciones sexuales consensuadas | Judicial | 89476 | 98 | 99,9 % | 913,0x |
| 3071 | 3.1.9 Pleno respeto por la integridad física | Judicial | 89476 | 75 | 99,9 % | 1193,0x |
| 3072 | 3.10             Método subsidiario: la demanda | Familia | 65192 | 65 | 99,9 % | 1003,0x |
| 3073 | 3.11.1 Suspensión de licencia de conducir | Familia | 65192 | 78 | 99,9 % | 835,8x |
| 3074 | 3.14     Protección de la buena fe procesal en | Familia | 65192 | 65 | 99,9 % | 1003,0x |
| 3075 | 3.14.1 Multa por incidentes dilatorios | Familia | 65192 | 87 | 99,9 % | 749,3x |
| 3076 | 3.14.5 Mala fe del deudor | Familia | 65192 | 84 | 99,9 % | 776,1x |
| 3077 | 3.16 Preguntas orientadoras                                                                    153 | Familia | 65192 | 49 | 99,9 % | 1330,4x |
| 3078 | 3.2               Estructura orgánica dentro | Penal | 57066 | 65 | 99,9 % | 877,9x |
| 3079 | 3.2         Composición y organización | Judicial | 54457 | 72 | 99,9 % | 756,3x |
| 3080 | 3.2      El Sistema Interamericano de Derechos Humanos | Judicial | 87237 | 75 | 99,9 % | 1163,2x |
| 3081 | 3.2     La Ley Nº 19.628 de 1999 | Constitucional | 104063 | 92 | 99,9 % | 1131,1x |
| 3082 | 3.2     La protección constitucional a la identidad | Judicial | 93914 | 102 | 99,9 % | 920,7x |
| 3083 | 3.2     Plan | Familia | 65192 | 48 | 99,9 % | 1358,2x |
| 3084 | 3.2    Tramitación del procedimiento | Judicial | 64632 | 55 | 99,9 % | 1175,1x |
| 3085 | 3.2 Fase sustantiva El objetivo de esta fase es obtener un relato | Penal | 72395 | 84 | 99,9 % | 861,8x |
| 3086 | 3.2. Mayor protección a la propiedad y | Civil | 90056 | 83 | 99,9 % | 1085,0x |
| 3087 | 3.2. Principales recomendaciones realizadas por las relatorías especiales sobre | Constitucional | 115835 | 97 | 99,9 % | 1194,2x |
| 3088 | 3.2.1 Aspectos procesales relevantes | Judicial | 81476 | 71 | 99,9 % | 1147,5x |
| 3089 | 3.2.1 Concepto | Judicial | 79146 | 102 | 99,9 % | 775,9x |
| 3090 | 3.2.1 Contextualización preliminar | Constitucional | 112823 | 104 | 99,9 % | 1084,8x |
| 3091 | 3.2.1 Derecho a la vida y a la integridad física y psíquica | Laboral | 113458 | 143 | 99,9 % | 793,4x |
| 3092 | 3.2.1 Derecho al juicio previo | Penal | 211066 | 119 | 99,9 % | 1773,7x |
| 3093 | 3.2.1 El concepto de violencia intrafamiliar | Familia | 95131 | 96 | 99,9 % | 990,9x |
| 3094 | 3.2.1 Identificación de problemas relativos | Penal | 119528 | 126 | 99,9 % | 948,6x |
| 3095 | 3.2.1 Ingreso | Laboral | 71986 | 79 | 99,9 % | 911,2x |
| 3096 | 3.2.1 Las tierras y el derecho | Judicial | 134465 | 91 | 99,9 % | 1477,6x |
| 3097 | 3.2.1 Periodo de Calificación | Procesal | 94881 | 98 | 99,9 % | 968,2x |
| 3098 | 3.2.1 Principios rectores | Familia | 100107 | 57 | 99,9 % | 1756,3x |
| 3099 | 3.2.1 Transformación digital | Judicial | 83934 | 72 | 99,9 % | 1165,8x |
| 3100 | 3.2.1 Transparencia y “Justicia Abierta” | Administrativo | 89720 | 102 | 99,9 % | 879,6x |
| 3101 | 3.2.1.1 Conducta | Familia | 95131 | 118 | 99,9 % | 806,2x |
| 3102 | 3.2.1.1 Puede comenzar por una demanda o una | Judicial | 52128 | 78 | 99,9 % | 668,3x |
| 3103 | 3.2.1.2 Vínculo | Familia | 95131 | 97 | 99,9 % | 980,7x |
| 3104 | 3.2.1.3 Contenido de la demanda | Judicial | 81476 | 94 | 99,9 % | 866,8x |
| 3105 | 3.2.1.3 Daño | Familia | 95131 | 124 | 99,9 % | 767,2x |
| 3106 | 3.2.1.4 Concluida la audiencia de contestación y | Judicial | 52128 | 70 | 99,9 % | 744,7x |
| 3107 | 3.2.1.7 La sentencia debe dictarse en el término | Judicial | 52128 | 74 | 99,9 % | 704,4x |
| 3108 | 3.2.2 Análisis de criterios emanados de | Penal | 119528 | 118 | 99,9 % | 1012,9x |
| 3109 | 3.2.2 Comisión calificadora | Procesal | 94881 | 91 | 99,9 % | 1042,6x |
| 3110 | 3.2.2 Derecho a no sufrir discriminaciones o tratos | Judicial | 89476 | 72 | 99,9 % | 1242,7x |
| 3111 | 3.2.2 Derecho a ser juzgado dentro de un plazo razonable | Penal | 211066 | 122 | 99,9 % | 1730,0x |
| 3112 | 3.2.2 Estructura del procedimiento | Judicial | 81476 | 84 | 99,9 % | 970,0x |
| 3113 | 3.2.2 Gobierno electrónico en Chile | Judicial | 83934 | 80 | 99,9 % | 1049,2x |
| 3114 | 3.2.2 Justicia Abierta | Administrativo | 89720 | 85 | 99,9 % | 1055,5x |
| 3115 | 3.2.2 Nominación del Veedor | Judicial | 64632 | 93 | 99,9 % | 695,0x |
| 3116 | 3.2.2 Privacidad y honra | Laboral | 113458 | 97 | 99,9 % | 1169,7x |
| 3117 | 3.2.2.1 Discriminación en la familia | Judicial | 89476 | 83 | 99,9 % | 1078,0x |
| 3118 | 3.2.2.1 El ius puniendi estatal | Constitucional | 112823 | 75 | 99,9 % | 1504,3x |
| 3119 | 3.2.2.2 Discriminación en el trabajo | Judicial | 89476 | 105 | 99,9 % | 852,2x |
| 3120 | 3.2.2.2 Justicia civil | Constitucional | 112823 | 72 | 99,9 % | 1567,0x |
| 3121 | 3.2.2.2 La igualdad comunitarista | Constitucional | 121906 | 94 | 99,9 % | 1296,9x |
| 3122 | 3.2.2.3 Discriminación en los estudios | Judicial | 89476 | 83 | 99,9 % | 1078,0x |
| 3123 | 3.2.2.3 El concepto de grupos desventajados o vulnerables | Constitucional | 121906 | 101 | 99,9 % | 1207,0x |
| 3124 | 3.2.2.4 Lotes y grupos | Constitucional | 121906 | 101 | 99,9 % | 1207,0x |
| 3125 | 3.2.2.4 Recepción, carga y valoración de la prueba | Judicial | 81476 | 114 | 99,9 % | 714,7x |
| 3126 | 3.2.2.5 Medidas cautelares | Judicial | 81476 | 85 | 99,9 % | 958,5x |
| 3127 | 3.2.2.6 Interseccionalidad | Constitucional | 121906 | 96 | 99,9 % | 1269,9x |
| 3128 | 3.2.2.6 Sentencia | Judicial | 81476 | 50 | 99,9 % | 1629,5x |
| 3129 | 3.2.2.7 Desigualdad estructural | Constitucional | 121906 | 97 | 99,9 % | 1256,8x |
| 3130 | 3.2.2.7 Recurso de apelación | Judicial | 81476 | 76 | 99,9 % | 1072,1x |
| 3131 | 3.2.2.8 Acción afirmativa y discriminación indirecta | Constitucional | 121906 | 104 | 99,9 % | 1172,2x |
| 3132 | 3.2.3 Derechos de los pueblos indígenas sobre las | Judicial | 134465 | 113 | 99,9 % | 1190,0x |
| 3133 | 3.2.3 Funciones del secretario de la comisión | Procesal | 94881 | 48 | 99,9 % | 1976,7x |
| 3134 | 3.2.3 No discriminación | Laboral | 113458 | 94 | 99,9 % | 1207,0x |
| 3135 | 3.2.3 Procedimiento de derivación | Familia | 100107 | 88 | 99,9 % | 1137,6x |
| 3136 | 3.2.3 Proceso de innovación | Judicial | 83934 | 84 | 99,9 % | 999,2x |
| 3137 | 3.2.3 Solicitudes y presentaciones | Laboral | 71986 | 62 | 99,9 % | 1161,1x |
| 3138 | 3.2.3.2 Valor vinculado al proceso de innovación | Judicial | 83934 | 94 | 99,9 % | 892,9x |
| 3139 | 3.2.4 Control y resolución de escritos | Laboral | 71986 | 68 | 99,9 % | 1058,6x |
| 3140 | 3.2.4 Desarrollo de la mediación | Familia | 100107 | 84 | 99,9 % | 1191,8x |
| 3141 | 3.2.4 Inviolabilidad de toda forma | Laboral | 113458 | 88 | 99,9 % | 1289,3x |
| 3142 | 3.2.5 Fundamentos de la claridad y el | Judicial | 79146 | 98 | 99,9 % | 807,6x |
| 3143 | 3.2.5 Libertad ideológica y religiosa | Laboral | 113458 | 117 | 99,9 % | 969,7x |
| 3144 | 3.2.5.1 Efectos judiciales | Judicial | 64632 | 61 | 99,9 % | 1059,5x |
| 3145 | 3.2.5.3 Efectos administrativos | Judicial | 64632 | 68 | 99,9 % | 950,5x |
| 3146 | 3.2.5.4 Plazos | Judicial | 64632 | 91 | 99,9 % | 710,2x |
| 3147 | 3.2.6 Actas de mediación | Familia | 100107 | 104 | 99,9 % | 962,6x |
| 3148 | 3.2.6 Función general de la narrativa jurídica | Judicial | 79146 | 96 | 99,9 % | 824,4x |
| 3149 | 3.2.6 La libertad de emitir opinión y de | Laboral | 113458 | 110 | 99,9 % | 1031,4x |
| 3150 | 3.2.6.3 Valoración y fiscalización de activos | Judicial | 64632 | 76 | 99,9 % | 850,4x |
| 3151 | 3.2.7 Libertad de trabajo | Laboral | 113458 | 98 | 99,9 % | 1157,7x |
| 3152 | 3.2.7.1 Verificación e impugnación de créditos | Judicial | 64632 | 50 | 99,9 % | 1292,6x |
| 3153 | 3.2.7.2 Presentación de la propuesta | Judicial | 64632 | 80 | 99,9 % | 807,9x |
| 3154 | 3.2.8 Libertad sindical | Laboral | 113458 | 85 | 99,9 % | 1334,8x |
| 3155 | 3.2.8 Los párrafos | Judicial | 79146 | 96 | 99,9 % | 824,4x |
| 3156 | 3.2.9 Ineficacia del acuerdo | Judicial | 64632 | 84 | 99,9 % | 769,4x |
| 3157 | 3.2.9 Las oraciones | Judicial | 79146 | 79 | 99,9 % | 1001,8x |
| 3158 | 3.3           La igualdad ante la | Constitucional | 121906 | 66 | 99,9 % | 1847,1x |
| 3159 | 3.3          Aspectos sustantivos | Familia | 65192 | 52 | 99,9 % | 1253,7x |
| 3160 | 3.3     La protección de datosy | Constitucional | 104063 | 88 | 99,9 % | 1182,5x |
| 3161 | 3.3     Sobre las funciones | Judicial | 54457 | 57 | 99,9 % | 955,4x |
| 3162 | 3.3    Ingreso a las salas de audiencia y | Judicial | 39447 | 53 | 99,9 % | 744,3x |
| 3163 | 3.3. Derechos o acciones en una sociedad propietaria del inmueble que sirva de | Familia | 44766 | 53 | 99,9 % | 844,6x |
| 3164 | 3.3. Las obligaciones que tienen por fuente un delito o cuasidelito cometido por la | Familia | 136567 | 182 | 99,9 % | 750,4x |
| 3165 | 3.3.1 Componentes del back office | Judicial | 83934 | 89 | 99,9 % | 943,1x |
| 3166 | 3.3.1 Concepto | Judicial | 79146 | 101 | 99,9 % | 783,6x |
| 3167 | 3.3.1 Contar con servicios educativos y de | Judicial | 89476 | 97 | 99,9 % | 922,4x |
| 3168 | 3.3.1 Del origen y contexto de la idea de legislar | Judicial | 93914 | 109 | 99,9 % | 861,6x |
| 3169 | 3.3.1 Derecho a juicio público | Penal | 211066 | 128 | 99,9 % | 1649,0x |
| 3170 | 3.3.1 El deber de dirección y supervisión entendido | Penal | 119528 | 110 | 99,9 % | 1086,6x |
| 3171 | 3.3.1 El hecho internacionalmente ilícito | Penal | 121924 | 89 | 99,9 % | 1369,9x |
| 3172 | 3.3.1 Ingresos | Judicial | 81476 | 81 | 99,9 % | 1005,9x |
| 3173 | 3.3.1 La igualdad ante la ley como prohibición | Constitucional | 121906 | 127 | 99,9 % | 959,9x |
| 3174 | 3.3.1 Mecanismos extrajudiciales de | Constitucional | 112823 | 87 | 99,9 % | 1296,8x |
| 3175 | 3.3.1 Precalificación | Procesal | 94881 | 70 | 99,9 % | 1355,4x |
| 3176 | 3.3.1.1 Contenido de la Precalificación | Procesal | 94881 | 109 | 99,9 % | 870,5x |
| 3177 | 3.3.1.1 Gestión administrativa de tribunales | Judicial | 83934 | 114 | 99,9 % | 736,3x |
| 3178 | 3.3.1.1 Mutuo acuerdo | Laboral | 100583 | 126 | 99,9 % | 798,3x |
| 3179 | 3.3.1.1 Punto Nacional de Contacto de la Organización | Constitucional | 112823 | 65 | 99,9 % | 1735,7x |
| 3180 | 3.3.1.2 Estadísticas jurisdiccionales | Judicial | 83934 | 98 | 99,9 % | 856,5x |
| 3181 | 3.3.1.2 Instituto Nacional de Derechos Humanos | Constitucional | 112823 | 78 | 99,9 % | 1446,4x |
| 3182 | 3.3.1.2 Vencimiento del plazo convenido | Laboral | 100583 | 114 | 99,9 % | 882,3x |
| 3183 | 3.3.1.3 Conclusión del trabajo o servicio que dio origen al | Laboral | 100583 | 130 | 99,9 % | 773,7x |
| 3184 | 3.3.1.3 Sistemas de tramitación de causas | Judicial | 83934 | 97 | 99,9 % | 865,3x |
| 3185 | 3.3.1.4 Apoyo a la decisión jurisdiccional | Judicial | 83934 | 98 | 99,9 % | 856,5x |
| 3186 | 3.3.1.5 Expediente electrónico | Judicial | 83934 | 88 | 99,9 % | 953,8x |
| 3187 | 3.3.2 Acceso a servicios de salud sexual de calidad | Judicial | 89476 | 115 | 99,9 % | 778,1x |
| 3188 | 3.3.2 Calificación | Procesal | 94881 | 117 | 99,9 % | 810,9x |
| 3189 | 3.3.2 Componentes del front office | Judicial | 83934 | 106 | 99,9 % | 791,8x |
| 3190 | 3.3.2 De los fundamentos para la idea de | Judicial | 93914 | 55 | 99,9 % | 1707,5x |
| 3191 | 3.3.2 Exigencias relativas a la orgánica | Penal | 119528 | 91 | 99,9 % | 1313,5x |
| 3192 | 3.3.2 Finalidad de la argumentación | Judicial | 79146 | 88 | 99,9 % | 899,4x |
| 3193 | 3.3.2 Funciones reguladas en leyes generales | Judicial | 54457 | 78 | 99,9 % | 698,2x |
| 3194 | 3.3.2 La igualdad ante la ley como igualdad | Constitucional | 121906 | 101 | 99,9 % | 1207,0x |
| 3195 | 3.3.2 La integración y distribución | Penal | 57066 | 84 | 99,9 % | 679,4x |
| 3196 | 3.3.2 La responsabilidad internacional | Penal | 121924 | 93 | 99,9 % | 1311,0x |
| 3197 | 3.3.2 Mecanismos de reclamación no | Constitucional | 112823 | 70 | 99,9 % | 1611,8x |
| 3198 | 3.3.2 Respuesta del Poder Judicial a las | Penal | 72395 | 107 | 99,9 % | 676,6x |
| 3199 | 3.3.2 Régimen de las tierras indígenas en el | Judicial | 134465 | 94 | 99,9 % | 1430,5x |
| 3200 | 3.3.2 Término | Judicial | 81476 | 42 | 99,9 % | 1939,9x |
| 3201 | 3.3.2.1 Labores asignadas en el CPrP | Judicial | 54457 | 63 | 99,9 % | 864,4x |
| 3202 | 3.3.2.1 Oficina Judicial Virtual | Judicial | 83934 | 94 | 99,9 % | 892,9x |
| 3203 | 3.3.2.2 Audiencias | Judicial | 83934 | 97 | 99,9 % | 865,3x |
| 3204 | 3.3.2.2 Invalidez total o parcial del trabajador | Laboral | 100583 | 109 | 99,9 % | 922,8x |
| 3205 | 3.3.2.2 Mecanismos de reclamación establecidos | Constitucional | 112823 | 75 | 99,9 % | 1504,3x |
| 3206 | 3.3.2.3 Cuaderno de tercerías | Judicial | 52128 | 62 | 99,9 % | 840,8x |
| 3207 | 3.3.2.3 Notificaciones | Judicial | 83934 | 96 | 99,9 % | 874,3x |
| 3208 | 3.3.2.4 Consulta de causas | Judicial | 83934 | 97 | 99,9 % | 865,3x |
| 3209 | 3.3.2.4 Cuaderno de incidentes | Judicial | 52128 | 63 | 99,9 % | 827,4x |
| 3210 | 3.3.2.5 Pagos online | Judicial | 83934 | 91 | 99,9 % | 922,4x |
| 3211 | 3.3.2.6 Atención autónoma | Judicial | 83934 | 93 | 99,9 % | 902,5x |
| 3212 | 3.3.2.7 Atención asistida | Judicial | 83934 | 102 | 99,9 % | 822,9x |
| 3213 | 3.3.3 Acceso a métodos anticonceptivos | Judicial | 89476 | 100 | 99,9 % | 894,8x |
| 3214 | 3.3.3 Contenido esencial de un sistema de | Penal | 119528 | 87 | 99,9 % | 1373,9x |
| 3215 | 3.3.3 De algunos aspectos de la tramitación legislativa | Judicial | 93914 | 55 | 99,9 % | 1707,5x |
| 3216 | 3.3.3 Igualdad en la ley e igualdad ante la ley | Constitucional | 121906 | 106 | 99,9 % | 1150,1x |
| 3217 | 3.3.3 Impugnación de la Calificación | Procesal | 94881 | 66 | 99,9 % | 1437,6x |
| 3218 | 3.3.3 Los demandantes | Judicial | 81476 | 42 | 99,9 % | 1939,9x |
| 3219 | 3.3.3 Mapa conceptual de la argumentación | Judicial | 79146 | 61 | 99,9 % | 1297,5x |
| 3220 | 3.3.3 Mecanismos internacionales | Constitucional | 112823 | 97 | 99,9 % | 1163,1x |
| 3221 | 3.3.3 Respuesta del Estado de Chile al informe | Penal | 72395 | 106 | 99,9 % | 683,0x |
| 3222 | 3.3.3 Régimen de las tierras indígenas en | Judicial | 134465 | 89 | 99,9 % | 1510,8x |
| 3223 | 3.3.3.1 El deber de advertencia de la peligrosidad | Penal | 119528 | 88 | 99,9 % | 1358,3x |
| 3224 | 3.3.3.1 Renuncia voluntaria | Laboral | 100583 | 150 | 99,9 % | 670,6x |
| 3225 | 3.3.3.1 Sistema interamericano de derechos humanos | Constitucional | 112823 | 96 | 99,9 % | 1175,2x |
| 3226 | 3.3.3.2 Autodespido o despido indirecto | Laboral | 100583 | 126 | 99,9 % | 798,3x |
| 3227 | 3.3.3.2 Deber de respuesta frente al riesgo previamente | Penal | 119528 | 100 | 99,9 % | 1195,3x |
| 3228 | 3.3.3.2 Sistema universal de los derechos humanos | Constitucional | 112823 | 78 | 99,9 % | 1446,4x |
| 3229 | 3.3.4 Acceso a servicios de salud o atención médica | Judicial | 89476 | 114 | 99,9 % | 784,9x |
| 3230 | 3.3.4 Causal invocada en la demanda | Judicial | 81476 | 62 | 99,9 % | 1314,1x |
| 3231 | 3.3.4 Etapas del procedimiento | Judicial | 64632 | 93 | 99,9 % | 695,0x |
| 3232 | 3.3.4 Pregunta orientadora | Penal | 72395 | 81 | 99,9 % | 893,8x |
| 3233 | 3.3.4 Requisitos de la argumentación | Judicial | 79146 | 88 | 99,9 % | 899,4x |
| 3234 | 3.3.4.1 Causales de despido disciplinario | Laboral | 100583 | 145 | 99,9 % | 693,7x |
| 3235 | 3.3.4.2 Necesidades de la empresa, establecimiento o | Laboral | 100583 | 91 | 99,9 % | 1105,3x |
| 3236 | 3.3.4.4 Alimentos a los hermanos | Familia | 65192 | 70 | 99,9 % | 931,3x |
| 3237 | 3.3.4.5 Por sometimiento a procedimiento concursal de | Laboral | 100583 | 123 | 99,9 % | 817,7x |
| 3238 | 3.3.5 De la ejecutoriedad de las calificaciones | Procesal | 94881 | 117 | 99,9 % | 810,9x |
| 3239 | 3.3.5 Etapas de la argumentación | Judicial | 79146 | 101 | 99,9 % | 783,6x |
| 3240 | 3.3.5 Multas | Judicial | 81476 | 66 | 99,9 % | 1234,5x |
| 3241 | 3.3.5 Protección del embarazo y de las enfermedades | Judicial | 89476 | 98 | 99,9 % | 913,0x |
| 3242 | 3.3.5.3 Extinción | Familia | 65192 | 87 | 99,9 % | 749,3x |
| 3243 | 3.3.5.3.1 Muerte del alimentario | Familia | 65192 | 89 | 99,9 % | 732,5x |
| 3244 | 3.3.6   Interrupción legal y segura del embarazo en circunstancias específicas                        134 | Judicial | 89476 | 58 | 99,9 % | 1542,7x |
| 3245 | 3.3.6 Elementos de la argumentación | Judicial | 79146 | 101 | 99,9 % | 783,6x |
| 3246 | 3.3.6 Interrupción legal y segura del embarazo | Judicial | 89476 | 102 | 99,9 % | 877,2x |
| 3247 | 3.3.6 La prescripción | Familia | 65192 | 83 | 99,9 % | 785,4x |
| 3248 | 3.3.6 Resolución de término | Judicial | 64632 | 88 | 99,9 % | 734,5x |
| 3249 | 3.3.6 Transparencia en el procedimiento de Calificación | Procesal | 94881 | 109 | 99,9 % | 870,5x |
| 3250 | 3.3.6.4 Interrupción | Familia | 65192 | 94 | 99,9 % | 693,5x |
| 3251 | 3.3.7 Concepto de argumentación jurídica | Judicial | 79146 | 83 | 99,9 % | 953,6x |
| 3252 | 3.3.7 De la organización administrativa | Penal | 57066 | 75 | 99,9 % | 760,9x |
| 3253 | 3.3.8 El abogado y el empleo de la | Judicial | 79146 | 94 | 99,9 % | 842,0x |
| 3254 | 3.4               Críticas a la Ley N° 20.609 y | Judicial | 81476 | 44 | 99,9 % | 1851,7x |
| 3255 | 3.4             Rol de las jurisdicciones nacionales en el | Penal | 121924 | 62 | 99,9 % | 1966,5x |
| 3256 | 3.4     Las políticas judiciales en materia de | Constitucional | 104063 | 88 | 99,9 % | 1182,5x |
| 3257 | 3.4    Cumplimiento de sentencias | Laboral | 71986 | 68 | 99,9 % | 1058,6x |
| 3258 | 3.4.1 Comunicación de terminación del contrato | Laboral | 100583 | 143 | 99,9 % | 703,4x |
| 3259 | 3.4.1 Concepto | Judicial | 79146 | 101 | 99,9 % | 783,6x |
| 3260 | 3.4.1 Concepto de delito informático | Judicial | 96536 | 84 | 99,9 % | 1149,2x |
| 3261 | 3.4.1 De las Comisiones Precalificadoras | Procesal | 94881 | 115 | 99,9 % | 825,1x |
| 3262 | 3.4.1 El rol de las tecnologías en el futuro | Judicial | 83934 | 89 | 99,9 % | 943,1x |
| 3263 | 3.4.1 El régimen de los recursos naturales y su | Judicial | 134465 | 98 | 99,9 % | 1372,1x |
| 3264 | 3.4.1 Reproducción de la sentencia | Constitucional | 121906 | 117 | 99,9 % | 1041,9x |
| 3265 | 3.4.1 Requisitos | Judicial | 52128 | 78 | 99,9 % | 668,3x |
| 3266 | 3.4.1 Violencia intrafamiliar constitutiva de delito | Familia | 95131 | 91 | 99,9 % | 1045,4x |
| 3267 | 3.4.1 Ámbito de aplicación espacial y material | Laboral | 113458 | 88 | 99,9 % | 1289,3x |
| 3268 | 3.4.1.1 Antecedente histórico de la figura en | Familia | 95131 | 92 | 99,9 % | 1034,0x |
| 3269 | 3.4.1.1 Definición en el proyecto original | Judicial | 93914 | 97 | 99,9 % | 968,2x |
| 3270 | 3.4.1.1 Tutela en la etapa precontractual | Laboral | 113458 | 109 | 99,9 % | 1040,9x |
| 3271 | 3.4.1.2 Bien jurídico protegido | Familia | 95131 | 122 | 99,9 % | 779,8x |
| 3272 | 3.4.1.3 Definición de identidad de género en el | Judicial | 93914 | 75 | 99,9 % | 1252,2x |
| 3273 | 3.4.1.3 Elementos del tipo penal: conducta típica | Familia | 95131 | 84 | 99,9 % | 1132,5x |
| 3274 | 3.4.1.4 Elementos del tipo penal: la habitualidad | Familia | 95131 | 97 | 99,9 % | 980,7x |
| 3275 | 3.4.1.5 Elementos del tipo penal: sujetos | Familia | 95131 | 75 | 99,9 % | 1268,4x |
| 3276 | 3.4.1.6 Elementos del tipo penal: elemento subjetivo | Familia | 95131 | 72 | 99,9 % | 1321,3x |
| 3277 | 3.4.1.7 Elementos del tipo penal: la pena | Familia | 95131 | 84 | 99,9 % | 1132,5x |
| 3278 | 3.4.1.8 Exigencia de procesabilidad | Familia | 95131 | 96 | 99,9 % | 990,9x |
| 3279 | 3.4.2 Acreditación de pago de | Laboral | 100583 | 111 | 99,9 % | 906,2x |
| 3280 | 3.4.2 Análisis de la sentencia | Constitucional | 121906 | 109 | 99,9 % | 1118,4x |
| 3281 | 3.4.2 Características | Judicial | 52128 | 65 | 99,9 % | 802,0x |
| 3282 | 3.4.2 De las Comisiones Precalificadoras en las Cortes | Procesal | 94881 | 117 | 99,9 % | 810,9x |
| 3283 | 3.4.2 Tecnologías aplicables a la labor de la justicia | Judicial | 83934 | 111 | 99,9 % | 756,2x |
| 3284 | 3.4.2 Tecnologías aplicables a la labor de la justicia                              167 | Judicial | 83934 | 44 | 99,9 % | 1907,6x |
| 3285 | 3.4.2 Ámbito temporal de la acción de tutela y | Laboral | 113458 | 120 | 99,9 % | 945,5x |
| 3286 | 3.4.2.1 Integración del Órgano Precalificador | Procesal | 94881 | 65 | 99,9 % | 1459,7x |
| 3287 | 3.4.2.1. Antecedentes generales y modificaciones | Familia | 95131 | 128 | 99,9 % | 743,2x |
| 3288 | 3.4.2.2 Análisis de la figura simple de | Familia | 95131 | 96 | 99,9 % | 990,9x |
| 3289 | 3.4.2.2 Redes sociales | Judicial | 83934 | 88 | 99,9 % | 953,8x |
| 3290 | 3.4.2.2 Representantes de los escalafones | Procesal | 94881 | 67 | 99,9 % | 1416,1x |
| 3291 | 3.4.2.3 Análisis de la figura calificada | Familia | 95131 | 98 | 99,9 % | 970,7x |
| 3292 | 3.4.2.3 Interoperabilidad | Judicial | 83934 | 94 | 99,9 % | 892,9x |
| 3293 | 3.4.2.3 Requisitos para ser representante | Procesal | 101194 | 111 | 99,9 % | 911,7x |
| 3294 | 3.4.2.4 Delito de sometimiento a trato degradante | Familia | 95131 | 118 | 99,9 % | 806,2x |
| 3295 | 3.4.2.4 Realidad virtual | Judicial | 83934 | 91 | 99,9 % | 922,4x |
| 3296 | 3.4.2.6 Blockchain | Judicial | 83934 | 78 | 99,9 % | 1076,1x |
| 3297 | 3.4.2.7 Teletrabajo, jurisdicción en línea | Judicial | 83934 | 96 | 99,9 % | 874,3x |
| 3298 | 3.4.3 Características objetivas de | Judicial | 96536 | 65 | 99,9 % | 1485,2x |
| 3299 | 3.4.3 Estructura del texto expositivo | Judicial | 79146 | 54 | 99,9 % | 1465,7x |
| 3300 | 3.4.3 Inhabilidades | Procesal | 101194 | 72 | 99,9 % | 1405,5x |
| 3301 | 3.4.3 Pasos para hacer una especificación | Constitucional | 121906 | 114 | 99,9 % | 1069,4x |
| 3302 | 3.4.3.1 Antecedentes | Familia | 95131 | 67 | 99,9 % | 1419,9x |
| 3303 | 3.4.3.1 Conductas defraudatorias | Judicial | 96536 | 75 | 99,9 % | 1287,1x |
| 3304 | 3.4.3.2 Análisis del nuevo delito de femicidio | Familia | 95131 | 114 | 99,9 % | 834,5x |
| 3305 | 3.4.3.2 Conductas de sabotaje | Judicial | 96536 | 59 | 99,9 % | 1636,2x |
| 3306 | 3.4.3.2 El femicidio introducido por la Ley Nº 21.212 | Familia | 95131 | 98 | 99,9 % | 970,7x |
| 3307 | 3.4.3.3 Espionaje informático | Judicial | 96536 | 89 | 99,9 % | 1084,7x |
| 3308 | 3.4.3.4 Intrusiones ilegítimas | Judicial | 96536 | 97 | 99,9 % | 995,2x |
| 3309 | 3.4.4 Comisiones recopiladoras de antecedentes | Procesal | 101194 | 88 | 99,9 % | 1149,9x |
| 3310 | 3.4.4 Derechos de personas titulares del | Judicial | 93914 | 70 | 99,9 % | 1341,6x |
| 3311 | 3.4.4 Síntesis integral del texto expositivo | Judicial | 79146 | 55 | 99,9 % | 1439,0x |
| 3312 | 3.4.5 Definición | Judicial | 79146 | 93 | 99,9 % | 851,0x |
| 3313 | 3.4.6 Efectos de la rectificación | Judicial | 93914 | 55 | 99,9 % | 1707,5x |
| 3314 | 3.4.6.1 Concepto | Judicial | 79146 | 53 | 99,9 % | 1493,3x |
| 3315 | 3.4.6.2 Objetivos del análisis | Judicial | 79146 | 94 | 99,9 % | 842,0x |
| 3316 | 3.4.8 Resumen | Judicial | 79146 | 93 | 99,9 % | 851,0x |
| 3317 | 3.4.9 División | Judicial | 79146 | 67 | 99,9 % | 1181,3x |
| 3318 | 3.5     Acción de habeas data y su | Constitucional | 104063 | 72 | 99,9 % | 1445,3x |
| 3319 | 3.5.1 Notificación a funcionarios o empleados | Procesal | 101194 | 96 | 99,9 % | 1054,1x |
| 3320 | 3.5.1 Ámbito sustantivo | Judicial | 96536 | 81 | 99,9 % | 1191,8x |
| 3321 | 3.5.1.1 Acceso ilícito (art. 2) | Judicial | 96536 | 62 | 99,9 % | 1557,0x |
| 3322 | 3.5.1.2 Del artículo 160 del Código del Trabajo: la indemni- | Laboral | 100583 | 128 | 99,9 % | 785,8x |
| 3323 | 3.5.1.2 Interceptación ilícita (art. 3) | Judicial | 96536 | 91 | 99,9 % | 1060,8x |
| 3324 | 3.5.1.3 Ataque a la integridad de datos (art. 4) | Judicial | 96536 | 68 | 99,9 % | 1419,6x |
| 3325 | 3.5.1.4 Ataque a la integridad del sistema (art. 5) | Judicial | 96536 | 76 | 99,9 % | 1270,2x |
| 3326 | 3.5.1.4 Del artículo 161 del Código del Trabajo: la indemni- | Laboral | 100583 | 65 | 99,9 % | 1547,4x |
| 3327 | 3.5.1.5 Abuso de dispositivos (art. 6) | Judicial | 96536 | 92 | 99,9 % | 1049,3x |
| 3328 | 3.5.1.6 En el caso de la causal del artículo 163 bis del Códi- | Laboral | 100583 | 114 | 99,9 % | 882,3x |
| 3329 | 3.5.1.6 Falsificación informática (art. 7) | Judicial | 96536 | 87 | 99,9 % | 1109,6x |
| 3330 | 3.5.1.7 Fraude informático (art. 8) | Judicial | 96536 | 68 | 99,9 % | 1419,6x |
| 3331 | 3.5.1.8 Delitos relacionados con la | Judicial | 96536 | 92 | 99,9 % | 1049,3x |
| 3332 | 3.5.1.9 Delitos relacionados con la | Judicial | 96536 | 74 | 99,9 % | 1304,5x |
| 3333 | 3.5.2 Del procedimiento judicial para personas | Judicial | 93914 | 78 | 99,9 % | 1204,0x |
| 3334 | 3.5.2 Del procedimiento judicial para personas solicitantes con vínculo matrimonial vigente              155 | Judicial | 93914 | 65 | 99,9 % | 1444,8x |
| 3335 | 3.5.2 Indemnización por falta de aviso previo | Laboral | 100583 | 139 | 99,9 % | 723,6x |
| 3336 | 3.5.2 Modificación en la forma de notificación | Procesal | 101194 | 97 | 99,9 % | 1043,2x |
| 3337 | 3.5.2 Ámbito adjetivo o normas procesales | Judicial | 96536 | 100 | 99,9 % | 965,4x |
| 3338 | 3.6               El régimen infraccionalen la | Constitucional | 104063 | 57 | 99,9 % | 1825,7x |
| 3339 | 3.6           El derecho a la identidad de género de | Judicial | 93914 | 72 | 99,9 % | 1304,4x |
| 3340 | 3.6     Plazo para | Laboral | 100583 | 55 | 99,9 % | 1828,8x |
| 3341 | 3.6.1 Antecedentes | Judicial | 96536 | 93 | 99,9 % | 1038,0x |
| 3342 | 3.6.1 Notificación a funcionarios o empleados | Procesal | 94881 | 96 | 99,9 % | 988,3x |
| 3343 | 3.6.1 Remoción | Procesal | 101194 | 79 | 99,9 % | 1280,9x |
| 3344 | 3.6.1.1 Renuncia de funcionarios removidos | Procesal | 101194 | 107 | 99,9 % | 945,7x |
| 3345 | 3.6.1.2 Remuneración de funcionarios removidos referidos | Procesal | 101194 | 97 | 99,9 % | 1043,2x |
| 3346 | 3.6.2 Ascenso | Procesal | 101194 | 102 | 99,9 % | 992,1x |
| 3347 | 3.6.2 El bien jurídico protegido en la Ley Nº 19.223 | Judicial | 96536 | 100 | 99,9 % | 965,4x |
| 3348 | 3.6.2 Modificación en la forma de notificación | Procesal | 94881 | 97 | 99,9 % | 978,2x |
| 3349 | 3.6.3 El objeto del delito | Judicial | 96536 | 59 | 99,9 % | 1636,2x |
| 3350 | 3.6.3 Transacción | Familia | 65192 | 96 | 99,9 % | 679,1x |
| 3351 | 3.6.3.1 Solicitud de permisos del artículo 347 | Procesal | 101194 | 102 | 99,9 % | 992,1x |
| 3352 | 3.6.4 El sujeto activo de los delitos de la Ley Nº 19.223 | Judicial | 96536 | 93 | 99,9 % | 1038,0x |
| 3353 | 3.6.4 Sistema informático de registro de calificaciones | Procesal | 101194 | 96 | 99,9 % | 1054,1x |
| 3354 | 3.6.5 Los elementos subjetivos de los | Judicial | 96536 | 106 | 99,9 % | 910,7x |
| 3355 | 3.6.6 Análisis del artículo 1º de la Ley Nº 19.223 | Judicial | 96536 | 71 | 99,9 % | 1359,7x |
| 3356 | 3.6.7 Análisis del artículo 3º de la Ley Nº 19.223 | Judicial | 96536 | 89 | 99,9 % | 1084,7x |
| 3357 | 3.7     Sanción del despido con incumplimiento | Laboral | 100583 | 66 | 99,9 % | 1524,0x |
| 3358 | 3.7 Criterios de programación de audiencias                                                   101 | Judicial | 39447 | 46 | 99,9 % | 857,5x |
| 3359 | 3.7 Sanción del despido con incumplimiento de las obligaciones previsionales. Alcance de la | Laboral | 100583 | 67 | 99,9 % | 1501,2x |
| 3360 | 3.7. Principales leyes complementarias del Código Civil. 4.- Tendencias actuales del | Civil | 90056 | 81 | 99,9 % | 1111,8x |
| 3361 | 3.7.1 Delitos contra la propiedad | Judicial | 96536 | 107 | 99,9 % | 902,2x |
| 3362 | 3.7.1 Información estadística | Judicial | 93914 | 93 | 99,9 % | 1009,8x |
| 3363 | 3.7.1 Remoción | Procesal | 94881 | 79 | 99,9 % | 1201,0x |
| 3364 | 3.7.1.1 Renuncia de funcionarios removidos | Procesal | 94881 | 107 | 99,9 % | 886,7x |
| 3365 | 3.7.1.2 Remuneración de funcionarios removidos referidos | Procesal | 94881 | 97 | 99,9 % | 978,2x |
| 3366 | 3.7.2 Ascenso | Procesal | 94881 | 102 | 99,9 % | 930,2x |
| 3367 | 3.7.2 Competencia relativa | Familia | 65192 | 71 | 99,9 % | 918,2x |
| 3368 | 3.7.2 Delitos de pornografía infantil a | Judicial | 96536 | 81 | 99,9 % | 1191,8x |
| 3369 | 3.7.2 Lineamientos jurisprudenciales25 | Judicial | 93914 | 97 | 99,9 % | 968,2x |
| 3370 | 3.7.3   Grooming, bullying y otras formas de discriminación en línea                                       129 | Judicial | 96536 | 53 | 99,9 % | 1821,4x |
| 3371 | 3.7.3 Grooming, bullying y otras formas | Judicial | 96536 | 81 | 99,9 % | 1191,8x |
| 3372 | 3.7.3.1 Bullying | Judicial | 96536 | 100 | 99,9 % | 965,4x |
| 3373 | 3.7.3.1 Solicitud de permisos del artículo 347 | Procesal | 94881 | 102 | 99,9 % | 930,2x |
| 3374 | 3.7.3.2 Grooming | Judicial | 96536 | 91 | 99,9 % | 1060,8x |
| 3375 | 3.7.4 Patrocinio | Familia | 65192 | 74 | 99,9 % | 881,0x |
| 3376 | 3.7.4 Sistema informático de registro de calificaciones | Procesal | 94881 | 96 | 99,9 % | 988,3x |
| 3377 | 3.7.6 Legitimación | Familia | 65192 | 89 | 99,9 % | 732,5x |
| 3378 | 3.7.7 Estructura y fases de su tramitación | Familia | 65192 | 94 | 99,9 % | 693,5x |
| 3379 | 3.8        Ejecución forzosa | Familia | 65192 | 50 | 99,9 % | 1303,8x |
| 3380 | 3.8     Referencias a otros Estados que establecen | Judicial | 93914 | 54 | 99,9 % | 1739,1x |
| 3381 | 3.8.          El despido atentatorio de derechos | Laboral | 113458 | 80 | 99,9 % | 1418,2x |
| 3382 | 3.8.1 Alcance del concepto de territorio | Judicial | 134465 | 110 | 99,9 % | 1222,4x |
| 3383 | 3.8.2 Métodos de cumplimiento y estructura | Familia | 65192 | 96 | 99,9 % | 679,1x |
| 3384 | 3.8.3 Constitución    de    servidumbres | Judicial | 134465 | 85 | 99,9 % | 1581,9x |
| 3385 | 3.8.3.1.3 Tramitación de los arrestos | Familia | 65192 | 85 | 99,9 % | 767,0x |
| 3386 | 30 Agrega: «Basar una decisión en el peso de las reglas de las pruebas, es como | Judicial | 150341 | 80 | 99,9 % | 1879,3x |
| 3387 | 30 Considerando séptimo: «En relación al padre, dicha institución concluye que | Familia | 97488 | 81 | 99,9 % | 1203,6x |
| 3388 | 30 De hecho, Vásquez critica expresamente a Duce señalando que utiliza datos de | Procesal | 86112 | 105 | 99,9 % | 820,1x |
| 3389 | 30 En este sentido, Mañalich (2018: 108), para quien siempre sería aplicable en | Penal | 178516 | 130 | 99,9 % | 1373,2x |
| 3390 | 30 Entre los antecedentes que reveló Jorratt, indicó que el ministro del Interior | Penal | 178516 | 140 | 99,9 % | 1275,1x |
| 3391 | 30 La jurisprudencia ha determinado: «Que la actora reconvencional debe ser | Familia | 123490 | 130 | 99,9 % | 949,9x |
| 3392 | 30 Para más información, véase «Informe Mundial sobre Envejecimiento y Salud | Judicial | 87950 | 54 | 99,9 % | 1628,7x |
| 3393 | 30. Boletín N° 13.285-34. Proyecto de ley que modifica la Ley | Judicial | 89476 | 68 | 99,9 % | 1315,8x |
| 3394 | 30. CORTE DE APELACIONES DE SAN MIGUEL, rol | Familia | 65085 | 66 | 99,9 % | 986,1x |
| 3395 | 30. Decreto Nº 142/2010, aprueba el reglamento de la Ley N° 20.422, que esta- | Constitucional | 121906 | 88 | 99,9 % | 1385,3x |
| 3396 | 30. DÍAZ DE VALDÉS, José (2018): “Las categorías sospechosas en el Derecho | Judicial | 81476 | 72 | 99,9 % | 1131,6x |
| 3397 | 30. Esta afirmación a que debe llegarse, se patentiza de resalto con el precepto consignado en el | Civil | 171433 | 226 | 99,9 % | 758,6x |
| 3398 | 30. Evaluación de programa de fortalecimiento de habilidades para | Constitucional | 177323 | 137 | 99,9 % | 1294,3x |
| 3399 | 30. Hecho de referencia (o de conexión): conducta | Penal | 119528 | 89 | 99,9 % | 1343,0x |
| 3400 | 30. Inspección Provincial del Trabajo de Temuco con | Laboral | 113458 | 97 | 99,9 % | 1169,7x |
| 3401 | 30. La obligación extraterritorial de proteger exige que los | Constitucional | 112823 | 104 | 99,9 % | 1084,8x |
| 3402 | 30. Ley N° 21.120. Reconoce y da protección al derecho a la identidad | Judicial | 89476 | 49 | 99,9 % | 1826,0x |
| 3403 | 30. Saldivia, Laura. 2009. “Reexaminando la cons- | Judicial | 87237 | 87 | 99,9 % | 1002,7x |
| 3404 | 303   GAMONAL C., Sergio (2004c), “Los derechos del trabajador en la Constitución chilena”, Anuario de Derecho | Laboral | 113458 | 97 | 99,9 % | 1169,7x |
| 3405 | 303 Los individuos perpetradores comenzaron a ser enjuiciados en Austria y en Alemania. En 1994, una corte | Penal | 121924 | 135 | 99,9 % | 903,1x |
| 3406 | 303. Y siempre que la comisión del delito sea consecuencia del | Penal | 119528 | 118 | 99,9 % | 1012,9x |
| 3407 | 304 GAMBOA (1999), pp. 80-84; FOX (1999), pp. 207-208; GÓMEZ (2000), pp. 277-280; Audiencia Nacional (Espa- | Penal | 121924 | 136 | 99,9 % | 896,5x |
| 3408 | 304 MCGINLEY, Ann (2018), “Género, derecho y cultura en los lugares de trabajo jurídicos: un caso chileno de | Laboral | 113458 | 97 | 99,9 % | 1169,7x |
| 3409 | 306 En una reciente sentencia de la Corte Suprema (Corte Suprema, 4 de abril de 2018, Rol Nº 12176-2017), co- | Civil | 142015 | 145 | 99,9 % | 979,4x |
| 3410 | 306; SHINER (2005), p. 214; WOUTERS y VERHOEVEN (2005), pp. 401-416; PUCEIRO (2005), p. 379; DE WET | Penal | 121924 | 104 | 99,9 % | 1172,3x |
| 3411 | 308 Corte Suprema, 25 de septiembre de 2007, Rol Nº 4103-2005. En el mismo sentido, véase Corte Suprema, 12 | Civil | 142015 | 106 | 99,9 % | 1339,8x |
| 3412 | 308 Corte Suprema, Rol 7023/2009, de 14 de enero de 2010. Nos referiremos a esta sentencia en el capítulo 3.6 | Laboral | 113458 | 128 | 99,9 % | 886,4x |
| 3413 | 31                Pena de Comiso para crímenes y        Pérdida de los efectos que provengan | Penal | 194788 | 111 | 99,9 % | 1754,8x |
| 3414 | 31   Acta N° 181-2007, Sistema de evaluación del desempeño de funcionarios y empleados del Poder Judicial (de | Procesal | 94881 | 65 | 99,9 % | 1459,7x |
| 3415 | 31 A propósito de esta última alternativa, Jünemann y Wiegand citan como ejem- | Laboral | 98828 | 92 | 99,9 % | 1074,2x |
| 3416 | 31 El autor considera que: «Consciousness of the instant ‘now’ has logically to be | Judicial | 150341 | 81 | 99,9 % | 1856,1x |
| 3417 | 31 En España véase Gracia Martin (2016: 73), quien señala que las tesis favorables | Penal | 178516 | 101 | 99,9 % | 1767,5x |
| 3418 | 31 En la que se reclamaba en contra de las deficientes condiciones sanitarias de | Judicial | 81675 | 71 | 99,9 % | 1150,4x |
| 3419 | 31 En un sentido similar, vinculando la fidelidad en el desempeño del cargo con | Procesal | 86112 | 79 | 99,9 % | 1090,0x |
| 3420 | 31 Hay que hacer presente que las estadísticas oficiales del Poder Judicial no son | Judicial | 144656 | 109 | 99,9 % | 1327,1x |
| 3421 | 31 Incluso, está demostrado que cuando los indicadores señalan mayores niveles | Penal | 178516 | 109 | 99,9 % | 1637,8x |
| 3422 | 31 La calificación de «nominal» de nuestro sistema es sostenida por Valladares | Penal | 97633 | 65 | 99,9 % | 1502,0x |
| 3423 | 31 La sentencia Corte Suprema rol 4135-1999, de 29 de enero de 2001, resuelve que | Judicial | 144656 | 109 | 99,9 % | 1327,1x |
| 3424 | 31 Sentencia de la Corte de Apelaciones de Santiago, rol 3.174-2018, 26 de julio de | Familia | 97488 | 53 | 99,9 % | 1839,4x |
| 3425 | 31 Sentencia de la Corte de Apelaciones de Talca, 16 de octubre de 2020, rol 486- | Judicial | 150341 | 178 | 99,9 % | 844,6x |
| 3426 | 31. CORTE DE APELACIONES DE SANTIAGO, rol N° | Familia | 65085 | 74 | 99,9 % | 879,5x |
| 3427 | 31. DIEZ SCHWERTER, José Luis (2008): “Responsa-               FERRER, Santiago (2013): “Revisión crítica del | Civil | 142015 | 117 | 99,9 % | 1213,8x |
| 3428 | 31. DÍAZ DE VALDÉS, José (2017): “Cuatro años de la ley Zamudio: análisis | Judicial | 81476 | 71 | 99,9 % | 1147,5x |
| 3429 | 31. Esa obligación se extiende a cualquier entidad empresarial | Constitucional | 112823 | 98 | 99,9 % | 1151,3x |
| 3430 | 31. Esta Corte debe abordar estas temáticas teniendo en cuenta | Judicial | 93914 | 78 | 99,9 % | 1204,0x |
| 3431 | 31. FUENZALIDA, Daniela (2017): “Estatuto jurídico | Penal | 72395 | 97 | 99,9 % | 746,3x |
| 3432 | 31. Identificación de riesgos: una de las etapas de la | Penal | 119528 | 70 | 99,9 % | 1707,5x |
| 3433 | 31. STUVEN, Ana (2015): “La Iglesia católica chilena | Familia | 65192 | 80 | 99,9 % | 814,9x |
| 3434 | 32   Acta N° 181-2007, Sistema de evaluación del desempeño de funcionarios y empleados del Poder Judicial (de | Procesal | 101194 | 65 | 99,9 % | 1556,8x |
| 3435 | 32 El Acta 92-2005 es la norma más sistemática sobre el Consejo Técnico, aunque | Procesal | 86112 | 67 | 99,9 % | 1285,3x |
| 3436 | 32 En sentencia Corte Suprema rol 2564-2009, de 12 de octubre de 2010, se estima | Judicial | 144656 | 117 | 99,9 % | 1236,4x |
| 3437 | 32 Oficina de las Naciones Unidas contra las Drogas y el Delito, «Corrupción y | Penal | 178516 | 124 | 99,9 % | 1439,6x |
| 3438 | 32 Para más información, véase «Historia de la Ley 20.467», pp. 3-4, disponible en | Judicial | 62514 | 44 | 99,9 % | 1420,8x |
| 3439 | 32 Por cierto, otra estrategia diversa al paternalismo epistémico consistiría en | Procesal | 86112 | 52 | 99,9 % | 1656,0x |
| 3440 | 32 Sentencia de la Corte de Apelaciones de Santiago, rol 3.174-2018, 26 de julio de | Familia | 97488 | 53 | 99,9 % | 1839,4x |
| 3441 | 32.   Auto acordado, Acta Nº 754 - 2019 Corte Supre- | Administrativo | 89720 | 102 | 99,9 % | 879,6x |
| 3442 | 32. A mero título ilustrativo e incluso demostrativo de la dificultad | Judicial | 93914 | 92 | 99,9 % | 1020,8x |
| 3443 | 32. Aprueba Reglamento que Establece Normas para la Aplicación | Constitucional | 177323 | 149 | 99,9 % | 1190,1x |
| 3444 | 32. CORTE DE APELACIONES DE TALCA, rol N° 106-            45. CORTE SUPREMA, rol N° 7.080-2008, de veinti- | Familia | 65085 | 91 | 99,9 % | 715,2x |
| 3445 | 32. DÍAZ DE VALDÉS, José (2018): “Análisis cuantitativo de la acción | Judicial | 81476 | 70 | 99,9 % | 1163,9x |
| 3446 | 32. Responsabilidad por uso de instrumental defec- | Civil | 142015 | 144 | 99,9 % | 986,2x |
| 3447 | 326   RODRÍGUEZ-PIÑERO, Miguel (2004), “Libertad ideológica, contrato de trabajo y objeción de conciencia”, en | Laboral | 113458 | 63 | 99,9 % | 1800,9x |
| 3448 | 33   En medicina, se consideran tres tipos de hermafroditismo: seudohermafroditismo femenino, seudoherma- | Judicial | 89476 | 94 | 99,9 % | 951,9x |
| 3449 | 33 Boletín Legislativo 12.213-07, que Modifica diversos textos legales en materia de | Judicial | 89450 | 52 | 99,9 % | 1720,2x |
| 3450 | 33 El Protocolo describe cinco grupos vulnerables que serán foco de acción en sus | Constitucional | 177323 | 100 | 99,9 % | 1773,2x |
| 3451 | 33 El autor señala que «una cosa distinta es que, antes de esta ley, en cualquier | Penal | 178516 | 114 | 99,9 % | 1565,9x |
| 3452 | 33 Este punto se desarrolla más extensamente en el Material docente para jueces en | Judicial | 78893 | 93 | 99,9 % | 848,3x |
| 3453 | 33 Para Frieyro (2017: 182), comentando la tipificación del artículo 368 del Código | Penal | 97633 | 87 | 99,9 % | 1122,2x |
| 3454 | 33 Se citan como ejemplos de posibles pericias que pueden generar dicho riesgo | Procesal | 86112 | 127 | 99,9 % | 678,0x |
| 3455 | 33 Sentencia Corte Suprema rol 3136-2005, de 29 de marzo de 2007. En sentencia | Judicial | 144656 | 132 | 99,9 % | 1095,9x |
| 3456 | 33 Sentencia de la Corte Suprema, rol 38.490-2007, 24 de agosto de 2018; en el | Penal | 178516 | 175 | 99,9 % | 1020,1x |
| 3457 | 33 Un comentario respecto de los países en que se han recepcionado estas dos | Familia | 123490 | 162 | 99,9 % | 762,3x |
| 3458 | 33. Curso E-learning Derechos Humanos para funcionarios/as de | Constitucional | 177323 | 114 | 99,9 % | 1555,5x |
| 3459 | 33. DE BELMONTE, L.R.; GUTIERREZ, E.; MAGNANI             40. FREEDMAN, L.; ISAACS, S. (1993): “Human Rights | Judicial | 89476 | 107 | 99,9 % | 836,2x |
| 3460 | 33. Decreto Nº 47/2012, aprueba reglamento para la calificación y certificación | Constitucional | 121906 | 70 | 99,9 % | 1741,5x |
| 3461 | 33. DÍAZ, Iván (2013): “Ley chilena contra la discriminación. Una evaluación | Judicial | 81476 | 53 | 99,9 % | 1537,3x |
| 3462 | 33. En cumplimiento de su deber de proteger, los Estados partes | Constitucional | 112823 | 70 | 99,9 % | 1611,8x |
| 3463 | 33. Un juez(a) puede contribuir a la educación jurídica y profesional | Procesal | 94881 | 114 | 99,9 % | 832,3x |
| 3464 | 332   APARICIO, Joaquín (1992), “Empresas ideológicas y derechos fundamentales del trabajador”, Autoridad y | Laboral | 113458 | 154 | 99,9 % | 736,7x |
| 3465 | 34       Disponible en línea [consulta: 15.09.2020] | Administrativo | 89720 | 57 | 99,9 % | 1574,0x |
| 3466 | 34 Agregan los autores que si dicha conclusión, perjudicial al funcionario, es por | Penal | 178516 | 100 | 99,9 % | 1785,2x |
| 3467 | 34 Decreto 2, de 2015, del Ministerio Secretaría General de la Presidencia. Más | Penal | 178516 | 143 | 99,9 % | 1248,4x |
| 3468 | 34 Informe Nacional presentado de conformidad con el párrafo 23: «Calificó a las | Constitucional | 177323 | 109 | 99,9 % | 1626,8x |
| 3469 | 34 Para más información, véase «Ley 21.375 que consagra los cuidados paliativos y | Judicial | 87950 | 65 | 99,9 % | 1353,1x |
| 3470 | 34 Sagüés (2010: 119) destaca que «el criterio de la Corte Interamericana no es | Constitucional | 177323 | 104 | 99,9 % | 1705,0x |
| 3471 | 34 Sin embargo, MacCormick agrega (p. 226) «Few such stories allow of certainty | Judicial | 150341 | 106 | 99,9 % | 1418,3x |
| 3472 | 34 Sin perjuicio de lo anterior, la profesora Etcheberry (2019) ha establecido cinco | Familia | 97488 | 140 | 99,9 % | 696,3x |
| 3473 | 34 Universidad de Navarra, «Elementos subjetivos del injusto», disponible en | Judicial | 62514 | 39 | 99,9 % | 1602,9x |
| 3474 | 34 Véase el artículo 40.2 letra b) punto ii y vi de la Convención de los Derechos del | Penal | 86906 | 85 | 99,9 % | 1022,4x |
| 3475 | 34.   Tribunal Constitucional, Rol 2250-2012. Sentencia de 18 de junio de 2013 | Judicial | 81476 | 45 | 99,9 % | 1810,6x |
| 3476 | 34. CORTE DE APELACIONES DE TEMUCO, rol N°                47. CORTE SUPREMA, rol N° 1896-2009, de uno de | Familia | 65085 | 87 | 99,9 % | 748,1x |
| 3477 | 34. En los casos transnacionales, para lograr una rendición | Constitucional | 112823 | 105 | 99,9 % | 1074,5x |
| 3478 | 34. Implementación curso en “Derechos Humanos y Discapacidad” | Constitucional | 177323 | 135 | 99,9 % | 1313,5x |
| 3479 | 34. Ley N° 21.197. Modifica la Ley Nº 19.712, Ley del Deporte, la | Judicial | 89476 | 84 | 99,9 % | 1065,2x |
| 3480 | 340 Véase v.g. Corte de Apelaciones de Santiago: considerandos cuarto y decimocuarto del voto en contra del | Penal | 121924 | 148 | 99,9 % | 823,8x |
| 3481 | 341 Artículo 4° de la Convención: “Los Tratados serán publicados inmediatamente después del canje de las ra- | Penal | 121924 | 126 | 99,9 % | 967,7x |
| 3482 | 341. Una vez constatada la situación anterior, la Corte estima que el | Judicial | 92792 | 119 | 99,9 % | 779,8x |
| 3483 | 345 BULNES ALDUNATE, Luz (1980), “La libertad de trabajo y su protección en la Constitución de 1980”, Revista | Laboral | 113458 | 111 | 99,9 % | 1022,1x |
| 3484 | 346   Corte Suprema, 29 de agosto de 2017, Rol Nº 101769-2016. En igual sentido, véase Corte Suprema, 14 de | Civil | 142015 | 74 | 99,9 % | 1919,1x |
| 3485 | 35   ALEXY (2001), p. 89, GUASTINI (1999), p. 170 y MELIS VALENCIA, Christian (2009), Los derechos fundamen- | Laboral | 113458 | 80 | 99,9 % | 1418,2x |
| 3486 | 35 Dicha ley establece que las reformas a la Ley 20.393 entrarán en vigor el primer | Penal | 178516 | 113 | 99,9 % | 1579,8x |
| 3487 | 35 En un sentido similar Couture (2021: 198) señala: «La ley crea el litigante la | Judicial | 150341 | 150 | 99,9 % | 1002,3x |
| 3488 | 35 Fuentes (2008: 487) niega la existencia de norma internacional que obligue a | Constitucional | 177323 | 139 | 99,9 % | 1275,7x |
| 3489 | 35 La autora lo explica de la siguiente manera: «How supportive evidence is of a | Judicial | 150341 | 115 | 99,9 % | 1307,3x |
| 3490 | 35 Texto expreso de la letra a) del artículo 5 de la Ley 19.968, circunscrito solo a | Procesal | 86112 | 111 | 99,9 % | 775,8x |
| 3491 | 35 Véase la sentencia de la Corte Suprema, rol 4.387-2018, 13 de junio de 2018 y la | Familia | 97488 | 87 | 99,9 % | 1120,6x |
| 3492 | 35 Véase las Reglas de la Habana (números 59 al 60), las Reglas de Beijing (número | Penal | 86906 | 74 | 99,9 % | 1174,4x |
| 3493 | 35. CORTE DE APELACIONES DE TEMUCO, rol N°                48. CORTE SUPREMA, rol N° 4.783-2009, de catorce | Familia | 65085 | 88 | 99,9 % | 739,6x |
| 3494 | 35. DOMÍNGUEZ, Carmen (2006): “La reparación del | Civil | 142015 | 92 | 99,9 % | 1543,6x |
| 3495 | 35. Un juez(a) puede participar en organizaciones comunitarias sin | Procesal | 94881 | 109 | 99,9 % | 870,5x |
| 3496 | 350 La Asamblea General de las Naciones Unidas, desde que tomó nota del proyecto de artículos, refiere a la | Penal | 121924 | 124 | 99,9 % | 983,3x |
| 3497 | 351   Corte Suprema, 29 de agosto de 2017, Rol Nº 101769-2016; así también véase Corte Suprema, 6 de noviembre | Civil | 142015 | 117 | 99,9 % | 1213,8x |
| 3498 | 357   HENRÍQUEZ, Helia, RIQUELME, Verónica, GÁLVEZ, Thelma y MORALES, Gabriela (2006), “Lejos del trabajo | Laboral | 113458 | 96 | 99,9 % | 1181,9x |
| 3499 | 359 Primer Juzgado del Trabajo de Santiago, RIT T-272-2011 (caratulado “Vicuña Vergara con Santa Úrsula”), de | Laboral | 113458 | 122 | 99,9 % | 930,0x |
| 3500 | 36 Artículo 16, número 2 de la Ley 14.908: «[El juez] ordenará, en el mes de marzo | Familia | 97488 | 145 | 99,9 % | 672,3x |
| 3501 | 36 Cabe destacar que, dada la relevancia del tema y el mayor protagonismo de la | Penal | 178516 | 159 | 99,9 % | 1122,7x |
| 3502 | 36 El artículo 8, inciso primero, dispone: «Con sujeción a su Constitución y a los | Penal | 178516 | 171 | 99,9 % | 1044,0x |
| 3503 | 36 El detalle de los protocolos de uso de la fuerza se trata en el material docente | Judicial | 78893 | 65 | 99,9 % | 1213,7x |
| 3504 | 36 En materia de aplicación del derecho internacional sobre derechos humanos | Constitucional | 177323 | 94 | 99,9 % | 1886,4x |
| 3505 | 36 Nótese que, en la década de del ochenta, la Comisión Europea de Derechos | Constitucional | 177323 | 172 | 99,9 % | 1030,9x |
| 3506 | 36 Para más información, véase «Declaración Universal de Bioética y Derechos | Judicial | 87950 | 87 | 99,9 % | 1010,9x |
| 3507 | 36 Un ejemplo destacable en esta materia es Transparencia Internacional, una | Penal | 178516 | 91 | 99,9 % | 1961,7x |
| 3508 | 36 Vigente el régimen de participación en los gananciales, el eventual crédito es de | Familia | 123490 | 71 | 99,9 % | 1739,3x |
| 3509 | 36 Véase la sentencia de la Corte Suprema, rol 1.275-2020, 12 de noviembre de | Familia | 97488 | 105 | 99,9 % | 928,5x |
| 3510 | 36. CORTE DE APELACIONES DE VALDIVIA, rol N°              49. CORTE SUPREMA, rol Nº 2.275-2008, de veinti- | Familia | 65085 | 78 | 99,9 % | 834,4x |
| 3511 | 36. DÍAZ DE VALDÉS, José Manuel, (2013): ¿Es la Ley Zamudio | Judicial | 81476 | 100 | 99,9 % | 814,8x |
| 3512 | 36. El artículo 2, párrafo 1, del Pacto dispone que se espera | Constitucional | 112823 | 91 | 99,9 % | 1239,8x |
| 3513 | 36. Este capítulo comienza con una introducción que define el | Constitucional | 112823 | 67 | 99,9 % | 1683,9x |
| 3514 | 363   Corte de Apelaciones de Santiago, 25 de noviembre de 2015, Rol Nº 4467/2015; también véase Corte de | Civil | 142015 | 118 | 99,9 % | 1203,5x |
| 3515 | 367   Se exceptúan de esta prohibición los trabajadores que tengan poder para representar al empleador, tales | Laboral | 113458 | 115 | 99,9 % | 986,6x |
| 3516 | 369   ITURRIAGA DELGADO (2016), Camilo, “Los actos de discriminación en las entrevistas de trabajo y la acción | Laboral | 113458 | 104 | 99,9 % | 1090,9x |
| 3517 | 37    Cuadro basado en los textos de PÉREZ MANRÍQUEZ (2007), p. 254 y ss.; American Bar Association (1999) y | Familia | 100107 | 63 | 99,9 % | 1589,0x |
| 3518 | 37 Artículo 6 numeral 2 del Código Orgánico de Tribunales. En dicho numeral ya | Penal | 178516 | 92 | 99,9 % | 1940,4x |
| 3519 | 37 Confrontar con Minagawa (1968: 8), Kelly (2004: 76) y Mariño (2005: 825 y | Constitucional | 177323 | 179 | 99,9 % | 990,6x |
| 3520 | 37 Sentencia Tribunal Constitucional de 17 de enero de 2023, rol ingreso número | Judicial | 144656 | 81 | 99,9 % | 1785,9x |
| 3521 | 37 Terminología que proviene de la analogía con la doctrina de la interpretación | Constitucional | 177323 | 146 | 99,9 % | 1214,5x |
| 3522 | 37 Véase la sección «Ley 21.121, que Modifica el Código Penal y Otras Normas | Penal | 178516 | 109 | 99,9 % | 1637,8x |
| 3523 | 37.   CORTE DE APELACIONES DE VALDIVIA, rol N°            50. CORTE SUPREMA, rol N° 9.155-2009, de veintio- | Familia | 65085 | 85 | 99,9 % | 765,7x |
| 3524 | 37.   CS, rol 3527-98 “Asociación Chilena de Seguridad | Judicial | 105809 | 105 | 99,9 % | 1007,7x |
| 3525 | 37.   ESPEJO, Nicolás y LATHROP, Fabiola | Judicial | 89476 | 111 | 99,9 % | 806,1x |
| 3526 | 37. De conformidad con el artículo 28 de la Declaración | Constitucional | 112823 | 101 | 99,9 % | 1117,1x |
| 3527 | 37. La introducción y el primer párrafo disponen que los | Constitucional | 112823 | 101 | 99,9 % | 1117,1x |
| 3528 | 37. Ley N° 21.676, de 24 de junio de 2024, que extiende plazo para la inscripción del | Familia | 190697 | 197 | 99,9 % | 968,0x |
| 3529 | 37. Plan Nacional de Capacitación (ID 124). Cumplimiento total. En | Constitucional | 177323 | 106 | 99,9 % | 1672,9x |
| 3530 | 37. Si un juez(a) tiene una propiedad en un edificio que cuenta con | Procesal | 94881 | 120 | 99,9 % | 790,7x |
| 3531 | 370                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 163 | 99,9 % | 1926,3x |
| 3532 | 377   TOLEDO CORSI, César (2016), “Análisis crítico de la sanción de las prácticas antisindicales en la Ley Nº | Laboral | 113458 | 98 | 99,9 % | 1157,7x |
| 3533 | 378   Juzgado del Trabajo de Antofagasta, de 27 de mayo de 2010. Esta sentencia fue ratificada por la Corte de | Laboral | 113458 | 89 | 99,9 % | 1274,8x |
| 3534 | 38       Corte IDH. Caso Claude Reyes y otros. Fondo, Reparaciones y Costas. Sentencia del 19 de septiembre de | Administrativo | 89720 | 127 | 99,9 % | 706,5x |
| 3535 | 38   Ver también sentencias de la Excma. Corte Suprema roles N° 3.412-2015, N° 23.587-2015, N° 17.405-2016 y | Judicial | 105809 | 89 | 99,9 % | 1188,9x |
| 3536 | 38 En Corte Suprema, rol 12.564-18, del 16 de agosto de 2018, se señala que «los | Penal | 97633 | 127 | 99,9 % | 768,8x |
| 3537 | 38 Para más información, véase Poder Judicial (2015-2020: 78): «Acto jurídico | Constitucional | 177323 | 97 | 99,9 % | 1828,1x |
| 3538 | 38 Por ejemplo, en Italia, cuando se trata de delitos cometidos por los directivos | Penal | 178516 | 131 | 99,9 % | 1362,7x |
| 3539 | 38 Sentencia de la Corte de Apelaciones de Coihaique, 16 de febrero de 2021, rol | Judicial | 150341 | 81 | 99,9 % | 1856,1x |
| 3540 | 38 Sentencia de la Corte de Apelaciones de San Miguel, rol 278-2020, 31 de julio | Familia | 97488 | 52 | 99,9 % | 1874,8x |
| 3541 | 38 Sentencia de la Corte de Apelaciones de Valdivia, 14 de diciembre de 2021, rol | Judicial | 150341 | 123 | 99,9 % | 1222,3x |
| 3542 | 38 Sobre las diferencias entre el juez y el historiados, véase, Taruffo, 2009a: 336 y | Judicial | 150341 | 104 | 99,9 % | 1445,6x |
| 3543 | 38 Tanta es su habitualidad que tiene normas legales expresas: artículos 199 y 199 | Procesal | 86112 | 55 | 99,9 % | 1565,7x |
| 3544 | 38. El hecho de que un Estado no aplique su legislación | Constitucional | 112823 | 100 | 99,9 % | 1128,2x |
| 3545 | 38. Juan Sarabia Tolosa y otros con Servicio de Sa-      53. Macarena Estay Estay y otro con Ilustre Munici- | Civil | 142015 | 105 | 99,9 % | 1352,5x |
| 3546 | 380. El matiz en la opinión de Somarriva, podría deberse a la pluma de Domínguez Benavente, pues se | Civil | 96458 | 100 | 99,9 % | 964,6x |
| 3547 | 387. Primero, contiene | Penal | 211066 | 135 | 99,9 % | 1563,5x |
| 3548 | 39   Debemos tener presente que no se encuentra amparado por esta clase de acción constitucional el ejercicio | Judicial | 105809 | 104 | 99,9 % | 1017,4x |
| 3549 | 39   Y, en general, como todo contrato de servicios; en este sentido: BRANTT y MEJÍAS (2016), p. 75; RODRÍGUEZ | Civil | 142015 | 72 | 99,9 % | 1972,4x |
| 3550 | 39 Cabe señalar que lo problemático de esto es volver a concepciones subjetivas | Penal | 178516 | 96 | 99,9 % | 1859,5x |
| 3551 | 39 Como los «Lineamientos para la elaboración de indicadores de progreso en | Judicial | 87950 | 94 | 99,9 % | 935,6x |
| 3552 | 39 El 4 de junio de 2001, en el marco de la Asamblea General de la OEA celebrada | Penal | 178516 | 161 | 99,9 % | 1108,8x |
| 3553 | 39 En Corte Suprema, rol 30.252-21, del 2 de agosto de 2021, se establece que «el | Penal | 97633 | 145 | 99,9 % | 673,3x |
| 3554 | 39 En caso de que haya más de un empleador, el tribunal ordenará el pago en los | Familia | 97488 | 104 | 99,9 % | 937,4x |
| 3555 | 39 En virtud del comiso por equivalencia, se permite que, cuando por cualquier | Penal | 178516 | 162 | 99,9 % | 1102,0x |
| 3556 | 39. Decreto N° 182. Reglamento del examen para | Judicial | 89476 | 93 | 99,9 % | 962,1x |
| 3557 | 39. El Comité insta al Estado parte a investigar las denuncias de malos | Judicial | 78893 | 87 | 99,9 % | 906,8x |
| 3558 | 39. En todos los casos y con independencia del país o del | Constitucional | 112823 | 94 | 99,9 % | 1200,2x |
| 3559 | 39. GUASTINI, Riccardo (2013): Distinguendo ancora | Penal | 72395 | 67 | 99,9 % | 1080,5x |
| 3560 | 39. Un juez(a) tiene derecho a actuar para proteger sus derechos e | Procesal | 94881 | 122 | 99,9 % | 777,7x |
| 3561 | 39. división jurídico – legislativa del ministerio secretaría | Judicial | 81476 | 71 | 99,9 % | 1147,5x |
| 3562 | 399 BLANPAIN, Roger (2007), “The European Union”, The Global Workplace, International and Comparative Em- | Laboral | 113458 | 101 | 99,9 % | 1123,3x |
| 3563 | 4   Sobre los múltiples alcances distintos de la voz principios dentro del derecho, véase GAMONAL C., Sergio | Laboral | 113458 | 145 | 99,9 % | 782,5x |
| 3564 | 4 Al respecto, existen opiniones divergentes, véase Vodanovic (1994: 223): «Siendo | Familia | 97488 | 107 | 99,9 % | 911,1x |
| 3565 | 4 Artículo 150 C. «En los casos previstos en los artículos 150 A y 150 B se excluirá | Judicial | 78893 | 105 | 99,9 % | 751,4x |
| 3566 | 4 Artículo 25. Protección Judicial: 1) Toda persona tiene derecho a un recurso | Constitucional | 177323 | 170 | 99,9 % | 1043,1x |
| 3567 | 4 Asimismo, en sentencia Corte Suprema rol 24229-2019, de 30 de octubre de | Judicial | 144656 | 84 | 99,9 % | 1722,1x |
| 3568 | 4 Carbonell (2013: 220) señala que «incluye mecanismos no solamente reactivos | Judicial | 81675 | 101 | 99,9 % | 808,7x |
| 3569 | 4 Compete a la autoridad ambiental determinar si una comu- | Judicial | 134465 | 83 | 99,9 % | 1620,1x |
| 3570 | 4 Dirección del Trabajo, Dictamen Ord. 1654 del 14 de junio de 2021, disponible | Laboral | 98828 | 74 | 99,9 % | 1335,5x |
| 3571 | 4 Entre otros, Jörgensen (1937), Wróblewski (1971), Wellman (1985), Bulygin y | Judicial | 92792 | 83 | 99,9 % | 1118,0x |
| 3572 | 4 Estas expectativas fueron superadas en el año 2021 en que se da cuenta que la | Judicial | 82507 | 92 | 99,9 % | 896,8x |
| 3573 | 4 Este derecho, también conocido como libertad informática, consiste no solo en | Laboral | 98828 | 111 | 99,9 % | 890,3x |
| 3574 | 4 Juzgado de Letras del Trabajo de Chillán, RIT O-118-2009, del 22 de febrero de | Laboral | 98828 | 70 | 99,9 % | 1411,8x |
| 3575 | 4 La crítica fundamental a los modelos comunitarios fue que ellos sirvieron para | Penal | 86906 | 97 | 99,9 % | 895,9x |
| 3576 | 4 La literatura es generosa en ejemplos de duelos judiciales, ordalías o juicios de | Procesal | 86112 | 113 | 99,9 % | 762,1x |
| 3577 | 4 Martorell (2007: 246) expresa que al considerar que el consumo sea «próximo | Penal | 97633 | 105 | 99,9 % | 929,8x |
| 3578 | 4 Mañalich (2004a: 348), Navarro (2005: 266), Marcazzolo (2009: 93), González | Penal | 97633 | 63 | 99,9 % | 1549,7x |
| 3579 | 4 Mensaje de S. E. la presidenta de la República 1055-362 del 29 de diciembre de | Laboral | 74025 | 78 | 99,9 % | 949,0x |
| 3580 | 4 Para los detalles de la discusión parlamentaria en relación con este artículo, se | Penal | 86906 | 105 | 99,9 % | 827,7x |
| 3581 | 4 Para más información, véase «Norma sobre seguridad de paciente y calidad de | Judicial | 87950 | 68 | 99,9 % | 1293,4x |
| 3582 | 4 Piénsese en quien, mientras desempeña sus funciones en un establecimiento | Penal | 178516 | 141 | 99,9 % | 1266,1x |
| 3583 | 4 Sentencia de la Corte de Apelaciones de Santiago, rol 9.341-2006, 30 de marzo | Penal | 178516 | 197 | 99,9 % | 906,2x |
| 3584 | 4 Sentencia del caso López con Latam Airlines Goup S. A., Corte de Apelaciones | Laboral | 74025 | 62 | 99,9 % | 1194,0x |
| 3585 | 4 Véase la sentencia de la Corte Suprema en Recurso de casación en el fondo, 7 | Familia | 123490 | 176 | 99,9 % | 701,6x |
| 3586 | 4.    ALEXY, Robert (2002), “Epílogo a la teoría de los     14. ARREDONDO PACHECO, Jorge (2014), “La llega- | Laboral | 113458 | 109 | 99,9 % | 1040,9x |
| 3587 | 4.    BERTELSEN R., Raúl (1987): “El Estado empresario | Judicial | 105809 | 84 | 99,9 % | 1259,6x |
| 3588 | 4.    Benítez Piraíno, Dinka. 2018. Filiación y mujeres | Judicial | 93914 | 102 | 99,9 % | 920,7x |
| 3589 | 4.    Corte de Apelaciones de Concepción, rol N° 190- | Familia | 100107 | 84 | 99,9 % | 1191,8x |
| 3590 | 4.    Requerimiento de inaplicabilidad por inconstitucionalidad presentado por | Familia | 95131 | 101 | 99,9 % | 941,9x |
| 3591 | 4.    Requerimiento de inconstitucionalidad presentado respecto del proyecto de | Constitucional | 121906 | 80 | 99,9 % | 1523,8x |
| 3592 | 4. A falta de estipulación en el contrato o de normas especiales, sean ajenas al Código | Civil | 120848 | 107 | 99,9 % | 1129,4x |
| 3593 | 4. A los fines de la extradición entre Estados parte, se considerará que | Judicial | 78893 | 96 | 99,9 % | 821,8x |
| 3594 | 4. Abrir y cerrar las sesiones del tribunal, anticipar o prorrogar las horas | Procesal | 66012 | 84 | 99,9 % | 785,9x |
| 3595 | 4. Acceso al conocimiento, la 1. Igualdad de oportunidades en | Judicial | 82507 | 67 | 99,9 % | 1231,4x |
| 3596 | 4. Acogiendo, receptando o protegiendo habitualmente a los malhe- | Penal | 194788 | 120 | 99,9 % | 1623,2x |
| 3597 | 4. Alcoholismo o drogadicción que constituya un impedimento grave para la | Familia | 190697 | 154 | 99,9 % | 1238,3x |
| 3598 | 4. Asegurar la puntualidad en el inicio de las audiencias. Se estima | Constitucional | 177323 | 107 | 99,9 % | 1657,2x |
| 3599 | 4. Boletín N° 10.911-04. Proyecto de ley que establece un régimen | Judicial | 89476 | 98 | 99,9 % | 913,0x |
| 3600 | 4. Cabe recordar a los jueces y juezas que el Poder Judicial cuenta con | Constitucional | 177323 | 117 | 99,9 % | 1515,6x |
| 3601 | 4. Capacitación: para los efectos de la presente Política se entenderá | Judicial | 81476 | 109 | 99,9 % | 747,5x |
| 3602 | 4. Caracterización del case management en los | Procesal | 96699 | 91 | 99,9 % | 1062,6x |
| 3603 | 4. Con el objeto de facilitar la resolución de las cuestiones | Constitucional | 112823 | 94 | 99,9 % | 1200,2x |
| 3604 | 4. Considerar la posibilidad de brindar un ajuste razonable | Judicial | 81476 | 94 | 99,9 % | 866,8x |
| 3605 | 4. Corte Interamericana de Derechos Humanos. Cuadernillos de | Judicial | 87237 | 74 | 99,9 % | 1178,9x |
| 3606 | 4. Creación de la Comisión de Transparencia e Información | Administrativo | 89720 | 104 | 99,9 % | 862,7x |
| 3607 | 4. Cuando el retorno no sea posible, tal como | Judicial | 134465 | 92 | 99,9 % | 1461,6x |
| 3608 | 4. Cuando el retorno no sea posible, tal como se determine por acuerdo | Judicial | 134465 | 107 | 99,9 % | 1256,7x |
| 3609 | 4. Cuando se señalan al delito copulativamente penas comprendidas en | Penal | 194788 | 126 | 99,9 % | 1545,9x |
| 3610 | 4. Cumplimiento de Acuerdo de Solución Amistosa caso César Pe- | Constitucional | 177323 | 141 | 99,9 % | 1257,6x |
| 3611 | 4. Deberá prestarse especial atención a la creación | Judicial | 134465 | 81 | 99,9 % | 1660,1x |
| 3612 | 4. Decretos económicos, facultades disciplinarias de jueces y | Laboral | 71986 | 74 | 99,9 % | 972,8x |
| 3613 | 4. Derecho a la salud (párr. 7) • Universalización del derecho | Judicial | 82507 | 117 | 99,9 % | 705,2x |
| 3614 | 4. Derechos de las personas migrantes | Constitucional | 115835 | 66 | 99,9 % | 1755,1x |
| 3615 | 4. Desconocimiento del Modelo de Prevención y falta de actividades | Constitucional | 112823 | 92 | 99,9 % | 1226,3x |
| 3616 | 4. Determinar un régimen provisorio de | Familia | 95131 | 75 | 99,9 % | 1268,4x |
| 3617 | 4. Disponer que los recursos del fondo de reserva se mantengan en depósito en una | Civil | 192585 | 109 | 99,9 % | 1766,8x |
| 3618 | 4. Ejecutarlo en     El sentido del/a legislador/a al momento de consagrar | Familia | 95131 | 110 | 99,9 % | 864,8x |
| 3619 | 4. El Estado debe realizar un acto público de reconocimiento de | Judicial | 87237 | 128 | 99,9 % | 681,5x |
| 3620 | 4. El Estado es responsable de la violación de los artículos 11 N° 2 | Judicial | 87237 | 119 | 99,9 % | 733,1x |
| 3621 | 4. El comportamiento demostrado con anterioridad y posterioridad a | Penal | 194788 | 189 | 99,9 % | 1030,6x |
| 3622 | 4. El comportamiento demostrado con anterioridad y posterioridad a la | Penal | 194788 | 205 | 99,9 % | 950,2x |
| 3623 | 4. El deber de información previsto en el artículo 12 del Reglamento (UE) 2017/679 se entenderá cumplido | Constitucional | 104063 | 126 | 99,9 % | 825,9x |
| 3624 | 4. El ejercicio de los derechos reconocidos en el inciso 1 puede asimismo ser restringido por la ley, en zonas | Constitucional | 115835 | 150 | 99,9 % | 772,2x |
| 3625 | 4. El establecimiento de métodos para la aplicación efectiva del mo- | Penal | 178516 | 162 | 99,9 % | 1102,0x |
| 3626 | 4. El padre biológico de FFFF, cuya filiación no es desconocida | Judicial | 93914 | 76 | 99,9 % | 1235,7x |
| 3627 | 4. Empalme de la Presidenta, Vicepresidenta, Vocal 1, Fiscal 1 | Judicial | 79146 | 101 | 99,9 % | 783,6x |
| 3628 | 4. En casos más graves, que no sea derechamente otra forma de | Familia | 95131 | 88 | 99,9 % | 1081,0x |
| 3629 | 4. En las asambleas extraordinarias, entre la primera y segunda citación deberá mediar un | Civil | 192585 | 166 | 99,9 % | 1160,2x |
| 3630 | 4. En materia laboral, el principio de vinculación directa implicará | Laboral | 113458 | 114 | 99,9 % | 995,2x |
| 3631 | 4. Esta acción se tramitará como incidente, ante el juez con competencia en asuntos | Familia | 81198 | 98 | 99,9 % | 828,6x |
| 3632 | 4. Evaluación del Programa de Reparación y Atención Integral de | Constitucional | 177323 | 132 | 99,9 % | 1343,4x |
| 3633 | 4. Exigibilidad personal: la medida debe afectar al menor número | Laboral | 113458 | 59 | 99,9 % | 1923,0x |
| 3634 | 4. Finalmente, debe tenerse presente que no existe aún una solución | Penal | 194788 | 175 | 99,9 % | 1113,1x |
| 3635 | 4. Finalmente, un fuerte sentido patriótico que ha caracterizado a | Penal | 178516 | 159 | 99,9 % | 1122,7x |
| 3636 | 4. Garantizar la accesibilidad, eliminando no solo las barreras | Judicial | 81476 | 89 | 99,9 % | 915,5x |
| 3637 | 4. Identificar las manifestaciones sexistas que se presentan en el caso | Familia | 100107 | 120 | 99,9 % | 834,2x |
| 3638 | 4. Impugnación de la legalidad de la privación de libertad. La garantía | Penal | 86906 | 91 | 99,9 % | 955,0x |
| 3639 | 4. Incongruencia entre la “plena capacidad de la mujer casada” y los resabios de la | Familia | 190697 | 175 | 99,9 % | 1089,7x |
| 3640 | 4. Irretroactividad ratione personae. Nadie puede ser perseguido por | Penal | 121924 | 68 | 99,9 % | 1793,0x |
| 3641 | 4. La condición negativa y suspensiva moralmente imposible o concebida en términos | Civil | 118177 | 85 | 99,9 % | 1390,3x |
| 3642 | 4. La creación de una institucionalidad propuesta por la ministra | Judicial | 81476 | 104 | 99,9 % | 783,4x |
| 3643 | 4. La forma de entender el principio de igualdad por parte del TC | Judicial | 81476 | 81 | 99,9 % | 1005,9x |
| 3644 | 4. La igualdad ante la ley e igual protección de la ley en el ejercicio | Judicial | 89476 | 79 | 99,9 % | 1132,6x |
| 3645 | 4. La libre investigación de la | Familia | 65085 | 41 | 99,9 % | 1587,4x |
| 3646 | 4. La prestación de tales servicios de salud deberá coordinarse con | Judicial | 89476 | 59 | 99,9 % | 1516,5x |
| 3647 | 4. Las actas firmadas por las partes, y autorizadas por los inspectores | Laboral | 100583 | 97 | 99,9 % | 1036,9x |
| 3648 | 4. Las sentencias. Una primera sentencia de la Corte Suprema, de | Civil | 142015 | 123 | 99,9 % | 1154,6x |
| 3649 | 4. Los Estados Partes deben tomar medidas apropiadas para asegurar | Judicial | 89476 | 111 | 99,9 % | 806,1x |
| 3650 | 4. Los Estados Partes en el presente pacto tomarán las medidas | Judicial | 89476 | 98 | 99,9 % | 913,0x |
| 3651 | 4. Los actos preventivos, previos o preparatorios de un estado de | Penal | 121924 | 114 | 99,9 % | 1069,5x |
| 3652 | 4. Los acuerdos deben respetar los derechos conferidos por las | Familia | 100107 | 114 | 99,9 % | 878,1x |
| 3653 | 4. Los principios generales del derecho se aplicarán en defecto de ley o costumbre, sin | General | 129559 | 169 | 99,9 % | 766,6x |
| 3654 | 4. Muñoz León, Fernando. “Estándares conceptuales y cargas proce- | Judicial | 87237 | 106 | 99,9 % | 823,0x |
| 3655 | 4. Otro significado concierne a los contratos innominados, en cuanto faculta a las partes a | Civil | 110175 | 92 | 99,9 % | 1197,6x |
| 3656 | 4. Participación de las personas de edad | Judicial | 82507 | 63 | 99,9 % | 1309,6x |
| 3657 | 4. Participación en Comité Interministerial para el Plan de Acción | Constitucional | 177323 | 152 | 99,9 % | 1166,6x |
| 3658 | 4. Piezas que deben ser notificadas (resoluciones anteriores, solicitud | Judicial | 89450 | 67 | 99,9 % | 1335,1x |
| 3659 | 4. Procedimiento relativo a actos judiciales no contenciosos. Los ac- | Familia | 97488 | 139 | 99,9 % | 701,4x |
| 3660 | 4. Proceso activo | Judicial | 53521 | 80 | 99,9 % | 669,0x |
| 3661 | 4. Procurar en la medida de lo posible, auxiliarse con un equipo | Judicial | 81476 | 55 | 99,9 % | 1481,4x |
| 3662 | 4. Promover la articulación con otras instancias al interior del Poder | Judicial | 81476 | 83 | 99,9 % | 981,6x |
| 3663 | 4. Promover la mediación de oficio o a petición de parte, sólo en las | Familia | 100107 | 78 | 99,9 % | 1283,4x |
| 3664 | 4. Promover las oportunidades en favor del derecho | Familia | 100107 | 83 | 99,9 % | 1206,1x |
| 3665 | 4. Que a fojas 21 rola una copia del Reglamento de Uso de Bienes y Servicios Comunes – | Civil | 192585 | 124 | 99,9 % | 1553,1x |
| 3666 | 4. Que el administrador obtenga el acuerdo previo del Comité de Administración, el que | Civil | 192585 | 170 | 99,9 % | 1132,9x |
| 3667 | 4. Que en la resolución hayan influido de modo esencial documentos | Judicial | 144656 | 166 | 99,9 % | 871,4x |
| 3668 | 4. Que la persona a quien deba notificarse se encuentre en el lugar | Judicial | 89450 | 115 | 99,9 % | 777,8x |
| 3669 | 4. Que por su parte, la sentencia rechazó el otorgamiento de la libertad | Penal | 194788 | 169 | 99,9 % | 1152,6x |
| 3670 | 4. Que, además de lo anterior, y en relación a la restricción contempla- | Penal | 194788 | 197 | 99,9 % | 988,8x |
| 3671 | 4. Que, de este modo, la decisión impugnada se aparta del mandato | Judicial | 144656 | 154 | 99,9 % | 939,3x |
| 3672 | 4. Que, en consecuencia, lo que se plantea a esta Corte, es un proble- | Penal | 194788 | 148 | 99,9 % | 1316,1x |
| 3673 | 4. Que, en el caso de que la parte reclame de la nulidad, sea por no | Judicial | 89450 | 130 | 99,9 % | 688,1x |
| 3674 | 4. R.W. Connell | Judicial | 87237 | 119 | 99,9 % | 733,1x |
| 3675 | 4. Rechazos o revocación de visas, medidas de | Constitucional | 115835 | 128 | 99,9 % | 905,0x |
| 3676 | 4. Refieren a la ratificación de los Protocolos I y II de 1977 que complementan las Convenciones, ampliando | Penal | 121924 | 102 | 99,9 % | 1195,3x |
| 3677 | 4. Resoluciones y Circulares | Civil | 192585 | 150 | 99,9 % | 1283,9x |
| 3678 | 4. Salvo en el caso en que prevalezca un texto determinado conforme a lo previsto en el párrafo 1, cuand o | Judicial | 134465 | 114 | 99,9 % | 1179,5x |
| 3679 | 4. Servicios al usuario, donde la máquina aprende el lenguaje | Judicial | 83934 | 87 | 99,9 % | 964,8x |
| 3680 | 4. Supervisión y certificación del sistema de prevención de los | Penal | 119528 | 106 | 99,9 % | 1127,6x |
| 3681 | 4. Síntesis comparativa entre los modelos de case | Procesal | 96699 | 55 | 99,9 % | 1758,2x |
| 3682 | 4. Sólo en el caso de la condena, el tribunal deberá resolver sobre | Penal | 211066 | 126 | 99,9 % | 1675,1x |
| 3683 | 4. Tabla N° 4 Tipos o manifestaciones de maltrato infantil | Familia | 95131 | 119 | 99,9 % | 799,4x |
| 3684 | 4. Un juez(a) debe comportarse en público con la sensibilidad y | Procesal | 94881 | 91 | 99,9 % | 1042,6x |
| 3685 | 4. Verificar y perfeccionar las condiciones de la privación de libertad | Constitucional | 177323 | 157 | 99,9 % | 1129,4x |
| 3686 | 4. j | Familia | 100107 | 132 | 99,9 % | 758,4x |
| 3687 | 4.1           Jueces | Familia | 100107 | 67 | 99,9 % | 1494,1x |
| 3688 | 4.1           Presentación | Constitucional | 121906 | 89 | 99,9 % | 1369,7x |
| 3689 | 4.1           Reglas | Familia | 65085 | 67 | 99,9 % | 971,4x |
| 3690 | 4.1     Descripción general del sistema de sanciones | Penal | 119528 | 84 | 99,9 % | 1423,0x |
| 3691 | 4.1. Concepto. 4.2. Casos de obligaciones naturales. 4.3. Efectos de las obligaciones | Civil | 118177 | 175 | 99,9 % | 675,3x |
| 3692 | 4.1.1 Características del procedimiento | Familia | 95131 | 81 | 99,9 % | 1174,5x |
| 3693 | 4.1.1 Del control ético a la responsabilidad | Judicial | 54457 | 74 | 99,9 % | 735,9x |
| 3694 | 4.1.1 El acceso a la justicia | Judicial | 81476 | 93 | 99,9 % | 876,1x |
| 3695 | 4.1.1 Evolución jurisprudencial en el | Penal | 121924 | 98 | 99,9 % | 1244,1x |
| 3696 | 4.1.1 Integrantes | Laboral | 71986 | 105 | 99,9 % | 685,6x |
| 3697 | 4.1.1 Litigio entre actores no estatales y Estados | Constitucional | 112823 | 96 | 99,9 % | 1175,2x |
| 3698 | 4.1.1 Los Principios de Bangalore | Procesal | 94881 | 117 | 99,9 % | 810,9x |
| 3699 | 4.1.1.1 Caso Thabametsi, Earthlife Africa Johannesburg203 | Constitucional | 112823 | 88 | 99,9 % | 1282,1x |
| 3700 | 4.1.1.1 Independencia | Procesal | 94881 | 84 | 99,9 % | 1129,5x |
| 3701 | 4.1.1.1 Protocolo de acceso a la justicia | Judicial | 81476 | 59 | 99,9 % | 1380,9x |
| 3702 | 4.1.1.2 Caso del Aeropuerto de Viena, Austria206 | Constitucional | 112823 | 91 | 99,9 % | 1239,8x |
| 3703 | 4.1.1.2 Imparcialidad | Procesal | 94881 | 78 | 99,9 % | 1216,4x |
| 3704 | 4.1.1.2 Protocolo de acceso a la justicia | Judicial | 81476 | 83 | 99,9 % | 981,6x |
| 3705 | 4.1.1.3 Generaciones Futuras contra | Constitucional | 112823 | 71 | 99,9 % | 1589,1x |
| 3706 | 4.1.1.3 Protocolo de acceso a la justicia de | Judicial | 81476 | 66 | 99,9 % | 1234,5x |
| 3707 | 4.1.1.4 Caso Holanda con Urgenda211 | Constitucional | 112823 | 106 | 99,9 % | 1064,4x |
| 3708 | 4.1.1.4 Corrección | Procesal | 94881 | 59 | 99,9 % | 1608,2x |
| 3709 | 4.1.1.4 Protocolo de acceso a la justicia de grupos | Judicial | 81476 | 58 | 99,9 % | 1404,8x |
| 3710 | 4.1.1.5 Caso Carvalho y otros contra Unión Europea215 | Constitucional | 112823 | 96 | 99,9 % | 1175,2x |
| 3711 | 4.1.1.5 Equidad | Procesal | 101194 | 55 | 99,9 % | 1839,9x |
| 3712 | 4.1.1.6 Competencia y diligencia | Procesal | 101194 | 54 | 99,9 % | 1874,0x |
| 3713 | 4.1.2 Código Iberoamericano de Ética Judicial | Procesal | 94881 | 109 | 99,9 % | 870,5x |
| 3714 | 4.1.2 Estructura del procedimiento | Familia | 95131 | 104 | 99,9 % | 914,7x |
| 3715 | 4.1.2 Evolución jurisprudencial en el | Penal | 121924 | 104 | 99,9 % | 1172,3x |
| 3716 | 4.1.2 La interpretación evolutiva | Judicial | 134465 | 96 | 99,9 % | 1400,7x |
| 3717 | 4.1.2 Liquidación Refleja | Judicial | 64632 | 71 | 99,9 % | 910,3x |
| 3718 | 4.1.2 Litigios contra empresas: Carbon Majors | Constitucional | 112823 | 85 | 99,9 % | 1327,3x |
| 3719 | 4.1.2 Pacto Internacional de Derechos Civiles y Políticos | Laboral | 100583 | 78 | 99,9 % | 1289,5x |
| 3720 | 4.1.2.1 Clasificación funcional | Judicial | 79146 | 89 | 99,9 % | 889,3x |
| 3721 | 4.1.2.1 Independencia | Procesal | 94881 | 114 | 99,9 % | 832,3x |
| 3722 | 4.1.2.1 La prescriptibilidad de las acciones | Penal | 121924 | 119 | 99,9 % | 1024,6x |
| 3723 | 4.1.2.10 Secreto profesional | Procesal | 94881 | 78 | 99,9 % | 1216,4x |
| 3724 | 4.1.2.11 Apertura de buzón de sugerencias, reclamos y | Laboral | 71986 | 65 | 99,9 % | 1107,5x |
| 3725 | 4.1.2.12 Notificaciones | Laboral | 71986 | 74 | 99,9 % | 972,8x |
| 3726 | 4.1.2.14 Chequear diariamente el encendido y apagado | Laboral | 71986 | 106 | 99,9 % | 679,1x |
| 3727 | 4.1.2.2 Clasificación según finalidad | Judicial | 79146 | 92 | 99,9 % | 860,3x |
| 3728 | 4.1.2.2 Imparcialidad | Procesal | 101194 | 106 | 99,9 % | 954,7x |
| 3729 | 4.1.2.2 La imprescriptibilidad integral de las | Penal | 121924 | 119 | 99,9 % | 1024,6x |
| 3730 | 4.1.2.3 Clasificación según grado de formalidad | Judicial | 79146 | 94 | 99,9 % | 842,0x |
| 3731 | 4.1.2.3 Entregar información atingente a su jurisdicción | Laboral | 71986 | 98 | 99,9 % | 734,6x |
| 3732 | 4.1.2.3 Motivación | Procesal | 94881 | 105 | 99,9 % | 903,6x |
| 3733 | 4.1.2.4 Conocimiento y capacitación | Procesal | 94881 | 114 | 99,9 % | 832,3x |
| 3734 | 4.1.2.4 El informe de investigación | Judicial | 79146 | 89 | 99,9 % | 889,3x |
| 3735 | 4.1.2.4 Recibir documentación y despacho de | Laboral | 71986 | 92 | 99,9 % | 782,5x |
| 3736 | 4.1.2.5 Atender los llamados telefónicos y canalizarlos a | Laboral | 71986 | 101 | 99,9 % | 712,7x |
| 3737 | 4.1.2.6 Responsabilidad institucional | Procesal | 94881 | 62 | 99,9 % | 1530,3x |
| 3738 | 4.1.2.8 Integridad | Procesal | 94881 | 66 | 99,9 % | 1437,6x |
| 3739 | 4.1.2.8 Publicar la información de las audiencias diarias | Laboral | 71986 | 98 | 99,9 % | 734,6x |
| 3740 | 4.1.2.9 Entregar copias de resoluciones, oficios, actas de | Laboral | 71986 | 106 | 99,9 % | 679,1x |
| 3741 | 4.1.2.9 Transparencia | Procesal | 94881 | 76 | 99,9 % | 1248,4x |
| 3742 | 4.1.3 Convención Americana de Derechos | Laboral | 100583 | 100 | 99,9 % | 1005,8x |
| 3743 | 4.1.3 Estructuras de un informe | Judicial | 79146 | 49 | 99,9 % | 1615,2x |
| 3744 | 4.1.3.1 La primera acogida | Familia | 95131 | 59 | 99,9 % | 1612,4x |
| 3745 | 4.1.3.2 Tramitación de la solicitud | Judicial | 64632 | 92 | 99,9 % | 702,5x |
| 3746 | 4.1.5   Adecuaciones dispuestas por el Acta 103-2018 sobre acoso sexual                 131 | Judicial | 54457 | 65 | 99,9 % | 837,8x |
| 3747 | 4.1.5 Audiencia preliminar o cautelar | Familia | 95131 | 102 | 99,9 % | 932,7x |
| 3748 | 4.1.5 Declaración Universal de los | Laboral | 100583 | 74 | 99,9 % | 1359,2x |
| 3749 | 4.1.5.1 Habilidades y recursos a desplegar | Familia | 95131 | 92 | 99,9 % | 1034,0x |
| 3750 | 4.1.5.2 Relevancia de esta audiencia | Familia | 95131 | 101 | 99,9 % | 941,9x |
| 3751 | 4.1.6.1 La discusión | Familia | 95131 | 96 | 99,9 % | 990,9x |
| 3752 | 4.1.6.2 La prueba | Familia | 95131 | 111 | 99,9 % | 857,0x |
| 3753 | 4.1.7 Potestad cautelar | Familia | 95131 | 113 | 99,9 % | 841,9x |
| 3754 | 4.1.7.1 Factores de riesgo desde el ámbito psicosocial | Familia | 95131 | 111 | 99,9 % | 857,0x |
| 3755 | 4.1.8 Término del procedimiento de violencia | Familia | 95131 | 117 | 99,9 % | 813,1x |
| 3756 | 4.2                 Campo de aplicación de la pena de acuerdo | Penal | 119528 | 93 | 99,9 % | 1285,2x |
| 3757 | 4.2     Dispositivos electrónicos: firma | Judicial | 52128 | 57 | 99,9 % | 914,5x |
| 3758 | 4.2 Acceso a la justicia de personas trans. Diferentes miradas desde las diversas funciones de | Judicial | 93914 | 91 | 99,9 % | 1032,0x |
| 3759 | 4.2. Demanda civil interpuesta ante el juez civil: en este caso, la acción podrá | Civil | 96458 | 117 | 99,9 % | 824,4x |
| 3760 | 4.2.1 Audiencia de juicio oral y de | Penal | 57066 | 80 | 99,9 % | 713,3x |
| 3761 | 4.2.1 Concepto | Judicial | 79146 | 84 | 99,9 % | 942,2x |
| 3762 | 4.2.1 Conceptos fundamentales de los tratados vigentes | Constitucional | 121906 | 100 | 99,9 % | 1219,1x |
| 3763 | 4.2.1 Constitución Política de la República de Chile | Procesal | 94881 | 68 | 99,9 % | 1395,3x |
| 3764 | 4.2.1 Definición | Laboral | 100583 | 79 | 99,9 % | 1273,2x |
| 3765 | 4.2.1 Designación de Ministra de la Excma. Corte | Judicial | 81476 | 55 | 99,9 % | 1481,4x |
| 3766 | 4.2.1 Designación de Ministra de la Excma. Corte Suprema encargada de los asuntos de género | Judicial | 81476 | 59 | 99,9 % | 1380,9x |
| 3767 | 4.2.1 El consentimiento del interesado | Constitucional | 104063 | 88 | 99,9 % | 1182,5x |
| 3768 | 4.2.1 Identidad de los contratantes | Judicial | 96536 | 92 | 99,9 % | 1049,3x |
| 3769 | 4.2.1 La visión de los organismos | Constitucional | 112823 | 81 | 99,9 % | 1392,9x |
| 3770 | 4.2.1 La víctima: el proceso penal en hipótesis de | Familia | 95131 | 68 | 99,9 % | 1399,0x |
| 3771 | 4.2.1 Protocolo de Atención de Usuarios | Laboral | 71986 | 92 | 99,9 % | 782,5x |
| 3772 | 4.2.1 Reconocimiento legal y su noción | Civil | 142015 | 78 | 99,9 % | 1820,7x |
| 3773 | 4.2.1.1 Discapacidad | Constitucional | 121906 | 101 | 99,9 % | 1207,0x |
| 3774 | 4.2.1.3 Ajustes razonables | Constitucional | 121906 | 89 | 99,9 % | 1369,7x |
| 3775 | 4.2.2   Integridad y autenticidad del documento                                                            144 | Judicial | 96536 | 50 | 99,9 % | 1930,7x |
| 3776 | 4.2.2 Código Orgánico de Tribunales | Procesal | 94881 | 63 | 99,9 % | 1506,0x |
| 3777 | 4.2.2 Efectos respecto de las obligaciones | Judicial | 64632 | 92 | 99,9 % | 702,5x |
| 3778 | 4.2.2 Elementos | Laboral | 100583 | 62 | 99,9 % | 1622,3x |
| 3779 | 4.2.2 Estructura | Judicial | 79146 | 88 | 99,9 % | 899,4x |
| 3780 | 4.2.2 Integridad y autenticidad del documento | Judicial | 96536 | 106 | 99,9 % | 910,7x |
| 3781 | 4.2.2 La autorización legal como legitimante | Constitucional | 104063 | 104 | 99,9 % | 1000,6x |
| 3782 | 4.2.2 Protocolo de Atención de Usuarios | Laboral | 71986 | 83 | 99,9 % | 867,3x |
| 3783 | 4.2.2 Resultados del Estudio Diagnóstico de | Judicial | 81476 | 81 | 99,9 % | 1005,9x |
| 3784 | 4.2.2 Situaciones observadas desde la sociedad civil | Constitucional | 112823 | 72 | 99,9 % | 1567,0x |
| 3785 | 4.2.2.1 Deber de residencia | Procesal | 94881 | 101 | 99,9 % | 939,4x |
| 3786 | 4.2.2.1 El inicio del procedimiento penal | Familia | 95131 | 115 | 99,9 % | 827,2x |
| 3787 | 4.2.2.1 Suspensión de los contratos a través | Constitucional | 112823 | 87 | 99,9 % | 1296,8x |
| 3788 | 4.2.2.2 Afectación de las condiciones | Constitucional | 112823 | 83 | 99,9 % | 1359,3x |
| 3789 | 4.2.2.2 Deber de asistencia | Procesal | 94881 | 120 | 99,9 % | 790,7x |
| 3790 | 4.2.2.2 La investigación del Ministerio | Familia | 95131 | 105 | 99,9 % | 906,0x |
| 3791 | 4.2.2.3 Condiciones sanitarias | Constitucional | 112823 | 78 | 99,9 % | 1446,4x |
| 3792 | 4.2.2.3 La investigación del Ministerio | Familia | 95131 | 84 | 99,9 % | 1132,5x |
| 3793 | 4.2.2.3 La investigación del Ministerio Público: el | Familia | 95131 | 87 | 99,9 % | 1093,5x |
| 3794 | 4.2.2.3 Obligación de despacho y fallo | Procesal | 94881 | 117 | 99,9 % | 810,9x |
| 3795 | 4.2.2.4 La víctima en la etapa de juicio oral | Familia | 95131 | 107 | 99,9 % | 889,1x |
| 3796 | 4.2.2.4 Prohibición de ejercicio profesional | Procesal | 94881 | 102 | 99,9 % | 930,2x |
| 3797 | 4.2.2.4 Subcontratistas, trabajo precario e | Constitucional | 112823 | 85 | 99,9 % | 1327,3x |
| 3798 | 4.2.2.5 Prohibición de ejercicio como árbitro | Procesal | 94881 | 105 | 99,9 % | 903,6x |
| 3799 | 4.2.2.6 Prohibición de opinión y alegaciones privadas | Procesal | 94881 | 79 | 99,9 % | 1201,0x |
| 3800 | 4.2.2.7 Prohibición de adquisición de bienes | Procesal | 94881 | 139 | 99,9 % | 682,6x |
| 3801 | 4.2.2.8 Inhabilidades por parcialidad | Procesal | 101194 | 127 | 99,9 % | 796,8x |
| 3802 | 4.2.2.9 Diferencias entre implicancias y recusaciones | Procesal | 101194 | 130 | 99,9 % | 778,4x |
| 3803 | 4.2.3 El interés legítimo como “legitimante” | Constitucional | 104063 | 118 | 99,9 % | 881,9x |
| 3804 | 4.2.3 Ley sobre Probidad en la función pública | Procesal | 94881 | 101 | 99,9 % | 939,4x |
| 3805 | 4.2.3 Prevención sobre la certidumbre | Civil | 142015 | 100 | 99,9 % | 1420,2x |
| 3806 | 4.2.3 Secretaría Técnica de igualdad | Judicial | 81476 | 80 | 99,9 % | 1018,5x |
| 3807 | 4.2.3 Sujetos activos de las prácticas antisindicales | Laboral | 100583 | 59 | 99,9 % | 1704,8x |
| 3808 | 4.2.3.1 Consulta | Judicial | 79146 | 113 | 99,9 % | 700,4x |
| 3809 | 4.2.3.2 Informe | Judicial | 79146 | 48 | 99,9 % | 1648,9x |
| 3810 | 4.2.4 La normativa de la Corte Suprema | Procesal | 94881 | 67 | 99,9 % | 1416,1x |
| 3811 | 4.2.4 Política de igualdad de género y no | Judicial | 81476 | 85 | 99,9 % | 958,5x |
| 3812 | 4.2.4 Sujetos pasivos de las prácticas antisindicales | Laboral | 100583 | 118 | 99,9 % | 852,4x |
| 3813 | 4.2.4.1 Objetivo | Judicial | 81476 | 57 | 99,9 % | 1429,4x |
| 3814 | 4.2.5 Institucionalidad vigente y Creación | Judicial | 81476 | 54 | 99,9 % | 1508,8x |
| 3815 | 4.2.5 Sanciones | Procesal | 101194 | 67 | 99,9 % | 1510,4x |
| 3816 | 4.2.5.1 De acuerdo a lo dispuesto en el artículo 486 inciso | Laboral | 100583 | 115 | 99,9 % | 874,6x |
| 3817 | 4.2.6 Conductas sancionadas por la | Laboral | 100583 | 110 | 99,9 % | 914,4x |
| 3818 | 4.2.7 El despido antisindical | Laboral | 100583 | 130 | 99,9 % | 773,7x |
| 3819 | 4.2.7 Protocolo de actuación para la atención en | Judicial | 81476 | 89 | 99,9 % | 915,5x |
| 3820 | 4.2.7.1 Estructura del Protocolo | Judicial | 81476 | 57 | 99,9 % | 1429,4x |
| 3821 | 4.2.7.2 Recomendaciones de interés | Judicial | 81476 | 70 | 99,9 % | 1163,9x |
| 3822 | 4.2.8 Condicionantes de género en la | Judicial | 81476 | 96 | 99,9 % | 848,7x |
| 3823 | 4.2.8 Condicionantes de género en la movilidad y ascensos a los cargos de mayor jerarquía | Judicial | 81476 | 52 | 99,9 % | 1566,8x |
| 3824 | 4.2.8 Registro de la sanción por prácticas antisindicales | Laboral | 100583 | 115 | 99,9 % | 874,6x |
| 3825 | 4.2.9.1 Plazo de interposición: “La denuncia a que se refieren | Laboral | 100583 | 91 | 99,9 % | 1105,3x |
| 3826 | 4.2.9.2 Contenido de la sentencia: según el artículo 495 del Có- | Laboral | 100583 | 124 | 99,9 % | 811,2x |
| 3827 | 4.3               Extinción de la responsabilidad penaly reglas | Penal | 119528 | 61 | 99,9 % | 1959,5x |
| 3828 | 4.3          Posesión | Familia | 65085 | 74 | 99,9 % | 879,5x |
| 3829 | 4.3   Estado de cumplimiento de la sentencia | Judicial | 87237 | 59 | 99,9 % | 1478,6x |
| 3830 | 4.3   Juez o jueza | Familia | 100107 | 61 | 99,9 % | 1641,1x |
| 3831 | 4.3.1 Agua potable Osorno | Constitucional | 112823 | 102 | 99,9 % | 1106,1x |
| 3832 | 4.3.1 Deber de notificación y Registro | Constitucional | 104063 | 97 | 99,9 % | 1072,8x |
| 3833 | 4.3.1 Imprescriptibilidad de la acción penal | Penal | 121924 | 94 | 99,9 % | 1297,1x |
| 3834 | 4.3.1 Reconocimiento legal y noción | Civil | 142015 | 104 | 99,9 % | 1365,5x |
| 3835 | 4.3.2 Aplicación de la media de prescripción | Penal | 121924 | 92 | 99,9 % | 1325,3x |
| 3836 | 4.3.2 Deber de información | Constitucional | 104063 | 84 | 99,9 % | 1238,8x |
| 3837 | 4.3.2 Decretos y reglamentos | Constitucional | 121906 | 63 | 99,9 % | 1935,0x |
| 3838 | 4.3.2 Lucro cesante y lesión al interés | Civil | 142015 | 101 | 99,9 % | 1406,1x |
| 3839 | 4.3.2 Objeción e impugnación de créditos | Judicial | 64632 | 68 | 99,9 % | 950,5x |
| 3840 | 4.3.2 Pascua Lama | Constitucional | 112823 | 84 | 99,9 % | 1343,1x |
| 3841 | 4.3.2 Requisitos | Familia | 65085 | 50 | 99,9 % | 1301,7x |
| 3842 | 4.3.3 Un obstáculo: la certidumbre del lucro cesante | Civil | 142015 | 100 | 99,9 % | 1420,2x |
| 3843 | 4.3.3 Verificación extraordinaria | Judicial | 64632 | 88 | 99,9 % | 734,5x |
| 3844 | 4.3.4 El lucro cesante en la responsabilidad | Civil | 142015 | 117 | 99,9 % | 1213,8x |
| 3845 | 4.3.5 El contenido del lucro cesante | Civil | 142015 | 107 | 99,9 % | 1327,2x |
| 3846 | 4.3.7 Lucro cesante reflejo o por repercusión | Civil | 142015 | 106 | 99,9 % | 1339,8x |
| 3847 | 4.4     Impacto de la Ley Nº 19.799 | Judicial | 96536 | 68 | 99,9 % | 1419,6x |
| 3848 | 4.4.1 Composición | Familia | 100107 | 72 | 99,9 % | 1390,4x |
| 3849 | 4.4.1 Conceptos | Constitucional | 112823 | 84 | 99,9 % | 1343,1x |
| 3850 | 4.4.1 El punto de partida: la regla de la | Civil | 142015 | 143 | 99,9 % | 993,1x |
| 3851 | 4.4.1 Iniciativas institucionales en materia de violencia | Familia | 95131 | 96 | 99,9 % | 990,9x |
| 3852 | 4.4.1 La inaplicabilidad judicial del Decreto ley 2191 | Penal | 121924 | 105 | 99,9 % | 1161,2x |
| 3853 | 4.4.1 Modalidades | Laboral | 100583 | 67 | 99,9 % | 1501,2x |
| 3854 | 4.4.1 Persecución penal estatal de los | Judicial | 134465 | 105 | 99,9 % | 1280,6x |
| 3855 | 4.4.1 Portal web del Poder Judicial | Laboral | 71986 | 62 | 99,9 % | 1161,1x |
| 3856 | 4.4.10 Duración y vigencia de los | Laboral | 100583 | 88 | 99,9 % | 1143,0x |
| 3857 | 4.4.11 Ultraactividad del instrumento colectivo | Laboral | 100583 | 118 | 99,9 % | 852,4x |
| 3858 | 4.4.12 Incumplimiento del instrumento | Laboral | 100583 | 119 | 99,9 % | 845,2x |
| 3859 | 4.4.13 Mérito ejecutivo | Laboral | 100583 | 118 | 99,9 % | 852,4x |
| 3860 | 4.4.2 Causas pendientes de RIT | Penal | 57066 | 83 | 99,9 % | 687,5x |
| 3861 | 4.4.2 El daño moral contractual es indemnizable | Civil | 142015 | 101 | 99,9 % | 1406,1x |
| 3862 | 4.4.2 Información sobre audiencias | Laboral | 71986 | 79 | 99,9 % | 911,2x |
| 3863 | 4.4.2 La comunidad sancionadora: el deber del juez de | Judicial | 134465 | 93 | 99,9 % | 1445,9x |
| 3864 | 4.4.2 La indemnización civil como forma de | Penal | 121924 | 94 | 99,9 % | 1297,1x |
| 3865 | 4.4.2.1 No existirá NC en las empresas del Estado dependientes del | Laboral | 100583 | 81 | 99,9 % | 1241,8x |
| 3866 | 4.4.2.2 Tampoco podrá existir NC en las empresas o instituciones | Laboral | 100583 | 107 | 99,9 % | 940,0x |
| 3867 | 4.4.2.3 Sobre los trabajadores impedidos de ejercer el derecho a | Laboral | 100583 | 126 | 99,9 % | 798,3x |
| 3868 | 4.4.2.6 Sobre el plazo mínimo para negociar colectivamente en una | Laboral | 100583 | 100 | 99,9 % | 1005,8x |
| 3869 | 4.4.2.7 Las empresas en que no exista un instrumento colectivo | Laboral | 100583 | 87 | 99,9 % | 1156,1x |
| 3870 | 4.4.3 Interacción con el tribunal | Familia | 100107 | 89 | 99,9 % | 1124,8x |
| 3871 | 4.4.3 La revisión de las sentencias | Penal | 121924 | 100 | 99,9 % | 1219,2x |
| 3872 | 4.4.3 Traducción para las personas con | Laboral | 71986 | 100 | 99,9 % | 719,9x |
| 3873 | 4.4.4 Casos en otras jurisdicciones: Caso Lidl (Alemania) | Constitucional | 112823 | 94 | 99,9 % | 1200,2x |
| 3874 | 4.4.4 Contenido de la negociación | Laboral | 100583 | 114 | 99,9 % | 882,3x |
| 3875 | 4.4.4 Oferta de compra directa | Judicial | 64632 | 81 | 99,9 % | 797,9x |
| 3876 | 4.4.4.1 Atención de público | Penal | 57066 | 72 | 99,9 % | 792,6x |
| 3877 | 4.4.4.2 Búsqueda de causas | Penal | 57066 | 85 | 99,9 % | 671,4x |
| 3878 | 4.4.5 Fuero de negociación colectiva reglada | Laboral | 100583 | 127 | 99,9 % | 792,0x |
| 3879 | 4.4.6 Relación y efectos del instrumento colectivo | Laboral | 100583 | 113 | 99,9 % | 890,1x |
| 3880 | 4.4.6 Tramitación de solicitudes | Penal | 57066 | 78 | 99,9 % | 731,6x |
| 3881 | 4.4.7 Instrumento colectivo | Laboral | 100583 | 84 | 99,9 % | 1197,4x |
| 3882 | 4.4.8 Aplicación de las estipulaciones | Laboral | 100583 | 123 | 99,9 % | 817,7x |
| 3883 | 4.4.9 Instrumento colectivo y afiliación sindical | Laboral | 100583 | 122 | 99,9 % | 824,5x |
| 3884 | 4.5           Acciones de | Familia | 65085 | 65 | 99,9 % | 1001,3x |
| 3885 | 4.5     El certificado de firma electrónica y | Judicial | 96536 | 58 | 99,9 % | 1664,4x |
| 3886 | 4.5     Unidad de | Judicial | 44331 | 46 | 99,9 % | 963,7x |
| 3887 | 4.5   La discapacidad | Constitucional | 121906 | 63 | 99,9 % | 1935,0x |
| 3888 | 4.5.1 Acceso a la justicia de las mujeres víctimas | Familia | 95131 | 92 | 99,9 % | 1034,0x |
| 3889 | 4.5.1 Condiciones relativas a la calidad | Constitucional | 104063 | 111 | 99,9 % | 937,5x |
| 3890 | 4.5.1 Inicio | Laboral | 100583 | 74 | 99,9 % | 1359,2x |
| 3891 | 4.5.1 La noción de daño corporal y su | Civil | 142015 | 123 | 99,9 % | 1154,6x |
| 3892 | 4.5.1 La validez de los certificados | Judicial | 96536 | 104 | 99,9 % | 928,2x |
| 3893 | 4.5.1.1 Pertinencia de los datos | Constitucional | 104063 | 117 | 99,9 % | 889,4x |
| 3894 | 4.5.1.2 Exactitud y actualización | Constitucional | 104063 | 107 | 99,9 % | 972,6x |
| 3895 | 4.5.1.3 Razonabilidad | Constitucional | 104063 | 84 | 99,9 % | 1238,8x |
| 3896 | 4.5.10 Derecho al piso de la negociación | Laboral | 100583 | 126 | 99,9 % | 798,3x |
| 3897 | 4.5.2   Protocolo de actuación para la atención en justicia con enfoque de género | Familia | 95131 | 54 | 99,9 % | 1761,7x |
| 3898 | 4.5.2 Contenido del proyecto | Laboral | 100583 | 75 | 99,9 % | 1341,1x |
| 3899 | 4.5.2 La acreditación fehaciente de la | Judicial | 96536 | 84 | 99,9 % | 1149,2x |
| 3900 | 4.5.2 Proporcionalidad | Constitucional | 104063 | 76 | 99,9 % | 1369,2x |
| 3901 | 4.5.2 Protocolo de actuación para la atención en | Familia | 95131 | 85 | 99,9 % | 1119,2x |
| 3902 | 4.5.2 Sala | Familia | 100107 | 80 | 99,9 % | 1251,3x |
| 3903 | 4.5.2. Tracks | Procesal | 96699 | 141 | 99,9 % | 685,8x |
| 3904 | 4.5.3 Atención de público y mediación | Familia | 100107 | 89 | 99,9 % | 1124,8x |
| 3905 | 4.5.3 Comisión negociadora sindical | Laboral | 100583 | 113 | 99,9 % | 890,1x |
| 3906 | 4.5.3 Temporalidad del tratamiento | Constitucional | 104063 | 80 | 99,9 % | 1300,8x |
| 3907 | 4.5.4 Calidad de proceso | Constitucional | 104063 | 101 | 99,9 % | 1030,3x |
| 3908 | 4.5.4 Comisión negociadora del empleador | Laboral | 100583 | 113 | 99,9 % | 890,1x |
| 3909 | 4.5.4 Servicio | Familia | 100107 | 85 | 99,9 % | 1177,7x |
| 3910 | 4.5.5 Administración de causas | Familia | 100107 | 65 | 99,9 % | 1540,1x |
| 3911 | 4.5.5 Cumplimiento de derechos de los titulares de datos | Constitucional | 104063 | 89 | 99,9 % | 1169,2x |
| 3912 | 4.5.5 Presentación del proyecto | Laboral | 100583 | 110 | 99,9 % | 914,4x |
| 3913 | 4.5.5.1 Cumplimiento | Familia | 100107 | 66 | 99,9 % | 1516,8x |
| 3914 | 4.5.6 Trabajadores afectos a la negociación | Laboral | 100583 | 98 | 99,9 % | 1026,4x |
| 3915 | 4.5.7 Oportunidad de presentación del | Laboral | 100583 | 71 | 99,9 % | 1416,7x |
| 3916 | 4.5.8 Respuesta del empleador | Laboral | 100583 | 78 | 99,9 % | 1289,5x |
| 3917 | 4.5.9 Impugnaciones y reclamaciones | Laboral | 100583 | 104 | 99,9 % | 967,1x |
| 3918 | 4.6   Acción de | Familia | 65085 | 39 | 99,9 % | 1668,8x |
| 3919 | 4.6   Negociación colectiva de | Laboral | 100583 | 54 | 99,9 % | 1862,6x |
| 3920 | 4.6.1 Acerca de la noción de pérdida | Civil | 142015 | 101 | 99,9 % | 1406,1x |
| 3921 | 4.6.1 Normas especiales sobre la discapacidad | Constitucional | 121906 | 92 | 99,9 % | 1325,1x |
| 3922 | 4.6.1.1 Ley Nº 20.609, que establece medidas contra la | Constitucional | 121906 | 127 | 99,9 % | 959,9x |
| 3923 | 4.6.1.2 Ley Nº 20.584, de derechos y deberes de las per- | Constitucional | 121906 | 71 | 99,9 % | 1717,0x |
| 3924 | 4.6.1.3 Ley Nº 19.966, que establece un régimen de garan- | Constitucional | 121906 | 91 | 99,9 % | 1339,6x |
| 3925 | 4.6.1.4 Ley Nº 20.422, sobre igualdad de oportunidades e | Constitucional | 121906 | 124 | 99,9 % | 983,1x |
| 3926 | 4.6.2 Normas civiles con posible | Constitucional | 121906 | 109 | 99,9 % | 1118,4x |
| 3927 | 4.6.2.1 Discapacidad e interdicción por demencia | Constitucional | 121906 | 74 | 99,9 % | 1647,4x |
| 3928 | 4.6.2.2 Discapacidad e interdicción por disipación | Constitucional | 121906 | 80 | 99,9 % | 1523,8x |
| 3929 | 4.6.4 Pérdida de la oportunidad de los familiares | Civil | 142015 | 118 | 99,9 % | 1203,5x |
| 3930 | 4.7           Nulidad del | Familia | 65085 | 37 | 99,9 % | 1759,1x |
| 3931 | 4.7     Negociación colectiva de trabajadores contratados | Laboral | 100583 | 84 | 99,9 % | 1197,4x |
| 3932 | 4.7    Documentación recibida y | Laboral | 71986 | 41 | 99,9 % | 1755,8x |
| 3933 | 4.7 Negociación colectiva de trabajadores contratados por eventuales, de temporada y por obra o | Laboral | 100583 | 68 | 99,9 % | 1479,2x |
| 3934 | 4.7.1 Error | Familia | 65085 | 85 | 99,9 % | 765,7x |
| 3935 | 4.7.1 Oportunidad, formalidades y | Laboral | 100583 | 123 | 99,9 % | 817,7x |
| 3936 | 4.7.1 Principales documentos recibidos | Laboral | 71986 | 63 | 99,9 % | 1142,6x |
| 3937 | 4.7.1.1 Respuesta del empleador: la empresa deberá dar respues- | Laboral | 100583 | 128 | 99,9 % | 785,8x |
| 3938 | 4.7.1.2 Reuniones durante la negociación: durante la negocia- | Laboral | 100583 | 93 | 99,9 % | 1081,5x |
| 3939 | 4.7.1.3 Mediación: cualquiera de las partes podrá solicitar la me- | Laboral | 100583 | 93 | 99,9 % | 1081,5x |
| 3940 | 4.7.2 Dolo | Familia | 65085 | 79 | 99,9 % | 823,9x |
| 3941 | 4.7.2 Principales documentos | Laboral | 71986 | 94 | 99,9 % | 765,8x |
| 3942 | 4.7.2 Relación del convenio colectivo con el | Laboral | 100583 | 122 | 99,9 % | 824,5x |
| 3943 | 4.7.3   Fuerza                                                                                            126 | Familia | 65085 | 53 | 99,9 % | 1228,0x |
| 3944 | 4.7.3 Pactos sobre condiciones especiales de trabajo | Laboral | 100583 | 98 | 99,9 % | 1026,4x |
| 3945 | 4.7.4 Convenio de provisión de puestos de trabajo | Laboral | 100583 | 74 | 99,9 % | 1359,2x |
| 3946 | 4.8   Interposición conjunta de las acciones | Familia | 65085 | 85 | 99,9 % | 765,7x |
| 3947 | 4.8   Negociación colectiva de | Laboral | 100583 | 68 | 99,9 % | 1479,2x |
| 3948 | 4.8.1 Acreditación | Judicial | 96536 | 91 | 99,9 % | 1060,8x |
| 3949 | 4.8.2 Registro | Judicial | 96536 | 66 | 99,9 % | 1462,7x |
| 3950 | 4.8.3 Fiscalización | Judicial | 96536 | 55 | 99,9 % | 1755,2x |
| 3951 | 4.9     El documento electrónico firmado comomedio de | Judicial | 96536 | 81 | 99,9 % | 1191,8x |
| 3952 | 40   Oficio Nº 885 (17 de octubre de 1974), Decreto de remoción de funcionarios removidos. Según art. 277 COT | Procesal | 94881 | 91 | 99,9 % | 1042,6x |
| 3953 | 40   STC rol N° 2009-111 sobre control preventivo de constitucionalidad de diversas disposiciones del proyecto | Judicial | 105809 | 106 | 99,9 % | 998,2x |
| 3954 | 40 A modo ejemplar, véase la sentencia de la Ilustrísima Corte de Apelaciones de | Procesal | 86112 | 120 | 99,9 % | 717,6x |
| 3955 | 40 Ley 21.515 que modifica diversos cuerpos legales para establecer la mayoría de | Familia | 123490 | 100 | 99,9 % | 1234,9x |
| 3956 | 40 Piénsese en algunas categorías de remuneraciones, como las gratificaciones o | Procesal | 86112 | 65 | 99,9 % | 1324,8x |
| 3957 | 40 Véase las sentencias del Supremo Tribunal Federal de Brasil, ADI 3768/DF, del | Judicial | 81675 | 100 | 99,9 % | 816,8x |
| 3958 | 40. CORTE SUPREMA, rol N° 2.820-2003, de dos de | Familia | 65085 | 87 | 99,9 % | 748,1x |
| 3959 | 40. Decreto N° 10. Crea comisión nacional obstétrica | Judicial | 89476 | 68 | 99,9 % | 1315,8x |
| 3960 | 40. Juan Vásquez Olivares con Servicio de Salud de       55. María Rossi Sánchez con Colegio Academia de | Civil | 142015 | 91 | 99,9 % | 1560,6x |
| 3961 | 40. Las empresas pueden incidir prácticamente en todo lo | Constitucional | 112823 | 97 | 99,9 % | 1163,1x |
| 3962 | 40. Un juez(a) y los miembros de su familia no pedirán ni aceptarán | Procesal | 94881 | 84 | 99,9 % | 1129,5x |
| 3963 | 40.3 Los Estados parte tomarán todas las medidas apropiadas para pro- | Penal | 86906 | 71 | 99,9 % | 1224,0x |
| 3964 | 405 Así por ejemplo, el informe de fiscalización de la Dirección del Trabajo puede ser estimado como un puro | Laboral | 113458 | 70 | 99,9 % | 1620,8x |
| 3965 | 41   Oficio Nº 885 (17 de octubre de 1974), Decreto de remoción de funcionarios removidos. Según art. 277 COT | Procesal | 101194 | 91 | 99,9 % | 1112,0x |
| 3966 | 41 En este último punto hubo un debate importante, pues la postura inicial de | Penal | 178516 | 172 | 99,9 % | 1037,9x |
| 3967 | 41 La Ley 17/2021 introdujo modificaciones al Código Civil español en aras del | Familia | 123490 | 106 | 99,9 % | 1165,0x |
| 3968 | 41 Obviamente hay excepciones, pero con procedimientos excepcionales, como | Procesal | 86112 | 79 | 99,9 % | 1090,0x |
| 3969 | 41 Para más información, véase Poder Judicial (2015-2020: 78-79): «a) Aquella | Constitucional | 177323 | 170 | 99,9 % | 1043,1x |
| 3970 | 41.   Secretaría de la Función Pública (2007): Manual | Judicial | 79146 | 80 | 99,9 % | 989,3x |
| 3971 | 41. CORTE SUPREMA, rol Nº 2.564-2006, de veinti- | Familia | 65085 | 85 | 99,9 % | 765,7x |
| 3972 | 41. En el párrafo 1, hacer frente a impactos negativos, reales | Constitucional | 112823 | 104 | 99,9 % | 1084,8x |
| 3973 | 41. HOIKKALA, Susanna y PÖSÖ, Tarja (2020): “The | Penal | 72395 | 100 | 99,9 % | 724,0x |
| 3974 | 41. Judith Cecilia González Concha con Clínica Los       56. Maricel Vallejos García con Servicio de Salud | Civil | 142015 | 100 | 99,9 % | 1420,2x |
| 3975 | 410   Una enumeración de las distintas hipótesis de indemnización del daño moral estando “vigente” el contrato | Laboral | 113458 | 144 | 99,9 % | 787,9x |
| 3976 | 413   MARZI MUÑOZ, Daniela (2015), “La readmisión como reparación: condición para la ciudadanía en el trabajo | Laboral | 113458 | 81 | 99,9 % | 1400,7x |
| 3977 | 42   Corte Suprema, 25 de abril de 2006, “Laboratorio Bestpharma con Instituto de Salud Pública”; Corte Supre- | Judicial | 105809 | 109 | 99,9 % | 970,7x |
| 3978 | 42 La regulación del descubrimiento de un tesoro se encuentra en los artículos | Familia | 123490 | 98 | 99,9 % | 1260,1x |
| 3979 | 42. CAPONI, Remo (2016 b): Rigidita` e flessibilita` del processo civile, en | Procesal | 96699 | 106 | 99,9 % | 912,3x |
| 3980 | 42. CORTE SUPREMA, rol N° 2.084-2005, de veintio- | Familia | 65085 | 92 | 99,9 % | 707,4x |
| 3981 | 42. ESTRADA, Dorothy (2019): “El principio de igualdad ante la ley en el | Judicial | 81476 | 66 | 99,9 % | 1234,5x |
| 3982 | 42. GARCÍA, Sabina y VILLAVICENCIO, Luis (2016): “Alcances y límites del | Constitucional | 121906 | 72 | 99,9 % | 1693,1x |
| 3983 | 420 CS Rol 28.922-2015, de fecha 13 de julio de 2016, caratulados “Miranda Pradenas Macarena con Subsecretaría | Laboral | 113458 | 88 | 99,9 % | 1289,3x |
| 3984 | 421      Corte Suprema: Gallegos con Fernández (2008, rol Nº 6574-2007) considerando 6° de la sentencia de re- | Penal | 121924 | 139 | 99,9 % | 877,2x |
| 3985 | 426   Documento disponible en https://www.senadis.gob.cl/pag/291/1547/constitucion_politica_y_tratados_inter- | Constitucional | 121906 | 66 | 99,9 % | 1847,1x |
| 3986 | 427      OBSERVATORIO DE DERECHOS HUMANOS UDP (2014), p. 17; SUÁREZ (2016), pp. 424-425; MEZA-LOPEHANDÍA | Penal | 121924 | 67 | 99,9 % | 1819,8x |
| 3987 | 429 Corte de Apelaciones de Santiago: Contra Contreras Sepúlveda y otros (Caso Miguel Ángel Sandoval Ro- | Penal | 121924 | 93 | 99,9 % | 1311,0x |
| 3988 | 43      National Human Genome Research Institute (2019) | Familia | 65085 | 97 | 99,9 % | 671,0x |
| 3989 | 43 Como explican Núñez y Pérez (2014: 252), ambas tienen en común que se trata | Judicial | 144656 | 184 | 99,9 % | 786,2x |
| 3990 | 43 En contra Navas y Jaar (2018: 1.036), que señalan: «Sin embargo, este criterio | Penal | 178516 | 167 | 99,9 % | 1069,0x |
| 3991 | 43 En ese entonces se trataba de la Ley 13.196 de 1958, que básicamente establecía | Penal | 178516 | 182 | 99,9 % | 980,9x |
| 3992 | 43 En estos casos Taruffo se pregunta: «¿De quién es la experiencia relevante para | Judicial | 150341 | 184 | 99,9 % | 817,1x |
| 3993 | 43 En estos casos no tendrá aplicación lo dispuesto en el artículo 52 del Código de | Familia | 97488 | 94 | 99,9 % | 1037,1x |
| 3994 | 43 Famosa es la afirmación clásica dolus vere probari non potest, cum in animun | Judicial | 62514 | 55 | 99,9 % | 1136,6x |
| 3995 | 43 La ley asimila el hallazgo de un tesoro a una adquisición a título gratuito y | Familia | 123490 | 75 | 99,9 % | 1646,5x |
| 3996 | 43 Las materias objeto de las recomendaciones tienen distintos fundamentos. Si | Penal | 178516 | 102 | 99,9 % | 1750,2x |
| 3997 | 43 Lo antedicho aun cuando en la motivación de la sentencia pueda sostenerse | Procesal | 86112 | 61 | 99,9 % | 1411,7x |
| 3998 | 43 Matus y Ramírez (2019: 482), quienes agregan que no podría exigirse que se | Penal | 97633 | 118 | 99,9 % | 827,4x |
| 3999 | 43 Para más información, véase Poder Judicial (2015-2020: 80): «Es en la que se | Constitucional | 177323 | 172 | 99,9 % | 1030,9x |
| 4000 | 43 Que tiene como condición necesaria la aceptación del reenvío a las normas del | Procesal | 86112 | 84 | 99,9 % | 1025,1x |
| 4001 | 43 Véase las Reglas de La Habana (número 64) y la Observación General número | Penal | 86906 | 91 | 99,9 % | 955,0x |
| 4002 | 43. CAPONI, Remo (2010): II principio di proporzíonalitá nella giustizia | Procesal | 96699 | 115 | 99,9 % | 840,9x |
| 4003 | 43. CORTE SUPREMA, rol N° 3.249-2006, de vein- | Familia | 65085 | 87 | 99,9 % | 748,1x |
| 4004 | 43. El párrafo 3 se refiere a situaciones más complejas en las | Constitucional | 112823 | 107 | 99,9 % | 1054,4x |
| 4005 | 43. FACIO, A. y FRIES, L. (2005): “Feminismo, Género y Patriarcado”, en Revista | Judicial | 81476 | 65 | 99,9 % | 1253,5x |
| 4006 | 43. Katherine Gajardo Orellana con Patricio Stevens      58. Megafrut Limitada con Andes Logistics de Chile | Civil | 142015 | 94 | 99,9 % | 1510,8x |
| 4007 | 430 Cfr. NOGUEIRA (2005), p. 41; ZÚÑIGA (2006), p. 3; DÍAZ (2006). La sentencia del caso de desaparición for- | Penal | 121924 | 132 | 99,9 % | 923,7x |
| 4008 | 431 Documento disponible en http://www.supersalud.gob.cl/consultas/667/w3-article-7959.html | Constitucional | 121906 | 81 | 99,9 % | 1505,0x |
| 4009 | 433      Corte Suprema: Contra Pinto, caso Chena (2007, rol Nº 3125-2004) considerando 24° de la sentencia de | Penal | 121924 | 136 | 99,9 % | 896,5x |
| 4010 | 433   Considerando octavo, CS Rol 28.922- 2015, de 13 de julio de 2016, caratulados “Miranda Pradenas Macarena | Laboral | 113458 | 89 | 99,9 % | 1274,8x |
| 4011 | 434               Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 159 | 99,9 % | 1974,7x |
| 4012 | 434 Guía legal sobre Plan GES o AUGE. Ley de Derechos y Deberes del Paciente, Nº 20.584. Documento disponible | Constitucional | 121906 | 62 | 99,9 % | 1966,2x |
| 4013 | 436. Señala al efecto: “…se ha observado que además del influjo del contrato principal sobre el accesorio (…) | Civil | 110175 | 118 | 99,9 % | 933,7x |
| 4014 | 438 OBSERVATORIO DE DERECHOS HUMANOS UDP (2014), p. 17; CUBIDES et. ál.. (2015), p. 33; MEZA-LOPEHANDÍA | Penal | 121924 | 111 | 99,9 % | 1098,4x |
| 4015 | 438 Se ha hecho presente que la ciudadanía en la empresa es complementaria de los derechos fundamentales más | Laboral | 113458 | 83 | 99,9 % | 1367,0x |
| 4016 | 44   FERRADA, Juan Carlos (2006), pp. 257-264. Ver también, sentencia Corte Suprema, de 29 de diciembre de | Judicial | 105809 | 92 | 99,9 % | 1150,1x |
| 4017 | 44 En el mismo lugar, el autor cita abundante jurisprudencia en respaldo de cada | Judicial | 81675 | 72 | 99,9 % | 1134,4x |
| 4018 | 44 En sentencia Corte Suprema, rol 11673-2021, de 16 de diciembre de 2022, se | Judicial | 144656 | 163 | 99,9 % | 887,5x |
| 4019 | 44 Entre ellos, los artículos 30 y 31 de la Ley sobre Impuesto a la Renta, contenida en | Penal | 178516 | 172 | 99,9 % | 1037,9x |
| 4020 | 44 Estas normas buscan proteger a los terceros que de buena fe contratan con uno | Familia | 123490 | 107 | 99,9 % | 1154,1x |
| 4021 | 44 Sí hay un importante desarrollo doctrinario y jurisprudencial respecto de los | Judicial | 144656 | 97 | 99,9 % | 1491,3x |
| 4022 | 44 Una aplicación moderna de la asociación de las máximas de la experiencia con | Judicial | 150341 | 148 | 99,9 % | 1015,8x |
| 4023 | 44 Véase el artículo 40.2 letra b) punto iv. de la Convención de los Derechos del | Penal | 86906 | 119 | 99,9 % | 730,3x |
| 4024 | 44.   Biblioteca del Congreso Nacional (s.d.): “Historia de la Ley Nº 20.352. Pro- | Penal | 121924 | 83 | 99,9 % | 1469,0x |
| 4025 | 44. CASAS BECERRA, Lidia (2012), “Un estudio sobre        53. COUSO SALAS, Jaime (2018), “Relevancia penal | Laboral | 113458 | 136 | 99,9 % | 834,2x |
| 4026 | 44. CORTE SUPREMA, rol N° 5.698-2006, de veinti- | Familia | 65085 | 68 | 99,9 % | 957,1x |
| 4027 | 44. CS, rol 2896-2002, de 22 de agosto de 2002.           65. RIT VD-10-00010-2014 (TTA del Biobío, de 11 de | Judicial | 105809 | 119 | 99,9 % | 889,2x |
| 4028 | 44. El párrafo 4 recomienda a las empresas que manifiesten su | Constitucional | 112823 | 68 | 99,9 % | 1659,2x |
| 4029 | 44. FERNÁNDEZ, Mariano (2018): “La protección contra la discriminación por | Judicial | 81476 | 100 | 99,9 % | 814,8x |
| 4030 | 44. Katherine Torrontegui González y otra con Clínica    59. Milan Ceric Aguila con Servicio de Salud de Viña | Civil | 142015 | 96 | 99,9 % | 1479,3x |
| 4031 | 44. Los Estados partes deben adoptar las medidas necesarias | Constitucional | 112823 | 96 | 99,9 % | 1175,2x |
| 4032 | 44. NÚÑEZ, René y CORTÉS, Mauricio (2012): De- | Familia | 100107 | 87 | 99,9 % | 1150,7x |
| 4033 | 45 Comité de las Naciones Unidas para la Eliminación de todas las Formas de | Constitucional | 177323 | 165 | 99,9 % | 1074,7x |
| 4034 | 45 Como modalidad de la subrogación por compra, en la práctica podría darse | Familia | 123490 | 115 | 99,9 % | 1073,8x |
| 4035 | 45 En la denominación del procedimiento civil: audiencia de nombramiento de | Procesal | 86112 | 53 | 99,9 % | 1624,8x |
| 4036 | 45 Hay consenso en que para que se configure este vicio deben haberse hecho | Judicial | 144656 | 128 | 99,9 % | 1130,1x |
| 4037 | 45 Para más información, véase Poder Judicial (2015-2020: 80): «Es un delito que | Constitucional | 177323 | 111 | 99,9 % | 1597,5x |
| 4038 | 45 Por ejemplo, en el caso Educer, la sentencia señaló: «Por último, la comisión | Penal | 178516 | 172 | 99,9 % | 1037,9x |
| 4039 | 45 Sentencia de la Corte Suprema, rol 13.823-2014, 16 de abril de 2015; sentencia | Penal | 178516 | 191 | 99,9 % | 934,6x |
| 4040 | 45 Turner Saelzer advierte sobre la necesidad de alejar la compensación de una | Familia | 123490 | 74 | 99,9 % | 1668,8x |
| 4041 | 45 Ver artículos 28 y 54 de la Ley 19.968 que crea los Tribunales de Familia, 295 y | Procesal | 86112 | 78 | 99,9 % | 1104,0x |
| 4042 | 45.   Villanueva, E. (2010): Publicidad oficial: Trans- | Administrativo | 89720 | 106 | 99,9 % | 846,4x |
| 4043 | 45. FIGUEROA, Rodolfo (2000): “Igualdad y discriminación”, en Cuadernos de | Judicial | 81476 | 70 | 99,9 % | 1163,9x |
| 4044 | 45. Katty Vásquez Contreras y otros con Hospital         60. Héctor Montecinos Peralta con Hospital Clínico | Civil | 142015 | 94 | 99,9 % | 1510,8x |
| 4045 | 452                Jean Pierre Matus Acuña y Mª Cecilia Ramírez Guzmán | General | 313985 | 166 | 99,9 % | 1891,5x |
| 4046 | 454 N° 5 párrafo final del CT, que establece que la comparecencia | Laboral | 113458 | 76 | 99,9 % | 1492,9x |
| 4047 | 46   Véase https://www.pjud.cl/post/etica-judicial-cs | Procesal | 94881 | 53 | 99,9 % | 1790,2x |
| 4048 | 46 A partir del tenor expreso del número 2 del artículo 1727 del Código Civil se ha | Familia | 123490 | 84 | 99,9 % | 1470,1x |
| 4049 | 46 Couture agrega: «El progreso de la ciencia está hecho de una serie de máximas | Judicial | 150341 | 93 | 99,9 % | 1616,6x |
| 4050 | 46 En dicho sentido, véase Vásquez (2015: 48), quien coherentemente ubica a la | Procesal | 86112 | 89 | 99,9 % | 967,6x |
| 4051 | 46 Entre ellas destacan las siguientes del Servicio de Impuestos Internos (SII): i) | Penal | 178516 | 179 | 99,9 % | 997,3x |
| 4052 | 46 Para más información, véase Poder Judicial (2015-2020: 80-81): «Es el proceso | Constitucional | 177323 | 153 | 99,9 % | 1159,0x |
| 4053 | 46 STC, 174-1985, del 17 de diciembre de 1985. Ponente: Segura Latorres. Citado | Judicial | 62514 | 61 | 99,9 % | 1024,8x |
| 4054 | 46 Sentencia Tribunal Constitucional 5369, de 8 de octubre de 2019. De manera | Judicial | 144656 | 161 | 99,9 % | 898,5x |
| 4055 | 46 Ya en 2015 el Banco del Estado identificó movimientos irregulares en una | Penal | 178516 | 162 | 99,9 % | 1102,0x |
| 4056 | 46. GARNELO Marta; BUSTIN Chloe; DURYEA Suzanne; MORRISON Andrew | Judicial | 81476 | 76 | 99,9 % | 1072,1x |
| 4057 | 46. Jorge Arnaldo Leal Labrín con Servicio de Salud | Civil | 142015 | 92 | 99,9 % | 1543,6x |
| 4058 | 46. La igualdad de armas, que constituye un elemento del proceso | Judicial | 144656 | 102 | 99,9 % | 1418,2x |
| 4059 | 47       Véanse al respecto los documentos emanados de la XXV Cumbre Iberoamericana de Jefes de Estado y de | Constitucional | 104063 | 113 | 99,9 % | 920,9x |
| 4060 | 47 Artículo 331 b) del Código Procesal Penal, artículo 453 número 8 inciso cuarto | Procesal | 86112 | 100 | 99,9 % | 861,1x |
| 4061 | 47 En todo caso, y aunque puede ser controvertido, parece que cada cónyuge solo | Familia | 123490 | 89 | 99,9 % | 1387,5x |
| 4062 | 47 Para más información, véase Poder Judicial (2015-2020: 81): «Es la ayuda que | Constitucional | 177323 | 163 | 99,9 % | 1087,9x |
| 4063 | 47. Decreto N° 927. Aprueba reglamento del examen | Judicial | 89476 | 115 | 99,9 % | 778,1x |
| 4064 | 47. Elsa León Muñoz con Mauricio Hinostroza Scheel | Civil | 142015 | 91 | 99,9 % | 1560,6x |
| 4065 | 47. GAUCHÉ, Ximena (2018): “Comentarios a la opinión consultiva 24/17 de la | Judicial | 81476 | 74 | 99,9 % | 1101,0x |
| 4066 | 48   Corte Interamericana de Derechos Humanos. Caso Urrutia-Laubreaux vs. Chile. Sentencia de 27 de agosto | Procesal | 94881 | 89 | 99,9 % | 1066,1x |
| 4067 | 48 Dentro de este pasivo se encuentran las deudas de los numerales 1, 2, 4 y 5 del | Familia | 123490 | 127 | 99,9 % | 972,4x |
| 4068 | 48 Se seguirá el orden de aparición en el texto legal y no un orden sistemático | Procesal | 86112 | 54 | 99,9 % | 1594,7x |
| 4069 | 48 Sentencia de la Corte Suprema, rol 7.006-2021, 23 de marzo de 2022. En el | Penal | 178516 | 200 | 99,9 % | 892,6x |
| 4070 | 48 Sentencia expediente 2945-2003-AA/TC, Tribunal Constitucional peruano, de | Judicial | 81675 | 67 | 99,9 % | 1219,0x |
| 4071 | 48. Leonel Ramírez Robledo con Fisco de Chile | Civil | 142015 | 87 | 99,9 % | 1632,4x |
| 4072 | 48. MACCORMICK, Neil (1982): “Children’s Rights: A | Penal | 72395 | 94 | 99,9 % | 770,2x |
| 4073 | 49   Corte Interamericana de Derechos Humanos. Caso Urrutia-Laubreaux vs. Chile. Sentencia de 27 de agosto | Procesal | 101194 | 91 | 99,9 % | 1112,0x |
| 4074 | 49   GAMONAL C., Sergio (2010), Trabajo y derecho, Santiago, AbeledoPerrot, pp. 51 y ss., y GAMONAL C., Sergio | Laboral | 113458 | 104 | 99,9 % | 1090,9x |
| 4075 | 49 Hoop agrega: «existen abundantes y variados ejemplos en la jurisprudencia | Judicial | 150341 | 130 | 99,9 % | 1156,5x |
| 4076 | 49 Los derechos y garantías reconocidos por la Constitución y por los tratados | Constitucional | 177323 | 169 | 99,9 % | 1049,2x |
| 4077 | 49 Medida cautelar, Pet. 1246 MC/SC (Santa Catarina), Supremo Tribunal Federal | Judicial | 81675 | 54 | 99,9 % | 1512,5x |
| 4078 | 49 Observación General 18 del CteDH de 1989, párrafo 13; Observación General | Constitucional | 177323 | 109 | 99,9 % | 1626,8x |
| 4079 | 49 Se comprenden en el pasivo relativo o provisorio las deudas del numeral 3 del | Familia | 123490 | 102 | 99,9 % | 1210,7x |
| 4080 | 49 Sentencia del Tribunal Oral de lo Penal de Angol, RUC 0100083503-6, del 14 de | Judicial | 62514 | 58 | 99,9 % | 1077,8x |
| 4081 | 49 Sin duda, en un debate de objeción de preguntas (por tratarse de una pregunta | Procesal | 86112 | 88 | 99,9 % | 978,5x |
| 4082 | 49. GAUCHÉ, Ximena (2020 b)): Curso sobre estándares internacionales en | Judicial | 81476 | 67 | 99,9 % | 1216,1x |
| 4083 | 49. Lucy Treizman Sacks y otros con Rodrigo Erazo | Civil | 142015 | 130 | 99,9 % | 1092,4x |
| 4084 | 5         Derechos digitales en entornos específicos | Constitucional | 177323 | 143 | 99,9 % | 1240,0x |
| 4085 | 5   Código de Comercio de la República de Chile, de 1 de enero de 1867, Biblioteca del Congreso Nacional de | Judicial | 64632 | 89 | 99,9 % | 726,2x |
| 4086 | 5 Alexy (2003b: 131 y 132). Al respecto, Covarrubias (2018: 483), quien sostiene que | Judicial | 144656 | 166 | 99,9 % | 871,4x |
| 4087 | 5 Artículo 2: 1) Cada uno de los Estados parte en el presente Pacto se compromete | Constitucional | 177323 | 98 | 99,9 % | 1809,4x |
| 4088 | 5 CAT, Guengueng y otros con Senegal, Comunicación 181/2001, Doc. ONU CAT/ | Judicial | 78893 | 62 | 99,9 % | 1272,5x |
| 4089 | 5 Carbonell (2013: 220) precisa que incluye «acciones positivas en favor de grupos | Judicial | 81675 | 76 | 99,9 % | 1074,7x |
| 4090 | 5 Cuenta Pública del Comité Nacional de Riesgos Psicosociales del Poder Judicial | Laboral | 53293 | 50 | 99,9 % | 1065,9x |
| 4091 | 5 Diputada Fanny Pollarolo, Cámara de Diputados, sesión 14, legislatura 343, 9 de | Laboral | 53374 | 58 | 99,9 % | 920,2x |
| 4092 | 5 Dirección del Trabajo, Circular 63 del 29 de julio de 2020, que informa aspectos | Laboral | 98828 | 98 | 99,9 % | 1008,4x |
| 4093 | 5 El Decreto 873 ratifica la suscripción por Chile del Pacto de San José de Costa | Penal | 51155 | 72 | 99,9 % | 710,5x |
| 4094 | 5 El término pureza es erróneo en las especies vegetales, pues atiende a considerar | Penal | 97633 | 107 | 99,9 % | 912,5x |
| 4095 | 5 En cita a pie de página, Ortiz y Arévalo (2021: 305) sostienen que, conforme al | Penal | 194788 | 188 | 99,9 % | 1036,1x |
| 4096 | 5 En contra Ramírez (2021: 14), quien en una reciente obra referida precisamente | Penal | 178516 | 120 | 99,9 % | 1487,6x |
| 4097 | 5 En este sentido Laudan (2006: 65) considera: «In the criminal context, when | Judicial | 150341 | 110 | 99,9 % | 1366,7x |
| 4098 | 5 En este sentido, Gascón (2010: 37) considera que el problema no es la subsunción | Judicial | 150341 | 182 | 99,9 % | 826,0x |
| 4099 | 5 En este sentido, la inviolabilidad de las comunicaciones privadas «comprende | Laboral | 98828 | 109 | 99,9 % | 906,7x |
| 4100 | 5 En otros países, como Argentina, España, Bélgica, Italia y Estados Unidos, se ha | Laboral | 98828 | 98 | 99,9 % | 1008,4x |
| 4101 | 5 En un sentido similar, Taruffo (2010: 161), quien sostiene que es un principio | Judicial | 150341 | 85 | 99,9 % | 1768,7x |
| 4102 | 5 Estas críticas en general son tratadas en Rodríguez Collao y Ossandón Widow | Penal | 178516 | 150 | 99,9 % | 1190,1x |
| 4103 | 5 Este caso que afectó a la Empresa Nacional de Petróleo (ENAP) consistió en | Penal | 178516 | 107 | 99,9 % | 1668,4x |
| 4104 | 5 Este informe constituye un importante precedente de la ley francesa «El Khomri» | Laboral | 98828 | 65 | 99,9 % | 1520,4x |
| 4105 | 5 Fue defendida inicialmente por Cury Urzúa (1992). Sin embargo, luego cambió | Penal | 178516 | 193 | 99,9 % | 925,0x |
| 4106 | 5 Hasta 1994 el adulterio era un delito consagrado en el artículo 375 del Código | Familia | 123490 | 117 | 99,9 % | 1055,5x |
| 4107 | 5 Hombres menores de 14 y mujeres menores de 12 años sometidos a la patria | Constitucional | 177323 | 122 | 99,9 % | 1453,5x |
| 4108 | 5 Juzgado de Letras del Trabajo de Concepción, RIT T-228-2017, 20 de diciembre | Laboral | 53374 | 79 | 99,9 % | 675,6x |
| 4109 | 5 La cafeína como materia prima fue incluida como sustancia química sujeta a | Penal | 97633 | 135 | 99,9 % | 723,2x |
| 4110 | 5 La prueba de la infidelidad es en extremo difícil, ya que tal como lo destaca | Familia | 123490 | 174 | 99,9 % | 709,7x |
| 4111 | 5 Para más información, confrontar con Hernández (2011: 19). El destacado es | Judicial | 62514 | 54 | 99,9 % | 1157,7x |
| 4112 | 5 Porque, como se lee, no usa esa misma expresión, sino que habla de garantías de | Judicial | 144656 | 87 | 99,9 % | 1662,7x |
| 4113 | 5 Reglas de las Naciones Unidas para la protección de los menores privados de | Penal | 86906 | 57 | 99,9 % | 1524,7x |
| 4114 | 5 Según consigna el propio documento, este manual es fruto de las experiencias y | Laboral | 98828 | 88 | 99,9 % | 1123,0x |
| 4115 | 5 Sentencia de la Corte Suprema, 24 de septiembre de 2018, rol 129­2018. En igual | Familia | 123490 | 131 | 99,9 % | 942,7x |
| 4116 | 5 Sentencia de la Corte Suprema, rol 343-2023, 9 de enero 2023, considerando | Familia | 97488 | 102 | 99,9 % | 955,8x |
| 4117 | 5 Sentencia de ministro en visita extraordinaria Milton Juica, rol 118-284, del 31 de | Judicial | 62514 | 91 | 99,9 % | 687,0x |
| 4118 | 5 Sobre negligencia por incumplimiento de esta normativa, se puede acudir al | Judicial | 87950 | 67 | 99,9 % | 1312,7x |
| 4119 | 5 Un acabado estudio sobre el modelo de trabajo en esta Fiscalía se expone por | Judicial | 42513 | 54 | 99,9 % | 787,3x |
| 4120 | 5 Véanse los artículos 105 a 107 y 109 a 115 del Código Civil, en concordancia con | Familia | 123490 | 110 | 99,9 % | 1122,6x |
| 4121 | 5.     Resguardar las pruebas periciales de los NNA, así el registro debe efec- | Judicial | 81476 | 105 | 99,9 % | 776,0x |
| 4122 | 5.    ALEXY, Robert (2001), Teoría de los derechos | Laboral | 113458 | 100 | 99,9 % | 1134,6x |
| 4123 | 5.    CA Santiago, “Enrique Llano con Seremi de | Judicial | 105809 | 118 | 99,9 % | 896,7x |
| 4124 | 5.    Corte de Apelaciones de Concepción, rol N° 31- | Familia | 100107 | 127 | 99,9 % | 788,2x |
| 4125 | 5.    Decreto 100, Constitución Política de la Repú- | Familia | 100107 | 101 | 99,9 % | 991,2x |
| 4126 | 5.    Ley Nº 21.180 sobre transformación digital del | Judicial | 83934 | 58 | 99,9 % | 1447,1x |
| 4127 | 5.   Corte Constitucional de Colombia, Demanda de inconstitucionalidad | Penal | 121924 | 111 | 99,9 % | 1098,4x |
| 4128 | 5. Alentar el desarrollo de una enseñanza, una capacitación y una | Judicial | 82507 | 78 | 99,9 % | 1057,8x |
| 4129 | 5. Apoyo a testigos y peritos | Penal | 57066 | 80 | 99,9 % | 713,3x |
| 4130 | 5. Aquellos a los que se les otorgue tal carácter en el Reglamento de Copropiedad o que | Civil | 192585 | 202 | 99,9 % | 953,4x |
| 4131 | 5. Comisión Interamericana de Derechos Humanos. Reconocimiento | Judicial | 87237 | 63 | 99,9 % | 1384,7x |
| 4132 | 5. Cuando se trate de documentos, datos o informaciones que una ley | Judicial | 92792 | 87 | 99,9 % | 1066,6x |
| 4133 | 5. Decretar la prohibición de celebrar | Familia | 95131 | 57 | 99,9 % | 1669,0x |
| 4134 | 5. Definición de indicadores de gestión que permitan evaluar | Procesal | 94881 | 100 | 99,9 % | 948,8x |
| 4135 | 5. El Estado es responsable por la violación del derecho a ser oído | Judicial | 87237 | 118 | 99,9 % | 739,3x |
| 4136 | 5. El acuerdo correspondiente deberá reducirse a escritura pública suscrita por el | Civil | 192585 | 166 | 99,9 % | 1160,2x |
| 4137 | 5. El contrato contiene una serie de cláusulas concebidas en exclusivo interés del | Civil | 110175 | 158 | 99,9 % | 697,3x |
| 4138 | 5. El párrafo 6 del título XXII del Libro IV, se titula, precisamente, “De la renuncia de | Familia | 136567 | 109 | 99,9 % | 1252,9x |
| 4139 | 5. El tribunal no podrá imponer una pena que sea mayor o menor al | Penal | 194788 | 137 | 99,9 % | 1421,8x |
| 4140 | 5. Enfoque de derechos para avanzar en las demandas indígenas | Judicial | 89476 | 59 | 99,9 % | 1516,5x |
| 4141 | 5. Entrevista a Alda Facio sobre políticas públicas y actuar del Poder | Judicial | 87237 | 71 | 99,9 % | 1228,7x |
| 4142 | 5. Esta acción no aplicará respecto de los actos celebrados en cumplimiento de las | Familia | 81198 | 110 | 99,9 % | 738,2x |
| 4143 | 5. Estefan Vargas, Soraya; “Discriminación estatal de la población | Judicial | 87237 | 81 | 99,9 % | 1077,0x |
| 4144 | 5. Existencia de aptitud de ambos padres para garantizar el bienestar del niño y la posibilidad | Judicial | 79146 | 97 | 99,9 % | 815,9x |
| 4145 | 5. Haberse cometido en cualquier tipo de situación en | Familia | 95131 | 84 | 99,9 % | 1132,5x |
| 4146 | 5. Implementación de equipos investigativos multidisciplinarios para | Constitucional | 177323 | 148 | 99,9 % | 1198,1x |
| 4147 | 5. Interés superior del niño: por el cual, en el curso de la mediación, el mediador | Familia | 190697 | 126 | 99,9 % | 1513,5x |
| 4148 | 5. La circunstancia de haberse acordado que el trabajador a | Judicial | 96536 | 84 | 99,9 % | 1149,2x |
| 4149 | 5. La circunstancia de haberse acordado que el trabajador a distancia | Laboral | 98828 | 104 | 99,9 % | 950,3x |
| 4150 | 5. La enunciación precisa y concreta de las peticiones que se some- | Laboral | 100583 | 70 | 99,9 % | 1436,9x |
| 4151 | 5. La ley debe reconocer iguales derechos tanto a los hijos nacidos | Judicial | 89476 | 57 | 99,9 % | 1569,8x |
| 4152 | 5. Las prohibiciones e impedimentos de ingreso | Constitucional | 115835 | 113 | 99,9 % | 1025,1x |
| 4153 | 5. Ley N° 5.680, de 13 de septiembre de 193521: esta Ley, extendió de cinco a diez | Familia | 190697 | 100 | 99,9 % | 1907,0x |
| 4154 | 5. Los artículos 146, 147 y 148 de los Convenios son de aplicación | Penal | 121924 | 109 | 99,9 % | 1118,6x |
| 4155 | 5. Los contratos forzosos constituyen una realidad insoslayable en el Derecho de los | Civil | 110175 | 96 | 99,9 % | 1147,7x |
| 4156 | 5. Los secretarios de los juzgados de letras llevarán también un libro | Judicial | 52128 | 75 | 99,9 % | 695,0x |
| 4157 | 5. Modelos predictivos, donde la máquina es capaz de aprender | Judicial | 83934 | 109 | 99,9 % | 770,0x |
| 4158 | 5. Muñoz León, Fernando. “La necesidad de una interpretación | Judicial | 87237 | 84 | 99,9 % | 1038,5x |
| 4159 | 5. No se compense lo que el alimentante debe al representante | Familia | 100107 | 54 | 99,9 % | 1853,8x |
| 4160 | 5. Núcleo Especializado de derechos humanos en la carrera militar | Constitucional | 177323 | 153 | 99,9 % | 1159,0x |
| 4161 | 5. Para mejorar la Gobernanza y la Participación Ciudadana: Los datos | Administrativo | 89720 | 93 | 99,9 % | 964,7x |
| 4162 | 5. Preguntar a la persona con discapacidad auditiva si requiere de | Constitucional | 177323 | 102 | 99,9 % | 1738,5x |
| 4163 | 5. Procedimiento contravencional ante los tribunales de familia. Las | Familia | 97488 | 105 | 99,9 % | 928,5x |
| 4164 | 5. Promoción de vida sana y alimentación saludable con niños, niñas | Constitucional | 177323 | 119 | 99,9 % | 1490,1x |
| 4165 | 5. Promover la conciliación total o parcial, conforme a las bases | Familia | 100107 | 143 | 99,9 % | 700,0x |
| 4166 | 5. Que por un lado se denuncia a través de la presente acción constitucional el corte de | Civil | 192585 | 145 | 99,9 % | 1328,2x |
| 4167 | 5. Que, de esta manera, la resolución judicial reclamada por esta vía | Penal | 194788 | 183 | 99,9 % | 1064,4x |
| 4168 | 5. Que, si bien esta Corte ha señalado que en los casos previstos en el | Penal | 194788 | 172 | 99,9 % | 1132,5x |
| 4169 | 5. Que, tal como señala Alfredo Etcheberry, la expresión «fecha de la | Penal | 194788 | 100 | 99,9 % | 1947,9x |
| 4170 | 5. Recursos, procedimientos y tribunales contencioso-administrativos                              78 | Judicial | 105809 | 66 | 99,9 % | 1603,2x |
| 4171 | 5. Reglamento de copropiedad del condominio | Civil | 192585 | 167 | 99,9 % | 1153,2x |
| 4172 | 5. Respecto a la forma en que se practica la notificación del artículo | Judicial | 89450 | 98 | 99,9 % | 912,8x |
| 4173 | 5. Se deberá precisar la institución o la estrategia interinstitucional para | Penal | 194788 | 156 | 99,9 % | 1248,6x |
| 4174 | 5. Señala si procede o no el otorgamiento de alguna pena sustitutiva | Penal | 194788 | 137 | 99,9 % | 1421,8x |
| 4175 | 5. Si al poner en práctica las reglas precedentes no resultare pena que | Penal | 194788 | 104 | 99,9 % | 1873,0x |
| 4176 | 5. Si ha hablado con su pareja sobre los riesgos de tener relaciones | Judicial | 89476 | 118 | 99,9 % | 758,3x |
| 4177 | 5. Si la pena es igual o inferior a sesenta días, o si no constituye una | Penal | 194788 | 117 | 99,9 % | 1664,9x |
| 4178 | 5. Si la pena es igual o inferior a sesenta días, o si no constituye una pena | Penal | 194788 | 111 | 99,9 % | 1754,8x |
| 4179 | 5.1                Deber de seguridad en el tratamiento | Constitucional | 104063 | 53 | 99,9 % | 1963,5x |
| 4180 | 5.1            Ley N° 19.253 | Judicial | 134465 | 84 | 99,9 % | 1600,8x |
| 4181 | 5.1           Aspectos | Judicial | 64632 | 55 | 99,9 % | 1175,1x |
| 4182 | 5.1        Marco constitucional y nacional sobre igualdad | Judicial | 87237 | 67 | 99,9 % | 1302,0x |
| 4183 | 5.1     Presentación | Constitucional | 121906 | 109 | 99,9 % | 1118,4x |
| 4184 | 5.1     Sanción en caso de oposición | Familia | 65085 | 46 | 99,9 % | 1414,9x |
| 4185 | 5.1.1 Acción de protección de las garantías | Judicial | 105809 | 111 | 99,9 % | 953,2x |
| 4186 | 5.1.1 Concepto | Judicial | 79146 | 75 | 99,9 % | 1055,3x |
| 4187 | 5.1.1 Concepto de competencia | Laboral | 100583 | 111 | 99,9 % | 906,2x |
| 4188 | 5.1.1 Control de admisibilidad | Familia | 100107 | 119 | 99,9 % | 841,2x |
| 4189 | 5.1.1 Instrucción | Procesal | 94881 | 92 | 99,9 % | 1031,3x |
| 4190 | 5.1.2 Clasificación de un tribunal del trabajo | Laboral | 100583 | 117 | 99,9 % | 859,7x |
| 4191 | 5.1.2 Estructura | Judicial | 79146 | 106 | 99,9 % | 746,7x |
| 4192 | 5.1.2 Etapa resolutiva | Procesal | 94881 | 122 | 99,9 % | 777,7x |
| 4193 | 5.1.2 Facultades del juez en la etapa de recepción | Familia | 100107 | 70 | 99,9 % | 1430,1x |
| 4194 | 5.1.2 Nulidad de derecho público | Judicial | 105809 | 70 | 99,9 % | 1511,6x |
| 4195 | 5.1.2 Nº 7 de la Ordenanza General de Urbanismo y Construcciones sólo es necesario el | Civil | 192585 | 218 | 99,9 % | 883,4x |
| 4196 | 5.1.2.12 Notificaciones | Judicial | 52128 | 76 | 99,9 % | 685,9x |
| 4197 | 5.1.2.2 Confeccionar y mantener | Judicial | 52128 | 76 | 99,9 % | 685,9x |
| 4198 | 5.1.2.4 Recibir documentación y | Judicial | 52128 | 70 | 99,9 % | 744,7x |
| 4199 | 5.1.2.8 Publicar la información de las audiencias | Judicial | 52128 | 74 | 99,9 % | 704,4x |
| 4200 | 5.1.3 Acción constitucional de amparo (artículo 21) | Judicial | 105809 | 158 | 99,9 % | 669,7x |
| 4201 | 5.1.3 Ejemplos | Judicial | 79146 | 58 | 99,9 % | 1364,6x |
| 4202 | 5.1.3 Impugnación | Procesal | 94881 | 104 | 99,9 % | 912,3x |
| 4203 | 5.1.3 Ámbito de aplicación del procedimiento ordinario | Familia | 100107 | 126 | 99,9 % | 794,5x |
| 4204 | 5.1.3.2 Posesión inscrita, derecho dominio | Judicial | 79146 | 75 | 99,9 % | 1055,3x |
| 4205 | 5.1.3.3 Por interpuesta demanda | Judicial | 79146 | 87 | 99,9 % | 909,7x |
| 4206 | 5.1.3.5 Consulta del estado de la causa | Judicial | 79146 | 50 | 99,9 % | 1582,9x |
| 4207 | 5.1.3.6 Resolución acuerdo en mediación familiar | Judicial | 79146 | 61 | 99,9 % | 1297,5x |
| 4208 | 5.1.3.7 Resolución demanda de cuidado personal | Judicial | 79146 | 65 | 99,9 % | 1217,6x |
| 4209 | 5.1.4 Reclamo por causa de privación o | Judicial | 105809 | 105 | 99,9 % | 1007,7x |
| 4210 | 5.1.4 Requisitos de admisibilidad de la demanda | Familia | 100107 | 131 | 99,9 % | 764,2x |
| 4211 | 5.1.5 Reclamos asociados al acto administrativo | Judicial | 105809 | 97 | 99,9 % | 1090,8x |
| 4212 | 5.1.6 Reclamo de ilegalidad de la | Judicial | 105809 | 83 | 99,9 % | 1274,8x |
| 4213 | 5.1.7 Reclamo para la determinación definitiva | Judicial | 105809 | 143 | 99,9 % | 739,9x |
| 4214 | 5.1.9 Frutos pendientes | Judicial | 105809 | 102 | 99,9 % | 1037,3x |
| 4215 | 5.10     Cuenta corriente | Laboral | 71986 | 45 | 99,9 % | 1599,7x |
| 4216 | 5.103               Mujeres | Judicial | 33208 | 35 | 99,9 % | 948,8x |
| 4217 | 5.2               La captación de registros a través de cámaras y | Judicial | 96536 | 53 | 99,9 % | 1821,4x |
| 4218 | 5.2         Ley 20.609, que establece medidas contra | Judicial | 87237 | 58 | 99,9 % | 1504,1x |
| 4219 | 5.2     Cosa | Familia | 65085 | 66 | 99,9 % | 986,1x |
| 4220 | 5.2     Marino de los Pueblos Originarios’ o ECMPO | Judicial | 134465 | 117 | 99,9 % | 1149,3x |
| 4221 | 5.2     Procedimiento para | Procesal | 94881 | 57 | 99,9 % | 1664,6x |
| 4222 | 5.2.1 Conceptos generales | Judicial | 79146 | 63 | 99,9 % | 1256,3x |
| 4223 | 5.2.1 El territorio | Laboral | 100583 | 98 | 99,9 % | 1026,4x |
| 4224 | 5.2.1 La Ley N° 20.249 en síntesis | Judicial | 134465 | 97 | 99,9 % | 1386,2x |
| 4225 | 5.2.1 Observando más de cerca | Constitucional | 121906 | 67 | 99,9 % | 1819,5x |
| 4226 | 5.2.1 Planificación de compras anuales | Laboral | 71986 | 106 | 99,9 % | 679,1x |
| 4227 | 5.2.1 Proactivo, no reactivo ni remedial | Constitucional | 104063 | 78 | 99,9 % | 1334,1x |
| 4228 | 5.2.1.1 Considerando tercero | Constitucional | 121906 | 101 | 99,9 % | 1207,0x |
| 4229 | 5.2.1.2 Considerando cuarto | Constitucional | 121906 | 66 | 99,9 % | 1847,1x |
| 4230 | 5.2.1.3 Considerando quinto | Constitucional | 121906 | 93 | 99,9 % | 1310,8x |
| 4231 | 5.2.1.4 Considerando sexto | Constitucional | 121906 | 128 | 99,9 % | 952,4x |
| 4232 | 5.2.1.5 Considerando séptimo | Constitucional | 121906 | 72 | 99,9 % | 1693,1x |
| 4233 | 5.2.1.6 Considerando octavo | Constitucional | 121906 | 70 | 99,9 % | 1741,5x |
| 4234 | 5.2.2 Adquisiciones | Laboral | 71986 | 98 | 99,9 % | 734,6x |
| 4235 | 5.2.2 Competencia territorial de un tribunal del trabajo | Laboral | 100583 | 122 | 99,9 % | 824,5x |
| 4236 | 5.2.2 Criterios de redacción | Judicial | 79146 | 104 | 99,9 % | 761,0x |
| 4237 | 5.2.2 El ECMPO | Judicial | 134465 | 75 | 99,9 % | 1792,9x |
| 4238 | 5.2.2 Integración diaria | Judicial | 44331 | 61 | 99,9 % | 726,7x |
| 4239 | 5.2.2 Privacidad como configuración | Constitucional | 104063 | 83 | 99,9 % | 1253,8x |
| 4240 | 5.2.2. Obligación de proveer al mandatario de lo necesario para la ejecución del | Civil | 42773 | 50 | 99,9 % | 855,5x |
| 4241 | 5.2.2.1 Prórroga de la competencia: se refiere a la posibilidad de | Laboral | 100583 | 100 | 99,9 % | 1005,8x |
| 4242 | 5.2.2.2 Efecto de la incompetencia relativa: cuando se declara | Laboral | 100583 | 135 | 99,9 % | 745,1x |
| 4243 | 5.2.2.3 Oportunidad de la incompetencia relativa: la declara- | Laboral | 100583 | 100 | 99,9 % | 1005,8x |
| 4244 | 5.2.3 A quiénes aplica | Judicial | 134465 | 118 | 99,9 % | 1139,5x |
| 4245 | 5.2.3 Competencia material de un tribunal del trabajo | Laboral | 100583 | 84 | 99,9 % | 1197,4x |
| 4246 | 5.2.3 Etapas de las actas judiciales | Judicial | 79146 | 89 | 99,9 % | 889,3x |
| 4247 | 5.2.3. Obligación de reembolsar al mandatario los gastos razonables causados por | Civil | 42773 | 52 | 99,9 % | 822,6x |
| 4248 | 5.2.3.1 Artículo 420 letra a): serán de competencia de los JLT | Laboral | 100583 | 98 | 99,9 % | 1026,4x |
| 4249 | 5.2.3.2 Artículo 420 letra b): “Las cuestiones derivadas de la | Laboral | 100583 | 120 | 99,9 % | 838,2x |
| 4250 | 5.2.3.4 Artículo 420 letra d): “Los juicios en que se demande el | Laboral | 100583 | 84 | 99,9 % | 1197,4x |
| 4251 | 5.2.3.5 Artículo 420 letra e): “Las reclamaciones que procedan | Laboral | 100583 | 87 | 99,9 % | 1156,1x |
| 4252 | 5.2.3.6 Artículo 420 letra f): “Los juicios iniciados por el propio | Laboral | 100583 | 126 | 99,9 % | 798,3x |
| 4253 | 5.2.3.7 Artículo 420 letra g): “Todas aquellas materias que las | Laboral | 100583 | 71 | 99,9 % | 1416,7x |
| 4254 | 5.2.3.8 Efecto de la incompetencia absoluta: cuando se declara | Laboral | 100583 | 131 | 99,9 % | 767,8x |
| 4255 | 5.2.3.9 Oportunidad en que se declara la incompetencia | Laboral | 100583 | 120 | 99,9 % | 838,2x |
| 4256 | 5.2.4 Modelos de actas judiciales | Judicial | 79146 | 74 | 99,9 % | 1069,5x |
| 4257 | 5.2.4 Normas de discriminación positiva | Judicial | 134465 | 92 | 99,9 % | 1461,6x |
| 4258 | 5.2.5 Ley N° 20.249, Convenio y concepto | Judicial | 134465 | 106 | 99,9 % | 1268,5x |
| 4259 | 5.2.5. Obligación de pagar al mandatario las anticipaciones de dinero, más los | Civil | 42773 | 62 | 99,9 % | 689,9x |
| 4260 | 5.2.6 Ley N° 20.249, ECMPO y Convenio | Judicial | 134465 | 96 | 99,9 % | 1400,7x |
| 4261 | 5.2.6. Obligación de indemnizar al mandatario de las pérdidas en que haya | Civil | 42773 | 58 | 99,9 % | 737,5x |
| 4262 | 5.3          Generalidades | Civil | 142015 | 119 | 99,9 % | 1193,4x |
| 4263 | 5.3     Ley 20.830, sobre acuerdo de unión | Judicial | 87237 | 94 | 99,9 % | 928,1x |
| 4264 | 5.3    Revocabilidad | Judicial | 64632 | 49 | 99,9 % | 1319,0x |
| 4265 | 5.3.1 Caso Siemens (Alemania) | Constitucional | 112823 | 89 | 99,9 % | 1267,7x |
| 4266 | 5.3.1 La evaluación ambiental | Judicial | 134465 | 91 | 99,9 % | 1477,6x |
| 4267 | 5.3.1 Página web del Poder Judicial | Judicial | 52128 | 68 | 99,9 % | 766,6x |
| 4268 | 5.3.1 Requisitos de la revocabilidad subjetiva | Judicial | 64632 | 66 | 99,9 % | 979,3x |
| 4269 | 5.3.2 Caso Acreditación de | Constitucional | 112823 | 81 | 99,9 % | 1392,9x |
| 4270 | 5.3.2 El sancionatorio ambiental | Judicial | 134465 | 89 | 99,9 % | 1510,8x |
| 4271 | 5.3.2 Los materiales jurídicos y la interpretación | Constitucional | 121906 | 106 | 99,9 % | 1150,1x |
| 4272 | 5.3.2.1 Técnicas de interpretación | Constitucional | 121906 | 117 | 99,9 % | 1041,9x |
| 4273 | 5.3.3 Caso Corpesca | Constitucional | 112823 | 78 | 99,9 % | 1446,4x |
| 4274 | 5.3.3 La  tutela     jurisdiccional    en   los | Judicial | 134465 | 158 | 99,9 % | 851,0x |
| 4275 | 5.3.4 Razonamiento con principios | Constitucional | 121906 | 100 | 99,9 % | 1219,1x |
| 4276 | 5.3.4.1 Pasos para especificar un principio | Constitucional | 121906 | 104 | 99,9 % | 1172,2x |
| 4277 | 5.3.4.2 Conflictos entre principios y ponderación | Constitucional | 121906 | 104 | 99,9 % | 1172,2x |
| 4278 | 5.3.4.3 Los principios en los casos de discapacidad | Constitucional | 121906 | 94 | 99,9 % | 1296,9x |
| 4279 | 5.3.5 Razonamiento probatorio | Constitucional | 121906 | 109 | 99,9 % | 1118,4x |
| 4280 | 5.3.5.1 La prueba en casos de discapacidad | Constitucional | 121906 | 137 | 99,9 % | 889,8x |
| 4281 | 5.4     Pascua y otras normas especiales sobre Rapa Nui | Judicial | 134465 | 140 | 99,9 % | 960,5x |
| 4282 | 5.4   Ley 21.120, que reconoce y da protección al derecho | Judicial | 87237 | 66 | 99,9 % | 1321,8x |
| 4283 | 5.4   Licitación | Laboral | 71986 | 37 | 99,9 % | 1945,6x |
| 4284 | 5.4   Revocabilidad y las reformas a los | Judicial | 64632 | 59 | 99,9 % | 1095,5x |
| 4285 | 5.4.1 Constitución del tribunal en | Familia | 100107 | 85 | 99,9 % | 1177,7x |
| 4286 | 5.4.1 El lenguaje claro como propósito | Constitucional | 121906 | 118 | 99,9 % | 1033,1x |
| 4287 | 5.4.1 La Ley Nº 16.441, que crea el | Judicial | 134465 | 131 | 99,9 % | 1026,5x |
| 4288 | 5.4.2 Ley Nº 21.070, que regula el ejercicio de los | Judicial | 134465 | 114 | 99,9 % | 1179,5x |
| 4289 | 5.4.2 Objetivo | Familia | 100107 | 72 | 99,9 % | 1390,4x |
| 4290 | 5.4.3 Estructura de las sentencias | Constitucional | 121906 | 92 | 99,9 % | 1325,1x |
| 4291 | 5.4.4 Audiencia de NNA | Familia | 100107 | 110 | 99,9 % | 910,1x |
| 4292 | 5.4.4 Recomendaciones de uso de lenguaje | Constitucional | 121906 | 93 | 99,9 % | 1310,8x |
| 4293 | 5.4.5 Contenido de la resolución que cita a juicio | Familia | 100107 | 113 | 99,9 % | 885,9x |
| 4294 | 5.5              Videovigilancia como medio para obtener | Judicial | 96536 | 71 | 99,9 % | 1359,7x |
| 4295 | 5.5         Situación de los órganos excluidos del | Civil | 142015 | 104 | 99,9 % | 1365,5x |
| 4296 | 5.5     Licitación | Laboral | 71986 | 42 | 99,9 % | 1714,0x |
| 4297 | 5.5     Material complementario | Constitucional | 121906 | 76 | 99,9 % | 1604,0x |
| 4298 | 5.5    Revocación de actos ejecutados o contratos | Judicial | 64632 | 55 | 99,9 % | 1175,1x |
| 4299 | 5.5   Normativa sectorial sobre recursos naturales, con particular referencia a la que es aplicada | Judicial | 134465 | 87 | 99,9 % | 1545,6x |
| 4300 | 5.5.1 Constitución del tribunal | Familia | 100107 | 101 | 99,9 % | 991,2x |
| 4301 | 5.5.1 Código de Minería, concesiones | Judicial | 134465 | 135 | 99,9 % | 996,0x |
| 4302 | 5.5.2 Las aguas y los pueblos indígenas | Judicial | 134465 | 97 | 99,9 % | 1386,2x |
| 4303 | 5.5.2 Objetivo | Familia | 100107 | 89 | 99,9 % | 1124,8x |
| 4304 | 5.5.2.1 El Código de Aguas y los usos ‘ancestrales’ | Judicial | 134465 | 158 | 99,9 % | 851,0x |
| 4305 | 5.5.3 Desarrollo de la audiencia de juicio | Familia | 100107 | 127 | 99,9 % | 788,2x |
| 4306 | 5.5.4 Apertura del juicio oral | Familia | 100107 | 109 | 99,9 % | 918,4x |
| 4307 | 5.5.5 Recepción de la prueba | Familia | 100107 | 78 | 99,9 % | 1283,4x |
| 4308 | 5.6     Documentación recibida y | Judicial | 52128 | 42 | 99,9 % | 1241,1x |
| 4309 | 5.6.1 Normativa sectorial doméstica | Judicial | 134465 | 102 | 99,9 % | 1318,3x |
| 4310 | 5.6.1 Relevancia, idoneidad y proporcionalidad | Judicial | 96536 | 79 | 99,9 % | 1222,0x |
| 4311 | 5.6.1 Resolución o decisión | Familia | 100107 | 104 | 99,9 % | 962,6x |
| 4312 | 5.6.2 El patrimonio cultural indígena en la | Judicial | 134465 | 81 | 99,9 % | 1660,1x |
| 4313 | 5.6.2 Prohibiciones probatorias y | Judicial | 96536 | 75 | 99,9 % | 1287,1x |
| 4314 | 5.6.2 Radicación de la causa en el (la) juez(a) | Familia | 100107 | 122 | 99,9 % | 820,5x |
| 4315 | 5.7     Compra | Laboral | 71986 | 37 | 99,9 % | 1945,6x |
| 4316 | 5.7   Recursos | Judicial | 64632 | 83 | 99,9 % | 778,7x |
| 4317 | 5.7.1 Orientaciones sobre el uso del | Laboral | 71986 | 102 | 99,9 % | 705,7x |
| 4318 | 5.7.1 Requisitos de la parte expositiva | Familia | 100107 | 124 | 99,9 % | 807,3x |
| 4319 | 5.7.1 Salud y autodeterminación | Judicial | 134465 | 105 | 99,9 % | 1280,6x |
| 4320 | 5.7.2    Educación | Judicial | 134465 | 93 | 99,9 % | 1445,9x |
| 4321 | 5.7.2 Directrices para el uso del | Laboral | 71986 | 100 | 99,9 % | 719,9x |
| 4322 | 5.7.3 Requisitos de la parte resolutiva | Familia | 100107 | 115 | 99,9 % | 870,5x |
| 4323 | 5.8 Costas y recompensas                                                            151 | Judicial | 64632 | 49 | 99,9 % | 1319,0x |
| 4324 | 5.8.1 Administración de la bodega y su resguardo | Laboral | 71986 | 93 | 99,9 % | 774,0x |
| 4325 | 5.8.1.2 Bodega de materiales | Laboral | 71986 | 102 | 99,9 % | 705,7x |
| 4326 | 5.8.1.3 Salida de materiales | Laboral | 71986 | 92 | 99,9 % | 782,5x |
| 4327 | 5.8.1.4 Control de inventarios | Laboral | 71986 | 107 | 99,9 % | 672,8x |
| 4328 | 5.8.2 Dirección y control de activo fijo y equipos críticos | Laboral | 71986 | 91 | 99,9 % | 791,1x |
| 4329 | 5.8.2.1 Recepción de bienes | Laboral | 71986 | 63 | 99,9 % | 1142,6x |
| 4330 | 5.8.2.2 Ubicación de bienes | Laboral | 71986 | 74 | 99,9 % | 972,8x |
| 4331 | 5.8.2.3 Salida o traslado de bienes | Laboral | 71986 | 102 | 99,9 % | 705,7x |
| 4332 | 5.8.2.4 Control de inventarios de activo fijo | Laboral | 71986 | 107 | 99,9 % | 672,8x |
| 4333 | 5.8.3 Recaudación, custodia y depósito | Laboral | 71986 | 87 | 99,9 % | 827,4x |
| 4334 | 5.8.4 Gestión de requerimientos | Laboral | 71986 | 92 | 99,9 % | 782,5x |
| 4335 | 5.8.5 Control de la gestión de las | Laboral | 71986 | 88 | 99,9 % | 818,0x |
| 4336 | 5.9.1 Planilla de control | Laboral | 71986 | 107 | 99,9 % | 672,8x |
| 4337 | 5.9.3 Copia cedible | Laboral | 71986 | 107 | 99,9 % | 672,8x |
| 4338 | 50 Artículo 453 número 8 inciso cuarto del Código del Trabajo, artículo 46 de | Procesal | 86112 | 117 | 99,9 % | 736,0x |
| 4339 | 50 Así, con respecto a la especial protección de la niñez migrante, es esencial la | Constitucional | 177323 | 122 | 99,9 % | 1453,5x |
| 4340 | 50 Aunque el reenvío en los otros procedimientos reformados es al artículo 315 del | Procesal | 86112 | 68 | 99,9 % | 1266,4x |
| 4341 | 50 Debe advertirse que, sin embargo, la ley omitió mandatar a algún organismo | Penal | 178516 | 102 | 99,9 % | 1750,2x |
| 4342 | 50 Información provista por la Comisión de Probidad y Transparencia, «¿Qué | Penal | 178516 | 156 | 99,9 % | 1144,3x |
| 4343 | 50 Larrauri (1994: 1) agrega: «cuando se afirma que el derecho, y en el caso que | Judicial | 150341 | 101 | 99,9 % | 1488,5x |
| 4344 | 50 Para más información, véase Declaración Universal de los Derechos Humanos | Constitucional | 177323 | 118 | 99,9 % | 1502,7x |
| 4345 | 50. CONTRERAS, Pablo (2009), Poder privado y | Laboral | 113458 | 98 | 99,9 % | 1157,7x |
| 4346 | 50. GAUCHÉ, Ximena (2014): “Análisis crítico de la ley N° 20.609, que establece | Judicial | 81476 | 106 | 99,9 % | 768,6x |
| 4347 | 503 CT (ya que resultan incompatibles ambas reclamaciones) y sólo | Laboral | 100583 | 80 | 99,9 % | 1257,3x |
| 4348 | 51 Adoptada por Resolución 34/180 de 18 de diciembre de 1979 por la Asamblea | Familia | 123490 | 96 | 99,9 % | 1286,4x |
| 4349 | 51 COT; y | Procesal | 94881 | 89 | 99,9 % | 1066,1x |
| 4350 | 51 Estos autores reparan en que muchas veces los tribunales sancionan al particular | Penal | 178516 | 140 | 99,9 % | 1275,1x |
| 4351 | 51 Los artículos 49 de la Ley 19.968 que crea los Tribunales de Familia, 453 número | Procesal | 86112 | 102 | 99,9 % | 844,2x |
| 4352 | 51 Paradojalmente, toda la teoría de la prueba ilícita por infracción de garantías | Procesal | 86112 | 96 | 99,9 % | 897,0x |
| 4353 | 51.   IRARRÁZAVAL, Cristián (2017): “Minuta sobre las modificaciones introduci- | Familia | 95131 | 85 | 99,9 % | 1119,2x |
| 4354 | 51. GAUCHÉ, Ximena y LOVERA, Domingo (2019): “Identidad de género de | Judicial | 81476 | 76 | 99,9 % | 1072,1x |
| 4355 | 52 Alicia E. Yamin y otros (2013: 137-138) mencionan como ejemplos la atención | Judicial | 81675 | 58 | 99,9 % | 1408,2x |
| 4356 | 52 Boletín 3.407-07 de 2003, que se trataba de un Mensaje presentado como fruto | Penal | 178516 | 127 | 99,9 % | 1405,6x |
| 4357 | 52 Las dificultades pueden deberse a la acreditación de elementos subjetivos o la | Penal | 178516 | 167 | 99,9 % | 1069,0x |
| 4358 | 52 OEA MESICIC, «Informe final», 28. Respecto de esta materia, cabe destacar | Penal | 178516 | 163 | 99,9 % | 1095,2x |
| 4359 | 52 Para más información, véase Declaración Universal de los Derechos Humanos | Constitucional | 177323 | 106 | 99,9 % | 1672,9x |
| 4360 | 52 Sentencia Tribunal Constitucional 1368, de 18 de mayo de 2010 y sentencia | Judicial | 144656 | 156 | 99,9 % | 927,3x |
| 4361 | 52 Véase las Reglas de La Habana (números 72, 73 y 74), la Observación General | Penal | 86906 | 52 | 99,9 % | 1671,3x |
| 4362 | 52. CORREA, Rodrigo (2004), “En defensa de una | Laboral | 113458 | 104 | 99,9 % | 1090,9x |
| 4363 | 52. El artículo 25 de la Convención también consagra el derecho de | Judicial | 144656 | 75 | 99,9 % | 1928,7x |
| 4364 | 52. GRACIA, Jorge (2011): Los derechos humanos y la posición social de las | Judicial | 81476 | 79 | 99,9 % | 1031,3x |
| 4365 | 52. HENRÍQUEZ, Ian (2006): “La regla de la ventaja para el concebido y el | Constitucional | 121906 | 88 | 99,9 % | 1385,3x |
| 4366 | 52. MADDALENO, Matilde; SCHUTT–AINE, Jessie | Judicial | 89476 | 94 | 99,9 % | 951,9x |
| 4367 | 53 Acertadamente, la ley estableció una implementación gradual, que sirvió para | Penal | 178516 | 159 | 99,9 % | 1122,7x |
| 4368 | 53 Al respecto, véase Gardner y Anderson (2013: 483). Para estos autores Frye test | Judicial | 150341 | 89 | 99,9 % | 1689,2x |
| 4369 | 53 Para más información, véase Declaración Universal de los Derechos Humanos | Constitucional | 177323 | 135 | 99,9 % | 1313,5x |
| 4370 | 53 Sentencia Tribunal Constitucional 1994, de 26 de abril de 2012. En el mismo | Judicial | 144656 | 83 | 99,9 % | 1742,8x |
| 4371 | 53 Véase el artículo 40.4 de la Convención de los Derechos del Niño y las reglas | Penal | 86906 | 100 | 99,9 % | 869,1x |
| 4372 | 53. CORTE SUPREMA, rol N° 9.420-2010, de veintiu- | Familia | 65085 | 84 | 99,9 % | 774,8x |
| 4373 | 54 Llama la atención que siendo el quebrantamiento lo que el tribunal tiene que | Penal | 86906 | 106 | 99,9 % | 819,9x |
| 4374 | 54 Para más información, véase Poder Judicial (2021b: 11). También destaca que | Constitucional | 177323 | 114 | 99,9 % | 1555,5x |
| 4375 | 54.   LARRAURI, Elena (2009): “Igualdad y violencia de género, Comentario a la | Familia | 95131 | 61 | 99,9 % | 1559,5x |
| 4376 | 54. CORTE SUPREMA, rol N° 353-11, de veintiocho | Familia | 65085 | 83 | 99,9 % | 784,2x |
| 4377 | 54. GÓMEZ BERNALES, Gastón, (2001): “El principio de igualdad constitucio- | Judicial | 81476 | 65 | 99,9 % | 1253,5x |
| 4378 | 54. MARTENS, Sebastian y WILLENS, Constantine | Civil | 142015 | 101 | 99,9 % | 1406,1x |
| 4379 | 54.1 Constitución), es claro que el Tribunal Constitucional carece de | Judicial | 134465 | 107 | 99,9 % | 1256,7x |
| 4380 | 55   BRANTT (2017), p. 507; PIZARRO (2017), p. 107. El contrato se perfecciona por el sólo consentimiento. Sin | Civil | 142015 | 85 | 99,9 % | 1670,8x |
| 4381 | 55 Artículos 429 y 453 número 9 del Código del Trabajo y artículos 29 y 61 número | Procesal | 86112 | 71 | 99,9 % | 1212,8x |
| 4382 | 55 El Código Civil no se pronuncia sobre la sanción en caso de actuación de la | Familia | 123490 | 107 | 99,9 % | 1154,1x |
| 4383 | 55 En los requisitos de la sentencia definitiva, atento a lo prevenido en el artículo | Procesal | 86112 | 85 | 99,9 % | 1013,1x |
| 4384 | 55 Puede cuestionarse que se incluya a estos últimos, considerando que las bases de | Penal | 178516 | 150 | 99,9 % | 1190,1x |
| 4385 | 55 Pues se trataba de niños sometidos a apremios ilegítimos. Así lo concluyó la | Judicial | 81675 | 102 | 99,9 % | 800,7x |
| 4386 | 55 Sentencia de la Corte Interamericana de Derechos Humanos, 16 de noviembre | Judicial | 150341 | 76 | 99,9 % | 1978,2x |
| 4387 | 55 Véase el artículo 40.3 y 40.4 de la Convención de los Derechos del Niño, la regla | Penal | 86906 | 120 | 99,9 % | 724,2x |
| 4388 | 55. CS, reclamo de ilegalidad “Bienes Raíces e Inver- | Judicial | 105809 | 133 | 99,9 % | 795,6x |
| 4389 | 55. HERRERO, Sara (2016): “Formalización del concepto de salud a través de | Constitucional | 121906 | 78 | 99,9 % | 1562,9x |
| 4390 | 55. Lesiones psíquicas graves | Familia | 95131 | 97 | 99,9 % | 980,7x |
| 4391 | 56 Se configura una excepción al artículo 1754 del Código Civil en cuanto prohíbe | Familia | 123490 | 115 | 99,9 % | 1073,8x |
| 4392 | 56 Sentencia de la Corte Suprema, 20 de septiembre de 2018, rol 2455-2018. La | Familia | 123490 | 100 | 99,9 % | 1234,9x |
| 4393 | 56. ÍÑIGUEZ, Andrea (2014): La noción de «categoría sospechosa» y el | Judicial | 81476 | 71 | 99,9 % | 1147,5x |
| 4394 | 57 Correctamente se ha puesto en duda que sea posible fundamentar esta especial | Penal | 178516 | 150 | 99,9 % | 1190,1x |
| 4395 | 57 Por el reenvío del artículo 496 del Código del Trabajo al artículo 201 del mismo | Procesal | 86112 | 126 | 99,9 % | 683,4x |
| 4396 | 57 Según Espinoza (1980: 153) procederá el recurso de casación en la forma si se | Judicial | 144656 | 94 | 99,9 % | 1538,9x |
| 4397 | 57.   CHAPMAN, Anna (2002), “Vie privée et survei- | Laboral | 113458 | 71 | 99,9 % | 1598,0x |
| 4398 | 57. No habrá, pues, discriminación si una distinción de tratamiento | Judicial | 87237 | 88 | 99,9 % | 991,3x |
| 4399 | 58   CORREA, Rodrigo (2004), “En defensa de una aplicación exclusivamente vertical de los derechos constitu- | Laboral | 113458 | 128 | 99,9 % | 886,4x |
| 4400 | 58   Ciertamente, en materia de niños, niñas y adolescentes hay mucho trabajo por hacer. Nuestro país está al | Penal | 211066 | 119 | 99,9 % | 1773,7x |
| 4401 | 58 Agregado por Ley 20.239, de 8 de febrero de 2007. Conforme al artículo 2 de | Familia | 123490 | 141 | 99,9 % | 875,8x |
| 4402 | 58 Ello supone, la aplicación —en lo que fuere pertinente— de los artículos 390 | Familia | 123490 | 107 | 99,9 % | 1154,1x |
| 4403 | 58 No era necesario señalarlo, pues como se indicó, se encuentra expresamente | Penal | 178516 | 141 | 99,9 % | 1266,1x |
| 4404 | 58 Para García y Contreras (2013: 267), el derecho a una adecuada defensa implica | Judicial | 144656 | 79 | 99,9 % | 1831,1x |
| 4405 | 58. JENKINS, Gaspar (2020): “La acción de no discriminación arbitraria a la | Judicial | 81476 | 65 | 99,9 % | 1253,5x |
| 4406 | 58. RIT VD-04-00005-2010 (TTA Magallanes, de 25 | Judicial | 105809 | 75 | 99,9 % | 1410,8x |
| 4407 | 59 Algunos comentarios sobre esta norma de protección de intereses de terceros | Familia | 123490 | 81 | 99,9 % | 1524,6x |
| 4408 | 59 En reportaje de La Tercera del 21 de septiembre de 2019, se relata que el director | Penal | 178516 | 122 | 99,9 % | 1463,2x |
| 4409 | 6            Si el delito está consumado, es frustrado o tentado, o se trata de una | Penal | 194788 | 106 | 99,9 % | 1837,6x |
| 4410 | 6   PLÁ la denomina renuncia a beneficios ya devengados, que se han convertido en verdaderos derechos de | Laboral | 100583 | 100 | 99,9 % | 1005,8x |
| 4411 | 6 Actualmente este trámite debe realizarse en línea por el empleador a través del | Laboral | 98828 | 79 | 99,9 % | 1251,0x |
| 4412 | 6 Albrecht señala que pese a la «trivialidad de esta tautología, ésta se pierde de | Penal | 86906 | 96 | 99,9 % | 905,3x |
| 4413 | 6 Carbonell (2013: 222) destaca que «la legislación nacional no solo debe ser no | Judicial | 81675 | 79 | 99,9 % | 1033,9x |
| 4414 | 6 El artículo 14 de la Ley 20.830 también establece que los convivientes estarán | Familia | 123490 | 132 | 99,9 % | 935,5x |
| 4415 | 6 El código Sanitario Panamericano fue suscrito en La Habana, Cuba, el 14 de | Judicial | 87950 | 89 | 99,9 % | 988,2x |
| 4416 | 6 En contra, Rodríguez Collao y Ossandón Widow (2021: 443), para quienes el | Penal | 178516 | 114 | 99,9 % | 1565,9x |
| 4417 | 6 En este sentido Cheng y Holyoak (1985: 395) afirman que: «a syntactically based | Judicial | 150341 | 81 | 99,9 % | 1856,1x |
| 4418 | 6 En la 23.ª edición de 2014 se eliminaron las acepciones de «alteración o vicio | Penal | 178516 | 119 | 99,9 % | 1500,1x |
| 4419 | 6 Este tipo de medidas se entienden de ultima ratio, es decir, que son aplicadas | Familia | 97488 | 79 | 99,9 % | 1234,0x |
| 4420 | 6 Felipe Díaz, «Operación Huracán: peritaje de experto contradice versión de | Procesal | 86112 | 66 | 99,9 % | 1304,7x |
| 4421 | 6 Historia de la Ley 21.220, que modifica el Código del Trabajo en materia de | Laboral | 98828 | 72 | 99,9 % | 1372,6x |
| 4422 | 6 La doctora Elena Larrauri (2002) realiza un análisis del derecho penal en este | Penal | 86906 | 49 | 99,9 % | 1773,6x |
| 4423 | 6 Las citas corresponden, respectivamente, al Cuaderno de buenas prácticas… | Judicial | 92792 | 123 | 99,9 % | 754,4x |
| 4424 | 6 N° 1 letra a) y N° 2, en relación con el Decreto N° 66 de 15 | Judicial | 134465 | 119 | 99,9 % | 1130,0x |
| 4425 | 6 Para una exposición más detallada de estos principios véanse, entre otros, Searle | Judicial | 92792 | 92 | 99,9 % | 1008,6x |
| 4426 | 6 Se realiza según el «Convenio sobre Protocolo interinstitucional de constatación | Judicial | 78893 | 101 | 99,9 % | 781,1x |
| 4427 | 6 Se trata del caso con mayor impacto mediático y político para la época, que | Penal | 178516 | 175 | 99,9 % | 1020,1x |
| 4428 | 6 Segundo Juzgado de Letras del Trabajo de Santiago, RIT 1218-2019, 21 de abril | Laboral | 53374 | 55 | 99,9 % | 970,4x |
| 4429 | 6 Sentencia del caso Martín Calderón Leyton contra Sindicato Forjadores de Ferias | Laboral | 74025 | 62 | 99,9 % | 1194,0x |
| 4430 | 6 Sin embargo, existen pronunciamientos judiciales en dicho sentido: «Que el | Familia | 123490 | 178 | 99,9 % | 693,8x |
| 4431 | 6 Sobre el parangón detallado de la prueba pericial entre el modelo anglosajón y el | Procesal | 86112 | 57 | 99,9 % | 1510,7x |
| 4432 | 6 También ha sido utilizado por Vernengo, que la define como «la practicada por | Judicial | 92792 | 62 | 99,9 % | 1496,6x |
| 4433 | 6 Vásquez Sotelo (1984: 453) comenta: «Pero el paso hacia el nuevo sistema era | Judicial | 150341 | 169 | 99,9 % | 889,6x |
| 4434 | 6.    Acto administrativo: acto jurídico emitido por | Judicial | 105809 | 109 | 99,9 % | 970,7x |
| 4435 | 6.    BARAONA, Jorge (1997): “Responsabilidad | Civil | 142015 | 102 | 99,9 % | 1392,3x |
| 4436 | 6.    FERNÁNDEZ G., Miguel Ángel (2001): “La nacio-         15. PFEFFER U., Emilio (2000): “Naturaleza, carac- | Judicial | 105809 | 120 | 99,9 % | 881,7x |
| 4437 | 6.    Ley N° 19.585. Modifica el Código Civil y otros | Judicial | 89476 | 58 | 99,9 % | 1542,7x |
| 4438 | 6.    Ley Nº 19.759, que modifica el Código del Tra-           cedimiento de Tutela Laboral y Procedimiento | Laboral | 113458 | 135 | 99,9 % | 840,4x |
| 4439 | 6.    Ley Nº 20.480, modifica el Código Penal y la Ley Nº 20.066 sobre violencia | Familia | 95131 | 84 | 99,9 % | 1132,5x |
| 4440 | 6.   CS, 31 de mayo de 2006, “Thunderbird Antofa- | Judicial | 105809 | 122 | 99,9 % | 867,3x |
| 4441 | 6.   Comité Jurídico Interamericano. Resolución Nº | Administrativo | 89720 | 97 | 99,9 % | 924,9x |
| 4442 | 6.   Corte Constitucional de Colombia, Revisión de la Ley 742 del 5 de junio | Penal | 121924 | 107 | 99,9 % | 1139,5x |
| 4443 | 6.   Las guardas, con excepción de aquellas relativas a pupilos mayores de edad y aquellas | Familia | 100107 | 141 | 99,9 % | 710,0x |
| 4444 | 6. Acuerdos de las asambleas de copropietarios | Civil | 192585 | 153 | 99,9 % | 1258,7x |
| 4445 | 6. Al tribunal se le otorga un presupuesto anual cuya gestión está | Judicial | 52128 | 67 | 99,9 % | 778,0x |
| 4446 | 6. Brindar a las personas con discapacidad visual, una explicación | Constitucional | 177323 | 117 | 99,9 % | 1515,6x |
| 4447 | 6. Capacitación en materia de Derechos Humanos y Empresas a las | Constitucional | 177323 | 159 | 99,9 % | 1115,2x |
| 4448 | 6. Comisión Interamericana de Derechos Humanos. Estándares | Judicial | 87237 | 67 | 99,9 % | 1302,0x |
| 4449 | 6. Considerar que las personas mayores, en razón de su edad, pueden | Constitucional | 177323 | 119 | 99,9 % | 1490,1x |
| 4450 | 6. Cualquier otro título a que las leyes laborales o de seguridad | Laboral | 100583 | 61 | 99,9 % | 1648,9x |
| 4451 | 6. Determinar el objeto del juicio. El objeto del juicio no lo aclara | Familia | 100107 | 106 | 99,9 % | 944,4x |
| 4452 | 6. Dirección de Estudios Corte Suprema (2018). “Análisis Estadís- | Judicial | 87237 | 87 | 99,9 % | 1002,7x |
| 4453 | 6. Efectividad de que el/la demandante posee una discapacidad, esto | Constitucional | 121906 | 118 | 99,9 % | 1033,1x |
| 4454 | 6. Eficiencia: la persona jurídica debe emplear adecuadamente | Penal | 119528 | 87 | 99,9 % | 1373,9x |
| 4455 | 6. Elaboración de diversos estudios que permiten conocer la realidad | Judicial | 81476 | 111 | 99,9 % | 734,0x |
| 4456 | 6. En caso de expulsión, el interesado tendrá oportunidad razonable, antes o después de la partida, para | Constitucional | 115835 | 152 | 99,9 % | 762,1x |
| 4457 | 6. Entrega de las copias. La entrega de las copias a que se refiere el | Judicial | 89450 | 107 | 99,9 % | 836,0x |
| 4458 | 6. Establecer mecanismos legítimos o cooperar mediante estos | Constitucional | 112823 | 72 | 99,9 % | 1567,0x |
| 4459 | 6. Exención de los menores de 18 años. La Corte no es competente | Penal | 121924 | 76 | 99,9 % | 1604,3x |
| 4460 | 6. Formación de funcionarios/as públicos en derechos humanos (ID | Constitucional | 177323 | 96 | 99,9 % | 1847,1x |
| 4461 | 6. Igualdad de la calidad de hijos: un gran paso formal y de fondo, afirma el profesor | Familia | 190697 | 180 | 99,9 % | 1059,4x |
| 4462 | 6. Informar a las y los notificadores que la persona a notificar tiene | Constitucional | 177323 | 102 | 99,9 % | 1738,5x |
| 4463 | 6. Intolerancia es el acto o conjunto de actos o manifestaciones que | Judicial | 93914 | 107 | 99,9 % | 877,7x |
| 4464 | 6. La gravedad de las consecuencias sociales y económicas o, en su | Penal | 194788 | 107 | 99,9 % | 1820,4x |
| 4465 | 6. La incorporación de modelos de plantillas de resoluciones | Procesal | 94881 | 71 | 99,9 % | 1336,4x |
| 4466 | 6. La migración irregular, el ingreso clandestino y otras | Constitucional | 115835 | 109 | 99,9 % | 1062,7x |
| 4467 | 6. La subordinación y el término anticipado de la misma, son actos solemnes. Podrá | Civil | 120848 | 81 | 99,9 % | 1492,0x |
| 4468 | 6. Las guardas, con excepción de aquellas relativas a pupilos mayores de edad, y | Familia | 190697 | 183 | 99,9 % | 1042,1x |
| 4469 | 6. Las personas de edad con 1. Mantenimiento de una capacidad funcional | Judicial | 82507 | 70 | 99,9 % | 1178,7x |
| 4470 | 6. Ley N° 19.585. Modifica el Código Civil y otros cuerpos legales | Judicial | 89476 | 65 | 99,9 % | 1376,6x |
| 4471 | 6. Los adultos tienen responsabilidad respecto de los | Familia | 100107 | 71 | 99,9 % | 1410,0x |
| 4472 | 6. Mejorar procedimientos penitenciarios sobre regulación y uso de | Constitucional | 177323 | 135 | 99,9 % | 1313,5x |
| 4473 | 6. Ninguna disposición de este artículo autoriza a los Estados | Laboral | 100583 | 113 | 99,9 % | 890,1x |
| 4474 | 6. Opiniones de terceros: en virtud de este principio, el mediador velará para que se | Familia | 190697 | 102 | 99,9 % | 1869,6x |
| 4475 | 6. Proceso de adecuación y modificaciones normativas sectoriales | Judicial | 89476 | 72 | 99,9 % | 1242,7x |
| 4476 | 6. Prohibición de establecer leyes penales en blanco, art. 19 Nº | Procesal | 94881 | 49 | 99,9 % | 1936,3x |
| 4477 | 6. Promover la más amplia participación de la sociedad civil y de | Judicial | 82507 | 83 | 99,9 % | 994,1x |
| 4478 | 6. Que expuesta así la controversia, resulta necesario examinar la legalidad de la | Civil | 192585 | 204 | 99,9 % | 944,0x |
| 4479 | 6. Que por último, cabe señalar que si bien la decisión de otorgar be- | Penal | 194788 | 162 | 99,9 % | 1202,4x |
| 4480 | 6. Que, en consecuencia, en este caso la Comisión recurrida ha ejerci- | Penal | 194788 | 197 | 99,9 % | 988,8x |
| 4481 | 6. Que, en el orden referido, las Convenciones suscritas por Chile en | Penal | 194788 | 172 | 99,9 % | 1132,5x |
| 4482 | 6. Que, esta asignación de sentido se encuentra más acorde con los | Penal | 194788 | 141 | 99,9 % | 1381,5x |
| 4483 | 6. Que, la justificación de la institución de la prescripción en el ámbito | Penal | 194788 | 145 | 99,9 % | 1343,4x |
| 4484 | 6. Se regula y limita la detención provisoria solo tratándose de im- | Penal | 194788 | 123 | 99,9 % | 1583,6x |
| 4485 | 6. Ubicarse dentro del campo visual de la persona con discapacidad | Constitucional | 177323 | 113 | 99,9 % | 1569,2x |
| 4486 | 6. Velar, en las decisiones judiciales, por el derecho a la seguridad, a | Constitucional | 177323 | 101 | 99,9 % | 1755,7x |
| 4487 | 6.1               Organización y flujo de trabajo | Judicial | 52128 | 48 | 99,9 % | 1086,0x |
| 4488 | 6.1            Acción de amparo económico | Judicial | 105809 | 97 | 99,9 % | 1090,8x |
| 4489 | 6.1          Casos | Constitucional | 121906 | 72 | 99,9 % | 1693,1x |
| 4490 | 6.1         Estándares internacionales de derechos | Judicial | 87237 | 55 | 99,9 % | 1586,1x |
| 4491 | 6.1     Ley Nº 20.886 (Auto acordado N° | Laboral | 71986 | 45 | 99,9 % | 1599,7x |
| 4492 | 6.1     Su composición | Laboral | 100583 | 59 | 99,9 % | 1704,8x |
| 4493 | 6.1 Acción de amparo económico (artículo único Ley N° 18.971)                                            130 | Judicial | 105809 | 78 | 99,9 % | 1356,5x |
| 4494 | 6.1 Aspectos básicos de la monografía             178 | Judicial | 79146 | 54 | 99,9 % | 1465,7x |
| 4495 | 6.1. Escala jerárquica de las normas. 6.2. Factores en virtud de los cuales se | General | 125500 | 156 | 99,9 % | 804,5x |
| 4496 | 6.1.10 Objeto de la ley106 | Familia | 100107 | 114 | 99,9 % | 878,1x |
| 4497 | 6.1.11 Actuación de la policía107 | Familia | 100107 | 85 | 99,9 % | 1177,7x |
| 4498 | 6.1.12 Habitualidad108 | Familia | 100107 | 87 | 99,9 % | 1150,7x |
| 4499 | 6.1.2 Entre quiénes hay violencia intrafamiliar | Familia | 100107 | 105 | 99,9 % | 953,4x |
| 4500 | 6.1.2 Principios que rigen | Laboral | 71986 | 42 | 99,9 % | 1714,0x |
| 4501 | 6.1.3 Competencia | Familia | 100107 | 92 | 99,9 % | 1088,1x |
| 4502 | 6.1.3 Respuestas capítulo 3 | Constitucional | 121906 | 70 | 99,9 % | 1741,5x |
| 4503 | 6.1.4 Obligación de denunciar | Familia | 100107 | 120 | 99,9 % | 834,2x |
| 4504 | 6.1.4 Respuestas capítulo 4 | Constitucional | 121906 | 135 | 99,9 % | 903,0x |
| 4505 | 6.1.5 Exclusión del control de admisibilidad | Familia | 100107 | 122 | 99,9 % | 820,5x |
| 4506 | 6.1.5 Respuestas capítulo 5 | Constitucional | 121906 | 110 | 99,9 % | 1108,2x |
| 4507 | 6.1.6 Presunciones legales de riesgo | Familia | 100107 | 126 | 99,9 % | 794,5x |
| 4508 | 6.1.7 Medidas cautelares | Familia | 100107 | 91 | 99,9 % | 1100,1x |
| 4509 | 6.1.8 Remisión de antecedentes si el | Familia | 100107 | 124 | 99,9 % | 807,3x |
| 4510 | 6.1.9 Actuación del tribunal si el | Familia | 100107 | 98 | 99,9 % | 1021,5x |
| 4511 | 6.11      Calificaciones | Laboral | 100583 | 130 | 99,9 % | 773,7x |
| 4512 | 6.2           El comité | Laboral | 100583 | 55 | 99,9 % | 1828,8x |
| 4513 | 6.2     Dispositivos electrónicos: Firma Electrónica | Laboral | 71986 | 49 | 99,9 % | 1469,1x |
| 4514 | 6.2     Jerarquía y consagración | Penal | 72395 | 49 | 99,9 % | 1477,4x |
| 4515 | 6.2     Reclamo de ilegalidad del artículo 151 | Judicial | 105809 | 111 | 99,9 % | 953,2x |
| 4516 | 6.2.1 Firma Digital Electrónica (Ley Nº 19.799) | Laboral | 71986 | 97 | 99,9 % | 742,1x |
| 4517 | 6.2.1 Respuestas capítulo 1 | Constitucional | 121906 | 94 | 99,9 % | 1296,9x |
| 4518 | 6.2.1 Suspensión condicional de la | Familia | 100107 | 126 | 99,9 % | 794,5x |
| 4519 | 6.2.2 Respuestas capítulo 2 | Constitucional | 121906 | 117 | 99,9 % | 1041,9x |
| 4520 | 6.2.3 Georreferenciación | Laboral | 71986 | 68 | 99,9 % | 1058,6x |
| 4521 | 6.2.3 Requerimiento de la víctima (denuncia de tercero) | Familia | 100107 | 135 | 99,9 % | 741,5x |
| 4522 | 6.2.4 Sentencia | Familia | 100107 | 62 | 99,9 % | 1614,6x |
| 4523 | 6.2.4.1 Pronunciamiento sobre la existencia de hechos | Familia | 100107 | 117 | 99,9 % | 855,6x |
| 4524 | 6.2.4.3 Aplicación de la sanción | Familia | 100107 | 105 | 99,9 % | 953,4x |
| 4525 | 6.3     Procedimiento | Procesal | 94881 | 65 | 99,9 % | 1459,7x |
| 4526 | 6.3     Reclamo de ilegalidad del artículo 108 de la | Judicial | 105809 | 66 | 99,9 % | 1603,2x |
| 4527 | 6.3.1 Según el tipo de sujetos intervinientes | Judicial | 96536 | 74 | 99,9 % | 1304,5x |
| 4528 | 6.3.2 Según la forma en que se expresa la voluntad | Judicial | 96536 | 104 | 99,9 % | 928,2x |
| 4529 | 6.3.3 Según la forma de aceptación del contrato | Judicial | 96536 | 106 | 99,9 % | 910,7x |
| 4530 | 6.3.4 Según el modo de adhesión | Judicial | 96536 | 76 | 99,9 % | 1270,2x |
| 4531 | 6.3.5 Según su ejecución | Judicial | 96536 | 98 | 99,9 % | 985,1x |
| 4532 | 6.4       Acción por vulneración de derechos del | Judicial | 105809 | 92 | 99,9 % | 1150,1x |
| 4533 | 6.4   Consagración | Penal | 72395 | 46 | 99,9 % | 1573,8x |
| 4534 | 6.4 Acción por vulneración de derechos del contribuyente (Ley N° 20.322 y Ley N° 20.420)                 162 | Judicial | 105809 | 105 | 99,9 % | 1007,7x |
| 4535 | 6.4. El mandante dispone de todas las acciones del mandatario en contra del | Civil | 42773 | 45 | 99,9 % | 950,5x |
| 4536 | 6.4.3 La unidad de Administración de causas: desarrolla toda la | Laboral | 100583 | 80 | 99,9 % | 1257,3x |
| 4537 | 6.4.4 La unidad de Servicios: reúne las labores de soporte técnico | Laboral | 100583 | 93 | 99,9 % | 1081,5x |
| 4538 | 6.4.5 La unidad de Cumplimiento: se creará en aquellos juzgados | Laboral | 100583 | 59 | 99,9 % | 1704,8x |
| 4539 | 6.4.6 La unidad de Liquidación: por su parte, son propias de los | Laboral | 100583 | 111 | 99,9 % | 906,2x |
| 4540 | 6.5     Tribunal de Defensa de la Libre Competencia | Judicial | 105809 | 93 | 99,9 % | 1137,7x |
| 4541 | 6.6     Reclamación contra sanciones administrativas | Judicial | 105809 | 62 | 99,9 % | 1706,6x |
| 4542 | 6.6 Reclamación contra sanciones administrativas regulada en el Código Sanitario (artículos 171 y ss.)   186 | Judicial | 105809 | 107 | 99,9 % | 988,9x |
| 4543 | 6.6.1 Los derechos fundamentales de la | Penal | 72395 | 75 | 99,9 % | 965,3x |
| 4544 | 6.6.3 El interés superior del niño como un derecho | Penal | 72395 | 100 | 99,9 % | 724,0x |
| 4545 | 6.6.4 El interés superior del niño como un principio | Penal | 72395 | 84 | 99,9 % | 861,8x |
| 4546 | 6.7.1 Jurisprudencia nacional | Penal | 72395 | 72 | 99,9 % | 1005,5x |
| 4547 | 6.7.2 Jurisprudencia comparada | Penal | 72395 | 102 | 99,9 % | 709,8x |
| 4548 | 6.8           El procedimiento | Laboral | 100583 | 63 | 99,9 % | 1596,6x |
| 4549 | 60 Dwyer agrega: «To talk about evidence of opinion as being quite distinct from | Judicial | 150341 | 101 | 99,9 % | 1488,5x |
| 4550 | 60 El artículo 251 sexies del Código Penal dispone en su inciso primero: «No será | Penal | 178516 | 104 | 99,9 % | 1716,5x |
| 4551 | 60 Situación que ya no debería presentarse, con motivo de la modificación de la | Familia | 123490 | 88 | 99,9 % | 1403,3x |
| 4552 | 60 Utiliza como ejemplo pericias sobre credibilidad del relato en que se corre el | Procesal | 86112 | 62 | 99,9 % | 1388,9x |
| 4553 | 60. CORTE SUPREMA, rol N° 2.907 2011, de cinco de         75. CORTE SUPREMA, rol N° 16.189-2014, de nueve | Familia | 65085 | 88 | 99,9 % | 739,6x |
| 4554 | 60. DWORKIN, Ronald (1999), Los derechos en serio | Laboral | 113458 | 105 | 99,9 % | 1080,6x |
| 4555 | 60. MACHADO RUIZ, María Dolores, (2002): “El derecho a no ser | Judicial | 81476 | 91 | 99,9 % | 895,3x |
| 4556 | 60. RODRÍGUEZ, María José (2012): “El código penal | Penal | 72395 | 83 | 99,9 % | 872,2x |
| 4557 | 61 Fue a propósito de las tratativas para la elaboración de la Convención de las | Penal | 178516 | 117 | 99,9 % | 1525,8x |
| 4558 | 61 Por lo mismo es que algunos jueces laborales han exigido que en la demanda se | Procesal | 86112 | 106 | 99,9 % | 812,4x |
| 4559 | 61. CORTE SUPREMA, rol N° 9.607-2011, de vein-            76. CORTE SUPREMA, rol N° 12.492-14, de dieciocho | Familia | 65085 | 88 | 99,9 % | 739,6x |
| 4560 | 61. LEÓN, Francisco Javier (2012): “Ley de derechos y deberes de las personas | Constitucional | 121906 | 76 | 99,9 % | 1604,0x |
| 4561 | 61. MACHADO RUIZ, María Dolores, (2002): La discriminación en el ámbito delos | Judicial | 81476 | 58 | 99,9 % | 1404,8x |
| 4562 | 62   Incluso, desde una perspectiva histórica, podemos encontrar derechos sociales (de los denominados de se- | Laboral | 113458 | 131 | 99,9 % | 866,1x |
| 4563 | 62 Entre las medidas que se señalan se encuentran: la elaboración de códigos | Penal | 178516 | 152 | 99,9 % | 1174,4x |
| 4564 | 62 Lo que implicaría que el perito concurra a declarar a la audiencia única, salvo | Procesal | 86112 | 80 | 99,9 % | 1076,4x |
| 4565 | 62 Sentencia Tribunal Constitucional rol 1718, de 14 de junio de 2011 y sentencia | Judicial | 144656 | 80 | 99,9 % | 1808,2x |
| 4566 | 62.   Cárdenas Aravena, Claudia (2013): “La aplicabilidad del derecho internacio- | Penal | 121924 | 78 | 99,9 % | 1563,1x |
| 4567 | 62. Aprobamos, con la redacción definitiva que se incorpora | Judicial | 79146 | 76 | 99,9 % | 1041,4x |
| 4568 | 62. PANTALEON, Fernando (1991): “El sistema de | Civil | 142015 | 79 | 99,9 % | 1797,7x |
| 4569 | 62. Yugar con Ministerio del Interior y Seguridad Pública (2018): CS, 23 de | Constitucional | 115835 | 104 | 99,9 % | 1113,8x |
| 4570 | 63       Estados Unidos de América. Public Law 110–175—Dec. 31, 2007. Openness Promotes Effectiveness in Our | Administrativo | 89720 | 132 | 99,9 % | 679,7x |
| 4571 | 63 Modificado por la Norma de Carácter General 126, de fecha 1 de septiembre | Familia | 123490 | 65 | 99,9 % | 1899,8x |
| 4572 | 63 Por ejemplo, Televisión Nacional de Chile, la Empresa de los Ferrocarriles del | Penal | 178516 | 97 | 99,9 % | 1840,4x |
| 4573 | 63. CORTE SUPREMA, rol N° 3509-2012, de uno de            78. CORTE SUPREMA, rol N° 28.905-2014, de die- | Familia | 65085 | 94 | 99,9 % | 692,4x |
| 4574 | 63. MUÑOZ, Fernando (2015): “Estándares conceptuales y cargas procesales | Judicial | 81476 | 76 | 99,9 % | 1072,1x |
| 4575 | 64 Así lo ha resuelto el máximo tribunal declarando inadmisibles los recursos | Judicial | 144656 | 114 | 99,9 % | 1268,9x |
| 4576 | 64 Para más información, véase Fernández (2001: 392). Así, la Recomendación | Constitucional | 177323 | 96 | 99,9 % | 1847,1x |
| 4577 | 64. CORTE SUPREMA, rol N° 3.674-2012, de treinta          79.   CORTE SUPREMA, rol N° 27.307-14, de veinti- | Familia | 65085 | 79 | 99,9 % | 823,9x |
| 4578 | 64. MUÑOZ, Fernando (2015): “La Ley Zamudio en Acción: Sentencias de | Judicial | 81476 | 80 | 99,9 % | 1018,5x |
| 4579 | 64. VALDIVIESO, Patricio (2006): Dignidad humana | Penal | 72395 | 105 | 99,9 % | 689,5x |
| 4580 | 65 Artículo 11 PIDESC: «1. Los Estados partes en el presente Pacto reconocen el | Judicial | 81675 | 68 | 99,9 % | 1201,1x |
| 4581 | 65 Cohen advirtió que von Frisch iba modificando tanto las hipótesis como las | Judicial | 150341 | 175 | 99,9 % | 859,1x |
| 4582 | 65 El primer ciclo de revisión de Chile, por parte de El Salvador y Ucrania, fue | Penal | 178516 | 169 | 99,9 % | 1056,3x |
| 4583 | 65. CORTE SUPREMA, rol N° 8.953-2012, de veinte           80. CORTE SUPREMA, rol N° 6.674-15, de uno de | Familia | 65085 | 92 | 99,9 % | 707,4x |
| 4584 | 65. Exhortamos, por tanto, a los Poderes Judiciales de la Cumbre | Judicial | 79146 | 68 | 99,9 % | 1163,9x |
| 4585 | 65. MUÑOZ, Patricia (2011): Violencias Interseccionales, Debates Feministas y | Judicial | 81476 | 68 | 99,9 % | 1198,2x |
| 4586 | 66      Inscripciones | Civil | 171433 | 187 | 99,9 % | 916,8x |
| 4587 | 66 Así lo dispone el inciso tercero del artículo 150 del Código Civil: «Incumbe a la | Familia | 123490 | 97 | 99,9 % | 1273,1x |
| 4588 | 66 En este sentido, Ragués (1999: 334) considera que «sin embargo, la diferencia | Judicial | 150341 | 123 | 99,9 % | 1222,3x |
| 4589 | 66 La reforma constitucional también estableció que la ley determinará los casos | Penal | 178516 | 120 | 99,9 % | 1487,6x |
| 4590 | 66 Sentencia del Tercer Tribunal Oral en lo Penal, RIT 60-2016, 9 de junio de | Penal | 178516 | 137 | 99,9 % | 1303,0x |
| 4591 | 66. CORTE SUPREMA, rol N° 1.996-2013, de uno de           81. CORTE SUPREMA, rol Nº 124-2015, de dieciocho | Familia | 65085 | 93 | 99,9 % | 699,8x |
| 4592 | 66. EVANS DE LA CUADRA, Enrique (2004), Los | Laboral | 113458 | 75 | 99,9 % | 1512,8x |
| 4593 | 66. VARGAS, Macarena (2011): “La voz de los niños | Penal | 72395 | 91 | 99,9 % | 795,5x |
| 4594 | 67   Corte Suprema, 10 de marzo de 2016, Rol Nº 21373-2015; en el mismo sentido, véase Corte de Apelaciones | Civil | 142015 | 72 | 99,9 % | 1972,4x |
| 4595 | 67   Ver entre otros: VERGARA, Alejandro (2013), pp. 45-46; CARMONA, Carlos (2005), pp. 165-240; y COSTA, Ezio | Judicial | 105809 | 66 | 99,9 % | 1603,2x |
| 4596 | 67 En 2003 se había incorporado una definición de conflicto de intereses en el | Penal | 178516 | 179 | 99,9 % | 997,3x |
| 4597 | 67 En efecto, los Comentarios sobre la Convención para Combatir el Cohecho | Penal | 178516 | 105 | 99,9 % | 1700,2x |
| 4598 | 67 Hay que tener en consideración, por ejemplo, que la asignatura de la psicología | Judicial | 150341 | 131 | 99,9 % | 1147,6x |
| 4599 | 67 Sentencia de la Corte de Apelaciones de Santiago, rol 16122-2018, 18 de marzo | Familia | 123490 | 75 | 99,9 % | 1646,5x |
| 4600 | 67.   CORTE SUPREMA, rol N° 3.784-2013, de veinti-        82. CORTE SUPREMA, rol N° 4.938-15, de veintidós | Familia | 65085 | 89 | 99,9 % | 731,3x |
| 4601 | 67.   TTA de Biobío, (RIT VD-10-00155-2013 y RIT | Judicial | 105809 | 100 | 99,9 % | 1058,1x |
| 4602 | 67.   VERHELLEN, Eugeen (1994): Convention on the | Penal | 72395 | 100 | 99,9 % | 724,0x |
| 4603 | 68 Asimismo, en sentencia Corte Suprema rol 135481-2022, de 15 de diciembre de | Judicial | 144656 | 192 | 99,9 % | 753,4x |
| 4604 | 68 La adopción de un texto con carácter vinculante por parte de la Conferencia | Penal | 178516 | 170 | 99,9 % | 1050,1x |
| 4605 | 68 Para más información, véase el artículo 1, inciso segundo, de la Convención | Constitucional | 177323 | 165 | 99,9 % | 1074,7x |
| 4606 | 68 Por ejemplo, Nieva (2012: 35) considera: «las legislaciones de cualquier Estado | Judicial | 150341 | 106 | 99,9 % | 1418,3x |
| 4607 | 68 Sobre la denominada trilogía Daubert y sus efectos respecto de los criterios de | Judicial | 150341 | 87 | 99,9 % | 1728,1x |
| 4608 | 68. CORTE SUPREMA, rol N° 4.159-13, de nueve de           83. CORTE SUPREMA, rol N° 8.216-2015, de quince | Familia | 65085 | 88 | 99,9 % | 739,6x |
| 4609 | 68. FALGUERA BARÓ, Miguel Ángel (2004), “Criterios | Laboral | 113458 | 123 | 99,9 % | 922,4x |
| 4610 | 68. MORESO, José Juan (2004): “Dos concepciones de la aplicación de las nor- | Constitucional | 121906 | 76 | 99,9 % | 1604,0x |
| 4611 | 68. NOGUEIRA, Humberto (2006): “El derecho a la igualdad ante la ley, no | Judicial | 81476 | 68 | 99,9 % | 1198,2x |
| 4612 | 68. Patricia Corvalan Castillo con Servicio de Salud       81. Sociedad Educacional Colegio Alemán de Arica | Civil | 142015 | 98 | 99,9 % | 1449,1x |
| 4613 | 69 Artículo 16, secreto bancario: «1) El Estado parte requerido no podrá negarse | Penal | 178516 | 153 | 99,9 % | 1166,8x |
| 4614 | 69 En Sentencia Corte Suprema rol número 38.439-2021, de 9 de diciembre de | Judicial | 144656 | 189 | 99,9 % | 765,4x |
| 4615 | 69 Ley 19.968). Lo anterior, deberá estar coordinado con lo previs- | Familia | 97488 | 87 | 99,9 % | 1120,6x |
| 4616 | 69. CORTE SUPREMA, rol Nº 4311-2013, de veintiuno         84. CORTE SUPREMA, rol N° 37.478-2015, de tres de | Familia | 65085 | 93 | 99,9 % | 699,8x |
| 4617 | 69. FEDTKE, Jörg (2007a), “Drittwirkung in Germany”,         derecho del trabajo, (Santiago, Thomson Reuters | Laboral | 113458 | 110 | 99,9 % | 1031,4x |
| 4618 | 69. LAURENZO COPELLO, Patricia, (1996): La discriminación en el Código Penal | Judicial | 81476 | 50 | 99,9 % | 1629,5x |
| 4619 | 69. Patricia Loreto Muñoz Oliva con Servicio de Salud | Civil | 142015 | 104 | 99,9 % | 1365,5x |
| 4620 | 7        RUZ LÁRTIGA, G. (2017): Nuevo Derecho Concursal Chileno, Tomo I: Reorganización de Empresa Deudora y | Judicial | 64632 | 74 | 99,9 % | 873,4x |
| 4621 | 7        Reglamento (UE) 2016/679 del Parlamento Europeo y del Consejo | Judicial | 96536 | 49 | 99,9 % | 1970,1x |
| 4622 | 7   BORDALÍ SALAMANCA, Andrés (2009): “Organización judicial en el derecho chileno”, en Revista Chilena de | Procesal | 94881 | 72 | 99,9 % | 1317,8x |
| 4623 | 7 Artículo 595: «Si, ratificado el desahucio, llega el día señalado para la restitución | Judicial | 89450 | 122 | 99,9 % | 733,2x |
| 4624 | 7 Caterina Guidi, «El régimen de trabajo 996», RH Management, 15 de mayo de | Laboral | 98828 | 63 | 99,9 % | 1568,7x |
| 4625 | 7 Declaración adoptada por la 31.ª reunión de la Conferencia General de Unesco | Constitucional | 177323 | 107 | 99,9 % | 1657,2x |
| 4626 | 7 Decreto 943, de 1994, del Ministerio del Interior. La Comisión se conformó por | Penal | 178516 | 149 | 99,9 % | 1198,1x |
| 4627 | 7 El artículo 10 letra b) establece que se deberá gestionar, asegurar y registrar que | Judicial | 82507 | 101 | 99,9 % | 816,9x |
| 4628 | 7 El inciso primero del artículo 5 del Código del Trabajo «hace referencia a las | Laboral | 98828 | 139 | 99,9 % | 711,0x |
| 4629 | 7 En cumplimiento de estas obligaciones internacionales, se discute actualmente | Penal | 97633 | 141 | 99,9 % | 692,4x |
| 4630 | 7 En ese mismo sentido la política de actuación del Ministerio Público, al señalar | Penal | 178516 | 174 | 99,9 % | 1026,0x |
| 4631 | 7 Especifica también que cualquier proyectil que se utilice no debe desviarse más | Penal | 51155 | 67 | 99,9 % | 763,5x |
| 4632 | 7 Esta concepción también fue seguida por la Comisión Nacional de Ética Pública | Penal | 178516 | 104 | 99,9 % | 1716,5x |
| 4633 | 7 Esta definición y las que vienen a continuación, incluidos los ejemplos, son de | Judicial | 92792 | 53 | 99,9 % | 1750,8x |
| 4634 | 7 Intervención del profesor Matus en «Historia de la Ley 20.813 que modifica la | Judicial | 62514 | 80 | 99,9 % | 781,4x |
| 4635 | 7 Nuestra legislación, a partir de la entrada en vigencia de la Ley 21.430 (Sobre | Familia | 97488 | 117 | 99,9 % | 833,2x |
| 4636 | 7 Obviamente dicha operatividad es algo distinta en procedimientos especiales | Procesal | 86112 | 74 | 99,9 % | 1163,7x |
| 4637 | 7 Pacto Internacional de Derechos Económicos, Sociales y Culturales. Disponible | Judicial | 81675 | 61 | 99,9 % | 1338,9x |
| 4638 | 7 Por ejemplo, artículo 170 del Código de Procedimiento Civil; artículo 342 del | Judicial | 92792 | 74 | 99,9 % | 1253,9x |
| 4639 | 7 Rainer, Martínez y Zúñiga (2012: 83 y 84) apuntan que, en materia de conflictos | Judicial | 144656 | 172 | 99,9 % | 841,0x |
| 4640 | 7 Recuérdese la afirmación de Aristóteles (2005) sobre la necesidad de diversidad | Judicial | 81675 | 88 | 99,9 % | 928,1x |
| 4641 | 7 Según esta misma disposición, la periodicidad estará definida en el programa | Laboral | 98828 | 143 | 99,9 % | 691,1x |
| 4642 | 7 Sentencia de la Corte de Apelaciones de Concepción, 25 de junio de 2009, rol | Familia | 123490 | 79 | 99,9 % | 1563,2x |
| 4643 | 7 Sentencia de la Corte de Apelaciones de Rancagua, rol 59-2010, 10 de marzo de | Penal | 178516 | 169 | 99,9 % | 1056,3x |
| 4644 | 7 Sentencia de reemplazo en el caso Soledad Astudillo Martínez con Codelco, rol | Laboral | 74025 | 55 | 99,9 % | 1345,9x |
| 4645 | 7 Véase Sentencia de la Corte Suprema, rol 7964-2010, de 20 de enero de 2011. La | Familia | 123490 | 84 | 99,9 % | 1470,1x |
| 4646 | 7 Véase el estado de ratificación del PIDESC y su Protocolo Adicional en: Naciones | Judicial | 81675 | 65 | 99,9 % | 1256,5x |
| 4647 | 7 Véase la Convención sobre los Derechos del Niño (artículo 40.1), las Reglas de | Penal | 86906 | 81 | 99,9 % | 1072,9x |
| 4648 | 7 Véase «Jornada laboral efectiva en Chile se ha reducido 20 % en los últimos 30 | Laboral | 98828 | 70 | 99,9 % | 1411,8x |
| 4649 | 7) APUNTES DE CLASES DE DERECHO PROCESAL CIVIL.Francis-- | Procesal | 95124 | 63 | 99,9 % | 1509,9x |
| 4650 | 7.    FERNÁNDEZ G., Miguel Ángel (2003): “El recurso | Judicial | 105809 | 123 | 99,9 % | 860,2x |
| 4651 | 7.    Ley N° 19.779, que establece Normas relativas al | Laboral | 113458 | 84 | 99,9 % | 1350,7x |
| 4652 | 7.    Ley N° 21.155, establece medidas de protección a la lactancia materna y su | Judicial | 81476 | 54 | 99,9 % | 1508,8x |
| 4653 | 7.    Opinión Consultiva oc-24/17 de 24 de noviembre                 Referencias electrónicas | Judicial | 89476 | 100 | 99,9 % | 894,8x |
| 4654 | 7.   BARCIA, Rodrigo (2013): “La capacidad extrapa-            adolescentes. Disponible en http://www.oas.org/ | Familia | 100107 | 101 | 99,9 % | 991,2x |
| 4655 | 7.   Corte Constitucional de Colombia, Demanda de inconstitucionalidad | Penal | 121924 | 65 | 99,9 % | 1875,8x |
| 4656 | 7.   En cuanto al tiempo en el que el daño tiene lugar, generalmente, en la responsabilidad | Civil | 142015 | 87 | 99,9 % | 1632,4x |
| 4657 | 7.   Explique la crítica relativa a la afectación de la autonomía privada en | Laboral | 113458 | 124 | 99,9 % | 915,0x |
| 4658 | 7.   Ley Nº 19.712, establece un deber del Estado en relación al deporte para | Constitucional | 121906 | 68 | 99,9 % | 1792,7x |
| 4659 | 7. Boletín N° 11.758-07. Reforma Constitucional: busca avanzar | Judicial | 89476 | 81 | 99,9 % | 1104,6x |
| 4660 | 7. Cuando la sentencia hubiere sido dictada en oposición a otra senten- | Procesal | 66012 | 85 | 99,9 % | 776,6x |
| 4661 | 7. Cumplimiento de sentencia caso Norin Catriman en materia de | Constitucional | 177323 | 115 | 99,9 % | 1541,9x |
| 4662 | 7. Diagnóstico sobre barreras territoriales en la entrega de beneficios | Constitucional | 177323 | 165 | 99,9 % | 1074,7x |
| 4663 | 7. Donde la ley no distingue, no cabe distinguir el intérprete: la ley, al referirse al daño | Civil | 120848 | 107 | 99,9 % | 1129,4x |
| 4664 | 7. El Estado debe, dentro del plazo de un año contado a partir de | Judicial | 87237 | 124 | 99,9 % | 703,5x |
| 4665 | 7. El Estado no violó la garantía judicial de imparcialidad consagrada | Judicial | 87237 | 111 | 99,9 % | 785,9x |
| 4666 | 7. El pronunciamiento sobre el pago de costas y, en su caso, los | Laboral | 100583 | 81 | 99,9 % | 1241,8x |
| 4667 | 7. Evaluaciones sobre la eficacia del case management | Procesal | 96699 | 140 | 99,9 % | 690,7x |
| 4668 | 7. Incluir de oficio por el tribunal o recomendar a los comparecientes | Constitucional | 177323 | 98 | 99,9 % | 1809,4x |
| 4669 | 7. Indicar que, en caso de impedimento, deberán comunicarlo y jus- | Judicial | 89450 | 106 | 99,9 % | 843,9x |
| 4670 | 7. Institucionalidad | Constitucional | 44292 | 48 | 99,9 % | 922,8x |
| 4671 | 7. La planificación de reuniones de coordinación interna | Procesal | 94881 | 107 | 99,9 % | 886,7x |
| 4672 | 7. La proporción del precio pagado con anterioridad al inicio del ré- | Familia | 123490 | 79 | 99,9 % | 1563,2x |
| 4673 | 7. La renuncia a los gananciales, según ha expresado de manera uniforme nuestra | Familia | 136567 | 172 | 99,9 % | 794,0x |
| 4674 | 7. Notificación a petición de parte: Los patrocinantes de las partes, en | Judicial | 89450 | 109 | 99,9 % | 820,6x |
| 4675 | 7. Ofrecimiento de prueba, decisión de admisibilidad y rendición | Laboral | 71986 | 55 | 99,9 % | 1308,8x |
| 4676 | 7. Otorgar, en los casos en que sea necesario, un plazo mayor para | Constitucional | 177323 | 89 | 99,9 % | 1992,4x |
| 4677 | 7. Para el caso en que nadie se encuentre en los citados lugares o si | Judicial | 89450 | 120 | 99,9 % | 745,4x |
| 4678 | 7. Para la aplicación del principio de oportunidad los fiscales tendrán | Penal | 194788 | 206 | 99,9 % | 945,6x |
| 4679 | 7. Promover factores protectores y evitar conductas de riesgo en las | Constitucional | 177323 | 98 | 99,9 % | 1809,4x |
| 4680 | 7. Que, además, para la acertada resolución de este recurso es útil tener | Penal | 194788 | 107 | 99,9 % | 1820,4x |
| 4681 | 7. Representar en juicio, activa y pasivamente, a los copropietarios, con las facultades del | Civil | 192585 | 123 | 99,9 % | 1565,7x |
| 4682 | 7. Toda persona tiene el derecho de buscar y recibir asilo en territorio extranjero en caso de persecución por | Constitucional | 115835 | 128 | 99,9 % | 905,0x |
| 4683 | 7.1               Poder de vigilancia | Judicial | 96536 | 91 | 99,9 % | 1060,8x |
| 4684 | 7.1     Los principios formativos | Laboral | 100583 | 80 | 99,9 % | 1257,3x |
| 4685 | 7.1.1 Recursos humanos | Laboral | 71986 | 104 | 99,9 % | 692,2x |
| 4686 | 7.1.2 Servicios | Laboral | 71986 | 87 | 99,9 % | 827,4x |
| 4687 | 7.10                Sana crítica. Apreciación de la | Laboral | 100583 | 72 | 99,9 % | 1397,0x |
| 4688 | 7.11.1 Características y contenido | Laboral | 100583 | 122 | 99,9 % | 824,5x |
| 4689 | 7.11.1 Determinación del derecho vulnerado | Familia | 100107 | 128 | 99,9 % | 782,1x |
| 4690 | 7.11.2 Necesidad y conveniencia de la medida adoptada | Familia | 100107 | 104 | 99,9 % | 962,6x |
| 4691 | 7.11.2 Plazo | Laboral | 100583 | 128 | 99,9 % | 785,8x |
| 4692 | 7.11.4 Objetivos de la medida adoptada | Familia | 100107 | 113 | 99,9 % | 885,9x |
| 4693 | 7.11.5 Duración de la medida | Familia | 100107 | 84 | 99,9 % | 1191,8x |
| 4694 | 7.11.6 Fundamentación reforzada en caso | Familia | 100107 | 118 | 99,9 % | 848,4x |
| 4695 | 7.11.6.2 Estándares para proceder a la internación de un NNA | Familia | 100107 | 110 | 99,9 % | 910,1x |
| 4696 | 7.11.7 Medida de protección como “mal menor” | Familia | 100107 | 91 | 99,9 % | 1100,1x |
| 4697 | 7.13.1 Características. Resoluciones | Laboral | 100583 | 102 | 99,9 % | 986,1x |
| 4698 | 7.13.2 Causales de nulidad | Laboral | 100583 | 100 | 99,9 % | 1005,8x |
| 4699 | 7.13.2.1 Causales genéricas | Laboral | 100583 | 107 | 99,9 % | 940,0x |
| 4700 | 7.13.2.2 Causales específicas | Laboral | 100583 | 72 | 99,9 % | 1397,0x |
| 4701 | 7.13.3 Requisitos y formalidades | Laboral | 100583 | 92 | 99,9 % | 1093,3x |
| 4702 | 7.13.4 Remisión de antecedentes al tribunal de alzada | Laboral | 100583 | 101 | 99,9 % | 995,9x |
| 4703 | 7.13.5 Resolución del recurso | Laboral | 100583 | 123 | 99,9 % | 817,7x |
| 4704 | 7.14.1 Procedencia, objeto y resoluciones | Laboral | 100583 | 122 | 99,9 % | 824,5x |
| 4705 | 7.14.2 Interposición y remisión de los antecedentes al | Laboral | 100583 | 98 | 99,9 % | 1026,4x |
| 4706 | 7.14.3 Tramitación ante la Corte Suprema | Laboral | 100583 | 119 | 99,9 % | 845,2x |
| 4707 | 7.2         Teletrabajo | Judicial | 96536 | 93 | 99,9 % | 1038,0x |
| 4708 | 7.2. Clasificaci nes d ctrinarias de l s c ntrat s.70 | Civil | 110175 | 65 | 99,9 % | 1695,0x |
| 4709 | 7.2. Clasificaciones doctrinarias de los contratos | Civil | 110175 | 140 | 99,9 % | 787,0x |
| 4710 | 7.2. Por muerte presunta de uno de los convivientes civiles, de conformidad a lo | Familia | 190697 | 175 | 99,9 % | 1089,7x |
| 4711 | 7.2.1 El lugar físico en que se ha previsto | Judicial | 96536 | 104 | 99,9 % | 928,2x |
| 4712 | 7.2.1.1 Centros de recursos compartidos | Judicial | 96536 | 107 | 99,9 % | 902,2x |
| 4713 | 7.2.1.2 Telecentros | Judicial | 96536 | 76 | 99,9 % | 1270,2x |
| 4714 | 7.2.1.3 Oficinas satélite | Judicial | 96536 | 100 | 99,9 % | 965,4x |
| 4715 | 7.2.1.4 Televillage o telecottages | Judicial | 96536 | 57 | 99,9 % | 1693,6x |
| 4716 | 7.2.2 El teletrabajo en la legislación nacional | Judicial | 96536 | 101 | 99,9 % | 955,8x |
| 4717 | 7.3     Deberes y atribuciones del | Laboral | 100583 | 91 | 99,9 % | 1105,3x |
| 4718 | 7.3. Cosas susceptibles de hipotecarse; y | Civil | 66868 | 81 | 99,9 % | 825,5x |
| 4719 | 7.3.1 Firma del contrato de trabajo a | Judicial | 96536 | 98 | 99,9 % | 985,1x |
| 4720 | 7.3.1 La querella | Penal | 211066 | 117 | 99,9 % | 1804,0x |
| 4721 | 7.3.1 Sentencia caso Y. y B. vs. República Dominicana80 | Penal | 72395 | 93 | 99,9 % | 778,4x |
| 4722 | 7.3.2 Registro de asistencia | Judicial | 96536 | 91 | 99,9 % | 1060,8x |
| 4723 | 7.3.3 Libro y comprobante de remuneraciones | Judicial | 96536 | 107 | 99,9 % | 902,2x |
| 4724 | 7.3.4 Finiquito laboral | Judicial | 96536 | 91 | 99,9 % | 1060,8x |
| 4725 | 7.3.6 Abandono de la querella | Penal | 211066 | 111 | 99,9 % | 1901,5x |
| 4726 | 7.3.7 La acción civil en el proceso penal | Penal | 211066 | 140 | 99,9 % | 1507,6x |
| 4727 | 7.3.9 La acción civil y las medidas cautelares reales | Penal | 211066 | 150 | 99,9 % | 1407,1x |
| 4728 | 7.4    Tareas relacionadas con | Judicial | 44331 | 52 | 99,9 % | 852,5x |
| 4729 | 7.5. Por mutuo acuerdo de los convivientes civiles, que deberá constar por escritura | Familia | 190697 | 149 | 99,9 % | 1279,8x |
| 4730 | 7.5.1 Distribución del personal | Laboral | 71986 | 104 | 99,9 % | 692,2x |
| 4731 | 7.5.2 Modelos de polifuncionalidad | Laboral | 71986 | 93 | 99,9 % | 774,0x |
| 4732 | 7.5.3 Protocolo de inducción | Laboral | 71986 | 94 | 99,9 % | 765,8x |
| 4733 | 7.5.5 Metas de gestión de desempeño | Laboral | 71986 | 93 | 99,9 % | 774,0x |
| 4734 | 7.5.7   Indicadores de gestión                                                  168 | Judicial | 52128 | 59 | 99,9 % | 883,5x |
| 4735 | 7.6     Deber de adoptar medidas inexistentes solicitadas | Familia | 100107 | 53 | 99,9 % | 1888,8x |
| 4736 | 7.6.   La notificación de la demanda y personas | Laboral | 100583 | 54 | 99,9 % | 1862,6x |
| 4737 | 7.6. Por voluntad unilateral de uno de los convivientes civiles, que deberá constar por | Familia | 190697 | 198 | 99,9 % | 963,1x |
| 4738 | 7.7     Admisión, citación, contestación de | Laboral | 100583 | 80 | 99,9 % | 1257,3x |
| 4739 | 7.8     La audiencia preparatoria | Laboral | 100583 | 55 | 99,9 % | 1828,8x |
| 4740 | 7.8. Por la cesación de las funciones del mandante si el mandato ha sido dado en | Civil | 42773 | 59 | 99,9 % | 725,0x |
| 4741 | 7.8.1 Conciliación | Laboral | 100583 | 119 | 99,9 % | 845,2x |
| 4742 | 7.8.2 Ofrecimiento y pertinencia de prueba | Laboral | 100583 | 92 | 99,9 % | 1093,3x |
| 4743 | 7.9.1 Recepción de la prueba | Laboral | 100583 | 124 | 99,9 % | 811,2x |
| 4744 | 7.9.1.1 Orden de recepción | Laboral | 100583 | 83 | 99,9 % | 1211,8x |
| 4745 | 7.9.1.2 Otras pruebas | Laboral | 100583 | 117 | 99,9 % | 859,7x |
| 4746 | 7.9.2 Observaciones a la prueba | Laboral | 100583 | 97 | 99,9 % | 1036,9x |
| 4747 | 7.9.3 Acta de la audiencia | Laboral | 100583 | 100 | 99,9 % | 1005,8x |
| 4748 | 70   COUTURE (1956), p. 280 | Familia | 100107 | 67 | 99,9 % | 1494,1x |
| 4749 | 70   Véase Corte de Apelaciones de Concepción, 14 de octubre de 2012, Rol Nº 1473-2012 y Corte Suprema, 28 | Civil | 142015 | 78 | 99,9 % | 1820,7x |
| 4750 | 70 Decimos eventualmente porque bien puede el particular ofrecer un beneficio | Penal | 178516 | 156 | 99,9 % | 1144,3x |
| 4751 | 70 Ius cogens son las normas imperativas de derecho internacional generalmente conocidas, es decir, aquellas | Penal | 121924 | 149 | 99,9 % | 818,3x |
| 4752 | 70 Respecto de los órganos de la Administración del Estado, el ente contralor, de | Penal | 178516 | 162 | 99,9 % | 1102,0x |
| 4753 | 70 Simón (1999: 18) considera que la naturaleza del razonamiento judicial está | Judicial | 150341 | 179 | 99,9 % | 839,9x |
| 4754 | 70 Una cuestión no menor que afecta a la relación entre el derecho probatorio y | Judicial | 150341 | 170 | 99,9 % | 884,4x |
| 4755 | 70 Una síntesis de la jurisprudencia de la CIDH sobre el derecho a ser juzgado | Judicial | 144656 | 195 | 99,9 % | 741,8x |
| 4756 | 70. CORTE SUPREMA, rol N° 8473-2013, de veinti-           85. CORTE SUPREMA, rol N° 51-2016, de cuatro de | Familia | 65085 | 91 | 99,9 % | 715,2x |
| 4757 | 70. MUCCIO, Leah (2012): Head Start Instructional Professionals’ Perceptions | Constitucional | 121906 | 74 | 99,9 % | 1647,4x |
| 4758 | 704 Los organismos administradores del seguro de la ley N° 16.744, deberán informar a sus empresas afilia- | Laboral | 100583 | 78 | 99,9 % | 1289,5x |
| 4759 | 704 Nº 4: posesión con “título putativo” y eventualmente con justo título si se obtiene | Civil | 36671 | 49 | 99,9 % | 748,4x |
| 4760 | 71 El inciso primero del artículo 154 del Decreto con Fuerza de Ley 3 dispone una | Penal | 178516 | 182 | 99,9 % | 980,9x |
| 4761 | 71.   CORTE SUPREMA, rol N° 14.117-13, de veintisiete     86. CORTE SUPREMA, rol N° 20.136-2015, de dieci- | Familia | 65085 | 85 | 99,9 % | 765,7x |
| 4762 | 71.   MUÑOZ, Juan Manuel (2013): “La evaluación psicológica forense del daño | Familia | 95131 | 78 | 99,9 % | 1219,6x |
| 4763 | 71.   Paz López Osorio con Ilustre Municipalidad de            San Borja Arriarán (2016): Corte Suprema, 14 de | Civil | 142015 | 97 | 99,9 % | 1464,1x |
| 4764 | 71. En ambos casos deberá darse cumplimiento a lo ordenado en el | Judicial | 64632 | 70 | 99,9 % | 923,3x |
| 4765 | 718. Y cuando el art. 703 la considera título traslaticio se estaría refiriendo a las | Familia | 136567 | 165 | 99,9 % | 827,7x |
| 4766 | 72   La Ley Nº 20.252, de 15 de febrero de 2008, introdujo modificaciones a la Ley Nº 20.022, (2006), y otros | Laboral | 100583 | 104 | 99,9 % | 967,1x |
| 4767 | 72 El artículo primero del DFL 707 establece: «La cuenta corriente bancaria es un | Penal | 178516 | 188 | 99,9 % | 949,6x |
| 4768 | 72.   Lord, Nicolas; van Wingerde, Karin, y Campbell | Penal | 119528 | 85 | 99,9 % | 1406,2x |
| 4769 | 72. CORTE SUPREMA, rol N° 20.732-2014, de vein-           87. CORTE SUPREMA, rol N° 37.431-15, de cinco de | Familia | 65085 | 88 | 99,9 % | 739,6x |
| 4770 | 72. ONU, Comité de los Derechos del Niño (CRC) (2013): Observación general | Judicial | 81476 | 76 | 99,9 % | 1072,1x |
| 4771 | 73 Aquellas que desempeñen un cargo de elección popular, de exclusiva confianza | Penal | 178516 | 98 | 99,9 % | 1821,6x |
| 4772 | 73 El autor considera que el esquema inferencial de la toma de decisiones, en el | Judicial | 150341 | 91 | 99,9 % | 1652,1x |
| 4773 | 73 En el caso Lhaka Honhat con Argentina, notas al pie 90 y 91 (párrafos 92 y 93) | Judicial | 81675 | 100 | 99,9 % | 816,8x |
| 4774 | 73. NORAMBUENA, Rocío y SANDOVAL, Sebastián (2019): “Jurisprudencia | Constitucional | 121906 | 122 | 99,9 % | 999,2x |
| 4775 | 74       PUGA VIAL, Juan Esteban: La sociedad anónima y otras sociedades por acciones en el derecho chileno y | Constitucional | 104063 | 61 | 99,9 % | 1706,0x |
| 4776 | 74   Convendrá tener a la vista como referencia el caso español. Particularmente, el artículo 4.1 de la Ley Nº | Civil | 142015 | 115 | 99,9 % | 1234,9x |
| 4777 | 74   Por ejemplo, VERDUGO, PFEFFER y NOGUEIRA (2005), p. 198, señalan: “Si una persona es mutilada o tortu- | Constitucional | 121906 | 81 | 99,9 % | 1505,0x |
| 4778 | 74 El artículo 101 del Código Civil español establece: «El derecho a la pensión se | Familia | 123490 | 75 | 99,9 % | 1646,5x |
| 4779 | 74 Se establece así también en el artículo 154 del DFL 3, en el artículo 1 del DFL 707 | Penal | 178516 | 107 | 99,9 % | 1668,4x |
| 4780 | 74 Sentencia Corte Suprema rol 37181-2015, de 29 de noviembre de 2016. Sobre esta | Judicial | 144656 | 189 | 99,9 % | 765,4x |
| 4781 | 74 Una empresa pública es cualquier empresa, independientemente de su figura | Penal | 178516 | 143 | 99,9 % | 1248,4x |
| 4782 | 74. CORTE SUPREMA, rol N° 5.127-2014, de diecisie-        89. CORTE SUPREMA, rol N° 19.766-2015, de vein- | Familia | 65085 | 96 | 99,9 % | 678,0x |
| 4783 | 74. PIOVESAN, Flavia (2013): “Prohibición de la discriminación por orientación | Judicial | 81476 | 83 | 99,9 % | 981,6x |
| 4784 | 743-758; CASSESE (2005), pp. 100-101; REECE y SMALL (2003), p. 20; STEWART (2005), p. 195; BORNKAMM | Penal | 121924 | 133 | 99,9 % | 916,7x |
| 4785 | 75     Inscripciones | Civil | 171433 | 189 | 99,9 % | 907,1x |
| 4786 | 75 Como bien lo expresa Gabucio (2005: 42), la psicología del pensamiento se | Judicial | 150341 | 132 | 99,9 % | 1138,9x |
| 4787 | 75 Los artículos 62 y 62 bis del Código Tributario regulan este procedimiento, el | Penal | 178516 | 166 | 99,9 % | 1075,4x |
| 4788 | 75 Sobre la garantía constitucional del derecho a la prueba, véase Núñez y Pérez | Judicial | 144656 | 185 | 99,9 % | 781,9x |
| 4789 | 76       CABALLERO GERMAIN, G. (2018): “Sobreendeudamiento y exoneración legal de los saldos insolutos en el | Judicial | 64632 | 75 | 99,9 % | 861,8x |
| 4790 | 76 Estas atribuciones se encuentran contempladas en el artículo 5 numeral 5 del | Penal | 178516 | 152 | 99,9 % | 1174,4x |
| 4791 | 76. Reynaldo Santana Duarte y otro con Corpora- | Civil | 142015 | 93 | 99,9 % | 1527,0x |
| 4792 | 77   Canaris plantea que perfectamente la misma Constitución puede disponer excepcionalmente en su texto la | Laboral | 113458 | 146 | 99,9 % | 777,1x |
| 4793 | 77 Informe final de Chile, vigésima octava reunión del Comité de Expertos del | Penal | 178516 | 92 | 99,9 % | 1940,4x |
| 4794 | 77 Sentencia del Tribunal Oral en lo Penal de Villarrica, RIT 1-2022, 29 de mayo | Penal | 178516 | 205 | 99,9 % | 870,8x |
| 4795 | 77. PODER JUDICIAL DE CHILE, Secretaría Técnica Igualdad de Género y No | Judicial | 81476 | 78 | 99,9 % | 1044,6x |
| 4796 | 78       CONTADOR ROSALES y PALACIOS VERGARA, op. cit;, p. 188 | Judicial | 64632 | 67 | 99,9 % | 964,7x |
| 4797 | 78 Los autores expresan la hipótesis de su primera experimentación (envolved | Judicial | 150341 | 175 | 99,9 % | 859,1x |
| 4798 | 78. GAMONAL C., Sergio (2018), “De la eficacia               empresa o los derechos fundamentales inespecí- | Laboral | 113458 | 117 | 99,9 % | 969,7x |
| 4799 | 78. PODER JUDICIAL DE CHILE, Secretaría Técnica Igualdad de Género y | Judicial | 81476 | 71 | 99,9 % | 1147,5x |
| 4800 | 79 En cuanto a la vigencia de la ley, habiéndose dictado el XXX, se establece un | Penal | 178516 | 167 | 99,9 % | 1069,0x |
| 4801 | 79 La Fase 3 culminó con la evaluación de nuestro país en octubre de 2017, en | Penal | 178516 | 145 | 99,9 % | 1231,1x |
| 4802 | 79. PODER JUDICIAL DE CHILE, Secretaría Técnica Igualdad de Género y No | Judicial | 81476 | 63 | 99,9 % | 1293,3x |
| 4803 | 8     En Latinoamérica este tema ha sido una de las principales preocupaciones de la doctrina. Hay distintos | Penal | 72395 | 96 | 99,9 % | 754,1x |
| 4804 | 8 Antes de la entrada en vigor de la Ley 18.802 de 1989, la norma solo imponía a | Familia | 123490 | 105 | 99,9 % | 1176,1x |
| 4805 | 8 Artículo 19 bis Ley 14.908: «El plazo de prescripción para las acciones ejecutivas | Familia | 97488 | 106 | 99,9 % | 919,7x |
| 4806 | 8 Artículo 222 del Código Civil: «La preocupación fundamental de los padres es | Familia | 97488 | 126 | 99,9 % | 773,7x |
| 4807 | 8 Capítulo basado en el Informe Técnico sobre Alternativas al Encarcelamiento | Penal | 97633 | 57 | 99,9 % | 1712,9x |
| 4808 | 8 Cepal, «Etapas del proceso de envejecimiento demográfico de los países de | Judicial | 82507 | 88 | 99,9 % | 937,6x |
| 4809 | 8 Clermont agrega: «Their formulations beget probabilistic musing, which beget all | Judicial | 150341 | 178 | 99,9 % | 844,6x |
| 4810 | 8 Corte Suprema, rol 8.340-19, del 11 de julio de 2019. Oxman (2017: 71) cuestiona | Penal | 97633 | 133 | 99,9 % | 734,1x |
| 4811 | 8 Dentro de este capítulo se encontraba la Recomendación 11, referida al «Poder | Penal | 178516 | 149 | 99,9 % | 1198,1x |
| 4812 | 8 El artículo 1 de la Ley 20.880 sobre Probidad en la Función Pública y Prevención | Judicial | 144656 | 213 | 99,9 % | 679,1x |
| 4813 | 8 En Corte Suprema, rol 45.630-17, del 27 de febrero de 2018, se cuenta entre los | Penal | 97633 | 104 | 99,9 % | 938,8x |
| 4814 | 8 En esta disposición se enumeran agentes químicos, físicos, biológicos y polvos | Laboral | 98828 | 83 | 99,9 % | 1190,7x |
| 4815 | 8 Es posible acceder al detalle de la labor de este comité en su sitio web, disponible | Judicial | 81675 | 114 | 99,9 % | 716,4x |
| 4816 | 8 La ley se promulgó durante el gobierno del presidente Sebastián Piñera, quien | Familia | 123490 | 122 | 99,9 % | 1012,2x |
| 4817 | 8 La palabra infligir remite a castigo, que lleva a la hipótesis de tormento; aunque | Judicial | 78893 | 65 | 99,9 % | 1213,7x |
| 4818 | 8 Los matrimonios celebrados con anterioridad a la entrada en vigencia de la | Familia | 123490 | 171 | 99,9 % | 722,2x |
| 4819 | 8 Por ejemplo, en el estudio se determina que en un 27% de los casos en que se | Procesal | 86112 | 122 | 99,9 % | 705,8x |
| 4820 | 8 Reflexión expresada en Corte Suprema, rol 14.863-16, del 4 de abril de 2016. Igual | Penal | 97633 | 80 | 99,9 % | 1220,4x |
| 4821 | 8 Rodríguez agrega que de incluirse la entrada y registro a lugar cerrado con | Judicial | 144656 | 165 | 99,9 % | 876,7x |
| 4822 | 8 Sentencia de la Corte Suprema, 31 de enero de 1996. En otro caso de una causa | Penal | 178516 | 117 | 99,9 % | 1525,8x |
| 4823 | 8 Sentencia del caso Sindicato Nacional de Trabajadores de Empresa Santa Isabel | Laboral | 74025 | 110 | 99,9 % | 673,0x |
| 4824 | 8 Sentencia del caso Suez Medioambiente Chile S. A. con Inspección Provincial del | Laboral | 74025 | 75 | 99,9 % | 987,0x |
| 4825 | 8.    BENADAVA, Santiago (2004): Derecho Internacional Público (8ª edi- | Constitucional | 115835 | 113 | 99,9 % | 1025,1x |
| 4826 | 8.    Convención Internacional sobre la protección de | Penal | 72395 | 79 | 99,9 % | 916,4x |
| 4827 | 8.    Corte Constitucional de Colombia, Revisión constitucional de la Ley 1072 | Penal | 121924 | 117 | 99,9 % | 1042,1x |
| 4828 | 8.    FERNÁNDEZ R., José (2006): “Improcedencia | Judicial | 105809 | 115 | 99,9 % | 920,1x |
| 4829 | 8.    GÓMEZ B., Gastón (2005): Derechos fundamen- | Judicial | 105809 | 97 | 99,9 % | 1090,8x |
| 4830 | 8.    Ley Nº 19.886, Ley de Bases sobre Contratos | Laboral | 113458 | 115 | 99,9 % | 986,6x |
| 4831 | 8.    comisión interamericana de derechos | Judicial | 134465 | 107 | 99,9 % | 1256,7x |
| 4832 | 8.   Boletín Estadístico Procedimientos concursales | Judicial | 64632 | 92 | 99,9 % | 702,5x |
| 4833 | 8.   Constitución Política de la República de Guate-           Principios y recomendaciones para la promoción | Administrativo | 89720 | 85 | 99,9 % | 1055,5x |
| 4834 | 8.   Despido discriminatorio grave: cuando es dis-               fundamentales del ciudadano. Debe ser la más | Laboral | 113458 | 119 | 99,9 % | 953,4x |
| 4835 | 8.   ECHR: Caso Khusnutdinov and X v. Russia, ECHR | Penal | 72395 | 91 | 99,9 % | 795,5x |
| 4836 | 8.   SOTO KLOSS, Eduardo (2009): Derecho admi- | Judicial | 105809 | 104 | 99,9 % | 1017,4x |
| 4837 | 8. Atención de usuarios | Judicial | 81476 | 92 | 99,9 % | 885,6x |
| 4838 | 8. Contrato dirigido o normado por el legislador: aunque la ley otorga algún margen a la | Civil | 192585 | 139 | 99,9 % | 1385,5x |
| 4839 | 8. Derecho a la libertad personal y la seguridad individual (art. 19 | Judicial | 89476 | 74 | 99,9 % | 1209,1x |
| 4840 | 8. El derecho a vivir en un medioambiente libre de contaminación. Es | Constitucional | 177323 | 92 | 99,9 % | 1927,4x |
| 4841 | 8. El tratamiento por el empleador de datos obtenidos a través de sistemas de cámaras o videocámaras se | Constitucional | 104063 | 67 | 99,9 % | 1553,2x |
| 4842 | 8. En fin, un último argumento, nos parece que por sí solo, puede esgrimirse para | Familia | 136567 | 193 | 99,9 % | 707,6x |
| 4843 | 8. En la eventualidad de que la morada o el lugar donde pernocta o | Judicial | 89450 | 104 | 99,9 % | 860,1x |
| 4844 | 8. En ningún caso el extranjero puede ser expulsado o devuelto a otro país, sea o no de origen, donde su | Constitucional | 115835 | 117 | 99,9 % | 990,0x |
| 4845 | 8. Establecer medidas de protección | Familia | 95131 | 88 | 99,9 % | 1081,0x |
| 4846 | 8. Experiencias de administración de servicios de salud por parte de | Judicial | 89476 | 94 | 99,9 % | 951,9x |
| 4847 | 8. Generar un distintivo en los sist mas iformáticos de tramitación | Constitucional | 177323 | 133 | 99,9 % | 1333,3x |
| 4848 | 8. Independencia: la función de prevención y cumplimiento | Penal | 119528 | 93 | 99,9 % | 1285,2x |
| 4849 | 8. La definición de la periodicidad de confección y entrega | Procesal | 94881 | 120 | 99,9 % | 790,7x |
| 4850 | 8. La teoría de la posesión inscrita ha producido una cantidad importante de debates en un tema | Civil | 171433 | 197 | 99,9 % | 870,2x |
| 4851 | 8. Los gastos a que dé lugar el procedimiento de expulsión de un trabajador migratorio o un familiar suyo no | Constitucional | 115835 | 169 | 99,9 % | 685,4x |
| 4852 | 8. Memoria histórica: Reimpresión de libros de Sitios de Memoria | Constitucional | 177323 | 156 | 99,9 % | 1136,7x |
| 4853 | 8. Practicar la comunicación directa con las personas con | Judicial | 81476 | 79 | 99,9 % | 1031,3x |
| 4854 | 8. Principios y directrices básicos sobre el derecho de las víctimas de | Constitucional | 177323 | 122 | 99,9 % | 1453,5x |
| 4855 | 8. Que, así las cosas teniendo presente los hechos materia de la senten- | Penal | 194788 | 187 | 99,9 % | 1041,6x |
| 4856 | 8. Tabla N° 8 Estereotipos y mitos respecto de la persona mayor (Edadismo o Ageísmo): extraído | Judicial | 81476 | 101 | 99,9 % | 806,7x |
| 4857 | 8. Un juez o jueza, en sus relaciones personales con miembros | Procesal | 94881 | 81 | 99,9 % | 1171,4x |
| 4858 | 8. Utilizar diversos medios materiales para que las personas mayores | Constitucional | 177323 | 118 | 99,9 % | 1502,7x |
| 4859 | 8. Utilizar todas las herramientas legales disponibles para | Constitucional | 112823 | 59 | 99,9 % | 1912,3x |
| 4860 | 8.1       Consagración normativa | Penal | 72395 | 53 | 99,9 % | 1365,9x |
| 4861 | 8.1. Justo título | Civil | 36671 | 53 | 99,9 % | 691,9x |
| 4862 | 8.12     Caducidad | Laboral | 100583 | 83 | 99,9 % | 1211,8x |
| 4863 | 8.13     Titularidad | Laboral | 100583 | 102 | 99,9 % | 986,1x |
| 4864 | 8.14                Deberes y atribuciones del juez en el | Laboral | 100583 | 65 | 99,9 % | 1547,4x |
| 4865 | 8.16     La sentencia en el procedimiento de | Laboral | 100583 | 71 | 99,9 % | 1416,7x |
| 4866 | 8.17      Recursos | Laboral | 100583 | 97 | 99,9 % | 1036,9x |
| 4867 | 8.18.1 Clases de reclamación | Laboral | 100583 | 107 | 99,9 % | 940,0x |
| 4868 | 8.18.1.1 La acción del artículo 503 del CT | Laboral | 100583 | 101 | 99,9 % | 995,9x |
| 4869 | 8.18.1.2 La acción del artículo 511 y 512 del CT | Laboral | 100583 | 79 | 99,9 % | 1273,2x |
| 4870 | 8.18.2 Recursos | Laboral | 100583 | 122 | 99,9 % | 824,5x |
| 4871 | 8.2          Procedencia en | Laboral | 100583 | 72 | 99,9 % | 1397,0x |
| 4872 | 8.2     Condiciones para ejercer | Penal | 72395 | 48 | 99,9 % | 1508,2x |
| 4873 | 8.2 CADH). Si bien la garantía del debido proceso no comprende | Judicial | 134465 | 102 | 99,9 % | 1318,3x |
| 4874 | 8.2. De orden público y de orden privado. 8.3. Interpretativas, declarativas o explicativas | General | 129559 | 100 | 99,9 % | 1295,6x |
| 4875 | 8.2.1 Características de la Ley N° 20.084 | Penal | 211066 | 140 | 99,9 % | 1507,6x |
| 4876 | 8.2.1 Policía de Investigaciones | Constitucional | 104063 | 79 | 99,9 % | 1317,3x |
| 4877 | 8.2.2 Carabineros de Chile | Constitucional | 104063 | 68 | 99,9 % | 1530,3x |
| 4878 | 8.2.2 Régimen de sanciones contemplado | Penal | 211066 | 145 | 99,9 % | 1455,6x |
| 4879 | 8.2.3 Agencia Nacional de Inteligencia | Constitucional | 104063 | 111 | 99,9 % | 937,5x |
| 4880 | 8.2.4 Protección de datos y actividades | Constitucional | 104063 | 79 | 99,9 % | 1317,3x |
| 4881 | 8.3.1 Defensoría de la Niñez | Constitucional | 104063 | 111 | 99,9 % | 937,5x |
| 4882 | 8.3.2 Instituto Nacional de Derechos Humanos | Constitucional | 104063 | 104 | 99,9 % | 1000,6x |
| 4883 | 8.3.3 Servicio Electoral | Constitucional | 104063 | 75 | 99,9 % | 1387,5x |
| 4884 | 8.4   La diligencia de la audiencia reservada: ¿se trata | Penal | 72395 | 84 | 99,9 % | 861,8x |
| 4885 | 8.4. Reguladoras, completas o autónomas y de aplicación, de reenvío o | General | 129559 | 74 | 99,9 % | 1750,8x |
| 4886 | 8.4.1 Tratamiento de datos de imágenes y video | Constitucional | 104063 | 92 | 99,9 % | 1131,1x |
| 4887 | 8.4.2 Tratamiento de datos de videovigilancia | Constitucional | 104063 | 92 | 99,9 % | 1131,1x |
| 4888 | 8.4.2 Tratamiento de datos de videovigilancia como prueba en los juicios laborales                      220 | Constitucional | 104063 | 63 | 99,9 % | 1651,8x |
| 4889 | 8.5   Deberes y atribuciones del juez en | Laboral | 100583 | 53 | 99,9 % | 1897,8x |
| 4890 | 8.6             La valoración | Penal | 72395 | 52 | 99,9 % | 1392,2x |
| 4891 | 8.6     Efectos de la decisión del juez al | Laboral | 100583 | 55 | 99,9 % | 1828,8x |
| 4892 | 8.7            El DNO y la ley que regula las entrevistas | Penal | 72395 | 105 | 99,9 % | 689,5x |
| 4893 | 8.7     Reclamo | Laboral | 100583 | 93 | 99,9 % | 1081,5x |
| 4894 | 8.7. Clases de           decretos       supremos,        de    conformidad         a    la   función       que | General | 125500 | 96 | 99,9 % | 1307,3x |
| 4895 | 8.8           Audiencia de juicio | Laboral | 100583 | 88 | 99,9 % | 1143,0x |
| 4896 | 8.9. Control de constitucionalidad y de legalidad de los decretos supremos y | General | 125500 | 96 | 99,9 % | 1307,3x |
| 4897 | 8.9.1 Procedimiento de tutela de | Laboral | 100583 | 120 | 99,9 % | 838,2x |
| 4898 | 80 Jequier (2007: 465) entrega como ejemplos del derecho español el caso de un | Judicial | 144656 | 139 | 99,9 % | 1040,7x |
| 4899 | 80 Nieva (2010: 115) considera: «pues bien, esa representación contiene unos datos | Judicial | 150341 | 156 | 99,9 % | 963,7x |
| 4900 | 80. PODER JUDICIAL DE CHILE, Secretaría Técnica Igualdad de Género y No | Judicial | 81476 | 76 | 99,9 % | 1072,1x |
| 4901 | 80. TAPIA, Mauricio (2003): “Responsabilidad civil | Civil | 142015 | 101 | 99,9 % | 1406,1x |
| 4902 | 81 Corte Suprema, rol 18252-2017, del 27 de noviembre de 2018 | Constitucional | 177323 | 132 | 99,9 % | 1343,4x |
| 4903 | 81 En una causa llevada por la Fiscalía Metropolitana Oriente, el exdirector de | Penal | 178516 | 167 | 99,9 % | 1069,0x |
| 4904 | 81.   Decisión de Amparo. Rol Nº C515-11. Consejo | Administrativo | 89720 | 57 | 99,9 % | 1574,0x |
| 4905 | 81. ONU (2019): Nota de prensa. “La violencia y              scielo.org.mx/scielo.php?script=sci_arttext&pi- | Judicial | 89476 | 94 | 99,9 % | 951,9x |
| 4906 | 82   La Ley N° 20.974, de 3 de diciembre de 2006, introdujo modificaciones a las normas sobre procedimiento de | Laboral | 100583 | 71 | 99,9 % | 1416,7x |
| 4907 | 82 Comité para la Eliminación de Todas las Formas de Discriminación contra la | Constitucional | 177323 | 96 | 99,9 % | 1847,1x |
| 4908 | 82 Jequier (2007: 465) reconoce que incluso en el supuesto de que la actividad | Judicial | 144656 | 111 | 99,9 % | 1303,2x |
| 4909 | 82.   Decisión de Amparo. Rol Nº C102-11. Consejo | Administrativo | 89720 | 57 | 99,9 % | 1574,0x |
| 4910 | 82. PODER JUDICIAL DE CHILE, Secretaría Técnica Igualdad de Género y No | Judicial | 81476 | 68 | 99,9 % | 1198,2x |
| 4911 | 83 Adoptadas en el Primer Congreso de las Naciones Unidas sobre Prevención del | Constitucional | 177323 | 114 | 99,9 % | 1555,5x |
| 4912 | 83.   Decisión de Amparo. Rol Nº C188-11. Consejo | Administrativo | 89720 | 57 | 99,9 % | 1574,0x |
| 4913 | 83. La Corte ha establecido, al igual que el Tribunal Europeo de | Judicial | 93914 | 111 | 99,9 % | 846,1x |
| 4914 | 83. PODER JUDICIAL DE CHILE, Secretaría Técnica Igualdad de Género y No | Judicial | 81476 | 71 | 99,9 % | 1147,5x |
| 4915 | 84   Estas divergencias entre estándares de conducta y de control pueden basarse en las diferencias de infor- | Laboral | 113458 | 101 | 99,9 % | 1123,3x |
| 4916 | 84 En el mismo sentido, Nieva es categórico al respecto: «Pero todo lo dicho es | Judicial | 150341 | 157 | 99,9 % | 957,6x |
| 4917 | 84.   Decisión de Amparo. Rol Nº C121-11. Consejo | Administrativo | 89720 | 57 | 99,9 % | 1574,0x |
| 4918 | 84.   MUÑOZ LEÓN, Fernando (2013): “No a ‘separados pero iguales’ | Constitucional | 115835 | 149 | 99,9 % | 777,4x |
| 4919 | 84. PODER JUDICIAL DE CHILE, Secretaría Técnica Igualdad de Género y No | Judicial | 81476 | 71 | 99,9 % | 1147,5x |
| 4920 | 85       VIVANCO (2006), p. 307 | Judicial | 81476 | 58 | 99,9 % | 1404,8x |
| 4921 | 85 En diciembre de 2019, a través del Oficio FN 1111-2019, el Ministerio Público | Penal | 178516 | 171 | 99,9 % | 1044,0x |
| 4922 | 85 Sin embargo, estoy en conocimiento de lo que se afirma coloquialmente acerca | Judicial | 150341 | 109 | 99,9 % | 1379,3x |
| 4923 | 85.   Decisión de Amparo. Rol Nº C70-11. Consejo para | Administrativo | 89720 | 58 | 99,9 % | 1546,9x |
| 4924 | 85. VALDIVIA, José Miguel (2019): “La responsabi- | Civil | 142015 | 97 | 99,9 % | 1464,1x |
| 4925 | 86   REYES RIVEROS (1998), p. 13. A esta postura adhieren, entre otros, los profesores José Luis Cea Egaña y | Judicial | 105809 | 114 | 99,9 % | 928,1x |
| 4926 | 86 Los problemas relativos al desarrollo que tienen las audiencias de preparación | Penal | 178516 | 162 | 99,9 % | 1102,0x |
| 4927 | 86 Romero, Aguirrezabal y Baraona (2008: 226) recuerdan que el legislador de | Judicial | 144656 | 178 | 99,9 % | 812,7x |
| 4928 | 86. PODER JUDICIAL DE CHILE, Comisión Lenguaje Claro: Propuesta Manual | Judicial | 81476 | 55 | 99,9 % | 1481,4x |
| 4929 | 86. Tal como se indica en el presente informe, cuando los | Constitucional | 112823 | 104 | 99,9 % | 1084,8x |
| 4930 | 86. VIDAL, Álvaro (2000): “La construcción de la | Civil | 142015 | 101 | 99,9 % | 1406,1x |
| 4931 | 87 Adoptados y proclamados por la Asamblea General en su resolución 45/111 del | Constitucional | 177323 | 94 | 99,9 % | 1886,4x |
| 4932 | 87. PODER JUDICIAL DE CHILE, Comisión Lenguaje Claro (2015): Glosa-rio | Judicial | 81476 | 50 | 99,9 % | 1629,5x |
| 4933 | 87. VIDAL, Álvaro (2002): “La responsabilidad civil del   4.   Bernarda Olmos Bruna con M. Angélica Hernán- | Civil | 142015 | 88 | 99,9 % | 1613,8x |
| 4934 | 88. Ahora bien, un aspecto central del reconocimiento de la | Judicial | 93914 | 110 | 99,9 % | 853,8x |
| 4935 | 88. Así pues, como principio básico, si los abusos contra los | Constitucional | 112823 | 93 | 99,9 % | 1213,2x |
| 4936 | 88. VIDAL, Álvaro (2006): “La responsabilidad del         5.   Bidasoa Limitada y otros con Patricia Isaacs | Civil | 142015 | 127 | 99,9 % | 1118,2x |
| 4937 | 89 En otras palabras, SORENSEN (1945), p. 694, señala que “las represalias en tiempo de guerra son circuns- | Penal | 121924 | 128 | 99,9 % | 952,5x |
| 4938 | 89. PREVERT Aline, NAVARRO, Oscar y BOGALSKA-MARTIN, Ewa (2012): “La | Judicial | 81476 | 63 | 99,9 % | 1293,3x |
| 4939 | 89. Por otra parte, y en ese orden de ideas, esta Corte ha interpre- | Judicial | 93914 | 62 | 99,9 % | 1514,7x |
| 4940 | 9 Ahora, no es muy feliz la conceptualización del racionalismo probatorio a partir | Judicial | 150341 | 107 | 99,9 % | 1405,1x |
| 4941 | 9 Así lo señala explícitamente Alexy: «Los problemas ligados con la justificación | Judicial | 92792 | 131 | 99,9 % | 708,3x |
| 4942 | 9 Convenio 175 de la OIT de 1994 sobre el Trabajo a Tiempo Parcial. Disponible | Laboral | 98828 | 96 | 99,9 % | 1029,5x |
| 4943 | 9 Corte Suprema, rol 95.545-21, del 9 de junio de 2022. Autorización otorgada por | Penal | 97633 | 100 | 99,9 % | 976,3x |
| 4944 | 9 Covarrubias (2018: 517) aclara que el Tribunal Constitucional Federal Alemán | Judicial | 144656 | 107 | 99,9 % | 1351,9x |
| 4945 | 9 El artículo 177 del Código Procesal Penal, remite a lo establecido en el artículo | Familia | 97488 | 81 | 99,9 % | 1203,6x |
| 4946 | 9 El desprestigio de la política y el lenguaje de los derechos son las causas más | Judicial | 81675 | 74 | 99,9 % | 1103,7x |
| 4947 | 9 En dicho sentido, y en particular sobre la prueba pericial, véase Aguilera (2016) | Procesal | 86112 | 55 | 99,9 % | 1565,7x |
| 4948 | 9 En este capítulo se estableció la necesidad de tipificar correctamente el tráfico de | Penal | 178516 | 110 | 99,9 % | 1622,9x |
| 4949 | 9 En un sentido similar Haack (2004: 58): «It doesn’t follow that more evidence is | Judicial | 150341 | 102 | 99,9 % | 1473,9x |
| 4950 | 9 Esta norma parece referirse a una forma de determinar la pena adolescente más | Penal | 86906 | 61 | 99,9 % | 1424,7x |
| 4951 | 9 La cuestión del reconocimiento del matrimonio civil y, posteriormente, las | Familia | 123490 | 89 | 99,9 % | 1387,5x |
| 4952 | 9 Las actividades de la vida diaria comprenden las acciones básicas que involucran | Judicial | 87950 | 94 | 99,9 % | 935,6x |
| 4953 | 9 Para más información, véase la sentencia del Tribunal Constitucional en causa | Judicial | 87950 | 63 | 99,9 % | 1396,0x |
| 4954 | 9 STS español, 2/1997 del 29 de noviembre de 1997. Ponente: Roberto García-Calvo | Judicial | 62514 | 68 | 99,9 % | 919,3x |
| 4955 | 9 Sentencia Corte Suprema de 26 de septiembre de 2022, de apelación en recurso de | Judicial | 144656 | 113 | 99,9 % | 1280,1x |
| 4956 | 9 Sentencia Corte Suprema de 30 de diciembre de 2022, rol ingreso número | Judicial | 144656 | 74 | 99,9 % | 1954,8x |
| 4957 | 9 Sentencia de la Corte de Apelaciones de Santiago, rol 2.620-2020, 17 de noviem- | Familia | 97488 | 80 | 99,9 % | 1218,6x |
| 4958 | 9 Sentencia del caso Messer Chile Limitada/Ministerio de Economía, Fomento y | Laboral | 74025 | 104 | 99,9 % | 711,8x |
| 4959 | 9 Sobre estereotipos de género, además de la sentencia del caso Atala que viene a | Judicial | 92792 | 83 | 99,9 % | 1118,0x |
| 4960 | 9 Una recopilación de informes que dan cuenta de las crisis en Castillo-Gallardo | Constitucional | 46896 | 61 | 99,9 % | 768,8x |
| 4961 | 9 Véase la Observación General número 24 (párrafo 95b) y las Reglas de la Habana | Penal | 86906 | 61 | 99,9 % | 1424,7x |
| 4962 | 9 Y ello es coincidente, como rescata la historia de la ley, con las disposiciones del | Judicial | 62514 | 89 | 99,9 % | 702,4x |
| 4963 | 9.    Corte Constitucional de Colombia, Demanda de inconstitucionalidad con- | Penal | 121924 | 79 | 99,9 % | 1543,3x |
| 4964 | 9.    Decreto con Fuerza de Ley Nº 3. Ministerio Se- | Administrativo | 89720 | 65 | 99,9 % | 1380,3x |
| 4965 | 9.    Dictamen N° 2875/72 de 22 de julio de 2003. Ma- | Laboral | 113458 | 113 | 99,9 % | 1004,1x |
| 4966 | 9.    Ley Nº 18.216, establece penas que indica como sustitutivas a las penas | Familia | 95131 | 65 | 99,9 % | 1463,6x |
| 4967 | 9.   CS, roles Nos 3412-2015, 23.587-2015, 17.405- | Judicial | 105809 | 106 | 99,9 % | 998,2x |
| 4968 | 9.   Daño moral en sede contractual (en general): Es        14. Error médico: Es aquella falla que comete el | Civil | 142015 | 143 | 99,9 % | 993,1x |
| 4969 | 9.   Ley Nº 20.146, establece reglas especiales para la apelación en causas rela- | Constitucional | 121906 | 66 | 99,9 % | 1847,1x |
| 4970 | 9.   PAREJO ALFONSO, Luciano (2003): Derecho | Judicial | 105809 | 105 | 99,9 % | 1007,7x |
| 4971 | 9.   Reclamo Ilegalidad: Acción de impugnación que | Administrativo | 89720 | 76 | 99,9 % | 1180,5x |
| 4972 | 9. A falta de toda ley, el juez debía recurrir al monarca y no le estaba permitido fallar | Civil | 90056 | 57 | 99,9 % | 1579,9x |
| 4973 | 9. Como principio general, procede decretar indemnización por daño moral en la esfera | Civil | 120848 | 84 | 99,9 % | 1438,7x |
| 4974 | 9. Coordinación interinstitucional para el abordaje de delitos de | Constitucional | 177323 | 111 | 99,9 % | 1597,5x |
| 4975 | 9. El contacto social entre miembros de la judicatura y miembros de | Procesal | 94881 | 88 | 99,9 % | 1078,2x |
| 4976 | 9. En este contexto, este tribunal entiende que la expresión «condenas | Penal | 194788 | 150 | 99,9 % | 1298,6x |
| 4977 | 9. Entregar a los notificadores y a las notificadoras la información | Constitucional | 177323 | 110 | 99,9 % | 1612,0x |
| 4978 | 9. Excepcionalmente, y por motivos justificados, recibir la prueba | Familia | 100107 | 75 | 99,9 % | 1334,8x |
| 4979 | 9. Implementación curso para público general de introducción a los | Constitucional | 177323 | 104 | 99,9 % | 1705,0x |
| 4980 | 9. Informar al tribunal —por el medio más idóneo, expedito y en | Judicial | 89450 | 118 | 99,9 % | 758,1x |
| 4981 | 9. La subordinación suspende el cómputo de la prescripción de las acciones de cobro | Civil | 120848 | 141 | 99,9 % | 857,1x |
| 4982 | 9. Plan de Formación Ciudadana: Orientaciones al sistema escolar | Constitucional | 177323 | 152 | 99,9 % | 1166,6x |
| 4983 | 9. Preparar la sala de audiencias y los sistemas accesorios antes de | Judicial | 52128 | 65 | 99,9 % | 802,0x |
| 4984 | 9. Proporcionalidad: los controles implementados por la | Penal | 119528 | 68 | 99,9 % | 1757,8x |
| 4985 | 9. Que también el actor recurrió de apelación, en cuanto a que no se acogió su acción de | Judicial | 79146 | 118 | 99,9 % | 670,7x |
| 4986 | 9. Que, en consecuencia, en este caso la Comisión recurrida ha negado | Penal | 194788 | 198 | 99,9 % | 983,8x |
| 4987 | 9. Renovación de la Política Nacional para la Gestión del Riesgo de | Constitucional | 177323 | 150 | 99,9 % | 1182,2x |
| 4988 | 9. Responsabilidad por cumplimiento de cargo. No es eximente | Penal | 121924 | 93 | 99,9 % | 1311,0x |
| 4989 | 9. Supervisar la elaboración del informe contable que consolide la | Judicial | 52128 | 74 | 99,9 % | 704,4x |
| 4990 | 9. Tabla N° 9: Mitos hacia las personas con discapacidad (Confeccionada a partir de los 10 | Judicial | 81476 | 62 | 99,9 % | 1314,1x |
| 4991 | 9. Toda notificación que no sea personal, por cédula y aquellas que | Judicial | 89450 | 94 | 99,9 % | 951,6x |
| 4992 | 9. Todos los asuntos en que se impute la comisión de cualquier falta a adolescentes | Familia | 190697 | 137 | 99,9 % | 1391,9x |
| 4993 | 9.- CAPPELLETTI y GARTH (1987), p. 23 | Procesal | 96699 | 93 | 99,9 % | 1039,8x |
| 4994 | 9.1            El ejercicio progresivo de los | Penal | 72395 | 53 | 99,9 % | 1365,9x |
| 4995 | 9.1     El fenómeno de la minería de datos y el | Constitucional | 104063 | 83 | 99,9 % | 1253,8x |
| 4996 | 9.2.1 Oficialidad en el inicio de la ejecución | Laboral | 100583 | 130 | 99,9 % | 773,7x |
| 4997 | 9.2.2 Remisión de la causa al juzgado de | Laboral | 100583 | 133 | 99,9 % | 756,3x |
| 4998 | 9.2.3 Tramitación de la causa en sede ejecución | Laboral | 100583 | 72 | 99,9 % | 1397,0x |
| 4999 | 9.2.4 Embargo sin orden previa | Laboral | 100583 | 74 | 99,9 % | 1359,2x |
| 5000 | 9.2.5 Sentencia de pago o remate | Laboral | 100583 | 130 | 99,9 % | 773,7x |
| 5001 | 9.2.6 Adjudicación con cargo al | Laboral | 100583 | 70 | 99,9 % | 1436,9x |
| 5002 | 9.2.7 Recursos | Laboral | 100583 | 91 | 99,9 % | 1105,3x |
| 5003 | 9.2.8 Medida cautelar especial | Laboral | 100583 | 115 | 99,9 % | 874,6x |
| 5004 | 9.2.9 Aseguramiento del acuerdo de pago en cuotas | Laboral | 100583 | 136 | 99,9 % | 739,6x |
| 5005 | 9.3. Se dedujo acción penal y el procedimiento se suspendió o terminó sin que la | Civil | 96458 | 123 | 99,9 % | 784,2x |
| 5006 | 9.3.1 Oficialidad | Laboral | 100583 | 79 | 99,9 % | 1273,2x |
| 5007 | 9.3.2 Liquidación coetánea al “despáchese” | Laboral | 100583 | 97 | 99,9 % | 1036,9x |
| 5008 | 9.3.3 Notificación y requerimiento | Laboral | 100583 | 133 | 99,9 % | 756,3x |
| 5009 | 9.3.4 Remisión a normas del cumplimiento de sentencia | Laboral | 100583 | 132 | 99,9 % | 762,0x |
| 5010 | 9.5                Datos en internet | Constitucional | 104063 | 93 | 99,9 % | 1119,0x |
| 5011 | 9.5. Caracteres de la costumbre. 9.6. Clasificación de la costumbre. 9.7. Valor y fuerza | General | 129559 | 178 | 99,9 % | 727,9x |
| 5012 | 9.9. Prescripción de la acción derivada de un contrato de prestación de | Civil | 71319 | 46 | 99,9 % | 1550,4x |
| 5013 | 90   Para efectos de este material, no se mencionan causas tramitadas bajo la Ley No 21.120 por reserva en el | Judicial | 89476 | 70 | 99,9 % | 1278,2x |
| 5014 | 90   Referencias | Constitucional | 46896 | 54 | 99,9 % | 868,4x |
| 5015 | 90 La autora (2007: 728) expresa la diferencia entre estos tipos de prueba de la | Judicial | 150341 | 172 | 99,9 % | 874,1x |
| 5016 | 90.   Cumplido Cereceda, Francisco (1996): “Alcances de la modificación del | Penal | 121924 | 85 | 99,9 % | 1434,4x |
| 5017 | 90. CORTE SUPREMA, rol N° 38.321-16, de veintisiete        105. CORTE SUPREMA, rol N° 37.368-2017, de diez de | Familia | 65085 | 88 | 99,9 % | 739,6x |
| 5018 | 90. GARCÍA ODGERS, Ramón (2019b): “El case management en el proceso | Procesal | 96699 | 122 | 99,9 % | 792,6x |
| 5019 | 90. Los detalles de este largo empeño legislativo no son objeto del | Judicial | 83934 | 98 | 99,9 % | 856,5x |
| 5020 | 90. ROMAÑACH, Javier y LOBATO, Manuel (2005): “Diversidad funcional, nuevo | Constitucional | 121906 | 71 | 99,9 % | 1717,0x |
| 5021 | 90. Respecto al derecho a la identidad, esta Corte ha indicado | Judicial | 93914 | 113 | 99,9 % | 831,1x |
| 5022 | 90. VIDAL, Álvaro (2008): “La carga de mitigar las | Civil | 142015 | 87 | 99,9 % | 1632,4x |
| 5023 | 91 Si bien es posible indicar que Nieva acoge un modelo multidimensional de la | Judicial | 150341 | 183 | 99,9 % | 821,5x |
| 5024 | 91 Sobre el principio de legalidad en materia de Derecho Procesal, véase Núñez y | Judicial | 144656 | 93 | 99,9 % | 1555,4x |
| 5025 | 91.   Cumplido Cereceda, Francisco (2003): “La reforma constitucional de 1989 | Penal | 121924 | 87 | 99,9 % | 1401,4x |
| 5026 | 91. CORTE SUPREMA, rol N° 37.792-2.015, de veinti-         106. CORTE SUPREMA, rol Nº 34.109-2017, de once de | Familia | 65085 | 96 | 99,9 % | 678,0x |
| 5027 | 91. La Corte observa que tanto la Comisión como los representantes | Judicial | 144656 | 137 | 99,9 % | 1055,9x |
| 5028 | 91. RONCONI Liliana y VITA Leticia (2012): “El principio de igualdad en la ense- | Judicial | 81476 | 84 | 99,9 % | 970,0x |
| 5029 | 91. VIDAL, Álvaro (2008): “Las acciones civiles deri- | Civil | 142015 | 107 | 99,9 % | 1327,2x |
| 5030 | 92 Paraita lo explica de esta forma: «hay que señalar que aquello que se activa, que | Judicial | 150341 | 146 | 99,9 % | 1029,7x |
| 5031 | 92.   Corte Suprema, Desafuero Pinochet Ugarte (2000): 8 agosto 2000, rol Nº | Penal | 121924 | 67 | 99,9 % | 1819,8x |
| 5032 | 92. A fin de investigar y enjuiciar correctamente esas conductas | Constitucional | 112823 | 104 | 99,9 % | 1084,8x |
| 5033 | 92. Este Tribunal estima que no es en sí mismo incompatible con la | Judicial | 144656 | 161 | 99,9 % | 898,5x |
| 5034 | 92. Por lo demás, el derecho a la identidad y, por tanto, el derecho | Judicial | 93914 | 113 | 99,9 % | 831,1x |
| 5035 | 93 Esto es lo que habría ocurrido con la decisión de Alberto Ayala, entonces fiscal | Penal | 178516 | 109 | 99,9 % | 1637,8x |
| 5036 | 93 La clasificación de los arbitrajes, según las facultades del compromisario, en | Judicial | 144656 | 176 | 99,9 % | 821,9x |
| 5037 | 93 N° 9 CPR), y c) control de constitucionalidad de los decretos | Judicial | 105809 | 117 | 99,9 % | 904,4x |
| 5038 | 93. CORTE SUPREMA, rol N° 46.521-2016 de trece             108. CORTE SUPREMA, rol N° 35.256-2017, de seis de | Familia | 65085 | 94 | 99,9 % | 692,4x |
| 5039 | 93. En relación con la identidad de género y sexual, esta Corte | Judicial | 93914 | 87 | 99,9 % | 1079,5x |
| 5040 | 93. RODRÍGUEZ YAGÜE, Ana Cristina, (2007): La tutela penal del derecho a no | Judicial | 81476 | 66 | 99,9 % | 1234,5x |
| 5041 | 94. CORTE SUPREMA, rol N° 46.516-2016, de trece            109. CORTE SUPREMA, rol N° 2.292-2018, de veintiu- | Familia | 65085 | 84 | 99,9 % | 774,8x |
| 5042 | 94. En este punto, corresponde recordar que la identidad de | Judicial | 93914 | 72 | 99,9 % | 1304,4x |
| 5043 | 95 De allí que sea esencial determinar claramente si los tribunales arbitrales son | Judicial | 144656 | 171 | 99,9 % | 845,9x |
| 5044 | 95 En este sentido, el autor Taruffo (2009a: 196) considera sobre la repercusión e | Judicial | 150341 | 123 | 99,9 % | 1222,3x |
| 5045 | 95. CORTE SUPREMA, rol N° 45.838-2016 de quince            110. CORTE SUPREMA, rol N° 1324-18, de seis de | Familia | 65085 | 88 | 99,9 % | 739,6x |
| 5046 | 95. De esa forma, el sexo, así como las identidades, las funciones | Judicial | 93914 | 113 | 99,9 % | 831,1x |
| 5047 | 96       CAVOUKIAN, Ann: Privacy by Design. The 7 Foundational Principles. Implementation and Mapping of Fair | Constitucional | 104063 | 75 | 99,9 % | 1387,5x |
| 5048 | 96. CORTE SUPREMA, rol N° 41.066-2016, de vein-            111. CORTE SUPREMA, rol N° 3363-18, de veinte de | Familia | 65085 | 89 | 99,9 % | 731,3x |
| 5049 | 96. Es evidente que las condiciones en las que participa un niño | Judicial | 87237 | 119 | 99,9 % | 733,1x |
| 5050 | 96. Las consideraciones del juez de primera instancia demuestran | Penal | 72395 | 98 | 99,9 % | 738,7x |
| 5051 | 96. SALINERO ECHEVERRÍA, Sebastián. (2013): “La nueva agravante penal | Judicial | 81476 | 62 | 99,9 % | 1314,1x |
| 5052 | 97  SEIFERT, Achim (2012), “L’effet horizontal des droits fondamentaux”, Revue Trimestrielle de Droit Européen | Laboral | 113458 | 128 | 99,9 % | 886,4x |
| 5053 | 97.   CORTE SUPREMA, rol N° 87.853-2016, de trece          112. CORTE SUPREMA, rol N° 1.081-2018, de veinte de | Familia | 65085 | 94 | 99,9 % | 692,4x |
| 5054 | 97.   Corte Suprema, Martínez y otros c. Fisco de Chile (2006): sentencia 27 di- | Penal | 121924 | 72 | 99,9 % | 1693,4x |
| 5055 | 97. En atención a lo previamente indicado, la Corte coincide con | Judicial | 93914 | 111 | 99,9 % | 846,1x |
| 5056 | 98 Véase Comisión de Derechos Humanos (1993) párrs. 14 y 15: “14. It cannot be denied that both individuals | Judicial | 134465 | 167 | 99,9 % | 805,2x |
| 5057 | 98. CORTE SUPREMA, rol N° 59.106-2016, de cinco            113. CORTE SUPREMA, rol N° 33.793-2017, veintisiete | Familia | 65085 | 94 | 99,9 % | 692,4x |
| 5058 | 98. SHELTON, Dinah (2008): “Prohibición de discriminación en el Derecho | Judicial | 81476 | 62 | 99,9 % | 1314,1x |
| 5059 | 989 Código Civil; la calidad de legitimario conforme al artículos 1182 Código Civil; y | Familia | 123490 | 70 | 99,9 % | 1764,1x |
| 5060 | 99   En el caso de la Constitución de España (artículo 18), se incluye de manera expresa el reconocimiento al | Judicial | 89476 | 70 | 99,9 % | 1278,2x |
| 5061 | 99   Siguiendo el análisis de ZÚÑIGA (en imprenta) no “es exagerado sostener que 2018 ha sido el año de la | Constitucional | 121906 | 161 | 99,9 % | 757,2x |
| 5062 | 99 En este párrafo he utilizado la palabra verdadera solo para que se entienda de | Judicial | 150341 | 185 | 99,9 % | 812,7x |
| 5063 | 99. CORTE SUPREMA, rol N° 50.055-2016, de doce             114. CORTE SUPREMA, rol N° 8.363-2018, de ocho de | Familia | 65085 | 96 | 99,9 % | 678,0x |
| 5064 | 99. En ese mismo sentido, esta Corte comparte lo señalado por | Judicial | 93914 | 107 | 99,9 % | 877,7x |
| 5065 | A nivel individual:                    a nivel social | Judicial | 81476 | 49 | 99,9 % | 1662,8x |
| 5066 | ACTA Nº 022 | Judicial | 79146 | 68 | 99,9 % | 1163,9x |
| 5067 | Academia judicial de chile | Constitucional | 115835 | 120 | 99,9 % | 965,3x |
| 5068 | Actividad                    plazo                  responsable | Procesal | 94881 | 88 | 99,9 % | 1078,2x |
| 5069 | Aduanas: etapa judicial | Judicial | 62888 | 66 | 99,9 % | 952,8x |
| 5070 | Al caso concreto sub lite, contraria al párrafo primero del número 3° del | Civil | 192585 | 209 | 99,9 % | 921,5x |
| 5071 | Apoderado                                                     eeee | Familia | 100107 | 78 | 99,9 % | 1283,4x |
| 5072 | Atención video llamada | Judicial | 53521 | 45 | 99,9 % | 1189,4x |
| 5073 | C) pago con subrogación | Civil | 75968 | 68 | 99,9 % | 1117,2x |
| 5074 | C1790-14 | Administrativo | 89720 | 94 | 99,9 % | 954,5x |
| 5075 | C3420-2082 | Administrativo | 89720 | 63 | 99,9 % | 1424,1x |
| 5076 | CIDO EN EL ARTÍCULO 67 DE LA LEY Nº 19.947 | Judicial | 79146 | 74 | 99,9 % | 1069,5x |
| 5077 | Cadh                               7                                   13% | Constitucional | 115835 | 165 | 99,9 % | 702,0x |
| 5078 | Capitulo i: aspectos generales | Civil | 110175 | 78 | 99,9 % | 1412,5x |
| 5079 | Capitulo i: de las convenciones matrimoniales.5 | Familia | 136567 | 157 | 99,9 % | 869,9x |
| 5080 | Capitulo i: regulación, concepto y caracteristicas del | Civil | 50203 | 41 | 99,9 % | 1224,5x |
| 5081 | Capitulo iv: de los derechos, deberes y obligaciones entre los | Familia | 62470 | 72 | 99,9 % | 867,6x |
| 5082 | Capitulo iv: interpretacion de los contratos.384 | Civil | 110175 | 65 | 99,9 % | 1695,0x |
| 5083 | Capítulo 2                                                                          27 | Procesal | 66012 | 58 | 99,9 % | 1138,1x |
| 5084 | Capítulo 2                                                   (2001): “Discrecionalidad y técnica en la admi- | Judicial | 105809 | 105 | 99,9 % | 1007,7x |
| 5085 | Capítulo 3                                                           72 | Procesal | 66012 | 45 | 99,9 % | 1466,9x |
| 5086 | Capítulo 6                                                   jurisprudencia (1990-1995)”, en Revista de De- | Judicial | 105809 | 110 | 99,9 % | 961,9x |
| 5087 | Capítulo II de la citada ley, que estamos analizando. Dichos efectos civiles se | Familia | 190697 | 202 | 99,9 % | 944,0x |
| 5088 | Capítulo III de la Constitución, se infiere que lo que el | Constitucional | 112823 | 87 | 99,9 % | 1296,8x |
| 5089 | Capítulo Indígena de la Política Energética 2050 | Judicial | 134465 | 101 | 99,9 % | 1331,3x |
| 5090 | Capítulo V: Incapacidades e indignidades para suceder. 1.- Requisitos para | Civil | 92843 | 89 | 99,9 % | 1043,2x |
| 5091 | Capítulo ii: de la determinación de la filiación | Familia | 62470 | 79 | 99,9 % | 790,8x |
| 5092 | Capítulo ii: las categorías contractuales | Civil | 110175 | 83 | 99,9 % | 1327,4x |
| 5093 | Capítulo iii: principios fundamentales de la contratación | Civil | 110175 | 115 | 99,9 % | 958,0x |
| 5094 | Capítulo vi: de la revocación del testamento | Civil | 50203 | 75 | 99,9 % | 669,4x |
| 5095 | Capítulo vii: de la liquidación de la sociedad conyugal | Familia | 136567 | 157 | 99,9 % | 869,9x |
| 5096 | Capítulo viii: de los bienes reservados de la mujer casada | Familia | 136567 | 137 | 99,9 % | 996,8x |
| 5097 | Capítulo, siempre que incida sustancialmente en el quórum del | Judicial | 64632 | 57 | 99,9 % | 1133,9x |
| 5098 | Cargo | Familia | 85324 | 79 | 99,9 % | 1080,1x |
| 5099 | Cedaw | Familia | 65085 | 61 | 99,9 % | 1067,0x |
| 5100 | Citacion a juicio-fecha                               21 de julio de 2020, a las 11:15 horas | Familia | 100107 | 58 | 99,9 % | 1726,0x |
| 5101 | Citada | Constitucional | 115835 | 109 | 99,9 % | 1062,7x |
| 5102 | Comisión interamericana de derechos humanos | Constitucional | 177323 | 145 | 99,9 % | 1222,9x |
| 5103 | Conadi | Judicial | 134465 | 127 | 99,9 % | 1058,8x |
| 5104 | Contrato de arrendamiento113 | Civil | 71319 | 53 | 99,9 % | 1345,6x |
| 5105 | Contrato de compraventa1 | Civil | 153962 | 150 | 99,9 % | 1026,4x |
| 5106 | Cuestionario | Familia | 190697 | 198 | 99,9 % | 963,1x |
| 5107 | De la responsabilidad civil en general | Civil | 96458 | 76 | 99,9 % | 1269,2x |
| 5108 | De la responsabilidad objetiva1 | Civil | 26055 | 35 | 99,9 % | 744,4x |
| 5109 | De la sucesion por causa de muerte1 | Civil | 92843 | 83 | 99,9 % | 1118,6x |
| 5110 | Demandar la resolución de la compraventa en el evento de que no le | Civil | 153962 | 162 | 99,9 % | 950,4x |
| 5111 | Derecho a la identidad de género y la rectifi- | Judicial | 93914 | 68 | 99,9 % | 1381,1x |
| 5112 | Dl 1094) | Constitucional | 115835 | 150 | 99,9 % | 772,2x |
| 5113 | Ds 66                                 ds 40 | Judicial | 134465 | 111 | 99,9 % | 1211,4x |
| 5114 | Ds.255-ds.27 | Judicial | 82507 | 46 | 99,9 % | 1793,6x |
| 5115 | Ee. uu. (usca) | Constitucional | 112823 | 104 | 99,9 % | 1084,8x |
| 5116 | El derecho civil y la codificación1 | Civil | 90056 | 106 | 99,9 % | 849,6x |
| 5117 | En chile | Procesal | 96699 | 124 | 99,9 % | 779,8x |
| 5118 | En cuanto a la excepcion de prescripcion | Civil | 192585 | 188 | 99,9 % | 1024,4x |
| 5119 | En cuanto al fondo | Civil | 192585 | 161 | 99,9 % | 1196,2x |
| 5120 | En cuanto al recurso de casación en el fondo del | Civil | 171433 | 209 | 99,9 % | 820,3x |
| 5121 | Examen de compatibilidad entre los estándares internacionales | Constitucional | 115835 | 117 | 99,9 % | 990,0x |
| 5122 | Factores de riesgo de la dinámica relacional | Familia | 95131 | 50 | 99,9 % | 1902,6x |
| 5123 | Factores de riesgo del imputado | Familia | 95131 | 59 | 99,9 % | 1612,4x |
| 5124 | Familia de santiago, que se individualiza en la firma electrónica | Judicial | 79146 | 49 | 99,9 % | 1615,2x |
| 5125 | Familiar haití | Constitucional | 115835 | 159 | 99,9 % | 728,5x |
| 5126 | Genchi | Penal | 194788 | 115 | 99,9 % | 1693,8x |
| 5127 | Hipoteca | Civil | 66868 | 62 | 99,9 % | 1078,5x |
| 5128 | Hipoteca67 | Civil | 66868 | 63 | 99,9 % | 1061,4x |
| 5129 | I.- del pasivo de la sociedad conyugal y de los cónyuges en relación con | Familia | 136567 | 126 | 99,9 % | 1083,9x |
| 5130 | Ii.-    el mutuo disenso o resciliación | Civil | 75968 | 67 | 99,9 % | 1133,9x |
| 5131 | Ii.- administracion ordinaria de los bienes propios de la mujer y | Familia | 136567 | 70 | 99,9 % | 1951,0x |
| 5132 | Ii.- administración ordinaria de los bienes propios de la mujer y del | Familia | 136567 | 106 | 99,9 % | 1288,4x |
| 5133 | Ii.- del pasivo de la sociedad conyugal y de los cónyuges en relación | Familia | 136567 | 167 | 99,9 % | 817,8x |
| 5134 | Importante | Procesal | 94881 | 72 | 99,9 % | 1317,8x |
| 5135 | Información general | Familia | 100107 | 57 | 99,9 % | 1756,3x |
| 5136 | Inglaterra y francia | Procesal | 96699 | 94 | 99,9 % | 1028,7x |
| 5137 | Ipe/ipa | Constitucional | 115835 | 102 | 99,9 % | 1135,6x |
| 5138 | Irrelevante si el tercero tenía o no conocimiento de la prohibición al | General | 166275 | 200 | 99,9 % | 831,4x |
| 5139 | Iv.- de la terminacion del matrimonio | Familia | 190697 | 109 | 99,9 % | 1749,5x |
| 5140 | Ix.- de los efectos del matrimonio | Familia | 190697 | 102 | 99,9 % | 1869,6x |
| 5141 | La experiencia de | Procesal | 96699 | 71 | 99,9 % | 1362,0x |
| 5142 | La política migratoria chilena | Constitucional | 115835 | 94 | 99,9 % | 1232,3x |
| 5143 | La sucesión por causa de muerte117 | Civil | 92843 | 55 | 99,9 % | 1688,1x |
| 5144 | Los NNA NO SON TOMADOS EN CUENTA | Familia | 100107 | 65 | 99,9 % | 1540,1x |
| 5145 | Los derechos de las personas migrantes | Constitucional | 115835 | 101 | 99,9 % | 1146,9x |
| 5146 | MIl. Y UNA PREGUNTAS EN DERECHO PROCESAL CIVIL | Procesal | 95124 | 93 | 99,9 % | 1022,8x |
| 5147 | Materiales | Judicial | 30834 | 36 | 99,9 % | 856,5x |
| 5148 | Migración y el sistema jurídico chileno | Constitucional | 115835 | 123 | 99,9 % | 941,7x |
| 5149 | Migratoria chilena | Constitucional | 115835 | 130 | 99,9 % | 891,0x |
| 5150 | Movilidad humana en | Constitucional | 115835 | 130 | 99,9 % | 891,0x |
| 5151 | NADAVA (1997), p. 54; VAN SCHAACK (1997), p. 2261; BIANCHI (1999), p. 272; BYERS (1999), p. 186; KELLEY | Penal | 121924 | 149 | 99,9 % | 818,3x |
| 5152 | Normas jurídicas citadas | Constitucional | 115835 | 110 | 99,9 % | 1053,0x |
| 5153 | Nos y libertades fundamentales de los | Judicial | 134465 | 79 | 99,9 % | 1702,1x |
| 5154 | N° 11.978-2018.- | Constitucional | 121906 | 130 | 99,9 % | 937,7x |
| 5155 | N° 19.253 | Judicial | 134465 | 83 | 99,9 % | 1620,1x |
| 5156 | N° 19.620 | Familia | 100107 | 67 | 99,9 % | 1494,1x |
| 5157 | N° 19.947 | Familia | 100107 | 91 | 99,9 % | 1100,1x |
| 5158 | OFICIO Nº | Judicial | 79146 | 85 | 99,9 % | 931,1x |
| 5159 | ORAKHELASHVILI (2006), p. 43; THIENEL (2006), p. 363; YARWOOD (2006), p. 33; COHEN (2007), p. 111; KUTZ | Penal | 121924 | 98 | 99,9 % | 1244,1x |
| 5160 | Orden del día | Judicial | 79146 | 48 | 99,9 % | 1648,9x |
| 5161 | Ordinaria de la sociedad conyugal | Familia | 136567 | 178 | 99,9 % | 767,2x |
| 5162 | Parte IX. Disposiciones finales | Judicial | 81675 | 75 | 99,9 % | 1089,0x |
| 5163 | Parte de la doctrina suele asociar el carga de la prueba en un sentido | Judicial | 150341 | 188 | 99,9 % | 799,7x |
| 5164 | Parte de la doctrina y jurisprudencia estima que la indemnización | Laboral | 113458 | 111 | 99,9 % | 1022,1x |
| 5165 | Parte de los Tribunales Ambientales: ¿Avance y/o Retroceso? | Constitucional | 112823 | 136 | 99,9 % | 829,6x |
| 5166 | Parte demandada | Judicial | 79146 | 96 | 99,9 % | 824,4x |
| 5167 | Parte en los Convenios de Ginebra es la condición más importante | Penal | 121924 | 87 | 99,9 % | 1401,4x |
| 5168 | Parte en sus Protocolos adicionales, así como la trascendencia de los | Penal | 121924 | 92 | 99,9 % | 1325,3x |
| 5169 | Parte la Directiva complementando algunas definiciones ausentes en | Constitucional | 104063 | 85 | 99,9 % | 1224,3x |
| 5170 | Parte que adopten disposiciones positivas para reducir o elimi- | Judicial | 81476 | 93 | 99,9 % | 876,1x |
| 5171 | Participacion en los gananciales | Familia | 136567 | 135 | 99,9 % | 1011,6x |
| 5172 | Personas migrantes | Constitucional | 115835 | 59 | 99,9 % | 1963,3x |
| 5173 | Poder general44 | Civil | 42773 | 31 | 99,9 % | 1379,8x |
| 5174 | Por casas o departamentos, piezas, secciones o locales y fija la renta maxima que se podra | Civil | 192585 | 141 | 99,9 % | 1365,9x |
| 5175 | Prcgunta: COMO ACTUA EL JUEZ EN LA AUDIENCIA DE CONCIPregunta: &QUE ES EL LLAMADO A CONCILIACION? | Procesal | 95124 | 54 | 99,9 % | 1761,6x |
| 5176 | Prcgunta: QUE SIGNIFICA PREPARAR EL RECURSO DE CASACION | Procesal | 95124 | 58 | 99,9 % | 1640,1x |
| 5177 | PregUnta: COMO SE CUMPLE LA SENTENCIA CUANDO ORDENA LA | Procesal | 95124 | 49 | 99,9 % | 1941,3x |
| 5178 | PregUnta: COMPETENCIA EN LOS JUICIOS SOBRE COBRO DE HOJ | Procesal | 95124 | 49 | 99,9 % | 1941,3x |
| 5179 | PregUnta: FALLO DE LA ACCION DE INCONSTITUCIONALIDAD | Procesal | 95124 | 105 | 99,9 % | 905,9x |
| 5180 | PregUnta:ANTE QUE TRIBUNAL SE INTERPONE? | Procesal | 95124 | 104 | 99,9 % | 914,7x |
| 5181 | PregUnta:CUANDO ESDESFAVORABLEALFISCOLASENTENCIA? | Procesal | 95124 | 102 | 99,9 % | 932,6x |
| 5182 | Pregunta: &A QUE TRIBUNAL CORRESPONDE LA EJECUCION DE | Procesal | 95124 | 55 | 99,9 % | 1729,5x |
| 5183 | Pregunta: &A QUIEN AMPARAN LAS QUERELLAS POSESORIAS? | Procesal | 95124 | 50 | 99,9 % | 1902,5x |
| 5184 | Pregunta: &COMO SE INICIA EL JUICIO ORDINARIO? | Procesal | 95124 | 133 | 99,9 % | 715,2x |
| 5185 | Pregunta: &COMO SE NOTIFICA LA RESOLUCION QUE DECRETA | Procesal | 95124 | 62 | 99,9 % | 1534,3x |
| 5186 | Pregunta: &COMO SE RESUELVE ESTA CONTRADICCION? | Procesal | 95124 | 81 | 99,9 % | 1174,4x |
| 5187 | Pregunta: &COMO SE TRAMITAN LAS EXCEPCIONES? | Procesal | 95124 | 89 | 99,9 % | 1068,8x |
| 5188 | Pregunta: &COMO SE TRAMITAN LOS INCIDENTES QUE SE SUSCITANDURANTEELPROBATORIO? | Procesal | 95124 | 104 | 99,9 % | 914,7x |
| 5189 | Pregunta: &CUAL ES LA REGLA GENERAL EN EL PROCESO CIVIL? | Procesal | 95124 | 132 | 99,9 % | 720,6x |
| 5190 | Pregunta: &CUALES SON LOS REQUISITOS GENERALES PARA SOLICITARUNAMEDIDAPREJUDICIAL? | Procesal | 95124 | 62 | 99,9 % | 1534,3x |
| 5191 | Pregunta: &CUANDO DEBE HACERSE ACTA DEL REMATE? | Procesal | 95124 | 118 | 99,9 % | 806,1x |
| 5192 | Pregunta: &CUANDO PUEDE SER NULO EL REMATE POR VICIOS | Procesal | 95124 | 52 | 99,9 % | 1829,3x |
| 5193 | Pregunta: &CUANDO SE PRESENTA LA LISTA DE TESTIGOS? | Procesal | 95124 | 91 | 99,9 % | 1045,3x |
| 5194 | Pregunta: &CUANDO SE RESUELVE LA SOLICITUD DE RESERVA? | Procesal | 95124 | 133 | 99,9 % | 715,2x |
| 5195 | Pregunta: &EN QUE OPORTUNIDAD PUEDE EL EJECUTADO RESERVARSUS EXCEPCIONES? | Procesal | 95124 | 67 | 99,9 % | 1419,8x |
| 5196 | Pregunta: &PUEDE EL VENCIDO OPONERSE A ESTA EJECUCION O | Procesal | 95124 | 52 | 99,9 % | 1829,3x |
| 5197 | Pregunta: &PUEDE UN LITIGANTE REBELDE PEDIR LA NULIDAD | Procesal | 95124 | 53 | 99,9 % | 1794,8x |
| 5198 | Pregunta: &PUEDE UNA MISMA COSA SER EMBARGADA MAS DE | Procesal | 95124 | 57 | 99,9 % | 1668,8x |
| 5199 | Pregunta: &QUE ACTITUDES PUEDE ASUMIR EL TRIBUNAL ANTE | Procesal | 95124 | 66 | 99,9 % | 1441,3x |
| 5200 | Pregunta: &QUE ACTOS DE DISPOSICION PUEDE REALIZAR POR | Procesal | 95124 | 54 | 99,9 % | 1761,6x |
| 5201 | Pregunta: &QUE CONDICIONES DEBEN REUNIR LOS TESTIGOS? | Procesal | 95124 | 87 | 99,9 % | 1093,4x |
| 5202 | Pregunta: &QUE COSAS NO SE ENTREGAN AL DEPOSITARIO NI | Procesal | 95124 | 78 | 99,9 % | 1219,5x |
| 5203 | Pregunta: &QUE DEBE CONTENER LA SENTENCIA DEFINITIVA DEL | Procesal | 95124 | 55 | 99,9 % | 1729,5x |
| 5204 | Pregunta: &QUE ES EL JUICIO EJECUTIVO DE OBLIGACIONES DE | Procesal | 95124 | 61 | 99,9 % | 1559,4x |
| 5205 | Pregunta: &QUE ES LA DESERCION DE LA APELACION? | Procesal | 95124 | 92 | 99,9 % | 1034,0x |
| 5206 | Pregunta: &QUE ES LA PRUEBA INSTRUMENTAL O DOCUMENTAL? | Procesal | 95124 | 92 | 99,9 % | 1034,0x |
| 5207 | Pregunta: &QUE OBLIGACION TIENEN LAS PARTES EN UN JUICIO | Procesal | 95124 | 81 | 99,9 % | 1174,4x |
| 5208 | Pregunta: &QUE OTROS DERECHOS PUEDE HACER VALER UN TERCEROEN UN JUICIO EJECUTIVO? | Procesal | 95124 | 87 | 99,9 % | 1093,4x |
| 5209 | Pregunta: &QUE PASA SI EL DEUDOR COMPARECE Y RECONOCE | Procesal | 95124 | 53 | 99,9 % | 1794,8x |
| 5210 | Pregunta: &QUE PASA SI EL EJECUTANTE CONCURRE Y REMATA? | Procesal | 95124 | 53 | 99,9 % | 1794,8x |
| 5211 | Pregunta: &QUE PLAZO TIENE EL DEMANDADO PARA DUPLICAR? | Procesal | 95124 | 65 | 99,9 % | 1463,4x |
| 5212 | Pregunta: &QUE PUEDE HACER EL DEMANDANTE EN LA REPLICA? | Procesal | 95124 | 71 | 99,9 % | 1339,8x |
| 5213 | Pregunta: &QUE RECURSOS PROCEDEN EN CONTRA DE ESTA REPregunta: &QUIEN SENALA LOS PUNTOS DE PRUEBA? | Procesal | 95124 | 59 | 99,9 % | 1612,3x |
| 5214 | Pregunta: &QUE REQUISITOS DEBE CUMPLIR EL EJECUTANTE | Procesal | 95124 | 83 | 99,9 % | 1146,1x |
| 5215 | Pregunta: &QUE SON LAS GESTIONES PREPARATORIAS DE LA ViA | Procesal | 95124 | 49 | 99,9 % | 1941,3x |
| 5216 | Pregunta: &QUE SON LOS EQUIVALENTES JURISDICCIONALES? | Procesal | 95124 | 58 | 99,9 % | 1640,1x |
| 5217 | Pregunta: &QUE TRIBUNALES INTERVIENEN EN EL RECURSO DE | Procesal | 95124 | 48 | 99,9 % | 1981,8x |
| 5218 | Pregunta: &QUE VALOR PROBATORIO TIENE UN TESTIGO IMPARPregunta: Y SI LAS DECLARACIONES DE LOS TESTIGOS DE UNA | Procesal | 95124 | 57 | 99,9 % | 1668,8x |
| 5219 | Pregunta: &SE ENTIENDEN CONCEDIDAS ESTAS FACULTADES | Procesal | 95124 | 100 | 99,9 % | 951,2x |
| 5220 | Pregunta: 2COMO SE NOTIFICA LA DEMANDA EJECUTIVA? &QUE | Procesal | 95124 | 63 | 99,9 % | 1509,9x |
| 5221 | Pregunta: 2COMO SE TRAMITAN LOS JUICIOS ANTE ARBITROS | Procesal | 95124 | 53 | 99,9 % | 1794,8x |
| 5222 | Pregunta: 2COMO SE TRAMITAN? A QUE PROCEDIMIENTO SE | Procesal | 95124 | 57 | 99,9 % | 1668,8x |
| 5223 | Pregunta: 2CONTRA QUE RESOLUCIONES PROCEDE? | Procesal | 95124 | 131 | 99,9 % | 726,1x |
| 5224 | Pregunta: 2CUAL ES EL TRIBUNAL COMPETENTE PARA CONOCER | Procesal | 95124 | 48 | 99,9 % | 1981,8x |
| 5225 | Pregunta: 2CUALES SON LOS REQUISrTOS PARA QUE PROCEDA LA | Procesal | 95124 | 132 | 99,9 % | 720,6x |
| 5226 | Pregunta: 2CUANDO SE ENTIENDE QUE HAY NOTIFICACION TACITA? | Procesal | 95124 | 130 | 99,9 % | 731,7x |
| 5227 | Pregunta: 2QUE EXCEPCIONES PUEDE RESERVAR EL EJECUTAPregunta:QUE ESLAINEMBARGABILIDAD? | Procesal | 95124 | 100 | 99,9 % | 951,2x |
| 5228 | Pregunta: 2QUE PASA SI FALLA ALGUNA QUE NO SE HIZO VALER | Procesal | 95124 | 58 | 99,9 % | 1640,1x |
| 5229 | Pregunta: 2QUE RECURSO PROCEDE RESPECTO DE LA SENTENPARTESHAGAN OBSERVACIONESALAPRUEBA? | Procesal | 95124 | 58 | 99,9 % | 1640,1x |
| 5230 | Pregunta: 2QUE SON LOS ACTOS JUDICIALES NO CONTENCIOSOS? | Procesal | 95124 | 79 | 99,9 % | 1204,1x |
| 5231 | Pregunta: 2Y QUE PUEDE HACER EN ESTE CASO EL TRIBUNAL | Procesal | 95124 | 84 | 99,9 % | 1132,4x |
| 5232 | Pregunta: A QUE PRINCIPIO HACE EXCEPCION ESTE MEDIO DE | Procesal | 95124 | 62 | 99,9 % | 1534,3x |
| 5233 | Pregunta: ACTITUDES QUE PUEDE ASUMIR EL DEMANDADO UNA | Procesal | 95124 | 118 | 99,9 % | 806,1x |
| 5234 | Pregunta: ANTE QUE TRIBUNAL SE PROPONE LA DECLINATORIA? | Procesal | 95124 | 96 | 99,9 % | 990,9x |
| 5235 | Pregunta: CAPACIDAD PARA SER PARTE, O cQUIENES PUEDEN | Procesal | 95124 | 53 | 99,9 % | 1794,8x |
| 5236 | Pregunta: COMO COMIENZA LA SEGUNDA INSTANCIA? | Procesal | 95124 | 107 | 99,9 % | 889,0x |
| 5237 | Pregunta: COMO CONOCEN LAS CORTES DE APELACIONES? | Procesal | 95124 | 87 | 99,9 % | 1093,4x |
| 5238 | Pregunta: COMO INTERVIENEN DE MANERA VOLUNTARIA? | Procesal | 95124 | 119 | 99,9 % | 799,4x |
| 5239 | Pregunta: COMO PROCEDE LA INSPECCION PERSONAL DEL TRIBUNAL?HAY CASOSENQUEESOBLIGATORIA? | Procesal | 95124 | 123 | 99,9 % | 773,4x |
| 5240 | Pregunta: COMO PUEDE CONCEDERSE LA APELACION? | Procesal | 95124 | 91 | 99,9 % | 1045,3x |
| 5241 | Pregunta: COMO PUEDE SER NULO EL REMATE POR VICIOS SUSTANTIVOS? | Procesal | 95124 | 91 | 99,9 % | 1045,3x |
| 5242 | Pregunta: COMO PUEDE SER REMOVIDO DE SUS FUNCIONES UN | Procesal | 95124 | 93 | 99,9 % | 1022,8x |
| 5243 | Pregunta: COMO PUEDEN SER LAS SENTENCIAS DEFINITIVAS DE | Procesal | 95124 | 63 | 99,9 % | 1509,9x |
| 5244 | Pregunta: COMO RESUELVE EL JUEZ ESTA REPOSICION? | Procesal | 95124 | 107 | 99,9 % | 889,0x |
| 5245 | Pregunta: COMO SE CONCEDEN LAS MEDIDAS PREJUDICIALES? | Procesal | 95124 | 119 | 99,9 % | 799,4x |
| 5246 | Pregunta: COMO SE HACEN VALER ESTAS INHABILIDADES Y | Procesal | 95124 | 54 | 99,9 % | 1761,6x |
| 5247 | Pregunta: COMO SE NOTIFICA ESTA RESOLUCION? | Procesal | 95124 | 75 | 99,9 % | 1268,3x |
| 5248 | Pregunta: COMO SE NOTIFICA LA RESOLUCION QUE DECLARA | Procesal | 95124 | 55 | 99,9 % | 1729,5x |
| 5249 | Pregunta: COMO SE PROVEE EL ESCRITO DE LA REPLICA? | Procesal | 95124 | 61 | 99,9 % | 1559,4x |
| 5250 | Pregunta: COMO SE PROVEE LA SOLICITUD DE CUMPLIMIENTO | Procesal | 95124 | 55 | 99,9 % | 1729,5x |
| 5251 | Pregunta: COMO Y CUANDO DEBE RECLAMARSE DE LOS VICIOS | Procesal | 95124 | 98 | 99,9 % | 970,7x |
| 5252 | Pregunta: CONCEPTO ACCION DE INCONSTITUCIONALIDAD | Procesal | 95124 | 132 | 99,9 % | 720,6x |
| 5253 | Pregunta: CONCEPTO DE RECURSO DE PROTECCION | Procesal | 95124 | 66 | 99,9 % | 1441,3x |
| 5254 | Pregunta: CONOCE ALGUN CASO EN QUE SEA INADMISIBLE LA | Procesal | 95124 | 61 | 99,9 % | 1559,4x |
| 5255 | Pregunta: CUAL ES EL TRIBUNAL COMPETENTE PARA CONOCER | Procesal | 95124 | 62 | 99,9 % | 1534,3x |
| 5256 | Pregunta: CUAL ES LA CLASIFICACION QUE DA EL C.P.C.EN EL | Procesal | 95124 | 49 | 99,9 % | 1941,3x |
| 5257 | Pregunta: CUAL ES LA LIMITACION DE SU INTERPOSICION? | Procesal | 95124 | 88 | 99,9 % | 1081,0x |
| 5258 | Pregunta: CUALES SON LAS GESTIONES PREPARATORIAS DE LA | Procesal | 95124 | 70 | 99,9 % | 1358,9x |
| 5259 | Pregunta: CUALES SON LAS MEDIDAS PRECAUTORIAS ENUMEPregunta: COMO SE DECRETAN LAS MEDIDAS PRECAUTORIAS? | Procesal | 95124 | 50 | 99,9 % | 1902,5x |
| 5260 | Pregunta: CUALES SON LAS MEDIDAS PREJUDICIALES PROBAC) | Procesal | 95124 | 57 | 99,9 % | 1668,8x |
| 5261 | Pregunta: CUALES SON LOS OBJETIVOS DE ESTE RECURSO? | Procesal | 95124 | 141 | 99,9 % | 674,6x |
| 5262 | Pregunta: CUANDO POR EXCEPCION SE PUEDE COMPARECER | Procesal | 95124 | 49 | 99,9 % | 1941,3x |
| 5263 | Pregunta: DE ACUERDO A QUE PROCEDIMIENTO SE TRAMITA EL | Procesal | 95124 | 83 | 99,9 % | 1146,1x |
| 5264 | Pregunta: DE CUANTOS DfAS CONSTA EL PROBATORIO EN EL | Procesal | 95124 | 48 | 99,9 % | 1981,8x |
| 5265 | Pregunta: DE UNA BREVE EXPLICACION SOBRE LO QUE ES CADA | Procesal | 95124 | 136 | 99,9 % | 699,4x |
| 5266 | Pregunta: DESDE CUANDO SE CUENTAN LOS SEIS MESES? | Procesal | 95124 | 124 | 99,9 % | 767,1x |
| 5267 | Pregunta: DIFERENCIAS ENTRE CLAUSULA COMPROMISORIA Y | Procesal | 95124 | 98 | 99,9 % | 970,7x |
| 5268 | Pregunta: EFECTOS DE LA ACUMULACION DE AUTOS.gDESDE | Procesal | 95124 | 59 | 99,9 % | 1612,3x |
| 5269 | Pregunta: EFECTOS DE LA NO CITACION DE LOS ACREEDORES | Procesal | 95124 | 55 | 99,9 % | 1729,5x |
| 5270 | Pregunta: EJEMPLOS DE EXCEPCIONES EN QUE LOS TRIBUNALES | Procesal | 95124 | 119 | 99,9 % | 799,4x |
| 5271 | Pregunta: EN QUE CASO SE OMITE DICTAR SENTENCIA EN EL | Procesal | 95124 | 58 | 99,9 % | 1640,1x |
| 5272 | Pregunta: EN QUE CONSISTE LA NOTIFICACION PERSONAL? | Procesal | 95124 | 67 | 99,9 % | 1419,8x |
| 5273 | Pregunta: EN QUE OTROS PROCEDIMIENTOS SE APLICA ESTA | Procesal | 95124 | 101 | 99,9 % | 941,8x |
| 5274 | Pregunta: EN QUE SE DIFERENCIAN LAS EXCEPCIONES DE LAS | Procesal | 95124 | 55 | 99,9 % | 1729,5x |
| 5275 | Pregunta: EQUE ES LA AGENCIA OrICIOSA JUDICIAL O FIANZA DE | Procesal | 95124 | 123 | 99,9 % | 773,4x |
| 5276 | Pregunta: ES APELABLE LA RESOLUCION QUE RESUELVE SOBRE | Procesal | 95124 | 53 | 99,9 % | 1794,8x |
| 5277 | Pregunta: EXCEPCIONES AL DESASIMIENTO. RESOLUCIONES QUE | Procesal | 95124 | 137 | 99,9 % | 694,3x |
| 5278 | Pregunta: EXCEPCIONES AL PRINCIPIO SEGUN EL CUAL EL FALLO | Procesal | 95124 | 59 | 99,9 % | 1612,3x |
| 5279 | Pregunta: JCOMO PUEDE FALLAR UN JUEZ UNA CAUSA SI NO HAY | Procesal | 95124 | 62 | 99,9 % | 1534,3x |
| 5280 | Pregunta: JES DEFINITIVA LA AVALUACION QUE HACE EL PERITO? | Procesal | 95124 | 61 | 99,9 % | 1559,4x |
| 5281 | Pregunta: OPORTUNIDAD PARA EJERCER LA ACCION DE IWAPLI- | Procesal | 95124 | 68 | 99,9 % | 1398,9x |
| 5282 | Pregunta: QUE DEBE CONTENER LA RESOLUCION QUE RECIBE | Procesal | 95124 | 61 | 99,9 % | 1559,4x |
| 5283 | Pregunta: QUE DEBE RESOLVER EL JUEZ ANTE LA RESERVA DE | Procesal | 95124 | 54 | 99,9 % | 1761,6x |
| 5284 | Pregunta: QUE DERECHOS TIENE EL ACREEDOR SOBRE LOS | Procesal | 95124 | 62 | 99,9 % | 1534,3x |
| 5285 | Pregunta: QUE ES EL CONTRATO DE COMPROMISARIO? | Procesal | 95124 | 96 | 99,9 % | 990,9x |
| 5286 | Pregunta: QUE ES EL TERMINO PROBATORIO EXTRAORDINARIO? | Procesal | 95124 | 70 | 99,9 % | 1358,9x |
| 5287 | Pregunta: QUE ES LA CONSULTA? O gEN QUE CASOS LA SENTENCIA QUE NO ES REVISADA POR EL SUPERIOR POR | Procesal | 95124 | 70 | 99,9 % | 1358,9x |
| 5288 | Pregunta: QUE ES LA PRORROGA DE COMPETENCIA? | Procesal | 95124 | 106 | 99,9 % | 897,4x |
| 5289 | Pregunta: QUE FUNCION RELACIONADA CON ESTE PRINCIPIO | Procesal | 95124 | 53 | 99,9 % | 1794,8x |
| 5290 | Pregunta: QUE HACE EL JUEZ UNA VEZ TERMINADO EL PERiODO | Procesal | 95124 | 67 | 99,9 % | 1419,8x |
| 5291 | Pregunta: QUE PERSONAS PUEDEN SENALAR BIENES PARA EL | Procesal | 95124 | 68 | 99,9 % | 1398,9x |
| 5292 | Pregunta: QUE PUEDE HACER EL DEMANDADO SI SE ACCEDE | Procesal | 95124 | 50 | 99,9 % | 1902,5x |
| 5293 | Pregunta: QUE REGLAS SE APLICAN PARA EL CUMPLIMIENTO DE | Procesal | 95124 | 96 | 99,9 % | 990,9x |
| 5294 | Pregunta: QUE REQUISITOS DEBE CUMPLIR EL EJECUTADO | Procesal | 95124 | 52 | 99,9 % | 1829,3x |
| 5295 | Pregunta: QUE REQUISITOS DEBE CUMPLIR LA SENTENCIA EJEPregunta: CUANDO ES CONDENATORIA? | Procesal | 95124 | 52 | 99,9 % | 1829,3x |
| 5296 | Pregunta: QUE SE ENTREGA?A QUIEN SE PUEDE ENTREGAR? | Procesal | 95124 | 68 | 99,9 % | 1398,9x |
| 5297 | Pregunta: QUE SIGNIFICA QUE LA CONFESION SEA DIVISIBLE? | Procesal | 95124 | 102 | 99,9 % | 932,6x |
| 5298 | Pregunta: QUE SUCEDE SI SOBRE EL BIEN EMBARGADO EXISTEN HIPOTECAS A FAVOR DE OTRAS PERSONAS QUE | Procesal | 95124 | 61 | 99,9 % | 1559,4x |
| 5299 | Pregunta: QUIEN ES EL SUJETO DE LA CONFESION? | Procesal | 95124 | 137 | 99,9 % | 694,3x |
| 5300 | Pregunta: QUIEN REALIZA LA CONFRONTACION DE LOS TITULOS | Procesal | 95124 | 81 | 99,9 % | 1174,4x |
| 5301 | Pregunta: REGLAS DE DISTRIBUCION DE CAUSAS EN ASUNTOS NO | Procesal | 95124 | 115 | 99,9 % | 827,2x |
| 5302 | Pregunta: RESPECTO DE QUE HONORARIOS PROCEDE EL JUICIO | Procesal | 95124 | 61 | 99,9 % | 1559,4x |
| 5303 | Pregunta: SE PUEDE RECONVENIR EN EL JUICIO SUMARIO? | Procesal | 95124 | 137 | 99,9 % | 694,3x |
| 5304 | Pregunta: cQUE DERECHO TIENE EL AFECTADO POR LA JACTANPregunta: COMPARECENCIA EN JUICIO. COMO SE COMPARECE | Procesal | 95124 | 53 | 99,9 % | 1794,8x |
| 5305 | Pregunta: gCOMO RESUELVE ESTE RECURSO EL TRIBUNAL? | Procesal | 95124 | 93 | 99,9 % | 1022,8x |
| 5306 | Pregunta: gDESDE CUANDO COMIENZA A CORRER EL TERMINO | Procesal | 95124 | 62 | 99,9 % | 1534,3x |
| 5307 | Pregunta: gHAY ALGUNA SANCION SI UNA PARTE NO PRESENTA | Procesal | 95124 | 67 | 99,9 % | 1419,8x |
| 5308 | Pregunta:&COMO SE CONCEDE O DECRETA (EN CASO QUE SEA | Procesal | 95124 | 88 | 99,9 % | 1081,0x |
| 5309 | Pregunta:&CUANDO EXISTE RECURSO DE HECHO VERDADERO? | Procesal | 95124 | 114 | 99,9 % | 834,4x |
| 5310 | Pregunta:&HAY ALGUNA RESOLUCION QUE PUEDA CUMPLIRSE | Procesal | 95124 | 54 | 99,9 % | 1761,6x |
| 5311 | Pregunta:&PUEDE HABER OTROS TERMINOS ESPECIALES DE | Procesal | 95124 | 48 | 99,9 % | 1981,8x |
| 5312 | Pregunta:&QUE RECURSOS PROCEDEN EN CONTRA DEL MANDAa | Procesal | 95124 | 52 | 99,9 % | 1829,3x |
| 5313 | Pregunta:&SUSPENDE LA SOLICITUD DE REPOSICION EL PLAZO | Procesal | 95124 | 52 | 99,9 % | 1829,3x |
| 5314 | Pregunta:CAPACIDADDE LASPARTESPARA NOMBRARALARBIPregunta: QUE ES LA CLAUSULA COMPROMISORIA? | Procesal | 95124 | 111 | 99,9 % | 857,0x |
| 5315 | Pregunta:COMO PUEDENINTERVENIR LOS TERCEROS? | Procesal | 95124 | 126 | 99,9 % | 755,0x |
| 5316 | Pregunta:COMO SE EJECUTA LA SENTENCIA CONDENATORIA | Procesal | 95124 | 48 | 99,9 % | 1981,8x |
| 5317 | Pregunta:CUAL ES LA NATURALEZA JURIDICA DE LA RESOLUCION QUE DA POR RECONOCIDA LA FIRMA? | Procesal | 95124 | 100 | 99,9 % | 951,2x |
| 5318 | Pregunta:CUALES SON LOS EFECTOS DE LA PRORROGA DE | Procesal | 95124 | 74 | 99,9 % | 1285,5x |
| 5319 | Pregunta:CUANDO DEBE REALIZARSE LA AUDIENCIA? | Procesal | 95124 | 109 | 99,9 % | 872,7x |
| 5320 | Pregunta:DEBE TENER LA RECONVENCION ALGUNA RELACION | Procesal | 95124 | 55 | 99,9 % | 1729,5x |
| 5321 | Pregunta:EFECTOS DE LA LEY PROCESAL EN CUANTO AL TIEMPO.COMO AFECTAN A LOS PROCESOS LAS LEYES QUE | Procesal | 95124 | 110 | 99,9 % | 864,8x |
| 5322 | Pregunta:EFECTOS DE LAS SENTENCIAS CRIMINALES EN JUICIOS | Procesal | 95124 | 67 | 99,9 % | 1419,8x |
| 5323 | Pregunta:EN QUE CASOS EL JUEZ CITA A OfR SENTENCIA UNA | Procesal | 95124 | 85 | 99,9 % | 1119,1x |
| 5324 | Pregunta:EN QUE CONSISTIRAN LOS TITULOS EN ESTOS CASOS | Procesal | 95124 | 61 | 99,9 % | 1559,4x |
| 5325 | Pregunta:ES EXCEPCION AL PRINCIPIO DE TERRITORIALIDAD | Procesal | 95124 | 55 | 99,9 % | 1729,5x |
| 5326 | Pregunta:EXCEPCIONES EN QUE LA LEY FACULTA AL TRI-BUNAL | Procesal | 95124 | 131 | 99,9 % | 726,1x |
| 5327 | Pregunta:HASTA CUANDO PUEDE HACERSE VALER? | Procesal | 95124 | 107 | 99,9 % | 889,0x |
| 5328 | Pregunta:INCURRE EN DELITO EL TRIBUNAL QUE SE NIEGA A | Procesal | 95124 | 58 | 99,9 % | 1640,1x |
| 5329 | Pregunta:MENCIONE ALGUNAS EXCEPCIONES A ESTOS EFECPregunta:HAY ALGUNA SANCION PARA LA PARTE QUE NO HAGA | Procesal | 95124 | 58 | 99,9 % | 1640,1x |
| 5330 | Pregunta:NATURALEZA JURIDICA DE LA RESOLUCION QUE CITA | Procesal | 95124 | 62 | 99,9 % | 1534,3x |
| 5331 | Pregunta:PROCEDEN AUMENTOS EXTRAORDINARIOS PARA | Procesal | 95124 | 62 | 99,9 % | 1534,3x |
| 5332 | Pregunta:PUEDE AMPLIARSEESTE PLAZO SIELDEMANDADO SE | Procesal | 95124 | 123 | 99,9 % | 773,4x |
| 5333 | Pregunta:PUEDE FALLAR ESTAS ACCIONES SIN NECESIDAD DE | Procesal | 95124 | 55 | 99,9 % | 1729,5x |
| 5334 | Pregunta:QUE ES LA JACTANCIA?CUANDO HAY JACTANCIA? | Procesal | 95124 | 110 | 99,9 % | 864,8x |
| 5335 | Pregunta:QUE GARANTIZA ELRECURSO DE AMPARO? | Procesal | 95124 | 109 | 99,9 % | 872,7x |
| 5336 | Pregunta:QUE OTRO PROCEDIMIENTO TIENE EL TERCERISTA | Procesal | 95124 | 58 | 99,9 % | 1640,1x |
| 5337 | Pregunta:QUE PASA SI LA FINCA ESTA GRAVADA CON OTRAS | Procesal | 95124 | 52 | 99,9 % | 1829,3x |
| 5338 | Pregunta:QUE REQUISITOS DEBEN CUMPLIRSE PARA ACCEDER | Procesal | 95124 | 53 | 99,9 % | 1794,8x |
| 5339 | Pregunta:QUE SON LOS INTERDICTOS POSESORIOS? | Procesal | 95124 | 117 | 99,9 % | 813,0x |
| 5340 | Pregunta:QUE SUCEDE UNA VEZ QUE HA VENCIDO EL TERMINO | Procesal | 95124 | 49 | 99,9 % | 1941,3x |
| 5341 | Pregunta:QUEPLAZOTIENEELDEMANDADORECONVENCIONAL | Procesal | 95124 | 66 | 99,9 % | 1441,3x |
| 5342 | Pregunta:QUEVALOR TIENE ESTA ACTA DE REMATE? | Procesal | 95124 | 104 | 99,9 % | 914,7x |
| 5343 | Pregunta:REQUISITOSPARA QUE PROCEDALAACUMULACION DE | Procesal | 95124 | 87 | 99,9 % | 1093,4x |
| 5344 | Pregunta:RESOLUCIONES RESPECTO DE LAS CUALES PROCEDE | Procesal | 95124 | 127 | 99,9 % | 749,0x |
| 5345 | Pregunta:UNA VEZ CORREGIDA LA DEMANDA O SI SE DESECHAN | Procesal | 95124 | 58 | 99,9 % | 1640,1x |
| 5346 | Preguuta: QUE SON LAS MEDIDAS PARA MEJOR RESOLVER? | Procesal | 95124 | 85 | 99,9 % | 1119,1x |
| 5347 | Prevalecer aquella que ampara a quien también tiene un mejor derecho, sea por su | Civil | 171433 | 89 | 99,9 % | 1926,2x |
| 5348 | Prevalencia a lo largo de la vida | Constitucional | 177323 | 114 | 99,9 % | 1555,5x |
| 5349 | Prevalencia en los 12 meses precedentes | Constitucional | 177323 | 153 | 99,9 % | 1159,0x |
| 5350 | Progunta: CONCEPTO DE LA ACCION DE INAPLICABILIDAD POR | Procesal | 95124 | 65 | 99,9 % | 1463,4x |
| 5351 | Progunta:CQUIEN ES LA PARTE LEGITIMADA PARA EJERCER | Procesal | 95124 | 63 | 99,9 % | 1509,9x |
| 5352 | Promesa de compraventa25 | Civil | 29257 | 32 | 99,9 % | 914,3x |
| 5353 | Protección de las | Constitucional | 115835 | 133 | 99,9 % | 870,9x |
| 5354 | Proveído por el señor presidente del tribunal cons- | Judicial | 30834 | 42 | 99,9 % | 734,1x |
| 5355 | Prueba ofrecida por los cónyuges | Judicial | 79146 | 44 | 99,9 % | 1798,8x |
| 5356 | Quiénes? reflexiones sobre algunas cuestiones em- | Constitucional | 177323 | 156 | 99,9 % | 1136,7x |
| 5357 | R.u.n.: 33.333.333-3 | Judicial | 79146 | 50 | 99,9 % | 1582,9x |
| 5358 | Reclamación contra | Constitucional | 115835 | 139 | 99,9 % | 833,3x |
| 5359 | Regimenes matrimoniales1 | Familia | 136567 | 136 | 99,9 % | 1004,2x |
| 5360 | Registrese y notifiquese | Civil | 192585 | 100 | 99,9 % | 1925,8x |
| 5361 | Requisitos de existencia y de validez de los actos juridicos. 1.- | General | 166275 | 191 | 99,9 % | 870,5x |
| 5362 | Rit 0 - 2021 | Penal | 57066 | 70 | 99,9 % | 815,2x |
| 5363 | Rit 9.211-2012 | Penal | 178516 | 91 | 99,9 % | 1961,7x |
| 5364 | Rit: f-000-2020 | Familia | 100107 | 67 | 99,9 % | 1494,1x |
| 5365 | Ruc: 25-1-1627569-6 | Judicial | 79146 | 57 | 99,9 % | 1388,5x |
| 5366 | SITLA y SITCO | Laboral | 71986 | 83 | 99,9 % | 867,3x |
| 5367 | Sección Atención de Público | Judicial | 52128 | 63 | 99,9 % | 827,4x |
| 5368 | Sección Civil | Judicial | 52128 | 61 | 99,9 % | 854,6x |
| 5369 | Sección Laboral y Cobranza | Judicial | 52128 | 71 | 99,9 % | 734,2x |
| 5370 | Sección barra de estado | Penal | 57066 | 70 | 99,9 % | 815,2x |
| 5371 | Sección cerrar | Penal | 57066 | 68 | 99,9 % | 839,2x |
| 5372 | Sección de nombre de archivo | Penal | 57066 | 62 | 99,9 % | 920,4x |
| 5373 | Sección de opciones | Penal | 57066 | 84 | 99,9 % | 679,4x |
| 5374 | Sección mezclador | Penal | 57066 | 62 | 99,9 % | 920,4x |
| 5375 | Sección o Unidad de | Judicial | 52128 | 44 | 99,9 % | 1184,7x |
| 5376 | Sección primera: de la administración ordinaria de la sociedad | Familia | 136567 | 150 | 99,9 % | 910,4x |
| 5377 | Sección segunda: de la administración extraordinaria de la sociedad | Familia | 136567 | 157 | 99,9 % | 869,9x |
| 5378 | Sección única | Constitucional | 44292 | 45 | 99,9 % | 984,3x |
| 5379 | Sección: Complejidad, plazo de intervención y plazo de remisión informe | Constitucional | 44292 | 65 | 99,9 % | 681,4x |
| 5380 | Sección: Datos para nueva derivación | Constitucional | 44292 | 58 | 99,9 % | 763,7x |
| 5381 | Segunda parte: efectos de las obligaciones | Civil | 120848 | 162 | 99,9 % | 746,0x |
| 5382 | Serie de | Judicial | 54457 | 59 | 99,9 % | 923,0x |
| 5383 | Si quien vende es el marido en su calidad de administrador de los bienes | Civil | 153962 | 124 | 99,9 % | 1241,6x |
| 5384 | Sii: etapa judicial | Judicial | 62888 | 66 | 99,9 % | 952,8x |
| 5385 | Sirva la presente acta de suficiente y atento oficio remisor para | Judicial | 79146 | 55 | 99,9 % | 1439,0x |
| 5386 | Sumario — Apelación | Judicial | 54457 | 50 | 99,9 % | 1089,1x |
| 5387 | Sumario: 1.- Necesidad de regular la conducta humana. 1.1. Necesidad del Derecho | General | 129559 | 161 | 99,9 % | 804,7x |
| 5388 | TUTORES Y CURADORES Y DEL DISCERNIMIENTO DE ESTOS CARGOS”, conformado | Familia | 85324 | 117 | 99,9 % | 729,3x |
| 5389 | Teoria de la ley1 | General | 125500 | 130 | 99,9 % | 965,4x |
| 5390 | Teoria del acto juridico1 | General | 166275 | 127 | 99,9 % | 1309,3x |
| 5391 | Testamento más solemne | Civil | 50203 | 55 | 99,9 % | 912,8x |
| 5392 | Teóricos del | Procesal | 96699 | 87 | 99,9 % | 1111,5x |
| 5393 | Total                  9              4          1             1               1             16 | Laboral | 53374 | 65 | 99,9 % | 821,1x |
| 5394 | Título 1, “Del procedimiento Concursal de Renegociación de la Persona Deudora”. El artículo 263, se refiere a | Civil | 120848 | 98 | 99,9 % | 1233,1x |
| 5395 | Título I del Libro IV del Código Procesal Penal, las faltas e infracciones | Penal | 194788 | 141 | 99,9 % | 1381,5x |
| 5396 | Título I del Libro Tercero del Código de Procedimiento Civil y su conocimiento | Civil | 192585 | 100 | 99,9 % | 1925,8x |
| 5397 | Título I del Libro V del Código del Trabajo. El párrafo 5° contiene, entre | Procesal | 66012 | 85 | 99,9 % | 776,6x |
| 5398 | Título II de dicha ley, “De la planificación urbana”. El art. 66 alude a la formación de | Civil | 192585 | 174 | 99,9 % | 1106,8x |
| 5399 | Título III -Audiencias por Videoconferencia- dispone: “El | Judicial | 83934 | 102 | 99,9 % | 822,9x |
| 5400 | Título III y a un siete por ciento destinado a financiar prestaciones de salud, las que se | Familia | 136567 | 191 | 99,9 % | 715,0x |
| 5401 | Título Sexto) sobre trabajo y previsión social. En él todas sus normas | Laboral | 113458 | 123 | 99,9 % | 922,4x |
| 5402 | Título VII: de la apertura de la sucesión y de su aceptación, repudiación e inventario | Civil | 92843 | 93 | 99,9 % | 998,3x |
| 5403 | Título XIX: “DE LAS TUTELAS Y CURADURÍAS EN GENERAL”, arts. 338 a 372, con | Familia | 85324 | 115 | 99,9 % | 741,9x |
| 5404 | Título XXIII del Libro IV del Código Civil, es indispensable, en principio, que la | Civil | 153962 | 202 | 99,9 % | 762,2x |
| 5405 | Título XXXV del mismo Libro IV).94 | Civil | 120848 | 111 | 99,9 % | 1088,7x |
| 5406 | Título final | Penal | 194788 | 184 | 99,9 % | 1058,6x |
| 5407 | Título preliminar: Disposiciones generales | Penal | 194788 | 130 | 99,9 % | 1498,4x |
| 5408 | Título, después de definir la compraventa y referirse al precio (arts. 1793 y 1794), se | Civil | 153962 | 183 | 99,9 % | 841,3x |
| 5409 | Título, ¿qué preceptos regulan en realidad los efectos de los contratos y cuáles regulan | Civil | 120848 | 171 | 99,9 % | 706,7x |
| 5410 | Umansky (2000); dejong (1979) | Constitucional | 121906 | 70 | 99,9 % | 1741,5x |
| 5411 | V     .- ncapac dades y excusas para ejercer la guarda | Familia | 85324 | 89 | 99,9 % | 958,7x |
| 5412 | V .- caso del guardador aparente y del guardador of c oso | Familia | 85324 | 70 | 99,9 % | 1218,9x |
| 5413 | V.- adm n strac ón de los guardadores | Familia | 85324 | 91 | 99,9 % | 937,6x |
| 5414 | V.- la novación | Civil | 75968 | 55 | 99,9 % | 1381,2x |
| 5415 | V.- obligaciones del guardador y responsabilidades inherentes al | Familia | 85324 | 100 | 99,9 % | 853,2x |
| 5416 | Vi.      ofrecimiento de pruebas e incorporación de las mismas | Judicial | 79146 | 101 | 99,9 % | 783,6x |
| 5417 | Vi.-       la remisión | Civil | 75968 | 71 | 99,9 % | 1070,0x |
| 5418 | Vi.- suerte de los bienes reservados a la disolucion de la sociedad | Familia | 136567 | 83 | 99,9 % | 1645,4x |
| 5419 | Vii.- de las reglas comunes a ciertos casos de separacion, nulidad | Familia | 190697 | 100 | 99,9 % | 1907,0x |
| 5420 | Vii.- la compensación | Civil | 75968 | 49 | 99,9 % | 1550,4x |
| 5421 | Vii.- pactos lícitos y pactos prohibidos, en el régimen de participación | Familia | 136567 | 74 | 99,9 % | 1845,5x |
| 5422 | Viii.    sentencia | Judicial | 79146 | 70 | 99,9 % | 1130,7x |
| 5423 | Viii.- la confusión | Civil | 75968 | 61 | 99,9 % | 1245,4x |
| 5424 | Visto: […] | Civil | 171433 | 191 | 99,9 % | 897,6x |
| 5425 | WET (2006), p. 59; MURPHY (2006), p. 82; ORAKHELASHVILI (2006), p. 43; YARWOOD (2006), p. 32; COHEN | Penal | 121924 | 110 | 99,9 % | 1108,4x |
| 5426 | X+y=1370 | Familia | 65192 | 67 | 99,9 % | 973,0x |
| 5427 | Y parte intestada.1 | Civil | 50203 | 54 | 99,9 % | 929,7x |
| 5428 | Y teniendo en consideración: […] | Civil | 171433 | 200 | 99,9 % | 857,2x |
| 5429 | Y=y*100/z=%y | Familia | 65192 | 67 | 99,9 % | 973,0x |
| 5430 | ________. b) automoviles.- (datos que aparecen en el padrón del auto) | Familia | 136567 | 166 | 99,9 % | 822,7x |
| 5431 | ___________________________________________ y otros | Civil | 92843 | 74 | 99,9 % | 1254,6x |
| 5432 | a) SEGUN | Procesal | 95124 | 59 | 99,9 % | 1612,3x |
| 5433 | apéndice de este índice se inventarían los documentos agregados al final del Registro | General | 59520 | 65 | 99,9 % | 915,7x |
| 5434 | apéndice, y como posteriores a éstas, guardarse con preferencia cuando hubiese | Civil | 90056 | 91 | 99,9 % | 989,6x |
| 5435 | b) SEGUN EL | Procesal | 95124 | 72 | 99,9 % | 1321,2x |
| 5436 | capítulo 3 para detalles), es necesario aclarar qué se entiende por | Constitucional | 112823 | 67 | 99,9 % | 1683,9x |
| 5437 | capítulo III “De la administración del personal”, dispone en sus ar- | Procesal | 94881 | 106 | 99,9 % | 895,1x |
| 5438 | capítulo V del Proyecto se enumeran las circunstancias que excluyen | Penal | 121924 | 89 | 99,9 % | 1369,9x |
| 5439 | capítulo de este curso, a propósito del estudio de las características | Penal | 119528 | 92 | 99,9 % | 1299,2x |
| 5440 | capítulo de la ley consagra los requisitos, funciones y obligaciones de | Judicial | 64632 | 76 | 99,9 % | 850,4x |
| 5441 | capítulo sostiene que el Conservador careció de competencia legal, ya que de conformidad a los | Judicial | 79146 | 118 | 99,9 % | 670,7x |
| 5442 | capítulo, el Estado está obligado a investigar y sancionar a quien re- | Constitucional | 112823 | 102 | 99,9 % | 1106,1x |
| 5443 | d) SEGUN SU DEPENDENCIA | Procesal | 95124 | 91 | 99,9 % | 1045,3x |
| 5444 | d)SEGUN LA | Procesal | 95124 | 63 | 99,9 % | 1509,9x |
| 5445 | f SEGUN LA NATURALEZA | Procesal | 95124 | 52 | 99,9 % | 1829,3x |
| 5446 | p. 685; BROWNLIE (2008), p. 511; O’CONNELL (2008), p. 9; CRIDDLE y FOX-DECENT (2009), p. 331; DUBOIS | Penal | 121924 | 75 | 99,9 % | 1625,7x |
| 5447 | p. 68; CUMPLIDO (1996), p. 256; VAN BOVEN (1996), p. 298 Nº 23 y 24; BENVENISTI (1997), p. 603; BIANCHI | Penal | 121924 | 157 | 99,9 % | 776,6x |
| 5448 | parte (artículo 2493    Respecto a la notificación de la demanda y la resolución que cita a | Laboral | 71986 | 91 | 99,9 % | 791,1x |
| 5449 | parte a la interpretación que el Tribunal Constitucional ofreció en la | Judicial | 134465 | 87 | 99,9 % | 1545,6x |
| 5450 | parte acompañó a la causa el contrato de compraventa por el cual adquirieron de Sara Gaete | Civil | 171433 | 146 | 99,9 % | 1174,2x |
| 5451 | parte activa en la implementación | Judicial | 83934 | 44 | 99,9 % | 1907,6x |
| 5452 | parte acudió a lo dispuesto en el inciso segundo del artículo 713 (sic)13, en cuanto autoriza agregar | Civil | 171433 | 210 | 99,9 % | 816,3x |
| 5453 | parte agraviada con determinadas resoluciones judiciales, para obte- | Familia | 100107 | 91 | 99,9 % | 1100,1x |
| 5454 | parte agraviada destinado a obtener del Tribunal superior jerárquico | Familia | 100107 | 133 | 99,9 % | 752,7x |
| 5455 | parte antigua del foro que reza “Iovestad”, significando “lo justo”. ii) Otros autores | General | 129559 | 167 | 99,9 % | 775,8x |
| 5456 | parte asume el riesgo, la cuantía del resarcimiento se reducirá en la | Civil | 142015 | 79 | 99,9 % | 1797,7x |
| 5457 | parte beneficiada con ella no la hubiere alegado en juicio.420 | Penal | 121924 | 107 | 99,9 % | 1139,5x |
| 5458 | parte compradora, con todos sus usos, costumbres, derechos y servidumbres activas y | Civil | 153962 | 133 | 99,9 % | 1157,6x |
| 5459 | parte con capitales de la sociedad conyugal y en parte con capitales del cónyuge que | Familia | 136567 | 169 | 99,9 % | 808,1x |
| 5460 | parte contraria,dentro de los cuales ésta puede oponerse o | Procesal | 95124 | 93 | 99,9 % | 1022,8x |
| 5461 | parte contraria”.69 | Familia | 95131 | 49 | 99,9 % | 1941,4x |
| 5462 | parte criterios de actuación en delitos de tortura y otros tratos | Constitucional | 177323 | 148 | 99,9 % | 1198,1x |
| 5463 | parte de adultos mayores a cambio de bienes y favores, por lo que los | Judicial | 89476 | 110 | 99,9 % | 813,4x |
| 5464 | parte de ambos cónyuges”. Se trata de un matrimonio que tenía la apariencia de | Familia | 190697 | 187 | 99,9 % | 1019,8x |
| 5465 | parte de aquellos magistrados que ejercen funciones de revisión o | Judicial | 87237 | 85 | 99,9 % | 1026,3x |
| 5466 | parte de autoridades estatales o por particulares, pueden disminuiro | Judicial | 81476 | 71 | 99,9 % | 1147,5x |
| 5467 | parte de ellas están insertadas en el contexto de la protección social en la | Constitucional | 121906 | 107 | 99,9 % | 1139,3x |
| 5468 | parte de ellos, según el artículo 251”.248 | Familia | 85324 | 93 | 99,9 % | 917,5x |
| 5469 | parte de estas costumbres procedían del derecho germánico importado en la Galia por | Civil | 90056 | 61 | 99,9 % | 1476,3x |
| 5470 | parte de estos cuando sean causa directa de un impacto significativo y | Judicial | 60665 | 89 | 99,9 % | 681,6x |
| 5471 | parte de familiares y hombres mayores; en consecuencia, corren | Judicial | 87950 | 48 | 99,9 % | 1832,3x |
| 5472 | parte de la Administración pueden instar la revisión de los actos | Judicial | 105809 | 124 | 99,9 % | 853,3x |
| 5473 | parte de la Administración pública, centralizada o no, y que comprende | Penal | 178516 | 158 | 99,9 % | 1129,8x |
| 5474 | parte de la Corporación de la Reforma Agraria mediante el acuerdo 482 de fecha 10 de abril de | Civil | 171433 | 214 | 99,9 % | 801,1x |
| 5475 | parte de la actividad axiológica, porque ya la realizó la ley al tasar la | Penal | 211066 | 109 | 99,9 % | 1936,4x |
| 5476 | parte de la administración, toda vez que aquellos, como todo acto ad- | Judicial | 144656 | 195 | 99,9 % | 741,8x |
| 5477 | parte de la autoridad | Penal | 72395 | 72 | 99,9 % | 1005,5x |
| 5478 | parte de la cantidad retirada ni podrá computarse en la liquidación de la sociedad | Familia | 136567 | 162 | 99,9 % | 843,0x |
| 5479 | parte de la cultura normal de un determinado sector social al tiempo de | Judicial | 150341 | 169 | 99,9 % | 889,6x |
| 5480 | parte de la demandada, sin que además esta hubiera rendido prueba con el objeto de | Civil | 153962 | 132 | 99,9 % | 1166,4x |
| 5481 | parte de la deuda de gastos comunes que existía, por $5.022.519.-, quedando por tanto | Civil | 192585 | 205 | 99,9 % | 939,4x |
| 5482 | parte de la discusión, que se circunscribió únicamente a las materias | Judicial | 144656 | 205 | 99,9 % | 705,6x |
| 5483 | parte de la doctrina considera que el legislador objetiviza máximas de | Judicial | 150341 | 162 | 99,9 % | 928,0x |
| 5484 | parte de la documental agregada a los autos, esto es, el aviso de cobro de gastos | Civil | 192585 | 100 | 99,9 % | 1925,8x |
| 5485 | parte de la fuente emisora de ruido, generen emisiones sonoras en forma simultánea, los límites máximos | Civil | 192585 | 191 | 99,9 % | 1008,3x |
| 5486 | parte de la herencia o de la mitad legitimaria en su caso. Tras la reforma, todos los | Familia | 190697 | 197 | 99,9 % | 968,0x |
| 5487 | parte de la implementación del programa”.101 Se trata de una especie | Constitucional | 104063 | 101 | 99,9 % | 1030,3x |
| 5488 | parte de la jefatura, llevando así un control de la contabilidad | Penal | 57066 | 54 | 99,9 % | 1056,8x |
| 5489 | parte de la llamada teoría crítica, caracterizada por una posición | Judicial | 87237 | 89 | 99,9 % | 980,2x |
| 5490 | parte de la obligación de una empresa de proceder con | Constitucional | 112823 | 92 | 99,9 % | 1226,3x |
| 5491 | parte de la persona jurídica, con independencia de las dificultades | Penal | 119528 | 128 | 99,9 % | 933,8x |
| 5492 | parte de la realidad. Estas reflexiones llevaron al surgimiento de la | Judicial | 93914 | 96 | 99,9 % | 978,3x |
| 5493 | parte de la voluntad de un tercero o de un acaso. René Ramos Pazos indica que hay | Civil | 118177 | 169 | 99,9 % | 699,3x |
| 5494 | parte de las autoridades gubernamentales y/o entidades privadas en la pres- | Constitucional | 121906 | 110 | 99,9 % | 1108,2x |
| 5495 | parte de las empresas; y iii) mejorar las condiciones de asistencia técnica | Constitucional | 177323 | 98 | 99,9 % | 1809,4x |
| 5496 | parte de las investigaciones científico-académicas sobre sexualidad | Judicial | 87237 | 94 | 99,9 % | 928,1x |
| 5497 | parte de los bienes comunes, de manera que a su respecto los actores carecen de | Civil | 192585 | 206 | 99,9 % | 934,9x |
| 5498 | parte de los contratantes el cumplimiento recíproco y simultáneo del contrato en lo que | Civil | 120848 | 175 | 99,9 % | 690,6x |
| 5499 | parte de los contrayentes, ante un testigo cualificado, que generalmente | Familia | 123490 | 97 | 99,9 % | 1273,1x |
| 5500 | parte de los hechos de la demanda, específicamente, que ella ocupaba y estaba en posesión | Civil | 171433 | 226 | 99,9 % | 758,6x |
| 5501 | parte de los profesionales y la denuncia que | Familia | 95131 | 91 | 99,9 % | 1045,4x |
| 5502 | parte de los trabajadores públicos382. La esencia de este problema | Laboral | 113458 | 137 | 99,9 % | 828,2x |
| 5503 | parte de los tres mayores acreedores y la preparación del certificado | Judicial | 64632 | 76 | 99,9 % | 850,4x |
| 5504 | parte de los órganos de la Administración del Estado, y requerir a | Administrativo | 89720 | 124 | 99,9 % | 723,5x |
| 5505 | parte de nuestra identidad y privacidad, que debe respetarse por igual | Judicial | 89476 | 102 | 99,9 % | 877,2x |
| 5506 | parte de quien los tiene a su cargo en virtud de una específica función | Penal | 178516 | 100 | 99,9 % | 1785,2x |
| 5507 | parte de quienes recurren a los tribunales ni de otras autoridades o | Procesal | 101194 | 113 | 99,9 % | 895,5x |
| 5508 | parte de su política | Laboral | 71986 | 105 | 99,9 % | 685,6x |
| 5509 | parte de su tarea económica o que asuma parte de sus responsabilidades, para lo cual se | Civil | 110175 | 163 | 99,9 % | 675,9x |
| 5510 | parte de sus actividades laborales, indicó que la rama judicial | Constitucional | 112823 | 104 | 99,9 % | 1084,8x |
| 5511 | parte de sus bienes, prescindir de ellos u obtener otros para garantizar | Judicial | 64632 | 66 | 99,9 % | 979,3x |
| 5512 | parte de tales criterios y que ello, además, se avenía con los deseos ex- | Familia | 97488 | 84 | 99,9 % | 1160,6x |
| 5513 | parte de tribunales». Ello se reafirma por el texto expreso del artículo | Judicial | 144656 | 189 | 99,9 % | 765,4x |
| 5514 | parte de un agresor | Judicial | 53521 | 74 | 99,9 % | 723,3x |
| 5515 | parte de un comerciante. Empero, se aclaró que no resulta indispen- | Judicial | 64632 | 91 | 99,9 % | 710,2x |
| 5516 | parte de un consorcio liderado por Phillips Petroleum, la construcción del avión Concorde por Sud Aviation | Constitucional | 112823 | 68 | 99,9 % | 1659,2x |
| 5517 | parte de un cónyuge o una cónyuge con una persona ajena a la pareja | Familia | 123490 | 167 | 99,9 % | 739,5x |
| 5518 | parte de un integrante no se sigue que la persona jurídica responda | Penal | 119528 | 110 | 99,9 % | 1086,6x |
| 5519 | parte de un tercero, mientras que en el contrato por persona a nombrar se obliga a un hecho | Civil | 110175 | 115 | 99,9 % | 958,0x |
| 5520 | parte de una actualización regular del marco legal, que han tenido por | Penal | 178516 | 141 | 99,9 % | 1266,1x |
| 5521 | parte de una persona” como caminar, correr, escribir, ir al cine o | Constitucional | 121906 | 110 | 99,9 % | 1108,2x |
| 5522 | parte debidamente citada y con el único objeto de hacer procedente | Familia | 100107 | 110 | 99,9 % | 910,1x |
| 5523 | parte del Consejo Nacional de Televisión en | Administrativo | 89720 | 80 | 99,9 % | 1121,5x |
| 5524 | parte del Convenio no entran en detalles respecto a la forma de | Judicial | 134465 | 114 | 99,9 % | 1179,5x |
| 5525 | parte del Estado. No obstante, la Corte recuerda que no existe un mode- | Constitucional | 177323 | 169 | 99,9 % | 1049,2x |
| 5526 | parte del Fisco en su propio beneficio, a partir del año 1959. Concluye manifestando que la | Civil | 171433 | 226 | 99,9 % | 758,6x |
| 5527 | parte del activo de su patrimonio. Se tiene respecto de ella un derecho adquirido. Si se | General | 125500 | 94 | 99,9 % | 1335,1x |
| 5528 | parte del alcalde en la etapa administrativa, puede conformarse con ella o reclamar dentro | Judicial | 105809 | 89 | 99,9 % | 1188,9x |
| 5529 | parte del demandando, se le informó que lo estaba haciendo en un predio de propiedad de la | Civil | 171433 | 217 | 99,9 % | 790,0x |
| 5530 | parte del derecho internacional general. En la actual etapa de la | Judicial | 87237 | 84 | 99,9 % | 1038,5x |
| 5531 | parte del funcionario a cargo, siendo estas desarrolladas generalmen- | Laboral | 71986 | 54 | 99,9 % | 1333,1x |
| 5532 | parte del haber real o absoluto? | Familia | 136567 | 183 | 99,9 % | 746,3x |
| 5533 | parte del haber social una vez que adquieran tal calidad (es decir, una vez que las | Familia | 136567 | 200 | 99,9 % | 682,8x |
| 5534 | parte del haber social, pues los que ingresan pueden ser enajenados libremente por el | Familia | 136567 | 166 | 99,9 % | 822,7x |
| 5535 | parte del inmueble – cada unidad o departamento- y por otro, la propiedad de las áreas | Civil | 192585 | 178 | 99,9 % | 1081,9x |
| 5536 | parte del ius. Lo anterior significa que dicha distinción no consiste en una división de | General | 129559 | 175 | 99,9 % | 740,3x |
| 5537 | parte del lenguaje cotidiano para reivindicar posturas en tensión: las | Judicial | 89476 | 84 | 99,9 % | 1065,2x |
| 5538 | parte del marido autoriza a la mujer para pedir la separación judicial de | Familia | 123490 | 88 | 99,9 % | 1403,3x |
| 5539 | parte del mismo y en cualquier circunstancia, cumplir con los | Judicial | 93914 | 106 | 99,9 % | 886,0x |
| 5540 | parte del ordenamiento jurídico chileno. También, suelen aludir a | Penal | 121924 | 153 | 99,9 % | 796,9x |
| 5541 | parte del ordenamiento jurídico. No habría sido dejado sin efecto, a | Judicial | 105809 | 92 | 99,9 % | 1150,1x |
| 5542 | parte del patrimonio inmaterial que custodian y administran las | Judicial | 134465 | 87 | 99,9 % | 1545,6x |
| 5543 | parte del patrón respecto de sus trabajadores en diversas hipótesis | Laboral | 113458 | 61 | 99,9 % | 1860,0x |
| 5544 | parte del proceso de reinserción.6 | Penal | 194788 | 152 | 99,9 % | 1281,5x |
| 5545 | parte del proceso que posee una discapacidad no espera solamente | Constitucional | 121906 | 79 | 99,9 % | 1543,1x |
| 5546 | parte del proceso, no ingresó al mundo jurídico y no debe ser | Procesal | 94881 | 128 | 99,9 % | 741,3x |
| 5547 | parte del vendedor ni de su actividad profesional. 8°) Que no se mandará pagar | Civil | 153962 | 221 | 99,9 % | 696,7x |
| 5548 | parte demandada casación en el fondo, ésta fue declarada inadmisible por sentencia de | Civil | 153962 | 201 | 99,9 % | 766,0x |
| 5549 | parte demandada con relación al inmueble de la litis, como viene dicho en el fundamento décimo | Civil | 171433 | 218 | 99,9 % | 786,4x |
| 5550 | parte demandada o el        2. 	Rechazar oposición | Familia | 100107 | 93 | 99,9 % | 1076,4x |
| 5551 | parte demandante debe ser acogido, siendo inoficioso pronunciarse sobre las otras | Civil | 153962 | 208 | 99,9 % | 740,2x |
| 5552 | parte demandante y la sentencia dictada por la Ilustrísima Corte de Apelaciones de | Civil | 192585 | 196 | 99,9 % | 982,6x |
| 5553 | parte determinará el orden en que rendirá su prueba, correspondiendo recibir | Penal | 211066 | 139 | 99,9 % | 1518,5x |
| 5554 | parte dispositiva o cuando se hubiere incurrido en alguna de las otras | Procesal | 66012 | 62 | 99,9 % | 1064,7x |
| 5555 | parte dispositiva, sin perjuicio de añadir los fundamentos que den | Procesal | 66012 | 55 | 99,9 % | 1200,2x |
| 5556 | parte en dicha convención, por lo que la demanda en su contra no | Civil | 142015 | 94 | 99,9 % | 1510,8x |
| 5557 | parte en el proceso, al igual que la organización sindical de la cual | Laboral | 113458 | 91 | 99,9 % | 1246,8x |
| 5558 | parte en especies y éstas últimas valen más que el dinero, el contrato será de permuta | General | 166275 | 174 | 99,9 % | 955,6x |
| 5559 | parte en la Convención Marco de las Naciones Unidas sobre el | Constitucional | 177323 | 159 | 99,9 % | 1115,2x |
| 5560 | parte en los Convenios. También es posible transferir al culpable ante | Penal | 121924 | 66 | 99,9 % | 1847,3x |
| 5561 | parte especial que sancionan expresamente al extraneus (artículo 250 | Penal | 178516 | 107 | 99,9 % | 1668,4x |
| 5562 | parte evicta, o en el de no pedirse la rescisión de la venta, el comprador tendrá | Civil | 153962 | 81 | 99,9 % | 1900,8x |
| 5563 | parte final del inc. 1º del N° 5 del art. 1740. Quedan comprendidos en esta | Familia | 136567 | 124 | 99,9 % | 1101,3x |
| 5564 | parte formule, en qué plazo máximo debe concluir la negociación, sea que tenga un | Civil | 110175 | 100 | 99,9 % | 1101,8x |
| 5565 | parte importante de la labor de un juez o jueza, exige la evaluación | Procesal | 94881 | 94 | 99,9 % | 1009,4x |
| 5566 | parte integrante de la legislación del Estado”.332 Idéntico principio | Penal | 121924 | 91 | 99,9 % | 1339,8x |
| 5567 | parte integrante del Estado, estos se encuentran igualmente vinculados | Judicial | 144656 | 75 | 99,9 % | 1928,7x |
| 5568 | parte integrante del thema probandum. En tercer lugar, la confluencia de | Judicial | 150341 | 166 | 99,9 % | 905,7x |
| 5569 | parte interesada (por ejemplo, cuando la nulidad absoluta aparece de manifiesto en un | General | 129559 | 193 | 99,9 % | 671,3x |
| 5570 | parte interesada podrá siempre encargar a su costa la práctica de la | Laboral | 100583 | 94 | 99,9 % | 1070,0x |
| 5571 | parte interesada, argumentaron que no había disposición expresa para | Constitucional | 112823 | 94 | 99,9 % | 1200,2x |
| 5572 | parte la representación autoriza al representante para ejecutar actos lícitos a nombre | General | 166275 | 185 | 99,9 % | 898,8x |
| 5573 | parte le impone. Es preciso reconocer al contratante perseguido el derecho de poner | Civil | 120848 | 117 | 99,9 % | 1032,9x |
| 5574 | parte material de ella | Civil | 153962 | 183 | 99,9 % | 841,3x |
| 5575 | parte medular de la colección de los reyes españoles de la Casa de los | Judicial | 87237 | 130 | 99,9 % | 671,1x |
| 5576 | parte no era dueña de todas las unidades que se indican en la demanda, por lo que el | Civil | 192585 | 198 | 99,9 % | 972,7x |
| 5577 | parte nos detenemos para analizar el ejercicio de los derechos de los | Penal | 72395 | 100 | 99,9 % | 724,0x |
| 5578 | parte para comprender mejor, permite generar mejores alternativas | Judicial | 79146 | 44 | 99,9 % | 1798,8x |
| 5579 | parte para exclusión de prueba y, ante tal situación, se debe tener | Penal | 211066 | 159 | 99,9 % | 1327,5x |
| 5580 | parte porque los requisitos que se exigen no son fáciles de cumplir | Constitucional | 104063 | 122 | 99,9 % | 853,0x |
| 5581 | parte posterior derecha del vehículo patente xxxx, marca Cherry, color | Penal | 194788 | 156 | 99,9 % | 1248,6x |
| 5582 | parte pueda controvertir tanto los elementos fácticos que sustentan la | Judicial | 144656 | 124 | 99,9 % | 1166,6x |
| 5583 | parte puede influir en situaciones que se producen fuera de | Constitucional | 112823 | 101 | 99,9 % | 1117,1x |
| 5584 | parte puso total énfasis en la calidad de la malla de la propaganda, velando y | Civil | 192585 | 143 | 99,9 % | 1346,7x |
| 5585 | parte que corresponde al descubridor ingresará al haber relativo de la sociedad | Familia | 136567 | 150 | 99,9 % | 910,4x |
| 5586 | parte que falta es inferior a la décima parte de la cabida declarada, se rebajará el | Civil | 153962 | 187 | 99,9 % | 823,3x |
| 5587 | parte que había rechazado la demanda, y en su lugar la acogió, condenando | Civil | 192585 | 191 | 99,9 % | 1008,3x |
| 5588 | parte que los ha solicitado quedando facultado desde ya para requerir la respuesta a los mismos | Judicial | 79146 | 106 | 99,9 % | 746,7x |
| 5589 | parte que recupera el dominio en virtud de la declaración de nulidad: por ejemplo, el | Familia | 136567 | 189 | 99,9 % | 722,6x |
| 5590 | parte recurrente, por lo que solicita el rechazo del recurso de protección en todas sus | Civil | 192585 | 197 | 99,9 % | 977,6x |
| 5591 | parte resolutiva del fallo donde condenen y/o absuelvan a cada uno | Penal | 211066 | 145 | 99,9 % | 1455,6x |
| 5592 | parte responsables de la situación, ya que la violencia sería provocada | Familia | 95131 | 55 | 99,9 % | 1729,7x |
| 5593 | parte se encuentra en la situación de escoger entre proceder a esa | Penal | 121924 | 89 | 99,9 % | 1369,9x |
| 5594 | parte se obliga para con otra a dar, hacer o no hacer alguna cosa.20 | General | 166275 | 196 | 99,9 % | 848,3x |
| 5595 | parte son «adecuadas» o «razonables», dicho colegiado podrá tener en | Judicial | 81675 | 50 | 99,9 % | 1633,5x |
| 5596 | parte sus instituciones se han construido sobre una matriz sin mayores | Judicial | 87237 | 79 | 99,9 % | 1104,3x |
| 5597 | parte vencida, salvo que el tribunal estimare la concurrencia de mo- | Judicial | 64632 | 94 | 99,9 % | 687,6x |
| 5598 | parte vendedora con fecha ________________________; y c) Con la suma de | Civil | 153962 | 156 | 99,9 % | 986,9x |
| 5599 | parte vendedora no tuvo derecho a crédito fiscal por la adquisición y/o construcción del | Civil | 153962 | 175 | 99,9 % | 879,8x |
| 5600 | parte –y esto es lo que podría conjurar el riesgo de una aceptación | Civil | 142015 | 74 | 99,9 % | 1919,1x |
| 5601 | parte) y decretar medidas de revinculación. Asimismo, podrá modificar | Familia | 97488 | 68 | 99,9 % | 1433,6x |
| 5602 | parte, a quien contrató con el causante, sólo le quedaría la posibilidad de demandarlo por | Civil | 110175 | 123 | 99,9 % | 895,7x |
| 5603 | parte, contiene una disposición relativa a los delitos sexuales cometidos | Penal | 86906 | 78 | 99,9 % | 1114,2x |
| 5604 | parte, de acuerdo al principio de la razón suficiente, nada es sin razón o | Judicial | 150341 | 81 | 99,9 % | 1856,1x |
| 5605 | parte, deberá indemnizar perjuicios al comprador? | Civil | 153962 | 209 | 99,9 % | 736,7x |
| 5606 | parte, dispondrá, en la primera resolución que dicte, la suspensión | Laboral | 113458 | 137 | 99,9 % | 828,2x |
| 5607 | parte, dispone el parágrafo 141 del Código Civil alemán: “Si un negocio jurídico nulo | General | 166275 | 195 | 99,9 % | 852,7x |
| 5608 | parte, el Sr. Nisuke Ando señala que hacer diferencias entre el idioma | Judicial | 81476 | 104 | 99,9 % | 783,4x |
| 5609 | parte, el art. 2518, en las normas de la prescripción extintiva, dice que “La | General | 125500 | 146 | 99,9 % | 859,6x |
| 5610 | parte, el artículo 14 señala en su N° 1 que “deberá reconocerse a los | Judicial | 134465 | 150 | 99,9 % | 896,4x |
| 5611 | parte, el citado artículo 1892 es impreciso, pues no dice bien claramente si lo que se | Civil | 153962 | 206 | 99,9 % | 747,4x |
| 5612 | parte, el consentimiento informado cobra relevancia para la acepta- | Civil | 142015 | 106 | 99,9 % | 1339,8x |
| 5613 | parte, el elemento intencional que es la esencia del dolo constituirá siempre un factor | Civil | 120848 | 161 | 99,9 % | 750,6x |
| 5614 | parte, el precio debe convenirse dentro de márgenes razonables, según sea el valor | Civil | 153962 | 205 | 99,9 % | 751,0x |
| 5615 | parte, en Estados Unidos, junto al presidente Roosevelt, podemos verlo | Constitucional | 177323 | 178 | 99,9 % | 996,2x |
| 5616 | parte, en dos distintas calidades (por ejemplo, representante que declara, por un lado, en | Civil | 110175 | 81 | 99,9 % | 1360,2x |
| 5617 | parte, en su versión objetiva, se trata de una regla de juicio o general | Judicial | 150341 | 159 | 99,9 % | 945,5x |
| 5618 | parte, en una transferencia, sistemática y no recíproca de poderes | Constitucional | 121906 | 109 | 99,9 % | 1118,4x |
| 5619 | parte, estar sometido a influencias negativas que impliquen verdaderas | Penal | 178516 | 166 | 99,9 % | 1075,4x |
| 5620 | parte, ha creado a través su jurisprudencia ciertos estándares que | Judicial | 87237 | 85 | 99,9 % | 1026,3x |
| 5621 | parte, hay temor frente a la posibilidad de que estos programas inciten | Penal | 97633 | 68 | 99,9 % | 1435,8x |
| 5622 | parte, la Corte de Apelaciones de Arica ha señalado | Judicial | 150341 | 185 | 99,9 % | 812,7x |
| 5623 | parte, la Superintendencia lo pone en conocimiento de la nómina de | Civil | 142015 | 128 | 99,9 % | 1109,5x |
| 5624 | parte, la administración penitenciaria —Gendarmería de Chile— y por | Penal | 194788 | 100 | 99,9 % | 1947,9x |
| 5625 | parte, la circular Nº 5 en comento establece expresamente qué | Judicial | 64632 | 65 | 99,9 % | 994,3x |
| 5626 | parte, la conducta omite los verbos restricción o limitación, así como | Judicial | 81476 | 63 | 99,9 % | 1293,3x |
| 5627 | parte, la distribución horizontal de competencias podría aumentar la | Penal | 119528 | 97 | 99,9 % | 1232,2x |
| 5628 | parte, la imposibilidad de los ciudadanos de realizar muchas actuacio- | Judicial | 89450 | 94 | 99,9 % | 951,6x |
| 5629 | parte, la inversión de recursos destinados a la capacitación del Poder | Judicial | 82507 | 84 | 99,9 % | 982,2x |
| 5630 | parte, la letra b) de dicho artículo sanciona al que adquiera, posea, tenga | Penal | 178516 | 204 | 99,9 % | 875,1x |
| 5631 | parte, la normativa alemana de 1980 exigía que el peticionario no | Judicial | 89476 | 101 | 99,9 % | 885,9x |
| 5632 | parte, las medidas necesarias para permitir dicho ejercicio. Si esas medidas | Penal | 211066 | 241 | 99,9 % | 875,8x |
| 5633 | parte, más de la mitad de las mujeres de 30 a 34 años (el 52%) no | Judicial | 89476 | 66 | 99,9 % | 1355,7x |
| 5634 | parte, no completamente. En la premisa menor, se afirma la existencia | Judicial | 92792 | 49 | 99,9 % | 1893,7x |
| 5635 | parte, no existe norma legal alguna que lo habilite para proceder al corte del suministro | Civil | 192585 | 104 | 99,9 % | 1851,8x |
| 5636 | parte, no propició reforma reglamentaria alguna para contrapesar | Judicial | 134465 | 130 | 99,9 % | 1034,3x |
| 5637 | parte, no se puede desconocer que la atribución de responsabilidad | Penal | 119528 | 92 | 99,9 % | 1299,2x |
| 5638 | parte, porque las causas que lo provocan, no resultan independientes de su ejecutor, sino | Civil | 192585 | 197 | 99,9 % | 977,6x |
| 5639 | parte, puede ocurrir que una norma general esté incorporada en una materia | Civil | 120848 | 107 | 99,9 % | 1129,4x |
| 5640 | parte, que dentro de la organización de nuestro Registro Conservatorio así como dentro de las | Civil | 171433 | 197 | 99,9 % | 870,2x |
| 5641 | parte, que estas ventas son rescindibles por lesión enorme, porque siendo la regla | Civil | 153962 | 197 | 99,9 % | 781,5x |
| 5642 | parte, que la Corte, conociendo del recurso de apelación subsidiario | Familia | 100107 | 128 | 99,9 % | 782,1x |
| 5643 | parte, que la aplicación indiscriminada de la teoría en cuya virtud la | Judicial | 105809 | 68 | 99,9 % | 1556,0x |
| 5644 | parte, que se regule una regla específica que establezca exigencias de | Procesal | 86112 | 119 | 99,9 % | 723,6x |
| 5645 | parte, que tiene el carácter de comerciante otorga a otro la licencia o permiso para que | Civil | 110175 | 102 | 99,9 % | 1080,1x |
| 5646 | parte, refuerza la necesidad de interpretar adecuadamente la normativa | Laboral | 53374 | 62 | 99,9 % | 860,9x |
| 5647 | parte, sec. 1ª, pág. 348, el 12 de agosto de 1938, haciendo suyo el razonamiento del | Civil | 75968 | 89 | 99,9 % | 853,6x |
| 5648 | parte, señala que la verdad como exigencia de justicia se proyecta en el | Judicial | 150341 | 188 | 99,9 % | 799,7x |
| 5649 | parte, señala «siempre es necesario más de un testigo, porque en tanto | Judicial | 150341 | 185 | 99,9 % | 812,7x |
| 5650 | parte, señalaron que se trata de un recinto privado y que se les debe pedir permiso | Constitucional | 177323 | 105 | 99,9 % | 1688,8x |
| 5651 | parte, si se verifica que se cumplieron todos los requisitos que exigen aquellas disposiciones | Civil | 171433 | 140 | 99,9 % | 1224,5x |
| 5652 | parte, siendo la demandada sólo poseedora, obligando a acoger la acción entablada. Agrega, que | Civil | 171433 | 214 | 99,9 % | 801,1x |
| 5653 | parte, un instrumento público, el tribunal, junto con su devolución, ordenará | Penal | 211066 | 175 | 99,9 % | 1206,1x |
| 5654 | parte, y en estrecha relación con el derecho a ser oído, la Corte se | Judicial | 93914 | 124 | 99,9 % | 757,4x |
| 5655 | parte, y las potestades, por otra parte. El distingo se funda en que el derecho subjetivo | General | 166275 | 182 | 99,9 % | 913,6x |
| 5656 | parte, y las razones de equidad que buscan atenuar el rigor de las cláusulas | Civil | 120848 | 88 | 99,9 % | 1373,3x |
| 5657 | parte, “perjuicio” se define como el “detrimento patrimonial que debe ser indemnizado | Civil | 120848 | 94 | 99,9 % | 1285,6x |
| 5658 | parte. A tal efecto, se tendrá en cuenta la finalidad de la norma. Los usos, prácticas y | General | 129559 | 192 | 99,9 % | 674,8x |
| 5659 | parte. Añade que, en el peor de los casos, el envío de dicha correspondencia constituye a | Civil | 192585 | 172 | 99,9 % | 1119,7x |
| 5660 | parte.184 | Civil | 153962 | 107 | 99,9 % | 1438,9x |
| 5661 | sección 2ª, p. 136 y Corte Suprema Rol N° 7032-2010) Trigésimo noveno: … En esas | Civil | 171433 | 209 | 99,9 % | 820,3x |
| 5662 | sección de ella y, además, para garantizar su impersonalidad, deberá | Laboral | 113458 | 87 | 99,9 % | 1304,1x |
| 5663 | sección y funcionarios respecto de los indicadores de gestión | Procesal | 94881 | 85 | 99,9 % | 1116,2x |
| 5664 | sumario con algunas precisiones, así evacuados los informes o ven- | Judicial | 81476 | 114 | 99,9 % | 714,7x |
| 5665 | sumario, pero nada impide que el proceso ordinario permita | Constitucional | 112823 | 58 | 99,9 % | 1945,2x |
| 5666 | sumario. Los mismos derechos corresponderán a los herederos del conde- | Penal | 211066 | 196 | 99,9 % | 1076,9x |
| 5667 | título 2° de la Ley Nº 18.575, acudiendo a las normas del título 35 | Civil | 142015 | 110 | 99,9 % | 1291,0x |
| 5668 | título 3° del libro II, cuando fuere previsible que la persona de cuya declara- | Penal | 211066 | 222 | 99,9 % | 950,7x |
| 5669 | título 4 del mismo libro Segundo, con delitos como el falso testimonio | Penal | 178516 | 171 | 99,9 % | 1044,0x |
| 5670 | título alguno de dominio anterior al año 1997, época a la que se remonta la inscripción de las | Civil | 171433 | 137 | 99,9 % | 1251,3x |
| 5671 | título de culpa y dolo,               requisitos diferenciados. Así lo reconocen los autores y la sentencia | Civil | 142015 | 118 | 99,9 % | 1203,5x |
| 5672 | título de dominio | Judicial | 82507 | 46 | 99,9 % | 1793,6x |
| 5673 | título de información procurará no llamar la atención con esa clase de | Constitucional | 104063 | 106 | 99,9 % | 981,7x |
| 5674 | título de los albaceas, establece que lo dispuesto en los arts. 394 y 412, se extenderá | Civil | 153962 | 184 | 99,9 % | 836,8x |
| 5675 | título deseado. Así, dos años bastaban para obtener el de médico, al que había terminado | General | 129559 | 167 | 99,9 % | 775,8x |
| 5676 | título ejecutivo especial para el cobro de gastos comunes, noción última cuya definición | Civil | 192585 | 183 | 99,9 % | 1052,4x |
| 5677 | título ejecutivo ha de entenderse aquel que da cuenta de un derecho indubitable al cual | Civil | 192585 | 215 | 99,9 % | 895,7x |
| 5678 | título en cuestión no tiene el carácter de ejecutivo en relación al artículo 27 de la citada | Civil | 192585 | 196 | 99,9 % | 982,6x |
| 5679 | título en que se funde la demanda ejecutiva) y despachará mandamiento de ejecución | Civil | 120848 | 161 | 99,9 % | 750,6x |
| 5680 | título es oneroso, el bien adquirido será social, sin perjuicio de la recompensa a que | Familia | 136567 | 81 | 99,9 % | 1686,0x |
| 5681 | título fundante de la ejecución, en circunstancias que el mismo cumple con las exigencias | Civil | 192585 | 184 | 99,9 % | 1046,7x |
| 5682 | título fundante del dominio que reclama una inscripción que data del año 2013 y, si bien el | Civil | 171433 | 217 | 99,9 % | 790,0x |
| 5683 | título gratuito u oneroso. De esta manera, siguiendo esta tesis de Alessandri, a la que adherimos, no | Familia | 136567 | 148 | 99,9 % | 922,8x |
| 5684 | título inscrito de 1947 a favor del causante Juan Bautista Maricahuín Curiñán, pues la sucesión | Civil | 171433 | 210 | 99,9 % | 816,3x |
| 5685 | título inscrito y es poseedor de buena fe, no empeciéndole los efectos de la sentencia dictada en | Civil | 171433 | 214 | 99,9 % | 801,1x |
| 5686 | título invocado por su contraparte carece de mérito ejecutivo en lo que dice relación con | Civil | 192585 | 226 | 99,9 % | 852,1x |
| 5687 | título lucrativo. Dichos bienes, propios, podrán ser administrados y enajenados | Familia | 136567 | 80 | 99,9 % | 1707,1x |
| 5688 | título nulo absoluta como relativamente produce efectos no deseados en el Registro de | General | 59520 | 76 | 99,9 % | 783,2x |
| 5689 | título oneroso las cuotas de los restantes comuneros. La cuota que se adquiera, en | Familia | 136567 | 198 | 99,9 % | 689,7x |
| 5690 | título oneroso, aunque en ella se comprendan bienes raíces; la especificación de éstos | Civil | 153962 | 218 | 99,9 % | 706,2x |
| 5691 | título oneroso, y en seguida hay que reparar que el número tercero del artículo 1962 | Civil | 71319 | 102 | 99,9 % | 699,2x |
| 5692 | título oneroso”. “Artículo 1034.- Garantías comprendidas en la obligación de saneamiento. El obligado al | Civil | 110175 | 92 | 99,9 % | 1197,6x |
| 5693 | título para adquirir el dominio, pero no son modo de adquirirlo, siguiendo al Derecho | Civil | 153962 | 208 | 99,9 % | 740,2x |
| 5694 | título profesional. El tribunal, considerando que no se acreditó si | Civil | 142015 | 109 | 99,9 % | 1302,9x |
| 5695 | título singular, pudiendo comprender sólo bienes propios de los esposos, presentes o | Familia | 136567 | 114 | 99,9 % | 1198,0x |
| 5696 | título un vicio de nulidad relativa y en otras oportunidades sólo si el vicio en cuestión | General | 59520 | 62 | 99,9 % | 960,0x |
| 5697 | título universal (herencia) o a titulo singular (legado), según el art. 951 del Código | General | 166275 | 192 | 99,9 % | 866,0x |
| 5698 | título válidamente inscrito, habrá dominio. […] | Civil | 171433 | 206 | 99,9 % | 832,2x |
| 5699 | título y los que resulten de la liquidación de la sociedad conyugal o | Familia | 123490 | 161 | 99,9 % | 767,0x |
| 5700 | título, de recursos hidrobiológicos o productos derivados de ellos de | Penal | 194788 | 228 | 99,9 % | 854,3x |
| 5701 | título, desde que los derechos que corresponderían al demandado dicen relación con un predio | Civil | 171433 | 219 | 99,9 % | 782,8x |
| 5702 | título, e inscrita en el registro respectivo del Conservador de Bienes Raíces, el solicitante adquiere | Civil | 171433 | 189 | 99,9 % | 907,1x |
| 5703 | título, el juez distribuirá la obligación en proporción a sus facultades”. Siendo así, nos | Civil | 118177 | 98 | 99,9 % | 1205,9x |
| 5704 | título, mientras que los demandados ocupan cerca de 60 hectáreas, pese a que su título abarca | Civil | 171433 | 189 | 99,9 % | 907,1x |
| 5705 | título. Para los sostenedores absolutos de la teoría de la posesión inscrita yo no tengo sobre el | Civil | 171433 | 178 | 99,9 % | 963,1x |
| 5706 | título. Tratándose de las faltas indicadas en los artículos 494, Nº 5, y 496, Nº | Penal | 211066 | 245 | 99,9 % | 861,5x |
| 5707 | título” (art. 1436), es decir, a las reglas generales de las donaciones.15 | Familia | 136567 | 174 | 99,9 % | 784,9x |
| 5708 | ¿cuáles son las prestaciones de salud a las que puedo acceder? | Constitucional | 115835 | 150 | 99,9 % | 772,2x |
| 5709 | ¿cuáles son los establecimientos de salud pública a los que puedo acceder? | Constitucional | 115835 | 150 | 99,9 % | 772,2x |
| 5710 | ¿qué ocurre si estoy en situación irregular y no tengo recursos? | Constitucional | 115835 | 143 | 99,9 % | 810,0x |
| 5711 | “Capítulo II. DE LA CAPACIDAD PARA CONTRATAR Y OTRAS NORMAS RELATIVAS A LA PROTECCIÓN DEL | General | 166275 | 205 | 99,9 % | 811,1x |
| 5712 | “establece bases de los procedimientos administrativos que rigen los actos | Civil | 192585 | 189 | 99,9 % | 1019,0x |
| 5713 | “ley de bases sobre contratos administrativos de suministro y | Civil | 153962 | 149 | 99,9 % | 1033,3x |
| 5714 | “vistos | Civil | 192585 | 170 | 99,9 % | 1132,9x |
| 5715 | (si se trata del arrendamiento de un inmueble urbano regido por la ley | Civil | 71319 | 146 | 99,8 % | 488,5x |
| 5716 | 1    Por esto, la Comisión de Derechos Humanos creó un grupo de trabajo compuesto básicamente por 48 de los | Penal | 72395 | 128 | 99,8 % | 565,6x |
| 5717 | 1 Artículo 40.3: Los Estados parte tomarán las medidas apropiadas para promover | Penal | 86906 | 139 | 99,8 % | 625,2x |
| 5718 | 1 Artículo 64 Ley 19.947: «A falta de acuerdo, corresponderá al juez determinar la | Familia | 97488 | 204 | 99,8 % | 477,9x |
| 5719 | 1 Asigna a los principios especificados en instrumentos administrativos un rol de | Penal | 51155 | 91 | 99,8 % | 562,1x |
| 5720 | 1 Así fue reconocido en 2014 por la Corte de Apelaciones de Concepción, que | Laboral | 74025 | 166 | 99,8 % | 445,9x |
| 5721 | 1 Con relación a esto último, véanse Tarello (1980: 39-42), Guastini (2001: 1) y | Judicial | 92792 | 157 | 99,8 % | 591,0x |
| 5722 | 1 Durante el tiempo en que esté vigente la alerta sanitaria decretada con ocasión | Laboral | 98828 | 189 | 99,8 % | 522,9x |
| 5723 | 1 El artículo 7 señala en su inciso final: «Todo acto en contravención a este artículo | Judicial | 87950 | 136 | 99,8 % | 646,7x |
| 5724 | 1 En el cuerpo del texto se hace alusión a que el catálogo de normas del Protocolo | Judicial | 82507 | 135 | 99,8 % | 611,2x |
| 5725 | 1 Esta premisa ratifica que no basta con exigir el conocimiento de la ley, sino que | Judicial | 30834 | 72 | 99,8 % | 428,2x |
| 5726 | 1 Este proceso se encuentra ampliamente documentado en diversos estudios, como | Penal | 86906 | 162 | 99,8 % | 536,5x |
| 5727 | 1 Inciso final artículo 225 del Código Civil: «Mientras una nueva subinscripción | Familia | 97488 | 205 | 99,8 % | 475,6x |
| 5728 | 1 Internet ofrece una amplia gama de uso, algunos la comparan con un iceberg | Penal | 97633 | 202 | 99,8 % | 483,3x |
| 5729 | 1 La figura original castigaba con presidio o reclusión menores y suspensión en | Judicial | 78893 | 153 | 99,8 % | 515,6x |
| 5730 | 1 No obstante la imprecisión de las expresiones «tráfico de drogas» y «microtráfico | Penal | 97633 | 217 | 99,8 % | 449,9x |
| 5731 | 1 Para representar a Chile en este trabajo, la Corte Suprema designó al ministro | Judicial | 30834 | 63 | 99,8 % | 489,4x |
| 5732 | 1 Rol 137.840-2022 del 19 de diciembre de 2022, Marcelo Antúnez Espíndola con | Judicial | 87950 | 205 | 99,8 % | 429,0x |
| 5733 | 1 Se agradece especialmente la selección de casos realizada por Marcela Toledo | Penal | 51155 | 100 | 99,8 % | 511,6x |
| 5734 | 1 Sentencia de la Corte Suprema, rol 91.731, 1 de febrero de 2023: «Sexto: Que el | Familia | 97488 | 204 | 99,8 % | 477,9x |
| 5735 | 1 También, Corte Suprema, rol 22.179-21, del 8 de abril de 2022, en la que expresa | Penal | 97633 | 170 | 99,8 % | 574,3x |
| 5736 | 1 saludar | Judicial | 53521 | 81 | 99,8 % | 660,8x |
| 5737 | 1. A los efectos de la presente Convención, se entenderá por el término | Judicial | 78893 | 176 | 99,8 % | 448,3x |
| 5738 | 1. Atender satisfactoriamente los requerimientos de información | Judicial | 52128 | 98 | 99,8 % | 531,9x |
| 5739 | 1. Como un can n criteri para la interpretación de l s c ntrat s: la interpretación ha | Civil | 110175 | 187 | 99,8 % | 589,2x |
| 5740 | 1. Corresponde a una acción u omisión, en tanto no solo puede pro- | Laboral | 53374 | 109 | 99,8 % | 489,7x |
| 5741 | 1. Cualquier trabajador u organización sindical que invocando un | Laboral | 74025 | 152 | 99,8 % | 487,0x |
| 5742 | 1. Desde el momento en que un contrato no contiene nada contrario a las leyes, ni al orden | Civil | 110175 | 184 | 99,8 % | 598,8x |
| 5743 | 1. En el primero de estos informes, el Estado dio cuenta de las | Judicial | 87237 | 133 | 99,8 % | 655,9x |
| 5744 | 1. En todas las medidas | Penal | 72395 | 119 | 99,8 % | 608,4x |
| 5745 | 1. En una cláusula del contrato de trabajo o del anexo, en su caso, se | Laboral | 98828 | 180 | 99,8 % | 549,0x |
| 5746 | 1. Formas en que | Procesal | 95124 | 154 | 99,8 % | 617,7x |
| 5747 | 1. La acción civil que tenga como único objeto la restitución de la cosa, deberá | Civil | 96458 | 163 | 99,8 % | 591,8x |
| 5748 | 1. La codificación estabilizó el Derecho. 2. Existencia de un monopolio interpretativo | General | 125500 | 198 | 99,8 % | 633,8x |
| 5749 | 1. La reasignación temporal de funciones se realizará durante el | Judicial | 52128 | 110 | 99,8 % | 473,9x |
| 5750 | 1. Los Estados partes garantizarán al niño que esté en condiciones de | Constitucional | 44292 | 97 | 99,8 % | 456,6x |
| 5751 | 1. Los tribunales chilenos tienen competencia para juzgar | Procesal | 95124 | 150 | 99,8 % | 634,2x |
| 5752 | 1. Lugar hábil: i) Lugares y recintos de libre acceso al público; b) en | Judicial | 89450 | 178 | 99,8 % | 502,5x |
| 5753 | 1. Normalidad, carácter episódico y remisión espontánea de la mayor | Penal | 86906 | 161 | 99,8 % | 539,8x |
| 5754 | 1. Obstaculizar la formación del sindicato: refiere a cualquier acción | Laboral | 74025 | 132 | 99,8 % | 560,8x |
| 5755 | 1. Procedimiento ordinario. Este será aplicable a todos los asuntos | Familia | 97488 | 157 | 99,8 % | 620,9x |
| 5756 | 1. Propósitos | Judicial | 53521 | 85 | 99,8 % | 629,7x |
| 5757 | 1. Que en este pleito se va a juzgar el funcionamiento de un servicio público y, en esa medida, esta materia | Judicial | 105809 | 162 | 99,8 % | 653,1x |
| 5758 | 1. Que la parte demandante dedujo recurso de casación en la forma en contra de la sentencia | Judicial | 79146 | 123 | 99,8 % | 643,5x |
| 5759 | 1. Revisar el correo electrónico del tribunal y el del oficial 1°, para | Judicial | 52128 | 89 | 99,8 % | 585,7x |
| 5760 | 1. Rol Nº 1093-2019. Fijación de audiencia pública y convocatoria para formación de | Judicial | 54457 | 114 | 99,8 % | 477,7x |
| 5761 | 1. Rol Nº 25-2020. Acta de visita practicada por la ministro suplente señora Carmen | Judicial | 54457 | 93 | 99,8 % | 585,6x |
| 5762 | 1. Rol Nº 888-2018. Excma. CS revoca la sentencia dictada por el Tribunal Pleno | Judicial | 54457 | 101 | 99,8 % | 539,2x |
| 5763 | 1. Se aplicarán, en lo que no resulte contrario a las normas especia- | Penal | 57066 | 107 | 99,8 % | 533,3x |
| 5764 | 1. Sensibilización y difusión del lenguaje claro en las labores del Poder | Judicial | 53521 | 117 | 99,8 % | 457,4x |
| 5765 | 1. Si la intervención con la familia en contexto de voluntariedad no | Constitucional | 46896 | 107 | 99,8 % | 438,3x |
| 5766 | 1. Si no anota en el repertorio los títulos en el acto de recibirlos o no lo cierra | General | 59520 | 94 | 99,8 % | 633,2x |
| 5767 | 1. Situación de los causahabientes a título singular: reciben este nombre quienes suceden a | Civil | 110175 | 197 | 99,8 % | 559,3x |
| 5768 | 1. Sujetos y vinculación: el artículo 92 número 8 de la Ley 19.968 no | Judicial | 82507 | 184 | 99,8 % | 448,4x |
| 5769 | 1. Síntomas síquicos: depresión, ansiedad, ataques de pánico, irritabili- | Laboral | 53374 | 98 | 99,8 % | 544,6x |
| 5770 | 1. Todo Estado parte dispondrá lo que sea necesario para instituir su | Judicial | 78893 | 136 | 99,8 % | 580,1x |
| 5771 | 1. Todo Estado parte en cuyo territorio se encuentre la persona de la | Judicial | 78893 | 170 | 99,8 % | 464,1x |
| 5772 | 1. Todo Estado parte velará por que se incluyan una educación y una | Judicial | 78893 | 130 | 99,8 % | 606,9x |
| 5773 | 1. Una modalidad de la notificación por cédula: Así, algunos sostie- | Judicial | 89450 | 162 | 99,8 % | 552,2x |
| 5774 | 1.1 El administrador o quien corresponda, presentará al | Judicial | 52128 | 87 | 99,8 % | 599,2x |
| 5775 | 1.1. Prohibiciones de ingreso | Constitucional | 115835 | 183 | 99,8 % | 633,0x |
| 5776 | 1.1.1 Antiguo procedimiento | Penal | 57066 | 102 | 99,8 % | 559,5x |
| 5777 | 1.1.2 Nuevo procedimiento | Penal | 57066 | 111 | 99,8 % | 514,1x |
| 5778 | 1.1.4 Principales principios y garantías | Penal | 57066 | 101 | 99,8 % | 565,0x |
| 5779 | 1.1.4.2 Exclusividad de la investigación penal | Penal | 57066 | 122 | 99,8 % | 467,8x |
| 5780 | 1.1.4.3 Oralidad, publicidad e inmediación | Penal | 57066 | 111 | 99,8 % | 514,1x |
| 5781 | 1.1.4.4 Presunción de inocencia | Penal | 57066 | 119 | 99,8 % | 479,5x |
| 5782 | 1.1.4.7 Vigencia de derechos fundamentales | Penal | 57066 | 111 | 99,8 % | 514,1x |
| 5783 | 1.1.4.8 Legalidad | Penal | 57066 | 102 | 99,8 % | 559,5x |
| 5784 | 1.1.5.1 Ministerio Público | Penal | 57066 | 102 | 99,8 % | 559,5x |
| 5785 | 1.1.5.2 El imputado | Penal | 57066 | 114 | 99,8 % | 500,6x |
| 5786 | 1.1.5.3 Defensoría Penal Pública | Penal | 57066 | 114 | 99,8 % | 500,6x |
| 5787 | 1.1.5.4 La víctima y el querellante | Penal | 57066 | 109 | 99,8 % | 523,5x |
| 5788 | 1.1.5.5 El tribunal | Penal | 57066 | 101 | 99,8 % | 565,0x |
| 5789 | 1.2 Funciones de la responsabilidad. 2.- Clases de responsabilidad civil. 3.- ¿En qué se | Civil | 96458 | 154 | 99,8 % | 626,4x |
| 5790 | 1.2. Especialización | Penal | 86906 | 145 | 99,8 % | 599,4x |
| 5791 | 1.2.1 Consejo General del Poder Judicial (España) | Judicial | 54457 | 123 | 99,8 % | 442,7x |
| 5792 | 1.2.2 Consiglio Superiore della Magistratura (Italia) | Judicial | 54457 | 94 | 99,8 % | 579,3x |
| 5793 | 1.2.2 Reglas técnicas | Procesal | 94881 | 150 | 99,8 % | 632,5x |
| 5794 | 1.2.2 Sexualidad e identidad sexual en | Judicial | 87237 | 135 | 99,8 % | 646,2x |
| 5795 | 1.2.3 El Consejo Superior de la Judicatura (Colombia) | Judicial | 54457 | 135 | 99,8 % | 403,4x |
| 5796 | 1.2.4 El caso chileno | Judicial | 54457 | 117 | 99,8 % | 465,4x |
| 5797 | 1.3. La Regla 16. Las conferencias y órdenes de case management | Procesal | 96699 | 161 | 99,8 % | 600,6x |
| 5798 | 1.3.1 La variedad infinita de la diversidad sexual | Judicial | 87237 | 140 | 99,8 % | 623,1x |
| 5799 | 1.3.4.3 Identidad de género y disforia de género | Judicial | 87237 | 132 | 99,8 % | 660,9x |
| 5800 | 1.4        Contenido | Familia | 65192 | 118 | 99,8 % | 552,5x |
| 5801 | 1.4. Carácter mudable de los alimentos: cosa juzgada provisional en materia de | Civil | 23185 | 48 | 99,8 % | 483,0x |
| 5802 | 1.5     Estructura organizacional | Judicial | 44331 | 88 | 99,8 % | 503,8x |
| 5803 | 1.5     Unidad de | Familia | 26096 | 40 | 99,8 % | 652,4x |
| 5804 | 1.5. Imposición del pago de alimentos a determinados asignatarios. Responsabilidad | Civil | 23185 | 57 | 99,8 % | 406,8x |
| 5805 | 1.5.1 El interés superior del niño | Familia | 65192 | 117 | 99,8 % | 557,2x |
| 5806 | 1.5.2 El derecho a ser oído y la autonomía progresiva | Familia | 65192 | 110 | 99,8 % | 592,7x |
| 5807 | 1.6     Reglas sobre cumplimiento | Familia | 26096 | 44 | 99,8 % | 593,1x |
| 5808 | 1.6. Resumen de las reglas a que se somete el pago de los alimentos como asignación | Civil | 23185 | 53 | 99,8 % | 437,5x |
| 5809 | 1.6.2 Convencional | Familia | 65192 | 115 | 99,8 % | 566,9x |
| 5810 | 1.6.3 Judicial | Familia | 65192 | 130 | 99,8 % | 501,5x |
| 5811 | 1.6.3.1 Otorgamiento a uno de los padres | Familia | 65192 | 111 | 99,8 % | 587,3x |
| 5812 | 1.6.3.2 Otorgamiento a un tercero | Familia | 65192 | 115 | 99,8 % | 566,9x |
| 5813 | 1.6.3.2.1 NNA no reconocido por ninguno de sus | Familia | 65192 | 115 | 99,8 % | 566,9x |
| 5814 | 1.6.3.2.2 Inhabilidad física o moral de ambos padres | Familia | 65192 | 130 | 99,8 % | 501,5x |
| 5815 | 1.8.1 Competencia | Familia | 65192 | 101 | 99,8 % | 645,5x |
| 5816 | 1.8.2 Procedimiento | Familia | 65192 | 117 | 99,8 % | 557,2x |
| 5817 | 1.8.3 Cumplimiento | Familia | 65192 | 107 | 99,8 % | 609,3x |
| 5818 | 1.8.4   Medidas de resguardo            74 | Familia | 26096 | 54 | 99,8 % | 483,3x |
| 5819 | 10   Se sugiere revisar la breve reseña histórica sobre el contencioso-administrativo en el Estado de derecho | Judicial | 105809 | 161 | 99,8 % | 657,2x |
| 5820 | 10 Artículo 192: «Cuando la apelación proceda sólo en el efecto devolutivo, seguirá | Judicial | 89450 | 204 | 99,8 % | 438,5x |
| 5821 | 10 Artículo 28 de la Ley 21.430, derecho a ser oído: «Todo niño, niña o adolescente | Familia | 97488 | 157 | 99,8 % | 620,9x |
| 5822 | 10 Cisternas (2011: 111, 142 y 143), quien además enuncia los criterios indiciarios | Penal | 97633 | 158 | 99,8 % | 617,9x |
| 5823 | 10 Es decir, es una solución vinculada toda vez que existen límites institucionales | Judicial | 92792 | 157 | 99,8 % | 591,0x |
| 5824 | 10 Estas normas actualmente se encuentran derogadas por la promulgación el 6 | Judicial | 81675 | 198 | 99,8 % | 412,5x |
| 5825 | 10 Este es un estudio internacional que incluye también el análisis de comentarios | Laboral | 53374 | 91 | 99,8 % | 586,5x |
| 5826 | 10 Matus (1998: 138 y 139) agrega que al mismo resultado se llegaría si se miran | Penal | 97633 | 185 | 99,8 % | 527,7x |
| 5827 | 10 Según Iturriaga, esta tesis se basa en «una interpretación armónica y coherente | Laboral | 98828 | 200 | 99,8 % | 494,1x |
| 5828 | 10 Véase https://bit.ly/3I70MWs | Judicial | 78893 | 170 | 99,8 % | 464,1x |
| 5829 | 10 Véase los fallos en causa rol 203-2009 de la Corte de Apelaciones de Santiago de | Penal | 86906 | 158 | 99,8 % | 550,0x |
| 5830 | 10 Véase «Teletrabajo: La ley que la crisis del covid-19 ayudó a aprobar». Palabra | Laboral | 98828 | 152 | 99,8 % | 650,2x |
| 5831 | 10. Arraigo: Es el proceso a través del cual se establece una relación | Judicial | 53521 | 102 | 99,8 % | 524,7x |
| 5832 | 10. CARRETTA, Francesco (2018b): “El derecho del | Penal | 72395 | 109 | 99,8 % | 664,2x |
| 5833 | 10. Con la misma finalidad de propender al equilibrio en la carga de trabajo entre | Penal | 57066 | 127 | 99,8 % | 449,3x |
| 5834 | 10. En casos de personas solicitantes de asilo y refugiadas con causas | Judicial | 53521 | 110 | 99,8 % | 486,6x |
| 5835 | 10. Gauché Marchetti, Ximena. 2014. “Análisis crítico | Judicial | 87237 | 132 | 99,8 % | 660,9x |
| 5836 | 10. Notificaciones a personas privadas de libertad en Centros de | Judicial | 89450 | 196 | 99,8 % | 456,4x |
| 5837 | 10. Realizar certificación de acuerdo a lo solicitado por el abogado | Judicial | 44331 | 81 | 99,8 % | 547,3x |
| 5838 | 10.1.1 El derecho del niño a ser criado y | Penal | 72395 | 115 | 99,8 % | 629,5x |
| 5839 | 10.2.3 Niños y adolescentes frente a la persecución | Penal | 72395 | 114 | 99,8 % | 635,0x |
| 5840 | 10.2.4 Secuestro internacional de menores | Penal | 72395 | 119 | 99,8 % | 608,4x |
| 5841 | 100. Las decisiones judiciales analizadas no velaron efectivamente | Penal | 72395 | 128 | 99,8 % | 565,6x |
| 5842 | 105   Señalando ejemplos de privación o desconocimiento, los profesores SILVA BASCUÑÁN, Alejandro, citado en | Judicial | 105809 | 161 | 99,8 % | 657,2x |
| 5843 | 106. A inicios de 2017 el Fiscal a cargo de la investigación penal por la | Penal | 72395 | 122 | 99,8 % | 593,4x |
| 5844 | 107. Los NNA en las residencias han reportado prácticas de malos | Penal | 72395 | 115 | 99,8 % | 629,5x |
| 5845 | 11 Corresponde a la cantidad de adolescentes y jóvenes que ingresaron durante el | Penal | 86906 | 158 | 99,8 % | 550,0x |
| 5846 | 11 Corte Suprema, rol 94.899-16, del 25 de enero de 2017 (111,9 gramos de cannabis | Penal | 97633 | 198 | 99,8 % | 493,1x |
| 5847 | 11 El reenvío al Libro II del Código de Procedimiento Civil —por norma expresa | Procesal | 86112 | 167 | 99,8 % | 515,6x |
| 5848 | 11 En Corte Suprema, rol 33.723-19, del 10 de marzo de 2020, se declara que «no | Penal | 97633 | 201 | 99,8 % | 485,7x |
| 5849 | 11 En ese sentido, nuestra jurisprudencia ha comentado: «Noveno: que, conviene | Familia | 97488 | 197 | 99,8 % | 494,9x |
| 5850 | 11 En esta línea se encuentra en actual tramitación en el Congreso Nacional, bajo | Judicial | 89450 | 219 | 99,8 % | 408,4x |
| 5851 | 11 En este contexto, «el estudio español sobre “Teletrabajo/Trabajo Presencial” | Laboral | 98828 | 195 | 99,8 % | 506,8x |
| 5852 | 11 La Ley de Matrimonio Civil (LMC) de 2004, en la versión original del artículo 5 | Familia | 123490 | 211 | 99,8 % | 585,3x |
| 5853 | 11 La minoría de edad como eximente de responsabilidad penal en Chile proviene | Penal | 86906 | 145 | 99,8 % | 599,4x |
| 5854 | 11 Nos referimos a la tendencia de las y los jueces a analizar los argumentos de | Judicial | 81675 | 170 | 99,8 % | 480,4x |
| 5855 | 11 Para los efectos de la Convención, específicamente teniendo en consideración | Judicial | 62514 | 150 | 99,8 % | 416,8x |
| 5856 | 11 Sentencia de la Corte de Apelaciones de Santiago, rol 1.356-2015, 14 de julio de | Familia | 97488 | 204 | 99,8 % | 477,9x |
| 5857 | 11 Véase «Acceso a la justicia en la promoción y protección de los derechos de los | Judicial | 60665 | 93 | 99,8 % | 652,3x |
| 5858 | 11.   ETCHEBERRY, Leonor; VELOSO, Paulina y MU-             24. QUINTANA, María (2009): “Legislación y juris- | Familia | 65192 | 136 | 99,8 % | 479,4x |
| 5859 | 11. El Comité insta al Estado parte a modificar el tipo penal del artícu- | Judicial | 78893 | 148 | 99,8 % | 533,1x |
| 5860 | 11. Los exhortos que ingresen serán tramitados en forma rotativa por cada uno | Penal | 57066 | 133 | 99,8 % | 429,1x |
| 5861 | 11. Protección internacional: Es la ayuda que se ofrece a una persona | Judicial | 53521 | 133 | 99,8 % | 402,4x |
| 5862 | 11.1. Extinción por adquirir la propiedad otra persona. 11.2. Extinción sin que se | Civil | 49700 | 96 | 99,8 % | 517,7x |
| 5863 | 113. El Tribunal constata que la Corte Suprema de Justicia mencionó | Judicial | 92792 | 172 | 99,8 % | 539,5x |
| 5864 | 118. Este Tribunal recuerda, como lo señala la Convención de Belém do | Judicial | 78893 | 144 | 99,8 % | 547,9x |
| 5865 | 118. Si cumple con lo anterior, el tribunal tendrá la solicitud por | Judicial | 64632 | 131 | 99,8 % | 493,4x |
| 5866 | 12 A propósito de los trabajadores de plataformas digitales que presten servicios | Laboral | 98828 | 209 | 99,8 % | 472,9x |
| 5867 | 12 Al respecto, véase la sentencia de la Corte Suprema, rol 29.228-2018, 3 de febrero | Familia | 97488 | 217 | 99,8 % | 449,3x |
| 5868 | 12 Corte Suprema, rol 12.564-18, del 16 de agosto de 2018. La disquisición de la | Penal | 97633 | 196 | 99,8 % | 498,1x |
| 5869 | 12 El mensaje del ejecutivo señaló: «Como primera medida en orden a simplificar | Judicial | 62888 | 118 | 99,8 % | 532,9x |
| 5870 | 12 En la sentencia del caso Valenzuela con Administradora de Supermercados | Laboral | 74025 | 184 | 99,8 % | 402,3x |
| 5871 | 12 Fundamentación y motivación son términos que, en ocasiones, se expresan | Judicial | 42513 | 78 | 99,8 % | 545,0x |
| 5872 | 12 Matus y Ramírez (2019: 475). En Corte Suprema, rol 24.909-17, del 12 de julio de | Penal | 97633 | 188 | 99,8 % | 519,3x |
| 5873 | 12 Por ejemplo, en Francia la normativa vigente establece que «esta modalidad en | Laboral | 98828 | 174 | 99,8 % | 568,0x |
| 5874 | 12 Véase por ejemplo audiencias RIT 28-2009; 53-2009; 81-2009; y, 83-2009, todas | Penal | 86906 | 179 | 99,8 % | 485,5x |
| 5875 | 12. En el testimonio de notificación deberá expresarse, además del | Judicial | 89450 | 206 | 99,8 % | 434,2x |
| 5876 | 12. La providencia del auto de apertura de juicio oral será dictada por el Juez | Penal | 57066 | 135 | 99,8 % | 422,7x |
| 5877 | 12. Preparar la agenda de audiencias entregando la carpeta al juez con | Judicial | 52128 | 110 | 99,8 % | 473,9x |
| 5878 | 12. Que, tal como se expresó en el fallo en revisión, en subsidio de lo anterior el actor afirmó | Judicial | 79146 | 126 | 99,8 % | 628,1x |
| 5879 | 125. En el presente caso, la señora Fernández Ortega estuvo sometida | Judicial | 78893 | 167 | 99,8 % | 472,4x |
| 5880 | 126. En el presente caso, las diferencias en la regulación disciplinaria | Judicial | 78893 | 122 | 99,8 % | 646,7x |
| 5881 | 127. La vulnerabilidad del detenido se agrava cuando la detención es ilegal | Judicial | 78893 | 171 | 99,8 % | 461,4x |
| 5882 | 13   Barragana según la RAE: Concubina. Esposa legítima, aunque de condición inferior a la del mari- | Familia | 65085 | 124 | 99,8 % | 524,9x |
| 5883 | 13. El Estado parte debe adoptar medidas eficaces para garantizar que | Judicial | 78893 | 178 | 99,8 % | 443,2x |
| 5884 | 13. Los órdenes de prelación establecidos en el acápite 11 y en el párrafo primero | Penal | 57066 | 92 | 99,8 % | 620,3x |
| 5885 | 13. Tomar juramento a los testigos y personas que intervengan en | Judicial | 52128 | 85 | 99,8 % | 613,3x |
| 5886 | 1338 N° 1. En consecuencia, se requiere de un texto legal expreso o una explícita | Civil | 118177 | 206 | 99,8 % | 573,7x |
| 5887 | 139 La Corte Suprema confirmó la sentencia apelada dictada por la Corte de Apelaciones de Santiago y rechazó | Judicial | 105809 | 176 | 99,8 % | 601,2x |
| 5888 | 14   Derecho a los beneficios de la cultura | Judicial | 81675 | 130 | 99,8 % | 628,3x |
| 5889 | 14 APT, Monitoreo de lugares de detención. Una guía práctica. 2004. Disponible en | Judicial | 78893 | 152 | 99,8 % | 519,0x |
| 5890 | 14 Corte Suprema, rol 2.005-05, del 19 de julio de 2005, sin embargo, en el mismo | Penal | 97633 | 156 | 99,8 % | 625,9x |
| 5891 | 14 Corte Suprema, rol 37.797-15, del 26 de enero de 2016. En Corte Suprema, rol | Penal | 97633 | 198 | 99,8 % | 493,1x |
| 5892 | 14 Demanda de oposición a la ejecución provisional: «La demanda de oposición a | Judicial | 89450 | 174 | 99,8 % | 514,1x |
| 5893 | 14 En relación con esta atenuante especial cabe subrayar la disposición contenida | Penal | 97633 | 148 | 99,8 % | 659,7x |
| 5894 | 14 Esta conclusión la desprenden de los siguientes fallos: Sentencia del Tribunal | Laboral | 98828 | 171 | 99,8 % | 577,9x |
| 5895 | 14 Para más información, véase Corte Suprema, rol 29.094-2019 del 1 de junio de | Judicial | 87950 | 178 | 99,8 % | 494,1x |
| 5896 | 14 Se señaló en el capítulo 2 que lo costoso de la prueba pericial puede recogerse a | Procesal | 86112 | 195 | 99,8 % | 441,6x |
| 5897 | 14. El Comité toma nota de la reforma en 2010 de la competencia de | Judicial | 78893 | 176 | 99,8 % | 448,3x |
| 5898 | 14. Implementar y dar cumplimiento a las políticas y directrices | Judicial | 52128 | 109 | 99,8 % | 478,2x |
| 5899 | 14. Si durante el periodo de vigencia del presente acuerdo, con ocasión de nuevos | Penal | 57066 | 89 | 99,8 % | 641,2x |
| 5900 | 14.1. Generalidades | Civil | 36671 | 76 | 99,8 % | 482,5x |
| 5901 | 14.5. Las contraescrituras.49 | Procesal | 24749 | 49 | 99,8 % | 505,1x |
| 5902 | 14.908. A mayor abundamiento, además, se debe tener presente para arribar a la interpretación | Familia | 81198 | 159 | 99,8 % | 510,7x |
| 5903 | 14.908. Pero el aludido planteamiento doctrinario mantiene su vigencia, en lo que | Familia | 81198 | 193 | 99,8 % | 420,7x |
| 5904 | 14160. Sin embargo, la misma sentencia contiene el voto | Familia | 65085 | 140 | 99,8 % | 464,9x |
| 5905 | 144   Ver “Asociación de Industrias Metalúrgicas y Metalmecánicas ASIMET A.G. con CODELCO-CHILE”, CA San- | Judicial | 105809 | 196 | 99,8 % | 539,8x |
| 5906 | 146. Al respecto, la Corte recuerda que los servicios sanitarios referidos | Judicial | 87950 | 158 | 99,8 % | 556,6x |
| 5907 | 1469. El artículo 1457 dispone: “Por el contrato en favor de tercero, el promitente se obliga | Civil | 110175 | 172 | 99,8 % | 640,6x |
| 5908 | 15   Dictamen Nº 5845/365 de 30 de noviembre de 1999, reconsiderando la doctrina anterior contenida en dicta- | Laboral | 100583 | 152 | 99,8 % | 661,7x |
| 5909 | 15 En la primera hipótesis la colaboración recae sobre la misma investigación que | Penal | 97633 | 219 | 99,8 % | 445,8x |
| 5910 | 15 Esta visión entiende que la negociación colectiva es «un mecanismo idóneo | Laboral | 98828 | 208 | 99,8 % | 475,1x |
| 5911 | 15 Por cierto, en los casos de jueces y juezas que, además de ser abogados, tengan | Procesal | 86112 | 144 | 99,8 % | 598,0x |
| 5912 | 15 Sentencia del caso Actionline Chile S. A. con Yutronic, Corte de Apelaciones de | Laboral | 74025 | 117 | 99,8 % | 632,7x |
| 5913 | 15 Véase «Proyecto de recomendación general núm. 28 relativa al artículo 2 de | Judicial | 60665 | 100 | 99,8 % | 606,6x |
| 5914 | 15. El Comité insta al Estado a continuar la reforma del Sistema de | Judicial | 78893 | 119 | 99,8 % | 663,0x |
| 5915 | 15. Que el artículo 892 del Código Civil dispone que se puede reivindicar una cuota determinada | Judicial | 79146 | 126 | 99,8 % | 628,1x |
| 5916 | 15. Se propenderá a que las audiencias más breves, tales como: revisión de | Penal | 57066 | 122 | 99,8 % | 467,8x |
| 5917 | 150 A y B, ni se introducía un nuevo párrafo, sino que se modificaban los | Judicial | 78893 | 191 | 99,8 % | 413,1x |
| 5918 | 150 A) de los apremios ilegítimos (artículo 150 D) aunque contempla | Judicial | 78893 | 158 | 99,8 % | 499,3x |
| 5919 | 150 A, cuando define torturas. La primera se refiere a la intención en las | Judicial | 78893 | 132 | 99,8 % | 597,7x |
| 5920 | 1526 N° 4. El acreedor tendrá entonces derecho a exigir a cualquiera de los herederos | Civil | 118177 | 209 | 99,8 % | 565,4x |
| 5921 | 1549. La secuencia es, entonces: obligación de dar →obligación de conservar → | Civil | 118177 | 204 | 99,8 % | 579,3x |
| 5922 | 155   CS rol 20-2004, de 5 de enero de 2004, “SAAM con Fetrapa y Fetramapora” y rol 962-2006, de 6 de marzo | Judicial | 105809 | 189 | 99,8 % | 559,8x |
| 5923 | 1553 C.C.). Si es necesario embargar y realizar bienes, se | Procesal | 95124 | 179 | 99,8 % | 531,4x |
| 5924 | 16 CIDH. Caso de los Hermanos Gómez Paquiyauri con Perú. Sentencia de 8 de | Judicial | 78893 | 175 | 99,8 % | 450,8x |
| 5925 | 16 Convención de las Naciones Unidas en contra de la corrupción promulgada | Judicial | 62514 | 118 | 99,8 % | 529,8x |
| 5926 | 16 Corte Suprema, rol 2.005-05, del 19 de julio de 2005. Decisiones similares en | Penal | 97633 | 206 | 99,8 % | 473,9x |
| 5927 | 16 En este sentido, el sistema de menores pretende prescindir de la garantía de la | Penal | 86906 | 139 | 99,8 % | 625,2x |
| 5928 | 16 Juzgado de Letras del Trabajo de Puerto Montt. RIT T-40-2016, 5 de septiembre | Laboral | 53374 | 83 | 99,8 % | 643,1x |
| 5929 | 16 La doctrina que distingue entre los daños que produce el divorcio en sí mismo | Familia | 123490 | 191 | 99,8 % | 646,5x |
| 5930 | 16 Respecto a la función analítica del silogismo, señala Alexy (2009: 221) que «la | Judicial | 92792 | 165 | 99,8 % | 562,4x |
| 5931 | 16 Sentencia del caso Dirección Regional del Trabajo Metropolitana Oriente con | Laboral | 74025 | 136 | 99,8 % | 544,3x |
| 5932 | 16 Sobre la falibilidad de la prueba de ADN, los casos de error han sido de falsos | Procesal | 86112 | 131 | 99,8 % | 657,3x |
| 5933 | 16 Un listado y análisis de esos fallos en el período 2016 a 2018, en Rodríguez | Penal | 97633 | 184 | 99,8 % | 530,6x |
| 5934 | 16 Una antinomia lógica es «cualquier situación en la que dos normas jurídicas | Judicial | 92792 | 183 | 99,8 % | 507,1x |
| 5935 | 16. Dictar los reglamentos sobre seguridad y bienestar social de los | Judicial | 54457 | 89 | 99,8 % | 611,9x |
| 5936 | 16. Ejercer las demás funciones que le sean asignadas por el juez | Judicial | 52128 | 83 | 99,8 % | 628,0x |
| 5937 | 16. Los magistrados del Tribunal deberán abstenerse de introducir modificaciones | Penal | 57066 | 119 | 99,8 % | 479,5x |
| 5938 | 161 La discriminación por sexo ha sido entendida dentro el Sistema Universal de Protección de los Derechos | Judicial | 89476 | 137 | 99,8 % | 653,1x |
| 5939 | 161. Y aun en cuanto a estos presúmese por lo regular que se limitó la intención de las | Civil | 120848 | 219 | 99,8 % | 551,8x |
| 5940 | 162. Rafael Samuel y Emilio Moisés Gómez Paquiyauri eran niños de | Judicial | 78893 | 157 | 99,8 % | 502,5x |
| 5941 | 163. En esta materia, cuando se trata de la protección de los derechos | Judicial | 78893 | 122 | 99,8 % | 646,7x |
| 5942 | 1636. Así, por ejemplo, Juan debe $5.000.000.- a Pedro, y en lugar de pagarle tal | Civil | 75968 | 178 | 99,8 % | 426,8x |
| 5943 | 165 Código Tributario | Judicial | 62888 | 127 | 99,8 % | 495,2x |
| 5944 | 17 Agrega la sentencia que el principio de dignidad irradia en igual magnitud a | Judicial | 81675 | 124 | 99,8 % | 658,7x |
| 5945 | 17 Artículo 174: «Se entenderá firme o ejecutoriada una resolución desde que se | Judicial | 89450 | 211 | 99,8 % | 423,9x |
| 5946 | 17 De la familia original se pasa a una familia derivada, constituida por hijos o | Familia | 123490 | 195 | 99,8 % | 633,3x |
| 5947 | 17 En Wróblewski (1969), Alexy (2009), MacCormick (2003; 2005; 2007), Tarello | Judicial | 92792 | 162 | 99,8 % | 572,8x |
| 5948 | 17 En el caso del artículo 8 de la Ley 20.000, salvo algunos fallos aislados, la Corte | Penal | 97633 | 185 | 99,8 % | 527,7x |
| 5949 | 17 Es menester distinguir, para efectos de la precisión en el ámbito financiero del | Judicial | 87950 | 170 | 99,8 % | 517,4x |
| 5950 | 17 Por ejemplo, un cambio de juez entre la etapa de admisibilidad y la rendición de | Procesal | 86112 | 135 | 99,8 % | 637,9x |
| 5951 | 17 Véase «Informe definitivo del Estudio sobre los pueblos indígenas y el derecho a | Judicial | 60665 | 144 | 99,8 % | 421,3x |
| 5952 | 17. Confeccionar el archivo y hacer una nómina de las causas que se | Judicial | 52128 | 100 | 99,8 % | 521,3x |
| 5953 | 17. Las dificultades de interpretación que a la administración suscite la aplicación | Penal | 57066 | 110 | 99,8 % | 518,8x |
| 5954 | 17. Observar y cumplir las instrucciones impartidas por el jefe directo | Judicial | 52128 | 84 | 99,8 % | 620,6x |
| 5955 | 178. Si la sentencia fuese de condena a dar una cantidad de dinero, el ejecutado solo | Judicial | 89450 | 213 | 99,8 % | 420,0x |
| 5956 | 179 Corte Suprema sentencia de casación en el fondo declarado inadmisible, en proceso rol 32864-2016, segunda | Judicial | 105809 | 165 | 99,8 % | 641,3x |
| 5957 | 18 Convención para combatir el cohecho a funcionarios públicos extranjeros en | Judicial | 62514 | 97 | 99,8 % | 644,5x |
| 5958 | 18 Corte de Apelaciones de Santiago, rol 676-05, del 14 de diciembre de 2005. En | Penal | 97633 | 179 | 99,8 % | 545,4x |
| 5959 | 18 El artículo 17 de la Ley 14.908, contempla lo relativo al pago de intereses desde | Familia | 97488 | 183 | 99,8 % | 532,7x |
| 5960 | 18 La Pontificia Universidad Católica de Valparaíso, Corte Suprema, Cámara de | Judicial | 30834 | 72 | 99,8 % | 428,2x |
| 5961 | 18 Medina (2016: 256) cuestiona el carácter de bien jurídico de la idea de salud | Penal | 97633 | 153 | 99,8 % | 638,1x |
| 5962 | 18 Protocolo de actuación en una visita preventiva a residencias de protección para | Judicial | 78893 | 122 | 99,8 % | 646,7x |
| 5963 | 18 Winter (2016: 201) y Castro (2021: 65 y 66) indican que la jurisprudencia ha | Penal | 97633 | 217 | 99,8 % | 449,9x |
| 5964 | 18. Si bien toma nota del contenido y estado actual del proyecto de ley | Judicial | 78893 | 171 | 99,8 % | 461,4x |
| 5965 | 18. Toda sala que dicte una resolución será responsable de los efectos que esta | Penal | 57066 | 120 | 99,8 % | 475,6x |
| 5966 | 18.010. En estas, se presume el pago de intereses, siendo necesario pacto expreso | Civil | 118177 | 196 | 99,8 % | 602,9x |
| 5967 | 1804. Como expresa Riccardo Ferrante, “La ley mediante la cual se promulgó el Código | Civil | 90056 | 174 | 99,8 % | 517,6x |
| 5968 | 1831. En él, se indicaba que la codificación no podía ser una compilación simplificada y | Civil | 90056 | 172 | 99,8 % | 523,6x |
| 5969 | 1833. Infante tenía muy buenos reflejos, y lo demostró con su agilidad característica | Civil | 90056 | 176 | 99,8 % | 511,7x |
| 5970 | 19 Artículo 44 de la Ley de Menores: «La asignación familiar que corresponda a | Familia | 97488 | 180 | 99,8 % | 541,6x |
| 5971 | 19 Considerando segundo: «Que en relación a ello ha de tenerse presente que el | Familia | 97488 | 191 | 99,8 % | 510,4x |
| 5972 | 19 El artículo 408 del Código del Trabajo establece lo siguiente: «Presentación | Laboral | 98828 | 180 | 99,8 % | 549,0x |
| 5973 | 19 En el sentido de establecer a la Ley 20.584 como integrante del contenido de | Judicial | 87950 | 133 | 99,8 % | 661,3x |
| 5974 | 19 Nº 3 CPR]”. EVANS (2004); p. 144. Natalia Muñoz, a propósito de las actuaciones de las superintendencias | Penal | 57066 | 137 | 99,8 % | 416,5x |
| 5975 | 19 Oxman (2017: 72 y 73) señala que dada la naturaleza de esta figura no puede | Penal | 97633 | 182 | 99,8 % | 536,4x |
| 5976 | 19 Refiriéndose a la orden judicial de detención, Salas (2009: 383), defiende que | Judicial | 144656 | 221 | 99,8 % | 654,6x |
| 5977 | 19 Según consta en sentencias pronunciadas por el Tribunal Constitucional en | Laboral | 74025 | 162 | 99,8 % | 456,9x |
| 5978 | 19 Véase, sentencia de la Corte de Apelaciones de Santiago, rol 4.491-2013, 13 de | Familia | 97488 | 227 | 99,8 % | 429,5x |
| 5979 | 19. El Comité insta al Estado parte a revisar y enmendar su legislación | Judicial | 78893 | 127 | 99,8 % | 621,2x |
| 5980 | 19. Establecer indicadores de gestión de los despachos judiciales e | Judicial | 54457 | 88 | 99,8 % | 618,8x |
| 5981 | 19.946. El art. 51, Nº 9, establece: “El procedimiento señalado en este | Civil | 96458 | 179 | 99,8 % | 538,9x |
| 5982 | 191. A la luz del artículo 19 de la Convención Americana la Corte debe | Judicial | 78893 | 175 | 99,8 % | 450,8x |
| 5983 | 194. Tanto la Convención Americana como la Convención sobre | Penal | 72395 | 109 | 99,8 % | 664,2x |
| 5984 | 195. La Convención sobre los Derechos del Niño contiene diversas | Penal | 72395 | 124 | 99,8 % | 583,8x |
| 5985 | 1966. Sin embargo, en su art. 6º transitorio, se dispuso que todo despido que | General | 125500 | 189 | 99,8 % | 664,0x |
| 5986 | 1995. Si bien el texto contemplaba la mayoría de las materias reguladas | Penal | 97633 | 169 | 99,8 % | 577,7x |
| 5987 | 1998. Ambos procedimientos de adopción se realizaron ante el mismo | Judicial | 92792 | 163 | 99,8 % | 569,3x |
| 5988 | 2 Art. 40.4. Se dispondrán de diversas medidas, tales como el cuidado, las órdenes | Penal | 86906 | 162 | 99,8 % | 536,5x |
| 5989 | 2 Artículo 113: «La ejecución de las resoluciones corresponde a los tribunales que | Judicial | 89450 | 171 | 99,8 % | 523,1x |
| 5990 | 2 CRC, Observación General Número 5 de 2003, Medidas generales de aplicación | Constitucional | 44292 | 68 | 99,8 % | 651,4x |
| 5991 | 2 Caso de la Masacre de Pueblo Bello versus Colombia, Sentencia del 31 de enero de | Penal | 51155 | 105 | 99,8 % | 487,2x |
| 5992 | 2 Corte Suprema, rol 4.949-15, del 4 de junio de 2015. Las razones entregadas en | Penal | 97633 | 176 | 99,8 % | 554,7x |
| 5993 | 2 El carácter progresivo del impuesto se desprendía del artículo 3 del proyecto de | Judicial | 62888 | 145 | 99,8 % | 433,7x |
| 5994 | 2 Ley 18.216 letra a) Prohibición de acudir a determinados lugares; letra b) Prohi- | Penal | 51155 | 101 | 99,8 % | 506,5x |
| 5995 | 2.    CONTADOR ROSALES, N. y PALACIOS VERGA-                     Parlamento Europeo, al Comité Económico y | Judicial | 64632 | 117 | 99,8 % | 552,4x |
| 5996 | 2.   Refiérase a la relación entre los principios de juridicidad, control y responsabilidad como | Judicial | 105809 | 159 | 99,8 % | 665,5x |
| 5997 | 2. A los efectos de garantizar y promover los derechos enunciados | Penal | 72395 | 120 | 99,8 % | 603,3x |
| 5998 | 2. Acaba de cometerlo (el policía presenció la comisión del ilícito o | Penal | 51155 | 117 | 99,8 % | 437,2x |
| 5999 | 2. Adolescente: Todo ser humano entre los catorce años cumplidos y | Judicial | 53521 | 126 | 99,8 % | 424,8x |
| 6000 | 2. Asegurar la puntualidad en el inicio de las audiencias. Se estima | Judicial | 53521 | 114 | 99,8 % | 469,5x |
| 6001 | 2. Atención de público | Penal | 57066 | 89 | 99,8 % | 641,2x |
| 6002 | 2. Atención integral a la mujer víctima: Está constituida por todas las | Judicial | 53521 | 118 | 99,8 % | 453,6x |
| 6003 | 2. Atender satisfactoriamente los requerimientos de información | Judicial | 52128 | 98 | 99,8 % | 531,9x |
| 6004 | 2. Atender y satisfacer los requerimientos de información y atención | Judicial | 52128 | 102 | 99,8 % | 511,1x |
| 6005 | 2. Constitución de derechos de usufructo, uso o habitación, respecto | Familia | 97488 | 167 | 99,8 % | 583,8x |
| 6006 | 2. Coser documentos y recursos correspondientes a la causa y realizar | Judicial | 44331 | 80 | 99,8 % | 554,1x |
| 6007 | 2. Cuando la audiencia del juicio oral hubiere tenido lugar en ausen- | Procesal | 66012 | 126 | 99,8 % | 523,9x |
| 6008 | 2. De sus funciones | Penal | 57066 | 124 | 99,8 % | 460,2x |
| 6009 | 2. Demanda civil que tenga como objeto una indemnización de perjuicios deducida | Civil | 96458 | 157 | 99,8 % | 614,4x |
| 6010 | 2. Deportación: Acto jurídico administrativo dictado por la autoridad | Judicial | 53521 | 93 | 99,8 % | 575,5x |
| 6011 | 2. Derecho a ser escuchado en forma directa. La Convención de los | Penal | 86906 | 157 | 99,8 % | 553,5x |
| 6012 | 2. Dichas autoridades tomarán su decisión en las mismas condiciones | Judicial | 78893 | 128 | 99,8 % | 616,4x |
| 6013 | 2. El Comité considera que el plazo de 24 horas, contado desde el mo- | Judicial | 78893 | 153 | 99,8 % | 515,6x |
| 6014 | 2. El punto de partida: la Reforma Procesal Penal | Procesal | 96699 | 153 | 99,8 % | 632,0x |
| 6015 | 2. En caso de haberse realizado el examen de ADN y que su resultado | Familia | 65085 | 124 | 99,8 % | 524,9x |
| 6016 | 2. En el caso de las medidas cautelares, podrán llevarse a efecto aún | Judicial | 89450 | 167 | 99,8 % | 535,6x |
| 6017 | 2. En nuestro Código Civil, el artículo 227 establece: «En las materias | Familia | 97488 | 171 | 99,8 % | 570,1x |
| 6018 | 2. Establecer las presunciones de voluntad administrativas; otorgar | Judicial | 105809 | 163 | 99,8 % | 649,1x |
| 6019 | 2. Fase de reclamo ante el Consejo para la Transparencia: con el | Administrativo | 89720 | 139 | 99,8 % | 645,5x |
| 6020 | 2. Formación de terna para la designación de juez (a) interino (a) del Tribunal de Juicio | Judicial | 54457 | 105 | 99,8 % | 518,6x |
| 6021 | 2. Gestión de personas: fortalecer las capacidades de adaptación del | Judicial | 44331 | 100 | 99,8 % | 443,3x |
| 6022 | 2. Haber sido realmente autorizados por las personas y de la manera que en los | General | 125500 | 193 | 99,8 % | 650,3x |
| 6023 | 2. Imparcialidad: actuar con ecuanimidad, objetividad, igualdad y no | Judicial | 44331 | 68 | 99,8 % | 651,9x |
| 6024 | 2. Imposibilidad de notificar en forma personal: Por no ser habida la | Judicial | 89450 | 157 | 99,8 % | 569,7x |
| 6025 | 2. Ingresar las órdenes del día al libro de Carabineros, lo que implica | Judicial | 52128 | 97 | 99,8 % | 537,4x |
| 6026 | 2. La creación de identidades legales o la división de la empresa u | Laboral | 74025 | 140 | 99,8 % | 528,8x |
| 6027 | 2. Las órdenes de citación a testigos o inculpados; las que se den | Judicial | 52128 | 119 | 99,8 % | 438,1x |
| 6028 | 2. Ley 17.344, que Autoriza Cambio de Nombre y Apellidos: El artí- | Judicial | 89450 | 161 | 99,8 % | 555,6x |
| 6029 | 2. Los acreedores de las partes: ajenos a la relación jurídica, están por su parte los | Civil | 110175 | 169 | 99,8 % | 651,9x |
| 6030 | 2. Los que acometen o resisten con violencia, emplean fuerza o intimi- | Judicial | 62514 | 111 | 99,8 % | 563,2x |
| 6031 | 2. Nada de lo dispuesto en el presente artículo o en el artículo 28 | Penal | 72395 | 118 | 99,8 % | 613,5x |
| 6032 | 2. Por otra parte, el respeto a esta ley creada por la voluntad de los interesados se impone a | Civil | 110175 | 206 | 99,8 % | 534,8x |
| 6033 | 2. Procedimiento para la aplicación judicial de medidas de protec- | Familia | 97488 | 166 | 99,8 % | 587,3x |
| 6034 | 2. Proponer al juez presidente la designación de los empleados | Judicial | 52128 | 81 | 99,8 % | 643,6x |
| 6035 | 2. Pueblos indígenas: Personas que tienen preexistencia y descienden | Judicial | 53521 | 98 | 99,8 % | 546,1x |
| 6036 | 2. Que, pues bien, la regla en comento, corresponde a una sanción | Familia | 65085 | 120 | 99,8 % | 542,4x |
| 6037 | 2. Recibir los informes de los relatores de sala una vez que salen de | Judicial | 44331 | 80 | 99,8 % | 554,1x |
| 6038 | 2. Recibir, registrar, archivar y distribuir la correspondencia que | Judicial | 52128 | 96 | 99,8 % | 543,0x |
| 6039 | 2. Representar judicial y extrajudicialmente a los trabajadores y las | Laboral | 74025 | 140 | 99,8 % | 528,8x |
| 6040 | 2. Respecto de la violencia de género que pueden experimentar las | Judicial | 53521 | 122 | 99,8 % | 438,7x |
| 6041 | 2. Riesgo criminógeno de la reacción penal formal frente a las primeras | Penal | 86906 | 150 | 99,8 % | 579,4x |
| 6042 | 2. Rol Nº 26-2020. Acta de visita practicada por la ministro suplente señora Carmen | Judicial | 54457 | 98 | 99,8 % | 555,7x |
| 6043 | 2. Sacar fotocopias para los registros respectivos y para adjuntar | Judicial | 52128 | 79 | 99,8 % | 659,8x |
| 6044 | 2. Se establece para un año determinado, por ejemplo 2021, las | Judicial | 52128 | 87 | 99,8 % | 599,2x |
| 6045 | 2. Si fallece el deudor: la obligación condicional que proviene de un testamento o | Civil | 118177 | 215 | 99,8 % | 549,7x |
| 6046 | 2. Stock de causas en tramitación. En este aspecto, el indicador va | Judicial | 52128 | 91 | 99,8 % | 572,8x |
| 6047 | 2. Tener en cuenta los diversos tipos de discapacidad existente, así | Judicial | 53521 | 88 | 99,8 % | 608,2x |
| 6048 | 2. Tesis favorable a estimar que trabajadores remunerados a | Judicial | 79146 | 130 | 99,8 % | 608,8x |
| 6049 | 2. Tipos de discapacidad: Existen diversos tipos, que dependen de la | Judicial | 53521 | 117 | 99,8 % | 457,4x |
| 6050 | 2. Todo Estado parte que subordine la extradición a la existencia de | Judicial | 78893 | 120 | 99,8 % | 657,4x |
| 6051 | 2.1.1 Investigación | Penal | 57066 | 106 | 99,8 % | 538,4x |
| 6052 | 2.1.1.2 Reglamentación del Acta Nº 71-2016, relativa | Judicial | 83934 | 153 | 99,8 % | 548,6x |
| 6053 | 2.1.2 Formalización | Penal | 57066 | 106 | 99,8 % | 538,4x |
| 6054 | 2.1.6 Ayudante de Servicios | Judicial | 39447 | 93 | 99,8 % | 424,2x |
| 6055 | 2.10     Dirección de la audiencia, retardo | Judicial | 54457 | 104 | 99,8 % | 523,6x |
| 6056 | 2.12      De la sala | Judicial | 54457 | 83 | 99,8 % | 656,1x |
| 6057 | 2.13      Ley de Tramitación | Judicial | 54457 | 88 | 99,8 % | 618,8x |
| 6058 | 2.13. Cosas registrables y no registrables | Civil | 42954 | 101 | 99,8 % | 425,3x |
| 6059 | 2.17      Las facultades | Judicial | 54457 | 93 | 99,8 % | 585,6x |
| 6060 | 2.2. Bienes muebles e inmuebles | Civil | 42954 | 88 | 99,8 % | 488,1x |
| 6061 | 2.2. El principio de la unidad del patrimonio. 2.3. El principio de la igualdad. 2.4. El | Civil | 92843 | 188 | 99,8 % | 493,8x |
| 6062 | 2.2.1 Aspectos comunes y diferencias | Judicial | 52128 | 104 | 99,8 % | 501,2x |
| 6063 | 2.2.1 Fase intermedia | Penal | 57066 | 113 | 99,8 % | 505,0x |
| 6064 | 2.2.2 Acusación | Penal | 57066 | 105 | 99,8 % | 543,5x |
| 6065 | 2.2.2 Suministro de mano de obra | Laboral | 100583 | 187 | 99,8 % | 537,9x |
| 6066 | 2.2.3 Auto de apertura | Penal | 57066 | 124 | 99,8 % | 460,2x |
| 6067 | 2.3     Funcionamiento ordinario y extraordinario | Judicial | 54457 | 84 | 99,8 % | 648,3x |
| 6068 | 2.3.1 Remisión al tribunal oral | Penal | 57066 | 110 | 99,8 % | 518,8x |
| 6069 | 2.3.3.2. Acta 98 -2009, sobre Gestión y Administración de los Juzgados de Familia | Procesal | 96699 | 187 | 99,8 % | 517,1x |
| 6070 | 2.3.4 Ejecución | Penal | 57066 | 98 | 99,8 % | 582,3x |
| 6071 | 2.4   Estructura | Judicial | 64632 | 101 | 99,8 % | 639,9x |
| 6072 | 2.4. Restituciones: casos en que el legitimario puede exigir un saldo o puede estar | Civil | 23185 | 54 | 99,8 % | 429,4x |
| 6073 | 2.4.1 Ingreso de recursos en las Cortes de Apelaciones | Judicial | 44331 | 102 | 99,8 % | 434,6x |
| 6074 | 2.4.2 Presunción de paternidad | Familia | 65085 | 130 | 99,8 % | 500,7x |
| 6075 | 2.5 Situaciones que pueden presentarse en el pago de las legítimas, según | Civil | 23185 | 49 | 99,8 % | 473,2x |
| 6076 | 2.5. Cosas fungibles y no fungibles | Civil | 42954 | 75 | 99,8 % | 572,7x |
| 6077 | 2.5. Derecho a la reunificación familiar | Constitucional | 115835 | 204 | 99,8 % | 567,8x |
| 6078 | 2.5.1 Definiciones | Judicial | 64632 | 132 | 99,8 % | 489,6x |
| 6079 | 2.5.1. La Ley 20.886 sobre Tramitación Electrónica | Procesal | 96699 | 156 | 99,8 % | 619,9x |
| 6080 | 2.5.2 Competencia | Judicial | 64632 | 111 | 99,8 % | 582,3x |
| 6081 | 2.5.2 Determinación judicial | Familia | 65192 | 135 | 99,8 % | 482,9x |
| 6082 | 2.5.3 Facultad oficiosa del juez en el | Familia | 65192 | 123 | 99,8 % | 530,0x |
| 6083 | 2.5.3 Recursos | Judicial | 64632 | 113 | 99,8 % | 572,0x |
| 6084 | 2.5.4 Incidentes | Judicial | 64632 | 97 | 99,8 % | 666,3x |
| 6085 | 2.5.4 Incumplimiento del régimen | Familia | 65192 | 119 | 99,8 % | 547,8x |
| 6086 | 2.5.4.1 Incumplimiento del padre titular del régimen | Familia | 65192 | 122 | 99,8 % | 534,4x |
| 6087 | 2.5.5 Notificaciones | Judicial | 64632 | 97 | 99,8 % | 666,3x |
| 6088 | 2.5.7 Exigibilidad | Judicial | 64632 | 102 | 99,8 % | 633,6x |
| 6089 | 2.6.1 Derecho del niño a ser oído | Familia | 65085 | 118 | 99,8 % | 551,6x |
| 6090 | 2.6.1 Veedor | Judicial | 64632 | 106 | 99,8 % | 609,7x |
| 6091 | 2.6.1.1 Aplicación supletoria del Código de Procedimiento | Laboral | 71986 | 122 | 99,8 % | 590,0x |
| 6092 | 2.6.1.3 Reglas comunes a los procedimientos laborales | Laboral | 71986 | 141 | 99,8 % | 510,5x |
| 6093 | 2.6.2 Autonomía progresiva | Familia | 65085 | 140 | 99,8 % | 464,9x |
| 6094 | 2.6.2 Liquidador | Judicial | 64632 | 98 | 99,8 % | 659,5x |
| 6095 | 2.7     Las Cortes de Apelaciones pueden conocer | Judicial | 54457 | 114 | 99,8 % | 477,7x |
| 6096 | 2.7.5 Procedimiento ejecutivo para el | Laboral | 71986 | 117 | 99,8 % | 615,3x |
| 6097 | 2.8     Formación de las tablas | Judicial | 54457 | 101 | 99,8 % | 539,2x |
| 6098 | 2.8.1 El inicio del procedimiento | Laboral | 71986 | 128 | 99,8 % | 562,4x |
| 6099 | 2.8.2 Análisis de admisibilidad y | Laboral | 71986 | 136 | 99,8 % | 529,3x |
| 6100 | 2.8.3 La contestación a la demanda | Laboral | 71986 | 120 | 99,8 % | 599,9x |
| 6101 | 2.8.8 Paso a cumplimiento (art. 462 del CT) | Laboral | 71986 | 120 | 99,8 % | 599,9x |
| 6102 | 2.9     Integración de las | Judicial | 54457 | 87 | 99,8 % | 625,9x |
| 6103 | 2.9.4 Resolución del juez acerca de la | Laboral | 71986 | 118 | 99,8 % | 610,1x |
| 6104 | 20 Alvarado Velloso (2009: 385) en lo concerniente a la función de garantía de las | Procesal | 86112 | 174 | 99,8 % | 494,9x |
| 6105 | 20 Artículo 345: «Los instrumentos públicos otorgados fuera de Chile deberán | Judicial | 89450 | 172 | 99,8 % | 520,1x |
| 6106 | 20 Así entre otros, «El nuevo Derecho penal de adolescentes y la necesaria revisión | Penal | 86906 | 166 | 99,8 % | 523,5x |
| 6107 | 20 El artículo 116 del Código Procesal Civil italiano de 1940, sin perjuicios de otras | Procesal | 86112 | 180 | 99,8 % | 478,4x |
| 6108 | 20 El inciso séptimo del citado artículo 1 de la Ley 18.216 establece que «para los | Penal | 97633 | 183 | 99,8 % | 533,5x |
| 6109 | 20 Esta posición es planteada por Nance (Vásquez 2015: 165 y ss.). Con todo, se le | Procesal | 86112 | 143 | 99,8 % | 602,2x |
| 6110 | 20 Requisito demandado por la jurisprudencia española, como lo expone Frieyro | Penal | 97633 | 174 | 99,8 % | 561,1x |
| 6111 | 20. Que de otro lado, la demandante reconvencional, Forestal C. apeló de la sentencia, en | Judicial | 79146 | 122 | 99,8 % | 648,7x |
| 6112 | 20. Si bien toma nota de las disposiciones del Código Procesal Penal | Judicial | 78893 | 162 | 99,8 % | 487,0x |
| 6113 | 20.830. En efecto, dispone el art. 12 de este cuerpo legal: “Los acuerdos de unión civil | General | 125500 | 215 | 99,8 % | 583,7x |
| 6114 | 2017. El recurso se funda en que el recurrente, de 84 años, con cáncer de | Judicial | 87950 | 165 | 99,8 % | 533,0x |
| 6115 | 2018. Lo anterior, en consideración a las circunstancias personales | Penal | 72395 | 131 | 99,8 % | 552,6x |
| 6116 | 2020. Desestima esta causal de exclusión de responsabilidad por falta de prueba de | Penal | 97633 | 197 | 99,8 % | 495,6x |
| 6117 | 21 Artículo 345 bis: «Los instrumentos públicos otorgados en un Estado parte de la | Judicial | 89450 | 139 | 99,8 % | 643,5x |
| 6118 | 21 Comité PIDESC, Observación General 14, párrafos 31 y 32. Ello no obsta a que | Judicial | 81675 | 171 | 99,8 % | 477,6x |
| 6119 | 21 Considerando cuarto: «El padre adquirió una vivienda en donde vive con sus | Familia | 97488 | 184 | 99,8 % | 529,8x |
| 6120 | 21 Hay quienes sostienen que todo argumento puede ser reconstruido en términos | Judicial | 92792 | 166 | 99,8 % | 559,0x |
| 6121 | 21 Inciso segundo del artículo 45 de la Ley de Menores: «Si los menores que se | Familia | 97488 | 188 | 99,8 % | 518,6x |
| 6122 | 21 Sentencia de la Corte Suprema, rol 4.523-2019, 3 de febrero 2020, considerando | Familia | 97488 | 178 | 99,8 % | 547,7x |
| 6123 | 21. El Estado parte debe adoptar medidas efectivas que aseguren en la | Judicial | 78893 | 156 | 99,8 % | 505,7x |
| 6124 | 21.515. De igual forma, si se modificare la Ley de Matrimonio Civil y se dispusiere que | General | 125500 | 213 | 99,8 % | 589,2x |
| 6125 | 22 Artículo 347: «Los instrumentos extendidos en lengua extranjera se mandarán | Judicial | 89450 | 157 | 99,8 % | 569,7x |
| 6126 | 22 Chile ha ratificado todos los tratados internacionales sustanciales suscritos y | Judicial | 60665 | 93 | 99,8 % | 652,3x |
| 6127 | 22 Conforme a los principios que informan la materia, en especial los consagrados | Familia | 97488 | 179 | 99,8 % | 544,6x |
| 6128 | 22 En efecto, el inciso quinto del artículo 14 de la Ley 20.584 introducido por la | Judicial | 87950 | 176 | 99,8 % | 499,7x |
| 6129 | 22 Esta forma de apreciar la justicia restaurativa no es unánime. Para algunos la | Penal | 86906 | 139 | 99,8 % | 625,2x |
| 6130 | 22 Juzgado de Letras del Trabajo de Punta Arenas, RIT T-63-2019, considerando | Laboral | 53374 | 85 | 99,8 % | 627,9x |
| 6131 | 22 Lema (2019: 484) explica que no debe excluirse la «independencia» a que alude | Penal | 97633 | 172 | 99,8 % | 567,6x |
| 6132 | 22 Para determinar este valor se utilizó la Encuesta Nacional del Uso de Tiempo | Laboral | 98828 | 187 | 99,8 % | 528,5x |
| 6133 | 22 Reza dicha norma: «La prueba se apreciará en la forma ordinaria. Pero podrá el | Procesal | 86112 | 137 | 99,8 % | 628,6x |
| 6134 | 22. El Comité expresa su preocupación por los numerosos episodios de | Judicial | 78893 | 162 | 99,8 % | 487,0x |
| 6135 | 22. Que en el presente caso, no se puede pasar por alto que el actor J.P.J., al interponer la | Judicial | 79146 | 126 | 99,8 % | 628,1x |
| 6136 | 221. Sin embargo, estimamos que en estas hipótesis la notificación | Procesal | 66012 | 139 | 99,8 % | 474,9x |
| 6137 | 23 Considerando décimo tercero: «Que, si bien el niño ha manifestado como ya se | Familia | 97488 | 148 | 99,8 % | 658,7x |
| 6138 | 23 La nueva disposición, en tal sentido, señala: «Los delitos de secuestro, sea en | Judicial | 62514 | 132 | 99,8 % | 473,6x |
| 6139 | 23 Por cierto, no sería aplicable el número 1 del citado artículo 413 del Código de | Procesal | 86112 | 213 | 99,8 % | 404,3x |
| 6140 | 23 Recientemente (2020) fue aprobada por la Cámara de Diputados el proyecto de | Judicial | 60665 | 94 | 99,8 % | 645,4x |
| 6141 | 23. DENYER, Roderick (1988): Children and Personal              los autores en YAKSIC, Nicolás y LEIVA, Car- | Penal | 72395 | 115 | 99,8 % | 629,5x |
| 6142 | 23. Que es un hecho del pleito, que la actora no se ha atribuido dominio ni derechos sobre la | Judicial | 79146 | 132 | 99,8 % | 599,6x |
| 6143 | 2317. En otras palabras, esta norma se referiría al dolo como maquinación fraudulenta | Civil | 120848 | 188 | 99,8 % | 642,8x |
| 6144 | 24 Artículo 19 Ley 19.968: «Representación: En todos los asuntos de competencia | Familia | 97488 | 197 | 99,8 % | 494,9x |
| 6145 | 24 La única oportunidad para presentar objeciones a la liquidación, en los casos | Judicial | 89450 | 166 | 99,8 % | 538,9x |
| 6146 | 24 Rey (1999: 89) no califica como acto de tráfico aquella adquisición destinada | Penal | 97633 | 191 | 99,8 % | 511,2x |
| 6147 | 24. Otrosí: Petición adicional a la solicitud principal | Judicial | 39447 | 88 | 99,8 % | 448,3x |
| 6148 | 24. Que en lo tocante al segundo aspecto de la apelación del demandante reconvencional, en | Judicial | 79146 | 143 | 99,8 % | 553,5x |
| 6149 | 2468. Un acto causa perjuicio a los acreedores, en este contexto, cuando ocasiona la | Civil | 120848 | 205 | 99,8 % | 589,5x |
| 6150 | 2469. En efecto, el Art. 2465 permite efectuar la ejecución de todos los bienes del | Civil | 120848 | 200 | 99,8 % | 604,2x |
| 6151 | 25 Considerando sexto: «Que en relación a ello ha de decirse, en primer lugar, que | Familia | 97488 | 148 | 99,8 % | 658,7x |
| 6152 | 25 Se ha resuelto que «no puede aceptarse que la notificación de una sentencia | Judicial | 89450 | 146 | 99,8 % | 612,7x |
| 6153 | 25 Ídem, detalla sobre la problemática del sistema de salud, indicando que, en el | Judicial | 81675 | 189 | 99,8 % | 432,1x |
| 6154 | 2509. En este orden de ideas se ha fallado que ‘la referencia del art. 2524 a ‘ciertos | Civil | 96458 | 202 | 99,8 % | 477,5x |
| 6155 | 253   Sobre acoso sexual, revisar LIZAMA y UGARTE (2005), GAMONAL C., Sergio (2007), El daño moral en el con- | Laboral | 113458 | 180 | 99,8 % | 630,3x |
| 6156 | 26 Corte IDH, Opinión consultiva… | Laboral | 53374 | 84 | 99,8 % | 635,4x |
| 6157 | 26 Droga es una sustancia no alimenticia empleada para producir un efecto en la | Penal | 97633 | 171 | 99,8 % | 571,0x |
| 6158 | 26 Tales puntos de inflexión sobre el Convenio motivaron el pronunciamiento del | Judicial | 60665 | 123 | 99,8 % | 493,2x |
| 6159 | 264. Ahora bien, es necesario resaltar que el proceso penal por casos | Judicial | 87237 | 133 | 99,8 % | 655,9x |
| 6160 | 27 Boletín 10.793-18, «Proyecto de ley que modifica el Código Penal con el objeto | Judicial | 89450 | 141 | 99,8 % | 634,4x |
| 6161 | 27 Considerando séptimo: «Puede reaccionar con impulsividad ante situaciones | Familia | 97488 | 149 | 99,8 % | 654,3x |
| 6162 | 27 El denominado «consumo compasivo» consiste en la entrega altruista y sin | Penal | 97633 | 157 | 99,8 % | 621,9x |
| 6163 | 27 Se citan como ejemplos habituales a las personas expertas que opinan sobre la | Procesal | 86112 | 133 | 99,8 % | 647,5x |
| 6164 | 27 Se ha resuelto que «el artículo 50 del Código de Procedimiento Civil establece | Judicial | 89450 | 165 | 99,8 % | 542,1x |
| 6165 | 27 Sentencia de la Corte de Apelaciones de Santiago, rol amparo 393-2023, 27 de | Familia | 97488 | 198 | 99,8 % | 492,4x |
| 6166 | 27 Si el delito de tráfico del artículo 3 recae sobre sustancias o drogas capaces de | Penal | 97633 | 180 | 99,8 % | 542,4x |
| 6167 | 27 Su artículo 2: «La consulta es un deber de los órganos de la Administración del | Judicial | 60665 | 144 | 99,8 % | 421,3x |
| 6168 | 27 Ídem, un estudio de la OCDE posiciona a Chile como el cuarto país del mundo | Judicial | 81675 | 152 | 99,8 % | 537,3x |
| 6169 | 272 cc | Familia | 65085 | 122 | 99,8 % | 533,5x |
| 6170 | 28 Artículo 416: «Existirá un Juzgado de Cobranza Laboral y Previsional, con | Judicial | 89450 | 179 | 99,8 % | 499,7x |
| 6171 | 28 Corte Suprema, rol 5185-21 del 22 de junio de 2021. Al conocer un recurso | Laboral | 98828 | 224 | 99,8 % | 441,2x |
| 6172 | 28 El Fondo para el Desarrollo de los Pueblos Indígenas de América Latina y El | Judicial | 60665 | 150 | 99,8 % | 404,4x |
| 6173 | 28 Según Tapia (2007), en nuestro país la codificación decimonónica reconoció | Familia | 123490 | 189 | 99,8 % | 653,4x |
| 6174 | 28 Sentencia de la Corte Suprema, rol 91.731-2021, 1 de febrero de 2023, señala en | Familia | 97488 | 198 | 99,8 % | 492,4x |
| 6175 | 28. Llevar el control del rendimiento y gestión institucional de la | Judicial | 54457 | 84 | 99,8 % | 648,3x |
| 6176 | 28. Procedimiento simplificado: Tipo especial de | Judicial | 39447 | 78 | 99,8 % | 505,7x |
| 6177 | 29 Aunque aquí también se incluye dentro de la obligación de respetar aspectos | Judicial | 81675 | 163 | 99,8 % | 501,1x |
| 6178 | 29. Inmediatamente después de la acción policial del 24 de agosto de | Penal | 51155 | 110 | 99,8 % | 465,0x |
| 6179 | 3 Así lo establece el inciso quinto del artículo 229 del Código Civil: «Sea que se | Familia | 97488 | 178 | 99,8 % | 547,7x |
| 6180 | 3 Como señala el informe, es menos frecuente el caso de profesiones u oficios que | Judicial | 30834 | 74 | 99,8 % | 416,7x |
| 6181 | 3 Corte Interamericana de Derechos Humanos. Caso Apitz Barbera y otros con | Judicial | 42513 | 71 | 99,8 % | 598,8x |
| 6182 | 3 El artículo 4 de la Ley 21.302 contempla veinte principios rectores. Un examen de | Constitucional | 46896 | 72 | 99,8 % | 651,3x |
| 6183 | 3 Entró en vigencia el 2 de septiembre de 1990. A enero de 2023, 196 estados la | Constitucional | 46896 | 72 | 99,8 % | 651,3x |
| 6184 | 3 Este es el principio rector con respecto a los derechos fundamentales de cada | Familia | 97488 | 201 | 99,8 % | 485,0x |
| 6185 | 3 La doctrina del Tribunal Supremo español considera que el control de la medida | Penal | 97633 | 184 | 99,8 % | 530,6x |
| 6186 | 3 Las críticas al ideal de rehabilitación provinieron tanto desde la criminología | Penal | 86906 | 157 | 99,8 % | 553,5x |
| 6187 | 3 Para Hernández (2007: 14), la agrupación o reunión «no cuenta con el grado de | Penal | 97633 | 171 | 99,8 % | 571,0x |
| 6188 | 3 Recordar que es una VIDEO LLAMADA. Si | Judicial | 53521 | 105 | 99,8 % | 509,7x |
| 6189 | 3 Se ha resuelto que «es nula la notificación que no se ajusta a las notificaciones | Judicial | 89450 | 206 | 99,8 % | 434,2x |
| 6190 | 3 Se recuerda que las torturas de sujetos privados de libertad constituyen una | Penal | 51155 | 96 | 99,8 % | 532,9x |
| 6191 | 3 Sentencia de la Corte Suprema, rol 15.889-19, 3 de junio de 2020: «Sexto: Que el | Familia | 123490 | 193 | 99,8 % | 639,8x |
| 6192 | 3 Ya Aristóteles (2005), en su Política, advertía que la labor del juez era juzgar el | Judicial | 81675 | 179 | 99,8 % | 456,3x |
| 6193 | 3.   Filiación No Matrimonial: aquella en que no existe | Familia | 65085 | 105 | 99,8 % | 619,9x |
| 6194 | 3. Administrar la cuenta corriente del tribunal, lo que implica | Judicial | 52128 | 96 | 99,8 % | 543,0x |
| 6195 | 3. Antes del plazo de dos años una de las empresas comprendidas en | Laboral | 74025 | 166 | 99,8 % | 445,9x |
| 6196 | 3. Asegurar que se estén implementando los ajustes razonables de | Judicial | 53521 | 93 | 99,8 % | 575,5x |
| 6197 | 3. Autorizar la celebración de contratos y convenios de cooperación | Judicial | 54457 | 113 | 99,8 % | 481,9x |
| 6198 | 3. Autorizar la salida del país de los hijos menores de edad sin nece- | Familia | 97488 | 161 | 99,8 % | 605,5x |
| 6199 | 3. Aviso del ministro de fe: El ministro de fe dará aviso de esta notifi- | Judicial | 89450 | 166 | 99,8 % | 538,9x |
| 6200 | 3. Como un criteri de c nducta, c nf rme al cual deben ser cumplidas las | Civil | 110175 | 189 | 99,8 % | 582,9x |
| 6201 | 3. Condiciones de cumplimiento de la prisión preventiva. Las garantías | Penal | 86906 | 154 | 99,8 % | 564,3x |
| 6202 | 3. Cuales serían los resultados esperados del programa al que le daría prioridad | Judicial | 29920 | 53 | 99,8 % | 564,5x |
| 6203 | 3. Cuando la víctima sea especialmente vulnerable, por razón de su | Laboral | 53374 | 113 | 99,8 % | 472,3x |
| 6204 | 3. Dar conocimiento a cualquiera persona que lo solicite de los | Judicial | 52128 | 97 | 99,8 % | 537,4x |
| 6205 | 3. Demanda civil que tenga como objeto una indemnización de perjuicios deducida por | Civil | 96458 | 178 | 99,8 % | 541,9x |
| 6206 | 3. Derechos extendidos | Judicial | 82507 | 148 | 99,8 % | 557,5x |
| 6207 | 3. Efectos de la ley; 4. Interpretación de la ley; 5. Definición de varias palabras de uso | Civil | 90056 | 213 | 99,8 % | 422,8x |
| 6208 | 3. Ejecutar maliciosamente actos tendientes a alterar el quórum de | Laboral | 74025 | 158 | 99,8 % | 468,5x |
| 6209 | 3. El derecho a ser oído y opinar en todos los asuntos que le afectan y a | Judicial | 53521 | 130 | 99,8 % | 411,7x |
| 6210 | 3. Entrega de los dos antecedentes anteriores en forma personal a la | Judicial | 89450 | 195 | 99,8 % | 458,7x |
| 6211 | 3. Evitar comparecencias innecesarias. Distinguir de manera correcta | Judicial | 53521 | 84 | 99,8 % | 637,2x |
| 6212 | 3. Finalmente, desde marzo del 2022, a este conjunto de normas se | Familia | 97488 | 202 | 99,8 % | 482,6x |
| 6213 | 3. Finalmente, hay quienes aceptan la validez de estas cláusulas de no | Judicial | 92792 | 167 | 99,8 % | 555,6x |
| 6214 | 3. Finalmente, y en lo relativo a los comités de ética, el usuario tiene | Judicial | 87950 | 211 | 99,8 % | 416,8x |
| 6215 | 3. Formar, el último día hábil de cada semana, en conformidad a la | Judicial | 54457 | 91 | 99,8 % | 598,4x |
| 6216 | 3. Funcionarios encargados de la práctica de la notificación perso- | Judicial | 89450 | 183 | 99,8 % | 488,8x |
| 6217 | 3. La determinación acerca de si la alteración de la individualidad | Laboral | 74025 | 153 | 99,8 % | 483,8x |
| 6218 | 3. La indicación concreta de las medidas a que está obligada la parte | Laboral | 74025 | 182 | 99,8 % | 406,7x |
| 6219 | 3. La resolución que ordena recibir la causa a prueba en el juicio or- | Judicial | 89450 | 217 | 99,8 % | 412,2x |
| 6220 | 3. La sentencia de segunda instancia será notifica por el estado dia- | Judicial | 89450 | 156 | 99,8 % | 573,4x |
| 6221 | 3. Las que se hagan a terceros que no sean partes en el juicio o a quie- | Judicial | 89450 | 188 | 99,8 % | 475,8x |
| 6222 | 3. Ley 18.101, que Fija Normas Especiales sobre Arrendamiento de | Judicial | 89450 | 166 | 99,8 % | 538,9x |
| 6223 | 3. Maximización de la autonomía y acceso a la justicia: Considerando | Judicial | 53521 | 88 | 99,8 % | 608,2x |
| 6224 | 3. Participación entre emisor y receptor | Judicial | 53521 | 83 | 99,8 % | 644,8x |
| 6225 | 3. Personas con interés legítimo en la consulta: el deudor de alimentos, su alimentario | Familia | 81198 | 176 | 99,8 % | 461,4x |
| 6226 | 3. Pierre Bourdieu | Judicial | 87237 | 132 | 99,8 % | 660,9x |
| 6227 | 3. Que el tribunal debe apreciar los antecedentes con conocimiento de | Judicial | 89450 | 157 | 99,8 % | 569,7x |
| 6228 | 3. Que, desde dicha perspectiva, la interpretación que se efectúe de | Familia | 65085 | 126 | 99,8 % | 516,5x |
| 6229 | 3. Ratificar las firmas de las partes y sus mandatarios o delegados | Judicial | 52128 | 104 | 99,8 % | 501,2x |
| 6230 | 3. Rol Nº1046-2019. Fiscal judicial de la tercera fiscalía señora Carla Troncoso | Judicial | 54457 | 97 | 99,8 % | 561,4x |
| 6231 | 3. Régimen transitorio que impone a los tribunales la realización de | Judicial | 89450 | 183 | 99,8 % | 488,8x |
| 6232 | 3. Sustitúyese el inciso tercero por el siguiente: «Se pondrá en los | Judicial | 89450 | 145 | 99,8 % | 616,9x |
| 6233 | 3. Tratos degradantes: en los relatos se dieron a conocer hechos que | Judicial | 78893 | 176 | 99,8 % | 448,3x |
| 6234 | 3.1 Fase presustantiva. Una vez en la sala de entrevista, el en- | Penal | 72395 | 120 | 99,8 % | 603,3x |
| 6235 | 3.1.1 Determinación de la maternidad | Familia | 65085 | 117 | 99,8 % | 556,3x |
| 6236 | 3.1.1 Regulación | Penal | 57066 | 105 | 99,8 % | 543,5x |
| 6237 | 3.1.1 Unidad de Administración de Causas | Laboral | 71986 | 113 | 99,8 % | 637,0x |
| 6238 | 3.1.2 Características principales | Penal | 57066 | 87 | 99,8 % | 655,9x |
| 6239 | 3.1.2 Determinación de filiación matrimonial | Familia | 65085 | 126 | 99,8 % | 516,5x |
| 6240 | 3.1.2 Procedimiento ordinario de menor cuantía | Judicial | 52128 | 105 | 99,8 % | 496,5x |
| 6241 | 3.1.3 Determinación de la filiación no matrimonial | Familia | 65085 | 139 | 99,8 % | 468,2x |
| 6242 | 3.1.3 Procedimiento ordinario de mínima cuantía | Judicial | 52128 | 106 | 99,8 % | 491,8x |
| 6243 | 3.1.3 Solicitud de copias | Judicial | 39447 | 91 | 99,8 % | 433,5x |
| 6244 | 3.1.3 Territorio donde ejercen su actividad | Penal | 57066 | 131 | 99,8 % | 435,6x |
| 6245 | 3.1.3.1 Características del reconocimiento | Familia | 65085 | 128 | 99,8 % | 508,5x |
| 6246 | 3.1.3.3 Repudiación | Familia | 65085 | 100 | 99,8 % | 650,9x |
| 6247 | 3.1.3.4 Características de la repudiación | Familia | 65085 | 122 | 99,8 % | 533,5x |
| 6248 | 3.1.4 Competencia | Penal | 57066 | 135 | 99,8 % | 422,7x |
| 6249 | 3.1.4 Determinación en la fertilización asistida | Familia | 65085 | 122 | 99,8 % | 533,5x |
| 6250 | 3.1.4 Direcciones de entidades e instituciones | Judicial | 39447 | 81 | 99,8 % | 487,0x |
| 6251 | 3.11.2 Autorización de salida del país de | Familia | 65192 | 149 | 99,8 % | 437,5x |
| 6252 | 3.11.3 Medidas relacionadas el | Familia | 65192 | 127 | 99,8 % | 513,3x |
| 6253 | 3.12.1 Medidas precautorias | Familia | 65192 | 120 | 99,8 % | 543,3x |
| 6254 | 3.12.2 Arraigo | Familia | 65192 | 111 | 99,8 % | 587,3x |
| 6255 | 3.12.3 Hipoteca o prenda | Familia | 65192 | 127 | 99,8 % | 513,3x |
| 6256 | 3.12.4 Garantías de la devolución de impuestos | Familia | 65192 | 130 | 99,8 % | 501,5x |
| 6257 | 3.12.5 Retención de las remuneraciones | Familia | 65192 | 120 | 99,8 % | 543,3x |
| 6258 | 3.13.1 Transparencia patrimonial del deudor | Familia | 65192 | 115 | 99,8 % | 566,9x |
| 6259 | 3.13.2 Declaración de patrimonio | Familia | 65192 | 128 | 99,8 % | 509,3x |
| 6260 | 3.13.3 Acción pauliana de Alimentos | Familia | 65192 | 132 | 99,8 % | 493,9x |
| 6261 | 3.14.2 Fair play en la ejecución | Familia | 65192 | 120 | 99,8 % | 543,3x |
| 6262 | 3.14.3 Mala fe del empleador del alimentante | Familia | 65192 | 130 | 99,8 % | 501,5x |
| 6263 | 3.14.4 Mala fe de terceros | Familia | 65192 | 105 | 99,8 % | 620,9x |
| 6264 | 3.15.2 Recurso de amparo | Familia | 65192 | 140 | 99,8 % | 465,7x |
| 6265 | 3.2     Procedimiento sumario | Judicial | 52128 | 110 | 99,8 % | 473,9x |
| 6266 | 3.2.1. Casos de incorporación de la CDN como obiter dictum | Constitucional | 115835 | 198 | 99,8 % | 585,0x |
| 6267 | 3.2.1.2 Ante una demanda que cumpla con los | Judicial | 52128 | 83 | 99,8 % | 628,0x |
| 6268 | 3.2.1.3 La audiencia tiene por objeto recibir | Judicial | 52128 | 92 | 99,8 % | 566,6x |
| 6269 | 3.2.1.5 El término probatorio es de ocho días, pues | Judicial | 52128 | 110 | 99,8 % | 473,9x |
| 6270 | 3.2.2 Distribución de causas | Laboral | 71986 | 110 | 99,8 % | 654,4x |
| 6271 | 3.2.2 Orgánica de los tribunales orales | Penal | 57066 | 109 | 99,8 % | 523,5x |
| 6272 | 3.2.2.2. Circuit Moyen (Circuito mediano) | Procesal | 96699 | 152 | 99,8 % | 636,2x |
| 6273 | 3.2.4 Resolución de Reorganización | Judicial | 64632 | 124 | 99,8 % | 521,2x |
| 6274 | 3.2.5 Protección Financiera Concursal | Judicial | 64632 | 119 | 99,8 % | 543,1x |
| 6275 | 3.2.5.2 Efectos contractuales | Judicial | 64632 | 97 | 99,8 % | 666,3x |
| 6276 | 3.2.6 Financiamiento y continuación de actividades | Judicial | 64632 | 113 | 99,8 % | 572,0x |
| 6277 | 3.2.6.1 Continuidad del suministro (art. 72) | Judicial | 64632 | 109 | 99,8 % | 593,0x |
| 6278 | 3.2.6.2 Venta de activos y contratación de préstamos | Judicial | 64632 | 115 | 99,8 % | 562,0x |
| 6279 | 3.2.7 Fase de acuerdo | Judicial | 64632 | 104 | 99,8 % | 621,5x |
| 6280 | 3.2.7.3 Examen de la propuesta por parte del Veedor | Judicial | 64632 | 132 | 99,8 % | 489,6x |
| 6281 | 3.2.7.4 Conocimiento y votación de la propuesta | Judicial | 64632 | 122 | 99,8 % | 529,8x |
| 6282 | 3.2.8 Efectos del acuerdo | Judicial | 64632 | 105 | 99,8 % | 615,5x |
| 6283 | 3.2.9.2   Impugnación | Judicial | 64632 | 117 | 99,8 % | 552,4x |
| 6284 | 3.2.9.3    Nulidad | Judicial | 64632 | 132 | 99,8 % | 489,6x |
| 6285 | 3.2.9.4   Incumplimiento | Judicial | 64632 | 98 | 99,8 % | 659,5x |
| 6286 | 3.3     Aspectos importantes relacionados con el control | Judicial | 44331 | 96 | 99,8 % | 461,8x |
| 6287 | 3.3.1 Clasificación | Judicial | 52128 | 101 | 99,8 % | 516,1x |
| 6288 | 3.3.1 Consideraciones generales | Penal | 57066 | 111 | 99,8 % | 514,1x |
| 6289 | 3.3.1 Funciones reguladas por el | Judicial | 54457 | 102 | 99,8 % | 533,9x |
| 6290 | 3.3.1 Informe del Comité al Estado | Penal | 72395 | 109 | 99,8 % | 664,2x |
| 6291 | 3.3.1 Ámbito de aplicación | Judicial | 64632 | 101 | 99,8 % | 639,9x |
| 6292 | 3.3.2 Requisitos | Judicial | 64632 | 106 | 99,8 % | 609,7x |
| 6293 | 3.3.2.1 Cuaderno principal | Judicial | 52128 | 85 | 99,8 % | 613,3x |
| 6294 | 3.3.2.2 Cuaderno de apremio | Judicial | 52128 | 96 | 99,8 % | 543,0x |
| 6295 | 3.3.2.2. Reclamo de ilegalidad municipal | Judicial | 54457 | 117 | 99,8 % | 465,4x |
| 6296 | 3.3.3 Clasificación de los Alimentos | Familia | 65192 | 109 | 99,8 % | 598,1x |
| 6297 | 3.3.3 Solicitud de inicio del procedimiento | Judicial | 64632 | 101 | 99,8 % | 639,9x |
| 6298 | 3.3.3.1 Según la fuente de la obligación | Familia | 65192 | 102 | 99,8 % | 639,1x |
| 6299 | 3.3.3.2 Según el contenido de la pensión alimenticia | Familia | 65192 | 119 | 99,8 % | 547,8x |
| 6300 | 3.3.3.3 Según el momento procesal en que se decretan y | Familia | 65192 | 122 | 99,8 % | 534,4x |
| 6301 | 3.3.4 Comité de jueces | Penal | 57066 | 110 | 99,8 % | 518,8x |
| 6302 | 3.3.4 Funciones impartidas por la | Judicial | 54457 | 123 | 99,8 % | 442,7x |
| 6303 | 3.3.4 Titulares | Familia | 65192 | 109 | 99,8 % | 598,1x |
| 6304 | 3.3.4.1 Alimentos entre cónyuges | Familia | 65192 | 114 | 99,8 % | 571,9x |
| 6305 | 3.3.4.1 Resolución de admisibilidad | Judicial | 64632 | 122 | 99,8 % | 529,8x |
| 6306 | 3.3.4.2 Alimentos a los ascendientes | Familia | 65192 | 106 | 99,8 % | 615,0x |
| 6307 | 3.3.4.2 Audiencia de determinación del pasivo | Judicial | 64632 | 114 | 99,8 % | 566,9x |
| 6308 | 3.3.4.3 Alimentos a los descendientes | Familia | 65192 | 131 | 99,8 % | 497,6x |
| 6309 | 3.3.4.3 Audiencia de renegociación | Judicial | 64632 | 113 | 99,8 % | 572,0x |
| 6310 | 3.3.4.4 Audiencia de ejecución | Judicial | 64632 | 111 | 99,8 % | 582,3x |
| 6311 | 3.3.4.5 Entre los titulares del contrato de donación | Familia | 65192 | 122 | 99,8 % | 534,4x |
| 6312 | 3.3.5 El juez presidente del Comité | Penal | 57066 | 128 | 99,8 % | 445,8x |
| 6313 | 3.3.5 Impugnación de los acuerdos de | Judicial | 64632 | 104 | 99,8 % | 621,5x |
| 6314 | 3.3.5 Inicio, duración y extinción de los Alimentos | Familia | 65192 | 98 | 99,8 % | 665,2x |
| 6315 | 3.3.5.1 Inicio | Familia | 65192 | 110 | 99,8 % | 592,7x |
| 6316 | 3.3.5.1.1 Tasación de los alimentos provisorios, a propósito | Familia | 65192 | 126 | 99,8 % | 517,4x |
| 6317 | 3.3.5.2 Duración | Familia | 65192 | 128 | 99,8 % | 509,3x |
| 6318 | 3.3.5.3.2 Edad y estudios del alimentario | Familia | 65192 | 149 | 99,8 % | 437,5x |
| 6319 | 3.3.5.3.3 Injuria atroz | Familia | 65192 | 115 | 99,8 % | 566,9x |
| 6320 | 3.3.5.3.4 Dolo | Familia | 65192 | 110 | 99,8 % | 592,7x |
| 6321 | 3.3.5.3.5 Sentencia en juicio de filiación | Familia | 65192 | 132 | 99,8 % | 493,9x |
| 6322 | 3.3.6 El administrador de tribunal18 | Penal | 57066 | 137 | 99,8 % | 416,5x |
| 6323 | 3.3.6.1 Problemática | Familia | 65192 | 104 | 99,8 % | 626,8x |
| 6324 | 3.3.6.2 Intención del legislador | Familia | 65192 | 115 | 99,8 % | 566,9x |
| 6325 | 3.3.6.3 Suspensión de la prescripción | Familia | 65192 | 148 | 99,8 % | 440,5x |
| 6326 | 3.3.6.5 Inconvenientes procesales con la excepción de | Familia | 65192 | 117 | 99,8 % | 557,2x |
| 6327 | 3.3.7 Alimentos pagados después | Familia | 65192 | 131 | 99,8 % | 497,6x |
| 6328 | 3.3.8 Cargos de jefes de unidad de un tribunal oral | Penal | 57066 | 140 | 99,8 % | 407,6x |
| 6329 | 3.3.8 Determinación del quantum de la pensión | Familia | 65192 | 136 | 99,8 % | 479,4x |
| 6330 | 3.3.9 Cargos de funcionario en un tribunal oral | Penal | 57066 | 110 | 99,8 % | 518,8x |
| 6331 | 3.4     Actos judiciales no contenciosos | Judicial | 52128 | 109 | 99,8 % | 478,2x |
| 6332 | 3.4     Aspectos relevantes relacionados | Judicial | 44331 | 93 | 99,8 % | 476,7x |
| 6333 | 3.4.2 Ejecución de sentencias y devolución | Judicial | 39447 | 98 | 99,8 % | 402,5x |
| 6334 | 3.4.3 Tramitación | Judicial | 52128 | 104 | 99,8 % | 501,2x |
| 6335 | 3.5. Nacimiento, adquisición, modificación, extinción y pérdida de los derechos | General | 34424 | 78 | 99,8 % | 441,3x |
| 6336 | 3.5.1 Del procedimiento judicial para | Judicial | 93914 | 152 | 99,8 % | 617,9x |
| 6337 | 3.5.1 Proceso de inducción del personal | Judicial | 39447 | 97 | 99,8 % | 406,7x |
| 6338 | 3.5.1.7 Según el artículo 163 inciso tercero del Código del | Laboral | 100583 | 153 | 99,8 % | 657,4x |
| 6339 | 3.5.3 Inventario y custodia de especies | Judicial | 39447 | 98 | 99,8 % | 402,5x |
| 6340 | 3.5.4 Decretos económicos | Judicial | 39447 | 91 | 99,8 % | 433,5x |
| 6341 | 3.6.4 Efectos comunes | Familia | 65192 | 122 | 99,8 % | 534,4x |
| 6342 | 3.7. Ejercicio de los derechos subjetivos. Los límites en dicho ejercicio. El abuso | General | 34424 | 68 | 99,8 % | 506,2x |
| 6343 | 3.7.1 Supletoriedad | Familia | 65192 | 113 | 99,8 % | 576,9x |
| 6344 | 3.7.3 Competencia absoluta | Familia | 65192 | 127 | 99,8 % | 513,3x |
| 6345 | 3.7.5 Representación judicial | Familia | 65192 | 120 | 99,8 % | 543,3x |
| 6346 | 3.7.8 Alimentos provisorios | Familia | 65192 | 120 | 99,8 % | 543,3x |
| 6347 | 3.8.1 Características generales del | Familia | 65192 | 109 | 99,8 % | 598,1x |
| 6348 | 3.8.3 Métodos coactivos de cumplimiento | Familia | 65192 | 122 | 99,8 % | 534,4x |
| 6349 | 3.8.3.1 Método directo: arresto | Familia | 65192 | 109 | 99,8 % | 598,1x |
| 6350 | 3.8.3.1.1 Clasificación | Familia | 65192 | 113 | 99,8 % | 576,9x |
| 6351 | 3.8.3.1.2 Procedimiento de apremio | Familia | 65192 | 124 | 99,8 % | 525,7x |
| 6352 | 3.8.3.2 Método indirecto: excepción de no pago de los | Familia | 65192 | 115 | 99,8 % | 566,9x |
| 6353 | 30 Así lo destaca Carlos Pizarro (2009: 153): «En opinión de la profesora Maricruz | Familia | 97488 | 170 | 99,8 % | 573,5x |
| 6354 | 30 Corte de Apelaciones de Valparaíso, rol 135-06, del 6 de marzo de 2006, explica | Penal | 97633 | 193 | 99,8 % | 505,9x |
| 6355 | 30. Conforme a las explicaciones ofrecidas por la delegación sobre la | Judicial | 78893 | 167 | 99,8 % | 472,4x |
| 6356 | 31 Sentencia de la Corte Apelaciones de San Miguel, rol 1.069-2021, 25 de enero de | Familia | 97488 | 182 | 99,8 % | 535,6x |
| 6357 | 32 El rol de las policías en la efectividad de las órdenes de arresto resulta vital para | Familia | 97488 | 223 | 99,8 % | 437,2x |
| 6358 | 32 Que dispone: «Son derechos fundamentales de los niños: la vida, la integridad | Judicial | 81675 | 161 | 99,8 % | 507,3x |
| 6359 | 32. Si bien toma nota de los esfuerzos realizados por el Estado parte | Judicial | 78893 | 158 | 99,8 % | 499,3x |
| 6360 | 33 Considerando décimo sexto: «Que, en síntesis, el informe psicológico evacuado | Familia | 97488 | 170 | 99,8 % | 573,5x |
| 6361 | 33 La jurisprudencia ha reconocido que: «El presupuesto consistente en no haber | Familia | 123490 | 195 | 99,8 % | 633,3x |
| 6362 | 33. Si el o la solicitante de los documentos a que se refieren los artículos 32 y 33 precedentes | Familia | 81198 | 183 | 99,8 % | 443,7x |
| 6363 | 334. Con respecto a la discriminación estructural, la Corte hace notar | Judicial | 92792 | 166 | 99,8 % | 559,0x |
| 6364 | 335. Por otro lado, en relación con el artículo 1.1 de la Convención, la | Judicial | 92792 | 166 | 99,8 % | 559,0x |
| 6365 | 337. La Corte se ha pronunciado en el sentido de establecer que toda | Judicial | 92792 | 163 | 99,8 % | 569,3x |
| 6366 | 339. La Corte constata, en el presente caso, algunas características de | Judicial | 92792 | 154 | 99,8 % | 602,5x |
| 6367 | 34   La jurisprudencia de Contraloría es rigurosa a la hora de resolver la abstención de su pronunciamiento en | Judicial | 105809 | 180 | 99,8 % | 587,8x |
| 6368 | 34 En sentido similar y respecto del peligro de sobrevaloración en sede penal, el | Procesal | 86112 | 167 | 99,8 % | 515,6x |
| 6369 | 34 Lo que la ley ha pretendido estableciendo estas «modalidades de tráfico» es | Penal | 97633 | 205 | 99,8 % | 476,3x |
| 6370 | 34. Refiérase a las materias excluidas de la acción por vulneración de los derechos del | Judicial | 105809 | 162 | 99,8 % | 653,1x |
| 6371 | 340. De la prueba aportada al expediente se advierte la existencia de | Judicial | 92792 | 167 | 99,8 % | 555,6x |
| 6372 | 342. Por todo lo anterior, Brasil no demostró haber adoptado, respecto | Judicial | 92792 | 162 | 99,8 % | 572,8x |
| 6373 | 343. En razón de todo lo expuesto, el Tribunal considera que el Estado | Judicial | 92792 | 172 | 99,8 % | 539,5x |
| 6374 | 35 En especial sobre el Innocence Project, véase Duce (2017: 47-49). Valen también | Procesal | 86112 | 150 | 99,8 % | 574,1x |
| 6375 | 36. El Comité expresa su profunda preocupación ante el número de | Judicial | 78893 | 158 | 99,8 % | 499,3x |
| 6376 | 37 Artículo 30 Ley 14.908: «Retención de la devolución de impuestos a la renta. En | Familia | 97488 | 200 | 99,8 % | 487,4x |
| 6377 | 37 Así, por ejemplo, la sentencia Hartz IV del Tribunal Constitucional alemán de | Judicial | 81675 | 149 | 99,8 % | 548,2x |
| 6378 | 37 De modo semejante, sentencia Corte Suprema rol 8106-2018, de 29 de enero | Judicial | 144656 | 226 | 99,8 % | 640,1x |
| 6379 | 37 Para develar el sentido de esta regla resulta muy útil el texto original del artículo | Familia | 123490 | 188 | 99,8 % | 656,9x |
| 6380 | 37 Usaremos aquí el vocablo «exención» en términos amplios, siendo discutida | Penal | 97633 | 153 | 99,8 % | 638,1x |
| 6381 | 38   The Nobel Prize (2020): Karl Landsteiner, disponible en https://www.nobelprize.org/prizes/medicine/1930/ | Familia | 65085 | 137 | 99,8 % | 475,1x |
| 6382 | 38 La Ley 21.389 modificó el antiguo tenor del artículo 8, apuntando a uno de los | Familia | 97488 | 156 | 99,8 % | 624,9x |
| 6383 | 38 Superintendencia de Seguridad Social, Oficio 62409, 6 de junio de 2015. En el | Familia | 123490 | 191 | 99,8 % | 646,5x |
| 6384 | 38. CORTE IDH (2005): Caso Hermanas Serrano               51. CORTE SUPREMA, rol N° 3.055-2010, de dos de | Familia | 65085 | 106 | 99,8 % | 614,0x |
| 6385 | 38. Señale cuáles son las medidas que puede adoptar el Tribunal de Defensa de la Libre | Judicial | 105809 | 179 | 99,8 % | 591,1x |
| 6386 | 39 El artículo 1736 inciso primero del Código Civil dispone: «La especie adquirida | Familia | 123490 | 195 | 99,8 % | 633,3x |
| 6387 | 39 Véase los artículos 37 letr d) y 40.2 letra b) puntos ii y iii de la Convención de los | Penal | 86906 | 132 | 99,8 % | 658,4x |
| 6388 | 39. Juzgado de Letras y Garantía de Puerto Natales | Constitucional | 44292 | 98 | 99,8 % | 452,0x |
| 6389 | 4 Artículo 231: «La ejecución de las resoluciones corresponde a los tribunales que las | Judicial | 89450 | 149 | 99,8 % | 600,3x |
| 6390 | 4 Barberis hace referencia al libro de G.H. Von Wright, Norm and action. A logical | Constitucional | 46896 | 76 | 99,8 % | 617,1x |
| 6391 | 4 CAT, Observación general número 1: aplicación del artículo 3 en relación con el | Judicial | 78893 | 149 | 99,8 % | 529,5x |
| 6392 | 4 Considerando que el artículo 13 número 1 de la Ley 18.290 establece que para | Penal | 86906 | 174 | 99,8 % | 499,5x |
| 6393 | 4 Decreto número 11, aprueba reglamento que regula el procedimiento de tutela | Constitucional | 46896 | 96 | 99,8 % | 488,5x |
| 6394 | 4 Los pueblos originarios latinoamericanos rememoran en sus países el choque | Judicial | 87950 | 156 | 99,8 % | 563,8x |
| 6395 | 4 Los reenvíos que existen son: i) el inciso final del artículo 62 de la Ley 19.968 | Procesal | 86112 | 146 | 99,8 % | 589,8x |
| 6396 | 4 Según la Superintendencia de Seguridad Social, Dictamen 3572 del 15 de enero | Laboral | 98828 | 171 | 99,8 % | 577,9x |
| 6397 | 4 Sentencia de la Corte de Apelaciones San Miguel, rol 278-2020, 31 de julio de | Familia | 97488 | 149 | 99,8 % | 654,3x |
| 6398 | 4 Sin regulación legal general, Wilenmann (2020: 8) observa que las disposiciones | Penal | 51155 | 98 | 99,8 % | 522,0x |
| 6399 | 4 Véase «El derecho a la tierra en el marco de la Declaración de las Naciones Unidas | Judicial | 60665 | 100 | 99,8 % | 606,6x |
| 6400 | 4 Véase «Percepción de los procesos de investigación y judicialización en los casos | Judicial | 33208 | 83 | 99,8 % | 400,1x |
| 6401 | 4 Véase, Ivelic (2019: 58-111) y Corte Suprema rol 46.489-16, del 5 de septiembre de | Penal | 97633 | 201 | 99,8 % | 485,7x |
| 6402 | 4. Abrir y cerrar las sesiones del tribunal, anticipar o prorrogar las | Judicial | 54457 | 85 | 99,8 % | 640,7x |
| 6403 | 4. Administración de causas | Penal | 57066 | 98 | 99,8 % | 582,3x |
| 6404 | 4. Ajustes razonables: Son modificaciones, adaptaciones necesarias y | Judicial | 53521 | 94 | 99,8 % | 569,4x |
| 6405 | 4. Ampliación del ámbit de aplicación de la lesión en rme: a partir del Código Civil | Civil | 110175 | 200 | 99,8 % | 550,9x |
| 6406 | 4. Asesorar al juez, a requerimiento de este, en la evaluación del | Judicial | 52128 | 92 | 99,8 % | 566,6x |
| 6407 | 4. Brindar a las víctimas mecanismos que les permitan acceder en | Judicial | 53521 | 114 | 99,8 % | 469,5x |
| 6408 | 4. Certificado de ejecutoria | Penal | 57066 | 109 | 99,8 % | 523,5x |
| 6409 | 4. Con la de prisión en su grado máximo a presidio menor en su grado | Penal | 51155 | 106 | 99,8 % | 482,6x |
| 6410 | 4. Cuando en el juicio oral hubieren sido violadas las disposiciones esta- | Procesal | 66012 | 110 | 99,8 % | 600,1x |
| 6411 | 4. Cuando esa separación sea resultado de una medida adoptada | Penal | 72395 | 124 | 99,8 % | 583,8x |
| 6412 | 4. Cuando un Estado, en virtud del presente artículo, detenga a una | Judicial | 78893 | 139 | 99,8 % | 567,6x |
| 6413 | 4. Cuando, además de las causas que dieron origen a la protección | Constitucional | 46896 | 113 | 99,8 % | 415,0x |
| 6414 | 4. Cuarto, desde los 6 a 11 años. En este tiempo, los niños entran en | Judicial | 87237 | 132 | 99,8 % | 660,9x |
| 6415 | 4. Designación de relator (a) interino (a) de esta CA, por nombramiento de doña | Judicial | 54457 | 92 | 99,8 % | 591,9x |
| 6416 | 4. El acuerdo de extensión de beneficios o la referencia de no haberse | Laboral | 74025 | 161 | 99,8 % | 459,8x |
| 6417 | 4. El acuerdo de extensión deberá fijar criterios objetivos, generales | Laboral | 74025 | 182 | 99,8 % | 406,7x |
| 6418 | 4. En un tiempo inmediato a la ocurrencia de un delito, es encontrada | Penal | 51155 | 100 | 99,8 % | 511,6x |
| 6419 | 4. Gestionar los procesos de contratación del tribunal, lo que incluye | Judicial | 52128 | 88 | 99,8 % | 592,4x |
| 6420 | 4. Instituciones indígenas: Aquellas que los pueblos y comunidades | Judicial | 53521 | 88 | 99,8 % | 608,2x |
| 6421 | 4. La Inspección del Trabajo: si actuando dentro del ámbito de sus | Laboral | 74025 | 184 | 99,8 % | 402,3x |
| 6422 | 4. La notificación aparece en la historia de la causa con el resultado | Judicial | 89450 | 156 | 99,8 % | 573,4x |
| 6423 | 4. La polifuncionalidad además se deberá reflejar en los turnos de | Judicial | 52128 | 101 | 99,8 % | 516,1x |
| 6424 | 4. Los contratos forzosos propiamente tales constituyen, con mucho, la regla general, y los | Civil | 110175 | 178 | 99,8 % | 619,0x |
| 6425 | 4. Los mecanismos de control o supervisión que usará el empleador | Laboral | 98828 | 201 | 99,8 % | 491,7x |
| 6426 | 4. Nuevos antecedentes de vulneración de derechos de igual o mayor | Constitucional | 46896 | 87 | 99,8 % | 539,0x |
| 6427 | 4. Plazos de agendamiento. Establecer un indicador más exigente | Judicial | 52128 | 97 | 99,8 % | 537,4x |
| 6428 | 4. Prueba | Constitucional | 46896 | 85 | 99,8 % | 551,7x |
| 6429 | 4. Que por otra parte, el actor recurrió en contra de la sentencia de primer grado, en cuanto | Judicial | 79146 | 144 | 99,8 % | 549,6x |
| 6430 | 4. Que, como es sabido, dentro de las actitudes que el demandado | Familia | 65085 | 124 | 99,8 % | 524,9x |
| 6431 | 4. Relaciones interinstitucionales: generar vínculos entre institu- | Judicial | 44331 | 68 | 99,8 % | 651,9x |
| 6432 | 4. Revisión periódica de la privación de la libertad para examinar la | Penal | 86906 | 169 | 99,8 % | 514,2x |
| 6433 | 4. Se debe rellenar el recuadro “álbum” con el año, mes y día | Judicial | 44331 | 102 | 99,8 % | 434,6x |
| 6434 | 4. Si dicha diferencia de trato constituyó discriminación, para lo | Judicial | 87237 | 132 | 99,8 % | 660,9x |
| 6435 | 4.1     Introducción | Judicial | 54457 | 122 | 99,8 % | 446,4x |
| 6436 | 4.1. Demanda civil interpuesta ante el juez de garantía: establece el art. 60 del Código | Civil | 96458 | 187 | 99,8 % | 515,8x |
| 6437 | 4.1.1 Liquidación Voluntaria | Judicial | 64632 | 106 | 99,8 % | 609,7x |
| 6438 | 4.1.1.1 Antecedentes que deben acompañar la solicitud | Judicial | 64632 | 139 | 99,8 % | 465,0x |
| 6439 | 4.1.1.2 Tramitación | Judicial | 64632 | 100 | 99,8 % | 646,3x |
| 6440 | 4.1.2 Del procedimiento para investigar y | Judicial | 54457 | 120 | 99,8 % | 453,8x |
| 6441 | 4.1.2.1 Informar al público general acerca del estado de | Laboral | 71986 | 111 | 99,8 % | 648,5x |
| 6442 | 4.1.2.13 Patrocinio y Poder | Laboral | 71986 | 113 | 99,8 % | 637,0x |
| 6443 | 4.1.2.7 Recibir escritos de causas por parte de usuarios | Laboral | 71986 | 109 | 99,8 % | 660,4x |
| 6444 | 4.1.3 Etapas del procedimiento ordinario | Judicial | 54457 | 89 | 99,8 % | 611,9x |
| 6445 | 4.1.3 Liquidación Forzada | Judicial | 64632 | 113 | 99,8 % | 572,0x |
| 6446 | 4.1.3.1 Causales de Liquidación Forzada | Judicial | 64632 | 117 | 99,8 % | 552,4x |
| 6447 | 4.1.3.1 Etapa de instrucción | Judicial | 54457 | 118 | 99,8 % | 461,5x |
| 6448 | 4.1.3.2 Etapa resolutiva | Judicial | 54457 | 131 | 99,8 % | 415,7x |
| 6449 | 4.1.3.3 Audiencia inicial | Judicial | 64632 | 122 | 99,8 % | 529,8x |
| 6450 | 4.1.3.3 Etapa de impugnación y revisión | Judicial | 54457 | 106 | 99,8 % | 513,7x |
| 6451 | 4.1.3.4 Juicio de oposición | Judicial | 64632 | 122 | 99,8 % | 529,8x |
| 6452 | 4.1.4 Sobre otros procedimientos para | Judicial | 54457 | 113 | 99,8 % | 481,9x |
| 6453 | 4.1.5 Adecuaciones dispuestas por el | Judicial | 54457 | 94 | 99,8 % | 579,3x |
| 6454 | 4.2.1 Efectos sobre los bienes | Judicial | 64632 | 107 | 99,8 % | 604,0x |
| 6455 | 4.2.2 Otras audiencias ante tribunal oral en lo penal | Penal | 57066 | 107 | 99,8 % | 533,3x |
| 6456 | 4.2.2 Tramitación de gestiones judiciales | Judicial | 44331 | 85 | 99,8 % | 521,5x |
| 6457 | 4.2.2.1 Toma de declaración a testigo o perito | Penal | 57066 | 118 | 99,8 % | 483,6x |
| 6458 | 4.2.2.2 Audiencia de discusión de medida cautelar | Penal | 57066 | 120 | 99,8 % | 475,6x |
| 6459 | 4.2.2.3 Audiencias de sobreseimiento | Penal | 57066 | 114 | 99,8 % | 500,6x |
| 6460 | 4.2.2.4 Audiencias de cautela de garantía | Penal | 57066 | 117 | 99,8 % | 487,7x |
| 6461 | 4.2.2.5 Revisión de sanción aplicada por régimen interno | Penal | 57066 | 114 | 99,8 % | 500,6x |
| 6462 | 4.2.2.6 Audiencias de control de detención | Penal | 57066 | 119 | 99,8 % | 479,5x |
| 6463 | 4.2.3 Efectos respecto de los juicios | Judicial | 64632 | 105 | 99,8 % | 615,5x |
| 6464 | 4.2.3 Situación por pandemia | Penal | 57066 | 114 | 99,8 % | 500,6x |
| 6465 | 4.2.4 Efectos respecto de los contratos | Judicial | 64632 | 101 | 99,8 % | 639,9x |
| 6466 | 4.2.4 Sistema de grabación y respaldo de audiencias | Penal | 57066 | 114 | 99,8 % | 500,6x |
| 6467 | 4.2.4.1 Esquema de grabación con “Audiograbber” | Penal | 57066 | 132 | 99,8 % | 432,3x |
| 6468 | 4.3     Uso de los sistemasSITCI y SITMIX | Judicial | 52128 | 88 | 99,8 % | 592,4x |
| 6469 | 4.3.1 Elementos de la posesión notoria | Familia | 65085 | 105 | 99,8 % | 619,9x |
| 6470 | 4.3.1 Ingreso de causas | Penal | 57066 | 126 | 99,8 % | 452,9x |
| 6471 | 4.3.1 Verificación ordinaria | Judicial | 64632 | 117 | 99,8 % | 552,4x |
| 6472 | 4.3.2 Término de una causa | Penal | 57066 | 127 | 99,8 % | 449,3x |
| 6473 | 4.3.3 Colisión con la prueba biológica | Familia | 65085 | 107 | 99,8 % | 608,3x |
| 6474 | 4.4. Principio de la equidad, del interés preponderante o principio de preponderancia del | Civil | 26055 | 49 | 99,8 % | 531,7x |
| 6475 | 4.4.1 Acción de reclamación de la filiación matrimonial129 | Familia | 65085 | 104 | 99,8 % | 625,8x |
| 6476 | 4.4.1 Ingreso de un auto de apertura | Penal | 57066 | 92 | 99,8 % | 620,3x |
| 6477 | 4.4.1 Realización simplificada o sumaria | Judicial | 64632 | 113 | 99,8 % | 572,0x |
| 6478 | 4.4.2 Acción de reclamación de filiación no matrimonial | Familia | 65085 | 152 | 99,8 % | 428,2x |
| 6479 | 4.4.2 Realización ordinaria | Judicial | 64632 | 100 | 99,8 % | 646,3x |
| 6480 | 4.4.3 Acción de reclamación en el caso | Familia | 65085 | 126 | 99,8 % | 516,5x |
| 6481 | 4.4.3 Gestión de causas | Penal | 57066 | 111 | 99,8 % | 514,1x |
| 6482 | 4.4.3 Venta como unidad económica | Judicial | 64632 | 109 | 99,8 % | 593,0x |
| 6483 | 4.4.4 Hijos nacidos antes de la entrada | Familia | 65085 | 136 | 99,8 % | 478,6x |
| 6484 | 4.4.4 Ingreso de solicitudes o escritos | Penal | 57066 | 89 | 99,8 % | 641,2x |
| 6485 | 4.4.5 Leasing | Judicial | 64632 | 98 | 99,8 % | 659,5x |
| 6486 | 4.4.5 Notificaciones | Penal | 57066 | 110 | 99,8 % | 518,8x |
| 6487 | 4.4.7 Tramitación en audiencia | Penal | 57066 | 117 | 99,8 % | 487,7x |
| 6488 | 4.4.8 Devolución de la causa al juzgado de garantía | Penal | 57066 | 123 | 99,8 % | 464,0x |
| 6489 | 4.5. Herramientas | Procesal | 96699 | 158 | 99,8 % | 612,0x |
| 6490 | 4.5.1 Impugnación de la filiación determinada según | Familia | 65085 | 148 | 99,8 % | 439,8x |
| 6491 | 4.5.1 Por dictación de la Resolución de término | Judicial | 64632 | 97 | 99,8 % | 666,3x |
| 6492 | 4.5.2 Impugnación de la paternidad | Familia | 65085 | 145 | 99,8 % | 448,9x |
| 6493 | 4.5.2 Por Acuerdo de Reorganización Judicial | Judicial | 64632 | 106 | 99,8 % | 609,7x |
| 6494 | 4.5.3 Impugnación de la maternidad | Familia | 65085 | 107 | 99,8 % | 608,3x |
| 6495 | 4.7.3 Fuerza | Familia | 65085 | 128 | 99,8 % | 508,5x |
| 6496 | 40.1. Los Estados parte reconocen el derecho de todo niño de quien se | Penal | 86906 | 162 | 99,8 % | 536,5x |
| 6497 | 41 El inciso segundo del artículo 31 de la Ley 14.908 señala: «Si el vendedor del | Familia | 97488 | 221 | 99,8 % | 441,1x |
| 6498 | 42 Puede haber matices. En sede penal, el ofrecimiento de los medios probatorios | Procesal | 86112 | 135 | 99,8 % | 637,9x |
| 6499 | 42 Situaciones subjetivas de esta naturaleza pueden igualmente encuadrarse en la | Penal | 97633 | 187 | 99,8 % | 522,1x |
| 6500 | 42 Sobre algunas citas doctrinales que pueden directa o indirectamente referirse | Procesal | 86112 | 172 | 99,8 % | 500,7x |
| 6501 | 43. El Comité insta al Estado parte a adoptar las medidas legislativas y | Judicial | 78893 | 169 | 99,8 % | 466,8x |
| 6502 | 44 Como señala Taruffo (2005: 381): «La existencia de procedimientos legales de | Procesal | 86112 | 180 | 99,8 % | 478,4x |
| 6503 | 44 Reglamento de la Ley 21.389 consta en el Decreto Supremo 62, publicado en el | Familia | 97488 | 183 | 99,8 % | 532,7x |
| 6504 | 46 A modo ejemplar, salta a la vista el uso cotidiano que en sede penal tiene, para | Procesal | 86112 | 187 | 99,8 % | 460,5x |
| 6505 | 46 Matus y Ramírez (2019: 483 y 484) explican que esta asimilación de la tentativa | Penal | 97633 | 195 | 99,8 % | 500,7x |
| 6506 | 46. El Comité mantiene su preocupación por la vigencia del Decreto | Judicial | 78893 | 172 | 99,8 % | 458,7x |
| 6507 | 47 Véase el artículo 16 y 40.2 letra b) punto viii de la Convención de los Derechos | Penal | 86906 | 158 | 99,8 % | 550,0x |
| 6508 | 5        Mayor cuantía: 500 UTM o más; menor cuantía: más de 10 UTM y hasta 500 UTM; mínima cuantía: cuando | Judicial | 52128 | 102 | 99,8 % | 511,1x |
| 6509 | 5 Al efecto es interesante analizar el trabajo del Observatorio Contra el Acoso en | Laboral | 53374 | 92 | 99,8 % | 580,2x |
| 6510 | 5 Artículo 97. «Obligación de cumplimiento e información. El tribunal, los fiscales | Penal | 51155 | 101 | 99,8 % | 506,5x |
| 6511 | 5 Así lo señalan Allard, Hennig y Galdámez (2016: 108) a partir de los fallos del | Judicial | 87950 | 161 | 99,8 % | 546,3x |
| 6512 | 5 Como refiere Bustos (2009: 592), dadas las dificultades para distinguir cuándo el | Penal | 97633 | 180 | 99,8 % | 542,4x |
| 6513 | 5 Comunicación 1298/2004, Becerra Barney con Colombia, párrafo 7.2 | Judicial | 62514 | 149 | 99,8 % | 419,6x |
| 6514 | 5 El ya citado artículo 453 número 4 del Código del Trabajo establece en su inicio | Procesal | 86112 | 150 | 99,8 % | 574,1x |
| 6515 | 5 En su artículo de 1971, Wróblewski señala con toda claridad que el concepto de | Judicial | 92792 | 171 | 99,8 % | 542,6x |
| 6516 | 5 Este apartado complementa la propuesta pragma-dialéctica en dos sentidos. En | Judicial | 92792 | 163 | 99,8 % | 569,3x |
| 6517 | 5 Este apartado reproduce algunas ideas de Carbonell (2021). Véase también el | Judicial | 92792 | 157 | 99,8 % | 591,0x |
| 6518 | 5 Esto no significa, en caso alguno, menospreciar la labor de la judicatura, pues | Judicial | 81675 | 182 | 99,8 % | 448,8x |
| 6519 | 5 Matus y Ramírez (2019: 502) señalan que la actividad de tráfico, si bien puede | Penal | 97633 | 201 | 99,8 % | 485,7x |
| 6520 | 5 Según el Comité de Derechos Humanos de Naciones Unidas una manifestación | Penal | 51155 | 113 | 99,8 % | 452,7x |
| 6521 | 5 Sentencia de la Corte de Apelaciones de Concepción, rol 141-2021, 20 de mayo | Familia | 97488 | 196 | 99,8 % | 497,4x |
| 6522 | 5 Situación distinta es la que acontece en otros cuerpos legales, donde es el Juez de | Penal | 97633 | 167 | 99,8 % | 584,6x |
| 6523 | 5 Sondear en las NECESIDADES DEL | Judicial | 53521 | 81 | 99,8 % | 660,8x |
| 6524 | 5 Tal como señalan Nash y David, a lo largo de la Convención Americana sobre | Laboral | 53374 | 118 | 99,8 % | 452,3x |
| 6525 | 5 Tomo el término de Albrecht: «El derecho penal en la intervención de la política | Penal | 86906 | 141 | 99,8 % | 616,4x |
| 6526 | 5.    GOLDENBERG, J. y JEQUIER, E. (2019): “Dos | Judicial | 64632 | 126 | 99,8 % | 513,0x |
| 6527 | 5.   BCN (1998): Historia de la Ley Nº 19.585, Modifica | Familia | 65085 | 105 | 99,8 % | 619,9x |
| 6528 | 5.   Ley N° 18.175, de 28 de octubre de 1982, que Fija | Judicial | 64632 | 133 | 99,8 % | 486,0x |
| 6529 | 5. Cumpliendo con el mandato del artículo 61 del Código de Proce- | Judicial | 89450 | 179 | 99,8 % | 499,7x |
| 6530 | 5. Dentro de los seis meses de practicada la visita de que trata el | Judicial | 52128 | 115 | 99,8 % | 453,3x |
| 6531 | 5. Estampar el timbre de cargo a los escritos presentados por las | Judicial | 52128 | 93 | 99,8 % | 560,5x |
| 6532 | 5. La condición negativa y resolutoria física o moralmente imposible o ininteligible, se | Civil | 118177 | 195 | 99,8 % | 606,0x |
| 6533 | 5. La persona natural o jurídica a cuyo favor se haga la inscripción, con indicación del | General | 59520 | 141 | 99,8 % | 422,1x |
| 6534 | 5. Lenguas indígenas: Lenguas propias de los pueblos originarios de | Judicial | 53521 | 107 | 99,8 % | 500,2x |
| 6535 | 5. Lesiones a raíz de uso de perdigones: en las manifestaciones del | Judicial | 78893 | 170 | 99,8 % | 464,1x |
| 6536 | 5. No se podrá imputar al pago mensual una suma que exceda del | Familia | 97488 | 148 | 99,8 % | 658,7x |
| 6537 | 5. Por solicitarlo alguna de las partes o pedirlo de común acuerdo | Judicial | 54457 | 115 | 99,8 % | 473,5x |
| 6538 | 5. Que en la especie, como se advierte del texto de la contestación | Familia | 65085 | 132 | 99,8 % | 493,1x |
| 6539 | 5. Que sobre el punto en cuestión hay que señalar que dentro del régimen establecido por | Judicial | 79146 | 127 | 99,8 % | 623,2x |
| 6540 | 5. Quinto, en la pubertad. Entran los niños en una “etapa genital” | Judicial | 87237 | 133 | 99,8 % | 655,9x |
| 6541 | 5. Recibir causas inadmisibles derivadas de la sala de cuenta para | Judicial | 44331 | 83 | 99,8 % | 534,1x |
| 6542 | 5. Rol Nº 1339-2019. Reclamo deducido por las abogadas señoras Marcela Miranda | Judicial | 54457 | 101 | 99,8 % | 539,2x |
| 6543 | 5. Seguimiento de la legislación del Estado referida o vinculada a los | Constitucional | 46896 | 117 | 99,8 % | 400,8x |
| 6544 | 5. Unidad familiar: Se refiere a que la separación de los niños, niñas y | Judicial | 53521 | 94 | 99,8 % | 569,4x |
| 6545 | 5.1. Debe tratarse de una herencia en la que se apliquen las reglas de la | Civil | 36934 | 84 | 99,8 % | 439,7x |
| 6546 | 5.1. Regla de la aplicación restringida del texto contractual: art. 1561: “Por generales que | Civil | 110175 | 169 | 99,8 % | 651,9x |
| 6547 | 5.1.1 Integrantes | Judicial | 52128 | 101 | 99,8 % | 516,1x |
| 6548 | 5.1.10 Liquidación de la indemnización | Judicial | 105809 | 171 | 99,8 % | 618,8x |
| 6549 | 5.1.2 Funciones de la Unidad de Atención de Público | Judicial | 52128 | 104 | 99,8 % | 501,2x |
| 6550 | 5.1.2.1 Informar al público general acerca | Judicial | 52128 | 100 | 99,8 % | 521,3x |
| 6551 | 5.1.2.10 Coordinar, en caso que se requiera, la | Judicial | 52128 | 111 | 99,8 % | 469,6x |
| 6552 | 5.1.2.13 Patrocinio y poder | Judicial | 52128 | 111 | 99,8 % | 469,6x |
| 6553 | 5.1.2.3 Entregar información sobre direcciones | Judicial | 52128 | 89 | 99,8 % | 585,7x |
| 6554 | 5.1.2.5 Atender los llamados telefónicos | Judicial | 52128 | 100 | 99,8 % | 521,3x |
| 6555 | 5.1.2.6 Escanear escritos, solicitudes e | Judicial | 52128 | 92 | 99,8 % | 566,6x |
| 6556 | 5.1.2.7 Recibir escritos de causas de usuarios | Judicial | 52128 | 101 | 99,8 % | 516,1x |
| 6557 | 5.1.2.9 Entregar copias de resoluciones, oficios, actas | Judicial | 52128 | 111 | 99,8 % | 469,6x |
| 6558 | 5.2. Regla de la natural extensión de la declaración: art. 1565: “Cuando en un contrato se | Civil | 110175 | 179 | 99,8 % | 615,5x |
| 6559 | 5.2.1 Causales | Judicial | 64632 | 111 | 99,8 % | 582,3x |
| 6560 | 5.2.1 Sorteo de salas | Judicial | 44331 | 87 | 99,8 % | 509,6x |
| 6561 | 5.2.2 La actuación jurisdiccional | Judicial | 64632 | 122 | 99,8 % | 529,8x |
| 6562 | 5.3. Regla del objetivo práctico o utilidad de las cláusulas: art. 1562: “El sentido en que | Civil | 110175 | 171 | 99,8 % | 644,3x |
| 6563 | 5.4. Regla del sentido natural: art. 1563, inciso 1º: “En aquellos casos en que no apareciere | Civil | 110175 | 178 | 99,8 % | 619,0x |
| 6564 | 5.5. Regla de la armonía de las cláusulas: art. 1564, inciso 1º: “Las cláusulas de un | Civil | 110175 | 175 | 99,8 % | 629,6x |
| 6565 | 5.6. Regla de la interpretación de un contrato por otro: art. 1564, inciso 2º: “Podrán | Civil | 110175 | 170 | 99,8 % | 648,1x |
| 6566 | 5.6.1 Efectos entre las partes | Judicial | 64632 | 120 | 99,8 % | 538,6x |
| 6567 | 5.6.1.1 Oficios de diversas instituciones | Judicial | 52128 | 98 | 99,8 % | 531,9x |
| 6568 | 5.6.1.2 Las demandas y escritos que pudieran | Judicial | 52128 | 123 | 99,8 % | 423,8x |
| 6569 | 5.6.1.4 Otros | Judicial | 52128 | 93 | 99,8 % | 560,5x |
| 6570 | 5.6.2 Efectos respecto de terceros | Judicial | 64632 | 126 | 99,8 % | 513,0x |
| 6571 | 5.6.2 Principales documentos despachados | Judicial | 52128 | 105 | 99,8 % | 496,5x |
| 6572 | 5.8. Regla de las cláusulas usuales: art. 1563, inciso 2º: “Las cláusulas de uso común se | Civil | 110175 | 171 | 99,8 % | 644,3x |
| 6573 | 5.8.1.1 Recepción de materiales o existencias | Laboral | 71986 | 110 | 99,8 % | 654,4x |
| 6574 | 5.8.2.5 Registros | Laboral | 71986 | 109 | 99,8 % | 660,4x |
| 6575 | 5.8.3.1 Dinero en efectivo | Laboral | 71986 | 114 | 99,8 % | 631,5x |
| 6576 | 5.8.3.2 Cheque o vale vista | Laboral | 71986 | 111 | 99,8 % | 648,5x |
| 6577 | 5.9. Regla de la última alternativa: art. 1566: “No pudiendo aplicarse ninguna de las reglas | Civil | 110175 | 202 | 99,8 % | 545,4x |
| 6578 | 50. NASH, Claudio (2013): “Control de convencionali- | Penal | 72395 | 115 | 99,8 % | 629,5x |
| 6579 | 50. Recientemente, la Corte ha señalado que la determinación del | Penal | 72395 | 131 | 99,8 % | 552,6x |
| 6580 | 51       OEA, Asamblea General, Resolución AG/RES. 2607 (XL-O/10), a través de la cual acoge una “Ley Modelo | Administrativo | 89720 | 140 | 99,8 % | 640,9x |
| 6581 | 51 COT); 4) un ministro de la CA respectiva (artículo 50 | Judicial | 54457 | 117 | 99,8 % | 465,4x |
| 6582 | 53 El Código del Trabajo no previene en su texto a los peritos de confianza en | Procesal | 86112 | 200 | 99,8 % | 430,6x |
| 6583 | 53. El Comité señala a la atención del Estado parte su observación ge- | Judicial | 78893 | 182 | 99,8 % | 433,5x |
| 6584 | 54 Entre la notificación de la demanda y la realización de la audiencia única deben | Procesal | 86112 | 150 | 99,8 % | 574,1x |
| 6585 | 54 Piénsese, en sede familiar, en un profesional de un programa de diagnóstico | Procesal | 86112 | 139 | 99,8 % | 619,5x |
| 6586 | 55. Se puede concluir, que en razón de las condiciones en las | Judicial | 87237 | 146 | 99,8 % | 597,5x |
| 6587 | 56 Artículo 453 número 8 inciso cuarto del Código del Trabajo, artículo 46 de | Procesal | 86112 | 161 | 99,8 % | 534,9x |
| 6588 | 57   RAMOS (1999), pp. 448-449 | Familia | 65192 | 100 | 99,8 % | 651,9x |
| 6589 | 57 En la Ley 19.968 que crea los Tribunales de Familia se previene el plazo de cinco | Procesal | 86112 | 137 | 99,8 % | 628,6x |
| 6590 | 57 Véase el artículo 40.3 letra b) de la Convención de los Derechos del Niño y la | Penal | 86906 | 137 | 99,8 % | 634,4x |
| 6591 | 58 En el Juzgado del Trabajo de Concepción, durante el 2021 ingresaron 1.435 casos | Procesal | 86112 | 192 | 99,8 % | 448,5x |
| 6592 | 58. Si bien no puede desconocerse que las circunstancias de | Judicial | 87237 | 141 | 99,8 % | 618,7x |
| 6593 | 6 Artículo 13: «El cumplimiento de las resoluciones que se dicten en los juicios a | Judicial | 89450 | 143 | 99,8 % | 625,5x |
| 6594 | 6 Bustos (2009: 592) plantea que es «un delito de lesión del bien jurídico salud | Penal | 97633 | 180 | 99,8 % | 542,4x |
| 6595 | 6 Declaración de Medidas para Eliminar el Terrorismo Internacional, anexo a la | Judicial | 62514 | 136 | 99,8 % | 459,7x |
| 6596 | 6 En este sentido, y referenciando a las opiniones y jurisprudencia de las cortes | Judicial | 81675 | 166 | 99,8 % | 492,0x |
| 6597 | 6 Para más información, véase Corte de Apelaciones de Concepción, rol 501-2018 | Judicial | 87950 | 184 | 99,8 % | 478,0x |
| 6598 | 6 Por ejemplo, el Segundo Juzgado de Letras del Trabajo de Santiago, en la Causa | Laboral | 98828 | 188 | 99,8 % | 525,7x |
| 6599 | 6 Sentencia de la Corte de Apelaciones de San Miguel, rol 920-1992, del 24 de julio | Judicial | 62514 | 123 | 99,8 % | 508,2x |
| 6600 | 6. Actuación del demandado, tratándose de la demanda civil interpuesta ante el juez | Civil | 96458 | 172 | 99,8 % | 560,8x |
| 6601 | 6. El Estado debe pagar las cantidades fijadas en los párrafos 294 y | Judicial | 87237 | 139 | 99,8 % | 627,6x |
| 6602 | 6. En los supuestos anteriores, también debe establecerse el tiempo | Laboral | 98828 | 187 | 99,8 % | 528,5x |
| 6603 | 6. Incorporar a los planes de trabajo la adopción de un protocolo | Constitucional | 44292 | 89 | 99,8 % | 497,7x |
| 6604 | 6. Los sindicatos actualmente pueden perseguir fines de lucro. Esto | Laboral | 74025 | 157 | 99,8 % | 471,5x |
| 6605 | 6. Participación e inclusión plenas y efectivas en la sociedad. Cobra | Judicial | 53521 | 98 | 99,8 % | 546,1x |
| 6606 | 6. Persigue siempre un objetivo espurio, ya sea destruir el honor o la | Laboral | 53374 | 110 | 99,8 % | 485,2x |
| 6607 | 6. Que dicha actitud procesal, está lejos de configurarse como una | Familia | 65085 | 110 | 99,8 % | 591,7x |
| 6608 | 6. Que ni la ley ni su reglamento del Registro del Conservador de Bienes Raíces admiten la | Judicial | 79146 | 132 | 99,8 % | 599,6x |
| 6609 | 6. Rol Nº 7-2020. Recurso de apelación interpuesto por la abogado señora XXXX, en | Judicial | 54457 | 117 | 99,8 % | 465,4x |
| 6610 | 6. Tendrán asimismo validez los acuerdos de constitución de dere- | Familia | 97488 | 166 | 99,8 % | 587,3x |
| 6611 | 6. Velar por la correcta mantención y actualización del sistema de | Judicial | 89450 | 157 | 99,8 % | 569,7x |
| 6612 | 6. Violencia de género contra las mujeres: Todo acto de violencia de | Judicial | 53521 | 106 | 99,8 % | 504,9x |
| 6613 | 6. Visualización de derivación en binoculares | Constitucional | 44292 | 97 | 99,8 % | 456,6x |
| 6614 | 6. unicef, 2004 | Penal | 86906 | 146 | 99,8 % | 595,2x |
| 6615 | 6.6.2 Observación General N° 14 | Penal | 72395 | 122 | 99,8 % | 593,4x |
| 6616 | 6.6.5 El interés superior del niño como | Penal | 72395 | 109 | 99,8 % | 664,2x |
| 6617 | 6.6.5.1 El derecho a la defensa como parte esencial del | Penal | 72395 | 148 | 99,8 % | 489,2x |
| 6618 | 61 Sentencia rol 17.043, Corte Suprema, de 6 de noviembre de 2018, considerando | Judicial | 81675 | 175 | 99,8 % | 466,7x |
| 6619 | 63 Nótese que en los procedimientos reformados, cuando se ha querido exigir que | Procesal | 86112 | 178 | 99,8 % | 483,8x |
| 6620 | 65. Exhortamos, por tanto, a los Poderes Judiciales de la Cumbre Judi- | Judicial | 42513 | 74 | 99,8 % | 574,5x |
| 6621 | 65. VARAS, Juan Andrés (2009): “Decisiones vitales | Penal | 72395 | 114 | 99,8 % | 635,0x |
| 6622 | 68   En el caso de los juzgados de Cobranza Laboral y Previsional, su competencia material se encuentra esta- | Laboral | 100583 | 175 | 99,8 % | 574,8x |
| 6623 | 7 Así ocurre en la Ley 19.617, de 12 de julio 1999, que modifica el Código Penal, el | Penal | 86906 | 172 | 99,8 % | 505,3x |
| 6624 | 7 Corte Suprema, rol 41.356-2017, del 5 de diciembre de 2017; Corte Suprema, rol | Penal | 97633 | 231 | 99,8 % | 422,7x |
| 6625 | 7 El escrito mediante el cual se interpone un recurso de casación en la forma debe | Judicial | 144656 | 228 | 99,8 % | 634,5x |
| 6626 | 7 En Corte Suprema, rol 1.351-18, del 8 de marzo de 2018 y Corte Suprema, rol | Penal | 97633 | 178 | 99,8 % | 548,5x |
| 6627 | 7 En el antiguo Código de Procedimiento Penal se regulaba en los artículos 471 y | Procesal | 86112 | 166 | 99,8 % | 518,7x |
| 6628 | 7 Esta norma se encuentra en consonancia con la del artículo 9° de la Ley N° | Penal | 86906 | 162 | 99,8 % | 536,5x |
| 6629 | 7 Hay que tener presente que la condición la deben cumplir imputados respecto | Judicial | 42513 | 67 | 99,8 % | 634,5x |
| 6630 | 7 La conducta del agente provocador es constitutiva de una acción de microtráfico | Penal | 97633 | 187 | 99,8 % | 522,1x |
| 6631 | 7 Los análisis históricos revelan una recíproca influencia entre el derecho penal de | Penal | 86906 | 136 | 99,8 % | 639,0x |
| 6632 | 7 Menciona los siguientes ejemplos: «Personas que viven en zonas alejadas de | Laboral | 98828 | 174 | 99,8 % | 568,0x |
| 6633 | 7 Para más información, véase Corte Suprema, rol 31.849-2019 del 14 de mayo | Judicial | 87950 | 178 | 99,8 % | 494,1x |
| 6634 | 7 Sentencia de la Corte de Apelaciones de San Miguel, rol 425-2021, 20 de julio de | Familia | 123490 | 195 | 99,8 % | 633,3x |
| 6635 | 7 Sobre familias multiproblemáticas este estupendo paper de Gómez, Muñoz y | Constitucional | 46896 | 93 | 99,8 % | 504,3x |
| 6636 | 7 Véase «Consentimiento libre…» e «Informe provisorio del estudio sobre los | Judicial | 60665 | 91 | 99,8 % | 666,6x |
| 6637 | 7 derivar | Judicial | 53521 | 81 | 99,8 % | 660,8x |
| 6638 | 7. Corte de Santiago comprende la parte de la Región Metropolitana | Judicial | 44331 | 106 | 99,8 % | 418,2x |
| 6639 | 7. El Comité urge al Estado parte a que establezca o designe un me- | Judicial | 78893 | 144 | 99,8 % | 547,9x |
| 6640 | 7. El monto de la pensión, expresado en unidades tributarias men- | Familia | 97488 | 152 | 99,8 % | 641,4x |
| 6641 | 7. En el mediano plazo, una estandarización de procedimientos, a tra- | Constitucional | 44292 | 81 | 99,8 % | 546,8x |
| 6642 | 7. Gráfica. Referida a señales cuyo significado es conocido por una | Judicial | 53521 | 100 | 99,8 % | 535,2x |
| 6643 | 7. La aplicación de la anticipación de audiencias, contemplada en | Judicial | 52128 | 93 | 99,8 % | 560,5x |
| 6644 | 7. Llevar la contabilidad y administrar la cuenta corriente del | Judicial | 52128 | 83 | 99,8 % | 628,0x |
| 6645 | 7. Por último y en relación con lo anterior, se trata de atentados de | Laboral | 53374 | 104 | 99,8 % | 513,2x |
| 6646 | 7. Prontitud y prioridad: Implica adoptar las medidas necesarias para | Judicial | 53521 | 113 | 99,8 % | 473,6x |
| 6647 | 7. Que en relación con este capítulo de la apelación, debe tenerse presente que el caso sub | Judicial | 79146 | 132 | 99,8 % | 599,6x |
| 6648 | 7. Redactar correo a las isapres, adjuntando carpeta de protecciones | Judicial | 44331 | 88 | 99,8 % | 503,8x |
| 6649 | 7. Situación migratoria: Condición en la que se encuentra una persona | Judicial | 53521 | 109 | 99,8 % | 491,0x |
| 6650 | 7.1.2 Recursos humanos | Judicial | 52128 | 109 | 99,8 % | 478,2x |
| 6651 | 7.1.3 Procesos | Laboral | 71986 | 109 | 99,8 % | 660,4x |
| 6652 | 7.1.3 Servicios e infraestructura | Judicial | 52128 | 79 | 99,8 % | 659,8x |
| 6653 | 7.1.4 Procesos | Judicial | 52128 | 107 | 99,8 % | 487,2x |
| 6654 | 7.2    Organización | Judicial | 52128 | 93 | 99,8 % | 560,5x |
| 6655 | 7.2. Por la expiración del plazo extintivo o al cumplirse la condición resolutoria | Civil | 42773 | 84 | 99,8 % | 509,2x |
| 6656 | 7.3. Situación, cuando entre los coasignatarios hay mujeres casadas en sociedad | Civil | 22201 | 48 | 99,8 % | 462,5x |
| 6657 | 7.3.3 Análisis general de las sentencias | Penal | 72395 | 114 | 99,8 % | 635,0x |
| 6658 | 7.5.1 Distribución del personal en las diferentes | Judicial | 52128 | 97 | 99,8 % | 537,4x |
| 6659 | 7.5.2 Modelo de polifuncionalidad y matriz de | Judicial | 52128 | 88 | 99,8 % | 592,4x |
| 6660 | 7.5.2.1   Matriz de subrogaciones | Laboral | 71986 | 122 | 99,8 % | 590,0x |
| 6661 | 7.5.3 Procedimiento objetivo y general de distribución | Judicial | 52128 | 111 | 99,8 % | 469,6x |
| 6662 | 7.5.4 Decretos económicos | Laboral | 71986 | 115 | 99,8 % | 626,0x |
| 6663 | 7.5.4 Protocolo de inducción al personal nuevo | Judicial | 52128 | 105 | 99,8 % | 496,5x |
| 6664 | 7.5.5 Decretos económicos | Judicial | 52128 | 119 | 99,8 % | 438,1x |
| 6665 | 7.5.6 Metas de gestión de desempeño | Judicial | 52128 | 110 | 99,8 % | 473,9x |
| 6666 | 7.5.7 Indicadores de gestión | Judicial | 52128 | 100 | 99,8 % | 521,3x |
| 6667 | 7.6. Por tener la calidad de deudor en un procedimiento concursal de liquidación, el | Civil | 42773 | 67 | 99,8 % | 638,4x |
| 6668 | 72 Generalmente, la Corte sostiene esta afirmación citando su propia opinión | Judicial | 81675 | 169 | 99,8 % | 483,3x |
| 6669 | 729. Estos artículos dejan en claro que la garantía que otorga la inscripción es para el | Civil | 36671 | 91 | 99,8 % | 403,0x |
| 6670 | 74 Si bien la expresión «bloque de constitucionalidad» es reconocida en países | Judicial | 81675 | 136 | 99,8 % | 600,6x |
| 6671 | 75 El control de convencionalidad que ejerce la Corte Interamericana de Derechos | Judicial | 81675 | 166 | 99,8 % | 492,0x |
| 6672 | 757. Establece dicha disposición que si ella se impone sin autorización judicial y sin | Civil | 66868 | 166 | 99,8 % | 402,8x |
| 6673 | 76 Algunos obiter dicta de la Corte Interamericana, sostienen que el control de | Judicial | 81675 | 169 | 99,8 % | 483,3x |
| 6674 | 77 Así por ejemplo, en Brasil, la sentencia STA 175 AgR/CE - CEARÁ, de 2009, que | Judicial | 81675 | 171 | 99,8 % | 477,6x |
| 6675 | 8        CONTADOR ROSALES, N. y PALACIOS VERGARA, C. (2015): Procedimientos concursales. Ley de insolvencia | Judicial | 64632 | 117 | 99,8 % | 552,4x |
| 6676 | 8 Además de las convenciones aquí citadas, en el contexto europeo el artículo 3 de | Judicial | 78893 | 179 | 99,8 % | 440,7x |
| 6677 | 8 Artículo 258: «El término de emplazamiento para contestar la demanda será de | Judicial | 89450 | 211 | 99,8 % | 423,9x |
| 6678 | 8 Corte Suprema, rol 10.197-17, del 4 de mayo de 2017. Se arriba a igual conclusión | Penal | 97633 | 174 | 99,8 % | 561,1x |
| 6679 | 8 Esto porque entre los beneficios del trabajo a distancia destacan «la reducción | Laboral | 98828 | 188 | 99,8 % | 525,7x |
| 6680 | 8 Información recabada de la Agencia Nacional de Medicamentos (Anamed), del | Penal | 97633 | 192 | 99,8 % | 508,5x |
| 6681 | 8 Para Muñoz Conde, quien de alguna manera se «enfrentó con Jakobs», las citas | Judicial | 62514 | 126 | 99,8 % | 496,1x |
| 6682 | 8 Si bien usualmente se requiere un tutor de la persona mayor como responsable | Judicial | 82507 | 166 | 99,8 % | 497,0x |
| 6683 | 8. Confidencialidad: Implica que los datos personales de las personas | Judicial | 53521 | 96 | 99,8 % | 557,5x |
| 6684 | 8. Ejercer su autoridad una vez reclamada su intervención en forma | Judicial | 52128 | 83 | 99,8 % | 628,0x |
| 6685 | 8. Notificaciones sentencias definitivas, comparecencia personal y | Judicial | 89450 | 157 | 99,8 % | 569,7x |
| 6686 | 8. Que en el caso de autos el actor impugnó de nulidad de derecho público la competencia | Judicial | 79146 | 131 | 99,8 % | 604,2x |
| 6687 | 8. Realizar el inventario de bodega de acuerdo a lo establecido por | Judicial | 52128 | 88 | 99,8 % | 592,4x |
| 6688 | 8. Verificar la recepción de documentos de la Ilma. Corte de Apelaciones y | Judicial | 52128 | 91 | 99,8 % | 572,8x |
| 6689 | 8.1. Extensión de la garantía, es decir, cosas que comprende la hipoteca, efectos con | Civil | 66868 | 136 | 99,8 % | 491,7x |
| 6690 | 83   Normalmente los textos refieren a Mario Bernaschina González, Eduardo Soto Kloss, Pedro Pierry Arrau y a | Judicial | 105809 | 163 | 99,8 % | 649,1x |
| 6691 | 83. La no discriminación, junto con la igualdad ante la ley y la igual | Judicial | 87237 | 140 | 99,8 % | 623,1x |
| 6692 | 84 En materia laboral, el inciso final del número 4 del artículo 453 del Código del | Judicial | 144656 | 227 | 99,8 % | 637,3x |
| 6693 | 85   En Chile, Corral opina lo contrario: “Los problemas del transexualismo no cabe enfocarlos con una óptica | Judicial | 89476 | 148 | 99,8 % | 604,6x |
| 6694 | 858.2 CC). La renuncia, sin embargo, no permitirá liberarse de obligaciones que ya | Civil | 49700 | 104 | 99,8 % | 477,9x |
| 6695 | 9 Aquí se sigue un concepto amplio de ideología entendida como una «toma de | Judicial | 92792 | 174 | 99,8 % | 533,3x |
| 6696 | 9 Concluye este autor que el denominado derecho penal de enemigo —al menos | Judicial | 62514 | 131 | 99,8 % | 477,2x |
| 6697 | 9 Corte Suprema, rol 37.989-17, del 12 de octubre de 2017. En Corte Suprema, rol | Penal | 97633 | 200 | 99,8 % | 488,2x |
| 6698 | 9 El artículo 454 del Código del Trabajo dispone que la audiencia comienza con la | Judicial | 42513 | 67 | 99,8 % | 634,5x |
| 6699 | 9 En Corte de Apelaciones de Valparaíso, rol 148-18, del 12 de febrero de 2018, se | Penal | 97633 | 185 | 99,8 % | 527,7x |
| 6700 | 9 En materia penal, la concepción del derecho penal como un medio de control | Penal | 86906 | 175 | 99,8 % | 496,6x |
| 6701 | 9 Solo puede existir una primera demanda en causas de alimentos, por tanto, una | Familia | 97488 | 188 | 99,8 % | 518,6x |
| 6702 | 9 Una crítica a la forma en que se realiza el control de detención la formula el | Judicial | 78893 | 180 | 99,8 % | 438,3x |
| 6703 | 9. La diligencia de notificación se extenderá en el proceso, señalando | Judicial | 89450 | 174 | 99,8 % | 514,1x |
| 6704 | 9. Los hechos a juicio del tribunal, en la actualidad, no pueden ser ca- | Judicial | 62514 | 140 | 99,8 % | 446,5x |
| 6705 | 9. Responder oficios provenientes tanto de la Iltma. Corte de | Judicial | 52128 | 79 | 99,8 % | 659,8x |
| 6706 | 9. Testimonio de NNA: Declaración que se presta mediante el uso del | Judicial | 53521 | 117 | 99,8 % | 457,4x |
| 6707 | 9. Trata de personas: Es un delito que consiste en el uso de diversas | Judicial | 53521 | 110 | 99,8 % | 486,6x |
| 6708 | 9. Víctimas indirectas y colaterales: Todas las personas que tienen un | Judicial | 53521 | 132 | 99,8 % | 405,5x |
| 6709 | 9.1. Prohibición de celebrar contratos de promesa de compraventa, si están | Civil | 29257 | 48 | 99,8 % | 609,5x |
| 6710 | 90 N° 2 del Código Orgánico de Tribunales, las que deberán quedar | Judicial | 44331 | 110 | 99,8 % | 403,0x |
| 6711 | 90. La Corte Interamericana ha reconocido que las personas LGBTI | Judicial | 81675 | 137 | 99,8 % | 596,2x |
| 6712 | 93. De esta manera, los órganos del SIDH han determinado que un proceso que demande excesivos costos para su | Procesal | 96699 | 172 | 99,8 % | 562,2x |
| 6713 | 93. La violencia contra las personas LGBTI tiene un fin simbólico, la | Judicial | 81675 | 161 | 99,8 % | 507,3x |
| 6714 | 955. Los derechos hereditarios que se invocan, podrían nacer “de las relaciones de | General | 125500 | 205 | 99,8 % | 612,2x |
| 6715 | 97   En el proceso rol 522-2019, la misma Corte de Apelaciones de San Miguel, en recurso de amparo deduci- | Judicial | 105809 | 171 | 99,8 % | 618,8x |
| 6716 | 97. A este respecto, conviene recordar que la corte señaló en la | Judicial | 87237 | 136 | 99,8 % | 641,4x |
| 6717 | Aduanas: etapa administrativa | Judicial | 62888 | 111 | 99,8 % | 566,6x |
| 6718 | Apellido2 | Judicial | 39447 | 79 | 99,8 % | 499,3x |
| 6719 | Años, según se trate de inmuebles urbanos o rústicos, que forman parte | Civil | 71319 | 140 | 99,8 % | 509,4x |
| 6720 | B) pago por consignación | Civil | 75968 | 165 | 99,8 % | 460,4x |
| 6721 | Capitulo i: el derecho de representacion | Civil | 36934 | 61 | 99,8 % | 605,5x |
| 6722 | Capitulo ii: las categorias contractuales.150 | Civil | 110175 | 185 | 99,8 % | 595,5x |
| 6723 | Capitulo ii: principios que informan la sucesion intestada | Civil | 36934 | 63 | 99,8 % | 586,3x |
| 6724 | Capitulo iii: clasificacion del testamento | Civil | 50203 | 79 | 99,8 % | 635,5x |
| 6725 | Capj | Judicial | 54457 | 120 | 99,8 % | 453,8x |
| 6726 | Capítulo III del Título III del Libro III, o sea, a propósito de los contratos o de las | Civil | 120848 | 218 | 99,8 % | 554,3x |
| 6727 | Capítulo X, «Del trabajo mediante plataformas digitales de servicios», en el Título | Laboral | 98828 | 184 | 99,8 % | 537,1x |
| 6728 | Confianza con discresión | Judicial | 53521 | 87 | 99,8 % | 615,2x |
| 6729 | Curadurías en part cular1 | Familia | 85324 | 166 | 99,8 % | 514,0x |
| 6730 | D) pago con beneficio de competencia | Civil | 75968 | 140 | 99,8 % | 542,6x |
| 6731 | De los enfermos mentales, de los alcoholicos y de los que presenten | Familia | 85324 | 205 | 99,8 % | 416,2x |
| 6732 | Derecho de alimentos1 | Familia | 81198 | 180 | 99,8 % | 451,1x |
| 6733 | Doi 10.4067/s0718-97532018000100257 | Judicial | 78893 | 139 | 99,8 % | 567,6x |
| 6734 | El contrato de arrendamiento1 | Civil | 71319 | 172 | 99,8 % | 414,6x |
| 6735 | Ii. del beneficio de separación | Civil | 21170 | 45 | 99,8 % | 470,4x |
| 6736 | Ii.-   la propiedad fiduciaria | General | 20070 | 35 | 99,8 % | 573,4x |
| 6737 | Iv.- la dacion en pago | Civil | 75968 | 169 | 99,8 % | 449,5x |
| 6738 | LGBTIQ+ y DESC | Judicial | 81675 | 145 | 99,8 % | 563,3x |
| 6739 | Los bienes1 | Civil | 42954 | 79 | 99,8 % | 543,7x |
| 6740 | MARiA CERRA ORTIZ | Procesal | 95124 | 158 | 99,8 % | 602,1x |
| 6741 | Management | Procesal | 96699 | 152 | 99,8 % | 636,2x |
| 6742 | Mira a los ojos | Judicial | 53521 | 104 | 99,8 % | 514,6x |
| 6743 | Nombramiento de tutores y curadores y del discernimiento de estos | Familia | 85324 | 196 | 99,8 % | 435,3x |
| 6744 | Normativa citada | Procesal | 66012 | 163 | 99,8 % | 405,0x |
| 6745 | Parte II | Judicial | 92792 | 153 | 99,8 % | 606,5x |
| 6746 | Parte de estas características son recogidas en una definición clásica de | Judicial | 92792 | 171 | 99,8 % | 542,6x |
| 6747 | Parte de la confusión aquí expresada tiene su origen en el criterio | Judicial | 62514 | 102 | 99,8 % | 612,9x |
| 6748 | Parte de la doctrina intenta buscar los fundamentos de la imprevisión en los | Civil | 120848 | 200 | 99,8 % | 604,2x |
| 6749 | Parte la norma señalando que el requerimiento de pago se notificará al | Familia | 65192 | 130 | 99,8 % | 501,5x |
| 6750 | Poder especial | Civil | 42773 | 74 | 99,8 % | 578,0x |
| 6751 | PrOgUnta:ANTE QUE TRIBUNAL SE INTERPONE? | Procesal | 95124 | 166 | 99,8 % | 573,0x |
| 6752 | PregUnta: QUEN PUEDE INTERPONER EL RECURSOY COMO? | Procesal | 95124 | 148 | 99,8 % | 642,7x |
| 6753 | PregUnta:QUE ES EL RECURSO DE REVISION? | Procesal | 95124 | 161 | 99,8 % | 590,8x |
| 6754 | Pregunta: &COMO SE TRAMITAN LOS JUICIOS ANTE LOS ARBITROSDEDERECHO? | Procesal | 95124 | 172 | 99,8 % | 553,0x |
| 6755 | Pregunta: &CUAL ES LA ESTRUCTURA DEL CODIGO DE PROCEDIMIENTO CIVIL? | Procesal | 95124 | 167 | 99,8 % | 569,6x |
| 6756 | Pregunta: &CUALES SON LAS EXCEPCIONES QUE PUEDEN OPONERSEEN EL JUICIOEJECUTIVO? | Procesal | 95124 | 172 | 99,8 % | 553,0x |
| 6757 | Pregunta: &CUANDO QUEDA UNA CAUSA EN ESTADO DE FALLO? | Procesal | 95124 | 208 | 99,8 % | 457,3x |
| 6758 | Pregunta: &QUE DERECHO TIENE EL DEMANDANTE SI EL DEMANDADO NO CONCURRE A LAAUDIENCIA? | Procesal | 95124 | 175 | 99,8 % | 543,6x |
| 6759 | Pregunta: &QUE ES LA EXCEPCION DE COSA JUZGADA? | Procesal | 95124 | 200 | 99,8 % | 475,6x |
| 6760 | Pregunta: &QUE ES LA INSPECCION PERSONAL DEL TRIBUNAL? | Procesal | 95124 | 154 | 99,8 % | 617,7x |
| 6761 | Pregunta: &QUE ES LA NOTIFICACION PERSONAL SUBSIDIARIA? | Procesal | 95124 | 163 | 99,8 % | 583,6x |
| 6762 | Pregunta: &QUE ES Y CUANDO SE PRODUCE EL DESASIMIENTO? | Procesal | 95124 | 154 | 99,8 % | 617,7x |
| 6763 | Pregunta: &QUE RESPONSABILIDAD TIENE EL MANDATARIO JUDICIAL? | Procesal | 95124 | 165 | 99,8 % | 576,5x |
| 6764 | Pregunta: &QUE SON LAS REGLAS DE LA COMPETENCIA RELATIPregunta: CUANDO EN MATERIA PENAL? | Procesal | 95124 | 187 | 99,8 % | 508,7x |
| 6765 | Pregunta: &QUIEN PRODUCE LA PRUEBA INSTRUMENTAL? | Procesal | 95124 | 161 | 99,8 % | 590,8x |
| 6766 | Pregunta: 2CUAL ES EL CONCEPTO DE ESTE RECURSOP | Procesal | 95124 | 167 | 99,8 % | 569,6x |
| 6767 | Pregunta: 2CUAL ES EL PLAZO PARA INTERPONERLO? | Procesal | 95124 | 162 | 99,8 % | 587,2x |
| 6768 | Pregunta: 2CUANDO SE OPONEN EN EL JUICIO ORDINARIO? EN | Procesal | 95124 | 176 | 99,8 % | 540,5x |
| 6769 | Pregunta: 2QUE ES LA CONTESTACION DE LA DEMANDA? REQUI1) | Procesal | 95124 | 169 | 99,8 % | 562,9x |
| 6770 | Pregunta: 2QUE SON LAS BASES FUNDAMENTALES DE LA ORGANIZACION DE LOS TRIBUNALES?&CUALES SON? | Procesal | 95124 | 163 | 99,8 % | 583,6x |
| 6771 | Pregunta: ANTE QUE TRIBUNAL SE EFECTUA EL REMATE? | Procesal | 95124 | 180 | 99,8 % | 528,5x |
| 6772 | Pregunta: ANTE QUE TRIBUNAL SE PROPONE LA INHIBITORIA? | Procesal | 95124 | 171 | 99,8 % | 556,3x |
| 6773 | Pregunta: CAPACIDAD PARA POSTULAR. eQUIENES TIENEN CAPACIDADPARAPOSTULARO“IUSPOSTULANDP"? | Procesal | 95124 | 157 | 99,8 % | 605,9x |
| 6774 | Pregunta: CARACTERiSTICAS DEL JUICIO ORDINARIO DE MAYOR | Procesal | 95124 | 169 | 99,8 % | 562,9x |
| 6775 | Pregunta: CAUSALES QUE AUTORIZAN LA INTERPOSICION DEL | Procesal | 95124 | 215 | 99,8 % | 442,4x |
| 6776 | Pregunta: COMO PUEDE PONERLE FIN EL ACREEDOR? | Procesal | 95124 | 179 | 99,8 % | 531,4x |
| 6777 | Pregunta: COMO PUEDE RESOLVER EL TRIBUNAL DE ALZADA EL | Procesal | 95124 | 171 | 99,8 % | 556,3x |
| 6778 | Pregunta: COMO RESUELVEN LAS CORTES DE APELACIONES? | Procesal | 95124 | 182 | 99,8 % | 522,7x |
| 6779 | Pregunta: COMO SE CLASIFICA EL AMPARO CONSTITUCIONAL? | Procesal | 95124 | 167 | 99,8 % | 569,6x |
| 6780 | Pregunta: COMO SE CLASIFICAN LOS INCIDENTES? | Procesal | 95124 | 178 | 99,8 % | 534,4x |
| 6781 | Pregunta: COMO SE COMPARECE ANTE LA CORTE SUPREMA? | Procesal | 95124 | 180 | 99,8 % | 528,5x |
| 6782 | Pregunta: COMO SE DENOMINA Y EN QUE CONSISTE LA SENTENCIADEUNARBITRO? | Procesal | 95124 | 182 | 99,8 % | 522,7x |
| 6783 | Pregunta: COMO SE FORMULA LA OPOSICION A LA EJECUCION? | Procesal | 95124 | 182 | 99,8 % | 522,7x |
| 6784 | Pregunta: COMO SE INICIA EL JUICIO DE DESPOSEIMIENTO? | Procesal | 95124 | 175 | 99,8 % | 543,6x |
| 6785 | Pregunta: COMO SE INTERPONE EL RECURSO DE CASACION EN | Procesal | 95124 | 162 | 99,8 % | 587,2x |
| 6786 | Pregunta: CONCEPTO DEL RECURSO DEACLARACION,INTERPRERECTIFICACION O ENMIENDA | Procesal | 95124 | 154 | 99,8 % | 617,7x |
| 6787 | Pregunta: CONTRA QUE RESOLUCIONES PROCEDE? | Procesal | 95124 | 150 | 99,8 % | 634,2x |
| 6788 | Pregunta: CQUE RESOLUCION RECAE EN LA DEMANDA? | Procesal | 95124 | 153 | 99,8 % | 621,7x |
| 6789 | Pregunta: CUAL ES LA NATURALEZA JURIDICA DE LAS TERCERIAS? | Procesal | 95124 | 179 | 99,8 % | 531,4x |
| 6790 | Pregunta: CUAL ES LA PROCEDENCIA DE ESTE RECURSOP | Procesal | 95124 | 174 | 99,8 % | 546,7x |
| 6791 | Pregunta: CUALES SON LAS RESOLUCIONES INAPELABLES? | Procesal | 95124 | 163 | 99,8 % | 583,6x |
| 6792 | Pregunta: CUALES SON LOS ACTOS QUE LA COMPONEN? | Procesal | 95124 | 167 | 99,8 % | 569,6x |
| 6793 | Pregunta: CUALES SON LOS INTERDICTOS POSESORIOS? | Procesal | 95124 | 152 | 99,8 % | 625,8x |
| 6794 | Pregunta: CUANDO DEBE OIRSE INFORME DE PERITOS? | Procesal | 95124 | 176 | 99,8 % | 540,5x |
| 6795 | Pregunta: CUANDO ES DIVISIBLE LA CONFESION? | Procesal | 95124 | 159 | 99,8 % | 598,3x |
| 6796 | Pregunta: CUANDO NO ES NECESARIO PREPARARLO? | Procesal | 95124 | 171 | 99,8 % | 556,3x |
| 6797 | Pregunta: CUANDO PUEDE CUMPLIRSE EN AMBOS CASOS? | Procesal | 95124 | 172 | 99,8 % | 553,0x |
| 6798 | Pregunta: CUANDO PUEDE LLEVARSE A CABO EL REMATE? | Procesal | 95124 | 158 | 99,8 % | 602,1x |
| 6799 | Pregunta: CUANDO SE PRODUCE LA PRESCRIPCION DE LA APELACION? | Procesal | 95124 | 166 | 99,8 % | 573,0x |
| 6800 | Pregunta: CUANTAS VECES PUEDE PEDIRSE LA CONFESION? | Procesal | 95124 | 179 | 99,8 % | 531,4x |
| 6801 | Pregunta: CUANTOS CUADERNOS PUEDEN FORMARSE EN UN | Procesal | 95124 | 163 | 99,8 % | 583,6x |
| 6802 | Pregunta: DE EJCMPLOS DE SENTENCIAS INTERLOCUTORIAS QUE | Procesal | 95124 | 166 | 99,8 % | 573,0x |
| 6803 | Pregunta: DE EJEMPLOS EN QUE HAYA DOS O MAS TRIBUNALES | Procesal | 95124 | 180 | 99,8 % | 528,5x |
| 6804 | Pregunta: DE QUE SENTENCIAS SURGE LA COSA JUZGADA? | Procesal | 95124 | 163 | 99,8 % | 583,6x |
| 6805 | Pregunta: DIFERENCIAS DE LA NOTIFICACION POR CEDULA CON | Procesal | 95124 | 163 | 99,8 % | 583,6x |
| 6806 | Pregunta: DIGA CUALES SON LAS FORMAS DE SOLUCION A LOS | Procesal | 95124 | 167 | 99,8 % | 569,6x |
| 6807 | Pregunta: DONDE SE NOTIFICA PERSONALMENTE? | Procesal | 95124 | 163 | 99,8 % | 583,6x |
| 6808 | Pregunta: EFECTOS CIVILES Y PROCESALES DE LA NOTIFICACION | Procesal | 95124 | 163 | 99,8 % | 583,6x |
| 6809 | Pregunta: EFECTOS DE LA DECLARACION DE ABANDONO DEL | Procesal | 95124 | 143 | 99,8 % | 665,2x |
| 6810 | Pregunta: EFECTOS DE LA INTERPOSICION DE UNA TERCERIA DE | Procesal | 95124 | 163 | 99,8 % | 583,6x |
| 6811 | Pregunta: EFECTOS DE LA INTERPOSICION DEL RECURSO DE | Procesal | 95124 | 191 | 99,8 % | 498,0x |
| 6812 | Pregunta: ELEMENTOS DEL EMPLAZAMIENTO EN DIFERENTES | Procesal | 95124 | 150 | 99,8 % | 634,2x |
| 6813 | Pregunta: EN QUE CASOS, POR EXCEPCION, PUEDE CUMPLIRSE | Procesal | 95124 | 165 | 99,8 % | 576,5x |
| 6814 | Pregunta: EN QUE JUICIOS PROCEDE AUMENTO EXTRAORDINARIODELTERMINOPROBATORIO? | Procesal | 95124 | 180 | 99,8 % | 528,5x |
| 6815 | Pregunta: EN QUE OPORTUNIDAD SE PUEDE PROPONER? | Procesal | 95124 | 183 | 99,8 % | 519,8x |
| 6816 | Pregunta: ENTONCES, &POR QUE SE DICE QUE ES ESPECIAL? | Procesal | 95124 | 162 | 99,8 % | 587,2x |
| 6817 | Pregunta: EQUE TIPO DE EXCEPCION ES LA COSA JUZGADA? | Procesal | 95124 | 182 | 99,8 % | 522,7x |
| 6818 | Pregunta: ES DE APLICACION GENERAL EL JUICIO SUMARIO? | Procesal | 95124 | 163 | 99,8 % | 583,6x |
| 6819 | Pregunta: ES LIBRE EL JUEZ PARA FIJAR LAS BASES DEL REMATE? | Procesal | 95124 | 182 | 99,8 % | 522,7x |
| 6820 | Pregunta: FALLO DE LA ACCION DE INAPLICABILIDAD | Procesal | 95124 | 176 | 99,8 % | 540,5x |
| 6821 | Pregunta: HASTA CUANDO SUBSISTE LA CAUCION? | Procesal | 95124 | 178 | 99,8 % | 534,4x |
| 6822 | Pregunta: IMPORTANCIA DE LA ENTREGA REAL O SIMBOLICA, AL | Procesal | 95124 | 179 | 99,8 % | 531,4x |
| 6823 | Pregunta: INTERPOSICION DEL RECURSO DE CASACION EN EL | Procesal | 95124 | 165 | 99,8 % | 576,5x |
| 6824 | Pregunta: PLAZO PARA DICTAR LAS RESOLUCIONES EN EL JUICIO | Procesal | 95124 | 167 | 99,8 % | 569,6x |
| 6825 | Pregunta: PUEDEN ENTABLARSE EN UNA DEMANDA DOS O MAS | Procesal | 95124 | 170 | 99,8 % | 559,6x |
| 6826 | Pregunta: QUE CARACTER TIENE ENTONCES ELMANDAMIENTO? | Procesal | 95124 | 158 | 99,8 % | 602,1x |
| 6827 | Pregunta: QUE CONTIENE EL CUADERNO PRINCIPAL O EJECUTI- | Procesal | 95124 | 157 | 99,8 % | 605,9x |
| 6828 | Pregunta: QUE DEBE HACER EL AGENTE OFICIOSO AL COMPARECER? | Procesal | 95124 | 171 | 99,8 % | 556,3x |
| 6829 | Pregunta: QUE ES EL DESISTIMIENTO DE LA DEMANDA? | Procesal | 95124 | 166 | 99,8 % | 573,0x |
| 6830 | Pregunta: QUE ES LA SUSTITUCION DEL EMBARGO? | Procesal | 95124 | 176 | 99,8 % | 540,5x |
| 6831 | Pregunta: QUE ES UNA SENTENCIA INTERLOCUTORIA? | Procesal | 95124 | 144 | 99,8 % | 660,6x |
| 6832 | Pregunta: QUE HACE EL TRIBUNAL UNA VEZ EVACUADO EL TRAMITEDERESPUESTAALAOPOSICION? | Procesal | 95124 | 178 | 99,8 % | 534,4x |
| 6833 | Pregunta: QUE ROLES CUMPLE EL REQUERIMIENTO DE PAGO? | Procesal | 95124 | 174 | 99,8 % | 546,7x |
| 6834 | Pregunta: QUE SON LAS EXCEPCIONES MIXTAS O ANOMALAS? | Procesal | 95124 | 175 | 99,8 % | 543,6x |
| 6835 | Pregunta: QUE VALOR TIENE ESTA ACTA DE CONCILIACION? | Procesal | 95124 | 163 | 99,8 % | 583,6x |
| 6836 | Pregunta: REFIERASE AL PRINCIPIO DE LA FIJEZA O RADICACION | Procesal | 95124 | 163 | 99,8 % | 583,6x |
| 6837 | Pregunta: REQUISITOS DE LOS AUTOS Y SENTENCIAS INTERLO | Procesal | 95124 | 172 | 99,8 % | 553,0x |
| 6838 | Pregunta: REQUISITOS PARA OECLARAR LA PRESCRIPCION DE LA | Procesal | 95124 | 176 | 99,8 % | 540,5x |
| 6839 | Pregunta: REQUISITOS PARA OTORGAR LA ESCRITURA PUBLICA | Procesal | 95124 | 167 | 99,8 % | 569,6x |
| 6840 | Pregunta: RESPECTO DE QUE RESOLUCIONES PROCEDE? | Procesal | 95124 | 150 | 99,8 % | 634,2x |
| 6841 | Pregunta: SENALE CUALES SON LAS REGLAS DE COMPETENCIA | Procesal | 95124 | 171 | 99,8 % | 556,3x |
| 6842 | Pregunta: SENALE LAS DIFERENCIAS ENTRE JURISDICCION Y | Procesal | 95124 | 163 | 99,8 % | 583,6x |
| 6843 | Pregunta: SENALE Y EXPLIQUE LOS PRINCIPIOS FORMATIVOS | Procesal | 95124 | 166 | 99,8 % | 573,0x |
| 6844 | Pregunta: gEN QUE CASOS HABRA SIEMPRE JUSTO MOTIVO? | Procesal | 95124 | 145 | 99,8 % | 656,0x |
| 6845 | Pregunta: gPUEDE PEDIRSE AMPLIACION DE LA PRUEBA? | Procesal | 95124 | 166 | 99,8 % | 573,0x |
| 6846 | Pregunta:&COMO SE FALLAN LAS EXCEPCIONES DILATORIAS? | Procesal | 95124 | 183 | 99,8 % | 519,8x |
| 6847 | Pregunta:&QUE CONTIENE EL CUADERNO DE APREMIO? | Procesal | 95124 | 163 | 99,8 % | 583,6x |
| 6848 | Pregunta:&QUEDEBE CONTENERLA PARTE RESOLUTIVA DE UNA | Procesal | 95124 | 145 | 99,8 % | 656,0x |
| 6849 | Pregunta:&TIENE ALGON DERECHO EL EJECUTADO EN RELACION | Procesal | 95124 | 195 | 99,8 % | 487,8x |
| 6850 | Pregunta:CAPACIDADPROCESAL.QUIENESLA TIENEN? | Procesal | 95124 | 154 | 99,8 % | 617,7x |
| 6851 | Pregunta:EFECTOS DE LA RESERVA HECHA PORELEJECUTADO | Procesal | 95124 | 154 | 99,8 % | 617,7x |
| 6852 | Pregunta:FALLO QUE ACOGEELRECURSO DE CASACION CN LA | Procesal | 95124 | 166 | 99,8 % | 573,0x |
| 6853 | Pregunta:FORMA NORMAL DE TERMINAR LA UNICA,PRIMERA O | Procesal | 95124 | 145 | 99,8 % | 656,0x |
| 6854 | Pregunta:MANERAS DE TERMINAR ELRECURSO DE CASACION | Procesal | 95124 | 169 | 99,8 % | 562,9x |
| 6855 | Pregunta:PLAZOPARA CONTESTARLA DEMANDA O TERMINO DE | Procesal | 95124 | 161 | 99,8 % | 590,8x |
| 6856 | Pregunta:PLURALIDAD DE PARTES O LITIS CONSORCIO.CASOS | Procesal | 95124 | 162 | 99,8 % | 587,2x |
| 6857 | Pregunta:PUEDE HABER PRUEBA EN LA CASACION EN LA FORMA? | Procesal | 95124 | 163 | 99,8 % | 583,6x |
| 6858 | Pregunta:QUE ES ELDESISTIMIENTO DE LA APELACION? | Procesal | 95124 | 171 | 99,8 % | 556,3x |
| 6859 | Pregunta:QUE FACULTADES TIENE ELPATROCINANTE? | Procesal | 95124 | 159 | 99,8 % | 598,3x |
| 6860 | Pregunta:QUESONLAS MEDIDASPREJUDICIALES? | Procesal | 95124 | 179 | 99,8 % | 531,4x |
| 6861 | Pregunta:REQUISITOS DE LAS SENTENCIAS CONFIRMATORIAS | Procesal | 95124 | 159 | 99,8 % | 598,3x |
| 6862 | Pregunta:REQUISITOS PARA QUE PROCEDA LA ACCION DE COSA | Procesal | 95124 | 183 | 99,8 % | 519,8x |
| 6863 | Pregunta:TRAMITACION EN SEGUNDA INSTANCIA | Procesal | 95124 | 156 | 99,8 % | 609,8x |
| 6864 | Pregunta:Y SI SE TRATA DE UNA MEDIDA PREJUDICIALPRECAUTORIA, QUE REQUISITOS DEBEN CUMPLIRSE PARA | Procesal | 95124 | 183 | 99,8 % | 519,8x |
| 6865 | Programa de habilitación | Procesal | 66012 | 106 | 99,8 % | 622,8x |
| 6866 | Sección ID3-TAG | Penal | 57066 | 111 | 99,8 % | 514,1x |
| 6867 | Sección de control de grabación | Penal | 57066 | 91 | 99,8 % | 627,1x |
| 6868 | Separación judicial por su culpa y del matrimonio nulo | Civil | 36934 | 63 | 99,8 % | 586,3x |
| 6869 | Sii: etapa administrativa | Judicial | 62888 | 109 | 99,8 % | 577,0x |
| 6870 | TAN EXPRESAMENTE ORDENADOS PORLA LEY.Se trata | Procesal | 95124 | 167 | 99,8 % | 569,6x |
| 6871 | Tercera parte: extinción de las obligaciones | Civil | 75968 | 174 | 99,8 % | 436,6x |
| 6872 | Trato personalizado | Judicial | 53521 | 113 | 99,8 % | 473,6x |
| 6873 | Título 1, “Del procedimiento Concursal de Renegociación de la Persona Deudora”. El artículo 263, se refiere | Civil | 110175 | 211 | 99,8 % | 522,2x |
| 6874 | Título I del Libro III del CPC. (arts. 434 a 529 del Código citado), con las | Civil | 54173 | 102 | 99,8 % | 531,1x |
| 6875 | Título V del Código Orgánico de Tribunales, cuyo incumplimien- | Procesal | 66012 | 150 | 99,8 % | 440,1x |
| 6876 | Título V, “Del sello SERNAC135, del servicio de atención al cliente y del Sistema de | Civil | 110175 | 188 | 99,8 % | 586,0x |
| 6877 | Título XI: del pago de las deudas hereditarias y testamentarias (artículos 1354 a | Civil | 92843 | 214 | 99,8 % | 433,8x |
| 6878 | Título XXI: “DE LA ADMINISTRACIÓN DE LOS TUTORES Y CURADORES | Familia | 85324 | 132 | 99,8 % | 646,4x |
| 6879 | Título XXVI: “REGLAS ESPECIALES RELATIVAS A LA CURADURÍA DEL SORDO O | Familia | 85324 | 139 | 99,8 % | 613,8x |
| 6880 | Xxxxxx tribunal de juicio oral en lo penal de santiago | Penal | 57066 | 94 | 99,8 % | 607,1x |
| 6881 | capítulo III de la LMC, artículos 21 a 24, dentro de la regulación de la | Familia | 123490 | 202 | 99,8 % | 611,3x |
| 6882 | capítulo de nulidad denunciado, relativo a la infracción de los artí- | Judicial | 105809 | 182 | 99,8 % | 581,4x |
| 6883 | capítulo o norma que pugne con la nueva regulación contemplada en | Laboral | 98828 | 210 | 99,8 % | 470,6x |
| 6884 | capítulo, los remedios destinados a restar eficacia a aquellas actua- | Judicial | 64632 | 123 | 99,8 % | 525,5x |
| 6885 | parte actora llama «Hojas o Fichas de Enfermería», de la que aparece que | Judicial | 87950 | 178 | 99,8 % | 494,1x |
| 6886 | parte alguna del haber social a título de gananciales (art. 1782, inc. 1º). Así, por | Familia | 136567 | 208 | 99,8 % | 656,6x |
| 6887 | parte alguna en el bien) tiene sobre un inmueble de la herencia. Refiere Olavarría que | Civil | 92843 | 193 | 99,8 % | 481,1x |
| 6888 | parte cuando la complejidad del asunto así lo aconsejare. En con- | Familia | 97488 | 169 | 99,8 % | 576,9x |
| 6889 | parte de compañeros y compañeras de la escuela, en su propia familia | Penal | 86906 | 159 | 99,8 % | 546,6x |
| 6890 | parte de cooperación internacional. Por último, se obligan a reconocer | Judicial | 78893 | 167 | 99,8 % | 472,4x |
| 6891 | parte de la Convención de Belém do Pará | Penal | 86906 | 152 | 99,8 % | 571,8x |
| 6892 | parte de la Unidad de Sala, Causas y Cumplimiento a un administrativo | Familia | 97488 | 152 | 99,8 % | 641,4x |
| 6893 | parte de la comunidad jurídica o de los ciudadanos en general («control | Judicial | 92792 | 156 | 99,8 % | 594,8x |
| 6894 | parte de la universalidad jurídica al cesionario. Si bien existe consenso en doctrina que | Civil | 92843 | 217 | 99,8 % | 427,8x |
| 6895 | parte de la “Baja Edad Media” (siglos XII a XV),80 prevalecerá el Derecho consuetudinario | Civil | 90056 | 188 | 99,8 % | 479,0x |
| 6896 | parte de lo que el vendedor debe en ‘cumplimiento del contrato’, de acuerdo con los términos del artículo | Civil | 120848 | 182 | 99,8 % | 664,0x |
| 6897 | parte de los especialistas está de acuerdo en que nos encontramos ante una obra | Civil | 90056 | 184 | 99,8 % | 489,4x |
| 6898 | parte de los gananciales y, por lo mismo, sobre el bien afectado por el contrato nulo. El | Familia | 136567 | 224 | 99,8 % | 609,7x |
| 6899 | parte de los juzgadores es una ilusión, por el condicionamiento que se | Procesal | 86112 | 179 | 99,8 % | 481,1x |
| 6900 | parte de los miembros en ejercicio deducir dicho requerimiento”. La frase “a | General | 125500 | 208 | 99,8 % | 603,4x |
| 6901 | parte de los trabajadores y las trabajadoras de una empresa, cumpliendo | Laboral | 74025 | 185 | 99,8 % | 400,1x |
| 6902 | parte de otros instrumentos internacionales, a los que la Conven- | Judicial | 82507 | 157 | 99,8 % | 525,5x |
| 6903 | parte de su familia y amigos, habida consideración de las limitaciones | Judicial | 87950 | 169 | 99,8 % | 520,4x |
| 6904 | parte de su hermano, y no al dictarse la sentencia de alimentos. Por cierto, en caso de | Familia | 62470 | 120 | 99,8 % | 520,6x |
| 6905 | parte de su posesión, como es la posesión material del inmueble. A esa conclusión | Civil | 92843 | 210 | 99,8 % | 442,1x |
| 6906 | parte de sus funciones, retendrá también una parte proporcionada de su décima. / Si | Familia | 85324 | 209 | 99,8 % | 408,2x |
| 6907 | parte de un proceso permanente de acceso a información para la toma | Judicial | 87950 | 188 | 99,8 % | 467,8x |
| 6908 | parte de uno de los miembros de la comunidad hereditaria, de la cuota que a éste | Civil | 92843 | 218 | 99,8 % | 425,9x |
| 6909 | parte de él, en bienes determinados. Incluso, efectuada ésta, ella opera con efecto | Civil | 92843 | 179 | 99,8 % | 518,7x |
| 6910 | parte deben ponderar no sólo el desempeño del funcionario por un | Judicial | 54457 | 94 | 99,8 % | 579,3x |
| 6911 | parte debido a su historicismo característico, que los romanistas alemanes de principios | General | 129559 | 198 | 99,8 % | 654,3x |
| 6912 | parte del Comité de Derechos Económicos, Sociales y Culturales de las | Judicial | 81675 | 161 | 99,8 % | 507,3x |
| 6913 | parte del Derecho privado, dado que los sujetos de la relación jurídica laboral son | General | 129559 | 204 | 99,8 % | 635,1x |
| 6914 | parte del Imperio, como Capitanía General dependiente del Virreinato de Lima.119 Así | Civil | 90056 | 174 | 99,8 % | 517,6x |
| 6915 | parte del Poder Judicial y están encargados de resolver los conflictos | Laboral | 71986 | 114 | 99,8 % | 631,5x |
| 6916 | parte del contenido fijado por la ley o incorporar algún elemento accidental. En cambio, los | Civil | 110175 | 170 | 99,8 % | 648,1x |
| 6917 | parte del contenido personal del contrato de trabajo, específicamente | Laboral | 98828 | 152 | 99,8 % | 650,2x |
| 6918 | parte del crédito, se encuentran en igualdad de condiciones frente al deudor (sin | Civil | 75968 | 178 | 99,8 % | 426,8x |
| 6919 | parte del deudor o el depositario | Judicial | 89450 | 140 | 99,8 % | 638,9x |
| 6920 | parte del edificio, y la indemnización se dividirá entre todas ellas; a menos que se | Civil | 96458 | 221 | 99,8 % | 436,5x |
| 6921 | parte del empleador se ajusta o no a derecho. La premisa básica es la | Laboral | 98828 | 200 | 99,8 % | 494,1x |
| 6922 | parte del juicio sino que son arrastrados a él para el sólo efecto de | Familia | 65085 | 133 | 99,8 % | 489,4x |
| 6923 | parte del ordenamiento jurídico nacional, sólo en la medida que el Estado de Chile las | General | 129559 | 197 | 99,8 % | 657,7x |
| 6924 | parte del patrimonio de la persona que se obliga o que impone una obligación a un | Civil | 42954 | 79 | 99,8 % | 543,7x |
| 6925 | parte del perjuicio que se causó a éste, y afirmar por otra que no obstante haber sido | Civil | 96458 | 163 | 99,8 % | 591,8x |
| 6926 | parte del precio al contado, estipulándose que el saldo, será pagado en el plazo de tres | Civil | 118177 | 179 | 99,8 % | 660,2x |
| 6927 | parte del proyecto aprobado por ellas. En este último caso, se devolverá al Presidente | General | 125500 | 201 | 99,8 % | 624,4x |
| 6928 | parte del público, debe actuar de acuerdo al artículo 35 del | Familia | 26096 | 52 | 99,8 % | 501,8x |
| 6929 | parte del sujeto activo lo que constituye una diferencia muy relevante | Judicial | 78893 | 169 | 99,8 % | 466,8x |
| 6930 | parte del testador? | Civil | 92843 | 178 | 99,8 % | 521,6x |
| 6931 | parte del total de las virtudes, que tiene como objeto la distribución e intercambio de | General | 129559 | 205 | 99,8 % | 632,0x |
| 6932 | parte del trabajador durante la jornada de trabajo, siempre que —como | Laboral | 98828 | 183 | 99,8 % | 540,0x |
| 6933 | parte dispositiva, la Corte puede corregir los que advirtiere con ocasión | Procesal | 66012 | 102 | 99,8 % | 647,2x |
| 6934 | parte débil de la relación en el desarrollo de la tramitación del pro- | Familia | 65192 | 133 | 99,8 % | 490,2x |
| 6935 | parte débil de la relación procesal que mantendrá con el alimentante | Familia | 65192 | 100 | 99,8 % | 651,9x |
| 6936 | parte el derecho a la contraprestación”; El Código Civil peruano, por su parte, en su | Civil | 120848 | 195 | 99,8 % | 619,7x |
| 6937 | parte el inmueble hipotecado. De manera que si en la sucesión del deudor uno de los | Civil | 66868 | 132 | 99,8 % | 506,6x |
| 6938 | parte en cuanto a que no acepta la resolución del tribunal. Dicho re- | Laboral | 71986 | 115 | 99,8 % | 626,0x |
| 6939 | parte en el contrato. Jurídicamente, sólo intervendrían dos personas.319 Tampoco podría | Civil | 110175 | 197 | 99,8 % | 559,3x |
| 6940 | parte en el juicio, o a quienes no afecten sus resultados, se harán perso- | Judicial | 89450 | 153 | 99,8 % | 584,6x |
| 6941 | parte manifestándole su intención de no renovar el contrato, con una | Judicial | 92792 | 205 | 99,8 % | 452,6x |
| 6942 | parte o de oficio y sin necesidad de audiencia, imponer al deudor como | Judicial | 89450 | 210 | 99,8 % | 426,0x |
| 6943 | parte o esté en mora de cumplirla o para obtener el pago de una indemnización | Civil | 120848 | 200 | 99,8 % | 604,2x |
| 6944 | parte para mejorar esas condiciones y reducir la sobreocupación de los | Judicial | 78893 | 139 | 99,8 % | 567,6x |
| 6945 | parte por revisar su contenido en el derecho internacional | Judicial | 87950 | 163 | 99,8 % | 539,6x |
| 6946 | parte que el sentido debe entenderse como la correspondencia o armonía entre la | General | 125500 | 206 | 99,8 % | 609,2x |
| 6947 | parte se obliga a entregar a la otra deben tener un valor que, al menos de manera | Civil | 90056 | 196 | 99,8 % | 459,5x |
| 6948 | parte éstos disponen de alguna de las mencionadas excepciones, para enervar la | Civil | 118177 | 183 | 99,8 % | 645,8x |
| 6949 | parte, ambos, de categorías contrapuestas y organizadas de interesados. Se recurre | Civil | 110175 | 189 | 99,8 % | 582,9x |
| 6950 | parte, con los modelos del noble sueño, la pesadilla y la vigilia de Hart | Judicial | 92792 | 188 | 99,8 % | 493,6x |
| 6951 | parte, cuando se habla de efectos del contrato respecto de terceros se quiere hacer referencia al hecho de que | Civil | 110175 | 166 | 99,8 % | 663,7x |
| 6952 | parte, el concepto de vida privada es un término amplio no susceptible | Judicial | 78893 | 166 | 99,8 % | 475,3x |
| 6953 | parte, el contexto de violencia y discriminación contra personas | Judicial | 87237 | 140 | 99,8 % | 623,1x |
| 6954 | parte, el estudio de Reyes indica que el 39% de las parejas de las mujeres | Penal | 86906 | 178 | 99,8 % | 488,2x |
| 6955 | parte, hay que tener presente el art. 12 del C.C. que prescribe que los derechos | Civil | 66868 | 124 | 99,8 % | 539,3x |
| 6956 | parte, igual que con las donaciones, herencias o legados, los acreedores | Familia | 123490 | 208 | 99,8 % | 593,7x |
| 6957 | parte, la referida norma nada dice sobre el deber de comparecencia de | Procesal | 86112 | 166 | 99,8 % | 518,7x |
| 6958 | parte, las atenciones12 en contexto de medidas cautelares ambulatorias | Penal | 86906 | 171 | 99,8 % | 508,2x |
| 6959 | parte, no tiene valor jurídico sino en la medida en que la ley así lo permita.100 | General | 129559 | 205 | 99,8 % | 632,0x |
| 6960 | parte, obsta al ejercicio de la corresponsabilidad parental, vale decir, a | Laboral | 98828 | 178 | 99,8 % | 555,2x |
| 6961 | parte, y se sustanciará de acuerdo con las normas del procedimiento | Laboral | 74025 | 149 | 99,8 % | 496,8x |
| 6962 | parte. B) En aquellas en que se aprueban las condiciones de una sus- | Penal | 86906 | 197 | 99,8 % | 441,1x |
| 6963 | parte: “El administrador tendrá las funciones que se establezcan en el reglamento de | Civil | 110175 | 200 | 99,8 % | 550,9x |
| 6964 | parte: “Para la determinación de los herederos del causante, el Servicio de Registro | Civil | 92843 | 205 | 99,8 % | 452,9x |
| 6965 | parte; disponer de ese derecho a cualquier título, total o parcialmente; y | Judicial | 81675 | 141 | 99,8 % | 579,3x |
| 6966 | parte”.127 | Civil | 120848 | 183 | 99,8 % | 660,4x |
| 6967 | sección o unidad, en la que mensualmente van realizando las | Judicial | 52128 | 87 | 99,8 % | 599,2x |
| 6968 | sección primera, página 73”.123 | Civil | 75968 | 150 | 99,8 % | 506,5x |
| 6969 | sumario ante el tribunal que conoce o debiera conocer de los procesos | Judicial | 64632 | 114 | 99,8 % | 566,9x |
| 6970 | sumario y se iniciaba caso que en ella podía pedirse la absolución del acusado o bien la | Penal | 57066 | 97 | 99,8 % | 588,3x |
| 6971 | sumario, y que constaban todas en un expediente foliado, podían ser | Penal | 57066 | 115 | 99,8 % | 496,2x |
| 6972 | título VI del libro I del Código de Procedimiento Civil, título en el cual | Judicial | 89450 | 184 | 99,8 % | 486,1x |
| 6973 | título VIII del libro II de este código (Del maltrato a menores | Judicial | 82507 | 148 | 99,8 % | 557,5x |
| 6974 | título a gozar de todos los derechos económicos, sociales y culturales | Judicial | 81675 | 159 | 99,8 % | 513,7x |
| 6975 | título de crédito mercantil, de los regulados en la Ley Nº 18.092, conforme lo dispone | Civil | 75968 | 159 | 99,8 % | 477,8x |
| 6976 | título de crédito). Algo semejante puede decirse respecto de los elementos de | Civil | 96458 | 214 | 99,8 % | 450,7x |
| 6977 | título de indemnización de perjuicios a favor de la víctima (artículo 238 | Penal | 86906 | 188 | 99,8 % | 462,3x |
| 6978 | título de legítimas. 18 | Civil | 23185 | 39 | 99,8 % | 594,5x |
| 6979 | título gratuito? Refiérase al fundamento de la doctrina tradicional y al planteado por los | Civil | 92843 | 205 | 99,8 % | 452,9x |
| 6980 | título injusto, como sería el falsificado o el otorgado por una persona en calidad de | Civil | 36671 | 85 | 99,8 % | 431,4x |
| 6981 | título la autorización del cónyuge no propietario o de la justicia en subsidio. En el | General | 59520 | 139 | 99,8 % | 428,2x |
| 6982 | título oneroso, única regida por los arts. 1909 y 1910. En cambio, si la cesión fuere a | Civil | 92843 | 180 | 99,8 % | 515,8x |
| 6983 | título para inscribir los derechos reales y la prohibición de enajenar o gravar en los registros | Familia | 81198 | 191 | 99,8 % | 425,1x |
| 6984 | título que determina el estado civil.87 | Familia | 65085 | 98 | 99,8 % | 664,1x |
| 6985 | título que los ciudadanos.30 | Civil | 90056 | 159 | 99,8 % | 566,4x |
| 6986 | título singular” (arts. 1104 a 1135); (vii) “De las donaciones revocables” (arts. 1136 a | Civil | 50203 | 105 | 99,8 % | 478,1x |
| 6987 | título universal se mira como una institución de heredero (art. 1142) y sólo tiene | Civil | 92843 | 201 | 99,8 % | 461,9x |
| 6988 | título, con la sola limitación de que dichos bienes no pasen al dominio | Laboral | 74025 | 119 | 99,8 % | 622,1x |
| 6989 | título, ocupen las unidades, sean copropietarios, o titulares de otros derechos reales o | Civil | 49700 | 80 | 99,8 % | 621,2x |
| 6990 | /DFDVDFL®QHQODIRUPDGHRůFLR | Procesal | 66012 | 209 | 99,7 % | 315,8x |
| 6991 | /DQXOLGDGGHRůFLR | Procesal | 66012 | 171 | 99,7 % | 386,0x |
| 6992 | 1 Andrea González Schmessane, «Termina juicio de chilenos en España: “Viva | Judicial | 62514 | 165 | 99,7 % | 378,9x |
| 6993 | 1 Dieciocho y no diez, como erradamente afirman Carreta y Barcia (2019). La | Constitucional | 46896 | 143 | 99,7 % | 327,9x |
| 6994 | 1 En el Sistema Interamericano artículo 1.1 de la Convención Americana sobre | Penal | 51155 | 174 | 99,7 % | 294,0x |
| 6995 | 1. A los pueblos tribales en países independientes, cuyas condiciones | Judicial | 60665 | 161 | 99,7 % | 376,8x |
| 6996 | 1. Artex. Es un redactor asistido para el español que revisa textos de | Judicial | 30834 | 88 | 99,7 % | 350,4x |
| 6997 | 1. Contacto. Su finalidad es acercarse a la persona que expresa enfado | Judicial | 53521 | 172 | 99,7 % | 311,2x |
| 6998 | 1. Cuando la sentencia hubiere sido pronunciada por un tribunal incom- | Procesal | 66012 | 188 | 99,7 % | 351,1x |
| 6999 | 1. Derecho a ser atendida. La víctima de un delito tiene derecho a ser | Penal | 51155 | 139 | 99,7 % | 368,0x |
| 7000 | 1. Eliminar cualquier trato discriminatorio en contra de las personas | Judicial | 53521 | 166 | 99,7 % | 322,4x |
| 7001 | 1. Generar conciencia en la institución respecto de la importancia del | Judicial | 53521 | 139 | 99,7 % | 385,0x |
| 7002 | 1. Infraestructura: Evaluar los riesgos a que se enfrentan las mujeres que | Judicial | 53521 | 172 | 99,7 % | 311,2x |
| 7003 | 1. Los Estados partes respetarán los derechos enunciados en la presente | Constitucional | 44292 | 132 | 99,7 % | 335,5x |
| 7004 | 1. Observar los principios en todas las etapas del proceso en los que | Judicial | 53521 | 158 | 99,7 % | 338,7x |
| 7005 | 1. Prestar atención inmediata, integral, coordinada, interinstitucional y | Judicial | 53521 | 171 | 99,7 % | 313,0x |
| 7006 | 1. Que en el mes de septiembre de 1984 se derogó el artículo 16 de la | Judicial | 62514 | 192 | 99,7 % | 325,6x |
| 7007 | 1. Quien lleva adelante la ejecución es un acreedor prendario, y existen otros | Civil | 54173 | 182 | 99,7 % | 297,7x |
| 7008 | 1. Resolver y pronunciarse en única instancia sobre las causas que | Judicial | 52128 | 143 | 99,7 % | 364,5x |
| 7009 | 1. Se procurará incorporar el Código de conducta a la legislación y a | Penal | 51155 | 166 | 99,7 % | 308,2x |
| 7010 | 1. Tratándose de Cortes de Apelaciones que funcionen en más de | Judicial | 44331 | 124 | 99,7 % | 357,5x |
| 7011 | 1. Usar un lenguaje no ofensivo y no discriminatorio para referirse a las | Judicial | 53521 | 158 | 99,7 % | 338,7x |
| 7012 | 1.1    Definición | Judicial | 39447 | 102 | 99,7 % | 386,7x |
| 7013 | 1.1. CADH, conforme al juicio de proporcionalidad en sentido es- | Laboral | 53374 | 169 | 99,7 % | 315,8x |
| 7014 | 1.1.1 Jefe de Unidad de Sala | Familia | 26096 | 81 | 99,7 % | 322,2x |
| 7015 | 1.2. Como la ley no efectúa tal distinción, resulta que la inscripción, cuando se invoca | Civil | 36671 | 106 | 99,7 % | 346,0x |
| 7016 | 1.2. Gastos correspondientes a las expensas extraordinarias: serán también de cargo | Familia | 62470 | 192 | 99,7 % | 325,4x |
| 7017 | 1.2.1 Clasificación por número de | Judicial | 44331 | 128 | 99,7 % | 346,3x |
| 7018 | 1.3    Administrador | Judicial | 39447 | 110 | 99,7 % | 358,6x |
| 7019 | 1.4.1 Con la Corte Suprema | Judicial | 44331 | 113 | 99,7 % | 392,3x |
| 7020 | 1.4.2 Con los juzgados de primera instancia | Judicial | 44331 | 117 | 99,7 % | 378,9x |
| 7021 | 1.4.3 Con la Corporación Administrativa | Judicial | 44331 | 133 | 99,7 % | 333,3x |
| 7022 | 1.4.4 Con los centros y unidades de apoyo a tribunales | Judicial | 44331 | 128 | 99,7 % | 346,3x |
| 7023 | 1.8.1 Atención de público | Familia | 26096 | 66 | 99,7 % | 395,4x |
| 7024 | 10 El artículo 263 del Código de Procedimiento Civil, señala «El juez obrará como | Judicial | 42513 | 111 | 99,7 % | 383,0x |
| 7025 | 10. Dar cuenta al presidente de la CS de las causas en que no se haya | Judicial | 54457 | 182 | 99,7 % | 299,2x |
| 7026 | 10. Excepcionalidad en la detención: Las prácticas migratorias deben | Judicial | 53521 | 166 | 99,7 % | 322,4x |
| 7027 | 10. Que la referida conclusión se desprende de la circunstancia que el | Judicial | 62514 | 175 | 99,7 % | 357,2x |
| 7028 | 11 La Cámara de origen remitió el proyecto a la Comisión de Hacienda, la que | Judicial | 62888 | 189 | 99,7 % | 332,7x |
| 7029 | 11 Nótese que, a diferencia del artículo 5, letra a, el 5, letra b, añade como elemento | Judicial | 62514 | 204 | 99,7 % | 306,4x |
| 7030 | 11. Corte de Chillán comprende la Región de Ñuble (Decimosexta) | Judicial | 44331 | 115 | 99,7 % | 385,5x |
| 7031 | 11. No revictimización: Desde los estudios del Derecho Penal y las | Judicial | 53521 | 187 | 99,7 % | 286,2x |
| 7032 | 12 Sin perjuicio de ello, nada impediría que, eventualmente, se elevase la pena si se | Judicial | 62514 | 171 | 99,7 % | 365,6x |
| 7033 | 12. Interseccionalidad: Es una herramienta metodológica que permite | Judicial | 53521 | 167 | 99,7 % | 320,5x |
| 7034 | 124. El Comité recomienda que el Estado parte adopte el paradigma de | Constitucional | 46896 | 124 | 99,7 % | 378,2x |
| 7035 | 13 Artículo 2 Convención Belém do Pará: «Se entenderá que violencia contra la | Laboral | 53374 | 174 | 99,7 % | 306,7x |
| 7036 | 13 El nuevo artículo 251 bis reza: «El que, con el propósito de obtener o mantener | Judicial | 62514 | 180 | 99,7 % | 347,3x |
| 7037 | 13 Leighton Puga (1966: 62) señala que el modelo que siguió el legislador fue la ley | Judicial | 62888 | 179 | 99,7 % | 351,3x |
| 7038 | 13 Para más información, véase «Historia de la Ley 19.027», disponible en https:// | Judicial | 62514 | 180 | 99,7 % | 347,3x |
| 7039 | 13. Garantizar que se cumplan los siguientes derechos al acceder a la | Judicial | 53521 | 146 | 99,7 % | 366,6x |
| 7040 | 14 Artículo 9 de la Constitución. El terrorismo, en cualquiera de sus formas, es | Judicial | 62514 | 204 | 99,7 % | 306,4x |
| 7041 | 14 La Dirección del Trabajo, a través del dictamen 2856/162 del 30 de agosto de | Laboral | 53374 | 179 | 99,7 % | 298,2x |
| 7042 | 14.4. Los instrumentos privados.40 | Procesal | 24749 | 66 | 99,7 % | 375,0x |
| 7043 | 1464 N° 3 del Código Civil). También deberá cerciorarse el notario que el arrendador | Civil | 71319 | 198 | 99,7 % | 360,2x |
| 7044 | 15 Como consecuencia de la crisis, en noviembre de 1981, la Superintendencia de | Judicial | 62888 | 175 | 99,7 % | 359,4x |
| 7045 | 15.2. Presunciones para probar la posesión | Civil | 36671 | 127 | 99,7 % | 288,7x |
| 7046 | 16 Proyecto de Ley, en segundo trámite, que modifica la Ley 20.285 sobre Acceso | Judicial | 30834 | 87 | 99,7 % | 354,4x |
| 7047 | 17 D). De esta manera, cuatro obligaciones de hacer tiene el acreedor hipotecario, una | Civil | 66868 | 205 | 99,7 % | 326,2x |
| 7048 | 170 Nº 5 del CPC, que consagra el principio de inexcusabilidad. El | Judicial | 54457 | 141 | 99,7 % | 386,2x |
| 7049 | 1853. Su art. 822 señalaba que la tradición podía ser real o simbólica. El art. 823 | General | 59520 | 202 | 99,7 % | 294,7x |
| 7050 | 19 En este sentido, el Comité ha observado: «Los Estados parte deben velar por | Judicial | 62514 | 165 | 99,7 % | 378,9x |
| 7051 | 1991. En efecto, dado que esta modificación trajo consigo la exigencia de | Judicial | 62514 | 213 | 99,7 % | 293,5x |
| 7052 | 1994. Lo anterior también fue marcado por las protestas en torno a la | Judicial | 60665 | 162 | 99,7 % | 374,5x |
| 7053 | 2 Artículo 73.«Se aplicará asimismo la pena inferior en uno, dos o tres grados al | Penal | 51155 | 167 | 99,7 % | 306,3x |
| 7054 | 2 Solo a modo de ejemplo podemos citar Corte Suprema, 4 de junio de 2019, rol | Constitucional | 46896 | 154 | 99,7 % | 304,5x |
| 7055 | 2. Carácter dinámico de la comunicación | Judicial | 53521 | 158 | 99,7 % | 338,7x |
| 7056 | 2. Considerar que la violencia contra las mujeres puede generar en las | Judicial | 53521 | 167 | 99,7 % | 320,5x |
| 7057 | 2. Cuando un niño sea privado ilegalmente de algunos de los elementos de su | Familia | 62470 | 202 | 99,7 % | 309,3x |
| 7058 | 2. Estilector. Inicialmente fue un programa de ayuda para la redacción | Judicial | 30834 | 92 | 99,7 % | 335,2x |
| 7059 | 2. Evitar incurrir en tratos discriminatorios por el hecho de asumir la | Judicial | 53521 | 161 | 99,7 % | 332,4x |
| 7060 | 2. La grabación de audiencias se debe realizar de acuerdo con el | Judicial | 44331 | 122 | 99,7 % | 363,4x |
| 7061 | 2. Moderar. En algunos casos, cuando los equipos están en una etapa | Judicial | 29920 | 101 | 99,7 % | 296,2x |
| 7062 | 2. Para los equipos de trabajo | Judicial | 29920 | 97 | 99,7 % | 308,5x |
| 7063 | 2. Principio de enfoque de género en el acceso a la justicia. Entendido | Judicial | 53521 | 180 | 99,7 % | 297,3x |
| 7064 | 2. Si no existe instrumento colectivo anterior, la vigencia se contará a | Laboral | 74025 | 196 | 99,7 % | 377,7x |
| 7065 | 2. Velar por una protección efectiva a las víctimas | Judicial | 53521 | 174 | 99,7 % | 307,6x |
| 7066 | 2.1.1 Jefe de la Unidad de Atención de Público y Servicios | Judicial | 39447 | 111 | 99,7 % | 355,4x |
| 7067 | 2.1.2 Administrativo de Atención de Público | Judicial | 39447 | 110 | 99,7 % | 358,6x |
| 7068 | 2.1.3 Administrativo Contable | Judicial | 39447 | 107 | 99,7 % | 368,7x |
| 7069 | 2.1.4 Administrativo Informático | Judicial | 39447 | 104 | 99,7 % | 379,3x |
| 7070 | 2.1.5 Asistente Administrativo | Judicial | 39447 | 101 | 99,7 % | 390,6x |
| 7071 | 2.2. asignaciones a titulo universal o herencias. 1 | Civil | 16643 | 42 | 99,7 % | 396,3x |
| 7072 | 2.2.1 Jefe de la Unidad de Sala | Judicial | 39447 | 101 | 99,7 % | 390,6x |
| 7073 | 2.2.2 Encargado de Sala | Judicial | 39447 | 110 | 99,7 % | 358,6x |
| 7074 | 2.2.3 Administrativo de Acta | Judicial | 39447 | 113 | 99,7 % | 349,1x |
| 7075 | 2.2.4 Ayudante de Sala | Judicial | 39447 | 110 | 99,7 % | 358,6x |
| 7076 | 2.2.5 Administrativo de Notificación | Judicial | 39447 | 111 | 99,7 % | 355,4x |
| 7077 | 2.2.6 Notificador | Judicial | 39447 | 101 | 99,7 % | 390,6x |
| 7078 | 2.3.1 Jefe de la Unidad de Causas | Judicial | 39447 | 114 | 99,7 % | 346,0x |
| 7079 | 2.3.3 Administrativo de Causas | Judicial | 39447 | 113 | 99,7 % | 349,1x |
| 7080 | 2.3.4 Ayudante de Causas | Judicial | 39447 | 104 | 99,7 % | 379,3x |
| 7081 | 2.4.1 Jefe de la Unidad de Cumplimiento | Judicial | 39447 | 102 | 99,7 % | 386,7x |
| 7082 | 2.4.2 Administrativo de Cumplimiento | Judicial | 39447 | 110 | 99,7 % | 358,6x |
| 7083 | 2.4.2 Ingreso de escritos e informes | Judicial | 44331 | 119 | 99,7 % | 372,5x |
| 7084 | 2.5.4.2 Incumplimiento del padre custodio | Familia | 65192 | 166 | 99,7 % | 392,7x |
| 7085 | 20.190. Su art. 5 dispone que podrá constituirse prenda sobre todo tipo de cosas | Civil | 54173 | 188 | 99,7 % | 288,2x |
| 7086 | 2011. Cuarto: Que se hace necesario entonces determinar los efectos jurídicos | Civil | 66868 | 209 | 99,7 % | 319,9x |
| 7087 | 22. Esta resolución deberá individualizar de forma completa a la persona que registre deudas | Familia | 81198 | 206 | 99,7 % | 394,2x |
| 7088 | 2358 Nº 4).15 | Civil | 25022 | 65 | 99,7 % | 385,0x |
| 7089 | 25 En contra, Villegas ha sostenido que: «El hecho de que el terrorismo necesite | Judicial | 62514 | 166 | 99,7 % | 376,6x |
| 7090 | 28 Para más información, véase «Historia de la Ley 20.467», disponible en https:// | Judicial | 62514 | 205 | 99,7 % | 304,9x |
| 7091 | 3 Los principales objetivos de este primer proyecto fueron los siguientes: i) gravar | Judicial | 62888 | 174 | 99,7 % | 361,4x |
| 7092 | 3 Sin perjuicio de su posterior análisis, estas modificaciones son las siguientes: i) | Judicial | 62514 | 175 | 99,7 % | 357,2x |
| 7093 | 3.   Acuerdo reparatorio: Trato al que llegan el impu-       14. Ejecutoriada: Cuando han finalizado todos los | Judicial | 39447 | 109 | 99,7 % | 361,9x |
| 7094 | 3. A los egresados de los recintos carcelarios en los casos que la ley | Penal | 51155 | 169 | 99,7 % | 302,7x |
| 7095 | 3. Actos o resoluciones que denieguen total o parcialmente las solici- | Judicial | 62888 | 197 | 99,7 % | 319,2x |
| 7096 | 3. Articulación interna. Referida a la coordinación que debe existir | Judicial | 53521 | 169 | 99,7 % | 316,7x |
| 7097 | 3. Clara. Se trata de una aplicación disponible en la web que permite | Judicial | 30834 | 83 | 99,7 % | 371,5x |
| 7098 | 3. Considerar en todos los asuntos en los que intervengan mujeres | Judicial | 53521 | 163 | 99,7 % | 328,3x |
| 7099 | 3. En buena medida la validación y credibilidad de retroalimentar se | Judicial | 29920 | 98 | 99,7 % | 305,3x |
| 7100 | 3. Entorpecimiento laboral: toda acción tendiente a obstaculizar el | Laboral | 53293 | 153 | 99,7 % | 348,3x |
| 7101 | 3. Factores que intervienen en la comunicación | Judicial | 53521 | 135 | 99,7 % | 396,5x |
| 7102 | 3. Migración internacional: Movimiento de personas que dejan su país | Judicial | 53521 | 163 | 99,7 % | 328,3x |
| 7103 | 3. Por haber dejado de cumplir con los requisitos necesarios para su | Laboral | 74025 | 215 | 99,7 % | 344,3x |
| 7104 | 3. Si la intervención en un caso de protección administrativa universal | Constitucional | 46896 | 148 | 99,7 % | 316,9x |
| 7105 | 3. Traslado a lugar tranquilo. Solo efectuar en el caso que el tribunal | Judicial | 53521 | 178 | 99,7 % | 300,7x |
| 7106 | 3.1.2 Recepción de escritos materiales y correspondencia | Judicial | 39447 | 102 | 99,7 % | 386,7x |
| 7107 | 3.2.1 Tramitación de solicitudes | Judicial | 39447 | 132 | 99,7 % | 298,8x |
| 7108 | 3.2.3 Solicitud de una forma especial de notificación | Judicial | 39447 | 101 | 99,7 % | 390,6x |
| 7109 | 3.3.1 Normalización de la circulación y espera | Judicial | 39447 | 107 | 99,7 % | 368,7x |
| 7110 | 3.3.1.1 Rol del fiscal en la tramitación de los juicios o “vis- | Judicial | 54457 | 140 | 99,7 % | 389,0x |
| 7111 | 3.3.1.2 Fiscales judiciales como miembros e integrantes | Judicial | 54457 | 145 | 99,7 % | 375,6x |
| 7112 | 3.3.3 Funciones dispuestas por | Judicial | 54457 | 150 | 99,7 % | 363,0x |
| 7113 | 3.3.3 Preparación y desarrollo de audiencias | Judicial | 39447 | 117 | 99,7 % | 337,2x |
| 7114 | 3.3.4.1 Las visitas de cárcel | Judicial | 54457 | 152 | 99,7 % | 358,3x |
| 7115 | 3.4.1 Ejecución de sentencias y envío de oficios | Judicial | 39447 | 119 | 99,7 % | 331,5x |
| 7116 | 3.5.2 Certificación de depósitos y giro de cheques | Judicial | 39447 | 104 | 99,7 % | 379,3x |
| 7117 | 3.6.1 En general | Judicial | 39447 | 101 | 99,7 % | 390,6x |
| 7118 | 3.6.2 En particular | Judicial | 39447 | 111 | 99,7 % | 355,4x |
| 7119 | 33 Con respecto a este último —delito de tendencia interna trascendente— parte | Judicial | 62514 | 174 | 99,7 % | 359,3x |
| 7120 | 348 CPP y artículo 41 de la Ley Nº 20.084, de las comunicaciones | Judicial | 39447 | 113 | 99,7 % | 349,1x |
| 7121 | 35. Del expediente de este caso surge que el 24 de agosto de 1994 no | Penal | 51155 | 178 | 99,7 % | 287,4x |
| 7122 | 4. El derecho a la vida digna, supervivencia y desarrollo: Garantizarlo | Judicial | 53521 | 182 | 99,7 % | 294,1x |
| 7123 | 4. Estereotipos de género: Generalizaciones preconcebidas a partir de | Judicial | 53521 | 165 | 99,7 % | 324,4x |
| 7124 | 4. Evaluar a partir de datos tales como lugar de origen, idioma de | Judicial | 53521 | 180 | 99,7 % | 297,3x |
| 7125 | 4. Ponga especial atención al contenido de lo que está manifestando | Judicial | 29920 | 89 | 99,7 % | 336,2x |
| 7126 | 4. Protección especial a sus territorios y recursos naturales: Es uno de | Judicial | 53521 | 170 | 99,7 % | 314,8x |
| 7127 | 4. Retroalimentación. La persona encargada de realizar la evaluación | Judicial | 29920 | 76 | 99,7 % | 393,7x |
| 7128 | 4. Todo el sistema del Código tiende a que los inmuebles se incorporen al régimen | Civil | 36671 | 122 | 99,7 % | 300,6x |
| 7129 | 4.2.1 Administración de los recursos jurisdiccionales | Judicial | 44331 | 117 | 99,7 % | 378,9x |
| 7130 | 4.2.3 Ingreso y tramitación de causas desde la | Judicial | 44331 | 113 | 99,7 % | 392,3x |
| 7131 | 4.3 No es susceptible de sujetarse a modalidades o gravámenes, salvo las excepciones | Civil | 23185 | 75 | 99,7 % | 309,1x |
| 7132 | 4.3.1 Recurso de amparo | Judicial | 44331 | 128 | 99,7 % | 346,3x |
| 7133 | 4.3.2 Recurso de protección | Judicial | 44331 | 127 | 99,7 % | 349,1x |
| 7134 | 4.3.3 Recurso de apelación | Judicial | 44331 | 128 | 99,7 % | 346,3x |
| 7135 | 4.3.3.1 Tramitación ante el tribunal “a quo” (el | Judicial | 44331 | 126 | 99,7 % | 351,8x |
| 7136 | 4.3.3.2 Tramitación ante el tribunal | Judicial | 44331 | 118 | 99,7 % | 375,7x |
| 7137 | 4.3.4 Recurso de hecho | Judicial | 44331 | 127 | 99,7 % | 349,1x |
| 7138 | 4.3.5 Recurso de casación en la forma | Judicial | 44331 | 117 | 99,7 % | 378,9x |
| 7139 | 4.3.7 Recurso de queja | Judicial | 44331 | 146 | 99,7 % | 303,6x |
| 7140 | 5 Así se reconoció en la décima cuarta sesión de la Cámara de Diputados el 7 de | Judicial | 62888 | 169 | 99,7 % | 372,1x |
| 7141 | 5. Casos en que los acreedores hereditarios y testamentarios no pueden solicitar el | Civil | 21170 | 57 | 99,7 % | 371,4x |
| 7142 | 5. Comunicación institucional | Judicial | 53521 | 166 | 99,7 % | 322,4x |
| 7143 | 5. Cuando, en la sentencia, se hubiere omitido alguno de los requisitos | Procesal | 66012 | 185 | 99,7 % | 356,8x |
| 7144 | 5. Derecho a solicitar protección. La víctima de un delito tiene derecho | Penal | 51155 | 163 | 99,7 % | 313,8x |
| 7145 | 5. El registro parcial en que debe hacerse la inscripción y el número que en él le | General | 59520 | 165 | 99,7 % | 360,7x |
| 7146 | 5. Entendiendo que existe una precondición de vulnerabilidad del | Judicial | 53521 | 171 | 99,7 % | 313,0x |
| 7147 | 5. Iniquidad laboral: excesivas sobrecargas de trabajo; asignación de | Laboral | 53293 | 140 | 99,7 % | 380,7x |
| 7148 | 5. La clase o denominación de sindicato que lo identifique, la que no | Laboral | 74025 | 206 | 99,7 % | 359,3x |
| 7149 | 5. Para reuniones no autorizadas, pero de carácter no violento, los | Penal | 51155 | 137 | 99,7 % | 373,4x |
| 7150 | 5. Participación, consulta y consentimiento frente a cualquier acción | Judicial | 53521 | 162 | 99,7 % | 330,4x |
| 7151 | 5. Preguntar a la persona con discapacidad cuál es la forma o el medio | Judicial | 53521 | 169 | 99,7 % | 316,7x |
| 7152 | 5. Respeto a la dignidad inherente, autonomía individual, libertad para | Judicial | 53521 | 158 | 99,7 % | 338,7x |
| 7153 | 5.1 Debe tratarse de na herencia en la q e se apliq en las reglas de la s cesión | Civil | 36934 | 104 | 99,7 % | 355,1x |
| 7154 | 5.2. Constitución de derechos reales de goce | Familia | 44766 | 120 | 99,7 % | 373,1x |
| 7155 | 5.2.3 Vista de las causas | Judicial | 44331 | 124 | 99,7 % | 357,5x |
| 7156 | 5.3. Que la promesa contenga un plazo o condición que fije la época de la celebración | Civil | 29257 | 79 | 99,7 % | 370,3x |
| 7157 | 5.4 Sanción por la infracción de la promesa | Civil | 23185 | 58 | 99,7 % | 399,7x |
| 7158 | 5.4. Que en la promesa se especifique de tal manera el contrato prometido, que sólo | Civil | 29257 | 100 | 99,7 % | 292,6x |
| 7159 | 55    La sentencia de la Corte Suprema, rol N° 42.527-2017, de 12 de abril de 2018, reconoce expresamente este | Penal | 72395 | 185 | 99,7 % | 391,3x |
| 7160 | 6 Además de las convenciones que se refieren particularmente a la eliminación de | Laboral | 53374 | 162 | 99,7 % | 329,5x |
| 7161 | 6. Cuando la sentencia se hubiere dictado con infracción de lo prescrito | Procesal | 66012 | 171 | 99,7 % | 386,0x |
| 7162 | 6. Cuatro ejes estratégicos: i) No discriminación de género; ii) enfo- | Judicial | 23342 | 70 | 99,7 % | 333,5x |
| 7163 | 6. Por tener alguno de los abogados otra vista o comparecencia | Judicial | 54457 | 140 | 99,7 % | 389,0x |
| 7164 | 6. Respetar la autonomía de los pueblos indígenas, en el ámbito de sus | Judicial | 53521 | 158 | 99,7 % | 338,7x |
| 7165 | 6. Verbal o lingüística/ no verbal o no lingüística. La comunicación | Judicial | 53521 | 170 | 99,7 % | 314,8x |
| 7166 | 6.2. No es efectivo que el problema de la responsabilidad se simplifique por el hecho de | Civil | 26055 | 66 | 99,7 % | 394,8x |
| 7167 | 6.4. La teoría del riesgo, lejos de extender el ámbito de la responsabilidad y de contribuir a | Civil | 26055 | 70 | 99,7 % | 372,2x |
| 7168 | 69 COT), salvo en caso de que se hubiera producido la radicación | Judicial | 44331 | 120 | 99,7 % | 369,4x |
| 7169 | 690. Esta escritura rectificará y complementará aquella que fue objetada, de manera | General | 59520 | 198 | 99,7 % | 300,6x |
| 7170 | 7 Dictamen contra Chile por situación de niños y niñas en residencias 1 de junio | Constitucional | 46896 | 119 | 99,7 % | 394,1x |
| 7171 | 7 Las seis categorías de renta fueron las siguientes: i) renta de los bienes raíces; ii) | Judicial | 62888 | 185 | 99,7 % | 339,9x |
| 7172 | 7 Para más información, véase «Historia de la Ley 19.906», p. 48, disponible en | Judicial | 62514 | 180 | 99,7 % | 347,3x |
| 7173 | 7 Tales delitos, de acuerdo con el artículo segundo la Ley 18.314, son actualmente | Judicial | 62514 | 211 | 99,7 % | 296,3x |
| 7174 | 7. Identificar si el asunto del que se está en conocimiento, involucra el | Judicial | 53521 | 169 | 99,7 % | 316,7x |
| 7175 | 7. Mujer víctima directa: Aquella mujer de cualquier edad que sufra el | Judicial | 53521 | 140 | 99,7 % | 382,3x |
| 7176 | 7. Por ordenarlo así el tribunal, por resolución fundada, al disponer | Judicial | 54457 | 149 | 99,7 % | 365,5x |
| 7177 | 7. Respeto por la diferencia. Implica la aceptación de la discapacidad | Judicial | 53521 | 171 | 99,7 % | 313,0x |
| 7178 | 7.8. Por la cesación de las funciones del mandante si el mandato ha sido dado en ejercicio | Civil | 42773 | 115 | 99,7 % | 371,9x |
| 7179 | 768 N°s. 1 a 8 del CPC) y en vicios ocurridos durante la sustanciación | Procesal | 66012 | 222 | 99,7 % | 297,4x |
| 7180 | 8 Artículo 14: «Debido proceso y especialización. El Estado velará por asegurar | Constitucional | 46896 | 130 | 99,7 % | 360,7x |
| 7181 | 8 Sentencia de ministro en visita extraordinaria Villavicencio, rol 15.236, del 1 de | Judicial | 62514 | 183 | 99,7 % | 341,6x |
| 7182 | 8. Cierre. El objetivo es lograr reunir a la persona rápidamente con | Judicial | 53521 | 183 | 99,7 % | 292,5x |
| 7183 | 8. Conocer y declarar, a petición de parte, la nulidad de los actos admi- | Judicial | 62888 | 161 | 99,7 % | 390,6x |
| 7184 | 9 El artículo 64 de la Ley 19.968 permite el interrogatorio de las partes tras la | Procesal | 86112 | 222 | 99,7 % | 387,9x |
| 7185 | 9 En la década de 1920, el doctor Edwin Kemmerer, profesor de Economía de la | Judicial | 62888 | 175 | 99,7 % | 359,4x |
| 7186 | 9 Por ejemplo: artículo 3 de la Ley 26.061 (Argentina), artículo 8 del Código de la | Constitucional | 46896 | 143 | 99,7 % | 327,9x |
| 7187 | 9. Asegurar la atención de manera prioritaria a aquellas causas en que | Judicial | 53521 | 153 | 99,7 % | 349,8x |
| 7188 | 9. La indicación, cuando proceda, de que se trata de tierras indígenas de conformidad | General | 59520 | 198 | 99,7 % | 300,6x |
| 7189 | 9.2. Obligación de caucionar con un seguro o boleta bancaria, ciertos | Civil | 29257 | 80 | 99,7 % | 365,7x |
| 7190 | 996. El problema se plantea sobre la base de precisar en qué consiste “la porción que | Civil | 50203 | 174 | 99,7 % | 288,5x |
| 7191 | C.p.r.) | General | 21362 | 55 | 99,7 % | 388,4x |
| 7192 | Capitulo iii: concurrencia de los derechos anteriores con el derecho de | Civil | 20710 | 57 | 99,7 % | 363,3x |
| 7193 | Capitulo v: los extranjeros y la sucesion intestada | Civil | 36934 | 120 | 99,7 % | 307,8x |
| 7194 | Capitulo viii: las personas juridicas1 | General | 13045 | 36 | 99,7 % | 362,4x |
| 7195 | Contrato de hipoteca1 | Civil | 66868 | 170 | 99,7 % | 393,3x |
| 7196 | Contrato de prenda1 | Civil | 54173 | 176 | 99,7 % | 307,8x |
| 7197 | Contrato de promesa1 | Civil | 29257 | 75 | 99,7 % | 390,1x |
| 7198 | De la ley número 20.190 | Civil | 22583 | 74 | 99,7 % | 305,2x |
| 7199 | El contrato de mandato1 | Civil | 42773 | 145 | 99,7 % | 295,0x |
| 7200 | Ii. el beneficio de inventario, que invoca el heredero | Civil | 15693 | 44 | 99,7 % | 356,7x |
| 7201 | Ii.-   la accion reivindicatoria | General | 21362 | 70 | 99,7 % | 305,2x |
| 7202 | Iii    de las acciones posesorias | General | 21362 | 62 | 99,7 % | 344,5x |
| 7203 | Iii.- el pago | Civil | 75968 | 208 | 99,7 % | 365,2x |
| 7204 | Parte importante de la gestión del JG consiste en evitar al máximo | Judicial | 39447 | 113 | 99,7 % | 349,1x |
| 7205 | Parte”. Agrega el Decreto “Que los documentos públicos otorgados por un Estado Parte | General | 59520 | 179 | 99,7 % | 332,5x |
| 7206 | Procedimiento administrativo de rectificación de la inscripción | General | 17306 | 55 | 99,7 % | 314,7x |
| 7207 | Referencias bibliográficas | Judicial | 30834 | 100 | 99,7 % | 308,3x |
| 7208 | Sección 2ª.- Comprensión de actuaciones judiciales | Judicial | 42513 | 141 | 99,7 % | 301,5x |
| 7209 | Segunda parte: la sucesion intestada1 | Civil | 36934 | 113 | 99,7 % | 326,8x |
| 7210 | Sumario: 1.- Generalidades. 2.- Definición de comunidad y de copropiedad. 3.- | Civil | 49700 | 165 | 99,7 % | 301,2x |
| 7211 | Sumario: 1.- Regulación y definición. 2.- Características. 3.- Campo de | General | 59520 | 171 | 99,7 % | 348,1x |
| 7212 | Sumario: Introducción. 1.- Dominio y propiedad. 2.- Definiciones. 3.- Principios acerca | Civil | 49700 | 130 | 99,7 % | 382,3x |
| 7213 | Título VI del Libro I del Código de Procedimiento Civil, vale decir, de acuerdo a lo que | Civil | 71319 | 180 | 99,7 % | 396,2x |
| 7214 | Título VI “De la tradición”, del Libro II. Se divide en tres párrafos: “1. Disposiciones | General | 59520 | 184 | 99,7 % | 323,5x |
| 7215 | capítulo relativo a esa materia, adelantando sólo que la labor que | Judicial | 54457 | 145 | 99,7 % | 375,6x |
| 7216 | nuevo: “TÍTULO IV BIS DE LA SOLICITUD DE DISOLUCIÓN DEL VÍNCULO | General | 17306 | 48 | 99,7 % | 360,5x |
| 7217 | parte agraviada por la resolución del tribunal de primera instancia que | Procesal | 66012 | 198 | 99,7 % | 333,4x |
| 7218 | parte alguna de él. Esta es la regla general. Excepcionalmente permite la ley que | Familia | 85324 | 219 | 99,7 % | 389,6x |
| 7219 | parte de ellas. […] | Judicial | 60665 | 171 | 99,7 % | 354,8x |
| 7220 | parte de esta discusión que pone el acento en mejorar las condiciones | Laboral | 53293 | 165 | 99,7 % | 323,0x |
| 7221 | parte de la población el temor justificado de ser víctima de delitos de la | Judicial | 62514 | 158 | 99,7 % | 395,7x |
| 7222 | parte de la sociedad. Esto también reafirma las relaciones racializadas | Judicial | 60665 | 162 | 99,7 % | 374,5x |
| 7223 | parte de los jueces de garantía es real, como también lo es el populismo | Judicial | 78893 | 198 | 99,7 % | 398,4x |
| 7224 | parte de s s bienes -por ejemplo, disponiendo de la c arta de libre disposición y/o de la c arta de mejoras- | Civil | 36934 | 105 | 99,7 % | 351,8x |
| 7225 | parte de ésta señala que la sanción a la falta de discernimiento debió haber sido la | Familia | 85324 | 214 | 99,7 % | 398,7x |
| 7226 | parte del Tribunal de las controversias de superior relevancia jurídica o | Judicial | 62888 | 213 | 99,7 % | 295,2x |
| 7227 | parte del inciso 1° del artículo 477, se refiere a aquellas situacio- | Procesal | 66012 | 222 | 99,7 % | 297,4x |
| 7228 | parte del plazo; nunca gozaría de todo el plazo que la ley le confiere para interrumpir | Civil | 75968 | 206 | 99,7 % | 368,8x |
| 7229 | parte empleadora deberá facilitar que la votación se lleve a efecto con | Laboral | 74025 | 189 | 99,7 % | 391,7x |
| 7230 | parte en cuyo favor se declara la nulidad sólo puede hacer valer la acción de | Civil | 28857 | 81 | 99,7 % | 356,3x |
| 7231 | parte en el juicio ordinario de mayor cuantía (instrumentos –artículo | Procesal | 66012 | 213 | 99,7 % | 309,9x |
| 7232 | parte en las decisiones que les afectan | Laboral | 20469 | 58 | 99,7 % | 352,9x |
| 7233 | parte entregue a dicho intermediario un documento por el monto de dicha pena (un | Civil | 29257 | 93 | 99,7 % | 314,6x |
| 7234 | parte que “Si la finca es subastada a instancias de un acreedor hipotecario, y la | Civil | 71319 | 215 | 99,7 % | 331,7x |
| 7235 | parte respectiva, que, si está fundada en un derecho efectivo, será acogida y, por lo | Civil | 75968 | 204 | 99,7 % | 372,4x |
| 7236 | parte sino solamente de forma íntegra), la ejecución parcial no obligará al mandante sino en | Civil | 42773 | 131 | 99,7 % | 326,5x |
| 7237 | parte y a cualquier hora, disponible. La hiperestimulación se relaciona | Laboral | 53293 | 171 | 99,7 % | 311,7x |
| 7238 | parte, deja en claro que estos bienes, ubicados en posesiones particulares, son bienes | Civil | 42954 | 140 | 99,7 % | 306,8x |
| 7239 | parte, el cambio de la perspectiva del hecho producido por la del hecho que se va a | Judicial | 62514 | 172 | 99,7 % | 363,5x |
| 7240 | parte, el tribunal o la fuerza pública o en el que aquel se encuentre, por un plazo de sesenta días | Familia | 81198 | 219 | 99,7 % | 370,8x |
| 7241 | parte, que el juez se cerciore de que el tutor o curador es persona legalmente hábil | Familia | 85324 | 230 | 99,7 % | 371,0x |
| 7242 | parte, tratar a las personas que se encuentren en una misma situación de | Laboral | 53374 | 163 | 99,7 % | 327,4x |
| 7243 | parte. Tal solicitud debe ser conocida en cuenta, y, si se concede, el efecto | Procesal | 66012 | 208 | 99,7 % | 317,4x |
| 7244 | sección veremos los cinco aspectos centrales que deben ser explorados | Laboral | 53293 | 166 | 99,7 % | 321,0x |
| 7245 | título al dominio, al derecho real o asiento practicable (…). Este principio se vincula con | General | 59520 | 178 | 99,7 % | 334,4x |
| 7246 | título en la tradición”. Lo mismo cabe decir si hay ausencia de título traslaticio. Desde | General | 59520 | 188 | 99,7 % | 316,6x |
| 7247 | título entregado por el Estado; un concepto vagamente definido que se | Judicial | 60665 | 167 | 99,7 % | 363,3x |
| 7248 | título no translaticio de dominio; y recíprocamente por el mero contrato en que el | General | 59520 | 171 | 99,7 % | 348,1x |
| 7249 | título para la posesión regular. En este caso, no le conviene al actual poseedor agregar | General | 59520 | 191 | 99,7 % | 311,6x |
| 7250 | título presentado tiene más de tres años, contados desde que la obligación se haya hecho exigible; salvo que | Civil | 75968 | 218 | 99,7 % | 348,5x |
| 7251 | título que sea”. También el profesor don Andrés Cuneo Machiavello en un artículo | Civil | 66868 | 196 | 99,7 % | 341,2x |
| 7252 | título traslaticio de dominio”.66 | Civil | 66868 | 178 | 99,7 % | 375,7x |
| 7253 | título traslaticio y tradición a la vez, lo que implicaba que no podía celebrarla quien no | Civil | 49700 | 158 | 99,7 % | 314,6x |
| 7254 | título y el titular. En definitiva, el asiento debe estar extendido en términos claros y | General | 59520 | 189 | 99,7 % | 314,9x |
| 7255 | título, sino que también de una manera simbólica, como sería permitiendo o | General | 59520 | 197 | 99,7 % | 302,1x |
| 7256 | título” (artículo 1436), es decir, a las reglas generales de las donaciones.70 | Civil | 24389 | 81 | 99,7 % | 301,1x |
| 7257 | 1 El 13 de enero de 2023 fue publicado en el Diario Oficial el decreto número 12 que | Constitucional | 46896 | 170 | 99,6 % | 275,9x |
| 7258 | 1 Que pueden consultarse en la base de datos de estadísticas oficiales de delitos | Judicial | 33208 | 149 | 99,6 % | 222,9x |
| 7259 | 1. Debe constar expresamente el crédito garantizado; y | Civil | 22583 | 88 | 99,6 % | 256,6x |
| 7260 | 1. Los programas de difusión de la información consisten en hacer | Judicial | 29920 | 132 | 99,6 % | 226,7x |
| 7261 | 1. Para el tribunal como organización | Judicial | 29920 | 105 | 99,6 % | 285,0x |
| 7262 | 1. Puede ocurrir que el propio contrato de prenda, sea a la vez el título ejecutivo en el | Civil | 54173 | 218 | 99,6 % | 248,5x |
| 7263 | 1. Registrar información. Lleva registro de los temas tratados, registro | Judicial | 29920 | 124 | 99,6 % | 241,3x |
| 7264 | 1.1.2 Administrativo Jefe de Unidad de Sala | Familia | 26096 | 101 | 99,6 % | 258,4x |
| 7265 | 1.1.3 Unidad de Acta o Administrativo de Agenda | Familia | 26096 | 97 | 99,6 % | 269,0x |
| 7266 | 1.1.3. El propietario del suelo procedió a sabiendas que los materiales eran ajenos (es | Civil | 28857 | 102 | 99,6 % | 282,9x |
| 7267 | 1.1.4 Administrativos de Unidad de Sala | Familia | 26096 | 115 | 99,6 % | 226,9x |
| 7268 | 1.2.1 Jefe de Atención de Público | Familia | 26096 | 102 | 99,6 % | 255,8x |
| 7269 | 1.2.2 Administrativo Jefe de Atención de Público | Familia | 26096 | 109 | 99,6 % | 239,4x |
| 7270 | 1.2.3 Administrativo de Atención de Público | Familia | 26096 | 117 | 99,6 % | 223,0x |
| 7271 | 1.3.1 Jefe de Unidad de Servicios | Familia | 26096 | 100 | 99,6 % | 261,0x |
| 7272 | 1.3.2 Administrativo Contable | Familia | 26096 | 93 | 99,6 % | 280,6x |
| 7273 | 1.3.3 Administrativo Informático | Familia | 26096 | 92 | 99,6 % | 283,7x |
| 7274 | 1.4.1 Jefe de la Unidad de Causas | Familia | 26096 | 106 | 99,6 % | 246,2x |
| 7275 | 1.4.2 Administrativo Jefe de Unidad de Causas | Familia | 26096 | 101 | 99,6 % | 258,4x |
| 7276 | 1.4.3 Administrativo de Causas | Familia | 26096 | 97 | 99,6 % | 269,0x |
| 7277 | 1.5.1 Administrativo de Cumplimiento | Familia | 26096 | 101 | 99,6 % | 258,4x |
| 7278 | 1.8.2 Dotación mínima | Familia | 26096 | 109 | 99,6 % | 239,4x |
| 7279 | 1.8.3 Retorno masivo | Familia | 26096 | 96 | 99,6 % | 271,8x |
| 7280 | 1.8.4 Medidas de resguardo | Familia | 26096 | 93 | 99,6 % | 280,6x |
| 7281 | 10. Dar cuenta al presidente de la Corte Suprema de las causas en que no | Procesal | 66012 | 244 | 99,6 % | 270,5x |
| 7282 | 10. Situación del heredero beneficiario, que paga deudas que exceden el valor de los | Civil | 15693 | 66 | 99,6 % | 237,8x |
| 7283 | 1141. Los legados, en cuanto a la forma en que deben contribuir a los citados pagos, se | Civil | 21170 | 88 | 99,6 % | 240,6x |
| 7284 | 13. Las cosas corporales son las que se pueden tocar, como un fundo, un esclavo, un | Civil | 42954 | 182 | 99,6 % | 236,0x |
| 7285 | 15.1. Ficción acerca de la continuidad en la posesión | Civil | 36671 | 156 | 99,6 % | 235,1x |
| 7286 | 15.4 Valor probatorio de la prueba de testigos.72 | Procesal | 24749 | 100 | 99,6 % | 247,5x |
| 7287 | 150 A inciso 1, 148 y 150 A, inciso final, todos del Código Penal, respecto | Penal | 51155 | 195 | 99,6 % | 262,3x |
| 7288 | 2 En el mismo sentido, Toro explica que el derecho a ser oído «significa que se | Judicial | 42513 | 176 | 99,6 % | 241,6x |
| 7289 | 2. En cuanto a la eliminación de la inscripción, sólo un tribunal podrá disponerla, “de | Civil | 22583 | 88 | 99,6 % | 256,6x |
| 7290 | 2. Enfoque de género en el acceso a la justicia: La incorporación del | Judicial | 23342 | 102 | 99,6 % | 228,8x |
| 7291 | 2. Razón de la reglamentación de la donación entre vivos en el Libro III y normas que las | Civil | 24389 | 89 | 99,6 % | 274,0x |
| 7292 | 2. Se infringiría el art. 2505: si la posesión irregular pudiera adquirirse sin la | Civil | 36671 | 144 | 99,6 % | 254,7x |
| 7293 | 2.2. El art. 730 confirmaría que no es necesario inscribir: el inciso 1º no hace distinción | Civil | 36671 | 137 | 99,6 % | 267,7x |
| 7294 | 20 Ministerio Público, Defensoría Nacional, Corporación de Asistencia Judicial | Judicial | 30834 | 117 | 99,6 % | 263,5x |
| 7295 | 3 En un conflicto de necesidad en el que intervengan bienes vinculados con la | Penal | 51155 | 189 | 99,6 % | 270,7x |
| 7296 | 3. Para las personas | Judicial | 29920 | 107 | 99,6 % | 279,6x |
| 7297 | 3. Protección especial. Dentro de las acciones de protección de dere- | Constitucional | 46896 | 176 | 99,6 % | 266,5x |
| 7298 | 3.1.5 Patrocinio y poder | Judicial | 39447 | 148 | 99,6 % | 266,5x |
| 7299 | 344. En efecto, los padres estarán “impedidos” de ejercer el derecho legal de goce en | Familia | 62470 | 223 | 99,6 % | 280,1x |
| 7300 | 4 Artículo 8. «Ámbito de la defensa. El imputado tendrá derecho a ser defendido | Penal | 51155 | 182 | 99,6 % | 281,1x |
| 7301 | 4. Centro de Sistemas Públicos, Universidad de Chile para UNICEF | Constitucional | 46896 | 166 | 99,6 % | 282,5x |
| 7302 | 4.3.6 Recurso de nulidad penal | Judicial | 44331 | 163 | 99,6 % | 272,0x |
| 7303 | 5. Es sindicado como autor o cómplice de un delito cometido en un | Penal | 51155 | 204 | 99,6 % | 250,8x |
| 7304 | 5.- promesa de no disponer de la cuarta de mejoras. 4 | Civil | 23185 | 104 | 99,6 % | 222,9x |
| 7305 | 6. Las cosas cuya adquisición está prohibida por la ley (por ejemplo, explosivos y | Civil | 16643 | 68 | 99,6 % | 244,8x |
| 7306 | 6. Si el contrato ha sido concluído queda obligada a restituir la suma o a entregar la | Civil | 20010 | 79 | 99,6 % | 253,3x |
| 7307 | 66. Estos procedimientos deben respetar y resguardar los derechos de | Constitucional | 46896 | 202 | 99,6 % | 232,2x |
| 7308 | 7.4. Obligación que pesa sobre los guardadores o sobre los padres de un hijo menor de | Civil | 22201 | 94 | 99,6 % | 236,2x |
| 7309 | 8. Derecho a interponer una querella. La víctima de un delito tiene | Penal | 51155 | 197 | 99,6 % | 259,7x |
| 7310 | 9.2. Obligación de caucionar con un seguro o boleta bancaria, ciertos contratos de | Civil | 29257 | 123 | 99,6 % | 237,9x |
| 7311 | Al código civil y otros cuerpos legales por | General | 17306 | 71 | 99,6 % | 243,7x |
| 7312 | I. del pago de las deudas hereditarias y testamentarias | Civil | 21170 | 87 | 99,6 % | 243,3x |
| 7313 | Introducción: concepto y aplicación | Civil | 36934 | 157 | 99,6 % | 235,2x |
| 7314 | Nacional de testamentos | Civil | 50203 | 196 | 99,6 % | 256,1x |
| 7315 | O préstamo de consumo1 | Civil | 18418 | 70 | 99,6 % | 263,1x |
| 7316 | Representación y de transmisión | Civil | 20710 | 91 | 99,6 % | 227,6x |
| 7317 | Título I de la Ley, que deberá ser inscrito en el Registro de Prendas sin Desplazamiento. En | Civil | 22583 | 93 | 99,6 % | 242,8x |
| 7318 | Título XX del Libro IV. En ambos casos, la rescisión aludiría a un modo de extinguir | Civil | 22201 | 81 | 99,6 % | 274,1x |
| 7319 | parte compradora de una copia en soporte digital y material, del primer reglamento de | Civil | 29257 | 117 | 99,6 % | 250,1x |
| 7320 | parte de ellos (así, si en la comunidad existe un inmueble y un automóvil, cada | Civil | 49700 | 214 | 99,6 % | 232,2x |
| 7321 | parte de nadie. Se trata además de un negocio jurídico unilateral no recepticio. No es | Civil | 49700 | 197 | 99,6 % | 252,3x |
| 7322 | parte del adquirente. La ley no exige en todo caso que el almacén, cofre, etc., esté a la | General | 59520 | 211 | 99,6 % | 282,1x |
| 7323 | parte del edificio para que la responsabilidad afecte a todos quienes moran o residen en | Civil | 26055 | 100 | 99,6 % | 260,6x |
| 7324 | parte ideales o imaginarias (cuotas), aunque no lo puedan ser materialmente. Desde | Civil | 42954 | 162 | 99,6 % | 265,1x |
| 7325 | parte intransmisible del activo y pasivo del causante no pasa a los herederos, como | Civil | 16643 | 72 | 99,6 % | 231,2x |
| 7326 | parte o cuota; y iv) Que las cosas que componen tal universo y entre las cuales debe | Civil | 16643 | 62 | 99,6 % | 268,4x |
| 7327 | parte solicite dejar sin efecto una orden de arresto, como | Familia | 26096 | 107 | 99,6 % | 243,9x |
| 7328 | parte su mujer: le bastará el consentimiento de su mujer, si no estuviere imposibilitada de | General | 17306 | 62 | 99,6 % | 279,1x |
| 7329 | parte, antes de resolver lo del inventario, creo pertinente formular una pregunta | Familia | 44766 | 174 | 99,6 % | 257,3x |
| 7330 | parte, el derecho real de usufructo que se obtiene en virtud del art. 147 podría en | Familia | 44766 | 187 | 99,6 % | 239,4x |
| 7331 | parte, velará por el cumplimiento de las condiciones de la suspensión | Judicial | 42513 | 167 | 99,6 % | 254,6x |
| 7332 | sumario, para que se declare que ha operado ipso facto la desafectación de la calidad | Familia | 44766 | 195 | 99,6 % | 229,6x |
| 7333 | sumario.42 | Familia | 44766 | 188 | 99,6 % | 238,1x |
| 7334 | título al banco, según dispone el art. 1° de la Ley N° 4.287: “Los bonos y cualesquiera | Civil | 54173 | 214 | 99,6 % | 253,1x |
| 7335 | título de alimentos y la citada norma, precisamente, prohíbe toda pensión que supere | Familia | 44766 | 197 | 99,6 % | 227,2x |
| 7336 | título de crédito al portador, estará indeterminado hasta el momento en que se | Civil | 42954 | 176 | 99,6 % | 244,1x |
| 7337 | título de mutuo, aunque dicha prenda no garantizara ese mutuo. El pignoratario, pues, tiene una suerte de | Civil | 54173 | 209 | 99,6 % | 259,2x |
| 7338 | título oneroso. Se suele afirmar que es el único de los modos de adquirir que puede | General | 59520 | 210 | 99,6 % | 283,4x |
| 7339 | título para inscribir los derechos reales y la prohibición de enajenar o gravar en los | Familia | 44766 | 195 | 99,6 % | 229,6x |
| 7340 | título remoto. La discusión surge, en cuanto a los títulos inmediatos.21 | Civil | 28857 | 110 | 99,6 % | 262,3x |
| 7341 | título translaticio de dominio? | Civil | 36671 | 161 | 99,6 % | 227,8x |
| 7342 | Énfasis en los tratos negociales previos1 | Civil | 20010 | 72 | 99,6 % | 277,9x |
| 7343 | 1 Este uso va contra la norma ortográfica del castellano. La Ortografía académica | Judicial | 30834 | 149 | 99,5 % | 206,9x |
| 7344 | 1. Es un contrato unilateral: sólo se obliga el constituyente; sus principales obligaciones | Civil | 22583 | 105 | 99,5 % | 215,1x |
| 7345 | 1. Es verdad que la posesión no necesita de tradición, de inscripción; pero también lo | Civil | 36671 | 169 | 99,5 % | 217,0x |
| 7346 | 1. Plazo para enviar antecedentes al Servicio de Registro Civil e Identificación: el Notario | Civil | 22583 | 107 | 99,5 % | 211,1x |
| 7347 | 1. Principio de igualdad: Refiere al goce y al ejercicio efectivo de los | Judicial | 23342 | 109 | 99,5 % | 214,1x |
| 7348 | 1.1. El dueño de los materiales, plantas o semillas no tenía conocimiento del uso que | Civil | 28857 | 156 | 99,5 % | 185,0x |
| 7349 | 1.2.1. Opera el acrecimiento: de conformidad al art. 1148, el acrecimiento tiene lugar | General | 20070 | 93 | 99,5 % | 215,8x |
| 7350 | 1.2.2. No opera el acrecimiento: si el constituyente no ha designado sustituto ni hay lugar a | General | 20070 | 102 | 99,5 % | 196,8x |
| 7351 | 1.3. Clases de relaciones jurídicas. 2.- El deber jurídico y su relación con los derechos | General | 34424 | 182 | 99,5 % | 189,1x |
| 7352 | 1.6.1 Existencia de un régimen general | Familia | 26096 | 127 | 99,5 % | 205,5x |
| 7353 | 15.2. Actos que no pueden probarse por testigos.56 | Procesal | 24749 | 122 | 99,5 % | 202,9x |
| 7354 | 1610 N° 6, en las normas del pago con subrogación legal. Conforme al precepto, el préstamo que un tercero le | Civil | 18418 | 92 | 99,5 % | 200,2x |
| 7355 | 2. Para los efectos anteriores, el tribunal que esté conociendo de la realización de la prenda | Civil | 22583 | 102 | 99,5 % | 221,4x |
| 7356 | 2. Si falta el propietario fiduciario después de deferido el fideicomiso, se transmite la | General | 20070 | 104 | 99,5 % | 193,0x |
| 7357 | 20.190. Se trata por ende de ultra-actividad de esos preceptos legales, lo que por lo demás | Civil | 22583 | 109 | 99,5 % | 207,2x |
| 7358 | 2022-a-1912 | Familia | 26096 | 123 | 99,5 % | 212,2x |
| 7359 | 3. Que una resolución judicial declare procedente la retención; y | Civil | 22583 | 119 | 99,5 % | 189,8x |
| 7360 | 4. Los programas de reconocimiento al personal permiten estimular | Judicial | 29920 | 159 | 99,5 % | 188,2x |
| 7361 | 4. Principio de no violencia de género: Implica orientar los esfuerzos | Judicial | 23342 | 109 | 99,5 % | 214,1x |
| 7362 | 5. El deudor prendario que, tratándose de prendas de créditos o de cualquier otra clase de | Civil | 22583 | 124 | 99,5 % | 182,1x |
| 7363 | 5. Principio de participación e inclusión: Refiere a que la toma de | Judicial | 23342 | 107 | 99,5 % | 218,1x |
| 7364 | 7. El beneficio de separación obtenido por uno de los acreedores hereditarios o | Civil | 21170 | 97 | 99,5 % | 218,2x |
| 7365 | Cuarta parte: de las donaciones revocables. 1 | Civil | 20710 | 105 | 99,5 % | 197,2x |
| 7366 | Del abuso de los derechos1 | General | 8192 | 41 | 99,5 % | 199,8x |
| 7367 | H) regulaciones juridicas de las personas juridicas de derecho | General | 13045 | 70 | 99,5 % | 186,4x |
| 7368 | I.-       diversas formas de protección | General | 21362 | 97 | 99,5 % | 220,2x |
| 7369 | La posesión1 | Civil | 36671 | 166 | 99,5 % | 220,9x |
| 7370 | Los cuasicontratos1 | Civil | 8008 | 39 | 99,5 % | 205,3x |
| 7371 | Parte de la crisis vinculada a las funas, por ejemplo, guarda estrecha | Judicial | 33208 | 182 | 99,5 % | 182,5x |
| 7372 | parte de su excónyuge 40 años menor y de los hijos mayores de ambos. En razón de | Familia | 44766 | 205 | 99,5 % | 218,4x |
| 7373 | parte, el artículo 141 del Código Civil no distingue y, por ende, no es lícito hacerlo | Familia | 44766 | 208 | 99,5 % | 215,2x |
| 7374 | parte, porque se verá privado del bien a pesar de haber obtenido la declaración de | Familia | 44766 | 215 | 99,5 % | 208,2x |
| 7375 | parte, y por ende la herencia se regirá por las normas de la s cesión intestada, en los | Civil | 36934 | 193 | 99,5 % | 191,4x |
| 7376 | sumario (antiguo tenor del art. 141, inc. 2º). En otras palabras, atendido lo dispuesto | Familia | 44766 | 209 | 99,5 % | 214,2x |
| 7377 | título declarativo y no translaticio de dominio. ¿Cómo resolver este conflicto | Civil | 36671 | 166 | 99,5 % | 220,9x |
| 7378 | título injusto. Por el contrario, si interpretamos el numeral ateniéndonos estrictamente | Civil | 36671 | 196 | 99,5 % | 187,1x |
| 7379 | título lo será, por regla general (arts. 1097 y 1104). Ello, porque la condición jurídica | Civil | 36671 | 182 | 99,5 % | 201,5x |
| 7380 | título no traslaticio de dominio? B) ¿Exige la ley inscribir en este caso? Fundamente su | Civil | 36671 | 175 | 99,5 % | 209,5x |
| 7381 | título oneroso. En cambio, si se adquiere a título gratuito, ingresará al haber propio del | General | 11057 | 57 | 99,5 % | 194,0x |
| 7382 | título traslaticio de dominio, tal como la venta, sino que es errado hacerlo. El título, como se | Civil | 42773 | 226 | 99,5 % | 189,3x |
| 7383 | 1. Estime el tiempo necesario para la reunión, para ello considere la | Judicial | 29920 | 174 | 99,4 % | 172,0x |
| 7384 | 1. Estos derechos sólo podrán transferirse a quien diere cumplimiento a los requisitos | Civil | 22583 | 133 | 99,4 % | 169,8x |
| 7385 | 1.1.1. El propietario del inmueble procedió con justa causa de error (es decir, sin | Civil | 28857 | 178 | 99,4 % | 162,1x |
| 7386 | 1.2. El dueño de los materiales tuvo conocimiento del uso que de ellos hacía el | Civil | 28857 | 172 | 99,4 % | 167,8x |
| 7387 | 1.6.2 Cumplimiento del derecho de alimentos | Familia | 26096 | 144 | 99,4 % | 181,2x |
| 7388 | 1.6.3 Causas sobre el derecho de relación directa y regular | Familia | 26096 | 146 | 99,4 % | 178,7x |
| 7389 | 1211 El título se divide en los siguientes párrafos: 1° “De las asignaciones alimenticias | Civil | 20710 | 119 | 99,4 % | 174,0x |
| 7390 | 2. Antecedentes que deben enviarse en el referido plazo: el Notario deberá enviar para su | Civil | 22583 | 127 | 99,4 % | 177,8x |
| 7391 | 2. Los bienes nacionales de uso público, o los de propiedad estatal o municipal | Civil | 16643 | 101 | 99,4 % | 164,8x |
| 7392 | 2. No se les garantice con prenda sobre esos mismos bienes, lo que han pagado o se han | Civil | 22583 | 133 | 99,4 % | 169,8x |
| 7393 | 2. Seleccione la opción Todos los programas y dentro de ella la carpeta | Laboral | 14212 | 80 | 99,4 % | 177,7x |
| 7394 | 2.1.1. Derecho a hacer suyo el edificio, plantación o sementera, pagando al dueño de | Civil | 28857 | 185 | 99,4 % | 156,0x |
| 7395 | 2.2. Clases de capacidad. 2.3. Capacidad de goce, atributo de la personalidad. 2.4. La | General | 32080 | 198 | 99,4 % | 162,0x |
| 7396 | 2.2. El dueño del suelo tuvo conocimiento de lo que hacía el propietario de los | Civil | 28857 | 175 | 99,4 % | 164,9x |
| 7397 | 3. Principio de no discriminación de género: Refiere a la prohibición | Judicial | 23342 | 132 | 99,4 % | 176,8x |
| 7398 | 4 Un breve comentario técnico. Como se explica en Soto (2020), formalmente la | Judicial | 30834 | 184 | 99,4 % | 167,6x |
| 7399 | 4. Efectos que se originan, cuando las personas jurídicas de Derecho Público y los | Civil | 15693 | 87 | 99,4 % | 180,4x |
| 7400 | 5.- asignaciones voluntarias a titulo singular | Civil | 23185 | 137 | 99,4 % | 169,2x |
| 7401 | 5.2. Cuando ambos deudores, principal y fiador, se sujetan a una pena, pero la del fiador | Civil | 25022 | 148 | 99,4 % | 169,1x |
| 7402 | 577.1 CC). Usualmente se les califica de derechos ‘erga omnes’. Los derechos de eficacia | General | 34424 | 208 | 99,4 % | 165,5x |
| 7403 | 6. Copie la fórmula del formato condicional hacia las celdas inferiores para | Laboral | 14212 | 79 | 99,4 % | 179,9x |
| 7404 | 9. El artículo 16 de la Ley número 19.865, sobre Financiamiento Urbano Compartido; y | Civil | 22583 | 127 | 99,4 % | 177,8x |
| 7405 | El contrato de fianza1 | Civil | 25022 | 141 | 99,4 % | 177,5x |
| 7406 | El derecho real de conservación1 | General | 11057 | 71 | 99,4 % | 155,7x |
| 7407 | Los modos de adquirir el dominio1 | Civil | 28857 | 174 | 99,4 % | 165,8x |
| 7408 | Parte de la doctrina, según se verá al estudiar la hipoteca, rechaza la posibilidad de adquirir por | Civil | 17473 | 97 | 99,4 % | 180,1x |
| 7409 | Y sus derechos en la sucesion | Civil | 36934 | 218 | 99,4 % | 169,4x |
| 7410 | parte abintestato y parte testamentariamente. Si se aceptara la opinión de la primera | Civil | 28857 | 184 | 99,4 % | 156,8x |
| 7411 | parte de la herencia con infracción de ley (art. 1216). Dejada sin efecto dicha | Civil | 23185 | 144 | 99,4 % | 161,0x |
| 7412 | parte del titular de un derecho frente a otros sujetos, por motivos de enemistad, de | General | 34424 | 217 | 99,4 % | 158,6x |
| 7413 | parte, el cambio del orden de los apellidos del solicitante provocará el cambio del | General | 32080 | 206 | 99,4 % | 155,7x |
| 7414 | título de enajenación derivado del usurpador, desde el momento que la ley admite que | Civil | 36671 | 204 | 99,4 % | 179,8x |
| 7415 | 1. Crearemos una planilla con los datos necesarios, en este caso, rol de la | Laboral | 14212 | 97 | 99,3 % | 146,5x |
| 7416 | 1. En la inscripción de nacimiento del primero de los hijos comunes, los progenitores | General | 17306 | 124 | 99,3 % | 139,6x |
| 7417 | 1. Puede ocurrir que el propio contrato de prenda, sea a la vez el título ejecutivo en el cual | Civil | 22583 | 169 | 99,3 % | 133,6x |
| 7418 | 1. Vaya a la pestaña Revisar y escoja la opción Permitir que los usuarios | Laboral | 14212 | 93 | 99,3 % | 152,8x |
| 7419 | 1. Vaya a la pestaña Revisar y seleccione Proteger hoja. Deje las | Laboral | 14212 | 94 | 99,3 % | 151,2x |
| 7420 | 2. Comience a escribir. Verá cómo este adquiere el formato que ha | Laboral | 14212 | 106 | 99,3 % | 134,1x |
| 7421 | 2. Para otros, la ley sólo quiso referirse a las pensiones alimenticias que a la muerte | Civil | 20710 | 141 | 99,3 % | 146,9x |
| 7422 | 2.1.2. Derecho a obligar al que edificó o plantó a pagarle el justo precio del terreno | Civil | 28857 | 196 | 99,3 % | 147,2x |
| 7423 | 3. Forma de enviar los antecedentes: las copias de los actos o contratos deberán enviarse | Civil | 22583 | 167 | 99,3 % | 135,2x |
| 7424 | 4.- del testamento menos solemne o privilegiado. 1 | Civil | 15191 | 113 | 99,3 % | 134,4x |
| 7425 | 5. Los instrumentos otorgados en el extranjero, las transcripciones y las traducciones | Procesal | 24749 | 183 | 99,3 % | 135,2x |
| 7426 | 5.5. La legítima como asignación privilegiada y preferente.9 | Civil | 15039 | 110 | 99,3 % | 136,7x |
| 7427 | 5.7. Formalidades que deben cumplirse para obtener la declaración de muerte | General | 12229 | 80 | 99,3 % | 152,9x |
| 7428 | 7.1. Existe cosa juzgada respecto de los herederos, en un juicio seguido contra o por el | Civil | 16643 | 117 | 99,3 % | 142,2x |
| 7429 | 830. Esta última disposición, y otras, como por ejemplo el artículo 833, se encuentran | General | 20070 | 131 | 99,3 % | 153,2x |
| 7430 | De las asignaciones1 | Civil | 24207 | 170 | 99,3 % | 142,4x |
| 7431 | parte de un sistema más general, cual es el de las liberalidades. Por “liberalidad”, se | Civil | 24389 | 170 | 99,3 % | 143,5x |
| 7432 | parte interesada, inscriban en el Registro de Hipotecas y Gravámenes, los contratos de | Civil | 29257 | 197 | 99,3 % | 148,5x |
| 7433 | parte no cubierta del seguro o por su totalidad. Para Armando Uribe, “el Estado debe ser | Civil | 26055 | 180 | 99,3 % | 144,8x |
| 7434 | parte se grave a favor de la otra, lo que no ocurre si es un tercero ajeno al contrato quien | Civil | 25022 | 183 | 99,3 % | 136,7x |
| 7435 | parte superior de un edificio, cuando no puede establecerse con precisión quién es el | Civil | 26055 | 193 | 99,3 % | 135,0x |
| 7436 | título, se adquirirá una parte distinta de la herencia. Así, el heredero podrá adquirir por | Civil | 28857 | 211 | 99,3 % | 136,8x |
| 7437 | 1. Por regla general, el procedimiento aplicable para las acciones que se deduzcan, será | Civil | 22583 | 178 | 99,2 % | 126,9x |
| 7438 | 12. En efecto, s ren ncia no está prohibida por la ley y la acción está | Civil | 24207 | 182 | 99,2 % | 133,0x |
| 7439 | 2. En toda inscripción de nacimiento en que al tiempo de la inscripción quede determinada | General | 17306 | 131 | 99,2 % | 132,1x |
| 7440 | 2. Es por regla general un contrato oneroso: en efecto, usualmente el contrato reportará | Civil | 22583 | 184 | 99,2 % | 122,7x |
| 7441 | 2. Haga clic sobre ella con el botón derecho del mouse y del menú escoja la | Laboral | 14212 | 109 | 99,2 % | 130,4x |
| 7442 | 2. Hay dos casos especiales, contemplados en los artículos 17 y 22 de la Ley que | Civil | 22583 | 180 | 99,2 % | 125,5x |
| 7443 | 2. Para proceder ejecutivamente contra su | Civil | 8650 | 70 | 99,2 % | 123,6x |
| 7444 | 2. Podrán, además, obtener la realización de la mercadería retenida, para el reembolso de | Civil | 22583 | 172 | 99,2 % | 131,3x |
| 7445 | 2. Quien lleva adelante la ejecución es un acreedor hipotecario, y existen acreedores | Civil | 22583 | 178 | 99,2 % | 126,9x |
| 7446 | 3. El tribunal resolverá por escrito y sin más trámite lo que corresponda. Distinguimos al | Civil | 22583 | 171 | 99,2 % | 132,1x |
| 7447 | 3. Si el contrato fuere oneroso, será además conmutativo, pues las partes están en | Civil | 22583 | 175 | 99,2 % | 129,0x |
| 7448 | 4. La suma determinada o determinable a la que se limitare la prenda o la proporción en que | Civil | 22583 | 182 | 99,2 % | 124,1x |
| 7449 | 5. Si transcurriere el plazo de sesenta días sin que los organismos hayan suscrito la escritura | Civil | 22583 | 183 | 99,2 % | 123,4x |
| 7450 | 52 Nº 2). Excepcionalmente, la tradición de la servidumbre de alcantarillado | General | 20070 | 154 | 99,2 % | 130,3x |
| 7451 | De la particion de bienes1 | Civil | 22201 | 188 | 99,2 % | 118,1x |
| 7452 | De las asignaciones forzosas1 | Civil | 20189 | 170 | 99,2 % | 118,8x |
| 7453 | El contrato de comodato1 | Civil | 4521 | 36 | 99,2 % | 125,6x |
| 7454 | Que corresponden a los interesados. 1 | Civil | 9067 | 75 | 99,2 % | 120,9x |
| 7455 | Sección de la Comuna de Santiago, y pacten en ese acto sociedad conyugal o régimen de | General | 17306 | 135 | 99,2 % | 128,2x |
| 7456 | Teoria de la prueba1 | Procesal | 24749 | 192 | 99,2 % | 128,9x |
| 7457 | parte de la herencia, en cuyo caso el déficit se cubre con la cuarta de libre disposición | Civil | 23185 | 175 | 99,2 % | 132,5x |
| 7458 | parte de libre disposición. En conformidad con el art. 1194, este exceso o esta | Civil | 23185 | 182 | 99,2 % | 127,4x |
| 7459 | parte de s asignación por efecto de la vol ntad expresa del ca sante, expresada en | Civil | 24207 | 196 | 99,2 % | 123,5x |
| 7460 | parte de su legítima, nada se agrega a la mitad legitimaria, sino que ella se dividirá por | Civil | 15039 | 115 | 99,2 % | 130,8x |
| 7461 | partición: “¿ES NECESARIO CURADOR ESPECIAL CUANDO EN LA PARTICIÓN HAY CONFLICTO DE | Civil | 22201 | 180 | 99,2 % | 123,3x |
| 7462 | título de la propiedad fiduciaria (arts. 733 a 763). Así, por ejemplo, el testador | Civil | 20710 | 165 | 99,2 % | 125,5x |
| 7463 | título de legítima a personas que eran legitimarios, pero que pierden esta calidad | Civil | 23185 | 182 | 99,2 % | 127,4x |
| 7464 | título de mejora. Por lo mismo, toda donación hecha a un legitimario se presume | Civil | 23185 | 178 | 99,2 % | 130,3x |
| 7465 | título universal. 19 | Civil | 23185 | 182 | 99,2 % | 127,4x |
| 7466 | 1. Quien lleva adelante la ejecución es un acreedor prendario, y existen otros acreedores | Civil | 22583 | 192 | 99,1 % | 117,6x |
| 7467 | 1269. En este caso, es indisc tible q e la acción de petición de herencia se | Civil | 24207 | 210 | 99,1 % | 115,3x |
| 7468 | 2. En cuanto a su razón social: se forma con el nombre de todos | Civil | 8650 | 80 | 99,1 % | 108,1x |
| 7469 | 2. Los actos de emulación; y | General | 8192 | 71 | 99,1 % | 115,4x |
| 7470 | 2. No se suspenderá la tramitación de los juicios civiles a que se refiere este ley, por la | Civil | 22583 | 209 | 99,1 % | 108,1x |
| 7471 | 2. Puede ocurrir que en el contrato de prenda no se indique la obligación caucionada, lo que | Civil | 22583 | 204 | 99,1 % | 110,7x |
| 7472 | 2. Socios comanditarios responden solamente hasta | Civil | 8650 | 81 | 99,1 % | 106,8x |
| 7473 | 3. Una tercera doctrina, que ha prevalecido en las Cortes, entiende que no obstante | Civil | 20710 | 182 | 99,1 % | 113,8x |
| 7474 | 4. Consecuencias por el incumplimiento de las obligaciones anteriores: la omisión de las | Civil | 22583 | 195 | 99,1 % | 115,8x |
| 7475 | 4.6. Naturaleza jurídica de los alimentos: ¿Asignación a título singular? | Civil | 20710 | 179 | 99,1 % | 115,7x |
| 7476 | 7.3. En contra de los herederos del deudor hipotecario procede la acción personal y no | Civil | 16643 | 158 | 99,1 % | 105,3x |
| 7477 | 8.- obligaciones de los socios | Civil | 8650 | 76 | 99,1 % | 113,8x |
| 7478 | N° 1). 16 | Civil | 20710 | 179 | 99,1 % | 115,7x |
| 7479 | Sumario: 1.- Regulación y definición. 2.- Crítica de la reglamentación conjunta | Civil | 17473 | 165 | 99,1 % | 105,9x |
| 7480 | Título IV, “De los Interdictos”, del Código de Procedimiento Civil. Específicamente, en | General | 21362 | 198 | 99,1 % | 107,9x |
| 7481 | Título ‘De la reivindicación’; no todas, lógicamente, sino sólo las que se concilien con la | General | 21362 | 185 | 99,1 % | 115,5x |
| 7482 | parte de la cuarta de libre disposición; excepcionalmente, podría gravarse la cuarta de | Civil | 20710 | 187 | 99,1 % | 110,7x |
| 7483 | parte de sus bienes a otra persona, que la acepta.”12 Comentando esta definición, Meza | Civil | 24389 | 214 | 99,1 % | 114,0x |
| 7484 | parte del bien raíz, proporcionado por el Servicio de Imp estos Internos. El criterio del | General | 17296 | 163 | 99,1 % | 106,1x |
| 7485 | parte expositiva del fallo de casación que antecede, cabe no obstante recordar, que como ha señalado la | Civil | 24207 | 211 | 99,1 % | 114,7x |
| 7486 | título de compraventa y que, por lo mismo, tratándose del objeto cuyo valor hace | Civil | 22201 | 209 | 99,1 % | 106,2x |
| 7487 | título de legítimas o de mejoras y que exceda la mitad legitimaria o la cuarta de | Civil | 21170 | 198 | 99,1 % | 106,9x |
| 7488 | título en virtud del contrato de concesión; o | Civil | 22583 | 209 | 99,1 % | 108,1x |
| 7489 | 1. Pueden los acreedores del socio interponer, como acción oblicua o | Civil | 8650 | 87 | 99,0 % | 99,4x |
| 7490 | 1337. Así lo manifiesta el legislador en el art. 1334, al decir (…). el art. 1334 transcrito | Civil | 22201 | 224 | 99,0 % | 99,1x |
| 7491 | 2502 Nº 1). El Código Civil señala como ejemplo, una heredad permanentemente | Civil | 17473 | 178 | 99,0 % | 98,2x |
| 7492 | 7.2. En cuanto a la posibilidad de que los herederos puedan o no demandar la nulidad | Civil | 16643 | 172 | 99,0 % | 96,8x |
| 7493 | Contrato de transacción | Civil | 3742 | 37 | 99,0 % | 101,1x |
| 7494 | Partida de nacimiento de las personas mayores de catorce y | General | 17306 | 170 | 99,0 % | 101,8x |
| 7495 | capítulo referido a la posesión. El Código Civil indica, sin embargo, ciertas reglas | Civil | 17473 | 180 | 99,0 % | 97,1x |
| 7496 | título. Una vez practicada su inscripción en el Registro del Conservador de Bienes | Civil | 17473 | 170 | 99,0 % | 102,8x |
| 7497 | 1. Presione la tecla Alt. Verá que aparecen unos cuadros pequeños | Laboral | 14212 | 154 | 98,9 % | 92,3x |
| 7498 | 1127. Pueden legarse las cosas muebles y los inmuebles. Incluso, con ciertas | Civil | 16643 | 189 | 98,9 % | 88,1x |
| 7499 | 2.2. - teoria del patrimonio de afectacion | General | 13045 | 137 | 98,9 % | 95,2x |
| 7500 | 3. En la inscripción de nacimiento de un hijo cuya filiación al tiempo de la inscripción quede | General | 17306 | 183 | 98,9 % | 94,6x |
| 7501 | Del deposito y del secuestro 1 | Civil | 4499 | 48 | 98,9 % | 93,7x |
| 7502 | I. los beneficios en el código civil chileno | Civil | 15693 | 179 | 98,9 % | 87,7x |
| 7503 | Título III de la ley N° 19.968. El juez se pronunciará en la sentencia definitiva con el solo | General | 17306 | 184 | 98,9 % | 94,1x |
| 7504 | parte del patrimonio o masa de bienes que sirve de antecedente para la fijación o | Civil | 20710 | 218 | 98,9 % | 95,0x |
| 7505 | 1038. Se ha fallado que no habiéndose señalado por la ley otras normas para el | Civil | 15191 | 184 | 98,8 % | 82,6x |
| 7506 | 1199. Procede entonces descontar de ella la parte en que se están aprovechando de | Civil | 15039 | 179 | 98,8 % | 84,0x |
| 7507 | 2. Concepto | Civil | 15693 | 184 | 98,8 % | 85,3x |
| 7508 | J) responsabilidad de las personas jurídicas | General | 13045 | 152 | 98,8 % | 85,8x |
| 7509 | 1. - teorias que la aceptan | General | 13045 | 166 | 98,7 % | 78,6x |
| 7510 | 2009. Esta responsabilidad sólo puede originarse por la comisión de los delitos de lavado de | General | 13045 | 176 | 98,7 % | 74,1x |
| 7511 | 5.- elementos del contrato de sociedad | Civil | 8650 | 111 | 98,7 % | 77,9x |
| 7512 | 6. Ley 19.499 sobre saneamiento de vicios de nulidad de sociedades | Civil | 8650 | 115 | 98,7 % | 75,2x |
| 7513 | C nstitución del d mini s bre ella1 | General | 17296 | 217 | 98,7 % | 79,7x |
| 7514 | parte de la herencia, no pasa por este hecho a ser heredero. La denuncia de la | Civil | 9067 | 119 | 98,7 % | 76,2x |
| 7515 | parte o cuota que le corresponda, sin que la cuota del insolvente grave a los demás. Lo | Civil | 16643 | 211 | 98,7 % | 78,9x |
| 7516 | 1. Por regla general, es un contrato consensual | Civil | 8650 | 123 | 98,6 % | 70,3x |
| 7517 | Las personas naturales1 | General | 12229 | 176 | 98,6 % | 69,5x |
| 7518 | O ejecutores testamentarios1 | Civil | 12262 | 170 | 98,6 % | 72,1x |
| 7519 | parte de los bienes del testador y un curador de la herencia yacente encargado de | Civil | 9067 | 128 | 98,6 % | 70,8x |
| 7520 | 1275. La ausencia, en las normas aplicables a los albaceas fiduciarios, de una norma | Civil | 12262 | 182 | 98,5 % | 67,4x |
| 7521 | 2. Obligación de obtener el consentimiento unánime de los socios | Civil | 8650 | 128 | 98,5 % | 67,6x |
| 7522 | La anticresis 1 | General | 2440 | 36 | 98,5 % | 67,8x |
| 7523 | La responsabilidad extracontractual1 | Civil | 5366 | 78 | 98,5 % | 68,8x |
| 7524 | Los medicos en particular | Civil | 3823 | 59 | 98,5 % | 64,8x |
| 7525 | título de los albaceas, establece que lo dispuesto en los arts. 394 y 412 se extenderá a | Civil | 12262 | 180 | 98,5 % | 68,1x |
| 7526 | 4. Las Municipalidades; o | General | 11057 | 172 | 98,4 % | 64,3x |
| 7527 | 6. Muerte de uno de los socios, Art. 2103 | Civil | 8650 | 136 | 98,4 % | 63,6x |
| 7528 | 10.       Renuncia de cualquiera de los socios, Art. 2108 | Civil | 8650 | 143 | 98,3 % | 60,5x |
| 7529 | 4. Pérdida total de los bienes sociales, Art. 2100 | Civil | 8650 | 148 | 98,3 % | 58,4x |
| 7530 | 6.- especies de sociedad | Civil | 8650 | 146 | 98,3 % | 59,2x |
| 7531 | 9.- disolución de la sociedad. articulos 2098 a 2115 | Civil | 8650 | 148 | 98,3 % | 58,4x |
| 7532 | Sociedades | Civil | 8650 | 146 | 98,3 % | 59,2x |
| 7533 | 2. No se puede transigir sobre los alimentos futuros de las personas a | Civil | 3742 | 68 | 98,2 % | 55,0x |
| 7534 | 2. Si no tenía poder suficiente, 2094 inciso 3. Es el socio el que | Civil | 8650 | 153 | 98,2 % | 56,5x |
| 7535 | 3.- la sociedad, persona jurídica distinta de los socios | Civil | 8650 | 157 | 98,2 % | 55,1x |
| 7536 | 7.- administración de la sociedad colectiva | Civil | 8650 | 154 | 98,2 % | 56,2x |
| 7537 | La ley como fuente de las obligaciones | Civil | 8008 | 143 | 98,2 % | 56,0x |
| 7538 | parte, se crea una solución de continuidad o vacío en el Registro de Propiedad, cuestión que | General | 7473 | 131 | 98,2 % | 57,0x |
| 7539 | 1578 Nº 1, norma que establece que, por regla general, el pago hecho al incapaz adolece | Civil | 4521 | 84 | 98,1 % | 53,8x |
| 7540 | 3. Situación del socio acreedor de una persona que es a su vez | Civil | 8650 | 162 | 98,1 % | 53,4x |
| 7541 | 3. Contrato oneroso: pues grava a ambas partes, la una en beneficio | Civil | 3742 | 76 | 98,0 % | 49,2x |
| 7542 | Capitulo x : el censo | General | 1757 | 36 | 98,0 % | 48,8x |
| 7543 | 6.- casos de nulidad en la transaccion | Civil | 3742 | 84 | 97,8 % | 44,5x |
| 7544 | 3.1. Cuando el comodatario empleó la cosa en un uso indebido o está en mora de restituir | Civil | 4521 | 106 | 97,7 % | 42,7x |
| 7545 | 3. No se puede transigir sobre el estado civil: Art. 2450. Ello porque | Civil | 3742 | 94 | 97,5 % | 39,8x |
| 7546 | título, no ha querido referirse indudablemente a su entrega material, pues lo que se | General | 7473 | 187 | 97,5 % | 40,0x |
| 7547 | 2.- elementos constitutivos de la transacción | Civil | 3742 | 114 | 97,0 % | 32,8x |
| 7548 | 3.3. Cuando en lugar de salvar la cosa dada en comodato, el comodatario prefirió salvar una | Civil | 4521 | 141 | 96,9 % | 32,1x |
| 7549 | título es el acto del que nace el derecho objeto de la transacción, y | Civil | 3742 | 123 | 96,7 % | 30,4x |
| 7550 | 1. No se puede transigir sobre las acciones penales que nacen de un | Civil | 3742 | 128 | 96,6 % | 29,2x |
| 7551 | 18.575. Otro caso emblemático de responsabilidad civil del Fisco por falta de | Civil | 5366 | 197 | 96,3 % | 27,2x |
| 7552 | 5.- objeto de la transacción | Civil | 3742 | 140 | 96,3 % | 26,7x |
| 7553 | 1. Existencia de un derecho dudoso, es decir, existencia o perspectiva | Civil | 3742 | 159 | 95,8 % | 23,5x |
| 7554 | 1. Si son muchos los interesados en el negocio sobre el cual se | Civil | 3742 | 159 | 95,8 % | 23,5x |
| 7555 | 2006. El mismo artículo 1999 rige para las profesiones que se regulan por | Civil | 3823 | 162 | 95,8 % | 23,6x |
| 7556 | Asignaciones por causa de muerte1 | Civil | 3914 | 169 | 95,7 % | 23,2x |
| 7557 | 2. Que las partes se hagan concesiones reciprocas. Lo anterior no | Civil | 3742 | 163 | 95,6 % | 23,0x |
| 7558 | 4.- quienes pueden transigir | Civil | 3742 | 167 | 95,5 % | 22,4x |
| 7559 | Infracción Ambiental Continua y Prescripción |  | 1450 | 67 | 95,4 % | 21,6x |
| 7560 | Tendencias modernas sobre responsabilidad 12 | Civil | 2650 | 154 | 94,2 % | 17,2x |
| 7561 | Tutela Cautelar Ambiental (Art. 24) |  | 1450 | 100 | 93,1 % | 14,5x |
| 7562 | Daño Ambiental Significativo |  | 1450 | 102 | 93,0 % | 14,2x |
| 7563 | Reparación Ambiental In Natura |  | 1450 | 106 | 92,7 % | 13,7x |
| 7564 | Principio Precautorio y Preventivo |  | 1450 | 107 | 92,6 % | 13,6x |
| 7565 | Protección de Humedales Urbanos |  | 1450 | 107 | 92,6 % | 13,6x |
| 7566 | Capacidad de Carga y Anaerobiosis Acuícola |  | 1450 | 114 | 92,1 % | 12,7x |
| 7567 | Regularización Migratoria, Debido Proceso en Expulsiones y Arraigo Familiar |  | 1450 | 124 | 91,4 % | 11,7x |
| 7568 | Juzgamiento con Perspectiva de Género y No Discriminación |  | 1450 | 126 | 91,3 % | 11,5x |
| 7569 | Principio de Confianza Legítima en Contratas Públicas |  | 1450 | 135 | 90,7 % | 10,7x |
| 7570 | Extinción del Acto Administrativo: Invalidación vs. Revocación | Derecho Administrativo | 1037 | 98 | 90,5 % | 10,6x |
| 7571 | Control Constitucional de Alzas de Planes de Isapre, Tabla de Factores y Cobertura GES/CAEC |  | 1450 | 141 | 90,3 % | 10,3x |
| 7572 | Imprescriptibilidad de Crímenes de Lesa Humanidad y Reparación Integral |  | 1450 | 140 | 90,3 % | 10,4x |
| 7573 | Obligaciones Sujetas a Modalidad: Condición, Plazo y Modo | Derecho Civil | 1112 | 117 | 89,5 % | 9,5x |
| 7574 | Indemnización de Perjuicios y Cláusula Penal (Art. 1535 CC) | Derecho Civil | 1534 | 162 | 89,4 % | 9,5x |
| 7575 | El Acto Administrativo: Concepto y Efectos (Ley N° 19.880) | Derecho Administrativo | 1037 | 117 | 88,7 % | 8,9x |
| 7576 | Obligaciones Naturales y Civiles (Art. 1470 CC) | Derecho Civil | 1112 | 130 | 88,3 % | 8,6x |
| 7577 | El Alivio Probatorio de Indicios (Art. 493 CT) | Derecho del Trabajo (Laboral) | 1176 | 143 | 87,8 % | 8,2x |
| 7578 | Baremo Estadístico de Daño Moral por Muerte y Lesiones (PJUD) |  | 1450 | 179 | 87,7 % | 8,1x |
| 7579 | Obligaciones con Pluralidad de Sujetos: Solidaridad Pasiva | Derecho Civil | 1112 | 139 | 87,5 % | 8,0x |
| 7580 | Ley Karin (Ley N° 21.643) y el Daño Moral Laboral | Derecho del Trabajo (Laboral) | 1176 | 150 | 87,2 % | 7,8x |
| 7581 | Prelación de Créditos y Clases de Privilegios (Arts. 2470 al 2491 CC) | Derecho Civil | 850 | 119 | 86,0 % | 7,1x |
| 7582 | Causales de Exoneración y Reducción del Daño | Derecho Civil | 884 | 126 | 85,7 % | 7,0x |
| 7583 | Concepto Dogmático de Delito y Teoría de la Conducta (Art. 1 CP) | Derecho Penal | 795 | 118 | 85,2 % | 6,7x |
| 7584 | El Control de Constitucionalidad: Inaplicabilidad ante el TC (Art. 93 N° 6 CPR) | Derecho Constitucional | 1041 | 156 | 85,0 % | 6,7x |
| 7585 | Autoría y Participación Criminal (Arts. 14 al 17 CP) | Derecho Penal | 833 | 131 | 84,3 % | 6,4x |
| 7586 | El Orden Público Económico (Art. 19 N° 21 y N° 22 CPR) | Derecho Constitucional | 798 | 126 | 84,2 % | 6,3x |
| 7587 | Responsabilidad Estricta u Objetiva en el Ordenamiento Chileno | Derecho Civil | 816 | 131 | 83,9 % | 6,2x |
| 7588 | El Recurso de Queja Disciplinario (Art. 545 COT) | Derecho Procesal | 859 | 139 | 83,8 % | 6,2x |
| 7589 | El Error como Vicio del Consentimiento (Arts. 1451 a 1455 CC) | Derecho Civil | 1612 | 265 | 83,6 % | 6,1x |
| 7590 | Efectos del Recurso de Apelación y Adhesión | Derecho Procesal | 923 | 154 | 83,3 % | 6,0x |
| 7591 | El Recurso de Casación en la Forma (Art. 768 CPC) | Derecho Procesal | 859 | 144 | 83,2 % | 6,0x |
| 7592 | El Dominio y su Estatuto Constitucional | Derecho Civil | 759 | 133 | 82,5 % | 5,7x |
| 7593 | Presunción de Culpa por el Hecho Ajeno (Art. 2320 CC) | Derecho Civil | 816 | 144 | 82,4 % | 5,7x |
| 7594 | Estado de Necesidad Justificante (Art. 10 N° 7 CP) | Derecho Penal | 699 | 127 | 81,8 % | 5,5x |
| 7595 | La Fuerza o Violencia Moral e Intimidación (Arts. 1456 y 1457 CC) | Derecho Civil | 1612 | 293 | 81,8 % | 5,5x |
| 7596 | Tipicidad Subjetiva: Dolo y Culpa | Derecho Penal | 795 | 146 | 81,6 % | 5,4x |
| 7597 | Prescripción Extintiva o Liberatoria (Arts. 2514 al 2524 CC) | Derecho Civil | 850 | 157 | 81,5 % | 5,4x |
| 7598 | Catálogo de Modos de Extinguir las Obligaciones (Art. 1567 CC) | Derecho Civil | 850 | 159 | 81,3 % | 5,3x |
| 7599 | Culpabilidad e Inexigibilidad de Otra Conducta | Derecho Penal | 833 | 156 | 81,3 % | 5,3x |
| 7600 | Nexo Causal e Imputación Objetiva (Tesis de Barros Bourie) | Derecho Civil | 884 | 165 | 81,3 % | 5,4x |
| 7601 | Concepto Dogmático y Estructura Trilateral de la Obligación | Derecho Civil | 1112 | 217 | 80,5 % | 5,1x |
| 7602 | Concepto, Estructura y Clases de Posesión (Art. 700 CC) | Derecho Civil | 731 | 143 | 80,4 % | 5,1x |
| 7603 | Iter Criminis: Grados de Desarrollo del Delito (Art. 7 CP) | Derecho Penal | 833 | 165 | 80,2 % | 5,0x |
| 7604 | Prescripción de la Acción Extracontractual (Art. 2332 CC) | Derecho Civil | 884 | 178 | 79,9 % | 5,0x |
| 7605 | Concepto de Antijuridicidad y Causas de Justificación | Derecho Penal | 699 | 141 | 79,8 % | 5,0x |
| 7606 | Igual Protección de la Ley en el Ejercicio de los Derechos (Art. 19 N° 3 CPR) | Derecho Constitucional | 798 | 163 | 79,6 % | 4,9x |
| 7607 | Inviolabilidad del Dominio y Contenido Esencial (Art. 19 N° 24 y N° 26 CPR) | Derecho Constitucional | 798 | 163 | 79,6 % | 4,9x |
| 7608 | El Principio de Legalidad Penal y Garantías Fundamentales | Derecho Penal | 795 | 163 | 79,5 % | 4,9x |
| 7609 | La Voluntad Jurídica y Formación del Consentimiento | Derecho Civil | 1612 | 330 | 79,5 % | 4,9x |
| 7610 | La Dualidad Título y Modo de Adquirir en Chile | Derecho Civil | 759 | 161 | 78,8 % | 4,7x |
| 7611 | Terminación por Necesidades de la Empresa (Art. 161 CT) y Descuento AFC | Derecho del Trabajo (Laboral) | 621 | 135 | 78,3 % | 4,6x |
| 7612 | La Legítima Defensa (Art. 10 N° 4, 5 y 6 CP) | Derecho Penal | 699 | 153 | 78,1 % | 4,6x |
| 7613 | El Dolo Civil y la Maquinación Fraudulenta (Arts. 44 y 1458 CC) | Derecho Civil | 1612 | 366 | 77,3 % | 4,4x |
| 7614 | La Teoría Chilena de la Posesión Inscrita (Garantía Registral) | Derecho Civil | 731 | 167 | 77,2 % | 4,4x |
| 7615 | Presunción General de Culpa por el Hecho Propio (Art. 2329 CC) | Derecho Civil | 816 | 187 | 77,1 % | 4,4x |
| 7616 | La Causa Lícita y Teoría de la Causa en Chile (Art. 1467 CC) | Derecho Civil | 1249 | 295 | 76,4 % | 4,2x |
| 7617 | Bases de la Institucionalidad y Principios Estructurales (Arts. 1 al 9 CPR) | Derecho Constitucional | 557 | 132 | 76,3 % | 4,2x |
| 7618 | Derecho Administrativo Sancionador y sus Principios Rectores | Derecho Administrativo | 657 | 156 | 76,3 % | 4,2x |
| 7619 | La Tradición de Bienes Raíces y el Conservador de Bienes Raíces (CBR) | Derecho Civil | 759 | 182 | 76,0 % | 4,2x |
| 7620 | La Conducta Humana (Acción y Omisión) | Derecho Civil | 599 | 146 | 75,6 % | 4,1x |
| 7621 | Derechos Reales frente a Derechos Personales | Derecho Civil | 527 | 132 | 75,0 % | 4,0x |
| 7622 | La Mora del Deudor y la Excepción de Contrato No Cumplido | Derecho Civil | 1534 | 384 | 75,0 % | 4,0x |
| 7623 | Concepto Dogmático de Cosa y Bien (Art. 565 CC) | Derecho Civil | 527 | 133 | 74,8 % | 4,0x |
| 7624 | La Enajenación de Bienes del Artículo 1464 del Código Civil | Derecho Civil | 1249 | 323 | 74,1 % | 3,9x |
| 7625 | El Recurso de Casación en el Fondo (Art. 767 CPC) | Derecho Procesal | 859 | 228 | 73,5 % | 3,8x |
| 7626 | Soberanía y el Bloque de Constitucionalidad (Art. 5 inc. 2 CPR) | Derecho Constitucional | 557 | 149 | 73,2 % | 3,7x |
| 7627 | El Daño Reparable: Daño Patrimonial y Daño Moral | Derecho Civil | 884 | 239 | 73,0 % | 3,7x |
| 7628 | El Vínculo de Subordinación y Límites al *Ius Variandi* (Art. 12 CT) | Derecho del Trabajo (Laboral) | 621 | 170 | 72,6 % | 3,7x |
| 7629 | Las Asignaciones Forzosas en el Derecho Civil Chileno (Art. 1167 CC) | Derecho Civil | 921 | 254 | 72,4 % | 3,6x |
| 7630 | La Acción Pauliana o Revocatoria (Art. 2468 CC) | Derecho Civil | 513 | 145 | 71,7 % | 3,5x |
| 7631 | Las Notificaciones Judiciales en el Sistema Procesal Chileno (Arts. 38 a 58 CPC) | Derecho Procesal | 975 | 276 | 71,7 % | 3,5x |
| 7632 | Teoría General de la Impugnación Procesal | Derecho Procesal | 559 | 159 | 71,6 % | 3,5x |
| 7633 | Sistema General y Funciones de la Responsabilidad Civil | Derecho Civil | 599 | 171 | 71,5 % | 3,5x |
| 7634 | El Principio Protector y sus Tres Vertientes Dogmáticas | Derecho del Trabajo (Laboral) | 447 | 130 | 70,9 % | 3,4x |
| 7635 | Alimentos Forzosos y el Régimen de Apremios (Ley N° 14.908) | Derecho Civil | 848 | 261 | 69,2 % | 3,2x |
| 7636 | El Recurso de Reposición o Reconsideración (Arts. 181 al 183 CPC) | Derecho Procesal | 559 | 172 | 69,2 % | 3,2x |
| 7637 | La Compensación Económica en el Divorcio y Nulidad (Arts. 61 a 66 Ley N° 19.947) | Derecho Civil | 848 | 262 | 69,1 % | 3,2x |
| 7638 | La Simulación de los Actos Jurídicos y la Acción de Simulación | Derecho Civil | 968 | 299 | 69,1 % | 3,2x |
| 7639 | Antijuridicidad y Deber General de Cuidado (*Alterum Non Laedere*) | Derecho Civil | 510 | 158 | 69,0 % | 3,2x |
| 7640 | Concurrencia de Responsabilidades: Cúmulo u Opción de Responsabilidades | Derecho Civil | 599 | 188 | 68,6 % | 3,2x |
| 7641 | El Objeto del Acto Jurídico y Objeto Ilícito (Art. 1460 a 1466 CC) | Derecho Civil | 1249 | 400 | 68,0 % | 3,1x |
| 7642 | La Partición de Bienes y Efecto Declarativo (Art. 1317 a 1344 CC) | Derecho Civil | 885 | 284 | 67,9 % | 3,1x |
| 7643 | El Patrimonio Reservado de la Mujer Casada (Artículo 150 CC) | Derecho Civil | 841 | 271 | 67,8 % | 3,1x |
| 7644 | Las Medidas Precautorias en el Juicio Civil (Arts. 290 a 302 CPC) | Derecho Procesal | 967 | 312 | 67,7 % | 3,1x |
| 7645 | El Derecho Real de Herencia y Modos de Adquirirlo (Art. 577 CC) | Derecho Civil | 854 | 278 | 67,4 % | 3,1x |
| 7646 | Apertura y Delación de la Herencia (Arts. 955 y 956 CC) | Derecho Civil | 854 | 279 | 67,3 % | 3,1x |
| 7647 | La Jurisdicción, Competencia y Prórroga (Arts. 108 y ss. COT) | Derecho Procesal | 975 | 319 | 67,3 % | 3,1x |
| 7648 | La Nulidad de Derecho Público en el Ordenamiento Chileno | Derecho Administrativo | 841 | 275 | 67,3 % | 3,1x |
| 7649 | La Sociedad por Acciones (SpA) en el Derecho Chileno (Arts. 424 a 446 C.Com) | Derecho Comercial | 839 | 275 | 67,2 % | 3,1x |
| 7650 | Procedimientos Concursales y Reorganización (Ley N° 20.720) | Derecho Comercial | 847 | 278 | 67,2 % | 3,0x |
| 7651 | Los Actos de Comercio y el Principio de Accesoriedad (Art. 3 C.Com) | Derecho Comercial | 839 | 276 | 67,1 % | 3,0x |
| 7652 | La Posesión Efectiva de la Herencia (Judicial vs. Ley N° 19.903) | Derecho Civil | 921 | 305 | 66,9 % | 3,0x |
| 7653 | Principio de Probidad Administrativa y Transparencia (Art. 8 CPR) | Derecho Administrativo | 488 | 162 | 66,8 % | 3,0x |
| 7654 | Régimen Jurídico de la Nulidad Civil (Absoluta vs. Relativa) | Derecho Civil | 968 | 321 | 66,8 % | 3,0x |
| 7655 | Cumplimiento Forzado de las Obligaciones (Ejecución en Naturaleza) | Derecho Civil | 1534 | 514 | 66,5 % | 3,0x |
| 7656 | La Culpa como Estándar Objetivo de Conducta | Derecho Civil | 510 | 175 | 65,7 % | 2,9x |
| 7657 | Responsabilidad Extracontractual del Estado por Falta de Servicio | Derecho Administrativo | 657 | 226 | 65,6 % | 2,9x |
| 7658 | El Juicio de Precario (Art. 2195 inc. 2 CC) | Derecho Civil | 1323 | 466 | 64,8 % | 2,8x |
| 7659 | Principio de Primacía de la Realidad | Derecho del Trabajo (Laboral) | 447 | 158 | 64,7 % | 2,8x |
| 7660 | Concepto y Catálogo de los Derechos Auxiliares | Derecho Civil | 513 | 182 | 64,5 % | 2,8x |
| 7661 | La Culpa Infraccional y Lex Artis | Derecho Civil | 510 | 182 | 64,3 % | 2,8x |
| 7662 | Las Reglas de Interpretación de los Contratos (Arts. 1560 a 1566 CC) | Derecho Civil | 928 | 341 | 63,3 % | 2,7x |
| 7663 | La Teoría de la Imprevisión y Cláusula *Rebus Sic Stantibus* en Chile | Derecho Civil | 928 | 345 | 62,8 % | 2,7x |
| 7664 | Títulos de Crédito Circulatorios y el Pagaré Mercantil (Ley N° 18.092) | Derecho Comercial | 847 | 318 | 62,5 % | 2,7x |
| 7665 | La Relación Procesal y la Teoría del Emplazamiento | Derecho Procesal | 967 | 377 | 61,0 % | 2,6x |
| 7666 | La Acción de Petición de Herencia (Art. 1264 CC) | Derecho Civil | 885 | 356 | 59,8 % | 2,5x |
| 7667 | La Acción Reivindicatoria (Art. 889 CC) | Derecho Civil | 1323 | 540 | 59,2 % | 2,5x |
| 7668 | El Principio de la Buena Fe Contractual Objetiva (Art. 1546 CC) | Derecho Civil | 798 | 339 | 57,5 % | 2,4x |
| 7669 | La Sociedad Conyugal y Estructura Trilateral de Patrimonios | Derecho Civil | 841 | 358 | 57,4 % | 2,3x |
| 7670 | El Principio de Juridicidad y Estado de Derecho (Arts. 6 y 7 CPR) | Derecho Administrativo | 841 | 360 | 57,2 % | 2,3x |
| 7671 | Consulta y Descarga del Documento Original | Penal / RPA | 135 | 58 | 57,0 % | 2,3x |
| 7672 | Procedimiento de Tutela Laboral y Derechos Fundamentales (Art. 485 CT) | Derecho del Trabajo (Laboral) | 1176 | 531 | 54,8 % | 2,2x |
| 7673 | La Fuerza Obligatoria del Contrato (*Pacta Sunt Servanda*, Art. 1545 CC) | Derecho Civil | 798 | 383 | 52,0 % | 2,1x |
| 7674 | El Recurso de Protección (Art. 20 CPR) | Derecho Constitucional | 1041 | 534 | 48,7 % | 1,9x |
| 7675 | La Nulidad de Derecho Público | Derecho Administrativo | 1037 | 544 | 47,5 % | 1,9x |
| 7676 | Concepto, Resoluciones Apelables y Plazos (Arts. 186 al 189 CPC) | Derecho Procesal | 923 | 495 | 46,4 % | 1,9x |
| 7677 | Resumen Ejecutivo de Práctica Judicial | Penal / RPA | 135 | 174 | 0,0 % | 0,8x |

---

Regenerar esta tabla:

```bash
.venv/bin/python scripts/medir_ahorro_tokens.py
```
