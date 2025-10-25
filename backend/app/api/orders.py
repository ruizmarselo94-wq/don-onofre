# api/orders.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.crud import SessionLocal
from app import schemas
from app.services import order_service

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/orders")
def create_order(order_in: schemas.OrderCreate, db: Session = Depends(get_db)):
    try:
        order, pay_url = order_service.create_order_with_payment(db, order_in)
        return {"order_id": order.id, "payment_url": pay_url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="No se pudo crear la orden")

@router.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    data = order_service.get_order_status(db, order_id)
    if not data:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return {"id": data["id"], "status": data["status"]}

@router.delete("/orders/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    try:
        resp = order_service.cancel_order(db, order_id)
        if not resp:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        return resp
    except ValueError as e:
        # ej: intentar cancelar una pagada
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error eliminando deuda")
