#!/bin/bash
# Guardia PreToolUse de graphify recortada al alcance del grafo de CÓDIGO.
#
# `graphify hook-guard` empuja a consultar el grafo ante cualquier Read/Grep de .py, .md o .txt del
# proyecto: medido el 07-10-2026, leer doctrina/README.md devolvía «MANDATORY: You MUST run graphify
# before reading source files». Pero el grafo excluye el corpus jurídico (.graphifyignore), así que
# ese aviso mandaría a un agente que estudia doctrina a un grafo de código. Para las carpetas que
# .graphifyignore excluye, la guardia se calla y la investigación jurídica sigue su protocolo
# (consulta_maestra, cita_texto). Falla abierta: sin graphify, sin grafo o ante un error, sale 0.
TIPO="${1:-search}"
command -v graphify >/dev/null 2>&1 || exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
ENTRADA="$(cat)" || exit 0

# Una sola fuente de verdad: las reglas de carpeta («nombre/») de .graphifyignore, sin comodines.
FUERA="$(grep -E '^[^#!*?[:space:]][^*?[:space:]]*/$' .graphifyignore 2>/dev/null \
  | sed -e 's#/$##' -e 's#\.#\\.#g' | paste -sd '|' -)"
if [ -n "$FUERA" ] && printf '%s' "$ENTRADA" | grep -Eq "(^|[\"/[:space:]])(${FUERA})/"; then
  exit 0
fi
printf '%s' "$ENTRADA" | graphify hook-guard "$TIPO" 2>/dev/null || true
exit 0
