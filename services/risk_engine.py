# services/risk_engine.py
from __future__ import annotations
import math
import random
from typing import Dict, Tuple, List
import numpy as np
import pandas as pd

# ======= Configuración de features (piloto) =======
# Tipos y rangos para normalización simple
FEATURE_CONFIG = {
    "age": {"type":"num", "norm":(18, 90), "beta": 0.018, "text":"Edad avanzada aumenta riesgo"},
    "sex": {"type":"cat", "map":{"M":0.0,"F":-0.02}, "beta": 1.0, "text":"Riesgo ligeramente mayor en hombres"},
    "sbp": {"type":"num", "norm":(90, 200), "beta": 0.010, "text":"PAS alta eleva riesgo CV y renal"},
    "dbp": {"type":"num", "norm":(50, 120), "beta": 0.004, "text":"PAD elevada contribuye a HTA no controlada"},
    "hba1c": {"type":"num", "norm":(4.8, 13), "beta": 0.045, "text":"Glucemia crónicamente alta acelera daño vascular"},
    "ldl": {"type":"num", "norm":(40, 250), "beta": 0.008, "text":"LDL elevado incrementa riesgo aterosclerótico"},
    "egfr": {"type":"num_inv", "norm":(15, 120), "beta": 0.020, "text":"Filtrado bajo sugiere disfunción renal"},
    "uacr": {"type":"num", "norm":(0, 1000), "beta": 0.006, "text":"Albuminuria es marcador de daño renal y CV"},
    "bmi": {"type":"num", "norm":(18, 45), "beta": 0.012, "text":"Obesidad aumenta carga cardiometabólica"},
    "smoker": {"type":"cat", "map":{"No":0.0, "Ex":0.02, "Sí":0.07}, "beta": 1.0, "text":"Tabaquismo activo eleva eventos CV"},
    "diabetes": {"type":"cat", "map":{"No":0.0, "Sí":0.09}, "beta": 1.0, "text":"Diabetes es impulsor mayor de riesgo"},
    "htn": {"type":"cat", "map":{"No":0.0, "Sí":0.05}, "beta": 1.0, "text":"Hipertensión añade riesgo residual"},
    "statin": {"type":"cat", "map":{"No":0.03, "Sí":-0.02}, "beta": 1.0, "text":"Estatina reduce riesgo si está indicada"},
    "ace_arb": {"type":"cat", "map":{"No":0.03, "Sí":-0.02}, "beta": 1.0, "text":"iECA/ARA-II protege CV y renal"},
    "sglt2": {"type":"cat", "map":{"No":0.03, "Sí":-0.03}, "beta": 1.0, "text":"SGLT2 reduce progresión renal/HF"},
    "glp1": {"type":"cat", "map":{"No":0.02, "Sí":-0.02}, "beta": 1.0, "text":"GLP-1 ayuda a control cardiometabólico"},
    "prior_cv": {"type":"cat", "map":{"No":0.0, "Sí":0.12}, "beta": 1.0, "text":"Antecedente CV marca riesgo residual alto"},
    "ckd_stage": {"type":"cat_ord", "map":{"No":0, "1":0.00,"2":0.02,"3a":0.05,"3b":0.08,"4":0.12,"5":0.18}, "beta":1.0, "text":"Etapa ERC aumenta riesgo de eventos y progresión"}
}

DUMMY_ORDERED_COLS = list(FEATURE_CONFIG.keys())

def _norm_num(v, lo, hi, inverse=False):
    v = max(lo, min(hi, float(v)))
    x = (v - lo) / (hi - lo + 1e-9)
    return 1 - x if inverse else x

def _value_to_score(name, val):
    cfg = FEATURE_CONFIG[name]
    if cfg["type"] == "num":
        lo, hi = cfg["norm"]
        return cfg["beta"] * _norm_num(val, lo, hi, inverse=False)
    if cfg["type"] == "num_inv":
        lo, hi = cfg["norm"]
        return cfg["beta"] * _norm_num(val, lo, hi, inverse=True)
    if cfg["type"] == "cat":
        return cfg["beta"] * cfg["map"].get(val, 0.0)
    if cfg["type"] == "cat_ord":
        return cfg["beta"] * cfg["map"].get(val, 0.0)
    return 0.0

def _linear_predictor(row: Dict) -> float:
    s = 0.0
    for k in FEATURE_CONFIG.keys():
        s += _value_to_score(k, row.get(k))
    # Centramos en 0 aprox
    return s - 0.12

def _weibull_params(lp: float) -> Tuple[float, float]:
    """
    Mapea lp -> parámetros de Weibull: k (shape), lambda (scale)
    Baseline moderado; mayor lp aumenta lambda (hazard).
    """
    k = 1.45 + 0.15 * np.tanh(lp)        # shape 1.3-1.6 aprox.
    lam = 0.015 * math.exp(lp)           # scale aumenta exponencialmente con lp
    return k, lam

def survival_weibull(months: int, k: float, lam: float) -> pd.DataFrame:
    t = np.arange(0, months+1)
    # t en meses; convertimos a años para una escala razonable de lam mensual
    S = np.exp(- (lam * (t))**k)
    # Riesgo acumulado 1 - S
    df = pd.DataFrame({"month": t, "survival": S, "cumulative_risk": 1 - S})
    return df

def _peak_hazard_window(k: float, lam: float, horizon: int) -> Tuple[int, int]:
    # Hazard Weibull: h(t) = k*lam^k * t^(k-1)
    t = np.arange(1, horizon+1)
    h = k * (lam**k) * (t ** (k-1))
    # ventana de 6 meses donde el promedio de h es máximo
    W = 6
    if len(t) < W:
        return (1, horizon)
    rolling = pd.Series(h).rolling(W).mean().to_numpy()
    i = int(np.nanargmax(rolling))
    start = max(1, i - W + 2)
    end = min(horizon, start + W - 1)
    return (start, end)

def compute_risk_and_survival(row: Dict, horizon_months: int = 24) -> Tuple[float, pd.DataFrame, Dict]:
    lp = _linear_predictor(row)
    k, lam = _weibull_params(lp)
    surv = survival_weibull(max(horizon_months, 60), k, lam)
    risk_pct = float((1 - surv.loc[surv["month"]==horizon_months,"survival"].values[0]) * 100.0)
    peak = _peak_hazard_window(k, lam, horizon_months)
    meta = {"lp": lp, "k": k, "lam": lam, "peak_window": peak}
    return risk_pct, surv, meta

def explain_contributions(row: Dict) -> List[Tuple[str, float, str]]:
    """
    Devuelve lista [(feature, contrib_pp, texto)], ordenada por |contrib|.
    Aproximación: diferencia de riesgo al tope vs. al mínimo para cada variable.
    """
    base_risk, _, meta = compute_risk_and_survival(row, 24)
    outs = []
    for k, cfg in FEATURE_CONFIG.items():
        r2 = dict(row)
        # mover a un nivel "más sano" para ver potencial
        if cfg["type"]=="num":
            lo, _ = cfg["norm"]
            r2[k] = lo
        elif cfg["type"]=="num_inv":
            _, hi = cfg["norm"]
            r2[k] = hi
        elif cfg["type"] in ("cat","cat_ord"):
            # elegir el valor con menor contribución del mapa
            min_val = min(cfg["map"], key=lambda x: cfg["map"][x])
            r2[k] = min_val
        risk2, _, _ = compute_risk_and_survival(r2, 24)
        delta = base_risk - risk2
        outs.append((k, delta, cfg.get("text","")))
    outs.sort(key=lambda x: abs(x[1]), reverse=True)
    return outs

def risk_tier(risk_pct: float) -> str:
    if risk_pct >= 20:
        return "alto"
    if risk_pct >= 10:
        return "medio"
    return "bajo"

def make_dummy_population(n: int, seed: int = 42, include_dept: bool=False) -> pd.DataFrame:
    random.seed(seed); np.random.seed(seed)
    sex = np.random.choice(["M","F"], size=n, p=[0.55,0.45])
    age = np.random.randint(22, 74, size=n)
    sbp = np.random.normal(132, 16, size=n).clip(95, 200)
    dbp = np.random.normal(82, 10, size=n).clip(55, 120)
    hba1c = np.random.normal(6.3, 1.2, size=n).clip(4.8, 12.5)
    ldl = np.random.normal(118, 35, size=n).clip(40, 240)
    egfr = np.random.normal(85, 18, size=n).clip(20, 125)
    uacr = np.exp(np.random.normal(np.log(25), 1.0, size=n)).clip(0, 1000)
    bmi = np.random.normal(28.5, 4.5, size=n).clip(18, 45)
    smoker = np.random.choice(["No","Ex","Sí"], size=n, p=[0.7, 0.15, 0.15])
    diabetes = np.random.choice(["No","Sí"], size=n, p=[0.72, 0.28])
    htn = np.random.choice(["No","Sí"], size=n, p=[0.35, 0.65])
    statin = np.random.choice(["No","Sí"], size=n, p=[0.55, 0.45])
    ace_arb = np.random.choice(["No","Sí"], size=n, p=[0.5, 0.5])
    sglt2 = np.random.choice(["No","Sí"], size=n, p=[0.8, 0.2])
    glp1 = np.random.choice(["No","Sí"], size=n, p=[0.85, 0.15])
    prior_cv = np.random.choice(["No","Sí"], size=n, p=[0.85, 0.15])
    ckd_stage = np.random.choice(["No","1","2","3a","3b","4","5"], size=n, p=[0.55,0.06,0.13,0.12,0.08,0.04,0.02])

    data = pd.DataFrame({
        "age": age, "sex": sex, "sbp": sbp, "dbp": dbp,
        "hba1c": hba1c, "ldl": ldl, "egfr": egfr, "uacr": uacr,
        "bmi": bmi, "smoker": smoker, "diabetes": diabetes, "htn": htn,
        "statin": statin, "ace_arb": ace_arb, "sglt2": sglt2, "glp1": glp1,
        "prior_cv": prior_cv, "ckd_stage": ckd_stage
    })
    if include_dept:
        depts = ["Clínicas", "Admin", "Docencia", "Investigación", "Servicios Generales"]
        data["department"] = np.random.choice(depts, size=n, p=[0.34,0.28,0.16,0.12,0.10])
        data["employee_id"] = [f"E-{10000+i:05d}" for i in range(n)]
    return data

def recommended_actions(row: Dict, tier: str, meta: Dict) -> List[str]:
    actions = []
    # Ajustes basados en impulsores clave
    if row.get("hba1c", 5.8) >= 7.0 or row.get("diabetes")=="Sí":
        actions.append("⚕️ Intensificar control glucémico y educación terapéutica; evaluar GLP-1/SGLT2 si corresponde.")
    if row.get("sbp", 120) >= 140 or row.get("htn")=="Sí":
        actions.append("🫀 Optimizar control de PA (<130/80 si tolerado); adherencia a iECA/ARA-II.")
    if row.get("ldl", 90) >= 130 or row.get("statin")=="No":
        actions.append("🧬 Iniciar/optimizar estatina de alta intensidad; objetivo LDL <70 mg/dL si alto riesgo.")
    if row.get("egfr", 90) < 60 or (isinstance(row.get("uacr",0),(int,float)) and row.get("uacr",0)>=30):
        actions.append("🧪 Nefroprotección: iECA/ARA-II; evaluar SGLT2; nefrología si ERC ≥ 3b o UACR ≥ 300.")
    if row.get("bmi",25) >= 30:
        actions.append("🏃 Programa de pérdida de peso y actividad física supervisada.")
    if row.get("smoker") == "Sí":
        actions.append("🚭 Intervención intensiva de cesación de tabaco.")
    # Priorización por nivel
    if tier=="alto":
        actions.insert(0, "🔴 Seguimiento intensivo (1–3 meses) y plan personalizado multidisciplinario.")
    elif tier=="medio":
        actions.insert(0, "🟠 Seguimiento reforzado (3–6 meses) y metas dirigidas por riesgo.")
    else:
        actions.insert(0, "🟢 Educación preventiva y seguimiento anual.")
    # Ventana crítica
    actions.append(f"⏱️ Refuerza intervenciones entre meses {meta['peak_window'][0]}–{meta['peak_window'][1]} (ventana de mayor hazard).")
    return actions
