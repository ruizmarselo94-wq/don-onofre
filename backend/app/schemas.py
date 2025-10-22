from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- PRODUCTOS ---
class Product(BaseModel):
    id: int
    nombre: str
    precio: float
    descripcion: Optional[str] = None
    imagen: Optional[str] = None
    tipo: Optional[str] = None

    model_config = {"from_attributes": True}

# --- CLIENTE ---
class Customer(BaseModel):
    id: int
    nombre: str
    email: Optional[str] = None

    model_config = {"from_attributes": True}

# --- ORDENES ---
class OrderItem(BaseModel):
    id: Optional[int] = None
    product_id: int
    cantidad: int
    price: float  # price at time of order
    product: Optional[Product] = None

    model_config = {"from_attributes": True}

# Schema solo para crear orden: NO requiere price
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
