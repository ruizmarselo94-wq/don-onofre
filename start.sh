#!/bin/bash

# Ir a la carpeta backend
cd backend

# Actualizar pip y instalar dependencias
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Inicializar la base de datos si no existe
if [ ! -f "dononofre.db" ]; then
    python -m app.init_db
fi

# Levantar el servidor con Uvicorn
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
