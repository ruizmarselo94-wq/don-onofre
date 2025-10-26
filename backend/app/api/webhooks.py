# api/webhooks.py
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse
from app.db.crud import SessionLocal, update_order_status
import asyncio, json
from typing import Dict, Set

router = APIRouter()
_subs: Dict[int, Set[asyncio.Queue[str]]] = {}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _extract_doc_and_status(payload: dict):
    debt = payload.get("debt") or {}
    doc_id = payload.get("docId") or debt.get("docId")
    pay_status = (debt.get("payStatus") or {}).get("status")
    obj_status = (debt.get("objStatus") or {}).get("status")
    top_status = payload.get("status") or debt.get("status")
    status = pay_status or top_status
    return doc_id, status, obj_status

async def _broadcast(order_id: int, status: str):
    qs = _subs.get(order_id)
    if not qs: return
    msg = f"data: {json.dumps({'order_id': order_id, 'status': status})}\n\n"
    for q in list(qs):
        try:
            await asyncio.wait_for(q.put(msg), timeout=0.1)
        except Exception:
            qs.discard(q)

@router.get("/events/orders/{order_id}")
async def events(order_id: int):
    q: asyncio.Queue[str] = asyncio.Queue()
    _subs.setdefault(order_id, set()).add(q)

    async def gen():
        try:
            yield "event: ping\ndata: ok\n\n"
            while True:
                try:
                    yield await asyncio.wait_for(q.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield "event: ping\ndata: ok\n\n"
        finally:
            _subs.get(order_id, set()).discard(q)

    return StreamingResponse(gen(), media_type="text/event-stream")

@router.post("/webhooks/adams")
async def adams_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload inválido")

    doc_id, status, obj_status = _extract_doc_and_status(payload)
    if not doc_id:
        raise HTTPException(status_code=400, detail="docId ausente")

    parts = str(doc_id).split("-")
    if len(parts) < 2 or parts[0] != "order" or not parts[1].isdigit():
        raise HTTPException(status_code=400, detail="docId inválido")
    order_id = int(parts[1])

    normalized = None
    if status == "paid":
        normalized = "paid"
    elif status == "refunded":
        normalized = "devuelta"
    elif (obj_status or "") in ("expired", "deleted", "cancelled"):
        normalized = "cancelled"

    if normalized:
        try:
            update_order_status(db, order_id, normalized)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        asyncio.create_task(_broadcast(order_id, normalized))

    return {"ok": True}
