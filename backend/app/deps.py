from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from .database import get_db
from .config import settings
from . import models
import jwt
from datetime import datetime, timezone

def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.Usuario:
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    uid = payload.get("sub")
    sid = payload.get("sid")
    if not uid or not sid:
        raise HTTPException(status_code=401, detail="Invalid claims")

    # verificar sesión viva
    ses = db.get(models.Sesion, sid)
    # MySQL guarda datetime sin timezone, así que comparamos con datetime naive
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    if not ses or ses.revocada or ses.cierre is not None or now_utc > ses.expira_en:
        raise HTTPException(status_code=401, detail="Session not active")

    user = db.get(models.Usuario, int(uid))
    if not user or user.estado != "activo":
        raise HTTPException(status_code=401, detail="User inactive")

    # touch último movimiento
    ses.ultimo_mov = now_utc
    db.add(ses)
    db.commit()

    return user
