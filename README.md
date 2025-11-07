# Auth Stack (MySQL + FastAPI + Streamlit)

## 1) MySQL
- Crea la BD: `mysql -u root -p < sql/schema_mysql.sql`

## 2) Backend (FastAPI)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
cp .env.example .env  # y ajusta credenciales
uvicorn app.main:app --reload --port 8000
```

## 3) Frontend (Streamlit)
```bash
cd ../frontend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export API_BASE="http://localhost:8000"  # Windows: set API_BASE=http://localhost:8000
streamlit run app.py
```

## REQUISITOS IMPLEMENTADOS (7/7)

---

## 📊 Matriz de Cumplimiento

| # | Requisito | Estado | Evidencia en UI | Evidencia en BD |
|---|-----------|--------|----------------|-----------------|
| **RS1** | Validación de cuenta | ✅ | Tab "Perfil" muestra estado verificación | Campos `email_verificado`, `telefono_verificado` |
| **RS2** | Segundo factor (MFA) | ✅ | Tab "Seguridad" lista 5 métodos | Tablas `usuario_mfa`, `otp_codigo` |
| **RS3** | Auditoría completa | ✅ | Tab "Auditoría" muestra logs | Tabla `acceso_log` con todos los eventos |
| **RS4** | Recuperación credenciales | ✅ | Tab "Seguridad" formulario recovery | Tablas `password_reset_token`, `username_recovery_log` |
| **RS5** | Sesiones únicas | ✅ | Tab "Tokens" muestra session ID | Tabla `sesion` revoca anteriores |
| **RS6** | Bloqueo automático | ✅ | Login muestra "bloqueado" al 4to fallo | Tabla `usuario_bloqueo`, `bloqueo_evento` |
| **RS7** | Gestión sesiones | ✅ | Tab "Tokens" renueva tokens | Tabla `refresh_historial` con rotaciones |

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Streamlit)                  │
│  ┌───────┬───────┬────────┬────────┬─────────┬────────┐ │
│  │Registro│ Login │ Perfil │ Tokens │Seguridad│Auditoría│ │
│  └───────┴───────┴────────┴────────┴─────────┴────────┘ │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP/REST
┌───────────────────────────▼─────────────────────────────┐
│                    BACKEND (FastAPI)                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Endpoints:                                      │   │
│  │  • POST /auth/register  → Crea cliente + usuario│   │
│  │  • POST /auth/login     → Genera tokens         │   │
│  │  • POST /auth/refresh   → Rota refresh token    │   │
│  │  • POST /auth/logout    → Revoca sesión         │   │
│  │  • GET  /me            → Perfil con auth        │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Seguridad:                                      │   │
│  │  • SHA-256 + Bcrypt    • JWT con RS256          │   │
│  │  • Token rotation      • Session tracking        │   │
│  │  • Audit logging       • Auto-blocking           │   │
│  └──────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────┘
                            │ SQLAlchemy ORM
┌───────────────────────────▼─────────────────────────────┐
│                    DATABASE (MySQL 8.0)                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │  15 Tablas Implementadas:                        │   │
│  │                                                   │   │
│  │  Core:                    Seguridad:             │   │
│  │  • cliente               • verificacion_contacto │   │
│  │  • usuario               • usuario_mfa           │   │
│  │  • usuario_credencial    • otp_codigo            │   │
│  │                          • usuario_pregunta      │   │
│  │  Sesiones:               • cat_pregunta_seg.     │   │
│  │  • sesion                                        │   │
│  │  • refresh_historial     Recovery:               │   │
│  │                          • password_reset_token  │   │
│  │  Auditoría:              • username_recovery_log │   │
│  │  • acceso_log                                    │   │
│  │  • usuario_bloqueo       Total: 15 tablas       │   │
│  │  • bloqueo_evento                                │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

