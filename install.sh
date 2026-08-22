#!/usr/bin/env bash
# ==============================================================================
# Open Legal Chile — Instalador Automatizado para macOS y Linux
# ==============================================================================

set -e

echo ""
echo -e "\033[1;36m================================================================================\033[0m"
echo -e "\033[1;33m   ⚖️  INSTALADOR DE OPEN LEGAL CHILE (macOS / Linux)  ⚖️\033[0m"
echo -e "\033[1;36m================================================================================\033[0m"
echo ""

# 1. Verificar Python 3
echo -e "\033[0;37m🔍 Verificando Python 3...\033[0m"
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo -e "\033[0;31m❌ Error: Python 3 no está instalado.\033[0m"
    echo "👉 En macOS: brew install python"
    echo "👉 En Ubuntu/Debian: sudo apt install python3 python3-pip"
    exit 1
fi

PY_VER=$($PY_CMD --version)
echo -e "\033[0;32m✅ $PY_VER detectado.\033[0m"

# 2. Configurar .env
echo -e "\033[0;37m🔐 Verificando archivo .env local...\033[0m"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "\033[0;32m✅ Se ha creado el archivo '.env' a partir de '.env.example'.\033[0m"
    fi
else
    echo -e "\033[0;32m✅ Archivo .env detectado.\033[0m"
fi

# 3. Diagnóstico de conectores
echo ""
echo -e "\033[0;37m🚀 Ejecutando diagnóstico de conectores...\033[0m"
$PY_CMD openlegal.py check

# 4. Enlace simbólico y lanzador de escritorio
echo ""
read -p "¿Deseas instalar el comando global 'openlegal' en /usr/local/bin? (requiere sudo) [s/N]: " create_symlink
if [[ "$create_symlink" =~ ^[sS]$ ]]; then
    DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
    WRAPPER_PATH="/usr/local/bin/openlegal"
    echo -e "#!/usr/bin/env bash\n$PY_CMD \"$DIR/openlegal.py\" \"\$@\"" | sudo tee "$WRAPPER_PATH" > /dev/null
    sudo chmod +x "$WRAPPER_PATH"
    echo -e "\033[0;32m✅ Comando global 'openlegal' instalado en /usr/local/bin/openlegal\033[0m"
fi

# Instalar .desktop en Linux si corresponde
if [ -d "$HOME/.local/share/applications" ] && [ -f "openlegal.desktop" ]; then
    cp openlegal.desktop "$HOME/.local/share/applications/"
    echo -e "\033[0;32m✅ Lanzador de menú de escritorio instalado en $HOME/.local/share/applications/openlegal.desktop\033[0m"
fi

echo ""
echo -e "\033[1;36m================================================================================\033[0m"
echo -e "\033[1;32m   🎉 ¡INSTALACIÓN COMPLETADA CON ÉXITO!  🎉\033[0m"
echo -e "\033[1;36m================================================================================\033[0m"
echo ""
echo "Formas de uso:"
echo -e " • Iniciar Desktop / Web: \033[1;36mopenlegal web\033[0m o \033[1;36m$PY_CMD app_desktop.py\033[0m"
echo -e " • Chat con IA (Consola): \033[1;36mopenlegal chat\033[0m"
echo -e " • Compilar binario Linux: \033[1;36m./build_linux.sh\033[0m (Ubuntu, Linux Mint, Arch)"
echo -e " • Compilar .app macOS:   \033[1;36m./build_macos.sh\033[0m"
echo -e " • Búsqueda universal:    \033[1;36mopenlegal search 'Ley Karin'\033[0m"
echo ""
