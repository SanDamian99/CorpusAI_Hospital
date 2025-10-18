# services/data.py
from __future__ import annotations
import pandas as pd
from services.risk_engine import DUMMY_ORDERED_COLS

def expected_columns() -> list[str]:
    return DUMMY_ORDERED_COLS

def validate_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in DUMMY_ORDERED_COLS if c not in df.columns]
