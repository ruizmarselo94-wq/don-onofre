# don-onofre - Backend (Desafío AdamsPay)

## Descripción
API REST para tienda online de Don Onofre. Permite listar productos, crear órdenes y generar enlaces de pago usando AdamsPay (sandbox). La DB SQLite (`dononofre.db`) incluye productos gastronómicos y clientes de ejemplo.

## Tecnologías
- Python 3.11+
- FastAPI
- SQLAlchemy
- Alembic
- SQLite
- Uvicorn / Gunicorn
- AdamsPay sandbox

## Requisitos
- Python 3.11+
- pip
- (Opcional) Docker

## Instalación y ejecución
1. Clonar repositorio:
git clone <TU_REPO> don-onofre
cd don-onofre/backend

2. Activar virtualenv:
python -m venv venv
.\venv\Scripts\Activate.ps1

3. Instalar dependencias:
pip install -r requirements.txt

4. Crear `.env` con:
DATABASE_URL=sqlite:///./dononofre.db
ADAMSPAY_BASE_URL=https://sandbox.adamspay.com
ADAMSPAY_API_KEY=TU_API_KEY_DE_PRUEBA
SECRET_KEY=clave_secreta_local
PORT=8000

5. Inicializar DB (crea `dononofre.db` con seed):
python -m app.init_db

6. Ejecutar servidor:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

7. Documentación API: http://127.0.0.1:8000/docs

## Endpoints principales
- GET /api/products — Listar productos  
- GET /api/products/{id} — Detalle producto  
- POST /api/orders — Crear orden (items + cliente)  
- GET /api/orders/{id} — Estado de orden y pago  
- POST /api/payments/create — Crear link de pago  
- POST /api/payments/webhook — Notificaciones de AdamsPay  

## Entrega
Enviar e-mail a jobs@adamspay.com con asunto `Desafío IT` incluyendo:
- Tu nombre y apellido
- Nombre de tu comercio en AdamsPay
- Link al código fuente (GitHub/GitLab o ZIP)
- Link donde se vea funcionando (Heroku, Cloud Run, servidor propio o ngrok temporal)

## Consejos rápidos
- Para pruebas de webhook local: ngrok http 8000  
- Verifica que `dononofre.db` exista y tenga permisos  
- Revisa ADAMSPAY_BASE_URL y ADAMSPAY_API_KEY antes de probar pagos
