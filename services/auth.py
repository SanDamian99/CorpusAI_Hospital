# services/auth.py
from __future__ import annotations
import hashlib
import os
import time
import streamlit as st

SESS_AUTH_OK = "auth_ok"
SESS_AUTH_USER = "auth_user"

def _auth_conf():
    """
    Lee credenciales desde st.secrets.
    Formato esperado en .streamlit/secrets.toml:

    [auth]
    pepper = "cambia-esto-por-una-cadena-larga-aleatoria"
      [auth.users]
      jose = "sha256:xxxxxxxx..."
      santafe = "sha256:yyyyyyyy..."

    Para generar un hash: ver función hash_for() abajo.
    """
    auth = st.secrets.get("auth", {})
    users = auth.get("users", {})
    pepper = auth.get("pepper", "")
    return users, pepper

def _hash(uname: str, password: str, pepper: str) -> str:
    return hashlib.sha256(f"{uname}:{password}:{pepper}".encode("utf-8")).hexdigest()

def verify_password(uname: str, password: str) -> bool:
    users, pepper = _auth_conf()
    stored = users.get(uname)
    if not stored or not pepper:
        return False
    if stored.startswith("sha256:"):
        stored = stored.split(":", 1)[1]
    return _hash(uname, password, pepper) == stored

def _dev_mode_enabled() -> bool:
    # Permite desactivar auth en desarrollo: CORPUS_AUTH_DISABLED=1
    return os.getenv("CORPUS_AUTH_DISABLED", "0").lower() in ("1", "true", "yes")

def logout_button():
    if st.session_state.get(SESS_AUTH_OK):
        with st.sidebar:
            st.divider()
            st.caption(f"🔐 Sesión: {st.session_state.get(SESS_AUTH_USER, '-')}")
            if st.button("Salir", use_container_width=True):
                for k in [SESS_AUTH_OK, SESS_AUTH_USER]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()

def login_required(app_name: str | None = None) -> bool:
    """
    Coloca esto al inicio de cada página (después de set_page_config):
      from services.auth import login_required
      login_required("Corpus AI · Pilotos Hospitalarios")
    """
    # Bypass en desarrollo si se define la variable de entorno
    if _dev_mode_enabled():
        st.session_state[SESS_AUTH_OK] = True
        st.session_state[SESS_AUTH_USER] = "dev"
        return True

    # Ya autenticado
    if st.session_state.get(SESS_AUTH_OK):
        logout_button()
        return True

    # Formulario de login
    with st.container():
        if app_name:
            st.title(app_name)
        st.subheader("Inicio de sesión")
        st.caption("Ingresa tu usuario y clave para continuar.")

        with st.form("login_form"):
            u = st.text_input("Usuario", value="", autocomplete="username")
            p = st.text_input("Clave", value="", type="password", autocomplete="current-password")
            remember = st.checkbox("Recordar durante esta sesión", value=True)
            ok = st.form_submit_button("Entrar", use_container_width=True)

        if ok:
            if verify_password(u.strip(), p):
                st.session_state[SESS_AUTH_OK] = True
                st.session_state[SESS_AUTH_USER] = u.strip()
                if remember:
                    # Pequeño delay para UX al redirigir
                    time.sleep(0.1)
                st.success("Acceso concedido. Redirigiendo…")
                st.rerun()
            else:
                st.error("Usuario o clave inválidos.")

        # No autenticado: detenemos el render del resto de la página
        st.stop()

def hash_for(username: str, password: str, pepper: str) -> str:
    """
    Ayuda: genera el hash para secrets.
    Uso local (ejemplo):
        python -c 'import services.auth as a; print("sha256:"+a.hash_for("jose","MiClaveSegura","PEPPER-LARGO"))'
    """
    return _hash(username, password, pepper)
