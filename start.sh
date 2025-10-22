#!/bin/bash
# instalar pip y dependencias
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# crear la DB si no existe
if [ ! -f "dononofre.db" ]; then
    python -m app.init_db
fi

# correr la app
uvicorn app.main:app --host 0.0.0.0 --port $PORT
