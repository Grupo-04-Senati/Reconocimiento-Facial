@echo off
title Backend - Reconocimiento Facial
cd /d "%~dp0"
color 0B
echo.
echo  ========================================
echo   Backend - Reconocimiento Facial
echo  ========================================
echo.
python --version
echo.
if not exist "venv\Scripts\python.exe" (
    echo  Creando entorno virtual...
    python -m venv venv
)
call venv\Scripts\activate.bat
if not exist "venv\Lib\site-packages\fastapi" (
    echo  Instalando dependencias...
    pip install -r requirements.txt --quiet
)
echo.
echo  Iniciando servidor en http://localhost:8000
echo  API Docs: http://localhost:8000/docs
echo  ========================================
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
