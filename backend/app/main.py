from fastapi import FastAPI
from app.api import products, orders, payments, webhooks

app = FastAPI(title="Don Onofre API")

# Rutas usadas por el frontend:
# - GET    /products
# - POST   /orders
# - GET    /orders/{order_id}
# - DELETE /orders/{order_id}
# - POST   /webhooks/adams
app.include_router(products.router)   # /products
app.include_router(orders.router)     # /orders
app.include_router(payments.router)   # reservado (futuros endpoints)
app.include_router(webhooks.router)   # /webhooks/adams

@app.get("/health")
def health():
    return {"status": "ok"}
