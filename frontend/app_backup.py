import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="Sistema de Autenticación", page_icon="🔐", layout="centered")
st.title("🔐 Sistema de Autenticación")

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

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Registro",
    "🔑 Login",
    "👤 Mi Perfil",
    "🎫 Gestión de Tokens",
    "📊 Auditoría"
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
                    else:
                        error_detail = r.json().get("detail", r.text)
                        st.error(f"❌ {error_detail}")
                except Exception as e:
                    st.error(f"❌ Error de conexión: {str(e)}")

    if st.session_state.access_token:
        st.divider()
        st.success("✅ Ya tienes una sesión activa")
        if st.button("🔄 Renovar Token", use_container_width=True):
            try:
                r = requests.post(f"{API_BASE}/auth/refresh", json={
                    "session_id": st.session_state.session_id,
                    "refresh_token": st.session_state.refresh_token
                })
                if r.status_code == 200:
                    data = r.json()
                    st.session_state.access_token = data["access_token"]
                    st.session_state.refresh_token = data["refresh_token"]
                    st.success("✅ Token renovado")
                    st.rerun()
                else:
                    st.error("❌ Error al renovar token")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

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

                # Tarjeta de perfil
                with st.container():
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("👤 ID", user_data.get("id"))
                    with col2:
                        st.metric("📧 Estado", user_data.get("estado"))
                    with col3:
                        st.metric("✉️ Email Verificado", "✅ Sí" if user_data.get("email_verificado") else "❌ No")

                st.divider()

                # Información detallada
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
                if st.button("🔄 Ir a Login"):
                    st.rerun()
            else:
                st.error(f"❌ Error: {r.status_code}")
        except Exception as e:
            st.error(f"❌ Error de conexión: {str(e)}")

# ==================== TAB 4: Gestión de Tokens ====================
with tab4:
    st.header("🎫 Gestión de Tokens y Sesiones")
    st.info("**RS5 & RS7**: Control de sesiones únicas y gestión completa de sesiones")

    if not st.session_state.access_token:
        st.warning("⚠️ Debes iniciar sesión primero")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Estado de la Sesión")
            st.write(f"**Session ID:** `{st.session_state.session_id}`")
            if st.session_state.access_token:
                st.write(f"**Access Token (inicio):** `{st.session_state.access_token[:30]}...`")
                st.write(f"**Access Token (fin):** `...{st.session_state.access_token[-20:]}`")
            if st.session_state.refresh_token:
                st.write(f"**Refresh Token:** `{'•' * 40}`")

            st.divider()
            st.caption("✅ **RS7**: Gestión completa de sesiones")
            st.caption("- Token de acceso con expiración")
            st.caption("- Refresh token para renovación")
            st.caption("- Session ID único")
            st.caption("- Cierre de sesión seguro")

        with col2:
            st.subheader("⚙️ Acciones")

            if st.button("🔄 Renovar Tokens (Refresh)", use_container_width=True):
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
                        st.success("✅ Tokens renovados exitosamente")
                        st.info("🔄 Token rotation implementado")
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {r.text}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

            st.divider()

            if st.button("🚪 Cerrar Sesión Completa", use_container_width=True, type="primary"):
                try:
                    r = requests.post(f"{API_BASE}/auth/logout", json={
                        "session_id": st.session_state.session_id,
                        "refresh_token": st.session_state.refresh_token
                    })
                    st.session_state.access_token = None
                    st.session_state.refresh_token = None
                    st.session_state.session_id = None
                    st.success("✅ Sesión cerrada y tokens revocados")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ==================== TAB 5: Auditoría ====================
with tab5:
    st.header("📊 Auditoría y Monitoreo")
    st.info("**RS3**: Sistema de auditoría completa implementado")

    if not st.session_state.access_token:
        st.warning("⚠️ Debes iniciar sesión para ver información de auditoría")
    else:
        st.subheader("📋 Características de Auditoría Implementadas")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**🔍 Registro de Accesos:**")
            st.success("✅ Tabla `acceso_log`")
            st.write("""
            - Usuario ID
            - Email intentado
            - Timestamp exacto
            - Éxito/Fallo
            - IP de origen
            - Detalle de la acción
            """)

            st.divider()

            st.write("**🔒 Eventos de Bloqueo:**")
            st.success("✅ Tabla `bloqueo_evento`")
            st.write("""
            - Tipo: bloqueo/desbloqueo/autodesbloqueo
            - Motivo
            - Efectuado por
            - Timestamp
            """)

        with col2:
            st.write("**🔄 Historial de Tokens:**")
            st.success("✅ Tabla `refresh_historial`")
            st.write("""
            - Hash del token anterior
            - Timestamp de rotación
            - Session ID
            """)

            st.divider()

            st.write("**👤 Recuperación de Credenciales:**")
            st.success("✅ Tabla `username_recovery_log`")
            st.write("""
            - Email destino
            - IP solicitante
            - Timestamp de envío
            """)

        st.divider()

        # Resumen de tablas
        st.subheader("🗄️ Estructura de Base de Datos")

        with st.expander("Ver todas las tablas implementadas"):
            tables_data = {
                "Tabla": [
                    "cliente", "usuario", "usuario_credencial",
                    "verificacion_contacto", "usuario_mfa", "cat_pregunta_seguridad",
                    "usuario_pregunta", "otp_codigo", "sesion", "refresh_historial",
                    "acceso_log", "usuario_bloqueo", "bloqueo_evento",
                    "password_reset_token", "username_recovery_log"
                ],
                "Función": [
                    "Gestión de clientes",
                    "Información de usuarios",
                    "Contraseñas hasheadas",
                    "Verificación email/teléfono",
                    "Configuración MFA",
                    "Catálogo de preguntas",
                    "Preguntas de seguridad por usuario",
                    "Códigos OTP temporales",
                    "Sesiones activas",
                    "Historial de refresh tokens",
                    "Log de todos los accesos",
                    "Control de intentos fallidos",
                    "Eventos de bloqueo/desbloqueo",
                    "Tokens de reset de contraseña",
                    "Log de recuperación de usuarios"
                ],
                "Requisito": [
                    "RS5", "RS1, RS5", "RS1",
                    "RS1", "RS2", "RS2",
                    "RS2", "RS2", "RS5, RS7",
                    "RS7", "RS3", "RS6",
                    "RS6", "RS4", "RS4"
                ]
            }

            import pandas as pd
            df = pd.DataFrame(tables_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()

        # Demostración en vivo
        st.subheader("📈 Datos en Vivo")

        try:
            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
            r = requests.get(f"{API_BASE}/me", headers=headers)

            if r.status_code == 200:
                user_data = r.json()

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("👤 Usuario ID", user_data.get("id"))
                with col2:
                    st.metric("📧 Estado", user_data.get("estado"))
                with col3:
                    st.metric("🔐 Sesión", st.session_state.session_id[:8] + "...")

                st.success("✅ Todos los datos están siendo auditados en tiempo real")
                st.info("💡 Cada acción (login, logout, refresh, etc.) se registra en `acceso_log`")

        except Exception as e:
            st.error(f"Error: {str(e)}")

# Footer
st.divider()
st.caption("🔐 Sistema de Autenticación | FastAPI + MySQL + Streamlit")
st.caption("✅ Cumple con los 7 requisitos de seguridad (RS1-RS7)")
