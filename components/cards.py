# components/cards.py
from __future__ import annotations
import streamlit as st

def kpi(title: str, value: str, help_text: str = "", delta: str | None = None, cols=None):
    box = st.container() if cols is None else cols
    with (box if cols is None else cols):
        st.markdown(f"<div class='kpi'><div class='soft'>{title}</div><div style='font-size:1.6rem;font-weight:700'>{value}</div><div class='soft'>{help_text}</div></div>", unsafe_allow_html=True)

def risk_chip(p: float) -> str:
    if p >= 0.40:
        return "<span class='chip chip-red'>ALTO</span>"
    if p >= 0.15:
        return "<span class='chip chip-amber'>MEDIO</span>"
    return "<span class='chip chip-green'>BAJO</span>"

def section(title: str, subtitle: str = ""):
    st.markdown(f"### {title}  \n<span class='soft'>{subtitle}</span>", unsafe_allow_html=True)
