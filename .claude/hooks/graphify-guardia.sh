#!/bin/bash
# Guardia PreToolUse de graphify recortada al alcance del grafo de CÓDIGO.
#
# `graphify hook-guard` empuja a consultar el grafo ante cualquier Read/Grep de .py, .md o .txt del
# proyecto: medido el 07-10-2026, leer doctrina/README.md devolvía «MANDATORY: You MUST run graphify
# before reading source files». Pero el grafo excluye el corpus jurídico (.graphifyignore), así que
# ese aviso mandaría a un agente que estudia doctrina a un grafo de código. La decisión de alcance
# vive en graphify_alcance.py (Python puro, probado también en Windows): calla en las carpetas que
# .graphifyignore excluye y avisa una sola vez por sesión y tipo (search/read), porque el aviso de
# graphify pesa ~100 tokens por Read y ~47 por Grep. Este script es solo el envoltorio.
#
# Falla abierta: sin graphify, sin grafo, sin python o ante cualquier error, sale 0 sin decir nada.
# Costo medido el 07-10-2026 (graphify 0.9.79 real, grafo presente): ~40 ms cuando calla (corpus o
# ya avisado: el arranque de Python) y ~140 ms cuando avisa (más el arranque de graphify; antes se
# pagaban ~100 ms en CADA llamada). Sin graph.json, la salida temprana de abajo solo cuesta un `test -f`.
TIPO="${1:-search}"
AQUI="$(cd "$(dirname "$0")" && pwd)"   # antes del cd: la ruta no depende del directorio actual

command -v graphify >/dev/null 2>&1 || exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
[ -f "${GRAPHIFY_OUT:-graphify-out}/graph.json" ] || exit 0

PY="$(command -v python3 || command -v python || true)"
[ -n "$PY" ] || exit 0
ENTRADA="$(cat)" || exit 0

MARCA="$(printf '%s' "$ENTRADA" | "$PY" "$AQUI/graphify_alcance.py" "$TIPO" 2>/dev/null)"
RC=$?
# 1 = dentro del grafo y sin aviso previo; 0 = fuera del grafo o ya avisado; otro = error.
[ "$RC" -eq 1 ] || exit 0

SALIDA="$(printf '%s' "$ENTRADA" | graphify hook-guard "$TIPO" 2>/dev/null || true)"
[ -n "$SALIDA" ] || exit 0
printf '%s\n' "$SALIDA"
# Se marca solo cuando graphify avisó de verdad: así un `git status` que no genera aviso no
# consume el del primer Grep de código.
if [ -n "$MARCA" ]; then
  mkdir -p "$(dirname "$MARCA")" 2>/dev/null && : > "$MARCA" 2>/dev/null
fi
exit 0
