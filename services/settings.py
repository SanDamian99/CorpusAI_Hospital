# services/settings.py
from __future__ import annotations
import os
from dataclasses import dataclass
import streamlit as st

@dataclass
class CorpusTheme:
    # Paleta Corpus
    primary = "#3DA9FC"   # Azul claro (acciones, acentos)
    accent  = "#5FB4FF"   # Azul claro alterno (hover, detalles)
    warn    = "#F4A261"   # Ámbar (advertencias)
    danger  = "#E76F51"   # Coral (errores)
    success = "#2ECC71"   # Verde (éxito)
    neutral = "#BFD7FF"   # Azul muy claro/neutral (borders suaves)


def get_debug() -> bool:
    # Prioridad: query param ?debug=1 -> sidebar toggle -> env var
    qp = st.query_params.get("debug", None)
    if qp is not None:
        return str(qp).lower() in ("1","true","yes")
    if "DEBUG_MODE" not in st.session_state:
        st.session_state.DEBUG_MODE = os.getenv("CORPUS_DEBUG","0") in ("1","true","yes")
    return bool(st.session_state.DEBUG_MODE)

def debug_toggle():
    st.sidebar.checkbox("🔧 Modo Debug", key="DEBUG_MODE", value=get_debug())

def debug(msg: str):
    if get_debug():
        st.sidebar.markdown(f"**[DEBUG]** {msg}")

def inject_css():
    from .settings import CorpusTheme  # estamos en el mismo archivo, no hay ciclo
    st.markdown(f"""
        <style>
        :root {{
          --corpus-primary: {CorpusTheme.primary};
          --corpus-accent: {CorpusTheme.accent};
          --corpus-neutral: {CorpusTheme.neutral};
        }}

        /* Chips */
        .chip {{ padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; margin-right: 6px; }}
        .chip-red   {{ background:#E76F51; color:#0B1E3F; }}   /* texto azul oscuro para buen contraste */
        .chip-amber {{ background:#F4A261; color:#0B1E3F; }}
        .chip-green {{ background:#2ECC71; color:#0B1E3F; }}

        /* Cards / métricas */
        .kpi {{
            border-radius:14px;
            padding:14px;
            background:#122B4A;          /* secondaryBackgroundColor */
            border:1px solid #1E3A5F;    /* borde acorde a azul oscuro */
        }}
        .soft {{ color: {CorpusTheme.neutral}; }}
        .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}

        /* Pills / bordes */
        .pill {{
            border-radius: 999px;
            padding: 2px 10px;
            border:1px solid {CorpusTheme.accent};
        }}
        </style>
    """, unsafe_allow_html=True)


