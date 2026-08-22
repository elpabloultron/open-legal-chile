@echo off
chcp 65001 > nul
title Open Legal Chile — Instalador y Launcher

echo ================================================================================
echo    ⚖️  OPEN LEGAL CHILE — INSTALADOR Y LANZADOR RÁPIDO (WINDOWS)  ⚖️
echo ================================================================================
echo.

:: Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no está instalado o no se encuentra en el PATH.
    echo Por favor instala Python desde https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Crear .env si no existe
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" > nul
        echo [OK] Se ha creado el archivo .env a partir de .env.example.
    )
)

echo [OK] Verificando estado del sistema...
echo.
python openlegal.py check

echo.
echo ================================================================================
echo ¿Cómo deseas iniciar Open Legal Chile?
echo  [1] Abrir Consola Interactiva (CLI)
echo  [2] Abrir Dashboard Web en el Navegador
echo  [3] Solo Salir
echo ================================================================================
set /p opt="Selecciona una opción (1-3): "

if "%opt%"=="1" (
    cls
    python openlegal.py
) else if "%opt%"=="2" (
    cls
    python openlegal.py web
) else (
    echo ¡Hasta luego!
)
