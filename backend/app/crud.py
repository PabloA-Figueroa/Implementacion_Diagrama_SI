from sqlalchemy.orm import Session
from sqlalchemy import select, func, update
from datetime import datetime, timezone, timedelta
from . import models
from .security import hash_password, verify_password, hash_refresh_token, verify_refresh_token
from .security import create_access_token, generate_refresh_token, access_expiry_dt, refresh_expiry_dt
from typing import Optional, Tuple
from sqlalchemy.exc import NoResultFound

def _utcnow() -> datetime:
    """
    Retorna datetime actual en UTC sin timezone (naive).
    MySQL guarda datetime sin timezone, así que usamos naive para evitar errores de comparación.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)

def create_cliente(db: Session, *, nombre: str, identificador: str | None = None, estado: str = "activo") -> models.Cliente:
    """Crea un cliente y devuelve la instancia.

    Esto es útil para crear el registro padre antes de crear usuarios que referencien a él.
    """
    now = _utcnow()
    cliente = models.Cliente(
        nombre=nombre,
        identificador=identificador,
        estado=estado,
        created_at=now,
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente

def get_user_by_email(db: Session, email: str) -> Optional[models.Usuario]:
    return db.execute(select(models.Usuario).where(models.Usuario.email == email)).scalar_one_or_none()

def register_user_with_auto_client(db: Session, *, nombres: str, apellidos: str, email: str, telefono: str | None, password: str) -> models.Usuario:
    """
    Registra un nuevo usuario creando automáticamente un cliente asociado.
    El cliente se crea con el nombre completo del usuario.
    """
    print(f"[DEBUG] register_user_with_auto_client - Starting for email: {email}")

    # Crear cliente automáticamente con el nombre del usuario
    nombre_completo = f"{nombres} {apellidos}"
    cliente = create_cliente(
        db,
        nombre=nombre_completo,
        identificador=email.split('@')[0],  # Usar parte del email como identificador
        estado="activo"
    )
    print(f"[DEBUG] register_user_with_auto_client - Cliente auto-creado con ID: {cliente.id}")

    # Crear usuario asociado al cliente
    user = create_user(
        db,
        cliente_id=cliente.id,
        nombres=nombres,
        apellidos=apellidos,
        email=email,
        telefono=telefono,
        password=password
    )

    print(f"[DEBUG] register_user_with_auto_client - Usuario registrado con ID: {user.id}")
    return user

def create_user(db: Session, *, cliente_id: int, nombres: str, apellidos: str, email: str, telefono: str | None, password: str) -> models.Usuario:
    print(f"[DEBUG] crud.create_user - Starting for email: {email}")
    print(f"[DEBUG] crud.create_user - Password length: {len(password)} chars")

    # Verificar que el cliente exista antes de intentar insertar el usuario.
    cliente = db.get(models.Cliente, cliente_id)
    if cliente is None:
        print(f"[ERROR] crud.create_user - Cliente {cliente_id} not found")
        raise ValueError(f"Cliente con id={cliente_id} no existe. Debe crearlo antes de crear usuarios asociados.")

    print(f"[DEBUG] crud.create_user - Cliente found: {cliente.nombre}")

    user = models.Usuario(
        cliente_id=cliente_id,
        nombres=nombres,
        apellidos=apellidos,
        email=email,
        telefono=telefono,
        estado="activo",
        email_verificado=False,
        telefono_verificado=False,
        created_at=_utcnow(),
    )
    db.add(user)
    db.flush()  # get user.id
    print(f"[DEBUG] crud.create_user - User created with ID: {user.id}")

    print(f"[DEBUG] crud.create_user - About to hash password")
    try:
        password_hash = hash_password(password)
        print(f"[DEBUG] crud.create_user - Password hashed successfully, length: {len(password_hash)}")
    except Exception as e:
        print(f"[ERROR] crud.create_user - Failed to hash password: {type(e).__name__}: {e}")
        raise

    cred = models.UsuarioCredencial(
        usuario_id=user.id,
        password_hash=password_hash,
        password_updated_at=_utcnow(),
    )
    db.add(cred)
    print(f"[DEBUG] crud.create_user - Credential created, about to commit")
    db.commit()
    db.refresh(user)
    print(f"[DEBUG] crud.create_user - User creation completed successfully")
    return user

def register_access_log(db: Session, *, usuario_id: int | None, email_intentado: str | None, exito: bool, ip: str | None, detalle: str | None):
    db.add(models.AccesoLog(
        usuario_id=usuario_id,
        email_intentado=email_intentado,
        momento=_utcnow(),
        exito=exito,
        ip=ip,
        detalle=detalle
    ))
    db.commit()

def ensure_bloqueo_row(db: Session, usuario_id: int):
    row = db.get(models.UsuarioBloqueo, usuario_id)
    if not row:
        row = models.UsuarioBloqueo(
            usuario_id=usuario_id,
            intentos_fallidos=0,
            bloqueado_hasta=None,
            ultimo_intento=None,
            updated_at=_utcnow(),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row

def check_blocked(db: Session, usuario_id: int) -> bool:
    row = ensure_bloqueo_row(db, usuario_id)
    now = _utcnow()
    if row.bloqueado_hasta and row.bloqueado_hasta > now:
        return True
    return False

def register_failed_attempt(db: Session, usuario_id: int, max_intentos: int = 4, ventana_min: int = 15):
    row = ensure_bloqueo_row(db, usuario_id)
    now = _utcnow()
    row.intentos_fallidos += 1
    row.ultimo_intento = now
    if row.intentos_fallidos >= max_intentos:
        row.bloqueado_hasta = now.replace(microsecond=0) + timedelta(minutes=ventana_min)
        db.add(models.BloqueoEvento(
            usuario_id=usuario_id,
            tipo="bloqueo",
            motivo=f"{max_intentos} intentos fallidos",
            efectuado_por=None,
            momento=now
        ))
    db.add(row)
    db.commit()

def reset_failed_attempts(db: Session, usuario_id: int):
    row = ensure_bloqueo_row(db, usuario_id)
    row.intentos_fallidos = 0
    row.bloqueado_hasta = None
    db.add(models.BloqueoEvento(
        usuario_id=usuario_id,
        tipo="desbloqueo",
        motivo="login exitoso",
        efectuado_por=None,
        momento=_utcnow()
    ))
    db.add(row)
    db.commit()

def create_session(db: Session, usuario_id: int, ip: str | None, user_agent: str | None) -> models.Sesion:
    # cerrar cualquier sesión activa del usuario si deseas forzar solo una
    # (ya tenemos constraint en MySQL; aquí hacemos best-effort)
    active = db.execute(
        select(models.Sesion).where(models.Sesion.usuario_id==usuario_id, models.Sesion.cierre==None, models.Sesion.revocada==False)
    ).scalars().all()
    for s in active:
        s.revocada = True
        s.cierre = _utcnow()
        db.add(s)
    db.commit()

    # ULID-like simple 26 chars (no paquete): timestamp + random
    now = _utcnow()
    sid = now.strftime("%Y%m%d%H%M%S%f")[:18]  # 18 chars
    import secrets, base64
    sid += base64.urlsafe_b64encode(secrets.token_bytes(6)).decode()[:8]  # total ~26

    ses = models.Sesion(
        id=sid,
        usuario_id=usuario_id,
        inicio=now,
        ultimo_mov=now,
        cierre=None,
        ip=ip,
        user_agent=user_agent,
        revocada=False,
        expira_en=now + timedelta(hours=8),  # absolute session lifetime (ajustable)
    )
    db.add(ses)
    db.commit()
    db.refresh(ses)
    return ses

from datetime import timedelta

def issue_tokens_for_session(db: Session, sesion: models.Sesion) -> tuple[str, str]:
    access = create_access_token(subject=str(sesion.usuario_id), session_id=sesion.id)
    refresh_plain = generate_refresh_token()
    sesion.refresh_hash = hash_refresh_token(refresh_plain)
    sesion.refresh_expira_en = refresh_expiry_dt()
    sesion.rotation_counter = (sesion.rotation_counter or 0) + 1
    db.add(sesion)
    db.commit()
    return access, refresh_plain

def rotate_refresh(db: Session, sesion: models.Sesion, provided_refresh: str) -> tuple[str, str]:
    # verifica actual
    if not sesion.refresh_hash or not sesion.refresh_expira_en:
        raise ValueError("No refresh en sesión")
    now = _utcnow()
    if now > sesion.refresh_expira_en or sesion.revocada or sesion.cierre is not None:
        raise ValueError("Refresh expirado o sesión revocada")
    if not verify_refresh_token(provided_refresh, sesion.refresh_hash):
        raise ValueError("Refresh inválido")

    # rotar y registrar historial
    db.add(models.RefreshHistorial(
        sesion_id=sesion.id,
        prev_hash=sesion.refresh_hash,
        rotado_en=now,
    ))

    new_access = create_access_token(subject=str(sesion.usuario_id), session_id=sesion.id)
    new_refresh = generate_refresh_token()
    sesion.refresh_hash = hash_refresh_token(new_refresh)
    sesion.refresh_expira_en = refresh_expiry_dt()
    sesion.rotation_counter = (sesion.rotation_counter or 0) + 1
    sesion.ultimo_mov = now
    db.add(sesion)
    db.commit()
    return new_access, new_refresh

def revoke_session(db: Session, sesion: models.Sesion):
    sesion.revocada = True
    sesion.cierre = _utcnow()
    sesion.refresh_hash = None
    sesion.refresh_expira_en = None
    db.add(sesion)
    db.commit()
