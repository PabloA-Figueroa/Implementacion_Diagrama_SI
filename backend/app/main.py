from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine, get_db
from . import models, schemas, crud
from .deps import get_current_user
from .security import verify_password
from typing import List

app = FastAPI(title="Auth API (FastAPI + MySQL)")

# CORS para pruebas (ajusta dominios en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear tablas si no existen (si no usas el SQL directamente)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/init")
def initialize_default_data(db: Session = Depends(get_db)):
    """Crea un cliente por defecto si no existe ninguno."""
    from sqlalchemy import select
    existing = db.execute(select(models.Cliente)).first()
    if existing:
        return {"message": "Ya existen clientes en la base de datos", "cliente_id": existing[0].id}

    cliente = crud.create_cliente(
        db,
        nombre="Cliente por defecto",
        identificador="default-client"
    )
    return {"message": "Cliente por defecto creado", "cliente_id": cliente.id}

# --------- Clientes ---------

@app.post("/clientes", response_model=schemas.ClienteOut)
def create_cliente(body: schemas.ClienteCreate, db: Session = Depends(get_db)):
    c = crud.create_cliente(db, nombre=body.nombre, identificador=body.identificador, estado="activo")
    return c

@app.get("/clientes", response_model=List[schemas.ClienteOut])
def list_clientes(db: Session = Depends(get_db)):
    from sqlalchemy import select
    clientes = db.execute(select(models.Cliente)).scalars().all()
    return clientes

# --------- Auth ---------

@app.post("/auth/register", response_model=schemas.UsuarioOut)
def register(body: schemas.UsuarioCreate, request: Request, db: Session = Depends(get_db)):
    print(f"[DEBUG] /auth/register - Starting registration for email: {body.email}")
    print(f"[DEBUG] /auth/register - Password length: {len(body.password)} chars")

    if crud.get_user_by_email(db, body.email):
        print(f"[DEBUG] /auth/register - Email already registered")
        raise HTTPException(status_code=400, detail="Email ya registrado")

    print(f"[DEBUG] /auth/register - Calling register_user_with_auto_client")
    try:
        # Crear usuario con cliente automático
        user = crud.register_user_with_auto_client(
            db,
            nombres=body.nombres,
            apellidos=body.apellidos,
            email=body.email,
            telefono=body.telefono,
            password=body.password
        )
        print(f"[DEBUG] /auth/register - User created successfully with ID: {user.id}")
    except ValueError as e:
        print(f"[ERROR] /auth/register - ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[ERROR] /auth/register - Unexpected Exception: {type(e).__name__}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    crud.register_access_log(db, usuario_id=user.id, email_intentado=user.email, exito=True, ip=request.client.host if request.client else None, detalle="registro")
    print(f"[DEBUG] /auth/register - Registration completed successfully")
    return user

@app.post("/auth/login", response_model=schemas.TokenPair)
def login(body: schemas.LoginIn, request: Request, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, body.email)
    if not user:
        crud.register_access_log(db, usuario_id=None, email_intentado=body.email, exito=False, ip=request.client.host if request.client else None, detalle="email no existe")
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    if user.estado != "activo":
        raise HTTPException(status_code=401, detail=f"Usuario {user.estado}")

    # bloqueo?
    if crud.check_blocked(db, user.id):
        raise HTTPException(status_code=423, detail="Usuario bloqueado temporalmente")

    cred = user.credencial
    if not cred or not verify_password(body.password, cred.password_hash):
        crud.register_failed_attempt(db, user.id)
        crud.register_access_log(db, usuario_id=user.id, email_intentado=user.email, exito=False, ip=request.client.host if request.client else None, detalle="password inválido")
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # éxito
    crud.reset_failed_attempts(db, user.id)
    ses = crud.create_session(db, user.id, ip=request.client.host if request.client else None, user_agent=request.headers.get("user-agent"))
    access, refresh = crud.issue_tokens_for_session(db, ses)
    crud.register_access_log(db, usuario_id=user.id, email_intentado=user.email, exito=True, ip=request.client.host if request.client else None, detalle="login ok")
    return {"access_token": access, "refresh_token": refresh, "session_id": ses.id, "token_type": "bearer"}

@app.post("/auth/refresh", response_model=schemas.TokenPair)
def refresh_tokens(body: schemas.RefreshIn, request: Request, db: Session = Depends(get_db)):
    ses = db.get(models.Sesion, body.session_id)
    if not ses:
        raise HTTPException(status_code=401, detail="Sesión no encontrada")
    try:
        access, new_refresh = crud.rotate_refresh(db, ses, body.refresh_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    return {"access_token": access, "refresh_token": new_refresh, "session_id": ses.id, "token_type": "bearer"}

@app.post("/auth/logout")
def logout(body: schemas.RefreshIn, db: Session = Depends(get_db)):
    ses = db.get(models.Sesion, body.session_id)
    if not ses:
        raise HTTPException(status_code=200, detail="ok")  # idempotente
    crud.revoke_session(db, ses)
    return {"ok": True}

# --------- Perfil ---------

@app.get("/me", response_model=schemas.UsuarioOut)
def me(current_user: models.Usuario = Depends(get_current_user)):
    return current_user
