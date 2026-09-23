# Charla: Open Legal Chile — de lo básico a lo complejo

Material para la prueba en vivo (docentes de la universidad). No hay libreto: el sistema se prueba
con preguntas al azar; esto es lo que lo explica.

## Para proyectar

**`presentacion.html` — la presentación principal.** Un solo archivo HTML, 22 láminas **todas
animadas**, diseño minimalista (papel cálido, tinta y bronce), sin dependencias externas: se abre con
doble clic y con `F` queda a pantalla completa; se navega con `←` `→` (o espacio) y cada lámina se
re-anima al entrar. Empieza por el porqué y el para qué (La idea), sigue por los cimientos y el
conocimiento, y termina en la prueba en vivo y las fuentes.

| Archivo | Qué es |
| --- | --- |
| `presentacion.html` | **La presentación (22 láminas animadas).** ← → navegar · F pantalla completa |
| `Open_Legal_Chile_como_funciona.pptx` | Versión PowerPoint (alternativa), con los videos de las animaciones incrustados (clic sobre cada cuadro). |
| `animacion_idea.html` | Animación suelta: por qué nació y para qué es (su contenido está también en la presentación). |
| `animacion_llm.html` | Animación: la máquina de la siguiente palabra (cómo escribe un LLM). |
| `animacion_grafo.html` | Animación: cómo se construyó el grafo (seis etapas, del PDF al mapa). |
| `animacion_citas.html` | Animación: cómo operan las citas (documento vs conversación, y el rastreo). |
| `animacion_flujo.html` | Animación: de la pregunta a la respuesta citada (las cinco etapas). |
| `animacion_caso.html` | Animación: un caso de punta a punta (carpeta → mesa de entrada → fuentes → Word). |
| `animacion_ahorro.html` | Animación: el ahorro de tokens medido (113.458 → 123). |

**Cómo abrirlas sueltas:** son HTML autónomo — doble clic, y con `F11` quedan a pantalla completa.
Se repiten solas con el botón «Repetir ↻».

## Videos, arte y capturas

- `video/*.mp4` — las animaciones grabadas (van incrustadas en el PowerPoint). Se regeneran con
  `grabar_animaciones.py` (Playwright + ffmpeg; venv de grabación en `~/.venvs/charla`).
- `video/*_poster.png` — cuadro de portada de cada video.
- `img/` — diagramas y arte (redes de nodos de portada y separadores).
- `capturas/` — capturas de referencia de la presentación.

## Cómo se reconstruye y verifica

```bash
.venv/bin/python docs/charla/construir_deck.py                  # el PowerPoint (alternativo)
python docs/charla/grabar_animaciones.py [animación...]         # graba videos (venv de la charla)
python docs/charla/verificar_presentacion.py                    # navega la presentación y mide desbordes
```

La presentación HTML es un archivo único escrito a mano (motor propio de láminas y animaciones,
sin librerías). El PowerPoint usa un sistema de diseño propio (azul tinta + bronce, tipografías
Calibri, tarjetas, números grandes, marcos), inspirado en la arquitectura de bloques de
`python-pptx-theme-kit` (GPL: se tomaron las ideas, no su código).

## Orden sugerido (flexible)

1. Láminas 1–4: **el porqué y el para qué** (ejercicio y estudio) — «La idea».
2. Láminas 5–10: los cimientos (IA → agente → MCP → skill → capas).
3. Láminas 11–18: el conocimiento (contexto, grafo, ahorro, citas, caso).
4. Láminas 19–22: cifras, reglas, **prueba en vivo** y fuentes.

## Nota de honestidad

Las cifras de las láminas salen del propio sistema (grafo, contadores de tokens y el medidor del
corpus), y la última lámina cita las fuentes. Los ejemplos legales de las animaciones citan la norma
(«art. 168 y ss. del Código del Trabajo») y no afirman plazos sin fuente. La consulta de causas del
PJUD fue retirada: no hay puerta pública y podía entregar información errónea.
