#!/bin/bash
# graphify en las sesiones de Claude Code en la nube: instala la CLI con la versión fijada y deja
# construyendo el grafo de CÓDIGO (graphify-out/, no versionado) sin retener el arranque.
#
# Nunca falla ni demora la sesión: graphify es una ayuda para navegar el código, no una dependencia
# de la suite. Los hooks PreToolUse de .claude/settings.json ya lo toleran ausente (`|| true`).
#
# Dos modos. El normal (SessionStart) es síncrono y barato: resuelve dónde queda graphify, publica
# el PATH, reinicia las marcas de aviso de la guardia y lanza el trabajo. El modo `--trabajo` corre
# desacoplado (nohup + setsid, sin heredar stdout ni stderr: si los heredara, Claude Code esperaría
# al grafo) e incluye la instalación, que es lo único que toca la red. Antes la instalación iba en
# el hook mismo con `timeout 120`; con la red degradada, uv reintenta y el arranque quedaba
# detenido hasta 2 minutos (el tope por defecto de un hook de comando es de 600 s).
# Medido el 07-10-2026: instalar con uv tarda ~3 s en frío y 0,1 s si ya está; el grafo completo,
# ~9 s sin caché (3.740 nodos); `graphify update .` sin cambios de código no reescribe nada.
set -uo pipefail   # sin -e a propósito: cualquier paso puede fallar sin cortar la sesión

# Fijada por cadena de suministro (un paquete de terceros que se instala solo en cada sesión) y
# porque `hook-guard` ya trae un modo --strict capaz de DENEGAR un Read (permissionDecision): subir
# la versión es una decisión revisada, no un efecto de que PyPI publique. Los bytes del grafo no
# importan: es local y no se versiona. La skill versionada en .claude/skills/graphify es 0.9.55;
# 0.9.79 es la medida el 07-10-2026. Subirla junto con CLAUDE.md, .agents/rules/graphify.md y
# .cursor/rules/graphify.mdc (lo exige una prueba).
GRAPHIFY_VERSION="0.9.79"

# La ruta del script se calcula ANTES de cambiar de directorio (con CLAUDE_PROJECT_DIR definido,
# un `$0` relativo dejaría de apuntar a este archivo tras el cd).
SCRIPT="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$SCRIPT")/../..}" || exit 0

# uv deja el ejecutable en `uv tool dir --bin` (~/.local/bin). Se mira ahí ANTES de decidir si
# instalar: CLAUDE_ENV_FILE solo llega al Bash del agente, no a la próxima corrida de este hook, y
# sin esto cada reanudación de la sesión reinstalaba.
PATH_SESION="$PATH"
BIN="$(uv tool dir --bin 2>/dev/null || true)"
if [ -n "$BIN" ]; then
  case ":$PATH:" in *":$BIN:"*) ;; *) export PATH="$BIN:$PATH" ;; esac
fi

if [ "${1:-}" = "--trabajo" ]; then
  if [ "$(graphify --version 2>/dev/null | head -n 1)" != "graphify ${GRAPHIFY_VERSION}" ] \
      && command -v uv >/dev/null 2>&1; then
    # uv tool aísla graphify (networkx, numpy, rapidfuzz…) del entorno de la suite y cambia de
    # versión sin --force. Con tope de tiempo: una red lenta no puede colgar ni este proceso.
    timeout 120 uv tool install --quiet "graphifyy==${GRAPHIFY_VERSION}" || echo 'uv tool install falló'
  fi
  if ! command -v graphify >/dev/null 2>&1; then
    echo 'graphify no quedó instalado'
    exit 0
  fi
  timeout 300 graphify update .
  exit 0
fi

if ! command -v graphify >/dev/null 2>&1 && ! command -v uv >/dev/null 2>&1; then
  echo "graphify no quedó instalado: la sesión sigue sin el grafo de código." >&2
  exit 0
fi

# Si graphify queda en un directorio que la sesión no tenía en el PATH, se publica (una vez) en
# CLAUDE_ENV_FILE para que el Bash del agente encuentre `graphify`. Se escribe aunque la
# instalación aún no haya terminado: la línea solo apunta a una carpeta.
if [ -n "$BIN" ] && [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  case ":$PATH_SESION:" in
    *":$BIN:"*) ;;
    *)
      LINEA="export PATH=\"$BIN:\$PATH\""
      grep -qxF "$LINEA" "$CLAUDE_ENV_FILE" 2>/dev/null || echo "$LINEA" >> "$CLAUDE_ENV_FILE"
      ;;
  esac
fi

# La guardia avisa una vez por sesión y tipo: las marcas se reinician al iniciar, reanudar,
# compactar o limpiar (todos pasan por SessionStart).
mkdir -p graphify-out
rm -rf graphify-out/.guardia

if [ "${OPENLEGAL_GRAPHIFY_ESPERAR:-}" = "1" ]; then
  # Para las pruebas: trabajar en primer plano y poder revisar el resultado.
  bash "$SCRIPT" --trabajo > graphify-out/.sesion.log 2>&1 < /dev/null
elif command -v setsid >/dev/null 2>&1; then
  nohup setsid bash "$SCRIPT" --trabajo > graphify-out/.sesion.log 2>&1 < /dev/null &
else
  nohup bash "$SCRIPT" --trabajo > graphify-out/.sesion.log 2>&1 < /dev/null &
fi
exit 0
