import secrets
import hashlib
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import jwt
from passlib.context import CryptContext
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _normalize_password(password: str) -> str:
    """
    Normaliza la contraseña usando SHA-256 antes de bcrypt.
    Esto evita el límite de 72 bytes de bcrypt y permite contraseñas de cualquier longitud.
    """
    print(f"[DEBUG] _normalize_password - Input length: {len(password)} chars, {len(password.encode('utf-8'))} bytes")
    # Hash SHA-256 de la contraseña
    sha_hash = hashlib.sha256(password.encode('utf-8')).digest()
    # Convertir a base64 para tener una representación de texto válida
    normalized = base64.b64encode(sha_hash).decode('ascii')
    print(f"[DEBUG] _normalize_password - Output length: {len(normalized)} chars")
    return normalized

def hash_password(password: str) -> bytes:
    """Hashea una contraseña usando SHA-256 + bcrypt."""
    print(f"[DEBUG] hash_password - Starting with password length: {len(password)}")
    try:
        normalized = _normalize_password(password)
        print(f"[DEBUG] hash_password - Normalized: {normalized[:20]}...")
        hashed = pwd_context.hash(normalized).encode()
        print(f"[DEBUG] hash_password - Success! Hash length: {len(hashed)}")
        return hashed
    except Exception as e:
        print(f"[ERROR] hash_password - Exception: {type(e).__name__}: {e}")
        raise

def verify_password(password: str, password_hash: bytes) -> bool:
    """Verifica una contraseña contra su hash."""
    print(f"[DEBUG] verify_password - Starting")
    try:
        normalized = _normalize_password(password)
        result = pwd_context.verify(normalized, password_hash.decode())
        print(f"[DEBUG] verify_password - Result: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] verify_password - Exception: {type(e).__name__}: {e}")
        raise

def hash_refresh_token(token: str) -> bytes:
    """Hashea un refresh token usando SHA-256 + bcrypt."""
    print(f"[DEBUG] hash_refresh_token - Token length: {len(token)}")
    try:
        normalized = _normalize_password(token)  # Reutilizamos la misma función
        hashed = pwd_context.hash(normalized).encode()
        print(f"[DEBUG] hash_refresh_token - Success! Hash length: {len(hashed)}")
        return hashed
    except Exception as e:
        print(f"[ERROR] hash_refresh_token - Exception: {type(e).__name__}: {e}")
        raise

def verify_refresh_token(token: str, token_hash: bytes) -> bool:
    """Verifica un refresh token contra su hash."""
    print(f"[DEBUG] verify_refresh_token - Starting")
    try:
        normalized = _normalize_password(token)  # Reutilizamos la misma función
        result = pwd_context.verify(normalized, token_hash.decode())
        print(f"[DEBUG] verify_refresh_token - Result: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] verify_refresh_token - Exception: {type(e).__name__}: {e}")
        raise

def create_access_token(subject: str, session_id: str, expires_minutes: int = None) -> str:
    if expires_minutes is None:
        expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "sid": session_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token

def generate_refresh_token() -> str:
    # 256 bits approx
    return secrets.token_urlsafe(48)

def access_expiry_dt() -> datetime:
    """Retorna datetime de expiración del access token (naive para MySQL)."""
    return (datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).replace(tzinfo=None)

def refresh_expiry_dt() -> datetime:
    """Retorna datetime de expiración del refresh token (naive para MySQL)."""
    return (datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).replace(tzinfo=None)
