# services/risk_api.py
from __future__ import annotations
import numpy as np
import pandas as pd
from .settings import debug

def _sigmoid(x): return 1/(1+np.exp(-x))

def _make_survival_curve(hazard_per_day: float, horizon_days: int = 60):
    # S(t) = exp(-λt) con clipping [0.02, 1.0]
    days = np.arange(0, horizon_days+1, 5)
    S = np.exp(-hazard_per_day * days)
    S = np.clip(S, 0.02, 1.0)
    return [{"day": int(d), "S": float(s)} for d, s in zip(days, S)]

def _window_from_risk(r):
    # Riesgo alto: ventana más temprana y estrecha
    if r >= 0.40:
        a = np.random.randint(7, 14); b = a + np.random.randint(10, 18)
    elif r >= 0.15:
        a = np.random.randint(12, 20); b = a + np.random.randint(12, 24)
    else:
        a = np.random.randint(18, 25); b = a + np.random.randint(14, 28)
    return a, b

def score_batch(df: pd.DataFrame, seed: int = 123) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    x = (
        0.9*(df["creatinina"].astype(float)-1.0) +
        0.6*(df["hba1c"].astype(float)-6.0) +
        0.05*(df["sistolica"].astype(float)-120.0)/10.0 +
        0.08*(df["polifarmacia_n"].astype(float)) +
        0.5*(df["hosp_6m"].astype(float))
    )
    # normaliza y convierte a probabilidad tipo riesgo 0–0.95
    z = (x - x.mean()) / (x.std() + 1e-6)
    risk = np.clip(_sigmoid(z) * 0.9, 0.03, 0.95)
    out = df.copy()
    out["risk_factor"] = risk

    # hazard proporcional al riesgo (más suave)
    hazard = 0.015 + 0.045 * risk
    out["surv_curve"] = [ _make_survival_curve(h) for h in hazard ]

    # ventana temporal
    starts, ends = [], []
    for r in risk:
        a,b = _window_from_risk(float(r))
        starts.append(a); ends.append(b)
    out["t_start_days"] = starts
    out["t_end_days"] = ends

    # top-features (dummy explicativo)
    top_all = ["Creatinina", "HbA1c", "Polifarmacia", "HospPrev6m", "PAS"]
    # ordena por contribución heurística
    weights = np.vstack([
        0.35*risk, 0.30*risk, 0.15*risk, 0.12*risk, 0.08*risk
    ]).T
    out["top_features"] = [ [f for _,f in sorted(zip(w, top_all), reverse=True)] for w in weights ]
    debug("Riesgos calculados y curvas generadas.")
    return out
