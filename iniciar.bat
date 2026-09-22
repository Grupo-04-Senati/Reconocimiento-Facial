@echo off
title Sistema Reconocimiento Facial - Grupo 04 Senati
cd /d "%~dp0"
color 0F

:menu
cls
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║    SISTEMA DE RECONOCIMIENTO FACIAL             ║
echo  ║    Grupo 04 Senati                              ║
echo  ╠══════════════════════════════════════════════════╣
echo  ║                                                  ║
echo  ║   [1]  Iniciar Frontend    (React - :5173)      ║
echo  ║   [2]  Iniciar Backend     (FastAPI - :8000)    ║
echo  ║   [3]  Iniciar AMBOS servidores                 ║
echo  ║   [4]  Instalar dependencias                    ║
echo  ║   [5]  Ver estado del proyecto                  ║
echo  ║   [0]  Salir                                    ║
echo  ║                                                  ║
echo  ╚══════════════════════════════════════════════════╝
echo.
set /p opcion="   Selecciona: "

if "%opcion%"=="1" goto frontend
if "%opcion%"=="2" goto backend
if "%opcion%"=="3" goto ambos
if "%opcion%"=="4" goto install
if "%opcion%"=="5" goto estado
if "%opcion%"=="0" goto salir

echo.
echo  Opcion no valida.
timeout /t 2 >nul
goto menu

:: =============================================
:: FRONTEND
:: =============================================
:frontend
cls
echo.
echo  Abriendo Frontend en nueva ventana...
echo.

set "FRONTEND_DIR=%~dp0Frontend"

start "Frontend-RF" cmd /k "title Frontend - Reconocimiento Facial && color 0A && echo. && echo  ======================================== && echo   Frontend - Reconocimiento Facial && echo   React + TypeScript + Vite && echo  ======================================== && echo. && cd /d %FRONTEND_DIR% && echo  Verificando Node.js... && node --version && npm --version && echo. && if not exist node_modules (echo  Instalando dependencias... && npm install && echo.) else (echo  Dependencias OK.) && echo. && echo  Iniciando servidor en http://localhost:5173 && echo  Presiona Ctrl+C para detener && echo  ======================================== && echo. && npm run dev"

timeout /t 3 /nobreak >nul
echo  Frontend abierto: http://localhost:5173
echo.
echo  [Enter] Volver al menu
pause >nul
goto menu

:: =============================================
:: BACKEND
:: =============================================
:backend
cls
echo.
echo  Abriendo Backend en nueva ventana...
echo.

set "BACKEND_DIR=%~dp0backend"

start "Backend-RF" cmd /k "title Backend - Reconocimiento Facial && color 0B && echo. && echo  ======================================== && echo   Backend - Reconocimiento Facial && echo   FastAPI + Python && echo  ======================================== && echo. && cd /d %BACKEND_DIR% && echo  Verificando Python... && python --version && echo. && if not exist venv (echo  Creando entorno virtual... && python -m venv venv) && call venv\Scripts\activate.bat && if not exist venv\Lib\site-packages\fastapi (echo  Instalando dependencias... && pip install -r requirements.txt --quiet) && echo. && echo  Iniciando servidor en http://localhost:8000 && echo  API Docs: http://localhost:8000/docs && echo  Presiona Ctrl+C para detener && echo  ======================================== && echo. && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul
echo  Backend abierto: http://localhost:8000
echo.
echo  [Enter] Volver al menu
pause >nul
goto menu

:: =============================================
:: AMBOS
:: =============================================
:ambos
cls
echo.
echo  Abriendo Backend y Frontend...
echo.

set "BACKEND_DIR=%~dp0backend"
set "FRONTEND_DIR=%~dp0Frontend"

echo  [1/2] Abriendo Backend...
start "Backend-RF" cmd /k "title Backend - Reconocimiento Facial && color 0B && cd /d %BACKEND_DIR% && if not exist venv python -m venv venv && call venv\Scripts\activate.bat && if not exist venv\Lib\site-packages\fastapi pip install -r requirements.txt --quiet && echo. && echo  Backend: http://localhost:8000 && echo  Docs:    http://localhost:8000/docs && echo. && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 4 /nobreak >nul

echo  [2/2] Abriendo Frontend...
start "Frontend-RF" cmd /k "title Frontend - Reconocimiento Facial && color 0A && cd /d %FRONTEND_DIR% && if not exist node_modules npm install && echo. && echo  Frontend: http://localhost:5173 && echo. && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   SERVIDORES INICIADOS                           ║
echo  ║                                                  ║
echo  ║   Frontend:  http://localhost:5173               ║
echo  ║   Backend:   http://localhost:8000               ║
echo  ║   API Docs:  http://localhost:8000/docs          ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  [Enter] Volver al menu
pause >nul
goto menu

:: =============================================
:: INSTALAR DEPENDENCIAS
:: =============================================
:install
cls
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   INSTALANDO DEPENDENCIAS                        ║
echo  ╚══════════════════════════════════════════════════╝
echo.

echo  [1/2] Frontend...
cd /d "%~dp0Frontend"
node --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Node.js no encontrado
) else (
    echo   Node.js OK
    if not exist "node_modules" (
        echo   Instalando paquetes npm...
        call npm install
        echo   Frontend OK.
    ) else (
        echo   Dependencias ya instaladas.
    )
)

echo.
echo  [2/2] Backend...
cd /d "%~dp0backend"
python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python no encontrado
) else (
    echo   Python OK
    if not exist "venv\Scripts\python.exe" (
        echo   Creando entorno virtual...
        python -m venv venv
    )
    call venv\Scripts\activate.bat
    if not exist "venv\Lib\site-packages\fastapi" (
        echo   Instalando paquetes pip...
        pip install -r requirements.txt --quiet
        echo   Backend OK.
    ) else (
        echo   Dependencias ya instaladas.
    )
)

cd /d "%~dp0"
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   INSTALACION COMPLETADA                         ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  [Enter] Volver al menu
pause >nul
goto menu

:: =============================================
:: ESTADO
:: =============================================
:estado
cls
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   ESTADO DEL PROYECTO                            ║
echo  ╚══════════════════════════════════════════════════╝
echo.

echo  --- Node.js ---
node --version >nul 2>&1
if errorlevel 1 (
    echo   [X] Node.js NO encontrado
) else (
    for /f "tokens=*" %%i in ('node --version 2^>^&1') do echo   [OK] %%i
    for /f "tokens=*" %%i in ('npm --version 2^>^&1') do echo   [OK] npm %%i
)

echo.
echo  --- Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo   [X] Python NO encontrado
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo   [OK] %%i
)

echo.
echo  --- Frontend ---
if exist "Frontend\node_modules" (
    echo   [OK] Dependencias instaladas
) else (
    echo   [!] Sin dependencias - ejecuta opcion 4
)
if exist "Frontend\package.json" (
    echo   [OK] package.json existe
)
if exist "Frontend\.env" (
    echo   [OK] .env existe
) else (
    echo   [!] .env no encontrado
)

echo.
echo  --- Backend ---
if exist "backend\venv\Scripts\python.exe" (
    echo   [OK] Entorno virtual creado
) else (
    echo   [!] Sin venv - ejecuta opcion 4
)
if exist "backend\.env" (
    echo   [OK] .env existe
) else (
    echo   [!] .env no encontrado
)

echo.
echo  --- Git ---
git --version >nul 2>&1
if errorlevel 1 (
    echo   [X] Git NO encontrado
) else (
    for /f "tokens=*" %%i in ('git --version 2^>^&1') do echo   [OK] %%i
)

echo.
echo  --- Docker ---
docker --version >nul 2>&1
if errorlevel 1 (
    echo   [!] Docker no encontrado (opcional)
) else (
    for /f "tokens=*" %%i in ('docker --version 2^>^&1') do echo   [OK] %%i
)

cd /d "%~dp0"
echo.
echo  [Enter] Volver al menu
pause >nul
goto menu

:: =============================================
:: SALIR
:: =============================================
:salir
cls
echo.
echo  Hasta luego!
echo.
timeout /t 1 >nul
exit
