from sqlalchemy import (
    Column, Integer, BigInteger, String, Enum, DateTime, TIMESTAMP, Boolean,
    ForeignKey, LargeBinary, UniqueConstraint, Computed
)
from sqlalchemy.orm import relationship
from .database import Base

# Enums como strings
UserEstado = ("pendiente","activo","suspendido","bloqueado","inactivo")
ClienteEstado = ("activo","inactivo")
VerifTipo = ("email","telefono")
MFAMetodo = ("email_code","sms_code","security_question","security_key","totp")
OTPMedio = ("email_code","sms_code","totp")
BloqueoTipo = ("bloqueo","desbloqueo","autodesbloqueo")

class Cliente(Base):
    __tablename__ = "cliente"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre = Column(String(150), nullable=False)
    identificador = Column(String(50))
    estado = Column(Enum(*ClienteEstado), default="activo", nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)

    usuarios = relationship("Usuario", back_populates="cliente")

class Usuario(Base):
    __tablename__ = "usuario"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("cliente.id"), nullable=False)
    nombres = Column(String(120), nullable=False)
    apellidos = Column(String(120), nullable=False)
    email = Column(String(160), nullable=False, unique=True, index=True)
    telefono = Column(String(30))
    estado = Column(Enum(*UserEstado), nullable=False, default="pendiente")
    email_verificado = Column(Boolean, nullable=False, default=False)
    telefono_verificado = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP, nullable=False)

    cliente = relationship("Cliente", back_populates="usuarios")
    credencial = relationship("UsuarioCredencial", uselist=False, back_populates="usuario")
    sesiones = relationship("Sesion", back_populates="usuario")

class UsuarioCredencial(Base):
    __tablename__ = "usuario_credencial"
    usuario_id = Column(BigInteger, ForeignKey("usuario.id"), primary_key=True)
    password_hash = Column(LargeBinary(255), nullable=False)
    password_updated_at = Column(TIMESTAMP, nullable=False)

    usuario = relationship("Usuario", back_populates="credencial")

class VerificacionContacto(Base):
    __tablename__ = "verificacion_contacto"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    usuario_id = Column(BigInteger, ForeignKey("usuario.id"), nullable=False)
    tipo = Column(Enum(*VerifTipo), nullable=False)
    token = Column(String(64), nullable=False)
    expira_en = Column(DateTime, nullable=False)
    verificado_en = Column(DateTime, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)

class UsuarioMFA(Base):
    __tablename__ = "usuario_mfa"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    usuario_id = Column(BigInteger, ForeignKey("usuario.id"), nullable=False)
    metodo = Column(Enum(*MFAMetodo), nullable=False)
    secreto = Column(LargeBinary(512), nullable=True)
    habilitado = Column(Boolean, nullable=False, default=True)
    added_at = Column(TIMESTAMP, nullable=False)
    last_used_at = Column(TIMESTAMP, nullable=True)

    __table_args__ = (UniqueConstraint("usuario_id","metodo", name="uq_usuario_metodo"),)

class CatPreguntaSeguridad(Base):
    __tablename__ = "cat_pregunta_seguridad"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    texto = Column(String(255), nullable=False)

class UsuarioPregunta(Base):
    __tablename__ = "usuario_pregunta"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    usuario_id = Column(BigInteger, ForeignKey("usuario.id"), nullable=False)
    pregunta_id = Column(BigInteger, ForeignKey("cat_pregunta_seguridad.id"), nullable=False)
    respuesta_hash = Column(LargeBinary(255), nullable=False)
    __table_args__ = (UniqueConstraint("usuario_id","pregunta_id", name="uq_usuario_pregunta"),)

class OTPCodigo(Base):
    __tablename__ = "otp_codigo"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    usuario_id = Column(BigInteger, ForeignKey("usuario.id"), nullable=False)
    metodo = Column(Enum(*OTPMedio), nullable=False)
    code_hash = Column(LargeBinary(255), nullable=False)
    expira_en = Column(DateTime, nullable=False)
    consumido_en = Column(DateTime, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)

class Sesion(Base):
    __tablename__ = "sesion"
    id = Column(String(26), primary_key=True)
    usuario_id = Column(BigInteger, ForeignKey("usuario.id"), nullable=False)
    inicio = Column(DateTime, nullable=False)
    ultimo_mov = Column(DateTime, nullable=False)
    cierre = Column(DateTime, nullable=True)
    ip = Column(String(45))
    user_agent = Column(String(255))
    revocada = Column(Boolean, nullable=False, default=False)
    expira_en = Column(DateTime, nullable=False)

    refresh_hash = Column(LargeBinary(255), nullable=True)
    refresh_expira_en = Column(DateTime, nullable=True)
    rotation_counter = Column(Integer, nullable=False, default=0)
    kid = Column(String(64), nullable=True)

    # MySQL computed stored column
    activa = Column(Boolean, Computed("IF(cierre IS NULL AND revocada=0, 1, 0)", persisted=True))

    usuario = relationship("Usuario", back_populates="sesiones")

class RefreshHistorial(Base):
    __tablename__ = "refresh_historial"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sesion_id = Column(String(26), ForeignKey("sesion.id"), nullable=False)
    prev_hash = Column(LargeBinary(255), nullable=False)
    rotado_en = Column(TIMESTAMP, nullable=False)

class AccesoLog(Base):
    __tablename__ = "acceso_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    usuario_id = Column(BigInteger, ForeignKey("usuario.id"), nullable=True)
    email_intentado = Column(String(160), nullable=True)
    momento = Column(DateTime, nullable=False)
    exito = Column(Boolean, nullable=False)
    ip = Column(String(45), nullable=True)
    detalle = Column(String(255), nullable=True)

class UsuarioBloqueo(Base):
    __tablename__ = "usuario_bloqueo"
    usuario_id = Column(BigInteger, ForeignKey("usuario.id"), primary_key=True)
    intentos_fallidos = Column(Integer, nullable=False, default=0)
    bloqueado_hasta = Column(DateTime, nullable=True)
    ultimo_intento = Column(DateTime, nullable=True)
    updated_at = Column(TIMESTAMP, nullable=False)

class BloqueoEvento(Base):
    __tablename__ = "bloqueo_evento"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    usuario_id = Column(BigInteger, ForeignKey("usuario.id"), nullable=False)
    tipo = Column(Enum(*BloqueoTipo), nullable=False)
    motivo = Column(String(200), nullable=True)
    efectuado_por = Column(BigInteger, nullable=True)
    momento = Column(TIMESTAMP, nullable=False)

class PasswordResetToken(Base):
    __tablename__ = "password_reset_token"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    usuario_id = Column(BigInteger, ForeignKey("usuario.id"), nullable=False)
    token = Column(String(64), nullable=False, unique=True)
    expira_en = Column(DateTime, nullable=False)
    usado_en = Column(DateTime, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)

class UsernameRecoveryLog(Base):
    __tablename__ = "username_recovery_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email_enviado_a = Column(String(160), nullable=False)
    ip = Column(String(45), nullable=True)
    enviado_en = Column(TIMESTAMP, nullable=False)
