# services/whatif.py
from __future__ import annotations

def expected_avoided_events(n_cohort:int, baseline_rate:float, coverage:float, efficacy:float) -> float:
    # n_cohort: tamaño cohorte total
    # coverage, efficacy: 0–1
    return n_cohort * baseline_rate * coverage * efficacy

def roi(avoided_events:float, cost_per_event:float, program_cost_per_patient:float, n_treated:int):
    benefits = avoided_events * cost_per_event
    costs = program_cost_per_patient * n_treated
    ratio = (benefits - costs) / costs if costs > 0 else float("inf")
    return benefits, costs, ratio
