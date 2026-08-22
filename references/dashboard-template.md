# Plantilla de Tablero (Dashboard) — Open Legal Chile

*Referenciada por los workflows importados (vigilancia regulatoria, registro de renovaciones, checklist de cierre). Mantén los tableros simples y consistentes: el valor es la velocidad de comprensión, no el pulido visual.*

## Estructura (de arriba hacia abajo)

1. **Título y metadatos.** Qué es, cuándo se generó, qué cubre. Una línea.
2. **Estadísticas resumen.** Los conteos que importan, con código de color. "40 hallazgos: 🔴 3 bloqueantes · 🟠 8 altos · 🟡 15 medios · 🟢 14 bajos — 6 vencen esta semana." Esta es la línea más valiosa. Hazla escaneable.
3. **La nota de revisión.** Mismo bloque único que cualquier salida: fuentes, alcance, banderas, antes de confiar. Los tableros no omiten la metadata de seguridad (incluir la ⚖️ Compuerta de Revisión Jurídica).
4. **Gráfico(s).** Uno o dos como máximo. Elige el que muestre la forma:
   - **Distribución de riesgo** (barras): conteos por severidad. Para hallazgos, issues, banderas.
   - **Desglose por categoría** (torta o barras apiladas): conteos por tipo. Para materias de dictámenes, tipos de contrato, categorías de causas.
   - **Línea de tiempo** (tabla ordenada): fechas en orden. Para renovaciones, plazos fatales, checklist de cierre.
   - Nunca más de dos. Un tablero con cinco gráficos es un informe, y los informes son más difíciles de leer que la tabla.
5. **La tabla.** Ordenable, filtrable, con color por severidad/estado. Columnas: las del output original, recortadas a lo que cabe en pantalla. Pon una columna "detalles" o "notas" al final — es la que se trunca.
6. **El árbol de decisión.** Mismas opciones que la salida de texto. "¿Qué sigue?"

## Renderizado por superficie

- **Claude Desktop / Cowork:** artefacto HTML autocontenido, un solo archivo, CSS inline. Sin dependencias externas, sin CDN, sin npm. Tablas HTML con atributos `data-sort` y un sorter JS mínimo (solo ordenar/filtrar). Gráficos: SVG inline o caracteres Unicode de bloques para barras.
- **Terminal (openlegal):** versión Markdown con gráficos de bloques Unicode para las estadísticas resumen, de modo que el usuario vea la forma sin salir de la terminal.
- **Excel (opcional, donde calce):** para el registro de renovaciones, cumplimiento societario y checklist de cierre — todo lo que el usuario llevará a una reunión. Aplicar la defensa contra inyección de fórmulas (prefijar con `'` cualquier celda que comience con `=`, `+`, `-`, `@`).
- **Escapar entrada no confiable (aplicar siempre).** Todo valor que provenga de fuera de la sesión — texto de contratos, hallazgos de due diligence, nombres de contrapartes, descripciones de causas, cualquier string suministrado por el usuario — debe escaparse como HTML antes de aterrizar en el documento. Escapar `&`, `<`, `>`, `"`, `'` al escribir celdas de tabla, líneas de resumen, etiquetas de gráficos y tooltips. En JS inline, fijar texto de celdas con `textContent`, nunca `innerHTML`. No renderizar URLs no confiables en `href`/`src` sin validar esquema (`http:` / `https:` / `mailto:` solo). Un tablero que el revisor abre en un navegador es un límite de confianza; trátalo como tal.

## Mantenlo aburrido

- **Paleta:** rojo / naranja / amarillo / verde para severidad. Gris para neutral. Azul para estado. Nada más.
- **Sin animaciones, sin frameworks, sin fuentes externas.** Un tablero que se rompe offline es un tablero que se rompe.
- **Sin layouts ingeniosos.** Resumen, nota de revisión, gráfico, tabla, árbol de decisión. De arriba hacia abajo. Todos los tableros se ven iguales para que el lector sepa dónde mirar.
- **La versión Markdown importa.** Algunos usuarios están en terminal y no abrirán un navegador. La línea de estadísticas con barras Unicode (p. ej. `🔴 ███ 3  🟠 ████████ 8  🟡 ███████████████ 15  🟢 ██████████████ 14`) les da la forma.
