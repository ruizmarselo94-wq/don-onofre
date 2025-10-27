from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import products, orders, webhooks
import os

app = FastAPI(title="Don Onofre API")

app.include_router(products.router)
app.include_router(orders.router)
app.include_router(webhooks.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HERE = Path(__file__).resolve()
CANDIDATES = [
    HERE.parents[2] / "frontend",  # repo_root/frontend
    HERE.parents[1] / "frontend",  # backend/frontend (por si se mueve)
]
FRONTEND_DIR = next((p for p in CANDIDATES if p.is_dir()), None)
if FRONTEND_DIR:
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
