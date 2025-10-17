# app.py
from __future__ import annotations
import streamlit as st
from services.settings import inject_css, debug_toggle, debug

st.set_page_config(page_title="Corpus AI · Pilotos Hospitalarios", page_icon="🩺", layout="wide")
inject_css()
debug_toggle()

st.title("Corpus AI · Pilotos Hospitalarios")
st.write("Explora 4 opciones de interfaz para Hospitales/IPS: **Alta Segura, Censo Inteligente, Clínicas Cardio-Renales y Dirección/ROI**.")

st.markdown("""
**Cómo empezar**
1. Ve a la barra lateral → Páginas.
2. Sube tu CSV (o usa los datos **dummy** precargados).
3. Prueba filtros, acciones y exportaciones.
""")

if st.session_state.get("DEBUG_MODE", False):
    st.info("🔧 Debug activo: se mostrarán mensajes internos en la barra lateral.")
debug("App iniciada")
