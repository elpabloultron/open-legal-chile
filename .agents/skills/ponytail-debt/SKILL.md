---
name: ponytail-debt
description: >
  Harvest every `ponytail:` comment in the codebase into a debt ledger, so the
  deliberate shortcuts and deferrals ponytail leaves behind get tracked instead
  of rotting into "later means never". Use when the user says "ponytail debt",
  "/ponytail-debt", "what did ponytail defer", "list the shortcuts", "ponytail
  ledger", or "what did we mark to do later". One-shot report, changes nothing.
---

Every deliberate ponytail shortcut is marked with a `ponytail:` comment naming
its ceiling and upgrade path. This collects them into one ledger so a deferral
can't quietly become permanent.

## Scan

Grep the repo for comment markers, skipping `node_modules`, `.git`, and build
output:

`grep -rnE '(#|//) ?ponytail:' .`  (add other comment prefixes if your stack uses them)

Each hit is one ledger row. The comment prefix keeps prose that merely mentions
the convention out of the ledger.

## 📎 Citas y formato de entrega

- **Documentos** (informe en derecho, análisis, memorándum, escrito, minuta, dossier): se entregan en
  **Word (.docx), no en PDF**, para que se puedan modificar; las citas van **a pie de página**,
  numeradas, con fuente · identificador · enlace.
- **Conversación**: la respuesta va primero y las citas van **al final**, después del texto.

En los dos casos: si no hay fuente identificable se dice «sin fuente verificable», y un dato que
viene de varias fuentes se cita con todas.


## Output

One row per marker, grouped by file:

`<file>:<line>, <what was simplified>. ceiling: <the limit named>. upgrade: <the trigger to revisit>.`

The convention is `ponytail: <ceiling>, <upgrade path>`, so pull the ceiling
and the trigger straight from the comment. Want an owner per row too? add
`git blame -L<line>,<line>`.

Flag the rot risk: any `ponytail:` comment that names no upgrade path or
trigger gets a `no-trigger` tag, those are the ones that silently rot.

End with `<N> markers, <M> with no trigger.` Nothing found: `No ponytail: debt. Clean ledger.`

## Boundaries

Reads and reports only, changes nothing. To persist it, ask and it writes the
ledger to a file (e.g. `PONYTAIL-DEBT.md`). One-shot. "stop ponytail-debt" or
"normal mode" to revert.

---

## 🎨 Presentación y Lenguaje Claro (Legal Design)

Overlay de `docs/legal_design.md` para este repositorio (por eso va en español: es el idioma de trabajo de Open Legal Chile). Esta skill es de código, no de derecho: hereda las reglas de presentación, no las jurídicas.

- **Quién lee:** quien mantiene el repositorio, que puede no ser experto en este módulo.
- **Lenguaje claro:** todo término técnico o sigla va con su equivalencia simple entre paréntesis la primera vez — `no-trigger (el comentario no dice cuándo revisarlo, así que se va a quedar ahí para siempre)`.
- **Salida (estructura):** una fila por marcador agrupada por archivo, cerrando con `<N> markers, <M> with no trigger.`
- **Citas:** si la salida toca materia jurídica, se cita en el *Formato de Citación Obligatorio* de `AGENTS.md` §2 (`[BCN - Ley N° 21.643, Art. 2]`); si es código, archivo y línea.
- **Compuerta:** ⚖️ Compuerta de Revisión Jurídica aplica solo si la salida de esta skill termina en un producto jurídico (escrito, memo, comunicación a contraparte). Una skill que simplifica código no produce asesoría jurídica ni la sustituye.
