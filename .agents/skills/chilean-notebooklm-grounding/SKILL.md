---
name: chilean-notebooklm-grounding
description: Investigación jurídica compleja y síntesis probatoria fundamentada utilizando Google NotebookLM, ingesta documental masiva y generación de grafos de vínculos relacionales.
---

# Habilidad: Investigación Estratégica con NotebookLM y Grafos de Vínculos (chilean-notebooklm-grounding)

## 📌 Principios Rectores
1. **Razonamiento Fundado (Grounded Reasoning):** Toda afirmación o conclusión jurídica compleja debe estar respaldada por fuentes documentales indexadas en un cuaderno de NotebookLM. Si una premisa no figura en las fuentes, no debe presumirse.
2. **Citas Explícitas y Trazables:** Al consultar la base de conocimiento con `notebooklm_query`, se deben respetar las citas y referencias directas provistas por el modelo hacia los números de página de las sentencias, contratos o balances.
3. **Mapeo Relacional de Redes de Poder:** Las investigaciones sobre fraude, simulación absoluta o desvío de fondos públicos exigen representar visualmente las redes corporativas y políticas mediante grafos de nodos y aristas (Mermaid / JSON).

## 📚 Formato de Citación Obligatorio
* Cuaderno de Investigación: `[NotebookLM - Cuaderno ID: <ID>, Fuente: <Título>]`
* Diagrama de Vínculos: `[Grafo Relacional - Nodo: <ID_Nodo> -> Relación: <Vínculo>]`

## 🛠️ Herramientas MCP Disponibles
* `notebooklm_create_notebook`: Crea un cuaderno temático de caso.
* `notebooklm_add_source`: Sube escritos, sentencias o peritajes en PDF al cuaderno.
* `notebooklm_query`: Ejecuta consultas complejas con citaciones directas a las fuentes.
* `generar_grafo_vinculos`: Modela y genera diagramas Mermaid de relaciones societarias y políticas.

---

## 🧠 Workflow 1: Ciclo Completo de Investigación con IA

### Pasos
1. **Creación del Entorno del Caso:** Invocar `notebooklm_create_notebook` asignando un título descriptivo a la causa.
2. **Carga Estratégica de Evidencia:**
   - Ingestar la sentencia de primera instancia, recursos y dictámenes relevantes con `notebooklm_add_source`.
   - Ingestar el escrito principal de la denuncia o demanda.
3. **Interrogación y Detección de Inconsistencias:**
   - Realizar consultas orientadas a identificar contradicciones entre testimonios, cláusulas de contratos y fechas críticas usando `notebooklm_query`.
4. **Construcción del Grafo de Vínculos:**
   - Identificar las entidades clave (autoridades, sociedades compradoras, intermediarios, fondos públicos).
   - Generar el diagrama relacional con `generar_grafo_vinculos` para incrustar en el informe final o reporte de prensa.
