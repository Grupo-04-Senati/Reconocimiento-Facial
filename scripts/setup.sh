#!/bin/bash
# Setup Automatizado - Linux/macOS
# Reconocimiento Facial - Grupo 04 Senati

set -e

echo "========================================"
echo "  Setup Reconocimiento Facial - Grupo 04"
echo "========================================"

# 1. Verificar herramientas
echo "[1/7] Verificando herramientas..."
command -v node >/dev/null 2>&1 && echo "  Node.js OK" || echo "  Node.js NO encontrado"
command -v python3 >/dev/null 2>&1 && echo "  Python OK" || echo "  Python NO encontrado"
command -v git >/dev/null 2>&1 && echo "  Git OK" || echo "  Git NO encontrado"
command -v docker >/dev/null 2>&1 && echo "  Docker OK" || echo "  Docker NO encontrado"

# 2. Configurar git
echo "[2/7] Configurando Git..."
git config --global user.name "Grupo 04 Senati"
git config --global user.email "gruposenatinos@gmail.com"

# 3. Backend setup
echo "[3/7] Configurando Backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 4. Frontend setup
echo "[4/7] Configurando Frontend..."
cd frontend
npm install
cd ..

# 5. Supabase
echo "[5/7] Verificando Supabase..."
command -v supabase >/dev/null 2>&1 && echo "  Supabase CLI OK" || echo "  Supabase CLI no encontrado"

# 6. Git init
echo "[6/7] Inicializando Git..."
if [ ! -d ".git" ]; then
    git init
fi
git add .
git commit -m "chore: setup inicial del proyecto" --allow-empty

# 7. Resumen
echo "[7/7] Setup completado!"
echo ""
echo "========================================"
echo "  Proximos pasos:"
echo "  1. Instalar gh CLI"
echo "  2. gh auth login"
echo "  3. git remote add origin https://github.com/Grupo-04-Senati/Reconocimiento-Facial.git"
echo "  4. git push -u origin main"
echo "  5. Crear proyecto en Supabase Dashboard"
echo "  6. Configurar .env con keys de Supabase"
echo "========================================"
