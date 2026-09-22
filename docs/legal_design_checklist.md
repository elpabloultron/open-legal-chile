# ✅ Checklist de Legal Design — Open Legal Chile

Se pasa **antes** de publicar una skill, una herramienta MCP o un documento. Cada casilla tiene su
criterio; si algo queda sin marcar, no se publica así. Reglas completas en
[`legal_design.md`](legal_design.md).

**¿Qué estás revisando?** (  ) skill  (  ) herramienta MCP  (  ) documento generado  (  ) texto del chat

| ✔ | Punto | Criterio para marcarlo | Regla |
|---|---|---|---|
| [ ] | **Lenguaje claro** | Un no abogado lo entiende sin diccionario. Cada término técnico trae su equivalencia simple **entre paréntesis la primera vez**. Ninguna sigla sin expandir la primera vez. | LD-01 |
| [ ] | **Primero lo práctico** | La primera línea dice qué debe hacer el lector, para cuándo y qué pasa si no lo hace. El fundamento va después. Cero «pronto» / «a la brevedad». | LD-02 |
| [ ] | **Estructura** | Más de tres datos → tabla, lista o esquema. El orden es conclusión → tabla → detalle → fuentes → compuerta. | LD-03 |
| [ ] | **Color no es dato** | Todo estado con color o emoji tiene además su palabra (VERDE/AMARILLO/ROJO, ALTO/MEDIO/BAJO). Se entiende en impresión blanco y negro. | LD-03 |
| [ ] | **Citas** | Cada afirmación normativa o jurisprudencial con el formato de `AGENTS.md` §2 (`[BCN - Ley N° 21.643, Art. 2]`, `[CS - Rol N° …, Fecha: …]`). Nada afirmado «de memoria». | LD-04 |
| [ ] | **Huecos marcados** | Lo que no se pudo verificar, leer o consultar aparece marcado (`[VERIFICAR]`, `[CITA FALTANTE]`, `[ESTADO DE VIGENCIA NO VERIFICADO]`, `[ILEGIBLE EN ORIGINAL: Fs. X]`, `[EVIDENCIA FALTANTE]`). Ningún relleno plausible. | LD-05 |
| [ ] | **Compuerta** | Si es producto de alto riesgo (escrito judicial, despido o finiquito, informe Ley Karin, denuncia o informe a CGR/SMA/CMF/SII, minuta para firma, comunicación a contraparte): lleva la Compuerta de Revisión Jurídica de `AGENTS.md` §5. No dice «listo para presentar». | LD-06 |
| [ ] | **Motor de IA declarado** | Se sabe y se dice con qué se respondió: `soberano` u `ollama` (local) o el proveedor externo por su nombre. Lo que sale del equipo se avisa antes. | LD-07 |
| [ ] | **Documento accesible** | A4, cuerpo ≥ 11 pt, jerarquía por encabezados y no por color, anexos con su número correlativo, y número de página si pasa de una hoja. | LD-08 |
| [ ] | **Nada prometido de más** | Cada cifra trae el comando que la reproduce. Lo planificado se dice «planificado». Ninguna función se describe en presente si no corre hoy. | LD-09 |
| [ ] | **Formato repetido** | Usa la estructura y el formato de citación comunes al repo, no una variante propia sin justificar. | LD-10 |
| [ ] | **Probado** | Corre en la corrida de `pytest` (o trae su caso en `evals/test_cases.json`). Las pruebas que se saltan por red no cuentan como pasadas. | LD-11 |
| [ ] | **Prevención nombrada** | Si existe salida no contenciosa (mediación, PdC, protocolo Ley Karin, carta de cese, cumplimiento voluntario), se nombra antes de la vía judicial, con su norma. No se promete resultado. | LD-12 |

**Cierre:** anota quién revisó y cuándo. Una casilla marcada sin revisión es peor que una casilla
vacía.
