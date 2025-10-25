#!/bin/bash
set -ex

echo "PWD antes:" $(pwd)
echo "Listando raíz:"
ls -la

# Entrar a backend (donde está la carpeta app)
cd backend
echo "PWD después cd backend:" $(pwd)
echo "Listando backend:"
ls -la

# Asegurar que backend esté en PYTHONPATH
export PYTHONPATH="$PWD:${PYTHONPATH:-}"

# Instalar deps
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Inicializar DB si hace falta
if [ ! -f "dononofre.db" ]; then
  python -m app.init_db
fi

# Ejecutar uvicorn (usa -m para garantizar el python correcto)
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
