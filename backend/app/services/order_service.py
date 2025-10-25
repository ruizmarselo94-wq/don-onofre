# services/order_service.py
from app.db import crud
from app.core.config import make_doc_id
from app.services import adamspay_service as aps

# Crear orden en DB y deuda en AdamsPay. Devuelve (order_id, pay_url)
def create_order_with_payment(db, order_in):
    order = crud.create_order(db, order_in)  # status "pending"
    doc_id = make_doc_id(order.id)
    pay_url = aps.create_debt(doc_id, order.total, label=f"Pedido #{order.id}")
    return order, pay_url

# Estado “real” de la orden usando AdamsPay (sin polling en backend; llamada on-demand)
def get_order_status(db, order_id: int):
    order = crud.get_order(db, order_id)
    if not order:
        return None
    doc_id = make_doc_id(order.id)
    try:
        d = aps.read_debt(doc_id)
        # map simple para frontend actual
        status = "paid" if (d.get("payStatus") == "paid") else "pending"
        return {"id": order.id, "status": status, "payUrl": d.get("payUrl")}
    except Exception:
        # si falla lectura, devolvemos lo que sabemos de DB
        return {"id": order.id, "status": order.status, "payUrl": None}

# Cancelar: elimina la deuda si existe y marca orden en DB
def cancel_order(db, order_id: int):
    order = crud.get_order(db, order_id)
    if not order:
        return None
    # bloquear si ya entregada (si implementás ese estado luego)
    if getattr(order, "status", "") == "paid":
        # Devolver 400 en API: para refund usen otro endpoint (opcional)
        raise ValueError("Orden pagada: usá refund (no implementado aquí).")
    doc_id = make_doc_id(order.id)
    try:
        aps.delete_debt(doc_id, notify_webhook="true")
    except Exception:
        # si ya no existe en AdamsPay, seguimos igual
        pass
    crud.update_order_status(db, order.id, "cancelled")
    return {"order_id": order.id, "status": "cancelled"}
