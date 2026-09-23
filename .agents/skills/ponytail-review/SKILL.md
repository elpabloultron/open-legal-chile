---
name: ponytail-review
description: >
  Code review focused exclusively on over-engineering. Finds what to delete:
  reinvented standard library, unneeded dependencies, speculative abstractions,
  dead flexibility. One line per finding: location, what to cut, what replaces
  it. Use when the user says "review for over-engineering", "what can we
  delete", "is this over-engineered", "simplify review", or invokes
  /ponytail-review. Complements correctness-focused review, this one only
  hunts complexity.
---

Review diffs for unnecessary complexity. One line per finding: location, what
to cut, what replaces it. The diff's best outcome is getting shorter.

## Format

`L<line>: <tag> <what>. <replacement>.`, or `<file>:L<line>: ...` for
multi-file diffs.

Tags:

- `delete:` dead code, unused flexibility, speculative feature. Replacement: nothing.
- `stdlib:` hand-rolled thing the standard library ships. Name the function.
- `native:` dependency or code doing what the platform already does. Name the feature.
- `yagni:` abstraction with one implementation, config nobody sets, layer with one caller.
- `shrink:` same logic, fewer lines. Show the shorter form.

## 📎 Citas: a pie de página en los documentos

Cuando lo que se entrega es un **documento** —informe en derecho, análisis, memorándum, escrito,
minuta o dossier—, las citas van **a pie de página**, numeradas, con fuente · identificador · enlace.
En la conversación alcanza con citar la fuente en el texto.

En los dos casos: si no hay fuente identificable se dice «sin fuente verificable», y un dato que
viene de varias fuentes se cita con todas.


## Examples

❌ "This EmailValidator class might be more complex than necessary, have you
considered whether all these validation rules are needed at this stage?"

✅ `L12-38: stdlib: 27-line validator class. "@" in email, 1 line, real validation is the confirmation mail.`

✅ `L4: native: moment.js imported for one format call. Intl.DateTimeFormat, 0 deps.`

✅ `repo.py:L88: yagni: AbstractRepository with one implementation. Inline it until a second one exists.`

✅ `L52-71: delete: retry wrapper around an idempotent local call. Nothing replaces it.`

✅ `L30-44: shrink: manual loop builds dict. dict(zip(keys, values)), 1 line.`

## Scoring

End with the only metric that matters: `net: -<N> lines possible.`

If there is nothing to cut, say `Lean already. Ship.` and stop.

## Boundaries

Scope: over-engineering and complexity only. Correctness bugs, security holes,
and performance are explicitly out of scope. Route them to a normal review
pass, not this one. A single smoke test or `assert`-based
self-check is the ponytail minimum, not bloat, never flag it for deletion.
Does not apply the fixes, only lists them.
"stop ponytail-review" or "normal mode": revert to verbose review style.

---

## 🎨 Presentación y Lenguaje Claro (Legal Design)

Overlay de `docs/legal_design.md` para este repositorio (por eso va en español: es el idioma de trabajo de Open Legal Chile). Esta skill es de código, no de derecho: hereda las reglas de presentación, no las jurídicas.

- **Quién lee:** quien revisa el diff, que puede no ser experto en este módulo.
- **Lenguaje claro:** todo término técnico o sigla va con su equivalencia simple entre paréntesis la primera vez — `yagni (no construyas lo que todavía no se necesita)`.
- **Salida (estructura):** una línea por hallazgo (`L<line>: <tag> <what>. <replacement>.`) cerrando con `net: -<N> lines possible.`
- **Citas:** si la salida toca materia jurídica, se cita en el *Formato de Citación Obligatorio* de `AGENTS.md` §2 (`[BCN - Ley N° 21.643, Art. 2]`); si es código, archivo y línea.
- **Compuerta:** ⚖️ Compuerta de Revisión Jurídica aplica solo si la salida de esta skill termina en un producto jurídico (escrito, memo, comunicación a contraparte). Una skill que simplifica código no produce asesoría jurídica ni la sustituye.
