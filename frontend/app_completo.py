import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="Sistema de Autenticación", page_icon="🔐", layout="wide")
st.title("🔐 Sistema de Autenticación")
st.caption("✅ 4/7 Requisitos Funcionando | 🟡 3/7 Estructurados")

# Estado de sesión
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# Mostrar si hay sesión activa
if st.session_state.access_token:
    st.success("✅ Sesión activa")
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🚪 Cerrar Sesión"):
            if st.session_state.session_id and st.session_state.refresh_token:
                try:
                    requests.post(f"{API_BASE}/auth/logout", json={
                        "session_id": st.session_state.session_id,
                        "refresh_token": st.session_state.refresh_token
                    })
                except:
                    pass
            st.session_state.access_token = None
            st.session_state.refresh_token = None
            st.session_state.session_id = None
            st.rerun()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📝 Registro",
    "🔑 Login",
    "👤 Mi Perfil",
    "🎫 Tokens (RS5,RS7)",
    "🔒 Requisitos (RS1-RS7)",
    "📊 Auditoría (RS3)"
])

# ==================== TAB 1: Registro ====================
with tab1:
    st.header("📝 Crear Cuenta")
    st.info("💡 Al registrarte, se creará automáticamente tu cuenta de cliente")

    with st.form("form_registro"):
        col1, col2 = st.columns(2)
        with col1:
            nombres = st.text_input("Nombres *", placeholder="Ej: Juan Carlos")
            email = st.text_input("Email *", placeholder="usuario@ejemplo.com")
            password = st.text_input("Contraseña *", type="password", placeholder="Mínimo 8 caracteres")

        with col2:
            apellidos = st.text_input("Apellidos *", placeholder="Ej: Pérez García")
            telefono = st.text_input("Teléfono (opcional)", placeholder="+52 123 456 7890")
            password_confirm = st.text_input("Confirmar Contraseña *", type="password")

        submitted = st.form_submit_button("🎯 Registrarme", use_container_width=True)

        if submitted:
            if not all([nombres, apellidos, email, password]):
                st.error("❌ Todos los campos marcados con * son obligatorios")
            elif password != password_confirm:
                st.error("❌ Las contraseñas no coinciden")
            elif len(password) < 8:
                st.error("❌ La contraseña debe tener al menos 8 caracteres")
            else:
                try:
                    with st.spinner("Registrando..."):
                        r = requests.post(f"{API_BASE}/auth/register", json={
                            "nombres": nombres,
                            "apellidos": apellidos,
                            "email": email,
                            "telefono": telefono or None,
                            "password": password
                        })

                    if r.status_code == 200:
                        user_data = r.json()
                        st.success("✅ ¡Cuenta creada exitosamente!")
                        st.balloons()
                        st.info("💡 Ahora puedes ir a la pestaña '🔑 Login' para iniciar sesión")
                        with st.expander("📄 Ver detalles"):
                            st.json(user_data)
                    else:
                        error_detail = r.json().get("detail", r.text)
                        st.error(f"❌ Error: {error_detail}")
                except Exception as e:
                    st.error(f"❌ Error de conexión: {str(e)}")

# ==================== TAB 2: Login ====================
with tab2:
    st.header("🔑 Iniciar Sesión")
    st.warning("🔒 **RS6 Activo**: Bloqueo automático tras 4 intentos fallidos (15 min)")

    with st.form("form_login"):
        email_login = st.text_input("Email", placeholder="usuario@ejemplo.com")
        password_login = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("🚀 Iniciar Sesión", use_container_width=True)

        if submitted:
            if not email_login or not password_login:
                st.error("❌ Email y contraseña son obligatorios")
            else:
                try:
                    with st.spinner("Autenticando..."):
                        r = requests.post(f"{API_BASE}/auth/login", json={
                            "email": email_login,
                            "password": password_login
                        })

                    if r.status_code == 200:
                        data = r.json()
                        st.session_state.access_token = data["access_token"]
                        st.session_state.refresh_token = data["refresh_token"]
                        st.session_state.session_id = data["session_id"]
                        st.success("✅ ¡Bienvenido!")
                        st.balloons()
                        st.info("💡 Ve a la pestaña '👤 Mi Perfil' para ver tu información")
                        st.rerun()
                    elif r.status_code == 423:
                        st.error("🔒 Usuario bloqueado temporalmente (15 minutos)")
                        st.warning("Has excedido el número de intentos permitidos")
                    else:
                        error_detail = r.json().get("detail", r.text)
                        st.error(f"❌ {error_detail}")
                except Exception as e:
                    st.error(f"❌ Error de conexión: {str(e)}")

    if st.session_state.access_token:
        st.divider()
        st.success("✅ Ya tienes una sesión activa")

# ==================== TAB 3: Perfil ====================
with tab3:
    st.header("👤 Mi Perfil")

    if not st.session_state.access_token:
        st.warning("⚠️ Debes iniciar sesión primero")
        st.info("👈 Ve a la pestaña '🔑 Login' para acceder")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("Información Personal")
        with col2:
            if st.button("🔄 Actualizar"):
                st.rerun()

        try:
            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
            r = requests.get(f"{API_BASE}/me", headers=headers)

            if r.status_code == 200:
                user_data = r.json()

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("👤 ID", user_data.get("id"))
                with col2:
                    st.metric("📧 Estado", user_data.get("estado"))
                with col3:
                    # RS1: Verificación (campo existe pero no funciona)
                    status = "✅" if user_data.get("email_verificado") else "🟡"
                    st.metric("Email Verificado", status)
                    if not user_data.get("email_verificado"):
                        st.caption("🟡 RS1: Endpoint faltante")

                st.divider()

                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Nombre Completo:**")
                    st.info(f"{user_data.get('nombres')} {user_data.get('apellidos')}")
                    st.write("**Email:**")
                    st.info(user_data.get('email'))

                with col2:
                    if user_data.get('telefono'):
                        st.write("**Teléfono:**")
                        st.info(user_data.get('telefono'))
                    else:
                        st.write("**Teléfono:**")
                        st.info("No especificado")

                st.divider()
                with st.expander("📋 Ver todos los datos (JSON)"):
                    st.json(user_data)

            elif r.status_code == 401:
                st.error("❌ Sesión expirada. Por favor inicia sesión nuevamente.")
                st.session_state.access_token = None
            else:
                st.error(f"❌ Error: {r.status_code}")
        except Exception as e:
            st.error(f"❌ Error de conexión: {str(e)}")

# ==================== TAB 4: Gestión de Tokens ====================
with tab4:
    st.header("🎫 Gestión de Tokens y Sesiones")
    st.success("✅ **RS5 & RS7**: Completamente funcionales")

    if not st.session_state.access_token:
        st.warning("⚠️ Debes iniciar sesión primero")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Estado de la Sesión")
            st.write(f"**Session ID:** `{st.session_state.session_id}`")
            st.write(f"**Access Token:** `{st.session_state.access_token[:30]}...`")
            st.write(f"**Refresh Token:** `{'•' * 40}`")

            st.divider()
            st.caption("✅ **RS5**: Control de sesiones únicas")
            st.caption("✅ **RS7**: Token rotation activo")

        with col2:
            st.subheader("⚙️ Acciones")

            if st.button("🔄 Renovar Tokens (RS7)", use_container_width=True):
                try:
                    with st.spinner("Renovando tokens..."):
                        r = requests.post(f"{API_BASE}/auth/refresh", json={
                            "session_id": st.session_state.session_id,
                            "refresh_token": st.session_state.refresh_token
                        })
                    if r.status_code == 200:
                        data = r.json()
                        st.session_state.access_token = data["access_token"]
                        st.session_state.refresh_token = data["refresh_token"]
                        st.success("✅ Tokens renovados (Token Rotation)")
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {r.text}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

            st.divider()

            if st.button("🚪 Cerrar Sesión", use_container_width=True, type="primary"):
                try:
                    r = requests.post(f"{API_BASE}/auth/logout", json={
                        "session_id": st.session_state.session_id,
                        "refresh_token": st.session_state.refresh_token
                    })
                    st.session_state.access_token = None
                    st.session_state.refresh_token = None
                    st.session_state.session_id = None
                    st.success("✅ Sesión cerrada y revocada")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ==================== TAB 5: Requisitos ====================
with tab5:
    st.header("🔒 Estado de Requisitos de Seguridad")

    # RS1 - PARCIAL
    with st.expander("🟡 **RS1**: Validación de Email/Teléfono (50% - Estructura lista)", expanded=False):
        st.warning("**Estado**: 🟡 Estructurado - Endpoints faltantes")

        col1, col2 = st.columns(2)
        with col1:
            st.write("**✅ Lo que existe:**")
            st.success("- Campos `email_verificado` y `telefono_verificado`")
            st.success("- Tabla `verificacion_contacto` creada")
            st.success("- Modelo SQLAlchemy definido")

        with col2:
            st.write("**❌ Lo que falta:**")
            st.error("- POST /auth/verify/send-email")
            st.error("- POST /auth/verify/send-sms")
            st.error("- POST /auth/verify/confirm")
            st.error("- Lógica de generación de tokens")

        st.divider()
        st.subheader("🎨 UI Simulada - Verificación de Email")
        with st.form("form_verify_email"):
            st.text_input("Email", value=st.session_state.get("email", "usuario@ejemplo.com"), disabled=True)
            if st.form_submit_button("📧 Enviar código de verificación"):
                st.error("❌ Endpoint no implementado: POST /auth/verify/send-email")

        st.text_input("Código de verificación", placeholder="123456")
        if st.button("✅ Verificar código"):
            st.error("❌ Endpoint no implementado: POST /auth/verify/confirm")

    # RS2 - PARCIAL
    with st.expander("🟡 **RS2**: Multi-Factor Authentication (30% - Tablas creadas)", expanded=False):
        st.warning("**Estado**: 🟡 Estructurado - Lógica faltante")

        col1, col2 = st.columns(2)
        with col1:
            st.write("**✅ Lo que existe:**")
            st.success("- Tabla `usuario_mfa` creada")
            st.success("- Tabla `otp_codigo` creada")
            st.success("- Tabla `usuario_pregunta` creada")
            st.success("- Soporte para 5 métodos")

        with col2:
            st.write("**❌ Lo que falta:**")
            st.error("- POST /auth/mfa/setup")
            st.error("- POST /auth/mfa/verify")
            st.error("- Generación de códigos TOTP")
            st.error("- Integración en login")

        st.divider()
        st.subheader("🎨 UI Simulada - Configurar MFA")
        metodo = st.selectbox("Método MFA", ["Email OTP", "SMS OTP", "TOTP (Authenticator)", "Security Questions", "Security Key"])
        if st.button("🔐 Activar MFA"):
            st.error("❌ Endpoint no implementado: POST /auth/mfa/setup")

    # RS3 - COMPLETO
    with st.expander("✅ **RS3**: Auditoría Completa (100% - ACTIVO)", expanded=False):
        st.success("**Estado**: ✅ Completamente funcional")

        col1, col2 = st.columns(2)
        with col1:
            st.write("**✅ Funcionando:**")
            st.success("- Tabla `acceso_log` activa")
            st.success("- Función `register_access_log()` activa")
            st.success("- Se registra cada login (exitoso/fallido)")
            st.success("- Captura IP, email, timestamp, detalles")

        with col2:
            st.write("**📊 Datos auditados:**")
            st.info("- Registro de usuarios")
            st.info("- Login exitoso")
            st.info("- Login fallido")
            st.info("- Bloqueos")
            st.info("- Desbloqueos")

        st.code("""
# En crud.py - FUNCIONANDO
def register_access_log(db, *, usuario_id, email_intentado, exito, ip, detalle):
    db.add(models.AccesoLog(
        usuario_id=usuario_id,
        email_intentado=email_intentado,
        momento=_utcnow(),
        exito=exito,
        ip=ip,
        detalle=detalle
    ))
        """, language="python")

    # RS4 - PARCIAL
    with st.expander("🟡 **RS4**: Recuperación de Credenciales (40% - Tablas creadas)", expanded=False):
        st.warning("**Estado**: 🟡 Estructurado - Endpoints faltantes")

        col1, col2 = st.columns(2)
        with col1:
            st.write("**✅ Lo que existe:**")
            st.success("- Tabla `password_reset_token` creada")
            st.success("- Tabla `username_recovery_log` creada")
            st.success("- Modelos SQLAlchemy definidos")

        with col2:
            st.write("**❌ Lo que falta:**")
            st.error("- POST /auth/password-reset/request")
            st.error("- POST /auth/password-reset/confirm")
            st.error("- POST /auth/username-recovery")
            st.error("- Lógica de envío de emails")

        st.divider()
        st.subheader("🎨 UI Simulada - Recuperar Contraseña")
        with st.form("form_recover"):
            st.text_input("Email", placeholder="usuario@ejemplo.com")
            if st.form_submit_button("📧 Enviar enlace de recuperación"):
                st.error("❌ Endpoint no implementado: POST /auth/password-reset/request")

    # RS5 - COMPLETO
    with st.expander("✅ **RS5**: Sesiones Únicas (100% - ACTIVO)", expanded=False):
        st.success("**Estado**: ✅ Completamente funcional")

        st.write("**✅ Funcionando:**")
        st.success("- Una sesión activa por usuario")
        st.success("- Revocación de sesiones anteriores")
        st.success("- Estados: pendiente, activo, suspendido, bloqueado, inactivo")
        st.success("- Columna computada `activa` en MySQL")

        st.code("""
# En crud.py - FUNCIONANDO
def create_session(db, usuario_id, ip, user_agent):
    # Cierra sesiones anteriores
    active = db.execute(
        select(models.Sesion).where(
            models.Sesion.usuario_id==usuario_id,
            models.Sesion.cierre==None,
            models.Sesion.revocada==False
        )
    ).scalars().all()
    
    for s in active:
        s.revocada = True
        s.cierre = _utcnow()
        """, language="python")

    # RS6 - COMPLETO
    with st.expander("✅ **RS6**: Bloqueo Automático (100% - ACTIVO)", expanded=False):
        st.success("**Estado**: ✅ Completamente funcional")

        col1, col2 = st.columns(2)
        with col1:
            st.write("**✅ Funcionando:**")
            st.success("- Bloqueo tras 4 intentos fallidos")
            st.success("- Auto-desbloqueo tras 15 minutos")
            st.success("- Tabla `usuario_bloqueo` activa")
            st.success("- Tabla `bloqueo_evento` activa")

        with col2:
            st.write("**⚙️ Configuración:**")
            st.info("- Max intentos: 4")
            st.info("- Tiempo bloqueo: 15 min")
            st.info("- Reset en login exitoso")

        st.warning("⚠️ Pruébalo: Intenta hacer login 4 veces con contraseña incorrecta")

    # RS7 - COMPLETO
    with st.expander("✅ **RS7**: Gestión de Sesiones (100% - ACTIVO)", expanded=False):
        st.success("**Estado**: ✅ Completamente funcional")

        st.write("**✅ Funcionando:**")
        st.success("- Refresh token rotation automático")
        st.success("- Tabla `refresh_historial` activa")
        st.success("- Endpoint `/auth/refresh` funcionando")
        st.success("- Endpoint `/auth/logout` funcionando")

        st.write("**⚙️ Configuración:**")
        st.info("- Access token: 30 minutos")
        st.info("- Refresh token: 7 días")
        st.info("- Sesión máxima: 8 horas")

        st.info("💡 Ve a la pestaña 'Tokens' para probar el token rotation")

# ==================== TAB 6: Auditoría ====================
with tab6:
    st.header("📊 Auditoría y Monitoreo")
    st.success("✅ **RS3**: Completamente funcional y activo")

    st.subheader("🗄️ Base de Datos - 15 Tablas")

    try:
        import pandas as pd

        tables_data = {
            "Tabla": [
                "cliente", "usuario", "usuario_credencial",
                "verificacion_contacto", "usuario_mfa", "cat_pregunta_seguridad",
                "usuario_pregunta", "otp_codigo", "sesion", "refresh_historial",
                "acceso_log", "usuario_bloqueo", "bloqueo_evento",
                "password_reset_token", "username_recovery_log"
            ],
            "Requisito": [
                "Core", "Core", "Core",
                "RS1 🟡", "RS2 🟡", "RS2 🟡",
                "RS2 🟡", "RS2 🟡", "RS5 ✅", "RS7 ✅",
                "RS3 ✅", "RS6 ✅", "RS6 ✅",
                "RS4 🟡", "RS4 🟡"
            ],
            "Estado": [
                "✅ Activa", "✅ Activa", "✅ Activa",
                "🟡 Creada", "🟡 Creada", "🟡 Creada",
                "🟡 Creada", "🟡 Creada", "✅ Activa", "✅ Activa",
                "✅ Activa", "✅ Activa", "✅ Activa",
                "🟡 Creada", "🟡 Creada"
            ]
        }

        df = pd.DataFrame(tables_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    except:
        st.write("(Instalar pandas para ver tabla)")

    st.divider()

    if st.session_state.access_token:
        st.subheader("📈 Tu Sesión Actual")
        try:
            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
            r = requests.get(f"{API_BASE}/me", headers=headers)

            if r.status_code == 200:
                user_data = r.json()

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("👤 Usuario ID", user_data.get("id"))
                with col2:
                    st.metric("📧 Estado", user_data.get("estado"))
                with col3:
                    st.metric("🔐 Sesión", st.session_state.session_id[:8] + "...")
                with col4:
                    st.metric("✅ RS Activos", "4/7")

                st.success("✅ Esta sesión está siendo auditada en tiempo real (RS3)")
        except:
            pass
    else:
        st.info("💡 Inicia sesión para ver métricas de tu sesión")

# Footer
st.divider()
st.caption("🔐 Sistema de Autenticación Enterprise")
st.caption("✅ 4/7 Requisitos Funcionando (RS3, RS5, RS6, RS7) | 🟡 3/7 Estructurados (RS1, RS2, RS4)")

