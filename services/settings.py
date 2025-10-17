# services/settings.py
from __future__ import annotations
import os
from dataclasses import dataclass
import streamlit as st

@dataclass
class CorpusTheme:
    primary = "#2AA198"       # teal
    accent = "#35C1B6"        # aqua
    warn = "#F4A261"          # amber
    danger = "#E76F51"        # coral
    success = "#2ECC71"       # green
    neutral = "#AAB7C4"

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
    st.markdown("""
        <style>
        /* Chips */
        .chip { padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; margin-right: 6px;}
        .chip-red { background:#E76F51; color:#0B0F14; }
        .chip-amber { background:#F4A261; color:#0B0F14;}
        .chip-green { background:#2ECC71; color:#0B0F14;}
        /* Cards */
        .kpi { border-radius:14px; padding:14px; background:#10161D; border:1px solid #1f2a33; }
        .soft { color:#AAB7C4; }
        .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
        .pill { border-radius: 999px; padding: 2px 10px; border:1px solid #1f2a33;}
        </style>
    """, unsafe_allow_html=True)
