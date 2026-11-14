---
name: chilean-dogmatic-graphify
description: Especialista en Subsunción Dogmática y Grafo de Conocimiento Jurídico (LegalGraphify): navegación de 228 tratados doctrinales chilenos, 21 guías de la Academia Judicial, extracción de subgrafos con Personalized PageRank (PPR) y análisis topológico de radio de impacto normativo (blast radius).
---

# Habilidad: Subsunción Dogmática y LegalGraphify (chilean-dogmatic-graphify)

## 📌 Principios Rectores
1. **Subsunción Jurídica Tripartita:** Toda construcción dogmática articula el precepto legal positivo (BCN), la doctrina de los tratadistas chilenos canónicos (Barros Bourie, Ramos Pazos, Peñailillo, Somarriva, Claro Solar, Abeliuk, Maturana) y la jurisprudencia uniforme de las Cortes.
2. **Eficiencia Estructural por Subgrafo (`LegalGraphify`):** En lugar de saturar la ventana de contexto con tratados completos, se extrae el subgrafo sintético de 2 saltos con ranking de centralidad personalizada (*Personalized PageRank* / PPR) y ponderación léxica BM25F/IDF, logrando una reducción mediana de tokens del 99,9 %.
3. **Cero Terminología de Common Law:** Queda estrictamente prohibido emplear conceptos ajenos a la tradición continental como *punitive damages*, *discovery*, *at-will employment*, *subpoena*, *grand jury* o *summary judgment*. Utilizar siempre instituciones dogmáticas chilenas (*daño moral*, *lucro cesante*, *condición resolutoria tácita*, *responsabilidad extracontractual por el hecho propio o ajeno*, *casación en el fondo*).
4. **Trazabilidad en Hugging Face:** Cada institución doctrinal se vincula a su archivo fuente verificable en el repositorio público `pablobenavidesj/doctrina-jurisprudencia-chile`.

## 📎 Citas y formato de entrega

- **Documentos** (informe en derecho, minuta dogmática, análisis de impacto normativo): se entregan en **Word (.docx), no en PDF**, para que se puedan modificar; las citas van **a pie de página**, numeradas, con fuente · identificador · enlace.
- **Conversación**: la respuesta va primero y las citas van **al final**, después del texto.

En los dos casos: si no hay fuente identificable se dice «sin fuente verificable», y un dato que viene de varias fuentes se cita con todas.

## 📚 Formato de Citación Obligatorio
* Doctrina canónica: `[Doctrina - <Autor>, <Tratado>, Institución: <Nombre>]`
* Repositorio Hugging Face: `[Hugging Face - pablobenavidesj/doctrina-jurisprudencia-chile, Archivo: <Ruta>]`
* Norma legal: `[BCN - Código Civil, Art. <Número>]`
* Jurisprudencia CS: `[CS - Rol N° <Número>-<Año>, Fecha: <D-M-A>]`

## 🛠️ Herramientas MCP Disponibles
* `consulta_maestra`: Primer paso obligatorio; ejecuta en paralelo la búsqueda en el mapa del corpus de Hugging Face, doctrina canónica, grafo y conectores oficiales.
* `graphify_consulta_subgrafo`: Extrae el subgrafo relacional de 2 saltos en torno a una institución o precepto, incluyendo los vecinos más relevantes según *Personalized PageRank* (`ppr_vecinos_clave`).
* `graphify_explicar_institucion`: Genera una explicación dogmática de 360° con fundamento normativo, autores y criterios de la Corte Suprema.
* `graphify_trazar_camino`: Traza el camino relacional más corto (BFS) entre dos instituciones jurídicas o normas legales.
* `graphify_analizar_impacto`: Calcula el radio de impacto topológico (*blast radius*) ante una reforma legal o cambio jurisprudencial.
* `graphify_god_nodes`: Identifica los nodos estructurales centrales del ordenamiento mediante centralidad de grado.
* `doctrina_search` y `doctrina_get_institucion`: Búsqueda semántica FTS5 BM25 sobre las 11.858 fichas dogmáticas locales.

---

## 🎨 Presentación y Lenguaje Claro (Legal Design)

Reglas de [`docs/legal_design.md`](../../../docs/legal_design.md) aplicadas a esta skill. No cambian el fondo jurídico: cambian cómo se entrega.

- **Quién lee:** abogados litigantes, jueces, académicos e investigadores que requieren fundamentación doctrinal rigurosa y mapeo de relaciones entre normas e instituciones.
- **Lenguaje claro:** el primer término técnico de cada sección lleva su explicación directa entre paréntesis — `subsunción dogmática (encuadrar los hechos probados del caso dentro de los requisitos teóricos y legales de una institución jurídica)`.
- **Salida (estructura):** planteamiento dogmático + definición canónica y elementos de la institución + grafo relacional (nodos centrales PPR y normas conectadas) + concordancias doctrinales y jurisprudenciales + conclusión estratégica y citas verificables.
- **Citas:** las de *Formato de Citación Obligatorio*, siempre; nunca atribuir una opinión doctrinal a un tratadista sin verificar su ficha en `doctrina.db` o Hugging Face.
- **Compuerta:** ⚖️ Compuerta de Revisión Jurídica: todo informe en derecho o minuta doctrinal debe ser validado por un abogado habilitado antes de su incorporación en escritos judiciales o dictámenes.

---

## 🔄 Workflow: Construcción de Informe Dogmático con `LegalGraphify`

1. **Consulta Inicial del Mapa y Subgrafo:** Invocar `consulta_maestra` y `graphify_consulta_subgrafo` para identificar el nodo rector, sus artículos asociados y los vecinos priorizados por *Personalized PageRank* (`ppr_vecinos_clave`).
2. **Trazado de Caminos Relacionales:** Cuando el caso involucre dos instituciones aparentemente distantes (por ejemplo, *cúmulo de responsabilidades* y *prescripción extintiva*), invocar `graphify_trazar_camino` para demostrar el puente normativo y doctrinal.
3. **Extracción de Tratadistas Canónicos:** Recuperar las fichas completas con `doctrina_get_institucion` y `huggingface_search_dataset`, contrastando posturas doctrinales cuando exista discusión en la literatura chilena.
4. **Cierre y Compuerta:** Estructurar la respuesta según los cinco capítulos canónicos del Informe en Derecho e incluir la ⚖️ **Compuerta de Revisión Jurídica**.
