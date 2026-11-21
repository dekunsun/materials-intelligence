"""Materials Intelligence — Portfolio Board v0.1.

    .venv/bin/streamlit run board/app.py

Renders the curated tables in data/board/ and the figures in results/. It never
writes. Every evidence row carries its source and verification status; rows that
are not verified are shown in grey.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
st.set_page_config(page_title="Materials Intelligence Board", page_icon="🧭", layout="wide")

from board.views import decisions, direction, modules, overview  # noqa: E402

VIEWS = {"overview": overview.render, "direction": direction.render, "decisions": decisions.render, "modules": modules.render}
NAMES = {"overview": ("Overview", "总览"), "direction": ("Direction detail", "方向详情"),
         "decisions": ("Decisions", "决策"), "modules": ("Module results", "模块结果")}


def main() -> None:
    q = st.query_params
    lang = q.get("lang", "en")
    keys = list(VIEWS)
    current = q.get("view", "overview")
    with st.sidebar:
        st.title("Materials Intelligence")
        st.caption("Portfolio Board v0.1 · From Research to Market" if lang == "en" else "投资组合看板 v0.1 · 从研究到市场")
        lang = st.radio("Language / 语言", ["en", "zh"], index=["en", "zh"].index(lang) if lang in ("en", "zh") else 0,
                        format_func=lambda x: "English" if x == "en" else "中文", horizontal=True)
        choice = st.radio("View", keys, index=keys.index(current) if current in keys else 0,
                          format_func=lambda k: NAMES[k][0 if lang == "en" else 1], label_visibility="collapsed")
        st.divider()
        st.caption("Outside-in analysis from public evidence. Not DeepMind's plan; role lenses, not people."
                   if lang == "en" else "基于公开证据的由外向内分析，不代表 DeepMind 的计划；按角色视角，不针对具体的人。")
        st.caption("Renders data/board/*.csv and results/. Never writes." if lang == "en"
                   else "只读取 data/board/*.csv 和 results/，不写入任何东西。")
    if choice != current or q.get("lang") != lang:
        st.query_params.update({"view": choice, "lang": lang})
    VIEWS[choice](lang)


main()
