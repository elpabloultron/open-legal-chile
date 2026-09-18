# Medición del ahorro de tokens de LegalGraphify

*Generado por `scripts/medir_ahorro_tokens.py` el 2026-09-18 16:45 UTC (PYTHONHASHSEED=0).*

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
este script solo los recorre y los tabula. El grafo medido tiene 967 nodos y 1366 aristas.

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

- **Instituciones medidas:** 105
- **Ahorro por institución:** mínimo 31,9 %, mediana 74,1 %, máximo 90,5 % (media 73,0 %)
- **Subgrafos devueltos:** entre 58 y 544 tokens (mediana 170)
- **Textos completos de las obras:** entre 135 y 1612 tokens (mediana 847)
- **Instituciones con ahorro ≥ 85 %:** 12 de 105
- **Instituciones con ahorro ≥ 80 %:** 32 de 105
- **Instituciones con ahorro < 70 %:** 43 de 105

## Tabla completa (105 instituciones)

| # | Institución | Área | Texto completo (tokens) | Subgrafo (tokens) | Ahorro | Factor |
|---:|---|---|---:|---:|---:|---:|
| 1 | Extinción del Acto Administrativo: Invalidación vs. Revocación | Derecho Administrativo | 1037 | 98 | 90,5 % | 10,6x |
| 2 | Obligaciones Sujetas a Modalidad: Condición, Plazo y Modo | Derecho Civil | 1112 | 117 | 89,5 % | 9,5x |
| 3 | Indemnización de Perjuicios y Cláusula Penal (Art. 1535 CC) | Derecho Civil | 1534 | 162 | 89,4 % | 9,5x |
| 4 | El Acto Administrativo: Concepto y Efectos (Ley N° 19.880) | Derecho Administrativo | 1037 | 117 | 88,7 % | 8,9x |
| 5 | Obligaciones Naturales y Civiles (Art. 1470 CC) | Derecho Civil | 1112 | 130 | 88,3 % | 8,6x |
| 6 | El Alivio Probatorio de Indicios (Art. 493 CT) | Derecho del Trabajo (Laboral) | 1176 | 143 | 87,8 % | 8,2x |
| 7 | Obligaciones con Pluralidad de Sujetos: Solidaridad Pasiva | Derecho Civil | 1112 | 139 | 87,5 % | 8,0x |
| 8 | Ley Karin (Ley N° 21.643) y el Daño Moral Laboral | Derecho del Trabajo (Laboral) | 1176 | 150 | 87,2 % | 7,8x |
| 9 | Prelación de Créditos y Clases de Privilegios (Arts. 2470 al 2491 CC) | Derecho Civil | 850 | 119 | 86,0 % | 7,1x |
| 10 | Causales de Exoneración y Reducción del Daño | Derecho Civil | 884 | 126 | 85,7 % | 7,0x |
| 11 | Concepto Dogmático de Delito y Teoría de la Conducta (Art. 1 CP) | Derecho Penal | 795 | 118 | 85,2 % | 6,7x |
| 12 | El Control de Constitucionalidad: Inaplicabilidad ante el TC (Art. 93 N° 6 CPR) | Derecho Constitucional | 1041 | 156 | 85,0 % | 6,7x |
| 13 | Autoría y Participación Criminal (Arts. 14 al 17 CP) | Derecho Penal | 833 | 131 | 84,3 % | 6,4x |
| 14 | El Orden Público Económico (Art. 19 N° 21 y N° 22 CPR) | Derecho Constitucional | 798 | 126 | 84,2 % | 6,3x |
| 15 | Responsabilidad Estricta u Objetiva en el Ordenamiento Chileno | Derecho Civil | 816 | 131 | 83,9 % | 6,2x |
| 16 | El Recurso de Queja Disciplinario (Art. 545 COT) | Derecho Procesal | 859 | 139 | 83,8 % | 6,2x |
| 17 | El Error como Vicio del Consentimiento (Arts. 1451 a 1455 CC) | Derecho Civil | 1612 | 265 | 83,6 % | 6,1x |
| 18 | Catálogo de Modos de Extinguir las Obligaciones (Art. 1567 CC) | Derecho Civil | 850 | 141 | 83,4 % | 6,0x |
| 19 | Efectos del Recurso de Apelación y Adhesión | Derecho Procesal | 923 | 154 | 83,3 % | 6,0x |
| 20 | El Recurso de Casación en la Forma (Art. 768 CPC) | Derecho Procesal | 859 | 144 | 83,2 % | 6,0x |
| 21 | El Dominio y su Estatuto Constitucional | Derecho Civil | 759 | 133 | 82,5 % | 5,7x |
| 22 | Presunción de Culpa por el Hecho Ajeno (Art. 2320 CC) | Derecho Civil | 816 | 144 | 82,4 % | 5,7x |
| 23 | Concepto Dogmático y Estructura Trilateral de la Obligación | Derecho Civil | 1112 | 201 | 81,9 % | 5,5x |
| 24 | Estado de Necesidad Justificante (Art. 10 N° 7 CP) | Derecho Penal | 699 | 127 | 81,8 % | 5,5x |
| 25 | La Fuerza o Violencia Moral e Intimidación (Arts. 1456 y 1457 CC) | Derecho Civil | 1612 | 293 | 81,8 % | 5,5x |
| 26 | Tipicidad Subjetiva: Dolo y Culpa | Derecho Penal | 795 | 146 | 81,6 % | 5,4x |
| 27 | Prescripción Extintiva o Liberatoria (Arts. 2514 al 2524 CC) | Derecho Civil | 850 | 157 | 81,5 % | 5,4x |
| 28 | Culpabilidad e Inexigibilidad de Otra Conducta | Derecho Penal | 833 | 156 | 81,3 % | 5,3x |
| 29 | Nexo Causal e Imputación Objetiva (Tesis de Barros Bourie) | Derecho Civil | 884 | 165 | 81,3 % | 5,4x |
| 30 | El Daño Reparable: Daño Patrimonial y Daño Moral | Derecho Civil | 884 | 169 | 80,9 % | 5,2x |
| 31 | Concepto, Estructura y Clases de Posesión (Art. 700 CC) | Derecho Civil | 731 | 143 | 80,4 % | 5,1x |
| 32 | Iter Criminis: Grados de Desarrollo del Delito (Art. 7 CP) | Derecho Penal | 833 | 165 | 80,2 % | 5,0x |
| 33 | Prescripción de la Acción Extracontractual (Art. 2332 CC) | Derecho Civil | 884 | 178 | 79,9 % | 5,0x |
| 34 | Concepto de Antijuridicidad y Causas de Justificación | Derecho Penal | 699 | 141 | 79,8 % | 5,0x |
| 35 | Igual Protección de la Ley en el Ejercicio de los Derechos (Art. 19 N° 3 CPR) | Derecho Constitucional | 798 | 163 | 79,6 % | 4,9x |
| 36 | Inviolabilidad del Dominio y Contenido Esencial (Art. 19 N° 24 y N° 26 CPR) | Derecho Constitucional | 798 | 163 | 79,6 % | 4,9x |
| 37 | El Principio de Legalidad Penal y Garantías Fundamentales | Derecho Penal | 795 | 163 | 79,5 % | 4,9x |
| 38 | La Voluntad Jurídica y Formación del Consentimiento | Derecho Civil | 1612 | 330 | 79,5 % | 4,9x |
| 39 | La Dualidad Título y Modo de Adquirir en Chile | Derecho Civil | 759 | 161 | 78,8 % | 4,7x |
| 40 | Terminación por Necesidades de la Empresa (Art. 161 CT) y Descuento AFC | Derecho del Trabajo (Laboral) | 621 | 135 | 78,3 % | 4,6x |
| 41 | La Legítima Defensa (Art. 10 N° 4, 5 y 6 CP) | Derecho Penal | 699 | 153 | 78,1 % | 4,6x |
| 42 | El Dolo Civil y la Maquinación Fraudulenta (Arts. 44 y 1458 CC) | Derecho Civil | 1612 | 366 | 77,3 % | 4,4x |
| 43 | La Teoría Chilena de la Posesión Inscrita (Garantía Registral) | Derecho Civil | 731 | 167 | 77,2 % | 4,4x |
| 44 | Presunción General de Culpa por el Hecho Propio (Art. 2329 CC) | Derecho Civil | 816 | 187 | 77,1 % | 4,4x |
| 45 | La Causa Lícita y Teoría de la Causa en Chile (Art. 1467 CC) | Derecho Civil | 1249 | 295 | 76,4 % | 4,2x |
| 46 | Bases de la Institucionalidad y Principios Estructurales (Arts. 1 al 9 CPR) | Derecho Constitucional | 557 | 132 | 76,3 % | 4,2x |
| 47 | Derecho Administrativo Sancionador y sus Principios Rectores | Derecho Administrativo | 657 | 156 | 76,3 % | 4,2x |
| 48 | La Tradición de Bienes Raíces y el Conservador de Bienes Raíces (CBR) | Derecho Civil | 759 | 182 | 76,0 % | 4,2x |
| 49 | La Conducta Humana (Acción y Omisión) | Derecho Civil | 599 | 146 | 75,6 % | 4,1x |
| 50 | Derechos Reales frente a Derechos Personales | Derecho Civil | 527 | 132 | 75,0 % | 4,0x |
| 51 | La Mora del Deudor y la Excepción de Contrato No Cumplido | Derecho Civil | 1534 | 384 | 75,0 % | 4,0x |
| 52 | Concepto Dogmático de Cosa y Bien (Art. 565 CC) | Derecho Civil | 527 | 133 | 74,8 % | 4,0x |
| 53 | La Enajenación de Bienes del Artículo 1464 del Código Civil | Derecho Civil | 1249 | 323 | 74,1 % | 3,9x |
| 54 | El Recurso de Casación en el Fondo (Art. 767 CPC) | Derecho Procesal | 859 | 228 | 73,5 % | 3,8x |
| 55 | Soberanía y el Bloque de Constitucionalidad (Art. 5 inc. 2 CPR) | Derecho Constitucional | 557 | 149 | 73,2 % | 3,7x |
| 56 | El Vínculo de Subordinación y Límites al *Ius Variandi* (Art. 12 CT) | Derecho del Trabajo (Laboral) | 621 | 170 | 72,6 % | 3,7x |
| 57 | Las Asignaciones Forzosas en el Derecho Civil Chileno (Art. 1167 CC) | Derecho Civil | 921 | 254 | 72,4 % | 3,6x |
| 58 | La Acción Pauliana o Revocatoria (Art. 2468 CC) | Derecho Civil | 513 | 145 | 71,7 % | 3,5x |
| 59 | Las Notificaciones Judiciales en el Sistema Procesal Chileno (Arts. 38 a 58 CPC) | Derecho Procesal | 975 | 276 | 71,7 % | 3,5x |
| 60 | Teoría General de la Impugnación Procesal | Derecho Procesal | 559 | 159 | 71,6 % | 3,5x |
| 61 | Sistema General y Funciones de la Responsabilidad Civil | Derecho Civil | 599 | 171 | 71,5 % | 3,5x |
| 62 | El Principio Protector y sus Tres Vertientes Dogmáticas | Derecho del Trabajo (Laboral) | 447 | 130 | 70,9 % | 3,4x |
| 63 | Alimentos Forzosos y el Régimen de Apremios (Ley N° 14.908) | Derecho Civil | 848 | 261 | 69,2 % | 3,2x |
| 64 | El Recurso de Reposición o Reconsideración (Arts. 181 al 183 CPC) | Derecho Procesal | 559 | 172 | 69,2 % | 3,2x |
| 65 | La Compensación Económica en el Divorcio y Nulidad (Arts. 61 a 66 Ley N° 19.947) | Derecho Civil | 848 | 262 | 69,1 % | 3,2x |
| 66 | La Simulación de los Actos Jurídicos y la Acción de Simulación | Derecho Civil | 968 | 299 | 69,1 % | 3,2x |
| 67 | Antijuridicidad y Deber General de Cuidado (*Alterum Non Laedere*) | Derecho Civil | 510 | 158 | 69,0 % | 3,2x |
| 68 | Concurrencia de Responsabilidades: Cúmulo u Opción de Responsabilidades | Derecho Civil | 599 | 188 | 68,6 % | 3,2x |
| 69 | El Objeto del Acto Jurídico y Objeto Ilícito (Art. 1460 a 1466 CC) | Derecho Civil | 1249 | 400 | 68,0 % | 3,1x |
| 70 | La Partición de Bienes y Efecto Declarativo (Art. 1317 a 1344 CC) | Derecho Civil | 885 | 284 | 67,9 % | 3,1x |
| 71 | El Patrimonio Reservado de la Mujer Casada (Artículo 150 CC) | Derecho Civil | 841 | 271 | 67,8 % | 3,1x |
| 72 | Las Medidas Precautorias en el Juicio Civil (Arts. 290 a 302 CPC) | Derecho Procesal | 967 | 312 | 67,7 % | 3,1x |
| 73 | Concepto y Catálogo de los Derechos Auxiliares | Derecho Civil | 513 | 166 | 67,6 % | 3,1x |
| 74 | El Derecho Real de Herencia y Modos de Adquirirlo (Art. 577 CC) | Derecho Civil | 854 | 278 | 67,4 % | 3,1x |
| 75 | Apertura y Delación de la Herencia (Arts. 955 y 956 CC) | Derecho Civil | 854 | 279 | 67,3 % | 3,1x |
| 76 | La Jurisdicción, Competencia y Prórroga (Arts. 108 y ss. COT) | Derecho Procesal | 975 | 319 | 67,3 % | 3,1x |
| 77 | La Nulidad de Derecho Público en el Ordenamiento Chileno | Derecho Administrativo | 841 | 275 | 67,3 % | 3,1x |
| 78 | La Sociedad por Acciones (SpA) en el Derecho Chileno (Arts. 424 a 446 C.Com) | Derecho Comercial | 839 | 275 | 67,2 % | 3,1x |
| 79 | Procedimientos Concursales y Reorganización (Ley N° 20.720) | Derecho Comercial | 847 | 278 | 67,2 % | 3,0x |
| 80 | Los Actos de Comercio y el Principio de Accesoriedad (Art. 3 C.Com) | Derecho Comercial | 839 | 276 | 67,1 % | 3,0x |
| 81 | La Posesión Efectiva de la Herencia (Judicial vs. Ley N° 19.903) | Derecho Civil | 921 | 305 | 66,9 % | 3,0x |
| 82 | Principio de Probidad Administrativa y Transparencia (Art. 8 CPR) | Derecho Administrativo | 488 | 162 | 66,8 % | 3,0x |
| 83 | Régimen Jurídico de la Nulidad Civil (Absoluta vs. Relativa) | Derecho Civil | 968 | 321 | 66,8 % | 3,0x |
| 84 | Cumplimiento Forzado de las Obligaciones (Ejecución en Naturaleza) | Derecho Civil | 1534 | 514 | 66,5 % | 3,0x |
| 85 | La Culpa como Estándar Objetivo de Conducta | Derecho Civil | 510 | 175 | 65,7 % | 2,9x |
| 86 | Responsabilidad Extracontractual del Estado por Falta de Servicio | Derecho Administrativo | 657 | 226 | 65,6 % | 2,9x |
| 87 | El Juicio de Precario (Art. 2195 inc. 2 CC) | Derecho Civil | 1323 | 466 | 64,8 % | 2,8x |
| 88 | Principio de Primacía de la Realidad | Derecho del Trabajo (Laboral) | 447 | 158 | 64,7 % | 2,8x |
| 89 | La Culpa Infraccional y Lex Artis | Derecho Civil | 510 | 182 | 64,3 % | 2,8x |
| 90 | Las Reglas de Interpretación de los Contratos (Arts. 1560 a 1566 CC) | Derecho Civil | 928 | 341 | 63,3 % | 2,7x |
| 91 | La Teoría de la Imprevisión y Cláusula *Rebus Sic Stantibus* en Chile | Derecho Civil | 928 | 345 | 62,8 % | 2,7x |
| 92 | Títulos de Crédito Circulatorios y el Pagaré Mercantil (Ley N° 18.092) | Derecho Comercial | 847 | 318 | 62,5 % | 2,7x |
| 93 | La Relación Procesal y la Teoría del Emplazamiento | Derecho Procesal | 967 | 377 | 61,0 % | 2,6x |
| 94 | La Acción de Petición de Herencia (Art. 1264 CC) | Derecho Civil | 885 | 356 | 59,8 % | 2,5x |
| 95 | La Acción Reivindicatoria (Art. 889 CC) | Derecho Civil | 1323 | 540 | 59,2 % | 2,5x |
| 96 | El Principio de la Buena Fe Contractual Objetiva (Art. 1546 CC) | Derecho Civil | 798 | 339 | 57,5 % | 2,4x |
| 97 | La Sociedad Conyugal y Estructura Trilateral de Patrimonios | Derecho Civil | 841 | 358 | 57,4 % | 2,3x |
| 98 | El Principio de Juridicidad y Estado de Derecho (Arts. 6 y 7 CPR) | Derecho Administrativo | 841 | 360 | 57,2 % | 2,3x |
| 99 | Consulta y Descarga del Documento Original | Penal / RPA | 135 | 58 | 57,0 % | 2,3x |
| 100 | Procedimiento de Tutela Laboral y Derechos Fundamentales (Art. 485 CT) | Derecho del Trabajo (Laboral) | 1176 | 531 | 54,8 % | 2,2x |
| 101 | La Fuerza Obligatoria del Contrato (*Pacta Sunt Servanda*, Art. 1545 CC) | Derecho Civil | 798 | 383 | 52,0 % | 2,1x |
| 102 | El Recurso de Protección (Art. 20 CPR) | Derecho Constitucional | 1041 | 534 | 48,7 % | 1,9x |
| 103 | La Nulidad de Derecho Público | Derecho Administrativo | 1037 | 544 | 47,5 % | 1,9x |
| 104 | Concepto, Resoluciones Apelables y Plazos (Arts. 186 al 189 CPC) | Derecho Procesal | 923 | 495 | 46,4 % | 1,9x |
| 105 | Resumen Ejecutivo de Práctica Judicial | Penal / RPA | 135 | 92 | 31,9 % | 1,5x |

---

Regenerar esta tabla:

```bash
.venv/bin/python scripts/medir_ahorro_tokens.py
```
