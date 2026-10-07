#!/bin/bash
# Sesiones de Claude Code en la nube: deja instaladas las dependencias para que las pruebas,
# el servidor MCP y el doctor corran sin pasos manuales. En una máquina local no hace nada.
set -euo pipefail

# Carpeta de los hooks, calculada ANTES del cd de abajo: con CLAUDE_PROJECT_DIR definido, un `$0`
# relativo (por ejemplo `./session-start.sh` dentro de .claude/hooks) dejaría de apuntar aquí.
HOOKS_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}"

# Idempotente: si el paquete ya está instalado en modo editable con sus extras, pip no baja nada.
if ! python3 -m pip install -q -e ".[dev]" 2>/dev/null; then
  python3 -m pip install -q --break-system-packages -e ".[dev]"
fi

# poppler (pdftotext/pdfinfo/pdftoppm): lo usan el OCR y la ingesta de PDFs.
if ! command -v pdftotext >/dev/null 2>&1 && command -v apt-get >/dev/null 2>&1; then
  (apt-get install -y -qq poppler-utils >/dev/null 2>&1 || true)
fi

# Sin PYTHONPATH: pytest ya define pythonpath=["."] y mcp_server.py agrega su propia carpeta. Un
# PYTHONPATH relativo hace que cualquier pip/python tome la carpeta actual como importable.

# graphify (grafo de CÓDIGO que pide CLAUDE.md): se instala y construye desacoplado; nunca corta el arranque.
bash "$HOOKS_DIR/graphify-sesion.sh" || true
