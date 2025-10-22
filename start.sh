#!/bin/bash
cd backend

# Actualizar pip e instalar dependencias
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Inicializar la base de datos si no existe
if [ ! -f "dononofre.db" ]; then
    python3 -m app.init_db
fi

# Ejecutar servidor
python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
