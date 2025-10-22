#!/bin/bash
# Instalar dependencias
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Inicializar DB si no existe
if [ ! -f "dononofre.db" ]; then
    python -m app.init_db
fi

# Ejecutar la app con uvicorn
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
