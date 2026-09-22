# Mesa de entrada: de un caso a un plan

Entra un caso —una **carpeta** de expediente, un **texto** pegado o una **consulta** en lenguaje
natural— y sale un **plan**: de qué se trata, qué herramientas usar y en qué orden, y qué falta
para poder avanzar.

```python
# una consulta
caso_analizar("Me despidieron sin aviso previo después de 6 años, el finiquito está mal calculado",
              consulta="qué indemnizaciones me corresponden")

# una carpeta de expediente
caso_analizar("/home/estudio/casos/ailin", tipo="carpeta")

# y después, ejecutar el plan contra las fuentes reales
caso_ejecutar("Me despidieron sin aviso previo…", pasos=[1, 2, 3])
```

## Quién decide qué

| Decide | Quién |
|---|---|
| De qué se trata el caso (materia, fuero, instituciones) | **El código**: patrones de Rol/RIT y palabras clave del derecho chileno |
| Qué herramientas y en qué orden | **El código**, con el plan a la vista para que se pueda discutir |
| Qué falta para avanzar | **El código**: lo enumera en vez de rellenarlo con supuestos |
| Cómo se cuenta, cómo se repregunta, cómo se redacta | **El modelo**, con la skill `chilean-case-intake` |

Que la decisión sea código no es un capricho: no depende de que el modelo tenga un buen día, se
puede probar (hay una tabla de 15 casos en `tests/test_case_intake.py`) y no consume tokens para
algo que es una regla.

## Las dos herramientas

**`caso_analizar`** — sólo lee y propone. No consulta servicios externos ni escribe nada.
Devuelve `materia`, `fuero_probable`, `instituciones`, `plan` (cada paso con su herramienta, sus
argumentos y **por qué**), `faltantes`, `advertencias` y un `resumen` en castellano para leerlo
sin descifrar un JSON.

**`caso_ejecutar`** — ejecuta el plan contra las fuentes reales: BCN, PJUD, CGR, DT, SII, CMF,
SMA, la doctrina indexada y los documentos de la carpeta. Un paso que falla queda anotado con su
error; un paso al que le faltan parámetros se saltea **diciendo por qué**; nunca devuelve un
resultado inventado.

## Lo que hoy no hace, dicho de frente

- **No consulta el expediente por su Rol/RIT.** La suite busca **jurisprudencia** en el Poder
  Judicial, no el estado de una causa: eso se pide en la Oficina Judicial Virtual, y todavía no
  hay conector para eso. El plan lo dice en el paso correspondiente.
- **El buscador del Poder Judicial es literal**: dos o tres palabras responden bien, una frase
  larga no devuelve nada. Por eso ese paso lleva una consulta corta, distinta de la que usa la
  doctrina.
- **La letra del Rol/RIT es una pista, no una verdad**: los tribunales no rotulan igual en todo
  el país. Por eso se exige que coincida con palabras clave antes de afirmar una materia, y
  cuando hay una sola señal, el plan lo advierte.
- **El OCR no corre al analizar**: leer documentos escaneados se demora, así que va en el paso
  de ejecución, donde ya se sabe que hay que pagar ese tiempo.
- **Los documentos se clasifican por su nombre** (demanda, contestación, sentencia, escritura…).
  Si el nombre no dice nada, se anota como documento y el plan no promete haberlo entendido.

---

⚖️ **Compuerta de Revisión Jurídica:** el plan lo arma un sistema. Todo escrito que salga de acá
debe ser validado por un abogado habilitado antes de su firma o presentación.
