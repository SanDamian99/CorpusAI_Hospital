# Corpus AI · Pilotos Hospitalarios (Streamlit)

Cuatro prototipos de interfaz para Hospitales/IPS:
- **Alta Segura 30D** (gestión del egreso y reingresos)
- **Censo Inteligente** (mapa de camas con overlays de riesgo)
- **Clínicas Cardio-Renales** (constructor de cohortes + KM por deciles + agenda)
- **Dirección & ROI** (what-ifs y evidencia para contratos)

## Ejecutar local
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
```bash
corpusai_hospital/
├─ app.py
├─ README.md
├─ requirements.txt
├─ .gitignore
├─ .streamlit/
│  └─ config.toml
├─ data/
│  └─ (vacío; se autogenera sample_egresos.csv en el primer arranque)
├─ services/
│  ├─ settings.py
│  ├─ data_loader.py
│  ├─ risk_api.py
│  └─ whatif.py
├─ components/
│  ├─ charts.py
│  ├─ cards.py
│  └─ tables.py
└─ pages/
   ├─ 1_Alta_Segura.py
   ├─ 2_Censo_Inteligente.py
   ├─ 3_Clinicas_CardioRenales.py
   └─ 4_Direccion_ROI.py
