from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api import products, orders, payments, webhooks

app = FastAPI(title="Don Onofre API")

# --- Rutas API primero ---
app.include_router(products.router)   # /products
app.include_router(orders.router)     # /orders
app.include_router(payments.router)   # reservado
app.include_router(webhooks.router)   # /webhooks/adams

@app.get("/health")
def health():
    return {"status": "ok"}

# --- Frontend (sirve index.html y archivos estáticos desde /) ---
BASE_DIR = Path(__file__).resolve().parent        # .../backend/app
FRONTEND_DIR = (BASE_DIR / "../../frontend").resolve()

# Montamos el frontend en la RAÍZ con html=True:
# - GET / -> index.html
# - GET /app.js -> frontend/app.js
# - GET /favicon.ico -> frontend/favicon.ico (si existe)
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
