# app/services/order_service.py
import math, time
from app.db import crud
from app.services import adamspay_service as aps

def _make_unique_doc_id(order) -> str:
    # Estable, reproducible y único incluso si reinicia el autoincremental:
    # order-<id>-<epoch_s_de_created_at>
    ts = int(order.created_at.timestamp()) if hasattr(order, "created_at") else int(time.time())
    return f"order-{order.id}-{ts}"

def create_order_with_payment(db, order_in):
    order = crud.create_order(db, order_in)  # status "pending"
    doc_id = _make_unique_doc_id(order)
    pay_url = aps.create_debt(doc_id, order.total, label=f"Pedido #{order.id}")
    crud.set_order_payment_info(db, order.id, doc_id, pay_url)
    return order, pay_url

def get_order_status(db, order_id: int):
    order = crud.get_order(db, order_id)
    if not order:
        return None
    doc_id = order.adams_doc_id or _make_unique_doc_id(order)  # fallback por compatibilidad
    try:
        d = aps.read_debt(doc_id)
        status = "paid" if (d.get("payStatus") == "paid") else "pending"
        return {"id": order.id, "status": status, "payUrl": d.get("payUrl")}
    except Exception:
        return {"id": order.id, "status": order.status, "payUrl": order.adams_pay_url}

def cancel_order(db, order_id: int):
    order = crud.get_order(db, order_id)
    if not order:
        return None
    if getattr(order, "status", "") == "paid":
        raise ValueError("Orden pagada: usá refund (no implementado aquí).")
    doc_id = order.adams_doc_id or _make_unique_doc_id(order)
    try:
        aps.delete_debt(doc_id, notify_webhook="true")
    except Exception:
        pass
    crud.update_order_status(db, order.id, "cancelled")
    return {"order_id": order.id, "status": "cancelled"}
