import sys
import os

_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

# Import en TOP-LEVEL - Vercel lo detecta
from app.main import app
