# don-onofre - Backend (Desafío AdamsPay)

## Descripción
API REST para tienda online de Don Onofre. Permite listar productos, crear órdenes y generar enlaces de pago usando AdamsPay (sandbox). La base de datos SQLite (`dononofre.db`) incluye productos gastronómicos y clientes de ejemplo.

Actualmente desplegado en Railway usando SQLite.

## Tecnologías
- Python 3.11.8
- FastAPI
- SQLAlchemy
- Alembic
- SQLite
- Uvicorn
- AdamsPay sandbox

## Requisitos
- Python 3.11+
- pip

## Instalación y ejecución
git clone https://github.com/ruizmarselo94-wq/don-onofre don-onofre
cd don-onofre/backend

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Documentación API: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Endpoints principales
- GET /api/products
- GET /api/products/{id}
- POST /api/orders
- GET /api/orders/{id}
- POST /api/payments/create
