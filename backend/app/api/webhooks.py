# api/webhooks.py
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.crud import SessionLocal, update_order_status
# Si implementás logs de eventos: from app.db.crud import save_payment_event

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/webhooks/adams")
async def adams_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload inválido")

    # Ejemplo de payload esperado (coincide con tu código viejo):
    # { "docId": "order-123", "status": "paid", ... }
    doc_id = payload.get("docId")
    status = payload.get("status")  # 'paid', 'pending', 'refunded', etc.

    if not doc_id:
        raise HTTPException(status_code=400, detail="docId ausente")

    # Idempotencia simple: si tenés tabla de eventos, guardá y evita reprocesar duplicados.
    # save_payment_event(db, doc_id, payload)

    # Nunca llamar a AdamsPay desde el webhook. Solo reflejar estado local.
    try:
        # extraer order_id de "order-<id>"
        if not doc_id.startswith("order-"):
            raise ValueError("docId inválido")
        order_id = int(doc_id.split("-", 1)[1])

        # Mapear estados: si status == 'paid' → orden 'paid'; si 'refunded' → 'devuelta', etc.
        if status == "paid":
            update_order_status(db, order_id, "paid")
        elif status == "refunded":
            update_order_status(db, order_id, "devuelta")
        elif status in ("expired", "deleted", "cancelled"):
            update_order_status(db, order_id, "cancelled")
        # Si vienen otros estados, podés ignorarlos o registrarlos.

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"ok": True}
