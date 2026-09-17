@echo off
title Sistema Reconocimiento Facial - Grupo 04 Senati
cd /d "%~dp0"
color 0A
echo ==========================================
echo   Sistema de Reconocimiento Facial
echo   Grupo 04 Senati
echo ==========================================
echo.
echo  [1] Iniciar Frontend    (puerto 5173)
echo  [2] Iniciar Backend     (puerto 8000)
echo  [3] Iniciar AMBOS
echo  [4] Instalar/Reinstalar dependencias
echo  [0] Salir
echo.
set /p opcion="  Selecciona una opcion: "

if "%opcion%"=="1" goto frontend
if "%opcion%"=="2" goto backend
if "%opcion%"=="3" goto ambos
if "%opcion%"=="4" goto install
if "%opcion%"=="0" goto salir

echo Opcion no valida.
pause
goto fin

:frontend
echo.
echo Iniciando Frontend...
start "Frontend" cmd /k "cd /d "%~dp0frontend" && title Frontend - Reconocimiento Facial && if not exist node_modules npm install && npm run dev"
timeout /t 2 /nobreak >nul
echo Frontend iniciado en http://localhost:5173
goto fin

:backend
echo.
echo Iniciando Backend...
start "Backend" cmd /k "cd /d "%~dp0backend" && title Backend - Reconocimiento Facial && if not exist venv python -m venv venv && call venv\Scripts\activate.bat && if not exist venv\Lib\site-packages\fastapi pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000"
timeout /t 2 /nobreak >nul
echo Backend iniciado en http://localhost:8000
goto fin

:ambos
echo.
echo Iniciando Backend y Frontend...
echo.

start "Backend - Reconocimiento Facial" cmd /k "cd /d "%~dp0backend" && title Backend - Reconocimiento Facial && if not exist venv python -m venv venv && call venv\Scripts\activate.bat && if not exist venv\Lib\site-packages\fastapi pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000"
timeout /t 3 /nobreak >nul

start "Frontend - Reconocimiento Facial" cmd /k "cd /d "%~dp0frontend" && title Frontend - Reconocimiento Facial && if not exist node_modules npm install && npm run dev"

echo ==========================================
echo   Servidores iniciados:
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo ==========================================
echo.
echo Presiona Enter para cerrar esta ventana...
pause >nul
goto fin

:install
echo.
echo ==========================================
echo   Instalando todas las dependencias
echo ==========================================
echo.

echo --- Frontend ---
cd frontend
if not exist "node_modules" (
    call npm install
) else (
    echo node_modules ya existe.
)
cd ..

echo.
echo --- Backend ---
cd backend
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt
cd ..

echo.
echo ==========================================
echo   Dependencias instaladas correctamente
echo ==========================================
pause
goto fin

:salir
exit

:fin
