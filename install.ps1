# ==============================================================================
# Open Legal Chile — Instalador Automatizado para Windows (PowerShell)
# ==============================================================================

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "   ⚖️  INSTALADOR DE OPEN LEGAL CHILE (WINDOWS)  ⚖️" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Python
Write-Host "🔍 Verificando instalación de Python..." -ForegroundColor Gray
$pythonPath = Get-Command python -ErrorAction SilentlyContinue

if (-not $pythonPath) {
    Write-Host "❌ Error: Python no está instalado en tu sistema." -ForegroundColor Red
    Write-Host "👉 Por favor descarga e instala Python 3.9+ desde https://www.python.org/downloads/ (asegúrate de marcar 'Add Python to PATH')." -ForegroundColor Yellow
    exit 1
}

$pyVersion = python --version
Write-Host "✅ $pyVersion detectado." -ForegroundColor Green

# 2. Configurar archivo .env
Write-Host "🔐 Verificando archivo de configuración local .env..." -ForegroundColor Gray
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Se ha creado el archivo '.env' a partir de '.env.example'." -ForegroundColor Green
        Write-Host "💡 Puedes editar '.env' para agregar tu BCN_API_KEY y credenciales de CNE." -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ Archivo .env existente detectado." -ForegroundColor Green
}

# 3. Diagnóstico de conectores
Write-Host ""
Write-Host "🚀 Probando conectores oficiales..." -ForegroundColor Gray
python openlegal.py check

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "   🎉 ¡INSTALACIÓN COMPLETADA CON ÉXITO!  🎉" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Puedes ejecutar Open Legal Chile de las siguientes formas:" -ForegroundColor White
Write-Host " • Iniciar Consola Interactiva:   python openlegal.py" -ForegroundColor Cyan
Write-Host " • Iniciar Dashboard Web:         python openlegal.py web" -ForegroundColor Cyan
Write-Host " • Búsqueda Jurídica Rápida:      python openlegal.py search 'Ley Karin'" -ForegroundColor Cyan
Write-Host ""
