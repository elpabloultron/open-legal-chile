---
name: ponytail-gain
description: >
  Show ponytail's measured impact as a compact scoreboard: less code, less
  cost, more speed, from the benchmark medians. One-shot display, not a
  persistent mode, and not a per-repo number. Trigger: /ponytail-gain,
  "ponytail gain", "what does ponytail save", "show ponytail impact",
  "ponytail scoreboard".
---

# Ponytail Gain

Display this scoreboard when invoked. One-shot: do NOT change mode, write flag
files, or persist anything.

The figures are the published benchmark medians (5 everyday tasks: email
validator, debounce, CSV sum, countdown timer, rate limiter; three models:
Haiku, Sonnet, Opus). They are measured, not computed from the current repo.
Source: `benchmarks/` and the README.

## Scoreboard

Render plain ASCII bars. The bar length shows the measured range; the label
carries the exact figure:

```
  ponytail gain                     benchmark median · 5 tasks · 3 models

  Lines of code   no-skill  ████████████████████  100%
                  ponytail  ██▌·················    6–20%   ▼ 80–94%
  Cost            no-skill  ████████████████████  100%
                  ponytail  █████▌··············   23–53%  ▼ 47–77%
  Speed           ponytail  ▸ 3–6× faster

  This repo:  /ponytail-debt  (shortcuts you deferred)
              /ponytail-audit (what's still cuttable)
```

## 📎 Citas a pie de página

**Toda respuesta que use una fuente la cita a pie de página**, venga de donde venga: conectores del
Estado (BCN, CGR, DT, SII, CMF, SMA, PJUD, CNE, TDLC), doctrina indexada, las guías de la Academia
Judicial o el corpus publicado en Hugging Face. Sin fuente identificable se dice «sin fuente
verificable» en vez de afirmar sin respaldo.

Formato: `[Fuente - Identificador]` y el enlace cuando exista. Un dato con varias fuentes se cita
con todas.

## Honesty boundary

These are benchmark medians, not this repo. NEVER print a per-repo savings
number ("you saved X lines/tokens here"): the unbuilt version was never
written, so there is no real baseline to subtract from in a live repo. The
only real per-repo figures come from `/ponytail-debt` (a counted ledger), and
this card points there instead of inventing one.

## Boundaries

One-shot display. Edits nothing, changes no mode.
"stop ponytail" or "normal mode": revert.

---

## 🎨 Presentación y Lenguaje Claro (Legal Design)

Overlay de `docs/legal_design.md` para este repositorio (por eso va en español: es el idioma de trabajo de Open Legal Chile). Esta skill es de código, no de derecho: hereda las reglas de presentación, no las jurídicas.

- **Quién lee:** quien mantiene el repositorio, que puede no ser experto en este módulo.
- **Lenguaje claro:** todo término técnico o sigla va con su equivalencia simple entre paréntesis la primera vez — `mediana (el valor del medio: la mitad de los casos queda por debajo)`.
- **Salida (estructura):** barras ASCII planas, sin depender del color, y sin cifra por repositorio: la regla de honestidad de esta misma skill ya lo prohíbe y coincide con la regla LD-09.
- **Citas:** si la salida toca materia jurídica, se cita en el *Formato de Citación Obligatorio* de `AGENTS.md` §2 (`[BCN - Ley N° 21.643, Art. 2]`); si es código, archivo y línea.
- **Compuerta:** ⚖️ Compuerta de Revisión Jurídica aplica solo si la salida de esta skill termina en un producto jurídico (escrito, memo, comunicación a contraparte). Una skill que simplifica código no produce asesoría jurídica ni la sustituye.
