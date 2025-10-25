from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from pathlib import Path

from app.api import products, orders, payments, webhooks

app = FastAPI(title="Don Onofre API")

# --- APIs ---
app.include_router(products.router)   # /products
app.include_router(orders.router)     # /orders
app.include_router(payments.router)   # /...
app.include_router(webhooks.router)   # /webhooks/adams

@app.get("/health")
def health():
    return {"status": "ok"}

# --- Frontend (servir archivos explícitos) ---
BASE_DIR = Path(__file__).resolve().parent          # .../backend/app
FRONTEND_DIR = (BASE_DIR / "../../frontend").resolve()

def must_exist(p: Path):
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"{p.name} no encontrado")
    return str(p)

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(must_exist(FRONTEND_DIR / "index.html"))

@app.get("/app.js", include_in_schema=False)
def app_js():
    return FileResponse(must_exist(FRONTEND_DIR / "app.js"))

@app.get("/styles.css", include_in_schema=False)
def styles_css():
    p = FRONTEND_DIR / "styles.css"
    if p.exists():
        return FileResponse(str(p))
    return Response(status_code=204)

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    p = FRONTEND_DIR / "favicon.ico"
    if p.exists():
        return FileResponse(str(p))
    return Response(status_code=204)
