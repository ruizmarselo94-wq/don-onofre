import pathlib
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import products, orders, payments, webhooks

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

BASE_DIR = pathlib.Path(__file__).resolve().parents[2]   # .../don-onofre
FRONTEND_DIR = BASE_DIR / "frontend"

@app.get("/", include_in_schema=False)
def root():
    p = FRONTEND_DIR / "index.html"
    if not p.exists(): raise HTTPException(404, "index.html no encontrado")
    return FileResponse(p)

@app.get("/app.js", include_in_schema=False)
def app_js():
    p = FRONTEND_DIR / "app.js"
    if not p.exists(): raise HTTPException(404, "app.js no encontrado")
    return FileResponse(p)

@app.get("/styles.css", include_in_schema=False)
def styles_css():
    p = FRONTEND_DIR / "styles.css"
    if not p.exists(): raise HTTPException(404, "styles.css no encontrado")
    return FileResponse(p)
