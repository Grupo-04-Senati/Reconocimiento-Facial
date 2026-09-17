@echo off
title Backend - Reconocimiento Facial
cd /d "%~dp0"
color 0B

echo ========================================
echo   Backend - Reconocimiento Facial
echo   FastAPI + Python
echo ========================================
echo.

:: Verificar Python
echo [1/4] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python no encontrado
    echo  Descargar: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  %%i

:: Crear venv si no existe
echo.
echo [2/4] Verificando entorno virtual...
if not exist "venv\Scripts\python.exe" (
    echo  Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo  ERROR: No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
    echo  Entorno virtual creado.
) else (
    echo  Entorno virtual encontrado.
)

:: Activar venv
echo.
echo [3/4] Activando entorno virtual...
call venv\Scripts\activate.bat

:: Verificar/instalar dependencias
echo.
echo [4/4] Verificando dependencias...
if not exist "venv\Lib\site-packages\fastapi" (
    echo  Instalando dependencias (puede tardar)...
    pip install -r requirements.txt --quiet
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
echo ========================================
echo   Servidor iniciado
echo   URL:      http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   ReDoc:    http://localhost:8000/redoc
echo ========================================
echo.
echo  Presiona Ctrl+C para detener
echo ========================================
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
echo.
echo  Servidor detenido.
pause
