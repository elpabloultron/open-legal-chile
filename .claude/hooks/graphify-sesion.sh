#!/bin/bash
# graphify en las sesiones de Claude Code en la nube: instala la CLI con la versión fijada y deja
# construyendo el grafo de CÓDIGO (graphify-out/, no versionado) en segundo plano.
#
# Nunca falla ni demora la sesión: graphify es una ayuda para navegar el código, no una dependencia
# de la suite. Los hooks PreToolUse de .claude/settings.json ya lo toleran ausente (`|| true`).
# Medido el 07-10-2026: instalar con uv tarda ~3 s en frío y 0,1 s si ya está; el grafo completo,
# ~9 s sin caché (3.740 nodos); `graphify update .` sin cambios de código no reescribe nada.
set -uo pipefail   # sin -e a propósito: cualquier paso puede fallar sin cortar la sesión

# Fijada: el grafo que escribe `graphify update .` cambia de bytes entre versiones (la skill
# versionada en .claude/skills/graphify es 0.9.55; 0.9.79 es la medida el 07-10-2026). Subirla junto
# con CLAUDE.md, .agents/rules/graphify.md y .cursor/rules/graphify.mdc (lo exige una prueba).
GRAPHIFY_VERSION="0.9.79"

cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0

# uv deja el ejecutable en `uv tool dir --bin` (~/.local/bin). Se mira ahí ANTES de decidir si
# instalar: CLAUDE_ENV_FILE solo llega al Bash del agente, no a la próxima corrida de este hook, y
# sin esto cada reanudación de la sesión reinstalaba.
PATH_SESION="$PATH"
BIN="$(uv tool dir --bin 2>/dev/null || true)"
if [ -n "$BIN" ]; then
  case ":$PATH:" in *":$BIN:"*) ;; *) export PATH="$BIN:$PATH" ;; esac
fi

if [ "$(graphify --version 2>/dev/null | head -n 1)" != "graphify ${GRAPHIFY_VERSION}" ] \
    && command -v uv >/dev/null 2>&1; then
  # uv tool aísla graphify (networkx, numpy, rapidfuzz…) del entorno de la suite y cambia de
  # versión sin --force. Con tope de tiempo: una red lenta no puede colgar el arranque.
  timeout 120 uv tool install --quiet "graphifyy==${GRAPHIFY_VERSION}" >/dev/null 2>&1 || true
fi

# Si graphify quedó en un directorio que la sesión no tenía en el PATH, se publica (una vez) en
# CLAUDE_ENV_FILE para que el Bash del agente encuentre `graphify`.
if [ -n "$BIN" ] && [ -x "$BIN/graphify" ] && [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  case ":$PATH_SESION:" in
    *":$BIN:"*) ;;
    *)
      LINEA="export PATH=\"$BIN:\$PATH\""
      grep -qxF "$LINEA" "$CLAUDE_ENV_FILE" 2>/dev/null || echo "$LINEA" >> "$CLAUDE_ENV_FILE"
      ;;
  esac
fi

if ! command -v graphify >/dev/null 2>&1; then
  echo "graphify no quedó instalado: la sesión sigue sin el grafo de código." >&2
  exit 0
fi

mkdir -p graphify-out
if [ "${OPENLEGAL_GRAPHIFY_ESPERAR:-}" = "1" ]; then
  # Para las pruebas: construir en primer plano y poder revisar el resultado.
  timeout 300 graphify update . > graphify-out/.sesion.log 2>&1 || true
else
  nohup setsid timeout 300 graphify update . > graphify-out/.sesion.log 2>&1 < /dev/null &
fi
exit 0
