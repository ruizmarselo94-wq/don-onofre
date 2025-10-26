from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from pathlib import Path
from app.api import products, orders, payments, webhooks
import pathlib
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Don Onofre API")

# APIs
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(webhooks.router)

# --- CORS para frontend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Podés limitar a tu frontend real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# directorio base del proyecto (sube 2 niveles) y frontend en la raíz del repo
BASE_DIR = pathlib.Path(__file__).resolve().parents[2]   # backend/app -> don-onofre
FRONTEND_DIR = BASE_DIR / "frontend"

# montar archivos estáticos en /static (styles.css, app.js, etc.)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
