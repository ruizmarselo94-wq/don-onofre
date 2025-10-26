import pathlib
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import products, orders, payments, webhooks

app = FastAPI(title="Don Onofre API")

# Routers
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

# --- Dependencia para DB ---
def get_db():
    db = crud.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Raíz ---
@app.get("/", include_in_schema=False)
def root():
    return FileResponse(FRONTEND_DIR / "index.html")