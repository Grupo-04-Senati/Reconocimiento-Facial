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
echo  Opcion no valida. Intenta de nuevo.
timeout /t 2 >nul
goto menu

:: =============================================
:: FRONTEND
:: =============================================
:frontend
cls
echo.
echo  Iniciando Frontend...
echo.
start "Frontend-RF" "%~dp0frontend\start.bat"
timeout /t 3 /nobreak >nul
echo.
echo  Frontend abierto en ventana nueva: http://localhost:5173
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
echo  Iniciando Backend...
echo.
start "Backend-RF" "%~dp0backend\start.bat"
timeout /t 3 /nobreak >nul
echo.
echo  Backend abierto en ventana nueva: http://localhost:8000
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
echo  Iniciando Backend y Frontend...
echo.

:: Primero backend
echo  [1/2] Abriendo Backend...
start "Backend-RF" "%~dp0backend\start.bat"
timeout /t 4 /nobreak >nul

:: Luego frontend
echo  [2/2] Abriendo Frontend...
start "Frontend-RF" "%~dp0frontend\start.bat"
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

:: Frontend
echo  [1/2] Frontend - Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Node.js no encontrado
) else (
    echo   Node.js OK
    echo   Instalando paquetes npm...
    cd frontend
    call npm install
    cd ..
    echo   Frontend: dependencias instaladas.
)

echo.

:: Backend
echo  [2/2] Backend - Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python no encontrado
) else (
    echo   Python OK
    if not exist "backend\venv" (
        echo   Creando entorno virtual...
        cd backend
        python -m venv venv
        cd ..
    )
    echo   Instalando paquetes pip...
    cd backend
    call venv\Scripts\activate.bat
    pip install -r requirements.txt --quiet
    cd ..
    echo   Backend: dependencias instaladas.
)

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

:: Node.js
echo  --- Node.js ---
node --version >nul 2>&1
if errorlevel 1 (
    echo   [X] Node.js NO encontrado
) else (
    for /f "tokens=*" %%i in ('node --version 2^>^&1') do echo   [OK] %%i
)

:: Python
echo.
echo  --- Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo   [X] Python NO encontrado
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo   [OK] %%i
)

:: Frontend
echo.
echo  --- Frontend ---
if exist "frontend\node_modules" (
    echo   [OK] Dependencias instaladas
) else (
    echo   [!] Dependencias NO instaladas (ejecutar opcion 4)
)

:: Backend
echo.
echo  --- Backend ---
if exist "backend\venv\Scripts\python.exe" (
    echo   [OK] Entorno virtual creado
) else (
    echo   [!] Entorno virtual NO creado (ejecutar opcion 4)
)

:: .env
echo.
echo  --- Configuracion ---
if exist "backend\.env" (
    echo   [OK] backend\.env existe
) else (
    echo   [!] backend\.env NO existe
)

:: Git
echo.
echo  --- Git ---
git --version >nul 2>&1
if errorlevel 1 (
    echo   [X] Git NO encontrado
) else (
    for /f "tokens=*" %%i in ('git --version 2^>^&1') do echo   [OK] %%i
)

:: Docker
echo.
echo  --- Docker ---
docker --version >nul 2>&1
if errorlevel 1 (
    echo   [!] Docker no encontrado (opcional)
) else (
    for /f "tokens=*" %%i in ('docker --version 2^>^&1') do echo   [OK] %%i
)

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
