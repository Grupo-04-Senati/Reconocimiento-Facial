@echo off
title Backend - Reconocimiento Facial
cd /d "%~dp0"
echo ========================================
echo   Backend - Reconocimiento Facial
echo ========================================
echo.

echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado. Instalar desde https://python.org
    pause
    exit /b 1
)

echo Verificando entorno virtual...
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
    echo.
)

echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo Verificando dependencias...
if not exist "venv\Lib\site-packages\fastapi" (
    echo Instalando dependencias...
    pip install -r requirements.txt
    echo.
)

echo Iniciando servidor FastAPI...
echo URL:      http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Presiona Ctrl+C para detener el servidor
echo ========================================
echo.
uvicorn app.main:app --reload --port 8000
if errorlevel 1 (
    echo.
    echo ERROR: El servidor se detuvo. Verifica los logs arriba.
    pause
)
