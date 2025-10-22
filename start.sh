#!/bin/bash
cd backend
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if [ ! -f "dononofre.db" ]; then
    python -m app.init_db
fi

uvicorn app.main:app --host 0.0.0.0 --port $PORT
