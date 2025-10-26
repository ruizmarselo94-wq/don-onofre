from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from pathlib import Path
from app.api import products, orders, payments, webhooks

app = FastAPI(title="Don Onofre API")

# APIs
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(webhooks.router)

@app.get("/health")
def health():
    return {"status": "ok"}

# Frontend
BASE_DIR = Path(__file__).resolve().parent            # .../backend/app
FRONTEND_DIR = (BASE_DIR / "../../frontend").resolve()# .../frontend

def must(p: Path):
    if not p.exists(): raise HTTPException(404, f"{p.name} no encontrado"); return None
    return str(p)

@app.get("/", include_in_schema=False)
def index():        return FileResponse(must(FRONTEND_DIR / "index.html"))

@app.get("/app.js", include_in_schema=False)
def app_js():       return FileResponse(must(FRONTEND_DIR / "app.js"))

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    p = FRONTEND_DIR / "favicon.ico"
    return FileResponse(str(p)) if p.exists() else Response(status_code=204)
