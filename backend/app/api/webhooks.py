# api/webhooks.py
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.crud import SessionLocal, update_order_status

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _extract_doc_and_status(payload: dict):
    """
    Soporta formatos comunes de AdamsPay:
      A) { "docId": "...", "status": "paid" }
      B) { "debt": { "docId": "...", "status": "...", "payStatus": {"status": "paid"}, "objStatus": {"status": "..."} } }
      (El estado de pago fiable suele venir en debt.payStatus.status)
    """
    debt = payload.get("debt") or {}
    doc_id = payload.get("docId") or debt.get("docId")

    # Candidatos de estado (preferimos payStatus.status si existe)
    pay_status = (debt.get("payStatus") or {}).get("status")
    obj_status = (debt.get("objStatus") or {}).get("status")
    top_status = payload.get("status") or debt.get("status")

    # Regla: si hay payStatus, usamos ese; si no, usamos top_status
    status = pay_status or top_status

    return doc_id, status, obj_status

@router.post("/webhooks/adams")
async def adams_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload inválido")

    doc_id, status, obj_status = _extract_doc_and_status(payload)
    if not doc_id:
        raise HTTPException(status_code=400, detail="docId ausente")

    # Aceptamos docId "order-<id>" y "order-<id>-<ts>"
    parts = str(doc_id).split("-")
    if len(parts) < 2 or parts[0] != "order" or not parts[1].isdigit():
        raise HTTPException(status_code=400, detail="docId inválido")

    order_id = int(parts[1])

    # Mapeo de estados
    # - "paid" → paid
    # - obj_status en {expired, deleted, cancelled} → cancelled
    # - "refunded" (si llega) → devuelta
    try:
        normalized = None
        if status == "paid":
            normalized = "paid"
        elif status == "refunded":
            normalized = "devuelta"
        elif (obj_status or "") in ("expired", "deleted", "cancelled"):
            normalized = "cancelled"

        if normalized:
            update_order_status(db, order_id, normalized)
        # Si llega un estado desconocido, devolvemos 200 igualmente (idempotente y no rompemos reintentos).
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"ok": True}
