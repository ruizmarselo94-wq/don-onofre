from typing import List, Optional
from decimal import Decimal, InvalidOperation
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app import models, schemas
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dononofre.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Productos
def get_products(db: Session) -> List[models.Product]:
    return db.query(models.Product).order_by(models.Product.id).all()

def get_product(db: Session, product_id: int) -> Optional[models.Product]:
    return db.query(models.Product).filter(models.Product.id == product_id).first()

# Clientes
def get_customer(db: Session, customer_id: int) -> Optional[models.Customer]:
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()

def create_customer_if_not_exists(db: Session, nombre: str, email: Optional[str] = None) -> models.Customer:
    # Si email es provisto, intentamos buscar por email primero
    c = None
    if email:
        c = db.query(models.Customer).filter(models.Customer.email == email).first()
    if c:
        return c

    new = models.Customer(nombre=nombre, email=email)
    db.add(new)
    try:
        db.commit()
        db.refresh(new)
        return new
    except Exception:
        # intento simple contra race condition: si otro proceso creó el mismo email, reconsultar
        db.rollback()
        if email:
            existing = db.query(models.Customer).filter(models.Customer.email == email).first()
            if existing:
                return existing
        # si falla por otro motivo, re-raise
        raise

# Ordenes
def create_order(db: Session, order_data: schemas.OrderCreate) -> models.Order:
    """
    Crea orden + items en una única transacción. Usa Decimal para totales.
    Hace rollback si ocurre cualquier error.
    """
    customer = get_customer(db, order_data.customer_id)
    if not customer:
        raise ValueError("Cliente no encontrado")

    order = models.Order(customer_id=customer.id, status="pending", total=0.0)
    db.add(order)
    try:
        db.flush()  # asigna order.id antes del commit

        total = Decimal("0")
        for item in order_data.items:
            product = get_product(db, item.product_id)
            if not product:
                raise ValueError(f"Producto {item.product_id} no encontrado")

            # Convertir price a Decimal (asumiendo product.precio es almacenado como string/num)
            try:
                price = Decimal(str(product.precio))
            except (InvalidOperation, TypeError):
                raise ValueError(f"Precio inválido para producto {product.id}")

            cantidad = int(item.cantidad)
            line_price = price * cantidad

            oi = models.OrderItem(
                order_id=order.id,
                product_id=product.id,
                cantidad=cantidad,
                price=float(price)  # guarda según modelo; ideal sería Decimal en el modelo/DB
            )
            db.add(oi)
            total += line_price

        # Asignar total a la orden (cast a float si el modelo lo requiere)
        order.total = float(total)
        db.commit()
        db.refresh(order)
        return order

    except Exception:
        db.rollback()
        raise

def get_order(db: Session, order_id: int) -> Optional[models.Order]:
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return None
    # force load relationships
    _ = order.customer
    for it in order.items:
        _ = it.product
    return order

def mark_order_paid(db: Session, order_id: int) -> bool:
    order = get_order(db, order_id)
    if not order:
        return False
    order.status = "paid"
    # si el modelo tiene campo paid_at, actualizarlo:
    if hasattr(order, "paid_at"):
        import datetime
        order.paid_at = datetime.datetime.utcnow()
    db.add(order)
    db.commit()
    return True
