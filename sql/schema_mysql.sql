
-- ------------------------------------------------------------
-- Base de datos de Seguridad / Autenticación (MySQL 8+)
-- ------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS seguridaddb
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;
USE seguridaddb;

-- Limpieza (opcional en desarrollo)
DROP TABLE IF EXISTS refresh_historial;
DROP TABLE IF EXISTS username_recovery_log;
DROP TABLE IF EXISTS password_reset_token;
DROP TABLE IF EXISTS bloqueo_evento;
DROP TABLE IF EXISTS usuario_bloqueo;
DROP TABLE IF EXISTS acceso_log;
DROP TABLE IF EXISTS sesion;
DROP TABLE IF EXISTS otp_codigo;
DROP TABLE IF EXISTS usuario_pregunta;
DROP TABLE IF EXISTS cat_pregunta_seguridad;
DROP TABLE IF EXISTS usuario_mfa;
DROP TABLE IF EXISTS verificacion_contacto;
DROP TABLE IF EXISTS usuario_credencial;
DROP TABLE IF EXISTS usuario;
DROP TABLE IF EXISTS cliente;

-- CLIENTE
CREATE TABLE cliente (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  nombre        VARCHAR(150) NOT NULL,
  identificador VARCHAR(50),
  estado ENUM('activo','inactivo') DEFAULT 'activo',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- USUARIO
CREATE TABLE usuario (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  cliente_id BIGINT NOT NULL,
  nombres   VARCHAR(120) NOT NULL,
  apellidos VARCHAR(120) NOT NULL,
  email     VARCHAR(160) NOT NULL,
  telefono  VARCHAR(30),
  estado    ENUM('pendiente','activo','suspendido','bloqueado','inactivo')
            NOT NULL DEFAULT 'pendiente',
  email_verificado   TINYINT(1) NOT NULL DEFAULT 0,
  telefono_verificado TINYINT(1) NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_usuario_email (email),
  CONSTRAINT fk_usuario_cliente FOREIGN KEY (cliente_id) REFERENCES cliente(id)
) ENGINE=InnoDB;

-- CREDENCIAL
CREATE TABLE usuario_credencial (
  usuario_id BIGINT PRIMARY KEY,
  password_hash VARBINARY(255) NOT NULL,
  password_updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (usuario_id) REFERENCES usuario(id)
) ENGINE=InnoDB;

-- Verificación de contacto (email / teléfono)
CREATE TABLE verificacion_contacto (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  usuario_id BIGINT NOT NULL,
  tipo ENUM('email','telefono') NOT NULL,
  token CHAR(64) NOT NULL,
  expira_en DATETIME NOT NULL,
  verificado_en DATETIME NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_verif_usuario_tipo (usuario_id, tipo, verificado_en),
  FOREIGN KEY (usuario_id) REFERENCES usuario(id)
) ENGINE=InnoDB;

-- Métodos MFA por usuario
CREATE TABLE usuario_mfa (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  usuario_id BIGINT NOT NULL,
  metodo ENUM('email_code','sms_code','security_question','security_key','totp') NOT NULL,
  secreto VARBINARY(512) NULL,
  habilitado TINYINT(1) NOT NULL DEFAULT 1,
  added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_used_at TIMESTAMP NULL,
  FOREIGN KEY (usuario_id) REFERENCES usuario(id),
  UNIQUE KEY uq_usuario_metodo (usuario_id, metodo)
) ENGINE=InnoDB;

-- Catálogo de preguntas de seguridad
CREATE TABLE cat_pregunta_seguridad (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  texto VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

-- Respuestas de seguridad (hash)
CREATE TABLE usuario_pregunta (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  usuario_id BIGINT NOT NULL,
  pregunta_id BIGINT NOT NULL,
  respuesta_hash VARBINARY(255) NOT NULL,
  UNIQUE KEY uq_usuario_pregunta (usuario_id, pregunta_id),
  FOREIGN KEY (usuario_id) REFERENCES usuario(id),
  FOREIGN KEY (pregunta_id) REFERENCES cat_pregunta_seguridad(id)
) ENGINE=InnoDB;

-- Códigos OTP/TOTP de un solo uso
CREATE TABLE otp_codigo (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  usuario_id BIGINT NOT NULL,
  metodo ENUM('email_code','sms_code','totp') NOT NULL,
  code_hash VARBINARY(255) NOT NULL,
  expira_en DATETIME NOT NULL,
  consumido_en DATETIME NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_otp_usuario (usuario_id, metodo, expira_en),
  FOREIGN KEY (usuario_id) REFERENCES usuario(id)
) ENGINE=InnoDB;

-- Sesiones (una activa por usuario) con refresh token
CREATE TABLE sesion (
  id CHAR(26) PRIMARY KEY,
  usuario_id BIGINT NOT NULL,
  inicio DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ultimo_mov DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  cierre DATETIME NULL,
  ip VARCHAR(45) NULL,
  user_agent VARCHAR(255) NULL,
  revocada TINYINT(1) NOT NULL DEFAULT 0,
  expira_en DATETIME NOT NULL,

  refresh_hash VARBINARY(255) NULL,
  refresh_expira_en DATETIME NULL,
  rotation_counter INT NOT NULL DEFAULT 0,
  kid VARCHAR(64) NULL,

  activa TINYINT(1) AS (IF(cierre IS NULL AND revocada=0, 1, 0)) STORED,
  FOREIGN KEY (usuario_id) REFERENCES usuario(id),
  UNIQUE KEY uq_sesion_unica_activa (usuario_id, activa)
) ENGINE=InnoDB;

-- Historial de refresh (detección de reutilización)
CREATE TABLE refresh_historial (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  sesion_id CHAR(26) NOT NULL,
  prev_hash VARBINARY(255) NOT NULL,
  rotado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (sesion_id) REFERENCES sesion(id)
) ENGINE=InnoDB;

-- Log de accesos (éxitos/fallos)
CREATE TABLE acceso_log (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  usuario_id BIGINT NULL,
  email_intentado VARCHAR(160) NULL,
  momento DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  exito TINYINT(1) NOT NULL,
  ip VARCHAR(45) NULL,
  detalle VARCHAR(255) NULL,
  FOREIGN KEY (usuario_id) REFERENCES usuario(id)
) ENGINE=InnoDB;

-- Contador/bloqueo por intentos
CREATE TABLE usuario_bloqueo (
  usuario_id BIGINT PRIMARY KEY,
  intentos_fallidos INT NOT NULL DEFAULT 0,
  bloqueado_hasta DATETIME NULL,
  ultimo_intento DATETIME NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (usuario_id) REFERENCES usuario(id)
) ENGINE=InnoDB;

-- Auditoría de bloqueos/desbloqueos
CREATE TABLE bloqueo_evento (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  usuario_id BIGINT NOT NULL,
  tipo ENUM('bloqueo','desbloqueo','autodesbloqueo') NOT NULL,
  motivo VARCHAR(200) NULL,
  efectuado_por BIGINT NULL,
  momento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (usuario_id) REFERENCES usuario(id)
) ENGINE=InnoDB;

-- Recuperación de contraseña
CREATE TABLE password_reset_token (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  usuario_id BIGINT NOT NULL,
  token CHAR(64) NOT NULL,
  expira_en DATETIME NOT NULL,
  usado_en DATETIME NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_prt_token (token),
  FOREIGN KEY (usuario_id) REFERENCES usuario(id)
) ENGINE=InnoDB;

-- Recordar usuario (opcional)
CREATE TABLE username_recovery_log (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  email_enviado_a VARCHAR(160) NOT NULL,
  ip VARCHAR(45) NULL,
  enviado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Seed mínimo
INSERT INTO cliente (nombre, identificador, estado) VALUES ('Default', NULL, 'activo');
