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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas del frontend
BASE_DIR = pathlib.Path(__file__).resolve().parents[2]     # .../don-onofre
FRONTEND_DIR = BASE_DIR / "frontend"

# ✅ CORRECCIÓN: montar /static a frontend/static
app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")

# Raíz -> index.html
@app.get("/", include_in_schema=False)
def root():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        # Mensaje claro en prod si falta el archivo en el deploy
        raise HTTPException(status_code=404, detail="index.html no encontrado")
    return FileResponse(index_path)
