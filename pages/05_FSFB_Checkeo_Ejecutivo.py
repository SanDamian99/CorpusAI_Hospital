# pages/05_FSFB_Checkeo_Ejecutivo.py
from __future__ import annotations
import io
import numpy as np
import pandas as pd
import streamlit as st

from services.settings import inject_css, debug_toggle, debug, CorpusTheme, get_debug
from services.risk_engine import (
    FEATURE_CONFIG, compute_risk_and_survival, explain_contributions,
    risk_tier, DUMMY_ORDERED_COLS, make_dummy_population, recommended_actions
)
from components.survival_plot import render_survival_curve
from components.ui_blocks import kpi_card, pill, section_header

st.set_page_config(
    page_title="FSFB • Checkeo Ejecutivo",
    page_icon="🩺",
    layout="wide"
)

inject_css()
debug_toggle()

from services.auth import login_required
login_required("Corpus AI · Pilotos Hospitalarios")


section_header("🩺 FSFB • Checkeo Ejecutivo", subtitle="Evaluación cardio-renal preventiva con explicabilidad y recomendación personalizada")

tab_individual, tab_lote, tab_ayuda = st.tabs(["Evaluación individual", "Carga por lotes (CSV)", "Ayuda / Descargables"])

with tab_individual:
    st.subheader("Datos del ejecutivo/a")
    # Formulario principal
    with st.form("exec_check_form"):
        c1, c2, c3, c4 = st.columns(4)
        age = c1.number_input("Edad (años)", 18, 100, 52)
        sex = c2.selectbox("Sexo", ["M", "F"])
        sbp = c3.number_input("PAS (mmHg)", 80, 240, 134)
        dbp = c4.number_input("PAD (mmHg)", 50, 140, 82)

        c5, c6, c7, c8 = st.columns(4)
        hba1c = c5.number_input("HbA1c (%)", 4.5, 15.0, 6.8, step=0.1)
        ldl = c6.number_input("LDL (mg/dL)", 0, 400, 122)
        egfr = c7.number_input("eGFR (mL/min/1.73m²)", 5, 150, 78)
        uacr = c8.number_input("Albuminuria UACR (mg/g)", 0, 3000, 45)

        c9, c10, c11, c12 = st.columns(4)
        bmi = c9.number_input("IMC (kg/m²)", 14.0, 60.0, 29.2, step=0.1)
        smoker = c10.selectbox("Tabaquismo", ["No", "Ex", "Sí"])
        diabetes = c11.selectbox("Diabetes", ["No", "Sí"])
        htn = c12.selectbox("Hipertensión", ["No", "Sí"])

        c13, c14, c15, c16 = st.columns(4)
        statin = c13.selectbox("Usa estatina", ["No", "Sí"])
        ace_arb = c14.selectbox("Usa iECA/ARA-II", ["No", "Sí"])
        sglt2 = c15.selectbox("Usa SGLT2", ["No", "Sí"])
        glp1 = c16.selectbox("Usa GLP-1", ["No", "Sí"])

        c17, c18, c19 = st.columns(3)
        prior_cv = c17.selectbox("Antecedente CV (IAM/ACV/HF)", ["No", "Sí"])
        ckd_stage = c18.selectbox("ERC (etapa)", ["No", "1", "2", "3a", "3b", "4", "5"])
        horizon = c19.select_slider("Horizonte (meses)", options=[6,12,24,36,60], value=24)

        submitted = st.form_submit_button("Calcular riesgo y supervivencia", use_container_width=True)

    if submitted:
        row = {
            "age": age, "sex": sex, "sbp": sbp, "dbp": dbp,
            "hba1c": hba1c, "ldl": ldl, "egfr": egfr, "uacr": uacr,
            "bmi": bmi, "smoker": smoker, "diabetes": diabetes, "htn": htn,
            "statin": statin, "ace_arb": ace_arb, "sglt2": sglt2, "glp1": glp1,
            "prior_cv": prior_cv, "ckd_stage": ckd_stage
        }
        debug(f"INPUT: {row}")

        risk, survival_df, meta = compute_risk_and_survival(row, horizon_months=horizon)
        contrib = explain_contributions(row)

        tier = risk_tier(risk)
        cA, cB, cC = st.columns([1.2,1,1])
        with cA:
            kpi_card("Risk factor", f"{risk:.1f}%", caption=f"Horizonte: {horizon} meses")
        with cB:
            kpi_card("Rango temporal más crítico", f"{meta['peak_window'][0]}–{meta['peak_window'][1]} m", caption="Ventana de mayor hazard")
        with cC:
            kpi_card("Nivel de riesgo", tier.upper(), color={"bajo":"green","medio":"amber","alto":"red"}[tier])

        with st.container(border=True):
            st.markdown("**Supervivencia estimada** (modelo paramétrico estilo Weibull ajustado a perfil)")
            render_survival_curve(survival_df, horizon)

        st.markdown("### Principales impulsores del riesgo (explicabilidad)")
        c1, c2 = st.columns([1.1, 1])
        with c1:
            for name, pct, text in contrib[:6]:
                chip = pill(f"{pct:+.1f} pp", tone="info")
                st.markdown(f"- **{name}** {chip} — {text}", unsafe_allow_html=True)
        with c2:
            st.info("Interpretación: valores positivos aumentan el riesgo; negativos lo reducen. Sugerimos centrar la educación y el plan personalizado en los 3–5 principales impulsores modificables.")

        st.markdown("### Recomendación Clínica Personalizada")
        recs = recommended_actions(row, tier, meta)
        for r in recs:
            st.markdown(f"- {r}")

        st.caption("**Aviso**: Este resultado es un apoyo a la decisión clínica, no reemplaza el juicio médico. Requiere validación y consentimiento del paciente para uso asistencial.")

with tab_lote:
    st.subheader("Carga de CSV para múltiples ejecutivos")
    st.caption("Descarga una plantilla con columnas esperadas y carga tu archivo para obtener resultados por lote.")

    # Plantilla
    template_df = pd.DataFrame([{}], columns=DUMMY_ORDERED_COLS).fillna("")
    buf = io.BytesIO()
    template_df.to_csv(buf, index=False)
    st.download_button("📄 Descargar plantilla CSV", data=buf.getvalue(), file_name="fsfb_checkeo_ejecutivo_template.csv", use_container_width=True)

    # Uploader
    file = st.file_uploader("Sube tu CSV", type=["csv"])
    if file:
        df = pd.read_csv(file)
        missing = [c for c in DUMMY_ORDERED_COLS if c not in df.columns]
        if missing:
            st.error(f"Faltan columnas obligatorias: {missing}")
            st.stop()

        st.success(f"Archivo recibido: {df.shape[0]} filas.")
        out_rows = []
        for _, r in df.iterrows():
            risk, s_df, meta = compute_risk_and_survival(r.to_dict(), horizon_months=24)
            out_rows.append({
                **r.to_dict(),
                "risk_pct_24m": np.round(risk,1),
                "risk_tier_24m": risk_tier(risk),
                "peak_start_m": meta["peak_window"][0],
                "peak_end_m": meta["peak_window"][1]
            })
        out = pd.DataFrame(out_rows)
        st.dataframe(out, use_container_width=True)

        down = io.BytesIO()
        out.to_csv(down, index=False)
        st.download_button("⬇️ Descargar resultados", data=down.getvalue(), file_name="fsfb_checkeo_resultados.csv", use_container_width=True)

with tab_ayuda:
    st.markdown("""
**Cómo usar esta página**

1) Modo individual: completa los campos, calcula, revisa explicabilidad y aplica el plan sugerido.  
2) Modo por lotes: usa la plantilla y carga en bloque para jornadas de checkeo.  
3) Puedes activar el **🔧 Modo Debug** en la barra lateral para ver detalles internos y facilitar soporte.
    """)
    if st.button("Generar 100 casos dummy para demos", use_container_width=True):
        demo = make_dummy_population(100)
        st.dataframe(demo.head(20), use_container_width=True)
