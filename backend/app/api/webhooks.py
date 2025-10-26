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

@router.post("/webhooks/adams")
async def adams_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload inválido")

    doc_id = payload.get("docId")
    status = payload.get("status")

    if not doc_id:
        raise HTTPException(status_code=400, detail="docId ausente")

    try:
        parts = str(doc_id).split("-")
        # acepta "order-<id>" o "order-<id>-<ts>"
        if len(parts) < 2 or parts[0] != "order" or not parts[1].isdigit():
            raise ValueError("docId inválido")
        order_id = int(parts[1])

        if status == "paid":
            update_order_status(db, order_id, "paid")
        elif status == "refunded":
            update_order_status(db, order_id, "devuelta")
        elif status in ("expired", "deleted", "cancelled"):
            update_order_status(db, order_id, "cancelled")
        # otros estados: ignorar o loguear
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"ok": True}
