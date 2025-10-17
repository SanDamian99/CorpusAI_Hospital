# pages/4_Direccion_ROI.py
from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
from components.cards import kpi, section
from components.charts import survival_curve_chart
from services.data_loader import load_csv
from services.risk_api import score_batch
from services.whatif import expected_avoided_events, roi
from services.settings import inject_css, debug_toggle, debug

st.set_page_config(page_title="Dirección & Contratos (ROI)", page_icon="📊", layout="wide")
inject_css(); debug_toggle()

st.header("📊 Dirección & Contratos (ROI/Calidad)")
uploaded = st.file_uploader("Sube CSV (opcional). Si omites, se usa dataset dummy.", type=["csv"])
df = load_csv(uploaded)
scored = score_batch(df)

st.subheader("Supuestos del escenario")
c1, c2, c3, c4 = st.columns(4)
coverage = c1.slider("Cobertura programa (Top riesgo)", 0, 100, 30, 5) / 100
efficacy = c2.slider("Eficacia intervención", 0, 100, 25, 5) / 100
cost_event = c3.number_input("Costo por evento (USD)", min_value=100.0, value=2500.0, step=100.0)
cost_program = c4.number_input("Costo por paciente tratado (USD)", min_value=5.0, value=45.0, step=5.0)

# Baseline: tasa de evento a 30 días ~ 1 - S(30)
def event_rate_30(row):
    s30 = [p["S"] for p in row if p["day"]==30]
    return 1.0 - (s30[0] if s30 else 0.85)

scored["event_rate_30d"] = scored["surv_curve"].apply(event_rate_30)

# Tratados = top por riesgo * cobertura
scored = scored.sort_values("risk_factor", ascending=False)
n_total = len(scored)
n_target = int(np.ceil(n_total * coverage))
baseline_rate = scored.head(n_target)["event_rate_30d"].mean() if n_target>0 else 0.0

avoided = expected_avoided_events(n_total, baseline_rate, coverage, efficacy)
benefits, costs, ratio = roi(avoided, cost_event, cost_program, n_target)

k1,k2,k3,k4 = st.columns(4)
kpi("Cohorte total", f"{n_total}", cols=k1)
kpi("Tratados (cobertura)", f"{n_target}", f"{coverage:.0%} del total", cols=k2)
kpi("Eventos evitados (30d)", f"{avoided:.1f}", f"Tasa base ~{baseline_rate:.0%}", cols=k3)
kpi("ROI", f"{ratio:.2f}x", f"Beneficio vs. costo", cols=k4)

st.divider()
section("Distribución de riesgo (Top 50)", "Explora curvas de algunos pacientes en alta prioridad")
subset = scored.head(min(50, len(scored)))
sel = st.selectbox("Paciente", subset["patient_id"])
row = subset[subset["patient_id"]==sel].iloc[0]
st.altair_chart(survival_curve_chart(row["surv_curve"], height=200), use_container_width=True)

# Evidencia exportable
st.subheader("Exportar evidencia para contrato")
exp = scored[["patient_id","servicio","risk_factor","event_rate_30d","t_start_days","t_end_days"]].copy()
exp["riesgo_%"] = (exp["risk_factor"]*100).round(0)
st.download_button("⬇️ Exportar evidencia CSV", exp.to_csv(index=False).encode("utf-8"), "evidencia_contrato.csv", "text/csv")
debug("Página Dirección & ROI renderizada")
