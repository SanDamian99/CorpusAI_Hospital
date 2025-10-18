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

# ──────────────────────────────────────────────────────────────────────────────
# 👇 NUEVO: Landing con accesos directos y chequeos para FSFB
# ──────────────────────────────────────────────────────────────────────────────
import importlib
import os
from pathlib import Path

st.divider()
st.subheader("🆕 Novedades: FSFB (Fundación Santa Fe de Bogotá)")
st.write(
    "Se agregaron dos páginas: **FSFB • Checkeo Ejecutivo** y **FSFB • Gestión Humana (Empleados)** "
    "para prevención proactiva con explicabilidad y recomendaciones personalizadas."
)

# Accesos directos (usa st.page_link si está disponible en tu versión de Streamlit)
HAS_PAGE_LINK = hasattr(st, "page_link")
col_a, col_b = st.columns(2)

with col_a:
    if HAS_PAGE_LINK:
        st.page_link("pages/05_FSFB_Checkeo_Ejecutivo.py", label="🩺 FSFB • Checkeo Ejecutivo", icon="🩺")
    else:
        st.markdown("🩺 **FSFB • Checkeo Ejecutivo** → Navega desde *Pages* (barra lateral).")

with col_b:
    if HAS_PAGE_LINK:
        st.page_link("pages/06_FSFB_Gestion_Humana.py", label="👥 FSFB • Gestión Humana (Empleados)", icon="👥")
    else:
        st.markdown("👥 **FSFB • Gestión Humana (Empleados)** → Navega desde *Pages* (barra lateral).")

st.caption("Tip: también puedes activar `?debug=1` en la URL para ver trazas internas durante el pilotaje.")

# ──────────────────────────────────────────────────────────────────────────────
# 🔎 Chequeos rápidos (módulos y archivos clave)
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("### ✅ Chequeo rápido del entorno")

def _ok_bad(flag: bool) -> str:
    return "✅ OK" if flag else "❌ FALTA"

def _exists(path: str) -> bool:
    return Path(path).exists()

chk_cols = st.columns(2)

with chk_cols[0]:
    # Módulos nuevos
    try:
        importlib.import_module("components.survival_plot")
        sp_ok = True
    except Exception as e:
        sp_ok = False
        debug(f"components.survival_plot error: {e}")

    try:
        importlib.import_module("components.ui_blocks")
        ui_ok = True
    except Exception as e:
        ui_ok = False
        debug(f"components.ui_blocks error: {e}")

    try:
        importlib.import_module("services.risk_engine")
        re_ok = True
    except Exception as e:
        re_ok = False
        debug(f"services.risk_engine error: {e}")

    st.write(f"- `components/survival_plot.py`: {_ok_bad(sp_ok)}")
    st.write(f"- `components/ui_blocks.py`: {_ok_bad(ui_ok)}")
    st.write(f"- `services/risk_engine.py`: {_ok_bad(re_ok)}")

with chk_cols[1]:
    # Archivos de páginas
    fsfb_exec = _exists("pages/05_FSFB_Checkeo_Ejecutivo.py")
    fsfb_hr   = _exists("pages/06_FSFB_Gestion_Humana.py")
    st.write(f"- `pages/05_FSFB_Checkeo_Ejecutivo.py`: {_ok_bad(fsfb_exec)}")
    st.write(f"- `pages/06_FSFB_Gestion_Humana.py`: {_ok_bad(fsfb_hr)}")

# Dependencia para curvas FSFB (plotly)
try:
    import plotly  # noqa
    st.write("- `plotly`: ✅ OK")
except Exception as e:
    st.write("- `plotly`: ❌ FALTA")
    st.warning("Agrega `plotly>=5.24` en requirements.txt (ojo: es **plotly**, no *ploty*).")
    debug(f"plotly import error: {e}")

# ──────────────────────────────────────────────────────────────────────────────
# 🧭 Accesos directos a las 4 páginas originales (comodidad)
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("### Navegación rápida (Hospitales/IPS)")
g1, g2, g3, g4 = st.columns(4)
if HAS_PAGE_LINK:
    with g1:
        st.page_link("pages/1_Alta_Segura.py", label="✅ Alta Segura 30D", icon="✅")
    with g2:
        st.page_link("pages/2_Censo_Inteligente.py", label="🛏️ Censo Inteligente", icon="🛏️")
    with g3:
        st.page_link("pages/3_Clinicas_CardioRenales.py", label="🫀 Clínicas Cardio-Renales", icon="🫀")
    with g4:
        st.page_link("pages/4_Direccion_ROI.py", label="📊 Dirección & ROI", icon="📊")
else:
    st.info("Usa el menú *Pages* (barra lateral) para abrir las páginas del piloto.")

# ──────────────────────────────────────────────────────────────────────────────
# 🧪 Modo Debug: info útil
# ──────────────────────────────────────────────────────────────────────────────
if st.session_state.get("DEBUG_MODE", False):
    st.divider()
    st.subheader("🔧 Debug · Info útil")
    st.write("- Query params:", dict(st.query_params))
    st.write("- Session keys:", list(st.session_state.keys()))
    st.caption("Desactiva el modo Debug desde la barra lateral para una demo limpia.")
