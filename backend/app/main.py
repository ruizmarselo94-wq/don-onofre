from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pathlib import Path

from app.api import products, orders, payments, webhooks

app = FastAPI(title="Don Onofre API")

# === Montar frontend ===
# Asumimos que 'frontend/' está en la raíz del repo, al mismo nivel que 'backend/'
BASE_DIR = Path(__file__).resolve().parent  # .../backend/app
FRONTEND_DIR = (BASE_DIR / "../../frontend").resolve()

print("FRONTEND_DIR=", FRONTEND_DIR)
print("INDEX EXISTS=", (FRONTEND_DIR / "index.html").exists())

# /static -> archivos del frontend (index.html referencia /static/app.js y /static/styles.css)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

# GET / -> servir index.html
@app.get("/", include_in_schema=False)
def serve_index():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="index.html no encontrado")

# Opcional: evitar error por favicon
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    fav = FRONTEND_DIR / "favicon.ico"
    if fav.exists():
        return FileResponse(str(fav))
    return Response(status_code=204)

# === APIs usadas por el frontend ===
app.include_router(products.router)   # /products
app.include_router(orders.router)     # /orders
app.include_router(payments.router)   # reservado (futuros endpoints)
app.include_router(webhooks.router)   # /webhooks/adams

# Healthcheck
@app.get("/health")
def health():
    return {"status": "ok"}
