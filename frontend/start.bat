@echo off
title Frontend - Reconocimiento Facial
cd /d "%~dp0"
color 0A
echo.
echo  ========================================
echo   Frontend - Reconocimiento Facial
echo  ========================================
echo.
node --version
npm --version
echo.
if not exist "node_modules" (
    echo  Instalando dependencias...
    call npm install
    echo.
)
echo  Iniciando servidor en http://localhost:5173
echo  ========================================
echo.
call npm run dev
pause
