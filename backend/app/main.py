# backend/app/main.py
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import products, orders, payments, webhooks
import os

app = FastAPI(title="Don Onofre API")

app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(webhooks.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Resolver FRONTEND_DIR de forma robusta ---
HERE = Path(__file__).resolve()
CANDIDATES = [
    HERE.parents[2] / "frontend",     # repo_root/frontend  (ej: C:\Proyectos\don-onofre\frontend)
    HERE.parents[1] / "frontend",     # backend/frontend     (por si lo movés adentro)
]
FRONTEND_DIR = next((p for p in CANDIDATES if p.is_dir()), None)
if FRONTEND_DIR is None:
    # Permite sobreescribir por env si hiciera falta
    env_dir = os.getenv("FRONTEND_DIR")
    if env_dir and Path(env_dir).is_dir():
        FRONTEND_DIR = Path(env_dir)
    else:
        # Último recurso: no montar estáticos (evita crashear)
        FRONTEND_DIR = None

if FRONTEND_DIR:
    # Sirve index.html en "/" y recursos dentro del mismo árbol
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
