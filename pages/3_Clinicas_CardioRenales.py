# pages/3_Clinicas_CardioRenales.py
from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
from components.cards import kpi, section
from components.charts import deciles_km_chart, survival_curve_chart
from services.data_loader import load_csv
from services.risk_api import score_batch
from services.settings import inject_css, debug_toggle, debug

st.set_page_config(page_title="Clínicas Cardio-Renales", page_icon="🫀", layout="wide")
inject_css(); debug_toggle()

st.header("🫀 Clínicas Cardio-Renales (Seguimiento Intensivo)")
uploaded = st.file_uploader("Sube CSV (opcional). Si omites, se usa dataset dummy.", type=["csv"])
df = load_csv(uploaded)
scored = score_batch(df)

# Constructor de cohortes
st.subheader("Constructor de cohortes")
c1, c2, c3, c4 = st.columns(4)
svc = c1.multiselect("Servicio", sorted(scored["servicio"].unique().tolist()))
hba = c2.slider("HbA1c mínima", 4.5, 13.5, 7.0, 0.1)
cre = c3.slider("Creatinina mínima", 0.4, 6.0, 1.2, 0.1)
poly = c4.slider("Polifarmacia mínima", 0, 18, 5, 1)

cohort = scored[
    (scored["hba1c"] >= hba) &
    (scored["creatinina"] >= cre) &
    (scored["polifarmacia_n"] >= poly)
]
if svc: cohort = cohort[cohort["servicio"].isin(svc)]

k1,k2,k3 = st.columns(3)
kpi("Tamaño cohorte", f"{len(cohort)}", cols=k1)
kpi("Riesgo medio (cohorte)", f"{cohort['risk_factor'].mean():.0%}" if len(cohort)>0 else "–", cols=k2)
kpi("Mediana ventana (cohorte)", f"{int(cohort['t_start_days'].median())}-{int(cohort['t_end_days'].median())} días" if len(cohort)>0 else "–", cols=k3)

# KM por deciles (promedio S(t) por decil de riesgo)
st.subheader("Curvas KM por deciles de riesgo")
if len(cohort) >= 10:
    cohort = cohort.copy()
    cohort["decile"] = pd.qcut(cohort["risk_factor"], 10, labels=False) + 1
    deciles = {}
    for d in range(1,11):
        sub = cohort[cohort["decile"]==d]
        # Promedia S(t) por día
        # (convertir lista de dicts a matriz)
        ts = sorted({p["day"] for row in sub["surv_curve"] for p in row})
        vals = []
        for t in ts:
            vals.append(np.mean([ [p["S"] for p in row if p["day"]==t][0] for row in sub["surv_curve"] ]))
        deciles[d] = [{"day":int(t), "S":float(v)} for t,v in zip(ts, vals)]
    st.altair_chart(deciles_km_chart(deciles), use_container_width=True)
else:
    st.info("Crea una cohorte con al menos 10 pacientes para ver KM por deciles.")

# Agenda sugerida (dentro de la ventana de mayor probabilidad)
st.subheader("Agenda sugerida (primer control)")
today = date.today()
def suggest_followup(t_start):
    return today + timedelta(days=int(max(7, min(14, t_start))))

if len(cohort) > 0:
    cohort["control_sugerido"] = cohort["t_start_days"].apply(suggest_followup)
    show = cohort.sort_values("risk_factor", ascending=False)[["patient_id","servicio","risk_factor","t_start_days","t_end_days","control_sugerido"]]
    show["riesgo"] = (show["risk_factor"]*100).round(0).astype(int).astype(str) + "%"
    st.dataframe(show.drop(columns=["risk_factor"]), use_container_width=True, height=380)
    st.download_button("⬇️ Exportar agenda CSV", show.to_csv(index=False).encode("utf-8"), "agenda_sugerida.csv", "text/csv")
debug("Página Clínicas Cardio-Renales renderizada")
