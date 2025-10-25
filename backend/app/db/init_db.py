from app.db.crud import SessionLocal, engine
from app.db import models

def seed():
    # Crear tablas si no existen
    models.Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Limpiar tablas para empezar desde cero
        db.query(models.OrderItem).delete()
        db.query(models.Order).delete()
        db.query(models.Product).delete()
        db.query(models.Customer).delete()
        db.commit()

        # Insertar productos gastronómicos (cursos y talleres)
        db.add_all([
            models.Product(
                nombre="Panadería Básica",
                precio=120000.0,
                descripcion="Aprendé a hacer panes caseros, masas madre y técnicas básicas de fermentación.",
                tipo="curso"
            ),
            models.Product(
                nombre="Pastelería Creativa",
                precio=150000.0,
                descripcion="Diseñá y elaborá postres innovadores, desde cupcakes hasta tartas decorativas.",
                tipo="taller"
            ),
            models.Product(
                nombre="Cocina Internacional",
                precio=100000.0,
                descripcion="Recorré recetas clásicas y modernas de la gastronomía mundial.",
                tipo="digital"
            ),
            models.Product(
                nombre="Cocina Vegetariana",
                precio=90000.0,
                descripcion="Aprendé recetas completas y nutritivas sin carne.",
                tipo="taller"
            ),
            models.Product(
                nombre="Técnicas de Repostería",
                precio=130000.0,
                descripcion="Dominá las técnicas avanzadas de repostería profesional.",
                tipo="curso"
            ),
            models.Product(
                nombre="Cocina Rápida Saludable",
                precio=60000.0,
                descripcion="Recetas fáciles y nutritivas para el día a día.",
                tipo="digital"
            ),
        ])

        # Insertar clientes de ejemplo
        db.add_all([
            models.Customer(nombre="Juan Perez", email="juan@example.com"),
            models.Customer(nombre="Ana Gomez", email="ana@example.com"),
        ])

        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
    print("DB seeded")
