#!/bin/bash
set -ex

echo "PWD: $(pwd)"
echo "Contenido actual:"
ls -la

# Estás ya dentro de /app/backend
export PYTHONPATH="$PWD:${PYTHONPATH:-}"

# Python en Railway es python3
command -v python3
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Inicializar DB si no existe (ruta correcta del módulo)
if [ ! -f "dononofre.db" ]; then
  python3 -m app.db.init_db
fi

# Levantar FastAPI
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
