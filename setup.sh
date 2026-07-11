#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "=== Buscando una version de Python compatible (recomendado: 3.11) ==="
PYTHON=""
if command -v py >/dev/null 2>&1 && py -3.11 --version >/dev/null 2>&1; then
    PYTHON="py -3.11"
    echo "Usando Python 3.11 via el launcher 'py' (ideal, compatible con scikit-learn==1.4.2)"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
    echo "Usando: $(python --version 2>&1)"
    echo "AVISO: si tu Python es 3.12 o mas nuevo, la instalacion de scikit-learn==1.4.2 puede"
    echo "fallar mas abajo (no hay wheel precompilado para versiones muy nuevas de Python)."
    echo "Si eso pasa, instala Python 3.11 desde https://www.python.org/downloads/ y vuelve a"
    echo "correr este script."
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
    echo "Usando: $(python3 --version 2>&1)"
else
    echo "ERROR: no se encontro Python instalado."
    echo "Instala Python 3.11 desde https://www.python.org/downloads/ y vuelve a intentar."
    exit 1
fi

echo ""
echo "=== Backend: creando entorno virtual (backend/.venv) ==="
cd backend
if [ -d ".venv" ]; then
    echo ".venv ya existe, lo dejo tal cual (borralo manualmente con 'rm -rf backend/.venv' si quieres uno limpio)."
else
    $PYTHON -m venv .venv
    echo "Entorno virtual creado."
fi

VENV_PY=".venv/Scripts/python.exe"
if [ ! -f "$VENV_PY" ]; then
    echo "ERROR: no se encontro $VENV_PY -- la creacion del venv pudo haber fallado."
    exit 1
fi

echo ""
echo "=== Backend: instalando dependencias (puede tardar varios minutos) ==="
"$VENV_PY" -m pip install --upgrade pip --quiet
"$VENV_PY" -m pip install -e ".[dev,notebook]"

echo ""
echo "=== Backend: verificando que diffprivlib + scikit-learn importen bien ==="
if ! "$VENV_PY" -c "import diffprivlib, sklearn; print('OK: diffprivlib', diffprivlib.__version__, '/ scikit-learn', sklearn.__version__)"; then
    echo ""
    echo "ERROR: diffprivlib o scikit-learn no importan correctamente en este entorno."
    echo "Causa mas probable: tu version de Python es demasiado nueva para scikit-learn==1.4.2."
    echo "Solucion: instala Python 3.11, borra backend/.venv, y vuelve a correr este script."
    exit 1
fi

echo ""
echo "=== Backend: verificando backend/.env ==="
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Se creo backend/.env desde la plantilla (.env.example)."
    echo ""
    echo "IMPORTANTE: backend/.env nunca se sube a GitHub (esta en .gitignore) porque tiene"
    echo "credenciales reales. Pidele a tu companero de equipo el contenido REAL de su"
    echo "backend/.env (DATABASE_URL, JWT_SECRET, FIELD_ENCRYPTION_KEY, BACKUP_ENCRYPTION_KEY)"
    echo "por un canal privado (WhatsApp, Slack, etc.) y reemplaza el contenido de tu"
    echo "backend/.env con esos valores exactos -- NO generes claves nuevas, tienen que"
    echo "coincidir con las que ya usa el resto del equipo o no vas a poder leer los datos"
    echo "cifrados de la base compartida."
else
    echo "backend/.env ya existe, no lo toco."
fi

echo ""
echo "=== Backend: corriendo tests (opcional, para confirmar que todo funciona) ==="
"$VENV_PY" -m pytest tests/ -q || echo "AVISO: si fallaron los de test_auth.py, revisa que backend/.env tenga las credenciales reales de la base de datos compartida."

cd ..

echo ""
echo "=== Frontend: instalando dependencias (npm install) ==="
cd frontend
if ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: no se encontro npm. Instala Node.js 18+ desde https://nodejs.org/ y vuelve a intentar."
    exit 1
fi
npm install
cd ..

echo ""
echo "=========================================="
echo " Listo. Para levantar el proyecto (dos terminales):"
echo ""
echo " Terminal 1 (backend):"
echo "   cd backend"
echo "   .venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000"
echo ""
echo " Terminal 2 (frontend):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo " Luego abre en el navegador:"
echo "   http://localhost:5173        (dashboard de privacidad diferencial)"
echo "   http://localhost:5173/banca  (operacion bancaria)"
echo "   http://localhost:8000/docs   (documentacion de la API)"
echo "=========================================="
