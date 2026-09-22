---
name: ponytail-audit
description: >
  Whole-repo audit for over-engineering. Like ponytail-review, but scans the
  entire codebase instead of a diff: a ranked list of what to delete, simplify,
  or replace with stdlib/native equivalents. Use when the user says "audit this
  codebase", "audit for over-engineering", "what can I delete from this repo",
  "find bloat", "ponytail-audit", or "/ponytail-audit". One-shot report, does
  not apply fixes.
---

ponytail-review, repo-wide. Scan the whole tree instead of a diff. Rank
findings biggest cut first.

## Tags

Same as ponytail-review:

- `delete:` dead code, unused flexibility, speculative feature. Replacement: nothing.
- `stdlib:` hand-rolled thing the standard library ships. Name the function.
- `native:` dependency or code doing what the platform already does. Name the feature.
- `yagni:` abstraction with one implementation, config nobody sets, layer with one caller.
- `shrink:` same logic, fewer lines. Show the shorter form.

## Hunt

Deps the stdlib or platform already ships, single-implementation interfaces,
factories with one product, wrappers that only delegate, files exporting one
thing, dead flags and config, hand-rolled stdlib.

## Output

One line per finding, ranked: `<tag> <what to cut>. <replacement>. [path]`.
End with `net: -<N> lines, -<M> deps possible.` Nothing to cut: `Lean already. Ship.`

## Boundaries

Scope: over-engineering and complexity only. Correctness bugs, security holes,
and performance are explicitly out of scope. Route them to a normal review
pass. Lists findings, applies nothing. One-shot.
"stop ponytail-audit" or "normal mode" to revert.

---

## 🎨 Presentación y Lenguaje Claro (Legal Design)

Overlay de `docs/legal_design.md` para este repositorio (por eso va en español: es el idioma de trabajo de Open Legal Chile). Esta skill es de código, no de derecho: hereda las reglas de presentación, no las jurídicas.

- **Quién lee:** quien mantiene el repositorio, que puede no ser experto en este módulo.
- **Lenguaje claro:** todo término técnico o sigla va con su equivalencia simple entre paréntesis la primera vez — `yagni (no construyas lo que todavía no se necesita)`.
- **Salida (estructura):** una línea por hallazgo, del corte más grande al más chico, cerrando con `net: -<N> lines, -<M> deps possible.`
- **Citas:** si la salida toca materia jurídica, se cita en el *Formato de Citación Obligatorio* de `AGENTS.md` §2 (`[BCN - Ley N° 21.643, Art. 2]`); si es código, archivo y línea.
- **Compuerta:** ⚖️ Compuerta de Revisión Jurídica aplica solo si la salida de esta skill termina en un producto jurídico (escrito, memo, comunicación a contraparte). Una skill que simplifica código no produce asesoría jurídica ni la sustituye.
