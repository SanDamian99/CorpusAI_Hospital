# components/ui_blocks.py
from __future__ import annotations
import streamlit as st
from services.settings import CorpusTheme

def kpi_card(title: str, value: str, caption: str|None=None, color: str|None=None):
    color_map = {
        "red": "#E76F51",
        "amber": "#F4A261",
        "green": "#23C97A",
        "info": CorpusTheme.primary
    }
    border = color_map.get(color, "#1f2a33")
    st.markdown(f"""
    <div class="kpi" style="border-color:{border}">
        <div style="font-size:0.9rem; color:#AAB7C4;">{title}</div>
        <div style="font-size:1.8rem; font-weight:700; margin-top:2px;">{value}</div>
        <div class="soft" style="font-size:0.8rem;">{caption or ""}</div>
    </div>
    """, unsafe_allow_html=True)

def pill(text: str, tone: str="info"):
    tones = {
        "info": CorpusTheme.primary,
        "ok": "#23C97A",
        "warn": "#F4A261",
        "danger": "#E76F51"
    }
    bg = tones.get(tone, CorpusTheme.primary)
    return f"""<span class="pill" style="border-color:{bg}">{text}</span>"""

def section_header(title: str, subtitle: str|None=None):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
