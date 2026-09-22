# Setup Automatizado - Windows (PowerShell)
# Reconocimiento Facial - Grupo 04 Senati

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Reconocimiento Facial - Grupo 04" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar herramientas
Write-Host "[1/7] Verificando herramientas..." -ForegroundColor Yellow

try { node --version | Out-Null; Write-Host "  Node.js OK" -ForegroundColor Green }
catch { Write-Host "  Node.js NO encontrado. Instalar desde https://nodejs.org" -ForegroundColor Red }

try { python --version | Out-Null; Write-Host "  Python OK" -ForegroundColor Green }
catch { Write-Host "  Python NO encontrado. Instalar desde https://python.org" -ForegroundColor Red }

try { git --version | Out-Null; Write-Host "  Git OK" -ForegroundColor Green }
catch { Write-Host "  Git NO encontrado" -ForegroundColor Red }

try { docker --version | Out-Null; Write-Host "  Docker OK" -ForegroundColor Green }
catch { Write-Host "  Docker NO encontrado (opcional para Docker Compose)" -ForegroundColor Yellow }

# 2. Configurar git
Write-Host "[2/7] Configurando Git..." -ForegroundColor Yellow
git config --global user.name "Grupo 04 Senati"
git config --global user.email "gruposenatinos@gmail.com"

# 3. Backend setup
Write-Host "[3/7] Configurando Backend..." -ForegroundColor Yellow
Set-Location backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Set-Location ..

# 4. Frontend setup
Write-Host "[4/7] Configurando Frontend..." -ForegroundColor Yellow
Set-Location frontend
npm install
Set-Location ..

# 5. Supabase
Write-Host "[5/7] Verificando Supabase..." -ForegroundColor Yellow
try { supabase --version | Out-Null; Write-Host "  Supabase CLI OK" -ForegroundColor Green }
catch { Write-Host "  Supabase CLI no encontrado. Instalar con: scoop install supabase" -ForegroundColor Yellow }

# 6. Git init
Write-Host "[6/7] Inicializando Git..." -ForegroundColor Yellow
if (-not (Test-Path ".git")) {
    git init
}
git add .
git commit -m "chore: setup inicial del proyecto" --allow-empty

# 7. Resumen
Write-Host "[7/7] Setup completado!" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Proximo paso:" -ForegroundColor Cyan
Write-Host "  1. Instalar gh CLI: winget install --id GitHub.cli" -ForegroundColor White
Write-Host "  2. gh auth login (credenciales del equipo)" -ForegroundColor White
Write-Host "  3. git remote add origin https://github.com/Grupo-04-Senati/Reconocimiento-Facial.git" -ForegroundColor White
Write-Host "  4. git push -u origin main" -ForegroundColor White
Write-Host "  5. Crear proyecto en Supabase Dashboard" -ForegroundColor White
Write-Host "  6. Configurar .env con keys de Supabase" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
