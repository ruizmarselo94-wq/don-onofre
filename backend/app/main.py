# C:\Proyectos\don-onofre\backend\app\main.py

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pathlib
from sqlalchemy.orm import Session
from app import crud, schemas, adamspay
from app.fake_checkout import router as fake_checkout_router
import logging

# --- Logging básico ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("don-onofre")

app = FastAPI(title="Don Onofre API")

# --- Routers ---
app.include_router(fake_checkout_router)

# --- CORS para frontend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Podés limitar a tu frontend real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# directorio base del proyecto (sube 2 niveles) y frontend en la raíz del repo
BASE_DIR = pathlib.Path(__file__).resolve().parents[2]   # backend/app -> don-onofre
FRONTEND_DIR = BASE_DIR / "frontend"

# montar archivos estáticos en /static (styles.css, app.js, etc.)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# --- Dependencia para DB ---
def get_db():
    db = crud.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Raíz ---
@app.get("/", include_in_schema=False)
def root():
    return FileResponse(FRONTEND_DIR / "index.html")

# --- PRODUCTOS ---
@app.get("/products", response_model=list[schemas.Product])
def list_products(db: Session = Depends(get_db)):
    return crud.get_products(db)

@app.get("/products/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = crud.get_product(db, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return p

# --- ORDENES ---
@app.post("/orders", response_model=dict)
def create_order(order_data: schemas.OrderCreate, db: Session = Depends(get_db)):
    """
    Crea una orden y genera URL de pago AdamsPay.
    Si la creación del payment URL falla, marca la orden como 'error' y hace commit
    para no dejarla en estado indeterminado (evita órdenes huérfanas).
    """
    try:
        order = crud.create_order(db, order_data)
        try:
            payment_url = adamspay.init_payment(order.id, order.total)
        except Exception as e:
            # marcamos orden como error para que quede explícito en la DB
            order.status = "error"
            db.add(order)
            db.commit()
            logger.error("init_payment falló para order %s: %s", order.id, e)
            raise HTTPException(status_code=400, detail=f"Error creando pago: {e}")
        return {"order_id": order.id, "payment_url": payment_url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/orders/{order_id}", response_model=schemas.Order)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    # Si sigue pendiente, intentamos verificar el estado en AdamsPay (fallback)
    if order.status != "paid":
        doc_id = f"order-{order_id}"
        try:
            debt_info = adamspay.get_debt(doc_id)
            if debt_info.get("isPaid"):
                # marcarla como pagada en BD
                crud.mark_order_paid(db, order_id)
                # recargar order si lo necesitas
                order = crud.get_order(db, order_id)
                logger.info("Orden %d actualizada a paid por verificación manual/fallback", order_id)
        except Exception as e:
            # no fallar la petición por un error externo; solo loguear
            logger.warning("No se pudo verificar deuda %s en AdamsPay: %s", doc_id, e)

    return order

@app.post("/orders/{order_id}/pay")
def pay_order(order_id: int, db: Session = Depends(get_db)):
    """
    Marca la orden como pagada solo si AdamsPay confirma pago
    """
    doc_id = f"order-{order_id}"
    try:
        debt = adamspay.get_debt(doc_id)
        if not debt["isPaid"]:
            raise HTTPException(status_code=400, detail="Orden no pagada aún")
        success = crud.mark_order_paid(db, order_id)
        if not success:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        return {"status": "paid"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# --- BORRAR DEUDA ---
@app.delete("/orders/{order_id}", response_model=dict)
def delete_order(order_id: int):
    """
    Elimina la deuda asociada a una orden en AdamsPay.
    """
    doc_id = f"order-{order_id}"
    try:
        deleted = adamspay.delete_debt(doc_id)
        return {"status": "deleted", "debt": deleted}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- WEBHOOK ADAMSPAY ---
@app.post("/adamspay/webhook")
async def adamspay_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Recibe notificaciones de AdamsPay sobre pagos.
    Payload esperado:
      {
        "docId": "order-{order_id}",
        "status": "paid"
      }
    """
    try:
        payload = await request.json()
        logger.info("Webhook recibido: %s", payload)

        if not adamspay.handle_webhook(payload):
            return {"status": "ignored"}

        doc_id = payload.get("docId", "")
        if not doc_id.startswith("order-"):
            return {"status": "invalid_docId"}

        order_id = int(doc_id.split("-")[1])
        crud.mark_order_paid(db, order_id)
        logger.info("Orden marcada como pagada: %d", order_id)
        return {"status": "ok"}

    except Exception as e:
        logger.error("Error procesando webhook: %s", e)
        return {"status": "error", "detail": str(e)}
