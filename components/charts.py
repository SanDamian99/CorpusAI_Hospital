# components/charts.py
from __future__ import annotations
import pandas as pd
import altair as alt

def survival_curve_chart(points: list[dict], height: int = 150):
    data = pd.DataFrame(points)
    return alt.Chart(data).mark_line(point=True).encode(
        x=alt.X("day:Q", title="Días"),
        y=alt.Y("S:Q", title="Supervivencia"),
        tooltip=["day","S"]
    ).properties(height=height)

def top_features_bar(features: list[str], importances: list[float] | None = None, height: int = 140):
    if importances is None:
        importances = list(range(len(features),0,-1))
    df = pd.DataFrame({"factor": features, "importancia": importances})
    return alt.Chart(df).mark_bar().encode(
        x=alt.X("importancia:Q", title="Importancia (relativa)"),
        y=alt.Y("factor:N", sort="-x", title="Factor"),
        tooltip=["factor","importancia"]
    ).properties(height=height)

def donut_gauge(value: float, title: str = "Riesgo"):
    # value en 0–1
    df = pd.DataFrame({
        "label":["Valor","Resto"],
        "val":[value, max(0.0001, 1-value)]
    })
    c = alt.Chart(df).mark_arc(innerRadius=45).encode(
        theta="val:Q",
        color=alt.Color("label:N", scale=alt.Scale(range=["#2AA198","#22343f"]), legend=None)
    ).properties(width=160, height=160)
    text = alt.Chart(pd.DataFrame({"v":[f"{value*100:.0f}%"]})).mark_text(size=22).encode(text="v:N")
    return (c + text).properties(title=title)

def deciles_km_chart(deciles_dict: dict[int, list[dict]], height: int = 260):
    # deciles_dict: {1:[{day,S},...], ...., 10:[...]}
    rows=[]
    for d, pts in deciles_dict.items():
        for p in pts:
            rows.append({"decile": d, "day": p["day"], "S": p["S"]})
    df = pd.DataFrame(rows)
    return alt.Chart(df).mark_line().encode(
        x=alt.X("day:Q", title="Días"),
        y=alt.Y("S:Q", title="Supervivencia"),
        color=alt.Color("decile:N", legend=alt.Legend(title="Decil")),
        tooltip=["decile","day","S"]
    ).properties(height=height)

def occupancy_heatmap(df: pd.DataFrame, height: int = 260):
    # requiere columnas: servicio, day_estancia, risk_factor
    agg = df.groupby(["servicio","day_estancia"], as_index=False)["risk_factor"].mean()
    return alt.Chart(agg).mark_rect().encode(
        x=alt.X("day_estancia:Q", title="Día de estancia"),
        y=alt.Y("servicio:N", title="Servicio"),
        color=alt.Color("risk_factor:Q", title="Riesgo medio", scale=alt.Scale(scheme="teals")),
        tooltip=["servicio","day_estancia","risk_factor"]
    ).properties(height=height)
