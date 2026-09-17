@echo off
title Frontend - Reconocimiento Facial
cd /d "%~dp0"
echo ========================================
echo   Frontend - Reconocimiento Facial
echo ========================================
echo.

echo Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js no encontrado. Instalar desde https://nodejs.org
    pause
    exit /b 1
)

echo Verificando dependencias...
if not exist "node_modules" (
    echo Instalando dependencias (npm install)...
    npm install
    echo.
)

echo Iniciando servidor de desarrollo...
echo URL: http://localhost:5173
echo.
echo Presiona Ctrl+C para detener el servidor
echo ========================================
echo.
npm run dev
if errorlevel 1 (
    echo.
    echo ERROR: El servidor se detuvo.
    pause
)
