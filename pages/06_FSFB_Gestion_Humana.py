# pages/06_FSFB_Gestion_Humana.py
from __future__ import annotations
import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

from services.settings import inject_css, debug_toggle, debug, CorpusTheme
from services.risk_engine import (
    make_dummy_population, compute_risk_and_survival, risk_tier, explain_contributions
)
from components.survival_plot import render_survival_curve
from components.ui_blocks import kpi_card, section_header

st.set_page_config(
    page_title="FSFB • Gestión Humana",
    page_icon="👥",
    layout="wide"
)

inject_css()
debug_toggle()

section_header("👥 FSFB • Gestión Humana (Empleados)", subtitle="Prevención y bienestar con enfoque poblacional y privacidad por diseño")

# Cohorte dummy (o reemplazar por integración)
if "hr_employees" not in st.session_state:
    st.session_state.hr_employees = make_dummy_population(400, include_dept=True)

df = st.session_state.hr_employees.copy()

# Filtros
with st.expander("🔎 Filtros de cohorte"):
    c1, c2, c3, c4 = st.columns(4)
    dept_opt = ["Todos"] + sorted(df["department"].unique().tolist())
    dept = c1.selectbox("Departamento", dept_opt)
    sex = c2.selectbox("Sexo", ["Todos", "M", "F"])
    age_min = c3.slider("Edad mínima", 18, 80, 25)
    age_max = c4.slider("Edad máxima", 20, 85, 65)
    apply = st.button("Aplicar filtros", use_container_width=True)

if apply:
    if dept != "Todos":
        df = df[df["department"]==dept]
    if sex != "Todos":
        df = df[df["sex"]==sex]
    df = df[(df["age"]>=age_min) & (df["age"]<=age_max)]

# Agregados: riesgo a 24m si no existe
if "risk_pct_24m" not in df.columns:
    risks = []
    for _, r in df.iterrows():
        risk, s_df, meta = compute_risk_and_survival(r.to_dict(), 24)
        risks.append(risk)
    df["risk_pct_24m"] = np.round(risks, 1)
    df["risk_tier_24m"] = df["risk_pct_24m"].apply(risk_tier)

# Privacidad (k-anonymity simple)
K_MIN = 10
if df.shape[0] < K_MIN:
    st.warning("⚠️ Para proteger la privacidad, los agregados se muestran solo con 10+ empleados. Ajusta los filtros.")
else:
    # KPIs poblacionales
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Empleados analizados", df.shape[0])
    c2.metric("Riesgo medio (24m)", f"{df['risk_pct_24m'].mean():.1f}%")
    c3.metric("Alto riesgo", f"{(df['risk_tier_24m']=='alto').mean()*100:.1f}%")
    c4.metric("Medio riesgo", f"{(df['risk_tier_24m']=='medio').mean()*100:.1f}%")

    st.markdown("### Distribución de riesgo (24 meses)")
    fig = px.histogram(df, x="risk_pct_24m", nbins=20, title="Histograma de riesgo (24m)")
    fig.update_layout(template="plotly_dark", xaxis_title="Riesgo (%)", yaxis_title="Frecuencia")
    st.plotly_chart(fig, use_container_width=True)

    # Tabla priorizada
    st.markdown("### Lista priorizada (top 50 por riesgo)")
    top = df.sort_values("risk_pct_24m", ascending=False).head(50).reset_index(drop=True)
    st.dataframe(top[["employee_id","department","age","sex","risk_pct_24m","risk_tier_24m"]], use_container_width=True)

st.markdown("---")
st.subheader("Búsqueda y revisión individual (con consentimiento)")

cA, cB = st.columns([0.9, 1.1])
with cA:
    emp_id = st.text_input("ID de empleado", placeholder="Ej. E-00128")
    consent = st.checkbox("✅ Confirmo que cuento con consentimiento explícito del empleado para revisar el resultado individual.", value=False)
with cB:
    horizon = st.select_slider("Horizonte", options=[12,24,36,60], value=24)

if st.button("Consultar empleado", use_container_width=True):
    if not consent:
        st.error("Se requiere consentimiento explícito para mostrar datos individuales.")
        st.stop()
    if emp_id not in df["employee_id"].values:
        st.error("Empleado no encontrado con los filtros actuales.")
        st.stop()

    row = df[df["employee_id"]==emp_id].iloc[0].to_dict()
    risk, s_df, meta = compute_risk_and_survival(row, horizon)
    tier = risk_tier(risk)
    contrib = explain_contributions(row)

    k1, k2, k3 = st.columns(3)
    k1.metric("Risk factor", f"{risk:.1f}%")
    k2.metric("Nivel", tier.upper())
    k3.metric("Ventana crítica", f"{meta['peak_window'][0]}–{meta['peak_window'][1]} m")

    with st.container(border=True):
        render_survival_curve(s_df, horizon)

    st.markdown("**Principales impulsores del riesgo**")
    for name, pct, text in contrib[:6]:
        st.markdown(f"- **{name}** — {pct:+.1f} pp · {text}")
    st.info("Recomendación para Gestión Humana: canaliza a programas de bienestar y prevención (nutrición, actividad física, control de HTA/DM, cesación de tabaco), priorizando empleados en riesgo **alto** y **medio** según impulsores modificables.")
