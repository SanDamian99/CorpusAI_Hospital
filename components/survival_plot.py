# components/survival_plot.py
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from services.settings import CorpusTheme

def render_survival_curve(df: pd.DataFrame, horizon: int = 24):
    sub = df[df["month"]<=max(60, horizon)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sub["month"], y=sub["survival"],
        mode="lines", name="Supervivencia", line=dict(width=3)
    ))
    fig.add_trace(go.Scatter(
        x=sub["month"], y=sub["cumulative_risk"],
        mode="lines", name="Riesgo acumulado", line=dict(width=2, dash="dot")
    ))
    fig.update_layout(
        template="plotly_dark",
        title="Curva de supervivencia estimada",
        xaxis_title="Meses",
        yaxis_title="Probabilidad",
        legend=dict(orientation="h")
    )
    st.plotly_chart(fig, use_container_width=True)
