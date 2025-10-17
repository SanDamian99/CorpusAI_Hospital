# components/tables.py
from __future__ import annotations
import pandas as pd

def style_risk_table(df: pd.DataFrame) -> pd.DataFrame:
    # Devuelve df "bonito" para st.dataframe
    show = df.copy()
    show["riesgo"] = (show["risk_factor"]*100).round(0).astype(int).astype(str) + "%"
    show["nivel"] = show["risk_factor"].apply(lambda p: "ALTO" if p>=0.40 else ("MEDIO" if p>=0.15 else "BAJO"))
    show["ventana"] = show[["t_start_days","t_end_days"]].apply(lambda r: f"{int(r[0])}-{int(r[1])} días", axis=1)
    cols = ["patient_id","servicio","edad","sexo","dx_principal_cie10","riesgo","nivel","ventana","municipio"]
    return show[cols]
