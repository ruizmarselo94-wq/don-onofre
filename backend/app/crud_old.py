from typing import List
from app.schemas import Product, OrderCreate, Order, Customer

# --- MOCK DB ---
PRODUCTS_DB = [
    {"id": 1, "nombre": "Pizza", "precio": 50000.0},
    {"id": 2, "nombre": "Hamburguesa", "precio": 35000.0},
]

ORDERS_DB = []
CUSTOMERS_DB = [
    {"id": 1, "nombre": "Juan Perez", "email": "juan@example.com"},
    {"id": 2, "nombre": "Ana Gomez", "email": "ana@example.com"},
]

# --- PRODUCTOS ---
def get_products() -> List[Product]:
    return [Product(**p) for p in PRODUCTS_DB]

def get_product(product_id: int) -> Product | None:
    p = next((p for p in PRODUCTS_DB if p["id"] == product_id), None)
    return Product(**p) if p else None

# --- CLIENTES ---
def get_customer(customer_id: int) -> Customer | None:
    c = next((c for c in CUSTOMERS_DB if c["id"] == customer_id), None)
    return Customer(**c) if c else None

# --- ORDENES ---
def create_order(order_data: OrderCreate) -> Order:
    customer = get_customer(order_data.customer_id)
    if not customer:
        raise ValueError("Cliente no encontrado")

    items = []
    total = 0.0
    for item in order_data.items:
        product = get_product(item.product_id)
        if not product:
            raise ValueError(f"Producto {item.product_id} no encontrado")
        total += product.precio * item.cantidad
        items.append({"product_id": product.id, "cantidad": item.cantidad})

    order_id = len(ORDERS_DB) + 1
    order = {
        "id": order_id,
        "customer": customer,
        "items": items,
        "total": total,
        "status": "pending"
    }
    ORDERS_DB.append(order)
    return Order(**order)

def get_order(order_id: int) -> Order | None:
    o = next((o for o in ORDERS_DB if o["id"] == order_id), None)
    return Order(**o) if o else None
