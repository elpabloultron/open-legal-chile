---
name: chilean-dossier-assembly
description: Compilación y ensamblaje de expedientes y dossiers procesales en formato PDF judicial formal A4, foliado digital, inserción de portadas separadoras para anexos y exportación dual (tribunales vs. móvil).
---

# Habilidad: Compilación y Ensamblaje de Expedientes Judiciales (chilean-dossier-assembly)

## 📌 Principios Rectores
1. **Estándar de Presentación Procesal:** Los escritos judiciales, denuncias administrativas ante superintendencias (SES, SMA, SUSESO) y presentaciones ante la Contraloría exigen rigurosidad visual y foliado claro.
2. **Separación Correlativa de la Prueba:** Cada anexo probatorio documental debe ir precedido de una portada A4 institucional que indique:
   - Número correlativo de anexo (ej. `ANEXO N° 1`).
   - Título oficial del documento (ej. `Sentencia Definitiva Rol C-373-2024`).
   - Descripción y pertinencia probatoria conforme a las reglas del CPC.
3. **Estrategia de Doble Salida:**
   - **Expediente Completo Consolidado:** Archivo único de 50 a 300+ páginas con el escrito principal y todos los anexos unidos para ingreso formal o juzgados.
   - **Versión Móvil Ligera:** Archivo de 200 a 350 KB que contiene únicamente el escrito principal renderizado con tipografía legible en teléfonos y pantallas táctiles sin superar límites de previsualización.

## 📚 Formato de Citación Obligatorio
* Folio de Expediente: `[Expediente Consolidado, Anexo N° <X>, Fs. <Y>]`
* Oficinas Digitales: `[OJV Ley N° 20.886 / Plataforma CGR / SES]`

## 🛠️ Herramientas MCP Disponibles
* `compile_legal_dossier`: Compila el Markdown, genera separadores y concatena los PDFs.
* `export_brief_ojv`: Genera la estructura formal procesal en HTML y Markdown.

---

## 📑 Workflow 1: Ensamblaje de Expediente Judicial

### Pasos
1. **Revisión del Escrito Principal:** Asegurar que el Markdown contenga la presuma, comparecencia, capítulos de hechos, derecho, peticiones y la lista ordenada de otrosíes y anexos.
2. **Preparación del Catálogo de Anexos:**
   - Crear una lista con `num`, `title`, `desc` y `path` para cada PDF o imagen probatoria.
   - Verificar que todos los archivos referenciados existan en el sistema de archivos.
3. **Compilación Automatizada:**
   - Ejecutar `compile_legal_dossier` definiendo la ruta del archivo consolidado y la ruta opcional de la versión ligera para móvil.
4. **Control de Calidad:**
   - Verificar el número total de páginas resultantes.
   - Comprobar que no existan errores de superposición de texto en los separadores.
   - Verificar que el peso del archivo sea admisible en las plataformas institucionales.
