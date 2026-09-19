"""
Punto de entrada Vercel Serverless Functions.

Vercel detecta 'app' en top-level de este archivo.
Los imports pesados se hacen lazy (solo cuando se usan, no al arrancar).

Referencia: Seccion 4 del PDF (Backend Python/FastAPI en Vercel)
"""
import os
import sys

print("[Vercel] Iniciando backend/api/index.py")

# Configurar sys.path para imports desde backend/
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, backend_dir)
print(f"[Vercel] sys.path[0] = {sys.path[0]}")

try:
    print("[Vercel] Importando app.main...")
    from app.main import app
    print("[Vercel] app.main importada OK")
except Exception as e:
    print(f"[Vercel] ERROR importando app.main: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    raise
