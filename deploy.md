# Despliegue backend Don Onofre (SQLite)

## Variables de entorno
Crea un archivo `.env` en `backend/` con estas variables:

DATABASE_URL=sqlite:///./dononofre.db
ADAMSPAY_BASE_URL=https://sandbox.adamspay.com
ADAMSPAY_API_KEY=TU_API_KEY_DE_PRUEBA
SECRET_KEY=clave_secreta_local
PORT=8000

## 1) Levantar local (desarrollo)
1. Activar virtualenv:
.\venv\Scripts\Activate.ps1

2. Instalar dependencias:
pip install -r requirements.txt

3. Inicializar y seedear DB:
python -m app.init_db

   Esto crea o resetea `dononofre.db` con productos y clientes de ejemplo.

4. Levantar servidor:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

5. Documentación automática:
OpenAPI: http://127.0.0.1:8000/docs

## 2) Pruebas AdamsPay
- Usa sandbox de AdamsPay con ADAMSPAY_API_KEY.
- Webhook de pagos: /api/payments/webhook
- Crea órdenes y verifica que se genere el link de pago.
- Usa ngrok si pruebas desde local para exponer la URL.

## 3) Notas
- SQLite es suficiente para desarrollo y prueba.
- Para producción con alta concurrencia, considerar Postgres u otra DB.
- Logs se ven en consola (uvicorn) o en contenedor Docker si se usa.
