#!/usr/bin/env bash
# ==============================================================================
# OPEN LEGAL CHILE — BUILDER Y EMPAQUETADOR PARA LINUX (Ubuntu, Mint, Arch, etc.)
# ==============================================================================

set -e

echo "================================================================================"
echo "   ⚖️  OPEN LEGAL CHILE — COMPILADOR Y PAQUETE NATIVO PARA LINUX"
echo "================================================================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Detectar Distribución
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    echo "🐧 Distribución detectada: $NAME ($DISTRO)"
else
    DISTRO="unknown"
fi

# 2. Instalar dependencias según la distribución
echo "📦 Verificando dependencias del sistema..."
case "$DISTRO" in
    ubuntu|debian|linuxmint|pop)
        echo "Instalando paquetes para Ubuntu/Mint/Debian (apt)..."
        sudo apt-get update -qq || true
        sudo apt-get install -y -qq python3 python3-pip python3-venv gir1.2-webkit2-4.0 || true
        ;;
    arch|manjaro|endeavouros)
        echo "Instalando paquetes para Arch Linux (pacman)..."
        sudo pacman -Sy --noconfirm python python-pip webkit2gtk || true
        ;;
    fedora)
        echo "Instalando paquetes para Fedora (dnf)..."
        sudo dnf install -y python3 python3-pip webkit2gtk4.0 || true
        ;;
    *)
        echo "Distribución genérica. Asegúrate de tener Python 3 y WebKit2GTK instalados."
        ;;
esac

# 3. Instalar entorno de compilación
pip3 install --user pyinstaller pywebview setuptools

# 4. Compilar ejecutable ELF nativo de Linux
echo "🔨 Compilando ejecutable nativo para Linux (OpenLegalChile)..."
python3 -m PyInstaller --onefile --noconsole --name "OpenLegalChile" --add-data "web:web" app_desktop.py

# 5. Copiar binario a la raíz del proyecto
cp dist/OpenLegalChile ./OpenLegalChile
chmod +x ./OpenLegalChile

# 6. Instalar lanzador de escritorio (.desktop)
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
cat << 'EOF' > "$DESKTOP_DIR/openlegal.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Open Legal Chile
GenericName=Inteligencia Jurídica
Comment=Plataforma de Inteligencia Jurídica, Asistente Forense y Conectores de Chile
Exec=openlegal web
Icon=accessories-dictionary
Terminal=false
Categories=Office;Legal;Education;Development;
EOF

chmod +x "$DESKTOP_DIR/openlegal.desktop"

# 7. Crear enlace simbólico global opcional
if [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    ln -sf "$SCRIPT_DIR/OpenLegalChile" /usr/local/bin/openlegal-desktop
    echo "✅ Comando global creado: /usr/local/bin/openlegal-desktop"
fi

echo """
================================================================================
   🎉 ¡COMPILACIÓN COMPLETADA CON ÉXITO!
================================================================================
 1. Ejecutable nativo generado en: $SCRIPT_DIR/OpenLegalChile
 2. Lanzador de menú añadido en:   $DESKTOP_DIR/openlegal.desktop
 3. Ahora puedes abrir Open Legal Chile desde tu menú de aplicaciones de:
    • Linux Mint (Cinnamon Menu)
    • Ubuntu (Dash / GNOME)
    • Arch Linux (Rofi / App Launcher)
================================================================================
"""
