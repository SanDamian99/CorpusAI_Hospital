# pages/2_Censo_Inteligente.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from components.cards import kpi, section
from components.charts import occupancy_heatmap
from components.tables import style_risk_table
from services.data_loader import load_csv, days_between
from services.risk_api import score_batch
from services.settings import inject_css, debug_toggle, debug

st.set_page_config(page_title="Censo Inteligente", page_icon="🛏️", layout="wide")
inject_css(); debug_toggle()

st.header("🛏️ Censo Inteligente")
uploaded = st.file_uploader("Sube CSV de censo (opcional). Si omites, se usa dataset dummy.", type=["csv"])
df = load_csv(uploaded)

df["day_estancia"] = df.apply(lambda r: max(0, days_between(r["fecha_ingreso"], r["fecha_egreso_prevista"])), axis=1)
scored = score_batch(df)

c1, c2, c3 = st.columns(3)
kpi("Pacientes", f"{len(scored)}", cols=c1)
kpi("Riesgo medio", f"{scored['risk_factor'].mean():.0%}", cols=c2)
kpi("Rojos por cama", f"{(scored['risk_factor']>=0.40).sum()}", "Conteo actual", cols=c3)

st.divider()
section("Mapa de calor por servicio", "Riesgo medio vs día de estancia")
st.altair_chart(occupancy_heatmap(scored), use_container_width=True)

st.divider()
section("Censo cama a cama", "Filtra por servicio o municipio")
svc = st.multiselect("Servicio", sorted(scored["servicio"].unique().tolist()))
muni = st.multiselect("Municipio", sorted(scored["municipio"].unique().tolist()))
dfv = scored.copy()
if svc: dfv = dfv[dfv["servicio"].isin(svc)]
if muni: dfv = dfv[dfv["municipio"].isin(muni)]
dfv = dfv.sort_values(["servicio","risk_factor"], ascending=[True,False])

st.dataframe(style_risk_table(dfv), use_container_width=True, height=420)
debug("Página Censo Inteligente renderizada")
