# backend/app/fake_checkout.py
from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.crud import SessionLocal  # <- aquí usamos tu SessionLocal real
from app.models import Order

router = APIRouter()

def mark_order_paid(db: Session, order_id: int):
    """Marca la orden como pagada en la DB"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = "paid"
        db.commit()
        db.refresh(order)
    return order

@router.get("/fake_checkout", response_class=HTMLResponse)
def fake_checkout(order_id: int, amount: float):
    """Simulador interno de pago"""
    html = f"""
    <html>
      <head><title>Simulador de pago Don Onofre</title></head>
      <body style="font-family:sans-serif; padding:30px;">
        <h1>Simulador de pago</h1>
        <p><strong>Orden ID:</strong> {order_id}</p>
        <p><strong>Total:</strong> {amount}</p>
        <form action="/fake_pay" method="post">
          <input type="hidden" name="order_id" value="{order_id}" />
          <button type="submit" style="padding:10px 20px; font-size:16px;">Simular pago exitoso</button>
        </form>
      </body>
    </html>
    """
    return HTMLResponse(content=html)

@router.post("/fake_pay")
def fake_pay(order_id: int = Form(...)):
    """Marca la orden como pagada y redirige al home"""
    db = SessionLocal()  # <- reutilizamos SessionLocal de app.crud
    try:
        mark_order_paid(db, order_id)
    finally:
        db.close()
    return RedirectResponse(url="/", status_code=303)
