#!/usr/bin/env bash
# ==============================================================================
# OPEN LEGAL CHILE — BUILDER PARA MACOS (.app BUNDLE)
# ==============================================================================

set -e

echo "================================================================================"
echo "   ⚖️  OPEN LEGAL CHILE — COMPILADOR DE .APP PARA MACOS (Apple Silicon / Intel)"
echo "================================================================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Instalar dependencias
pip3 install --user pyinstaller pywebview setuptools

# 2. Compilar aplicación macOS .app
echo "🍎 Generando paquete OpenLegalChile.app..."
python3 -m PyInstaller --onefile --windowed --name "OpenLegalChile" --add-data "web:web" app_desktop.py

echo """
================================================================================
   🎉 ¡PAQUETE MACOS GENERADO CON ÉXITO!
================================================================================
 Aplicación nativa disponible en: $SCRIPT_DIR/dist/OpenLegalChile.app
 Puedes arrastrar 'OpenLegalChile.app' a tu carpeta /Applications.
================================================================================
"""
