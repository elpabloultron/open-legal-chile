# Charla: Open Legal Chile — de lo básico a lo complejo

Material para la prueba en vivo (docentes de la universidad). No hay libreto: el sistema se prueba
con preguntas al azar; esto es lo que lo explica.

## Para proyectar

| Archivo | Qué es |
| --- | --- |
| `Open_Legal_Chile_como_funciona.pptx` | **La presentación (22 láminas).** Incluye los videos de las animaciones adentro: se reproducen con clic sobre cada cuadro. |
| `animacion_llm.html` | Animación: la máquina de la siguiente palabra (cómo escribe un LLM). |
| `animacion_grafo.html` | Animación: cómo se construyó el grafo (seis etapas, del PDF al mapa). |
| `animacion_citas.html` | Animación: cómo operan las citas (documento vs conversación, y el rastreo). |
| `animacion_flujo.html` | Animación: de la pregunta a la respuesta citada (las cinco etapas). |
| `animacion_caso.html` | Animación: un caso de punta a punta (carpeta → mesa de entrada → fuentes → Word). |
| `animacion_ahorro.html` | Animación: el ahorro de tokens medido (113.458 → 123). |

**Cómo abrirlas sueltas (por si quieren verlas en vivo):** son HTML autónomo — doble clic, y con
`F11` quedan a pantalla completa. Se repiten solas con el botón «Repetir ↻».

## Videos y arte

- `video/*.mp4` — las seis animaciones grabadas (van incrustadas en el PowerPoint). Se regeneran con
  `grabar_animaciones.py` (Playwright + ffmpeg; el venv de grabación vive en `~/.venvs/charla`).
- `video/*_poster.png` — cuadro de portada de cada video (el que se ve hasta hacer clic).
- `img/` — diagramas (capas, flujo, ahorro, muestra real del grafo) y el arte de portada y
  separadores (redes de nodos).

## Cómo se reconstruye el deck

```bash
.venv/bin/python docs/charla/construir_deck.py    # sistema de diseño propio + videos incrustados
```

El diseño es propio (paleta azul tinta + bronce, tipografías Calibri, tarjetas, números grandes y
marcos para imágenes), inspirado en la arquitectura de bloques de `python-pptx-theme-kit` (GPL: se
tomaron las ideas, no su código).

## Orden sugerido (flexible)

1. Láminas 1–9: los cimientos (IA → agente → MCP → skill → capas) — con la animación del LLM.
2. Láminas 10–18: el conocimiento (contexto, grafo, ahorro, citas, caso) — con sus videos.
3. Láminas 19–22: cifras, reglas, **prueba en vivo** y fuentes.

## Nota de honestidad

Las cifras de las láminas salen del propio sistema (grafo, contadores de tokens y el medidor del
corpus), y la última lámina cita las fuentes. La consulta de causas del PJUD fue retirada: no hay
puerta pública y podía entregar información errónea.
