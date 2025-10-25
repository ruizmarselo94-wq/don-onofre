from typing import List, Optional
from decimal import Decimal, InvalidOperation
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.db import models
from app import schemas

# ------------------------------------------------------------
# Conexión a DB
# ------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dononofre.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ------------------------------------------------------------
# Productos
# ------------------------------------------------------------
def get_products(db: Session) -> List[models.Product]:
    return db.query(models.Product).order_by(models.Product.id).all()


def get_product(db: Session, product_id: int) -> Optional[models.Product]:
    return db.query(models.Product).filter(models.Product.id == product_id).first()


# ------------------------------------------------------------
# Clientes
# ------------------------------------------------------------
def get_customer(db: Session, customer_id: int) -> Optional[models.Customer]:
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()


def create_customer_if_not_exists(db: Session, nombre: str, email: Optional[str] = None) -> models.Customer:
    """
    Crea un cliente si no existe. Si se provee email, intenta buscar por email primero.
    Maneja carrera simple: si otro proceso crea el mismo email, reconsulta.
    """
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
        db.rollback()
        if email:
            existing = db.query(models.Customer).filter(models.Customer.email == email).first()
            if existing:
                return existing
        raise


# ------------------------------------------------------------
# Órdenes
# ------------------------------------------------------------
def create_order(db: Session, order_data: schemas.OrderCreate) -> models.Order:
    """
    Crea orden + items en una única transacción.
    Calcula total usando Decimal y guarda el precio unitario del producto en el momento de la compra.
    """
    customer = get_customer(db, order_data.customer_id)
    if not customer:
        raise ValueError("Cliente no encontrado")

    order = models.Order(customer_id=customer.id, status="pending", total=0.0)
    db.add(order)

    try:
        db.flush()  # obtener order.id antes del commit

        total = Decimal("0")
        for item in order_data.items:
            product = get_product(db, item.product_id)
            if not product:
                raise ValueError(f"Producto {item.product_id} no encontrado")

            try:
                price = Decimal(str(product.precio))
            except (InvalidOperation, TypeError):
                raise ValueError(f"Precio inválido para producto {product.id}")

            cantidad = int(item.cantidad)
            if cantidad <= 0:
                raise ValueError(f"Cantidad inválida para producto {product.id}")

            line_price = price * cantidad

            oi = models.OrderItem(
                order_id=order.id,
                product_id=product.id,
                cantidad=cantidad,
                price=float(price)  # el modelo usa Float
            )
            db.add(oi)
            total += line_price

        order.total = float(total)
        db.commit()
        db.refresh(order)
        # precargar relaciones
        _ = order.customer
        for it in order.items:
            _ = it.product
        return order

    except Exception:
        db.rollback()
        raise


def get_order(db: Session, order_id: int) -> Optional[models.Order]:
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return None
    _ = order.customer
    for it in order.items:
        _ = it.product
    return order


def mark_order_paid(db: Session, order_id: int) -> bool:
    """
    Compatibilidad con código existente.
    """
    order = get_order(db, order_id)
    if not order:
        return False
    order.status = "paid"
    if hasattr(order, "paid_at"):
        import datetime as _dt
        order.paid_at = _dt.datetime.utcnow()
    db.add(order)
    db.commit()
    return True


def update_order_status(db: Session, order_id: int, new_status: str) -> bool:
    """
    Actualiza el estado de la orden.
    Estados esperados: pending | paid | cancelled | devuelta | entregada
    """
    order = get_order(db, order_id)
    if not order:
        return False
    order.status = new_status
    db.add(order)
    db.commit()
    return True
