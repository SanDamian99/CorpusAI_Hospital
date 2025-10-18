# pages/1_Alta_Segura.py
from __future__ import annotations
import streamlit as st
import pandas as pd
from components.charts import survival_curve_chart, top_features_bar, donut_gauge
from components.cards import kpi, risk_chip, section
from components.tables import style_risk_table
from services.data_loader import load_csv, days_between
from services.risk_api import score_batch
from services.settings import inject_css, debug, debug_toggle

st.set_page_config(page_title="Alta Segura 30D", page_icon="✅", layout="wide")
inject_css(); debug_toggle()
from services.auth import login_required
login_required("Corpus AI · Pilotos Hospitalarios")


st.header("✅ Alta Segura 30D")
uploaded = st.file_uploader("Sube CSV de egresos (opcional). Si omites, se usa dataset dummy.", type=["csv"])
df = load_csv(uploaded)

# Derivados
df["day_estancia"] = df.apply(lambda r: days_between(r["fecha_ingreso"], r["fecha_egreso_prevista"]), axis=1)

# Scoring
scored = score_batch(df)
st.success("Datos listos y riesgos calculados.")

# KPIs
c1, c2, c3, c4 = st.columns(4)
kpi("Pacientes", f"{len(scored)}", "Registros cargados", cols=c1)
kpi("Riesgo medio", f"{scored['risk_factor'].mean():.0%}", "Media simple", cols=c2)
kpi("Rojos (≥40%)", f"{(scored['risk_factor']>=0.40).mean():.0%}", "Proporción", cols=c3)
kpi("Ventana mediana", f"{int(scored['t_start_days'].median())}-{int(scored['t_end_days'].median())} días", "Mayor probabilidad", cols=c4)

st.divider()

# Lista priorizada
section("Lista de trabajo", "Ordena por riesgo y filtra por servicio")
svc = st.multiselect("Servicio", options=sorted(scored["servicio"].unique().tolist()))
dfv = scored.copy()
if svc:
    dfv = dfv[dfv["servicio"].isin(svc)]
dfv = dfv.sort_values("risk_factor", ascending=False)

st.dataframe(style_risk_table(dfv), use_container_width=True, height=380)

# Detalle de paciente
section("Detalle de paciente", "Explana la predicción y registra acciones")
pid = st.selectbox("Paciente", dfv["patient_id"].unique())
row = dfv[dfv["patient_id"]==pid].iloc[0]

c1, c2 = st.columns([1,1])
with c1:
    st.altair_chart(donut_gauge(float(row["risk_factor"]), "Riesgo"), use_container_width=True)
    st.markdown(f"Nivel: {risk_chip(float(row['risk_factor']))}", unsafe_allow_html=True)
    st.markdown(f"**Ventana:** {int(row['t_start_days'])}-{int(row['t_end_days'])} días")
with c2:
    st.altair_chart(survival_curve_chart(row["surv_curve"], height=180), use_container_width=True)
    st.altair_chart(top_features_bar(row["top_features"], height=140), use_container_width=True)

st.subheader("Plan de alta")
accion = st.selectbox("Acción realizada", ["--","Educación reforzada","Telemonitoreo 30d","Visita domiciliaria","Trabajo social","Ajuste medicación"])
nota = st.text_input("Notas (opcional)")
if "acciones" not in st.session_state: st.session_state.acciones = []
if st.button("💾 Guardar acción"):
    st.session_state.acciones.append({"patient_id": pid, "accion": accion, "nota": nota})
    st.success("Acción registrada.")

if st.session_state.get("acciones"):
    acts = pd.DataFrame(st.session_state.acciones)
    st.write("Historial de acciones")
    st.dataframe(acts, use_container_width=True)
    st.download_button("⬇️ Exportar acciones a CSV", acts.to_csv(index=False).encode("utf-8"), "acciones_alta_segura.csv", "text/csv")

debug("Página Alta Segura renderizada")
