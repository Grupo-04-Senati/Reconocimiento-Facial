@echo off
title Frontend - Reconocimiento Facial
cd /d "%~dp0"
color 0A

echo ========================================
echo   Frontend - Reconocimiento Facial
echo   React + TypeScript + Vite
echo ========================================
echo.

:: Verificar Node.js
echo [1/3] Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Node.js no encontrado
    echo  Descargar: https://nodejs.org/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version 2^>^&1') do echo  Node %%i
for /f "tokens=*" %%i in ('npm --version 2^>^&1') do echo  npm %%i

:: Instalar dependencias
echo.
echo [2/3] Verificando dependencias...
if not exist "node_modules" (
    echo  Instalando dependencias (npm install)...
    call npm install
    if errorlevel 1 (
        echo  ERROR: Fallo al instalar dependencias
        pause
        exit /b 1
    )
    echo  Dependencias instaladas.
) else (
    echo  Dependencias OK.
)

:: Iniciar servidor
echo.
echo [3/3] Iniciando servidor de desarrollo...
echo.
echo ========================================
echo   Servidor iniciado
echo   URL:      http://localhost:5173
echo   Network:  http://localhost:5173
echo ========================================
echo.
echo  Presiona Ctrl+C para detener
echo ========================================
echo.
call npm run dev
echo.
echo  Servidor detenido.
pause
