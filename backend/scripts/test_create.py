from app import crud
from app.database import SessionLocal


def main():
    db = SessionLocal()
    try:
        cliente = crud.create_cliente(db, nombre="Cliente de prueba", identificador="test-1")
        print("Cliente creado:", cliente.id, cliente.nombre)

        user = crud.create_user(
            db,
            cliente_id=cliente.id,
            nombres="asdasd",
            apellidos="asdasd",
            email="sdasdasd+test@gmail.com",
            telefono="123123123",
            password="secret123",
        )
        print("Usuario creado:", user.id, user.email)
    finally:
        db.close()


if __name__ == '__main__':
    main()

