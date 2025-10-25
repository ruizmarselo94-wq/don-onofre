from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# ---------- PRODUCTOS ----------
class Product(BaseModel):
    id: int
    nombre: str
    precio: float
    descripcion: Optional[str] = None
    imagen: Optional[str] = None
    tipo: Optional[str] = None

    model_config = {"from_attributes": True}  # Pydantic v2


# ---------- CLIENTE ----------
class Customer(BaseModel):
    id: int
    nombre: str
    email: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------- ORDENES ----------
class OrderItem(BaseModel):
    id: Optional[int] = None
    product_id: int
    cantidad: int
    price: float                      # precio unitario al momento de la compra
    product: Optional[Product] = None

    model_config = {"from_attributes": True}


# Para crear orden (el frontend envía product_id y cantidad)
class OrderItemCreate(BaseModel):
    product_id: int
    cantidad: int


class OrderCreate(BaseModel):
    customer_id: int
    items: List[OrderItemCreate]


class Order(BaseModel):
    id: int
    customer: Customer
    items: List[OrderItem]
    total: float
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
