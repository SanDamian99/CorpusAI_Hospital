# services/data_loader.py
from __future__ import annotations
import os, uuid, random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import streamlit as st
from pydantic import BaseModel, Field, ValidationError
from dateutil.relativedelta import relativedelta
from .settings import debug

DATA_DIR = "data"
SAMPLE_FILE = os.path.join(DATA_DIR, "sample_egresos.csv")

class Schema(BaseModel):
    patient_id: str
    episode_id: str
    fecha_ingreso: str
    fecha_egreso_prevista: str
    edad: int = Field(ge=0, le=110)
    sexo: str
    dx_principal_cie10: str
    dx_secundarios: str
    creatinina: float
    hba1c: float
    sistolica: int
    diastolica: int
    polifarmacia_n: int
    hosp_6m: int
    servicio: str
    municipio: str

SERVICIOS = ["Medicina Interna","Cardiología","Nefrología","Cirugía","UCI","Obs. Urgencias"]
CIE10 = ["I50", "I21", "N18", "E11", "I10", "E78", "J44", "K21", "F41"]
MUNICIPIOS = ["Bogotá","Medellín","Cali","Barranquilla","Monterrey","CDMX","Guadalajara","Puebla"]

def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def generate_dummy(n: int = 180, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    today = datetime.now().date()
    for i in range(n):
        pid = str(uuid.uuid4())[:8]
        epi = str(uuid.uuid4())[:8]
        servicio = random.choice(SERVICIOS)
        sexo = random.choice(["M","F"])
        edad = int(np.clip(rng.normal(66, 12), 20, 95))
        ing = today - timedelta(days=int(np.clip(rng.normal(6, 4), 0, 25)))
        egr_prev = ing + timedelta(days=int(np.clip(rng.normal(7, 3), 1, 21)))
        dxp = random.choice(CIE10)
        dxs = ";".join(rng.choice(CIE10, size=rng.integers(1,4), replace=False))
        creat = round(float(np.clip(rng.normal(1.4 if dxp in ["N18"] else 1.1, 0.5), 0.4, 6.0)),2)
        hba1c = round(float(np.clip(rng.normal(7.8 if dxp in ["E11"] else 6.2, 1.2), 4.8, 13.5)),1)
        sis = int(np.clip(rng.normal(132, 18), 90, 210))
        dia = int(np.clip(rng.normal(82, 12), 55, 130))
        poly = int(np.clip(rng.poisson(5), 0, 18))
        hosp6 = int(rng.random() < 0.22) + int(rng.random() < 0.10)  # 0-2
        muni = random.choice(MUNICIPIOS)
        rows.append(dict(
            patient_id=pid, episode_id=epi,
            fecha_ingreso=str(ing),
            fecha_egreso_prevista=str(egr_prev),
            edad=edad, sexo=sexo,
            dx_principal_cie10=dxp, dx_secundarios=dxs,
            creatinina=creat, hba1c=hba1c,
            sistolica=sis, diastolica=dia,
            polifarmacia_n=poly, hosp_6m=hosp6,
            servicio=servicio, municipio=muni
        ))
    df = pd.DataFrame(rows)
    return df

def write_sample_if_missing():
    _ensure_data_dir()
    if not os.path.exists(SAMPLE_FILE):
        df = generate_dummy()
        df.to_csv(SAMPLE_FILE, index=False)

@st.cache_data(show_spinner=False)
def load_csv(path_or_buffer=None) -> pd.DataFrame:
    write_sample_if_missing()
    if path_or_buffer is None:
        df = pd.read_csv(SAMPLE_FILE)
        debug(f"Cargado dataset dummy ({len(df)} filas)")
    else:
        df = pd.read_csv(path_or_buffer)
        debug(f"Cargado dataset del usuario ({len(df)} filas)")
    # quick schema check (sample 5)
    for _, r in df.sample(min(len(df),5), random_state=7).iterrows():
        try:
            Schema(**r.to_dict())
        except ValidationError as e:
            debug(str(e))
            st.warning("⚠️ Columnas o tipos inesperados en el CSV. Usando lo disponible.")
            break
    return df

def parse_date(s: str):
    return pd.to_datetime(s).dt.date if isinstance(s, (pd.Series,)) else pd.to_datetime(s).date()

def days_between(a, b) -> int:
    return (pd.to_datetime(b) - pd.to_datetime(a)).days
